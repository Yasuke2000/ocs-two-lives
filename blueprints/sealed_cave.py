"""The Sealed Cave: Veldora's prison and Rimuru's birthplace, in the Great Jura Forest (Life 2 canon landmark).

SIZE (88, 50, 88). Ground layer y 4 (grass, dirt and stone below), you walk at y 5. A rocky, mossy hill (about 70 blocks
across, up to 28 above the ground) rises from a forest clearing with the cave mouth in its south face; everything
above the ground layer that is not rock is air, so placement clears trees and hills inside the box. Arrival point:
blueprint (44, 5, 82), the path outside the mouth.

Inside, south to north (our interpretation of canon's "a big cave"): a winding mouth passage, the antechamber with a
cave pond, magic ore in the walls and a small hipokute plot (the cave later became Tempest's hipokute farm under Gabiru;
the magicules Veldora's aura soaked into the rock made the grass and the ore grow), a narrow dark passage, and the
sealed chamber: a round dome with the spent Unlimited Imprisonment seal. Veldora is already gone (Life 2 starts after
Rimuru swallowed him), so the dais is empty: snapped chains, claw gouges in the floor, the circle's runes dim and
cracked, the armillary rings of the barrier broken into arcs, six standing stones (two toppled). A small basin by the
south wall marks where a slime woke up. The cave is where the magicule of the Jura forest comes from: the chamber is
ringed with magic ore and amethyst, and a column of sea lanterns glows in its ceiling.

Every spawnable spot inside has block light (checked when this builds). Visual references and sources:
design/lore/sealed_cave.md.
"""
import math

import blueprint as _blueprint
from _dwargon_lib import AIR, fbm2, noise2, noise3, rnd
from _sites_lib import M, air_above, exposed, light_up, line, pick, put, ring_points, tree

SIZE = (88, 50, 88)
SX, SY, SZ = SIZE
G = 4
F = 5
ARRIVAL = (44, F, 82)
PARTS = [0, 30, 60]

CH = (44, 28)        # sealed chamber centre (x, z)
CH_R = (14, 13)      # radii x, z
CH_H = 15            # dome height above the floor layer
ANTE = (44, 57)      # antechamber centre
ANTE_R = (13, 9)
ANTE_H = 8

MOUND_C = (44, 40)
MOUND_R = (38, 34)
MOUND_H = 30

LANTERN = M("sea_lantern")
FROG = (M("verdant_froglight"), M("pearlescent_froglight"))

STONE_WALL = [(M("stone"), 40), (M("andesite"), 15), (M("tuff"), 15), (M("mossy_cobblestone"), 9),
              (M("cobblestone"), 6), (M("moss_block"), 6), (M("calcite"), 3), ("tensura:magic_ore", 3)]
DEEP_WALL = [(M("deepslate"), 48), (M("cobbled_deepslate"), 16), (M("tuff"), 8), (M("polished_deepslate"), 6),
             ("tensura:deepslate_magic_ore", 6), (M("amethyst_block"), 5), (M("calcite"), 3), (M("smooth_basalt"), 8)]


def dist2(x, z, c, r):
    return math.hypot((x - c[0]) / r[0], (z - c[1]) / r[1])


def mound_top(x, z) -> int:
    """Height of the hill above the ground layer at a column (0 = no hill)."""
    ex, ez = (x - MOUND_C[0]) / MOUND_R[0], (z - MOUND_C[1]) / MOUND_R[1]
    d = 1 - ex * ex - ez * ez
    if d <= 0:
        return 0
    h = MOUND_H * math.sqrt(d) + (fbm2(x, z, 14, 3) - 0.5) * 9
    h = min(h, 27 + (fbm2(x, z, 6, 8) - 0.5) * 3)
    if 36 <= x <= 52 and 60 <= z <= 74:  # the south face above the mouth must be tall enough to hold a roof
        h = max(h, 9 + (74 - z) * 0.3)
    return int(h) if h >= 2 else 0


def segment_dist(x, z, a, b):
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
    return math.hypot(x - (ax + t * dx), z - (az + t * dz))


