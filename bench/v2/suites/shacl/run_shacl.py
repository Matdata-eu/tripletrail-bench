#!/usr/bin/env python3
"""SHACL validation suite: the ERA RINF shapes, in three profiles, on a RINF dataset, with each
engine's own validator (tracker: #30; phase 0 and the engine commands: run_phase0.py).

  run_shacl.py setup                       engines into $BENCH_WORK/shacl-engines (downloads, a
                                           Python venv, the RDF4J jar built in a Maven container)
  run_shacl.py run --dataset D [--engine E ...]
                                           D = rinf-<graph code> (rinf-0076 Norway, rinf-0080
                                           Germany) or rinf-all; fetches data and shapes on first use
  run_shacl.py inject --dataset D [--engine E ...]
                                           seeded violations (inject.py) in D, validated with the
                                           era-local profile before and after: recall and precision
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
repeated twice more. Where engines' keys differ, results/shacl/<D>/<profile>/differences.json
counts the keys only one of them gives, by path, constraint component and severity, against
TopBraid's keys (or Jena's when TopBraid has none): it names no focus node (the key files stay
in $BENCH_WORK, for the engines run_suite.sh runs one at a time). A timeout (SHACL_TIMEOUT, 3600 s) or a crash is recorded as the result,
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
import inject  # noqa: E402
import run_phase0  # noqa: E402

W = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
ENG = os.path.join(W, "shacl-engines")
RESULTS = os.path.join(V2, "results", "shacl")
ENGINES = ["tripletrail", "jena", "topbraid", "graphdb", "rdf4j", "pyshacl"]
PROFILES = ["core", "era-local", "era"]
REPEAT_BELOW = float(os.environ.get("SHACL_REPEAT_BELOW", "300"))
INJECT_SEED = int(os.environ.get("SHACL_INJECT_SEED", "31"))
INJECT_RATE = float(os.environ.get("SHACL_INJECT_RATE", "0.01"))
INJECT_PROFILE = "era-local"

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


# Exception messages that cannot hold data. Any other message is left out: Java and Python
# messages quote the literal or IRI they failed on, and the results are public.
SAFE_MESSAGES = ("java.lang.OutOfMemoryError: Java heap space",)


def error_line(log, code):
    """What a failed engine's log says went wrong, without data: the class of its first exception
    or error (as `Exception in thread "main" X`, `Caused by: X` or a line starting with X), or our
    own scripts' `graphdb: ...` line, else the exit code."""
    cls = re.compile(r"^(?:Exception in thread \"[^\"]*\" |Caused by: )?([\w.$]+(?:Exception|Error))\b")
    for line in open(log, errors="replace").read().splitlines():
        line = line.strip()
        if line.startswith("graphdb: "):
            return line[:120]
        m = cls.match(line)
        if m:
            return next((s for s in SAFE_MESSAGES if s in line), m.group(1))
    return f"exit {code}"


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


def run_one(engine, data, shapes, out, keys_out=None, once=False):
    """One engine on one profile: one run, or three when it is quick (once: one run). With
    keys_out, the report's distinct result keys are written there (a work file)."""
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
        if once or r["timed_out"] or r["exit"] not in (0, 1) or r["wall_s"] >= REPEAT_BELOW or len(runs) == 3:
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
        rec.update(run_phase0.count_report(report, keys_out))
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
    # Engines the benchmark profile leaves out of this dataset (SHACL_SKIP, bench/v2/profiles):
    # shown in the report as not run, with the reason.
    left_out = os.environ.get("SHACL_SKIP", "").split()
    for profile in PROFILES:
        res = os.path.join(RESULTS, ds, profile)
        os.makedirs(res, exist_ok=True)
        for engine in left_out:
            json.dump({"engine": engine, "skipped": "left out of this dataset by the benchmark profile "
                       "(bench/v2/profiles/shacl.txt)"}, open(os.path.join(res, f"{engine}.json"), "w"), indent=1)
        keys_dir = os.path.join(work, profile, "keys")
        os.makedirs(keys_dir, exist_ok=True)
        for engine in engines:
            smaller = failed_on_smaller(ds, triples, profile, engine)
            if engine in timed_out:
                rec = {"engine": engine, "skipped": "timed out on an earlier profile of this dataset"}
            elif smaller:
                rec = {"engine": engine, "skipped": smaller}
            else:
                print(f"=== shacl {ds} {profile} on {engine}", flush=True)
                rec = run_one(engine, data, shapes[profile], os.path.join(work, profile),
                              os.path.join(keys_dir, f"{engine}.keys"))
                if rec.get("timed_out"):
                    timed_out.add(engine)
                if "error" in rec:
                    print(f"!!! shacl {ds} {profile} failed on {engine}: {rec['error']}", flush=True)
            json.dump(rec, open(os.path.join(res, f"{engine}.json"), "w"), indent=1)
            print(json.dumps({k: v for k, v in rec.items() if k != "runs"}), flush=True)
        differences(keys_dir, res)
    meta = {"dataset": ds, "data_triples": triples,
            "shapes_sha256": subprocess.run(["sha256sum", shapes["era"]], capture_output=True,
                                            text=True).stdout.split()[0],
            "profiles": {p: sum(1 for line in open(f) if line.strip()) for p, f in shapes.items()}}
    json.dump(meta, open(os.path.join(RESULTS, ds, "data.json"), "w"), indent=1)
    report()


