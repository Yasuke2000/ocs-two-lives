"""Hermit's Tower. SIZE 71 x 34 x 73; anchor (37, 4, 67) on the garden path.

A tapered stone tower with a timber reading room and a steep four-sided slate roof.
Border peel towers inspired the stacked, compact plan. Our interpretation and the
reference inventory are in design/lore/mortal_tower.md.
"""

import math

from blueprint import Blueprint

SIZE = (71, 34, 73)
PARTS = [0, 25, 50]
MC = "minecraft:"


def summit(bp):
    for z in range(25):
        for x in range(23):
            if ((x - 11) / 10.8) ** 2 + ((z - 12) / 12) ** 2 > 1 and not (10 <= x <= 12 and z >= 15):
                continue
            path = abs(x - 11) <= 1 and z >= 15 or 4 <= x <= 11 and z == 18
            bp.set(x, 2, z, MC + "dirt")
            bp.set(x, 3, z, MC + ("gravel" if path else "grass_block"))
            bp.pillar(x, z, 4, 6, MC + "air")
    # Thick stone corners cut off on the diagonal, with arrow loops in alternate storeys.
    bp.fill(6, 4, 5, 16, 21, 15, MC + "air")
    for z in range(5, 16):
        for x in range(6, 17):
            dx, dz = abs(x - 11), abs(z - 10)
            if dx + dz > 8:
                continue
            wall = max(dx, dz) == 5 or dx + dz == 8
            bp.pillar(x, z, 4, 16, MC + "air")
            if wall:
                for y in range(4, 17):
                    if z == 15 and x == 11 and y <= 6 or x in (6, 16) and z == 10 and y in (6, 7, 12, 13):
                        continue
                    seed = (x * 19 + y * 11 + z * 7) % 17
                    block = "mossy_cobblestone" if seed < 4 and y < 8 else "andesite" if seed < 7 else "stone_bricks"
                    bp.set(x, y, z, MC + block)
            else:
                bp.set(x, 3, z, MC + "cobblestone")
                for y in (9, 15):
                    bp.set(x, y, z, MC + "spruce_planks")
    # The ladder has uninterrupted stone backing and opens onto both landings.
    bp.pillar(11, 6, 4, 16, MC + "ladder[facing=south]")
    # Inset timber reading room with a window on each wall.
    bp.fill(7, 16, 6, 15, 20, 14, MC + "air")
    bp.fill(7, 15, 6, 15, 15, 14, MC + "spruce_planks")
    bp.set(11, 15, 6, MC + "ladder[facing=south]")
    for z in range(6, 15):
        for x in range(7, 16):
            if z not in (6, 14) and x not in (7, 15):
                continue
            post = x in (7, 15) and z in (6, 14)
            bp.pillar(x, z, 16, 19, MC + ("stripped_spruce_log" if post else "oak_planks"))
            if not post and (x in (10, 11, 12) or z in (9, 10, 11)):
                bp.fill(x, 17, z, x, 18, z, MC + "glass")
    # An inward landing at the top lets a climber step off the ladder towards the desk.
    bp.fill(11, 16, 6, 11, 18, 6, MC + "air")
    bp.set(11, 16, 6, MC + "ladder[facing=south]")
    bp.set(13, 16, 9, MC + "lectern[facing=west]")
    bp.fill(8, 16, 8, 8, 17, 11, MC + "bookshelf")
    bp.set(13, 16, 12, MC + "spruce_stairs[facing=south]")
    bp.fill(7, 20, 6, 15, 20, 14, MC + "spruce_planks")
    for x, z in ((10, 9), (13, 11)):
        bp.set(x, 19, z, MC + "lantern[hanging=true]")
    # Each tier has a full back course under the next slope. The ridge ends in a stone finial.
    for r in range(5, 0, -1):
        y = 26 - r
        bp.fill(11 - r, y, 10 - r, 11 + r, y, 10 + r, MC + "deepslate_tiles")
        for d in range(-r + 1, r):
            for x, z, facing in ((11 + d, 10 - r, "south"), (11 + d, 10 + r, "north"),
                                 (11 - r, 10 + d, "east"), (11 + r, 10 + d, "west")):
                bp.set(x, y, z, MC + f"deepslate_tile_stairs[facing={facing}]")
    bp.set(11, 26, 10, MC + "cobblestone_wall")
    bp.set(11, 27, 10, MC + "cobblestone_slab")
    # A pallet on the middle floor, writing supplies below and a fenced herb bed outside.
    for z, part in ((11, "foot"), (12, "head")):
        bp.set(9, 10, z, MC + f"brown_bed[part={part},facing=south]")
    for x, y, z in ((8, 4, 10), (14, 10, 9)):
        bp.set(x, y, z, MC + "barrel")
        bp.set(x, y + 1, z, MC + "lantern")
    bp.set(13, 4, 9, MC + "crafting_table")
    for x in range(3, 8):
        bp.set(x, 4, 16, MC + "cobblestone_slab")
        bp.set(x, 4, 20, MC + "cobblestone_slab")
    for x, z, plant in ((4, 17, "poppy"), (5, 19, "cornflower"), (6, 17, "oxeye_daisy")):
        bp.set(x, 4, z, MC + plant)
    for x, z in ((9, 17), (16, 16)):
        bp.set(x, 4, z, MC + "cobblestone_wall")
        bp.set(x, 5, z, MC + "lantern")


