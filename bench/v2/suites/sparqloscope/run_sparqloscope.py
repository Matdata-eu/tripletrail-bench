#!/usr/bin/env python3
"""Sparqloscope (https://github.com/ad-freiburg/sparqloscope, Apache-2.0) on the SPARQL engines
of benchmark v2.

Sparqloscope is about 100 queries per dataset, each isolating one SPARQL feature: joins of
small / large predicates, OPTIONAL / MINUS / EXISTS joins, UNION, GROUP BY with aggregates,
DISTINCT, property paths, REGEX and string functions, numeric and date functions, language
filters and result sizes. The query set is generated per dataset from its statistics (which
predicates are large, which joins have large results, ...), so it fits any data. The QLever
evaluation site (qlever.dev/evaluation) is the web app that shows Sparqloscope results; the
YAML written here is in the same format, so `qlever serve-evaluation-app --results-dir
results/sparqloscope/<dataset>` shows our runs the same way.

  run_sparqloscope.py fetch
      clone the pinned Sparqloscope commit to $BENCH_WORK/sparqloscope/src
  run_sparqloscope.py generate --dataset D
      generate the query set for D with Sparqloscope's generator against QLever (the generator
      relies on QLever's SERVICE to reuse its precomputed statistics; QLever must be loaded with
      D: engines/qlever.sh load D). Writes suites/sparqloscope/benchmarks/D.benchmark.tsv,
      which is committed so every run uses the same queries.
  run_sparqloscope.py run --dataset D --engine E [--skip-load] [--timeout 180] [--only id,...]
      load D into E, restart it (empty caches) and run every query once, like the paper (one
      cold run per query; QLever's cache is cleared before each). Writes
      results/sparqloscope/D/D.E.results.yaml (Sparqloscope / qlever-control format).
  run_sparqloscope.py report
      results/sparqloscope/report.md: per dataset and engine, queries answered / failed /
      timed out, the geometric mean time (failed and timed-out queries count as 2 x the
      timeout, the penalty QLever's evaluation uses) and the time per feature category.

Datasets: bsbm-<n> (suites/bsbm), rinf-<code> (suites/data/fetch_rinf.py) and dblp, for which the
official query set from the Sparqloscope repository is used (dblp needs ~64 GB RAM: run it on a
large machine, see bench/v2/cloud/README.md).
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

import requests
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, V2)
from run import Sparql  # noqa: E402

WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
OUT = os.path.join(V2, "results", "sparqloscope")
SRC = os.path.join(WORK, "sparqloscope", "src")
REPO = "https://github.com/ad-freiburg/sparqloscope.git"
COMMIT = "61ad92f7ae3de202580ab6112aa4f08001990f56"  # 2025-08-25
PY_IMAGE = os.environ.get("SPARQLOSCOPE_PY_IMAGE", "mirror.gcr.io/library/python:3.12-slim")
GEN_PORT = 8765
GEN_DEPS = ["argcomplete", "termcolor", "pyyaml", "requests"]
ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb", "maplib"]
# Feature categories, by query-id prefix (order matters: first match wins).
CATEGORIES = [
    ("join", r"^(join|multicolumn-join)"), ("optional", r"^optional"), ("minus", r"^minus"),
    ("exists", r"^exists"), ("union", r"^union"), ("group by / distinct", r"^(group-by|distinct)"),
    ("property path", r"^transitive-path"), ("regex / string", r"^(regex|str)"),
    ("result size", r"^result-size"), ("numeric", r"^numeric"), ("filter / language", r"^filter"),
    ("date", r"^date"), ("count", r"^number-of"),
]


def sh(*cmd, capture=True, **kw):
    r = subprocess.run(cmd, capture_output=capture, text=True, **kw)
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


def benchmark_tsv(ds):
    own = os.path.join(HERE, "benchmarks", f"{ds}.benchmark.tsv")
    if os.path.exists(own):
        return own
    cmd_fetch()
    upstream = os.path.join(SRC, "benchmarks", f"{ds}.benchmark.tsv")
    if os.path.exists(upstream):
        return upstream
    sys.exit(f"no query set for {ds}: run `run_sparqloscope.py generate --dataset {ds}` first")


def cmd_generate(a):
    """Run Sparqloscope's generator in a Python container (host network, so it reaches QLever
    on localhost:7001; QLever reaches the generator's SERVICE server through the docker bridge)."""
    cmd_fetch()
    ep = engine("qlever", "endpoint")
    for k, v in {"group-by-hash-map-enabled": "true", "default-query-timeout": "24h",
                 "service-max-value-rows": "0", "cache-service-results": "true"}.items():
        requests.post(ep, data={k: v, "access-token": "benchtoken"}, timeout=60).raise_for_status()
    gen = os.path.join(WORK, "sparqloscope", "gen", a.dataset)
    os.makedirs(gen, exist_ok=True)
    prefixes = os.path.join(HERE, "prefixes", f"{a.dataset.split('-')[0]}.ttl")
    pfx = open(prefixes).read().strip() if os.path.exists(prefixes) else ""
    bridge = os.environ.get("DOCKER_HOST_IP", "172.17.0.1")
    # The generator's dependencies, downloaded on the host (which may sit behind a proxy the
    # container does not know) and installed offline in the container.
    wheels = os.path.join(WORK, "sparqloscope", "wheels")
    if not os.path.isdir(wheels) or not os.listdir(wheels):
        sh(sys.executable, "-m", "pip", "download", "-q", "-d", wheels, "--only-binary=:all:",
           "--python-version", "3.12", "--platform", "manylinux2014_x86_64", *GEN_DEPS)
    script = (
        f"pip install -q --no-index --find-links /wheels {' '.join(GEN_DEPS)} >/dev/null && "
        f"python3 /src/generate-benchmark.py --query-templates /src/query-templates.yaml "
        f"--sparql-endpoint {ep} --kg-name {a.dataset} --output-format tsv "
        f"--external-url http://{bridge}:{GEN_PORT} --port {GEN_PORT} --argmax-timeout {a.argmax_timeout}"
        + (' --prefix-definitions "$PFX"' if pfx else ""))
    t = time.time()
    sh("docker", "run", "--rm", "--network", "host", "-u", f"{os.getuid()}:{os.getgid()}",
       "-e", "HOME=/tmp", "-e", f"PFX={pfx}", "-e", "PYTHONUSERBASE=/tmp/py",
       "-v", f"{SRC}:/src:ro", "-v", f"{gen}:/gen", "-v", f"{wheels}:/wheels:ro", "-w", "/gen", PY_IMAGE, "sh", "-c",
       script.replace("pip install", "pip install --user"), capture=False)
    os.makedirs(os.path.join(HERE, "benchmarks"), exist_ok=True)
    dst = os.path.join(HERE, "benchmarks", f"{a.dataset}.benchmark.tsv")
    shutil.copy(os.path.join(gen, f"{a.dataset}.benchmark.tsv"), dst)
    print(f"{dst}: {sum(1 for _ in open(dst))} queries in {time.time() - t:.0f} s")


