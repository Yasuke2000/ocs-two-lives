"""Wayfarer's Rest, a human coaching yard in the Mortal Realm, SIZE 39 x 22 x 39.

The anchor at local (14, 6, 14) is the ground under the shrine at world x/z 0/0.
Arrival is local (14, 7, 19), world (0.5, stored walking Y, 5.5), facing north.
Spruce and oak framing, plaster, fieldstone, packed earth and planted verges.
Sources and the inventory of visual references are in design/lore/mortal_spawn.md.
"""
from _dwargon_lib import dark_spots
from _footprint import settlement_footprint

SIZE = (39, 22, 39)
C = 14
PLAZA = 6
AIR = "minecraft:air"


def verge(x, z):
    # Keep the old square under turf on upgrades. Beyond it, follow the buildings
    # and the four lane ends, leaving the unbuilt corner woods in place.
    return (x <= 28 and z <= 28
            or ((x - 29) / 9.5) ** 2 + ((z - 9) / 11.5) ** 2 <= 1
            or 21 <= x <= 36 and 2 <= z <= 15
            or ((x - 18) / 20) ** 2 + ((z - 25) / 12) ** 2 <= 1
            or 2 <= x <= 11 and 24 <= z <= 35
            or 20 <= x <= 31 and 23 <= z <= 36
            or abs(x - 14) <= 2 or abs(z - 20) <= 2)


def landscape(bp):
    for z in range(SIZE[2]):
        for x in range(SIZE[0]):
            if not verge(x, z):
                continue
            # Replace the exposed stone rim of v1 with earth even on existing saves.
            base = 0 if (x in (0, 28) and z <= 28 or z in (0, 28) and x <= 28) else PLAZA - 1
            bp.pillar(x, z, base, PLAZA - 1, "minecraft:dirt")
            seed = (x * 31 + z * 23 + x * z * 7) % 19
            lane = (abs(z - 20) <= 1 or abs(x - 14) <= 1 and (z <= 8 or z >= 17)
                    or 6 <= x <= 14 and abs(z - 8) <= 1
                    or abs(x - 10) <= 1 and 8 <= z <= 19
                    or abs(x - 18) <= 1 and 8 <= z <= 20
                    or abs(z - 9) <= 1 and 14 <= x <= 18
                    or 28 <= x <= 30 and 12 <= z <= 20
                    or 6 <= x <= 8 and 15 <= z <= 26
                    or 24 <= x <= 26 and 20 <= z <= 23)
            square = ((x - 14) / 5.7) ** 2 + ((z - 15) / 5.2) ** 2 < 1
            if square:
                surface = ("andesite", "cobblestone", "stone_bricks", "gravel")[seed % 4]
            elif lane:
                surface = "gravel" if seed == 0 else "coarse_dirt" if seed < 5 else "dirt_path"
            else:
                surface = "grass_block"
            bp.set(x, PLAZA, z, "minecraft:" + surface)
            bp.pillar(x, z, PLAZA + 1, SIZE[1] - 1, AIR)
            if not lane and not square and seed == 1:
                bp.set(x, 7, z, "minecraft:short_grass")


def shrine(bp):
    bp.fill(12, PLAZA, 12, 16, PLAZA, 16, "minecraft:stone_bricks")
    for x in (12, 16):
        for z in (12, 16):
            bp.set(x, 7, z, "minecraft:cobblestone")
            bp.pillar(x, z, 8, 11, "minecraft:stripped_oak_log")
    for z in (12, 14, 16):
        bp.fill(12, 11, z, 16, 11, z, "minecraft:stripped_spruce_log[axis=x]")
    for x in range(10, 19):
        y = 15 - abs(x - C)
        roof = ("spruce_slab[type=bottom]" if x == C else
                "spruce_stairs[facing=" + ("east" if x < C else "west") + "]")
        bp.fill(x, y, 11, x, y, 17, "minecraft:" + roof)
    bp.fill(14, 14, 11, 14, 14, 17, "minecraft:stripped_oak_log[axis=z]")
    for z in (12, 16):
        bp.pillar(C, z, 12, 13, "minecraft:oak_fence")
    bp.set(C, 10, C, "minecraft:bell[attachment=ceiling,facing=north]")
    bp.set(C, 7, 13, "minecraft:lectern[facing=south]")
    for x in (13, 15):
        bp.set(x, 10, 12, "minecraft:lantern[hanging=true]")


