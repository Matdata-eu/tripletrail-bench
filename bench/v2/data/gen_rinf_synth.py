#!/usr/bin/env python3
"""Generate a synthetic, RINF-shaped railway dataset as N-Triples.

Used by benchmark v2 when the real RINF export is not available. Topology uses the RINF
micro-topology vocabulary exactly as published (era:LinearElement, era:NetRelation with
era:elementA/B, era:isOnOriginOfElementA/B, era:navigability), so profiles/era-micro.rq builds
the routing graph from it unchanged. Geometries are geo:hasGeometry/geo:asWKT in CRS84.

Layout: `h` east-west and `v` north-south double-ended lines crossing on a grid, `k` net
elements between crossings, and at every crossing four link elements (one per turn) with a
switch at each end, as in crates/tripletrail-bench/src/synthetic.rs. On top of the topology:

- era:Track per line section between crossings (era:wheelSetGauge, era:contactLineSystem,
  era:maximumPermittedSpeed); net elements point to their track with era:isPartOf
  (a modelling choice of this generator: published RINF links tracks and elements through
  era:netReference). Every `gauge_every`-th east-west line is 1520 mm, every
  `unelectrified_every`-th north-south line has no contact line.
- era:OperationalPoint at every crossing (junction) and every `station_every` elements along
  each line (station), with a POINT geometry and an era:lineReference (era:kilometer).
- era:Signal on every running element (not the links), at a pseudo-random offset, with a POINT
  geometry, era:signalType, a topological coordinate (era:netReference / era:hasTopoCoordinate
  / era:onLinearElement / era:offsetFromOrigin) and an era:lineReference.
- era:NationalRailwayLine per grid line with the line's whole geometry (for linear referencing:
  kilometre = geodesic distance from the line start / 1000).
- bench:Region: `regions` x `regions` polygons with jittered shared borders covering the network
  (admin-like units for spatial joins and aggregates).

Deterministic for given arguments (seeded RNG). Usage:
  gen_rinf_synth.py --h 24 --v 24 --k 20 --out small.nt
"""
import argparse
import json
import math
import random
import sys

ERA = "http://data.europa.eu/949/"
NAV = ERA + "concepts/navigabilities/"
GAUGE = ERA + "concepts/nominal-track-gauges/"
CLS = ERA + "concepts/contact-line-systems/"
SIGT = ERA + "concepts/signal-types/"
OPT = ERA + "concepts/op-types/rinf/"
GSP = "http://www.opengis.net/ont/geosparql#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
XSD = "http://www.w3.org/2001/XMLSchema#"
BENCH = "http://example.org/bench/"
BASE = "http://example.org/rinf-synth/"
R_EARTH = 6_371_008.8


def hav(a, b):
    lat1, lat2 = math.radians(a[1]), math.radians(b[1])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(
        math.radians(b[0] - a[0]) / 2
    ) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))


