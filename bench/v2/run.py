#!/usr/bin/env python3
"""Benchmark v2 runner.

  run.py load  --engine E --dataset D            load the dataset (engines/E.sh load D), record
                                                 load time / size / memory -> results/D/E/load.json
  run.py query --engine E --dataset D [--only q1,family,...] [--warm-scale 0.2] [--no-restart]
                                                 run the workload -> results/D/E/<qid>.json
  run.py check --engine E --dataset D --only qid [--index 0]
                                                 print one query, its rows and its time

Engines: tripletrail, postgis, graphdb, jena, qlever, oxigraph (see engines/*.sh; oxigraph has no
GeoSPARQL and serves the general suites in suites/). The engine is restarted
before every query family, so the first ("cold") run of each family's first query sees empty
engine caches (the OS page cache stays warm: dropping it needs root on the host). Then 2
untimed warm-up runs and N timed warm runs, each with its own parameters (run index i draws the
same parameters on every engine). Times are wall-clock at the client, including the protocol
(HTTP + SPARQL JSON results for the RDF engines, libpq for PostGIS) and fetching all rows.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from workload import NA, PFX, QUERIES, fill, for_dataset  # noqa: E402

WORK = os.environ.get("BENCH_WORK", os.path.join(HERE, "work"))
SPARQL_ENGINES = {"tripletrail", "oxigraph", "graphdb", "jena", "qlever"}


def sh(engine, *args, capture=True, stderr=False):
    """Runs an engine script; its output is returned when `capture`. With `stderr`, its
    standard error goes to ours as it comes (a long load's progress lines) instead."""
    cmd = [os.path.join(HERE, "engines", f"{engine}.sh"), *args]
    r = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=None if stderr or not capture else subprocess.PIPE, text=True)
    if r.returncode != 0:
        err = r.stderr[-2000:] if r.stderr else "(its error output is above)"
        raise RuntimeError(f"{' '.join(cmd)} failed: {err}")
    return r.stdout.strip() if capture else ""


class Sparql:
    def __init__(self, engine, endpoint):
        self.engine, self.endpoint = engine, endpoint
        self.s = requests.Session()
        # A new connection per request, like curl: on a kept-alive connection QLever's answers
        # wait ~40 ms for a delayed ACK (Nagle), which hid every QLever time under that floor.
        self.s.headers["Connection"] = "close"
        # And the pool is emptied after each answer (`self.s.close()`): a server that closes the
        # connection as asked but doesn't say so in its answer (tiny_http, so TripleTrail) would
        # otherwise see the next request sent on the closed connection, which fails as "Remote
        # end closed connection without response" now and then (#496).

    def before_run(self):
        if self.engine == "qlever":  # no result cache: every run computes its answer
            self.s.get(self.endpoint, params={"cmd": "clear-cache", "access-token": "benchtoken"}, timeout=60)

    def query(self, text, timeout):
        data = {"query": text}
        if self.engine == "qlever":  # a timeout above the server default needs the access token
            data["timeout"] = f"{timeout}s"
            data["access-token"] = "benchtoken"
        else:
            data["timeout"] = str(timeout)
        t = time.perf_counter()
        r = self.s.post(self.endpoint, data=data, timeout=timeout + 60,
                        headers={"Accept": "application/sparql-results+json"})
        body = r.content
        dt = time.perf_counter() - t
        self.s.close()
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {body[:600].decode(errors='replace')}")
        j = json.loads(body)
        if "boolean" in j:
            return dt, [[str(j["boolean"]).lower()]]
        vars_ = j["head"]["vars"]
        rows = [[b.get(v, {}).get("value") for v in vars_] for b in j["results"]["bindings"]]
        return dt, rows

    def update(self, text, timeout=3600):
        ep = self.endpoint
        data = {"update": text}
        if self.engine in ("tripletrail", "oxigraph", "jena", "maplib"):
            ep = ep.replace("/query", "/update")
        elif self.engine == "graphdb":
            ep = ep + "/statements"
        elif self.engine == "qlever":  # updates need the access token
            data["access-token"] = "benchtoken"
        t = time.perf_counter()
        r = self.s.post(ep, data=data, timeout=timeout)
        self.s.close()
        if r.status_code not in (200, 204):
            raise RuntimeError(f"update HTTP {r.status_code}: {r.text[:600]}")
        return time.perf_counter() - t


class Postgis:
    def __init__(self, dsn):
        import psycopg2
        self.dsn = dsn
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True

    def before_run(self):
        pass

    def query(self, text, timeout):
        cur = self.conn.cursor()
        cur.execute(f"SET statement_timeout = {int(timeout * 1000)}")
        t = time.perf_counter()
        try:
            cur.execute(text)
            rows = cur.fetchall()
        except Exception:
            self.conn.rollback() if not self.conn.autocommit else None
            raise
        dt = time.perf_counter() - t
        return dt, [[None if v is None else str(v) for v in row] for row in rows]

    def update(self, text, timeout=3600):
        return 0.0


