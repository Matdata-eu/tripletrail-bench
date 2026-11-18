#!/bin/bash
# Berlin SPARQL Benchmark (BSBM, http://wifo5-03.informatik.uni-mannheim.de/bizer/berlinsparqlbenchmark/)
# with the official bsbmtools 0.2 (Apache-2.0), run in a Java container so nothing is installed
# on the host and the downloaded jars never run outside docker.
#   bsbm.sh fetch                       download bsbmtools-v0.2.zip (sha256-checked) to $BENCH_WORK/bsbm
#   bsbm.sh generate <products>         -> $BENCH_WORK/data/bsbm-<products>.nt (+ update file and
#                                          the test driver's parameter data td_data-<products>)
#   bsbm.sh testdriver <products> <usecase> <endpoint> <out.xml> [update-endpoint]
#                                       usecase: explore | bi | exploreAndUpdate
# Env: BENCH_WORK, BSBM_JAVA_IMAGE, BSBM_RUNS (timed query mixes, default 50), BSBM_WARMUP
# (default 10), BSBM_TIMEOUT_MS (per query, default 60000), BSBM_CLIENTS (default 1),
# BSBM_IGNORE (query template numbers to leave out of the mixes, e.g. "9 12").
# Scale: 1,000 products ~ 375k triples; 2,785 ~ 1M; 28,480 ~ 10M; 284,826 ~ 100M.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../../work}
IMAGE=${BSBM_JAVA_IMAGE:-mirror.gcr.io/library/eclipse-temurin:21-jre}
URL=https://downloads.sourceforge.net/project/bsbmtools/bsbmtools/bsbmtools-0.2/bsbmtools-v0.2.zip
SHA=40f5e59baadec3af0014b7647989d3e0fc0476af25e84a4bc9d7f8cd81520aaa
B=$W/bsbm/bsbmtools-0.2
CP=lib/bsbm.jar:lib/jdom.jar:lib/log4j-1.2.12.jar:lib/ssj.jar

# http.keepAlive=false: a new connection per query, as in ../../run.py (QLever answers on a
# kept-alive connection wait ~40 ms for a delayed ACK).
java_run() {  # java_run <main class> args... (cwd = bsbmtools dir, $W/data mounted at /data)
  docker run --rm --network host -u "$(id -u):$(id -g)" -v "$B:/bsbm" -v "$W/data:/data" -v "$W/bsbm/out:/out" \
    -w /bsbm "$IMAGE" java -Xmx2g -Dhttp.keepAlive=false -cp "$CP" "$@"
}

case "${1:-}" in
  fetch)
    [ -d "$B" ] && exit 0
    mkdir -p "$W/bsbm"
    curl -sSfL -o "$W/bsbm/bsbmtools-v0.2.zip" "$URL"
    echo "$SHA  $W/bsbm/bsbmtools-v0.2.zip" | sha256sum -c --quiet
    (cd "$W/bsbm" && unzip -q -o bsbmtools-v0.2.zip)
    ;;
  generate)
    pc=$2
    "$0" fetch
    mkdir -p "$W/data" "$W/bsbm/out"
    # -ud -tc: also write the update dataset (dataset_update.nt, the last 10 % of the products, one
    # per transaction) used by the explore-and-update mix; the main file holds the other 90 %
    java_run benchmark.generator.Generator -pc "$pc" -s nt -fn "/data/bsbm-$pc" -dir "/out/td_data-$pc" -ud -tc "$((pc / 10))" \
      >"$W/bsbm/generate-$pc.log" 2>&1
    mv -f "$B/dataset_update.nt" "$W/bsbm/out/update-$pc.nt" 2>/dev/null || true
    printf '{"products":%s,"triples":%s}\n' "$pc" "$(wc -l <"$W/data/bsbm-$pc.nt")" >"$W/data/bsbm-$pc.meta.json"
    cat "$W/data/bsbm-$pc.meta.json"
    ;;
  testdriver)
    pc=$2 uc=$3 ep=$4 out=$5 uep=${6:-}
    [ "$uc" = bi ] && uc=businessIntelligence
    base=$uc  # before a skip variant renames it
    if [ -n "${BSBM_IGNORE:-}" ]; then
      # A copy of the use case whose query mixes skip the templates in BSBM_IGNORE (numbers).
      v=$uc-skip-$(echo "$BSBM_IGNORE" | tr ' ' '-')
      mkdir -p "$B/usecases/$v"; : >"$B/usecases/$v/sparql.txt"
      while read -r line; do
        d=${line#querymix=}; mkdir -p "$B/$d-$v"; cp "$B/$d"/* "$B/$d-$v/"
        echo "$BSBM_IGNORE" >"$B/$d-$v/ignoreQueries.txt"; echo "querymix=$d-$v" >>"$B/usecases/$v/sparql.txt"
      done <"$B/usecases/$uc/sparql.txt"
      uc=$v
    fi
    mkdir -p "$W/bsbm/out"
    extra=()
    if [ "$base" = exploreAndUpdate ]; then
      extra=(-u "$uep" -udataset "/out/update-$pc.nt")
    fi
    java_run benchmark.testdriver.TestDriver -idir "/out/td_data-$pc" -ucf "usecases/$uc/sparql.txt" \
      -runs "${BSBM_RUNS:-50}" -w "${BSBM_WARMUP:-10}" -t "${BSBM_TIMEOUT_MS:-60000}" -mt "${BSBM_CLIENTS:-1}" \
      -o "/out/$(basename "$out")" "${extra[@]}" "$ep"
    [ "$W/bsbm/out/$(basename "$out")" -ef "$out" ] || mv -f "$W/bsbm/out/$(basename "$out")" "$out"
    ;;
  *) echo "usage: $0 fetch | generate <products> | testdriver <products> <usecase> <endpoint> <out.xml> [update-endpoint]" >&2; exit 2 ;;
esac
