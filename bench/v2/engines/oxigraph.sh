#!/bin/bash
# Oxigraph (docker image ghcr.io/oxigraph/oxigraph, RocksDB store) for benchmark v2. Plain SPARQL
# 1.1, no GeoSPARQL: used by the general suites (suites/bsbm, suites/sparqloscope,
# suites/trainmarks), not by the spatial workload.
#   oxigraph.sh load <dataset>   `oxigraph load` into an on-disk store + start; prints JSON
#   oxigraph.sh start <dataset> | stop | endpoint | rss
# Env: BENCH_WORK, OXIGRAPH_IMAGE (default ghcr.io/oxigraph/oxigraph:0.5.13).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
IMAGE=${OXIGRAPH_IMAGE:-ghcr.io/oxigraph/oxigraph:0.5.13}
NAME=bench-oxigraph
PORT=7879
EP=http://localhost:$PORT/query

wait_up() {
  for _ in $(seq 1 600); do
    if curl -sf -G "$EP" --data-urlencode 'query=ASK {}' >/dev/null 2>&1; then return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' $NAME 2>/dev/null)" != true ]; then
      echo "oxigraph died" >&2; docker logs --tail 30 $NAME >&2; return 1; fi
    sleep 0.5
  done
  return 1
}

start() {
  local ds=$1
  docker rm -f $NAME >/dev/null 2>&1 || true
  docker run -d --name $NAME -p $PORT:7878 -u "$(id -u):$(id -g)" -v "$W/oxigraph/$ds:/store" \
    "$IMAGE" serve --location /store --bind 0.0.0.0:7878 --timeout-s 600 >/dev/null
  wait_up
}

case "$1" in
  load)
    ds=$2
    IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
    docker rm -f $NAME >/dev/null 2>&1 || true
    rm -rf "$W/oxigraph/$ds"; mkdir -p "$W/oxigraph/$ds"
    t0=$(date +%s.%N)
    docker run --rm -u "$(id -u):$(id -g)" -v "$W/oxigraph/$ds:/store" -v "$W/data:/data:ro" \
      "$IMAGE" load --location /store --file "/data/$(basename "$IN")" >"$W/oxigraph/$ds.load.log" 2>&1 \
      || { echo "oxigraph load failed:" >&2; tail -n 30 "$W/oxigraph/$ds.load.log" >&2; exit 1; }
    t1=$(date +%s.%N)
    start "$ds"
    t2=$(date +%s.%N)
    bytes=$(du -sb "$W/oxigraph/$ds" | cut -f1)
    printf '{"engine":"oxigraph","dataset":"%s","load_s":%.3f,"start_s":%.3f,"disk_bytes":%s}\n' \
      "$ds" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$bytes"
    ;;
  start) start "$2" ;;
  stop) docker rm -f $NAME >/dev/null 2>&1 || true ;;
  endpoint) echo "$EP" ;;
  rss) docker stats --no-stream --format '{{.MemUsage}}' $NAME ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss" >&2; exit 2 ;;
esac
