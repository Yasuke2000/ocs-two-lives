"""Ballachia, the former Orthrus exchange and the road the freed elves take east.

SIZE (76, 38, 66), two z slabs at 0 and 33. Anchor (38, 4, 41) on the forecourt.
Three ribbed blue domes, an arched porch and a tracery window rise over a south-facing arcade.
The form and illuminated windows follow the episode 65 Ballachia establishing shot. A broken chain in the yard paving connects the hall, lodging house and cart shed.
Materials include blue terracotta, deepslate, brick, spruce, dark oak, calcite,
stone bricks, warm lantern glass and iron. Manga chapter 108 gives the rescue and escort.
The use of this facade for the yard is our interpretation (design/lore/ballachia.md).
"""
from math import isqrt

from _lords_lib import disc_cells, light_pass
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
        t.fill(x, F + 1, 27, x, 8, 27, M("stone_brick_wall"))
        t.put(x, F, 27, M("polished_andesite"))
        t.put(x, 9, 27, M("chiseled_stone_bricks"))
        if x < 58:
            t.clear(x + 1, F, 22, x + 7, 9, 22)
            # Tall lit windows flank the opening from the exchange onto the colonnade.
            for jamb in (x + 1, x + 7):
                t.fill(jamb, F, 22, jamb, F, 22, M("stone_bricks"))
                t.fill(jamb, F + 1, 22, jamb, 9, 22, M("yellow_stained_glass"))
                t.put(jamb, 8, 21, M("ochre_froglight"))
            t.fill(x + 3, 7, 7, x + 5, 9, 7, M("glass"))
            t.fill(x + 3, 10, 7, x + 5, 10, 7, log("dark_oak_log", "x"))
            for z in range(8, 16):
                t.put(x, F, z, M("stone_bricks"))
                t.put(x, F + 1, z, M("iron_bars[north=true,south=true]"))
            t.put(x, 10, 15, M("chain"))
            t.put(x, 9, 15, lantern_hung())
    for z in (7, 22):
        t.fill(10, 12, z, 58, 12, z, log("dark_oak_log", "x"))
    t.gable(10, 7, 58, 22, 13, "slate", "x", M("calcite"))
    # Three loading dormers bring daylight into the long hall from the south.
    for x in (14, 30, 54):
        t.ring(x - 2, 17, x + 2, 22, 14, 17, M("calcite"))
        t.fill(x - 1, 15, 22, x + 1, 17, 22, M("yellow_stained_glass"))
        t.fill(x, 15, 22, x, 17, 22, M("polished_andesite"))
        for side in (x - 2, x + 2):
            t.fill(side, 14, 22, side, 17, 22, log("dark_oak_log"))
        t.gable(x - 2, 17, x + 2, 22, 18, "slate", "z", M("calcite"))
        t.fill(x - 1, 14, 19, x + 1, 17, 21, M("air"))
        t.put(x - 1, 16, 21, M("ochre_froglight"))
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
    dome(t, 64, 23, 26, (5, 5, 4, 4, 3, 2))


def dome(t, cx, cz, base, radii):
    # Dark blue panels rise between stone ribs; the steps tighten toward the finial.
    for dy, radius in enumerate(radii):
        for x, z in disc_cells(cx, cz, radius):
            rib = x == cx or z == cz
            t.put(x, base + dy, z, M("polished_deepslate" if rib else "blue_terracotta"))
    top = base + len(radii)
    t.put(cx, top, cz, M("deepslate_brick_wall"))
    t.put(cx, top + 1, cz, M("lightning_rod[facing=up]"))


def roofline(t):
    for cx, radius, base, radii in ((43, 6, 25, (7, 7, 6, 6, 5, 4, 2)),
                                    (21, 3, 24, (4, 4, 3, 2))):
        for y in range(14, base):
            for x, z in disc_cells(cx, 14, radius):
                state = "stone_bricks"
                if base - 4 <= y <= base - 2 and x % 2 != z % 2:
                    state = "ochre_froglight"
                t.put(x, y, z, M(state))
        dome(t, cx, 14, base, radii)
    for x in (11, 33, 57):
        t.fill(x, 15, 10, x + 1, 24, 11, M("stone_bricks"))
        t.fill(x, 25, 10, x + 1, 25, 11, slab("stone_brick"))
    # The luminous wheel sits in a raised square gable above the west end.
    t.fill(7, F, 12, 13, 26, 17, M("stone_bricks"))
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx * dx + dy * dy > 5:
                continue
            pane = "yellow_stained_glass" if abs(dx) != abs(dy) else "polished_andesite"
            t.put(10 + dx, 22 + dy, 17, M(pane))
            t.put(10 + dx, 22 + dy, 16, M("ochre_froglight"))
    t.gable(7, 12, 13, 17, 27, "slate", "z", M("stone_bricks"))


def porch(t):
    # The semicircular hood spans the walking route; each pier stands outside the opening.
    for dx in range(-7, 8):
        top = 11 + isqrt(49 - dx * dx)
        inner = 11 + isqrt(25 - dx * dx) if abs(dx) <= 5 else F - 1
        bottom = inner + 1
        t.fill(34 + dx, bottom, 27, 34 + dx, top, 29, M("stone_bricks"))
        t.put(34 + dx, top, 29, M("polished_andesite"))
    t.clear(33, F, 22, 35, 9, 27)
    for x in (27, 28, 40, 41):
        t.put(x, F, 29, M("chiseled_stone_bricks"))


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
    # The travel scene shows a curved canopy stretched over wooden hoops.
    for x in range(57, 64):
        hoop = x in (57, 60, 63)
        for z in (47, 51):
            t.fill(x, F + 2, z, x, F + 3, z, log("spruce_log") if hoop else M("white_wool"))
        t.fill(x, F + 4, 48, x, F + 4, 50, log("spruce_log", "z") if hoop else M("white_wool"))


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
    roofline(t)
    porch(t)
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
