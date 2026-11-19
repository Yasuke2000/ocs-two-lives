#!/usr/bin/env python3
"""Own world: world/map.svg -> checked map -> rasters -> preview -> sites -> anchors, in one go (WP-W1; stdlib only).

    python -I tools/world/build.py                      staging build into world/build/ (nothing live changes)
    python -I tools/world/build.py --apply              the switch: rasters into pack/config/ttl/world/, the
                                                        anchors' x/z/y into design/data/anchors.toml (and the canon
                                                        landmarks' `at` in canon_regions.json)
    ... [--svg world/map.svg] [--seed N] [--skip-check] [--sea-margin 1200] [--region 512]

Steps (design/architecture/own-world.md §5.1, "Local-first"):
  1. tools/world/map_check.py <svg>, when that tool exists (WP W-check); its errors stop the build (--skip-check
     carries on, for a quick look at a map that is not done yet);
  2. tools/world/svg2rasters.py: height, rugged, water, road, biome, site and exclusion rasters + index.json,
     sites.json, roads.json, canon_map.txt;
  3. tools/world/raster_preview.py: <out>/preview.png, the rasters as the generator will see them;
  4. tools/world/sites_from_builds.py: world/sites.toml with the sites' kinds, radii and walking levels;
  5. anchors: x, z (the SVG site centres; relative anchors keep <of> + dx/dz) and y (the walking level: the plate's
     ground, a pin's surface) for every anchor the SVG places. Every other line of anchors.toml is kept as it is.
     Without --apply the result goes to <out>/anchors.toml for review.

Why staging by default: the mod switches to the own world when pack/config/ttl/world/ holds rasters (WP-W2 falls
back to today's world without them), and anchors.toml positions every live build, so both move together, on purpose,
with --apply. Still to move by hand at the switch (the build lists them): life/dwargon.js GATE/BASE and the
tempest.js fallback literal (WP-W7), design/builds ground = "fixed" + y (WP-W5 data is in world/sites.toml).
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import raster_preview  # noqa: E402
import sites_from_builds as sfb  # noqa: E402
import svg2rasters as s2r  # noqa: E402

ROOT = HERE.parent.parent
SVG = ROOT / "world" / "map.svg"
STAGING = ROOT / "world" / "build"
LIVE = ROOT / "pack" / "config" / "ttl" / "world"
ANCHORS = ROOT / "design" / "data" / "anchors.toml"
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
MAP_CHECK = HERE / "map_check.py"


def anchor_coords(index, anchors):
    """{anchor id: (x, z, y)} from svg2rasters' index.json; relative anchors (of/dx/dz) follow their parent."""
    sites = {s["id"]: s for s in index["sites"]}
    out = {}
    for aid, s in sites.items():
        a = anchors.get(aid, {})
        x, z = s["x"], s["z"]
        if a.get("of") in sites:
            p = sites[a["of"]]
            x, z = p["x"] + a.get("dx", 0), p["z"] + a.get("dz", 0)
        out[aid] = (int(x), int(z), int(s["y"]))
    return out


TABLE = re.compile(r"^\[([a-z0-9_]+)\]\s*$")
KEY = re.compile(r"^(x|y|z)\s*=\s*(-?\d+)\s*$")


def update_anchors(text, coords):
    """anchors.toml text with x/z/y of the tables in coords rewritten (y inserted after z when missing); every other
    line (names, kinds, notes, keepouts, comments) unchanged."""
    lines = text.splitlines(keepends=True)
    has_y, cur = set(), None
    for line in lines:
        m = TABLE.match(line)
        if m or line.startswith("["):
            cur = m.group(1) if m else None
        elif cur and KEY.match(line) and KEY.match(line).group(1) == "y":
            has_y.add(cur)
    out, cur = [], None
    for line in lines:
        m = TABLE.match(line)
        if m or line.startswith("["):
            cur = m.group(1) if m else None
            out.append(line)
            continue
        k = KEY.match(line)
        if cur in coords and k:
            x, z, y = coords[cur]
            key = k.group(1)
            eol = "\n" if line.endswith("\n") else ""
            out.append("%s = %d%s" % (key, {"x": x, "z": z, "y": y}[key], eol))
            if key == "z" and cur not in has_y:
                out.append("y = %d\n" % y)
            continue
        out.append(line)
    return "".join(out)


