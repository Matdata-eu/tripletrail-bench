#!/usr/bin/env python3
"""Export a RINF-shaped N-Triples dataset into PostGIS/pgRouting tables.

Reads the N-Triples directly (no RDF engine involved, so the PostGIS side is an independent
reference for correctness checks) and builds:

  ne(iri, length, track, geom)               era:LinearElement with geometry
  track(iri, gauge, electrified, speed)      era:Track attributes
  signal(iri, signal_type, ne, offset_m, line, km, geom)
  op(iri, name, op_type, line, km, geom)     era:OperationalPoint
  line(iri, label, geom)                     era:NationalRailwayLine
  region(iri, label, geom)                   bench:Region polygons
  vertex(id, iri)                            routing vertices "<element>#fwd|#bwd"
  micro_edges(id, iri, source, target, cost, reverse_cost, ne, gauge, electrified)

micro_edges is the edge set of profiles/era-micro.rq, computed here in Python with the same
rules: a navigable era:NetRelation (navigability AB/Both for A->B, BA/Both for B->A) is an edge
from "<from element>#bwd|#fwd" to "<to element>#fwd|#bwd" costing the length of the element
entered. reverse_cost is -1 (the graph is directed). Vertex and edge ids are dense integers in
sorted IRI order. gauge/electrified are those of the track of the element entered.

Usage: export_postgis.py --dsn "host=/var/run/postgresql dbname=rinf user=postgres" data.nt...
Prints timings of each step as JSON on the last line.
"""
import argparse
import io
import json
import re
import sys
import time

import psycopg2

ERA = "http://data.europa.eu/949/"
GSP = "http://www.opengis.net/ont/geosparql#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
BENCH = "http://example.org/bench/"
NAV = ERA + "concepts/navigabilities/"

LINE = re.compile(r'^<([^>]*)> <([^>]*)> (.*) \.\s*$')
LIT = re.compile(r'^"((?:[^"\\]|\\.)*)"(?:\^\^<([^>]*)>|@[A-Za-z-]+)?$')

WANTED = {
    RDF_TYPE, RDFS_LABEL, GSP + "hasGeometry", GSP + "asWKT",
    ERA + "lengthOfNetLinearElement", ERA + "isPartOf", ERA + "elementA", ERA + "elementB",
    ERA + "isOnOriginOfElementA", ERA + "isOnOriginOfElementB", ERA + "navigability",
    ERA + "wheelSetGauge", ERA + "contactLineSystem", ERA + "maximumPermittedSpeed",
    ERA + "signalType", ERA + "netReference", ERA + "hasTopoCoordinate", ERA + "onLinearElement",
    ERA + "offsetFromOrigin", ERA + "lineReference", ERA + "kilometer", ERA + "lineNationalId",
    ERA + "opName", ERA + "opType",
}
TYPES = {ERA + "LinearElement", ERA + "NetRelation", ERA + "Track", ERA + "Signal",
         ERA + "OperationalPoint", ERA + "NationalRailwayLine", BENCH + "Region"}


def obj(o):
    if o.startswith("<"):
        return o[1:-1]
    m = LIT.match(o)
    if not m:
        return o
    return m.group(1).encode().decode("unicode_escape") if "\\" in m.group(1) else m.group(1)


def read(files):
    props = {}  # (s, p) -> o (single valued here)
    types = {t: [] for t in TYPES}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                m = LINE.match(line)
                if not m:
                    continue
                s, p, o = m.groups()
                if p not in WANTED:
                    continue
                o = obj(o)
                if p == RDF_TYPE:
                    if o in types:
                        types[o].append(s)
                    continue
                props[(s, p)] = o
    return props, types


