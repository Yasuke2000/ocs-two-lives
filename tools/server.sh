#!/usr/bin/env bash
# Operate the homelab staging server (K3s node3, namespace ocs-two-lives).
set -euo pipefail

NODE="${TTL_NODE:-root@100.109.28.21}"
NS=ocs-two-lives
KUBECONFIG_TTL="${TTL_KUBECONFIG:-$HOME/.kube/ocs-two-lives.yaml}"
KUBECTL=$(command -v kubectl || echo "/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")
# kubectl talks to the API directly inside the cluster (ttl-ops) and with the namespace key on a PC
# (ServiceAccount ttl-operator: no SSH, so no Tailscale SSH re-checks); otherwise via SSH to the node.
# rq quotes one argument for the SSH path: that hop goes through a remote shell, kubectl does not.
if [ -n "${TTL_IN_CLUSTER:-}" ]; then
  k() { kubectl -n "$NS" "$@"; }
  rq() { printf '%s' "$1"; }
elif [ -f "$KUBECONFIG_TTL" ]; then
  k() { "$KUBECTL" --kubeconfig "$KUBECONFIG_TTL" -n "$NS" "$@"; }
  rq() { printf '%s' "$1"; }
  TTL_DIRECT=1
else
  k() { ssh -n -o ConnectTimeout=10 -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS $*"; }
  rq() { printf '%q' "$1"; }
fi
rcon() { k exec deploy/mc -- rcon-cli "$(rq "$1")"; }
plain() { sed 's/\[[0-9;]*m//g'; }
# Real players online (test bots excluded), comma-separated; empty when nobody is playing.
humans() {
  local all bots
  all=$(rcon "list" | plain | sed -n 's/.*online: *//p' | tr -d ' 
')
  bots=$(rcon "ttlbot list" | plain | sed -n 's/^Test bots: *//p' | tr -d ' 
')
  tr ',' '
' <<<"$all" | grep -vxF -f <(tr ',' '
' <<<"$bots") | grep -v '^$' | paste -sd, - || true
}
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

case "${1:-}" in
  status)  k get pods,svc -o wide ;;
  logs)    k logs deploy/mc --tail="${2:-300}" ;;
  follow)  k logs -f deploy/mc --tail=50 ;;
  restart) k rollout restart deploy/mc && k rollout status deploy/mc --timeout=25m ;;
  rcon)    rcon "${2:?usage: server.sh rcon \"<command>\"}" ;;
  reload)  rcon "reload" ;;
  # Staging shortcut for KubeJS-only edits: copy pack/kubejs into the server and /reload (seconds).
  # The next restart installs git's version again, so push the change too.
  # Place a structure from the pack anywhere, no player needed: place <name> <dimension> <x> <y> <z>
  place) rcon "execute in ${3:?dimension} run place template ttl:${2:?name} ${4:?x} ${5:?y} ${6:?z}" ;;
  # Compare a placed build with its structure files: verify <name> (corner from the log) or verify <name> <dim> <x> <y> <z>
  verify) shift; python -I "$(dirname "$0")/verify_build.py" "${1:?usage: server.sh verify <name> [<dim> <x> <y> <z>]}" "${@:2}" $([ $# -eq 1 ] && echo --log) ;;
  push-scripts)
    pod=$(k get pods -l app=mc -o name | head -1 | cut -d/ -f2)
    tar -C "$(dirname "$0")/../pack" -cf - kubejs | if [ -n "${TTL_IN_CLUSTER:-}${TTL_DIRECT:-}" ]; then
      k exec -i "$pod" -- tar -C /data -xf -
    else
      ssh -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS exec -i $pod -- tar -C /data -xf -"
    fi
    rcon "reload" ;;
  # raw.githubusercontent.com edges can serve a stale pack.toml for minutes, so a plain restart may
  # install an old pack. Restart until the installed pack hash matches the local pack/pack.toml.
  deploy)
    online=$(humans)
    if [ -n "$online" ] && [ "${2:-}" != "--force" ]; then
      echo "not deploying: $online online (a restart kicks them); use 'deploy --force' to override" >&2
      exit 3
    fi
    want=$(sha256sum "$(dirname "$0")/../pack/pack.toml" | cut -d' ' -f1)
    for attempt in 1 2 3 4 5; do
      k rollout restart deploy/mc >/dev/null && k rollout status deploy/mc --timeout=25m >/dev/null
      got=$(k exec deploy/mc -- cat /data/packwiz.json | grep -o '"packFileHash":{[^}]*}' | grep -o '[0-9a-f]\{64\}')
      if [ "$got" = "$want" ]; then echo "deployed pack ${want:0:12} (attempt $attempt)"; exit 0; fi
      echo "attempt $attempt installed ${got:0:12}, want ${want:0:12}; retrying in 60s" >&2
      sleep 60
    done
    exit 1 ;;
  # Tests never post to Discord (#story, #events): the mute is set for the run and lifted after it, and
  # discord.js drops every post while a test bot is online as well.
  test)
    rcon "ttl discord mute on" >/dev/null
    run_test "$(dirname "$0")/../tests/ingame/${2:?usage: server.sh test <name>}.rcon"
    rcon "ttl discord mute off" >/dev/null ;;
  # Every tests/ingame/*.rcon. A test fails on command errors, or when a trial test ends the other way
  # than its name says (`*_fail` must fail, every other trial test must pass). Takes ~6 minutes.
  test-all)
    fails=0
    rcon "ttl discord mute on" >/dev/null
    for f in "$(dirname "$0")"/../tests/ingame/*.rcon; do
      name=$(basename "$f" .rcon)
      out=$(run_test "$f" 2>&1 | plain)
      verdict=ok
      if grep -qE 'Unknown or incomplete|Incorrect argument|An unexpected error|ttl: ' <<<"$out"; then verdict="command error"; fi
      if [[ $name == trial_* ]]; then
        bot=$(grep -m1 -oE 'ttlbot spawn [A-Za-z0-9_]+' "$f" | cut -d' ' -f3)
        result=$(k exec deploy/mc -- grep -E "$(rq "$bot (passed|failed) the")" /data/logs/latest.log | tail -1 | grep -oE 'passed|failed' || true)
        want=passed; [[ $name == *_fail ]] && want=failed
        [ "$result" = "$want" ] || verdict="expected $want, got ${result:-nothing}"
      fi
      [ "$verdict" = ok ] || fails=$((fails + 1))
      printf '%-24s %s
' "$name" "$verdict"
    done
    rcon "ttl discord mute off" >/dev/null
    echo "$fails failing"
    [ "$fails" -eq 0 ] ;;
  who) humans ;;
  *) echo "usage: server.sh status|logs [n]|follow|restart|deploy [--force]|rcon \"<cmd>\"|reload|push-scripts|place <name> <dim> <x> <y> <z>|verify <name> [<dim> <x> <y> <z>]|test <name>|test-all|who" >&2; exit 2 ;;
esac
