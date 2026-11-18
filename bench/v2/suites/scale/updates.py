#!/usr/bin/env python3
"""Small commits into a loaded SPARQL endpoint (#218): COMMITS INSERT DATA updates of EACH new
triples each (a new label on existing features), timed one by one.

  updates.py <query endpoint> <update endpoint> <out.json> [--commits 60] [--each 10000]
Writes {"commits", "each", "p50_ms", "p95_ms", "max_ms", "total_s", "ms": [...]}.
"""
import argparse
import json
import statistics
import time

import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("update")
    ap.add_argument("out")
    ap.add_argument("--commits", type=int, default=60)
    ap.add_argument("--each", type=int, default=10000)
    a = ap.parse_args()
    s = requests.Session()
    s.headers["Connection"] = "close"
    need = a.commits * a.each
    r = s.post(a.query, data={"query": f"SELECT ?f WHERE {{ ?f a ?c }} LIMIT {need}"},
               headers={"Accept": "application/sparql-results+json"}, timeout=3600)
    r.raise_for_status()
    subjects = [b["f"]["value"] for b in r.json()["results"]["bindings"] if b["f"]["type"] == "uri"]
    if not subjects:
        raise SystemExit("no subjects to update")
    ms = []
    for c in range(a.commits):
        lines = "\n".join(
            f'<{subjects[(c * a.each + i) % len(subjects)]}> <http://example.org/bench/note> "{c}-{i}" .'
            for i in range(a.each))
        t = time.perf_counter()
        r = s.post(a.update, data={"update": "INSERT DATA {\n" + lines + "\n}"}, timeout=3600)
        r.raise_for_status()
        ms.append((time.perf_counter() - t) * 1000)
    q = sorted(ms)
    rec = {"commits": a.commits, "each": a.each, "p50_ms": round(statistics.median(ms), 1),
           "p95_ms": round(q[int(0.95 * (len(q) - 1))], 1), "max_ms": round(q[-1], 1),
           "total_s": round(sum(ms) / 1000, 2), "ms": [round(m, 1) for m in ms]}
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"updates: {a.commits} x {a.each}: p50 {rec['p50_ms']} ms, p95 {rec['p95_ms']} ms, "
          f"total {rec['total_s']} s")


if __name__ == "__main__":
    main()
