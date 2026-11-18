"""The City of Rimuru after the Founder's Festival. SIZE 191 x 40 x 191; arrival (95,5,95).

Every inherited district and quest anchor keeps its world position. Four radial roads lead onto a new
promenade around the town. The northern audience palace, screened baths, eastern guild, southern
festival theatre and Ramiris's tournament-and-dungeon entrance are accessible on foot. The entrance is
architectural, without a teleport. White plaster, dark beams, sea-green tile and slate. Ramiris's gate incorporates the three shades of
Tensura labyrinth brick, verified in the pinned jar. All new architecture is original geometry.

References: official anime episode 61 (ten-sura.com/anime/tensura/story/no65, hot springs), 62
(no66, dungeon beneath the arena), 63 (no67, Rimuru's audience), and 71 (no76, public dungeon
trial). Crunchyroll's Festival Eve depicts the reception. The district plan, small guild and theatre are our interpretation.
The runtime template is just the new ring. draw_phase() also draws the town for full-city review.
"""
from math import cos, hypot, pi, sin

from blueprint import Blueprint
from _dwargon_lib import AIR, block_light, see_through, spawn_floor
from _town_lib import M, Town, lantern_floor, lantern_hung, log, slab, stair, trapdoor, wall_banner

SIZE = (191, 40, 191)
PARTS = list(range(0, SIZE[2], 16))
ARRIVAL = (95, 5, 95)
G = 4
F = 5


def foundation(t):
    # Above walking height six open blocks clear the roads and gardens. Each roofed district also
    # clears its full height; none of those cuts touches the inherited 137-block town.
    for z in range(191):
        for x in range(191):
            if 27 <= x <= 163 and 27 <= z <= 163:
                continue
            for y in range(G):
                t.bp.blocks[x, y, z] = M("dirt")
            t.bp.blocks[x, G, z] = M("grass_block")
            for y in range(F, 12):
                t.bp.blocks[x, y, z] = AIR
    for a, b in ((22, 26), (164, 168)):
        t.pave(a, 22, b, 168, "street")
        t.pave(22, a, 168, b, "street")
    for lo, hi in ((0, 26), (164, 190)):
        t.pave(93, lo, 97, hi, "cobble")
        t.pave(lo, 93, hi, 97, "cobble")
    for shift in range(0, 191, 12):
        for x, z in ((25, shift), (165, shift), (shift, 25), (shift, 165)):
            # Inlaid lamps leave the full cross streets and cart clearances open.
            t.put(x, G, z, M("sea_lantern"))


