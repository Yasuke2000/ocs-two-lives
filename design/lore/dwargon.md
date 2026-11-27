# Dwargon: lore behind blueprints/dwargon.py

**Initial-era placement.** Kaijin and his apprentices have already joined Rimuru’s village (official episode6/9). Their old Dwargon premises do not authorize a second current Kaijin resident. See [snapshot policy](../../world/era.md) and [targeted review](../../docs/research/tensura-world-2026-11-19/era-brief-review-r121.md).

The build reference for the Armed Nation of Dwargon (武装国家ドワルゴン). Geography and placement are in
[world.md](world.md) §D. Read this before changing the blueprint.

**Research note (18/11/2026).** tensura.fandom.com returns HTTP 402 to direct fetches, and fetching its mirrors was
not allowed, so the facts below come from search-engine extracts and the sources in world.md §D. Items marked
*(unverified)* are from memory of the anime, manga and light novel and could not be checked; treat them as our own
design choices.

## Inside Lerfing's Canaat (WP-L7b, TTL_DWARGON_VERSION 8)

Owner decision of 19/11/2026 for the Lerfing import: Dwargon INSIDE the Canaat mountain. It replaces the "on a plain"
override below, which was for the old generated continent. The blueprint no longer brings its own mountain
(`CARVE` in `blueprints/dwargon.py`): the structures hold the city, the cavern's air with a 2-block lining of rock,
the cleft in front of the gate and the skylight crack; the rest is Lerfing's rock. The gate is at (1878, -544), base
y 142 (road y 145), rotation none: at the foot of the escarpment on the massif's south flank (a 50-block rise from
the apron at y ~145 to a plateau at y 200-215 within 60 blocks), facing south onto the apron and the road to Tempest.
The cavern lies under the plateau with 7 to 64 blocks of rock over it (median 28); the gate wall stands in a ravine
cut into the escarpment (up to 51 deep at the wall, running out onto the apron 64 blocks south), and the skylight
crack is a slot in the plateau (up to 71 deep) over the main street and the plaza. Chosen and checked offline on the
real heights with `tools/lerfing/dwargon_fit.py` (the hollow at the foot of the Canaat, as the lore says, is this
escarpment; *our interpretation*).

## Owner override: Dwargon on a plain (19/11/2026, superseded by the import above)

