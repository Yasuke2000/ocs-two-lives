"""Build programs: the small JSON language Claude writes instead of block lists (stdlib only).

A program is a dict (or a JSON file):

    {"name": "goblin_hut", "size": [9, 8, 7],
     "palette": {"wall": "minecraft:spruce_planks", "roof": "minecraft:dark_oak_stairs"},
     "ops": [{"op": "fill", "from": [0, 0, 0], "to": [8, 0, 6], "block": "minecraft:cobblestone"},
             {"op": "walls", "from": [0, 1, 0], "to": [8, 4, 6], "block": "$wall"},
             {"op": "roof", "from": [-1, 5, -1], "to": [9, 5, 7], "style": "gable", "axis": "x", "stairs": "$roof"}]}

Coordinates are relative to the build's corner (0, 0, 0), y up, inside `size`. Ops run in order; a later op overwrites
an earlier one. Cells no op touches are kept as they are in the world ("keep"), unless "clear": true makes them air.
`compile_program` returns a tools/blueprint.py Blueprint (so previews, .nbt and .schem export are shared with the
canon builds) plus the per-op warnings. The op reference is OPS below and docs/dev/build-bridge.md.
"""
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from blueprint import AIR, Blueprint, from_schem, from_structure, parse_state  # noqa: E402

STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
BLUEPRINTS = ROOT / "blueprints"

OPS = {
    "set": "at, block: one block",
    "fill": "from, to, block: solid box",
    "clear": "from, to: air box (removes what is in the world there)",
    "hollow_box": "from, to, block[, open: ['top'|'bottom'...]]: shell with floor and ceiling",
    "walls": "from, to, block: the four vertical sides only",
    "replace": "from, to, match, block: change cells this program already set to `match` (id or full state)",
    "cylinder": "center [x, z], y [y1, y2], radius, block[, hollow, axis 'y']: vertical cylinder (tower, well)",
    "sphere": "center [x, y, z], radius, block[, hollow, half 'upper'|'lower']: ball or dome",
    "line": "from, to, block: 3-D line (beams, rails, ropes)",
    "path": "points [[x, z], ...], y, width, block: flat path along a polyline",
    "roof": "from [x1, y, z1], to [x2, _, z2], style gable|hip|flat|shed, stairs[, axis x|z, fill, ridge, slab]: roof on top of a footprint",
    "window_grid": "from, to (a flat wall face), block[, spacing 3, width 1, height 2, bottom 1, margin 1]: windows cut into a wall",
    "door": "at, facing, block[, hinge]: two-block door (lower + upper half)",
    "scatter": "from, to, block, density[, seed, on]: random cells (only where nothing is set, or on top of `on`)",
    "stamp": "structure (pack structure name | blueprint name | path .nbt/.schem), at[, rotate 0|90|180|270, mirror]: paste a saved build",
}

_HORIZONTAL = ["north", "east", "south", "west"]  # clockwise


class ProgramError(ValueError):
    pass


def load(source) -> dict:
    """A program from a dict, a JSON string or a path to a .json file."""
    if isinstance(source, dict):
        return source
    if isinstance(source, Path) or (isinstance(source, str) and source.strip().endswith(".json") and "\n" not in source):
        return json.loads(Path(source).read_text(encoding="utf-8"))
    return json.loads(source)


def split_nbt(state: str) -> tuple[str, str | None]:
    """'ns:id[props]{snbt}' -> ('ns:id[props]', '{snbt}'); block-entity data travels apart from the state."""
    i = state.find("{")
    return (state, None) if i < 0 else (state[:i], state[i:])


def with_props(state: str, **props) -> str:
    """`state` with these properties set (added or replaced); block-entity NBT is kept."""
    state, snbt = split_nbt(state)
    name, current = parse_state(state)
    current.update({k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in props.items()})
    return name + ("[" + ",".join(f"{k}={v}" for k, v in current.items()) + "]" if current else "") + (snbt or "")


