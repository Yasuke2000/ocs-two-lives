"""Heaven Tower, Dagruel's seat above the Desert of Death.

SIZE (81, 60, 91), anchor (40, 4, 83) on the south processional road facing north.
Three z slabs place a giant-scale threshold, an open shaft with internal galleries,
and a freestanding crown. The tower and its protected surroundings follow Fuse,
light novel vol. 18 ch. 2 and vol. 19 interlude/ch. 2. See design/lore/heaven_tower.md
for publisher sources. Our interpretation uses cut sandstone, rust-orange terracotta,
polished deepslate and ochre lamps. A paved boundary marks the refuge in the sand.
"""
from _dwargon_lib import AIR, rnd
from _lords_lib import M, fill, fill_air, light_pass
from _town_lib import lantern_floor

SIZE = (81, 60, 91)
PARTS = [0, 30, 60]
CX, CZ = 40, 34
G = 3
CUT = M("cut_sandstone")
PALE = M("smooth_sandstone")
DARK = M("polished_deepslate")
RED = M("orange_terracotta")
RUNE = M("chiseled_sandstone")
LAMP = M("ochre_froglight[axis=y]")


def octagon(dx, dz, radius):
    return max(abs(dx), abs(dz)) <= radius and abs(dx) + abs(dz) <= radius * 3 // 2


