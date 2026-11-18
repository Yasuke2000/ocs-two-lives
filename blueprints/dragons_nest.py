"""The Dragon's Nest: the stronghold of the dragons on the highest peak of the Great Canaat Mountains.

SIZE (73, 46, 73). Ground layer y 8 (stone, snow on top; stone and ice below), you walk at y 9; everything above is air,
so placement shaves the summit inside the box and the terrain skirt does the rest. Arrival and anchor point: blueprint
(36, 9, 62), at the south entrance gap of the nest wall, facing north.

Canon gives only: the Dragon's Nest is a stronghold at the very top of the tallest peak of the Great Canaat Mountains,
which the dragon lords hold, and dragons grow stronger the higher up the range they live (Tensura wiki: Great Canaat
Mountains, Central World). Everything about how it looks is our interpretation: a wide roosting bowl woven of spruce
and dark-oak trunks lined with hay, ringed by a jagged wall of blackstone, stone and bone-white calcite with a
south gap, eight broken spires, three smaller roosts for the lords' young, scattered bones and scorch marks, a
low hoard of gold and amethyst, and a central perch of stacked rock with a sea lantern. Snow lies on everything. Every
spawnable spot inside the wall has block light (checked when this builds).

Sources and what was and was not found: design/lore/dragons_nest.md.
"""
import math

from _dwargon_lib import AIR, fbm2, noise2, rnd
from _sites_lib import M, air_above, light_up, line, pick, put

SIZE = (73, 46, 73)
SX, SY, SZ = SIZE
G = 8
F = 9
C = 36
ANCHOR = (36, F, 62)
PARTS = [0, 37]

LANTERN = M("sea_lantern")
SNOW = M("snow_block")
CRAG = [(M("stone"), 8), (M("andesite"), 3), (M("blackstone"), 4), (M("calcite"), 2), (M("tuff"), 3), (M("packed_ice"), 1),
        (M("snow_block"), 3), (M("gravel"), 1)]


