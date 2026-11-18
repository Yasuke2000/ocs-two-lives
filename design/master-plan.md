# OCS Tensura: Two Lives — Master Plan

Nov 15, 2026 · @David Delporte

> **Status 18/11/2026.** This is the original design of 15/11/2026 and it stays the statement of intent. Where the
> build went another way, the values in the text were changed and the section carries a "Status 18/11/2026" note.
> Why: `decisions.md`. What is done: `roadmap.md`. The data schema in force: `CLAUDE.md`. Work is planned in
> Sprints 1-4 (`roadmap.md`) instead of the Phases below.

| Topic | Plan (15/11) | Now (18/11) |
| --- | --- | --- |
| Unique caps | Legendary 1, Rare 1 + 2, Common 1 + 4; `trulyUnique true` | Legendary 3, Rare 3, Common 5 holders (`design/data/skills.toml`); `trulyUnique false` |
| Rebirth tiers | Underdog / Normal / Elite / Legendary | Wanderer / Survivor / Hero / Legend, plus the Fallen dark path (`design/data/karma.toml`) |
| Corridor | Voice NPC offers 2-3 races, `/ttl choose` | Last Wish (10 wishes) + Trial of the Soul (10 arenas) + the Great Sage reincarnation ceremony |
| Life 1 worlds | Mortal Realm | + Mortal Nether and Mortal End (own portals and dragon fight, `ttl-portals` Java mod) |
| Life 1 finale | "The Iron Tyrant" | The Mortal Dragon (Mortal End); the Iron Tyrant is postponed |
| Lore map | WorldPainter region, 6-10k blocks | Canon continent from worldgen (`ttl:canon_map`), about 14,000 blocks wide |
| Discord | Bridge mod + custom sidecar bot; whitelist | Simple Discord Link (`sdlink`) as bridge and bot; joining through Discord account linking |
| Voice of the World NPC | Easy NPC | A glowing allay (`life/voice_npc.js`) |
| Quest source | YAML | TOML (`design/quests/*.toml`) |
| Registry reconcile | Every 10 minutes | Every 5 minutes, on login and after a rebirth |
| Hosting | Rented 16 GB host, -Xmx12G | Homelab K3s, node3: 7 GB heap in a 10 GiB pod, view distance 16 |
| Pull requests | - | A code-owner approval is required (supersedes the 17/11 "no approvals" row) |
| PvP in Life 1 | Off (Q12) | Open (owner decision) |
| Boss capture | - | Bosses can be bound as a Tombstone familiar only by a player who has slain them (`design/data/bosses.toml`) |

## Vision and what we keep from OCS

OCS Tensura: Two Lives is a from-scratch rebuild of OCS Tensura RPG (1.19.2 Forge, 114 mods) on Minecraft 1.21.1 NeoForge, for a 10+ player server. Every player lives twice: a hardcore human life in a mortal world, then a reincarnation into the Tensura world shaped by how they lived.

**Pillars**

- **Two lives.** Life 1 is hardcore and human-only; Life 2 is normal Tensura survival. Karma from Life 1 decides which races and uniques you can choose from, plus starting reputation.
- **A living Tensura world.** A hand-built, pre-mapped lore region with mostly canon NPCs and a spinoff story; random world beyond it.
- **Politics that matter.** Nations, wars, diplomacy, a Demon Lord council and a unique-skill economy where skills change hands.
- **Lore-tiered tech and magic.** Create to Immersive Engineering along the series' tech ladder; four magic systems, each with a lore home.
- **Lots of bosses and quests.** A T0–T4 boss ladder from Tensura and other mods, 500+ quests and Voice of the World events.
- **A forever world.** Yearly eras, never wiped; builders and nations leave a lasting mark.
- **Runs well.** About 200–230 mods, curated, profiled, mid-range PCs, heavily automated.

**Kept from OCS (the best of it)**

| From OCS | In Two Lives |
| --- | --- |
| Outcast Society name and identity | Becomes a lore faction: reincarnators rejected by every nation, with its own quest line |
| Iron's Spells + Tensura compat | Main magic pillar, runs on Tensura magicules |
| Mowzie's Mobs | Imported bosses, re-themed as Tensura threats |
| Enhanced Celestials | Blood and harvest moons as server events |
| Towns and Towers | Structures outside the lore region only |
| Corail Tombstone | Graves in Life 2 only |
| Artifacts, Relics, Curios | Relic loot and soul-bound slots |
| AttributeFix, Clumps, Controlling | Kept as utilities |
| Complementary shaders | Included, off by default |

**Not carried over:** Mekanism, Thermal, Compact Machines, Flux Networks, Pipez (replaced by Create), Botania and Mahou Tsukai (extra mana systems), Knight Quest, Samurai Dynasty, Mythic Mounts, OPaC compat (replaced by FTB compat), and old optimizers (Canary, LazyDFU, ServerCore, Lightspeed).

## Locked decisions

The base is Minecraft 1.21.1, NeoForge 21.1.x, Tensura: Reincarnated 2.0.1.x, KubeJS 2101.x, built as a git repo with packwiz and Claude Code. Defaults marked "default" were chosen for questions still open; change any of them in this table.

| # | Decision | Choice | Status |
| --- | --- | --- | --- |
| D1 | Version and loader | MC 1.21.1, NeoForge, Tensura 2.0.1.x (pin exact jars) | Decided |
| D2 | Build method | Pack-as-code: packwiz + git + Claude Code + headless test server over RCON | Decided |
| D3 | Life 1 → Life 2 | Cancelled death, then a strip list (inventory, ender chest, non-soulbound Curios, race and stats reset) | Decided |
| D4 | What carries to the soul | Anything metaphysical: XP, advancements, quest progress, learned spells, karma, merit, titles, reputation memory, soul-bound items | Decided |
| D5 | Unique skills | KubeJS skill registry with rarity tiers; all grants and revokes go through it | Decided |
| D6 | Nations layer | Warring Nations on FTB Teams/Chunks + KubeJS Tensura politics; fallback is pure FTB + KubeJS | Decided |
| D7 | Lore | Mostly canon spinoff: canon places and NPCs, own storyline, Outcast Society as an original faction | Decided |
| D8 | Tech pillar | Lore-tiered: Create (Dwargon/Tempest industry) → Create: New Age (Tempest magic-science) → Immersive Engineering as Eastern Empire magitech, gated late; no Mekanism (stability) | Decided |
| D9 | Mob difficulty | L2 Hostility for normal mobs; KubeJS scaling for bosses; no Apotheosis adventure module | Default |
| D10 | Enchanting | Apothic Enchanting as a standalone module, if available on 1.21.1 | Default, verify |
| D11 | Ice and Fire | Community Edition, Phase 3 optional only (beta history, heavy) | Default |
| D12 | Map | FTB Chunks for claims and minimap; BlueMap for the web map | Default |
| D13 | Excluded | Epic Fight, Better Combat, Tensura: Predation, Elite Tensura as a core | Decided |
| D14 | Quest source | TOML in the repo (`design/quests/*.toml`), converted to FTB Quests SNBT by `tools/gen_quests.py` | Decided; was YAML, changed 18/11/2026 |
| D15 | Pack name | OCS Tensura: Two Lives, published as v3.0 on the existing OCS CurseForge project | Default |
| D16 | Magic systems | Three at launch, each with a lore home: Tensura native (core), Iron's Spells (bridged to magicules), Occultism (summoning, demon contracts); Ars Nouveau (elven glyph magic) added in a later era | Decided |
| D17 | Rebirth choice | Each tier unlocks a range of races and unique-skill picks; karma gives an affinity bonus, never a lock | Decided |
| D18 | Seasons | Yearly eras; the world is never wiped and mod versions stay frozen; new content through KubeJS, datapacks and quests | Decided |
| D19 | Infrastructure | Public works earn Merit in Life 2 and Order/Craft karma in Life 1 | Decided |
| D20 | Discord | Simple Discord Link (`sdlink`) as chat bridge, bot and account linking; KubeJS posts and syncs roles through it, no sidecar bot | Decided; was a bridge mod + custom bot, changed 18/11/2026 |

