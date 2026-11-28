#!/bin/bash
# tripletrail (this repository's server) for benchmark v2, on the tripletrail store on disk.
#   tripletrail.sh load <dataset>   `tripletrail load` into an on-disk dataset + start; prints JSON
#   tripletrail.sh start <dataset> | stop | endpoint | rss | memory | pid
# Env: BENCH_WORK, BENCH_MEMORY (budget.sh: the --memory-limit, unless TRIPLETRAIL_MEMORY_LIMIT is set), TRIPLETRAIL_RESULT_CACHE_MB (default 0: result cache off), TRIPLETRAIL_BIN (default core/target/release/tripletrail: the
# TripleTrail repository checked out in core/, built with `cargo build --release -p tripletrail-server`), TRIPLETRAIL_SERVE_ARGS (more `serve` options, such as
# `--pack ds=DIR`), TRIPLETRAIL_WARM_WAIT (seconds to wait for the background map warm-up after start, default 600).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
. "$HERE/budget.sh"
# The run's memory budget (budget.sh), as for every engine: `load` and `serve` read it from the
# environment. TRIPLETRAIL_MEMORY_LIMIT set by the caller wins.
export TRIPLETRAIL_MEMORY_LIMIT=${TRIPLETRAIL_MEMORY_LIMIT:-$BENCH_MEMORY}
BIN=${TRIPLETRAIL_BIN:-$HERE/../../../core/target/release/tripletrail}
PORT=7878
EP=http://localhost:$PORT/ds/query
PIDF=$W/tripletrail/server.pid

# Waits up to TRIPLETRAIL_START_TIMEOUT seconds (default an hour: a store of a billion triples
# opens for a while) for the server to answer, and says why when it does not.
wait_up() {
  local deadline=$(($(date +%s) + ${TRIPLETRAIL_START_TIMEOUT:-3600}))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if curl -sf -G "$EP" --data-urlencode 'query=ASK {}' >/dev/null 2>&1; then return 0; fi
    if ! kill -0 "$(cat "$PIDF")" 2>/dev/null; then echo "tripletrail died" >&2; tail -30 "$W/tripletrail/server.log" >&2; return 1; fi
    sleep 0.5
  done
  echo "tripletrail did not answer within ${TRIPLETRAIL_START_TIMEOUT:-3600} s" >&2
  tail -30 "$W/tripletrail/server.log" >&2
  return 1
}

# `serve` builds each dataset's spatial index in the background once it is open, then makes
# its map (core #115: profile, shapes and facet counts, up to 5 minutes a dataset). Queries
# timed meanwhile would share the cores with them, so the bench waits for both: GET /$/ready
# answers 200 once the index is built (503 before; a core without it answers 404 and is not
# waited for), and the map logs a line (the served dataset is always "ds"): "ds: map ready",
# "ds: map made ahead in part" or "ds: the map was not made ahead". A core from before #115
# has no --no-warm-up and logs none of them, so that wait is skipped there;
# TRIPLETRAIL_WARM_WAIT (seconds, default 600) bounds the two waits together.
wait_warm() {
  local deadline=$(($(date +%s) + ${TRIPLETRAIL_WARM_WAIT:-600})) code
  # The spatial index, built in the background at open: /$/ready answers 200 once every
  # dataset's index is built, 503 before (a core without /$/ready answers 404: not waited for).
  while [ "$(date +%s)" -lt "$deadline" ]; do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:$PORT/\$/ready" || true)
    [ "$code" = 503 ] || break
    kill -0 "$(cat "$PIDF")" 2>/dev/null || return 0
    sleep 0.5
  done
  [ "$code" = 503 ] && echo "tripletrail: spatial index of $1 not built within ${TRIPLETRAIL_WARM_WAIT:-600} s, timing anyway" >&2
  # The map (core #115), made by its own thread after the datasets are open.
  grep -q -- "--no-warm-up" <<<"${TRIPLETRAIL_SERVE_ARGS:-}" && return 0
  "$BIN" serve --help 2>/dev/null | grep -q -- "--no-warm-up" || return 0
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if grep -qE "^ds: (map |the map was not made ahead)" "$W/tripletrail/server.log"; then
      grep -E "^ds: (map |the map was not made ahead)" "$W/tripletrail/server.log" | tail -n 1 >&2
      return 0
    fi
    kill -0 "$(cat "$PIDF")" 2>/dev/null || return 0
    sleep 0.5
  done
  echo "tripletrail: no map line for $1 within ${TRIPLETRAIL_WARM_WAIT:-600} s, timing anyway" >&2
}

