#!/usr/bin/env python3
"""Update throughput by update size (#496), on the SPARQL engines of benchmark v2.

Modelled on the update benchmark of "Efficient Updates for Worst-Case Optimal Join Triple Stores"
(Bigerl et al., ISWC 2025): batches of 10, 10^2, ..., 10^6 triples as INSERT DATA, then the same
batches as DELETE DATA, reporting time per triple by batch size. The triples are real ones held
out of a dataset (RINF, BSBM, ...), so they look like the data already in the store: new triples
about existing and new subjects, with the dataset's own literals.

  run_updates.py generate --source DS [--seed 42] [--max-size 1000000]
      reads $BENCH_WORK/data/DS.nt, holds out the triples of the batches (no blank nodes: DELETE
      DATA can't name them) -> $BENCH_WORK/data/updates-DS.nt (the base data, loaded by the
      engines) and $BENCH_WORK/updates/DS/<size>/<i>.nt (the batches), plus derive queries.
  run_updates.py run --source DS --engine E [--skip-load]
      bulk loads the base data, then per size: the INSERT DATA batches one after the other, a
      count check, the DELETE DATA batches, a count check; then the derive family: INSERT
      { } WHERE { } updates that mint new nodes from the data (like the rail KG uplift steps,
      #292), each undone by a DELETE WHERE. Store size on disk before and after.
      -> results/updates/DS/<engine>.json
  run_updates.py report -> results/updates/report.md

Times are wall-clock at the client, one update at a time, HTTP included. A failed update (an
error answer, or a timeout) is recorded and the run goes on; the count checks show whether the
store still holds what it should.
"""
import argparse
import array
import glob
import json
import os
import random
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, V2)
from run import Sparql  # noqa: E402

WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
OUT = os.path.join(V2, "results", "updates")
# Batches per size: enough to give a median at the small sizes, one at 10^6.
BATCHES = {10: 50, 100: 30, 1000: 10, 10_000: 5, 100_000: 3, 1_000_000: 1}
# Rows of the derive updates: the predicates whose triple counts come closest to these.
DERIVE_ROWS = [1_000, 10_000, 100_000]
ENGINES = ["tripletrail", "oxigraph", "jena", "graphdb", "qlever"]
TIMEOUT = 3600
NS = "urn:tripletrail:bench:updates:"


