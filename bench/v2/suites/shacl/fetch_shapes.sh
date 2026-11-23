#!/usr/bin/env bash
# Downloads the ERA SHACL shapes for RINF, the ERA ontology and its SKOS code lists, pinned to
# one commit of the ERA ontology repository (EUPL-1.2), into $BENCH_WORK/data/shacl/:
#
#   era-rinf-shapes.ttl   era-shacl/ERA-RINF-shapes.ttl, checked against its SHA-256
#   lookup.nt             ontology.ttl and every era-skos/*.ttl, as N-Triples (Jena's riot)
#
# Nothing of it is committed: the files are fetched at run time, the way Geographica is.
# Needs curl, python3 and JENA_HOME (an apache-jena distribution, for riot).
set -euo pipefail

COMMIT=${ERA_ONTOLOGY_COMMIT:-8177357f07e72cad979bc10596e53d88e966af83}
SHAPES_SHA256=${ERA_SHAPES_SHA256:-e0038a087dfeffd5575bd5ea78136632747d894cc2b9d7a657ec62186bf58097}
PROJECT=era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology
RAW="https://gitlab.com/$PROJECT/-/raw/$COMMIT"
API="https://gitlab.com/api/v4/projects/${PROJECT//\//%2F}/repository/tree"
V2=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${BENCH_WORK:-$V2/work}/data/shacl
mkdir -p "$OUT/skos"

curl -sSfL --retry 4 -o "$OUT/era-rinf-shapes.ttl" "$RAW/era-shacl/ERA-RINF-shapes.ttl"
echo "$SHAPES_SHA256  $OUT/era-rinf-shapes.ttl" | sha256sum -c --quiet

curl -sSfL --retry 4 -o "$OUT/ontology.ttl" "$RAW/ontology.ttl"
for page in 1 2 3 4 5; do
  curl -sSfL --retry 4 "$API?ref=$COMMIT&path=era-skos&recursive=true&per_page=100&page=$page"
done | python3 -c '
import json, sys
dec = json.JSONDecoder()
s, i = sys.stdin.read(), 0
while i < len(s):
    items, i = dec.raw_decode(s, i)
    for x in items:
        if x["type"] == "blob" and x["path"].endswith(".ttl"):
            print(x["path"])
' >"$OUT/skos.list"
xargs -P 8 -I{} sh -c 'curl -sSfL --retry 4 -o "$1/skos/$(basename "$2")" "$3/$2"' _ "$OUT" {} "$RAW" <"$OUT/skos.list"

"${JENA_HOME:?set JENA_HOME to an apache-jena distribution}/bin/riot" --output=nt \
  "$OUT/ontology.ttl" "$OUT"/skos/*.ttl >"$OUT/lookup.nt" 2>/dev/null
echo "shapes $(sha256sum "$OUT/era-rinf-shapes.ttl" | cut -c1-12) at $COMMIT;" \
  "lookup: $(wc -l <"$OUT/lookup.nt") triples from ontology.ttl and $(wc -l <"$OUT/skos.list") code lists"
