"""Trial of Dominion: a ranch. The herd starts in the north-west; the pen is x, z 8..14 with its gate at
(8, 11) facing east (trial_defs.js counts cows inside x, z 9..14). Bring three cows inside."""
from _arena import SIZE, at, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:grass_block", "minecraft:dark_oak_log[axis=y]", "minecraft:dark_oak_planks",
          pillar="minecraft:stripped_dark_oak_log[axis=y]", light="minecraft:glowstone")
    for i in range(8, 15):
        for x, z in (at(i, 8), at(i, 14), at(8, i), at(14, i)):
            bp.set(x, 1, z, "minecraft:oak_fence")
    x, z = at(8, 11)
    bp.set(x, 1, z, "minecraft:oak_fence_gate[facing=east]")
    x, z = at(10, 13)
    bp.set(x, 0, z, "minecraft:hay_block[axis=y]")
    x, z = at(12, 10)
    bp.set(x, 1, z, "minecraft:water_cauldron[level=3]")
    # A worn path from the herd to the pen.
    for i in range(-10, 8):
        x, z = at(i, i // 2 + 6)
        bp.set(x, 0, z, "minecraft:dirt_path")
    # A lookout for the one who rules them.
    bp.fill(3, 1, 26, 6, 3, 29, "minecraft:dark_oak_planks")
    bp.fill(3, 4, 26, 6, 4, 29, "minecraft:dark_oak_slab[type=bottom]")
    # Shade trees, hay and flowers, clear of the herd's start, the path and the pen.
    for dx, dz in ((11, -9), (1, 12)):
        x, z = at(dx, dz)
        bp.disc(x, 4, z, 2.5, "minecraft:oak_leaves[persistent=true]")
        bp.disc(x, 5, z, 1.5, "minecraft:oak_leaves[persistent=true]")
        bp.set(x, 6, z, "minecraft:oak_leaves[persistent=true]")
        bp.pillar(x, z, 1, 5, "minecraft:oak_log[axis=y]")
    for dx, dz in ((4, -13), (5, -13), (-13, 4)):
        x, z = at(dx, dz)
        bp.set(x, 1, z, "minecraft:hay_block[axis=x]")
    flowers = ["minecraft:dandelion", "minecraft:poppy", "minecraft:oxeye_daisy", "minecraft:azure_bluet"]
    for i, (dx, dz) in enumerate(((3, -4), (4, -5), (-3, 9), (6, 2), (-12, 1), (12, 3), (-4, -2), (9, -3))):
        x, z = at(dx, dz)
        bp.set(x, 1, z, flowers[i % len(flowers)])
