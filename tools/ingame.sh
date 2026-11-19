# In-game test runner for tests/ingame/*.rcon, shared by tools/server.sh (staging) and tools/local.sh (this PC).
# Source it after defining:
#   rcon "<command>"      run one server command and print the reply
#   log_grep "<regex>"    print the lines of the server's logs/latest.log that match (grep -E)
# Then call ingame_test <name> or ingame_test_all. Neither knows which server it talks to.

INGAME_DIR="$(dirname "${BASH_SOURCE[0]}")/../tests/ingame"
# The caller may override this: print a reason to skip test <name> on its server, nothing to run it.
ingame_skip_reason() { :; }
plain() { sed 's/\[[0-9;]*m//g'; }
FAILED_RE='Unknown or incomplete|Incorrect argument|An unexpected error|ttl: |Test failed'

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
ingame_test() {
  rcon "ttl discord mute on" >/dev/null
  run_test "$INGAME_DIR/${1:?usage: test <name>}.rcon"
  rcon "ttl discord mute off" >/dev/null
}

# A test fails on command errors, or when a trial test ends the other way than its name says (`*_fail` must fail,
# every other trial test must pass). Tests with an ingame_skip_reason print "skipped (<reason>)" and do not count as
# failing. INGAME_OUT=<dir> keeps each test's output as <dir>/<name>.out. Prints one line per test and
# "<n> failing"; returns non-zero when any test failed.
ingame_test_all() {
  local fails=0 f name out verdict bot result want why
  rcon "ttl discord mute on" >/dev/null
  for f in "$INGAME_DIR"/*.rcon; do
    name=$(basename "$f" .rcon)
    why=$(ingame_skip_reason "$name")
    if [ -n "$why" ]; then printf '%-24s %s\n' "$name" "skipped ($why)"; continue; fi
    out=$(run_test "$f" 2>&1 | plain)
    verdict=ok
    if grep -qE 'Unknown or incomplete|Incorrect argument|An unexpected error|ttl: ' <<<"$out"; then verdict="command error"; fi
    if [[ $name == trial_* ]]; then
      bot=$(grep -m1 -oE 'ttlbot spawn [A-Za-z0-9_]+' "$f" | cut -d' ' -f3)
      result=$(log_grep "$bot (passed|failed) the" | tail -1 | grep -oE 'passed|failed' || true)
      want=passed; [[ $name == *_fail ]] && want=failed
      [ "$result" = "$want" ] || verdict="expected $want, got ${result:-nothing}"
    fi
    [ "$verdict" = ok ] || fails=$((fails + 1))
    printf '%-24s %s\n' "$name" "$verdict"
    [ -z "${INGAME_OUT:-}" ] || printf '%s\n' "$out" > "$INGAME_OUT/$name.out"
  done
  rcon "ttl discord mute off" >/dev/null
  echo "$fails failing"
  [ "$fails" -eq 0 ]
}
