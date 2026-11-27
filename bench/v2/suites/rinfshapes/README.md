# RINF query-shape suite

The query shapes that RINF-atlas's pages and other map clients send, on real railway data at
full EU size: facets over a big class, top-k over a star, stars with combined filters, chains,
wide tables with OPTIONALs and anti-joins (tripletrail-bench #64). It started from a research
spike on 59 M triples (tripletrail #297, #298), where a top 20 with labels took 53 ms against 8 ms
for the same sort on its predicate alone, and a facet count spent two thirds of its time in
GROUP BY. On 12 M triples the same queries looked fine, and BSBM and Sparqloscope have few
queries of these shapes.

```bash
bench/v2/suites/run_suite.sh rinfshapes rinf-all tripletrail oxigraph qlever jena
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py queries              # the query ids
python3 bench/v2/suites/rinfshapes/run_rinfshapes.py queries topk-speed-label   # its two forms
python3 bench/v2/suites/rinfshapes/test_queries.py                       # answers on testdata/
```

- **Data**: `rinf-all`, every graph of ERA's RINF endpoint (about 43 M triples), or one graph
  `rinf-<code>`. `suites/data/fetch_rinf.py` fetches it into `$BENCH_WORK/data` on first use; it
  is never committed. `run_rinfshapes.py prepare` then writes the copy every engine loads,
  `rinfshapes-<code>.nt`, without the few triples that stop some engine's bulk load: lines over
  4 MiB (drawings as WKT, too long for Oxigraph's and QLever's parsers), numbers that are not
  numbers (`"N"^^xsd:integer`), and geometries Jena's spatial index refuses (`"NYA"` as
  `geo:asWKT`, a LINESTRING of one point). On `rinf-all` that is about 2,400 of 42.9 M triples,
  none of them read by the queries; the counts per reason are in `rinfshapes-<code>.meta.json`
  and in each engine's result file.
- **Queries** (`queries.py`): 16 queries in 7 shapes. Each has a **rows** form, the answer as a
  client reads it, and a **count** form, `SELECT (COUNT(*) AS ?solutions)` over the same
  pattern (over the rows form as a subquery when it has a GROUP BY, ORDER BY or LIMIT). The
  share of count time in rows time tells the join's cost from the cost of writing the rows.
  The **ablation controls** repeat each top-k and facet query with patterns taken out: the sort
  on its predicate alone, the join without its GROUP BY, the facet without its class.
- **Runs**: per query and form, one cold run, 2 warm-ups and 7 timed runs (`--warm`), wall-clock
  at the client over HTTP with every row read; the median is reported. TripleTrail's result
  cache is off and QLever's is cleared before each run, as in the other suites.
- **Checks**: the report flags a query whose row count differs between engines, and a count form
  whose number differs from its rows form's row count. `test_queries.py` checks every query's
  rows and count on a small hand-made extract (`testdata/extract.ttl`) with `tripletrail query`.
- **Engines**: tripletrail, oxigraph, qlever, jena and graphdb by default.
- **Output**: `results/rinfshapes/<dataset>/<engine>.json` and `results/rinfshapes/report.md`.

Not yet: scaled copies of `rinf-all` (instance IRIs copied 2 and 4 times, with concepts and
vocabulary shared) to show how each shape grows with size.
