"""Runs the RML throughput benchmark: each mapping with `tripletrail lift`, Morph-KGC and
RMLMapper, printing wall time, peak memory and triples. Run from this folder after gen.py:

    python3 run.py --tripletrail ../../core/target/release/tripletrail \
        --morph-python /path/to/venv/bin/python --rmlmapper data/rmlmapper.jar

Morph-KGC (Apache-2.0) is installed with `pip install morph-kgc` in its own venv, and
RMLMapper (MIT, a Java jar) is fetched with `fetch_rmlmapper.sh`; leave either out to skip
it. RMLMapper runs with `--java` (default `java`), or in a Java container with
`--java-image`, whose peak memory is then the JVM's peak resident memory. TripleTrail's triples are counted
from its standard output; the others write a file to out/, counted and then removed.
`--timeout` stops a run after that many seconds. Not for CI.
"""

import argparse
import os
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--tripletrail", default="tripletrail")
p.add_argument("--morph-python")
p.add_argument("--morph-processes", help="Morph-KGC's number_of_processes (default: its own)")
p.add_argument("--rmlmapper", help="the RMLMapper jar")
p.add_argument("--java", default="java")
p.add_argument("--java-image", help="run RMLMapper with docker in this Java image")
p.add_argument("--java-heap", default="12g", help="RMLMapper's -Xmx")
p.add_argument("--timeout", type=int, default=7200)
p.add_argument("--tools", nargs="*", default=["tripletrail", "morph-kgc", "rmlmapper"])
p.add_argument("--mappings", nargs="*", default=["simple", "join"])
a = p.parse_args()
os.makedirs("out", exist_ok=True)

# Runs a command in a fresh Python, so that ru_maxrss is the command's own: wall seconds,
# peak RSS (MiB), exit code and the lines of its standard output (or of the file `count`).
# A command in a container prints its peak memory in bytes as the last line of its standard
# error ("peak N"), which then stands in for ru_maxrss. After `timeout` seconds
# the command is stopped (its process group, or the container `name`).
MEASURE = """
import os,resource,signal,subprocess,sys,threading,time
count, timeout, name, cmd = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
s = time.perf_counter()
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
err = []
threading.Thread(target=lambda: err.extend(p.stderr), daemon=True).start()
def stop():
    if name:
        subprocess.run(["docker", "kill", name], capture_output=True)
    os.killpg(p.pid, signal.SIGKILL)
timer = threading.Timer(timeout, stop)
timer.start()
n = sum(1 for _ in p.stdout)
rc = p.wait()
timer.cancel()
t = time.perf_counter() - s
timed_out = t >= timeout
if count:
    n = sum(1 for _ in open(count, "rb")) if rc == 0 else 0
    if os.path.exists(count):
        os.remove(count)
m = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024
peak = [l.split() for l in err if l.startswith(b"peak ")]
if name:
    # The docker client's own memory says nothing: the command's, if it could read it.
    m = int(peak[-1][1]) if peak and peak[-1][1:2] and peak[-1][1].isdigit() else None
state = "" if rc == 0 else (f", stopped after {timeout} s" if timed_out else f", failed ({rc})")
memory = "? MiB" if m is None else f"{m / 2**20:.0f} MiB"
print(f"{t:.1f} s, {memory}, {n} triples" + state)
"""


def measured(cmd, count="", name=""):
    r = subprocess.run(
        ["python3", "-c", MEASURE, count, str(a.timeout), name, *cmd],
        capture_output=True,
        text=True,
    )
    return r.stdout.strip() or r.stderr.strip()


def rmlmapper(name, out):
    """The command that runs RMLMapper on a mapping, writing N-Quads to `out`."""
    args = ["-m", f"{name}.rml.ttl", "-o", out, "-s", "nquads"]
    if not a.java_image:
        return [a.java, f"-Xmx{a.java_heap}", "-jar", a.rmlmapper, *args]
    here = os.getcwd()
    jar = os.path.abspath(a.rmlmapper)
    # The JVM's peak resident memory (VmHWM, which only grows), read every half second while
    # it runs: as ru_maxrss is for the other tools, with cgroup v1 or v2.
    script = (
        f'java -Xmx{a.java_heap} -jar /jar/rmlmapper.jar "$@" & pid=$!; hwm=; '
        'while kill -0 $pid 2>/dev/null; do '
        'h=$(grep VmHWM /proc/$pid/status 2>/dev/null | tr -dc 0-9); [ -n "$h" ] && hwm=$h; '
        'sleep 0.5; done; wait $pid; rc=$?; '
        '[ -n "$hwm" ] && echo "peak $((hwm * 1024))" >&2; exit $rc'
    )
    return [
        "docker", "run", "--rm", "--name", f"rml-{name}", "-u", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{here}:/w", "-v", f"{jar}:/jar/rmlmapper.jar:ro", "-w", "/w", a.java_image,
        "sh", "-c", script, "sh", *args,
    ]


for name in a.mappings:
    if "tripletrail" in a.tools:
        print(f"{name} tripletrail: {measured([a.tripletrail, 'lift', f'{name}.rml.ttl'])}", flush=True)
    if a.morph_python and "morph-kgc" in a.tools:
        out = f"out/{name}-morph.nt"
        ini = f"out/{name}.ini"
        with open(ini, "w") as f:
            f.write(
                f"[CONFIGURATION]\noutput_file={out}\noutput_format=N-TRIPLES\n"
                + (f"number_of_processes={a.morph_processes}\n" if a.morph_processes else "")
                + f"[DataSource1]\nmappings={name}.rml.ttl\n"
            )
        print(f"{name} morph-kgc: {measured([a.morph_python, '-m', 'morph_kgc', ini], out)}", flush=True)
    if a.rmlmapper and "rmlmapper" in a.tools:
        out = f"out/{name}-rmlmapper.nq"
        name_ = f"rml-{name}" if a.java_image else ""
        print(f"{name} rmlmapper: {measured(rmlmapper(name, out), out, name_)}", flush=True)
