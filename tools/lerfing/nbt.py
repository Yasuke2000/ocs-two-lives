"""NBT and Anvil (.mca) reading/writing for the Lerfing import. Stdlib only.

The reader turns NBT into plain Python values (long arrays stay raw big-endian bytes, `LongArray`).
The import never re-serialises a whole chunk: `scan_chunk` records the byte spans of the few tags it rewrites
(the status string, each section's `biomes` compound) and `splice` replaces only those spans, so every other byte
of the chunk is copied unchanged.
"""
import struct
import zlib
import gzip

SECTOR = 4096


class LongArray(bytes):
    """Raw big-endian int64 payload (len = 8 * n)."""


# ---------------------------------------------------------------- reading

def _read_payload(buf, pos, tag):
    if tag == 1:
        return struct.unpack_from('>b', buf, pos)[0], pos + 1
    if tag == 2:
        return struct.unpack_from('>h', buf, pos)[0], pos + 2
    if tag == 3:
        return struct.unpack_from('>i', buf, pos)[0], pos + 4
    if tag == 4:
        return struct.unpack_from('>q', buf, pos)[0], pos + 8
    if tag == 5:
        return struct.unpack_from('>f', buf, pos)[0], pos + 4
    if tag == 6:
        return struct.unpack_from('>d', buf, pos)[0], pos + 8
    if tag == 7:
        n = struct.unpack_from('>i', buf, pos)[0]
        pos += 4
        return bytes(buf[pos:pos + n]), pos + n
    if tag == 8:
        n = struct.unpack_from('>H', buf, pos)[0]
        pos += 2
        return bytes(buf[pos:pos + n]).decode('utf-8', 'replace'), pos + n
    if tag == 9:
        et = buf[pos]
        n = struct.unpack_from('>i', buf, pos + 1)[0]
        pos += 5
        out = []
        for _ in range(max(n, 0)):
            v, pos = _read_payload(buf, pos, et)
            out.append(v)
        return out, pos
    if tag == 10:
        d = {}
        while True:
            t = buf[pos]
            pos += 1
            if t == 0:
                return d, pos
            n = struct.unpack_from('>H', buf, pos)[0]
            pos += 2
            name = bytes(buf[pos:pos + n]).decode('utf-8', 'replace')
            pos += n
            d[name], pos = _read_payload(buf, pos, t)
    if tag == 11:
        n = struct.unpack_from('>i', buf, pos)[0]
        pos += 4
        return list(struct.unpack_from('>%di' % n, buf, pos)), pos + 4 * n
    if tag == 12:
        n = struct.unpack_from('>i', buf, pos)[0]
        pos += 4
        return LongArray(buf[pos:pos + 8 * n]), pos + 8 * n
    raise ValueError('bad tag %r at %d' % (tag, pos))


_FIXED = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8}


def skip_payload(buf, pos, tag):
    """Position after a payload of type `tag` starting at `pos`, without building values."""
    if tag in _FIXED:
        return pos + _FIXED[tag]
    if tag == 7:
        return pos + 4 + struct.unpack_from('>i', buf, pos)[0]
    if tag == 8:
        return pos + 2 + struct.unpack_from('>H', buf, pos)[0]
    if tag == 11:
        return pos + 4 + 4 * struct.unpack_from('>i', buf, pos)[0]
    if tag == 12:
        return pos + 4 + 8 * struct.unpack_from('>i', buf, pos)[0]
    if tag == 9:
        et = buf[pos]
        n = struct.unpack_from('>i', buf, pos + 1)[0]
        pos += 5
        if n <= 0:
            return pos
        if et in _FIXED:
            return pos + n * _FIXED[et]
        for _ in range(n):
            pos = skip_payload(buf, pos, et)
        return pos
    if tag == 10:
        while True:
            t = buf[pos]
            pos += 1
            if t == 0:
                return pos
            pos += 2 + struct.unpack_from('>H', buf, pos)[0]
            pos = skip_payload(buf, pos, t)
    raise ValueError('bad tag %r at %d' % (tag, pos))


def read_payload(buf, pos, tag):
    """Public: (value, end) of the payload at `pos`."""
    return _read_payload(buf, pos, tag)


def parse(buf):
    """Parse an uncompressed NBT blob with a root compound into a dict."""
    buf = memoryview(buf)
    if buf[0] != 10:
        raise ValueError('root not compound')
    n = struct.unpack_from('>H', buf, 1)[0]
    v, _ = _read_payload(buf, 3 + n, 10)
    return v


def read_gzip_nbt(path):
    with open(path, 'rb') as f:
        data = f.read()
    try:
        data = gzip.decompress(data)
    except OSError:
        pass
    return parse(data)


