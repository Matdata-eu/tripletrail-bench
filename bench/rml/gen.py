"""Writes the CSV files of the RML throughput benchmark into DIR (default data/).

tracks.csv: track sections (about 60 bytes a row; --rows 21500000 is about 1 GB).
lines.csv: the lines they belong to (--lines rows), joined on tracks.line = lines.id.

    python3 gen.py --rows 21500000 --lines 100000 data/
"""

import argparse
import os
import random

p = argparse.ArgumentParser()
p.add_argument("--rows", type=int, default=21_500_000)
p.add_argument("--lines", type=int, default=100_000)
p.add_argument("dir", nargs="?", default="data")
a = p.parse_args()
os.makedirs(a.dir, exist_ok=True)
rnd = random.Random(42)
with open(os.path.join(a.dir, "lines.csv"), "w") as f:
    f.write("id,name,gauge\n")
    for i in range(a.lines):
        f.write(f"{i},Line {i},1435\n")
with open(os.path.join(a.dir, "tracks.csv"), "w") as f:
    f.write("id,name,line,km,speed,electrified\n")
    buf = []
    for i in range(a.rows):
        buf.append(
            f"T{i},Track {i},{rnd.randrange(a.lines)},{rnd.random() * 500:.3f},"
            f"{rnd.choice((80, 120, 160, 200))},{rnd.choice(('true', 'false'))}\n"
        )
        if len(buf) == 100_000:
            f.write("".join(buf))
            buf.clear()
    f.write("".join(buf))
