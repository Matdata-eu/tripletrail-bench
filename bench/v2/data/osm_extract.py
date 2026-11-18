#!/usr/bin/env python3
"""Build the OSM Norway benchmark dataset from an OSM extract, for every engine.

From the .osm.pbf (e.g. norway-rail-landuse-admin.osm.pbf) it takes, with osmium:
  tracks    ways with railway=rail                                  -> bench:OsmTrack   (LINESTRING)
  stations  railway=station|halt or public_transport=station        -> bench:OsmStation (POINT/POLYGON)
  landuse   areas with landuse=*                                     -> bench:OsmLanduse (POLYGON)
  admin     boundary=administrative areas, admin_level 2-7          -> bench:OsmAdmin   (MULTIPOLYGON)
and writes
  <out>.nt          N-Triples, IRIs https://www.openstreetmap.org/{node,way,relation}/<id> as osm2rdf
                    does, geometry geo:hasGeometry/geo:asWKT (CRS84, 7 decimals), bench:adminLevel,
                    bench:landuse, rdfs:label (name)
  <out>.meta.json   counts and bounding box
and, with --dsn, PostGIS tables osm_track, osm_station, osm_landuse, osm_admin with the very same
geometries (from the same WKT), GiST indexes and ANALYZE. Areas are assembled by osmium
(multipolygon relations and closed ways), so all engines see identical geometries.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time

GEO = "http://www.opengis.net/ont/geosparql#"
BENCH = "http://example.org/bench/"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
OSM = "https://www.openstreetmap.org/"
KIND = {"n": "node", "w": "way", "a": "way", "r": "relation"}


def wkt(g):
    t, c = g["type"], g["coordinates"]
    pt = lambda p: f"{p[0]:.7f} {p[1]:.7f}"
    line = lambda l: "(" + ", ".join(pt(p) for p in l) + ")"
    poly = lambda rings: "(" + ", ".join(line(r) for r in rings) + ")"
    if t == "Point":
        return f"POINT({pt(c)})"
    if t == "LineString":
        return "LINESTRING" + line(c)
    if t == "Polygon":
        return "POLYGON" + poly(c)
    if t == "MultiPolygon":
        return "MULTIPOLYGON(" + ", ".join(poly(p) for p in c) + ")"
    if t == "MultiLineString":
        return "MULTILINESTRING(" + ", ".join(line(l) for l in c) + ")"
    return None


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


def export(pbf, expr, tmp, name, geometry_types):
    f = os.path.join(tmp, name + ".pbf")
    subprocess.run(["osmium", "tags-filter", "-O", "-o", f, pbf, *expr], check=True)
    out = os.path.join(tmp, name + ".geojsonseq")
    subprocess.run(["osmium", "export", "-O", "-f", "geojsonseq", "--add-unique-id=type_id",
                    "--geometry-types=" + geometry_types, "-o", out, f], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pbf")
    ap.add_argument("--out", required=True, help="output path without extension")
    ap.add_argument("--dsn")
    a = ap.parse_args()
    t0 = time.perf_counter()
    tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(a.out)))
    sets = [
        ("track", ["w/railway=rail"], "linestring"),
        ("station", ["nwr/railway=station,halt", "nwr/public_transport=station"], "point,polygon"),
        ("landuse", ["wr/landuse"], "polygon"),
        ("admin", ["r/boundary=administrative"], "polygon"),
    ]
    rows = {k: [] for k, _, _ in sets}
    seen = set()
    n = 0
    bbox = [180, 90, -180, -90]
    with open(a.out + ".nt", "w", buffering=1 << 20) as nt:
        for name, expr, gt in sets:
            path = export(a.pbf, expr, tmp, name, gt)
            cls = BENCH + "Osm" + name.capitalize()
            for line in open(path, encoding="utf-8"):
                line = line.lstrip("\x1e").strip()
                if not line:
                    continue
                f = json.loads(line)
                props = f.get("properties", {})
                if name == "admin":
                    if props.get("boundary") != "administrative" or props.get("admin_level") not in {"2", "3", "4", "5", "6", "7"}:
                        continue
                if name == "landuse" and not props.get("landuse"):
                    continue  # a member way of a landuse relation, exported for its own tags
                if name == "track" and props.get("railway") != "rail":
                    continue
                if name == "station" and not (props.get("railway") in ("station", "halt") or props.get("public_transport") == "station"):
                    continue
                uid = f.get("id") or props.get("@id")
                kind, oid = KIND[uid[0]], uid[1:]
                iri = f"{OSM}{kind}/{oid}"
                # one set per OSM object: a closed way tagged both railway=rail and landuse=* would
                # otherwise give one feature two geometries (a line and a polygon), and the RDF joins
                # would pair it through both (seen in the 2026-11-05 run: 3 such ways in Norway)
                key = iri
                w = wkt(f["geometry"]) if f.get("geometry") else None
                if not w or key in seen:
                    continue
                seen.add(key)
                for x, y in _coords(f["geometry"]):
                    bbox = [min(bbox[0], x), min(bbox[1], y), max(bbox[2], x), max(bbox[3], y)]
                g = f"{iri}/geom/{name}"
                nt.write(f"<{iri}> <{RDF_TYPE}> <{cls}> .\n")
                nt.write(f"<{iri}> <{GEO}hasGeometry> <{g}> .\n")
                nt.write(f"<{g}> <{RDF_TYPE}> <{GEO}Geometry> .\n")
                nt.write(f'<{g}> <{GEO}asWKT> "{w}"^^<{GEO}wktLiteral> .\n')
                n += 4
                if props.get("name"):
                    nt.write(f'<{iri}> <{LABEL}> "{esc(props["name"])}" .\n')
                    n += 1
                extra = None
                if name == "admin":
                    extra = props["admin_level"]
                    nt.write(f'<{iri}> <{BENCH}adminLevel> "{extra}"^^<http://www.w3.org/2001/XMLSchema#integer> .\n')
                    n += 1
                if name == "landuse":
                    extra = props.get("landuse", "")
                    nt.write(f'<{iri}> <{BENCH}landuse> "{esc(extra)}" .\n')
                    n += 1
                rows[name].append((iri, props.get("name"), extra, w))
    meta = {"source": os.path.basename(a.pbf), "triples": n, "bbox": bbox,
            "counts": {k: len(v) for k, v in rows.items()}, "extract_s": round(time.perf_counter() - t0, 1)}
    if a.dsn:
        import psycopg2
        conn = psycopg2.connect(a.dsn)
        conn.autocommit = True
        cur = conn.cursor()
        t1 = time.perf_counter()
        for name in rows:
            cur.execute(f"DROP TABLE IF EXISTS osm_{name}; CREATE TABLE osm_{name} (iri text, name text, attr text, wkt text)")
            buf = io.StringIO()
            for r in rows[name]:
                buf.write("\t".join("\\N" if v is None else str(v).replace("\\", "\\\\").replace("\t", " ").replace("\n", " ") for v in r) + "\n")
            buf.seek(0)
            cur.copy_expert(f"COPY osm_{name} FROM STDIN", buf)
            cur.execute(f"""ALTER TABLE osm_{name} ADD COLUMN geom geometry(Geometry, 4326);
                UPDATE osm_{name} SET geom = ST_GeomFromText(wkt, 4326); ALTER TABLE osm_{name} DROP COLUMN wkt;
                CREATE INDEX ON osm_{name} USING gist (geom); CREATE INDEX ON osm_{name} USING gist ((geom::geography));""")
        cur.execute("VACUUM ANALYZE")
        cur.execute("SELECT pg_database_size(current_database())")
        meta["postgis"] = {"load_s": round(time.perf_counter() - t1, 3), "db_bytes": cur.fetchone()[0]}
    with open(a.out + ".meta.json", "w") as f:
        json.dump(meta, f, indent=1)
    subprocess.run(["rm", "-rf", tmp])
    print(json.dumps(meta))


def _coords(g):
    c = g["coordinates"]
    t = g["type"]
    if t == "Point":
        yield c
    elif t == "LineString":
        yield from c
    elif t == "Polygon":
        for r in c:
            yield from r
    elif t in ("MultiPolygon",):
        for p in c:
            for r in p:
                yield from r
    elif t == "MultiLineString":
        for l in c:
            yield from l


if __name__ == "__main__":
    sys.exit(main())
