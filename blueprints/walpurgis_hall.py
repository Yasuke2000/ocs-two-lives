"""The Walpurgis Hall: where the Demon Lords hold council, in its own dimension (ttl:walpurgis), with the Banquet Floor
for organised combat beside it.

SIZE (123, 44, 97). Built in a void dimension at ground = "fixed" (like the Dwelling of the Spirits): a floating island of
blackstone and deepslate under a fixed midnight sky; the top layer is y 14, you walk at y 15. Arrival and anchor point:
blueprint (40, 15, 79) on the south plaza, facing north; the return arch (PORTAL, anchor-relative, exported to
generated/walpurgis_hall.js) stands just south of it.

North of the plaza, the council chamber: a round hall (wall radius 18, centre 40 36) under a stepped dome with an oculus of
purple glass, doors to the south and east. Inside, ten thrones at radius 10.5 face a round table (radius 6.5-8.5) set
round a ten-pointed star inlaid in the floor and a beacon whose beam rises through the oculus: ten seats for the Ten Great
Demon Lords (the pack's ten Legendary places; canon's council is ten Demon Lords until the Octagram makes it eight), each
with its own coloured crest; ten pillars with soul lanterns between the seats.
East of the chamber, the Banquet Floor (centre 92 40): a round pit of polished blackstone (floor radius 17, you fight at
y 12) inside three terrace steps where onlookers stand (radius 17.5-22), a balustrade at radius 23 open to the west path,
and eight braziers on pillars round the rim. The pit is the arena box of design/data/arenas.toml (round, radius 17).
An invisible barrier runs round the island's rim so nobody walks off into the void; the biome has no spawners and the
floors are lit (soul lanterns, shroomlight in the floors).

Nothing here comes from a mod; Walpurgis has no venue in any mod. Canon and our interpretation: design/lore/arenas.md.
"""
import json
import math

from _dwargon_lib import AIR, fbm2, noise2, rnd
from _sites_lib import M, put

SIZE = (123, 44, 97)
SX, SY, SZ = SIZE
G = 14          # top layer of the island
F = G + 1       # walking level
CH = (40, 36)   # council chamber centre
WALL_R = 18
AR = (92, 40)   # Banquet Floor centre
PIT_R = 17
PIT = G - 3     # pit floor top layer (fight at PIT + 1 = 12)
ANCHOR = (40, F, 79)
# Return arch: open floor cells x 37..43, z 85..86, walking height y 15..20.
PORTAL = (-3, 0, 6, 3, 5, 7)
PARTS = [0, 48]

BLACK = [(M("polished_blackstone_bricks"), 55), (M("cracked_polished_blackstone_bricks"), 12),
         (M("deepslate_bricks"), 23), (M("deepslate_tiles"), 10)]
UNDER = [(M("blackstone"), 40), (M("deepslate"), 30), (M("basalt[axis=y]"), 10), (M("tuff"), 12),
         (M("crying_obsidian"), 2), (M("obsidian"), 6)]
SOUL_H = M("soul_lantern[hanging=true]")
SOUL = M("soul_lantern[hanging=false]")
# Ten crests, one per seat (our interpretation: no canon colours per Demon Lord are used).
CRESTS = ["red", "pink", "light_blue", "white", "yellow", "orange", "lime", "purple", "cyan", "gray"]


def pick(palette, r):
    total = sum(w for _, w in palette)
    t = r * total
    for state, w in palette:
        t -= w
        if t < 0:
            return state
    return palette[-1][0]


def brick(x, y, z):
    return pick(BLACK, rnd(x, y, z, 3))


def d_ch(x, z):
    return math.hypot(x - CH[0], z - CH[1])


def d_ar(x, z):
    return math.hypot(x - AR[0], z - AR[1])


