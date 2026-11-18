#!/usr/bin/env python3
"""Builds the GitHub Pages site of the benchmark dashboard into OUT (default _site):

    python3 site/build.py [RESULTS] [OUT]     # RESULTS defaults to bench/v2/results

The page (index.html, app.js, style.css), the dashboard's CSV files and summary.json under
data/, and data/runs.json: one row per run manifest in RESULTS/runs. Standard library only.
"""

import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    results = sys.argv[1] if len(sys.argv) > 1 else "bench/v2/results"
    out = sys.argv[2] if len(sys.argv) > 2 else "_site"
    data = os.path.join(out, "data")
    os.makedirs(data, exist_ok=True)
    for name in ("index.html", "app.js", "style.css"):
        shutil.copy(os.path.join(HERE, name), out)
    for path in glob.glob(os.path.join(results, "dashboard", "*.csv")) + \
            glob.glob(os.path.join(results, "dashboard", "summary.json")):
        shutil.copy(path, data)
    runs = []
    for path in glob.glob(os.path.join(results, "runs", "*.json")):
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
        jobs = m.get("jobs", [])
        count = lambda st: sum(1 for j in jobs if j.get("status") == st)
        runs.append({"run": m.get("run"), "url": m.get("workflow_run", ""), "started": m.get("started"),
                     "request": m.get("request"), "commit": m.get("commit", ""), "machine": m.get("machine"),
                     "jobs": f"{count('ok')} / {count('failed')} / {count('skipped')}"})
    runs.sort(key=lambda r: r.get("started") or "", reverse=True)
    with open(os.path.join(data, "runs.json"), "w", encoding="utf-8") as f:
        json.dump(runs, f, indent=1)
    print(f"site: {out} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
