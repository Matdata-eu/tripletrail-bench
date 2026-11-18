#!/bin/bash
# Apache Jena Fuseki with jena-geosparql (the standalone "GeoSPARQL Fuseki" jar) on TDB2.
#   jena.sh load <dataset>    tdb2.tdbloader (parallel) + first start, which builds the spatial index
#   jena.sh start <dataset> | stop | endpoint | rss
# Env: BENCH_WORK, JENA_JAR (default $BENCH_WORK/jena/jena-fuseki-geosparql-6.2.0.jar,
# from https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-geosparql/6.2.0/),
# JENA_HEAP (default 8g), JENA_PORT (default 3030), JENA_JAVA_IMAGE (used when the host has no `java`, default
# eclipse-temurin:21-jre; the server then runs as container bench-jena on the host network).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
JAR=${JENA_JAR:-$W/jena/jena-fuseki-geosparql-6.2.0.jar}
HEAP=${JENA_HEAP:-8g}
PORT=${JENA_PORT:-3030}
EP=http://localhost:$PORT/ds/query
PIDF=$W/jena/server.pid
NAME=bench-jena
JIMAGE=${JENA_JAVA_IMAGE:-mirror.gcr.io/library/eclipse-temurin:21-jre}
if command -v java >/dev/null 2>&1; then DOCKER_JAVA=; else DOCKER_JAVA=1; fi
JAR=$(realpath -m "$JAR"); W=$(realpath -m "$W")
# Container mounts: the work dir, and the jar's folder when it is outside it.
MOUNTS=(-v "$W:$W"); case "$JAR" in "$W"/*) ;; *) MOUNTS+=(-v "$(dirname "$JAR"):$(dirname "$JAR"):ro") ;; esac

# java "$@" on the host, or in the Java image with $W and the jar's folder mounted at the same paths.
djava() {
  if [ -z "$DOCKER_JAVA" ]; then java "$@"; return; fi
  docker image inspect "$JIMAGE" >/dev/null 2>&1 || docker pull -q "$JIMAGE" >/dev/null 2>&1 \
    || { JIMAGE=docker.io/${JIMAGE#mirror.gcr.io/}; docker pull -q "$JIMAGE" >&2; }
  docker run --rm -u "$(id -u):$(id -g)" "${MOUNTS[@]}" \
    --network host "$JIMAGE" java "$@"
}
running() {
  if [ -n "$DOCKER_JAVA" ]; then [ "$(docker inspect -f '{{.State.Running}}' $NAME 2>/dev/null)" = true ]
  else kill -0 "$(cat "$PIDF")" 2>/dev/null; fi
}

wait_up() {
  for _ in $(seq 1 3600); do
    if curl -sf -G "$EP" --data-urlencode 'query=ASK {}' >/dev/null 2>&1; then return 0; fi
    if ! running; then echo "jena died" >&2; if [ -n "$DOCKER_JAVA" ]; then docker logs --tail 30 $NAME >&2; else tail -30 "$W/jena/server.log" >&2; fi; return 1; fi
    sleep 1
  done
  return 1
}

start() {
  local ds=$1
  stop
  # Another service on the port would answer wait_up's probe, or make Fuseki fail to bind.
  if curl -s -o /dev/null --max-time 2 "http://localhost:$PORT/"; then
    echo "port $PORT is already in use on this machine: set JENA_PORT to a free port" >&2; return 1; fi
  # Query rewrite and the spatial index are on by default; the index is saved in the TDB folder.
  # --update: SPARQL Update on /ds/update (BSBM's update mix, Trainmarks' q6).
  local args=(-Xms$HEAP -Xmx$HEAP -jar "$JAR" --tdb2 --tdb "$W/jena/$ds"
    --spatial_index "$W/jena/$ds/spatial.index" --port $PORT --dataset ds --update)
  if [ -n "$DOCKER_JAVA" ]; then
    djava -version >/dev/null 2>&1 || true  # pulls the image if needed
    docker run -d --name $NAME -u "$(id -u):$(id -g)" "${MOUNTS[@]}" \
      --network host "$JIMAGE" java "${args[@]}" >/dev/null
  else
    nohup java "${args[@]}" >"$W/jena/server.log" 2>&1 &
    echo $! >"$PIDF"
  fi
  wait_up
}

stop() {
  [ -n "$DOCKER_JAVA" ] && { docker rm -f $NAME >/dev/null 2>&1 || true; }
  if [ -f "$PIDF" ]; then kill "$(cat "$PIDF")" 2>/dev/null || true
    for _ in $(seq 1 60); do kill -0 "$(cat "$PIDF")" 2>/dev/null || break; sleep 1; done
    rm -f "$PIDF"; fi
}

case "$1" in
  load)
    ds=$2
    IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
    rm -rf "$W/jena/$ds"; mkdir -p "$W/jena/$ds"
    t0=$(date +%s.%N)
    [ -f "$JAR" ] || { echo "no Jena jar at $JAR" >&2; exit 1; }
    djava -Xms$HEAP -Xmx$HEAP -cp "$JAR" tdb2.tdbloader --loader=parallel --loc "$W/jena/$ds" "$IN" \
      >"$W/jena/$ds.load.log" 2>&1 \
      || { echo "jena load failed:" >&2; tail -n 30 "$W/jena/$ds.load.log" >&2; exit 1; }
    t1=$(date +%s.%N)
    start "$ds"
    t2=$(date +%s.%N)
    bytes=$(du -sb "$W/jena/$ds" | cut -f1)
    printf '{"engine":"jena","dataset":"%s","load_s":%.3f,"start_and_spatial_index_s":%.3f,"disk_bytes":%s}\n' \
      "$ds" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$bytes"
    ;;
  start) start "$2" ;;
  stop) stop ;;
  endpoint) echo "$EP" ;;
  rss) if [ -n "$DOCKER_JAVA" ]; then docker stats --no-stream --format '{{.MemUsage}}' $NAME
       else ps -o rss= -p "$(cat "$PIDF")" | awk '{printf "%.0f MiB\n", $1/1024}'; fi ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss" >&2; exit 2 ;;
esac
