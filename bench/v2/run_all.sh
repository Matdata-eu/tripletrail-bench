#!/bin/bash
# Run benchmark v2 for one dataset on several engines, one engine at a time.
#   run_all.sh <dataset> [engine...]        (default: postgis tripletrail qlever jena graphdb)
# Env: WARM_SCALE (multiplies the warm-run counts, default 1), ONLY (query/family filter for
# run.py --only), SKIP_LOAD=1 (reuse the loaded stores), DROP_AFTER=1 (delete an engine's store
# after its run, to save disk).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/work}
DS=$1; shift
ENGINES=${*:-postgis tripletrail qlever jena graphdb}
ALL="postgis tripletrail tripletrail-1t qlever jena graphdb"
mkdir -p "$HERE/results/$DS"
python3 "$HERE/env.py" >"$HERE/results/$DS/env.json"
for e in $ENGINES; do
  for x in $ALL; do "$HERE/engines/$x.sh" stop >/dev/null 2>&1; done
  sync
  echo "=== $e on $DS ($(date -Is))"
  [ "$e" = postgis ] && "$HERE/engines/postgis.sh" start
  if [ -z "${SKIP_LOAD:-}" ]; then
    python3 "$HERE/run.py" load --engine "$e" --dataset "$DS" || { echo "load failed for $e"; continue; }
  fi
  python3 "$HERE/run.py" query --engine "$e" --dataset "$DS" --warm-scale "${WARM_SCALE:-1}" ${ONLY:+--only "$ONLY"}
  "$HERE/engines/$e.sh" stop
  if [ -n "${DROP_AFTER:-}" ]; then
    case $e in
      postgis) "$HERE/engines/postgis.sh" start && psql "${PG_DSN_BASE:-host=/var/run/postgresql user=postgres} dbname=postgres" -qc "DROP DATABASE IF EXISTS rinf_$DS" && "$HERE/engines/postgis.sh" stop ;;
      tripletrail-*) rm -rf "${W:?}/tripletrail/$DS" ;;  # tripletrail's store (engines/tripletrail-1t.sh)
      *) rm -rf "${W:?}/$e/$DS" ;;
    esac
  fi
done
# Again now that the engines' images are pulled (the first capture runs before, on a fresh server).
python3 "$HERE/env.py" >"$HERE/results/$DS/env.json"
echo "=== done ($(date -Is))"
