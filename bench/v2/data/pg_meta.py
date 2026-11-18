#!/usr/bin/env python3
"""Print postgis.sh's load record from an osm_extract.py meta file (postgis.sh load osm_*)."""
import json
import sys

m = json.load(open(sys.argv[1]))
print(json.dumps({"engine": "postgis", "dataset": sys.argv[2], "load_s": m["postgis"]["load_s"],
                  "disk_bytes": m["postgis"]["db_bytes"], "rows": m["counts"]}))
