"""Test hut: a 5x5 stone hut for the generic build placer (life/builds.js, tests/ingame/builds.rcon).

Placed by design/builds/test_hut.toml in the Spirit Corridor dimension far from the trial arenas (flat void,
ground = "fixed"), so the test needs no terrain. Layer 0 is the floor (ground layer), layers 1-3 the walls with
a door gap in the south wall, layer 4 the roof. Anchor (the doorstep inside): blueprint (2, 1, 2).
Not a canon location: delete design/builds/test_hut.toml (and this file) once the placer is trusted.
"""

SIZE = (5, 6, 5)
AIR = "minecraft:air"


def build(bp):
    bp.fill(0, 0, 0, 4, 0, 4, "minecraft:stone_bricks")
    bp.box(0, 1, 0, 4, 3, 4, "minecraft:oak_planks")
    bp.fill(1, 1, 1, 3, 3, 3, AIR)
    for x, z in ((0, 0), (4, 0), (0, 4), (4, 4)):
        bp.pillar(x, z, 1, 3, "minecraft:oak_log[axis=y]")
    bp.fill(2, 1, 4, 2, 2, 4, AIR)  # door gap, south wall
    bp.fill(0, 4, 0, 4, 4, 4, "minecraft:spruce_planks")
    bp.set(2, 3, 2, "minecraft:lantern[hanging=true]")
    bp.set(2, 4, 2, "minecraft:spruce_planks")
    bp.fill(0, 5, 0, 4, 5, 4, AIR)
