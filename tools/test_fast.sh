#!/usr/bin/env bash
# Offline unit tests, fast.
#   tools/test_fast.sh        quick tier, a few seconds: the build footprints come from a disk cache
#                             (TTL_FOOTPRINT_CACHE, see gen_data.read_footprint) and the @heavy tests (tests/tiers.py:
#                             full structure loads in verify_build) skip. The first run after a structure changed
#                             reads that structure again (up to ~1 minute when all of them changed).
#   tools/test_fast.sh --all  every test, one process per test module in parallel (also with the cache)
# The plain full suite is unchanged and caches nothing: python -I -m unittest discover -s tests
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=$(command -v python3 || command -v python)
cd "$ROOT"
# Keys are content hashes, so every worktree can share one cache.
# Not under %LOCALAPPDATA%: the Microsoft Store Python silently redirects its writes there to a private folder.
: "${TTL_FOOTPRINT_CACHE:=${XDG_CACHE_HOME:-$HOME/.cache}/ocs-two-lives/footprints}"
export TTL_FOOTPRINT_CACHE

if [ "${1:-}" != --all ]; then
  TTL_FAST_TESTS=1 exec "$PY" -I -m unittest discover -s tests "$@"
fi

out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
t0=$(date +%s)
# Each module writes only to its own temp dirs, so they can run side by side; the cache writes are atomic.
printf '%s\n' tests/test_*.py | sed 's|tests/||; s|\.py$||' | xargs -P "$(nproc 2>/dev/null || echo 4)" -I{} sh -c \
  '"$1" -I -m unittest discover -s tests -p "$2.py" > "$3/$2.log" 2>&1 || touch "$3/$2.failed"' _ "$PY" {} "$out"
failed=$(ls "$out"/*.failed 2>/dev/null | xargs -r -n1 basename | sed 's/\.failed$//')
ran=$(cat "$out"/*.log | grep -oE '^Ran [0-9]+' | awk '{s += $2} END {print s + 0}')
for m in $failed; do echo "=== $m"; cat "$out/$m.log"; done
echo "Ran $ran tests in $(( $(date +%s) - t0 ))s (one process per module): ${failed:+FAILED: }${failed:-OK}"
[ -z "$failed" ]
