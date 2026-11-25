#!/usr/bin/env bash
# GraphDB as a validator for the SHACL suite (run_phase0.py and probes.py call it):
#
#   graphdb_validate.sh <data> <shapes> <report.ttl>
#
# Starts the GraphDB image with an empty SHACL repository (graphdb-repo.ttl), loads the data,
# then adds the shapes to RDF4J's shapes graph in one transaction: GraphDB (RDF4J's ShaclSail
# inside) validates all the data then, and refuses the transaction with the report when the data
# does not conform. Writes the report (or a conforming one) and exits 1 when it does not
# conform, 0 when it does, 2 on an error. Env: GRAPHDB_IMAGE, GRAPHDB_HEAP (default 8g), JAVA_STACK (default 1g).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE=${GRAPHDB_IMAGE:-mirror.gcr.io/ontotext/graphdb:10.8.0}
HEAP=${GRAPHDB_HEAP:-8g}
NAME=shacl-graphdb
PORT=${GRAPHDB_PORT:-7201}
BASE=http://localhost:$PORT
DATA=$(realpath "$1") SHAPES=$(realpath "$2") REPORT=$3

case "$DATA" in *.nt) TYPE=application/n-triples ;; *) TYPE=text/turtle ;; esac
docker rm -f $NAME >/dev/null 2>&1 || true
docker run -d --name $NAME -p $PORT:7200 \
  -e GDB_JAVA_OPTS="-Xms$HEAP -Xmx$HEAP -Xss${JAVA_STACK:-1g}" "$IMAGE" >/dev/null
trap 'docker rm -f $NAME >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 300); do curl -sf "$BASE/rest/repositories" >/dev/null 2>&1 && break; sleep 1; done
curl -sSf -X POST "$BASE/rest/repositories" -F "config=@$HERE/graphdb-repo.ttl" >/dev/null || exit 2

t0=$(date +%s.%N)
# -T streams the file; --data-binary reads it into memory first and fails above 2 GB.
curl -sSf -X POST "$BASE/repositories/shacl/statements" -H "Content-Type: $TYPE" \
  -T "$DATA" >/dev/null || { echo "graphdb: loading the data failed" >&2; exit 2; }
t1=$(date +%s.%N)
code=$(curl -s -o "$REPORT.body" -w '%{http_code}' -X POST \
  "$BASE/repositories/shacl/statements?context=%3Chttp%3A%2F%2Frdf4j.org%2Fschema%2Frdf4j%23SHACLShapeGraph%3E" \
  -H "Content-Type: text/turtle" -H "Accept: text/turtle" --data-binary "@$SHAPES")
t2=$(date +%s.%N)
# The container's peak memory: cgroup v2 (memory.peak), else v1 (memory.max_usage_in_bytes).
peak=$(docker exec $NAME sh -c 'cat /sys/fs/cgroup/memory.peak 2>/dev/null ||
  cat /sys/fs/cgroup/memory/memory.max_usage_in_bytes 2>/dev/null || echo 0')
echo "graphdb: container peak memory $peak bytes" >&2
echo "graphdb: data loaded in $(echo "$t1 - $t0" | bc) s, shapes added and validated in $(echo "$t2 - $t1" | bc) s (HTTP $code)" >&2
if [ "$code" = 204 ] || [ "$code" = 200 ]; then
  printf '@prefix sh: <http://www.w3.org/ns/shacl#> .\n[] a sh:ValidationReport ; sh:conforms true .\n' >"$REPORT"
  rm -f "$REPORT.body"
  exit 0
fi
# A refused transaction answers the report; anything else is an error (its body goes to stderr).
if grep -q "ValidationReport" "$REPORT.body"; then
  python3 - "$REPORT.body" "$REPORT" <<'EOF'
import sys
body = open(sys.argv[1]).read()
# GraphDB wraps the Turtle report in an error message; keep from its first @prefix on.
start = body.find("@prefix")
open(sys.argv[2], "w").write(body[start:] if start >= 0 else body)
EOF
  rm -f "$REPORT.body"
  exit 1
fi
head -c 3000 "$REPORT.body" >&2
rm -f "$REPORT.body"
exit 2
