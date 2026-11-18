"""Golden City of El Dorado — Leon Cromwell's audience court.

SIZE (81, 39, 83), south approach anchor (40, 4, 74), PARTS split at z 28 and 56.
Episode 87 (design/lore/el_dorado.md) shows a high gilded throne and a red runner up broad pale
steps. The light novel's white central castle and six-pointed city plan inform the quartz walls and
paving motif. A glazed arcade bay holds the rose garden’s silver-framed mirror from episode 87.
The amber lantern roof, court layout and reflecting canals are our interpretation.
Materials: quartz, sandstone, polished blackstone, gold, waxed copper, coloured glass and wool.
"""
from _dwargon_lib import AIR, noise2, rnd
from _lords_lib import M, clear, fill, light_pass, rect_ring, stair
from _sites_lib import line
from _town_lib import lantern_floor

SIZE = (81, 39, 83)
PARTS = [0, 28, 56]
G = 3
CX, CZ = 40, 25
STONE = M("smooth_sandstone")
ASHLAR = M("cut_sandstone")
WHITE = M("smooth_quartz")
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
                bp.set(x, G, z, block if block == GOLD else WHITE)
            if r in (16, 17):
                for y in range(4, 17):
                    window = (abs(dx) in (4, 5, 6) or abs(dz) in (4, 5, 6)) and 8 <= y <= 13
                    bp.set(x, y, z, GLASS if window else (GOLD if y in (6, 15) else WHITE))
            # Broad overhanging octagonal eaves below the faceted lantern roof.
            if r <= 19:
                bp.set(x, 16, z, WHITE)
                bp.set(x, 17, z, GOLD if r == 19 else WHITE)
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
    # Episode 87: the delegation ascends a broad red-and-gold stair to a high-backed throne.
    fill(bp, 31, 4, 11, 49, 8, 17, WHITE)
    fill(bp, 37, 8, 11, 43, 8, 17, M("red_wool"))
    for step in range(5):
        z, y = 26 - 2 * step, 4 + step
        fill(bp, 31, 4, z-1, 49, y, z, WHITE)
        for x in range(31, 50):
            offset = abs(x - CX)
            surface = M("red_wool") if offset <= 3 else GOLD if offset == 4 else WHITE
            tread = "red_nether_brick" if offset <= 3 else "smooth_sandstone" if offset == 4 else "smooth_quartz"
            bp.set(x, y, z-1, surface)
            bp.set(x, y, z, stair(tread, "north"))
        for x in (31, 49):
            bp.set(x, y+1, z-1, LAMP if step in (0, 2, 4) else GOLD)
            bp.set(x, y+1, z, stair("smooth_sandstone", "north"))
    fill(bp, 37, G, 27, 43, G, 39, M("red_wool"))
    for x in (36, 44):
        fill(bp, x, G, 27, x, G, 39, GOLD)

    # Royal upholstery rises inside a pointed gold frame; the side posts carry the arms.
    for dx in range(-2, 3):
        top = 15 - abs(dx)
        x = CX + dx
        fill(bp, x, 9, 12, x, top, 12, GOLD)
        if abs(dx) < 2:
            fill(bp, x, 9, 12, x, top-1, 12, M("purple_wool"))
    fill(bp, 39, 9, 13, 41, 9, 14, M("crimson_planks"))
    for x in (38, 42):
        fill(bp, x, 9, 13, x, 10, 14, GOLD)
    # Pointed gold ornaments on pale wall panels flank the seat in the wide audience shot.
    for centre in (34, 46):
        for x in range(centre-1, centre+2):
            face_z = max(z for z in range(6, 15) if octagon(x-CX, z-CZ) >= 16) + 1
            if x == centre:
                fill(bp, x, 10, face_z, x, 13, face_z, GOLD)
            else:
                bp.set(x, 12, face_z, M("chiseled_quartz_block"))
    for z in (29, 36):
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


def rose_gallery(bp):
    """A walk-in glazed bay at the north end of the east arcade; the oval faces south."""
    # Replace just this length of solid hipped roof with one layer of rising glass
    # between three gilt transverse ribs. Carry the two original lanterns up to it.
    for z in range(30, 45):
        for x in range(64, 75):
            height = 12 + min(x-64, 74-x, 4)
            clear(bp, x, 12, z, x, 16, z)
            bp.set(x, height, z, GOLD if z in (30, 37, 44) else M("glass"))
    for z in (33, 39):
        fill(bp, 69, 12, z, 69, 15, z, M("chain[axis=y]"))

    # Roses grow from actual soil alongside the pillars. Flowering leaves carry their
    # colour across the higher trellis; both halves of each vanilla rose bush are present.
    for x in (66, 72):
        for z in range(32, 44):
            bp.set(x, G, z, M("rooted_dirt"))
            if z % 3 == 0:
                bp.set(x, G+1, z, M("rose_bush[half=lower]"))
                bp.set(x, G+2, z, M("rose_bush[half=upper]"))
        for z in (31, 37, 43):
            fill(bp, x, 4, z, x, 8, z, M("oak_fence"))
        fill(bp, x, 9, 31, x, 9, 43, M("flowering_azalea_leaves[persistent=true]"))
        for z in (32, 36, 38, 42):
            bp.set(x, 8, z, M("azalea_leaves[persistent=true]"))

    # A blue glass oval with a lavender backing holds its colour when seen in daylight.
    # Chiselled cheeks and flared white feet suggest the mirror's carved silver frame.
    for y, radius in ((6, 1), (7, 2), (8, 2), (9, 2), (10, 1), (11, 0)):
        for dx in range(-radius, radius+1):
            x = 69 + dx
            bp.set(x, y, 31, WHITE)
            if abs(dx) == radius or y == 6:
                bp.set(x, y, 32, M("chiseled_quartz_block"))
            else:
                bp.set(x, y, 31, M("light_blue_terracotta"))
                glass = "white_stained_glass" if (dx, y) == (-1, 9) else "light_blue_stained_glass"
                bp.set(x, y, 32, M(glass))
    bp.set(69, 5, 32, M("quartz_pillar"))
    fill(bp, 68, 4, 31, 70, 4, 32, WHITE)
    bp.set(68, 5, 32, stair("quartz", "east"))
    bp.set(70, 5, 32, stair("quartz", "west"))


