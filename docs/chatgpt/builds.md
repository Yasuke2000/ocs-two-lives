# Designing a build

A **build** is a structure that Claude's placer puts into the world at a canon place: a town square, a gate, a hall, a ruin. We make them
as **Python blueprints** (`blueprints/<name>.py`), small programs that fill, box and sprinkle blocks into a 3D grid. A tool turns each into
a vanilla structure file and two preview pictures. ChatGPT designs the look; Claude does the placement, terrain and testing.

What belongs to whom:

| ChatGPT | Claude |
|---|---|
| Design notes (`docs/art/places/<id>.md`), concept art, a blueprint file `blueprints/<name>.py` or a plain-language build brief | Runs `build_structures.py` and `gen_data.py`, writes `design/builds/<name>.toml` (where it stands), tests it in game, fixes terrain and placement |
| Palettes, silhouette, floor plan, details | The generated `pack/kubejs/data/ttl/structure/<name>*.nbt` and `docs/previews/<name>-*.png` |

Read first: the place page in [places/](places/) (lore, intent, current state) and the build's lore page in `design/lore/`.
**Always use references** (anime stills, official art, the light novel) and mark what is "our interpretation". Never copy another mod's or map's
structure files or textures.

## 1. The blueprint format

A blueprint is `blueprints/<name>.py` with a `SIZE` and a `build(bp)` function. Coordinates are **relative to the structure's corner (0, 0, 0)**;
x grows east, y up, z south. Nothing outside `SIZE` may be set (the tool raises an error).

```python
SIZE = (width_x, height_y, depth_z)

def build(bp):
    bp.set(x, y, z, "minecraft:stone_bricks")                 # one block
    bp.fill(x1, y1, z1, x2, y2, z2, "minecraft:oak_planks")   # a solid cuboid (inclusive corners)
    bp.box(x1, y1, z1, x2, y2, z2, "minecraft:glass")         # hollow box, only the shell
    bp.disc(cx, y, cz, radius, "minecraft:gravel", inner=-1)  # a filled circle on one layer (a ring if inner >= 0)
    bp.pillar(x, z, y1, y2, "minecraft:oak_log[axis=y]")      # a vertical column
    for x, z in bp.around(cx, cz, radius, count):             # evenly spaced points on a circle
        ...
```

Block states use the command syntax: `"minecraft:quartz_stairs[facing=north,half=top]"`. Anything you do not set is simply *not part of
the structure* (the placer leaves the terrain there alone). Later calls overwrite earlier ones, so build big first, details last.

The helper libraries in `blueprints/_*.py` are shared code: `_sites_lib.py` (`M("stone")` = `"minecraft:stone"`, `pick(palette, r)`,
`tree`, `light_up`, noise), `_town_lib.py` (stairs, slabs, doors, banners, beds, a `Town` class for towns), `_dwargon_lib.py` (noise and
fractal terrain helpers), `_citylib.py`, `_lords_lib.py`, `_arena.py`. Reading one finished blueprint of a similar kind
(`blueprints/raja.py` for a small site, `blueprints/blumund.py` for a walled town) is the fastest way in.
`tools/blueprint.py` holds the `Blueprint` class itself.

### A worked minimal example

A 9 x 9 x 9 hut. It shows the conventions: the **ground layer** (grass on top, dirt and stone below), **explicit air above it** (so the placer
clears trees and hills inside the box), the walls, a door, a roof, a light and a bed, and the arrival point.

![the example hut](img/example_hut-iso.png)

