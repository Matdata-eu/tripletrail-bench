#!/usr/bin/env python3
"""RINF query-shape suite (tripletrail-bench #64): facets, top-k, stars, chains, wide tables and
anti-joins on real RINF data, each query in a rows form and a count form (queries.py).

  run_rinfshapes.py prepare --dataset rinf-all|rinf-<code>
      $BENCH_WORK/data/rinf-<x>.nt -> $BENCH_WORK/data/rinfshapes-<x>.nt, without the triples
      that some engine cannot load (see clean())
  run_rinfshapes.py run --dataset rinf-all|rinf-<code> --engine E [--skip-load] [--warm 7]
      load rinfshapes-<x> (engines/E.sh load), start the engine, then per query and form: one
      cold run, 2 warm-ups and --warm timed runs (median)
      -> results/rinfshapes/<dataset>/<engine>.json
  run_rinfshapes.py report   -> results/rinfshapes/report.md

The data is fetched by run_suite.sh (suites/data/fetch_rinf.py) and never committed. Times are
wall-clock at the client over HTTP, all rows read (SPARQL JSON results). TripleTrail's result
cache is off (engines/tripletrail.sh) and QLever's is cleared before each run.
"""
import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, V2)
sys.path.insert(0, HERE)
from queries import QUERIES, SHAPES, BY_ID  # noqa: E402

WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
OUT = os.path.join(V2, "results", "rinfshapes")
ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb"]
TIMEOUT = 300


