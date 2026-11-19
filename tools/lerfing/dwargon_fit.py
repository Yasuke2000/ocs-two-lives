"""Overlay Dwargon's carve footprint on Lerfing's real heights (WP-L7b, design/architecture/lerfing-import.md §3.3).

    python -I tools/lerfing/dwargon_fit.py                                           check dwargon.js on the committed sample
    python -I tools/lerfing/dwargon_fit.py --world <import out dir>                  ... on the imported world itself
    python -I tools/lerfing/dwargon_fit.py --world <dir> --save-sample               rewrite the committed sample
    python -I tools/lerfing/dwargon_fit.py --world <dir> --gate X Z [--base Y]        check another gate / base
    python -I tools/lerfing/dwargon_fit.py --world <dir> --search 40 [--step 2]       scan gates within +-40 of it
    ... --png out.png                                                                  heights + footprint picture
    ... --json                                                                         the report as JSON

Reads the structure files (pack/kubejs/data/ttl/structure/dwargon_*.nbt), the generated footprint
(generated/dwargon_footprint.js: margin, arrival, fill, clear, roof) and TtlDwargon.GATE / BASE from life/dwargon.js,
then every column of the box and its margin: from the imported world (`--world`), else from the committed ground
sample design/data/lerfing/dwargon_ground.png (exact real ground of the box, its margin and SAMPLE_PAD more, cut from
the world with --save-sample; tests/test_dwargon_carve.py runs this check on it), else from the 1:16 rasters (only good
for a rough look; `--rasters` forces them). It simulates what dwargon.js does (place the slabs, clear above the open-sky
columns, fill the gaps and the skirt) on each real column and reports:

- rock cover: real rock between every closed column's highest interior air (footprint `roof`) and the surface, the
  surface lowered by any structure air above it (the cleft over the tunnel); the owner's floor is 6 blocks;
- surface change: box + margin columns whose top block moves (cut: cleft and crack; raised: forecourt fill, gate
  towers) or is replaced at the same height; everything else of Lerfing's surface is untouched;
- the road at the south edge against the real ground (the forecourt must run out onto the apron).

With --search the gate moves over a grid round the start (rotation none: the gate faces south, canon); for each
gate the base is the one that puts the road on the ground at the south edge, and a gate is feasible when that base
still leaves 6 blocks of cover everywhere. Read only; never writes to the world.
"""
import argparse
import json
import os
import re
import statistics
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS)
from lerfing.common import DATA, ROOT, read_png, write_png  # noqa: E402
from lerfing.probe import Rasters, World  # noqa: E402
import verify_build as vb  # noqa: E402

SCRIPT = ROOT / 'pack' / 'kubejs' / 'server_scripts' / 'ttl' / 'life' / 'dwargon.js'
FOOTPRINT = ROOT / 'pack' / 'kubejs' / 'server_scripts' / 'ttl' / 'generated' / 'dwargon_footprint.js'
AIR = 'minecraft:air'
MIN_COVER = 6
SAMPLE = DATA / 'dwargon_ground.png'
SAMPLE_META = DATA / 'dwargon_ground.json'
SAMPLE_PAD = 16


class Sample:
    """The committed exact ground (y + 64, 16-bit) round Dwargon's box; None outside it."""

    def __init__(self, png=SAMPLE, meta=SAMPLE_META):
        self.meta = json.loads(meta.read_text(encoding='utf-8'))
        _, _, self.rows = read_png(str(png))

    def covers(self, x0, z0, x1, z1):
        m = self.meta
        return m['x0'] <= x0 and m['z0'] <= z0 and x1 < m['x0'] + m['width'] and z1 < m['z0'] + m['height']

    def at(self, x, z):
        m = self.meta
        i, j = x - m['x0'], z - m['z0']
        if not (0 <= i < m['width'] and 0 <= j < m['height']) or not self.rows[j][i]:
            return None
        y = self.rows[j][i] - 64
        return {'ground_y': y, 'surface_y': y}


def save_sample(G, x0, z0, x1, z1, source):
    rows = [[G[(x, z)] + 64 if (x, z) in G else 0 for x in range(x0, x1 + 1)] for z in range(z0, z1 + 1)]
    write_png(str(SAMPLE), x1 - x0 + 1, z1 - z0 + 1, rows, depth=16)
    SAMPLE_META.write_text(json.dumps({
        'what': "Lerfing's real ground y + 64 (16-bit grey, 0 = no data) round Dwargon's carve box, written by "
                'tools/lerfing/dwargon_fit.py --save-sample; read by the same tool and tests/test_dwargon_carve.py',
        'x0': x0, 'z0': z0, 'width': x1 - x0 + 1, 'height': z1 - z0 + 1, 'source': source}, indent=1) + '\n',
        encoding='utf-8', newline='\n')


