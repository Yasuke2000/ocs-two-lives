#!/usr/bin/env python3
"""Paint layers for the own world: hand-painted height, ruggedness and biome on top of world/map.svg (stdlib only).

    python -I tools/world/paint.py template          make world/paint/ (neutral layers, legend, reference images)
    python -I tools/world/paint.py status            what the paint changes (pixels, height range, biomes, bad colours)
    python -I tools/world/paint.py blob height X Z RADIUS DELTA      soft round brush, by script (Claude, tests)
    python -I tools/world/paint.py blob rugged X Z RADIUS DELTA      DELTA -1..1
    python -I tools/world/paint.py disc biome  X Z RADIUS BIOME_ID   hard round brush
    python -I tools/world/paint.py ridge height X1 Z1 X2 Z2 WIDTH DELTA   soft brush along a line (a mountain chain)

The SVG keeps the geography (coast, lakes, rivers, regions, sites, roads); the paint shapes what is between them.
tools/world/svg2rasters.py applies the paint right after the relief and BEFORE lakes, rivers, sites and roads, so
every site plate stays flat and dry and every road graded whatever is painted. Paint only acts on land.

Layers in world/paint/ (any editor: Krita, GIMP, Photoshop; same size as the template, never resized):
  height.png   8-bit grey. 128 = no change; each step = 2 blocks (0 = -256, 255 = +254). Paint lighter to raise.
  rugged.png   8-bit grey. 128 = no change; (v - 128) / 127 is added to the ruggedness 0..1 (flat < 0.10 < rolling
               < 0.45 < hills < 0.75 < alpine).
  biome.png    RGB. Black = no change; a colour from legend.json (legend.png shows them) sets that biome. Use a hard
               pencil (no anti-aliasing): a colour further than 24 from every legend colour is ignored and reported.
  frame.json   where the layers sit in the world (x0, z0, blocks per pixel, size). Written by `template`; the map may
               grow or move later, the paint stays in world coordinates.
Reference images (world/paint/reference/, not committed): base.png (the current rasters, hillshade + biomes) and
overlay.png (transparent; sites, roads, coast) to put on top while painting.
"""
import json
import math
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pngcodec  # noqa: E402

ROOT = HERE.parent.parent
PAINT = ROOT / "world" / "paint"
BUILD = ROOT / "world" / "build"
BIOMES_TXT = HERE / "biomes.txt"
NEUTRAL = 128
HEIGHT_STEP = 2.0
COLOUR_TOLERANCE = 24

# Distinct, saturated, not black; the first ones go to the biomes painters use most.
_PALETTE = [
    (255, 0, 0), (0, 200, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 128, 0),
    (128, 0, 255), (0, 128, 64), (255, 128, 192), (128, 64, 0), (128, 128, 255), (192, 192, 192), (64, 128, 0),
    (255, 192, 128), (0, 64, 128), (192, 0, 64), (128, 255, 128), (64, 0, 128), (255, 255, 160), (0, 160, 160),
    (160, 80, 160), (96, 96, 96), (224, 96, 64), (64, 224, 160), (160, 224, 0), (96, 32, 32), (32, 96, 224),
    (224, 224, 255), (160, 128, 64), (0, 255, 128), (255, 64, 128), (128, 0, 0), (0, 128, 0), (0, 0, 128),
    (128, 128, 0), (128, 0, 128), (0, 128, 128), (255, 224, 32), (32, 32, 255),
]


def allowed_biomes():
    out = []
    for line in BIOMES_TXT.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line and line not in out:
            out.append(line)
    return out


def make_legend(biomes):
    legend = {}
    for k, b in enumerate(biomes):
        if k < len(_PALETTE):
            legend[b] = list(_PALETTE[k])
        else:
            h = zlib.crc32(b.encode())
            legend[b] = [40 + h % 200, 40 + (h >> 8) % 200, 40 + (h >> 16) % 200]
    return legend


# ------------------------------------------------------------------------------------------------------------- PNG I/O

