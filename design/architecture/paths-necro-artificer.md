# Standalone paths: Necromancer, Artificer, and the moral-choice world events

18/11/2026 · design only, for the implementation agents. Builds on `world-state.md` (rev. 2: continent rule §2.0, chronicle §3,
PvP scope §6.2, armies and wars §6.5, domains §6.6, radiant quests §6.8, instancing §7), `sprint3-4.md` §0 conventions,
`story-characters.md` R1–R4, the registry (`registry.js`), reputation (`rep/`), nations (`nations/`), bosses (`bosses/`),
the event director (`events/director.js`), the guild (`economy/`), arenas (`arena/`) and the Life 1 ban list
(`design/data/mortal_banned.toml`). Every mod id below was read on 18/11/2026 from the jars in the OCs Prism instance
(`tensura-neoforge-2.0.1.5`, `tensura_neb-2.0.0.3`, `tensura_iron_spells-2.0.0.0`, `irons_spellbooks-1.21.1-3.16.3`,
`occultism-1.21.1-neoforge-1.227.0`, `create-1.21.1-6.0.10`, `tombstone-9.5.6`) or from `pack/config/tensura/`.
**Verify in game** marks what an agent must confirm first. Nothing below is a story chapter: these are **systems** (§0).

Owner (Yasuke): *"I'd like a necromancy system if it integrates with what we have now — a bit like the anime Overlord. And for
people who want to be artificers there should be some stuff."* and, later the same day: *"All these systems must be separate
from a specific questline; everyone may do them. There is a grey or good version of everything, but you can always make evil
choices to get your way faster … I want several such systems."*

---

## 0. The general rule: standalone systems, two roads

