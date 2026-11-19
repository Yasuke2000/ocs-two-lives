"""Tempest (early): the hobgoblin village in a clearing of the Forest of Jura, just after the ogres joined.

SIZE (91, 40, 91), centre column (45, 45). Ground layer y 4 (grass, dirt paths; dirt below), you walk at
y 5; everything above is air so placement clears the forest and hills in the box. Arrival point: blueprint
(45, 5, 57) on the south edge of the village green, with a signpost east of it; placed at world 0, 0 (the
Life 2 world spawn) by life/tempest.js, which grounds it with generated/tempest_footprint.js. Village (a
rough rounded-square clearing, radius about 38, ringed by our own persistent-leaf forest edge): the
meeting longhouse (north of the green) where Rimuru holds council, Rimuru's small house behind it, the
cooking fire and well on the green, Kaijin's open forge and workshop (west road), Shuna's weaving hut
(east road), a raised food store, the goblins' old quarter (north-east: Tensura's own goblin village
pieces, blueprints/assets/goblin_village/, round their campfire behind a skull arch), finished hobgoblin houses,
a building site (south-west: half-roofed house, timber frame, foundation, scaffolding, log piles,
sawhorse), a fenced field and herb patch (south-east), a lookout tower (north-west) and a palisade begun
on the west side with a south gate. Roofs and trim borrow the goblin village palette (Tensura thatch, oak
logs and fences). Every spawnable spot in the clearing has block light (checked when this builds). Visual references and sources: design/lore/tempest.md.
"""
import json
import math
from pathlib import Path

import blueprint as _blueprint
import nbt
from _beds import CULTURE, pick, place_bed
from _dwargon_lib import AIR, dark_spots, noise2, rnd
from _footprint import settlement_footprint

# Tensura's own goblin village pieces (copied from the Tensura 2.0.1.5 jar,
# data/tensura/structure/goblin_village/<wood>/); style notes in design/lore/tempest.md.
GOBLIN_PIECES = Path(__file__).resolve().parent / "assets" / "goblin_village"
GOBLIN_SPAWN = "tensura:goblin_village/goblin_spawn"

# Previews: Tensura thatch is straw-coloured (the renderer has no keyword for it; hash colours come out pink).
if not any(k == "thatch" for k, _ in _blueprint._COLORS):
    _blueprint._COLORS.append(("thatch", (196, 164, 84)))

SIZE = (91, 40, 91)
SX, SY, SZ = SIZE
C = 45            # centre column (x and z)
G = 4             # ground layer
F = G + 1         # walking layer
R = 37.5          # clearing radius (rounded square, see dist())
ARRIVAL = (45, F, 57)
SIGNPOST = (47, 57)
PARTS = [0, 23, 46, 69]


def M(name: str) -> str:
    return "minecraft:" + name


LEAVES = {k: M(f"{k}_leaves[persistent=true]") for k in ("oak", "birch", "dark_oak", "spruce")}
THATCH = "tensura:thatch_block"
THATCH_STAIRS = "tensura:thatch_stairs"
THATCH_SLAB = "tensura:thatch_slab[type=bottom,waterlogged=false]"
SUPPORT_BELOW = ("short_grass", "fern", "poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet",
                 "lily_of_the_valley", "wheat", "carrots", "potatoes", "beetroots", "carpet", "_door", "_bed",
                 "scaffolding", "brown_mushroom", "red_mushroom")


def dist(x, z) -> float:
    """Rounded-square distance from the centre (a p=3 superellipse), so the corners hold buildings too."""
    return (abs(x - C) ** 3 + abs(z - C) ** 3) ** (1 / 3)


def edge(x, z) -> float:
    return R + 5 * (noise2(x, z, 9, 3) - 0.5)


def inside(x, z) -> bool:
    return dist(x, z) <= edge(x, z)


_TURN = {"north": "east", "east": "south", "south": "west", "west": "north"}


def _rotate_state(state: str, turns: int) -> str:
    """A block state turned `turns` quarter turns clockwise (seen from above)."""
    if turns % 4 == 0:
        return state
    name, props = _blueprint.parse_state(state)
    out = dict(props)
    for _ in range(turns % 4):
        nxt = dict(out)
        if nxt.get("facing") in _TURN:
            nxt["facing"] = _TURN[out["facing"]]
        if nxt.get("axis") in ("x", "z") and "axis" in out:
            nxt["axis"] = "z" if out["axis"] == "x" else "x"
        if "rotation" in out:
            nxt["rotation"] = str((int(out["rotation"]) + 4) % 16)
        for side in _TURN:
            if side in out:
                nxt[_TURN[side]] = out[side]
        out = nxt
    return name + ("[" + ",".join(f"{k}={v}" for k, v in out.items()) + "]" if out else "")


def goblin_piece(name: str):
    """One Tensura goblin village piece: blocks (jigsaws replaced by their final state, structure voids and
    'keep terrain' cells left out), its containers with loot tables, and the goblin spawn points."""
    root = nbt.read_gzip(GOBLIN_PIECES / f"{name}.nbt")
    if root.get("entities"):
        raise RuntimeError(f"{name}: embedded entities are not carried over")
    states = []
    for e in root["palette"]:
        props = e.get("Properties") or {}
        states.append(e["Name"] + ("[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]" if props else ""))
    blocks, loot, spawns = {}, {}, []
    for b in root["blocks"]:
        pos = tuple(b["pos"])
        state = states[b["state"]]
        data = b.get("nbt") or {}
        if state.startswith("minecraft:jigsaw"):
            if data.get("target") == GOBLIN_SPAWN:
                spawns.append(pos)
            state = data.get("final_state", "minecraft:air")
            if state == "minecraft:structure_void":
                continue
        if state.startswith("minecraft:structure_") or state.startswith("minecraft:jigsaw"):
            continue
        if "LootTable" in data:
            loot[pos] = data["LootTable"]
        blocks[pos] = state
    return tuple(root["size"]), blocks, loot, spawns


