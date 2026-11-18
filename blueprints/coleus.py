"""Coleus, the palace ascent above the oasis of Herbaria.

SIZE (85, 47, 79), three z slabs. Anchor (42, 4, 72) at the foot of the stair.
INEI's official Coleus panorama (ten-sura.com/anime/coleus/introduction) shows a
long inclined approach to an ochre hilltop drum, turquoise domes and an oasis.
Sandstone, terracotta, gold, cyan concrete and waxed oxidized copper model these
surfaces. The rose pavilion and audience chamber interpret the succession story.
"""
import math

import blueprint

from _lords_lib import AIR, M, fill_air, light_pass, stair

SIZE = (85, 47, 79)
PARTS = [0, 27, 54]
C = 42
SAND = M("smooth_sandstone")
CUT = M("cut_sandstone")
CARVED = M("chiseled_sandstone")
GOLD = M("gold_block")
TILE = M("waxed_oxidized_cut_copper")
LAMP = M("ochre_froglight")


def hill(bp):
    for x in range(85):
        for z in range(79):
            # An irregular sandstone outcrop breaks into dry washes at the foot.
            dx, dz = x - C, z - 23
            d = math.hypot(dx / 41, dz / 47)
            edge = 1 + .045 * math.sin(x / 4 + z / 8) + .04 * math.cos(z / 5)
            pool = ((x - 17) / 12) ** 2 + ((z - 62) / 7) ** 2
            road = abs(dx) <= 6 and z >= 39
            if d >= edge and pool > 1.7 and not road:
                continue
            height = 3 + max(0, int(17 * (edge - d)))
            if pool < 1.6:
                height = 3
            for y in range(height + 1):
                bed = (y + int(1.8 * math.sin(x / 16 + z / 22))) % 8
                rock = "terracotta" if bed == 1 else "sandstone" if bed < 5 else "cut_sandstone"
                if y == height and height <= 7:
                    rock = "sandstone" if (x * 3 + z) % 9 < 2 else "sand"
                bp.set(x, y, z, M(rock))
            if pool < 1:
                bp.set(x, 2, z, M("clay"))
                bp.set(x, 3, z, M("water"))


def palm(bp, x, z, h, lean):
    for y in range(4, 4 + h):
        offset = lean if y >= 4 + h // 2 else 0
        bp.set(x + offset, y, z, M("jungle_log"))
        if y == 4 + h // 2:
            bp.set(x, y, z, M("jungle_log"))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
        length = 3 if dx * dz else 4
        for n in range(length + 1):
            bp.set(x + lean + n * dx, 4 + h - (1 if n == 0 else max(0, n - 2)), z + n * dz,
                   M("jungle_leaves[persistent=true]"))


def octagon(x, z, r):
    return max(abs(x), abs(z)) <= r and abs(x) + abs(z) <= r + r // 2


