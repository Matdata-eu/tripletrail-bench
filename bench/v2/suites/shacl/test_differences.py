#!/usr/bin/env python3
"""differences() counts the result keys only one engine gives, by path, component and severity,
and keeps no focus node.

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
    def write(self, d, engine, keys):
        with open(os.path.join(d, f"{engine}.keys"), "w") as f:
            f.writelines(k + "\n" for k in sorted(keys))

    def test_counts_by_path_and_component_and_deletes_the_keys(self):
        with tempfile.TemporaryDirectory() as keys, tempfile.TemporaryDirectory() as res:
            same = [key(f"http://x/n{i}", "MinCountConstraintComponent") for i in range(5)]
            self.write(keys, "jena", same + [key("http://x/j", "SPARQLConstraintComponent", "_:")])
            self.write(keys, "tripletrail", same + [key("http://x/t1", "DatatypeConstraintComponent"),
                                                    key("http://x/t2", "DatatypeConstraintComponent")])
            self.write(keys, "pyshacl", same)
            run_shacl.differences(keys, res)
            self.assertEqual(os.listdir(keys), [])
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
                self.write(keys, e, [key("http://x/a", "ClassConstraintComponent")])
            run_shacl.differences(keys, res)
            self.assertFalse(os.path.exists(os.path.join(res, "differences.json")))


if __name__ == "__main__":
    unittest.main()
