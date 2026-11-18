"""Clayman's Castle: the dark fortress of the Demon Lord Clayman, "Crazy Pierrot", in the Puppet Nation of Jistav.

Lore notes and sources: design/lore/clayman_castle.md. SIZE (109, 66, 109), centre column (54, 54), saved as
four z slabs clayman_castle_0..3 (PARTS). Ground layer y 5 (outside: podzol and coarse dirt, you walk at y 6);
the castle stands on a deepslate platform (top y 7, you walk at y 8) ringed by a moat (square ring, 37-41
blocks from the centre, water y 2-5) and an outer bank. The gate faces south (+z). Arrival point: blueprint
(54, 6, 102) on the approach road, facing north.
From the south: road, a stone bridge (z 90-97, deck y 7, walk y 8) over the moat, the gatehouse in the
curtain wall (wall 3 thick, y 8-17, wall walk y 18, crenellated; opening x 51-57, y 8-16, raised portcullis,
two round towers with spires at x 45 and 63), the courtyard (paved in deepslate tiles, lamp posts, "puppet"
stands of skulls on posts and two gallows frames hung with chains and soul lanterns, the marionette motif),
and the keep (x 40-68, z 34-62, walls to y 32, four corner turrets r 4 with spires, a great central spire to
y 62, gothic windows of purple glass, buttresses, a giant pierrot mask over the great door).
Inside the keep: the entrance hall (south, z 49-60) with a stair along its west wall up to a gallery
(floor y 19) that overlooks the throne hall through the partition (z 47-48), and the 22-block-high throne
hall (z 36-46): purple carpet, two rows of pillars, a three-step dais with the throne, the pierrot mask
on the north wall and marionette controllers (chains and soul lanterns) hung from the vault. The curtain wall
has four corner towers (r 5), three mid towers (r 4) and wall-walk stairs inside the gate. The moat, the
platform and the bank are part of the build; dead trees stand on the outer bank. Every spawnable spot
inside the moat ring (and on the bridge and bank) has block light (checked when this builds).
"""
import math

from _dwargon_lib import AIR, noise2, rnd
from _lords_lib import (M, clear, cone, disc_cells, crenellate_ring, fill, fill_air, floor_disc, light_pass, mix, pixel_art,
                        put, rect_ring, roofed, round_tower, slab, stair)

SIZE = (109, 66, 109)
SX, SY, SZ = SIZE
C = 54
G = 5            # ground layer (top block outside the moat)
PY = 7           # platform top block
W = PY + 1       # walking level in the castle
WALL_TOP = 17    # curtain wall top block (wall walk), you walk at 18
PARTS = [0, 28, 55, 82]
ARRIVAL = (54, 6, 102)

BRICK = mix(11, (M("deepslate_bricks"), 62), (M("cracked_deepslate_bricks"), 14),
            (M("polished_blackstone_bricks"), 16), (M("deepslate_tiles"), 8))
TILE = mix(12, (M("deepslate_tiles"), 66), (M("cracked_deepslate_tiles"), 20), (M("polished_deepslate"), 14))
SOUL = M("soul_lantern[hanging=false]")
SOUL_H = M("soul_lantern[hanging=true]")
PANE = M("purple_stained_glass_pane")
ROOF_STAIR = "deepslate_tile"


def dm(x, z) -> int:
    return max(abs(x - C), abs(z - C))


def ground():
    for x in range(SX):
        for z in range(SZ):
            d = dm(x, z)
            for y in range(0, G):
                put_s = M("deepslate") if y < 2 else M("stone") if y < 4 else M("dirt")
                bp.set(x, y, z, put_s)
            n = noise2(x, z, 6, 4)
            bp.set(x, G, z, M("podzol") if n < 0.5 else M("coarse_dirt") if n < 0.75 else M("grass_block"))
            if d <= 36:
                for y in range(2, PY + 1):
                    bp.set(x, y, z, M("deepslate") if y < PY - 1 else M("cobbled_deepslate"))
                bp.set(x, PY, z, TILE(x, PY, z))
            if 37 <= d <= 41:  # moat
                for y in range(2, G + 1):
                    bp.set(x, y, z, M("water[level=0]"))
                bp.set(x, 1, z, M("deepslate_bricks"))
            if d == 42:  # lip of the bank
                bp.set(x, G, z, M("coarse_dirt"))
    # moat wall facing the platform
    for x in range(C - 36, C + 37):
        for z in range(C - 36, C + 37):
            if dm(x, z) == 36:
                for y in range(2, PY + 1):
                    bp.set(x, y, z, BRICK(x, y, z))