def well_and_notices(bp):
    bp.fill(5, 6, 4, 7, 7, 6, "minecraft:mossy_cobblestone")
    bp.set(6, 6, 5, "minecraft:water")
    bp.set(6, 7, 5, "minecraft:oak_trapdoor[half=bottom]")
    for x in (5, 7):
        bp.pillar(x, 5, 8, 9, "minecraft:oak_fence")
    bp.fill(4, 10, 4, 8, 10, 6, "minecraft:spruce_slab[type=bottom]")
    bp.fill(5, 10, 5, 7, 10, 5, "minecraft:stripped_oak_log[axis=x]")
    bp.set(6, 9, 5, "minecraft:lantern[hanging=true]")
    for x in (5, 9):
        bp.pillar(x, 13, 7, 10, "minecraft:stripped_spruce_log")
    bp.fill(6, 8, 13, 8, 10, 13, "minecraft:oak_planks")
    bp.fill(4, 11, 12, 10, 11, 14, "minecraft:spruce_slab[type=bottom]")
    for x in (6, 8):
        bp.set(x, 9, 14, "minecraft:oak_wall_sign[facing=south]")
    bp.set(7, 10, 14, "minecraft:lantern[hanging=true]")
    bp.pillar(17, 23, 7, 10, "minecraft:stripped_oak_log")
    for x, z, facing in ((17, 22, "north"), (18, 23, "east"), (17, 24, "south"), (16, 23, "west")):
        bp.set(x, 9, z, "minecraft:oak_wall_sign[facing=" + facing + "]")
    bp.set(17, 11, 23, "minecraft:lantern")


def edges(bp):
    for x, z, length in ((1, 16, 4), (30, 16, 5), (3, 35, 6), (23, 36, 5)):
        for dx in range(length):
            block = "mossy_cobblestone" if dx in (0, length - 1) else "cobblestone_slab[type=bottom]"
            bp.set(x + dx, 7, z, "minecraft:" + block)
        bp.set(x, 8, z, "minecraft:lantern")
    # A pollarded oak shelters the roadside well. The low hedges break up the old
    # square's stone boundary without blocking the driver's view at the crossroads.
    bp.pillar(3, 6, 7, 10, "minecraft:oak_log")
    for dx, dz, height in ((0, 0, 12), (1, 0, 11), (-1, 0, 11), (0, 1, 11),
                           (0, -1, 11), (1, -1, 10), (-1, 1, 10)):
        bp.pillar(3 + dx, 6 + dz, 10 if dx or dz else 11, height,
                  "minecraft:oak_leaves[persistent=true]")
    for x, z in ((1, 10), (1, 11), (2, 11), (2, 12), (19, 3), (20, 3),
                 (20, 4), (33, 22), (34, 22), (34, 23), (12, 34), (12, 35)):
        bp.set(x, 7, z, "minecraft:oak_leaves[persistent=true]")
    # Verge stones also mark a lane when approached at night from outside the yard.
    for x, z in ((16, 2), (36, 18), (16, 36), (1, 2), (36, 2), (32, 30)):
        bp.set(x, 7, z, "minecraft:mossy_cobblestone")
        bp.set(x, 8, z, "minecraft:lantern")


