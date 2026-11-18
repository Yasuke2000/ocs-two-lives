"""Raja's old lakeside gold workings, SIZE (80, 37, 70), anchor (36, 6, 49) on the haul road.

Scarlet Bond connects the fortunes of Queen Towa, Raja's gold mines and its lake. Our interpretation
is one exhausted adit beside a small inlet, with a wooden winding frame and a shore assay house.
Stone, tuff, granite, oak, dark oak, copper, sandstone and water. Sources in design/lore/raja.md.
"""
from math import sin, sqrt

from _dwargon_lib import noise2
from _lords_lib import light_pass
from _town_lib import M, Town, lantern_floor, lantern_hung, log, slab, stair

SIZE = (80, 37, 70)
PARTS = [0, 35]
G = 5


def ridge(t):
    for x in range(1, 69):
        for z in range(1, 38):
            height = 0
            for cx, cz, rx, rz, peak in ((22, 19, 21, 17, 23), (43, 15, 23, 14, 17)):
                d = sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2)
                height = max(height, (1 - d) * peak)
            if height < 0.9:
                continue
            height = int(height * (0.87 + 0.27 * noise2(x, z, 6, 17)))
            for h in range(1, height + 1):
                vein = h + int(2 * sin(x / 6) + 2 * sin(z / 9))
                stone = "tuff" if vein % 8 in (0, 1) else "andesite" if vein % 6 == 0 else "stone"
                if h == height and (height < 5 or noise2(x, z, 6, 4) > 0.58):
                    stone = "grass_block"
                t.put(x, G + h, z, M(stone))


def adit(t):
    # Two galleries terminate in unbroken rock. The south-facing main entrance opens onto the rails.
    t.clear(22, 6, 11, 28, 10, 36)
    t.clear(14, 6, 16, 22, 9, 20)
    for z in (12, 18, 24, 30, 35):
        for x in (22, 28):
            t.fill(x, 6, z, x, 10, z, log("dark_oak_log"))
            t.put(x, 6, z, M("polished_andesite"))
        t.fill(22, 10, z, 28, 10, z, log("stripped_spruce_log", "x"))
        t.put(23, 9, z, lantern_hung())
    for x in range(15, 23, 4):
        for z in (16, 20):
            t.fill(x, 6, z, x, 9, z, log("spruce_log"))
        t.fill(x, 9, 16, x, 9, 20, log("stripped_spruce_log", "z"))
    t.put(15, 8, 18, lantern_hung())
    # Exposed timbers and a rubble-covered portal where the bank falls away over the approach.
    t.fill(21, 10, 25, 29, 10, 35, log("spruce_log", "x"))
    t.fill(21, 11, 25, 29, 11, 35, M("tuff"))
    for side in (21, 29):
        t.fill(side, 6, 26, side, 9, 35, M("cobblestone"))
    for z in range(12, 46):
        t.put(25, G, z, M("polished_andesite"))
        t.put(25, 6, z, M("rail[shape=north_south]"))
    t.put(25, 6, 46, log("dark_oak_log", "x"))


