#!/usr/bin/env python3
"""SHACL suite, phase 0: run the ERA RINF shapes on one RINF graph with each engine's own
command-line validator, and record whether it ran, its time, peak memory and report size.

  run_phase0.py <data.nt> <shapes.ttl> <out dir> [engine ...]

<data.nt> is the RINF graph with the ERA ontology and SKOS code lists appended (the shapes read
`skos:` concepts), as fetch_shapes.sh and fetch_rinf.py make it. Each engine writes its report
to <out dir>/<engine>.report.ttl; <out dir>/<engine>.json holds the measurements and
<out dir>/<engine>.log the engine's standard error. The report holds RINF values, so it stays
in the work directory: only the JSON goes into results/.

Engines and the commands they need (set the paths with the environment variables):
  tripletrail   TRIPLETRAIL_BIN (default `tripletrail`): tripletrail validate
  jena          JENA_HOME: the apache-jena distribution's bin/shacl validate
  topbraid      TOPBRAID_HOME: TopBraid SHACL API's bin/shaclvalidate.sh
  pyshacl       the pyshacl command (pip install pyshacl), with -a (SHACL-AF: SPARQL targets,
                functions and rules)
  graphdb       Docker and GRAPHDB_IMAGE (default GraphDB 10.8.0): graphdb_validate.sh; its peak
                memory is that of the container, read by graphdb_validate.sh, not of the script
  rdf4j         RDF4J_JAR (default rdf4j/target/rdf4j-shacl-validate.jar, `mvn package` in rdf4j/):
                ShaclSail on a memory store, bulk validation of one transaction
"""
import hashlib
import json
import os
import re
import resource
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = int(os.environ.get("SHACL_TIMEOUT", "3600"))
SH = "http://www.w3.org/ns/shacl#"


def commands(data, shapes, report):
    tt = os.environ.get("TRIPLETRAIL_BIN", "tripletrail")
    jena = os.environ.get("JENA_HOME", "apache-jena")
    tq = os.environ.get("TOPBRAID_HOME", "shacl")
    return {
        "tripletrail": ([tt, "validate", "--data", data, "--shapes", shapes, "--report", report], None),
        "jena": ([f"{jena}/bin/shacl", "validate", "--shapes", shapes, "--data", data], report),
        "topbraid": (["sh", f"{tq}/bin/shaclvalidate.sh", "-datafile", data, "-shapesfile", shapes], report),
        "pyshacl": (["pyshacl", "-a", "-s", shapes, "-f", "turtle", "-o", report, data], None),
        "graphdb": (["bash", os.path.join(HERE, "graphdb_validate.sh"), data, shapes, report], None),
        "rdf4j": (["java", f"-Xmx{os.environ.get('JAVA_HEAP', '12g')}", f"-Xss{os.environ.get('JAVA_STACK', '1g')}", "-jar", os.environ.get(
            "RDF4J_JAR", os.path.join(HERE, "rdf4j", "target", "rdf4j-shacl-validate.jar")), data, shapes, report], None),
    }


def version(engine):
    try:
        if engine == "tripletrail":
            return subprocess.run([os.environ.get("TRIPLETRAIL_BIN", "tripletrail"), "--version"],
                                  capture_output=True, text=True).stdout.strip()
        if engine == "pyshacl":
            import pyshacl
            return f"pyshacl {pyshacl.__version__}"
        if engine == "jena":
            return os.path.basename(os.path.realpath(os.environ.get("JENA_HOME", "")))
        if engine == "graphdb":
            return os.environ.get("GRAPHDB_IMAGE", "mirror.gcr.io/ontotext/graphdb:10.8.0").rsplit("/", 1)[-1]
        if engine == "rdf4j":
            return "rdf4j 5.3.2"
        if engine == "topbraid":
            return os.path.basename(os.path.realpath(os.environ.get("TOPBRAID_HOME", "")))
    except OSError:
        pass
    return None