def write_rgba(path, w, h, rgba):
    raw = b"".join(b"\x00" + bytes(rgba[j * w * 4:(j + 1) * w * 4]) for j in range(h))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png)


def _read_any(path):
    """(w, h, channels, samples) for grey/palette/RGB/RGBA 8-bit PNGs (editors save in any of these)."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, pal = 8, b"", None
    w = h = depth = ctype = None
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos:pos + 4])
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            if inter:
                raise ValueError(f"{path}: interlaced PNG, save without interlacing")
        elif kind == b"PLTE":
            pal = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"IDAT":
            idat += body
    if depth not in (8, 16):
        raise ValueError(f"{path}: {depth}-bit PNG, save as 8-bit")
    spp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = spp * depth // 8
    stride = w * bpp
    raw = zlib.decompress(idat)
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for j in range(h):
        f = raw[p]
        row = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                row[i] = (row[i] + a) & 255
            elif f == 2:
                row[i] = (row[i] + b) & 255
            elif f == 3:
                row[i] = (row[i] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[j * stride:(j + 1) * stride] = row
        prev = row
    if depth == 16:  # keep the high byte
        out = out[0::2]
    if ctype == 3:
        rgb = bytearray()
        for v in out:
            rgb += bytes(pal[v])
        return w, h, 3, rgb
    return w, h, spp, out


def read_grey(path):
    w, h, c, s = _read_any(path)
    if c == 1:
        return w, h, bytes(s)
    if c == 2:
        return w, h, bytes(s[0::2])
    return w, h, bytes(s[0::c])  # RGB(A) painted in grey: take red


def read_rgb(path):
    w, h, c, s = _read_any(path)
    if c == 3:
        return w, h, bytes(s)
    if c == 4:
        out = bytearray(w * h * 3)
        for k in range(w * h):
            if s[k * 4 + 3] >= 128:
                out[k * 3:k * 3 + 3] = s[k * 4:k * 4 + 3]
        return w, h, bytes(out)
    if c == 1:
        return w, h, bytes(v for v in s for _ in range(3))
    raise ValueError(f"{path}: unsupported PNG layout")


# --------------------------------------------------------------------------------------------------------- the layers

class Paint:
    """The paint of world/paint/, sampled by world block position."""

    def __init__(self, folder=PAINT):
        self.folder = Path(folder)
        self.frame = json.loads((self.folder / "frame.json").read_text(encoding="utf-8"))
        self.x0, self.z0 = self.frame["x0"], self.frame["z0"]
        self.px, self.w, self.h = self.frame["px"], self.frame["w"], self.frame["h"]
        self.height = self._grey("height.png")
        self.rugged = self._grey("rugged.png")
        self.biome, self.bad_colours = self._biomes()

    def _grey(self, name):
        path = self.folder / name
        if not path.exists():
            return None
        w, h, data = read_grey(path)
        self._size(name, w, h)
        return data if any(v != NEUTRAL for v in data) else None

    def _size(self, name, w, h):
        if (w, h) != (self.w, self.h):
            raise ValueError(f"world/paint/{name} is {w} x {h}, frame.json says {self.w} x {self.h} (do not resize layers)")

    def _biomes(self):
        path = self.folder / "biome.png"
        legend_path = self.folder / "legend.json"
        if not path.exists() or not legend_path.exists():
            return None, {}
        legend = json.loads(legend_path.read_text(encoding="utf-8"))
        colours = [(tuple(c), b) for b, c in legend.items()]
        w, h, rgb = read_rgb(path)
        self._size("biome.png", w, h)
        names = [None]
        index = {}
        out = bytearray(w * h)
        bad = {}
        cache = {}
        for k in range(w * h):
            c = rgb[k * 3:k * 3 + 3]
            if c == b"\x00\x00\x00":
                continue
            hit = cache.get(c)
            if hit is None:
                best, bd = None, 1e9
                for col, b in colours:
                    d = math.dist(col, c)
                    if d < bd:
                        best, bd = b, d
                hit = best if bd <= COLOUR_TOLERANCE else ""
                cache[c] = hit
            if not hit:
                bad[tuple(c)] = bad.get(tuple(c), 0) + 1
                continue
            if hit not in index:
                index[hit] = len(names)
                names.append(hit)
            out[k] = index[hit]
        self.biome_names = names
        return (bytes(out) if len(names) > 1 else None), bad

    def fingerprint(self):
        """A hash of the layers and the frame: part of the build's source hash."""
        import hashlib
        h = hashlib.sha256(json.dumps(self.frame, sort_keys=True).encode())
        for layer in (self.height, self.rugged, self.biome):
            h.update(layer or b"-")
        h.update("|".join(getattr(self, "biome_names", [None])[1:]).encode())
        return h.hexdigest()

    def empty(self):
        return self.height is None and self.rugged is None and self.biome is None

    def _cell(self, x, z):
        i = int(math.floor((x - self.x0) / self.px))
        j = int(math.floor((z - self.z0) / self.px))
        if 0 <= i < self.w and 0 <= j < self.h:
            return j * self.w + i
        return None

    def height_at(self, x, z):
        """Blocks to add at (x, z) (bilinear, so a 4-block paint pixel gives no steps)."""
        if self.height is None:
            return 0.0
        u = (x - self.x0) / self.px - 0.5
        v = (z - self.z0) / self.px - 0.5
        i0, j0 = int(math.floor(u)), int(math.floor(v))
        tu, tv = u - i0, v - j0

        def at(i, j):
            i = min(max(i, 0), self.w - 1)
            j = min(max(j, 0), self.h - 1)
            return (self.height[j * self.w + i] - NEUTRAL) * HEIGHT_STEP

        top = at(i0, j0) + (at(i0 + 1, j0) - at(i0, j0)) * tu
        bot = at(i0, j0 + 1) + (at(i0 + 1, j0 + 1) - at(i0, j0 + 1)) * tu
        return top + (bot - top) * tv

    def rugged_at(self, x, z):
        if self.rugged is None:
            return 0.0
        g = self._cell(x, z)
        return 0.0 if g is None else (self.rugged[g] - NEUTRAL) / 127.0

    def biome_at(self, x, z):
        if self.biome is None:
            return None
        g = self._cell(x, z)
        return None if g is None or not self.biome[g] else self.biome_names[self.biome[g]]


