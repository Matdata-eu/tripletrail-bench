# Benchmark dashboard files

The CSV files here are what the [dashboard](https://matdata-eu.github.io/tripletrail-bench/)
reads, and `summary.json` holds the headline comparisons the TripleTrail website shows.
`bench/v2/dashboard.py` writes the CSV files from the results in `bench/v2/results`, and
`site/summary.py` writes `summary.json` from them; the collect job of the **Benchmarks**
workflow runs both, so every results pull request carries the files that match its results.
Merging it republishes the dashboard (`.github/workflows/pages.yml`).

| File | Columns | From |
|---|---|---|
| `summary.csv` | dataset, engine, geomean_ms, load_s, answered, timed_out, failed | `sparqloscope/*/*.results.yaml` |
| `categories.csv` | dataset, category, engine, ms | `sparqloscope/*/*.results.yaml` |
| `bsbm_qmph.csv` | scale, usecase, engine, qmph, note | `bsbm/bsbm-*/*.json` |
| `bsbm_aqet.csv` | scale, usecase, query, engine, ms | `bsbm/bsbm-*/*.json` |
| `trainmarks_load.csv` | scale, engine, load_s | `trainmarks/*/*.json` |
| `trainmarks_queries.csv` | scale, query, engine, warm_ms, cold_ms | `trainmarks/*/*.json` |
| `spatial_load.csv` | dataset, engine, load_s, disk_gib, triples | bench v2 `<dataset>/<engine>/load.json` |
| `spatial_queries.csv` | dataset, family, query, engine, status, cold_ms, p50_ms, p95_ms | bench v2 `<dataset>/<engine>/<query>.json` |
| `provenance.csv` | suite, dataset, machine, cpus, commit, date | `runs/*.json`, else the env files (no date) |
| `summary.json` | per suite and dataset: TripleTrail's number, each other engine's, and the speedup | the CSV files above |

By hand: `python3 bench/v2/dashboard.py && python3 site/summary.py bench/v2/results/dashboard`.

## For the website

The website shows a few headline numbers from a **tag** of this repository, so a new run never
changes a claim on it by itself. After reviewing a run, tag the results (`results-2026-12`,
for example) and point the website at

    https://raw.githubusercontent.com/Matdata-eu/tripletrail-bench/<tag>/bench/v2/results/dashboard/summary.json

with a link to the dashboard for everything else.
