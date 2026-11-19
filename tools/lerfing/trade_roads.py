"""Plan the trade roads of design/data/trade_roads/roads.toml on Lerfing's map (life/trade_roads.js lays them).

    python -I tools/lerfing/trade_roads.py plan <id> [--world <import dir>]   write design/data/trade_roads/<id>.json
    python -I tools/lerfing/trade_roads.py show <id>                         print the stored plan's figures

1. Coarse: A* over the 1:16 rasters (heights16, landmask16) from `from` through every `via` to `to`, 8 neighbours.
   Cost per step = length x (1 + slope penalty) + water: the open sea is closed, a lake or river cell costs WATER_STEP
   per block plus WATER_ENTER for every entry (a short river crossing is a bridge, a lake is a detour). Closed: Lerfing's
   keepouts (anchors.toml), Tempest's and Dwargon's boxes (the ends excepted), the `avoid` discs.
2. Fine (with --world): the same search on the imported world's exact columns every FINE blocks, inside a corridor of
   CORRIDOR blocks round the coarse path; slopes from the ground smoothed over +-4 blocks. Without --world the coarse
   path is used as it is (and says so in `source`).
3. Smoothing: string pulling (a straight segment replaces a run of the path when it costs at most PULL x as much and is
   at most SEG_MAX long), so the road runs in straight stretches with gentle bends.
4. Profile, one sample per block of arc length: the ground, a running median over 7 samples, the ends fixed (`to_y`),
   bridges over every wet run (deck = water surface + 2, never below the banks), then the grade limit (`max_grade`)
   forwards and backwards; rounded to block heights. Cut and fill per sample are in the stats.

The JSON holds `points` (the polyline, [x, z]), `profile` (surface y per block of arc length, sample i at arc i),
`bridges` ([s0, s1] arc ranges, inclusive), the stats and the source. life/trade_roads.js walks the same polyline
at the same arc steps (rasterize() below is its mirror; tests/trade_roads.js checks they agree).
"""
import argparse
import heapq
import json
import math
import os
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing.common import CHUNKS_X, CHUNKS_Z, DATA, SEA, read_png  # noqa: E402
from lerfing.terrain import Terrain  # noqa: E402
import anchor_refs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ROADS = ROOT / 'design' / 'data' / 'trade_roads'
CONFIG = ROADS / 'roads.toml'
GENERATED = ROOT / 'pack' / 'kubejs' / 'server_scripts' / 'ttl' / 'generated'

FINE = 2
CORRIDOR = 96
SMOOTH = 4            # blocks either side for the slope the search sees
WATER_STEP = 6.0      # per block of water crossed
WATER_ENTER = 30.0    # per entry into water
PULL = 1.04
SEG_MAX = 48
MEDIAN = 3            # running median half-window (7 samples)
KEEP_PAD = 8          # blocks kept clear of keepout boxes


def load_config():
    with CONFIG.open('rb') as f:
        return tomllib.load(f)


def place(where, spec):
    return anchor_refs.point(where, spec['anchor'], spec.get('dx', 0), spec.get('dz', 0))


def settlement_boxes():
    """Tempest's and Dwargon's worked areas (box + margin), as their scripts compute them (gen_data)."""
    import gen_data  # noqa: E402 (heavy import, only here)
    return {'tempest': gen_data.settlement_box('tempest.js', 'LANDMARK', 'tempest_footprint.js'),
            'dwargon': gen_data.settlement_box('dwargon.js', 'GATE', 'dwargon_footprint.js')}


def dwargon_core():
    """Dwargon's box without its terrain margin (the road may pave the margin up to the blueprint's own road)."""
    x0, z0, x1, z1 = settlement_boxes()['dwargon']
    m = footprint('dwargon_footprint.js')['margin']
    return x0 + m, z0 + m, x1 - m, z1 - m


def footprint(name):
    line = next(t for t in (GENERATED / name).read_text(encoding='utf-8').splitlines()
                if t.startswith('const ') and 'Footprint = ' in t)
    return json.loads(line[line.index('{'):])


# ------------------------------------------------------------------ obstacles

class Blocked:
    """Closed areas: boxes (x0, z0, x1, z1) and discs (x, z, r)."""

    def __init__(self, boxes=(), discs=()):
        self.boxes = list(boxes)
        self.discs = list(discs)

    def __call__(self, x, z):
        for b in self.boxes:
            if b[0] <= x <= b[2] and b[1] <= z <= b[3]:
                return True
        for d in self.discs:
            if (x - d[0]) ** 2 + (z - d[1]) ** 2 <= d[2] ** 2:
                return True
        return False