def plen(pts):
    return sum(hav(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def interp(pts, dist):
    """Point at geodesic distance `dist` along polyline `pts` (linear within a segment)."""
    for i in range(len(pts) - 1):
        d = hav(pts[i], pts[i + 1])
        if dist <= d or i == len(pts) - 2:
            f = 0 if d == 0 else min(max(dist / d, 0), 1)
            return (
                pts[i][0] + f * (pts[i + 1][0] - pts[i][0]),
                pts[i][1] + f * (pts[i + 1][1] - pts[i][1]),
            )
        dist -= d
    return pts[-1]


def wkt_line(pts):
    return "LINESTRING(" + ", ".join(f"{x:.7f} {y:.7f}" for x, y in pts) + ")"


def wkt_point(p):
    return f"POINT({p[0]:.7f} {p[1]:.7f})"


class W:
    def __init__(self, out):
        self.out = out
        self.n = 0

    def t(self, s, p, o):
        self.out.write(f"<{s}> <{p}> {o} .\n")
        self.n += 1

    @staticmethod
    def iri(x):
        return f"<{x}>"

    @staticmethod
    def lit(v, dt):
        return f'"{v}"^^<{dt}>'

    @staticmethod
    def s(v):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", type=int, default=24, help="east-west lines")
    ap.add_argument("--v", type=int, default=24, help="north-south lines")
    ap.add_argument("--k", type=int, default=20, help="elements between crossings")
    ap.add_argument("--station-every", type=int, default=6)
    ap.add_argument("--gauge-every", type=int, default=5)
    ap.add_argument("--unelectrified-every", type=int, default=4)
    ap.add_argument("--regions", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="-")
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    out = sys.stdout if a.out == "-" else open(a.out, "w", buffering=1 << 20)
    w = W(out)
    h, v, k = a.h, a.v, a.k
    lon0, lat0 = 5.0, 58.0
    dlon, dlat = 0.009, 0.0045  # ~470 m x 500 m at 58-64 N

    def jit():
        return rnd.uniform(-0.00012, 0.00012)

    counters = {"ne": 0, "nr": 0, "sig": 0, "op": 0, "track": 0}
    ne_pts = {}  # element id -> points

    def element(pts, track, label):
        i = counters["ne"]
        counters["ne"] += 1
        ne = f"{BASE}ne/{i}"
        g = ne + "/geom"
        ne_pts[i] = pts
        w.t(ne, RDF_TYPE, w.iri(ERA + "LinearElement"))
        w.t(ne, RDFS_LABEL, w.s(label))
        w.t(ne, ERA + "lengthOfNetLinearElement", w.lit(f"{plen(pts):.1f}", XSD + "double"))
        w.t(ne, ERA + "isPartOf", w.iri(track))
        w.t(ne, GSP + "hasGeometry", w.iri(g))
        w.t(g, RDF_TYPE, w.iri(GSP + "Geometry"))
        w.t(g, GSP + "asWKT", w.lit(wkt_line(pts), GSP + "wktLiteral"))
        return i

    def relation(ea, oa, eb, ob, nav):
        i = counters["nr"]
        counters["nr"] += 1
        nr = f"{BASE}nr/{i}"
        w.t(nr, RDF_TYPE, w.iri(ERA + "NetRelation"))
        w.t(nr, ERA + "elementA", w.iri(f"{BASE}ne/{ea}"))
        w.t(nr, ERA + "elementB", w.iri(f"{BASE}ne/{eb}"))
        w.t(nr, ERA + "isOnOriginOfElementA", w.lit("true" if oa else "false", XSD + "boolean"))
        w.t(nr, ERA + "isOnOriginOfElementB", w.lit("true" if ob else "false", XSD + "boolean"))
        w.t(nr, ERA + "navigability", w.iri(NAV + nav))

    def track(gauge, electrified, speed, label):
        i = counters["track"]
        counters["track"] += 1
        t = f"{BASE}track/{i}"
        w.t(t, RDF_TYPE, w.iri(ERA + "Track"))
        w.t(t, RDFS_LABEL, w.s(label))
        w.t(t, ERA + "wheelSetGauge", w.iri(GAUGE + str(gauge)))
        w.t(t, ERA + "contactLineSystem", w.iri(CLS + ("OCL" if electrified else "NotElectrified")))
        w.t(t, ERA + "maximumPermittedSpeed", w.lit(str(speed), XSD + "integer"))
        return t

    def line_ref(subj, line_iri, km):
        lr = subj + "/lr"
        w.t(subj, ERA + "lineReference", w.iri(lr))
        w.t(lr, RDF_TYPE, w.iri(ERA + "LineReference"))
        w.t(lr, ERA + "kilometer", w.lit(f"{km:.3f}", XSD + "double"))
        w.t(lr, ERA + "lineNationalId", w.iri(line_iri))

    def op(p, name, optype, line_iri, km):
        i = counters["op"]
        counters["op"] += 1
        o = f"{BASE}op/{i}"
        g = o + "/geom"
        w.t(o, RDF_TYPE, w.iri(ERA + "OperationalPoint"))
        w.t(o, ERA + "opName", w.s(name))
        w.t(o, ERA + "uopid", w.s(f"XX{i:06d}"))
        w.t(o, ERA + "opType", w.iri(OPT + optype))
        w.t(o, GSP + "hasGeometry", w.iri(g))
        w.t(g, RDF_TYPE, w.iri(GSP + "Geometry"))
        w.t(g, GSP + "asWKT", w.lit(wkt_point(p), GSP + "wktLiteral"))
        line_ref(o, line_iri, km)

    def signal(ne, pts, line_iri, km_at_start):
        i = counters["sig"]
        counters["sig"] += 1
        s = f"{BASE}sig/{i}"
        g = s + "/geom"
        length = plen(pts)
        off = length * rnd.uniform(0.1, 0.9)
        p = interp(pts, off)
        w.t(s, RDF_TYPE, w.iri(ERA + "Signal"))
        w.t(s, RDFS_LABEL, w.s(f"S{i}"))
        w.t(s, ERA + "signalType", w.iri(SIGT + ("main", "main", "distant", "shunting")[i % 4]))
        w.t(s, GSP + "hasGeometry", w.iri(g))
        w.t(g, RDF_TYPE, w.iri(GSP + "Geometry"))
        w.t(g, GSP + "asWKT", w.lit(wkt_point(p), GSP + "wktLiteral"))
        npr = s + "/ref"
        tc = s + "/topo"
        w.t(s, ERA + "netReference", w.iri(npr))
        w.t(npr, RDF_TYPE, w.iri(ERA + "NetPointReference"))
        w.t(npr, ERA + "hasTopoCoordinate", w.iri(tc))
        w.t(tc, RDF_TYPE, w.iri(ERA + "TopologicalCoordinate"))
        w.t(tc, ERA + "onLinearElement", w.iri(f"{BASE}ne/{ne}"))
        w.t(tc, ERA + "offsetFromOrigin", w.lit(f"{off:.1f}", XSD + "double"))
        line_ref(s, line_iri, km_at_start + off / 1000.0)

    def build_line(idx, kind, n, point_at, gauge, electrified):
        """A double-ended line of n elements; point_at(j) is the j-th boundary point."""
        line_iri = f"{BASE}line/{kind}{idx}"
        bounds = [point_at(j) for j in range(n + 1)]
        elems, all_pts = [], [bounds[0]]
        km = 0.0
        kms = [0.0]
        tr = None
        for j in range(n):
            if j % k == 0:
                tr = track(gauge, electrified, rnd.choice((80, 120, 160, 200)), f"{kind}{idx}/{j // k}")
            a_, b_ = bounds[j], bounds[j + 1]
            mid = [
                (a_[0] + (b_[0] - a_[0]) * f + jit(), a_[1] + (b_[1] - a_[1]) * f + jit())
                for f in (1 / 3, 2 / 3)
            ]
            pts = [a_] + mid + [b_]
            e = element(pts, tr, f"{kind}{idx}/{j}")
            signal(e, pts, line_iri, km)
            if j % a.station_every == a.station_every // 2 and (j + 1) % k != 0:
                op(b_, f"Station {kind}{idx}-{j}", "station", line_iri, km + plen(pts) / 1000.0)
            km += plen(pts) / 1000.0
            kms.append(km)
            elems.append(e)
            all_pts.extend(pts[1:])
        for x, y in zip(elems, elems[1:]):
            relation(x, False, y, True, "Both")
        lg = line_iri + "/geom"
        w.t(line_iri, RDF_TYPE, w.iri(ERA + "NationalRailwayLine"))
        w.t(line_iri, RDFS_LABEL, w.s(f"Line {kind}{idx}"))
        w.t(line_iri, GSP + "hasGeometry", w.iri(lg))
        w.t(lg, RDF_TYPE, w.iri(GSP + "Geometry"))
        w.t(lg, GSP + "asWKT", w.lit(wkt_line(all_pts), GSP + "wktLiteral"))
        return elems, line_iri, kms

    # Crossing (i, c) at lon0 + (c+1)k dlon, lat0 + (i+1)k dlat; lines run (n+1)k elements.
    def cross_lon(c):
        return lon0 + (c + 1) * k * dlon

    def cross_lat(i):
        return lat0 + (i + 1) * k * dlat

    horizontal, hlines, hkms = [], [], []
    for i in range(h):
        el, li, kms = build_line(
            i, "h", (v + 1) * k, lambda j, i=i: (lon0 + j * dlon, cross_lat(i)),
            1520 if i % a.gauge_every == a.gauge_every - 1 else 1435, True,
        )
        horizontal.append(el)
        hlines.append(li)
        hkms.append(kms)
    lines = [{"iri": li, "km": kms[-1]} for li, kms in zip(hlines, hkms)]
    vertical = []
    for c in range(v):
        el, li, kms = build_line(
            c, "v", (h + 1) * k, lambda j, c=c: (cross_lon(c), lat0 + j * dlat), 1435,
            c % a.unelectrified_every != a.unelectrified_every - 1,
        )
        vertical.append(el)
        lines.append({"iri": li, "km": kms[-1]})

    # Links: four per crossing, one per turn; small triangular loops into the quadrant.
    link_track = track(1435, True, 60, "junction links")
    for i in range(h):
        for c in range(v):
            xh, sh = horizontal[i][(c + 1) * k - 1], horizontal[i][(c + 1) * k]
            xv, sv = vertical[c][(i + 1) * k - 1], vertical[c][(i + 1) * k]
            p = (cross_lon(c), cross_lat(i))

            def tri(qx, qy):
                # a closed, simple triangle through the crossing (a retraced A-B-A line is valid
                # WKT but degenerate, and not every overlay implementation accepts it)
                return [p, (p[0] + qx * 0.3 * dlon, p[1] + qy * 0.1 * dlat),
                        (p[0] + qx * 0.1 * dlon, p[1] + qy * 0.3 * dlat), p]

            l1 = element(tri(1, 1), link_track, f"link {i}/{c}/en")  # east -> north
            relation(xh, False, l1, True, "Both")
            relation(l1, False, sv, True, "Both")
            relation(sh, True, l1, True, "None")
            l2 = element(tri(-1, 1), link_track, f"link {i}/{c}/ne")  # north -> east
            relation(xv, False, l2, True, "Both")
            relation(l2, False, sh, True, "Both")
            relation(sv, True, l2, True, "None")
            l3 = element(tri(1, -1), link_track, f"link {i}/{c}/es")  # east -> south
            relation(xh, False, l3, True, "Both")
            relation(l3, False, xv, False, "Both")
            relation(sh, True, l3, True, "None")
            l4 = element(tri(-1, -1), link_track, f"link {i}/{c}/wn")  # west -> north
            relation(sh, True, l4, True, "Both")
            relation(l4, False, sv, True, "Both")
            relation(xh, False, l4, True, "None")
            op(p, f"Junction {i}-{c}", "junction", hlines[i], hkms[i][(c + 1) * k])

    # Regions: a jittered r x r partition of the network's box (shared borders identical).
    r = a.regions
    x0, x1 = lon0 - 0.05, lon0 + (v + 1) * k * dlon + 0.05
    y0, y1 = lat0 - 0.05, lat0 + (h + 1) * k * dlat + 0.05
    nodes = {}
    for gi in range(r + 1):
        for gj in range(r + 1):
            x = x0 + (x1 - x0) * gi / r
            y = y0 + (y1 - y0) * gj / r
            if 0 < gi < r:
                x += rnd.uniform(-0.1, 0.1) * (x1 - x0) / r
            if 0 < gj < r:
                y += rnd.uniform(-0.1, 0.1) * (y1 - y0) / r
            nodes[(gi, gj)] = (x, y)
    edges = {}

    def border(a_, b_):
        if (b_, a_) in edges:
            return list(reversed(edges[(b_, a_)]))
        if (a_, b_) not in edges:
            pa, pb = nodes[a_], nodes[b_]
            on_frame = (a_[0] == b_[0] and a_[0] in (0, r)) or (a_[1] == b_[1] and a_[1] in (0, r))
            pts = [pa]
            for s in range(1, 8):
                f = s / 8
                q = [pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f]
                if not on_frame:
                    amp = 0.03 * max(abs(pb[0] - pa[0]), abs(pb[1] - pa[1]))
                    if a_[0] == b_[0]:
                        q[0] += rnd.uniform(-amp, amp)
                    else:
                        q[1] += rnd.uniform(-amp, amp)
                pts.append(tuple(q))
            pts.append(pb)
            edges[(a_, b_)] = pts
        return edges[(a_, b_)]

    for gi in range(r):
        for gj in range(r):
            ring = []
            corners = [(gi, gj), (gi + 1, gj), (gi + 1, gj + 1), (gi, gj + 1), (gi, gj)]
            for ca, cb in zip(corners, corners[1:]):
                ring.extend(border(ca, cb)[:-1])
            ring.append(ring[0])
            reg = f"{BENCH}region/{gi}_{gj}"
            g = reg + "/geom"
            w.t(reg, RDF_TYPE, w.iri(BENCH + "Region"))
            w.t(reg, RDFS_LABEL, w.s(f"Region {gi}-{gj}"))
            w.t(reg, GSP + "hasGeometry", w.iri(g))
            w.t(g, RDF_TYPE, w.iri(GSP + "Geometry"))
            wkt = "POLYGON((" + ", ".join(f"{x:.7f} {y:.7f}" for x, y in ring) + "))"
            w.t(g, GSP + "asWKT", w.lit(wkt, GSP + "wktLiteral"))

    if out is not sys.stdout:
        out.close()
        meta = {
            "generator": "gen_rinf_synth.py", "args": vars(a), "triples": w.n,
            "base": BASE, "counts": dict(counters, regions=r * r),
            "bbox": [lon0, lat0, lon0 + (v + 1) * k * dlon, lat0 + (h + 1) * k * dlat],
            "lines": lines,
        }
        with open(a.out.rsplit(".", 1)[0] + ".meta.json", "w") as f:
            json.dump(meta, f, indent=1)
    print(
        f"triples={w.n} elements={counters['ne']} relations={counters['nr']} "
        f"signals={counters['sig']} ops={counters['op']} tracks={counters['track']} regions={r * r}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
