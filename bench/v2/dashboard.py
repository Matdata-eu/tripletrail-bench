#!/usr/bin/env python3
"""Write the CSV files the benchmark dashboard reads, from the results in bench/v2/results.

    python3 bench/v2/dashboard.py [results dir] [out dir]

Defaults: bench/v2/results and bench/v2/results/dashboard. The collect job of the "Benchmarks
(manual)" workflow runs this before it commits a run's results, so every results pull request
carries the dashboard files that match it. Refreshing the dashboard is then: upload these files
to it (see bench/v2/results/dashboard/README.md).

Files (plain CSV, no quoted fields):
  summary.csv            Sparqloscope: dataset,engine,geomean_ms,load_s,answered,timed_out,failed
  categories.csv         Sparqloscope: dataset,category,engine,ms
  bsbm_qmph.csv          BSBM: scale,usecase,engine,qmph,note
  bsbm_aqet.csv          BSBM: scale,usecase,query,engine,ms
  trainmarks_load.csv    Trainmarks: scale,engine,load_s
  trainmarks_queries.csv Trainmarks: scale,query,engine,warm_ms,cold_ms
  spatial_load.csv       bench v2: dataset,engine,load_s,disk_gib,triples
  spatial_queries.csv    bench v2: dataset,family,query,engine,status,cold_ms,p50_ms,p95_ms,check,check_note;
                         check is compare.py's verdict (ok, mismatch, unchecked); a mismatch has the
                         status "wrong answer", so it counts as not answered everywhere (#96)
  rinfshapes_queries.csv RINF shapes: dataset,shape,query,control_of,engine,status,rows_ms,count_ms,rows,title
  provenance.csv         suite,dataset,machine,cpus,commit,date,engines: where and when each result ran
"""
import csv
import glob
import json
import math
import os
import re
import sys

try:
    import yaml
except ImportError:  # Sparqloscope's files are YAML; without PyYAML its two CSVs are left as they are
    yaml = None

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compare import verdicts  # noqa: E402
ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb", "maplib", "postgis"]
# bench v2 datasets in the order the dashboard shows them; any other dataset folder follows.
V2_DATASETS = ["small", "large", "osm_norway", "osm_benelux", "osm_europe", "osm_planet"]
# Same categories as suites/sparqloscope/run_sparqloscope.py (first match wins).
CATEGORIES = [
    ("join", r"^(join|multicolumn-join)"), ("optional", r"^optional"), ("minus", r"^minus"),
    ("exists", r"^exists"), ("union", r"^union"), ("group by / distinct", r"^(group-by|distinct)"),
    ("property path", r"^transitive-path"), ("regex / string", r"^(regex|str)"),
    ("result size", r"^result-size"), ("numeric", r"^numeric"), ("filter / language", r"^filter"),
    ("date", r"^date"), ("count", r"^number-of"),
]


def category(qid):
    for name, pat in CATEGORIES:
        if re.search(pat, qid):
            return name
    return "other"


def gmean(xs):
    return math.exp(sum(math.log(max(x, 1e-4)) for x in xs) / len(xs)) if xs else None


def num(x, digits=3):
    if x is None:
        return ""
    s = f"{x:.{digits}f}".rstrip("0").rstrip(".")
    return s or "0"


def clean(s):
    return str(s).replace(",", ";").replace("\n", " ")


def write(out, name, cols, rows):
    with open(os.path.join(out, name), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)


def ordered(names):
    return [e for e in ENGINES if e in names] + sorted(set(names) - set(ENGINES))


def sparqloscope(res):
    summary, cats = [], []
    for d in sorted(glob.glob(os.path.join(res, "sparqloscope", "*", ""))):
        ds = os.path.basename(os.path.dirname(d))
        docs = {}
        for f in glob.glob(os.path.join(d, f"{ds}.*.results.yaml")):
            doc = yaml.safe_load(open(f))
            docs[doc.get("engine") or f.split(".")[-3]] = doc
        for e in ordered(docs):
            doc = docs[e]
            to = doc.get("timeout", 180)
            times, ok, fail, tout, bycat = [], 0, 0, 0, {}
            for r in doc["queries"]:
                t = r.get("runtime_info", {}).get("client_time", 0)
                res_ = r.get("results")
                if isinstance(res_, str) and res_.startswith("Exception"):
                    msg = res_.lower()
                    if "timeout" in msg or "timed out" in msg or "cancel" in msg:
                        tout += 1
                    else:
                        fail += 1
                    t = 2 * to
                else:
                    ok += 1
                times.append(t)
                bycat.setdefault(category(r["query"]), []).append(t)
            load = doc.get("load", {}).get("load_s")
            summary.append([ds, e, num(gmean(times) * 1000), num(load), ok, tout, fail])
            for c, _ in CATEGORIES + [("other", "")]:
                if c in bycat:
                    cats.append([ds, c, e, num(gmean(bycat[c]) * 1000)])
    return summary, cats


