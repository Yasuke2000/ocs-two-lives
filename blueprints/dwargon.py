"""The Armed Nation of Dwargon: the dwarf kingdom inside a pale sandstone mountain.

SIZE (112, 76, 124); the gate faces south (+z). The mountain is part of the build (a rough, stepped
sandstone and terracotta massif with grass on its lower terraces and two spurs flanking the gate), so it
sits on any hill; outside the mountain and the approach the corners are left empty and terrain stays.
A dirt road runs north from the south edge (z 123) into a ravine to the white gate wall (back z 88,
front face z 91, towers out to z 95 and up to y 29, yellow banners with the red emblem). Gate opening:
x 53-59, y 4-11 (arch to y 13). Arrival point: blueprint (56, 4, 104) on the road, facing north.
A tunnel (z 78-90) leads into the cavern city: floor blocks at y 3 (you walk at y 4), cavern z 14-84,
vault up to y 43 with a canyon-like skylight crack over the main street. South street (z 68-82) of
stone and timber houses (2-4 storeys, lit windows, shop signs), lamps strung across the street, homes
with balconies carved into the cavern walls, a round plaza (centre 56, 54) with a cogwheel fountain and
market stalls, a forge hall (west) and a Create workshop (east), the forge street (z 34-43), then a
great stair to the royal terrace (floor y 7) and King Gazel's hall (z 16-27) with the throne. Chimneys
smoke (campfires on hay). Every spawnable spot inside has block light (checked when this builds).
"""
import math

from _dwargon_lib import AIR, dark_spots, fbm2, noise2, noise3, rnd

SIZE = (112, 76, 124)
SX, SY, SZ = SIZE
G = 3           # ground / city floor layer
CX = 56         # street centre line (x)
PLAZA_Z = 54    # plaza centre (z)
CAV_N, CAV_S = 14, 84
GATE_Z = 88     # back of the gate wall (front face at GATE_Z + 3)


def M(name: str) -> str:
    return "minecraft:" + name


# --- the mountain -----------------------------------------------------------------------------------
def heights() -> dict:
    """Top layer of the mountain per column: a rounded massif, steeper to north and south, terraced."""
    cx, cz, hx, hz, r = 55.5, 52.0, 50.0, 48.0, 34.0
    H = {}
    for x in range(SX):
        for z in range(SZ):
            qx, qz = abs(x - cx) - (hx - r), abs(z - cz) - (hz - r)
            out = math.hypot(max(qx, 0), max(qz, 0)) + min(max(qx, qz), 0) - r
            t = -out + (fbm2(x, z, 18, 1) - 0.5) * 16
            t = min(t, x + 0.5, SX - 0.5 - x, z + 0.5, 101 - z)  # stay inside the box, clear of the road
            if t <= 0:
                continue
            slope = 1.5 + 1.3 * fbm2(x, z, 20, 2) + 2.2 * min(1.0, abs(z - cz) / 46) ** 2
            ridge = math.exp(-((x - CX) / 32) ** 2)  # highest along the city's axis
            cap = 30 + 30 * ridge + 26 * (fbm2(x, z, 24, 3) - 0.4)
            raw = min(cap, t * slope)
            top = G + 3 * math.floor(raw / 3 + 0.45 * noise2(x, z, 6, 4))
            if top > G:
                H[(x, z)] = min(top, SY - 2)
    # Two rocky spurs reaching south on either side of the gate, so it sits deep in a ravine.
    for xs in (CX - 33, CX + 33):
        for x in range(xs - 16, xs + 17):
            for z in range(78, 114):
                if not 0 <= x < SX:
                    continue
                bump = 40 * math.exp(-((x - xs) / 8) ** 2 - ((z - 90) / 10) ** 2) * (0.75 + 0.5 * noise2(x, z, 5, 5))
                top = G + 3 * math.floor(bump / 3 + 0.45 * noise2(x, z, 6, 4))
                if top > H.get((x, z), G):
                    H[(x, z)] = top
    return H


def cav_top(z: float) -> float:
    return 40.0 if z >= 40 else 40 - (40 - z) * 0.55