def obstacles(cfg, ends):
    """Blocked areas for one road: keepouts + pad, the settlement boxes (minus a gap at each end), the avoid discs."""
    boxes = [(k['x0'] - KEEP_PAD, k['z0'] - KEEP_PAD, k['x1'] + KEEP_PAD, k['z1'] + KEEP_PAD) for k in anchor_refs.keepouts()]
    for name, b in settlement_boxes().items():
        boxes.append(b)
    discs = [(*place('roads.toml avoid', a), a['r']) for a in cfg.get('avoid', [])]
    blocked = Blocked(boxes, discs)
    # The ends lie at a settlement's edge: open a 24-block disc round each so the search can leave and arrive.
    opened = [(x, z) for x, z in ends]
    return lambda x, z: blocked(x, z) and all((x - ox) ** 2 + (z - oz) ** 2 > 24 ** 2 for ox, oz in opened)


# ------------------------------------------------------------------ search

def smoothed(t, r):
    """Ground averaged over +-r blocks (None where any sample is missing)."""
    k = max(1, r // t.step)
    out = [None] * (t.w * t.h)
    for j in range(t.h):
        for i in range(t.w):
            s = n = 0
            for jj in range(max(0, j - k), min(t.h, j + k + 1)):
                for ii in range(max(0, i - k), min(t.w, i + k + 1)):
                    g = t.ground[jj * t.w + ii]
                    if g is not None:
                        s += g
                        n += 1
            out[j * t.w + i] = s / n if n else None
    return out


def step_cost(d, ga, gb, wet_a, wet_b):
    if ga is None or gb is None:
        return None
    s = abs(gb - ga) / d
    c = d * (1 + 8 * max(0.0, s - 0.1) + 60 * max(0.0, s - 0.3))
    if wet_b:
        c += d * WATER_STEP + (0 if wet_a else WATER_ENTER)
    return c


def astar(t, sm, start, goal, closed, sea=lambda x, z: False, allowed=None):
    """Cheapest grid path (list of (x, z) sample positions) from start to goal (block positions, snapped)."""
    def snap(p):
        return ((p[0] - t.x0) // t.step, (p[1] - t.z0) // t.step)
    s, g = snap(start), snap(goal)
    if not (0 <= s[0] < t.w and 0 <= s[1] < t.h and 0 <= g[0] < t.w and 0 <= g[1] < t.h):
        raise SystemExit(f'{start} or {goal} is outside the terrain grid')

    def wet(i, j):
        return t.water[j * t.w + i] is not None

    def h(i, j):
        return math.hypot(i - g[0], j - g[1]) * t.step
    best = {s: 0.0}
    prev = {}
    heap = [(h(*s), 0.0, s)]
    nbr = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while heap:
        _, c, (i, j) = heapq.heappop(heap)
        if (i, j) == g:
            break
        if c > best.get((i, j), math.inf):
            continue
        for di, dj in nbr:
            ni, nj = i + di, j + dj
            if not (0 <= ni < t.w and 0 <= nj < t.h):
                continue
            if allowed is not None and (ni, nj) not in allowed:
                continue
            x, z = t.x0 + ni * t.step, t.z0 + nj * t.step
            if closed(x, z) or sea(x, z):
                continue
            d = math.hypot(di, dj) * t.step
            sc = step_cost(d, sm[j * t.w + i], sm[nj * t.w + ni], wet(i, j), wet(ni, nj))
            if sc is None:
                continue
            nc = c + sc
            if nc < best.get((ni, nj), math.inf):
                best[(ni, nj)] = nc
                prev[(ni, nj)] = (i, j)
                heapq.heappush(heap, (nc + h(ni, nj), nc, (ni, nj)))
    if g not in best:
        raise SystemExit(f'no path from {start} to {goal} on {t.source}')
    path = [g]
    while path[-1] != s:
        path.append(prev[path[-1]])
    path.reverse()
    return [(t.x0 + i * t.step, t.z0 + j * t.step) for i, j in path]


def line_cost(t, sm, a, b, closed, sea):
    """Cost of the straight segment a -> b sampled every block (None when it crosses something closed)."""
    n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]))))
    c = 0.0
    prev = None
    for k in range(n + 1):
        x = round(a[0] + (b[0] - a[0]) * k / n)
        z = round(a[1] + (b[1] - a[1]) * k / n)
        if closed(x, z) or sea(x, z):
            return None
        idx = t.index(x, z)
        if idx is None:
            return None
        cur = (sm[idx], t.water[idx] is not None)
        if prev is not None:
            d = math.hypot(b[0] - a[0], b[1] - a[1]) / n
            sc = step_cost(d, prev[0], cur[0], prev[1], cur[1])
            if sc is None:
                return None
            c += sc
        prev = cur
    return c


