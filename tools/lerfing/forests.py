"""Plan the forest patches of design/data/forests/patches.toml on Lerfing's map (life/forests.js plants them).

    python -I tools/lerfing/forests.py plan <id> --world <import dir> [--tensura-jar <jar>]   write design/data/forests/<id>.json
    python -I tools/lerfing/forests.py measure <id> --world <import dir>                      tree cover per ring, before/after

Giants are Tensura's ancient-forest trees (tensura:ancient_forest/ancient_forest_tree_1..6, the pieces of the
tensura:ancient_forest/tree jigsaw; the labyrinth variants hold a Labyrinth portal and are never used), placed as
templates with the jigsaw's own depth (start_height -5: layers 0-4 are roots under the ground). Their size and trunk
come from the Tensura jar (TEMPLATES below, checked against the jar when one is found). The understory is vanilla tree
features (`/place feature`), which grow only on dirt-like soil.

Spots: a seeded dart throw on a jittered grid (giants first, then the understory between them); a spot is kept when
it lies in the ring, on dry soil (the world's exact columns: no water, sand, rock or terracotta under the trunk, a giant's
trunk area within 4 blocks of level), its whole crown (giants: the rotated template box) outside every `clear` and
`keep_clear` box, Lerfing's keepouts and the settlement boxes, and its trunk clear of the lanes and the trade roads.
The JSON lists [template, x, z, rotation] per giant (x, z = the trunk centre) and [feature, x, z] per understory tree.
"""
import argparse
import collections
import glob
import json
import math
import os
import random
import sys
import tomllib
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing.terrain import Terrain  # noqa: E402
from lerfing import trade_roads  # noqa: E402
import anchor_refs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FORESTS = ROOT / 'design' / 'data' / 'forests'
CONFIG = FORESTS / 'patches.toml'
STEP = 2
ROOTS = 5          # template layers under the ground (the jigsaw's start_height -5)
LEVEL = 4          # a giant's trunk area may vary this much in ground height
ROTATIONS = ('none', 'clockwise_90', '180', 'counterclockwise_90')

# size [x, y, z], trunk centre [x, z] (centroid of the wood at the ground layer y 5) and trunk radius of each template,
# read from tensura-neoforge-2.0.1.5.jar (`plan`/`measure` check them against the jar when one is found).
TEMPLATES = {
    'tensura:ancient_forest/ancient_forest_tree_1': {'size': [39, 41, 42], 'trunk': [17, 18], 'trunk_r': 5},
    'tensura:ancient_forest/ancient_forest_tree_2': {'size': [39, 38, 37], 'trunk': [18, 18], 'trunk_r': 5},
    'tensura:ancient_forest/ancient_forest_tree_3': {'size': [51, 45, 50], 'trunk': [25, 27], 'trunk_r': 6},
    'tensura:ancient_forest/ancient_forest_tree_4': {'size': [38, 41, 37], 'trunk': [20, 18], 'trunk_r': 5},
    'tensura:ancient_forest/ancient_forest_tree_5': {'size': [36, 33, 36], 'trunk': [17, 16], 'trunk_r': 3},
    'tensura:ancient_forest/ancient_forest_tree_6': {'size': [38, 42, 41], 'trunk': [21, 20], 'trunk_r': 4},
}
# Crown radius of the understory features (for the cover figures only).
FEATURE_CROWN = {'minecraft:dark_oak': 3.5, 'minecraft:mega_spruce': 4, 'minecraft:mega_pine': 3.5,
                 'minecraft:fancy_oak': 3.5, 'minecraft:super_birch_bees_0002': 2.5, 'minecraft:azalea_tree': 2.5}


def load_config():
    with CONFIG.open('rb') as f:
        return tomllib.load(f)


# ------------------------------------------------------------------ templates

def find_jar():
    home = Path(os.environ.get('LOCALAPPDATA', Path.home()))
    for p in sorted(glob.glob(str(home / 'ocs-two-lives' / '*' / 'server' / 'mods' / 'tensura-neoforge-*.jar'))):
        return p
    return None