## Mod list

The MVP is about 90 mods; the full pack lands at 180–230. Every mod must have a NeoForge 1.21.1 build before it is added; Claude Code checks this with `/add-mod`.

| Category | Mods | Phase | From OCS |
| --- | --- | --- | --- |
| Tensura core | Tensura: Reincarnated + ManasCore, Not Enough Bosses, Tensura Compat: FTB, Tensura Compat: Iron's Spells, TensuraMoreConfig | 0 | Tensura, Iron's compat |
| Tensura optional | Tensura: Bug Fixes (test first), Unique Races, Great Sage (client), Mysticism / TR Addon (extra races) | 1–3 | — |
| Scripting and quests | KubeJS, LootJS, FTB Library, FTB Teams, FTB Chunks, FTB Quests, FTB XMod Compat, Easy NPC | 0 | — |
| Nations and economy | Warring Nations, Lightman's Currency (+ Create compat, Shoppers), LuckPerms | 2 | — |
| Tech, by lore tier | Create 6 + 2–4 addons (industry); Create: New Age 1.2.0 (magic-science: electricity, generators, reactor); Immersive Engineering 12.4.x (Eastern Empire magitech: multiblocks, revolver, railgun, chemthrower) | 1, 2, 3 | Mekanism replaced by IE |
| Magic | Iron's Spells; Occultism + Create: Occult Engineering (summoning); Ars Nouveau 5.11.x (later era, elven magic); Apothic Enchanting (verify) | 1–3 | Iron's |
| Bosses and mobs | L\_Ender's Cataclysm, Mowzie's Mobs, L2 Hostility, Born in Chaos, Twilight Forest (verify), Neo Daily Boss | 2–3 | Mowzie's |
| World and events | Enhanced Celestials, Towns and Towers, Chunky (pregen) | 1–3 | Celestials, Towns and Towers |
| Loot and gear | Artifacts, Relics, Curios, custom KubeJS relics | 1 | All three |
| Storage and QoL | One storage system (Sophisticated Backpacks/Storage), JEI or EMI, Jade, AppleSkin, Corail Tombstone, Controlling, Clumps, AttributeFix | 1 | Tombstone, Controlling, Clumps, AttributeFix |
| Social | Simple Discord Link (chat bridge, bot, account linking; DiscordBridge and Discord Integration have no usable 1.21.1 NeoForge build), Simple Voice Chat, BlueMap | 2 (Discord done in Sprint 1) | — |
| Performance | Sodium, Lithium, FerriteCore, ModernFix, AllTheLeaks, Entity Culling, ImmediatelyFast, Dynamic FPS, spark, Neruina (crash guard), one block logger with rollback (CervLogger) | 0 | FerriteCore, ModernFix, Entity Culling |
| Visual (optional) | Iris + Complementary shaders, off by default | 3 | Shaders |
| Phase 3 options | Ice and Fire CE, Frontier Cohorts (armies) | 3 | Ice and Fire |
| Offline tools | MCA Selector (chunk pruning), Blockbench (item models), WorldPainter (not used: the lore map is canon worldgen, see section 6) | — | — |

Why not Mekanism: its developers flagged some 1.21.1 releases as alpha. Immersive Engineering has a stable release line on 1.21.1, is built around a few large multiblocks rather than many small machines, and its revolver and railgun arm the magitech soldier without a separate gun mod. Its last update is about a year old, which suits a frozen-version server: pin 12.4.2 and soak-test it on staging.

**Never add:** Epic Fight and Better Combat (break Tensura rendering and combat), Tensura: Predation (bypasses the skill registry), a second claims mod, a second nations mod, a second minimap.

## Game systems

Tensura's own mechanics (races, skills, EP, souls, naming, evolution) stay the source of truth; a thin KubeJS layer under the `ttl` namespace adds karma, skill ownership, reputation and politics on top.

### 1. Two lives

