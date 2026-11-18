# Sprint 3–4 architecture: carryover, bosses, factions, nations, Legendary, events, economy, ops

18/11/2026 · for the implementation agents. Builds on `registry.js`, `karma/`, `life/`, `discord/`, `TtlData`
(`design/data/*.toml`) and `/ttlbot` tests. Every mod id, class and entity below was read from the jars in the
OCs Prism instance or `design/manas-integration.md`; **verify** marks what an agent must confirm in game first.

## 0. Conventions (all packages)

- **Data-driven:** `design/data/<system>.toml` → `python tools/gen_data.py` → `TtlData.<system>` (add a
  `check_<system>()` validator in `gen_data.py`).
- **Scripts:** `pack/kubejs/server_scripts/ttl/<area>/`, one `TtlXxx` object per file, `// priority:` (data 200 →
  manas 95 → registry 90 → karma 88 → corridor 80 → **new systems 70**, their commands 60), `[ttl]` logs, `var`
  in functions, `Java.loadClass` in try/catch with a null fallback.
- **State:** player facts in `player.persistentData`, server facts in `server.persistentData` as JSON strings
  (pattern: `ttl.reg.holders`, `ttl.hall.*`); **mirrors** in scoreboards (`ttl.rep.<f>`, `ttl.bounty`) for FTB
  Quests / Easy NPC conditions; **gates** as stages (`ttl.boss.t1`, `ttl.faction.<f>.<band>`, `ttl.nation.*`).
- **Region of a position** (nations = canon regions): `Java.loadClass('com.yasuke.ttl.world.CanonMap').grid()`,
  then `grid.charAt(x, z)`; if `'.'`, `grid.ownerCell(x, z)` (coastal water) — the `RegionTitles.regionAt` rule.
  Letters are `pack/config/ttl/canon_regions.json` keys (J Tempest, D Dwargon, R Blumund, F Falmuth, L Lubelius…).
- **Uniques only via `TtlRegistry`** (rule 1). WP5 adds `TtlRegistry.transfer(server, from, to, skill, reason)`:
  revoke + grant + `ttl.reg.history` + `#story` line. Nothing else calls `tensura edit ability` for uniques.
- **Kills:** `EntityEvents.death` is unreliable for mobs here (karma.js); kills are read from
  `minecraft.killed:<id>` objectives polled every 200 ticks (`discord.js checkBosses`). Bosses and bounties reuse it.
- **Commands:** `/ttl <system> …` (Brigadier merges literals); ops need `hasPermission(2)`; every test assertion is
  `/ttl <system> expect <player> <field> <value>` printing `ttl: …` on mismatch (`server.sh test-all` counts it as a
  failure). Tests use `ttlbot spawn TtlBot…`, `execute as`, `@sleep`.
- **Discord:** one `TtlDiscord.post` per story event; roles only via `TtlDiscordRoles`; ids in `discord.toml`.

## S1. Soul carryover (blind spot 1, plan §4)

**Behaviour.** At the Life 1 death inventory, armour, offhand, **ender chest and Curios/backpack slots** are
emptied; only `ttl:soulbound` items survive. Every soul gets one **Soul Gem** (`ttl:soul_gem`, soulbound charm) on
the first Life 1 join; its tooltip shows the verdict. A Craft-heavy Hero+ soul gets one **Remembered
Enchantment** (its best enchanted book re-created).

**Build on.** Curios 9.5.1 `top.theillusivec4.curios.api.CuriosApi.getCuriosInventory(player)` (backpacks sit in
the `back` slot, so clearing Curios parks them), `clear`, KubeJS `StartupEvents.registry('item')`,
`kubejs/data/ttl/tags/item/soulbound.json`, Curios tag `curios:charm`. No Java.

**Data.** Player `ttl.soul.parked` (JSON list of SNBT stacks while in the Corridor), `ttl.soul.gem` (bool);
`design/data/carryover.toml` (`[gem] lore`, `[book] min_tier = "elite"`, `max_levels`).

