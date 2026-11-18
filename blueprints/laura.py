"""Laura: the rebuilt capital of the Beast Kingdom of Eurazania, Carrion's jungle city.

Lore notes and sources: design/lore/laura.md. SIZE (113, 46, 113), centre column (56, 56), saved as four z slabs
laura_0..3 (PARTS). Ground layer y 4 (grass, moss, patches of coarse dirt; you walk at y 5); everything above is
air so placing clears the jungle in the box. The gate faces south (+z). Arrival point: blueprint (56, 5, 108)
outside the south gate, facing north.
Our interpretation of a place canon only says that Milim destroyed the old capital and Tempest helped build the new
one: a tropical timber-and-stone town inside a young stone wall (the lesson of the attack; Tempest blue
banners on the gate). From the south: the gate (opening x 52-60, two round towers with thatch cones, four corner
towers), a stone avenue (x 52-60) north to the fruit market plaza (centre 56, 66, radius 13: a fountain, eight
canopied stalls of melons and berries), then the Beast King's palace on a stone terrace (x 28-84, z 4-48, top
y 7): a great gabled hall of stripped jungle timber and bamboo with a thatch roof to y 32 (hall x 44-68, z 10-44,
walls to y 14), a lion's head (Carrion is a lion beastman) in the south gable, a colonnade of totem pillars, and
inside a long hall with two rows of tables, hanging lanterns and the lion throne on a dais with a hide rug. Stilt
houses (jungle planks, bamboo, thatch gables, ladders) line the side streets, with orchards of jungle fruit
trees (cocoa on the trunks, melon and berry rows) in the four corners. Every spawnable spot below y 30 has
block light (checked when this builds).
"""
import math

from _dwargon_lib import AIR, noise2, rnd
from _lords_lib import (M, clear, cone, disc_cells, fill, fill_air, floor_disc, light_pass, mix, pixel_art, put,
                        rect_ring, ring_cells, roofed, round_tower, slab, stair)

SIZE = (113, 46, 113)
SX, SY, SZ = SIZE
C = 56
G = 4
F = G + 1
PARTS = [0, 28, 56, 84]
ARRIVAL = (56, F, 108)

THATCH = "tensura:thatch_block"
THATCH_STAIRS = "tensura:thatch_stairs"
LANTERN = M("lantern[hanging=false]")
LANTERN_H = M("lantern[hanging=true]")
STONE = mix(71, (M("stone_bricks"), 55), (M("mossy_stone_bricks"), 25), (M("cobblestone"), 10), (M("cracked_stone_bricks"), 10))
ROAD = mix(72, (M("stone_bricks"), 45), (M("polished_andesite"), 35), (M("andesite"), 20))
PY = G + 3        # palace terrace top block (y 7)
PW = PY + 1       # walking level on the terrace
HX0, HX1, HZ0, HZ1 = 44, 68, 10, 44   # great hall footprint (25 x 35)
HWALL = 7


def ground():
    for x in range(SX):
        for z in range(SZ):
            for y in range(0, G):
                bp.set(x, y, z, M("stone") if y < 2 else M("dirt"))
            n = noise2(x, z, 6, 81)
            bp.set(x, G, z, M("grass_block") if n < 0.62 else M("moss_block") if n < 0.74 else M("coarse_dirt") if n < 0.86 else M("grass_block"))


def gable_z(x0, x1, z0, z1, y0, stairs, solid, under=True):
    """Gable roof over x0..x1, ridge along z, from layer y0 (eaves) upward; the roof shell is 2 thick diagonally."""
    k = 0
    while x0 + k <= x1 - k:
        xl, xr, y = x0 + k, x1 - k, y0 + k
        for z in range(z0, z1 + 1):
            if xl < xr:
                put(bp, xl, y, z, stairs("east"))
                put(bp, xr, y, z, stairs("west"))
                if under and xl + 1 < xr:
                    put(bp, xl + 1, y, z, solid)
                    put(bp, xr - 1, y, z, solid)
            else:
                put(bp, xl, y, z, solid)
        k += 1
    return y0 + k - 1


def tstairs(facing):
    return f"{THATCH_STAIRS}[facing={facing},half=bottom]"


