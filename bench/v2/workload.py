"""Benchmark v2 workload: the queries of each family, their parameters and result checks.

Each query has a template per engine in queries/<engine>/<qid>.rq (SPARQL) or .sql (PostGIS);
an engine without a template for a query is N/A for it (the reason is in NA below).
Placeholders {{name}} are filled from the parameter dict. Parameters are drawn from a RNG seeded
by (qid, index), so every engine gets the same parameters for the same run index.
"""
import math
import random

PFX = """PREFIX era: <http://data.europa.eu/949/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX bench: <http://example.org/bench/>
"""


def _rng(qid, i):
    return random.Random(f"{qid}/{i}")


def _point(r, meta, inset=0.05):
    x0, y0, x1, y1 = meta["bbox"]
    return r.uniform(x0 + inset, x1 - inset), r.uniform(y0 + inset, y1 - inset)


def p_bbox(qid, i, meta):
    r = _rng(qid, i)
    x, y = _point(r, meta, 0.15)
    w, h = 0.2, 0.1
    x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
    return dict(minx=f"{x0:.6f}", miny=f"{y0:.6f}", maxx=f"{x1:.6f}", maxy=f"{y1:.6f}",
                bbox_wkt=f"POLYGON(({x0:.6f} {y0:.6f}, {x1:.6f} {y0:.6f}, {x1:.6f} {y1:.6f}, "
                         f"{x0:.6f} {y1:.6f}, {x0:.6f} {y0:.6f}))")


def p_polygon(qid, i, meta):
    r = _rng(qid, i)
    x, y = _point(r, meta, 0.15)
    pts = []
    for k in range(7):
        a = 2 * math.pi * k / 7
        f = r.uniform(0.6, 1.0)
        pts.append((x + 0.1 * f * math.cos(a), y + 0.05 * f * math.sin(a)))
    pts.append(pts[0])
    return dict(poly_wkt="POLYGON((" + ", ".join(f"{a:.6f} {b:.6f}" for a, b in pts) + "))")


def p_point(qid, i, meta, radius=2000):
    r = _rng(qid, i)
    x, y = _point(r, meta)
    return dict(lon=f"{x:.6f}", lat=f"{y:.6f}", pt_wkt=f"POINT({x:.6f} {y:.6f})",
                radius_m=str(radius), radius_km=f"{radius / 1000:.3f}")


def p_lr_point(qid, i, meta):
    r = _rng(qid, i)
    line = r.choice(meta["lines"])
    return dict(line=line["iri"], km=f"{r.uniform(0, line['km']):.3f}")


def p_lr_range(qid, i, meta):
    r = _rng(qid, i)
    line = r.choice(meta["lines"])
    a = r.uniform(0, max(line["km"] - 10, 0.1))
    return dict(line=line["iri"], km_a=f"{a:.3f}", km_b=f"{a + 10:.3f}")


def _vertex(r, meta):
    return f"{meta['base']}ne/{r.randrange(meta['counts']['ne'])}#{r.choice(('fwd', 'bwd'))}"


def p_pair(qid, i, meta):
    # bdDijkstra/CH reuse the Dijkstra pairs, so their results can be compared pair by pair.
    r = _rng("pair", i)
    return dict(src=_vertex(r, meta), dst=_vertex(r, meta))


def p_cpair(qid, i, meta):
    r = _rng("cpair", i)
    return dict(src=_vertex(r, meta), dst=_vertex(r, meta))


def p_start(qid, i, meta):
    r = _rng(qid, i)
    return dict(src=_vertex(r, meta), distance="50000")


def p_matrix(qid, i, meta):
    r = _rng(qid, i)
    vids = sorted({_vertex(r, meta) for _ in range(100)})
    return dict(sparql_vids=" ;\n       ".join([f'pgr:start_vid "{v}"' for v in vids] + [f'pgr:end_vid "{v}"' for v in vids]),
                sql_vids="ARRAY[" + ",".join(f"'{v}'" for v in vids) + "]::text[]")


def p_none(qid, i, meta):
    return {}


def p_mixed(qid, i, meta):
    d = p_pair(qid, i, meta)
    d["radius_m"] = "50"
    return d


