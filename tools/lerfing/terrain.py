"""Terrain grids of Lerfing's map for the offline planners (forests.py, trade_roads.py; stdlib only).

Two sources, the same interface:

  * Terrain.from_rasters(...)  the committed 1:16 rasters (design/data/lerfing: heights16, landmask16, biomes16). Works
                               anywhere (CI); one sample per chunk.
  * Terrain.from_world(...)    exact columns of the imported world (read only, tools/lerfing/import.py output) at any
                               step; cached as gzip JSON in TTL_TERRAIN_CACHE (default ~/.cache/ocs-two-lives/terrain)
                               so a re-plan does not parse the region files again.

Per sample: ground (y of the top ground block; under water the bed), water (water or ice above the ground: its top y,
else None), cls ('soil' grass/dirt/podzol/moss, 'sand', 'rock' stone/terracotta/gravel/clay/..., 'other'), tree (the
top block is leaves or a log: a tree stands over the column), biome id.
"""
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing.common import CHUNKS_X, CHUNKS_Z, DATA, LAKE, LAND, SEA, read_png  # noqa: E402

SOIL = {'grass_block', 'dirt', 'podzol', 'coarse_dirt', 'moss_block', 'rooted_dirt', 'mycelium', 'mud', 'dirt_path'}
SAND = {'sand', 'red_sand', 'suspicious_sand'}


def ground_class(block):
    short = (block or '').split(':', 1)[-1]
    if short in SOIL:
        return 'soil'
    if short in SAND:
        return 'sand'
    if not short:
        return 'other'
    return 'rock'


def is_tree(block):
    short = (block or '').split(':', 1)[-1]
    return short.endswith('leaves') or short.endswith('_log') or short.endswith('_wood') or short in (
        'mushroom_stem', 'red_mushroom_block', 'brown_mushroom_block')


class Terrain:
    def __init__(self, x0, z0, step, w, h, source):
        self.x0, self.z0, self.step, self.w, self.h, self.source = x0, z0, step, w, h, source
        n = w * h
        self.ground = [None] * n
        self.water = [None] * n
        self.cls = ['other'] * n
        self.tree = [False] * n
        self.biome = [None] * n

    # ------------------------------------------------------------ access
    def index(self, x, z):
        i = (x - self.x0) // self.step
        j = (z - self.z0) // self.step
        if 0 <= i < self.w and 0 <= j < self.h:
            return j * self.w + i
        return None

    def at(self, x, z):
        """{ground, water, cls, tree, biome} of the sample holding (x, z), or None outside the grid."""
        k = self.index(x, z)
        if k is None:
            return None
        return {'ground': self.ground[k], 'water': self.water[k], 'cls': self.cls[k], 'tree': self.tree[k],
                'biome': self.biome[k]}

    def wet(self, x, z):
        k = self.index(x, z)
        return k is None or self.water[k] is not None or self.ground[k] is None

    def coords(self):
        for j in range(self.h):
            for i in range(self.w):
                yield self.x0 + i * self.step, self.z0 + j * self.step, j * self.w + i

    # ------------------------------------------------------------ sources
    @classmethod
    def from_rasters(cls, x0, z0, x1, z1, rdir=str(DATA)):
        _, _, mask = read_png(os.path.join(rdir, 'landmask16.png'))
        _, _, hgt = read_png(os.path.join(rdir, 'heights16.png'))
        _, _, bio = read_png(os.path.join(rdir, 'biomes16.png'))
        with open(os.path.join(rdir, 'legend.json'), encoding='utf-8') as f:
            legend = json.load(f)
        names = {b['index']: b['id'] for b in legend['biomes16.png']['biomes']}
        x0 &= ~15
        z0 &= ~15
        w = (x1 - x0) // 16 + 1
        h = (z1 - z0) // 16 + 1
        t = cls(x0, z0, 16, w, h, 'rasters 1:16')
        for x, z, k in t.coords():
            col, row = (x >> 4) - CHUNKS_X[0], (z >> 4) - CHUNKS_Z[0]
            if not (0 <= row < len(mask) and 0 <= col < len(mask[0])):
                continue
            hv = hgt[row][col]
            if not hv:
                continue
            t.ground[k] = hv - 64
            c = mask[row][col]
            if c in (SEA, LAKE):
                t.water[k] = 64  # Lerfing's water surface (top water block y 64)
            t.biome[k] = names.get(bio[row][col])
            b = t.biome[k] or ''
            t.cls[k] = 'sand' if b.endswith('beach') or b.endswith('desert') else 'soil' if c == LAND else 'other'
        return t

    @classmethod
    def from_world(cls, world, x0, z0, x1, z1, step, cache=None):
        """Exact columns every `step` blocks over x0..x1, z0..z1 (inclusive) of an imported world folder."""
        key = hashlib.sha1(json.dumps([os.path.abspath(world), x0, z0, x1, z1, step, 2]).encode()).hexdigest()[:16]
        cdir = Path(cache or os.environ.get('TTL_TERRAIN_CACHE') or Path.home() / '.cache' / 'ocs-two-lives' / 'terrain')
        cfile = cdir / f'terrain-{key}.json.gz'
        w = (x1 - x0) // step + 1
        h = (z1 - z0) // step + 1
        t = cls(x0, z0, step, w, h, f'world {Path(world).name}, step {step}')
        if cfile.is_file():
            with gzip.open(cfile, 'rt', encoding='utf-8') as f:
                d = json.load(f)
            t.ground, t.water, t.cls, t.tree, t.biome = d['ground'], d['water'], d['cls'], d['tree'], d['biome']
            return t
        from lerfing.probe import World  # noqa: E402 (needs the region reader only here)
        wd = World(world)
        for x, z, k in t.coords():
            p = wd.at(x, z)
            if p is None or p.get('ground_y') is None:
                continue
            t.ground[k] = p['ground_y']
            t.water[k] = p['water_y']
            t.cls[k] = ground_class(p['ground_block'])
            t.tree[k] = is_tree(p['top_block'])
            t.biome[k] = p['biome']
            if len(wd.chunks) > 4000:
                wd.chunks.clear()
                wd.regions.clear()
        try:
            cdir.mkdir(parents=True, exist_ok=True)
            with gzip.open(cfile, 'wt', encoding='utf-8') as f:
                json.dump({'ground': t.ground, 'water': t.water, 'cls': t.cls, 'tree': t.tree, 'biome': t.biome}, f)
        except OSError:
            pass
        return t
