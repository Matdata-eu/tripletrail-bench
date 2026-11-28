#!/usr/bin/env python3
"""Builds the GitHub Pages site of the benchmark dashboard into OUT (default _site):

    python3 site/build.py [RESULTS] [OUT] [--history] [--core GIT_DIR]

RESULTS defaults to bench/v2/results. The page (index.html, app.js, style.css), the dashboard's
CSV files and summary.json under data/, and data/runs.json: one row per run manifest in
RESULTS/runs. Standard library only.

--history (run from the repository's root, with its full history and tags) also writes one
snapshot per earlier commit of the current branch that changed RESULTS/dashboard, under
data/v/<commit>/, and data/versions.json, which the page's version picker reads: newest first,
each with its date, the TripleTrail commit of its newest run, and the results tags
(results-*) of this repository that point at it. --core names a clone of the TripleTrail
repository (a bare, blob-less clone will do) to label each commit with the release before it
(`v0.1.0+12`: twelve commits after v0.1.0).
"""

import glob
import hashlib
import json
import os
import shutil
import importlib.util
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def run_rows(manifests):
    runs = []
    for m in manifests:
        jobs = m.get("jobs", [])
        count = lambda st: sum(1 for j in jobs if j.get("status") == st)
        runs.append({"run": m.get("run"), "url": m.get("workflow_run", ""), "started": m.get("started"),
                     "request": m.get("request"), "commit": m.get("commit", ""), "machine": m.get("machine"),
                     "jobs": f"{count('ok')} / {count('failed')} / {count('skipped')}"})
    runs.sort(key=lambda r: r.get("started") or "", reverse=True)
    return runs


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=1)


def git(*args, git_dir=None):
    cmd = ["git"] + (["--git-dir", git_dir] if git_dir else []) + list(args)
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None


def core_version(core, commit):
    """The release before a TripleTrail commit: v0.1.0, v0.1.0+12, or None when unknown."""
    if not core or not commit or git("cat-file", "-e", f"{commit}^{{commit}}", git_dir=core) is None:
        return None
    d = git("describe", "--tags", "--match", "v*", "--long", commit, git_dir=core)
    if not d:
        return "before v0.1.0"
    tag, n, _ = d.rsplit("-", 2)
    return tag if n == "0" else f"{tag}+{n}"


def provenance_rows(results, commit, manifests_dir_files):
    """provenance.csv of a snapshot, rewritten by today's bench/v2/dashboard.py from that
    commit's run manifests and env files, so every snapshot names its runs the same way."""
    spec = importlib.util.spec_from_file_location("dashboard", os.path.join(HERE, "..", "bench", "v2", "dashboard.py"))
    dashboard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dashboard)
    with tempfile.TemporaryDirectory() as tmp:
        for n in manifests_dir_files:
            rel = os.path.relpath(n, results)
            os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(tmp, rel), "wb") as f:
                f.write(subprocess.run(["git", "show", f"{commit}:{n}"], capture_output=True, check=True).stdout)
        return dashboard.provenance(tmp)


def newest_commit(manifests):
    ms = [m for m in manifests if m.get("commit")]
    return max(ms, key=lambda m: m.get("started") or "")["commit"] if ms else ""


