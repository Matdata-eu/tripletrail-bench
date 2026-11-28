#!/bin/bash
# Run benchmarks at one commit, on one machine, one after the other, with one run manifest.
#   bench.sh all <profile> [engine...]      every job of profiles/<profile>.txt (full | scale | dashboard | nuc)
#   bench.sh <suite> <dataset> [engine...]  one job: v2 small|large|osm_norway, geographica all,
#                                            bsbm <products>, sparqloscope <dataset>,
#                                            trainmarks <scale>, updates <dataset>,
#                                            shacl rinf-<code>|rinf-all,
#                                            rinfshapes rinf-all|rinf-<code>,
#                                            scale osm_benelux|osm_europe|osm_planet,
#                                            railpack (only with the enterprise repository's suite and packs)
# Engines: none given (or "default") = each suite's own default set; otherwise each job runs the
# given engines it supports (v2: postgis tripletrail qlever jena graphdb; geographica: tripletrail
# qlever jena graphdb; bsbm, sparqloscope and trainmarks: tripletrail oxigraph qlever jena graphdb
# maplib; rinfshapes: tripletrail oxigraph qlever jena graphdb; tripletrail-1t, one thread per query, in v2 and those three, and tripletrail-ids, the
# id-column executor, in those three, only when named).
# A job whose inputs or tools are missing is skipped with the reason, not failed: osm_norway and
# geographica need their inputs (data/fetch_inputs.sh, from the bench-data release), osm_norway
# needs osmium, postgis needs psql and python3-psycopg2.
# The manifest results/runs/<run id>.json (commit, machine, per-job status and duration; the
# GitHub run id, or local-<time>) is rewritten after every job. Exit status 1 if a job failed.
# Env: BENCH_WORK, BENCH_MACHINE (label in the manifest), DROP_AFTER, plus those of run_all.sh
# and suites/run_suite.sh.
set -uo pipefail
V2=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$V2/work}
export BENCH_WORK=$W
SUITE=$1; DS=$2; shift 2
REQ=${*:-default}; [ "$REQ" = default ] && REQ=""
RUN=${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%S)}
MANIFEST=$V2/results/runs/$RUN.json
mkdir -p "$W/data" "$V2/results/runs"

if [ "$SUITE" = all ]; then
  [ -f "$V2/profiles/$DS.txt" ] || { echo "no profile $V2/profiles/$DS.txt" >&2; exit 2; }
  JOBS=$(grep -v '^\s*\(#\|$\)' "$V2/profiles/$DS.txt")
else
  JOBS="$SUITE $DS"
fi
python3 "$V2/runs.py" start "$MANIFEST" --run "$RUN" --request "$SUITE $DS" --engines "${REQ:-default}" \
  --machine "${BENCH_MACHINE:-$(hostname)}"

# engines <suite>: the engines of this job (the requested ones the suite supports).
engines() {
  local all extra=""
  case $1 in
    v2) all="postgis tripletrail qlever jena graphdb"; extra="tripletrail-1t" ;;
    geographica) all="tripletrail qlever jena graphdb" ;;
    # GraphDB runs the scale suite only when asked for by name (its own paid run).
    scale) all="tripletrail qlever"; extra="graphdb" ;;
    railpack) all="tripletrail" ;;
    updates) all="tripletrail oxigraph jena graphdb" ;;
    shacl) all="tripletrail jena topbraid graphdb rdf4j pyshacl" ;;
    rinfshapes) all="tripletrail oxigraph qlever jena graphdb" ;;
    *) all="tripletrail oxigraph qlever jena graphdb maplib" ;;
  esac
  # tripletrail-ids (the id-column executor as the default) and tripletrail-1t (one thread per
  # query) run only when asked for by name.
  case $1 in bsbm|sparqloscope|trainmarks|updates) extra="$extra tripletrail-ids tripletrail-1t" ;; esac
  # rinfshapes: the evaluator as the default too (tripletrail-spareval), for its valid-day queries.
  case $1 in rinfshapes) extra="$extra tripletrail-ids tripletrail-spareval" ;; esac
  [ -z "$REQ" ] && { echo "$all"; return; }
  local out=""
  for e in $all $extra; do case " $REQ " in *" $e "*) out="$out $e" ;; esac; done
  echo "${out# }"
}

# BENCH_PUSH_PARTIAL=1 (the workflow): after each job, the results so far are committed to the
# branch bench-partial/<run> and pushed, so a server lost later in a long run keeps them; the
# collect job takes them from there when the run's artifact is missing.
push_partial() {
  local repo idx tree parent c
  repo=$(cd "$V2/../.." && pwd)
  idx=$(mktemp -u)
  # A commit made from a temporary index: the checkout's HEAD and index stay as they were, so
  # env.py still records the harness commit the run measured.
  if c=$(cd "$repo" && export GIT_INDEX_FILE="$idx" &&
      git read-tree HEAD && git add bench/v2/results && tree=$(git write-tree) &&
      parent=${PARTIAL:-$(git rev-parse HEAD)} &&
      if [ "$tree" = "$(git rev-parse "$parent^{tree}")" ]; then echo "$parent"; else
        git -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
          commit-tree "$tree" -p "$parent" -m "chore(bench): partial results of run $RUN after $1"; fi) &&
     (cd "$repo" && git push -q origin "$c:refs/heads/bench-partial/$RUN"); then
    PARTIAL=$c
  else
    echo "::warning::results after $1 not pushed to bench-partial/$RUN"
  fi
  rm -f "$idx"
}

