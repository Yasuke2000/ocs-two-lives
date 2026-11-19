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
   menu, `/bug`). Release it with `python tools/release_mod.py` (local build, no Actions).
6. **Every mod must have a NeoForge 1.21.1 build** — add only with `/add-mod`. Never add: Epic Fight, Better Combat, Tensura: Predation, a second claims/nations/minimap mod, Mekanism.
7. Client-only mods need `side = "client"` in their `.pw.toml` (`packwiz` sets it from Modrinth metadata; check CurseForge ones).

## Data schema (namespace `ttl`)

| Where | Keys | Holds |
| --- | --- | --- |
| Player persistentData | `ttl.life`, `ttl.l1.start`, `ttl.l1.days`, `ttl.l2.arrived` | Which life, Life 1 timing, rebirth time (arrival grace, `life/mortal_immunity.js`) |
| Player persistentData | `ttl.karma.{valor,order,chaos,craft,faith,longevity}`, `ttl.karma.score`, `ttl.tier` | Raw karma, score, rebirth tier |
| Player persistentData | `ttl.step`, `ttl.wish`, `ttl.offers`, `ttl.race`, `ttl.uniqueOptions`, `ttl.trial.done`, `ttl.trial.passed` | Corridor flow (`life/corridor_flow.js`): step, Last Wish, race offers, Trial result |
| Player persistentData | `ttl.stash`, `ttl.soul.keep`, `ttl.stash.told` | Life 1 death strip (`life/mortal_banned.js`): banned items stashed, soulbound stacks kept, "told" flag |
| Player persistentData | `ttl.soul.gem`, `ttl.soul.book`, `ttl.soul.gemUse` | Soul carryover (`life/carryover.js`): gem issued once, remembered enchantment `<id>\|<level>`, last gem echo (ms) |
| Player persistentData | `ttl.rep` (JSON `{faction: n}`), `ttl.renown`, `ttl.renown.bonus`, `ttl.rep.exalted`, `ttl.rep.decayAt` | Reputation truth, renown mirror and bonus, exalted log, decay clock (`rep/rep.js`) |
| Player persistentData | `ttl.boss.kills`, `ttl.boss.lastkill`, `ttl.boss.core.owed` | Boss kill counts (JSON), credited story kills `{id: millis}` (per-party cooldown), Skill Cores owed (paid at login) |
| Player persistentData | `ttl.uniques`, `ttl.cd.absorb`, `ttl.lastSeen`, `ttl.titles` | Owned uniques mirror, absorb cooldown, last login, titles |
| Player persistentData | `ttl.story.path`, `ttl.story.oath`, `ttl.story.flips`, `ttl.story.acts`, `ttl.story.flags`, `ttl.story.pending` | Story core (`story/story.js`): Oath path (light/dark), Oath time, Atonement/Corruption count, acts and flags (JSON `{id: epoch}`), path the party layer applies at login |
| Player persistentData | `ttl.nation.extra`, `ttl.combat.until`, `ttl.combat.with`, `ttl.absorb.claimed` | Nation claim allowance last applied (`nations/claims.js`); last hit in a duel, challenge or war and its opponent (combat-log rule); awakenings already claimed (`absorb/absorb.js`, mirrored server-side in `ttl.absorb.souls`). Test hooks `ttl.absorb.epfake`, `ttl.absorb.awakefake` |
| Player persistentData | `ttl.arena.back`, `ttl.arena.cd`, `ttl.arena.record` | Arenas (`arena/arenas.js`): where to send the fighter back ("dim x y z yaw pitch"), loot cooldowns (JSON `{"<arena>.<mode>": millis}`), record (JSON `{w, l, d, c, p, f, ds}`) |
| Player persistentData | `ttl.walpurgis.back`, `ttl.walpurgis.invite`, `ttl.walpurgis.by` | Walpurgis Hall (`arena/walpurgis.js`, dimension `ttl:walpurgis`): where the soul entered from, invitation valid until (millis), who invited |
| Player persistentData | `ttl.karma2.{chaos,order,craft,faith}`, `ttl.karma2.spent`, `ttl.roads` | Two roads (`roads/roads.js`, `design/data/roads.toml`): the Life 2 karma ledger (ints) that the NEXT Life 1 judgement adds at `[karma2] mult` and then spends (kept by `/ttl reset`), spent ledgers (JSON, last 10), routes taken (JSON `{counts: {"<id>.<road>": n}, firsts, tide: {day, dark, light}, last}`) |
| Player persistentData | `ttl.artifice` | The Artificer (`artifice/artifice.js`, `design/data/artifice.toml`): JSON `{rank, points, week, wk, craft, workshop: {x,y,z,dim}, metals: {metal: epoch}, jobs: {"<date>:<id>": {id, at}}, done: ["<date>:<id>"], stole, last: {id, coins, points}, constructs, unlocked}` (rank 0 = no charter; jobs = accepted commissions; constructs for WP-A2) |
| Player persistentData | `ttl.ash.victims`, `ttl.necro.testrank` | Necromancer legion (`necro/legion.js`): player kills that paid soul ash (JSON `{victimUuid: epoch}`, O-N4 once per victim per 24 h); test hook rank |
| Player persistentData | `ttl.necro`, `ttl.necro.testplace`, `ttl.necro.testinside` | Necromancer (`necro/necro.js`, `design/data/necro.toml` [points] [entry] [rite] [[rank]] [church] [hunt] [licence]): JSON `{rank, points, wk, week, entry {how (race\|skill\|rite), at}, born, sense, senseAt, zeroAt, marked, licensed, revoked, hunt {at, until, mins, tick, paid}, hunts, lastHunt, title}`; test hooks (licence place rule off; 1/2 = on/off the continent for the Sense) |
| Server persistentData | `ttl.reg.skills.<id>`, `ttl.reg.legendarySlots` | Holders, rarity, history per unique; slots used this era |
| Server persistentData | `ttl.reg.holders` (by UUID), `ttl.reg.names`, `ttl.reg.seen`, `ttl.reg.history`, `ttl.reg.returned`, `ttl.reg.taken`, `ttl.reg.testcaps`, `ttl.era.started`, `ttl.era.titles`, `ttl.era.archive` | Registry v2: holders, last seen, transfer log, pending returns, era titles and archive |
| Server persistentData | `ttl.rep.log`, `ttl.boss.active`, `ttl.boss.seq`, `ttl.boss.lastkill`, `ttl.boss.arena`, `ttl.boss.queue`, `ttl.events.active/last/next/day/hold/muted/loop` | Reputation ring log, live bosses and counter, boss cooldowns (`bosses/boss.js`, WP-W2: mirror `{uuid: {id: millis}}` of the per-soul defeat stamps, last defeat per arena `{arenaKey: {t, id}}` for `arena_gap_minutes`, arena queue `{bossId: [{party, members, by, at, akey, ready}]}`), event director state |
| Server persistentData | `ttl.season`, `ttl.reincarnations`, `ttl.wars.active`, `ttl.council` | Era, rebirth history, war mirror, council |
| Server persistentData | `ttl.story.parties`, `ttl.story.log`, `ttl.story.unlocked` | Story: Oath path per party (`{teamId: {path, oathBy, at}}`), event ring, boss ids unlocked by completed acts |
| Server persistentData | `ttl.party.roster`, `ttl.party.loop` | Party layer (`party/party.js`): members the path lock has accepted per FTB team id, poll stamp |
| Server persistentData | `ttl.nations`, `ttl.nations.loop` | Nations (`nations/nations.js`): JSON `{teamId: {name, owner, home, homeRegion, path, rank, value, treasury, owed, owedWeeks, debuff, ally_to, wars, renown}}` (`debuff` = unpaid-upkeep stage, effects in `nations/upkeep_debuff.js`), never a roster (FTB Teams is the roster); poll stamp. The team id is the same id as in `ttl.story.parties` |
| Server persistentData | `ttl.absorb.pacts`, `ttl.absorb.wars`, `ttl.absorb.souls`, `ttl.absorb.damage` | Absorption (`absorb/absorb.js`): open duel/challenge/bequest pacts (`lia` on a liable one), staff-flagged war pairs, awakenings used per soul UUID (once per soul); duel damage records per liable pact (`absorb/liability.js`). Nation wars come from `TtlNations.atWar(server, keyA, keyB)` |
| Server persistentData | `ttl.arena.state`, `ttl.arena.last`, `ttl.arena.cd.<arena>`, `ttl.arena.test.<arena>`, `ttl.arena.testmode` | Arenas: the match per arena (JSON), last result per arena, challenge cooldown, test placement and test mode |
| Server persistentData | `ttl.world`, `ttl.world.log`, `ttl.world.archive`, `ttl.world.souls`, `ttl.world.unlocked`, `ttl.world.mood`, `ttl.world.loop`, `ttl.world.testmark*` | World Chronicle (`world/chronicle.js`, `design/architecture/world-state.md` §2.2): the record (counts, firsts, phases, milestones, balance/tide, rule, conflicts), ring log, era snapshots, per-soul ledger (compound uuid → deeds), unlocks and moods in force, loop stamp, test mark |
| Player persistentData | `ttl.world.counted`, `ttl.world.seen` | Chronicle backfill version; milestone Voice lines heard |
| Server persistentData | `ttl.domains.missing`, `ttl.domains.testdelay`, `ttl.domains.loop` | Canon domains (`world/domains.js`): residents found missing `{id: {at, seen}}`, the test respawn delay (s), loop stamp. Entity tags `ttl.resident.<id>` (+ `ttl_tempest_resident`, `ttl.npc.<faction>`) mark the kept residents |
| Scoreboards | `ttl.k.*`, `ttl.karma`, `ttl.rep.<faction>`, `ttl.pick`, `ttl.bounty`, `ttl.path` (0 none, 1 light, 2 dark), `ttl.nation.value`, `ttl.world.balance`, `ttl.world.phase.<place>`, `ttl.artifice` (artificer rank 0-4), `ttl.necro` (necromancer rank 0-4) | Display + Easy NPC conditions |
| Stages | `ttl.life1/2`, `ttl.tier.*`, `ttl.race.*`, `ttl.nation.*` (`member`, `owner`, `rank.<id>`), `ttl.boss.t1–t4`, `ttl.faction.<f>.<band>`, `ttl.path.light/dark`, `ttl.story.act1–7`, `ttl.story.<flag>`, `ttl.world.*` (chronicle mirrors; quest tasks only in `world = true` chapters, R7), `ttl.artifice.rank1–4` (every artificer rank reached), `ttl.necro.rank1–4` (cumulative), `ttl.necro.marked`, `ttl.necro.hunted`, `ttl.necro.licensed`, `ttl.title.unbroken` | Quest gating |
| Server persistentData | `ttl.roads.log` | Two roads: ring (200) of routes taken `[{t, p, id, road, w}]` |
| Server persistentData | `ttl.artifice.board`, `ttl.artifice.firsts`, `ttl.artifice.benches` | Artificer: today's commission board `{date, tiers: {"1": [ids]}}`, the server's first maker per metal `{metal: {name, at}}` (never a test bot), Workshop Benches placed `{"dim|x,y,z": {by, name, at}}` |
| Item custom data | `ttl_made_by`, `ttl_made_by_name`, `ttl_cursed` | The maker's stamp on Smithing Bench products (UUID + name, a lore line; commissions with `made_by` count only the soul's own), a blade cursed with a Cursed Whetstone (`artifice/workshop.js`) |
| Server persistentData | `ttl.necro.legions`, `ttl.necro.altars`, `ttl.necro.queue`, `ttl.necro.seq`, `ttl.necro.rested`, `ttl.necro.loop`, `ttl.necro.testcap` | Legion (`necro/legion.js`, `design/data/necro.toml`): compound `{ownerUuid: JSON {n, seen, muster, army, pts, corpses, rest, tiers, last, list: [{id, kind, road, knight, label, at, st (awake/dormant/fallen), dim, x, y, z, altar, nbt (sleeping), tname, named, stand, miss}]}}` (on the server so an offline owner's dead can sleep or fall), Bone Altars `{"dim\|x\|y\|z": {o, n, t}}`, the server-cap queue, last legionnaire id, graves laid to rest, loop stamp, test cap |
| Server persistentData | `ttl.necro.sanctums`, `ttl.necro.first.<tier>` | Player-built tombs (`necro/sanctum.js`): last check per altar `{tier, name, locked, air, open, why, missing, niches, rank, at}`; the first tomb of a tier on the server (one #story line) |
| Server persistentData | `ttl.necro.marked`, `ttl.necro.first.overlord`, `ttl.necro.loop` | The Church's bounty list `{uuid: {n, at, sense}}` (Marked souls, `TtlNecro.bounties`), the first Overlord of the era (one #story line), loop stamp |
| Entity tags | `ttl.legion`, `ttl.legion.<ownerUuid>`, `ttl.lid.<id>`, `ttl.knight` | A legionnaire (Tensura `tensura:skeleton`/`zombie` with a permanent owner), its owner, its record id, a Death Knight |
| Server persistentData | `ttl.choices.active`, `ttl.choices.done`, `ttl.choices.sweep`, `ttl.choices.seq`, `ttl.choices.state`, `ttl.choices.testonline` | Moral-choice scenes (`choices/engine.js`, `design/data/choices.toml`): open and clearing scenes `{sid: {id, dim, x, y, z, region, started, ends, online, mult, n, home, state, route, actor, part, hits, prog, blocks, paid, saw}}`, ring (20) of finished scenes, blocks to restore when their chunk loads, last scene number, `{roll, spawn, last}`, the scale test hook |
| Player persistentData | `ttl.choices`, `ttl.choices.testskills` | Moral-choice scenes: `{done: {event: {good, grey, dark, last}}, tide: {day, dark} (O-C2 balance points today), last}`; test hook skills (`necro`, Tensura skill ids) |
| Entity tags | `ttl.scene`, `ttl.scene.<sid>`, `ttl.role.<role>`, `ttl.cured`, `ttl.freed`, `ttl.wants_name`, `ttl.horde` | Every entity a choice scene spawns (removed with its scene; an orphan is dropped when its chunk loads); a cured villager, a freed hostage, the beast that wants a name, a starving orc. Entity persistentData `ttl.healer` = the soul that last healed it |
| Entity tags | `ttl.npc.guard`, `ttl.gear.r<rev>`, `ttl.test.gear(.<kind>)` | NPC gear (`world/npc_gear.js`, `design/data/npc_gear.toml`): a Tempest resident whose role is a guard (the guard loop sets it on monsters near its post), the gear rev it was equipped with, a test adventurer of `/ttl npcgear testspawn` |
| Item tags | `ttl:soulbound`, `ttl:skill_core`, `ttl:mortal_banned` | Survives rebirth, Skill Cores, banned in Life 1 |
| Item / block tags | `ttl:paths`, `ttl:necro_reagents` (items); `ttl:sanctum`, `ttl:scene` (blocks) | Every player-path item and block (banned in Life 1 via `mortal_banned.toml tags`), soul ash + bone dust; blocks a player-built tomb may count, blocks a choice scene places (`startup_scripts/ttl/blocks.js`) |

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

1. `python tools/validate.py` (JSON/JS/SNBT syntax, packwiz index fresh, forbidden mods absent); `bash tools/check.sh`
   runs it with the fast unit tier and `node --check`. Test in-game on a local server first:
   `tools/local.sh up|sync|test <name>` (docs/server.md "Local testing").
2. Push, restart or reload, then `tools/server.sh logs | python tools/logscan.py` — zero new `[ttl]` errors.
3. Run the matching `tests/ingame/<feature>.rcon` with `tools/server.sh test <feature>`.
4. Player flows: spawn a test player with `/ttlbot spawn <name>`, drive it with `execute as <name> run ...`,
   read its state with `/ttl inspect <name>`, then `/ttlbot remove <name>`. Bots don't move on their own.

## Done means

Validation passes · no new `[ttl]` errors in the log · acceptance test passes · `design/decisions.md` updated.
