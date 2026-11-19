"""Jura verification of Lerfing's imported map (design/architecture/lerfing-import.md §3.2, §3.6; WP-L8).

    python -I tools/lerfing/jura_check.py --world <import out dir> [--step 8] [--json out.json] [--png out.png]

Samples the STORED biomes of the imported world (read only) round Tempest (1720, 900) at the 4x4 biome-cell centres,
exactly where the import tool decided the repaint, and checks the owner's rings (repaint.json "jura"):

  * core r 200 = tensura:ancient_forest, except water, rivers and beach (repaint.json "keep");
  * band 200..600 = minecraft:dark_forest, same exceptions;
  * the rim (Jura's outline beyond the band) has no ancient_forest and no dark_forest;
  * every sample equals what rules.area_biome says (the import applied exactly the rule);
  * the Life 2 arrival (anchors.toml arrival) is dry, on the rim, in a non-deadly biome, and its 40-block search area too.

Then the two assessments of WP-L8: the beach in the core (how much of it, whether it lets a soul skirt the ancient
forest on the way to the green) and Tempest's own footprints (early village, town, city) for slope and water.
Exit code 1 when a check fails. Stdlib only.
"""
import argparse
import collections
import heapq
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing.common import RULES, Rules, write_png  # noqa: E402
from lerfing.probe import World  # noqa: E402
import anchor_refs  # noqa: E402

# design/data/anchors.toml (WP-L4): the check follows the anchors the pack data uses.
TEMPEST = anchor_refs.point('anchors.toml', 'tempest')
ARRIVAL = anchor_refs.point('anchors.toml', 'arrival')
GREEN = 56                       # the Life 2 magicule shelter round Tempest (life/mortal_immunity.js)
CORE_BIOME = 'tensura:ancient_forest'
BAND_BIOME = 'minecraft:dark_forest'
DEADLY = {CORE_BIOME, BAND_BIOME}   # area magicule above the 500 of every unlisted biome (Tensura biome_magicule)

# (name, blueprint size x/z, arrival offset x/z in the blueprint, terrain margin): blueprints/tempest*.py + _footprint
FOOTPRINTS = (
    ('early village', 91, (45, 57), 8),
    ('town', 137, (68, 68), 8),
    ('city', 191, (95, 95), 8),
)


# ------------------------------------------------------------------ pure logic (unit tested, no world needed)

def dist(x, z, c=TEMPEST):
    return math.hypot(x - c[0], z - c[1])


def kind(p):
    """'void', 'water' (water or ice over the ground) or 'land' for a probe column."""
    if p is None or p.get('class') == 'void':
        return 'void'
    return 'water' if p.get('water_y') is not None or p.get('class') == 'water' else 'land'


def classify(sample, rules):
    """(expected, verdict) for one sample {x, z, biome, kind}: what the repaint rules say it must be.

    verdict 'kept' = the stored biome is one the area rules never repaint (ocean, river, beach, swamp, caves) or the
    column is wet; 'ok' = stored equals area_biome; 'rim' = no ring applies and the stored biome is not a ring biome;
    otherwise 'WRONG'."""
    stored = sample['biome']
    exp = rules.area_biome(sample['x'], sample['z'])
    if sample['kind'] != 'land' or rules.kept(stored):
        return exp, 'kept'
    if exp is None:
        return exp, 'rim' if stored not in DEADLY else 'WRONG'
    return exp, 'ok' if stored == exp else 'WRONG'


def min_deadly_walk(samples, step, centre=TEMPEST, inner=GREEN, outer=200, blocked=(), bad=(CORE_BIOME,)):
    """Fewest blocks of `bad` biomes (default tensura:ancient_forest) a walker must cross from radius `outer` to the green.

    Dijkstra over the sample lattice (8 neighbours); entering an ancient_forest cell costs `step`, every other cell
    (land, beach, river, lake) costs nothing. `blocked` = cells that cannot be entered (pass the wet cells to ask for
    a dry-foot route; leave it empty when a soul may swim). Returns the blocks or None when the green is not reached.
    `samples` maps (x, z) -> biome."""
    inf = float('inf')
    starts = [k for k in samples if outer - step <= dist(k[0], k[1], centre) < outer + step and k not in blocked]
    best = {}
    heap = []
    for k in starts:
        c = step if samples[k] in bad else 0
        best[k] = c
        heapq.heappush(heap, (c, k))
    while heap:
        c, k = heapq.heappop(heap)
        if c > best.get(k, inf):
            continue
        if dist(k[0], k[1], centre) <= inner:
            return c
        for dx in (-step, 0, step):
            for dz in (-step, 0, step):
                if not dx and not dz:
                    continue
                n = (k[0] + dx, k[1] + dz)
                if n not in samples or n in blocked:
                    continue
                nc = c + (step if samples[n] in bad else 0)
                if nc < best.get(n, inf):
                    best[n] = nc
                    heapq.heappush(heap, (nc, n))
    return None


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, int(q * len(sorted_vals)))]


