"""Marris: capital of the Kingdom of Falmuth (later Farmenas) with the royal castle and the Western Holy Church.

Lore, canon notes and our interpretation: design/lore/marris.md. SIZE (136, 64, 112), three z slabs marris_0..2
(z 0-37, 38-75, 76-111; PARTS). Ground layer y 4 (you walk at y 5), air above. The great gate faces south (+z).
Arrival point: blueprint (68, 5, 106) on the royal road, facing north.

Layout, from the south: royal road (x 63-73) -> great gate in the city wall (z 92-96; opening x 63-73, y 5-12,
two tall gate towers with copper roofs and blue-and-white banners) -> the King's Avenue (x 62-74, z 78-91) lined
with tall townhouses -> the Royal Plaza (x 24-112, z 38-76, checker paving, a fountain monument at 68,57, banner
poles) with, on its west side, the Western Holy Church (x 24-46, z 50-68: white quartz nave with buttresses, blue
glass windows and a rose window over the doors, door on the east face at z 58-60, pews, aisle, altar at the west
end, a bell tower with a copper spire at x 46-52, z 44-50) and, on its east side, the Falmuth guard and customs
house -> at the north end the royal castle (curtain wall z 34-36 with a gatehouse at x 64-72, courtyard z 22-33,
the palace x 40-96, z 6-21 with a throne hall on the ground floor behind a grand portal and four copper-roofed
corner towers). City walls run north along both sides to the castle's flanks.

Points (blueprint coordinates): church door (46, 5, 59), altar (27, 6, 59), throne seat (68, 6, 9), plaza centre
(68, 5, 57). Style (our interpretation): pale stone and white quartz, verdigris copper roofs, blue and white
heraldry, gold trim on the church; richer and taller than Blumund's plastered timber town.
Block light is checked for every spawnable spot inside the walls and on the approach.
"""
import math

from _dwargon_lib import AIR, rnd
from _town_lib import (M, Town, banner, bed, door, fence_gate, lantern_floor, lantern_hung, log, slab, stair,
                       trapdoor, wall_banner)
from blumund import arch, fountain, wall_stairs, FENCE

SIZE = (136, 64, 112)
SX, SY, SZ = SIZE
G = 4
F = G + 1
PARTS = [0, 38, 76]
ARRIVAL = (68, F, 106)
CX = 68
WALL_H = 9
PANE = "glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"
BLUE_PANE = "blue_stained_glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"
PLASTERS = ("calcite", "smooth_quartz", "calcite", "stone_bricks")


def inside(x, z) -> bool:
    return (9 <= x <= 126 and 7 <= z <= 91) or (CX - 14 <= x <= CX + 14 and 97 <= z <= 110)


def roads(t: Town):
    t.pave(63, 97, 73, 111, "street")
    t.pave(62, 78, 74, 96, "street")
    t.pave(24, 38, 112, 76, "plaza")
    t.pave(62, 34, 74, 37, "street")


def walls_and_gates(t: Town):
    t.rampart(6, 92, 129, 96, WALL_H, "s")
    arch(t, 63, 73, 92, 96, 8)
    for tx in (52, 74):
        t.tower(tx, 90, tx + 9, 98, WALL_H + 8, "copper",
                flags=lambda top, tx=tx: (tx + 4, top + 1, 94, banner("light_blue")))
    t.rampart(6, 4, 8, 92, WALL_H, "w")
    t.rampart(127, 4, 129, 92, WALL_H, "e")
    t.rampart(6, 4, 129, 6, WALL_H, "n")
    for x, z in ((3, 90), (127, 90), (3, 1), (127, 1)):
        t.tower(x, z, x + 6, z + 6, WALL_H + 7, "copper", flags=lambda top, x=x, z=z: (x + 3, top + 1, z + 3, banner("white")))
    wall_stairs(t, 14, 91, WALL_H, "x")
    wall_stairs(t, 121, 91, WALL_H, "x", -1)
    for x in (61, 75):
        for y in (F + 5, F + 6, F + 7):
            pass
        t.put(x, F + 6, 91, wall_banner("light_blue", "north"))
    # great-gate decoration: banners on the wall face, portcullis grille high in the passage
    for x in range(64, 73):
        t.put(x, F + 7, 93, M("iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]"))


def royal_plaza(t: Town):
    fountain(t, CX, 57)
    for (x, z) in ((32, 42), (104, 42), (32, 72), (104, 72), (50, 42), (86, 42), (50, 72), (86, 72)):
        t.banner_pole(x, z, "light_blue", 6)
    for x in (30, 106):
        for z in (45, 69):
            t.lamp(x, z, 3, post="stone_brick_wall")