def terrace():
    for x in range(28, 85):
        for z in range(4, 49):
            for y in range(F, PY + 1):
                bp.set(x, y, z, STONE(x, y, z) if y < PY else M("polished_andesite") if (x + z) % 5 else M("smooth_stone"))
    for x in range(28, 85):
        for z in (4, 48):
            put(bp, x, PW, z, M("stone_brick_wall"))
    for z in range(4, 49):
        for x in (28, 84):
            put(bp, x, PW, z, M("stone_brick_wall"))
    # grand steps on the south face, x 51..61 (ascending north)
    for k in range(3):
        for x in range(50, 63):
            put(bp, x, F + k, 49 + (2 - k) + 0, stair("stone_brick", "north"))
            for y in range(F, F + k):
                put(bp, x, y, 49 + (2 - k), M("stone_bricks"))
            if k == 2:
                put(bp, x, PW - 1 + 0, 48, M("stone_bricks"))
    for x in range(51, 62):
        put(bp, x, PW, 48, AIR)
    # lamp posts on the terrace corners and along the front
    for x in (32, 40, 48, 64, 72, 80):
        for k in range(3):
            put(bp, x, PW + k, 46, M("stone_brick_wall"))
        put(bp, x, PW + 3, 46, LANTERN)
    # garden pool behind the hall (north)
    for x in range(50, 63):
        for z in range(6, 9):
            bp.set(x, PY, z, M("water[level=0]"))
    rect_ring(bp, 49, 5, 63, 9, PW, M("jungle_fence"))


