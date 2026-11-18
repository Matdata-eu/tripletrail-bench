#!/usr/bin/env python3
"""N-Triples for the scale benchmark (#218) from `osmium export -f geojsonseq` on stdin.

The shape is that of data/osm_extract.py (osm_norway), so the v2 OSM queries run on it
unchanged, with two classes more to reach a billion triples from one OSM extract:
  set a: admin     boundary=administrative areas, admin_level 2-7     -> bench:OsmAdmin
         station   railway=station|halt or public_transport=station    -> bench:OsmStation
         track     ways with railway=rail                               -> bench:OsmTrack
         landuse   areas with landuse=*                                 -> bench:OsmLanduse
  set b: building  areas with building=*                                -> bench:OsmBuilding
         highway   ways with highway=*                                  -> bench:OsmHighway
Each feature gets rdf:type, geo:hasGeometry, its geometry's rdf:type and geo:asWKT, rdfs:label
(name) and its class's tag value (bench:adminLevel, bench:landuse, bench:building,
bench:highway). A feature of set b with a set a tag is left out (set a has it).

Streaming, in parallel chunks: nothing is kept per feature, so it runs on all of Europe. With
--max-triples it stops there (at a whole chunk) and exits 0; the caller ignores osmium's broken
pipe then.

  osmium export -f geojsonseq --add-unique-id=type_id -o - a.osm.pbf | osm_scale.py --set a >> x.nt
Counts go to --meta (JSON, merged into an existing file) and stderr.
"""
import argparse
import collections
import json
import os
import sys
import time

GEO = "http://www.opengis.net/ont/geosparql#"
BENCH = "http://example.org/bench/"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
OSM = "https://www.openstreetmap.org/"
KIND = {"n": "node", "w": "way", "a": "way", "r": "relation"}
INTEGER = "http://www.w3.org/2001/XMLSchema#integer"
ADMIN_LEVELS = {"2", "3", "4", "5", "6", "7"}

# The osmium tags-filter expressions of each set.
FILTERS = {
    "a": ["w/railway=rail", "nwr/railway=station,halt", "nwr/public_transport=station",
          "wr/landuse", "r/boundary=administrative"],
    "b": ["wr/building", "w/highway"],
}


def pt(p):
    return f"{p[0]:.7f} {p[1]:.7f}"


def line(ps):
    return "(" + ", ".join(pt(p) for p in ps) + ")"


def poly(rings):
    return "(" + ", ".join(line(r) for r in rings) + ")"


def wkt(g):
    t, c = g["type"], g["coordinates"]
    if t == "Point":
        return f"POINT({pt(c)})"
    if t == "LineString":
        return "LINESTRING" + line(c)
    if t == "Polygon":
        return "POLYGON" + poly(c)
    if t == "MultiPolygon":
        return "MULTIPOLYGON(" + ", ".join(poly(p) for p in c) + ")"
    if t == "MultiLineString":
        return "MULTILINESTRING(" + ", ".join(line(x) for x in c) + ")"
    return None


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


AREAS = ("Polygon", "MultiPolygon")


def classify_a(p, gt):
    """The class of a set a feature and its tag value, or None."""
    if p.get("boundary") == "administrative" and gt in AREAS:
        level = p.get("admin_level")
        return ("admin", level) if level in ADMIN_LEVELS else None
    if p.get("railway") in ("station", "halt") or p.get("public_transport") == "station":
        return ("station", None) if gt in ("Point", *AREAS) else None
    if p.get("railway") == "rail" and gt in ("LineString", "MultiLineString"):
        return ("track", None)
    if p.get("landuse") and gt in AREAS:
        return ("landuse", p["landuse"])
    return None


def classify_b(p, gt):
    """The class of a set b feature and its tag value, or None (also when set a has it)."""
    if (p.get("landuse") or p.get("railway") in ("rail", "station", "halt")
            or p.get("public_transport") == "station" or p.get("boundary") == "administrative"):
        return None
    if p.get("building") and gt in AREAS:
        return ("building", p["building"])
    if p.get("highway") and gt in ("LineString", "MultiLineString"):
        return ("highway", p["highway"])
    return None