def rest_hall(bp):
    """Timber coaching inn with a covered south porch, two guest beds and a screened hearth."""
    beam = "minecraft:stripped_spruce_log"
    plaster = "minecraft:white_terracotta"
    sill = "minecraft:cobblestone"
    planks = "minecraft:spruce_planks"
    # Floor and framing. The exterior ground and the threshold share the same elevation.
    bp.fill(23, PLAZA, 3, 35, PLAZA, 11, sill)
    bp.fill(24, PLAZA, 4, 34, PLAZA, 10, planks)
    for z in (3, 11):
        bp.fill(23, 7, z, 35, 7, z, sill)
        bp.fill(23, 8, z, 35, 10, z, plaster)
        bp.fill(23, 10, z, 35, 10, z, beam + "[axis=x]")
        for x in (23, 27, 31, 35):
            bp.pillar(x, z, 7, 10, beam + "[axis=y]")
        for x in (25, 33):
            bp.set(x, 8, z, "minecraft:glass")
    for x in (23, 35):
        bp.fill(x, 7, 4, x, 7, 10, sill)
        bp.fill(x, 8, 4, x, 9, 10, plaster)
        bp.fill(x, 10, 3, x, 10, 11, beam + "[axis=z]")
        bp.pillar(x, 7, 7, 15, beam + "[axis=y]")
        for z in (5, 9):
            bp.set(x, 8, z, "minecraft:glass")
    # Closed gables under a spruce-shingle roof, with a single slab ridge.
    for step in range(5):
        y = 11 + step
        north, south = 2 + step, 12 - step
        for x in (23, 35):
            bp.fill(x, y, north + 1, x, y, south - 1, plaster)
            bp.set(x, y, 7, beam + "[axis=y]")
        bp.fill(22, y, north, 36, y, north, "minecraft:spruce_stairs[facing=south]")
        bp.fill(22, y, south, 36, y, south, "minecraft:spruce_stairs[facing=north]")
    bp.fill(22, 16, 7, 36, 16, 7, "minecraft:spruce_slab[type=bottom]")
    # Three exposed ceiling ties. The roof space remains visible from the common room.
    for x in (25, 29, 33):
        bp.fill(x, 10, 4, x, 10, 10, beam + "[axis=z]")
        bp.set(x, 9, 8, "minecraft:lantern[hanging=true]")
    # South-facing entrance under a lean-to. The middle bay opens onto the shrine path.
    bp.fill(26, PLAZA, 12, 32, PLAZA, 14, planks)
    for half, y in (("lower", 7), ("upper", 8)):
        bp.set(29, y, 11, "minecraft:spruce_door[facing=south,half=" + half + ",hinge=left]")
    bp.set(29, PLAZA, 11, planks)
    for x in (26, 32):
        bp.pillar(x, 14, 7, 9, beam + "[axis=y]")
    bp.fill(26, 10, 14, 32, 10, 14, beam + "[axis=x]")
    bp.fill(26, 11, 12, 32, 11, 12, planks)
    bp.fill(26, 11, 13, 32, 11, 13, "minecraft:spruce_stairs[facing=north]")
    bp.fill(26, 11, 14, 32, 11, 14, "minecraft:spruce_slab[type=bottom]")
    bp.set(27, 9, 14, "minecraft:lantern[hanging=true]")
    bp.set(31, 9, 14, "minecraft:lantern[hanging=true]")
    # Two guest beds against the north wall, with a low screen and a clear aisle.
    for x, colour in ((25, "blue"), (28, "light_gray")):
        for part, z in (("head", 4), ("foot", 5)):
            bp.set(x, 7, z, f"minecraft:{colour}_bed[facing=north,part={part}]")
    bp.set(27, 7, 4, "minecraft:barrel[facing=up]")
    bp.fill(24, 7, 6, 26, 7, 6, "minecraft:oak_planks")
    bp.set(24, 8, 6, "minecraft:bookshelf")
    # Refectory bench and table leave an open west aisle and a direct route from the door.
    bp.fill(25, 7, 9, 27, 7, 9, "minecraft:spruce_stairs[facing=south]")
    bp.fill(25, 7, 8, 27, 7, 8, "minecraft:oak_slab[type=top]")
    bp.set(26, 8, 8, "minecraft:flower_pot")
    bp.fill(29, 7, 7, 29, 7, 10, "minecraft:brown_carpet")
    # Deep stone firebox. Solid sides, bars across the front and a covered flue
    # keep the functional campfire out of reach from every walkable direction.
    for x in (31, 33):
        bp.fill(x, 7, 3, x, 9, 5, "minecraft:stone_bricks")
    bp.fill(31, 7, 3, 33, 10, 3, "minecraft:stone_bricks")
    bp.set(32, 7, 4, "minecraft:campfire[facing=south,lit=true]")
    bp.fill(32, 7, 5, 32, 8, 5, "minecraft:iron_bars[east=true,west=true]")
    bp.fill(31, 9, 4, 33, 9, 5, "minecraft:stone_bricks")
    bp.pillar(32, 4, 10, 15, "minecraft:stone_bricks")
    bp.set(32, 16, 4, "minecraft:cobblestone_wall")
    bp.set(33, 7, 9, "minecraft:barrel[facing=west]")
    bp.set(33, 8, 9, "minecraft:lantern")


