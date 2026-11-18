#!/bin/bash
# Download the benchmark inputs that cannot be generated into $BENCH_WORK/inputs, once:
#   norway-rail-landuse-admin.osm.pbf   OSM extract for v2 osm_norway (OSM as of 2026-11-05;
#                                        © OpenStreetMap contributors, ODbL): an asset of the
#                                        release BENCH_DATA_TAG (default bench-data) of
#                                        BENCH_DATA_REPO (default this repository)
#   geographica2/{datasets,queries}     the Geographica 2 real-world datasets (no census),
#                                        downloaded from https://geographica2.di.uoa.gr/ and
#                                        checked against the SHA-256 sums below; the query lists
#                                        come from ../geographica/queries (Apache-2.0)
# The datasets have no licence of their own, so they are fetched at run time and never copied
# into this repository. Pinned files keep the numbers comparable between runs. A missing or
# changed input only prints a warning: bench.sh then skips the jobs that need it.
#   GH_TOKEN=... data/fetch_inputs.sh      (GH_TOKEN: to read the release; any token works for a public one)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${BENCH_WORK:-$HERE/../work}
D=$W/inputs
REPO=${BENCH_DATA_REPO:-${GITHUB_REPOSITORY:-Matdata-eu/tripletrail-bench}}
TAG=${BENCH_DATA_TAG:-bench-data}
API=${GITHUB_API_URL:-https://api.github.com}
GEO_URL=${GEOGRAPHICA_URL:-https://geographica2.di.uoa.gr/datasets}
mkdir -p "$D"

# Geographica 2: the six datasets the micro and macro workloads use, at the sums of 2026-11-18.
G=$D/geographica2
if [ ! -d "$G/datasets" ] || [ "$(ls "$G/datasets"/*.tar.xz 2>/dev/null | wc -l)" -lt 6 ]; then
  mkdir -p "$G/datasets.part"
  ok=1
  while read -r sum name; do
    f="$G/datasets.part/$name.tar.xz"
    [ -f "$f" ] && echo "$sum  $f" | sha256sum -c --quiet 2>/dev/null && continue
    echo "fetching Geographica 2 $name"
    if ! curl -sSfL --retry 3 -o "$f" "$GEO_URL/$name.tar.xz"; then
      echo "::warning::download of Geographica 2 $name failed"; ok=""; continue
    fi
    echo "$sum  $f" | sha256sum -c --quiet || { echo "::warning::Geographica 2 $name changed upstream (SHA-256 differs)"; ok=""; }
  done <<'SUMS'
c21f0e5cdbfa51e9e31a33ae90cf0cf2558b94e9d8c540a48285c3f97507fd46 corine
170e591aeec13fdde69ce98831d2159ec60becac901d1fae0ccd82363766a845 dbpedia
f3340ee5391052cb2fa6ec6993c06c2dc7fb796ff7b782ad24cb6beb2b8933f4 gag
73c589112d876259f7dffa5d4a0764ff99df1f9aac23ba85a96b5cf16336aee2 geonames
38e2895e116882f323f480ddbec89e7bbe599195b592111fdce104302ebd676f hotspots
c13e0594707d28fa2d0c9da9819991ed71dd4700f9e7049126278d2d0fb1aefd linkedgeodata
SUMS
  if [ -n "$ok" ]; then
    rm -rf "$G/datasets" && mv "$G/datasets.part" "$G/datasets"
    rm -rf "$G/queries" && cp -r "$HERE/../geographica/queries" "$G/queries"
  fi
fi

need=()
[ -f "$D/norway-rail-landuse-admin.osm.pbf" ] || need+=(norway-rail-landuse-admin.osm.pbf)
[ ${#need[@]} = 0 ] && { echo "inputs present in $D"; exit 0; }
[ -n "${GH_TOKEN:-}" ] || { echo "::warning::GH_TOKEN is not set: cannot fetch ${need[*]}"; exit 0; }

auth=(-H "Authorization: Bearer $GH_TOKEN" -H "X-GitHub-Api-Version: 2022-11-28")
rel=$(curl -sS --retry 3 "${auth[@]}" -H "Accept: application/vnd.github+json" "$API/repos/$REPO/releases/tags/$TAG")
for name in "${need[@]}"; do
  url=$(python3 -c 'import json,sys
r=json.loads(sys.argv[1]); print(next((a["url"] for a in r.get("assets",[]) if a["name"]==sys.argv[2]),""))' "$rel" "$name")
  if [ -z "$url" ]; then
    echo "::warning::asset $name is not in release $TAG of $REPO (see bench/v2/cloud/README.md): its jobs are skipped"
    continue
  fi
  echo "fetching $name"
  # -L: the asset redirects to storage; curl drops the Authorization header on the other host.
  curl -sSfL --retry 3 "${auth[@]}" -H "Accept: application/octet-stream" -o "$D/$name.part" "$url" \
    || { echo "::warning::download of $name failed"; rm -f "$D/$name.part"; continue; }
  case $name in
    *.tar) tar -xf "$D/$name.part" -C "$D" && rm -f "$D/$name.part" ;;
    *) mv "$D/$name.part" "$D/$name" ;;
  esac
done
ls -la "$D"
