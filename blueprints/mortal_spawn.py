"""Wayfarer's Rest: where every new soul starts Life 1 in the Mortal Realm (a humble human hamlet square).

Placed by life/mortal_spawn.js centred on the surface at 0, 0. Layers 0-5 are a foundation (retaining
wall around an earth core) so it sits on any terrain; layer 6 is the plaza; layers 7-21 are cleared so
hills don't bury it. Players arrive south of the shrine, at blueprint (14, 7, 19).
"""

SIZE = (29, 22, 29)
C = 14
PLAZA = 6
AIR = "minecraft:air"


def build(bp):
    # Foundation: earth core inside a stone retaining wall.
    bp.fill(0, 0, 0, 28, PLAZA - 1, 28, "minecraft:dirt")
    bp.box(0, 0, 0, 28, PLAZA, 28, "minecraft:stone_bricks")
    bp.fill(1, PLAZA, 1, 27, PLAZA, 27, "minecraft:grass_block")

    # The square: cobble rim, andesite and stone-brick paving, four paths out.
    bp.disc(C, PLAZA, C, 12.5, "minecraft:cobblestone")
    bp.disc(C, PLAZA, C, 11.5, "minecraft:polished_andesite")
    for x in range(1, 28):
        for z in range(1, 28):
            if bp.blocks.get((x, PLAZA, z)) == "minecraft:polished_andesite" and (x + z) % 2 == 0:
                bp.set(x, PLAZA, z, "minecraft:stone_bricks")
    for i in range(1, 28):
        for w in (-1, 0, 1):
            for x, z in ((C + w, i), (i, C + w)):
                if bp.blocks.get((x, PLAZA, z)) == "minecraft:grass_block":
                    bp.set(x, PLAZA, z, "minecraft:dirt_path")

    # Shrine: a roofed 5x5 with a bell, where the Voice first speaks.
    bp.fill(C - 2, PLAZA, C - 2, C + 2, PLAZA, C + 2, "minecraft:chiseled_stone_bricks")
    for x, z in ((C - 2, C - 2), (C + 2, C - 2), (C - 2, C + 2), (C + 2, C + 2)):
        bp.pillar(x, z, PLAZA + 1, PLAZA + 4, "minecraft:stripped_spruce_log[axis=y]")
    bp.fill(C - 3, PLAZA + 5, C - 3, C + 3, PLAZA + 5, C + 3, "minecraft:spruce_slab[type=bottom]")
    bp.fill(C - 2, PLAZA + 5, C - 2, C + 2, PLAZA + 5, C + 2, "minecraft:spruce_planks")
    bp.set(C, PLAZA + 6, C, "minecraft:spruce_slab[type=bottom]")
    bp.set(C, PLAZA + 4, C, "minecraft:bell[attachment=ceiling,facing=north]")
    bp.set(C, PLAZA + 1, C - 1, "minecraft:lectern[facing=south]")

    # Well (north-west).
    wx, wz = C - 8, C - 7
    bp.fill(wx - 1, PLAZA, wz - 1, wx + 1, PLAZA + 1, wz + 1, "minecraft:cobblestone")
    bp.set(wx, PLAZA, wz, "minecraft:water")
    bp.set(wx, PLAZA + 1, wz, "minecraft:water")
    for x, z in ((wx - 1, wz - 1), (wx + 1, wz - 1), (wx - 1, wz + 1), (wx + 1, wz + 1)):
        bp.pillar(x, z, PLAZA + 2, PLAZA + 3, "minecraft:spruce_fence")
    bp.fill(wx - 1, PLAZA + 4, wz - 1, wx + 1, PLAZA + 4, wz + 1, "minecraft:spruce_slab[type=bottom]")

    # Campfire with log benches (north-east).
    fx, fz = C + 8, C - 7
    bp.set(fx, PLAZA + 1, fz, "minecraft:campfire[lit=true,facing=north]")
    bp.set(fx, PLAZA + 1, fz - 2, "minecraft:spruce_stairs[facing=south]")
    bp.set(fx, PLAZA + 1, fz + 2, "minecraft:spruce_stairs[facing=north]")
    bp.set(fx - 2, PLAZA + 1, fz, "minecraft:spruce_stairs[facing=east]")
    bp.set(fx + 2, PLAZA + 1, fz, "minecraft:spruce_stairs[facing=west]")

    # Supplies (south-west and south-east corners): crates and hay.
    for x, z in ((C - 9, C + 8), (C - 8, C + 9), (C + 9, C + 8)):
        bp.set(x, PLAZA + 1, z, "minecraft:barrel[facing=up]")
    bp.set(C + 8, PLAZA + 1, C + 9, "minecraft:hay_block[axis=y]")
    bp.set(C + 8, PLAZA + 2, C + 9, "minecraft:hay_block[axis=x]")

    # Lamp posts around the square.
    for x, z in bp.around(C, C, 10.5, 8, start_deg=22.5):
        bp.pillar(x, z, PLAZA + 1, PLAZA + 2, "minecraft:spruce_fence")
        bp.set(x, PLAZA + 3, z, "minecraft:lantern[hanging=false]")

    # Flower beds in the grass corners.
    flowers = ["minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower", "minecraft:oxeye_daisy"]
    for i, (x, z) in enumerate(((2, 2), (26, 2), (2, 26), (26, 26))):
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(x + dx, PLAZA + 1, z + dz, flowers[(i + dx + dz) % len(flowers)])

    # Clear the space above so terrain never buries the square.
    for x in range(29):
        for z in range(29):
            for y in range(PLAZA + 1, 22):
                if (x, y, z) not in bp.blocks:
                    bp.set(x, y, z, AIR)