def read_tsv(path):
    out = []
    for line in open(path):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        head, sparql = line.split("\t", 1)
        m = re.match(r"^(\S+)\s*(?:\[(.*)\])?$", head)
        out.append({"query": m.group(1), "long_query": m.group(2) or m.group(1), "sparql": sparql})
    return out


def cmd_run(a):
    qs = read_tsv(benchmark_tsv(a.dataset))
    if a.only:
        keep = {k.strip() for k in a.only.split(",")}
        qs = [q for q in qs if q["query"] in keep]
    outdir = os.path.join(OUT, a.dataset)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{a.dataset}.{a.engine}.results.yaml")
    old = yaml.safe_load(open(path)) if os.path.exists(path) else None
    prev = old if a.only else None
    load = None
    if not a.skip_load:
        print(f"loading {a.dataset} into {a.engine}", flush=True)
        load = json.loads(engine(a.engine, "load", a.dataset).splitlines()[-1])
    engine(a.engine, "start", a.dataset)  # restart: the first query sees empty engine caches
    cl = Sparql(a.engine, engine(a.engine, "endpoint"))
    records = []
    try:
        for i, q in enumerate(qs):
            rec = {"query": q["query"], "sparql": q["sparql"]}
            t = time.perf_counter()
            try:
                cl.before_run()
                dt, rows = cl.query(q["sparql"], a.timeout)
                if dt > a.timeout:
                    raise TimeoutError(f"took {dt:.1f} s, over the {a.timeout} s timeout")
                rec["runtime_info"] = {"client_time": dt}
                rec["result_size"] = len(rows)
                rec["results"] = [[str(v) for v in r] for r in rows[:5]]
                rec["digest"] = digest(rows)
                status = f"{dt * 1000:.0f} ms, {len(rows)} rows"
            except Exception as e:  # noqa: BLE001 - recorded, not hidden
                rec["runtime_info"] = {"client_time": time.perf_counter() - t}
                rec["headers"] = []
                rec["results"] = f"Exception: {str(e)[:500]}"
                status = f"FAILED {str(e)[:120]}"
                # A timed-out query may keep running in the server (not every engine cancels
                # it), and a crash or out-of-memory leaves no server: restart for the next query.
                if isinstance(e, (TimeoutError, requests.exceptions.Timeout)) or "timeout" in str(e).lower() \
                        or not alive(a.engine):
                    status += " (engine restarted)"
                    engine(a.engine, "start", a.dataset)
            rec["long_query"] = q["long_query"]
            records.append(rec)
            print(f"{i + 1}/{len(qs)} {q['query']}: {status}", flush=True)
    finally:
        engine(a.engine, "stop")
    if prev:
        done = {r["query"] for r in records}
        records = [r for r in prev["queries"] if r["query"] not in done] + records
    doc = {"timeout": a.timeout, "engine": a.engine, "dataset": a.dataset, "queries": records}
    if load:
        doc["load"] = load
    elif old and "load" in old:  # --skip-load keeps the load record of the earlier run
        doc["load"] = old["load"]
    yaml.safe_dump(doc, open(path, "w"), sort_keys=False, allow_unicode=True, width=120)
    print(path)


