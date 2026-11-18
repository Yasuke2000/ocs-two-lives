"""Sacred Mountain of Lubelius, the last ascent to Luminous's sealed Inner Sanctum.

SIZE (81, 57, 81), three PARTS along z. Anchor (40, 4, 76) on the southern pilgrim
road, facing north. Two flights climb to a pointed, gold-bound double seal cut into
a limestone ridge. Veiled reliefs face seven flush votive lights on the upper court.
Quartz, calcite, gold and light blue glass continue Lune's palette.
Sources: design/lore/sacred_mountain.md (the Holy Empire of Lubelius, Fuse's volume 7,
the project's political fan map and Minecraft Middle-earth's Minas Tirith).
"""
from math import hypot

from _citylib import M, Mat, Site
from _dwargon_lib import noise2, rnd

SIZE = (81, 57, 81)
PARTS = [0, 27, 54]
C, G = 40, 3
MARBLE = Mat("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab")


def terrace(z):
    # Two flights, separated by a level court wide enough for the two rose beds.
    return G + min(7, max(0, 70 - z)) + min(8, max(0, 52 - z))


def mountain(s):
    # Overlapping rock shoulders taper to individual outcrops on all four edges.
    summits = [(21, 18, 39, 1.6, 1.85), (47, 19, 49, 1.7, 2),
               (61, 24, 37, 1.75, 1.55), (15, 39, 23, 1.65, 1.4)]
    heights = {}
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            noise = noise2(x, z, 5, 271) - 0.5
            relief = max(h - hypot((x - px) * kx, (z - pz) * kz)
                         for px, pz, h, kx, kz in summits)
            # Long grassy toes run down either side of the stairs. The envelope
            # flattens the last few blocks where the placer's 1:1 skirt begins.
            toes = max(6 - hypot((x-17)*0.32, (z-57)*0.32),
                       8 - hypot((x-65)*0.35, (z-55)*0.34))
            rise = max(0, relief + 5 * noise, toes + noise)
            edge = min(x, z, SIZE[0]-1-x, SIZE[2]-1-z)
            taper = min(1.0, edge / (18 + 7 * noise))
            rise = int(rise * taper * taper * (3 - 2*taper))
            if z >= 25:
                rise = min(rise, terrace(z) - G + max(0, abs(x-C) - 16))
                shoulder = terrace(z) - G - 3 - max(0, abs(x-C) - 13)
                rise = max(rise, shoulder)

            surface = heights[x, z] = G + rise
            # A thin earth lip meets the live terrain. The placer supplies any
            # missing subsoil below the lowest saved block in each column.
            dirt_skin = rise <= 7 or (rise < 24 and noise > -0.2)
            bottom = G - min(G, edge)
            for y in range(bottom, surface + 1):
                band = (y + int(0.12 * x + 3 * noise)) % 12
                mat = "calcite" if band == 0 else "diorite" if band <= 3 else "andesite" if band < 7 else "stone"
                if dirt_skin and y >= surface - 2:
                    mat = "grass_block" if surface == y else "dirt"
                s.put(x, y, z, mat)
            if x % 7 == 3 and z % 7 == 3:
                s.put(x, surface, z, "glowstone")
                s.put(x, surface+1, z, "moss_carpet")
            elif dirt_skin and abs(x-C) > 17 and rnd(x, surface, z, 74) < 0.12:
                s.put(x, surface+1, z, "fern" if noise > 0.15 else "short_grass")
    return heights


