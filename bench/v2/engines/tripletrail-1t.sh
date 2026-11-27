#!/bin/bash
# TripleTrail with one thread per query (`serve --query-threads 1`), for comparing a query on
# one core with the same query on all of them (tripletrail#4). Same binary, store and port as
# tripletrail.sh, which does the work: a run of both engines loads the store once for each.
export TRIPLETRAIL_SERVE_ARGS="${TRIPLETRAIL_SERVE_ARGS:-} --query-threads 1"
exec "$(dirname "$0")/tripletrail.sh" "$@"