def ground(x, z):
    # A broad, level summit under the inhabited tower gives way to six walkable contours.
    distance = math.hypot((x - 34) / 1.32, (z - 25) / 1.16)
    edge = math.hypot((x - 34) / 34, (z - 32) / 34)
    shoulder = max(0, math.floor((1.02 - edge) * 22))
    return 3 + min(6, shoulder, max(0, math.floor((38 - distance) / 3.4)))


def trail(z):
    if z <= 46:
        return 34 + round(11 * math.sin((z - 36) / 10))
    return 43 - round(8 * math.sin((z - 46) / 9))


def build(bp):
    for z in range(73):
        for x in range(71):
            radius = math.hypot((x - 34) / 34, (z - 32) / 34)
            path = z >= 36 and abs(x - trail(z)) <= 1
            if radius > 1.03 and not path:
                continue
            height = ground(x, z)
            bp.pillar(x, z, max(1, height - 3), height - 1, MC + "dirt")
            surface = "gravel" if path else "grass_block"
            bp.set(x, height, z, MC + surface)
            bp.pillar(x, z, height + 1, height + 4, MC + "air")
    room = Blueprint("summit_tower", (23, 28, 25))
    summit(room)
    for (x, y, z), state in room.blocks.items():
        bp.set(x + 23, y + 6, z + 13, state)
    # Young, pollarded oaks have deliberately uneven crowns. Keeping them off the track
    # preserves the first distant view of the lit reading room from the southern approach.
    for x, z, h in ((8, 31, 6), (17, 17, 7), (47, 12, 6), (56, 26, 7),
                    (11, 46, 5), (27, 55, 6), (55, 47, 5), (47, 60, 5)):
        y = ground(x, z)
        bp.pillar(x, z, y + 1, y + h, MC + "oak_log")
        for dz in range(-3, 4):
            for dx in range(-3, 4):
                reach = abs(dx) + abs(dz)
                if reach > 4 or (dx == 0 and dz == 0):
                    continue
                top = y + h + (2 if reach <= 2 else 1)
                bp.pillar(x + dx, z + dz, y + h - 1, top, MC + "oak_leaves[persistent=true]")
        bp.pillar(x, z, y + h + 1, y + h + 2, MC + "oak_leaves[persistent=true]")
    # Terraced medicinals beside a gravel side track; each long bed follows the hillside.
    for z in (41, 44, 47):
        for x in range(20, 31):
            y = ground(x, z)
            bp.set(x, y, z, MC + "grass_block")
            if x in (20, 30):
                bp.set(x, y + 1, z, MC + "mossy_cobblestone_slab")
            else:
                flower = ("cornflower", "oxeye_daisy", "poppy")[(z - 41) // 3]
                bp.set(x, y + 1, z, MC + flower)
    for x in range(21, trail(45) + 1):
        bp.set(x, ground(x, 45), 45, MC + "gravel")
    for z in (42, 54, 65):
        x = trail(z) + 3
        y = ground(x, z)
        bp.pillar(x, z, y + 1, y + 2, MC + "cobblestone_wall")
        bp.set(x, y + 3, z, MC + "lantern")

    # Flat rocks break through the east slope and shelter a patch of bracken.
    for x, z, length in ((49, 37, 5), (48, 38, 7), (50, 39, 4), (19, 29, 3)):
        for step in range(length):
            y = ground(x + step, z)
            bp.set(x + step, y, z, MC + "andesite")
            if 0 < step < length - 1:
                bp.set(x + step, y + 1, z, MC + "andesite_slab")
    for x, z in ((49, 36), (52, 40), (47, 39), (20, 28)):
        bp.set(x, ground(x, z) + 1, z, MC + "fern")
