"""Lerfing's Tensura map → the Life 2 overworld region files (design/architecture/lerfing-import.md §1, WP-L1).

    python -I tools/lerfing/import.py "<Tensura By Lerfing.zip>" --out <world folder outside the repo>
    python -I tools/lerfing/import.py "<zip>" --out <dir> --regions r.3.1,r.-2.0     (a sample)
    python -I tools/lerfing/import.py ["<zip>"] --out <dir> --verify                 (re-read every written chunk)

Streams the inner-tile region files (r.-16..15 x r.-12..12) out of the zip (never extracted, never level.dat or
entities/) and writes `<out>/region/`. Per chunk:
  * status `liquid_carvers` → `minecraft:carvers` (1.21.1 has no liquid_carvers; an unknown status loads as EMPTY
    and the chunk would be regenerated over Lerfing's terrain);
  * biome repaint from design/data/lerfing/repaint.json (Nether/End biomes, Jura rings around Tempest, spots);
    biome palettes are re-packed (1.18 rule: ceil(log2(n)) bits, no data for one entry, no value spans two longs);
  * every other byte of the chunk NBT is copied unchanged (the two kinds of tags are spliced in place);
  * the WorldPainter border chunks inside the same files (outside x -8064..8192, z -6016..6528) are dropped.
Also writes `<out>/report.json`, `<out>/sha256.txt` (sha256sum format, for the upload check) and the 1:16 rasters
(`<out>/rasters/`, or `--rasters design/data/lerfing` to refresh the committed ones). Idempotent: a region whose
source, rules and tool version are unchanged and whose output is intact is skipped.
"""
import argparse
import collections
import hashlib
import json
import os
import statistics
import sys
import time
import zipfile
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing import nbt  # noqa: E402
from lerfing.common import (  # noqa: E402
    CHUNKS_X, CHUNKS_Z, GRID_H, GRID_W, LAKE, LAND, MISSING, NEW_STATUS, OLD_STATUS, ROOT, RULES, SEA, Columns,
    Rules, biome_bits, biome_index, inner_chunk, inner_region, pack, region_coords, region_name, section_biomes,
    unpack, write_png)

TOOL_VERSION = 1
MAX_MEMBER = 256 << 20          # a region file is at most 1024 x 255 sectors; refuse anything absurd in the zip
CELL_CENTRES = [(x * 4 + 2, z * 4 + 2) for z in range(4) for x in range(4)]


# ---------------------------------------------------------------- one chunk

def _encode_biomes(entries, palette, indices):
    bits = biome_bits(len(palette))
    out = []
    wrote_data = False
    for t, name, raw, _value in entries:
        if name == 'palette':
            out.append(nbt.enc_entry(9, 'palette', nbt.enc_string_list(palette)))
            if bits and not any(e[1] == 'data' for e in entries):
                out.append(nbt.enc_entry(12, 'data', nbt.enc_long_array(pack(indices, bits))))
                wrote_data = True
        elif name == 'data':
            if bits and not wrote_data:
                out.append(nbt.enc_entry(12, 'data', nbt.enc_long_array(pack(indices, bits))))
        else:
            out.append(raw)
    return b''.join(out) + b'\x00'


