#!/bin/bash
# The scale benchmark of #218: a store larger than its memory limit. An OSM extract becomes
# N-Triples (data/osm_scale.py, the shape of osm_norway plus buildings and highways), which each
# engine loads and answers the OSM and scale query families of benchmark v2 on. TripleTrail runs
# on its store on disk with --memory-limit, then takes small commits (updates.py) against it.
#   run_scale.sh osm_benelux|osm_europe|osm_planet [engine...]     (default: tripletrail qlever; graphdb by name)
#     osm_benelux  Belgium, the Netherlands and Luxembourg (a bounding box of Europe), about 100M
#                  triples; TripleTrail's commits are also timed on the store in memory there, the
#                  reference of the acceptance criterion (p95 within 2x)
#     osm_europe   all of Europe, cut at SCALE_MAX_TRIPLES (default 1,000,000,000)
#     osm_planet   the whole planet (planet.openstreetmap.org), cut at SCALE_MAX_TRIPLES (default
#                  5,000,000,000); needs about 3 TB of work disk (bench.yml gives it a
#                  3,000 GB volume: the N-Triples, about 1 TB, next to the largest store, GraphDB's
#                  about 1.2 TB) and more memory than a ccx43 (a ccx53, 128 GB)
# Env: BENCH_WORK, BENCH_MEMORY and BENCH_CORES (engines/budget.sh), TRIPLETRAIL_MEMORY_LIMIT (default BENCH_MEMORY), SCALE_MAX_TRIPLES, SCALE_PBF_URL
# (default Geofabrik's europe-latest, or the planet for osm_planet), SCALE_KEEP=1 (keep the inputs, the N-Triples and the
# stores; otherwise each goes once it is no longer needed: the disk of a 360 GB server holds one
# at a time). Results: results/<dataset>/ as for v2, plus updates-*.json and scale.json.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
V2=$(cd "$HERE/../.." && pwd)
W=${BENCH_WORK:-$V2/work}
export BENCH_WORK=$W
DS=$1; shift
ENGINES=${*:-tripletrail qlever}
# GraphDB runs only when named (run_scale.sh osm_benelux graphdb). Every engine gets the run's
# budget (engines/budget.sh: half the machine's RAM, 32G on a ccx43): TripleTrail's
# --memory-limit, GraphDB's heap and QLever's query and index memory (tripletrail-bench#94).
. "$V2/engines/budget.sh" || exit 1
LIMIT=${TRIPLETRAIL_MEMORY_LIMIT:-$BENCH_MEMORY}
case $DS in
  osm_planet) URL=${SCALE_PBF_URL:-https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf} ;;
  *) URL=${SCALE_PBF_URL:-https://download.geofabrik.de/europe-latest.osm.pbf} ;;
esac
PBF=$W/inputs/$(basename "$URL")
OUT=$V2/results/$DS
CONV=$V2/data/osm_scale.py
case $DS in
  osm_benelux) BBOX=2.5,49.4,7.3,53.6; MAX=${SCALE_MAX_TRIPLES:-0} ;;
  osm_europe) BBOX=""; MAX=${SCALE_MAX_TRIPLES:-1000000000} ;;
  osm_planet) BBOX=""; MAX=${SCALE_MAX_TRIPLES:-5000000000} ;;
  *) echo "unknown scale dataset $DS" >&2; exit 2 ;;
esac
# Kills, memory pressure and stops of the runner service, into the run log as they happen:
# twice the bench server's runner was stopped mid-run (runs 42927990120 and 42979745805) and
# the server went with its journal. Lines streamed after the runner's shutdown signal still
# reach the log for a few seconds.
if command -v journalctl >/dev/null && journalctl -n0 -q >/dev/null 2>&1; then
  journalctl -f -n0 -q -o short-iso -k -u systemd-oomd -u 'actions.runner*' 2>/dev/null \
    | grep --line-buffered -iE 'oom|kill|memory|stop|signal|shutdown|restart' \
    | sed -u 's/^/[journal] /' &
  trap 'kill %1 2>/dev/null' EXIT
fi
mkdir -p "$W/inputs" "$W/data" "$OUT"