def cav_base(z: float) -> float:
    e = min(z - CAV_N, CAV_S - z)
    if e < 0:
        return -1
    base = 17.0
    dz = z - PLAZA_Z
    if abs(dz) < 18:
        base = max(base, math.sqrt(324 - dz * dz) * 1.35)
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
        for h in range(1, 44):
            hw, he = cav_half(z, h, 0), cav_half(z, h, 1)
            if hw < 0 and he < 0:
                continue
            for x in range(CX - 30, CX + 31):
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
        if 26 <= z <= 80:
            mid = CX + (noise2(0, z, 12, 50) - 0.5) * 4
            crack = abs(x - mid) <= 7 + 6 * noise2(1, z, 7, 51)
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
    hw = 21 + max(0, z - GATE_Z) * 0.5 + (y - G) * 0.22 + (noise2(y, z, 5, 60) - 0.5) * 3
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


def floor_mat(x, z) -> str:
    dx = x - CX
    v = rnd(x, G, z, 30)
    if abs(dx) <= 7:
        if abs(dx) == 7:
            return M("polished_deepslate")
        return M("stone_bricks") if v < 0.45 else M("polished_andesite") if v < 0.8 else M("cobblestone") if v < 0.93 else M("mossy_stone_bricks")
    return M("cobblestone") if v < 0.4 else M("stone") if v < 0.7 else M("packed_mud") if v < 0.85 else M("andesite")


# --- the approach and the gate -------------------------------------------------------------------
def approach(c: City, H: dict):
    bp = c.bp
    for x in range(CX - 34, CX + 35):
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
            top = max(G + 8, H.get((x, z), 0))
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
        mid = CX if z < 100 else CX + round((noise2(0, z, 10, 72) - 0.5) * 4)
        for x in range(mid - 3, mid + 4):
            edge = abs(x - mid) == 3
            if edge and rnd(x, G, z, 73) < 0.5:
                continue
            bp.set(x, G, z, M("coarse_dirt") if edge else M("dirt_path"))
            bp.set(x, G + 1, z, AIR)
        if z % 9 == 4 and z > 98:  # lamp posts along the road, alternating sides
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
    for i, (bx, bz) in enumerate(((CX - 14, 106), (CX + 15, 111), (CX - 22, 117), (CX + 9, 120), (CX - 9, 99))):
        if (bx, bz) in H:
            continue
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(bx + dx, G + 1, bz + dz, M("sandstone") if (dx + dz + i) % 3 else M("stone"))
        bp.set(bx, G + 2, bz, M("smooth_sandstone"))
    for i, (bx, bz) in enumerate(((CX - 18, 101), (CX + 20, 104), (CX + 13, 117), (CX - 27, 110), (CX + 26, 119))):
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
STYLES = [
    dict(base="stone_bricks", infill="packed_mud", post="stripped_dark_oak_log", beam="dark_oak_log",
         roof="deepslate_tile", door="dark_oak_door", pane="orange_stained_glass_pane"),
    dict(base="cobblestone", infill="smooth_sandstone", post="stripped_spruce_log", beam="spruce_log",
         roof="dark_oak", door="spruce_door", pane="yellow_stained_glass_pane"),
    dict(base="deepslate_bricks", infill="bricks", post="stripped_dark_oak_log", beam="dark_oak_log",
         roof="spruce", door="dark_oak_door", pane="orange_stained_glass_pane"),
    dict(base="tuff_bricks", infill="white_terracotta", post="dark_oak_log", beam="stripped_dark_oak_log",
         roof="mud_brick", door="spruce_door", pane="yellow_stained_glass_pane"),
]