def update_canon(text, anchors, coords):
    """canon_regions.json text with each landmark `at` that an anchor positions (anchor `canon` = landmark name)
    moved to the anchor's new x/z (gen_data requires them equal)."""
    for aid, a in anchors.items():
        name = a.get("canon")
        if not name or aid not in coords:
            continue
        x, z, _ = coords[aid]
        pat = re.compile(r'("name":\s*%s,\s*(?:"[a-z_]+":\s*"[^"]*",\s*)*"at":\s*)\[-?\d+,\s*-?\d+\]'
                         % re.escape(json.dumps(name, ensure_ascii=False)))
        text, n = pat.subn(lambda m: "%s[%d, %d]" % (m.group(1), x, z), text, count=1)
        if not n:
            print("warn: canon_regions.json has no landmark %r with an `at` to move" % name, file=sys.stderr)
    return text


def run_map_check(svg):
    if not MAP_CHECK.is_file():
        print("map_check: tools/world/map_check.py not present yet, skipped")
        return 0
    return subprocess.call([sys.executable, "-I", str(MAP_CHECK), str(svg)])


def main(argv=None):
    ap = argparse.ArgumentParser(description="own world: SVG -> check -> rasters -> preview -> sites -> anchors")
    ap.add_argument("--svg", default=str(SVG))
    ap.add_argument("--out", default=None, help="raster dir (default world/build/, with --apply pack/config/ttl/world/)")
    ap.add_argument("--apply", action="store_true", help="the switch: live raster dir + anchors.toml + canon at")
    ap.add_argument("--skip-check", action="store_true")
    ap.add_argument("--seed", type=int, default=s2r.SEED)
    ap.add_argument("--sea-margin", type=int, default=s2r.SEA_MARGIN)
    ap.add_argument("--region", type=int, default=s2r.REGION)
    ap.add_argument("--sites", default=str(sfb.SITES_TOML))
    args = ap.parse_args(argv)
    svg = Path(args.svg)
    if not svg.is_file():
        print("build: %s does not exist (WP-W0 draws it; tools/world/map_check.py has the starter)" % svg,
              file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else (LIVE if args.apply else STAGING)
    t0 = time.time()

    rc = run_map_check(svg)
    if rc and not args.skip_check:
        print("build: map_check failed (exit %d); fix the map or pass --skip-check for a look" % rc, file=sys.stderr)
        return rc

    text = svg.read_text(encoding="utf-8")
    try:
        world = s2r.build(text, s2r.Options(seed=args.seed, sea_margin=args.sea_margin, region=args.region),
                          args.sites)
    except s2r.MapError as e:
        print("svg2rasters: %s" % e, file=sys.stderr)
        return 1
    s2r.write_outputs(world, out)
    for w in world.warnings:
        print("warn: " + w, file=sys.stderr)
    print("rasters: %s (%d x %d px, box %d..%d x %d..%d)" % (out, world.w, world.h, world.x0, world.x0 + world.w * 4,
                                                           world.z0, world.z0 + world.h * 4))

    preview = out / "preview.png" if not args.apply else ROOT / "world" / "rasters_preview.png"
    raster_preview.render(out, preview)
    print("preview: %s" % preview)

    src = sfb.Sources()
    sites, reqs = sfb.derive(src, sfb.svg_sites(svg), sfb.raster_grounds(out), sfb.load_existing(args.sites))
    Path(args.sites).write_text(sfb.dumps(sites, sfb.load_existing(args.sites)), encoding="utf-8", newline="\n")
    bad = sfb.problems(sites, reqs)
    for b in bad:
        print("error: sites: " + b, file=sys.stderr)
    print("sites: %s" % args.sites)

    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    coords = anchor_coords(index, src.anchors)
    missing = [a for a in src.anchors if a not in coords]
    new = update_anchors(ANCHORS.read_text(encoding="utf-8"), coords)
    target = ANCHORS if args.apply else out / "anchors.toml"
    target.write_text(new, encoding="utf-8", newline="\n")
    print("anchors: %s (%d placed from the map%s)" % (target, len(coords),
                                                       ", not on the map: " + ", ".join(missing) if missing else ""))
    if args.apply:
        CANON.write_text(update_canon(CANON.read_text(encoding="utf-8"), src.anchors, coords), encoding="utf-8",
                         newline="\n")
        print("canon_regions.json: landmark `at` moved with their anchors")
        print("still by hand (WP-W7): life/dwargon.js GATE/BASE, life/tempest.js fallback, design/builds ground/y "
              "from world/sites.toml; then python tools/gen_data.py")
    print("done in %.1f s" % (time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
