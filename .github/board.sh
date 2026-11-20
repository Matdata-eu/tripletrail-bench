#!/usr/bin/env bash
# Reads or sets fields of the TripleTrail project board through the Board
# workflow (.github/workflows/board.yml), using only the REST API, and prints
# the result as a tab-separated table.
#
#   .github/board.sh                                   open items on the board
#   .github/board.sh all                               every item, closed too
#   .github/board.sh 42                                one item of the repository this checkout is
#   .github/board.sh tripletrail-demo#3                an item of another repository
#   .github/board.sh 42 'Worker=Builder 1; Status=In progress'
#   .github/board.sh 42 'Worker='                      clears Worker
#
# The workflow runs in Matdata-eu/tripletrail-enterprise by default: it is
# private, so its logs may show items of private repositories. -R owner/repo
# (or BOARD_REPO) runs it elsewhere; a public repository shows only public
# items. Needs gh, signed in with a token that may run workflows. Exits non-zero when the run fails.
set -euo pipefail

repo=${BOARD_REPO:-Matdata-eu/tripletrail-enterprise}
if [[ ${1:-} == -R ]]; then
  repo=$2
  shift 2
fi
item=${1:-}
# A bare number means an item of this checkout's repository.
if [[ $item =~ ^[0-9]+$ ]] && url=$(git -C "$(dirname "$0")" remote get-url origin 2>/dev/null); then
  item="$(sed -E 's#\.git$##; s#^.*/##' <<<"$url")#$item"
fi
set_fields=${2:-}
request="$(date +%s)-$RANDOM$RANDOM"

branch=$(gh api "repos/$repo" --jq .default_branch)
gh api -X POST "repos/$repo/actions/workflows/board.yml/dispatches" \
  -f ref="$branch" -f "inputs[item]=$item" -f "inputs[set]=$set_fields" \
  -f "inputs[request]=$request" >/dev/null

run=
for _ in $(seq 60); do
  run=$(gh api "repos/$repo/actions/workflows/board.yml/runs?event=workflow_dispatch&per_page=30" \
    --jq ".workflow_runs[] | select(.display_title | endswith(\"[$request]\")) | .id" | head -n1)
  [[ -n $run ]] && break
  sleep 2
done
if [[ -z $run ]]; then
  echo "board.sh: the run did not show up in $repo" >&2
  exit 1
fi

for _ in $(seq 300); do
  status=$(gh api "repos/$repo/actions/runs/$run" --jq .status)
  [[ $status == completed ]] && break
  sleep 2
done
conclusion=$(gh api "repos/$repo/actions/runs/$run" --jq .conclusion)

log=$(for job in $(gh api "repos/$repo/actions/runs/$run/jobs" --jq '.jobs[].id'); do
  gh api "repos/$repo/actions/jobs/$job/logs"
done | sed -E 's/^[0-9-]+T[0-9:.]+Z ?//')

grep -E '^##\[(notice|warning|error)\]' <<<"$log" | sed -E 's/^##\[([a-z]+)\]/\1: /' >&2 || true
sed -n '/^----- board result -----$/,/^----- end -----$/{//!p}' <<<"$log"

if [[ $conclusion != success ]]; then
  echo "board.sh: run $conclusion: https://github.com/$repo/actions/runs/$run" >&2
  exit 1
fi