def load(folder=PAINT):
    """The Paint, or None when world/paint/ has no frame (painting not started)."""
    folder = Path(folder)
    if not (folder / "frame.json").exists():
        return None
    paint = Paint(folder)
    return None if paint.empty() else paint


# ------------------------------------------------------------------------------------------------------------ commands

def template(build=BUILD, folder=PAINT):
    build, folder = Path(build), Path(folder)
    idx_path = build / "index.json"
    if not idx_path.exists():
        raise SystemExit(f"no {idx_path}: run `python -I tools/world/build.py` first")
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    px = idx["pixel"]["blocks"]
    w, h, _, _ = pngcodec.read_png(build / idx["files"]["height"]["file"])
    folder.mkdir(parents=True, exist_ok=True)
    frame_path = folder / "frame.json"
    made = []
    if frame_path.exists():
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        print(f"kept {frame_path.relative_to(ROOT)} (the paint stays where it was painted)")
    else:
        frame = {"x0": idx["box"]["x0"], "z0": idx["box"]["z0"], "px": px, "w": w, "h": h,
                 "note": "Paint layers cover x0..x0+w*px, z0..z0+h*px in world blocks; do not resize the PNGs."}
        frame_path.write_text(json.dumps(frame, indent=1) + "\n", encoding="utf-8")
        made.append(frame_path)
    fw, fh = frame["w"], frame["h"]
    for name in ("height.png", "rugged.png"):
        p = folder / name
        if not p.exists():
            pngcodec.write_png(p, fw, fh, bytes([NEUTRAL]) * (fw * fh))
            made.append(p)
    if not (folder / "biome.png").exists():
        pngcodec.write_png(folder / "biome.png", fw, fh, bytes(fw * fh * 3), rgb=True)
        made.append(folder / "biome.png")
    legend_path = folder / "legend.json"
    if legend_path.exists():
        legend = json.loads(legend_path.read_text(encoding="utf-8"))
        for b, c in make_legend([b for b in allowed_biomes() if b not in legend]).items():
            used = {tuple(v) for v in legend.values()}
            while tuple(c) in used:
                c = [(c[0] + 37) % 256, (c[1] + 91) % 256, (c[2] + 53) % 256]
            legend[b] = c
    else:
        legend = make_legend(allowed_biomes())
        made.append(legend_path)
    legend_path.write_text(json.dumps(legend, indent=1) + "\n", encoding="utf-8")
    _legend_png(legend, folder / "legend.png")
    ref = folder / "reference"
    _reference(build, idx, frame, ref)
    gi = folder / ".gitignore"
    if not gi.exists():
        gi.write_text("reference/\n", encoding="utf-8")
    for p in made:
        print("wrote", p.relative_to(ROOT))
    print(f"reference images in {ref.relative_to(ROOT)}/ (base.png, overlay.png); legend.png shows the biome colours")