```python
"""Wayfarer's hut: a minimal example blueprint (9 x 9 x 9). Ground layer y 2, you walk at y 3.

Arrival point (the doorstep, outside the south door): blueprint (4, 3, 8).
"""

SIZE = (9, 9, 9)
AIR = "minecraft:air"
G = 2  # ground layer: grass on top, dirt and stone below; the placer continues the real terrain under it


def build(bp):
    sx, sy, sz = bp.size
    bp.fill(0, 0, 0, sx - 1, 0, sz - 1, "minecraft:stone")          # under the ground layer
    bp.fill(0, 1, 0, sx - 1, 1, sz - 1, "minecraft:dirt")
    bp.fill(0, G, 0, sx - 1, G, sz - 1, "minecraft:grass_block")      # the ground layer
    bp.fill(0, G + 1, 0, sx - 1, sy - 1, sz - 1, AIR)                 # explicit air: clears trees and hills in the box

    bp.fill(2, G, 2, 6, G, 6, "minecraft:cobblestone")                 # floor
    bp.box(2, G + 1, 2, 6, G + 3, 6, "minecraft:spruce_planks")        # walls
    bp.fill(3, G + 1, 3, 5, G + 3, 5, AIR)                             # hollow it out
    for x, z in ((2, 2), (6, 2), (2, 6), (6, 6)):
        bp.pillar(x, z, G + 1, G + 3, "minecraft:stripped_oak_log[axis=y]")
    bp.fill(4, G + 1, 6, 4, G + 2, 6, AIR)                             # door opening, south wall
    bp.set(4, G + 1, 6, "minecraft:spruce_door[facing=south,half=lower,hinge=left]")
    bp.set(4, G + 2, 6, "minecraft:spruce_door[facing=south,half=upper,hinge=left]")
    for z in range(2, 7):                                              # roof: stair rows and a ridge of slabs
        bp.set(1, G + 4, z, "minecraft:spruce_stairs[facing=east,half=bottom]")
        bp.set(7, G + 4, z, "minecraft:spruce_stairs[facing=west,half=bottom]")
        bp.set(2, G + 5, z, "minecraft:spruce_stairs[facing=east,half=bottom]")
        bp.set(6, G + 5, z, "minecraft:spruce_stairs[facing=west,half=bottom]")
        bp.fill(3, G + 5, z, 5, G + 5, z, "minecraft:spruce_planks")
        bp.set(4, G + 6, z, "minecraft:spruce_slab[type=bottom]")
    bp.set(4, G + 3, 4, "minecraft:lantern[hanging=true]")             # light inside (the build must have block light)
    bp.set(4, G + 4, 4, "minecraft:spruce_planks")
    bp.set(3, G + 1, 3, "minecraft:red_bed[facing=north,part=foot]")
    bp.set(3, G + 1, 2, "minecraft:red_bed[facing=north,part=head]")
```

The smallest real blueprint in the repo is [`blueprints/test_hut.py`](../../blueprints/test_hut.py) (a 5 x 5 stone hut). Check the preview with
`python tools/build_structures.py wayfarer_hut` (section 4). The example above was run with the repo's own `Blueprint` class and builds 729 blocks.

### What a blueprint file must also say

The module docstring is read by humans and by the gallery: say what the build is, its size, the **anchor** (the walking-level point that lands on
the canon spot, usually the doorstep or the middle of the square) and the sources ("our interpretation" marked). Optional module values:

- `PARTS = [0, 30, 60]`: z offsets that split a big build into slabs (`name_0`, `name_1`, ...) placed one after the other (less lag, smaller files). Use it for anything wider than about 70 blocks.
- `outputs(bp)`: advanced; returns generated data files (footprints). Leave to Claude.

## 2. Palettes, sizes, footprint and terrain