def client(engine, dataset):
    if engine == "postgis":
        return Postgis(sh("postgis", "endpoint", dataset))
    return Sparql(engine, sh(engine, "endpoint"))


NUM = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?")


def fnum(x):
    return float(NUM.search(x).group(0)) if x is not None and NUM.search(x) else None


def digest(items):
    return hashlib.sha1("\n".join(items).encode()).hexdigest()[:16]


def normalise(kind, rows):
    if kind == "ids":
        ids = sorted({r[0] for r in rows if r[0] is not None})
        return {"n": len(ids), "digest": digest(ids), **({"ids": ids} if len(ids) <= 3000 else {})}
    if kind == "ranked":
        ids = [r[0] for r in rows]
        return {"n": len(ids), "ids": ids}
    if kind == "groups":
        return {"groups": {r[0]: fnum(r[1]) for r in rows}}
    if kind == "scalars":
        return {"values": [fnum(v) for v in rows[0]] if rows else []}
    if kind == "point":
        if not rows or rows[0][0] is None:
            return {"point": None}
        wkt = rows[0][0]
        m = re.search(r"POINT\s*Z?\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)", wkt)
        return {"point": [float(m.group(1)), float(m.group(2))] if m else None, "raw": wkt[:200]}
    if kind == "path":
        edges = [r[1] for r in rows if r[1] not in (None, "-1", "")]
        aggs = [fnum(r[2]) for r in rows if r[2] is not None]
        return {"n": len(edges), "total": max(aggs) if aggs else None, "digest": digest(edges),
                "first": edges[:2], "last": edges[-2:]}
    if kind == "costs":
        return {"costs": sorted(fnum(r[1]) for r in rows)}
    raise ValueError(kind)


def selected(only, dataset):
    if not only:
        return for_dataset(dataset)
    keys = [k.strip() for k in only.split(",") if k.strip()]
    out = []
    for q in for_dataset(dataset):
        if any(fnmatch.fnmatch(q["qid"], k) or q["family"].startswith(k) for k in keys):
            out.append(q)
    return out


def na_reason(engine, qid):
    for pat, why in NA.get(engine, {}).items():
        if fnmatch.fnmatch(qid, pat):
            return why
    return None


def template(engine, qid):
    ext = "sql" if engine == "postgis" else "rq"
    p = os.path.join(HERE, "queries", engine, f"{qid}.{ext}")
    if not os.path.exists(p):
        return None
    text = open(p).read()
    return text if engine == "postgis" else PFX + text


def summary(times):
    if not times:
        return {}
    s = sorted(times)
    pct = lambda p: s[min(len(s) - 1, max(0, int(round(p / 100 * len(s) + 0.5)) - 1))]
    return {"n": len(s), "p50_ms": round(statistics.median(s) * 1000, 3), "p95_ms": round(pct(95) * 1000, 3),
            "min_ms": round(s[0] * 1000, 3), "max_ms": round(s[-1] * 1000, 3),
            "mean_ms": round(statistics.mean(s) * 1000, 3)}


def run_query(engine, cl, q, meta, warm_scale, budget_s):
    qid = q["qid"]
    rec = {"engine": engine, "qid": qid, "family": q["family"], "kind": q["kind"], "runs": []}
    why = na_reason(engine, qid)
    tpl = template(engine, qid)
    if why or tpl is None:
        rec["status"] = "n/a"
        rec["reason"] = why or "no template for this engine (unsupported, see docs)"
        return rec
    warm = max(1, int(round(q["warm"] * warm_scale)))
    plan = [("cold", 0)] + [("warmup", 1), ("warmup", 2)] + [("warm", 3 + i) for i in range(warm)]
    started = time.perf_counter()
    for phase, idx in plan:
        params = q["params"](qid, idx, meta)
        text = fill(tpl, params)
        run = {"phase": phase, "index": idx}
        try:
            cl.before_run()
            dt, rows = cl.query(text, q["timeout"])
            run.update(ms=round(dt * 1000, 3), ok=True, rows=len(rows), result=normalise(q["kind"], rows))
        except requests.exceptions.Timeout:
            run.update(ok=False, error="client timeout")
        except Exception as e:  # noqa: BLE001 - recorded, not hidden
            msg = str(e)
            run.update(ok=False, error=("timeout: " if "timeout" in msg.lower() or "cancel" in msg.lower() else "") + msg[:800])
        rec["runs"].append(run)
        if not run["ok"] and phase == "cold":
            rec["status"] = "failed"
            rec["reason"] = run["error"][:300]
            return rec
        if time.perf_counter() - started > budget_s and phase == "warm":
            rec["truncated"] = f"stopped after {budget_s} s budget"
            break
    ok_warm = [r["ms"] / 1000 for r in rec["runs"] if r["phase"] == "warm" and r["ok"]]
    errs = [r for r in rec["runs"] if not r["ok"]]
    rec["status"] = "ok" if not errs else f"ok with {len(errs)} failed runs"
    rec["cold_ms"] = rec["runs"][0]["ms"]
    rec["warm"] = summary(ok_warm)
    return rec