def engine(e, *args):
    r = subprocess.run([os.path.join(V2, "engines", f"{e}.sh"), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{e}.sh {' '.join(args)} failed:\n{r.stderr[-3000:]}")
    return r.stdout.strip()


def store_name(dataset):
    """The engines' dataset: the cleaned copy of the RINF file (rinf-all -> rinfshapes-all)."""
    return "rinfshapes-" + dataset.removeprefix("rinf-")


# RINF as ERA publishes it has triples that stop some engines' bulk loads. None of them is read by
# the suite's queries, so they are left out for every engine alike:
# Lines over 4 MiB (era:digitalSchematicOverview drawings as WKT, up to 16 MiB): Oxigraph's
# N-Triples line buffer is 16 MiB, and QLever's parallel parser needs a block end every 10 MB.
LONG_LINE = 4 * 1024 * 1024
NUMBER = re.compile(rb'"([^"]*)"\^\^<http://www\.w3\.org/2001/XMLSchema#(integer|decimal|double|float|int|long)> \.$')
VALID_NUMBER = {
    b"integer": re.compile(rb"[+-]?\d+"), b"int": re.compile(rb"[+-]?\d+"), b"long": re.compile(rb"[+-]?\d+"),
    b"decimal": re.compile(rb"[+-]?(\d+(\.\d*)?|\.\d+)"),
    b"double": re.compile(rb"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?|[+-]?INF|NaN"),
}
VALID_NUMBER[b"float"] = VALID_NUMBER[b"double"]
# Geometries Jena's spatial index refuses: a LINESTRING of one point, and geo:asWKT values that
# are not WKT literals (plain "NYA", not yet available).
WKT = re.compile(rb'<http://www\.opengis\.net/ont/geosparql#asWKT> (?!"[^"]*"\^\^<http://www\.opengis\.net/ont/geosparql#wktLiteral>)')
ONE_POINT_LINE = re.compile(rb'"(<[^>]*> )?LINESTRING ?\( *[^,()]+\)"\^\^')


def clean(line):
    """Why a line of N-Triples is left out, or None to keep it."""
    if len(line) > LONG_LINE:
        return "line over 4 MiB"
    m = NUMBER.search(line.rstrip())
    if m and not VALID_NUMBER[m.group(2)].fullmatch(m.group(1)):
        return f"not a number: xsd:{m.group(2).decode()}"
    if WKT.search(line):
        return "geo:asWKT not a WKT literal"
    if ONE_POINT_LINE.search(line):
        return "LINESTRING of one point"
    return None


def cmd_prepare(a):
    src = os.path.join(WORK, "data", f"{a.dataset}.nt")
    dst = os.path.join(WORK, "data", f"{store_name(a.dataset)}.nt")
    kept, left_out = 0, {}
    with open(src, "rb") as f, open(dst + ".part", "wb") as out:
        for line in f:
            why = clean(line)
            if why:
                left_out[why] = left_out.get(why, 0) + 1
            else:
                out.write(line)
                kept += 1
    os.replace(dst + ".part", dst)
    json.dump({"source": a.dataset, "triples": kept, "left_out": left_out}, open(dst[:-3] + ".meta.json", "w"))
    print(f"{dst}: {kept} triples, left out {left_out}")


def timed(cl, text, warm):
    """Cold run, 2 warm-ups, `warm` timed runs: the summary and the last answer's rows."""
    runs, rows = [], []
    for _ in range(3 + warm):
        cl.before_run()
        dt, rows = cl.query(text, TIMEOUT)
        runs.append(dt * 1000)
    timed_runs = runs[3:]
    return {"cold_ms": round(runs[0], 3), "median_ms": round(statistics.median(timed_runs), 3),
            "min_ms": round(min(timed_runs), 3), "runs": [round(t, 3) for t in runs]}, rows


def cmd_run(a):
    from run import Sparql
    store = store_name(a.dataset)
    meta = json.load(open(os.path.join(WORK, "data", f"{store}.meta.json")))
    os.makedirs(os.path.join(OUT, a.dataset), exist_ok=True)
    rec = {"engine": a.engine, "dataset": a.dataset, "triples": meta["triples"],
           "left_out": meta["left_out"], "warm_runs": a.warm, "queries": {}}
    if not a.skip_load:
        print(f"loading {store} into {a.engine}", flush=True)
        rec["load"] = json.loads(engine(a.engine, "load", store).splitlines()[-1])
    engine(a.engine, "start", store)
    cl = Sparql(a.engine, engine(a.engine, "endpoint"))
    try:
        for q in QUERIES:
            r = {}
            try:
                r["rows"], rows = timed(cl, q.rows, a.warm)
                r["rows"]["n"] = len(rows)
                r["count"], counted = timed(cl, q.count, a.warm)
                r["count"]["n"] = int(counted[0][0]) if counted else None
                r["status"] = "ok"
                if r["count"]["n"] != len(rows):  # the two forms must count the same solutions
                    r["status"] = "forms differ"
            except Exception as e:  # noqa: BLE001 - recorded, not hidden
                r.update(status="failed", reason=str(e)[:600])
            rec["queries"][q.id] = r
            print(f"{a.engine} {a.dataset} {q.id}: {r['status']} "
                  f"{r.get('rows', {}).get('median_ms', '')} / {r.get('count', {}).get('median_ms', '')} ms", flush=True)
    finally:
        engine(a.engine, "stop")
    path = os.path.join(OUT, a.dataset, f"{a.engine}.json")
    json.dump(rec, open(path, "w"), indent=1)
    print(path)


def fmt(ms):
    if ms is None:
        return ""
    return f"{ms:.1f}" if ms < 100 else f"{ms:,.0f}"


def cell(r, form="rows"):
    if r.get("status") not in ("ok", "forms differ"):
        return r.get("status", "")
    return fmt(r[form]["median_ms"])


def dataset_table(ds, recs):
    es = [e for e in ENGINES if e in recs] + sorted(set(recs) - set(ENGINES))
    triples = next((r["triples"] for r in recs.values() if r.get("triples")), None)
    lines = [f"## {ds}" + (f" ({triples:,} triples)" if triples else ""), "",
             "| query | " + " | ".join(f"{e} rows | {e} count" for e in es) + " | rows |",
             "|---|" + "---:|---:|" * len(es) + "---|"]
    if any("load" in r for r in recs.values()):
        lines.append("| load (s) | " + " | ".join(f"{recs[e].get('load', {}).get('load_s', '')} | " for e in es) + " |")
    for shape, label in SHAPES.items():
        qs = [q for q in QUERIES if q.shape == shape]
        lines.append(f"| **{label}** |" + " |" * (2 * len(es) + 1))
        for q in qs:
            rs = {e: recs[e]["queries"].get(q.id, {}) for e in es}
            cells = [f"{cell(rs[e])} | {cell(rs[e], 'count')}" for e in es]
            n = {e: r["rows"]["n"] for e, r in rs.items() if r.get("status") in ("ok", "forms differ")}
            note = ", ".join(f"{e}={v:,}" for e, v in n.items()) if len(set(n.values())) > 1 else \
                (f"{next(iter(n.values())):,}" if n else "")
            if len(set(n.values())) > 1:
                note = "**differ:** " + note
            bad = [e for e, r in rs.items() if r.get("status") == "forms differ"]
            if bad:
                note += f" (count form differs on {', '.join(bad)})"
            name = q.id + (f" (of {q.control_of})" if q.control_of else "")
            lines.append(f"| {name} | " + " | ".join(cells) + f" | {note} |")
    lines.append("")
    # How much of the rows time is the join: count time / rows time, per engine.
    lines += ["Count time as a share of rows time (the rest is writing and reading the rows):", "",
              "| query | " + " | ".join(es) + " |", "|---|" + "---:|" * len(es)]
    for q in QUERIES:
        cells = []
        for e in es:
            r = recs[e]["queries"].get(q.id, {})
            ok = r.get("status") in ("ok", "forms differ") and r["rows"]["median_ms"] > 0
            cells.append(f"{r['count']['median_ms'] / r['rows']['median_ms']:.2f}" if ok else "")
        lines.append(f"| {q.id} | " + " | ".join(cells) + " |")
    return lines + [""]


def cmd_report(_a):
    lines = ["# RINF query-shape suite", "",
             "Queries on public RINF data grouped by shape (`suites/rinfshapes/queries.py`), each "
             "in a rows form and a count form. Times in ms: the median of the warm runs, over HTTP "
             "with every row read. Engines that give different row counts are flagged; a count "
             "form whose number differs from its rows form's row count is flagged too. An "
             "ablation control repeats a top-k or facet query with patterns taken out.", ""]
    for d in sorted(glob.glob(os.path.join(OUT, "*", ""))):
        recs = {}
        for f in glob.glob(os.path.join(d, "*.json")):
            r = json.load(open(f))
            recs[r["engine"]] = r
        if recs:
            lines += dataset_table(os.path.basename(os.path.dirname(d)), recs)
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines))
    print(os.path.join(OUT, "report.md"))


def cmd_queries(a):
    """Prints a query's rows and count forms (or all ids)."""
    if not a.id:
        print("\n".join(f"{q.id}\t{q.shape}\t{q.title}" for q in QUERIES))
        return
    q = BY_ID[a.id]
    print(f"# rows\n{q.rows}\n\n# count\n{q.count}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    pr = sp.add_parser("prepare")
    pr.add_argument("--dataset", default="rinf-all")
    r = sp.add_parser("run")
    r.add_argument("--dataset", default="rinf-all")
    r.add_argument("--engine", required=True)
    r.add_argument("--skip-load", action="store_true")
    r.add_argument("--warm", type=int, default=7)
    sp.add_parser("report")
    q = sp.add_parser("queries")
    q.add_argument("id", nargs="?")
    a = p.parse_args()
    {"prepare": cmd_prepare, "run": cmd_run, "report": cmd_report, "queries": cmd_queries}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