def bsbm(res):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "suites", "bsbm"))
    from run_bsbm import WRONG_CAUSE, note_of, wrong_counts
    qmph, aqet = [], []
    for d in sorted(glob.glob(os.path.join(res, "bsbm", "bsbm-*", "")), key=lambda p: int(p.rstrip("/").split("-")[-1])):
        scale = os.path.basename(os.path.dirname(d))
        recs = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(d, "*.json"))}
        recs_by_engine = {r.get("engine", k): r for k, r in recs.items()}
        for uc in ["explore", "bi", "update"]:
            wrong = wrong_counts(recs_by_engine, uc) if uc != "update" else {}
            for e in ordered(recs):
                u = recs[e].get("usecases", {}).get(uc)
                note = note_of(recs[e].get("engine", e), uc, u)
                if e in wrong:
                    note = "; ".join(filter(None, [note, f"wrong result counts on {' '.join(wrong[e])}"
                                                         + (f" ({WRONG_CAUSE[e]})" if e in WRONG_CAUSE else "")]))
                qmph.append([scale, uc, e, num(u.get("qmph"), 2) if u else "", clean(note)])
                if not u or uc == "update":
                    continue
                for q, s in sorted(u.get("queries", {}).items(), key=lambda kv: int(kv[0])):
                    # Explore Q9 and Q12 (DESCRIBE, CONSTRUCT) are left out: QLever skips them.
                    if uc == "explore" and q in ("9", "12"):
                        continue
                    if s.get("aqet"):
                        aqet.append([scale, uc, f"Q{q}", e, num(s["aqet"] * 1000)])
    return qmph, aqet


def trainmarks(res):
    load, queries = [], []
    for scale in ["medium", "large", "xlarge"]:
        d = os.path.join(res, "trainmarks", scale)
        recs = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(d, "*.json"))}
        for e in ordered(recs):
            r = recs[e]
            if r.get("load", {}).get("load_s") is not None:
                load.append([scale, e, num(r["load"]["load_s"])])
            for q, s in r.get("queries", {}).items():
                if s.get("status") != "ok":
                    continue
                warm = (s.get("warm") or {}).get("median_ms")
                if warm is None and s.get("runs"):
                    warm = s["runs"][0]
                if warm is None:  # the update query (q6) runs once and records only "ms"
                    warm = s.get("ms")
                cold = s.get("cold_ms") if s.get("warm") else None
                queries.append([scale, q, e, num(warm), num(cold)])
    return load, queries


def v2(res):
    """bench v2 (spatial and routing): per dataset and engine the load record (load.json) and
    one row per query record (<qid>.json), from results/<dataset>/<engine>/."""
    found = {os.path.basename(os.path.dirname(os.path.dirname(f)))
             for f in glob.glob(os.path.join(res, "*", "*", "load.json"))}
    load, queries = [], []
    for ds in [d for d in V2_DATASETS if d in found] + sorted(found - set(V2_DATASETS)):
        engines = [os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(res, ds, "*", "load.json"))]
        checks = verdicts(os.path.join(res, ds))
        for e in ordered(engines):
            for f in sorted(glob.glob(os.path.join(res, ds, e, "*.json"))):
                try:
                    r = json.load(open(f))
                except ValueError:
                    continue
                if os.path.basename(f) == "load.json":
                    disk = r.get("disk_bytes")
                    load.append([ds, e, num(r.get("load_s")), num(disk / 2**30 if disk else None), r.get("triples", "")])
                elif "qid" in r:
                    w = r.get("warm") or {}
                    status = r.get("status", "")
                    check, note = checks.get((r["qid"], e), ("", ""))
                    if check == "mismatch" and status.startswith("ok"):
                        # A fast wrong answer is no answer: left out of every mean and speedup.
                        status = "wrong answer"
                    queries.append([ds, clean(r.get("family", "")), r["qid"], e, status,
                                    num(r.get("cold_ms")), num(w.get("p50_ms")), num(w.get("p95_ms")),
                                    check, clean(note)])
    return load, queries


def rinfshapes(res):
    """RINF query-shape suite: one row per dataset, query and engine, in the order of the
    suite's queries (suites/rinfshapes/queries.py, which gives each query's shape and title);
    queries it no longer lists follow. rows_ms and count_ms are the warm medians of the rows
    and the count form, rows the rows the rows form returned."""
    try:
        sys.path.insert(0, os.path.join(HERE, "suites", "rinfshapes"))
        from queries import QUERIES
    except ImportError:
        QUERIES = []
    known = {q.id: q for q in QUERIES}
    rows = []
    for d in sorted(glob.glob(os.path.join(res, "rinfshapes", "*", ""))):
        ds = os.path.basename(os.path.dirname(d))
        recs = {}
        for f in glob.glob(os.path.join(d, "*.json")):
            try:
                r = json.load(open(f))
            except ValueError:
                continue
            recs[r.get("engine") or os.path.basename(f)[:-5]] = r
        ids = list(known) + sorted({q for r in recs.values() for q in r.get("queries", {})} - set(known))
        for qid in ids:
            q = known.get(qid)
            for e in ordered(recs):
                r = recs[e].get("queries", {}).get(qid)
                if r is None:
                    continue
                answered = r.get("status") in ("ok", "forms differ")
                rows.append([ds, q.shape if q else "", qid, (q.control_of or "") if q else "", e,
                             clean(r.get("status", "")),
                             num(r["rows"]["median_ms"]) if answered else "",
                             num(r["count"]["median_ms"]) if answered else "",
                             r["rows"].get("n", "") if answered else "",
                             clean(q.title) if q else ""])
    return rows


