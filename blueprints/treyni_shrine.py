"""Treyni's shrine: the dryad altar beside the ancient tree of the dryad sanctuary (east of the Great Ameld, Jura forest).

SIZE (33, 22, 33). Ground layer y 4 (moss, grass, podzol; dirt and stone below), you walk at y 5; everything above is
air so placement clears the forest in the box. Arrival and anchor point: blueprint (16, 5, 16), the centre of the dais.

Canon: the dryads (Treyni and her younger sisters Trya and Doris) are spirits that live in the trees of the Great Jura
Forest and keep it; Treyni became the forest's guardian under Veldora (and later moved with Ramiris to the labyrinth,
taking a body made from the Great Spirit Tree). The grove's ancient tree is Tensura's own `tensura:ancient_forest/tree`
(placed by life/landmarks.js, landmark treyni_grove, about 40 x 42 blocks across); this small shrine stands beside it,
not under its crown (design/builds/treyni_shrine.toml puts it 38 blocks east of the landmark; the placer keeps clear of
placed landmarks). Our interpretation, nothing here is canon detail: a round mossy dais with a young azalea tree at its
heart (a seedling of the ancient one), three seats for the three sisters, each with a potted sapling, four log posts with
lanterns, and a living gate of two bent oak logs on the west side, facing the ancient tree. Every spawnable spot on the
dais has block light (checked when this builds). Sources: design/lore/treyni_shrine.md.
"""
import math

from _dwargon_lib import AIR, noise2, rnd
from _sites_lib import M, air_above, light_up, pick, put, tree

SIZE = (33, 22, 33)
SX, SY, SZ = SIZE
G = 4
F = 5
C = 16
ANCHOR = (16, F, 16)
PARTS = None

AZ_LEAF = M("azalea_leaves[persistent=true]")
FL_LEAF = M("flowering_azalea_leaves[persistent=true]")
LANTERN = M("lantern[hanging=false]")