def wall_ring():
    for y in range(W, WALL_TOP + 1):
        for t in range(3):
            rect_ring(bp, C - 34 + t, C - 34 + t, C + 34 - t, C + 34 - t, y, BRICK)
    # inner rim and crenellation on the outer face
    for x in range(C - 34, C + 35):
        for z in (C - 34, C + 34):
            if (x + z) % 2 == 0:
                put(bp, x, WALL_TOP + 1, z, M("deepslate_brick_wall"))
    for z in range(C - 34, C + 35):
        for x in (C - 34, C + 34):
            if (x + z) % 2 == 0:
                put(bp, x, WALL_TOP + 1, z, M("deepslate_brick_wall"))
    # base course
    rect_ring(bp, C - 35, C - 35, C + 35, C + 35, W, M("polished_blackstone_bricks"))


def towers():
    spots = [(C - 33, C - 33, 5, 32), (C + 33, C - 33, 5, 32), (C - 33, C + 33, 5, 32), (C + 33, C + 33, 5, 32),
             (C - 33, C, 4, 27), (C + 33, C, 4, 27), (C, C - 33, 5, 30),
             (C - 9, C + 33, 5, 30), (C + 9, C + 33, 5, 30)]
    for cx, cz, r, top in spots:
        round_tower(bp, cx, cz, r, W, top, BRICK, glass=PANE, glass_every=7, glass_from=7)
        for fy in (W + 9, W + 18) if top > 25 else (W + 9,):
            floor_disc(bp, cx, cz, r - 1, fy, TILE(cx, fy, cz))
        floor_disc(bp, cx, cz, r, top + 1, M("polished_blackstone_bricks"))
        crenellate_ring(bp, cx, cz, r + 1, top + 2, M("polished_blackstone_brick_wall"))
        cone(bp, cx, cz, top + 2, r + 1.5, 10 + r, TILE, finial=[M("iron_bars"), M("iron_bars"), M("lightning_rod[facing=up]")])
    # doorways from wall walk into corner towers (inner side)
    for cx, cz in ((C - 33, C - 33), (C + 33, C - 33), (C - 33, C + 33), (C + 33, C + 33)):
        sx = 1 if cx < C else -1
        sz = 1 if cz < C else -1
        for dy in (1, 2):
            put(bp, cx + sx * 5, WALL_TOP + dy, cz, AIR)  # opening towards the wall walk along the side