def pavilion(t, x0, z0, x1, z1, height, roof, doors):
    """Timber posts, plaster, translucent screens and a solid sill under every window."""
    top = F + height
    t.clear(x0 - 1, F, z0 - 1, x1 + 1, 31, z1 + 1)
    t.fill(x0, G, z0, x1, G, z1, M("birch_planks"))
    t.ring(x0, z0, x1, z1, F, top, M("white_terracotta"))
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if x in (x0, x1) or (x - x0) % 5 == 0:
                t.fill(x, F, z, x, top, z, log("stripped_dark_oak_log"))
            elif x < x1 - 1:
                t.fill(x, 7, z, x, 9, z, M("white_stained_glass"))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            if z in (z0, z1) or (z - z0) % 5 == 0:
                t.fill(x, F, z, x, top, z, log("stripped_dark_oak_log"))
            elif z < z1 - 1:
                t.fill(x, 7, z, x, 9, z, M("white_stained_glass"))
    for x in range(x0 + 3, x1, 7):
        t.fill(x, top, z0, x, top, z1, log("spruce_log", "z"))
        t.put(x, top - 1, (z0 + z1) // 2, lantern_hung())
    for x, z in doors:
        t.clear(x, F, z, x, 8, z)
    t.hip(x0, z0, x1, z1, top + 1, roof, solid_top=False)
    for x, z in ((x0 - 1, z0 - 1), (x1 + 1, z0 - 1), (x0 - 1, z1 + 1), (x1 + 1, z1 + 1)):
        t.put(x, top + 2, z, slab("dark_oak"))


def palace(t):
    # Two intimate reception rooms frame a taller hall. Aligned doors in the party walls
    # let a player walk from the cabinet library, across the throne room, to the banquet.
    for xa, xb in ((27, 44), (66, 83)):
        pavilion(t, xa, 6, xb, 18, 7, "blue", [(x, 18) for x in range(xa + 7, xa + 10)])
    pavilion(t, 44, 2, 66, 19, 11, "blue", [(x, 19) for x in range(52, 59)])
    for x in (44, 66):
        t.clear(x, F, 9, x, 8, 11)
    # A glazed lantern above the hipped roof top-lights the public audience. Its deep second
    # eave, paired bronze finials and projecting entrance gable distinguish the palace from the guild.
    t.clear(50, 22, 7, 60, 32, 14)
    t.ring(50, 7, 60, 14, 22, 26, M("light_blue_stained_glass"))
    for x in (50, 55, 60):
        for z in (7, 14):
            t.fill(x, 22, z, x, 26, z, log("stripped_dark_oak_log"))
    t.fill(50, 26, 7, 60, 26, 7, log("stripped_spruce_log", "x"))
    t.fill(50, 26, 14, 60, 26, 14, log("stripped_spruce_log", "x"))
    t.hip(49, 6, 61, 15, 27, "blue", solid_top=False)
    for x in (53, 57):
        t.put(x, 32, 10, M("cut_copper"))
        t.put(x, 33, 10, M("lightning_rod[facing=up]"))
    # Raised timber canopy, polished seat and a blue emblem in the rear screen.
    t.fill(51, 5, 4, 59, 5, 7, M("dark_oak_planks"))
    t.fill(52, 5, 8, 58, 5, 8, stair("dark_oak", "north"))
    for x in (51, 59):
        t.fill(x, 6, 4, x, 11, 4, log("stripped_spruce_log"))
        t.fill(x, 6, 7, x, 11, 7, log("stripped_spruce_log"))
    t.fill(51, 12, 4, 59, 12, 7, slab("dark_oak"))
    t.put(55, 6, 5, stair("dark_oak", "north"))
    t.fill(53, 8, 2, 57, 11, 2, M("cyan_stained_glass"))
    for z in range(9, 22):
        t.fill(54, 5, z, 56, 5, z, M("cyan_carpet"))
    t.fill(48, G, 20, 62, G, 23, M("spruce_planks"))
    for x in (48, 52, 58, 62):
        t.fill(x, 5, 21, x, 10, 21, log("stripped_dark_oak_log"))
    t.fill(47, 11, 19, 63, 11, 22, slab("dark_prismarine"))
    t.gable(51, 17, 59, 22, 12, "blue", "z", M("white_terracotta"))
    t.fill(54, 13, 22, 56, 14, 22, M("light_blue_stained_glass"))
    t.put(55, 15, 22, M("ochre_froglight"))
    for x in (49, 61):
        t.put(x, 10, 21, lantern_hung())
    for x in (29, 33, 37, 40):
        t.fill(x, 5, 7, x + 1, 7, 7, M("bookshelf"))
        t.put(x, 5, 13, stair("oak", "south"))
    for x in (69, 75, 80):
        t.fill(x, 5, 11, x + 1, 5, 13, slab("spruce", "top"))
        for z, side in ((10, "north"), (14, "south")):
            t.put(x, 5, z, stair("birch", side))


def springs(t):
    pavilion(t, 109, 3, 132, 19, 6, "dark", [(x, 19) for x in range(117, 122)] +
             [(132, z) for z in range(10, 13)])
    t.pave(115, 20, 123, 24, "cobble")
    # Changing cubicles, washing stools and two stone-lined outdoor pools at stepping height.
    for x in (111, 115, 119, 123, 127):
        t.fill(x, 5, 5, x, 7, 8, M("spruce_planks"))
        t.fill(x + 1, 5, 5, x + 2, 5, 5, slab("oak", "top"))
    for x in (112, 116, 125, 129):
        t.put(x, 5, 15, slab("spruce"))
    for x in range(133, 162):
        for z in range(3, 21):
            d = min(hypot((x - 141) / 7.8, (z - 11) / 6.8),
                    hypot((x - 154) / 6.4, (z - 12) / 5.5))
            if d < 1.2:
                t.put(x, G, z, M("andesite"))
            if d < 0.94:
                t.put(x, G - 1, z, M("prismarine") if (x + z) % 9 else M("sea_lantern"))
                t.put(x, G, z, M("water[level=0]"))
    for z in (2, 20):
        t.fill(134, 5, z, 161, 6, z, M("bamboo_planks"))
    t.fill(162, 5, 2, 162, 6, 20, M("bamboo_planks"))
    for x in (135, 143, 151, 160):
        t.lamp(x, 3, 2, "spruce_fence")
    t.fill(133, G, 10, 135, G, 12, M("spruce_planks"))
    # A low timber bridge divides the rock pools. A folded towel and little stone lanterns
    # occupy the washing side; no campfire hides under the water.
    for z in range(3, 21):
        t.fill(147, 5, z, 148, 5, z, slab("spruce"))
    for z in (6, 11, 16):
        t.fill(147, G - 1, z, 147, 5, z, log("stripped_oak_log"))
    for x, z in ((135, 6), (138, 16), (143, 5), (152, 7), (158, 16), (160, 10)):
        t.put(x, 5, z, slab("andesite"))
        t.put(x + 1, G, z, M("mossy_cobblestone"))
    for x in (136, 159):
        t.put(x, 5, 18, M("andesite_wall"))
        t.put(x, 6, 18, M("ochre_froglight"))
        t.put(x, 7, 18, slab("dark_prismarine"))
    for x in (113, 127):
        t.fill(x, 5, 16, x + 1, 5, 16, slab("oak", "top"))
        t.put(x, 6, 16, M("white_carpet"))


def guild(t):
    # An open dispatch counter admits customers from the west road; staff have a gap at its north end.
    pavilion(t, 171, 43, 187, 77, 8, "slate", [(171, z) for z in range(57, 62)])
    t.pave(164, 56, 171, 62, "cobble")
    t.fill(181, 5, 52, 181, 5, 68, M("stripped_oak_log[axis=z]"))
    for z in (54, 61, 67):
        t.put(181, 6, z, M("flower_pot"))
        t.fill(185, 5, z, 185, 8, z + 1, M("bookshelf"))
    for z in (47, 70):
        t.fill(175, 5, z, 178, 5, z + 1, slab("oak", "top"))
        t.put(176, 5, z + 2, stair("spruce", "south"))
    t.fill(171, 7, 65, 171, 9, 71, M("stripped_spruce_log[axis=z]"))
    for z in (66, 68, 70):
        t.put(170, 8, z, wall_banner("white", "west"))
    # Copper-canopied public entrance and a projecting guild board below a map-and-compass emblem.
    t.fill(169, 11, 54, 171, 11, 64, slab("cut_copper"))
    for z in (54, 64):
        t.fill(169, 5, z, 169, 10, z, log("dark_oak_log"))
    t.fill(171, 9, 57, 171, 12, 62, M("cyan_terracotta"))
    for y, z in ((9, 60), (10, 59), (10, 61), (11, 59), (11, 61), (12, 60)):
        t.put(171, y, z, M("cut_copper"))
    for z in (55, 63):
        t.lamp(170, z, 3, "stone_brick_wall")


def festival(t):
    # The open theatre is seen from the market promenade. Two broad stairs lead onto the musicians' dais.
    t.pave(31, 168, 78, 187, "cobble")
    t.fill(39, 5, 179, 71, 6, 187, M("spruce_planks"))
    t.fill(49, 5, 177, 61, 5, 177, stair("spruce", "south"))
    t.fill(49, 6, 178, 61, 6, 178, stair("spruce", "south"))
    t.fill(49, 5, 178, 61, 5, 178, M("spruce_planks"))
    for x in (40, 48, 62, 70):
        for z in (179, 186):
            t.fill(x, 7, z, x, 13, z, log("stripped_spruce_log"))
        t.fill(x, 13, 179, x, 13, 186, log("dark_oak_log", "z"))
        t.put(x, 12, 181, lantern_hung())
    t.gable(39, 179, 71, 186, 14, "slate", "x", M("white_terracotta"))
    for x in (43, 46, 52, 58, 64, 67):
        t.put(x, 7, 184, M("note_block"))
        t.put(x, 7, 182, stair("spruce", "north"))
    for z in (171, 174):
        for x0 in (34, 45, 59, 69):
            t.fill(x0, 5, z, x0 + 5, 5, z, stair("oak", "north"))
    # Swags hang behind the stage. A player at the north aisle can still see the musicians.
    for x in range(41, 70):
        y = 12 - min((x - 41) % 7, 7 - (x - 41) % 7) // 2
        t.put(x, y, 186, M(("cyan_wool", "orange_wool", "white_wool")[(x - 41) // 7 % 3]))
    for x in (40, 70):
        t.put(x, 10, 178, wall_banner("orange", "north"))
    for x in (35, 75):
        t.banner_pole(x, 181, "light_blue", h=6)
    for x, colours in ((104, ("orange", "white")), (115, ("cyan", "white")), (126, ("green", "white"))):
        t.stall(x, 176, 7, 5, colours, facing="n")
        t.pave(x, 168, x + 3, 175, "street")


def labyrinth(t):
    # A small tournament bowl. A level covered passage through the west bank reaches the
    # lantern-lit vestibule under the spectator seats; the marked inner gate is deliberately closed.
    cx, cz = 172, 174
    for x in range(cx - 15, cx + 16):
        for z in range(cz - 13, cz + 14):
            d = hypot((x - cx) / 15, (z - cz) / 13)
            if d > 1 or (27 <= x <= 163 and 27 <= z <= 163):
                continue
            if d < 0.55:
                t.put(x, G, z, M("smooth_sandstone"))
                continue
            h = min(6, 1 + int((d - 0.55) * 13))
            if abs(x - cx) <= 2 and z < cz:
                h = 0
                t.put(x, G, z, M("smooth_sandstone"))
            for dy in range(1, h + 1):
                t.put(x, G + dy, z, M("stone_bricks"))
            if h:
                t.put(x, G + h + 1, z, slab("smooth_sandstone"))
    t.pave(145, 172, 163, 176, "cobble")
    t.clear(157, 5, 172, 164, 8, 176)
    t.fill(157, 9, 171, 165, 9, 177, "tensura:dark_labyrinth_bricks")
    for z in (171, 177):
        t.fill(157, 5, z, 165, 8, z, "tensura:cream_labyrinth_bricks")
    t.fill(165, 5, 172, 165, 8, 176, "tensura:labyrinth_bricks")
    for x in (157, 163):
        t.put(x, 8, 173, lantern_hung())
    t.put(165, 7, 174, M("sea_lantern"))
    # The lower opening is a dungeon vestibule separate from the north entrance to the bowl.
    # Towers and a stepped stone arch frame the fairy-green seal viewed from the market street.
    for z in (170, 178):
        t.fill(155, 5, z, 157, 11, z, M("polished_andesite"))
        t.put(156, 12, z, M("sea_lantern"))
        t.put(156, 13, z, slab("dark_prismarine"))
    t.fill(156, 10, 171, 157, 11, 177, M("prismarine_bricks"))
    t.put(156, 11, 174, M("sea_lantern"))
    t.pave(147, 165, 151, 174, "street")
    for i in range(12):
        angle = i * pi / 6
        x, z = round(cx + 13.8 * cos(angle)), round(cz + 11.7 * sin(angle))
        if x <= 164 and abs(z - cz) <= 5 or x < 164 and z < 164 or abs(x - cx) <= 2 and z < cz:
            continue
        y = max(yy for yy in range(G, 13) if t.get(x, yy, z) not in (None, AIR))
        t.put(x, y, z, M("chiseled_stone_bricks"))
        t.put(x, y + 1, z, lantern_floor())
    for dx, dz in ((0, 0), (-1, 0), (1, 0), (0, 1), (0, -1), (0, -2)):
        t.put(cx + dx, G, cz + dz, M("prismarine_bricks"))
    t.pave(164, 157, 174, 159, "cobble")
    t.pave(170, 158, 174, 164, "cobble")
    for x in (168, 176):
        t.banner_pole(x, 160, "cyan", h=4)


def neighbourhoods(t):
    # Each block opens to the public promenade, with small residences at different roof heights.
    for xa, za, xb, zb, side, roof in (
        (5, 37, 18, 53, "e", "brick"), (6, 62, 18, 78, "e", "dark"),
        (5, 110, 18, 124, "e", "blue"), (4, 135, 18, 151, "e", "slate"),
        (172, 111, 185, 127, "w", "brick"), (172, 136, 187, 153, "w", "dark")
    ):
        _, (dx, dz) = t.house(xa, za, xb, zb, side, storeys=2, roof=roof)
        t.pave(min(dx, 22 if side == "e" else 168), dz - 1,
               max(dx, 22 if side == "e" else 168), dz + 1, "street")
    # The west inn: a public porch, a communal meal downstairs and two guest rooms off the loft.
    for z in (137, 149):
        t.fill(21, 5, z, 21, 9, z, log("stripped_spruce_log"))
    t.fill(19, 10, 136, 21, 10, 150, slab("spruce"))
    t.put(20, 9, 138, lantern_hung())
    t.put(20, 9, 148, lantern_hung())
    t.put(22, 8, 137, wall_banner("yellow", "east"))
    t.fill(8, 5, 140, 13, 5, 141, slab("oak", "top"))
    for x in (8, 10, 12):
        t.put(x, 5, 139, stair("spruce", "north"))
        t.put(x, 5, 142, stair("spruce", "south"))
    t.fill(7, 9, 145, 14, 10, 145, M("white_terracotta"))
    t.clear(11, 9, 145, 12, 10, 145)
    for z in (138, 147):
        t.put(6, 9, z, M("light_blue_bed[part=head,facing=west]"))
        t.put(7, 9, z, M("light_blue_bed[part=foot,facing=west]"))
        t.put(6, 9, z + 1, M("barrel[facing=up]"))
    t.fill(6, 5, 137, 6, 5, 138, M("smoker[facing=east]"))
    for x, z in ((10, 13), (179, 14), (14, 174), (13, 85), (179, 84),
                 (87, 12), (85, 180), (139, 182), (177, 32), (14, 159)):
        t.tree(x, z, "oak", 6, 3)



def gate(t, x, z, axis):
    """A roofed city gate spans each cart road. Five central columns stay open at walking height."""
    for across in (-5, 5):
        for along in (-2, 2):
            px, pz = (x + across, z + along) if axis == "x" else (x + along, z + across)
            t.fill(px, 5, pz, px, 6, pz, M("chiseled_stone_bricks"))
            t.fill(px, 7, pz, px, 12, pz, log("stripped_dark_oak_log"))
    if axis == "x":
        t.fill(x - 5, 12, z - 2, x + 5, 12, z - 2, log("dark_oak_log", "x"))
        t.fill(x - 5, 12, z + 2, x + 5, 12, z + 2, log("dark_oak_log", "x"))
        t.gable(x - 6, z - 2, x + 6, z + 2, 13, "blue", "x", M("white_terracotta"))
        t.put(x, 11, z - 2, lantern_hung())
    else:
        t.fill(x - 2, 12, z - 5, x - 2, 12, z + 5, log("dark_oak_log", "z"))
        t.fill(x + 2, 12, z - 5, x + 2, 12, z + 5, log("dark_oak_log", "z"))
        t.gable(x - 2, z - 6, x + 2, z + 6, 13, "blue", "z", M("white_terracotta"))
        t.put(x - 2, 11, z, lantern_hung())


def gardens(t):
    # A hedge-and-stone boundary gives the capital a green edge; openings line up with its four roads.
    for n in range(3, 188):
        if 86 <= n <= 104:
            continue
        for x, z in ((1, n), (189, n), (n, 1), (n, 189)):
            if n % 12 == 0:
                t.put(x, 5, z, M("polished_andesite"))
                t.put(x, 6, z, slab("stone_brick"))
            elif n % 6:
                t.put(x, 5, z, M("oak_leaves[persistent=true]"))
    for x, z in ((6, 20), (13, 26), (172, 12), (179, 18), (17, 168), (10, 182),
                 (180, 104), (8, 101), (86, 7), (85, 177)):
        for dx, dz, flower in ((-1, 1, "cornflower"), (1, 0, "oxeye_daisy"), (1, 2, "allium")):
            if t.get(x + dx, G, z + dz) == M("grass_block") and t.get(x + dx, 5, z + dz) == AIR:
                t.put(x + dx, 5, z + dz, M(flower))
    for x, z, axis in ((95, 5, "x"), (95, 185, "x"), (5, 95, "z"), (185, 95, "z")):
        gate(t, x, z, axis)


def light_districts(bp):
    # Check the actual top face of every new full block, plus upper/double slabs and upper stairs.
    # Explicit air above uncovered roofs is essential to the pack's conservative block-light solver.
    candidates = []
    for (x, y, z), state in list(bp.blocks.items()):
        if 27 <= x <= 163 and 27 <= z <= 163 or y < G or y + 1 >= SIZE[1]:
            continue
        if state == AIR or see_through(state):
            continue
        if not (spawn_floor(state) or state.startswith("minecraft:hay_block") or "type=top" in state or "type=double" in state or "half=top" in state):
            continue
        pos = (x, y + 1, z)
        if bp.blocks.setdefault(pos, AIR) == AIR:
            candidates.append(pos)
    sx, _, sz = SIZE
    for _ in range(16):
        light = block_light(bp.blocks, SIZE)
        dark = [p for p in candidates if bp.blocks[p] == AIR and not light[(p[1] * sz + p[2]) * sx + p[0]]]
        if not dark:
            return
        placed = []
        for x, y, z in dark:
            if all(abs(x - a) + abs(y - b) + abs(z - c) > 8 for a, b, c in placed):
                # Inlaid promenade lamps retain road width and never stand in a doorway or on the stage.
                if y == F and bp.blocks[x, G, z] in (M("grass_block"), M("gravel"), M("coarse_dirt"), M("cobblestone")):
                    lawn = bp.blocks[x, G, z] == M("grass_block")
                    bp.set(x, G, z, M("ochre_froglight"))
                    if lawn:
                        bp.set(x, F, z, M("moss_carpet"))
                else:
                    bp.set(x, y, z, lantern_floor())
                placed.append((x, y, z))
    raise ValueError("Tempest city still contains a dark spawnable surface")


def build(bp):
    """Emit only this phase's outer districts, with all town columns left out of the template."""
    t = Town(bp, G)
    foundation(t)
    palace(t)
    springs(t)
    guild(t)
    festival(t)
    labyrinth(t)
    neighbourhoods(t)
    gardens(t)
    light_districts(bp)
    t.check_support()
    if any(27 <= x <= 163 and 27 <= z <= 163 for x, _, z in bp.blocks):
        raise ValueError("the Tempest city ring overlaps a town column")


def draw_phase(bp):
    """A complete review drawing, including the unchanged lower phases at the shared world anchors."""
    import tempest_town

    build(bp)
    town = Blueprint("tempest_town", tempest_town.SIZE)
    tempest_town.draw_phase(town)
    dx = ARRIVAL[0] - tempest_town.ARRIVAL[0]
    dz = ARRIVAL[2] - tempest_town.ARRIVAL[2]
    for (x, y, z), state in town.blocks.items():
        bp.blocks[x + dx, y, z + dz] = state
