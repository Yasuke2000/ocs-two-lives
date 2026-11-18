"""Ballachia, the former Orthrus exchange and the road the freed elves take east.

SIZE (76, 38, 66), two z slabs at 0 and 33. Anchor (38, 4, 41) on the forecourt.
The long brick-roofed hall is open to the south under a timber arcade. A slate belfry
marks the east end. A broken chain is set into the yard paving between the hall,
a small lodging house and a cart shed. Materials are brick, spruce, dark oak, calcite,
stone bricks and iron. Manga chapter 108 and anime episode 65 give the Ballachia
episode, while the architecture is our interpretation (design/lore/ballachia.md).
"""
from _lords_lib import light_pass
from _town_lib import M, Town, lantern_floor, lantern_hung, log, slab, stair

SIZE = (76, 38, 66)
PARTS = [0, 33]
G = 3
F = G + 1


def exchange(t):
    # Rear and end walls. The former bays open onto a shared aisle along the south side.
    t.fill(10, G, 7, 58, G, 27, M("spruce_planks"))
    t.ring(10, 7, 58, 22, F, 11, M("bricks"))
    for x in range(10, 59, 8):
        for z in (7, 22):
            t.fill(x, F, z, x, 12, z, log("stripped_dark_oak_log"))
        t.fill(x, 11, 7, x, 11, 22, log("dark_oak_log", "z"))
        t.fill(x, F, 27, x, 9, 27, log("dark_oak_log"))
        t.put(x, F, 27, M("stone_bricks"))
        if x < 58:
            t.clear(x + 1, F, 22, x + 7, 9, 22)
            t.fill(x + 3, 7, 7, x + 5, 9, 7, M("glass"))
            t.fill(x + 3, 10, 7, x + 5, 10, 7, log("dark_oak_log", "x"))
            for z in range(8, 16):
                t.put(x, F, z, M("stone_bricks"))
                t.put(x, F + 1, z, M("iron_bars[north=true,south=true]"))
            t.put(x, 10, 15, M("chain"))
            t.put(x, 9, 15, lantern_hung())
    for z in (7, 22):
        t.fill(10, 12, z, 58, 12, z, log("dark_oak_log", "x"))
    t.gable(10, 7, 58, 22, 13, "brick", "x", M("calcite"))
    # Three loading dormers bring daylight into the long hall from the south.
    for x in (18, 34, 50):
        t.ring(x - 2, 17, x + 2, 22, 14, 17, M("calcite"))
        t.fill(x - 1, 15, 22, x + 1, 16, 22, M("light_blue_stained_glass"))
        for side in (x - 2, x + 2):
            t.fill(side, 14, 22, side, 17, 22, log("dark_oak_log"))
        t.gable(x - 2, 17, x + 2, 22, 18, "slate", "z", M("calcite"))
        t.fill(x - 1, 14, 19, x + 1, 17, 21, M("air"))
    # A separate, shallower lean-to keeps the arcade open in front of the taller roof.
    for z in range(23, 29):
        t.fill(9, 12 - (z - 23) // 2, z, 59, 12 - (z - 23) // 2, z,
               slab("spruce", "top" if z % 2 else "bottom"))
    t.fill(10, 9, 27, 58, 9, 27, log("dark_oak_log", "x"))
    for x in range(14, 59, 8):
        t.put(x, 8, 27, lantern_hung())
    # Signs of the yard's change of use: the empty partitions, provisions and blankets.
    for x in (14, 22, 46, 54):
        t.put(x, F, 9, M("barrel[facing=up]"))
        t.put(x + 1, F, 9, M("hay_block"))
    for x in (29, 32, 37, 40):
        t.fill(x, F, 10, x, F, 12, slab("spruce", "top"))
        t.fill(x, F + 1, 10, x, F + 1, 12, M("blue_carpet"))


