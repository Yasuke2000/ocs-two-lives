#!/usr/bin/env bash
# The in-game bot test runner behind `tools/server.sh test <name>` and `test-all`: it reads tests/ingame/<name>.rcon and
# sends every line over RCON. Sourced by server.sh, which defines `rcon <command>` (prints the server's reply) and `plain`
# (strips colour codes); tests/test_lerfing_tests.py sources it with a fake `rcon`, so everything here runs offline too.
#
# Lines of an .rcon file (blank lines and `#` comments are skipped):
#   <command>                    sent as it is, after the tokens below are expanded
#   @sleep N                     wait N seconds (game time has to pass between some steps)
#   @until N <command>           run the command once a second until its reply holds (no "ttl: ...", "Test failed", command
#                                error), for at most N seconds, and print the last reply: a step that waits on the server
#   @expect N <regex> :: <cmd>   run the command once a second until its reply matches the extended regex (grep -E, per line),
#                                for at most N seconds; prints "ttl: expected ..." when it never does. For commands that
#                                only print (/ttlmap, /ttlregion), which `ttl ... expect` cannot assert
#   @import                      first line of a test that needs Lerfing's imported world: on any other world the test is
#                                skipped ("skipped: ..." is printed, test-all counts it as skipped, not failing). The
#                                world counts as imported when his spawn chest (probe `chest`) stands in the overworld;
#                                TTL_IMPORTED=1 / 0 overrides the check
#
# Tokens (from tests/anchors.env, written by tools/gen_data.py from design/data/anchors.toml and design/data/lerfing/probes.toml):
#   ${anchor:tempest}            "1720 900" (x z)            ${anchor:tempest.x}   ${anchor:tempest.z-19}   (offsets: +N / -N)
#   ${probe:chest}               "-453 73 979" (x y z)       ${probe:chest.y+1}    ${probe:ring_east.x}      ${probe:chest.block}
# An unknown token or an offset on a non-number prints "ttl: ..." and the line is not sent, so test-all counts it as a failure.

FAILED_RE='Unknown or incomplete|Incorrect argument|An unexpected error|ttl: |Test failed'
TTL_ANCHORS_ENV="${TTL_ANCHORS_ENV:-$(dirname "${BASH_SOURCE[0]}")/../tests/anchors.env}"
declare -gA TTL_ANCHORS=()
TTL_ANCHORS_LOADED=

nap() { sleep "$1"; }

load_anchors() {
  [ -n "$TTL_ANCHORS_LOADED" ] && return 0
  TTL_ANCHORS_LOADED=1
  [ -f "$TTL_ANCHORS_ENV" ] || return 0
  local k v
  while IFS='=' read -r k v; do
    case "$k" in '' | '#'*) continue ;; esac
    TTL_ANCHORS["$k"]=${v%$''}   # a checkout with CRLF line ends must not leak a CR into a command
  done < "$TTL_ANCHORS_ENV"
}