def sh(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{(r.stderr or '')[-3000:]}")
    return (r.stdout or "").strip()


def engine(e, *args):
    return sh(os.path.join(V2, "engines", f"{e}.sh"), *args)


def predicate(line):
    """The predicate IRI of an N-Triples line (the second term)."""
    rest = line[line.index(b">") + 1:] if line.startswith(b"<") else line[line.index(b" ") + 1:]
    rest = rest.lstrip()
    return rest[1:rest.index(b">")].decode()


def cmd_generate(a):
    src = os.path.join(WORK, "data", f"{a.source}.nt")
    lines = 0
    eligible = array.array("Q")
    counts = {}
    with open(src, "rb") as f:
        for i, line in enumerate(f):
            if not line.strip() or line.startswith(b"#"):
                continue
            lines += 1
            if b"_:" not in line:
                eligible.append(i)
            try:
                p = predicate(line)
                counts[p] = counts.get(p, 0) + 1
            except ValueError:
                pass
    # Sizes that fit: the held-out triples stay under half of what can be held out.
    plan, need = {}, 0
    for size, n in BATCHES.items():
        if size > a.max_size or need + size * n > len(eligible) // 2:
            break
        plan[size] = n
        need += size * n
    rng = random.Random(a.seed)
    held = rng.sample(range(len(eligible)), need)
    batch_of = {}
    at = 0
    for size, n in plan.items():
        for b in range(n):
            for k in held[at:at + size]:
                batch_of[eligible[k]] = (size, b)
            at += size
    out = os.path.join(WORK, "updates", a.source)
    for old in glob.glob(os.path.join(out, "*", "*.nt")):
        os.remove(old)
    files = {}
    for size, n in plan.items():
        os.makedirs(os.path.join(out, str(size)), exist_ok=True)
        for b in range(n):
            files[(size, b)] = open(os.path.join(out, str(size), f"{b}.nt"), "wb")
    base = os.path.join(WORK, "data", f"updates-{a.source}.nt")
    with open(src, "rb") as f, open(base, "wb") as bf:
        for i, line in enumerate(f):
            k = batch_of.get(i)
            (files[k] if k else bf).write(line)
    for fh in files.values():
        fh.close()
    # Derive updates: predicates (not rdf:type, which would mint a node per typed subject)
    # with about 10^3, 10^4, 10^5 triples.
    rdf_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    cands = sorted((n, p) for p, n in counts.items() if p != rdf_type)
    derive = []
    for rows in DERIVE_ROWS:
        if not cands:
            break
        n, p = min(cands, key=lambda c: abs(c[0] - rows))
        if not rows // 4 <= n <= rows * 4 or any(d["predicate"] == p for d in derive):
            continue
        derive.append({"name": f"derive-{rows}", "predicate": p, "triples_in_source": n})
    meta = {"source": a.source, "seed": a.seed, "source_triples": lines, "held_out": need,
            "base_triples": lines - need, "batches": {str(s): n for s, n in plan.items()},
            "derive": derive}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    json.dump({"triples": lines - need}, open(base[:-3] + ".meta.json", "w"))
    print(json.dumps(meta))


def derive_update(p):
    # One new node per (?s, ?o), its IRI minted from the strings of both: three triples, plus
    # one per type of the subject (an OPTIONAL join, like the rail KG uplift steps).
    return (f"INSERT {{ ?n a <{NS}Derived> ; <{NS}of> ?s ; <{NS}value> ?o ; <{NS}class> ?c }}\n"
            f"WHERE {{ ?s <{p}> ?o . OPTIONAL {{ ?s a ?c }}\n"
            f"  BIND(IRI(CONCAT(\"{NS}d/\", MD5(CONCAT(STR(?s), \"|\", STR(?o))))) AS ?n) }}")


UNDO = f"DELETE WHERE {{ ?n a <{NS}Derived> ; ?p ?v }}"


def count(cl, where="?s ?p ?o"):
    # The alias must not be a variable of the pattern (the derive check counts ?n): SPARQL
    # forbids that, and GraphDB rejects it ("projection alias 'n' was previously used").
    _, rows = cl.query(f"SELECT (COUNT(*) AS ?count_) WHERE {{ {where} }}", TIMEOUT)
    return int(rows[0][0])


def send_update(cl, text):
    """One update, timed. Sent as an application/sparql-update body, not a form: a form is
    about twice the bytes (percent-encoding) and servers cap forms separately (Jetty's form
    limit in Fuseki). QLever takes its access token in a form, so it gets one."""
    if cl.engine == "qlever":
        return cl.update(text, TIMEOUT)
    ep = cl.endpoint.replace("/query", "/update") if cl.engine != "graphdb" else cl.endpoint + "/statements"
    t = time.perf_counter()
    r = cl.s.post(ep, data=text.encode(), timeout=TIMEOUT,
                  headers={"Content-Type": "application/sparql-update; charset=utf-8"})
    cl.s.close()
    if r.status_code not in (200, 204):
        raise RuntimeError(f"update HTTP {r.status_code}: {r.text[:600]}")
    return time.perf_counter() - t


def timed_update(cl, text):
    try:
        return round(send_update(cl, text) * 1000, 3), None
    except Exception as e:  # noqa: BLE001 - recorded, not hidden
        return None, str(e)[:400]


def stats(ms, size):
    ok = [m for m in ms if m is not None]
    if not ok:
        return {"failed": len(ms)}
    q = sorted(ok)
    return {"n": len(ok), "failed": len(ms) - len(ok),
            "p50_ms": round(statistics.median(q), 3),
            "p95_ms": round(q[int(0.95 * (len(q) - 1))], 3),
            "total_s": round(sum(ok) / 1000, 3),
            "us_per_triple": round(sum(ok) * 1000 / (len(ok) * size), 3)}


def disk_bytes(e, ds):
    d = os.path.join(WORK, e, ds)
    return int(sh("du", "-sb", d).split()[0]) if os.path.isdir(d) else None


def cmd_run(a):
    ds = f"updates-{a.source}"
    # A batch of 10^6 triples is a body of ~250 MB; TripleTrail's default limit is 16 MB.
    os.environ.setdefault("TRIPLETRAIL_MAX_BODY", str(1 << 30))
    meta = json.load(open(os.path.join(WORK, "updates", a.source, "meta.json")))
    os.makedirs(os.path.join(OUT, a.source), exist_ok=True)
    rec = {"engine": a.engine, "source": a.source, "base_triples": meta["base_triples"],
           "sizes": {}, "derive": {}}
    if not a.skip_load:
        print(f"loading {ds} into {a.engine}", flush=True)
        rec["load"] = json.loads(engine(a.engine, "load", ds).splitlines()[-1])
    engine(a.engine, "start", ds)
    cl = Sparql(a.engine, engine(a.engine, "endpoint"))
    try:
        base = count(cl)
        rec["count_base"] = base
        for size_s, n in meta["batches"].items():
            size = int(size_s)
            if a.sizes and size not in a.sizes:
                continue
            batches = [open(os.path.join(WORK, "updates", a.source, size_s, f"{b}.nt")).read()
                       for b in range(n)]
            r = {"batches": n}
            for op, kw in (("insert", "INSERT DATA"), ("delete", "DELETE DATA")):
                ms, errors = [], []
                for text in batches:
                    t, err = timed_update(cl, f"{kw} {{\n{text}}}")
                    ms.append(t)
                    if err:
                        errors.append(err)
                r[op] = {**stats(ms, size), "ms": ms}
                if errors:
                    r[op]["errors"] = errors[:3]
                got = count(cl)
                want = base + size * n if op == "insert" else base
                r[op]["count_ok"] = got == want
                if got != want:
                    r[op]["count"] = {"got": got, "want": want}
                print(f"{a.engine} {size} x {n} {op}: {r[op].get('us_per_triple')} us/triple, "
                      f"p50 {r[op].get('p50_ms')} ms, failed {r[op].get('failed')}, "
                      f"count {'ok' if got == want else f'{got} != {want}'}", flush=True)
            rec["sizes"][size_s] = r
        for d in [] if a.no_derive else meta["derive"]:
            rows = count(cl, f"?s <{d['predicate']}> ?o")
            t, err = timed_update(cl, derive_update(d["predicate"]))
            made = count(cl, f"?n a <{NS}Derived>")
            u, uerr = timed_update(cl, UNDO)
            left = count(cl)
            rec["derive"][d["name"]] = {"predicate": d["predicate"], "rows": rows, "insert_ms": t,
                                        "nodes": made, "delete_ms": u, "count_ok": left == base,
                                        **({"error": err} if err else {}),
                                        **({"delete_error": uerr} if uerr else {})}
            print(f"{a.engine} {d['name']}: {rows} rows, insert {t} ms, delete {u} ms, "
                  f"{made} nodes, count {'ok' if left == base else left}", flush=True)
    finally:
        engine(a.engine, "stop")
    rec["disk_bytes_after"] = disk_bytes(a.engine, ds)
    path = os.path.join(OUT, a.source, f"{a.engine}.json")
    json.dump(rec, open(path, "w"), indent=1)
    print(path)


def fmt(x):
    if x is None:
        return ""
    return f"{x:.2f}" if x < 10 else f"{x:.1f}" if x < 100 else f"{x:,.0f}"


def cmd_report(_a):
    lines = ["# Update throughput by update size", "",
             "Batches of held-out triples of the dataset sent one at a time as INSERT DATA, then the "
             "same batches as DELETE DATA (#496). Cells: microseconds per triple over all batches of "
             "that size, with the median batch time in ms in brackets; `!` marks a failed update or a "
             "count check that did not match. Derive: INSERT { } WHERE { } minting one node (3 "
             "triples plus one per type of the subject) per row, then DELETE WHERE, in ms.", ""]
    for src_dir in sorted(glob.glob(os.path.join(OUT, "*", ""))):
        recs = {}
        for f in glob.glob(os.path.join(src_dir, "*.json")):
            r = json.load(open(f))
            recs[r["engine"]] = r
        if not recs:
            continue
        es = [e for e in ENGINES if e in recs] + sorted(set(recs) - set(ENGINES))
        first = next(iter(recs.values()))
        lines += [f"## {first['source']} ({first['base_triples']:,} triples in the base data)", "",
                  "| | " + " | ".join(es) + " |", "|---|" + "---:|" * len(es)]
        lines.append("| load (s) | " + " | ".join(str(recs[e].get("load", {}).get("load_s", "")) for e in es) + " |")
        sizes = sorted({int(s) for r in recs.values() for s in r["sizes"]})
        for op in ("insert", "delete"):
            for s in sizes:
                cells = []
                for e in es:
                    r = recs[e]["sizes"].get(str(s), {}).get(op)
                    if not r:
                        cells.append("")
                        continue
                    bad = "!" if r.get("failed") or not r.get("count_ok", True) else ""
                    cells.append(f"{fmt(r.get('us_per_triple'))} ({fmt(r.get('p50_ms'))}){bad}")
                lines.append(f"| {op} {s:,} | " + " | ".join(cells) + " |")
        names = sorted({n for r in recs.values() for n in r["derive"]}, key=lambda n: int(n.split("-")[1]))
        for n in names:
            cells = []
            for e in es:
                d = recs[e]["derive"].get(n)
                if not d:
                    cells.append("")
                    continue
                bad = "!" if d.get("error") or d.get("delete_error") or not d.get("count_ok") else ""
                cells.append(f"{fmt(d.get('insert_ms'))} / {fmt(d.get('delete_ms'))}{bad}")
            rows = next((recs[e]["derive"][n]["rows"] for e in es if n in recs[e]["derive"]), "")
            lines.append(f"| {n} ({rows:,} rows) | " + " | ".join(cells) + " |")
        lines.append("| store after (MB) | " + " | ".join(
            fmt((recs[e].get("disk_bytes_after") or 0) / 1e6) for e in es) + " |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines))
    print(os.path.join(OUT, "report.md"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("generate")
    g.add_argument("--source", required=True)
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--max-size", type=int, default=1_000_000)
    r = sp.add_parser("run")
    r.add_argument("--source", required=True)
    r.add_argument("--engine", required=True)
    r.add_argument("--skip-load", action="store_true")
    r.add_argument("--sizes", type=int, nargs="*", help="only these batch sizes (default: all)")
    r.add_argument("--no-derive", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"generate": cmd_generate, "run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
