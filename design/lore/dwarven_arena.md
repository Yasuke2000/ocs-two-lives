# The Dwarven Arena

Issue #5 (Yasuke's request): "add dwarven arena to the dwarven village, without the royal warp pad and the Dwargo
boss, maybe also without all the black stained glass layers on the outside". Blueprint `blueprints/dwarven_arena.py`,
placement `design/builds/dwarven_arena.toml`, arena `dwarven` in `design/data/arenas.toml` (duel, party, challenge).

## Sources and what we found

| Fact | Where | Consequence |
| --- | --- | --- |
| The export is Tensura 2.0.1.5 `data/tensura/structure/dwarf_village/building/dwarf_arena.nbt` (69x27x51), byte for byte the file in `blueprints/assets/gazel_throne.nbt` (CREDITS.md) | the jar and `Downloads/dwarf_arena.nbt` | one source; the Dwargon throne room (`blueprints/dwargon.py`) is cut from the same file |
| The structure holds **no entity**: Gazel Dwargo comes from `LabyrinthHandler.placeGazelArena` / `BossFightStorage.createGazelBossFight` in the mod's own boss dimension `tensura:boss_area` | structure NBT (`entities: []`), design/lore/arenas.md | nothing to strip for "no Dwargo"; the build summons nothing, and the arena's challenge has `boss = ""` |
| 9 `royal_dwarven_warp_pad` blocks (the entry pad of the pit, x 1-3 z 24-26) and 4 `stone_warp_pad` blocks (the hidden nook) are real teleporters (block entity `warp_pad_block_entity`, exit handler `spawnPoint`) | structure NBT | all removed |
| 30,666 `black_stained_glass` blocks form the void-facing envelope round the hall (a whole layer under it, the outer shell, the rock above the vault); only 35 of them touch an air cell, all in the developers' nook | structure NBT | dropped; the hall's own stone/tuff/deepslate walls stand on their own and the shell stays closed |
| The developers' hidden nook (x 5-10, y 20-24, z 31-36) holds three player heads with real account names (`Hazza12345`, `minheragon`, `Nieadni`), a sign and the second set of pads | structure NBT | filled with tuff, not copied (account names of third parties) |
| The hall's only ways in were the warp pads | structure NBT (closed shell) | a door (3x3) through the west wall of the pad alcove and a small stone brick forecourt are ours |

## Our interpretation

The boss pit (export x 5-41: five rows of pillars, the floor between them) is the arena floor, as it was Gazel's fight
hall; the stairs at x 41-43 rise to the throne dais (the red runner, Gazel's red nether brick throne, the copper bulb
vault), which becomes the spectators' gallery: stepping up there leaves the arena box. Gazel is not in the hall; the
throne stays empty (he sits in his real throne room in Dwargon, `design/lore/dwargon.md`). The challenge is the hall's
own guard: beast gnomes, bone golems, armorsaurs and war gnomes, three waves, no boss. Yellow Dwargon banners are plain
(block entity data does not survive a structure file in this pack); `dwargon.js` re-applies patterns for the throne room
only.

## Place

Beside the dwarf village on the Dwarven Road (`landmarks.toml dwarf_village`, 250 -740, reach 116), in the Dwargon region
(D on `canon_map.txt`) like the village. The placer keeps a 24 block gap from a landmark's reach square, so the arena
stands at 40 -850 (survey radius 16), west-north-west of the village: outside the Dwargon capital domain (x 179..691,
z -1256..-744) and 200+ blocks from the Life 2 arrival (271 -624). As an unowned canon build it is protected from block
edits (`factions.toml [domains] unowned_builds`), which is what an arena wants.