def read_keys(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def key_diff(a, b):
    """The keys of sorted key files a and b that only one gives: (key, side), side "a" or "b"."""
    ia, ib = read_keys(a), read_keys(b)
    x, y = next(ia, None), next(ib, None)
    while x is not None or y is not None:
        if y is None or (x is not None and x < y):
            yield x, "a"
            x = next(ia, None)
        elif x is None or y < x:
            yield y, "b"
            y = next(ib, None)
        else:
            x, y = next(ia, None), next(ib, None)


def short(iri):
    """A SHACL IRI by its local name (sh:MinCountConstraintComponent as MinCountConstraintComponent)."""
    return iri.removeprefix("http://www.w3.org/ns/shacl#")


def keys_sha256(path):
    """The SHA-256 summary() gives the keys of a key file (joined by newlines, none at the end)."""
    import hashlib
    h = hashlib.sha256()
    for i, k in enumerate(read_keys(path)):
        h.update(("\n" if i else "").encode() + k.encode())
    return h.hexdigest()


def differences(keys_dir, res):
    """Compares each engine's result keys with the reference engine's (TopBraid, else Jena) and
    writes res/differences.json: per engine, the keys only it gives and those only the reference
    gives, counted by path, constraint component and severity. run_suite.sh runs one engine at a
    time, so the key files stay in the work directory (beside the RINF data they come from) for
    the next engine's run, and a key file counts only while its hash is the one in the engine's
    res/<engine>.json. The JSON holds no focus node."""
    files = {}
    for f in glob.glob(os.path.join(keys_dir, "*.keys")):
        engine = os.path.basename(f)[:-5]
        rec = os.path.join(res, f"{engine}.json")
        h = json.load(open(rec)).get("results_sha256") if os.path.exists(rec) else None
        if h and h == keys_sha256(f):
            files[engine] = f
        else:
            os.remove(f)
    ref = next((e for e in ("topbraid", "jena") if e in files), None)
    out = os.path.join(res, "differences.json")
    if os.path.exists(out):
        os.remove(out)
    found = {}
    for engine, f in sorted(files.items()):
        if ref is None or engine == ref:
            continue
        groups, totals = {}, {"a": 0, "b": 0}
        for key, side in key_diff(f, files[ref]):
            _, path, comp, sev = (key.split("\t") + [None] * 4)[:4]
            g = groups.setdefault((path, short(comp or "None"), short(sev or "None")), {"a": 0, "b": 0})
            g[side] += 1
            totals[side] += 1
        if groups:
            found[engine] = {"only_here": totals["a"], "only_in_reference": totals["b"], "by_path": [
                {"path": p, "component": c, "severity": s, "only_here": n["a"], "only_in_reference": n["b"]}
                for (p, c, s), n in sorted(groups.items(), key=lambda kv: -(kv[1]["a"] + kv[1]["b"]))]}
    if found:
        json.dump({"reference": ref, "engines": found}, open(out, "w"), indent=1)


def differences_lines(path):
    """The report's lines for a differences.json: per engine, the keys only it or only the
    reference gives, and the ten largest groups."""
    d = json.load(open(path))
    lines = []
    for e, r in d["engines"].items():
        groups = "; ".join(f"{g['component']} on {g['path']} ({g['severity']}): {g['only_here']:,} only here, "
                           f"{g['only_in_reference']:,} only in {d['reference']}" for g in r["by_path"][:10])
        more = f"; and {len(r['by_path']) - 10} more" if len(r["by_path"]) > 10 else ""
        lines.append(f"- {e} against {d['reference']}: {r['only_here']:,} keys only in {e}, "
                     f"{r['only_in_reference']:,} only in {d['reference']}. {groups}{more}.")
    return lines + [""] if lines else []


def run_inject(ds, engines):
    """Seeded violations in the dataset (inject.py), and each engine's recall and precision on
    them with the era-local profile: it validates the data before and after the mutations, and
    their result keys are compared with the expected ones. An engine that failed, timed out or
    was skipped on era-local in the suite's run of this dataset is skipped here too."""
    run_phase0.need_rdflib()
    os.environ.update(engine_env())
    data, shapes = prepare(ds)
    work = os.path.join(W, "shacl", ds, "injected")
    os.makedirs(work, exist_ok=True)
    manifest_file = os.path.join(work, "manifest.json")
    want = {"seed": INJECT_SEED, "rate": INJECT_RATE}
    if not os.path.exists(manifest_file) or any(json.load(open(manifest_file)).get(k) != v for k, v in want.items()):
        sh([sys.executable, os.path.join(HERE, "inject.py"), data, shapes[INJECT_PROFILE], work,
            "--seed", str(INJECT_SEED), "--rate", str(INJECT_RATE)])
    manifest = json.load(open(manifest_file))
    res = os.path.join(RESULTS, ds, "injected")
    os.makedirs(res, exist_ok=True)
    json.dump(dict(manifest, profile=INJECT_PROFILE), open(os.path.join(res, "manifest.json"), "w"), indent=1)
    for engine in engines:
        suite = os.path.join(RESULTS, ds, INJECT_PROFILE, f"{engine}.json")
        prior = json.load(open(suite)) if os.path.exists(suite) else {}
        if "skipped" in prior or "error" in prior or prior.get("timed_out"):
            rec = {"engine": engine, "skipped": f"no {INJECT_PROFILE} result on {ds}"}
        else:
            print(f"=== shacl {ds} injected on {engine}", flush=True)
            keys = {x: os.path.join(work, f"{engine}.{x}.keys") for x in ("before", "after")}
            before = run_one(engine, data, shapes[INJECT_PROFILE], work, keys["before"], once=True)
            after = run_one(engine, os.path.join(work, "mutated.nt"), shapes[INJECT_PROFILE], work,
                            keys["after"], once=True)
            rec = {"engine": engine, "version": before.get("version")}
            failed = [r for r in (before, after) if "results" not in r]
            if failed:
                rec["error"] = failed[0].get("error", "no report")
            else:
                rec.update(inject.score(work, keys["before"], keys["after"]))
                rec["wall_s"] = {"before": before["wall_s"], "after": after["wall_s"]}
            # The keys hold RINF values: not kept once scored.
            for k in keys.values():
                if os.path.exists(k):
                    os.remove(k)
        json.dump(rec, open(os.path.join(res, f"{engine}.json"), "w"), indent=1)
        print(json.dumps(rec), flush=True)
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
                    for p in sorted(glob.glob(os.path.join(ds_dir, profile, "*.json")))
                    if not p.endswith("differences.json")}
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
            diff = os.path.join(ds_dir, profile, "differences.json")
            if os.path.exists(diff):
                out += differences_lines(diff)
        inj = os.path.join(ds_dir, "injected", "manifest.json")
        if os.path.exists(inj):
            m = json.load(open(inj))
            kinds = ", ".join(f"{k} {n:,}" for k, n in m["by_kind"].items())
            out += ["### injected violations", "",
                    f"{m['mutated']:,} violations injected (seed {m['seed']}, {m['rate']:.0%} of "
                    f"{m['focus_nodes']:,} focus nodes drawn: {kinds}; `suites/shacl/inject.py`), "
                    f"validated with the {m.get('profile', INJECT_PROFILE)} profile before and after. "
                    "Recall is the share of injected violations reported; precision the share of new "
                    f"results on one of the {m['touched_nodes']:,} nodes the mutations touched (the "
                    "mutated nodes, the objects of removed triples and up to three hops upstream).", "",
                    "| engine | recall | precision | found | new results | missed (by component) |",
                    "|---|---:|---:|---:|---:|---|"]
            for e in ENGINES:
                f = os.path.join(ds_dir, "injected", f"{e}.json")
                if not os.path.exists(f):
                    continue
                r = json.load(open(f))
                if "skipped" in r or "error" in r:
                    out.append(f"| {e} | {r.get('skipped') or r.get('error')} | | | | |")
                    continue
                missed = ", ".join(f"{c} {n:,}" for c, n in r["missed_by_component"].items()) or "none"
                out.append(f"| {e} | {r['recall']:.1%} | {'' if r['precision'] is None else format(r['precision'], '.1%')} | "
                           f"{r['found']:,} of {r['expected']:,} | {r['new_results']:,} | {missed} |")
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
    i = sub.add_parser("inject")
    i.add_argument("--dataset", required=True)
    i.add_argument("--engine", action="append")
    sub.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "setup":
        setup()
    elif a.cmd == "run":
        run(a.dataset, a.engine or ENGINES)
    elif a.cmd == "inject":
        run_inject(a.dataset, a.engine or ENGINES)
    else:
        report()


if __name__ == "__main__":
    main()
