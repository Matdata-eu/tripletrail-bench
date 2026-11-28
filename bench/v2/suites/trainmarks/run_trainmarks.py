#!/usr/bin/env python3
"""Trainmarks-style RDF benchmark on the SPARQL engines of benchmark v2.

Trainmarks (https://github.com/DataTreehouse/trainmarks, report at
https://datatreehouse.github.io/trainmarks) compares RDF frameworks on a synthetic e-commerce
graph (customers, products, orders; fixed seed 42) at about 100K, 1M and 10M triples: loading
the data, and six SPARQL queries (count, group-by with aggregates, 3-entity join, OPTIONAL with
aggregates, CONSTRUCT, DELETE/INSERT). The Trainmarks repository has no license file, so no
code or queries of it are copied here: `fetch` clones a pinned commit at run time, its data
generator runs in a Python container, and its query files are read from the clone.

  run_trainmarks.py fetch
  run_trainmarks.py generate            -> $BENCH_WORK/data/trainmarks-{medium,large,xlarge}.nt
  run_trainmarks.py run --scale medium|large|xlarge --engine E [--skip-load] [--warm 5]
      load the data (engines/E.sh load; the time is Trainmarks' "read N-Triples" step, on our
      engines a bulk load into the on-disk store), restart the engine, then for q1-q5 one cold
      run, 1 warm-up and --warm timed runs; q6 (the update) runs once, last.
      -> results/trainmarks/<scale>/<engine>.json
  run_trainmarks.py report              -> results/trainmarks/report.md

Times are wall-clock at the client, HTTP and fetching all rows included (Trainmarks times the
Python and Java libraries in-process, so the in-process numbers on its site are not directly
comparable to these server numbers; its QLever, GraphDB and Virtuoso runs are over HTTP too).
maplib, which Trainmarks runs in-process, is served here by engines/maplib_server.py so that it
is timed over HTTP like the other engines.
"""
import argparse
import glob
import json
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, V2)
from majority import wrong as off_majority  # noqa: E402
from run import Sparql  # noqa: E402

WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
OUT = os.path.join(V2, "results", "trainmarks")
SRC = os.path.join(WORK, "trainmarks", "src")
GEN = os.path.join(WORK, "trainmarks", "gen")
REPO = "https://github.com/DataTreehouse/trainmarks.git"
COMMIT = "5679536692be63ecda86a2861c63780c955a4e7a"  # 2026-09-01
PY_IMAGE = os.environ.get("TRAINMARKS_PY_IMAGE", "mirror.gcr.io/library/python:3.12-slim")
SCALES = ["medium", "large", "xlarge"]
QUERIES = ["q1_count", "q2_customer_orders", "q3_join_3_entities", "q4_optional_aggregation", "q5_construct"]
UPDATE = "q6_delete_insert"
ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb", "maplib"]
TIMEOUT = 600


