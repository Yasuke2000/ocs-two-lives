"""Trial of Knowledge: a library. The lectern at (0, 0) is where the Voice asks; start (0, 0) beside it."""
from _arena import SIZE, at, ring, shell

SIZE = SIZE


def build(bp):
    shell(bp, "minecraft:dark_oak_planks", "minecraft:bookshelf", "minecraft:dark_oak_log[axis=x]",
          pillar="minecraft:stripped_dark_oak_log[axis=y]", light="minecraft:glowstone")
    ring(bp, 0, 7.5, "minecraft:spruce_planks")
    ring(bp, 0, 3.5, "minecraft:polished_deepslate")
    # Free-standing shelves with reading desks between them.
    for x in (5, 9, 23, 27):
        bp.fill(x, 1, 5, x, 3, 12, "minecraft:bookshelf")
        bp.fill(x, 1, 20, x, 3, 27, "minecraft:bookshelf")
    for x, z in ((7, 16), (25, 16), (16, 6), (16, 26)):
        bp.set(x, 1, z, "minecraft:spruce_slab[type=top]")
        bp.set(x, 2, z, "minecraft:candle[candles=3,lit=true]")
    x, z = at(0, 0)
    bp.set(x, 1, z - 1, "minecraft:lectern[facing=south]")
    # Amethyst chandeliers hanging from the ceiling.
    for cx, cz in ((10, 10), (22, 10), (10, 22), (22, 22)):
        bp.set(cx, 15, cz, "minecraft:amethyst_block")
        bp.set(cx, 14, cz, "minecraft:chain[axis=y]")
        bp.set(cx, 13, cz, "minecraft:lantern[hanging=true]")