def decode(rle):
    out = []
    for k in range(0, len(rle), 2):
        out += [rle[k]] * rle[k + 1]
    return out


def load_footprint():
    line = next(t for t in FOOTPRINT.read_text(encoding='utf-8').splitlines() if t.startswith('const TtlDwargonFootprint'))
    f = json.loads(line[line.index('{'):])
    n = f['grid'][0] * f['grid'][1]
    for key in ('fill', 'clear', 'bottom', 'roof'):
        f[key] = decode(f[key]) if key in f else [f['none']] * n
    return f


def placement():
    text = SCRIPT.read_text(encoding='utf-8')
    m = re.search(r'GATE:\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)', text)
    b = re.search(r'\bBASE:\s*(-?\d+)', text)
    return int(m.group(1)), int(m.group(2)), int(b.group(1)) if b else None


class Model:
    """Per grid cell (box + margin): the structure's air runs and highest block, the footprint values."""

    def __init__(self, f):
        self.f = f
        _, blocks, _ = vb.load_expected(vb.structure_files('dwargon'))
        m, w, l = f['margin'], f['grid'][0], f['grid'][1]
        self.w, self.l, self.m = w, l, m
        air, top = {}, {}
        for (x, y, z), s in blocks.items():
            i = (z + m) * w + (x + m)
            if s == AIR:
                air.setdefault(i, set()).add(y)
            elif y > top.get(i, -1):
                top[i] = y
        self.air, self.top = air, top
        # roof columns: the first structure air above the roof caps the real cover (the cleft over the tunnel)
        none = f['none']
        self.cap = {}
        for i, r in enumerate(f['roof']):
            if r == none:
                continue
            a = self.air.get(i, ())
            above = [y for y in a if y > r + 1 and y - 1 not in a]
            self.cap[i] = min(above) - 1 if above else None

    def column(self, i, g, s, B):
        """(new top y, replaced) of one column after the placement; g = real ground y, s = real surface y."""
        f, none = self.f, self.f['none']
        air = self.air.get(i, ())
        clear, fill = f['clear'][i], f['fill'][i]
        c0 = B + clear if clear != none else None
        nat = g
        if c0 is not None and nat >= c0:
            nat = c0 - 1
        while nat - B in air:
            nat -= 1
        made = []
        st = self.top.get(i)
        if st is not None and (c0 is None or B + st < c0):
            made.append(B + st)
        if fill != none and B + fill - 1 > g:
            made.append(B + fill - 1)
        new = max([nat] + made)
        return new, new in made


def heights(sampler, x0, z0, x1, z1):
    g, s = {}, {}
    for z in range(z0, z1 + 1):
        for x in range(x0, x1 + 1):
            p = sampler(x, z)
            if p and p.get('ground_y') is not None:
                g[(x, z)] = p['ground_y']
                s[(x, z)] = p.get('surface_y') if p.get('surface_y') is not None else p['ground_y']
    return g, s


def pct(vals, q):
    vals = sorted(vals)
    return vals[min(len(vals) - 1, int(q * len(vals)))] if vals else None


def corner(f, gx, gz):
    return gx - f['arrival'][0] - f['margin'], gz - f['arrival'][2] - f['margin']


def road_base(f, G, gx, gz):
    """The base that puts the road on the real ground at the south edge (median over the last 16 rows of probes)."""
    cx, cz = corner(f, gx, gz)
    m, sz = f['margin'], f['size'][2]
    ys = [G[(cx + m + px, cz + m + pz)] for px, pz in f['probes'] if pz >= sz - 16 and (cx + m + px, cz + m + pz) in G]
    return int(statistics.median(ys)) + 1 - f['arrival'][1] if ys else None