def sh(*cmd, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{(r.stderr or '')[-3000:]}")
    return (r.stdout or "").strip()


def engine(e, *args):
    return sh(os.path.join(V2, "engines", f"{e}.sh"), *args)


def cmd_fetch(_a=None):
    if os.path.exists(os.path.join(SRC, ".git")):
        return
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    sh("git", "clone", "-q", REPO, SRC)
    sh("git", "-C", SRC, "checkout", "-q", COMMIT)


def cmd_generate(_a):
    cmd_fetch()
    os.makedirs(GEN, exist_ok=True)
    # The generator only uses the standard library; it writes data/ and queries/ in its cwd.
    sh("docker", "run", "--rm", "--network", "none", "-u", f"{os.getuid()}:{os.getgid()}",
       "-v", f"{SRC}:/src:ro", "-v", f"{GEN}:/gen", "-w", "/gen", PY_IMAGE,
       "python3", "/src/generate_data.py", capture=False)
    os.makedirs(os.path.join(WORK, "data"), exist_ok=True)
    for s in SCALES:
        dst = os.path.join(WORK, "data", f"trainmarks-{s}.nt")
        os.replace(os.path.join(GEN, "data", f"{s}.nt"), dst)
        n = sum(1 for line in open(dst, "rb") if line.strip())
        json.dump({"scale": s, "triples": n}, open(dst[:-3] + ".meta.json", "w"))
        print(f"{dst}: {n} triples")


def query_text(name):
    for d in (os.path.join(GEN, "queries"), os.path.join(SRC, "queries")):
        p = os.path.join(d, f"{name}.rq")
        if os.path.exists(p):
            return open(p).read()
    sys.exit(f"no {name}.rq: run `run_trainmarks.py fetch` (and generate)")


def construct(cl, text):
    """CONSTRUCT over HTTP, N-Triples (or Turtle) answer; 'rows' = distinct triples (lines; for
    Turtle roughly)."""
    data = {"query": text}
    if cl.engine == "qlever":
        data.update(timeout=f"{TIMEOUT}s", **{"access-token": "benchtoken"})
    t = time.perf_counter()
    r = cl.s.post(cl.endpoint, data=data, timeout=TIMEOUT + 60,
                  headers={"Accept": "application/n-triples, text/turtle;q=0.9"})
    body = r.content
    dt = time.perf_counter() - t
    cl.s.close()  # a fresh connection for the next request, see run.Sparql
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {body[:600].decode(errors='replace')}")
    # Distinct lines: a CONSTRUCT answer is a graph, but QLever writes one triple per solution,
    # duplicates included.
    lines = {ln for ln in body.decode().splitlines() if ln.strip() and not ln.lstrip().startswith(("@prefix", "PREFIX"))}
    return dt, [[ln] for ln in sorted(lines)]


def summary(ts):
    return {"n": len(ts), "median_ms": round(statistics.median(ts) * 1000, 3),
            "min_ms": round(min(ts) * 1000, 3), "max_ms": round(max(ts) * 1000, 3)} if ts else {}


def cmd_run(a):
    ds = f"trainmarks-{a.scale}"
    meta = json.load(open(os.path.join(WORK, "data", f"{ds}.meta.json")))
    os.makedirs(os.path.join(OUT, a.scale), exist_ok=True)
    path = os.path.join(OUT, a.scale, f"{a.engine}.json")
    rec = {"engine": a.engine, "scale": a.scale, "triples": meta["triples"], "warm_runs": a.warm,
           "queries": {}}
    if not a.skip_load:
        print(f"loading {ds} into {a.engine}", flush=True)
        rec["load"] = json.loads(engine(a.engine, "load", ds).splitlines()[-1])
    engine(a.engine, "start", ds)
    cl = Sparql(a.engine, engine(a.engine, "endpoint"))
    try:
        for q in QUERIES:
            text = query_text(q)
            r = {"runs": []}
            try:
                for i in range(2 + a.warm):
                    cl.before_run()
                    dt, rows = construct(cl, text) if q == "q5_construct" else cl.query(text, TIMEOUT)
                    r["runs"].append(round(dt * 1000, 3))
                    r["rows"] = len(rows)
                    r["first_row"] = rows[0][:4] if rows else None
                r["status"] = "ok"
                r["cold_ms"] = r["runs"][0]
                r["warm"] = summary([t / 1000 for t in r["runs"][2:]])
            except Exception as e:  # noqa: BLE001 - recorded, not hidden
                r.update(status="failed", reason=str(e)[:600])
            rec["queries"][q] = r
            print(f"{a.engine} {a.scale} {q}: {r.get('warm', {}).get('median_ms', r.get('reason', ''))} ms", flush=True)
        try:
            dt = cl.update(query_text(UPDATE), TIMEOUT)
            rec["queries"][UPDATE] = {"status": "ok", "ms": round(dt * 1000, 3)}
        except Exception as e:  # noqa: BLE001
            rec["queries"][UPDATE] = {"status": "failed", "reason": str(e)[:600]}
        print(f"{a.engine} {a.scale} {UPDATE}: {rec['queries'][UPDATE]}", flush=True)
    finally:
        engine(a.engine, "stop")
    json.dump(rec, open(path, "w"), indent=1)
    print(path)


def fmt(ms):
    if ms is None:
        return ""
    return f"{ms:.1f}" if ms < 100 else f"{ms:,.0f}"


def cmd_report(_a):
    lines = ["# Trainmarks-style results", "",
             "Synthetic e-commerce data and queries from Trainmarks (seed 42), run over HTTP against "
             "each engine's SPARQL endpoint. Load = bulk load of the N-Triples file into the engine's "
             "store (s). Query times in ms: median of the warm runs (cold run in brackets); q6 is the "
             "DELETE/INSERT update, run once. Row counts that differ between engines are flagged; an "
             "engine whose row count differs from the majority (at least two engines, more than half "
             "of those that answered) answered wrongly: its time is struck out and left out of its "
             "geometric mean. "
             "Geometric mean: of the warm medians of the five read queries q1-q5 (not the update), "
             "over the queries the engine answered correctly; fewer than 5 is marked. "
             "maplib keeps its data in memory only: its load is reading the file into RAM, behind a "
             "small HTTP wrapper (engines/maplib_server.py).", ""]
    for s in SCALES:
        recs = {}
        for f in glob.glob(os.path.join(OUT, s, "*.json")):
            r = json.load(open(f))
            recs[r["engine"]] = r
        if not recs:
            continue
        es = [e for e in ENGINES if e in recs] + sorted(set(recs) - set(ENGINES))
        lines += [f"## {s} ({next(iter(recs.values()))['triples']:,} triples)", "",
                  "| | " + " | ".join(es) + " | rows |", "|---|" + "---:|" * len(es) + "---|",
                  "| load (s) | " + " | ".join(str(recs[e].get("load", {}).get("load_s", "")) for e in es) + " | |"]
        bad = {q: off_majority({e: recs[e]["queries"][q]["rows"] for e in es
                                if recs[e]["queries"].get(q, {}).get("status") == "ok" and "rows" in recs[e]["queries"][q]})
               for q in QUERIES}
        for q in QUERIES + [UPDATE]:
            cells, rows = [], {}
            for e in es:
                r = recs[e]["queries"].get(q, {})
                if r.get("status") != "ok":
                    cells.append(r.get("status", ""))
                elif q == UPDATE:
                    cells.append(fmt(r["ms"]))
                else:
                    t = f"{fmt(r['warm']['median_ms'])} ({fmt(r['cold_ms'])})"
                    cells.append(f"~~{t}~~ wrong" if e in bad.get(q, ()) else t)
                    rows[e] = r["rows"]
            note = "" if len(set(rows.values())) <= 1 else ", ".join(f"{e}={n}" for e, n in rows.items())
            if rows and not note:
                note = str(next(iter(rows.values())))
            lines.append(f"| {q} | " + " | ".join(cells) + f" | {note} |")
        gm = []
        for e in es:
            ms = [r["warm"]["median_ms"] for q in QUERIES
                  for r in [recs[e]["queries"].get(q, {})] if r.get("status") == "ok" and r.get("warm")
                  and e not in bad.get(q, ())]
            g = fmt(statistics.geometric_mean(ms)) if ms else ""
            gm.append(g if len(ms) == len(QUERIES) or not ms else f"{g} ({len(ms)} of {len(QUERIES)})")
        lines.append("| geometric mean q1-q5 | " + " | ".join(gm) + " | |")
        lines.append("")
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines))
    print(os.path.join(OUT, "report.md"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("fetch")
    sp.add_parser("generate")
    r = sp.add_parser("run")
    r.add_argument("--scale", choices=SCALES, default="large")
    r.add_argument("--engine", required=True)
    r.add_argument("--skip-load", action="store_true")
    r.add_argument("--warm", type=int, default=5)
    sp.add_parser("report")
    a = p.parse_args()
    {"fetch": cmd_fetch, "generate": cmd_generate, "run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
