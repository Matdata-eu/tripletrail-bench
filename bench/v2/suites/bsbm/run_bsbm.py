#!/usr/bin/env python3
"""Berlin SPARQL Benchmark (BSBM) on the SPARQL engines of benchmark v2.

  run_bsbm.py run --products N --engine E [--usecases explore,bi,update] [--skip-load]
      generate the dataset if needed (bsbm.sh generate N -> $BENCH_WORK/data/bsbm-N.nt), load it
      into E (engines/E.sh load bsbm-N), run the official BSBM test driver for each use case and
      write results/bsbm/bsbm-N/E.json. The update use case ("exploreAndUpdate") changes the
      store, so it runs last.
  run_bsbm.py report
      write results/bsbm/report.md from every results/bsbm/*/*.json.

Use cases (bsbmtools 0.2): explore (12 query templates, mix of 25 queries per run), bi (business
intelligence, 8 analytical templates) and update (explore mix plus INSERT DATA / DELETE WHERE).
The test driver draws parameters with a fixed seed (808080), so every engine sees the same
queries. Metrics: QMpH (query mixes per hour, single client) per use case and AQET (average
query execution time) per query template, as measured by the test driver at the client (HTTP
included). The average result count per template is kept to spot engines that answer
differently.

Env: BENCH_WORK, BSBM_RUNS / BSBM_WARMUP / BSBM_TIMEOUT_MS / BSBM_CLIENTS (see bsbm.sh).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
OUT = os.path.join(V2, "results", "bsbm")
ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb", "maplib"]
USECASES = {"explore": "explore", "bi": "bi", "update": "exploreAndUpdate"}
# The test driver cannot pass QLever's access token, which QLever requires for updates.
# The test driver asks for RDF/XML for DESCRIBE (explore Q9) and CONSTRUCT (Q12), which QLever
# does not serve (HTTP 406): QLever runs the mixes without them, so its QMpH is not comparable.
# maplib's endpoint (engines/maplib_server.py) answers CONSTRUCT as N-Triples and has no
# DESCRIBE, so it runs the explore mixes without them too. maplib 0.20.26 also rejects BI Q5
# ("Tried grouping on a variable `?country` that is not defined in the inner query": the query
# groups by a variable its subquery does not bind, which SPARQL allows).
# Per engine and use case: (query numbers to leave out, note).
_RDFXML = ("9 12", "{uc}: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for "
                   "RDF/XML, which {e} does not serve")
_MIX = {"explore": "explore", "update": "explore-and-update"}
SKIP = {"qlever": {uc: (_RDFXML[0], _RDFXML[1].format(uc=_MIX[uc], e="QLever")) for uc in ("explore", "update")},
        "maplib": {**{uc: (_RDFXML[0], _RDFXML[1].format(uc=_MIX[uc], e="the maplib endpoint"))
                      for uc in ("explore", "update")},
                   "bi": ("5", "BI Q5 skipped: maplib 0.20.26 rejects GROUP BY on a variable its "
                               "subquery does not bind")}}
# Templates whose "result count" the test driver measures in bytes of the RDF answer, which
# depends on the serialisation, so it is not compared between engines.
BYTE_RESULTS = {("explore", "9"), ("explore", "12")}
# Known causes of result counts that differ from the other engines (see wrong_counts).
WRONG_CAUSE = {"maplib": "maplib 0.20.26 returns one all-unbound row for a GROUP BY over no solutions "
                         "(SPARQL: no rows), e.g. for a product type without products"}
NO_UPDATE = {"qlever": "updates need QLever's access token, which the BSBM test driver cannot send"}


def sh(*cmd, capture=True, env=None):
    r = subprocess.run(cmd, capture_output=capture, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{(r.stderr or '')[-3000:]}")
    return (r.stdout or "").strip()


def engine(e, *args):
    return sh(os.path.join(V2, "engines", f"{e}.sh"), *args)


def failure_reason(err, e):
    """The test driver's error without its Java stack and URL-encoded query, plus the engine's own
    last error lines where it has a `logs` command (engines/maplib.sh)."""
    lines = [l for l in err.splitlines() if l.strip() and not l.lstrip().startswith("at ")
             and "%0A" not in l and "... " not in l]
    reason = "\n".join(lines[:12])[:1500]
    try:
        tail = [l for l in engine(e, "logs").splitlines() if "ERROR" in l or "Exception" in l][-3:]
        if tail:
            reason += "\nengine: " + "\n".join(tail)[:1500]
    except Exception:  # noqa: BLE001 - not every engine script has `logs`
        pass
    return reason


def update_endpoint(e, ep):
    if e in ("tripletrail", "oxigraph", "jena", "maplib"):
        return ep.rsplit("/query", 1)[0] + "/update"
    if e == "graphdb":
        return ep + "/statements"
    return None


def parse_xml(path):
    root = ET.parse(path).getroot()
    mix = root.find("querymix")
    num = lambda el, tag: float(el.findtext(tag)) if el.findtext(tag) not in (None, "") else None
    out = {k: num(mix, k) for k in ("querymixruns", "qmph", "cqet", "cqetg", "totalruntime",
                                     "minquerymixruntime", "maxquerymixruntime")}
    out["queries"] = {}
    for q in root.find("queries"):
        rec = {k: num(q, k) for k in ("executecount", "aqet", "aqetg", "qps", "minqet", "maxqet",
                                       "avgresults", "timeoutcount")}
        out["queries"][q.get("nr")] = rec
    return out


def cmd_run(a):
    ds = f"bsbm-{a.products}"
    if not os.path.exists(os.path.join(WORK, "data", f"{ds}.nt")):
        print(sh(os.path.join(HERE, "bsbm.sh"), "generate", str(a.products)))
    meta = json.load(open(os.path.join(WORK, "data", f"{ds}.meta.json")))
    os.makedirs(os.path.join(OUT, ds), exist_ok=True)
    path = os.path.join(OUT, ds, f"{a.engine}.json")
    rec = json.load(open(path)) if os.path.exists(path) else {}
    rec.update(engine=a.engine, dataset=ds, products=a.products, triples=meta["triples"],
               runs=int(os.environ.get("BSBM_RUNS", "50")), warmup=int(os.environ.get("BSBM_WARMUP", "10")),
               clients=int(os.environ.get("BSBM_CLIENTS", "1")))
    rec.setdefault("usecases", {})
    if not a.skip_load:
        print(f"loading {ds} into {a.engine}", flush=True)
        rec["load"] = json.loads(engine(a.engine, "load", ds).splitlines()[-1])
    else:
        engine(a.engine, "start", ds)
    ep = engine(a.engine, "endpoint")
    ucs = [u.strip() for u in a.usecases.split(",") if u.strip()]
    ucs.sort(key=lambda u: u == "update")  # the update mix changes the store: last
    try:
        for uc in ucs:
            if uc == "update" and a.engine in NO_UPDATE:
                rec["usecases"][uc] = {"status": "n/a", "reason": NO_UPDATE[a.engine]}
                continue
            xml = os.path.join(WORK, "bsbm", "out", f"{ds}.{a.engine}.{uc}.xml")
            args = [os.path.join(HERE, "bsbm.sh"), "testdriver", str(a.products), USECASES[uc], ep, xml]
            if uc == "update":
                args.append(update_endpoint(a.engine, ep))
            print(f"{a.engine} {ds} {uc}", flush=True)
            env = dict(os.environ)
            skip = SKIP.get(a.engine, {}).get(uc)
            if skip:
                env["BSBM_IGNORE"] = skip[0]
            try:
                log = sh(*args, env=env)
                res = parse_xml(xml)
                res["status"] = "ok"
                if "BSBM_IGNORE" in env:
                    res["note"] = skip[1]
                open(os.path.join(WORK, "bsbm", "out", f"{ds}.{a.engine}.{uc}.log"), "w").write(log)
            except Exception as e:  # noqa: BLE001 - recorded, not hidden
                res = {"status": "failed", "reason": failure_reason(str(e), a.engine)}
            rec["usecases"][uc] = res
            json.dump(rec, open(path, "w"), indent=1)
            print(f"  QMpH {res.get('qmph')}", flush=True)
    finally:
        engine(a.engine, "stop")
    json.dump(rec, open(path, "w"), indent=1)


def skipped(engine, uc, q):
    """True when the run left template q out for this engine (SKIP)."""
    return q in SKIP.get(engine, {}).get(uc, ("", ""))[0].split()


def note_of(engine, uc, u):
    """A use case's note: today's SKIP text when the run had one (older runs stored older wording)."""
    if not u or not u.get("note"):
        return ""
    return SKIP.get(engine, {}).get(uc, ("", u["note"]))[1]


def wrong_counts(recs, uc):
    """{engine: [templates]} where an engine's average result count differs from what most engines
    return. Its QMpH then includes wrong answers. Byte-counted and skipped templates are left out."""
    out = {}
    qs = {q for r in recs.values() for q in r.get("usecases", {}).get(uc, {}).get("queries", {})}
    for q in sorted(qs, key=int):
        if (uc, q) in BYTE_RESULTS:
            continue
        counts = {}
        for e, r in recs.items():
            s = r.get("usecases", {}).get(uc, {}).get("queries", {}).get(q)
            if s and s.get("executecount") and s.get("avgresults") is not None and not skipped(e, uc, q):
                counts[e] = round(s["avgresults"], 3)
        vals = list(counts.values())
        if len(set(vals)) <= 1:
            continue
        top = max(set(vals), key=vals.count)
        if vals.count(top) * 2 <= len(vals):
            continue  # no majority: nothing to say which engine is right
        for e, c in counts.items():
            if c != top:
                out.setdefault(e, []).append(f"Q{q}")
    return out


def fmt_ms(s):
    return "" if s is None else (f"{s * 1000:.1f}" if s * 1000 < 100 else f"{s * 1000:.0f}")


def cmd_report(a):
    lines = ["# BSBM results", "",
             "Berlin SPARQL Benchmark with the official bsbmtools 0.2 test driver (seed 808080, single "
             "client). QMpH = query mixes per hour (higher is better); per-template times are AQET in ms "
             "(lower is better), measured at the client. A result-count column that differs between "
             "engines marks a template where an engine answers differently.", ""]
    for d in sorted(glob.glob(os.path.join(OUT, "bsbm-*")), key=lambda p: int(p.rsplit("-", 1)[1])):
        recs = {}
        for f in glob.glob(os.path.join(d, "*.json")):
            r = json.load(open(f))
            recs[r["engine"]] = r
        if not recs:
            continue
        es = [e for e in ENGINES if e in recs] + sorted(set(recs) - set(ENGINES))
        any_r = next(iter(recs.values()))
        lines += [f"## {os.path.basename(d)} ({any_r['products']:,} products, {any_r['triples']:,} triples)", "",
                  f"{any_r['runs']} timed query mixes after {any_r['warmup']} warm-up mixes.", "",
                  "| | " + " | ".join(es) + " |", "|---|" + "---:|" * len(es)]
        lines.append("| load (s) | " + " | ".join(
            f"{recs[e].get('load', {}).get('load_s', '')}" for e in es) + " |")
        wrong = {uc: wrong_counts(recs, uc) for uc in ("explore", "bi")}
        for uc in USECASES:
            cells = []
            for e in es:
                u = recs[e].get("usecases", {}).get(uc)
                cells.append("" if u is None else (f"{u['qmph']:,.0f}" + (" *" if u.get("note") else "")
                                                   + (" †" if e in wrong.get(uc, {}) else "")
                                                   if u.get("status") == "ok" else u["status"]))
            lines.append(f"| QMpH {uc} | " + " | ".join(cells) + " |")
        notes = sorted({f"{e}: {note_of(e, uc, u)}" for e in es for uc, u in recs[e].get("usecases", {}).items()
                        if note_of(e, uc, u)})
        lines += [""] + [f"\\* {n}" for n in notes]
        for uc, w in wrong.items():
            for e, qs in w.items():
                lines.append(f"† {e}: {uc} result counts differ from the other engines on {', '.join(qs)}, so this "
                             "QMpH includes wrong answers" + (f" ({WRONG_CAUSE[e]})" if e in WRONG_CAUSE else ""))
        lines += [""] if notes or any(wrong.values()) else []
        for uc in ("explore", "bi"):
            qs = sorted({q for e in es for q in recs[e].get("usecases", {}).get(uc, {}).get("queries", {})}, key=int)
            if not qs:
                continue
            lines += [f"### {uc}: AQET per template (ms), average result count", "",
                      "| query | " + " | ".join(es) + " | results |", "|---|" + "---:|" * len(es) + "---|"]
            for q in qs:
                if all(not recs[e].get("usecases", {}).get(uc, {}).get("queries", {}).get(q, {}).get("executecount")
                       for e in es):
                    continue  # in the template set but not in the use case's query mix (explore Q6)
                cells, counts = [], []
                for e in es:
                    r = recs[e].get("usecases", {}).get(uc, {}).get("queries", {}).get(q)
                    if not r:
                        cells.append("")
                        continue
                    if skipped(e, uc, q):
                        cells.append("skipped")
                        continue
                    t = fmt_ms(r["aqet"])
                    if r.get("timeoutcount"):
                        t += f" ({int(r['timeoutcount'])} timeouts)"
                    cells.append(t)
                    if r.get("avgresults") is not None:
                        counts.append(f"{e}={r['avgresults']:g}")
                same = len({c.split("=")[1] for c in counts}) <= 1
                note = "same" if same else ", ".join(counts)
                if (uc, q) in BYTE_RESULTS:
                    note = "bytes (DESCRIBE/CONSTRUCT), not compared"
                lines.append(f"| Q{q} | " + " | ".join(cells) + f" | {note} |")
            lines.append("")
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines))
    print(os.path.join(OUT, "report.md"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--products", type=int, default=2785)
    r.add_argument("--engine", required=True)
    r.add_argument("--usecases", default="explore,bi,update")
    r.add_argument("--skip-load", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
