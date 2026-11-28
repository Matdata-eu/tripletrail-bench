#!/usr/bin/env python3
"""Tests of compare.py's reference rule (tripletrail-bench#96): PostGIS when it answered, else
the majority of the engines that answered, and never one engine alone; and of majority.py, the
same rule for result sizes.

    python3 bench/v2/test_compare.py
"""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare  # noqa: E402
import majority  # noqa: E402

QID = "agg_total_length"  # a scalars query: one number per run


def write(folder, answers, triples=None):
    """answers: {engine: [value of run 0, value of run 1, ...]}; triples: {engine: n} for load.json."""
    for e, values in answers.items():
        os.makedirs(os.path.join(folder, e), exist_ok=True)
        runs = [{"index": i, "ok": True, "result": {"values": [v]}} for i, v in enumerate(values)]
        with open(os.path.join(folder, e, f"{QID}.json"), "w") as f:
            json.dump({"qid": QID, "status": "ok", "runs": runs}, f)
        if triples and e in triples:
            with open(os.path.join(folder, e, "load.json"), "w") as f:
                json.dump({"triples": triples[e]}, f)


def rows(folder):
    old = sys.argv
    sys.argv = ["compare.py", folder]
    try:
        compare.main()
    finally:
        sys.argv = old
    with open(os.path.join(folder, "correctness.csv"), newline="") as f:
        return {r["engine"]: r for r in csv.DictReader(f) if r["qid"] == QID}


class ReferenceRule(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self._stdout
        shutil.rmtree(self.dir)

    def test_postgis_is_the_reference_when_it_answered(self):
        write(self.dir, {"postgis": [10.0], "tripletrail": [10.0], "qlever": [11.0], "jena": [11.0]})
        r = rows(self.dir)
        self.assertNotIn("postgis", r)
        self.assertEqual({e: x["reference"] for e, x in r.items()}, {e: "postgis" for e in r})
        self.assertEqual(r["tripletrail"]["match"], "1")
        # PostGIS wins over a majority that disagrees with it.
        self.assertEqual(r["qlever"]["mismatch"], "1")
        self.assertEqual(r["jena"]["mismatch"], "1")

    def test_without_postgis_the_majority_is_the_reference(self):
        write(self.dir, {"tripletrail": [10.0, 5.0], "qlever": [11.0, 5.0], "graphdb": [11.0, 5.0]})
        r = rows(self.dir)
        self.assertEqual({x["reference"] for x in r.values()}, {"majority"})
        # TripleTrail is the one that differs in run 0, so it is the one charged with it.
        self.assertEqual((r["tripletrail"]["match"], r["tripletrail"]["mismatch"]), ("1", "1"))
        for e in ("qlever", "graphdb"):
            self.assertEqual((r[e]["match"], r[e]["mismatch"]), ("2", "0"))
        self.assertEqual(compare.verdicts(self.dir)[(QID, "tripletrail")][0], "mismatch")
        self.assertEqual(compare.verdicts(self.dir)[(QID, "qlever")][0], "ok")

    def test_no_majority_means_no_reference(self):
        write(self.dir, {"tripletrail": [10.0], "qlever": [11.0], "graphdb": [12.0]})
        r = rows(self.dir)
        for e in r:
            self.assertEqual((r[e]["mismatch"], r[e]["no_reference"]), ("0", "1"))
            self.assertEqual(compare.verdicts(self.dir)[(QID, e)][0], "unchecked")

    def test_two_engines_that_disagree_have_no_reference(self):
        write(self.dir, {"tripletrail": [10.0], "qlever": [11.0]})
        r = rows(self.dir)
        self.assertEqual((r["qlever"]["mismatch"], r["qlever"]["no_reference"]), ("0", "1"))
        self.assertEqual((r["tripletrail"]["mismatch"], r["tripletrail"]["no_reference"]), ("0", "1"))

    def test_tripletrail_alone_is_never_the_reference(self):
        write(self.dir, {"tripletrail": [10.0]})
        r = rows(self.dir)
        self.assertEqual((r["tripletrail"]["match"], r["tripletrail"]["no_reference"]), ("0", "1"))
        self.assertEqual(compare.verdicts(self.dir)[(QID, "tripletrail")][0], "unchecked")

    def test_the_majority_is_taken_on_the_extract_most_engines_loaded(self):
        write(self.dir, {"tripletrail": [10.0], "qlever": [11.0], "graphdb": [11.0]},
              triples={"tripletrail": 201, "qlever": 200, "graphdb": 200})
        r = rows(self.dir)
        self.assertEqual((r["tripletrail"]["mismatch"], r["tripletrail"]["other_extract"]), ("0", "1"))
        self.assertIn("other extract", r["tripletrail"]["note"])
        self.assertEqual((r["qlever"]["match"], r["graphdb"]["match"]), ("1", "1"))


class MajorityOfSizes(unittest.TestCase):
    """majority.wrong, the same rule for Sparqloscope's and Trainmarks' result sizes."""

    def test_the_odd_one_out_is_wrong(self):
        self.assertEqual(majority.wrong({"tripletrail": 3, "qlever": 3, "jena": 4}), {"jena"})
        self.assertEqual(majority.wrong({"tripletrail": 4, "qlever": 3, "jena": 3}), {"tripletrail"})

    def test_no_majority_says_nothing(self):
        self.assertEqual(majority.wrong({"tripletrail": 3, "qlever": 4}), set())
        self.assertEqual(majority.wrong({"tripletrail": 1, "qlever": 1, "jena": 2, "graphdb": 2}), set())
        self.assertEqual(majority.wrong({"tripletrail": 1, "qlever": 2, "jena": 3}), set())

    def test_one_engine_alone_is_never_right_by_default(self):
        self.assertEqual(majority.wrong({"tripletrail": 3}), set())


if __name__ == "__main__":
    unittest.main()
