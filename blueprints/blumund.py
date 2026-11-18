"""Blumund: the small trading kingdom's walled capital (Londo on the fan map) with the Free Guild branch hall.

Lore, canon notes and our interpretation: design/lore/blumund.md. SIZE (124, 52, 116), saved as three z slabs
blumund_0..2 (z 0-39, 40-79, 80-115; PARTS). Ground layer y 4 (grass, paved streets; dirt below), you walk at y 5;
everything above is air so placement clears trees and hills inside the box. The gate faces south (+z). Arrival
point: blueprint (62, 5, 108) on the king's road, 15 blocks south of the gate, facing north.

Layout, from the south: approach road (z 93-115, x 59-65) between wheat fields and a farmstead; town wall z 90-92
(plastered timber is for houses, the wall is stone) with the south gate, opening x 59-65, y 5-9, flanked by two
gate towers; the main street (x 58-66) runs north through the gate; a few houses and a well at the gate; the market
square (x 34-90, z 54-80: checker paving, fountain at 62,67, twelve striped market stalls); the Free Guild branch
hall on the square's east side (x 93-112, z 56-80, door on the west side at z 67-68, double-height hall with the
reception counter, two notice boards, tavern tables, and a mezzanine office for the branch master); the merchant
cross street (z 50-52) with shops on both flanks; west district (two rows of houses facing the square and a rear
lane); south rows (z 82-88) between the gate and the square; at the north end the royal castle on the main axis:
ward wall z 46-48 with a gatehouse, courtyard z 32-45 (well, barracks, stable), the keep (x 50-74, z 10-28; throne
hall on the ground floor, council chamber above, battlemented roof) with four corner towers up to y 32, and the
side walls running north to the town's north wall (z 4-6). Orchards flank the castle.

Guild points (blueprint coordinates): reception counter x 102, z 60-76 (customers stand west of it, staff at x 103);
main quest board x 94, z 58-64, y 6-8 (a framed 7x3 panel on the west wall's inside); second (bounty) board x 94,
z 72-78; branch master's desk on the mezzanine at (109, 11, 61); stairs up at x 98-103, z 57. Throne seat (62, 6, 12).

Style: plastered timber-frame houses (calcite / cream plaster, dark oak frame, red tile roofs), stone walls and
gates, slate roofs on civic buildings, red and cream banners (our interpretation, canon gives no heraldry).
Block light is checked for every spawnable spot inside the walls and the approach.
"""
import math

from _dwargon_lib import AIR, noise2, rnd
from _town_lib import (M, Town, banner, bed, door, fence_gate, lantern_floor, lantern_hung, log, slab, stair,
                       trapdoor, wall_banner)

SIZE = (124, 52, 116)
SX, SY, SZ = SIZE
G = 4
F = G + 1
PARTS = [0, 40, 80]
ARRIVAL = (62, F, 108)
CX = 62
WALL_H = 7      # wall body height (F..F+6), walkway layer at F+7
PLASTERS = ("calcite", "calcite", "smooth_sandstone", "white_terracotta", "calcite")
ROOFS_H = ("brick", "brick", "brick", "mud", "nether")
FENCE = "spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


def inside(x, z) -> bool:
    return (11 <= x <= 112 and 7 <= z <= 89) or (CX - 14 <= x <= CX + 14 and 93 <= z <= 112)


