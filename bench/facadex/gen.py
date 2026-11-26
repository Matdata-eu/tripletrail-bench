"""Writes the Facade-X benchmark's input files into a folder:

    python3 gen.py --rows 1000000 data/

- tracks.csv: one row a track (id, line, length in metres, speed, electrified), `rows` rows;
- stations.json: an array of `rows // 10` objects (code, name, country, lat, lon, a list of
  platforms);
- points.xml: `rows // 10` operational points as elements with an id attribute and name,
  type and km children.

The values come from a fixed seed, so two runs write the same files.
"""

import argparse
import json
import os
import random

p = argparse.ArgumentParser()
p.add_argument("--rows", type=int, default=1_000_000)
p.add_argument("out")
a = p.parse_args()
os.makedirs(a.out, exist_ok=True)
r = random.Random(7)
countries = ["BE", "NL", "LU", "FR", "DE", "AT", "CH", "IT", "ES", "PL"]

with open(os.path.join(a.out, "tracks.csv"), "w") as f:
    f.write("id,line,length,speed,electrified\n")
    for i in range(a.rows):
        f.write(
            f"T{i},L{r.randrange(10_000)},{r.randrange(50, 20_000)}.{r.randrange(10)},"
            f"{r.choice((40, 60, 80, 100, 120, 160, 200, 250, 300))},{r.choice(('true', 'false'))}\n"
        )

n = max(a.rows // 10, 1)
with open(os.path.join(a.out, "stations.json"), "w") as f:
    f.write("[\n")
    for i in range(n):
        s = {
            "code": f"S{i}",
            "name": f"Station {i}",
            "country": r.choice(countries),
            "lat": round(r.uniform(36, 60), 5),
            "lon": round(r.uniform(-9, 24), 5),
            "platforms": [str(k + 1) for k in range(r.randrange(1, 5))],
        }
        f.write(json.dumps(s) + (",\n" if i + 1 < n else "\n"))
    f.write("]\n")

with open(os.path.join(a.out, "points.xml"), "w") as f:
    f.write("<points>\n")
    for i in range(n):
        f.write(
            f'<point id="P{i}"><name>Point {i}</name>'
            f"<type>{r.choice(('station', 'junction', 'halt', 'siding'))}</type>"
            f"<km>{r.randrange(0, 400)}.{r.randrange(1000):03d}</km></point>\n"
        )
    f.write("</points>\n")