PARTIAL=""
PG_STARTED=""; PG_WHY=""
# PostGIS: the local cluster when there is one, otherwise a container like docker-compose.yml's
# (started once per run, removed at the end). On failure the reason is in PG_WHY.
postgis_ready() {
  PG_WHY=""
  command -v psql >/dev/null || { PG_WHY="psql is missing (apt-get install postgresql-client)"; return 1; }
  python3 -c 'import psycopg2' 2>/dev/null || { PG_WHY="psycopg2 is missing (apt-get install python3-psycopg2)"; return 1; }
  [ -n "${PG_DSN_BASE:-}" ] && return 0
  # A local cluster (postgis.sh drives it with pg_ctlcluster), unless POSTGIS_CONTAINER=1.
  [ -z "${POSTGIS_CONTAINER:-}" ] && [ -d "/etc/postgresql/${PGVER:-16}/main" ] && return 0
  local img=${POSTGIS_IMAGE:-mirror.gcr.io/pgrouting/pgrouting:16-3.4-3.6.1}
  docker image inspect "$img" >/dev/null 2>&1 || docker pull -q "$img" >/dev/null 2>&1 \
    || { img=docker.io/${img#mirror.gcr.io/}; docker pull -q "$img" >/dev/null 2>&1; } \
    || { PG_WHY="could not pull the PostGIS image"; return 1; }
  docker rm -f bench-postgis >/dev/null 2>&1
  docker volume rm bench-postgis >/dev/null 2>&1
  docker run -d --name bench-postgis -e POSTGRES_PASSWORD=bench -p 127.0.0.1:5432:5432 \
    --shm-size "${PG_SHM:-6g}" -v bench-postgis:/var/lib/postgresql/data "$img" \
    postgres -c shared_buffers="${PG_SHARED_BUFFERS:-4GB}" -c work_mem=256MB -c maintenance_work_mem=1GB \
    -c effective_cache_size="${PG_EFFECTIVE_CACHE:-10GB}" -c max_parallel_workers_per_gather=4 \
    -c max_worker_processes=8 -c max_parallel_workers=4 -c random_page_cost=1.1 -c jit=off \
    -c synchronous_commit=off -c max_wal_size=8GB >/dev/null || { PG_WHY="could not start PostGIS"; return 1; }
  export PG_DSN_BASE="host=127.0.0.1 port=5432 user=postgres password=bench" PG_CONTAINER=bench-postgis
  PG_STARTED=1
  for _ in $(seq 1 120); do psql "$PG_DSN_BASE dbname=postgres" -Atc 'SELECT 1' >/dev/null 2>&1 && return 0; sleep 1; done
  PG_WHY="PostGIS did not come up"; return 1
}
cleanup() {
  [ -n "$PG_STARTED" ] && { docker rm -f bench-postgis >/dev/null 2>&1; docker volume rm bench-postgis >/dev/null 2>&1; }
}
trap cleanup EXIT

# v2 <dataset> <engines>: data, every engine, correctness against PostGIS, report.
run_v2() {
  local ds=$1; shift
  case $ds in
    small) [ -f "$W/data/small.nt" ] || python3 "$V2/data/gen_rinf_synth.py" --h 24 --v 24 --k 20 --regions 3 --seed 42 --out "$W/data/small.nt" || return 1 ;;
    large) [ -f "$W/data/large.nt" ] || python3 "$V2/data/gen_rinf_synth.py" --h 88 --v 88 --k 20 --regions 5 --seed 42 --out "$W/data/large.nt" || return 1 ;;
    osm_norway)
      if [ ! -f "$W/data/osm_norway.nt" ]; then
        cp "$W/inputs/norway-rail-landuse-admin.osm.pbf" "$W/data/osm_norway.osm.pbf" || return 1
        python3 "$V2/data/osm_extract.py" "$W/data/osm_norway.osm.pbf" --out "$W/data/osm_norway" || return 1
      fi ;;
  esac
  "$V2/run_all.sh" "$ds" "$@" || return 1
  python3 "$V2/compare.py" "$V2/results/$ds" >/dev/null || return 1
  python3 "$V2/report.py" "$V2/results/$ds" >/dev/null
}

