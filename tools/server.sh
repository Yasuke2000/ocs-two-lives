#!/usr/bin/env bash
# Operate the homelab staging server (K3s node3, namespace ocs-two-lives) over SSH.
set -euo pipefail

NODE="${TTL_NODE:-root@100.109.28.21}"
NS=ocs-two-lives
k() { ssh -o ConnectTimeout=10 -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS $*"; }
rcon() { k exec deploy/mc -- rcon-cli "$(printf '%q' "$1")"; }

case "${1:-}" in
  status)  k get pods,svc -o wide ;;
  logs)    k logs deploy/mc --tail="${2:-300}" ;;
  follow)  k logs -f deploy/mc --tail=50 ;;
  restart) k rollout restart deploy/mc && k rollout status deploy/mc --timeout=25m ;;
  rcon)    rcon "${2:?usage: server.sh rcon \"<command>\"}" ;;
  reload)  rcon "kubejs reload server_scripts" && rcon "reload" ;;
  test)
    f="$(dirname "$0")/../tests/ingame/${2:?usage: server.sh test <name>}.rcon"
    grep -vE '^\s*(#|$)' "$f" | while IFS= read -r cmd; do echo "> $cmd"; rcon "$cmd"; done ;;
  *) echo "usage: server.sh status|logs [n]|follow|restart|rcon \"<cmd>\"|reload|test <name>" >&2; exit 2 ;;
esac
