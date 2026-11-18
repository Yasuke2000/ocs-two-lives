"""Phase two of Tempest, the trade town in Jura. SIZE 137 × 40 × 137; ARRIVAL (68,5,68) at world 0,0.

A five-block road leaves the old village's south gate and branches to Blumund (west) and Dwargon
(north). Stone aprons, timber yards, shared kitchens, a working dye house and a council court ring
the established village. Ochre froglights, furnace fires and lanterns light the ring at night.
Original geometry using vanilla timber, Tensura thatch and a working Tensura woodcutter; the already-placed 91-square village is never written.
The optional draw_phase overview composes the existing village and the new cloth-and-iron town.
References: https://www.ten-sura.com/map/#A-112 and https://www.ten-sura.com/anime/tensura/story/no16
(regional settlement after the Orc Disaster); the street plan and building designs are our interpretation.
"""
from blueprint import Blueprint
from _dwargon_lib import AIR, block_light, emission, spawn_floor
from _town_lib import Town, M, lantern_floor, lantern_hung, log, slab, stair
import tempest

SIZE = (137, 40, 137)
ARRIVAL = (68, 5, 68)
PARTS = [0, 23, 46, 69, 92, 115]
G, F = 4, 5
CORE_X, CORE_Z = 23, 11


def in_core(x, z):
    return CORE_X <= x < CORE_X + tempest.SX and CORE_Z <= z < CORE_Z + tempest.SZ


def roadways(t):
    for x0, z0, x1, z1 in ((17, 5, 119, 9), (17, 5, 21, 106), (115, 5, 119, 106),
                           (17, 102, 119, 106), (66, 102, 70, 136), (66, 0, 70, 9),
                           (0, 66, 21, 70), (115, 66, 136, 70)):
        t.pave(x0, z0, x1, z1)
    for x in range(23, 115, 9):
        for z in (4, 107):
            if 65 <= x <= 71:
                continue
            t.lamp(x, z, 2, "spruce_fence")
    for z in range(12, 101, 9):
        for x in (16, 120):
            if abs(z - 68) > 3:
                t.lamp(x, z, 2, "spruce_fence")
    # Trade gates: two lamps hang under a timber lintel; the wagon bed is unobstructed.
    for cx, cz, east_west in ((4, 68, True), (68, 2, False), (132, 68, True), (68, 132, False)):
        def cross(n):
            return (cx, cz + n) if east_west else (cx + n, cz)
        for offset in (-4, 4):
            x, z = cross(offset)
            t.put(x, F, z, M("stone_bricks"))
            t.fill(x, F + 1, z, x, F + 5, z, log("stripped_spruce_log"))
        for offset in range(-5, 6):
            x, z = cross(offset)
            t.put(x, F + 5, z, log("spruce_log", "z" if east_west else "x"))
            t.put(x, F + 6, z, slab("dark_oak"))
            if abs(offset) == 2:
                t.put(x, F + 4, z, lantern_hung())

    for x, z, material in ((68, 2, "iron_block"), (4, 68, "hay_block")):
        t.put(x, F + 5, z, M(material))

def side_lanes(t):
    # Short door-to-road lanes; commons have space for a cart to turn.
    for x0, z0, x1, z1 in ((10, 22, 17, 24), (10, 81, 17, 83), (12, 96, 17, 98),
                            (118, 21, 124, 23), (118, 77, 124, 79), (117, 84, 128, 86),
                            (126, 86, 128, 88), (100, 105, 102, 130), (100, 108, 128, 110),
                            (107, 110, 110, 112), (70, 109, 77, 112), (62, 114, 67, 117),
                            (14, 113, 20, 114), (17, 115, 19, 121), (30, 114, 31, 130),
                            (9, 120, 31, 122), (14, 127, 17, 129)):
        t.pave(x0, z0, x1, z1, "cobble")
    # Timber hitching rail, replenishment barrels and a loaded two-wheeled dray.
    for x, z in ((8, 64), (10, 64), (12, 64)):
        t.put(x, F, z, M("spruce_fence"))
    t.fill(8, F + 1, 64, 12, F + 1, 64, log("stripped_oak_log", "x"))
    for x in (73, 75, 77):
        t.put(x, F, 2, M("barrel[facing=up]"))
    for x in (42, 45):
        t.put(x, F, 2, log("dark_oak_log", "x"))
    t.fill(43, F + 1, 1, 44, F + 1, 4, slab("spruce"))
    t.fill(43, F + 2, 2, 44, F + 2, 3, M("hay_block"))
    for x in (43, 44):
        t.put(x, F, 5, M("spruce_fence"))


