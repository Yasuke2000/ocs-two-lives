"""An abandoned hillside adit in the Mortal Realm. SIZE (73, 24, 68), anchor
(23, 4, 35) at the south yard. The single-level rail enters a stone slope and ends
at a deliberate collapse. Oak pit props, a tool recess and a winding wheel survive.
A siding leads east to a stepped quarry and the sorting shed. PARTS start at z 0 and 35.
Original layout, references in design/lore/mortal_mine.md.
"""
import math

from _dwargon_lib import noise2, rnd
from _lords_lib import light_pass
from _town_lib import M, Town, lantern_floor, lantern_hung, log, slab, stair

SIZE = (73, 24, 68)
PARTS = [0, 35]
G = 3
C = 23


def quarry_yard(t):
    # Three exposed working benches climb to the north and east of the quarry floor.
    for x in range(40, 72):
        for z in range(3, 42):
            radius = math.hypot((x - 53) / 17, (z - 26) / 22)
            if radius > 1.05:
                continue
            bank = max(0, 12 - abs(x - 53) // 3 - abs(z - 20) // 3)
            cut = max((x - 56) // 3, (18 - z) // 3, 0) * 2
            h = min(bank, cut)
            for y in range(1, h + 1):
                stone = "tuff" if (y + z // 4) % 6 == 0 else "andesite" if y % 4 == 0 else "stone"
                t.put(x, G + y, z, M(stone))
            if h == 0:
                t.put(x, G, z, M("andesite" if rnd(x, 0, z, 3) > 0.4 else "gravel"))
    # A siding runs past a shallow drainage channel to the quarry face.
    t.pave(21, 35, 56, 39, "cobble")
    t.pave(51, 19, 55, 37, "cobble")
    for x in range(29, 53):
        t.put(x, 4, 37, M("rail[shape=east_west]"))
    t.put(53, 4, 37, M("rail[shape=north_west]"))
    for z in range(19, 37):
        t.put(53, 4, z, M("rail[shape=north_south]"))
    for z in range(24, 33):
        t.put(58, G - 1, z, M("clay"))
        t.put(58, G, z, M("water[level=0]"))
    # An open stonecutters' shed looks across the siding, with a windlass and cutting bench.
    for x in (39, 53):
        for z in (44, 52):
            t.fill(x, 4, z, x, 8, z, log("spruce_log"))
    t.fill(39, 8, 44, 53, 8, 44, log("stripped_spruce_log", "x"))
    t.fill(39, 8, 52, 53, 8, 52, log("stripped_spruce_log", "x"))
    t.gable(39, 44, 53, 52, 9, "spruce", "x", M("spruce_planks"))
    t.put(44, 7, 44, lantern_hung())
    t.put(47, 7, 52, lantern_hung())
    t.put(50, 4, 49, M("stonecutter[facing=north]"))
    t.fill(41, 4, 50, 43, 4, 50, log("stripped_spruce_log", "x"))
    t.fill(22, G, 40, 25, G, 67, M("coarse_dirt"))
    t.pave(24, 46, 39, 49, "street")
    for x, z in ((7, 43), (9, 58), (14, 63), (36, 60), (51, 61), (62, 50), (68, 56)):
        t.tree(x, z, "birch", 5 + z % 2, 2)
    # Pit props sorted by length, with a crosswise sleeper at either end of each stack.
    for x in (31, 57):
        t.fill(x, 4, 55, x + 5, 4, 55, log("dark_oak_log", "x"))
        t.fill(x, 4, 59, x + 5, 4, 59, log("dark_oak_log", "x"))
        for dx in (1, 2, 3, 4):
            t.fill(x + dx, 5, 54, x + dx, 5, 60, log("spruce_log", "z"))
        t.fill(x + 2, 6, 55, x + 2, 6, 59, log("spruce_log", "z"))
    for x, z in ((25, 43), (41, 38), (54, 30), (26, 58), (57, 42)):
        t.lamp(x, z, 2, post="spruce_fence")


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    for x in range(SIZE[0]):
        for z in range(31):
            d = math.hypot((x - C) / 22, (z - 14) / 15)
            h = max(0, round((1 - d) * 17 + (noise2(x, z, 5, 12) - 0.5) * 2))
            # The rock over the two galleries must remain intact through the shoulders.
            if 19 <= x <= 27 and 7 <= z <= 24 or 27 <= x <= 34 and 11 <= z <= 17:
                h = max(h, 7)
            for y in range(1, h + 1):
                v = rnd(x, y, z, 16)
                rock = "andesite" if v < 0.22 else "cobblestone" if v < 0.29 else "stone"
                cap = "grass_block" if h < 6 or noise2(x, z, 4, 8) < 0.48 else rock
                t.put(x, G + y, z, M(cap if y == h else rock))
    t.clear(20, G + 1, 7, 26, G + 5, 30)
    t.clear(26, G + 1, 12, 33, G + 4, 16)
    t.pave(20, 7, 26, 30, "cobble")
    t.pave(27, 12, 33, 16, "cobble")
    t.pave(15, 26, 30, 34, "cobble")
    t.pave(21, 34, 25, 40, "street")
    for z in (9, 15, 21, 25):
        for x in (20, 26):
            t.fill(x, 4, z, x, 7, z, log("oak_log"))
        t.fill(20, 8, z, 26, 8, z, log("stripped_oak_log", "x"))
        t.put(21, 7, z, stair("oak", "west", "top"))
        t.put(25, 7, z, stair("oak", "east", "top"))
        t.put(24, 7, z, lantern_hung())
    for z in range(9, 33):
        if z not in (11, 28, 29):
            t.put(C, G + 1, z, M("rail[shape=north_south]"))
    for x, z, h in ((20, 8, 3), (21, 7, 3), (22, 7, 2), (23, 8, 1), (25, 8, 2), (26, 7, 2)):
        t.fill(x, 4, z, x, 3 + h, z, M("andesite"))
    t.put(20, 7, 8, M("cobweb"))
    # A prop and work bench identify the east tool recess. Keep the central aisle open.
    t.fill(30, 4, 12, 30, 7, 12, log("spruce_log"))
    t.fill(30, 7, 12, 30, 7, 16, log("spruce_log", "z"))
    t.fill(30, 4, 16, 30, 6, 16, log("spruce_log"))
    t.put(30, 6, 15, lantern_hung())
    t.put(33, 4, 15, M("crafting_table"))
    t.put(33, 4, 14, slab("spruce", "top"))
    # A fixed winding drum sits in its trestle beside the portal, clear of the approach.
    for x in (16, 20):
        t.fill(x, 4, 31, x, 6, 31, log("spruce_log"))
    t.fill(16, 6, 31, 20, 6, 31, log("stripped_spruce_log", "x"))
    t.put(18, 6, 31, log("dark_oak_log", "x"))
    t.put(16, 7, 31, M("lantern[hanging=false]"))
    for x in (27, 28):
        t.fill(x, 4, 30, x, 4, 33, log("oak_log", "z"))
    t.put(27, 5, 31, log("oak_log", "z"))
    # Spoil stone was tipped beside the entrance rather than down the haul road.
    for x in range(31, 40):
        for z in range(25, 34):
            h = round(3.0 - math.hypot((x - 35) * 0.8, (z - 29) * 0.9) + noise2(x, z, 2, 7))
            if h > 0:
                for y in range(4, 4 + h):
                    t.put(x, y, z, M("tuff" if rnd(x, y, z, 5) < 0.55 else "andesite"))
    for x in range(3, 44):
        for z in range(3, 39):
            if not (x < 15 or x > 37 or z < 6):
                continue
            top = next((yy for yy in range(21, G - 1, -1) if t.get(x, yy, z) != M("air")), G)
            if t.get(x, top, z) == M("grass_block") and rnd(x, top, z, 11) < 0.08:
                t.put(x, top + 1, z, M("fern"))
    quarry_yard(t)
    t.light(lambda x, z: 38 <= x <= 54 and 43 <= z <= 53)
    light_pass(bp, lambda x, y, z: y <= 8 and (20 <= x <= 26 and 7 <= z <= 26 or
               27 <= x <= 33 and 12 <= z <= 16), 4, lambda x, y, z: lantern_floor(), label="mortal_mine")
    t.check_support()
