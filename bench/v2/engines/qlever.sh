#!/bin/bash
# QLever (docker image adfreiburg/qlever) for benchmark v2.
#   qlever.sh load <dataset>   qlever-index with the geo-split vocabulary + start; prints JSON
#   qlever.sh start <dataset> | stop | endpoint | rss
# Env: BENCH_WORK, QLEVER_IMAGE, QLEVER_MEMORY (memory for queries incl. cache, default 8G),
# QLEVER_CACHE (default 2G), QLEVER_NOFILE (open files, default 1048576).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
IMAGE=${QLEVER_IMAGE:-mirror.gcr.io/adfreiburg/qlever:latest}
MEM=${QLEVER_MEMORY:-8G}
CACHE=${QLEVER_CACHE:-2G}
# Open files for the container; a host whose hard limit is lower (a cloud sandbox) sets it lower.
NOFILE=${QLEVER_NOFILE:-1048576}
NAME=bench-qlever
PORT=7001
EP=http://localhost:$PORT/

# Pull the image if it is not here yet. mirror.gcr.io only mirrors Docker Hub images that someone
# pulled through it before, so on a fresh machine fall back to Docker Hub itself.
ensure_image() {
  docker image inspect "$IMAGE" >/dev/null 2>&1 && return 0
  docker pull -q "$IMAGE" >/dev/null 2>&1 && return 0
  case "$IMAGE" in
    mirror.gcr.io/*) echo "pull of $IMAGE failed, trying docker.io" >&2; IMAGE=docker.io/${IMAGE#mirror.gcr.io/} ;;
  esac
  docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull -q "$IMAGE" >&2
}

wait_up() {
  for _ in $(seq 1 600); do
    if curl -sf -G "$EP" --data-urlencode 'query=ASK {}' >/dev/null 2>&1; then return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' $NAME 2>/dev/null)" != true ]; then
      echo "qlever died" >&2; docker logs --tail 30 $NAME >&2; return 1; fi
    sleep 1
  done
  return 1
}

start() {
  local ds=$1
  ensure_image
  docker rm -f $NAME >/dev/null 2>&1 || true
  docker run -d --name $NAME --ulimit nofile=$NOFILE:$NOFILE -p $PORT:7001 -u "$(id -u):$(id -g)" -v "$W/qlever/$ds:/index" \
    --entrypoint /qlever/qlever-server "$IMAGE" -i /index/bench -p 7001 -j 2 \
    -m "$MEM" -c "$CACHE" -s 600s -a benchtoken >/dev/null
  wait_up
}

case "$1" in
  load)
    ds=$2
    IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
    rm -rf "$W/qlever/$ds"; mkdir -p "$W/qlever/$ds"
    echo '{"num-triples-per-batch": 1000000}' >"$W/qlever/$ds/bench.settings.json"
    ensure_image
    t0=$(date +%s.%N)
    # The vocabulary merge of a large input keeps one file open per partial vocabulary (978
    # for OSM Europe), more than Docker's default limit of 1024 open files allows.
    docker run --rm --ulimit nofile=$NOFILE:$NOFILE -u "$(id -u):$(id -g)" \
      -v "$W/qlever/$ds:/index" -v "$W/data:/data:ro" -w /index \
      --entrypoint /qlever/qlever-index "$IMAGE" -i /index/bench -f "/data/$(basename "$IN")" -F "${IN##*.}" -p true \
      -s /index/bench.settings.json --vocabulary-type on-disk-compressed-geo-split -m 4G \
      >"$W/qlever/$ds.load.log" 2>&1 \
      || { echo "qlever load failed:" >&2; tail -n 30 "$W/qlever/$ds.load.log" >&2; exit 1; }
    t1=$(date +%s.%N)
    start "$ds"
    t2=$(date +%s.%N)
    bytes=$(du -sb "$W/qlever/$ds" | cut -f1)
    printf '{"engine":"qlever","dataset":"%s","load_s":%.3f,"start_s":%.3f,"disk_bytes":%s}\n' \
      "$ds" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$bytes"
    ;;
  start) start "$2" ;;
  stop) docker rm -f $NAME >/dev/null 2>&1 || true ;;
  endpoint) echo "$EP" ;;
  rss) docker stats --no-stream --format '{{.MemUsage}}' $NAME ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss" >&2; exit 2 ;;
esac