def iter_compound(buf, pos):
    """Yield (tag, name, payload_start, payload_end) for each entry of the compound payload at `pos`.

    After the loop, the generator's return value is the position after the end tag."""
    while True:
        t = buf[pos]
        if t == 0:
            return pos + 1
        n = struct.unpack_from('>H', buf, pos + 1)[0]
        name = bytes(buf[pos + 3:pos + 3 + n]).decode('utf-8', 'replace')
        start = pos + 3 + n
        end = skip_payload(buf, start, t)
        yield t, name, pos, start, end
        pos = end


# ---------------------------------------------------------------- chunk scanning

class Section:
    __slots__ = ('y', 'biomes', 'biomes_span', 'block_span')

    def __init__(self):
        self.y = None
        self.biomes = None          # list of (tag, name, raw_entry_bytes, value or None) in stored order
        self.biomes_span = None     # (start, end) of the biomes compound payload
        self.block_span = None      # (start, end) of the block_states compound payload


class ChunkScan:
    __slots__ = ('buf', 'status', 'status_span', 'x', 'z', 'data_version', 'sections', 'block_entities_span',
                 'root_keys')

    def __init__(self, buf):
        self.buf = buf
        self.status = None
        self.status_span = None
        self.x = self.z = self.data_version = None
        self.sections = []
        self.block_entities_span = None
        self.root_keys = []


def _scan_biomes(buf, start):
    entries = []
    for t, name, entry_start, ps, pe in iter_compound(buf, start):
        value = None
        if name == 'palette' and t == 9:
            value, _ = _read_payload(buf, ps, 9)
        elif name == 'data' and t == 12:
            value, _ = _read_payload(buf, ps, 12)
        entries.append((t, name, bytes(buf[entry_start:pe]), value))
    return entries


def scan_chunk(raw):
    """Scan an uncompressed chunk NBT (root compound). Returns a ChunkScan with spans of the rewritable tags."""
    buf = memoryview(raw)
    if buf[0] != 10:
        raise ValueError('chunk root is not a compound')
    n = struct.unpack_from('>H', buf, 1)[0]
    cs = ChunkScan(buf)
    for t, name, _, ps, pe in iter_compound(buf, 3 + n):
        cs.root_keys.append(name)
        if name == 'Status' and t == 8:
            cs.status, _ = _read_payload(buf, ps, 8)
            cs.status_span = (ps, pe)
        elif name == 'xPos' and t == 3:
            cs.x = struct.unpack_from('>i', buf, ps)[0]
        elif name == 'zPos' and t == 3:
            cs.z = struct.unpack_from('>i', buf, ps)[0]
        elif name == 'DataVersion' and t == 3:
            cs.data_version = struct.unpack_from('>i', buf, ps)[0]
        elif name == 'block_entities' and t == 9:
            cs.block_entities_span = (ps, pe)
        elif name == 'sections' and t == 9:
            et = buf[ps]
            cnt = struct.unpack_from('>i', buf, ps + 1)[0]
            if et != 10 and cnt > 0:
                raise ValueError('sections is not a list of compounds')
            pos = ps + 5
            for _ in range(max(cnt, 0)):
                sec = Section()
                for st, sname, _e, sps, spe in iter_compound(buf, pos):
                    if sname == 'Y' and st == 1:
                        sec.y = struct.unpack_from('>b', buf, sps)[0]
                    elif sname == 'biomes' and st == 10:
                        sec.biomes_span = (sps, spe)
                        sec.biomes = _scan_biomes(buf, sps)
                    elif sname == 'block_states' and st == 10:
                        sec.block_span = (sps, spe)
                    pos = spe
                pos += 1  # the section's end tag
                cs.sections.append(sec)
    return cs


def block_states(cs, sec):
    """(palette entries, packed data bytes) of a section's block_states, or None."""
    if sec.block_span is None:
        return None
    v, _ = _read_payload(cs.buf, sec.block_span[0], 10)
    pal = v.get('palette') or []
    return pal, v.get('data', b'')


def block_entities(cs):
    if cs.block_entities_span is None:
        return []
    v, _ = _read_payload(cs.buf, cs.block_entities_span[0], 9)
    return v


def splice(raw, edits):
    """Replace byte spans: edits = [(start, end, new_bytes)], non-overlapping."""
    out = []
    pos = 0
    for start, end, new in sorted(edits, key=lambda e: e[0]):
        if start < pos:
            raise ValueError('overlapping edits')
        out.append(bytes(raw[pos:start]))
        out.append(new)
        pos = end
    out.append(bytes(raw[pos:]))
    return b''.join(out)


# ---------------------------------------------------------------- writing (only the tags the import rewrites)