**Scripts.** `life/carryover.js` (`TtlSoul.park` from `death.js` before `clear`; `restore` from
`corridor_flow.rebirth` after `clear`), `startup_scripts/ttl/items.js`. Hooks: existing player death,
`PlayerEvents.loggedIn` (gem once), `ItemEvents.dropped` (soulbound never drops in Life 1).

**Ties.** Karma tier → book; guide page "What your soul keeps".

**Acceptance `carryover.rcon`.** Bot with `ttl:soul_gem`, an enchanted book in the ender chest and a diamond in a
backpack curio; `kill`; in the Corridor `ttl soul expect <bot> ender empty`, `… curios empty`; after rebirth
`… has soul_gem yes`, `… has diamond no`.

## S2. Boss framework (gated, non-tamable)

**Behaviour.** Bosses are **summoned** (quest, altar NPC or `/ttl boss summon`), never natural. They spawn at a
canon arena with a lore name, boss bar and HP scaled to players nearby; phases announce themselves (enrage,
minions). The kill gives stage `ttl.boss.t<N>` to every contributor within range, rep, coins, a **Skill Core**
from T3+, and a `#story` line. Bosses cannot be tamed, named or captured.

**Build on.** Tensura `tensura:orc_lord`, `supermassive_slime` (T1); `ifrit`, `orc_disaster`, NEB
`tensura_neb:rimuru_clone` "Mimic Echo" (T2); `charybdis`, `gazel_dwargo`, `hinata_sakaguchi`, `tensura_neb:carrion`
(T3); `tensura_neb:luminous_valentine`, `tensura_neb:veldora` (T4). Scaling by `attribute … generic.max_health base
set`, `/bossbar`, LootJS `LootJS.modifiers` per entity, L2Hostility `l2hostility:blacklist` tag (exists), Tombstone:
revert `compat/tombstone_bosses.js` so bosses stay in `tombstone:unhandled_tamable` (decision row).

**Data.** `design/data/bosses.toml`: `[[boss]] id, entity, tier, title, arena = {x, y, z} | landmark, hp_mult,
per_player_mult, range, phases = [{at_hp, minions, count, say}], rewards = {rep = {f = n}, coins = {gold = n},
core = bool}, cooldown_hours`. Server `ttl.boss.active` (JSON {uuid: {id, started, contributors}}),
`ttl.boss.last.<id>`. Player stage `ttl.boss.t<N>`, `ttl.boss.kills` (JSON). Item `ttl:skill_core` (tag
`ttl:skill_core`); `/ttl core open` draws through `TtlRegistry.draw` (WP5).

**Scripts.** `bosses/boss.js` (`TtlBoss.summon/scale/tick/finish`; 20-tick poll of `tag=ttl.boss` entities for
phases and death; killer from objective `ttl.b.<id>` with criterion `minecraft.killed:<entity>`), `bosses/loot.js`,
`bosses/commands.js` (`summon <id> [x y z]`, `list`, `expect <p> stage t1 yes`). Hooks: `ServerEvents.loaded`
loop, `EntityEvents.spawned` (tag + `NoAI` until players arrive), `LootJS.modifiers`.

**Ties.** Rep `TtlRep.add`; quests ch.10–13 `stage ttl.boss.tN`; Discord via `checkBosses` fed from `bosses.toml`;
registry only for Skill Cores.

**Acceptance `bosses.rcon`.** `ttl boss summon orc_lord 100 70 100` → log `[ttl] boss: orc_lord summoned (hp ×…,
1 player)`; `data get entity @e[tag=ttl.boss,limit=1] Health` above vanilla; `kill @e[tag=ttl.boss]` with a bot in
range → `ttl boss expect <bot> stage t1 yes`; `execute if entity @e[tag=ttl.boss]` fails.

## S3. Factions and reputation

