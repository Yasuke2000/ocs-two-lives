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

## Discord bot

The bot is the server-side mod **Simple Discord Link** (`sdlink` 3.4.5 + CraterLib, config
`pack/config/simple-discord-link/simple-discord-link.toml`). It runs inside the Minecraft server, so there is
no separate bot service. What it does in `#minecraft`:

| Feature | How |
|---|---|
| Chat bridge | game chat → `#minecraft`; Discord messages show in game as `[Discord] name: text` |
| Game events | joins, leaves, deaths and advancements (these two follow the `showDeathMessages` / `announceAdvancements` gamerules), server online / offline |
| Story events | `pack/kubejs/server_scripts/ttl/discord.js`: Life 1 death ("X died in their first life"), rebirth ("X was reborn as a Slime"), Legend verdicts, kills of `major` bosses from `design/data/karma.toml` |
| Status | bot status "N/15 souls in the world", channel topic, slash commands `/playerlist`, `/status`, `/help` |
| Account linking (optional) | in game `/discordverify` gives a code; in Discord `/verify <code>` (or DM the code to the bot) |

Test bots (`TtlBot…`) never reach Discord. A Life 1 death shows twice on purpose: the normal death line
(what killed you) and the story line. Scripts post with `TtlDiscord.post(server, text)`; without the mod or a
token every post is silently dropped.

### Creating the bot (once)

The token is the bot's password. It never goes into git, an issue, a PR or a Discord channel: whoever creates
the bot sends it to David privately, and David puts it into the Kubernetes secret. Leaked? Reset it (step 3)
and update the secret.

1. <https://discord.com/developers/applications> → **New Application**. Name it e.g. "Voice of the World"
   (no "Discord" in the name, Discord refuses that for bots).
2. **Installation**: untick *User Install*, keep *Guild Install*, *Install Link* = None.
3. **Bot**: **Reset Token** → copy the token (shown once). Untick **Public Bot**. Under *Privileged Gateway
   Intents* enable **MESSAGE CONTENT INTENT** (reading chat) and **SERVER MEMBERS INTENT** (account linking).
4. **OAuth2 → URL Generator**: scopes **bot** and **applications.commands**; bot permissions **View Channels**,
   **Send Messages**, **Send Messages in Threads**, **Embed Links**, **Attach Files**, **Read Message History**,
   **Add Reactions**, **Use External Emojis**, **Manage Channels** (only for the automatic channel topic) and
   **Manage Webhooks** (only needed if webhook mode is turned on later; it is off). Open the generated URL,
   pick our Discord server, **Authorize**. (sdlink also prints a ready-made invite link at the top of the server
   log once it has a token.)
5. In Discord create the text channel **#minecraft** and make sure the bot's role can see it, send messages and
   manage it (topic).
6. Discord **User Settings → Advanced → Developer Mode** on; right-click **#minecraft → Copy Channel ID**.

### Putting it on the server (David)

The config ships placeholders that the itzg image fills in from the environment on every start, after the
packwiz install (`REPLACE_ENV_VARIABLES`); sdlink then encrypts the token in the server's copy.

| Placeholder | Env var | Comes from |
|---|---|---|
| `botConfig.botToken` | `CFG_DISCORD_TOKEN` | secret `discord-bot`, key `token` (exists; the bot is the application "MInecraft server") |
| `channelsAndWebhooks.channels.chatChannelID` | `CFG_DISCORD_CHANNEL` | the `#minecraft` channel ID (step 6), a plain value in the Deployment; not secret |

The secret also holds `application-id`; sdlink does not need it. (The secret named `discord` is the ttl-ops
webhook, unrelated.) Env for the `mc` container in the Homelab repo (`apps/ocs-two-lives/`):

```yaml
- name: REPLACE_ENV_VARIABLES
  value: "TRUE"
- name: REPLACE_ENV_PATHS          # only scan the configs, not the whole world folder
  value: /data/config
- name: CFG_DISCORD_TOKEN
  valueFrom: { secretKeyRef: { name: discord-bot, key: token } }
- name: CFG_DISCORD_CHANNEL
  value: "<#minecraft channel ID>" # "0" until #minecraft exists: the bot logs in but posts nowhere
```

Check: `tools/server.sh logs | grep -i -E "sdlink|discord"` shows the bot logging in, and "The server is
online." appears in `#minecraft`.

**The placeholders are used up on the first start**: sdlink rewrites the server's copy (encrypted token,
channel ID filled in), so a later change of either env var does nothing on its own. After changing the token
or the channel ID, or when the server started with sdlink before the env existed ("Failed to connect to
discord" in the log), delete the server's copy and restart; packwiz puts the template back and the image
fills it in again:

```sh
k3s kubectl -n ocs-two-lives exec deploy/mc -- rm /data/config/simple-discord-link/simple-discord-link.toml
tools/server.sh restart
```

### Options (config PR, no secret needed)

- Separate channel for events: put its ID in `channelsAndWebhooks.channels.eventsChannelID` (`"0"` = `#minecraft`).
- In-game `/discord` invite command: set `botConfig.invite.inviteLink`.
- Linking required for everyone (Discord-based whitelist): `accessControl.enabled = true`. Everyone, staff
  included, must then `/discordverify` before they can play; test that the `TtlBot` test players still join.
- Run Minecraft commands from Discord: `[minecraftCommands]`, off.
