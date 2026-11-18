"""Ruined Border Keep. SIZE 75 x 22 x 73; anchor (36, 4, 63) on the southern approach.

Fieldstone and cracked brick curtain, oak repairs and a roofless watch block.
Norham Castle's surviving keep and inner ward are the historical reference.
See design/lore/mortal_keep.md for the jar inventory and placement notes.
"""

import math

from blueprint import Blueprint

SIZE = (75, 22, 73)
PARTS = [0, 25, 50]
MC = "minecraft:"


def masonry(x, y, z):
    seed = (x * 17 + z * 13 + y * 11 + x * z) % 23
    return MC + ("mossy_cobblestone" if seed < 3 and y < 9 else
                 "cracked_stone_bricks" if seed < 6 else
                 "cobblestone" if seed < 11 else "stone_bricks")


def inner_ward(bp):
    for z in range(33):
        for x in range(35):
            if ((x - 17) / 18) ** 2 + ((z - 16) / 17) ** 2 > 1 and not (3 <= x <= 30 and 4 <= z <= 26 or abs(x - 17) <= 2 and z > 24):
                continue
            path = abs(x - 17) <= 2 and z >= 15 or 10 <= x <= 17 and 13 <= z <= 16
            yard = 6 <= x <= 27 and 8 <= z <= 23
            seed = (x * 7 + z * 13 + x * z) % 11
            ground = ("gravel" if seed < 4 else "coarse_dirt") if path else (
                "cobblestone" if yard and z < 12 and x < 20 and seed < 6 else "grass_block")
            bp.set(x, 2, z, MC + "dirt")
            bp.set(x, 3, z, MC + ground)
            bp.pillar(x, z, 4, 6, MC + "air")

    # Broken curtain. The south gate is three blocks wide; the east breach stays open.
    for z in range(6, 27):
        for x in range(4, 31):
            if not (x in (4, 30) or z in (6, 26)):
                continue
            if z == 26 and abs(x - 17) <= 1 or x == 30 and 12 <= z <= 16:
                continue
            distance = abs(z - 14) if x == 30 else abs(x - 24) if z == 26 else 9
            top = min(9, 4 + distance // 2) + ((x + z) % 3 == 0)
            for y in range(4, top + 1):
                bp.set(x, y, z, masonry(x, y, z))
    for x in (14, 20):
        for z in (25, 26):
            bp.pillar(x, z, 4, 11, MC + "stone_bricks")
        bp.set(x, 12, 26, MC + "stone_brick_slab")
    bp.fill(14, 9, 26, 20, 9, 26, MC + "stripped_oak_log[axis=x]")
    for x in (15, 19):
        bp.set(x, 8, 26, MC + "lantern[hanging=true]")

    # The tall northwestern fragment still carries a timber lookout and its access ladder.
    bp.fill(6, 4, 5, 15, 18, 14, MC + "air")
    for z in range(5, 15):
        for x in range(6, 16):
            if x not in (6, 15) and z not in (5, 14):
                continue
            height = 19 - (x - 6) // 3 if z == 5 else 18 - (z - 5) // 2 if x == 6 else 14 - max(x - 9, z - 8) // 2
            for y in range(4, height + 1):
                if z == 14 and 10 <= x <= 12 and y <= 7 or x in (6, 15) and z == 9 and y in (8, 9) or z == 5 and x in (9, 12) and 13 <= y <= 15:
                    continue
                bp.set(x, y, z, masonry(x, y, z))
            if (x + z) % 3 != 1:
                bp.set(x, height + 1, z, MC + "stone_brick_slab")
    bp.fill(7, 10, 6, 14, 10, 13, MC + "spruce_planks")
    bp.fill(8, 10, 6, 8, 11, 6, MC + "air")
    bp.pillar(8, 6, 4, 11, MC + "ladder[facing=south]")
    for x, y, z in ((13, 4, 7), (10, 11, 8), (8, 4, 12), (21, 4, 12), (26, 4, 23)):
        bp.set(x, y, z, MC + "barrel")
        bp.set(x, y + 1, z, MC + "lantern")
    # Fallen rubble fans inward from the breach, clear of the gate and tower stair.
    for x, z in ((29, 11), (27, 13), (28, 17), (27, 18), (26, 17), (25, 15)):
        bp.set(x, 4, z, MC + "mossy_cobblestone_slab")

    # A surviving jamb and a worn step mark the lost guard room along the east curtain.
    bp.fill(22, 4, 7, 27, 4, 10, MC + "stone_bricks")
    bp.fill(22, 4, 11, 26, 4, 11, MC + "stone_brick_stairs[facing=north]")
    bp.pillar(27, 10, 5, 8, MC + "cracked_stone_bricks")
    bp.fill(24, 5, 7, 28, 5, 7, MC + "mossy_cobblestone")
    bp.set(22, 5, 8, MC + "lantern")


def build(bp):
    # The oval bank is highest on the exposed eastern flank. Two cuts remain for the cart track
    # and postern. Its ditch has a solid floor below the anchor, so the placer preserves the cut.
    for z in range(73):
        for x in range(75):
            dx, dz = x - 36, z - 34
            radius = math.hypot(dx / 33, dz / 30)
            gate = abs(dx) <= 3 and z > 48 or abs(z - 24) <= 2 and x > 53
            road = abs(x - 36) <= 2 and z >= 39 or abs(z - 24) <= 1 and x >= 48
            if radius > 1.115 and not road:
                continue
            bank = max(0, round(4 - abs(radius - 0.91) * 35)) if not gate else 0
            ditch = 1 if not gate and 1.014 < radius < 1.09 else 0
            y = 3 + bank - ditch
            bp.pillar(x, z, 1, y, MC + "dirt")
            surface = "gravel" if road else "coarse_dirt" if ditch else "grass_block"
            bp.set(x, y, z, MC + surface)
            bp.pillar(x, z, y + 1, max(9, y + 2), MC + "air")
            if (x > 46 or z < 25) and bank >= 4 and (x * 3 + z) % 5 < 2:
                bp.pillar(x, z, y + 1, y + 2 + (x + z) % 2, MC + "oak_log")
    keep = Blueprint("inner_ward", (35, 22, 33))
    inner_ward(keep)
    for (x, y, z), state in keep.blocks.items():
        bp.set(x + 19, y, z + 10, state)
    # One side of the outer bailey held a remount pen; the jump-free entrance faces the gate.
    for x in range(43, 54):
        for z in range(44, 52):
            bp.set(x, 3, z, MC + ("coarse_dirt" if (x + z) % 4 else "gravel"))
            if (x in (43, 53) or z in (44, 51)) and not (x == 43 and 46 <= z <= 48):
                bp.set(x, 4, z, MC + "oak_fence")
    for x in (44, 46, 47):
        bp.set(x, 4, 50, MC + "hay_block")
    # A covered issue counter and its lean-to roof occupy the opposite side.
    bp.fill(15, 3, 43, 25, 3, 50, MC + "cobblestone")
    for x in (16, 24):
        for z in (44, 49):
            bp.pillar(x, z, 4, 8 if z == 44 else 7, MC + "oak_log")
    for z in range(43, 51):
        bp.fill(15, 9 - (z - 43) // 4, z, 25, 9 - (z - 43) // 4, z, MC + "spruce_slab")
    bp.fill(17, 4, 44, 23, 4, 44, MC + "barrel")
    bp.set(18, 5, 44, MC + "lantern")
    bp.set(23, 5, 44, MC + "lantern")
    for x in (32, 40):
        bp.pillar(x, 61, 4, 7, MC + "cobblestone")
        bp.set(x, 8, 61, MC + "lantern")
