"""Shared pieces of the Lerfing import tools: map constants, packed arrays, block classes, columns, repaint rules,
value noise and a tiny PNG codec. Stdlib only (the tools run with `python -I`)."""
import fnmatch
import json
import math
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'design' / 'data' / 'lerfing'
RULES = DATA / 'repaint.json'

# Inner tiles of Lerfing's WorldPainter export (design/architecture/lerfing-import.md §0, §1.1).
REGIONS_X = (-16, 15)            # inclusive
REGIONS_Z = (-12, 12)
# Lerfing's drawn map inside those files, in chunks (x -8064..8192, z -6016..6528 in blocks).
# The 8-chunk strip around it inside the same files is WorldPainter's flat border (status "full"): dropped.
CHUNKS_X = (-504, 511)           # inclusive
CHUNKS_Z = (-376, 407)
GRID_W = CHUNKS_X[1] - CHUNKS_X[0] + 1   # 1016
GRID_H = CHUNKS_Z[1] - CHUNKS_Z[0] + 1   # 784

OLD_STATUS = ('liquid_carvers', 'minecraft:liquid_carvers')
NEW_STATUS = 'minecraft:carvers'

# Landmask classes (palette indices of landmask16.png).
SEA, LAKE, LAND, MISSING = 0, 1, 2, 3


def region_name(rx, rz):
    return 'r.%d.%d.mca' % (rx, rz)


def region_coords(name):
    m = re.search(r'r\.(-?\d+)\.(-?\d+)\.mca$', name)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def inner_region(rx, rz):
    return REGIONS_X[0] <= rx <= REGIONS_X[1] and REGIONS_Z[0] <= rz <= REGIONS_Z[1]


def inner_chunk(cx, cz):
    return CHUNKS_X[0] <= cx <= CHUNKS_X[1] and CHUNKS_Z[0] <= cz <= CHUNKS_Z[1]


# ---------------------------------------------------------------- packed arrays (1.16+ rule: no value spans two longs)

def ceil_log2(n):
    return (n - 1).bit_length() if n > 1 else 0


