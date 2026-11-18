"""The Armed Nation of Dwargon: the dwarf kingdom in a great cavern inside a pale sandstone mountain.

Lore notes and sources: design/lore/dwargon.md. SIZE (148, 92, 168), saved as three z slabs dwargon_0..2
(z 0-55, 56-111, 112-167; PARTS) placed side by side by life/dwargon.js. The gate faces south (+z). The
mountain is part of the build (stepped sandstone/terracotta massif, grass on its lower terraces, two spurs
flanking the gate); outside the mountain and the approach the corners are left empty and terrain stays.
Grounding: outputs() writes generated/dwargon_footprint.js (lowest block per column, open-sky columns),
which dwargon.js uses to fill the ground under the build and clear hills off the road (see there).
Outer road: from the south edge (z 167) past a checkpoint arch (z 160) and a road tower with a banner
(z 148-152, west), then fenced queue lanes for the gate inspection (z 114-125) between two guard booths, to
the white gate wall (back z 104, front face z 107, towers out to z 111 and up to y 29, yellow banners with
the red emblem). Gate opening x 71-77, y 4-11 (arch to y 13). Arrival point: blueprint (74, 4, 120) on the
road, facing north. A tunnel (z 94-106) leads into the cavern city: floor blocks at y 3 (you walk at y 4),
cavern z 14-100, about 44 wide on the streets and 63 at the plaza, vault up to y 53 with a canyon-like
skylight crack over the main street. Levels: the street (y 4), the royal terrace (y 8), wall homes on
balconies at y 18, 24 and 32 reached by ladders up stone props from the back alleys behind the houses, and
plank bridges hung on chains across the canyon street at y 24 linking facing homes. South street (z 68-94)
of stone and timber houses (2-4 storeys, lit windows, shop signs) including the Night Butterflies cabaret
(pink, west, z 83), lamps strung across the street; a round plaza (centre 74, 54, radius 17) with a
cogwheel fountain and twelve market stalls, a forge hall (west) and a Create workshop (east); the forge
street (z 34-43) with Kaijin's smithy (west, z 34); then a great stair (z 30-33) to the royal terrace
(floor y 7, landing z 28-29) and King Gazel's throne room: Tensura's own Gazel Dwargo boss arena
(blueprints/assets/gazel_throne.nbt, the dwarf_arena structure), its dais half (arena x 42-68) turned a quarter so
the throne faces south, at x 49-99, y 1-27, z 0-26 behind a tuff facade with a great door (z 27, x 71-77). The
arena's black glass shell became deepslate/tuff/stone (sandstone strata where it meets the open slope), the boss
pit and its warp pads were left out, the bulbs' redstone blocks became rock (bulbs stay lit). Throne seat
(74, 9, 11); dwargon.js seats Gazel there and restores the canon banner patterns. Chimneys smoke (campfires on
hay). Every spawnable spot inside has block light (checked when this builds).
"""
import json
import math
from pathlib import Path

from _dwargon_lib import AIR, dark_spots, fbm2, noise2, noise3, rnd

SIZE = (148, 92, 168)
SX, SY, SZ = SIZE
G = 3           # ground / city floor layer
CX = 74         # street centre line (x)
PLAZA_Z = 54    # plaza centre (z)
CAV_N, CAV_S = 14, 100
GATE_Z = 104    # back of the gate wall (front face at GATE_Z + 3)


def M(name: str) -> str:
    return "minecraft:" + name


# --- the mountain -----------------------------------------------------------------------------------
def heights() -> dict:
    """Top layer of the mountain per column: a rounded massif, steeper to north and south, terraced."""
    cx, cz, hx, hz, r = CX - 0.5, 60.0, 66.0, 56.0, 38.0
    H = {}
    for x in range(SX):
        for z in range(SZ):
            qx, qz = abs(x - cx) - (hx - r), abs(z - cz) - (hz - r)
            out = math.hypot(max(qx, 0), max(qz, 0)) + min(max(qx, qz), 0) - r
            t = -out + (fbm2(x, z, 18, 1) - 0.5) * 16
            t = min(t, x + 0.5, SX - 0.5 - x, z + 0.5, GATE_Z + 13 - z)  # stay inside the box, clear of the road
            if t <= 0:
                continue
            slope = 1.5 + 1.3 * fbm2(x, z, 20, 2) + 2.2 * min(1.0, abs(z - cz) / 54) ** 2
            ridge = math.exp(-((x - CX) / 42) ** 2)  # highest along the city's axis
            cap = 38 + 38 * ridge + 28 * (fbm2(x, z, 24, 3) - 0.4)
            raw = min(cap, t * slope)
            top = G + 3 * math.floor(raw / 3 + 0.45 * noise2(x, z, 6, 4))
            if top > G:
                H[(x, z)] = min(top, SY - 2)
    # Two rocky spurs reaching south on either side of the gate, so it sits deep in a ravine.
    for xs in (CX - 40, CX + 40):
        for x in range(xs - 20, xs + 21):
            for z in range(GATE_Z - 10, GATE_Z + 26):
                if not 0 <= x < SX:
                    continue
                bump = 48 * math.exp(-((x - xs) / 10) ** 2 - ((z - GATE_Z - 2) / 11) ** 2) * (0.75 + 0.5 * noise2(x, z, 5, 5))
                top = G + 3 * math.floor(bump / 3 + 0.45 * noise2(x, z, 6, 4))
                if top > H.get((x, z), G):
                    H[(x, z)] = top
    return H


def cav_top(z: float) -> float:
    return 50.0 if z >= 40 else 50 - (40 - z) * 0.7


def cav_base(z: float) -> float:
    e = min(z - CAV_N, CAV_S - z)
    if e < 0:
        return -1
    base = 22.0
    dz = z - PLAZA_Z
    if abs(dz) < 18:
        base = max(base, math.sqrt(324 - dz * dz) * 1.75)
    if e < 6:
        base *= math.sqrt(1 - ((6 - e) / 6.5) ** 2)
    return base


def cav_half(z: int, h: int, side: int) -> float:
    base = cav_base(z)
    if base < 0:
        return -1
    top = cav_top(z)
    wall = 0.55 * top
    if h > wall:
        r = (h - wall) / (top - wall)
        if r >= 1:
            return -1
        base *= math.sqrt(1 - r * r)
    return base + (noise2(h, z, 4, 40 + side) - 0.5) * 3.0


def cave_set(H: dict) -> set:
    """Cavern, entrance tunnel and the skylight crack above the street and plaza."""
    out = set()
    for z in range(CAV_N, CAV_S + 1):
        for h in range(1, 54):
            hw, he = cav_half(z, h, 0), cav_half(z, h, 1)
            if hw < 0 and he < 0:
                continue
            for x in range(CX - 44, CX + 45):
                dx = x - CX
                if (dx <= 0 and -dx <= hw) or (dx > 0 and dx <= he):
                    out.add((x, G + h, z))
    for z in range(CAV_S - 6, GATE_Z + 3):  # tunnel, arched
        for h in range(1, 12):
            half = 4 if h <= 9 else 3 if h == 10 else 1
            for x in range(CX - half, CX + half + 1):
                out.add((x, G + h, z))
    for (x, z), top in H.items():
        crack = False
        if 26 <= z <= CAV_S - 4:
            mid = CX + (noise2(0, z, 12, 50) - 0.5) * 4
            crack = abs(x - mid) <= 8 + 7 * noise2(1, z, 7, 51)
        if math.hypot(x - CX, z - PLAZA_Z) <= 16 + 4 * (noise2(x, z, 4, 52) - 0.5):
            crack = True
        if crack:
            for y in range(G + 20, top + 1):
                out.add((x, y, z))
    return out


def in_cleft(x: int, y: int, z: int) -> bool:
    start = GATE_Z if y <= G + 21 else GATE_Z - int(noise2(x, y, 4, 61) * 3)
    if z < start:
        return False
    hw = 24 + max(0, z - GATE_Z) * 0.5 + (y - G) * 0.22 + (noise2(y, z, 5, 60) - 0.5) * 3
    return abs(x - CX) <= hw