- **Life 1, the Mortal Realm:** datapack dimension `ttl:mortal_realm`, vanilla-like terrain, no Tensura mobs or items (filtered by KubeJS), everyone Human, Tensura skills toggled off. Hardcore: one death ends the life. *Status 18/11/2026:* Life 1 also has its own Nether and End (`ttl:mortal_nether`, `ttl:mortal_end`; portals and a separate dragon fight come from the `ttl-portals` Java mod, owner-approved). The Mortal Realm uses a vanilla multi-noise biome source with Tensura structures and features filtered out, and `life/confine.js` keeps Life 1 and Life 2 players in their own worlds. The item filter (`ttl:mortal_banned`) is still open on the roadmap. PvP is open (owner decision; the plan's Q12 recommended off): another player can end your only first life.
- **Death:** KubeJS restores health, cancels the death, runs the strip list, scores karma and sends the player to the Spirit Corridor. Fallback if cancel is unreliable: catch lethal damage in the hurt event instead. *Status 18/11/2026:* cancelling the death works as designed, the hurt-event fallback was not needed. Carry-over of the ender chest and Curios slots is an open item (`roadmap.md`).
- **Spirit Corridor:** void dimension `ttl:spirit_corridor` with a built hall. The "Voice of the World" NPC offers 2–3 races; the player picks with `/ttl choose`. *Status 18/11/2026:* the Voice of the World is a glowing allay that points to the current step. The flow is the Life screen (judgement), the **Last Wish** (ten wishes, each a pool of non-Legendary uniques), an optional **Trial of the Soul** (one arena per wish; win and pick 1 of 3 uniques, lose and fate draws), then the rebirth. Choices are on-screen menus (`/ttl menu`); `/ttl choose` stays as the command form.
- **Rebirth:** `/tensura edit` sets race and stats, the registry grants an innate unique, reputation is seeded, and the player lands in the lore region. *Status 18/11/2026:* the rebirth is the Great Sage reincarnation ceremony (`ttl-portals` opens Tensura's own menu with the player's offers and swallows Escape, so it cannot be declined by accident). The ceremony's own wishes (up to 3 skills) stay on top of the Last Wish unique; the registry reconcile records them or swaps an over-cap one for a free unique of the same rarity. The soul wakes in early Tempest at world 0, 0. Reputation is not seeded yet (factions are Sprint 4).
- **Life 2:** the Tensura overworld, normal survival with Tensura's own death rules and graves.
- **Gamerules:** `noUniqueStart true`, `trulyUnique false`; race lists set to Human only for first spawn. *Status 18/11/2026:* `trulyUnique` was planned on, but it removes every owned unique from the reincarnation pool; the registry caps (section 5) do that job, so it is off.

### 2. Karma

| Axis | Earned by | Pushes toward |
| --- | --- | --- |
| Valor | Hostile kills (by mob HP), Life 1 boss, blood moon survival | Ogre, Lizardman, martial uniques |
| Order | Trades, cured villagers, golems, defended villages | Human (Hero path), Elf |
| Chaos | Villager/golem kills, PvP kills, raids started | Orc, Daemon, sin skills |
| Craft | Create milestones, smithing, building quests | Dwarf, craft uniques |
| Faith | Enchanting, books, study quests | Elf, spirit-affine, sage-type uniques |
| Longevity | Days survived | Elf, Vampire |

Score per axis = 100 × ln(1 + raw / k); total = sum + 0.5 × the best axis. The log curve stops grinding one axis from winning; only distinct mob types and quests count.

*Status 18/11/2026:* built as designed in `server_scripts/ttl/karma/` with every number in `design/data/karma.toml`. Anti-farming went in on top: longevity counts active time only, kills diminish per kind of mob, exploration counts distinct squares on foot with a daily cap. Player kills feed Chaos (`player_kills`) and are possible in Life 1.

### 3. Rebirth tiers and choice

Every tier unlocks a range and the player chooses freely inside it; higher tiers add stronger starting races and better unique picks. Karma never locks a choice: the race matching the dominant karma axis gets an affinity bonus (a starting resistance skill or a soul relic).

| Tier (plan name) | Race range (cumulative) | Unique skill | How to get it (`karma.toml`) |
| --- | --- | --- | --- |
| Wanderer (Underdog) | Goblin, plus Slime (always offered); 2 offers | 1 random, leaning Common | Any score; the starting tier |
| Survivor (Normal) | + Human, Elf, Dwarf, Merfolk, Lizardman, Wight, Ghoul; 3 offers | 1 random | Score 100 and 2 days lived (about 40 minutes) |
| Hero (Elite) | + Ogre, Harpy, Beastfolk, Giant; 4 offers, 1 guaranteed from this tier | Pick 1 of 3, leaning Rare | Score 600 and 7 days |
| Legend (Legendary) | + Hobgoblin, Dragonewt, High Orc, Vampire, Lesser Daemon; 5 offers, 2 guaranteed from this tier | Pick 1 of 3 (never a Legendary unique yet) + 1 bonus Tensura skill; the Voice announces it | Score 1000, 30 days (about 10 hours) and at least one great foe slain |

Slime stays in every pool: it is the canon underdog with the highest ceiling. Unique picks are rolled with a karma bias (Craft rolls more craft uniques). Exact race IDs come from the jar dump; once 20+ players have reincarnated, thresholds switch to percentiles.

**Fallen (the dark path).** A soul is Fallen when its Chaos axis scores at least 60 and at least as much as Order (about 4 villagers or 2 players slain). It keeps its tier, shows "Fallen" before the title (a "Fallen Hero" is a Hero), and gets one guaranteed dark race offer: Orc (Wanderer), Ghoul or Wight (Survivor), High Orc or Lesser Daemon (Hero), Vampire (Legend). Dark races join the pool on top of the normal ones; nothing is taken away.

*Status 18/11/2026:* the four tiers are scored in `karma/karma.js`; the thresholds are absolute for now (the switch to percentiles waits for 20+ rebirths). The plan's Legendary-tier gate (Life 1 boss + trial + era slot, Legendary pick if a slot is free) is not built: Legendary uniques are never drawn at rebirth whatever the tier, and the Legend tier gets the bonus skill instead. The Legendary pick is Sprint 3.

### 4. Soul carryover

| Carries over | Does not |
| --- | --- |
| XP levels, advancements, FTB Quests progress | Inventory, armor, offhand, ender chest |
| Iron's learned spells | Life 1 Tensura skills (none should exist) |
| Karma, titles, reputation memory | Race and stats (reset by the new body) |
| Items tagged `ttl:soulbound` (one Soul Gem per player) | Coins and wallet |
| One "Remembered Enchantment" book per Craft tier | Bases and blocks in the Mortal Realm |

*Status 18/11/2026:* Karma, titles, XP and advancements carry over. The strip list so far clears inventory, armour and offhand; the ender chest and Curios/backpack slots, the Soul Gem and the Remembered Enchantment book are open (`roadmap.md`, `design/architecture/sprint3-4.md` S1).

### 5. Unique skill economy

| Rarity | Examples | Holders |
| --- | --- | --- |
| Legendary | Predator, Great Sage, the sin series, Creator | 3 on the server (was 1); never drawn at rebirth, granted on purpose |
| Rare | Most combat and magic uniques | 3 holders (the plan: 1 innate + 2 acquired copies) |
| Common | Utility uniques | 5 holders (the plan: 1 innate + 4 acquired copies) |

Ways to get one:

1. **Innate** at rebirth, from uniques with free slots.
2. **Absorption:** an absorbing-skill holder (Predator, Gluttony, Starved) kills a holder during a war or in a PvP zone, victim EP at least 50% of the killer's, 72-hour cooldown. Legendary is stolen; others are copied if slots are free.
3. **Apprenticeship** (copy, both consent, quest chain) or **succession ritual** (voluntary transfer, any tier).
4. **Skill Cores** from T3+ bosses, **Demon Lord / True Hero awakening**, and **Exalted faction reputation**.
5. **Return to pool** after 30 days inactive or a character reset.

Every transfer is logged and announced by the Voice of the World. A reconcile loop every 5 minutes (was 10; also on login and 100 ticks after a rebirth) reverts any skill change the registry didn't make.

*Status 18/11/2026:* the registry (`registry.js`, `manas.js`) counts holders against the caps in `design/data/skills.toml`; duplicates are allowed up to the cap. Built: innate unique at rebirth (never Legendary), `/ttl grant`, `/ttl registry`, the reconcile against ManasCore storage. Not built: absorption, apprenticeship, succession, return to pool, the veto hooks that stop plunder instantly instead of within 5 minutes.

### 6. Lore region and NPC factions

- **Map:** the canon Tensura continent, about 14,000 blocks wide (Jura Forest, Tempest, Dwargon, Blumund, Falmuth, the Holy Church, Orc lands, Lizardman marsh, Eurazania), ringed by open sea; ordinary terrain beyond for free building. Pre-generated, pre-mapped in BlueMap and FTB Chunks waypoints, plus an atlas item at rebirth. *Status 18/11/2026:* generated by worldgen instead of a WorldPainter paint: a grid made with `tools/canon_map.py` from a political map (`pack/config/ttl/canon_map.txt`, `canon_regions.json`) drives the `ttl:canon_map` density function (21 nations, rivers, lakes, a 1,600-block sea ring); world 0, 0 is Tempest. Edited as text, infinite. Built: Early Tempest, Dwargon, six canon landmarks from Tensura's own structures. Open: pregeneration (Chunky, owner's PC), BlueMap, the atlas.
- **NPCs:** canon characters as Easy NPC (Rimuru, Benimaru, Shion, Rigurd, Gobta, Milim, a sealed Veldora, Gazel's court, Hinata's office, Fuze, Falmuth's king). Tensura's own canon bosses stay encounters. The NEB Rimuru boss becomes a "Mimic Echo" in the story. *Status 18/11/2026:* only the Voice of the World exists as an NPC (an allay, not Easy NPC); the canon cast is still to build.
- **Outcast Society:** an original hidden faction of rejected reincarnators; its quest line is the pack's own story thread.
- **Reputation:** per faction, bands from Hostile to Exalted. It changes prices, quest access, guard hostility and war-ally offers. Karma and race seed starting values (Order → Blumund/Church, Chaos → Orc lands, Craft → Dwargon, Slime/Goblin → Tempest).
- **Armies:** Tensura's own subordinates and naming plus Easy NPC guards. Frontier Cohorts only re-evaluated in Phase 3.

### 7. Nations and politics

- **Warring Nations:** nations are FTB teams, territory is FTB Chunks claims, so Tensura Compat: FTB protections and team quest progress apply. Use a curated config preset and Lightman's Currency for the treasury.
- **KubeJS politics on top:** Walpurgis council (seats for true Demon Lords, seasonal votes), naming as vassalage, treaty log, titles. All Tensura politics live in KubeJS so the layer survives a Warring Nations removal.
- **Rules:** war windows at set times, offline raid protection, nation member cap, claim cost that scales with nation size.

### 8. Bosses

| Tier | Encounters | Unlocks |
| --- | --- | --- |
| T0 | Life 1 elites (L2 Hostility traits), the Mortal Realm finale: the Mortal End's dragon, "The Mortal Dragon" (the re-themed Ferrous Wroughtnaut "The Iron Tyrant" is postponed) | Legendary eligibility |
| T1 | Orc Lord, Supermassive Slime, Frostmaw, Born in Chaos bosses | Nation charter, Magisteel |
| T2 | Ifrit, Orc Disaster, Greater Spirits, NEB Rimuru "Mimic Echo", Cataclysm Ignis and Netherite Monstrosity | Adamantite, Demon Lord Seed |
| T3 | Charybdis, Gazel Dwargo, Hinata, NEB Carrion, Cataclysm Harbinger and Leviathan | Hihi'Irokane, awakenings, Skill Cores |
| T4 | NEB Luminous, Cataclysm Maledictus and Ender Guardian as Calamity-class, scheduled world bosses | Council seat, server titles |

Imported bosses get KubeJS scaling (HP × tier multiplier × player count), lore names and boss bars, scripted phases (enrage, minions, magicule drain, elemental resistances), LootJS loot with Tensura materials, and on-kill souls, coins, reputation and quest stages. Bosses are summoned by quests or scheduled events, not natural spawns.

*Status 18/11/2026:* the boss framework is Sprint 4. The Mortal Dragon is Life 1's finale (its fight is saved per dimension by `ttl-portals`; the `dragon` quest in chapter 0). The Iron Tyrant stays on the Sprint 3 list as an optional mid-boss. Capture: the plan says bosses are gated, but `compat/tombstone_bosses.js` first let every Tensura/NEB boss be bound as a Tombstone familiar (issue #3). It is now a knob in `design/data/bosses.toml`: by default only a player who has slain that boss can bind it (`defeated` mode, read from their kill statistics); `allow_list`, `any` and `none` are the alternatives.

### 9. Economy and events

- **Currency:** Lightman's Currency coins, player shops, Create shops and Shoppers NPC customers.
- **Faucets:** bounties, boss kills, faction quests, NPC trades. **Sinks:** nation founding and upkeep, war declarations, claims, rituals, Skill Core identification, repairs, luxuries. Target: sinks at least 80% of faucets per active player per week.
- **Events:** Enhanced Celestials blood and harvest moons, scheduled world bosses, monthly Walpurgis, seasonal resets of Legendary slots.

**Adventurer's Guild:** Fuze's Free Guild in Blumund runs the daily loop: 3 daily and 2 weekly bounties rotated by KubeJS, guild ranks F to S, paid in coins and reputation. It is the main coin faucet and replaces the plain bounty chapter.

**Tensura's own venues**

- **Labyrinth:** arena and raid venue. With the `labyrinthDeath` gamerule off, players drop to 1 HP and get teleported out, so duels and events cost nothing. Hosts the duel ladder and staged Legendary duels.
- **Hell:** a weekly Underworld Expedition.
- **Naming:** a ritual with a Voice announcement and karma; named subordinates are capped per player to keep entity counts low.
- **No MineColonies:** too heavy for the server; Easy NPC and named subordinates carry the population.

**Catch-up:** Reincarnation Grace gives new Life 2 players ×1.5 EP and XP for 14 days, on top of World's Favor.

### 10. Tech and magic, tied to lore

In the series, Dwargon and early Tempest run on dwarven engineering, Tempest later builds magic-science, and the Eastern Empire is the most advanced, with magic-powered weapons and machines. The tech tree follows that order, so higher tech fits the lore as long as it is gated.

| Tech tier | Mods | Lore home | Gate |
| --- | --- | --- | --- |
| Industry | Create + addons | Dwargon, Tempest workshops | Life 2 start |
| Magic-science | Create: New Age (electricity, generators, reactor), Create: Occult Engineering | Tempest research labs | Dwargon Friendly + T1 boss |
| Magitech | Immersive Engineering (multiblocks, revolver, railgun, chemthrower) | Eastern Empire | T3 boss + Eastern Empire reputation |

| Magic system | Mana | Lore home | Gate |
| --- | --- | --- | --- |
| Tensura native (elemental, spirit, holy) | Magicules | Everyone; spirits through the Spirit Tree | Race and skills |
| Iron's Spells | Magicules (via compat) | Guild and academy magic | Life 2 |
| Occultism | Rituals and spirits, no separate pool | Summoning and demon contracts | Faith karma or Daemon races + its chapter |
| Ars Nouveau | Its own Source | Elven glyph magic | Later era; then Elf race chapter or Elite tier |

Rule: no more than these four magic systems; each gets a faction home, a quest chapter and damage tuned against Tensura in playtests.

**Magitech soldier path (confirmed).** An Eastern Empire-style soldier class open to any race, with its own 30-quest chapter, "Magic Armored Corps". The Eastern Empire joins the lore region as a faction.

| Rank | Gear and abilities | Gate |
| --- | --- | --- |
| Recruit | IE revolver, steel armor, Tensura martial Arts (battlewill) | Eastern Empire Friendly |
| Soldier | Revolver upgrades, chemthrower, Iron's battle-mage spells | T2 boss + Honored |
| Magic Armored Corps | Railgun, custom KubeJS Magitech Armor set (set bonus turns magicules into a damage shield) | T3 boss + Exalted |

The Magitech Armor is a custom item set; its exact numbers come from balance testing.

### 11. Custom items, relics and loot

- **Custom items:** KubeJS startup scripts register the Soul Gem, Skill Cores, faction tokens, boss trophies and relics; models and textures live in `kubejs/assets/ttl`. Claude Code makes placeholder art; final art in Blockbench by a human.
- **Relics:** KubeJS items worn in Curios slots (through Curios item tags), with attribute modifiers and scripted abilities on cooldowns. The Relics mod's own relics stay as found loot; adding new relics to that mod needs Java.
- **Loot tables:** LootJS edits chest, mob, boss and structure loot: Tensura materials into Towns and Towers and Cataclysm structures, relics as rare drops, junk trimmed.

| Relic | Slot | Effect (numbers set in testing) | Source |
| --- | --- | --- | --- |
| Anti-Magic Mask | Head charm | Less magic damage taken; hides your race from scans | Shizu questline |
| Storm Dragon Scale | Charm | Lightning resistance, small magicule regen | Sealed-dragon cave event |
| Charybdis Scale Mantle | Back | Water breathing; damage reflect at low HP | Charybdis (T3) |
| Dwarven Masterwork Ring | Ring | Faster smithing and Create work | Dwargon Exalted |
| Luminus Rosary | Necklace | Holy damage up; undead deal less | Holy Church Honored |
| Hunger Fang | Charm | Lifesteal, Chaos-aligned players only | Orc Disaster |
| Outcast Sigil | Charm, soulbound | Survives reincarnation; opens the Outcast Society thread | Hidden Life 1 quest |

### 12. Voice of the World events

The Voice of the World is the server's narrator: a KubeJS event director that schedules and announces world events in game (title, sound, chat) and on Discord.

| Event | Trigger | Effect |
| --- | --- | --- |
| Calamity Rising | Scheduled, weekly | A T3/T4 boss spawns at an announced spot; server-wide raid |
| Blood Moon | Enhanced Celestials | Mortal Realm danger up with a Valor bonus; Life 2 mob surge |
| Harvest Festival | A player awakens as Demon Lord | Server-wide announcement, title, council seat opens |
| Hero Ascension | True Hero awakening | Church reputation boost for the hero's allies |
| Walpurgis | Monthly | Council meeting, votes, treaty ceremony |
| A Name Is Given | A player names a subordinate or vassal | Announcement, nation prestige |
| Skill Transfer | Absorption, succession, return to pool | "Unique skill X has changed hands" |
| Otherworlder Arrives | An Elite or Legendary rebirth | Lore line naming tier and race (unique hidden) |
| Dragon Stirs | Yearly era storyline | Sealed-dragon cave event, lore unlock |
| Era Turns | Yearly | Era recap, new Legendary slots, new story chapter |

Players can mute chat-only announcements; titles stay for major events.

**World's Favor: lifting the weak**

Once a week the Voice of the World picks one struggling but active player and grants a blessing: the World recognising a soul that endures.

- **Eligible:** bottom 25% of EP among players with at least 5 hours played that week, not blessed in the last 30 days, Discord-linked account.
- **Blessing, player picks one of three:** an EP surge toward the next evolution; a Common unique pick if a slot is free; a resistance skill; 3 days of Protection (damage resistance, no absorption against them); a relic.
- **Announcement:** "The World has taken notice of \[player\]."
- **Anti-abuse:** the playtime floor and Discord linking stop alts and idlers; players whose EP dropped sharply that week are skipped, so nobody sandbags on purpose.

**More events**

| Event | Trigger | Effect |
| --- | --- | --- |
| Requirements Met | A skill, evolution or title milestone | Personal Voice line in Great Sage style; major milestones go server-wide |
| Magicule Storm | Random, 1–2 a week, 1 hour, one region | Double magicule regen and EP gain, stronger mobs |
| Spirit Tree Blooms | Monthly | Spirit contracts easier, spirit magic boosted for a day |
| Labyrinth Opens | Every 2 weeks | Time-limited labyrinth run with a leaderboard and rewards |
| Nation Recognised | A nation hits size, merit and stability thresholds | "Recognised by the World": title, claim bonus, Discord post |
| Divine Protection | Weekly, nation with the most merit | Blessing on that nation: faster building, lower upkeep |
| Market Boom / Crash | Economy director, from mint/burn data | Prices shift for a few days |
| Sealed Calamity | Era storyline | The server cooperates to reseal a calamity; failure brings a harder boss |
| Underdog Rises | An Underdog-tier player evolves | Server-wide announcement and a small bonus |
| Master Builder Named | A player reaches a builder rank | Announcement, Discord role, title |

### 13. Merit: rewards for builders

Building for others is one of the strongest paths to standing on the server, like Geld's construction corps building roads across the Jura Forest; public works pay three times as much as private ones.

**Earning merit**

| Source | Merit | Rule |
| --- | --- | --- |
| Private or nation-only works | ×1 | Blocks tagged `ttl:infrastructure` in a Public Works Charter area, standing 7+ days |
| Public-use designation | ×3 | Area dedicated to the Commons: anyone may walk, ride and use doors, rails and crafting stations; the builder keeps edit rights; must stay public 30+ days or the bonus is clawed back |
| Usage | Merit per unique visitor per day | Players outside the builder's nation using the work (roads, stations, inns, smithies), capped daily |
| Big works | Large one-off award | A rail line or road connecting two capitals, confirmed by both leaders or a Discord vote |
| Likes | Counted toward ranks | One like per player per work, only after visiting it; at least half from other nations |

**Builder ranks: Geld's Corps**

| Rank | Needs (starting values) | Rewards |
| --- | --- | --- |
| Apprentice Builder | 3 public works, 500 merit | Title, Discord role, free charters |
| Builder | 8 public works, 2,000 merit, 15 likes | +1 block reach, cheaper claims |
| Master Builder | 20 public works, 6,000 merit, 50 likes from 20+ players | "Master Builder" skill: +2 block reach, faster block breaking, Voice of the World announcement |
| Grand Architect | The top Master Builder of each era | A craft-type unique roll through the registry (if a slot is free), an era monument |

- **Master Builder skill:** a KubeJS perk using the 1.21 player attributes for reach and block-breaking speed; if a fitting Tensura skill exists in the jar dump, grant that instead.
- **Commons land:** a server-owned FTB team; `/ttl publicworks dedicate` moves a charter area's chunks to it with the builder kept as editor (check FTB Chunks per-team permissions in Phase 2).
- **Life 1:** the same scanner gives Order and Craft karma for village infrastructure, doubled for works villagers and other players can use.
- **Also pays:** home-faction and neighbour reputation, nation prosperity (higher claim cap, lower upkeep) and soul karma toward a future reincarnation.
- **Anti-abuse:** no credit for moved or rebuilt blocks; visits and likes only from distinct Discord-linked accounts; staff can void a charter.

**Master Builder perk: Builder's Economy**

Master Builders sometimes place a regular building block without using it up, and the more distinct players like their builds, the better the odds. Lore: Geld's corps never wasted a stone; the Voice announces "Extra Skill \[Builder's Economy\] acquired."

