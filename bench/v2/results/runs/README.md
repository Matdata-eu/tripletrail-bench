# Benchmark runs

Written by `bench/v2/runs.py index`. One row per run of `bench/v2/bench.sh` (the
workflow `Benchmarks`); each run's manifest is `<run>.json` here. Commit is the
TripleTrail commit the run measured. The result
folders (`../small`, `../bsbm`, ...) hold the latest run of each job; git history has
the older ones.

| Run | Started | Commit | Machine | Request | Jobs ok / failed / skipped | Time |
|---|---|---|---|---|---|---|
| [45969184263](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45969184263) | 2026-11-27T09:00 | `13e940f6` | ccx43 | scale osm_europe | 1 / 0 / 0 | 3.2 h |
| [45883044532](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45883044532) | 2026-11-26T19:28 | `9f32d6ce` | ccx43 | all shacl-ml | 0 / 2 / 0 (shacl rinf-0080, shacl rinf-all) | 10.0 h |
| [45816390204](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45816390204) | 2026-11-26T12:12 | `99d1a36b` | ccx43 | all shacl | 0 / 1 / 0 (shacl rinf-0076) | 2.2 h |
| [45275973194](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45275973194) | 2026-11-23T22:10 | `0f9b0a14` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 22 min |
| [45127025267](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45127025267) | 2026-11-23T06:58 | `44f5dcd2` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 22 min |
| [45065789620](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45065789620) | 2026-11-22T20:26 | `a9aae028` | ccx43 | all full | 12 / 0 / 0 | 7.7 h |
| [45065786454](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45065786454) | 2026-11-22T20:26 | `a9aae028` | ccx43 | scale osm_europe | 1 / 0 / 0 | 1.7 h |
| [45004762850](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/45004762850) | 2026-11-22T08:58 | `3a266437` | ccx43 | scale osm_europe | 1 / 0 / 0 | 4.9 h |
| [44958878631](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44958878631) | 2026-11-21T22:58 | `5d76345f` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 1.3 h |
| [44938601022](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44938601022) | 2026-11-21T19:07 | `cee8c3c2` | ccx43 | scale osm_benelux | 1 / 0 / 0 | 25 min |
| [44901267384](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44901267384) | 2026-11-21T12:00 | `cc8c2f43` | ccx43 | scale osm_europe | 1 / 0 / 0 | 2.6 h |
| [44484189037](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44484189037) | 2026-11-19T08:09 | `e36d3baa` | ccx43 | updates bsbm-28480 | 1 / 0 / 0 | 4 min |
| [44375757624](https://github.com/Matdata-eu/tripletrail-bench/actions/runs/44375757624) | 2026-11-18T19:07 | `e36d3baa` | ccx43 | all full | 11 / 1 / 0 (updates bsbm-28480) | 7.9 h |
