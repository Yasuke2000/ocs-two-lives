"""City of the Forgotten Dragon: Milim Nava's capital, a poor dragon-worshipping town round an ancient temple.

Lore notes and sources: design/lore/forgotten_dragon_city.md. SIZE (121, 44, 125), centre column x 60, saved as
four z slabs forgotten_dragon_city_0..3 (PARTS). Ground layer y 4 (coarse dirt, grass, packed mud; you walk at
y 5); everything above is air so placing clears trees and hills in the box. The temple faces south (+z).
Arrival point: blueprint (60, 5, 118) at the south end of the processional avenue, facing north.
Our interpretation of a place canon barely describes (a commune of Dragon Faithful and dragonewts round a
Central Temple that hands out goods): the city grew inside the bones of a dead ancient dragon. From the south:
the avenue (x 56-64, smooth sandstone) under six rib arches of bone blocks (z 72-112, 20 wide, 13 high),
two open granaries with thatch gables either side (z 74-94; the Central Temple distributes goods from
them), a bone-fire plaza, and the Central Temple: a five-tier stepped pyramid of sandstone and terracotta
(base x 40-80, z 14-54, 3 high per tier, top 17 wide at y 20) fronted by a colossal dragon skull (cranium
with glowing eye sockets, horns to y 30, fanged snout) whose open mouth (x 56-64) is the temple gate. A
tunnel leads to the distribution hall inside (x 49-71, z 22-46): pillars, stacks of barrels and hay, a
counter, and the throne of the Demon Lord Milim (bone, pink terracotta) on a dais at the back. Stairs cut into
the east and west faces climb to a pavilion on the summit with a bonfire. Round mud-brick huts with
Tensura thatch cone roofs (lit inside, a bed and a barrel in each) lie either side, with campfires,
dry fields and a pond for the nearby lake. Every spawnable spot below y 30 has block light (checked when
this builds).
"""
import math

from _dwargon_lib import AIR, noise2, rnd
from _lords_lib import (M, clear, cone, disc_cells, fill, fill_air, light_pass, mix, pixel_art, put, rect_ring,
                        ring_cells, roofed, round_tower, slab, stair)

SIZE = (121, 44, 125)
SX, SY, SZ = SIZE
C = 60
G = 4
F = G + 1
PARTS = [0, 31, 62, 93]
ARRIVAL = (60, F, 118)

THATCH = "tensura:thatch_block"
THATCH_STAIRS = "tensura:thatch_stairs"
BONE = mix(31, (M("bone_block[axis=y]"), 58), (M("calcite"), 28), (M("white_terracotta"), 14))
SAND = mix(32, (M("sandstone"), 52), (M("cut_sandstone"), 28), (M("smooth_sandstone"), 12), (M("orange_terracotta"), 8))
PAVE = mix(33, (M("smooth_sandstone"), 55), (M("cut_sandstone"), 30), (M("polished_granite"), 15))
PINK = M("pink_terracotta")
LANTERN = M("lantern[hanging=false]")
LANTERN_H = M("lantern[hanging=true]")

TIERS = 5
TH = 3                       # tier height and inset
X0, X1, Z0, Z1 = 40, 80, 14, 54   # temple base (tier 1); the south face is z 54
TOP = G + TIERS * TH         # top block layer (y 19); the summit is walked at y 20


def ground():
    for x in range(SX):
        for z in range(SZ):
            for y in range(0, G):
                bp.set(x, y, z, M("stone") if y < 2 else M("dirt"))
            n = noise2(x, z, 5, 41)
            top = M("coarse_dirt") if n < 0.42 else M("grass_block") if n < 0.74 else M("packed_mud") if n < 0.88 else M("gravel")
            bp.set(x, G, z, top)