def hall():
    # stone footing and timber frame
    for y in range(PW, PW + 3):
        rect_ring(bp, HX0, HZ0, HX1, HZ1, y, STONE)
    for y in range(PW + 3, PW + HWALL):
        rect_ring(bp, HX0, HZ0, HX1, HZ1, y, M("bamboo_planks"))
    for x in range(HX0, HX1 + 1, 4):  # timber posts
        for z in (HZ0, HZ1):
            for y in range(PW, PW + HWALL + 1):
                put(bp, x, y, z, M("stripped_jungle_log[axis=y]"))
    for z in range(HZ0, HZ1 + 1, 4):
        for x in (HX0, HX1):
            for y in range(PW, PW + HWALL + 1):
                put(bp, x, y, z, M("stripped_jungle_log[axis=y]"))
    for x in range(HX0, HX1 + 1):  # tie beams
        for z in (HZ0, HZ1):
            put(bp, x, PW + HWALL, z, M("stripped_jungle_log[axis=x]"))
    for z in range(HZ0, HZ1 + 1):
        for x in (HX0, HX1):
            put(bp, x, PW + HWALL, z, M("stripped_jungle_log[axis=z]"))
    # window slots in the side walls (open, with a fence)
    for z in range(HZ0 + 3, HZ1 - 2, 4):
        for x in (HX0, HX1):
            for y in (PW + 4, PW + 5):
                put(bp, x, y, z, M("jungle_fence"))
    for x in range(HX0 + 3, HX1 - 2, 4):
        for y in (PW + 4, PW + 5):
            put(bp, x, y, HZ0, M("jungle_fence"))
    clear(bp, HX0 + 1, PW, HZ0 + 1, HX1 - 1, PW + 30, HZ1 - 1)
    for x in range(HX0 + 1, HX1):
        for z in range(HZ0 + 1, HZ1):
            put(bp, x, PY, z, M("jungle_planks") if (x + z) % 7 else M("stripped_jungle_log[axis=x]"))
    # roof: ridge along z, eaves overhang one block
    top = gable_z(HX0 - 1, HX1 + 1, HZ0 - 1, HZ1 + 1, PW + HWALL, tstairs, THATCH)
    # south gable wall: fill the triangle between the roof shell with planks, put the lion head in it
    k = 0
    while HX0 + k <= HX1 - k:
        y = PW + HWALL + k
        for x in range(HX0 + k + 1, HX1 - k):
            put(bp, x, y, HZ1, M("jungle_planks"))
        k += 1
    pixel_art(bp, C - 6, PW + HWALL + 11, HZ1 + 1, LION, LION_PAL)
    # great door in the south wall (x 53..59), colonnade of totem pillars in front
    for x in range(C - 3, C + 4):
        for y in range(PW, PW + 6):
            put(bp, x, y, HZ1, AIR)
            put(bp, x, y, HZ1 - 1, AIR)
    for x in (C - 4, C + 4):
        for y in range(PW, PW + 7):
            put(bp, x, y, HZ1, M("stripped_jungle_log[axis=y]"))
    for x in range(C - 4, C + 5):
        put(bp, x, PW + 6, HZ1, M("stripped_jungle_log[axis=x]"))
    for x in (HX0 + 4, HX0 + 10, HX1 - 10, HX1 - 4):
        for y in range(PW, PW + 9):
            put(bp, x, y, HZ1 + 3, M("jungle_log[axis=y]") if y % 3 else M("orange_terracotta"))
        put(bp, x, PW + 9, HZ1 + 3, M("yellow_terracotta"))   # totem cap: a lion's head block
        put(bp, x, PW + 8, HZ1 + 4, M("black_concrete"))
        put(bp, x, PW + 10, HZ1 + 3, M("jungle_fence"))
        put(bp, x, PW + 11, HZ1 + 3, LANTERN)
    for x in range(HX0 + 4, HX1 - 3):
        if x % 2:
            put(bp, x, PW + 7, HZ1 + 3, M("stripped_jungle_log[axis=x]"))
    # interior: tables, benches, chandeliers, the lion throne
    for z in range(HZ0 + 8, HZ1 - 6, 3):
        for x in (C - 7, C - 6, C + 6, C + 7):
            put(bp, x, PW, z, M("jungle_slab[type=top]"))
        for x in (C - 9, C + 9):
            put(bp, x, PW, z, M("jungle_stairs[facing=%s,half=bottom]" % ("east" if x < C else "west")))
        put(bp, C - 7, PW + 1, z, M("flower_pot"))
        put(bp, C + 7, PW + 1, z, M("flower_pot"))
    for z in range(HZ0 + 6, HZ1 - 4, 8):
        for x in (C - 6, C + 6):
            for y in range(PW + 8, PW + 13):
                put(bp, x, y, z, M("chain[axis=y]"))
            put(bp, x, PW + 7, z, LANTERN_H)
    for z in range(HZ0 + 6, HZ1 - 4, 8):
        for x in range(HX0 + 1, HX1):
            put(bp, x, PW + HWALL + 0, z, M("stripped_jungle_log[axis=x]"))
    # carpet aisle in orange
    for z in range(HZ0 + 2, HZ1):
        for x in range(C - 1, C + 2):
            put(bp, x, PW, z, M("orange_carpet"))
    # dais at the north end
    for x in range(C - 7, C + 8):
        for z in range(HZ0 + 1, HZ0 + 5):
            put(bp, x, PW, z, M("polished_andesite"))
    for x in range(C - 5, C + 6):
        for z in range(HZ0 + 1, HZ0 + 3):
            put(bp, x, PW + 1, z, M("polished_andesite"))
    for x in range(C - 7, C + 8):
        put(bp, x, PW, HZ0 + 5, stair("polished_andesite", "north"))
    for x in range(C - 5, C + 6):
        put(bp, x, PW + 1, HZ0 + 3, stair("polished_andesite", "north"))
    # throne: golden terracotta seat, tall back with mane, arm rests, a hide rug
    for x in range(C - 2, C + 3):
        for z in (HZ0 + 2, HZ0 + 3):
            put(bp, x, PW + 2, z, M("brown_wool"))
    put(bp, C, PW + 2, HZ0 + 2, M("yellow_terracotta"))
    for y in range(PW + 2, PW + 11):
        for x in range(C - 2, C + 3):
            put(bp, x, y, HZ0 + 1, M("orange_terracotta") if (abs(x - C) == 2 or y > PW + 8) else M("yellow_terracotta"))
    put(bp, C, PW + 11, HZ0 + 1, M("orange_terracotta"))
    for x in (C - 2, C + 2):
        for y in (PW + 2, PW + 3):
            put(bp, x, y, HZ0 + 2, M("yellow_terracotta"))
    for x in (C - 4, C + 4):
        put(bp, x, PW + 2, HZ0 + 2, M("jungle_fence"))
        put(bp, x, PW + 3, HZ0 + 2, M("jungle_fence"))
        put(bp, x, PW + 4, HZ0 + 2, LANTERN)
    # blue banners (Tempest) beside the throne: a reminder of who helped build the city
    for x in (C - 6, C + 6):
        for y in range(PW + 3, PW + 8):
            put(bp, x, y, HZ0 + 1, M("light_blue_wool"))


