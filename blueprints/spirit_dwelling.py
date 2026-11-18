"""The Dwelling of the Spirits (Home of the Elementals): a floating glade of the spirit domain (ttl:spirit_domain).

SIZE (89, 64, 89). Built in a void dimension at ground = "fixed": the glade's top layer is y 40 (grass), you walk at y 41,
the island hangs below it (about 29 blocks of rock, roots and amethyst), everything above is air. An invisible barrier
runs round the island's rim so nobody walks off into the void. Arrival and anchor point: blueprint (44, 41, 66), on the
south side of the glade, facing north. The return gate is an arch to the south (PORTAL, anchor-relative, exported to
generated/spirit_dwelling.js); the Dwelling itself is in the middle.

Glade: white-blossom (cherry) trees and birches, meadow flowers, two ponds, five elemental plinths round the rim (fire,
water, wind, earth, space). In the middle a round dais of Tensura labyrinth stone ringed by a broken colonnade, with a
glass lid over a shaft; a stair on the south side goes down into the grotto, the "cavern like Veldora's cave": a dome
with a summoning circle inlaid in the floor and, at its centre, a pedestal (a beacon on an iron base) whose light rises
through the shaft and the lid to the sky: where Rimuru stood the children on a pedestal bathed in light to call the
spirits. Every spawnable spot in the grotto and stair has block light (checked when this builds); the glade is daylit
(dimension fixed_time) and the biome has no spawners.

Nothing here is a Tensura warp pad or labyrinth portal; the way in and out is life/spirit_domain.js. Canon sources and what
is our interpretation: design/lore/spirit_domain.md.
"""
import json
import math

from _dwargon_lib import AIR, fbm2, noise2, rnd
from _sites_lib import M, air_above, light_up, line, pick, put, ring_points, tree

SIZE = (89, 64, 89)
SX, SY, SZ = SIZE
G = 40
F = 41
CX = CZ = 44
ANCHOR = (44, F, 66)
# Return gate: the arch's open floor cells x 41..47, z 72..73, walking height y 41..46.
PORTAL = (-3, 0, 6, 3, 5, 7)
PARTS = [0, 30, 60]

LAB = "tensura:labyrinth_bricks"
LAB_STONE = "tensura:labyrinth_stone"
CREAM = "tensura:cream_labyrinth_bricks"
LANTERN = M("sea_lantern")
WALL = "minecraft:mossy_stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"

ELEMENTS = {
    "fire": (M("red_nether_bricks"), M("orange_stained_glass"), M("shroomlight")),
    "water": (M("prismarine_bricks"), M("light_blue_stained_glass"), M("sea_lantern")),
    "wind": (M("quartz_pillar[axis=y]"), M("lime_stained_glass"), M("verdant_froglight")),
    "earth": (M("smooth_sandstone"), M("yellow_stained_glass"), M("glowstone")),
    "space": (M("purpur_pillar[axis=y]"), M("purple_stained_glass"), M("amethyst_block")),
}
ORDER = ("fire", "water", "wind", "earth", "space")

UNDER = [(M("stone"), 30), (M("tuff"), 22), (M("andesite"), 10), (M("deepslate"), 8), (M("calcite"), 6),
         (M("amethyst_block"), 5), ("tensura:magic_ore", 3), (M("moss_block"), 4), (M("smooth_basalt"), 6)]
FLOWERS = ("lily_of_the_valley", "azure_bluet", "oxeye_daisy", "allium", "cornflower", "white_tulip", "dandelion")


def rim(x, z) -> float:
    """Island radius at the direction of (x, z) (a wobbling circle)."""
    return 36.5 + (fbm2(x, z, 18, 3) - 0.5) * 7


def plinth(bp, name, px, pz, y, tall=2):
    base, glass, glow = ELEMENTS[name]
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            put(bp, px + dx, y, pz + dz, LAB)
    for k in range(1, tall + 1):
        put(bp, px, y + k, pz, base)
    put(bp, px, y + tall + 1, pz, M("chiseled_stone_bricks"))
    put(bp, px, y + tall + 2, pz, glow)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(bp, px + dx, y + tall + 2, pz + dz, glass)