BANDS = ["smooth_sandstone", "sandstone", "smooth_sandstone", "white_terracotta", "sandstone",
         "smooth_sandstone", "terracotta", "smooth_sandstone", "sandstone", "white_terracotta"]


def outer_mat(x, y, z) -> str:
    n = noise3(x, y, z, 5, 12)
    if n > 0.8:
        return M("stone") if n < 0.87 else M("andesite")
    band = int((y + 6 * noise2(x, z, 18, 11)) // 4) % len(BANDS)
    return M(BANDS[band])


def cave_mat(x, y, z) -> str:
    n = noise3(x, y, z, 6, 21)
    if rnd(x, y, z, 22) < 0.012:
        return M("glowstone") if rnd(x, y, z, 23) < 0.6 else M("shroomlight")
    return M("stone" if n < 0.32 else "andesite" if n < 0.5 else "dripstone_block" if n < 0.7
             else "tuff" if n < 0.84 else "sandstone")


class City:
    def __init__(self, bp):
        self.bp = bp
        self.rock: set = set()      # natural mountain blocks (re-texturable, glow-replaceable)
        self.outside: set = set()   # open-air spots outside (normal terrain rules, not light-checked)
        self.homes: dict = {}       # (west, z0, y0) -> facade distance of each wall dwelling
        self.ladders = 0

    def put(self, x, y, z, state):
        self.bp.set(x, y, z, state)
        self.rock.discard((x, y, z))

    def get(self, x, y, z):
        return self.bp.blocks.get((x, y, z))

    def air(self, x, y, z):
        return self.bp.blocks.get((x, y, z)) == AIR


def terrain(c: City):
    bp = c.bp
    H = heights()
    cave = cave_set(H)
    cleft_cols = set()
    for (x, z), top in H.items():
        nb = [H.get((x + dx, z + dz), G) for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2))]
        low = min(nb)
        for y in range(top + 1):
            p = (x, y, z)
            if p in cave:
                bp.blocks[p] = AIR
                continue
            if y > G and z >= GATE_Z - 3 and in_cleft(x, y, z):
                bp.blocks[p] = AIR
                c.outside.add(p)
                cleft_cols.add((x, z))
                continue
            green = top <= G + 9 + 8 * noise2(x, z, 9, 15) and top - low <= 3
            if y == top and green:
                v = noise2(x, z, 5, 13)
                state = M("moss_block") if v > 0.72 else M("coarse_dirt") if v < 0.2 else M("grass_block")
            elif y >= top - 2 and green:
                state = M("dirt")
            elif y >= low - 1 or y == top:
                state = outer_mat(x, y, z)
            elif y >= low - 5:
                state = M("sandstone")
            else:
                state = M("stone")
            bp.blocks[p] = state
            c.rock.add(p)
        # A little growth on the gentle foot slopes.
        if bp.blocks.get((x, top, z)) == M("grass_block") and top + 1 < SY:
            v = rnd(x, top, z, 14)
            if v < 0.25:
                bp.blocks[(x, top + 1, z)] = M("short_grass")
            elif v < 0.29:
                bp.blocks[(x, top + 1, z)] = M("dandelion" if v < 0.27 else "poppy")
    # Re-texture the rock around the cavern; the cleft and the top of the crack show the outer strata.
    for (x, y, z) in cave:
        for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)):
            if n in c.rock and n not in cave:
                if y - G <= 12 and z >= CAV_S - 5:
                    bp.blocks[n] = M("stone_bricks") if rnd(*n, 24) < 0.7 else M("cracked_stone_bricks")
                elif y > H[(x, z)] - 6 and y > G + 36:
                    bp.blocks[n] = outer_mat(*n)
                else:
                    bp.blocks[n] = cave_mat(*n)
    for (x, y, z) in c.outside:
        for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z - 1)):
            if n in c.rock and bp.blocks[n] in (M("stone"), M("sandstone")):
                bp.blocks[n] = outer_mat(*n)
    # Cavern floor.
    for (x, y, z) in cave:
        if y == G + 1:
            p = (x, G, z)
            bp.blocks[p] = floor_mat(x, z)
            c.rock.discard(p)
    # Breaches: cavern air below the crack level that reaches the open mountain surface (should be none).
    c.breaches = sum(1 for (x, y, z) in cave if y < G + 20 and (x, y + 1, z) not in bp.blocks and y >= H.get((x, z), 0))
    return H, cave


def road_mix(x, z, seed=30) -> str:
    """The dwarf villages' road surface: cobblestone, tuff and gravel in about equal parts."""
    v = rnd(x, G, z, seed)
    return M("cobblestone") if v < 0.34 else M("tuff") if v < 0.67 else M("gravel")


def floor_mat(x, z) -> str:
    dx = x - CX
    v = rnd(x, G, z, 30)
    if abs(dx) <= 7:
        if abs(dx) == 7:
            return M("polished_andesite")
        return road_mix(x, z)
    return M("cobblestone") if v < 0.4 else M("stone") if v < 0.7 else M("tuff") if v < 0.85 else M("andesite")


