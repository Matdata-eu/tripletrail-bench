#!/bin/bash
# TripleTrail with the id-column executor as the server's default (`serve --executor ids`), for
# comparing it with the default executor in the same run. Same binary, store and port as
# tripletrail.sh, which does the work: a run of both engines loads the store once for each.
export TRIPLETRAIL_SERVE_ARGS="${TRIPLETRAIL_SERVE_ARGS:-} --executor ids"
exec "$(dirname "$0")/tripletrail.sh" "$@"
