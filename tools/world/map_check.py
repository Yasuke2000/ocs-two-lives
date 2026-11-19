#!/usr/bin/env python3
"""Checker and previewer for world/map.svg, the layered block-coordinate map of OCS Two Lives' own Tensura world.

    python -I tools/world/map_check.py world/map.svg [--preview out.png] [--json] [--jar TENSURA.jar]
                                       [--anchors F] [--relations F] [--canon F] [--biomes F] [--landmarks F] [--sites F]

The format is described in world/README.md and in the comment at the top of world/map.svg; the design is
design/architecture/own-world.md (section 2 format, section 6.1 rules). In short: viewBox -8000 -6000 16000 12000 (block
coordinates, world 0,0 = Tempest, x east, y south = Minecraft z), named <g id=...> layers (coast lakes rivers mountains
hills forests biomes regions roads sites labels). The checker validates every rule of RULES, prints a readable report
(errors, warnings, stats, distances, canon relations) and exits 1 on errors. --preview renders a PNG at 1 px = 8 blocks.
Stdlib only; runs under `python -I`.
"""
import argparse
import importlib.util
import json
import math
import os
import re
import sys
import tomllib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANCHORS = ROOT / "design" / "data" / "anchors.toml"
DEFAULT_SITES = ROOT / "world" / "sites.toml"
DEFAULT_LANDMARKS = ROOT / "design" / "data" / "landmarks.toml"
DEFAULT_RELATIONS = ROOT / "tools" / "world" / "canon_relations.toml"
DEFAULT_CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
DEFAULT_BIOMES = ROOT / "tools" / "world" / "biomes.txt"
COMMON_PNG = ROOT / "tools" / "lerfing" / "common.py"

VIEWBOX = (-8000.0, -6000.0, 16000.0, 12000.0)
LAYERS = ("coast", "lakes", "rivers", "mountains", "hills", "forests", "biomes", "regions", "roads", "sites", "labels")
FOREST_TYPES = ("light", "dense", "dark", "ancient", "birch", "taiga", "old_taiga", "jungle", "sparse_jungle", "cherry",
                "mangrove")
SITE_KINDS = ("clearing", "plateau", "carve", "lakeside", "coast", "village")
ROAD_KINDS = ("main", "trail")
V1_ROADS = ("tempest_dwargon", "tempest_blumund", "blumund_englassia_lubelius", "dwargon_dwarf_village")
MOUNTAIN_SHAPES = ("alpine", "mesa", "dome")
HILL_SHAPES = ("rolling", "mesa")
AREAL = ("coast", "lakes", "mountains", "hills", "forests", "biomes", "regions")
RIVER_WIDTH = (4.0, 24.0)
PEAK_RANGE = (100.0, 300.0)
HILL_RANGE = (70.0, 150.0)
SITE_R = (8.0, 160.0)
POLY_NODES = (8, 400)
MARGIN_MAX = 256.0
SITE_MARGIN = 48.0       # default data-margin of a site (the generator's default too)
ANCHOR_DRIFT = 32.0      # a relative anchor's site may stand this far from parent + (dx, dz)
RIVER_MOUTH_SLACK = 16.0  # a river may end this far outside the coast
COAST_MIN = 48.0          # a site (except `coast`) is at least this far from the coast
TOUCH_SLACK = 16.0        # a coast / lakeside site's disc must reach the water within this slack
ROAD_END_SLACK = 32.0     # a road ends within this many blocks of a site (edge of its disc)
WET_RUN_MAX = 64.0        # longest stretch of water a road may cross (a bridge)
ROAD_REACH = 400.0        # a build site is on a road or within this far of one (warning)
SAMPLE_STEP = 4.0
REGION_STEP = 40.0
SEA_MARGIN = 1200.0
REGION_BLOCK = 512.0
MAINLAND_ERR = (11000.0, 8000.0)
MAINLAND_WARN = (10000.0, 7500.0)
BOX_CAP = (14336.0, 11264.0)
BOX_TARGET = (12288.0, 10240.0)
LAND_SHARE_MAX = 0.55
JURA_RING = 600.0
CURVE_STEPS = {"C": 16, "Q": 12}
PREVIEW_SCALE = 8        # blocks per pixel
WINDS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")

RULES = (
    "1 structure: viewBox -8000 -6000 16000 12000; exactly the 11 groups (unknown = error, missing labels = warning); "
    "no transform; no nested groups",
    "2 polygons: closed, 8..400 vertices, no self-intersection, all coordinates inside the viewBox",
    "3 attributes: rivers data-width 4..24; mountains data-peak 100..300; hills data-height 70..150; forests data-type; "
    "biomes data-biome (biomes.txt, checked against the jar when given); regions data-letter, every land sample in "
    "exactly one region, each letter once per landmass; roads data-kind; sites data-id (each anchor exactly once), "
    "data-site, r 8..160",
    "4 water: lakes, mountains, hills on land; rivers start on land and end in a lake or in the sea (<= 16 outside "
    "the coast); a river crossing a mountain warns",
    "5 sites: whole disc on land (coast/lakeside touch water), in the region of the anchor's letter, edge gap "
    "(distance - (r1_eff + r2_eff)) >= the larger data-margin (default 48) with r_eff = max(drawn r, min_r of "
    "world/sites.toml; anchors relative to each other via of/dx/dz are exempt), >= 48 from the coast, carve inside a mountain or hill, village r >= landmark reach; "
    "warnings: a circle drawn below its min_r, a relative anchor (of/dx/dz) more than 32 from parent + offset",
    "6 canon: direction + distance relations, site rules and sea gaps of tools/world/canon_relations.toml",
    "7 size: mainland <= 11,000 x 8,000 (warn 10,000 x 7,500); land <= 55 % of the design box; box <= 14,336 x 11,264 "
    "(warn above 12,288 x 10,240)",
    "8 roads: ends within 32 of a site, wet runs <= 64, the four v1 roads present; build sites on or within 400 of "
    "a road (warning)",
    "9 Jura: ancient or dark forest covers r 600 round Tempest (warning)",
    "10 exclusion margin: a site or road without data-margin warns (the generator blocks structure starts in site "
    "boxes + margin and on road corridors)",
)


class ParseError(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------------------
# Configuration (the data files the checker reads)

class Config:
    def __init__(self, anchors, letters, relations=None, biomes=None, colours=None, problems=None, site_rules=None,
                 gaps=None, reach=None, jar_problems=None, min_r=None):
        self.anchors = anchors                    # id -> {name, region, kind, surface, landmark, x, z}
        self.letters = set(letters)               # region letters of canon_regions.json
        self.relations = relations or []          # [[relation]]
        self.site_rules = site_rules or []        # [[site_rule]]
        self.gaps = gaps or []                    # [[gap]]
        self.biomes = set(biomes) if biomes is not None else None
        self.colours = colours or {}              # letter -> (r, g, b), only for the preview
        self.problems = problems or []            # mistakes in the data files themselves
        self.reach = reach or {}                  # landmark name -> reach
        self.jar_problems = jar_problems or []
        self.min_r = min_r or {}                  # site id -> smallest r the build needs (world/sites.toml), may be empty


def load_anchors(path):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    anchors = {}
    for key, val in data.items():
        if key == "keepout" or not isinstance(val, dict):
            continue
        anchors[key] = {
            "name": val.get("name", key), "region": val.get("region", ""), "kind": val.get("kind", ""),
            "surface": val.get("surface", "any"), "landmark": val.get("landmark"), "x": val.get("x"), "z": val.get("z"),
            "of": val.get("of"), "dx": val.get("dx", 0), "dz": val.get("dz", 0),
        }
    return anchors


def load_landmark_reach(path):
    if not path or not Path(path).is_file():
        return {}
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return {lm["name"]: lm["reach"] for lm in data.get("landmark", []) if "name" in lm and "reach" in lm}


def load_min_r(path):
    """{site id: min_r} from world/sites.toml; {} when the file is missing or unreadable (the SVG r then stands alone)."""
    if not path or not Path(path).is_file():
        return {}
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return {k: v["min_r"] for k, v in data.items()
            if isinstance(v, dict) and isinstance(v.get("min_r"), (int, float)) and not isinstance(v.get("min_r"), bool)}


def load_canon(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    regions = data.get("regions", {})
    return set(regions), {k: tuple(v.get("colour", (200, 200, 200))) for k, v in regions.items()}


def load_biomes(path):
    out = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line if ":" in line else "minecraft:" + line)
    return out


def check_jar(biomes, jar):
    """Every tensura: id of the allowed list must be a biome of the Tensura jar (the /dump-ids rule)."""
    if not jar or not Path(jar).is_file():
        return []
    with zipfile.ZipFile(jar) as z:
        names = set(z.namelist())
    return ["biomes.txt lists %s, which is not in %s (data/tensura/worldgen/biome/%s.json)" % (b, Path(jar).name, b[8:])
            for b in sorted(biomes) if b.startswith("tensura:") and "data/tensura/worldgen/biome/%s.json" % b[8:] not in names]


def load_relations(path, anchors):
    """([[relation]], [[site_rule]], [[gap]], problems). See canon_relations.toml for the fields."""
    problems = []
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))

    def known(tag, ident):
        if ident not in anchors:
            problems.append("%s: %s is not an anchor of anchors.toml" % (tag, ident))

    for i, r in enumerate(data.get("relation", [])):
        tag = "relation #%d (%s -> %s)" % (i + 1, r.get("a"), r.get("b"))
        for key in ("a", "b", "source"):
            if not r.get(key):
                problems.append("%s: missing %s" % (tag, key))
        known(tag, r.get("a"))
        known(tag, r.get("b"))
        d = r.get("dir", "any")
        if d not in WINDS and d not in ("near", "any"):
            problems.append("%s: dir %r is not a compass wind, near or any" % (tag, d))
        if "max" not in r and "min" not in r:
            problems.append("%s: needs a min and/or max distance" % tag)
    for i, r in enumerate(data.get("site_rule", [])):
        tag = "site_rule #%d (%s)" % (i + 1, r.get("id"))
        if not r.get("id") or not r.get("source"):
            problems.append("%s: needs id and source" % tag)
        known(tag, r.get("id"))
    for i, r in enumerate(data.get("gap", [])):
        tag = "gap #%d (%s -> %s)" % (i + 1, r.get("a"), r.get("b"))
        for key in ("a", "b", "source"):
            if not r.get(key):
                problems.append("%s: missing %s" % (tag, key))
        known(tag, r.get("a"))
        known(tag, r.get("b"))
    return data.get("relation", []), data.get("site_rule", []), data.get("gap", []), problems