_FONT = {  # 3 x 5 pixel font for the legend labels
    "a": "010101111101101", "b": "110101110101110", "c": "011100100100011", "d": "110101101101110",
    "e": "111100110100111", "f": "111100110100100", "g": "011100101101011", "h": "101101111101101",
    "i": "111010010010111", "j": "001001001101010", "k": "101101110101101", "l": "100100100100111",
    "m": "101111111101101", "n": "110101101101101", "o": "010101101101010", "p": "110101110100100",
    "q": "010101101110011", "r": "110101110101101", "s": "011100010001110", "t": "111010010010010",
    "u": "101101101101111", "v": "101101101101010", "w": "101101111111101", "x": "101101010101101",
    "y": "101101010010010", "z": "111001010100111", "_": "000000000000111", ":": "000010000010000",
    " ": "000000000000000",
}


def _legend_png(legend, path):
    rows = list(legend.items())
    cell, scale = 12, 2
    w = 420
    h = len(rows) * (cell + 4) + 4
    rgb = bytearray(b"\xff" * (w * h * 3))
    for r, (name, colour) in enumerate(rows):
        y0 = 4 + r * (cell + 4)
        for y in range(y0, y0 + cell):
            for x in range(4, 4 + cell * 2):
                rgb[(y * w + x) * 3:(y * w + x) * 3 + 3] = bytes(colour)
        x = 4 + cell * 2 + 8
        for ch in name.lower():
            glyph = _FONT.get(ch, _FONT[" "])
            for gy in range(5):
                for gx in range(3):
                    if glyph[gy * 3 + gx] == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                yy, xx = y0 + 1 + gy * scale + sy, x + gx * scale + sx
                                if xx < w and yy < h:
                                    rgb[(yy * w + xx) * 3:(yy * w + xx) * 3 + 3] = b"\x00\x00\x00"
            x += 4 * scale
    pngcodec.write_png(path, w, h, rgb, rgb=True)