def repaint_chunk(scan, rules, cx, cz, stats):
    """Edits (status + biomes) for one scanned chunk and its raster sample [class, height, biome]."""
    edits = []
    if scan.status in OLD_STATUS:
        edits.append((scan.status_span[0], scan.status_span[1], nbt.enc_string(NEW_STATUS)))
    x0, z0 = cx * 16, cz * 16
    area = rules.area_may_apply(x0, z0, x0 + 16, z0 + 16)
    cols = Columns(scan, nbt.block_states)
    col_cache = {}

    def column(bx, bz):
        c = col_cache.get((bx, bz))
        if c is None:
            c = col_cache[(bx, bz)] = cols.column(bx, bz)
        return c

    area_cache = {}

    def area_target(qx, qz):
        k = (qx, qz)
        if k not in area_cache:
            t = rules.area_biome(x0 + qx * 4 + 2, z0 + qz * 4 + 2)
            if t is not None:
                c = column(qx * 4 + 2, qz * 4 + 2)
                if c[4] is not None:      # water (or ice) over the ground: lakes, rivers, the sea
                    t = None
            area_cache[k] = t
        return area_cache[k]

    after = {}       # section Y -> (palette, indices) as stored after the import
    before = {}
    trans = stats['transitions']
    counts = stats['biomes_after']
    for sec in scan.sections:
        got = section_biomes(sec)
        if got is None:
            continue
        pal, idx = got
        before[sec.y] = (pal, idx)
        if not area and not any(p in rules.sources for p in pal):
            after[sec.y] = (pal, idx)
            if len(pal) == 1:
                counts[pal[0]] += 64
            else:
                for i in idx:
                    counts[pal[i]] += 1
            continue
        names = []
        changed = False
        for i, pi in enumerate(idx):
            old = pal[pi]
            qx, qz = i & 3, (i >> 2) & 3
            new = rules.base_biome(old, x0 + qx * 4 + 2, z0 + qz * 4 + 2)
            if area and not rules.kept(old) and not rules.kept(new):
                t = area_target(qx, qz)
                if t is not None:
                    new = t
            if new != old:
                changed = True
                trans[old + ' > ' + new] += 1
            names.append(new)
        new_pal = list(dict.fromkeys(names))
        lookup = {n: k for k, n in enumerate(new_pal)}
        new_idx = [lookup[n] for n in names]
        for n in names:
            counts[n] += 1
        after[sec.y] = (new_pal, new_idx)
        if changed:
            edits.append((sec.biomes_span[0], sec.biomes_span[1], _encode_biomes(sec.biomes, new_pal, new_idx)))
            stats['sections_repainted'] += 1

    # raster sample: 16 cell-centre columns
    dry, grounds, biomes = 0, [], collections.Counter()
    for bx, bz in CELL_CENTRES:
        surface, _sname, ground, _gname, water = column(bx, bz)
        if ground is not None:
            grounds.append(ground)
            if water is None:
                dry += 1
        if surface is not None:
            sy = surface >> 4
            got_b, got_a = before.get(sy), after.get(sy)
            if got_a is None:
                near = min(after, key=lambda y: abs(y - sy)) if after else None
                got_a, got_b = after.get(near), before.get(near)
                ly = 15 if near is not None and near < sy else 0
            else:
                ly = surface & 15
            if got_a:
                ci = biome_index(bx, ly, bz)
                b_new = got_a[0][got_a[1][ci]]
                b_old = got_b[0][got_b[1][ci]]
                biomes[b_new] += 1
                if b_new != b_old:
                    stats['surface_transitions'][b_old + ' > ' + b_new] += 1
    cls = LAND if dry >= 8 else SEA if grounds else MISSING
    height = int(statistics.median_low(grounds)) if grounds else None
    biome = biomes.most_common(1)[0][0] if biomes else None
    return edits, [cls, height, biome]


def new_stats():
    return {'status_before': collections.Counter(), 'status_after': collections.Counter(),
            'dropped_border': collections.Counter(), 'transitions': collections.Counter(),
            'surface_transitions': collections.Counter(), 'biomes_after': collections.Counter(),
            'block_entities': collections.Counter(), 'kept_block_entities': [], 'sections_repainted': 0,
            'chunks_written': 0, 'chunks_rewritten': 0}


def process_region(src, rx, rz, rules, keep_border=False):
    """(region bytes or None, stats, samples) for one source region file held in memory."""
    stats = new_stats()
    samples = {}
    out = {}
    for (lx, lz), (comp, payload, ts) in sorted(nbt.read_region(src).items()):
        cx, cz = rx * 32 + lx, rz * 32 + lz
        raw = nbt.decompress(comp, payload)
        scan = nbt.scan_chunk(raw)
        if (scan.x, scan.z) != (cx, cz):
            raise ValueError('%s slot %d,%d holds chunk %s,%s' % (region_name(rx, rz), lx, lz, scan.x, scan.z))
        stats['status_before'][scan.status] += 1
        if not keep_border and not inner_chunk(cx, cz):
            stats['dropped_border'][scan.status] += 1
            continue
        edits, sample = repaint_chunk(scan, rules, cx, cz, stats)
        new_raw = nbt.splice(raw, edits) if edits else raw
        status = NEW_STATUS if scan.status in OLD_STATUS else scan.status
        if status in OLD_STATUS:
            raise ValueError('refusing to write %s: chunk %d,%d still liquid_carvers' % (region_name(rx, rz), cx, cz))
        stats['status_after'][status] += 1
        if scan.block_entities_span and scan.block_entities_span[1] - scan.block_entities_span[0] > 5:
            for be in nbt.block_entities(scan):
                bid = str(be.get('id'))
                stats['block_entities'][bid] += 1
                if bid not in ('Banner', 'FlowerPot', 'minecraft:banner', 'minecraft:flower_pot'):
                    stats['kept_block_entities'].append([bid, be.get('x'), be.get('y'), be.get('z')])
        if edits:
            comp_out = comp if comp in (1, 2, 3) else 2
            out[(lx, lz)] = (comp_out, nbt.compress(new_raw, comp_out), ts)
            stats['chunks_rewritten'] += 1
        else:
            out[(lx, lz)] = (comp, payload, ts)
        stats['chunks_written'] += 1
        samples[(lx, lz)] = sample
    return (nbt.write_region(out) if out else None), stats, samples