def provenance(res):
    """Per suite and dataset, the run manifests the results come from: for each engine, the
    latest ok run that measured it (a later run of one engine overwrites only that engine's
    results), one row per run with the engines it stands for. The run that measured the most
    engines comes first. For results without a manifest, their env file (no date, no engines)."""
    rows, seen = [], set()
    latest = {}  # (suite, dataset) -> engine -> manifest
    for f in glob.glob(os.path.join(res, "runs", "*.json")):
        try:
            m = json.load(open(f))
        except ValueError:
            continue
        for j in m.get("jobs", []):
            if j.get("status") != "ok":
                continue
            per = latest.setdefault((j["suite"], j["dataset"]), {})
            for e in j.get("engines", []):
                if e not in per or m.get("started", "") > per[e].get("started", ""):
                    per[e] = m
    for (suite, ds), per in sorted(latest.items()):
        seen.add((suite, ds))
        by_run = {}
        for e, m in per.items():
            by_run.setdefault(m.get("run"), (m, []))[1].append(e)
        for m, engines in sorted(by_run.values(), key=lambda x: (-len(x[1]), x[0].get("started", ""))):
            env = m.get("env", {})
            rows.append([suite, ds, m.get("machine", ""), env.get("cpus", ""),
                         m.get("commit", "")[:7], m.get("started", "")[:10], " ".join(sorted(engines))])

    for suite, pattern, strip in [("sparqloscope", "env-*.json", "env-"), ("bsbm", "env-*.json", "env-"),
                                  ("trainmarks", "env-*.json", "env-"), ("rinfshapes", "env-*.json", "env-"),
                                  ("v2", "*/env.json", None)]:
        for f in sorted(glob.glob(os.path.join(res, suite if suite != "v2" else "", pattern))):
            if strip:
                ds = os.path.basename(f)[len(strip):-5]
                if ".only-" in ds:  # a run of some engines only (suites/run_suite.sh)
                    continue
            else:
                ds = os.path.basename(os.path.dirname(f))
                if ds in ("sparqloscope", "bsbm", "trainmarks", "rinfshapes", "geographica", "runs"):
                    continue
            if (suite, ds) in seen:
                continue
            seen.add((suite, ds))
            env = json.load(open(f))
            machine = "ccx43" if env.get("cpus") == 16 and "EPYC" in env.get("cpu", "") else f"{env.get('cpus', '?')} vCPU container"
            rows.append([suite, ds, machine, env.get("cpus", ""), env.get("tripletrail_commit", "")[:7], "", ""])
    return sorted(rows, key=lambda r: (r[0], r[1]))  # stable: the widest run stays first


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(res, "dashboard")
    os.makedirs(out, exist_ok=True)
    if yaml:
        summary, cats = sparqloscope(res)
        write(out, "summary.csv", ["dataset", "engine", "geomean_ms", "load_s", "answered", "timed_out", "failed"], summary)
        write(out, "categories.csv", ["dataset", "category", "engine", "ms"], cats)
    else:
        print("PyYAML missing: summary.csv and categories.csv (Sparqloscope) not rewritten", file=sys.stderr)
    qmph, aqet = bsbm(res)
    write(out, "bsbm_qmph.csv", ["scale", "usecase", "engine", "qmph", "note"], qmph)
    write(out, "bsbm_aqet.csv", ["scale", "usecase", "query", "engine", "ms"], aqet)
    load, queries = trainmarks(res)
    write(out, "trainmarks_load.csv", ["scale", "engine", "load_s"], load)
    write(out, "trainmarks_queries.csv", ["scale", "query", "engine", "warm_ms", "cold_ms"], queries)
    load, queries = v2(res)
    write(out, "spatial_load.csv", ["dataset", "engine", "load_s", "disk_gib", "triples"], load)
    write(out, "spatial_queries.csv", ["dataset", "family", "query", "engine", "status", "cold_ms", "p50_ms", "p95_ms",
                                       "check", "check_note"], queries)
    write(out, "rinfshapes_queries.csv",
          ["dataset", "shape", "query", "control_of", "engine", "status", "rows_ms", "count_ms", "rows", "title"],
          rinfshapes(res))
    write(out, "provenance.csv", ["suite", "dataset", "machine", "cpus", "commit", "date", "engines"], provenance(res))
    print(f"dashboard files written to {out}")


if __name__ == "__main__":
    main()
