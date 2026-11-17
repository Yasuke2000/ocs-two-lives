#!/usr/bin/env bash
# Operate the homelab staging server (K3s node3, namespace ocs-two-lives) over SSH.
set -euo pipefail

NODE="${TTL_NODE:-root@100.109.28.21}"
NS=ocs-two-lives
k() { ssh -n -o ConnectTimeout=10 -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS $*"; }
rcon() { k exec deploy/mc -- rcon-cli "$(printf '%q' "$1")"; }

case "${1:-}" in
  status)  k get pods,svc -o wide ;;
  logs)    k logs deploy/mc --tail="${2:-300}" ;;
  follow)  k logs -f deploy/mc --tail=50 ;;
  restart) k rollout restart deploy/mc && k rollout status deploy/mc --timeout=25m ;;
  rcon)    rcon "${2:?usage: server.sh rcon \"<command>\"}" ;;
  reload)  rcon "kubejs reload server_scripts" && rcon "reload" ;;
  # raw.githubusercontent.com edges can serve a stale pack.toml for minutes, so a plain restart may
  # install an old pack. Restart until the installed pack hash matches the local pack/pack.toml.
  deploy)
    want=$(sha256sum "$(dirname "$0")/../pack/pack.toml" | cut -d' ' -f1)
    for attempt in 1 2 3 4 5; do
      k rollout restart deploy/mc >/dev/null && k rollout status deploy/mc --timeout=25m >/dev/null
      got=$(k exec deploy/mc -- cat /data/packwiz.json | grep -o '"packFileHash":{[^}]*}' | grep -o '[0-9a-f]\{64\}')
      if [ "$got" = "$want" ]; then echo "deployed pack ${want:0:12} (attempt $attempt)"; exit 0; fi
      echo "attempt $attempt installed ${got:0:12}, want ${want:0:12}; retrying in 60s" >&2
      sleep 60
    done
    exit 1 ;;
  test)
    f="$(dirname "$0")/../tests/ingame/${2:?usage: server.sh test <name>}.rcon"
    grep -vE '^\s*(#|$)' "$f" | while IFS= read -r cmd; do echo "> $cmd"; rcon "$cmd"; done ;;
  *) echo "usage: server.sh status|logs [n]|follow|restart|deploy|rcon \"<cmd>\"|reload|test <name>" >&2; exit 2 ;;
esac