def gatehouse():
    # opening through the 3-thick wall (z 86..88): x 51..57, y 8..16, pointed top
    for z in range(C + 32, C + 35):
        for x in range(C - 3, C + 4):
            for y in range(W, 17):
                if y == 16 and abs(x - C) == 3:
                    continue
                bp.set(x, y, z, AIR)
        for x in (C - 4, C + 4):
            for y in range(W, 17):
                bp.set(x, y, z, M("polished_blackstone_bricks"))
        for x in (C - 3, C + 3):
            bp.set(x, 16, z, stair("polished_blackstone_brick", "east" if x < C else "west", "top"))
    # raised portcullis in the middle of the passage, dark floor, lamps
    for x in range(C - 3, C + 4):
        for y in (14, 15, 16):
            if not (y == 16 and abs(x - C) == 3):
                bp.set(x, y, C + 33, M("iron_bars"))
    for x in range(C - 3, C + 4):
        for z in range(C + 32, C + 35):
            bp.set(x, PY, z, M("polished_blackstone_bricks"))
    for z in (C + 32, C + 34):
        for x in (C - 3, C + 3):
            bp.set(x, 15, z, SOUL_H)
    # banner-less standards: black walls with purple glass slit over the arch
    for dx in range(-2, 3):
        put(bp, C + dx, 19, C + 35, M("deepslate_brick_stairs[facing=south,half=bottom]"))
    # approach: bridge and ramp
    for z in range(C + 36, C + 44):
        for x in range(C - 3, C + 4):
            bp.set(x, PY, z, M("polished_blackstone_bricks"))
            for y in range(2, PY):
                if x in (C - 3, C + 3) and z in (C + 38, C + 41):
                    bp.set(x, y, z, M("deepslate_bricks"))
        for x in (C - 3, C + 3):
            bp.set(x, W, z, M("polished_blackstone_brick_wall"))
    for z in (C + 36, C + 43):
        for x in (C - 3, C + 3):
            for k in range(1, 4):
                put(bp, x, W + k, z, M("polished_blackstone_brick_wall"))
            put(bp, x, W + 4, z, SOUL)
    for x in range(C - 3, C + 4):
        bp.set(x, 6, C + 44, stair("polished_blackstone_brick", "north"))
        bp.set(x, 5, C + 45, stair("polished_blackstone_brick", "north"))
    for x in range(C - 3, C + 4):
        bp.set(x, G, C + 44, M("polished_blackstone_bricks"))
        bp.set(x, PY, C + 40, M("sea_lantern") if abs(x - C) == 2 else M("polished_blackstone_bricks"))
    # approach road to the south edge (gravel and cobbled deepslate)
    for z in range(C + 46, SZ):
        for x in range(C - 2, C + 3):
            bp.set(x, G, z, M("gravel") if rnd(x, 0, z, 3) < 0.6 else M("cobbled_deepslate"))
        if z % 9 == 0:
            for x in (C - 4, C + 4):
                for k in range(1, 4):
                    put(bp, x, G + k, z, M("deepslate_brick_wall"))
                put(bp, x, G + 4, z, SOUL)


def wall_stairs():
    for sx, x0 in ((1, C - 31), (-1, C + 31)):
        for i in range(10):
            z = C + 25 - i
            facing = "north"
            for dx in (0, 1):
                x = x0 + sx * dx
                for y in range(W, W + i):
                    bp.set(x, y, z, M("deepslate_bricks"))
                bp.set(x, W + i, z, stair("deepslate_brick", facing))
        # landing at wall-walk height next to the stair top
        for dx in (0, 1):
            x = x0 + sx * dx
            for y in range(W, WALL_TOP + 1):
                bp.set(x, y, C + 15, M("deepslate_bricks"))
            bp.set(x, WALL_TOP, C + 15, M("deepslate_bricks"))
        put(bp, x0, WALL_TOP + 1, C + 15, SOUL)


def courtyard():
    # path from gate to the great door
    for z in range(C + 5, C + 32):
        for x in range(C - 3, C + 4):
            bp.set(x, PY, z, M("polished_blackstone_bricks") if abs(x - C) < 3 else M("chiseled_deepslate") if z % 4 == 0 and abs(x - C) == 3 else M("polished_deepslate"))
    # lamp posts
    for z in range(C + 8, C + 32, 7):
        for x in (C - 5, C + 5):
            for k in range(1, 4):
                bp.set(x, PY + k, z, M("deepslate_brick_wall"))
            bp.set(x, PY + 4, z, SOUL)
    # puppet stands: skulls on posts, rows either side of the path
    n = 0
    for z in (C + 12, C + 18, C + 24):
        for dx in (-9, -14, 9, 14):
            x = C + dx
            bp.set(x, W, z, M("deepslate_brick_wall"))
            bp.set(x, W + 1, z, M("deepslate_brick_wall"))
            bp.set(x, W + 2, z, M(f"wither_skeleton_skull[rotation={(n * 3) % 16}]"))
            n += 1
    # gallows frames hung with chains (marionette controllers)
    for fx in (C - 24, C + 18):
        z = C + 18
        for x in (fx, fx + 6):
            for y in range(W, W + 10):
                bp.set(x, y, z, M("dark_oak_log[axis=y]"))
        for x in range(fx, fx + 7):
            bp.set(x, W + 10, z, M("dark_oak_log[axis=x]"))
        for x in (fx + 1, fx + 3, fx + 5):
            for y in range(W + 5, W + 10):
                bp.set(x, y, z, M("chain[axis=y]"))
            bp.set(x, W + 4, z, SOUL_H)
        bp.set(fx + 3, W + 11, z, M("deepslate_brick_wall"))
    # gargoyle-like blackstone braziers at the keep steps
    for x in (C - 9, C + 9):
        bp.set(x, W, C + 29, M("polished_blackstone_bricks"))
        bp.set(x, W + 1, C + 29, M("soul_campfire[facing=south,lit=true]"))