def footprint_stats(cols, step):
    """Slope, water and ground figures of a box. `cols` maps (x, z) -> probe column dict (land or water)."""
    n = len(cols)
    ys = sorted(c['ground_y'] for c in cols.values() if c.get('ground_y') is not None)
    wet = [c for c in cols.values() if kind(c) == 'water']
    depth = sorted(c['water_depth'] for c in wet if c.get('water_depth') is not None)
    med = pct(ys, 0.5)
    slopes = []
    for (x, z), c in cols.items():
        for d in ((step, 0), (0, step)):
            o = cols.get((x + d[0], z + d[1]))
            if o and c.get('ground_y') is not None and o.get('ground_y') is not None:
                slopes.append(abs(c['ground_y'] - o['ground_y']) / step)
    slopes.sort()
    off = [abs(y - med) for y in ys]
    blocks = collections.Counter(c.get('ground_block') for c in cols.values() if kind(c) == 'land')
    biomes = collections.Counter(c.get('biome') for c in cols.values())
    top = collections.Counter(c.get('top_block') for c in cols.values())
    return {
        'columns': n,
        'water_share': round(len(wet) / n, 3) if n else None,
        'water_max_depth': depth[-1] if depth else 0,
        'lava_surface_columns': top.get('minecraft:lava', 0),
        'ground_min': ys[0] if ys else None, 'ground_p10': pct(ys, 0.1), 'ground_median': med,
        'ground_p90': pct(ys, 0.9), 'ground_max': ys[-1] if ys else None,
        'relief_p90_p10': (pct(ys, 0.9) - pct(ys, 0.1)) if ys else None,
        'slope_mean': round(sum(slopes) / len(slopes), 3) if slopes else None,
        'slope_p95': round(pct(slopes, 0.95), 3) if slopes else None,
        'slope_max': round(slopes[-1], 3) if slopes else None,
        'steep_share_gt_0_5': round(sum(1 for s in slopes if s > 0.5) / len(slopes), 3) if slopes else None,
        'within_2_of_median': round(sum(1 for o in off if o <= 2) / len(off), 3) if off else None,
        'within_4_of_median': round(sum(1 for o in off if o <= 4) / len(off), 3) if off else None,
        'cut_over_8': sum(1 for y in ys if med is not None and y - med > 8),
        'fill_over_8': sum(1 for y in ys if med is not None and med - y > 8),
        'ground_blocks': dict(blocks.most_common(5)),
        'biomes': dict(biomes.most_common(5)),
    }


# ------------------------------------------------------------------ the sweep

def sweep(world, centre, radius, step, rules):
    """All cell-centre samples with exact stored biomes: {(x, z): {x, z, biome, kind, ground_y}}."""
    lo_x = (centre[0] - radius) // 4 * 4 + 2
    lo_z = (centre[1] - radius) // 4 * 4 + 2
    out = {}
    cx0, cx1 = (centre[0] - radius) >> 4, (centre[0] + radius) >> 4
    cz0, cz1 = (centre[1] - radius) >> 4, (centre[1] + radius) >> 4
    for cz in range(cz0, cz1 + 1):
        for cx in range(cx0, cx1 + 1):
            for bz in range(cz * 16, cz * 16 + 16):
                if (bz - lo_z) % step or abs(bz - centre[1]) > radius:
                    continue
                for bx in range(cx * 16, cx * 16 + 16):
                    if (bx - lo_x) % step or abs(bx - centre[0]) > radius:
                        continue
                    p = world.at(bx, bz)
                    if p is None:
                        continue
                    out[(bx, bz)] = {'x': bx, 'z': bz, 'biome': p.get('biome'), 'kind': kind(p),
                                     'ground_y': p.get('ground_y')}
            world.chunks.pop((cx, cz), None)
    return out


