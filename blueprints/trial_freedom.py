"""Trial of Freedom: a jump course over a pit. The course is at y=PIT (the trial's floor level); the pit
floor at y=0 is 6 blocks lower. Start pad (0, -13), COURSE blocks, gold goal (0, 12..14).
Falling below the course sends the player back to the start (trial_defs.js)."""
from _arena import at, shell

SIZE = (33, 23, 33)
PIT = 6
COURSE = [(0, 0, -9), (0, 0, -6), (1, 1, -4), (1, 1, -1), (0, 2, 1), (0, 2, 4), (-1, 1, 7), (0, 0, 10)]


def build(bp):
    shell(bp, "minecraft:light_blue_concrete", "minecraft:white_concrete", "minecraft:light_gray_concrete",
          wall_height=PIT + 3, pillar="minecraft:quartz_pillar[axis=y]", ceiling=22)
    # A cloud sea in the pit: a fall looks like landing in the sky.
    for cx, cz, r in ((7, 8, 3), (24, 6, 2.5), (12, 22, 3.5), (26, 24, 3), (16, 14, 2), (5, 27, 2)):
        bp.disc(cx, 1, cz, r, "minecraft:white_wool")
        bp.disc(cx, 2, cz, r - 1.5, "minecraft:white_wool")
    x, z = at(0, -13)
    bp.fill(x - 1, PIT, z - 2, x + 1, PIT, z + 1, "minecraft:quartz_block")
    for dx, dy, dz in COURSE:
        cx, cz = at(dx, dz)
        bp.set(cx, PIT + dy, cz, "minecraft:quartz_pillar[axis=y]")
    x, z = at(0, 13)
    bp.fill(x - 1, PIT, z - 1, x + 1, PIT, z + 1, "minecraft:gold_block")
    # Light markers beside every other jump.
    for dx, dy, dz in COURSE[::2]:
        cx, cz = at(dx + 2, dz)
        bp.set(cx, PIT + dy + 2, cz, "minecraft:end_rod[facing=up]")
