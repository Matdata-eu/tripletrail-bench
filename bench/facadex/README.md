# Facade-X benchmark

How fast `tripletrail lift` runs Facade-X `CONSTRUCT` queries over CSV, JSON and XML files,
and how much memory it takes, next to the
[SPARQL Anything](https://github.com/SPARQL-Anything/sparql.anything) command line
(Apache-2.0, Java), on the same queries, which run unchanged in both. Three queries, in
`queries/`:

- `csv.rq`: each row of `tracks.csv` (id, line, length, speed, electrified) as a track with a
  class, an IRI to its line and three typed values, so 5 triples a row;
- `json.rq`: each object of `stations.json` as a station with its name, country, a WKT point
  built from its coordinates, and one triple per platform of its array (`fx:anySlot`);
- `xml.rq`: each `<point>` element of `points.xml` as an operational point, from its `id`
  attribute and its `name`, `type` and `km` children.

`run.py` checks that both tools write the same triples. Never run in CI.

## Running it

```sh
python3 gen.py --rows 3000000 data/        # tracks.csv about 90 MB, the others a tenth of the rows
mvn -q dependency:copy-dependencies -DoutputDirectory=lib    # SPARQL Anything 1.3.0 from Maven Central, with pom.xml
(cd ../../core && cargo build --release -p tripletrail-server)   # TripleTrail checked out in core/
python3 run.py --tripletrail ../../core/target/release/tripletrail --sparql-anything lib
```

`run.py` prints wall time, peak resident memory and the triples written, for each query and
tool. Both write N-Triples to `out/`, which is counted, sorted and compared, then removed
(`--keep` keeps it). SPARQL Anything gets `-Xmx12g` (`--heap`). Leave out `--sparql-anything`
to run TripleTrail only.

## Results (2026-11-26)

A 4-core Intel Xeon at 2.30 GHz with 15 GB of memory, Linux; TripleTrail from main at
c09412f, SPARQL Anything 1.3.0 on OpenJDK 21. One run each, started cold (the files in the
page cache).

**3,000,000 rows** (tracks.csv 90 MB; stations.json 36 MB and points.xml 26 MB, 300,000 each)

| Query | Tool | Time | Peak memory | Triples |
|---|---|---:|---:|---:|
| csv | TripleTrail | 61 s | 5.3 GiB | 15,000,000 |
| csv | SPARQL Anything | 97 s | 12.2 GiB | 15,000,000 |
| json | TripleTrail | 8.8 s | 1.6 GiB | 1,949,449 |
| json | SPARQL Anything | 17.2 s | 5.0 GiB | 1,949,449 |
| xml | TripleTrail | 8.0 s | 2.0 GiB | 1,200,000 |
| xml | SPARQL Anything | 18.7 s | 7.5 GiB | 1,200,000 |

**1,000,000 rows** (tracks.csv 29 MB; 100,000 stations and points)

| Query | Tool | Time | Peak memory | Triples |
|---|---|---:|---:|---:|
| csv | TripleTrail | 18.1 s | 2.0 GiB | 5,000,000 |
| csv | SPARQL Anything | 34.4 s | 7.9 GiB | 5,000,000 |
| json | TripleTrail | 3.0 s | 0.6 GiB | 650,293 |
| json | SPARQL Anything | 6.7 s | 2.3 GiB | 650,293 |
| xml | TripleTrail | 2.5 s | 0.9 GiB | 400,000 |
| xml | SPARQL Anything | 8.0 s | 3.4 GiB | 400,000 |

Both tools wrote the same triples for every query. SPARQL Anything's peak for the 3,000,000
row CSV is the 12 GiB heap it was given; with less it runs longer in garbage collection or
fails.

Both tools build the file's whole Facade-X graph in memory before the query runs on it, so
memory grows with the file: TripleTrail about 1.8 KB a CSV row here, SPARQL Anything about
4 KB. SPARQL Anything's `slice=true` option, which runs the query once per row instead, is
not used: it changes what a query that joins rows sees.
