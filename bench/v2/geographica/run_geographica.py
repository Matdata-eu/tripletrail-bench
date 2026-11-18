#!/usr/bin/env python3
"""Geographica 2 micro and macro workloads on the SPARQL engines of benchmark v2.

  prepare: run_geographica.py prepare <geographica2 dir>
           unpacks the real-world datasets the micro/macro queries use (corine/clc, dbpedia, gag,
           geonames, hotspots, linkedgeodata/lgd) into one N-Quads file, each dataset in the named
           graph the queries expect (http://geographica.di.uoa.gr/dataset/<name>), as
           $BENCH_WORK/data/geographica.nq
  run:     run_geographica.py run --engine E [--only wl:n,...] <geographica2 dir>
           (the engine must be loaded with dataset "geographica": engines/E.sh load geographica)
           Queries already in the results file are skipped (resume); --only re-runs the listed
           queries (e.g. micro_joins:18) and replaces their records.

Queries are taken verbatim from queries/*.lst, with these edits: the map-search queries hold the
placeholder "null" where the Geographica harness inserts a box, and we insert the fixed box of
the compute-statistics scenario (central Athens); Area_CLC's per-system placeholder ext:area
becomes GeoSPARQL 1.1 geof:metricArea; the aggregations' Strabon functions strdf:extent and
one-argument geof:union become geof:aggBoundingBox and geof:aggUnion; and prefixes some lists
use without declaring (geo, xsd, lgdo, gag) are declared. The data's CRS IRI is dropped (see
prepare). Like the paper, each query runs cold (first run
after the engine restart) and then warm (2 more runs here; the paper used 3); a query that takes
longer than the timeout is recorded as such and not repeated. A request that fails only when
the time limit is reached (an HTTP timeout status, or a result stream the server cut off at the
limit, which shows up as truncated JSON or a broken gzip body) counts as a timeout. Census (macro geocoding, 23.2 M
triples) and the synthetic / scalability workloads are not run.
Results: results/geographica/<engine>.json (time, row count per run).
"""
import glob
import json
import os
import re
import subprocess
import sys
import tarfile
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
WORK = os.environ.get("BENCH_WORK", os.path.join(V2, "work"))
GRAPH = "http://geographica.di.uoa.gr/dataset/"
# tarball -> graph name used in the queries
DATASETS = {"corine": "clc", "dbpedia": "dbpedia", "gag": "gag", "geonames": "geonames",
            "hotspots": "hotspots", "linkedgeodata": "lgd"}
WORKLOADS = ["micro_nontopological", "micro_selections", "micro_joins", "micro_aggregations",
             "macro_reversegeocoding", "macro_mapsearch", "macro_rapidmapping", "macro_computestatistics"]
BOX = ("POLYGON ((23.5669247401051 37.9893271592633, 23.5669247401051 38.0366287295546, "
       "23.6743333558464 38.0366287295546, 23.6743333558464 37.9893271592633, "
       "23.5669247401051 37.9893271592633))")
CRS_PREFIX = '"<http://www.opengis.net/def/crs/EPSG/4326> '
EXTRA_PREFIXES = {"geo": "http://www.opengis.net/ont/geosparql#",
                  "geof": "http://www.opengis.net/def/function/geosparql/",
                  "xsd": "http://www.w3.org/2001/XMLSchema#",
                  "lgdo": "http://linkedgeodata.org/ontology/",
                  "gag": "http://geo.linkedopendata.gr/gag/ontology/"}
TIMEOUT = int(os.environ.get("GEOGRAPHICA_TIMEOUT", "300"))


