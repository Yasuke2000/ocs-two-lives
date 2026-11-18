"""Jia, Frey's mountain landing court in Fulbrosia.

SIZE (73, 40, 69), anchor (36, 4, 64) on the southern mountain trail. Two z slabs.
The official map describes a cold highland harpy country; Tinseluwu's plate locates Jia.
Our interpretation gives the audience roost paired feather-shaped roofs, open flight
balconies and a pedestrian ascent. Andesite, tuff, pale quartz, spruce and oxidised copper.
See design/lore/jia.md for geography and sources.
"""
from math import hypot

from _dwargon_lib import noise2, rnd
from _lords_lib import light_pass
from _town_lib import M, Town, lantern_floor, lantern_hung, stair

SIZE = (73, 40, 69)
PARTS = [0, 35]
G = 3
C = 36
DECK = 15


def spur(t):
    for x in range(2, 71):
        for z in range(2, 64):
            distance = hypot((x - C) / 33, (z - 28) / 32)
            seam = noise2(x, z, 6, 38)
            h = max(0, round((1 - distance) * 24 + 3 * (seam - .5)))
            if not h:
                continue
            top = G + min(h, DECK - G)
            for y in range(G, top + 1):
                rock = "andesite" if (int(2 * seam + (x + z) / 11) + y // 3) % 4 else "tuff"
                t.put(x, y, z, M(rock))
            crest = "stone" if h < 9 else "calcite" if seam > .63 else "andesite"
            t.put(x, top, z, M(crest))


def flight_court(t):
    # The rounded central roost narrows to pointed horizontal runways at either end.
    for x in range(5, 68):
        wing = abs(x - C)
        half_depth = 14 if wing <= 13 else max(2, 14 - (wing - 13) * 2 // 3)
        for z in range(27 - half_depth, 28 + half_depth):
            rim = abs(z - 27) == half_depth or wing == 31
            stone = "smooth_quartz" if rim else "spruce_planks"
            t.put(x, DECK, z, M(stone))
            if rim:
                t.put(x, DECK - 1, z, M("cut_copper"))
    # Exposed ribs carry the runways back to slender tapering piers.
    for side in (-1, 1):
        for d in range(13, 31):
            underside = DECK - 1 - (30 - d) // 3
            for z in (25, 29):
                t.fill(C + side*d, underside, z, C + side*d, DECK - 1, z, M("stripped_spruce_log"))
        for d in (18, 26):
            for z in (25, 29):
                t.fill(C + side*d, G, z, C + side*d, DECK - 2, z, M("polished_andesite"))
        # Flight access stays open at each wingtip.
        for d in range(18, 27, 4):
            for sign in (-1, 1):
                z = 27 + sign*(14 - (d - 13) * 2 // 3)
                t.put(C + side*d, DECK + 1, z, lantern_floor())

    for z in (17, 27, 37):
        for x in (24, 48):
            t.fill(x-1, DECK+1, z-1, x+1, DECK+1, z+1, M("chiseled_quartz_block"))
            t.fill(x, DECK+2, z, x, 25, z, M("quartz_pillar"))
            t.fill(x-1, 25, z, x+1, 25, z, M("smooth_quartz"))
            for delta in range(1, 8):
                # Raked timber ribs follow the rise of the feathers.
                t.put(x + (1 if x > C else -1)*delta, 25 + delta // 3, z,
                      M("stripped_spruce_log[axis=x]"))
        t.fill(24, 25, z, 48, 25, z, M("stripped_spruce_log[axis=x]"))
        for x in (27, 45):
            t.put(x, 24, z, lantern_hung())

    # Overlapping flights of five primaries sweep back toward the tips. Each
    # feather has a pale outer edge and an exposed copper shaft at its fold.
    for side in (-1, 1):
        for quill in range(5):
            length = 24 - quill
            for d in range(length + 1):
                x = C + side*d
                center_z = 13 + quill*5 + d//3
                width = min(3, length - d)
                height = 26 + max(0, d - 10)//3 + (1 if quill == 0 else 0)
                for dz in range(-width, width+1):
                    material = "smooth_quartz" if abs(dz) == width else "waxed_oxidized_cut_copper"
                    if dz == 0:
                        material = "waxed_weathered_cut_copper"
                    t.put(x, height, center_z+dz, M(material))
    # At the crown, two swept tips rise above a split finial; the raked spine
    # continues through the roof to the real rear piers of the audience screen.
    for side in (-1, 1):
        for d in range(12):
            y = 26 + d*2//3
            x = C + side*(2+d)
            z = 15 - d//3
            t.fill(x, y, z, x, y+2, z+1, M("smooth_quartz"))
            t.put(x, y, z+2, M("waxed_weathered_cut_copper"))
            if d > 3:
                t.put(x, y+2, z, M("cut_copper"))
            if d in (3,7,11):
                t.put(x, y-1, z+2, M("waxed_oxidized_cut_copper"))
    for x in (32, 40):
        t.put(x, DECK, 27, M("ochre_froglight"))
    # Rear screen and elevated cushion face the climbing visitor.
    t.fill(31, DECK+1, 14, 41, 20, 14, M("spruce_planks"))
    for x in range(31, 42):
        rise = 5 - abs(x - C)
        t.fill(x, 19, 15, x, 20+rise, 15, M("quartz_pillar"))
        t.put(x, 20+rise, 16, M("gold_block" if x == C else "cut_copper"))
    t.fill(33, DECK+1, 16, 39, DECK+1, 19, M("smooth_quartz"))
    t.fill(35, DECK+2, 16, 37, DECK+2, 18, M("red_carpet"))
    for x in (28, 44):
        t.fill(x, DECK+1, 21, x, DECK+1, 24, stair("spruce", "north"))


def ascent(t):
    for z in range(38, 69):
        y = G + min(12, max(0, (62-z)//2))
        for x in range(32, 41):
            t.clear(x, y+1, z, x, max(y+1, DECK+3), z)
            if x in (32, 40) and z < 62:
                state = M("polished_andesite")
            elif 38 < z < 62 and z % 2 == 0:
                state = stair("stone_brick", "north")
            else:
                state = M("gravel" if z >= 62 else "stone_bricks")
            t.fill(x, G-1, z, x, y-1, z, M("andesite"))
            t.put(x, y, z, state)
        if z in (41, 49, 57):
            for x in (32, 40):
                t.put(x, y+1, z, M("stone_brick_wall"))
                t.put(x, y+2, z, lantern_floor())


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    spur(t)
    flight_court(t)
    ascent(t)
    for x, z in ((8, 48), (14, 57), (60, 55), (63, 44), (11, 9), (61, 7)):
        t.tree(x, z, "spruce", 7, 3)
    # Outcrops vary in height above a cold, sparsely flowered upland.
    for cx, cz, h in ((8,34,4),(15,42,3),(54,48,4),(64,34,3),(20,8,4),(49,9,3)):
        for dx in range(-2,3):
            for dz in range(-2,3):
                depth = h - abs(dx) - abs(dz)
                if depth <= 0:
                    continue
                x,z = cx+dx,cz+dz
                y = G
                while t.get(x,y+1,z) != M("air"):
                    y += 1
                t.fill(x,y+1,z,x,y+depth,z,M("andesite"))
                t.put(x,y+depth,z,M("calcite") if depth>=3 else M("tuff"))
    for x in range(3,70):
        for z in range(3,67):
            if 31 <= x <= 41 or t.get(x,G+1,z) != M("air"):
                continue
            r = rnd(x,G,z,89)
            if r < .12:
                t.put(x,G+1,z,M("fern" if r<.032 else "short_grass"))
    light_pass(bp, lambda x, y, z: 5 <= x <= 67 and 12 <= z <= 44 and y < 25, DECK+1,
               lambda x, y, z: lantern_floor(), label="jia")
    t.check_support()
