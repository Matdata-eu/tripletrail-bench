#!/usr/bin/env python3
"""Writes summary.json, the headline numbers of the benchmark results, next to the dashboard's
CSV files (bench/v2/results/dashboard). The website reads it from a tag of this repository:

    https://raw.githubusercontent.com/Matdata-eu/tripletrail-bench/<tag>/bench/v2/results/dashboard/summary.json

    python3 site/summary.py bench/v2/results/dashboard

For each dataset of each suite: TripleTrail's number, every other engine's, and how many times
faster TripleTrail is (`speedup` > 1) or slower (< 1). Lower is better for times, higher for
query mixes per hour. Engines that did not answer are left out, and so are wrong answers (the
dashboard's CSV files mark them, #96): a BSBM mix with wrong result counts, and the spatial
queries whose status is "wrong answer"; Sparqloscope's means leave such queries out already.
Standard library only.
"""

import csv
import json
import math
import os
import sys

ENGINE = "tripletrail"


def rows(d, name):
    path = os.path.join(d, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def compare(groups, metric, lower_is_better=True):
    """groups: {key: {engine: value}} -> [{key, unit, tripletrail, others: {engine: {value, speedup}}}]"""
    out = []
    for key, by_engine in sorted(groups.items()):
        ours = by_engine.get(ENGINE)
        if ours is None:
            continue
        others = {}
        for engine, v in sorted(by_engine.items()):
            if engine == ENGINE:
                continue
            speedup = v / ours if lower_is_better else ours / v
            others[engine] = {"value": v, "speedup": round(speedup, 2)}
        out.append({"dataset": key, "metric": metric, "tripletrail": ours, "others": others})
    return out


def gmean(xs):
    xs = [x for x in xs if x]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "bench/v2/results/dashboard"
    suites = {}

    g = {}
    for r in rows(d, "summary.csv"):
        v = num(r["geomean_ms"])
        if v:
            g.setdefault(r["dataset"], {})[r["engine"]] = v
    suites["sparqloscope_geomean_ms"] = compare(g, "geometric mean query time (ms)")

    g = {}
    for r in rows(d, "bsbm_qmph.csv"):
        v = num(r["qmph"])
        # A mix with wrong result counts is no headline number (#96).
        if v and not r.get("wrong"):
            g.setdefault(f"{r['scale']} {r['usecase']}", {})[r["engine"]] = v
    suites["bsbm_qmph"] = compare(g, "query mixes per hour", lower_is_better=False)

    g = {}
    for r in rows(d, "trainmarks_load.csv"):
        v = num(r["load_s"])
        if v:
            g.setdefault(r["scale"], {})[r["engine"]] = v
    suites["trainmarks_load_s"] = compare(g, "load time (s)")

    g = {}
    for r in rows(d, "spatial_load.csv"):
        v = num(r["load_s"])
        if v:
            g.setdefault(r["dataset"], {})[r["engine"]] = v
    suites["spatial_load_s"] = compare(g, "load time (s)")

    # Spatial queries: geometric mean of p50 over the queries every compared engine answered.
    per = {}
    for r in rows(d, "spatial_queries.csv"):
        v = num(r["p50_ms"])
        if v and r.get("status", "ok") == "ok":
            per.setdefault(r["dataset"], {}).setdefault(r["query"], {})[r["engine"]] = v
    g = {}
    for ds, queries in per.items():
        engines = {e for q in queries.values() for e in q}
        for e in engines - {ENGINE}:
            both = [q for q in queries.values() if ENGINE in q and e in q]
            if both:
                g.setdefault(ds, {})[e] = gmean([q[e] for q in both])
                g[ds].setdefault(f"{ENGINE}@{e}", gmean([q[ENGINE] for q in both]))
    spatial = []
    for ds, by in sorted(g.items()):
        others = {}
        for e, v in sorted(by.items()):
            if e.startswith(ENGINE + "@"):
                continue
            ours = by[f"{ENGINE}@{e}"]
            others[e] = {"value": round(v, 3), "tripletrail": round(ours, 3), "speedup": round(v / ours, 2)}
        spatial.append({"dataset": ds, "metric": "geometric mean p50 over shared answered queries (ms)",
                        "others": others})
    suites["spatial_queries_p50_ms"] = spatial

    prov = rows(d, "provenance.csv")
    out = {"engine": ENGINE, "provenance": prov, "suites": suites}
    with open(os.path.join(d, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"summary.json: {sum(len(v) for v in suites.values())} comparisons")


if __name__ == "__main__":
    main()
