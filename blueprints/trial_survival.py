"""Trial of Survival: a ruin. No weapons; poison, falling anvils and fire come at random. Start (0, 0).
Keep the floor flat and free of anvils and fire: the cleanup clears those."""
from _arena import SIZE, ring, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:cobblestone", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks",
          pillar="minecraft:mossy_cobblestone")
    ring(bp, 0, 8.5, "minecraft:mossy_cobblestone", width=2)
    for x in range(1, 32):
        for z in range(1, 32):
            if (x * 13 + z * 7) % 11 == 0:
                bp.set(x, 0, z, "minecraft:tuff")
    # Broken columns and rubble along the walls.
    for x, z, h in ((5, 5, 3), (27, 5, 1), (5, 27, 2), (27, 27, 4), (16, 3, 2), (3, 16, 1), (29, 16, 3)):
        bp.pillar(x, z, 1, h, "minecraft:cracked_stone_bricks")
    for x, z in ((8, 3), (24, 29), (3, 24), (29, 8)):
        bp.set(x, 1, z, "minecraft:mossy_stone_brick_slab[type=bottom]")