class Village:
    def __init__(self, bp):
        self.bp = bp
        self.used: set = set()  # columns taken by buildings and props (no plants, no trees)
        self.loot: list = []    # [x, y, z, loot table] for containers placed from Tensura pieces
        self.spawns: list = []  # [x, y, z, piece] where Tensura's goblin village spawns its goblins

    def paste(self, name, x0, z0, turns=0):
        """Place a Tensura goblin piece with its ground layer (y 0) on our ground layer G, corner (x0, z0),
        turned `turns` quarter turns clockwise (its entrance, on the north side in the file, then faces
        east, south, west). Returns the turned footprint (x0, z0, x1, z1)."""
        (sx, sy, sz), blocks, loot, spawns = goblin_piece(name)
        w, d = (sx, sz) if turns % 2 == 0 else (sz, sx)

        def turn_xz(x, z):
            a, b, lx, lz = x, z, sx, sz
            for _ in range(turns % 4):
                a, b = lz - 1 - b, a
                lx, lz = lz, lx
            return x0 + a, z0 + b

        cols = {(x0 + a, z0 + b) for a in range(w) for b in range(d)}
        built = {(x, z) for (x, y, z), s in self.bp.blocks.items() if y >= F and s != AIR}
        clash = [c for c in cols if c in built]
        if clash:
            raise RuntimeError(f"tempest: {name} at {x0},{z0} overlaps another build at {sorted(clash)[:4]}")
        for (x, y, z), state in blocks.items():
            wx, wz = turn_xz(x, z)
            self.put(wx, G + y, wz, _rotate_state(state, turns))
        for (x, y, z), table in loot.items():
            wx, wz = turn_xz(x, z)
            self.loot.append([wx, G + y, wz, table])
        for (x, y, z) in spawns:
            wx, wz = turn_xz(x, z)
            self.spawns.append([wx, G + y + 1, wz, name])
        self.used.update(cols)
        return x0, z0, x0 + w - 1, z0 + d - 1

    def put(self, x, y, z, state):
        self.bp.set(x, y, z, state)
        if y >= G:
            self.used.add((x, z))

    def get(self, x, y, z):
        return self.bp.blocks.get((x, y, z))

    def fill(self, x1, y1, z1, x2, y2, z2, state):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.put(x, y, z, state)

    def lamp(self, x, z, h=2, fence="oak_fence"):
        for y in range(F, F + h):
            self.put(x, y, z, M(fence))
        self.put(x, F + h, z, M("lantern[hanging=false]"))


# --- ground --------------------------------------------------------------------------------------
def ground(v: Village):
    bp = v.bp
    for x in range(SX):
        for z in range(SZ):
            for y in range(G):
                bp.blocks[(x, y, z)] = M("dirt")
            n = noise2(x, z, 6, 11)
            if inside(x, z):
                top = M("coarse_dirt") if n > 0.8 else M("grass_block")
            else:
                top = M("podzol") if n > 0.55 else M("coarse_dirt") if n < 0.15 else M("grass_block")
            bp.blocks[(x, G, z)] = top
            for y in range(F, SY):
                bp.blocks[(x, y, z)] = AIR


def path(v: Village, pts, w=1):
    """Dirt path along a polyline, `w` blocks either side, frayed with coarse dirt."""
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1))
        for i in range(n + 1):
            cx = round(x1 + (x2 - x1) * i / max(n, 1))
            cz = round(z1 + (z2 - z1) * i / max(n, 1))
            for dx in range(-w, w + 1):
                for dz in range(-w, w + 1):
                    x, z = cx + dx, cz + dz
                    if not (0 <= x < SX and 0 <= z < SZ):
                        continue
                    if v.get(x, G, z) not in (M("grass_block"), M("coarse_dirt"), M("podzol")):
                        continue
                    outer = max(abs(dx), abs(dz)) == w and w > 0
                    r = rnd(x, G, z, 41)
                    if outer and r < 0.35:
                        state = M("coarse_dirt")
                    elif outer and r < 0.5:
                        continue
                    else:
                        state = M("dirt_path")
                    v.bp.blocks[(x, G, z)] = state
                    v.used.add((x, z))


# --- houses -----------------------------------------------------------------------------------------
def gable(v: Village, x0, z0, x1, z1, y0, roof: str, axis: str, wall: str, skip_half=False):
    """Gable roof over the walls x0..x1, z0..z1 starting at layer y0, ridge along `axis` (x or z).

    roof 'thatch' = Tensura thatch stairs with a thatch-block ridge (as on the goblin village huts),
    'plank' = spruce stairs, 'dark' = dark oak stairs.
    skip_half leaves the +side slope beyond the middle unroofed (a house still being roofed)."""
    if axis == "x":
        a0, a1, b0, b1 = x0, x1, z0, z1
    else:
        a0, a1, b0, b1 = z0, z1, x0, x1
    lo_face, hi_face = ("south", "north") if axis == "x" else ("east", "west")
    stair = {"plank": "minecraft:spruce_stairs", "dark": "minecraft:dark_oak_stairs", "thatch": THATCH_STAIRS}[roof]
    mid = (a0 + a1) // 2
    k = 0
    while True:
        bl, br, y = b0 - 1 + k, b1 + 1 - k, y0 + k
        if bl > br or y >= SY:
            break
        for a in range(a0 - 1, a1 + 2):
            for b, face in ((bl, lo_face), (br, hi_face)):
                if skip_half and b == br and a > mid:
                    continue
                if bl == br:
                    state = THATCH if roof == "thatch" else stair.replace("stairs", "slab") + "[type=bottom,waterlogged=false]"
                else:
                    state = f"{stair}[facing={face},half=bottom,shape=straight,waterlogged=false]"
                x, z = (a, b) if axis == "x" else (b, a)
                if 0 <= x < SX and 0 <= z < SZ:
                    v.put(x, y, z, state)
        # Gable ends: wall material under the roof.
        if k > 0:
            for b in range(bl + 1, br):
                for a in (a0, a1):
                    x, z = (a, b) if axis == "x" else (b, a)
                    v.put(x, y, z, wall)
        k += 1
    return y0 + k - 1