def winding_frame(t):
    # Two bearing frames carry a spoked wooden sheave. Three-sided braces leave the winding drum visible.
    t.clear(36, 6, 31, 49, 30, 43)
    t.pave(36, 31, 49, 43, "cobble")
    for z in (33, 41):
        for side, direction in ((37, 1), (47, -1)):
            t.fill(side, 6, z, side, 7, z, M("polished_andesite"))
            for y in range(8, 22):
                x = side + direction * min(3, (y - 8) // 4)
                t.put(x, y, z, log("dark_oak_log"))
                if (y - 8) % 4 == 0:
                    t.put(x - direction, y, z, log("dark_oak_log", "x"))
        t.fill(39, 19, z, 45, 19, z, log("stripped_oak_log", "x"))
        t.fill(40, 21, z, 44, 21, z, log("dark_oak_log", "x"))
    t.fill(42, 21, 33, 42, 21, 41, log("stripped_dark_oak_log", "z"))
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            r = dx * dx + dy * dy
            if 12 <= r <= 20 or (r < 12 and (dx == 0 or dy == 0)):
                t.put(42 + dx, 21 + dy, 37, M("stripped_oak_wood"))
    t.fill(38, 9, 37, 38, 20, 37, M("chain"))
    for z in (35, 39):
        t.fill(38, 6, z, 38, 9, z, log("spruce_log"))
    t.fill(38, 8, 35, 38, 8, 39, log("stripped_dark_oak_log", "z"))
    for x in (37, 47):
        t.put(x, 8, 42, M("ochre_froglight"))
        t.fill(x, 6, 42, x, 7, 42, M("stone_bricks"))


def waterworks(t):
    # A contained inlet with a shallow, sloping bed under the scrub and a short timber landing.
    for z in range(42, 68):
        for x in range(3, 34):
            d = ((x - 17) / 14.3) ** 2 + ((z - 55) / 11.7) ** 2 + 0.09 * sin(x * 0.5 + z * 0.3)
            if d < 1.18:
                t.put(x, G, z, M("gravel"))
            if d < 1:
                depth = 1 if d > 0.57 else 2
                t.put(x, G - depth, z, M("clay" if d < 0.4 else "gravel"))
                t.fill(x, G - depth + 1, z, x, G, z, M("water[level=0]"))
    for x in range(22, 35):
        t.fill(x, 6, 53, x, 6, 55, slab("spruce"))
    for x in (22, 28, 33):
        for z in (53, 55):
            t.fill(x, 3, z, x, 6, z, log("dark_oak_log"))
    t.lamp(22, 53, 2, post="oak_fence", y0=7)
    # Shallow stone settling beds, part of the old gold-washing yard on the western shore.
    for x in (8, 14):
        t.fill(x, G, 34, x + 4, G, 40, M("stone_bricks"))
        t.ring(x, 34, x + 4, 40, 6, 6, M("mossy_stone_bricks"))
        t.fill(x + 1, 6, 35, x + 3, 6, 39, M("water[level=0]"))
        t.fill(x, 7, 35, x, 7, 39, slab("spruce"))
    for x, z in ((7, 48), (5, 54), (10, 65), (23, 65)):
        # Boulders on the bank leave the foot of the landing clear.
        t.put(x, G, z, M("andesite"))
        t.put(x, 6, z, slab("andesite"))
    # Assay benches and a window with a crown motif for Towa face the road.
    t.house(54, 33, 70, 45, "s", storeys=1, roof="copper", frame="spruce", furnish=False,
            plaster="white_terracotta", base="polished_granite", storey_h=6)
    for x in (56, 59, 65, 68):
        t.fill(x, 6, 35, x + 1, 6, 36, M("polished_andesite"))
        t.put(x, 7, 35, M("flower_pot"))
    for x in range(60, 65):
        t.put(x, 9, 45, M("yellow_stained_glass"))
    for x in (60, 62, 64):
        t.put(x, 10, 45, M("yellow_stained_glass"))
    t.put(62, 9, 45, M("red_stained_glass"))


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(33, 44, 40, 69, "street")
    t.pave(21, 36, 32, 45, "cobble")
    t.pave(24, 44, 70, 49, "street")
    ridge(t)
    adit(t)
    winding_frame(t)
    waterworks(t)
    for x, z in ((5, 31), (3, 42), (46, 54), (57, 57), (70, 50), (73, 22)):
        t.tree(x, z, "oak", 5, 2)
    # Wheel ruts taper as the haul road leaves the quarried surfaces.
    for z in range(58, 70):
        for x in range(33, 41):
            if abs(x - 36.5) > 4 - (z - 57) / 4:
                t.put(x, G, z, M("grass_block"))
        for x in (35, 38):
            t.put(x, G, z, M("coarse_dirt"))
    for x, z in ((31, 41), (41, 50), (52, 46), (67, 47), (33, 59)):
        t.lamp(x, z, 2, post="dark_oak_fence")
    light_pass(bp, lambda x, y, z: (14 <= x <= 29 and 10 <= z <= 36 and y <= 10)
               or (51 <= x <= 72 and 30 <= z <= 47) or (32 <= x <= 50 and 30 <= z <= 52 and y <= 10),
               6, lambda x, y, z: lantern_floor(), label="raja")
    t.check_support()