def digest(rows):
    """SHA-256 of every row in the order the engine sent them: two runs of one engine (all cores
    against one, tripletrail#4) must give the same answer in the same order."""
    h = hashlib.sha256()
    for r in rows:
        h.update(("\t".join("" if v is None else str(v) for v in r) + "\n").encode())
    return h.hexdigest()


def alive(e):
    try:
        requests.post(engine(e, "endpoint"), data={"query": "ASK {}"}, timeout=10)
        return True
    except requests.RequestException:
        return False


def failed(r):
    return isinstance(r.get("results"), str) and r["results"].startswith("Exception")


def one_row(rows):
    """The values of a one-row answer, numbers rounded to 10 significant digits (engines print
    decimals with different precision)."""
    out = []
    for v in (rows[0] if rows else []):
        try:
            out.append(f"{float(v):.10g}")
        except (TypeError, ValueError):
            out.append(str(v))
    return str(out)


def category(qid):
    for name, pat in CATEGORIES:
        if re.search(pat, qid):
            return name
    return "other"


def gmean(xs):
    return math.exp(sum(math.log(max(x, 1e-4)) for x in xs) / len(xs)) if xs else None


def fmt(s):
    if s is None:
        return ""
    return f"{s * 1000:.1f} ms" if s < 1 else f"{s:.2f} s"


def same_order(ids, by, es):
    """Each TripleTrail variant (tripletrail-1t: one thread per query, tripletrail-ids, ...)
    against tripletrail: every row, in order, by digest. Only runs that both answered count."""
    out = []
    for e in [e for e in es if e.startswith("tripletrail-") and "tripletrail" in es]:
        both, diff = 0, []
        for qid in ids:
            a, b = by["tripletrail"].get(qid), by[e].get(qid)
            if not a or not b or failed(a) or failed(b) or "digest" not in a or "digest" not in b:
                continue
            both += 1
            if a["digest"] != b["digest"]:
                diff.append(qid)
        if both:
            out += [f"Same rows in the same order, {e} against tripletrail: {both - len(diff)} of {both} "
                    "queries" + (f"; different: {', '.join(diff)}" if diff else "") + ".", ""]
    return out