**Behaviour.** Launch factions: Tempest, Dwargon, Blumund, Falmuth, Holy Church, Orc Horde (+ hidden Outcast
Society). Reputation −100…+100 in bands Hostile / Unfriendly / Neutral / Friendly / Honored / Exalted. Rebirth
seeds it from race and karma (Craft→Dwargon, Order→Blumund/Church, Chaos→Orcs, Slime/Goblin→Tempest). It rises
from faction quests, bosses, bounties and merit; it falls for killing a faction's NPCs or players inside its
region. Guards attack at Hostile, shops refuse below Unfriendly. `/ttl rep` lists bands.

**Build on.** Easy NPC 7.19 (dialog actions run commands; conditions on objective `ttl.rep.<f>`), FTB Quests
`stage` tasks, the canon grid. Tensura's own scalar `reputation` (`/tensura edit stat <p> reputation`, used by its
dwarf trades: `tensura.message.dwarf.wrong_reputation`): mirror the Dwargon band into it (**verify** the scale in
`PlayerConfig$Reputation`).

**Data.** `design/data/factions.toml`: `[[faction]] id, title, region (letter), capital (landmark), bands =
{hostile = -60, unfriendly = -20, friendly = 20, honored = 50, exalted = 80}, seed = {race = {slime = 20}, axis =
{craft = 15}}, npc_tags, kill_penalty, decay_per_week`. Player `ttl.rep` (JSON {f: int}), one stage
`ttl.faction.<f>.<band>` per faction, scoreboard `ttl.rep.<f>`. Server `ttl.rep.log` (ring, 200).

**Scripts.** `rep/rep.js` (`TtlRep.get/add/set/band/seed/sync`), `rep/guards.js` (NPC kill penalty via
`EntityEvents.death('easy_npc:*')` with `source.actual` — **verify** it fires; fallback: the NPC's own on-death
action `/ttl rep add …`), `rep/commands.js` (`/ttl rep [<p>]`, ops `set|add`, `expect <p> <f> band friendly`).
Hooks: one reserved line in `corridor_flow.rebirth` → `TtlRep.seed`; login sync; weekly decay in a daily loop.

**Ties.** Karma seeds; S2/S7 add; S4 nations start at their home faction's band; quests ch.16 by band; Exalted →
`#story` + a faction quest reward **command** `/ttl rep claimpick` (registry draw, plan §5.4).

**Acceptance `factions.rcon`.** Craft-heavy bot reborn as `dwarf` → `ttl rep expect <bot> dwargon band friendly`;
`ttl rep add <bot> dwargon -80` → `band hostile`, `… dwargon stage hostile` (and `.friendly` gone).

## S4. Player nations and claims (FTB Teams/Chunks, Life 2 only)

