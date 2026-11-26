"""Runs the Facade-X benchmark: each query of queries/ with `tripletrail lift` and with the
SPARQL Anything command line, printing wall time, peak memory and triples, and whether the
two wrote the same triples. Run from this folder after gen.py:

    python3 run.py --tripletrail ../../core/target/release/tripletrail --sparql-anything lib

`lib` holds the SPARQL Anything jars (see the README: Maven fetches them from Maven
Central). Leave out --sparql-anything to run TripleTrail only. Both write N-Triples to out/,
which is counted, compared (sorted, so that blank nodes would not matter: these queries
write none) and removed. Not for CI.
"""

import argparse
import os
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("--tripletrail", default="tripletrail")
p.add_argument("--sparql-anything", help="folder of the SPARQL Anything jars")
p.add_argument("--java", default="java")
p.add_argument("--heap", default="12g", help="the JVM's -Xmx for SPARQL Anything")
p.add_argument("--queries", nargs="*", default=["csv", "json", "xml"])
p.add_argument("--keep", action="store_true", help="keep out/*.nt")
a = p.parse_args()
os.makedirs("out", exist_ok=True)

# Runs a command in a fresh Python, so that ru_maxrss is the command's own: wall seconds, peak
# RSS (MiB) and exit code.
MEASURE = """
import resource,subprocess,sys,time
s = time.perf_counter()
rc = subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
t = time.perf_counter() - s
m = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
print(f"{t:.2f}\\t{m / 1024:.0f}\\t{rc}")
"""


def measured(cmd):
    r = subprocess.run([sys.executable, "-c", MEASURE, *cmd], capture_output=True, text=True)
    t, m, rc = r.stdout.strip().split("\t")
    return float(t), int(m), int(rc)


def lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def sort(path):
    subprocess.run(["sort", "-u", "-o", path, path], check=True, env={**os.environ, "LC_ALL": "C"})


print("query\ttool\ttime (s)\tpeak memory (MiB)\ttriples")
for q in a.queries:
    query = f"queries/{q}.rq"
    tt = f"out/{q}-tripletrail.nt"
    t, m, rc = measured([a.tripletrail, "lift", query, "--output", tt])
    print(f"{q}\ttripletrail\t{t}\t{m}\t{lines(tt)}" + ("" if rc == 0 else f"\tfailed ({rc})"), flush=True)
    if a.sparql_anything:
        sa = f"out/{q}-sparql-anything.nt"
        cmd = [
            a.java, f"-Xmx{a.heap}", "-cp", os.path.join(a.sparql_anything, "*"),
            "io.github.sparqlanything.cli.SPARQLAnything", "-q", query, "-f", "NT", "-o", sa,
        ]
        t, m, rc = measured(cmd)
        print(f"{q}\tsparql-anything\t{t}\t{m}\t{lines(sa)}" + ("" if rc == 0 else f"\tfailed ({rc})"), flush=True)
        if rc == 0 and os.path.exists(tt):
            sort(tt)
            sort(sa)
            same = subprocess.run(["cmp", "-s", tt, sa]).returncode == 0
            print(f"{q}\tsame triples\t{'yes' if same else 'NO'}", flush=True)
        if not a.keep and os.path.exists(sa):
            os.remove(sa)
    if not a.keep and os.path.exists(tt):
        os.remove(tt)
