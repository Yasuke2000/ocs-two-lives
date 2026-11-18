"""Holy City Lubelius (Lune): the cathedral of the Western Holy Church and its square, white stone and gold.

Lore notes and sources: design/lore/lubelius.md. SIZE (120, 64, 120), saved as three z slabs lubelius_0..2
(PARTS). Ground layer y 4 (grass and white paving, dirt below), you walk at y 5; everything above is air, so the
placer clears forest and hills in the box (clear_above). The city arrives from the south: the road runs up to the
Holy Gate (white wall z 103-105, two gold-capped pylons, a 9 wide passage x 56-64), arrival point blueprint
(60, 5, 114) facing north. Beyond the gate the Holy Square (z 64-102, a paved disc with gold rings, a fountain and
a golden-crowned pillar at (60, 84)) is closed by two colonnaded halls: the Hall of the Holy Knights on the east
side (Hinata Sakaguchi's Temple Knights, banners, long tables) and the Pilgrims' Hall on the west. The cathedral
fills the north (z 8-62): a cross-shaped church of white quartz, the nave x 49-71 (z 16-62) with the transept
x 30-90 (z 28-50), a dome over the crossing (drum and hemisphere, radius 11, gold bands, lantern turret and rod to y 55), twin
facade towers (x 40-48 and 72-80, spires and rods to y 58), a rose window and a seven wide portal in the facade (z 62).
Inside: marble floor with gold inlay, a red carpet, pews in the south arm, a raised choir with a gold altar in the
north arm, chandeliers hung from the ridge. The Sacred Mountain approach (separate landmark) is not built here.
Palette: quartz, quartz bricks, pillars, smooth quartz, calcite, gold blocks, light blue stained glass. Our
interpretation: canon says the capital is a rich city with high-end magic and technology, seat of the Western Holy
Church (the real-world Vatican analogy); the cathedral's form is ours. Every spawnable spot inside the plot has
block light (checked when this builds).
"""
import math

from _citylib import AIR, M, Mat, Site
from _dwargon_lib import noise2, rnd

SIZE = (120, 64, 120)
SX, SY, SZ = SIZE
G = 4
F = G + 1
ARRIVAL = (60, F, 114)
PARTS = [0, 40, 80]

QB = Mat("quartz_block", "quartz_stairs", "quartz_slab")
QBR = Mat("quartz_bricks")
SMQ = Mat("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab")
PILL = Mat("quartz_pillar")
CHISEL = Mat("chiseled_quartz_block")
CAL = Mat("calcite")
GOLD = Mat("gold_block")
BIRCH = Mat("birch_planks", "birch_stairs", "birch_slab")
GLASS = "light_blue_stained_glass_pane"


def inplot(x, z) -> bool:
    return 3 <= x < SX - 3 and 3 <= z < SZ - 1


def paving(x, z):
    q = rnd(x, 0, z, 6)
    return M("smooth_quartz") if q < 0.5 else M("calcite") if q < 0.8 else M("quartz_block")


# --- ground ---------------------------------------------------------------------------------------------------


def ground(s):
    s.ground(lambda x, z: M("grass_block"))
    for x in range(30, 90):
        for z in range(63, 103):
            s.bp.blocks[(x, G, z)] = paving(x, z)
    # the square: concentric inlays round the fountain at (60, 84)
    for x in range(30, 90):
        for z in range(63, 103):
            d = math.hypot(x - 60, z - 84)
            if 17.5 <= d < 18.5 or 9.6 <= d < 10.4:
                s.bp.blocks[(x, G, z)] = M("gold_block")
            elif 18.5 <= d < 19.5:
                s.bp.blocks[(x, G, z)] = M("chiseled_quartz_block")
    for x in range(59, 62):
        for z in range(62, 66):
            s.bp.blocks[(x, G, z)] = M("gold_block") if (x == 60) else M("quartz_pillar")
    # white road: avenue from the gate to the square and the road outside
    for z in range(103, 120):
        for x in range(57, 64):
            s.bp.blocks[(x, G, z)] = paving(x, z) if z < 108 else M("smooth_quartz") if (x in (57, 63)) else M("dirt_path")
    for z in range(95, 104):
        for x in range(56, 65):
            s.bp.blocks[(x, G, z)] = paving(x, z)
    # courtyard pavings for the two halls and the cathedral apron
    for x in range(28, 33):
        for z in range(66, 101):
            s.bp.blocks[(x, G, z)] = M("quartz_block")
    for x in range(88, 93):
        for z in range(66, 101):
            s.bp.blocks[(x, G, z)] = M("quartz_block")
    for x in range(40, 81):
        for z in range(63, 65):
            s.bp.blocks[(x, G, z)] = M("smooth_quartz")


