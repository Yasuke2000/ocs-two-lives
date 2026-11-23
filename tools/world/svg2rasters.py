#!/usr/bin/env python3
"""world/map.svg + world/sites.toml -> the generator rasters of the own world (WP-W1; stdlib only).

    python -I tools/world/svg2rasters.py [world/map.svg] [--out pack/config/ttl/world] [--sites world/sites.toml]
                                         [--seed N] [--sea-margin 1200] [--region 512]

design/architecture/own-world.md §2-§3. One pixel = 4 x 4 blocks (a quart, what the biome source samples). The design
box is the content (land, lakes, roads, sites) + `sea-margin` blocks of sea, rounded out to `region` blocks (512 = a
region file), hard limit 14,336 x 11,264. Pixel (i, j) covers blocks x0 + 4i .. x0 + 4i + 3, z0 + 4j .. z0 + 4j + 3 and
its value is taken at the pixel centre (x0 + 4i + 2, z0 + 4j + 2). Rows run north to south (+z), columns west to east.

Files written to --out (index.json is the legend the mod reads; every number below is repeated there):

    height.png    16-bit grey: round((H + 64) * 16), H = the designed surface = y of the first air block (vanilla's
                  offset convention: offset = (H - 128) / 128, so the depth gradient crosses zero at y = H; sea level
                  63, sea floor down to -20). Sub-block precision (1/16) so slopes do not terrace.
    rugged.png    8-bit grey: rugged * 255, rugged in 0..1. Classes (factor / jaggedness for ttl:design_*): flat
                  < 0.10 (8), rolling < 0.45 (5), hills < 0.75 (3), alpine >= 0.75 (1.5); piecewise-linear between
                  the class centres (legend `rugged.factor`), jaggedness 0 below 0.8 rising to 0.6 at 1.0.
    water.png     16-bit grey: 0 = no designed water; else level + 64. Level L = y of the first air above the water,
                  vanilla's sea-level convention (sea level 63 = water blocks up to y 62): ttl:design_water fills source
                  blocks from the bed up to y L - 1. Lakes, rivers (stepped flat reaches: a level per reach, steps of
                  1-2 blocks every 40-120 blocks; at 63 a tidal reach) and lakeside plates under water. The open sea
                  is not in it (vanilla's aquifer fills it to 63).
    road.png      8-bit: 0 none, 1 corridor (graded, cut/fill done, no surface), 2 trail surface, 3 main surface,
                  4 trail bridge, 5 main bridge. Exact centrelines and profiles are in roads.json.
    biome.png     8-bit palette: the index into legend `biomes` (index 0 = "#ocean": vanilla's ocean choice by depth
                  and temperature). Rules (design §2.2): `biomes` polygon > site biome inside r > Jura rings round
                  Tempest (core r 200 tensura:ancient_forest, band to 600 minecraft:dark_forest, inside region J) >
                  `forests` type > river on lake/river water > beach / snowy_beach / stony_shore on the coast strip >
                  peaks by height and rugged > the region's default_biome (sites.toml [region.<letter>]) > plains.
    sites.png     8-bit: 1-based index into legend `sites` inside every plated site's radius r; 0 elsewhere. r is
                  the SVG circle's, raised to the build's min_r (tools/world/sites_from_builds.py) when drawn smaller.
    exclude.png   8-bit bit mask, the Q4 structure exclusion (no structure start where non-zero): 1 = a plated
                  site's r + its data-margin (default 48), 2 = a road corridor + its data-margin (default 8), 4 = a
                  carve cavity (the build's box + margin: Dwargon's city, the Sealed Cave). The ttl:design_dry
                  wrapper uses bits 1 and 4.
    index.json    the legend: box, scale, encodings, biome list, classes, sites (id, kind, x, z, r, fade, y, ...),
                  water bodies, roads, warnings, the source hash and seed.
    sites.json    {"sites": [...]} in the schema CanonSites reads (name, centre, radius, fade, terrain "flat", ground,
                  biomes); carve sites are left out (a flat pull would level the massif over the cavern).
    roads.json    every road: id, kind, half width, corridor, centreline [[x, z, y, bridge]] every 4 blocks.
    canon_map.txt the chunk grid (CanonGrid format: '.' sea, '~' lake/river, region letters) of the design box.

Deterministic: the same SVG, sites.toml, footprints and seed give the same bytes. Unused by the game until the switch
(the mod falls back to today's world when pack/config/ttl/world/ is absent).
"""
import argparse
import hashlib
import json
import math
import statistics
import sys
import tomllib
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paint as paint_mod  # noqa: E402
import pngcodec  # noqa: E402
import sites_from_builds as sfb  # noqa: E402
import svgparse  # noqa: E402

ROOT = HERE.parent.parent
DEFAULT_SVG = ROOT / "world" / "map.svg"
DEFAULT_OUT = ROOT / "pack" / "config" / "ttl" / "world"
DEFAULT_SITES = ROOT / "world" / "sites.toml"

PX = 4                   # blocks per pixel
K = 4                    # pixels per coarse cell (coarse cell = 16 blocks = one chunk)
CELL = PX * K
SEA = 63
REGION = 512
SEA_MARGIN = 1200
HARD_LIMIT = (14336, 11264)
SEED = 2026
SCALE = 16               # height.png fixed point
WATER_OFFSET = 64
SHELF, SHELF_Y, DEEP_AT, DEEP_Y = 96, 52, 300, -20
COAST_BAND = 48          # blocks either side of the coast where the exact distance and the wiggle are computed
WIGGLE = 24              # blocks: 8 % of the ~300-block shelf
JURA_CORE, JURA_BAND = 200, 600
SITE_MARGIN = 48
ROAD_MARGIN = 8
CAVITY_MARGIN = 8
MIN_REACH, MAX_REACH_JITTER = 40, 24
MAX_STEP = 2
ROAD_HALF = {"main": 2, "trail": 1}
ROAD_GRADE = 0.5         # max rise per block (1:2, trade_roads max_grade)
BRIDGE_MAX = 64
VALLEY = 32              # blocks of 1:1 valley wall / batter beside rivers and roads
FOREST_BIOMES = {
    "light": "minecraft:forest", "dense": "minecraft:old_growth_birch_forest", "dark": "minecraft:dark_forest",
    "ancient": "tensura:ancient_forest", "birch": "minecraft:birch_forest", "taiga": "minecraft:taiga",
    "old_taiga": "minecraft:old_growth_spruce_taiga", "jungle": "minecraft:jungle",
    "sparse_jungle": "minecraft:sparse_jungle", "cherry": "minecraft:cherry_grove",
    "mangrove": "minecraft:mangrove_swamp",
    # aliases the map tooling has used while the spec settled
    "ancient_jura": "tensura:ancient_forest", "mixed": "minecraft:forest", "sparse": "minecraft:forest",
}
ALLOWED_BIOMES = {"minecraft:" + b for b in (
    "plains sunflower_plains meadow forest flower_forest birch_forest old_growth_birch_forest dark_forest taiga "
    "old_growth_pine_taiga old_growth_spruce_taiga snowy_taiga grove cherry_grove swamp mangrove_swamp jungle "
    "sparse_jungle bamboo_jungle savanna savanna_plateau windswept_savanna desert badlands eroded_badlands "
    "wooded_badlands windswept_hills windswept_forest windswept_gravelly_hills stony_peaks jagged_peaks frozen_peaks "
    "snowy_slopes snowy_plains ice_spikes mushroom_fields").split()} | {
    "tensura:ancient_forest", "tensura:barren_land", "tensura:desert_of_death", "tensura:miasmic_plains"}
BIOMES_TXT = HERE / "biomes.txt"
if BIOMES_TXT.is_file():
    # the map checker's list is the one source; the constant above is the fallback (design §2.2.1)
    ALLOWED_BIOMES = set()
    for _line in BIOMES_TXT.read_text(encoding="utf-8").splitlines():
        _line = _line.split("#", 1)[0].strip()
        if _line:
            ALLOWED_BIOMES.add(_line if ":" in _line else "minecraft:" + _line)
AUTO_BIOMES = ["#ocean", "minecraft:river", "minecraft:frozen_river", "minecraft:beach", "minecraft:snowy_beach",
               "minecraft:stony_shore"]
RUGGED = {"default_land": 0.2, "default_sea": 0.1, "hill": 0.4, "mountain": 0.8,
          "classes": [["flat", 0.0, 0.10, 8.0], ["rolling", 0.10, 0.45, 5.0], ["hills", 0.45, 0.75, 3.0],
                      ["alpine", 0.75, 1.0, 1.5]],
          "factor": [[0.0, 8.0], [0.10, 8.0], [0.30, 5.0], [0.60, 3.0], [0.80, 1.5], [1.0, 1.5]],
          "jaggedness": [[0.0, 0.0], [0.8, 0.0], [1.0, 0.6]]}
PEAKS = [("minecraft:frozen_peaks", 240, 0.6), ("minecraft:jagged_peaks", 200, 0.75),
         ("minecraft:snowy_slopes", 190, 0.0), ("minecraft:stony_peaks", 150, 0.6)]