# --- the approach and the gate -------------------------------------------------------------------
def approach(c: City, H: dict):
    bp = c.bp
    for x in range(CX - 44, CX + 45):
        for z in range(GATE_Z, SZ):
            mountain = (x, z) in H
            open_floor = mountain and bp.blocks.get((x, G + 1, z)) == AIR
            if mountain and not open_floor:
                continue
            for y in range(G):
                if (x, y, z) not in bp.blocks or not mountain:
                    bp.set(x, y, z, M("stone") if y == 0 else M("dirt"))
            v = noise2(x, z, 4, 70)
            bp.set(x, G, z, M("coarse_dirt") if v < 0.18 else M("grass_block"))
            c.rock.discard((x, G, z))
            top = max(G + 16, H.get((x, z), 0))
            for y in range(G + 1, min(top, SY - 1) + 1):
                if (x, y, z) not in bp.blocks or not mountain:
                    bp.set(x, y, z, AIR)
                    c.outside.add((x, y, z))
            if bp.blocks[(x, G, z)] == M("grass_block"):
                r = rnd(x, G, z, 71)
                if r < 0.22:
                    bp.set(x, G + 1, z, M("short_grass"))
                elif r < 0.26:
                    bp.set(x, G + 1, z, [M("poppy"), M("dandelion"), M("cornflower"), M("oxeye_daisy")][int(r * 100) % 4])
    # Road from the south edge to the gate, with an apron in front of the gate.
    for z in range(GATE_Z + 3, SZ):
        mid = CX if z < GATE_Z + 12 else CX + round((noise2(0, z, 10, 72) - 0.5) * 4)
        for x in range(mid - 3, mid + 4):
            edge = abs(x - mid) == 3
            if edge and rnd(x, G, z, 73) < 0.5:
                continue
            bp.set(x, G, z, M("coarse_dirt") if edge else M("dirt_path"))
            bp.set(x, G + 1, z, AIR)
        if z % 9 == 4 and z > GATE_Z + 10:  # lamp posts along the road, alternating sides
            px = mid - 5 if (z // 9) % 2 else mid + 5
            bp.set(px, G, z, M("cobblestone"))
            for y in range(G + 1, G + 4):
                bp.set(px, y, z, M("dark_oak_fence"))
            bp.set(px, G + 4, z, M("lantern[hanging=false]"))
    for x in range(CX - 7, CX + 8):
        for z in range(GATE_Z + 4, GATE_Z + 10):
            bp.set(x, G, z, M("polished_andesite") if (x + z) % 2 else M("stone_bricks"))
            bp.set(x, G + 1, z, AIR)
    # A few boulders and bushes beside the road.
    for i, (bx, bz) in enumerate(((CX - 14, GATE_Z + 18), (CX + 15, GATE_Z + 23), (CX - 22, GATE_Z + 29), (CX + 9, GATE_Z + 32), (CX - 9, GATE_Z + 11),
                                     (CX + 24, GATE_Z + 41), (CX - 30, GATE_Z + 47), (CX + 12, GATE_Z + 58))):
        if (bx, bz) in H:
            continue
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(bx + dx, G + 1, bz + dz, M("sandstone") if (dx + dz + i) % 3 else M("stone"))
        bp.set(bx, G + 2, bz, M("smooth_sandstone"))
    for i, (bx, bz) in enumerate(((CX - 18, GATE_Z + 13), (CX + 20, GATE_Z + 16), (CX + 13, GATE_Z + 29), (CX - 27, GATE_Z + 22), (CX + 26, GATE_Z + 31),
                                     (CX - 16, GATE_Z + 39), (CX + 32, GATE_Z + 52), (CX - 24, GATE_Z + 58), (CX + 18, GATE_Z + 45))):
        if (bx, bz) in H:
            continue
        for dx, dz, dy in ((0, 0, 1), (1, 0, 1), (0, 1, 1), (-1, 0, 1), (0, -1, 1), (0, 0, 2)):
            bp.set(bx + dx, G + dy, bz + dz, M("oak_leaves[persistent=true]") if i % 2 else M("azalea_leaves[persistent=true]"))


EMBLEMS = {
    3: [".R.", "RRR", ".R.", "...", "RRR"],
    4: [".RR.", "RRRR", "R..R", "RRRR", ".RR."],
    5: ["..R..", ".RRR.", "RR.RR", ".RRR.", "..R..", ".....", "RRRRR"],
    7: ["...R...", "..RRR..", ".RR.RR.", "RR...RR", ".RR.RR.", "..RRR..", "...R...", ".......", "RRRRRRR"],
}


def banner(c: City, at, w: int, h: int, rod_axis: str):
    """Tall yellow banner with a red Dwargon emblem; `at(i, r)` maps column i, row r (0 = rod) to a block."""
    for i in range(-1, w + 1):
        x, y, z = at(i, 0)
        if c.get(x, y, z) in (None, AIR):
            c.put(x, y, z, M(f"chain[axis={rod_axis}]"))
    emblem = EMBLEMS[w]
    for r in range(1, h):
        for i in range(w):
            if r == h - 1 and 0 < i < w - 1:
                continue  # swallowtail
            e = r - 2
            red = 0 <= e < len(emblem) and emblem[e][i] == "R"
            c.put(*at(i, r), M("red_wool") if red else M("yellow_wool"))


def gate(c: City):
    white, trim, base = M("smooth_quartz"), M("quartz_bricks"), M("calcite")
    z0, zf = GATE_Z, GATE_Z + 3
    # Curtain wall across the whole cleft, so nobody slips round the side.
    for x in range(CX - 30, CX + 31):
        for z in range(z0, zf + 1):
            for y in range(G + 1, G + 19):
                p = (x, y, z)
                if p in c.outside or abs(x - CX) <= 21:
                    state = base if y <= G + 2 else trim if y == G + 17 else white
                    c.put(x, y, z, state)
                    c.outside.discard(p)
            if c.get(x, G + 18, z) == white and z == zf and x % 2 == 0:
                c.put(x, G + 19, z, trim)
                c.outside.discard((x, G + 19, z))

    def tower(x1, x2, z2, top):
        for x in range(x1, x2 + 1):
            for z in range(z0 - 1, z2 + 1):
                for y in range(G + 1, top + 1):
                    edge = x in (x1, x2) or z in (z0 - 1, z2)
                    state = base if y <= G + 2 else trim if (y - G) % 8 == 0 else white
                    c.put(x, y, z, state if edge or y == top else white)
                    c.outside.discard((x, y, z))
                if x in (x1, x2) or z in (z0 - 1, z2):
                    if (x + z) % 2 == 0 or (x in (x1, x2) and z in (z0 - 1, z2)):
                        c.put(x, top + 1, z, trim)
        for x, z in ((x1, z2), (x2, z2)):
            c.put(x, top + 2, z, M("lantern[hanging=false]"))
        mid = (x1 + x2) // 2
        for y in range(G + 10, top - 2, 6):  # arrow slits
            c.put(mid, y, z2, M("black_stained_glass_pane"))
            c.put(mid, y + 1, z2, M("black_stained_glass_pane"))

    tower(CX - 21, CX - 15, GATE_Z + 7, G + 26)
    tower(CX + 15, CX + 21, GATE_Z + 7, G + 26)
    tower(CX - 11, CX - 5, GATE_Z + 6, G + 22)
    tower(CX + 5, CX + 11, GATE_Z + 6, G + 22)
    # Gatehouse with the great arch.
    for x in range(CX - 4, CX + 5):
        for z in range(z0, zf + 2):
            for y in range(G + 1, G + 21):
                c.put(x, y, z, base if y <= G + 2 else trim if y in (G + 17, G + 20) else white)
            if (x + z) % 2 == 0:
                c.put(x, G + 21, z, trim)
    for z in range(z0, zf + 2):
        for y in range(G + 1, G + 11):
            half = 3 if y <= G + 8 else 2 if y == G + 9 else 1
            for x in range(CX - half, CX + half + 1):
                c.put(x, y, z, AIR)
                c.outside.discard((x, y, z))
    for x, y in ((CX - 4, G + 9), (CX + 4, G + 9), (CX - 3, G + 10), (CX + 3, G + 10), (CX - 2, G + 11),
                 (CX + 2, G + 11), (CX - 1, G + 11), (CX + 1, G + 11)):
        c.put(x, y, zf + 1, M("chiseled_quartz_block"))
    c.put(CX, G + 11, zf + 1, M("gold_block"))
    for y, half in ((G + 8, 3), (G + 9, 2), (G + 10, 1)):  # raised portcullis
        for x in range(CX - half, CX + half + 1):
            c.put(x, y, z0 + 2, M("iron_bars"))
    c.put(CX, G + 10, z0, M("lantern[hanging=true]"))
    # Banners: big ones on the towers, a wide one over the arch.
    for x0, zb, top in ((CX - 20, GATE_Z + 8, G + 24), (CX + 16, GATE_Z + 8, G + 24),
                        (CX - 10, GATE_Z + 7, G + 20), (CX + 6, GATE_Z + 7, G + 20)):
        banner(c, lambda i, r, x0=x0, zb=zb, top=top: (x0 + i, top - r, zb), 5, 13, "x")
    banner(c, lambda i, r: (CX - 3 + i, G + 19 - r, zf + 2), 7, 8, "x")
    # Lamps flanking the arch.
    for x in (CX - 6, CX + 6):
        c.put(x, G + 1, GATE_Z + 9, M("chiseled_quartz_block"))
        c.put(x, G + 2, GATE_Z + 9, M("dark_oak_fence"))
        c.put(x, G + 3, GATE_Z + 9, M("lantern[hanging=false]"))


# --- houses -----------------------------------------------------------------------------------------
# Dwarf-village look (Tensura's dwarf_village pieces, design/lore/dwargon.md): walls of stone and andesite with
# polished andesite corners on a cobblestone foundation, stripped spruce posts, low roofs of weathered cut
# copper trimmed with granite, glass panes with open spruce trapdoor shutters, spruce doors.
STYLES = [
    dict(beam="spruce_log", post="stripped_spruce_wood", door="spruce_door", pane="glass_pane", roof="copper"),
    dict(beam="stripped_spruce_log", post="stripped_spruce_wood", door="spruce_door", pane="glass_pane", roof="copper"),
    dict(beam="spruce_log", post="stripped_spruce_wood", door="spruce_door", pane="light_gray_stained_glass_pane", roof="copper"),
    dict(beam="stripped_spruce_log", post="stripped_spruce_wood", door="spruce_door", pane="glass_pane", roof="granite"),
    # The elf cabaret (Night Butterflies): plastered front, pink and purple light.
    dict(beam="cherry_log", post="stripped_cherry_wood", door="cherry_door", pane="magenta_stained_glass_pane",
         roof="copper", infill="pink_terracotta", base="polished_deepslate"),
]


def village_wall(x, y, z) -> str:
    """Stone and andesite in about equal parts, a few cracked stone bricks (the dwarf villages' walls)."""
    v = rnd(x, y, z, 101)
    return M("stone" if v < 0.46 else "andesite" if v < 0.92 else "cracked_stone_bricks")


def copper_deck(x, y, z) -> str:
    """Weathered cut copper with patches of exposed copper (the patina of the village roofs)."""
    return M("waxed_exposed_cut_copper" if noise2(x, z, 3, 102 + y) > 0.68 else "waxed_weathered_cut_copper")


def shutters(c: City, x, y, zs, out: str):
    """Open spruce trapdoors folded flat against the wall either side of a window (outside face at x)."""
    for z in zs:
        if c.air(x, y, z):
            c.put(x, y, z, M(f"spruce_trapdoor[facing={out},half=bottom,open=true]"))


def house(c: City, west: bool, z0: int, w: int, storeys: int, style: int, chimney=False, sign=False, d=8,
          smithy=False):
    """A narrow dwarven house on the street: stone walls on a cobblestone footing, jettied upper storeys of
    stone between spruce posts and beams, a low copper roof (brick on Kaijin's smithy)."""
    s = STYLES[style % len(STYLES)]
    wall = (lambda x, y, z: M(s["infill"])) if "infill" in s else village_wall
    xf = CX - 8 if west else CX + 8
    out, inn = ("east", "west") if west else ("west", "east")

    def X(u):
        return xf - u if west else xf + u
    z1 = z0 + w - 1
    zmid = z0 + w // 2
    top = G + 4 * storeys
    # Ground storey.
    for u in range(d):
        for z in range(z0, z1 + 1):
            edge = u in (0, d - 1) or z in (z0, z1)
            c.put(X(u), G, z, M("cobblestone") if edge else M("spruce_planks"))
            for y in range(G + 1, G + 4):
                if not edge:
                    c.put(X(u), y, z, AIR)
                elif u in (0, d - 1) and z in (z0, z1):
                    c.put(X(u), y, z, M(s.get("base", "polished_andesite")))
                elif y == G + 1:
                    c.put(X(u), y, z, M("stone_bricks") if rnd(X(u), y, z, 103) < 0.7 else M("cracked_stone_bricks"))
                else:
                    c.put(X(u), y, z, wall(X(u), y, z))
    # Upper storeys, jettied one block over the street.
    for k in range(1, storeys + 1):
        yf = G + 4 * k
        for u in range(-1, d):
            for z in range(z0, z1 + 1):
                rim = u in (-1, d - 1) or z in (z0, z1)
                if rim and u in (-1, d - 1):
                    c.put(X(u), yf, z, M(s["beam"] + "[axis=z]"))
                elif rim:
                    c.put(X(u), yf, z, M(s["beam"] + "[axis=x]"))
                else:
                    c.put(X(u), yf, z, M("spruce_planks"))
                if k == storeys:
                    continue
                for y in range(yf + 1, yf + 4):
                    if not rim:
                        c.put(X(u), y, z, AIR)
                    elif u in (-1, d - 1) and z in (z0, z1):
                        c.put(X(u), y, z, M(s["post"] + "[axis=y]"))
                    else:
                        c.put(X(u), y, z, wall(X(u), y, z))
            if k < storeys:
                wins = list(range(z0 + 1, z1, 2))
                for z in wins:
                    for y in (yf + 1, yf + 2):
                        c.put(X(-1), y, z, M(s["pane"]))
                flank = sorted({z + dz for z in wins for dz in (-1, 1)} - set(wins))
                shutters(c, X(-2), yf + 2, [z for z in flank if z0 <= z <= z1], out)
    # Roof: low, as in the villages. A ring of stairs over the eaves, a flat deck, a raised ridge deck.
    kind = "brick" if smithy else s["roof"]
    if kind == "copper":
        stair, slab, deck = M("waxed_weathered_cut_copper_stairs"), M("waxed_weathered_cut_copper_slab"), copper_deck
    elif kind == "brick":
        stair, slab, deck = M("brick_stairs"), M("brick_slab"), (lambda x, y, z: M("bricks"))
    else:  # the flat mottled cap of the small village houses
        stair, slab = M("polished_granite_stairs"), M("polished_granite_slab")
        deck = lambda x, y, z: M(("granite", "polished_granite", "mud_bricks", "packed_mud")[int(rnd(x, y, z, 104) * 4)])
    trim = M("polished_granite_stairs") if kind == "copper" else stair
    y = top + 1
    for u in range(-2, d):
        for z, f in ((z0 - 1, "south"), (z1 + 1, "north")):
            c.put(X(u), y - 1, z, (trim if u == -2 else stair) + f"[facing={f},half=bottom]")
        if u >= -1:
            for z in range(z0, z1 + 1):
                corner = u in (-1, d - 1) and z in (z0, z1)
                c.put(X(u), y, z, M("polished_granite") if corner and kind == "copper" else deck(X(u), y, z))
    for z in range(z0, z1 + 1):
        c.put(X(-2), y - 1, z, stair + f"[facing={inn},half=bottom]")
    if w >= 5:
        for u in range(1, d - 2):
            for z in range(z0 + 1, z1):
                c.put(X(u), y + 1, z, slab + "[type=bottom]")
    # Ground floor front: door, windows with shutters, sign.
    c.put(X(0), G + 1, zmid, M(f"{s['door']}[facing={inn},half=lower,hinge=left,open=false]"))
    c.put(X(0), G + 2, zmid, M(f"{s['door']}[facing={inn},half=upper,hinge=left,open=false]"))
    for z in (z0 + 1, z1 - 1):
        if z != zmid:
            c.put(X(0), G + 2, z, M(s["pane"]))
            shutters(c, X(-1), G + 2, [zz for zz in (z - 1, z + 1) if z0 <= zz <= z1 and zz != zmid], out)
    if sign:
        c.put(X(-1), G + 3, z1, M("dark_oak_wall_hanging_sign[facing=north]"))
    # Inside: a lantern per storey, a ladder, and maybe a smoking chimney (cobbled deepslate; brick at the smithy).
    for k in range(storeys):
        c.put(X(d // 2), G + 4 * k + 1, zmid, M("lantern[hanging=false]"))
    for y in range(G + 1, G + 4 * (storeys - 1) + 1):
        c.put(X(d - 2), y, z1 - 1, M(f"ladder[facing={out}]"))
    if chimney:
        cz = z0 + 1
        ytop = top + 5
        for y in range(G + 1, ytop - 1):
            c.put(X(d - 2), y, cz, M("bricks") if smithy else M("cobbled_deepslate"))
        c.put(X(d - 2), ytop - 1, cz, M("hay_block[axis=y]"))
        c.put(X(d - 2), ytop, cz, M("campfire[facing=north,lit=true,signal_fire=true]"))


def dwellings(c: City):
    """Homes carved into the cavern walls above the street: a facade, a lit room, a balcony on a bracket."""
    spots = [(z0, y0) for z0 in range(31, CAV_S - 4, 7) for y0 in (G + 20, G + 28)]
    spots += [(z0, G + 14) for z0 in (40, 64, 78, 92)]
    for west in (True, False):
        sgn = -1 if west else 1
        for i, (z0, y0) in enumerate(spots):
            z1 = z0 + 4
            # The facade plane: the nearest rock of the wall over the whole front.
            near = None
            for z in range(z0, z1 + 1):
                for y in range(y0, y0 + 5):
                    d = 0
                    while d < 46 and c.air(CX + sgn * d, y, z):
                        d += 1
                    if d >= 46 or (CX + sgn * d, y, z) not in c.rock:
                        near = -1
                        break
                    near = d if near is None else min(near, d)
                if near == -1:
                    break
            if near is None or near < 17:
                continue

            def X(u):
                return CX + sgn * (near + u)
            room_ok = all((X(u), y, z) in c.rock or c.air(X(u), y, z)
                          for u in range(0, 6) for y in range(y0, y0 + 5) for z in range(z0, z1 + 1))
            ledge_ok = all(c.air(X(u), y, z) for u in (-2, -1) for y in (y0, y0 + 1) for z in range(z0, z1 + 1))
            if not (room_ok and ledge_ok):
                continue
            out = "east" if west else "west"
            back = "west" if west else "east"
            for z in range(z0, z1 + 1):
                for y in range(y0, y0 + 5):
                    edge = z in (z0, z1) or y in (y0, y0 + 4)
                    c.put(X(0), y, z, M("chiseled_stone_bricks") if y == y0 + 4 and z == (z0 + z1) // 2
                          else M("stone_bricks") if edge else M("packed_mud"))
                    for u in range(1, 5):
                        inside = z0 < z < z1 and y0 < y < y0 + 4
                        c.put(X(u), y, z, AIR if inside else M("stone"))
                    c.put(X(5), y, z, M("stone"))
                c.put(X(-1), y0, z, M("polished_andesite"))
                c.put(X(-2), y0, z, M("polished_andesite"))
                c.put(X(-2), y0 + 1, z, M("dark_oak_fence"))
                c.put(X(-1), y0 - 1, z, M(f"stone_brick_stairs[facing={back},half=top]"))
            for z in (z0, z1):
                c.put(X(-1), y0 + 1, z, M("dark_oak_fence"))
            zm = (z0 + z1) // 2
            c.put(X(0), y0 + 1, zm, M(f"spruce_door[facing={back},half=lower,hinge=left,open=false]"))
            c.put(X(0), y0 + 2, zm, M(f"spruce_door[facing={back},half=upper,hinge=left,open=false]"))
            for z in (z0 + 1, z1 - 1):
                c.put(X(0), y0 + 2, z, M("orange_stained_glass_pane"))
            c.put(X(3), y0 + 1, zm, M("lantern[hanging=false]"))
            c.put(X(-2), y0 + 2, z0, M("lantern[hanging=false]"))
            if i % 3 == 0:
                c.put(X(-1), y0 + 3, z1, M(f"dark_oak_wall_hanging_sign[facing=north]"))
            for p in [(X(u), y, z) for u in range(0, 6) for y in range(y0, y0 + 5) for z in range(z0, z1 + 1)]:
                c.rock.discard(p)
            c.homes[(west, z0, y0)] = near
            # A ladder up a stone-brick prop from the back alley, beside the balcony.
            for zl, zin in ((z0 - 1, z0), (z1 + 1, z1)):
                xs, xp = X(-2), X(-1)
                floor = c.get(xs, G, zl)
                if floor in (None, AIR) or not all(c.air(xs, y, zl) for y in range(G + 1, y0 + 2)):
                    continue
                for y in range(G + 1, y0 + 2):
                    if c.air(xp, y, zl):
                        c.put(xp, y, zl, M("stone_bricks"))
                        c.rock.discard((xp, y, zl))
                    c.put(xs, y, zl, M(f"ladder[facing={out}]"))
                c.put(xs, y0 + 1, zin, AIR)
                c.ladders += 1
                break


def lamp_post(c: City, x, z, height=3):
    for y in range(G + 1, G + 1 + height):
        c.put(x, y, z, M("dark_oak_fence"))
    c.put(x, G + 1 + height, z, M("lantern[hanging=false]"))


def hang(c: City, x, z, y_low, lantern=True):
    """Chain from the first solid block above y_low down to y_low, with a lantern at the bottom."""
    y = y_low
    while y < SY - 1 and c.air(x, y, z):
        y += 1
    if y >= SY - 1 or c.get(x, y, z) is None:
        return
    for yy in range(y_low + 1, y):
        c.put(x, yy, z, M("chain[axis=y]"))
    c.put(x, y_low, z, M("lantern[hanging=true]") if lantern else M("chain[axis=y]"))


def string_lights(c: City, z, y, drops=(-4, 0, 4)):
    """A chain strung across the cavern from wall to wall, with lanterns hanging from it."""
    x = CX
    while c.air(x - 1, y, z):
        x -= 1
    x2 = CX
    while c.air(x2 + 1, y, z):
        x2 += 1
    for xx in range(x, x2 + 1):
        c.put(xx, y, z, M("chain[axis=x]"))
    for i, dx in enumerate(drops):
        length = 3 + (i + z) % 3
        for yy in range(y - length, y):
            c.put(CX + dx, yy, z, M("chain[axis=y]"))
        c.put(CX + dx, y - length - 1, z, M("lantern[hanging=true]"))


# --- city districts ---------------------------------------------------------------------------------
def streets(c: City):
    # South street (gate to plaza) and the forge street (plaza to the royal terrace).
    rows = [
        (True, [(68, 5, 3, 0, True, True), (73, 5, 4, 1, False, True), (78, 5, 2, 2, True, False),
                (83, 6, 3, 4, True, True), (89, 5, 4, 3, False, True)]),
        (False, [(68, 4, 3, 3, False, True), (72, 6, 4, 0, True, False), (78, 5, 3, 1, False, True),
                 (83, 5, 2, 2, True, True), (88, 6, 3, 0, True, False)]),
        (True, [(34, 5, 3, 2, True, True), (39, 5, 2, 3, True, False)]),
        (False, [(34, 5, 2, 1, True, True), (39, 5, 3, 2, False, True)]),
    ]
    for west, houses in rows:
        for z0, w, storeys, style, chim, sign in houses:
            house(c, west, z0, w, storeys, style, chimney=chim, sign=sign, smithy=west and z0 == 34)
    for z in range(36, CAV_S - 2, 6):
        lamp_post(c, CX - 5 if z % 12 else CX + 5, z)
    for z in (37, 42, 67, 71, 80, 84, 92):
        string_lights(c, z, G + 21 if z > 60 else G + 19)


def plaza(c: City):
    for x in range(CX - 17, CX + 18):
        for z in range(PLAZA_Z - 17, PLAZA_Z + 18):
            d = math.hypot(x - CX, z - PLAZA_Z)
            if d > 17.3 or not c.air(x, G + 1, z):
                continue
            if abs(x - CX) <= 1 or abs(z - PLAZA_Z) <= 1:
                state = M("stone_bricks") if rnd(x, G, z, 31) < 0.8 else M("cracked_stone_bricks")
            elif d > 16.4:
                state = M("polished_andesite")
            else:
                state = road_mix(x, z, 32)
            c.put(x, G, z, state)
    # Fountain: a basin with a column crowned by a great cogwheel.
    for x in range(CX - 4, CX + 5):
        for z in range(PLAZA_Z - 4, PLAZA_Z + 5):
            d = math.hypot(x - CX, z - PLAZA_Z)
            if d <= 2.6:
                c.put(x, G, z, M("stone_bricks"))
                c.put(x, G + 1, z, M("water"))
            elif d <= 3.9:
                dx, dz = x - CX, z - PLAZA_Z
                if abs(abs(dx) - abs(dz)) <= 1 and abs(dx) > 1 and abs(dz) > 1:
                    c.put(x, G + 1, z, M("stone_brick_slab[type=bottom]"))
                elif abs(dx) > abs(dz):
                    c.put(x, G + 1, z, M("stone_brick_stairs[facing=" + ("west" if dx > 0 else "east") + "]"))
                else:
                    c.put(x, G + 1, z, M("stone_brick_stairs[facing=" + ("north" if dz > 0 else "south") + "]"))
    for y in range(G + 1, G + 6):
        c.put(CX, y, PLAZA_Z, M("chiseled_stone_bricks"))
    c.put(CX, G + 6, PLAZA_Z, M("gold_block"))
    c.put(CX, G + 7, PLAZA_Z, "create:large_cogwheel[axis=y]")
    c.put(CX, G + 8, PLAZA_Z, "create:shaft[axis=y]")
    for x, z in c.bp.around(CX, PLAZA_Z, 6, 4, start_deg=45):
        lamp_post(c, x, z)
    for x, z in c.bp.around(CX, PLAZA_Z, 15, 10, start_deg=18):
        lamp_post(c, x, z, 4)
    # Market stalls.
    # As the villages' plaza/shop_1..8: oak fence posts, white awnings striped with one colour, an oak counter
    # with a trapdoor lid, a chest and a lantern.
    awnings = [(col + "_wool", "white_wool") for col in ("blue", "green", "orange", "red", "cyan", "pink")] * 2
    stalls = list(c.bp.around(CX, PLAZA_Z, 9, 4, start_deg=0)) + list(c.bp.around(CX, PLAZA_Z, 12, 8, start_deg=22.5))
    for i, (sx, sz) in enumerate(stalls):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) == 1 and abs(dz) == 1:
                    c.put(sx + dx, G + 1, sz + dz, M("oak_fence"))
                    c.put(sx + dx, G + 2, sz + dz, M("oak_fence"))
                c.put(sx + dx, G + 3, sz + dz, M(awnings[i][(dx if i % 2 else dz) % 2]))
        c.put(sx, G + 1, sz, M("oak_planks"))
        c.put(sx, G + 2, sz, M("lantern[hanging=false]"))
        ox, oz = (1, 0) if i % 2 else (0, 1)
        c.put(sx + ox, G + 1, sz + oz, M("oak_trapdoor[facing=north,half=top,open=false]"))
        c.put(sx - ox, G + 1, sz - oz, M("chest[facing=north,type=single]") if i % 3 else M("barrel[facing=up]"))
    # Lamps hanging from the vault around the skylight.
    for x, z in c.bp.around(CX, PLAZA_Z, 19, 12, start_deg=0):
        hang(c, x, z, G + 18)


def forge_hall(c: City):
    """West of the plaza: an open-fronted forge with three smoking chimneys and cogs on its face."""
    x1, x2, z1, z2 = CX - 28, CX - 16, PLAZA_Z - 8, PLAZA_Z + 8
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            c.put(x, G, z, M("cobblestone") if edge else M("stone_bricks") if rnd(x, G, z, 33) < 0.6 else M("tuff"))
            for y in range(G + 1, G + 11):
                if y == G + 10:
                    c.put(x, y, z, copper_deck(x, y, z) if not corner else M("polished_granite"))
                elif corner:
                    c.put(x, y, z, M("polished_andesite"))
                elif edge:
                    c.put(x, y, z, M("waxed_weathered_cut_copper") if y == G + 5
                          else M("stone_bricks") if y == G + 1 else village_wall(x, y, z))
                else:
                    c.put(x, y, z, AIR)
            if edge and not corner:  # the low copper eave ring
                f = "east" if x == x1 else "west" if x == x2 else "south" if z == z1 else "north"
                c.put(x, G + 11, z, M(f"waxed_weathered_cut_copper_stairs[facing={f},half=bottom]"))
            elif corner:
                c.put(x, G + 11, z, M("polished_granite_slab[type=bottom]"))
    for z in range(z1 + 1, z2):  # arcade on stripped spruce piers
        for y in range(G + 1, G + 5):
            c.put(x2, y, z, AIR if (z - z1) % 4 != 0 else M("stripped_spruce_wood[axis=y]"))
    for z in range(z1 + 2, z2 - 1, 5):
        c.put(x2 + 1, G + 7, z, "create:large_cogwheel[axis=x]")
        for zz in range(z + 1, min(z + 5, z2 - 1)):
            c.put(x2 + 1, G + 7, zz, "create:shaft[axis=z]")
    for i, z in enumerate((z1 + 3, PLAZA_Z, z2 - 3)):  # chimneys
        for x in range(x1 + 1, x1 + 4):
            for zz in range(z - 1, z + 2):
                for y in range(G + 1, G + 17):
                    c.put(x, y, zz, M("bricks"))
        c.put(x1 + 2, G + 17, z, M("hay_block[axis=y]"))
        c.put(x1 + 2, G + 18, z, M("campfire[facing=north,lit=true,signal_fire=true]"))
        c.put(x1 + 4, G + 1, z, M("blast_furnace[facing=east,lit=true]"))
        c.put(x1 + 4, G + 2, z, M("furnace[facing=east,lit=true]"))
        c.put(x1 + 6, G + 1, z, M("anvil[facing=north]") if i != 1 else M("smithing_table"))
        c.put(x1 + 6, G + 1, z + 2, M("lava_cauldron"))
        c.put(x1 + 8, G + 1, z - 1, M("grindstone[face=floor,facing=east]") if i == 1 else M("water_cauldron[level=3]"))
    for z in range(z1 + 2, z2, 4):
        hang(c, x2 - 3, z, G + 7)
    for x in range(x1 - 4, x1):  # seal the back against the rock
        for z in range(z1 - 1, z2 + 2):
            for y in range(G + 1, G + 19):
                if c.air(x, y, z):
                    c.put(x, y, z, cave_mat(x, y, z))
                    c.rock.add((x, y, z))


def workshop(c: City):
    """East of the plaza: the engineers' workshop, all casings, shafts and cogwheels."""
    x1, x2, z1, z2 = CX + 16, CX + 28, PLAZA_Z - 8, PLAZA_Z + 8
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            c.put(x, G, z, M("polished_andesite"))
            for y in range(G + 1, G + 13):
                edge = x in (x1, x2) or z in (z1, z2)
                if y == G + 12:
                    c.put(x, y, z, "create:brass_casing" if edge else M("dark_oak_planks"))
                elif edge:
                    band = y in (G + 4, G + 8)
                    c.put(x, y, z, "create:brass_casing" if band else "create:andesite_casing" if (x + z + y) % 5 == 0 else M("stone_bricks"))
                else:
                    c.put(x, y, z, AIR)
    for z in range(z1 + 2, z2 - 1, 4):  # tall windows and a wide door
        for y in range(G + 5, G + 8):
            c.put(x1, y, z, M("glass_pane"))
            c.put(x1, y, z + 1, M("glass_pane"))
    for z in range(PLAZA_Z - 1, PLAZA_Z + 2):
        for y in range(G + 1, G + 4):
            c.put(x1, y, z, AIR)
    for z in (z1 + 3, z2 - 3):
        c.put(x1 - 1, G + 10, z, "create:large_cogwheel[axis=x]")
        c.put(x1 - 1, G + 6, z, "create:cogwheel[axis=x]")
        for y in range(G + 7, G + 10):
            c.put(x1 - 1, y, z, "create:shaft[axis=y]")
    for zz in range(z1 + 4, z2 - 3):
        c.put(x1 - 1, G + 10, zz, "create:shaft[axis=z]")
    # Inside: a drive train along the ceiling.
    for z in range(z1 + 1, z2):
        c.put(x1 + 6, G + 10, z, "create:shaft[axis=z]")
    for z in range(z1 + 2, z2 - 1, 4):
        c.put(x1 + 6, G + 10, z, "create:large_cogwheel[axis=z]")
        c.put(x1 + 6, G + 1, z, "create:copper_casing")
        c.put(x1 + 6, G + 2, z, "create:cogwheel[axis=y]")
        c.put(x1 + 3, G + 1, z, M("crafting_table") if z % 3 else M("smithing_table"))
        c.put(x1 + 9, G + 1, z, M("barrel[facing=up]"))
    for z in range(z1 + 2, z2, 4):
        hang(c, x1 + 3, z, G + 8)
        hang(c, x1 + 9, z, G + 8)
    # Steam stacks of copper.
    for z in (z1 + 2, z2 - 2):
        for y in range(G + 13, G + 18):
            c.put(x2 - 2, y, z, M("cut_copper"))
        c.put(x2 - 2, G + 18, z, M("hay_block[axis=y]"))
        c.put(x2 - 2, G + 19, z, M("campfire[facing=north,lit=true,signal_fire=true]"))
    for x in range(x2 + 1, x2 + 5):
        for z in range(z1 - 1, z2 + 2):
            for y in range(G + 1, G + 20):
                if c.air(x, y, z):
                    c.put(x, y, z, cave_mat(x, y, z))
                    c.rock.add((x, y, z))


def royal(c: City):
    """The royal terrace and King Gazel's hall at the back of the cavern."""
    TZ = 29          # front edge of the terrace
    T = G + 4        # terrace floor layer
    for x in range(CX - 44, CX + 45):
        for z in range(CAV_N, TZ + 1):
            if not c.air(x, G + 1, z):
                continue
            for y in range(G + 1, T):
                c.put(x, y, z, M("stone_bricks") if z == TZ else M("stone"))
            c.put(x, T, z, M("polished_andesite") if (x + z) % 3 else M("stone_bricks"))
            if z == TZ and abs(x - CX) > 7:
                c.put(x, T + 1, z, M("stone_brick_wall"))
    for k in range(4):  # the great stair
        z = TZ + 4 - k
        for x in range(CX - 7, CX + 8):
            for y in range(G + 1, G + 1 + k):
                c.put(x, y, z, M("stone_bricks"))
            c.put(x, G + 1 + k, z, M("stone_brick_stairs[facing=north]"))
    for x in (CX - 8, CX + 8):
        for z in range(TZ + 1, TZ + 5):
            for y in range(G + 1, T + 1):
                c.put(x, y, z, M("stone_bricks"))
            c.put(x, T + 1, z, M("stone_brick_wall"))
        c.put(x, T + 2, TZ + 4, M("lantern[hanging=false]"))
    throne_room(c, T)


# --- King Gazel's throne room: Tensura's own boss arena, carved into the back of the cavern --------------
THRONE_NBT = Path(__file__).resolve().parent / "assets" / "gazel_throne.nbt"
AX_CUT = 42          # arena x where the throne dais starts; the boss pit west of it (and its warp pads) is left out
ROOM_X0, ROOM_Z0 = CX - 25, 0  # arena z 0..50 -> x 49..99; arena x 68..42 -> z 0..26 (throne north, door south)
ROOM_DY = 1          # arena y 6 (dais floor) -> y 7, the royal terrace floor
ROOM_FRONT = ROOM_Z0 + 68 - AX_CUT   # z 26, the last row of the room; the facade stands at z 27
GAZEL_SEAT = (CX + 0.5, 9.5, ROOM_Z0 + 68 - 57 + 0.5)  # the red nether brick throne (arena 57, 8, 25), facing south
_TURN = {"north": "west", "east": "north", "south": "east", "west": "south"}


def _rotate(state: str) -> str:
    """Arena +x -> -z, arena +z -> +x (a quarter turn): facings, axes, rotations and side connections."""
    if "[" not in state:
        return state
    name, props = state[:-1].split("[", 1)
    out = []
    for pair in props.split(","):
        k, v = pair.split("=")
        if k == "facing" and v in _TURN:
            v = _TURN[v]
        elif k == "axis" and v in ("x", "z"):
            v = "z" if v == "x" else "x"
        elif k == "rotation":
            v = str((int(v) + 12) % 16)
        elif k in _TURN:
            k = _TURN[k]
        out.append(f"{k}={v}")
    return name + "[" + ",".join(sorted(out)) + "]"


def shell_rock(x, y, z, exposed: bool) -> str:
    """The arena's void-facing glass becomes the mountain: deepslate/tuff/stone, sandstone strata outside."""
    if exposed:
        return outer_mat(x, y, z)
    n = noise3(x, y, z, 5, 81)
    return M("deepslate" if n < 0.3 else "tuff" if n < 0.5 else "stone" if n < 0.72
             else "cobbled_deepslate" if n < 0.85 else "andesite")


def throne_room(c: City, T: int):
    """Place the canon Gazel Dwargo throne room (the dais half of Tensura's dwarf_arena) behind the terrace."""
    import nbt
    from blueprint import from_structure
    arena = from_structure("gazel_throne", THRONE_NBT)
    banners = nbt.read_gzip(THRONE_NBT)
    sx, sy, sz = arena.size
    A = arena.blocks
    # The side stairs down into the (left out) pit become dais floor, level with the terrace.
    for ax in range(AX_CUT, sx):
        for az in range(sz):
            col = [A[(ax, y, az)] for y in range(sy)]
            if col[6] == AIR or "stairs" in col[6] or "slab" in col[6]:
                if all(col[y] == AIR for y in range(7, 13)) and col[0] != AIR:
                    for y in range(1, 7):
                        if A[(ax, y, az)] == AIR or "stairs" in A[(ax, y, az)] or "slab" in A[(ax, y, az)]:
                            A[(ax, y, az)] = M("tuff_bricks")
    H = c.H
    room = set()
    for (ax, ay, az), state in A.items():
        if ax < AX_CUT:
            continue
        x, y, z = ROOM_X0 + az, ay + ROOM_DY, ROOM_Z0 + (sx - 1 - ax)
        name = state.split("[", 1)[0]
        if name == M("black_stained_glass"):
            c.put(x, y, z, shell_rock(x, y, z, y > H.get((x, z), 0) - 2))
            c.rock.add((x, y, z))
            continue
        if name == M("redstone_block"):  # powered the ceiling bulbs; they keep their light once lit
            c.put(x, y, z, shell_rock(x, y, z, False))
            continue
        if "copper_bulb" in name:
            state = state.replace("powered=true", "powered=false")
        c.put(x, y, z, _rotate(state))
        room.add((x, y, z))
    c.banner_patterns = []
    for b in banners["blocks"]:
        ax, ay, az = b["pos"]
        pats = (b.get("nbt") or {}).get("patterns")
        if ax >= AX_CUT and pats:
            snbt = "[" + ",".join('{color:"%s",pattern:"%s"}' % (p["color"], p["pattern"]) for p in pats) + "]"
            c.banner_patterns.append([ROOM_X0 + az, ay + ROOM_DY, ROOM_Z0 + (sx - 1 - ax), snbt])
    x1, x2 = ROOM_X0, ROOM_X0 + sz - 1
    top = sy - 1 + ROOM_DY
    F = ROOM_FRONT + 1
    # Seal the cavern behind and above the room against the rock (the cavern now ends at the facade).
    for (x, y, z) in c.cave:
        if z < F and (x, y, z) not in room and y > G:
            c.put(x, y, z, cave_mat(x, y, z) if y <= H.get((x, z), 0) - 3 else outer_mat(x, y, z))
            c.rock.add((x, y, z))
    # Where the mountain is lower than the room (its north slope), heap rock over it with a falling skirt.
    for x in range(x1 - 8, x2 + 9):
        for z in range(0, F):
            if not 0 <= x < SX:
                continue
            d = max(x1 - x, x - x2, 0)
            want = top + 2 - d - (1 if rnd(x, 0, z, 82) < 0.4 else 0)
            have = H.get((x, z), -1)
            for y in range(max(have + 1, 0), want + 1):
                if c.get(x, y, z) in (None, AIR) and (x, y, z) not in room:
                    c.put(x, y, z, outer_mat(x, y, z))
                    c.rock.add((x, y, z))
            if want > have:
                H[(x, z)] = want
    # The facade: tuff and deepslate like the room, a great door on the throne axis, banners either side.
    for x in range(x1, x2 + 1):
        for y in range(T + 1, top + 1):
            if c.get(x, y, F) in (None, AIR):
                band = y - T
                state = (M("polished_deepslate") if x in (CX - 9, CX + 9, CX - 17, CX + 17)
                         else M("deepslate_tiles") if band % 6 == 0 else M("tuff_bricks"))
                c.put(x, y, F, state)
    for y in range(T + 1, T + 12):
        half = 3 if y <= T + 9 else 2 if y == T + 10 else 1
        for x in range(CX - half, CX + half + 1):
            c.put(x, y, F, AIR)
    for x in range(CX - 4, CX + 5):
        c.put(x, T + 12, F, M("chiseled_tuff_bricks") if abs(x - CX) < 4 else M("deepslate_tiles"))
    c.put(CX, T + 13, F, M("gold_block"))
    for x in (CX - 4, CX + 4):
        c.put(x, T + 1, F + 1, M("lantern[hanging=false]"))
    banner(c, lambda i, r: (CX - 14 + i, T + 14 - r, F + 1), 3, 11, "x")
    banner(c, lambda i, r: (CX + 12 + i, T + 14 - r, F + 1), 3, 11, "x")


def tunnel(c: City):
    for z in range(CAV_S - 4, GATE_Z, 3):
        hang(c, CX, z, G + 9)
    for z in range(CAV_S - 5, GATE_Z):
        for x in range(CX - 3, CX + 4):
            c.put(x, G, z, M("polished_andesite") if abs(x - CX) < 3 else M("stone_bricks"))


def road_mid(z: int) -> int:
    return CX if z < GATE_Z + 12 else CX + round((noise2(0, z, 10, 72) - 0.5) * 4)


def kaijin_smithy(c: City):
    """Kaijin's smithy: the first house of the forge street (west), its ground floor a working forge."""
    X = lambda u: CX - 8 - u
    c.put(X(2), G + 1, 35, M("anvil[facing=north]"))
    c.put(X(2), G + 1, 37, M("lava_cauldron"))
    c.put(X(5), G + 1, 37, M("blast_furnace[facing=east,lit=true]"))
    c.put(X(4), G + 1, 35, M("smithing_table"))
    c.put(X(-1), G + 3, 35, M("dark_oak_wall_hanging_sign[facing=north]"))
    c.put(X(-1), G + 1, 37, M("barrel[facing=up]"))
    c.put(X(-1), G + 1, 35, M("grindstone[face=floor,facing=east]"))
    c.put(X(3), G + 1, 37, M("magma_block"))
    c.put(X(4), G + 1, 37, M("coal_block"))
    c.put(X(4), G + 2, 37, M("raw_iron_block"))


def bridges(c: City):
    """Plank bridges across the canyon street, hung on chains, linking facing wall homes at G + 20."""
    n = 0
    for (west, z0, y0), near in sorted(c.homes.items()):
        if not west or y0 != G + 20 or (z0 - 31) // 7 % 2 or (False, z0, y0) not in c.homes:
            continue
        xw, xe = CX - near + 2, CX + c.homes[(False, z0, y0)] - 2
        zm = z0 + 2
        for x in range(xw + 1, xe):
            for z in (zm - 1, zm, zm + 1):
                if c.air(x, y0, z):
                    c.put(x, y0, z, M("spruce_slab[type=top]"))
            for z in (zm - 1, zm + 1):
                if c.air(x, y0 + 1, z):
                    c.put(x, y0 + 1, z, M("spruce_fence"))
            if (x - xw) % 7 == 3:
                for z in (zm - 1, zm + 1):
                    hang(c, x, z, y0 + 2, lantern=False)
        for x in (xw, xe):
            c.put(x, y0 + 1, zm, AIR)
        n += 1
    c.bridges = n


def outpost(c: City):
    """The outer road: travellers queue in fenced lanes for the gate inspection, guard booths, a road
    tower with a banner and a checkpoint arch where the road leaves the mountain."""
    for z in range(GATE_Z + 10, GATE_Z + 22):  # queue lanes: in (west) and out (east)
        c.put(CX, G + 1, z, M("spruce_fence"))
        if z % 4 == 0:
            c.put(CX, G + 2, z, M("lantern[hanging=false]"))
    for sgn in (-1, 1):  # inspection booths beside the apron
        bx = CX + sgn * 8
        for x in (bx, bx + sgn, bx + 2 * sgn):
            for z in range(GATE_Z + 11, GATE_Z + 14):
                for y in range(G + 1, G + 4):
                    edge = x == bx + 2 * sgn or z in (GATE_Z + 11, GATE_Z + 13)
                    c.put(x, y, z, M("stone_bricks") if edge else AIR)
                c.put(x, G + 4, z, M("stone_brick_slab[type=bottom]"))
        c.put(bx + sgn, G + 1, GATE_Z + 12, M("lectern[facing=" + ("east" if sgn < 0 else "west") + "]"))
        c.put(bx + sgn, G + 3, GATE_Z + 12, M("lantern[hanging=true]"))
    # Road tower, west of the road.
    gz = GATE_Z + 44
    mid = road_mid(gz + 2)
    x1, x2 = mid - 11, mid - 7
    for x in range(x1, x2 + 1):
        for z in range(gz, gz + 5):
            c.put(x, G, z, M("stone_bricks"))
            for y in range(G + 1, G + 13):
                edge = x in (x1, x2) or z in (gz, gz + 4)
                corner = x in (x1, x2) and z in (gz, gz + 4)
                state = M("polished_andesite") if corner else M("stone_bricks") if edge else AIR
                c.put(x, y, z, M("stone_bricks") if y == G + 12 else state)
            if (x in (x1, x2) or z in (gz, gz + 4)) and (x + z) % 2 == 0:
                c.put(x, G + 13, z, M("stone_brick_wall"))
    for y in (G + 1, G + 2):
        c.put(x2, y, gz + 2, AIR)
    for y in range(G + 1, G + 13):
        c.put(x1 + 1, y, gz + 2, M("ladder[facing=east]"))
    c.put(x1 + 2, G + 3, gz + 1, M("lantern[hanging=true]"))
    for x, z in ((x1, gz), (x2, gz + 4), (x1, gz + 4), (x2, gz)):
        c.put(x, G + 14, z, M("lantern[hanging=false]"))
    for y in range(G + 6, G + 10, 3):
        c.put(x2, y, gz + 2, M("black_stained_glass_pane"))
    banner(c, lambda i, r: (x2 + 1, G + 11 - r, gz + 1 + i), 3, 7, "z")
    # Checkpoint arch over the road.
    cz = GATE_Z + 56
    mid = road_mid(cz)
    for x in (mid - 5, mid + 5):
        for y in range(G + 1, G + 9):
            c.put(x, y, cz, M("stone_bricks") if y < G + 8 else M("chiseled_stone_bricks"))
        c.put(x, G + 11, cz, M("lantern[hanging=false]"))
    for x in range(mid - 5, mid + 6):
        c.put(x, G + 9, cz, M("polished_andesite"))
        if x % 2 == 0:
            c.put(x, G + 10, cz, M("stone_brick_wall"))
    banner(c, lambda i, r: (mid - 2 + i, G + 8 - r, cz), 5, 5, "x")


def light_city(c: City):
    """Place glowing stones (in rock) or lanterns until no spawnable spot in the city is dark."""
    bp = c.bp
    for _ in range(12):
        candidates = [p for p, s in bp.blocks.items() if s == AIR and p not in c.outside]
        spots = dark_spots(bp.blocks, bp.size, candidates)
        if not spots:
            return 0
        placed = []
        for (x, y, z) in spots:
            if any(abs(x - a) + abs(y - b) + abs(z - d) <= 8 for a, b, d in placed):
                continue
            below = (x, y - 1, z)
            if below in c.rock:
                bp.set(*below, M("glowstone") if rnd(x, y, z, 90) < 0.6 else M("shroomlight"))
                c.rock.discard(below)
            else:
                bp.set(x, y, z, M("lantern[hanging=false]"))
            placed.append((x, y, z))
    raise RuntimeError("dwargon: could not light every spawnable spot")


def build(bp):
    c = City(bp)
    H, cave = terrain(c)
    c.H, c.cave = H, cave
    approach(c, H)
    gate(c)
    tunnel(c)
    royal(c)
    streets(c)
    kaijin_smithy(c)
    plaza(c)
    forge_hall(c)
    workshop(c)
    dwellings(c)
    bridges(c)
    outpost(c)
    light_city(c)
    bp.stats = dict(homes=len(c.homes), ladders=c.ladders, bridges=c.bridges)
    bp.banner_patterns = c.banner_patterns
    if c.breaches:
        print(f"dwargon: warning, {c.breaches} cavern blocks break the mountain surface")


ARRIVAL = (CX, G + 1, GATE_Z + 16)
PARTS = [0, 56, 112]  # z offsets of the slabs dwargon_0..2 (each a separate structure file)


def outputs(bp) -> dict:
    from _dwargon_footprint import footprint
    probes = [(road_mid(z) + dx, z) for z in range(GATE_Z + 6, SZ - 1, 4) for dx in (-8, 0, 8)]
    text = footprint(bp, probes, ARRIVAL, PARTS)
    # Block entity data the structure file can't carry: the canon Dwargon banner patterns of the throne room,
    # and King Gazel's seat (blueprint coordinates; dwargon.js applies both after placing).
    royal = {"banners": getattr(bp, "banner_patterns", []), "gazel": list(GAZEL_SEAT)}
    text += "const TtlDwargonRoyal = " + json.dumps(royal, separators=(",", ":")) + "\n"
    return {"pack/kubejs/server_scripts/ttl/generated/dwargon_footprint.js": text}