**Behaviour.** A nation is an FTB **party** that paid its charter: `/ttl nation found <name>` (Life 2, party
owner, `ttl.boss.t1`, 50 gold coins, ≥ 2 members). Founding fixes the **home region** (owner's position) and the
starting standing with that faction. Claims exist only in the Tensura overworld; the limit grows with rank
(members × `chunks_per_member` + boss tiers). Members get a Discord role; `/ttl nation` shows rank, treasury,
allies, wars. Cap 5 members (O2).

**Build on.** FTB Teams API `dev.ftb.mods.ftbteams.api.FTBTeamsAPI.api().getManager().getTeamForPlayer(p)`,
`Team.isPartyTeam()/getMembers()`, events `PlayerJoinedPartyTeamEvent` / `PlayerLeftPartyTeamEvent` (architectury
`Event` fields; register from JS in try/catch, fallback 5-min roster poll). FTB Chunks:
`claiming.claim_dimension_whitelist = ["minecraft:overworld"]` → **zero code** makes claims Life 2-only (Life 1
is confined to `ttl:mortal_*`); `max_claimed_chunks = 16`; per-nation limits through LuckPerms
`ftbchunks.max_claimed` (XMod Compat ships `LuckPermsProvider`; **verify** the node form in FTB Library).
`ftbteams-server.snbt max_party_size = 5`. Tensura Compat FTB `ftbAllyTensura` keeps subordinates allied.
Warring Nations is **not added** (no verified NeoForge 1.21.1 build; D6 fallback = FTB + KubeJS).

**Data.** Server `ttl.nations` (JSON {teamId: {name, owner, founded, home, rank, treasury, allies, wars}});
stages `ttl.nation.member`, `ttl.nation.owner`; `design/data/nations.toml` (`charter_cost`, `chunks_per_member`,
`ranks`, `member_cap`, `war_window`).

**Scripts.** `nations/nations.js` (`TtlNations.found/dissolve/rank/sync`), `nations/claims.js` (LuckPerms limit on
roster change), `nations/commands.js` (`found|info|ally|war`, `expect <p> member yes`). War v1 = flag + Discord post;
S5 reads it.

**Ties.** Rep seed; S2 T1 gate; S7 charter/upkeep sinks; Discord role + `#wars-and-treaties`; quests ch.8
`stage ttl.nation.member`; BlueMap "Nations" marker set (S8).

**Acceptance `nations.rcon`.** Two Life 2 bots, `execute as … ftbteams party create`, give 50 gold, `ttl nation
found Testland` → `ttl nation expect <bot> member yes`; a Life 1 bot's `execute in ttl:mortal_realm … ftbchunks
claim` fails.

## S5. Legendary tier, absorption, eras

**Behaviour.** A **Legend** soul may pick its wish's **echo** (`TtlWishes.echo`: Predator, Great Sage, Wrath…) at
rebirth if a Legendary slot is free this era (cap 3 in `skills.toml`); the Voice announces "Otherworlder Arrives".
Legendaries move only by **absorption**: a holder of an absorbing unique (`predator`, `gluttony`, `starved`,
`gourmet`, `engorger`) kills a holder in a Labyrinth duel (v1) or while both nations are at war (v2), victim EP ≥
50 % of the killer's, 72 h cooldown — Legendary is stolen, Rare/Common copied if a slot is free. Combat-logging
counts as a kill. Holders inactive 30 days return uniques to the pool. `/ttl era next` bumps `ttl.season`, resets
Legendary slots and era titles only.

**Build on.** `registry.js` (extend), `TtlManas.uniques`, gamerule `skillSteal = false` (Tensura's own plunder
can't bypass; the ttl-portals `SKILL_PLUNDER` veto stays a roadmap item), EP via
`TensuraStorages.getExistenceFrom(p).getEP()` (awaken.js pattern), `EntityEvents.death('minecraft:player')` +
`event.source.actual` (death.js pattern), `PlayerEvents.loggedOut` + `ttl.combat.until`.

**Data.** Server `ttl.reg.legendarySlots` ({era: used}), `ttl.reg.history` (ring {t, skill, from, to, reason}),
`ttl.season`, `ttl.era.started`. Player `ttl.cd.absorb`, `ttl.combat.until`, `ttl.lastSeen`. `skills.toml` adds
`[absorb] skills, min_ep_ratio = 0.5, cooldown_hours = 72, slots_per_era = 2, inactive_days = 30` and `[era] titles`.

**Scripts.** `registry.js` (+`transfer`, `legendarySlotFree`, `returnInactive`, `history`), `absorb/absorb.js`
(`TtlAbsorb.onKill`, rule matrix), `life/corridor_flow.js` (Legend branch in `showUniques`/`rebirth`, grant with
`allowLegendary`), `era/era.js`. Hooks: player death, login/logout, daily inactivity loop.

**Ties.** S4 war flag; S6 "Skill Transfer" / "Otherworlder Arrives"; Discord `#story`, Hall `noteLegend` (exists).

**Acceptance `absorb.rcon`, `legendary.rcon`.** 8-case matrix (killer with/without `predator`, victim Legendary/Rare,
EP ratio pass/fail, cooldown set/clear) driven by `ttl absorb simulate <killer> <victim>` (ops; same code path as
the death hook, because a bot killing a bot through `EntityEvents.death` is **to verify**) → `ttl registry` shows
the move, `ttl absorb expect <killer> cooldown yes`. Legend bot with a free slot sees the echo in
`ttl.uniqueOptions`; full → absent.

## S6. Event director + World's Favor

**Behaviour.** A scheduler fires world events with title, sound, chat and `#story`: weekly **World's Favor** (one
struggling, active Life 2 player picks 1 of 3 blessings), 1–2×/week **Magicule Storm** (one region, 1 h, EP ×2,
tougher mobs), weekly **Calamity Rising** (an S2 boss at an announced arena), **Blood Moon** (Enhanced Celestials 2
→ Valor bonus in Life 1, mob surge in Life 2), bi-weekly **Labyrinth Opens**. `/ttl events mute` silences chat
lines; titles stay.