def bell_tower(t):
    # The belfry has open arches, so the bell and its timber crossbeam are visible.
    t.fill(60, F, 19, 68, 19, 27, M("stone_bricks"))
    for x in (60, 68):
        for z in (19, 27):
            t.fill(x, 19, z, x, 25, z, log("stripped_dark_oak_log"))
    t.fill(60, 25, 19, 68, 25, 27, M("dark_oak_planks"))
    t.fill(60, 23, 23, 68, 23, 23, log("dark_oak_log", "x"))
    t.put(64, 22, 23, M("bell[attachment=ceiling,facing=south]"))
    for y in (8, 13):
        t.fill(63, y, 27, 65, y + 2, 27, M("light_blue_stained_glass"))
    t.hip(60, 19, 68, 27, 26, "slate")
    t.put(64, 32, 23, M("lightning_rod[facing=up]"))


def coach_shed(t):
    t.fill(54, G, 44, 67, G, 55, M("cobblestone"))
    for x in (54, 67):
        for z in (44, 55):
            t.fill(x, F, z, x, 8, z, log("spruce_log"))
    t.fill(54, 8, 44, 67, 8, 44, log("spruce_log", "x"))
    t.fill(54, 8, 55, 67, 8, 55, log("spruce_log", "x"))
    t.gable(54, 44, 67, 55, 9, "mud", "x", M("spruce_planks"))
    for x in (55, 61, 66):
        t.put(x, 7, 44, lantern_hung())
    # Wheel blocks support a low cart bed. Its shafts point into the eastbound lane.
    for x in (58, 62):
        for z in (47, 51):
            t.put(x, F, z, log("dark_oak_log", "z"))
    t.fill(57, F + 1, 48, 63, F + 1, 50, slab("spruce", "top"))
    for z in (48, 50):
        t.fill(64, F + 1, z, 66, F + 1, z, slab("dark_oak", "top"))
    t.put(58, F + 2, 49, M("barrel[facing=east]"))
    t.put(59, F + 2, 49, M("hay_block[axis=x]"))


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(0, 37, 75, 41)
    t.pave(34, 40, 41, 65)
    t.pave(7, 25, 69, 39, "plaza")
    t.pave(5, 40, 19, 45, "cobble")
    t.pave(54, 40, 69, 48, "cobble")
    exchange(t)
    bell_tower(t)
    coach_shed(t)
    t.house(5, 45, 19, 55, "n", 1, roof="slate", furnish=False)
    for x in (8, 12, 16):
        t.put(x, F, 54, stair("spruce", "south"))
        t.put(x, F, 53, slab("spruce", "top"))
    # Two separated iron links in the paving commemorate the rescue.
    for x0, gap in ((27, 1), (38, -1)):
        for dx in range(9):
            for dz in range(5):
                corner = dx in (0, 8) and dz in (0, 4)
                edge = dx in (0, 8) or dz in (0, 4)
                if edge and not corner and not (dx == (8 if gap == 1 else 0) and dz == 2):
                    t.put(x0 + dx, G, 31 + dz, M("polished_deepslate"))
                if dx in (1, 7) and dz in (1, 3):
                    t.put(x0 + dx, G, 31 + dz, M("polished_deepslate"))
    for x, z in ((7, 35), (22, 37), (52, 37), (69, 35), (33, 53), (42, 61)):
        t.lamp(x, z)
    for x, z, h in ((5, 14, 6), (26, 52, 5), (12, 61, 5), (49, 56, 7), (72, 11, 6)):
        t.tree(x, z, "oak", h, 3)
    # Small roadside flower beds and espaliered hedges soften the outer edges.
    for x0, z0, width in ((4, 4, 21), (22, 58, 9), (52, 60, 15)):
        for dx in range(width):
            t.put(x0 + dx, F, z0, M("oak_leaves[persistent=true]"))
            if dx % 3 != 1:
                t.put(x0 + dx, F, z0 + 1, M("poppy" if dx % 2 else "oxeye_daisy"))
    # Controlled pools of light along the street keep the pavement motif clear.
    for x in (11, 27, 44, 60):
        t.lamp(x, 30, h=2)
    light_pass(bp, lambda x, y, z: True, F, lambda x, y, z: lantern_floor(), label="ballachia")
    t.check_support()