def forge(t):
    """Two-bay Kaijin annex; the road door leads to the furnaces, the open forge faces a timber yard."""
    t.pave(2, 39, 16, 62, "cobble")
    t.house(3, 40, 12, 49, "e", 2, "bricks", "spruce", "slate", furnish=False)
    for z in (42, 46):
        t.put(4, F, z, M("blast_furnace[facing=east,lit=true]"))
        t.put(5, F, z + 1, M("anvil[facing=north]"))
    for x, z in ((3, 51), (12, 51), (3, 59), (12, 59)):
        t.fill(x, F, z, x, F + 3, z, log("stripped_spruce_log"))
    t.gable(3, 51, 12, 59, F + 4, "slate", "z", M("bricks"))
    for z in (53, 54, 55):
        t.put(4, F, z, M("lava_cauldron" if z == 54 else "bricks"))
        t.put(9, F, z, M("water_cauldron[level=3]" if z == 54 else "smooth_stone_slab"))
    t.fill(3, F, 55, 4, F + 8, 56, M("bricks"))
    t.put(3, F + 9, 55, M("campfire[lit=true]"))
    t.put(8, F, 57, M("smithing_table"))
    t.put(7, F, 57, M("grindstone[face=floor,facing=east]"))
    for x in range(7, 11):
        t.put(x, F, 61, log("stripped_oak_log", "x"))
    t.put(11, F, 61, M("raw_iron_block"))
    t.put(6, F, 60, "tensura:woodcutter[facing=east,waterlogged=false]")


def weaving(t):
    """Thread preparation, weaving and drying read in order from the street."""
    t.pave(120, 38, 134, 59, "cobble")
    t.house(122, 40, 132, 52, "w", 1, "white_terracotta", "birch", "blue", furnish=False, storey_h=5)
    for z in (42, 45, 48, 50):
        t.put(131, F, z, M("loom[facing=west]"))
    for x, dye in ((123, "red"), (126, "blue"), (129, "yellow")):
        t.put(x, F, 55, M("water_cauldron[level=3]"))
        t.put(x + 1, F, 55, M(dye + "_wool"))
    for x in (122, 132):
        t.fill(x, F, 58, x, F + 3, 58, log("stripped_birch_log"))
    t.fill(122, F + 3, 58, 132, F + 3, 58, log("birch_log", "x"))
    for x, dye in zip((124, 126, 128, 130), ("cyan", "white", "magenta", "yellow")):
        t.put(x, F + 2, 58, M(dye + "_wall_banner[facing=north]"))
        t.put(x, F + 2, 59, log("birch_log", "x"))


def council(t):
    """Council court with public seating, a central speaking aisle and an open portico."""
    t.pave(76, 108, 99, 129, "plaza")
    t.house(78, 114, 97, 126, "n", 1, "calcite", "dark_oak", "dark", furnish=False, storey_h=6)
    t.clear(77, F + 6, 113, 98, F + 18, 127)
    t.hip(78, 114, 97, 126, F + 6, "slate")
    for x in (80, 86, 90, 95):
        t.fill(x, F, 110, x, F + 3, 110, log("stripped_dark_oak_log"))
    t.hip(79, 110, 96, 114, F + 4, "copper")
    for z in (116, 119, 122):
        for x in (81, 82, 83, 92, 93, 94):
            t.put(x, F, z, stair("spruce", "west" if x < 86 else "east"))
    t.put(87, F, 124, M("lectern[facing=north]"))
    for x in range(81, 96):
        t.put(x, F, 125, slab("dark_oak"))
    for x in (82, 93):
        t.put(x, F + 4, 115, M("cyan_wall_banner[facing=south]"))
        t.put(x, F + 4, 114, log("dark_oak_log"))


def quarters(t):
    """Hobgoblin households share kitchen gardens; orc masons share a cutting yard and dormitories."""
    for x, z, roof, wall in ((5, 109, "spruce", "mud_bricks"), (20, 112, "mud", "brown_terracotta"),
                            (5, 124, "dark", "white_terracotta"), (21, 126, "spruce", "mud_bricks")):
        t.house(x, z, x + 8, z + 7, "e", 1, wall, "oak", roof)
        # Thatch shingles above the hobgoblins' domestic rooms keep the village roof profile.
        for bx in range(x - 1, x + 10):
            for bz in range(z - 1, z + 9):
                for by in range(F + 4, F + 11):
                    state = t.get(bx, by, bz)
                    if "_stairs[" in state:
                        t.put(bx, by, bz, tempest.THATCH_STAIRS + "[" + state.split("[", 1)[1])
                    elif state in (M("spruce_planks"), M("dark_oak_planks"), M("mud_bricks")):
                        t.put(bx, by, bz, tempest.THATCH)
    t.pave(15, 106, 18, 134)
    t.pave(18, 121, 32, 123)
    t.put(20, F, 120, M("smoker[facing=west]"))
    for x in range(32, 38):
        for z in range(112, 124):
            if x == 35:
                t.put(x, G, z, M("water[level=0]"))
            else:
                t.put(x, G, z, M("farmland[moisture=7]"))
                t.put(x, F, z, M("carrots[age=7]" if z < 119 else "potatoes[age=7]"))
    for x, z in ((104, 112), (120, 109), (120, 88)):
        t.house(x, z, x + 11, z + 10, "n", 1, "packed_mud", "dark_oak", "slate",
                base="polished_deepslate", storey_h=5, furnish=False)
        for bx in (x + 2, x + 5, x + 8):
            t.put(bx, F, z + 8, M("brown_bed[facing=south,part=foot]"))
            t.put(bx, F, z + 9, M("brown_bed[facing=south,part=head]"))
            t.put(bx, F, z + 2, M("barrel[facing=up]"))
    t.pave(102, 126, 131, 132, "cobble")
    for x in (105, 111, 118):
        t.put(x, F, 129, M("stonecutter[facing=north]"))
        t.put(x + 1, F, 130, M("polished_andesite"))
    for x in range(123, 130):
        for z in (128, 129):
            t.put(x, F, z, M("andesite"))
            if x % 3 == 0:
                t.put(x, F + 1, z, M("stone_bricks"))


