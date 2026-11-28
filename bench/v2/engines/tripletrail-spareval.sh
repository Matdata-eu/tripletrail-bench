#!/bin/bash
# TripleTrail with the evaluator (spareval) as the server's default executor (`serve --executor
# spareval`), to compare it with the id-column executor, the default, in the same run. Same binary,
# store and port as tripletrail.sh, which does the work.
export TRIPLETRAIL_SERVE_ARGS="${TRIPLETRAIL_SERVE_ARGS:-} --executor spareval"
exec "$(dirname "$0")/tripletrail.sh" "$@"