def rotate_state(state: str, quarter_turns: int, mirror: bool = False) -> str:
    """Rotate facing/axis/rotation properties clockwise (seen from above) by 90° steps; mirror flips x first."""
    state, snbt = split_nbt(state)
    if snbt:
        return rotate_state(state, quarter_turns, mirror) + snbt
    name, props = parse_state(state)
    turns = quarter_turns % 4
    if not props or (turns == 0 and not mirror):
        return state
    out = dict(props)
    if "facing" in props and props["facing"] in _HORIZONTAL:
        f = props["facing"]
        if mirror and f in ("east", "west"):
            f = "west" if f == "east" else "east"
        out["facing"] = _HORIZONTAL[(_HORIZONTAL.index(f) + turns) % 4]
    if "axis" in props and props["axis"] in ("x", "z") and turns % 2 == 1:
        out["axis"] = "z" if props["axis"] == "x" else "x"
    if "rotation" in props:
        r = int(props["rotation"])
        if mirror:
            r = (16 - r) % 16
        out["rotation"] = str((r + 4 * turns) % 16)
    if mirror and "hinge" in props:
        out["hinge"] = "right" if props["hinge"] == "left" else "left"
    sides = {s: props[s] for s in _HORIZONTAL if s in props}  # fences, walls, panes, vines
    if sides:
        for s, v in sides.items():
            t = s
            if mirror and t in ("east", "west"):
                t = "west" if t == "east" else "east"
            out[_HORIZONTAL[(_HORIZONTAL.index(t) + turns) % 4]] = v
    return name + "[" + ",".join(f"{k}={v}" for k, v in out.items()) + "]"