def sweep_box(world, x0, z0, x1, z1, step):
    cols = {}
    for z in range(z0, z1 + 1, step):
        for x in range(x0, x1 + 1, step):
            p = world.at(x, z)
            if p:
                cols[(x, z)] = p
    return cols


# ------------------------------------------------------------------ report

class Report:
    def __init__(self):
        self.lines, self.checks, self.data = [], [], {}

    def out(self, s=''):
        self.lines.append(s)
        print(s)

    def check(self, name, ok, detail):
        self.checks.append({'check': name, 'ok': bool(ok), 'detail': detail})
        self.out('  [%s] %s: %s' % ('PASS' if ok else 'FAIL', name, detail))


def table(rep, title, counter, total):
    rep.out('    %s' % title)
    for b, n in counter.most_common():
        rep.out('      %-34s %6d  %5.1f %%' % (b, n, 100.0 * n / total if total else 0))


def run(args):
    rules = Rules.load(args.rules)
    world = World(world=args.world)
    rep = Report()
    j = rules.jura
    assert j['centre'] == list(TEMPEST), 'repaint.json jura.centre moved: update TEMPEST'
    core, band, wob = j['core'], j['band'], j.get('wobble', 0)

    rep.out('Jura check: stored biomes of %s' % args.world)
    rep.out('Tempest %s, core r %d, band r %d, wobble +-%d, lattice step %d (cell centres), radius %d'
            % (TEMPEST, core, band, wob, args.step, args.radius))

    s = sweep(world, TEMPEST, args.radius, args.step, rules)
    rep.out('samples: %d' % len(s))
    clip = j.get('clip') or {}

    def in_clip(x, z):
        return clip['x'][0] <= x < clip['x'][1] and clip['z'][0] <= z < clip['z'][1]

    # per-sample verdicts
    wrong = []
    verdicts = collections.Counter()
    for k, v in s.items():
        v['d'] = dist(v['x'], v['z'])
        v['exp'], v['verdict'] = classify(v, rules)
        verdicts[v['verdict']] += 1
        if v['verdict'] == 'WRONG' and in_clip(v['x'], v['z']):
            wrong.append(v)

    def zone(lo, hi, clipped=True):
        return [v for v in s.values() if lo <= v['d'] < hi and (not clipped or in_clip(v['x'], v['z']))]

    def land(vs):
        return [v for v in vs if v['kind'] == 'land']

    rep.out()
    rep.out('1. Rings (exact radius from Tempest; the rule jitters every edge by +-%d, so "certain" zones are '
            'inside r %d and outside r %d..)' % (wob, core - wob, band + wob))
    z_core = zone(0, core)
    z_core_c = zone(0, core - wob)
    z_band_c = zone(core + wob, band - wob)
    z_rim = zone(band + wob, args.radius + 1)
    for title, vs in (('core r < %d (nominal)' % core, z_core),
                      ('core certain r < %d' % (core - wob), z_core_c),
                      ('band certain r %d..%d' % (core + wob, band - wob), z_band_c),
                      ('rim r >= %d (inside Jura clip)' % (band + wob), z_rim)):
        c = collections.Counter('%s%s' % (v['biome'], '' if v['kind'] == 'land' else ' (%s)' % v['kind']) for v in vs)
        table(rep, '%s: %d samples' % (title, len(vs)), c, len(vs))

    def exceptions(vs):
        return [v for v in vs if v['kind'] != 'land' or rules.kept(v['biome'])]

    def non_exc(vs):
        return [v for v in vs if v['kind'] == 'land' and not rules.kept(v['biome'])]

    rep.out()
    rep.out('   checks')
    ne = non_exc(z_core_c)
    bad = [v for v in ne if v['biome'] != CORE_BIOME]
    rep.check('core r<%d is ancient_forest (water, rivers, beach excepted)' % (core - wob), not bad,
              '%d of %d non-exception samples are not ancient_forest' % (len(bad), len(ne)))
    nom = non_exc(z_core)
    share = sum(1 for v in nom if v['biome'] == CORE_BIOME) / len(nom) if nom else 0
    rep.check('core r<%d nominal: ancient_forest share of non-exception samples' % core, share >= 0.9,
              '%.1f %% (the rest is the +-%d wobble band: dark_forest)' % (100 * share, wob))
    ne = non_exc(z_band_c)
    bad = [v for v in ne if v['biome'] != BAND_BIOME]
    rep.check('band r %d..%d is dark_forest (water, rivers, beach excepted)' % (core + wob, band - wob), not bad,
              '%d of %d non-exception samples are not dark_forest: %s'
              % (len(bad), len(ne), dict(collections.Counter(v['biome'] for v in bad).most_common(4))))
    bad = [v for v in z_rim if v['kind'] == 'land' and v['biome'] in DEADLY]
    rep.check('rim r>=%d has no ancient_forest / dark_forest' % (band + wob), not bad,
              '%d deadly-biome land samples outside the band%s'
              % (len(bad), (' e.g. ' + str([(v['x'], v['z'], v['biome']) for v in bad[:3]])) if bad else ''))
    rep.check('every sample in the Jura clip equals area_biome (the import applied the rule exactly)', not wrong,
              '%d of %d samples differ%s' % (len(wrong), sum(verdicts.values()),
                                              (' e.g. ' + str([(v['x'], v['z'], v['biome'], v['exp']) for v in wrong[:3]]))
                                              if wrong else ''))
    exc_core = exceptions(z_core)
    rep.out('   exceptions kept in the core (r < %d): %d of %d samples' % (core, len(exc_core), len(z_core)))
    rep.data['verdicts'] = dict(verdicts)

    # 2. arrival
    rep.out()
    rep.out('2. Life 2 arrival %s' % (ARRIVAL,))
    d = dist(*ARRIVAL)
    ap = world.at(*ARRIVAL)
    wx = ap
    ring = rules.ring_of(*ARRIVAL)
    rep.out('   distance from Tempest %.0f blocks; column: ground y %s (%s), surface %s, water_y %s, biome %s'
            % (d, ap['ground_y'], ap['ground_block'], ap['top_block'], ap['water_y'], ap['biome']))
    rep.check('arrival column is dry land', kind(wx) == 'land', 'class %s, water over ground: %s'
              % (wx['class'], wx['water_y']))
    rep.check('arrival is on the rim (outside the band + wobble)', ring is None and d > band + wob,
              'ring_of=%s, %.0f blocks from Tempest, band edge at %d' % (ring, d, band + wob))
    rep.check('arrival biome is non-deadly', ap['biome'] not in DEADLY, ap['biome'])
    area = sweep_box(world, ARRIVAL[0] - 40, ARRIVAL[1] - 40, ARRIVAL[0] + 40, ARRIVAL[1] + 40, 4)
    ak = collections.Counter(kind(p) for p in area.values())
    ab = collections.Counter(p['biome'] for p in area.values())
    ay = sorted(p['ground_y'] for p in area.values() if p.get('ground_y') is not None)
    dry_near = [p for (x, z), p in area.items() if math.hypot(x - ARRIVAL[0], z - ARRIVAL[1]) <= 16]
    rep.check('arrival: 16-block neighbourhood fully dry', all(kind(p) == 'land' for p in dry_near),
              '%d of %d columns wet' % (sum(1 for p in dry_near if kind(p) != 'land'), len(dry_near)))
    rep.check('arrival: the 40-block search area has no deadly biome', not any(b in DEADLY for b in ab),
              'biomes %s' % dict(ab.most_common(4)))
    rep.out('   40-block area: %d columns, water %.1f %%, ground y p10/p50/p90 = %s/%s/%s (relief %s)'
            % (len(area), 100.0 * ak.get('water', 0) / len(area), pct(ay, .1), pct(ay, .5), pct(ay, .9),
               pct(ay, .9) - pct(ay, .1)))
    peaks = [math.hypot(x - ARRIVAL[0], z - ARRIVAL[1]) for (x, z), p in area.items() if p['biome'] == 'minecraft:stony_peaks']
    rep.out('   note: %.0f %% of that area is stony_peaks (the repainted Canaat apron; 500 magicule like the rim, but '
            'Tensura mountain spawns); nearest %s blocks from the arrival'
            % (100.0 * len(peaks) / len(area), round(min(peaks)) if peaks else None))
    rep.data['arrival'] = {'d': round(d), 'column': ap, 'area_water_share': round(ak.get('water', 0) / len(area), 3),
                           'area_biomes': dict(ab)}

    # 3. beach in the core
    rep.out()
    rep.out('3. Beach in the core')
    cl = land(z_core)
    cw = [v for v in z_core if v['kind'] != 'land']
    beach = [v for v in cl if v['biome'].endswith('beach')]
    rep.out('   core samples %d: dry land %d, wet (lake/river) %d' % (len(z_core), len(cl), len(cw)))
    rep.out('   beach = %d of %d dry-land samples (%.1f %%), %.1f %% of ALL core samples; ancient_forest dry = %d (%.1f %%)'
            % (len(beach), len(cl), 100.0 * len(beach) / len(cl), 100.0 * len(beach) / len(z_core),
               sum(1 for v in cl if v['biome'] == CORE_BIOME),
               100.0 * sum(1 for v in cl if v['biome'] == CORE_BIOME) / len(cl)))
    rings = ((0, GREEN), (GREEN, 100), (100, 150), (150, 200))
    shares = {}
    for lo, hi in rings:
        vs = land([v for v in z_core if lo <= v['d'] < hi])
        b = sum(1 for v in vs if v['biome'].endswith('beach'))
        shares['%d-%d' % (lo, hi)] = round(b / len(vs), 3) if vs else None
        rep.out('     r %3d..%3d: beach %5.1f %% of %d dry samples' % (lo, hi, 100.0 * b / len(vs) if vs else 0, len(vs)))
    # what stands on the sand: the ground block of the beach cells
    rep.data['beach'] = {'core_dry_samples': len(cl), 'beach_samples': len(beach),
                         'share_of_dry': round(len(beach) / len(cl), 3), 'by_ring': shares}
    lattice = {k: v['biome'] for k, v in s.items() if v['d'] < band + 2 * args.step}
    wet = {k for k, v in s.items() if v['kind'] != 'land' and k in lattice}
    painted = {k: (CORE_BIOME if v.endswith('beach') and dist(*k) < core else v) for k, v in lattice.items()}
    both = (CORE_BIOME, BAND_BIOME)
    walks = {}
    for label, smp in (('as imported', lattice), ('if the core beach were repainted', painted)):
        walks[label] = {
            'ancient only, swimming allowed': min_deadly_walk(smp, args.step, outer=300),
            'ancient only, dry foot': min_deadly_walk(smp, args.step, outer=300, blocked=wet),
            'ancient + dark, from the rim, swimming allowed': min_deadly_walk(smp, args.step, outer=band, bad=both),
            'ancient + dark, from the rim, dry foot': min_deadly_walk(smp, args.step, outer=band, bad=both, blocked=wet)}
    rep.out('   fewest blocks of deadly biome to cross on the way to the green (r %d); a straight line from the band '
            'edge (r %d) crosses %d blocks, from r 300 %d:' % (GREEN, band, band - GREEN, 300 - GREEN))
    for label, ws in walks.items():
        rep.out('     %s' % label)
        for k, v in ws.items():
            rep.out('       %-48s %s' % (k, v))
    rep.data['beach']['walks'] = walks
    # how far does beach reach toward the green
    near = sorted((v['d'], v['x'], v['z']) for v in beach)[:1]
    rep.out('   nearest beach sample to Tempest: %s' % (near,))
    rep.data['beach']['nearest'] = near[0] if near else None

    # 4. Tempest footprints
    rep.out()
    rep.out('4. Tempest footprints at the anchor %s (terrain fit margin 8; exact columns at 2-block steps)' % (TEMPEST,))
    fp = {}
    for name, size, arr, margin in FOOTPRINTS:
        x0, z0 = TEMPEST[0] - arr[0] - margin, TEMPEST[1] - arr[1] - margin
        x1, z1 = x0 + size + 2 * margin - 1, z0 + size + 2 * margin - 1
        cols = sweep_box(world, x0, z0, x1, z1, 2)
        st = footprint_stats(cols, 2)
        fp[name] = {'box': [x0, z0, x1, z1], **st}
        rep.out('   %s: x %d..%d, z %d..%d (%d columns)' % (name, x0, x1, z0, z1, st['columns']))
        rep.out('     ground y min/p10/median/p90/max = %s/%s/%s/%s/%s, relief p90-p10 = %s'
                % (st['ground_min'], st['ground_p10'], st['ground_median'], st['ground_p90'], st['ground_max'],
                   st['relief_p90_p10']))
        rep.out('     slope (blocks per block between neighbours): mean %s, p95 %s, max %s; steeper than 0.5: %.1f %%'
                % (st['slope_mean'], st['slope_p95'], st['slope_max'], 100 * st['steep_share_gt_0_5']))
        rep.out('     within 2 / 4 blocks of the median: %.1f %% / %.1f %%; >8 above (cut): %d, >8 below (fill): %d'
                % (100 * st['within_2_of_median'], 100 * st['within_4_of_median'], st['cut_over_8'], st['fill_over_8']))
        rep.out('     water over ground: %.1f %% of columns (deepest %d), lava on the surface: %d'
                % (100 * st['water_share'], st['water_max_depth'], st['lava_surface_columns']))
        rep.out('     ground blocks %s' % st['ground_blocks'])
        rep.out('     stored biomes %s' % st['biomes'])
    rep.data['footprints'] = fp
    ep = fp['early village']
    rep.check('early Tempest box: no lava, water below 20 %, median slope buildable',
              ep['lava_surface_columns'] == 0 and ep['water_share'] < 0.2 and ep['slope_p95'] <= 1.0,
              'water %.1f %%, slope p95 %s, relief %s' % (100 * ep['water_share'], ep['slope_p95'], ep['relief_p90_p10']))

    rep.data['checks'] = rep.checks
    failed = [c for c in rep.checks if not c['ok']]
    rep.out()
    rep.out('%d checks, %d failed' % (len(rep.checks), len(failed)))
    if args.png:
        render(args.png, s, rules, args.radius, args.step)
        rep.out('map: %s' % args.png)
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(rep.data, f, indent=1, default=str)
    return 1 if failed else 0