| Rank | Starting chance | Cap | Daily refund cap |
| --- | --- | --- | --- |
| Master Builder | 8% | 35% | 256 blocks |
| Grand Architect | 15% | 45% | 512 blocks |

Chance = base + 0.05 × ln(1 + weighted likers), capped. Each liker counts once: 1 for other nations, 0.5 for your own; likes fade with a 1-year half-life.

- **Which blocks:** tag `ttl:builder_refundable`: polished, brick and tile stone families, bricks, planks, stripped logs, glass, terracotta, concrete, wool and Create decorative stone, with their slabs, stairs and walls. Never cobblestone, gravel, sand, dirt or logs with bark (processing inputs), ores, metal and storage blocks, block entities, gravity blocks, Tensura or magic-mod blocks, or Create casings. A startup check fails the build if any tagged block can be processed into something worth more.
- **Where:** only inside a Public Works Charter or your own claim.
- **Anti-dupe:** a refunded block broken within 72 hours drops nothing; no roll when re-placing the same spot within 10 minutes; no refunds within 16 blocks of Create kinetic blocks; creative mode, Create deployers and other automated placers never count.
- **How:** KubeJS `BlockEvents.placed` with the refund one tick later, because NeoForge overwrites the held stack after the event. Refunds are logged, and the Discord bot flags unusual refund rates.