def cmd_query(a):
    meta = json.load(open(os.path.join(WORK, "data", f"{a.dataset}.meta.json")))
    outdir = os.path.join(a.out, a.dataset, a.engine)
    os.makedirs(outdir, exist_ok=True)
    qs = selected(a.only, a.dataset)
    families = []
    for q in qs:
        if q["family"] not in families:
            families.append(q["family"])
    for fam in families:
        fq = [q for q in qs if q["family"] == fam]
        runnable = [q for q in fq if not na_reason(a.engine, q["qid"]) and template(a.engine, q["qid"])]
        setup = None
        if runnable:
            if not a.no_restart:
                t = time.perf_counter()
                sh(a.engine, "start", a.dataset)
                print(f"[{a.engine}] restarted for family {fam} in {time.perf_counter() - t:.1f} s", flush=True)
            cl = client(a.engine, a.dataset)
            key = fam.split()[1] if " " in fam else fam
            sp = os.path.join(HERE, "queries", a.engine, f"setup_{key}.ru")
            if os.path.exists(sp):
                setup = round(cl.update(open(sp).read()) * 1000, 3)
                print(f"[{a.engine}] setup {key}: {setup} ms", flush=True)
        for q in fq:
            rec = run_query(a.engine, cl if runnable else None, q, meta, a.warm_scale, a.budget) \
                if q in runnable else run_query(a.engine, None, q, meta, a.warm_scale, a.budget)
            rec["dataset"] = a.dataset
            if setup is not None:
                rec["family_setup_ms"] = setup
            if q in runnable:
                try:
                    rec["rss_after"] = sh(a.engine, "rss")
                except Exception as e:  # noqa: BLE001
                    rec["rss_after"] = f"n/a ({e})"
            with open(os.path.join(outdir, f"{q['qid']}.json"), "w") as f:
                json.dump(rec, f, indent=1)
            w = rec.get("warm", {})
            print(f"[{a.engine}] {q['qid']:24s} {rec['status']:10s} cold {rec.get('cold_ms', '-')} ms  "
                  f"p50 {w.get('p50_ms', '-')} p95 {w.get('p95_ms', '-')} (n={w.get('n', 0)})"
                  f"{'  ' + rec.get('reason', '') if rec['status'] != 'ok' else ''}", flush=True)


def cmd_load(a):
    outdir = os.path.join(a.out, a.dataset, a.engine)
    os.makedirs(outdir, exist_ok=True)
    t = time.perf_counter()
    out = sh(a.engine, "load", a.dataset, stderr=True)
    rec = json.loads(out.splitlines()[-1])
    rec["wall_s"] = round(time.perf_counter() - t, 3)
    rec["rss_after_start"] = sh(a.engine, "rss")
    if a.engine in SPARQL_ENGINES:
        cl = client(a.engine, a.dataset)
        quads = os.path.exists(os.path.join(WORK, "data", f"{a.dataset}.nq"))
        pattern = "GRAPH ?g { ?s ?p ?o }" if quads else "?s ?p ?o"
        _, rows = cl.query(PFX + f"SELECT (COUNT(*) AS ?n) WHERE {{ {pattern} }}", 3600)
        rec["triples"] = int(fnum(rows[0][0]))
    with open(os.path.join(outdir, "load.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec))


def cmd_check(a):
    meta = json.load(open(os.path.join(WORK, "data", f"{a.dataset}.meta.json")))
    q = QUERIES[a.only]
    text = fill(template(a.engine, a.only), q["params"](a.only, a.index, meta))
    cl = client(a.engine, a.dataset)
    print(text)
    dt, rows = cl.query(text, q["timeout"])
    for r in rows[:20]:
        print(r)
    print(f"{len(rows)} rows in {dt * 1000:.1f} ms")
    print(json.dumps(normalise(q["kind"], rows))[:1500])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["load", "query", "check"])
    ap.add_argument("--engine", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--only")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--warm-scale", type=float, default=1.0)
    ap.add_argument("--budget", type=float, default=900, help="max seconds of warm runs per query")
    ap.add_argument("--no-restart", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    a = ap.parse_args()
    {"load": cmd_load, "query": cmd_query, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