def _reference(build, idx, frame, ref):
    import raster_preview
    ref.mkdir(parents=True, exist_ok=True)
    raster_preview.render(build, ref / "base.png", scale=1)
    # The overlay: sites (white rings, plated = filled), road centrelines, the coast, on transparency.
    w, h, px = frame["w"], frame["h"], frame["px"]
    rgba = bytearray(w * h * 4)
    _, _, road, _ = pngcodec.read_png(build / idx["files"]["road"]["file"])
    _, _, water, _ = pngcodec.read_png(build / idx["files"]["water"]["file"])
    _, _, biome, _ = pngcodec.read_png(build / idx["files"]["biome"]["file"])
    dx = (idx["box"]["x0"] - frame["x0"]) // px
    dz = (idx["box"]["z0"] - frame["z0"]) // px
    rw, rh = idx["box"]["width_px"], idx["box"]["height_px"]
    for j in range(rh):
        for i in range(rw):
            g = j * rw + i
            fi, fj = i + dx, j + dz
            if not (0 <= fi < w and 0 <= fj < h):
                continue
            k = (fj * w + fi) * 4
            land = biome[g] != 0
            if road[g] in (2, 3, 4, 5):
                rgba[k:k + 4] = b"\x50\x30\x10\xff"
            elif water[g]:
                rgba[k:k + 4] = b"\x30\x60\xe0\xc0"
            elif land and ((i > 0 and biome[g - 1] == 0) or (j > 0 and biome[g - rw] == 0)):
                rgba[k:k + 4] = b"\x00\x00\x00\xff"
    for s in idx["sites"]:
        cx, cz, r = (s["x"] - frame["x0"]) / px, (s["z"] - frame["z0"]) / px, s["r"] / px
        for j in range(int(cz - r) - 1, int(cz + r) + 2):
            for i in range(int(cx - r) - 1, int(cx + r) + 2):
                if 0 <= i < w and 0 <= j < h:
                    d = math.hypot(i + 0.5 - cx, j + 0.5 - cz)
                    if d <= r:
                        k = (j * w + i) * 4
                        rgba[k:k + 4] = b"\xff\xff\xff\xff" if d > r - 1.5 else b"\xff\xff\xff\x50"
    write_rgba(ref / "overlay.png", w, h, rgba)


def status(folder=PAINT):
    folder = Path(folder)
    if not (folder / "frame.json").exists():
        print("no paint yet: python -I tools/world/paint.py template")
        return 0
    p = Paint(folder)
    print(f"frame: x {p.x0}..{p.x0 + p.w * p.px}, z {p.z0}..{p.z0 + p.h * p.px}, {p.px} blocks per pixel, {p.w} x {p.h} px")
    if p.height is not None:
        changed = [v for v in p.height if v != NEUTRAL]
        print(f"height: {len(changed)} px painted ({len(changed) * p.px * p.px / 1e6:.2f} km2), "
              f"{(min(changed) - NEUTRAL) * HEIGHT_STEP:+.0f}..{(max(changed) - NEUTRAL) * HEIGHT_STEP:+.0f} blocks")
    else:
        print("height: nothing painted")
    if p.rugged is not None:
        changed = [v for v in p.rugged if v != NEUTRAL]
        print(f"rugged: {len(changed)} px painted, {(min(changed) - NEUTRAL) / 127:+.2f}..{(max(changed) - NEUTRAL) / 127:+.2f}")
    else:
        print("rugged: nothing painted")
    if p.biome is not None:
        counts = {}
        for v in p.biome:
            if v:
                counts[p.biome_names[v]] = counts.get(p.biome_names[v], 0) + 1
        print("biome: " + ", ".join(f"{b} {n} px" for b, n in sorted(counts.items(), key=lambda kv: -kv[1])))
    else:
        print("biome: nothing painted")
    if p.bad_colours:
        top = sorted(p.bad_colours.items(), key=lambda kv: -kv[1])[:8]
        print("WARNING: colours not in legend.json (ignored; paint with a hard pencil in a legend colour): "
              + ", ".join(f"rgb{c} {n} px" for c, n in top))
        return 1
    return 0


def _edit_grey(folder, name, fn):
    folder = Path(folder)
    frame = json.loads((folder / "frame.json").read_text(encoding="utf-8"))
    w, h, data = read_grey(folder / name)
    data = bytearray(data)
    fn(frame, w, h, data)
    pngcodec.write_png(folder / name, w, h, bytes(data))