### 14. Eras: a world that lasts

Seasons become yearly eras: the world is never wiped and mod versions stay frozen for the server's life; new content arrives through KubeJS, datapacks and quests.

| Resets each era | Persists forever |
| --- | --- |
| Legendary rebirth slots | The world, bases and nations |
| Era titles and leaderboards | Races, skills, EP, owned uniques |
| Walpurgis council re-election | Reputation, merit, karma history |
| Era storyline chapter | Quest progress |

- **Version lock:** jars frozen at launch; only save-compatible bugfix updates after a staging test on a copy of the live world. Tensura feature updates are skipped unless proven safe.
- **World health:** the world border grows each era as "newly discovered lands"; unclaimed, unvisited chunks outside the lore region are pruned offline with MCA Selector; claims of players inactive 90 days expire.
- **Joining in year 2+:** catch-up quests, newbie protection and the Underdog path keep the world joinable.

## How the systems connect

Two hubs carry the design: the rebirth, which turns Life 1 karma into a race, a unique, reputation and quest stages, and the skill registry, which every unique-skill change in Life 2 must pass through.

&#91;embedded content: system interactions · 12 systems, 2 hubs\]

Arrows show data flowing; every registry change also triggers a Voice of the World announcement in game and on Discord.

**Shared data (namespace `ttl`)**