ROAD_CLASS = {"none": 0, "corridor": 1, "trail": 2, "main": 3, "trail_bridge": 4, "main_bridge": 5}
EXCL = {"site": 1, "road": 2, "cavity": 4}
BIOME_COLOURS = {
    "#ocean": (30, 60, 130), "minecraft:river": (60, 110, 220), "minecraft:frozen_river": (160, 190, 240),
    "minecraft:beach": (230, 220, 160), "minecraft:snowy_beach": (240, 240, 230), "minecraft:stony_shore": (140, 140, 140),
    "minecraft:plains": (140, 190, 90), "minecraft:sunflower_plains": (170, 200, 80), "minecraft:meadow": (150, 210, 120),
    "minecraft:forest": (60, 130, 50), "minecraft:flower_forest": (90, 150, 70), "minecraft:birch_forest": (110, 160, 90),
    "minecraft:old_growth_birch_forest": (80, 140, 70), "minecraft:dark_forest": (35, 80, 30),
    "minecraft:taiga": (60, 110, 80), "minecraft:old_growth_pine_taiga": (70, 100, 70),
    "minecraft:old_growth_spruce_taiga": (55, 95, 65), "minecraft:snowy_taiga": (180, 200, 190),
    "minecraft:grove": (190, 210, 200), "minecraft:cherry_grove": (230, 170, 200), "minecraft:swamp": (80, 100, 60),
    "minecraft:mangrove_swamp": (70, 110, 70), "minecraft:jungle": (40, 150, 30), "minecraft:sparse_jungle": (90, 160, 60),
    "minecraft:bamboo_jungle": (100, 180, 50), "minecraft:savanna": (190, 180, 90),
    "minecraft:savanna_plateau": (170, 160, 90), "minecraft:windswept_savanna": (180, 170, 110),
    "minecraft:desert": (225, 205, 140), "minecraft:badlands": (200, 100, 50), "minecraft:eroded_badlands": (210, 90, 40),
    "minecraft:wooded_badlands": (170, 110, 60), "minecraft:windswept_hills": (130, 150, 130),
    "minecraft:windswept_forest": (90, 120, 90), "minecraft:windswept_gravelly_hills": (150, 150, 150),
    "minecraft:stony_peaks": (160, 160, 160), "minecraft:jagged_peaks": (220, 220, 230),
    "minecraft:frozen_peaks": (235, 240, 250), "minecraft:snowy_slopes": (225, 230, 235),
    "minecraft:snowy_plains": (240, 245, 245), "minecraft:ice_spikes": (200, 230, 250),
    "minecraft:mushroom_fields": (160, 110, 160), "tensura:ancient_forest": (20, 60, 25),
    "tensura:barren_land": (150, 130, 110), "tensura:desert_of_death": (200, 170, 120),
    "tensura:miasmic_plains": (120, 100, 140),
}


class MapError(Exception):
    pass


# ----------------------------------------------------------------------------------------------------------- helpers

def smoothstep(t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return t * t * (3 - 2 * t)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def _hash01(ix, iz, seed):
    h = (ix * 0x27D4EB2D) ^ (iz * 0x165667B1) ^ (seed * 0x9E3779B1)
    h &= 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & 0xFFFFFFFF
    h ^= h >> 12
    h = (h * 0x297A2D39) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 4294967296.0


def vnoise(x, z, cell, seed):
    """Smooth value noise in [-1, 1) on a lattice of `cell` blocks (the Lerfing tools' wobble)."""
    fx, fz = x / cell, z / cell
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _hash01(ix, iz, seed), _hash01(ix + 1, iz, seed)
    c, d = _hash01(ix, iz + 1, seed), _hash01(ix + 1, iz + 1, seed)
    top = a + (b - a) * tx
    return (top + (c + (d - c) * tx - top) * tz) * 2 - 1


def seg_dist(px, pz, ax, az, bx, bz):
    """(distance, t) from a point to the segment a-b."""
    dx, dz = bx - ax, bz - az
    ll = dx * dx + dz * dz
    t = 0.0 if ll == 0 else clamp(((px - ax) * dx + (pz - az) * dz) / ll, 0.0, 1.0)
    ex, ez = ax + t * dx - px, az + t * dz - pz
    return math.sqrt(ex * ex + ez * ez), t


def bbox_of(pts):
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    return min(xs), min(zs), max(xs), max(zs)


def densify(pts, step):
    """Points every `step` blocks along a polyline (the vertices kept), with their distance along it."""
    out = [(pts[0][0], pts[0][1], 0.0)]
    s = 0.0
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(math.ceil(seg / step)))
        for k in range(1, n + 1):
            t = k / n
            out.append((ax + (bx - ax) * t, az + (bz - az) * t, s + seg * t))
        s += seg
    return out


def fill_polygon(pts, ox, oz, cell, w, h, mask, value=1):
    """Scanline fill (even-odd) of the cells whose centre lies inside; mask is a bytearray of w*h."""
    n = len(pts)
    if n < 3:
        return
    zs = [p[1] for p in pts]
    j0 = max(0, int(math.floor((min(zs) - oz) / cell - 0.5)))
    j1 = min(h - 1, int(math.ceil((max(zs) - oz) / cell)))
    byte = bytes([value])
    for j in range(j0, j1 + 1):
        zc = oz + (j + 0.5) * cell
        xs = []
        for k in range(n):
            ax, az = pts[k]
            bx, bz = pts[(k + 1) % n]
            if (az <= zc) != (bz <= zc):
                xs.append(ax + (zc - az) * (bx - ax) / (bz - az))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            i0 = max(0, math.ceil((a - ox) / cell - 0.5))
            i1 = min(w - 1, math.ceil((b - ox) / cell - 0.5) - 1)
            if i0 <= i1:
                mask[j * w + i0:j * w + i1 + 1] = byte * (i1 - i0 + 1)


INF = 1e12


def _edt1(f, n):
    # |f| <= INF and q - r >= 1 keep every parabola intersection above -INF, so k never drops below 0
    d = [0.0] * n
    v = [0] * n
    z = [0.0] * (n + 1)
    k = 0
    z[0], z[1] = -INF * 4, INF * 4
    for q in range(1, n):
        fq = f[q] + q * q
        r = v[k]
        s = (fq - (f[r] + r * r)) / (2 * q - 2 * r)
        while s <= z[k]:
            k -= 1
            r = v[k]
            s = (fq - (f[r] + r * r)) / (2 * q - 2 * r)
        k += 1
        v[k], z[k], z[k + 1] = q, s, INF * 4
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        r = v[k]
        d[q] = (q - r) * (q - r) + f[r]
    return d


def edt(mask, w, h, want=1):
    """Squared Euclidean distance (cells) from every cell to the nearest cell whose mask value is `want`
    (Felzenszwalb-Huttenlocher, exact). Cells beyond any feature get ~INF."""
    g = [0.0 if m == want else INF for m in mask]
    for i in range(w):
        col = _edt1(g[i::w], h)
        g[i::w] = col
    out = []
    for j in range(h):
        out.extend(_edt1(g[j * w:(j + 1) * w], w))
    return out


def upsample(c, cw, ch, k=K):
    """Bilinear: a coarse grid (cell centres) -> the fine grid k times denser (pixel centres)."""
    w = cw * k
    cols = []
    for i in range(w):
        u = (i + 0.5) / k - 0.5
        i0 = int(math.floor(u))
        t = u - i0
        a, b = clamp(i0, 0, cw - 1), clamp(i0 + 1, 0, cw - 1)
        cols.append((a, b, t))
    out = array("f")
    for j in range(ch * k):
        v = (j + 0.5) / k - 0.5
        j0 = int(math.floor(v))
        t = v - j0
        ra = c[clamp(j0, 0, ch - 1) * cw:clamp(j0, 0, ch - 1) * cw + cw]
        rb = c[clamp(j0 + 1, 0, ch - 1) * cw:clamp(j0 + 1, 0, ch - 1) * cw + cw]
        row = [x + (y - x) * t for x, y in zip(ra, rb)]
        out.extend([row[a] + (row[b] - row[a]) * tt for a, b, tt in cols])
    return out


def blur3(vals, w, h, passes=1):
    """3x3 box blur, edges clamped."""
    v = list(vals)
    for _ in range(passes):
        rows = []
        for j in range(h):
            r = v[j * w:(j + 1) * w]
            rows.append([(r[max(i - 1, 0)] + r[i] + r[min(i + 1, w - 1)]) / 3 for i in range(w)])
        v = []
        for j in range(h):
            a, b, c = rows[max(j - 1, 0)], rows[j], rows[min(j + 1, h - 1)]
            v.extend([(x + y + z) / 3 for x, y, z in zip(a, b, c)])
    return v


class SegIndex:
    """Bucketed segments for distance queries near them."""

    def __init__(self, segs, cell=64):
        self.cell = cell
        self.b = {}
        for s in segs:
            x0, x1 = sorted((s[0], s[2]))
            z0, z1 = sorted((s[1], s[3]))
            for bx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
                for bz in range(int(math.floor(z0 / cell)), int(math.floor(z1 / cell)) + 1):
                    self.b.setdefault((bx, bz), []).append(s)

    def dist(self, x, z, maxd):
        c = self.cell
        r = int(math.ceil(maxd / c))
        bx, bz = int(math.floor(x / c)), int(math.floor(z / c))
        best = maxd
        seen = set()
        for i in range(bx - r, bx + r + 1):
            for k in range(bz - r, bz + r + 1):
                for s in self.b.get((i, k), ()):
                    if id(s) in seen:
                        continue
                    seen.add(id(s))
                    d, _ = seg_dist(x, z, s[0], s[1], s[2], s[3])
                    if d < best:
                        best = d
        return best


# ------------------------------------------------------------------------------------------------------------- input

class Options:
    def __init__(self, seed=SEED, sea_margin=SEA_MARGIN, region=REGION, site_margin=SITE_MARGIN,
                 road_margin=ROAD_MARGIN, hard_limit=HARD_LIMIT):
        self.seed, self.sea_margin, self.region = seed, sea_margin, region
        self.site_margin, self.road_margin, self.hard_limit = site_margin, road_margin, hard_limit