PROPERTY = {"admin": "adminLevel", "landuse": "landuse", "building": "building", "highway": "highway"}


def convert(job):
    """N-Triples of a chunk of geojsonseq lines: (text, triples, counts per class)."""
    which, chunk = job
    classify = classify_a if which == "a" else classify_b
    buf, n, counts = [], 0, {}
    for raw in chunk.split(b"\n"):
        raw = raw.lstrip(b"\x1e").strip()
        if not raw:
            continue
        f = json.loads(raw)
        g = f.get("geometry")
        if not g:
            continue
        p = f.get("properties") or {}
        c = classify(p, g["type"])
        if not c:
            continue
        w = wkt(g)
        if not w:
            continue
        name, value = c
        uid = f.get("id") or p.get("@id")
        iri = f"{OSM}{KIND[uid[0]]}/{uid[1:]}"
        geom = f"{iri}/geom/{name}"
        buf.append(f"<{iri}> <{RDF_TYPE}> <{BENCH}Osm{name.capitalize()}> .\n"
                   f"<{iri}> <{GEO}hasGeometry> <{geom}> .\n"
                   f"<{geom}> <{RDF_TYPE}> <{GEO}Geometry> .\n"
                   f'<{geom}> <{GEO}asWKT> "{w}"^^<{GEO}wktLiteral> .\n')
        n += 4
        if p.get("name"):
            buf.append(f'<{iri}> <{LABEL}> "{esc(p["name"])}" .\n')
            n += 1
        if name == "admin":
            buf.append(f'<{iri}> <{BENCH}adminLevel> "{value}"^^<{INTEGER}> .\n')
            n += 1
        elif name in PROPERTY:
            buf.append(f'<{iri}> <{BENCH}{PROPERTY[name]}> "{esc(value)}" .\n')
            n += 1
        counts[name] = counts.get(name, 0) + 1
    return "".join(buf), n, counts


def chunks(stream, which, size=8 << 20):
    """The input in pieces of about `size` bytes, cut after a newline."""
    rest = b""
    while True:
        block = stream.read(size)
        if not block:
            break
        block = rest + block
        cut = block.rfind(b"\n") + 1
        rest = block[cut:]
        if cut:
            yield which, block[:cut]
    if rest:
        yield which, rest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["a", "b"], required=True)
    ap.add_argument("--max-triples", type=int, default=0,
                    help="stop once this many are written (at a whole chunk; 0: no limit)")
    ap.add_argument("--meta", help="JSON file to merge the counts into")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--filters", action="store_true", help="print the set's tags-filter expressions")
    a = ap.parse_args()
    if a.filters:
        print(" ".join(FILTERS[a.set]))
        return
    import multiprocessing
    t0 = time.perf_counter()
    counts, n, capped = {}, 0, False
    out = sys.stdout
    jobs = max(1, a.jobs)
    # At most two chunks per worker in flight (Pool.imap would read all of stdin ahead).
    pending = collections.deque()
    with multiprocessing.Pool(jobs) as pool:
        source = chunks(sys.stdin.buffer, a.set)
        while True:
            while len(pending) < 2 * jobs:
                job = next(source, None)
                if job is None:
                    break
                pending.append(pool.apply_async(convert, (job,)))
            if not pending:
                break
            text, k, cs = pending.popleft().get()
            out.write(text)
            n += k
            for c, v in cs.items():
                counts[c] = counts.get(c, 0) + v
            if a.max_triples and n >= a.max_triples:
                capped = True
                break
        pool.terminate()
    out.flush()
    meta = {}
    if a.meta and os.path.exists(a.meta):
        with open(a.meta) as fh:
            meta = json.load(fh)
    meta.setdefault("sets", {})[a.set] = {
        "triples": n, "counts": counts, "capped": capped,
        "seconds": round(time.perf_counter() - t0, 1)}
    meta["triples"] = sum(s["triples"] for s in meta["sets"].values())
    if a.meta:
        with open(a.meta, "w") as fh:
            json.dump(meta, fh, indent=1)
    print(f"set {a.set}: {n} triples, {counts}{' (capped)' if capped else ''}", file=sys.stderr)


if __name__ == "__main__":
    main()
