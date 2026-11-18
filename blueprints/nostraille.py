"""Nostraille's wool market, SIZE (72, 33, 64), anchor (36, 5, 43) in the southern market street.

The Western Council map is a geographical reference. The market is our interpretation of the pack's
hill kingdom. Chipping Campden's open arcades and repeated gables inform the hall. See
design/lore/nostraille.md. Sandstone, granite, stone-brick roofing, oak, wool and glass form the yard.
"""
from _town_lib import M, Town, lantern_hung, log, slab, stair, wall_banner

SIZE = (72, 33, 64)
PARTS = [0, 32]
G = 4


def hall(t):
    # Five open arches run each side of two parallel ridge roofs. The columns down the middle
    # carry the valley where the rafters meet and leave the ends open for the wool carts.
    t.pave(12, 12, 57, 32, "cobble")
    for x in range(14, 55, 8):
        for z in (13, 22, 31):
            t.fill(x - 1, 5, z, x + 1, 5, z, M("cut_sandstone"))
            t.fill(x, 6, z, x, 10, z, M("smooth_sandstone"))
            t.fill(x - 1, 10, z, x + 1, 10, z, M("chiseled_sandstone"))
        t.fill(x, 13, 13, x, 13, 31, log("stripped_oak_log", "z"))
        if x < 54:
            for z in (13, 31):
                t.fill(x + 1, 11, z, x + 7, 13, z, M("cut_sandstone"))
                t.clear(x + 2, 11, z, x + 6, 11, z)
                t.clear(x + 3, 12, z, x + 5, 12, z)
                t.put(x + 1, 10, z, stair("smooth_sandstone", "west", "top"))
                t.put(x + 7, 10, z, stair("smooth_sandstone", "east", "top"))
    for z in (13, 22, 31):
        t.fill(14, 14, z, 54, 14, z, log("dark_oak_log", "x"))
    for z in (13, 22):
        t.gable(14, z, 54, z + 9, 15, "stone", "x", M("cut_sandstone"))
    # Three stepped south gables with recessed twin lights in a dark oak mullion.
    for x in (18, 34, 50):
        t.gable(x - 3, 26, x + 3, 32, 15, "stone", "z", M("smooth_sandstone"))
        t.fill(x - 1, 15, 32, x + 1, 16, 32, M("brown_stained_glass"))
        t.fill(x, 15, 32, x, 16, 32, log("stripped_dark_oak_log"))
        t.fill(x - 2, 14, 32, x + 2, 14, 32, slab("smooth_sandstone", "top"))
    for x in (18, 26, 34, 42, 50):
        for z in (17, 27):
            t.fill(x, 13, z, x + 4, 13, z, log("dark_oak_log", "x"))
            t.put(x + 2, 12, z, lantern_hung())
    # The balance has two hanging trays for wool and counterweights. Its front is open to visitors.
    for x in (29, 39):
        t.fill(x, 5, 23, x, 10, 23, log("oak_log"))
    t.fill(29, 10, 23, 39, 10, 23, log("stripped_oak_log", "x"))
    for x in (32, 36):
        t.fill(x, 8, 23, x, 9, 23, M("chain"))
        t.fill(x - 1, 7, 23, x + 1, 7, 23, slab("oak", "top"))
    for x, colour in ((17, "white"), (24, "brown"), (44, "gray"), (50, "light_gray")):
        t.fill(x, 5, 16, x + 2, 6, 18, M(colour + "_wool"))
        t.put(x + 1, 7, 17, M(colour + "_wool"))


def cloth_yard(t):
    # Twin rows of free-standing tenter frames, each with a different piece of drying cloth.
    for x, colour in ((10, "red"), (20, "orange"), (49, "light_gray"), (59, "brown")):
        for z in (47, 54):
            t.fill(x, 5, z, x, 9, z, log("stripped_oak_log"))
            t.fill(x + 6, 5, z, x + 6, 9, z, log("stripped_oak_log"))
            t.fill(x, 9, z, x + 6, 9, z, log("spruce_log", "x"))
            for xx in range(x + 1, x + 6):
                t.put(xx, 8, z, M(colour + "_wool"))
                t.put(xx, 7, z, M(colour + "_wool"))
    for x, z in ((3, 8), (6, 37), (63, 38), (65, 18), (30, 55), (43, 56)):
        t.tree(x, z, "oak", 5, 2)
    for x in (29, 43):
        t.lamp(x, 42, 3)
        t.lamp(x, 50, 3)
    for x in (14, 54):
        t.put(x, 8, 32, wall_banner("orange", "south"))


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(4, 36, 68, 42, "street")
    t.pave(31, 32, 40, 63, "street")
    t.pave(10, 29, 56, 35, "plaza")
    # Cart tracks leave the broad market street as pairs of ruts through the meadow.
    for x in (*range(8), *range(65, 72)):
        for z in (38, 40):
            t.put(x, G, z, M("coarse_dirt"))
    for z in range(56, 64):
        for x in range(31, 41):
            if abs(x - 35.5) > 4 - (z - 55) / 3:
                t.put(x, G, z, M("grass_block"))
        for x in (34, 37):
            t.put(x, G, z, M("coarse_dirt"))
    hall(t)
    cloth_yard(t)
    # Pegged stone ridge caps leave a continuous silhouette above the arcade.
    for (x, y, z), state in list(bp.blocks.items()):
        if state == M("stone_bricks") and y >= 15 and t.get(x, y + 1, z) == M("air"):
            t.put(x, y + 1, z, slab("stone_brick"))
    for x, z in ((8, 6), (60, 8), (64, 32), (4, 49), (18, 57), (56, 58)):
        for dx, dz, flower in ((0, 0, "cornflower"), (1, 1, "oxeye_daisy"), (2, -1, "short_grass")):
            if t.get(x + dx, G, z + dz) == M("grass_block"):
                t.put(x + dx, 5, z + dz, M(flower))
    t.light(lambda x, z: 9 <= x <= 65 and 10 <= z <= 55)
    t.check_support()
