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

In the dwarf village (19/11/2026, Lerfing's map). Yasuke's issue asked for the arena "in the dwarven village", and
Tensura itself files the hall among the village's buildings (`dwarf_village/building/dwarf_arena`); Gazel's own hall,
the boss room, is already the throne room inside Dwargon (`design/lore/dwargon.md`), and the gate's cleft and queue
lanes leave no room for a 75 x 51 hall at the forecourt, so the village is the lore-accurate home (*our
interpretation*). Anchor `dwarven_arena` = `dwarf_village` + (100, 20) = (2100, -90), `beside = "dwarf_village"`: the
placer keeps only the build's 6-block margin off the village's real (recorded) box and surveys 48 blocks round the
anchor, so the hall stands against the village's east side with its west door facing the houses, on the flat plains
and gravel east of the village (ground y 85-88, relief 3). It stays in the Dwargon region (D), 380+ blocks from the
Life 2 arrival, and as an unowned canon build it is protected from block edits (`factions.toml [domains]
unowned_builds`), which is what an arena wants.

Before (WP-L4 of the import, version 1) it stood at (2256, -76), 180 blocks east of the village, because the placer then
kept builds a whole reach square (116 + 64 + 24) off a landmark's spot; version 2 moves it and `life/builds.js` takes the
version-1 copy out block for block first. On the old continent it stood west-north-west of the village at -30 -850.
