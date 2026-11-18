"""Helpers for the Demon Lord seat builds (clayman_castle, forgotten_dragon_city, laura, ...). Stdlib only.

Small drawing primitives on top of tools/blueprint.py (round towers, cones, rectangular wall rings, pixel
art) plus the "light every spawnable spot" pass shared with tempest.py/dwargon.py (_dwargon_lib.dark_spots).
Everything here clips to the blueprint box instead of raising, so builds can draw near the edge.
"""
import math

import blueprint as _blueprint
from _dwargon_lib import AIR, dark_spots, rnd

# Preview colours for blocks the renderer has no keyword for (unknown names get a hash colour, often pink).
for _key, _rgb in (("thatch", (196, 164, 84)), ("bone", (226, 222, 202)), ("podzol", (95, 68, 38)),
                   ("crying", (70, 30, 120)), ("campfire", (240, 150, 60)), ("hay_block", (190, 160, 40)),
                   ("amethyst", (150, 100, 200)), ("clay", (160, 166, 180))):
    if not any(k == _key for k, _ in _blueprint._COLORS):
        _blueprint._COLORS.append((_key, _rgb))


def M(name: str) -> str:
    return "minecraft:" + name


def stair(name: str, facing: str, half: str = "bottom") -> str:
    """Stairs that ascend toward `facing` (vanilla: the back of the stair is on that side)."""
    return M(f"{name}_stairs[facing={facing},half={half}]")


def slab(name: str, kind: str = "bottom") -> str:
    return M(f"{name}_slab[type={kind}]")


def inside(bp, x, y, z) -> bool:
    sx, sy, sz = bp.size
    return 0 <= x < sx and 0 <= y < sy and 0 <= z < sz


def put(bp, x, y, z, state: str) -> None:
    if inside(bp, x, y, z):
        bp.set(x, y, z, state)


def fill(bp, x1, y1, z1, x2, y2, z2, state: str) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                put(bp, x, y, z, state)


def fill_air(bp, y_from: int = 0) -> None:
    """Every cell from layer y_from up is explicitly air (placing the build clears trees; the light check needs it)."""
    sx, sy, sz = bp.size
    for y in range(y_from, sy):
        for z in range(sz):
            for x in range(sx):
                bp.blocks[(x, y, z)] = AIR


def clear(bp, x1, y1, z1, x2, y2, z2) -> None:
    fill(bp, x1, y1, z1, x2, y2, z2, AIR)


def ring_cells(cx, cz, r):
    """Integer columns of a one-block-thick circle of radius r (same rule as Blueprint.disc with inner=r-1)."""
    out = []
    for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
        for z in range(math.floor(cz - r), math.ceil(cz + r) + 1):
            d = math.hypot(x - cx, z - cz)
            if r - 0.75 < d <= r + 0.25:
                out.append((x, z))
    return out


def disc_cells(cx, cz, r):
    out = []
    for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
        for z in range(math.floor(cz - r), math.ceil(cz + r) + 1):
            if math.hypot(x - cx, z - cz) <= r + 0.25:
                out.append((x, z))
    return out


def round_tower(bp, cx, cz, r, y0, y1, wall, glass=None, glass_every=7, glass_from=3, inner_air=True):
    """Hollow round tower: wall rings y0..y1; slit windows on the four sides every `glass_every` layers."""
    ring, hollow = ring_cells(cx, cz, r), [c for c in disc_cells(cx, cz, r) if c not in set(ring_cells(cx, cz, r))]
    for y in range(y0, y1 + 1):
        for x, z in ring:
            put(bp, x, y, z, wall(x, y, z) if callable(wall) else wall)
        if inner_air:
            for x, z in hollow:
                put(bp, x, y, z, AIR)
    if glass:
        for y in range(y0 + glass_from, y1 - 2, glass_every):
            for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
                for k in (0, 1, 2):
                    put(bp, cx + dx, y + k, cz + dz, glass)


def floor_disc(bp, cx, cz, r, y, state):
    for x, z in disc_cells(cx, cz, r):
        put(bp, x, y, z, state)