LION = [
    "...BBBBBBB...",
    "..BOOOOOOOB..",
    ".BOOYYYYYOOB.",
    "BOOYYYYYYYOOB",
    "BOYYKYYYKYYOB",
    "BOYYYYYYYYYOB",
    "BOOYYYKYYYOOB",
    ".BOYYKKKYYOB.",
    ".BOOYWRWYOOB.",
    "..BOOWRWOOB..",
    "...BBOOOBB...",
]
LION_PAL = {"B": M("brown_concrete"), "O": M("orange_concrete"), "Y": M("yellow_concrete"), "K": M("black_concrete"),
            "W": M("white_concrete"), "R": M("red_concrete")}


def walls():
    for y in range(F, F + 7):
        for t in range(2):
            rect_ring(bp, C - 50 + t, C - 50 + t, C + 50 - t, C + 50 - t, y, STONE)
    for x in range(C - 50, C + 51):
        for z in (C - 50, C + 50):
            if (x + z) % 2 == 0:
                put(bp, x, F + 7, z, M("stone_brick_wall"))
    for z in range(C - 50, C + 51):
        for x in (C - 50, C + 50):
            if (x + z) % 2 == 0:
                put(bp, x, F + 7, z, M("stone_brick_wall"))
    for cx, cz in ((C - 49, C - 49), (C + 49, C - 49), (C - 49, C + 49), (C + 49, C + 49)):
        round_tower(bp, cx, cz, 3, F, F + 10, STONE, glass=None)
        floor_disc(bp, cx, cz, 3, F + 11, M("stripped_jungle_log[axis=y]"))
        cone(bp, cx, cz, F + 12, 4.5, 6, THATCH, finial=[M("jungle_fence")])
    # south gate: opening x 52..60, y F..F+5, arched; gate towers
    for x in range(C - 4, C + 5):
        for z in (C + 49, C + 50):
            for y in range(F, F + 6):
                if y == F + 5 and abs(x - C) >= 3:
                    continue
                put(bp, x, y, z, AIR)
    for x in range(C - 4, C + 5):
        for z in (C + 49, C + 50):
            put(bp, x, G, z, ROAD(x, G, z))
    for gx in (C - 7, C + 7):
        round_tower(bp, gx, C + 49, 3, F, F + 10, STONE, glass=None)
        floor_disc(bp, gx, C + 49, 3, F + 11, M("stripped_jungle_log[axis=y]"))
        cone(bp, gx, C + 49, F + 12, 4.5, 6, THATCH, finial=[M("jungle_fence")])
    for x in range(C - 5, C + 6):  # lintel and a banner each side
        put(bp, x, F + 6, C + 50, M("stripped_jungle_log[axis=x]"))
    for x in (C - 5, C + 5):
        for y in range(F + 1, F + 6):
            put(bp, x, y, C + 51, M("light_blue_wool"))
    for x in (C - 4, C + 4):
        put(bp, x, F + 6, C + 49, LANTERN_H)


def roads():
    # avenue from the gate to the plaza and on to the palace
    for z in range(30, SZ):
        for x in range(C - 4, C + 5):
            bp.set(x, G, z, ROAD(x, G, z))
    # plaza
    for x, z in disc_cells(C, 66, 13):
        bp.set(x, G, z, ROAD(x, G, z))
    # fountain
    for x, z in disc_cells(C, 66, 3):
        bp.set(x, G, z, M("water[level=0]"))
    for x, z in ring_cells(C, 66, 4):
        bp.set(x, F, z, M("stone_brick_wall"))
        bp.set(x, G, z, M("stone_bricks"))
    bp.set(C, F, 66, M("stone_bricks"))
    bp.set(C, F + 1, 66, M("stone_brick_wall"))
    bp.set(C, F + 2, 66, M("sea_lantern"))
    # side streets
    for z in (72, 86):
        for x in range(8, 105):
            if abs(x - C) > 4 and bp.blocks.get((x, G, z)) and bp.blocks[(x, G, z)].startswith("minecraft:") and bp.blocks[(x, G, z)] != M("water[level=0]"):
                bp.set(x, G, z, M("gravel") if rnd(x, 1, z, 83) < 0.7 else M("coarse_dirt"))
        for x in range(8, 105):
            if abs(x - C) > 14 and x % 8 == 0:
                for k in range(1, 4):
                    put(bp, x, G + k, z + 1, M("jungle_fence"))
                put(bp, x, G + 4, z + 1, LANTERN)
    for z in range(54, 100, 8):  # lamp posts along the avenue
        for x in (C - 5, C + 5):
            if math.hypot(x - C, z - 66) > 14:
                for k in range(1, 4):
                    put(bp, x, G + k, z, M("jungle_fence"))
                put(bp, x, G + 4, z, LANTERN)
    # market stalls around the plaza
    for i in range(12):
        a = math.radians(i * 30 + 15)
        sx, sz = round(C + 9.5 * math.cos(a)), round(66 + 9.5 * math.sin(a))
        if abs(sx - C) <= 5 and abs(sz - 66) >= 7:
            continue
        colour = ("red", "yellow", "orange", "lime")[i % 4]
        for dx in (0, 2):
            for dz in (0, 2):
                for y in range(F, F + 3):
                    put(bp, sx + dx, y, sz + dz, M("jungle_fence"))
        for dx in range(-1, 4):
            for dz in range(-1, 4):
                put(bp, sx + dx, F + 3, sz + dz, M(f"{colour}_wool"))
        put(bp, sx + 1, F, sz + 1, M("barrel[facing=up]"))
        put(bp, sx + 1, F + 1, sz + 1, M("melon"))
        put(bp, sx, F, sz + 1, M("hay_block[axis=y]"))
        put(bp, sx + 2, F, sz + 1, M("melon"))
        put(bp, sx + 1, F, sz, M("jungle_slab[type=top]"))
        put(bp, sx + 1, F + 2, sz + 1, LANTERN_H)


