#!/usr/bin/env python3
"""Markdown tables from a results folder.

  report.py <results>/<dataset> [engine ...]   -> prints Markdown; also writes report.md and
                                                  summary.csv in that folder
"""
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run import na_reason  # noqa: E402
from workload import QUERIES  # noqa: E402

ORDER = ["tripletrail", "tripletrail-1t", "postgis", "graphdb", "jena", "qlever"]
NAMES = {"tripletrail": "tripletrail", "tripletrail-1t": "tripletrail, 1 thread per query", "postgis": "PostGIS/pgRouting", "graphdb": "GraphDB", "jena": "Jena GeoSPARQL",
         "qlever": "QLever"}


def fmt_ms(v):
    if v is None:
        return "-"
    if v >= 10000:
        return f"{v / 1000:.0f} s"
    if v >= 1000:
        return f"{v / 1000:.2f} s"
    if v >= 10:
        return f"{v:.0f}"
    return f"{v:.1f}"


def fmt_bytes(b):
    if b is None:
        return "-"
    return f"{b / 2**20:.0f} MiB" if b < 2**30 else f"{b / 2**30:.2f} GiB"


def fmt_count(load, engine):
    if engine == "postgis":
        rows = load.get("rows") or {}
        return f"{sum(rows.values()):,} rows" if rows else "-"
    t = load.get("triples")
    return f"{t:,}" if isinstance(t, int) else "-"


def main():
    folder = sys.argv[1]
    engines = sys.argv[2:] or [e for e in ORDER if os.path.isdir(os.path.join(folder, e))]
    res = {}
    for p in glob.glob(os.path.join(folder, "*", "*.json")):
        e, name = os.path.basename(os.path.dirname(p)), os.path.basename(p)[:-5]
        res.setdefault(name, {})[e] = json.load(open(p))
    out = []
    loads = res.get("load", {})
    if loads:
        out.append("| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |")
        out.append("|---|---|---|---|---|---|")
        for e in engines:
            l = loads.get(e)
            if not l:
                continue
            extra = l.get("spatial_index_s", l.get("start_and_spatial_index_s", l.get("start_s")))
            out.append(f"| {NAMES[e]} | {l['load_s']:.1f} | {extra if extra is not None else '-'} | "
                       f"{fmt_bytes(l.get('disk_bytes'))} | {l.get('rss_after_start', '-')}"
                       f"{'; ' + l['rss_when_answering'] + ' when it first answered' if l.get('rss_when_answering') else ''} | "
                       f"{fmt_count(l, e)} |")
        counts = {fmt_count(loads[e], e) for e in engines if e != "postgis" and loads.get(e)}
        if len(counts) > 1:
            # An engine measured in its own run on a newer extract (data-<engine>.json says which).
            out.append("\nThe engines loaded different extracts (see the Triples column), so their answers are"
                       " compared across extracts. data-<engine>.json and env-<engine>.json describe an engine"
                       " that ran on its own.")
        out.append("")
    notes = {}
    summary = []
    fam = None
    for qid, q in QUERIES.items():
        if qid not in res:
            continue
        if q["family"] != fam:
            fam = q["family"]
            out.append(f"\n**Family {fam}** — warm p50 / p95 in ms (cold first run in brackets)\n")
            out.append("| Query | " + " | ".join(NAMES[e] for e in engines) + " |")
            out.append("|---|" + "---|" * len(engines))
        cells = []
        for e in engines:
            r = res.get(qid, {}).get(e)
            if r is None and na_reason(e, qid):
                r = {"status": "n/a", "reason": na_reason(e, qid)}
            if r is None:
                cells.append("not run")
                continue
            st = r.get("status", "")
            if st == "n/a":
                notes.setdefault(r["reason"], len(notes) + 1)
                cells.append(f"N/A [{notes[r['reason']]}]")
            elif st == "failed":
                reason = r.get("reason", "")
                low = reason.lower()
                # QLever says "timed out" (HTTP 429), GraphDB "took too long" (HTTP 503).
                short = "timeout" if any(w in low for w in ("timeout", "timed out", "took too long", "cancel")) \
                    else "error"
                notes.setdefault(f"{NAMES[e]} {qid}: {reason[:160]}", len(notes) + 1)
                cells.append(f"{short} [{notes[f'{NAMES[e]} {qid}: {reason[:160]}']}]")
            else:
                w = r.get("warm", {})
                cells.append(f"{fmt_ms(w.get('p50_ms'))} / {fmt_ms(w.get('p95_ms'))} ({fmt_ms(r.get('cold_ms'))})"
                             + ("*" if st != "ok" else ""))
                summary.append(dict(qid=qid, engine=e, status=st, cold_ms=r.get("cold_ms"), **w))
        out.append(f"| {qid} | " + " | ".join(cells) + " |")
    if notes:
        out.append("\nNotes:\n")
        for text, n in notes.items():
            out.append(f"{n}. {text}")
    # Hand-written notes about this dataset's results (notes.md next to report.md).
    extra = os.path.join(folder, "notes.md")
    if os.path.exists(extra):
        out.append("\n" + open(extra).read().strip())
    md = "\n".join(out)
    print(md)
    with open(os.path.join(folder, "report.md"), "w") as f:
        f.write(md + "\n")
    if summary:
        keys = ["qid", "engine", "status", "cold_ms", "n", "p50_ms", "p95_ms", "min_ms", "max_ms", "mean_ms"]
        with open(os.path.join(folder, "summary.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for s in summary:
                w.writerow({k: s.get(k) for k in keys})


if __name__ == "__main__":
    main()
