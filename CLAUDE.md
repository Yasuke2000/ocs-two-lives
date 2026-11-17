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
| Server image | itzg/minecraft-server:2026.7.1-java21 | Homelab repo |

`pack/mods/*.pw.toml` is the real source of truth; update this table when a pin changes.

## Golden rules

1. **Every unique-skill grant/revoke goes through `kubejs/server_scripts/ttl/registry.js`.** Nothing else calls Tensura skill commands for uniques.
2. **Namespace is `ttl`** — items, tags, persistentData keys, stages, scoreboards, dimensions.
3. **Never hand-edit generated files**: `pack/mods/*.pw.toml`, `pack/index.toml`, `pack/config/ftbquests/quests/**`. Use `packwiz` and `tools/gen_quests.py`.
4. **Never invent mod, race, skill, entity or item IDs.** Look them up in `design/dumps/`. If the dump is missing, run `/dump-ids` first.
5. **No Java** without asking. KubeJS, datapacks and configs first. The one approved Java mod is `mod/`
   (`ttl-portals`: portals, Mortal End dragon fight, test bots, choice menus, `/quietly`, Life 2 rebirth
   menu, `/bug`). Release it with `python tools/release_mod.py` (local build, no Actions).
6. **Every mod must have a NeoForge 1.21.1 build** — add only with `/add-mod`. Never add: Epic Fight, Better Combat, Tensura: Predation, a second claims/nations/minimap mod, Mekanism.
7. Client-only mods need `side = "client"` in their `.pw.toml` (`packwiz` sets it from Modrinth metadata; check CurseForge ones).

## Data schema (namespace `ttl`)

| Where | Keys | Holds |
| --- | --- | --- |
| Player persistentData | `ttl.life`, `ttl.l1.start`, `ttl.l1.days` | Which life, Life 1 timing |
| Player persistentData | `ttl.karma.{valor,order,chaos,craft,faith,longevity}`, `ttl.karma.score`, `ttl.tier` | Raw karma, score, rebirth tier |
| Player persistentData | `ttl.step`, `ttl.wish`, `ttl.offers`, `ttl.race`, `ttl.uniqueOptions`, `ttl.trial.done`, `ttl.trial.passed` | Corridor flow (`life/corridor_flow.js`): step, Last Wish, race offers, Trial result |
| Player persistentData | `ttl.uniques`, `ttl.cd.absorb`, `ttl.lastSeen`, `ttl.titles` | Owned uniques mirror, absorb cooldown, last login, titles |
| Server persistentData | `ttl.reg.skills.<id>`, `ttl.reg.legendarySlots` | Holders, rarity, history per unique; slots used this era |
| Server persistentData | `ttl.season`, `ttl.reincarnations`, `ttl.wars.active`, `ttl.council` | Era, rebirth history, war mirror, council |
| Scoreboards | `ttl.k.*`, `ttl.karma`, `ttl.rep.<faction>`, `ttl.pick`, `ttl.bounty` | Display + Easy NPC conditions |
| Stages | `ttl.life1/2`, `ttl.tier.*`, `ttl.race.*`, `ttl.nation.*`, `ttl.boss.t1–t4`, `ttl.faction.<f>.<band>` | Quest gating |
| Item tags | `ttl:soulbound`, `ttl:skill_core`, `ttl:mortal_banned` | Survives rebirth, Skill Cores, banned in Life 1 |

Karma score per axis = `100 × ln(1 + raw / k)`; total = sum + 0.5 × best axis.

## KubeJS 1.21 conventions

- `player.persistentData.getInt/putInt/getString/putString/getCompound` — never assign properties directly.
- Commands from scripts: `server.runCommandSilent(...)`. Delays: `server.scheduleInTicks(n, cb)`.
- `Java.loadClass` only inside try/catch, with a logged fallback.
- One feature per file under `server_scripts/ttl/<area>/`. Log with the prefix `[ttl]`.
- After `BlockEvents.placed`, mutate the held stack one tick later (NeoForge overwrites it after the event).

## Test server (homelab)

The staging server runs on the homelab K3s cluster, node3 (side tier), namespace `ocs-two-lives`,
and installs this pack from `PACKWIZ_URL` (raw GitHub `main`) on every restart. Manifests live in
the Homelab repo (`Yasuke2000/Homelab`, branch `master`, `apps/ocs-two-lives/`) — ArgoCD syncs them.

- `tools/server.sh logs|restart|status|rcon "<cmd>"|reload` — wraps `ssh root@100.109.28.21 k3s kubectl …`.
- Script iteration: push to `main` → `tools/server.sh restart` (full pack update) or, for KubeJS-only edits, `tools/server.sh reload` after the restart has pulled them.
- Game: `10.0.20.103:25565` (LAN / Tailscale). Whitelist enforced.

## Testing protocol

1. `python tools/validate.py` (JSON/JS/SNBT syntax, packwiz index fresh, forbidden mods absent).
2. Push, restart or reload, then `tools/server.sh logs | python tools/logscan.py` — zero new `[ttl]` errors.
3. Run the matching `tests/ingame/<feature>.rcon` with `tools/server.sh test <feature>`.
4. Player flows: spawn a test player with `/ttlbot spawn <name>`, drive it with `execute as <name> run ...`,
   read its state with `/ttl inspect <name>`, then `/ttlbot remove <name>`. Bots don't move on their own.

## Done means

Validation passes · no new `[ttl]` errors in the log · acceptance test passes · `design/decisions.md` updated.