def approach(s):
    for z in range(25, 74):
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
    # Worn stones give way to gravel, then a three-block earth track. The
    # final cross-section lies at the surveyed ground level on the southern edge.
    for z in range(74, SIZE[2]):
        width = max(1, 9 - (z-73)*1.2)
        mid = C + (1 if z >= 76 else 0)
        for x in range(mid-8, mid+9):
            dx = abs(x-mid)
            grain = rnd(x, G, z, 143)
            if dx > width and (dx > width+1 or grain > 0.35):
                continue
            if (z == 74 and dx <= 2) or (z < 78 and grain > (z-72)/6):
                mat = "andesite" if grain < 0.65 else "calcite"
            elif grain < 0.25 and z < 80:
                mat = "gravel"
            else:
                mat = "coarse_dirt" if grain < 0.62 else "dirt_path"
            if s.get(x, G+1, z) == M("moss_carpet"):
                s.bp.blocks.pop((x, G+1, z))
            s.put(x, G, z, mat)
    # The two landings have rose parterres inside low marble rims.
    for z in (39, 57):
        y = terrace(z)
        for x in (C-4, C+4):
            s.put(x, y, z, "sea_lantern")
        for x in (C-12, C+12):
            s.fill(x-2, y+1, z-3, x+2, y+1, z+3, "smooth_quartz")
            s.fill(x-1, y+1, z-2, x+1, y+1, z+2, "grass_block")
            for dz in (-2, 0, 2):
                s.put(x, y+2, z+dz, "rose_bush[half=lower]")
                s.put(x, y+3, z+dz, "rose_bush[half=upper]")
    for z in (33, 42, 53, 61, 71):
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


def threshold(s):
    floor = terrace(29)
    # Shallow hooded figures, cut into the front of the existing gate piers.
    # Dark backing leaves the white veil legible even from the lower flight.
    for x in (C-15, C+15):
        s.fill(x-2, floor+2, 27, x+2, floor+10, 27, "polished_deepslate")
        s.fill(x-2, floor+1, 28, x+2, floor+1, 30, "chiseled_quartz_block")
        for dx in (-2, 2):
            s.fill(x+dx, floor+2, 28, x+dx, floor+10, 28, "quartz_pillar")
            s.put(x+dx, floor+11, 28, "gold_block")
        s.fill(x-2, floor+12, 28, x+2, floor+12, 29, "smooth_quartz")
        s.put(x, floor+11, 28, "sea_lantern")
        # Pale stole on each side of the robe, folds in front, a blank veil
        # beneath a gold circlet, and a dark-red clasp below the veil.
        s.fill(x-1, floor+2, 28, x+1, floor+5, 28, "polished_diorite")
        s.fill(x, floor+2, 29, x, floor+7, 29, "calcite")
        for dx in (-1, 1):
            s.stair(x+dx, floor+2, 29, "n", MARBLE)
            s.put(x+dx, floor+5, 29, "polished_diorite")
            s.fill(x+dx, floor+6, 28, x+dx, floor+7, 28, "quartz_pillar")
        s.put(x, floor+8, 29, "gold_block")
        s.slab(x, floor+9, 29, MARBLE)
        s.put(x, floor+5, 30, "crimson_button[face=wall,facing=south,powered=false]")
    # Seven lights, each set in a gold-edged stone socket flush with the
    # landing. The central light completes the arc without blocking the aisle.
    for dx, z in ((-9, 30), (-6, 32), (-3, 34), (0, 35),
                  (3, 34), (6, 32), (9, 30)):
        x = C + dx
        s.put(x, floor, z, "sea_lantern")
        s.put(x, floor, z-1, "gold_block")
        s.put(x, floor, z+1, "chiseled_quartz_block")
    # Two straps per leaf and hand-height bolts break up the dark lower gate.
    for side in (-1, 1):
        for dy in (2, 14):
            for dx in range(5, 9):
                s.put(C+side*dx, floor+dy, 26, "waxed_exposed_cut_copper")
            s.put(C+side*8, floor+dy, 27, "polished_blackstone_button[face=wall,facing=south,powered=false]")
        s.put(C+side*2, floor+2, 26, "chiseled_quartz_block")
        s.put(C+side*2, floor+2, 27, "polished_blackstone_button[face=wall,facing=south,powered=false]")


def build(bp):
    s = Site(bp, G)
    heights = mountain(s)
    for x, z, height in ((8, 64, 8), (17, 72, 6), (22, 60, 7), (63, 69, 8),
                         (71, 58, 9), (72, 73, 6)):
        Site(bp, heights[x, z]).tree(x, z, h=height, leaf="spruce_leaves", log="spruce_log", r=3)
    approach(s)
    gate(s)
    threshold(s)
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