def count_report(path, keys_out=None):
    """Results in the report, by severity, and whether it says it conforms. With JENA_HOME set,
    Jena's riot turns the report into N-Triples, read line by line (a report of a million results
    is too big for rdflib); otherwise rdflib reads it. With keys_out, the sorted distinct result
    keys are also written there (they hold RINF values: a work file, never published)."""
    jena = os.environ.get("JENA_HOME")
    if jena and os.path.exists(f"{jena}/bin/riot"):
        return count_report_nt(path, f"{jena}/bin/riot", keys_out)
    return count_report_rdflib(path, keys_out)


NT = re.compile(r'^(\S+) <([^>]*)> (.*) \.$')
FIELDS = {SH + "focusNode": 0, SH + "resultPath": 1, SH + "sourceConstraintComponent": 2,
          SH + "resultSeverity": 3}


def count_report_nt(path, riot, keys_out=None):
    # riot's warnings go to a file: a pipe read only after stdout could fill and hang it.
    errf = tempfile.TemporaryFile(mode="w+")
    p = subprocess.Popen([riot, "--syntax=turtle", "--output=nt", path], stdout=subprocess.PIPE,
                         stderr=errf, text=True)
    results, fields, conforms, shapes = set(), {}, None, {}
    for line in p.stdout:
        m = NT.match(line.rstrip("\n"))
        if not m:
            continue
        s, pred, o = m.groups()
        if pred == SH + "result":
            results.add(o)
        elif pred in FIELDS:
            v = "_:" if o.startswith("_:") else o[1:-1] if o.startswith("<") else o
            fields.setdefault(s, [None] * 4)[FIELDS[pred]] = v
        elif pred == SH + "conforms":
            conforms = o.startswith('"true"')
        elif pred == SH + "sourceShape":
            shapes[s] = o
    if p.wait() != 0:
        errf.seek(0)
        return {"report_parse_error": errf.read().strip()[-300:]}
    sev, keys = {}, []
    for r in results:
        f = fields.get(r, [None] * 4)
        k = (f[3] or "none").rsplit("#", 1)[-1]
        sev[k] = sev.get(k, 0) + 1
        keys.append("\t".join("None" if v is None else v for v in f))
    return summary(sev, keys, conforms, {shapes.get(r) for r in results}, keys_out)