Yasuke, after looking at the public map: "Dwargon should be on a plain, not an ice mountain." The city's site in
`pack/config/ttl/canon_regions.json` (`dwargon`, flat ground y 72, plains; `dwargon_plain`, a plains/meadow
lowland of radius 230) wins over the lore's "hollow at the foot of the Canaat Mountains" for the area round the
build: the city stands on open ground and the Canaat peaks rise behind it to the north. The build's own mountain
stays (since version 7 in the Canaat's grey, see "The mountain's palette"). Takes effect on the next overworld reset (docs/HANDOFF.md).

## Facts the build follows

| Fact | How the build shows it | Source |
| --- | --- | --- |
| A dwarf kingdom, the "Armed Nation", in an underground cavern city behind fortified gates, in a natural hollow at the foot of the Great Canaat Mountains | The city sits in a cavern carved into Lerfing's Canaat massif (since version 8; before, its own mountain shell); the only way in is the white gate wall and a tunnel | world.md §D (fandom: Armed_Nation_of_Dwargon, Great_Canaat_Mountains) |
| Neutral trade hub, open to dwarves, elves and humans | Market plaza with twelve stalls, shop signs along the streets, an outer road with lamp posts | world.md §D; [gamerbraves](https://www.gamerbraves.com/?p=75332) |
| A big, busy city that can be dangerous for the careless | Dense multi-storey streets, back alleys, homes high in the walls | [thetvdb episode summary](https://www.thetvdb.com/series/that-time-i-got-reincarnated-as-a-slime/episodes/6843179) |
| Travellers queue at the city gate and are inspected; Rimuru's scuffle just outside the gate lands him in a cell | Fenced queue lanes (in and out) and two guard booths with lecterns in front of the gate; road tower and checkpoint arch further out | [thetvdb](https://www.thetvdb.com/series/that-time-i-got-reincarnated-as-a-slime/episodes/6843179) (scuffle at the gate); queue and inspection *(unverified)* |
| Mines near the city (the Armoursaurus report) | Not built yet: a mine entrance would fit beside the road tower | [thetvdb](https://www.thetvdb.com/series/that-time-i-got-reincarnated-as-a-slime/episodes/6843179) |
| King Gazel Dwargo, the Hero King, third king of Dwargon, ruling for over 300 years; his court (Arch-Wizard Jaine) judged Kaijin in a sham trial | The canon throne room (Tensura's Gazel Dwargo arena) carved into the back of the cavern behind the royal terrace and great stair; Gazel himself sits on the throne (NPC, not the boss fight) | [MyAnimeList](https://myanimelist.net/character/165297/Gazeru_Dwargo), [anibase](https://anibase.net/en/character/1GOQv/Gazel-Dwargo), [tvmaze ep. 5](https://www.tvmaze.com/episodes/1542630/that-time-i-got-reincarnated-as-a-slime-1x05-hero-king-gazel-dwargo/castappearances) |
| Kaijin runs the arms shop with his childhood friends Garm, Dold and Mildo, who are three brothers | Kaijin's smithy: the first house of the forge street (west), its ground floor a working forge with anvil, blast furnace and lava; a big forge hall on the plaza | [Official Kaijin profile](https://www.ten-sura.com/character/kaijin); smithy location *(our interpretation)* |
| The elf cabaret Night Butterflies | A pink-plastered house with magenta windows on the south street (west, z 83) | [search extract of the Tensura wiki "Dungeon" page](https://breezewiki.discard.no/tensura/wiki/Dungeon) |
| Dwarven engineering: Dwargon is the first tech tier | Create cogwheels on the plaza fountain, the workshop and the forge hall | design/master-plan.md (D8, tech pillar) |
| Pegasus Knights guard the king *(unverified)* | Not built (no mount NPCs yet); the royal terrace is the place for a stable | — |
| Colours: yellow banners with a red emblem, white gate *(unverified, our design)* | Gate banners, royal banners, road tower and checkpoint banners | — |

## Layout in short

South to north: outer road (checkpoint arch, road tower) → queue lanes and guard booths → white gate wall with
four towers → tunnel → south street (houses, the cabaret, lamps strung across the street) → round plaza with
fountain, stalls, forge hall and workshop → forge street (Kaijin's smithy) → great stair → royal terrace and
King Gazel's throne room. Above the street: wall homes on balconies at three heights, ladders up from the back alleys,
plank bridges across the canyon street under a skylight crack.

## The throne room (canon, since TTL_DWARGON_VERSION 3)

Source: Tensura 2.0.1.5 `data/tensura/structure/dwarf_village/building/dwarf_arena.nbt` (69x27x51), the room the
Gazel Dwargo boss fight is held in (dimension `tensura:boss_area`, `BossFightStorage.createGazelBossFight`). Copied
to `blueprints/assets/gazel_throne.nbt` and loaded with `from_structure` in `dwargon.py` (`throne_room`).

- Kept: the dais half (arena x 42-68): tuff/deepslate/stone brick hall, the red runner (fire coral fans on
  waterlogged mangrove slabs: they stay alive), the red nether brick throne with its red banner, copper bulb
  ceiling, candles, campfires, banners (patterns re-applied by `dwargon.js`, the structure loader drops block
  entity data).
- Changed: the black glass shell is rock; the redstone blocks that powered the bulbs are rock (bulbs keep
  `lit=true`); the side stairs into the pit are floor; a tuff/deepslate facade with a great door closes the cut.
- Left out: the boss pit (arena x 0-41) with its pillars, the exit warp pads (`tensura:royal_dwarven_warp_pad`,
  `tensura:stone_warp_pad`: real teleporters to the spawn point) and the developers' hidden nook (player heads, a
  sign).
- King Gazel: `tensura:gazel_dwargo` seated (Phase 0 plays the sit animation), NoAI, Invulnerable, Silent,
  PersistenceRequired and a dummy `Owner` so he is "tame": no boss bar or boss music (untamed he shows one in every
  dimension) and right-clicks do nothing (untamed, a click wakes him: phase 1, knockback). Tag `ttl_gazel`; a
  creative-mode hit can still wake him.

## The mountain's palette (WP-L7a, TTL_DWARGON_VERSION 7)

Source: Lerfing's map (design/architecture/lerfing-import.md §3.3), sampled on 19/11/2026 round the gate, x 1700..2040,
z -760..-300 (21,120 columns, 2-block stride, top non-plant block per column). The Canaat there is not concrete (the
grey concrete of the analysis lies in the far west, the Barren Lands): it is WorldPainter's grey cover, one material
per patch about 7 blocks deep (mycelium: one block over dirt), then stone. The blueprint's shell uses the same blocks
in the same proportions (`CANAAT_FLAT`, `CANAAT_SLOPE` in `blueprints/dwargon.py`, held by
`tests/test_dwargon_palette.py`); the city interior, the gate wall, towers, road furniture and the throne room keep
their own look.

| Block | Gentle ground (apron, terraces, 59 %) | Sloping ground (the rest, 41 %) | Whole sample |
| --- | --- | --- | --- |
| gravel | 57.8 % | 21.2 % | 42.9 % |
| clay | 5.1 % | 35.9 % | 17.6 % |
| mycelium (over dirt) | 20.5 % | 0.6 % | 12.5 % |
| tuff | 16.5 % | 1.0 % | 10.2 % |
| cobblestone | 0.1 % | 17.8 % | 7.3 % |
| stone | 0.1 % | 17.6 % | 7.2 % |
| light gray terracotta | — | 5.8 % | 2.3 % |

Replaced: banded sandstone, smooth sandstone, white and plain terracotta, the grass, moss, flowers and azalea bushes of
the apron and its terraces, and the sandstone of the cavern wall mix (now cobblestone). Placer side: `TtlDwargon.BANDS`
carries the same sloping-ground mix for the skirt and the fill under the build; the deep fill is stone.

## Style of Tensura's dwarf villages (for the city's houses)

From Tensura's `data/tensura/structure/dwarf_village/**` (79 pieces; jigsaw blocks ignored). Dwargon should read
as the capital of the same people. Applied since TTL_DWARGON_VERSION 4 to the street houses (`house()`: stone/andesite walls, polished andesite corners, cobblestone footing, stripped spruce posts, low weathered-copper roofs with granite trim, one granite/mud-brick cap style, glass panes with open spruce trapdoor shutters, spruce doors, cobbled deepslate chimneys), Kaijin's smithy (brick roof and chimney, a magma/coal/raw iron forge bed), the plaza (road-mix paving with a stone brick cross, a fountain rim of stone brick stairs and slabs, oak-fence stalls with white awnings striped in one colour, oak counter, chest, lantern), the forge hall (village walls, copper band and roof, stripped spruce arcade piers) and the street paving (cobblestone/tuff/gravel, polished andesite kerb). The wall homes, bridges, workshop (Create casings), gate and outer road keep their own look.

| Element | Dwarf village (NBT names) |
| --- | --- |
| Buildings | `building/house_small_1..6` 6x7x5, `library_1/2` 6x8x9, `butcher_1..3`/`shepherd` 10x7x12, `guard_1/2` 10x11x9, `smithy_1/2` 14x11x20, `house_large_1/2` 16x13x16 / 14x12x14, `royal_tower` 13x20x13 |
| Walls | Cobblestone foundation; solid stone + andesite infill (about 50/50, no half-timbering); polished_andesite corner posts; stone_bricks / cracked_stone_bricks plinth; stripped_spruce_wood posts on bigger buildings |
| Roofs | Low pitch: one ring of bottom-half `waxed_weathered_cut_copper_stairs` facing out, then a flat or one-step deck of cut copper (weathered mixed with exposed: patina), hips trimmed with polished_granite; small houses get a flat mottled granite / mud brick / packed mud cap; the smithy brick slabs |
| Windows, doors | glass_pane (some light_gray), iron_bars, open bottom-half spruce_trapdoor shutters (the commonest motif), spruce_door |
| Inside, decoration | spruce_planks floors, oak slab/trapdoor ceilings, cobbled_deepslate chimneys with a wall cap; lanterns (many hanging), barrels, chests, bookshelves, oak wall signs, yellow wall banners, flower and decorated pots, furnaces/smokers, water cauldrons; the smithy forge of magma, raw iron and coal blocks |
| Roads, plaza | Roads 5 wide of cobblestone/tuff/gravel in equal random parts, no edging; `plaza/village_plaza` 9x9 of the same mix with a stone brick cross; `plaza/fountain` 5x3x5 stone brick stair ring with a spruce trapdoor rim; `plaza/shop_1..8` 6x5x6 stalls: oak fence posts, white wool awning striped with one colour, oak plank/trapdoor counter, chest, lantern, banners |
| Palette (buildings) | stone 10%, andesite 10%, cobblestone 9%, stone_bricks 8%, spruce_planks 7%, oak_slab 3%, cracked_stone_bricks 3%, oak_planks/stairs 2% each, weathered cut copper (block, stairs, slab) 6% together, stripped_spruce_wood 2%, spruce_trapdoor 2%, polished_andesite 2% |
