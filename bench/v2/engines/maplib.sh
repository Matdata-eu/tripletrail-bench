#!/bin/bash
# maplib (Python library, in-memory, https://github.com/DataTreehouse/maplib, Apache-2.0) for
# benchmark v2. maplib has no server: maplib_server.py wraps a Model in a minimal SPARQL protocol
# endpoint, in a Python container with maplib installed, so it is timed over HTTP like the other
# engines. Plain SPARQL 1.1: used by the general suites (suites/trainmarks, suites/bsbm,
# suites/sparqloscope), not by the spatial workload.
#   maplib.sh load <dataset>   start the server, which reads the N-Triples into memory; prints JSON
#   maplib.sh start <dataset> | stop | endpoint | rss | logs
# The store lives in memory only: `load` and `start` both read the file, and `start` keeps a
# server that already holds <dataset>. disk_bytes is 0.
# Env: BENCH_WORK, MAPLIB_VERSION (default 0.22.0; maplib_server.py needs 0.22.0 or later), MAPLIB_PY_IMAGE.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
VERSION=${MAPLIB_VERSION:-0.22.0}
PY_IMAGE=${MAPLIB_PY_IMAGE:-mirror.gcr.io/library/python:3.12-slim}
IMAGE=bench-maplib:$VERSION
NAME=bench-maplib
PORT=7883
EP=http://localhost:$PORT/query

# A local image with maplib installed, built once per version.
ensure_image() {
  docker image inspect "$IMAGE" >/dev/null 2>&1 && return 0
  printf 'FROM %s\nRUN pip install --no-cache-dir maplib==%s\n' "$PY_IMAGE" "$VERSION" \
    | docker build -q -t "$IMAGE" - >&2
}

wait_up() {
  for _ in $(seq 1 3600); do
    if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' $NAME 2>/dev/null)" != true ]; then
      echo "maplib died" >&2; docker logs --tail 30 $NAME >&2; return 1; fi
    sleep 0.5
  done
  echo "maplib did not start" >&2; return 1
}

start() {
  local ds=$1
  if [ "$(docker inspect -f '{{.State.Running}} {{index .Config.Labels "dataset"}}' $NAME 2>/dev/null)" = "true $ds" ]; then
    return 0
  fi
  local IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
  ensure_image
  docker rm -f $NAME >/dev/null 2>&1 || true
  docker run -d --name $NAME --label "dataset=$ds" -p $PORT:7000 -u "$(id -u):$(id -g)" -e HOME=/tmp \
    -v "$W/data:/data:ro" -v "$HERE/maplib_server.py:/maplib_server.py:ro" \
    "$IMAGE" python3 /maplib_server.py "/data/$(basename "$IN")" 7000 >/dev/null
  wait_up
}

case "$1" in
  load)
    ds=$2
    docker rm -f $NAME >/dev/null 2>&1 || true
    ensure_image
    t0=$(date +%s.%N)
    start "$ds"
    t1=$(date +%s.%N)
    # The server's own read time (without the container start), and its peak RSS.
    info=$(docker logs $NAME 2>/dev/null | grep -m1 '"load_s"')
    python3 - "$ds" "$t0" "$t1" "$info" <<'EOF'
import json, sys
ds, t0, t1, info = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), json.loads(sys.argv[4])
print(json.dumps({"engine": "maplib", "dataset": ds, "load_s": info["load_s"],
                  "start_s": round(t1 - t0 - info["load_s"], 3), "disk_bytes": 0,
                  "load_peak_rss_bytes": info["load_peak_rss_bytes"], "in_memory": True}))
EOF
    ;;
  start) start "$2" ;;
  stop) docker rm -f $NAME >/dev/null 2>&1 || true ;;
  endpoint) echo "$EP" ;;
  logs) docker logs --tail 50 $NAME 2>&1 ;;
  rss) docker stats --no-stream --format '{{.MemUsage}}' $NAME ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss" >&2; exit 2 ;;
esac
