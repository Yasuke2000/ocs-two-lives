"""Blueprints: builds written as code, saved as vanilla structure files, previewed as PNG. Stdlib only.

A blueprint file (blueprints/<name>.py) defines `build(bp)`; tools/build_structures.py runs it, writes
pack/kubejs/data/ttl/structure/<name>.nbt (placed in game with `/ttl build <name>`) and previews in
docs/previews/<name>-iso.png and -top.png.

Coordinates are relative to the structure's corner (0, 0, 0); y is up. Block states use the command
syntax: "minecraft:quartz_stairs[facing=north,half=top]".
"""
import math
import re
import struct
import zlib
from pathlib import Path

DATA_VERSION = 3955  # Minecraft 1.21.1
AIR = "minecraft:air"
_STATE = re.compile(r"^([a-z0-9_.-]+:[a-z0-9_/.-]+)(?:\[(.*)\])?$")


def parse_state(state: str) -> tuple[str, dict]:
    m = _STATE.match(state)
    if not m:
        raise ValueError(f"bad block state: {state}")
    props = {}
    if m.group(2):
        for pair in m.group(2).split(","):
            key, value = pair.split("=")
            props[key.strip()] = value.strip()
    return m.group(1), props


def from_schem(name: str, path: Path) -> "Blueprint":
    """Load a WorldEdit Sponge schematic (v2 or v3, what `//schem save` writes) as a Blueprint.

    Air is kept, so placing the build also clears what was removed in game. Block entity contents
    (chest items, sign text) are not carried over.
    """
    import nbt
    root = nbt.read_gzip(path)
    schem = root.get("Schematic", root)  # v3 nests everything under "Schematic"
    w, h, l = schem["Width"], schem["Height"], schem["Length"]
    blocks = schem.get("Blocks", schem)  # v3: Blocks{Palette, Data}; v2: Palette + BlockData at the top
    palette = {index: state for state, index in blocks["Palette"].items()}
    data = blocks.get("Data", blocks.get("BlockData"))
    bp = Blueprint(name, (w, h, l))
    i = pos = 0
    while pos < len(data):  # varint-encoded palette indexes, x fastest, then z, then y
        value = shift = 0
        while True:
            byte = data[pos]
            pos += 1
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                break
            shift += 7
        x, z, y = i % w, (i // w) % l, i // (w * l)
        bp.blocks[(x, y, z)] = palette[value]
        i += 1
    return bp


class Blueprint:
    def __init__(self, name: str, size: tuple[int, int, int]):
        self.name = name
        self.size = size
        self.blocks: dict[tuple[int, int, int], str] = {}

    # --- building -------------------------------------------------------------------------------
    def set(self, x: int, y: int, z: int, state: str) -> None:
        sx, sy, sz = self.size
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"{self.name}: ({x},{y},{z}) outside size {self.size}")
        parse_state(state)
        self.blocks[(x, y, z)] = state

    def fill(self, x1, y1, z1, x2, y2, z2, state: str) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.set(x, y, z, state)

    def box(self, x1, y1, z1, x2, y2, z2, state: str) -> None:
        """Hollow box: only the outer shell."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    if x in (x1, x2) or y in (y1, y2) or z in (z1, z2):
                        self.set(x, y, z, state)

    def disc(self, cx: float, y: int, cz: float, radius: float, state: str, inner: float = -1) -> None:
        """Filled circle (or ring when `inner` >= 0) on layer y, centred on (cx, cz)."""
        for x in range(math.floor(cx - radius), math.ceil(cx + radius) + 1):
            for z in range(math.floor(cz - radius), math.ceil(cz + radius) + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= radius + 0.25 and d > inner + 0.25:
                    self.set(x, y, z, state)

    def pillar(self, x: int, z: int, y1: int, y2: int, state: str) -> None:
        self.fill(x, y1, z, x, y2, z, state)

    def around(self, cx: float, cz: float, radius: float, count: int, start_deg: float = 0):
        """Yield `count` integer (x, z) points evenly on a circle (for pillars, pedestals, lights)."""
        for i in range(count):
            a = math.radians(start_deg + 360.0 * i / count)
            yield round(cx + radius * math.cos(a)), round(cz + radius * math.sin(a))

    # --- output -----------------------------------------------------------------------------------
    def to_structure(self) -> dict:
        palette: list[dict] = []
        index: dict[str, int] = {}
        blocks = []
        for pos in sorted(self.blocks, key=lambda p: (p[1], p[2], p[0])):
            state = self.blocks[pos]
            if state not in index:
                name, props = parse_state(state)
                entry = {"Name": name}
                if props:
                    entry["Properties"] = props
                index[state] = len(palette)
                palette.append(entry)
            blocks.append({"pos": list(pos), "state": index[state]})
        return {"DataVersion": DATA_VERSION, "size": list(self.size), "palette": palette,
                "blocks": blocks, "entities": []}

    def render(self, iso_path: Path, top_path: Path) -> None:
        solid = {p: s for p, s in self.blocks.items() if parse_state(s)[0] not in (AIR, "minecraft:barrier", "minecraft:structure_void")}
        _render_iso(solid, iso_path)
        _render_top(solid, self.size, top_path)


# --- preview rendering (no image library: raw RGBA buffer + a tiny PNG writer) ------------------------

_COLORS = [
    ("sea_lantern", (172, 214, 200)), ("glowstone", (230, 200, 120)), ("lantern", (240, 190, 90)),
    ("end_rod", (245, 240, 225)), ("amethyst", (150, 100, 200)), ("calcite", (225, 225, 220)),
    ("quartz", (236, 230, 223)), ("purpur", (170, 125, 170)), ("prismarine", (90, 160, 150)),
    ("deepslate", (75, 75, 82)), ("blackstone", (45, 40, 48)), ("obsidian", (30, 22, 45)),
    ("crying_obsidian", (70, 30, 120)), ("glass", (200, 225, 235)), ("gold", (240, 205, 70)),
    ("emerald", (60, 200, 110)), ("diamond", (110, 220, 220)), ("copper", (190, 110, 80)),
    ("oak", (170, 135, 85)), ("spruce", (110, 80, 50)), ("dark_oak", (70, 50, 30)), ("birch", (215, 200, 150)),
    ("grass", (100, 160, 70)), ("moss", (90, 130, 50)), ("dirt", (130, 95, 65)), ("sand", (220, 205, 160)),
    ("snow", (245, 250, 250)), ("water", (60, 100, 200)), ("lava", (230, 110, 30)), ("soul", (80, 200, 215)),
    ("bookshelf", (140, 100, 60)), ("brick", (150, 75, 60)), ("stone", (125, 125, 125)), ("cobble", (115, 115, 115)),
    ("andesite", (135, 135, 135)), ("tuff", (100, 100, 90)), ("wool", (220, 220, 220)), ("leaves", (60, 120, 50)),
    ("log", (110, 85, 55)), ("planks", (165, 130, 85)),
]


def _color(state: str) -> tuple[int, int, int]:
    name = parse_state(state)[0].split(":", 1)[1]
    for key, rgb in _COLORS:
        if key in name:
            return rgb
    h = zlib.crc32(name.encode())
    return (90 + h % 120, 90 + (h >> 8) % 120, 90 + (h >> 16) % 120)


def _shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def _inside(px, py, poly):
    inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


# 16x16 cube sprite: which pixel belongs to the top (0), +z/left (1) or +x/right (2) face.
_TOP = [(8, 0), (16, 4), (8, 8), (0, 4)]
_LEFT = [(0, 4), (8, 8), (8, 16), (0, 12)]
_RIGHT = [(8, 8), (16, 4), (16, 12), (8, 16)]
_SPRITE = []
for _py in range(16):
    for _px in range(16):
        cx, cy = _px + 0.5, _py + 0.5
        face = 0 if _inside(cx, cy, _TOP) else 1 if _inside(cx, cy, _LEFT) else 2 if _inside(cx, cy, _RIGHT) else -1
        if face >= 0:
            _SPRITE.append((_px, _py, face))


def _render_iso(blocks: dict, path: Path) -> None:
    if not blocks:
        return
    def screen(p):
        x, y, z = p
        return (x - z) * 8, (x + z) * 4 - y * 8
    xs, ys = zip(*(screen(p) for p in blocks))
    ox, oy = -min(xs) + 4, -min(ys) + 4
    w, h = max(xs) - min(xs) + 24, max(ys) - min(ys) + 24
    buf = bytearray(w * h * 4)
    for p in sorted(blocks, key=lambda q: (q[0] + q[2], q[1], q[0])):
        x, y, z = p
        if (x, y + 1, z) in blocks and (x + 1, y, z) in blocks and (x, y, z + 1) in blocks:
            continue  # fully hidden
        base = _color(blocks[p])
        faces = (_shade(base, 1.0), _shade(base, 0.78), _shade(base, 0.62))
        sx, sy = screen(p)
        for px, py, face in _SPRITE:
            X, Y = sx + ox + px, sy + oy + py
            i = (Y * w + X) * 4
            buf[i:i + 4] = bytes(faces[face]) + b"\xff"
    _write_png(path, w, h, buf)


def _render_top(blocks: dict, size, path: Path, scale: int = 8) -> None:
    sx, sy, sz = size
    top: dict[tuple[int, int], tuple[int, str]] = {}
    for (x, y, z), state in blocks.items():
        if (x, z) not in top or y > top[(x, z)][0]:
            top[(x, z)] = (y, state)
    w, h = sx * scale, sz * scale
    buf = bytearray(w * h * 4)
    for (x, z), (y, state) in top.items():
        rgb = _shade(_color(state), 0.65 + 0.35 * (y + 1) / max(1, sy))
        for dz in range(scale):
            row = ((z * scale + dz) * w + x * scale) * 4
            buf[row:row + scale * 4] = (bytes(rgb) + b"\xff") * scale
    _write_png(path, w, h, buf)


def _write_png(path: Path, w: int, h: int, rgba: bytearray) -> None:
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