def tsv(rows):
    buf = io.StringIO()
    for r in rows:
        buf.write("\t".join("\\N" if v is None else str(v).replace("\t", " ") for v in r) + "\n")
    buf.seek(0)
    return buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="host=/var/run/postgresql dbname=rinf user=postgres")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    timing = {}
    t0 = time.perf_counter()
    props, types = read(a.files)
    timing["parse_s"] = time.perf_counter() - t0
    g = props.get

    def wkt(s):
        geom = g((s, GSP + "hasGeometry"))
        return g((geom, GSP + "asWKT")) if geom else None

    def strip_crs(w):
        # CRS84 / no CRS prefix only (the synthetic data and RINF use plain WKT)
        if w and w.startswith("<"):
            w = w[w.index(">") + 1:].strip()
        return w

    t0 = time.perf_counter()
    ne_rows = [(s, g((s, ERA + "lengthOfNetLinearElement")), g((s, ERA + "isPartOf")),
                strip_crs(wkt(s))) for s in types[ERA + "LinearElement"]]
    tr_rows = []
    for s in types[ERA + "Track"]:
        gauge = g((s, ERA + "wheelSetGauge"))
        cls = g((s, ERA + "contactLineSystem"))
        tr_rows.append((s, gauge.rsplit("/", 1)[-1] if gauge else None,
                        None if cls is None else ("f" if cls.endswith("NotElectrified") else "t"),
                        g((s, ERA + "maximumPermittedSpeed"))))

    def lref(s):
        lr = g((s, ERA + "lineReference"))
        return (g((lr, ERA + "lineNationalId")), g((lr, ERA + "kilometer"))) if lr else (None, None)

    sig_rows = []
    for s in types[ERA + "Signal"]:
        ref = g((s, ERA + "netReference"))
        tc = g((ref, ERA + "hasTopoCoordinate")) if ref else None
        st = g((s, ERA + "signalType"))
        sig_rows.append((s, st.rsplit("/", 1)[-1] if st else None,
                         g((tc, ERA + "onLinearElement")) if tc else None,
                         g((tc, ERA + "offsetFromOrigin")) if tc else None,
                         *lref(s), strip_crs(wkt(s))))
    op_rows = []
    for s in types[ERA + "OperationalPoint"]:
        ot = g((s, ERA + "opType"))
        op_rows.append((s, g((s, ERA + "opName")), ot.rsplit("/", 1)[-1] if ot else None,
                        *lref(s), strip_crs(wkt(s))))
    line_rows = [(s, g((s, RDFS_LABEL)), strip_crs(wkt(s))) for s in types[ERA + "NationalRailwayLine"]]
    reg_rows = [(s, g((s, RDFS_LABEL)), strip_crs(wkt(s))) for s in types[BENCH + "Region"]]

    # era-micro edge set
    length = {s: float(l) for s, l, _, _ in ne_rows if l is not None}
    track_of = {s: t for s, _, t, _ in ne_rows}
    tr_attr = {s: (gg, el) for s, gg, el, _ in tr_rows}
    edges = []
    for r in types[ERA + "NetRelation"]:
        ea, eb = g((r, ERA + "elementA")), g((r, ERA + "elementB"))
        oa, ob = g((r, ERA + "isOnOriginOfElementA")), g((r, ERA + "isOnOriginOfElementB"))
        nav = g((r, ERA + "navigability"))
        if None in (ea, eb, oa, ob, nav):
            continue
        oa, ob = oa == "true", ob == "true"
        if nav in (NAV + "AB", NAV + "Both") and eb in length:
            edges.append((r + "#ab", ea + ("#bwd" if oa else "#fwd"), eb + ("#fwd" if ob else "#bwd"),
                          length[eb], eb))
        if nav in (NAV + "BA", NAV + "Both") and ea in length:
            edges.append((r + "#ba", eb + ("#bwd" if ob else "#fwd"), ea + ("#fwd" if oa else "#bwd"),
                          length[ea], ea))
    vertices = sorted({e[1] for e in edges} | {e[2] for e in edges})
    vid = {v: i + 1 for i, v in enumerate(vertices)}
    edges.sort()
    edge_rows = []
    for i, (iri, s, t, c, ne) in enumerate(edges):
        gauge, el = tr_attr.get(track_of.get(ne), (None, None))
        edge_rows.append((i + 1, iri, vid[s], vid[t], c, -1, ne, gauge, el))
    timing["build_s"] = time.perf_counter() - t0

    conn = psycopg2.connect(a.dsn)
    conn.autocommit = True
    cur = conn.cursor()
    t0 = time.perf_counter()
    cur.execute("""
      DROP TABLE IF EXISTS ne, track, signal, op, line, region, vertex, micro_edges CASCADE;
      CREATE TABLE ne (iri text, length double precision, track text, wkt text);
      CREATE TABLE track (iri text, gauge int, electrified boolean, speed int);
      CREATE TABLE signal (iri text, signal_type text, ne text, offset_m double precision,
                           line text, km double precision, wkt text);
      CREATE TABLE op (iri text, name text, op_type text, line text, km double precision, wkt text);
      CREATE TABLE line (iri text, label text, wkt text);
      CREATE TABLE region (iri text, label text, wkt text);
      CREATE TABLE vertex (id bigint, iri text);
      CREATE TABLE micro_edges (id bigint, iri text, source bigint, target bigint,
        cost double precision, reverse_cost double precision, ne text, gauge int, electrified boolean);
    """)
    for table, rows in (("ne", ne_rows), ("track", tr_rows), ("signal", sig_rows), ("op", op_rows),
                        ("line", line_rows), ("region", reg_rows),
                        ("vertex", [(i, v) for v, i in vid.items()]), ("micro_edges", edge_rows)):
        cur.copy_expert(f"COPY {table} FROM STDIN", tsv(rows))
    timing["copy_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    for table in ("ne", "signal", "op", "line", "region"):
        cur.execute(f"""
          ALTER TABLE {table} ADD COLUMN geom geometry(Geometry, 4326);
          UPDATE {table} SET geom = ST_GeomFromText(wkt, 4326);
          ALTER TABLE {table} DROP COLUMN wkt;
          ALTER TABLE {table} ADD PRIMARY KEY (iri);
        """)
    timing["geometry_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    cur.execute("""
      CREATE INDEX ON ne USING gist (geom);
      CREATE INDEX ON ne USING gist ((geom::geography));
      CREATE INDEX ON signal USING gist (geom);
      CREATE INDEX ON signal USING gist ((geom::geography));
      CREATE INDEX ON op USING gist (geom);
      CREATE INDEX ON op USING gist ((geom::geography));
      CREATE INDEX ON line USING gist (geom);
      CREATE INDEX ON region USING gist (geom);
      CREATE INDEX ON signal (line, km);
      CREATE INDEX ON signal (ne);
      CREATE INDEX ON ne (track);
      ALTER TABLE track ADD PRIMARY KEY (iri);
      ALTER TABLE vertex ADD PRIMARY KEY (id);
      CREATE UNIQUE INDEX ON vertex (iri);
      ALTER TABLE micro_edges ADD PRIMARY KEY (id);
      CREATE INDEX ON micro_edges (source);
      CREATE INDEX ON micro_edges (target);
      CREATE INDEX ON micro_edges (ne);
    """)
    cur.execute("VACUUM ANALYZE")
    timing["index_s"] = time.perf_counter() - t0
    cur.execute("SELECT pg_database_size(current_database())")
    timing["db_bytes"] = cur.fetchone()[0]
    timing["rows"] = {"ne": len(ne_rows), "track": len(tr_rows), "signal": len(sig_rows),
                      "op": len(op_rows), "line": len(line_rows), "region": len(reg_rows),
                      "vertex": len(vid), "micro_edges": len(edge_rows)}
    print(json.dumps(timing))


if __name__ == "__main__":
    sys.exit(main())
