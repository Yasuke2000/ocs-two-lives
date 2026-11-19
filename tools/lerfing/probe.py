"""Probe Lerfing's map at a block position (design/architecture/lerfing-import.md §2.3, §3).

    python -I tools/lerfing/probe.py X Z [HALF]                      from the committed 1:16 rasters
    python -I tools/lerfing/probe.py X Z [HALF] --world <out dir>    from the imported world (exact columns)
    python -I tools/lerfing/probe.py X Z [HALF] --zip "<zip>"        from the source zip (stored biomes before the repaint)

Prints the surface y, the top block, the ground y and block, water over the ground, the biome and land/sea at (X, Z);
with HALF, also the window X±HALF, Z±HALF: land/water share, ground y percentiles, relief (p90 - p10), biomes.
The raster mode needs no world at all; `--world`/`--zip` read single chunks (every 4 blocks in the window).
"""
import argparse
import collections
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing import nbt  # noqa: E402
from lerfing.common import (  # noqa: E402
    CHUNKS_X, CHUNKS_Z, DATA, LAKE, LAND, MISSING, RULES, SEA, Columns, Rules, biome_index, inner_region,
    read_png, region_coords, section_biomes)

CLASS = {SEA: 'sea', LAKE: 'lake/river', LAND: 'land', MISSING: 'missing'}


class Rasters:
    def __init__(self, rdir):
        with open(os.path.join(rdir, 'legend.json'), encoding='utf-8') as f:
            self.legend = json.load(f)
        _, _, self.cls = read_png(os.path.join(rdir, 'landmask16.png'))
        _, _, self.hgt = read_png(os.path.join(rdir, 'heights16.png'))
        _, _, self.bio = read_png(os.path.join(rdir, 'biomes16.png'))
        self.names = {b['index']: b['id'] for b in self.legend['biomes16.png']['biomes']}

    def at(self, x, z):
        col, row = (x >> 4) - CHUNKS_X[0], (z >> 4) - CHUNKS_Z[0]
        if not (0 <= row < len(self.cls) and 0 <= col < len(self.cls[0])):
            return None
        h = self.hgt[row][col]
        return {'class': CLASS[self.cls[row][col]], 'ground_y': h - 64 if h else None,
                'biome': self.names.get(self.bio[row][col])}


class World:
    """Chunk reads from an imported world folder or from the zip."""

    def __init__(self, world=None, zip_path=None):
        self.world, self.zip, self.members = world, None, {}
        if zip_path:
            self.zip = zipfile.ZipFile(zip_path)
            for info in self.zip.infolist():
                parts = info.filename.replace('\\', '/').split('/')
                rc = region_coords(parts[-1]) if len(parts) >= 2 and parts[-2] == 'region' else None
                if rc:
                    self.members[rc] = info.filename
        self.regions = {}
        self.chunks = {}

    def _region(self, rx, rz):
        if (rx, rz) not in self.regions:
            data = None
            if self.zip is not None:
                if (rx, rz) in self.members:
                    data = self.zip.read(self.members[(rx, rz)])
            else:
                p = os.path.join(self.world, 'region', 'r.%d.%d.mca' % (rx, rz))
                if os.path.exists(p):
                    with open(p, 'rb') as f:
                        data = f.read()
            self.regions[(rx, rz)] = nbt.read_region(data) if data else {}
        return self.regions[(rx, rz)]

    def chunk(self, cx, cz):
        if (cx, cz) not in self.chunks:
            reg = self._region(cx >> 5, cz >> 5)
            got = reg.get((cx & 31, cz & 31))
            if got is None:
                self.chunks[(cx, cz)] = None
            else:
                scan = nbt.scan_chunk(nbt.decompress(got[0], got[1]))
                self.chunks[(cx, cz)] = (scan, Columns(scan, nbt.block_states))
        return self.chunks[(cx, cz)]

    def at(self, x, z):
        got = self.chunk(x >> 4, z >> 4)
        if got is None:
            return None
        scan, cols = got
        lx, lz = x & 15, z & 15
        surface, sname, ground, gname, water = cols.column(lx, lz)
        biome = None
        if surface is not None:
            secs = {s.y: s for s in scan.sections}
            sy = surface >> 4
            sec = secs.get(sy)
            ly = surface & 15
            if sec is None or section_biomes(sec) is None:
                cand = [s for s in scan.sections if section_biomes(s)]
                if cand:
                    sec = min(cand, key=lambda s: abs(s.y - sy))
                    ly = 15 if sec.y < sy else 0
            got_b = section_biomes(sec) if sec is not None else None
            if got_b:
                pal, idx = got_b
                biome = pal[idx[biome_index(lx, ly, lz)]]
        return {'status': scan.status, 'surface_y': surface, 'top_block': sname, 'ground_y': ground,
                'ground_block': gname, 'water_y': water, 'water_depth': None if water is None else water - ground,
                'class': 'water' if water is not None else 'land' if ground is not None else 'void', 'biome': biome}