def load_config(anchors=None, relations=None, canon=None, biomes=None, landmarks=None, jar=None, sites=None):
    anchors_d = load_anchors(anchors or DEFAULT_ANCHORS)
    letters, colours = load_canon(canon or DEFAULT_CANON)
    rels, rules, gaps, problems = load_relations(relations or DEFAULT_RELATIONS, anchors_d)
    bio = load_biomes(biomes or DEFAULT_BIOMES)
    jar = jar or os.environ.get("TTL_TENSURA_JAR")
    return Config(anchors_d, letters, rels, bio, colours, problems, rules, gaps,
                  load_landmark_reach(landmarks or DEFAULT_LANDMARKS), check_jar(bio, jar),
                  load_min_r(sites or DEFAULT_SITES))


# ---------------------------------------------------------------------------------------------------------------------
# Geometry

def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _in_box(a, b, c):
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def seg_intersect(p1, p2, p3, p4):
    """'cross' (proper crossing), 'touch' (an end lies on the other segment, incl. collinear overlap) or None."""
    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return "cross"
    if (d1 == 0 and _in_box(p3, p4, p1)) or (d2 == 0 and _in_box(p3, p4, p2)) \
            or (d3 == 0 and _in_box(p1, p2, p3)) or (d4 == 0 and _in_box(p1, p2, p4)):
        return "touch"
    return None


