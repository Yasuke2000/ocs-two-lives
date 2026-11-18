"""Englassia, the royal capital Lura: the Freedom Academy and the Free Guild headquarters inside the city wall.

Lore notes and sources: design/lore/englassia.md. SIZE (128, 60, 112), saved as three z slabs englassia_0..2
(PARTS). Ground layer y 4 (grass and paving, dirt below), you walk at y 5; everything above is air, so the placer
clears forest and hills in the box (clear_above). The city wall runs across the south (z 100-106); the road
arrives from the south (z 107-111) and the arrival point is blueprint (64, 5, 109), facing north at the gate.
Landmark scale, not a whole city: the walled gate (two towers, banners, a 7 wide passage x 61-67), Lura Square
(z 68-98, paved, fountain, market stalls, a townhouse row on the west side), the Free Guild headquarters on the
east side of the square (a 31 x 17 hall with a gable facade to the west, columned portico, golden emblem, red
banners, two wings; reception counter, quest wall, tables and chandeliers inside), and north of the square the
Freedom Academy: a long main hall (x 44-84, z 8-28) with a clock tower over the entrance (x 58-70, spire to
y 56), two classroom wings (x 24-43 and 85-104, z 12-62) round a walled lawn courtyard with a fountain and
four trees (x 44-84, z 29-62), cloister wall with a gate (z 63-65). Styles: stone brick walls, dark oak
timber, oxidised-copper roofs on the Academy, slate roofs on the gate and the Guild. Refined academic city;
the Guild is the sturdy working half. Every spawnable spot inside the plot has block light (checked when this
builds). The exact architecture is our interpretation (canon gives a walled capital with two gates).
"""
from _citylib import AIR, M, Mat, Site
from _dwargon_lib import noise2, rnd

SIZE = (128, 60, 112)
SX, SY, SZ = SIZE
G = 4
F = G + 1
ARRIVAL = (64, F, 109)
PARTS = [0, 40, 80]

STONE = Mat("stone_bricks", "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall")
MOSSY = Mat("mossy_stone_bricks")
CHISEL = Mat("chiseled_stone_bricks")
ANDESITE = Mat("polished_andesite", "polished_andesite_stairs", "polished_andesite_slab")
COPPER = Mat("waxed_oxidized_cut_copper", "waxed_oxidized_cut_copper_stairs", "waxed_oxidized_cut_copper_slab")
SLATE = Mat("deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_slab", "deepslate_tile_wall")
DARK = Mat("dark_oak_planks", "dark_oak_stairs", "dark_oak_slab")
LOG = Mat("dark_oak_log")
PLASTER = Mat("white_terracotta")
QUARTZ = Mat("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab")
OAK = Mat("oak_planks", "oak_stairs", "oak_slab")
COBBLE = Mat("cobblestone", "cobblestone_stairs", "cobblestone_slab", "cobblestone_wall")


def inplot(x, z) -> bool:
    return 3 <= x < SX - 3 and 3 <= z < 112 - 1


# --- ground and paving ---------------------------------------------------------------------------------


def pave(s, x0, z0, x1, z1, fn):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            s.bp.blocks[(x, G, z)] = fn(x, z)


def paving(x, z):
    q = rnd(x, 0, z, 5)
    return M("stone_bricks") if q < 0.55 else M("polished_andesite") if q < 0.85 else M("cobblestone")


def ground(s):
    def top(x, z):
        n = noise2(x, z, 7, 3)
        return M("coarse_dirt") if n > 0.85 else M("grass_block")
    s.ground(top)
    # Lura Square and the avenue
    pave(s, 38, 68, 90, 98, paving)
    pave(s, 60, 99, 68, 106, paving)
    for x in range(38, 91):
        for z in (68, 98):
            s.bp.blocks[(x, G, z)] = M("chiseled_stone_bricks")
    # the road outside the gate, a plain dirt road
    for z in range(107, SZ):
        for x in range(62, 67):
            s.bp.blocks[(x, G, z)] = M("dirt_path")
    # academy: forecourt lawn stays grass; paths of polished andesite
    for z in range(31, 63):
        for x in range(62, 67):
            s.bp.blocks[(x, G, z)] = M("polished_andesite")
    for x in range(44, 85):
        for z in range(44, 49):
            s.bp.blocks[(x, G, z)] = M("polished_andesite")
    for z in range(63, 68):
        for x in range(60, 69):
            s.bp.blocks[(x, G, z)] = M("polished_andesite")
    # fountain forecourt paving
    s.disc(64, G, 46, 7, "stone_bricks")
    # road from the square east to the Guild steps, and the west row houses' yard path
    pave(s, 86, 78, 91, 86, paving)
    pave(s, 28, 66, 37, 99, lambda x, z: M("gravel") if rnd(x, 0, z, 8) < 0.5 else M("coarse_dirt"))