def pavilion(bp, cx, cz, floor, r, height, dome):
    """Octagonal sandstone hall with a recessed portal, clerestory and ribbed shallow dome."""
    top = floor + height
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            dx, dz = x - cx, z - cz
            if not octagon(dx, dz, r):
                continue
            bp.fill(x, 1, z, x, floor, z, CUT)
            bp.set(x, floor, z, CARVED if (dx + dz) % 9 == 0 else SAND)
            edge = any(not octagon(dx + a, dz + b, r) for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)))
            if edge:
                along = dx if abs(dz) == r else dz
                for y in range(floor + 1, top):
                    band = y - floor
                    state = CARVED if band in (2, height - 2) else SAND
                    if abs(dx) == r or abs(dz) == r:
                        if along % 4 == 0:
                            state = CUT if band % 4 else CARVED
                        elif 3 <= band <= height - 3:
                            state = M("cyan_stained_glass") if along % 4 == 2 or band < height - 3 else SAND
                    if band == height - 1:
                        state = M("yellow_terracotta") if (x + z) % 4 else CARVED
                    if dz == r and abs(dx) <= 2 and band <= min(6, height - 2) - abs(dx) // 2:
                        state = AIR
                    bp.set(x, y, z, state)
            bp.set(x, top, z, CUT)
            if edge:
                bp.set(x, top + 1, z, M("smooth_sandstone_slab"))
            if not edge and dx % 6 == 0 and dz % 6 == 0:
                bp.set(x, top - 1, z, LAMP)
    # The roof has a broad ochre rim around the small, blue-green crown in INEI's panorama.
    for dy in range(dome + 1):
        radius = math.sqrt(max(0, dome * dome - dy * dy))
        for dx in range(-dome, dome + 1):
            for dz in range(-dome, dome + 1):
                if math.hypot(dx, dz) <= radius + .25:
                    bp.set(cx + dx, top + 1 + dy, cz + dz,
                           TILE if dx == 0 or dz == 0 else M("cyan_concrete"))
    bp.set(cx, top + dome + 2, cz, GOLD)
    bp.set(cx, top + dome + 3, cz, M("lightning_rod"))
    if r > 7:
        for dx, dz in ((-r // 2 + 1, -r), (r // 2, -r), (-r // 2 + 1, r), (r // 2, r)):
            bp.fill(cx + dx, top + 1, cz + dz, cx + dx, top + 3, cz + dz, M("sandstone_wall"))
            bp.set(cx + dx, top + 4, cz + dz, M("lightning_rod"))


def court(bp):
    # A walkable mid-terrace links both secondary pavilions to the main stair.
    for x in range(10, 75):
        for z in range(32, 50):
            if abs(x - C) < 7 or abs(x - C) + z > 74:
                continue
            bp.fill(x, 1, z, x, 13, z, CUT)
            bp.fill(x, 14, z, x, 14, z, SAND)
    for x in range(22, 63):
        for z in range(6, 40):
            if abs(x - C) + abs(z - 22) < 33:
                bp.fill(x, 2, z, x, 18, z, CUT)
                bp.set(x, 19, z, SAND)
    pavilion(bp, 42, 21, 19, 13, 13, 8)
    for x in (17, 67):
        pavilion(bp, x, 33, 14, 6, 7, 4)
        # The annexes open south; a carved screen marks the private part of each room.
        for dx in (-3, 3):
            bp.set(x + dx, 15, 32, M("flower_pot"))
            bp.fill(x + dx, 15, 29, x + dx, 18, 29, CARVED)
        bp.fill(x - 2, 15, 29, x + 2, 15, 29, M("red_carpet"))
    # The sovereign's seat and the two princes' benches face a blue-and-gold runner.
    bp.fill(39, 20, 10, 45, 20, 14, CUT)
    bp.set(C, 21, 11, stair("dark_oak", "north"))
    bp.fill(41, 21, 10, 43, 23, 10, M("red_terracotta"))
    bp.set(C, 24, 10, GOLD)
    for side in (-1, 1):
        for z in (16, 22, 28):
            bp.set(C + side * 6, 20, z, stair("dark_oak", "east" if side > 0 else "west"))
        bp.fill(C + side * 3, 19, 15, C + side * 3, 19, 33, M("yellow_terracotta"))
    bp.fill(41, 20, 15, 43, 20, 33, M("cyan_carpet"))
    for x in (34, 50):
        for z in (16, 25):
            bp.fill(x, 20, z, x, 31, z, CUT)
            bp.set(x, 21, z, CARVED)
            bp.set(x, 30, z, GOLD)


def galleries(bp):
    # Projecting eaves shade the south loggia. Five slender arches keep its centre open.
    for x in (31, 36, 48, 53):
        bp.fill(x, 20, 36, x, 26, 36, CUT)
        bp.set(x, 20, 36, CARVED)
        bp.set(x, 25, 36, CARVED)
        for dx in (-1, 1):
            bp.set(x + dx, 26, 36, stair("smooth_sandstone", "west" if dx > 0 else "east", "top"))
    for x in range(30, 55):
        for z in range(32, 38):
            bp.set(x, 27, z, M("smooth_sandstone_slab"))
    for x in (33, 51):
        bp.set(x, 26, 35, M("lantern[hanging=true]"))
    bp.fill(36, 27, 37, 48, 27, 37, M("yellow_terracotta"))
    for x in (37, 39, 42, 45, 47):
        bp.set(x, 27, 37, TILE)
    # Carved recesses and their stone coping make the masonry legible along the stair.
    for x in (21, 27, 33, 51, 57, 63):
        front = min(49, 74 - abs(x - C))
        for dx in range(-1, 2):
            bp.fill(x + dx, 8, front, x + dx, 11 - abs(dx), front, AIR)
            bp.set(x + dx, 12 - abs(dx), front, CARVED)
        bp.set(x, 9, front - 1, LAMP)
    # Openwork terrace screens leave a break at the stairs and at the side halls.
    for side in (-1, 1):
        for n in range(9, 24):
            x = C + side * n
            bp.set(x, 15, 48, CARVED if n % 4 == 1 else M("sandstone_wall[east=low,west=low,up=false]"))
            if n % 4 == 1:
                bp.set(x, 16, 48, M("smooth_sandstone_slab"))
    # Zenobia's sickroom: a bed beneath a narrow fabric canopy, book and water at hand.
    bp.set(65, 15, 32, M("red_bed[part=head,facing=north]"))
    bp.set(65, 15, 33, M("red_bed[part=foot,facing=north]"))
    for x in (64, 66):
        for z in (31, 34):
            bp.fill(x, 15, z, x, 17, z, M("stripped_birch_log"))
    bp.fill(64, 18, 31, 66, 18, 34, M("white_wool"))
    bp.set(69, 15, 33, M("lectern[facing=west]"))
    bp.set(69, 15, 35, M("water_cauldron[level=3]"))
    for x in (14, 20):
        bp.fill(x, 15, 32, x, 15, 34, M("smooth_sandstone_slab"))
    bp.fill(16, 15, 32, 18, 15, 33, M("dark_oak_slab[type=top]"))
    bp.set(17, 16, 33, M("flower_pot"))


def ascent(bp):
    for z in range(39, 79):
        step = max(3, 4 + (69 - z) // 2)
        for x in range(36, 49):
            dx = abs(x - C)
            bp.fill(x, 2, z, x, step, z, CUT)
            tread = stair("smooth_sandstone", "north") if z <= 69 and z % 2 else SAND
            bp.set(x, step, z, tread)
            if dx == 6 and z < 70 and not 47 <= z <= 50:
                bp.set(x, step + 1, z, CARVED if z % 6 == 0 else M("smooth_sandstone_slab"))
                if z % 8 == 0:
                    bp.set(x, step + 1, z, CARVED)
                    bp.set(x, step + 2, z, M("lantern"))
    # Roses beside the two lower doorways refer to the final episode, Purple and Roses.
    for x in (13, 21, 63, 71):
        bp.set(x, 14, 40, M("dirt"))
        bp.set(x, 15, 40, M("rose_bush[half=lower]"))
        bp.set(x, 16, 40, M("rose_bush[half=upper]"))


def lower_gate(bp):
    # The concept board sets two little domes at the foot of the long incline.
    for x in (33, 51):
        for rx in range(x - 4, x + 5):
            for rz in range(63, 73):
                bp.fill(rx, 1, rz, rx, 3, rz, CUT)
        pavilion(bp, x, 67, 3, 3, 5, 2)
        bp.set(x, 4, 66, M("barrel[facing=up]"))
    for x in (36, 48):
        for z in (65, 71):
            bp.set(x, 4, z, CARVED)
            bp.set(x, 5, z, M("lantern"))
    for x in range(36, 49):
        underside = 8 + min(3, (6 - abs(x - C)) // 2)
        bp.fill(x, underside, 67, x, 11, 67, SAND)
        bp.set(x, 12, 67, CARVED if x % 2 else M("smooth_sandstone_slab"))


def build(bp):
    # The generic preview palette otherwise displays all copper as fresh orange.
    if not any(name == "waxed_oxidized_cut_copper" for name, _ in blueprint._COLORS):
        blueprint._COLORS.append(("waxed_oxidized_cut_copper", (72, 163, 141)))
    fill_air(bp)
    hill(bp)
    for x, z, h, lean in ((11, 55, 7, -1), (23, 69, 8, 1), (6, 66, 5, -1)):
        palm(bp, x, z, h, lean)
    court(bp)
    galleries(bp)
    ascent(bp)
    lower_gate(bp)
    light_pass(bp, lambda x, y, z: (9 <= x <= 75 and 7 <= z <= 41 and y >= 14) or (29 <= x <= 55 and 63 <= z <= 71), 4,
               lambda x, y, z: M("lantern"), label="coleus")
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            # Clear inside rooms, keep the natural surface outside the outcrop.
            for y in reversed(range(SIZE[1])):
                if bp.blocks[x, y, z] != AIR:
                    break
                del bp.blocks[x, y, z]
