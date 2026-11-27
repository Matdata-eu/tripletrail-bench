#!/usr/bin/env python3
"""The suite's queries give the expected answers on a small RINF-like extract (testdata/).

  python3 bench/v2/suites/rinfshapes/test_queries.py

Runs each query's rows and count forms with `tripletrail query` on testdata/extract.ttl, without
a server. TRIPLETRAIL_BIN names the binary (default: core/target/release/tripletrail, as
engines/tripletrail.sh); the tests are skipped when it is not there.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from queries import QUERIES, BY_ID  # noqa: E402
from run_rinfshapes import clean  # noqa: E402

BIN = os.environ.get("TRIPLETRAIL_BIN", os.path.join(HERE, "..", "..", "..", "..", "core", "target", "release", "tripletrail"))
DATA = os.path.join(HERE, "testdata", "extract.ttl")
FI = "http://data.europa.eu/949/functionalInfrastructure/"
G = "http://data.europa.eu/949/concepts/gaugings/"
C = "http://publications.europa.eu/resource/authority/country/"

# The expected rows, with IRIs shortened to their local name (t1, sol1, G1, DEU, ...). An ordered
# query's rows must come in this order; the others are compared as sets.
EXPECTED = {
    "facet-gauging-deu": [("G1", 2), ("G2", 2)],
    "facet-sol-length": [("DEU", 14, 2), ("FRA", 20, 1)],
    "topk-speed-label": [("t4", 300, "T4"), ("t7", 250, "T7"), ("t1", 200, "T1"), ("t2", 160, "T2"), ("t3", 120, "T3")],
    "topk-cant-speed": [("t4", 170, 300), ("t7", 160, 250), ("t1", 160, 200), ("t3", 150, 120), ("t2", 100, 160)],
    "star-speed-cant-deu": [("t1", 200)],
    "star-bool-range": [("t1", 200), ("t4", 300)],
    "chain-track-op": [("t1", 200, "sol1", 10, "A Nord"), ("t2", 160, "sol1", 10, "A Nord"),
                       ("t4", 300, "sol3", 20, "C"), ("t7", 250, "sol3", 20, "C")],
    "chain-op-wkt": [("op1", "A Nord", "POINT(4.1 50.8)"), ("op2", "B", "POINT(4.2 50.9)")],
    "wide-track-optional": [("t1", "T1", 200, 160, "N"), ("t2", "T2", 160, 100, None), ("t3", "T3", 120, 150, None),
                            ("t4", "T4", 300, 170, None), ("t5", "T5", None, None, None),
                            ("t6", "T6", None, 80, None), ("t7", "T7", 250, 160, None)],
    "wide-op": [("op1", "A Nord", "DEU", "pl1", "DE001"), ("op2", "B", "DEU", "pl2", None),
                ("op3", "C", "FRA", "pl3", "FR001")],
    "anti-track-no-speed": [("t5",), ("t6",)],
    "control-topk-speed": [("x1", 400), ("t4", 300), ("t7", 250), ("t1", 200), ("t2", 160), ("t3", 120)],
    # t1 and t7 tie on 160: compared as a set, the order of the cant values is checked apart.
    "control-topk-cant": [("x1", 200), ("t4", 170), ("t1", 160), ("t7", 160), ("t3", 150), ("t2", 100), ("t6", 80)],
    "control-facet-gauging-join": [("t1", "G1"), ("t2", "G1"), ("t3", "G2"), ("t5", "G2")],
    "control-facet-gauging-noclass": [("G1", 3), ("G2", 2)],
    "control-facet-sol-join": [("sol1", "DEU", 10), ("sol2", "DEU", 4), ("sol3", "FRA", 20)],
}
ORDERED = {"topk-speed-label", "topk-cant-speed", "control-topk-speed"}


def short(v):
    if v is None:
        return None
    for prefix in (FI, G, C):
        if v.startswith(prefix):
            return v[len(prefix):]
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except ValueError:
        return v


def run(text):
    r = subprocess.run([BIN, "query", "--data", DATA, "--query", text, "--format", "json"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"tripletrail query failed:\n{r.stderr}\n{text}")
    j = json.loads(r.stdout)
    vs = j["head"]["vars"]
    return [tuple(short(b.get(v, {}).get("value")) for v in vs) for b in j["results"]["bindings"]]


def key(row):
    return tuple((x is None, str(x)) for x in row)


class Suite(unittest.TestCase):
    def test_every_query_has_an_answer(self):
        self.assertEqual(set(EXPECTED), set(BY_ID))

    def test_controls_name_a_query_of_the_suite(self):
        for q in QUERIES:
            if q.control_of:
                self.assertIn(q.control_of, BY_ID)
                self.assertEqual(q.shape, "control")


class Clean(unittest.TestCase):
    XSD = "http://www.w3.org/2001/XMLSchema#"

    def line(self, literal):
        return f"<http://a> <http://b> {literal} .\n".encode()

    def test_numbers(self):
        self.assertIsNone(clean(self.line(f'"12"^^<{self.XSD}integer>')))
        self.assertIsNone(clean(self.line(f'"-1.5E3"^^<{self.XSD}double>')))
        self.assertEqual(clean(self.line(f'"N"^^<{self.XSD}integer>')), "not a number: xsd:integer")
        self.assertEqual(clean(self.line(f'"1.5"^^<{self.XSD}integer>')), "not a number: xsd:integer")

    def test_geometries(self):
        wkt = "<http://www.opengis.net/ont/geosparql#wktLiteral>"
        self.assertEqual(clean(self.line(f'"LINESTRING (24.27 54.89)"^^{wkt}')), "LINESTRING of one point")
        self.assertIsNone(clean(self.line(f'"LINESTRING (1 2, 3 4)"^^{wkt}')))
        self.assertIsNone(clean(self.line(f'"POINT (1 2)"^^{wkt}')))
        as_wkt = "<http://www.opengis.net/ont/geosparql#asWKT>"
        self.assertEqual(clean(f'<http://a> {as_wkt} "NYA" .\n'.encode()), "geo:asWKT not a WKT literal")
        self.assertIsNone(clean(f'<http://a> {as_wkt} "POINT (1 2)"^^{wkt} .\n'.encode()))

    def test_long_lines(self):
        self.assertEqual(clean(self.line('"' + "x" * (4 * 1024 * 1024) + '"')), "line over 4 MiB")
        self.assertIsNone(clean(self.line('"short"')))


@unittest.skipUnless(os.access(BIN, os.X_OK), f"no tripletrail binary at {BIN} (set TRIPLETRAIL_BIN)")
class Answers(unittest.TestCase):

    def test_rows_and_count_forms(self):
        for q in QUERIES:
            with self.subTest(q.id):
                rows = run(q.rows)
                want = EXPECTED[q.id]
                if q.id in ORDERED:
                    self.assertEqual(rows, want)
                else:
                    self.assertEqual(sorted(rows, key=key), sorted(want, key=key))
                self.assertEqual(run(q.count), [(len(want),)], "the count form counts the rows form's rows")

    def test_ties_keep_the_order_of_the_sort_key(self):
        rows = run(BY_ID["control-topk-cant"].rows)
        self.assertEqual([r[1] for r in rows], [200, 170, 160, 160, 150, 100, 80])


if __name__ == "__main__":
    unittest.main()