def build(bp):
    blocks = bp.blocks
    air_above(bp, G)

    # --- the island: rock below a grass layer, rounded and tapering to the underside -----------------------------
    cols = {}
    for x in range(SX):
        for z in range(SZ):
            r = math.hypot(x - CX, z - CZ)
            rn = rim(x, z)
            if r > rn:
                continue
            u = r / rn
            t = int(29 * (1 - u ** 1.7) + (noise2(x, z, 6, 7) - 0.5) * 5 * u)
            if t < 1:
                t = 1
            cols[(x, z)] = (r, rn, G - t)
            blocks[(x, G, z)] = M("grass_block[snowy=false]")
            for y in range(G - t, G):
                depth = G - y
                if depth <= 2:
                    blocks[(x, y, z)] = M("dirt") if depth > 1 or rnd(x, y, z, 5) < 0.5 else M("coarse_dirt")
                else:
                    blocks[(x, y, z)] = pick(UNDER, rnd(x, y, z, 6))
    # hanging roots and a few drip crystals on the underside
    for (x, z), (r, rn, yb) in cols.items():
        rr = rnd(x, 1, z, 9)
        if rr < 0.05:
            put(bp, x, yb - 1, z, M("hanging_roots[waterlogged=false]"))
        elif rr < 0.07:
            put(bp, x, yb - 1, z, M("pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]"))

    # --- the glade --------------------------------------------------------------------------------------------------
    for (x, z), (r, rn, yb) in cols.items():
        if r > rn - 1.5:
            blocks[(x, G, z)] = M("moss_block")
            continue
        if rnd(x, 2, z, 11) < 0.35:
            blocks[(x, G, z)] = M("moss_block") if noise2(x, z, 7, 12) > 0.62 else M("grass_block[snowy=false]")
    # ponds
    for (pcx, pcz, pr) in ((22, 52, 5.0), (68, 40, 4.0)):
        for x in range(int(pcx - pr - 2), int(pcx + pr + 3)):
            for z in range(int(pcz - pr - 2), int(pcz + pr + 3)):
                d = math.hypot(x - pcx, z - pcz)
                if (x, z) in cols and d <= pr:
                    blocks[(x, G, z)] = M("water[level=0]")
                    blocks[(x, G - 1, z)] = M("water[level=0]")
                    blocks[(x, G - 2, z)] = M("clay")
                elif (x, z) in cols and d <= pr + 1.2:
                    blocks[(x, G, z)] = M("sand") if rnd(x, 3, z, 13) < 0.4 else M("clay")
        for (x, z) in ((pcx + 1, pcz), (pcx - 2, pcz + 1)):
            put(bp, x, F, z, M("lily_pad"))
    # dais of the Dwelling: labyrinth stone, amethyst ring and a quartz inlay
    for x in range(CX - 10, CX + 11):
        for z in range(CZ - 10, CZ + 11):
            d = math.hypot(x - CX, z - CZ)
            if d <= 9.5:
                blocks[(x, G, z)] = pick([(LAB_STONE, 4), (LAB, 3), (CREAM, 2), (M("stone_bricks"), 1)], rnd(x, 4, z, 21))
            if 6.3 < d <= 7.3:
                blocks[(x, G, z)] = M("amethyst_block") if (x + z) % 2 else M("oxidized_cut_copper")
            if 9.5 < d <= 10.5 and blocks.get((x, G, z)) == M("grass_block[snowy=false]"):
                blocks[(x, G, z)] = M("mossy_stone_bricks")
    # colonnade: 12 pillars at r = 15, the southern one left out (the stair), several broken
    heights = (9, 7, 9, 4, 9, 8, 3, 9, 6, 9, 9, 5)
    for i, (x, z) in enumerate(bp.around(CX, CZ, 15.0, 12, start_deg=0)):
        if i == 3:  # angle 90 degrees = south
            continue
        h = heights[i]
        for y in range(F, F + h):
            blocks[(x, y, z)] = LAB_STONE if (y - F) % 4 else CREAM
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) + abs(dz) < 2:
                    blocks[(x + dx, G, z + dz)] = LAB
        if h >= 8:
            blocks[(x, F + h, z)] = M("chiseled_stone_bricks")
            blocks[(x, F + h + 1, z)] = LANTERN
        else:
            for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                if rnd(x + dx, 0, z + dz, 22) < 0.5:
                    put(bp, x + dx, F, z + dz, M("stone_brick_slab[type=bottom,waterlogged=false]"))
        for y in range(F + 1, F + max(2, h - 2)):  # vines on the pillars
            if rnd(x, y, z, 23) < 0.25:
                put(bp, x + 1, y, z, M("vine[west=true]"))
    # architrave fragments between the standing pillars
    pil = [p for i, p in enumerate(bp.around(CX, CZ, 15.0, 12, start_deg=0)) if i != 3 and heights[i] >= 8]
    for a, b in zip(pil, pil[1:] + pil[:1]):
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 9:
            for k, (x, z) in enumerate(line(a[0], a[1], b[0], b[1])):
                if 1 < k < 8 and rnd(x, 9, z, 24) < 0.55:
                    put(bp, x, F + 8, z, M("stone_brick_slab[type=top,waterlogged=false]"))
    # the glass lid over the shaft (x 43..45) with a low rim
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            blocks[(CX + dx, G, CZ + dz)] = M("white_stained_glass")
    for x in range(CX - 2, CX + 3):
        for z in range(CZ - 2, CZ + 3):
            if max(abs(x - CX), abs(z - CZ)) == 2:
                blocks[(x, F, z)] = M("smooth_quartz_slab[type=bottom,waterlogged=false]")
    # five plinths round the rim
    for i, name in enumerate(ORDER):
        a = math.radians(-90 + 72 * i + 36)
        px, pz = round(CX + 28 * math.cos(a)), round(CZ + 28 * math.sin(a))
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if (px + dx, pz + dz) in cols and math.hypot(dx, dz) <= 3.3:
                    blocks[(px + dx, G, pz + dz)] = M("moss_block")
        plinth(bp, name, px, pz, F, tall=2)
        blocks[(px, G, pz)] = LAB_STONE

    # --- trees and flowers -----------------------------------------------------------------------------------------
    taken = set()
    for i in range(70):
        x, z = 4 + int(rnd(i, 1, 0, 31) * (SX - 8)), 4 + int(rnd(i, 2, 0, 31) * (SZ - 8))
        c = cols.get((x, z))
        d = math.hypot(x - CX, z - CZ)
        if not c or c[0] > c[1] - 5 or d < 19 or blocks.get((x, G, z)) != M("grass_block[snowy=false]"):
            continue
        if any(abs(x - a) < 6 and abs(z - b) < 6 for a, b in taken) or (36 <= x <= 52 and z >= 58):
            continue
        if blocks.get((x, F, z)) != AIR:
            continue
        taken.add((x, z))
        tree(bp, x, F, z, 6 + int(rnd(i, 3, 0, 31) * 4), leaves="cherry" if i % 4 else "birch", wide=3)
    for (x, z), (r, rn, yb) in cols.items():
        if blocks.get((x, G, z)) != M("grass_block[snowy=false]") or blocks.get((x, F, z)) != AIR:
            continue
        if math.hypot(x - CX, z - CZ) < 11.5 or (40 <= x <= 48 and z >= 53):
            continue
        rr = rnd(x, 5, z, 41)
        if rr < 0.05:
            blocks[(x, F, z)] = M(FLOWERS[int(rnd(x, 6, z, 42) * len(FLOWERS))])
        elif rr < 0.22:
            blocks[(x, F, z)] = M("short_grass") if rr < 0.17 else M("fern")

    # --- the grotto: dome, floor, summoning circle, pedestal ----------------------------------------------------------
    floor = 31
    interior = {}
    for x in range(CX - 12, CX + 13):
        for z in range(CZ - 12, CZ + 13):
            d = math.hypot(x - CX, z - CZ) / 12.0
            if d < 1:
                ceil = floor + 1 + int(6.5 * math.sqrt(1 - d * d) + (noise2(x, z, 4, 8) - 0.5) * 0.8)
                interior[(x, z)] = ceil
    for (x, z), c in interior.items():
        for y in range(floor + 1, c + 1):
            blocks[(x, y, z)] = AIR
        for y in range(c + 1, c + 2):  # a lining so the ceiling is a deliberate surface
            if blocks.get((x, y, z)) is not None and blocks[(x, y, z)] not in (AIR,):
                blocks[(x, y, z)] = pick([(M("calcite"), 4), (M("tuff"), 3), (M("amethyst_block"), 2), (M("smooth_basalt"), 2),
                                          ("tensura:magic_ore", 1)], rnd(x, y, z, 61))
        d = math.hypot(x - CX, z - CZ)
        blocks[(x, floor, z)] = pick([(M("smooth_quartz"), 4), (M("calcite"), 3), (M("quartz_bricks"), 3), (M("polished_diorite"), 1)],
                                     rnd(x, 0, z, 62))
        if 9.5 < d < 12.2:  # wall ring
            blocks[(x, floor, z)] = M("polished_andesite")
    # summoning circle: two rings and a five-pointed star, runes lit by sea lanterns
    for k in range(120):
        a = math.radians(k * 3)
        for rr, st in ((10.0, M("amethyst_block")), (7.0, M("oxidized_cut_copper")), (4.2, M("amethyst_block"))):
            x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
            if (x, z) in interior and blocks.get((x, floor + 1, z), AIR) == AIR:
                blocks[(x, floor, z)] = st
    pts = [(round(CX + 9 * math.cos(math.radians(-90 + 72 * i))), round(CZ + 9 * math.sin(math.radians(-90 + 72 * i)))) for i in range(5)]
    for i in range(5):
        a, b = pts[i], pts[(i + 2) % 5]
        for k, (x, z) in enumerate(line(a[0], a[1], b[0], b[1])):
            if blocks.get((x, floor + 1, z), AIR) == AIR and (x, z) in interior:
                blocks[(x, floor, z)] = LANTERN if k % 5 == 2 else M("oxidized_cut_copper")
    # the five elemental pillars on the star's points, short ones (the dome is low at the edge)
    for i, name in enumerate(ORDER):
        px, pz = pts[i]
        plinth(bp, name, px, pz, floor + 1, tall=1)
        blocks[(px, floor, pz)] = LAB
    # the pedestal: a beacon on an iron base, ringed by a low quartz step
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            blocks[(CX + dx, floor, CZ + dz)] = M("iron_block")
            if (dx, dz) != (0, 0):
                blocks[(CX + dx, floor + 1, CZ + dz)] = M("smooth_quartz_slab[type=bottom,waterlogged=false]")
    blocks[(CX, floor + 1, CZ)] = M("beacon")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and abs(dx) + abs(dz) < 4:
                blocks[(CX + dx, floor, CZ + dz)] = M("chiseled_quartz_block")
    # the shaft above the pedestal: 3 x 3 up to the glass lid at y 40 (the beam leaves through it)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for y in range(floor + 2, G):
                blocks[(CX + dx, y, CZ + dz)] = AIR
            for y in range(floor + 1, floor + 2):
                if (dx, dz) != (0, 0) and blocks.get((CX + dx, y, CZ + dz)) == AIR:
                    blocks[(CX + dx, y, CZ + dz)] = M("smooth_quartz_slab[type=bottom,waterlogged=false]")
    # the shaft is lined with quartz and a lantern at each corner every few blocks
    for y in range(floor + 2, G):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if max(abs(dx), abs(dz)) == 2 and blocks.get((CX + dx, y, CZ + dz)) not in (None, AIR):
                    corner = abs(dx) == 2 and abs(dz) == 2
                    blocks[(CX + dx, y, CZ + dz)] = LANTERN if corner and y % 4 == 0 else M("quartz_bricks")
    # grotto dressing: crystals and vines
    for (x, z), c in interior.items():
        if math.hypot(x - CX, z - CZ) < 4.5 or math.hypot(x - CX, z - CZ) > 11.2:
            continue
        r = rnd(x, 7, z, 71)
        if r < 0.05 and blocks.get((x, c, z)) == AIR:
            blocks[(x, c, z)] = M("pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
        elif r < 0.09 and blocks.get((x, c, z)) == AIR:
            n = 1 + int(rnd(x, 8, z, 72) * 3)
            for k in range(n):
                yy = c - k
                if blocks.get((x, yy, z)) != AIR:
                    break
                blocks[(x, yy, z)] = (M("cave_vines[age=20,berries=true]") if k == n - 1 else M("cave_vines_plant[berries=true]"))

    # --- the way down: a stair on the south side into the grotto ------------------------------------------------------
    for i in range(9):
        z = 61 - i
        y = G - i
        for x in range(42, 47):
            for yy in range(floor + 1, y):
                if blocks.get((x, yy, z)) == AIR:
                    blocks[(x, yy, z)] = LAB
            blocks[(x, y, z)] = M("stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(y + 1, (G if i <= 4 else y + 3) + 1):  # open trench down to y + 4, then a covered stair
                blocks[(x, yy, z)] = AIR
        for x in (41, 47):
            for yy in range(y, (G + 2 if i <= 4 else y + 4)):
                blocks[(x, yy, z)] = LAB if (yy + z) % 3 else CREAM
        if i > 4:
            for x in range(41, 48):
                for yy in range(y + 4, G + 1):
                    blocks[(x, yy, z)] = M("stone_bricks") if rnd(x, yy, z, 51) < 0.7 else M("mossy_stone_bricks")
    for x in (41, 47):  # gateposts at the top of the stair
        for y in range(F, F + 3):
            blocks[(x, y, 62)] = LAB_STONE
        blocks[(x, F + 3, 62)] = M("lantern[hanging=false]")

    # --- the return gate: an arch to the south ---------------------------------------------------------------------------
    gz0, gz1 = 71, 75
    for x0 in (38, 48):
        for x in range(x0, x0 + 3):
            for z in range(gz0, gz1 + 1):
                for y in range(F, F + 9):
                    blocks[(x, y, z)] = LAB if (y + z) % 5 else CREAM
    for x in range(37, 52):
        for z in range(gz0, gz1 + 1):
            blocks[(x, F + 9, z)] = LAB_STONE
            blocks[(x, F + 10, z)] = LAB
    for x in range(41, 48):
        for y in range(F, F + 9):
            for z in range(gz0, gz1 + 1):
                blocks[(x, y, z)] = AIR
        for z in range(gz0, gz1 + 1):
            blocks[(x, G, z)] = M("smooth_stone") if (x + z) % 2 else M("polished_andesite")
    for z in range(gz0, gz1 + 1):
        blocks[(44, G, z)] = M("chiseled_stone_bricks")
    for dx in range(-2, 3):
        blocks[(44 + dx, F + 11, 73)] = M("amethyst_block") if abs(dx) < 2 else LAB
    blocks[(44, F + 12, 73)] = LANTERN
    for x in (41, 47):
        blocks[(x, F + 7, gz1 - 1)] = LANTERN
    # five small element lamps over the arch
    for i, name in enumerate(ORDER):
        blocks[(40 + 2 * i + 1, F + 11, 71)] = ELEMENTS[name][2]
    # path from the arrival point to the arch and to the stair
    for z in range(62, 71):
        blocks[(44, G, z)] = M("chiseled_stone_bricks") if z % 2 else LAB_STONE
        for x in (43, 45):
            if blocks.get((x, G, z)) == M("grass_block[snowy=false]"):
                blocks[(x, G, z)] = M("coarse_dirt") if rnd(x, 0, z, 81) < 0.6 else M("mossy_stone_bricks")

    # --- the invisible rim -------------------------------------------------------------------------------------------------
    for x in range(SX):
        for z in range(SZ):
            r = math.hypot(x - CX, z - CZ)
            rn = rim(x, z)
            if rn - 0.4 < r <= rn + 1.0:
                for y in range(G, G + 20):
                    if blocks.get((x, y, z)) in (None, AIR) :
                        blocks[(x, y, z)] = M("barrier")

    # --- light (grotto and stair) ---------------------------------------------------------------------------------------
    cands = [(x, y, z) for (x, z), c in interior.items() for y in range(floor + 1, c + 1)] + \
            [(x, G - i + 1, 61 - i) for i in range(9) for x in range(42, 47)]

    def add_light(x, y, z):
        yy = y + 1
        while yy < SY and blocks.get((x, yy, z)) == AIR:
            yy += 1
        if yy - y < 10 and blocks.get((x, yy, z)) not in (None, AIR) and "glass" not in blocks[(x, yy, z)]:
            blocks[(x, yy, z)] = LANTERN
        else:
            blocks[(x, y, z)] = M("lantern[hanging=false]")

    light_up(bp, cands, add_light, spread=8)
    bp.interior = interior
    return None


def outputs(bp):
    geo = {"size": list(SIZE), "anchor": list(ANCHOR), "portal": list(PORTAL), "arrival_yaw": 180}
    return {"pack/kubejs/server_scripts/ttl/generated/spirit_dwelling.js":
            "// priority: 200\n// GENERATED by tools/build_structures.py from blueprints/spirit_dwelling.py. Do not edit.\n"
            "// The Dwelling's return gate: PORTAL is an anchor-relative box [dx0, dy0, dz0, dx1, dy1, dz1] (inclusive,\n"
            "// block coordinates of the feet). The anchor is the arrival point of the spirit domain.\n"
            f"const TtlSpiritDwelling = {json.dumps(geo, separators=(',', ':'))}\n"}