def crenellate_ring(bp, cx, cz, r, y, state):
    for x, z in ring_cells(cx, cz, r):
        if (x + z) % 2 == 0:
            put(bp, x, y, z, state)


def cone(bp, cx, cz, y0, r, h, state, finial=None):
    """Stepped spire from y0 to y0+h-1: rings shrinking from radius r to a point (solid from radius 2)."""
    for k in range(h):
        rr = max(0.6, r * (1 - k / h) ** 1.2)
        cells = disc_cells(cx, cz, rr)  # solid: a hollow spire would hold dark cells nobody can reach
        for x, z in cells:
            put(bp, x, y0 + k, z, state(x, y0 + k, z) if callable(state) else state)
    if finial:
        for i, s in enumerate(finial):
            put(bp, cx, y0 + h + i, cz, s)


def rect_ring(bp, x1, z1, x2, z2, y, state, thick=1):
    """Perimeter of a rectangle on layer y, `thick` blocks deep (state may be a function of x, y, z)."""
    for t in range(thick):
        a, b, c, d = x1 + t, z1 + t, x2 - t, z2 - t
        if a > c or b > d:
            break
        cells = [(x, b) for x in range(a, c + 1)] + [(x, d) for x in range(a, c + 1)]
        cells += [(a, z) for z in range(b + 1, d)] + [(c, z) for z in range(b + 1, d)]
        for x, z in cells:
            put(bp, x, y, z, state(x, y, z) if callable(state) else state)


def pixel_art(bp, x0, y_top, z, rows, palette, axis="x", flip=False):
    """Draw rows (top to bottom, one character per block; '.' = skip) in a vertical plane.

    axis "x": the picture spans x at fixed z. `flip` mirrors it (use it for art seen from the other side)."""
    for r, row in enumerate(rows):
        seq = row[::-1] if flip else row
        for i, ch in enumerate(seq):
            if ch != "." and ch in palette:
                if axis == "x":
                    put(bp, x0 + i, y_top - r, z, palette[ch])
                else:
                    put(bp, z, y_top - r, x0 + i, palette[ch])


def light_pass(bp, region, y_min, lamp, post=None, rounds: int = 12, label: str = "build") -> int:
    """Add lamps until no spawnable spot in `region(x, y, z)` (above layer y_min) has block light 0.

    `lamp(x, y, z)` returns the state placed in the dark cell itself (a floor lantern); `post(x, y, z)`, if
    given and the 4 cells above are free, returns a callable list of (dy, state) forming a lamp post instead.
    Returns how many lamps were added."""
    added = 0
    for _ in range(rounds):
        cands = [p for p, s in bp.blocks.items() if s == AIR and p[1] >= y_min and region(p[0], p[1], p[2])]
        spots = dark_spots(bp.blocks, bp.size, cands)
        if not spots:
            return added
        placed = []
        for (x, y, z) in spots:
            if any(abs(x - a) + abs(y - b) + abs(z - c) <= 9 for a, b, c in placed):
                continue
            if post and all(bp.blocks.get((x, y + k, z)) == AIR for k in range(4)):
                for dy, state in post(x, y, z):
                    bp.set(x, y + dy, z, state)
            else:
                bp.set(x, y, z, lamp(x, y, z))
            placed.append((x, y, z))
            added += 1
    raise RuntimeError(f"{label}: could not light every spawnable spot")


def roofed(bp, x, y, z) -> bool:
    """Whether any block above (x, y, z) in the box is not air (the cell is under a roof or ceiling)."""
    for yy in range(y + 1, bp.size[1]):
        if bp.blocks.get((x, yy, z), AIR) != AIR:
            return True
    return False


def mix(seed: int, *choices):
    """A state function picking among (state, weight) by position noise: mix(7, (a, 70), (b, 30))."""
    total = sum(w for _, w in choices)

    def pick(x, y, z):
        v = rnd(x, y, z, seed) * total
        for state, w in choices:
            v -= w
            if v < 0:
                return state
        return choices[-1][0]

    return pick
