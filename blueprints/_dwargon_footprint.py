"""Ground data for placing Dwargon on real terrain: written to a generated KubeJS file by build_structures.py.

The grid covers the structure box plus MARGIN columns on every side, row-major (z outer, x inner), cell
(0, 0) = blueprint column (-MARGIN, -MARGIN). Per cell, two run-length encoded values ([value, count, ...];
NONE = nothing to do), heights relative to the structure's base layer:

- fill:  fill the gap between the real ground and this layer (exclusive) with mountain rock. Footprint
         columns: the lowest non-air block of the build, so nothing floats. Columns round the footprint:
         a 1:1 talus skirt falling away from the build's surface, so edges meet low ground in a slope.
- clear: remove terrain from this layer upward. Columns whose highest block is air (the approach, the
         ravine, the skylight crack) are open sky by design; the columns round them get a 1:1 cut slope.
- bottom: the lowest block the build defines in a footprint column, explicit air included (NONE: the column
         holds no solid block at all, only air or nothing, and every margin column). life/repair.js fills caves and
         lava only below it and treats a NONE box column as open ground, so it never fills into the carved city; a
         column of air alone (the cleft's upper walls in carve mode) is never given a foundation under its air.
- roof:  carve mode (bp.roof): the highest interior air of a column that Lerfing's rock closes over the city;
         dwargon.js and tools/lerfing/dwargon_fit.py measure the rock cover above it.
- shell: carve mode: the cells the build does NOT define that touch (6 sides) a cell it defines as air: where the
         real mountain meets the carved air (the cleft's walls, the skylight crack, the box faces). Flat list of
         [grid cell, y1, y2] runs (y relative to the base layer). dwargon.js turns water and lava there into rock
         after placing, so Lerfing's springs and lava pockets cannot pour into the city (staging 19/11: 2,253
         cells of the throne hall and forge street flooded from two springs at the crack's rim, lava in the cleft).
"""
import json
import math

from _dwargon_lib import AIR

MARGIN = 10
NONE = -999


def _rle(values):
    out = []
    for v in values:
        if out and out[-2] == v:
            out[-1] += 1
        else:
            out += [v, 1]
    return out


def footprint(bp, probes, arrival, parts) -> str:
    sx, sy, sz = bp.size
    low, high, top_state, bottom = {}, {}, {}, {}
    for (x, y, z), state in bp.blocks.items():
        k = (x, z)
        if y < bottom.get(k, sy):
            bottom[k] = y
        if state != AIR and y < low.get(k, sy):
            low[k] = y
        if y > high.get(k, -1):
            high[k] = y
            top_state[k] = state
    surface = {}  # highest non-air block per footprint column
    for (x, y, z), state in bp.blocks.items():
        if state != AIR and y > surface.get((x, z), -1):
            surface[(x, z)] = y
    clear_cols = {k: high[k] + 1 for k in high if top_state[k] == AIR}
    w, l = sx + 2 * MARGIN, sz + 2 * MARGIN
    fill = {(x, z): y for (x, z), y in low.items()}
    clear = dict(clear_cols)
    # Skirts and cut slopes: stamp a disc round every edge column, keep the best value per cell.
    skirt, cut = {}, {}
    disc = [(dx, dz, math.hypot(dx, dz)) for dx in range(-MARGIN, MARGIN + 1) for dz in range(-MARGIN, MARGIN + 1)
            if 0 < math.hypot(dx, dz) <= MARGIN]
    def edge(cols, k):
        x, z = k
        return any((x + dx, z + dz) not in cols for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for k, s in surface.items():
        if not edge(surface, k):
            continue
        for dx, dz, d in disc:
            c = (k[0] + dx, k[1] + dz)
            if c in surface:
                continue
            v = s + 1 - math.ceil(d)
            if v > skirt.get(c, NONE):
                skirt[c] = v
    for k, c0 in clear_cols.items():
        if not edge(clear_cols, k):
            continue
        for dx, dz, d in disc:
            c = (k[0] + dx, k[1] + dz)
            if c in high:
                continue
            v = c0 + math.ceil(d)
            if c not in cut or v < cut[c]:
                cut[c] = v
    roof = getattr(bp, "roof", None) or {}
    shell = {}
    if roof:
        for (x, y, z), state in bp.blocks.items():
            if state != AIR:
                continue
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + dx, y + dy, z + dz)
                if q not in bp.blocks and -MARGIN <= q[0] < sx + MARGIN and -MARGIN <= q[2] < sz + MARGIN:
                    shell.setdefault((q[0], q[2]), set()).add(q[1])
    runs = []
    for (x, z) in sorted(shell, key=lambda k: (k[1], k[0])):
        ys = sorted(shell[(x, z)])
        i = (z + MARGIN) * w + (x + MARGIN)
        start = prev = ys[0]
        for y in ys[1:] + [None]:
            if y is not None and y == prev + 1:
                prev = y
                continue
            runs += [i, start, prev]
            if y is not None:
                start = prev = y
    fills, clears, bottoms, roofs = [], [], [], []
    for gz in range(l):
        for gx in range(w):
            k = (gx - MARGIN, gz - MARGIN)
            fills.append(fill.get(k, skirt.get(k, NONE)))
            clears.append(clear.get(k, cut.get(k, NONE)))
            bottoms.append(bottom.get(k, NONE) if k in low else NONE)
            roofs.append(roof.get(k, NONE))
    data = {
        "size": list(bp.size), "margin": MARGIN, "grid": [w, l], "none": NONE,
        "arrival": list(arrival), "probes": [list(p) for p in probes],
        "parts": list(parts) if parts else [0],
        "fill": _rle(fills), "clear": _rle(clears), "bottom": _rle(bottoms), "roof": _rle(roofs),
        "shell": runs,
    }
    body = json.dumps(data, separators=(",", ":"))
    return ("// priority: 200\n"
            "// GENERATED by tools/build_structures.py from blueprints/dwargon.py (_dwargon_footprint.py). Do not edit.\n"
            f"const TtlDwargonFootprint = {body}\n")
