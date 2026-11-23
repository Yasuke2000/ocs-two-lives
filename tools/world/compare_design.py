#!/usr/bin/env python3
"""Does the generated world match the design? Reads the live terrain through the build bridge and compares it with the
own-world rasters, site by site (stdlib only).

    python -I tools/world/compare_design.py [--rasters world/build] [--sites tempest,dwargon,...] [--margin 96]
                                            [--box X1 Z1 X2 Z2 ...] [--out world/build/compare] [--no-load]

Needs a running server with the bridge on (docs/dev/build-bridge.md; TTL_BRIDGE_URL / TTL_BRIDGE_TOKEN or
TTL_LOCAL_DIR) whose config/ttl/world/ holds the same rasters. Chunks that do not exist yet are generated (--no-load
skips them). Per window it reports:

  plate   plated sites: share of columns within +-1 of the site's walking level (inside 0.8 r), worst deviation
          (village sites carry a Tensura village structure: reported, not gated)
  ground  dry land outside plates: median and 90th percentile of |generated - designed| ground height, and the bias
          (vanilla noise adds detail on purpose: a few blocks of median difference is the design working)
  water   designed lakes/rivers: share of columns whose surface is at the designed water level (+-1)
  biome   share of columns whose generated surface biome is the designed one

and writes <out>/<window>.png (designed | generated | difference: blue lower, red higher, white within 2 blocks)
plus <out>/report.json. Exit 1 when a plate is off (< 90 % within +-1) or a site's ground median is above 6 blocks.
"""
import argparse
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "tools" / "forge"))
import pngcodec  # noqa: E402

PLATE_OK = 0.90
GROUND_MEDIAN_MAX = 6.0