def parse(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^(?:QUERY|Query) (\d+) - (\S+?):\s*$", text, flags=re.M)
    out = []
    for i in range(1, len(parts), 3):
        q = parts[i + 2].strip()
        q = q.replace('"null"^^<http://www.opengis.net/ont/geosparql#wktLiteral>',
                      f'"{BOX}"^^<http://www.opengis.net/ont/geosparql#wktLiteral>')
        # Area_CLC calls the harness's per-system placeholder ext:area: use GeoSPARQL 1.1's
        # geof:metricArea (square metres)
        q = q.replace("ext:area(", "geof:metricArea(")
        # the aggregation queries use Strabon's strdf:extent and a one-argument geof:union
        # (an aggregate in Strabon): use GeoSPARQL 1.1's aggregates
        q = q.replace("strdf:extent(", "geof:aggBoundingBox(")
        q = re.sub(r"geof:union\((\?\w+)\)", r"geof:aggUnion(\1)", q)
        # some lists use prefixes they do not declare (the Geographica harness adds them)
        declared = set(re.findall(r"PREFIX\s+(\w*):", q, re.I))
        body = re.sub(r"<[^>]*>|\"[^\"]*\"", "", q)
        missing = [p for p in EXTRA_PREFIXES if p not in declared and re.search(rf"\b{p}:", body)]
        q = "".join(f"PREFIX {p}: <{EXTRA_PREFIXES[p]}>\n" for p in missing) + q
        out.append((int(parts[i]), parts[i + 1], q))
    return out


def prepare(g2):
    os.makedirs(os.path.join(WORK, "data"), exist_ok=True)
    out = os.path.join(WORK, "data", "geographica.nq")
    tmp = os.path.join(WORK, "geographica-tmp")
    os.makedirs(tmp, exist_ok=True)
    n = 0
    line_re = re.compile(r"^(.*\S)\s*\.\s*$")
    with open(out, "w", encoding="utf-8") as o:
        for tb, g in DATASETS.items():
            with tarfile.open(os.path.join(g2, "datasets", tb + ".tar.xz")) as t:
                for m in t.getmembers():
                    if not m.isfile() or not m.name.endswith((".nt", ".n3", ".ttl")):
                        continue
                    if not m.name.endswith(".nt"):
                        raise SystemExit(f"{m.name}: only N-Triples is handled")
                    f = t.extractfile(m)
                    for raw in f:
                        line = raw.decode("utf-8", "replace").strip()
                        if not line or line.startswith("#"):
                            continue
                        mm = line_re.match(line)
                        if not mm:
                            continue
                        # Every WKT literal of these datasets starts with the non-standard CRS IRI
                        # <http://www.opengis.net/def/crs/EPSG/4326> (no "/0/") but holds lon/lat
                        # coordinates, and the query constants have no CRS. Engines differ on that IRI
                        # (an unknown CRS, or EPSG:4326's lat/lon axis order), so drop it: the
                        # geometries become CRS84, which is what the coordinates are.
                        triple = mm.group(1).replace(CRS_PREFIX, '"')
                        o.write(f"{triple} <{GRAPH}{g}> .\n")
                        n += 1
    os.rmdir(tmp)
    print(json.dumps({"quads": n, "file": out}))


def is_timeout(run_rec):
    """A failed run is a timeout when it reached the time limit: some servers answer 503, others
    have already started streaming a 200 response and cut it off (truncated JSON / gzip body)."""
    if run_rec["ok"]:
        return False
    if run_rec.get("timeout"):
        return True
    err = run_rec["error"].lower()
    return (run_rec["ms"] >= TIMEOUT * 1000 or "timeout" in err or "too long" in err
            or "cancel" in err or "timed out" in err)


def run(engine, g2, only=None):
    ep = subprocess.run([os.path.join(V2, "engines", f"{engine}.sh"), "endpoint"], capture_output=True,
                        text=True, check=True).stdout.strip()
    s = requests.Session()
    out = os.path.join(V2, "results", "geographica", f"{engine}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # resume: queries already in the results file are not run again
    res = json.load(open(out)) if os.path.exists(out) else {"engine": engine, "timeout_s": TIMEOUT, "queries": []}
    if only:
        res["queries"] = [x for x in res["queries"] if (x["workload"], x["n"]) not in only]
    done = {(x["workload"], x["n"]) for x in res["queries"]}
    for wl in WORKLOADS:
        for qn, name, q in parse(os.path.join(g2, "queries", wl + ".lst")):
            if (wl, qn) in done or (only and (wl, qn) not in only):
                continue
            rec = {"workload": wl, "n": qn, "name": name, "runs": []}
            for i in range(3):
                data = {"query": q}
                if engine == "qlever":
                    s.get(ep, params={"cmd": "clear-cache", "access-token": "benchtoken"})
                    data.update({"timeout": f"{TIMEOUT}s", "access-token": "benchtoken"})
                else:
                    data["timeout"] = str(TIMEOUT)
                t = time.perf_counter()
                try:
                    r = s.post(ep, data=data, timeout=TIMEOUT + 60,
                               headers={"Accept": "application/sparql-results+json"})
                    body = r.content
                    dt = time.perf_counter() - t
                    if r.status_code != 200:
                        rec["runs"].append({"ok": False, "ms": round(dt * 1000, 1),
                                            "error": f"HTTP {r.status_code}: {body[:300].decode(errors='replace')}"})
                        break
                    # each RDF term object becomes 1, so a 900 k-row result stays small in memory
                    js = json.loads(body, object_hook=lambda d: 1 if "type" in d and "value" in d else d)
                    del body
                    r = None  # drop the response (it holds the body too)
                    bindings = js["results"]["bindings"]
                    hv = js.get("head", {}).get("vars", [])
                    # rows with an unbound projected variable (e.g. a function the engine lacks)
                    partial = sum(1 for b in bindings if any(v not in b for v in hv))
                    rec["runs"].append({"ok": True, "ms": round(dt * 1000, 1), "rows": len(bindings),
                                        "rows_with_unbound": partial})
                except Exception as e:  # noqa: BLE001
                    err = str(e)[:300]
                    if isinstance(e, requests.exceptions.ContentDecodingError):
                        # GraphDB 10.8 sends its plain-text "503 Query interrupted" answer with a
                        # "Content-Encoding: gzip" header, so the client cannot decode it
                        err = "error body not decodable (plain text sent as gzip): " + err
                    rec["runs"].append({"ok": False, "ms": round((time.perf_counter() - t) * 1000, 1),
                                        "error": err})
                    break
                finally:
                    if not rec["runs"][-1]["ok"] and is_timeout(rec["runs"][-1]):
                        rec["runs"][-1]["timeout"] = True
                if dt > TIMEOUT / 3:
                    break  # long query: one run only
            res["queries"].append(rec)
            res["queries"].sort(key=lambda x: (WORKLOADS.index(x["workload"]), x["n"]))
            r0 = rec["runs"][0]
            print(f"[{engine}] {wl:24s} {qn:2d} {name:45s} "
                  + (f"cold {r0['ms']:9.1f} ms rows {r0['rows']}" if r0["ok"] else f"FAILED {r0['error'][:90]}")
                  + (f" warm {min(x['ms'] for x in rec['runs'][1:]):.1f} ms" if len(rec["runs"]) > 1 and rec["runs"][1]["ok"] else ""),
                  flush=True)
            with open(out, "w") as f:
                json.dump(res, f, indent=1)


NAMES = {"tripletrail": "tripletrail", "graphdb": "GraphDB", "jena": "Jena GeoSPARQL", "qlever": "QLever"}


def fmt_ms(v):
    if v >= 10000:
        return f"{v / 1000:.0f} s"
    if v >= 1000:
        return f"{v / 1000:.2f} s"
    return f"{v:.0f}" if v >= 10 else f"{v:.1f}"


def status(q):
    """answered | partial (some projected values unbound) | timeout | error"""
    r = q["runs"][0]
    if not r["ok"]:
        return "timeout" if is_timeout(r) else "error"
    return "partial" if r.get("rows_with_unbound") else "answered"


def best(q):
    r = q["runs"]
    warm = [x["ms"] for x in r[1:] if x["ok"]]
    return min(warm) if warm else r[0]["ms"]


def report():
    """Markdown report (also written to results/geographica/report.md): load, a per-engine
    summary and one row per query with cold / best warm time and row count. The fastest complete
    answer is in bold; a row count that differs from the most common one among the complete
    answers is marked with *."""
    folder = os.path.join(V2, "results", "geographica")
    res = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(folder, "*.json"))}
    engines = [e for e in ["tripletrail", "graphdb", "jena", "qlever"] if e in res]
    get = {e: {(x["workload"], x["n"]): x for x in res[e]["queries"]} for e in engines}
    keys = sorted({k for e in engines for k in get[e]}, key=lambda k: (WORKLOADS.index(k[0]), k[1]))
    out = []
    loads = {e: json.load(open(p)) for e in engines
             for p in [os.path.join(folder, "load", f"{e}.json")] if os.path.exists(p)}
    if loads:
        out += ["| Engine | Load (s) | Index / start (s) | On disk |", "|---|---|---|---|"]
        for e, ld in loads.items():
            idx = sum(v for k, v in ld.items() if k.endswith("_s") and k != "load_s")
            out.append(f"| {NAMES[e]} | {ld['load_s']:.1f} | {idx:.1f} | {ld['disk_bytes'] / 2**20:,.0f} MiB |")
        out.append("")
    out += ["| Engine | Answered | Answered, some values unbound | Timeout | Error | Fastest complete answer |",
            "|---|---|---|---|---|---|"]
    wins = {e: 0 for e in engines}
    for k in keys:
        done = [(best(get[e][k]), e) for e in engines if k in get[e] and status(get[e][k]) == "answered"]
        if done:
            wins[min(done)[1]] += 1
    for e in engines:
        st = [status(q) for q in get[e].values()]
        out.append(f"| {NAMES[e]} | {st.count('answered')} | {st.count('partial')} | {st.count('timeout')} | "
                   f"{st.count('error')} | {wins[e]} |")
    out += ["", f"{len(keys)} queries; timeout {TIMEOUT} s. Cold / best warm time in ms (`s` = seconds), "
            "row count in brackets.", "",
            "| Workload | Query | " + " | ".join(NAMES[e] for e in engines) + " |",
            "|---|---|" + "---|" * len(engines)]
    notes = []
    for k in keys:
        done = {e: get[e][k] for e in engines if k in get[e] and status(get[e][k]) == "answered"}
        counts = [q["runs"][0]["rows"] for q in done.values()]
        common = max(set(counts), key=counts.count) if counts else None
        fastest = min(done, key=lambda e: best(done[e])) if len(done) > 1 else None
        cells = []
        for e in engines:
            q = get[e].get(k)
            if not q:
                cells.append("-")
                continue
            stt = status(q)
            r = q["runs"]
            if stt == "timeout":
                cells.append("timeout")
                continue
            if stt == "error":
                err = " ".join(r[0]["error"].split())
                m = re.search(r'"exception": "((?:[^"\\]|\\.)*)', err)
                err = m.group(1).replace('\\"', '"') if m else err
                err = re.sub(r"\.? In file .*", "", err)
                notes.append(f"{NAMES[e]} {k[1]} {q['name']}: {err[:160]}")
                cells.append(f"error [{len(notes)}]")
                continue
            warm = [x["ms"] for x in r[1:] if x["ok"]]
            t = f"{fmt_ms(r[0]['ms'])} / {fmt_ms(min(warm))}" if warm else f"{fmt_ms(r[0]['ms'])} / -"
            if e == fastest:
                t = f"**{t}**"
            rows = f"{r[0]['rows']:,}"
            if stt == "partial":
                rows += f", {r[0]['rows_with_unbound']:,} unbound"
            elif len(set(counts)) > 1 and r[0]["rows"] != common:
                rows += " *"
            cells.append(f"{t} ({rows})")
        out.append(f"| {k[0].replace('_', ' ')} | {k[1]} {get_name(get, k)} | " + " | ".join(cells) + " |")
    if notes:
        out += ["", "Errors:", ""] + [f"{i}. {n}" for i, n in enumerate(notes, 1)]
    text = "\n".join(out) + "\n"
    with open(os.path.join(folder, "report.md"), "w") as f:
        f.write(text)
    print(text, end="")


def get_name(get, k):
    return next(g[k]["name"] for g in get.values() if k in g)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prepare":
        prepare(sys.argv[2])
    elif cmd == "run":
        args = sys.argv[2:]
        engine = args[args.index("--engine") + 1]
        only = None
        if "--only" in args:
            only = {(w, int(n)) for w, n in (x.split(":") for x in args[args.index("--only") + 1].split(","))}
        run(engine, args[-1], only)
    elif cmd == "report":
        report()