def market(t):
    t.pave(40, 108, 63, 126, "cobble")
    for x, colours in ((41, ("yellow", "white")), (49, ("cyan", "white")), (57, ("orange", "brown"))):
        t.stall(x, 110, 5, 4, colours)
    t.house(43, 120, 56, 130, "n", 2, "terracotta", "spruce", "brick")
    for x in (59, 61):
        t.put(x, F, 123, M("barrel[facing=up]"))
    for x, z, face in ((3, 18, "e"), (4, 77, "e"), (5, 92, "e"), (122, 17, "w"), (123, 73, "w")):
        t.house(x, z, x + 9, z + 10, face, 1, "white_terracotta", "oak", "spruce")
    for x, z in ((8, 11), (10, 34), (15, 89), (128, 34), (127, 11), (8, 102),
                 (38, 129), (59, 133), (75, 132), (101, 132), (133, 104), (132, 62), (32, 2), (55, 2), (88, 2), (102, 2)):
        t.tree(x, z, "oak", 6, 2)


def light_ring(t):
    """Test the actual ring without borrowing any light from the village or sky.

    Include top stairs/slabs, hay and crops conservatively. Inset lights preserve both the
    walkable street and the clearance in front of doors. Roofs receive standing lanterns.
    """
    bp = t.bp
    floors = [p for p, s in bp.blocks.items() if p[1] >= G and s != AIR
              and (spawn_floor(s) or "type=top" in s or "half=top" in s or "hay_block" in s)]
    # Treat every non-emitting fitting as opaque, even open doors and stairs. This prevents
    # the simplified flood fill from crediting light through the solid face of a directional block.
    stone = M("stone")
    for _ in range(16):
        palette = {s: AIR if s == AIR or "carrots" in s or "potatoes" in s else
                   s if emission(s) else stone for s in set(bp.blocks.values())}
        transmission = {p: palette[s] for p, s in bp.blocks.items()}
        levels = block_light(transmission, SIZE)
        placed = []
        for x, y, z in floors:
            above = bp.blocks.get((x, y + 1, z), AIR)
            if above != AIR and not any(n in above for n in ("carrots", "potatoes")):
                continue
            if levels[((y + 1) * SIZE[2] + z) * SIZE[0] + x] > 0:
                continue
            if any(abs(x - a) + abs(y - b) + abs(z - c) < 9 for a, b, c in placed):
                continue
            if y == G and above == AIR:
                t.put(x, y, z, M("ochre_froglight"))
            else:
                t.put(x, y + 1, z, lantern_floor())
            placed.append((x, y, z))
        if not placed:
            return
    raise ValueError(f"unlit surfaces remain in the trade town {placed[:8]}")


def build(bp):
    """Placement delta. The entire original village, including its forest and resident feet, is absent."""
    t = Town(bp, G)
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            if in_core(x, z):
                continue
            for y in range(SIZE[1]):
                bp.blocks[x, y, z] = M("dirt") if y < G else M("grass_block") if y == G else AIR
    side_lanes(t)
    roadways(t)
    forge(t)
    weaving(t)
    council(t)
    quarters(t)
    market(t)
    if any(in_core(x, z) for x, _, z in bp.blocks):
        raise ValueError("phase two overlaps the village")
    light_ring(t)
    t.check_support()


def draw_phase(bp):
    """Full phase-two overview for review. Never pass the composite to the NBT exporter."""
    build(bp)
    core = Blueprint("tempest", tempest.SIZE)
    tempest.build(core)
    for (x, y, z), state in core.blocks.items():
        bp.blocks[x + CORE_X, y, z + CORE_Z] = state