def packed_longs(n_values, bits):
    if bits == 0:
        return 0
    per = 64 // bits
    return -(-n_values // per)


def unpack(raw, n_values, bits):
    """List of n_values ints from a big-endian long array `raw` packed at `bits` per value."""
    if bits == 0:
        return [0] * n_values
    per = 64 // bits
    need = -(-n_values // per)
    if len(raw) < need * 8:
        raise ValueError('packed array too short: %d longs < %d (bits %d)' % (len(raw) // 8, need, bits))
    longs = struct.unpack('>%dQ' % need, bytes(raw[:need * 8]))
    mask = (1 << bits) - 1
    out = []
    for word in longs:
        for k in range(per):
            out.append((word >> (k * bits)) & mask)
    return out[:n_values]


def pack(values, bits):
    """Big-endian long array bytes for `values` at `bits` per value."""
    if bits == 0:
        return b''
    per = 64 // bits
    words = []
    for i in range(0, len(values), per):
        w = 0
        for k, v in enumerate(values[i:i + per]):
            w |= (v & ((1 << bits) - 1)) << (k * bits)
        words.append(w)
    return struct.pack('>%dQ' % len(words), *words)


def value_at(raw, index, bits):
    """One value of a packed long array, without unpacking the rest."""
    if bits == 0:
        return 0
    per = 64 // bits
    word = struct.unpack_from('>Q', raw, (index // per) * 8)[0]
    return (word >> ((index % per) * bits)) & ((1 << bits) - 1)


def block_bits(n_palette):
    return 0 if n_palette <= 1 else max(4, ceil_log2(n_palette))


def biome_bits(n_palette):
    return ceil_log2(n_palette)


# ---------------------------------------------------------------- block classes

AIR, LEAF, WATER, LAVA, ICE, GROUND = 1, 2, 4, 8, 16, 32

PLANT_RE = re.compile(
    r'(^|_)(grass|fern|flower|tulip|orchid|allium|bluet|daisy|poppy|dandelion|cornflower|lily|rose_bush|peony|lilac|'
    r'sunflower|dead_bush|sugar_cane|vines?|sapling|bush|bamboo|kelp|seagrass|coral|coral_fan|azalea|moss_carpet|'
    r'pointed_dripstone|glow_lichen|cactus|cocoa|hanging_roots|spore_blossom|dripleaf|torch|log|wood|stem|hyphae|'
    r'fence|mangrove_roots|cobweb|propagule|pickle|pitcher|torchflower|frogspawn|weeping|twisting|roots|'
    r'nether_sprouts|fungus|mushroom|berry_bush|lichen|plant|carpet|snow)(_|$)')
NOT_PLANT = {'grass_block', 'moss_block', 'dirt_path', 'mycelium', 'podzol', 'mushroom_stem', 'red_mushroom_block',
             'brown_mushroom_block', 'snow_block'}
_CLASS = {}


def classify(entry):
    """Bit flags of a block_states palette entry ({Name, Properties})."""
    name = entry.get('Name', 'minecraft:air')
    props = entry.get('Properties') or {}
    wet = props.get('waterlogged') == 'true'
    key = (name, wet)
    f = _CLASS.get(key)
    if f is not None:
        return f
    short = name.split(':', 1)[-1]
    if short in ('air', 'cave_air', 'void_air'):
        f = AIR
    else:
        f = 0
        if short.endswith('leaves'):
            f |= LEAF
        if short in ('water', 'bubble_column', 'seagrass', 'tall_seagrass', 'kelp', 'kelp_plant') or wet:
            f |= WATER
        if short in ('ice', 'frosted_ice', 'packed_ice', 'blue_ice'):
            f |= ICE
        if short == 'lava':
            f |= LAVA
        plant = bool(PLANT_RE.search(short)) and short not in NOT_PLANT
        if not (f & (LEAF | LAVA | ICE | WATER)) and not plant and short not in ('fire', 'soul_fire', 'light') \
                and not short.startswith('potted_'):
            f |= GROUND
    _CLASS[key] = f
    return f


class Columns:
    """Top-down column reads of one chunk (block_states parsed lazily, once per section)."""

    def __init__(self, scan, read_states):
        self.secs = sorted((s for s in scan.sections if s.y is not None), key=lambda s: -s.y)
        self.read_states = read_states
        self.scan = scan
        self._states = {}

    def _section(self, sec):
        st = self._states.get(sec.y)
        if st is None:
            got = self.read_states(self.scan, sec)
            if not got:
                st = ([], [], b'', 0)
            else:
                pal, data = got
                st = (pal, [classify(p) for p in pal], data, block_bits(len(pal)))
            self._states[sec.y] = st
        return st

    def column(self, x, z):
        """(surface_y, surface_name, ground_y, ground_name, water_y): top non-air block, top ground block,
        top water/ice block above the ground (None when dry or not found)."""
        surface = ground = water = None
        sname = gname = None
        for sec in self.secs:
            pal, flags, data, bits = self._section(sec)
            if not pal:
                continue
            if len(pal) == 1 and flags[0] == AIR:
                continue
            base = sec.y * 16
            for y in range(15, -1, -1):
                i = value_at(data, (y * 16 + z) * 16 + x, bits) if bits else 0
                if i >= len(pal):
                    raise ValueError('block index %d >= palette %d' % (i, len(pal)))
                f = flags[i]
                if f & AIR:
                    continue
                if surface is None:
                    surface, sname = base + y, pal[i].get('Name')
                if water is None and f & (WATER | ICE):
                    water = base + y
                if f & GROUND:
                    ground, gname = base + y, pal[i].get('Name')
                    if water is not None and water <= ground:
                        water = None
                    return surface, sname, ground, gname, water
        return surface, sname, ground, gname, water


# ---------------------------------------------------------------- value noise (the Jura ring wobble)

def _hash01(ix, iz, seed):
    h = (ix * 0x27D4EB2D) ^ (iz * 0x165667B1) ^ (seed * 0x9E3779B1)
    h &= 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & 0xFFFFFFFF
    h ^= h >> 12
    h = (h * 0x297A2D39) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 4294967296.0


def value_noise(x, z, cell, seed):
    """Smooth value noise in [-1, 1) on a lattice of `cell` blocks."""
    fx, fz = x / cell, z / cell
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a = _hash01(ix, iz, seed)
    b = _hash01(ix + 1, iz, seed)
    c = _hash01(ix, iz + 1, seed)
    d = _hash01(ix + 1, iz + 1, seed)
    top = a + (b - a) * tx
    bot = c + (d - c) * tx
    return (top + (bot - top) * tz) * 2 - 1


# ---------------------------------------------------------------- repaint rules (design/data/lerfing/repaint.json)

def _in_range(v, rng):
    if rng is None:
        return True
    lo, hi = rng
    return (lo is None or v >= lo) and (hi is None or v < hi)


class Rules:
    def __init__(self, data):
        self.data = data
        self.base = data.get('rules', [])
        self.keep = data.get('keep', [])
        self.forbidden = set(data.get('forbidden', []))
        self.spots = data.get('spots', [])
        self.jura = data.get('jura')
        self.sources = {r['from'] for r in self.base}
        self._keep_cache = {}
        self.hash = '%08x' % (zlib.crc32(json.dumps(data, sort_keys=True).encode()) & 0xFFFFFFFF)

    @classmethod
    def load(cls, path=RULES):
        with open(path, encoding='utf-8') as f:
            return cls(json.load(f))

    def kept(self, biome):
        """True when the area rules (spots, Jura rings) never repaint this stored biome (water, caves)."""
        k = self._keep_cache.get(biome)
        if k is None:
            k = any(fnmatch.fnmatchcase(biome, p) for p in self.keep)
            self._keep_cache[biome] = k
        return k

    def base_biome(self, biome, x, z):
        for r in self.base:
            if r['from'] == biome and _in_range(x, r.get('x')) and _in_range(z, r.get('z')):
                return r['to']
        return biome

    def _jura_reach(self):
        j = self.jura
        return j['band'] + j.get('wobble', 0)

    def area_may_apply(self, x0, z0, x1, z1):
        """Could a spot or the Jura rings touch the block box [x0, x1) x [z0, z1)?"""
        def near(cx, cz, r):
            dx = max(x0 - cx, 0, cx - (x1 - 1))
            dz = max(z0 - cz, 0, cz - (z1 - 1))
            return dx * dx + dz * dz <= r * r
        for s in self.spots:
            if near(s['centre'][0], s['centre'][1], s['radius']):
                return True
        j = self.jura
        if j:
            clip = j.get('clip') or {}
            cx_rng, cz_rng = clip.get('x'), clip.get('z')
            if cx_rng and (cx_rng[1] is not None and x0 >= cx_rng[1] or cx_rng[0] is not None and x1 <= cx_rng[0]):
                return False
            if cz_rng and (cz_rng[1] is not None and z0 >= cz_rng[1] or cz_rng[0] is not None and z1 <= cz_rng[0]):
                return False
            return near(j['centre'][0], j['centre'][1], self._jura_reach())
        return False

    def area_biome(self, x, z):
        """Biome the spots/rings assign to a land cell centred at (x, z), or None."""
        for s in self.spots:
            dx, dz = x - s['centre'][0], z - s['centre'][1]
            if dx * dx + dz * dz < s['radius'] * s['radius']:
                return s['biome']
        j = self.jura
        if not j:
            return None
        clip = j.get('clip') or {}
        if not (_in_range(x, clip.get('x')) and _in_range(z, clip.get('z'))):
            return None
        d = math.hypot(x - j['centre'][0], z - j['centre'][1])
        if d >= self._jura_reach():
            return None
        w = j.get('wobble', 0)
        if w:
            d += w * value_noise(x, z, j.get('wobble_cell', 64), j.get('seed', 0))
        if d < j['core']:
            return j['core_biome']
        if d < j['band']:
            return j['band_biome']
        return None

    def ring_of(self, x, z):
        """'core', 'band' or None for a block position (no water test): for probes and reports."""
        b = self.area_biome(x, z)
        if b is None or not self.jura:
            return None
        return 'core' if b == self.jura['core_biome'] else 'band' if b == self.jura['band_biome'] else 'spot'


# ---------------------------------------------------------------- PNG (8-bit palette / 8-bit gray / 16-bit gray)

def _chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF)


def write_png(path, width, height, rows, depth=8, palette=None):
    """rows: list of `height` sequences of `width` ints. palette: list of (r, g, b) → colour type 3 (8-bit)."""
    ctype = 3 if palette else 0
    raw = bytearray()
    for row in rows:
        raw.append(0)
        if depth == 16:
            raw += struct.pack('>%dH' % width, *row)
        else:
            raw += bytes(row)
    out = b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, ctype, 0, 0, 0))
    if palette:
        out += _chunk(b'PLTE', b''.join(bytes(c) for c in palette))
    out += _chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + _chunk(b'IEND', b'')
    Path(path).write_bytes(out)


def read_png(path):
    """(width, height, rows) with rows of raw sample values (palette indices, gray levels)."""
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    pos, idat = 8, b''
    w = h = depth = ctype = None
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
            if interlace or ctype not in (0, 3) or depth not in (8, 16):
                raise ValueError('unsupported PNG (type %d, depth %d)' % (ctype, depth))
        elif kind == b'IDAT':
            idat += body
        elif kind == b'IEND':
            break
    bpp = depth // 8
    stride = w * bpp
    raw = zlib.decompress(idat)
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                if f == 1:
                    line[x] = (line[x] + a) & 255
                elif f == 2:
                    line[x] = (line[x] + b) & 255
                elif f == 3:
                    line[x] = (line[x] + (a + b) // 2) & 255
                elif f == 4:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(list(struct.unpack('>%dH' % w, bytes(line))) if depth == 16 else list(line))
        prev = line
    return w, h, rows


# ---------------------------------------------------------------- stored biomes of a scanned chunk

def section_biomes(sec):
    """(palette list, cell index list of 64) of a scanned section's biomes, or None."""
    if not sec.biomes:
        return None
    pal = data = None
    for _t, name, _raw, value in sec.biomes:
        if name == 'palette':
            pal = value
        elif name == 'data':
            data = value
    if not pal:
        return None
    bits = biome_bits(len(pal))
    return pal, unpack(data or b'', 64, bits)


def biome_index(lx, ly, lz):
    """Cell index inside a section's 4x4x4 biome array for block offsets inside the section."""
    return ((ly >> 2) * 4 + (lz >> 2)) * 4 + (lx >> 2)