def stilt_house(hx, hz, face):
    """5x5 house on four posts (floor y F+3), jungle planks and bamboo, a thatch gable, a ladder on the `face` side."""
    x0, z0 = hx - 2, hz - 2
    for dx in (0, 4):
        for dz in (0, 4):
            for y in range(F, F + 4):
                put(bp, x0 + dx, y, z0 + dz, M("jungle_log[axis=y]"))
    for dx in range(5):
        for dz in range(5):
            put(bp, x0 + dx, F + 3, z0 + dz, M("jungle_planks"))
    for y in range(F + 4, F + 7):
        rect_ring(bp, x0, z0, x0 + 4, z0 + 4, y, M("bamboo_planks"))
    for dx in (0, 4):
        for dz in (0, 4):
            for y in range(F + 4, F + 7):
                put(bp, x0 + dx, y, z0 + dz, M("stripped_jungle_log[axis=y]"))
    for y in (F + 5,):
        for p in ((hx, z0), (hx, z0 + 4), (x0, hz), (x0 + 4, hz)):
            put(bp, p[0], y, p[1], M("jungle_fence"))
    door = {"n": (hx, z0), "s": (hx, z0 + 4), "e": (x0 + 4, hz), "w": (x0, hz)}[face]
    for y in (F + 4, F + 5):
        put(bp, door[0], y, door[1], AIR)
    # a ladder from the ground to the door sill, on the outside, hung on a post under the door (a ladder hangs on the
    # block opposite its facing, and the stilts leave the wall open below the floor)
    lad = {"n": (door[0], door[1] - 1, "north"), "s": (door[0], door[1] + 1, "south"),
           "e": (door[0] + 1, door[1], "east"), "w": (door[0] - 1, door[1], "west")}[face]
    for y in range(F, F + 3):
        put(bp, door[0], y, door[1], M("jungle_log[axis=y]"))
    for y in range(F, F + 4):
        put(bp, lad[0], y, lad[1], f"minecraft:ladder[facing={lad[2]}]")
    gable_z(x0 - 1, x0 + 5, z0 - 1, z0 + 5, F + 7, tstairs, THATCH)
    put(bp, hx, F + 4, hz, LANTERN)
    put(bp, hx - 1, F + 4, hz - 1, M("red_bed[facing=north,part=head]"))
    put(bp, hx - 1, F + 4, hz, M("red_bed[facing=north,part=foot]"))
    put(bp, hx + 1, F + 4, hz + 1, M("barrel[facing=up]"))
    # clear the ground under the house so the space reads as a stilt house
    for dx in range(1, 4):
        for dz in range(1, 4):
            put(bp, x0 + dx, G, z0 + dz, M("packed_mud"))