**Build on.** EC2 Core `dev.corgitaco.enhancedcelestials2core.api.EnhancedCelestialsEvents` /
`LunarEventChangeListener` (**verify** registration; fallback: poll the overworld's lunar state every 100 ticks),
`/title`, `/playsound`, `TtlCorridor.say` (Great Sage worldvoice), gamerule `epGainMultiplier` (storm: 2 then 1),
`/tensura worldData areaMagicule` for the region buff (**verify** arguments), `TtlBoss.summon`.

**Data.** `design/data/events.toml`: `[[event]] id, every = {days|hours}, at_hour, duration_minutes, scope
(region|world|player), announce = {title, chat, clip}, action = {boss | gamerule | favor}`; `[favor] bottom_pct = 25,
min_hours = 5, cooldown_days = 30, require_discord = true, choices = [ep_surge, common_unique, resistance,
protection, relic]`. Server `ttl.events.next` ({id: epoch}), `ttl.events.active`, `ttl.favor.last`. Player
`ttl.events.muted`, `ttl.play.week` (weekly `play_time` delta).

**Scripts.** `events/director.js` (`TtlEvents.schedule/fire/end/announce`, 1200-tick loop, catch-up after
restart), `events/favor.js` (`TtlFavor.pick/offer/apply`; unique via `TtlRegistry.draw`, menu via `ttlmenu`),
`events/storm.js`, `events/moon.js`, `events/calamity.js`, `events/commands.js` (`fire <id>|end|next|mute`, `expect`).

**Ties.** S2 Calamity; karma stat `blood_moon_kills` (new `ttl.s.` objective + active flag); registry (Favor);
Discord + Hall `noteEvent`; storm region named from `canon_regions`.

**Acceptance `events.rcon`.** `ttl events fire magicule_storm` → log `[ttl] events: magicule_storm started in
<region>`, `gamerule epGainMultiplier` = 2, `ttl events expect active magicule_storm`; `end` → 1. `ttl events fire
favor` with three Life 2 bots whose `ttl.play.week` is set → the lowest-EP eligible bot is named; `ttl favor choose
common_unique` as it → `ttl.uniques` non-empty.

## S7. Economy: coins, Adventurer's Guild, merit-lite

**Behaviour.** Currency = Tensura's coins (`tensura:bronze_coin`, `silver_coin`, `gold_coin`, `stellar_gold_coin`;
**no new mod**). Fuze's Free Guild (Easy NPC in Blumund, interim desk in Tempest) posts 3 daily + 2 weekly bounties
(kill N of X in region Y, deliver, visit a landmark) paid in coins + rep; guild ranks F–S. Sinks: nation
charter/upkeep, boss altar fee, Skill Core identification. Merit-lite: `ttl:infrastructure` blocks placed in a
nation's **Public Works** chunk count toward weekly Merit → rep with the home faction + `Builder` title (full
charters/likes/Builder's Economy: O5).

**Build on.** Easy NPC dialog action `/ttl guild board`, Tensura coin items, FTB Chunks
`FTBChunksAPI.api().getManager().getChunk(...)` (**verify** `ChunkDimPos` from JS; fallback: chunk list in
`ttl.nations`), `BlockEvents.placed` (+1-tick rule), `ItemEvents` for deliveries.

