"""Trial of Strength: a colosseum. Four waves spawn at (+-10, 10), (+-10, -2), (0, 12); start (0, -12)."""
from _arena import SIZE, at, ring, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:polished_andesite", "minecraft:stone_bricks", "minecraft:chiseled_stone_bricks",
          pillar="minecraft:polished_andesite")
    # Sand fighting pit inside a stone ring, like an old arena floor.
    bp.disc(16, 0, 16, 11.5, "minecraft:smooth_sandstone")
    ring(bp, 0, 11.5, "minecraft:stone_bricks")
    ring(bp, 0, 6.5, "minecraft:cut_sandstone")
    # Spectator steps along the north and south walls.
    for x in range(3, 30):
        bp.set(x, 1, 1, "minecraft:stone_brick_stairs[facing=south]")
        bp.set(x, 1, 31, "minecraft:stone_brick_stairs[facing=north]")
    # Weapon racks on the side walls.
    for z in (8, 16, 24):
        for x in (1, 31):
            bp.set(x, 1, z, "minecraft:iron_block")
            bp.set(x, 2, z, "minecraft:iron_bars")
    x, z = at(0, -12)
    bp.fill(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:chiseled_stone_bricks")