def string_pull(t, sm, path, closed, sea):
    """Straight segments over the grid path: from each kept point, the farthest later point whose straight segment costs
    at most PULL x the path between them (and is at most SEG_MAX long)."""
    # cumulative path cost
    cum = [0.0]
    for a, b in zip(path, path[1:]):
        lc = line_cost(t, sm, a, b, closed, sea)
        cum.append(cum[-1] + (lc if lc is not None else math.hypot(b[0] - a[0], b[1] - a[1])))
    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        j_best = i + 1
        for j in range(i + 2, len(path)):
            if math.hypot(path[j][0] - path[i][0], path[j][1] - path[i][1]) > SEG_MAX:
                break
            lc = line_cost(t, sm, path[i], path[j], closed, sea)
            if lc is not None and lc <= PULL * (cum[j] - cum[i]) + 0.5:
                j_best = j
        out.append(path[j_best])
        i = j_best
    return out


# ------------------------------------------------------------------ arc samples and the profile (mirrored in JS)

def arc_samples(points):
    """Positions (float x, z) every block of arc length along the polyline, the last point included. Plain sqrt, not
    hypot: life/trade_roads.js (Math.sqrt) must get the very same floats."""
    out = []
    carry = 0.0
    for (ax, az), (bx, bz) in zip(points, points[1:]):
        seg = math.sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az))
        s = carry
        while s < seg - 1e-9:
            f = s / seg
            out.append((ax + (bx - ax) * f, az + (bz - az) * f))
            s += 1.0
        carry = s - seg
    out.append(tuple(points[-1]))
    return out


