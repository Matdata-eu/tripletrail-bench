#!/usr/bin/env python3
"""differences() counts the result keys only one engine gives, by path, component and severity,
names no focus node, and compares engines run one at a time (as run_suite.sh runs them).

  python3 bench/v2/suites/shacl/test_differences.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_shacl  # noqa: E402

SH = "http://www.w3.org/ns/shacl#"
P = "http://data.europa.eu/949/length"


def key(focus, comp, path=P, sev="Violation"):
    return "\t".join((focus, path, SH + comp, SH + sev))


class Differences(unittest.TestCase):
    def write(self, d, engine, keys, res=None):
        """An engine's key file, and (in res) its record with the keys' hash, as run_one leaves them."""
        path = os.path.join(d, f"{engine}.keys")
        with open(path, "w") as f:
            f.writelines(k + "\n" for k in sorted(keys))
        if res:
            rec = run_shacl.run_phase0.summary({"Violation": len(keys)}, keys, False, set())
            json.dump(rec, open(os.path.join(res, f"{engine}.json"), "w"))

    def test_counts_by_path_and_component_and_deletes_the_keys(self):
        with tempfile.TemporaryDirectory() as keys, tempfile.TemporaryDirectory() as res:
            same = [key(f"http://x/n{i}", "MinCountConstraintComponent") for i in range(5)]
            # One engine per run, as run_suite.sh does: the first finds nothing to compare with.
            self.write(keys, "tripletrail", same + [key("http://x/t1", "DatatypeConstraintComponent"),
                                                    key("http://x/t2", "DatatypeConstraintComponent")], res)
            run_shacl.differences(keys, res)
            self.assertFalse(os.path.exists(os.path.join(res, "differences.json")))
            self.write(keys, "jena", same + [key("http://x/j", "SPARQLConstraintComponent", "_:")], res)
            self.write(keys, "pyshacl", same, res)
            run_shacl.differences(keys, res)
            text = open(os.path.join(res, "differences.json")).read()
            self.assertNotIn("http://x/", text)
            d = json.loads(text)
            self.assertEqual(d["reference"], "jena")
            tt = d["engines"]["tripletrail"]
            self.assertEqual((tt["only_here"], tt["only_in_reference"]), (2, 1))
            self.assertEqual(tt["by_path"][0], {"path": P, "component": "DatatypeConstraintComponent",
                                                "severity": "Violation", "only_here": 2, "only_in_reference": 0})
            self.assertEqual(tt["by_path"][1]["path"], "_:")
            self.assertEqual(d["engines"]["pyshacl"]["only_in_reference"], 1)
            lines = run_shacl.differences_lines(os.path.join(res, "differences.json"))
            self.assertTrue(any(line.startswith("- tripletrail against jena: 2 keys only in tripletrail, 1 only in jena.") for line in lines))

    def test_no_file_when_the_engines_agree(self):
        with tempfile.TemporaryDirectory() as keys, tempfile.TemporaryDirectory() as res:
            for e in ("topbraid", "jena"):
                self.write(keys, e, [key("http://x/a", "ClassConstraintComponent")], res)
            run_shacl.differences(keys, res)
            self.assertFalse(os.path.exists(os.path.join(res, "differences.json")))

    def test_a_key_file_of_an_earlier_run_is_left_out(self):
        with tempfile.TemporaryDirectory() as keys, tempfile.TemporaryDirectory() as res:
            self.write(keys, "jena", [key("http://x/a", "ClassConstraintComponent")], res)
            # A key file whose engine's record no longer has its hash (another run, or a failure).
            self.write(keys, "tripletrail", [key("http://x/b", "ClassConstraintComponent")])
            json.dump({"engine": "tripletrail", "error": "timed out"}, open(os.path.join(res, "tripletrail.json"), "w"))
            run_shacl.differences(keys, res)
            self.assertFalse(os.path.exists(os.path.join(res, "differences.json")))
            self.assertEqual(os.listdir(keys), ["jena.keys"])


if __name__ == "__main__":
    unittest.main()