def site_overrides(path):
    p = Path(path) if path else None
    return tomllib.loads(p.read_text(encoding="utf-8")) if p and p.is_file() else {}


class Site:
    def __init__(self, sid, kind, x, z, r, anchor, req, ov):
        self.id, self.kind, self.x, self.z, self.r = sid, kind, x, z, r
        self.anchor = anchor or {}
        self.req = req or {}
        self.ov = ov or {}
        akind = self.anchor.get("kind")
        self.plated = akind in sfb.PLATED if akind else r > sfb.PIN_R
        self.svg_r = r
        if self.plated and self.req.get("min_r", 0) > r:
            self.r = r = self.req["min_r"]       # the footprint drives the site (design §4.2)
        self.fade = int(self.ov.get("fade", clamp(round(r / 2), 24, 96)))
        self.biome = self.ov.get("biome")
        self.facing = self.ov.get("facing", "south" if kind == "carve" else "auto")
        self.cover = int(self.ov.get("min_cover", sfb.MIN_COVER))
        self.surface = self.ov.get("surface", "land")
        self.ground = None
        self.index = 0


# -------------------------------------------------------------------------------------------------------- the build

class World:
    """All rasters of one build. Fine grid w x h at PX blocks, coarse grid cw x ch at CELL blocks."""

    def __init__(self, shapes, opts, anchors=None, overrides=None, reqs=None, source_hash="", paint=None):
        self.shapes, self.o = shapes, opts
        self.paint = paint  # tools/world/paint.py Paint (world/paint/*.png) or None
        self.anchors = anchors or {}
        self.ov = overrides or {}
        self.reqs = reqs or {}
        self.source_hash = source_hash
        self.warnings = []
        self.lakes_info, self.rivers_info, self.roads_info = [], [], []

    def warn(self, msg):
        self.warnings.append(msg)

    # ---- box
    def design_box(self):
        pts = []
        for layer in ("coast", "lakes", "roads"):
            for s in self.shapes[layer]:
                pts.extend(s.pts)
        for s in self.shapes["sites"]:
            if s.r is not None:
                pts += [(s.cx - s.r, s.cy - s.r), (s.cx + s.r, s.cy + s.r)]
        if not pts:
            raise MapError("the map has no coast, lakes, roads or sites")
        x0, z0, x1, z1 = bbox_of(pts)
        m, reg = self.o.sea_margin, self.o.region
        bx0 = int(math.floor((x0 - m) / reg)) * reg
        bz0 = int(math.floor((z0 - m) / reg)) * reg
        bx1 = int(math.ceil((x1 + m) / reg)) * reg
        bz1 = int(math.ceil((z1 + m) / reg)) * reg
        if bx1 - bx0 > self.o.hard_limit[0] or bz1 - bz0 > self.o.hard_limit[1]:
            raise MapError("design box %d x %d exceeds the hard limit %d x %d" % (
                bx1 - bx0, bz1 - bz0, self.o.hard_limit[0], self.o.hard_limit[1]))
        return bx0, bz0, bx1, bz1, (x0, z0, x1, z1)

    def setup(self):
        self.x0, self.z0, x1, z1, self.content = self.design_box()
        self.w, self.h = (x1 - self.x0) // PX, (z1 - self.z0) // PX
        self.cw, self.ch = self.w // K, self.h // K
        n = self.w * self.h
        self.n = n
        self.water = array("H", bytes(2 * n))       # level + 64
        self.wkind = bytearray(n)                   # 0 dry, 1 lake, 2 river, 3 site under water
        self.road = bytearray(n)
        self.site = bytearray(n)
        self.excl = bytearray(n)
        self.floor = array("f", [-INF]) * n          # lowest allowed H (lake rims, banks, roof cover)

    def centre(self, i, j):
        return self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX

    def pix(self, x, z):
        return int(math.floor((x - self.x0) / PX)), int(math.floor((z - self.z0) / PX))

    def px_range(self, x0, z0, x1, z1):
        i0 = clamp(int(math.floor((x0 - self.x0) / PX - 0.5)), 0, self.w - 1)
        i1 = clamp(int(math.ceil((x1 - self.x0) / PX - 0.5)), 0, self.w - 1)
        j0 = clamp(int(math.floor((z0 - self.z0) / PX - 0.5)), 0, self.h - 1)
        j1 = clamp(int(math.ceil((z1 - self.z0) / PX - 0.5)), 0, self.h - 1)
        return i0, i1, j0, j1

    def sample(self, x, z):
        """Bilinear H at a block position (px values at px centres)."""
        u = (x - self.x0) / PX - 0.5
        v = (z - self.z0) / PX - 0.5
        i0, j0 = int(math.floor(u)), int(math.floor(v))
        tu, tv = u - i0, v - j0
        w, h, H = self.w, self.h, self.H
        a = clamp(i0, 0, w - 1)
        b = clamp(i0 + 1, 0, w - 1)
        c = clamp(j0, 0, h - 1) * w
        d = clamp(j0 + 1, 0, h - 1) * w
        top = H[c + a] + (H[c + b] - H[c + a]) * tu
        bot = H[d + a] + (H[d + b] - H[d + a]) * tu
        return top + (bot - top) * tv

    # ---- land and base relief
    def coarse_base(self):
        cw, ch = self.cw, self.ch
        land = bytearray(cw * ch)
        for s in self.shapes["coast"]:
            if s.closed:
                fill_polygon(s.pts, self.x0, self.z0, CELL, cw, ch, land)
        self.land_c = land
        to_sea = edt(land, cw, ch, 0)
        to_land = edt(land, cw, ch, 1)
        sd = []
        for k in range(cw * ch):
            if land[k]:
                sd.append((math.sqrt(to_sea[k]) - 0.5) * CELL)
            else:
                sd.append(-(math.sqrt(to_land[k]) - 0.5) * CELL)
        self.sd_c = sd
        seed = self.o.seed
        noise, hb = [], []
        for j in range(ch):
            for i in range(cw):
                x, z = self.x0 + (i + 0.5) * CELL, self.z0 + (j + 0.5) * CELL
                nz = 4.0 * vnoise(x, z, 256, seed + 11) + 1.5 * vnoise(x, z, 64, seed + 12)
                noise.append(nz)
                s = sd[j * cw + i]
                hb.append(base_height(s) + nz * noise_weight(s))
        self.noise_c, self.hb_c = noise, hb

    def fine_land(self):
        w, h = self.w, self.h
        land = bytearray(self.n)
        for s in self.shapes["coast"]:
            if s.closed:
                fill_polygon(s.pts, self.x0, self.z0, PX, w, h, land)
        sd = upsample(self.sd_c, self.cw, self.ch)
        segs = []
        for s in self.shapes["coast"]:
            if s.closed:
                p = s.pts
                segs += [(p[k][0], p[k][1], p[(k + 1) % len(p)][0], p[(k + 1) % len(p)][1]) for k in range(len(p))]
        idx = SegIndex(segs)
        band = COAST_BAND + CELL
        protect = self.protectors()
        seed = self.o.seed
        for k in range(self.n):
            v = sd[k]
            inside = land[k]
            if abs(v) > band and (v > 0) == bool(inside):
                continue
            i, j = k % w, k // w
            x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
            d = idx.dist(x, z, band + CELL)
            s = d if inside else -d
            if abs(s) < WIGGLE + 4:
                a = WIGGLE * protect(x, z)
                if a:
                    s += a * (0.65 * vnoise(x, z, 96, seed + 1) + 0.35 * vnoise(x, z, 32, seed + 2))
            sd[k] = s
            land[k] = 1 if s > 0 else 0
        self.sd, self.land = sd, land

    def protectors(self):
        """Wiggle factor 0..1: no coastal wiggle on coast sites (r + fade) or within 32 blocks of a road."""
        discs = [(s.cx, s.cy, s.r + max(24, s.r / 2)) for s in self.shapes["sites"] if s.r is not None]
        segs = []
        for s in self.shapes["roads"]:
            segs += [(a[0], a[1], b[0], b[1]) for a, b in zip(s.pts, s.pts[1:])]
        idx = SegIndex(segs) if segs else None

        def f(x, z):
            for cx, cz, rr in discs:
                d = math.hypot(x - cx, z - cz)
                if d < rr + 32:
                    return smoothstep((d - rr) / 32)
            if idx is not None:
                d = idx.dist(x, z, 64)
                if d < 64:
                    return smoothstep((d - 32) / 32)
            return 1.0
        return f

    # ---- hills and mountains (coarse lift above the base)
    def features(self):
        cw, ch = self.cw, self.ch
        lift = [0.0] * (cw * ch)
        rug = [RUGGED["default_land"] if self.land_c[k] else RUGGED["default_sea"] for k in range(cw * ch)]
        ridges = [s for s in self.shapes["mountains"] if not s.closed or "ridge" in s.classes]
        for s in self.shapes["mountains"]:
            if s.closed and "ridge" not in s.classes:
                mine = [r for r in ridges if r.pts and svg_point_in(r.pts[0], s.pts)]
                self.feature(s, lift, rug, "mountain", mine)
        for s in self.shapes["hills"]:
            if s.closed:
                self.feature(s, lift, rug, "hill", [])
        self.lift_c = lift
        self.rug_c = blur3(rug, cw, ch, 1)

    def feature(self, s, lift, rug, kind, ridges):
        cw = self.cw
        bx0, bz0, bx1, bz1 = bbox_of(s.pts)
        i0 = clamp(int(math.floor((bx0 - self.x0) / CELL)) - 2, 0, cw - 1)
        i1 = clamp(int(math.ceil((bx1 - self.x0) / CELL)) + 2, 0, cw - 1)
        j0 = clamp(int(math.floor((bz0 - self.z0) / CELL)) - 2, 0, self.ch - 1)
        j1 = clamp(int(math.ceil((bz1 - self.z0) / CELL)) + 2, 0, self.ch - 1)
        lw, lh = i1 - i0 + 1, j1 - j0 + 1
        ox, oz = self.x0 + i0 * CELL, self.z0 + j0 * CELL
        mask = bytearray(lw * lh)
        fill_polygon(s.pts, ox, oz, CELL, lw, lh, mask)
        if not any(mask):
            self.warn("%s: smaller than one 16-block cell, ignored" % s.label)
            return
        de = [(math.sqrt(v) - 0.5) * CELL for v in edt(mask, lw, lh, 0)]
        seed = self.o.seed
        if kind == "mountain":
            peak = s.num("data-peak")
            if peak is None:
                self.warn("%s: no data-peak, ignored" % s.label)
                return
            shape = s.get("data-shape", "alpine")
            rugged = clamp(s.num("data-rugged", RUGGED["mountain"]), 0.0, 1.0)
            if ridges:
                rm = bytearray(lw * lh)
                for r in ridges:
                    for x, z, _ in densify(r.pts, CELL / 2):
                        a, b = int((x - ox) // CELL), int((z - oz) // CELL)
                        if 0 <= a < lw and 0 <= b < lh:
                            rm[b * lw + a] = 1
                dr = [math.sqrt(v) * CELL for v in edt(rm, lw, lh, 1)]
            else:
                mx = max(de[k] for k in range(lw * lh) if mask[k])
                dr = None
            for b in range(lh):
                for a in range(lw):
                    k = b * lw + a
                    if not mask[k]:
                        continue
                    e = max(de[k], 0.0)
                    t = e / (e + dr[k]) if dr is not None and e + dr[k] > 0 else (e / mx if mx > 0 else 1.0)
                    t = clamp(t, 0.0, 1.0)
                    p = mesa(t) if shape == "mesa" else math.sin(t * math.pi / 2) if shape == "dome" else t ** 1.5
                    g = (j0 + b) * cw + i0 + a
                    x, z = ox + (a + 0.5) * CELL, oz + (b + 0.5) * CELL
                    hb = self.hb_c[g]
                    top = hb + (peak - hb) * p
                    top += rugged * 0.05 * (peak - hb) * p * (1 - p) * vnoise(x, z, 128, seed + 21)
                    top = min(top, peak)
                    lift[g] = max(lift[g], top - hb)
                    rug[g] = max(rug[g], rugged)
        else:
            height = s.num("data-height")
            if height is None:
                self.warn("%s: no data-height, ignored" % s.label)
                return
            shape = s.get("data-shape", "rolling")
            rugged = clamp(s.num("data-rugged", RUGGED["hill"]), 0.0, 1.0)
            reach = 12.0 if shape == "mesa" else 64.0
            for b in range(lh):
                for a in range(lw):
                    k = b * lw + a
                    if not mask[k]:
                        continue
                    wgt = smoothstep(max(de[k], 0.0) / reach)
                    g = (j0 + b) * cw + i0 + a
                    x, z = ox + (a + 0.5) * CELL, oz + (b + 0.5) * CELL
                    hb = self.hb_c[g]
                    roll = 0.0 if shape == "mesa" else rugged * 6.0 * vnoise(x, z, 96, seed + 31)
                    top = hb + (height + roll - hb) * wgt
                    lift[g] = max(lift[g], top - hb)
                    rug[g] = max(rug[g], rugged * wgt)

    def relief(self):
        w = self.w
        lift = upsample(self.lift_c, self.cw, self.ch)
        noise = upsample(self.noise_c, self.cw, self.ch)
        self.rug = upsample(self.rug_c, self.cw, self.ch)
        sd = self.sd
        H = array("f")
        for j in range(self.h):
            row = range(j * w, (j + 1) * w)
            H.extend([base_height(sd[k]) + noise[k] * noise_weight(sd[k]) + lift[k] for k in row])
        self.H = H

    # ---- lakes
    def lakes(self):
        w = self.w
        for li, s in enumerate(self.shapes["lakes"]):
            if not s.closed:
                continue
            bx0, bz0, bx1, bz1 = bbox_of(s.pts)
            pad = 32
            i0, i1, j0, j1 = self.px_range(bx0 - pad, bz0 - pad, bx1 + pad, bz1 + pad)
            lw, lh = i1 - i0 + 1, j1 - j0 + 1
            ox, oz = self.x0 + i0 * PX, self.z0 + j0 * PX
            mask = bytearray(lw * lh)
            fill_polygon(s.pts, ox, oz, PX, lw, lh, mask)
            if not any(mask):
                self.warn("%s: smaller than one pixel, ignored" % s.label)
                continue
            din = [math.sqrt(v) * PX for v in edt(mask, lw, lh, 0)]
            dout = [math.sqrt(v) * PX for v in edt(mask, lw, lh, 1)]
            level = s.num("data-level")
            if level is None:
                rim = [self.H[(j0 + k // lw) * w + i0 + k % lw] for k in range(lw * lh) if 0 < dout[k] <= 8]
                level = math.floor(min(rim)) - 1 if rim else SEA
                level = max(level, SEA)
            level = int(round(level))
            depth = max(2, int(round(s.num("data-depth", 6))))
            name = s.get("id") or s.get("data-name") or "lake_%d" % (li + 1)
            self.lakes_info.append({"id": name, "level": level, "depth": depth, "pts": s.pts})
            for k in range(lw * lh):
                g = (j0 + k // lw) * w + i0 + k % lw
                if mask[k]:
                    self.H[g] = level - 1 - (depth - 1) * smoothstep(din[k] / 24.0)
                    self.water[g] = level + WATER_OFFSET
                    self.wkind[g] = 1
                    self.rug[g] = 0.0
                elif dout[k] <= 24:
                    need = level + 2 - max(0.0, dout[k] - 8)
                    if dout[k] <= 8:
                        self.H[g] = max(self.H[g], level + 2)
                    self.floor[g] = max(self.floor[g], need)
                    self.rug[g] = min(self.rug[g], 0.6 * smoothstep(dout[k] / 24.0))

    def lake_at(self, x, z):
        for lk in self.lakes_info:
            if svg_point_in((x, z), lk["pts"]):
                return lk
        return None

    # ---- rivers
    def rivers(self):
        for ri, s in enumerate(self.shapes["rivers"]):
            if s.closed or len(s.pts) < 2:
                continue
            width = clamp(s.num("data-width", 8), 4, 24)
            name = s.get("id") or "river_%d" % (ri + 1)
            samples = densify(s.pts, PX)
            wet = []
            for x, z, _ in samples:
                lk = self.lake_at(x, z)
                i, j = self.pix(x, z)
                sea = not (0 <= i < self.w and 0 <= j < self.h) or not self.land[j * self.w + i]
                wet.append(("lake", lk) if lk else ("sea", None) if sea else None)
            runs, k = [], 0
            while k < len(samples):
                if wet[k] is not None:
                    k += 1
                    continue
                a = k
                while k < len(samples) and wet[k] is None:
                    k += 1
                runs.append((a, k))
            info = {"id": name, "width": width, "reaches": []}
            for n_run, (a, b) in enumerate(runs):
                before = wet[a - 1] if a > 0 else None
                after = wet[b] if b < len(samples) else None
                terr = [self.sample(x, z) for x, z, _ in samples[a:b]]
                if before and before[0] == "lake":
                    head = before[1]["level"]
                elif a == 0 and s.num("data-head") is not None:
                    head = int(round(s.num("data-head")))
                else:
                    head = int(math.floor(terr[0])) - 2
                if after is None:
                    mouth = int(round(s.num("data-mouth", min(head, math.floor(terr[-1]) - 2))))
                    self.warn("%s: ends on land (a river must end in a lake or the sea)" % s.label)
                elif after[0] == "lake":
                    mouth = after[1]["level"]
                else:
                    mouth = SEA
                head = max(head, mouth)
                levels = reach_levels(terr, head, mouth, self.o.seed + 101 * ri + n_run)
                self.paint_river(samples[a:b], levels, width)
                info["reaches"] += reach_summary(samples[a:b], levels)
            self.rivers_info.append(info)

    def paint_river(self, samples, levels, width):
        hw = width / 2.0
        hw_wet = max(hw, 2.9)        # at 4-block pixels a narrow river needs this to stay connected
        band = hw + VALLEY
        best = {}
        w = self.w
        for k in range(len(samples) - 1 if len(samples) > 1 else 1):
            ax, az, _ = samples[k]
            bx, bz, _ = samples[min(k + 1, len(samples) - 1)]
            i0, i1, j0, j1 = self.px_range(min(ax, bx) - band, min(az, bz) - band, max(ax, bx) + band,
                                           max(az, bz) + band)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
                    d, t = seg_dist(x, z, ax, az, bx, bz)
                    if d > band:
                        continue
                    g = j * w + i
                    lv = levels[k] if t < 0.5 or k + 1 >= len(levels) else levels[k + 1]
                    old = best.get(g)
                    if old is None or d < old[0]:
                        best[g] = (d, lv)
        for g, (d, lv) in sorted(best.items()):
            if self.wkind[g] == 1 or not self.land[g]:
                continue
            if d <= hw_wet:
                if self.wkind[g] == 2 and self.water[g] - WATER_OFFSET <= lv:
                    continue
                self.water[g] = lv + WATER_OFFSET
                self.wkind[g] = 2
                q = min(d / hw_wet, 1.0)
                self.H[g] = lv - 1 - 3 * (1 - q * q)
                self.floor[g] = -INF
                self.rug[g] = 0.0
            elif self.wkind[g] == 0:
                dd = d - hw_wet
                lo = lv + 2 - max(0.0, dd - 4)
                hi = lv + 2 + dd
                self.H[g] = min(max(self.H[g], lo), hi)
                self.floor[g] = max(self.floor[g], lo)
                if dd < 16:
                    self.rug[g] = min(self.rug[g], 0.5 * smoothstep(dd / 16))

    # ---- sites
    def sites(self):
        reqs = self.reqs
        out = []
        for s in self.shapes["sites"]:
            sid = s.get("data-id")
            if not sid or s.r is None:
                self.warn("%s: a site needs data-id and r" % s.label)
                continue
            kind = s.get("data-site", "clearing")
            t = Site(sid, kind, s.cx, s.cy, s.r, self.anchors.get(sid), reqs.get(sid), self.ov.get(sid))
            t.margin = s.num("data-margin", self.o.site_margin)
            if t.r > t.svg_r:
                self.warn("site %s: drawn r %d is smaller than its build needs (min_r %d); using %d" % (
                    sid, t.svg_r, t.r, t.r))
            out.append(t)
        # relative anchors (of/dx/dz) follow their parent, as gen_data requires
        by_id = {t.id: t for t in out}
        for t in out:
            a = t.anchor
            if a.get("of") and a["of"] in by_id:
                p = by_id[a["of"]]
                x, z = p.x + a.get("dx", 0), p.z + a.get("dz", 0)
                if math.hypot(x - t.x, z - t.z) > 8:
                    self.warn("site %s: drawn %d blocks from %s + (%d, %d); the anchor keeps the offset" % (
                        t.id, math.hypot(x - t.x, z - t.z), p.id, a.get("dx", 0), a.get("dz", 0)))
                t.x, t.z = x, z
        self.site_list = out
        plated = [t for t in out if t.plated]
        for n, t in enumerate(plated):
            t.index = n + 1
            if n + 1 > 255:
                raise MapError("more than 255 plated sites")
            self.plate(t)

    def pin_grounds(self):
        """Pins and spots only pin coordinates: y = the surface (or the water level) under them."""
        for t in self.site_list:
            if not t.plated:
                i, j = self.pix(t.x, t.z)
                g = j * self.w + i if 0 <= i < self.w and 0 <= j < self.h else None
                if g is not None and self.wkind[g]:
                    t.ground = int(self.water[g]) - WATER_OFFSET
                else:
                    t.ground = int(math.floor(self.sample(t.x, t.z) + 0.5))

    def disc(self, t, radius):
        """(g, distance) of the pixels within `radius` of the site centre."""
        w = self.w
        i0, i1, j0, j1 = self.px_range(t.x - radius, t.z - radius, t.x + radius, t.z + radius)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
                d = math.hypot(x - t.x, z - t.z)
                if d <= radius:
                    yield j * w + i, d, x, z

    def nearest_water(self, t, radius):
        best = None
        for g, d, _, _ in self.disc(t, radius):
            if self.wkind[g] in (1, 2) and (best is None or d < best[0]):
                best = (d, int(self.water[g]) - WATER_OFFSET, g)
        return best

    def plate(self, t):
        H, land = self.H, self.land
        wetkinds = ("lakeside", "coast")
        water_ok = t.kind in wetkinds
        ground = self.ov.get(t.id, {}).get("plate_y")
        near = self.nearest_water(t, t.r + 32) if t.kind == "lakeside" else None
        if ground is None:
            if near is not None:
                ground = near[1] - 1 if t.surface == "water" else near[1] + 2
            elif t.kind == "carve":
                ground = self.carve_ground(t)
            else:
                vals = [H[g] for g, d, _, _ in self.disc(t, t.r) if land[g] and not self.wkind[g]]
                vals = vals or [H[g] for g, d, _, _ in self.disc(t, t.r)]
                ground = statistics.median(vals) if vals else SEA + 2
                ground = max(int(math.floor(ground + 0.5)), SEA + 2)
        t.ground = int(ground)
        if t.kind == "lakeside" and near is None:
            self.warn("site %s: lakeside without a lake or river within r + 32" % t.id)
        under = t.surface == "water" and near is not None
        reach = t.r + (max(t.fade, 2 * VALLEY) if t.kind == "plateau" else t.fade)
        sm = t.margin
        for g, d, x, z in self.disc(t, max(reach, t.r + sm)):
            if d <= t.r + sm:
                self.excl[g] |= EXCL["site"]
            if d > reach:
                continue
            wet = self.wkind[g] in (1, 2) or not land[g]
            if d <= t.r:
                self.site[g] = t.index
            if t.kind == "carve":
                if d <= t.r:
                    self.rug[g] = min(self.rug[g], 0.3)
                continue
            if wet and water_ok and not under:
                continue
            if d <= t.r:
                if under:
                    self.water[g] = t.ground + 1 + WATER_OFFSET
                    self.wkind[g] = 3
                    H[g] = t.ground
                else:
                    if self.wkind[g] in (1, 2):
                        self.warn("site %s: its plate covers designed water at (%d, %d)" % (t.id, x, z))
                    self.water[g] = 0
                    self.wkind[g] = 0
                    H[g] = t.ground
                    land[g] = 1
                self.floor[g] = -INF
                self.rug[g] = 0.0
                continue
            q = (d - t.r) / t.fade if t.fade else 1.0
            if self.wkind[g]:
                continue
            if t.kind == "plateau":
                if H[g] >= t.ground:
                    H[g] = t.ground + (H[g] - t.ground) * smoothstep((d - t.r) / 8.0)
                else:
                    H[g] = max(H[g], t.ground - (d - t.r) / 2.0)
            else:
                H[g] = t.ground + (H[g] - t.ground) * smoothstep(q)
            self.rug[g] *= smoothstep(q)
        if t.kind == "carve":
            self.carve(t)

    def carve_ground(self, t):
        dx, dz = facing_vector(t.facing if t.facing != "auto" else "south")
        vals = [self.H[g] for g, d, x, z in self.disc(t, t.r + t.fade)
                if d >= t.r and (x - t.x) * dx + (z - t.z) * dz > 0.7 * d and self.land[g]]
        if not vals:
            vals = [self.H[g] for g, d, _, _ in self.disc(t, t.r)]
        return max(int(math.floor(statistics.median(vals) + 0.5)), SEA + 2) if vals else SEA + 2

    def carve(self, t):
        """Raise the massif over the roof columns (cover), mark the cavity, cut the approach ravine."""
        req = t.req
        w = self.w
        if req.get("box"):
            sx, sz = req["box"]
            ax, _, az = req["anchor"]
            m = req.get("margin", 8) + CAVITY_MARGIN
            bx0, bz0 = t.x - ax, t.z - az
            i0, i1, j0, j1 = self.px_range(bx0 - m, bz0 - m, bx0 + sx + m, bz0 + sz + m)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    self.excl[j * w + i] |= EXCL["cavity"]
            need = {}
            for (bx, bz), rel in req.get("roof_cols", {}).items():
                i, j = self.pix(bx0 + bx + 0.5, bz0 + bz + 0.5)
                if 0 <= i < w and 0 <= j < self.h:
                    g = j * w + i
                    v = t.ground + rel + t.cover
                    if v > need.get(g, -INF):
                        need[g] = v
            # dilate one pixel (bilinear sampling between pixels stays >= the cover) then a 1:1 batter
            grown = {}
            for g, v in need.items():
                i, j = g % w, g // w
                for b in range(-1, 2):
                    for a in range(-1, 2):
                        if 0 <= i + a < w and 0 <= j + b < self.h:
                            k = (j + b) * w + i + a
                            if v > grown.get(k, -INF):
                                grown[k] = v
            for g, v in grown.items():
                i, j = g % w, g // w
                for b in range(-6, 7):
                    for a in range(-6, 7):
                        if 0 <= i + a < w and 0 <= j + b < self.h:
                            k = (j + b) * w + i + a
                            vv = v - PX * max(abs(a), abs(b))
                            if vv > self.floor[k]:
                                self.floor[k] = vv
                if v > self.H[g]:
                    self.H[g] = v
            facing = t.facing if t.facing != "auto" else "south"
            (ox, oz), half_w = opening(req, facing, bx0, bz0)
            self.ravine(t, ox, oz, facing, half_w, set(grown))
        else:
            self.ravine(t, t.x, t.z, t.facing if t.facing != "auto" else "south", 8.0, set())

    def ravine(self, t, ox, oz, facing, half_w, keep):
        """The approach: from the opening on the box's `facing` edge out to r + fade at the gate's level, 1:1
        walls. Pixels in `keep` (the roof cover and its one-pixel guard) are never cut."""
        dx, dz = facing_vector(facing)
        length = t.r + t.fade
        w = self.w
        reach = length + half_w + VALLEY
        i0, i1, j0, j1 = self.px_range(ox - reach, oz - reach, ox + reach, oz + reach)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                g = j * w + i
                if g in keep:
                    continue
                x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
                along = (x - ox) * dx + (z - oz) * dz
                across = abs((x - ox) * -dz + (z - oz) * dx)
                if along < -PX or along > length or across > half_w + VALLEY:
                    continue
                lid = t.ground + max(0.0, across - half_w)
                if lid < self.H[g]:
                    self.H[g] = lid
                if self.floor[g] > lid:
                    self.floor[g] = lid

    # ---- roads
    def roads(self):
        w = self.w
        for n, s in enumerate(self.shapes["roads"]):
            if len(s.pts) < 2:
                continue
            kind = s.get("data-kind", "trail")
            if kind not in ROAD_HALF:
                self.warn("%s: data-kind %r is not main or trail; drawn as a trail" % (s.label, kind))
                kind = "trail"
            half = ROAD_HALF[kind]
            corridor = half + 3
            rmargin = s.num("data-margin", self.o.road_margin)
            rid = s.get("data-id") or self.road_id(s.pts, n)
            samples = densify(s.pts, PX)
            ys, wet, levels = [], [], []
            for x, z, _ in samples:
                i, j = self.pix(x, z)
                g = j * w + i if 0 <= i < w and 0 <= j < self.h else None
                is_wet = g is None or not self.land[g] or self.wkind[g] in (1, 2)
                wet.append(is_wet)
                levels.append(int(self.water[g]) - WATER_OFFSET if g is not None and self.wkind[g] else SEA)
                ys.append(self.sample(x, z))
            prof = road_profile(ys, wet, levels)
            runs = wet_runs(wet)
            for a, b in runs:
                length = (b - a + 1) * PX
                if length > BRIDGE_MAX:
                    self.warn("road %s: a %d-block wet run (bridges are at most %d)" % (rid, length, BRIDGE_MAX))
            best = {}
            band = max(corridor + VALLEY, corridor + rmargin)
            for k in range(len(samples) - 1):
                ax, az, _ = samples[k]
                bx, bz, _ = samples[k + 1]
                i0, i1, j0, j1 = self.px_range(min(ax, bx) - band, min(az, bz) - band, max(ax, bx) + band,
                                               max(az, bz) + band)
                for j in range(j0, j1 + 1):
                    for i in range(i0, i1 + 1):
                        x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
                        d, t = seg_dist(x, z, ax, az, bx, bz)
                        if d > band:
                            continue
                        g = j * w + i
                        old = best.get(g)
                        if old is None or d < old[0]:
                            best[g] = (d, prof[k] + (prof[k + 1] - prof[k]) * t, wet[k] or wet[k + 1])
            surf = ROAD_CLASS[kind]
            bridge = ROAD_CLASS[kind + "_bridge"]
            for g, (d, y, on_wet) in sorted(best.items()):
                if d <= corridor + rmargin:
                    self.excl[g] |= EXCL["road"]
                in_site = self.site[g] != 0
                wet_px = not self.land[g] or self.wkind[g] in (1, 2)
                if d <= half + 2.0:
                    c = bridge if wet_px else surf
                elif d <= corridor + 2.0:
                    c = bridge if wet_px and d <= half + 3.0 else ROAD_CLASS["corridor"]
                else:
                    c = 0
                if c > self.road[g]:
                    self.road[g] = c
                if wet_px or in_site or self.wkind[g]:
                    continue
                if d <= corridor:
                    self.H[g] = y
                    self.rug[g] = 0.0
                elif d <= corridor + VALLEY:
                    dd = d - corridor
                    self.H[g] = clamp(self.H[g], y - dd, y + dd)
                    if dd < 8:
                        self.rug[g] = min(self.rug[g], 0.3 * dd / 8)
            pts = [[round(x, 1), round(z, 1), round(prof[k], 2), 1 if wet[k] else 0]
                   for k, (x, z, _) in enumerate(samples)]
            self.roads_info.append({"id": rid, "kind": kind, "half": half, "corridor": corridor, "margin": rmargin,
                                    "points": pts,
                                    "bridges": [[a * PX, (b - a + 1) * PX] for a, b in runs]})

    def road_id(self, pts, n):
        def nearest(p):
            best = None
            for s in self.shapes["sites"]:
                if s.r is None or not s.get("data-id"):
                    continue
                d = math.hypot(p[0] - s.cx, p[1] - s.cy) - s.r
                if best is None or d < best[0]:
                    best = (d, s.get("data-id"))
            return best[1] if best and best[0] <= 64 else None
        a, b = nearest(pts[0]), nearest(pts[-1])
        return "%s_%s" % (a, b) if a and b else "road_%d" % (n + 1)

    # ---- biomes
    def biomes(self):
        w, h, n = self.w, self.h, self.n
        explicit = [None]
        poly = bytearray(n)
        for s in self.shapes["biomes"]:
            b = s.get("data-biome")
            if not s.closed or not b:
                continue
            if b not in ALLOWED_BIOMES:
                raise MapError("%s: data-biome %r is not an allowed biome (design §2.2.1)" % (s.label, b))
            if b not in explicit:
                explicit.append(b)
            fill_polygon(s.pts, self.x0, self.z0, PX, w, h, poly, explicit.index(b))
        forests = [None]
        fmask = bytearray(n)
        ftypes = dict(FOREST_BIOMES)
        ftypes.update({k: v for k, v in self.ov.get("forest", {}).items() if isinstance(v, str)})
        for s in self.shapes["forests"]:
            t = s.get("data-type")
            if not s.closed or not t:
                continue
            if t not in ftypes:
                raise MapError("%s: data-type %r is not a forest type (%s)" % (s.label, t, ", ".join(FOREST_BIOMES)))
            b = ftypes[t]
            if b not in forests:
                forests.append(b)
            fill_polygon(s.pts, self.x0, self.z0, PX, w, h, fmask, forests.index(b))
        regions = self.region_cells()
        defaults = {k: v.get("default_biome") for k, v in self.ov.get("region", {}).items() if isinstance(v, dict)}
        site_b = [None] * (len(self.site_list) + 1)
        for t in self.site_list:
            if t.plated and t.index:
                b = t.biome or (None if t.kind == "carve" else "minecraft:plains")
                if b is not None and b not in ALLOWED_BIOMES:
                    raise MapError("sites.toml %s: biome %r is not allowed" % (t.id, b))
                site_b[t.index] = b
        tempest = next((t for t in self.site_list if t.id == "tempest"), None)
        coast = self.coast_strip()
        out = [None] * n
        H, rug, land, wk, site = self.H, self.rug, self.land, self.wkind, self.site
        cw = self.cw
        for g in range(n):
            if not land[g]:
                out[g] = "#ocean"
                continue
            i, j = g % w, g // w
            letter = regions[(j // K) * cw + i // K]
            if poly[g]:
                out[g] = explicit[poly[g]]
                continue
            if site[g] and site_b[site[g]]:
                out[g] = site_b[site[g]]
                continue
            if tempest is not None and (letter in ("J", None)):
                x, z = self.x0 + (i + 0.5) * PX, self.z0 + (j + 0.5) * PX
                d = math.hypot(x - tempest.x, z - tempest.z)
                if d < JURA_CORE:
                    out[g] = "tensura:ancient_forest"
                    continue
                if d < JURA_BAND:
                    out[g] = "minecraft:dark_forest"
                    continue
            if fmask[g]:
                out[g] = forests[fmask[g]]
                continue
            snowy = is_snowy(defaults.get(letter))
            if wk[g]:
                out[g] = "minecraft:frozen_river" if snowy else "minecraft:river"
                continue
            if coast[g]:
                if snowy:
                    out[g] = "minecraft:snowy_beach"
                elif H[g] <= SEA + 3 and rug[g] < 0.5:
                    out[g] = "minecraft:beach"
                else:
                    out[g] = "minecraft:stony_shore"
                continue
            hit = None
            for b, y, r in PEAKS:
                if H[g] >= y and rug[g] >= r:
                    hit = b
                    break
            if hit:
                out[g] = hit
                continue
            out[g] = defaults.get(letter) or "minecraft:plains"
        used = sorted(set(out) - {"#ocean"})
        bad = [b for b in used if b not in ALLOWED_BIOMES and b not in AUTO_BIOMES]
        if bad:
            raise MapError("sites.toml region/forest defaults name biomes that are not allowed: %s" % ", ".join(bad))
        self.paint_biomes(out, site, site_b)
        used = sorted(set(out) - {"#ocean"})
        self.biome_list = ["#ocean"] + used
        index = {b: k for k, b in enumerate(self.biome_list)}
        self.biome = bytes(index[b] for b in out)

    # ---- paint (world/paint/, tools/world/paint.py): after the relief, before water, sites and roads
    def _paint_range(self, layer):
        p = self.paint
        data = getattr(p, layer)
        if data is None:
            return None
        cols = [k % p.w for k, v in enumerate(data) if v != (0 if layer == "biome" else 128)]
        rows = [k // p.w for k, v in enumerate(data) if v != (0 if layer == "biome" else 128)]
        if not cols:
            return None
        pad = p.px  # bilinear height reaches one paint pixel further
        return self.px_range(p.x0 + min(cols) * p.px - pad, p.z0 + min(rows) * p.px - pad,
                             p.x0 + (max(cols) + 1) * p.px + pad, p.z0 + (max(rows) + 1) * p.px + pad)

    def apply_paint(self):
        if self.paint is None:
            return
        w, H, rug, land, p = self.w, self.H, self.rug, self.land, self.paint
        raised = lowered = 0
        rng = self._paint_range("height")
        if rng:
            i0, i1, j0, j1 = rng
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    g = j * w + i
                    if not land[g]:
                        continue
                    x, z = self.centre(i, j)
                    d = p.height_at(x, z)
                    if d:
                        # Painted land never drops into the sea: the coast is the SVG's.
                        H[g] = max(SEA + 1.0, H[g] + d)
                        raised += d > 0
                        lowered += d < 0
        rng = self._paint_range("rugged")
        if rng:
            i0, i1, j0, j1 = rng
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    g = j * w + i
                    if land[g]:
                        d = p.rugged_at(*self.centre(i, j))
                        if d:
                            rug[g] = clamp(rug[g] + d, 0.0, 1.0)
        self.paint_stats = {"raised_px": raised, "lowered_px": lowered}
        if p.bad_colours:
            self.warn("paint: %d biome.png pixels have colours not in legend.json (ignored; python -I tools/world/paint.py status)"
                      % sum(p.bad_colours.values()))

    def paint_biomes(self, out, site, site_b):
        """Painted biomes win over the SVG's biomes, forests and the Jura rings; site plates and water keep theirs."""
        if self.paint is None or self.paint.biome is None:
            return
        rng = self._paint_range("biome")
        if not rng:
            return
        w, land, wk = self.w, self.land, self.wkind
        i0, i1, j0, j1 = rng
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                g = j * w + i
                if not land[g] or wk[g] or (site[g] and site_b[site[g]]):
                    continue
                b = self.paint.biome_at(*self.centre(i, j))
                if b:
                    if b not in ALLOWED_BIOMES:
                        raise MapError("world/paint/biome.png paints %r, not an allowed biome (tools/world/biomes.txt)" % b)
                    out[g] = b

    def coast_strip(self):
        """Land pixels within ~2 pixels of the sea (the exact coast distance is known in the band)."""
        land, sd = self.land, self.sd
        return bytes(1 if land[g] and sd[g] < 2.5 * PX else 0 for g in range(self.n))

    def region_cells(self):
        """Region letter per coarse cell (= chunk): the polygon holding the centre (later polygons win), land cells
        outside every polygon take the nearest lettered cell; None on the open sea."""
        cw, ch = self.cw, self.ch
        letters = [None]
        mask = bytearray(cw * ch)
        for s in self.shapes["regions"]:
            le = s.get("data-letter")
            if not s.closed or not le:
                continue
            if le not in letters:
                letters.append(le)
            fill_polygon(s.pts, self.x0, self.z0, CELL, cw, ch, mask, letters.index(le))
        out = [letters[m] if m else None for m in mask]
        if len(letters) > 1:
            # chunk land: any fine land pixel in it
            land_c = bytearray(cw * ch)
            w = self.w
            for g in range(self.n):
                if self.land[g]:
                    land_c[((g // w) // K) * cw + (g % w) // K] = 1
            todo = [k for k in range(cw * ch) if land_c[k] and out[k] is None]
            if todo:
                frontier = [k for k in range(cw * ch) if out[k] is not None]
                seen = bytearray(cw * ch)
                for k in frontier:
                    seen[k] = 1
                for _ in range(64):
                    nxt = []
                    for k in frontier:
                        i, j = k % cw, k // cw
                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            if 0 <= i + a < cw and 0 <= j + b < ch:
                                q = (j + b) * cw + i + a
                                if not seen[q]:
                                    seen[q] = 1
                                    out[q] = out[k]
                                    nxt.append(q)
                    frontier = nxt
                    if not frontier:
                        break
                for k in range(cw * ch):
                    if not land_c[k] and mask[k] == 0:
                        out[k] = None
                    elif land_c[k] and out[k] is None:
                        self.warn("land chunk at (%d, %d) has no region within 64 chunks" % (
                            self.x0 + (k % cw) * CELL, self.z0 + (k // cw) * CELL))
        self.region_c = out
        return out

    # ---- run
    def run(self):
        self.setup()
        self.coarse_base()
        self.fine_land()
        self.features()
        self.relief()
        self.apply_paint()
        self.lakes()
        self.rivers()
        self.sites()
        self.roads()
        H, fl = self.H, self.floor
        for g in range(self.n):
            v = H[g]
            if fl[g] > v and not self.wkind[g]:
                v = fl[g]
            H[g] = clamp(v, -60.0, 318.0)
        self.pin_grounds()
        self.biomes()
        return self


def base_height(s):
    """The designed surface at signed distance s from the coast (blocks, + inland)."""
    if s >= 0:
        return SEA + 1.5 * min(s, 16.0) / 16.0 + 9.0 * smoothstep((s - 16.0) / 600.0)
    d = -s
    if d <= SHELF:
        return SEA - 1 - (SEA - 1 - SHELF_Y) * d / SHELF
    if d <= DEEP_AT:
        return SHELF_Y - (SHELF_Y - DEEP_Y) * smoothstep((d - SHELF) / (DEEP_AT - SHELF))
    return DEEP_Y


def noise_weight(s):
    return smoothstep(s / 200.0) if s > 0 else 0.0


def mesa(t):
    return smoothstep(min(1.0, t / 0.3))


def opening(req, facing, bx0, bz0):
    """((x, z) world point at the middle of the gate opening on the box's `facing` edge, half width): the run of
    roofless columns on that edge row nearest the anchor (Dwargon: the forecourt, ~20 wide)."""
    sx, sz = req["box"]
    ax, _, az = req["anchor"]
    roof = req.get("roof_cols", {})
    if facing in ("south", "north"):
        bz = sz - 1 if facing == "south" else 0
        cells = [(b, bz) for b in range(sx)]
        key = ax
    else:
        bx = sx - 1 if facing == "east" else 0
        cells = [(bx, b) for b in range(sz)]
        key = az
    open_ = [c not in roof for c in cells]
    runs, k = [], 0
    while k < len(cells):
        if open_[k]:
            a = k
            while k < len(cells) and open_[k]:
                k += 1
            runs.append((a, k - 1))
        else:
            k += 1
    if not runs:
        a = b = key
    else:
        a, b = min(runs, key=lambda r: (0 if r[0] <= key <= r[1] else min(abs(r[0] - key), abs(r[1] - key)),
                                        -(r[1] - r[0])))
    mid = (a + b + 1) / 2.0
    half = max(4.0, (b - a + 1) / 2.0)
    if facing in ("south", "north"):
        return (bx0 + mid, bz0 + (sz if facing == "south" else 0)), half
    return (bx0 + (sx if facing == "east" else 0), bz0 + mid), half


def facing_vector(f):
    return {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}.get(f, (0, 1))


def is_snowy(biome):
    return bool(biome) and any(k in biome for k in ("snow", "frozen", "ice"))


def svg_point_in(pt, poly):
    x, z = pt
    inside = False
    n = len(poly)
    for k in range(n):
        ax, az = poly[k]
        bx, bz = poly[(k + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az):
            inside = not inside
    return inside


def wet_runs(wet):
    runs, k = [], 0
    while k < len(wet):
        if wet[k]:
            a = k
            while k < len(wet) and wet[k]:
                k += 1
            runs.append((a, k - 1))
        else:
            k += 1
    return runs


def road_profile(ys, wet, levels):
    """Walking level along a road every 4 blocks: running median (7 samples) of the dry terrain, decks 2 above the
    water on wet runs, grade <= 1:2 (2 blocks per sample) as the mean of the upper and lower envelopes."""
    n = len(ys)
    dry = [ys[k] for k in range(n) if not wet[k]]
    if not dry:
        dry = [SEA + 2.0]
    base = []
    for k in range(n):
        win = [ys[q] for q in range(max(0, k - 3), min(n, k + 4)) if not wet[q]]
        base.append(statistics.median(win) if win else None)
    last = next(v for v in base if v is not None) if any(v is not None for v in base) else dry[0]
    for k in range(n):
        if base[k] is None:
            base[k] = last
        last = base[k]
    step = ROAD_GRADE * PX
    for a, b in wet_runs(wet):
        deck = max(levels[a:b + 1]) + 2
        for k in range(a, b + 1):
            base[k] = max(base[k], deck)
    up, lo = list(base), list(base)
    for k in range(1, n):
        up[k] = max(up[k], up[k - 1] - step)
        lo[k] = min(lo[k], lo[k - 1] + step)
    for k in range(n - 2, -1, -1):
        up[k] = max(up[k], up[k + 1] - step)
        lo[k] = min(lo[k], lo[k + 1] + step)
    prof = [(u + v) / 2 for u, v in zip(up, lo)]
    for a, b in wet_runs(wet):
        deck = max(levels[a:b + 1]) + 2
        for k in range(a, b + 1):
            prof[k] = max(prof[k], deck)
    for k in range(1, n):
        prof[k] = max(prof[k], prof[k - 1] - step)
    for k in range(n - 2, -1, -1):
        prof[k] = max(prof[k], prof[k + 1] - step)
    return prof


def reach_levels(terr, head, mouth, seed):
    """Water level per sample (4 blocks apart): flat reaches from head down to mouth, a step of 1-2 blocks after at
    least 40 (+ seeded 0..24) blocks wherever the terrain wants the water lower (level <= terrain - 2), and earlier
    when the mouth could not be reached otherwise."""
    n = len(terr)
    want, low = [], INF
    for v in terr:
        low = min(low, v - 2)
        want.append(max(mouth, min(head, int(math.floor(low)))))
    out = []
    cur, last, steps = head, 0, 0
    reach = MIN_REACH + int(_hash01(steps, 0, seed) * MAX_REACH_JITTER)
    for k in range(n):
        pos = k * PX
        rem = (n - 1 - k) * PX
        cap = mouth + MAX_STEP * int(rem // MIN_REACH)
        target = min(want[k], cap)
        if cur > target and (pos - last >= reach or cur > cap):
            drop = min(MAX_STEP, cur - target) if cur <= cap else cur - cap
            cur -= max(1, drop)
            last = pos
            steps += 1
            reach = MIN_REACH + int(_hash01(steps, 0, seed) * MAX_REACH_JITTER)
        out.append(cur)
    if out:
        out[-1] = max(out[-1], mouth)
    return out


def reach_summary(samples, levels):
    out, a = [], 0
    for k in range(1, len(levels) + 1):
        if k == len(levels) or levels[k] != levels[a]:
            out.append({"level": levels[a], "from": [round(samples[a][0]), round(samples[a][1])],
                        "to": [round(samples[k - 1][0]), round(samples[k - 1][1])], "length": (k - a) * PX})
            a = k
    return out


# ----------------------------------------------------------------------------------------------------------- output

def legend(world):
    sites = []
    for t in world.site_list:
        rec = {"id": t.id, "kind": t.kind, "x": int(round(t.x)), "z": int(round(t.z)), "r": int(round(t.r)),
               "plated": t.plated, "y": t.ground}
        if t.plated:
            rec.update({"index": t.index, "fade": t.fade, "biome": t.biome, "margin": t.margin})
            if t.svg_r != t.r:
                rec["svg_r"] = int(round(t.svg_r))
            if t.kind == "carve":
                rec["cover"] = t.cover
        sites.append(rec)
    return {
        "what": "Own-world generator rasters (tools/world/svg2rasters.py, design/architecture/own-world.md).",
        "version": 1,
        "source_sha256": world.source_hash,
        "paint": (dict(world.paint.frame, sha256=world.paint.fingerprint(), **getattr(world, "paint_stats", {}))
                  if world.paint is not None else None),
        "seed": world.o.seed,
        "box": {"x0": world.x0, "z0": world.z0, "x1": world.x0 + world.w * PX, "z1": world.z0 + world.h * PX,
                "width_px": world.w, "height_px": world.h, "content": [round(v) for v in world.content],
                "sea_margin": world.o.sea_margin, "region": world.o.region},
        "pixel": {"blocks": PX, "sample": "centre", "rows": "north to south (+z)",
                  "world_to_px": "u = (x - x0) / 4 - 0.5, v = (z - z0) / 4 - 0.5 (pixel centres)"},
        "sea_level": SEA,
        "files": {
            "height": {"file": "height.png", "format": "gray16", "value": "round((H + 64) * 16)", "scale": SCALE,
                       "offset": 64, "meaning": "H = designed surface = y of the first air block; offset = (H-128)/128"},
            "rugged": {"file": "rugged.png", "format": "gray8", "value": "round(rugged * 255)",
                       "classes": RUGGED["classes"], "factor": RUGGED["factor"], "jaggedness": RUGGED["jaggedness"]},
            "water": {"file": "water.png", "format": "gray16", "value": "0 = dry, else level + 64",
                      "offset": WATER_OFFSET,
                      "meaning": "level = y of the first air above the water; fill sources from the bed to level - 1"},
            "road": {"file": "road.png", "format": "gray8", "classes": ROAD_CLASS},
            "biome": {"file": "biome.png", "format": "palette8", "biomes": world.biome_list,
                      "auto": {"#ocean": "vanilla's ocean biome by depth and temperature"}},
            "sites": {"file": "sites.png", "format": "gray8", "value": "1-based index into sites (plated, inside r)"},
            "exclude": {"file": "exclude.png", "format": "gray8", "bits": EXCL,
                        "margins": {"site": world.o.site_margin, "road": world.o.road_margin,
                                    "cavity": CAVITY_MARGIN}},
        },
        "jura": {"core": JURA_CORE, "band": JURA_BAND, "core_biome": "tensura:ancient_forest",
                 "band_biome": "minecraft:dark_forest"},
        "sites": sites,
        "lakes": [{k: v for k, v in lk.items() if k != "pts"} for lk in world.lakes_info],
        "rivers": world.rivers_info,
        "roads": [{k: v for k, v in r.items() if k != "points"} for r in world.roads_info],
        "warnings": world.warnings,
    }


def sites_json(world):
    out = []
    for t in world.site_list:
        if not t.plated or t.kind == "carve":
            continue
        radius = t.r
        if t.kind in ("lakeside", "coast") and t.surface != "water":
            near = None
            for g, d, _, _ in world.disc(t, t.r):
                if world.wkind[g] in (1, 2) or not world.land[g]:
                    near = d if near is None else min(near, d)
            if near is not None:
                radius = max(8.0, near - 4.0)
        rec = {"name": t.id, "centre": [int(round(t.x)), int(round(t.z))], "radius": int(round(radius)),
               "fade": t.fade, "terrain": "flat", "ground": t.ground}
        b = t.biome or "minecraft:plains"
        rec["biomes"] = [[b, 1]]
        out.append(rec)
    return {"_doc": "GENERATED by tools/world/svg2rasters.py: the own world's flat sites (CanonSites schema).",
            "sites": out}


def canon_map(world):
    w, cw, ch = world.w, world.cw, world.ch
    sea = [0] * (cw * ch)
    wet = [0] * (cw * ch)
    for g in range(world.n):
        c = ((g // w) // K) * cw + (g % w) // K
        if not world.land[g]:
            sea[c] += 1
        elif world.wkind[g] in (1, 2, 3):
            wet[c] += 1
    rows = []
    for j in range(ch):
        row = []
        for i in range(cw):
            c = j * cw + i
            if sea[c] >= K * K // 2:
                row.append(".")
            elif wet[c] >= K * K // 2:
                row.append("~")
            else:
                row.append(world.region_c[c] or ".")
        rows.append("".join(row))
    head = [
        "# Canon continent of the own Tensura world, one character per chunk (16x16 blocks). GENERATED by",
        "# tools/world/svg2rasters.py from world/map.svg (coast, lakes, rivers, regions); do not edit by hand.",
        "# '.' open sea, '~' lake/river, letters = nations.",
        "# origin %d %d  (this cell's north-west corner is world 0, 0)" % (-world.x0 // CELL, -world.z0 // CELL),
    ]
    return "\n".join(head + rows) + "\n"


def write_outputs(world, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = world.w, world.h
    pngcodec.write_png(out / "height.png", w, h, [int(round((v + 64) * SCALE)) for v in world.H], depth=16)
    pngcodec.write_png(out / "rugged.png", w, h, bytes(int(round(clamp(v, 0.0, 1.0) * 255)) for v in world.rug))
    pngcodec.write_png(out / "water.png", w, h, world.water, depth=16)
    pngcodec.write_png(out / "road.png", w, h, world.road)
    pal = [BIOME_COLOURS.get(b, tuple(hashlib.sha256(b.encode()).digest()[:3])) for b in world.biome_list]
    pngcodec.write_png(out / "biome.png", w, h, world.biome, palette=pal)
    pngcodec.write_png(out / "sites.png", w, h, world.site)
    pngcodec.write_png(out / "exclude.png", w, h, world.excl)
    dump = lambda p, d: Path(p).write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8", newline="\n")  # noqa
    dump(out / "index.json", legend(world))
    dump(out / "sites.json", sites_json(world))
    dump(out / "roads.json", {"roads": world.roads_info})
    (out / "canon_map.txt").write_text(canon_map(world), encoding="utf-8", newline="\n")


def build(svg_text, opts=None, sites_toml=None, anchors=None, sources=None, paint=None):
    """Parse + rasterise. Returns the World (raises MapError on a fatal map problem)."""
    opts = opts or Options()
    rep = svgparse.Report()
    shapes = svgparse.parse_svg(svg_text, rep)
    if shapes is None or rep.errors:
        raise MapError("; ".join(e["message"] for e in rep.errors))
    overrides = site_overrides(sites_toml)
    src = sources
    if src is None and anchors is None:
        src = sfb.Sources()
    anchors = anchors if anchors is not None else src.anchors
    kinds = {s.get("data-id"): s.get("data-site", "clearing") for s in shapes["sites"] if s.get("data-id")}
    reqs = {}
    if src is not None:
        full = sfb.requirements(src, kinds)
        reqs = {k: v for k, v in full.items() if k in kinds}
    sha = hashlib.sha256(svg_text.encode("utf-8")).hexdigest()
    if paint is not None:  # the paint is part of the source: a paint change is a new build
        sha = hashlib.sha256((sha + paint.fingerprint()).encode("utf-8")).hexdigest()
    world = World(shapes, opts, anchors, overrides, reqs, sha, paint)
    for wmsg in rep.warnings:
        world.warn(wmsg["message"])
    return world.run()


def main(argv=None):
    ap = argparse.ArgumentParser(description="world/map.svg -> pack/config/ttl/world/*.png (own world WP-W1)")
    ap.add_argument("svg", nargs="?", default=str(DEFAULT_SVG))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--sites", default=str(DEFAULT_SITES))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--sea-margin", type=int, default=SEA_MARGIN)
    ap.add_argument("--region", type=int, default=REGION)
    ap.add_argument("--paint", default=str(paint_mod.PAINT), help="paint layers folder ('' = no paint)")
    args = ap.parse_args(argv)
    text = Path(args.svg).read_text(encoding="utf-8")
    try:
        layers = paint_mod.load(args.paint) if args.paint else None
        world = build(text, Options(seed=args.seed, sea_margin=args.sea_margin, region=args.region), args.sites,
                      paint=layers)
    except MapError as e:
        print("svg2rasters: %s" % e, file=sys.stderr)
        return 1
    write_outputs(world, args.out)
    for wmsg in world.warnings:
        print("warn: " + wmsg, file=sys.stderr)
    print("wrote %s: %d x %d px (%d x %d blocks from %d, %d), %d biomes, %d sites, %d lakes, %d rivers, %d roads" % (
        args.out, world.w, world.h, world.w * PX, world.h * PX, world.x0, world.z0, len(world.biome_list),
        len(world.site_list), len(world.lakes_info), len(world.rivers_info), len(world.roads_info)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