def window(sampler, x, z, half, step):
    land = water = n = 0
    ys, biomes = [], collections.Counter()
    for zz in range(z - half, z + half + 1, step):
        for xx in range(x - half, x + half + 1, step):
            p = sampler(xx, zz)
            if not p:
                continue
            n += 1
            if p['class'] == 'land':
                land += 1
            elif p['class'] in ('sea', 'lake/river', 'water'):
                water += 1
            if p.get('ground_y') is not None:
                ys.append(p['ground_y'])
            if p.get('biome'):
                biomes[p['biome']] += 1
    ys.sort()

    def pct(q):
        return ys[min(len(ys) - 1, int(q * len(ys)))] if ys else None
    return {'half': half, 'step': step, 'samples': n, 'land_share': round(land / n, 3) if n else None,
            'water_share': round(water / n, 3) if n else None, 'ground_min': ys[0] if ys else None,
            'ground_p10': pct(0.1), 'ground_median': pct(0.5), 'ground_p90': pct(0.9),
            'ground_max': ys[-1] if ys else None, 'relief_p90_p10': (pct(0.9) - pct(0.1)) if ys else None,
            'biomes': dict(biomes.most_common(8))}


def probe(x, z, half=None, world=None, zip_path=None, rasters=str(DATA), rules=str(RULES)):
    out = {'x': x, 'z': z, 'inner_tiles': inner_region(x >> 9, z >> 9)
           and CHUNKS_X[0] <= x >> 4 <= CHUNKS_X[1] and CHUNKS_Z[0] <= z >> 4 <= CHUNKS_Z[1]}
    try:
        rs = Rules.load(rules)
        out['jura_ring'] = rs.ring_of(x, z)
    except OSError:
        rs = None
    r = Rasters(rasters) if rasters and os.path.exists(os.path.join(rasters, 'legend.json')) else None
    if world or zip_path:
        w = World(world, zip_path)
        out['source'] = 'zip (before the import)' if zip_path else 'world ' + world
        out['column'] = w.at(x, z)
        if r:
            out['landmask16'] = r.at(x, z)
        if half:
            out['window'] = window(w.at, x, z, half, 4)
    elif r:
        out['source'] = 'rasters 1:16 (%s)' % rasters
        out['column'] = r.at(x, z)
        if half:
            out['window'] = window(r.at, x, z, half, 16)
    else:
        raise SystemExit('no rasters in %s and no --world/--zip' % rasters)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('x', type=int)
    ap.add_argument('z', type=int)
    ap.add_argument('half', type=int, nargs='?')
    ap.add_argument('--world', help='imported world folder (holds region/)')
    ap.add_argument('--zip', help="Lerfing's zip (read only)")
    ap.add_argument('--rasters', default=str(DATA))
    ap.add_argument('--rules', default=str(RULES))
    args = ap.parse_args(argv)
    print(json.dumps(probe(args.x, args.z, args.half, args.world, args.zip, args.rasters, args.rules), indent=1))


if __name__ == '__main__':
    main()
