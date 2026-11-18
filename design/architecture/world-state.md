# World state: personal, party and world — no lock-outs, a world that evolves

18/11/2026 · design only, for the implementation agents. Builds on `sprint3-4.md` (§0 conventions apply unchanged),
`story-characters.md` (acts, parties, boss spawn redesign), the story core (`story/story.js`), the boss framework
(`bosses/boss.js`, `bosses/wild.js`), reputation (`rep/`), nations (`nations/`), the event director (`events/director.js`),
the party layer (`party/party.js`), eras (`era/era.js`), absorption (`absorb/absorb.js`) and the canon builds
(`life/builds.js`, `life/tempest.js`, `life/dwargon.js`). Every file:line below was read on 18/11/2026; **verify in game**
marks what an agent must confirm first.

Owner question (Yasuke, paraphrased): *"How do we make sure people don't get locked out of quests, and that the world
evolves along with them? What if there are a few good people and then bad people who overtake or ruin the good
questlines? At this point this becomes kind of an MMO."*

## 0. The five principles, checked against the code

| # | Principle (the lead's proposal) | What the code does today | Verdict |
| --- | --- | --- | --- |
| P1 | Personal/party story is separate from world state; nothing one party does can lock another out; canon characters are immortal anchors; every fight is a per-party instance | Story state is personal (`ttl.story.*`) and quest progress per FTB team: **good**. But a boss id is **server-unique** and its cooldown is **server-wide** (`boss.js:266-269`, `:117-125`, `:271-274`, `:701`): one party's kill of Veldora locks every other party out for 96 h. Statues and Easy NPCs are invulnerable and re-spawned; the named Tempest goblins (Rigurd, Gobta…) are **not** (`tempest.js:234`). Canon builds have **no protection at all** (no claims, `ftbchunks-world.snbt:74 pvp_mode "always"`). | Right principle, **four holes** (§1 H1–H5). |
| P2 | A World Chronicle of aggregated outcomes drives evolution at thresholds, always adding, never removing | Nothing aggregates. The only server-wide story fact is `ttl.story.unlocked` (`story.js:421-429`), additive, read by nobody yet. Builds are placed once per `version` (`builds.js:4-5`, `:560-564`), which is exactly the lever a "Tempest grows" needs. | Agree; §3–§4. One caution: offline players cannot be read from KubeJS, so counts are **backfilled at login**, and milestones must be sticky. |
| P3 | Late joiners play every quest; the past replays as memories; catch-up boosts; party sync | FTB Quests progress is per team, so **joining a progressed party skips everything** (the joiner sees the party's book; rewards are claimed per player — **verify in game**); leaving returns the soul to its own book. Quest text is static SNBT (per locale, `quests.md:159-166`), so "memory" framing cannot live in the quest text per player. | Agree on the goal; the mechanism differs: **echo = Voice lines + boss-bar prefix + NPC lines**, and party join = **skip-ahead**, never replay (§5). |
| P4 | Light vs dark becomes world events; PvP only in nation wars with notice and liability; reputation guards; scarce things protected by consent or refusable-with-cost | Dark deeds only move the dark soul's own reputation. PvP is **open everywhere** in Life 2 (Tensura default; FTB Chunks `pvp_mode always`); war is a flag that only feeds absorption (`nations.js:633-654`, `absorb.js:235-256`), **either** owner can end it at once (`nations.js:656-668`), and the awakening challenge is **not refusable** (`absorb.js:507-529`, by design). | Agree; it is all new code: a rules pass (§6.2), dark-deed events (§6.1), consent routes (§6.4). |
| P5 | MMO-scale needs at 10–30 players | No instancing limits, no queue, no anti-hoarding beyond the registry caps, era resets touch slots and titles only (`era.js:155-170`, correct), `/ttl worldreset` regenerates dimensions (`world_reset.js:6-60`: era-breaking, ops only). | §7. |

Pushed back on: (a) "every fight already summons per party" — it does not, see H2/H3; (b) "replay the past" — not possible inside
a party's quest book, so the design is skip-ahead + echo fights; (c) "PvP only via wars" — today there is no PvP gate at all,
and Life 1 PvP is **open by owner decision** (18/11/2026) and stays out of scope here.

## 1. Problem list: concrete holes in the current code

Severity: **L** = locks a party or soul out of content · **W** = lets one soul damage the shared world · **F** = fairness.

| # | Sev | Hole | Where | How it is closed (work package) |
| --- | --- | --- | --- | --- |
| H1 | W | Rigurd, Rigur, Gobta, Haruna are `tensura:goblin` with `PersistenceRequired` only; any player can kill them, and they only return when `TTL_TEMPEST_VERSION` changes. They also carry no `ttl.npc.tempest` tag, so the kill costs no reputation (`factions.toml:71`, `guards.js:31-41`). | `life/tempest.js:228-234` | WP-W3: `Invulnerable:1b` + `ttl.npc.tempest` tag in the resident NBT, and an idempotent `hardenResidents` pass at load (`data merge entity`) so no re-placement is needed. |
| H2 | L | "`${title} is already out there`": one live instance per boss id, server-wide. A second party at Gazel's throne waits for the first to finish or give up (idle 30 min). | `bosses/boss.js:266-269` | WP-W2: an **arena busy lock with a queue** per boss id; a second party is told its place and pinged when the arena frees; wild instances never count. |
| H3 | L | The boss cooldown (24–96 h) is one server-wide stamp `ttl.boss.last.<id>`; the first party to kill Veldora locks every other party out for four days. Wild rolls read the same stamp (`wild.js:126-127`), and a wild Shizu blocks the story Shizu (`wild.js:121-124`). | `bosses/boss.js:117-125`, `:271-274`, `:701`; `bosses/wild.js:119-137` | WP-W2: the cooldown becomes **per party** (`ttl.boss.lastkill` on every credited soul; a party is on cooldown when any member is), plus a short global `arena_gap_minutes` for loot and chunk settling. Wild and story instances get separate "already out" sets. |
| H4 | W | Tempest, Dwargon and the 19 canon builds have no claim and no block protection: `disable_protection: false` but nobody claims them (`ftbchunks-world.snbt:15`, `:74`); the only recourse is CervLogger rollback by staff. A dark party can dismantle the Tempest green or the Lubelius crypt altar. | `life/builds.js` (records `ttl.build.<name>.box`, read in `wild.js:251-257`), `life/tempest.js`, `life/dwargon.js` | WP-W3: `life/reserve.js`: block break/place, explosions, fire and fluid vetoed inside every recorded build box plus the Tempest and Dwargon boxes for non-ops; the Tempest **growth reserve** (§4) is part of it from day 1. FTB server-team claims are optional on top (**verify** `ftbchunks admin claim_as`). |
| H5 | L | Chapter 4's finale is a `kill tensura:orc_lord` task (team member must land the killing blow); `block_natural` cancels the camp's own spawns (`NATURAL` includes `structure`), so the only Orc Lord is the summoned one, started by typing `/ttl story fight orc_lord` by hand (open to players, `story/commands.js:202`) — nothing in the book says so. | `design/quests/chapter_4_orc_lord.toml:150-154`; `bosses.toml:127`; `boss.js:926-945` | WP-W11: a "The camp's altar" quest with the `command` reward `ttl story fight orc_lord`, and the finale task becomes `stage ttl.defeated.orc_lord` (credit for the whole party, boss.js `:768`). |
| H6 | L | The path lock kicks a joiner of the other Oath (by design, O2). Combined with team quest progress, a light soul can never fight beside a dark friend and get credit: boss credit only flows through the FTB party (`boss.js:428-458`, `:728-757`). | `party/party.js:229-244` | WP-W7: **raid groups**: a temporary cross-party group for one fight that gets boss credit; the FTB party stays the quest/path object. |
| H7 | F | War absorption: a declared war goes active after 24 h with **no consent** of the defender, any kill then moves a Legendary with no EP gate (`[absorb.war] min_ep_ratio 0`) — but the **defender's owner can end the war at once** (`endWar` only checks the caller is an owner of one side), so the route is both exploitable (declare, strike in the first minute after `active_at`, done) and toothless (end it). | `nations/nations.js:634-668`; `absorb/absorb.js:235-256`, `:276`; `skills.toml [absorb.war]` | WP-W8: war needs the defender's **acceptance** (or the notice *and* an active defender nation); ending an active war is a **surrender** with a treasury cost; absorption in war only during the war window (§6.2). |
| H8 | F | A holiday of 30 days returns every unique to the pool, Legendary included, with no warning. | `registry.js:598-625`; `skills.toml [registry] inactive_days = 30` | WP-W8: 45 days, a `#story` warning at 30 and a Voice line at login; owner decision O-W5. |
| H9 | F | Nothing stops one soul holding several of the Ten (`canHoldLegendary` only counts distinct holders). | `registry.js:106-111` | WP-W8: `max_legendary_per_holder` (recommend 2). |
| H10 | L | The Gazel encounter is `spawn.kind = "statue"` but nothing implements a statue swap; the fight Gazel is summoned into the throne room next to the seated statue (`dwargon.js:278-289` re-seats him within seconds). Harmless, but two kings in one room. | `bosses.toml:409`; `bosses/boss.js` (no `statue` handling) | WP-W2: `kind = statue` means "the statue steps aside": the ensure loop skips the seat while an instance of that boss is active in the arena. |
| H11 | W | The Oath record of a party never dies with the party (`ttl.story.parties`), only `party.js:327-336` prunes its roster; a re-created party with a reused id (FTB ids are UUIDs, so practically never) — low. | `story/story.js:342-346` | WP-W1 prunes it in the chronicle sync. |
| H12 | F | The weekly World's Favor is the only catch-up; the master plan's "Reincarnation Grace ×1.5 EP for 14 days" (§9) is not built. | `events/favor.js` | WP-W6. |
| H13 | W | `/ttl worldreset` regenerates dimensions and re-places Tempest/Dwargon/builds; it is the right tool between eras and the wrong one during one. | `life/world_reset.js:6-60` | Docs rule in §7.4; no code. |

Not holes (verified): `ttl.defeated.<id>` and `ttl.boss.t<n>` are per-player stages (`boss.js:766-768`); `kill_rep` is charged per credited
soul (`story.js:475-495`); NPC lines pick on the soul's own act and path (`story.js:524-548`); acts are sequential per soul
(`story.js:414`); `ttl.story.unlocked` only adds (`story.js:421-429`); eras keep quests, races, skills and the world
(`era.js:154-170`); the director only bypasses boss cooldowns on a manual fire (`director.js:401`).

## 2. The model: three layers of state

```
PERSONAL  (player persistentData, player stages)           the soul's truth: path, acts, flags, defeats, kills, rep, renown
PARTY     (FTB party team + ttl.story.parties + FTB TeamData)  the Oath path, quest completion, nation, boss-credit roster
WORLD     (server persistentData ttl.world*)               aggregates of the two above + phases + sticky milestones + balance
```

Rules (R-numbers continue `story-characters.md`):

- **R5 — one-way flow.** Personal and party events are *counted* into the world; the world never writes personal story
  state. The only things the world hands a soul are additive: a stage `ttl.world.*`, a Voice line, an event, a boost.
- **R6 — no removal.** No script removes `ttl.story.*`, `ttl.defeated.*`, `ttl.boss.*`, `ttl.faction.*` from a soul because of
  what *another* soul did. (Today's exceptions are the soul's own: `/ttl reset`, Atonement/Corruption swapping `ttl.path.*`,
  the honour-duel flag spent by its own kill.) `tools/validate.py` greps the scripts for `stages.remove('ttl.story` outside
  `story.js` and fails.
- **R7 — quests gate on personal/party stages only.** `ttl.world.*` stages may appear as tasks only in chapters marked
  `world = true` (new chapters that the chronicle unlocks), never as a `deps`/stage gate of chapters 0–13. `gen_quests.py`
  enforces it (WP-W11).
- **R8 — capacity, not availability.** Any global limit on fights (instances, arenas, wild caps) is a queue with a place
  and an ETA, never a "done for today". The per-boss cooldown is per party.
- **R9 — anchors.** Canon characters are invulnerable, kept by an ensure loop, and stand inside a reserve nobody but ops can
  edit. A fight is always a *separate* summoned entity (`[[boss]]`), never the anchor.
- **R10 — sticky, additive milestones.** A world milestone, once reached, stays reached for the era. The only reversible
  world number is `balance` (light/dark), and it only chooses *which* events and flavours are added.

### 2.1 Storage keys

| Where | Key | Holds | Written by |
| --- | --- | --- | --- |
| Server | `ttl.world` (JSON, ≤ 60 KB) | `{v, era, since, counts, firsts, phases, milestones, balance, tide, active}` (§3.1) | `world/chronicle.js` only |
| Server | `ttl.world.log` (ring, `log_size`) | `{t, kind, who, data}` chronicle entries | chronicle |
| Server | `ttl.world.archive` | one `ttl.world` snapshot per finished era (cap 10) | `TtlEra.next` reserved line |
| Server | `ttl.world.loop` | loop stamp (reload-safe, the director pattern) | chronicle |
| Server | `ttl.boss.queue` (JSON `{bossId: [{party, by, at}]}`) | arena queue per boss id | boss.js (WP-W2) |
| Server | `ttl.raid.groups` (JSON `{raidId: {leader, members, boss, until}}`) | raid groups | `party/raid.js` |
| Player | `ttl.world.counted` (int) | chronicle schema version this soul's past was counted at | chronicle (login backfill) |
| Player | `ttl.world.seen` (JSON `{milestoneId: epoch}`) | milestones announced to this soul (one Voice line each) | chronicle |
| Player | `ttl.boss.lastkill` (JSON `{bossId: epoch}`) | per-soul defeat stamps (the per-party cooldown reads every member's) | boss.js |
| Player | `ttl.catchup` (JSON `{grace_until, synced_to, offered}`) | catch-up state | `story/catchup.js` |
| Player | `ttl.pvp.warned` (epoch) | last "no PvP here" message (rate limit) | `pvp/pvp.js` |
| Stages | `ttl.world.phase.<place>.<phase>` (e.g. `ttl.world.phase.tempest.town`), `ttl.world.milestone.<id>`, `ttl.world.act<n>`, `ttl.world.tide.light` / `.dark` | world facts mirrored on every online Life 2 soul (login + `sync_ticks`) | chronicle `sync` |
| Scoreboard | `ttl.world.balance`, `ttl.world.phase.tempest` (0 village, 1 town, 2 city) | Easy NPC conditions, `/ttl inspect` | chronicle `sync` |

Mirrors follow the R3 pattern: truth in `ttl.world`, stages and scoreboard rewritten together by `TtlChronicle.sync(server, player)`.
Stages are per player, so a world stage is simply put on every soul; a soul that logs in later gets it at login.

### 2.2 How each consumer reads the world

| Consumer | Reads | Through |
| --- | --- | --- |
| Quests (world chapters only, R7) | `ttl.world.*` stages | FTB `stage` task, `team_stage = false` |
| NPC dialogue | phases, tides, milestones | `story.toml [[npc.talk]] world = { tempest_at_least = "town", tide = "dark", milestone = "first_demon_lord" }` (WP-W11 extends `TtlStory.pick`) |
| Builds | phases | `TtlTempest.phase(server)` → which footprint ring to place (§4) |
| Events | milestones, tide | `events.toml [[event]] requires = { milestone = "act5_reached" }` + `unlock_events` effects; the director's `blocked()` gains one `canStart` check (reserved line) |
| Factions | `mood` | `TtlRep.mood(f)`: a band offset for guards and shops only (`guardsHostile`/`shopOpen` read `band + mood`), never the stored reputation |
| Discord / BlueMap | the export | `/ttl world export` JSON + `TtlDiscord.post` lines |

## 3. The World Chronicle

### 3.1 Data (`ttl.world`)

```json
{ "v": 1, "era": 1, "since": 1763400000000,
  "counts": {
    "souls": 23, "active30": 14,
    "oaths": { "light": 9, "dark": 5 },
    "acts": { "light": { "1": 9, "2": 6, "3": 3 }, "dark": { "1": 5, "2": 4, "3": 1 } },
    "flips": { "atonement": 1, "corruption": 0 },
    "flags": { "regicide": 2, "honour_duel": 3, "hero": 0, "demon_lord": 0, "charybdis_woke": 1 },
    "kills": { "orc_lord": 7, "gazel_dwargo": 4 }, "wildKills": { "shizu": 1 },
    "nations": 3, "wars": 1, "raidsWon": { "defenders": 2, "raiders": 0 },
    "legendary": { "holders": 2, "moves": 1 }
  },
  "firsts": { "orc_lord": { "by": "Yasuke", "party": "Lancelot's party", "at": 1763500000000 } },
  "phases": { "tempest": "village" },
  "milestones": { "act2_reached": 1763600000000 },
  "balance": 7, "tide": "",
  "active": { "rebuilding": 0 }
}
```

- `counts.*` are **souls** (distinct players), not parties: a party of five that finishes Act III counts five. Every act
  completion, Oath, flip, flag, kill and nation event is one `TtlChronicle.note(server, kind, player, data)` call from a
  **reserved line** in the owning script (story.js `applyOath/act/flip/flag`, boss.js `finish`, nations.js
  `found/declareWar/endWar/dissolve`, registry.js `log` for Legendary grants/transfers, the raid event's end). Guarded
  with `typeof TtlChronicle`, so every owner script keeps working without it.
- `active30` = souls seen in Life 2 in the last 30 days (from `ttl.lastSeen`, read at login and in the 5-min sync of online
  players). Thresholds use it (§3.2).
- `balance` is a clamped integer (`-100..100`): light deeds add, dark deeds subtract (weights in TOML), and it drifts toward 0
  by `decay_per_week`. `tide` = `light` above `+tide_at`, `dark` below `-tide_at`, else `''`.
- **Backfill.** KubeJS cannot read an offline player's persistentData, so the chronicle counts each soul **once at login**
  (`ttl.world.counted < v`): acts, flags, `ttl.boss.kills`, Oath. The rings `ttl.story.log` and `ttl.reg.history` seed
  firsts on first boot. Counts converge as people log in; milestones are sticky (R10), so a late backfill can only reach more
  of them, never un-reach one.

### 3.2 `design/data/world.toml` (new; `gen_data.py check_world()`)

```toml
[chronicle]
log_size = 300
sync_ticks = 6000            # world stages/scoreboard rewritten on online souls (also at login)
active_window_days = 30
discord = true               # one #story line per milestone and tide change (TtlDiscord.post; muted in tests as today)

# A threshold is `souls` (absolute) OR `pct` of active30, whichever is HIGHER, so it scales from 10 to 30 players.
[threshold]
souls = 3
pct = 25

[balance]
weights = { oath_light = 2, oath_dark = -2, act_light = 1, act_dark = -1, atonement = 3, corruption = -3,
            regicide = -3, honour_duel = 1, charybdis_woke = -2, hero = 10, demon_lord = -10,
            raid_defended = 2, raid_sacked = -3, uprising_put_down = 2, uprising_won = -3 }
decay_per_week = 2
tide_at = 25                 # |balance| at which a tide starts; it ends at tide_end
tide_end = 10

# Milestones are sticky and additive. `when` keys are ANDed:
#   acts = { act = n }                 (threshold souls finished act n, any path)
#   acts_path = { act = n, path = x }  (… on one path)
#   flags = { <flag> = n }             (n souls hold the flag)
#   kills = { <boss> = n }             (n defeats, any party)
#   nations = n · wars = n · balance_at_least = n · balance_at_most = n · milestone = "<id>" · era_days = n
# `effects`: stage (to every Life 2 soul), phase = { <place> = <phase> }, unlock_events = [ids], mood = { <faction> = ±bands },
#   title (to all online), voice (one Voice line per soul, once), story (#story line), chapter = "<quest chapter key>"
#   (the chapter's first quest has a stage task on this milestone's stage: R7).
[[milestone]]
id = "act2_reached"
when = { acts = { act = 2 } }
effects = { stage = "ttl.world.act2", story = "The Armed Nation has taken the measure of the newcomers: Act II is written into the world." }

[[milestone]]
id = "tempest_town"
when = { acts = { act = 3 } }
effects = { phase = { tempest = "town" }, stage = "ttl.world.phase.tempest.town", unlock_events = ["horde_raid"],
            title = "Tempest grows", voice = "Tempest has grown into a town. Roads, walls, a market: the world remembers who stood here.",
            story = "Tempest has grown into a town." }

[[milestone]]
id = "act5_reached"
when = { acts = { act = 5 } }
effects = { stage = "ttl.world.act5", unlock_events = ["falmuth_invasion_repeat", "holy_hunt"] }

[[milestone]]
id = "tempest_city"
when = { acts = { act = 6 } }
effects = { phase = { tempest = "city" }, stage = "ttl.world.phase.tempest.city", unlock_events = ["walpurgis_monthly"],
            story = "Tempest is a city. The council of the Jura-Tempest Federation sits in its own hall." }

[[milestone]]
id = "first_demon_lord"
when = { flags = { demon_lord = 1 } }
effects = { stage = "ttl.world.milestone.first_demon_lord", unlock_events = ["harvest_festival"], mood = { holy_church = -1 } }

[[milestone]]
id = "first_true_hero"
when = { flags = { hero = 1 } }
effects = { stage = "ttl.world.milestone.first_true_hero", unlock_events = ["hero_ascension"], mood = { holy_church = 1 } }

[[milestone]]
id = "dwargon_pact"
when = { flags = { honour_duel = 3 } }      # three honour duels: the Dwarf King trusts Tempest's friends
effects = { mood = { dwargon = 1 }, unlock_events = ["dwarven_caravan"], story = "Dwargon and Tempest exchange envoys." }

# Tides are reversible and only ADD. A dark tide adds raids and the Church's hunt; a light tide adds the Outcast uprising
# and the horde's counter-raid, so both sides always have something to answer.
[tide.dark]
unlock_events = ["horde_raid", "holy_hunt"]
mood = { tempest = -1 }
story = "A dark tide rises over Jura."

[tide.light]
unlock_events = ["outcast_uprising"]
mood = { outcast = -1 }
story = "The light holds Jura. The Outcasts stir in the shadows."
```

### 3.3 Effects, precisely

| Effect | Does | Never does |
| --- | --- | --- |
| `stage` | `player.stages.add` on every online Life 2 soul now and on every login (idempotent) | remove a stage |
| `phase` | writes `phases.<place>` and calls the place's `phase` hook (Tempest: `TtlTempest.grow(server, phase)`, §4) | demolish anything |
| `unlock_events` | adds ids to `ttl.world.unlocked`; `events.toml` events with `requires = { unlocked = true }` only schedule once listed | schedule something at once (the director keeps its caps) |
| `mood` | a band offset table `ttl.world.mood` read by `TtlRep.guardsHostile/shopOpen` and `[[npc.talk]] faction` conditions | touch `ttl.rep` of anyone |
| `chapter` | the named world chapter becomes reachable (its first quest has a stage task on this milestone) | hide or reset a chapter |
| `title`/`voice`/`story` | announcements; `voice` once per soul (`ttl.world.seen`) | — |

Milestone evaluation runs in the 5-min sync and after every `note`; firing is logged `[ttl] world: milestone <id> reached
(<counts>)`, and `/ttl world milestone fire <id>` (ops) forces one for tests and launches.

## 4. Tempest grows: build versions as phases

Today `TTL_TEMPEST_VERSION = 3` (`tempest.js:28`) places the whole village with terrain; the generic placer does the same per
`design/builds/*.toml` version (`builds.js:4-5`, `:560-564`). Growth reuses that lever with one change: **a phase places a ring,
not the whole town**.

- **Blueprints.** `blueprints/tempest.py` stays the village (phase 0). New `blueprints/tempest_town.py` and `tempest_city.py`
  are **rings** around it: structures whose footprint excludes the village core (walls, market, barracks, council hall, inn,
  the Federation hall for the city). Same anchor (world 0, 0 = blueprint (45, 57)). `tools/build_structures.py` emits
  `tempest_town_ring.nbt`, `tempest_city_ring.nbt` and `generated/tempest_footprint.js` gains `rings: {town: {...}, city: {...}}`.
- **Core-preserving rule.** Every quest anchor of chapters 2 and 7 (Rigurd's hut (22, −39), the campfire (22, −30), the green
  (0, −7), the south gate (0, 23), the Outcast contact (0, 52), the crossroads) keeps its coordinates in every phase.
  `tests/test_tempest_phases.py` (offline) reads the chapter TOMLs' `location` tasks inside the Tempest box and asserts each
  lies in the village core or in a ring's declared "kept open" list. The arena (0, 0, r 48) stays the green.
- **Reserve.** The city ring needs room: a square `growth_reserve = 192` blocks around 0, 0 (knob in `design/data/world.toml
  [tempest]`) is part of the reserve of WP-W3 from day 1, so nobody builds or claims where the walls will stand. Players who
  want to live in Tempest get a `tempest_quarter` ring in the city phase: plots inside the walls that `/ttl merit works mark`
  turns into Public Works (merit ×3 lives there, master plan §13) — additive housing, not a claim.
- **Placement.** `TtlTempest.grow(server, phase)`: forceload the ring, place the ring NBTs with the village's own slab/terrain
  helpers (only under the ring), spawn the phase's residents from `tempest_extras.rings.<phase>.residents` (hardened, H1),
  record `ttl.tempest.phase = <phase>` and `ttl.tempest.phase.<phase>.at`. A failed terrain pass is retried like today (`place`
  logs `terrain FAILED`). Nothing of a lower phase is removed; a ring may *replace* the palisade with a wall only where the
  blueprint says so (explicit `replace` boxes, validated against the core-preserving list).
- **NPC spots.** `npcs.toml [[spot]]` gains `min_phase = "town"`; `TtlGuildNpc.active` returns false below it; the spot
  signature includes the phase so the existing re-spawn logic handles it. Benimaru moves from the longhouse to the barracks?
  **No**: canon spots stay, new phases add spots (the council hall gets a second Rigurd? No — one entity per character:
  R1). New characters only (guards tagged `ttl.guard.tempest`, which finally gives `guards.js:72-94` something to aim).
- **Dwargon** does not grow (it is a finished city in canon). Its evolution is **mood** (`dwargon_pact`) and additive
  decorations (`dwarven_caravan` event: a caravan on the Dwargon road with trades). Regicide never damages Dwargon for
  anyone but the regicide (`kill_rep`, personal) — the statue is re-seated (`dwargon.js:278-289`).
- **Dark server?** The town and city come at act 3 / act 6 **whatever the balance**; the tide only chooses the banner
  decorations (`tempest_city_light_banners` / `_dark_marks`, small overlay structures placed by the tide effect and left in
  place when the tide turns — the city carries its history).
- **Echo for late joiners.** A soul in Act I walking into the city still gets chapter 2's "bring logs for Mildo": the text
  is the memory, the hand-in still works, and Mildo's `[[npc.talk]] world = { tempest_at_least = "town" }` line says
  "You bring me the logs the way the first souls did. The Great Sage keeps the memory; I keep the house."

## 5. Catch-up, echoes and party sync

### 5.1 What a late joiner gets without any code

Every quest chapter stays, every boss is a per-party instance (after WP-W2), every NPC line is picked on the soul's own act
and path. A soul reborn in month six plays Acts I–VII in a city instead of a village and that is the design: the world
moved, the story did not.

### 5.2 Echoes (the Great Sage framing)

An **echo** is any fight whose boss already has a `firsts` entry in the chronicle. Mechanically identical (same `[[boss]]`
numbers, scaled to the party), framed as a memory:

- `TtlStory.fight` (reserved line) prefixes the Voice: *"Great Sage: reproducing the memory of the battle at Lake Siss. The
  outcome is yours alone."*; the boss bar reads `Echo · Charybdis, the Whirlpool Calamity` (title prefix `echo_prefix` in
  `bosses.toml [framework]`, empty = off); `#story` says "… fell to X (an echo)".
- `echo_hp_mult = 0.85` (knob) on echo instances for a party whose **highest** act is below the boss's act: a small
  catch-up bonus, never for the first kill, never for a party that is already there.
- Wild bosses are never echoes (they are the world's own).

### 5.3 Catch-up boosts (`design/data/world.toml [catchup]`)

```toml
[catchup]
late_after_days = 14        # reborn this long after the era began …
behind_acts = 2             # … and this many acts behind the world's highest reached act (ttl.world.act<n>) = "late"
ep_grace_pct = 50           # Reincarnation Grace: this much extra on every EP gain for ep_grace_days (master plan §9)
ep_grace_days = 14
favor_weight = 2            # a late soul counts twice in the World's Favor draw
rep_welcome = 10            # with every faction that has a positive mood (the world's friends befriend the newcomer)
coins = { silver = 20 }     # once, at the first login after the late check
```

EP grace is a 5-min loop in `story/catchup.js`: it samples EP (`TensuraStorages.getExistenceFrom(p).getEP()`, the absorb.js
pattern) and adds `pct` of the positive delta with `tensura edit stat <p> ep current add <n>` (the command favor.js already
uses for `ep_surge`; **verify in game** that repeated adds are stable). The Favor weight is one reserved line in
`favor.js eligible()`.

### 5.4 Party sync: joining friends who are further

FTB Quests progress is per team. The rules, in order:

1. **Joining a progressed party = skip-ahead, not replay.** The joiner's book becomes the party's; the party layer already
   gives the party's Oath (`party.js:245-254`). `story/catchup.js` (reserved line in `admit()`) then offers once, on screen:
   *"Walk the memories later, or stand where your friends stand?"* — **Skip ahead** calls `TtlStory.act(…, {force, quiet,
   catchup: true})` for every act below the party leader's highest; with `catchup: true` the act pays **no** reputation,
   `renown_pct` (50) of the renown, no `unlock_bosses` (already unlocked) and never a flag (`hero`, `demon_lord`, `regicide`
   stay earned). **Walk** leaves acts personal; the joiner can still claim the party's unclaimed quest rewards (FTB claims
   are per player; **verify in game**) and plays fights as echoes with the party. Either way nothing is lost: the party's
   quests are done, the soul's own acts are what NPCs read.
2. **Leaving** returns the soul to its own book and its own acts (FTB keeps the personal `TeamData`; **verify in game**,
   `story-characters.md` §4.2 already lists it).
3. **A soul of the other Oath** is still turned away (O2). It fights beside the party through a **raid group** (§5.5) and
   plays its own quests in its own party (a party of one is fine).
4. **Boss credit** needs presence (hit, `presence_secs`, in range at death) as today; a skip-ahead gives stages, not kills.

### 5.5 Raid groups (`party/raid.js`)

A raid is a temporary group for one fight across parties and paths: `/ttl raid invite <p>` (by the soul who will summon),
`/ttl raid accept <p>`, `/ttl raid leave`, `/ttl raid` (status). Knobs `bosses.toml [raid] max = 10, ttl_minutes = 30,
core_per_raid = 1`. `boss.js partyOf` consults `TtlRaid.groupOf(server, player)` **first** (then the test party, then
`TtlParty`): the raid roster is what `snapParty` freezes, so the existing credit, snapshot and core rules apply unchanged
(`boss.js:492-502`, `:728-757`). A lower-act member gets `ttl.defeated.<id>` and `ttl.boss.t<n>` like everyone (that is the
catch-up); `requires` still checks the **summoner** only. A raid dissolves at the fight's end or after `ttl_minutes`.
The per-party cooldown (§7.1) counts a raid kill for every member.

## 6. Light vs dark: how the dark road touches the world

### 6.1 Dark deeds become events others can answer

Every dark-lane deed already exists as a flag or an act (`regicide`, `charybdis_woke`, `falmuth_march`, Act III dark
"Devour the King", Act VII `demon_lord`). They feed `balance` (§3.2) and, through tides and milestones, **unlock events**
that the director schedules with its own caps (`events.toml [[event]] requires = { unlocked = true }`):

| Event | Unlocked by | What happens | Light answers | Dark answers | Outcome → chronicle |
| --- | --- | --- | --- | --- | --- |
| `horde_raid` | `tempest_town` or dark tide | Orc waves at Tempest's south gate (the invasion engine of WP-S8 `events/invasion.js`, or its own waves), an Orc Lord instance at the end, 20 min | Defenders: anyone in the zone when the waves are cleared gets `raid_defended` credit: tempest +10, coins, title "Gatekeeper" (era) | A dark soul may `/ttl raid side horde` before the first wave: PvP against defenders inside the zone for the duration (§6.2), orc_horde +10 if the gate falls | `raidsWon.defenders` / `.raiders`; a sacked gate sets `active.rebuilding = 7 days`: the chapter `rebuilding` (world chapter, repeatable hand-ins at the gate, merit ×3) opens, **the town phase never regresses** |
| `outcast_uprising` | light tide | Outcast agents appear in Blumund's streets (Easy NPC `uprising` kinds + a proxy boss), 15 min | Put it down: blumund +10 | Join it (`side outcast`): outcast +10, blumund −10 | `uprising_*` |
| `holy_hunt` | `act5_reached` + dark tide | For 24 h Hinata's wild `path_mult.dark` ×5 and the Church posts a bounty on dark souls (guild board row) | Hunt with the Church (bounty) | Survive it: a dark soul that is online 2 h without falling to Hinata gets outcast +15 and the title "Unbroken" | counted as kills/survivals |
| `falmuth_invasion_repeat` | `act5_reached` | The scripted ch.11 invasion as a director repeat (O10 of story-characters.md) | as ch.11 | as ch.11 | kills |
| `walpurgis_monthly` | `tempest_city` | Council scene at Clayman's castle, monthly: the Ten (Legendary holders) and nation owners are named, treaties posted | attend | attend | log |
| `harvest_festival` / `hero_ascension` | first awakening | server-wide title, Hall line, the capstone's `#story` (master plan §12) | — | — | log |
| `dwarven_caravan` | `dwargon_pact` | a trading caravan on the Dwargon road (Easy NPC traders, 1 h) | trade | raid it (dwargon −20, orc_horde +10) | log |

Rule: an event never removes a quest, a build or a stage. A "lost" raid adds a rebuilding chapter and a mark; a "won" one adds
a title. Both lanes get something to do on every tide (R10).

### 6.2 PvP rules pass (`pvp/pvp.js`, `design/data/pvp.toml`)

Today PvP is open in Life 2 and nothing reads wars except absorption. The pass is one `EntityEvents.beforeHurt` handler at
priority 71 (loaded before absorb.js at 70, so a cancel stops it; it reads `TtlAbsorb.openPact` at run time, guarded):

```toml
[pvp]
mode = "rules"                 # rules | always (today) | never
life1 = "always"               # owner decision 18/11/2026: Life 1 PvP open; this pass never touches ttl:mortal_*
warn_seconds = 10              # one "no PvP here" line per attacker per this many seconds
[pvp.allow]
duel_pact = true               # an open absorb duel/challenge pact (anywhere; liability below)
war = true                     # both in nations at ACTIVE war, inside war_hours
war_hours = [19, 23]           # Brussels wall clock; [] = any hour
arenas = ["tensura:labyrinth"] # dimensions
arena_builds = ["clayman_castle", "spirit_dwelling"]   # the Walpurgis hall and Ramiris' arena: inside their ttl.build.<name>.box
event_sides = true             # opposite sides of a raid/uprising inside its zone
[pvp.liability]
public_duel = "deposit"        # deposit | refuse | free — a duel started inside a reserve, a build box or another team's claim
deposit = { gold = 5 }         # paid by the challenger into the local faction (a sink through TtlEcon.charge); staff rollback with CervLogger
```

`TtlPvp.allowed(server, attacker, victim)` returns `{ok, why}`; a refused hit is cancelled with a rate-limited line ("Only a
duel, a war or an arena allows that here"). `/ttl pvp why <a> <b>` (ops) and `/ttl pvp simulate <a> <b>` (test hook, the
absorb pattern) print the verdict. A `war` hit also tags both for the combat-log rule (absorb.js does already). Reputation
guards stay as they are: a kill on a faction's ground costs `kill_penalty.player` (`guards.js:56-60`), and a dark soul at
Hostile meets guards (once `ttl.guard.<f>` entities exist: WP-W5 adds Tempest guards).

**Damage liability** (owner rule of 18/11/2026: "whoever starts a duel in a public place pays"): the challenger's deposit is
charged when the duel is *accepted* inside a public place; it is a plain sink. Rollback stays a staff action (`cl rollback
u:<name> t:30m`, `docs/server.md`). Automated damage accounting is not worth its code at this size.

### 6.3 Reputation guards in practice

Nothing locks a quest: a Hostile soul still gets a line (`shuna`, `shion` have them), still fights, still completes acts. What
Hostile costs is guards, shops and the dark lane's own prices (`tempest -40` at Act V). The chronicle adds **mood** on top:
a faction the world has befriended is one band kinder in guards and shops to everyone, one the world has wronged one band
harsher — again for guards and shops only, never for quest gates.

### 6.4 Scarce things: the Ten Legendaries

| Route (today) | Consent? | Change |
| --- | --- | --- |
| Rebirth echo, capstone draw, Skill Core | the holder's own | none |
| Duel (`absorb.duel`) | both accept | none; the public-place deposit applies |
| Bequest | both accept | none |
| Awakening claim | free place | none |
| Awakening **challenge** (`absorb.js:507-529`) | the holder cannot refuse | **refusable with cost**: `/ttl absorb refuse <p>` within `offer_minutes`: renown −20, era title "Craven" (shown in the Hall), and the challenger may not challenge the same holder again for 30 days. Not refusing = the pact opens as today. |
| **War** (`absorb.war`) | none; the defender can end the war at once (H7) | war goes active only when the defender's owner **accepts** (`/ttl nation war accept <n>`) or after `war_notice_hours` *and* the defender had a member online in the last 7 days; ending an active war is a **surrender** (`/ttl nation surrender <n>`: `surrender_cost_pct` 25 of the treasury to the winner, renown −10 for the owner) — refusable with cost. Absorption on war kills only inside `war_hours`. |
| Inactivity return (`registry.js:598-625`) | — | 45 days; `#story` + login Voice warning at 30 (O-W5). |
| Hoarding | — | `max_legendary_per_holder = 2` (registry `grant`/`transfer`; O-W5). |
| Era tenure | — | **open decision O-W13**: at each era turn, a holder of the Ten must *defend* within 30 days (an echo of their capstone boss, solo or raid) or the Legendary returns to the pool. |

## 7. MMO-scale rules at 10–30 players

### 7.1 Instancing limits (`bosses.toml [framework]`, WP-W2)

```toml
cooldown_scope = "party"       # party (new) | server (today); a party is on cooldown while ANY member's ttl.boss.lastkill is
arena_gap_minutes = 10         # global pause per arena after a defeat (loot, forceload release)
max_instances = 4              # bosses alive server-wide (story + wild), beyond it: queue
max_per_party = 1              # a party/raid has at most one boss out
queue_ttl_minutes = 20         # a queued party that does not show up at the arena loses its place
echo_prefix = "Echo · "
echo_hp_mult = 0.85
```

The arena lock: `summon()` refuses "already out there" only for the **same arena**; a party whose summon is refused is put in
`ttl.boss.queue[id]` with a place, told the ETA (idle 30 min at worst), and pinged in chat and by one Discord DM-free `#story`
line when the arena frees (the next in the queue gets `queue_ttl_minutes` to summon; then it passes on). Wild and story
instances never block each other (separate "already out" sets); a wild boss still counts in `max_instances`.

### 7.2 Anti-hoarding

- Skill Cores: `core_cap_week = 2` per soul (`ttl.boss.cores.week`), the rest of the kill still pays; raid cores `core_per_raid`.
- Boss coins/rep on a repeat kill by the same party inside `repeat_window_days = 7`: `repeat_mult = 0.5` (the per-party
  cooldown already spaces them; this stops a five-party rota farming one T4 at ×1.0).
- Legendary per holder (§6.4), nation member cap 5 (exists), claim limits (exist).

### 7.3 Fairness of world firsts

- `firsts.<boss>` is written once, from `finish()` names (the credited souls, party and raid included) — the first kill
  belongs to everyone credited, not to the killing blow.
- Era titles: `skills.toml [era] titles` gains `pioneer` ("First Blade of the Era": the first kill of any T3+ boss) and
  `gatekeeper`, `unbroken`, `craven` (§6). First kills are a Hall leaderboard section ("Firsts of the era") and a weekly recap
  section ("The world this week": milestones, tide, raids).
- A first kill is never gated: an echo party can still be first on a boss nobody has beaten.

### 7.4 Eras and resets

- An era turn (`TtlEra.next`, reserved line) **archives** `ttl.world` to `ttl.world.archive`, resets `balance` and `tide` to 0,
  keeps `phases`, `milestones` and `firsts` as **history** (new milestones of the new era get an `era` suffix in the stage:
  `ttl.world.milestone.<id>.e2`), and opens the next era chapter (world chapter, R7). Quests, builds, nations, skills: never.
- `/ttl worldreset` stays an ops tool for a world *remake* between eras, documented as such in `docs/server.md` (H13).

### 7.5 Admin tooling (`world/commands.js` + existing trees)

`/ttl world` (status: counts, balance, tide, phases, milestones) · `/ttl world log [n]` · `/ttl world balance add <n>` ·
`/ttl world milestone fire|list` · `/ttl world phase set tempest <phase>` (ops: places the ring) · `/ttl world recount`
(login backfill for everyone online) · `/ttl world export` (JSON, one line, for ttl-ops) · `/ttl world expect <field>
<value>` (tests) · `/ttl boss queue [id]` · `/ttl raid …` · `/ttl pvp why|simulate` · `/ttl nation war accept|surrender`.
Every ops change writes one `[ttl] world:` log line and a `ttl.world.log` entry with `who = ops`.

## 8. Discord and BlueMap hooks

- **Discord.** One `TtlDiscord.post` per milestone, tide change, raid outcome, first kill and era archive (`#story`,
  reused: O-W9). `discord/hall.js recapText` gets a section "The world this week" (milestones, tide, raids won/lost, firsts)
  and the leaderboard a "Firsts of the era" block; `TtlHall.noteWorld(server, kind, text)` is the one call. Test runs stay
  silent through the existing mute (`discord.js:45-55`).
- **BlueMap.** `gen_map.py:12` writes static markers only. Live "World" markers (Tempest phase label, active raid zone,
  queued/active arenas, wild boss region, nation homes from `ttl.nations`, war pairs): first choice the API from a script
  (`Java.loadClass('de.bluecolored.bluemap.api.BlueMapAPI')`, `getInstance()` → a `MarkerSet` on the Tensura map;
  **verify in game** that the API jar is reachable from KubeJS 2101 and survives `/reload`), fallback ttl-ops: every 10 min
  `rcon "ttl world export"` → `tools/gen_map.py --live <json>` rewrites the marker set in the map config and runs `bluemap
  reload` (the pod already runs RCON for tests and pregeneration, `docs/server.md`). The export is the same JSON either way.

## 9. Migration of existing state (one boot, idempotent)

| State today | Becomes | How |
| --- | --- | --- |
| `ttl.boss.last.<id>` (server-wide cooldown) | per-soul `ttl.boss.lastkill` | not migrated: the global stamps are read once as an `arena_gap` (10 min from boot) and then ignored; `/ttl boss cooldown clear all` already exists for tests and launch |
| `ttl.boss.active` records | gain `party` (summoner's party/raid id, `''` for ops and wild) and `echo` | records without `party` are treated as `''` (no per-party cooldown written) |
| `ttl.boss.kills` (per player) | counted into `counts.kills` | login backfill (`ttl.world.counted`) |
| `ttl.story.log`, `ttl.reg.history` rings | `firsts`, `counts.legendary` | first boot, once (`ttl.world.v` absent) |
| `ttl.story.parties` | pruned of team ids FTB no longer has | chronicle sync (the party.js `:327-336` rule) |
| `ttl.tempest.version = 3` | `phases.tempest = "village"` | first boot; `ttl.tempest.phase` written by `grow` |
| Tempest residents (goblins without `Invulnerable`) | hardened in place | `TtlTempest.hardenResidents` at load (`data merge entity @e[tag=ttl_tempest_resident] {Invulnerable:1b}` + `tag add ttl.npc.tempest`), no re-placement |
| Build boxes `ttl.build.<name>.box`, Tempest/Dwargon boxes | the reserve | read as they are; the Tempest growth reserve is a knob (192) around 0, 0 |
| Chapter 4 `orc_lord_kill` task | `stage ttl.defeated.orc_lord` (same quest key) | the task id changes type; nobody could complete it, so no progress is lost; decisions row |
| `skills.toml [registry] inactive_days 30` | 45 + warnings | knob |
| Era | the current era's `ttl.world` starts now (`since`) | first boot |

The staging checklist (`docs/HANDOFF.md` "Before launch") gets `/ttl world recount` and `/ttl boss queue clear`.

## 10. Work packages (one agent each, ≤ ~70 min, owned files only; cross-system call sites are one reserved, guarded line)

| # | Package | Owns | Deps | Bot test (`tests/ingame/<x>.rcon`) |
| --- | --- | --- | --- | --- |
| **Wave A** | | | | |
| WP-W1 | **Chronicle core**: `TtlChronicle.note/count/balance/tide/milestones/phase/mood/sync/export/lines`, login backfill, 5-min sync, era archive | `world/chronicle.js`, `world/commands.js`, `design/data/world.toml`, `gen_data.py check_world`, `tests/ingame/world.rcon`; reserved lines: `story.js` (`applyOath`, `act`, `flip`, `flag`), `boss.js finish`, `nations.js` (`found`, `declareWar`, `endWar`, `dropRecord`), `registry.js log`, `era.js next`, `rep.js guardsHostile/shopOpen` (mood) | — | three Life 2 bots: `ttl story oath light` ×2 + `act … 2` ×3 (ops) → `ttl world expect counts.acts.light.2 3`, `expect milestone act2_reached yes`, `kubejs stages` shows `ttl.world.act2` on a 4th bot after login; `ttl world balance add -40` → `expect tide dark`; `ttl world milestone fire tempest_town` → `expect phase tempest town` (no Tempest script yet: the phase hook is a stub that logs) |
| WP-W2 | **Boss instancing**: per-party cooldown, arena lock + queue, `max_instances`/`max_per_party`, wild/story separation, echo prefix + `echo_hp_mult`, `kind = statue` hides the seat, `TtlRaid.groupOf` hook | `bosses/boss.js`, `bosses/wild.js`, `bosses/commands.js` (`queue`, `expect <p> busy|queued|cooldown`), `design/data/bosses.toml` knobs, `tests/ingame/bosses.rcon`, `tests/ingame/wild.rcon`; reserved line in `life/dwargon.js ensure` (skip while `TtlBoss.activeAt(server, 'gazel_dwargo')`) | — | party A (testparty a b) summons and kills `orc_lord` → `expect a cooldown orc_lord yes`, bot c (no party) `ttl story fight orc_lord` → summoned (no server-wide cooldown); `wild roll shizu` while a story Shizu is out → started; two summons of `gazel_dwargo` → second `expect c queued gazel_dwargo yes`, `boss abort` → c is told, `expect c queued … no` |
| WP-W3 | **Reserve + immortal residents**: block/explosion/fire/fluid veto in build boxes, Tempest/Dwargon boxes and the growth reserve for non-ops; `hardenResidents`; hardened resident NBT | `life/reserve.js`, `design/data/world.toml [reserve]` (`growth_reserve`, `pad`, `allow_ops`, `allow_tags`), `life/tempest.js` (NBT line + harden pass), `tests/ingame/reserve.rcon` | — | bot at Tempest green `setblock` through `execute as` (non-op bot) → block unchanged, `ttl reserve expect <bot> blocked yes`; `data get entity @e[tag=ttl_tempest_resident,limit=1] Invulnerable` = 1b; `kill @e[name=Rigurd]`-style `damage` on Rigurd → still alive |
| WP-W4 | **PvP rules pass** | `pvp/pvp.js`, `pvp/commands.js` (`status`, `why`, `simulate`, `expect`), `design/data/pvp.toml`, `gen_data.py check_pvp`, `tests/ingame/pvp.rcon`; reserved line in `absorb.js offerDuel/accept` (deposit) | — (reads `TtlAbsorb`, `TtlNations`, `TtlRaid` at run time, guarded) | `ttl pvp simulate a b` → `refused (no duel, war or arena)`; `ttl absorb duel`/`accept` between them → `allowed (duel)`; `ttl absorb war a b` (staff flag) → `allowed (war)` only inside `war_hours` (test sets `[]`); inside `tensura:labyrinth` → allowed |
| **Wave B** | | | | |
| WP-W5 | **Tempest phases**: town and city rings, residents and guards per phase, `TtlTempest.grow`, `min_phase` spots, core-preserving test | `blueprints/tempest_town.py`, `blueprints/tempest_city.py`, `tools/build_structures.py` (ring output), `pack/kubejs/data/ttl/structure/tempest_*_ring.nbt`, `generated/tempest_footprint.js`, `life/tempest.js` (`grow`, `phase`), `design/data/npcs.toml` (`min_phase`, guard kinds), `economy/guild_npcs.js` (`active` reads `min_phase`), `tests/test_tempest_phases.py`, `tests/ingame/tempest_phase.rcon` | WP-W1 (phase hook; `/ttl world phase set` stub works without the chronicle), WP-W3 (reserve) | `ttl world phase set tempest town` → log `[ttl] tempest: town ring placed`, `ttl tempest expect phase town`, chapter-2 anchors still solid (`execute if block` at (22,-39) floor), `ttl cast verify all` 0 failed |
| WP-W6 | **Catch-up + echo**: late check, EP grace, Favor weight, skip-ahead offer on party join, echo Voice lines, guide page | `story/catchup.js`, `design/data/world.toml [catchup]`, `design/data/guide.toml` (page "Late to the world?"), `tests/ingame/catchup.rcon`; reserved lines: `party.js admit` (`TtlCatchup.offer`), `story.js fight` (echo line), `story.js act` (`opts.catchup`), `favor.js eligible` (weight) | WP-W1, WP-W2 | bot reborn with `ttl.l2.arrived` faked 20 days after era start and acts 0 while `ttl.world.act3` is set → `ttl catchup expect <bot> late yes`; `ep` sample hook: `ttl absorb ep <bot> 1000`, then `ttl absorb ep <bot> 1200` + `ttl catchup tick` → log `grace +100`; join a party at act 3 → `ttl catchup skip` as the bot → `ttl story expect <bot> act 3 yes`, `ttl rep expect <bot> dwargon band neutral` (no rep paid) |
| WP-W7 | **Raid groups** | `party/raid.js`, `party/commands.js` (`/ttl raid …`), `design/data/bosses.toml [raid]`, `tests/ingame/raid.rcon` | WP-W2 (hook) | a (light) invites c (dark) → `accept` → summon `orc_lord`, kill with both in range → both `ttl boss expect … defeated orc_lord yes`; raid gone after the kill (`ttl raid expect c in no`) |
| WP-W8 | **Consent + anti-hoard**: refusable challenge, war acceptance/surrender, war-hours absorption, 45-day return with warnings, `max_legendary_per_holder` | `absorb/absorb.js`, `nations/nations.js` (`acceptWar`, `surrender`), `nations/commands.js`, `registry.js` (per-holder cap, warning), `design/data/skills.toml`, `design/data/nations.toml`, `tests/ingame/absorb.rcon`, `tests/ingame/nations.rcon`, `tests/ingame/legendary.rcon` | — (WP-W4 optional) | challenge → `ttl absorb refuse` → pact gone, renown −20; declare war → `warstate pending` after 24 h faked (`active_at` test hook) without acceptance and no defender seen in 7 days → still pending; `accept` → active; `surrender` → treasury −25 %; `registry legend` a 3rd Legendary to one bot → refused |
| **Wave C** | | | | |
| WP-W9 | **Dark-deed events**: `horde_raid`, `outcast_uprising`, `holy_hunt`, `dwarven_caravan`, `requires = { unlocked }`, sides, defenders' rewards, the `rebuilding` world chapter | `events/raid.js`, `events/uprising.js`, `events/hunt.js`, `events/caravan.js`, `design/data/events.toml` rows, `design/quests/chapter_14_rebuilding.toml` (`world = true`), `tests/ingame/raid_event.rcon`; reserved line in `director.js blocked` (`requires.unlocked`) | WP-W1, WP-W4, WP-W7, WP-S8 (invasion engine; else own waves) | `ttl world milestone fire tempest_town` → `ttl events fire horde_raid` → 20 orcs at the south gate + an orc_lord instance; `kill @e[tag=ttl.event.horde_raid]` with two bots in the zone → `expect raid defenders 2`, `ttl world expect counts.raidsWon.defenders 1`; `side horde` bot + `pvp simulate` → allowed inside the zone only |
| WP-W10 | **Discord + BlueMap + Hall**: chronicle lines, recap section, firsts block, live markers (API or ttl-ops export) | `discord/chronicle.js`, `discord/hall.js` (section + block), `tools/gen_map.py --live`, `docs/server.md` (ttl-ops job), `design/data/discord.toml` (none new if `#story` is reused) | WP-W1 | `ttl world export` prints one JSON line with `phases`, `firsts`, `active`; `ttl discord expect last contains "Tempest has grown"` after a milestone with mute off and no bots (log line, the existing dropped-line check) |
| WP-W11 | **Quest wiring**: chapter 4 altar quest + stage finale, `world = true` chapters and the R7 check in `gen_quests.py`, `[[npc.talk]] world = {…}` conditions in `TtlStory.pick`, echo/phase lines in `story.toml`, `quests.md` | `design/quests/chapter_4_orc_lord.toml`, `tools/gen_quests.py`, `design/quests.md`, `design/data/story.toml` (talk entries only), `story/story.js pick` (the `world` condition), `tests/test_gen_quests.py`, `tests/ingame/quests.rcon` | WP-W1 (stage names), WP-W5 (phase names) | `gen_quests.py --check` fails on a chapter 0–13 quest with a `ttl.world.*` task; `execute as <bot> run ttl story talk mildo` with `ttl.world.phase.tempest.town` set → the town line |
| WP-W12 | **Fairness + docs**: era titles (`pioneer`, `gatekeeper`, `unbroken`, `craven`), Skill Core weekly cap, `repeat_mult`, `/ttl world` admin polish, `master-plan.md` divergence notes (§7, §9, §12, §14), `decisions.md` rows, `roadmap.md`, `docs/discord-guides.md`, `docs/HANDOFF.md` checklist | those files, `bosses/boss.js reward` (cap + repeat), `design/data/skills.toml [era]` | all | `ttl boss expect <p> cores 2` after three T3 kills in one week; docs reviewed |

Waves: **A** WP-W1 WP-W2 WP-W3 WP-W4 (independent) → **B** WP-W5 WP-W6 WP-W7 WP-W8 → **C** WP-W9 WP-W10 WP-W11 WP-W12.
Each package ends with `validate.py` green, `server.sh test <name>` green, no new `[ttl]` errors, and a `decisions.md` row.
Script priorities: `world/chronicle.js` 72 (next to the director; it only defines an object), `pvp/pvp.js` 71, the rest 70,
commands 60.

Verify-in-game list (owned by the package that depends on it): FTB per-player reward claims and personal `TeamData` after
leaving (W6), `tensura edit stat … ep current add` repeated (W6), `ftbchunks admin claim_as` for an optional server claim (W3),
`BlueMapAPI` from KubeJS (W10), `EntityEvents.beforeHurt` ordering between pvp.js and absorb.js (W4), `data merge entity`
on a loaded `tensura:goblin` keeping its `CustomName` (W3).

## 11. Open owner decisions (recommendation first)

| # | Question | Recommendation |
| --- | --- | --- |
| O-W1 | Boss availability: per-party cooldown + arena queue, or true multi-instancing (two Gazels in one throne room)? | **Per-party cooldown + queue.** Fights are 5–15 min; a queue with an ETA is honest and keeps one king per room. Revisit if `#story` shows waits above 20 min. |
| O-W2 | PvP in Life 2: the rules pass (`mode = "rules"`), or open as today? | **Rules pass.** Duels, wars in a window, arenas and event sides cover every legitimate fight; griefing of questlines is otherwise one sword away. Life 1 stays open (your 18/11 decision). |
| O-W3 | A duel started in a public place: deposit (5 gold) + staff rollback, refuse, or free? | **Deposit.** Your rule says the starter pays; a deposit is the one automatic form of "pays" that needs no damage accounting. |
| O-W4 | When raiders win at Tempest: a "rebuilding week" with a repeatable chapter, or the town phase regresses? | **Rebuilding week.** The phase never goes back (R10); the sack leaves a mark and work for builders. |
| O-W5 | Inactivity return 45 days with warnings (was 30), and at most 2 Legendaries per holder? | **Yes to both.** Holidays happen; the Ten should be ten people, not five. |
| O-W6 | Awakening challenge refusable at a cost (renown −20, era title "Craven", 30-day shield), or never refusable? | **Refusable with cost.** Consent with a price keeps the drama and removes the "I was offline-fed to a Demon Lord" complaint. |
| O-W7 | Milestone thresholds: max(3 souls, 25 % of active) and Tempest town at Act III, city at Act VI? | **Yes.** At 10 players that is 3 souls; at 30 it is 8. Tune after the first town. |
| O-W8 | War: defender's acceptance or 24 h + an active defender; surrender costs 25 % of the treasury? | **Yes.** Today either owner cancels a war for free (H7), which makes war absorption a coin flip. |
| O-W9 | Chronicle lines in `#story`, or a new `#chronicle` channel? | **`#story`** now; a channel of its own once lines exceed ~10 a day. |
| O-W10 | Era turn: balance/tide reset, phases/milestones/firsts kept as history? | **Yes.** "A forever world" (master plan §14). |
| O-W11 | Joining a progressed party: skip-ahead pays 50 % renown, no reputation, no flags? | **Yes.** Friends first; the renown half keeps nation value honest. |
| O-W12 | Tempest growth reserve: 192×192 around 0, 0, protected from day 1? | **Yes.** Smaller than the city needs is a demolition later. |
| O-W13 | Era tenure for the Ten: defend within 30 days of an era turn or return the Legendary? | **Yes, mild**: an echo fight, solo or raid, is a small ask that keeps the Ten alive and gives late joiners a path. |
| O-W14 | Dwargon: mood and caravans only, or a growth ring too? | **Mood only.** Dwargon is finished in canon; Tempest is the one that grows. |