# --- city wall and gate ---------------------------------------------------------------------------------


def city_wall(s):
    WZ0, WZ1 = 101, 103
    for x in range(SX):
        if 52 <= x <= 76:
            continue
        for z in range(WZ0, WZ1 + 1):
            for y in range(F, F + 9):
                q = rnd(x, y, z, 21)
                s.put(x, y, z, "mossy_stone_bricks" if q < 0.12 else "cracked_stone_bricks" if q < 0.2 else "stone_bricks")
        for z in (WZ0, WZ1):
            if x % 2 == 0:
                s.put(x, F + 9, z, "stone_bricks")
        s.put(x, F + 9, 102, "stone_brick_slab[type=bottom,waterlogged=false]")
    # a buttress every 12 blocks on the outer face and a walkway ladder stair
    for x in range(6, SX, 12):
        if 50 <= x <= 78:
            continue
        for z in (WZ1 + 1, WZ1 + 2):
            for y in range(F, F + (9 if z == WZ1 + 1 else 6)):
                s.put(x, y, z, "stone_bricks")
        s.fill(x - 1, F, WZ1 + 1, x - 1, F + 5, WZ1 + 1, "stone_bricks")
        s.fill(x + 1, F, WZ1 + 1, x + 1, F + 5, WZ1 + 1, "stone_bricks")
    # inner wall lamps
    for x in range(10, SX, 16):
        if 48 <= x <= 80:
            continue
        s.lamp(x, 100, 2, post="stone_brick_wall", y0=F)


def gate(s):
    for (tx0, tx1) in ((52, 60), (68, 76)):
        tz0, tz1 = 98, 106
        # shell with arrow slits, floor in the ground layer
        s.box_walls(tx0, tz0, tx1, tz1, F, 17, STONE, STONE, bay=3, glass="iron_bars", rows=((7, 9),),
                    base_h=2, base=MOSSY)
        s.fill(tx0 + 1, F + 17, tz0 + 1, tx1 - 1, F + 17, tz1 - 1, "stone_bricks")  # cap floor
        s.rim(tx0 - 1, tz0 - 1, tx1 + 1, tz1 + 1, F + 17, "stone_bricks")
        s.crenels(tx0 - 1, tz0 - 1, tx1 + 1, tz1 + 1, F + 18, STONE)
        s.fill(tx0 + 1, F + 18, tz0 + 1, tx1 - 1, F + 18, tz1 - 1, "air")
        cx = (tx0 + tx1) // 2
        s.hip(tx0 + 1, tz0 + 1, tx1 - 1, tz1 - 1, F + 18, SLATE, over=1)
    # the passage and its arch
    s.air(61, F, 98, 67, F + 8, 106)
    for z in range(98, 107):
        s.stair(61, F + 8, z, "e", STONE, half="top")
        s.stair(67, F + 8, z, "w", STONE, half="top")
    s.fill(60, F, 98, 60, F + 8, 106, "stone_bricks")
    s.fill(68, F, 98, 68, F + 8, 106, "stone_bricks")
    for z in (99, 105):
        s.fill(61, F + 9, z, 67, F + 9, z, "stone_bricks")
    s.fill(61, F + 9, 98, 67, F + 16, 106, "stone_bricks")
    s.air(62, F + 9, 100, 66, F + 11, 104)  # gatehouse chamber above the passage, with the portcullis slot
    for z in (100, 104):
        for x in range(62, 67):
            s.put(x, F + 8, z, "iron_bars[north=false,south=false,east=true,west=true,waterlogged=false]")
    # hanging lanterns inside the passage
    for z in (99, 102, 105):
        for x in (63, 65):
            pass
        s.put(64, F + 7, z, "chain[axis=y,waterlogged=false]")
        s.lantern(64, F + 6, z, hanging=True)
    # banners on the towers (inner and outer faces), blue
    for tx in (56, 72):
        s.wall_banner(tx, F + 11, 97, "n", "blue")
        s.wall_banner(tx, F + 11, 107, "s", "blue")
    for tx in (60, 68):
        s.wall_banner(tx - 1 if tx == 60 else tx + 1, F + 12, 107, "s", "light_blue")
    # city name on the lintel: a gold plaque course
    s.fill(62, F + 14, 107, 66, F + 14, 107, "chiseled_stone_bricks")


