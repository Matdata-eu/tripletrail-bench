# RML throughput benchmark

How fast `tripletrail lift` runs an RML mapping over a large CSV file, and how much memory it
takes, next to [Morph-KGC](https://github.com/morph-kgc/morph-kgc) (Apache-2.0, Python) and
[RMLMapper](https://github.com/RMLio/rmlmapper-java) (MIT, Java). Two mappings:

- `simple.rml.ttl`: one triples map over `tracks.csv`, a subject template, a class and four
  typed literals (`xsd:decimal`, `xsd:integer`, `xsd:boolean`), so 5 triples a row.
- `join.rml.ttl`: each track linked to its line in `lines.csv` (100,000 rows) through a
  join condition (`tracks.line = lines.id`), plus the lines' classes.

Both start with `@base`, since RMLMapper refuses the relative IRIs of the triples maps
otherwise. Never run in CI.

## Running it

```sh
python3 gen.py --rows 21500000 --lines 100000 data/     # tracks.csv is about 1 GB
python3 -m venv /tmp/mk && /tmp/mk/bin/pip install morph-kgc
./fetch_rmlmapper.sh data/                               # RMLMapper 7.3.3, SHA-256 checked
(cd ../../core && cargo build --release -p tripletrail-server)   # TripleTrail checked out in core/
python3 run.py --tripletrail ../../core/target/release/tripletrail --morph-python /tmp/mk/bin/python \
    --rmlmapper data/rmlmapper.jar --java-image mirror.gcr.io/library/eclipse-temurin:21-jre
```

`run.py` prints wall time, peak resident memory and the triples written. TripleTrail's
N-Triples are counted from its standard output; Morph-KGC and RMLMapper write a file to
`out/`, counted and removed. RMLMapper runs with `java` on the host, or with `--java-image` in
a Java container (nothing installed on the host), with `-Xmx12g` (`--java-heap`); its memory
is the JVM's peak resident memory. `--timeout` (default 7200 s) stops a run, and `--tools`
picks some of `tripletrail morph-kgc rmlmapper`.

## Results (2026-11-14)

A 4-core Intel Xeon at 2.10 GHz with 15 GB of memory, Linux; TripleTrail from main with the
streaming lift (#159), Morph-KGC 2.10.0 on Python 3.13.

**1 GB, 21,500,000 rows**

| Mapping | Tool | Time | Peak memory | Triples |
|---|---|---:|---:|---:|
| simple | TripleTrail | 227 s | 3.5 GiB | 107,500,000 |
| join | TripleTrail | 81 s | 3.6 GiB | 21,600,000 |
| simple | Morph-KGC | did not finish in 2 h | | |

Morph-KGC took 3.8 GiB for a fifth of the rows (below), so on the full file it needs more
memory than the machine has; it was stopped after 2 hours.

**210 MB, 4,500,000 rows** (the first rows of the same file)

| Mapping | Tool | Time | Peak memory | Triples |
|---|---|---:|---:|---:|
| simple | TripleTrail | 41 s | 1.0 GiB | 22,500,000 |
| simple | Morph-KGC | 45 s | 3.8 GiB | 22,500,000 |
| join | TripleTrail | 18 s | 0.9 GiB | 4,600,000 |
| join | Morph-KGC | 34 s | 3.3 GiB | 4,600,000 |

Both tools write the same number of triples. TripleTrail's memory is mostly the source rows
it holds (about 100 bytes a row) and the source file while it is read; the triples
themselves are streamed, with duplicates dropped through temporary files.

Before #159's streaming change, `lift` held every triple of a mapping and every CSV row as
a JSON object: 1,000,000 rows took 34 s and 5.3 GB, and the 1 GB file did not fit.
