"""Golden City of El Dorado — Leon Cromwell's audience court.

SIZE (81, 39, 83), south approach anchor (40, 4, 74), PARTS split at z 28 and 56.
The fan-map record in design/lore/world.md and its Golden City / WN:El Dorado sources identify
Leon's seat and the continent's precious metals. The copper-ribbed amber lantern above the throne,
stepped octagonal hall, shaded galleries and reflecting canals are our interpretation. Materials:
cut and smooth sandstone, polished blackstone, waxed cut copper, gold, amber glass and glowstone.
"""
from _lords_lib import M, clear, fill, fill_air, light_pass, rect_ring, stair
from _town_lib import lantern_floor

SIZE = (81, 39, 83)
PARTS = [0, 28, 56]
G = 3
CX, CZ = 40, 25
STONE = M("smooth_sandstone")
ASHLAR = M("cut_sandstone")
DARK = M("polished_blackstone")
GOLD = M("gold_block")
COPPER = M("waxed_cut_copper")
GLASS = M("yellow_stained_glass")
LAMP = M("glowstone")


def octagon(x, z):
    """Radius in an octagon with cardinal and diagonal faces of comparable size."""
    return max(abs(x), abs(z), (abs(x) + abs(z) + 1) * 5 // 7)


def hall(bp):
    for x in range(CX - 20, CX + 21):
        for z in range(CZ - 20, CZ + 21):
            dx, dz = x - CX, z - CZ
            r = octagon(dx, dz)
            if r > 20:
                continue
            bp.set(x, G, z, DARK if r in (19, 20) else ASHLAR)
            if r <= 17:
                block = GOLD if r in (8, 15) or (abs(dx) == abs(dz) and r <= 8) else STONE
                bp.set(x, G, z, block)
            if r in (16, 17):
                for y in range(4, 17):
                    window = (abs(dx) in (4, 5, 6) or abs(dz) in (4, 5, 6)) and 8 <= y <= 13
                    bp.set(x, y, z, GLASS if window else (GOLD if y in (6, 15) else ASHLAR))
            # Broad overhanging octagonal eaves below the faceted lantern roof.
            if r <= 19:
                bp.set(x, 16, z, DARK)
                bp.set(x, 17, z, GOLD if r == 19 else COPPER)
            if r <= 15:
                for y in range(18, 22):
                    if r == 15:
                        bp.set(x, y, z, GOLD if (dx + dz) % 5 == 0 else GLASS)
                roof_y = 22 + (15 - r) * 2 // 3
                rib = min(abs(dx), abs(dz)) == 0 or abs(dx) == abs(dz)
                pane = M("orange_stained_glass") if r in (5, 10) else GLASS
                for y in range(roof_y - 1, roof_y + 1):
                    bp.set(x, y, z, COPPER if rib else (GOLD if r == 15 else pane))
                # Open the ceiling under the lantern to the amber panes overhead.
                if r < 15:
                    clear(bp, x, 16, z, x, 17, z)
    fill(bp, CX, 32, CZ, CX, 33, CZ, GOLD)
    bp.set(CX, 34, CZ, LAMP)
    bp.set(CX, 35, CZ, M("end_rod[facing=up]"))
    # High triple-recessed portal, open through both wall layers.
    for half, top in ((4, 9), (3, 11), (2, 12)):
        clear(bp, CX - half, 4, 40, CX + half, top, 43)
    # North dais, backed by a dark sunburst against the amber clerestory.
    fill(bp, 35, 4, 11, 45, 4, 16, DARK)
    fill(bp, 35, 4, 17, 45, 4, 17, stair("polished_blackstone", "north"))
    fill(bp, 37, 5, 12, 43, 5, 14, COPPER)
    fill(bp, 37, 5, 15, 43, 5, 15, stair("cut_copper", "north"))
    for x in range(36, 45):
        h = 10 - abs(CX - x)
        fill(bp, x, 6, 12, x, h, 12, GOLD)
    bp.set(40, 6, 13, stair("polished_blackstone", "north"))
    for x in (38, 42):
        bp.set(x, 6, 13, LAMP)
    for z in (20, 28, 36):
        for x in (32, 48):
            fill(bp, x-1, 4, z, x+1, 4, z, stair("sandstone", "north"))
            bp.set(x, G, z+2, LAMP)


def gallery(bp, x0):
    """A two-row arcade with corbelled openings and a low hipped roof."""
    for x in (x0, x0 + 8):
        for z in range(30, 68):
            bp.set(x, 11, z, GOLD)
            for end in range(30, 67, 6):
                distance = abs(end - z)
                if distance <= 2:
                    fill(bp, x, (4, 9, 10)[distance], z, x, 10, z,
                         M("quartz_pillar") if distance == 0 else ASHLAR)
            if (z - 30) % 6 == 0:
                bp.set(x, 4, z, DARK)
                bp.set(x, 10, z, GOLD)
    for k in range(5):
        fill(bp, x0 - 1 + k, 12 + k, 29 + k, x0 + 9 - k, 12 + k, 67 - k,
             GOLD if k in (0, 4) else M("dark_prismarine"))
    for z in range(33, 65, 6):
        bp.set(x0+4, 11, z, M("lantern[hanging=true]"))


def gardens(bp):
    # Paired reflecting pools, each with a transverse bridge connecting an arcade.
    for x0 in (18, 48):
        rect_ring(bp, x0, 47, x0+14, 71, G, DARK)
        fill(bp, x0+1, G, 48, x0+13, G, 70, M("water[level=0]"))
        for z in range(51, 70, 6):
            bp.set(x0+7, G-1, z, LAMP)
        fill(bp, x0, G, 58, x0+14, G, 60, STONE)
        for z in (57, 61):
            for x in (x0+1, x0+13):
                bp.set(x, G, z, DARK)
                bp.set(x, G+1, z, lantern_floor())
    for x in (7, 73):
        for z in (13, 22, 73):
            # Cypress silhouettes in stone planters, persistent leaves need no ticks.
            fill(bp, x-2, G, z-2, x+2, G, z+2, DARK)
            fill(bp, x, G+1, z, x, 9, z, M("jungle_log"))
            for y, radius in ((6, 2), (7, 2), (8, 2), (9, 1), (10, 1), (11, 0)):
                for i in range(-radius, radius+1):
                    for j in range(-radius, radius+1):
                        if abs(i)+abs(j) <= radius+1:
                            bp.set(x+i, y, z+j, M("jungle_leaves[persistent=true]"))


def build(bp):
    fill_air(bp, G+1)
    fill(bp, 0, 0, 0, 80, G-1, 82, M("sandstone"))
    for x in range(81):
        for z in range(83):
            floor = M("grass_block")
            if 6 <= x <= 74 and 28 <= z <= 72 or abs(x-CX) <= 5 and z >= 41:
                floor = DARK if x in (34, 46) else STONE
            if z in (45, 59, 73) and abs(x-CX) < 6:
                floor = GOLD
            if x % 12 == 4 and z % 12 == 4:
                floor = LAMP
            bp.set(x, G, z, floor)
    # An eight-rayed sun marks the crossing between the pools, visible from the portal.
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            distance = abs(dx) + abs(dz)
            if distance == 5 or distance <= 2 or (distance <= 4 and dx * dz == 0):
                bp.set(CX + dx, G, 59 + dz, GOLD if distance < 5 else DARK)
    gardens(bp)
    hall(bp)
    for x0 in (7, 65):
        gallery(bp, x0)
    # Gold-banded paired obelisks frame the entrance without covering the view.
    for x in (30, 50):
        for y, radius, material in ((4, 2, DARK), (5, 2, ASHLAR), (6, 1, GOLD)):
            fill(bp, x-radius, y, 75-radius, x+radius, y, 75+radius, material)
        fill(bp, x-1, 7, 74, x+1, 11, 76, ASHLAR)
        fill(bp, x, 12, 75, x, 14, 75, GOLD)
        bp.set(x, 15, 75, LAMP)
        bp.set(x, 16, 75, M("end_rod[facing=up]"))
    light_pass(bp, lambda x, y, z: True, G+1, lambda x, y, z: lantern_floor(), label="el_dorado")
