"""Trial of Hunger: a ruined storehouse. Food lies around the edges (+-10..13); start (0, 0)."""
from _arena import SIZE, at, ring, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:coarse_dirt", "minecraft:mud_bricks", "minecraft:packed_mud",
          pillar="minecraft:stripped_oak_log[axis=y]", light="minecraft:jack_o_lantern[facing=north]")
    ring(bp, 0, 9.5, "minecraft:rooted_dirt", width=2)
    bp.disc(16, 0, 16, 3.5, "minecraft:mud_bricks")
    # Empty barrels, sacks (hay) and compost along the walls; nothing edible here.
    for x in range(3, 30, 3):
        bp.set(x, 1, 1, "minecraft:barrel[facing=up]")
        bp.set(x, 1, 31, "minecraft:hay_block[axis=x]")
    for z in range(4, 29, 4):
        bp.set(1, 1, z, "minecraft:composter")
        bp.set(31, 1, z, "minecraft:barrel[facing=west]")
    x, z = at(0, 0)
    bp.set(x, 0, z, "minecraft:jack_o_lantern[facing=north]")
