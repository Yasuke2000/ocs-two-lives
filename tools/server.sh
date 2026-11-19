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
log_grep() { k exec deploy/mc -- grep -E "$(rq "$1")" /data/logs/latest.log; }
# plain, run_test, ingame_test and ingame_test_all; tools/local.sh runs the same tests on this PC.
source "$(dirname "$0")/ingame.sh"
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
  # Tests never post to Discord (mute on for the run), see tools/ingame.sh. test-all takes ~6 minutes.
  test)     ingame_test "${2:?usage: server.sh test <name>}" ;;
  test-all) ingame_test_all ;;
  who) humans ;;
  *) echo "usage: server.sh status|logs [n]|follow|restart|deploy [--force]|rcon \"<cmd>\"|reload|push-scripts|place <name> <dim> <x> <y> <z>|verify <name> [<dim> <x> <y> <z>]|test <name>|test-all|who" >&2; exit 2 ;;
esac
