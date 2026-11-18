#!/usr/bin/env python3
"""Run manifests of bench.sh: which benchmarks ran together, at which commit, on which machine.

  runs.py start  <manifest> --run R --request "all full" --engines E --machine M
  runs.py job    <manifest> --suite S --dataset D --engines E --status ok|failed|skipped
                 [--reason TEXT] --seconds N [--log FILE]
  runs.py finish <manifest>
  runs.py index  <results/runs>     results/runs/README.md: one row per run, newest first

A manifest (results/runs/<run>.json) holds the commit, the machine (env.py) and one record per
job in the order they ran, so results written by different suites can be tied to one run.
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, m):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(m, f, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def capture_env():
    return json.loads(subprocess.run([sys.executable, os.path.join(HERE, "env.py")],
                                     capture_output=True, text=True, check=False).stdout or "{}")


def cmd_start(a):
    env = capture_env()
    m = {"run": a.run, "request": a.request, "engines": a.engines, "machine": a.machine,
         "commit": env.get("tripletrail_commit", ""), "started": now(), "finished": None,
         "env": env, "jobs": []}
    if os.environ.get("GITHUB_RUN_ID"):
        m["workflow_run"] = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                             f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    save(a.manifest, m)


def cmd_job(a):
    m = load(a.manifest)
    rec = {"suite": a.suite, "dataset": a.dataset, "engines": a.engines.split(), "status": a.status,
           "seconds": a.seconds, "finished": now()}
    if a.reason:
        rec["reason"] = a.reason
    if a.log:
        rec["log"] = a.log
    m["jobs"].append(rec)
    save(a.manifest, m)


def cmd_finish(a):
    m = load(a.manifest)
    m["finished"] = now()
    # Again at the end: on a fresh server the engine images are only pulled by the jobs, so the
    # start has no image versions to record.
    env = capture_env()
    if env:
        m["env"] = env
    save(a.manifest, m)


def hours(s):
    return f"{s / 3600:.1f} h" if s >= 3600 else f"{s / 60:.0f} min"


def cmd_index(a):
    folder = a.folder
    runs = [load(p) for p in glob.glob(os.path.join(folder, "*.json"))]
    runs.sort(key=lambda m: m.get("started") or "", reverse=True)
    out = ["# Benchmark runs", "",
           "Written by `bench/v2/runs.py index`. One row per run of `bench/v2/bench.sh` (the",
           "workflow `Benchmarks`); each run's manifest is `<run>.json` here. Commit is the",
           "TripleTrail commit the run measured. The result",
           "folders (`../small`, `../bsbm`, ...) hold the latest run of each job; git history has",
           "the older ones.", "",
           "| Run | Started | Commit | Machine | Request | Jobs ok / failed / skipped | Time |",
           "|---|---|---|---|---|---|---|"]
    for m in runs:
        js = m.get("jobs", [])
        c = {s: sum(1 for j in js if j["status"] == s) for s in ("ok", "failed", "skipped")}
        bad = [f"{j['suite']} {j['dataset']}" for j in js if j["status"] != "ok"]
        run = m["run"]
        link = f"[{run}]({m['workflow_run']})" if m.get("workflow_run") else run
        out.append(f"| {link} | {(m.get('started') or '')[:16]} | `{(m.get('commit') or '')[:8]}` | "
                   f"{m.get('machine', '')} | {m.get('request', '')} | {c['ok']} / {c['failed']} / {c['skipped']}"
                   f"{' (' + ', '.join(bad) + ')' if bad else ''} | {hours(sum(j['seconds'] for j in js))} |")
    with open(os.path.join(folder, "README.md"), "w") as f:
        f.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("manifest")
    for k in ("--run", "--request", "--engines", "--machine"):
        s.add_argument(k, required=True)
    j = sub.add_parser("job")
    j.add_argument("manifest")
    for k in ("--suite", "--dataset", "--status"):
        j.add_argument(k, required=True)
    j.add_argument("--engines", default="")
    j.add_argument("--reason")
    j.add_argument("--log")
    j.add_argument("--seconds", type=int, required=True)
    f = sub.add_parser("finish")
    f.add_argument("manifest")
    i = sub.add_parser("index")
    i.add_argument("folder")
    a = ap.parse_args()
    {"start": cmd_start, "job": cmd_job, "finish": cmd_finish, "index": cmd_index}[a.cmd](a)


if __name__ == "__main__":
    main()
