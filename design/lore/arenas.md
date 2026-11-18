# The combat arenas: lore and sources

Reference for `design/data/arenas.toml` and `arena/arenas.js` (owner, 18/11/2026: "combat can be in Walpurgis as well,
or maybe the Labyrinth arena from Ramiris, with loot drops"). Read this before moving an arena or changing its foes.

## What the mods already provide (read from the jars, 18/11/2026)

| Fact | Where it was read | How the arenas use it |
| --- | --- | --- |
| Tensura 2.0.1.5 ships Ramiris's Labyrinth as a dimension, `tensura:labyrinth` (void flat generator, fixed time, End sky), with its own blocks (labyrinth bricks/stone/lamps/crystals, `labyrinth_portal`, `labyrinth_barrier_block`, praying path) and the advancement "Dungeon Encroachment" | `data/tensura/dimension/labyrinth.json`, `dimension_type/labyrinth.json`, `assets/tensura/lang/en_us.json` | The Labyrinth arena is a place in that dimension; nothing is built by us |
| The Labyrinth is not worldgen: the mod writes ~610,000 blocks from `data/tensura/structure/labyrinth/dim/{ids,states,blocks}.ldat` the first time the level loads (`LabyrinthHandler` on LEVEL_PREPARED → `LabyrinthStorage.generateStructures`, asynchronous) | `LabyrinthStorage`, `LabyrinthHandler` (javap) | `ready = { at = [16, 37, 537] }`: nobody is let in before the hall's floor exists |
| The layout (decoded from the .ldat files, five pieces placed at offsets 0/0/0, 7/-35/317, -25/36/496, 7/-35/578, -39/-35/628): entrance at 16 1 12, the maze up to z ≈ 495, then a ROUND HALL centred on 16 38 537 (labyrinth-brick floor at y 37 on bedrock, bedrock wall at radius ≈ 40, dome to y ≈ 105, both doors sealed with labyrinth barrier blocks), then the "passed" area from z 578 on | `blocks.ldat` + `LabyrinthStorage.getOriginPos` | That hall is the arena: box -24 38 497 to 56 100 577, round radius 38 |
| The hall is the mod's Elemental Colossus arena: `ILabyrinth` defaults colossusPos 16 38 537, areaRadius 40; every player tick inside the radius spawns the Colossus (NATURAL) for a soul that has not beaten it, as long as the "first spawn" has not happened (or the gamerule `colossusRespawn` is on) | `LabyrinthHandler.playerTick`, `LabyrinthStorage.<init>` | See "The Colossus" below |
| Inside the Labyrinth nothing dies unless its type is in `#tensura:can_die_in_labyrinth` (`#tensura:spiritual`, `#tensura:clones`, `#tensura:non_living`, `tensura:elemental_colossus`) or the damage bypasses invulnerability; with the gamerule `labyrinthDeath` off (default) the creature is left at 0.01 HP, cleansed, made invulnerable for 5 s and sent to the overworld | `DeathHandler` (javap), `data/tensura/tags/entity_type/*.json` | Labyrinth waves are spirits and golems from that tag (salamander, beast gnome, feathered serpent, bone golem, war gnome) and the referee removes a wave mob on its fatal blow; a fighter's fatal blow is turned into a defeat before Tensura sees it |
| Entering the Labyrinth switches a survival player to adventure mode, leaving switches back (`LabyrinthPortal.switchGameMode` on every dimension change) | `LabyrinthHandler`, `LabyrinthPortal` | Nobody breaks the hall; the teleport back restores the mode |
| `labyrinthPvp` (default on) allows PvP there | `TensuraGameRules`, design/manas-integration.md | Duels and party battles work without changes |
| Tensura's other "arena" is `tensura:boss_area` (Gazel's arena `dwarf_village/building/dwarf_arena`, `BossFightStorage`) | `LabyrinthHandler.placeGazelArena` | Not used (story-characters.md §0: arenas stay ours) |
| No mod ships a Walpurgis venue or a Ramiris entity | lang files, structure folders of every jar | The Walpurgis Hall is our own build (`walpurgis_hall`) in our own dimension `ttl:walpurgis` (owner decision 18/11/2026) |

## Canon behind the two arenas (our interpretation is marked)

