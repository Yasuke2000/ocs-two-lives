"""Guy Crimson's Frost Palace entrance, seen from the Ice Continent. SIZE (85, 51, 69);
anchor (42, 4, 65) on the south approach, looking north. Three z slabs. The white masonry
shows through Velzard's ice. A causeway crosses a frozen cleft to a pointed gate, guarded
by two faceted towers and sweeping ice horns. Packed ice, blue ice, quartz, snow,
violet glass and sea lanterns. References: anime episode 42 "The Demon Lords" (Leon's
walk through the palace); Fuse, light novel vol. 16, epilogue; Tensura Wiki, Frost Palace and Ice
Continent; the pack's political map. Sources and architectural interpretation in
design/lore/frost_palace.md.
"""
import math

import blueprint
from _dwargon_lib import AIR, noise2
from _lords_lib import M, fill, fill_air, light_pass, stair

SIZE = (85, 51, 69)
PARTS = [0, 23, 46]
C = 42

ICE = M("packed_ice")
BLUE = M("blue_ice")
SNOW = M("snow_block")
STONE = M("smooth_quartz")
PILLAR = M("quartz_pillar[axis=y]")
GLASS = M("light_blue_stained_glass")
LAMP = M("sea_lantern")


def shelf_depth(x, z):
    """Positive inside the wind-cut snow shelf; negative cells receive no new snow."""
    rim = 1 - (abs(x - C) / 40) ** 2.6 - (abs(z - 33) / 32) ** 2.6
    return rim + 0.22 * (noise2(x, z, 7, 11) - 0.5)


def snowfield(bp):
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            depth = shelf_depth(x, z)
            if depth <= 0:
                continue
            # Long, low drifts break up the snow surface. The outer ones settle back
            # toward survey grade before the hand-built ground gives way to native snow.
            wind = noise2(x * 0.48 + z * 0.35, z, 5, 37)
            drift = min(1, depth * 3) * max(0, 5 * wind - 2)
            shoulder = min(1, depth * 6)
            surface = 2 + round(shoulder) + int(drift)
            material = SNOW

            # The shallow cleft pinches out under the snow at both ends. Near the bridge
            # the blue-ice vein widens into a band of packed ice with low snow banks.
            taper = max(0, min(1, (x - 10) / 15, (74 - x) / 14))
            offset = abs(z - 46 - 3 * math.sin(x / 9) - 1.5 * math.sin(x / 4))
            if taper:
                surface = min(surface, 3 + int(max(0, offset - 7 * taper) / 2))
                if offset < 7 * taper:
                    surface = 3 - round(2 * taper * (1 - offset / (8 * taper)))
                    material = BLUE if offset < 1.7 * taper else ICE
            if abs(x - C) <= 8 and (z <= 6 or z >= 59):
                surface = 3
            bottom = min(surface - 1, 2 - round(2 * shoulder))
            fill(bp, x, bottom, z, x, surface - 1, z, ICE if material != SNOW else SNOW)
            bp.set(x, surface, z, material)
            if material == SNOW and wind > 0.56 and abs(x - C) > 12:
                layers = 1 + int(drift * 2) % 6
                bp.set(x, surface + 1, z, M(f"snow[layers={layers}]"))


def shard(bp, x, z, base, radius, height, lean):
    for i in range(height):
        r = max(0, math.ceil(radius * (1 - i / (height - 1))))
        mid = x + round(lean * (i / (height - 1)) ** 1.5)
        for dx in range(-r, r + 1):
            for dz in range(-r + abs(dx), r - abs(dx) + 1):
                face = BLUE if dx < 0 else ICE
                if dx == 0 and dz >= 0:
                    face = GLASS
                bp.set(mid + dx, base + i, z + dz, face)


def crossing(bp):
    for z in range(32, 69):
        deck = min(7, max(3, 66 - z))
        width = min(7, 69 - z)
        for x in range(C - width, C + width + 1):
            edge = abs(x - C)
            # Pairs of piers carry three open spans. The solid path at the ends meets the snow.
            if z < 37 or z >= 58 or z in (42, 43, 50, 51) and edge >= 5:
                fill(bp, x, 2, z, x, deck - 1, z, ICE)
            material = STONE
            if 59 < z < 63 or edge == 7:
                material = M("quartz_bricks")
            if 59 <= z <= 62:
                material = stair("quartz", "north")
            if z >= 64:
                material = ICE if edge < 66 - z else SNOW
                if (x - C, z) in ((-2, 64), (1, 65), (-1, 66), (0, 68)):
                    material = M("gravel")
            if edge == 5 and z < 59:
                material = LAMP if z % 6 == 0 else BLUE
            bp.set(x, deck, z, material)
            if edge == 7 and 36 <= z <= 58:
                bp.set(x, deck + 1, z, M("quartz_slab[type=bottom]"))
                if z in (36, 43, 51, 58):
                    bp.set(x, deck + 1, z, STONE)
                    bp.set(x, deck + 2, z, LAMP)
                    bp.set(x, deck + 3, z, M("quartz_slab[type=bottom]"))

    # A compass cut into the bridge marks the centre of the frozen channel.
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if dx == 0 or dz == 0 or abs(dx) == abs(dz) and abs(dx) <= 2:
                bp.set(C + dx, 7, 47 + dz, LAMP if dx == dz == 0 else BLUE)


def lintel_height(dx):
    return 25 - abs(dx) if abs(dx) < 8 else 7