# The N-Triples of $DS and their meta file, from the Europe extract (downloaded once).
prepare() {
  local nt=$W/data/$DS.nt meta=$W/data/$DS.meta.json tmp=$W/scale-tmp budget=$MAX
  [ -f "$nt" ] && [ -f "$meta" ] && return 0
  if [ ! -f "$PBF" ]; then
    echo "downloading $URL ($(date -Is))"
    curl -sSfL --retry 3 -o "$PBF.part" "$URL" || { echo "!!! download of $URL failed"; return 1; }
    mv "$PBF.part" "$PBF"
  fi
  rm -rf "$tmp"; mkdir -p "$tmp"
  local src=$PBF
  if [ -n "$BBOX" ]; then
    osmium extract -b "$BBOX" -O -o "$tmp/region.osm.pbf" "$PBF" || return 1
    src=$tmp/region.osm.pbf
  fi
  python3 - "$meta.part" "$PBF" "$BBOX" "$MAX" "$DS" <<'PY'
import json, os, sys, time
out, pbf, bbox, cap, ds = sys.argv[1:]
st = os.stat(pbf)
json.dump({"source": os.path.basename(pbf), "source_bytes": st.st_size,
           "source_mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
           "bbox_filter": bbox or None, "max_triples": int(cap) or None,
           "bbox": [float(v) for v in bbox.split(",")] if bbox else
           ([-180.0, -85.0, 180.0, 85.0] if ds == "osm_planet" else [-32.0, 34.0, 45.0, 72.0])},
          open(out, "w"))
PY
  rm -f "$nt.part"
  local t0; t0=$(date +%s)
  for set in a b; do
    if [ "$MAX" -gt 0 ]; then
      budget=$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(int(sys.argv[2]) - m.get("triples", 0))' "$meta.part" "$MAX")
      [ "$budget" -gt 0 ] || break
    fi
    # shellcheck disable=SC2046 # the expressions are separate words
    osmium tags-filter -O -o "$tmp/$set.osm.pbf" "$src" $(python3 "$CONV" --set "$set" --filters) || return 1
    osmium export -O -f geojsonseq --add-unique-id=type_id -i "sparse_file_array,$tmp/$set.idx" \
      -o - "$tmp/$set.osm.pbf" 2>"$tmp/$set.export.log" \
      | python3 "$CONV" --set "$set" --meta "$meta.part" --max-triples "$budget" >>"$nt.part"
    local st=("${PIPESTATUS[@]}")
    [ "${st[1]}" = 0 ] || { echo "!!! osm_scale.py failed on set $set"; return 1; }
    # osmium dies of the broken pipe once the converter stops at its cap.
    if [ "${st[0]}" != 0 ] && ! python3 -c 'import json,sys; sys.exit(not json.load(open(sys.argv[1]))["sets"][sys.argv[2]]["capped"])' "$meta.part" "$set"; then
      echo "!!! osmium export failed on set $set:"; tail -n 20 "$tmp/$set.export.log"; return 1
    fi
    rm -f "$tmp/$set.osm.pbf" "$tmp/$set.idx"
  done
  rm -rf "$tmp"
  python3 - "$meta.part" "$(( $(date +%s) - t0 ))" "$(stat -c %s "$nt.part")" <<'PY'
import json, sys
p, s, b = sys.argv[1:]
m = json.load(open(p)); m["convert_s"] = int(s); m["nt_bytes"] = int(b)
json.dump(m, open(p, "w"), indent=1)
PY
  mv "$nt.part" "$nt"; mv "$meta.part" "$meta"
  echo "prepared $DS: $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["triples"])' "$meta") triples"
}