def median(vals):
    v = sorted(vals)
    return v[len(v) // 2]


def build_profile(ground, wet_top, max_grade, fixed=None):
    """Surface y per sample. ground[i] = top ground y (the bed under water), wet_top[i] = water surface y or None.
    fixed = {i: y} (ends). Returns (profile, bridges as [s0, s1] runs)."""
    n = len(ground)
    dry = [ground[i] for i in range(n) if wet_top[i] is None] or [64]
    g = [ground[i] if wet_top[i] is None else None for i in range(n)]
    # dry ground through wet runs: the lower bank, for the median
    for i in range(n):
        if g[i] is None:
            left = next((g[k] for k in range(i - 1, -1, -1) if g[k] is not None), None)
            right = next((ground[k] for k in range(i + 1, n) if wet_top[k] is None), None)
            g[i] = min(v for v in (left, right, dry[0]) if v is not None)
    y = [float(median(g[max(0, i - MEDIAN):i + MEDIAN + 1])) for i in range(n)]
    bridges = []
    i = 0
    while i < n:
        if wet_top[i] is not None:
            j = i
            while j + 1 < n and wet_top[j + 1] is not None:
                j += 1
            deck = max(max(wet_top[k] for k in range(i, j + 1)) + 2,
                       ground[i - 1] if i > 0 else -999, ground[j + 1] if j + 1 < n else -999)
            bridges.append([i, j])
            for k in range(i, j + 1):
                y[k] = float(deck)
            i = j + 1
        else:
            i += 1
    locks = {k: y[k] for b in bridges for k in range(b[0], b[1] + 1)}
    for k, v in (fixed or {}).items():
        locks[k] = float(v)
    for k, v in locks.items():
        y[k] = v
    # grade limit: raise towards locked samples (ramps to bridges and the ends), then smooth both ways
    for _ in range(3):
        for i in range(1, n):
            if i in locks:
                continue
            y[i] = min(max(y[i], y[i - 1] - max_grade), y[i - 1] + max_grade)
        for i in range(n - 2, -1, -1):
            if i in locks:
                continue
            y[i] = min(max(y[i], y[i + 1] - max_grade), y[i + 1] + max_grade)
    return [int(round(v)) for v in y], bridges


def rasterize(points, profile, half):
    """{(x, z): (y, arc index, |offset|)} for every paved column (mirror of TtlTradeRoads.columns in JS)."""
    cols = {}
    samples = arc_samples(points)
    lens, dirs = [], []
    for (ax, az), (bx, bz) in zip(points, points[1:]):
        dx, dz = bx - ax, bz - az
        L = math.sqrt(dx * dx + dz * dz)
        lens.append(L)
        dirs.append((dx / (L or 1), dz / (L or 1)))
    seg = 0
    acc = 0.0
    steps = int(math.floor(half * 2)) * 2
    for i, (px, pz) in enumerate(samples):
        while seg < len(lens) - 1 and i >= acc + lens[seg] - 1e-9:
            acc += lens[seg]
            seg += 1
        dx, dz = dirs[seg]
        nx, nz = -dz, dx
        y = profile[min(i, len(profile) - 1)]
        for h in (0, 1):
            hi = h * 0.5
            if hi and i == len(samples) - 1:
                continue
            cx, cz = px + dx * hi, pz + dz * hi
            for s in range(-steps, steps + 1):
                o = s * half / steps
                x, z = int(math.floor(cx + nx * o + 0.5)), int(math.floor(cz + nz * o + 0.5))
                cur = cols.get((x, z))
                if cur is None or abs(o) < cur[2]:
                    cols[(x, z)] = (y, i, abs(o))
    return cols


def lanterns(road, cfg):
    """Lantern posts (x, z, arc) as life/trade_roads.js lanterns() computes them."""
    every = cfg.get('lantern_every', 0)
    if not every:
        return []
    samples = arc_samples(road["points"])
    out = []
    side = 1
    for i in range(every, len(samples) - every // 2, every):
        if any(b[0] - 2 <= i <= b[1] + 2 for b in road['bridges']):
            continue
        a = samples[max(0, i - 1)]
        b = samples[min(len(samples) - 1, i + 1)]
        L = math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) or 1
        nx, nz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        off = cfg['half'] + 1.5
        out.append((int(math.floor(samples[i][0] + nx * off * side + 0.5)), int(math.floor(samples[i][1] + nz * off * side + 0.5)), i))
        side = -side
    return out


# ------------------------------------------------------------------ the planner

def sea_test(rdir=str(DATA)):
    _, _, mask = read_png(os.path.join(rdir, 'landmask16.png'))

    def sea(x, z):
        col, row = (x >> 4) - CHUNKS_X[0], (z >> 4) - CHUNKS_Z[0]
        return not (0 <= row < len(mask) and 0 <= col < len(mask[0])) or mask[row][col] == SEA
    return sea


def plan(rid, world=None, log=print):
    cfg_all = load_config()
    if rid not in cfg_all:
        raise SystemExit(f'roads.toml has no road {rid!r}')
    cfg = cfg_all[rid]
    where = f'roads.toml [{rid}]'
    start = place(where, cfg['from'])
    goal = place(where, cfg['to'])
    stops = [start] + [place(where, v) for v in cfg.get('via', [])] + [goal]
    closed = obstacles(cfg, [start, goal])
    sea = sea_test()
    xs = [p[0] for p in stops]
    zs = [p[1] for p in stops]
    pad = 400
    coarse_t = Terrain.from_rasters(min(xs) - pad, min(zs) - pad, max(xs) + pad, max(zs) + pad)
    coarse_sm = smoothed(coarse_t, 16)
    coarse = []
    for a, b in zip(stops, stops[1:]):
        seg = astar(coarse_t, coarse_sm, a, b, closed, sea)
        coarse += seg if not coarse else seg[1:]
    coarse = [stops[0]] + coarse[1:-1] + [stops[-1]]
    log(f'coarse path on the rasters: {len(coarse)} cells')
    if world:
        bx0 = min(p[0] for p in coarse) - CORRIDOR
        bz0 = min(p[1] for p in coarse) - CORRIDOR
        bx1 = max(p[0] for p in coarse) + CORRIDOR
        bz1 = max(p[1] for p in coarse) + CORRIDOR
        t = Terrain.from_world(world, bx0, bz0, bx1, bz1, FINE)
        sm = smoothed(t, SMOOTH)
        allowed = set()
        for (ax, az), (bx, bz) in zip(coarse, coarse[1:]):
            n = max(1, int(math.hypot(bx - ax, bz - az) // FINE))
            for k in range(n + 1):
                cx = ax + (bx - ax) * k / n
                cz = az + (bz - az) * k / n
                ci, cj = int((cx - t.x0) // FINE), int((cz - t.z0) // FINE)
                r = CORRIDOR // FINE
                for dj in range(-r, r + 1):
                    for di in range(-r, r + 1):
                        if di * di + dj * dj <= r * r:
                            allowed.add((ci + di, cj + dj))
        fine = []
        for a, b in zip(stops, stops[1:]):
            seg = astar(t, sm, a, b, closed, sea, allowed)
            fine += seg if not fine else seg[1:]
        fine = [stops[0]] + fine[1:-1] + [stops[-1]]
        log(f'fine path on the world ({t.source}): {len(fine)} samples')
        source = f'{t.source}, corridor {CORRIDOR} round the raster path'
    else:
        t, sm, fine = coarse_t, coarse_sm, coarse
        source = 'rasters 1:16 only (no --world: coarse path, ground per chunk)'
    # string pulling per leg so every stop stays on the road
    pts = []
    legs = []
    for a, b in zip(stops, stops[1:]):
        ia = min(range(len(fine)), key=lambda k: (fine[k][0] - a[0]) ** 2 + (fine[k][1] - a[1]) ** 2)
        ib = min(range(len(fine)), key=lambda k: (fine[k][0] - b[0]) ** 2 + (fine[k][1] - b[1]) ** 2)
        legs.append(fine[ia:ib + 1])
    for leg in legs:
        pulled = string_pull(t, sm, leg, closed, sea)
        pts += pulled if not pts else pulled[1:]
    pts[0], pts[-1] = start, goal
    samples = arc_samples(pts)
    ground, wet = [], []
    for x, z in samples:
        a = t.at(int(round(x)), int(round(z)))
        ground.append(a['ground'] if a and a['ground'] is not None else 64)
        wet.append(a['water'] if a else None)
    fixed = {}
    if 'to_y' in cfg:
        fixed[len(samples) - 1] = cfg['to_y']
    if 'from_y' in cfg:
        fixed[0] = cfg['from_y']
    prof, bridges = build_profile(ground, wet, cfg['max_grade'], fixed)
    cut = [g - y for g, y, w in zip(ground, prof, wet) if w is None and g > y]
    fill = [y - g for g, y, w in zip(ground, prof, wet) if w is None and y > g]
    grades = [abs(b - a) for a, b in zip(prof, prof[1:])]
    run = best_run = 0
    for gr in grades:
        run = run + 1 if gr == 0 else 0
    rises = sum(1 for gr in grades if gr)
    length = len(samples) - 1
    steep = max((sum(grades[i:i + 12]) / 12 for i in range(0, max(1, len(grades) - 11))), default=0)
    stats = {
        'length': length,
        'vertices': len(pts),
        'climb': sum(max(0, b - a) for a, b in zip(prof, prof[1:])),
        'descent': sum(max(0, a - b) for a, b in zip(prof, prof[1:])),
        'y_min': min(prof), 'y_max': max(prof),
        'max_step': max(grades) if grades else 0,
        'steepest_12': round(steep, 3),
        'block_steps': rises,
        'cut_max': max(cut, default=0), 'cut_columns_over_3': sum(1 for c in cut if c > 3),
        'fill_max': max(fill, default=0), 'fill_columns_over_3': sum(1 for f in fill if f > 3),
        'bridges': len(bridges), 'bridge_blocks': sum(b[1] - b[0] + 1 for b in bridges),
        'stops': [list(p) for p in stops],
    }
    del best_run
    out = {
        'id': rid,
        'title': cfg['title'],
        'generated_by': 'python -I tools/lerfing/trade_roads.py plan ' + rid + (' --world <import dir>' if world else ''),
        'source': source,
        'points': [[int(round(x)), int(round(z))] for x, z in pts],
        'profile': prof,
        'bridges': bridges,
        'stats': stats,
    }
    return out


def write(rid, data):
    p = ROADS / f'{rid}.json'
    body = json.dumps({k: v for k, v in data.items() if k not in ('points', 'profile')}, indent=1, sort_keys=True)
    # points and profile on single lines: the file stays readable and diffs stay small
    text = body[:-2] + ',\n "points": ' + json.dumps(data['points'], separators=(',', ':')) + \
        ',\n "profile": ' + json.dumps(data['profile'], separators=(',', ':')) + '\n}\n'
    json.loads(text)
    p.write_text(text, encoding='utf-8', newline='\n')
    return p


def stored(rid):
    p = ROADS / f'{rid}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan')
    p.add_argument('id')
    p.add_argument('--world', help='imported world folder (holds region/); without it the 1:16 rasters only')
    s = sub.add_parser('show')
    s.add_argument('id')
    args = ap.parse_args(argv)
    if args.cmd == 'plan':
        data = plan(args.id, args.world)
        path = write(args.id, data)
        print(json.dumps(data['stats'], indent=1))
        print(f'wrote {path.relative_to(ROOT).as_posix()}')
    else:
        d = stored(args.id)
        if d is None:
            raise SystemExit(f'no plan for {args.id}; run plan first')
        print(json.dumps(d['stats'], indent=1))


if __name__ == '__main__':
    main()
