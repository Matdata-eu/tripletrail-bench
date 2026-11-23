#!/usr/bin/env python3
"""SHACL suite, phase 0: which SHACL features each engine supports, by small probes.

  probes.py <out.json> [engine ...]

Each probe in features/ is a shapes file run on features/data.ttl; its first comment line says
how many results (or, for rules, new triples) a supporting engine gives. An engine passes a
probe when it gives that number, fails when it gives another, and errs when it stops with an
error. The engines' commands and environment variables are those of run_phase0.py; rules run
with each engine's own inference command (TripleTrail `infer`, TopBraid `shaclinfer.sh`,
pySHACL's advanced mode). Engines without one are "n/a" for rules.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_phase0  # noqa: E402

FEATURES = os.path.join(HERE, "features")
DATA = os.path.join(FEATURES, "data.ttl")
VALIDATION = ["core", "sparql-constraint", "sparql-target", "sparql-function", "custom-component"]


def expected(probe):
    first = open(os.path.join(FEATURES, f"{probe}.shapes.ttl")).read()
    return int(re.search(r"Expected: (\d+)", first).group(1))


def validate(engine, shapes, tmp):
    report = os.path.join(tmp, "report.ttl")
    if os.path.exists(report):
        os.remove(report)
    cmd, stdout_to = run_phase0.commands(DATA, shapes, report)[engine]
    p = subprocess.run(cmd, stdout=open(stdout_to, "w") if stdout_to else subprocess.DEVNULL,
                       stderr=subprocess.PIPE, text=True, timeout=600)
    if not os.path.exists(report) or not os.path.getsize(report):
        # A conforming run of TripleTrail, pySHACL or RDF4J still writes a report; none means
        # the engine stopped.
        return None, p.stderr[-400:]
    counts = run_phase0.count_report(report)
    if "report_parse_error" in counts:
        return None, counts["report_parse_error"]
    return counts.get("results", 0), p.stderr[-400:] if p.returncode not in (0, 1) else ""


def infer(engine, shapes, tmp):
    """New triples the rules infer, or None when the engine has no inference command."""
    out = os.path.join(tmp, "inferred.nt")
    if engine == "tripletrail":
        cmd = [os.environ.get("TRIPLETRAIL_BIN", "tripletrail"), "infer", "--data", DATA,
               "--shapes", shapes, "--output", out]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    elif engine == "topbraid":
        tq = os.environ.get("TOPBRAID_HOME", "shacl")
        p = subprocess.run(["sh", f"{tq}/bin/shaclinfer.sh", "-datafile", DATA, "-shapesfile", shapes],
                           stdout=open(out, "w"), stderr=subprocess.PIPE, text=True, timeout=600)
    elif engine == "pyshacl":
        import pyshacl
        import rdflib
        g = rdflib.Graph().parse(DATA)
        before = len(g)
        pyshacl.validate(g, shacl_graph=rdflib.Graph().parse(shapes), advanced=True, inplace=True,
                         iterate_rules=True)
        return len(g) - before, ""
    else:
        return "n/a", ""
    if p.returncode != 0:
        return None, p.stderr[-400:]
    import rdflib
    g = rdflib.Graph()
    g.parse(out, format="turtle")  # Turtle reads N-Triples too
    have = rdflib.Graph().parse(DATA)
    return sum(1 for t in g if t not in have), ""


def main():
    out, *engines = sys.argv[1:]
    engines = engines or ["tripletrail", "jena", "topbraid", "pyshacl", "rdf4j"]
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for engine in engines:
            row = {"version": run_phase0.version(engine)}
            for probe in VALIDATION + ["rule"]:
                shapes = os.path.join(FEATURES, f"{probe}.shapes.ttl")
                try:
                    got, err = (infer if probe == "rule" else validate)(engine, shapes, tmp)
                except Exception as e:  # noqa: BLE001 - an engine's crash is its result
                    got, err = None, str(e)[-400:]
                want = expected(probe)
                verdict = "n/a" if got == "n/a" else "error" if got is None else \
                    "pass" if got == want else "fail"
                row[probe] = {"verdict": verdict, "got": got, "expected": want}
                if err and verdict != "pass":
                    row[probe]["error"] = err.strip()
                print(f"{engine:12s} {probe:18s} {verdict:6s} got {got} expected {want}", flush=True)
            res[engine] = row
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
