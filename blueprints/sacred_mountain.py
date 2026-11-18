"""Sacred Mountain of Lubelius, the last ascent to Luminous's sealed Inner Sanctum.

SIZE (81, 57, 81), three PARTS along z. Anchor (40, 4, 76) on the southern pilgrim
road, facing north. Two flights climb to a pointed, gold-bound double seal cut into
a limestone ridge. Quartz, calcite, gold and light blue glass continue Lune's palette.
Sources: design/lore/sacred_mountain.md (the Holy Empire of Lubelius, Fuse's volume 7,
the project's political fan map and Minecraft Middle-earth's Minas Tirith).
"""
from math import hypot

from _citylib import M, Mat, Site
from _dwargon_lib import noise2

SIZE = (81, 57, 81)
PARTS = [0, 27, 54]
C, G = 40, 3
MARBLE = Mat("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab")


def terrace(z):
    # Two flights, separated by a level court wide enough for the two rose beds.
    return G + min(7, max(0, 70 - z)) + min(8, max(0, 52 - z))


def mountain(s):
    # Overlapping rock shoulders taper to individual outcrops on all four edges.
    summits = [(21, 15, 39, 1.6, 1.85), (47, 15, 49, 1.7, 2),
               (61, 24, 37, 1.75, 1.55), (15, 39, 23, 1.65, 1.4)]
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            relief = max(h - hypot((x - px) * kx, (z - pz) * kz)
                         for px, pz, h, kx, kz in summits)
            noise = noise2(x, z, 5, 271) - 0.5
            rise = max(0, int(relief + 5 * noise))
            rise = min(rise, min(x, z, 80 - x, 80 - z) * 3)
            # Trim away the rock in front of the entrance and beside the flights.
            if z >= 25:
                rise = min(rise, terrace(z) - G + max(0, abs(x-C) - 16))
                # The processional road sits in its hillside. Feather earth away
                # from the retaining walls to leave only their upper courses visible.
                shoulder = terrace(z) - G - 3 - max(0, abs(x-C) - 13)
                rise = max(rise, shoulder)
            for y in range(G + 1, G + rise + 1):
                band = (y + int(0.12 * x + 3 * noise)) % 12
                mat = "calcite" if band == 0 else "diorite" if band <= 3 else "andesite" if band < 7 else "stone"
                if y == G + rise and rise < 24 and noise > -0.2:
                    mat = "grass_block"
                s.put(x, y, z, mat)
            if x % 7 == 3 and z % 7 == 3:
                s.put(x, G+rise, z, "glowstone")
                s.put(x, G+rise+1, z, "moss_carpet")


def approach(s):
    for z in range(25, 81):
        y = terrace(z)
        steps = z in range(63, 70) or z in range(44, 52)
        width = 10 if steps else 15 if z < 63 else 9
        for x in range(C-width, C+width+1):
            if y > G:
                s.fill(x, G, z, x, y-1, z, "quartz_bricks")
            dx = abs(x-C)
            # Meadow lamps were laid before the stonework. Remove carpet under
            # the pavement or above the top of a grass ledge in the route.
            if s.get(x, y+1, z) == M("moss_carpet"):
                s.bp.blocks.pop((x, y+1, z))
            if steps and dx < width:
                s.stair(x, y, z, "n", MARBLE)
            elif dx == width or (dx == 7 and not steps):
                s.put(x, y, z, "chiseled_quartz_block")
            else:
                s.put(x, y, z, "calcite" if (x//3 + z//3) % 2 else "smooth_quartz")
    # The two landings have rose parterres inside low marble rims.
    for z in (39, 57):
        y = terrace(z)
        for x in (C-12, C+12):
            s.fill(x-2, y+1, z-3, x+2, y+1, z+3, "smooth_quartz")
            s.fill(x-1, y+1, z-2, x+1, y+1, z+2, "grass_block")
            for dz in (-2, 0, 2):
                s.put(x, y+2, z+dz, "rose_bush[half=lower]")
                s.put(x, y+3, z+dz, "rose_bush[half=upper]")
    for z in (33, 42, 53, 61, 71, 78):
        y = terrace(z)
        for x in (C-8, C+8):
            s.put(x, y+1, z, "chiseled_quartz_block")
            s.put(x, y+2, z, "quartz_pillar")
            s.put(x, y+3, z, "gold_block")
            s.lantern(x, y+4, z)


def gate(s):
    # Each arch layer projects one block beyond the previous one. The two leaves
    # are full solid blocks marking the threshold of the summit sanctuary.
    floor = terrace(25)
    for dx in range(-12, 13):
        crown = floor + 26 - int(abs(dx)**1.30 * 0.66)
        x = C + dx
        s.fill(x, floor, 21, x, crown, 25, "quartz_bricks")
        for y in range(floor+1, crown+1):
            rim = min(crown-y, 12-abs(dx))
            if rim >= 3:
                # A circular rose in leaded glass crosses the central door seam.
                radius = hypot(dx, y-floor-9)
                mat = "polished_deepslate"
                if dx == 0 or y in (floor+3, floor+15):
                    mat = "chiseled_quartz_block"
                if 4.3 <= radius <= 5.4:
                    mat = "gold_block"
                elif radius <= 4.3:
                    mat = "sea_lantern" if min(abs(dx), abs(y-floor-9)) == 0 else "light_blue_stained_glass"
                s.put(x, y, 26, mat)
            else:
                mat = ("smooth_quartz", "gold_block", "quartz_pillar")[rim]
                s.fill(x, y, 26, x, y, 28-rim, mat)
    # Sloping wing walls carry a pair of narrow, gold-tipped pinnacles.
    for side in (-1, 1):
        for dx in range(13, 23):
            x = C+side*dx
            y = floor + 13 - (dx-13)//2
            s.fill(x, G, 22, x, y, 26, "quartz_bricks")
            s.fill(x, y+1, 22, x, y+1, 26, "smooth_quartz")
            if dx in (13, 17, 21):
                s.fill(x, G, 27, x, y+1, 27, "quartz_pillar")
        x = C+side*15
        s.fill(x-2, G, 23, x+2, floor+17, 27, "quartz_bricks")
        for y in (floor+7, floor+16):
            s.fill(x-2, y, 23, x+2, y, 27, "chiseled_quartz_block")
        s.fill(x-1, floor+18, 24, x+1, floor+21, 26, "quartz_pillar")
        s.put(x, floor+22, 25, "gold_block")
        s.put(x, floor+23, 25, "end_rod[facing=up]")


def build(bp):
    s = Site(bp, G)
    s.ground(lambda x, z: M("grass_block"), under="stone")
    mountain(s)
    for x, z, height in ((8, 64, 8), (17, 72, 6), (22, 60, 7), (63, 69, 8),
                         (71, 58, 9), (72, 73, 6)):
        s.tree(x, z, h=height, leaf="spruce_leaves", log="spruce_log", r=3)
    approach(s)
    gate(s)
    s.light(lambda x, z: True, "sacred_mountain")
    s.check_support("sacred_mountain")
    # The placer clears above each column. Explicit air below an overhang or a
    # lantern preserves those gaps even on a mountain where terrain would fill them.
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            top = max(y for y in range(SIZE[1]) if s.get(x, y, z))
            for y in range(G+1, top):
                if s.get(x, y, z) is None:
                    s.put(x, y, z, "air")
