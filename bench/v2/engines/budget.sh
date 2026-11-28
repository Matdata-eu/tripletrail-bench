#!/bin/bash
# The resource budget every engine of a run gets (tripletrail-bench#94), so no engine is measured
# with more memory or more cores than another. Sourced by the engine scripts; run it to print
# the budget and what each engine makes of it as JSON (env.py records that in env.json):
#   engines/budget.sh json
#
#   BENCH_MEMORY  memory for each engine, as <n>G (default: half the machine's RAM: 32G on a
#                 64 GB ccx43). The other half is the OS page cache and the client.
#   BENCH_CORES   cores an engine may use for one query (default: all of them, as TripleTrail
#                 uses them all).
#
# What each engine gets of it (an engine's own variable, such as JENA_HEAP, still wins):
#   tripletrail  --memory-limit BENCH_MEMORY (TRIPLETRAIL_MEMORY_LIMIT), all cores
#   jena         -Xmx BENCH_MEMORY (JENA_HEAP); Fuseki answers one query on one core
#   graphdb      -Xmx BENCH_MEMORY (GRAPHDB_HEAP); one query on one core
#   qlever       -m BENCH_MEMORY for queries and for the index build (QLEVER_MEMORY,
#                QLEVER_INDEX_MEMORY)
#   postgis      shared_buffers 25 % and effective_cache_size 75 % of BENCH_MEMORY,
#                max_parallel_workers_per_gather and max_parallel_workers BENCH_CORES
#   oxigraph, maplib  no setting for either; they use what they need
budget_defaults() {
  if [ -z "${BENCH_MEMORY:-}" ]; then
    # MemTotal is a little below the machine's size (the kernel keeps some): rounded up to a
    # multiple of 4 GiB, it is the size the machine is sold as.
    local kb gib
    kb=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
    gib=$(((kb + 4 * 1024 * 1024 - 1) / (4 * 1024 * 1024) * 4))
    BENCH_MEMORY="$((gib / 2))G"
    [ "$BENCH_MEMORY" = 0G ] && BENCH_MEMORY=1G
  fi
  case $BENCH_MEMORY in
    *[0-9]G) ;;
    *) echo "BENCH_MEMORY must be whole GiB, such as 32G (got $BENCH_MEMORY)" >&2; return 1 ;;
  esac
  BENCH_CORES=${BENCH_CORES:-$(nproc 2>/dev/null || echo 1)}
  BENCH_MEMORY_GIB=${BENCH_MEMORY%G}
  export BENCH_MEMORY BENCH_CORES BENCH_MEMORY_GIB
}

# PostGIS's memory settings, in MB: shared_buffers (25 %) and effective_cache_size (75 %).
pg_shared_buffers() { echo "$((BENCH_MEMORY_GIB * 1024 / 4))MB"; }
pg_effective_cache() { echo "$((BENCH_MEMORY_GIB * 1024 * 3 / 4))MB"; }
# Room for the parallel workers and PostgreSQL's own background workers.
pg_worker_processes() { echo "$((BENCH_CORES + 8))"; }

budget_defaults || { [ "${BASH_SOURCE[0]}" = "$0" ] && exit 1 || return 1; }

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case ${1:-json} in
    json)
      printf '{"memory": "%s", "cores": %s, "engines": {' "$BENCH_MEMORY" "$BENCH_CORES"
      printf '"tripletrail": "--memory-limit %s", ' "${TRIPLETRAIL_MEMORY_LIMIT:-$BENCH_MEMORY}"
      printf '"jena": "-Xmx%s", ' "${JENA_HEAP:-${BENCH_MEMORY_GIB}g}"
      printf '"graphdb": "-Xmx%s", ' "${GRAPHDB_HEAP:-${BENCH_MEMORY_GIB}g}"
      printf '"qlever": "-m %s (index -m %s)", ' "${QLEVER_MEMORY:-$BENCH_MEMORY}" "${QLEVER_INDEX_MEMORY:-$BENCH_MEMORY}"
      printf '"postgis": "shared_buffers %s, effective_cache_size %s, %s parallel workers"}}\n' \
        "${PG_SHARED_BUFFERS:-$(pg_shared_buffers)}" "${PG_EFFECTIVE_CACHE:-$(pg_effective_cache)}" "$BENCH_CORES"
      ;;
    *) echo "usage: $0 json" >&2; exit 2 ;;
  esac
fi