def build(bp):
    blocks = bp.blocks
    air_above(bp, G)
    for x in range(SX):
        for z in range(SZ):
            blocks[(x, 0, z)] = M("stone")
            blocks[(x, 1, z)] = M("stone")
            blocks[(x, 2, z)] = M("dirt")
            blocks[(x, 3, z)] = M("dirt")
            d = math.hypot(x - C, z - C)
            r = rnd(x, 0, z, 3)
            if d < 13:
                blocks[(x, G, z)] = M("moss_block") if r < 0.45 else M("podzol[snowy=false]") if r < 0.6 else M("grass_block[snowy=false]")
            else:
                blocks[(x, G, z)] = M("grass_block[snowy=false]")

    # the dais: mossy stone with a moss ring and a ring of verdant-green runes
    for x in range(SX):
        for z in range(SZ):
            d = math.hypot(x - C, z - C)
            if d <= 7.3:
                blocks[(x, G, z)] = pick([(M("mossy_stone_bricks"), 4), (M("stone_bricks"), 3), (M("mossy_cobblestone"), 2), (M("cracked_stone_bricks"), 1)],
                                         rnd(x, 1, z, 4))
            if 4.2 < d <= 5.2:
                blocks[(x, G, z)] = M("moss_block")
            if 7.3 < d <= 8.3:
                blocks[(x, F, z)] = M("mossy_stone_brick_slab[type=bottom,waterlogged=false]") if rnd(x, 2, z, 5) < 0.85 else AIR
    for k in range(48):  # emerald-green runes: a ring of glow lichen-coloured stone at r = 6
        a = math.radians(k * 7.5)
        x, z = round(C + 6 * math.cos(a)), round(C + 6 * math.sin(a))
        blocks[(x, G, z)] = M("verdant_froglight") if k % 12 == 0 else M("oxidized_cut_copper") if k % 2 else M("mossy_stone_bricks")

    # the seedling: a young azalea tree at the heart (trunk 6, round crown)
    for y in range(F, F + 6):
        blocks[(C, y, C)] = M("oak_log[axis=y]")
    for dx in range(-3, 4):
        for dy in range(-2, 3):
            for dz in range(-3, 4):
                if dx * dx + dz * dz + dy * dy * 1.6 <= 9.5 and (dx, dz) != (0, 0) or (dy > 0 and (dx, dz) == (0, 0) and dy < 3):
                    y = F + 6 + dy
                    if 0 <= y < SY and blocks.get((C + dx, y, C + dz)) == AIR:
                        blocks[(C + dx, y, C + dz)] = FL_LEAF if rnd(C + dx, y, C + dz, 6) < 0.4 else AZ_LEAF
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # roots
        put(bp, C + dx, F, C + dz, M("oak_log[axis=x]") if dx else M("oak_log[axis=z]"))
    blocks[(C, F + 5, C + 1)] = M("shroomlight")
    # moss and flowers round the trunk
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if 1.5 < math.hypot(dx, dz) < 3.2 and blocks.get((C + dx, F, C + dz)) == AIR and rnd(C + dx, 3, C + dz, 7) < 0.6:
                blocks[(C + dx, F, C + dz)] = M("moss_carpet") if rnd(C + dx, 4, C + dz, 8) < 0.7 else M("azure_bluet")

    # three seats for the three sisters, in a half circle on the east side, each with a potted sapling
    pots = ("potted_azalea_bush", "potted_flowering_azalea_bush", "potted_cherry_sapling")
    for i, (ang, pot) in enumerate(zip((-45, 0, 45), pots)):
        a = math.radians(ang)
        x, z = round(C + 5.6 * math.cos(a)), round(C + 5.6 * math.sin(a))
        blocks[(x, F, z)] = M("stone_brick_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
        blocks[(x + 1, F, z)] = M("mossy_stone_bricks")
        blocks[(x + 1, F + 1, z)] = M(pot)
    # four log posts with lanterns, vines and moss
    for dx, dz in ((9, 9), (-9, 9), (9, -9), (-9, -9)):
        x, z = C + dx, C + dz
        for y in range(F, F + 5):
            blocks[(x, y, z)] = M("stripped_oak_log[axis=y]") if y > F else M("mossy_cobblestone")
        blocks[(x, F + 5, z)] = M("oak_log[axis=y]")
        for ox, oz, face in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
            if rnd(x + ox, 5, z + oz, 9) < 0.35:
                for y in range(F + 2, F + 5):
                    put(bp, x + ox, y, z + oz, M(f"vine[{face}=true]"))
        blocks[(x, F + 6, z)] = M("lantern[hanging=false]")
    # the living gate on the west side: two bent oak logs meeting overhead, leaves woven in
    gx = 2
    for z in (C - 3, C + 3):
        for y in range(F, F + 4):
            blocks[(gx, y, z)] = M("oak_log[axis=y]")
    for dz in range(-3, 4):
        blocks[(gx, F + 4 + (1 if abs(dz) <= 1 else 0) , C + dz)] = M("oak_log[axis=z]")
    for dz in range(-3, 4):
        for dy in (4, 5, 6):
            for dx in (-1, 0, 1):
                if rnd(gx + dx, F + dy, C + dz, 12) < 0.55 and blocks.get((gx + dx, F + dy, C + dz)) == AIR and dy >= 5 - (1 if abs(dz) > 1 else 0):
                    blocks[(gx + dx, F + dy, C + dz)] = AZ_LEAF if rnd(gx + dx, F + dy, C + dz, 13) < 0.7 else FL_LEAF
    blocks[(gx, F + 3, C)] = M("lantern[hanging=true]")
    # a stepping path from the gate to the dais
    for x in range(gx + 1, C - 7):
        for z in (C - 1, C, C + 1):
            blocks[(x, G, z)] = M("mossy_stone_bricks") if (x + z) % 3 else M("moss_block")
    # flowers, ferns and boulders in the clearing
    for x in range(SX):
        for z in range(SZ):
            d = math.hypot(x - C, z - C)
            if 8.6 < d < 14.5 and blocks.get((x, F, z)) == AIR and blocks.get((x, G, z)) in (M("moss_block"), M("grass_block[snowy=false]"), M("podzol[snowy=false]")):
                r = rnd(x, 7, z, 15)
                if r < 0.07:
                    blocks[(x, F, z)] = M(("lily_of_the_valley", "azure_bluet", "white_tulip", "oxeye_daisy")[int(rnd(x, 8, z, 16) * 4)])
                elif r < 0.18:
                    blocks[(x, F, z)] = M("fern") if r < 0.12 else M("short_grass")
                elif r < 0.2:
                    blocks[(x, F, z)] = M("mossy_cobblestone")
    # a ring of trees round the clearing so the box does not end in a wall
    for i in range(46):
        a = i * 2 * math.pi / 46 + rnd(i, 0, 0, 21) * 0.1
        r = 14.8 + rnd(i, 1, 0, 21) * 1.5
        x, z = round(C + r * math.cos(a)), round(C + r * math.sin(a))
        if 2 <= x < SX - 2 and 2 <= z < SZ - 2 and not (x <= 4 and abs(z - C) <= 4):
            tree(bp, x, F, z, 7 + int(rnd(i, 2, 0, 21) * 4), leaves="oak" if i % 3 else "birch", wide=2)

    cands = [(x, F, z) for x in range(SX) for z in range(SZ) if math.hypot(x - C, z - C) <= 10 or (x <= C and abs(z - C) <= 2)]

    def add_light(x, y, z):
        put(bp, x, y, z, M("mossy_stone_brick_wall[east=false,north=false,south=false,up=true,waterlogged=false,west=false]"))
        put(bp, x, y + 1, z, LANTERN)

    light_up(bp, cands, add_light, spread=8)
    return None