- **Ramiris's Labyrinth.** Ramiris builds the dungeon beneath Tempest with her skill (Small World / Labyrinth Creation);
  she runs it, Veldora is its final boss on the 100th floor, and it opens to adventurers at the Founding Festival. Deaths
  inside do not stick: adventurers wear a Resurrection Bracelet and come back to the surface, wounds healed (anime season 3
  episodes 14 and 23; light novel vol. 7-8). The mod's "1 HP and out" rule is that idea, and so is our non-lethal defeat.
  Sources: [Tensura wiki, Dungeon](https://breezewiki.discard.no/tensura/wiki/Dungeon) ·
  [Sportskeeda, season 3 episode 14](https://www.sportskeeda.com/anime/that-time-i-got-reincarnated-slime-season-3-episode-14-rimuru-gets-veldora-ramiris-help-dungeon) ·
  [Sportskeeda, season 3 episode 23](https://sportskeeda.com/anime/that-time-i-got-reincarnated-slime-season-3-episode-23-the-dungeon-trial-ends-rimuru-s-founder-s-festival-high) ·
  web-novel chapter "Underground Labyrinth Exploration Party" (revival about ten seconds after death).
- **The Elemental Colossus** is Ramiris's own golem, broken by Rimuru at Tempest; in the mod it guards this hall. *Our
  interpretation:* it is the Labyrinth challenge's last foe; the waves before it are the elemental spirits Ramiris rules as
  the Spirit Queen (the Dwelling of the Spirits, design/lore/spirit_domain.md).
- **Walpurgis.** The Demon Lords' banquet where they meet to report and settle disputes, where Rimuru defeated Clayman
  and the ten Demon Lords became the eight of the Octagram (anime season 2 episodes 45-48, episode 46 "Demon Lords'
  Banquet ~Walpurgis~"; light novel vol. 6). Sources: [Tensura wiki, Demon Lord council](https://tensura.fandom.com/wiki/Demon_Lord_council) ·
  [Tensura wiki, Walpurgis](https://tensura.fandom.com/wiki/Walpurgis_(chapter)) ·
  [animecorner, episodes 43-46](https://animecorner.me/that-time-i-got-reincarnated-as-a-slime-43-46-claymans-collapse/) ·
  [animecorner, episode 48](https://animecorner.me/that-time-i-got-reincarnated-as-a-slime-episode-48-rimurus-victory/) ·
  [thetvdb, Walpurgis episode](https://thetvdb.com/series/that-time-i-got-reincarnated-as-a-slime/episodes/8432232).
  The banquet was **not** held in Clayman's castle (design/lore/clayman_castle.md), and no description of the venue's
  layout was found. *Our interpretation:* the hall floats in its own dimension under a fixed midnight sky
  (`ttl:walpurgis`); a domed council chamber with a round table and **ten thrones**, one crest colour each (the pack's ten
  Legendary places are themed as the Ten Great Demon Lords; the later Octagram is eight); a beacon under a purple oculus;
  and beside it the Banquet Floor, a round pit with terraces where the Demon Lords' disputes are settled by combat (canon:
  Rimuru and Clayman fought at the banquet itself). The waves of the Walpurgis challenge are Jistav's undead (the wight
  king's army) and Clayman's daemons, the last foe the Clayman proxy boss (bosses.toml, owner decision O3).
- **The way in.** The hall is for Demon Lords and their guests: Legendary holders, souls who reached the story's Demon
  Lord / True Hero capstone, invited souls, and fighters with a booked match. *Our interpretation:* the doorway is the dais
  of Clayman's throne in his castle (he left from there for the banquet); the Walpurgis council statues already stand in
  that throne hall (npcs.toml).

## The Colossus

Our boss framework cancels every boss entity that spawns by itself (`bosses.toml [framework] block_natural`; the
Elemental Colossus is a `[[boss]]`), and Tensura retries its first Colossus every tick while that spawn does not come
alive. The arena therefore marks Tensura's first Colossus as spawned (`quiet_colossus = true`, through
`TensuraStorages.getLabyrinthFrom(level).setColossusFirstSpawned(true)`) the first time someone joins the Labyrinth arena,
and the Colossus fight lives on as the challenge boss, summoned through `TtlBoss.summon` (tagged, scaled, credited, with
its 96 h cooldown). A Colossus of the mod's own that is already standing in the hall (spawned before this) blocks joining
until it is beaten. **Verify in game:** whether `block_natural` really sees Tensura's `respawnColossus` spawn, and whether
beating the summoned Colossus marks the soul as having passed it in Tensura's own records.
