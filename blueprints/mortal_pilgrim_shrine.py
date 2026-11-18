"""Pilgrims' Hill, an original roadside shrine in the Mortal Realm. SIZE (69, 26, 70).
Anchor (19, 4, 37) on the south approach. Cobblestone steps rise through grass and
exposed andesite to an oak shelter with a steep spruce roof, benches and a small bell.
The lower track passes a roofed rest bench, three wayside stations and a walled orchard.
PARTS start at z 0 and 35. References and local setting in design/lore/mortal_pilgrim_shrine.md.
"""
import math

from _dwargon_lib import noise2, rnd
from _town_lib import M, Town, lantern_hung, log, slab, stair

SIZE = (69, 26, 70)
PARTS = [0, 35]
G = 3
C = 19


def pilgrims_walk(t):
    # A second way in passes through the orchard and joins the stair approach.
    for x in range(19, 69):
        mid = 48 + round(0.09 * (x - 19)) + round(2 * math.sin(x / 10))
        for z in range(mid - 2, mid + 3):
            t.put(x, G, z, M("gravel" if abs(z - mid) < 2 else "coarse_dirt"))
            t.put(x, G + 1, z, M("air"))
    for z in range(5, 55):
        for x in (44, 45, 46):
            t.put(x, G, z, M("coarse_dirt" if x != 45 else "gravel"))
            t.put(x, G + 1, z, M("air"))
    # The apple orchard is divided by low rubble walls to keep the path visible.
    for z in (7, 19, 31):
        for x in (51, 62):
            t.tree(x, z, "oak", 4 + z % 3, 2)
    for z in range(3, 42):
        if z not in range(20, 25):
            t.put(65, G + 1, z, M("mossy_cobblestone_wall"))
    for x in range(49, 66):
        if x not in (56, 57, 58):
            t.put(x, G + 1, 40, M("cobblestone_wall"))
    # Three worn wayside stations follow the eastern track. Kneelers face their niches.
    for x, z in ((41, 10), (48, 23), (41, 36)):
        t.fill(x - 1, 4, z, x + 1, 6, z, M("mossy_stone_bricks"))
        t.put(x, 5, z, M("chiseled_stone_bricks"))
        t.fill(x - 1, 7, z, x + 1, 7, z, slab("stone_brick"))
        t.put(x, 4, z + 2, stair("spruce", "south"))
        t.put(x + 2, 4, z, M("lantern[hanging=false]"))
    # A roofed rest bench at the southern crossing marks the beginning of the pilgrimage.
    for x in (27, 35):
        for z in (55, 61):
            t.fill(x, 4, z, x, 7, z, log("oak_log"))
        t.fill(x, 7, 55, x, 7, 61, log("oak_log", "z"))
    t.fill(27, 7, 55, 35, 7, 55, log("stripped_oak_log", "x"))
    t.fill(27, 7, 61, 35, 7, 61, log("stripped_oak_log", "x"))
    t.gable(27, 55, 35, 61, 8, "spruce", "x", M("oak_planks"))
    t.fill(29, 4, 60, 33, 4, 60, stair("spruce", "south"))
    t.put(32, 6, 55, lantern_hung())
    for x in range(21, 34):
        t.put(x, G, 57, M("gravel"))
        t.put(x, 4, 57, M("air"))
    for x, z in ((6, 43), (10, 57), (5, 66), (50, 63), (59, 59), (65, 65)):
        t.tree(x, z, "birch", 5, 2)
    for x, z in ((21, 45), (36, 46), (46, 49), (59, 53), (21, 64)):
        t.lamp(x, z, 1, post="cobblestone_wall")


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            d = math.hypot((x - C) / 18, (z - 16) / 19)
            h = max(0, min(6, round((1 - d) * 12 + noise2(x, z, 5, 3) - 0.5)))
            if 13 <= x <= 25 and 10 <= z <= 20:
                h = 6
            if abs(x - C) <= 3 and z >= 20:
                h = min(6, max(0, (32 - z) // 2))
            if h:
                t.fill(x, G, z, x, G + h - 1, z, M("dirt"))
                rock = h < 5 and x < 13 and noise2(x, z, 3, 4) > 0.62
                t.put(x, G + h, z, M("andesite" if rock else "grass_block"))
            if abs(x - C) <= 2 and z >= 20:
                surface = "gravel" if z < 35 or abs(x - C) == 1 else "coarse_dirt"
                t.put(x, G + h, z, M(surface))
                if 21 <= z <= 31 and z % 2:
                    t.put(x, G + h + 1, z, stair("cobblestone", "north"))
            elif not (12 <= x <= 26 and 8 <= z <= 22) and t.get(x, G + h, z) == M("grass_block"):
                value = rnd(x, h, z, 90)
                if value < 0.085:
                    t.put(x, G + h + 1, z, M("oxeye_daisy" if value < 0.015 else "short_grass"))
    floor = G + 6
    t.fill(13, floor, 10, 25, floor, 19, M("cobblestone"))
    t.fill(14, floor, 11, 24, floor, 18, M("oak_planks"))
    for x in (14, 24):
        for z in (11, 18):
            t.fill(x, floor + 1, z, x, floor + 5, z, log("oak_log"))
    for z in (11, 18):
        t.fill(14, floor + 5, z, 24, floor + 5, z, log("stripped_oak_log", "x"))
    t.fill(15, floor + 1, 11, 23, floor + 2, 11, M("mossy_stone_bricks"))
    t.fill(17, floor + 3, 11, 21, floor + 4, 11, M("oak_planks"))
    t.put(19, floor + 4, 11, M("chiseled_stone_bricks"))
    t.gable(13, 10, 25, 19, floor + 6, "spruce", "z", M("oak_planks"))
    # Half-tiles finish the ridge above the gabled bell shelter.
    for z in range(9, 21):
        roof = max(y for y in range(floor + 6, SIZE[1]) if t.get(C, y, z) != M("air"))
        t.put(C, roof + 1, z, slab("spruce"))
    for x in (15, 23):
        for z in (13, 14, 15):
            t.put(x, floor + 1, z, stair("spruce", "west" if x == 15 else "east"))
        t.put(x, floor + 4, 18, lantern_hung())
    t.put(C, floor + 4, 18, M("bell[attachment=ceiling,facing=south]"))
    for x, z in ((15, 26), (23, 31), (17, 36)):
        top = max(y for y in range(G, G + 7) if t.get(x, y, z) in (M("grass_block"), M("gravel"), M("coarse_dirt")))
        t.put(x, top + 1, z, M("cobblestone"))
        t.put(x, top + 2, z, M("lantern[hanging=false]"))
    pilgrims_walk(t)
    t.light(lambda x, z: 12 <= x <= 26 and 9 <= z <= 20 or 26 <= x <= 36 and 54 <= z <= 62)
    t.check_support()
