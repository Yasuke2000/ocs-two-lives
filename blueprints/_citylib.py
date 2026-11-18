"""Shared building blocks for the canon city landmarks (englassia.py, lubelius.py): stdlib only.

A Site wraps a Blueprint with a ground layer G (you walk at G + 1) and offers the pieces a stone city is made
of: material sets with stairs and slabs, walls with window bays, gable and hip roofs, spires, crenellations,
columns, arches, doors, lamps, trees, a fountain, plus a block-light fixer that adds lanterns until no
spawnable spot in the plot is dark (same rule as tempest.py, via _dwargon_lib.dark_spots).

Stairs: `facing` is the DOWNHILL direction of the stair (a roof slope falling north uses facing north).
Everything above the ground layer that is not placed stays air; the placer clears the box above the ground
layer (clear_above in design/builds/<name>.toml), so no explicit air is stored.
"""
import math

from _dwargon_lib import AIR, dark_spots

DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}
NAME = {"n": "north", "s": "south", "e": "east", "w": "west"}
OPP = {"n": "s", "s": "n", "e": "w", "w": "e"}


def M(name: str) -> str:
    return "minecraft:" + name


class Mat:
    """A building material with its stair, slab and (optional) wall variants."""

    def __init__(self, block, stairs=None, slab=None, wall=None):
        self.block, self.stairs, self.slab, self.wall = block, stairs, slab, wall