def enc_string(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def enc_string_list(values):
    return bytes([8]) + struct.pack('>i', len(values)) + b''.join(enc_string(v) for v in values)


def enc_long_array(raw_be):
    if len(raw_be) % 8:
        raise ValueError('long array payload not a multiple of 8')
    return struct.pack('>i', len(raw_be) // 8) + bytes(raw_be)


def enc_entry(tag, name, payload):
    return bytes([tag]) + enc_string(name) + payload


# ---------------------------------------------------------------- region files

def read_region(data):
    """{(lx, lz): (compression, payload_bytes, timestamp)} of a region file held in memory."""
    out = {}
    if len(data) < 2 * SECTOR:
        return out
    for i in range(1024):
        off = struct.unpack_from('>I', data, i * 4)[0]
        sec, cnt = off >> 8, off & 0xFF
        if sec == 0 and cnt == 0:
            continue
        ts = struct.unpack_from('>I', data, SECTOR + i * 4)[0]
        p = sec * SECTOR
        if sec < 2 or p + 5 > len(data):
            raise ValueError('chunk %d: offset %d outside the file' % (i, sec))
        length = struct.unpack_from('>I', data, p)[0]
        if length < 1 or p + 4 + length > len(data) or length + 4 > cnt * SECTOR:
            raise ValueError('chunk %d: bad length %d (sectors %d)' % (i, length, cnt))
        comp = data[p + 4]
        out[(i % 32, i // 32)] = (comp, bytes(data[p + 5:p + 4 + length]), ts)
    return out


def decompress(comp, payload):
    if comp & 0x80:
        raise ValueError('external .mcc chunk not supported')
    if comp == 2:
        return zlib.decompress(payload)
    if comp == 1:
        return gzip.decompress(payload)
    if comp == 3:
        return bytes(payload)
    raise ValueError('compression %d not supported' % comp)


def compress(raw, comp=2):
    if comp == 2:
        return zlib.compress(raw, 6)
    if comp == 1:
        return gzip.compress(raw, 6, mtime=0)
    if comp == 3:
        return bytes(raw)
    raise ValueError('compression %d not supported' % comp)


def write_region(chunks):
    """Region file bytes from {(lx, lz): (compression, payload, timestamp)}; chunks laid out in slot order."""
    offsets = bytearray(SECTOR)
    stamps = bytearray(SECTOR)
    body = []
    sector = 2
    for i in range(1024):
        key = (i % 32, i // 32)
        if key not in chunks:
            continue
        comp, payload, ts = chunks[key]
        blob = struct.pack('>I', len(payload) + 1) + bytes([comp]) + payload
        n = -(-len(blob) // SECTOR)
        if n > 255:
            raise ValueError('chunk %s needs %d sectors (> 255, external file not supported)' % (key, n))
        struct.pack_into('>I', offsets, i * 4, (sector << 8) | n)
        struct.pack_into('>I', stamps, i * 4, ts)
        body.append(blob + b'\0' * (n * SECTOR - len(blob)))
        sector += n
    return bytes(offsets) + bytes(stamps) + b''.join(body)


# ---------------------------------------------------------------- typed writer (synthetic chunks for tests and tools)

def enc_payload(tag, value):
    """Payload bytes of a typed value. Compound: list of (name, tag, value); list: (element_tag, [values]);
    long array: list of ints; strings, numbers and byte arrays as plain Python values."""
    if tag == 1:
        return struct.pack('>b', value)
    if tag == 2:
        return struct.pack('>h', value)
    if tag == 3:
        return struct.pack('>i', value)
    if tag == 4:
        return struct.pack('>q', value)
    if tag == 5:
        return struct.pack('>f', value)
    if tag == 6:
        return struct.pack('>d', value)
    if tag == 7:
        return struct.pack('>i', len(value)) + bytes(value)
    if tag == 8:
        return enc_string(value)
    if tag == 9:
        et, items = value
        return bytes([et if items else (et or 0)]) + struct.pack('>i', len(items)) + \
            b''.join(enc_payload(et, v) for v in items)
    if tag == 10:
        return b''.join(enc_entry(t, n, enc_payload(t, v)) for n, t, v in value) + b'\x00'
    if tag == 11:
        return struct.pack('>i', len(value)) + struct.pack('>%di' % len(value), *value)
    if tag == 12:
        if isinstance(value, (bytes, bytearray)):
            return enc_long_array(value)
        return struct.pack('>i', len(value)) + struct.pack('>%dq' % len(value), *value)
    raise ValueError('bad tag %r' % tag)


def enc_root(entries, name=''):
    """A whole NBT blob: root compound from a list of (name, tag, value)."""
    return bytes([10]) + enc_string(name) + enc_payload(10, entries)
