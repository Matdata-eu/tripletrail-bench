# RINF query-shape suite

The query shapes that RINF-atlas's pages and other map clients send, on real railway data at
full EU size: facets over a big class, top-k over a star, stars with combined filters, chains,
wide tables with OPTIONALs, anti-joins (tripletrail-bench #64) and "valid on a day" over
`era:validity` (tripletrail #311). It started from a research
spike on 59 M triples (tripletrail #297, #298), where a top 20 with labels took 53 ms against 8 ms
for the same sort on its predicate alone, and a facet count spent two thirds of its time in
GROUP BY. On 12 M triples the same queries looked fine, and BSBM and Sparqloscope have few
queries of these shapes.

```bash
bench/v2/suites/run_suite.sh rinfshapes rinf-all tripletrail oxigraph qlever jena
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py queries              # the query ids
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py queries topk-speed-label   # its two forms
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py run --engine tripletrail-spareval --skip-load --shape valid
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py counts                      # how RINF writes validity
python3 bench/v2/suites/rinfshapes/test_queries.py                       # answers on testdata/
```

- **Data**: `rinf-all`, every graph of ERA's RINF endpoint (about 43 M triples), or one graph
  `rinf-<code>`. `suites/data/fetch_rinf.py` fetches it into `$BENCH_WORK/data` on first use; it
  is never committed. `run_rinfshapes.py prepare` then writes the copy every engine loads,
  `rinfshapes-<code>.nt`, without the triples that stop some engine's bulk load: lines over
  4 MiB (drawings as WKT, too long for Oxigraph's and QLever's parsers), numbers that are not
  numbers (`"N"^^xsd:integer`), and geometries Jena's spatial index refuses (`"NYA"` as
  `geo:asWKT`, coordinates such as `+-100000000`, LINESTRINGs of fewer than 2 distinct points).
  On `rinf-all` that is about 8,600 of 42.9 M triples; the counts per reason are in
  `rinfshapes-<code>.meta.json` and in each engine's result file. QLever loads without its
  geometry preprocessing (`QLEVER_NO_GEO=1`), as no query is spatial.
- **Queries** (`queries.py`): 21 queries in 8 shapes. Each has a **rows** form, the answer as a
  client reads it, and a **count** form, `SELECT (COUNT(*) AS ?solutions)` over the same
  pattern (over the rows form as a subquery when it has a GROUP BY, ORDER BY or LIMIT). The
  share of count time in rows time tells the join's cost from the cost of writing the rows.
  The **ablation controls** repeat each top-k and facet query with patterns taken out: the sort
  on its predicate alone, the join without its GROUP BY, the facet without its class, and the
  validity join without its day filter.
- **Valid on a day** (`valid`): the sections of line, operational points, running tracks, and
  anything, valid on 2026-11-28, written as a client writes it today, without temporal support in
  the engine: `era:validity/time:hasBeginning/(time:inXSDDate|time:inXSDDateTimeStamp)`, the same
  for the end, `!BOUND` for an open end, and casts so that ERA's `xsd:date` and Bane NOR's
  `xsd:dateTimeStamp` compare as `xsd:dateTime` (a date is midnight UTC; the end day is still
  valid). They are the baseline that tripletrail #303 is measured against. `counts` writes, per
  class, the entities with a validity, their writings, how many writings each has and how many
  are valid on that day, to `results/rinfshapes/<dataset>/validity-counts.json`.
- **Runs**: per query and form, one cold run, 2 warm-ups and 7 timed runs (`--warm`), wall-clock
  at the client over HTTP with every row read; the median is reported. TripleTrail's result
  cache is off and QLever's is cleared before each run, as in the other suites.
- **Checks**: the report flags a query whose row count differs between engines. A count form
  whose number differs from its rows form's row count is recorded with the status `forms differ`
  (the run goes on, and the times are kept), and the report notes it. `test_queries.py` checks
  every query's rows and count on a small hand-made extract (`testdata/extract.ttl`) with
  `tripletrail query`.
- **Engines**: tripletrail, oxigraph, qlever, jena and graphdb by default. `tripletrail-ids` and
  `tripletrail-spareval` run TripleTrail with one executor as the default, on the same store
  (`--skip-load`).
- **Output**: `results/rinfshapes/<dataset>/<engine>.json` and `results/rinfshapes/report.md`.
- **On a rented server**: `bench/v2/bench.sh rinfshapes rinf-all`, or from GitHub, Actions →
  **Benchmarks** with suite `rinfshapes` and dataset `rinf-all` (or `rinf-<code>`), after
  approval. The results come back in the run's results commit, as for the other suites.

Not yet: scaled copies of `rinf-all` (instance IRIs copied 2 and 4 times, with concepts and
vocabulary shared) to show how each shape grows with size.