# --- houses and stalls -----------------------------------------------------------------------------------


def townhouse(s, x0, z0, x1, z1, floors=2, door="e", axis=None, roof=SLATE, beam=LOG, plaster=PLASTER, pitch=4):
    h = pitch * floors
    s.box_walls(x0, z0, x1, z1, F, h, plaster, beam, bay=4, glass="glass_pane", rows=tuple((1 + pitch * k, 2 + pitch * k) for k in range(floors)),
                base_h=1, base=STONE)
    # floors
    s.fill(x0 + 1, G, z0 + 1, x1 - 1, G, z1 - 1, "spruce_planks")
    for k in range(1, floors):
        y = F + pitch * k - 1
        s.fill(x0, y, z0, x1, y, z1, "dark_oak_planks")
        s.rim(x0, z0, x1, z1, y, "dark_oak_log")
    ax = axis or ("x" if (x1 - x0) >= (z1 - z0) else "z")
    ridge = s.gable(x0, z0, x1, z1, F + h, roof, axis=ax, wall=plaster, cap=roof)
    # door
    dx, dz = {"e": (x1, (z0 + z1) // 2), "w": (x0, (z0 + z1) // 2), "n": ((x0 + x1) // 2, z0), "s": ((x0 + x1) // 2, z1)}[door]
    s.air(dx, F, dz, dx, F + 1, dz)
    s.door(dx, F, dz, door, "dark_oak_door")
    ox, oz = {"e": (1, 0), "w": (-1, 0), "n": (0, -1), "s": (0, 1)}[door]
    # lights inside (hanging from the roof timber is overkill: lanterns on a table)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for k in range(floors):
        s.put(cx, F + pitch * k, cz, "oak_fence")
        s.lantern(cx, F + pitch * k + 1, cz)
    return dx, dz


def stall(s, x, z, colour="red"):
    for dx in (0, 4):
        for dz in (0, 3):
            s.fill(x + dx, F, z + dz, x + dx, F + 2, z + dz, "spruce_fence")
    for dx in range(-1, 6):
        for dz in range(-1, 5):
            s.put(x + dx, F + 3, z + dz, f"{colour if (dx + dz) % 2 == 0 else 'white'}_wool")
    for dx in range(1, 4):
        s.put(x + dx, F, z, "barrel[facing=up,open=false]")
    s.put(x + 2, F + 1, z, "oak_pressure_plate")
    s.put(x + 2, F + 2, z + 3, "spruce_fence")


def west_row(s):
    z = 67
    for i, (zz0, zz1, floors) in enumerate(((67, 75, 3), (77, 85, 2), (87, 93, 2), (95, 99, 2))):
        townhouse(s, 24 + (i % 2) * 2, zz0, 36, zz1, floors=floors, door="e")
    # a tavern sign pole in front of the second house
    s.fill(38, F, 80, 38, F + 3, 80, "oak_fence")
    for zz in (69, 82, 96):
        s.lamp(39, zz, 3)


def square(s):
    # centre: fountain, statue pedestal (the guild's founders, we say) and benches
    cx, cz = 64, 83
    s.disc(cx, G, cz, 6, "polished_andesite")
    s.disc(cx, G, cz, 6, "stone_bricks", inner=4.5)
    s.disc(cx, F, cz, 5, "stone_brick_wall", inner=3.5)
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if (x - cx) ** 2 + (z - cz) ** 2 <= 3.5 ** 2:
                s.put(x, G, z, "water[level=0]")
    s.fill(cx, F, cz, cx, F + 5, cz, "stone_bricks")
    s.put(cx, F + 6, cz, "chiseled_stone_bricks")
    s.put(cx, F + 7, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        s.stair(cx + dx, F + 4, cz + dz, {(-1, 0): "w", (1, 0): "e", (0, -1): "n", (0, 1): "s"}[(dx, dz)], STONE)
    # benches round the fountain ring
    for dx, dz, f in ((-8, 0, "e"), (8, 0, "w"), (0, -8, "s"), (0, 8, "n")):
        s.stair(cx + dx, F, cz + dz, f, DARK)
        s.stair(cx + dx + (0 if dx else 1), F, cz + dz + (1 if dx else 0), f, DARK)
    # market stalls
    stall(s, 41, 72, "red")
    stall(s, 41, 90, "blue")
    # lamp posts along the avenue
    for z in (70, 76, 90, 96):
        s.lamp(58, z, 3)
        s.lamp(70, z, 3)
    # planters (rose beds) at the avenue mouth
    for x in (47, 52, 76, 81):
        for dx in range(2):
            s.put(x + dx, F - 1, 96, "grass_block")
            s.put(x + dx, F, 96, "rose_bush[half=lower]")
            s.put(x + dx, F + 1, 96, "rose_bush[half=upper]")


# --- the Free Guild -------------------------------------------------------------------------------------


def guild(s):
    GX0, GX1, GZ0, GZ1 = 92, 122, 74, 90
    # wings
    for (z0, z1) in ((66, 73), (91, 97)):
        s.box_walls(GX0, z0, 114, z1, F, 12, STONE, LOG, bay=4, glass="glass_pane", rows=((2, 4), (8, 10)), base_h=2, base=MOSSY)
        s.fill(GX0 + 1, G, z0 + 1, 113, G, z1 - 1, "dark_oak_planks")
        s.fill(GX0, F + 5, z0, 114, F + 5, z1, "dark_oak_planks")
        s.hip(GX0, z0, 114, z1, F + 12, SLATE, over=1)
        s.air(GX0 + 1, F + 6, z0 + 1, 113, F + 11, z1 - 1)
    # the hall
    s.box_walls(GX0, GZ0, GX1, GZ1, F, 14, STONE, LOG, bay=5, glass="glass_pane", rows=((3, 6), (9, 11)), base_h=2, base=MOSSY)
    s.rim(GX0, GZ0, GX1, GZ1, F + 7, "dark_oak_log")
    s.fill(GX0 + 1, G, GZ0 + 1, GX1 - 1, G, GZ1 - 1, "polished_deepslate")
    s.gable(GX0, GZ0, GX1, GZ1, F + 14, SLATE, axis="x", wall=STONE, cap=DARK, over=1)
    # open interior
    s.air(GX0 + 1, F, GZ0 + 1, GX1 - 1, F + 13, GZ1 - 1)
    s.fill(93, G, 75, 121, G, 89, "polished_deepslate")
    for x in range(94, 122, 4):
        for z in range(75, 90, 2):
            s.put(x, G, z, "dark_oak_planks")
    # the wings open into the hall by wide arches; carve through the shared wall
    s.air(GX0 + 8, F, GZ0, GX0 + 12, F + 5, GZ0)
    s.air(GX0 + 8, F, GZ1, GX0 + 12, F + 5, GZ1)
    # the portico
    for z in (77, 79, 85, 87):
        s.column(87, z, F, F + 8, STONE, base=CHISEL, cap=CHISEL, pillar="stone_bricks")
        s.put(87, F, z, "chiseled_stone_bricks")
    s.fill(87, F + 9, 76, 91, F + 9, 88, "stone_bricks")
    s.rim(87, 76, 91, 88, F + 10, "chiseled_stone_bricks")
    for z in range(76, 89):
        s.put(87, F + 11, z, "stone_brick_wall")
    for x in range(88, 92):
        s.put(x, F + 11, 76, "stone_brick_wall")
        s.put(x, F + 11, 88, "stone_brick_wall")
    # great doors
    s.air(92, F, 80, 92, F + 6, 84)
    for z in (80, 84):
        s.put(92, F + 7, z, "chiseled_stone_bricks")
    s.fill(92, F + 7, 80, 92, F + 7, 84, "chiseled_stone_bricks")
    # steps from the square
    # emblem on the gable wall: a gold ring with a white heart
    for dy in range(-4, 5):
        for dz in range(-4, 5):
            d = (dy * dy + dz * dz) ** 0.5
            if d <= 3.6:
                s.put(92, F + 18 + dy, 82 + dz, "gold_block" if d > 2.4 else "white_concrete" if d > 1.2 else "orange_concrete")
    # red banners on the facade pillars
    for z in (76, 88):
        s.wall_banner(91, F + 4, z, "w", "red")
    for z in (78, 86):
        s.wall_banner(91, F + 3, z, "w", "red")
    for z in (71, 93):
        s.wall_banner(91, F + 6, z, "w", "red")
    # inside: reception counter, quest wall, long tables, chandeliers
    for z in range(77, 88):
        s.put(100, F, z, "polished_blackstone")
        s.put(100, F + 1, z, "dark_oak_slab[type=bottom,waterlogged=false]")
    s.air(100, F, 82, 100, F + 1, 82)
    for x in range(96, 119):
        for y in (F, F + 1, F + 2):
            s.put(x, y, 75, "bookshelf" if (x % 3) else "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
    for z in (78, 86):
        for x in range(106, 118):
            s.put(x, F + 1, z, "dark_oak_slab[type=bottom,waterlogged=false]")
            if x % 3 == 0:
                s.put(x, F, z, "dark_oak_fence")
        for x in range(106, 118):
            s.stair(x, F, z - 1, "s", DARK)
            s.stair(x, F, z + 1, "n", DARK)
    for x in (101, 108, 115):
        s.fill(x, F + 12, 75, x, F + 12, 89, "dark_oak_log[axis=z]")
        for z in (78, 82, 86):
            s.chandelier(x, F + 12, z, drop=3)
    # banners inside the east wall and red carpet down the middle
    for x in range(101, 121):
        s.put(x, F, 82, "red_carpet")
    for z in (78, 86):
        s.wall_banner(121, F + 5, z, "w", "red")
    # outside the facade: a notice board and two lamps
    for z in (74, 90):
        s.lamp(88, z, 3, post="stone_brick_wall")
    # chimneys (smoking) on the wings
    for (x, z) in ((100, 70), (100, 94)):
        s.fill(x, F + 12, z, x, F + 17, z, "bricks")


# --- the Freedom Academy ------------------------------------------------------------------------------------


def classroom(s, x0, z0, x1, z1):
    """Desks in rows inside a wing: oak slab desks with stair chairs, a lectern at the far end."""
    for x in range(x0 + 2, x1 - 1, 3):
        for z in range(z0 + 3, z1 - 2, 4):
            s.put(x, F, z, "oak_fence")
            s.put(x, F + 1, z, "oak_pressure_plate")
            s.stair(x, F, z + 1, "n", OAK)


def wing(s, x0, z0, x1, z1, side):
    s.box_walls(x0, z0, x1, z1, F, 12, STONE, STONE, bay=4, glass="glass_pane", rows=((2, 4), (8, 10)), base_h=2, base=MOSSY,
                sill=CHISEL)
    s.rim(x0, z0, x1, z1, F + 6, "chiseled_stone_bricks")
    s.fill(x0 + 1, G, z0 + 1, x1 - 1, G, z1 - 1, "polished_andesite")
    s.fill(x0, F + 5, z0, x1, F + 5, z1, "dark_oak_planks")
    s.fill(x0, F + 5, z0, x1, F + 5, z1, "dark_oak_planks")
    s.air(x0 + 1, F, z0 + 1, x1 - 1, F + 4, z1 - 1)
    s.air(x0 + 1, F + 6, z0 + 1, x1 - 1, F + 11, z1 - 1)
    # pilasters on the courtyard face
    face_x = x1 if side == "w" else x0
    for z in range(z0 + 4, z1, 4):
        for y in range(F, F + 12):
            s.put(face_x + (1 if side == "w" else -1), y, z, "stone_bricks")
        s.put(face_x + (1 if side == "w" else -1), F + 12, z, "chiseled_stone_bricks")
    s.gable(x0, z0, x1, z1, F + 12, COPPER, axis="z", wall=STONE, cap=COPPER, over=1)
    # door to the courtyard
    door_f = "e" if side == "w" else "w"
    dz = 46
    s.air(face_x, F, dz - 1, face_x, F + 3, dz + 1)
    for z in (dz - 1, dz + 1):
        s.door(face_x, F, z, door_f, "dark_oak_door", hinge="left" if z == dz - 1 else "right")
    s.fill(face_x, F + 4, dz - 1, face_x, F + 4, dz + 1, "chiseled_stone_bricks")
    # a stair to the upper floor along the north inner wall
    sx = x0 + 2
    s.air(sx, F + 5, z0 + 2, sx + 1, F + 5, z0 + 7)
    s.staircase(sx, F, z0 + 2, 6, axis="z", direction=1, width=2, m=OAK, base_y=G + 1)
    # desks, upstairs a reading room with shelves along the outer wall
    classroom(s, x0 + 4, z0 + 10, x1 - 1, z1 - 1)
    for z in range(z0 + 10, z1 - 1, 2):
        ox = x0 + 1 if side == "w" else x1 - 1
        for y in (F + 6, F + 7, F + 8):
            s.put(ox, y, z, "bookshelf")
    # chandeliers
    for z in range(z0 + 6, z1, 8):
        s.chandelier((x0 + x1) // 2, F + 5, z, drop=1)


def academy(s):
    # wings first, then the hall over their joins
    wing(s, 24, 12, 43, 62, "w")
    wing(s, 85, 12, 104, 62, "e")
    # the main hall
    HX0, HX1, HZ0, HZ1 = 44, 84, 8, 28
    s.box_walls(HX0, HZ0, HX1, HZ1, F, 13, STONE, STONE, bay=5, glass="glass_pane", rows=((3, 9),), base_h=2, base=MOSSY,
                sill=CHISEL)
    s.rim(HX0, HZ0, HX1, HZ1, F + 13, "chiseled_stone_bricks")
    s.fill(HX0 + 1, G, HZ0 + 1, HX1 - 1, G, HZ1 - 1, "polished_andesite")
    s.gable(HX0, HZ0, HX1, HZ1, F + 13, COPPER, axis="x", wall=STONE, cap=COPPER, over=1)
    s.air(HX0 + 1, F, HZ0 + 1, HX1 - 1, F + 12, HZ1 - 1)
    # open the hall into the wings, at ground level, through the shared end walls
    s.air(44, F, 20, 44, F + 4, 24)
    s.air(84, F, 20, 84, F + 4, 24)
    # tower: hollow shaft from the ground over the entrance bay
    TX0, TX1, TZ0, TZ1 = 58, 70, 18, 30
    s.air(TX0, F, TZ0, TX1, F + 13, TZ1)
    s.box_walls(TX0, TZ0, TX1, TZ1, F, 34, STONE, STONE, bay=6, glass="iron_bars", rows=((26, 29),), base_h=3, base=MOSSY)
    s.rim(TX0, TZ0, TX1, TZ1, F + 20, "chiseled_stone_bricks")
    s.rim(TX0, TZ0, TX1, TZ1, F + 33, "chiseled_stone_bricks")
    s.rim(TX0 - 1, TZ0 - 1, TX1 + 1, TZ1 + 1, F + 34, "stone_bricks")
    # belfry: floor, four open arches, bell
    s.fill(TX0, F + 34, TZ0, TX1, F + 34, TZ1, "stone_bricks")
    s.rim(TX0 - 1, TZ0 - 1, TX1 + 1, TZ1 + 1, F + 34, "stone_bricks")
    s.box_walls(TX0, TZ0, TX1, TZ1, F + 35, 6, STONE, STONE, bay=12, glass="iron_bars", rows=((1, 4),))
    s.rim(TX0 - 1, TZ0 - 1, TX1 + 1, TZ1 + 1, F + 41, "chiseled_stone_bricks")
    s.fill(TX0, F + 41, TZ0, TX1, F + 41, TZ1, "stone_bricks")
    s.put(64, F + 40, 24, "bell[facing=north,attachment=ceiling]")
    s.hip(TX0, TZ0, TX1, TZ1, F + 42, COPPER, over=1)
    for y in range(F + 49, F + 53):
        s.put(64, y, 24, "lightning_rod[facing=up,powered=false,waterlogged=false]" if y == F + 52 else "gold_block")
    # clock faces
    for (px, pz, f) in ((64, TZ1 + 1, "s"), (64, TZ0 - 1, "n")):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 5:
                    s.put(64 + dx, F + 27 + dy, pz, "white_concrete" if (dx, dy) not in ((0, 0), (0, 1), (1, 0)) else "black_concrete")
    # entrance: arch through the south wall of the tower, the hall's wall and the porch
    s.air(62, F, TZ1, 66, F + 7, TZ1)
    s.air(62, F, 28, 66, F + 6, 28)
    for x in (62, 66):
        pass
    s.fill(62, F + 8, TZ1, 66, F + 8, TZ1, "chiseled_stone_bricks")
    # grand porch
    for x in (57, 61, 67, 71):
        s.column(x, 36, F, F + 8, STONE, base=CHISEL, cap=CHISEL, pillar="stone_bricks")
        s.put(x, F, 36, "chiseled_stone_bricks")
    s.fill(56, F + 9, 31, 72, F + 9, 36, "stone_bricks")
    s.rim(56, 31, 72, 36, F + 10, "chiseled_stone_bricks")
    s.gable(56, 31, 72, 36, F + 11, STONE, axis="z", wall=STONE, cap=STONE, over=0)
    s.air(57, F, 31, 71, F + 8, 35)
    # emblem of the academy on the porch pediment: copper ring
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                s.put(64 + dx, F + 12 + dy, 36, "waxed_oxidized_copper" if dx * dx + dy * dy > 1 else "gold_block")
    # hall interior: long reading tables, shelf walls, chandeliers
    for z in range(10, 27, 2):
        for y in (F, F + 1, F + 2):
            pass
    for x in range(46, 83, 1):
        for y in (F, F + 1, F + 2, F + 3):
            s.put(x, y, HZ0 + 1, "bookshelf")
    for x in range(48, 82, 2):
        if 58 <= x <= 70:
            continue
    for z in (13, 17, 21):
        for x in range(46, 58):
            s.put(x, F + 1, z, "dark_oak_slab[type=bottom,waterlogged=false]")
            if x % 3 == 0:
                s.put(x, F, z, "dark_oak_fence")
        for x in range(71, 83):
            s.put(x, F + 1, z, "dark_oak_slab[type=bottom,waterlogged=false]")
            if x % 3 == 0:
                s.put(x, F, z, "dark_oak_fence")
    for x in (50, 54, 74, 78):
        s.fill(x, F + 11, 9, x, F + 11, 27, "dark_oak_log[axis=z]")
        for z in (12, 18, 24):
            s.chandelier(x, F + 11, z, drop=2)
    # banners inside the hall and on the courtyard side of the wings
    for x in (48, 52, 76, 80):
        s.wall_banner(x, F + 5, HZ0 + 1, "s", "light_blue")


def courtyard(s):
    # lawn, hedges, cloister wall with the gate, trees, fountain
    # fountain
    cx, cz = 64, 46
    s.disc(cx, F, cz, 4.5, "stone_brick_wall", inner=3.2)
    s.disc(cx, G, cz, 3.2, "water[level=0]")
    s.fill(cx, F, cz, cx, F + 3, cz, "chiseled_stone_bricks")
    s.put(cx, F + 4, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # cloister wall along z 63-64 with a gate gap x 60-68
    for x in range(44, 85):
        if 59 <= x <= 69:
            continue
        for y in range(F, F + 4):
            s.put(x, y, 63, "stone_bricks")
        s.put(x, F + 4, 63, "stone_brick_slab[type=bottom,waterlogged=false]")
        s.put(x, F + 4, 63, "cobblestone_wall") if x % 4 == 0 else None
    for x in (58, 59, 69, 70):
        for z in (62, 63, 64):
            s.fill(x, F, z, x, F + 5, z, "stone_bricks") if x in (59, 69) else None
    for x in (59, 69):
        s.put(x, F + 6, 63, "chiseled_stone_bricks")
        s.lantern(x, F + 7, 63)
    # gate bars
    for x in range(60, 69):
        s.put(x, F + 4, 63, "iron_bars[north=false,south=false,east=true,west=true,waterlogged=false]") if x not in (64,) else None
    s.air(60, F, 63, 68, F + 3, 63)
    # wall banners on the pillars toward the square
    s.wall_banner(59, F + 3, 64, "s", "light_blue")
    s.wall_banner(69, F + 3, 64, "s", "light_blue")
    # hedges either side of the path and four trees
    for z in range(33, 62):
        for x in (60, 68):
            if 44 <= z <= 48:
                continue
            s.put(x, F, z, "oak_leaves[persistent=true,distance=1]")
    for (tx, tz) in ((50, 38), (78, 38), (50, 56), (78, 56)):
        s.tree(tx, tz, h=6, r=2)
    # benches along the wing facades
    for z in (34, 58):
        for x in (47, 81):
            s.stair(x, F, z, "e" if x < 64 else "w", OAK)
    # flower beds
    for x in range(46, 58):
        for z in range(52, 54):
            q = rnd(x, F, z, 33)
            s.put(x, F, z, "cornflower" if q < 0.3 else "allium" if q < 0.5 else "azure_bluet" if q < 0.7 else "poppy")
    for x in range(71, 83):
        for z in range(52, 54):
            q = rnd(x, F, z, 34)
            s.put(x, F, z, "cornflower" if q < 0.3 else "allium" if q < 0.5 else "azure_bluet" if q < 0.7 else "poppy")
    for z in (35, 42, 51, 58):
        s.lamp(61, z, 3)
        s.lamp(67, z, 3)


def landscape(s):
    # trees and hedges round the plot, a park west and east of the academy, and the forest edge
    for (x, z) in ((8, 20), (14, 40), (6, 60), (12, 85), (4, 100), (118, 20), (122, 45), (116, 62), (120, 100),
                   (20, 106), (100, 108), (30, 108), (90, 108), (10, 30), (114, 35), (14, 12), (112, 10),
                   (40, 108), (84, 109)):
        s.tree(x, z, h=5 + int(rnd(x, 0, z, 61) * 3), r=2)
    for x in (4, 6, 8, 10):
        s.tree(x, 70 + (x % 3) * 8, h=5, r=2)
    # the west garden of the academy: a gate pavilion to the dormitories we do not build
    for z in range(14, 62, 8):
        s.lamp(21, z, 3)
        s.lamp(107, z, 3)
    # a milestone by the road
    s.fill(60, F, 109, 60, F + 1, 109, "stone_bricks")
    s.put(60, F + 2, 109, "stone_brick_slab[type=bottom,waterlogged=false]")


def plants(s):
    for x in range(SX):
        for z in range(SZ):
            if s.get(x, F, z) is not None:
                continue
            if s.bp.blocks.get((x, G, z)) != M("grass_block"):
                continue
            q = rnd(x, F, z, 90)
            if q < 0.14:
                s.put(x, F, z, "short_grass")
            elif q < 0.16:
                s.put(x, F, z, ("dandelion", "poppy", "cornflower", "oxeye_daisy")[int(q * 1000) % 4])


def build(bp):
    s = Site(bp, G)
    ground(s)
    city_wall(s)
    gate(s)
    west_row(s)
    square(s)
    guild(s)
    academy(s)
    courtyard(s)
    landscape(s)
    plants(s)
    s.check_support("englassia")
    s.light(inplot, "englassia")
    s.check_support("englassia")
