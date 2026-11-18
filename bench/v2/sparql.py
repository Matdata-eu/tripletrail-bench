#!/usr/bin/env python3
"""Send one SPARQL query (file or -e text) to an endpoint and print the CSV result and timing.

  sparql.py http://localhost:7878/ds/query query.rq
  sparql.py http://localhost:7878/ds/query -e 'SELECT * WHERE { ?s ?p ?o } LIMIT 3'
  sparql.py --update http://localhost:7878/ds/update -e 'INSERT DATA { ... }'
"""
import sys
import time

import requests


def main():
    args = sys.argv[1:]
    update = False
    if args and args[0] == "--update":
        update, args = True, args[1:]
    url = args[0]
    text = args[2] if args[1] == "-e" else open(args[1]).read()
    t = time.perf_counter()
    if update:
        r = requests.post(url, data={"update": text}, timeout=3600)
    else:
        r = requests.post(url, data={"query": text}, headers={"Accept": "text/csv"}, timeout=3600)
    dt = time.perf_counter() - t
    out = r.text
    lines = out.splitlines()
    print("\n".join(lines[:40]))
    if len(lines) > 40:
        print(f"... {len(lines) - 1} rows")
    print(f"HTTP {r.status_code} in {dt * 1000:.1f} ms", file=sys.stderr)


if __name__ == "__main__":
    main()