PALETTE = {  # biome -> rgb
    'tensura:ancient_forest': (16, 70, 28), 'minecraft:dark_forest': (60, 100, 40), 'minecraft:beach': (236, 214, 130),
    'minecraft:plains': (150, 190, 90), 'minecraft:river': (60, 120, 220), 'minecraft:swamp': (90, 110, 80),
}


def render(path, s, rules, radius, step, scale=4):
    """Colour map of the sweep: ring biome colours, beach sand, water blue, rings as thin white circles."""
    n = 2 * radius // step + 1
    img = [[(10, 18, 50)] * n for _ in range(n)]
    for (x, z), v in s.items():
        col = (TEMPEST[0] - radius, TEMPEST[1] - radius)
        i, j = (x - col[0]) // step, (z - col[1]) // step
        if 0 <= i < n and 0 <= j < n:
            if v['kind'] == 'water':
                c = (40, 100, 200)
            else:
                c = PALETTE.get(v['biome'], (140, 140, 140))
            img[j][i] = c
    pal = sorted({c for row in img for c in row} | {(255, 255, 255), (230, 40, 40)})
    idx = {c: k for k, c in enumerate(pal)}
    c0 = radius // step * scale + scale // 2
    rows = []
    for j in range(n * scale):
        row = []
        for i in range(n * scale):
            c = img[j // scale][i // scale]
            x = (i / scale) * step - radius
            z = (j / scale) * step - radius
            r = math.hypot(x, z)
            if abs(r - rules.jura['core']) < step / scale or abs(r - rules.jura['band']) < step / scale:
                c = (255, 255, 255)
            if abs(i - c0) <= 3 and abs(j - c0) <= 3:
                c = (230, 40, 40)
            row.append(idx[c])
        rows.append(row)
    write_png(path, n * scale, n * scale, rows, palette=pal)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--world', required=True, help='imported world folder (holds region/); read only')
    ap.add_argument('--step', type=int, default=8, help='sample spacing in blocks, a multiple of 4 (default 8)')
    ap.add_argument('--radius', type=int, default=800, help='sweep radius round Tempest in blocks (default 800)')
    ap.add_argument('--rules', default=str(RULES))
    ap.add_argument('--json', help='write the figures as JSON')
    ap.add_argument('--png', help='write a colour map of the rings (white circles: core, band; red: Tempest)')
    args = ap.parse_args(argv)
    if args.step % 4:
        ap.error('--step must be a multiple of 4 (samples sit on 4x4 biome-cell centres)')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
