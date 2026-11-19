#!/usr/bin/env python3
"""Render the own-world rasters (svg2rasters output) as one review picture (stdlib only).

    python -I tools/world/raster_preview.py [pack/config/ttl/world] [--out world/rasters_preview.png] [--scale N]

Hillshade of height.png tinted by biome.png, designed water in blue, road surface dark, bridges orange, the
structure exclusion mask hatched, site radii outlined. One output pixel = `scale` raster pixels (default: 1 for small
maps, 2 above 1,500 px wide). This renders what the generator will be fed; tools/world/map_check.py renders the SVG
itself (world/preview.png) for the map author.
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pngcodec  # noqa: E402

ROOT = HERE.parent.parent
DEFAULT_IN = ROOT / "pack" / "config" / "ttl" / "world"
DEFAULT_OUT = ROOT / "world" / "rasters_preview.png"


def render(src, out, scale=None):
    src = Path(src)
    idx = json.loads((src / "index.json").read_text(encoding="utf-8"))
    f = idx["files"]
    w, h, height, _ = pngcodec.read_png(src / f["height"]["file"])
    _, _, biome, pal = pngcodec.read_png(src / f["biome"]["file"])
    _, _, water, _ = pngcodec.read_png(src / f["water"]["file"])
    _, _, road, _ = pngcodec.read_png(src / f["road"]["file"])
    _, _, excl, _ = pngcodec.read_png(src / f["exclude"]["file"])
    sc, off = f["height"]["scale"], f["height"]["offset"]
    H = [v / sc - off for v in height]
    if scale is None:
        scale = 1 if w <= 1500 else 2
    ow, oh = w // scale, h // scale
    rgb = bytearray(ow * oh * 3)
    for j in range(oh):
        for i in range(ow):
            g = (j * scale) * w + i * scale
            a = H[g - 1] if i * scale > 0 else H[g]
            b = H[g - w] if j * scale > 0 else H[g]
            shade = max(0.45, min(1.35, 1.0 + ((a - H[g]) + (b - H[g])) * 0.08))
            c = pal[biome[g]] if pal and biome[g] < len(pal) else (128, 128, 128)
            if water[g]:
                c = (50, 100, 210)
            if road[g] in (2, 3):
                c = (70, 55, 40)
            elif road[g] in (4, 5):
                c = (230, 140, 40)
            elif road[g] == 1:
                c = tuple(int(v * 0.8 + 40) for v in c)
            if excl[g] and (i + j) % 6 == 0:
                c = (240, 60, 60) if excl[g] & 4 else (250, 220, 60)
            k = (j * ow + i) * 3
            sh = 1.0 if water[g] or road[g] else shade
            rgb[k:k + 3] = bytes(max(0, min(255, int(v * sh))) for v in c)
    x0, z0 = idx["box"]["x0"], idx["box"]["z0"]
    blocks = idx["pixel"]["blocks"] * scale
    for s in idx["sites"]:
        cx, cz, r = (s["x"] - x0) / blocks, (s["z"] - z0) / blocks, s["r"] / blocks
        n = max(24, int(2 * math.pi * r))
        for t in range(n):
            px = int(cx + r * math.cos(2 * math.pi * t / n))
            pz = int(cz + r * math.sin(2 * math.pi * t / n))
            if 0 <= px < ow and 0 <= pz < oh:
                k = (pz * ow + px) * 3
                rgb[k:k + 3] = b"\xff\xff\xff" if s.get("plated") else b"\x10\x10\x10"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    pngcodec.write_png(out, ow, oh, rgb, rgb=True)
    return ow, oh


def main(argv=None):
    ap = argparse.ArgumentParser(description="render the own-world rasters for review")
    ap.add_argument("src", nargs="?", default=str(DEFAULT_IN))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--scale", type=int, default=None)
    args = ap.parse_args(argv)
    ow, oh = render(args.src, args.out, args.scale)
    print("wrote %s (%d x %d)" % (args.out, ow, oh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