def orchard(x0, z0, x1, z1):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x - x0) % 4 == 2 and (z - z0) % 4 == 2:
                h = 4 + int(rnd(x, 1, z, 91) * 3)
                for y in range(F, F + h):
                    put(bp, x, y, z, M("jungle_log[axis=y]"))
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        for dy in (0, 1):
                            if abs(dx) + abs(dz) + dy < 4 and (dx or dz or dy):
                                put(bp, x + dx, F + h - 1 + dy, z + dz, M("jungle_leaves[persistent=true]"))
                put(bp, x, F + h, z, M("jungle_leaves[persistent=true]"))
                put(bp, x + 1, F + 2, z, M("cocoa[age=2,facing=west]"))
                put(bp, x - 1, F + 1, z, M("cocoa[age=2,facing=east]"))
            elif (x - x0) % 4 == 0 and (z - z0) % 2 == 0 and rnd(x, 2, z, 92) < 0.7:
                put(bp, x, F, z, M("sweet_berry_bush[age=3]"))
            elif (x - x0) % 4 == 3 and (z - z0) % 3 == 0 and rnd(x, 3, z, 93) < 0.6:
                put(bp, x, F, z, M("melon"))


def jungle_tree(x, z, h):
    for y in range(F, F + h):
        put(bp, x, y, z, M("jungle_log[axis=y]"))
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            for dy in range(-1, 3):
                if math.hypot(dx, dz) + abs(dy) * 1.2 <= 3.3 and rnd(x + dx, z + dz, dy, 94) < 0.9:
                    put(bp, x + dx, F + h + dy, z + dz, M("jungle_leaves[persistent=true]"))


def palm(x, z, h):
    for y in range(F, F + h):
        put(bp, x + (1 if y > F + h // 2 else 0), y, z, M("jungle_wood"))
    tx = x + 1
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        for i in range(1, 4):
            put(bp, tx + dx * i, F + h - (1 if i > 1 else 0) - (i // 3), z + dz * i, M("jungle_leaves[persistent=true]"))
    put(bp, tx, F + h, z, M("jungle_leaves[persistent=true]"))


def settlement():
    houses = []
    for z in (60, 78, 92):
        for x in (14, 24, 34, 78, 88, 98):
            if z == 60 and 40 < x < 72:
                continue
            houses.append((x, z, "e" if x < C else "w"))
    for x in (16, 28, 40, 72, 84, 96):
        houses.append((x, 18, "s"))
    for hx, hz, face in houses:
        hx += int((rnd(hx, hz, 1, 95) - 0.5) * 3)
        hz += int((rnd(hx, hz, 2, 96) - 0.5) * 3)
        if hz < 50 and 26 < hx < 86:
            continue
        stilt_house(hx, hz, face)
    orchard(10, 98, 40, 106)
    orchard(72, 98, 102, 106)
    orchard(9, 30, 24, 54)
    orchard(88, 30, 103, 54)
    for k in range(36):
        x = int(rnd(k, 1, 6, 101) * (SX - 10)) + 5
        z = int(rnd(k, 2, 6, 102) * (SZ - 10)) + 5
        if abs(x - C) < 7 or (26 < x < 86 and z < 52):
            continue
        if bp.blocks.get((x, F, z)) != AIR or bp.blocks.get((x, G, z)) not in (M("grass_block"), M("moss_block")):
            continue
        if any(bp.blocks.get((x + dx, F, z + dz)) != AIR for dx in range(-3, 4) for dz in range(-3, 4)):
            continue
        (palm if k % 2 else jungle_tree)(x, z, 6 + int(rnd(k, 3, 6, 103) * 3))
    # plants on open grass
    for x in range(SX):
        for z in range(SZ):
            if bp.blocks.get((x, F, z)) == AIR and bp.blocks.get((x, G, z)) in (M("grass_block"), M("moss_block")):
                r = rnd(x, 7, z, 104)
                if r < 0.16:
                    bp.set(x, F, z, M("short_grass"))
                elif r < 0.21:
                    bp.set(x, F, z, M("fern"))


def build(b):
    global bp
    bp = b
    fill_air(bp, 0)
    ground()
    roads()
    terrace()
    hall()
    walls()
    settlement()

    def region(x, y, z):
        return 3 <= x <= SX - 4 and 3 <= z <= SZ - 4 and (y <= 30 or roofed(bp, x, y, z))

    n = light_pass(bp, region, G + 1, lambda x, y, z: LANTERN, post=lambda x, y, z: [
        (0, M("jungle_fence")), (1, M("jungle_fence")), (2, M("jungle_fence")), (3, LANTERN)],
        label="laura")
    print(f"laura: {n} extra lamps")