KX0, KX1, KZ0, KZ1 = C - 14, C + 14, C - 20, C + 8   # keep footprint (40..68, 34..62)
KTOP = 32
ROOF = 30


def keep():
    for y in range(W, KTOP + 1):
        for t in range(2):
            rect_ring(bp, KX0 + t, KZ0 + t, KX1 - t, KZ1 - t, y, BRICK)
    clear(bp, KX0 + 2, W, KZ0 + 2, KX1 - 2, ROOF - 1, KZ1 - 2)
    # roof deck and crenellation
    fill(bp, KX0 + 2, ROOF, KZ0 + 2, KX1 - 2, ROOF, KZ1 - 2, M("polished_blackstone_bricks"))
    for x in range(KX0, KX1 + 1):
        for z in (KZ0, KZ1):
            if (x + z) % 2 == 0:
                put(bp, x, KTOP + 1, z, M("deepslate_brick_wall"))
    for z in range(KZ0, KZ1 + 1):
        for x in (KX0, KX1):
            if (x + z) % 2 == 0:
                put(bp, x, KTOP + 1, z, M("deepslate_brick_wall"))
    # interior floor
    fill(bp, KX0 + 2, PY, KZ0 + 2, KX1 - 2, PY, KZ1 - 2, M("polished_blackstone"))
    # corner turrets with spires
    for cx, cz in ((KX0, KZ0), (KX1, KZ0), (KX0, KZ1), (KX1, KZ1)):
        round_tower(bp, cx, cz, 4, W, KTOP + 8, BRICK, glass=PANE, glass_every=8, glass_from=12)
        floor_disc(bp, cx, cz, 4, KTOP + 9, M("polished_blackstone_bricks"))
        cone(bp, cx, cz, KTOP + 9, 5.5, 12, TILE, finial=[M("iron_bars"), M("lightning_rod[facing=up]")])
    # great central spire (a tower of its own on the roof)
    cx, cz = C, C - 8
    for y in range(ROOF + 1, ROOF + 17):  # solid: the roof is not reachable from inside
        for x, z in disc_cells(cx, cz, 6):
            put(bp, x, y, z, BRICK(x, y, z))
    for y in (ROOF + 5, ROOF + 6, ROOF + 11, ROOF + 12):
        for dx, dz in ((6, 0), (-6, 0), (0, 6), (0, -6)):
            put(bp, cx + dx, y, cz + dz, PANE)
    cone(bp, cx, cz, ROOF + 17, 7.5, 24, TILE, finial=[M("iron_bars"), M("iron_bars"), M("amethyst_block"), M("lightning_rod[facing=up]")])
    # buttresses and gothic windows on the south facade and sides
    for x in range(KX0 + 4, KX1 - 3, 6):
        for y in range(W, KTOP - 3):
            put(bp, x, y, KZ0 - 1, M("deepslate_bricks"))
            if abs(x - C) > 5:
                put(bp, x, y, KZ1 + 1, M("deepslate_bricks"))
        put(bp, x, KTOP - 3, KZ0 - 1, stair("deepslate_brick", "south"))
        if abs(x - C) > 5:
            put(bp, x, KTOP - 3, KZ1 + 1, stair("deepslate_brick", "north"))
    for z in range(KZ0 + 4, KZ1 - 3, 6):
        for y in range(W, KTOP - 3):
            put(bp, KX0 - 1, y, z, M("deepslate_bricks"))
            put(bp, KX1 + 1, y, z, M("deepslate_bricks"))
        put(bp, KX0 - 1, KTOP - 3, z, stair("deepslate_brick", "east"))
        put(bp, KX1 + 1, KTOP - 3, z, stair("deepslate_brick", "west"))
    # windows (1 wide pointed slots of purple glass) between buttresses: throne hall walls and gallery
    def slot(x, z, face, y0, h):
        for y in range(y0, y0 + h):
            for t in (0, 1):
                dx, dz = {"north": (0, t), "south": (0, -t), "west": (t, 0), "east": (-t, 0)}[face]
                put(bp, x + dx, y, z + dz, PANE)
        put(bp, x, y0 + h, z, M("chiseled_deepslate"))

    for x in range(KX0 + 7, KX1 - 5, 6):
        slot(x, KZ0, "north", W + 6, 13)
        if abs(x - C) > 5:
            slot(x, KZ1 - 1, "south", W + 14, 8)
    for z in range(KZ0 + 7, KZ1 - 5, 6):
        slot(KX0, z, "west", W + 6, 13) if z < KZ0 + 14 else slot(KX0, z, "west", W + 14, 8)
        slot(KX1 - 1, z, "east", W + 6, 13) if z < KZ0 + 14 else slot(KX1 - 1, z, "east", W + 14, 8)
    # great door on the south facade (x 51..57), pointed arch, raised portcullis
    for x in range(C - 3, C + 4):
        for y in range(W, W + 10):
            if y >= W + 8 and abs(x - C) >= 2 and y > W + 8 + (1 if abs(x - C) == 2 else 0):
                continue
            for z in (KZ1 - 1, KZ1):
                put(bp, x, y, z, AIR)
    for x in range(C - 3, C + 4):
        put(bp, x, W + 8, KZ1, M("iron_bars"))
        put(bp, x, W + 9, KZ1, M("iron_bars") if abs(x - C) <= 1 else BRICK(x, W + 9, KZ1))
    for x in (C - 4, C + 4):
        for y in range(W, W + 10):
            put(bp, x, y, KZ1, M("polished_blackstone_bricks"))
            put(bp, x, y, KZ1 - 1, M("polished_blackstone_bricks"))
    for y in range(W, W + 10):
        put(bp, C - 4, y, KZ1 + 1, M("chiseled_polished_blackstone"))
        put(bp, C + 4, y, KZ1 + 1, M("chiseled_polished_blackstone"))
    for x in range(C - 3, C + 4):
        put(bp, x, W + 10, KZ1 + 1, M("polished_blackstone_bricks"))
    # the pierrot mask over the great door, Clayman's sign on the keep
    pixel_art(bp, C - 4, KTOP - 1, KZ1 + 1, MASK, MASK_PAL, flip=False)
    # steps in front of the great door
    for x in range(C - 5, C + 6):
        put(bp, x, PY + 0, KZ1 + 1, M("polished_blackstone_bricks"))
    for x in (C - 4, C + 4):
        for k in range(1, 4):
            put(bp, x, W + k + 8, KZ1 + 1, AIR)