def read_templates(jar):
    """{id: {size, trunk, trunk_r, crown}} from the jar's structure files (stdlib NBT reader of tools/nbt.py)."""
    out = {}
    with zipfile.ZipFile(jar) as z:
        for tid in TEMPLATES:
            ns, path = tid.split(':', 1)
            raw = z.read(f'data/{ns}/structure/{path}.nbt')
            root = _read_nbt(raw)
            pal = [e['Name'] for e in root['palette']]
            wood = [(b['pos'][0], b['pos'][2]) for b in root['blocks']
                    if b['pos'][1] == ROOTS and ('wood' in pal[b['state']] or 'log' in pal[b['state']])]
            tx = round(sum(p[0] for p in wood) / len(wood))
            tz = round(sum(p[1] for p in wood) / len(wood))
            tr = max(math.ceil(math.hypot(p[0] - tx, p[1] - tz)) for p in wood)
            cols = {(b['pos'][0], b['pos'][2]) for b in root['blocks'] if pal[b['state']] != 'minecraft:air'}
            out[tid] = {'size': list(root['size']), 'trunk': [tx, tz], 'trunk_r': tr, 'cols': cols}
    return out


def _read_nbt(raw):
    import tempfile
    import nbt  # noqa: E402
    with tempfile.NamedTemporaryFile(suffix='.nbt', delete=False) as f:
        f.write(raw)
        name = f.name
    try:
        return nbt.read_gzip(name)
    finally:
        os.unlink(name)


# ------------------------------------------------------------------ geometry (mirrored in life/forests.js)

def rotate(rot, lx, lz):
    """Template-local offset -> world offset for a /place template rotation (pivot = the placement corner)."""
    if rot == 'clockwise_90':
        return -lz, lx
    if rot == '180':
        return -lx, -lz
    if rot == 'counterclockwise_90':
        return lz, -lx
    return lx, lz


def giant_box(t, x, z, rot):
    """(corner x, corner z, box x0, z0, x1, z1) of template t placed so its trunk centre stands on (x, z)."""
    ox, oz = rotate(rot, t['trunk'][0], t['trunk'][1])
    cx, cz = x - ox, z - oz
    ax, az = rotate(rot, t['size'][0] - 1, t['size'][2] - 1)
    return cx, cz, min(cx, cx + ax), min(cz, cz + az), max(cx, cx + ax), max(cz, cz + az)


def box_hit(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def seg_dist(px, pz, ax, az, bx, bz):
    vx, vz = bx - ax, bz - az
    L2 = vx * vx + vz * vz
    f = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / L2))
    return math.hypot(px - (ax + f * vx), pz - (az + f * vz))


def lane_segment(box, side, toward, length):
    """The lane's centre segment: from the middle of the box's side, `length` blocks towards the point `toward`."""
    x0, z0, x1, z1 = box
    sx, sz = {'west': (x0, (z0 + z1) / 2), 'east': (x1, (z0 + z1) / 2),
              'north': ((x0 + x1) / 2, z0), 'south': ((x0 + x1) / 2, z1)}[side]
    dx, dz = toward[0] - sx, toward[1] - sz
    L = math.hypot(dx, dz) or 1.0
    return sx, sz, sx + dx / L * length, sz + dz / L * length


# ------------------------------------------------------------------ the planner

def weighted(rng, table):
    keys = sorted(table)
    total = sum(table[k] for k in keys)
    r = rng.random() * total
    for k in keys:
        r -= table[k]
        if r < 0:
            return k
    return keys[-1]


