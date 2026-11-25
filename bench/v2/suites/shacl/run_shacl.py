#!/usr/bin/env python3
"""SHACL validation suite: the ERA RINF shapes, in three profiles, on a RINF dataset, with each
engine's own validator (tracker: #30; phase 0 and the engine commands: run_phase0.py).

  run_shacl.py setup                       engines into $BENCH_WORK/shacl-engines (downloads, a
                                           Python venv, the RDF4J jar built in a Maven container)
  run_shacl.py run --dataset D [--engine E ...]
                                           D = rinf-<graph code> (rinf-0076 Norway, rinf-0080
                                           Germany) or rinf-all; fetches data and shapes on first use
  run_shacl.py report                      results/shacl/report.md from every results/shacl/<D>/

Profiles, all made at run time from ERA's ERA-RINF-shapes.ttl (fetch_shapes.sh):
  core       the SHACL Core part: every sh:sparql constraint and every SPARQL target removed
  era-local  the shapes as published minus those ERA marks era:scope "global" (5 SPARQL
             constraints and 2 property shapes), so a country graph can be validated on its own
  era        the shapes as published

Each engine validates <D> plus the ERA ontology and code lists (one N-Triples file) with each
profile, and results/shacl/<D>/<profile>/<engine>.json gets: every run's wall time (the whole
command: start, parsing, validation, report), the median, the validation time where the engine
logs it, peak memory, the results by severity and the SHA-256 of the sorted result keys (focus
node, path, constraint component, severity). A run under SHACL_REPEAT_BELOW seconds (300) is
repeated twice more. A timeout (SHACL_TIMEOUT, 3600 s) or a crash is recorded as the result,
and an engine that times out skips the dataset's later profiles; an engine that timed out or
failed on a profile of a smaller dataset (one already in results/shacl/) skips it on this one. Reports hold RINF values, so
they stay in $BENCH_WORK; only the JSON is committed.
"""
import argparse
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import run_phase0  # noqa: E402

W = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
ENG = os.path.join(W, "shacl-engines")
RESULTS = os.path.join(V2, "results", "shacl")
ENGINES = ["tripletrail", "jena", "topbraid", "graphdb", "rdf4j", "pyshacl"]
PROFILES = ["core", "era-local", "era"]
REPEAT_BELOW = float(os.environ.get("SHACL_REPEAT_BELOW", "300"))

# Pinned downloads (SHA-256 checked).
JENA = ("apache-jena-6.2.0", "https://archive.apache.org/dist/jena/binaries/apache-jena-6.2.0.tar.gz",
        "14c12ef4aa2f0078a473be4b10b015e0e0b85e767d6867e8581679de8fec3f6e")
TOPBRAID = ("shacl-1.5.0", "https://repo1.maven.org/maven2/org/topbraid/shacl/1.5.0/shacl-1.5.0-bin.zip",
            "d09f945c1108cca20aca6110089c3078e762e0c45acaf3c9cd6ac2b08830da71")
PIP = ["rdflib==7.6.0", "pyshacl==0.30.1", "requests"]
MAVEN_IMAGE = "mirror.gcr.io/library/maven:3.9-eclipse-temurin-21"


