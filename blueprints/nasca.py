"""Nasca, the imperial guard's audience court. SIZE (85, 42, 79), PARTS along z.

The south processional entrance is on axis with the raised audience pavilion. Anchor
(42, 5, 66) faces the pavilion from the approach. Pale sandstone, polished andesite,
dark prismarine, crimson terracotta and waxed copper distinguish the imperial quarter.
References: the official Eastern Empire map entry, the novel's imperial guard and the
pack's political plate. This court is our interpretation. See design/lore/nasca.md.
"""
from _town_lib import M, Town, lantern_hung, slab, stair, wall_banner

SIZE = (85, 42, 79)
PARTS = [0, 27, 54]
G = 4
C = 42


def pier(t, x, z, bottom, top):
    t.fill(x - 1, bottom, z - 1, x + 1, bottom, z + 1, M("cut_sandstone"))
    t.fill(x, bottom + 1, z, x, top - 1, z, M("smooth_quartz"))
    t.fill(x - 1, top, z - 1, x + 1, top, z + 1, M("chiseled_sandstone"))


def pavilion(t):
    # Five north-facing stair risers give access to the raised hearing platform.
    t.fill(18, G, 7, 66, 9, 32, M("cut_sandstone"))
    t.pave(18, 7, 66, 32, "plaza", y=9)
    for i in range(5):
        z = 37 - i
        if i:
            t.fill(32, 5, z, 52, 4 + i, z, M("smooth_sandstone"))
        t.fill(32, 5 + i, z, 52, 5 + i, z, stair("smooth_sandstone", "north"))
    for x in (20, 28, 36, 48, 56, 64):
        for z in (9, 30):
            pier(t, x, z, 10, 17)
    for x in (20, 64):
        for z in (16, 23):
            pier(t, x, z, 10, 17)
    # Red rear screen, relief panels and three chairs for receiving delegations.
    t.fill(21, 10, 10, 63, 16, 10, M("red_terracotta"))
    for x in range(24, 62, 6):
        t.fill(x, 10, 11, x, 15, 11, M("chiseled_sandstone"))
        t.put(x, 13, 12, wall_banner("red", "south"))
    for x in (35, 42, 49):
        t.put(x, 10, 15, stair("dark_oak", "north"))
        t.put(x - 1, 10, 15, slab("smooth_sandstone"))
        t.put(x + 1, 10, 15, slab("smooth_sandstone"))
    t.fill(40, 10, 17, 44, 10, 29, M("red_carpet"))
    # A low hipped roof is interrupted by a daylight clerestory over the central bay.
    for i in range(5):
        t.ring(16 + i, 5 + i, 68 - i, 34 - i, 18 + i, 18 + i, M("dark_prismarine"))
        t.ring(17 + i, 6 + i, 67 - i, 33 - i, 18 + i, 18 + i, slab("dark_prismarine", "top"))
    t.fill(21, 22, 10, 63, 22, 29, M("dark_prismarine"))
    t.clear(33, 22, 14, 51, 22, 24)
    t.ring(32, 13, 52, 25, 23, 26, M("orange_stained_glass"))
    for x in range(32, 53, 4):
        for z in (13, 25):
            t.fill(x, 23, z, x, 26, z, M("cut_sandstone"))
    for i in range(6):
        t.fill(30 + i, 27 + i, 11 + i, 54 - i, 27 + i, 27 - i, M("dark_prismarine"))
    t.fill(36, 33, 17, 48, 33, 21, M("waxed_cut_copper"))
    t.fill(39, 34, 19, 45, 34, 19, slab("waxed_cut_copper"))
    # Paired gilt scrolls and a copper crest outline the raised roof against the sky.
    for x, direction in ((37, -1), (47, 1)):
        t.fill(x, 34, 19, x + 2 * direction, 34, 19, M("waxed_cut_copper"))
        t.fill(x + 2 * direction, 35, 19, x + 3 * direction, 35, 19, M("waxed_cut_copper"))
        t.put(x + 3 * direction, 36, 19, M("lightning_rod[facing=up]"))
    # Bottom-slab pan tiles cap every exposed roof shelf. Two underside crossbeams carry lamps.
    for z in (14, 25):
        t.fill(22, 21, z, 62, 21, z, M("dark_oak_planks"))
    for x in (24, 31, 53, 60):
        for z in (14, 25):
            t.put(x, 20, z, lantern_hung())


