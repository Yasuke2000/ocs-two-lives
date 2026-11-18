"""Siltrosso, a Rosso audience house and enclosed counting court. SIZE (73, 37, 65).
Anchor (36, 5, 52) looks north from the public entrance. Three template slabs cut across z.
Materials: brick tile, pink granite, calcite plaster, dark oak, red terracotta and stone.
Granbell's influence and Mariabell's financial plans are canon. The house, its rose court
and its figures of account are our interpretation. References in design/lore/siltrosso.md.
"""
from _town_lib import M, Town, lantern_hung, slab, stair

SIZE = (73, 37, 65)
PARTS = [0, 22, 44]
G = 4


def audience_house(t):
    t.fill(17, G, 9, 55, G, 25, M("polished_granite"))
    t.ring(17, 9, 55, 25, 5, 16, M("calcite"))
    for y in (5, 11, 16):
        t.ring(17, 9, 55, 25, y, y, M("polished_granite"))
    # Clerks use the gallery to fetch ledgers. Its west stair rises toward the rear.
    t.fill(18, 11, 10, 54, 11, 14, M("dark_oak_planks"))
    for x in range(23, 54):
        t.put(x, 12, 14, M("dark_oak_fence[east=true,west=true]"))
    for i in range(7):
        z = 21 - i
        if i:
            t.fill(19, 5, z, 21, 4 + i, z, M("dark_oak_planks"))
        t.fill(19, 5 + i, z, 21, 5 + i, z, stair("dark_oak", "north"))
    for x in (24, 31, 38, 45, 52):
        t.fill(x - 1, 12, 10, x + 1, 14, 10, M("bookshelf"))
        for z in (9, 25):
            t.fill(x - 1, 13, z, x + 1, 15, z, M("light_gray_stained_glass"))
            t.put(x, 15, z, M("chiseled_stone_bricks"))
        for z in (17, 21):
            if x in (24, 45):
                t.put(x, 5, z, stair("dark_oak", "west"))
                t.put(x + 1, 5, z, slab("dark_oak", "top"))
    for x in (21, 28, 36, 44, 51):
        t.clear(x - 1, 5, 25, x + 1, 8, 25)
        t.put(x - 1, 8, 25, stair("polished_granite", "west", "top"))
        t.put(x + 1, 8, 25, stair("polished_granite", "east", "top"))
    t.gable(17, 9, 55, 25, 17, "brick", "x", M("red_terracotta"))
    for z in (17, 22):
        t.fill(17, 15, z, 55, 15, z, M("stripped_dark_oak_log[axis=x]"))
        for x in (25, 36, 47):
            t.put(x, 14, z, lantern_hung())
    # Side windows and a stepped central dormer make the audience hall legible from the lane.
    for x in (17, 55):
        for z in (13, 20):
            for y in (6, 12):
                t.fill(x, y, z, x, y + 2, z + 1, M("light_gray_stained_glass"))
        t.put(x, 20, 17, M("chiseled_stone_bricks"))
    t.fill(32, 17, 24, 40, 20, 24, M("red_terracotta"))
    t.fill(32, 17, 21, 32, 20, 23, M("red_terracotta"))
    t.fill(40, 17, 21, 40, 20, 23, M("red_terracotta"))
    for x in (34, 36, 38):
        t.fill(x, 17, 24, x, 19, 24, M("light_gray_stained_glass"))
    t.gable(32, 20, 40, 24, 21, "slate", "z", M("calcite"))
    t.put(36, 22, 24, M("chiseled_stone_bricks"))
    # High, flanking stone chimneys with exposed collars break the long tiled ridge.
    for x, z in ((21, 14), (50, 16)):
        t.fill(x, 5, z, x + 1, 25, z + 1, M("bricks"))
        t.fill(x - 1, 25, z - 1, x + 2, 25, z + 2, slab("brick", "top"))
        for dx in (0, 1):
            t.put(x + dx, 26, z, M("flower_pot"))
    # The covered loggia is four bays wide with a planted terrace visible from above.
    t.fill(15, 10, 25, 57, 10, 30, M("smooth_sandstone"))
    for x in (16, 26, 36, 46, 56):
        t.fill(x, 5, 29, x, 9, 29, M("polished_granite"))
        for dx, face in ((-1, "east"), (1, "west")):
            t.put(x + dx, 9, 29, stair("polished_granite", face, "top"))
    for x in (21, 31, 41, 51):
        t.put(x, 9, 29, lantern_hung())
        t.fill(x - 1, 11, 28, x + 1, 11, 28, M("oak_leaves[persistent=true]"))
    t.fill(15, 11, 30, 57, 11, 30, slab("polished_granite"))


