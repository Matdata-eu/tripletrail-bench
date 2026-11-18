#!/usr/bin/env python3
"""Download one RINF country graph from ERA's public SPARQL endpoint as N-Triples.

  fetch_rinf.py <graph code> [--endpoint URL]     e.g. fetch_rinf.py 0076
      -> $BENCH_WORK/data/rinf-<code>.nt and rinf-<code>.meta.json
  fetch_rinf.py all                               every graph of the endpoint (the countries'
      -> $BENCH_WORK/data/rinf-all.nt              and the code lists, ~43 M triples), merged

RINF (the EU Register of Infrastructure, published by the EU Agency for Railways) is real
railway data with literals of every common kind (strings with language tags, dates, numbers,
WKT), which suits the generic Sparqloscope query templates. The graph is downloaded one
predicate at a time (CONSTRUCT per predicate) with retries, because large CONSTRUCTs over the
public endpoint get cut off; each part is checked against the predicate's triple count.
Graph 0076 has about 1.6 M triples (see results/sparqloscope for the code -> size table).
"""
import argparse
import json
import os
import sys
import time

import requests

V2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
ENDPOINT = "https://graph.data.era.europa.eu/repositories/rinf-plus"


def select(ep, q):
    r = requests.post(ep, data={"query": q}, headers={"Accept": "application/sparql-results+json"}, timeout=600)
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def fetch_graph(ep, g, parts):
    """Downloads graph g into parts/, one file per predicate; answers the triples expected."""
    preds = select(ep, f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }} GROUP BY ?p")
    if not preds:
        sys.exit(f"graph {g} is empty or unknown")
    os.makedirs(parts, exist_ok=True)
    total = 0
    for i, b in enumerate(sorted(preds, key=lambda b: b["p"]["value"])):
        pred, n = b["p"]["value"], int(b["n"]["value"])
        out = os.path.join(parts, f"{i:04d}.nt")
        for attempt in range(6):
            if os.path.exists(out) and sum(1 for _ in open(out, "rb")) >= n:
                break
            try:
                r = requests.post(ep, timeout=1800, headers={"Accept": "application/n-triples"},
                                  data={"query": f"CONSTRUCT {{ ?s <{pred}> ?o }} WHERE {{ GRAPH <{g}> {{ ?s <{pred}> ?o }} }}"})
                r.raise_for_status()
                open(out, "wb").write(r.content)
            except requests.RequestException as e:
                print(f"retry {pred}: {e}", file=sys.stderr)
            time.sleep(attempt * 5)
        else:
            sys.exit(f"could not download {pred} ({n} triples)")
        total += n
        print(f"{g} {i + 1}/{len(preds)} {pred} {n}", flush=True)
    return total


def main():
    p = argparse.ArgumentParser()
    p.add_argument("code")
    p.add_argument("--endpoint", default=ENDPOINT)
    a = p.parse_args()
    data = os.path.join(WORK, "data")
    if a.code == "all":
        graphs = sorted(b["g"]["value"] for b in select(a.endpoint, "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"))
        dirs = []
        total = 0
        for g in graphs:
            d = os.path.join(data, "rinf-all.parts", g.rsplit("/graph/", 1)[-1].replace("/", "-"))
            total += fetch_graph(a.endpoint, g, d)
            dirs.append(d)
    else:
        g = f"http://data.europa.eu/949/graph/{a.code}"
        dirs = [os.path.join(data, f"rinf-{a.code}.parts")]
        total = fetch_graph(a.endpoint, g, dirs[0])
    nt = os.path.join(data, f"rinf-{a.code}.nt")
    with open(nt, "wb") as f:
        for parts in dirs:
            for name in sorted(os.listdir(parts)):
                f.write(open(os.path.join(parts, name), "rb").read())
    lines = sum(1 for _ in open(nt, "rb"))
    meta = {"graph": g, "triples": lines, "expected": total} if a.code != "all" else \
        {"graphs": graphs, "triples": lines, "expected": total}
    json.dump(meta, open(nt[:-3] + ".meta.json", "w"))
    print(f"{nt}: {lines} triples (expected {total})")

if __name__ == "__main__":
    main()
