"""Trial of Deceit: a dark gallery watched by nine Watchers (rows z = -4, 3, 10; x = -8, 0, 8).
Start (0, -14); the emerald exit at (0, 13..15). Only distance decides whether you are seen, so the decor
here is mood, not cover."""
from _arena import SIZE, at, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:deepslate_tiles", "minecraft:deepslate_bricks", "minecraft:polished_deepslate",
          pillar="minecraft:chiseled_deepslate", light="minecraft:verdant_froglight[axis=y]")
    # Sculk creeping over the floor and hanging lanterns: an uneasy place.
    for x in range(1, 32):
        for z in range(1, 32):
            if (x * 11 + z * 5) % 13 == 0:
                bp.set(x, 0, z, "minecraft:sculk")
    for x, z in ((6, 8), (26, 8), (6, 24), (26, 24), (16, 22)):
        bp.pillar(x, z, 9, 15, "minecraft:chain[axis=y]")
        bp.set(x, 8, z, "minecraft:soul_lantern[hanging=true]")
    x, z = at(0, 14)
    bp.fill(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:emerald_block")
    x, z = at(0, -14)
    bp.fill(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:polished_deepslate")