**R12 — a system is not a chapter.** Necromancy, artifice and every later "path" are open to every Life 2 soul from the day it
arrives on the continent, whatever its Oath, act, race or tier. A quest chapter may *teach* a system (a `[[npc.talk]]` line, a
guide page, a tutorial chapter with `world = false`) and the story may *colour* it (the dark lane names it, the light lane frowns
at it), but no stage of the form `ttl.story.*`, `ttl.path.*` or `ttl.boss.*` ever gates a system's entry, its tools or its
ranks. `tools/validate.py` greps the system data files (`necro.toml`, `artifice.toml`, `choices.toml`) for those stage ids and
fails. Gates that *are* allowed: EP (Tensura's own, e.g. `WightKing epRequirement`), items, rank points the system itself pays,
faction bands (reputation is a consequence, not a story), nation rank.

**R13 — two roads.** Every system and every moral-choice event has (a) a **good or grey route**: slower, pays reputation, merit,
renown, light balance; (b) a **dark shortcut**: faster or richer, with *real* costs that are always the same five, in this order:

| Cost | Where it lands | Knob |
| --- | --- | --- |
| Karma (Life 2 "soul karma" for the next life) | `ttl.karma.chaos` raw (the same axis Life 1 uses; `karma.js` scores it) → the **next** rebirth's Fallen odds (`karma.toml [dark]`) and tier | `[road.dark] chaos = n` per act |
| World balance / tide | `TtlChronicle.note(server, 'dark_deed', player, {system, act})` → `balance` weight `dark_deed = -1`, `light_deed = +1` (`world.toml [balance]`) | per act |
| Faction reputation | `TtlRep.add` with the wronged faction (always the Holy Church for necromancy; the victims' home faction for the rest), `kill_penalty` on the continent as today; Hostile = guards and the **Hinata hunt** (`holy_hunt` event, `world-state.md` §6.1) | per act |
| Renown | `TtlRep.addRenown(p, -n)` for a dark act seen by a witness (a Life 2 player or a story NPC within 32 blocks), `+n` for the good route | per act |
| The chronicle in Discord | one `#story` line per *first* dark act of a kind per soul and per milestone (never spam): "A soul in Jura has raised the dead of Tempest's farms." | `discord = true` |

The good route pays: reputation, merit (`economy/merit.js`), renown, `light_deed` balance, favour points with the board's
faction (`ttl.favor.<f>`, the vassal road of §6.6), and the slow unlocks of the system itself. The dark road pays: time, EP, souls,
materials, and the system's *dark-only* unlocks (§2.6, §3.6). Neither road is ever locked (R12); a soul may walk both and the
chronicle remembers each act. **Life 1 stays mortal** (§0.2).

**R14 — witnesses, not surveillance.** Costs that depend on "being seen" (renown, guards) read entities within 32 blocks at the
moment of the act; a dark act in the wilds at night with nobody near costs karma, balance and the Church's Sense (§2.5) but
no renown. That is the owner's "you can always make evil choices to get your way faster": the shortcut is real, the price is paid
later, and a careful soul can hide most of it except the soul's own karma.

### 0.1 Systems this document designs, and the ones it only names

| System | Status here | Home (talk, not gate) | Good/grey route | Dark shortcut |
| --- | --- | --- | --- | --- |
| **Necromancer** (§2) | designed | Adalmann's crypt in the Labyrinth; the Outcast contact; Luminous' crypt | raise only monsters and the fallen of battle; a sanctum under your own land; the Church's "Licensed Exorcist" grey road | raise villagers, NPCs and players' corpses; the sick village; Soul Harvest |
| **Artificer** (§3) | designed | Kaijin's forge (Tempest), the Dwargon smithy, Vester's research (Tempest, phase town+) | guild commissions, public works machines, Create industry | stolen schematics, cursed engraving, daemon-possessed golems |
| Moral-choice events (§4) | designed, 12 events | radiant boards + the director | per event | per event |
| Beast-tamer / Ranger (Tensura taming + naming, Direwolf packs) | named only | Gobta's wolf kennels | — | — |
| Priest / Exorcist (Iron's holy school + Tensura holy magic, the Church) | named only (it is the necromancer's mirror; its good/grey/dark roads are the Church's own: heal, hunt, inquisition) | Lubelius | — | — |
| Summoner / Spirit-binder (Occultism rituals, Tensura `summon_daemon`, the Spirit Dwelling) | named only | Ramiris | — | — |
| Merchant / Caravan master (Lightman's shops, caravans, tolls) | named only | Blumund guild | — | — |

Each named one gets its own design later in the same shape (R12/R13, a `design/data/<system>.toml`, a `ttl/<system>/` folder).

### 0.2 Life 1 stays mortal (owner rule, `mortal_banned.toml`)

Today `namespaces = ["tensura", "tensura_neb", "greatsage", "lightmanscurrency"]`: Tensura's necromancy, naming, golems and
smithing bench are already impossible in `ttl:mortal_*`. **Not banned today**: Iron's blood school (`raise_dead`, `devour`,
`ray_of_siphoning` …) and Occultism's rituals (`possess_skeleton`, `wild_hunt`, `resurrect_mob`), which both exist in
Life 1 unless banned. Decision **O-N1** (§10): add `occultism` to `namespaces` (its items are all Life 2 things) and cancel
Iron's *blood* and *eldritch* school casts in the three Mortal dimensions through Iron's `SpellPreCastEvent` from KubeJS
(`NativeEvents` on `io.redspace.ironsspellbooks.api.events.SpellPreCastEvent`, **verify** reachable; fallback: `irons_spellbooks`
into `namespaces`, which is the master plan's own Q13 recommendation "Iron's in Life 1: off"). D4 ("Iron's learned spells carry
over") stays true for what a soul learned in Life 1 outside those two schools.

---

## 1. What the mods already ship (verified)

| Need | What exists | Where (verified) | Consequence |
| --- | --- | --- | --- |
| Undead player races | `tensura:wight` → `wight_king` (EP 200,000) → `spirit_skeleton` (800,000) → `divine_skeleton` (2,000,000); `ghoul` ("a vampiric thrall brought about by Blood Raise, highly weakened by sunlight") → `vampire` → `vampire_lord` / `vampire_overcomer` → `divine_vampire`. Wight: "Demi-Spiritual skeletal Undead Monster, highly weakened by sunlight"; Wight King: "power comparable to that of Demon Lord Seeds". Wight/Ghoul are in our Survivor tier and in the dark lists (`karma.toml`), Vampire in Legend | `assets/tensura/lang/en_us.json`, `race/wight/*.class`, `race/vampire/*.class`, `pack/config/tensura/race/wight_config.toml` | The necromancer's **race road** is Tensura's own evolution ladder; we add nothing to it. Wight King's class references `CREATE_LESSER_UNDEAD` (an intrinsic skill on evolution, **verify**) |
| Necromancy magic | Tag `#tensura:necromancy_magic` = `create_lesser_undead`, `create_greater_undead`, `curse`, `curse_bind` (inside `#tensura:spiritual_magic`, learnable from tomes / the Spellbinding Table). Lesser: cast 80 ticks, 800 magicule per undead, **300 s duration**, 1 (3 when mastered and sneaking), HP 20 / attack 5, modes Random / Skeleton / Zombie; Greater: 120 ticks, 8,000 magicule, 300 s, 1 (3 sneaking). Summons carry a `SummonUUID` tag | `data/tensura/tags/manascore_skill/skills/necromancy_magic.json`, `pack/config/tensura/ability/magic/spiritual_config.toml [CreateLesserUndead]/[CreateGreaterUndead]`, `CreateUndeadMagic.class` strings | Tensura's undead are **temporary battle summons**; a standing legion needs our own permanent undead (§2.3) |
| Undead entities | `tensura:skeleton`, `tensura:zombie` (`UndeadHumanoidEntity` with `SkeletonVariant`/`ZombieVariant`, an `owner` field, a `SkeletonClothingLayer` so they wear armour) | class list, lang `entity.tensura.skeleton/zombie` | Our permanent legion is made of these two entity types, armed through their equipment slots |
| Fear and aura | Extra skills `tensura:mortal_fear` ("Inspire a gripping fear of death in weaker enemies while empowering your allies"; learn at EP 200,000, haki radius 7 × size, strength on subordinates 1,200 ticks, fear level by EP difference × 0.25), `tensura:demon_lord_haki` (EP 200,000), `tensura:haki` (100,000), `tensura:majesty` (after 10 raids: permanent Hero of the Village); effect `tensura:fear` (`FearEffect`, mobs `AvoidFearedEntityGoal`); tag `#tensura:no_fear` | `extra_skills.json`, `extra_config.toml [MortalFear]/[DemonLordHaki]/[Haki]/[Majesty]`, class list | Overlord's "Despair Aura" is `mortal_fear`; nothing to build, only to *teach* and to gate the Tomb's aura ring on it (§2.4) |
| Command and domination | Unique `tensura:commander` (modes Communication: Movement / Targeting, Thought Domination), aspectual mental magic `tensura:dominate` ("Dominate over any low-leveled targets", `tensura.targeting.ep_not_meet`) and `demon_dominate`; tags `#tensura:no_mind_control`, `#tensura:no_possession` | `unique_skills.json`, class list, entity tags | A Rare unique for the general; `dominate` is the mid-game "bind a monster" tool for both paths |
| Subordinates, naming, armies | `TensuraTamableEntity`, `ISubordinate`, `SubordinateHelper`, `SubordinateFollowOwner`; `/tensura edit owner <e> name set|remove · permanent|temporary set <e1>|remove · neutral …`; `NAMING_EVENT(sub, owner, epGain, cost, type LOW/MEDIUM/HIGH, name)`; `tensura.naming.lack_EP`, `not_submit`, `had_owner`; gamerule `playerNaming`; tag `#tensura:can_be_named` (**verify** contents include `tensura:skeleton`/`zombie`/`bone_golem`); FTB compat `protectSubordinates = true`, `ftbAllyTensura = true` | `manas-integration.md` rows 182, 284, 290; lang; `ftb_config.toml` | `world-state.md` §6.5 counts an army as *named permanent subordinates within `muster_radius`*: undead and constructs join it the same way (§2.3, §3.3) |
| Golems | Items `tensura:<metal>_bone_golem` for low_magisteel, high_magisteel, mithril, pure_magisteel, orichalcum, adamantite, hihiirokane; entity `tensura:bone_golem` (`BoneGolemEntity`, `BoneGolemVariant`, `setRace`, `HumanoidContainer` inventory, `getDrop`); recipe = the metal's full armour set + 4 ingots + a **`tensura:daemon_core`**; placing needs EP ≥ 6,000 / 20,000 / 45,000 / 60,000 / 75,000 / 225,000 / 750,000 (`tensura.message.bone_golem.low_ep`); daemons can **possess** a golem body (`HPPossession`) | `data/tensura/recipe/*_bone_golem.json`, `entity/daemon_config.toml [LowMagisteel]…[Hihiirokane]`, advancement `build_body` | The artificer's constructs are Tensura's bone golems; the EP ladder is Tensura's own gate (R12-clean). The daemon-core ingredient is the **Overlord/Tensura crossover**: a necromancer's Summon Daemon fills an artificer's shell |
| Magic engines | Blocks `tensura:<stone>_bricks_magic_engine` (14 variants; recipe 7 bricks + `pure_magisteel_ingot` + `high_quality_magic_crystal`) and `labyrinth_bricks_magic_engine`; each lowers the magicule of surrounding chunks by `magicEngineReduction = 1000` within `magicEngineRange = 16` (labyrinth: 10,000 / 32) so mobs stop spawning below `minimalMagiculeSpawn = 10`; advancement "Use a Magic Engine to block monster spawn in an area" | `MagicEngineHelper.class`, `area_magicule_config.toml` | Magic engines are the pack's **mob-free zone** machine. Nation infrastructure (§3.5): engines in a nation's claims are counted as public works |
| Smithing | `tensura:smithing_bench` (298 recipes), `tensura:kiln` + `kiln_mithril` (melting 272, mixing 14), `refining` (31; pure magisteel from magic ore blocks), `mining_station` (28), **schematics** (`*_gear_schematic`, `japanese_sword_schematic`, `anti_magic_mask_schematic`, `pierrot_mask_schematic`, `spatial_blade_schematic`, …), `tensura:spellbinding_table`, `magic_tome` / `unbound_tome`, `warp_core` + warp pads, `element_core_*`, `tensura:godly_craftsman` (unique: "create masterpieces with ease and engrave your weapons"), `researcher` (unique: "study ancient magic tomes, reverse engineer them"), `degenerate` (Rare: craft/decraft), `creator` (Legendary) | recipe types, lang, `unique_skills.json` | The artificer's whole crafting tree exists; our work is **gating by rank, commissions, workshops and the economy**, not recipes |
| Iron's blood school | `acupuncture, blood_needles, blood_slash, blood_step, devour, heartstop, raise_dead, ray_of_siphoning, sacrifice, wither_skull`; `raise_dead` → `irons_spellbooks:summoned_skeleton` / `summoned_zombie` ("%s faded from this world", `summon_count` UI); Greater Conjurer's Talisman; `necronomicon_spell_book`, `blood_staff`, `blood_rune`/`blood_upgrade_orb`; mobs `necromancer`, `cultist`, `dead_king` (+ `dead_king_phylactery`, the Catacombs) | `spells/blood/*.class`, lang | Mana → magicule at ×50 (`iron_spell_config.toml manaConversionMultiplier = 50`), damage ×10; summons are timed. Second **temporary** summon source; `dead_king` is a ready-made T3 "lich" proxy (§2.7) |
| Iron's artifice | `arcane_anvil` (imbue, upgrade orbs: blood/fire/ice/lightning/holy/ender/evocation/nature/mana/cooldown/protection; `shriving_stone` removes), `inscription_table`, `scroll_forge` + inks (common…legendary), `alchemist_cauldron`, `pedestal`, runes, `arcane_essence`/`arcane_ingot`, `artificer_cane`, `mithril_ingot` (**Iron's own**, distinct from `tensura:mithril_ingot`), `energized_core`, `lightning_rod` (rod o' lightning) | lang | The artificer's **enchanting/inscription** half; two mithrils must be reconciled in JEI (a tag or a kiln recipe, §3.4) |
| Occultism | Rituals `possess_skeleton`, `wild_hunt` (hostile Wild Hunt skeletons), `resurrect_mob`, `resurrect_familiar`, `familiar_mummy`, `familiar_headless`, `familiar_guardian`, `familiar_blacksmith` (repairs gear), worker spirits `summon_foliot_lumberjack/farmer/cleaner/transport_items`, machine spirits `summon_djinni_manage_machine`, `*_crusher/smelter/crystallizer`, miners (`craft_miner_*`, Dimensional Mineshaft), `possess_iesnium_golem`, `craft_soul_gem`, `craft_familiar_ring`, `craft_storage_controller_base` (Dimensional Storage Actuator + stabilisers, wormholes), `craft_dimensional_battlefield` | `data/occultism/recipe/ritual/*.json`, lang | Occultism is the **summoner's** home (named only); the necromancer borrows `familiar_mummy/headless` and `resurrect_mob` for the grey "Keeper" road; the artificer borrows worker spirits and storage |
| Create 6.0.10 | kinetic only; **no magicule bridge exists** (Tensura's `compat/` has only JEI categories; no Create addon jar in the pack) | `tensura/compat/*.class`, `pack/mods/` | Create stays Dwargon's mechanical tier. A magicule↔SU bridge is a mod to *evaluate* (§9), not something to script |
| Tombstone | "Receptacle of Familiar" binding gated by `bosses.toml [tombstone] mode = defeated` | `compat/tombstone_bosses.js` | Undead legionnaires are never bindable (they are ours, tag `ttl.legion`); constructs may be (a golem is an item anyway) |
| Dimensions | `tensura:hell`, `tensura:labyrinth`, `tensura:boss_area`; ours `ttl:spirit_domain`, `ttl:walpurgis` (void flat, fixed midnight) | `data/tensura/dimension/`, decisions 18/11 | §2.4 recommends a **build**, not a dimension, for the sanctum |

---

## 2. The Necromancer

Overlord vibe, verified against what Tensura already is: **Ainz Ooal Gown** (Overlord, Maruyama, LN vol. 1–; the Great Tomb of
Nazarick, Death Knights raised from corpses, Despair Aura, Create Undead, the undead who do not tire) mapped on **Adalmann**
(Tensura LN vol. 10–11, anime season 3 "Tempest Labyrinth" arc; a Wight King, once a saint of the Western Holy Church, who guards a
floor of Ramiris' labyrinth with **Alberto the Death Knight** and **Wenti the Dragon Zombie**, and who Hinata once sent to his
death — *our interpretation* where the quest text says so). The Church's hunt is canon on both sides: Hinata's Holy Knights
purge undead; Luminous Valentine, the Church's secret god, is herself a vampire (LN vol. 7).

### 2.1 How you become one (any of these, no chapter)

| Road | What it is | Gate (R12-clean) | Where it is taught |
| --- | --- | --- | --- |
| **Race** | Reborn as `wight` or `ghoul` (Survivor tier, and the Fallen's guaranteed dark offer), or evolved there later by Tensura's own "Reincarnation" magic / a Character Reset Scroll. `wight_king` at EP 200,000 is the Overlord moment: the Voice says "Requirements met. The Wight King rises." (Great Sage style, master plan §12) and the chronicle notes `wight_king` | Tensura EP | the Voice |
| **Skills** | Learn `create_lesser_undead` (tome / Spellbinding Table — Tensura's own spiritual-magic learning), then `create_greater_undead`, `curse`, `curse_bind`; `mortal_fear` and `demon_lord_haki` at EP 200,000; Iron's `raise_dead` scroll (blood school) | Tensura EP + tomes | Adalmann's crypt (§2.7), the Outcast contact (dark line), Iron's scroll loot |
| **The Rite** (ours) | `/ttl necro rite` at a **Bone Altar** (§2.3): any Life 2 soul with one necromancy spell known (Tensura or Iron's) and 10 `ttl:soul_ash` becomes a *Necromancer* (`ttl.necro.rank = 1`, title "Gravebinder"). Nothing is granted that Tensura does not own; the rite only opens **our** layer (legion, sanctum, ranks, boards) | items + one spell | guide page "The dead and the law"; any board |

**Light souls may walk it** with the lore of Adalmann: the Church calls him an abomination, Rimuru made him a guardian. A light
necromancer is the **Keeper**: raises only monsters and the fallen of battle, keeps the dead of others buried, and may even hold
the Church's grey licence (§2.6). The Oath only colours the lines NPCs speak (`[[npc.talk]] path`).

### 2.2 Ranks (`necro.toml [[rank]]`, points from acts of the system itself)

| Rank | Title | Points | Unlocks (our layer) |
| --- | --- | --- | --- |
| 1 | Gravebinder | the Rite | legion cap 2, a **Crypt** sanctum (§2.4), the Bone Altar |
| 2 | Bonecaller | 30 | cap 4, armed skeletons (armour slots), `ttl:grave_lantern` |
| 3 | Death Marshal | 120 | cap 6, one **Death Knight** (§2.3), the Mausoleum ring |
| 4 | Overlord | 400 + `wight_king` *or* `vampire` *or* `mortal_fear` learned | cap 8 (10 in a war muster), two Death Knights, the Great Tomb ring with the **aura hall**, the title line "Overlord of <sanctum name>" |

Points: raising a legionnaire 1, a named legionnaire 3, a legion kill of a boss-tier target 5, a sanctum ring built 10, a
moral-choice event resolved through necromancy 5 (either road: the system does not judge, the world does), the Keeper road's
"lay to rest" 2. Weekly cap 60 (anti-farm, the guild pattern).

### 2.3 Raising and keeping a legion (on top of Tensura's subordinates)

Tensura's `create_*_undead` summons last 300 s and are the **battle spell**; Iron's `raise_dead` likewise. The **legion** is ours:

- **Soul Ash.** Every kill a necromancer makes of a humanoid-like entity (`#tensura:human_like`, villagers, illagers, our
  `tensura:goblin/orc/lizardman/dwarf/falmuth_knight`, players) has a chance (`ash_chance = 0.25`, ×2 with `curse` active on the
  target) to drop `ttl:soul_ash` (startup item, `items.js` pattern). Monsters (`#tensura:hostile_monster`) drop **bone dust**
  (`ttl:bone_dust`) instead. Ash is the **dark** currency, dust the **grey** one; both are sinks (§5). Spawner mobs and test
  bots never drop either (the karma anti-farm rule).
- **The Bone Altar** (`ttl:bone_altar`, a KubeJS block: bone block + daemon-core-less recipe; placed only on the owner's claim or
  in the wilds, never in a canon domain — `TtlDomains.canEdit`). `/ttl necro raise <skeleton|zombie> [name]` at the altar:
  consumes 4 bone dust **or** 1 soul ash, summons `tensura:skeleton`/`zombie` with `PersistenceRequired`, `Tags:["ttl.legion",
  "ttl.legion.<ownerUuid>"]`, `/tensura edit owner <e> permanent set <owner>` (**verify** the undead entity accepts a permanent
  owner; fallback `data merge entity {Owner:<uuid>}` on the `owner` field the class exposes) and our record `ttl.necro.legion`
  (`[{uuid, kind, name, raisedAt, dormant}]`). An **ash-raised** undead is stronger (`ash_mult = 1.5` on HP/attack via
  `attribute … base set`) — the shortcut — and costs `chaos +3`, `dark_deed`, Church −3, renown −1 if witnessed, and the
  chronicle line on the first one. A **dust-raised** one is the grey road: `light_deed = 0` (neutral), no faction cost.
- **Naming** goes through Tensura's own naming screen (EP cost, `NAMING_EVENT`). A named legionnaire counts for the war muster
  (`army_named_only = true`): `nations.js muster` needs **one reserved line** — count entities tagged `ttl.legion` and
  `ttl.construct` with `getName()` non-empty like any subordinate (they already are subordinates if the owner set works). The
  Voice's "A Name Is Given" fires as today.
- **Death Knight** (rank 3): `/ttl necro knight <name>` consumes a **player's or an NPC's corpse** — i.e. 1 soul ash dropped by
  a player kill in an arena/war, or by a story NPC kill (the `kill_penalty.npc` already paid) — plus a full `high_magisteel` armour
  set and sword: a `tensura:skeleton` equipped with it (equipment slots, `SkeletonClothingLayer`), HP ×4, attack ×2, Strength I, name
  "<name>, Death Knight", `Tags:["ttl.legion","ttl.knight"]`. Max 1 (rank 3) / 2 (rank 4). Lore: Overlord vol. 1, the Death Knight
  made from a villager's corpse at Carne; here the corpse is always one you killed yourself (the price is already in the kill).
  Grey alternative: a knight from **bone dust ×32 + the armour**, HP ×3 (slower to farm, no corpse).
- **Elder Lich / Dragon Zombie**: not ours to make — the T3 proxy fights of §2.7 (Iron's `dead_king`, a scaled `tensura:skeleton`
  "Alberto"). Owning one is a boss-capture question and stays `[tombstone] mode = defeated`.
- **Caps** (`necro.toml [legion]`): active (loaded, awake) legionnaires per soul = rank cap above; `sanctum_cap = 12` dormant.
  Dormant = **not an entity**: `/ttl necro stow` at the sanctum writes the legionnaire's NBT (`entity.getNbt()` minus position) into
  the record and discards the entity; `/ttl necro rouse <n>` re-summons it at the altar (the same pattern the Tombstone receptacle
  uses, minus the mod). This is what keeps a 10-player server at 10 × 8 = 80 undead *at most* awake, and usually far fewer
  (§6). Unloaded legionnaires still exist as normal entities (chunks unloaded, no tick cost); `muster` only counts loaded ones,
  as the story demands ("bring the army to the muster").
- **Control** uses Tensura's own subordinate orders (follow / wander / sit through `SubordinateFollowOwner` and the naming/owner
  menu; **verify** the order UI works on `tensura:skeleton`) plus `tensura:commander` for the general. Our layer adds only
  `/ttl necro recall` (teleport loaded legionnaires to the owner if within 64 blocks; otherwise rouse at the altar) and `/ttl
  necro stand` (NoAI on, as a tomb guard).
- **Sunlight.** Wights are "highly weakened by sunlight" (Tensura's own race tick). Legion undead get Tensura's skeleton/zombie
  behaviour as shipped (**verify** whether `UndeadHumanoidEntity` burns); if they do not, no change — Overlord's undead do not.
- **PvP.** A legionnaire's hit on a player is the owner's hit: `pvp/pvp.js` resolves `source.actual` → owner (one reserved line,
  `TtlLegion.ownerOf(entity)`), so undead obey the arena/war/quest scope and are **cancelled** elsewhere like their master.
  Legion vs legion in a war is just mobs hitting mobs (FTB `protectSubordinates` is off in a war between the two nations
  **verify** how Tensura's FTB compat reads "non-pvp claims" during our war flag; fallback: the war layer sets the two nations'
  claims to PvP for `war_hours`).

### 2.4 The sanctum: a build, not a dimension (recommendation)

**Recommend a placeable build** ("Tomb kit") on the necromancer's own land, placed by `life/builds.js`'s generic placer from
`design/builds/tomb_crypt.toml` / `tomb_mausoleum.toml` / `tomb_great.toml` (blueprints under `blueprints/`), as rings around the
Bone Altar — the same ring lever as "Tempest grows" (`world-state.md` §4). Why not a dimension: a per-player dimension is a Java
change and a chunk-loading cost we refused for every other personal thing; a shared `ttl:catacombs` dimension would make every
necromancer's tomb a public arena, which breaks the "sanctum" (and would need domains of its own). A build on a claim already gets
FTB protection, the nation's upkeep economics, BlueMap, and sits in the world where the Church can *find* it (§2.5) — which is
the Overlord story: Nazarick is a place in the world. Underground by default (the crypt ring digs a 15×15×8 vault, y −1 to −8
below the altar; placement refuses water and canon domains; `TtlDomains.canEdit` + claim owner check).

| Ring | Rank | What it adds | Cost (sink) |
| --- | --- | --- | --- |
| Crypt | 1 | vault, altar niche, 4 bone-dust sconces (`ttl:grave_lantern`), 6 stow niches | 16 bone dust + 32 stone bricks, 1 gold |
| Mausoleum | 3 | a hall with 12 niches, a throne (`minecraft:skeleton_skull` + blackstone), two guard posts (`stand`), a **Magic Engine** niche (the mob-free zone is bought from an artificer — the one cross-path dependency, §3.5) | 8 soul ash *or* 64 bone dust, 5 gold |
| Great Tomb | 4 | the **aura hall**: while the Overlord stands on the throne `mortal_fear`'s own haki is the aura (nothing scripted); our layer adds the entry line, a boss bar "The Great Tomb of <name>" for visitors inside the box, and the guard muster point | 24 soul ash *or* 192 bone dust, 20 gold, an artificer's `tensura:labyrinth_bricks_magic_engine` commission |

The sanctum is a **duel/raid venue** on request (`arenas.toml [[arena]]` kind `sanctum`, owner-flagged): a challenger may ask
`/ttl necro challenge <owner>` — an arena pact inside the tomb box (PvP scope: arenas), the legion fights too. Outside a pact
the tomb is as safe as any claim.

### 2.5 The Church, the hunt and the others (reputation consequences)

- **Seeds** already exist: `holy_church` seeds `ghoul −25, wight −25, vampire −40` (`factions.toml`). Nothing changes there.
- **The Church's Sense** (`necro.toml [church]`): every *dark* act (ash raise, Death Knight from a corpse, the shortcut of a §4
  event) adds `sense` points to the soul (`ttl.necro.sense`, decays 5/week). At `sense ≥ 20` the soul is **Marked** (stage
  `ttl.necro.marked`): the guild board shows a Church bounty on it (a radiant `hunt` template, §4 and `world-state.md` §6.8),
  Lubelius guards are Hostile to it whatever its band, and Hinata's wild roll gets `path_mult`-like `necro_mult = 3` for that soul
  (one reserved line in `wild.js`: the `[boss.wild]` chance multiplier reads `TtlNecro.hunted(player)`). At `sense ≥ 50` the
  **Holy Hunt** on that soul: the director's `holy_hunt` event (§6.1) may be fired *on a soul* (24 h, server-wide line "The
  Church has named <soul> an abomination"); surviving 2 h online pays the "Unbroken" title as designed. The Hunt never enters a
  tomb box unless the soul leaves it: the Hinata instance is summoned at the tomb's door (an echo if `firsts.hinata` exists).
- **Grey licence** (the Keeper road, §2.6): Honored with the Church + zero sense for 14 days → `/ttl necro licence` at Lubelius:
  stage `ttl.necro.licensed`, title "Licensed Exorcist", the Church's board pays for *laying to rest* (radiant `cleanse` kind) and
  the Church ignores dust-raised legions. A single dark act revokes it (and costs Church −20, the chronicle line).
- **Tempest** does not care (Adalmann serves Rimuru): tempest rep is untouched by raising, except `kill_penalty` on its ground.
  **Blumund/Falmuth** treat a legion in their domain as an armed band: guards Hostile inside the domain while ≥ 3 legionnaires are
  awake (`TtlRep.guardsHostile` reserved line). **Orc Horde / Outcasts**: +2 per Death Knight (the dark lane's friends).
- **Moods** (`world-state.md` §3.3): the milestone `necromancer_rises` (first Overlord) sets `mood = { holy_church = -1 }`;
  `tomb_of_the_era` (first Great Tomb) opens the conflict `lubelius`? **No** — thrones are §6.6's business; it only unlocks the
  event `holy_crusade` (a server raid on a Great Tomb, §4.9 variant) and the Hall section "Tombs".

### 2.6 Two roads inside the system (R13 applied)

| | Good / grey (the Keeper) | Dark shortcut (the Overlord's way) |
| --- | --- | --- |
| Raw material | bone dust from monsters (4 per raise); lay the dead to rest (`/ttl necro rest` on a grave/corpse spot: +2 points, +1 Church) | soul ash from humanoids and players (1 per raise, ×1.5 stats) |
| Death Knight | 32 dust + armour, ×3 | 1 corpse ash + armour, ×4, Strength |
| Events (§4) | heal, bury, escort | raise the sick, the hostages, the refugees |
| Pays | Church/Tempest rep, licence, merit when the legion builds (yes: a legionnaire placing `ttl:infrastructure` under `/ttl necro build` counts for merit-lite at ×0.5 — Geld's corps of the dead) | time; the Marked/Hunt line opens the "Unbroken" title and the Outcast/Horde favour |
| World | `light_deed` 0 / `rest` +0.5 | `dark_deed` −1 per act, `necro_dark` milestones feed the dark tide |

### 2.7 Story hooks, boards, arenas, outside the continent (colour, never gates)

- **Adalmann's crypt**: a small build on a Labyrinth floor (the Labyrinth arena hall is Tensura's own; put the crypt in a side
  room of `tensura:labyrinth`, placed by `builds.js` in that dimension like `spirit_dwelling` is placed in `ttl:spirit_domain`),
  with an Easy NPC "Adalmann" (humanoid, skeleton skin — a DEFAULT variant until an own skin exists, R4) who **teaches** (talk,
  buttons `ttl necro guide`), posts the **Crypt board** (radiant, faction `tempest`, path any: cleanse/escort/hunt/rest templates),
  and whose statue line changes with the soul's rank. Proxy fights (`bosses.toml`, T3, `proxy = true`): **Alberto the Death
  Knight** on `tensura:skeleton` (armed, `hp_mult 4`), **Wenti** on `irons_spellbooks:dead_king`? — no: Wenti is a dragon
  zombie; keep `dead_king` as **"The Dead King of the Catacombs"** (Iron's own structure boss, lore-named, T3, `requires = []`)
  and leave Wenti for a later dragon mod. Both path-free (R2), both with a per-party cooldown (§7).
- **Chapter colour**: the dark lane of Act I ("The Outcast's Mark") gets one talk line pointing at the Rite; Act V's light lane
  gets Hinata's line about Adalmann. No task of chapters 0–13 reads `ttl.necro.*` (R7 extended to system stages).
- **A tutorial chapter** `chapter_16_gravebinder.toml` (`world = false`, `system = "necro"`: the generator marks it optional, its
  first quest is an `item` task — hold a tome — never a stage): 10 quests teaching dust → altar → raise → name → stow → the
  licence, rewards are coins and bone dust, never a unique (rule 5(d)).
- **Arenas**: `arenas.toml` gets `allow_legion = true` per arena and a match type **legion** (owner's undead and constructs enter
  with the fighter; cap 4 per side; `TtlArenas` strips the rest at the gate). The Labyrinth arena is Ramiris' — Adalmann lore.
- **Wars**: the legion is an army (§2.3); a war with a Great Tomb on the land makes the tomb a `raid_objective` (score 5).
- **Outside the continent** (R11): no Church Sense, no hunt, no domain rules; raising works as shipped by the mods plus our
  altar; the legion cap still holds (it is a server rule, not a story rule), ash still drops, karma is still the soul's own.

---

## 3. The Artificer

Canon anchors: **Kaijin** the master smith, **Kurobe** who forges Tempest's weapons and magisteel, the dwarf brothers **Garm**
(armour), **Dold** (crafts, decoration) and **Mildo** (building), all from Dwargon's "Armed Nation" tradition (Tensura LN vol. 1–2,
anime ep. 5–6 "Hero King, Gazel Dwargo"); **Vester**, the court mage disgraced for the Kaijin affair who becomes Tempest's head of
research (potions, later magic-science; LN vol. 4+); the Dwarf King's own smithing of Rimuru's gear; Tempest's later "magic
science" labs are our reading of LN vol. 8–10 (*our interpretation* in texts). The bone golem of Tensura is the pack's construct;
Overlord's Golems (Nazarick's Eight-Edge Assassins are not golems; its golems are the Great Tomb's doors and statues) are flavour
only.

### 3.1 How you become one (any road, no chapter)

| Road | What | Gate |
| --- | --- | --- |
| **Craft** | Smithing Bench + Kiln (Tensura's own learning: schematics from dwarf trades and loot) | items |
| **Unique** | `godly_craftsman` (the Rare craft unique; registry caps), `researcher`, `degenerate`, `analyst`; Craft-heavy souls already roll craft uniques more (plan §3) | registry |
| **The Charter** (ours) | `/ttl artifice charter` at a **Workshop Bench** (`ttl:workshop_bench`, a KubeJS block: smithing bench + magic crystal) with any 3 schematics in the inventory: `ttl.artifice.rank = 1`, title "Journeyman" | items |

Race: Dwarf gets the Dwargon seed (+20) and the Dwarven Masterwork Ring relic road (plan §11); nothing is dwarf-only.

### 3.2 Ranks (`artifice.toml [[rank]]`)

| Rank | Title | Points | Unlocks |
| --- | --- | --- | --- |
| 1 | Journeyman | charter | construct cap 1, the Workshop (home), commissions tier 1, `tensura:low_magisteel_bone_golem` placing is Tensura's EP 6,000 anyway |
| 2 | Artisan | 40 | cap 2, commissions tier 2 (high magisteel, mithril), **engraving** (Iron's imbue at the Arcane Anvil is open; our layer adds the engraving **licence** for Tensura's `godly_craftsman` engrave line through a rank-gated `ttl:engraving_chisel`) |
| 3 | Master Artificer | 150 | cap 3, magic engines commissions (the Mausoleum's niche, nations' zones), the **Research Bench** (Vester: potions/element cores line), Create contraption commissions |
| 4 | Grand Artificer | 500 + `godly_craftsman` *or* `researcher` held *or* a Dwargon Exalted band | cap 4 (6 in a war muster), hihi'irokane commissions, one **Warden** construct (§3.3), the era's "Grand Artificer" title (one per era, like Grand Architect) |

Points: a commission delivered 5–20 by tier, a construct built 3, an engine placed in a Public Works chunk 5 (×3 if the chunk is
Commons), a §4 event resolved with artifice 5, a magisteel/mithril/orichalcum/adamantite/hihi'irokane *first* on the server 10
(chronicle `firsts.craft.<metal>`). Weekly cap 60.

### 3.3 Constructs as subordinates, and the army cap

- A **construct** is a Tensura bone golem the artificer placed (`tensura:bone_golem` with `Owner` = placer; **verify** the golem
  takes the placer as permanent owner; fallback `/tensura edit owner … permanent set` on `EntityEvents.spawned` from the item,
  tag `ttl.construct`, `ttl.construct.<uuid>`), recorded in `ttl.artifice.constructs` (`[{uuid, metal, name, dormant}]`).
  Dormant = **the item**: a golem stows as its own `getDrop` item (Tensura's design), so the "rack" is just a chest: zero cost.
- **Naming** a golem (`#tensura:can_be_named` — **verify**) makes it count for the war muster like any named subordinate (one
  reserved line in `nations.js muster`, shared with §2.3). Army cap for constructs = the rank cap (1–4, 6 in a war muster).
  Golem EP requirements are Tensura's own ladder (6k … 750k), so the army's *quality* is EP-gated, its *size* rank-gated.
- **Daemon-possessed golems** (the dark shortcut): Tensura lets a summoned daemon possess a golem body (`HPPossession`). A
  possessed golem is stronger and autonomous but its daemon is a majin with a will: **verify** in game what possession does to
  ownership. Our rule: a possessed construct counts as a **named** army unit at once (no naming EP) — the shortcut — and costs
  `chaos +3`, `dark_deed`, Church −3, and, if it dies, the daemon is loose (a hostile `tensura:lesser_daemon` at the spot). The
  grey road names the golem the normal way (EP).
- **Warden** (rank 4): a hihi'irokane or adamantite golem with a **magic engine core** (recipe: golem item + engine block +
  `tensura:warp_core` at the Workshop Bench → `ttl:warden_core` applied by `/ttl artifice warden <golem>`): HP ×3, immune to
  fear, and it **holds a zone**: while it stands in a Public Works chunk the chunk counts as engine-covered (mob-free) and the
  Warden posts to the nation's Discord channel when a non-member enters at night. One per soul.
- **Occultism worker spirits** are not constructs (they are the summoner's); an artificer may use them, no cap of ours.

### 3.4 Gear, engines, enchanting, inscription, Create

- **Magisteel ladder** is Tensura's: low → high → pure magisteel (refining from magic ore), mithril, orichalcum, adamantite,
  hihi'irokane, all through kiln melting/mixing and the Smithing Bench. The pack's **boss gates** on key materials (plan
  "Create skipping tiers": Magisteel at T1, Adamantite at T2, Hihi'irokane at T3) are implemented as **recipe stages**: KubeJS
  `ServerEvents.recipes` replaces the kiln/refining recipe outputs of `adamantite_ingot` and `hihiirokane_ingot` with versions that
  require a `ttl:tier_seal_t2` / `_t3` catalyst — no: KubeJS recipes cannot keep a catalyst. **Decision O-A2**: gate by the
  *schematic*, not the ingot: `ttl:adamantite_gear_schematic` etc. are already items; LootJS drops them only from T2/T3 bosses and
  the artificer's commissions, and the smithing recipes already consume schematics (**verify** that Tensura's smithing recipes
  take the schematic as an ingredient; if they do not consume it, the gate is "have it in the bench", which is enough).
- **Engines**: as shipped; our layer counts engines in nation claims (`nations/infra.js`, §3.5) and sells **engine commissions**.
- **Enchanting / inscription**: Iron's Arcane Anvil (imbue a spell on gear, upgrade orbs), Inscription Table, Scroll Forge +
  inks, and Tensura's Spellbinding Table — all open (R12). Our layer: **engraving licence** (rank 2) for Tensura's
  `godly_craftsman` engrave (`/engrave` is GAMEMASTER; the unique's own engrave UI is the player path — **verify** the unique's
  engrave needs nothing from us), and a **cursed engraving** dark shortcut: at the Bone Altar (cross-path) an artificer with soul
  ash may engrave `tensura:tsukumogami`? — no, that enchantment is Tensura's own; keep ours simple: `ttl:cursed_whetstone` (1 soul
  ash + 1 arcane essence) applies Iron's `blood_upgrade_orb`-equivalent upgrade *and* Tensura's `curse` on hit (an `ItemEvents`
  hook: on hit by a cursed-tagged weapon, `/tensura` can't cast for a mob; so: apply `tensura:fear` + Wither I to the target, 10 %
  chance) with the five costs. The grey road is the Arcane Anvil with mined/looted orbs.
- **Mithril ×2**: `tensura:mithril_ingot` and `irons_spellbooks:mithril_ingot` both exist. Add a kiln **melting** recipe each way
  (1:1) in `economy/recipes.js` so neither mod's content is orphaned; JEI shows both.
- **Create**: Dwargon's industry as decided (D8). No magicule bridge exists; **Create: New Age** (electricity, generators) and
  **Create: Occult Engineering** are the master plan's bridge candidates and must be *evaluated* for NeoForge 1.21.1 builds
  (`/add-mod`, §9). Until then "magicule-powered contraptions" are flavour: a Master Artificer's **contraption commission** is a
  radiant `build` template (place a Create water wheel/mill/press line in a Public Works chunk) paid in merit ×3 — Dwargon's
  waterwheels are canon (anime ep. 5).

### 3.5 Workshops, guild contracts, merit, nation infrastructure

- **Workshops**: Kaijin's forge in Tempest (the existing forge spot; `npcs.toml` Kaijin gets a **Workshop board**, radiant, faction
  `tempest`), the Dwargon smithy (Garm/Dold/Mildo at 423, −1084; board faction `dwargon`), and **Vester's research bench** in the
  Tempest *town* phase ring (`min_phase = "town"`, `world-state.md` §4: the town ring gains a research hut; Vester as Easy NPC
  humanoid). All three teach (talk) and post commissions. A player's own Workshop is the `ttl:workshop_bench` block on a claim.
- **Commissions** = radiant templates of kind `collect` with the artificer twist `made_by = true`: the hand-in must be an item
  the player crafted (KubeJS `ItemEvents.crafted` stamps `ttl.made_by` on smithing-bench/kiln outputs, **verify** the event fires
  for Tensura's bench; fallback: no stamp, any item). Pay: coins + rep + artifice points + **unique recipe unlocks** (§3.6).
  Commissions are the artificer's radiant board slice; the guild's (Fuze's) board keeps its own rows.
- **Merit** (plan §13 / merit-lite): `ttl:infrastructure` gains the engine blocks, warp pads, Create kinetic blocks (per Q21) and
  the Workshop Bench; an engine in a Commons chunk is ×3. Points above.
- **Nation infrastructure** (`nations/infra.js`, new): the weekly value loop counts, per nation, `engines` (magic engines inside
  its claims), `wardens`, `warp_pads` (a Dwargon-style warp network, Tensura's own `warp_core` + pads) and `workshops`. Effects
  (`nations.toml [infra]`): `upkeep_discount_per_engine_pct = 2` (cap 20 %: the engines keep the land safe, so fewer guards —
  the owner's "upkeep reduction?" answered yes, capped), `value_per_engine = 5`, `value_per_workshop = 10`, a warp pad network of
  ≥ 3 pads = `rank_bonus_chunks +1`. Unpaid-upkeep debuffs stay as designed.
- **Renown**: `factions.toml [renown] stage` gains `"ttl.artifice.rank4" = 10`, `"ttl.necro.rank4" = 10` (both systems are worth
  the same to the world; the Church's opinion is reputation, not renown).

### 3.6 Unique recipes gated by rank and reputation (sources and sinks)

| Recipe (KubeJS, `artifice/recipes.js`) | Gate | Sink | Source |
| --- | --- | --- | --- |
| `ttl:workshop_bench` | none | 1 smithing bench + 4 low-quality crystals | — |
| `ttl:engraving_chisel` | rank 2 | 1 pure magisteel + 1 arcane essence (Iron's) | enables engraving |
| **Magic engine commission** (Mausoleum/nation) | rank 3 | the engine's own recipe + 2 gold fee to the workshop (sink) | the client pays 5 gold (transfer) |
| `ttl:warden_core` | rank 4 | golem + engine + warp core | the Warden |
| Dwarven Masterwork Ring (plan §11 relic) | Dwargon Exalted + rank 3 | 1 hihi'irokane ingot, 8 gold | faster smithing (Haste on bench use) |
| Anti-Magic Mask (Tensura's own, schematic) | the schematic from Shizu's fight (exists) | — | — |
| `ttl:cursed_whetstone` (dark) | the Bone Altar | 1 soul ash + 1 arcane essence | the five costs |
| Stolen schematics (dark) | the Act II dark lane already has "steal the schematics" (talk); ours: `/ttl artifice steal` inside the Dwargon smithy domain at night, 30 s channel: a random dwarf-trade schematic, Dwargon −20, `dark_deed`, chaos +3, guards Hostile while in the domain | — | a schematic the grey road buys with 20 gold + Dwargon Friendly |

Economy targets (`/ttl econ` report): the two systems add sinks ≈ 25 % of an active crafter's weekly faucet (rings, engines, fees)
and no new coin faucet except commissions (which replace guild bounties for that player: `per_player_open` is shared).

---

## 4. Moral-choice world events (random, radiant, on the continent)

A family of **director events** (`events.toml [[event]]`, kind `choice`, `scope = region`) that spawn a small instanced scene at
a wild spot (`wild.js pickSpot`: loaded chunk, outside domains, right surface) near Life 2 players and post the same scene as an
**offer on the region's radiant board** (`radiant.toml [[template]] kind = "choice"`), so a soul can walk into one or take it from
a board. Rules: continent only (R11); never in Life 1; one scene per region at a time, `max_active = 3` server-wide, `ttl_minutes
= 30` then the scene resolves itself the *neutral* way (people die, bandits leave, the egg hatches wild) and the chronicle notes
`unresolved`; resolution is **per scene, first come**, but every soul within 48 blocks at the resolution is credited (the boss
credit rule) and pays that road's costs *if it took part* (hit, healed, raised; otherwise only the witness line). Scaling: the
scene's `count` fields scale with Life 2 players online: `n = base + per_player × (online − 1)`, capped (`max_mult = 3`); the
reward scales the same way; a scene near a party scales by the party, like a boss.

Each event has a **good route** (slow, pays faction/merit/light), a **dark shortcut** (fast, pays the five costs), the tools
each uses, and the chronicle fields it feeds. Costs below are the defaults of `choices.toml` (one `[[choice]]` per event:
`routes.good`, `routes.dark`, optional `routes.grey`).

| # | Event | Scene (base counts, scale) | Good / grey route | Dark shortcut | Tools | Consequences (good → dark) |
| --- | --- | --- | --- | --- | --- | --- |
| 4.1 | **The sick village** (the owner's example) | 6 villagers with Weakness + Poison in a 3-hut camp (Easy NPC `villager` kind or vanilla villagers tagged `ttl.scene`), a plague mist (`tensura:miasmic_mist` cosmetic); +2 villagers per extra player | **Heal**: 2 `ttl:hipokute_salve` (brewed: hipokute grass + honey, or Iron's `heal` cast ×3 per villager, or Tensura `healing_potion`) per villager over 10 min; they recover, a Blumund caravan takes them | **Raise**: cast `create_lesser_undead` / `raise_dead` *on* them, or `/ttl necro raise` at a portable altar: they die (no suffering, the Voice says so) and each becomes a legionnaire at once (`ash_mult`), 1 soul ash each on top | Necromancy, healing (Iron's holy / Tensura water), alchemy (artificer: the salve recipe is a Research Bench recipe) | good: blumund +8, tempest +4, light +1, renown +3, `counts.healed`; dark: chaos +6, `dark_deed` ×2, blumund −15, holy_church −10, sense +10, renown −5 if witnessed, `#story` "the plague village of <region> did not recover" |
| 4.2 | **Bandit hostages** | a camp of 6 `tensura:orc` + 1 captain ("clear" kind) holding 3 bound Easy NPC hostages; +3 orcs/+1 hostage per player | **Rescue**: clear the camp, cut the bonds (right-click), escort them 200 blocks to a road (escort kind) | **Pay or take**: pay the captain 5 gold (grey, instant, funds the Horde: orc_horde +5) — or kill the hostages yourself for ash and loot the camp with the captain alive (dark) | Combat, diplomacy (coins), necromancy (ash) | good: blumund/falmuth +6 (hostages' home), renown +2; grey: coins sink, orc_horde +5; dark: chaos +9, `dark_deed` ×3, home faction −20, sense +6, renown −6 |
| 4.3 | **The starving band** (ties to the Orc Lord famine, `world-state.md` §6.7) | 5 `tensura:orc` tagged `ttl.horde` *not* attacking, begging at a farm; after `horde_seen` only | **Feed**: 32 food items into their bowl (a `ttl:offering_bowl` block) → they leave as a `dust`-free *allied* band for 1 h (follow kind) and `flags.orcs_fed` | **Devour / enslave**: kill them (Valor as any kill) — or **Predator/Gluttony holders** `absorb` them for EP ×2 (the Tensura skill is the shortcut), or `dominate` them into subordinates without naming (temporary owner) | Diplomacy (food), Tensura `predator`/`gluttony` (absorbers), `dominate`, combat | good: tempest +5, orc_horde +10, light +1; dark: chaos +4, orc_horde −10 (the Horde remembers), `dark_deed`; absorbers: EP as the skill gives, nothing more — Tensura's own mechanic is not punished twice |
| 4.4 | **A wounded monster wants a name** | one `tensura:direwolf` (or `blade_tiger`, `horned_bear`) at 10 % HP, `Tags:["ttl.scene","ttl.wants_name"]`, non-hostile; ×1 | **Heal and name**: heal it (any heal), then Tensura's naming (EP cost) → a named subordinate (army-worthy) and `flags.named_wild` | **Bind it**: `dominate` at full force (EP gate, no cost to you), or kill it for the trophy and raise its bones (necromancer: a `tensura:skeleton` "beast" variant, **verify** zombie/skeleton variants) | Naming (EP), `dominate`, necromancy | good: renown +3, "A Name Is Given" line; dark: chaos +2, `dark_deed`, renown −2 if witnessed |
| 4.5 | **The broken dam / the broken golem** | a leaking dam (a 7×3 wall of `ttl:cracked_dam` blocks with water behind) above a farm, *or* a `tensura:bone_golem` lying "broken" (NoAI, 1 HP) in a dwarf outpost; one of the two by region (W/R dam, D/J golem) | **Repair**: artificer: 8 stone bricks + 2 low magisteel into the cracks (right-click) / for the golem, a `low_magisteel_ingot` + daemon core *or* the Occultism Blacksmith familiar's repair → the golem joins the outpost as a guard (not yours) | **Take it**: the golem becomes yours (`/ttl artifice claim`): fast, but it was the outpost's (dwargon −15, `dark_deed`); the dam: let it burst for the flooded farm's loot (a chest of 6 silver + crops; the farm's villagers "drown" — Blumund −20) | Artifice, Occultism familiar, greed | good: dwargon/blumund +8, merit +50, artifice points +5; dark: chaos +5, faction −15/−20, renown −4, `dark_deed` |
| 4.6 | **The merchant with cursed goods** | an Easy NPC trader with 5 shiny items (loot-table rolls: magisteel gear, a schematic, a scroll) each carrying `ttl.cursed` (on equip: Wither + Tensura `curse` effect every 5 min) | **Cleanse**: Iron's `cleanse` / holy water / an artificer's Research Bench "uncurse" (2 holy runes) → sell clean (grey: keep 1); or warn the next board (good: `deliver` a letter to the region's capital board) | **Resell**: sell them on your Lightman's shop / hand them to another player untouched; or **engrave the curse deeper** (cursed whetstone) and keep a cursed blade: +15 % damage, the five costs when first used on a player | Artifice (uncurse/engrave), holy magic, trade | good: blumund +5, light +0.5, artifice +5; dark: chaos +4 per cursed item sold to a *player* (the buyer's `ttl.cursed.from` names you; the chronicle line when it triggers) |
| 4.7 | **Refugees from Falmuth** (after `act5_reached` *or* any Falmuth conflict, else from Blumund's border war) | 8 Easy NPC refugees (follow kind) at a road; +4 per player | **Shelter**: escort them to Tempest's gate (escort) → they become `tempest_extras` residents for a week (the town grows a tent row, additive) and `counts.refugees` | **Sell them to Falmuth** (deliver to Marris, falmuth +15, tempest −15, `dark_deed`) or **raise them** (necromancer, 8 ash-grade legionnaires, the full price ×8), or **recruit them** into your nation as settlers (grey: nation value +8 for a month) | Escort, diplomacy, necromancy, nations | good: tempest +10, merit ×3 on the tent row, light +1; grey: nation value; dark: chaos +8, tempest −20, sense +12, holy_church −10 |
| 4.8 | **The haunted battlefield** (Orc War marsh, Lake Siss, or any `firsts` arena) | 12 hostile `tensura:skeleton`/`zombie` tagged `ttl.scene.restless` rising at night, a "wailing" sound; +4 per player | **Lay to rest**: kill them *and* `/ttl necro rest` / Iron's `cleanse` at the three `ttl:grave_marker` blocks (Keeper road: necromancers of the grey road are the *best* at this) | **Harvest**: bind them instead — `create_greater_undead` over the markers raises them as **yours** (8 at once, no ash, "Soul Harvest"), or an absorber eats the "soul remnants" (`ttl:soul_remnant` drops) for EP | Necromancy (both roads), holy magic, combat | good: holy_church +8, tempest +4, light +1, licence progress; dark: chaos +6, sense +15, `dark_deed` ×2, "The dead of <battle> march again" |
| 4.9 | **The dragon egg** (M, E or the Dragon's Nest build) | a `ttl:dragon_egg_cradle` block (a vanilla dragon egg on a nest) guarded by 2 `tensura:hover_lizard`; a Blumund scholar NPC wants it | **Return / entrust**: carry it to Treyni (light: the egg stays wild, `flags.egg_spared`, treyni line) or to the scholar (grey: 10 gold, blumund +5) | **Hatch it for yourself**: the Research Bench "incubate" (artificer, 3 days of engine-covered chunk) → a named `tensura:dragon_peacock`? — no: hatching needs an entity: use `tensura:feathered_serpent` as the "wyrmling" (**verify** it is tamable) — fast, a flying subordinate; **or** sell it to the Outcasts (dark, 30 gold, outcast +15) | Artifice (incubation), diplomacy, trade | good: treyni/blumund +; grey: coins; dark: chaos +3, `dark_deed`, Dragon's Nest mood −1 (a later dragon story reads `counts.eggs_taken`) |
| 4.10 | **The captured slime** | a caged `tensura:slime` (iron bars box) with a Falmuth knight camp (4) selling it "for the arena" | **Free it**: break the cage after clearing or paying 2 gold; the slime follows you (temporary owner) and may be named (a canon nod: a slime is always offered at rebirth) | **Buy it for parts**: kill it for 4 `slime core`-grade drops (Tensura's own slime items) ×4 — or feed it to an absorber (EP) | Diplomacy, combat, naming, absorbers | good: tempest +6, light +0.5, "the slime of <region>" (counts.slimes_freed); dark: chaos +2, tempest −6 |
| 4.11 | **The debt collector** | an Easy NPC collector with 2 guards at a player nation's border or a Blumund farm: a villager owes 8 gold | **Pay or mediate**: pay the debt (sink), or win a `deliver` of the farmer's harvest to the collector within 20 min (grey) | **Kill the collector** (blumund −20, ash ×3; the debt is "forgotten" and the farmer is yours: +1 radiant favour with the Outcasts) or **buy the debt** and enslave the farmer as a Workshop hand (artificer: a worker NPC for your claim, +5 % commission speed, `dark_deed`) | Coins, combat, necromancy, artifice | good: blumund +6, renown +2; dark: chaos +6, blumund −20, sense +3, renown −6 |
| 4.12 | **The collapsed mine** (artificer-first) | a dwarf outpost with 4 `tensura:dwarf` trapped behind 20 `ttl:rubble` blocks (slow to mine; 2 air left: a 15-min timer) | **Dig them out**: pickaxes, or an artificer's Create drill/`spectral_hammer` scroll, or a Marid miner spirit → dwargon +10, artifice +5 | **Let the mine keep them**: wait out the timer and loot the sealed stores (3 magisteel ingots + a schematic), or raise the dead dwarves (4 ash) | Artifice (Create/Iron's/Occultism), mining, necromancy | good: dwargon +10, `firsts.mine_rescue`; dark: chaos +6, dwargon −25, sense +6, `dark_deed` ×2 |

Common machinery (`events/choices.js`, kinds in `events/choice_kinds.js`): a scene is a `[[choice]]` row with `spawn` (entities,
blocks, NPC kinds), `routes` (each: `detect` = a condition the resolver polls every 100 ticks — kills, heals (`EntityEvents.hurt`
inverse: a `LivingHealEvent` via NativeEvents, **verify**), block placed, item handed in, undead owner change, naming event,
delivery — and `pay` = the costs/rewards table), `scale`, `ttl_minutes`, `neutral` (what happens when nobody acts), `boards`
(which radiant boards may offer it and with which weights from the chronicle view: a dark tide shows more hostages and harvests,
a light tide more refugees and eggs). The **witness** rule (R14) reads players/NPCs within 32 blocks when a dark route resolves.
A scene is removed like a boss instance (`idle_minutes`), its tag `ttl.scene.<id>` cleans up every spawned entity.

Chronicle: `counts.choices = { good, grey, dark, unresolved }`, `counts.choices_by = { sick_village = {good, dark}, … }`,
milestones `first_harvest` (first Soul Harvest: unlocks `holy_hunt` whatever the act), `village_saved_x5` (five healed villages:
mood `{ blumund = +1 }`, unlock `plague_doctor` title), `famine_fed_x10` (the Horde remembers: orc_horde mood +1), balance weights
`choice_good = +1`, `choice_dark = −1.5` (the shortcut costs more than a routine deed because it is a *choice*).

Life 1 never sees a scene (the director only picks Life 2 players on the continent); outside the ring there are no scenes (R11),
but a board may *send* a soul outside for a `collect`/`kill` radiant as today.

---

## 5. How both paths plug in

| System | Necromancer | Artificer | Choice events |
| --- | --- | --- | --- |
| **Registry** (`registry.js`) | no uniques granted; `commander`/`merciless` stay registry-capped; the Overlord title is a title, never a skill. Rank 4 adds `necro_dark` to the Act VII **dark pool weighting**? — no: the pools are fixed (O6). Nothing. | `godly_craftsman`/`researcher` as today; the Grand Artificer era title may roll a craft unique like Grand Architect (plan §13) through `TtlRegistry.draw({craft: true})` if a slot is free — one line | none |
| **Karma** (`karma/`) | `chaos` raw for dark acts (R13) — Life 2 karma is the **next** life's seed: `karma.js` must keep scoring in Life 2 (**verify** it only runs in Life 1 today; if so, WP-N1 adds a Life 2 ledger `ttl.karma2.*` read by the next judgement at ×0.5) | same | same |
| **Factions** (`rep/`) | Church seeds/sense/hunt/licence (§2.5); guards vs legions; `mood` by milestones | Dwargon/Tempest rep from commissions; stolen schematics | per route |
| **Nations** (`nations/`) | legion in `muster` (named, loaded); the tomb as a `raid_objective`; the Hunt never breaks claims | constructs in `muster`; `infra.js` upkeep discount/value; Wardens | refugees as settlers (value) |
| **Economy** (`economy/`) | sinks: rings, ash/dust (no coin value), tomb fees; faucet: Crypt board radiants | sinks: fees, rings, chisel; faucet: commissions (replace bounties) | sinks (pay routes), faucets (loot) at the guild's scale |
| **Bosses** (`bosses/`) | T3 proxies Alberto / the Dead King; the Hunt's Hinata instance at the tomb; legion vs boss = owner credit (`boss.js finish` already credits hits by subordinates? **verify** `source.actual`; else one line) | Warden counts as a contributor for its owner | scene captains are not bosses (no stage) |
| **Arenas** (`arena/`) | match type `legion`, tomb challenges | constructs in `legion` matches | — |
| **Quests** | ch. 16 tutorial (`system = "necro"`, optional, no story gate) | ch. 17 "Kaijin's Apprentice" tutorial (`system = "artifice"`) | radiant only |
| **Discord** (`discord/`) | first dark act per soul, Overlord rank, Great Tomb, Hunt start/end | Grand Artificer, first metal, Warden | milestones + per-event first lines; the Hall gets "Tombs", "Workshops", "Choices this week" (good/dark counts) |
| **Chronicle** (`world/chronicle.js`) | `counts.necro = {rites, overlords, tombs, dark_acts, rests}`, `firsts.overlord`, milestones `necromancer_rises`, `great_tomb` | `counts.artifice = {charters, masters, engines, wardens}`, `firsts.craft.<metal>`, milestone `first_warden` | §4 |
| **World-state tides** | dark acts weigh −1 each (capped −5/day/soul) | engines/public works +0.5 each | choice weights above |
| **Era** | tomb rings persist; "Overlord of the Era" = most legion boss kills; the Hunt counters reset | "Grand Artificer of the Era" | counts reset, firsts persist |

---

## 6. Balance and server load

| Risk | Rule |
| --- | --- |
| Entity count | legion awake cap 2/4/6/8 by rank (10 in a muster for 24 h), constructs 1–4 (6 muster); dormant are NBT/items, never entities; **server cap** `necro.toml [legion] server_cap = 60` awake undead + 30 constructs: above it `raise/rouse` queue with an ETA (R8: capacity, not availability). Tensura's own 300-s summons and Iron's timed summons are not counted (they expire) |
| Chunk loading | nothing of ours force-loads. A tomb unloads with its chunks; a muster counts loaded entities only; Wardens hold a zone only while loaded. (FTB Chunks force-loading stays the nation's own allowance.) |
| Despawn | every legionnaire and construct is `PersistenceRequired`; a legionnaire whose owner is offline > 7 days is **stowed** by the sweep (NBT into the record, entity discarded) — the undead wait in the crypt; constructs become items in the Workshop Bench's chest. Scene entities despawn with the scene (`ttl.scene.<id>` tag sweep) |
| Anti-farm | ash/dust never from spawner mobs, bots, or the same `kind` beyond `kill_cap` (karma's diminishing table); weekly point caps 60; a scene's rewards use the guild's `repeat_mult = 0.5` inside 7 days for the same soul and event; ash from player kills only in arenas/wars (there is no other PvP) and only once per victim per 24 h (`ttl.ash.victims`); `rest`/`heal` detection requires the scene's own tagged targets |
| Dupes | stow/rouse is atomic on the record (`dormant: true` written before `discard`, `rouse` refuses a non-dormant entry); a construct's item is Tensura's own drop |
| Lag of fear/haki | `mortal_fear` is Tensura's; our aura hall adds nothing per tick except the boss-bar presence check every 40 ticks |
| PvP leaks | legion damage to players resolves to the owner in `pvp.js` (one line) — cancelled outside the scope; subordinates cannot be used to kill in towns |
| Church hunts griefing a tomb | the Hunt instance spawns at the tomb door, never inside; claims untouched (wars are for people and thrones) |
| Overlord snowball | rank 4 needs `wight_king`/`vampire`/`mortal_fear` (EP 200,000) — Tensura's curve; the Ten and absorption remain the only Legendary routes; Death Knights die for good (no re-raise of a knight: the record marks `fallen`, a new corpse is needed) |

---

## 7. Data and storage keys

| Where | Key | Holds | Written by |
| --- | --- | --- | --- |
| Player | `ttl.necro` (JSON `{rank, points, week, wk, sense, senseAt, licensed, sanctum: {x,y,z,dim,ring,name}, legion: [{uuid, kind, name, raisedAt, dormant, nbt?, knight, fallen}]}`) | the necromancer | `necro/necro.js` |
| Player | `ttl.artifice` (JSON `{rank, points, week, wk, workshop: {x,y,z,dim}, constructs: [{uuid, metal, name, dormant, warden}], unlocked: [recipe ids]}`) | the artificer | `artifice/artifice.js` |
| Player | `ttl.choices` (JSON `{done: {eventId: {good, dark, grey, last}}, week}`), `ttl.ash.victims` | choice history, ash anti-farm | `events/choices.js`, `necro/legion.js` |
| Player | `ttl.karma2.chaos|order|craft|faith` | Life 2 soul karma for the next life (if `karma.js` is Life 1-only; WP-N1 decides) | `karma/karma.js` reserved line |
| Server | `ttl.necro.queue`, `ttl.artifice.firsts`, `ttl.choices.active` (`{sceneId: {event, region, x, z, started, entities, state}}`), `ttl.choices.seq` | queues, firsts, live scenes | the three systems |
| Stages | `ttl.necro.rank<n>`, `ttl.necro.marked`, `ttl.necro.licensed`, `ttl.artifice.rank<n>`, `ttl.scene.pvp.<id>` (an event side that opens PvP inside a scene, like raids) | gates for NPC conditions and quests (tutorial chapters only) | sync |
| Scoreboard | `ttl.necro`, `ttl.artifice` (rank), `ttl.army` already (+legion/constructs) | Easy NPC conditions | sync |
| Items (startup) | `ttl:soul_ash`, `ttl:bone_dust`, `ttl:grave_lantern`, `ttl:engraving_chisel`, `ttl:cursed_whetstone`, `ttl:warden_core`, `ttl:hipokute_salve`, `ttl:soul_remnant`, `ttl:offering_bowl` (block), `ttl:bone_altar` (block), `ttl:workshop_bench` (block), `ttl:grave_marker`, `ttl:cracked_dam`, `ttl:rubble`, `ttl:dragon_egg_cradle` (blocks) | `items.js` pattern (textures by `tools/gen_item_textures.py`, placeholders first) | WP-N0 |
| Data | `design/data/necro.toml`, `artifice.toml`, `choices.toml`, `nations.toml [infra]`, `factions.toml [church]`? (no: `necro.toml [church]`), `world.toml` milestones/weights, `radiant.toml` boards (crypt, kaijin, smithy, vester), `events.toml` choice rows, `arenas.toml allow_legion` | all knobs | `gen_data.py check_necro/check_artifice/check_choices` |
| Tags | `ttl.legion`, `ttl.legion.<uuid>`, `ttl.knight`, `ttl.construct`, `ttl.construct.<uuid>`, `ttl.scene`, `ttl.scene.<id>`, `ttl.scene.restless`, `ttl.wants_name`, `ttl.horde` (exists) | entity tags | — |

---

## 8. Work packages (one agent each, ≤ ~70 min, owned files only; cross-system call sites are one reserved, guarded line)

Priorities: data 200 → `necro/necro.js` 70, `necro/legion.js` 70, `artifice/artifice.js` 70, `events/choices.js` 70, commands 60.
Every package ends with `validate.py` green, `server.sh test <name>` green, no new `[ttl]` errors, a `decisions.md` row.

| # | Package | Owns | Deps | Bot test (`tests/ingame/<x>.rcon`) |
| --- | --- | --- | --- | --- |
| **Wave A** (no deps on world-state wave A, except where noted) | | | | |
| WP-N0 | **Items, blocks and tags**: every `ttl:` item/block of §7 with placeholder art, item tags, `validate.py` R12 grep (`ttl.story`/`ttl.path`/`ttl.boss` in the three system TOMLs fails) | `startup_scripts/ttl/items.js` (additive), `startup_scripts/ttl/blocks.js`, `kubejs/data/ttl/tags/`, `tools/gen_item_textures.py`, `tools/validate.py`, `tests/ingame/paths_items.rcon` | — | `give` each id to a bot → `ttl inspect` lists it; `setblock ttl:bone_altar` places; validate fails on a planted `ttl.story.act2` in `necro.toml` (unit test) |
| WP-N1 | **Two-roads core + Life 2 karma + Life 1 ban**: `TtlRoads.pay(server, player, {system, act, road, faction, witnessRadius})` applying the five costs (karma/`karma2`, chronicle `note` guarded, `TtlRep.add`, `addRenown` with the witness rule, Discord first-line), O-N1 bans, guide page "The dead and the law" | `roads/roads.js`, `roads/commands.js`, `design/data/roads.toml`, `design/data/mortal_banned.toml` (+`occultism`), `life/mortal_banned.js` (Iron's `SpellPreCastEvent` veto), `karma/karma.js` (reserved line: Life 2 ledger), `design/data/guide.toml`, `tests/ingame/roads.rcon` | — | `ttl roads pay <bot> necro ash_raise dark` → `ttl karma expect <bot> chaos2 3`, `ttl rep expect <bot> holy_church -3`; a second bot 10 blocks away → renown −1 on the first; Life 1 bot `give occultism:chalk_white` → stashed within 2 s |
| WP-N2 | **Legion**: altar block use, `raise/knight/stow/rouse/recall/stand/rest`, ash/dust drops (LootJS), caps + server cap + queue, owner set (verify), persistence, 7-day stow sweep, `TtlLegion.ownerOf` | `necro/legion.js`, `necro/commands.js` (legion subtree), `design/data/necro.toml [legion]`, `gen_data.py check_necro`, `bosses/loot.js` (reserved: ash/dust rows), `tests/ingame/legion.rcon`; reserved lines: `pvp/pvp.js` (owner resolution), `nations/nations.js muster` (count `ttl.legion`/`ttl.construct` named) | N0, N1 | bot with 4 `ttl:bone_dust` at an altar: `ttl necro raise skeleton` → `execute if entity @e[tag=ttl.legion]`, `ttl necro expect <bot> legion 1`; 5th raise at rank 1 → "cap 2"; `stow` → no entity, `expect dormant 1`; `rouse 1` → back; `ttl nation muster` after naming (`tensura edit owner … name set`) → `nation expect <bot> army 1` |
| WP-N3 | **Necromancer ranks, Rite, Church Sense, licence, hunt hooks**: `/ttl necro rite|rank|licence|status`, points + weekly cap, `sense` + Marked stage + Church bounty template + Hinata `necro_mult`, Hunt-on-a-soul, renown stage rows | `necro/necro.js`, `necro/commands.js` (rank subtree), `design/data/necro.toml [[rank]] [church]`, `design/data/factions.toml [renown] stage`, `tests/ingame/necro.rcon`; reserved lines: `bosses/wild.js` (multiplier), `events/hunt.js` or `director.js` (`fire holy_hunt <player>`), `rep/rep.js guardsHostile` (legion ≥ 3 in Blumund/Falmuth domain) | N1, N2 | `ttl necro rite` with a tome + 10 ash → `expect rank 1`; `ttl necro points add 400` + `tensura edit race … wight_king` → `expect rank 4`; `sense set 20` → `expect marked yes`, Lubelius guard bot hostile; `sense set 0` 14 d faked + Church Honored → `licence` → `expect licensed yes` |
| WP-A1 | **Artificer core**: Workshop Bench, charter, ranks/points, commissions (`made_by` stamp, verify), recipe unlocks, mithril bridge recipes, engraving chisel, cursed whetstone (dark road via `TtlRoads`) | `artifice/artifice.js`, `artifice/recipes.js`, `artifice/commands.js`, `design/data/artifice.toml`, `gen_data.py check_artifice`, `economy/recipes.js` (mithril rows), `tests/ingame/artifice.rcon`; reserved line `quests/radiant.js` (kind `collect` with `made_by`) | N0, N1, WP-W13 (radiant; stub: `/ttl artifice commission test`) | charter with 3 schematics → `expect rank 1`; craft a low magisteel sword at the bench → `commission turnin` → coins + `expect points 5`; `ttl artifice steal` inside the Dwargon domain (test hook skips the night rule) → schematic given, `rep expect dwargon -20` |
| **Wave B** | | | | |
| WP-N4 | **Tomb sanctum**: three ring blueprints + TOMLs, placement rules (claim, no domain, no water, underground), `/ttl necro sanctum place|name|ring`, visitor boss bar, engine niche check, tomb as arena kind `sanctum` + `challenge`, `arenas.toml allow_legion` + match type `legion` | `blueprints/tomb_crypt.py`, `tomb_mausoleum.py`, `tomb_great.py`, `design/builds/tomb_*.toml`, `pack/kubejs/data/ttl/structure/tomb_*.nbt`, `necro/sanctum.js`, `arena/arenas.js` (match type, cap 4 per side), `design/data/arenas.toml`, `tests/ingame/sanctum.rcon` | N2, N3, WP-W3 (domains; stub) | bot owner of a claimed chunk: `sanctum place` → `[ttl] necro: crypt placed`, `ttl necro expect <bot> ring crypt`; place inside the Tempest domain → refused; second bot `challenge` → arena pact, `pvp simulate` allowed inside the box only |
| WP-A2 | **Constructs + Warden + nation infra**: golem ownership (verify), `ttl.construct` tags/record, caps, possession shortcut costs, Warden core + zone, `nations/infra.js` (engines/wardens/warp pads/workshops → upkeep discount, value, chunk bonus) | `artifice/constructs.js`, `nations/infra.js`, `design/data/nations.toml [infra]`, `design/data/artifice.toml [construct]`, `tests/ingame/constructs.rcon`; reserved line `nations/nations.js value/upkeep` | A1, WP4 nations (exists) | bot with EP 6,000 (`tensura edit stat`) places `low_magisteel_bone_golem` → `expect constructs 1`, named → `muster` counts it; nation with 3 engines in claims → `ttl nation expect <bot> infra engines 3`, upkeep line shows −6 % |
| WP-C1 | **Choice events engine**: `[[choice]]` scenes, spawn/scale/ttl/neutral, route detection (kill, heal, place, hand-in, owner change, naming, deliver), witness rule, credit radius, cleanup, board offers (kind `choice`), chronicle counts, Discord lines; events 4.1 sick village, 4.2 hostages, 4.3 starving band, 4.4 wants a name | `events/choices.js`, `events/choice_kinds.js`, `events/choice_commands.js`, `design/data/choices.toml`, `gen_data.py check_choices`, `design/data/events.toml` (choice rows), `design/data/radiant.toml` (kind `choice`), `tests/ingame/choices.rcon`; reserved lines: `director.js` (`kind = choice` runner), `quests/radiant.js` (offer kind), `world/chronicle.js` (counts/milestones rows in `world.toml`) | N1, N2 (raise route), WP-W1 (chronicle; stub `typeof`), WP-W13 (boards; stub: `/ttl choice start <id> <x> <z>`) | `ttl choice start sick_village 300 300` → 6 tagged villagers; bot heals (test hook `ttl choice heal <bot>` ×6) → `expect scene good`, `rep expect blumund 8`; second scene, bot `ttl necro raise` on them → `expect scene dark`, legion +6, `karma expect chaos2 6`; `ttl choice start … ` with 3 bots online → counts 10 (scale) |
| **Wave C** | | | | |
| WP-N5 | **Adalmann's crypt + proxies + tutorial chapter 16**: crypt build in `tensura:labyrinth`, Adalmann NPC (teach + Crypt board), `[[boss]]` Alberto (proxy on `tensura:skeleton`) and the Dead King (`irons_spellbooks:dead_king`, lore-named), `chapter_16_gravebinder.toml` (`system = "necro"`, generator flag), story talk lines (Outcast contact, Hinata) | `design/builds/adalmann_crypt.toml` + blueprint, `life/builds.js` (dimension placement reuse), `design/data/npcs.toml`, `design/data/story.toml` (talk rows), `design/data/bosses.toml` (two rows), `design/quests/chapter_16_gravebinder.toml`, `tools/gen_quests.py` (`system` flag: no story deps allowed), `tests/ingame/crypt.rcon` | N3, WP-W2 (instancing; else today's boss.js) | `ttl cast expect adalmann found` in the labyrinth; `ttl story fight alberto` → summoned, kill → `ttl boss expect <bot> defeated alberto yes`; `gen_quests.py --check` fails on a `ttl.story.*` task planted in chapter 16 |
| WP-A3 | **Workshops + Vester + tutorial chapter 17**: Kaijin/Dwargon/Vester boards (radiant commissions templates ×12), Vester hut in the Tempest town ring (`min_phase = town`), `chapter_17_kaijins_apprentice.toml`, the Dwarven Masterwork Ring relic (Curios), contraption commission template (Create build) | `design/data/radiant.toml` (templates), `design/data/npcs.toml` (Vester, boards), `blueprints/tempest_town.py` (reserved: research hut spot, with WP-W5), `design/quests/chapter_17_kaijins_apprentice.toml`, `artifice/relics.js`, `tests/ingame/workshops.rcon` | A1, A2, WP-W13, WP-W5 (phase; else village spot) | `ttl radiant roll kaijin_forge` → 5 commissions; take + craft + turnin → points; Dwargon Exalted bot + rank 3 → ring recipe unlocked (`expect unlocked masterwork_ring yes`) |
| WP-C2 | **Choice events 4.5–4.12** (dam/golem, cursed goods, refugees, haunted battlefield, dragon egg, captured slime, debt collector, collapsed mine), the cursed-item hook, refugees as residents/settlers, `rest` markers, incubation at the Research Bench | `events/choice_kinds.js` (new kinds: repair, cleanse, escort-to, incubate), `design/data/choices.toml` rows, `artifice/research.js` (salve, uncurse, incubate), `life/tempest.js` (reserved: refugee tent row additive), `tests/ingame/choices2.rcon` | C1, A1, N2 | each event started by command resolves both roads with bots and asserts the costs table (one block per event) |
| WP-X1 | **Chronicle, Hall, Discord, docs**: `world.toml` milestones (`necromancer_rises`, `great_tomb`, `first_warden`, `first_harvest`, `village_saved_x5`, `famine_fed_x10`), balance weights, Hall sections "Tombs / Workshops / Choices this week", era titles (Overlord / Grand Artificer of the Era), `master-plan.md` divergence notes (§6 armies, §10, §11 relics, §13 merit), `decisions.md` rows, `roadmap.md`, `docs/discord-guides.md`, `#patch-notes` draft | those files, `discord/hall.js`, `era/era.js` (titles) | N3, A2, C1, WP-W1, WP-W10 | `ttl world milestone fire necromancer_rises` → stage on a bot, mood line; `ttl world export` shows `counts.necro`, `counts.artifice`, `counts.choices` |

Waves: **A** WP-N0 WP-N1 WP-N2 WP-N3 WP-A1 → **B** WP-N4 WP-A2 WP-C1 → **C** WP-N5 WP-A3 WP-C2 WP-X1. Wave A has no
dependency on `world-state.md`'s packages (every chronicle/radiant call is a `typeof`-guarded reserved line); B and C prefer
WP-W1/W3/W13 merged but run with stubs.

Verify-in-game list (owned by the package named): `tensura:skeleton`/`zombie` accept a permanent owner and the subordinate
order UI (N2); `#tensura:can_be_named` contents (N2, A2); whether `UndeadHumanoidEntity` burns in sunlight (N2); `BoneGolemEntity`
owner on item placement and what daemon possession does to it (A2); Tensura smithing recipes consume the schematic (A1);
`ItemEvents.crafted` for the Smithing Bench (A1); `SpellPreCastEvent` from KubeJS NativeEvents (N1); `LivingHealEvent` for the
heal route (C1); `tensura:feathered_serpent` tamable (C2); Hinata wild multiplier line (N3); `boss.js finish` credits
subordinate hits to the owner (N2); FTB `protectSubordinates` during our war flag (N2).

---

## 9. Mod additions to evaluate (NeoForge 1.21.1 builds only; the never-add list of CLAUDE.md rule 6 stands)

| Candidate | Why | How |
| --- | --- | --- |
| **Create: New Age** | the master plan's magic-science tier (electricity, generators, reactor) = the only real "magicule-powered Create" story; also the artificer's rank 3–4 content | `/add-mod` check for a NeoForge 1.21.1 build; soak on staging; if none exists, drop the bridge idea for this era |
| **Create: Occult Engineering** | Occultism ↔ Create bridge (spirits running machines) | same |
| **Tensura: Unique Races / TR Addon / Mysticism** (plan Q10) | more undead/skeleton race options and golem variants, *if* they ship them | check their race ids with `/dump-ids` first; nothing in this design needs them |
| A dragon mod (Wenti, the dragon egg's hatchling) | §2.7, §4.9 | later era only; Ice and Fire CE is already "Phase 3 optional, heavy" |
| **Not needed**: a necromancy mod (Tensura + Iron's + Occultism cover it), a golem mod (bone golems exist), a "Recipe Stages" mod (gates are schematics/commissions), LuckPerms (breaks `/ttlbot`), a second claims/nations/minimap mod | — | — |

---

## 10. Owner decisions (recommendation first)

| # | Question | Recommendation |
| --- | --- | --- |
| O-N1 | Life 1 and the necromancy tools of Iron's/Occultism (§0.2) | **Ban Occultism by namespace; veto Iron's blood + eldritch casts in the Mortal dimensions** (fallback: ban `irons_spellbooks` entirely, the plan's Q13) |
| O-N2 | Sanctum: a build on your own claim (recommended) or a shared/personal dimension | **Build** (§2.4): no Java, no chunk cost, the Church can find it, claims protect it |
| O-N3 | Legion caps 2/4/6/8 (10 mustered), server cap 60 awake undead + 30 constructs | **These starting values**; tune after the first war |
| O-N4 | Soul ash from player kills: arenas and wars only, once per victim per 24 h | **Yes** (there is no other PvP; a duel loser feeding a Death Knight is the Overlord story) |
| O-N5 | The Church's Sense thresholds (Marked 20, Hunt 50, decay 5/week) and the grey licence (Honored + 14 clean days) | **As written**; the licence is what lets a light soul be a necromancer without the Church at the door |
| O-N6 | Death Knights only from corpses you made (ash) or 32 dust; max 1/2 | **Yes**; no re-raising a fallen knight |
| O-A1 | Nation upkeep discount per magic engine 2 %, cap 20 %; value per engine 5, per workshop 10; warp network +1 chunk | **Yes** (the owner's "upkeep reduction?" → yes, capped so engines do not replace the treasury) |
| O-A2 | Material gating by schematic drops/commissions (T2 adamantite, T3 hihi'irokane), not by recipe removal | **Schematics**: Tensura already consumes them (verify), nothing to remove |
| O-A3 | Daemon-possessed golems count as named at once, with the five costs; a dead possessed golem frees a hostile daemon | **Yes** |
| O-A4 | Create magicule bridge: evaluate Create: New Age / Occult Engineering now, or defer to era 2 | **Evaluate now, add only with a verified NeoForge 1.21.1 build**; the design works without it |
| O-C1 | Choice events: 3 active server-wide, 30-min TTL with a *neutral* resolution, first-come per scene, credit within 48 blocks | **As written** |
| O-C2 | Choice balance weights `choice_good +1`, `choice_dark −1.5`; dark acts capped at −5/day/soul in the tide | **As written** (a shortcut costs more than a routine deed; the cap stops one soul from flipping the tide alone) |
| O-C3 | Which of the named future systems (§0.1) next: Priest/Exorcist (the necromancer's mirror, cheapest: the Church already exists), Beast-tamer, Summoner, Merchant | **Priest/Exorcist** next, then Beast-tamer (naming and the war muster already reward it) |
| O-C4 | Chapters 16 and 17 as optional tutorial chapters (`system = "<id>"`, no story gates), or no chapters at all (boards + guide pages only) | **Tutorial chapters**, 10 quests each, so the quest book shows the systems exist; R12 enforced by the generator |

---

## 11. References (always "our interpretation" in player-facing text where the source is read loosely)

- **Overlord** (Kugane Maruyama, light novel vol. 1 "The Undead King", vol. 2 "The Dark Warrior"; anime S1 ep. 1–4): Ainz Ooal
  Gown as an Overlord (undead race), the Great Tomb of Nazarick as a place in the world, the Death Knight created from a corpse at
  Carne Village, Create Undead / Create Greater Undead (the very names Tensura uses for its necromancy magic), Despair Aura, the
  undead who neither tire nor fear. Used for tone and for the legion/tomb/aura shape — never for names in game.
- **Tensura — That Time I Got Reincarnated as a Slime** (Fuse): Adalmann the Wight King, Alberto the Death Knight and Wenti (LN
  vol. 10–11; anime season 3, the Tempest Labyrinth episodes — episode numbers to **verify** against the Wikipedia episode list
  already cited in `quests.md`); Hinata's Holy Knights and the Western Holy Church's war on monsters (LN vol. 5–7); Luminous
  Valentine, the vampire god of the Church (LN vol. 7); Kaijin, Kurobe, Garm, Dold, Mildo and the Armed Nation of Dwargon (LN
  vol. 1–2; anime ep. 5–6); Vester's fall and his research department (LN vol. 2, 4+); the Orc Lord's famine (LN vol. 2; anime
  S1, the Orc War episodes); naming as EP investment and the master-subordinate bond (LN vol. 1, Rimuru naming the goblins);
  Tempest's magic engines/magisteel economy as the Jura-Tempest Federation industrialises (LN vol. 4–8, *our reading*).
- **Mods** (ids verified 18/11/2026): Tensura: Reincarnated 2.0.1.5 (`race/wight`, `necromancy_magic`, `mortal_fear`, bone golems,
  magic engines, smithing/kiln/refining, naming/owner commands, FTB compat), Not Enough Bosses 2.0.0.3, Tensura Compat: Iron's
  2.0.0.0 (`manaConversionMultiplier = 50`, `spellDamageMultiplier = 10`, entity/gear existence tables), Iron's Spells 'n Spellbooks
  3.16.3 (blood school, Arcane Anvil, Inscription Table, Scroll Forge, the Dead King), Occultism 1.227.0 (rituals, familiars,
  worker spirits, dimensional storage), Create 6.0.10 (no magicule bridge), Corail Tombstone 9.5.6 (familiar receptacle, gated by
  `bosses.toml [tombstone]`).

---
**Owner decisions 18/11/2026 (Yasuke):** all O-N/O-A/O-C recommendations accepted, EXCEPT:
- **O-N2 changed:** the necromancer's tomb sanctum is NOT a pre-generated/placed build. Players build it themselves.
  The system recognises a sanctum from a core block (the Bone Altar) plus build criteria (enclosed volume, required
  blocks/features per tier) and grows Crypt → Mausoleum → Great Tomb from what the player builds. No ring blueprints.
- **Discoverability (new rule):** every path and system must be easy to find in game — guide pages, roadmap entries,
  NPCs/boards that point to it, and a short optional intro quest per path (`system = "<id>"`, never story-gated).
- `tensura:boss_area` stays Tensura's own pre-generated boss area (normal mod behaviour, outside the story rules).
- Eurazania becomes a faction (W3).