def area_signed(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def perimeter(pts, closed=True):
    n = len(pts)
    return sum(math.dist(pts[i], pts[(i + 1) % n]) for i in range(n if closed else n - 1))


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def dist_point_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def dist_point_path(p, pts, closed):
    n = len(pts)
    best = math.inf
    for i in range(n if closed else n - 1):
        best = min(best, dist_point_seg(p, pts[i], pts[(i + 1) % n]))
    return best


def self_intersections(pts, limit=3):
    """Pairs of non-adjacent edges of the closed ring that cross or touch (and spikes), found with a grid."""
    n = len(pts)
    cell = 500.0
    buckets = {}
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for cx in range(int(min(a[0], b[0]) // cell), int(max(a[0], b[0]) // cell) + 1):
            for cy in range(int(min(a[1], b[1]) // cell), int(max(a[1], b[1]) // cell) + 1):
                buckets.setdefault((cx, cy), []).append(i)
    seen, out = set(), []
    for lst in buckets.values():
        for u in range(len(lst)):
            for v in range(u + 1, len(lst)):
                i, j = lst[u], lst[v]
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                a1, a2 = pts[i], pts[(i + 1) % n]
                b1, b2 = pts[j], pts[(j + 1) % n]
                if j == i + 1 or (i == 0 and j == n - 1):
                    p0, p1, p2 = (a1, a2, b2) if j == i + 1 else (b1, b2, a2)   # two edges meeting at p1: a spike?
                    if orient(p0, p1, p2) == 0 and (p1[0] - p0[0]) * (p2[0] - p1[0]) + (p1[1] - p0[1]) * (p2[1] - p1[1]) < 0:
                        out.append((i, j))
                    continue
                if seg_intersect(a1, a2, b1, b2):
                    out.append((i, j))
                if len(out) >= limit:
                    return out
    return out


def polys_cross(p, q):
    """True when an edge of ring p properly crosses an edge of ring q."""
    bp, bq = bbox(p), bbox(q)
    if bp[2] < bq[0] or bq[2] < bp[0] or bp[3] < bq[1] or bq[3] < bp[1]:
        return None
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        lo_x, hi_x, lo_y, hi_y = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
        if hi_x < bq[0] or lo_x > bq[2] or hi_y < bq[1] or lo_y > bq[3]:
            continue
        for j in range(len(q)):
            c, d = q[j], q[(j + 1) % len(q)]
            if seg_intersect(a, b, c, d) == "cross":
                return a
    return None


def strictly_inside(pt, poly, eps=1.0):
    return point_in_poly(pt, poly) and dist_point_path(pt, poly, True) > eps


def polys_overlap(p, q):
    """Overlap of two rings: a proper edge crossing, or a vertex / edge middle of one strictly inside the other."""
    if polys_cross(p, q):
        return True
    for a, b in ((p, q), (q, p)):
        for i in range(len(a)):
            if strictly_inside(a[i], b) or strictly_inside(((a[i][0] + a[(i + 1) % len(a)][0]) / 2,
                                                              (a[i][1] + a[(i + 1) % len(a)][1]) / 2), b):
                return True
    return False


def bearing(a, b):
    """Compass bearing in degrees from a to b (north = up = smaller y, east = 90)."""
    return math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))) % 360.0


def wind(deg):
    return WINDS[int((deg % 360.0) / 22.5 + 0.5) % 16]


def angle_diff(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def default_tolerance(d):
    if len(d) == 1:
        return 45.0
    return 35.0 if len(d) == 2 else 25.0




# ---------------------------------------------------------------------------------------------------------------------
# SVG parsing

class Shape:
    def __init__(self, layer, kind, pts, attrs, label, closed=True, cx=None, cy=None, r=None, nodes=None):
        self.layer = layer
        self.kind = kind            # polygon | polyline | circle | rect
        self.pts = pts
        self.attrs = attrs
        self.label = label
        self.closed = closed
        self.cx, self.cy, self.r = cx, cy, r
        self.nodes = nodes          # vertices as drawn (curves count one per segment end)

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    @property
    def classes(self):
        return self.attrs.get("class", "").split()


NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(r"[MmLlHhVvZzCcQqSsTtAa]|" + NUM)
TRANSFORM = re.compile(r"\s*(\w+)\s*\(([^)]*)\)\s*,?")


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def fnum(s, what):
    try:
        v = float(s)
    except (TypeError, ValueError):
        raise ParseError("%s is not a number: %r" % (what, s))
    if not math.isfinite(v):
        raise ParseError("%s is not finite" % what)
    return v


def parse_transform(s):
    """translate and scale only (the map allows no transform at all; the geometry is still read as written).
    Returns (sx, sy, tx, ty): p' = (sx*x + tx, sy*y + ty)."""
    t = (1.0, 1.0, 0.0, 0.0)
    pos = 0
    s = s or ""
    while pos < len(s):
        m = TRANSFORM.match(s, pos)
        if not m:
            if s[pos:].strip():
                raise ParseError("unreadable transform %r" % s)
            break
        pos = m.end()
        name = m.group(1)
        vals = [fnum(v, "transform value") for v in re.split(r"[\s,]+", m.group(2).strip()) if v]
        if name == "translate" and len(vals) in (1, 2):
            f = (1.0, 1.0, vals[0], vals[1] if len(vals) == 2 else 0.0)
        elif name == "scale" and len(vals) in (1, 2):
            f = (vals[0], vals[1] if len(vals) == 2 else vals[0], 0.0, 0.0)
        else:
            raise ParseError("unsupported transform %s(...): only translate and scale are read" % name)
        t = compose(t, f)
    return t


def compose(a, b):
    """a applied after b."""
    return (a[0] * b[0], a[1] * b[1], a[0] * b[2] + a[2], a[1] * b[3] + a[3])


def apply(t, p):
    return (t[0] * p[0] + t[2], t[1] * p[1] + t[3])


def parse_points(s):
    nums = [fnum(v, "points value") for v in re.findall(NUM, s or "")]
    if len(nums) % 2:
        raise ParseError("points has an odd number of values")
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]


def parse_path(d):
    """List of (points, closed, nodes) subpaths, curves flattened. Supports M L H V Z C Q (absolute and relative)."""
    toks = TOKEN.findall(d or "")
    subs = []
    cur = []
    nodes = 0
    closed = False
    i = 0
    cmd = None
    x = y = sx = sy = 0.0
    started = False

    def need(n):
        nonlocal i
        if i + n > len(toks) or any(t.isalpha() for t in toks[i:i + n]):
            raise ParseError("path command %s needs %d numbers" % (cmd, n))
        vals = [float(t) for t in toks[i:i + n]]
        i += n
        return vals

    def flush():
        nonlocal cur, closed, nodes
        if cur:
            subs.append((cur, closed, nodes))
        cur, closed, nodes = [], False, 0

    def begin():
        nonlocal cur, nodes
        if not cur:
            cur = [(x, y)]
            nodes = 1

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                if cur:
                    closed = True
                    x, y = sx, sy
                    flush()
                continue
        elif cmd is None:
            raise ParseError("path data must start with a command")
        elif cmd in "Zz":
            raise ParseError("numbers after Z")
        rel = cmd.islower()
        c = cmd.upper()
        if c in "SAT":
            raise ParseError("unsupported path command %s (use M L H V C Q Z)" % cmd)
        if c == "M":
            a, b = need(2)
            if rel:
                a, b = x + a, y + b
            flush()
            x, y, sx, sy = a, b, a, b
            started = True
            cur, nodes = [(x, y)], 1
            cmd = "l" if rel else "L"       # further pairs are implicit line-to
        elif not started:
            raise ParseError("path draws before a moveto")
        elif c == "L":
            a, b = need(2)
            begin()
            x, y = (x + a, y + b) if rel else (a, b)
            cur.append((x, y))
            nodes += 1
        elif c == "H":
            (a,) = need(1)
            begin()
            x = x + a if rel else a
            cur.append((x, y))
            nodes += 1
        elif c == "V":
            (b,) = need(1)
            begin()
            y = y + b if rel else b
            cur.append((x, y))
            nodes += 1
        elif c in "CQ":
            n = 6 if c == "C" else 4
            v = need(n)
            if rel:
                v = [v[k] + (x if k % 2 == 0 else y) for k in range(n)]
            begin()
            ctrl = [(x, y)] + [(v[k], v[k + 1]) for k in range(0, n, 2)]
            for s in range(1, CURVE_STEPS[c] + 1):
                u = s / CURVE_STEPS[c]
                if c == "C":
                    p0, p1, p2, p3 = ctrl
                    px = (1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u * u * p2[0] + u ** 3 * p3[0]
                    py = (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u * u * p2[1] + u ** 3 * p3[1]
                else:
                    p0, p1, p2 = ctrl
                    px = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
                    py = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
                cur.append((px, py))
            x, y = ctrl[-1]
            nodes += 1
    flush()
    return subs


def element_label(el, layer, index):
    ident = el.get("id") or el.get("data-id") or el.get("data-letter") or el.get("data-name")
    return "%s <%s> #%s%s" % (layer, local(el.tag), index, " (%s)" % ident if ident else "")


SKIP_TAGS = {"title", "desc", "metadata", "text", "style", "defs", "tspan"}


def circle_pts(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def shapes_of(el, layer, tf, index, report):
    """Shapes of one element (a <path> may hold several subpaths)."""
    tag = local(el.tag)
    tf = compose(tf, parse_transform(el.get("transform")))
    attrs = {k: v for k, v in el.attrib.items() if k.startswith("data-") or k in ("class", "id")}
    label = element_label(el, layer, index)
    out = []
    if tag == "polygon":
        raw = parse_points(el.get("points"))
        out.append(Shape(layer, "polygon", [apply(tf, p) for p in raw], attrs, label, True, nodes=len(raw)))
    elif tag == "polyline":
        raw = parse_points(el.get("points"))
        out.append(Shape(layer, "polyline", [apply(tf, p) for p in raw], attrs, label, False, nodes=len(raw)))
    elif tag == "line":
        pts = [(fnum(el.get("x1", "0"), "x1"), fnum(el.get("y1", "0"), "y1")),
               (fnum(el.get("x2", "0"), "x2"), fnum(el.get("y2", "0"), "y2"))]
        out.append(Shape(layer, "polyline", [apply(tf, p) for p in pts], attrs, label, False, nodes=2))
    elif tag == "path":
        for k, (pts, closed, nodes) in enumerate(parse_path(el.get("d"))):
            lab = label if k == 0 else "%s subpath %d" % (label, k + 1)
            out.append(Shape(layer, "polygon" if closed else "polyline", [apply(tf, p) for p in pts], attrs, lab, closed,
                             nodes=nodes))
    elif tag == "rect":
        x, y = fnum(el.get("x", "0"), "x"), fnum(el.get("y", "0"), "y")
        w, h = fnum(el.get("width"), "width"), fnum(el.get("height"), "height")
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        sh = Shape(layer, "rect", [apply(tf, p) for p in corners], attrs, label, True)
        sh.cx, sh.cy = apply(tf, (x + w / 2, y + h / 2))
        sh.r = max(abs(w * tf[0]), abs(h * tf[1])) / 2
        out.append(sh)
    elif tag == "circle":
        cx, cy, r = fnum(el.get("cx", "0"), "cx"), fnum(el.get("cy", "0"), "cy"), fnum(el.get("r"), "r")
        c = apply(tf, (cx, cy))
        rr = abs(r) * (abs(tf[0]) + abs(tf[1])) / 2
        out.append(Shape(layer, "circle", circle_pts(c[0], c[1], rr), attrs, label, True, c[0], c[1], rr))
    else:
        report.error("structure", "%s: unsupported element <%s> (use polygon, polyline, path, circle, rect)" % (label, tag))
    return out


def walk_layer(el, layer, tf, report, shapes, counter):
    for child in el:
        tag = local(child.tag)
        if tag in SKIP_TAGS or not isinstance(child.tag, str):
            continue
        counter[0] += 1
        label = element_label(child, layer, counter[0])
        try:
            if child.get("transform") is not None:
                report.error("structure", "%s has a transform (the map allows none; write the final coordinates)" % label)
            if tag == "g":
                report.error("structure", "%s: nested groups are not allowed inside a layer" % label)
                walk_layer(child, layer, compose(tf, parse_transform(child.get("transform"))), report, shapes, counter)
                continue
            shapes.extend(shapes_of(child, layer, tf, counter[0], report))
        except ParseError as e:
            report.error("structure", "%s: %s" % (label, e))


def find_layers(root, report):
    """Map layer name -> list of (element, accumulated transform); unknown top-level groups are errors."""
    found = {name: [] for name in LAYERS}

    def rec(el, tf, depth):
        for child in el:
            if not isinstance(child.tag, str) or local(child.tag) != "g":
                continue
            try:
                ctf = compose(tf, parse_transform(child.get("transform")))
            except ParseError as e:
                report.error("structure", "<g id=%s>: %s" % (child.get("id"), e))
                continue
            ident = child.get("id")
            if child.get("transform") is not None:
                report.error("structure", "group %s has a transform (the map allows none)" % ident)
            if ident in found:
                found[ident].append((child, ctf))
            else:
                report.error("structure", "unknown group id=%r: the map has exactly the groups %s" % (ident, " ".join(LAYERS)))
    rec(root, (1.0, 1.0, 0.0, 0.0), 0)
    return found


# ---------------------------------------------------------------------------------------------------------------------
# Report

class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {}
        self.distances = []
        self.relations = []
        self.notes = []

    def error(self, rule, msg):
        self.errors.append({"rule": rule, "message": msg})

    def warn(self, rule, msg):
        self.warnings.append({"rule": rule, "message": msg})

    @property
    def ok(self):
        return not self.errors


def fmt_pt(p):
    return "(%d, %d)" % (round(p[0]), round(p[1]))


def fmt_list(items, n=6):
    items = list(items)
    return ", ".join(items[:n]) + (" ... (+%d)" % (len(items) - n) if len(items) > n else "")


class World:
    """The parsed map: shapes per layer, plus the land queries the checks share."""

    def __init__(self, shapes):
        self.shapes = shapes
        self.coast = [s for s in shapes["coast"] if s.closed]
        self.lakes = [s for s in shapes["lakes"] if s.closed]
        self.boxes = {id(s): bbox(s.pts) for s in self.coast + self.lakes if s.pts}

    def find(self, shape_list, p):
        for s in shape_list:
            b = self.boxes.get(id(s))
            if b and b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] and point_in_poly(p, s.pts):
                return s
        return None

    def landmass(self, p):
        return self.find(self.coast, p)

    def in_coast(self, p):
        return self.find(self.coast, p) is not None

    def in_lake(self, p):
        return self.find(self.lakes, p) is not None

    def on_land(self, p):
        return self.in_coast(p) and not self.in_lake(p)

    def coast_dist(self, p):
        return min((dist_point_path(p, s.pts, True) for s in self.coast), default=math.inf)

    def lake_dist(self, p):
        if self.in_lake(p):
            return 0.0
        return min((dist_point_path(p, s.pts, True) for s in self.lakes), default=math.inf)

    def river_dist(self, p):
        return min((dist_point_path(p, r.pts, False) - river_half(r) for r in self.shapes["rivers"]), default=math.inf)


def river_half(r):
    try:
        return float(r.get("data-width")) / 2
    except (TypeError, ValueError):
        return 0.0


def parse_svg(text, report):
    """Returns shapes per layer (None when the file cannot be read at all)."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        report.error("structure", "not well-formed XML: %s" % e)
        return None
    if local(root.tag) != "svg":
        report.error("structure", "the root element is <%s>, not <svg>" % local(root.tag))
        return None
    vb = root.get("viewBox")
    try:
        vals = tuple(float(v) for v in re.split(r"[\s,]+", (vb or "").strip()))
    except ValueError:
        vals = ()
    if vals != VIEWBOX:
        report.error("structure", "viewBox is %r, must be \"-8000 -6000 16000 12000\"" % vb)
    found = find_layers(root, report)
    shapes = {name: [] for name in LAYERS}
    for name in LAYERS:
        groups = found[name]
        if not groups:
            (report.warn if name == "labels" else report.error)("structure", "layer <g id=\"%s\"> is missing" % name)
        elif len(groups) > 1:
            report.error("structure", "layer id=\"%s\" exists %d times" % (name, len(groups)))
        if name == "labels":
            continue
        counter = [0]
        for el, tf in groups:
            walk_layer(el, name, tf, report, shapes[name], counter)
    return shapes


# ---------------------------------------------------------------------------------------------------------------------
# Checks

def dedupe(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > 1e-9:
            out.append(p)
    return out


def clean_ring(pts):
    out = dedupe(pts)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= 1e-9:
        out.pop()
    return out


def split_mountains(shapes, report):
    """Mountains hold polygons and optional <polyline class="ridge">: separate them before the polygon checks."""
    ridges, polys = [], []
    for s in shapes["mountains"]:
        if s.kind == "polyline" and "ridge" in s.classes:
            if len(s.pts) < 2:
                report.error("polygon", "%s has fewer than 2 points" % s.label)
            else:
                ridges.append(s)
        else:
            polys.append(s)
    shapes["mountains"] = polys
    shapes["ridges"] = ridges


def check_geometry(shapes, report):
    """Rule 2 (polygons) and the viewBox bounds for everything."""
    for layer in AREAL:
        keep = []
        for s in shapes[layer]:
            if s.kind == "polyline":
                report.error("polygon", "%s is open (a <path> needs Z, or use <polygon>)" % s.label)
                continue
            s.pts = clean_ring(s.pts)
            if len(s.pts) < 3:
                report.error("polygon", "%s has fewer than 3 distinct points" % s.label)
                continue
            if s.nodes is not None and not POLY_NODES[0] <= s.nodes <= POLY_NODES[1]:
                report.error("polygon", "%s has %d vertices (allowed %d..%d)" % (s.label, s.nodes, POLY_NODES[0], POLY_NODES[1]))
            if abs(area_signed(s.pts)) < 1.0:
                report.error("polygon", "%s has no area" % s.label)
                continue
            if s.kind not in ("circle", "rect"):
                bad = self_intersections(s.pts)
                if bad:
                    i, j = bad[0]
                    report.error("polygon", "%s crosses itself near %s (edges %d and %d)" %
                                 (s.label, fmt_pt(s.pts[i]), i + 1, j + 1))
                    continue
            keep.append(s)
        shapes[layer] = keep
    for layer in ("rivers", "roads"):
        keep = []
        for s in shapes[layer]:
            if s.kind == "polygon":
                report.error("polygon", "%s is closed; rivers and roads are open polylines" % s.label)
                continue
            s.pts = dedupe(s.pts)
            if len(s.pts) < 2:
                report.error("polygon", "%s has fewer than 2 distinct points" % s.label)
                continue
            keep.append(s)
        shapes[layer] = keep
    x0, y0, x1, y1 = VIEWBOX[0], VIEWBOX[1], VIEWBOX[0] + VIEWBOX[2], VIEWBOX[1] + VIEWBOX[3]
    for layer in LAYERS:
        if layer == "labels":
            continue
        for s in shapes.get(layer, []) + (shapes["ridges"] if layer == "mountains" else []):
            pts = s.pts if s.kind != "circle" else s.pts
            out = [p for p in pts if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1)]
            if out:
                report.error("polygon", "%s has %d point(s) outside the viewBox, first %s" % (s.label, len(out), fmt_pt(out[0])))


def check_land(world, shapes, report):
    if not shapes["coast"]:
        report.error("water", "coast has no land polygons")
    cs = shapes["coast"]
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            at = polys_cross(cs[i].pts, cs[j].pts)
            if at:
                report.error("water", "%s and %s cross near %s: one polygon per landmass" % (cs[i].label, cs[j].label, fmt_pt(at)))
            elif strictly_inside(cs[i].pts[0], cs[j].pts) or strictly_inside(cs[j].pts[0], cs[i].pts):
                report.warn("water", "%s and %s are nested; land is the union, so use a lake for water inside land" %
                            (cs[i].label, cs[j].label))
    for s in shapes["lakes"]:
        out = [p for p in s.pts if not world.in_coast(p)]
        if out:
            report.error("water", "%s has %d point(s) outside the land, first %s" % (s.label, len(out), fmt_pt(out[0])))
            continue
        for c in shapes["coast"]:
            at = polys_cross(s.pts, c.pts)
            if at:
                report.error("water", "%s crosses the coast line near %s" % (s.label, fmt_pt(at)))
                break
        for key, lo, hi in (("data-level", -64, 320), ("data-depth", 1, 64)):
            if s.get(key) is not None and not num_in(s.get(key), lo, hi):
                report.error("attribute", "%s: %s %r is not a number in %d..%d" % (s.label, key, s.get(key), lo, hi))
    lk = shapes["lakes"]
    for i in range(len(lk)):
        for j in range(i + 1, len(lk)):
            if polys_overlap(lk[i].pts, lk[j].pts):
                report.warn("water", "%s and %s overlap" % (lk[i].label, lk[j].label))
    for layer in ("mountains", "hills"):
        for s in shapes[layer]:
            if not world.coast:
                continue
            out = [p for p in s.pts if not world.in_coast(p)]
            far = [p for p in out if world.coast_dist(p) > 64]
            if far:
                report.error("water", "%s lies partly in the sea: %s is %d blocks outside the coast" %
                             (s.label, fmt_pt(far[0]), round(world.coast_dist(far[0]))))
            elif out:
                report.warn("water", "%s has %d point(s) just outside the coast, first %s" % (s.label, len(out), fmt_pt(out[0])))


def num_in(v, lo, hi):
    try:
        return lo <= float(v) <= hi
    except (TypeError, ValueError):
        return False


def check_rivers(world, shapes, report):
    for s in shapes["rivers"]:
        raw = s.get("data-width")
        if raw is None:
            report.error("attribute", "%s has no data-width (blocks, %d..%d)" % (s.label, RIVER_WIDTH[0], RIVER_WIDTH[1]))
        elif not num_in(raw, *RIVER_WIDTH):
            report.error("attribute", "%s: data-width %r is outside %d..%d blocks" % (s.label, raw, RIVER_WIDTH[0], RIVER_WIDTH[1]))
        for key, lo, hi in (("data-head", -64, 320), ("data-mouth", -64, 320)):
            if s.get(key) is not None and not num_in(s.get(key), lo, hi):
                report.error("attribute", "%s: %s %r is not a number in %d..%d" % (s.label, key, s.get(key), lo, hi))
        if not world.coast:
            continue
        start, end = s.pts[0], s.pts[-1]
        if not world.on_land(start):
            report.error("water", "%s starts at %s, which is not on land (a river rises on land, outside every lake)" %
                         (s.label, fmt_pt(start)))
        if world.in_lake(end) or world.coast_dist(end) <= RIVER_MOUTH_SLACK:
            pass
        elif not world.in_coast(end):
            report.error("water", "%s ends at %s, %d blocks out at sea (a mouth is at most %d outside the coast)" %
                         (s.label, fmt_pt(end), round(world.coast_dist(end)), RIVER_MOUTH_SLACK))
        else:
            report.error("water", "%s ends at %s on dry land: a river must end in a lake or the sea" % (s.label, fmt_pt(end)))
        for m in shapes["mountains"]:
            if any(point_in_poly(p, m.pts) for p in sample_path(s.pts, 50.0)):
                report.warn("water", "%s crosses the mountain %s" % (s.label, m.label))
                break


def check_attrs(world, shapes, cfg, report):
    for s in shapes["mountains"]:
        if s.get("data-peak") is None or not num_in(s.get("data-peak"), *PEAK_RANGE):
            report.error("attribute", "%s: data-peak %r is missing or outside y %d..%d" % (s.label, s.get("data-peak"), PEAK_RANGE[0], PEAK_RANGE[1]))
        if s.get("data-shape") is not None and s.get("data-shape") not in MOUNTAIN_SHAPES:
            report.error("attribute", "%s: data-shape %r is not one of %s" % (s.label, s.get("data-shape"), "|".join(MOUNTAIN_SHAPES)))
        if s.get("data-rugged") is not None and not num_in(s.get("data-rugged"), 0, 1):
            report.error("attribute", "%s: data-rugged %r is not a number in 0..1" % (s.label, s.get("data-rugged")))
    for s in shapes["ridges"]:
        if not any(point_in_poly(p, m.pts) for m in shapes["mountains"] for p in s.pts[:1]):
            report.warn("attribute", "%s starts outside every mountain polygon" % s.label)
    for s in shapes["hills"]:
        if s.get("data-height") is None or not num_in(s.get("data-height"), *HILL_RANGE):
            report.error("attribute", "%s: data-height %r is missing or outside y %d..%d" % (s.label, s.get("data-height"), HILL_RANGE[0], HILL_RANGE[1]))
        if s.get("data-shape") is not None and s.get("data-shape") not in HILL_SHAPES:
            report.error("attribute", "%s: data-shape %r is not one of %s" % (s.label, s.get("data-shape"), "|".join(HILL_SHAPES)))
        if s.get("data-rugged") is not None and not num_in(s.get("data-rugged"), 0, 1):
            report.error("attribute", "%s: data-rugged %r is not a number in 0..1" % (s.label, s.get("data-rugged")))
    for s in shapes["forests"]:
        if s.get("data-type") not in FOREST_TYPES:
            report.error("attribute", "%s: data-type %r is not one of %s" % (s.label, s.get("data-type"), ", ".join(FOREST_TYPES)))
    for s in shapes["biomes"]:
        b = s.get("data-biome")
        if not b:
            report.error("attribute", "%s has no data-biome" % s.label)
            continue
        full = b if ":" in b else "minecraft:" + b
        if cfg.biomes is not None and full not in cfg.biomes:
            report.error("attribute", "%s: biome %r is not allowed (tools/world/biomes.txt; beaches, rivers, shores and oceans "
                         "are assigned by the tool)" % (s.label, b))
    for s in shapes["regions"]:
        letter = s.get("data-letter")
        if not letter:
            report.error("attribute", "%s has no data-letter" % s.label)
        elif letter not in cfg.letters:
            report.error("attribute", "%s: letter %r is not in canon_regions.json (%s)" % (s.label, letter, "".join(sorted(cfg.letters))))
    for s in shapes["roads"]:
        if s.get("data-kind") not in ROAD_KINDS:
            report.error("attribute", "%s: data-kind %r is not main or trail" % (s.label, s.get("data-kind")))


def check_region_cover(world, shapes, report):
    """Every land sample in exactly one region; each letter at most once per landmass."""
    regions = [s for s in shapes["regions"] if s.get("data-letter")]
    if not world.coast or not regions:
        if world.coast and not regions:
            report.error("region", "regions has no polygons: every land px needs a region")
        return
    boxes = [bbox(s.pts) for s in regions]
    xs = [b for c in world.coast for b in (bbox(c.pts)[0], bbox(c.pts)[2])]
    ys = [b for c in world.coast for b in (bbox(c.pts)[1], bbox(c.pts)[3])]
    gaps, overlaps = [], {}
    per_mass = {}
    n = 0
    j = 0
    y = min(ys) + 0.37
    while y <= max(ys):
        x = min(xs) + 0.61
        while x <= max(xs):
            p = (x, y)
            mass = world.landmass(p)
            if mass is not None and not world.in_lake(p):
                n += 1
                hit = [k for k, s in enumerate(regions)
                       if boxes[k][0] <= x <= boxes[k][2] and boxes[k][1] <= y <= boxes[k][3] and point_in_poly(p, s.pts)]
                if not hit:
                    gaps.append(p)
                elif len(hit) > 1:
                    key = tuple(sorted(set(regions[k].get("data-letter") for k in hit)))
                    if len(set(hit)) > 1:
                        overlaps.setdefault(key, []).append(p)
                for k in hit:
                    per_mass.setdefault((id(mass), regions[k].get("data-letter")), set()).add(k)
            x += REGION_STEP
        y += REGION_STEP
    if gaps:
        report.error("region", "%d of %d land samples (every %d blocks) belong to no region, first %s: regions must cover all land" %
                     (len(gaps), n, REGION_STEP, fmt_pt(gaps[0])))
    for key, pts in overlaps.items():
        if len(set(key)) == 1:
            continue
        report.error("region", "regions %s overlap on land (%d samples, first %s)" % ("/".join(key), len(pts), fmt_pt(pts[0])))
    for (_, letter), ks in per_mass.items():
        if len(ks) > 1:
            report.error("region", "letter %s has %d polygons on one landmass (at most one per landmass): %s" %
                         (letter, len(ks), fmt_list(regions[k].label for k in sorted(ks))))


class Site:
    def __init__(self, shape, ident, kind):
        self.shape, self.id, self.kind = shape, ident, kind
        self.x, self.y, self.r = shape.cx, shape.cy, shape.r
        self.min_r = 0
        try:
            self.margin = float(shape.get("data-margin", SITE_MARGIN))
        except (TypeError, ValueError):
            self.margin = SITE_MARGIN

    @property
    def eff_r(self):
        """The radius the generator uses: the drawn r, raised to the build's min_r (svg2rasters.py)."""
        return max(self.r, self.min_r)

    @property
    def pt(self):
        return (self.x, self.y)


def collect_sites(shapes, cfg, report):
    sites = []
    for s in shapes["sites"]:
        if s.kind not in ("circle", "rect"):
            report.error("site", "%s: a site is a <circle>, not a %s" % (s.label, s.kind))
            continue
        ident, kind = s.get("data-id"), s.get("data-site")
        if not ident:
            report.error("site", "%s has no data-id" % s.label)
            continue
        if kind not in SITE_KINDS:
            report.error("site", "%s (%s): data-site %r is not one of %s" % (s.label, ident, kind, "|".join(SITE_KINDS)))
            continue
        if not s.r or not SITE_R[0] <= s.r <= SITE_R[1]:
            report.error("site", "%s (%s): r %s is outside %d..%d" % (s.label, ident, round(s.r or 0, 1), SITE_R[0], SITE_R[1]))
            continue
        if s.get("data-margin") is not None and not num_in(s.get("data-margin"), 0, MARGIN_MAX):
            report.error("attribute", "%s (%s): data-margin %r is not a number in 0..%d" % (s.label, ident, s.get("data-margin"), MARGIN_MAX))
        st = Site(s, ident, kind)
        st.min_r = cfg.min_r.get(ident, 0)
        sites.append(st)
    by = {}
    for st in sites:
        by.setdefault(st.id, []).append(st)
    for ident, lst in by.items():
        if len(lst) > 1:
            report.error("site", "anchor %s has %d sites (exactly one): %s" % (ident, len(lst), ", ".join(fmt_pt(s.pt) for s in lst)))
    for aid in cfg.anchors:
        if aid not in by:
            report.error("site", "anchor %s (%s) has no site in the sites layer" % (aid, cfg.anchors[aid]["name"]))
    for ident in by:
        if ident not in cfg.anchors:
            report.error("site", "site %s is not an anchor of anchors.toml" % ident)
    return sites, {k: v[0] for k, v in by.items()}


def check_sites(world, shapes, cfg, sites, report):
    by_letter = {}
    for s in shapes["regions"]:
        by_letter.setdefault(s.get("data-letter"), []).append(s)
    have_coast = bool(world.coast)
    for st in sites:
        anchor = cfg.anchors.get(st.id)
        water_anchor = bool(anchor) and anchor["surface"] == "water"
        p = st.pt
        in_lake, in_coast = world.in_lake(p), world.in_coast(p)
        on_land = in_coast and not in_lake
        cd = world.coast_dist(p) if have_coast else math.inf
        if have_coast:
            if not on_land and not (water_anchor and st.kind in ("lakeside", "coast")):
                report.error("site", "site %s (%s) at %s is %s: a site stands on land (only the surface = water anchors Lake Siss "
                             "and the Ameld mouth may be on water, as lakeside/coast)" %
                             (st.id, st.kind, fmt_pt(p), "in a lake" if in_lake else "in the ocean"))
            elif on_land and st.kind not in ("coast", "lakeside"):
                if cd < st.r:
                    report.error("site", "site %s: its disc (r %d) reaches the coast line (centre %d blocks from it)" % (st.id, round(st.r), round(cd)))
                elif cd < COAST_MIN:
                    report.error("site", "site %s is %d blocks from the coast (minimum %d)" % (st.id, round(cd), COAST_MIN))
                ld = world.lake_dist(p)
                if ld < st.r:
                    report.error("site", "site %s: its disc (r %d) reaches a lake (centre %d blocks from it)" % (st.id, round(st.r), round(ld)))
            if on_land and st.kind == "coast" and cd > st.r + TOUCH_SLACK:
                report.error("site", "coast site %s: the sea is %d blocks from its centre, farther than r %d + %d" % (st.id, round(cd), round(st.r), TOUCH_SLACK))
            if on_land and st.kind == "lakeside":
                wd = min(world.lake_dist(p), world.river_dist(p))
                if wd > st.r + TOUCH_SLACK:
                    report.error("site", "lakeside site %s: the nearest lake or river is %s from its centre, farther than r %d + %d" %
                                 (st.id, "%d blocks" % wd if wd < math.inf else "(none)", round(st.r), TOUCH_SLACK))
        if st.kind == "carve" and not any(point_in_poly(p, m.pts) for m in shapes["mountains"] + shapes["hills"]):
            report.error("site", "carve site %s at %s is not inside a mountain or hill polygon" % (st.id, fmt_pt(p)))
        if st.kind == "village" and anchor and anchor["landmark"]:
            reach = cfg.reach.get(anchor["landmark"])
            if reach is not None and st.r < reach:
                report.error("site", "village site %s: r %d is below the landmark %s's reach %d (landmarks.toml)" %
                             (st.id, round(st.r), anchor["landmark"], reach))
        if anchor:
            letters = set(anchor["region"])
            polys = [s for L in letters for s in by_letter.get(L, [])]
            if not polys:
                report.error("site", "site %s: no region polygon with letter %s" % (st.id, anchor["region"]))
            elif not any(point_in_poly(p, s.pts) for s in polys):
                actual = sorted({s.get("data-letter") for s in shapes["regions"] if point_in_poly(p, s.pts)})
                report.error("site", "site %s at %s is %s, anchors.toml says region %s" %
                             (st.id, fmt_pt(p), "in region " + "/".join(actual) if actual else "in no region", anchor["region"]))
    for st in sites:
        if st.min_r > st.r:
            report.warn("site", "site %s: drawn too small, r %d < min_r %d of its build; it will be enlarged to %d (draw r %d)" %
                        (st.id, round(st.r), round(st.min_r), round(st.min_r), round(st.min_r)))
    parent = {k: v.get("of") for k, v in cfg.anchors.items()}
    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            a, b = sites[i], sites[j]
            # anchors placed relative to each other (of/dx/dz) are one place: a child lies by design in its parent's disc
            # and siblings may sit a few blocks apart (dwargo, dwargon_throne, kaijin_smithy)
            if parent.get(a.id) == b.id or parent.get(b.id) == a.id or (parent.get(a.id) and parent.get(a.id) == parent.get(b.id)):
                continue
            need = max(a.margin, b.margin)
            d = math.dist(a.pt, b.pt)
            gap = d - (a.eff_r + b.eff_r)
            if gap < need:
                report.error("site", "sites %s and %s are %d blocks apart: edge gap %d = distance - (r1_eff %d + r2_eff %d) is "
                             "below the larger data-margin %d" %
                             (a.id, b.id, round(d), round(gap), round(a.eff_r), round(b.eff_r), round(need)))


def check_relative_anchors(cfg, site_by_id, report):
    """An anchor placed `of` another with dx/dz must be drawn near parent + offset (the scripts keep the offsets)."""
    for aid, a in cfg.anchors.items():
        parent = a.get("of")
        st, ps = site_by_id.get(aid), site_by_id.get(parent) if parent else None
        if not parent or st is None or ps is None:
            continue
        want = (ps.x + a.get("dx", 0), ps.y + a.get("dz", 0))
        off = math.dist(st.pt, want)
        if off > ANCHOR_DRIFT:
            report.warn("site", "relative anchor %s is drawn at %s, %d blocks from %s + (%d, %d) = %s (anchors.toml of/dx/dz); "
                        "move it within %d" % (aid, fmt_pt(st.pt), round(off), parent, a.get("dx", 0), a.get("dz", 0),
                                                fmt_pt(want), ANCHOR_DRIFT))


def sample_path(pts, step):
    out = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.dist(a, b)
        n = max(1, int(L // step))
        for k in range(1, n + 1):
            t = min(1.0, k * step / L) if L else 1.0
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        if out[-1] != b:
            out.append(b)
    return out


def nearest_site(pt, sites):
    best, bd = None, math.inf
    for s in sites:
        d = math.dist(pt, s.pt) - s.r
        if d < bd:
            best, bd = s, d
    return best, bd


def check_roads(world, shapes, sites, cfg, report):
    seen = {}
    bridges = 0
    road_len = {"main": 0.0, "trail": 0.0}
    rivers = shapes["rivers"]
    for s in shapes["roads"]:
        kind = s.get("data-kind")
        L = perimeter(s.pts, False)
        if kind in road_len:
            road_len[kind] += L
        ends = []
        for role, pt in (("start", s.pts[0]), ("end", s.pts[-1])):
            site, d = nearest_site(pt, sites)
            if site is None or d > ROAD_END_SLACK:
                report.error("road", "%s: its %s %s is %s from the nearest site (max %d from a site's disc)" %
                             (s.label, role, fmt_pt(pt), "%d blocks" % d if site else "far", ROAD_END_SLACK))
            ends.append(site)
        rid = s.get("data-id") or ("%s_%s" % (ends[0].id, ends[1].id) if all(ends) else None)
        s.road_id = rid
        if rid:
            if rid in seen:
                report.error("road", "%s: road id %s is used twice (%s)" % (s.label, rid, seen[rid]))
            seen[rid] = s.label
        if not world.coast:
            continue
        wet = 0.0
        wet_at = None
        for k, p in enumerate(sample_path(s.pts, SAMPLE_STEP)):
            is_wet = (not world.on_land(p)) or any(dist_point_path(p, r.pts, False) <= river_half(r) for r in rivers)
            if is_wet:
                wet += SAMPLE_STEP if k else 0.0
                wet_at = wet_at or p
            else:
                if wet:
                    if wet + SAMPLE_STEP > WET_RUN_MAX:
                        report.error("road", "%s crosses water for ~%d blocks near %s (max %d: draw a bridgeable gap or a detour)" %
                                     (s.label, round(wet + SAMPLE_STEP), fmt_pt(wet_at), WET_RUN_MAX))
                    else:
                        bridges += 1
                wet, wet_at = 0.0, None
        if wet:
            if wet + SAMPLE_STEP > WET_RUN_MAX:
                report.error("road", "%s ends in water: a wet run of ~%d blocks near %s (max %d)" %
                             (s.label, round(wet + SAMPLE_STEP), fmt_pt(wet_at), WET_RUN_MAX))
            else:
                bridges += 1
    for need in V1_ROADS:
        if need not in seen:
            report.error("road", "the v1 road %s is missing (data-id=%r, or ends at its two sites)" % (need, need))
    report.stats["bridges"] = bridges
    report.stats["road_main_blocks"] = round(road_len["main"])
    report.stats["road_trail_blocks"] = round(road_len["trail"])
    far = []
    for st in sites:
        a = cfg.anchors.get(st.id)
        if a and a["kind"] in ("build", "settlement", "landmark") and shapes["roads"]:
            d = min(dist_point_path(st.pt, r.pts, False) for r in shapes["roads"])
            if d > ROAD_REACH:
                far.append("%s (%d)" % (st.id, round(d)))
        elif a and a["kind"] in ("build", "settlement", "landmark"):
            far.append(st.id)
    if far:
        report.warn("road", "%d build sites are more than %d blocks from any road: %s" % (len(far), ROAD_REACH, fmt_list(far, 12)))


def check_margins(shapes, sites, report):
    miss = [s.id for s in sites if s.shape.get("data-margin") is None]
    if miss:
        report.warn("margin", "%d sites have no data-margin (exclusion margin round the disc for structure starts): %s" % (len(miss), fmt_list(miss)))
    miss = [getattr(s, "road_id", None) or s.label for s in shapes["roads"] if s.get("data-margin") is None]
    if miss:
        report.warn("margin", "%d roads have no data-margin (exclusion margin round the corridor): %s" % (len(miss), fmt_list(miss)))


def bearing_in(brg, lo, hi):
    brg, lo, hi = brg % 360, lo % 360, hi % 360
    return lo <= brg <= hi if lo <= hi else brg >= lo or brg <= hi


def landmass_gap(a, b):
    best = math.inf
    for p in a.pts:
        best = min(best, dist_point_path(p, b.pts, True))
    for p in b.pts:
        best = min(best, dist_point_path(p, a.pts, True))
    return best


def check_canon(world, shapes, cfg, site_by_id, report):
    for prob in cfg.problems:
        report.error("canon", prob)
    for prob in cfg.jar_problems:
        report.error("attribute", prob)
    rows = []
    for r in cfg.relations:
        a, b = r.get("a"), r.get("b")
        if a not in site_by_id or b not in site_by_id:
            continue
        pa, pb = site_by_id[a].pt, site_by_id[b].pt
        d = math.dist(pa, pb)
        brg = bearing(pb, pa)
        direction = r.get("dir", "any")
        lo, hi = r.get("min", 0), r.get("max", math.inf)
        problems = []
        if not lo <= d <= hi:
            problems.append("distance %d is outside %s..%s" % (round(d), lo, hi if hi != math.inf else "inf"))
        if "bearing" in r:
            if not bearing_in(brg, r["bearing"][0], r["bearing"][1]):
                problems.append("bearing %d deg is outside %d..%d deg" % (round(brg), r["bearing"][0], r["bearing"][1]))
        elif direction in WINDS:
            tol = r.get("tol", default_tolerance(direction))
            if angle_diff(brg, WINDS.index(direction) * 22.5) > tol:
                problems.append("bearing %d deg (%s) is not within %d deg of %s" % (round(brg), wind(brg), round(tol), direction))
        rows.append({"a": a, "b": b, "dir": direction, "min": lo, "max": None if hi == math.inf else hi, "distance": round(d),
                     "bearing": round(brg), "wind": wind(brg), "ok": not problems, "source": r.get("source", "")})
        if problems:
            report.error("canon", "%s is %s of %s, %s..%s blocks: %s (source %s)" %
                         (a, direction, b, lo, hi if hi != math.inf else "inf", "; ".join(problems), r.get("source", "?")))
    report.relations = rows
    for r in cfg.site_rules:
        st = site_by_id.get(r.get("id"))
        if st is None:
            continue
        p = st.pt
        why = []
        for key, ok in (("x_min", p[0] >= r.get("x_min", -math.inf)), ("x_max", p[0] <= r.get("x_max", math.inf)),
                        ("y_min", p[1] >= r.get("y_min", -math.inf)), ("y_max", p[1] <= r.get("y_max", math.inf))):
            if key in r and not ok:
                why.append("%s %s is not %s %s" % ("x" if key[0] == "x" else "y", round(p[0] if key[0] == "x" else p[1]),
                                                   ">=" if key.endswith("min") else "<=", r[key]))
        inside = r.get("inside")
        if inside == "mountains" and not any(point_in_poly(p, m.pts) for m in shapes["mountains"]):
            why.append("not inside a mountain polygon")
        if inside == "mountains_or_hills" and not any(point_in_poly(p, m.pts) for m in shapes["mountains"] + shapes["hills"]):
            why.append("not inside a mountain or hill polygon")
        if inside == "forests":
            types = r.get("forest_types")
            if not any(point_in_poly(p, f.pts) and (not types or f.get("data-type") in types) for f in shapes["forests"]):
                why.append("not inside a forest polygon%s" % (" of type " + "/".join(types) if types else ""))
        if "near_road" in r:
            near = [rd for rd in shapes["roads"] if not r.get("road_kind") or rd.get("data-kind") == r["road_kind"]]
            d = min((dist_point_path(p, rd.pts, False) for rd in near), default=math.inf)
            if d > r["near_road"]:
                why.append("%s from a %s road (max %d)" % ("%d blocks" % d if d < math.inf else "no", r.get("road_kind", ""), r["near_road"]))
        if "lake_width_min" in r:
            lk = world.find(world.lakes, p)
            wd = 0 if lk is None else bbox(lk.pts)[2] - bbox(lk.pts)[0]
            if wd < r["lake_width_min"]:
                why.append("the lake there is %d blocks wide (min %d)" % (wd, r["lake_width_min"]))
        if why:
            report.error("canon", "%s: %s (source %s)" % (st.id, "; ".join(why), r.get("source", "?")))
    for g in cfg.gaps:
        a, b = site_by_id.get(g.get("a")), site_by_id.get(g.get("b"))
        if a is None or b is None:
            continue
        ma, mb = world.landmass(a.pt), world.landmass(b.pt)
        if ma is None or mb is None:
            continue
        if ma is mb:
            report.error("canon", "%s and %s are on the same landmass; the design wants a sea of %s..%s blocks between them (source %s)" %
                         (a.id, b.id, g.get("min"), g.get("max"), g.get("source", "?")))
            continue
        d = landmass_gap(ma, mb)
        if not g.get("min", 0) <= d <= g.get("max", math.inf):
            report.error("canon", "the sea between the landmasses of %s and %s is %d blocks, wanted %s..%s (source %s)" %
                         (a.id, b.id, round(d), g.get("min"), g.get("max"), g.get("source", "?")))


def check_jura(world, shapes, site_by_id, report):
    t = site_by_id.get("tempest")
    if t is None or not shapes["forests"]:
        if t is not None:
            report.warn("jura", "no ancient or dark forest round Tempest: the core (r 200) and band (to r 600) are drawn as forest")
        return
    cover = [f for f in shapes["forests"] if f.get("data-type") in ("ancient", "dark")]
    out = 0
    for k in range(32):
        a = 2 * math.pi * k / 32
        p = (t.x + (JURA_RING - 10) * math.cos(a), t.y + (JURA_RING - 10) * math.sin(a))
        if not any(point_in_poly(p, f.pts) for f in cover):
            out += 1
    if out or not any(point_in_poly(t.pt, f.pts) for f in cover):
        report.warn("jura", "ancient or dark forest does not cover r %d round Tempest (%d of 32 ring points outside): the "
                    "converter paints the rings anyway, the drawing should agree" % (JURA_RING, out))


def box_of(world, shapes):
    pts = [p for s in world.coast + world.lakes for p in s.pts] + [p for s in shapes["roads"] for p in s.pts]
    if not pts:
        return None
    x0, y0, x1, y1 = bbox(pts)
    bx0 = math.floor((x0 - SEA_MARGIN) / REGION_BLOCK) * REGION_BLOCK
    by0 = math.floor((y0 - SEA_MARGIN) / REGION_BLOCK) * REGION_BLOCK
    bx1 = math.ceil((x1 + SEA_MARGIN) / REGION_BLOCK) * REGION_BLOCK
    by1 = math.ceil((y1 + SEA_MARGIN) / REGION_BLOCK) * REGION_BLOCK
    return (bx0, by0, bx1, by1)


def check_size(world, shapes, report):
    st = report.stats
    if not world.coast:
        return
    main = max(world.coast, key=lambda s: abs(area_signed(s.pts)))
    b = bbox(main.pts)
    w, h = b[2] - b[0], b[3] - b[1]
    st["mainland_bbox"] = [round(w), round(h)]
    if w > MAINLAND_ERR[0] or h > MAINLAND_ERR[1]:
        report.error("size", "the mainland is %d x %d blocks, over the limit %d x %d" % (w, h, MAINLAND_ERR[0], MAINLAND_ERR[1]))
    elif w > MAINLAND_WARN[0] or h > MAINLAND_WARN[1]:
        report.warn("size", "the mainland is %d x %d blocks, over %d x %d (recommended about 9,500 x 7,000)" % (w, h, MAINLAND_WARN[0], MAINLAND_WARN[1]))
    box = box_of(world, shapes)
    bw, bh = box[2] - box[0], box[3] - box[1]
    st["design_box"] = {"x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3], "width": bw, "height": bh}
    if bw > BOX_CAP[0] or bh > BOX_CAP[1]:
        report.error("size", "the design box (content + 1,200 of sea, rounded to 512) is %d x %d, over the cap %d x %d" % (bw, bh, BOX_CAP[0], BOX_CAP[1]))
    elif bw > BOX_TARGET[0] or bh > BOX_TARGET[1]:
        report.warn("size", "the design box is %d x %d, above the target %d x %d (cap %d x %d)" % (bw, bh, BOX_TARGET[0], BOX_TARGET[1], BOX_CAP[0], BOX_CAP[1]))
    land = sum(abs(area_signed(s.pts)) for s in world.coast) - sum(abs(area_signed(s.pts)) for s in world.lakes)
    share = land / (bw * bh)
    st["land_share_of_box"] = round(share, 3)
    if share > LAND_SHARE_MAX:
        report.error("size", "land is %d %% of the design box (max %d %%)" % (round(share * 100), LAND_SHARE_MAX * 100))


def compute_stats(world, shapes, sites, report):
    st = report.stats
    land = sum(abs(area_signed(s.pts)) for s in shapes["coast"])
    lakes = sum(abs(area_signed(s.pts)) for s in shapes["lakes"])
    st["land_area_blocks2"] = round(land - lakes)
    st["land_area_km2"] = round((land - lakes) / 1e6, 2)
    st["lake_area_km2"] = round(lakes / 1e6, 2)
    st["coast_length_blocks"] = round(sum(perimeter(s.pts) for s in shapes["coast"]))
    st["river_length_blocks"] = round(sum(perimeter(s.pts, False) for s in shapes["rivers"]))
    for layer in LAYERS:
        if layer != "labels":
            st["count_" + layer] = len(shapes[layer])
    st["count_ridges"] = len(shapes["ridges"])
    tempest = next((s for s in sites if s.id == "tempest"), None)
    if tempest:
        rows = []
        for s in sites:
            if s is not tempest:
                brg = bearing(tempest.pt, s.pt)
                rows.append({"id": s.id, "kind": s.kind, "distance": round(math.dist(tempest.pt, s.pt)),
                             "bearing": round(brg), "wind": wind(brg)})
        rows.sort(key=lambda r: r["distance"])
        report.distances = rows


def check_svg(text, cfg):
    """Run every check. Returns (report, shapes, sites)."""
    report = Report()
    shapes = parse_svg(text, report)
    if shapes is None:
        return report, None, []
    split_mountains(shapes, report)
    check_geometry(shapes, report)
    world = World(shapes)
    check_land(world, shapes, report)
    check_rivers(world, shapes, report)
    check_attrs(world, shapes, cfg, report)
    check_region_cover(world, shapes, report)
    sites, site_by_id = collect_sites(shapes, cfg, report)
    check_sites(world, shapes, cfg, sites, report)
    check_relative_anchors(cfg, site_by_id, report)
    check_roads(world, shapes, sites, cfg, report)
    check_margins(shapes, sites, report)
    check_canon(world, shapes, cfg, site_by_id, report)
    check_jura(world, shapes, site_by_id, report)
    check_size(world, shapes, report)
    compute_stats(world, shapes, sites, report)
    return report, shapes, sites


# ---------------------------------------------------------------------------------------------------------------------
# Report output

def render_text(path, report):
    out = ["map_check: %s" % path, ""]
    out.append("ERRORS (%d)" % len(report.errors))
    out += ["  [%s] %s" % (e["rule"], e["message"]) for e in report.errors] or ["  none"]
    out.append("")
    out.append("WARNINGS (%d)" % len(report.warnings))
    out += ["  [%s] %s" % (e["rule"], e["message"]) for e in report.warnings] or ["  none"]
    out += ["", "STATS"]
    st = report.stats
    if st:
        out.append("  land %s km2 (%s blocks2), lakes %s km2, coast line %s blocks, rivers %s blocks" % (
            st.get("land_area_km2"), st.get("land_area_blocks2"), st.get("lake_area_km2"),
            st.get("coast_length_blocks"), st.get("river_length_blocks")))
        if "mainland_bbox" in st:
            b = st["design_box"]
            out.append("  mainland %d x %d, design box %d x %d (x %d..%d, y %d..%d), land %s of the box" % (
                st["mainland_bbox"][0], st["mainland_bbox"][1], b["width"], b["height"], b["x0"], b["x1"], b["y0"], b["y1"],
                st.get("land_share_of_box")))
        out.append("  roads: main %s blocks, trail %s blocks, %s bridge(s)" % (
            st.get("road_main_blocks", 0), st.get("road_trail_blocks", 0), st.get("bridges", 0)))
        out.append("  shapes: " + ", ".join("%s %s" % (k[6:], v) for k, v in st.items() if k.startswith("count_")))
    out += ["", "DISTANCES from tempest (block distance, compass)"]
    if report.distances:
        for i in range(0, len(report.distances), 3):
            out.append("  " + "".join("%-30s" % ("%s %d %s" % (r["id"], r["distance"], r["wind"])) for r in report.distances[i:i + 3]).rstrip())
    else:
        out.append("  (no tempest site)")
    bad = [r for r in report.relations if not r["ok"]]
    out += ["", "CANON RELATIONS (%d checked, %d failed)" % (len(report.relations), len(bad))]
    for r in bad:
        out.append("  FAIL %s %s of %s: %d blocks, bearing %d (%s); wanted %s..%s" % (
            r["a"], r["dir"], r["b"], r["distance"], r["bearing"], r["wind"], r["min"], r["max"]))
    out += ["", "RESULT: %s (%d error(s), %d warning(s))" % ("OK" if report.ok else "FAIL", len(report.errors), len(report.warnings))]
    return "\n".join(out)


def render_json(path, report):
    return json.dumps({"file": str(path), "ok": report.ok, "errors": report.errors, "warnings": report.warnings,
                       "stats": report.stats, "distances": report.distances, "relations": report.relations},
                      indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------------------------------------------------
# PNG preview (1 px = 8 blocks)

FONT = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "111101101101101", "O": "111101101101111", "P": "111101111100100",
    "Q": "111101101111001", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111",
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111", "3": "110001010001110",
    "4": "101101111001001", "5": "111100110001110", "6": "011100111101111", "7": "111001010010010",
    "8": "111101111101111", "9": "111101111001110", "_": "000000000000111", "-": "000000111000000",
    ".": "000000000000010", " ": "000000000000000",
}

OCEAN, LAND, LAKE, RIVER, MOUNT, HILL = 0, 1, 2, 3, 4, 5
FOREST_IDX = {t: 6 + i for i, t in enumerate(FOREST_TYPES)}
ROAD_MAIN, ROAD_TRAIL, BORDER, COAST_LINE, SITE_DOT, PIN_DOT, TEXT, HALO, GRID_SEA, GRID_LAND, MARGIN_LINE, BIOME_LINE, RIDGE = range(20, 33)
TINT0 = 40
BASE_PALETTE = {
    OCEAN: (186, 212, 234), LAND: (238, 232, 208), LAKE: (110, 165, 225), RIVER: (45, 105, 200),
    MOUNT: (128, 118, 108), HILL: (190, 170, 130),
    FOREST_IDX["light"]: (110, 170, 80), FOREST_IDX["dense"]: (40, 110, 50), FOREST_IDX["dark"]: (30, 60, 50),
    FOREST_IDX["ancient"]: (10, 80, 35), FOREST_IDX["birch"]: (150, 195, 85), FOREST_IDX["taiga"]: (60, 115, 105),
    FOREST_IDX["old_taiga"]: (35, 85, 80), FOREST_IDX["jungle"]: (20, 150, 65), FOREST_IDX["sparse_jungle"]: (130, 190, 90),
    FOREST_IDX["cherry"]: (235, 150, 190), FOREST_IDX["mangrove"]: (90, 110, 60),
    ROAD_MAIN: (110, 50, 15), ROAD_TRAIL: (205, 120, 35), BORDER: (120, 30, 120), COAST_LINE: (35, 55, 85),
    SITE_DOT: (205, 20, 20), PIN_DOT: (215, 120, 15), TEXT: (0, 0, 0), HALO: (255, 255, 255),
    GRID_SEA: (160, 190, 215), GRID_LAND: (205, 198, 170), MARGIN_LINE: (225, 90, 90), BIOME_LINE: (90, 150, 90),
    RIDGE: (70, 60, 55),
}


class Canvas:
    def __init__(self):
        self.w = int(VIEWBOX[2] // PREVIEW_SCALE)
        self.h = int(VIEWBOX[3] // PREVIEW_SCALE)
        self.rows = [bytearray(self.w) for _ in range(self.h)]

    def px(self, p):
        return ((p[0] - VIEWBOX[0]) / PREVIEW_SCALE, (p[1] - VIEWBOX[1]) / PREVIEW_SCALE)

    def fill(self, pts, table, pattern=None):
        """Even-odd scanline fill of a polygon (world points). `table` is a 256-byte translate table, so a layer
        only recolours the pixels it should (land under a region tint, never the sea). pattern: None | 'checker' | 'stipple'."""
        pp = [self.px(p) for p in pts]
        hits = {}
        n = len(pp)
        for i in range(n):
            (x0, y0), (x1, y1) = pp[i], pp[(i + 1) % n]
            if y0 == y1:
                continue
            if y0 > y1:
                x0, y0, x1, y1 = x1, y1, x0, y0
            r0 = max(0, math.ceil(y0 - 0.5))
            r1 = min(self.h - 1, math.ceil(y1 - 0.5) - 1)
            for r in range(r0, r1 + 1):
                hits.setdefault(r, []).append(x0 + (r + 0.5 - y0) * (x1 - x0) / (y1 - y0))
        for r, xs in hits.items():
            xs.sort()
            row = self.rows[r]
            for k in range(0, len(xs) - 1, 2):
                a = max(0, math.ceil(xs[k] - 0.5))
                b = min(self.w, math.ceil(xs[k + 1] - 0.5))
                if b <= a:
                    continue
                if pattern == "checker":
                    a += (a + r) % 2
                    seg = row[a:b:2]
                    row[a:b:2] = seg.translate(table)
                elif pattern == "stipple":
                    a += (-(a + 2 * r)) % 3
                    seg = row[a:b:3]
                    row[a:b:3] = seg.translate(table)
                else:
                    row[a:b] = row[a:b].translate(table)

    def set(self, x, y, idx):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rows[y][x] = idx

    def line(self, p, q, idx, thick=1, dash=0):
        (x0, y0), (x1, y1) = self.px(p), self.px(q)
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            if dash and (k // dash) % 2:
                continue
            t = k / n if n else 0
            x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
            for dx in range(-(thick // 2), thick - thick // 2):
                for dy in range(-(thick // 2), thick - thick // 2):
                    self.set(x + dx, y + dy, idx)

    def polyline(self, pts, idx, thick=1, closed=False, dash=0):
        for i in range(len(pts) - (0 if closed else 1)):
            self.line(pts[i], pts[(i + 1) % len(pts)], idx, thick, dash)

    def disc(self, p, radius_px, idx, ring=False):
        cx, cy = self.px(p)
        r = max(1, radius_px)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if (not ring and d <= r) or (ring and r - 1 <= d <= r):
                    self.set(x, y, idx)

    def text(self, p, s, scale=2, halo=True):
        x0, y0 = int(self.px(p)[0]), int(self.px(p)[1])
        cells = []
        x = x0
        for ch in s.upper():
            g = FONT.get(ch, FONT[" "])
            for row in range(5):
                for col in range(3):
                    if g[row * 3 + col] == "1":
                        cells.append((x + col * scale, y0 + row * scale))
            x += 4 * scale
        if halo:
            for cx, cy in cells:
                for dx in range(-1, scale + 1):
                    for dy in range(-1, scale + 1):
                        self.set(cx + dx, cy + dy, HALO)
        for cx, cy in cells:
            for dx in range(scale):
                for dy in range(scale):
                    self.set(cx + dx, cy + dy, TEXT)


def table_for(mapping):
    t = bytearray(range(256))
    for src, dst in mapping.items():
        t[src] = dst
    return bytes(t)


def blend(c1, c2, f):
    return tuple(round(a * (1 - f) + b * f) for a, b in zip(c1, c2))


def load_png_writer():
    spec = importlib.util.spec_from_file_location("ttl_lerfing_common", COMMON_PNG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.write_png


def render_preview(path, shapes, sites, cfg):
    cv = Canvas()
    letters = sorted(cfg.letters)
    palette = [(0, 0, 0)] * 256
    for k, v in BASE_PALETTE.items():
        palette[k] = v
    tint = {}
    for i, L in enumerate(letters):
        palette[TINT0 + i] = blend(BASE_PALETTE[LAND], cfg.colours.get(L, (200, 200, 200)), 0.38)
        tint[L] = TINT0 + i
    cv.rows = [bytearray([OCEAN]) * cv.w for _ in range(cv.h)]
    land_like = [LAND] + list(tint.values())
    to_land = table_for({OCEAN: LAND})
    for s in shapes["coast"]:
        cv.fill(s.pts, to_land)
    for s in shapes["regions"]:
        idx = tint.get(s.get("data-letter"))
        if idx:
            cv.fill(s.pts, table_for({LAND: idx}))
    for s in shapes["hills"]:
        cv.fill(s.pts, table_for({v: HILL for v in land_like}), "stipple")
    for s in shapes["mountains"]:
        cv.fill(s.pts, table_for({v: MOUNT for v in land_like}), "checker")
    for s in shapes["forests"]:
        idx = FOREST_IDX.get(s.get("data-type"))
        if idx:
            cv.fill(s.pts, table_for({v: idx for v in land_like}), "checker")
    for s in shapes["lakes"]:
        cv.fill(s.pts, table_for({v: LAKE for v in range(256)}))
    for s in shapes["biomes"]:
        cv.polyline(s.pts, BIOME_LINE, 1, True, dash=2)
    # grid every 1,000 blocks, only over open ground so it never hides a layer
    grid = table_for({OCEAN: GRID_SEA, LAND: GRID_LAND})
    for gx in range(-8000, 8001, 1000):
        x = int((gx - VIEWBOX[0]) / PREVIEW_SCALE)
        if 0 <= x < cv.w:
            for y in range(cv.h):
                cv.rows[y][x] = grid[cv.rows[y][x]]
    for gy in range(-6000, 6001, 1000):
        y = int((gy - VIEWBOX[1]) / PREVIEW_SCALE)
        if 0 <= y < cv.h:
            cv.rows[y] = cv.rows[y].translate(grid)
    for s in shapes["rivers"]:
        try:
            thick = max(1, round(float(s.get("data-width")) / PREVIEW_SCALE))
        except (TypeError, ValueError):
            thick = 1
        cv.polyline(s.pts, RIVER, thick)
    for s in shapes["coast"] + shapes["lakes"]:
        cv.polyline(s.pts, COAST_LINE, 1, True)
    for s in shapes["ridges"]:
        cv.polyline(s.pts, RIDGE, 1)
    for s in shapes["regions"]:
        cv.polyline(s.pts, BORDER, 1, True)
    for s in shapes["roads"]:
        main_road = s.get("data-kind") == "main"
        cv.polyline(s.pts, ROAD_MAIN if main_road else ROAD_TRAIL, 2 if main_road else 1, False, dash=0 if main_road else 3)
    for st in sites:
        small = st.r <= 8
        cv.disc(st.pt, max(2, round(st.r / PREVIEW_SCALE)), PIN_DOT if small else SITE_DOT, ring=True)
        cv.disc(st.pt, 2, PIN_DOT if small else SITE_DOT)
    for st in sites:
        cv.text((st.x + st.r + 24, st.y - 20), st.id, 2)
    cv.text((VIEWBOX[0] + 80, VIEWBOX[1] + 80), "1 PX = 8 BLOCKS  GRID 1000 BLOCKS", 2)
    load_png_writer()(path, cv.w, cv.h, cv.rows, 8, palette)


# ---------------------------------------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate world/map.svg and optionally render a preview PNG.")
    ap.add_argument("svg", help="the map, normally world/map.svg")
    ap.add_argument("--preview", metavar="OUT.png", help="render a PNG at 1 px = 8 blocks")
    ap.add_argument("--json", action="store_true", help="print the report as JSON instead of text")
    ap.add_argument("--jar", help="Tensura jar to verify the tensura: biome ids against (or $TTL_TENSURA_JAR)")
    ap.add_argument("--anchors", help="anchors.toml (default: design/data/anchors.toml)")
    ap.add_argument("--landmarks", help="landmarks.toml (default: design/data/landmarks.toml)")
    ap.add_argument("--relations", help="canon relations (default: tools/world/canon_relations.toml)")
    ap.add_argument("--canon", help="canon_regions.json (default: pack/config/ttl/canon_regions.json)")
    ap.add_argument("--biomes", help="allowed biome list (default: tools/world/biomes.txt)")
    ap.add_argument("--sites", help="sites.toml with each site's min_r (default: world/sites.toml; optional)")
    args = ap.parse_args(argv)
    cfg = load_config(args.anchors, args.relations, args.canon, args.biomes, args.landmarks, args.jar, args.sites)
    try:
        text = Path(args.svg).read_text(encoding="utf-8")
    except OSError as e:
        print("map_check: cannot read %s: %s" % (args.svg, e), file=sys.stderr)
        return 2
    report, shapes, sites = check_svg(text, cfg)
    if args.preview:
        if shapes is None:
            print("map_check: no preview, the SVG could not be parsed", file=sys.stderr)
        else:
            render_preview(args.preview, shapes, sites, cfg)
            if not args.json:
                print("preview: %s" % args.preview)
    print(render_json(args.svg, report) if args.json else render_text(args.svg, report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
