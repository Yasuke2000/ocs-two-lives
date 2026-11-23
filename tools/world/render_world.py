#!/usr/bin/env python3
"""Render the generated own world as one top-down map, read through the build bridge (tools/forge/client.py).

Usage: render_world.py [--step 4] [--tile 1024] [--box content|design|x0,z0,x1,z1] [--load] [--out world/build/render]

Reads `region mode=heightmap` tile by tile on a running server with the bridge on (docs/dev/build-bridge.md), keeps one
column in every --step x --step square and writes world.png (hill-shaded surface blocks, sites outlined in red) plus
world_design.png: the design height raster of the same box beside it, to hold the two against each other. Chunks that
were never generated stay black unless --load is given (then the bridge generates them on the server thread: slow, use
the pregeneration first, docs/own-world-local.md step 3).
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools" / "forge"))
sys.path.insert(1, str(ROOT / "tools"))
import client  # noqa: E402
from blueprint import _color, _write_png  # noqa: E402
import pngcodec  # noqa: E402

WORLD = ROOT / "pack" / "config" / "ttl" / "world"
WATER = (48, 86, 180)


def pick_box(spec, meta):
    b = meta["box"]
    if spec == "design":
        return b["x0"], b["z0"], b["x1"], b["z1"]
    if spec == "content":
        x0, z0, x1, z1 = b["content"]
        return x0 - 64, z0 - 64, x1 + 64, z1 + 64
    x0, z0, x1, z1 = (int(v) for v in spec.split(","))
    return x0, z0, x1, z1


def read_tiles(bridge, box, step, tile, load):
    x0, z0, x1, z1 = box
    W, H = (x1 - x0) // step, (z1 - z0) // step
    heights = [None] * (W * H)
    tops = [None] * (W * H)
    tiles = [(tx, tz) for tz in range(z0, z1, tile) for tx in range(x0, x1, tile)]
    t0 = time.time()
    for n, (tx, tz) in enumerate(tiles, 1):
        bx1, bz1 = min(tx + tile, x1) - 1, min(tz + tile, z1) - 1
        q = {"dim": "minecraft:overworld", "x1": tx, "y1": -64, "z1": tz, "x2": bx1, "y2": 319, "z2": bz1,
             "mode": "heightmap"}
        if not load:
            q["load"] = "false"
        d = bridge.get("region", **q)
        w, l = d["size"]
        blocks = []
        for count, value in d["blocks_rle"]:
            blocks.extend([value] * count)
        pal = d["block_palette"]
        for z in range(0, l):
            wz = tz + z
            if (wz - z0) % step:
                continue
            for x in range(0, w):
                wx = tx + x
                if (wx - x0) % step:
                    continue
                u, v = (wx - x0) // step, (wz - z0) // step
                if u >= W or v >= H:
                    continue
                i = z * w + x
                if d["heights"][i] is None or blocks[i] < 0:
                    continue
                heights[v * W + u] = d["heights"][i]
                tops[v * W + u] = pal[blocks[i]]
        print(f"tile {n}/{len(tiles)} ({tx},{tz}) {time.time() - t0:.0f}s", flush=True)
    return W, H, heights, tops


def shade_image(W, H, heights, tops, step):
    buf = bytearray(W * H * 4)
    cache = {}
    for v in range(H):
        for u in range(W):
            i = v * W + u
            h = heights[i]
            if h is None:
                rgb = (0, 0, 0)
            else:
                top = tops[i]
                if top not in cache:
                    cache[top] = WATER if "water" in top else _color(top)
                rgb = cache[top]
                west = heights[i - 1] if u and heights[i - 1] is not None else h
                north = heights[i - W] if v and heights[i - W] is not None else h
                f = max(0.55, min(1.4, 1.0 + 0.5 * ((h - west) + (h - north)) / step))
                rgb = tuple(max(0, min(255, int(c * f))) for c in rgb)
            buf[i * 4:i * 4 + 4] = bytes(rgb) + b"\xff"
    return buf


def outline_sites(buf, W, H, box, step):
    x0, z0 = box[0], box[1]
    sites = json.loads((WORLD / "sites.json").read_text(encoding="utf-8"))["sites"]
    for s in sites:
        cx, cz = s["centre"]
        r = s["radius"] / step
        cu, cv = (cx - x0) / step, (cz - z0) / step
        for k in range(360):
            u = int(cu + r * math.cos(math.radians(k)))
            v = int(cv + r * math.sin(math.radians(k)))
            if 0 <= u < W and 0 <= v < H:
                buf[(v * W + u) * 4:(v * W + u) * 4 + 4] = b"\xe0\x20\x20\xff"
    return len(sites)


def design_image(meta, box, step):
    """The design height raster (4 blocks a pixel) over the same box, grey by height, sea blue."""
    w, h, px = pngcodec.read_png(WORLD / "height.png")[:3]
    b = meta["box"]
    sea = meta["sea_level"]
    x0, z0, x1, z1 = box
    W, H = (x1 - x0) // step, (z1 - z0) // step
    buf = bytearray(W * H * 4)
    for v in range(H):
        for u in range(W):
            wx, wz = x0 + u * step, z0 + v * step
            pu, pv = (wx - b["x0"]) // 4, (wz - b["z0"]) // 4
            if 0 <= pu < w and 0 <= pv < h:
                hgt = px[pv * w + pu] / 16 - 64
                if hgt < sea:
                    rgb = WATER
                else:
                    g = max(40, min(250, int(90 + (hgt - sea) * 1.6)))
                    rgb = (g - 20, g, g - 40)
            else:
                rgb = (0, 0, 0)
            buf[(v * W + u) * 4:(v * W + u) * 4 + 4] = bytes(rgb) + b"\xff"
    return W, H, buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, default=4)
    ap.add_argument("--tile", type=int, default=1024)
    ap.add_argument("--box", default="content")
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "world" / "build" / "render"))
    a = ap.parse_args()
    meta = json.loads((WORLD / "index.json").read_text(encoding="utf-8"))
    box = pick_box(a.box, meta)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    W, H, heights, tops = read_tiles(client.Bridge(timeout=600), box, a.step, a.tile, a.load)
    buf = shade_image(W, H, heights, tops, a.step)
    n = outline_sites(buf, W, H, box, a.step)
    _write_png(out / "world.png", W, H, buf)
    dw, dh, dbuf = design_image(meta, box, a.step)
    _write_png(out / "world_design.png", dw, dh, dbuf)
    missing = sum(1 for h in heights if h is None)
    print(f"box {box}, {W}x{H} px at {a.step} blocks/px, {n} sites outlined, "
          f"{100 * missing / len(heights):.1f}% not generated -> {out / 'world.png'} and world_design.png")


if __name__ == "__main__":
    main()
