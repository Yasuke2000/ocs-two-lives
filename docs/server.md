# Test server

The staging server runs on David's homelab (Kubernetes, node3) from the `itzg/minecraft-server` image.
Its settings live in a private infrastructure repo, so they are listed here. To change one, open an
issue with the label `server` or ask David.

| Setting | Value |
|---|---|
| Address (testers) | `molecule-threefold.tun.ply.gg` (playit.gg tunnel) |
| Minecraft / NeoForge | 1.21.1 / 21.1.266 (pinned in `pack/pack.toml`) |
| World | `world-ttl` (reset 17/11/2026 for Two Lives) |
| Memory | 7 GB heap (pod limit 10 GiB), 2 CPU guaranteed |
| Max players | 15 |
| View / simulation distance | 16 / 8 chunks (Distant Horizons draws further) |
| Difficulty | hard |
| Whitelist | on — send David your Minecraft name |
| Spawn protection | off |
| Flight | allowed (Tensura flight skills and wings; off kicks players mid-air) |
| Pack | installed from `main` (`pack/pack.toml`) on every restart |

**Deploys:** a merge to `main` is picked up automatically when nobody is online; the bot tests then
run and the commit gets a ✅/❌ "ttl staging" status. Players online are never kicked for a deploy.

**Bug reports:** `/bug <text>` in game. Reports become GitHub issues (labels `bug`, `from-game`,
`triage`) once the server has a token; until then they are saved on the server in `ttl-reports/`.

## Access from a PC without SSH

`tools/server.sh` and the Python tools (`capture.py`, `import_configs.py`, `import_schem.py`, via `tools/cluster.py`)
use `~/.kube/ocs-two-lives.yaml` when it exists: kubectl straight to the K3s API over Tailscale with the
ServiceAccount `ttl-operator`, which can only reach this namespace (pods, exec, logs, restarts). No SSH means no
Tailscale SSH re-checks. Without the file they fall back to SSH to the node. Ask David for the key; never commit it.

## Backups and restore

The world volume (`mc-data`, Longhorn) is in Longhorn's `default` recurring-job group: a snapshot every night
at 03:00 (7 kept), a backup to the NAS (`nfs://10.0.20.14:/volume1/media/longhorn-backups`) at 04:30 Mon–Sat
(7 kept) and every Sunday at 04:00 (4 kept). Minecraft autosaves every 5 minutes, so a backup is at most a few
minutes behind. ttl-ops posts in Discord when the newest completed backup is older than 2 days.
A world reset (`ttl-reset.txt`) also keeps the old terrain in `world-ttl/ttl-backup/<time>/` on the volume.

Restore (David, Longhorn UI → Backup):
1. Pick the backup of `pvc-d09ea911-…` → **Restore** to a new volume (e.g. `mc-data-restore`), wait until
   it is healthy.
2. Nobody online; scale the server down by pausing ArgoCD auto-sync for `ocs-two-lives` and
   `kubectl -n ocs-two-lives scale deploy/mc --replicas=0`.
3. Either copy the needed folders from the restored volume into `mc-data` with a helper pod that mounts both,
   or create a PV/PVC for the restored volume and point the Deployment's `mc-data` claim at it.
4. Scale back to 1, re-enable auto-sync, check `tools/server.sh logs`.
Only part of the world broken (one dimension)? Restore just that folder (`world-ttl/dimensions/<ns>/<id>` or
the overworld's `region`) from the restored volume; everything else stays.