def walls(v: Village, x0, z0, x1, z1, door, wall, post, height=3, windows=True):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            v.put(x, G, z, M("spruce_planks"))
            if x in (x0, x1) or z in (z0, z1):
                corner = x in (x0, x1) and z in (z0, z1)
                for y in range(F, F + height):
                    v.put(x, y, z, M(f"{post}[axis=y]") if corner else wall)
    if windows:
        for x in range(x0 + 2, x1 - 1, 3):
            for z in (z0, z1):
                v.put(x, F + 1, z, M("glass_pane"))
        for z in range(z0 + 2, z1 - 1, 3):
            for x in (x0, x1):
                v.put(x, F + 1, z, M("glass_pane"))
    dx, dz, facing = {"s": ((x0 + x1) // 2, z1, "north"), "n": ((x0 + x1) // 2, z0, "south"),
                      "e": (x1, (z0 + z1) // 2, "west"), "w": (x0, (z0 + z1) // 2, "east")}[door]
    v.put(dx, F, dz, M(f"oak_door[facing={facing},half=lower,hinge=left,open=false]"))
    v.put(dx, F + 1, dz, M(f"oak_door[facing={facing},half=upper,hinge=left,open=false]"))
    for y in range(F + 2, F + height):
        v.put(dx, y, dz, wall)
    # Lantern on a post beside the door, outside.
    ox, oz = {"s": (dx + 1, z1 + 1), "n": (dx + 1, z0 - 1), "e": (x1 + 1, dz + 1), "w": (x0 - 1, dz + 1)}[door]
    v.lamp(ox, oz, 1)
    return dx, dz


def house(v: Village, x0, z0, x1, z1, door="s", roof="thatch", wall="oak_planks", post="oak_log",
          chimney=False, stage="done", furnish=True, bed=None):
    w = M(wall)
    axis = "x" if x1 - x0 >= z1 - z0 else "z"
    walls(v, x0, z0, x1, z1, door, w, post)
    top = gable(v, x0, z0, x1, z1, F + 3, roof, axis, w, skip_half=(stage == "roofing"))
    if furnish:
        # Bed in the back corner, a barrel with a lantern, a crafting table.
        bx, bz = (x0 + 1, z0 + 1) if door != "n" else (x0 + 1, z1 - 1)
        head, foot, facing = ((bx, bz), (bx, bz + 1), "north") if door != "n" else ((bx, bz), (bx, bz - 1), "south")
        colour = bed or pick(CULTURE["tempest"], x0, z0)
        v.put(head[0], F, head[1], M(f"{colour}_bed[facing={facing},part=head,occupied=false]"))
        v.put(foot[0], F, foot[1], M(f"{colour}_bed[facing={facing},part=foot,occupied=false]"))
        v.put(x1 - 1, F, z0 + 1 if door != "n" else z1 - 1, M("barrel[facing=up,open=false]"))
        v.put(x1 - 1, F + 1, z0 + 1 if door != "n" else z1 - 1, M("lantern[hanging=false]"))
        v.put(x1 - 1, F, z1 - 1 if door != "n" else z0 + 1, M("crafting_table"))
    if chimney:
        cx, cz = x1 + 1, (z0 + z1) // 2 if axis == "x" else z0 + 1
        if axis == "z":
            cx, cz = (x0 + x1) // 2, z1 + 1
        for y in range(F, top + 2):
            v.put(cx, y, cz, M("cobblestone"))
        v.put(cx, top + 2, cz, M("campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]"))
    return top


def scaffold(v: Village, x, z, h):
    for y in range(F, F + h):
        v.put(x, y, z, M("scaffolding[bottom=false,distance=0,waterlogged=false]"))


def log_pile(v: Village, x, z, length=4, axis="x", wood="oak_log"):
    """Logs stacked three, two, one high, lying along `axis`."""
    for layer, offsets in enumerate(((0, 1, 2), (0, 1), (1,))):
        for i in offsets:
            for j in range(length):
                px, pz = (x + j, z + i) if axis == "x" else (x + i, z + j)
                v.put(px, F + layer, pz, M(f"{wood}[axis={axis}]"))


def plank_stack(v: Village, x, z, h=2, wood="spruce"):
    for y in range(F, F + h - 1):
        v.put(x, y, z, M(f"{wood}_planks"))
    v.put(x, F + h - 1, z, M(f"{wood}_slab[type=bottom,waterlogged=false]"))


def sawhorse(v: Village, x, z):
    v.put(x, F, z, M("spruce_fence"))
    v.put(x + 2, F, z, M("spruce_fence"))
    for dx in range(3):
        v.put(x + dx, F + 1, z, M("stripped_oak_log[axis=x]"))


# --- districts ----------------------------------------------------------------------------------------
def green(v: Village):
    """The village green: cooking fire with a spit and slab seats, the well, the arrival signpost."""
    cx, cz = C, 50
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            if math.hypot(x - cx, z - cz) <= 6.3:
                r = rnd(x, G, z, 5)
                v.bp.blocks[(x, G, z)] = M("dirt_path") if r < 0.55 else M("coarse_dirt") if r < 0.8 else M("packed_mud")
    v.put(cx, F, cz, M("campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]"))
    v.put(cx - 1, F, cz, M("oak_fence"))
    v.put(cx + 1, F, cz, M("oak_fence"))
    v.put(cx - 1, F + 1, cz, M("oak_fence"))
    v.put(cx + 1, F + 1, cz, M("oak_fence"))
    v.put(cx, F + 1, cz, M("chain[axis=x]"))
    # Seats as round a Tensura goblin campfire (goblin_campfire_oak: single oak slabs on the four sides).
    for d in (-1, 0, 1):
        for x, z in ((cx + d, cz - 3), (cx + d, cz + 3), (cx - 3, cz + d), (cx + 3, cz + d)):
            v.put(x, F, z, M("oak_slab[type=bottom,waterlogged=false]"))
    v.put(cx + 2, F, cz - 2, M("water_cauldron[level=3]"))
    v.put(cx - 2, F, cz - 2, M("smoker[facing=south,lit=false]"))
    v.put(cx - 2, F, cz + 2, M("barrel[facing=up,open=false]"))
    # Well (east of the fire).
    wx, wz = 53, 50
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for y in (G - 1, G, F):
                v.put(wx + dx, y, wz + dz, M("mossy_cobblestone") if rnd(wx + dx, y, wz + dz, 6) < 0.4 else M("cobblestone"))
    for y in (G - 2, G - 1, G, F):
        v.put(wx, y, wz, M("water[level=0]"))
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        v.put(wx + dx, F + 1, wz + dz, M("oak_fence"))
        v.put(wx + dx, F + 2, wz + dz, M("oak_fence"))
    v.fill(wx - 1, F + 3, wz - 1, wx + 1, F + 3, wz + 1, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.put(wx, F + 2, wz, M("lantern[hanging=true]"))
    # Signpost east of the arrival point (sign texts are written by life/tempest.js after placing).
    sx, sz = SIGNPOST
    v.put(sx, F, sz, M("stripped_spruce_log[axis=y]"))
    v.put(sx, F + 1, sz, M("stripped_spruce_log[axis=y]"))
    v.put(sx, F + 2, sz, M("lantern[hanging=false]"))
    for (dx, dz, face) in ((-1, 0, "west"), (1, 0, "east"), (0, -1, "north"), (0, 1, "south")):
        v.put(sx + dx, F + 1, sz + dz, M(f"oak_wall_sign[facing={face},waterlogged=false]"))
    ax, ay, az = ARRIVAL
    v.used.add((ax, az))


def longhouse(v: Village):
    """Council longhouse (Rimuru's meetings): 21 x 10, tall timber walls, big thatched roof, long table."""
    x0, z0, x1, z1 = 35, 33, 55, 42
    w = M("oak_planks")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            v.put(x, G, z, M("spruce_planks"))
            if x in (x0, x1) or z in (z0, z1):
                post = (x - x0) % 5 == 0 or z in (z0, z1) and x in (x0, x1) or (x in (x0, x1) and (z - z0) % 3 == 0)
                for y in range(F, F + 4):
                    v.put(x, y, z, M("stripped_spruce_log[axis=y]") if post else w)
                if not post:
                    v.put(x, F + 2, z, M("glass_pane") if (x + z) % 2 else w)
    # Stone footing course.
    for x in range(x0 - 1, x1 + 2):
        for z in (z0 - 1, z1 + 1):
            v.put(x, G, z, M("cobblestone"))
    for z in range(z0, z1 + 1):
        for x in (x0 - 1, x1 + 1):
            v.put(x, G, z, M("cobblestone"))
    # Double door south, toward the green; a porch roof over it.
    for x in (44, 46):
        v.put(x, F, z1, M(f"spruce_door[facing=north,half=lower,hinge={'left' if x == 44 else 'right'},open=true]"))
        v.put(x, F + 1, z1, M(f"spruce_door[facing=north,half=upper,hinge={'left' if x == 44 else 'right'},open=true]"))
    v.put(45, F, z1, AIR)
    v.put(45, F + 1, z1, AIR)
    for x in (43, 47):
        for y in range(F, F + 3):
            v.put(x, y, z1 + 2, M("stripped_spruce_log[axis=y]"))
    v.fill(42, F + 3, z1 + 1, 48, F + 3, z1 + 2, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.put(45, F + 2, z1 + 2, M("lantern[hanging=true]"))
    top = gable(v, x0, z0, x1, z1, F + 4, "thatch", "x", w)
    # Ridge beam ends sticking out (crossed gable boards).
    v.put(x0 - 2, top, (z0 + z1) // 2, M("stripped_spruce_log[axis=x]"))
    v.put(x1 + 2, top, (z0 + z1) // 2, M("stripped_spruce_log[axis=x]"))
    # Interior: long table with benches, Rimuru's seat on a dais at the west end, hanging lanterns.
    for x in range(39, 52):
        v.put(x, F, 37, M("spruce_slab[type=top,waterlogged=false]"))
        v.put(x, F, 38, M("spruce_slab[type=top,waterlogged=false]"))
        v.put(x, F, 36, M("spruce_stairs[facing=north,half=bottom]"))
        v.put(x, F, 39, M("spruce_stairs[facing=south,half=bottom]"))
    v.fill(36, F, 35, 37, F, 40, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.put(36, F + 1, 37, M("light_blue_carpet"))
    v.put(36, F + 1, 38, M("light_blue_carpet"))
    for z in (35, 40):
        v.put(37, F + 1, z, M("lantern[hanging=false]"))
    for x in range(40, 52, 4):
        for z in (35, 40):
            v.put(x, F + 3, z, M("lantern[hanging=true]"))
    for z in range(34, 42, 3):
        v.put(54, F, z, M("barrel[facing=up,open=false]"))
    v.put(54, F, 41, M("chest[facing=west,type=single,waterlogged=false]"))
    for x in range(41, 50):
        v.put(x, F, 34, M("light_gray_carpet"))
    # Chains under the ridge for the lanterns: run them up to the roof.
    for x in range(40, 52, 4):
        for z in (35, 40):
            y = F + 4
            while y < SY - 1 and v.get(x, y, z) == AIR:
                v.put(x, y, z, M("chain[axis=y]"))
                y += 1


def rimuru_house(v: Village):
    house(v, 41, 22, 49, 28, door="s", roof="plank", wall="spruce_planks", post="stripped_dark_oak_log", chimney=True,
          bed="light_blue")  # Rimuru's own bed in his colour
    v.put(43, F, 27, M("light_blue_carpet"))


def forge(v: Village):
    """Kaijin's open smithy (with Kurobe's anvil) and the dwarves' workshop house."""
    x0, z0, x1, z1 = 13, 40, 25, 50
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            r = rnd(x, G, z, 12)
            v.put(x, G, z, M("cobblestone") if r < 0.45 else M("stone") if r < 0.8 else M("andesite"))
    for x in (x0, 19, x1):
        for z in (z0, z1):
            for y in range(F, F + 4):
                v.put(x, y, z, M("stripped_spruce_log[axis=y]"))
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            v.put(x, F + 3, z, M("stripped_spruce_log[axis=x]"))
    top = gable(v, x0, z0, x1, z1, F + 4, "plank", "x", M("spruce_planks"))
    # Hearth at the west end: brick forge, blast furnace and furnaces, lava glow, chimney through the roof.
    for z in range(42, 49):
        for y in (F, F + 1):
            v.put(14, y, z, M("bricks"))
    v.put(15, F, 43, M("blast_furnace[facing=east,lit=false]"))
    v.put(15, F, 44, M("furnace[facing=east,lit=false]"))
    v.put(15, F, 46, M("furnace[facing=east,lit=false]"))
    v.put(15, F, 47, M("blast_furnace[facing=east,lit=false]"))
    v.put(15, F, 45, M("lava_cauldron"))
    v.put(15, F + 1, 45, M("bricks"))
    for z in (43, 44, 46, 47):
        v.put(15, F + 1, z, M("bricks"))
    for y in range(F + 2, top + 3):
        v.put(14, y, 45, M("bricks"))
    v.put(14, top + 3, 45, M("campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]"))
    v.put(18, F, 45, M("anvil[facing=east]"))
    v.put(18, F, 43, M("smithing_table"))
    v.put(18, F, 48, M("water_cauldron[level=3]"))
    v.put(21, F, 42, M("grindstone[face=floor,facing=north]"))
    v.put(23, F, 42, M("barrel[facing=up,open=false]"))
    v.put(23, F + 1, 42, M("lantern[hanging=false]"))
    v.put(24, F, 48, M("chest[facing=west,type=single,waterlogged=false]"))
    v.put(24, F, 47, M("iron_block"))
    v.put(24, F + 1, 47, M("lantern[hanging=false]"))
    for z in (44, 46):
        v.put(19, F + 3, z, M("lantern[hanging=true]"))
        for y in range(F + 4, top + 1):
            if v.get(19, y, z) == AIR:
                v.put(19, y, z, M("chain[axis=y]"))
    # Charcoal and ore heaps outside the open south side.
    v.put(16, F, 52, M("coal_block"))
    v.put(17, F, 52, M("coal_block"))
    v.put(16, F + 1, 52, M("coal_block"))
    v.put(20, F, 52, M("raw_iron_block"))
    # Workshop house (Kaijin and the three dwarf brothers: Garm armour, Dold crafts, Mildo building).
    house(v, 14, 29, 23, 36, door="s", roof="dark", wall="spruce_planks", post="stripped_dark_oak_log", furnish=False)
    # Four plain gray beds, two to a side wall (heads to the wall), for Kaijin and the three brothers.
    for z in (32, 34):
        place_bed(v.put, v.get, 15, F, z, "west", "gray")
        place_bed(v.put, v.get, 22, F, z, "east", "gray")
    v.put(15, F, 30, M("crafting_table"))
    v.put(16, F, 30, M("loom[facing=south]"))
    v.put(17, F, 30, M("fletching_table"))
    v.put(18, F, 30, M("cartography_table"))
    v.put(20, F, 30, M("stonecutter[facing=south]"))
    v.put(22, F, 30, M("barrel[facing=up,open=false]"))
    v.put(22, F + 1, 30, M("lantern[hanging=false]"))
    v.put(22, F, 35, M("chest[facing=west,type=single,waterlogged=false]"))
    v.put(15, F, 35, M("lantern[hanging=false]"))


def weaving(v: Village):
    """Shuna's weaving hut: looms, dyed wool bales, cloth drying under an awning."""
    house(v, 63, 44, 72, 52, door="w", roof="thatch", wall="birch_planks", post="stripped_spruce_log", furnish=False)
    for z in (45, 47):
        v.put(71, F, z, M("loom[facing=west]"))
    v.put(71, F, 51, M("barrel[facing=up,open=false]"))
    v.put(71, F + 1, 51, M("lantern[hanging=false]"))
    v.put(64, F, 45, M("lantern[hanging=false]"))
    for i, colour in enumerate(("white", "light_blue", "pink", "purple", "white")):
        v.put(64 + i, F, 51, M(f"{colour}_wool"))
    v.put(64, F + 1, 51, M("white_wool"))
    for x in range(65, 70):
        v.put(x, F, 47, M("white_carpet"))
    # Awning on the west side, looms and cloth bales under it.
    for z in (44, 52):
        for y in range(F, F + 3):
            v.put(60, y, z, M("spruce_fence"))
    v.fill(60, F + 3, 44, 62, F + 3, 52, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.put(61, F, 45, M("loom[facing=west]"))
    v.put(61, F, 51, M("loom[facing=west]"))
    v.put(61, F, 50, M("white_wool"))
    v.put(61, F + 1, 50, M("white_wool"))
    v.put(61, F, 46, M("light_blue_wool"))
    v.put(61, F + 2, 47, M("lantern[hanging=true]"))
    v.put(61, F + 2, 50, M("lantern[hanging=true]"))
    # Drying line south of the hut: posts with cloth draped over a rail.
    for x in (64, 71):
        for y in range(F, F + 3):
            v.put(x, y, 55, M("spruce_fence"))
    for x in range(65, 71):
        v.put(x, F + 2, 55, M(("white", "light_blue", "white", "pink", "white", "light_gray")[x - 65] + "_wool"))


def store(v: Village):
    """Raised food store on log stilts (dry and out of reach of beasts), stairs up the south side."""
    x0, z0, x1, z1 = 58, 31, 64, 36
    for x in (x0, x1):
        for z in (z0, z1):
            for y in (F, F + 1):
                v.put(x, y, z, M("spruce_log[axis=y]"))
    v.fill(x0, F + 2, z0, x1, F + 2, z1, M("spruce_planks"))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                corner = x in (x0, x1) and z in (z0, z1)
                for y in (F + 3, F + 4):
                    v.put(x, y, z, M("spruce_log[axis=y]") if corner else M("spruce_planks"))
    v.put(61, F + 3, z1, AIR)
    v.put(61, F + 4, z1, AIR)
    v.put(61, F, z1 + 2, M("spruce_stairs[facing=north,half=bottom]"))
    v.put(61, F + 1, z1 + 1, M("spruce_stairs[facing=north,half=bottom]"))
    v.put(61, F, z1 + 1, M("spruce_planks"))
    gable(v, x0, z0, x1, z1, F + 5, "thatch", "x", M("spruce_planks"))
    for x in (59, 60, 63):
        v.put(x, F + 3, 32, M("barrel[facing=up,open=false]"))
    v.put(59, F + 3, 35, M("hay_block[axis=y]"))
    v.put(63, F + 3, 35, M("lantern[hanging=false]"))
    v.put(60, F + 4, 32, M("lantern[hanging=false]"))
    # Under the store: hay, a drying rack with meat (smoker), firewood.
    v.put(59, F, 32, M("hay_block[axis=x]"))
    v.put(60, F, 32, M("hay_block[axis=z]"))
    v.put(59, F + 1, 32, M("hay_block[axis=x]"))
    v.put(62, F, 33, M("smoker[facing=south,lit=false]"))
    for x in (70, 72):
        for y in (F, F + 1):
            v.put(x, y, 35, M("oak_fence"))
    v.put(71, F + 1, 35, M("chain[axis=x]"))


def goblin_quarter(v: Village):
    """The goblins' own quarter (north-east): Tensura goblin village pieces placed as they come from the mod,
    so the old village is still there inside the new town. Rigurd's chief hut faces the goblins' campfire,
    the sick tent (where Rimuru's potions went) to the west, tents to the east and north-west, the goblins'
    little watch tower at the forest edge, and their skull arch where the quarter meets the town."""
    v.paste("goblin_chief_oak", 63, 14, turns=2)          # x63-71 z14-22, door south to the fire
    v.paste("goblin_campfire_oak", 65, 23)                  # x65-69 z23-29, fire at (67, 27)
    v.paste("goblin_arch_oak", 66, 30)                      # x66-70 z30-32, skull facing the town
    v.paste("goblin_medical_tent_birch", 53, 23, turns=1)   # x53-62 z23-29, door east to the fire
    v.paste("goblin_tent_oak", 72, 21, turns=3)             # x72-75 z21-25, door west to the fire
    v.paste("goblin_tent_birch", 72, 27, turns=3)           # x72-75 z27-31
    v.paste("goblin_tent_oak", 57, 16, turns=1)             # x57-60 z16-20, door east to the chief hut
    v.paste("goblin_tower_oak", 76, 29, turns=3)            # x76-80 z29-32
    # Light the pieces from inside: hanging lanterns under the thatch, as the town now lights everything.
    v.put(67, F + 1, 18, M("lantern[hanging=true]"))          # under the chief hut's ceiling slabs
    for x in (55, 59):
        v.put(x, F + 2, 26, M("lantern[hanging=true]"))       # under the sick tent's ridge


def homes(v: Village):
    """Finished hobgoblin houses (the first ones Mildo's crews put up)."""
    house(v, 55, 58, 62, 64, door="w", roof="thatch")
    house(v, 66, 58, 73, 64, door="n", roof="plank", chimney=True)
    house(v, 25, 19, 32, 26, door="s", roof="thatch", wall="spruce_planks")
    house(v, 30, 46, 36, 53, door="e", roof="thatch")


def building_site(v: Village):
    """South-west: houses going up (half-roofed, timber frame, foundation), lumber and tools."""
    # A: walls up, roof half done, scaffolding on the open side.
    house(v, 13, 57, 21, 63, door="n", roof="thatch", stage="roofing", furnish=False)
    for x in (18, 20):
        scaffold(v, x, 64, 5)
    v.put(17, F, 64, M("ladder[facing=south,waterlogged=false]"))
    # B: timber frame on a plank floor.
    x0, z0, x1, z1 = 25, 59, 32, 65
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            v.put(x, G, z, M("spruce_planks"))
    for x in (x0, 28, x1):
        for z in (z0, z1):
            for y in range(F, F + 4):
                v.put(x, y, z, M("stripped_spruce_log[axis=y]"))
    for z in (62,):
        for x in (x0, x1):
            for y in range(F, F + 4):
                v.put(x, y, z, M("stripped_spruce_log[axis=y]"))
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            v.put(x, F + 3, z, M("stripped_spruce_log[axis=x]"))
    for z in range(z0 + 1, z1):
        for x in (x0, x1):
            v.put(x, F + 3, z, M("stripped_spruce_log[axis=z]"))
    for x in range(x0 + 1, x0 + 4):
        v.put(x, F, z0, M("oak_planks"))
        v.put(x, F + 1, z0, M("oak_planks"))
    plank_stack(v, 30, 61, 2)
    plank_stack(v, 30, 62, 1)
    v.put(27, F, 63, M("crafting_table"))
    scaffold(v, 33, 60, 4)
    scaffold(v, 33, 64, 4)
    # C: foundation stones and corner stakes.
    x0, z0, x1, z1 = 18, 69, 25, 74
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                v.put(x, G, z, M("cobblestone"))
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        v.put(x, F, z, M("oak_fence"))
    v.put(x0, F + 1, z0, M("oak_fence"))
    for x in range(x0 + 1, x0 + 4):
        v.put(x, F, z0, M("cobblestone"))
    # Lumber yard: log piles, plank stacks, a sawhorse, a stonecutter used as a saw bench.
    for i, (x, z, wood) in enumerate(((28, 70, "oak_log"), (28, 74, "spruce_log"), (33, 71, "birch_log"))):
        log_pile(v, x, z, 4, "x", wood)
    plank_stack(v, 35, 66, 3, "oak")
    plank_stack(v, 36, 66, 2, "oak")
    plank_stack(v, 35, 67, 2, "spruce")
    sawhorse(v, 23, 66)
    v.put(27, F, 67, M("stonecutter[facing=north]"))
    v.put(26, F, 67, M("crafting_table"))
    v.put(29, F, 67, M("barrel[facing=up,open=false]"))
    v.put(29, F + 1, 67, M("lantern[hanging=false]"))
    v.lamp(22, 67, 2)
    v.lamp(33, 68, 2)


def farm(v: Village):
    """Fenced field south-east (wheat, carrots, potatoes, beetroot), a scarecrow, the herb patch."""
    x0, z0, x1, z1 = 51, 68, 67, 78
    crops = ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                v.put(x, F, z, M("oak_fence"))
                v.put(x, G, z, M("grass_block"))
                continue
            if z == 73:
                v.put(x, G, z, M("water[level=0]"))
                continue
            v.put(x, G, z, M("farmland[moisture=7]"))
            v.put(x, F, z, M(crops[((x - x0 - 1) // 4) % 4]))
    v.put(x0, F, 73, M("oak_fence_gate[facing=west,in_wall=false,open=false,powered=false]"))
    for x in (x0, x1):
        v.put(x, G, 73, M("grass_block"))
    v.put(58, F, 73, M("oak_fence"))
    v.put(58, G, 73, M("dirt"))
    v.put(58, F + 1, 73, M("hay_block[axis=y]"))
    v.put(58, F + 2, 73, M("carved_pumpkin[facing=west]"))
    for x in (x0, x1):
        for z in (z0, z1):
            v.put(x, F + 1, z, M("lantern[hanging=false]"))
    # Herb patch (hipokute herbs for Rimuru's potions): ferns and wildflowers on podzol, low fence.
    hx0, hz0, hx1, hz1 = 70, 66, 75, 71
    herbs = ("fern", "azure_bluet", "fern", "lily_of_the_valley", "fern", "oxeye_daisy")
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            if x in (hx0, hx1) or z in (hz0, hz1):
                v.put(x, F, z, M("spruce_fence"))
                continue
            v.put(x, G, z, M("podzol"))
            v.put(x, F, z, M(herbs[(x * 3 + z) % len(herbs)]))
    v.put(hx0, F, 68, M("spruce_fence_gate[facing=west,in_wall=false,open=false,powered=false]"))
    v.put(hx1, F + 1, hz1, M("lantern[hanging=false]"))


def lookout(v: Village):
    """Lookout tower (north-west): four log legs, a ladder up a central post, a railed platform, a roof."""
    x0, z0, x1, z1 = 13, 13, 17, 17
    cx, cz = 15, 15
    for x in (x0, x1):
        for z in (z0, z1):
            for y in range(F, F + 13):
                v.put(x, y, z, M("stripped_spruce_log[axis=y]"))
    for y in range(F, F + 9):
        v.put(cx, y, cz, M("spruce_log[axis=y]"))
    for y in range(F, F + 10):
        v.put(cx, y, cz + 1, M("ladder[facing=south,waterlogged=false]"))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)) or (x, z) == (cx, cz + 1):
                continue
            v.put(x, F + 9, z, M("spruce_planks"))
            if x in (x0, x1) or z in (z0, z1):
                v.put(x, F + 10, z, M("spruce_fence"))
    # Cross bracing low down.
    for x in range(x0 + 1, x1):
        v.put(x, F + 4, z0, M("stripped_spruce_log[axis=x]"))
        v.put(x, F + 4, z1, M("stripped_spruce_log[axis=x]"))
    v.fill(x0 - 1, F + 13, z0 - 1, x1 + 1, F + 13, z1 + 1, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.fill(x0, F + 13, z0, x1, F + 13, z1, M("spruce_planks"))
    v.put(cx, F + 14, cz, M("spruce_slab[type=bottom,waterlogged=false]"))
    v.put(cx, F + 12, cz, M("lantern[hanging=true]"))
    v.put(x0 + 1, F + 10, z0 + 1, M("lantern[hanging=false]"))


def palisade(v: Village):
    """Palisade begun on the forest side (west), sharpened log stakes; a south gate; stakes where it stops."""
    gx = C
    done = set()
    for i in range(0, 1200):
        t = math.radians(80 + i * 0.2)
        cs, sn = math.cos(t), math.sin(t)
        r = 35.5 / (abs(cs) ** 3 + abs(sn) ** 3) ** (1 / 3)
        x, z = round(C + r * cs), round(C + r * sn)
        if (x, z) in done:
            continue
        done.add((x, z))
        deg = 80 + i * 0.2
        if abs(x - gx) <= 3 and z > C:
            continue  # the gate gap
        if deg <= 86:
            h = 4
        elif deg <= 215:
            h = 4
        elif deg <= 245:
            h = 1 + int(rnd(x, 0, z, 81) * 2.5)
            if rnd(x, 0, z, 82) < 0.35:
                continue
        else:
            break
        if v.get(x, F, z) != AIR:
            continue
        for y in range(F, F + h):
            v.put(x, y, z, M("oak_log[axis=y]"))
        if h >= 3:
            v.put(x, F + h, z, M("oak_fence"))
    # South gate: two tall posts and a lintel, lanterns hanging under it.
    for x in (gx - 3, gx + 3):
        for y in range(F, F + 6):
            v.put(x, y, 81, M("oak_log[axis=y]"))
    for x in range(gx - 4, gx + 5):
        v.put(x, F + 6, 81, M("oak_log[axis=x]"))
    for x in (gx - 2, gx + 2):
        v.put(x, F + 5, 81, M("lantern[hanging=true]"))
    # Where the wall stops: a stack of logs waiting to be raised.
    log_pile(v, 8, 26, 4, "z", "spruce_log")


# --- trees -----------------------------------------------------------------------------------------
def tree(v: Village, x, z, kind, h):
    log = M(f"{kind}_log[axis=y]")
    leaves = LEAVES[kind]
    top = F + h
    if top + 2 >= SY:
        return
    for y in range(F, top):
        v.bp.set(x, y, z, log)
    radius = 2.6 if kind != "spruce" else 2.2
    for y in range(top - 3, top + 2):
        rr = radius if y < top else radius - 1.2
        if kind == "spruce":
            rr = max(0.8, radius - (y - (top - 3)) * 0.55)
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                px, pz = x + dx, z + dz
                if not (0 <= px < SX and 0 <= pz < SZ):
                    continue
                if math.hypot(dx, dz) > rr + 0.3 or (px, pz) in v.used:
                    continue
                if v.bp.blocks.get((px, y, pz)) == AIR and rnd(px, y, pz, 55) < 0.92:
                    v.bp.blocks[(px, y, pz)] = leaves
    v.bp.set(x, top, z, leaves)
    v.bp.set(x, top + 1, z, leaves)


def forest_edge(v: Village):
    """Our own ring of forest round the clearing: hides the cut edge of the real forest outside the box."""
    trunks = []
    for x in range(SX):
        for z in range(SZ):
            if inside(x, z) or dist(x, z) < edge(x, z) + 1.5 or (x, z) in v.used:
                continue
            if rnd(x, 0, z, 60) > 0.16:
                continue
            if any(abs(x - a) < 4 and abs(z - b) < 4 for a, b in trunks):
                continue
            trunks.append((x, z))
            q = rnd(x, 1, z, 61)
            kind = "oak" if q < 0.4 else "birch" if q < 0.65 else "dark_oak" if q < 0.85 else "spruce"
            tree(v, x, z, kind, 5 + int(rnd(x, 2, z, 62) * 4) + (2 if kind == "spruce" else 0))
    # A few trees left standing inside the village for shade.
    for x, z, kind in ((38, 60, "oak"), (60, 41, "birch"), (28, 38, "oak"), (75, 52, "birch")):
        tree(v, x, z, kind, 6)


# --- lights, plants, checks ------------------------------------------------------------------------
def road_lamps(v: Village):
    for x, z in ((42, 46), (48, 46), (42, 55), (49, 55), (45, 64), (45, 72), (46, 79), (37, 50), (29, 44),
                 (55, 47), (59, 49), (52, 41), (57, 39), (40, 31), (51, 31), (62, 27), (31, 57), (40, 66),
                 (50, 66), (70, 41), (24, 54), (16, 26), (37, 18), (69, 16), (77, 45), (60, 82), (30, 80),
                 (12, 50), (81, 28), (11, 34), (78, 64)):
        if v.get(x, F, z) == AIR and v.get(x, G, z) not in (M("water[level=0]"),) and inside(x, z):
            v.lamp(x, z, 2)


def light(v: Village):
    """Add lamp posts (or floor lanterns indoors) until no spawnable spot in the clearing is dark."""
    bp = v.bp
    for _ in range(10):
        cands = [p for p, s in bp.blocks.items() if s == AIR and p[1] >= F and inside(p[0], p[2])]
        spots = dark_spots(bp.blocks, bp.size, cands)
        if not spots:
            return
        placed = []
        for (x, y, z) in spots:
            if any(abs(x - a) + abs(y - b) + abs(z - c) <= 9 for a, b, c in placed):
                continue
            if y == F and all(bp.blocks.get((x, yy, z)) == AIR for yy in range(F, F + 4)):
                v.lamp(x, z, 2)
            else:
                v.put(x, y, z, M("lantern[hanging=false]"))
            placed.append((x, y, z))
    raise RuntimeError("tempest: could not light every spawnable spot")


def plants(v: Village):
    for x in range(SX):
        for z in range(SZ):
            if (x, z) in v.used or v.bp.blocks.get((x, F, z)) != AIR:
                continue
            below = v.bp.blocks.get((x, G, z))
            if below not in (M("grass_block"), M("podzol")):
                continue
            q = rnd(x, F, z, 90)
            if inside(x, z):
                if q < 0.12:
                    v.bp.blocks[(x, F, z)] = M("short_grass")
                elif q < 0.14:
                    v.bp.blocks[(x, F, z)] = M(("dandelion", "poppy", "cornflower", "oxeye_daisy")[int(q * 1000) % 4])
            else:
                if q < 0.3:
                    v.bp.blocks[(x, F, z)] = M("fern") if q < 0.15 else M("short_grass")
                elif q < 0.32:
                    v.bp.blocks[(x, F, z)] = M("brown_mushroom") if below == M("podzol") else M("lily_of_the_valley")


def settle_paths(bp):
    """Dirt path under a solid block (fences included) turns to dirt as soon as the game updates it; do it here
    so the previews show what the world will."""
    soft = ("air", "lantern", "torch", "carpet", "slab", "fence_gate", "sign", "banner", "pane", "chain", "short_grass",
            "fern", "poppy", "dandelion", "cornflower", "daisy", "bluet", "valley", "mushroom")
    for (x, y, z), s in list(bp.blocks.items()):
        if s == M("dirt_path"):
            above = bp.blocks.get((x, y + 1, z), AIR).split("[", 1)[0]
            if not any(k in above for k in soft):
                bp.blocks[(x, y, z)] = M("dirt")


def check_support(bp):
    """Blocks that pop off without support: what is under them (or behind, for ladders and wall signs)."""
    bad = []
    behind = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}
    for (x, y, z), s in bp.blocks.items():
        name = s.split("[", 1)[0].split(":", 1)[1]
        below = bp.blocks.get((x, y - 1, z), AIR)
        if name == "lantern":
            need = (x, y + 1, z) if "hanging=true" in s else (x, y - 1, z)
            if bp.blocks.get(need, AIR) == AIR:
                bad.append((x, y, z, s))
        elif name in ("ladder", "oak_wall_sign"):
            face = s.split("facing=", 1)[1].split(",", 1)[0].rstrip("]")
            dx, dz = behind[face]
            if bp.blocks.get((x + dx, y, z + dz), AIR) == AIR:
                bad.append((x, y, z, s))
        elif any(k in name for k in SUPPORT_BELOW) and "upper" not in s and "part=head" not in s:
            if below == AIR:
                bad.append((x, y, z, s))
        if name in ("wheat", "carrots", "potatoes", "beetroots") and "farmland" not in below:
            bad.append((x, y, z, s))
    if bad:
        raise RuntimeError(f"tempest: {len(bad)} unsupported blocks, e.g. {bad[:5]}")


# Named hobgoblins of early Tempest (all goblins became hobgoblins when Rimuru named them); the rest unnamed.
RESIDENT_NAMES = {"goblin_chief_oak": ["Rigurd", "Rigur"], "goblin_campfire_oak": ["Gobta", ""],
                  "goblin_medical_tent_birch": ["Haruna"]}


def residents(v: Village) -> list:
    """Where life/tempest.js puts the goblin residents: Tensura's own goblin spawn points in each piece (the
    jigsaws that pull in goblin_village/goblin_spawn), at most two per piece, named ones first."""
    out = []
    for x, y, z, piece in v.spawns:
        names = RESIDENT_NAMES.get(piece, [""])
        n = sum(1 for r in out if r[4] == piece)
        if n >= max(1, len(names)) or n >= 2:
            continue
        if v.get(x, y, z) != AIR or v.get(x, y + 1, z) != AIR:
            raise RuntimeError(f"tempest: resident spot {x},{y},{z} in {piece} is not free")
        out.append([x, y, z, names[n] if n < len(names) else "", piece])
    return out


def build(bp):
    v = Village(bp)
    bp.village = v
    ground(v)
    ax, _, az = ARRIVAL
    path(v, [(45, 90), (45, 50)], 1)            # south gate - green, out through the forest
    path(v, [(45, 50), (45, 43)], 1)            # green - longhouse
    path(v, [(45, 32), (45, 29)], 0)            # longhouse - Rimuru's house
    path(v, [(39, 50), (26, 46)], 1)            # west: forge
    path(v, [(19, 39), (19, 37)], 0)            # forge - workshop
    path(v, [(51, 50), (59, 48)], 1)            # east: weaving hut
    path(v, [(50, 45), (58, 39), (68, 39), (68, 33)], 0)  # north-east: store, goblin quarter arch
    path(v, [(45, 67), (25, 67), (17, 65)], 0)  # building site
    path(v, [(45, 67), (51, 73)], 0)            # field gate
    path(v, [(30, 50), (15, 20)], 0)            # lookout
    path(v, [(56, 30), (40, 30)], 0)            # behind the longhouse
    green(v)
    longhouse(v)
    rimuru_house(v)
    forge(v)
    weaving(v)
    store(v)
    goblin_quarter(v)
    homes(v)
    building_site(v)
    farm(v)
    lookout(v)
    palisade(v)
    v.used.update((x, z) for x in range(ax - 1, ax + 2) for z in range(az - 1, az + 2))
    road_lamps(v)
    forest_edge(v)
    light(v)
    plants(v)
    settle_paths(bp)
    check_support(bp)


def outputs(bp):
    probes = [(x, z) for x in range(C - 32, C + 33, 8) for z in range(C - 32, C + 33, 8) if dist(x, z) <= R - 3]
    v = bp.village
    extras = {"loot": sorted(v.loot), "residents": residents(v)}
    body = json.dumps(extras, separators=(",", ":"))
    return {"pack/kubejs/server_scripts/ttl/generated/tempest_footprint.js":
            settlement_footprint(bp, "TtlTempestFootprint", "blueprints/tempest.py", G, probes, ARRIVAL, PARTS),
            "pack/kubejs/server_scripts/ttl/generated/tempest_extras.js":
            "// priority: 200\n// GENERATED by tools/build_structures.py from blueprints/tempest.py. Do not edit.\n"
            "// Blueprint coordinates: containers from Tensura goblin pieces with their loot tables, and the goblin\n"
            "// residents (Tensura's goblin spawn points) that life/tempest.js summons after placing the village.\n"
            f"const TtlTempestExtras = {body}\n"}