# kind: how results are normalised and compared (see run.normalise / compare.py)
#   ids      set of the first column
#   ranked   first column in order (KNN; compared as a set, the order is reported)
#   groups   {first column: float second column}
#   scalars  floats of the first row
#   point    one WKT point (compared by distance)
#   path     route rows: edge column in order + total agg_cost
#   costs    sorted floats of the first column
Q = [
    # family, qid, params, warm runs, kind, timeout (s), tolerance
    ("1 selection", "sel_bbox", p_bbox, 30, "ids", 300, None),
    ("1 selection", "sel_polygon", p_polygon, 30, "ids", 300, None),
    ("1 selection", "sel_distance", p_point, 30, "ids", 300, None),
    ("2 knn", "knn_signals", p_point, 30, "ranked", 300, None),
    ("2 knn", "knn_ops", p_point, 30, "ranked", 300, None),
    ("3 join", "join_signal_ne_20m", p_none, 5, "scalars", 300, 0),
    ("3 join", "join_op_region", p_none, 5, "groups", 600, 0),
    ("4 aggregate", "agg_length_region", p_none, 5, "groups", 600, 1e-3),
    ("4 aggregate", "agg_total_length", p_none, 5, "scalars", 600, 1e-3),
    ("4 aggregate", "agg_union_buffers", p_bbox, 20, "scalars", 600, 2e-2),
    ("5 linear referencing", "lr_km_to_point", p_lr_point, 30, "point", 300, 1.0),
    ("5 linear referencing", "lr_assets_between_km", p_lr_range, 30, "ids", 300, None),
    ("6 routing", "route_dijkstra", p_pair, 1000, "path", 300, 1e-6),
    ("6 routing", "route_dijkstra_cost", p_pair, 1000, "scalars", 300, 1e-6),
    ("6 routing", "route_bddijkstra", p_pair, 1000, "path", 300, 1e-6),
    ("6 routing", "route_ch", p_pair, 1000, "path", 300, 1e-6),
    ("6 routing", "route_constrained", p_cpair, 200, "path", 300, 1e-6),
    ("6 routing", "driving_distance_50km", p_start, 50, "scalars", 300, 1e-6),
    ("6 routing", "ksp5", p_pair, 50, "costs", 300, 1e-6),
    ("6 routing", "cost_matrix_100", p_matrix, 10, "scalars", 600, 1e-6),
    ("6 routing", "components", p_none, 5, "scalars", 600, 0),
    ("7 mixed", "mixed_route_signals", p_mixed, 50, "ids", 300, None),
    # OSM Norway (dataset osm_norway, from data/osm_extract.py)
    ("8 osm", "osm_station_admin", p_none, 3, "groups", 600, 0),
    ("8 osm", "osm_track_landuse", p_none, 3, "scalars", 600, 0),
    ("8 osm", "osm_track_track_5m", p_none, 3, "scalars", 600, 0),
    # Scale (#218: osm_benelux, osm_europe, osm_planet from data/osm_scale.py): scans, groups and point
    # lookups on a store larger than its memory limit
    ("9 scale", "scale_class_counts", p_none, 3, "groups", 600, 0),
    ("9 scale", "scale_building_kinds", p_none, 3, "groups", 600, 0),
    ("9 scale", "scale_label_lookup", p_none, 20, "ids", 120, None),
    ("9 scale", "scale_named_stations", p_none, 3, "scalars", 600, 0),
]

# The datasets of the scale suite (suites/scale): the OSM queries and the scale family.
SCALE_DATASETS = ("osm_benelux", "osm_europe", "osm_planet")

QUERIES = {q[1]: dict(family=q[0], qid=q[1], params=q[2], warm=q[3], kind=q[4], timeout=q[5], tol=q[6],
                     data={"8 osm": "osm", "9 scale": "scale"}.get(q[0], "rinf"))
           for q in Q}


def for_dataset(dataset):
    """The queries that apply to a dataset: OSM queries on osm_* datasets (and the scale family on
    those of the scale suite), the others elsewhere."""
    kind = "osm" if dataset.startswith("osm") else "rinf"
    kinds = {kind, "scale"} if dataset in SCALE_DATASETS else {kind}
    return [q for q in QUERIES.values() if q["data"] in kinds]

NA = {
    "graphdb": {
        "agg_*": "geof:metricLength / metricArea / aggUnion (GeoSPARQL 1.1) are unknown to GraphDB 10.8 "
                 "(HTTP 500 'Unknown function')",
        "lr_km_to_point": "no linear-referencing functions",
        "route_*": "no routing", "driving_distance_50km": "no routing", "ksp5": "no routing",
        "cost_matrix_100": "no routing", "components": "no routing", "mixed_*": "no routing",
    },
}
NA["jena"] = dict(NA["graphdb"])
NA["jena"]["agg_*"] = ("geof:metricLength / metricArea / aggUnion are not implemented by jena-geosparql 6.2 "
                       "(they return no value; geof:intersection works)")
NA["qlever"] = dict(NA["graphdb"])
del NA["qlever"]["agg_*"]
NA["qlever"]["agg_length_region"] = "geof:intersection is not supported by QLever (HTTP 400 'not supported')"
NA["qlever"]["agg_union_buffers"] = "geof:buffer and geof:aggUnion are not supported by QLever"
NA["postgis"] = {"route_ch": "pgRouting has no contraction-hierarchy query (pgr_contraction only contracts)"}


def fill(template, params):
    out = template
    for k, v in params.items():
        out = out.replace("{{" + k + "}}", v)
    if "{{" in out:
        raise ValueError("unfilled placeholder in " + out[out.index("{{"):][:40])
    return out
