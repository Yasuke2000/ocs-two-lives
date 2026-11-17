"""The Spirit Corridor hall: where a soul waits between lives (master plan §1).

A round floating hall in the void. Ten pedestals stand for the ten Last Wishes; a halo hangs above the
centre, where souls arrive (structure centre = corridor 0 64 0, so the arrival point (15, 1, 15) stays
free). Placed by life/corridor.js at -15 64 -15.
"""

SIZE = (31, 22, 31)
C = 15  # centre on x and z


def build(bp):
    # Floor: quartz disc, calcite rim, amethyst ring, dark centre with a crying-obsidian ring.
    bp.disc(C, 0, C, 14.5, "minecraft:smooth_quartz")
    bp.disc(C, 0, C, 14.5, "minecraft:calcite", inner=13.5)
    bp.disc(C, 0, C, 10.5, "minecraft:amethyst_block", inner=9.5)
    bp.disc(C, 0, C, 3.5, "minecraft:polished_blackstone")
    bp.disc(C, 0, C, 3.5, "minecraft:crying_obsidian", inner=2.5)
    bp.set(C, 0, C, "minecraft:sea_lantern")
    for x, z in bp.around(C, C, 7, 8, start_deg=22.5):
        bp.set(x, 0, z, "minecraft:sea_lantern")

    # Ten pedestals, one per Last Wish, starting north.
    for x, z in bp.around(C, C, 11.5, 10, start_deg=-90):
        bp.set(x, 1, z, "minecraft:polished_deepslate")
        bp.set(x, 2, z, "minecraft:chiseled_quartz_block")
        bp.set(x, 3, z, "minecraft:soul_lantern")

    # Six quartz pillars on the rim, capped with end rods.
    for x, z in bp.around(C, C, 13, 6, start_deg=-60):
        bp.pillar(x, z, 1, 9, "minecraft:quartz_pillar")
        bp.set(x, 10, z, "minecraft:chiseled_quartz_block")
        bp.set(x, 11, z, "minecraft:end_rod")

    # The halo above the arrival point.
    bp.disc(C, 16, C, 6, "minecraft:amethyst_block", inner=5)
    for x, z in bp.around(C, C, 5.5, 8):
        bp.set(x, 16, z, "minecraft:sea_lantern")

    # Invisible wall: nobody falls into the void.
    for y in range(1, 21):
        bp.disc(C, y, C, 15, "minecraft:barrier", inner=13.6)