# ---------------------------------------------------------------- verification

def _strip(raw, scan):
    """The chunk bytes without the Status payload and the biomes payloads (what the import may change)."""
    spans = [scan.status_span] if scan.status_span else []
    spans += [s.biomes_span for s in scan.sections if s.biomes_span]
    return nbt.splice(raw, [(a, b, b'') for a, b in spans])


def verify_region(data, rx, rz, rules, src=None):
    """(problems, counts) for one written region file; `src` = the source region bytes for the byte compare."""
    problems = []
    counts = collections.Counter()
    name = region_name(rx, rz)
    try:
        chunks = nbt.read_region(data)
    except ValueError as e:
        return ['%s: header: %s' % (name, e)], counts
    used = {}
    for i in range(1024):
        off = int.from_bytes(data[i * 4:i * 4 + 3], 'big')
        cnt = data[i * 4 + 3]
        for s in range(off, off + cnt):
            if s in used:
                problems.append('%s: sector %d shared by slots %d and %d' % (name, s, used[s], i))
            used[s] = i
    if len(data) % nbt.SECTOR:
        problems.append('%s: file size %d not a multiple of 4096' % (name, len(data)))
    source = nbt.read_region(src) if src is not None else None
    for (lx, lz), (comp, payload, _ts) in sorted(chunks.items()):
        cx, cz = rx * 32 + lx, rz * 32 + lz
        where = '%s chunk %d,%d' % (name, cx, cz)
        try:
            raw = nbt.decompress(comp, payload)
            scan = nbt.scan_chunk(raw)
        except Exception as e:  # noqa: BLE001 - every broken chunk is a finding
            problems.append('%s: unreadable: %r' % (where, e))
            continue
        counts['chunks'] += 1
        counts['status ' + str(scan.status)] += 1
        if (scan.x, scan.z) != (cx, cz):
            problems.append('%s: xPos/zPos %s,%s' % (where, scan.x, scan.z))
        if not inner_chunk(cx, cz):
            counts['outside inner tiles'] += 1
        n_problems = len(problems)
        if scan.status in OLD_STATUS or scan.status is None:
            problems.append('%s: status %r' % (where, scan.status))
        for sec in scan.sections:
            if sec.biomes is not None:
                pal = next((v for _t, n, _r, v in sec.biomes if n == 'palette'), None)
                data_l = next((v for _t, n, _r, v in sec.biomes if n == 'data'), None)
                if not pal or not all(isinstance(p, str) and p for p in pal):
                    problems.append('%s Y %s: empty or bad biome palette' % (where, sec.y))
                    continue
                bits = biome_bits(len(pal))
                need = 0 if bits == 0 else -(-64 // (64 // bits))
                if bits and (data_l is None or len(data_l) != need * 8):
                    problems.append('%s Y %s: biome data %s longs, need %d' % (
                        where, sec.y, None if data_l is None else len(data_l) // 8, need))
                    continue
                idx = unpack(data_l or b'', 64, bits)
                if max(idx) >= len(pal):
                    problems.append('%s Y %s: biome index %d >= palette %d' % (where, sec.y, max(idx), len(pal)))
                    continue
                used_names = {pal[i] for i in idx}
                if len(used_names) != len(pal):
                    counts['biome palettes with unused entries'] += 1
                for b in used_names & rules.forbidden:
                    problems.append('%s Y %s: forbidden biome %s' % (where, sec.y, b))
                counts['biome sections'] += 1
            got = nbt.block_states(scan, sec)
            if got:
                bpal, bdata = got
                if not bpal:
                    problems.append('%s Y %s: empty block palette' % (where, sec.y))
                elif len(bpal) > 1:
                    bbits = max(4, (len(bpal) - 1).bit_length())
                    if len(bdata) != (-(-4096 // (64 // bbits))) * 8:
                        problems.append('%s Y %s: block data %d longs for palette %d' % (
                            where, sec.y, len(bdata) // 8, len(bpal)))
        # the rules are a fixpoint: running them again on a sound output chunk changes nothing
        edits = repaint_chunk(scan, rules, cx, cz, new_stats())[0] if len(problems) == n_problems else []
        if edits:
            problems.append('%s: repaint is not a fixpoint (%d edits on re-run)' % (where, len(edits)))
        if source is not None:
            s = source.get((lx, lz))
            if s is None:
                problems.append('%s: not in the source region' % where)
            else:
                sraw = nbt.decompress(s[0], s[1])
                sscan = nbt.scan_chunk(sraw)
                if _strip(sraw, sscan) != _strip(raw, scan):
                    problems.append('%s: bytes outside Status/biomes differ from the source' % where)
                else:
                    counts['byte-identical outside Status/biomes'] += 1
                if len(sscan.sections) != len(scan.sections):
                    problems.append('%s: section count changed' % where)
    if source is not None:
        missing = [k for k in source if k not in chunks and inner_chunk(rx * 32 + k[0], rz * 32 + k[1])]
        if missing:
            problems.append('%s: %d inner chunks of the source missing' % (name, len(missing)))
    return problems, counts


# ---------------------------------------------------------------- workers

_W = {}


def _init(zip_path, rules_data, out, keep_border, verify):
    _W['zip'] = zipfile.ZipFile(zip_path) if zip_path else None
    _W['rules'] = Rules(rules_data)
    _W['out'] = out
    _W['keep_border'] = keep_border
    _W['verify'] = verify


def _close():
    if _W.get('zip') is not None:
        _W['zip'].close()
        _W['zip'] = None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def _state_path(out, rx, rz):
    return os.path.join(out, '.state', 'r.%d.%d.json' % (rx, rz))


def _job(job):
    member, rx, rz, crc, size = job
    t = time.time()
    out, rules = _W['out'], _W['rules']
    dst = os.path.join(out, 'region', region_name(rx, rz))
    sp = _state_path(out, rx, rz)
    try:
        with open(sp, encoding='utf-8') as f:
            state = json.load(f)
        if (state.get('tool') == TOOL_VERSION and state.get('rules') == rules.hash and state.get('crc') == crc
                and state.get('size') == size and state.get('keep_border') == _W['keep_border']
                and (state.get('out_size') is None and not os.path.exists(dst)
                     or state.get('out_size') == (os.path.getsize(dst) if os.path.exists(dst) else -1))):
            return rx, rz, 'skip', state, time.time() - t
    except (OSError, ValueError):
        pass
    if size > MAX_MEMBER:
        raise ValueError('%s: %d bytes, refusing' % (member, size))
    src = _W['zip'].read(member)
    data, stats, samples = process_region(src, rx, rz, rules, _W['keep_border'])
    state = {'tool': TOOL_VERSION, 'rules': rules.hash, 'crc': crc, 'size': size, 'keep_border': _W['keep_border'],
             'stats': stats, 'samples': [[k[0], k[1]] + v for k, v in sorted(samples.items())]}
    if data is None:
        if os.path.exists(dst):
            os.remove(dst)
        state['out_size'] = state['sha256'] = None
    else:
        tmp = dst + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, dst)
        state['out_size'] = len(data)
        state['sha256'] = hashlib.sha256(data).hexdigest()
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    with open(sp + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(state, f)
    os.replace(sp + '.tmp', sp)
    return rx, rz, 'wrote %d chunks' % stats['chunks_written'], state, time.time() - t


def _verify_job(job):
    path, rx, rz, member = job
    with open(path, 'rb') as f:
        data = f.read()
    src = _W['zip'].read(member) if _W['zip'] is not None and member else None
    problems, counts = verify_region(data, rx, rz, _W['rules'], src)
    return rx, rz, problems, counts


# ---------------------------------------------------------------- rasters and report

BIOME_COLOURS = {
    'minecraft:deep_ocean': (20, 40, 110), 'minecraft:ocean': (40, 70, 160), 'minecraft:river': (60, 110, 220),
    'minecraft:frozen_river': (150, 180, 240), 'minecraft:beach': (230, 215, 150), 'minecraft:plains': (130, 190, 90),
    'minecraft:snowy_plains': (240, 245, 250), 'minecraft:badlands': (205, 100, 50), 'minecraft:desert': (240, 210, 120),
    'minecraft:dark_forest': (40, 80, 30), 'minecraft:forest': (60, 130, 50), 'minecraft:jungle': (40, 160, 40),
    'minecraft:swamp': (80, 100, 60), 'minecraft:mushroom_fields': (190, 100, 190),
    'minecraft:lush_caves': (100, 200, 120), 'minecraft:dripstone_caves': (140, 110, 90),
    'minecraft:stony_peaks': (150, 150, 150), 'minecraft:windswept_gravelly_hills': (120, 130, 120),
    'tensura:barren_land': (110, 150, 140), 'tensura:ancient_forest': (20, 50, 20),
    'minecraft:soul_sand_valley': (90, 70, 60), 'minecraft:nether_wastes': (150, 40, 40),
    'minecraft:the_end': (220, 220, 160),
}


def _colour(biome):
    c = BIOME_COLOURS.get(biome)
    if c:
        return c
    h = hashlib.md5(biome.encode()).digest()
    return (h[0], h[1], h[2])


SEA_NARROWS = 4     # px (64 blocks): water this close to the shore on both sides is a river or strait, not open sea


def split_water(cls):
    """Water pixels → SEA (open sea) or LAKE (lakes, rivers, the narrows that join them to the sea), in place.

    Open sea = water reachable from the outer edge through pixels more than SEA_NARROWS from any land, plus the
    water within SEA_NARROWS of that (a morphological opening). A plain flood fill from the edge would call Lake Siss
    and every river that reaches the coast "sea"; this keeps them `~` while the channels and bays stay sea."""
    from collections import deque
    h, w = len(cls), len(cls[0])
    far = [[-1] * w for _ in range(h)]
    q = deque()
    for r in range(h):
        for c in range(w):
            if cls[r][c] == LAND:
                far[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        d = far[r][c] + 1
        if d > SEA_NARROWS:
            continue
        for r2, c2 in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= r2 < h and 0 <= c2 < w and far[r2][c2] < 0:
                far[r2][c2] = d
                q.append((r2, c2))
    sea = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if cls[r][c] != LAND and far[r][c] < 0 and (r in (0, h - 1) or c in (0, w - 1) or cls[r][c] == MISSING):
                sea[r][c] = True
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for r2, c2 in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= r2 < h and 0 <= c2 < w and not sea[r2][c2] and cls[r2][c2] != LAND and far[r2][c2] < 0:
                sea[r2][c2] = True
                q.append((r2, c2))
    dist = {}
    for r in range(h):
        for c in range(w):
            if sea[r][c]:
                dist[(r, c)] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        d = dist[(r, c)] + 1
        if d > SEA_NARROWS:
            continue
        for r2, c2 in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= r2 < h and 0 <= c2 < w and not sea[r2][c2] and cls[r2][c2] == SEA:
                sea[r2][c2] = True
                dist[(r2, c2)] = d
                q.append((r2, c2))
    for r in range(h):
        for c in range(w):
            if cls[r][c] == SEA:
                cls[r][c] = SEA if sea[r][c] else LAKE


def build_rasters(states, rdir):
    os.makedirs(rdir, exist_ok=True)
    cls = [[MISSING] * GRID_W for _ in range(GRID_H)]
    hgt = [[0] * GRID_W for _ in range(GRID_H)]
    bio = [[None] * GRID_W for _ in range(GRID_H)]
    for (rx, rz), st in states.items():
        for lx, lz, c, h, b in st['samples']:
            cx, cz = rx * 32 + lx, rz * 32 + lz
            if not inner_chunk(cx, cz):
                continue
            col, row = cx - CHUNKS_X[0], cz - CHUNKS_Z[0]
            cls[row][col] = c
            hgt[row][col] = 0 if h is None else max(0, min(65535, h + 64))
            bio[row][col] = b
    split_water(cls)
    counts = collections.Counter()
    for row in range(GRID_H):
        for col in range(GRID_W):
            counts[cls[row][col]] += 1
    names = collections.Counter(b for r in bio for b in r if b)
    order = [n for n, _ in names.most_common()]
    index = {n: i + 1 for i, n in enumerate(order)}
    brows = [[index.get(b, 0) for b in r] for r in bio]
    write_png(os.path.join(rdir, 'landmask16.png'), GRID_W, GRID_H, cls,
              palette=[(30, 60, 140), (80, 150, 230), (110, 170, 80), (0, 0, 0)])
    write_png(os.path.join(rdir, 'heights16.png'), GRID_W, GRID_H, hgt, depth=16)
    write_png(os.path.join(rdir, 'biomes16.png'), GRID_W, GRID_H, brows,
              palette=[(0, 0, 0)] + [_colour(n) for n in order])
    legend = {
        'source': "Lerfing's Tensura map, inner tiles, after tools/lerfing/import.py (status rename + biome repaint)",
        'scale': 16, 'width': GRID_W, 'height': GRID_H,
        'origin_chunk': [CHUNKS_X[0], CHUNKS_Z[0]], 'origin_block': [CHUNKS_X[0] * 16, CHUNKS_Z[0] * 16],
        'pixel': 'column = chunk x - %d, row = chunk z - %d; each pixel samples the 16 cell-centre columns of its chunk'
                 % (CHUNKS_X[0], CHUNKS_Z[0]),
        'landmask16.png': {'type': '8-bit palette', 'classes': {'0': 'open sea (see split_water: reached from the '
                                                                       'outer edge through water > %d px from land, '
                                                                       'plus %d px of shore)' % (SEA_NARROWS,
                                                                                                 SEA_NARROWS),
                                                                  '1': 'lake or river (other water: Lake Siss, rivers '
                                                                       'and their mouths, ponds)',
                                                                  '2': 'land (>= 8 of 16 columns dry)',
                                                                  '3': 'missing chunk'},
                           'counts': {str(k): v for k, v in sorted(counts.items())}},
        'heights16.png': {'type': '16-bit gray', 'value': 'ground y + 64 (median of the 16 columns; the floor under '
                                                          'water); 0 = missing',
                          'note': '16-bit because the Canaat summit is y 316'},
        'biomes16.png': {'type': '8-bit palette', 'value': 'index into biomes (0 = missing); most common surface '
                                                           'biome of the 16 columns',
                         'biomes': [{'index': index[n], 'id': n, 'chunks': names[n], 'colour': list(_colour(n))}
                                    for n in order]},
    }
    with open(os.path.join(rdir, 'legend.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(legend, f, indent=1)
        f.write('\n')
    return counts


def edge_histogram(states):
    edges = {'west': collections.Counter(), 'east': collections.Counter(), 'north': collections.Counter(),
             'south': collections.Counter()}
    for (rx, rz), st in states.items():
        for lx, lz, _c, h, _b in st['samples']:
            cx, cz = rx * 32 + lx, rz * 32 + lz
            if h is None or not inner_chunk(cx, cz):
                continue
            if cx == CHUNKS_X[0]:
                edges['west'][h] += 1
            if cx == CHUNKS_X[1]:
                edges['east'][h] += 1
            if cz == CHUNKS_Z[0]:
                edges['north'][h] += 1
            if cz == CHUNKS_Z[1]:
                edges['south'][h] += 1
    out = {}
    for k, c in edges.items():
        if not c:
            continue
        vals = sorted(c.elements())
        out[k] = {'chunks': len(vals), 'min': vals[0], 'median': vals[len(vals) // 2], 'max': vals[-1],
                  'histogram': {str(y): n for y, n in sorted(c.items())}}
    return out


def _merge(total, stats):
    for k, v in stats.items():
        if isinstance(v, int):
            total[k] = total.get(k, 0) + v
        elif isinstance(v, list):
            total.setdefault(k, []).extend(v)
        else:
            total.setdefault(k, collections.Counter()).update(v)


def _members(z):
    """{(rx, rz): (name, crc, size)} of the inner region files in the zip (any top folder)."""
    out = {}
    for info in z.infolist():
        parts = info.filename.replace('\\', '/').split('/')
        if len(parts) < 2 or parts[-2] != 'region' or info.is_dir():
            continue
        rc = region_coords(parts[-1])
        if rc and inner_region(*rc):
            if rc in out:
                raise ValueError('two region files for %s in the zip' % (rc,))
            out[rc] = (info.filename, info.CRC, info.file_size)
    return out


def _inside_repo(path):
    try:
        os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT))
    except ValueError:
        return False
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT))
    return not rel.startswith('..')


def run_import(args, rules):
    with zipfile.ZipFile(args.zip) as z:
        members = _members(z)
        others = [i.filename for i in z.infolist()
                  if not i.is_dir() and '/region/' not in i.filename.replace('\\', '/')]
    if args.regions:
        want = set()
        for r in args.regions.split(','):
            rc = region_coords(r.strip() + ('' if r.strip().endswith('.mca') else '.mca'))
            if rc is None or rc not in members:
                sys.exit('unknown inner region: %s' % r)
            want.add(rc)
        members = {k: v for k, v in members.items() if k in want}
    os.makedirs(os.path.join(args.out, 'region'), exist_ok=True)
    jobs = sorted(((v[0], k[0], k[1], v[1], v[2]) for k, v in members.items()), key=lambda j: -j[4])
    print('import: %d inner region files from %s -> %s (%d workers, rules %s)' % (
        len(jobs), args.zip, args.out, args.workers, rules.hash), flush=True)
    t0 = time.time()
    states = {}
    init = (args.zip, rules.data, args.out, args.keep_border, False)
    if args.workers <= 1:
        _init(*init)
        results = map(_job, jobs)
    else:
        pool = Pool(args.workers, initializer=_init, initargs=init)
        results = pool.imap_unordered(_job, jobs, chunksize=1)
    done = skipped = 0
    for rx, rz, msg, state, dt in results:
        done += 1
        skipped += msg == 'skip'
        states[(rx, rz)] = state
        if done % 10 == 0 or done == len(jobs) or args.workers <= 1:
            eta = (time.time() - t0) / done * (len(jobs) - done)
            print('[%d/%d] %s %s (%.1fs) elapsed %.0fs eta %.0fs' % (
                done, len(jobs), region_name(rx, rz), msg, dt, time.time() - t0, eta), flush=True)
    if args.workers > 1:
        pool.close()
        pool.join()
    else:
        _close()
    # every state on disk (earlier sample runs included) feeds the manifest, report and rasters
    sdir = os.path.join(args.out, '.state')
    for fn in os.listdir(sdir):
        rc = region_coords(fn.replace('.json', '.mca'))
        if rc and rc not in states and os.path.exists(os.path.join(args.out, 'region', region_name(*rc))):
            with open(os.path.join(sdir, fn), encoding='utf-8') as f:
                states[rc] = json.load(f)
    total = {}
    for st in states.values():
        _merge(total, st['stats'])
    manifest = sorted('%s  region/%s' % (st['sha256'], region_name(*rc)) for rc, st in states.items() if st.get('sha256'))
    with open(os.path.join(args.out, 'sha256.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(manifest) + '\n')
    rdir = os.path.join(args.out, 'rasters')
    land = build_rasters(states, rdir)
    if args.rasters:
        import shutil
        os.makedirs(args.rasters, exist_ok=True)
        for fn in ('landmask16.png', 'heights16.png', 'biomes16.png', 'legend.json'):
            shutil.copyfile(os.path.join(rdir, fn), os.path.join(args.rasters, fn))
    size = sum(st.get('out_size') or 0 for st in states.values())
    report = {
        'tool_version': TOOL_VERSION, 'rules': os.path.relpath(args.rules, ROOT) if _inside_repo(args.rules) else args.rules,
        'rules_hash': rules.hash, 'source': os.path.basename(args.zip), 'regions_written': len(manifest),
        'output_bytes': size, 'chunks_written': total.get('chunks_written', 0),
        'status_before': total.get('status_before', {}), 'status_after': total.get('status_after', {}),
        'dropped_border_chunks': total.get('dropped_border', {}),
        'repaint_cells_3d': dict(total.get('transitions', collections.Counter()).most_common()),
        'repaint_surface_cells': dict(total.get('surface_transitions', collections.Counter()).most_common()),
        'surface_cell_note': 'surface cells = the 16 cell-centre columns per chunk (one per 4x4 blocks)',
        'sections_repainted': total.get('sections_repainted', 0),
        'biomes_after_3d': dict(total.get('biomes_after', collections.Counter()).most_common()),
        'landmask_pixels': {['sea', 'lake_river', 'land', 'missing'][k]: v for k, v in sorted(land.items())},
        'inner_edge_floor': edge_histogram(states),
        'block_entities': dict(total.get('block_entities', collections.Counter()).most_common()),
        'kept_block_entities': sorted(total.get('kept_block_entities', [])),
        'not_copied': others,
        'elapsed_s': round(time.time() - t0, 1), 'skipped_regions': skipped,
    }
    with open(os.path.join(args.out, 'report.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=1)
        f.write('\n')
    print('done: %d regions (%d unchanged), %d chunks, %.2f GB, statuses %s; report %s' % (
        len(manifest), skipped, report['chunks_written'], size / 1e9, report['status_after'],
        os.path.join(args.out, 'report.json')), flush=True)
    return report


def run_verify(args, rules):
    rdir = os.path.join(args.out, 'region')
    files = sorted(f for f in os.listdir(rdir) if region_coords(f))
    members = {}
    if args.zip:
        with zipfile.ZipFile(args.zip) as z:
            members = _members(z)
    jobs = []
    for f in files:
        rx, rz = region_coords(f)
        jobs.append((os.path.join(rdir, f), rx, rz, members.get((rx, rz), (None,))[0]))
    print('verify: %d region files in %s%s' % (len(jobs), rdir, ' against ' + args.zip if args.zip else ''), flush=True)
    init = (args.zip, rules.data, args.out, args.keep_border, True)
    if args.workers <= 1:
        _init(*init)
        results = map(_verify_job, jobs)
    else:
        pool = Pool(args.workers, initializer=_init, initargs=init)
        results = pool.imap_unordered(_verify_job, jobs, chunksize=1)
    problems, counts = [], collections.Counter()
    t0 = time.time()
    for i, (rx, rz, p, c) in enumerate(results, 1):
        problems += p
        counts.update(c)
        if i % 25 == 0 or i == len(jobs):
            print('[%d/%d] %d problems so far (%.0fs)' % (i, len(jobs), len(problems), time.time() - t0), flush=True)
    if args.workers > 1:
        pool.close()
        pool.join()
    else:
        _close()
    manifest_ok = None
    mpath = os.path.join(args.out, 'sha256.txt')
    if os.path.exists(mpath):
        manifest_ok = 0
        with open(mpath, encoding='utf-8') as f:
            lines = f.read().split('\n')
        for line in lines:
            if not line.strip():
                continue
            h, rel = line.split('  ', 1)
            p = os.path.join(args.out, rel)
            if not os.path.exists(p) or _sha256(p) != h:
                problems.append('sha256 mismatch: %s' % rel)
            else:
                manifest_ok += 1
    result = {'regions': len(jobs), 'problems': len(problems), 'first_problems': problems[:50],
              'counts': dict(sorted(counts.items())), 'sha256_ok': manifest_ok}
    with open(os.path.join(args.out, 'verify.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1)
        f.write('\n')
    for p in problems[:20]:
        print('PROBLEM', p)
    print('verify: %s - %d regions, %d chunks, %d problems; %s' % (
        'OK' if not problems else 'FAILED', len(jobs), counts.get('chunks', 0), len(problems),
        ', '.join('%s %d' % kv for kv in sorted(counts.items()) if kv[0].startswith('status'))), flush=True)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('zip', nargs='?', help='Tensura By Lerfing.zip (untrusted: read, never extracted)')
    ap.add_argument('--out', required=True, help='output world folder (outside the repo); region/ goes inside')
    ap.add_argument('--rules', default=str(RULES), help='repaint rules (default design/data/lerfing/repaint.json)')
    ap.add_argument('--rasters', help='also copy the rasters here (design/data/lerfing for the committed set)')
    ap.add_argument('--regions', help='only these inner regions, e.g. r.3.1,r.-2.0 (a sample run)')
    ap.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument('--keep-border', action='store_true', help="keep WorldPainter's border chunks in the inner files")
    ap.add_argument('--verify', action='store_true', help='re-read every written chunk (compare with the zip if given)')
    args = ap.parse_args(argv)
    if _inside_repo(args.out):
        sys.exit('refusing to write the world inside the repo: %s' % args.out)
    rules = Rules.load(args.rules)
    if args.verify:
        res = run_verify(args, rules)
        return 1 if res['problems'] else 0
    if not args.zip:
        sys.exit('the zip is required to import')
    run_import(args, rules)
    return 0


if __name__ == '__main__':
    sys.exit(main())