| Where | Keys | Holds |
| --- | --- | --- |
| Player persistentData | `ttl.life`, `ttl.l1.start`, `ttl.l1.days` | Which life, Life 1 timing |
| Player persistentData | `ttl.karma.{valor,order,chaos,craft,faith,longevity}`, `ttl.karma.score`, `ttl.tier` | Raw karma, score, rebirth tier |
| Player persistentData | `ttl.offers`, `ttl.trial.passed` | Race offers (blocks forged `/ttl choose`), trial result |
| Player persistentData | `ttl.uniques`, `ttl.cd.absorb`, `ttl.lastSeen`, `ttl.titles` | Owned uniques mirror, absorption cooldown, last login, titles |
| Server persistentData | `ttl.reg.skills.<id>`, `ttl.reg.legendarySlots` | Holders, rarity and history per unique; slots used this season |
| Server persistentData | `ttl.season`, `ttl.reincarnations`, `ttl.wars.active`, `ttl.council` | Season, rebirth history for percentiles, war mirror, council seats |
| Scoreboards | `ttl.k.*`, `ttl.karma`, `ttl.rep.<faction>`, `ttl.pick`, `ttl.bounty` | Display and Easy NPC conditions |
| Stages | `ttl.life1/2`, `ttl.tier.*`, `ttl.race.*`, `ttl.nation.*`, `ttl.dl.*`, `ttl.hero.true`, `ttl.council`, `ttl.boss.t1–t4`, `ttl.faction.<f>.<band>` | Quest gating |
| Item tags | `ttl:soulbound`, `ttl:skill_core`, `ttl:mortal_banned` | Survives rebirth, Skill Cores, banned in Life 1 |

*Status 18/11/2026:* the schema in force is the table in `CLAUDE.md` (it adds `ttl.step`, `ttl.wish`, `ttl.race`, `ttl.uniqueOptions` and `ttl.trial.done`). Keep that one current; this table is the original.

## Quest structure

About 560 quests in 19 chapters, written as TOML (`design/quests/*.toml`) and generated into FTB Quests (`tools/gen_quests.py`). Chapters unlock by stage, so each player sees only what fits their life, race, faction standing and tier. *Status 18/11/2026:* chapters 0 "A Mortal Life" and 1 "Reborn" are built (`design/quests.md`); the rest is Sprint 3.

| Chapter | Purpose | Quests | Unlocks when | Key rewards |
| --- | --- | --- | --- | --- |
| 0. Mortal Life | Teach survival, award karma, lead to the Life 1 boss | 60 | Life 1 | Karma, XP, titles |
| 1. The Reincarnation | Corridor, offers, trial | 15 | Life 2 | Atlas, starter kit, reputation seed |
| 2–7. Race families | Evolution paths per race family (Human, Slime, Goblin/Ogre, Orc, Lizardman, Daemon/Spirit/Vampire/Dwarf/Elf) | 120 | Race stage | Tensura race and EP rewards, evolution items |
| 8. Founding a Nation | Team, claims, naming subordinates, building a town | 40 | Life 2 | Coins, banners, claim bonus |
| 9. Diplomacy and War | Alliances, treaties, wars, council | 30 | Nation founder | Titles, souls, reputation |
| 10–13. Boss tiers T1–T4 | Progression gates | 60 | Previous tier | Souls, materials, Skill Cores (T3+) |
| 14. Dwarven Engineering | Create pillar | 60 | Dwargon Friendly | Coins, Create parts |
| 15. Arcane Studies | Iron's Spells pillar | 50 | Life 2 | Scrolls, inks |
| 16. Spinoff storyline | Canon faction arcs plus the Outcast Society thread | 80 | Faction reputation | Story items, apprenticeship unlocks |
| 17. Demon Lord / True Hero | Capstones | 20 | Demon Lord Seed or Hero Egg | Awakening, council seat, unique upgrade roll |
| 18. Bounties | Repeatable daily loop, main coin faucet | 25 | Always | Coins, reputation |

**Workflow:** design one chapter in TOML (key, title, deps, tasks, rewards), run `python tools/gen_quests.py` to make SNBT with stable IDs, validate, reload in game, spot-check. Check the generated layout against one quest made by hand in game before generating at scale.

## Server operations, balance and anti-abuse

A live server needs backups, staging and abuse rules from day one, because Life 1 deaths and stolen Legendary skills cannot be undone casually.

**Operations**

- **Hosting:** the homelab K3s cluster, node3 (side tier): a pod with 2 guaranteed CPUs and a 10 GiB limit, 7 GB heap, Java 21, Generational ZGC. View distance 16, simulation 8, with Distant Horizons drawing further. *Status 18/11/2026:* the plan asked for a rented high single-core host with a 16 GB plan, -Xmx12G and view distance 8-10 / simulation 6-8 (decisions Q1); revisit before the full ~200-mod pack or more than 10 players, and load-test (MSPT under 40 with 10 players).
- **Backups:** automatic and off-site, with a tested restore; separate snapshots of the skill registry and karma data. *Status 18/11/2026:* Longhorn snapshots every night and NAS backups every day, with the newest checked by ttl-ops (`docs/server.md`); the off-site copy and the restore drill are open.
- **Staging server:** every Tensura update runs there first, with an ID diff via `/dump-ids`.
- **Stability:** daily scheduled restart, auto-restart on crash, crash alerts, spark on standby, world border, pregenerated world.
- **Permissions:** LuckPerms roles (admin, moderator, builder, player); every admin `/tensura edit` and `/ttl` command is logged.
- **Grief and dupes:** a block-logging/rollback mod (verify a NeoForge 1.21.1 option); watch known Create/Tensura dupes.
- **Community:** Discord bridge with the Voice of the World feed, a rules page, one-click install via Prism or CurseForge.

**Player lifecycle**

- **Late joiners:** catch-up quest line, newbie PvP protection, cheaper claims for small nations.
- **Friends in Life 1:** dead friends reincarnate in the same region; consider a group trial.
- **Offline players:** war windows, offline raid protection, nation inheritance when a leader quits.
- **Alts and combat logging:** one account per person; logging out in combat counts as a kill for absorption.

**Balance rules**