MASK = [
    "....K....",
    "...KKK...",
    "..KKKKK..",
    ".KKKKKKK.",
    "KKKKKKKKK",
    "WWWWWWWWW",
    "WKKWWWKKW",
    "WKPKWKPKW",
    "WWKWWWKWW",
    "WWWWRWWWW",
    "WWWWWWWWW",
    "WRWWWWWRW",
    "WWRRRRRWW",
    ".WWWWWWW.",
]
MASK_PAL = {"K": M("black_concrete"), "W": M("white_concrete"), "R": M("red_concrete"), "P": M("purple_concrete")}


def interior():
    # partition between the entrance hall and the throne hall with a great pointed arch (z 47..48)
    for z in (47, 48):
        fill(bp, KX0 + 2, W, z, KX1 - 2, ROOF - 1, z, M("deepslate_bricks"))
        for x in range(C - 4, C + 5):
            for y in range(W, W + 9):
                if y == W + 8 and abs(x - C) > 2:
                    continue
                if y == W + 7 and abs(x - C) == 4:
                    continue
                put(bp, x, y, z, AIR)
        # upper opening (gallery balcony onto the throne hall)
        for x in range(C - 8, C + 9):
            for y in range(20, 29):
                if y == 28 and abs(x - C) > 5:
                    continue
                put(bp, x, y, z, AIR)
    for x in range(C - 8, C + 9):
        put(bp, x, 20, 47, M("iron_bars"))
    # gallery floor over the entrance hall (y 19) except the stair hole on the west side
    for x in range(KX0 + 2, KX1 - 1):
        for z in range(49, KZ1 - 1):
            if x in (KX0 + 2, KX0 + 3) and z >= 50:
                continue
            put(bp, x, 19, z, M("deepslate_tiles") if (x + z) % 3 else M("polished_deepslate"))
    # stair up the west wall of the entrance hall: 12 steps, ascending north, z 60 -> 49
    for i in range(12):
        z = KZ1 - 2 - i
        for x in (KX0 + 2, KX0 + 3):
            for y in range(PY + 1, W + i):
                put(bp, x, y, z, M("deepslate_bricks"))
            put(bp, x, W + i, z, stair("deepslate_brick", "north"))
    for z in range(50, KZ1 - 1):
        put(bp, KX0 + 4, 20, z, M("iron_bars"))
        put(bp, KX0 + 4, 21, z, AIR)
    # throne hall: carpet, pillars, dais, throne
    for z in range(37, 47):
        for x in range(C - 2, C + 3):
            put(bp, x, W, z, M("purple_carpet"))
    for x in range(C - 2, C + 3):
        for z in range(49, 61):
            put(bp, x, W, z, M("purple_carpet"))
    for z in (40, 44):
        for x in (C - 6, C + 6):
            for y in range(W, 28):
                put(bp, x, y, z, M("polished_blackstone_bricks") if y % 6 else M("chiseled_polished_blackstone"))
            put(bp, x, 28, z, M("deepslate_brick_wall"))
    # dais (z 36..39)
    for x in range(C - 6, C + 7):
        for z in range(36, 40):
            put(bp, x, W, z, M("polished_blackstone_bricks"))
    for x in range(C - 5, C + 6):
        for z in range(36, 38):
            put(bp, x, W + 1, z, M("polished_blackstone_bricks"))
    for x in range(C - 6, C + 7):
        put(bp, x, W, 40, stair("polished_blackstone_brick", "north"))
    for x in range(C - 5, C + 6):
        put(bp, x, W + 1, 38, stair("polished_blackstone_brick", "north"))
    # the throne: crying obsidian seat, tall blackstone back with a purple crest, arms
    fill(bp, C - 1, W + 2, 36, C + 1, W + 2, 37, M("polished_blackstone_bricks"))
    put(bp, C, W + 3, 37, stair("polished_blackstone_brick", "south"))
    fill(bp, C - 2, W + 2, 36, C - 2, W + 4, 37, M("polished_blackstone_bricks"))
    fill(bp, C + 2, W + 2, 36, C + 2, W + 4, 37, M("polished_blackstone_bricks"))
    fill(bp, C - 1, W + 3, 36, C + 1, W + 9, 36, M("polished_blackstone_bricks"))
    for y in range(W + 4, W + 10):
        put(bp, C, y, 36, M("crying_obsidian"))
    put(bp, C, W + 10, 36, M("amethyst_block"))
    put(bp, C - 1, W + 10, 36, stair("polished_blackstone_brick", "east"))
    put(bp, C + 1, W + 10, 36, stair("polished_blackstone_brick", "west"))
    for x in (C - 3, C + 3):
        put(bp, x, W + 2, 37, SOUL)
        put(bp, x, W + 2, 36, M("polished_blackstone_bricks"))
    # the pierrot mask on the north wall above the throne (interior face z 36), mirrored for the viewer facing north
    pixel_art(bp, C - 4, 27, 36, MASK, MASK_PAL, flip=False)
    # marionette controllers: chains from the vault to an iron crossbar, three chains down ending in soul lanterns
    for cx, cz in ((C - 8, 42), (C + 8, 42), (C, 44)):
        for y in range(23, ROOF):
            put(bp, cx, y, cz, M("chain[axis=y]"))
        for dx in (-2, -1, 0, 1, 2):
            put(bp, cx + dx, 22, cz, M("iron_bars"))
        for dx in (-2, 0, 2):
            for y in (21, 20):
                put(bp, cx + dx, y, cz, M("chain[axis=y]"))
            put(bp, cx + dx, 19, cz, SOUL_H)
    # entrance hall: wall sconces and a small armoury of skulls on pedestals
    for x in (KX0 + 6, KX1 - 6):
        for z in (53, 57):
            put(bp, x, W, z, M("polished_blackstone_bricks"))
            put(bp, x, W + 1, z, M("wither_skeleton_skull[rotation=8]"))
            put(bp, x, W + 2, z, AIR)


