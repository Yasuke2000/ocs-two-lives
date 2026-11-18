"""The gate to the Dwelling of the Spirits: the sealed entrance in the Great Jura Forest (owner request, Life 2).

SIZE (57, 40, 57). Ground layer y 4 (grass, dirt and stone below), you walk at y 5; everything above the ground layer
that is not built is air (placement clears the forest in the box). Arrival and anchor point: blueprint (28, 5, 24) on
the plaza, 9 blocks in front of the doorway, facing north; a soul coming back from the Dwelling arrives here.

A paved plaza of Tensura labyrinth stone (a praying path runs in from the south) is ringed by five elemental plinths
(fire, water, wind, earth, space: the elements of the spirits Rimuru called with the children) in front of a mossy
cliff. In the cliff a tall doorway with a pentagon-of-elements seal on its back wall. The doorway is the portal:
stepping into PORTAL (anchor-relative box, exported to generated/spirit_gate.js) sends a Life 2 soul to the Dwelling
(life/spirit_domain.js); the blueprint only holds the open doorway and the seal. Nothing here is a Tensura warp pad or
labyrinth portal block, so no mod logic fires. Every spawnable spot has block light (checked when this builds).

Canon: the Dwelling of the Elementals is reached through Ramiris's labyrinth (light novel vol. 4, ch. 50); where on the
continent is our interpretation. References and sources: design/lore/spirit_domain.md.
"""
import json
import math

from _dwargon_lib import AIR, fbm2, noise2, rnd
from _sites_lib import M, air_above, light_up, line, pick, put, tree

SIZE = (57, 40, 57)
SX, SY, SZ = SIZE
G = 4
F = 5
CX = 28
ANCHOR = (28, F, 24)
# Anchor-relative box that teleports (dx0, dy0, dz0, dx1, dy1, dz1), inclusive: the doorway's floor cells x 25..31,
# z 14..15, walking height y 5..10.
PORTAL = (-3, 0, -10, 3, 5, -9)
PARTS = None

HILL_C = (28, 4)
HILL_R = (31, 17)
HILL_H = 22
FACE_Z = 16  # the cliff's south face

LAB = "tensura:labyrinth_bricks"
LAB_STONE = "tensura:labyrinth_stone"
CREAM = "tensura:cream_labyrinth_bricks"
PRAY = "tensura:labyrinth_praying_path"
LANTERN = M("sea_lantern")

ELEMENTS = {
    "fire": (M("red_nether_bricks"), M("orange_stained_glass"), M("shroomlight")),
    "water": (M("prismarine_bricks"), M("light_blue_stained_glass"), M("sea_lantern")),
    "wind": (M("quartz_pillar[axis=y]"), M("lime_stained_glass"), M("verdant_froglight")),
    "earth": (M("smooth_sandstone"), M("yellow_stained_glass"), M("glowstone")),
    "space": (M("purpur_pillar[axis=y]"), M("purple_stained_glass"), M("amethyst_block")),
}
PLINTHS = (("fire", 18, 21), ("water", 38, 21), ("wind", 16, 30), ("earth", 40, 30), ("space", 28, 39))


def hill_top(x, z) -> int:
    ex, ez = (x - HILL_C[0]) / HILL_R[0], (z - HILL_C[1]) / HILL_R[1]
    d = 1 - ex * ex - ez * ez
    if d <= 0:
        return 0
    h = HILL_H * math.sqrt(d) ** 0.8 + (fbm2(x, z, 11, 5) - 0.5) * 7
    if h < 3:
        return 0
    return int(min(h, 24))


def plinth(bp, name, px, pz):
    base, glass, glow = ELEMENTS[name]
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            put(bp, px + dx, F, pz + dz, LAB)
            put(bp, px + dx, G, pz + dz, LAB_STONE)
    for y in range(F + 1, F + 4):
        put(bp, px, y, pz, base)
    put(bp, px, F + 4, pz, M("chiseled_stone_bricks"))
    put(bp, px, F + 5, pz, glow)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(bp, px + dx, F + 5, pz + dz, glass)
    for dx, dz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        put(bp, px + dx, F + 1, pz + dz, M("polished_andesite_slab[type=bottom,waterlogged=false]"))