# Stops the server and waits until it has exited and let go of the port: a server holding a
# store of a billion triples can take minutes to close, and one still exiting made the next
# start fail with "Address already in use" (scale run 42845266505). Killed after
# TRIPLETRAIL_STOP_TIMEOUT seconds (default 600).
stop() {
  if [ -f "$PIDF" ]; then
    local pid; pid=$(cat "$PIDF")
    kill "$pid" 2>/dev/null || true
    local deadline=$(($(date +%s) + ${TRIPLETRAIL_STOP_TIMEOUT:-600}))
    while kill -0 "$pid" 2>/dev/null && [ "$(date +%s)" -lt "$deadline" ]; do sleep 0.5; done
    if kill -0 "$pid" 2>/dev/null; then
      echo "tripletrail did not stop within ${TRIPLETRAIL_STOP_TIMEOUT:-600} s: killed" >&2
      kill -9 "$pid" 2>/dev/null || true
      while kill -0 "$pid" 2>/dev/null; do sleep 0.2; done
    fi
    rm -f "$PIDF"
  fi
  # Whatever else still listens on the port (a server started outside this script).
  for _ in $(seq 1 120); do
    curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$PORT/" || return 0
    sleep 0.5
  done
  echo "port $PORT is still in use" >&2
  return 1
}

# One line on a running load: elapsed seconds, heap, store size, I/O and CPU of the process.
progress() {
  local pid=$1 secs=$2 anon=$3 dir=$4 io cpu
  io=$(for p in "$pid" $(pgrep -P "$pid"); do cat "/proc/$p/io" 2>/dev/null || true; done |
    awk '/^(read|write)_bytes:/ {s[$1]+=$2} END {printf "read %.0f MB, written %.0f MB, ", s["read_bytes:"] / 1048576, s["write_bytes:"] / 1048576}')
  cpu=$(for p in "$pid" $(pgrep -P "$pid"); do awk '{print $14 + $15}' "/proc/$p/stat" 2>/dev/null || true; done |
    awk -v hz="$(getconf CLK_TCK)" '{s+=$1} END {printf "%.0f", s / hz}')
  echo "load $((secs / 60)) min: heap $((anon / 1024)) MB, store $(du -sm "$dir" 2>/dev/null | cut -f1) MB, ${io}cpu ${cpu} s"
}

start() {
  local ds=$1
  stop
  mkdir -p "$W/tripletrail"
  # The log of the server before this one, kept: a restart after a failed query would
  # otherwise lose what that query logged (tripletrail#340).
  [ -s "$W/tripletrail/server.log" ] && cat "$W/tripletrail/server.log" >> "$W/tripletrail/server.earlier.log"
  # The result cache is off unless TRIPLETRAIL_RESULT_CACHE_MB says otherwise: a warm run must
  # evaluate its query again, not answer from the cache (QLever's cache is cleared too).
  TRIPLETRAIL_RESULT_CACHE_MB=${TRIPLETRAIL_RESULT_CACHE_MB:-0} nohup "$BIN" serve --bind 127.0.0.1:$PORT --location "$W/tripletrail/$ds" --dataset ds --timeout 600 ${TRIPLETRAIL_SERVE_ARGS:-} \
    >"$W/tripletrail/server.log" 2>&1 &
  echo $! >"$PIDF"
  wait_up
}