**Palettes.** Stay with vanilla blocks unless a mod block is part of the lore (Tensura's labyrinth stone, magic ore). **Never invent a block
id**: if you are not sure it exists in Minecraft 1.21.1, use a vanilla one. Mod ids must be verified by Claude. A good palette is 3 to 6 materials with a weighted mix, not one block:
the libraries take `palette = [(state, weight), ...]` and `pick(palette, r)` with a position-based noise value `r` in 0..1 (see `blueprints/sealed_cave.py`: `STONE_WALL`, `DEEP_WALL`).
Match the pack's colours: heraldry of each nation in `design/lore/heraldry.md` and [art.md](art.md); Tempest is Japanese-influenced blue and sage,
Dwargon red and yellow with grey stone, Lubelius white and gold, Eurazania gold and brown, Englassia navy and teal.

**Size limits.**
- Typical sites are 70 to 130 blocks wide and 30 to 66 high; the biggest are Dwargon (148 x 92 x 168) and the Tempest city (191 x 40 x 191).
- Height: everything must stay **below y 320** once placed (the build height limit). The ground layer sits at about y 60 to 90 on most places; mountains are higher (the Dragon's Nest is 46 high and tops out under 320).
- The placer's search area (box + margin + search radius x 2) must stay under 1,000 blocks, so very large builds search less. Do not exceed about 200 blocks in x or z.
- Keep every walkable room **lit**: the tool checks block light on every spawnable spot and fails if one is dark (`light_up` in `_sites_lib.py` adds lanterns).

**Footprint and terrain: the placer owns the terrain outside the box.** A blueprint describes the box only. The placer (Claude's `life/builds.js`) does the rest:
- It **surveys** the flattest dry spot within a search radius of the canon point, fills the gap under every column the blueprint defines down to the real ground (no floating builds), clears everything above the highest block of a column (trees, hills; unless `clear_above = false`), puts a 1:1 earth skirt of `margin` (8) columns round the box and repairs pits, caves, lava and water along the edge.
- **So you do**: draw a **ground layer** as the bottom of the box (grass, paving, sand, snow: whatever the site wants) and **write explicit air** wherever the inside must stay open (a cave, a hall, a tunnel). The placer fills under the lowest and clears above the highest block of a column, so anything you leave undefined is left to the terrain.
- **You do not** make the surrounding landscape, big flat pads, terraces or retaining walls to hide a slope. The owner's rule: **no structures pasted on**. A build should look like it belongs to its place: irregular edges, rock that continues into the hillside, vegetation, a path in and out. The audit lists the flat-pad problems below.
- Builds meant for a mountain or cave (Dwargon, the Sealed Cave, the Dragon's Nest) say so in their lore page and are cut into the terrain, not placed on top.

## 3. Rules that always hold

- Namespace and ids: only real vanilla or mod ids; ask Claude to verify a mod id.
- No entities, no loot tables, no scripts in a blueprint. NPCs, bosses and chests are Claude's.
- No other mod's or map's structure files, and no textures. Visual references only; name them in the lore page.
- Marks: write which parts are canon and which are "our interpretation" in `design/lore/<name>.md` (every existing page has a "Canon" and "What we built" section).
- Do not edit `pack/kubejs/server_scripts/`, `mod/` or the generated files (`pack/kubejs/data/ttl/structure/*.nbt`, `docs/previews/*.png`, `docs/previews/README.md`, `pack/kubejs/server_scripts/ttl/generated/`).

## 4. Making previews

```
python tools/build_structures.py <name>      # one build
python tools/build_structures.py             # all builds
```

This runs `blueprints/<name>.py`, writes `pack/kubejs/data/ttl/structure/<name>.nbt` (or `<name>_0.nbt`, ... for PARTS) and two pictures in
[`docs/previews/`](../previews/README.md): `<name>-iso.png` (an isometric view) and `<name>-top.png` (top-down), and refreshes the
gallery `docs/previews/README.md`. The preview is a flat-shaded block picture with a fixed colour per block family; it is for checking the
shape, not for beauty. ChatGPT cannot run the tool: **hand in the `.py` file; Claude runs the tool** and commits the structure and previews
(CI fails when a structure file is out of date, so these generated files must never be hand-edited or left stale). A WorldEdit `.schem` or a
captured `.nbt` can also be a blueprint (`blueprints/<name>.schem` wins over the `.py`).

## 5. All existing builds

Previews are the blueprint on its own (not in the world). **Status** is the place audit of 19/11/2026 on Lerfing's map
("Map: Tensura by Lerfing (current, being replaced)"): it tells which builds look wrong in the world and why. The positions and terrain will change with the new world;
the blueprint itself usually stays. Each place page has the BlueMap screenshots.


### The Tensura world (overworld)

| Blueprint | Size (x, y, z) | Dimension | Preview | Place page | Status in the world (19/11/2026) |
|---|---|---|---|---|---|
| `sealed_cave` | 88 x 50 x 88 | overworld | <img src="../previews/sealed_cave-iso.png" width="200" alt="sealed_cave"> | [sealed_cave](places/sealed_cave.md) | **ISSUE (low).** Placed 113 blocks from the canon point (31 candidate spots fell in a keepout); the flat square pad round the dome is visible. verify 99.99 %: 32 log cells missing (oak_log/dark_oak_log -> air at y 73-74, e.g. 1424 73 387), a few cave vines. |
| `spirit_gate` | 57 x 40 x 57 | overworld | <img src="../previews/spirit_gate-iso.png" width="200" alt="spirit_gate"> | [spirit_gate](places/spirit_gate.md) | **OK.** Dense dark forest (stored biome dark_forest), verify 100 %; fits the lore. |
| `treyni_shrine` | 33 x 22 x 33 | overworld | <img src="../previews/treyni_shrine-iso.png" width="200" alt="treyni_shrine"> | [treyni_shrine](places/treyni_shrine.md) | **ISSUE (medium).** Lore: shrine stands in an open meadow (stored biome plains), with the forest starting just east. Known; fix in progress. verify 99.99 % (3 vines), foundation solid, no fluids. |
| `dragons_nest` | 73 x 46 x 73 | overworld | <img src="../previews/dragons_nest-iso.png" width="200" alt="dragons_nest"> | [dragons_nest](places/dragons_nest.md) | **ISSUE (low).** Cosmetic: the nest sits on a bright white square pad (the terrain fit's flat plate) on a brown stony peak, very visible from above. verify 100 %, foundation solid, no fluids, 12 blocks from the canon point at y 274. |
| `dwarven_arena` | 75 x 26 x 51 | overworld | <img src="../previews/dwarven_arena-iso.png" width="200" alt="dwarven_arena"> | [dwarven_arena](places/dwarven_arena.md) | **ISSUE (medium).** Out of place (known): a closed grey stone hall with a red stripe on a slope at the plains/stone edge, unrelated to anything nearby. The anchor (2256 77 -76) is on the west edge of the 75 x 51 build (anchor offset x 3), so the arena's centre is about 30 blocks east of the canon point. |
| `blumund` | 124 x 52 x 116 | overworld | <img src="../previews/blumund-iso.png" width="200" alt="blumund"> | [blumund](places/blumund.md) | **OK.** Walled town on plains by a lake, 43 blocks from the canon point; verify 100 %. |
| `ballachia` | 76 x 38 x 66 | overworld | <img src="../previews/ballachia-iso.png" width="200" alt="ballachia"> | [ballachia](places/ballachia.md) | **OK.** Plains between a river and the coast; verify 100 %. |
| `englassia` | 128 x 60 x 112 | overworld | <img src="../previews/englassia-iso.png" width="200" alt="englassia"> | [englassia](places/englassia.md) | **OK.** Plains with streams; verify 100 %. |
| `marris` | 136 x 64 x 112 | overworld | <img src="../previews/marris-iso.png" width="200" alt="marris"> | [marris](places/marris.md) | **OK.** Walled town in forest; verify 100 %. |
| `siltrosso` | 73 x 37 x 65 | overworld | <img src="../previews/siltrosso-iso.png" width="200" alt="siltrosso"> | [siltrosso](places/siltrosso.md) | **OK.** On the coast; verify 100 %. |
| `lubelius` | 120 x 64 x 120 | overworld | <img src="../previews/lubelius-iso.png" width="200" alt="lubelius"> | [lubelius](places/lubelius.md) | **OK.** White holy city on plains; verify 100 %. |
| `sacred_mountain` | 81 x 57 x 81 | overworld | <img src="../previews/sacred_mountain-iso.png" width="200" alt="sacred_mountain"> | [sacred_mountain](places/sacred_mountain.md) | **ISSUE (low).** Cosmetic: cut into a steep slope (mean deviation 7.5, spread 23): a stepped square terrace is visible round the box, with water pockets on its north edge (86 water cells in the box above ground, 16 in the ring; 1 moss_carpet -> water at -3012 120 -929). verify 100 %, foundation solid. |
| `coleus` | 85 x 47 x 79 | overworld | <img src="../previews/coleus-iso.png" width="200" alt="coleus"> | [coleus](places/coleus.md) | **OK.** Palace in the desert at the grass edge (Damargania, stored desert); verify 99.99 % (lightning rods). |
| `heaven_tower` | 81 x 60 x 91 | overworld | <img src="../previews/heaven_tower-iso.png" width="200" alt="heaven_tower"> | [heaven_tower](places/heaven_tower.md) | **OK.** Desert tower (stored desert); verify 100 %. |
| `morgdahl` | 69 x 31 x 61 | overworld | <img src="../previews/morgdahl-iso.png" width="200" alt="morgdahl"> | [morgdahl](places/morgdahl.md) | **OK.** Timber landing in forest by a lake; verify 100 %. |
| `raja` | 80 x 37 x 70 | overworld | <img src="../previews/raja-iso.png" width="200" alt="raja"> | [raja](places/raja.md) | **ISSUE (medium).** A surface LAVA pool about 15 blocks south-east of the box, clearly visible on the map (the survey counted 171 lava spots within 48). verify 100 %, foundation solid, water inside the box is the build's own pond (repair_keep_water). |
| `nostraille` | 72 x 33 x 64 | overworld | <img src="../previews/nostraille-iso.png" width="200" alt="nostraille"> | [nostraille](places/nostraille.md) | **OK.** Wool hall on open plains; a small surface lava pool about 50 blocks north-west. |
| `ulgr_nature_park` | 71 x 28 x 65 | overworld | <img src="../previews/ulgr_nature_park-iso.png" width="200" alt="ulgr_nature_park"> | [ulgr_nature_park](places/ulgr_nature_park.md) | **OK.** Edge of a forest; verify 100 %. |
| `jia` | 73 x 40 x 69 | overworld | <img src="../previews/jia-iso.png" width="200" alt="jia"> | [jia](places/jia.md) | **OK.** Hilltop court, 80 blocks from the canon point; verify 100 %. |
| `elmine` | 75 x 60 x 75 | overworld | <img src="../previews/elmine-iso.png" width="200" alt="elmine"> | [elmine](places/elmine.md) | **OK.** Divine-tree terrace (plains); only the build's own chunks are rendered so far. |
| `laura` | 113 x 46 x 113 | overworld | <img src="../previews/laura-iso.png" width="200" alt="laura"> | [laura](places/laura.md) | **OK.** Jungle (stored jungle), fits the beast kingdom; verify 100 %. |
| `forgotten_dragon_city` | 121 x 44 x 125 | overworld | <img src="../previews/forgotten_dragon_city-iso.png" width="200" alt="forgotten_dragon_city"> | [forgotten_dragon_city](places/forgotten_dragon_city.md) | **OK.** Badlands/terracotta (Milim's domain); verify 100 %. |
| `clayman_castle` | 109 x 66 x 109 | overworld | <img src="../previews/clayman_castle-iso.png" width="200" alt="clayman_castle"> | [clayman_castle](places/clayman_castle.md) | **OK.** Dark castle with moat in a dark forest; verify 100 %, moat water is the build's. |
| `amrita` | 69 x 32 x 75 | overworld | <img src="../previews/amrita-iso.png" width="200" alt="amrita"> | [amrita](places/amrita.md) | **OK.** Buried gallery in badlands; verify 100 %. |
| `nasca` | 85 x 42 x 79 | overworld | <img src="../previews/nasca-iso.png" width="200" alt="nasca"> | [nasca](places/nasca.md) | **OK.** Imperial court near the coast; verify 100 %. |
| `great_holy_mountain` | 89 x 52 x 85 | overworld | <img src="../previews/great_holy_mountain-iso.png" width="200" alt="great_holy_mountain"> | [great_holy_mountain](places/great_holy_mountain.md) | **OK.** Volcano sanctuary on red badlands; the flat square pad is visible but acceptable; verify 100 %. |
| `el_dorado` | 81 x 39 x 83 | overworld | <img src="../previews/el_dorado-iso.png" width="200" alt="el_dorado"> | [el_dorado](places/el_dorado.md) | **OK.** Golden court on a green hill, 45 blocks from the canon point; verify 100 %. |
| `frost_palace` | 85 x 51 x 69 | overworld | <img src="../previews/frost_palace-iso.png" width="200" alt="frost_palace"> | [frost_palace](places/frost_palace.md) | **ISSUE (low).** Cosmetic: a brown dirt skirt shows along the south edge of the box on the snowfield (no snow layer on top). verify 100 %, foundation solid, no fluids. |

### Settlements with their own scripts

Tempest is built in three phases (village, trade town, festival capital); Dwargon is carved into the mountain. Their audit status is in the place pages [tempest](places/tempest.md) and [dwargon](places/dwargon.md).

| Blueprint | Size (x, y, z) | Dimension | Preview | Place page | Status in the world (19/11/2026) |
|---|---|---|---|---|---|
| `tempest` | 91 x 40 x 91 | - | <img src="../previews/tempest-iso.png" width="200" alt="tempest"> | [tempest](places/tempest.md) | **ISSUE (medium).** Lore: Tempest stands in an open grass clearing with beach sand and a lake to the west; the forest only starts 100+ blocks away (the anchor's stored biome is tensura:ancient_forest, but the surface reads as plains). Known; fix in progress. Build itself is perfect: verify 100.00 %, 0 air under the footprint, 16 water cells in the box (the pond). |
| `tempest_town` | 137 x 40 x 137 | - | <img src="../previews/tempest_town-iso.png" width="200" alt="tempest_town"> | [tempest](places/tempest.md) | **ISSUE (medium).** Lore: Tempest stands in an open grass clearing with beach sand and a lake to the west; the forest only starts 100+ blocks away (the anchor's stored biome is tensura:ancient_forest, but the surface reads as plains). Known; fix in progress. Build itself is perfect: verify 100.00 %, 0 air under the footprint, 16 water cells in the box (the pond). |
| `tempest_city` | 191 x 40 x 191 | - | <img src="../previews/tempest_city-iso.png" width="200" alt="tempest_city"> | [tempest](places/tempest.md) | **ISSUE (medium).** Lore: Tempest stands in an open grass clearing with beach sand and a lake to the west; the forest only starts 100+ blocks away (the anchor's stored biome is tensura:ancient_forest, but the surface reads as plains). Known; fix in progress. Build itself is perfect: verify 100.00 %, 0 air under the footprint, 16 water cells in the box (the pond). |
| `dwargon` | 148 x 92 x 168 | - | <img src="../previews/dwargon-iso.png" width="200" alt="dwargon"> | [dwargon](places/dwargon.md) | **ISSUE (high).** Inside the city: 2,253 cells that the structure defines as air are WATER (x 1868..1905, z -658..-603, y 146..201), concentrated in the throne-hall area round 1880 -648 / -656 (560+ cells each); red_carpet -> water x16 at the throne (1876..1880 150 -647). The ... LAVA in the gate court: 68 cells (x 1835..1843, z -534..-522, y 146..150), about 40 blocks WSW of the gate (1878 146 -544), visible on the map next to the approach road. |

### Other dimensions and Life 1

Not on the Tensura map: the Dwelling of the Spirits (`ttl:spirit_domain`), the Walpurgis Hall (`ttl:walpurgis`), the Spirit Corridor, Wayfarer's Rest and the Mortal Realm waypoints (`ttl:mortal_realm`), and the test hut. See [design/lore/](../../design/lore/).

| Blueprint | Size (x, y, z) | Dimension | Preview | Place page | Status in the world (19/11/2026) |
|---|---|---|---|---|---|
| `spirit_dwelling` | 89 x 64 x 89 | ttl:spirit_domain | <img src="../previews/spirit_dwelling-iso.png" width="200" alt="spirit_dwelling"> | - | Not in the audit (not on the Tensura map). |
| `walpurgis_hall` | 123 x 44 x 97 | ttl:walpurgis | <img src="../previews/walpurgis_hall-iso.png" width="200" alt="walpurgis_hall"> | - | Not in the audit (not on the Tensura map). |
| `spirit_corridor_hall` | 31 x 22 x 31 | - | <img src="../previews/spirit_corridor_hall-iso.png" width="200" alt="spirit_corridor_hall"> | - | Not in the audit (not on the Tensura map). |
| `mortal_spawn` | 39 x 22 x 39 | - | <img src="../previews/mortal_spawn-iso.png" width="200" alt="mortal_spawn"> | - | Not in the audit (not on the Tensura map). |
| `mortal_ferry` | 79 x 16 x 77 | ttl:mortal_realm | <img src="../previews/mortal_ferry-iso.png" width="200" alt="mortal_ferry"> | - | Not in the audit (not on the Tensura map). |
| `mortal_keep` | 75 x 22 x 73 | ttl:mortal_realm | <img src="../previews/mortal_keep-iso.png" width="200" alt="mortal_keep"> | - | Not in the audit (not on the Tensura map). |
| `mortal_market` | 73 x 25 x 69 | ttl:mortal_realm | <img src="../previews/mortal_market-iso.png" width="200" alt="mortal_market"> | - | Not in the audit (not on the Tensura map). |
| `mortal_mine` | 73 x 24 x 68 | ttl:mortal_realm | <img src="../previews/mortal_mine-iso.png" width="200" alt="mortal_mine"> | - | Not in the audit (not on the Tensura map). |
| `mortal_pilgrim_shrine` | 69 x 26 x 70 | ttl:mortal_realm | <img src="../previews/mortal_pilgrim_shrine-iso.png" width="200" alt="mortal_pilgrim_shrine"> | - | Not in the audit (not on the Tensura map). |
| `mortal_tower` | 71 x 34 x 73 | ttl:mortal_realm | <img src="../previews/mortal_tower-iso.png" width="200" alt="mortal_tower"> | - | Not in the audit (not on the Tensura map). |
| `test_hut` | 5 x 6 x 5 | ttl:spirit_corridor | <img src="../previews/test_hut-iso.png" width="200" alt="test_hut"> | - | Not in the audit (not on the Tensura map). |

### The ten Trials of the Soul

Small arenas in the Spirit Corridor (`blueprints/trial_*.py`, shared code in `_arena.py`), one per trial of the reincarnation. Previews in [docs/previews/](../previews/): `trial_creation`, `trial_deceit`, `trial_dominion`, `trial_freedom`, `trial_hunger`, `trial_knowledge`, `trial_protection`, `trial_strength`, `trial_survival`, `trial_vengeance`. Not part of the world map.

## 6. Builds that are open (the creative backlog)

| Build | What is wanted |
|---|---|
| [`ogre_village_ruin`](places/ogre_village_ruin.md) | A new blueprint: the burnt hidden ogre village (the kijin homeland). Today only one burnt tower stands. |
| [`orc_camp`](places/orc_camp.md) | A new blueprint: the Orc Lord's war camp at the Lake Siss marsh (Tensura's jigsaw stand-in failed to place). |
| `wayfarers_camp`, `rookie_camp`, `old_well`, road camps | Small camps and shelters (suggestions in the place pages). |
| Later phases | More detail for existing builds: see the status column and [tasks.md](tasks.md). |

Back to the [knowledge pack](README.md).