def summary(sev, keys, conforms, shapes, keys_out=None):
    keys = sorted(set(keys))
    if keys_out:
        with open(keys_out, "w", encoding="utf-8") as f:
            f.writelines(k + "\n" for k in keys)
    return {"results": sum(sev.values()), "by_severity": sev, "conforms": conforms,
            "shapes_with_results": len(shapes), "distinct_results": len(keys),
            "results_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest()}


def count_report_rdflib(path, keys_out=None):
    """count_report with rdflib."""
    import rdflib
    g = rdflib.Graph()
    try:
        g.parse(path, format="turtle")
    except Exception as e:  # noqa: BLE001 - any parse error is a finding of its own
        return {"report_parse_error": str(e)[:300]}
    sev, keys = {}, []
    for r in g.objects(None, rdflib.URIRef(SH + "result")):
        s = g.value(r, rdflib.URIRef(SH + "resultSeverity"))
        k = str(s).rsplit("#", 1)[-1] if s else "none"
        sev[k] = sev.get(k, 0) + 1
        # Engines name blank property shapes differently, so a result is keyed by what every
        # report has: focus node, path, constraint component and severity.
        # A blank node (a complex path) is keyed as "_:".
        keys.append("\t".join("_:" if isinstance(v, rdflib.BNode) else str(v) for v in (
            g.value(r, rdflib.URIRef(SH + x)) for x in
            ("focusNode", "resultPath", "sourceConstraintComponent", "resultSeverity"))))
    conforms = [bool(o.toPython()) for o in g.objects(None, rdflib.URIRef(SH + "conforms"))]
    shapes = {str(g.value(r, rdflib.URIRef(SH + "sourceShape")))
              for r in g.objects(None, rdflib.URIRef(SH + "result"))}
    return summary(sev, keys, conforms[0] if conforms else None, shapes, keys_out)


def run(engine, cmd, stdout_to, out):
    log = open(os.path.join(out, f"{engine}.log"), "w")
    sink = open(stdout_to, "w") if stdout_to else subprocess.DEVNULL
    t0 = time.monotonic()
    # Its own process group, so a timeout ends the engine's children too (curl, the JVM under a
    # launcher script), not only the command.
    p = subprocess.Popen(cmd, stdout=sink, stderr=log, start_new_session=True)
    status, timed_out = None, False
    while status is None:
        pid, st, ru = os.wait4(p.pid, os.WNOHANG)
        if pid:
            status = st
            break
        if time.monotonic() - t0 > TIMEOUT:
            # TERM first, so a wrapper's cleanup (graphdb_validate.sh removes its container on
            # exit) runs; KILL after 30 s.
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            for _ in range(150):
                pid, status, ru = os.wait4(p.pid, os.WNOHANG)
                if pid:
                    break
                time.sleep(0.2)
            else:
                os.killpg(p.pid, signal.SIGKILL)
                _, status, ru = os.wait4(p.pid, 0)
            timed_out = True
            break
        time.sleep(0.2)
    # The engine's time, before the cleanup below.
    wall = time.monotonic() - t0
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    if engine == "graphdb":
        # A GraphDB container left running holds tens of GB, and the next engine then runs out
        # of memory (run 45816390204 lost its runner that way, rdf4j after a GraphDB timeout).
        subprocess.run(["docker", "rm", "-f", "shacl-graphdb"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
    # ru_maxrss (kB on Linux) as wait4 answers it: the largest of the child and of every
    # descendant it waited for, so the JVM under a launcher script counts, and engines run one
    # after the other in one process do not inherit each other's peak.
    peak = ru.ru_maxrss * 1024
    return {"exit": os.waitstatus_to_exitcode(status), "timed_out": timed_out,
            "wall_s": round(wall, 3), "peak_rss_bytes": peak}


def need_rdflib():
    """Reports are read with rdflib; without it every engine would look as if it gave nothing."""
    try:
        import rdflib  # noqa: F401
    except ImportError:
        sys.exit("rdflib is needed to read the reports: pip install rdflib")


def main():
    need_rdflib()
    data, shapes, out, *engines = sys.argv[1:]
    os.makedirs(out, exist_ok=True)
    engines = engines or list(commands(data, shapes, ""))
    if len(engines) > 1:
        # One process per engine: RUSAGE_CHILDREN keeps the largest child ever waited for.
        for engine in engines:
            subprocess.run([sys.executable, __file__, data, shapes, out, engine], check=False)
        return
    for engine in engines:
        report = os.path.join(out, f"{engine}.report.ttl")
        cmd, stdout_to = commands(data, shapes, report)[engine]
        rec = {"engine": engine, "version": version(engine), "timeout_s": TIMEOUT}
        rec.update(run(engine, cmd, stdout_to, out))
        if os.path.exists(report) and os.path.getsize(report):
            rec["report_bytes"] = os.path.getsize(report)
            rec.update(count_report(report))
        with open(os.path.join(out, f"{engine}.log")) as f:
            log = f.read()
        tail = log[-1500:]
        m = re.search(r"container peak memory (\d+) bytes", log)
        if m and int(m.group(1)):
            rec["peak_rss_bytes"] = int(m.group(1))
        rec["stderr_tail"] = tail
        json.dump(rec, open(os.path.join(out, f"{engine}.json"), "w"), indent=1)
        print(json.dumps({k: v for k, v in rec.items() if k != "stderr_tail"}), flush=True)


if __name__ == "__main__":
    main()