def trees():
    for k in range(70):
        x = int(rnd(k, 1, 7, 21) * (SX - 6)) + 3
        z = int(rnd(k, 2, 7, 22) * (SZ - 6)) + 3
        if dm(x, z) < 45 or (abs(x - C) <= 4 and z > C):
            continue
        if bp.blocks.get((x, G + 1, z)) != AIR or bp.blocks.get((x, G, z)) in (None, M("water[level=0]")):
            continue
        h = 4 + int(rnd(k, 3, 7, 23) * 5)
        for y in range(G + 1, G + 1 + h):
            put(bp, x, y, z, M("dark_oak_log[axis=y]"))
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        for j, (dx, dz) in enumerate(dirs):
            if rnd(k, j, 9, 24) < 0.55:
                by = G + 2 + int(rnd(k, j, 10, 25) * (h - 2))
                put(bp, x + dx, by, z + dz, M("dark_oak_log[axis=%s]" % ("x" if dx else "z")))
                put(bp, x + 2 * dx, by + 1, z + 2 * dz, M("dark_oak_log[axis=y]"))
        put(bp, x + 1, G + 1, z, M("dead_bush")) if bp.blocks.get((x + 1, G + 1, z)) == AIR else None


def build(b):
    global bp
    bp = b
    fill_air(bp, 0)
    ground()
    wall_ring()
    gatehouse()
    towers()
    wall_stairs()
    courtyard()
    keep()
    interior()
    trees()
    gatehouse_after()
    def region(x, y, z):
        near = dm(x, z) <= 37 or (abs(x - C) <= 5 and C < z <= C + 50)
        return near and (y <= 34 or roofed(bp, x, y, z))
    
    n = light_pass(bp, region, G + 1, lambda x, y, z: SOUL, post=lambda x, y, z: [
        (0, M("deepslate_brick_wall")), (1, M("deepslate_brick_wall")), (2, M("deepslate_brick_wall")), (3, SOUL)],
        label="clayman_castle")
    print(f"clayman_castle: {n} extra lamps")


def gatehouse_after():
    # The projecting base course meets the bridge at z=89. Cut it flush with the deck.
    for x in range(C - 3, C + 4):
        bp.set(x, W, C + 35, AIR)
    # re-open the gate passage and keep door (towers and walls were drawn after the first cut)
    for z in range(C + 32, C + 35):
        for x in range(C - 3, C + 4):
            for y in range(W, 16):
                bp.set(x, y, z, AIR)
    for x in range(C - 3, C + 4):
        for y in (14, 15):
            bp.set(x, y, C + 33, M("iron_bars"))
    for x in range(C - 3, C + 4):
        for z in range(C + 32, C + 35):
            bp.set(x, PY, z, M("polished_blackstone_bricks"))