def history(results, data, core, latest_runs):
    """Snapshots of RESULTS/dashboard at each earlier commit; returns the versions.json rows."""
    dash = f"{results.rstrip('/')}/dashboard"
    log = git("log", "--first-parent", "--format=%H %cI", "--", dash) or ""
    commits = [line.split(" ", 1) for line in log.splitlines() if line]
    tags = {}
    for t in (git("tag", "--list", "results-*") or "").split():
        c = git("log", "-1", "--first-parent", "--format=%H", t, "--", dash)
        if c:
            tags.setdefault(c, []).append(t)
    head = git("rev-parse", "HEAD")
    head_dash = git("log", "-1", "--format=%H", "--", dash)
    versions = []
    for i, (c, date) in enumerate(commits):
        latest = c == head_dash
        if latest:
            manifests = latest_runs
            path = "data/"
        else:
            out = os.path.join(data, "v", c[:7])
            os.makedirs(out, exist_ok=True)
            names = (git("ls-tree", "--name-only", c, f"{dash}/") or "").splitlines()
            for n in names:
                if n.endswith(".csv") or n.endswith("summary.json"):
                    blob = subprocess.run(["git", "show", f"{c}:{n}"], capture_output=True, check=True).stdout
                    with open(os.path.join(out, os.path.basename(n)), "wb") as f:
                        f.write(blob)
            manifests = []
            for n in (git("ls-tree", "--name-only", c, f"{results.rstrip('/')}/runs/") or "").splitlines():
                if n.endswith(".json"):
                    try:
                        manifests.append(json.loads(git("show", f"{c}:{n}") or ""))
                    except ValueError:
                        pass
            if not manifests:  # before the first run of the workflow: nothing to show
                shutil.rmtree(out)
                continue
            write_json(os.path.join(out, "runs.json"), run_rows(manifests))
            files = [n for n in (git("ls-tree", "-r", "--name-only", c, f"{results.rstrip('/')}/") or "").splitlines()
                     if n.endswith(".json") and (n.startswith(f"{results.rstrip('/')}/runs/") or os.path.basename(n).startswith("env"))]
            with open(os.path.join(out, "provenance.csv"), "w", encoding="utf-8") as f:
                f.write("suite,dataset,machine,cpus,commit,date,engines\n")
                for row in provenance_rows(results, c, files):
                    f.write(",".join(str(x) for x in row) + "\n")
            path = f"data/v/{c[:7]}/"
        tt = newest_commit(manifests)
        subject = git("log", "-1", "--format=%s", c) or ""
        versions.append({"id": "latest" if latest else c[:7], "path": path, "date": date[:10],
                         "bench_commit": c, "subject": subject, "tripletrail": tt,
                         "version": core_version(core, tt), "tags": sorted(tags.get(c, []))})
    if head and head_dash is None:
        versions.insert(0, {"id": "latest", "path": "data/", "date": "", "bench_commit": head, "subject": "",
                            "tripletrail": newest_commit(latest_runs), "version": None, "tags": []})
    return versions


def main():
    args = [a for a in sys.argv[1:]]
    with_history = "--history" in args
    core = None
    if "--core" in args:
        i = args.index("--core")
        core = args[i + 1]
        del args[i:i + 2]
    args = [a for a in args if a != "--history"]
    results = args[0] if len(args) > 0 else "bench/v2/results"
    out = args[1] if len(args) > 1 else "_site"
    data = os.path.join(out, "data")
    os.makedirs(data, exist_ok=True)

    # The page, with its script and style sheet named by content so a deploy is never hidden
    # behind a cached copy of the last one.
    page = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    for name in ("app.js", "style.css"):
        shutil.copy(os.path.join(HERE, name), out)
        digest = hashlib.sha256(open(os.path.join(HERE, name), "rb").read()).hexdigest()[:10]
        page = page.replace(f'"{name}"', f'"{name}?v={digest}"')
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    for path in glob.glob(os.path.join(results, "dashboard", "*.csv")) + \
            glob.glob(os.path.join(results, "dashboard", "summary.json")):
        shutil.copy(path, data)
    manifests = []
    for path in glob.glob(os.path.join(results, "runs", "*.json")):
        with open(path, encoding="utf-8") as f:
            manifests.append(json.load(f))
    runs = run_rows(manifests)
    write_json(os.path.join(data, "runs.json"), runs)

    if with_history:
        versions = history(results, data, core, manifests)
        write_json(os.path.join(data, "versions.json"), versions)
        print(f"site: {out} ({len(runs)} runs, {len(versions)} versions)")
    else:
        print(f"site: {out} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
