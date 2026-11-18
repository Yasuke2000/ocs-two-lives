"""Helpers for the medieval-European human towns (blueprints/blumund.py, marris.py). Stdlib only.

Style of these towns (our interpretation, canon has no architecture notes): plastered timber-frame houses on stone
footings, tiled gable roofs, stone town walls with merlons, banners and lanterns. This is deliberately not Dwargon's
dwarven stone-in-a-mountain nor Tempest's goblin timber and thatch.

Orientation: x east, z south, y up. "Door side" letters n/s/e/w name the wall the door is in. Stairs `facing` is the
direction they ascend (their tall back side), so a roof stair on the north edge of a roof faces south.
Every Town.put raises when a block falls outside the box, so layout mistakes show up at build time.
"""
import math

from _dwargon_lib import AIR, dark_spots, noise2, rnd


def M(name: str) -> str:
    return "minecraft:" + name


# roof materials: (stairs, slab, block)
ROOFS = {
    "brick": ("brick_stairs", "brick_slab", "bricks"),
    "slate": ("deepslate_tile_stairs", "deepslate_tile_slab", "deepslate_tiles"),
    "stone": ("stone_brick_stairs", "stone_brick_slab", "stone_bricks"),
    "dark": ("dark_oak_stairs", "dark_oak_slab", "dark_oak_planks"),
    "spruce": ("spruce_stairs", "spruce_slab", "spruce_planks"),
    "mud": ("mud_brick_stairs", "mud_brick_slab", "mud_bricks"),
    "blue": ("prismarine_brick_stairs", "prismarine_brick_slab", "prismarine_bricks"),
    "copper": ("oxidized_cut_copper_stairs", "oxidized_cut_copper_slab", "oxidized_cut_copper"),
    "nether": ("red_nether_brick_stairs", "red_nether_brick_slab", "red_nether_bricks"),
}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DOORS = {"s": "north", "n": "south", "e": "west", "w": "east"}  # door in the s wall faces north (into the house)


def stair(mat: str, facing: str, half="bottom", shape="straight") -> str:
    return M(f"{mat}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]")


def slab(mat: str, kind="bottom") -> str:
    return M(f"{mat}_slab[type={kind},waterlogged=false]")


def trapdoor(mat: str, facing: str, half="bottom", open_="false") -> str:
    return M(f"{mat}_trapdoor[facing={facing},half={half},open={open_},powered=false,waterlogged=false]")


