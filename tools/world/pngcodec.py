"""PNG codec for the own-world rasters (stdlib only).

Moved here from tools/lerfing/common.py (design/architecture/own-world.md §5.2: the PNG codec moves to tools/world/;
the Lerfing copy stays until WP-W13 retires that package). Writes 8/16-bit grey, 8-bit palette and 8-bit RGB; reads
the same (non-interlaced). Output is deterministic: no timestamps, fixed zlib level, filter type 0 on every row.
"""
import struct
import zlib
from pathlib import Path

SIGNATURE = b'\x89PNG\r\n\x1a\n'


def _chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF)


def encode(width, height, data, depth=8, palette=None, rgb=False):
    """PNG bytes. data: a flat sequence of width*height samples (row-major), or width*height*3 bytes when rgb.
    depth 16 = big-endian 16-bit grey; palette = list of (r, g, b) -> colour type 3."""
    if rgb:
        ctype, spp = 2, 3
    elif palette:
        ctype, spp = 3, 1
    else:
        ctype, spp = 0, 1
    if depth == 16 and ctype != 0:
        raise ValueError('16-bit is grey only')
    n = width * spp
    raw = bytearray()
    for j in range(height):
        raw.append(0)
        row = data[j * n:(j + 1) * n]
        if depth == 16:
            raw += struct.pack('>%dH' % n, *row)
        else:
            raw += bytes(row)
    out = SIGNATURE + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, ctype, 0, 0, 0))
    if palette:
        out += _chunk(b'PLTE', b''.join(bytes(c) for c in palette))
    return out + _chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + _chunk(b'IEND', b'')


def write_png(path, width, height, data, depth=8, palette=None, rgb=False):
    Path(path).write_bytes(encode(width, height, data, depth, palette, rgb))


def read_png(path):
    """(width, height, flat samples, palette or None). RGB images give 3 samples per pixel."""
    data = Path(path).read_bytes()
    if data[:8] != SIGNATURE:
        raise ValueError('not a PNG')
    pos, idat, palette = 8, b'', None
    w = h = depth = ctype = None
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
            if interlace or ctype not in (0, 2, 3) or depth not in (8, 16) or (depth == 16 and ctype != 0):
                raise ValueError('unsupported PNG (type %d, depth %d)' % (ctype, depth))
        elif kind == b'PLTE':
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b'IDAT':
            idat += body
        elif kind == b'IEND':
            break
    bpp = (depth // 8) * (3 if ctype == 2 else 1)
    stride = w * bpp
    raw = zlib.decompress(idat)
    out = []
    prev, i = bytearray(stride), 0
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
        if depth == 16:
            out.extend(struct.unpack('>%dH' % (stride // 2), bytes(line)))
        else:
            out.extend(line)
        prev = line
    return w, h, out, palette