**Data.** `design/data/economy.toml` (`[guild] daily = 3, weekly = 2, ranks`, `[[bounty]] id, kind
(kill|deliver|visit), target, count, region, reward = {coins, rep}, weight`, `[sinks] charter, upkeep_per_chunk_week,
core_id`, `[merit] per_block, weekly_cap, rep_per_100`). Server `ttl.guild.board` ({date, daily, weekly}),
`ttl.econ.mint` (weekly faucet/sink counters). Player `ttl.guild` ({rank, done, taken}), `ttl.merit`, scoreboard
`ttl.bounty`.

**Scripts.** `economy/guild.js` (`TtlGuild.roll/take/progress/complete`; kill progress from objectives
`ttl.g.<entity>`), `economy/sinks.js` (`TtlEcon.charge(p, cost)` used by S2/S4/S5), `economy/merit.js`,
`economy/commands.js` (`guild board|take|turnin`, `merit`, `expect`), weekly mint/burn line to the staff channel.

**Ties.** S3 rewards, S4 sinks, S2 fees, Discord `#leaderboard` (rank S), quests ch.18 → 5 tutorial quests + the
live board.

**Acceptance `guild.rcon`.** `ttl guild roll` → 3 daily ids logged; bot `take` a deliver bounty, `give` items,
`turnin` → coins present (`clear <bot> tensura:silver_coin 0` ≥ n), `ttl guild expect <bot> done 1`; a Life 1 bot
gets `ttl: Life 2 only`.

## S8. Ops: Discord hooks, BlueMap, LuckPerms, command log

**Behaviour.** `#story` reports nation foundings, wars, Exalted standings, boss kills, events, skill transfers;
nation members get a Discord role; a BlueMap web map shows canon regions, landmarks, nation claims and active
events, linked from `#welcome`. Staff see every `/ttl` and `/tensura edit` admin command in the staff channel.

**Build on.** sdlink bridges (exist), BlueMap + LuckPerms NeoForge 1.21.1 (both via `/add-mod`; FTB Library reads
LuckPerms through XMod Compat), BlueMap markers from a static file written by `tools/gen_map.py` from
`canon_regions.json` + landmarks (live nation markers only if the MarkerAPI is reachable from scripts — **verify**),
KubeJS `ServerEvents.command` for the log (**verify** in 2101; fallback `NativeEvents` on NeoForge `CommandEvent`).

**Data.** `discord.toml` + `[roles] nation_prefix`, `[channels] wars`; `design/data/ops.toml` (`[cmdlog] prefixes =
["ttl", "tensura edit", "lp", "ftbchunks admin"]`, `[map] marker_sets`). Server `ttl.ops.cmdlog` (ring 500).

**Scripts.** `discord/story.js` (lines called by S2–S7), `discord/roles.js` (+nation role), `ops/cmdlog.js`,
`tools/gen_map.py`, config PRs (LuckPerms groups `player/builder/moderator/admin`, BlueMap, sdlink allow-list).

**Acceptance `ops.rcon`.** `ttl rep set TtlBotX dwargon 10` → `ttl ops expect cmdlog last "ttl rep set"`;
`ttl discordroles <bot> dry expect nation` after a founding; `lp group list` and `bluemap` answer.

## 9. Work packages (one agent each, ≤ ~70 min, no shared files)

Cross-system call sites are **one reserved line** each (named below); an agent edits only its owned files.