def travellers_yard(bp):
    """Two open horse bays, a cloth merchant's counter and the hamlet's dye garden."""
    ground = PLAZA
    post = "minecraft:stripped_oak_log[axis=y]"
    beam = "minecraft:stripped_oak_log[axis=x]"

    # The open-front shelter faces the square. The rear rails divide two horse bays.
    for x in range(3, 11):
        for z in range(24, 35):
            floor = "coarse_dirt" if (x + 3 * z) % 7 < 3 else "dirt_path"
            if z >= 30 and (x * z) % 5 < 2:
                floor = "packed_mud"
            bp.set(x, ground, z, "minecraft:" + floor)
    for z in (26, 33):
        for x in (3, 10):
            bp.pillar(x, z, ground + 1, ground + 4, post)
        bp.fill(3, ground + 4, z, 10, ground + 4, z, beam)
    for x in (3, 10):
        bp.fill(x, ground + 1, 27, x, ground + 1, 32, "minecraft:spruce_fence[north=true,south=true]")
    bp.fill(4, ground + 1, 33, 9, ground + 2, 33, "minecraft:spruce_planks")
    bp.fill(6, ground + 1, 30, 6, ground + 1, 32, "minecraft:spruce_fence[north=true,south=true]")
    bp.set(6, ground + 1, 29, post)

    # Wide eaves and a narrow timber ridge. The trusses are visible from the lane.
    for x in range(2, 12):
        pitch = min(x - 2, 11 - x)
        roof_y = ground + 4 + min(pitch, 3)
        if pitch < 4:
            face = "east" if x < 7 else "west"
            roof = f"minecraft:spruce_stairs[facing={face},half=bottom,shape=straight]"
        else:
            roof = "minecraft:spruce_slab[type=bottom]"
        bp.fill(x, roof_y, 25, x, roof_y, 34, roof)
        if roof_y > ground + 5:
            for z in (26, 33):
                bp.set(x, roof_y - 1, z, "minecraft:spruce_planks")
    for z in (26, 33):
        bp.pillar(7, z, ground + 5, ground + 6, post)
    bp.set(4, ground + 3, 26, "minecraft:lantern[hanging=true]")
    bp.set(9, ground + 3, 33, "minecraft:lantern[hanging=true]")

    # Hitching rail outside the second bay leaves the first entrance open to the road.
    for x in (8, 10):
        bp.set(x, ground + 1, 24, post)
    bp.set(9, ground + 1, 24, "minecraft:oak_fence[east=true,west=true]")

    # A single dye-cloth counter. Rolled samples leave most of its surface free.
    for x in (21, 28):
        for z in (24, 27):
            bp.pillar(x, z, ground + 1, ground + 3, post)
        bp.fill(x, ground + 4, 24, x, ground + 4, 27, "minecraft:stripped_oak_log[axis=z]")
    for z in (24, 27):
        bp.fill(21, ground + 4, z, 28, ground + 4, z, beam)
    for x in range(20, 30):
        wool = "minecraft:green_wool" if x % 4 in (0, 1) else "minecraft:white_wool"
        bp.fill(x, ground + 5, 23, x, ground + 5, 28, wool)
    bp.fill(22, ground + 1, 24, 27, ground + 1, 24, "minecraft:stripped_spruce_log[axis=x]")
    bp.set(22, ground + 2, 24, "minecraft:green_carpet")
    bp.set(23, ground + 2, 24, "minecraft:white_carpet")
    bp.set(27, ground + 3, 24, "minecraft:lantern[hanging=true]")

    # An irregular low stone edging and a gravel turn between two planting beds.
    for x in range(21, 32):
        for z in range(30, 36):
            path = x in (25, 26) or (x >= 27 and z == 32)
            bp.set(x, ground, z, "minecraft:gravel" if path else "minecraft:grass_block")
    for x in (21, 22, 23, 24, 27, 28, 30, 31):
        edge = "mossy_cobblestone_slab" if x % 3 == 0 else "cobblestone_slab"
        bp.set(x, ground + 1, 35, "minecraft:" + edge + "[type=bottom]")
    flowers = ((22, 31, "oxeye_daisy"), (23, 31, "cornflower"), (22, 32, "cornflower"),
               (23, 34, "azure_bluet"), (24, 33, "short_grass"), (27, 31, "poppy"),
               (28, 30, "short_grass"), (29, 31, "poppy"), (30, 33, "oxeye_daisy"),
               (29, 34, "azure_bluet"), (27, 34, "poppy"))
    for x, z, flower in flowers:
        bp.set(x, ground + 1, z, "minecraft:" + flower)


def build(bp):
    landscape(bp)
    shrine(bp)
    well_and_notices(bp)
    rest_hall(bp)
    travellers_yard(bp)
    edges(bp)
    dark = dark_spots(bp.blocks, bp.size, bp.blocks)
    if dark:
        raise ValueError(f"Unlit spawnable surfaces at Wayfarer's Rest: {dark}")


def outputs(bp):
    return {"pack/kubejs/server_scripts/ttl/generated/mortal_spawn_footprint.js":
            settlement_footprint(bp, "TtlMortalSpawnFootprint", "blueprints/mortal_spawn.py",
                                 PLAZA, [], (C, PLAZA + 1, 19), None, margin=0)}
