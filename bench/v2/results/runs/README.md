# Benchmark runs

Written by `bench/v2/runs.py index`. One row per run of `bench/v2/bench.sh` (the
workflow `Benchmarks`); each run's manifest is `<run>.json` here. Commit is the
TripleTrail commit the run measured. The result
folders (`../small`, `../bsbm`, ...) hold the latest run of each job; git history has
the older ones.

| Run | Started | Commit | Machine | Request | Jobs ok / failed / skipped | Time |
|---|---|---|---|---|---|---|
| [44484189037](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44484189037) | 2026-11-19T08:09 | `e36d3baa` | ccx43 | updates bsbm-28480 | 1 / 0 / 0 | 4 min |
| [44375757624](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44375757624) | 2026-11-18T19:07 | `e36d3baa` | ccx43 | all full | 11 / 1 / 0 (updates bsbm-28480) | 7.9 h |
