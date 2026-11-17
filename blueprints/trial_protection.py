"""Trial of Protection: a farmyard. The ward (villager) stands on the hay at (0, 0); start (0, -4).
Attackers come from the corners (+-12, +-12): keep those open."""
from _arena import SIZE, at, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:grass_block", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks",
          pillar="minecraft:spruce_log[axis=y]", light="minecraft:glowstone")
    # Dirt paths from the corners to the centre: the routes the attackers take.
    for i in range(-12, 13):
        for x, z in (at(i, i), at(i, -i)):
            bp.set(x, 0, z, "minecraft:dirt_path")
    x, z = at(0, 0)
    bp.fill(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:hay_block[axis=y]")
    # Low fence ring around the ward with a gap on each side.
    for d in range(-3, 4):
        if d == 0:
            continue
        for x, z in (at(d, -3), at(d, 3), at(-3, d), at(3, d)):
            bp.set(x, 1, z, "minecraft:spruce_fence")
    # A field and a hut: a home worth defending.
    bp.fill(2, 0, 26, 7, 0, 30, "minecraft:farmland[moisture=7]")
    bp.fill(2, 1, 26, 7, 1, 30, "minecraft:wheat[age=7]")
    bp.fill(25, 1, 25, 30, 4, 30, "minecraft:oak_planks")
    bp.fill(26, 1, 26, 29, 3, 29, "minecraft:air")
    bp.fill(27, 1, 25, 27, 2, 25, "minecraft:air")
    x, z = at(0, -4)
    bp.set(x, 0, z, "minecraft:coarse_dirt")