def court(t):
    # Individual desks face the passage. Visitors enter beneath the two gabled offices.
    for x in (10, 47):
        t.house(x, 35, x + 15, 45, "e" if x == 10 else "w", 1,
                plaster="white_terracotta", roof="brick", furnish=False)
        # The shared house puts a window shutter in front of these narrow end doors.
        outside_x = 26 if x == 10 else 46
        t.put(outside_x, 6, 40, M("air"))
        for z in (38, 42):
            t.put(x + 7, 5, z, stair("dark_oak", "east"))
            t.put(x + 6, 5, z, slab("dark_oak", "top"))
        t.put(x + 2, 5, 36, M("lectern[facing=south]"))
    # The scale is a two-colour paving mosaic between the offices, visible from the loggia.
    for z in range(33, 41):
        t.put(36, G, z, M("polished_blackstone"))
    for x in range(29, 44):
        t.put(x, G, 34, M("polished_blackstone"))
    for center in (30, 42):
        for dx in (-2, 2):
            t.fill(center + dx, G, 35, center + dx, G, 37, M("polished_blackstone"))
        t.fill(center - 1, G, 38, center + 1, G, 38, M("red_terracotta"))
    t.fill(33, G, 41, 39, G, 41, M("polished_blackstone"))
    for x0 in (7, 56):
        for z0 in (20, 26):
            t.fill(x0, G, z0, x0 + 8, G, z0 + 2, M("grass_block"))
            t.fill(x0, 5, z0, x0 + 8, 5, z0, M("oak_leaves[persistent=true]"))
            for x in range(x0 + 1, x0 + 8, 2):
                t.put(x, 5, z0 + 1, M("rose_bush[half=lower]"))
                t.put(x, 6, z0 + 1, M("rose_bush[half=upper]"))
    for x in (27, 45):
        t.fill(x, 5, 48, x, 8, 48, M("polished_granite"))
        t.put(x, 9, 48, M("chiseled_stone_bricks"))
        t.put(x, 10, 48, M("lantern[hanging=false]"))
    for x, z in ((7, 33), (64, 33), (12, 52), (60, 52), (32, 58), (40, 58)):
        t.lamp(x, z, 2, post="dark_oak_fence")


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(7, 24, 65, 48, "plaza")
    t.pave(32, 48, 40, 64, "street")
    t.pave(3, 30, 69, 32, "cobble")
    t.pave(10, 8, 16, 22, "street")
    audience_house(t)
    court(t)
    for x, z, h in ((8, 10, 6), (61, 10, 7), (6, 52, 6), (66, 54, 5), (21, 57, 5), (51, 58, 6)):
        t.tree(x, z, "oak", h, 2)
    # The estate lane narrows to two wheel tracks in the grass outside the gate.
    for z in range(56, 65):
        half = 4 if z < 60 else 3
        for x in range(32, 41):
            offset = abs(x - 36)
            surface = "grass_block" if offset > half else "coarse_dirt" if offset == 2 else "gravel"
            t.put(x, G, z, M(surface))
    # A continuous half-tile ridge keeps lamps off the long red roofs.
    for (x, y, z), state in list(bp.blocks.items()):
        if y >= 14 and state in (M("bricks"), M("deepslate_tiles")) and t.get(x, y + 1, z) == M("air"):
            tile = "brick" if state == M("bricks") else "deepslate_tile"
            t.put(x, y + 1, z, slab(tile))
    t.light(lambda x, z: 5 <= x <= 67 and 7 <= z <= 50 or 30 <= x <= 42 and z > 49)
    t.check_support()