def blob(layer, x, z, radius, delta, folder=PAINT):
    """Soft round brush (smooth falloff to the rim) added to height (blocks) or rugged (-1..1)."""
    unit = HEIGHT_STEP if layer == "height" else 1 / 127.0

    def fn(frame, w, h, data):
        px = frame["px"]
        ci, cj, r = (x - frame["x0"]) / px, (z - frame["z0"]) / px, radius / px
        for j in range(max(0, int(cj - r) - 1), min(h, int(cj + r) + 2)):
            for i in range(max(0, int(ci - r) - 1), min(w, int(ci + r) + 2)):
                d = math.hypot(i + 0.5 - ci, j + 0.5 - cj) / r
                if d < 1:
                    t = 1 - d * d
                    k = j * w + i
                    data[k] = max(0, min(255, int(round(data[k] + delta * t * t / unit))))
    _edit_grey(folder, f"{layer}.png", fn)


def ridge(layer, x1, z1, x2, z2, width, delta, folder=PAINT):
    """A soft brush stroke along a line: a mountain chain (height) or a rough belt (rugged)."""
    unit = HEIGHT_STEP if layer == "height" else 1 / 127.0

    def fn(frame, w, h, data):
        px = frame["px"]
        ax, az, bx, bz = (x1 - frame["x0"]) / px, (z1 - frame["z0"]) / px, (x2 - frame["x0"]) / px, (z2 - frame["z0"]) / px
        r = width / 2 / px
        for j in range(max(0, int(min(az, bz) - r) - 1), min(h, int(max(az, bz) + r) + 2)):
            for i in range(max(0, int(min(ax, bx) - r) - 1), min(w, int(max(ax, bx) + r) + 2)):
                cx, cz = i + 0.5, j + 0.5
                dx, dz = bx - ax, bz - az
                t = 0 if dx == dz == 0 else max(0.0, min(1.0, ((cx - ax) * dx + (cz - az) * dz) / (dx * dx + dz * dz)))
                d = math.hypot(cx - (ax + t * dx), cz - (az + t * dz)) / r
                if d < 1:
                    s = 1 - d * d
                    k = j * w + i
                    data[k] = max(0, min(255, int(round(data[k] + delta * s * s / unit))))
    _edit_grey(folder, f"{layer}.png", fn)


def disc(x, z, radius, biome, folder=PAINT):
    folder = Path(folder)
    legend = json.loads((folder / "legend.json").read_text(encoding="utf-8"))
    if biome not in legend:
        raise SystemExit(f"{biome} is not in world/paint/legend.json (allowed biomes: tools/world/biomes.txt)")
    frame = json.loads((folder / "frame.json").read_text(encoding="utf-8"))
    w, h, rgb = read_rgb(folder / "biome.png")
    rgb = bytearray(rgb)
    px = frame["px"]
    ci, cj, r = (x - frame["x0"]) / px, (z - frame["z0"]) / px, radius / px
    colour = bytes(legend[biome])
    for j in range(max(0, int(cj - r) - 1), min(h, int(cj + r) + 2)):
        for i in range(max(0, int(ci - r) - 1), min(w, int(ci + r) + 2)):
            if math.hypot(i + 0.5 - ci, j + 0.5 - cj) <= r:
                k = (j * w + i) * 3
                rgb[k:k + 3] = colour
    pngcodec.write_png(folder / "biome.png", w, h, bytes(rgb), rgb=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "template":
        template()
        return 0
    if cmd == "status":
        return status()
    if cmd == "blob" and len(argv) == 6 and argv[1] in ("height", "rugged"):
        blob(argv[1], float(argv[2]), float(argv[3]), float(argv[4]), float(argv[5]))
        return 0
    if cmd == "ridge" and len(argv) == 8 and argv[1] in ("height", "rugged"):
        ridge(argv[1], *(float(v) for v in argv[2:8]))
        return 0
    if cmd == "disc" and len(argv) == 6 and argv[1] == "biome":
        disc(float(argv[2]), float(argv[3]), float(argv[4]), argv[5])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