# expand_tokens <line>: prints the line with every ${anchor:...} / ${probe:...} replaced; returns 1 (and prints why to stdout,
# as a "ttl: ..." line) for a token it cannot resolve.
expand_tokens() {
  local s=$1 re='\$\{(anchor|probe):([a-z0-9_]+)(\.[a-z]+)?([+-][0-9]+)?\}' tok kind id field off v f
  load_anchors
  while [[ $s =~ $re ]]; do
    tok=${BASH_REMATCH[0]}; kind=${BASH_REMATCH[1]}; id=${BASH_REMATCH[2]}; field=${BASH_REMATCH[3]#.}; off=${BASH_REMATCH[4]}
    if [ -n "$field" ]; then
      if [ -z "${TTL_ANCHORS[$kind.$id.$field]+set}" ]; then
        echo "ttl: unknown token $tok: no $kind.$id.$field in tests/anchors.env (python tools/gen_data.py writes it)"
        return 1
      fi
      v=${TTL_ANCHORS[$kind.$id.$field]}
      if [ -n "$off" ]; then
        if [[ ! $v =~ ^-?[0-9]+$ ]]; then echo "ttl: token $tok: $v is not a number, no offset"; return 1; fi
        v=$((v + off))
      fi
    else
      if [ -n "$off" ]; then echo "ttl: token $tok: an offset needs a field (.x, .y, .z)"; return 1; fi
      v=
      for f in x y z; do
        [ -n "${TTL_ANCHORS[$kind.$id.$f]+set}" ] && v+="${v:+ }${TTL_ANCHORS[$kind.$id.$f]}"
      done
      if [ -z "$v" ]; then
        echo "ttl: unknown token $tok: no $kind.$id in tests/anchors.env (python tools/gen_data.py writes it)"
        return 1
      fi
    fi
    s=${s/"$tok"/$v}
  done
  printf '%s' "$s"
}

# world_imported: 0 when the overworld holds Lerfing's import (his spawn chest is there). The chest chunk is force-loaded
# for the check and released again; a chunk that is still not loaded after a minute counts as imported (the test then runs
# and fails visibly instead of hiding behind a skip).
world_imported() {
  case "${TTL_IMPORTED:-}" in 1) return 0 ;; 0) return 1 ;; esac
  load_anchors
  local x=${TTL_ANCHORS[probe.chest.x]-} y=${TTL_ANCHORS[probe.chest.y]-} z=${TTL_ANCHORS[probe.chest.z]-} block=${TTL_ANCHORS[probe.chest.block]-} out i verdict=
  [ -n "$x" ] && [ -n "$y" ] && [ -n "$z" ] && [ -n "$block" ] || return 0
  rcon "execute in minecraft:overworld run forceload add $x $z" < /dev/null > /dev/null
  for ((i = 0; i < 60; i++)); do
    out=$(plain <<< "$(rcon "execute in minecraft:overworld if block $x $y $z $block" < /dev/null)")
    case "$out" in
      *"Test passed"*) verdict=yes; break ;;
      *"Test failed"*) verdict=no; break ;;
    esac
    nap 1
  done
  rcon "execute in minecraft:overworld run forceload remove $x $z" < /dev/null > /dev/null
  [ "$verdict" != no ]
}

run_test() {
  # The while loop runs in a pipeline subshell: `rcon` must not read the test file, hence `< /dev/null` everywhere.
  local skip=
  grep -vE '^\s*(#|$)' "$1" | while IFS= read -r cmd; do
    [ -z "$skip" ] || continue
    if [ "$cmd" = "@import" ]; then
      if world_imported; then echo "(Lerfing's import is in the overworld)"; else
        echo "skipped: the overworld is not Lerfing's import (@import), see design/architecture/lerfing-import.md 6.3"
        skip=1
      fi
      continue
    fi
    if ! cmd=$(expand_tokens "$cmd"); then echo "$cmd"; continue; fi
    case "$cmd" in
      @sleep\ *) nap "${cmd#@sleep }" ;;
      @until\ *)
        rest=${cmd#@until }; secs=${rest%% *}; c=${rest#* }
        echo "> $c (until it holds, ${secs}s at most)"
        for ((i = 0; i < secs; i++)); do
          out=$(rcon "$c" < /dev/null)
          grep -qE "$FAILED_RE" <<<"$(plain <<<"$out")" || break
          nap 1
        done
        echo "$out" ;;
      @expect\ *)
        rest=${cmd#@expect }; secs=${rest%% *}; rest=${rest#* }
        if [[ $rest != *" :: "* ]]; then echo "ttl: bad @expect line (want: @expect N <regex> :: <command>): $cmd"; continue; fi
        want=${rest%% :: *}; c=${rest#* :: }
        echo "> $c (expect /$want/, ${secs}s at most)"
        got=
        for ((i = 0; i <= secs; i++)); do
          out=$(rcon "$c" < /dev/null)
          if grep -qE "$want" <<<"$(plain <<<"$out")"; then got=yes; break; fi
          [ "$i" -lt "$secs" ] && nap 1
        done
        echo "$out"
        [ -n "$got" ] || echo "ttl: expected /$want/ in the reply to: $c" ;;
      @*) echo "ttl: unknown directive: $cmd" ;;
      *) echo "> $cmd"; rcon "$cmd" < /dev/null ;;
    esac
  done
}
