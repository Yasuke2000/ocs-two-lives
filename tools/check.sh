#!/usr/bin/env bash
# Pre-push check (offline, ~1 minute or less): validate.py + the fast unit tier + node --check on the JS that changed.
# When builds or the structure tools changed, the heavy tests run too (tools/test_fast.sh --all).
#
#   bash tools/check.sh              compare with origin/main (what a PR would contain, plus uncommitted edits)
#   bash tools/check.sh <base-ref>   compare with another ref
#
# Opt-in git pre-push hook (one clone; worktrees share it):
#   printf '#!/bin/sh\nexec bash tools/check.sh\n' > "$(git rev-parse --git-common-dir)/hooks/pre-push"
# Skip it once with `git push --no-verify`.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=$(command -v python3 || command -v python)
cd "$ROOT"
base=$(git merge-base HEAD "${1:-origin/main}" 2>/dev/null || echo HEAD)
changed=$( { git diff --name-only "$base"; git ls-files --others --exclude-standard; } | sort -u)
fail=

step() { printf '\n== %s\n' "$*"; }

step "validate.py"
# validate.py looks for packwiz on PATH; Go installs it to ~/go/bin. Two of its steps take minutes, and both get an
# opt-in cache keyed by file contents (CI and a plain validate.py never cache): gen_data.py --check reads every
# build's footprint (the same cache as tools/test_fast.sh), build_structures.py --check rebuilds every blueprint
# (skipped while blueprints/, the structure tools and the files it compared are as they were at its last pass).
# Not under %LOCALAPPDATA%: the Microsoft Store Python silently redirects its writes there to a private folder.
: "${TTL_FOOTPRINT_CACHE:=${XDG_CACHE_HOME:-$HOME/.cache}/ocs-two-lives/footprints}"
: "${TTL_STRUCTURE_CHECK_CACHE:=${XDG_CACHE_HOME:-$HOME/.cache}/ocs-two-lives/structure-check}"
export TTL_FOOTPRINT_CACHE TTL_STRUCTURE_CHECK_CACHE
PATH="$PATH:$HOME/go/bin" "$PY" tools/validate.py || fail="$fail validate"

js=$(grep -E '\.js$' <<<"$changed" | while read -r f; do [ -f "$f" ] && echo "$f"; done)
step "node --check ($(grep -c . <<<"$js") changed JS file(s))"
for f in $js; do node --check "$f" || fail="$fail node:$f"; done

if grep -qE '^(blueprints/|pack/kubejs/data/ttl/structure/|tools/(blueprint|build_structures|verify_build|nbt)\.py|tools/lerfing/|tests/tiers\.py)' <<<"$changed"; then
  step "unit tests, all (structures or structure tools changed)"
  bash tools/test_fast.sh --all || fail="$fail unit-tests"
else
  step "unit tests, fast tier"
  bash tools/test_fast.sh || fail="$fail unit-tests"
fi

if [ -n "$fail" ]; then printf '\ncheck FAILED:%s\n' "$fail"; exit 1; fi
printf '\ncheck passed (in-game: bash tools/local.sh test <name>, then staging after the deploy)\n'
