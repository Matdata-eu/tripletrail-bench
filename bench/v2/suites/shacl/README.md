# SHACL suite

SHACL validation (Core and SHACL-SPARQL) and, later, SHACL-AF rules on real railway data: RINF, the EU
Register of Infrastructure, against the shapes the EU Agency for Railways (ERA) publishes for it.
Tracker: Matdata-eu/tripletrail-bench#29 (phase 0), #30 to #34 (the suite).

## Phase 0: what each engine supports

Phase 0 answers two questions before a suite is built: which engines can run the ERA shapes at
all, and how long one country takes. It runs in a cloud session, never in CI.

```bash
export BENCH_WORK=/path/with/space          # data and reports; never in git
export JENA_HOME=/path/to/apache-jena-6.2.0 TOPBRAID_HOME=/path/to/shacl-1.5.0
export TRIPLETRAIL_BIN=/path/to/core/target/release/tripletrail
pip install rdflib pyshacl==0.30.1                     # rdflib reads every engine's report
(cd bench/v2/suites/shacl/rdf4j && mvn -q package)   # RDF4J ShaclSail as a command

bench/v2/suites/data/fetch_rinf.py 0076                # RINF Norway, ~1.6 M triples
bench/v2/suites/shacl/fetch_shapes.sh                  # ERA shapes, ontology, code lists (pinned)
cat $BENCH_WORK/data/rinf-0076.nt $BENCH_WORK/data/shacl/lookup.nt >$BENCH_WORK/data/shacl/no.nt

bench/v2/suites/shacl/probes.py $BENCH_WORK/shacl/probes.json   # feature probes, all engines
bench/v2/suites/shacl/run_phase0.py $BENCH_WORK/data/shacl/no.nt \
  $BENCH_WORK/data/shacl/era-rinf-shapes.ttl $BENCH_WORK/shacl    # the ERA shapes, all engines
bench/v2/suites/shacl/report.py bench/v2/results/shacl/phase0     # after copying the JSON files
```

- **Engines**: TripleTrail (`tripletrail validate`, `tripletrail infer`), Apache Jena
  (`shacl validate`), TopBraid SHACL API (`shaclvalidate.sh`, `shaclinfer.sh`), pySHACL (`-a`,
  SHACL-AF on), RDF4J ShaclSail (`rdf4j/`, a memory store, bulk validation of one transaction)
  and GraphDB (`graphdb_validate.sh`: the shapes are added to a SHACL repository that holds the
  data). maplib's open build has no SHACL (its `validate` asks to contact Data Treehouse), and
  Oxigraph, QLever and PostGIS have none, so they stay out.
- **Feature probes** (`features/`): five validation features and the AF rules, each a small
  shapes file on `features/data.ttl` with the number of results it should give in its first
  comment. They are ours.
- **Data**: the RINF graph with the ERA ontology and every SKOS code list appended, since 82 of
  the SPARQL constraints read `skos:` concepts. Every engine gets the same single file.
- **Same results**: a report is reduced to sorted keys (focus node, path, constraint component,
  severity; a blank-node path is `_:`), and their SHA-256 is compared with Jena's. Engines name
  blank property shapes differently, so the shape is not part of the key.
