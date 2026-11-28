#!/bin/bash
# PostgreSQL + PostGIS + pgRouting for benchmark v2.
#   postgis.sh load <dataset>   data/export_postgis.py into database rinf_<dataset>; prints JSON
#   postgis.sh start <dataset> | stop | endpoint <dataset> | rss
# By default it drives a local Debian/Ubuntu cluster (pg_ctlcluster 16 main, settings in
# postgis.conf and the run's budget from budget.sh, which `postgis.sh setup` writes to conf.d). With PG_DSN_BASE set (e.g.
# "host=localhost port=5432 user=postgres password=bench" for the docker compose service) it only
# connects; start restarts the container named by PG_CONTAINER (docker-compose.yml), if set.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
. "$HERE/budget.sh"
PGVER=${PGVER:-16}
BASE=${PG_DSN_BASE:-host=/var/run/postgresql user=postgres}

start() {
  if [ -n "${PG_DSN_BASE:-}" ]; then
    [ -n "${PG_CONTAINER:-}" ] && docker restart "$PG_CONTAINER" >/dev/null
  else
    pg_ctlcluster "$PGVER" main restart
  fi
  for _ in $(seq 1 60); do psql "$BASE dbname=postgres" -Atc 'SELECT 1' >/dev/null 2>&1 && return 0; sleep 0.5; done
  return 1
}

case "$1" in
  setup)
    { cat "$HERE/postgis.conf"
      echo "shared_buffers = ${PG_SHARED_BUFFERS:-$(pg_shared_buffers)}"
      echo "effective_cache_size = ${PG_EFFECTIVE_CACHE:-$(pg_effective_cache)}"
      echo "max_parallel_workers_per_gather = $BENCH_CORES"
      echo "max_parallel_workers = $BENCH_CORES"
      echo "max_worker_processes = $(pg_worker_processes)"
    } >"/etc/postgresql/$PGVER/main/conf.d/bench.conf"
    start
    ;;
  load)
    ds=$2
    psql "$BASE dbname=postgres" -qc "DROP DATABASE IF EXISTS rinf_$ds" -c "CREATE DATABASE rinf_$ds"
    psql "$BASE dbname=rinf_$ds" -qc "CREATE EXTENSION postgis" -c "CREATE EXTENSION pgrouting"
    t0=$(date +%s.%N)
    if [ -f "$W/data/$ds.osm.pbf" ]; then
      # OSM dataset: the same extraction as the RDF side (geometries from the same WKT)
      python3 "$HERE/../data/osm_extract.py" "$W/data/$ds.osm.pbf" --out "$W/pg-$ds" --dsn "$BASE dbname=rinf_$ds" >/dev/null
      python3 "$HERE/../data/pg_meta.py" "$W/pg-$ds.meta.json" "$ds"
      rm -f "$W/pg-$ds.nt" "$W/pg-$ds.meta.json"
      exit 0
    fi
    out=$(python3 "$HERE/../data/export_postgis.py" --dsn "$BASE dbname=rinf_$ds" "$W/data/$ds.nt")
    t1=$(date +%s.%N)
    echo "$out" >"$W/postgis-$ds.load.json"
    python3 - "$ds" "$(echo "$t1 - $t0" | bc)" "$out" <<'EOF'
import json, sys
ds, total, out = sys.argv[1], float(sys.argv[2]), json.loads(sys.argv[3])
load = out["copy_s"] + out["geometry_s"] + out["index_s"]
print(json.dumps({"engine": "postgis", "dataset": ds, "load_s": round(load, 3),
                  "parse_and_convert_s": round(out["parse_s"] + out["build_s"], 3),
                  "total_s": round(total, 3), "disk_bytes": out["db_bytes"], "rows": out["rows"]}))
EOF
    ;;
  start) start ;;
  stop) [ -n "${PG_DSN_BASE:-}" ] || pg_ctlcluster "$PGVER" main stop || true ;;
  endpoint) echo "$BASE dbname=rinf_$2" ;;
  rss) ps -C postgres -o rss= | awk '{s+=$1} END {printf "%.0f MiB (sum over backends, shared buffers counted per process)\n", s/1024}' ;;
  *) echo "usage: $0 setup | load|start <dataset> | stop | endpoint <dataset> | rss" >&2; exit 2 ;;
esac
