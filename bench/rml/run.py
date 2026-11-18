"""Runs the RML throughput benchmark: each mapping with `tripletrail lift` and with Morph-KGC,
printing wall time, peak memory and triples. Run from this folder after gen.py:

    python3 run.py --tripletrail ../../core/target/release/tripletrail --morph-python /path/to/venv/bin/python

Morph-KGC (Apache-2.0) is installed with `pip install morph-kgc` in its own venv; leave out
--morph-python to run TripleTrail only. TripleTrail's triples are counted from its standard
output; Morph-KGC writes a file to out/, counted and then removed. Not for CI.
"""

import argparse
import os
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--tripletrail", default="tripletrail")
p.add_argument("--morph-python")
p.add_argument("--mappings", nargs="*", default=["simple", "join"])
a = p.parse_args()
os.makedirs("out", exist_ok=True)

# Runs a command in a fresh Python, so that ru_maxrss is the command's own: wall seconds,
# peak RSS (MiB), exit code and the lines of its standard output (or of the file `count`).
MEASURE = """
import os,resource,subprocess,sys,time
count, cmd = sys.argv[1], sys.argv[2:]
s = time.perf_counter()
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
n = sum(1 for _ in p.stdout)
rc = p.wait()
t = time.perf_counter() - s
if count:
    n = sum(1 for _ in open(count, "rb")) if rc == 0 else 0
    if os.path.exists(count):
        os.remove(count)
m = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
print(f"{t:.1f} s, {m / 1024:.0f} MiB, {n} triples" + ("" if rc == 0 else f", failed ({rc})"))
"""


def measured(cmd, count=""):
    r = subprocess.run(["python3", "-c", MEASURE, count, *cmd], capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip()


for name in a.mappings:
    print(f"{name} tripletrail: {measured([a.tripletrail, 'lift', f'{name}.rml.ttl'])}", flush=True)
    if a.morph_python:
        out = f"out/{name}-morph.nt"
        ini = f"out/{name}.ini"
        with open(ini, "w") as f:
            f.write(
                f"[CONFIGURATION]\noutput_file={out}\noutput_format=N-TRIPLES\n"
                f"[DataSource1]\nmappings={name}.rml.ttl\n"
            )
        print(f"{name} morph-kgc: {measured([a.morph_python, '-m', 'morph_kgc', ini], out)}", flush=True)