def vestibule(bp):
    # A pointed barrel vault spans the north-south audience approach. Repeated ribs are
    # carried down to the floor; the narrow bay between each pair holds a lancet window.
    for z in range(6, 36):
        rib = z in (6, 13, 20, 27, 34, 35)
        for dx in range(-12, 13):
            x = C + dx
            edge = abs(dx)
            fill(bp, x, 3, z, x, 7, z, STONE)
            if edge < 10:
                # Leon walks between blue pinstripes on a reflective panelled floor.
                bp.set(x, 7, z, BLUE if edge == 7 or z in (13, 27) else ICE)
                if edge == 7 and z % 6 == 1:
                    bp.set(x, 7, z, LAMP)
            ceiling = 31 - edge
            if edge >= 10:
                fill(bp, x, 8, z, x, ceiling, z, ICE)
                if not rib:
                    fill(bp, x, 11, z, x, 16 - abs((z - 6) % 7 - 3), z, GLASS)
            bp.set(x, ceiling, z, STONE if rib else GLASS)
            if rib:
                bp.set(x, ceiling - 1, z, PILLAR if edge >= 9 else STONE)
            if z in (6, 34, 35):
                # Masonry above and around the pointed doorway on both ends.
                for y in range(lintel_height(dx) + 1, ceiling + 1):
                    material = STONE if y <= lintel_height(dx) + 2 or edge >= 10 else ICE
                    bp.set(x, y, z, material)
        if rib:
            for x in (C - 9, C + 9):
                fill(bp, x, 8, z, x, 22, z, PILLAR)
                bp.set(x, 12, z, LAMP)
    # Crystal clusters grow below the windows of the passage, leaving the axial route open.
    for sign in (-1, 1):
        for z in (10, 17, 24, 31):
            shard(bp, C + sign * 9, z, 8, 1, 4, -sign)
    # The arch picks up the violet of the reception hall's elevated lights.
    for dx in range(-3, 4):
        for dy in range(-3 + abs(dx), 4 - abs(dx)):
            if abs(dx) + abs(dy) < 2:
                bp.set(C + dx, 28 + dy, 34, LAMP)
                bp.set(C + dx, 28 + dy, 35, M("purple_stained_glass"))
            else:
                bp.set(C + dx, 28 + dy, 35, STONE)
    # A small snow terrace receives visitors passing the northern arch.
    for z in range(1, 7):
        y = min(7, 3 + z)
        width = min(8, 2 + z)
        for dx in range(-width, width + 1):
            fill(bp, C + dx, 2, z, C + dx, y - 1, z, ICE)
            bp.set(C + dx, y, z, stair("quartz", "south") if 1 <= z <= 4 else STONE)
    for dx in range(-2, 3):
        fill(bp, C + dx, 2, 0, C + dx, 3, 0, SNOW)
    bp.set(C + 1, 3, 0, M("gravel"))


def spire(bp, cx, cz, radius, shoulder, tip):
    # The octagonal stone core breaks through the ice on its eight corners. Staggered
    # horizontal ledges read as stone courses behind the long blue facets.
    for y in range(3, tip + 1):
        if y < shoulder:
            r = radius + int(y in (7, shoulder - 2, shoulder - 1))
        else:
            r = math.ceil((radius + 1) * (tip - y) / (tip - shoulder))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) > r + r // 2:
                    continue
                if y < shoulder:
                    state = ICE
                    if y in (7, shoulder - 2, shoulder - 1) or abs(dx) + abs(dz) >= r + r // 2:
                        state = STONE
                    if (dx == 0 or dz == 0) and 12 <= y < shoulder - 3:
                        state = LAMP if y % 6 == 0 else GLASS
                else:
                    state = BLUE if dx < 0 else ICE
                    if dx == 0 or dz == 0:
                        state = STONE
                bp.set(cx + dx, y, cz + dz, state)
    bp.set(cx, tip, cz, LAMP)


def build(bp):
    # Keep ice recognisable in this repo's schematic renderer.
    for key, rgb in (("packed_ice", (164, 198, 240)), ("blue_ice", (105, 150, 219))):
        if not any(existing == key for existing, _ in blueprint._COLORS):
            blueprint._COLORS.append((key, rgb))
    fill_air(bp, 0)
    snowfield(bp)
    crossing(bp)
    vestibule(bp)
    for sign in (-1, 1):
        spire(bp, C + sign * 17, 26, 6, 30, 49)
        spire(bp, C + sign * 15, 10, 4, 21, 35)
        # The establishing shot frames the castle between curving blades of ice.
        for dx, z, r, height, lean in ((34, 28, 4, 22, 8), (27, 34, 3, 14, 4),
                                        (36, 35, 2, 10, 3), (28, 55, 4, 19, 8),
                                        (19, 59, 2, 8, 3)):
            shard(bp, C + sign * dx, z, 3, r, height, -sign * lean)
    light_pass(bp, lambda x, y, z: abs(x - C) <= 10 and 6 <= z <= 35 and y < 31 - abs(x - C),
               8, lambda x, y, z: M("lantern[hanging=false]"), label="frost_palace")
    # Explicit air under the structure keeps its passage open. The placer cuts up to
    # the sky automatically, including above survey grade in empty footprint columns.
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            for y in reversed(range(SIZE[1])):
                if bp.blocks[x, y, z] != AIR:
                    break
                del bp.blocks[x, y, z]
            # A feathered snow lip lies directly on the land; never put air beneath it.
            for y in range(SIZE[1]):
                if bp.blocks.get((x, y, z)) != AIR:
                    break
                del bp.blocks[x, y, z]
