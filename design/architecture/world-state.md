# World state: personal, party and world — no lock-outs, a world that evolves

18/11/2026 (rev. 2, after the owner's answers of the same day) · design only, for the implementation agents. Builds on
`sprint3-4.md` (§0 conventions apply unchanged), `story-characters.md` (acts, parties, boss spawn redesign), the story core
(`story/story.js`), the boss framework (`bosses/boss.js`, `bosses/wild.js`), reputation (`rep/`), nations (`nations/`), the
event director (`events/director.js`), the party layer (`party/party.js`), eras (`era/era.js`), absorption
(`absorb/absorb.js`), the guild (`economy/guild.js`) and the canon builds (`life/builds.js`, `life/tempest.js`,
`life/dwargon.js`). Every file:line below was read on 18/11/2026; **verify in game** marks what an agent must confirm first.
**DECIDED** marks what the owner (Yasuke) settled on 18/11/2026; those rows are not up for discussion in the packages.

Owner question (paraphrased): *"How do we make sure people don't get locked out of quests, and that the world evolves along
with them? What if there are a few good people and then bad people who overtake or ruin the good questlines? At this point
this becomes kind of an MMO."*

## 0. The five principles, checked against the code (with the owner's answers)

| # | Principle | What the code does today | Verdict |
| --- | --- | --- | --- |
| P1 | Personal/party story is separate from world state; nothing one party does can lock another out; canon characters are immortal anchors; every fight is a per-party instance | Story state is personal (`ttl.story.*`) and quest progress per FTB team: **good**. A boss id is **server-unique** and its cooldown **server-wide** (`boss.js:266-269`, `:117-125`, `:271-274`, `:701`): one party's Veldora kill locks everyone out for 96 h. Statues and Easy NPCs are invulnerable and re-spawned; the named Tempest goblins are **not** (`tempest.js:234`). Canon builds have **no protection** (`ftbchunks-world.snbt:74 pvp_mode "always"`, no claims). | Right principle, holes H1–H5. **DECIDED:** per-party cooldown + queue; story NPCs always respawn; and all of it applies **only on the mainland continent** — outside the ocean ring the mods behave as shipped (§2.0). |
| P2 | A World Chronicle drives evolution at thresholds, always adding | Nothing aggregates; the only server-wide story fact is `ttl.story.unlocked` (`story.js:421-429`). Builds are placed once per `version` (`builds.js:4-5`, `:560-564`): the lever "Tempest grows" needs. | Agree (§3–§4). Offline players cannot be read from KubeJS, so counts are backfilled at login and milestones are sticky. **DECIDED:** thresholds, phases, era archive as recommended; canon nations are **factions with protected domains** and a long **takeover path** (§6.6). |
| P3 | Late joiners play every quest; the past replays as memories; catch-up boosts; party sync | FTB progress is per team: joining a progressed party **skips** its book (rewards claimed per player, **verify in game**); leaving returns the own book. Quest text is static SNBT per locale (`quests.md:159-166`). | Echo = Voice lines + boss-bar prefix + NPC lines; party join = skip-ahead (§5). **DECIDED** as recommended. **DECIDED:** quests are story quests **and radiant quests** generated from world state (§6.8). |
| P4 | Light vs dark becomes world events; PvP limited; reputation guards; scarce things protected | Dark deeds only move the dark soul's own reputation. PvP is **open** everywhere in Life 2; war is a flag only read by absorption (`nations.js:633-654`, `absorb.js:235-256`); either owner ends a war at once (`nations.js:656-668`); the awakening challenge is not refusable (`absorb.js:507-529`). | **DECIDED:** PvP only in special quests, arenas and declared wars (§6.2); a war needs an **army** of named subordinates and the winning **defender may demand reparations** (§6.5); Legendaries: **no per-holder cap, no inactivity loss, the ceiling of ten stays** (§6.4); challenge refusable with cost. |
| P5 | MMO-scale needs at 10–30 players | No instancing limits, no queue, no anti-hoarding beyond the registry caps, era resets touch slots and titles only (`era.js:155-170`), `/ttl worldreset` regenerates dimensions (`world_reset.js:6-60`). | §7. |

Pushed back on and kept: (a) "every fight already summons per party" — it does not (H2/H3); (b) "replay the past" — not inside a
party's book, so skip-ahead + echo; (c) the afternoon note "duels anywhere, the starter pays" is **superseded** by the owner's PvP
scope (arenas, wars, special quests) — no deposit mechanism is needed.

## 1. Problem list: concrete holes in the current code

Severity: **L** = locks a party or soul out of content · **W** = lets one soul damage the shared world · **F** = fairness.

| # | Sev | Hole | Where | Closed by |
| --- | --- | --- | --- | --- |
| H1 | W | Rigurd, Rigur, Gobta, Haruna are `tensura:goblin` with `PersistenceRequired` only: killable, and only re-spawned when `TTL_TEMPEST_VERSION` changes; no `ttl.npc.tempest` tag, so the kill costs nothing (`factions.toml:71`, `guards.js:31-41`). | `life/tempest.js:228-234` | WP-W3: **DECIDED** — story NPCs on the continent always respawn. Residents get `ttl.npc.tempest` and a respawn ensure loop (the `guild_npcs.js ensureSpot` pattern), killable or not (§2.0, owner answer 2). |
| H2 | L | "already out there": one live instance per boss id, server-wide. | `bosses/boss.js:266-269` | WP-W2: arena busy lock with a **queue**; wild instances never count. **DECIDED.** |
| H3 | L | One server-wide cooldown stamp `ttl.boss.last.<id>` (24–96 h); wild rolls read it (`wild.js:126-127`); a wild Shizu blocks the story Shizu (`wild.js:121-124`). | `boss.js:117-125`, `:271-274`, `:701`; `wild.js:119-137` | WP-W2: cooldown **per party** (`ttl.boss.lastkill` on every credited soul) + `arena_gap_minutes`; wild/story separated. **DECIDED.** |
| H4 | W | Tempest, Dwargon and the 19 canon builds have no claim and no block protection (`disable_protection: false`, nobody claims; `pvp_mode "always"`). | `ftbchunks-world.snbt:15`, `:74`; `builds.js` (`ttl.build.<name>.box`) | WP-W3: **canon domains** (§6.6): no break/place/explosion/fire/fluid for non-members inside a canon nation's domain; **DECIDED** that the territory is protected until the world state turns it into a conflict. |
| H5 | L | Chapter 4's finale is a `kill tensura:orc_lord` task; `block_natural` cancels the camp's spawns (`NATURAL` includes `structure`); the only Orc Lord is summoned by typing `/ttl story fight orc_lord` (open to players, `story/commands.js:202`), which the book never says. | `chapter_4_orc_lord.toml:150-154`; `bosses.toml:127`; `boss.js:926-945` | WP-W14: the **March of the Horde** (§6.7): Geld arrives on the battlefield after the party holds the line; the finale reads `ttl.defeated.orc_lord`. **DECIDED** (immersive arrival, not a plain summon). |
| H6 | L | The path lock kicks a joiner of the other Oath (O2) and boss credit only flows through the FTB party (`boss.js:428-458`, `:728-757`): light and dark friends cannot share a fight. | `party/party.js:229-244` | WP-W7: **raid groups**. |
| H7 | F | War: active after 24 h with no consent, any kill moves a Legendary with no EP gate (`[absorb.war] min_ep_ratio 0`), and the defender's owner ends the war at once (`endWar` only checks "an owner"). | `nations.js:634-668`; `absorb.js:235-256`, `:276` | WP-W8: war needs an **army** + acceptance or notice with an active defender; ending an active war is a **surrender**; the winning **defender demands reparations** (§6.5). **DECIDED.** |
| H8 | F | A 30-day absence returns **every** unique to the pool, Legendary included (`sweep` takes `heldBy(recs, id)` whole). | `registry.js:598-625`; `skills.toml [registry] inactive_days = 30` | WP-W8: **DECIDED** — a Legendary **never** returns through inactivity (it would distort leaderboards and scores); Rare/Common keep the 30-day return. `sweep` skips `rarityOf(skill) === 'legendary'`; `[registry] inactive_returns = ["rare", "common"]`. |
| H9 | — | (rev. 1 proposed a cap of 2 Legendaries per holder.) | `registry.js:106-111` | **DECIDED: no per-holder cap.** A soul may gather several, as Rimuru did, and lose them through the absorption routes. Dropped. |
| H10 | L | `spawn.kind = "statue"` (Gazel) is not implemented; the fight Gazel is summoned beside the seated statue (`dwargon.js:278-289` re-seats him within seconds). | `bosses.toml:409`; `bosses/boss.js` | WP-W2: `kind = statue` = the statue steps aside while an instance of that boss is active in the arena. |
| H11 | W | `ttl.story.parties` keeps records of parties FTB no longer has. | `story/story.js:342-346` | WP-W1 prunes in the chronicle sync (the `party.js:327-336` rule). |
| H12 | F | No catch-up beyond the weekly Favor; "Reincarnation Grace ×1.5 EP, 14 days" (master plan §9) is not built. | `events/favor.js` | WP-W6. |
| H13 | W | `/ttl worldreset` regenerates dimensions and re-places everything: between eras only. | `life/world_reset.js:6-60` | Docs rule (§7.4). |
| H14 | W | The story rules (`block_natural`, kill_rep, guards, protection) today apply **everywhere** in the overworld, the free lands beyond the ring included: a boss entity that spawns naturally out there is cancelled (`boss.js:926-945`). | `boss.js:926-945`; `guards.js:43-70` | WP-W1 `TtlWorld.onContinent`; every story rule checks it (§2.0). **DECIDED:** outside the continent the mods behave as shipped. |

Not holes (verified): `ttl.defeated.<id>`/`ttl.boss.t<n>` per player (`boss.js:766-768`); `kill_rep` per credited soul
(`story.js:475-495`); NPC lines by the soul's own act and path (`story.js:524-548`); acts sequential per soul (`story.js:414`);
`ttl.story.unlocked` additive; eras keep quests, races, skills, the world (`era.js:154-170`); the director bypasses boss
cooldowns only on a manual fire (`director.js:401`).

## 2. The model

### 2.0 Where the rules apply: the continent test (DECIDED)

The Tensura overworld has two halves. **Inside** the canon continent (the mainland of `pack/config/ttl/canon_map.txt`, its
rivers and its near-coast water) the story rules of this document hold. **Outside** — the open-sea ring (`canon_regions.json
"ring"`, 1,600 blocks) and the free lands beyond it — Tensura, NEB and every other mod behave as shipped: bosses spawn
naturally and die as often as they die, nothing is gated, nothing is protected, nothing respawns by our hand.

- Test: `TtlWorld.onContinent(x, z)` = `CanonMap.grid().ownerCell(x, z) !== 0` (the grid's `owner` array: the cell's nation,
  the nearest nation for `'~'` river/lake cells and near-coast `'.'` water, `0` beyond — `mod/.../CanonGrid.java:61`, `:205`).
  Cached per chunk column for the hot paths. **Verify in game** at the coast: a boat 200 blocks out should read "outside".
- What switches off outside: `block_natural` (`boss.js checkSpawn` reads the spawn position first), the wild roll (it already
  needs a region), `kill_rep` and the NPC kill penalty, the domain protection, the respawn loops, the boss queue and party
  cooldown (an outside boss is the mod's own, not a `[[boss]]` instance: no `ttl.boss` tag, no reward, no stage).
- What stays on outside: reputation seeding, renown, the registry, nations (a nation may settle outside: its home faction is
  then `''` = the wilds, as `nations.js:436-447` already allows), the chronicle counting kills (`wildKills.outside`, never a
  first), and the PvP scope (§6.2) — the owner's "free roam must never be disrupted" means no story gating out there, not
  open PvP.
- Dimensions: the Labyrinth, the Spirit Domain and Hell count as **inside** (arenas and story places); the Mortal dimensions
  are untouched (Life 1).

### 2.1 Three layers

```
PERSONAL  (player persistentData, player stages)              the soul's truth: path, acts, flags, defeats, kills, rep, renown
PARTY     (FTB party team + ttl.story.parties + FTB TeamData)  the Oath path, quest completion, nation, army, boss-credit roster
WORLD     (server persistentData ttl.world*)                  aggregates of the two above + phases + sticky milestones + balance
                                                              + canon-nation rule (who sits on which throne) + conflicts
```

Rules (R-numbers continue `story-characters.md`):

- **R5 — one-way flow.** Personal and party events are counted into the world; the world never writes personal story state.
  What the world hands a soul is additive: a stage `ttl.world.*`, a Voice line, an event, a boost, a radiant quest.
- **R6 — no removal.** No script removes `ttl.story.*`, `ttl.defeated.*`, `ttl.boss.*`, `ttl.faction.*` from a soul because of
  what another soul did (the soul's own exceptions stay: `/ttl reset`, Atonement/Corruption, the honour-duel flag spent by
  its own kill; one sanctioned exception is the throne stage of §6.6). `tools/validate.py` greps for `stages.remove('ttl.story`
  outside `story.js` and fails.
- **R7 — quests gate on personal/party stages only.** `ttl.world.*` stages may be tasks only in chapters marked `world = true`
  (chapters the chronicle unlocks), never a gate of chapters 0–13. `gen_quests.py` enforces it.
- **R8 — capacity, not availability.** Any global limit on fights is a queue with a place and an ETA, never "done for today".
- **R9 — anchors.** On the continent, canon characters and story NPCs are kept by an ensure loop and come back when killed;
  a fight is always a separate `[[boss]]` entity. Outside, nothing is an anchor.
- **R10 — sticky, additive milestones.** Once reached, a milestone stays for the era; the only reversible world numbers are
  `balance` (tides) and `rule` (who holds a canon throne), and both only choose *which* content is added.
- **R11 — the continent line.** Every story rule asks `TtlWorld.onContinent` first (§2.0).

### 2.2 Storage keys

| Where | Key | Holds | Written by |
| --- | --- | --- | --- |
| Server | `ttl.world` (JSON, ≤ 60 KB) | `{v, era, since, counts, firsts, phases, milestones, balance, tide, rule, conflicts, active}` (§3.1) | `world/chronicle.js` only |
| Server | `ttl.world.log` (ring `log_size`) | `{t, kind, who, data}` | chronicle |
| Server | `ttl.world.archive` | one `ttl.world` snapshot per finished era (cap 10) | `TtlEra.next` reserved line |
| Server | `ttl.world.loop` | loop stamp (reload-safe) | chronicle |
| Server | `ttl.boss.queue` (`{bossId: [{party, by, at}]}`) | arena queue per boss id | boss.js (WP-W2) |
| Server | `ttl.raid.groups` (`{raidId: {leader, members, boss, until}}`) | raid groups | `party/raid.js` |
| Server | `ttl.radiant.board` (`{boardId: {rolled, offers: [...]}}`), `ttl.radiant.seq` | radiant quest offers per board | `quests/radiant.js` |
| Player | `ttl.world.counted` (int), `ttl.world.seen` (`{milestoneId: epoch}`) | backfill version; milestones announced | chronicle |
| Player | `ttl.boss.lastkill` (`{bossId: epoch}`) | per-soul defeat stamps (the per-party cooldown reads every member's) | boss.js |
| Player | `ttl.catchup` (`{grace_until, synced_to, offered}`) | catch-up state | `story/catchup.js` |
| Player | `ttl.radiant` (`{taken: [...], done: {templateId: n}, week, wk}`) | radiant quests held and done | `quests/radiant.js` |
| Player | `ttl.pvp.warned` (epoch) | rate limit of the "no PvP here" line | `pvp/pvp.js` |
| Player | `ttl.faction.member` (faction id or `''`), `ttl.favor.<faction>` (int) | canon-nation membership; favour points toward the takeover path | `world/domains.js`, `quests/radiant.js` |
| Stages | `ttl.world.phase.<place>.<phase>`, `ttl.world.milestone.<id>`, `ttl.world.act<n>`, `ttl.world.tide.light|dark`, `ttl.world.conflict.<faction>`, `ttl.world.rule.<faction>.<mode>`, `ttl.faction.<f>.member`, `ttl.faction.<f>.vassal`, `ttl.faction.<f>.ruler` | world facts and standing mirrored on every online Life 2 soul | chronicle `sync`, domains |
| Scoreboard | `ttl.world.balance`, `ttl.world.phase.tempest` (0/1/2), `ttl.army` (named subordinates mustered) | Easy NPC conditions, `/ttl inspect` | chronicle, nations |

Mirrors follow R3: truth in `ttl.world`, stages and scoreboard rewritten together by `TtlChronicle.sync(server, player)`.

### 2.3 How each consumer reads the world

| Consumer | Reads | Through |
| --- | --- | --- |
| Quests (world chapters only, R7) | `ttl.world.*` stages | FTB `stage` task |
| Radiant quests | counts, tide, phases, moods, conflicts, the soul's region | `TtlChronicle.view(server)` in the template weights (§6.8) |
| NPC dialogue | phases, tides, milestones, rule | `story.toml [[npc.talk]] world = { tempest_at_least = "town", tide = "dark", milestone = "…", rule = { dwargon = "vassal" } }` (`TtlStory.pick`, WP-W11) |
| Builds | phases | `TtlTempest.grow(server, phase)` (§4) |
| Events | milestones, tide, conflicts | `events.toml [[event]] requires = { unlocked = true }` + `unlock_events` effects; one reserved `canStart` line in `director.js blocked` |
| Factions | `mood`, `rule` | `TtlRep.mood(f)` (band offset for guards and shops only); `TtlDomains.canEdit(player, f)` |
| Discord / BlueMap | the export | `/ttl world export` JSON + `TtlDiscord.post` |

## 3. The World Chronicle

### 3.1 Data (`ttl.world`)

```json
{ "v": 2, "era": 1, "since": 1763400000000,
  "counts": {
    "souls": 23, "active30": 14,
    "oaths": { "light": 9, "dark": 5 },
    "acts": { "light": { "1": 9, "2": 6, "3": 3 }, "dark": { "1": 5, "2": 4, "3": 1 } },
    "flips": { "atonement": 1, "corruption": 0 },
    "flags": { "regicide": 2, "honour_duel": 3, "hero": 0, "demon_lord": 0, "charybdis_woke": 1 },
    "kills": { "orc_lord": 7, "gazel_dwargo": 4 }, "wildKills": { "shizu": 1, "outside": 40 },
    "nations": 3, "wars": 1, "armies": { "<teamId>": 6 },
    "raidsWon": { "defenders": 2, "raiders": 0 },
    "radiant": { "tempest": 31, "dwargon": 12, "outcast": 9 },
    "legendary": { "holders": 2, "moves": 1 }
  },
  "firsts": { "orc_lord": { "by": "Yasuke", "party": "Lancelot's party", "at": 1763500000000 } },
  "phases": { "tempest": "village" },
  "milestones": { "act2_reached": 1763600000000 },
  "balance": 7, "tide": "",
  "rule": { "dwargon": { "nation": "<teamId>", "mode": "vassal", "since": 1763700000000, "by": "Yasuke" } },
  "conflicts": { "eurazania": { "opened": 1763650000000, "by": "milestone walpurgis_held" } },
  "active": { "rebuilding": 0 }
}
```

- `counts.*` are **souls** (distinct players). Every Oath, act, flip, flag, kill, nation event, radiant completion and
  takeover step is one `TtlChronicle.note(server, kind, player, data)` from a reserved, `typeof`-guarded line in the owning
  script (story.js `applyOath/act/flip/flag`, boss.js `finish`, nations.js `found/declareWar/acceptWar/surrender/dropRecord/
  muster`, registry.js `log` for Legendary grants/transfers, radiant.js `complete`, thrones.js `join/vassalize/usurp`).
- `active30` from `ttl.lastSeen` at login and in the 5-min sync; thresholds use it.
- `balance` clamped `-100..100`, weights in TOML, drifts to 0 by `decay_per_week`; `tide` from `tide_at`/`tide_end`.
- **Backfill.** Each soul is counted once at login (`ttl.world.counted < v`): acts, flags, `ttl.boss.kills`, Oath, radiant
  done. `ttl.story.log` and `ttl.reg.history` seed `firsts` on first boot. Counts converge; milestones are sticky (R10).

### 3.2 `design/data/world.toml` (new; `gen_data.py check_world()`)

```toml
[chronicle]
log_size = 300
sync_ticks = 6000
active_window_days = 30
discord = true

[continent]                  # §2.0; the test itself is the grid's ownerCell, these only name the exceptions
inside_dimensions = ["tensura:labyrinth", "ttl:spirit_domain", "tensura:hell"]
outside_counts = true        # kills outside still count in wildKills.outside (never in firsts)

[threshold]                  # souls OR pct of active30, whichever is higher                              DECIDED
souls = 3
pct = 25

[balance]
weights = { oath_light = 2, oath_dark = -2, act_light = 1, act_dark = -1, atonement = 3, corruption = -3,
            regicide = -3, honour_duel = 1, charybdis_woke = -2, hero = 10, demon_lord = -10,
            raid_defended = 2, raid_sacked = -3, uprising_put_down = 2, uprising_won = -3,
            radiant_light = 0.2, radiant_dark = -0.2 }
decay_per_week = 2
tide_at = 25
tide_end = 10

# Milestones: sticky, additive. `when` keys are ANDed: acts = { act = n } · acts_path = { act = n, path = x } ·
# flags = { <flag> = n } · kills = { <boss> = n } · nations = n · wars = n · armies = n (nations with a mustered army) ·
# radiant = { <faction> = n } · balance_at_least / balance_at_most = n · milestone = "<id>" · era_days = n · rule = { <f> = mode }
# `effects`: stage · phase = { <place> = <phase> } · unlock_events = [ids] · mood = { <faction> = ±bands } · conflict = "<faction>"
#   (opens that faction's takeover path, §6.6) · chapter = "<world chapter key>" · title · voice (once per soul) · story (#story)
[[milestone]]
id = "act2_reached"
when = { acts = { act = 2 } }
effects = { stage = "ttl.world.act2", story = "The Armed Nation has taken the measure of the newcomers: Act II is written into the world." }

[[milestone]]
id = "horde_seen"
when = { kills = { horde_band = 1 } }
effects = { stage = "ttl.world.milestone.horde_seen", story = "Starving orcs have been seen on the roads of Jura." }

[[milestone]]
id = "tempest_town"
when = { acts = { act = 3 } }
effects = { phase = { tempest = "town" }, stage = "ttl.world.phase.tempest.town", unlock_events = ["horde_raid"],
            title = "Tempest grows", voice = "Tempest has grown into a town. Roads, walls, a market: the world remembers who stood here.",
            story = "Tempest has grown into a town." }

[[milestone]]
id = "act5_reached"
when = { acts = { act = 5 } }
effects = { stage = "ttl.world.act5", unlock_events = ["falmuth_invasion_repeat", "holy_hunt"], conflict = "falmuth" }

[[milestone]]
id = "tempest_city"
when = { acts = { act = 6 } }
effects = { phase = { tempest = "city" }, stage = "ttl.world.phase.tempest.city", unlock_events = ["walpurgis_monthly"],
            story = "Tempest is a city. The council of the Jura-Tempest Federation sits in its own hall." }

# Walpurgis in canon: Clayman's scheme sets Milim on Carrion's Eurazania — the model of a canon takeover.
[[milestone]]
id = "walpurgis_held"
when = { acts = { act = 6 }, kills = { clayman = 1 } }
effects = { conflict = "eurazania", story = "Walpurgis has met. Eurazania's throne is in play." }

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
when = { flags = { honour_duel = 3 }, radiant = { dwargon = 20 } }
effects = { mood = { dwargon = 1 }, unlock_events = ["dwarven_caravan"], conflict = "dwargon", story = "Dwargon and Tempest exchange envoys." }

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
| `stage` | `player.stages.add` on every online Life 2 soul now and at every login | remove a stage |
| `phase` | writes `phases.<place>`, calls the place's hook (`TtlTempest.grow`, §4) | demolish anything |
| `unlock_events` | adds ids to `ttl.world.unlocked`; `events.toml` rows with `requires = { unlocked = true }` only schedule once listed | fire anything at once |
| `mood` | band offset table `ttl.world.mood` read by `TtlRep.guardsHostile/shopOpen` and `[[npc.talk]] faction` conditions | touch anyone's `ttl.rep` |
| `conflict` | opens the takeover path of a canon nation (`conflicts.<f>`, stage `ttl.world.conflict.<f>`) | change who rules until a nation finishes the path |
| `chapter` | the world chapter becomes reachable (first quest = stage task on the milestone) | hide or reset a chapter |
| `title`/`voice`/`story` | announcements; `voice` once per soul | — |

Evaluation runs in the 5-min sync and after every `note`; `/ttl world milestone fire <id>` (ops) forces one.

## 4. Tempest grows: build versions as phases (DECIDED as recommended)

Today `TTL_TEMPEST_VERSION = 3` (`tempest.js:28`) places the whole village; the generic placer does the same per
`design/builds/*.toml` version. Growth reuses that lever with one change: **a phase places a ring, not the whole town**.

- **Blueprints.** `blueprints/tempest.py` stays the village. `blueprints/tempest_town.py` and `tempest_city.py` are rings
  around it (walls, market, barracks, council hall, inn; the Federation hall and a residents' quarter for the city), same anchor
  (world 0, 0 = blueprint (45, 57)); `tools/build_structures.py` emits `tempest_<phase>_ring.nbt` and
  `generated/tempest_footprint.js` gains `rings`.
- **Core-preserving rule.** Every quest anchor of chapters 2 and 7 (Rigurd's hut (22, −39), the campfire (22, −30), the green
  (0, −7), the south gate (0, 23), the Outcast contact (0, 52)) keeps its coordinates in every phase; the arena stays the green.
  `tests/test_tempest_phases.py` (offline) asserts every `location` task inside the Tempest box lies in the village core or in a
  ring's `kept_open` list.
- **Domain.** Tempest's domain (§6.6) is a 192×192 square around 0, 0 from day 1 (**DECIDED**), so the city has room.
- **Placement.** `TtlTempest.grow(server, phase)`: forceload the ring, place it with the village's slab/terrain helpers under the
  ring only, spawn the phase's residents (`tempest_extras.rings.<phase>.residents`, all with the respawn loop of §6.6), record
  `ttl.tempest.phase`. Nothing of a lower phase is removed except explicit `replace` boxes (palisade → wall) validated against the
  core-preserving list.
- **NPC spots.** `npcs.toml [[spot]] min_phase`; `TtlGuildNpc.active` reads it; the spot signature includes the phase. New
  characters only (Tempest guards tagged `ttl.guard.tempest`, which finally gives `guards.js:72-94` something to aim); one entity
  per canon character (R1).
- **Dwargon** does not grow (**DECIDED**): mood, caravans and the takeover path only.
- **Dark server?** Town at Act III, city at Act VI whatever the balance; the tide chooses the banner overlays (left in place when
  the tide turns: the city carries its history).
- **Echo.** A soul in Act I walking into the city still brings logs for Mildo; Mildo's `world = { tempest_at_least = "town" }` line
  says the Great Sage keeps the memory and he keeps the house.

## 5. Catch-up, echoes and party sync (DECIDED as recommended)

### 5.1 Without code
Every chapter stays, every boss is a per-party instance (after WP-W2), every NPC line is picked on the soul's own act and path.

### 5.2 Echoes
An **echo** is any continent fight whose boss has a `firsts` entry. Same numbers, framed as a memory: `TtlStory.fight` (reserved
line) says *"Great Sage: reproducing the memory of the battle at Lake Siss. The outcome is yours alone."*; the boss bar reads
`Echo · <title>` (`[framework] echo_prefix`); `#story` says "(an echo)". `echo_hp_mult = 0.85` only for a party whose highest act
is below the boss's act. Wild bosses are never echoes.

### 5.3 Boosts (`world.toml [catchup]`)
```toml
[catchup]
late_after_days = 14
behind_acts = 2
ep_grace_pct = 50            # Reincarnation Grace on every EP gain for ep_grace_days (tensura edit stat <p> ep current add; verify repeated adds)
ep_grace_days = 14
favor_weight = 2             # counts twice in the World's Favor draw (reserved line in favor.js eligible)
rep_welcome = 10             # with every faction whose mood is positive
coins = { silver = 20 }
```

### 5.4 Party sync
1. **Joining a progressed party = skip-ahead, not replay.** The joiner's book becomes the party's and the party layer gives the
   party's Oath (`party.js:245-254`); `story/catchup.js` (reserved line in `admit()`) offers once: *skip ahead* calls
   `TtlStory.act(…, {force, quiet, catchup: true})` for every act below the leader's — no reputation, 50 % renown, no flags
   (`hero`, `demon_lord`, `regicide` stay earned); *walk* keeps acts personal and plays fights as echoes with the party.
2. **Leaving** returns the own book and acts (FTB keeps personal `TeamData`; **verify in game**).
3. **The other Oath** is still turned away (O2); such friends fight together through a raid group (§5.5).
4. Boss credit needs presence as today; a skip-ahead gives stages, not kills.

### 5.5 Raid groups (`party/raid.js`)
`/ttl raid invite <p>` (by the future summoner), `accept`, `leave`, status. `bosses.toml [raid] max = 10, ttl_minutes = 30,
core_per_raid = 1`. `boss.js partyOf` consults `TtlRaid.groupOf` first, then the test party, then `TtlParty`; the raid roster is
what `snapParty` freezes, so credit, snapshot and core rules apply unchanged (`boss.js:492-502`, `:728-757`). A lower-act member
gets `ttl.defeated.<id>` (the catch-up); `requires` checks the summoner only. The per-party cooldown counts a raid kill for every member.

## 6. Light vs dark, wars, canon nations and the rest of the world

### 6.1 Dark deeds become events others can answer (DECIDED as recommended)

| Event | Unlocked by | What happens | Light answers | Dark answers | Outcome |
| --- | --- | --- | --- | --- | --- |
| `horde_raid` | `tempest_town` or dark tide | Orc waves at Tempest's south gate (the WP-S8 invasion engine or own waves), an Orc Lord instance, 20 min | Defenders in the zone when the waves clear: tempest +10, coins, era title "Gatekeeper" | `/ttl raid side horde` before the first wave: PvP against defenders inside the zone for the duration (a **special quest** in the owner's PvP scope); orc_horde +10 if the gate falls | `raidsWon.*`; a sacked gate sets `active.rebuilding = 7 d` and opens the world chapter `rebuilding` (repeatable hand-ins, merit ×3); **the town phase never regresses** |
| `outcast_uprising` | light tide | Outcast agents in Blumund's streets + a proxy boss, 15 min | put it down: blumund +10 | join it: outcast +10, blumund −10 | `uprising_*` |
| `holy_hunt` | `act5_reached` + dark tide | 24 h: Hinata's wild `path_mult.dark` ×5, a Church bounty on dark souls on the guild board | hunt (bounty) | survive 2 h online: outcast +15, title "Unbroken" | kills / survivals |
| `falmuth_invasion_repeat` | `act5_reached` | the ch.11 invasion as a director repeat (O10) | as ch.11 | as ch.11 | kills |
| `walpurgis_monthly` | `tempest_city` | the council scene monthly: the Ten and the nation owners named, treaties and canon thrones posted | attend | attend | log |
| `dwarven_caravan` | `dwargon_pact` | a caravan on the Dwargon road (Easy NPC traders, 1 h) | trade, escort (radiant) | raid it (dwargon −20, orc_horde +10) | log |

### 6.2 PvP rules pass — DECIDED scope: special quests, arenas, declared wars

`pvp/pvp.js`, one `EntityEvents.beforeHurt` handler at priority 71 (before absorb.js at 70; a cancel stops later handlers; it
reads `TtlAbsorb.openPact`, `TtlNations`, `TtlRaid` at run time, guarded):

```toml
[pvp]
mode = "rules"               # rules | always | never                                                    DECIDED: rules
life1 = "always"             # owner decision 18/11/2026: Life 1 PvP open; this pass never touches ttl:mortal_*
warn_seconds = 10
[pvp.allow]
war = true                   # both in nations at ACTIVE war (§6.5), inside war_hours
war_hours = [19, 23]         # Brussels; [] = any hour
arenas = ["tensura:labyrinth"]                          # dimensions
arena_builds = ["clayman_castle", "spirit_dwelling"]    # the Walpurgis hall and Ramiris' arena (ttl.build.<name>.box)
event_sides = true           # opposite sides of a raid/uprising inside its zone (the "special quests")
quest_flags = true           # a quest chapter may open a PvP window for a soul: stage ttl.quest.pvp.<id> on BOTH souls
duel_pact = "arenas"         # an open absorb duel/challenge pact counts only inside arenas (was: anywhere)
```

Everything else is cancelled with a rate-limited line ("Only an arena, a war or a quest allows that here"), on the continent and
outside alike (the owner's scope names where, not which half of the world). `/ttl pvp why <a> <b>` (ops) and `/ttl pvp simulate
<a> <b>` (test hook) print the verdict. `[absorb.duel] dimensions` grows to the arena builds; the rev. 1 deposit mechanism is gone.
Reputation guards stay: a kill on a faction's ground costs `kill_penalty.player` (`guards.js:56-60`).

### 6.3 Reputation guards and moods
Nothing locks a quest. Hostile costs guards, shops and the dark lane's own prices. **Mood** (§3.3) shifts guards and shops one band
for everyone, never quest gates.

### 6.4 The Ten Legendaries — DECIDED

| Rule | Decision |
| --- | --- |
| Global ceiling | **stays**: `max_holders = 10`, the Ten Great Demon Lords (`registry.js:106-111`, every grant and transfer). |
| Per-holder cap | **none.** A soul may hold several (Rimuru did). |
| Inactivity | a Legendary **never** returns through inactivity (`sweep` skips `legendary`; `[registry] inactive_returns = ["rare", "common"]`): leaderboards and scores keep meaning. A soul away for a year still blocks a place; that is the price of the Ten, and the absorption routes are how a place is taken. |
| How a Legendary leaves a soul | only the absorption routes: duel (arenas), war (§6.5), bequest, awakening challenge (refusable with cost: renown −20, era title "Craven", a 30-day shield against the same challenger — **DECIDED** as recommended), `/ttl reset`, staff. |
| Era tenure (O-W13) | **DECIDED as recommended, mild**: at an era turn a holder defends within 30 days (an echo of their capstone boss, solo or raid) or the Legendary returns to the pool. The only non-absorption exit, announced for a month. |

### 6.5 War limits — DECIDED: an army, the nation rules, reparations for a winning defender

`nations.toml [war]` (new) and `nations.js`:

```toml
[war]
army_min = 5                 # named subordinates (majin) mustered by the nation's members, together
army_named_only = true       # only NAMED subordinates count (Tensura naming), not merely tamed ones
muster_radius = 32           # /ttl nation muster: subordinates within this many blocks of a member are counted
muster_valid_hours = 24      # a declaration needs a muster this fresh
notice_hours = 24            # the existing war_notice_hours
accept_or_active_days = 7    # without the defender's acceptance the war only starts if the defender had a member online within this many days
max_days = 7                 # a war ends by surrender, or after this long on points
score = { kill = 1, raid_objective = 5 }   # war points; the side with more points after max_days wins
surrender_cost_pct = 25      # of the surrendering nation's treasury, to the winner
reparations_cap_pct = 50     # the WINNING DEFENDER may demand up to this share of the attacker's treasury
tribute_weeks = 2            # … plus this many weeks of the attacker's upkeep paid into the defender's treasury
```

- **Army.** A subordinate is an entity whose Tensura existence names the player as permanent owner
  (`TensuraStorages.getExistenceFrom(e).getPermanentOwner()`, `manas-integration.md` row `getExistenceFrom`); *named* =
  `getName()` non-empty (Tensura naming, `NAMING_EVENT`). `/ttl nation muster` walks the loaded entities within
  `muster_radius` of every online member, counts them once by UUID, stores `rec.army = {n, at, by}` and scoreboard `ttl.army`
  on the members. **Verify in game** the storage reads from KubeJS on a tamed, named `tensura:goblin` and that a Tensura
  "temporary owner" is not counted. Unloaded subordinates are not counted — bring the army to the muster, as in the story.
- **Declaring** needs: owner, Life 2, a nation of rank ≥ `village`, a fresh muster ≥ `army_min`, the target not an ally, no war
  with it (existing rules), the charter stage. The target gets `/ttl nation war accept <n>` (war starts at once) or the notice
  runs and the war starts only if the defender is active (`accept_or_active_days`) — a dormant nation cannot be farmed.
- **During** a war: PvP allowed between the two nations' members inside `war_hours` (§6.2), war absorption (`absorb.war`)
  only then, claims untouched (FTB protection stays: a war is for people and thrones, not blocks), kills and raid objectives score.
- **Ending.** `surrender` by either owner (cost to the winner) or `max_days` on points. The winning **defender** may demand
  reparations within 48 h: `/ttl nation reparations <n> <gold>` up to the cap, taken from the attacker's treasury (what it does
  not hold becomes `owed`, paid before upkeep), plus `tribute_weeks` of upkeep. A winning attacker gets the glory line, the
  absorptions it made and the chronicle entry — not the defender's coins (owner's rule: reparations are for defenders).
- **Chronicle**: `wars`, `armies`, firsts (`first_war_won`), `#story` lines.

### 6.6 Canon nations are factions with protected domains, and a long road to their thrones — DECIDED

The canon nations (Tempest, Dwargon, Blumund, Falmuth, the Holy Church, the Lizardmen, Eurazania …) are the factions of
`factions.toml`. Each gets a **domain** and a **throne**:

```toml
# factions.toml additions (per [[faction]])
domain = { capital_radius = 256, builds = ["dwargon"], landmarks = ["dwarf_village"] }   # the protected land: a square around the capital + build boxes + landmark areas
throne = { boss = "gazel_dwargo", statue = "gazel_throne", seat = "dwargon" }            # the ruler fight and the seated anchor
territory = "domain"         # domain (default) | region: `region` protects the faction's whole canon letter (the wilderness too)
```

- **Protection** (`world/domains.js`): inside a domain on the continent a player who is not an op, not a **member** of that
  faction and not in the **ruling nation** cannot break or place blocks, light fire, pour fluids or start explosions (KubeJS
  `BlockEvents.broken/placed`, `ItemEvents.rightClicked` for buckets and flint, explosion events; TNT/creeper inside claims
  already fall under FTB Chunks' `protect_unknown_explosions`, our veto covers the rest). Doors, chests, crafting stations and
  NPC dialogue keep working — that is why a **block guard** is chosen over adventure mode: adventure mode flips a gamemode on
  every border crossing (ops, spectators, Tensura flight and Tombstone graves all have opinions about that) and still needs a
  guard for buckets and explosions. The Tempest domain includes the 192×192 growth square (§4). Outside the continent there are
  no domains (R11).
- **Respawning story NPCs** (owner answer 2): every spot (`npcs.toml`), resident (`tempest_extras`) and hook entity on the
  continent is re-summoned by its ensure loop when missing (Easy NPC spots already are: `guild_npcs.js ensureSpot`; residents
  and the Gazel seat get the same loop; `respawn_minutes = 5` knob). Killable ones (the goblins) stay killable and cost
  `kill_penalty.npc`; invulnerable ones stay invulnerable. Outside the continent: only natural spawns, nothing of ours.
- **Members.** A soul at Exalted with a faction (`ttl.faction.<f>.exalted`) with `favor_join` (50) radiant favour points (§6.8)
  may `/ttl faction join <f>` (one faction at a time, 30-day cooldown on leaving): stage `ttl.faction.<f>.member`, edit rights in
  the domain's **public works** areas (not the canon builds: `works_only = true`), a title, the faction's radiant board at better
  pay. Membership is personal; it never moves the throne.
- **The road to a throne** is one world-state-driven path per faction, opened by a **conflict** (a milestone effect; in canon,
  Walpurgis puts Eurazania in play, Act V puts Falmuth in play, the Dwargon pact opens Dwargon's). Steps, all recorded in the
  chronicle and shown by `/ttl faction road <f>`:
  1. the conflict is open (`ttl.world.conflict.<f>`);
  2. a **nation** of rank ≥ `city` whose owner is Exalted with the faction (vassal road) or Hostile with it and holds the
     faction's `kill_rep.flag` (usurper road: `regicide` for Dwargon);
  3. a mustered army ≥ `throne_army` (10) for the usurper road, or `throne_favor` (200 radiant favour points across the nation's
     members) for the vassal road;
  4. the throne fight: the faction's ruler boss as a **party instance** — an honour duel (`unless_flag`) for vassals, a regicide for
     usurpers; a lore-named proxy boss where no entity exists (O-W18);
  5. the **ceremony**: a world chapter quest (`world = true`) at the throne, claimable by the nation owner, whose command reward runs
     `ttl faction vassalize|usurp <f>` (checks every step again).
  Result `rule.<f> = {nation, mode}`: the nation's members get edit rights in the whole domain (`ttl.faction.<f>.ruler` on the
  owner, `.vassal` on members), the domain's guards obey the nation (mood follows the nation's path), a weekly `tithe_pct` (10) of
  the faction's radiant payouts flows into the nation's treasury, the faction's radiant board posts the nation's own templates,
  the canon ruler's **statue stays** with new lines (vassal: "my sword and my steward"; usurper: "the throne is yours; the hall
  remembers mine"); `#story`, a Hall line, a BlueMap marker. Nothing is removed; a usurped Dwargon still sells to a Friendly
  newcomer (shops read band + mood).
- **Contested.** Another nation may walk the same road against the ruling nation: the throne fight becomes a **war objective**
  (`raid_objective` points, §6.5) between the two nations, so a throne changes hands through the war rules, never by a solo
  kill. Losing the throne costs nothing but the throne (the one sanctioned stage removal of R6: the stage *is* the throne;
  `validate.py` allow-lists `thrones.js`).
- Thrones persist across eras by default (O-W16).

### 6.7 The March of the Horde: how the Orc Lord arrives — DECIDED (immersive, not a plain summon)

Canon (anime season 1, the Orc War episodes — "Gabiru Is Here!", "The One Who Devours All", "The Jura Forest Alliance";
light novel vol. 2 — **verify** the episode numbers against the Wikipedia episode list already cited in `quests.md`): a famine
in the orcs' southern lands sends two hundred thousand starving orcs into the Great Jura Forest; the majin Gelmud, Clayman's
agent, has *named* Geld an **Orc Lord** so that the horde devours everything in its path (the unique skill *Starved*: whoever the
Orc Lord eats, his horde gains); the lizardmen of Lake Siss muster and Gabiru's vanguard is routed; Rimuru's alliance of goblins,
lizardmen and Tempest holds the marsh; Gelmud is devoured by his own creation and Geld evolves into the **Orc Disaster** on the
battlefield; Rimuru devours him and takes *Starved*; the survivors are forgiven and the second Geld leads an orc nation of
builders. *Our interpretation*, marked as such in the quest texts: the horde's march is staged in the marsh at the orc camp
landmark (1106, 539), the alliance is the party, and Gelmud's role is played by the Outcast letter of the dark lane.

Design (`events/horde_march.js`, per party, inside the battlefield arena `{x = 1106, z = 539, radius = 64}`):

1. **Famine on the roads** (world, not party): once any soul reaches chapter 4's `scout_camp`, the director's `wild_boss` poll gets a
   sibling `horde_bands`: small starving orc bands (3–5 `tensura:orc`, `Tags:["ttl.horde"]`, hungry: they go for livestock and
   crops first — a target tweak via `EntityEvents`, **verify**) roam J/W/V and the roads; Treyni's and Souei's lines gain
   `world = { milestone = "horde_seen" }` warnings; the first band killed sets `horde_seen`. Killing them counts for `orc_hunt`.
2. **The line**: `hold_the_line` (20 orcs) becomes an instanced **wave fight** inside the arena: its first task is the location,
   its auto-claimed invisible `command` reward runs `ttl story march begin` (`TtlStory.march` → `TtlHorde.begin(party)`): three
   waves from the camp edge (`horde_march.toml`: `waves = [{orcs = 6}, {orcs = 8, shaman = 1}, {orcs = 10, captain = 1}]`),
   horn sound, title "The horde marches", the party's lizardmen allies as tame `tensura:lizardman` (named Gabiru's men, tagged,
   despawned at the end) fighting beside them. Waves scale with the party like a boss (`per_player_mult`).
3. **Geld's arrival**: when the third wave falls, the Voice says *"Something walks through the horde, and the horde parts."*;
   the Orc Lord instance is summoned at the camp edge **awake** (`opts.awake = true`, WP-W2: no NoAI wait), with four escorts,
   and walks in (never `tp`: the entity paths to the nearest party member; **verify** `tensura:orc_lord` pathing with NoAI 0);
   the boss record starts — party cooldown, queue, credit as any boss. `orc_lord_kill` reads `stage ttl.defeated.orc_lord`.
4. **Evolution**: Geld's enrage phase stays; the **Orc Disaster** is the separate `[[boss]]` as today (`requires = ["orc_lord"]`):
   the finale quest's reward `ttl story fight orc_disaster` summons him on the same battlefield within `evolve_minutes` (15) of
   Geld's fall with the line *"He devoured the one who named him. Geld evolves."* (dark lane: "your champion turns on you").
   Outside the window the Disaster is summoned by the quest as before.
5. **Wild**: the 3 %/day `orc_lord` wild roll stays as "a lord of a splinter horde" with escorts; the famine bands are not bosses.
   **Outside the continent** `tensura:orc_lord` spawns as the mod ships.
6. **Chronicle**: `kills.orc_lord`, `firsts.orc_lord`, `horde_seen`; after `threshold` souls finish Act III the camp becomes the
   **orc builders' camp** (Geld's corps, master plan §13): a small additive build at the landmark (`orc_camp_builders`) with a
   radiant board that pays merit — the canon ending, placed by the chronicle.

### 6.8 Radiant quests: repeatable quests generated from world state — DECIDED (quests are story AND random)

The FTB book stays the **story**; radiant quests are **generated** by `quests/radiant.js` from templates in
`design/data/radiant.toml`, offered on **boards** (an Easy NPC "Board" button or `/ttl radiant board`), taken per soul, tracked
in `ttl.radiant`, repeatable with cooldowns. They extend the guild (`economy/guild.js` already rolls `kill | deliver | visit`
bounties; radiant reuses its kill objectives `ttl.g.<entity>` and `TtlEcon` payouts) and feed the chronicle (`radiant.<f>`),
the takeover favour (`ttl.favor.<f>`) and the balance (`radiant_light/dark`).

```toml
[radiant]
per_player_open = 3          # offers held at once
per_board_offers = 5         # offers shown per board per roll
roll_hours = 6               # boards re-roll
weekly_cap = 15              # completions per soul per week (the guild's anti-farm pattern)
favor_per_quest = 1          # favour points with the board's faction (membership, the vassal road)
outside_continent = true     # radiant quests may send souls to the free lands (kill/collect there: the mod's own spawns)

# Boards: where offers are read. `faction` = whose favour and rep they pay; `path` = who sees it (any | light | dark).
[[board]]
id = "tempest_council"
faction = "tempest"
npc = "benimaru"             # the Talk button of this cast kind gets a "Board" button
path = "any"
[[board]]
id = "outcast_contact"
faction = "outcast"
npc = "outcast_contact"
path = "dark"
[[board]]
id = "free_guild"            # Fuze's existing board keeps its [[bounty]] rows; radiant adds to it
faction = "blumund"
npc = "fuze"

# Templates. `kind`: kill (count of an entity in a region) · collect (hand in items) · visit (a landmark/build/random spot in a
# region) · escort (walk an Easy NPC from A to B; it follows, dies if left) · clear (a camp: a mini-instance of n mobs + a captain
# around a random spot, like a wild boss spot) · defend (hold a spot for m minutes against waves) · hunt (a wild/echo boss id) ·
# build (place n ttl:infrastructure blocks in a Public Works chunk of the region) · deliver (carry a sealed letter to another board)
# `where`: region letters, "domain" (the board's faction domain), "outside" (beyond the ring) · `weight`: base weight, then
# `weight_if` multipliers read from the chronicle view: tide, phase, conflict, mood, milestone, wild_active.
[[template]]
id = "cull_the_famine_bands"
kind = "kill"
entity = "tensura:orc"
count = [8, 16]
where = ["J", "W"]
boards = ["tempest_council", "free_guild"]
weight = 3
weight_if = { milestone = { horde_seen = 3 }, tide = { dark = 1.5 } }
reward = { coins = { silver = 6 }, rep = { tempest = 3 }, renown = 1 }
text = "Starving bands of orcs raid the roads. Thin them out before the farms go."

[[template]]
id = "escort_the_caravan"
kind = "escort"
npc_kind = "caravan_master"
from = { build = "dwargon" }
to = { landmark = "tempest" }
boards = ["tempest_council"]
weight = 2
weight_if = { milestone = { dwargon_pact = 2 }, conflict = { dwargon = 0 } }
reward = { coins = { gold = 1 }, rep = { dwargon = 4, tempest = 2 }, renown = 2 }

[[template]]
id = "break_the_watch"
kind = "clear"
mobs = { "tensura:falmuth_knight" = 6 }
captain = "tensura:falmuth_knight"
where = ["F"]
boards = ["outcast_contact"]
path = "dark"
weight = 2
weight_if = { conflict = { falmuth = 2 } }
reward = { coins = { silver = 10 }, rep = { outcast = 4, falmuth = -3 }, renown = 2 }

[[template]]
id = "the_hunt"
kind = "hunt"
boss = "any_wild"            # the wild boss currently roaming, else an echo the party may summon
boards = ["free_guild", "tempest_council"]
weight = 1
weight_if = { wild_active = 4 }
reward = { coins = { gold = 2 }, renown = 5 }
```

Rules: a radiant quest never gates the story and never pays a unique (rule 5(d)); it is personal (party members may take the
same offer); offers are rolled from the **chronicle view** so the board reads the world (a dark tide shows culls and defences,
a conflict shows sabotage and escorts, a city phase shows deliveries and builds); `clear`/`defend` spots use the wild-spot
picker (`wild.js pickSpot`: loaded chunk, right surface, outside domains); `escort` NPCs are Easy NPC `follow` kinds (**verify
in game** the Easy NPC 7.19 follow objective from a preset). Completion: `TtlRadiant.complete` pays through `TtlEcon`/`TtlRep`,
notes the chronicle, adds favour. Weekly cap, 30-min cooldown per template per soul; `clear` instances are removed after
`idle_minutes` like a boss. `/ttl radiant board|take <n>|drop <id>|status|expect` with the usual `ttl:` assertions.

## 7. MMO-scale rules at 10–30 players

### 7.1 Instancing (`bosses.toml [framework]`, WP-W2) — DECIDED
```toml
cooldown_scope = "party"       # a party/raid is on cooldown while ANY member's ttl.boss.lastkill[id] is inside cooldown_hours
arena_gap_minutes = 10         # global pause per arena after a defeat
max_instances = 4              # story + wild bosses alive on the continent
max_per_party = 1
queue_ttl_minutes = 20
echo_prefix = "Echo · "
echo_hp_mult = 0.85
```
`summon()` refuses "already out there" only for the **same arena**; a refused party is queued in `ttl.boss.queue[id]`, told its
place and ETA, pinged when the arena frees (then `queue_ttl_minutes` to summon). Wild and story never block each other.

### 7.2 Anti-hoarding
Skill Cores `core_cap_week = 2` per soul; repeat kills by the same party inside `repeat_window_days = 7` pay `repeat_mult = 0.5`
on coins and rep (never the stage). Legendaries: **no per-holder cap** (DECIDED); the Ten is the only ceiling. Radiant: weekly cap.

### 7.3 World firsts
`firsts.<boss>` from `finish()` names (party and raid included; the first kill belongs to everyone credited). Era titles
`pioneer`, `gatekeeper`, `unbroken`, `craven`, `first_war_won`; Hall sections "Firsts of the era" and "The world this week".
A first is never gated; an echo party can still be first on an unbeaten boss. Outside-continent kills never count as firsts.

### 7.4 Eras and resets — DECIDED
An era turn archives `ttl.world`, resets `balance` and `tide`, keeps `phases`, `milestones`, `firsts`, `rule` (default; O-W16).
`/ttl worldreset` stays an ops tool between eras, documented as such (H13).

### 7.5 Admin tooling
`/ttl world` (status) · `log [n]` · `balance add <n>` · `milestone fire|list` · `phase set <place> <phase>` · `conflict open|close <f>` ·
`rule set <f> <nation> <mode>|clear` · `recount` · `export` · `expect <field> <value>` · `/ttl boss queue [id]` · `/ttl raid …` ·
`/ttl pvp why|simulate` · `/ttl nation muster|war accept|surrender|reparations` · `/ttl faction join|leave|road|vassalize|usurp` ·
`/ttl radiant …` · `/ttl domain check <x> <z>` (inside/outside, domain, who may edit). Every ops change logs `[ttl] world:`.

## 8. Discord and BlueMap hooks (DECIDED: `#story`)
One `TtlDiscord.post` per milestone, tide, raid outcome, first kill, war start/end, throne change and era archive; `hall.js
recapText` gets "The world this week" and the leaderboard "Firsts of the era" and "Thrones" blocks (`TtlHall.noteWorld`). BlueMap:
`gen_map.py:12` is static; live "World" markers (Tempest phase, raid zones, arenas and queues, wild bosses, nation homes, wars,
thrones, domains as area markers) through `Java.loadClass('de.bluecolored.bluemap.api.BlueMapAPI')` (**verify** reachable from
KubeJS 2101 and `/reload`-safe), fallback ttl-ops: every 10 min `rcon "ttl world export"` → `tools/gen_map.py --live` → `bluemap
reload`. Tests stay silent through the existing mute (`discord.js:45-55`).

## 9. Migration of existing state (one boot, idempotent)

| State today | Becomes | How |
| --- | --- | --- |
| `ttl.boss.last.<id>` | per-soul `ttl.boss.lastkill` | the global stamps are read once as an `arena_gap` from boot, then ignored |
| `ttl.boss.active` records | gain `party`, `echo`, `awake` | missing `party` = `''` |
| `ttl.boss.kills`, acts, flags (per player) | chronicle counts | login backfill (`ttl.world.counted`) |
| `ttl.story.log`, `ttl.reg.history` | `firsts`, `counts.legendary` | first boot |
| `ttl.story.parties` | pruned of dead team ids | chronicle sync |
| `ttl.tempest.version = 3` | `phases.tempest = "village"` | first boot |
| Tempest residents | tagged `ttl.npc.tempest`, kept by the respawn loop | `data merge entity` + `tag add` at load; the loop re-summons a missing resident at its spot (`tempest_extras.residents`) |
| Build boxes, Tempest/Dwargon boxes, landmark areas | domains (`factions.toml domain`) | read as they are |
| Chapter 4 `hold_the_line` / `orc_lord_kill` | wave fight + `stage ttl.defeated.orc_lord` | same quest keys; the kill task's id changes type (nobody could finish it); decisions row |
| `[registry] inactive_days 30` | unchanged for Rare/Common; Legendary exempt | `inactive_returns` knob; a holder already swept of a Legendary before this lands is restored by staff from `ttl.reg.returned` (`/ttl registry restore <p>`, one-off ops command in WP-W8) |
| PvP | from open to the rules pass | announced in `#patch-notes` (`docs/patch-notes/`) a week ahead; `mode = "always"` is the rollback knob |
| Era | the current era's `ttl.world` starts now | first boot |

Launch checklist (`docs/HANDOFF.md`): add `/ttl world recount`, `/ttl boss queue clear`, `/ttl radiant roll`, `/ttl nation muster` test rows.

## 10. Work packages (one agent each, ≤ ~70 min, owned files only; cross-system call sites are one reserved, guarded line)

| # | Package | Owns | Deps | Bot test (`tests/ingame/<x>.rcon`) |
| --- | --- | --- | --- | --- |
| **Wave A** | | | | |
| WP-W1 | **Chronicle core + continent test**: `TtlWorld.onContinent`, `TtlChronicle.note/count/balance/tide/milestones/phase/mood/conflict/rule/sync/view/export/lines`, login backfill, 5-min sync, era archive | `world/chronicle.js`, `world/commands.js`, `design/data/world.toml`, `gen_data.py check_world`, `tests/ingame/world.rcon`; reserved lines: `story.js` (`applyOath`, `act`, `flip`, `flag`), `boss.js finish` + `checkSpawn` (continent), `nations.js` (`found`, `declareWar`, `endWar`, `dropRecord`), `registry.js log`, `era.js next`, `rep.js guardsHostile/shopOpen` (mood), `guards.js onDeath` (continent) | — | three Life 2 bots: oath ×2 + `act … 2` ×3 (ops) → `ttl world expect counts.acts.light.2 3`, `expect milestone act2_reached yes`, a 4th bot gets `ttl.world.act2` at login; `ttl world balance add -40` → `expect tide dark`; `ttl world expect continent 0 0 yes`, `… continent 9000 0 no`; `milestone fire tempest_town` → `expect phase tempest town` (phase hook stub logs) |
| WP-W2 | **Boss instancing**: per-party cooldown, arena lock + queue, `max_instances`/`max_per_party`, wild/story separation, echo prefix + hp, `opts.awake`, `kind = statue` hides the seat, `TtlRaid.groupOf` hook, `block_natural` only on the continent | `bosses/boss.js`, `bosses/wild.js`, `bosses/commands.js` (`queue`, `expect <p> busy|queued|cooldown`), `design/data/bosses.toml`, `tests/ingame/bosses.rcon`, `tests/ingame/wild.rcon`; reserved line in `life/dwargon.js ensure` | — | party A (testparty) kills `orc_lord` → `expect a cooldown orc_lord yes`; bot c alone → `ttl story fight orc_lord` summoned; `wild roll shizu` while a story Shizu is out → started; two `gazel_dwargo` summons → `expect c queued gazel_dwargo yes`, `boss abort` → `… no`; `summon orc_lord 9000 70 0` (outside) refused "outside the continent: the mod's own spawns rule there" |
| WP-W3 | **Domains + respawning story NPCs**: `TtlDomains.of(x,z)/canEdit/protect`, block/fire/fluid/explosion veto, membership stages read-only here, resident respawn loop, `ttl.npc.<f>` tags | `world/domains.js`, `design/data/factions.toml` (`domain`, `throne`, `territory`), `gen_data.py check_factions` (domain refs), `life/tempest.js` (resident respawn + tags), `tests/ingame/domains.rcon` | — | a non-op bot `setblock` at the Tempest green via `execute as` → unchanged, `ttl domain expect <bot> edit 0 0 no`; same at 9000 0 → yes; `kill @e[name=Rigurd]` → within 300 ticks `ttl cast expect hook_rigurd found` |
| WP-W4 | **PvP rules pass** (arenas, wars, quest flags, event sides; duel pacts only in arenas) | `pvp/pvp.js`, `pvp/commands.js`, `design/data/pvp.toml`, `gen_data.py check_pvp`, `tests/ingame/pvp.rcon`; `skills.toml [absorb.duel] dimensions` + arena builds | — (reads `TtlAbsorb`, `TtlNations`, `TtlRaid` at run time) | `ttl pvp simulate a b` → refused; `ttl absorb war a b` (staff flag, `war_hours = []` in the test) → allowed (war); both in `tensura:labyrinth` → allowed (arena); stage `ttl.quest.pvp.t1` on both → allowed (quest) |
| **Wave B** | | | | |
| WP-W5 | **Tempest phases** (rings, residents and guards per phase, `TtlTempest.grow`, `min_phase` spots, core-preserving test) | `blueprints/tempest_town.py`, `tempest_city.py`, `tools/build_structures.py`, `pack/kubejs/data/ttl/structure/tempest_*_ring.nbt`, `generated/tempest_footprint.js`, `life/tempest.js` (`grow`, `phase`), `design/data/npcs.toml`, `economy/guild_npcs.js` (`active` reads `min_phase`), `tests/test_tempest_phases.py`, `tests/ingame/tempest_phase.rcon` | W1, W3 | `ttl world phase set tempest town` → `[ttl] tempest: town ring placed`, chapter-2 anchors still solid, `ttl cast verify all` 0 failed |
| WP-W6 | **Catch-up + echo** | `story/catchup.js`, `world.toml [catchup]`, `design/data/guide.toml` page, `tests/ingame/catchup.rcon`; reserved lines in `party.js admit`, `story.js fight/act`, `favor.js eligible` | W1, W2 | late bot (`ttl.l2.arrived` faked, acts 0, `ttl.world.act3` set) → `expect <bot> late yes`; EP sample hook → log `grace +100`; party join + `ttl catchup skip` → `ttl story expect <bot> act 3 yes`, `ttl rep expect <bot> dwargon band neutral` |
| WP-W7 | **Raid groups** | `party/raid.js`, `party/commands.js`, `bosses.toml [raid]`, `tests/ingame/raid.rcon` | W2 | light a invites dark c → both `ttl boss expect … defeated orc_lord yes`; raid gone after the kill |
| WP-W8 | **Legendary rules + war rules**: Legendary exempt from the sweep (+ `restore`), refusable challenge, army muster, war acceptance/active-defender, surrender, points, reparations, war-hours absorption | `registry.js` (sweep, `restore`), `absorb/absorb.js` (`refuse`, war hours), `nations/nations.js` (`muster`, `acceptWar`, `surrender`, `score`, `reparations`), `nations/commands.js`, `design/data/skills.toml`, `design/data/nations.toml [war]`, `gen_data.py check_nations`, `tests/ingame/absorb.rcon`, `nations.rcon`, `legendary.rcon` | — (W4 optional) | `registry seen <p> 40` + sweep → the bot's Rare returned, its Legendary kept (`registry expect holders 1`); `challenge` → `refuse` → pact gone, renown −20; declare without muster → refused "no army"; tame + name 5 goblins (`tensura edit owner … permanent set`, naming; **verify**) + `muster` → `nation expect <p> army 5`; declare → `accept` → active; `surrender` → treasury −25 %; defender wins on points → `reparations` → attacker treasury down |
| WP-W13 | **Radiant quests v1**: templates, boards, kinds kill/collect/visit/deliver/build, chronicle view weights, favour, caps | `quests/radiant.js`, `quests/radiant_commands.js`, `design/data/radiant.toml`, `gen_data.py check_radiant`, `tests/ingame/radiant.rcon`; reserved lines: `economy/guild.js` (objective reuse), `economy/guild_npcs.js` (board button), `story/cast.js` (statue board) | W1 | `ttl radiant roll tempest_council` → 5 offers logged; bot `take 1` (a kill template), `ttl radiant expect <bot> open 1`; kills via the objective hook → `complete` → coins present, `ttl world expect counts.radiant.tempest 1`, `expect <bot> favor tempest 1` |
| **Wave C** | | | | |
| WP-W9 | **Dark-deed events** (`horde_raid`, `outcast_uprising`, `holy_hunt`, `dwarven_caravan`, `requires.unlocked`, sides, defenders' rewards, the `rebuilding` world chapter) | `events/raid.js`, `events/uprising.js`, `events/hunt.js`, `events/caravan.js`, `design/data/events.toml`, `design/quests/chapter_14_rebuilding.toml` (`world = true`), `tests/ingame/raid_event.rcon`; reserved line in `director.js blocked` | W1, W4, W7, WP-S8 (else own waves) | `milestone fire tempest_town` → `events fire horde_raid` → orcs + an orc_lord instance at the south gate; kill with two bots in the zone → `expect raid defenders 2`, `world expect counts.raidsWon.defenders 1`; `side horde` bot → `pvp simulate` allowed inside the zone only |
| WP-W10 | **Discord + BlueMap + Hall** | `discord/chronicle.js`, `discord/hall.js`, `tools/gen_map.py --live`, `docs/server.md` | W1 | `ttl world export` prints one JSON line with `phases`, `firsts`, `rule`; a milestone with mute off and no bots logs the posted line |
| WP-W11 | **Quest wiring**: `world = true` chapters + the R7 check, `[[npc.talk]] world = {…}` in `TtlStory.pick`, echo/phase/rule lines in `story.toml`, `quests.md` | `tools/gen_quests.py`, `design/quests.md`, `design/data/story.toml` (talk entries), `story/story.js pick`, `tests/test_gen_quests.py`, `tests/ingame/quests.rcon` | W1, W5 | `gen_quests.py --check` fails on a chapter 0–13 quest with a `ttl.world.*` task; `talk mildo` with the town stage → the town line |
| WP-W12 | **Fairness + docs**: era titles, core cap, `repeat_mult`, admin polish, `master-plan.md` divergence notes (§6, §7, §9, §12, §14), `decisions.md` rows, `roadmap.md`, `docs/discord-guides.md`, `docs/HANDOFF.md`, `#patch-notes` draft for the PvP change | those files, `bosses/boss.js reward` | all | `ttl boss expect <p> cores 2` after three T3 kills in a week |
| WP-W14 | **March of the Horde**: famine bands, wave fight, Geld's awake arrival, evolution window, chapter 4 rewiring, builders' camp build | `events/horde_march.js`, `design/data/horde_march.toml`, `gen_data.py check_horde`, `design/quests/chapter_4_orc_lord.toml`, `design/builds/orc_camp_builders.toml` + blueprint, `tests/ingame/horde.rcon`; reserved line in `story.js` (`march`) | W1, W2 (`opts.awake`) | bot at the marsh → `ttl story march begin` (ops) → three waves logged, `expect <bot> wave 3 done` → `[ttl] horde: Geld arrives`, `ttl boss expect <bot> active orc_lord yes`; kill → `expect <bot> defeated orc_lord yes`; `ttl story fight orc_disaster` within 15 min → summoned with the evolution line |
| WP-W15 | **Radiant v2 kinds**: escort, clear, defend, hunt (instances via the wild spot picker), one board per canon capital | `quests/radiant_kinds.js`, `design/data/radiant.toml` rows, `design/data/npcs.toml` (`caravan_master` follow kind, boards), `tests/ingame/radiant_kinds.rcon` | W13, W2 | `take` a clear template → a camp of 6 + captain near the bot (log), kill all → complete; escort NPC follows the bot (`verify` follow) |
| **Wave D** | | | | |
| WP-W16 | **Canon thrones**: membership (`join/leave`), the road (`/ttl faction road`), vassalize/usurp ceremony, rule effects (edit rights, tithe, guards, statue lines), contested thrones as war objectives, BlueMap/Hall lines | `world/thrones.js`, `world/commands.js` (faction subtree), `design/data/factions.toml` (`throne_army`, `throne_favor`, `tithe_pct`, `works_only`, `favor_join`), `design/quests/chapter_15_thrones.toml` (`world = true`, one ceremony quest per faction), `design/data/story.toml` (ruler statue lines), `tests/ingame/thrones.rcon`; reserved lines in `domains.js canEdit` (rule), `nations.js score` (objective) | W1, W3, W8, W11, W13 | `world conflict open dwargon`; a nation of rank city (value test hook) with owner Exalted + favour 200 (ops `favor set`) + an `honour_duel` kill of `gazel_dwargo` → `ttl faction vassalize dwargon` → `world expect rule.dwargon.mode vassal`, `ttl domain expect <member> edit 435 -1106 yes`; a second nation declares war + takes the throne objective → `rule.dwargon.nation` changes |

Waves: **A** WP-W1 WP-W2 WP-W3 WP-W4 → **B** WP-W5 WP-W6 WP-W7 WP-W8 WP-W13 → **C** WP-W9 WP-W10 WP-W11 WP-W12 WP-W14 WP-W15 → **D** WP-W16.
Each package ends with `validate.py` green, `server.sh test <name>` green, no new `[ttl]` errors, a `decisions.md` row.
Priorities: `world/chronicle.js` 72, `pvp/pvp.js` 71, `world/domains.js` 71, the rest 70, commands 60.

Verify-in-game list (owned by the depending package): the continent test at the coast (W1); FTB per-player reward claims and
personal `TeamData` after leaving (W6); repeated `tensura edit stat … ep current add` (W6); `BlueMapAPI` from KubeJS (W10);
`beforeHurt` ordering pvp.js/absorb.js (W4); `data merge entity` on a loaded goblin keeping its name (W3); Tensura existence
`getPermanentOwner`/`getName` from KubeJS on a tamed, named mob (W8); `tensura:orc_lord` pathing when summoned awake (W14);
Easy NPC follow objective from a preset (W15); the episode numbers of the Orc War (W14, quest texts).

## 11. Owner decisions

| # | Question | Status |
| --- | --- | --- |
| O-W1 | Boss availability: per-party cooldown + arena queue vs multi-instancing | **DECIDED: per-party cooldown + queue.** |
| O-W2 | PvP scope | **DECIDED: only in special quests, arenas and declared wars** (Life 1 stays open: earlier decision). |
| O-W3 | Duel in a public place: deposit/refuse/free | **Superseded**: duel pacts count only in arenas (O-W2); no deposit. |
| O-W4 | Raiders win at Tempest → rebuilding week, never a phase regress | **DECIDED** as recommended. |
| O-W5 | Inactivity and per-holder cap for Legendaries | **DECIDED: no per-holder cap; no inactivity loss for Legendaries; the ceiling of ten stays.** Rare/Common keep the 30-day return. |
| O-W6 | Awakening challenge refusable with cost | **DECIDED** as recommended (renown −20, "Craven", 30-day shield). |
| O-W7 | Thresholds max(3 souls, 25 %); town at Act III, city at Act VI | **DECIDED** as recommended. |
| O-W8 | War consent + surrender cost | **DECIDED, extended**: an army of named subordinates is required to declare; the winning defender may demand reparations (§6.5). |
| O-W9 | Chronicle lines in `#story` | **DECIDED** as recommended. |
| O-W10 | Era turn resets balance/tide, keeps history | **DECIDED** as recommended. |
| O-W11 | Skip-ahead pays 50 % renown, no rep, no flags | **DECIDED** as recommended. |
| O-W12 | Tempest growth square 192×192 protected from day 1 | **DECIDED** as recommended (now part of the Tempest domain). |
| O-W13 | Era tenure for the Ten (defend within 30 days of an era turn) | **DECIDED** as recommended (mild). |
| O-W14 | Dwargon: mood only, no growth ring | **DECIDED** as recommended. |
| O-W15 | Scope of a canon nation's protected territory: the **domain** (capital radius 256 + its builds + landmark areas; the region's wilderness stays free for player nations) or the whole canon **region** letter | **Open.** Recommendation: **domain** (`territory = "domain"`). The whole letter would leave nowhere on the continent to found a player nation (`nations.js:436-447` seeds the home faction from the region you stand in) and would make the free lands the only building ground; the per-faction knob `territory = "region"` exists for the ones that should be sealed (the Holy City). |
| O-W16 | Do canon thrones persist across eras? | **Open.** Recommendation: **persist** (a forever world); `/ttl world rule clear` is the staff tool if an era story needs a clean board. |
| O-W17 | Army numbers: `army_min = 5` named subordinates to declare war, `throne_army = 10` to usurp a canon throne, `throne_favor = 200` radiant favour to vassalize | **Open.** Recommendation: these starting values; tune after the first war. Named only (Tensura naming costs EP, so an army is an investment). |
| O-W18 | Thrones without a mod entity (Blumund's king, Falmuth's Edmaris): a lore-named proxy boss (the Clayman pattern, O3) or vassal-only thrones (favour road, no usurper road) | **Open.** Recommendation: **proxies** for Edmaris (the fight is Razen; `tensura:greater_daemon` was rejected in O4 — propose a scaled, lore-named `tensura:falmuth_knight` "Razen, the Court Mage") and Blumund; the Church's throne is Luminous (exists), Eurazania's is Carrion (exists), Dwargon's is Gazel (exists), Tempest's is Rimuru (`rimuru_ogre_fight`, **vassal road only**: Tempest is never usurped, it is the players' own capital). |
| O-W19 | Radiant boards: the three listed, or one per canon capital | **Open.** Recommendation: the three at launch (Tempest council, Outcast contact, Fuze), one per canon capital as WP-W15 content. |
| O-W20 | Orc Lord arrival staging as in §6.7 (famine bands, three waves, Geld walks in awake, the Disaster within 15 min) | **Open** (the owner asked for the design): recommendation is §6.7 as written; the lore reading is flagged "our interpretation" in the quest texts, episode numbers to verify. |

---
**Owner decision 18/11/2026 (Yasuke): "volg ze maar"** — O-W15 … O-W20 are DECIDED with the recommendations above
(protection = domain only; thrones persist across eras; army sizes 5/10/200; thrones without a mod entity use proxies,
Tempest only via the vassal path; boards at the Tempest council, the Outcast contact and Fuze; Orc Lord staging as §6.7).
