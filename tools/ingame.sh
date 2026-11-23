# In-game test runner for tests/ingame/*.rcon, shared by tools/server.sh (staging) and tools/local.sh (this PC).
# Source it after defining:
#   rcon "<command>"      run one server command and print the reply
#   log_grep "<regex>"    print the lines of the server's logs/latest.log that match (grep -E)
# Then call ingame_test <name> or ingame_test_all. Neither knows which server it talks to.

INGAME_DIR="$(dirname "${BASH_SOURCE[0]}")/../tests/ingame"
# The caller may override this: print a reason to skip test <name> on its server, nothing to run it.
ingame_skip_reason() { :; }
plain() { sed 's/\[[0-9;]*m//g'; }
FAILED_RE='Unknown or incomplete|Incorrect argument|Expected whitespace|An unexpected error|ttl: |Test failed'

run_test() {
  # `@sleep N` lines wait N seconds (game time has to pass between some steps). `@until N <command>` runs the command once
  # a second until its reply holds (no "ttl: ..." / "Test failed" / command error), for at most N seconds, and prints the
  # last reply: a step that waits on the server (a boss that has to spawn and be polled) waits as long as it needs, not a
  # fixed guess that a lag spike can beat.
  grep -vE '^\s*(#|$)' "$1" | while IFS= read -r cmd; do
    case "$cmd" in
      @sleep\ *) sleep "${cmd#@sleep }" ;;
      @until\ *)
        rest=${cmd#@until }; secs=${rest%% *}; c=${rest#* }
        echo "> $c (until it holds, ${secs}s at most)"
        for ((i = 0; i < secs; i++)); do
          out=$(rcon "$c" < /dev/null)
          grep -qE "$FAILED_RE" <<<"$(plain <<<"$out")" || break
          sleep 1
        done
        echo "$out" ;;
      *) echo "> $cmd"; rcon "$cmd" ;;
    esac
  done
}

# Tests never post to Discord (#story, #events): the mute is set for the run and lifted after it, and
# discord.js drops every post while a test bot is online as well.
# TTL_QUIET=1 prints only the failing steps (the command and its error reply) and one verdict line, and returns 1 when a
# step failed: the full transcript of a green test is noise for whoever reads the output (an agent pays for every line).
ingame_test() {
  local out bad rc=0
  rcon "ttl discord mute on" >/dev/null
  if [ -n "${TTL_QUIET:-}" ]; then
    out=$(run_test "$INGAME_DIR/${1:?usage: test <name>}.rcon" 2>&1 | plain)
    bad=$(grep -B1 -E "$FAILED_RE" <<<"$out" || true)
    if [ -n "$bad" ]; then printf '%s\n%s: failing\n' "$bad" "$1"; rc=1
    elif grep -q '^skipped: ' <<<"$out"; then echo "$1: skipped"
    else echo "$1: ok"; fi
  else
    run_test "$INGAME_DIR/${1:?usage: test <name>}.rcon"
  fi
  rcon "ttl discord mute off" >/dev/null
  return $rc
}

# Start-up world works: after a restart the canon builds and landmarks whose version changed are taken out and placed
# again, one by one, for minutes, and the server lags while they run (staging 19/11 22:33: dwarf_village re-placed right
# after a deploy, 2 s behind, and arena_dwarven's fixed waits ran out). test-all waits until no build or landmark is being
# placed or queued; one still "pending" but never queued (its boot attempts used up, or the start delay not yet over) is
# waited for TTL_SETTLE_GRACE seconds (300) at most. TTL_SETTLE_WAIT (1800) caps the whole wait; then the tests run anyway.
wait_world_settled() {
  local t0=$SECONDS lines active waiting last=
  while :; do
    lines=$( { rcon "ttl build list"; rcon "ttl landmark list"; } < /dev/null 2>/dev/null | plain)
    active=$(grep -cE '\((placing|queued)\)' <<<"$lines" || true)
    waiting=$(grep -cE ' pending' <<<"$lines" || true)
    if [ "$active" -eq 0 ] && { [ "$waiting" -eq 0 ] || [ $((SECONDS - t0)) -ge "${TTL_SETTLE_GRACE:-300}" ]; }; then
      [ $((SECONDS - t0)) -lt 2 ] || echo "(start-up placements settled after $((SECONDS - t0))s)" >&2
      return 0
    fi
    if [ $((SECONDS - t0)) -ge "${TTL_SETTLE_WAIT:-1800}" ]; then
      echo "(start-up placements still busy after $((SECONDS - t0))s; running the tests anyway)" >&2
      return 0
    fi
    [ "$active/$waiting" = "$last" ] || echo "(waiting for start-up placements: $active placing or queued, $waiting pending)" >&2
    last="$active/$waiting"
    sleep 10
  done
}

# A test fails on command errors, or when a trial test ends the other way than its name says (`*_fail` must fail,
# every other trial test must pass). Tests with an ingame_skip_reason print "skipped (<reason>)" and do not count as
# failing. INGAME_OUT=<dir> keeps each test's output as <dir>/<name>.out. Prints one line per test and
# "<n> failing"; returns non-zero when any test failed. TTL_QUIET=1 leaves out the ok and skipped lines and prints
# "passed: <n>, skipped: <n>" instead (no "<name> " start, so verify does not take it for a failing test's line).
ingame_test_all() {
  local fails=0 passed=0 skipped=0 f name out verdict bot result want why
  wait_world_settled
  rcon "ttl discord mute on" >/dev/null
  for f in "$INGAME_DIR"/*.rcon; do
    name=$(basename "$f" .rcon)
    why=$(ingame_skip_reason "$name")
    if [ -n "$why" ]; then
      skipped=$((skipped + 1))
      [ -n "${TTL_QUIET:-}" ] || printf '%-24s %s\n' "$name" "skipped ($why)"
      continue
    fi
    out=$(run_test "$f" 2>&1 | plain)
    verdict=ok
    if grep -qE 'Unknown or incomplete|Incorrect argument|An unexpected error|ttl: ' <<<"$out"; then verdict="command error"; fi
    if [[ $name == trial_* ]]; then
      bot=$(grep -m1 -oE 'ttlbot spawn [A-Za-z0-9_]+' "$f" | cut -d' ' -f3)
      result=$(log_grep "$bot (passed|failed) the" | tail -1 | grep -oE 'passed|failed' || true)
      want=passed; [[ $name == *_fail ]] && want=failed
      [ "$result" = "$want" ] || verdict="expected $want, got ${result:-nothing}"
    fi
    # `@import` tests (lerfing*.rcon) skip themselves on a world that is not Lerfing's import: not a failure.
    if [ "$verdict" = ok ] && grep -q '^skipped: ' <<<"$out"; then verdict="skipped (not Lerfing's import)"; fi
    case "$verdict" in
      ok) passed=$((passed + 1)) ;;
      skipped*) skipped=$((skipped + 1)) ;;
      *) fails=$((fails + 1)) ;;
    esac
    if [ -z "${TTL_QUIET:-}" ] || [[ $verdict != ok && $verdict != skipped* ]]; then
      printf '%-24s %s\n' "$name" "$verdict"
    fi
    [ -z "${INGAME_OUT:-}" ] || printf '%s\n' "$out" > "$INGAME_OUT/$name.out"
  done
  rcon "ttl discord mute off" >/dev/null
  [ -z "${TTL_QUIET:-}" ] || echo "passed: $passed, skipped: $skipped"
  echo "$fails failing"
  [ "$fails" -eq 0 ]
}