def edge(x, z) -> float:
    """How far inside the island (x, z) is (negative = outside): a union of discs and bands with a wobbling rim."""
    w = (fbm2(x, z, 14, 5) - 0.5) * 3
    parts = [
        24 - d_ch(x, z),                       # chamber
        28 - d_ar(x, z),                       # Banquet Floor
        13 - math.hypot(x - 40, z - 80),       # plaza
    ]
    if 33 <= x <= 47:                          # chamber - plaza
        parts.append(min(x - 33, 47 - x, 6) if 52 <= z <= 72 else -99)
    if 30 <= z <= 44:                          # chamber - Banquet Floor
        parts.append(min(z - 30, 44 - z, 6) if 54 <= x <= 72 else -99)
    if 84 <= z <= 89 and 32 <= x <= 48:        # the arch's footing
        parts.append(3)
    return max(parts) + w


def stair(name, facing, half="bottom"):
    return M(f"{name}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]")


def outward(dx, dz) -> str:
    """The cardinal direction away from the centre for a seat at offset (dx, dz) (a stair's back faces it)."""
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def build(bp):
    blocks = bp.blocks
    for x in range(SX):
        for z in range(SZ):
            for y in range(F, SY):
                blocks[(x, y, z)] = AIR

    # --- the island ----------------------------------------------------------------------------------------------
    cols = {}
    for x in range(SX):
        for z in range(SZ):
            e = edge(x, z)
            if e < 0:
                continue
            t = max(2, min(G, int(3 + e * 0.9 + (noise2(x, z, 5, 8) - 0.5) * 4)))
            cols[(x, z)] = e
            for y in range(G - t, G + 1):
                blocks[(x, y, z)] = pick(UNDER, rnd(x, y, z, 6))
            blocks[(x, G, z)] = M("polished_blackstone") if rnd(x, 0, z, 7) < 0.6 else M("deepslate_tiles")
            if e < 1.2:
                blocks[(x, G, z)] = M("blackstone")

    # --- the plaza and paths --------------------------------------------------------------------------------------
    for (x, z) in cols:
        if math.hypot(x - 40, z - 80) <= 10 or (37 <= x <= 43 and 54 <= z <= 80) or (57 <= x <= 72 and 34 <= z <= 38):
            blocks[(x, G, z)] = M("polished_deepslate") if (x + z) % 2 else M("deepslate_tiles")
    for z in range(56, 79, 6):
        for x in (36, 44):
            blocks[(x, F, z)] = M("polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            blocks[(x, F + 1, z)] = M("polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            blocks[(x, F + 2, z)] = SOUL
    for x in range(60, 70, 5):
        for z in (32, 40):
            blocks[(x, F, z)] = M("polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            blocks[(x, F + 1, z)] = SOUL

    chamber(blocks)
    banquet_floor(blocks)
    arch(blocks)

    # --- the invisible rim ---------------------------------------------------------------------------------------
    for (x, z), e in cols.items():
        outer = any((x + dx, z + dz) not in cols for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if outer:
            for y in range(F, F + 16):
                if blocks.get((x, y, z)) in (None, AIR):
                    blocks[(x, y, z)] = M("barrier")
    return None


def chamber(blocks):
    cx, cz = CH
    top = F + 10
    # floor: dark tiles, a red carpet ring under the thrones, the ten-pointed star round the beacon
    for x in range(cx - WALL_R, cx + WALL_R + 1):
        for z in range(cz - WALL_R, cz + WALL_R + 1):
            d = d_ch(x, z)
            if d > WALL_R + 1.2:
                continue
            if d <= WALL_R + 0.5:
                blocks[(x, G, z)] = M("polished_blackstone") if (x + z) % 2 else M("polished_deepslate")
            if 9.2 <= d <= 12.0:
                blocks[(x, F, z)] = M("red_carpet")
            if d <= 5.5:
                a = math.atan2(z - cz, x - cx)
                ray = abs(((a / (2 * math.pi) * 10) % 1) - 0.5) * 2   # 1 on a ray, 0 between two
                blocks[(x, G, z)] = M("crying_obsidian") if ray > 1 - d / 5.5 * 0.85 else M("obsidian")
            # walls with slit windows, two doors (south, east)
            if WALL_R - 0.5 <= d <= WALL_R + 1.2:
                ang = math.degrees(math.atan2(x - cx, -(z - cz))) % 360   # 0 = north, clockwise
                door = (abs(x - cx) <= 2 and z > cz) or (abs(z - cz) <= 2 and x > cx)
                for y in range(F, top + 1):
                    if door and y <= F + 5:
                        blocks[(x, y, z)] = AIR
                        continue
                    window = int(ang) % 36 in (17, 18, 19) and F + 4 <= y <= F + 8
                    blocks[(x, y, z)] = M("purple_stained_glass") if window else brick(x, y, z)
    # lantern posts beside both doors
    post = M("polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    for x, z in ((cx - 4, cz + WALL_R + 2), (cx + 4, cz + WALL_R + 2), (cx + WALL_R + 2, cz - 4), (cx + WALL_R + 2, cz + 4)):
        blocks[(x, F, z)] = post
        blocks[(x, F + 1, z)] = post
        blocks[(x, F + 2, z)] = SOUL
    # stepped dome with an oculus of purple glass
    r = WALL_R + 0.8
    y = top + 1
    while r > 2.5 and y < SY - 1:
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for z in range(int(cz - r) - 1, int(cz + r) + 2):
                d = d_ch(x, z)
                if r - 1.6 <= d <= r:
                    blocks[(x, y, z)] = brick(x, y, z) if rnd(x, y, z, 9) < 0.9 else M("deepslate_tiles")
        r -= 1.6
        y += 1
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            if d_ch(x, z) <= r + 0.5:
                blocks[(x, y - 1, z)] = M("purple_stained_glass")
    # the beacon under the oculus (its beam rises through the purple glass)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            blocks[(x, G - 1, z)] = M("iron_block")
    blocks[(cx, G, cz)] = M("beacon")
    # the round table
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            if 6.5 <= d_ch(x, z) <= 8.5:
                blocks[(x, F, z)] = M("polished_deepslate")
    # ten thrones facing the table, a crest above each; ten pillars between them
    for i in range(10):
        a = math.radians(18 + 36 * i)
        dx, dz = math.sin(a), -math.cos(a)
        sx, sz = round(cx + 10.5 * dx), round(cz + 10.5 * dz)
        face = outward(sx - cx, sz - cz)
        bx, bz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[face]
        blocks[(sx, F, sz)] = stair("polished_blackstone_brick", face)
        for y in range(F, F + 3):
            blocks[(sx + bx, y, sz + bz)] = M("polished_blackstone_bricks")
        blocks[(sx + bx, F + 3, sz + bz)] = M(f"{CRESTS[i]}_glazed_terracotta")
        blocks[(sx + bx, F + 4, sz + bz)] = M("polished_blackstone_brick_slab[type=bottom,waterlogged=false]")
        pa = math.radians(36 * i)
        px, pz = round(cx + 14 * math.sin(pa)), round(cz - 14 * math.cos(pa))
        for y in range(F, F + 10):
            blocks[(px, y, pz)] = M("chiseled_polished_blackstone") if y % 4 == 0 else M("polished_blackstone_bricks")
        blocks[(px, F + 10, pz)] = M("polished_blackstone_bricks")
        for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if d_ch(px + ddx, pz + ddz) < 14 and blocks.get((px + ddx, F, pz + ddz)) in (None, AIR, M("red_carpet")):
                blocks[(px + ddx, F, pz + ddz)] = SOUL
                break
    # lanterns hung over the table on chains from the dome
    for i in range(5):
        a = math.radians(72 * i)
        x, z = round(cx + 4 * math.sin(a)), round(cz - 4 * math.cos(a))
        yy = F + 7
        while yy < SY - 1 and blocks.get((x, yy, z)) == AIR:
            yy += 1
        for y in range(F + 7, yy):
            blocks[(x, y, z)] = M("chain[axis=y]")
        blocks[(x, F + 6, z)] = SOUL_H


def banquet_floor(blocks):
    cx, cz = AR
    for x in range(cx - 26, cx + 27):
        for z in range(cz - 26, cz + 27):
            if not (0 <= x < SX and 0 <= z < SZ):
                continue
            d = d_ar(x, z)
            if d <= 22.2:
                level = PIT if d <= PIT_R + 0.5 else PIT + 1 if d <= 19.0 else PIT + 2 if d <= 20.5 else G
                for y in range(level + 1, F):
                    blocks[(x, y, z)] = AIR
                if d <= PIT_R + 0.5:
                    ring = abs(d - 12) < 0.6 or abs(d - 6) < 0.6
                    blocks[(x, level, z)] = M("red_nether_bricks") if ring else (
                        M("polished_blackstone") if (x + z) % 2 else M("polished_deepslate"))
                    if (abs(d - 9) < 0.5 or abs(d - 15) < 0.5) and (x * 7 + z * 3) % 9 == 0:
                        blocks[(x, level, z)] = M("shroomlight")
                else:
                    blocks[(x, level, z)] = M("polished_blackstone_bricks")
                if d <= 1.0:
                    blocks[(x, level, z)] = M("crying_obsidian")
            # balustrade at radius 23, open to the west path
            if 22.5 <= d <= 23.5 and not (x < cx and abs(z - 36) <= 4):
                blocks[(x, F, z)] = M("polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    # eight brazier pillars round the rim
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        x, z = round(cx + 25 * math.cos(a)), round(cz + 25 * math.sin(a))
        if not (0 <= x < SX and 0 <= z < SZ):
            continue
        for y in range(F, F + 5):
            blocks[(x, y, z)] = M("polished_blackstone_bricks") if y < F + 4 else M("chiseled_polished_blackstone")
        blocks[(x, F + 5, z)] = M("soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def arch(blocks):
    ax, ay, az = ANCHOR
    z0, z1 = az + 5, az + 9
    for x0 in (ax - 6, ax + 4):
        for x in range(x0, x0 + 3):
            for z in range(z0, z1 + 1):
                for y in range(F, F + 9):
                    blocks[(x, y, z)] = brick(x, y, z)
    for x in range(ax - 7, ax + 8):
        for z in range(z0, z1 + 1):
            blocks[(x, F + 9, z)] = M("polished_blackstone_bricks")
            blocks[(x, F + 10, z)] = M("deepslate_tiles")
    for x in range(ax - 3, ax + 4):
        for z in range(z0, z1 + 1):
            for y in range(F, F + 9):
                blocks[(x, y, z)] = AIR
            blocks[(x, G, z)] = M("crying_obsidian") if x == ax else M("polished_deepslate")
    for x in (ax - 3, ax + 3):
        blocks[(x, F + 7, z1 - 1)] = SOUL_H
    blocks[(ax, F + 11, az + 7)] = M("purple_stained_glass")
    blocks[(ax, F + 12, az + 7)] = SOUL


def outputs(bp):
    geo = {"size": list(SIZE), "anchor": list(ANCHOR), "portal": list(PORTAL), "arrival_yaw": 180}
    return {"pack/kubejs/server_scripts/ttl/generated/walpurgis_hall.js":
            "// priority: 200\n// GENERATED by tools/build_structures.py from blueprints/walpurgis_hall.py. Do not edit.\n"
            "// The hall's return arch: PORTAL is an anchor-relative box [dx0, dy0, dz0, dx1, dy1, dz1] (inclusive,\n"
            "// block coordinates of the feet). The anchor is the arrival point of the Walpurgis dimension.\n"
            f"const TtlWalpurgisHall = {json.dumps(geo, separators=(',', ':'))}\n"}
