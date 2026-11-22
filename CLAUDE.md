# OCS Tensura: Two Lives — Claude Code rules

From-scratch rebuild of OCS Tensura RPG on Minecraft 1.21.1 NeoForge for a 10+ player server.
Every player lives twice: a hardcore human Life 1 in `ttl:mortal_realm`, then a reincarnation
into the Tensura world (Life 2) shaped by Life 1 karma. Full design: `design/master-plan.md`.
Decisions: `design/decisions.md` (append, never rewrite history).

## Pinned versions

| Component | Version | Source |
| --- | --- | --- |
| Minecraft | 1.21.1 | `pack/pack.toml` |
| NeoForge | 21.1.266 | `pack/pack.toml` |
| Tensura: Reincarnated | 2.0.1.5 | Modrinth `Br0kXPwc` |
| ManasCore | 4.0.0.2 | Modrinth |
| KubeJS / Rhino | 2101.7.2-build.381 / 2101.2.7-build.85 | Modrinth |
| FTB Library / Teams / Chunks / Quests | 2101.1.40 / .12 / .24 / .39 | CurseForge |
| BlueMap (server-only) | 5.7 | Modrinth `swbUV1cr` |
| Server image | itzg/minecraft-server:2026.7.1-java21 | Homelab repo |

`pack/mods/*.pw.toml` is the real source of truth; update this table when a pin changes.

## Golden rules

1. **Every unique-skill grant/revoke goes through `kubejs/server_scripts/ttl/registry.js`.** Nothing else calls Tensura skill commands for uniques.
2. **Namespace is `ttl`** — items, tags, persistentData keys, stages, scoreboards, dimensions.
3. **Never hand-edit generated files**: `pack/mods/*.pw.toml`, `pack/index.toml`, `pack/config/ftbquests/quests/**`. Use `packwiz` and `tools/gen_quests.py`.
4. **Never invent mod, race, skill, entity or item IDs.** Look them up in `design/dumps/`. If the dump is missing, run `/dump-ids` first.
5. **No Java** without asking. KubeJS, datapacks and configs first. The one approved Java mod is `mod/`
   (`ttl-portals`: portals, Mortal End dragon fight, test bots, choice menus, `/quietly`, Life 2 rebirth
   menu, `/bug`, the AI build bridge `docs/dev/build-bridge.md`). Release it with `python tools/release_mod.py` (local build, no Actions).
6. **Every mod must have a NeoForge 1.21.1 build** — add only with `/add-mod`. Never add: Epic Fight, Better Combat, Tensura: Predation, a second claims/nations/minimap mod, Mekanism.
7. Client-only mods need `side = "client"` in their `.pw.toml` (`packwiz` sets it from Modrinth metadata; check CurseForge ones).

## Data schema

All `ttl` persistentData keys, scoreboards, stages and tags: [`docs/dev/data-schema.md`](docs/dev/data-schema.md).
Read it before adding or renaming a key, and add a row for every new one.

Karma score per axis = `100 × ln(1 + raw / k)`; total = sum + 0.5 × best axis.

## KubeJS 1.21 conventions

- `player.persistentData.getInt/putInt/getString/putString/getCompound` — never assign properties directly.
- Commands from scripts: `server.runCommandSilent(...)`. Delays: `server.scheduleInTicks(n, cb)`.
- `Java.loadClass` only inside try/catch, with a logged fallback.
- One feature per file under `server_scripts/ttl/<area>/`. Log with the prefix `[ttl]`.
- After `BlockEvents.placed`, mutate the held stack one tick later (NeoForge overwrites it after the event).

## Test server (homelab)

Staging runs on the homelab K3s cluster, node3, namespace `ocs-two-lives`, and installs this pack from `PACKWIZ_URL`
(raw GitHub `main`) on every restart. Manifests: Homelab repo (`Yasuke2000/Homelab`, branch `master`,
`apps/ocs-two-lives/`), synced by ArgoCD. `docs/server.md` has the details.

- `tools/server.sh brief` — one screen: players online, mc pod, memory, ttl-ops, deploy gate. Start here.
- `tools/server.sh logs|status|rcon "<cmd>"|who|test <name>|test-all` — through the `ttl-operator` kubeconfig
  (`~/.kube/ocs-two-lives.yaml`), no SSH. Git Bash: prefix `MSYS2_ARG_CONV_EXCL='*'` for `/data` paths.
- Never restart or deploy while a human is online; ttl-ops deploys gated `main` commits by itself.
- Game: `10.0.20.103:25565` (LAN / Tailscale). Whitelist enforced.

## Testing protocol

1. `python tools/validate.py` (JSON/JS/SNBT syntax, packwiz index fresh, forbidden mods absent); `bash tools/check.sh`
   runs it with the fast unit tier and `node --check`. Test in-game on a local server first:
   `tools/local.sh up|sync|test <name>` (docs/server.md "Local testing").
2. After the merge: `tools/local.sh verify` on the local Lerfing server (the deploy gate, AGENTS.md): ttl-ops deploys
   `main` to staging only once its commit has the status `local-test-all = success`. Then
   `tools/server.sh logs | python tools/logscan.py` — zero new `[ttl]` errors.
3. Run the matching `tests/ingame/<feature>.rcon` with `tools/server.sh test <feature>`.
4. Player flows: spawn a test player with `/ttlbot spawn <name>`, drive it with `execute as <name> run ...`,
   read its state with `/ttl inspect <name>`, then `/ttlbot remove <name>`. Bots don't move on their own.

## Keep Claude usage low

- Waiting (locks, tests, merges, rollouts) is done by a shell loop or ttl-ops, never by an agent that sits idle.
- Set `TTL_QUIET=1` for `tools/local.sh test|verify` and `tools/server.sh test|test-all`: only failures and the summary.
- Read logs with `tail`/`grep` or `tools/logscan.py`, not whole files; one agent at a time for big independent work.

## Done means

Validation passes · no new `[ttl]` errors in the log · acceptance test passes · `design/decisions.md` updated.
