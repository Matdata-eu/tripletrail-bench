#!/bin/bash
# GraphDB (docker image ontotext/graphdb) for benchmark v2.
#   graphdb.sh load <dataset>   offline preload (importrdf) + start + GeoSPARQL index; prints JSON
#   graphdb.sh start <dataset> | stop | endpoint | rss
# Env: BENCH_WORK (default bench/v2/work), GRAPHDB_IMAGE, GRAPHDB_HEAP (default BENCH_MEMORY, see budget.sh).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
. "$HERE/budget.sh"
IMAGE=${GRAPHDB_IMAGE:-mirror.gcr.io/ontotext/graphdb:10.8.0}
HEAP=${GRAPHDB_HEAP:-${BENCH_MEMORY_GIB}g}
NAME=bench-graphdb
PORT=7200
EP=http://localhost:$PORT/repositories/bench
# Run the container as the calling user, as the other engines do, so the store it writes under
# $W can be measured (du) and deleted (DROP_AFTER) by the runner. Without it GraphDB's files are
# owned by the image's user and a non-root runner (the Hetzner one) cannot read them.
AS_ME=(-u "$(id -u):$(id -g)" -e HOME=/tmp)

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
    if curl -sf "$EP/size" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  echo "graphdb did not start" >&2; docker logs --tail 50 $NAME >&2; return 1
}

start() {
  local ds=$1
  ensure_image
  docker rm -f $NAME >/dev/null 2>&1 || true
  docker run -d --name $NAME -p $PORT:7200 "${AS_ME[@]}" \
    -v "$W/graphdb/$ds:/opt/graphdb/home" \
    -e GDB_JAVA_OPTS="-Xms$HEAP -Xmx$HEAP -Dgraphdb.home=/opt/graphdb/home" \
    "$IMAGE" >/dev/null
  wait_up
}

case "$1" in
  load)
    ds=$2
    IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
    rm -rf "$W/graphdb/$ds"; mkdir -p "$W/graphdb/$ds"
    ensure_image
    t0=$(date +%s.%N)
    docker run --rm "${AS_ME[@]}" -v "$W/graphdb/$ds:/opt/graphdb/home" -v "$W/data:/data:ro" \
      -v "$HERE/graphdb-repo.ttl:/repo.ttl:ro" -e GDB_HEAP_SIZE="$HEAP" \
      -e GDB_JAVA_OPTS="-Xms$HEAP -Xmx$HEAP -Dgraphdb.home=/opt/graphdb/home" \
      --entrypoint /opt/graphdb/dist/bin/importrdf "$IMAGE" preload -f -c /repo.ttl "/data/$(basename "$IN")" >"$W/graphdb/$ds.load.log" 2>&1 \
      || { echo "graphdb load failed:" >&2; tail -n 30 "$W/graphdb/$ds.load.log" >&2; exit 1; }
    t1=$(date +%s.%N)
    start "$ds"
    t2=$(date +%s.%N)
    # Build the GeoSPARQL plugin index (geohash prefix tree, GraphDB's default precision).
    # GRAPHDB_NO_GEO=1 skips it (the general suites in ../suites need no spatial index).
    if [ -z "${GRAPHDB_NO_GEO:-}" ]; then
      curl -sf -X POST "$EP/statements" --data-urlencode \
        'update=PREFIX geosparql: <http://www.ontotext.com/plugins/geosparql#> INSERT DATA { [] geosparql:enabled "true" . }' >/dev/null
    fi
    t3=$(date +%s.%N)
    bytes=$(du -sb "$W/graphdb/$ds" | cut -f1)
    printf '{"engine":"graphdb","dataset":"%s","load_s":%.3f,"start_s":%.3f,"spatial_index_s":%.3f,"disk_bytes":%s}\n' \
      "$ds" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$(echo "$t3 - $t2" | bc)" "$bytes"
    ;;
  start) start "$2" ;;
  stop) docker rm -f $NAME >/dev/null 2>&1 || true ;;
  endpoint) echo "$EP" ;;
  rss) docker stats --no-stream --format '{{.MemUsage}}' $NAME ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss" >&2; exit 2 ;;
esac
