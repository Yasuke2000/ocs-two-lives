"""Mortal market square for Folk of the Realm. SIZE (73, 25, 69), anchor
(24, 4, 36) on the southern approach. Two timber houses, a tiled bell arcade and
cloth stalls enclose a cobbled square. A loom, composter, grindstone and lectern are
present. A weigh house, cattle yard and orchard extend along the east and south lanes.
PARTS start at z 0 and 35. Original plan inspired by vanilla village meetings. See design/lore/mortal_market.md.
"""
from _town_lib import M, Town, bed, lantern_hung, log, slab, stair

SIZE = (73, 25, 69)
PARTS = [0, 35]
G = 3


def stall(t, x, z, colour):
    for px in (x, x + 6):
        for pz in (z, z + 3):
            t.fill(px, 4, pz, px, 6, pz, M("oak_fence"))
    for dx in range(-1, 8):
        t.fill(x + dx, 7, z - 1, x + dx, 7, z + 4, M(f"{colour if dx % 3 else 'white'}_wool"))
    t.fill(x + 1, 4, z, x + 5, 4, z, log("stripped_spruce_log", "x"))
    t.put(x + 2, 6, z, lantern_hung())


def drovers_yard(t):
    # The stock lane comes in from the east while the field road reaches the south boundary.
    t.pave(47, 22, 72, 26, "street")
    t.pave(22, 44, 26, 68, "street")
    t.pave(25, 45, 65, 48, "cobble")
    t.pave(57, 23, 61, 47, "street")
    # An open-sided weigh house shelters a large suspended balance and the grain measure.
    for x in (50, 64):
        for z in (8, 19):
            t.fill(x, 4, z, x, 8, z, log("oak_log"))
    for x in (50, 64):
        t.fill(x, 8, 8, x, 8, 19, log("stripped_oak_log", "z"))
    t.fill(50, 8, 19, 64, 8, 19, log("stripped_oak_log", "x"))
    t.fill(50, 8, 8, 64, 8, 8, log("stripped_oak_log", "x"))
    t.fill(50, 8, 13, 64, 8, 13, log("stripped_oak_log", "x"))
    t.fill(50, G, 8, 64, G, 19, M("cobblestone"))
    t.gable(50, 8, 64, 19, 9, "brick", "x", M("white_terracotta"))
    t.put(57, 7, 13, M("chain[axis=y]"))
    t.fill(54, 6, 13, 60, 6, 13, log("dark_oak_log", "x"))
    for x in (54, 60):
        t.put(x, 5, 13, M("chain[axis=y]"))
        t.put(x, 4, 13, slab("oak", "top"))
    t.put(63, 4, 10, M("composter[level=0]"))
    for x in (52, 62):
        t.put(x, 7, 19, lantern_hung())
    # Reachable livestock enclosure, with a three-block opening toward the stock lane.
    for x in range(33, 66):
        for z in (50, 64):
            if z == 50 and 46 <= x <= 48:
                continue
            t.put(x, 4, z, M("oak_fence[east=true,west=true]"))
    for z in range(51, 64):
        for x in (33, 65):
            t.put(x, 4, z, M("oak_fence[north=true,south=true]"))
    for x in (33, 65):
        for z in (50, 64):
            t.put(x, 4, z, log("oak_log"))
    t.fill(37, 4, 61, 42, 4, 61, log("stripped_oak_log", "x"))
    t.fill(39, 4, 60, 40, 4, 60, M("packed_mud"))
    for x in (36, 43):
        t.fill(x, 4, 61, x, 5, 61, log("oak_log"))
    t.tree(61, 58, "oak", 5, 3)
    for x, z in ((34, 52), (44, 61), (48, 56), (56, 62), (53, 55), (63, 51)):
        t.put(x, 4, z, M("short_grass"))
    # Market gardeners enter by the western gate to unload beside the cloth traders.
    for x in (6, 13):
        for z in (49, 59):
            t.tree(x, z, "oak", 4 + x % 2, 2)
    for x in range(3, 18):
        t.put(x, 4, 64, M("oak_leaves[persistent=true]"))
    for z in range(46, 64):
        if z not in (52, 53, 54):
            t.put(18, 4, z, M("oak_leaves[persistent=true]"))
    t.pave(17, 52, 23, 54, "street")
    for x, z in ((48, 25), (63, 26), (57, 41), (41, 45), (28, 53), (20, 62)):
        t.lamp(x, z, 2, post="oak_fence")


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(13, 13, 35, 33, "plaza")
    t.pave(0, 22, 48, 26, "street")
    t.pave(22, 5, 26, 44, "street")
    # Front doors look onto the square. Beds are reachable from either side.
    for x, side in ((3, "e"), (34, "w")):
        t.house(x, 7, x + 11, 18, side, 1, roof="brick" if side == "e" else "spruce", furnish=False)
        door_z = (7 + 18) // 2
        approach_x = x + 12 if side == "e" else x - 1
        t.put(approach_x, 5, door_z, M("air"))
        t.put(x + 2, 4, 9, bed("white", "north", "head"))
        t.put(x + 2, 4, 10, bed("white", "north", "foot"))
        t.put(x + 7, 4, 13, stair("oak", "east"))
        t.put(x + 6, 4, 13, slab("oak", "top"))
    # Covered meeting bell and reading desk south of the houses' northern garden.
    for x in (19, 29):
        for z in (9, 14):
            t.fill(x, 4, z, x, 7, z, log("stripped_oak_log"))
    t.fill(19, 7, 14, 29, 7, 14, log("stripped_oak_log", "x"))
    t.fill(19, 7, 9, 29, 7, 9, log("stripped_oak_log", "x"))
    t.gable(18, 8, 30, 15, 8, "slate", "x", M("oak_planks"))
    t.put(24, 6, 14, M("bell[attachment=ceiling,facing=south]"))
    t.put(21, 6, 14, lantern_hung())
    t.put(27, 6, 14, lantern_hung())
    t.put(20, 4, 10, M("lectern[facing=south]"))
    stall(t, 11, 30, "green")
    stall(t, 32, 30, "yellow")
    t.put(13, 4, 32, M("loom[facing=north]"))
    t.put(36, 4, 32, M("grindstone[face=floor,facing=north]"))
    t.put(10, 4, 33, M("composter[level=0]"))
    t.put(12, 5, 30, M("green_carpet"))
    t.put(13, 5, 30, M("white_carpet"))
    t.put(37, 5, 30, M("flower_pot"))
    # Two small back plots soften the edge of the square without obstructing either road.
    for x0 in (5, 37):
        for dx in range(6):
            t.put(x0 + dx, 4, 4, M("oak_leaves[persistent=true]"))
            if dx % 2:
                t.put(x0 + dx, G, 5, M("grass_block"))
                t.put(x0 + dx, 4, 5, M("poppy"))
    for x in (18, 30):
        for z in (19, 27, 36):
            t.lamp(x, z, 2, post="oak_fence")
    for x, z in ((6, 30), (43, 35), (9, 38), (39, 4)):
        t.tree(x, z, "oak", 5, 2)
    for x, z in ((16, 18), (32, 18), (27, 33), (21, 33)):
        t.put(x, G, z, M("grass_block"))
        t.put(x, 4, z, M("oxeye_daisy"))
    drovers_yard(t)
    t.light(lambda x, z: 2 <= x <= 46 and 6 <= z <= 37 or 49 <= x <= 65 and 7 <= z <= 20)
    t.check_support()
