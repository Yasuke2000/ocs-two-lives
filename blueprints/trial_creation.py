"""Trial of Creation: a workshop. The crafting table at (0, 0); parts are dropped around (+-10..13);
start (0, -6). No anvils or fire here: the trial cleanup clears those."""
from _arena import SIZE, at, ring, shell

SIZE = SIZE
STATIONS = ["minecraft:smithing_table", "minecraft:loom", "minecraft:cartography_table",
            "minecraft:fletching_table", "minecraft:stonecutter[facing=north]", "minecraft:barrel[facing=up]"]


def build(bp):
    shell(bp, "minecraft:oak_planks", "minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=x]",
          pillar="minecraft:spruce_log[axis=y]", light="minecraft:glowstone")
    ring(bp, 0, 4.5, "minecraft:polished_andesite")
    x, z = at(0, 0)
    bp.set(x, 1, z, "minecraft:crafting_table")
    # Workbenches along the walls.
    for i, x in enumerate(range(4, 30, 4)):
        bp.set(x, 1, 1, STATIONS[i % len(STATIONS)])
        bp.set(x, 1, 31, STATIONS[(i + 3) % len(STATIONS)])
    for z in range(6, 28, 5):
        bp.set(1, 1, z, "minecraft:bookshelf")
        bp.set(31, 1, z, "minecraft:barrel[facing=west]")