def cmd_report(_a):
    lines = ["# Sparqloscope results", "",
             "One cold run per query after an engine restart (QLever's cache cleared before each "
             "query), at the client, HTTP included. Failed and timed-out queries count as 2 x the "
             "timeout in the geometric means, as on the QLever evaluation site. Engines whose "
             "result sizes differ from the majority are listed per query in the last section.", ""]
    for d in sorted(glob.glob(os.path.join(OUT, "*", ""))):
        ds = os.path.basename(os.path.dirname(d))
        docs = {}
        for f in glob.glob(os.path.join(d, f"{ds}.*.results.yaml")):
            doc = yaml.safe_load(open(f))
            docs[doc.get("engine") or f.split(".")[-3]] = doc
        if not docs:
            continue
        es = [e for e in ENGINES if e in docs] + sorted(set(docs) - set(ENGINES))
        n = max(len(doc["queries"]) for doc in docs.values())
        lines += [f"## {ds} ({n} queries)", "", "| | " + " | ".join(es) + " |", "|---|" + "---:|" * len(es)]
        stats = {}
        for e in es:
            doc = docs[e]
            to = doc.get("timeout", 180)
            times, ok, fail, tout, cats = [], 0, 0, 0, {}
            for r in doc["queries"]:
                t = r.get("runtime_info", {}).get("client_time", 0)
                if failed(r):
                    msg = r["results"].lower()
                    if "timeout" in msg or "timed out" in msg or "cancel" in msg:
                        tout += 1
                    else:
                        fail += 1
                    t = 2 * to
                else:
                    ok += 1
                times.append(t)
                cats.setdefault(category(r["query"]), []).append(t)
            stats[e] = dict(ok=ok, fail=fail, tout=tout, g=gmean(times), cats=cats,
                            load=doc.get("load", {}).get("load_s"))
        lines.append("| load (s) | " + " | ".join(str(stats[e]["load"] or "") for e in es) + " |")
        lines.append("| answered | " + " | ".join(str(stats[e]["ok"]) for e in es) + " |")
        lines.append("| failed | " + " | ".join(str(stats[e]["fail"]) for e in es) + " |")
        lines.append("| timed out | " + " | ".join(str(stats[e]["tout"]) for e in es) + " |")
        lines.append("| **geometric mean** | " + " | ".join(f"**{fmt(stats[e]['g'])}**" for e in es) + " |")
        for c, _ in CATEGORIES + [("other", "")]:
            if any(c in stats[e]["cats"] for e in es):
                lines.append(f"| {c} | " + " | ".join(fmt(gmean(stats[e]["cats"].get(c, []))) for e in es) + " |")
        lines.append("")
        # per query
        ids = [r["query"] for r in max(docs.values(), key=lambda d: len(d["queries"]))["queries"]]
        by = {e: {r["query"]: r for r in docs[e]["queries"]} for e in es}
        lines += ["<details><summary>Per query</summary>", "", "| query | " + " | ".join(es) + " |",
                  "|---|" + "---:|" * len(es)]
        mism = []
        for qid in ids:
            cells, sizes = [], {}
            for e in es:
                r = by[e].get(qid)
                if r is None:
                    cells.append("")
                elif failed(r):
                    cells.append("timeout" if "timeout" in r["results"].lower() else "failed")
                else:
                    cells.append(fmt(r["runtime_info"]["client_time"]))
                    # The first row is only compared for one-row answers (COUNT, SUM, MIN, ...):
                    # the order of a LIMIT without ORDER BY is up to the engine.
                    n = r.get("result_size")
                    sizes[e] = (n, one_row(r.get("results", [])) if n == 1 else "")
            lines.append(f"| {qid} | " + " | ".join(cells) + " |")
            vals = list(sizes.values())
            if len(set(vals)) > 1:
                show = lambda v: v[1][:80] if v[1] else f"{v[0]} rows"  # noqa: E731
                common = max(sorted(set(vals), key=repr), key=vals.count)
                if vals.count(common) * 2 <= len(vals):
                    # No majority: list every engine's answer instead of picking one side.
                    mism.append(f"- {qid}: no majority ({', '.join(f'{e}: {show(v)}' for e, v in sizes.items())})")
                    continue
                odd = [e for e, v in sizes.items() if v != common]
                mism.append(f"- {qid}: {', '.join(odd)} differ ({', '.join(f'{e}: {show(sizes[e])}' for e in odd)}; "
                            f"majority: {show(common)})")
        lines += ["", "</details>", ""]
        if mism:
            lines += ["Queries where engines disagree (row count, or the value of a one-row answer):", ""] + mism + [""]
        lines += same_order(ids, by, es)
    open(os.path.join(OUT, "report.md"), "w").write("\n".join(lines))
    print(os.path.join(OUT, "report.md"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("fetch")
    g = sp.add_parser("generate")
    g.add_argument("--dataset", required=True)
    g.add_argument("--argmax-timeout", type=int, default=300)
    r = sp.add_parser("run")
    r.add_argument("--dataset", required=True)
    r.add_argument("--engine", required=True)
    r.add_argument("--skip-load", action="store_true")
    r.add_argument("--timeout", type=int, default=180)
    r.add_argument("--only")
    sp.add_parser("report")
    a = p.parse_args()
    {"fetch": cmd_fetch, "generate": cmd_generate, "run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