def cover_base(model, G, gx, gz):
    """The highest base that keeps MIN_COVER blocks of real rock over every roof column."""
    f = model.f
    cx, cz = corner(f, gx, gz)
    best = None
    for i, r in enumerate(f['roof']):
        if r == f['none']:
            continue
        g = G.get((cx + i % model.w, cz + i // model.w))
        if g is None:
            return None
        b = g - r - MIN_COVER
        best = b if best is None else min(best, b)
    return best


def evaluate(model, G, S, gx, gz, B):
    f, none, w = model.f, model.f['none'], model.w
    cx, cz = corner(f, gx, gz)
    covers, worst, missing, exposed = [], [], 0, 0
    lowered, raised, replaced, same = [], [], 0, 0
    box = (f['margin'], f['margin'], f['margin'] + f['size'][0], f['margin'] + f['size'][2])
    out_box = {'lowered': 0, 'raised': 0, 'replaced': 0}
    gate_row = f['margin'] + f['arrival'][2] - 16  # the back of the gate wall (blueprint GATE_Z)
    parts = {'crack': [], 'cleft': []}
    for i in range(w * model.l):
        x, z = cx + i % w, cz + i // w
        if (x, z) not in G:
            missing += 1
            continue
        g, s = G[(x, z)], S[(x, z)]
        r = f['roof'][i]
        if r != none:
            top = g if model.cap[i] is None else min(g, B + model.cap[i])
            cov = top - (B + r)
            covers.append(cov)
            if cov < MIN_COVER:
                worst.append((cov, x, z))
        st = model.top.get(i)
        if f['clear'][i] == none and st is not None and B + st >= g and i // w < gate_row:
            exposed += 1  # a closed column's lining (no open air above it) at or above the real surface
        new, rep = model.column(i, g, s, B)
        inside = box[0] <= i % w < box[2] and box[1] <= i // w < box[3]
        if new < g:
            lowered.append(g - new)
            if f['clear'][i] != none:
                parts['crack' if i // w < gate_row else 'cleft'].append(g - new)
        elif new > g:
            raised.append(new - g)
        elif rep:
            replaced += 1
        else:
            same += 1
        if not inside and (new != g or rep):
            out_box['lowered' if new < g else 'raised' if new > g else 'replaced'] += 1
    n = w * model.l - missing
    road = road_base(f, G, gx, gz)
    worst.sort()
    return {
        'gate': [gx, gz], 'base': B, 'walk_y': B + f['arrival'][1], 'rotation': 'none (gate faces south)',
        'corner': [cx + f['margin'], B, cz + f['margin']], 'columns': n, 'missing': missing,
        'cover': {'columns': len(covers), 'min': min(covers) if covers else None, 'p10': pct(covers, 0.1),
                  'median': pct(covers, 0.5), 'max': max(covers) if covers else None,
                  'under_6': len(worst), 'worst': [list(t) for t in worst[:8]], 'exposed': exposed},
        'surface': {'changed': len(lowered) + len(raised) + replaced, 'changed_share': round((len(lowered) + len(raised) + replaced) / n, 3) if n else None,
                    'lowered': len(lowered), 'lowered_median': pct(lowered, 0.5), 'lowered_max': max(lowered) if lowered else 0,
                    'raised': len(raised), 'raised_median': pct(raised, 0.5), 'raised_max': max(raised) if raised else 0,
                    'replaced_same_height': replaced, 'unchanged': same, 'outside_box': out_box,
                    'cut_volume': sum(lowered),
                    'parts': {k: {'columns': len(v), 'median': pct(v, 0.5), 'max': max(v) if v else 0, 'volume': sum(v)}
                              for k, v in parts.items()}},
        'road': {'south_edge_base': road, 'road_minus_ground': None if road is None else B - road},
    }


def search(model, G, S, gx, gz, radius, step):
    f = model.f
    rows = []
    for dz in range(-radius, radius + 1, step):
        for dx in range(-radius, radius + 1, step):
            x, z = gx + dx, gz + dz
            road, cov = road_base(f, G, x, z), cover_base(model, G, x, z)
            if road is None or cov is None:
                continue
            rows.append((cov - road, x, z, road, cov))
    ok = sorted((r for r in rows if r[0] >= 0), key=lambda r: (-r[0], abs(r[1] - gx) + abs(r[2] - gz)))
    out = []
    for slack, x, z, road, cov in ok[:12]:
        e = evaluate(model, G, S, x, z, road)
        out.append({'gate': [x, z], 'base': road, 'slack': slack, 'cover_min': e['cover']['min'],
                    'cover_median': e['cover']['median'], 'changed': e['surface']['changed']})
    out.sort(key=lambda r: (r['changed'], -r['cover_min']))
    return {'scanned': len(rows), 'feasible': len(ok), 'best': out}


def picture(model, G, gx, gz, B, path):
    """Greyscale real heights of box + margin, the city under the rock blue (magenta: cover under 6), the cleft yellow,
    the skylight crack red."""
    f, none, w, l = model.f, model.f['none'], model.w, model.l
    cx, cz = corner(f, gx, gz)
    ys = [G[k] for k in G]
    lo, hi = min(ys), max(ys)
    pal = [(int(40 + 200 * k / 63),) * 3 for k in range(64)] + [(70, 110, 230), (240, 210, 40), (230, 50, 50), (200, 40, 200)]
    rows = []
    for gz_ in range(l):
        row = []
        for gx_ in range(w):
            i = gz_ * w + gx_
            g = G.get((cx + gx_, cz + gz_))
            v = 0 if g is None else int(63 * (g - lo) / max(1, hi - lo))
            a = model.air.get(i)
            if f['roof'][i] != none:
                top = g if model.cap[i] is None else min(g, B + model.cap[i])
                v = 67 if g is not None and top - (B + f['roof'][i]) < MIN_COVER else 64
            elif a and f['clear'][i] != none:
                v = 66 if gz_ < f['margin'] + f['arrival'][2] - 16 else 65
            row.append(v)
        rows.append(row)
    write_png(path, w, l, rows, palette=pal)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--world', help='imported world folder (holds region/); without it the 1:16 rasters are used')
    ap.add_argument('--rasters', nargs='?', const=str(DATA), help='use the 1:16 rasters (rough)')
    ap.add_argument('--save-sample', action='store_true', help='write the committed ground sample (needs --world)')
    ap.add_argument('--gate', type=int, nargs=2, metavar=('X', 'Z'))
    ap.add_argument('--base', type=int)
    ap.add_argument('--search', type=int, metavar='R')
    ap.add_argument('--step', type=int, default=2)
    ap.add_argument('--png')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    f = load_footprint()
    gx, gz, B = placement()
    if a.gate:
        gx, gz = a.gate
    if a.base is not None:
        B = a.base
    model = Model(f)
    reach = max(a.search or 0, SAMPLE_PAD if a.save_sample else 0)
    cx, cz = corner(f, gx, gz)
    area = (cx - reach, cz - reach, cx + model.w - 1 + reach, cz + model.l - 1 + reach)
    if a.save_sample and not a.world:
        raise SystemExit('--save-sample needs --world')
    if a.world:
        sampler, source = World(a.world).at, 'world ' + a.world
    elif not a.rasters and SAMPLE.exists() and Sample().covers(*area):
        sampler, source = Sample().at, 'committed sample ' + SAMPLE.name
    else:
        sampler, source = Rasters(a.rasters or str(DATA)).at, 'rasters 1:16 (rough)'
    G, S = heights(sampler, *area)
    if a.save_sample:
        save_sample(G, *area, source="Lerfing's imported world (tools/lerfing/import.py), exact columns")
    if B is None:
        B = road_base(f, G, gx, gz)
    rep = evaluate(model, G, S, gx, gz, B)
    rep['source'] = source
    if a.search:
        rep['search'] = search(model, G, S, gx, gz, a.search, a.step)
    if a.png:
        picture(model, G, gx, gz, B, a.png)
    if a.json:
        print(json.dumps(rep, indent=1))
        return 0
    c, s, r = rep['cover'], rep['surface'], rep['road']
    print(f"Dwargon carve at gate ({gx}, {gz}), base y {B} (walk y {rep['walk_y']}), rotation none; {rep['source']}")
    print(f"  rock cover over {c['columns']} closed columns: min {c['min']}, p10 {c['p10']}, median {c['median']}, "
          f"max {c['max']}; {c['under_6']} under {MIN_COVER}" + (f" (worst {c['worst']})" if c['under_6'] else '') +
          f"; {c['exposed']} lining columns exposed")
    print(f"  surface: {s['changed']} of {rep['columns']} columns change ({100 * s['changed_share']:.1f} % of box + margin): "
          f"{s['lowered']} cut (median {s['lowered_median']}, max {s['lowered_max']}), {s['raised']} raised "
          f"(median {s['raised_median']}, max {s['raised_max']}), {s['replaced_same_height']} re-surfaced at the same "
          f"height; outside the box {s['outside_box']}")
    for k, v in s['parts'].items():
        print(f"    {k}: {v['columns']} columns cut, median {v['median']}, max {v['max']} ({v['volume']} blocks)")
    print(f"  road at the south edge: base {r['south_edge_base']} would put it on the ground (this base is "
          f"{r['road_minus_ground']:+d})" if r['south_edge_base'] is not None else '  road: no ground data')
    if a.search:
        sr = rep['search']
        print(f"  search +-{a.search} step {a.step}: {sr['feasible']} of {sr['scanned']} gates feasible; best:")
        for b in sr['best']:
            print(f"    gate {b['gate']}, base {b['base']}: cover min {b['cover_min']} median {b['cover_median']}, "
                  f"{b['changed']} surface columns change (slack {b['slack']})")
    return 0 if c['under_6'] == 0 and c['exposed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
