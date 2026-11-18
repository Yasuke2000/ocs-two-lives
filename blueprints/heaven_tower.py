"""Heaven Tower, Dagruel's seat above the Desert of Death.

SIZE (81, 60, 91), anchor (40, 4, 83) on the south processional road facing north.
Three z slabs place a giant-scale threshold, an open shaft with internal galleries,
and a freestanding crown. The tower and its protected surroundings follow Fuse,
light novel vol. 18 ch. 2 and vol. 19 interlude/ch. 2. See design/lore/heaven_tower.md
for publisher sources. Our interpretation uses cut sandstone, rust-orange terracotta,
polished deepslate and ochre lamps. A paved boundary marks the refuge in the sand.
"""
from _dwargon_lib import AIR, noise2, rnd
from _lords_lib import M, fill, light_pass, slab, stair
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
            drift = noise2(x, z, 6, 35)
            # Overlapping sand tongues around the court and the two pairs of gate
            # stones. Omitted columns contain neither solid blocks nor explicit air.
            court_edge = max(abs(dx), abs(dz), (abs(dx) + abs(dz)) / 1.5) - 31
            # The dressed paving ends early, but its sand bed meets the outside
            # 1:1 skirt at the anchor grade along eleven columns of the south edge.
            apron_width = max(5, 15 - max(0, z - 79))
            road_edge = max(abs(dx) - apron_width, 63 - z)
            edge = min(court_edge, road_edge)
            if edge > 1 + 4 * drift:
                continue
            top = G - 1 if edge > 1 + drift else G
            seam = (2 * x + z + int(7 * drift)) % 30
            surface = M("red_sand") if seam < 3 else M("sand")
            if seam in (3, 4) and grain > 0.55:
                surface = M("terracotta")
            # Wind gradually buries first the border stones, then the road itself.
            # One central paving block at the anchor always survives.
            road_width = max(0, 6 - max(0, z - 76) // 2)
            intact = z <= 76 or (z <= 83 and abs(dx) <= 1)
            road = dz >= 0 and abs(dx) <= road_width and (
                intact or grain > min(1, (z - 76) / 12 + abs(dx) / 16))
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
            bp.set(x, 0, z, M("sandstone"))
            for y in range(1, top):
                bp.set(x, y, z, CUT if court_edge <= 0 else M("sandstone"))
            bp.set(x, top, z, surface)
            # Explicit air keeps interiors and covered passages open. The placer
            # clears above the footprint and trims surrounding hills to the skirt.
            if edge <= 0:
                for y in range(top + 1, SIZE[1]):
                    bp.blocks[x, y, z] = AIR


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


def fortress_hall(bp):
    """Two arcades frame the central floor, leaving a wide aisle below the shaft."""
    for x in (CX - 9, CX + 9):
        for z in (CZ - 8, CZ, CZ + 8):
            fill(bp, x - 1, 4, z - 1, x + 1, 4, z + 1, RED)
            fill(bp, x, 5, z, x, 17, z, DARK)
            for y in (6, 14):
                bp.set(x, y, z, RUNE)
            for side in (-1, 1):
                bp.set(x + side, 5, z, PALE)
                bp.set(x + side, 15, z, RUNE)
                bp.set(x + side, 16, z, PALE)
            for dz in range(-4, 5):
                # The arch rises at mid-span between successive piers.
                soffit = 15 + min(abs(dz), 3)
                fill(bp, x, soffit, z + dz, x, 18, z + dz, PALE)
                bp.set(x, soffit, z + dz, LAMP if abs(dz) == 4 else RED)
        # Two human-sized seats in each side aisle look across the giant hall.
        facing = "west" if x < CX else "east"
        for z in (CZ - 4, CZ + 4):
            for offset in (-1, 0, 1):
                bp.set(x + (-4 if x < CX else 4), 4, z + offset, stair("sandstone", facing))

    # A blind doorway on the north wall carries the same outline as the summit
    # opening. Its dark recess and lit keystone are visible from the south road.
    wall_z = CZ - 16
    for dx in range(-5, 6):
        head = 14 - max(0, abs(dx) - 2)
        fill(bp, CX + dx, 4, wall_z, CX + dx, head, wall_z, DARK)
        if abs(dx) >= 4:
            fill(bp, CX + dx, 4, wall_z + 1, CX + dx, head, wall_z + 1, RUNE)
        bp.set(CX + dx, head, wall_z + 1, LAMP if dx == 0 else RED)
        bp.set(CX + dx, head + 1, wall_z + 1, PALE)


def watch_porch(bp):
    """An upper door opens from the first gallery onto a roofed lookout."""
    inner_z, outer_z = CZ + 13, CZ + 18
    for dx in range(-3, 4):
        head = 25 - max(0, abs(dx) - 1)
        fill(bp, CX + dx, 20, inner_z, CX + dx, head, inner_z + 1, AIR)
        bp.set(CX + dx, head + 1, inner_z + 2, RUNE)
    for dx in (-5, 5):
        x = CX + dx
        fill(bp, x, 20, outer_z, x, 25, outer_z, DARK)
        bp.set(x, 20, outer_z, RUNE)
        bp.set(x, 25, outer_z, RUNE)
        fill(bp, x, 20, inner_z + 2, x, 20, outer_z - 1, M("sandstone_wall"))
    fill(bp, CX - 5, 26, inner_z + 1, CX + 5, 26, outer_z, CUT)
    fill(bp, CX - 5, 26, outer_z + 1, CX + 5, 26, outer_z + 1, RED)
    fill(bp, CX - 5, 27, outer_z + 1, CX + 5, 27, outer_z + 1, slab("sandstone"))
    for dx in range(-4, 5):
        bp.set(CX + dx, 20, outer_z, M("sandstone_wall"))
    for dx in (-3, 3):
        bp.set(CX + dx, 26, outer_z - 1, LAMP)


def build(bp):
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
    fortress_hall(bp)
    watch_porch(bp)
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
