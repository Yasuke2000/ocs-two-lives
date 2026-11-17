"""Trial of Vengeance: a dark duelling ground. The nemesis spawns at (0, 4); start (0, -12)."""
from _arena import SIZE, at, ring, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:polished_blackstone", "minecraft:polished_blackstone_bricks",
          "minecraft:gilded_blackstone", pillar="minecraft:red_nether_bricks", light="minecraft:shroomlight")
    ring(bp, 0, 6.5, "minecraft:crying_obsidian")
    ring(bp, 0, 10.5, "minecraft:red_nether_bricks")
    bp.disc(16, 0, 16, 2.5, "minecraft:obsidian")
    # Soul lanterns on posts around the ring.
    for x, z in bp.around(16, 16, 9, 8):
        bp.set(x, 1, z, "minecraft:polished_blackstone_wall")
        bp.set(x, 2, z, "minecraft:soul_lantern[hanging=false]")
    x, z = at(0, -12)
    bp.fill(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:chiseled_polished_blackstone")
