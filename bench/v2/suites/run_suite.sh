#!/bin/bash
# Run one general benchmark suite on several engines, one engine at a time, and write its report.
#   run_suite.sh bsbm <products> [engine...]          e.g. run_suite.sh bsbm 28480
#   run_suite.sh sparqloscope <dataset> [engine...]   bsbm-<products> | rinf-<code> | dblp
#   run_suite.sh trainmarks <scale> [engine...]       medium | large | xlarge
#   run_suite.sh updates <dataset> [engine...]        bsbm-<products> | rinf-<code> | any $BENCH_WORK/data/<name>.nt
#   run_suite.sh shacl <dataset> [engine...]          rinf-<code> | rinf-all (engines: tripletrail jena topbraid graphdb rdf4j pyshacl)
# Default engines: tripletrail oxigraph qlever jena graphdb maplib (updates: no qlever, no maplib). Datasets are generated or downloaded
# on first use (into $BENCH_WORK/data, never into git). DROP_AFTER=1 deletes each engine's store
# after its run (needed for dblp on a 300 GB disk). Never run in CI on pull requests: see
# README.md (manual workflow .github/workflows/bench-suites.yml).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
V2=$(dirname "$HERE")
W=${BENCH_WORK:-$V2/work}
SUITE=$1; DS=$2; shift 2
DEFAULT="tripletrail oxigraph qlever jena graphdb maplib"
[ "$SUITE" = updates ] && DEFAULT="tripletrail oxigraph jena graphdb"
[ "$SUITE" = shacl ] && DEFAULT="tripletrail jena topbraid graphdb rdf4j pyshacl"
ENGINES=${*:-$DEFAULT}
ALL="tripletrail tripletrail-ids oxigraph qlever jena graphdb maplib postgis"
# The general suites need no spatial index.
export GRAPHDB_NO_GEO=1
mkdir -p "$V2/results/$SUITE"
# A run of some engines only (say, one engine added later) keeps its environment apart, so the
# dataset's env file still describes the run that the other engines' numbers come from.
ENV_FILE="$V2/results/$SUITE/env-$DS.json"
[ "$ENGINES" = "$DEFAULT" ] || ENV_FILE="$V2/results/$SUITE/env-$DS.only-$(echo $ENGINES | tr ' ' '-').json"
python3 "$V2/env.py" >"$ENV_FILE"
stop_all() { for x in $ALL; do "$V2/engines/$x.sh" stop >/dev/null 2>&1; done; sync; }

case $SUITE in
  bsbm)
    [ -f "$W/data/bsbm-$DS.nt" ] || "$HERE/bsbm/bsbm.sh" generate "$DS" ;;
  sparqloscope)
    case $DS in
      bsbm-*) [ -f "$W/data/$DS.nt" ] || "$HERE/bsbm/bsbm.sh" generate "${DS#bsbm-}" ;;
      rinf-*) [ -f "$W/data/$DS.nt" ] || python3 "$HERE/data/fetch_rinf.py" "${DS#rinf-}" ;;
      dblp) "$HERE/data/fetch_dblp.sh" ;;
    esac
    if [ ! -f "$HERE/sparqloscope/benchmarks/$DS.benchmark.tsv" ] && [ "$DS" != dblp ]; then
      stop_all; "$V2/engines/qlever.sh" load "$DS" && python3 "$HERE/sparqloscope/run_sparqloscope.py" generate --dataset "$DS"
    fi ;;
  trainmarks)
    [ -f "$W/data/trainmarks-$DS.nt" ] || python3 "$HERE/trainmarks/run_trainmarks.py" generate ;;
  updates)
    case $DS in
      bsbm-*) [ -f "$W/data/$DS.nt" ] || "$HERE/bsbm/bsbm.sh" generate "${DS#bsbm-}" ;;
      rinf-*) [ -f "$W/data/$DS.nt" ] || python3 "$HERE/data/fetch_rinf.py" "${DS#rinf-}" ;;
    esac
    python3 "$HERE/updates/run_updates.py" generate --source "$DS" || exit 1 ;;
  shacl)
    # setup makes a venv with rdflib and pySHACL; the suite then runs in it.
    python3 "$HERE/shacl/run_shacl.py" setup || exit 1
    SHPY=$W/shacl-engines/py/bin/python3 ;;
  *) echo "unknown suite $SUITE" >&2; exit 2 ;;
esac

for e in $ENGINES; do
  stop_all
  echo "=== $SUITE $DS on $e ($(date -Is))"
  case $SUITE in
    bsbm) python3 "$HERE/bsbm/run_bsbm.py" run --products "$DS" --engine "$e" ;;
    sparqloscope) python3 "$HERE/sparqloscope/run_sparqloscope.py" run --dataset "$DS" --engine "$e" ;;
    trainmarks) python3 "$HERE/trainmarks/run_trainmarks.py" run --scale "$DS" --engine "$e" ;;
    updates) python3 "$HERE/updates/run_updates.py" run --source "$DS" --engine "$e" ;;
    # run_shacl.py prints "!!! " itself for a profile an engine fails on.
    # Seeded violations (recall and precision) on the datasets in SHACL_INJECT, Norway by default.
    shacl) "$SHPY" "$HERE/shacl/run_shacl.py" run --dataset "$DS" --engine "$e"; rc=$?
      case " ${SHACL_INJECT-rinf-0076} " in
        *" $DS "*) "$SHPY" "$HERE/shacl/run_shacl.py" inject --dataset "$DS" --engine "$e" \
          || echo "!!! $SUITE $DS injected violations failed on $e" ;;
      esac
      (exit $rc) ;;
  esac || echo "!!! $SUITE $DS failed on $e"
  "$V2/engines/$e.sh" stop >/dev/null 2>&1
  if [ -n "${DROP_AFTER:-}" ]; then
    case $SUITE in bsbm) d=bsbm-$DS ;; trainmarks) d=trainmarks-$DS ;; updates) d=updates-$DS ;; *) d=$DS ;; esac
    # tripletrail-ids keeps its store in tripletrail's directory (engines/tripletrail-ids.sh).
    s=$e; [ "$e" = tripletrail-ids ] && s=tripletrail
    rm -rf "${W:?}/$s/$d"
  fi
done
case $SUITE in
  bsbm) python3 "$HERE/bsbm/run_bsbm.py" report ;;
  sparqloscope) python3 "$HERE/sparqloscope/run_sparqloscope.py" report ;;
  trainmarks) python3 "$HERE/trainmarks/run_trainmarks.py" report ;;
  updates) python3 "$HERE/updates/run_updates.py" report ;;
  shacl) python3 "$HERE/shacl/run_shacl.py" report ;;
esac
# Again now that the engines' images are pulled (the first capture runs before, on a fresh server).
python3 "$V2/env.py" >"$ENV_FILE"
echo "=== done ($(date -Is))"