def build(bp):
    blocks = bp.blocks
    air_above(bp, G)

    # --- ground: stone, dirt, grass ---------------------------------------------------------------
    for x in range(SX):
        for z in range(SZ):
            blocks[(x, 0, z)] = M("stone")
            for y in (1, 2, 3):
                blocks[(x, y, z)] = M("dirt") if y > 1 else M("stone")
            blocks[(x, G, z)] = M("grass_block[snowy=false]")

    # --- the hill ----------------------------------------------------------------------------------
    tops = {}
    for x in range(SX):
        for z in range(SZ):
            h = mound_top(x, z)
            if h:
                tops[(x, z)] = G + h
                for y in range(G + 1, G + h + 1):
                    blocks[(x, y, z)] = M("stone")

    # --- carve: ceiling map of everything walkable -------------------------------------------------
    ceil = {}

    def carve(x, z, c):
        c = min(c, SY - 2)
        if c > ceil.get((x, z), 0):
            ceil[(x, z)] = c

    for x in range(SX):
        for z in range(SZ):
            d = dist2(x, z, CH, CH_R)
            if d < 1:
                carve(x, z, F + CH_H * math.sqrt(1 - d * d) + (noise2(x, z, 5, 1) - 0.5) * 1.6)
            d = dist2(x, z, ANTE, ANTE_R)
            if d < 1:
                carve(x, z, F + ANTE_H * math.sqrt(1 - d * d) + (noise2(x, z, 4, 2) - 0.5) * 1.4)
    # mouth passage (winding), then the narrow passage between the antechamber and the sealed chamber
    mouth = [(44, 76), (41, 70), (44, 64), (44, 60)]
    narrow = [(44, 49), (40, 45), (45, 42), (44, 40)]
    for path, rh, rv in ((mouth, 3.4, 4.6), (narrow, 2.6, 3.6)):
        for x in range(SX):
            for z in range(SZ):
                d = min(segment_dist(x, z, a, b) for a, b in zip(path, path[1:]))
                if d < rh:
                    carve(x, z, F + rv * math.sqrt(1 - (d / rh) ** 2) + (noise2(x, z, 3, 4) - 0.5))

    interior = {}
    for (x, z), c in ceil.items():
        if c < F + 1.5 or (x, z) not in tops:
            continue  # too low to walk (leave it rock), or outside the hill (open ground)
        top = int(c)
        interior[(x, z)] = top
        for y in range(F, top + 1):
            blocks[(x, y, z)] = AIR
        # open the hill's skin only where the carve reaches it (mouth)
    for (x, z), top in list(interior.items()):
        if (x, z) in tops and tops[(x, z)] <= top + 1:  # never break the roof of the hill
            for y in range(top + 1, tops[(x, z)] + 1):
                blocks[(x, y, z)] = M("stone")
            # the roof cap must be solid: lower the ceiling instead
            new_top = max(F + 1, tops[(x, z)] - 2)
            for y in range(new_top + 1, top + 1):
                blocks[(x, y, z)] = M("stone")
            interior[(x, z)] = new_top

    # --- floors ------------------------------------------------------------------------------------
    pond = lambda x, z: math.hypot((x - 37) / 6.0, (z - 58) / 3.6) < 1
    farm_x = range(50, 58)
    farm_z = (53, 54, 55, 56, 57, 58, 59)  # z 56 is the water line
    for (x, z), top in interior.items():
        in_ch = dist2(x, z, CH, CH_R) < 1.0
        r = rnd(x, 0, z, 11)
        if in_ch:
            blocks[(x, G, z)] = pick([(M("deepslate_tiles"), 5), (M("polished_deepslate"), 4), (M("cracked_deepslate_tiles"), 2),
                                      (M("deepslate"), 2)], r)
        elif r < 0.22:
            blocks[(x, G, z)] = M("moss_block")
        elif r < 0.34:
            blocks[(x, G, z)] = M("gravel")
        elif r < 0.5:
            blocks[(x, G, z)] = M("coarse_dirt")
        else:
            blocks[(x, G, z)] = M("stone")

    # antechamber pond and hipokute plot
    for (x, z) in list(interior):
        if pond(x, z) and dist2(x, z, ANTE, ANTE_R) < 0.95:
            blocks[(x, 2, z)] = M("clay")
            blocks[(x, 3, z)] = M("water[level=0]")
            blocks[(x, G, z)] = M("water[level=0]")
    for x in farm_x:
        for z in farm_z:
            if (x, z) not in interior or interior[(x, z)] < F + 2:
                continue
            if z == 56:
                blocks[(x, G, z)] = M("water[level=0]")
                blocks[(x, 3, z)] = M("clay")
            else:
                blocks[(x, G, z)] = M("farmland[moisture=7]")
                blocks[(x, F, z)] = "tensura:hipokute_grass[age=%d]" % (3 if rnd(x, 1, z, 6) < 0.7 else 2)
    for x in (49, 58):  # edge of the plot
        for z in farm_z:
            if (x, z) in interior and blocks.get((x, F, z)) == AIR and rnd(x, 2, z, 7) < 0.6:
                blocks[(x, G, z)] = M("dirt")

    # --- walls: palette by position (only rock that touches cave air) ---------------------------------
    for (x, z), top in interior.items():
        deep = dist2(x, z, CH, (CH_R[0] + 3, CH_R[1] + 3)) < 1.0 or (z < 44 and 30 < x < 58)
        pal = DEEP_WALL if deep else STONE_WALL
        for y in range(F, top + 2):
            if blocks.get((x, y, z)) != AIR:
                continue
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1)):
                n = (x + dx, y + dy, z + dz)
                if blocks.get(n) == M("stone") and n[1] > G:
                    blocks[n] = pick(pal if dist2(n[0], n[2], CH, (CH_R[0] + 3, CH_R[1] + 3)) < 1.0 or (n[2] < 44 and 30 < n[0] < 58)
                                     else STONE_WALL, rnd(n[0], n[1], n[2], 21))

    # hill skin: grass on gentle ground, stone and moss on steep rock, trees
    for (x, z), t in tops.items():
        steep = max(abs(t - tops.get((x + dx, z + dz), G)) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        r = rnd(x, 3, z, 31)
        if steep >= 2 or noise2(x, z, 9, 17) < 0.42:  # rock outcrops among the grass
            blocks[(x, t, z)] = pick([(M("stone"), 3), (M("mossy_cobblestone"), 3), (M("andesite"), 2), (M("moss_block"), 2)], r)
        else:
            blocks[(x, t, z)] = M("grass_block[snowy=false]")
            for y in (t - 1, t - 2):
                if blocks.get((x, y, z)) == M("stone"):
                    blocks[(x, y, z)] = M("dirt")
            if r < 0.12:
                put(bp, x, t + 1, z, M("fern"))
            elif r < 0.2:
                put(bp, x, t + 1, z, M("short_grass"))
    # trees on the crown
    for i in range(34):
        x, z = 6 + int(rnd(i, 1, 0, 41) * (SX - 12)), 6 + int(rnd(i, 2, 0, 41) * (SZ - 12))
        t = tops.get((x, z))
        if not t or blocks.get((x, t, z)) != M("grass_block[snowy=false]") or (x, z) in interior:
            continue
        if blocks.get((x, t + 1, z)) != AIR:
            continue
        tree(bp, x, t + 1, z, 5 + int(rnd(i, 3, 0, 41) * 3), leaves="oak" if i % 3 else "dark_oak", wide=2)
    # forest ring round the box so the clearing does not end in a straight wall
    for i in range(70):
        a = i * 2 * math.pi / 70 + rnd(i, 0, 0, 51) * 0.08
        r = 41.5 + rnd(i, 1, 0, 51) * 2
        x, z = round(44 + r * math.cos(a)), round(44 + r * math.sin(a))
        if 3 <= x < SX - 3 and 3 <= z < SZ - 3 and not tops.get((x, z)):
            tree(bp, x, G + 1, z, 7 + int(rnd(i, 2, 0, 51) * 4), leaves=("dark_oak" if i % 2 else "oak"), wide=2)

    # --- the way in: path, boulders, a ruined arch of stones at the mouth ----------------------------
    for z in range(66, SZ):
        wob = round(2 * math.sin(z / 5.0))
        for x in range(42 + wob, 47 + wob):
            if blocks.get((x, F, z)) == AIR and blocks.get((x, G, z)) == M("grass_block[snowy=false]"):
                blocks[(x, G, z)] = M("dirt_path") if rnd(x, 0, z, 61) < 0.8 else M("coarse_dirt")
    for i, (bx, bz) in enumerate(((38, 79), (51, 78), (36, 70), (53, 71), (48, 83))):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) + abs(dz) < 2 or rnd(bx + dx, 0, bz + dz, 71) < 0.5:
                    put(bp, bx + dx, F, bz + dz, M("mossy_cobblestone"))
                    if dx == 0 and dz == 0:
                        put(bp, bx, F + 1, bz, M("mossy_cobblestone"))
    for x, z in ((40, 74), (48, 74)):  # weathered stones flanking the mouth
        for y in range(F, F + 4):
            put(bp, x, y, z, M("mossy_cobblestone") if y < F + 3 else M("mossy_stone_bricks"))
    put(bp, 41, F + 3, 73, M("cobblestone_stairs[facing=east,half=bottom]"))
    put(bp, 47, F + 3, 73, M("cobblestone_stairs[facing=west,half=bottom]"))

    # --- antechamber furniture --------------------------------------------------------------------------
    for x, z in ((46, 52), (47, 51), (52, 60), (36, 54), (34, 56)):
        if (x, z) in interior and blocks.get((x, F, z)) == AIR:
            blocks[(x, F, z)] = M("mossy_cobblestone")
    for x, z in ((49, 60), (49, 52)):
        if (x, z) in interior:
            put(bp, x, F, z, M("barrel[facing=up,open=false]"))

    # --- the sealed chamber: seal, dais, stones, rings, chains ----------------------------------------
    cx, cz = CH
    ring_floor = F - 1
    C_FLOOR_CYAN = M("oxidized_cut_copper")
    disc = lambda r, inner=-1: [(x, z) for x in range(cx - 15, cx + 16) for z in range(cz - 15, cz + 16)
                                if inner + 0.3 < math.hypot(x - cx, z - cz) <= r + 0.3]
    # outer double ring and an inner ring, runes dim: cut copper (teal) with a few sea lanterns still lit
    for x, z in disc(12, 11):
        blocks[(x, ring_floor, z)] = C_FLOOR_CYAN if rnd(x, 0, z, 91) < 0.78 else M("cracked_deepslate_tiles")
    for x, z in disc(8, 7):
        blocks[(x, ring_floor, z)] = C_FLOOR_CYAN if rnd(x, 0, z, 92) < 0.8 else M("cracked_deepslate_tiles")
    # hexagram between the rings: two triangles whose points lie on r = 10
    pts = [(round(cx + 10 * math.cos(math.radians(-90 + 60 * i))), round(cz + 10 * math.sin(math.radians(-90 + 60 * i))))
           for i in range(6)]
    for tri in ((0, 2, 4), (1, 3, 5)):
        for i in range(3):
            a, b = pts[tri[i]], pts[tri[(i + 1) % 3]]
            for k, (x, z) in enumerate(line(a[0], a[1], b[0], b[1])):
                if blocks.get((x, ring_floor, z)) is None or math.hypot(x - cx, z - cz) > 12:
                    continue
                blocks[(x, ring_floor, z)] = LANTERN if k % 6 == 3 and rnd(x, 1, z, 93) < 0.75 else (
                    C_FLOOR_CYAN if rnd(x, 2, z, 94) < 0.85 else M("cracked_deepslate_tiles"))
    for x, z in pts:  # vertex lamps and the six standing stones
        blocks[(x, ring_floor, z)] = LANTERN
    # the dais where the dragon lay
    for x, z in disc(4.6):
        blocks[(x, ring_floor, z)] = M("polished_blackstone")
        blocks[(x, F, z)] = M("polished_blackstone") if math.hypot(x - cx, z - cz) > 3.2 else M("blackstone")
    for x, z in disc(4.6, 3.6):
        blocks[(x, F, z)] = M("crying_obsidian") if rnd(x, 3, z, 95) < 0.7 else M("polished_blackstone")
    for x, z in disc(2.2):
        blocks[(x, F, z)] = M("obsidian")
    # claw gouges: five scored lines across the floor from the dais towards the south wall
    for k, off in enumerate((-4, -2, 0, 2, 4)):
        for x, z in line(cx + off, cz + 6, cx + off + (k - 2), cz + 12):
            if blocks.get((x, ring_floor, z)) not in (None, LANTERN):
                blocks[(x, ring_floor, z)] = M("blackstone") if rnd(x, 4, z, 96) < 0.8 else M("basalt[axis=y]")
    # six standing stones at r = 11, two broken
    for i, (x, z) in enumerate(bp.around(cx, cz, 11.0, 6, start_deg=-90)):
        height = (7, 6, 3, 7, 2, 6)[i]
        for y in range(F, F + height):
            blocks[(x, y, z)] = M("deepslate_bricks") if y % 3 else M("chiseled_deepslate")
        if height > 5:
            blocks[(x, F + height, z)] = M("crying_obsidian")
            blocks[(x, F + height + 1, z)] = M("end_rod[facing=up]")
        else:  # toppled: rubble beside the stump
            for dx, dz in ((1, 0), (0, 1), (-1, 0)):
                if rnd(x + dx, 0, z + dz, 97) < 0.6:
                    put(bp, x + dx, F, z + dz, M("cobbled_deepslate_slab[type=bottom,waterlogged=false]"))
    # the armillary: three rings of tinted glass round the dais, broken into arcs (the seal is spent)
    for plane, rad, cy in (("h", 9, 13), ("x", 6, 13), ("z", 6, 13)):
        for (px, py, pz), ang in ring_points(cx, cy, cz, rad, plane):
            if rnd(int(ang), 3, rad + (1 if plane == "x" else 2 if plane == "z" else 0), 98) < 0.36:
                continue  # missing arc
            if blocks.get((px, py, pz)) == AIR:
                blocks[(px, py, pz)] = M("light_blue_stained_glass")
    # glass shards on the dais and the floor
    for x, z in ((cx - 3, cz + 5), (cx + 5, cz + 2), (cx + 1, cz - 6), (cx - 6, cz - 3), (cx + 7, cz + 6)):
        if blocks.get((x, F, z)) == AIR:
            blocks[(x, F, z)] = M("light_blue_stained_glass_pane")
    # snapped chains hanging from the ceiling round the dais (and lying on it)
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        x, z = cx + dx, cz + dz
        top = interior.get((x, z), 18)
        for y in range(top, 12, -1):
            if blocks.get((x, y, z)) == AIR:
                blocks[(x, y, z)] = M("chain[axis=y,waterlogged=false]")
        blocks[(x, 12, z)] = M("iron_block")
    for x, z, axis in ((cx - 1, cz + 3, "x"), (cx + 2, cz - 2, "z"), (cx + 3, cz + 2, "x")):
        if blocks.get((x, F + 1, z)) == AIR:
            blocks[(x, F + 1, z)] = f"minecraft:chain[axis={axis},waterlogged=false]"
    # where a slime woke up: a small basin by the south wall
    bx, bz = cx - 10, cz + 7
    for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
        blocks[(bx + dx, G, bz + dz)] = M("water[level=0]")
        blocks[(bx + dx, 3, bz + dz)] = M("clay")
    for dx, dz in ((-1, 0), (2, 0), (-1, 1), (2, 1), (0, -1), (1, -1), (0, 2), (1, 2)):
        blocks[(bx + dx, G, bz + dz)] = M("moss_block")
        blocks[(bx + dx, F, bz + dz)] = M("moss_carpet")
    # magic ore and amethyst in the dome wall
    for (x, y, z), state in list(blocks.items()):
        if y > F + 1 and state == M("deepslate") and dist2(x, z, CH, CH_R) > 0.82 and rnd(x, y, z, 99) < 0.12:
            if exposed(blocks, x, y, z):
                blocks[(x, y, z)] = pick([("tensura:deepslate_magic_ore", 3), (M("amethyst_block"), 2),
                                          (M("budding_amethyst"), 1)], rnd(x, y, z, 100))

    # --- dressing: vines, dripstone, rubble, moss -----------------------------------------------------------
    for (x, z), top in interior.items():
        y = top + 1
        if blocks.get((x, y, z)) is None or blocks[(x, y, z)] == AIR:
            continue
        r = rnd(x, 7, z, 111)
        if r < 0.07:  # glow-berry vine
            n = 1 + int(rnd(x, 8, z, 112) * 4)
            for k in range(n):
                yy = top - k
                if yy <= F + 2 or blocks.get((x, yy, z)) != AIR:
                    break
                last = k == n - 1 or yy - 1 <= F + 2
                blocks[(x, yy, z)] = (M("cave_vines[age=20,berries=true]") if last else M("cave_vines_plant[berries=true]"))
        elif r < 0.13:  # stalactite
            if blocks.get((x, top, z)) == AIR and blocks.get((x, top - 1, z)) == AIR and top - 1 > F + 2:
                blocks[(x, top, z)] = M("pointed_dripstone[thickness=base,vertical_direction=down,waterlogged=false]")
                blocks[(x, top - 1, z)] = M("pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
            elif blocks.get((x, top, z)) == AIR:
                blocks[(x, top, z)] = M("pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    for (x, z), top in interior.items():
        if blocks.get((x, F, z)) != AIR or blocks.get((x, G, z)) in (None, M("water[level=0]"), M("farmland[moisture=7]")):
            continue
        # leave the seal area and the paths free
        if math.hypot(x - cx, z - cz) < 13.5 and dist2(x, z, CH, CH_R) < 1:
            continue
        near_wall = any((x + dx, z + dz) not in interior for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        r = rnd(x, 9, z, 121)
        if near_wall and r < 0.18:
            blocks[(x, F, z)] = M("pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
        elif r < 0.30 and blocks.get((x, G, z)) == M("moss_block"):
            blocks[(x, F, z)] = M("moss_carpet")
        elif r < 0.36:
            blocks[(x, F, z)] = M("glow_lichen[down=true]")

    # --- light: sea lanterns and froglights set in the ceiling, then whatever the check finds dark ------------
    for z0 in (40, 46, 51, 57, 63, 69, 74):  # mouth passage and antechamber ceiling lamps
        for (x, z), top in interior.items():
            if z == z0 and x in (43, 44, 45) and blocks.get((x, top + 1, z)) == M("stone"):
                blocks[(x, top + 1, z)] = FROG[(z0 // 6) % 2]
                break

    def add_light(x, y, z):
        # the nearest solid roof above the spot (or a lantern on the floor when there is none)
        yy = y + 1
        while yy < SY and blocks.get((x, yy, z)) == AIR:
            yy += 1
        if yy < SY and blocks.get((x, yy, z)) not in (None, AIR) and yy - y < 14 and "leaves" not in blocks[(x, yy, z)]:
            blocks[(x, yy, z)] = LANTERN if dist2(x, z, CH, CH_R) < 1 else FROG[(x + z) % 2]
        else:
            blocks[(x, y, z)] = M("lantern[hanging=false]")

    cands = [(x, y, z) for (x, z), top in interior.items() for y in range(F, min(top, F + 12) + 1)]
    light_up(bp, cands, add_light)
    # keep a dim cyan glow on the dais so the seal reads in the preview
    for x, z in ((cx - 5, cz), (cx + 5, cz), (cx, cz - 5), (cx, cz + 5)):
        blocks[(x, ring_floor, z)] = LANTERN

    bp.interior = interior
    return None