def patch_geometry(pid, cfg):
    """Everything both the planner and the cover figures need: centre, closed boxes, lanes, road segments."""
    where = f'patches.toml [{pid}]'
    centre = anchor_refs.point(where, cfg['centre'])
    boxes = []
    for c in cfg.get('clear', []):
        ax, az = anchor_refs.point(where, c['anchor'])
        boxes.append((ax + c['x0'], az + c['z0'], ax + c['x1'], az + c['z1']))
    for k in cfg.get('keep_clear', []):
        b = k['offline']
        p = k.get('pad', 0)
        boxes.append((b[0] - p, b[1] - p, b[2] + p, b[3] + p))
    boxes += [(k['x0'], k['z0'], k['x1'], k['z1']) for k in anchor_refs.keepouts()]
    boxes += list(trade_roads.settlement_boxes().values())
    lanes = []
    for ln in cfg.get('lanes', []):
        toward = anchor_refs.point(where, ln['toward'])
        lanes.append((lane_segment(ln['offline'], ln['side'], toward, ln['length']), ln['half']))
    roads = []
    for p in sorted(trade_roads.ROADS.glob('*.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        half = trade_roads.load_config().get(d['id'], {}).get('half', 2)
        pts = d['points']
        roads += [((a[0], a[1], b[0], b[1]), half) for a, b in zip(pts, pts[1:])]
    return centre, boxes, lanes, roads


def near_roads(roads, x, z, gap):
    return any(seg_dist(x, z, *s) < half + gap for s, half in roads)


def near_lanes(lanes, x, z, gap):
    return any(seg_dist(x, z, *s) < half + gap for s, half in lanes)


def soil_ok(t, x, z):
    a = t.at(x, z)
    return a is not None and a['ground'] is not None and a['water'] is None and a['cls'] == 'soil'


def plan(pid, world, templates=None, log=print):
    cfg_all = load_config()
    if pid not in cfg_all:
        raise SystemExit(f'patches.toml has no patch {pid!r}')
    cfg = cfg_all[pid]
    tpl = templates or TEMPLATES
    centre, boxes, lanes, roads = patch_geometry(pid, cfg)
    cx, cz = centre
    R = cfg['outer'] + 40
    t = Terrain.from_world(world, cx - R, cz - R, cx + R, cz + R, STEP)
    rng = random.Random(cfg['seed'])
    giants, under = [], []
    seen = collections.Counter()

    def ring(x, z, outer):
        r = math.hypot(x - cx, z - cz)
        return cfg['inner'] <= r <= outer

    def jitter_grid(cell, outer):
        pts = []
        n = int(outer // cell) + 1
        for j in range(-n, n + 1):
            for i in range(-n, n + 1):
                pts.append((cx + int((i + rng.random()) * cell), cz + int((j + rng.random()) * cell)))
        rng.shuffle(pts)
        return pts

    gs = cfg['giant_spacing']
    for x, z in jitter_grid(gs * 0.7, cfg['giants_outer']):
        if not ring(x, z, cfg['giants_outer']):
            continue
        seen['giant candidates'] += 1
        if any(math.hypot(x - g[1], z - g[2]) < gs for g in giants):
            seen['giant: too close'] += 1
            continue
        tid = weighted(rng, cfg['giants'])
        rot = ROTATIONS[rng.randrange(4)]
        tp = tpl[tid]
        b = giant_box(tp, x, z, rot)[2:]
        if any(box_hit(b, o) for o in boxes):
            seen['giant: crown in a kept box'] += 1
            continue
        r = tp['trunk_r']
        if near_roads(roads, x, z, cfg['road_gap'] + r) or near_lanes(lanes, x, z, r + 1):
            seen['giant: road or lane'] += 1
            continue
        pts = [(x, z)] + [(x + dx, z + dz) for dx in (-r, 0, r) for dz in (-r, 0, r) if dx or dz]
        if not all(soil_ok(t, px, pz) for px, pz in pts):
            seen['giant: not dry soil'] += 1
            continue
        ys = [t.at(px, pz)['ground'] for px, pz in pts]
        if max(ys) - min(ys) > LEVEL:
            seen['giant: trunk area not level'] += 1
            continue
        giants.append([tid, x, z, rot])
    us = cfg['understory_spacing']
    feats = []
    for x, z in jitter_grid(us * 0.75, cfg['outer']):
        if not ring(x, z, cfg['outer']):
            continue
        seen['understory candidates'] += 1
        if any(math.hypot(x - g[1], z - g[2]) < tpl[g[0]]['trunk_r'] + 4 for g in giants):
            seen['understory: under a giant'] += 1
            continue
        if any(math.hypot(x - u[1], z - u[2]) < us for u in feats):
            seen['understory: too close'] += 1
            continue
        if any(o[0] - 3 <= x <= o[2] + 3 and o[1] - 3 <= z <= o[3] + 3 for o in boxes):
            seen['understory: in a kept box'] += 1
            continue
        if near_roads(roads, x, z, cfg['road_gap']) or near_lanes(lanes, x, z, 2):
            seen['understory: road or lane'] += 1
            continue
        if not all(soil_ok(t, px, pz) for px, pz in ((x, z), (x + 2, z), (x - 2, z), (x, z + 2), (x, z - 2))):
            seen['understory: not dry soil'] += 1
            continue
        fid = weighted(rng, cfg['understory'])
        feats.append([fid, x, z])
    gkeys = sorted(cfg['giants'])
    fkeys = sorted(cfg['understory'])
    giants.sort(key=lambda g: (g[2], g[1]))
    feats.sort(key=lambda u: (u[2], u[1]))
    data = {
        'id': pid,
        'title': cfg['title'],
        'generated_by': f'python -I tools/lerfing/forests.py plan {pid} --world <import dir>',
        'source': t.source,
        'centre': list(centre),
        'templates': {k: {kk: tpl[k][kk] for kk in ('size', 'trunk', 'trunk_r')} for k in gkeys},
        'features': fkeys,
        'giant_keys': gkeys,
        'giants': [[gkeys.index(g[0]), g[1], g[2], ROTATIONS.index(g[3])] for g in giants],
        'understory': [[fkeys.index(u[0]), u[1], u[2]] for u in feats],
        'stats': {'giants': len(giants), 'understory': len(feats), 'rejected': dict(sorted(seen.items()))},
    }
    log(json.dumps(data['stats'], indent=1))
    return data, t


# ------------------------------------------------------------------ cover figures

RINGS = {'tempest': [(60, 110), (110, 200), (200, 250)], 'treyni': [(25, 80), (80, 180)]}


def crowns(data, templates):
    """Set of (x, z) block columns under a planned crown (giants: their template columns; understory: a disc)."""
    cols = set()
    for ti, x, z, ri in data['giants']:
        tid = data['giant_keys'][ti]
        tp = templates[tid]
        rot = ROTATIONS[ri]
        cx, cz = giant_box(tp, x, z, rot)[:2]
        for lx, lz in tp.get('cols', ()):
            ox, oz = rotate(rot, lx, lz)
            cols.add((cx + ox, cz + oz))
    for fi, x, z in data['understory']:
        r = FEATURE_CROWN.get(data['features'][fi], 3)
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dz * dz <= r * r:
                    cols.add((x + dx, z + dz))
    return cols


def cover(pid, t, data, templates, rings=None):
    """{ring: {samples, land, before, after}} tree cover on the terrain samples (land = dry samples)."""
    cx, cz = data['centre']
    new = crowns(data, templates) if data else set()
    out = {}
    for r0, r1 in rings or RINGS.get(pid, [(0, 250)]):
        n = land = before = after = 0
        for x, z, k in t.coords():
            r = math.hypot(x - cx, z - cz)
            if not (r0 <= r < r1) or t.ground[k] is None:
                continue
            n += 1
            if t.water[k] is None:
                land += 1
            b = bool(t.tree[k])
            before += b
            after += b or (x, z) in new
        out[f'{r0}-{r1}'] = {'samples': n, 'land_share': round(land / n, 3) if n else None,
                             'before': round(before / n, 3) if n else None, 'after': round(after / n, 3) if n else None}
    return out


def stored(pid):
    p = FORESTS / f'{pid}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None


def write(pid, data):
    p = FORESTS / f'{pid}.json'
    head = {k: v for k, v in data.items() if k not in ('giants', 'understory')}
    text = json.dumps(head, indent=1, sort_keys=True)[:-2] + ',\n "giants": [\n  ' + ',\n  '.join(
        json.dumps(g, separators=(',', ':')) for g in data['giants']) + '\n ],\n "understory": [\n  ' + ',\n  '.join(
        json.dumps(u, separators=(',', ':')) for u in data['understory']) + '\n ]\n}\n'
    json.loads(text)
    p.write_text(text, encoding='utf-8', newline='\n')
    return p


def templates_with_crowns(jar):
    if not jar:
        return None
    got = read_templates(jar)
    for tid, v in got.items():
        want = TEMPLATES[tid]
        if (v['size'], v['trunk'], v['trunk_r']) != (want['size'], want['trunk'], want['trunk_r']):
            raise SystemExit(f'{tid} in {jar}: size {v["size"]} trunk {v["trunk"]} r {v["trunk_r"]}, '
                             f'TEMPLATES says {want}: update TEMPLATES (the jar changed)')
    return got


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('plan', 'measure'):
        p = sub.add_parser(name)
        p.add_argument('id')
        p.add_argument('--world', required=True, help='imported world folder (holds region/)')
        p.add_argument('--tensura-jar', default=find_jar())
    args = ap.parse_args(argv)
    tpls = templates_with_crowns(args.tensura_jar)
    if args.cmd == 'plan':
        data, t = plan(args.id, args.world, tpls)
        path = write(args.id, data)
        print(f'wrote {path.relative_to(ROOT).as_posix()}')
    else:
        data = stored(args.id)
        if data is None:
            raise SystemExit(f'no plan for {args.id}; run plan first')
        cfg = load_config()[args.id]
        cx, cz = data['centre']
        R = cfg['outer'] + 40
        t = Terrain.from_world(args.world, cx - R, cz - R, cx + R, cz + R, STEP)
        if tpls is None:
            print('no Tensura jar found: giant crowns counted as their trunk only', file=sys.stderr)
        print(json.dumps(cover(args.id, t, data, tpls or TEMPLATES), indent=1))


if __name__ == '__main__':
    main()