def townhouses(t: Town):
    # King's Avenue: tall townhouses, doors on the avenue
    for x0, x1, side in ((44, 60, "e"), (76, 92, "w")):
        z = 78
        for d in (6, 6):
            t.house(x0 if side == "e" else x0, z, x1, z + d + 1, side, 3, plaster=PLASTERS[int(rnd(x0, z, 3, 1) * 4)],
                    roof="slate", axis="z", frame="dark_oak", base="stone_bricks")
            z += d + 2
    for x0, x1, side in ((24, 42, "e"), (94, 112, "w")):
        pass
    # the customs house on the plaza's east side
    t.house(94, 48, 110, 66, "w", 3, plaster="stone_bricks", roof="copper", axis="z", frame="spruce")
    # more houses along the avenue's rear and corners
    for z0 in (82, 88):
        pass
    for x0 in (12, 100):
        t.house(x0, 78, x0 + 10, 88, "e" if x0 < 60 else "w", 2, plaster="calcite", roof="slate", axis="z")
    t.house(26, 80, 38, 88, "e", 3, plaster="smooth_quartz", roof="slate", axis="z")
    t.house(98, 80, 110, 88, "w", 3, plaster="calcite", roof="slate", axis="z")


def church(t: Town):
    """Western Holy Church: a quartz cathedral with buttresses, blue windows, a rose window and a bell tower."""
    x0, x1, z0, z1 = 24, 46, 50, 68
    top = F + 12
    qb, qp = M("quartz_bricks"), M("quartz_pillar[axis=y]")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            t.put(x, G, z, M("polished_andesite") if (x // 2 + z // 2) % 2 else M("smooth_quartz"))
            edge = x in (x0, x1) or z in (z0, z1)
            if not edge:
                continue
            corner = x in (x0, x1) and z in (z0, z1)
            for y in range(F, top + 1):
                t.put(x, y, z, qp if corner else (M("stone_bricks") if y <= F else qb))
    # buttresses (every 4) on the long walls with stepped tops
    for x in range(x0 + 2, x1 - 1, 4):
        for z in (z0 - 1, z1 + 1):
            for y in range(F, F + 9):
                t.put(x, y, z, qp)
            t.put(x, F + 9, z, M("quartz_slab[type=bottom,waterlogged=false]"))
        # tall blue windows between the buttresses
    for x in range(x0 + 4, x1 - 2, 4):
        for z in (z0, z1):
            for y in range(F + 3, F + 9):
                t.put(x, y, z, M(BLUE_PANE))
            t.put(x, F + 9, z, M("quartz_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]" % ("south" if z == z0 else "north")))
    for z in range(z0 + 3, z1 - 2, 4):
        for y in range(F + 3, F + 9):
            t.put(x0, y, z, M(BLUE_PANE))
    # tall west window behind the altar
    for z in range(57, 62):
        for y in range(F + 2, F + 10):
            t.put(x0, y, z, M(BLUE_PANE))
    # facade (east): doors, rose window, steps
    for z in (58, 59, 60):
        for y in range(F, F + 4):
            t.put(x1, y, z, AIR)
    t.put(x1, F, 58, door("spruce", "west", "lower", "left"))
    t.put(x1, F + 1, 58, door("spruce", "west", "upper", "left"))
    t.put(x1, F, 60, door("spruce", "west", "lower", "right"))
    t.put(x1, F + 1, 60, door("spruce", "west", "upper", "right"))
    for y in (F, F + 1):
        t.put(x1, y, 59, AIR)
    for y in (F + 2, F + 3):
        for z in (58, 59, 60):
            t.put(x1, y, z, M(BLUE_PANE))
    for z in (57, 61):
        for y in range(F, F + 4):
            t.put(x1, y, z, qp)
    for z in range(57, 62):
        t.put(x1, F + 4, z, M("quartz_bricks"))
    for z in (57, 61):
        t.put(x1, F + 3, z, qp)
    for dz in range(-3, 4):
        for dy in range(-3, 4):
            d = math.hypot(dz, dy)
            if 1.2 <= d <= 3.2:
                t.put(x1, F + 8 + dy, 59 + dz, M(BLUE_PANE) if d < 2.6 else M("chiseled_quartz_block"))
            elif d < 1.2:
                t.put(x1, F + 8 + dy, 59 + dz, M("gold_block"))
    for z in range(55, 64):
        t.put(x1 + 1, G, z, M("smooth_quartz"))
        t.put(x1 + 2, G, z, M("smooth_quartz"))
    # roof: gable with ridge along x
    t.gable(x0, z0, x1, z1, top + 1, "slate", "x", qb)
    # interior: aisle, pews, altar, columns, chandeliers
    for x in range(x0 + 2, x1):
        t.put(x, F, 59, M("light_blue_carpet"))
    for x in range(x0 + 8, x1 - 3, 3):
        for z in (53, 54, 55, 63, 64, 65):
            t.put(x, F, z, stair("spruce", "west"))
    for x in (x0 + 5, x0 + 9, x0 + 13, x0 + 17):
        for z in (z0 + 1, z1 - 1):
            for y in range(F, F + 12):
                t.put(x, y, z, qp) if t.get(x, y, z) == AIR else None
    for x in range(x0 + 1, x0 + 5):
        for z in range(55, 64):
            t.put(x, F, z, M("quartz_block"))
    for x in range(x0 + 1, x0 + 3):
        for z in range(56, 63):
            t.put(x, F + 1, z, M("quartz_slab[type=bottom,waterlogged=false]"))
    t.put(x0 + 2, F + 2, 59, M("quartz_slab[type=bottom,waterlogged=false]"))
    t.put(x0 + 2, F + 1, 59, M("quartz_block"))
    t.put(x0 + 2, F + 3, 59, M("candle[candles=3,lit=true,waterlogged=false]"))
    for z in (56, 62):
        t.put(x0 + 2, F + 2, z, M("candle[candles=2,lit=true,waterlogged=false]"))
    for z in range(57, 62):
        t.put(x0 + 1, F + 6, z, M("gold_block") if z == 59 else M("blue_wool"))
    for z in (55, 63):
        t.put(x0 + 1, F + 4, z, wall_banner("light_blue", "east"))
    t.points["altar"] = (x0 + 3, F + 2, 59)
    t.points["door"] = (x1 + 1, F, 59)
    for x in (30, 36, 42):
        for y in range(F + 19, F + 23):
            t.put(x, y, 59, M("chain[axis=y,waterlogged=false]"))
        t.put(x, F + 18, 59, lantern_hung())
    # bell tower at the north-east corner, solid body with a belfry and a copper spire
    tx0, tz0 = 46, 44
    t.tower(tx0, tz0, tx0 + 6, tz0 + 6, 26, "copper", flags=lambda top: (tx0 + 3, top + 1, tz0 + 3, banner("light_blue")))
    t.points["bell_tower"] = (tx0 + 3, F + 27, tz0 + 3)


def palace(t: Town):
    # curtain wall and gatehouse toward the plaza
    t.rampart(28, 34, 108, 36, WALL_H, "s")
    arch(t, 64, 72, 34, 36, 7)
    for tx in (54, 74):
        t.tower(tx, 32, tx + 8, 38, WALL_H + 6, "copper")
    t.rampart(28, 6, 30, 33, WALL_H, "w")
    t.rampart(106, 6, 108, 33, WALL_H, "e")
    for x, z in ((24, 31), (106, 31), (24, 4), (106, 4)):
        t.tower(x, z, x + 6, z + 6, WALL_H + 11, "copper", flags=lambda top, x=x, z=z: (x + 3, top + 1, z + 3, banner("light_blue")))
    # palace block
    px0, px1, pz0, pz1 = 40, 96, 8, 21
    top = F + 17
    for x in range(px0, px1 + 1):
        for z in range(pz0, pz1 + 1):
            t.put(x, G, z, M("polished_andesite") if (x + z) % 4 else M("stone_bricks"))
            edge = x in (px0, px1) or z in (pz0, pz1)
            for y in range(F, top + 1):
                if edge:
                    t.stone(x, y, z)
                else:
                    t.put(x, y, z, AIR)
            if not edge:
                t.put(x, F + 8, z, M("spruce_planks"))
                t.put(x, top, z, M("stone_bricks"))
    # windows on the facade and sides
    for x in range(px0 + 3, px1 - 1, 4):
        for z in (pz0, pz1):
            for y in (F + 3, F + 4, F + 5, F + 11, F + 12, F + 13):
                if z == pz1 and 62 <= x <= 74 and y < F + 8:
                    continue
                t.put(x, y, z, M(PANE))
    for z in range(pz0 + 3, pz1 - 1, 4):
        for x in (px0, px1):
            for y in (F + 3, F + 4, F + 11, F + 12):
                t.put(x, y, z, M(PANE))
    # grand portal on the courtyard side (x 64-72)
    for x in range(64, 73):
        for y in range(F, F + 7):
            t.put(x, y, pz1, AIR)
        t.put(x, F + 7, pz1, M("stone_bricks"))
    t.put(64, F + 6, pz1, stair("stone_brick", "west", "top"))
    t.put(72, F + 6, pz1, stair("stone_brick", "east", "top"))
    for x in (63, 73):
        for y in range(F, F + 9):
            t.put(x, y, pz1 + 1, log("dark_oak_log"))
        t.put(x, F + 9, pz1 + 1, M("lantern[hanging=false,waterlogged=false]"))
    for x in range(62, 75):
        t.bp.blocks[(x, G, pz1 + 1)] = M("stone_bricks")
        t.bp.blocks[(x, G, pz1 + 2)] = M("stone_bricks")
        t.bp.blocks[(x, G, pz1 + 3)] = M("stone_bricks")
    # battlements and a central hip roof with banners
    t.battlements(px0, pz0, px1, pz1, top + 1)
    t.hip(58, 10, 78, 19, top + 1, "copper", overhang=1)
    for x, z in ((46, 14), (90, 14)):
        t.hip(x - 2, z - 2, x + 2, z + 2, top + 1, "copper", overhang=1)
    # throne hall: carpet, columns, dais, throne, banners and chandeliers
    for z in range(pz0 + 6, pz1):
        for x in (67, 68, 69):
            t.put(x, F, z, M("light_blue_carpet") if x == 68 else M("white_carpet"))
    for x in (52, 84):
        for z in (14, 18):
            for y in range(F, F + 8):
                t.put(x, y, z, M("stone_bricks") if y < F + 7 else M("chiseled_stone_bricks"))
    for x in range(62, 75):
        for z in range(pz0 + 1, pz0 + 4):
            t.put(x, F, z, M("stone_bricks"))
        t.put(x, F + 1, pz0 + 1, M("stone_bricks"))
    t.put(68, F + 1, pz0 + 2, stair("dark_oak", "north"))
    for y in (F + 2, F + 3, F + 4):
        t.put(68, y, pz0 + 1, M("dark_oak_planks"))
    for x in (67, 69):
        t.put(x, F + 1, pz0 + 2, stair("dark_oak", "north"))
    t.points["throne"] = (68, F + 1, pz0 + 2)
    for z in (11, 15, 19):
        t.put(px0 + 1, F + 4, z, wall_banner("light_blue", "east"))
        t.put(px1 - 1, F + 4, z, wall_banner("white", "west"))
    for x in (60, 76):
        for z in (12, 17):
            for y in range(F + 5, F + 8):
                t.put(x, y, z, M("chain[axis=y,waterlogged=false]"))
            t.put(x, F + 4, z, lantern_hung())
    # stairs to the gallery floor (east side, climbing north)
    for i in range(9):
        z = 20 - i
        t.fill(95, F, z, 95, F + i - 1, z, M("stone_bricks")) if i else None
        t.put(95, F + i, z, stair("stone_brick", "north"))
    for z in range(13, 21):
        t.put(95, F + 8, z, AIR)
    for x in (50, 62, 74, 86):
        t.put(x, F + 16, 14, lantern_hung())
    # courtyard: cobbles, road, well, guard barracks and stables
    t.pave(62, 22, 74, 33, "street")
    t.pave(30, 22, 106, 33, "cobble")
    t.pave(62, 22, 74, 33, "street")
    t.house(34, 25, 46, 32, "e", 2, plaster="calcite", roof="slate", axis="z")
    t.house(90, 25, 102, 32, "w", 2, plaster="calcite", roof="slate", axis="z")
    for x in (56, 80):
        t.tree(x, 28, "oak", 4, 2)
    t.points["castle_gate"] = (68, F, 37)


def approach(t: Town):
    for (xa, xb) in ((20, 56), (80, 116)):
        for x in range(xa, xb + 1):
            for z in range(100, 111):
                if (x - xa) % 4 == 3:
                    t.bp.blocks[(x, G, z)] = M("water[level=0]")
                else:
                    t.bp.blocks[(x, G, z)] = M("farmland[moisture=7]")
                    t.put(x, F, z, M("wheat[age=%d]" % (5 + int(rnd(x, 0, z, 4) * 3))))
        for x in range(xa - 1, xb + 2):
            for z in (99, 111):
                t.put(x, F, z, M(FENCE))
        for z in range(99, 112):
            for x in (xa - 1, xb + 1):
                t.put(x, F, z, M(FENCE))
    for z in (99, 111):
        for x in (56, 57, 79, 80):
            t.put(x, F, z, AIR)
    for z in (98, 106):
        for x in (62, 74):
            t.lamp(x, z, 3, post="spruce_fence")
    for x, z, k in ((58, 108, "oak"), (78, 109, "birch"), (12, 105, "oak"), (124, 104, "oak"), (4, 98, "birch"), (132, 98, "oak")):
        t.tree(x, z, k, 5, 2)


def build(bp):
    t = Town(bp, G)
    bp.town = t
    t.base_ground()
    roads(t)
    walls_and_gates(t)
    royal_plaza(t)
    palace(t)
    church(t)
    townhouses(t)
    approach(t)
    t.light(inside)
    t.check_support()