class Site:
    def __init__(self, bp, G: int):
        self.bp, self.G, self.F = bp, G, G + 1
        self.SX, self.SY, self.SZ = bp.size

    # --- raw access ------------------------------------------------------------------------------
    def put(self, x, y, z, state: str) -> None:
        if state.startswith("minecraft:") or ":" in state:
            self.bp.set(x, y, z, state)
        else:
            self.bp.set(x, y, z, M(state))

    def get(self, x, y, z):
        return self.bp.blocks.get((x, y, z))

    def fill(self, x1, y1, z1, x2, y2, z2, state: str) -> None:
        if ":" not in state:
            state = M(state)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.bp.set(x, y, z, state)

    def air(self, x1, y1, z1, x2, y2, z2) -> None:
        self.fill(x1, y1, z1, x2, y2, z2, AIR)

    def stair(self, x, y, z, facing, m: Mat, half="bottom", shape="straight") -> None:
        self.put(x, y, z, M(f"{m.stairs}[facing={NAME[facing]},half={half},shape={shape},waterlogged=false]"))

    def slab(self, x, y, z, m: Mat, half="bottom") -> None:
        self.put(x, y, z, M(f"{m.slab}[type={half},waterlogged=false]"))

    def pane(self, x, y, z, kind="glass_pane", axis="x") -> None:
        ew = "true" if axis == "x" else "false"
        ns = "true" if axis == "z" else "false"
        self.put(x, y, z, M(f"{kind}[north={ns},south={ns},east={ew},west={ew},waterlogged=false]"))

    def lantern(self, x, y, z, hanging=False) -> None:
        self.put(x, y, z, M(f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"))

    def door(self, x, y, z, facing, kind="oak_door", hinge="left", open_=False) -> None:
        for half, yy in (("lower", y), ("upper", y + 1)):
            self.put(x, yy, z, M(f"{kind}[facing={NAME[facing]},half={half},hinge={hinge},open={'true' if open_ else 'false'},powered=false]"))

    def wall_banner(self, x, y, z, facing, colour="red") -> None:
        self.put(x, y, z, M(f"{colour}_wall_banner[facing={NAME[facing]}]"))

    # --- ground ----------------------------------------------------------------------------------
    def ground(self, top_fn, under="dirt") -> None:
        """Solid ground below G, top layer from top_fn(x, z)."""
        for x in range(self.SX):
            for z in range(self.SZ):
                for y in range(self.G):
                    self.bp.blocks[(x, y, z)] = M(under)
                self.bp.blocks[(x, self.G, z)] = top_fn(x, z)

    # --- structure -------------------------------------------------------------------------------
    def column(self, x, z, y0, y1, shaft: Mat, base: Mat = None, cap: Mat = None, pillar=None) -> None:
        """Fluted column: shaft in `pillar` (a block name) or the material block, with a stair base and cap."""
        for y in range(y0, y1 + 1):
            self.put(x, y, z, pillar or shaft.block)
        if base:
            self.put(x, y0, z, base.block)
        if cap:
            self.put(x, y1, z, cap.block)

    def box_walls(self, x0, z0, x1, z1, y0, h, wall: Mat, pier: Mat = None, bay=4, glass=None, rows=((2, 3),),
                  glass_axis_skip=(), pane_kind="glass_pane", sill: Mat = None, base_h=0, base: Mat = None) -> None:
        """Four walls of height h from y0 with pier columns at corners and every `bay` blocks, glass between.

        rows = (rel_y_from, rel_y_to) window bands (relative to y0); base/base_h = a plinth course of another material.
        Walls with an index in glass_axis_skip ('n','s','e','w') get no windows.
        """
        pier = pier or wall
        cols = []
        for x in range(x0, x1 + 1):
            cols += [(x, z0, "n", x - x0), (x, z1, "s", x - x0)]
        for z in range(z0 + 1, z1):
            cols += [(x0, z, "w", z - z0), (x1, z, "e", z - z0)]
        for (x, z, face, i) in cols:
            length = (x1 - x0) if face in "ns" else (z1 - z0)
            is_pier = i == 0 or i == length or i % bay == 0
            for dy in range(h):
                y = y0 + dy
                state = (pier if is_pier else wall).block
                if dy < base_h and base:
                    state = base.block
                self.put(x, y, z, state)
            if not is_pier and glass and face not in glass_axis_skip:
                ax = "x" if face in "ns" else "z"
                for (a, b) in rows:
                    for dy in range(a, b + 1):
                        self.pane(x, y0 + dy, z, pane_kind if glass is True else glass, ax)
                    if sill:
                        self.put(x, y0 + a - 1, z, sill.block)

    def gable(self, x0, z0, x1, z1, y, roof: Mat, axis="x", over=1, wall: Mat = None, cap: Mat = None,
              ends="both") -> int:
        """Gable roof: ridge along `axis`, eaves at y, overhang `over` all round. Returns the ridge y.

        The triangular gable ends are filled with `wall`. cap = ridge material (full blocks) laid on a ridge row."""
        if axis == "x":
            a0, a1, b0, b1 = z0 - over, z1 + over, x0, x1
        else:
            a0, a1, b0, b1 = x0 - over, x1 + over, z0, z1
        lo_face, hi_face = ("n", "s") if axis == "x" else ("w", "e")
        i = 0
        top = y
        while a0 + i <= a1 - i:
            yy = y + i
            for b in range(b0 - over, b1 + over + 1):
                if a0 + i == a1 - i:  # single ridge row
                    self._put_ab(axis, a0 + i, b, yy, (cap or roof).block)
                else:
                    self._put_ab(axis, a0 + i, b, yy, None, roof, lo_face)
                    self._put_ab(axis, a1 - i, b, yy, None, roof, hi_face)
                    if cap and a0 + i + 1 == a1 - i:
                        pass
            if wall:
                for a in range(a0 + i + 1, a1 - i):
                    for b in ((b0, b1) if ends == "both" else (b0,) if ends == "lo" else (b1,) if ends == "hi" else ()):
                        self._put_ab(axis, a, b, yy, wall.block)
            top = yy
            i += 1
        return top

    def _put_ab(self, axis, a, b, y, state, roof: Mat = None, face=None):
        x, z = (b, a) if axis == "x" else (a, b)
        if state is not None:
            self.put(x, y, z, state)
        else:
            self.stair(x, y, z, face, roof)

    def hip(self, x0, z0, x1, z1, y, roof: Mat, over=1, cap: Mat = None) -> int:
        """Pyramidal hip roof over a rectangle (a spire when square). Returns the top layer y."""
        xa, xb, za, zb = x0 - over, x1 + over, z0 - over, z1 + over
        k = 0
        while xa + k <= xb - k and za + k <= zb - k:
            ax0, ax1, az0, az1 = xa + k, xb - k, za + k, zb - k
            yy = y + k
            if ax0 == ax1 or az0 == az1:  # ridge line or point
                for x in range(ax0, ax1 + 1):
                    for z in range(az0, az1 + 1):
                        self.put(x, yy, z, (cap or roof).block)
                return yy
            self.fill(ax0 + 1, yy, az0 + 1, ax1 - 1, yy, az1 - 1, roof.block)
            for x in range(ax0 + 1, ax1):
                self.stair(x, yy, az0, "n", roof)
                self.stair(x, yy, az1, "s", roof)
            for z in range(az0 + 1, az1):
                self.stair(ax0, yy, z, "w", roof)
                self.stair(ax1, yy, z, "e", roof)
            self.stair(ax0, yy, az0, "n", roof, shape="outer_left")
            self.stair(ax1, yy, az0, "n", roof, shape="outer_right")
            self.stair(ax1, yy, az1, "s", roof, shape="outer_left")
            self.stair(ax0, yy, az1, "s", roof, shape="outer_right")
            k += 1
        return y + k - 1

    def crenels(self, x0, z0, x1, z1, y, m: Mat) -> None:
        """Crenellated parapet ring on layer y (merlons on even steps)."""
        i = 0
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                if (x - x0) % 2 == 0:
                    self.put(x, y, z, m.block)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                if (z - z0) % 2 == 0:
                    self.put(x, y, z, m.block)

    def rim(self, x0, z0, x1, z1, y, state: str) -> None:
        for x in range(x0, x1 + 1):
            self.put(x, y, z0, state)
            self.put(x, y, z1, state)
        for z in range(z0, z1 + 1):
            self.put(x0, y, z, state)
            self.put(x1, y, z, state)

    def lamp(self, x, z, h=3, post="stone_brick_wall", y0=None) -> None:
        y0 = y0 or self.F
        for y in range(y0, y0 + h):
            self.put(x, y, z, post)
        self.lantern(x, y0 + h, z)

    def chandelier(self, x, y_ceil, z, drop=2) -> None:
        """Chain from the ceiling block at y_ceil-1... lantern hangs `drop` below it."""
        for k in range(drop):
            self.put(x, y_ceil - 1 - k, z, M("chain[axis=y,waterlogged=false]"))
        self.lantern(x, y_ceil - 1 - drop, z, hanging=True)

    def tree(self, x, z, h=5, leaf="oak_leaves", log="oak_log", r=2) -> None:
        y0 = self.F
        for y in range(y0, y0 + h):
            self.put(x, y, z, log)
        for dy in range(-1, 3):
            rr = r if dy < 1 else r - 1 if dy == 1 else max(1, r - 2)
            for dx in range(-rr, rr + 1):
                for dz in range(-rr, rr + 1):
                    if abs(dx) == rr and abs(dz) == rr and dy != 0:
                        continue
                    y = y0 + h - 1 + dy
                    if (dx, dz) == (0, 0) and y < y0 + h:
                        continue
                    if self.get(x + dx, y, z + dz) is None:
                        self.put(x + dx, y, z + dz, M(f"{leaf}[persistent=true,distance=1]"))

    def disc(self, cx, y, cz, radius, state, inner=-1) -> None:
        self.bp.disc(cx, y, cz, radius, state if ":" in state else M(state), inner)

    def staircase(self, x, y0, z0, steps, axis="z", direction=1, width=2, m: Mat = None, base_y=None) -> None:
        """Straight stair of `steps` steps rising toward +direction along `axis` (x = across position when
        axis is z, z0 = start along it); the blocks under each step are filled down to base_y."""
        base_y = y0 if base_y is None else base_y
        for s_ in range(steps):
            for w in range(width):
                if axis == "z":
                    xx, zz, face = x + w, z0 + s_ * direction, ("n" if direction == 1 else "s")
                else:
                    xx, zz, face = z0 + s_ * direction, x + w, ("w" if direction == 1 else "e")
                for yy in range(base_y, y0 + s_):
                    self.put(xx, yy, zz, m.block)
                self.stair(xx, y0 + s_, zz, face, m)

    # --- light -----------------------------------------------------------------------------------
    def light(self, plot, name: str, max_rounds=12) -> None:
        """Place lanterns until no spawnable spot inside `plot(x, z)` is dark. Lamp posts out in the open,
        floor lanterns under cover. Works on a copy of the blocks with air filled in."""
        bp = self.bp
        F = self.F
        self.fixed = 0
        for _ in range(max_rounds):
            full = dict(bp.blocks)
            top = {}
            for (x, y, z) in bp.blocks:
                if y > top.get((x, z), -1):
                    top[(x, z)] = y
            cands = []
            for x in range(self.SX):
                for z in range(self.SZ):
                    if not plot(x, z):
                        continue
                    for y in range(F, min(self.SY, top.get((x, z), self.G) + 4)):
                        if (x, y, z) not in full:
                            full[(x, y, z)] = AIR
                            cands.append((x, y, z))
            spots = dark_spots(full, bp.size, cands)
            if not spots:
                print(f"{name}: light fixer added {self.fixed} lanterns")
                return
            placed = []
            for (x, y, z) in spots:
                open_sky = all((x, yy, z) not in bp.blocks for yy in range(y + 1, self.SY))
                gap = 11 if open_sky else 6
                if any(abs(x - a) + abs(y - b) + abs(z - c) <= gap for a, b, c in placed):
                    continue
                if bp.blocks.get((x, y, z)) is not None:
                    continue
                below = bp.blocks[(x, y - 1, z)]
                if y == F and open_sky and below.startswith(("minecraft:grass_block", "minecraft:dirt", "minecraft:stone_bricks", "minecraft:polished", "minecraft:quartz", "minecraft:smooth", "minecraft:calcite", "minecraft:cobbled", "minecraft:gravel", "minecraft:andesite")):
                    self.lamp(x, z, 3)
                else:
                    self.lantern(x, y, z)
                placed.append((x, y, z))
                self.fixed += 1
        raise RuntimeError(f"{name}: could not light every spawnable spot")

    def check_support(self, name: str) -> None:
        """Blocks that pop off without support (lantern, door, plant, wall banner, ladder, torch...)."""
        bad = []
        behind = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}
        bl = self.bp.blocks
        for (x, y, z), s in bl.items():
            n = s.split("[", 1)[0].split(":", 1)[1]
            below = bl.get((x, y - 1, z))
            if n == "lantern":
                need = (x, y + 1, z) if "hanging=true" in s else (x, y - 1, z)
                if need not in bl:
                    bad.append((x, y, z, s))
            elif n.endswith("wall_banner") or n == "ladder":
                face = s.split("facing=", 1)[1].split(",", 1)[0].rstrip("]")
                dx, dz = behind[face]
                if (x + dx, y, z + dz) not in bl:
                    bad.append((x, y, z, s))
            elif n.endswith("_door") and "half=lower" in s:
                if below is None:
                    bad.append((x, y, z, s))
            elif n in ("short_grass", "poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet", "red_tulip",
                       "pink_tulip", "allium", "lily_of_the_valley", "rose_bush", "peony", "lilac", "fern") or n.endswith("carpet") or n.endswith("pressure_plate"):
                if "half=upper" not in s and below is None:
                    bad.append((x, y, z, s))
            elif n == "chain" and (x, y + 1, z) not in bl and (x, y - 1, z) not in bl:
                bad.append((x, y, z, s))
        if bad:
            raise RuntimeError(f"{name}: {len(bad)} unsupported blocks, e.g. {bad[:6]}")
