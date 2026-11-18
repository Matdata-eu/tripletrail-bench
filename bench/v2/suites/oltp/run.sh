#!/bin/bash
# OLTP sweep against one engine that is already running and holds the data of `oltp gen`.
#   run.sh <engine> [scenario]      engine: tripletrail | oxigraph | jena
# Env: CLIENTS (default 1,2,4,8,16,32,64), WORKLOADS (default all), DUR (default 8s),
#      OUT (default ../../results/oltp/results.jsonl), TT_URL, OX_URL, JENA_URL.
# For TripleTrail's policy and rows scenarios, start the server with --auth-config policy.json or
# rows.json from this folder: the clients then send x-forwarded-user: team<0..15>.
# TripleTrail must run with TRIPLETRAIL_RESULT_CACHE_MB=0.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
E=$1; S=${2:-open}
CL=${CLIENTS:-1,2,4,8,16,32,64}
WL=${WORKLOADS:-point,lookup,hop,insert,edit,gsp,read90,rw50}
OUT=${OUT:-$HERE/../../results/oltp/results.jsonl}
BIN=$HERE/oltp; [ -x "$BIN" ] || (cd "$HERE" && go build -o oltp .)
H=()
case $E in
  tripletrail) B=${TT_URL:-http://127.0.0.1:7070/ds}; Q=$B/query; U=$B/update; G=$B/data
    [ "$S" != open ] && H=(-header "x-forwarded-user: team%d") ;;
  oxigraph) B=${OX_URL:-http://127.0.0.1:7878}; Q=$B/query; U=$B/update; G=$B/store ;;
  jena) B=${JENA_URL:-http://127.0.0.1:3030/ds}; Q=$B/query; U=$B/update; G=$B/data
    # The JVM needs warming up first.
    "$BIN" run -engine jena -scenario warm -query $Q -update $U -gsp $G -workloads read90 -clients 8 -duration 20s -warmup 1s >/dev/null ;;
  *) echo "unknown engine $E" >&2; exit 2 ;;
esac
"$BIN" run -engine "$E" -scenario "$S" -query $Q -update $U -gsp $G "${H[@]}" -workloads "$WL" \
  -clients "$CL" -duration "${DUR:-8s}" -warmup 2s -out "$OUT"