class Compiler:
    def __init__(self, program: dict):
        self.p = program
        try:
            self.size = tuple(int(v) for v in program["size"])
        except (KeyError, TypeError, ValueError):
            raise ProgramError("program needs size: [width_x, height_y, length_z]")
        if len(self.size) != 3 or min(self.size) < 1:
            raise ProgramError("size must be three positive integers")
        if self.size[0] * self.size[1] * self.size[2] > 8_000_000:
            raise ProgramError(f"size {self.size} is over 8,000,000 cells; split the build")
        self.bp = Blueprint(str(program.get("name", "program")), self.size)
        self.bp.nbt = {}  # (x, y, z) -> block-entity SNBT ("{Items:[...]}"); placed by the bridge, not in .nbt/.schem
        self.aliases = {k.lstrip("$"): v for k, v in (program.get("palette") or {}).items()}
        self.warnings: list[str] = []
        self.outside = 0

    # --- helpers ----------------------------------------------------------------------------------------------------
    def block(self, value, where: str) -> str:
        if not isinstance(value, str) or not value:
            raise ProgramError(f"{where}: block missing")
        depth = 0
        while value.startswith("$"):
            key = value[1:]
            if key not in self.aliases:
                raise ProgramError(f"{where}: unknown palette alias {value}")
            value = self.aliases[key]
            depth += 1
            if depth > 8:
                raise ProgramError(f"{where}: palette alias loop at {value}")
        if ":" not in value.split("[")[0].split("{")[0]:
            value = "minecraft:" + value
        base, snbt = split_nbt(value)
        try:
            parse_state(base)
        except ValueError:
            raise ProgramError(f"{where}: bad block state {value!r} (use ns:id[prop=value,...] or ns:id[...]{{snbt}})")
        if snbt is not None and (not snbt.endswith("}") or snbt.count("{") != snbt.count("}")):
            raise ProgramError(f"{where}: unbalanced block-entity NBT in {value!r}")
        return value

    def put(self, x, y, z, state):
        sx, sy, sz = self.size
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            base, snbt = split_nbt(state)
            self.bp.blocks[(x, y, z)] = base
            if snbt:
                self.bp.nbt[(x, y, z)] = snbt
            else:
                self.bp.nbt.pop((x, y, z), None)
        else:
            self.outside += 1

    @staticmethod
    def vec(op, key, n=3, where=""):
        v = op.get(key)
        if not isinstance(v, (list, tuple)) or len(v) != n:
            raise ProgramError(f"{where}: {key} must be [{', '.join('xyz'[:n] if n == 3 else 'xz')}]")
        return [int(round(c)) for c in v]

    @staticmethod
    def span(a, b):
        return range(min(a, b), max(a, b) + 1)

    # --- ops --------------------------------------------------------------------------------------------------------
    def run(self):
        ops = self.p.get("ops")
        if not isinstance(ops, list) or not ops:
            raise ProgramError("program needs a non-empty ops list")
        for i, op in enumerate(ops):
            kind = op.get("op") if isinstance(op, dict) else None
            where = f"ops[{i}] {kind}"
            fn = getattr(self, "op_" + str(kind), None)
            if kind not in OPS or fn is None:
                raise ProgramError(f"{where}: unknown op (known: {', '.join(OPS)})")
            before = self.outside
            fn(op, where)
            if self.outside > before:
                self.warnings.append(f"{where}: {self.outside - before} cells fell outside size {list(self.size)} and were dropped")
        if self.p.get("clear"):
            sx, sy, sz = self.size
            for x in range(sx):
                for y in range(sy):
                    for z in range(sz):
                        self.bp.blocks.setdefault((x, y, z), AIR)
        return self.bp

    def op_set(self, op, where):
        x, y, z = self.vec(op, "at", where=where)
        self.put(x, y, z, self.block(op.get("block"), where))

    def op_fill(self, op, where, state=None):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = state or self.block(op.get("block"), where)
        for x in self.span(a[0], b[0]):
            for y in self.span(a[1], b[1]):
                for z in self.span(a[2], b[2]):
                    self.put(x, y, z, state)

    def op_clear(self, op, where):
        self.op_fill(op, where, AIR)

    def op_hollow_box(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = self.block(op.get("block"), where)
        open_sides = set(op.get("open") or [])
        x1, x2, y1, y2, z1, z2 = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), min(a[2], b[2]), max(a[2], b[2])
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for z in range(z1, z2 + 1):
                    shell = x in (x1, x2) or z in (z1, z2) or (y == y1 and "bottom" not in open_sides) or (y == y2 and "top" not in open_sides)
                    if shell:
                        self.put(x, y, z, state)

    def op_walls(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = self.block(op.get("block"), where)
        x1, x2, z1, z2 = min(a[0], b[0]), max(a[0], b[0]), min(a[2], b[2]), max(a[2], b[2])
        for y in self.span(a[1], b[1]):
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        self.put(x, y, z, state)

    def op_replace(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        match = self.block(op.get("match"), where)
        state = self.block(op.get("block"), where)
        exact = "[" in match
        for pos, current in list(self.bp.blocks.items()):
            x, y, z = pos
            if min(a[0], b[0]) <= x <= max(a[0], b[0]) and min(a[1], b[1]) <= y <= max(a[1], b[1]) and min(a[2], b[2]) <= z <= max(a[2], b[2]):
                if (current == match) if exact else (parse_state(current)[0] == match):
                    self.bp.blocks[pos] = state

    def op_cylinder(self, op, where):
        cx, cz = op.get("center", [None, None])[:2]
        if cx is None:
            raise ProgramError(f"{where}: center must be [x, z]")
        y1, y2 = self.vec(op, "y", n=2, where=where)
        r = float(op.get("radius", 0))
        if r <= 0:
            raise ProgramError(f"{where}: radius must be > 0")
        state = self.block(op.get("block"), where)
        hollow = bool(op.get("hollow"))
        for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
            for z in range(math.floor(cz - r), math.ceil(cz + r) + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.25 and (not hollow or d > r - 0.75):
                    for y in self.span(y1, y2):
                        self.put(x, y, z, state)

    def op_sphere(self, op, where):
        c = op.get("center")
        if not isinstance(c, list) or len(c) != 3:
            raise ProgramError(f"{where}: center must be [x, y, z]")
        r = float(op.get("radius", 0))
        if r <= 0:
            raise ProgramError(f"{where}: radius must be > 0")
        state = self.block(op.get("block"), where)
        hollow, half = bool(op.get("hollow")), op.get("half")
        for x in range(math.floor(c[0] - r), math.ceil(c[0] + r) + 1):
            for y in range(math.floor(c[1] - r), math.ceil(c[1] + r) + 1):
                if half == "upper" and y < c[1] or half == "lower" and y > c[1]:
                    continue
                for z in range(math.floor(c[2] - r), math.ceil(c[2] + r) + 1):
                    d = math.dist((x, y, z), c)
                    if d <= r + 0.25 and (not hollow or d > r - 0.85):
                        self.put(x, y, z, state)

    def op_line(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = self.block(op.get("block"), where)
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), abs(b[2] - a[2]))
        for i in range(n + 1):
            t = i / n if n else 0
            self.put(round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t), state)

    def op_path(self, op, where):
        pts = op.get("points") or []
        if len(pts) < 2:
            raise ProgramError(f"{where}: points needs at least two [x, z]")
        y = int(op.get("y", 0))
        half = max(0.5, float(op.get("width", 3)) / 2)
        state = self.block(op.get("block"), where)
        xs = [p[0] for p in pts]
        zs = [p[1] for p in pts]
        for x in range(math.floor(min(xs) - half), math.ceil(max(xs) + half) + 1):
            for z in range(math.floor(min(zs) - half), math.ceil(max(zs) + half) + 1):
                for (ax, az), (bx, bz) in zip(pts, pts[1:]):
                    dx, dz = bx - ax, bz - az
                    t = 0 if dx == dz == 0 else max(0, min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
                    if math.hypot(x - (ax + t * dx), z - (az + t * dz)) <= half - 0.25:
                        self.put(x, y, z, state)
                        break

    def op_roof(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        y0 = a[1]
        x1, x2, z1, z2 = min(a[0], b[0]), max(a[0], b[0]), min(a[2], b[2]), max(a[2], b[2])
        style = op.get("style", "gable")
        if style == "flat":
            self.op_fill({"from": [x1, y0, z1], "to": [x2, y0, z2]}, where, self.block(op.get("block") or op.get("slab") or op.get("stairs"), where))
            return
        stairs = self.block(op.get("stairs"), where)
        if not parse_state(stairs)[0].endswith("_stairs"):
            self.warnings.append(f"{where}: stairs {stairs} is not a *_stairs block")
        fill = self.block(op["fill"], where) if op.get("fill") else None
        ridge = self.block(op["ridge"], where) if op.get("ridge") else None
        axis = op.get("axis") or ("x" if (x2 - x1) >= (z2 - z1) else "z")

        def st(facing):
            return with_props(stairs, facing=facing, half="bottom")

        if style == "shed":  # one slope rising toward +z (axis x) or +x (axis z)
            n = (z2 - z1) if axis == "x" else (x2 - x1)
            for k in range(n + 1):
                for t in (range(x1, x2 + 1) if axis == "x" else range(z1, z2 + 1)):
                    if axis == "x":
                        self.put(t, y0 + k, z1 + k, st("south"))
                    else:
                        self.put(x1 + k, y0 + k, t, st("east"))
            return
        if style == "gable":
            if axis == "x":
                k = 0
                while z1 + k <= z2 - k:
                    y = y0 + k
                    for x in range(x1, x2 + 1):
                        if z1 + k == z2 - k:
                            self.put(x, y, z1 + k, ridge or fill or with_props(stairs.split("[")[0].replace("_stairs", "_slab"), type="bottom"))
                        else:
                            self.put(x, y, z1 + k, st("south"))
                            self.put(x, y, z2 - k, st("north"))
                    if fill and k > 0:  # gable ends: the triangle under this layer, one in from the eaves
                        for z in range(z1 + k, z2 - k + 1):
                            for x in (x1 + 1, x2 - 1):
                                self.put(x, y - 1, z, fill)
                    k += 1
            else:
                k = 0
                while x1 + k <= x2 - k:
                    y = y0 + k
                    for z in range(z1, z2 + 1):
                        if x1 + k == x2 - k:
                            self.put(x1 + k, y, z, ridge or fill or with_props(stairs.split("[")[0].replace("_stairs", "_slab"), type="bottom"))
                        else:
                            self.put(x1 + k, y, z, st("east"))
                            self.put(x2 - k, y, z, st("west"))
                    if fill and k > 0:
                        for x in range(x1 + k, x2 - k + 1):
                            for z in (z1 + 1, z2 - 1):
                                self.put(x, y - 1, z, fill)
                    k += 1
            return
        if style == "hip":
            k = 0
            while x1 + k <= x2 - k and z1 + k <= z2 - k:
                y = y0 + k
                ax, bx, az, bz = x1 + k, x2 - k, z1 + k, z2 - k
                if ax == bx or az == bz:
                    for x in range(ax, bx + 1):
                        for z in range(az, bz + 1):
                            self.put(x, y, z, ridge or fill or with_props(stairs.split("[")[0].replace("_stairs", "_slab"), type="bottom"))
                    break
                for x in range(ax, bx + 1):
                    self.put(x, y, az, st("south"))
                    self.put(x, y, bz, st("north"))
                for z in range(az + 1, bz):
                    self.put(ax, y, z, st("east"))
                    self.put(bx, y, z, st("west"))
                if fill:
                    for x in range(ax + 1, bx):
                        for z in range(az + 1, bz):
                            self.put(x, y, z, fill)
                k += 1
            return
        raise ProgramError(f"{where}: style must be gable, hip, shed or flat")

    def op_window_grid(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = self.block(op.get("block"), where)
        spacing, width, height = int(op.get("spacing", 3)), int(op.get("width", 1)), int(op.get("height", 2))
        bottom, margin = int(op.get("bottom", 1)), int(op.get("margin", 1))
        x1, x2, y1, y2, z1, z2 = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), min(a[2], b[2]), max(a[2], b[2])
        if x1 != x2 and z1 != z2:
            raise ProgramError(f"{where}: from/to must be a flat wall (same x or same z)")
        along = range(x1, x2 + 1) if x1 != x2 else range(z1, z2 + 1)
        start = along.start + margin
        stop = along.stop - margin
        t = start
        while t + width <= stop:
            for dt in range(width):
                for dy in range(height):
                    y = y1 + bottom + dy
                    if y > y2:
                        continue
                    if x1 != x2:
                        self.put(t + dt, y, z1, state)
                    else:
                        self.put(x1, y, t + dt, state)
            t += width + spacing

    def op_door(self, op, where):
        x, y, z = self.vec(op, "at", where=where)
        state = self.block(op.get("block", "minecraft:oak_door"), where)
        facing = op.get("facing", "north")
        hinge = op.get("hinge", "left")
        self.put(x, y, z, with_props(state, facing=facing, half="lower", hinge=hinge, open="false"))
        self.put(x, y + 1, z, with_props(state, facing=facing, half="upper", hinge=hinge, open="false"))

    def op_scatter(self, op, where):
        a, b = self.vec(op, "from", where=where), self.vec(op, "to", where=where)
        state = self.block(op.get("block"), where)
        density = float(op.get("density", 0.1))
        rng = random.Random(op.get("seed", 1))
        on = self.block(op["on"], where) if op.get("on") else None
        on_id = parse_state(on)[0] if on else None
        for x in self.span(a[0], b[0]):
            for z in self.span(a[2], b[2]):
                for y in self.span(a[1], b[1]):
                    if rng.random() >= density:
                        continue
                    if on_id:
                        below = self.bp.blocks.get((x, y - 1, z))
                        if not below or parse_state(below)[0] != on_id or (x, y, z) in self.bp.blocks:
                            continue
                    elif (x, y, z) in self.bp.blocks:
                        continue
                    self.put(x, y, z, state)

    def op_stamp(self, op, where):
        ref = op.get("structure")
        if not ref:
            raise ProgramError(f"{where}: structure missing")
        src = load_structure(str(ref))
        ox, oy, oz = self.vec(op, "at", where=where)
        turns = (int(op.get("rotate", 0)) // 90) % 4
        mirror = bool(op.get("mirror"))
        for (x, y, z), state in src.blocks.items():
            w, l = src.size[0], src.size[2]
            if mirror:
                x = w - 1 - x
            for _ in range(turns):  # clockwise seen from above: (x, z) in w x l -> (l - 1 - z, x) in l x w
                x, z, w, l = l - 1 - z, x, l, w
            self.put(ox + x, oy + y, oz + z, rotate_state(state, turns, mirror))


def load_structure(ref: str) -> Blueprint:
    """A saved build by name: a pack structure (pack/kubejs/data/ttl/structure/<ref>.nbt), a blueprint
    (blueprints/<ref>.py), or a path to a .nbt / .schem file."""
    path = Path(ref)
    if path.suffix in (".nbt", ".schem") and path.exists():
        return from_schem(path.stem, path) if path.suffix == ".schem" else from_structure(path.stem, path)
    if re.fullmatch(r"[a-z0-9_]+", ref):
        nbt_path = STRUCTURES / f"{ref}.nbt"
        if nbt_path.exists():
            return from_structure(ref, nbt_path)
        bp_path = BLUEPRINTS / f"{ref}.py"
        if bp_path.exists():
            import build_structures  # noqa: E402  (tools/ is on sys.path)
            return build_structures.load(bp_path)
    raise ProgramError(f"structure {ref!r} not found (pack structure name, blueprint name, or a .nbt/.schem path)")


def compile_program(source) -> tuple[Blueprint, list[str]]:
    program = load(source)
    c = Compiler(program)
    bp = c.run()
    return bp, c.warnings