def terrain(bp):
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            dx, dz = x - CX, z - CZ
            grain = rnd(x, 0, z, 9)
            # Streaks of red hardpan crossing the plain like exposed beds.
            seam = (2 * x + z + int(4 * rnd(x // 6, 0, z // 6, 12))) % 30
            surface = M("red_sand") if seam < 3 else M("sand")
            if seam in (3, 4) and grain > 0.55:
                surface = M("terracotta")
            road = abs(dx) <= 6 and dz >= 0
            # The Holy Void shelters the ground near the tower. Let the red seams
            # stop at an octagonal curb, visible from each of the upper galleries.
            if octagon(dx, dz, 31):
                surface = PALE if octagon(dx, dz, 30) else RED
            if octagon(dx, dz, 25) or road:
                surface = PALE if grain > 0.74 else CUT
            if abs(dx) + abs(dz) in (6, 12) or dx == 0 and abs(dz) < 12:
                surface = RED
            if abs(dx) + abs(dz) == 6 and (dx == 0 or dz == 0):
                surface = LAMP
            if road and abs(dx) in (4, 6):
                surface = RED
            if road and abs(dx) == 5 and z % 8 == 0:
                surface = LAMP
            fill(bp, x, 0, z, x, G - 1, z, CUT)
            bp.set(x, G, z, surface)


def shell(bp, radius, low, high):
    """Battered octagonal walls, incised recesses and fluted jambs on four axes."""
    for x in range(CX - radius, CX + radius + 1):
        for z in range(CZ - radius, CZ + radius + 1):
            dx, dz = abs(x - CX), abs(z - CZ)
            if not octagon(dx, dz, radius) or octagon(dx, dz, radius - 2):
                continue
            along = min(dx, dz)
            for y in range(low, high + 1):
                state = CUT
                if y in (low, high):
                    state = RED
                elif y == high - 1:
                    state = PALE
                elif along in (3, 4) and max(dx, dz) == radius:
                    state = DARK
                elif along == 0 and low + 2 <= y <= high - 3:
                    state = LAMP if y == high - 3 else M("orange_stained_glass")
                elif along % 5 == 0 and y == low + 2:
                    state = RUNE
                bp.set(x, y, z, state)


def gallery(bp, radius, y):
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            if not octagon(dx, dz, radius):
                continue
            # Looking up through the progressively smaller tiers, visitors can see sky.
            if abs(dx) <= 2 and abs(dz) <= 2:
                continue
            if (dx, dz) == (4, -3):
                continue  # continuous ladder well
            state = RED if max(abs(dx), abs(dz)) == radius else PALE
            if (abs(dx), abs(dz)) in ((3, 3), (0, radius - 1)):
                state = LAMP
            bp.set(CX + dx, y, CZ + dz, state)
            if max(abs(dx), abs(dz)) == 3:
                bp.set(CX + dx, y + 1, CZ + dz, M("sandstone_wall"))


def processional_gate(bp):
    # The entrance and the crown repeat the same notched monumental opening.
    for dx in range(-5, 6):
        height = 10 - max(0, abs(dx) - 2)
        for z in range(CZ + 15, CZ + 23):
            fill(bp, CX + dx, G + 1, z, CX + dx, G + height, z, AIR)
    for dx in range(-8, 9):
        cap = G + 12 - max(0, abs(dx) - 2)
        for z in (CZ + 19, CZ + 20):
            if abs(dx) >= 6:
                fill(bp, CX + dx, G + 1, z, CX + dx, cap, z, DARK)
            bp.set(CX + dx, cap, z, RED)
            bp.set(CX + dx, cap + 1, z, RUNE if dx % 3 == 0 else PALE)
    # Tall, slightly tapering gate stones. The damaged pair marks the outer threshold.
    for x in (CX - 12, CX + 12):
        for z, height in ((66, 12), (78, 6)):
            fill(bp, x - 2, 4, z - 2, x + 2, 5, z + 2, RED)
            fill(bp, x - 1, 6, z - 1, x + 1, 5 + height, z + 1, CUT)
            fill(bp, x, 7, z + 1, x, 4 + height, z + 1, DARK)
            bp.set(x, 4 + height, z + 1, LAMP)
            bp.set(x, 6 + height, z, RUNE)


def build(bp):
    fill_air(bp)
    terrain(bp)
    # Four diminishing drums share one atrium and three walkable ledges.
    for radius, low, high in ((18, 4, 18), (14, 20, 32), (11, 34, 43), (8, 45, 47)):
        shell(bp, radius, low, high)
        gallery(bp, radius + 1, high + 1)
    # Continuous masonry ribs lean inward to carry each next tier on all four faces.
    for sign in (-1, 1):
        for offset in (-8, 8):
            for y in range(4, 44):
                reach = 24 - (y - 4) // 3
                for d in range(reach - 4, reach + 1):
                    for side in (offset, offset + 1):
                        material = RED if y in (8, 18, 32, 43) else PALE
                        bp.set(CX + sign * d, y, CZ + side, material)
                        bp.set(CX + side, y, CZ + sign * d, material)
    # Waist-high bollards carry the refuge boundary across the four diagonal faces.
    # The south road stays open for the procession.
    for dx in (-23, 23):
        for dz in (-23, 23):
            x, z = CX + dx, CZ + dz
            fill(bp, x - 1, 4, z - 1, x + 1, 4, z + 1, RED)
            bp.set(x, 5, z, RUNE)
            bp.set(x, 6, z, LAMP)
    processional_gate(bp)
    # East of the atrium, a ladder gives all gallery floors a common landing.
    fill(bp, CX + 5, 4, CZ - 3, CX + 5, 49, CZ - 3, DARK)
    fill(bp, CX + 4, 4, CZ - 3, CX + 4, 49, CZ - 3, M("ladder[facing=west]"))
    # A giant door frame silhouetted against the sky. There are no portal blocks.
    for dx in range(-5, 6):
        h = 58 - max(0, abs(dx) - 2)
        for z in (CZ - 1, CZ, CZ + 1):
            if abs(dx) >= 4:
                fill(bp, CX + dx, 49, z, CX + dx, h, z, DARK)
            bp.set(CX + dx, h, z, LAMP if dx == 0 else RUNE)
            bp.set(CX + dx, h + 1, z, RED)
    light_pass(bp, lambda x, y, z: octagon(x - CX, z - CZ, 31) or
               (abs(x - CX) <= 14 and z >= CZ + 19), 4,
               lambda x, y, z: lantern_floor(), label="heaven_tower")
