"""Ferry and Toll House. SIZE 79 x 16 x 77; anchor (10, 5, 35) on the western towpath.

A lined water cut links two reed beds. Oak, spruce, gravel, clay and fieldstone.
Reedham's chain ferry supplies the crossing principle; arrangements and banks are original.
See design/lore/mortal_ferry.md for the references and survey contract.
"""

import math

from blueprint import Blueprint

SIZE = (79, 16, 77)
PARTS = [0, 25, 50]
MC = "minecraft:"


def landing(bp):
    # Fixed landing stages flank the tied-up punt. The continuous decking makes the crossing walkable.
    bp.fill(15, 4, 14, 21, 4, 18, MC + "spruce_planks")
    bp.fill(26, 4, 14, 31, 4, 18, MC + "spruce_planks")
    bp.fill(22, 3, 13, 25, 3, 19, MC + "dark_oak_planks")
    bp.fill(22, 4, 13, 25, 4, 19, MC + "oak_planks")
    for z, direction in ((12, "south"), (20, "north")):
        bp.fill(22, 4, z, 25, 4, z, MC + f"dark_oak_stairs[facing={direction}]")
    for x in (19, 28):
        for z in (13, 19):
            bp.pillar(x, z, 1, 6, MC + "stripped_oak_log")
            bp.set(x, 7, z, MC + "lantern")
    bp.fill(20, 5, 13, 27, 5, 13, MC + "chain[axis=x]")

    # Scale at the front counter, two open doorways, and a gabled roof with a small chimney.
    bp.fill(2, 5, 2, 14, 9, 13, MC + "air")
    bp.fill(3, 4, 3, 13, 4, 12, MC + "cobblestone")
    bp.box(3, 5, 3, 13, 8, 12, MC + "white_terracotta")
    bp.fill(4, 5, 4, 12, 9, 11, MC + "air")
    for x in (3, 8, 13):
        for z in (3, 12):
            bp.pillar(x, z, 5, 9, MC + "stripped_oak_log")
    for z in (7, 8):
        bp.set(13, 7, z, MC + "glass_pane")
    bp.fill(5, 5, 12, 6, 7, 12, MC + "air")
    bp.fill(9, 6, 12, 12, 7, 12, MC + "air")
    bp.fill(9, 5, 12, 12, 5, 12, MC + "spruce_planks")
    bp.set(11, 6, 12, MC + "light_weighted_pressure_plate")
    bp.fill(5, 5, 5, 6, 5, 5, MC + "barrel")
    bp.set(6, 6, 5, MC + "lantern")
    bp.set(11, 5, 5, MC + "lectern[facing=south]")
    bp.fill(3, 9, 3, 13, 9, 12, MC + "oak_planks")
    bp.fill(3, 10, 3, 13, 14, 12, MC + "air")
    for dx in range(7):
        for x, facing in ((2 + dx, "east"), (14 - dx, "west")):
            if dx:
                for z in (3, 12):
                    bp.fill(x, 10, z, x, 9 + dx, z, MC + "spruce_planks")
            bp.fill(x, 9 + dx, 2, x, 9 + dx, 13, MC + f"spruce_stairs[facing={facing}]")
    bp.fill(8, 15, 2, 8, 15, 13, MC + "spruce_slab")
    bp.pillar(11, 5, 9, 14, MC + "bricks")
    bp.set(8, 8, 6, MC + "lantern[hanging=true]")
    bp.set(10, 8, 11, MC + "lantern[hanging=true]")

    bp.set(8, 10, 7, MC + "lantern")
    bp.set(22, 5, 14, MC + "grindstone[face=floor,facing=east]")
    bp.set(25, 5, 18, MC + "barrel")


def channel(z):
    return 41 + round(7 * math.sin((z - 38) / 12.0))


def build(bp):
    # The towpath tracks the west shoulder of a sinuous, banked channel between two culverts.
    for z in range(77):
        center = channel(z)
        width = min(5 + round(1.5 * abs(math.sin((z - 38) / 13))), z - 3, 73 - z)
        for x in range(79):
            delta = x - center
            road_z = 38 + round(4 * math.sin((x - 42) / 18))
            street = abs(z - road_z) <= 2
            verge = abs(z - road_z) <= 4 + round(math.sin(x / 6))
            bank = abs(delta) <= max(0, width) + 6 and 1 <= z <= 75
            yard = ((x - 28) / 16) ** 2 + ((z - 31) / 15) ** 2 < 1
            slip = 14 <= z <= 22 and -17 <= delta <= -4
            if not (bank or verge or yard or slip):
                continue
            if abs(delta) <= width:
                bp.set(x, 1, z, MC + ("clay" if (x + z) % 7 else "gravel"))
                bp.pillar(x, z, 2, 3, MC + "water")
                bp.pillar(x, z, 4, 8, MC + "air")
                continue
            towpath = abs(delta + max(width, 0) + 3) <= 1
            height = 4 + int(bank and delta > width + 3 and not street and not yard)
            bp.pillar(x, z, 1, height - 1, MC + "dirt")
            surface = "gravel" if street else "coarse_dirt" if towpath or slip else "grass_block"
            bp.set(x, height, z, MC + surface)
            bp.pillar(x, z, height + 1, 9, MC + "air")
            if width >= 2 and delta == width + 1 and z % 7 in (1, 2) and not street:
                bp.set(x, 3, z, MC + "sand")
                bp.pillar(x, z, 4, 5 + z % 2, MC + "sugar_cane")
    landing_bp = Blueprint("toll_house_and_punt", (41, 16, 33))
    landing(landing_bp)
    for (x, y, z), state in landing_bp.blocks.items():
        bp.set(x + 18, y, z + 22, state)
    for z in (2, 74):
        cx = channel(z)
        bp.fill(cx - 3, 4, z, cx + 3, 6, z, MC + "mossy_cobblestone")
        bp.fill(cx - 1, 4, z, cx + 1, 5, z, MC + "iron_bars")
        bp.fill(cx - 3, 7, z, cx + 3, 7, z, MC + "cobblestone_slab")
    # A repair slip beside the north reach, with parallel timber rollers and a stack of planking.
    for z in (16, 18, 20):
        cx = channel(z)
        bp.fill(cx - 14, 5, z, cx - 8, 5, z, MC + "stripped_oak_log[axis=x]")
    cx = channel(17)
    bp.fill(cx - 16, 5, 14, cx - 14, 5, 16, MC + "spruce_planks")
    for z in (10, 25, 51, 66):
        x = channel(z) - 10
        bp.pillar(x, z, 4, 6, MC + "oak_log")
        bp.set(x, 7, z, MC + "lantern")

    # Low field boundaries converge on the approaches and leave gaps for the repair track.
    for x0, x1 in ((2, 10), (13, 17), (58, 66), (69, 76)):
        for x in range(x0, x1 + 1):
            z = 38 + round(4 * math.sin((x - 42) / 18)) + 4
            bp.set(x, 4, z, MC + "grass_block")
            bp.set(x, 5, z, MC + ("mossy_cobblestone" if x in (x0, x1) else "oak_leaves[persistent=true]"))