prepare || exit 1
[ "$DS" != osm_benelux ] && [ -z "${SCALE_KEEP:-}" ] && rm -f "$PBF"
cp "$W/data/$DS.meta.json" "$OUT/data.json"
python3 "$V2/env.py" >"$OUT/env.json"
# What is known about a failed load, into the run log and the results: the engine's load log
# and memory curve, the kernel's and systemd-oomd's kills, memory and disk. The work volume
# goes with the server, so this is all that is left of it afterwards.
diagnose() {
  local e=$1
  for f in "$W/$e/$DS.load.log" "$W/$e/$DS.load.mem"; do
    [ -f "$f" ] || continue
    cp "$f" "$OUT/$e-$(basename "$f")"
    echo "--- tail of $(basename "$f")"; tail -n 40 "$f"
  done
  echo "--- kills"
  { journalctl -k --no-pager -n 300 2>/dev/null || dmesg 2>/dev/null; } | grep -i -E 'out of memory|oom|killed process' | tail -n 10
  journalctl -u systemd-oomd --no-pager -n 10 2>/dev/null | tail -n 10
  echo "--- memory and disk"; free -m; df -h "$W" 2>/dev/null
}
FAILED=0
for e in $ENGINES; do
  for x in postgis tripletrail oxigraph qlever jena graphdb; do "$V2/engines/$x.sh" stop >/dev/null 2>&1; done
  sync
  echo "=== $e on $DS ($(date -Is))"
  if [ "$e" = tripletrail ]; then
    # Warm runs are evaluated again, not answered from the result cache.
    export TRIPLETRAIL_MEMORY_LIMIT=$LIMIT TRIPLETRAIL_RESULT_CACHE_MB=0
  fi
  if ! python3 "$V2/run.py" load --engine "$e" --dataset "$DS"; then
    echo "!!! load failed for $e"; FAILED=1
    diagnose "$e"
    continue
  fi
  python3 "$V2/run.py" query --engine "$e" --dataset "$DS" --warm-scale "${WARM_SCALE:-1}" ${ONLY:+--only "$ONLY"} \
    || { echo "!!! queries failed for $e"; FAILED=1; }
  if [ "$e" = tripletrail ]; then
    # Small commits on the store on disk, under the memory limit, after the queries.
    "$V2/engines/tripletrail.sh" start "$DS" || { echo "!!! tripletrail did not start"; FAILED=1; }
    ep=$("$V2/engines/tripletrail.sh" endpoint)
    python3 "$HERE/updates.py" "$ep" "${ep%/query}/update" "$OUT/updates-tripletrail.json" \
      || { echo "!!! updates failed on tripletrail"; FAILED=1; }
    # In the job log, which outlives the volume when the artifact upload fails (#437).
    python3 -c 'import json,sys; print("per-commit ms:", json.load(open(sys.argv[1]))["ms"])' \
      "$OUT/updates-tripletrail.json" 2>/dev/null || true
    grep "slow commit" "$W/tripletrail/server.log" | tail -40 || true
    "$V2/engines/tripletrail.sh" rss | sed 's/^/tripletrail rss after the updates: /'
    "$V2/engines/tripletrail.sh" stop
    unset TRIPLETRAIL_MEMORY_LIMIT TRIPLETRAIL_RESULT_CACHE_MB
    if [ "$DS" = osm_benelux ]; then
      # The reference: the same commits on the store in memory (the data loaded at start).
      bin=${TRIPLETRAIL_BIN:-$V2/../../core/target/release/tripletrail}
      "$bin" serve --bind 127.0.0.1:7979 --dataset ds --load "$W/data/$DS.nt" --timeout 600 \
        >"$W/tripletrail-memory.log" 2>&1 &
      pid=$!
      for _ in $(seq 1 7200); do
        curl -sf -G http://127.0.0.1:7979/ds/query --data-urlencode 'query=ASK {}' >/dev/null 2>&1 && break
        kill -0 $pid 2>/dev/null || break
        sleep 0.5
      done
      python3 "$HERE/updates.py" http://127.0.0.1:7979/ds/query http://127.0.0.1:7979/ds/update \
        "$OUT/updates-tripletrail-memory.json" || { echo "!!! updates failed on the store in memory"; FAILED=1; }
      kill $pid; wait $pid 2>/dev/null
    fi
  fi
  "$V2/engines/$e.sh" stop >/dev/null 2>&1
  [ -z "${SCALE_KEEP:-}" ] && rm -rf "${W:?}/$e/$DS"
done
[ -z "${SCALE_KEEP:-}" ] && rm -f "$W/data/$DS.nt"
# Again now that the engines' images are pulled: the first capture runs on a fresh server, before
# any image is there, and named no engine's version (tripletrail-bench#99).
python3 "$V2/env.py" >"$OUT/env.json"
python3 "$V2/compare.py" "$OUT" >/dev/null || true
python3 "$V2/report.py" "$OUT" >/dev/null || true
echo "=== done ($(date -Is))"
exit $FAILED
