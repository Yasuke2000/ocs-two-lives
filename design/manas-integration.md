` marker verbatim to
`C:\Users\david\Documents\ocs-two-lives\design\manas-integration.md` (no other file touched, no commit).

Evidence base: jars in `PrismLauncher/instances/OCs/minecraft/mods`, extracted to
`<scratchpad>/mr/` (short dir names because of Windows MAX_PATH: `mc_n/<module>` = ManasCore
nested modules, `ts` = Tensura, `gs` = Great Sage, `ftb`, `iss`, `neb`, `tmc`, `kjs`), read with
`javap -p -c -v` and constant-pool string dumps.

=== BEGIN FILE ===

# ManasCore / Tensura integration guide (OCS Tensura: Two Lives)

Research date 17/11/2026. Read-only analysis of the jar files in the OCs Prism instance:
`manascore-neoforge-4.0.0.2` (nested modules), `tensura-neoforge-2.0.1.5`, `greatsage-0.0.7.1`,
`tensura_ftb-neoforge-2.0.0.4`, `tensura_iron_spells-neoforge-2.0.0.0`, `tensura_neb-neoforge-2.0.0.3`,
`tensuramoreconfigs-0.0.2`, `kubejs-neoforge-2101.7.2-build.381`, `rhino-2101.2.7-build.85`,
`architectury-13.0.12`. Every statement names the class or file it came from. Anything not
confirmed in bytecode is marked **unverified**. Re-check after any version bump.

Conventions: `ms.` = `io.github.manasmods.manascore.`, `ts.` = `io.github.manasmods.tensura.`,
`gs.` = `dev.dedek.greatsage.`.

---

## 0. TL;DR

- All ManasCore and Tensura hooks are **Architectury `Event`s** (`dev.architectury.event.Event<T>`:
  `register`, `unregister`, `isRegistered`, `clearListeners`, `invoker`). None are posted on the NeoForge
  bus, so KubeJS `NativeEvents` cannot see them. Java: `SkillEvents.UNLOCK_SKILL.register(...)`.
  KubeJS: reachable through `Java.loadClass` (no class-filter block), with caveats (section 4).
- "Pre" events, cancellable: `UNLOCK_SKILL`, `REMOVE_SKILL`, `SET_RACE`, `AWAKENING_EVENT`,
  `NAMING_EVENT`, `SKILL_PLUNDER`. Returning `EventResult.interruptFalse()` vetoes. Other listeners
  (Tensura's own) can still cancel after yours, so do bookkeeping one tick later from storage.
- **Legendary leak found:** the Great Sage reincarnation scene grants up to 3 skills
  (`gs.server.ReincarnationGrants.apply`) **without checking `noUniqueStart`**, inside the very
  `ReincarnationMenu` that `ttl-portals` opens for the Life 2 rebirth. Its "wish" button calls
  Tensura's `ReincarnationMenu.randomUniqueSkill`, which draws from `startingSkills`. The pack's
  `startingSkills` currently **contains all 9 Legendaries**. Section 5 lists every leak path and the fix.
- Cleanest choke point: one `SkillEvents.UNLOCK_SKILL` veto listener (Java, in `ttl-portals`, needs the
  rule-5 approval) that refuses any `tensura:unique_skills`/Legendary grant the registry did not authorise,
  plus a reconcile pass that reads `SkillAPI.getSkillsFrom(player).getLearnedSkills()`.

---

## 1. ManasCore public API (per module)

ManasCore 4.0.0.2 is a shell jar (`io.github.manasmods.manascore.ManasCore` only) with nested jars in
`META-INF/jars/`: `manascore-{architectury,attribute,command,config,inventory,keybind,network,race,skill,storage}-neoforge-4.0.0.2.jar`.
Registry ids (from `ms.skill.impl.SkillRegistry`, `ms.race.impl.RaceRegistry`): skills
`manascore_skill:skills`, races `manascore_race:races`. Storage keys: `skills` (`SkillStorage`),
`race_key` (`RaceStorage`).

### 1.1 Skill module (`ms.skill.api`)

| Class | Member | Notes |
| --- | --- | --- |
| `SkillAPI` | `static Registrar<ManasSkill> getSkillRegistry()` | Architectury `Registrar`; `.get(ResourceLocation)`, `.getId(skill)`, `.getIds()` |
| | `static ResourceKey<Registry<ManasSkill>> getSkillRegistryKey()` | |
| | `static SkillStorage getSkillsFrom(LivingEntity)` | `ms.skill.impl.SkillStorage implements Skills` |
| | `skillActivationPacket / skillReleasePacket / skillTogglePacket` | client to server only |
| `Skills` (interface) | `Collection<ManasSkillInstance> getLearnedSkills()` | read path for the registry |
| | `Optional<ManasSkillInstance> getSkill(ResourceLocation \| ManasSkill)` | |
| | `boolean learnSkill(ResourceLocation \| ManasSkill \| ManasSkillInstance [, MutableComponent msg])` | fires `UNLOCK_SKILL` |
| | `void forgetSkill(ResourceLocation \| ManasSkill \| ManasSkillInstance [, MutableComponent msg])` | fires `REMOVE_SKILL` |
| | `void updateSkill(ManasSkillInstance, boolean sync)` | **no event**: puts the instance straight in the map |
| | `forEachSkill(BiConsumer<SkillStorage, ManasSkillInstance>)`, `markDirty()` | |
| `ManasSkillInstance` | `getSkill()`, `getSkillId()`, `getMastery()`, `setMastery(double)`, `getMaxMastery()`, `isMastered(LivingEntity)`, `addMasteryPoint(..)` | negative mastery = still being learned (section 2.6) |
| | `isTemporarySkill()`, `getRemoveTime()`, `setRemoveTime(int)` | temporary skills auto-forget (`SkillStorage.checkSkillTimers`) |
| | `getTag()/getOrCreateTag()/setTag(CompoundTag)` | per-skill NBT (e.g. Tensura's `NoMagiculeCost`, `CreatedSkill`) |
| | `is(TagKey<ManasSkill>)`, `isToggled()`, `getCooldown(int)`, `getSubInstances()` | |
| `ManasSkill` | `getRegistryName()`, `getName()`, `getMaxMastery()`, `onLearnSkill/onForgetSkill/onSkillMastered(..)` | base class of every skill |

Bytecode of `SkillStorage.learnSkill(ManasSkillInstance, MutableComponent)`: returns false if the id is
already present; otherwise fires `UNLOCK_SKILL`; if the result `isFalse()` it aborts; else puts the
instance, sends the message, calls `onLearnSkill`, marks dirty.
`SkillStorage.forgetSkill(ResourceLocation, MutableComponent)`: fires `REMOVE_SKILL`; if `isFalse()`
it aborts; else `onForgetSkill`, removes, marks dirty.

### 1.2 Skill events (`ms.skill.api.SkillEvents`, all `dev.architectury.event.Event`)

| Field | Callback signature | Cancellable / meaning |
| --- | --- | --- |
| `UNLOCK_SKILL` | `EventResult unlockSkill(ManasSkillInstance, LivingEntity, Changeable<MutableComponent> msg)` | yes, before insert. Also fired by `ts.ability.SkillHelper.learnSkill` when re-learning an existing skill |
| `REMOVE_SKILL` | `EventResult removeSkill(ManasSkillInstance, LivingEntity, Changeable<MutableComponent>)` | yes, before removal |
| `SKILL_MASTERY` | `EventResult master(ManasSkillInstance, LivingEntity, Changeable<Double> points)` | yes |
| `ACTIVATE_SKILL` / `RELEASE_SKILL` / `TOGGLE_SKILL` / `SKILL_SCROLL` | `(Changeable<ManasSkillInstance>, LivingEntity, ...)` | yes |
| `SKILL_PRE_TICK` / `SKILL_POST_TICK` / `SKILL_UPDATE_COOLDOWN` | tick hooks | |
| `SKILL_DAMAGE_PRE_CALCULATION` / `_CALCULATION` / `_POST_CALCULATION` | damage hooks | |
| `POST_INIT` | `Runnable` | after registration |
| `SKILL_SCROLL_CLIENT` | client only | |

Also `ms.skill.api.EntityEvents` (`LivingChangeTarget`, `LivingDamage`, `LivingEffectAdded`,
`LivingHurt`, `LivingTick`, `ProjectileHit`); `ms.skill.neoforge.NeoForgeCommonEventInvoker` bridges
NeoForge events into these (one-way, nothing is posted back to the NeoForge bus).

### 1.3 Race module (`ms.race.api`)

| Class | Member | Notes |
| --- | --- | --- |
| `RaceAPI` | `getRaceRegistry()`, `getRaceRegistryKey()`, `Races getRaceFrom(LivingEntity)`, `raceEvolutionPacket(ResourceLocation)` | `ttl-portals` already uses `getRaceRegistry` / `getRaceFrom` |
| `Races` | `Optional<ManasRaceInstance> getRace()` | empty = no race yet (used by `Rebirth.blockFirstLogin`) |
| | `setRace(ResourceLocation \| ManasRace \| ManasRaceInstance, boolean evolution [, boolean teleport], [MutableComponent])` | concrete: `RaceStorage.setRace(instance, evolution, teleportToSpawn, msg)` |
| | `evolveRace(...)` | `= setRace(instance, true, false, msg)` (`Races.evolveRace` bytecode) |
| `ManasRaceInstance` | `getRace()`, `getRaceId()`, `getTag()`, `getIntrinsicSkills(LivingEntity)`, `isIntrinsicSkill(..)`, `add/removeIntrinsicSkill(ManasSkill)` | |
| `ManasRace` | `getNextEvolutions(..)`, `getPreviousEvolutions(..)`, `getDefaultEvolution(..)`, `getEvolutionProgress(..)`, `getIntrinsicSkills(..)`, `getDifficulty()` | |

`RaceEvents` (`ms.race.api.RaceEvents`):

| Field | Signature | Notes |
| --- | --- | --- |
| `SET_RACE` | `EventResult set(ManasRaceInstance previous /*nullable*/, LivingEntity, ManasRaceInstance next, boolean isEvolution, Changeable<Boolean> teleportToSpawn, Changeable<MutableComponent> msg)` | fired first in `RaceStorage.setRace`; `isFalse()` aborts. After it: attribute swap, `onRaceEvolution` (if evolution), `onRaceSet`, `learnIntrinsicSkills` (each fires `UNLOCK_SKILL`), optional `SpawnPointHelper.teleportToNewSpawn` |
| `RACE_PRE_TICK`, `RACE_POST_TICK`, `RACE_UPDATE_COOLDOWN`, `ACTIVATE_ABILITY`, `RELEASE_ABILITY`, `POST_INIT` | | |

### 1.4 Storage module (`ms.storage.api`)

`Storage` (abstract: `save/load(CompoundTag)`, `markDirty()`), `StorageHolder` (mixed into Entity, LevelChunk,
Level: `manasCore$getStorage(StorageKey)`, `manasCore$sync()`), `StorageKey<T>(ResourceLocation id, Class<T>)`,
`StorageType {ENTITY, CHUNK, WORLD}`, `StorageEvents.REGISTER_ENTITY_STORAGE / REGISTER_CHUNK_STORAGE / REGISTER_WORLD_STORAGE`
(`register(StorageRegistry)` -> `registry.register(id, Class, Predicate, factory)`). A Java mod can attach its
own synced per-player storage this way; the pack does not need to (persistentData is enough).

### 1.5 Other modules

- `ms.network.api.util.Changeable<T>`: `of(T)`, `get()`, `set(T)`, `isPresent()`. Every mutable event argument.
- `ms.command.api`: annotation command framework (`@Command(value, subCommands)`, `@Execute`, `@Permission(value, permissionLevel)`,
  parameter annotations `@SenderArg`, `@EntityArg`, `@LiteralArg`, `@IntegerArg`, ...). `Permission$PermissionLevel`:
  `OWNER`=4, `ADMIN`=3, `GAMEMASTER`=2 (bytecode); `MODERATOR`=1 and `PLAYER`=0 by position (**unverified** values).
- `ms.config.api.ManasConfig` / `ManasSubConfig`: TOML configs with public fields (used by `ReincarnationConfig`).
- `ms.attribute.api.AttributeEvents` (`CriticalAttackChanceEvent`, `GlideEvent`), `ms.inventory.api` (inventory tabs), keybind: not relevant.

---

## 2. Tensura: Reincarnated 2.0.1.5 hooks

### 2.1 Game rules (`ts.world.TensuraGameRules`; defaults from `init()` bytecode, text from `assets/tensura/lang/en_us.json`)

| Rule | Type, default | Meaning |
| --- | --- | --- |
| `noUniqueStart` | bool, false | No unique at (re)birth; MP/AP buff instead (`ReincarnationMenu.grantUniqueSkill`). Pack: true |
| `trulyUnique` | bool, false | Removes owned uniques from the reincarnation pool (`ITrulyUnique` world map). Pack: false |
| `skillBeforeRace` | bool, false | Unique granted before race choice (first login sets Human and grants) |
| `rimuruMode` | bool, false | First login reincarnates as Rimuru (`reincarnateAsRimuru`) |
| `hardcoreRace` | bool, false | Some races harder |
| `mpSkillCost` | int, 100 | % of acquiring MP cost charged on learning a skill; also scales the noUniqueStart buff |
| `skillGriefing` | bool, true | Abilities may grief blocks |
| `skillSteal` | bool, true | Certain skills steal (instead of copy) skills from players |
| `epSteal` | bool, false | Skills may steal EP/MP/AP from players |
| `playerMindControl` | bool, true | Mind control works on players |
| `disableNullification` | bool, false | Disables Nullification |
| `maximumMagicExplosion` | int, 100 | Max magic explosion grief radius |
| `maxMpGain` / `maxApGain` | int, 1000000000 | Max MP/AP gained per kill |
| `epGainMultiplier` | int, 1 | EP gain multiplier on kills |
| `playerEP` / `vanillaEP` / `tensuraEP` / `moddedEP` | int, 100 | % of default EP that killed players / vanilla / Tensura / modded mobs count for |
| `spawnerEP` | int, 10 | % EP for spawner mobs |
| `epDeathPenalty` | int, 5 | % EP lost on respawn (`ts.handler.DeathHandler`) |
| `disableDaemonAutoMagic` | bool, false | Daemons stop auto-learning Aspectual magic |
| `disableSpiritualLimit` | bool, false | Removes EP limit for spiritual players in the physical world |
| `tensuraDisplayName` | bool, false | Show Tensura name instead of MC name when named |
| `playerNaming` | bool, true | Players can be named by others |
| `playerSummoning` | bool, true | Players can be summoned |
| `playerManualDodging` | bool, false | Keybind dodge (experimental) |
| `demonLordSeed` | int, 200000 | EP needed to become a Demon Lord Seed |
| `demonLordAwaken` | int, 10000 | Soul points for True Demon Lord |
| `forceHarvestFestival` | int, 20000 | Souls that force the Harvest Festival |
| `labyrinthPvp` | bool, true | PvP in the Labyrinth |
| `labyrinthDeath` | bool, false | Real death in the Labyrinth (else 1 HP + teleport out) |
| `npcGrief` / `npcWorking` | bool, true | NPC griefing / professions |
| `colossusRespawn` | bool, false | Respawn Elemental Colossus for new challengers |
| `resetCounterBonusUnique` | int, 0 | Extra uniques on reset per Reset Counter |
| `resetIncompletePenalty` | int, 0 | Reset Counter points lost on an incomplete reset |
| `resetPerSkillLock` | int, 0 | Reset Counter points per Unique skill lock |

Helpers: `canStealSkill(Level)`, `canEpSteal(Level)`, `noPlayerMindControl(Level)`, `canSkillGrief(Level)`, `isLabyrinthPvpOff(..)`.

### 2.2 Tensura events (all Architectury `Event`, public static fields)

`ts.event.TensuraEntityEvents`:

| Field | Signature | Fired from / notes |
| --- | --- | --- |
| `AWAKENING_EVENT` | `EventResult awaken(LivingEntity, Changeable<Boolean> isHero)` | `ts.race.RaceHelper.awakening(entity, isHero)`; true = True Hero, false = True Demon Lord. Cancellable, fires before rewards. Callers: `EvolveCommand`, `ForceEvoCommand`, `RequestEvolutionPacket`, `ExistenceStorage` |
| `NAMING_EVENT` | `EventResult name(LivingEntity sub, Player owner, Changeable<Double> epGain, Changeable<Double> cost, Changeable<NamingType> type /*LOW,MEDIUM,HIGH*/, Changeable<String> name)` | `ts.network.c2s.RequestNamingMenuPacket` (names from its LocalVariableTable) |
| `ATTRIBUTE_BASE_CHANGE_EVENT` | `EventResult change(LivingEntity, AttributeInstance, double, double)` | `ts.mixin.MixinAttributeInstance`; catches max MP/AP base changes (arg order old/new **unverified**) |
| `ENERGY_DRAIN_EVENT` | `drain(LivingEntity, Entity, Changeable<DrainType>, Changeable<GainType>, Changeable<Double>, Changeable<Boolean>)` | |
| `ENTER_HARVEST_FESTIVAL_EVENT` | `enter(LivingEntity, Changeable<Integer>, Changeable<Integer>)` | |
| `HARVEST_FESTIVAL_REWARD_EVENT` | `reward(LivingEntity)` | |
| `POSSESSION_EVENT` | `possess(LivingEntity, Entity)` | |
| `POST_TAME_EVENT` | `void tame(LivingEntity, Player)` | not cancellable |
| `ENGRAVE_EVENT`, `ADD_FRESH`, `ENTER_SLEEP_MODE_EVENT`, `FORCE_MOVEMENT_EVENT`, `FORCE_TAME_EVENT`, `LIVING_POST_DAMAGE`, `SPIRITUAL_HURT_EVENT`, `EQUIPMENT_CHANGE_EVENT`, `PRE_ITEM_HURT_EVENT`, `DIMENSION_TRAVEL_EVENT`, `INSTANT_TRANSMISSION_EVENT` | | not needed by the pack |

`ts.event.TensuraSkillEvents`:

| Field | Signature | Notes |
| --- | --- | --- |
| `SKILL_PLUNDER` | `EventResult plunder(Entity, Entity, boolean, Changeable<ManasSkill>)` | fired by Predator mist (`ts.entity.magic.beam.PredatorMistProjectile`), `DrainSkill`, `PossessionSkill`, `AnalystSkill`, `ChosenOneSkill`, `DegenerateSkill`, `GluttonySkill`, `GourmetSkill`, `GreatSageSkill`, `PrideSkill`, `SeekerSkill`, `SpearheadSkill`, `StarvedSkill`. In `PredatorMistProjectile.devourProjectile` arg 1 = projectile owner (victim), arg 2 = mist owner (plunderer); meaning of the boolean **unverified** |
| `SKILL_LEARNING` | `learn(ManasSkillInstance, LivingEntity, int, double, Changeable<Double>)` | learning-progress points for skills not yet acquired |
| `ABILITY_EQUIP` | `equip(Player, Changeable<ManasSkillInstance>, Changeable<Integer> x3)` | ability-slot equip |
| `SKILL_GRIEF_PRE` / `SKILL_GRIEF_POS` | `SkillGriefEvent` | block grief by skills (FTB compat hooks PRE) |

`ts.event.TensuraSpiritEvents.SPIRIT_UPDATE` (`update(LivingEntity, Changeable<Element>, Changeable<SpiritLevel>)`),
`TensuraLevelEvents`, `TensuraInputEvents`, `TensuraLocalPlayerEvents` (client).

**No dedicated events** for: EP value changes, Demon Lord Seed / Hero Egg flags, death-reincarnation.
Great Sage's own `gs.server.AwakeningWatcher` polls `IExistence.isDemonLordSeed/isHeroEgg/isTrueDemonLord/isTrueHero`
on `PlayerTickEvent.Post`; do the same (cheap: check every 20 ticks, compare with a `ttl.*` mirror).

Tensura's own listeners (`ts.handler.AbilityHandler.init`), relevant because they run alongside yours:
- `UNLOCK_SKILL`: passes early when mastery < 0 (learning entry); otherwise fires the `ABILITY_OBTAINED`
  advancement, charges `mpSkillCost`, and **returns `interruptFalse()`** (cancels the unlock) when max MP is
  too low (`tensura.skill.acquire_failed.mp`) or for invalid Creator-created skills.
- `REMOVE_SKILL`: **cancels** removal of temporary skills that have `OldRemoval`/`OldMastery` (restores them) and
  of `learnableResistances` (resets them to learning mastery instead).
- So neither event guarantees the change happened; verify in storage next tick.

### 2.3 Storages (`ts.storage.TensuraStorages`)

| Getter | Interface | Useful fields |
| --- | --- | --- |
| `getExistenceFrom(LivingEntity)` | `ts.storage.ep.IExistence` | `getEP/setEP`, `getGainedEP`, `getMagicule/getAura`, `getSpiritualHealth`, `getSoulPoints`, `getHumanKill`, `isDemonLordSeed`, `isTrueDemonLord`, `isHeroEgg`, `isTrueHero`, `isBlessed`, `getAlignment/getOriginalAlignment` (`ts.storage.Alignment`), `getName/isNameable`, `getPermanentOwner/getTemporaryOwner`, `isSpiritualForm`, `getHarvestTick` |
| `getPlayerDataFrom(LivingEntity)` | `ts.storage.player.ITensuraPlayer` | `getTrackedEvolution()`, `getResetCounter()`, `getBonusSkillLock()`, `getInResetProgress()`, `getLockedSkills()/addLockedSkill/removeLockedSkill/clearLockedSkills`, `getReputations()/getReputation(id)`, warp points/pads, schematics |
| `getAbilityFrom(LivingEntity)` | `ts.storage.ability.IAbility` | presets and ability slots (`removeSkillFromPresets(ManasSkill)`) |
| `getUniqueStorageFrom(Level)` (overworld) | `ts.storage.unique.ITrulyUnique` | world map `getSkillMap(): Map<ResourceLocation, UUID>`, `addSkill(id, uuid)`, `removeSkill`, `removeOwner`, `hasSkill`, `getOwner`. Only filled by Tensura's reincarnation grant (`ReincarnationMenu.grantedUniqueSkill`) and `/tensura worldData trulyUnique add` |
| `getSpiritFrom`, `getEffectFrom`, `getChunkFrom`, `getLabyrinthFrom`, `getBossFightHolder`, `getWorldRestrictionFrom` | | |
| `resetExistence(entity [, bool, bool, bool])`, `resetPlayerData`, `resetSpirit`, `resetEffect` | | used by reset scrolls / reincarnation magic |

Skill helpers: `ts.ability.SkillUtils.hasSkill / hasSkillPermanently / hasSkillFully / isSkillMastered / isSkillToggled`.
`hasSkillFully` (bytecode) = instance present AND mastery >= 0 AND not temporary. Use that definition
for "holds a unique". `ts.ability.SkillHelper.learnSkill(LivingEntity, ManasSkill|ManasSkillInstance [, int, MutableComponent])`
is the Tensura grant path (handles learning state, fires `UNLOCK_SKILL`).
Skill type: `ts.ability.skill.Skill.getType()` -> `Skill$SkillType {RESISTANCE, INTRINSIC, COMMON, EXTRA, UNIQUE, ULTIMATE}`.
Tags (`ts.data.TensuraSkillTags`, files `data/tensura/tags/manascore_skill/skills/*.json`):
`UNIQUE_SKILLS` = `tensura:unique_skills` (59 entries, includes all 9 Legendaries), `NO_PLUNDERING` =
`tensura:no_plundering` (currently `law_manipulation`, `anti_skill`), `RESET_WITH_RACE`, `INTRINSIC_SKILLS`, etc.
Race tags: `data/tensura/tags/manascore_race/races/*.json` (`human_like`, `spiritual`, `undead`, `daemon`, ...).

### 2.4 Reincarnation config (`ts.config.ReincarnationConfig`, file `config/tensura/reincarnation_config.toml`)

Live instance: `ts.menu.ReincarnationMenu.CONFIG` (public static final; Great Sage mutates `Skills.skillNumber` on it at runtime, so Java can too).

| Section.field | Type | Used by |
| --- | --- | --- |
| `Races.startingRaces` / `randomRaces` | List<String> | first-login menu (`getRacePool`/`getRandomRacePool`, overridden by `ReincarnationMenuMixin` when `Rebirth` has offers) |
| `Races.reincarnationRaces` / `reincarnationRandomRaces` | | after casting Aspectual magic Reincarnation |
| `Races.reincarnationRacesMastered` / `reincarnationRandomRacesMastered` | | same, when mastered |
| `Skills.startingSkills` | List<String> | `ReincarnationMenu.getSkillPool()` -> `randomUniqueSkill` |
| `Skills.skillNumber` | int | uniques per reincarnation |
| `Skills.additionalUniqueChance` | double | chance for rolls above 1 |
| `Skills.secondSkills` | List<String> | `getSecondSkillPool()` (second roll) |
| `Skills.learnableResistances` | List<String> | `grantLearningResistance` |
| `Skills.nonPlayerResistance` | boolean | |

**Pack finding:** `pack/config/tensura/reincarnation_config.toml` `startingSkills` contains
`creator, envy, great_sage, greed, lust, predator, pride, sloth, wrath`, and `secondSkills` contains `great_sage`.

Grant flow (bytecode of `ReincarnationMenu`):
`clickMenuButton(SUBMIT)` -> static `setRace(Player, ManasRace, boolean, boolean grantUnique)` -> `Races.setRace(...)`
-> if `grantUnique`: `grantUniqueSkill(player)` -> if `noUniqueStart`: `EnergyHelper.increaseMaxEP` buff only;
else `randomUniqueSkill(player, bool)` -> `getReincarnationSkills(pool)` filters by `trulyUnique` + `hasSkillFully`
-> locked skills first, then random picks -> `grantedUniqueSkill` (`SkillHelper.learnSkill` + `ITrulyUnique.addSkill`).
`randomUniqueSkill` itself never checks `noUniqueStart`.

### 2.5 `tensura` command tree (reconstructed from `@Command`/`@Execute`/parameter annotations in `ts.command.**`)

Registered roots (`ts.command.TensuraCommands`): `/tensura`, `/ability`, `/despawn`, `/engrave`, `/evolve`, `/nameable`, `/syncStorage`.
`<e>` = entities selector, `<e1>` = single entity, `<p>` = players, `self` = literal. Permission node and level in brackets.

```
/tensura edit ability [tensura.command.edit_ability, GAMEMASTER]
  grant  <e> <skill> | <e> all [skill [<skilltype>] | magic [<magictype>] | battlewill] | <e> random [skill [<skilltype>] | magic [<magictype>] | battlewill]
  revoke <e> <skill> | <e> all [skill [<skilltype>] | magic [<magictype>] | battlewill] | <e> random [...]
  mastery <e> <skill> (<double>|max) | <e> all|random [skill [<skilltype>]|magic [<magictype>]|battlewill] (<double>|max)
  modeLearning <e> <skill> (<mode>|all) (<double>|max) | <e> all [skill|magic|battlewill ...] (<double>|max)
  toggle <e> <skill> <bool> | <e> (all|random) (everything|skill [<t>]|magic [<t>]|battlewill) <bool>
  removeTime <e> <skill> <seconds> | <e> all [skill|magic|battlewill ...] <seconds>
  cooldown <e> <skill> <seconds> <mode> | <e> all [skill|magic|battlewill ...] <seconds>
/tensura edit race <e> set <race> [<resetExistenceStats:bool>] | <e> alignment <alignment> | <e> alignment <spiritualForm:bool>   [edit_race, GAMEMASTER]
/tensura edit awakening <e> humanKill (set|add) <n> | demonLord soul (set|add) <n> | demonLord harvestFestivalTick (set|add) <n>
                        | demonLord seed <bool> | demonLord awakened <bool> | hero blessed <bool> | hero egg <bool> | hero awakened <bool>   [edit_awakening, GAMEMASTER]
/tensura edit forceevo <e> race [<triggerRewards:bool>] | <e> demonLord | <e> hero   [edit_forceevo, GAMEMASTER]
/tensura edit stat <e> (magicule|aura|spiritualHP|ep) (current|max) (set|add) <double> [<resetCurrent:bool>] | ... current set max
                   | <e> severance (set <float>|clear) | <p> resetCounter|bonusSkillLock|maxWarp (set|add) <int>
                   | <p> reputation (set|add <double>|reset) | <e> sleepMode (set|add) <int>   [edit_stat, GAMEMASTER]
/tensura edit spirit <e> set <element> <spiritlevel> | clear | cooldown <int>   [edit_spirit, GAMEMASTER]
/tensura edit owner <e> name (set <text>|remove) | permanent|temporary (set <e1>|remove) | neutral (add|remove <e1>|clear)   [edit_owner, GAMEMASTER]
/tensura get ability check (<e1>|self) <skill> | storage <e1> <skill> | list [all|skill [<t>]|magic [<t>]|battlewill] (<e1>|self) <excludeLearning:bool> | checkFlight <p>
/tensura get race (<e1>|self) race|alignment|spiritualForm          [get_race_self, PLAYER]
/tensura get awakening (<e1>|self) demonLord soul|harvestFestivalTick|seed|awakened | hero blessed|egg|awakened | humanKill   [get_awakening_self, PLAYER]
/tensura get stat (<e1>|self) (aura|magicule|ep|spiritualHealth) (current|max) | severance | sleepMode | maxWarp | bonusSkillLock | reputation | resetCounter [check]
/tensura get spirit check (<e1>|self) <element> | list (<e1>|self) | cooldown (<e1>|self)
/tensura get owner (<e1>|self) name|permanent|temporary|neutral
/tensura reset <p> everything | race [<race>] | awakening | skill | statistic   [tensura.command.reset, GAMEMASTER]
/tensura worldData [world_data, ADMIN]
  trulyUnique add <player> <skill> | remove <skill> | check <skill> | list taken | list remaining
  labyrinth ... | areaMagicule ... | bossFight ... | warpPad ... | worldRestriction ...
/ability set <skill> <mode> <slot> | lock add|remove <skill> | lock clear|list | toggle <skill> <bool> | toggle all|random [skill|magic|battlewill ...] <bool>
         | preset set <n> | preset name <n> <name> | spatial warp|portal <skill> <pos> [<dim>] | spatial storage <skill> open|add   [ability_slot, PLAYER]
/evolve race | demonLord | hero   [tensura.command.evolve, PLAYER]
/nameable <bool>   [PLAYER]     /despawn <e> [OWNER]     /syncStorage <e> [OWNER]     /engrave <e> <enchantment> [<level>] [GAMEMASTER]
```

Notes for `registry.js`: `revoke <p> all` removes **every** ability (intrinsics, resistances, magic,
battlewill), not just uniques; per-skill `revoke <p> <skill>` is safer. Grant/revoke go through
`SkillHelper.learnSkill` (fires `UNLOCK_SKILL`) and `Skills.forgetSkill` (fires `REMOVE_SKILL`), and grant
adds `NoMagiculeCost` so the MP cost is skipped. `tensura reset <p> skill` and the skill Reset Scroll
(`ts.item.misc.ResetScrollItem`) call `randomUniqueSkill` and so reroll from `startingSkills`.

### 2.6 Learning state

Tensura stores "being learned" skills in the same storage with **negative mastery** (`AbilityHandler` UNLOCK
listener; `SkillUtils.hasSkillFully`). `getLearnedSkills()` returns them too. Always filter
`getMastery() >= 0 && !isTemporarySkill()` before counting a holder.

### 2.7 Death and reincarnation paths

- Normal death: `ts.handler.DeathHandler` applies `epDeathPenalty`; no reincarnation.
- Aspectual magic Reincarnation (`ts.ability.magic.aspectual.misc.ReincarnationMagic`): fires `REMOVE_SKILL`,
  `resetExistence(..)`, opens `ReincarnationMenu(id, inv, player, false, racePool, AP, MP)`. A player-driven second
  rebirth outside the pack flow; `ReincarnationMenuMixin.offersFor` returns null there, so Tensura's lists apply.
- Reset scrolls (`ResetScrollItem`): fire `REMOVE_SKILL`, `ITrulyUnique.removeOwner`, `resetExistence`, open the menu,
  call `grantUniqueSkill` or `randomUniqueSkill` (the latter ignores `noUniqueStart`).
- `/tensura reset <p> ...` (`ts.command.edit.ResetCommand`): fires `REMOVE_SKILL`, calls `ReincarnationMenu.setRace(...)`.

---

## 3. Addons

### 3.1 Great Sage 0.0.7.1 (`gs.*`, modId `greatsage`)

Mixins (`greatsage.mixins.json`):

| Mixin | Target | Effect |
| --- | --- | --- |
| `UniqueStartMixin` | `ts.menu.ReincarnationMenu.grantUniqueSkill` @HEAD (cancellable) | if `sageReincarnation` and not paying: `UniqueDebt.owe(player)` and **cancel** (Tensura's `noUniqueStart` buff branch is skipped too) |
| | `ReincarnationMenu.clickMenuButton` (id -2, not change-race-only) | owes a unique when `sageReincarnation && !noUniqueStart` |
| `RimuruStartMixin` | `ReincarnationMenu.reincarnateAsRimuru` @TAIL | `RimuruBirth.reborn` scene |
| `FollyRequirementMixin$Ep/$Consume/$Carry/$Boss` | `ts.race.template.EvolutionRequirement$*Requirement.getProgress / getRequirementComponent` | Folly curse alters evolution requirements |
| client: `GuiMixin`, `GuiGraphicsMixin`, `ThoughtSoundMixin` | | rendering |

Listeners: `SkillUnlockListener` (`SkillEvents.UNLOCK_SKILL`, announcements), `EvolutionListener` (`RaceEvents.SET_RACE`),
`SkillFusion` (`SkillEvents.REMOVE_SKILL`, fusion detection), `NamingWatcher` (`TensuraEntityEvents.NAMING_EVENT` + server tick),
`AwakeningWatcher` (NeoForge `PlayerTickEvent.Post`, polls `IExistence` flags), `UniqueDebt.onClose` (NeoForge
`PlayerContainerEvent.Close` on a `ReincarnationMenu`: pays an owed unique via `grantUniqueSkill` with `PAYING` set and
`skillNumber` temporarily reduced; under `noUniqueStart` that only gives the MP/AP buff).

Reincarnation scene grants (`gs.server.ReincarnationGrants.apply(ServerPlayer, ReincarnationChoicePayload)`), bytecode:
- Accepted whenever the player's open container is a `ReincarnationMenu` that is not change-race-only. The network
  handler (`gs.network.GreatSageNetwork`) does no gamerule check and `apply` never reads `noUniqueStart` or `sageReincarnation`.
- Max 3 wishes per menu (`WISHES`). `payload.wish()` on the first wish: `ReincarnationMenu.randomUniqueSkill(player, ..)`
  (Tensura pool, **not** filtered by `reincarnationExcludedSkills`) then `UniqueDebt.settleAll`.
- Sigil wish: `SigilShuffle.gifts(player, sigil)` -> `ReincarnationPool$Gift(unique, minor, evolved)`; first wish grants
  `unique`, later wishes `minor`; with probability `reincarnationErrorChance` it grants `evolved` instead. If the chosen id is
  excluded/null, it falls back to a shuffled `ReincarnationPool.all()`. Grants via `SkillGift.grant` (bypasses registry.js).
- `ReincarnationPool.fixed(sigil)` passes unique/minor/evolved through `allowed()` -> `excluded(id)` (exact id or `mod:*`), so
  `reincarnationExcludedSkills` does work for the sigil path.
- Fixed sigil table (`gs.Sigils`) entries holding Legendaries: `bolt` -> wrath, `eight` -> envy, `loop` -> creator,
  `circle` -> predator (evolved: gluttony), `diamond` -> greed, `pillar` -> pride, `crescent` -> sloth, `heart` -> lust,
  `inward` -> analyst / minor sage / evolved **great_sage**.
- **Unverified:** whether the client scene still offers wishes when `noUniqueStart` is true (no client reference to
  `NO_UNIQUE_START` was found). Server-side nothing stops it; a modified client can send the payload anyway.

Other skill changes: `RaphaelEvolutionService` forgets `tensura:great_sage` (+ `tensura:degenerate`) and grants
`greatsage:raphael`; `SkillFusion` grants fused skills. Both change holder state of a Legendary line.

Public API: `gs.api.WorldVoice`
- `announce(MinecraftServer, String clip, Component japanese, Component text, UUID except)` (all online players except one)
- `announce(Collection<ServerPlayer>, String clip, Component japanese, Component text)`
- `enabled(MinecraftServer)` = gamerule `worldVoice`. Valid `clip` ids **unverified** (command `test` uses `true_demon_lord`, `harvest_festival`, `true_hero`).

Commands (`gs.server.GreatSageCommands`, `DEV` = `!FMLEnvironment.production`):
- production: `/greatsage worldvoice <targets> <clip> <japanese> <text>` (perm 2), `/greatsage xp <targets> info | add <n> | set <n> | level <n>` (perm 2)
- dev-only: `worldvoice test <event>`, `ceremony <type>`, `evolve <from> <to>`, `demo`, `fusion [<skills>]`, `preview <skills>`, `sigils`,
  `grant <skill>`, `mark <entities> demon_lord_seed|true_demon_lord|hero_egg|true_hero|blessed|clear`

Game rules (`gs.GreatSageGameRules`): `announcementsRequireGreatSage` (false), `requireGreatSage` (true),
`sageProgression` (true), `sageInterface` (true), `sageShaderRendering` (true), `sageReincarnation` (true; pack sets true),
`worldVoice` (true).

Config `config/greatsage-common.toml` [general] (`gs.GreatSageCommonConfig`): `joinGraceTicks`, `announcedCeremonies`,
`shieldedCeremonies`, `ceremonyShieldTicks`, `analysisTicks`, `analysisFailChance`, `analysisClassFactors`, `analysisSkillTimes`,
`reincarnationErrorChance` (0.03), `latentTimeFactor`, `latentMagiculeExtra`, `modeTimeExtra`, `assessRange`, `assessEpRatio`,
`assessNauseaRatio`, `enableTips`, `tipQuietTicks`, `reincarnationShuffle` (OFF/WORLD/PLAYER), `reincarnationAddonUniques`
(TENSURA_LIST/ALL/NONE), `reincarnationExcludedSkills` (default `["trnightmares:sentient"]`), `growthContentShare`,
`growthXpMultiplier`, `thoughtAcceleration*`, `growthAppraisal`. The pack repo has **no** `pack/config/greatsage-common.toml`,
so the server runs the defaults.

Player NBT written by Great Sage (`getPersistentData().PlayerPersisted`): `greatsage_unique_owed`, `greatsage_unique_given`,
`greatsage_unique_wished`, `greatsage_unique_drawn`, `greatsage_sigils`, `greatsage_sigil_life` (`UniqueDebt`, `SigilShuffle`).

### 3.2 TenSura Compat: FTB 2.0.0.4 (`io.github.manasmods.tensura_ftb`)

- Mixins: `MixinFTBQuestsEventHandler` (`dev.ftb.mods.ftbquests.FTBQuestsEventHandler.playerKill` @RETURN: subordinate kills count
  for the owner's kill tasks), `MixinSubordinateHelper` (`ts.util.SubordinateHelper.isAlly`: FTB team mates count as allies when `ftbAllyTensura`).
- `FtbHandler`: FTB Chunks protection via `SKILL_GRIEF_PRE`, `SKILL_PLUNDER`, `ENERGY_DRAIN_EVENT`, `FORCE_MOVEMENT_EVENT`,
  `FORCE_TAME_EVENT`, `POSSESSION_EVENT`, `SPIRITUAL_HURT_EVENT`, `INSTANT_TRANSMISSION_EVENT`, `LivingEffectAddedEvent`.
- Config `tensura/ftb_config` (`FtbConfig`): `ftbAllyTensura`, `protectPlayers`, `protectSubordinates`, `protectMobs`, `protectedEntities`,
  `mobDamage`, `mobDamageAbility`, `harmfulEffect`, `energyDrain`, `mindControl`, `possession`, `spiritualDamage`, `forcedMovement`,
  `forcedTeleportation`, `abilityPlundering`, `abilityGrief`.
- FTB Quests types (`TensuraFtb`; ids assumed `tensura_ftb:<name>`, **unverified** prefix): tasks `ability`, `awakening`,
  `existence_value`, `spirit`, `race`; rewards `ability`, `awakening`, `existence_value`, `spirit`, `race`, `random_ability`.
  `RandomAbilityReward` draws from the whole skill registry by `RandomType` (ALL, SKILL, RESISTANCE, COMMON, INTRINSIC, EXTRA,
  **UNIQUE**, ULTIMATE, MAGIC, ...). `AbilityReward`/`RandomAbilityReward` call `SkillHelper.learnSkill`: another grant path.

### 3.3 TenSura Compat: Iron's Spells 2.0.0.0 (`io.github.manasmods.tensura_iron`)

Mixins (`tensura-iron-forge.mixins.json`): Tensura `AbnormalConditionNullification`, `ColdNullification`, `ColdResistance`,
`ThermalFluctuationNullification/Resistance`, `ExistenceStorage`, `MagicUtils`, `TensuraDamageHelper`; Iron's `AbstractSpell`,
`EvasionEffect`, `ManaBarOverlay`, `PortalManager`. `NeoEventsHandler` listens to Iron's `SpellPreCastEvent`, `SpellOnCastEvent`,
`SpellDamageEvent` and Tensura `ENERGY_DRAIN_EVENT`. Config (`IronConfig`): `manaConversionMultiplier`, `spellDamageMultiplier`.
Data: EP values for Iron's mobs/gear (`data/irons_spellbooks/entity_existence`, `gear_existence`). No skill grants found.

### 3.4 TenSura: Not Enough Bosses 2.0.0.3 (`io.github.manasmods.tensura_neb`)

Entities: `VeldoraEntity`, `CarrionEntity` (learns `royal_beast`), `LuminousValentineEntity` (learns **`lust`**,
`infinite_regeneration`, darkness/spiritual nullification), `RimuruCloneEntity` (`coercion`, `water_blade`), `RimuruOgreFightEntity`.
Mixins: `MixinOtherworlder` (`ts.entity.human.KyoyaTachinbanaEntity`), `MixinSolarBeamProjectile` (`ts.entity.magic.beam.SolarBeamProjectile`).
`NebHandler` listens to `ENERGY_DRAIN_EVENT`. Config (`NebConfig`): `rimuruChance`, `carrionChance`, `luminousChance`.
A boss holding `lust` can be plundered (Predator mist etc. fire `SKILL_PLUNDER`), which is a Legendary path outside registry.js.

### 3.5 TensuraMoreConfigs 0.0.2 (`com.github.wal_bos.tensuramoreconfigs`)

Op-only (perm 2) chat commands that rewrite the live reincarnation config: `/tmconfig`, `/tmconfig reincarnation skills|races|undo`,
then per list `list [available|addons] [page n]`, `add <name>`, `add all [addons]`, `add from <mod>`, `remove <name>`, `removeall [addons]`.
Backups and `audit.log` under `config/tensuramoreconfigs/` (`ConfigService`). Edits `Skills.startingSkills`, `skillNumber`,
`additionalUniqueChance`, `secondSkills`, race lists. No mixins, no events. Risk: an op can re-add Legendaries to `startingSkills` live.

---

## 4. KubeJS reach

- Class filter: `kubejs.classfilter.txt` in the KubeJS jar (also in `ftb-library`, `ftb-teams`, `ftb-xmod-compat`). `ClassFilter.isAllowed0`
  (bytecode): exact deny, exact allow, then prefix deny; everything else **allowed**. Nothing denies `io.github.manasmods`,
  `dev.dedek` or `dev.architectury` (the file even has `+ dev.architectury`). Denied: `org.spongepowered.asm`, `java.io`, `java.net`,
  `net.neoforged.fml`, most of `java.lang`. So `Java.loadClass('io.github.manasmods.manascore.skill.api.SkillAPI')` works.
- Plugins: `kubejs.plugins.txt` exists only in KubeJS, `ftb-xmod-compat`, `l2hostility`, `lootjs`. **No Tensura/ManasCore/Great Sage
  KubeJS plugin**: no `TensuraEvents.*` in JS, no bindings, no typed wrappers.
- `NativeEvents.onEvent(Class, Consumer)` (`dev.latvian.mods.kubejs.plugin.builtin.wrapper.NativeEventWrapper`) is NeoForge-bus only;
  it cannot hear Architectury events.
- Listening from JS is possible but fragile (**unverified in game**):
  - `Event.register(T)` erases to `register(Object)`, so Rhino will not auto-wrap a JS function. Build the interface explicitly
    (Rhino ships `dev.latvian.mods.rhino.InterfaceAdapter`/`JavaAdapter`), e.g.
    `new UnlockSkillEvent({ unlockSkill: (inst, entity, msg) => EventResult.pass() })`.
  - Server scripts re-run on `/reload`; `register` again adds a second listener. Keep the listener in `global` and call
    `unregister(old)` first, or register once from a startup script.
  - The callback runs inside game logic (skill grant, race set). A JS exception there can break that grant; wrap the body in try/catch and return `EventResult.pass()`.
- Reading is easy and safe: storages and APIs are plain Java objects; KubeJS 2101 `player` is the real `ServerPlayer`.

```js
// server_scripts/ttl/manas.js (sketch, golden rule: loadClass inside try/catch)
let TtlManas = null
try {
  const SkillAPI = Java.loadClass('io.github.manasmods.manascore.skill.api.SkillAPI')
  const RaceAPI = Java.loadClass('io.github.manasmods.manascore.race.api.RaceAPI')
  const Tags = Java.loadClass('io.github.manasmods.tensura.data.TensuraSkillTags')
  TtlManas = {
    // ids of uniques the player really holds (not learning, not temporary)
    uniques(player) {
      const out = []
      SkillAPI.getSkillsFrom(player).getLearnedSkills().forEach(i => {
        if (i.is(Tags.UNIQUE_SKILLS) && i.getMastery() >= 0 && !i.isTemporarySkill()) out.push(String(i.getSkillId()))
      })
      return out
    },
    race(player) {
      const r = RaceAPI.getRaceFrom(player).getRace()
      return r.isPresent() ? String(r.get().getRaceId()) : null
    }
  }
} catch (e) { console.error(`[ttl] manas bridge unavailable: ${e}`) }
```

---

## 5. Recommendations

### (a) Read learned uniques for the holder registry

- Source of truth: `SkillAPI.getSkillsFrom(player).getLearnedSkills()`, filtered with `is(TensuraSkillTags.UNIQUE_SKILLS)`
  (or `((Skill) inst.getSkill()).getType() == UNIQUE`, which also covers addon uniques not in the tag), `getMastery() >= 0`,
  `!isTemporarySkill()`. Do not trust `ttl.uniques` alone; it drifts because of the paths in (d).
- Reconcile on `PlayerEvents.loggedIn`, after every registry grant/revoke (next tick), on a slow timer (e.g. every 5 min for
  online players), and after a rebirth. Rebuild `ttl.reg.skills.<id>` holders from what is actually learned; log differences with `[ttl]`.
- Offline holders: storage lives in player NBT; keep the server-side holder map as the record and correct it when the player logs in.
- For per-skill caps the registry needs the full held set, not one string: change `ttl.uniques` to a list (comma-joined, like `ttl.reg.held`).

### (b) React when a player learns or loses a skill

- Best: Java listener in `ttl-portals` (needs approval under rule 5): `SkillEvents.UNLOCK_SKILL` and `REMOVE_SKILL`.
  Use them to **veto** (return `EventResult.interruptFalse()`) and to schedule a reconcile on the next server tick
  (`server.execute(...)`), because Tensura's own listener can still cancel either event and `SkillHelper.learnSkill`
  re-fires `UNLOCK_SKILL` for skills already present. Hand control to scripts with a silent command, as `Rebirth.onRaceSet` already does
  (e.g. `ttl skillchanged <player> <skill> learned|lost`).
- KubeJS-only alternative: register through `Java.loadClass` with an explicit `InterfaceAdapter` and `global`-guarded unregister (section 4),
  or skip events and rely on the reconcile pass (simplest, eventually consistent).
- Skills that disappear without `REMOVE_SKILL`: none found in ManasCore (`forgetSkill` always fires it; `updateSkill` adds without
  `UNLOCK_SKILL`). Reconcile covers both.

### (c) React to race changes and evolutions

- `RaceEvents.SET_RACE(previous, entity, next, isEvolution, teleport, msg)` covers first race, rebirth, `/tensura edit race`,
  reset scrolls and evolutions (`Races.evolveRace` -> `setRace(evolution=true)`); it fires before the change, so act next tick.
- The existing mixin on `ReincarnationMenu.setRace` @TAIL stays the right hook for the pack's own rebirth; use `SET_RACE` for everything else.
- Awakening: `TensuraEntityEvents.AWAKENING_EVENT` (`isHero` true/false). Seed/Egg/True flags have no event: poll `IExistence` like Great Sage's `AwakeningWatcher`.
- Naming: `NAMING_EVENT(sub, owner, epGain, cost, type, name)`.

### (d) Keep Legendaries out of every automatic grant path

| Path | Where | Fix |
| --- | --- | --- |
| Tensura reincarnation roll | `ReincarnationMenu.randomUniqueSkill` <- `startingSkills`/`secondSkills` | remove the 9 Legendaries (and `gluttony`) from both lists in `pack/config/tensura/reincarnation_config.toml` |
| Great Sage "wish" button | `ReincarnationGrants.apply` -> `randomUniqueSkill` | same config fix (exclusion list does not apply here) |
| Great Sage sigil wishes + 3% error upgrade | `ReincarnationPool.fixed` / `Gift.evolved` | ship `pack/config/greatsage-common.toml` with `reincarnationExcludedSkills = ["trnightmares:sentient", "tensura:predator", "tensura:great_sage", "tensura:creator", "tensura:envy", "tensura:greed", "tensura:lust", "tensura:pride", "tensura:sloth", "tensura:wrath", "tensura:gluttony"]`; consider `reincarnationErrorChance = 0.0` |
| Great Sage scene grants any unique outside registry.js | `ReincarnationGrants.apply` ignores `noUniqueStart` | decide: (1) mixin in `ttl-portals` cancelling `ReincarnationGrants.apply` @HEAD while `Rebirth` holds offers for that player, or (2) open the rebirth menu with `changeRaceOnly = true` (apply, `UniqueStartMixin` and `UniqueDebt.onClose` all skip change-race-only menus; whether the scene still plays and `Rebirth.onRaceSet` still fires: **unverified**), or (3) `gamerule sageReincarnation false` (loses the scene). Update the comment in `life/gamerules.js`, which currently claims `noUniqueStart` blocks the scene grants |
| Reset scrolls, `/tensura reset <p> skill` | `ResetScrollItem`, `ResetCommand` | config fix above; optionally ban the scroll items via recipes/loot |
| Aspectual magic Reincarnation | `ReincarnationMagic` | config fix; `noUniqueStart` blocks Tensura's own grant there, the Great Sage path needs the fix above |
| FTB Quests rewards | `tensura_ftb` `ability` / `random_ability` | `tools/gen_quests.py`: never emit these for uniques; never `random_ability` with ALL/UNIQUE |
| Plunder (Predator mist, Gluttony, Great Sage, Pride, ...) from bosses (NEB Luminous holds `lust`) and players (`skillSteal`) | `SKILL_PLUNDER` | veto Legendary plunder in a `SKILL_PLUNDER` listener unless the registry's absorb flow authorises it; or add Legendaries to `data/tensura/tags/manascore_skill/skills/no_plundering.json` via datapack (only checked by some skills, so the event veto is the complete fix) |
| Great Sage fusion / Raphael evolution | `SkillFusion`, `RaphaelEvolutionService` | let the reconcile pass re-key holders (`great_sage` -> `greatsage:raphael`) |
| `/tmconfig reincarnation skills add ...` | TensuraMoreConfigs | operational rule: ops never re-add Legendaries; check `config/tensuramoreconfigs/audit.log` |
| Ops typing `/tensura edit ability grant` | | by golden rule 1 only `registry.js` does this |

Defence in depth (single choke point): one `UNLOCK_SKILL` veto in Java that refuses any `tensura:unique_skills` member, any
Legendary and `greatsage:raphael`, unless `registry.js` authorised that exact (player, skill) pair moments before (for example
`ttl authorize <player> <skill>` setting a short-lived server-side allowance consumed by the listener). Every grant path above
goes through `Skills.learnSkill` or `SkillHelper.learnSkill`, which both fire `UNLOCK_SKILL`; `Skills.updateSkill` does not,
but no grant path found uses it for new skills (**unverified** for all of Tensura's 60 unique skill classes).
Also strip Legendaries from `ReincarnationMenu.CONFIG.Skills.startingSkills/secondSkills` at server start in the same mod, so a
stray config edit cannot bring them back.

### Top 5 actions

1. Remove the Legendaries (and `gluttony`) from `startingSkills`/`secondSkills` in `pack/config/tensura/reincarnation_config.toml`.
2. Add `pack/config/greatsage-common.toml` with the Legendary `reincarnationExcludedSkills` and `reincarnationErrorChance = 0.0`.
3. Close the Great Sage scene grant path in the Life 2 rebirth (mixin on `ReincarnationGrants.apply`, or test `changeRaceOnly = true`) and fix the `gamerules.js` comment.
4. With approval, add an `UNLOCK_SKILL` + `SKILL_PLUNDER` veto ("authorised grants only") and an `UNLOCK_SKILL`/`REMOVE_SKILL`/`SET_RACE` notifier to `ttl-portals`, forwarding to scripts via silent `ttl` commands.
5. Make `registry.js` reconcile from `SkillAPI.getSkillsFrom(player).getLearnedSkills()` (mastery >= 0, not temporary, unique tag), store a list per player, and revoke per skill instead of `revoke <p> all`.