- **Time and memory**: wall time of the whole command (parsing included, JVM start included) and
  the peak resident memory of its process tree (for GraphDB, its container's cgroup peak).

## The validation suite

`run_shacl.py` runs the ERA shapes in three profiles on one RINF dataset with every engine, through
the same entry point as the other suites:

```bash
bench/v2/suites/run_suite.sh shacl rinf-0076            # step S, Norway, all engines
bench/v2/bench.sh all shacl                             # steps S, M (Germany) and L (all of RINF)
```

On the Benchmarks workflow: suite `all`, dataset `shacl` (one server for the three steps), or suite
`shacl` with dataset `rinf-<code>` or `rinf-all`.

- **Engines** are set up by `run_shacl.py setup` into `$BENCH_WORK/shacl-engines`: Jena and TopBraid
  downloaded and checked against their SHA-256, rdflib and pySHACL in a venv, and the RDF4J jar
  built in a Maven container (the bench server has Java 21 but no Maven). GraphDB is its Docker
  image. TripleTrail is the core build of the run. `JAVA_HEAP` (48g) sets the JVMs' heap and
  `GRAPHDB_HEAP` GraphDB's. `JAVA_STACK` (1g) sets every JVM's thread stack: Java's regular
  expressions recurse once per repeated character, and with the default 1 MB a `sh:pattern` on a
  long literal in all of RINF ends in a `StackOverflowError` in Jena, TopBraid and RDF4J alike.
- **Profiles**, made from the pinned shapes at run time: `core` drops every SPARQL constraint and
  SPARQL target (SHACL Core only); `era-local` unlinks the 5 SPARQL constraints and 2 property
  shapes ERA marks `era:scope "global"`, which need the whole network; `era` is the shapes as
  published.
- **Runs**: a run under 300 s (`SHACL_REPEAT_BELOW`) is repeated twice more and the median kept.
  `SHACL_TIMEOUT` (3,600 s) bounds a run; a timeout or crash is the result, and an engine that
  times out skips the dataset's later profiles, and one that timed out or failed on a profile of
  a smaller dataset skips that profile on the larger ones (so pySHACL and RDF4J do not spend hours
  on M and L after failing on S). TripleTrail, GraphDB and RDF4J also log their
  validation time apart from loading.
- **Agreement**: the result keys of each engine are compared with TopBraid's and with the
  majority's (the hash most engines share). An engine can give several results with one key
  (another value or message for the same focus node and path); the report then shows the distinct
  keys beside the results. TripleTrail gives identical results once (tripletrail#91, as pySHACL
  does), while Jena and TopBraid give one per solution of a SPARQL constraint: on Germany
  a `UNION` of `era:isPartOf` and `era:hasPart` finds the same track twice, so Jena and TopBraid
  report 947,629 results where TripleTrail reports 894,300, with the same distinct results.
- **Injected violations** (`inject.py`, tracker #31): real RINF data already fails many ERA
  shapes, which measures speed on realistic reports but not whether an engine misses violations.
  `run_shacl.py inject --dataset D` (by `run_suite.sh` on the datasets in `SHACL_INJECT`, Norway
  by default) draws 1% of the instances of the classes the `era-local` shapes target
  (`SHACL_INJECT_RATE`, seed `SHACL_INJECT_SEED`, 31) and gives each one mutation its class's
  shapes and its own triples allow, the kinds in turn: a value with the wrong datatype
  (`xsd:string`), every value of a required property removed, a code-list value replaced by an IRI
  in no SKOS scheme, a value its `sh:pattern` rejects, and a second value where `sh:maxCount 1`
  applies. Each engine validates the data before and after with `era-local`. Recall is the share
  of injected violations (focus node, path, constraint component) it reports; precision the share
  of its new results that are on a node the mutations touched: the mutated node, a node a removed
  triple pointed to, or one up to three links before the mutated node, which inverse and sequence
  paths read. A mutation can break more than the one constraint it targets, so precision does not
  ask for the expected results only. The seed and the counts by kind go into
  `results/shacl/<dataset>/injected/manifest.json`; the mutated data and the expected violations
  hold RINF values and stay in the work directory.
- **Errors**: a failed engine's error is the class of its first exception (or our script's own
  message), never the exception's message, which can quote RINF values.
- **Output**: `results/shacl/<dataset>/<profile>/<engine>.json`, `results/shacl/<dataset>/data.json`
  and `results/shacl/report.md`. Reports are counted and deleted in the work directory.

Not yet measured (tracker #30): the ten slowest shapes per engine, and the cost of revalidating
after inserting or deleting 1,000 triples in a store engine.

## Licences

- **RINF data**: ERA publishes no licence for it. It is fetched at run time from ERA's public
  endpoint and never committed or released. Results hold only timings, counts and hashes, never
  reports or inferred triples.
- **ERA shapes, ontology and code lists**: EUPL-1.2, from the
  [ERA ontology repository](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology),
  fetched at run time, pinned to a commit and the shapes' SHA-256 (`fetch_shapes.sh`).
- **Engines**: downloaded or installed at run time; none is redistributed.