# --- the cathedral ------------------------------------------------------------------------------------------
NX0, NX1, NZ0, NZ1 = 49, 71, 16, 62
TX0, TX1, TZ0, TZ1 = 30, 90, 28, 50
H = 20
CX, CZ = 60, 39


def cathedral(s):
    s.box_walls(NX0, NZ0, NX1, NZ1, F, H, QBR, PILL, bay=4, glass=GLASS, rows=((5, 15),), base_h=2, base=QB,
                glass_axis_skip=("s",))
    s.box_walls(TX0, TZ0, TX1, TZ1, F, H, QBR, PILL, bay=4, glass=GLASS, rows=((5, 15),), base_h=2, base=QB,
                glass_axis_skip=())
    # floor: marble with gold inlay, nave and transept
    for (x0, z0, x1, z1) in ((NX0, NZ0, NX1, NZ1), (TX0, TZ0, TX1, TZ1)):
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                q = (x // 2 + z // 2) % 2
                s.bp.blocks[(x, G, z)] = M("smooth_quartz") if q else M("calcite")
    for z in range(NZ0 + 1, NZ1):
        for x in (56, 64):
            s.bp.blocks[(x, G, z)] = M("gold_block")
    for x in range(TX0 + 1, TX1):
        for z in (CZ - 6, CZ + 6):
            s.bp.blocks[(x, G, z)] = M("gold_block")
    # open the crossing: the nave's side walls inside the transept and the transept's walls across the nave
    s.air(NX0, F, TZ0 + 1, NX0, F + H - 1, TZ1 - 1)
    s.air(NX1, F, TZ0 + 1, NX1, F + H - 1, TZ1 - 1)
    s.air(NX0 + 1, F, TZ0, NX1 - 1, F + H - 1, TZ0)
    s.air(NX0 + 1, F, TZ1, NX1 - 1, F + H - 1, TZ1)
    for (px, pz) in ((49, 28), (69, 28), (49, 48), (69, 48)):
        for x in range(px, px + 3):
            for z in range(pz, pz + 3):
                for y in range(F, F + H):
                    s.put(x, y, z, "quartz_pillar")
    # roofs: four gabled arms round the crossing
    s.gable(NX0, NZ0, NX1, 27, F + H, SMQ, axis="z", wall=QBR, cap=QB, ends="both")
    s.gable(NX0, 51, NX1, NZ1, F + H, SMQ, axis="z", wall=QBR, cap=QB, ends="both")
    s.gable(TX0, TZ0, 48, TZ1, F + H, SMQ, axis="x", wall=QBR, cap=QB, ends="both")
    s.gable(72, TZ0, TX1, TZ1, F + H, SMQ, axis="x", wall=QBR, cap=QB, ends="both")
    # gold rims at the eaves
    for (x0, z0, x1, z1) in ((NX0, NZ0, NX1, NZ1),):
        pass
    # the crossing: clear the roof stubs, then a square-to-circle platform, drum and dome
    s.air(NX0, F + H, TZ0, NX1, F + H + 20, TZ1)
    for x in range(NX0, NX1 + 1):
        for z in range(TZ0 + 1, TZ1):
            d = math.hypot(x - CX, z - CZ)
            if d > 10.5:
                s.put(x, F + H, z, "smooth_quartz")
    for x in range(NX0 + 1, NX1):
        for z in range(TZ0 + 1, TZ1):
            if math.hypot(x - CX, z - CZ) <= 10.5:
                s.bp.blocks.pop((x, F + H, z), None)
    # drum
    for dy in range(1, 9):
        y = F + H + dy
        for x in range(CX - 12, CX + 13):
            for z in range(CZ - 12, CZ + 13):
                d = math.hypot(x - CX, z - CZ)
                if 10.5 < d <= 11.5:
                    ang = math.degrees(math.atan2(z - CZ, x - CX)) % 45
                    window = 3 <= dy <= 6 and 17 < ang < 28
                    s.put(x, y, z, "light_blue_stained_glass" if window else "quartz_pillar" if dy in (1, 8) or ang < 4 else "quartz_bricks")
    # drum cornice, gold band
    for x in range(CX - 13, CX + 14):
        for z in range(CZ - 13, CZ + 14):
            d = math.hypot(x - CX, z - CZ)
            if 11.5 < d <= 12.5:
                s.put(x, F + H + 8, z, "gold_block")
            if 11.5 < d <= 12.5:
                s.put(x, F + H + 7, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    # hemisphere dome
    base = F + H + 9
    R = 11.5
    for h in range(0, 12):
        r = math.sqrt(R * R - h * h)
        y = base + h
        mat = "gold_block" if h in (0, 5) else "smooth_quartz"
        if r <= 2.6:
            s.disc(CX, y, CZ, r, mat)
        else:
            s.disc(CX, y, CZ, r, mat, inner=r - 1.4)
    # lantern turret
    ty = base + 12
    for dy in range(0, 4):
        s.disc(CX, ty + dy, CZ, 2.4, "light_blue_stained_glass" if dy in (1, 2) else "quartz_pillar", inner=1.4)
    s.disc(CX, ty + 4, CZ, 3.0, "gold_block")
    s.disc(CX, ty + 5, CZ, 1.4, "gold_block")
    for dy in range(6, 10):
        s.put(CX, ty + dy, CZ, "gold_block" if dy < 9 else "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # one great chandelier on a long chain from the lantern turret down to head height over the crossing
    s.chandelier(CX, ty + 4, CZ, drop=ty + 3 - 12)


def towers(s):
    for (x0, x1) in ((40, 48), (72, 80)):
        z0, z1 = 54, 62
        s.box_walls(x0, z0, x1, z1, F, 36, QBR, PILL, bay=4, glass=GLASS, rows=((8, 12), (18, 22)), base_h=3, base=QB)
        s.rim(x0 - 1, z0 - 1, x1 + 1, z1 + 1, F + 12, "smooth_quartz")
        s.rim(x0 - 1, z0 - 1, x1 + 1, z1 + 1, F + 24, "smooth_quartz")
        s.rim(x0 - 1, z0 - 1, x1 + 1, z1 + 1, F + 35, "gold_block")
        s.rim(x0 - 1, z0 - 1, x1 + 1, z1 + 1, F + 36, "chiseled_quartz_block")
        s.fill(x0, F + 36, z0, x1, F + 36, z1, "smooth_quartz")
        # belfry: open arches with bars, a bell inside
        s.box_walls(x0, z0, x1, z1, F + 37, 6, QBR, PILL, bay=8, glass="iron_bars", rows=((1, 4),))
        s.put((x0 + x1) // 2, F + 41, (z0 + z1) // 2, "bell[facing=north,attachment=ceiling]")
        s.fill((x0 + x1) // 2, F + 42, (z0 + z1) // 2, (x0 + x1) // 2, F + 42, (z0 + z1) // 2, "quartz_block")
        s.rim(x0 - 1, z0 - 1, x1 + 1, z1 + 1, F + 43, "gold_block")
        top = s.hip(x0, z0, x1, z1, F + 44, SMQ, over=1)
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        for y in range(top + 1, top + 4):
            s.put(cx, y, cz, "gold_block")
        s.put(cx, top + 4, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        # small gold-capped pinnacles on the tower corners
        for px in (x0 - 1, x1 + 1):
            for pz in (z0 - 1, z1 + 1):
                s.fill(px, F + 44, pz, px, F + 46, pz, "quartz_pillar")
                s.put(px, F + 47, pz, "gold_block")
        s.air(x0 + 1, F, z0 + 1, x1 - 1, F + 35, z1 - 1)
        # a door in each tower's south side
        s.air((x0 + x1) // 2, F, z1, (x0 + x1) // 2, F + 2, z1)
        s.door((x0 + x1) // 2, F, z1, "s", "birch_door")
    # banners on the tower faces
    for x in (42, 46, 74, 78):
        s.wall_banner(x, F + 14, 63, "s", "light_blue")


def facade(s):
    z = 62
    # rose window above the portal
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            d = math.hypot(dx, dy)
            if d <= 5.2:
                if d <= 1.3:
                    st = "yellow_stained_glass"
                elif d <= 2.6:
                    st = "white_stained_glass"
                elif d <= 3.8:
                    st = "light_blue_stained_glass" if (round(math.degrees(math.atan2(dy, dx)) / 30) % 2) else "blue_stained_glass"
                else:
                    st = "gold_block"
                s.put(60 + dx, F + 22 + dy, z, st)
    # portal: seven wide, golden jambs, round-topped by stairs
    s.air(57, F, z, 63, F + 10, z)
    s.air(57, F, z - 1, 63, F + 10, z - 1)
    s.fill(56, F, z, 56, F + 11, z, "gold_block")
    s.fill(64, F, z, 64, F + 11, z, "gold_block")
    s.fill(56, F + 11, z, 64, F + 11, z, "gold_block")
    for xx, f in ((57, "e"), (63, "w")):
        s.stair(xx, F + 10, z, f, QB, half="top")
        s.stair(xx, F + 10, z - 1, f, QB, half="top")
    # steps in front
    # gold pilasters on the nave front
    for xx in (52, 68):
        s.fill(xx, F + 3, 63, xx, F + 17, 63, "quartz_pillar")
        s.put(xx, F + 18, 63, "gold_block")
        s.put(xx, F + 2, 63, "chiseled_quartz_block")


def interior(s):
    # choir: raised dais with the altar in the north arm, pews in the south arm, a red carpet down the nave
    for x in range(52, 69):
        for z in range(17, 25):
            s.put(x, F, z, "smooth_quartz")
    for x in range(54, 67):
        for z in range(17, 22):
            s.put(x, F + 1, z, "quartz_slab[type=bottom,waterlogged=false]")
    s.fill(58, F + 1, 18, 62, F + 2, 19, "gold_block")
    s.fill(59, F + 3, 18, 61, F + 3, 18, "gold_block")
    for x in (56, 64):
        s.fill(x, F + 1, 17, x, F + 4, 17, "quartz_pillar")
        s.lantern(x, F + 5, 17)
    # carpet
    for z in range(26, 62):
        for x in range(59, 62):
            if 28 <= z <= 50 and False:
                continue
            s.put(x, F, z, "red_carpet")
    # pews
    for z in (53, 55, 57, 59):
        for x in list(range(51, 57)) + list(range(63, 70)):
            s.stair(x, F, z, "n", BIRCH)
    # pillars and statues along the transept ends: gold candelabra
    for (x, z) in ((32, 33), (32, 45), (88, 33), (88, 45)):
        s.fill(x, F, z, x, F + 2, z, "quartz_pillar")
        s.put(x, F + 3, z, "gold_block")
        s.lantern(x, F + 4, z)
    # chandeliers hung from the ridge (y = F + H + 12), low enough to light the marble floor
    ridge = F + H + 12
    for (x, z) in ((60, 21), (60, 25), (60, 54), (60, 59), (33, 39), (45, 39), (75, 39), (87, 39)):
        s.chandelier(x, ridge, z, drop=26)


def square(s):
    cx, cz = 60, 84
    # fountain basin, three tiers of pedestal and the golden-crowned pillar
    s.disc(cx, F, cz, 6, "quartz_block", inner=4.6)
    s.disc(cx, G, cz, 4.6, "water[level=0]")
    s.disc(cx, F, cz, 2.5, "quartz_block")
    s.disc(cx, F + 1, cz, 1.6, "quartz_block")
    for y in range(F + 2, F + 18):
        s.put(cx, y, cz, "quartz_pillar")
    s.put(cx, F + 18, cz, "gold_block")
    s.put(cx, F + 19, cz, "gold_block")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.put(cx + dx, F + 18, cz + dz, "gold_block")
    s.put(cx, F + 20, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # eight braziers round the pillar ring
    for px, pz in s.bp.around(cx, cz, 14, 8, 22.5):
        s.fill(px, F, pz, px, F + 2, pz, "quartz_pillar")
        s.put(px, F + 3, pz, "gold_block")
        s.put(px, F + 4, pz, "lantern[hanging=false,waterlogged=false]")
    # rose gardens along the apron and the avenue
    for x in list(range(36, 48)) + list(range(73, 84)):
        z = 68
        q = rnd(x, F, z, 77)
        s.put(x, F, z, "rose_bush[half=lower]")
        s.put(x, F + 1, z, "rose_bush[half=upper]")
        s.put(x, F, z + 1, "red_tulip" if q < 0.5 else "poppy")
        s.put(x, G, z, "grass_block")
        s.put(x, G, z + 1, "grass_block")
    # benches facing the fountain
    for dx, dz, f in ((-16, 0, "e"), (16, 0, "w"), (0, 16, "n")):
        for k in (-1, 0, 1):
            xx, zz = (cx + dx, cz + dz + k) if dx else (cx + dx + k, cz + dz)
            s.stair(xx, F, zz, f, QB)
    # lamp posts
    for (x, z) in ((44, 70), (76, 70), (44, 98), (76, 98), (48, 90), (72, 90), (48, 78), (72, 78)):
        s.lamp(x, z, 3, post="diorite_wall")


# --- the two halls ------------------------------------------------------------------------------------------


def hall(s, x0, z0, x1, z1, face, banner="light_blue"):
    h = 15
    s.box_walls(x0, z0, x1, z1, F, h, QBR, PILL, bay=4, glass=GLASS, rows=((3, 5), (9, 11)), base_h=2, base=QB)
    s.rim(x0, z0, x1, z1, F + 6, "smooth_quartz")
    s.fill(x0 + 1, G, z0 + 1, x1 - 1, G, z1 - 1, "smooth_quartz")
    s.rim(x0, z0, x1, z1, F + 15, "chiseled_quartz_block")
    top = s.hip(x0, z0, x1, z1, F + 16, SMQ, over=1)
    s.put((x0 + x1) // 2, top + 1, (z0 + z1) // 2, "gold_block")
    for y in range(top + 2, top + 5):
        s.put((x0 + x1) // 2, y, (z0 + z1) // 2, "gold_block")
    s.air(x0 + 1, F, z0 + 1, x1 - 1, F + 14, z1 - 1)
    # doors onto the colonnade
    fx = x0 if face == "w" else x1
    zc = (z0 + z1) // 2
    s.air(fx, F, zc - 2, fx, F + 6, zc + 2)
    s.fill(fx, F + 7, zc - 2, fx, F + 7, zc + 2, "chiseled_quartz_block")
    o = "w" if face == "w" else "e"
    # interior: long tables, lecterns, chandeliers on beams
    for z in range(z0 + 3, z1 - 2, 4):
        for x in range(x0 + 4, x1 - 3):
            s.put(x, F + 1, z, "birch_slab[type=bottom,waterlogged=false]")
            if x % 3 == 0:
                s.put(x, F, z, "birch_fence")
            s.stair(x, F, z - 1, "s", BIRCH)
            s.stair(x, F, z + 1, "n", BIRCH)
    bx = (x0 + x1) // 2
    s.fill(bx, F + 13, z0 + 1, bx, F + 13, z1 - 1, "quartz_pillar[axis=z]")
    for z in range(z0 + 4, z1 - 2, 6):
        s.chandelier(bx, F + 13, z, drop=2)
    # banners inside, on the end walls
    for z in range(z0 + 4, z1 - 2, 8):
        s.wall_banner(x0 + 1 if face == "e" else x1 - 1, F + 5, z, "e" if face == "e" else "w", banner)
    return top


def colonnade(s, x0, x1, z0, z1, wall_x, face):
    """A covered walk of pillars along a hall's front: pillars every 4, flat roof with a gold course."""
    for z in range(z0, z1 + 1, 4):
        s.column(x1 if face == "e" else x0, z, F, F + 8, QB, pillar="quartz_pillar")
        s.put(x1 if face == "e" else x0, F, z, "chiseled_quartz_block")
        s.put(x1 if face == "e" else x0, F + 8, z, "chiseled_quartz_block")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            s.put(x, F + 9, z, "smooth_quartz")
    s.rim(x0, z0, x1, z1, F + 9, "gold_block")
    for z in range(z0, z1 + 1):
        s.put(x1 if face == "e" else x0, F + 10, z, "quartz_slab[type=bottom,waterlogged=false]")
    for x in range(x0, x1 + 1):
        s.put(x, F + 10, z0, "quartz_slab[type=bottom,waterlogged=false]")
        s.put(x, F + 10, z1, "quartz_slab[type=bottom,waterlogged=false]")


def halls(s):
    # Holy Knights' hall (east) and Pilgrims' hall (west), mirrored
    hall(s, 93, 68, 111, 100, "w", "light_blue")
    hall(s, 9, 68, 27, 100, "e", "white")
    colonnade(s, 89, 92, 68, 100, 93, "w")
    colonnade(s, 28, 31, 68, 100, 27, "e")
    # the knights' emblem: a white shield with a gold cross over the hall door, east
    for dy in range(-3, 4):
        for dz in range(-2, 3):
            if abs(dz) <= 2 and (abs(dy) <= 3):
                s.put(93, F + 12 + dy, 84 + dz, "white_concrete")
    for dy in range(-3, 4):
        s.put(93, F + 12 + dy, 84, "gold_block")
    for dz in range(-2, 3):
        s.put(93, F + 12, 84 + dz, "gold_block")
    # flags on the colonnades


def gate(s):
    for x in range(SX):
        if 46 <= x <= 74:
            continue
        for z in range(103, 106):
            for y in range(F, F + 7):
                s.put(x, y, z, "quartz_bricks")
        for z in (103, 105):
            if x % 2 == 0:
                s.put(x, F + 7, z, "quartz_block")
        s.put(x, F + 7, 104, "quartz_slab[type=bottom,waterlogged=false]")
    for x in range(4, SX, 10):
        if 44 <= x <= 76:
            continue
        s.fill(x, F, 106, x, F + 7, 106, "quartz_pillar")
        s.put(x, F + 8, 106, "gold_block")
    for (x0, x1) in ((47, 55), (65, 73)):
        s.box_walls(x0, 102, x1, 108, F, 20, QBR, PILL, bay=4, glass=GLASS, rows=((6, 9),), base_h=2, base=QB)
        s.rim(x0 - 1, 101, x1 + 1, 109, F + 20, "gold_block")
        s.fill(x0, F + 20, 102, x1, F + 20, 108, "smooth_quartz")
        top = s.hip(x0, 102, x1, 108, F + 21, SMQ, over=1)
        cx = (x0 + x1) // 2
        for y in range(top + 1, top + 4):
            s.put(cx, y, 105, "gold_block")
        s.put(cx, top + 4, 105, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        s.air(x0 + 1, F, 103, x1 - 1, F + 19, 107)
        s.air((x0 + x1) // 2, F, 108, (x0 + x1) // 2, F + 1, 108)
        s.door((x0 + x1) // 2, F, 108, "s", "birch_door")
    # the passage, with a round-topped arch
    s.air(56, F, 102, 64, F + 10, 108)
    s.fill(56, F + 11, 102, 64, F + 19, 108, "quartz_bricks")
    for z in range(102, 109):
        s.stair(56, F + 10, z, "e", QB, half="top")
        s.stair(64, F + 10, z, "w", QB, half="top")
    for z in (104, 106):
        s.put(60, F + 9, z, "chain[axis=y,waterlogged=false]")
        s.put(60, F + 8, z, "chain[axis=y,waterlogged=false]")
        s.lantern(60, F + 7, z, hanging=True)
    s.fill(57, F + 14, 109, 63, F + 14, 109, "gold_block")
    for x in (49, 53, 67, 71):
        s.wall_banner(x, F + 12, 109, "s", "light_blue")
    # a golden sun-disc over the passage
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            d = math.hypot(dx, dy)


def landscape(s):
    # birches and cherry trees round the plot, rose beds along the paved avenue
    trees = [(8, 20), (14, 40), (6, 60), (12, 110), (4, 90), (112, 20), (108, 40), (114, 60), (110, 112), (22, 10),
             (96, 10), (30, 20), (90, 20), (18, 56), (102, 56), (36, 112), (84, 112), (26, 108), (94, 108), (112, 85), (6, 85)]
    for (x, z) in trees:
        s.tree(x, z, h=5 + int(rnd(x, 0, z, 61) * 3), r=2, leaf="cherry_leaves" if (x + z) % 3 == 0 else "birch_leaves", log="birch_log")
    for z in range(110, 119, 4):
        s.lamp(56, z, 3, post="diorite_wall")
        s.lamp(64, z, 3, post="diorite_wall")
    # rose hedges beside the road outside the gate
    for z in range(110, 119):
        for x in (54, 66):
            s.put(x, F, z, "rose_bush[half=lower]")
            s.put(x, F + 1, z, "rose_bush[half=upper]")


def plants(s):
    for x in range(SX):
        for z in range(SZ):
            if s.get(x, F, z) is not None:
                continue
            if s.bp.blocks.get((x, G, z)) != M("grass_block"):
                continue
            q = rnd(x, F, z, 90)
            if q < 0.12:
                s.put(x, F, z, "short_grass")
            elif q < 0.15:
                s.put(x, F, z, ("dandelion", "poppy", "cornflower", "oxeye_daisy", "red_tulip")[int(q * 1000) % 5])


def build(bp):
    s = Site(bp, G)
    ground(s)
    gate(s)
    cathedral(s)
    towers(s)
    facade(s)
    interior(s)
    square(s)
    halls(s)
    landscape(s)
    plants(s)
    s.check_support("lubelius")
    s.light(inplot, "lubelius")
    s.check_support("lubelius")