def sh(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def fetch(url, sha, out):
    if not os.path.exists(out):
        sh(["curl", "-sSfL", "--retry", "4", "-o", out + ".part", url])
        os.replace(out + ".part", out)
    got = subprocess.run(["sha256sum", out], capture_output=True, text=True).stdout.split()[0]
    if got != sha:
        sys.exit(f"{out}: SHA-256 {got}, expected {sha}")


def setup():
    os.makedirs(ENG, exist_ok=True)
    name, url, sha = JENA
    if not os.path.isdir(os.path.join(ENG, name)):
        fetch(url, sha, os.path.join(ENG, name + ".tar.gz"))
        sh(["tar", "xzf", os.path.join(ENG, name + ".tar.gz"), "-C", ENG])
    name, url, sha = TOPBRAID
    if not os.path.isdir(os.path.join(ENG, name)):
        fetch(url, sha, os.path.join(ENG, name + ".zip"))
        sh(["unzip", "-q", "-o", os.path.join(ENG, name + ".zip"), "-d", ENG])
    venv = os.path.join(ENG, "py")
    if not os.path.exists(os.path.join(venv, "bin", "pyshacl")):
        sh([sys.executable, "-m", "venv", venv])
        sh([os.path.join(venv, "bin", "pip"), "install", "-q"] + PIP)
    jar = os.path.join(ENG, "rdf4j-shacl-validate.jar")
    if not os.path.exists(jar):
        # Java 21 has no Maven on the bench server: build the jar in a Maven container.
        build = os.path.join(ENG, "rdf4j-build")
        shutil.rmtree(build, ignore_errors=True)
        shutil.copytree(os.path.join(HERE, "rdf4j"), build, ignore=shutil.ignore_patterns("target"))
        sh(["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
            "-v", f"{build}:/src", "-w", "/src", MAVEN_IMAGE,
            "mvn", "-q", "-B", "-Dmaven.repo.local=/tmp/m2", "package", "-DskipTests"])
        shutil.copy(os.path.join(build, "target", "rdf4j-shacl-validate.jar"), jar)
    print("engines ready in", ENG)


def error_line(log, code):
    """The line of an engine's log that names its error: the first Java exception or error (not
    the last line of a stack trace), else the last line."""
    lines = open(log, errors="replace").read().strip().splitlines()
    for line in lines:
        if re.search(r"(Exception|Error)\b", line) and not line.lstrip().startswith("at "):
            return line.strip()[:300]
    return lines[-1].strip()[:300] if lines else f"exit {code}"


def engine_env():
    """The environment run_phase0's commands read, pointing at the engines of setup()."""
    heap = os.environ.get("JAVA_HEAP", "48g")
    stack = os.environ.get("JAVA_STACK", "1g")
    env = {
        "JENA_HOME": os.path.join(ENG, JENA[0]),
        "TOPBRAID_HOME": os.path.join(ENG, TOPBRAID[0]),
        "RDF4J_JAR": os.path.join(ENG, "rdf4j-shacl-validate.jar"),
        "JAVA_HEAP": heap,
        # A deep thread stack: java.util.regex recurses once per repetition, so a sh:pattern on a
        # long literal (all of RINF has some) overflows the default 1 MB stack.
        "JAVA_STACK": stack,
        "JVM_ARGS": f"-Xmx{heap} -Xss{stack}",
        "GRAPHDB_HEAP": os.environ.get("GRAPHDB_HEAP", heap),
        "PATH": os.path.join(ENG, "py", "bin") + os.pathsep + os.environ["PATH"],
    }
    if "TRIPLETRAIL_BIN" not in os.environ:
        core = os.path.join(V2, "..", "..", "core", "target", "release", "tripletrail")
        env["TRIPLETRAIL_BIN"] = os.path.abspath(core) if os.path.exists(core) else "tripletrail"
    return env


def profiles(shapes_ttl, out_dir):
    """Writes core.ttl, era-local.ttl and era.ttl into out_dir (rdflib; the shapes are small)."""
    import rdflib
    from rdflib.namespace import RDF
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    SCOPE = rdflib.URIRef("http://data.europa.eu/949/scope")
    os.makedirs(out_dir, exist_ok=True)
    era = rdflib.Graph().parse(shapes_ttl)
    shutil.copy(shapes_ttl, os.path.join(out_dir, "era.ttl"))

    local = rdflib.Graph()
    for t in era:
        local.add(t)
    for node in set(era.subjects(SCOPE, rdflib.Literal("global"))):
        # Unlinked from every shape, a global constraint or property shape is never checked.
        for s, p in list(local.subject_predicates(node)):
            local.remove((s, p, node))
    local.serialize(os.path.join(out_dir, "era-local.ttl"), format="turtle")

    core = rdflib.Graph()
    for t in era:
        core.add(t)
    for s, c in list(core.subject_objects(SH.sparql)):
        core.remove((s, SH.sparql, c))
    for s, t in list(core.subject_objects(SH.target)):
        if (t, RDF.type, SH.SPARQLTarget) in core:
            core.remove((s, SH.target, t))
    core.serialize(os.path.join(out_dir, "core.ttl"), format="turtle")
    return {p: os.path.join(out_dir, f"{p}.ttl") for p in PROFILES}


def prepare(ds):
    """The dataset's data file (RINF + lookup) and the three profiles."""
    data_dir = os.path.join(W, "data")
    shacl_dir = os.path.join(data_dir, "shacl")
    env = dict(os.environ, **engine_env())
    rinf = os.path.join(data_dir, f"{ds}.nt")
    if not os.path.exists(rinf):
        sh([sys.executable, os.path.join(V2, "suites", "data", "fetch_rinf.py"), ds.removeprefix("rinf-")], env=env)
    if not os.path.exists(os.path.join(shacl_dir, "lookup.nt")):
        sh([os.path.join(HERE, "fetch_shapes.sh")], env=env)
    data = os.path.join(shacl_dir, f"{ds}.nt")
    if not os.path.exists(data):
        with open(data + ".part", "wb") as out:
            for f in (rinf, os.path.join(shacl_dir, "lookup.nt")):
                with open(f, "rb") as src:
                    shutil.copyfileobj(src, out, 1 << 24)
        os.replace(data + ".part", data)
    return data, profiles(os.path.join(shacl_dir, "era-rinf-shapes.ttl"), os.path.join(shacl_dir, "profiles"))


def validation_seconds(engine, log):
    """The validation time an engine logs apart from loading, where it does."""
    import re
    pats = {"tripletrail": r"(?:does not conform|conforms) in ([\d.]+) s",
            "graphdb": r"validated in ([\d.]+) s",
            "rdf4j": r"(?:does not conform|conforms) in ([\d.]+) s"}
    m = re.search(pats[engine], log) if engine in pats else None
    return float(m.group(1)) if m else None


def run_one(engine, data, shapes, out):
    """One engine on one profile: one run, or three when it is quick."""
    report = os.path.join(out, f"{engine}.report.ttl")
    cmd, stdout_to = run_phase0.commands(data, shapes, report)[engine]
    runs = []
    while True:
        if os.path.exists(report):
            os.remove(report)
        r = run_phase0.run(engine, cmd, stdout_to, out)
        log = open(os.path.join(out, f"{engine}.log")).read()
        m = __import__("re").search(r"container peak memory (\d+) bytes", log)
        if m and int(m.group(1)):
            r["peak_rss_bytes"] = int(m.group(1))
        r["validate_s"] = validation_seconds(engine, log)
        runs.append(r)
        if r["timed_out"] or r["exit"] not in (0, 1) or r["wall_s"] >= REPEAT_BELOW or len(runs) == 3:
            break
    rec = {"engine": engine, "version": run_phase0.version(engine), "timeout_s": run_phase0.TIMEOUT,
           "runs": runs, "wall_s": statistics.median(r["wall_s"] for r in runs),
           "peak_rss_bytes": max(r["peak_rss_bytes"] for r in runs),
           "timed_out": runs[-1]["timed_out"], "exit": runs[-1]["exit"]}
    v = [r["validate_s"] for r in runs if r["validate_s"] is not None]
    if v:
        rec["validate_s"] = statistics.median(v)
    if os.path.exists(report) and os.path.getsize(report) and not rec["timed_out"]:
        rec["report_bytes"] = os.path.getsize(report)
        rec.update(run_phase0.count_report(report))
    if "results" not in rec:
        rec["error"] = "timed out" if rec["timed_out"] else error_line(os.path.join(out, f"{engine}.log"), rec["exit"])
    # The report holds RINF values: it is not kept once counted.
    if os.path.exists(report):
        os.remove(report)
    return rec


def run(ds, engines):
    run_phase0.need_rdflib()
    env = engine_env()
    os.environ.update(env)
    data, shapes = prepare(ds)
    work = os.path.join(W, "shacl", ds)
    timed_out = set()
    triples = sum(1 for _ in open(data, "rb"))
    for profile in PROFILES:
        res = os.path.join(RESULTS, ds, profile)
        os.makedirs(res, exist_ok=True)
        os.makedirs(os.path.join(work, profile), exist_ok=True)
        for engine in engines:
            smaller = failed_on_smaller(ds, triples, profile, engine)
            if engine in timed_out:
                rec = {"engine": engine, "skipped": "timed out on an earlier profile of this dataset"}
            elif smaller:
                rec = {"engine": engine, "skipped": smaller}
            else:
                print(f"=== shacl {ds} {profile} on {engine}", flush=True)
                rec = run_one(engine, data, shapes[profile], os.path.join(work, profile))
                if rec.get("timed_out"):
                    timed_out.add(engine)
                if "error" in rec:
                    print(f"!!! shacl {ds} {profile} failed on {engine}: {rec['error']}", flush=True)
            json.dump(rec, open(os.path.join(res, f"{engine}.json"), "w"), indent=1)
            print(json.dumps({k: v for k, v in rec.items() if k != "runs"}), flush=True)
    meta = {"dataset": ds, "data_triples": triples,
            "shapes_sha256": subprocess.run(["sha256sum", shapes["era"]], capture_output=True,
                                            text=True).stdout.split()[0],
            "profiles": {p: sum(1 for line in open(f) if line.strip()) for p, f in shapes.items()}}
    json.dump(meta, open(os.path.join(RESULTS, ds, "data.json"), "w"), indent=1)
    report()


def failed_on_smaller(ds, triples, profile, engine):
    """Why to skip: the engine timed out or failed on this profile of a smaller dataset."""
    for d in glob.glob(os.path.join(RESULTS, "*", "data.json")):
        meta = json.load(open(d))
        if meta["dataset"] == ds or meta["data_triples"] >= triples:
            continue
        f = os.path.join(os.path.dirname(d), profile, f"{engine}.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        if r.get("timed_out") or ("error" in r and "skipped" not in r):
            return f"{'timed out' if r.get('timed_out') else 'failed'} on {meta['dataset']}"
        if "skipped" in r:
            # Skipped there (after a timeout on an earlier profile, or on a smaller dataset still).
            return f"skipped on {meta['dataset']}: {r['skipped']}"
    return None


def agreement(recs):
    """Per engine: same keys as TopBraid's, and as the majority's (most engines with one hash)."""
    hashes = {e: r.get("results_sha256") for e, r in recs.items() if r.get("results_sha256")}
    counts = {}
    for h in hashes.values():
        counts[h] = counts.get(h, 0) + 1
    major = max(counts, key=counts.get) if counts and max(counts.values()) > 1 else None
    tq = hashes.get("topbraid")
    return {e: ("yes" if tq and h == tq else "no" if tq else "", "yes" if major and h == major else "no" if major else "")
            for e, h in hashes.items()}


def fmt(x, d=1):
    return "" if x is None else f"{x:,.{d}f}"


def results_cell(r):
    """Results, and the distinct result keys when fewer: an engine can give several results with
    the same key (another value or message of one focus node and path)."""
    d = r.get("distinct_results")
    return f"{r['results']:,}" + (f" ({d:,} distinct)" if d is not None and d != r["results"] else "")


def report():
    out = ["# SHACL validation suite", "",
           "The ERA RINF shapes on RINF data, in three profiles (`suites/shacl/run_shacl.py`): `core` is "
           "SHACL Core only, `era-local` leaves out the shapes ERA marks as global, `era` is the shapes as "
           "published. Time is the whole command (median of 3 runs when under "
           f"{REPEAT_BELOW:.0f} s), validation is the engine's own validation time where it logs one. Same "
           "results compares the sorted result keys (focus node, path, constraint component, severity) with "
           "TopBraid's and with the majority's; results shows the distinct keys too when an engine gives "
           "several results with one key.", ""]
    for d in sorted(glob.glob(os.path.join(RESULTS, "*", "data.json"))):
        ds_dir = os.path.dirname(d)
        meta = json.load(open(d))
        out += [f"## {meta['dataset']} ({meta['data_triples']:,} triples with the ontology and code lists)", ""]
        for profile in PROFILES:
            recs = {os.path.basename(p)[:-5]: json.load(open(p))
                    for p in sorted(glob.glob(os.path.join(ds_dir, profile, "*.json")))}
            if not recs:
                continue
            agree = agreement(recs)
            out += [f"### {profile}", "",
                    "| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |",
                    "|---|---:|---:|---:|---:|---:|---:|---|---|"]
            for e in ENGINES:
                r = recs.get(e)
                if not r:
                    continue
                if "skipped" in r:
                    out.append(f"| {e} | skipped: {r['skipped']} | | | | | | | |")
                    continue
                if "results" not in r:
                    out.append(f"| {e} | {fmt(r['wall_s'])} ({r.get('error', '')}) | | {fmt(r['peak_rss_bytes'] / 2**20, 0)} | | | | | |")
                    continue
                sev = r.get("by_severity", {})
                a = agree.get(e, ("", ""))
                out.append(f"| {e} | {fmt(r['wall_s'])} | {fmt(r.get('validate_s'))} | "
                           f"{fmt(r['peak_rss_bytes'] / 2**20, 0)} | {results_cell(r)} | {sev.get('Violation', 0):,} | "
                           f"{sev.get('Warning', 0):,} | {a[0]} | {a[1]} |")
            out.append("")
    notes = os.path.join(RESULTS, "notes.md")
    if os.path.exists(notes):
        out += [open(notes).read().strip(), ""]
    os.makedirs(RESULTS, exist_ok=True)
    open(os.path.join(RESULTS, "report.md"), "w").write("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    r = sub.add_parser("run")
    r.add_argument("--dataset", required=True)
    r.add_argument("--engine", action="append")
    sub.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "setup":
        setup()
    elif a.cmd == "run":
        run(a.dataset, a.engine or ENGINES)
    else:
        report()


if __name__ == "__main__":
    main()