def standards(t):
    # Two crenellated gate piers carry matching copper bands and tall red standards.
    for x in (28, 56):
        t.fill(x - 3, 5, 57, x + 3, 6, 63, M("polished_andesite"))
        t.fill(x - 2, 7, 58, x + 2, 16, 62, M("cut_sandstone"))
        for y in (8, 14, 17):
            t.fill(x - 3, y, 57, x + 3, y, 63, M("waxed_cut_copper"))
        t.fill(x - 1, 18, 59, x + 1, 20, 61, M("dark_prismarine"))
        t.fill(x, 21, 60, x, 26, 60, M("dark_oak_fence"))
        for dx in range(1, 5):
            t.fill(x + dx, 24 - (dx == 4), 60, x + dx, 26 - (dx == 4), 60, M("red_wool"))
        # Standards hang below the guard towers' front cornice, visible on approach.
        t.fill(x - 1, 10, 63, x + 1, 14, 63, M("red_wool"))
        t.put(x, 12, 63, M("orange_wool"))
        t.put(x, 11, 63, M("yellow_wool"))
        t.put(x, 9, 63, M("red_wool"))
    for x0 in (9, 64):
        # Side galleries shelter the guard ranks. Slots overlook the parade lines.
        t.fill(x0, 5, 38, x0 + 12, 5, 54, M("smooth_sandstone"))
        for x in (x0 + 1, x0 + 11):
            for z in (39, 46, 53):
                pier(t, x, z, 6, 11)
        for i in range(4):
            t.fill(x0 - 1 + i, 12 + i, 36 + i, x0 + 13 - i, 12 + i, 56 - i, M("dark_prismarine"))
        for z in (40, 46, 52):
            t.put(x0 + 5, 11, z, lantern_hung())
        t.fill(x0 + 3, 5, 55, x0 + 9, 5, 55, stair("smooth_sandstone", "north"))


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    t.pave(8, 30, 76, 57, "plaza")
    t.pave(37, 55, 47, 78, "street")
    t.pave(7, 15, 16, 54, "cobble")
    t.pave(68, 15, 77, 54, "cobble")
    for z in (40, 45, 50, 55):
        for x in range(23, 62):
            if x % 5 in (0, 1) and abs(x - C) > 4:
                t.put(x, G, z, M("smooth_sandstone"))
    pavilion(t)
    standards(t)
    for (x, y, z), state in list(bp.blocks.items()):
        if y >= 12 and state in (M("dark_prismarine"), M("waxed_cut_copper")):
            if t.get(x, y + 1, z) == M("air"):
                t.put(x, y + 1, z, slab(state.split(":")[1]))
    for x in (24, 60):
        for z in (39, 49, 56):
            t.lamp(x, z, 2)
    for x in (35, 49):
        t.lamp(x, 68, 2)
    for x, z in ((7, 8), (76, 9), (12, 64), (71, 62), (21, 72), (65, 73)):
        t.tree(x, z, "oak", 6, 2)
    for x in (8, 75):
        t.fill(x, 5, 19, x, 5, 31, M("oak_leaves[persistent=true]"))
    for z in range(72, 79):
        for x in range(37, 48):
            wheel = abs(x - C) in (2, 3)
            t.put(x, G, z, M("coarse_dirt" if wheel else "grass_block" if abs(x - C) > 3 else "gravel"))
    t.light(lambda x, z: 7 <= x <= 77 and 5 <= z <= 63 or 35 <= x <= 49 and z >= 62)
    t.check_support()