| # | Package (value order) | Owns | Deps |
| --- | --- | --- | --- |
| WP1 | **Soul carryover** (S1) | `life/carryover.js`, `startup_scripts/ttl/items.js`, `kubejs/data/ttl/tags/item/soulbound.json`, `design/data/carryover.toml`, `tests/ingame/carryover.rcon`; reserved lines in `life/death.js`, `life/corridor_flow.js` | — |
| WP2 | **Boss core** (S2) | `bosses/boss.js`, `bosses/loot.js`, `bosses/commands.js`, `design/data/bosses.toml`, `compat/tombstone_bosses.js`, `kubejs/data/ttl/tags/entity_type/boss.json`, `tests/ingame/bosses.rcon` | — |
| WP3 | **Reputation core** (S3) | `rep/rep.js`, `rep/guards.js`, `rep/commands.js`, `design/data/factions.toml`, `tests/ingame/factions.rcon`; reserved line in `corridor_flow.rebirth` | — |
| WP4 | **Nations + claims** (S4) | `nations/*.js`, `design/data/nations.toml`, `pack/config/ftbchunks-world.snbt`, `pack/config/ftbteams-server.snbt`, `tests/ingame/nations.rcon` | WP3 (seed; stub if absent) |
| WP5 | **Registry v2**: transfer, Legendary slots, eras, Skill Core open | `registry.js`, `era/era.js`, `design/data/skills.toml`, `tests/ingame/legendary.rcon` | — |
| WP6 | **Legendary pick + absorption** (S5) | `absorb/absorb.js`, `life/corridor_flow.js` (Legend branch), `life/wishes.js`, `life/gamerules.js`, `tests/ingame/absorb.rcon` | WP5; WP4 optional (war flag) |
| WP7 | **Event director + Favor** (S6) | `events/director.js`, `events/favor.js`, `events/commands.js`, `design/data/events.toml`, `tests/ingame/events.rcon` | — |
| WP8 | **Event pack**: storm, Blood Moon, Calamity, Labyrinth | `events/storm.js`, `events/moon.js`, `events/calamity.js`, `events/labyrinth.js`, blood-moon stat in `karma.toml` | WP7, WP2 |
| WP9 | **Guild + sinks + merit-lite** (S7) | `economy/*.js`, `design/data/economy.toml`, Easy NPC preset (Fuze) under `pack/config/easy_npc/`, `tests/ingame/guild.rcon` | WP3; WP4 (sinks: stub) |
| WP10 | **Boss payouts + quests ch.10** | `bosses/rewards.js`, `design/quests/chapter_10_orc_lord.toml` (+ `gen_quests`) | WP2, WP3, WP9 |
| WP11 | **Discord story + roles + cmd log** (S8) | `discord/story.js`, `discord/roles.js`, `design/data/discord.toml`, `ops/cmdlog.js`, `design/data/ops.toml`, `tests/ingame/ops.rcon` | WP3, WP4, WP7 (call sites) |
| WP12 | **LuckPerms + BlueMap + markers** (S8) | `pack/mods/luckperms.pw.toml`, `pack/mods/bluemap.pw.toml` (via `/add-mod`), `pack/config/luckperms/`, `pack/config/bluemap/`, `tools/gen_map.py`, `docs/server.md` section | — (WP4 consumes) |
| WP13 | **Docs**: `master-plan.md` divergence pass, `decisions.md` rows, `roadmap.md` ticks | those three files | after each merge |

Waves: **A** WP1 WP2 WP3 WP5 WP7 WP12 (no deps) → **B** WP4 WP6 WP8 WP9 → **C** WP10 WP11 WP13. Each package ends
with `validate.py` green, `server.sh test <name>` green and a `decisions.md` row.

## 10. Open owner decisions (recommendation first)

| # | Question | Recommendation |
| --- | --- | --- |
| O1 | Currency: Tensura coins only, or add Lightman's Currency? | **Tensura coins** for 10 players; Lightman's only if player shops are wanted in era 2. |
| O2 | Nation member cap and charter cost? | **Cap 5**, charter 50 gold + `ttl.boss.t1`: two nations of friends beat one zerg. |
| O3 | Absorption venue at launch: Labyrinth duels only, or also open PvP between nations at war? | **Duels only** (v1); war PvP after a month of data. |
| O4 | Legendary slots per era: `1 per 10 players` or a flat number? | **Flat 2** now; the ratio rule once > 20 souls. |
| O5 | Merit-lite now vs. full charters/likes/Builder's Economy? | **Merit-lite now**; the full system as its own sprint when builders ask. |
| O6 | Claims Life 2-only by dimension whitelist, or a LuckPerms/stage gate? | **Whitelist** (zero code); LuckPerms limits per nation rank on top. |
