# Benchmark runs

Written by `bench/v2/runs.py index`. One row per run of `bench/v2/bench.sh` (the
workflow `Benchmarks`); each run's manifest is `<run>.json` here. Commit is the
TripleTrail commit the run measured. The result
folders (`../small`, `../bsbm`, ...) hold the latest run of each job; git history has
the older ones.

| Run | Started | Commit | Machine | Request | Jobs ok / failed / skipped | Time |
|---|---|---|---|---|---|---|