def build(bp):
    blocks = bp.blocks
    air_above(bp, G)
    for x in range(SX):
        for z in range(SZ):
            blocks[(x, 0, z)] = M("stone")
            blocks[(x, 1, z)] = M("stone")
            blocks[(x, 2, z)] = M("dirt")
            blocks[(x, 3, z)] = M("dirt")
            blocks[(x, G, z)] = M("grass_block[snowy=false]")

    # --- the cliff: an ellipse of rock cut off at the south face -----------------------------------------
    tops = {}
    for x in range(SX):
        for z in range(SZ):
            face = FACE_Z + round((noise2(x, 0, 6, 9) - 0.5) * 3) if not 19 <= x <= 37 else FACE_Z
            if z > face:
                continue
            h = hill_top(x, z)
            if h:
                tops[(x, z)] = G + h
                for y in range(G + 1, G + h + 1):
                    blocks[(x, y, z)] = M("stone")
    # weathered face and crown
    for (x, z), t in tops.items():
        for y in range(G + 1, t + 1):
            exposed = z >= FACE_Z - 2 or (x + 1, z) not in tops or (x - 1, z) not in tops or y == t
            if exposed and blocks.get((x, y, z)) == M("stone"):
                blocks[(x, y, z)] = pick([(M("stone"), 5), (M("mossy_cobblestone"), 3), (M("andesite"), 2), (M("moss_block"), 2),
                                          (M("mossy_stone_bricks"), 1), (M("tuff"), 1)], rnd(x, y, z, 21))
        steep = max(abs(t - tops.get((x + dx, z + dz), G)) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if steep < 2 and z < FACE_Z - 3 and noise2(x, z, 8, 17) > 0.3:
            blocks[(x, t, z)] = M("grass_block[snowy=false]")
            if rnd(x, 1, z, 33) < 0.2:
                put(bp, x, t + 1, z, M("fern"))
    # trees on the crown of the cliff
    for i in range(18):
        x, z = 8 + int(rnd(i, 1, 0, 41) * (SX - 16)), 2 + int(rnd(i, 2, 0, 41) * 12)
        t = tops.get((x, z))
        if t and blocks.get((x, t, z)) == M("grass_block[snowy=false]") and blocks.get((x, t + 1, z)) == AIR:
            tree(bp, x, t + 1, z, 5 + int(rnd(i, 3, 0, 41) * 3), leaves="oak" if i % 2 else "birch", wide=2)
    # hanging vines down the face
    for x in range(SX):
        for z in range(FACE_Z - 3, FACE_Z + 1):
            t = tops.get((x, z))
            if not t or rnd(x, 5, z, 51) > 0.16 or (23 <= x <= 33):
                continue
            n = 2 + int(rnd(x, 6, z, 52) * 5)
            if (x, z + 1) in tops or blocks.get((x, F + 4, z + 1)) != AIR:
                continue
            for y in range(t, t - n, -1):
                if y > F and blocks.get((x, y, z + 1)) == AIR:
                    blocks[(x, y, z + 1)] = f"minecraft:vine[north=true]"

    # --- the doorway: frame, vestibule, seal ---------------------------------------------------------------------
    # carve the opening (x 25..31, y 5..11) from the face back to z 12
    for x in range(25, 32):
        for y in range(F, F + 8):
            for z in range(12, FACE_Z + 4):
                blocks[(x, y, z)] = AIR
    # arch: rounded top, corners filled
    for x, y in ((25, F + 7), (31, F + 7), (25, F + 6), (31, F + 6)):
        for z in range(12, FACE_Z + 4):
            blocks[(x, y, z)] = LAB
    # frame pillars (x 22..24 and 32..34), proud of the face (z up to 19), 9 tall
    for x0 in (22, 32):
        for x in range(x0, x0 + 3):
            for z in range(13, FACE_Z + 4):
                for y in range(F, F + 11):
                    blocks[(x, y, z)] = LAB if (y + z) % 5 else CREAM
        # base and capital
        for x in range(x0 - (1 if x0 == 22 else 0), x0 + 3 + (1 if x0 == 32 else 0)):
            for z in range(FACE_Z + 1, FACE_Z + 4):
                blocks[(x, F, z)] = M("chiseled_stone_bricks")
    # lintel and crest
    for x in range(21, 36):
        for z in range(13, FACE_Z + 4):
            blocks[(x, F + 11, z)] = LAB_STONE
            blocks[(x, F + 12, z)] = LAB
    for x in range(23, 34):
        for z in range(FACE_Z + 1, FACE_Z + 4):
            blocks[(x, F + 13, z)] = M("chiseled_stone_bricks") if x % 2 else CREAM
    for dx in range(-2, 3):
        blocks[(28 + dx, F + 14, FACE_Z + 2)] = M("amethyst_block") if abs(dx) < 2 else LAB
    blocks[(28, F + 15, FACE_Z + 2)] = LANTERN
    # threshold: a strip of praying path through the doorway
    for x in range(25, 32):
        for z in range(12, FACE_Z + 4):
            blocks[(x, G, z)] = M("polished_andesite") if (x + z) % 2 else M("smooth_stone")
    for z in range(12, FACE_Z + 4):
        blocks[(28, G, z)] = PRAY
    # the sealed door: a quartz wall at z 11..12 with the five-element seal
    for x in range(25, 32):
        for y in range(F, F + 8):
            for z in (11, 12):
                blocks[(x, y, z)] = M("smooth_quartz")
    cx, cy, cz = 28, F + 3, 12
    for k in range(40):  # ring r = 3 on the door face (plane z = 12)
        a = math.radians(k * 9)
        x, y = round(cx + 3 * math.cos(a)), round(cy + 3 * math.sin(a))
        blocks[(x, y, cz)] = M("amethyst_block")
    for i, name in enumerate(("fire", "water", "wind", "earth", "space")):
        a = math.radians(-90 + 72 * i)
        x, y = round(cx + 3 * math.cos(a)), round(cy + 3 * math.sin(a))
        blocks[(x, y, cz)] = ELEMENTS[name][2]
        blocks[(x, y, cz + 1)] = ELEMENTS[name][1].replace("stained_glass", "stained_glass_pane") + "[east=false,north=false,south=false,waterlogged=false,west=false]"
    pts = [(round(cx + 3 * math.cos(math.radians(-90 + 72 * i))), round(cy + 3 * math.sin(math.radians(-90 + 72 * i)))) for i in range(5)]
    for i in range(5):  # pentagram: every second vertex
        a, b = pts[i], pts[(i + 2) % 5]
        for x, y in line(a[0], a[1], b[0], b[1]):
            if blocks.get((x, y, cz)) == M("smooth_quartz"):
                blocks[(x, y, cz)] = M("quartz_bricks")
    blocks[(cx, cy, cz)] = M("chiseled_quartz_block")
    # wall lamps flanking the door
    for x in (25, 31):
        blocks[(x, F + 6, 13)] = LANTERN
    # the portal air: make sure the box is open (x 25..31, y 5..10, z 14..15)
    for x in range(25, 32):
        for y in range(F, F + 6):
            for z in (14, 15):
                blocks[(x, y, z)] = AIR

    # --- plaza ---------------------------------------------------------------------------------------------------
    for x in range(SX):
        for z in range(FACE_Z + 4, SZ):
            d = math.hypot(x - 28, z - 28)
            if d <= 13.4 and blocks.get((x, F, z)) == AIR:
                blocks[(x, G, z)] = pick([(LAB_STONE, 4), (LAB, 3), (CREAM, 2), (M("stone_bricks"), 1)], rnd(x, 0, z, 61))
    for x in range(SX):  # the plaza meets the doorway steps
        for z in range(FACE_Z + 1, FACE_Z + 4):
            if 22 <= x <= 34 and blocks.get((x, G, z)) == M("grass_block[snowy=false]"):
                blocks[(x, G, z)] = LAB_STONE
    for x, z in ((x, z) for x in range(SX) for z in range(SZ)):
        d = math.hypot(x - 28, z - 28)
        if 11 < d <= 13.4 and blocks.get((x, F, z)) == AIR and blocks.get((x, G, z)) in (LAB_STONE, LAB, CREAM):
            blocks[(x, G, z)] = M("polished_andesite")
    # inlaid circle of the five elements on the plaza
    for k in range(60):
        a = math.radians(k * 6)
        x, z = round(28 + 7 * math.cos(a)), round(28 + 7 * math.sin(a))
        blocks[(x, G, z)] = M("amethyst_block") if k % 2 else M("oxidized_cut_copper")
    blocks[(28, G, 28)] = M("chiseled_quartz_block")
    # the avenue: praying path from the south edge to the plaza
    for z in range(40, SZ):
        wob = round(1.5 * math.sin(z / 4.0))
        for x in range(27 + wob, 30 + wob):
            blocks[(x, G, z)] = PRAY if x == 28 + wob else (LAB_STONE if rnd(x, 0, z, 62) < 0.7 else M("mossy_stone_bricks"))
        for x in (26 + wob, 30 + wob):
            if blocks.get((x, G, z)) == M("grass_block[snowy=false]"):
                blocks[(x, G, z)] = M("coarse_dirt")
    # elemental plinths
    for name, px, pz in PLINTHS:
        plinth(bp, name, px, pz)
    # low walls with lanterns along the avenue (every 6 blocks)
    for z in range(44, SZ - 2, 6):
        for x in (24, 32):
            put(bp, x, F, z, M("mossy_stone_brick_wall[east=false,north=false,south=false,up=true,waterlogged=false,west=false]"))
            put(bp, x, F + 1, z, M("lantern[hanging=false]"))
    # a few mossy fallen stones and ferns around
    for i in range(24):
        x, z = 4 + int(rnd(i, 1, 1, 71) * (SX - 8)), 20 + int(rnd(i, 2, 1, 71) * 34)
        if blocks.get((x, G, z)) == M("grass_block[snowy=false]") and blocks.get((x, F, z)) == AIR and math.hypot(x - 28, z - 28) > 15:
            put(bp, x, F, z, M("fern") if i % 3 else M("mossy_cobblestone"))
    # forest ring round the box
    for i in range(80):
        a = i * 2 * math.pi / 80 + rnd(i, 0, 0, 81) * 0.08
        r = 25.5 + rnd(i, 1, 0, 81) * 2
        x, z = round(28 + r * math.cos(a)), round(28 + r * math.sin(a))
        if 3 <= x < SX - 3 and 3 <= z < SZ - 3 and not tops.get((x, z)) and not 40 <= x < 46:
            tree(bp, x, G + 1, z, 7 + int(rnd(i, 2, 0, 81) * 4), leaves=("dark_oak" if i % 2 else "oak"), wide=2)

    # --- light ---------------------------------------------------------------------------------------------------
    cands = [(x, F, z) for x in range(SX) for z in range(SZ)
             if math.hypot(x - 28, z - 28) <= 15.5 or (26 <= x <= 30 and z >= 28) or (22 <= x <= 34 and 12 <= z <= 19)]

    def add_light(x, y, z):
        put(bp, x, y, z, M("mossy_stone_brick_wall[east=false,north=false,south=false,up=true,waterlogged=false,west=false]"))
        put(bp, x, y + 1, z, M("lantern[hanging=false]"))

    light_up(bp, cands, add_light, spread=10)
    return None


def outputs(bp):
    geo = {"size": list(SIZE), "anchor": list(ANCHOR), "portal": list(PORTAL), "arrival_yaw": 180}
    return {"pack/kubejs/server_scripts/ttl/generated/spirit_gate.js":
            "// priority: 200\n// GENERATED by tools/build_structures.py from blueprints/spirit_gate.py. Do not edit.\n"
            "// The doorway of the Dwelling's gate: PORTAL is an anchor-relative box [dx0, dy0, dz0, dx1, dy1, dz1]\n"
            "// (inclusive, block coordinates of the feet); a soul coming back arrives on the anchor.\n"
            f"const TtlSpiritGate = {json.dumps(geo, separators=(',', ':'))}\n"}
