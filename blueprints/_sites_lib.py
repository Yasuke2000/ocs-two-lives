"""Helpers shared by the Jura/Canaat site blueprints (sealed_cave, spirit_domain_gate, treyni_shrine, dragons_nest).

Stdlib only. Builds here are "ground layer + explicit air above": every cell of the box above the ground layer
is written (air unless built), so placing the structure also clears trees and hills inside the box.
"""
import math

import blueprint as _blueprint
from _dwargon_lib import AIR, dark_spots, noise2, noise3, rnd  # noqa: F401  (re-exported for the builds)

# Previews: a few Tensura / mossy keywords the renderer has no colour for.
for _k, _rgb in (("labyrinth", (150, 140, 120)), ("magic_ore", (90, 150, 200)), ("hipokute", (120, 190, 90)),
                 ("tinted", (90, 70, 120)), ("froglight", (190, 225, 160))):
    if not any(k == _k for k, _ in _blueprint._COLORS):
        _blueprint._COLORS.append((_k, _rgb))


def M(name: str) -> str:
    return "minecraft:" + name


def air_above(bp, ground: int) -> None:
    sx, sy, sz = bp.size
    for x in range(sx):
        for z in range(sz):
            for y in range(ground + 1, sy):
                bp.blocks[(x, y, z)] = AIR


def put(bp, x, y, z, state: str) -> None:
    """bp.set without bounds errors for decorations that may graze the box edge."""
    sx, sy, sz = bp.size
    if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
        bp.set(x, y, z, state)


def pick(palette, r: float) -> str:
    """Weighted choice from [(state, weight), ...] with r in [0, 1)."""
    total = sum(w for _, w in palette)
    t = r * total
    for state, w in palette:
        t -= w
        if t < 0:
            return state
    return palette[-1][0]


def line(x1, z1, x2, z2):
    """Integer points on the segment (Bresenham)."""
    dx, dz = abs(x2 - x1), abs(z2 - z1)
    sx = 1 if x1 < x2 else -1
    sz = 1 if z1 < z2 else -1
    err = dx - dz
    x, z = x1, z1
    out = []
    while True:
        out.append((x, z))
        if x == x2 and z == z2:
            break
        e2 = 2 * err
        if e2 > -dz:
            err -= dz
            x += sx
        if e2 < dx:
            err += dx
            z += sz
    return out


def ring_points(cx, cy, cz, radius, plane, step_deg=1.0):
    """Integer points on a circle in the xz ('h'), xy ('x') or zy ('z') plane through (cx, cy, cz)."""
    seen = []
    pts = set()
    n = int(360 / step_deg)
    for i in range(n):
        a = math.radians(i * step_deg)
        u, v = round(radius * math.cos(a)), round(radius * math.sin(a))
        p = {"h": (cx + u, cy, cz + v), "x": (cx + u, cy + v, cz), "z": (cx, cy + v, cz + u)}[plane]
        if p not in pts:
            pts.add(p)
            seen.append((p, math.degrees(a)))
    return seen


def tree(bp, x, y, z, height, leaves="oak", log=None, wide=2):
    """A small round-crowned tree standing on (x, y, z) (y = first trunk block). Persistent leaves."""
    log = log or f"minecraft:{leaves}_log"
    leaf = f"minecraft:{leaves}_leaves[persistent=true]"
    for dy in range(height):
        put(bp, x, y + dy, z, log)
    top = y + height
    for dy in range(-2, 2):
        r = wide if dy < 0 else wide - 1 if dy == 0 else max(0, wide - 2)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r and abs(dz) == r and r > 1 and rnd(x + dx, top + dy, z + dz, 5) < 0.5:
                    continue
                if (dx, dz) == (0, 0) and dy < 0:
                    continue
                sx, sy, sz = bp.size
                px, py, pz = x + dx, top + dy, z + dz
                if 0 <= px < sx and 0 <= py < sy and 0 <= pz < sz and bp.blocks.get((px, py, pz), AIR) == AIR:
                    bp.blocks[(px, py, pz)] = leaf


def exposed(blocks, x, y, z) -> bool:
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        if blocks.get((x + dx, y + dy, z + dz)) == AIR:
            return True
    return False


def light_up(bp, candidates, add_light, limit: int = 400) -> int:
    """Re-run the block-light check and call add_light(x, y, z) on each dark spot until none is left.

    Returns the number of lights added. Raises if the loop does not converge (a spot that cannot be lit).
    """
    added = 0
    for _ in range(12):
        spots = dark_spots(bp.blocks, bp.size, candidates)
        if not spots:
            return added
        # Light the darkest area first, one source per cluster (a source reaches ~14 blocks).
        done = set()
        for (x, y, z) in spots:
            if any(abs(x - a) + abs(z - b) < 6 and abs(y - c) < 6 for a, b, c in done):
                continue
            add_light(x, y, z)
            done.add((x, y, z))
            added += 1
            if added > limit:
                raise RuntimeError("too many lights added; check the build")
    raise RuntimeError(f"{bp.name}: dark spots left after lighting: {dark_spots(bp.blocks, bp.size, candidates)[:5]}")