def build(bp):
    blocks = bp.blocks
    air_above(bp, G)
    # foundation disc, a little irregular, snowy on top
    for x in range(SX):
        for z in range(SZ):
            for y in range(0, G):
                blocks[(x, y, z)] = M("stone") if y < G - 2 else M("snow_block") if y == G - 1 else M("stone")
            d = math.hypot(x - C, z - C)
            blocks[(x, G, z)] = SNOW if rnd(x, 0, z, 3) < 0.7 else M("stone") if rnd(x, 1, z, 3) < 0.6 else M("packed_ice")

    # the nest bowl: spruce and dark-oak trunks woven in rings, hay and bones inside
    R = 20.5
    for x in range(SX):
        for z in range(SZ):
            d = math.hypot(x - C, z - C)
            if d <= R:
                depth = 3 * (1 - (d / R) ** 2)
                top = G - int(round(depth))  # floor level of the bowl (block y)
                for y in range(top + 1, G + 1):
                    blocks[(x, y, z)] = AIR
                if depth >= 1:
                    ring = int(d) % 3
                    blocks[(x, top, z)] = (M("spruce_log[axis=x]") if abs(x - C) > abs(z - C) else M("spruce_log[axis=z]")) if ring == 0 else \
                        (M("dark_oak_log[axis=y]") if ring == 1 and rnd(x, 2, z, 4) < 0.35 else M("hay_block[axis=y]") if rnd(x, 3, z, 5) < 0.55 else M("coarse_dirt"))
                    if rnd(x, 4, z, 6) < 0.05 and top < G:
                        blocks[(x, top + 1, z)] = M("bone_block[axis=y]") if rnd(x, 5, z, 7) < 0.5 else M("hay_block[axis=y]")
                else:
                    blocks[(x, G, z)] = pick([(M("coarse_dirt"), 3), (M("gravel"), 2), (SNOW, 2), (M("spruce_log[axis=x]"), 1)], rnd(x, 6, z, 8))

    # the wall: a jagged ring r 21..25 with a gap at the south, heights up to 12
    for x in range(SX):
        for z in range(SZ):
            d = math.hypot(x - C, z - C)
            if not 20.8 < d <= 25.5:
                continue
            ang = math.degrees(math.atan2(z - C, x - C))  # south = +90
            if abs(ang - 90) < 11:
                continue
            h = 4 + 8 * fbm2(x, z, 7, 11) + 3 * (1 - abs(d - 23) / 2.5)
            h = int(max(2, h))
            for y in range(G + 1, G + 1 + h):
                blocks[(x, y, z)] = pick(CRAG, rnd(x, y, z, 12))
            blocks[(x, G + h, z)] = SNOW if rnd(x, 7, z, 13) < 0.6 else M("snow[layers=3]")
    # eight spires on the wall, several broken
    for i, (x, z) in enumerate(bp.around(C, C, 23.0, 8, start_deg=22.5)):
        h = (19, 14, 20, 11, 17, 21, 13, 18)[i]
        for y in range(G + 1, G + 1 + h):
            for dx in (0, 1) if y < G + h - 6 else (0,):
                for dz in (0, 1) if y < G + h - 6 else (0,):
                    blocks[(x + dx, y, z + dz)] = M("blackstone") if (y + i) % 4 else M("calcite")
        blocks[(x, G + h + 1, z)] = M("soul_lantern[hanging=false]")
    # three smaller roosts for the young, half sunk in the floor
    for (rx, rz) in ((26, 29), (45, 27), (36, 47)):
        for x in range(rx - 4, rx + 5):
            for z in range(rz - 4, rz + 5):
                d = math.hypot(x - rx, z - rz)
                if d <= 3.6:
                    blocks[(x, G - 1, z)] = M("hay_block[axis=y]") if rnd(x, 8, z, 14) < 0.6 else M("dark_oak_log[axis=y]")
                    blocks[(x, G, z)] = AIR
                elif d <= 4.5:
                    blocks[(x, G, z)] = M("spruce_log[axis=x]") if (x + z) % 2 else M("dark_oak_log[axis=z]")
                    if d <= 4.0 and rnd(x, 9, z, 15) < 0.5:
                        blocks[(x, G + 1, z)] = M("bone_block[axis=y]")
    # the hoard: gold, raw gold and amethyst heaped north of the middle
    for dx in range(-4, 5):
        for dz in range(-3, 3):
            x, z = C + dx, C - 9 + dz
            h = int(2.4 - math.hypot(dx / 1.6, dz) + rnd(x, 1, z, 16) * 1.2)
            for y in range(G, G + max(0, h) + 1):
                blocks[(x, y, z)] = pick([(M("gold_block"), 3), (M("raw_gold_block"), 3), (M("amethyst_block"), 2), (M("hay_block[axis=y]"), 1)],
                                         rnd(x, y, z, 17))
    # the perch: stacked rock in the middle, broken, with a sea lantern on top
    for y in range(G + 1, G + 12):
        r = 3.2 - (y - G) * 0.18
        for x in range(C - 4, C + 5):
            for z in range(C - 4, C + 5):
                if math.hypot(x - C, z - C) <= r + rnd(x, y, z, 18) * 0.6:
                    blocks[(x, y, z)] = pick(CRAG, rnd(x, y, z, 19))
    blocks[(C, G + 12, C)] = LANTERN
    blocks[(C, G + 11, C)] = M("polished_blackstone")
    # scorch marks: blackstone patches and basalt on the floor; a rib cage of bone near the west wall
    for i in range(26):
        x, z = C - 18 + int(rnd(i, 1, 2, 31) * 36), C - 18 + int(rnd(i, 2, 2, 31) * 36)
        if math.hypot(x - C, z - C) < 19 and blocks.get((x, G, z)) is not None:
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if rnd(x + dx, 3, z + dz, 32) < 0.7 and blocks.get((x + dx, G + 1, z + dz)) in (None, AIR) and blocks.get((x + dx, G, z + dz)) not in (None, AIR):
                        blocks[(x + dx, G, z + dz)] = M("blackstone") if rnd(x + dx, 4, z + dz, 33) < 0.6 else M("basalt[axis=y]")
    for k in range(6):  # ribs: half circles of bone block over a spine on the floor
        z = 28 + k * 3
        for a in range(0, 181, 15):
            put(bp, 19 + round(4.0 * math.cos(math.radians(a))), G + 1 + round(4.0 * math.sin(math.radians(a))), z, M("bone_block[axis=y]"))
    for z in range(26, 46):
        put(bp, 19, G + 1, z, M("bone_block[axis=z]"))
    # an approach: packed snow and stones leading up to the gap, with two lanterns
    for z in range(46, SZ):
        for x in range(C - 2, C + 3):
            blocks[(x, G, z)] = M("stone_bricks") if rnd(x, 0, z, 41) < 0.5 else M("cobblestone")
    for z in (49, 55, 61):
        for x in (C - 3, C + 3):
            put(bp, x, F, z, M("cobblestone_wall[east=false,north=false,south=false,up=true,waterlogged=false,west=false]"))
            put(bp, x, F + 1, z, M("soul_lantern[hanging=false]"))

    cands = [(x, y, z) for x in range(SX) for z in range(SZ) for y in range(G - 3, G + 4)
             if math.hypot(x - C, z - C) <= 21 or (abs(x - C) <= 4 and z >= 46)]

    def add_light(x, y, z):
        put(bp, x, y, z, M("cobblestone_wall[east=false,north=false,south=false,up=true,waterlogged=false,west=false]"))
        put(bp, x, y + 1, z, M("soul_lantern[hanging=false]"))

    light_up(bp, cands, add_light, spread=9)
    return None