def temple():
    for k in range(TIERS):
        i = TH * k
        y0, y1 = G + 1 + TH * k, G + TH * (k + 1)
        for y in range(y0, y1 + 1):
            for x in range(X0 + i, X1 - i + 1):
                for z in range(Z0 + i, Z1 - i + 1):
                    edge = x in (X0 + i, X1 - i) or z in (Z0 + i, Z1 - i)
                    band = y == y1
                    bp.set(x, y, z, M("cut_sandstone") if band else (M("orange_terracotta") if edge and y == y0 and k % 2 == 0
                                                                    else SAND(x, y, z)))
        # a red terracotta frieze under each tier's lip
        for x in range(X0 + i, X1 - i + 1):
            for z in (Z0 + i, Z1 - i):
                put(bp, x, y1 - 1, z, M("red_terracotta") if (x // 2) % 2 else M("chiseled_sandstone"))
        for z in range(Z0 + i, Z1 - i + 1):
            for x in (X0 + i, X1 - i):
                put(bp, x, y1 - 1, z, M("red_terracotta") if (z // 2) % 2 else M("chiseled_sandstone"))
    # stairs cut into the east and west faces (z 33..35), 1:1 slope like the tiers
    for side, x_start, dirn, facing in (("east", X1, -1, "west"), ("west", X0, 1, "east")):
        for s in range(15):
            x = x_start + dirn * s
            for z in (33, 34, 35):
                for y in range(G + 1 + s, TOP + 1):
                    bp.set(x, y, z, AIR)
                bp.set(x, G + 1 + s, z, stair("sandstone", facing))
        for z in (32, 36):
            for s in range(15):
                put(bp, x_start + dirn * s, G + 2 + s, z, M("sandstone_wall"))
            put(bp, x_start + dirn * -1, G + 1, z, M("sandstone_wall"))
    # summit pavilion: 11 x 11 with eight columns, flat terracotta roof, bonfire and a throne-like seat
    cx, cz = C, (Z0 + Z1) // 2
    for dx in (-5, 0, 5):
        for dz in (-5, 0, 5):
            if dx == 0 and dz == 0:
                continue
            for y in range(TOP + 1, TOP + 6):
                put(bp, cx + dx, y, cz + dz, M("bone_block[axis=y]") if y % 2 else M("chiseled_sandstone"))
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            edge = abs(x - cx) == 6 or abs(z - cz) == 6
            put(bp, x, TOP + 6, z, M("red_terracotta") if edge else M("orange_terracotta"))
            if edge:
                put(bp, x, TOP + 7, z, slab("red_sandstone"))
    for y in range(TOP + 2, TOP + 6):
        put(bp, cx, y, cz, AIR)
    put(bp, cx, TOP + 1, cz, M("campfire[facing=south,lit=true,signal_fire=true]"))
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            if max(abs(x - cx), abs(z - cz)) == 3:
                put(bp, x, TOP + 1, z, M("smooth_sandstone_slab[type=bottom]")) if (x + z) % 2 else None
    for dx in (-5, 5):
        for dz in (-5, 5):
            put(bp, cx + dx, TOP + 6, cz + dz, M("sandstone_wall"))  # lantern posts sit in the corner columns
    for dx, dz in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        put(bp, cx + dx, TOP + 1, cz + dz, M("bone_block[axis=y]"))
        for y in range(TOP + 2, TOP + 6):
            put(bp, cx + dx, y, cz + dz, M("bone_block[axis=y]") if y % 2 else M("chiseled_sandstone"))
        put(bp, cx + dx + (1 if dx < 0 else -1), TOP + 5, cz + dz, LANTERN_H)


SKULL_Y = G + 8


def skull():
    cz0, cz1 = 54, 61
    # cranium: an ellipse in x/y extruded 8 deep (front face z 61)
    for x in range(48, 73):
        for y in range(G + 1, G + 18):
            v = ((x - C) / 12.0) ** 2 + ((y - SKULL_Y) / 9.2) ** 2
            if v <= 1.0:
                for z in range(cz0, cz1 + 1):
                    # the back of the cranium rounds off
                    if z == cz0 and v > 0.7:
                        continue
                    bp.set(x, y, z, BONE(x, y, z))
    # snout and upper jaw, narrowing to the nose
    for z in range(cz1 + 1, 65):
        half = 7 - (z - cz1)
        for x in range(C - half, C + half + 1):
            for y in range(G + 1, G + 10 - (z - cz1) // 2):
                bp.set(x, y, z, BONE(x, y, z))
    # brow ridge and cheek ridges
    for x in range(50, 71):
        put(bp, x, G + 15, cz1, M("calcite"))
        put(bp, x, G + 15, cz1 - 1, M("calcite"))
    # eye sockets with a soul fire glowing inside
    for ex in (55, 65):
        for x in range(ex - 1, ex + 2):
            for y in range(G + 11, G + 14):
                for z in range(cz1 - 2, cz1 + 1):
                    bp.set(x, y, z, AIR)
        for x in range(ex - 1, ex + 2):
            for y in range(G + 11, G + 14):
                bp.set(x, y, cz1 - 3, M("black_concrete"))
        bp.set(ex, G + 11, cz1 - 2, M("soul_lantern[hanging=false]"))
    # nostrils
    for x in (C - 3, C + 3):
        for y in (G + 7, G + 8):
            put(bp, x, y, 64, AIR)
            put(bp, x, y, 63, AIR)
    # horns: curve outward and up, tip as an end rod
    for sgn in (-1, 1):
        for i in range(14):
            x = C + sgn * (11 + i // 2)
            y = G + 14 + i
            z = 57 - i // 4
            for t in (0, 1):
                put(bp, x, y, z + t, M("bone_block[axis=y]") if i % 3 else M("calcite"))
                put(bp, x - sgn, y, z + t, M("bone_block[axis=y]"))
        put(bp, C + sgn * (11 + 14 // 2), G + 28, 55, M("end_rod[facing=up]"))
    # the mouth: a tunnel x 56..64 through the snout and the pyramid to the hall
    for x in range(56, 65):
        for y in range(G + 1, G + 8):
            for z in range(46, 65):
                bp.set(x, y, z, AIR)
        for z in range(46, 65):
            bp.set(x, G, z, M("smooth_sandstone"))
    # fangs
    for x in (56, 58, 60, 62, 64):
        for z in (64, 63, 61):
            for y, state in ((G + 7, BONE(x, 9, z)), (G + 6, BONE(x, 8, z))):
                if x in (56, 64) or y == G + 7:
                    bp.set(x, y, z, state)
        if x in (56, 64):
            bp.set(x, G + 5, 64, M("calcite"))
    for x in (56, 64):
        for y in (G + 1, G + 2):
            bp.set(x, y, 64, BONE(x, y, 64))
    # pink banners hung from the brow (Milim's colour, our choice)
    for x in (53, 67):
        for y in range(G + 1, G + 6):
            put(bp, x, y, cz1 + 1, M("pink_wool"))
        put(bp, x, G + 6, cz1 + 1, M("pink_wool"))


def hall():
    # carve the distribution hall inside tiers 1-3: x 49..71, z 22..46, y F..G+8
    clear(bp, 49, F, 22, 71, G + 8, 46)
    for x in range(49, 72):
        for z in range(22, 47):
            bp.set(x, G, z, M("smooth_sandstone") if (x + z) % 4 else M("polished_granite"))
    # pillars in two rows, hanging lanterns
    for z in (26, 31, 36, 41):
        for x in (53, 67):
            for y in range(F, G + 9):
                bp.set(x, y, z, M("bone_block[axis=y]") if y % 3 else M("chiseled_sandstone"))
        for x in (56, 64):
            bp.set(x, G + 7, z, M("chain[axis=y]"))
            bp.set(x, G + 6, z, LANTERN_H)
    # carpet aisle in pink, a counter where the Faithful hand out food, stacks of goods
    for z in range(23, 47):
        for x in range(58, 63):
            bp.set(x, F, z, M("pink_carpet"))
    for x in range(50, 53):
        bp.set(x, F, 40, M("smooth_sandstone_slab[type=top]"))
    for z in range(29, 44):
        bp.set(51, F, z, M("smooth_sandstone_slab[type=top]"))
        bp.set(50, F, z, M("barrel[facing=up]") if z % 2 else M("hay_block[axis=y]"))
        bp.set(50, F + 1, z, M("hay_block[axis=y]") if z % 4 == 0 else AIR)
    for z in range(29, 44):
        bp.set(69, F, z, M("smooth_sandstone_slab[type=top]"))
        bp.set(70, F, z, M("barrel[facing=up]") if z % 2 == 0 else M("hay_block[axis=y]"))
    # dais and the throne (back wall, z 22..)
    for x in range(54, 67):
        for z in range(22, 26):
            bp.set(x, F, z, M("smooth_sandstone"))
    for x in range(55, 66):
        for z in range(22, 24):
            bp.set(x, F + 1, z, M("smooth_sandstone"))
    for x in range(54, 67):
        bp.set(x, F, 26, stair("smooth_sandstone", "north"))
    for x in range(55, 66):
        bp.set(x, F + 1, 24, stair("smooth_sandstone", "north"))
    fill(bp, C - 1, F + 2, 22, C + 1, F + 2, 23, M("bone_block[axis=y]"))
    for y in range(F + 3, F + 9):
        for x in range(C - 2, C + 3):
            put(bp, x, y, 22, BONE(x, y, 22))
    put(bp, C, F + 9, 22, M("pink_terracotta"))
    put(bp, C - 2, F + 3, 23, M("pink_terracotta"))
    put(bp, C + 2, F + 3, 23, M("pink_terracotta"))
    put(bp, C, F + 3, 23, stair("quartz", "south"))
    for x in (C - 4, C + 4):
        put(bp, x, F + 2, 23, M("bone_block[axis=y]"))
        put(bp, x, F + 3, 23, M("soul_lantern[hanging=false]"))
        for y in range(F + 2, F + 6):
            put(bp, x, y, 22, M("pink_wool"))


def ribs():
    for z in (72, 80, 88, 96, 104, 112):
        for deg in range(0, 181, 2):
            a = math.radians(deg)
            x = round(C + 10 * math.cos(a))
            y = F + round(13 * math.sin(a))
            put(bp, x, y, z, BONE(x, y, z))
        for x, sgn in ((C - 10, -1), (C + 10, 1)):
            put(bp, x, F, z, BONE(x, 1, z))
            put(bp, x + sgn, F, z, M("bone_block[axis=y]"))
            put(bp, x, F + 1, z, BONE(x, 2, z))
        # spine ridge and a lantern from the top
        put(bp, C, F + 13, z, BONE(C, 13, z))
        put(bp, C, F + 12, z, M("chain[axis=y]"))
        put(bp, C, F + 11, z, LANTERN_H)


def avenue():
    for z in range(55, SZ):
        for x in range(C - 4, C + 5):
            if bp.blocks.get((x, F, z)) is None or bp.blocks[(x, F, z)] == AIR:
                bp.set(x, G, z, PAVE(x, G, z))
    # plaza in front of the skull
    for z in range(58, 72):
        for x in range(C - 11, C + 12):
            bp.set(x, G, z, PAVE(x, G, z))
    # bone bonfires in the plaza
    for x in (C - 9, C + 9):
        bp.set(x, F, 66, M("bone_block[axis=y]"))
        bp.set(x, F + 1, 66, M("campfire[facing=south,lit=true]"))
    # lamp posts down the avenue
    for z in range(76, SZ - 2, 8):
        for x in (C - 6, C + 6):
            for k in range(1, 4):
                bp.set(x, G + k, z, M("sandstone_wall"))
            bp.set(x, G + 4, z, LANTERN)
    # signpost at the south end
    for k in range(1, 4):
        put(bp, C + 6, G + k, 121, M("sandstone_wall"))
    put(bp, C + 6, G + 4, 121, M("lantern[hanging=false]"))


def granary(x0, x1, z0, z1):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, G, z, M("smooth_sandstone"))
    for x in (x0, x1):
        for z in range(z0, z1 + 1, 4):
            for y in range(F, F + 4):
                bp.set(x, y, z, M("bone_block[axis=y]") if y == F + 1 else M("sandstone_wall") if y == F else M("cut_sandstone"))
    # gable roof of thatch over the x extent
    w = x1 - x0 + 1
    for k in range((w + 1) // 2):
        xl, xr = x0 - 1 + k, x1 + 1 - k
        y = F + 4 + k
        for z in range(z0 - 1, z1 + 2):
            if xl < xr:
                bp.set(xl, y, z, f"{THATCH_STAIRS}[facing=east,half=bottom]")
                bp.set(xr, y, z, f"{THATCH_STAIRS}[facing=west,half=bottom]")
            else:
                bp.set(xl, y, z, THATCH)
    # goods: barrels and hay along the long sides, a counter in the middle
    for z in range(z0 + 1, z1, 2):
        for x in (x0 + 1, x1 - 1):
            bp.set(x, F, z, M("barrel[facing=up]") if (z // 2) % 2 else M("hay_block[axis=y]"))
    for z in range(z0 + 3, z1 - 2):
        bp.set((x0 + x1) // 2, F, z, M("smooth_sandstone_slab[type=top]"))
    for z in (z0 + 4, z1 - 4):
        bp.set((x0 + x1) // 2, F + 3, z, M("chain[axis=y]"))
        bp.set((x0 + x1) // 2, F + 2, z, LANTERN_H)


HUTS = []


def hut(hx, hz, door):
    r = 3
    for x, z in ring_cells(hx, hz, r):
        for y in range(F, F + 3):
            bp.set(x, y, z, M("mud_bricks"))
    for x, z in disc_cells(hx, hz, r - 1):
        bp.set(x, G, z, M("packed_mud"))
    # door gap on the `door` side
    dx, dz = {"n": (0, -r), "s": (0, r), "e": (r, 0), "w": (-r, 0)}[door]
    for y in (F, F + 1):
        bp.set(hx + dx, y, hz + dz, AIR)
    bp.set(hx + dx, F + 2, hz + dz, M("mud_bricks"))
    # thatch cone roof, solid
    for k in range(6):
        rr = 4.6 - k * 0.85
        for x, z in disc_cells(hx, hz, max(rr, 0.5)):
            bp.set(x, F + 3 + k, z, THATCH)
    bp.set(hx, F + 9, hz, M("oak_fence"))
    # interior: lantern from the roof, bed, barrel
    bp.set(hx, F + 2, hz, LANTERN_H)
    bp.set(hx - 1, F, hz - 1, M("red_bed[facing=north,part=head]"))
    bp.set(hx - 1, F, hz, M("red_bed[facing=north,part=foot]"))
    bp.set(hx + 1, F, hz + 1, M("barrel[facing=up]"))
    HUTS.append((hx, hz))


def pen(x0, z0, x1, z1):
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            put(bp, x, F, z, M("acacia_fence"))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            put(bp, x, F, z, M("acacia_fence"))


def field(x0, z0, x1, z1):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x == (x0 + x1) // 2 and z == (z0 + z1) // 2:
                bp.set(x, G, z, M("water[level=0]"))
            else:
                bp.set(x, G, z, M("farmland[moisture=7]"))
                bp.set(x, F, z, M(f"wheat[age={int(rnd(x, 1, z, 43) * 5) + 1}]") if rnd(x, 2, z, 44) < 0.8 else AIR)
    rect_ring(bp, x0 - 1, z0 - 1, x1 + 1, z1 + 1, F, M("acacia_fence"))


def pond(cx, cz, r):
    for x, z in disc_cells(cx, cz, r):
        d = math.hypot(x - cx, z - cz)
        bp.set(x, G, z, M("water[level=0]"))
        if d < r - 2:
            bp.set(x, G - 1, z, M("water[level=0]"))
        bp.set(x, G - 2, z, M("clay"))
    for x, z in ring_cells(cx, cz, r + 1):
        bp.set(x, G, z, M("sand") if (x + z) % 3 else M("coarse_dirt"))


def settlement():
    spots = []
    for gx, xs in ((0, (14, 28)), (1, (92, 106))):
        for zi, z in enumerate(range(44, 112, 13)):
            for xi, x in enumerate(xs):
                jx = int((rnd(x, z, 1, 51) - 0.5) * 5)
                jz = int((rnd(x, z, 2, 52) - 0.5) * 5)
                spots.append((x + jx, z + jz, "e" if gx == 0 else "w"))
    for x in (12, 26, 94, 108):
        for z in (12, 26):
            spots.append((x + int((rnd(x, z, 3, 53) - 0.5) * 4), z + int((rnd(x, z, 4, 54) - 0.5) * 4), "s"))
    for hx, hz, door in spots:
        if 100 < hx < 114 and 94 < hz < 108:
            continue  # the pond
        if 8 < hx < 26 and 100 < hz < 118:
            continue  # the field
        hut(hx, hz, door)
        # a campfire and a drying rack beside some huts
        if rnd(hx, hz, 5, 55) < 0.5:
            ox = 5 if door == "e" else -5 if door == "w" else 0
            oz = 5 if door == "s" else 0
            put(bp, hx + ox, F, hz + oz, M("campfire[facing=south,lit=true]"))
    pond(105, 99, 7)
    field(10, 102, 24, 114)
    pen(36, 100, 46, 108)
    pen(76, 100, 86, 108)
    # a few savanna acacias, then the huts can sit between them
    for k in range(40):
        x = int(rnd(k, 1, 6, 61) * (SX - 10)) + 5
        z = int(rnd(k, 2, 6, 62) * (SZ - 10)) + 5
        if any(math.hypot(x - hx, z - hz) < 7 for hx, hz in HUTS) or abs(x - C) < 16 or (30 < x < 90 and z < 58):
            continue
        if bp.blocks.get((x, G, z), "").endswith("water[level=0]") or math.hypot(x - 105, z - 99) < 10 or (4 < x < 28 and 98 < z < 120):
            continue
        h = 4 + int(rnd(k, 3, 6, 63) * 3)
        for y in range(F, F + h):
            put(bp, x, y, z, M("acacia_log[axis=y]"))
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if math.hypot(dx, dz) <= 3.2 and rnd(x + dx, z + dz, k, 64) < 0.85:
                    put(bp, x + dx, F + h, z + dz, M("acacia_leaves[persistent=true]"))
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                put(bp, x + dx, F + h + 1, z + dz, M("acacia_leaves[persistent=true]"))


def build(b):
    global bp
    bp = b
    fill_air(bp, 0)
    ground()
    temple()
    skull()
    hall()
    ribs()
    avenue()
    granary(C + 14, C + 27, 74, 94)
    granary(C - 27, C - 14, 74, 94)
    settlement()

    def region(x, y, z):
        return 3 <= x <= SX - 4 and 3 <= z <= SZ - 4 and (y <= 30 or roofed(bp, x, y, z))

    n = light_pass(bp, region, G + 1, lambda x, y, z: LANTERN, post=lambda x, y, z: [
        (0, M("sandstone_wall")), (1, M("sandstone_wall")), (2, M("sandstone_wall")), (3, LANTERN)],
        label="forgotten_dragon_city")
    print(f"forgotten_dragon_city: {n} extra lamps")