| Risk | Rule |
| --- | --- |
| Snowballing Demon Lords | Hero counterplay, bounties on the top 3, diminishing EP gain at the top, Legendary titles defended through absorption |
| EP, soul and karma farms | Daily caps per entity type, no souls from spawner mobs, only distinct mob types count for karma |
| Create skipping tiers | Key Tensura material recipes locked behind boss stages |
| Double magic (Iron's + Tensura) | Tune the compat multipliers in playtests |
| Group boss loot | Per-player loot with a contribution threshold |
| Zerg nations | Member cap per nation, claim cost scales with size |
| Inflation | Weekly mint/burn report, adjust sinks |
| Race offers feeling unfair | Underdog races get extra growth quests |

**Rules and legal:** written server rules (PvP, roleplay with canon NPCs, absorption etiquette, alts). Minecraft EULA: donations buy cosmetics only, never races, skills or Legendary slots.

**Discord integration**

- **Chat and verification:** Simple Discord Link (`sdlink`), server side: two-way chat, join/leave/death messages and Discord account linking (`/discordverify`, `/verify`); linking enforces one account per person. *Status 18/11/2026:* linking replaced the manual whitelist; `access.js` admits only whitelist-file players and ops while the bot is offline.
- **Custom bot, built by Claude Code:** KubeJS writes game state to JSON (leaderboards, nations, wars, Demon Lords, events); the bot posts it and sends RCON commands back. *Status 18/11/2026:* there is no sidecar bot. The scripts post through sdlink (`ttl/discord.js`) and sync roles through its JDA (`ttl/discord/`); see `docs/server.md` "Discord bot".
- **Channels:** #voice-of-the-world, #wars-and-treaties, #leaderboards (weekly), and a private channel per nation, created automatically.
- **Roles:** race, nation and title roles synced from the game.
- **Commands:** /status, /whois, /nation, /events; staff commands for backups, restarts and event triggers.

**Automation**

| Area | Automated |
| --- | --- |
| Builds | GitHub Actions validate every commit; tagged releases publish the packwiz pack |
| Server | Nightly off-site backups with a weekly restore test, daily restart, crash alerts to Discord, packwiz update on restart |
| Gameplay | Event director, bounty rotation, world-boss schedule, inactive-holder skill returns, claim expiry |
| Economy | Weekly mint/burn report; NPC prices move within a band when inflation drifts |
| Balance | Weekly staff report: EP growth, boss kill times, deaths per tier |
| Moderation | Alerts on combat logs, suspicious skill transfers, dupes and admin commands |

**Stability and safety tooling**

- **Neruina** stops one broken ticking entity from crashing the whole server.
- **Block logger with rollback:** CervLogger (fallback CoreProtectNeo or modlog). Test rollback against Create contraptions first, since blocks moving inside contraptions are not logged.
- **Backups:** off-server incremental backups (restic or borg) with `save-off` and `save-all flush` over RCON, plus a monthly restore drill on the test server. *Status 18/11/2026:* not done; the Longhorn route above replaced it for now. A restic CronJob needs a backup target.
- **Monitoring:** spark for profiling; TPS and player metrics over RCON into Prometheus, alerts to Discord. *Status 18/11/2026:* ttl-ops sends TPS, crash, server down/up, backup-age and deploy alerts to Discord; there is no Prometheus.
- **Pinning:** Tensura and its addons frozen on one build after a 2-week soak on staging.
- **No client anti-cheat:** Tensura movement skills would cause false positives. Instead: KubeJS sanity checks (speed, reach, flight against race), the block logger and staff review.
- **Client defaults:** a shipped `options.txt` with render distance 8–10, Sodium defaults and pre-resolved keybinds for Tensura skills, the Iron's spell wheel and voice chat.
- **GDPR (EU-hosted):** a privacy notice, legitimate interest as the basis for logs and anti-cheat, block logs purged after 180 days, export or delete on request for linked Discord IDs. *Status 18/11/2026:* the notice is the guide page "Privacy: what we keep" (`design/data/guide.toml`); what is stored, where and for how long, and how to ask for removal, is in `docs/server.md` "Data we keep". `/bug` reports (`ttl-reports/`) and the CervLogger activity log are purged after 180 days with the shell snippet there; scheduling it is the open step.
- **Monetization within Minecraft's rules:** cosmetics except capes; donation goals unlock server-wide boosts only, never personal power.

## Claude Code build plan

Build the pack as code: Claude Code edits a git repo, runs a headless test server, reloads scripts over RCON and reads the logs; you play-test and build in game.

### Repo layout

```
ocs-two-lives/
├─ CLAUDE.md                 # rules Claude Code follows
├─ .claude/                  # settings.json (hooks), commands/, agents/
├─ pack/                     # packwiz root: pack.toml, index.toml, mods/*.pw.toml
│  ├─ config/  defaultconfigs/
│  ├─ kubejs/
│  │  ├─ startup_scripts/ttl/   # Soul Gem, Skill Cores, custom items
│  │  ├─ server_scripts/ttl/    # life/ karma/ registry.js absorb/ politics/ bosses/ economy/ announce.js commands.js
│  │  ├─ client_scripts/ttl/
│  │  ├─ data/ttl/              # dimensions, loot, tags, structures
│  │  └─ assets/ttl/            # lang, textures
│  └─ config/ftbquests/quests/  # GENERATED, never hand-edited
├─ design/                   # quests/*.toml, data/*.toml (karma, skills, trials, guide, bosses), decisions.md, roadmap.md, dumps/
├─ tools/                    # server.sh, rcon.py, gen_quests.py, validators, logscan.py
├─ server/                   # gitignored test server
└─ tests/ingame/             # RCON test scripts + expected output
```

### CLAUDE.md contents

1. Pitch and pinned versions table (MC, NeoForge, KubeJS, Tensura, FTB, Warring Nations).
2. Golden rules: every unique-skill change goes through `ttl/registry.js`; namespace `ttl`; never edit generated SNBT or `*.pw.toml` by hand; never invent mod, race or skill IDs, look them up in `design/dumps/`; no Java without asking.
3. The data schema (next section).
4. KubeJS 1.21 conventions: `persistentData` get/put methods, `server.runCommandSilent`, `scheduleInTicks`, `Java.loadClass` wrapped in try/catch, one feature per file.
5. Testing protocol: reload via RCON, scan logs, run the matching `tests/ingame` script.
6. Done = validation passes, no new `ttl` errors, acceptance test passes, `decisions.md` updated.

### Tooling

- **Hooks:** after every edit, validate by file type (JS syntax, JSON, SNBT); block hand edits to `*.pw.toml` and deleting the test world.
- **Slash commands:** `/validate`, `/reload-test <test>`, `/gen-quests`, `/add-mod <slug>`, `/dump-ids`, `/crash`.
- **Subagents:** `quest-writer`, `kubejs-reviewer`, `balance-analyst`, `log-triage`.

### Phases

*Status 18/11/2026:* the work is run as four **Sprints** (`roadmap.md`) instead of these phases: Sprint 1 the friend playtest (Phase 0 and most of Phase 1: karma, tiers, registry, Corridor, backups, Discord), Sprint 2 building and visuals (blueprints, canon worldgen), Sprint 3 content (Life 1/2 quests, soul carryover, Legendary pick), Sprint 4 politics, bosses and economy (Phase 2). The tables below are kept for the intent and the exit criteria.

| Phase | Weeks | Claude Code builds | Done when |
| --- | --- | --- | --- |
| 0. Prototype | 1–2 | packwiz repo with Tensura, KubeJS, FTB suite, Easy NPC; server and RCON tools; ID dump; SkillAPI probe; Life 1 death cancel; both dimensions; `/ttl choose` stub; revoke and plunder tests | Death by zombie, lava, fall and void in the Mortal Realm lands you in the Corridor with XP and advancements, empty inventory, no EP penalty; rebirth gives the right race and one unique |
| 1. MVP | 3–5 | Karma engine, tiers, Corridor offers, Voice NPC, skill registry v1 + reconcile, soul carryover, Mortal Realm filters, quest generator, chapters 0–1, performance mods, backups and staging | 5 testers complete Life 1 → Life 2; caps refuse an extra Legendary; MSPT under 40 with 10 players |
| 2. Politics and bosses | 4–6 | Warring Nations + config, KubeJS politics, absorption with all rules, boss framework (scaling, phases, loot, souls), reputation + first 3 factions' NPCs, Discord bridge, voice chat, farm caps | 8-case absorption matrix passes; T1–T3 bosses scale correctly; war and peace work with claim protection intact |
| 3. Full pack | 6–10 | All factions and the spinoff story, all chapters to \~560 quests, Create and Iron's chapters, bounties, events, extra boss mods, BlueMap markers, balance pass, onboarding docs | One in-game week with 3–5 testers; 24-hour crash-free soak |
| 4. Live ops | ongoing | Season tooling, weekly economy report, registry audit, hotfix workflow | Season reset runs cleanly on staging first |

### First prompt for Claude Code

> Read CLAUDE.md. Initialise a packwiz pack for Minecraft 1.21.1 NeoForge with KubeJS, LootJS, the FTB suite with XMod Compat, Tensura: Reincarnated and its dependencies, Tensura Compat: FTB, TensuraMoreConfig and Easy NPC. Write tools/server.sh and tools/rcon.py, start the server, confirm a clean boot and RCON `list`, then dump every `tensura:` race, skill, entity and item ID to design/dumps/.

### Only you can do

- WorldPainter map and merging it into the world (no longer needed: the map is canon worldgen).
- Building capitals, the Spirit Corridor and Mortal Realm landmarks.
- Easy NPC skins and the tone of canon dialogue.
- Real-player death and PvP tests, and balance feel.
- Manual downloads for mods that block third-party distribution, and hosting.

## Risks and open questions

Three things must be proven in Phase 0 before anything else is built; if one fails, the fallback is listed.

| Risk | Why it matters | Fallback |
| --- | --- | --- |
| Cancelling a player's death is unreliable (other mods' death handlers, `/kill`, void, totems) | The whole two-life loop depends on it | Catch lethal damage in the hurt event; disable graves in the Mortal Realm |
| KubeJS can't read Tensura skills through ManasCore's SkillAPI | The registry reconcile needs to see real skills | Parse `/tensura get ability list` output; worst case a \~100-line Java bridge mod |
| Tensura's native plunder bypasses the registry | Legendary uniques could leak | Tensura reportedly can't steal uniques except Starved; verify, keep Tensura: Predation out |
| Tensura updates rename IDs | Scripts and configs break | Pin versions, diff `/dump-ids` on every update |
| Warring Nations is young and pins FTB versions | Blocks FTB updates, possible bugs | Pin, keep all Tensura politics in KubeJS, fallback to FTB + KubeJS |
| Tensura power makes imported bosses trivial | Boss ladder collapses | Tier multipliers tuned with real playtest data |
| Claude Code invents IDs or APIs | Silent bugs | ID dumps, validation hooks, "never invent IDs" rule |

