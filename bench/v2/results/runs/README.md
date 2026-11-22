# Benchmark runs

Written by `bench/v2/runs.py index`. One row per run of `bench/v2/bench.sh` (the
workflow `Benchmarks`); each run's manifest is `<run>.json` here. Commit is the
TripleTrail commit the run measured. The result
folders (`../small`, `../bsbm`, ...) hold the latest run of each job; git history has
the older ones.

| Run | Started | Commit | Machine | Request | Jobs ok / failed / skipped | Time |
|---|---|---|---|---|---|---|
| [44998055578](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44998055578) | 2026-11-22T07:30 | `3a266437` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 1.3 h |
| [44938601022](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44938601022) | 2026-11-21T19:07 | `cee8c3c2` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 25 min |
| [44901267384](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44901267384) | 2026-11-21T12:00 | `cc8c2f43` | ccx43 | scale osm_europe | 1 / 0 / 0 | 2.6 h |
| [44484189037](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44484189037) | 2026-11-19T08:09 | `e36d3baa` | ccx43 | updates bsbm-28480 | 1 / 0 / 0 | 4 min |
| [44375757624](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44375757624) | 2026-11-18T19:07 | `e36d3baa` | ccx43 | all full | 11 / 1 / 0 (updates bsbm-28480) | 7.9 h |