def gardens(bp):
    # Paired reflecting pools, each with a transverse bridge connecting an arcade.
    for x0 in (18, 48):
        fill(bp, x0+1, G-1, 48, x0+13, G-1, 70, ASHLAR)
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


def precinct_distance(x, z):
    """Horizontal distance outside the hall, paved court, planters and gate plinths."""
    court = max(6 - x, x - 74, 28 - z, z - 72)
    hall_edge = octagon(x - CX, z - CZ) - 20
    trees = max(min(abs(x - 7), abs(x - 73)) - 2, min(abs(z - k) for k in (13, 22, 73)) - 2)
    plinths = max(min(abs(x - 30), abs(x - 50)), abs(z - 75)) - 2
    return min(court, hall_edge, trees, plinths)


def grounds(bp):
    """One surveyed surface under the architecture; broken turf shoulders and a worn approach."""
    lit = set()
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            grain = rnd(x, 0, z, 74)
            distance = precinct_distance(x, z)
            wear = max(0, z - 74)
            track_centre = CX + min(max(0, wear - 2), max(0, 8 - wear)) // 2
            track_edge = abs(x - track_centre) - max(1, 5 - wear * 0.48)
            on_track = z >= 73 and track_edge <= 0
            if z >= 73:
                distance = min(distance, track_edge)
            verge = 1.5 + 4 * noise2(x, z, 5, 14)
            if distance > verge:
                continue
            # The first column outside the box may be G-1 or G+1 after terrain fitting.
            # Keep the walking lane at G and let the verge descend on either side.
            y = G - int(distance > 1.5)
            if distance > 3.5:
                y -= 1
            earth = noise2(x, z, 4, 28)
            floor = M("coarse_dirt" if earth > 0.64 else "grass_block")
            court = 6 <= x <= 74 and 28 <= z <= 72
            if court:
                floor = DARK if x in (34, 46) else STONE
            if on_track:
                if wear < 2 or grain > (wear - 1) / 8 + max(0, track_edge + 1) * 0.3:
                    floor = STONE
                else:
                    floor = M("dirt_path" if track_edge < -0.5 and z < SIZE[2]-1 else "coarse_dirt")
            if z in (45, 73) and abs(x-CX) < 6:
                floor = GOLD
            if z < 73 and distance <= 0 and x % 12 == 4 and z % 12 == 4:
                floor = LAMP
            bp.set(x, y, z, floor)
            # Leave unclaimed columns out of the NBT, including air. The placer can supply
            # local filler immediately beneath this surface according to its terrain survey.
            for yy in range(y+1, SIZE[1]):
                bp.blocks[x, yy, z] = AIR
            if distance <= 0:
                lit.add((x, z))
            elif floor == M("grass_block") and grain < 0.17:
                bp.set(x, y+1, z, M("short_grass"))
    return lit


def build(bp):
    lit = grounds(bp)
    # A small paving inlay recalls the city's six points within the single palace precinct.
    for tip in (-1, 1):
        triangle = [(CX, 59 + 6*tip), (CX-5, 59 - 3*tip), (CX+5, 59 - 3*tip)]
        for a, b in zip(triangle, triangle[1:] + triangle[:1]):
            for x, z in line(*a, *b):
                bp.set(x, G, z, GOLD)
    gardens(bp)
    hall(bp)
    for x0 in (7, 65):
        gallery(bp, x0)
    rose_gallery(bp)
    # Gold-banded paired obelisks frame the entrance without covering the view.
    for x in (30, 50):
        for y, radius, material in ((4, 2, DARK), (5, 2, ASHLAR), (6, 1, GOLD)):
            fill(bp, x-radius, y, 75-radius, x+radius, y, 75+radius, material)
        fill(bp, x-1, 7, 74, x+1, 11, 76, ASHLAR)
        fill(bp, x, 12, 75, x, 14, 75, GOLD)
        bp.set(x, 15, 75, LAMP)
        bp.set(x, 16, 75, M("end_rod[facing=up]"))
    # Low lights in the inner plinth corners leave the whole incoming road unobstructed.
    for x in (32, 48):
        bp.set(x, G+1, 77, LAMP)
    light_pass(bp, lambda x, y, z: (x, z) in lit, 1, lambda x, y, z: lantern_floor(), label="el_dorado")