# geographica <engines>: prepare once, then load, run (from scratch) and stop each engine.
run_geographica() {
  local g2=$W/inputs/geographica2 failed=0
  mkdir -p "$V2/results/geographica/load"
  [ -f "$W/data/geographica.nq" ] || python3 "$V2/geographica/run_geographica.py" prepare "$g2" || return 1
  for e in "$@"; do
    for x in postgis tripletrail oxigraph qlever jena graphdb; do "$V2/engines/$x.sh" stop >/dev/null 2>&1; done
    echo "=== geographica on $e ($(date -Is))"
    rm -f "$V2/results/geographica/$e.json"
    if "$V2/engines/$e.sh" load geographica >"$W/geographica-$e.load.out"; then
      tail -n 1 "$W/geographica-$e.load.out" >"$V2/results/geographica/load/$e.json"
      python3 "$V2/geographica/run_geographica.py" run --engine "$e" "$g2" || { echo "!!! geographica failed on $e"; failed=1; }
    else
      echo "!!! geographica load failed on $e"; failed=1
    fi
    "$V2/engines/$e.sh" stop >/dev/null 2>&1
    [ -n "${DROP_AFTER:-}" ] && rm -rf "${W:?}/$e/geographica"
  done
  python3 "$V2/geographica/run_geographica.py" report >/dev/null || return 1
  return $failed
}

FAILED=0
while read -r suite ds extra; do
  [ -n "$suite" ] || continue
  es=$(engines "$suite")
  # SHACL_SKIP=<engines> on a profile line leaves those engines out of the job.
  for kv in $extra; do
    case $kv in SHACL_SKIP=*) for x in ${kv#SHACL_SKIP=}; do es=$(echo " $es " | sed "s/ $x / /; s/^ *//; s/ *$//"); done ;; esac
  done
  LOG=$V2/results/runs/$RUN-$suite-$ds.log
  skip=""; note=""
  case $suite in
    v2)
      [ "$ds" = osm_norway ] && ! command -v osmium >/dev/null && skip="osmium is missing (apt-get install osmium-tool)"
      [ "$ds" = osm_norway ] && [ ! -f "$W/inputs/norway-rail-landuse-admin.osm.pbf" ] && skip="input norway-rail-landuse-admin.osm.pbf is missing (data/fetch_inputs.sh)"
      if [ -z "$skip" ] && [[ " $es " == *" postgis "* ]]; then
        if ! postgis_ready; then
          note="postgis left out: $PG_WHY"; echo "::warning::v2 $ds: $note"; es=$(echo " $es " | sed 's/ postgis / /; s/^ //; s/ $//')
        fi
      fi ;;
    geographica)
      [ -d "$W/inputs/geographica2/datasets" ] || skip="input geographica2/ is missing (data/fetch_inputs.sh)" ;;
    bsbm|sparqloscope|trainmarks|updates|shacl|rinfshapes) ;;
    railpack)
      [ -d "$V2/../../packs/rail-era" ] && [ -f "$V2/suites/railpack/run_railpack.py" ] \
        || skip="the rail pack (packs/rail-era) is not in this tree" ;;
    scale) command -v osmium >/dev/null || skip="osmium is missing (apt-get install osmium-tool)" ;;
    *) skip="unknown suite $suite" ;;
  esac
  [ -z "$skip" ] && [ -z "$es" ] && skip="none of the requested engines runs this suite"
  if [ -n "$skip" ]; then
    echo "--- skip $suite $ds: $skip"
    python3 "$V2/runs.py" job "$MANIFEST" --suite "$suite" --dataset "$ds" --engines "$es" --status skipped --reason "$skip" --seconds 0
    continue
  fi
  echo "##### $suite $ds on $es ($(date -Is))"
  t0=$(date +%s)
  (
    # KEY=VALUE words after the dataset in a profile line set the job's environment.
    for kv in $extra; do export "${kv?}"; done
    case $suite in
      v2) run_v2 "$ds" $es ;;
      geographica) run_geographica $es ;;
      scale) "$V2/suites/scale/run_scale.sh" "$ds" $es ;;
      railpack) python3 "$V2/suites/railpack/run_railpack.py" run --dataset "$ds" ;;
      *) "$V2/suites/run_suite.sh" "$suite" "$ds" $es ;;
    esac
  ) 2>&1 | tee "$LOG"
  st=${PIPESTATUS[0]}
  # The suites note a failed engine with "!!! " and run_all.sh a failed load, and go on.
  grep -q '^!!! \|^load failed for ' "$LOG" && st=1
  status=ok; [ "$st" = 0 ] || { status=failed; FAILED=1; }
  python3 "$V2/runs.py" job "$MANIFEST" --suite "$suite" --dataset "$ds" --engines "$es" --status $status \
    ${note:+--reason "$note"} --seconds $(( $(date +%s) - t0 )) --log "$(basename "$LOG")"
  [ -n "${BENCH_PUSH_PARTIAL:-}" ] && push_partial "$suite $ds"
done <<<"$JOBS"
python3 "$V2/runs.py" finish "$MANIFEST"
python3 "$V2/runs.py" index "$V2/results/runs"
exit $FAILED
