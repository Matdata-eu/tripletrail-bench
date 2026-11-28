# TripleTrail benchmarks

The benchmark harness of [TripleTrail](https://github.com/Matdata-eu/tripletrail), its results
and the [dashboard](https://matdata-eu.github.io/tripletrail-bench/) that shows them.

TripleTrail is measured against PostGIS + pgRouting, QLever, Apache Jena (Fuseki +
jena-geosparql), GraphDB, Oxigraph and maplib, on spatial and routing workloads (benchmark v2,
Geographica 2, OSM at scale) and on the standard RDF suites (BSBM, Sparqloscope, Trainmarks,
updates). Every result comes from a run of the [Benchmarks](.github/workflows/bench.yml)
workflow on a Hetzner server rented for that run: the run's page has its logs, its manifest
(`bench/v2/results/runs/<run>.json`) names the TripleTrail commit, the harness commit and the
machine, and the raw results are next to it in `bench/v2/results/`.

| Where | What |
|---|---|
| [`bench/v2/`](bench/v2) | The harness: `bench.sh` (one entry point), `run_all.sh` and `run.py` (benchmark v2), the engines' settings (`engines/`), the queries per engine (`queries/`), the data generators (`data/`), the profiles (`profiles/`) |
| [`bench/v2/suites/`](bench/v2/suites) | BSBM, Sparqloscope, Trainmarks, updates, scale, OLTP |
| [`bench/v2/geographica/`](bench/v2/geographica) | Geographica 2 |
| [`bench/v2/cloud/`](bench/v2/cloud) | How a run rents, uses and deletes a server |
| [`bench/rml/`](bench/rml) | RML lifting against Morph-KGC |
| [`bench/facadex/`](bench/facadex) | Facade-X lifting (CSV, JSON, XML) against SPARQL Anything |
| [`crates/tripletrail-bench/`](crates/tripletrail-bench) | Micro-benchmarks in Rust on a generated ERA-shaped network and on real RINF files (`cargo run --release -p tripletrail-bench`, `--bin store`, `--bin cost`, `--bin rinf`, `--bin access`), built against TripleTrail in `core/` |
| [`bench/v2/results/`](bench/v2/results) | Results, run manifests, and the files the dashboard reads |
| [`site/`](site) | The dashboard (GitHub Pages) and `summary.py`, the headline numbers as JSON |

The results start empty: the first complete run measures the first public release.

## Datasets

| Dataset | Triples | Content |
|---|---:|---|
| `small` (synthetic RINF) | 805,538 | 24 × 24 grid of lines, 20 elements between crossings: 26,304 linear elements, 30,864 net relations, 1,201 tracks, 24,000 signals, 4,176 operational points, 48 national lines, 9 regions |
| `large` (synthetic RINF) | 10,539,890 | 88 × 88 grid: 344,256 linear elements, 406,032 net relations, 15,665 tracks, 313,280 signals, 54,736 operational points, 25 regions |
| `osm_norway` | 1,458,029 | From `norway-rail-landuse-admin.osm.pbf` (OSM as of 2026-11-05): 13,108 `railway=rail` ways, 1,123 stations, 275,718 landuse areas, 390 administrative areas (levels 2-7) |
| `geographica` | 2,065,148 | The Geographica 2 real-world datasets used by the micro and macro workloads: CORINE land cover, DBpedia, GAG, GeoNames, hotspots, LinkedGeoData, each in its own named graph |

**Synthetic RINF** (`gen_rinf_synth.py --h 24 --v 24 --k 20 --regions 3 --seed 42` for small,
`--h 88 --v 88 --k 20 --regions 5` for large). It uses the ERA vocabulary as published:
`era:LinearElement` with `geo:hasGeometry/geo:asWKT` (CRS84) and `era:length`,
`era:NetRelation` with `era:elementA/elementB`, `era:isOnOriginOfElementA/B` and
`era:navigability` (Both / None), `era:Track` with `era:wheelSetGauge` (1435 or 1520 mm),
`era:contactLineSystem` (overhead or not electrified) and `era:maximumPermittedSpeed`,
`era:OperationalPoint` and `era:Signal` with POINT geometries, `era:lineReference` /
`era:kilometer`, and topological coordinates (`era:netReference` / `era:hasTopoCoordinate` /
`era:onLinearElement` / `era:offsetFromOrigin`). Lines cross on a grid. Every crossing has four
switch-connected link elements, one per turn, so routing is edge-based (the ERA micro profile:
graph vertices are element ends). Two differences from real RINF data matter for the results:
the geometry is a regular grid with short, straight elements (real track is longer and
curved, so per-geometry costs are lower here), and the regions are 9 or 25 jittered
rectangles (real admin units have many more vertices). The generator is deterministic, so the
same arguments give the same file on every machine.

**OSM Norway.** `bench/v2/data/osm_extract.py` builds the dataset from the pbf with osmium
(`tags-filter` + `export`, which assembles multipolygons). It writes N-Triples with osm2rdf's
IRIs (`https://www.openstreetmap.org/{node,way,relation}/<id>`) and `geo:hasGeometry/geo:asWKT`,
and loads the same WKT strings into PostGIS, so every engine sees identical geometries.

**Geographica 2.** `bench/v2/geographica/run_geographica.py prepare` unpacks the six
real-world tarballs into one N-Quads file, each dataset in the named graph the query lists use
(`http://geographica.di.uoa.gr/dataset/{clc,dbpedia,gag,geonames,hotspots,lgd}`).

## Method and engine settings

- **One engine at a time.** `run_all.sh` stops every engine before it starts the next, and
  calls `sync`. Nothing else ran while an engine was timed.
- **Warm and cold.** Each query family starts with a restart of the engine. The first run of
  each query is the *cold* run: for the first query of a family the engine's caches are empty.
  The OS page cache stays warm, because dropping it needs root on the host. Then 2 untimed
  warm-up runs, then N timed *warm* runs. Each run has its own parameters (bounding box,
  point, route pair...), drawn from a seed per query and run index, so run *i* uses the same
  parameters on every engine. The tables give the warm p50 / p95 and the cold run.
- **After a failure.** A run that times out or fails is followed by a restart of the engine (and
  the family's setup again) before the next run, so a query the engine did not cancel cannot
  share the machine with the next one. The query's result file lists those runs under
  `restarted_after`.
- **N.** `small`: 30 runs for selections, KNN and LR, 1,000 route pairs, 200 constrained pairs,
  50 driving-distance / KSP / mixed runs, 10 cost matrices, 5 joins and aggregates. `large`: the
  same counts × 0.2 (`WARM_SCALE=0.2`, so 200 route pairs and one warm run for the joins).
- **Timing.** Wall clock at the client, including the protocol (HTTP + SPARQL JSON results for
  the RDF engines, libpq for PostGIS) and fetching all rows. Timeout 300 s (600 s for
  joins and aggregates). QLever's result cache is cleared before every run.
- **Correctness.** `compare.py` checks every engine's answers against a reference, run by run,
  and writes `correctness.csv` next to the results (tripletrail-bench#96).
  - The reference is PostGIS/pgRouting where it ran. Elsewhere (the scale suite, `route_ch`, OSM
    runs without PostGIS), it is the answer a strict majority of the engines gave, at least two of
    them, on the extract most of them loaded. One engine is never the reference on its own, and
    TripleTrail is no exception.
  - A run without such a majority counts as "no reference" for every engine, not as a mismatch.
  - A query an engine answered differently from the reference in any run is a wrong answer.
    `report.md` strikes its time out, and the dashboard counts it as not answered. It is
    therefore left out of every geometric mean and speedup, `summary.json` included, and the
    dashboard lists it with its note.
  - Times that could not be checked (another extract, no majority) stay in, marked "unchecked"
    in `report.md`.
- **Query forms.** Each engine runs its own fastest correct form of the same question, in
  `bench/v2/queries/<engine>/`. TripleTrail and GraphDB use standard GeoSPARQL `FILTER` functions
  (GraphDB uses its indexed `geo:sfWithin` property form for the box and polygon selections).
  Jena uses `spatial:withinBox`, `spatial:nearby` and `spatial:nearbyGeom` from its spatial
  index; a `FILTER` was faster than its property functions for the region join. QLever uses
  `geof:metricDistance`, its `spatialSearch` service (S2 for KNN, libspatialjoin for the
  distance joins). PostGIS uses `ST_Intersects` / `ST_DWithin` on `geography`, `<->` KNN and
  pgRouting functions on a `micro_edges` table built from the same N-Triples.
- **Spatial indexes.** TripleTrail's `serve` builds its R-tree in the background once a dataset is
  open, and makes each dataset's map (profile, shapes, facet counts) after that. The bench waits until
  `/$/ready` answers 200 (the index is built) and the map's line is in the server log ("map
  ready") before it times anything, so neither is in the query times. PostGIS has GiST indexes on `geom` and on `geom::geography`, then `VACUUM ANALYZE`.
  GraphDB has its GeoSPARQL plugin enabled after loading (the time is in "index"). Jena builds
  its spatial index file at first start. QLever builds with
  `--vocabulary-type on-disk-compressed-geo-split`.
- **Memory and cores.** Every engine of a run gets the same budget, and runs as the only process
  ([`engines/budget.sh`](bench/v2/engines/budget.sh), tripletrail-bench#94).
  - `BENCH_MEMORY` is the memory for each engine. It defaults to half the machine's RAM: 32G on
    a 64 GB ccx43. The other half is left to the OS page cache and the client.
  - `BENCH_CORES` is the cores one query may use. It defaults to all of them, since TripleTrail
    uses them all.
  - How each engine gets the budget:

    | Engine | Memory | Cores per query |
    |---|---|---|
    | TripleTrail | `--memory-limit` | all |
    | Jena | `-Xms`/`-Xmx` | one (Fuseki's design) |
    | GraphDB | `-Xms`/`-Xmx` | one |
    | QLever | `-m` for queries and for the index build, with `-c 2G` of it for the cache | its own |
    | PostgreSQL | `shared_buffers` 25 % and `effective_cache_size` 75 % of the budget | `max_parallel_workers_per_gather` and `max_parallel_workers` = `BENCH_CORES` |

    PostgreSQL also gets `work_mem=256MB`, `random_page_cost=1.1` and `jit=off`
    (`engines/postgis.conf`). Oxigraph and maplib have no such settings.
  - `env.json` (and each run's manifest) records the budget under `budget`, with what each engine
    was given. The dashboard's provenance table shows it.
  - An engine's own variable (`JENA_HEAP`, `GRAPHDB_HEAP`, `QLEVER_MEMORY`,
    `QLEVER_INDEX_MEMORY`, `TRIPLETRAIL_MEMORY_LIMIT`, `PG_SHARED_BUFFERS`,
    `PG_EFFECTIVE_CACHE`) still overrides it.
  - Results from before #94 ran with unequal budgets: Jena, GraphDB and QLever had 8 GB,
    TripleTrail had no limit, and PostgreSQL had 4 parallel workers.
- **Memory after start.** "RSS after start" is taken once the engine is ready to be timed: for
  TripleTrail, after the R-tree and the map warm-up above. The figure "when it first answered" is
  TripleTrail's RSS as soon as the dataset answers `ASK {}`, before that start-up work. Runs from
  before tripletrail-bench#39 took RSS after start at that moment, so compare those with the
  "when it first answered" figure.
- **Routing graph.** TripleTrail builds named networks from the ERA micro profile edge query
  (`queries/tripletrail/setup_routing.ru`; `bench:microc` adds gauge and electrification columns for
  the constrained route). PostGIS gets the same edges, computed in Python by
  `data/export_postgis.py`. Vertices are element ends (`E#fwd`, `E#bwd`), cost is the element
  length in metres, and route pairs are drawn from all vertices, so some pairs have no path.

## Running it

The workflow is the way results get here (see [`bench/v2/cloud/README.md`](bench/v2/cloud/README.md)).
To run something on your own machine:

```sh
git clone https://github.com/Matdata-eu/tripletrail-bench && cd tripletrail-bench
git clone https://github.com/Matdata-eu/tripletrail core
(cd core && cargo build --release -p tripletrail-server)        # core/target/release/tripletrail
export BENCH_WORK=$PWD/bench/v2/work                            # stores and data; gitignored
mkdir -p $BENCH_WORK/jena && curl -o $BENCH_WORK/jena/jena-fuseki-geosparql-6.2.0.jar \
  https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-geosparql/6.2.0/jena-fuseki-geosparql-6.2.0.jar

bench/v2/bench.sh v2 small                       # benchmark v2 on the small synthetic set, all engines
bench/v2/bench.sh bsbm 2785 tripletrail qlever   # one suite, some engines
bench/v2/bench.sh all full                       # everything of profiles/full.txt (a 64 GB machine)
bench/v2/bench.sh all threads tripletrail tripletrail-1t  # all cores against one (profiles/threads.txt)
```

Requirements: Linux, Docker (QLever, GraphDB, Oxigraph and the suites' tools run in
containers), Java 21 for Jena, Python 3 with `requests`, `pyyaml` and `psycopg2`, `osmium-tool`
for OSM, `bc` and GNU `time`, and either a local PostgreSQL 16 with PostGIS and pgRouting or the
compose service (`docker compose -f bench/v2/docker-compose.yml up -d postgis`). Environment
variables: `BENCH_WORK`, `BENCH_MEMORY`, `BENCH_CORES`, `WARM_SCALE`, `ONLY` (queries or families, e.g. `ONLY=6,mixed_*`),
`SKIP_LOAD=1`, `DROP_AFTER=1`, `TRIPLETRAIL_BIN`, `TRIPLETRAIL_WARM_WAIT`, `JENA_JAR`, `JENA_HEAP`, `GRAPHDB_IMAGE`,
`GRAPHDB_HEAP`, `QLEVER_IMAGE`, `QLEVER_MEMORY`, `QLEVER_INDEX_MEMORY`, `QLEVER_CACHE`, `PG_DSN_BASE`, `PG_CONTAINER`,
`GEOGRAPHICA_TIMEOUT`, `PERF_QUERIES` (query ids to profile on TripleTrail with `perf` during their warm runs: `perf-<qid>.txt` beside their results).

## Licence

The harness is under the Apache License 2.0 ([LICENSE](LICENSE)). The suites' own tools and
data keep their licences (listed in [`bench/v2/suites/README.md`](bench/v2/suites/README.md));
nothing under a copyleft licence is copied into this repository, it is fetched at run time.
