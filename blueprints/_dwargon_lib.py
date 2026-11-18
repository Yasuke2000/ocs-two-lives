"""Helpers for blueprints/dwargon.py: deterministic noise and a block-light check (stdlib only).

The light check is a small re-implementation of Minecraft block light: sources spread light through
non-opaque blocks, losing one level per block. Overworld monsters only spawn at block light 0, so any
spawnable surface inside the city with light >= 1 is safe. Slabs and stairs are treated as opaque
(conservative: real light leaks past them, so the check only ever over-lights).
"""
import math

AIR = "minecraft:air"


# --- noise --------------------------------------------------------------------------------------
def _h(ix: int, iy: int, iz: int, seed: int) -> float:
    n = (ix * 374761393 + iy * 668265263 + iz * 1274126177 + seed * 144269504) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return n / 0xFFFFFFFF


def rnd(x: int, y: int, z: int, seed: int) -> float:
    """White noise in [0, 1] for one position (stable between runs, unlike hash())."""
    return _h(x, y, z, seed)


def _s(t: float) -> float:
    return t * t * (3 - 2 * t)


def noise2(x: float, z: float, scale: float, seed: int) -> float:
    fx, fz = x / scale, z / scale
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = _s(fx - ix), _s(fz - iz)
    a, b = _h(ix, 0, iz, seed), _h(ix + 1, 0, iz, seed)
    c, d = _h(ix, 0, iz + 1, seed), _h(ix + 1, 0, iz + 1, seed)
    return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz


def fbm2(x: float, z: float, scale: float, seed: int, octaves: int = 3) -> float:
    total = norm = 0.0
    amp = 1.0
    for i in range(octaves):
        total += amp * noise2(x, z, scale / (2 ** i), seed + 31 * i)
        norm += amp
        amp *= 0.5
    return total / norm


def noise3(x: float, y: float, z: float, scale: float, seed: int) -> float:
    fx, fy, fz = x / scale, y / scale, z / scale
    ix, iy, iz = math.floor(fx), math.floor(fy), math.floor(fz)
    tx, ty, tz = _s(fx - ix), _s(fy - iy), _s(fz - iz)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (tx if dx else 1 - tx) * (ty if dy else 1 - ty) * (tz if dz else 1 - tz)
                out += w * _h(ix + dx, iy + dy, iz + dz, seed)
    return out


# --- block light ----------------------------------------------------------------------------------
_SEE_THROUGH = ("air", "glass", "pane", "lantern", "chain", "fence", "door", "sign", "banner", "carpet",
                "campfire", "cauldron", "anvil", "ladder", "bars", "torch", "rod", "leaves", "water", "lava",
                "short_grass", "fern", "poppy", "dandelion", "cornflower", "oxeye", "tulip", "allium",
                "cogwheel", "shaft", "bell", "grindstone", "button", "azalea", "bush", "_wall", "flower",
                "candle", "pot", "coral", "head")


def _name(state: str) -> str:
    return state.split("[", 1)[0].split(":", 1)[1]


def emission(state: str) -> int:
    n = _name(state)
    if n == "soul_lantern":
        return 10
    if n.endswith("lantern") or n in ("glowstone", "shroomlight", "lava_cauldron", "lava") or n.endswith("froglight"):
        return 15
    if n == "campfire" and "lit=false" not in state:
        return 15
    if n in ("torch", "wall_torch", "end_rod"):
        return 14
    if n.endswith("copper_bulb") and "lit=true" in state:
        return 4 if "oxidized" in n else 8 if "weathered" in n else 12 if "exposed" in n else 15
    if n.endswith("candle") and "lit=true" in state:
        return 3 * int(state.split("candles=", 1)[1][0]) if "candles=" in state else 3
    return 0


def see_through(state: str) -> bool:
    n = _name(state)
    return any(k in n for k in _SEE_THROUGH)


def spawn_floor(state: str) -> bool:
    """Whether a monster could stand on this block (a full, solid, non-glass cube)."""
    n = _name(state)
    return not see_through(state) and not any(k in n for k in ("slab", "stairs", "glass", "ice", "hay"))


def block_light(blocks: dict, size) -> bytearray:
    sx, sy, sz = size
    light = bytearray(sx * sy * sz)
    clear = bytearray(sx * sy * sz)  # 1 = light passes; positions not in `blocks` count as solid
    queue = []
    for (x, y, z), state in blocks.items():
        i = (y * sz + z) * sx + x
        if see_through(state):
            clear[i] = 1
        e = emission(state)
        if e:
            light[i] = e
            queue.append(i)
    stride_y, stride_z = sz * sx, sx
    # Bucketed BFS: process level 15 first so every cell gets its maximum on the first visit.
    buckets = [[] for _ in range(16)]
    for i in queue:
        buckets[light[i]].append(i)
    for level in range(15, 1, -1):
        for i in buckets[level]:
            if light[i] != level:
                continue
            x = i % sx
            z = (i // sx) % sz
            y = i // stride_y
            nxt = level - 1
            for j, ok in ((i - 1, x > 0), (i + 1, x < sx - 1), (i - stride_z, z > 0), (i + stride_z, z < sz - 1),
                          (i - stride_y, y > 0), (i + stride_y, y < sy - 1)):
                if ok and clear[j] and light[j] < nxt:
                    light[j] = nxt
                    buckets[nxt].append(j)
    return light


def dark_spots(blocks: dict, size, candidates) -> list:
    """Air positions (from `candidates`) a monster could spawn in: solid floor below, block light 0."""
    sx, sy, sz = size
    light = block_light(blocks, size)
    out = []
    for (x, y, z) in candidates:
        if y == 0 or blocks.get((x, y, z)) != AIR:
            continue
        below = blocks.get((x, y - 1, z))
        if below is None or not spawn_floor(below):
            continue
        if light[(y * sz + z) * sx + x] == 0:
            out.append((x, y, z))
    return sorted(out, key=lambda p: (p[1], p[2], p[0]))
