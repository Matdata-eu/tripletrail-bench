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
| `rinfshapes_queries.csv` | dataset, shape, query, control_of, engine, status, rows_ms, count_ms, rows, title | `rinfshapes/*/*.json` and `suites/rinfshapes/queries.py` |
| `provenance.csv` | suite, dataset, machine, cpus, commit, date, engines | `runs/*.json`: per engine the latest run that measured it, one row per run; else the env files (no date, no engines) |
| `summary.json` | per suite and dataset: TripleTrail's number, each other engine's, and the speedup | the CSV files above |

By hand: `python3 bench/v2/dashboard.py && python3 site/summary.py bench/v2/results/dashboard`.

## Earlier results: the version picker

A results pull request replaces these files, so the dashboard's **TripleTrail version** picker
goes back in git instead: the Pages build (`site/build.py --history`) writes a snapshot of this
folder for every earlier commit on main that changed it, under `data/v/<commit>/`, and
`data/versions.json` lists them, newest first. Each is labelled with its date and the TripleTrail
release before the commit of its newest run (`v0.1.0+22`: 22 commits after v0.1.0), and is
starred when a `results-*` tag points at it. `?v=` in the page's URL takes a snapshot id, a
commit of this repository or a tag (`?v=results-2026-12`); without it the page shows the latest
results. Each snapshot's provenance is rewritten from its run manifests, so it names every run
its numbers come from the same way the latest does.

To try it locally (from the repository's root, with full history):

    git clone --bare --filter=blob:none https://github.com/Matdata-eu/tripletrail.git /tmp/core.git
    python3 site/build.py bench/v2/results _site --history --core /tmp/core.git
    python3 -m http.server -d _site

## For the website

The website shows a few headline numbers from a **tag** of this repository, so a new run never
changes a claim on it by itself. After reviewing a run, tag the results (`results-2026-12`,
for example; pushing the tag stars that snapshot in the dashboard's version picker) and point
the website at

    https://raw.githubusercontent.com/Matdata-eu/tripletrail-bench/<tag>/bench/v2/results/dashboard/summary.json

with a link to the dashboard for everything else.