class Design:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.idx = json.loads((self.folder / "index.json").read_text(encoding="utf-8"))
        f = self.idx["files"]
        self.w, self.h, self.H, _ = pngcodec.read_png(self.folder / f["height"]["file"])
        _, _, self.water, _ = pngcodec.read_png(self.folder / f["water"]["file"])
        _, _, self.biome, _ = pngcodec.read_png(self.folder / f["biome"]["file"])
        self.scale, self.offset = f["height"]["scale"], f["height"]["offset"]
        self.biomes = f["biome"]["biomes"]
        self.x0, self.z0 = self.idx["box"]["x0"], self.idx["box"]["z0"]
        self.px = self.idx["pixel"]["blocks"]

    def g(self, x, z):
        i, j = int((x - self.x0) // self.px), int((z - self.z0) // self.px)
        if 0 <= i < self.w and 0 <= j < self.h:
            return j * self.w + i
        return None

    def ground(self, x, z):
        """Designed H (first air above the ground) at a block, bilinear like the generator samples."""
        u, v = (x + 0.5 - self.x0) / self.px - 0.5, (z + 0.5 - self.z0) / self.px - 0.5
        i, j = math.floor(u), math.floor(v)
        tu, tv = u - i, v - j

        def at(a, b):
            a, b = min(max(a, 0), self.w - 1), min(max(b, 0), self.h - 1)
            return self.H[b * self.w + a] / self.scale - self.offset

        top = at(i, j) + (at(i + 1, j) - at(i, j)) * tu
        bot = at(i, j + 1) + (at(i + 1, j + 1) - at(i, j + 1)) * tu
        return top + (bot - top) * tv

    def water_level(self, x, z):
        g = self.g(x, z)
        v = self.water[g] if g is not None else 0
        return v - 64 if v else None

    def biome_at(self, x, z):
        g = self.g(x, z)
        return self.biomes[self.biome[g]] if g is not None else "#ocean"


def _runs(rle):
    out = []
    for n, v in rle:
        out.extend([v] * n)
    return out


def compare_window(bridge, design, name, x1, z1, x2, z2, plate=None, load=True, out=None):
    hm = bridge.get("region", dim="minecraft:overworld", mode="heightmap", surface="terrain",
                    x1=x1, z1=z1, x2=x2, z2=z2, load="true" if load else "false")
    w, l = hm["size"]
    heights = hm["heights"]
    biomes = _runs(hm["biomes_rle"])
    bpal = hm["biome_palette"]
    plate_dev, ground_diff, water_ok, water_n, biome_ok, biome_n = [], [], 0, 0, 0, 0
    des, gen = [None] * (w * l), [None] * (w * l)
    for k in range(w * l):
        x, z = x1 + k % w, z1 + k // w
        y = heights[k]
        if y is None:
            continue
        top = y + 1  # first air above the generated ground (the design's convention)
        d = design.ground(x, z)
        wl = design.water_level(x, z)
        dbiome = design.biome_at(x, z)
        if dbiome == "#ocean":
            continue
        des[k], gen[k] = (wl if wl is not None else d), top
        if plate and math.hypot(x + 0.5 - plate["x"], z + 0.5 - plate["z"]) <= 0.8 * plate["r"] and wl is None:
            plate_dev.append(top - plate["y"])
            continue
        if wl is not None:
            water_n += 1
            water_ok += abs(top - wl) <= 1
            continue
        ground_diff.append(top - d)
        if biomes[k] >= 0:
            biome_n += 1
            biome_ok += bpal[biomes[k]] == dbiome
    res = {"window": name, "from": [x1, z1], "to": [x2, z2]}
    if plate_dev:
        within = sum(1 for v in plate_dev if abs(v) <= 1) / len(plate_dev)
        res["plate"] = {"y": plate["y"], "r": plate["r"], "within_1": round(within, 3),
                        "worst": max(plate_dev, key=abs), "columns": len(plate_dev)}
    if ground_diff:
        a = sorted(abs(v) for v in ground_diff)
        res["ground"] = {"median_abs": statistics.median(a), "p90_abs": a[int(0.9 * (len(a) - 1))],
                         "bias": round(statistics.fmean(ground_diff), 1), "columns": len(a)}
    if water_n:
        res["water_at_level"] = round(water_ok / water_n, 3)
    if biome_n:
        res["biome_match"] = round(biome_ok / biome_n, 3)
    # A village site is the clearing a Tensura village structure generates on: its huts lift the surface, so its plate
    # is reported, not gated (the noise itself is checked flat by /ttlsite check).
    gate_plate = not (plate and plate.get("kind") == "village")
    if "plate" in res and not gate_plate:
        res["plate"]["note"] = "village: structure on the plate, not gated"
    res["ok"] = ((not gate_plate or res.get("plate", {}).get("within_1", 1.0) >= PLATE_OK)
                 and res.get("ground", {}).get("median_abs", 0.0) <= GROUND_MEDIAN_MAX)
    if out:
        _picture(Path(out) / f"{name}.png", w, l, des, gen)
        res["image"] = str((Path(out) / f"{name}.png").relative_to(ROOT)) if Path(out).is_relative_to(ROOT) else str(Path(out) / f"{name}.png")
    return res


def _shade(hs, w, l, k):
    x = k % w
    a = hs[k - 1] if x > 0 and hs[k - 1] is not None else hs[k]
    b = hs[k - w] if k >= w and hs[k - w] is not None else hs[k]
    return max(0.5, min(1.4, 1.0 + 0.1 * ((hs[k] - a) + (hs[k] - b))))


def _picture(path, w, l, des, gen):
    gap = 4
    W = 3 * w + 2 * gap
    rgb = bytearray(b"\x20" * (W * l * 3))
    vals = [v for v in des + gen if v is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0, 1)
    for k in range(w * l):
        x, z = k % w, k // w
        for panel, hs in ((0, des), (1, gen)):
            if hs[k] is None:
                c = (30, 60, 130)
            else:
                t = (hs[k] - lo) / max(1, hi - lo)
                base = (int(60 + 150 * t), int(130 + 90 * t), int(60 + 120 * t))
                s = _shade(hs, w, l, k)
                c = tuple(max(0, min(255, int(v * s))) for v in base)
            o = (z * W + panel * (w + gap) + x) * 3
            rgb[o:o + 3] = bytes(c)
        if des[k] is None or gen[k] is None:
            c = (30, 60, 130)
        else:
            d = gen[k] - des[k]
            if abs(d) <= 2:
                c = (245, 245, 245)
            elif d > 0:
                f = min(1.0, (d - 2) / 20)
                c = (255, int(220 - 180 * f), int(220 - 180 * f))
            else:
                f = min(1.0, (-d - 2) / 20)
                c = (int(220 - 180 * f), int(220 - 180 * f), 255)
        o = (z * W + 2 * (w + gap) + x) * 3
        rgb[o:o + 3] = bytes(c)
    path.parent.mkdir(parents=True, exist_ok=True)
    pngcodec.write_png(path, W, l, bytes(rgb), rgb=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="compare the generated world with the own-world design rasters")
    ap.add_argument("--rasters", default=str(ROOT / "world" / "build"))
    ap.add_argument("--sites", default="", help="comma-separated site ids (default: every plated site)")
    ap.add_argument("--margin", type=int, default=96, help="blocks around a site's r")
    ap.add_argument("--box", nargs=4, type=int, action="append", metavar=("X1", "Z1", "X2", "Z2"), default=[])
    ap.add_argument("--out", default=str(ROOT / "world" / "build" / "compare"))
    ap.add_argument("--no-load", action="store_true")
    args = ap.parse_args(argv)
    import client
    bridge = client.Bridge(timeout=600)
    design = Design(args.rasters)
    sites = design.idx["sites"]
    wanted = [s.strip() for s in args.sites.split(",") if s.strip()]
    if wanted:
        sites = [s for s in sites if s["id"] in wanted]
        missing = set(wanted) - {s["id"] for s in sites}
        if missing:
            print("unknown site ids: " + ", ".join(sorted(missing)), file=sys.stderr)
            return 2
    elif not args.box:
        sites = [s for s in sites if s.get("plated")]
    results = []
    for s in sites:
        r = int(s["r"]) + args.margin
        res = compare_window(bridge, design, s["id"], int(s["x"]) - r, int(s["z"]) - r, int(s["x"]) + r, int(s["z"]) + r,
                             plate=s if s.get("plated") and s.get("kind") != "carve" else None,
                             load=not args.no_load, out=args.out)
        results.append(res)
        _line(res)
    for k, (x1, z1, x2, z2) in enumerate(args.box):
        res = compare_window(bridge, design, f"box{k}_{x1}_{z1}", x1, z1, x2, z2, load=not args.no_load, out=args.out)
        results.append(res)
        _line(res)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "report.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    bad = [r["window"] for r in results if not r["ok"]]
    print(f"{len(results) - len(bad)}/{len(results)} windows ok" + (": off " + ", ".join(bad) if bad else ""))
    return 1 if bad else 0


def _line(r):
    parts = [f"{r['window']:<24}"]
    if "plate" in r:
        p = r["plate"]
        parts.append(f"plate y{p['y']} {100 * p['within_1']:.0f}% within 1 (worst {p['worst']:+d})" + (" [village]" if "note" in p else ""))
    if "ground" in r:
        g = r["ground"]
        parts.append(f"ground median {g['median_abs']:.0f} p90 {g['p90_abs']:.0f} bias {g['bias']:+.1f}")
    if "water_at_level" in r:
        parts.append(f"water {100 * r['water_at_level']:.0f}% at level")
    if "biome_match" in r:
        parts.append(f"biome {100 * r['biome_match']:.0f}%")
    parts.append("ok" if r["ok"] else "OFF")
    print("  ".join(parts), flush=True)


if __name__ == "__main__":
    sys.exit(main())