def arch(t: Town, x0, x1, z0, z1, h=5):
    """Carve a gate passage x0..x1 through z0..z1, height h, with cut upper corners."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(F, F + h):
                t.put(x, y, z, AIR)
            t.put(x, F + h, z, M("stone_bricks"))
    for z in range(z0, z1 + 1):
        t.put(x0, F + h, z, stair("stone_brick", "west", "top"))
        t.put(x1, F + h, z, stair("stone_brick", "east", "top"))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            t.put(x, G, z, M("stone_bricks" if (x + z) % 3 else "cobblestone"))


def wall_stairs(t: Town, x, z, length, axis, step=1):
    """Stairs up to a wall walk along its inner face. axis 'x': climbs east/west along z=z; 'z': along x=x."""
    for i in range(length + 1):
        if axis == "x":
            px, pz, face = x + step * i, z, ("east" if step > 0 else "west")
        else:
            px, pz, face = x, z + step * i, ("south" if step > 0 else "north")
        t.fill(px, F, pz, px, F + i - 1, pz, M("stone_bricks")) if i else None
        t.put(px, F + i, pz, stair("stone_brick", face))
    return


def walls_and_gates(t: Town):
    # south wall with the main gate
    t.rampart(8, 90, 115, 92, WALL_H, "s")
    arch(t, 59, 65, 90, 92, 5)
    for tx in (50, 67):
        t.tower(tx, 88, tx + 6, 94, WALL_H + 5, "slate")
    t.rampart(8, 4, 10, 92, WALL_H, "w")
    t.rampart(113, 4, 115, 92, WALL_H, "e")
    t.rampart(8, 4, 115, 6, WALL_H, "n")
    for x, z in ((5, 87), (112, 87), (5, 1), (112, 1)):
        t.tower(x, z, x + 6, z + 6, WALL_H + 5, "slate", flags=lambda top, x=x, z=z: (x + 3, top + 1, z + 3, banner("red")))
    # inner stairs to the walls
    wall_stairs(t, 16, 89, WALL_H, "x")
    wall_stairs(t, 105, 89, WALL_H, "x", -1)
    wall_stairs(t, 11, 20, WALL_H, "z")
    wall_stairs(t, 112, 20, WALL_H, "z")
    # shutters, banners on the gate wall
    for x in (57, 67):
        t.put(x, F + 4, 89, wall_banner("red", "north"))
    for x in (58, 66):
        pass


def roads(t: Town):
    t.pave(59, 93, 65, 115, "street")                 # king's road to the gate
    t.pave(58, 44, 66, 92, "street")                  # main street
    t.pave(12, 50, 112, 52, "street")                 # merchant cross street
    t.pave(19, 55, 21, 89, "cobble")                  # rear lane, west district
    t.pave(34, 54, 90, 80, "plaza")                   # market square
    t.pave(58, 44, 66, 53, "street")
    t.pave(58, 81, 66, 89, "street")


def fountain(t: Town, cx, cz):
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if d <= 3.2:
                t.bp.blocks[(x, G, z)] = M("water[level=0]")
                t.used.add((x, z))
            elif d <= 4.4:
                t.bp.blocks[(x, G, z)] = M("stone_bricks")
                t.put(x, F, z, M("stone_bricks") if (x + z) % 2 else M("stone_brick_slab[type=bottom,waterlogged=false]"))
    t.fill(cx, G, cz, cx, G, cz, M("stone_bricks"))
    for y in range(F, F + 4):
        t.put(cx, y, cz, M("stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"))
    t.put(cx, F + 4, cz, M("chiseled_stone_bricks"))
    t.put(cx, F + 5, cz, M("stone_brick_slab[type=bottom,waterlogged=false]"))
    t.put(cx, F + 6, cz, lantern_floor())
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        t.put(cx + dx, G, cz + dz, M("water[level=0]"))
        t.put(cx + dx, F + 1, cz + dz, AIR)


def well(t: Town, cx, cz):
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx or dz:
                t.put(cx + dx, F, cz + dz, M("cobblestone"))
                t.bp.blocks[(cx + dx, G, cz + dz)] = M("cobblestone")
    t.bp.blocks[(cx, G, cz)] = M("water[level=0]")
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        for y in (F + 1, F + 2):
            t.put(cx + dx, y, cz + dz, M(FENCE))
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            t.put(cx + dx, F + 3, cz + dz, M("spruce_slab[type=bottom,waterlogged=false]"))
    t.put(cx, F + 2, cz, M("chain[axis=y,waterlogged=false]"))
    t.put(cx, F + 1, cz, M("lantern[hanging=true,waterlogged=false]"))


def market(t: Town):
    pal = [("red", "white"), ("blue", "white"), ("yellow", "white"), ("green", "white"), ("orange", "white"), ("purple", "white")]
    goods = [["barrel", "hay_block", "melon", "pumpkin", "barrel"], ["barrel", "barrel", "hay_block", "barrel", "barrel"],
             ["melon", "pumpkin", "melon", "hay_block", "melon"], ["barrel", "barrel", "barrel", "barrel", "barrel"]]
    i = 0
    for z, facing in ((57, "s"), (75, "n")):
        for x in (37, 44, 51, 69, 76, 83):
            t.stall(x, z, 5, 3, pal[i % 6], goods[i % 4], facing)
            i += 1
    # notice pillar and horse trough
    for y in range(F, F + 3):
        t.put(45, y, 67, M("stone_bricks"))
    t.put(45, F + 3, 67, M("lantern[hanging=false,waterlogged=false]"))
    t.put(82, F, 67, M("spruce_slab[type=bottom,waterlogged=false]"))
    t.put(83, F, 67, M("spruce_slab[type=bottom,waterlogged=false]"))
    t.put(80, F, 66, M("hay_block[axis=x]"))
    t.put(81, F, 66, M("hay_block[axis=x]"))


def row_x(t: Town, x_from, x_to, z0, z1, door_side, seed, widths=(7, 8, 9, 10), storeys=(2, 2, 3, 2), gap=1):
    """Houses side by side along x, depth z0..z1, doors on door_side ('s' or 'n')."""
    x = x_from
    n = 0
    while True:
        w = widths[int(rnd(x, z0, seed, 1) * len(widths))]
        if x + w - 1 > x_to:
            w = x_to - x + 1
            if w < 6:
                break
        st = storeys[int(rnd(x, z0, seed, 2) * len(storeys))]
        pi = int(rnd(x, z0, seed, 3) * 5)
        t.house(x, z0, x + w - 1, z1, door_side, st, plaster=PLASTERS[pi], roof=ROOFS_H[int(rnd(x, z0, seed, 4) * 5)],
                axis="x")
        x += w + gap
        n += 1
        if x > x_to:
            break


def row_z(t: Town, z_from, z_to, x0, x1, door_side, seed, depths=(7, 8, 9), storeys=(2, 2, 3), gap=1):
    z = z_from
    while True:
        d = depths[int(rnd(z, x0, seed, 1) * len(depths))]
        if z + d - 1 > z_to:
            d = z_to - z + 1
            if d < 6:
                break
        st = storeys[int(rnd(z, x0, seed, 2) * len(storeys))]
        pi = int(rnd(z, x0, seed, 3) * 5)
        t.house(x0, z, x1, z + d - 1, door_side, st, plaster=PLASTERS[pi], roof=ROOFS_H[int(rnd(z, x0, seed, 4) * 5)],
                axis="z")
        z += d + gap
        if z > z_to:
            break


def guild_hall(t: Town):
    """Free Guild, Blumund branch: a stone-footed timber hall on the square's east side."""
    x0, x1, z0, z1 = 93, 112, 56, 80
    top_wall = F + 8                  # wall tops (beam layer)
    pl = M("calcite")
    pane = M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]")
    # floor
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            t.put(x, G, z, M("stone_bricks") if (x + z) % 5 else M("polished_andesite"))
    # walls
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)):
                continue
            corner = x in (x0, x1) and z in (z0, z1)
            on_x = z in (z0, z1)
            along, lo = (x, x0) if on_x else (z, z0)
            post = corner or (along - lo) % 4 == 0
            for y in range(F, top_wall + 1):
                if y <= F + 1:
                    s = M("stone_bricks") if not corner else log("stripped_dark_oak_log")
                elif post:
                    s = log("dark_oak_log")
                elif y == top_wall:
                    s = log("stripped_dark_oak_log", "x" if on_x else "z")
                elif y == F + 5 and x != x0 or y == F + 5 and z not in range(z0, z1 + 1):
                    s = log("stripped_dark_oak_log", "x" if on_x else "z")
                else:
                    s = pl
                t.put(x, y, z, s)
    # tall windows between the posts (not behind the notice boards), shutters outside
    boards = ((58, 64), (72, 78))
    for z in range(z0, z1 + 1):
        if (z - z0) % 4 in (1, 2, 3) and z not in (z0, z1):
            if any(a <= z <= b for a, b in boards):
                continue
            if x0 and (z - z0) % 4 == 2:
                for y in (F + 3, F + 4):
                    t.put(x0, y, z, pane)
                    t.put(x1, y, z, pane)
    for x in range(x0 + 1, x1):
        if (x - x0) % 4 == 2:
            for y in (F + 3, F + 4):
                t.put(x, y, z0, pane)
                t.put(x, y, z1, pane)
    # double door on the west side (z 67-68), porch steps and banners
    for z, hinge in ((67, "left"), (68, "right")):
        t.put(x0, F, z, door("dark_oak", "east", "lower", hinge))
        t.put(x0, F + 1, z, door("dark_oak", "east", "upper", hinge))
        t.put(x0 - 1, G, z, M("stone_bricks"))
        t.put(x0 - 2, G, z, M("stone_bricks"))
    for y in (F + 2, F + 3):
        for z in (67, 68):
            t.put(x0, y, z, M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]") if y == F + 3 else pl)
    for z in range(65, 71):
        t.put(x0 - 1, G, z, M("stone_bricks"))
        t.put(x0 - 2, G, z, M("stone_bricks"))
    for z in (65, 70):
        for y in range(F, F + 4):
            t.put(x0 - 2, y, z, log("dark_oak_log"))
        t.put(x0 - 2, F + 4, z, M("lantern[hanging=false,waterlogged=false]"))
    for z in range(65, 71):
        t.put(x0 - 2, F + 4, z, M("dark_oak_slab[type=bottom,waterlogged=false]") if z not in (65, 70) else M("lantern[hanging=false,waterlogged=false]"))
    for z in (63, 72):
        t.put(x0 - 1, F + 6, z, wall_banner("blue", "west"))
    # roof: gable, ridge along z, slate
    t.gable(x0, z0, x1, z1, top_wall + 1, "slate", "z", pl)
    # interior: open to the roof; mezzanine (office) over x 104..111
    for x in range(104, 112):
        for z in range(z0 + 1, z1):
            t.put(x, F + 5, z, M("spruce_planks"))
    for z in range(z0 + 1, z1, 4):
        for y in range(F, F + 5):
            t.put(104, y, z, log("dark_oak_log"))
    for z in range(z0 + 3, z1 - 1):
        if z not in (57, 58, 59):
            t.put(104, F + 6, z, M(FENCE))
    # stairs up along the north wall (z 57), climbing east to the mezzanine
    for i in range(6):
        x = 98 + i
        t.fill(x, F, 57, x, F + i - 1, 57, M("stone_bricks")) if i else None
        t.put(x, F + i, 57, stair("spruce", "east"))
    # notice boards (inside face of the west wall) and the reception counter
    for (zb0, zb1) in boards:
        for z in range(zb0 - 1, zb1 + 2):
            for y in range(F, F + 5):
                edge = z in (zb0 - 1, zb1 + 1) or y in (F, F + 4)
                t.put(x0 + 1, y, z, log("stripped_dark_oak_log", "y" if z in (zb0 - 1, zb1 + 1) else "z") if edge else M("birch_planks"))
        for z in range(zb0, zb1 + 1):
            for y in (F + 1, F + 2, F + 3):
                r = rnd(z, y, 5, 9)
                if r > 0.62:
                    t.put(x0 + 2, y, z, wall_banner(("white", "light_gray", "white", "yellow")[int(r * 40) % 4], "east"))
    t.points["quest_board"] = (x0 + 1, F, 61)
    t.points["bounty_board"] = (x0 + 1, F, 75)
    # counter
    for z in range(60, 79):
        t.put(102, F, z, M("dark_oak_planks"))
        t.put(102, F + 1, z, M("dark_oak_slab[type=bottom,waterlogged=false]"))
    t.put(102, F, 79, fence_gate("dark_oak", "east"))  # staff gate in the counter's south end
    for z in (62, 66, 72, 75):
        t.put(103, F, z, M("lectern[facing=west,has_book=false,powered=false]"))
    for z in (64, 70, 74):
        t.put(103, F, z, M("cartography_table"))
        t.put(103, F + 1, z, lantern_floor())
    t.points["counter_customer"] = (101, F, 68)
    t.points["counter_staff"] = (103, F, 68)
    # archive: bookshelves along the east wall and barrels
    for z in range(z0 + 2, z1 - 4):
        for y in range(F, F + 4):
            t.put(x1 - 1, y, z, M("bookshelf"))
    for z in range(z0 + 2, z1 - 4, 3):
        t.put(x1 - 2, F, z, M("barrel[facing=west,open=false]"))
    # tables and benches (customer area and tavern nook)
    def table(x, z):
        t.put(x, F, z, M(FENCE))
        t.put(x, F + 1, z, M("spruce_pressure_plate[powered=false]"))
        for dx, dz, f in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
            t.put(x + dx, F, z + dz, stair("spruce", f))
    for x, z in ((97, 61), (97, 66), (97, 71), (97, 76)):
        pass
    for x, z in ((98, 62), (98, 73), (99, 78), (107, 73), (110, 77), (107, 77)):
        table(x, z)
    # mezzanine office: master's desk, shelves, map table, rug
    for z in range(z0 + 2, z1 - 1):
        for y in (F + 6, F + 7, F + 8):
            if z in range(58, 74):
                t.put(x1 - 1, y, z, M("bookshelf"))
    t.put(109, F + 6, 61, M("dark_oak_planks"))
    t.put(109, F + 6, 62, M("dark_oak_planks"))
    t.put(109, F + 7, 61, M("lectern[facing=west,has_book=false,powered=false]"))
    t.put(108, F + 6, 61, stair("dark_oak", "east"))
    t.put(109, F + 7, 62, lantern_floor())
    t.points["master_desk"] = (109, F + 6, 61)
    t.put(107, F + 6, 68, M("cartography_table"))
    for x in range(105, 111):
        for z in range(64, 72):
            if (x, z) not in ((107, 68),):
                t.put(x, F + 6, z, M("blue_carpet" if (x in (105, 110) or z in (64, 71)) else "light_blue_carpet"))
    t.put(108, F + 6, 76, bed("blue", "north", "foot"))
    t.put(108, F + 6, 75, bed("blue", "north", "head"))
    # chandeliers hung from the ridge (x 102-103)
    for z in (61, 67, 73, 78):
        for y in range(F + 14, F + 18):
            t.put(102, y, z, M("chain[axis=y,waterlogged=false]"))
        t.put(102, F + 13, z, lantern_hung())
    for z in (61, 68, 75):
        for y in range(F + 10, F + 12):
            pass
    # banners and signboard over the door
    for z in (65, 70):
        t.put(x0 - 2, F + 5, z, M("blue_banner[rotation=4]"))
    t.points["door"] = (x0 - 1, F, 67)
    t.points["hall_centre"] = (98, F, 68)