case "$1" in
  load)
    ds=$2
    IN=$W/data/$ds.nt; [ -f "$W/data/$ds.nq" ] && IN=$W/data/$ds.nq
    stop
    rm -rf "$W/tripletrail/$ds"; mkdir -p "$W/tripletrail/$ds"
    t0=$(date +%s.%N)
    [ -x "$BIN" ] || { echo "no tripletrail binary at $BIN (cd core && cargo build --release -p tripletrail-server)" >&2; exit 1; }
    # GNU time gives the peak RSS of the load; without it (not installed) the load runs bare.
    TIMEV=(); [ -x /usr/bin/time ] && TIMEV=(/usr/bin/time -v)
    "${TIMEV[@]}" "$BIN" load --location "$W/tripletrail/$ds" --dataset ds "$IN" >"$W/tripletrail/$ds.load.log" 2>&1 &
    lp=$!
    # The peak RSS counts the mapped store files, which the kernel can drop; the peak of the
    # anonymous memory (heap) is what --memory-limit bounds, so it is sampled as well.
    # Every 10 s a line "<unix time> <anonymous KB> <file-backed KB> <store MB>" goes to
    # $ds.load.mem, so a load that dies (out of memory) leaves its memory curve behind.
    anon=0 n=0
    : >"$W/tripletrail/$ds.load.mem"
    while kill -0 "$lp" 2>/dev/null; do
      # `|| true`: the load can exit between `kill -0` and these reads (set -o pipefail).
      a=$(for p in "$lp" $(pgrep -P "$lp"); do awk '/^RssAnon:/ {print $2}' "/proc/$p/status" 2>/dev/null || true; done | awk '{s+=$1} END {print s+0}')
      [ "$a" -gt "$anon" ] && anon=$a
      if [ $((n % 20)) -eq 0 ]; then
        f=$(for p in "$lp" $(pgrep -P "$lp"); do awk '/^RssFile:/ {print $2}' "/proc/$p/status" 2>/dev/null || true; done | awk '{s+=$1} END {print s+0}')
        echo "$(date +%s) $a $f $(du -sm "$W/tripletrail/$ds" 2>/dev/null | cut -f1)" >>"$W/tripletrail/$ds.load.mem"
      fi
      # Every 10 minutes a progress line in the run's log (the work volume, with the load log
      # and memory curve, goes with the server): memory, store size, bytes read and written,
      # CPU seconds, so a load that runs long shows which phase it is in.
      if [ $((n % 1200)) -eq 1199 ]; then
        progress "$lp" "$(($(date +%s) - ${t0%.*}))" "$a" "$W/tripletrail/$ds" >&2
      fi
      n=$((n + 1))
      sleep 0.5
    done
    rc=0; wait "$lp" || rc=$?
    if [ "$rc" -ne 0 ]; then
      echo "tripletrail load failed (exit $rc), peak anonymous memory $((anon / 1024)) MB:" >&2
      tail -n 30 "$W/tripletrail/$ds.load.log" >&2
      exit 1
    fi
    t1=$(date +%s.%N)
    start "$ds"
    t2=$(date +%s.%N)
    # Memory when the dataset first answers, before the background work of start (the spatial
    # index, the map warm-up) has run: the bench's rss_after_start is taken after wait_warm, so
    # it includes that work, as runs from before tripletrail-bench#39 did not (core #188).
    answering=$("$0" rss)
    mem_answering=$("$0" memory 2>/dev/null || echo null)
    wait_warm "$ds"  # after t2: start_s stays the time until the dataset answers
    mem_started=$("$0" memory 2>/dev/null || echo null)
    bytes=$(du -sb "$W/tripletrail/$ds" | cut -f1)
    peak=$(awk -F: '/Maximum resident/ {gsub(/ /,"",$2); print $2*1024}' "$W/tripletrail/$ds.load.log")
    # Bytes by kind of store file (dict.bin, geoms.bin, dict.idx, spog.seg, ...: numbered
    # pieces and runs counted under their kind), for what takes the space (#370).
    files=$(find "$W/tripletrail/$ds" -type f -printf '%s %f\n' | awk '{n=$2; gsub(/-[0-9]+/,"",n); gsub(/\.[0-9]+[ar]?\./,".",n); s[n]+=$1} END {sep=""; for (k in s) {printf "%s\"%s\":%d", sep, k, s[k]; sep=","}}')
    printf '{"engine":"tripletrail","dataset":"%s","load_s":%.3f,"start_s":%.3f,"disk_bytes":%s,"disk_by_file":{%s},"load_peak_rss_bytes":%s,"load_peak_anon_bytes":%s,"rss_when_answering":"%s","memory_when_answering":%s,"memory_after_start":%s}\n' \
      "$ds" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$bytes" "$files" "${peak:-null}" "$((anon * 1024))" "$answering" "$mem_answering" "$mem_started"
    ;;
  start) start "$2" && wait_warm "$2" ;;
  stop) stop ;;
  endpoint) echo "$EP" ;;
  # Resident memory, and of it the anonymous part (heap); the rest is mapped store files.
  rss) awk '/^VmRSS:/ {r=$2} /^RssAnon:/ {a=$2} END {printf "%.0f MiB (heap %.0f MiB)\n", r/1024, a/1024}' \
    "/proc/$(cat "$PIDF")/status" ;;
  # The server's process id, for a profiler (run.py's PERF_QUERIES).
  pid) cat "$PIDF" ;;
  # Memory as JSON, for where RSS goes (core #188): the process's resident, anonymous (heap) and
  # file-backed (store pages the OS can drop) KB, and the parts the server counts itself in
  # /$/stats (the spatial and text indexes, the result cache, ...; a core without them: null).
  memory)
    pid=$(cat "$PIDF")
    stats=$(curl -s --max-time 30 "http://localhost:$PORT/\$/stats/ds" 2>/dev/null || true)
    python3 - "$pid" "$stats" <<'PY'
import json, sys
pid, stats = sys.argv[1], sys.argv[2]
st = {}
for line in open(f"/proc/{pid}/status"):
    k, _, v = line.partition(":")
    if k in ("VmRSS", "RssAnon", "RssFile", "RssShmem"):
        st[k] = int(v.split()[0])
try:
    d = json.loads(stats)["datasets"]["/ds"]
except (ValueError, KeyError, TypeError):
    d = {}
print(json.dumps({"rss_kb": st.get("VmRSS"), "anon_kb": st.get("RssAnon"), "file_kb": st.get("RssFile"),
                  "counted_bytes": d.get("memoryBytes"), "counted": d.get("memory"),
                  "mapped_bytes": d.get("mappedBytes")}, separators=(",", ":")))
PY
    ;;
  *) echo "usage: $0 load|start <dataset> | stop | endpoint | rss | memory | pid" >&2; exit 2 ;;
esac
