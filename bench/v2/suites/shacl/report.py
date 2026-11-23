#!/usr/bin/env python3
"""Writes the SHACL phase 0 report (support matrix and timings) as Markdown.

  report.py <results dir>     reads probes.json and <engine>.json there, writes report.md

The results dir holds only measurements: times, memory, result counts and the SHA-256 of each
engine's sorted result keys (focus node, path, component, severity), so that engines can be
compared without publishing RINF values.
"""
import glob
import json
import os
import sys

PROBES = [("core", "Core"), ("sparql-constraint", "SPARQL constraints"),
          ("sparql-target", "SPARQL targets"), ("sparql-function", "SPARQL functions"),
          ("custom-component", "SPARQL components"), ("rule", "AF rules")]
MARK = {"pass": "yes", "fail": "no (wrong count)", "error": "no (error)", "n/a": "n/a"}


def num(n):
    return "" if n is None else f"{n:,}"


def main():
    d = sys.argv[1]
    probes = json.load(open(os.path.join(d, "probes.json")))
    runs = {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))
            if not p.endswith(("probes.json", "run.json"))}
    meta = json.load(open(os.path.join(d, "run.json"))) if os.path.exists(os.path.join(d, "run.json")) else {}
    engines = list(probes) + [e for e in runs if e not in probes]
    out = ["# SHACL suite, phase 0", ""]
    if meta:
        out += [f"Data: {meta.get('data', '')}. Shapes: {meta.get('shapes', '')}. Machine: {meta.get('machine', '')}.", ""]
    out += ["## Feature support", "",
            "Each cell is a probe in `bench/v2/suites/shacl/features/` on `data.ttl`: yes when the engine gives "
            "the expected number of results (or inferred triples), no otherwise. AF rules run with the engine's "
            "own inference command; n/a means it has none.", "",
            "| engine | version | " + " | ".join(t for _, t in PROBES) + " |",
            "|---|---|" + "---|" * len(PROBES)]
    for e in engines:
        p = probes.get(e, {})
        out.append(f"| {e} | {p.get('version') or runs.get(e, {}).get('version') or ''} | "
                   + " | ".join(MARK.get(p.get(k, {}).get("verdict"), "") for k, _ in PROBES) + " |")
    ref = runs.get("jena", {}).get("results_sha256")
    out += ["", "## ERA RINF shapes on the data", "",
            "Same results: the engine's sorted result keys (focus node, path, constraint component, severity) "
            "hash to the same SHA-256 as Jena's.", "",
            "| engine | ran | time (s) | peak memory (MB) | results | violations | warnings | same results as Jena |",
            "|---|---|---:|---:|---:|---:|---:|---|"]
    for e in engines:
        r = runs.get(e)
        if not r:
            continue
        ran = "timed out" if r.get("timed_out") else "yes" if r.get("exit") in (0, 1) and "results" in r else \
            f"no (exit {r.get('exit')})"
        sev = r.get("by_severity", {})
        same = "" if "results_sha256" not in r else "yes" if r["results_sha256"] == ref else "no"
        out.append(f"| {e} | {ran} | {r['wall_s']:.1f} | {r['peak_rss_bytes'] / 2**20:,.0f} | "
                   f"{num(r.get('results'))} | {num(sev.get('Violation'))} | {num(sev.get('Warning'))} | {same} |")
    notes = os.path.join(d, "notes.md")
    if os.path.exists(notes):
        out += ["", open(notes).read().strip()]
    open(os.path.join(d, "report.md"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