def royal_castle(t: Town):
    # ward wall and gatehouse
    t.rampart(30, 46, 94, 48, WALL_H, "s")
    arch(t, 59, 65, 46, 48, 5)
    for tx in (51, 68):
        t.tower(tx, 44, tx + 6, 50, WALL_H + 4, "slate")
    t.rampart(30, 7, 32, 45, WALL_H, "w")
    t.rampart(92, 7, 94, 45, WALL_H, "e")
    for x, z in ((27, 43), (92, 43), (27, 7), (92, 7)):
        t.tower(x, z, x + 6, z + 6, WALL_H + 7, "slate", flags=lambda top, x=x, z=z: (x + 3, top + 1, z + 3, banner("red")))
    # keep: hollow ring x 50..74, z 10..28
    kx0, kx1, kz0, kz1 = 50, 74, 10, 28
    top = F + 13
    for x in range(kx0, kx1 + 1):
        for z in range(kz0, kz1 + 1):
            t.put(x, G, z, M("polished_andesite") if (x + z) % 4 else M("stone_bricks"))
            edge = x in (kx0, kx1) or z in (kz0, kz1)
            for y in range(F, top + 1):
                if edge:
                    t.stone(x, y, z)
                else:
                    t.put(x, y, z, AIR)
            if not edge:
                t.put(x, F + 12, z, M("stone_bricks"))
                t.put(x, F + 6, z, M("spruce_planks"))
    t.battlements(kx0, kz0, kx1, kz1, top + 1)
    # windows: slits on the ground floor, taller upstairs
    for x in range(kx0 + 3, kx1 - 2, 4):
        for z in (kz0, kz1):
            for y in (F + 3, F + 4, F + 8, F + 9):
                if z == kz1 and x in range(58, 67) and y < F + 6:
                    continue
                t.put(x, y, z, M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"))
    for z in range(kz0 + 3, kz1 - 2, 4):
        for x in (kx0, kx1):
            for y in (F + 3, F + 4, F + 8, F + 9):
                t.put(x, y, z, M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"))
    # entrance on the south face (x 60-64), steps down to the courtyard road
    for x in range(60, 65):
        for y in range(F, F + 4):
            t.put(x, y, kz1, AIR)
        t.put(x, F + 4, kz1, M("stone_bricks"))
    t.put(60, F + 3, kz1, stair("stone_brick", "west", "top"))
    t.put(64, F + 3, kz1, stair("stone_brick", "east", "top"))
    for x in (60, 64):
        pass
    for x in range(59, 66):
        t.bp.blocks[(x, G, kz1 + 1)] = M("stone_bricks")
        t.bp.blocks[(x, G, kz1 + 2)] = M("stone_bricks")
    for x in (58, 66):
        for y in range(F, F + 5):
            t.put(x, y, kz1 + 1, log("dark_oak_log"))
        t.put(x, F + 5, kz1 + 1, M("lantern[hanging=false,waterlogged=false]"))
    # throne hall: red carpet aisle, columns, dais and throne, wall banners, chandeliers
    for z in range(kz0 + 6, kz1):
        t.put(62, F, z, M("red_carpet"))
    for x in (61, 63):
        for z in range(kz0 + 6, kz1):
            t.put(x, F, z, M("red_carpet") if x == 61 or x == 63 else M("white_carpet"))
    for x in (56, 68):
        for z in (15, 19, 23):
            for y in range(F, F + 6):
                t.put(x, y, z, M("stone_bricks") if y < F + 5 else M("chiseled_stone_bricks"))
            t.put(x, F + 4, z, M("stone_bricks"))
    for x in range(kx0 + 1, kx1):
        for z in range(kz0 + 1, kz0 + 5):
            t.put(x, F, z, M("polished_andesite"))
    for x in range(56, 69):
        for z in range(kz0 + 1, kz0 + 4):
            t.put(x, F, z, M("stone_bricks"))
            if z == kz0 + 1:
                t.put(x, F + 1, z, M("stone_bricks"))
    t.put(62, F + 1, kz0 + 2, stair("dark_oak", "north"))
    t.put(62, F + 2, kz0 + 1, M("dark_oak_planks"))
    t.put(62, F + 3, kz0 + 1, M("dark_oak_planks"))
    t.put(62, F + 4, kz0 + 1, M("dark_oak_planks"))
    for x in (61, 63):
        t.put(x, F + 1, kz0 + 2, stair("dark_oak", "north"))
    t.points["throne"] = (62, F + 1, kz0 + 2)
    for z in (13, 17, 21, 25):
        t.put(kx0 + 1, F + 3, z, wall_banner("red", "east"))
        t.put(kx1 - 1, F + 3, z, wall_banner("white", "west"))
    for z in (14, 20, 26):
        for x in (59, 65):
            for y in range(F + 3, F + 6):
                t.put(x, y, z, M("chain[axis=y,waterlogged=false]"))
            t.put(x, F + 2, z, lantern_hung())
    # stairs to the council chamber (east wall x=73, climbing north) and furnishings
    for i in range(7):
        z = 26 - i
        t.fill(73, F, z, 73, F + i - 1, z, M("stone_bricks")) if i else None
        t.put(73, F + i, z, stair("stone_brick", "north"))
    for z in range(20, 27):
        t.put(73, F + 6, z, AIR) if z > 20 else None
    for x in range(55, 70):
        t.put(x, F + 7, 19, M("dark_oak_planks"))
    for x in range(56, 69, 2):
        t.put(x, F + 7, 17, stair("dark_oak", "south"))
        t.put(x, F + 7, 21, stair("dark_oak", "north"))
        t.put(x, F + 8, 19, M("candle[candles=1,lit=true,waterlogged=false]")) if x % 4 == 0 else None
    for z in (14, 24):
        t.put(62, F + 11, z, lantern_hung())
    for x in (57, 67):
        for z in (14, 24):
            t.put(x, F + 11, z, lantern_hung())
    # corner towers of the keep
    for x, z in ((45, 6), (72, 6), (45, 26), (72, 26)):
        pass
    for x, z in ((46, 7), (72, 7), (46, 27), (72, 27)):
        t.tower(x, z, x + 5, z + 5, 17, "slate", flags=lambda top, x=x, z=z: (x + 2, top + 1, z + 2, banner("red")))
    # courtyard: road, well, barracks, stable
    t.pave(59, 32, 65, 45, "street")
    t.pave(59, 29, 65, 31, "plaza")
    for z in range(32, 46):
        for x in range(33, 92):
            if t.get(x, G, z) == M("grass_block") and (x + z) % 7 == 0 and not (55 <= x <= 69):
                pass
    well(t, 50, 38)
    t.house(35, 36, 45, 44, "e", 1, plaster="calcite", roof="slate", axis="z")
    t.house(78, 34, 90, 43, "w", 1, plaster="smooth_sandstone", roof="dark", axis="z")
    for x in range(80, 89, 2):
        t.put(x, F, 36, M("hay_block[axis=y]")) if t.get(x, F, 36) == AIR else None
    # garden beds
    for x in range(34, 44):
        for z in (33, 34):
            t.bp.blocks[(x, G, z)] = M("farmland[moisture=7]")
            t.put(x, F, z, M(("poppy", "dandelion", "cornflower", "allium", "oxeye_daisy")[x % 5]))
    for x in (66, 70, 74):
        t.tree(x, 36, "oak", 4, 2)
    t.points["keep_door"] = (62, F, kz1 + 1)


def merchants(t: Town):
    # cross street, north flank (west and east of the castle walls)
    row_x(t, 12, 28, 42, 49, "s", 11, widths=(8, 8), storeys=(2, 3))
    row_x(t, 97, 112, 42, 49, "s", 12, widths=(7, 8), storeys=(2, 3))
    # cross street, south flank: houses facing it and the square frontage
    # south rows between the gate and the square, doors toward the square (north)
    row_x(t, 34, 56, 83, 88, "n", 21, widths=(7, 8), storeys=(2, 3))
    row_x(t, 68, 90, 83, 88, "n", 22, widths=(7, 8), storeys=(2, 3))
    # west district: row A faces the square (east door), row B faces the rear lane
    row_z(t, 54, 88, 23, 32, "e", 31, depths=(8, 9, 10), storeys=(2, 3))
    row_z(t, 54, 88, 11, 18, "e", 32, depths=(8, 9, 10), storeys=(2, 2, 3))
    # east side behind the guild hall
    row_x(t, 93, 112, 83, 88, "n", 41, widths=(9, 10), storeys=(2, 2))
    # shops beside the gate (inside) and a well
    # south-west and south-east: smithy and stables behind the rows


def approach(t: Town):
    """Fields, farmstead, trees, signpost and milestone outside the gate."""
    for (xa, xb) in ((18, 50), (74, 106)):
        for x in range(xa, xb + 1):
            for z in range(98, 112):
                if (x - xa) % 4 == 3:
                    t.bp.blocks[(x, G, z)] = M("water[level=0]")
                else:
                    t.bp.blocks[(x, G, z)] = M("farmland[moisture=7]")
                    t.put(x, F, z, M("wheat[age=%d]" % (5 + int(rnd(x, 0, z, 4) * 3))))
        for x in range(xa - 1, xb + 2):
            for z in (97, 112):
                t.put(x, F, z, M(FENCE))
        for z in range(97, 113):
            for x in (xa - 1, xb + 1):
                t.put(x, F, z, M(FENCE))
    # gaps in the fences next to the road
    for z in (97, 112):
        for x in (50, 51, 74, 73):
            t.put(x, F, z, AIR)
    for z in range(97, 113):
        for x in (51, 73):
            pass
    for z in (96, 104):
        for x in (57, 67):
            t.lamp(x, z, 3, post="spruce_fence")
    t.put(57, F, 108, M(FENCE))
    t.put(57, F + 1, 108, M(FENCE))
    t.put(57, F + 2, 108, M("spruce_slab[type=bottom,waterlogged=false]"))
    t.put(66, F, 106, M("stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"))
    for x, z, k in ((53, 113, "oak"), (70, 114, "birch"), (14, 108, "oak"), (112, 106, "oak"), (6, 96, "birch")):
        t.tree(x, z, k, 5, 2)


def orchards(t: Town):
    for x0, x1 in ((13, 27), (97, 111)):
        for x in range(x0, x1 + 1, 4):
            for z in range(9, 38, 5):
                if t.get(x, F, z) == AIR and (x, z) not in t.used:
                    t.tree(x + (z % 3), z, ("oak", "birch")[(x + z) % 2], 4, 2)
    for x in (34, 88):
        pass


def build(bp):
    t = Town(bp, G)
    bp.town = t
    t.base_ground()
    roads(t)
    fountain(t, CX, 67)
    walls_and_gates(t)
    royal_castle(t)
    guild_hall(t)
    market(t)
    merchants(t)
    approach(t)
    orchards(t)
    # a banner pole and lamps along the main street
    for z in (60, 86):
        for x in (58, 66):
            pass
    t.light(inside)
    t.check_support()
