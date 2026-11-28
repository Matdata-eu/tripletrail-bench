# General RDF benchmark suites

The benchmark v2 workload (`../run.py`) measures spatial and routing queries. The suites here
measure plain SPARQL against the established RDF benchmarks, on the same engines (tripletrail,
plain Oxigraph, QLever, Jena, GraphDB), so the numbers can be put next to published ones.

| suite | what it measures | data | license | runner |
|---|---|---|---|---|
| [BSBM](bsbm/) | Berlin SPARQL Benchmark: e-commerce explore mix (12 templates), business-intelligence mix (8 analytical templates), explore + update mix; QMpH with the official test driver | generated, any size (`products`: 2785 ≈ 1M triples, 28480 ≈ 10M) | bsbmtools: Apache-2.0 | `bsbm/run_bsbm.py` |
| [Sparqloscope](sparqloscope/) | ~100 queries, each isolating one SPARQL feature (joins, OPTIONAL/MINUS/EXISTS, UNION, GROUP BY, paths, regex/string, numeric, date, language filters); same YAML as the QLever evaluation site | query sets generated per dataset: `bsbm-<n>`, `rinf-<code>` (real RINF data), `dblp` (official set, 61 GB) | Apache-2.0 | `sparqloscope/run_sparqloscope.py` |
| [Trainmarks](trainmarks/) | load + 6 queries (count, group-by, 3-way join, OPTIONAL + aggregates, CONSTRUCT, DELETE/INSERT) on a synthetic shop | generated, 100K / 1M / 10M triples | no license: fetched at run time, nothing copied | `trainmarks/run_trainmarks.py` |
| [Updates](updates/) | update throughput by update size (#496): batches of 10 to 10^6 held-out triples as INSERT DATA, then DELETE DATA (time per triple, p50/p95, failures, count checks), plus INSERT { } WHERE { } updates that mint nodes like the rail KG uplift; store size afterwards | any dataset: `bsbm-<n>` (10M triples hold out all sizes), `rinf-<code>` (smaller graphs stop at 10^5) | ours | `updates/run_updates.py` |
| [SHACL](shacl/) | SHACL validation (Core, SHACL-SPARQL) with the ERA RINF shapes in three profiles (Core only, per country, as published) on TripleTrail, Jena, TopBraid, GraphDB, RDF4J and pySHACL: time, peak memory, results and agreement with TopBraid and the majority; phase 0 adds feature probes per engine | RINF from ERA's endpoint (fetched, never committed); ERA shapes, ontology and code lists pinned to a commit | data: none published; shapes: EUPL-1.2; probes: ours | `shacl/run_shacl.py` (`run_suite.sh shacl rinf-<code>`, profile `shacl`) |
| [RINF shapes](rinfshapes/) | the query shapes of map clients on real railway data: facets over a big class, top-k over a star, stars with combined filters, chains, wide tables with OPTIONALs, anti-joins, valid on a day, and ablation controls; each query in a rows form and a count form | `rinf-all` (every graph of ERA's RINF endpoint, ~43 M triples, fetched, never committed) or `rinf-<code>` | ours | `rinfshapes/run_rinfshapes.py` (`run_suite.sh rinfshapes rinf-all`) |
| Rail pack (`railpack/`, in the enterprise repository) | the rail pack's (`packs/rail-era`) map on tripletrail only: `style.json`, every collection's facets unfiltered and under each map view's filters (cold, then from the result cache), and 85 `all` tiles per view with its filters and colours; which SPARQL-computed requirement checks reach their 10 s cap | `all` (every graph of ERA's RINF endpoint, ~43 M triples) or one graph `<code>` | ours | `railpack/run_railpack.py` |

FEASIBLE (query-log based, AGPL, DBpedia 3.5.1 and SWDF logs) was considered and left out: its
data is dated, downloads go through Google Drive, and its authors point to a successor.

## Running

```bash
export BENCH_WORK=/path/with/space   # data and stores; never in git
git clone https://github.com/Matdata-eu/tripletrail core && (cd core && cargo build --release -p tripletrail-server)
bench/v2/suites/run_suite.sh bsbm 2785                       # all five engines
bench/v2/suites/run_suite.sh sparqloscope rinf-0076 tripletrail oxigraph qlever
bench/v2/suites/run_suite.sh trainmarks large
bench/v2/suites/run_suite.sh updates bsbm-28480              # tripletrail oxigraph jena graphdb
bench/v2/suites/run_suite.sh rinfshapes rinf-all tripletrail oxigraph qlever jena
```

Each suite writes `results/<suite>/report.md` plus the raw per-engine files. For Sparqloscope,
`qlever serve-evaluation-app --results-dir results/sparqloscope/<dataset>` (from
[qlever-control](https://github.com/qlever-dev/qlever-control)) shows the results in the QLever
evaluation web app.

Requirements: docker (QLever, GraphDB, Oxigraph, the BSBM tools and the Python containers of
the Sparqloscope and Trainmarks generators run in containers), Java 21 for Jena, Python 3 with
`requests` and `pyyaml`. Engine settings are those of benchmark v2 (`../engines/*.sh`); the
plain Oxigraph engine is `../engines/oxigraph.sh` (docker image `ghcr.io/oxigraph/oxigraph`).

## Where to run

**Never in CI on pull requests.** The manual workflow `.github/workflows/bench.yml`
(**Benchmarks**) runs, through `../bench.sh`, either every benchmark at once (suite `all`, the
default: one TripleTrail commit, one machine, one results commit with a run manifest) or one
suite on one dataset, on a Hetzner server it rents for the run and deletes afterwards. See
[`../cloud/README.md`](../cloud/README.md).

## Method notes

- **BSBM**: bsbmtools 0.2 from SourceForge (sha256-checked), run in a Java container. Default 50
  timed query mixes after 10 warm-up mixes, one client, seed 808080, 60 s per-query timeout
  (`BSBM_RUNS`, `BSBM_WARMUP`, `BSBM_CLIENTS`, `BSBM_TIMEOUT_MS`). The generator holds back
  10 % of the products as the update stream. QLever has no update run (the test driver cannot
  send its access token). The test driver cannot clear QLever's result cache; BSBM draws new
  parameters for every query, so repeated identical queries are rare.
  TripleTrail's result cache is off in every suite (`engines/tripletrail.sh` starts it with
  `TRIPLETRAIL_RESULT_CACHE_MB=0` unless set): with it on, BSBM's business-intelligence queries,
  which repeat parameters, were answered from the cache (runs before 2026-11-13).
- **Sparqloscope**: the query set of a dataset is generated once with Sparqloscope's generator
  against QLever (it needs QLever's SERVICE) and committed under `sparqloscope/benchmarks/`, so
  all engines and later runs use the same queries. Each query runs once, cold, after an engine
  restart; 180 s timeout; a timed-out or crashed engine is restarted before the next query.
  Failures and timeouts count as 2 × timeout in the geometric mean, like the QLever evaluation.
- **Trainmarks**: the data generator (Python, standard library only, seed 42) runs from a pinned
  clone in a container without network. Load time = bulk load into each engine's store (the
  library frameworks on the Trainmarks site parse into memory instead, so compare those with
  care). Queries: one cold run, one warm-up, five timed runs (median); the update runs once.
  Trainmarks, BSBM and Sparqloscope also run maplib (in memory, Python; BSBM explore without
  Q9/Q12, like QLever, and BI without Q5, which maplib 0.22.0 still rejects; its endpoint answers
  SELECT in XML when asked, so the BSBM driver counts its results, and CONSTRUCT as N-Triples, which maplib writes from a scratch named graph; that adds about 13 ms on Trainmarks q5 large, measured against the query alone):
  `engines/maplib.sh` builds a small image with
  `pip install maplib==$MAPLIB_VERSION` (default 0.22.0; the endpoint needs 0.22.0 or later) and serves a Model through
  `engines/maplib_server.py`, a minimal SPARQL protocol endpoint, so it is timed over HTTP like
  the others; its load is reading the file into RAM. xlarge (10M triples) needs the 64 GB server
  (Jena and GraphDB at 8 GB heap); it is part of the `full` profile.
- **Updates** (#496, after Bigerl et al., "Efficient Updates for Worst-Case Optimal Join Triple
  Stores", ISWC 2025): `generate` holds out triples of the dataset without blank nodes (seed
  42): 50 batches of 10, 30 of 100, 10 of 1,000, 5 of 10,000, 3 of 100,000 and 1 of 1,000,000
  triples, as many sizes as fit in half of the data; the rest is the base data
  `updates-<dataset>`. Per engine: bulk load of the base data, then per size the INSERT DATA
  batches one at a time, a COUNT check, the same batches as DELETE DATA and a COUNT check.
  Then the derive family: for predicates with about 10^3, 10^4 and 10^5 triples, an
  `INSERT { } WHERE { }` that mints one node per triple (IRI from MD5 of the subject and object,
  3 triples plus one per type of the subject, an OPTIONAL join), undone by a `DELETE WHERE`. A
  failed update is recorded, not retried. Updates go as `application/sparql-update` bodies (a
  10^6 batch is about 250 MB), and TripleTrail runs with `TRIPLETRAIL_MAX_BODY` at 1 GiB for it. Duplicate lines in the source would make a count
  check miss (`sort -u <file> | wc -l` shows whether there are any). QLever is left out by
  default; `run_suite.sh updates <ds> qlever` runs it.

## Scale: a store larger than its memory limit (#218)

`suites/scale/run_scale.sh osm_benelux|osm_europe [engine...]` (or `bench.sh scale <dataset>`,
or the "Benchmarks (manual)" workflow with suite `scale` on `ccx43`, 64 GB): OSM data as
N-Triples, loaded and queried by TripleTrail (on its store on disk, with `--memory-limit 32G`) and
QLever (with the same 32G for its queries, `QLEVER_MEMORY`; GraphDB, when named, gets a 32g heap).

- Data: Geofabrik's `europe-latest.osm.pbf` (about 31 GB), downloaded on the server.
  `data/osm_scale.py` turns `osmium export` output into the shape of `osm_norway` (rail
  tracks, stations, land use and admin areas) plus buildings and highways, so the v2 OSM
  queries run unchanged. `osm_benelux` is a bounding box of Belgium, the Netherlands and
  Luxembourg (about 200M triples); `osm_europe` is all of Europe, cut at 1B triples
  (`SCALE_MAX_TRIPLES`).
- Queries: family `8 osm` (spatial joins) and `9 scale` (a group-by over every `rdf:type`,
  one over the building kinds, a label lookup, and a count of the named stations). TripleTrail
  runs with the result cache off, so warm runs are evaluated again.
- Writes: `updates.py` times 60 `INSERT DATA` commits of 10,000 triples each against TripleTrail
  after the queries (`updates-tripletrail.json`, p50 and p95). On `osm_benelux` the same commits
  run on the store in memory too (`updates-tripletrail-memory.json`), the reference for the
  acceptance criterion of #218 (p95 within 2x).
- Disk: a 360 GB server holds the extract, the N-Triples and one store at a time, so each is
  deleted once it is no longer needed (`SCALE_KEEP=1` keeps them).