def house(c: City, west: bool, z0: int, w: int, storeys: int, style: int, chimney=False, sign=False, d=8):
    """A narrow dwarven house on the street: stone ground floor, jettied timber storeys, gable to the street."""
    s = STYLES[style % len(STYLES)]
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
            c.put(X(u), G, z, M("spruce_planks"))
            for y in range(G + 1, G + 4):
                edge = u in (0, d - 1) or z in (z0, z1)
                c.put(X(u), y, z, M(s["base"]) if edge else AIR)
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
                        c.put(X(u), y, z, M(s["infill"]))
            if k < storeys:
                for z in range(z0 + 1, z1, 2):
                    for y in (yf + 1, yf + 2):
                        c.put(X(-1), y, z, M(s["pane"]))
    # Gable roof, ridge running back into the rock.
    roof = M(s["roof"])
    k = 0
    while True:
        za, zb = z0 - 1 + k, z1 + 1 - k
        y = top + k
        if za > zb:
            break
        for u in range(-2, d):
            if za == zb:
                c.put(X(u), y, za, roof + "_slab[type=bottom]")
            else:
                c.put(X(u), y, za, roof + "_stairs[facing=south]")
                c.put(X(u), y, zb, roof + "_stairs[facing=north]")
                if k >= 1:
                    for z in range(za + 1, zb):
                        for uu in range(-1, d - 1):
                            c.put(X(uu), y, z, AIR)
                        c.put(X(-1), y, z, M(s["infill"]))
                        c.put(X(d - 1), y, z, M(s["infill"]))
        k += 1
    if w >= 5:
        c.put(X(-1), top + 1, zmid, M(s["pane"]))
    # Ground floor front: door, windows, sign.
    c.put(X(0), G + 1, zmid, M(f"{s['door']}[facing={inn},half=lower,hinge=left,open=false]"))
    c.put(X(0), G + 2, zmid, M(f"{s['door']}[facing={inn},half=upper,hinge=left,open=false]"))
    for z in (z0 + 1, z1 - 1):
        if z != zmid:
            c.put(X(0), G + 2, z, M(s["pane"]))
    if sign:
        c.put(X(-1), G + 3, z1, M("dark_oak_wall_hanging_sign[facing=north]"))
    # Inside: a lantern per storey, a ladder, and maybe a smoking chimney.
    for k in range(storeys):
        c.put(X(d // 2), G + 4 * k + 1, zmid, M("lantern[hanging=false]"))
    for y in range(G + 1, G + 4 * (storeys - 1) + 1):
        c.put(X(d - 2), y, z1 - 1, M(f"ladder[facing={out}]"))
    if chimney:
        cz = z0 + 1
        ytop = top + w // 2 + 3
        for y in range(G + 1, ytop - 1):
            c.put(X(d - 2), y, cz, M("bricks"))
        c.put(X(d - 2), ytop - 1, cz, M("hay_block[axis=y]"))
        c.put(X(d - 2), ytop, cz, M("campfire[facing=north,lit=true,signal_fire=true]"))
    # Close any gap between the house and the cavern wall.
    for u in range(d, d + 12):
        for z in range(z0 - 1, z1 + 2):
            for y in range(G + 1, top + w // 2 + 2):
                if c.air(X(u), y, z):
                    c.put(X(u), y, z, cave_mat(X(u), y, z))
                    c.rock.add((X(u), y, z))


def dwellings(c: City):
    """Homes carved into the cavern walls above the street: a facade, a lit room, a balcony on a bracket."""
    spots = [(z0, y0) for z0 in range(31, 80, 7) for y0 in (G + 20, G + 27)]
    spots += [(z0, G + 14) for z0 in (40, 64)]
    for west in (True, False):
        sgn = -1 if west else 1
        for i, (z0, y0) in enumerate(spots):
            z1 = z0 + 4
            # The facade plane: the nearest rock of the wall over the whole front.
            near = None
            for z in range(z0, z1 + 1):
                for y in range(y0, y0 + 5):
                    d = 0
                    while d < 30 and c.air(CX + sgn * d, y, z):
                        d += 1
                    if d >= 30 or (CX + sgn * d, y, z) not in c.rock:
                        near = -1
                        break
                    near = d if near is None else min(near, d)
                if near == -1:
                    break
            if near is None or near < 9:
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
        (True, [(68, 5, 3, 0, True, True), (73, 5, 4, 1, False, True), (78, 5, 2, 2, True, False)]),
        (False, [(68, 4, 3, 3, False, True), (72, 6, 4, 0, True, False), (78, 5, 3, 1, False, True)]),
        (True, [(34, 5, 3, 2, True, True), (39, 5, 2, 3, True, False)]),
        (False, [(34, 5, 2, 1, True, True), (39, 5, 3, 2, False, True)]),
    ]
    for west, houses in rows:
        for z0, w, storeys, style, chim, sign in houses:
            house(c, west, z0, w, storeys, style, chimney=chim, sign=sign)
    for z in range(36, 84, 6):
        lamp_post(c, CX - 5 if z % 12 else CX + 5, z)
    for z in (37, 42, 70, 76, 81):
        string_lights(c, z, G + 21 if z > 60 else G + 19)


def plaza(c: City):
    for x in range(CX - 13, CX + 14):
        for z in range(PLAZA_Z - 13, PLAZA_Z + 14):
            d = math.hypot(x - CX, z - PLAZA_Z)
            if d > 13.3 or not c.air(x, G + 1, z):
                continue
            ring = int(d) % 4
            state = M("chiseled_stone_bricks") if ring == 0 and d > 4 else M("stone_bricks") if ring == 2 else M("polished_andesite")
            c.put(x, G, z, state)
    # Fountain: a basin with a column crowned by a great cogwheel.
    for x in range(CX - 4, CX + 5):
        for z in range(PLAZA_Z - 4, PLAZA_Z + 5):
            d = math.hypot(x - CX, z - PLAZA_Z)
            if d <= 2.6:
                c.put(x, G, z, M("stone_bricks"))
                c.put(x, G + 1, z, M("water"))
            elif d <= 3.9:
                c.put(x, G + 1, z, M("polished_andesite"))
    for y in range(G + 1, G + 6):
        c.put(CX, y, PLAZA_Z, M("chiseled_stone_bricks"))
    c.put(CX, G + 6, PLAZA_Z, M("gold_block"))
    c.put(CX, G + 7, PLAZA_Z, "create:large_cogwheel[axis=y]")
    c.put(CX, G + 8, PLAZA_Z, "create:shaft[axis=y]")
    for x, z in c.bp.around(CX, PLAZA_Z, 6, 4, start_deg=45):
        lamp_post(c, x, z)
    for x, z in c.bp.around(CX, PLAZA_Z, 12, 8, start_deg=22.5):
        lamp_post(c, x, z, 4)
    # Market stalls.
    awnings = [("red_wool", "white_wool"), ("yellow_wool", "red_wool"), ("blue_wool", "white_wool"), ("green_wool", "yellow_wool")]
    for i, (sx, sz) in enumerate(c.bp.around(CX, PLAZA_Z, 9, 4, start_deg=0)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) == 1 and abs(dz) == 1:
                    c.put(sx + dx, G + 1, sz + dz, M("spruce_fence"))
                    c.put(sx + dx, G + 2, sz + dz, M("spruce_fence"))
                c.put(sx + dx, G + 3, sz + dz, M(awnings[i][(dx + dz) % 2]))
        c.put(sx, G + 1, sz, M("barrel[facing=up]"))
        c.put(sx + (1 if i % 2 else 0), G + 1, sz + (0 if i % 2 else 1), M("composter") if i % 2 else M("barrel[facing=up]"))
    # Lamps hanging from the vault around the skylight.
    for x, z in c.bp.around(CX, PLAZA_Z, 15, 8, start_deg=0):
        hang(c, x, z, G + 16)


def forge_hall(c: City):
    """West of the plaza: an open-fronted forge with three smoking chimneys and cogs on its face."""
    x1, x2, z1, z2 = CX - 23, CX - 11, PLAZA_Z - 8, PLAZA_Z + 8
    wall, trim = M("polished_blackstone_bricks"), M("stone_bricks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            c.put(x, G, z, M("polished_blackstone"))
            for y in range(G + 1, G + 11):
                edge = x in (x1, x2) or z in (z1, z2)
                if y == G + 10:
                    c.put(x, y, z, trim)
                elif edge:
                    c.put(x, y, z, M("copper_block") if y == G + 5 else wall)
                else:
                    c.put(x, y, z, AIR)
            if (x in (x1, x2) or z in (z1, z2)) and (x + z) % 2 == 0:
                c.put(x, G + 11, z, trim)
    for z in range(z1 + 1, z2):  # arcade
        if (z - z1) % 4 != 0:
            for y in range(G + 1, G + 5):
                c.put(x2, y, z, AIR)
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
    x1, x2, z1, z2 = CX + 11, CX + 23, PLAZA_Z - 8, PLAZA_Z + 8
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
    for x in range(CX - 30, CX + 31):
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
    # The hall.
    x1, x2, z1, z2 = CX - 13, CX + 13, 16, 27
    wall, pil, gild = M("polished_blackstone_bricks"), M("polished_blackstone"), M("gold_block")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(T + 1, T + 16):
                edge = x in (x1, x2) or z in (z1, z2)
                c.put(x, y, z, (gild if y == T + 13 and z == z2 else wall) if edge else AIR)
            c.put(x, T + 16, z, wall)
            if (x in (x1, x2) or z in (z1, z2)) and (x + z) % 2 == 0:
                c.put(x, T + 17, z, pil)
            c.put(x, T, z, M("polished_deepslate"))
    for x in (x1, x1 + 4, x1 + 8, x2 - 8, x2 - 4, x2):  # pilasters
        for y in range(T + 1, T + 17):
            c.put(x, y, z2 + 1, pil if y != T + 13 else gild)
        c.put(x, T + 17, z2 + 1, M("lantern[hanging=false]"))
    for x in (x1 + 2, x1 + 6, x2 - 6, x2 - 2):  # tall windows
        for y in range(T + 4, T + 11):
            c.put(x, y, z2, M("yellow_stained_glass_pane"))
    for y in range(T + 1, T + 11):  # door arch
        half = 3 if y <= T + 8 else 2 if y == T + 9 else 1
        for x in range(CX - half, CX + half + 1):
            c.put(x, y, z2, AIR)
            c.put(x, y, z2 + 1, AIR)
    c.put(CX, T + 11, z2 + 1, gild)
    for x in (CX - 3, CX - 2, CX + 2, CX + 3):
        c.put(x, T + 10 if abs(x - CX) == 3 else T + 11, z2 + 1, M("gilded_blackstone"))
    banner(c, lambda i, r: (x1 + 5 + i, T + 14 - r, z2 + 1), 3, 12, "x")
    banner(c, lambda i, r: (x2 - 7 + i, T + 14 - r, z2 + 1), 3, 12, "x")
    # Flanking towers.
    for tx1 in (x1 - 5, x2):
        for x in range(tx1, tx1 + 6):
            for z in range(z1 + 1, z2 + 2):
                for y in range(T + 1, T + 22):
                    edge = x in (tx1, tx1 + 5) or z in (z1 + 1, z2 + 1)
                    c.put(x, y, z, (gild if y == T + 13 else wall) if edge else AIR)
                c.put(x, T + 22, z, wall)
                if (x in (tx1, tx1 + 5) or z in (z1 + 1, z2 + 1)) and (x + z) % 2 == 0:
                    c.put(x, T + 23, z, pil)
        c.put(tx1 + 2, T + 1, z2 + 1, AIR)
        c.put(tx1 + 2, T + 2, z2 + 1, AIR)
        c.put(tx1 + 2, T + 1, z2, M("lantern[hanging=false]"))
        for y in range(T + 6, T + 20, 5):
            c.put(tx1 + 2, y, z2 + 1, M("yellow_stained_glass_pane"))
        c.put(tx1 + 2, T + 24, z2 + 1, M("lantern[hanging=false]"))
    # Throne room.
    for x in range(x1 + 1, x2):
        for z in (z1 + 1, z1 + 2):
            c.put(x, T + 1, z, pil if abs(x - CX) <= 5 else AIR)
    for z in range(z1 + 3, z2):
        for x in (CX - 1, CX, CX + 1):
            c.put(x, T + 1, z, M("red_carpet"))
    c.put(CX, T + 2, z1 + 1, M("polished_blackstone_stairs[facing=north]"))
    c.put(CX - 1, T + 2, z1 + 1, gild)
    c.put(CX + 1, T + 2, z1 + 1, gild)
    banner(c, lambda i, r: (CX - 2 + i, T + 12 - r, z1 + 1), 5, 9, "x")
    for x in (CX - 8, CX + 8):
        for z in (z1 + 3, z1 + 6, z1 + 9):
            for y in range(T + 1, T + 16):
                c.put(x, y, z, M("polished_blackstone_bricks") if y % 4 else gild)
    for x, z in ((CX - 4, 20), (CX + 4, 20), (CX - 4, 24), (CX + 4, 24), (CX, 22), (CX - 11, 22), (CX + 11, 22)):
        for y in range(T + 12, T + 16):
            c.put(x, y, z, M("chain[axis=y]"))
        c.put(x, T + 11, z, M("lantern[hanging=true]"))
    for x in (CX - 5, CX + 5):
        c.put(x, T + 2, z1 + 1, M("lantern[hanging=false]"))
    # Seal behind and beside the hall against the rock.
    for x in range(x1 - 10, x2 + 11):
        for z in range(CAV_N - 1, z1 + 1):
            for y in range(T + 1, T + 26):
                if c.air(x, y, z):
                    c.put(x, y, z, cave_mat(x, y, z))
                    c.rock.add((x, y, z))


def tunnel(c: City):
    for z in range(CAV_S - 4, GATE_Z, 3):
        hang(c, CX, z, G + 9)
    for z in range(CAV_S - 5, GATE_Z):
        for x in range(CX - 3, CX + 4):
            c.put(x, G, z, M("polished_andesite") if abs(x - CX) < 3 else M("stone_bricks"))


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
    H, _ = terrain(c)
    approach(c, H)
    gate(c)
    tunnel(c)
    royal(c)
    streets(c)
    plaza(c)
    forge_hall(c)
    workshop(c)
    dwellings(c)
    light_city(c)
    if c.breaches:
        print(f"dwargon: warning, {c.breaches} cavern blocks break the mountain surface")