def door(mat: str, facing: str, half: str, hinge="left") -> str:
    return M(f"{mat}_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def lantern_hung() -> str:
    return M("lantern[hanging=true,waterlogged=false]")


def lantern_floor() -> str:
    return M("lantern[hanging=false,waterlogged=false]")


def banner(colour: str, rotation=0) -> str:
    return M(f"{colour}_banner[rotation={rotation}]")


def wall_banner(colour: str, facing: str) -> str:
    return M(f"{colour}_wall_banner[facing={facing}]")


def bed(colour: str, facing: str, part: str) -> str:
    return M(f"{colour}_bed[facing={facing},part={part},occupied=false]")


def fence_gate(mat: str, facing: str) -> str:
    return M(f"{mat}_fence_gate[facing={facing},in_wall=false,open=false,powered=false]")


def log(mat: str, axis="y") -> str:
    return M(f"{mat}[axis={axis}]")


class Town:
    def __init__(self, bp, G: int):
        self.bp = bp
        self.G = G
        self.F = G + 1
        self.sx, self.sy, self.sz = bp.size
        self.used: set = set()   # columns taken by buildings (no plants, no trees)
        self.points: dict = {}   # named blueprint coordinates reported in the lore and the placement toml

    # -- primitives ------------------------------------------------------------------------------
    def put(self, x, y, z, state):
        self.bp.set(x, y, z, state)
        if y >= self.F and state != AIR:
            self.used.add((x, z))

    def get(self, x, y, z):
        return self.bp.blocks.get((x, y, z))

    def fill(self, x1, y1, z1, x2, y2, z2, state):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.put(x, y, z, state)

    def ring(self, x1, z1, x2, z2, y1, y2, state):
        """Vertical shell (outer wall only) of a rectangle."""
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    for y in range(y1, y2 + 1):
                        self.put(x, y, z, state)

    def clear(self, x1, y1, z1, x2, y2, z2):
        self.fill(x1, y1, z1, x2, y2, z2, AIR)

    def lamp(self, x, z, h=3, post="stone_brick_wall", y0=None):
        y0 = self.F if y0 is None else y0
        for y in range(y0, y0 + h):
            self.put(x, y, z, M(f"{post}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"))
        self.put(x, y0 + h, z, lantern_floor())

    # -- ground ----------------------------------------------------------------------------------
    def base_ground(self, grass=("grass_block",) * 9 + ("coarse_dirt",)):
        bp, G = self.bp, self.G
        for x in range(self.sx):
            for z in range(self.sz):
                for y in range(G):
                    bp.blocks[(x, y, z)] = M("dirt")
                n = noise2(x, z, 7, 5)
                bp.blocks[(x, G, z)] = M(grass[min(len(grass) - 1, int(n * len(grass)))])
                for y in range(self.F, self.sy):
                    bp.blocks[(x, y, z)] = AIR

    def pave(self, x1, z1, x2, z2, pattern="street", y=None):
        """Street paving: 'street' = gravel middle with cobble edges, 'plaza' = checker of stone bricks and
        polished andesite, 'cobble' = mixed cobblestone / stone."""
        y = self.G if y is None else y
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                r = rnd(x, y, z, 7)
                if pattern == "plaza":
                    if (x // 2 + z // 2) % 2:
                        s = "polished_andesite" if r > 0.12 else "andesite"
                    else:
                        s = "stone_bricks" if r > 0.2 else "cracked_stone_bricks"
                elif pattern == "street":
                    edge = x in (x1, x2) or z in (z1, z2)
                    s = ("cobblestone" if r > 0.3 else "mossy_cobblestone") if edge else ("gravel" if r > 0.25 else "coarse_dirt")
                else:
                    s = "cobblestone" if r > 0.35 else "stone" if r > 0.12 else "mossy_cobblestone"
                self.bp.blocks[(x, y, z)] = M(s)
                self.used.add((x, z)) if y == self.G else None

    # -- masonry -----------------------------------------------------------------------------------
    def stone(self, x, y, z, kinds=("stone_bricks", "stone_bricks", "stone_bricks", "cracked_stone_bricks", "mossy_stone_bricks")):
        r = rnd(x, y, z, 3)
        self.put(x, y, z, M(kinds[int(r * len(kinds)) % len(kinds)]))

    def rampart(self, x1, z1, x2, z2, h, outer):
        """Solid wall block x1..x2 / z1..z2, F..F+h-1, with a walkway on top and merlons on the `outer` side
        ('n','s','e','w') every other block, plus a low inner parapet."""
        F = self.F
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                for y in range(F, F + h):
                    self.stone(x, y, z)
                self.put(x, F + h, z, M("stone_bricks"))
        merlon = {"n": [(x, z1) for x in range(x1, x2 + 1)], "s": [(x, z2) for x in range(x1, x2 + 1)],
                  "w": [(x1, z) for z in range(z1, z2 + 1)], "e": [(x2, z) for z in range(z1, z2 + 1)]}[outer]
        for i, (x, z) in enumerate(merlon):
            if i % 2 == 0:
                self.put(x, F + h + 1, z, M("stone_bricks"))
                self.put(x, F + h + 2, z, M("stone_brick_slab[type=bottom,waterlogged=false]"))

    def battlements(self, x1, z1, x2, z2, y):
        """Merlon ring on the edge of a flat roof at layer y (every other block, 2 high)."""
        i = 0
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    if (x + z) % 2 == 0:
                        self.put(x, y, z, M("stone_bricks"))
                        self.put(x, y + 1, z, M("stone_brick_slab[type=bottom,waterlogged=false]"))
                    i += 1

    # -- roofs -------------------------------------------------------------------------------------
    def gable(self, x0, z0, x1, z1, y0, roof: str, axis: str, fill: str, overhang=1):
        """Gable roof over walls x0..x1 / z0..z1 from layer y0, ridge along `axis`; `fill` closes the gable ends."""
        st, sl, bl = ROOFS[roof]
        if axis == "x":
            a0, a1, b0, b1 = x0, x1, z0, z1
            lo, hi = "south", "north"
        else:
            a0, a1, b0, b1 = z0, z1, x0, x1
            lo, hi = "east", "west"
        k = 0
        top = y0
        while True:
            lb, hb, y = b0 - overhang + k, b1 + overhang - k, y0 + k
            if lb > hb:
                break
            for a in range(a0 - overhang, a1 + overhang + 1):
                for b, face in ((lb, lo), (hb, hi)):
                    if lb == hb and b == hb and face == hi:
                        continue
                    s = M(bl) if lb == hb else stair(st[:-7], face)
                    x, z = (a, b) if axis == "x" else (b, a)
                    self.put(x, y, z, s)
            if k > 0:
                for b in range(lb + 1, hb):
                    for a in (a0, a1):
                        x, z = (a, b) if axis == "x" else (b, a)
                        self.put(x, y, z, fill)
            top = y
            k += 1
        return top

    def hip(self, x0, z0, x1, z1, y0, roof: str, overhang=1, solid_top=True):
        """Pyramid (hip) roof over x0..x1 / z0..z1 from layer y0. Returns the top layer."""
        st, sl, bl = ROOFS[roof]
        name = st[:-7]
        k = 0
        top = y0
        while True:
            a0, a1, b0, b1 = x0 - overhang + k, x1 + overhang - k, z0 - overhang + k, z1 + overhang - k
            if a0 > a1 or b0 > b1:
                break
            y = y0 + k
            if a0 == a1 or b0 == b1:
                for x in range(a0, a1 + 1):
                    for z in range(b0, b1 + 1):
                        self.put(x, y, z, M(bl))
                top = y
                break
            for x in range(a0, a1 + 1):
                for z in range(b0, b1 + 1):
                    nx, sx_ = x == a0, x == a1
                    nz, sz_ = z == b0, z == b1
                    if nx and nz:
                        s = stair(name, "south", shape="outer_left")
                    elif sx_ and nz:
                        s = stair(name, "south", shape="outer_right")
                    elif nx and sz_:
                        s = stair(name, "north", shape="outer_right")
                    elif sx_ and sz_:
                        s = stair(name, "north", shape="outer_left")
                    elif nz:
                        s = stair(name, "south")
                    elif sz_:
                        s = stair(name, "north")
                    elif nx:
                        s = stair(name, "east")
                    elif sx_:
                        s = stair(name, "west")
                    else:
                        s = M(bl) if solid_top else AIR
                    self.put(x, y, z, s)
            top = y
            k += 1
        return top

    # -- houses ------------------------------------------------------------------------------------
    def house(self, x0, z0, x1, z1, door_side="s", storeys=2, plaster="calcite", frame="dark_oak", roof="brick",
              axis=None, base="stone_bricks", furnish=True, door_mat="spruce", shutters=True, storey_h=4, door_x=None):
        """Timber-frame house: stone footing, plaster panels between a dark frame, windows with shutters, floors and
        a loft ceiling, ladder up, tiled gable roof. Returns (top roof y, door position)."""
        F, G = self.F, self.G
        h = storey_h * storeys
        axis = axis or ("x" if (x1 - x0) >= (z1 - z0) else "z")
        pl, fr = M(plaster), log(f"{frame}_log")
        pane = M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]")
        if door_side in ("s", "n"):
            dx = door_x if door_x is not None else (x0 + x1) // 2
            dz = z1 if door_side == "s" else z0
        else:
            dz = door_x if door_x is not None else (z0 + z1) // 2
            dx = x1 if door_side == "e" else x0
        lx, lz = (x0 + 1, z0 + 1) if door_side != "n" else (x0 + 1, z1 - 1)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.put(x, G, z, M("spruce_planks"))
                edge = x in (x0, x1) or z in (z0, z1)
                if not edge:
                    for s in range(1, storeys + 1):  # floors and the loft ceiling
                        if not (s < storeys and (x, z) == (lx, lz)):
                            self.put(x, F + storey_h * s - 1, z, M("spruce_planks"))
                    continue
                corner = x in (x0, x1) and z in (z0, z1)
                on_x = z in (z0, z1)
                along, lo, hi_ = (x, x0, x1) if on_x else (z, z0, z1)
                post = corner or ((along - lo) % 4 == 0 and (hi_ - lo) > 5 and along != hi_)
                for y in range(F, F + h):
                    if y == F:
                        s_ = M(base)
                    elif post:
                        s_ = fr
                    elif (y - F) % storey_h == storey_h - 1:
                        s_ = log(f"stripped_{frame}_log", "x" if on_x else "z")
                    else:
                        s_ = pl
                    self.put(x, y, z, s_)
                if not corner and not post and (along - lo) % 4 == 2 and (x, z) != (dx, dz):
                    for s in range(storeys):
                        self.put(x, F + storey_h * s + 1, z, pane)
                        if shutters:
                            for d in (-1, 1):
                                sx_, sz_ = (x + d, z) if on_x else (x, z + d)
                                ox_, oz_ = ((0, -1) if z == z0 else (0, 1)) if on_x else ((-1, 0) if x == x0 else (1, 0))
                                face = {(0, -1): "south", (0, 1): "north", (-1, 0): "east", (1, 0): "west"}[(ox_, oz_)]
                                if self.get(sx_, F + storey_h * s + 1, sz_) in (pl,):
                                    self.put(sx_ + ox_, F + storey_h * s + 1, sz_ + oz_,
                                             trapdoor("dark_oak", face, "bottom", "true"))
        face = DOORS[door_side]
        self.put(dx, F, dz, door(door_mat, face, "lower"))
        self.put(dx, F + 1, dz, door(door_mat, face, "upper"))
        ox, oz = {"s": (0, 1), "n": (0, -1), "e": (1, 0), "w": (-1, 0)}[door_side]
        self.put(dx + ox, G, dz + oz, M("cobblestone"))
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        for s in range(storeys):
            self.put(cx, F + storey_h * s + storey_h - 2, cz, lantern_hung())
        if storeys > 1:
            face_l = "south" if door_side != "n" else "north"
            for y in range(F, F + storey_h * (storeys - 1) + 1):
                self.put(lx, y, lz, M(f"ladder[facing={face_l},waterlogged=false]"))
        if furnish:
            self._furnish(x0, z0, x1, z1, door_side, storeys, storey_h)
        return self.gable(x0, z0, x1, z1, F + h, roof, axis, pl), (dx, dz)

    def _furnish(self, x0, z0, x1, z1, door_side, storeys, storey_h):
        F = self.F
        bx, bz = (x1 - 1, z0 + 1) if door_side != "n" else (x1 - 1, z1 - 2)
        if storeys > 1:
            y = F + storey_h
            # The head lies one block toward `facing` from the foot: head against the back wall, foot toward the room.
            facing = "north" if door_side != "n" else "south"
            zz = bz + (1 if facing == "north" else -1)
            if self.get(bx, y, bz) == AIR and self.get(bx, y, zz) == AIR:
                self.put(bx, y, bz, bed("red", facing, "head"))
                self.put(bx, y, zz, bed("red", facing, "foot"))
            if self.get(bx - 1, y, bz) == AIR:
                self.put(bx - 1, y, bz, M("barrel[facing=up,open=false]"))
        gx, gz = (x1 - 1, z1 - 1) if door_side != "n" else (x1 - 1, z0 + 1)
        if self.get(gx, F, gz) == AIR:
            self.put(gx, F, gz, M("crafting_table"))
        if self.get(gx - 1, F, gz) == AIR:
            self.put(gx - 1, F, gz, M("barrel[facing=up,open=false]"))
        if (x1 - x0) >= 6 and self.get(x0 + 3, F, z0 + 2 if door_side != "n" else z1 - 2) == AIR:
            self.put(x0 + 3, F, z0 + 2 if door_side != "n" else z1 - 2, M("dark_oak_slab[type=bottom,waterlogged=false]"))

    # -- props --------------------------------------------------------------------------------------
    def stall(self, x, z, w=5, d=3, colours=("red", "white"), goods=None, facing="s"):
        """Market stall at corner (x, z): four posts, a striped wool roof, a counter with goods on the `facing` side."""
        F = self.F
        for px, pz in ((x, z), (x + w - 1, z), (x, z + d - 1), (x + w - 1, z + d - 1)):
            for y in range(F, F + 3):
                self.put(px, y, pz, M("spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"))
        for i in range(w):
            for j in range(d):
                self.put(x + i, F + 3, z + j, M(colours[(i) % len(colours)] + "_wool"))
        # counter on the facing side
        cz = z + d - 1 if facing == "s" else z
        for i in range(1, w - 1):
            self.put(x + i, F, cz, M("spruce_planks"))
            g = (goods or ["barrel", "hay_block", "melon", "pumpkin", "barrel"])[(i - 1) % 5]
            if g == "barrel":
                self.put(x + i, F + 1, cz, M("barrel[facing=up,open=false]"))
            elif g == "hay_block":
                self.put(x + i, F + 1, cz, M("hay_block[axis=y]"))
            else:
                self.put(x + i, F + 1, cz, M(g))
        self.put(x + w // 2, F + 2, z + d // 2, lantern_hung())

    def tower(self, x0, z0, x1, z1, h, roof="slate", room=True, flags=None):
        """Square tower: solid stone to F+h, then a lit watch room (1 thick walls, 3 high, window slits) with a
        pyramid roof, or a battlemented platform when `room` is False."""
        F = self.F
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(F, F + h):
                    self.stone(x, y, z)
                self.put(x, F + h, z, M("stone_bricks"))
        if not room:
            self.battlements(x0, z0, x1, z1, F + h + 1)
            return F + h + 1
        # slightly narrower room on top with an overhanging cornice
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    self.put(x, F + h, z, M("stone_brick_stairs[facing=%s,half=top,shape=straight,waterlogged=false]" % (
                        "south" if z == z0 else "north" if z == z1 else "east" if x == x0 else "west")))
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                self.put(x, F + h, z, M("stone_bricks"))
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                for y in range(F + h + 1, F + h + 4):
                    self.put(x, y, z, AIR)
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                if x in (x0 + 1, x1 - 1) or z in (z0 + 1, z1 - 1):
                    for y in range(F + h + 1, F + h + 4):
                        corner = x in (x0 + 1, x1 - 1) and z in (z0 + 1, z1 - 1)
                        mid = ((x - x0) + (z - z0)) % 2 == 0
                        if y == F + h + 2 and not corner and mid:
                            self.put(x, y, z, M("glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"))
                        else:
                            self.put(x, y, z, log("stripped_dark_oak_log") if corner else M("calcite"))
        if x1 - x0 >= 4:
            cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
            self.put(cx, F + h + 3, cz, lantern_hung())
        else:
            cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
            self.put(cx, F + h + 3, cz, lantern_hung())
        top = self.hip(x0 + 1, z0 + 1, x1 - 1, z1 - 1, F + h + 4, roof, overhang=1)
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        for y in range(top + 1, top + 4):
            self.put(mx, y, mz, M("dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"))
        if flags:
            self.put(*flags(top + 3))
        return top + 3

    def banner_pole(self, x, z, colour="red", h=5, y0=None):
        y0 = self.F if y0 is None else y0
        for y in range(y0, y0 + h):
            self.put(x, y, z, M("spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]"))
        self.put(x, y0 + h, z, banner(colour))

    def tree(self, x, z, kind="oak", h=5, r=2):
        F = self.F
        for y in range(F, F + h):
            self.put(x, y, z, log(f"{kind}_log"))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in range(-1, 3):
                    rr = r - (1 if dy >= 1 else 0)
                    if dx * dx + dz * dz + (dy * dy) // 2 <= rr * rr + 1 and not (dx == 0 and dz == 0 and dy <= 0):
                        px, py, pz = x + dx, F + h - 1 + dy, z + dz
                        if 0 <= px < self.sx and 0 <= pz < self.sz and self.get(px, py, pz) in (AIR, None):
                            if rnd(px, py, pz, 17) > 0.12:
                                self.put(px, py, pz, M(f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"))

    # -- checks ---------------------------------------------------------------------------------------
    def light(self, inside, max_rounds=14):
        """Add lamp posts outdoors / floor lanterns indoors until no spawnable spot inside `inside(x, z)` is dark."""
        bp, F = self.bp, self.F
        for _ in range(max_rounds):
            cands = [p for p, s in bp.blocks.items() if s == AIR and p[1] >= F and inside(p[0], p[2])]
            spots = dark_spots(bp.blocks, bp.size, cands)
            if not spots:
                return
            placed = []
            for (x, y, z) in spots:
                if any(abs(x - a) + abs(y - b) + abs(z - c) <= 8 for a, b, c in placed):
                    continue
                if y == F and all(bp.blocks.get((x, yy, z)) == AIR for yy in range(F, F + 5)) and (x, z) not in self.used:
                    self.lamp(x, z, 2, post="spruce_fence")
                else:
                    self.put(x, y, z, lantern_floor())
                placed.append((x, y, z))
        raise RuntimeError(f"{bp.name}: could not light every spawnable spot")

    def check_support(self):
        """Lanterns, ladders, wall banners, plants and carpets without support (they would pop off)."""
        bad = []
        behind = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}
        for (x, y, z), s in self.bp.blocks.items():
            name = s.split("[", 1)[0].split(":", 1)[1]
            below = self.bp.blocks.get((x, y - 1, z), AIR)
            if name == "lantern":
                need = (x, y + 1, z) if "hanging=true" in s else (x, y - 1, z)
                if self.bp.blocks.get(need, AIR) == AIR:
                    bad.append((x, y, z, s))
            elif name == "ladder" or name.endswith("wall_banner") or name.endswith("wall_sign"):
                face = s.split("facing=", 1)[1].split(",", 1)[0].rstrip("]")
                dx, dz = behind[face]
                if self.bp.blocks.get((x + dx, y, z + dz), AIR) == AIR:
                    bad.append((x, y, z, s))
            elif name.endswith("carpet") or name in ("short_grass", "fern", "poppy", "dandelion", "cornflower",
                                                      "oxeye_daisy", "wheat", "red_tulip", "allium", "lily_of_the_valley") \
                    or name.endswith("_banner") and "wall" not in name or name.endswith("_door"):
                if below == AIR and "upper" not in s:
                    bad.append((x, y, z, s))
        if bad:
            raise RuntimeError(f"{self.bp.name}: {len(bad)} unsupported blocks, e.g. {bad[:5]}")