*Status 18/11/2026:* the three Phase 0 risks were proven in practice. Death cancel works; ManasCore's SkillAPI is readable from KubeJS (the `manas.js` bridge, no Java bridge was needed); plunder bypassing the registry is only caught by the 5-minute reconcile until the veto hooks land (`roadmap.md`).

| New risk | Why it matters | Fallback |
| --- | --- | --- |
| Frozen versions keep known bugs | No fix through updates during an era | Config and KubeJS workarounds; save-compatible bugfix jars only after staging |
| Immersive Engineering not updated for about a year | Its bugs stay unfixed | Fits a frozen-version server; pin 12.4.2, soak test on staging, KubeJS workarounds |
| Four magic systems unbalance PvP | One system dominates | Damage tuning per system, staged rollout (Ars Nouveau last) |
| Merit scanner farmed | Free reputation | 7-day survival rule, daily caps, staff voiding |

**Launch scope: what ships when**

The design has about a dozen custom systems; launching all of them at once risks stability, so they arrive in waves.

| At launch (v1) | Phase 2 | Later eras |
| --- | --- | --- |
| Two lives, karma, rebirth tiers and choice, soul carryover | Absorption on war/PvP kills (v1 uses staged Legendary duels in the Labyrinth) | Ars Nouveau |
| Unique-skill registry and reconcile loop | Magitech soldier class and armor | Eastern Empire invasion event |
| Nations, claims, economy, Adventurer's Guild | Remaining Voice of the World events | Walpurgis votes, era titles, Legendary slot resets (first anniversary) |
| Merit, builder ranks, Builder's Economy | Duel ladder, train tolls, wanted levels | Ice and Fire CE, if the performance budget allows |
| 4 Voice events: World's Favor, Magicule Storm, Harvest Festival, Labyrinth Opens | Remaining factions and story chapters, Discord bot features | Up to \~590 quests |
| \~150 polished quests, \~180 mods, stability tooling, Discord bridge | Up to \~400 quests | — |

Life 1 targets 2–6 hours of content in a small, pregenerated Mortal Realm.

Version numbers and several mechanics come from community wikis and listings as of late 2026; Tensura is closed source, so every command and ID is re-checked against the pinned jar.

**Questions to answer before building**

Everything else is decided. Each question has my recommendation; answer only the ones you want to change and the rest go ahead as recommended.

| # | Question | My recommendation | Your answer |
| --- | --- | --- | --- |
| 1 | Hosting: your own hardware or a rented host? CPU and RAM? | Rented, high single-core CPU, 16 GB RAM, NVMe | Own hardware: homelab K3s node3 (decisions Q1, 16/11/2026) |
| 2 | Launch target and player count (launch, after a year)? | Soft launch after Phase 1 with 10–15 testers |  |
| 3 | Who builds the lore region and capitals? Is Belgiancandy267 in? | Belgiancandy267 on WorldPainter, 1–2 extra builders |  |
| 4 | Staff: how many admins and moderators? Monitoring in Grafana or only Discord alerts? | 1 admin + 2 moderators, Discord alerts only |  |
| 5 | Discord: your existing server or a new one for the pack? | A new server just for the pack |  |
| 6 | Access: public, whitelist, or invite-only? | Whitelist through Discord linking | Discord account linking (18/11/2026) |
| 7 | Donations: cosmetics only, or also server-wide goal boosts? | Both, within Minecraft's rules |  |
| 8 | Which Tensura build to pin? | Newest 2.0.1.x after a 2-week soak, unless an addon needs older | 2.0.1.5 (D1) |
| 9 | Tensura: Ascension (3× EP chamber)? | Not at launch; maybe later behind an era quest |  |
| 10 | Extra race addons? | TR Addon (Slime line) + Unique Races at launch; Mysticism later |  |
| 11 | Life 1: Legendary needs how many in-game days? | 15 days (about 5 hours), to fit 2–6 hours of Life 1 | 30 days (about 10 hours) for the Legend tier (`karma.toml`) |
| 12 | PvP in the Mortal Realm? | Off | Open (owner decision, 18/11/2026) |
| 13 | Iron's Spells in Life 1? | Off |  |
| 14 | Life 2 death: graves or keepInventory? | Graves | Graves (Tombstone; off in the Mortal dimensions and the Corridor) |
| 15 | Can Life 2 players revisit the Mortal Realm? | No, except one quest to visit your own Life 1 grave |  |
| 16 | Skill absorption: staged duels only at launch, full war/PvP absorption in Phase 2 (72 h cooldown, victim ≥ 50% of killer EP)? | Yes |  |
| 17 | World's Favor: one per week, or one per 10 active players? | One per 10 active players per week |  |
| 18 | Builder rank thresholds and the ×3 public bonus OK as starting values? | Yes |  |
| 19 | Grand Architect: one per era server-wide, or one per nation? | Server-wide |  |
| 20 | Can Life 1 players give likes? | No, Life 2 only |  |
| 21 | Create kinetic blocks in Public Works Charters? | Allowed for merit; no Builder's Economy refunds within 16 blocks |  |
| 22 | Lore region size and launch nations? | About 6k × 6k blocks: Tempest, Dwargon, Blumund, Falmuth, Holy Church, Eastern Empire | The canon continent, about 14,000 blocks wide, 21 nations |
| 23 | Era length? | One year from launch; era features start at the first anniversary |  |
| 24 | Who makes textures for custom items and relics? | Claude Code placeholders, final art by you or a commissioned artist |  |
| 25 | Pack name and branding? | OCS Tensura: Two Lives, v3.0 on the existing OCS CurseForge page |  |
