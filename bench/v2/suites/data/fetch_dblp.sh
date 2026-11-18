#!/bin/bash
# The DBLP knowledge graph, 2025-04-01 release (CC0), the dataset of Sparqloscope's official DBLP
# query set: https://doi.org/10.4230/dblp.rdf.ntriples.2025-04-01
#   fetch_dblp.sh   -> $BENCH_WORK/data/dblp.nt (about 5 GB download, 61 GB unpacked)
# Running Sparqloscope on it needs about 64 GB of RAM and 300 GB of disk for the file plus one
# engine's store at a time (run_suite.sh drops each store after its run): not the NUC or a
# GitHub-hosted runner; see ../../cloud/README.md.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../../work}
URL=https://drops.dagstuhl.de/storage/artifacts/dblp/rdf/2025/dblp-2025-04-01.nt.gz
mkdir -p "$W/data"
cd "$W/data"
[ -f dblp.nt ] && { echo "dblp.nt already there"; exit 0; }
curl -sSfL -C - -o dblp-2025-04-01.nt.gz "$URL"
curl -sSfL -o dblp-2025-04-01.nt.gz.md5 "$URL.md5"
echo "$(awk '{print $1}' dblp-2025-04-01.nt.gz.md5)  dblp-2025-04-01.nt.gz" | md5sum -c --quiet
gunzip -c dblp-2025-04-01.nt.gz >dblp.nt.tmp && mv dblp.nt.tmp dblp.nt && rm dblp-2025-04-01.nt.gz
printf '{"release":"2025-04-01","triples":%s}\n' "$(wc -l <dblp.nt)" >dblp.meta.json
cat dblp.meta.json
