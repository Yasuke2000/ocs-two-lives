#!/usr/bin/env python3
"""Build footprints -> the site each anchor needs -> world/sites.toml (own world, WP-W5; stdlib only).

    python -I tools/world/sites_from_builds.py            rewrite world/sites.toml
    python -I tools/world/sites_from_builds.py --check    exit 1 when world/sites.toml is stale or a build misfits
    ... [--svg world/map.svg] [--rasters pack/config/ttl/world] [--out FILE]

design/architecture/own-world.md §3.3 and §4.2: a blueprint's footprint drives its site. For every anchor of
design/data/anchors.toml this derives from the footprint (generated/builds.js `TtlBuildFootprints`, the Tempest and
Dwargon footprints of their own generators, landmarks.toml `reach`, arrival.toml `safe_radius`):

    min_r   the smallest site radius the build fits: half the box diagonal + 12, and at least the half diagonal of the
            plate (box + 2 x margin); a landmark: its jigsaw `reach` + 8; the arrival: `safe_radius` + 12
    plate   the flat plate (x, z blocks) = the box + 2 x max(margin, repair_margin)
    height  blocks of the build above its walking level (Dragon's Nest: y + height < 320)
    roof    carve sites: the highest roof the massif must cover, in blocks above the walking level; svg2rasters.py
            raises the terrain over every roof column to y + roof_rel + cover
    cover   carve sites: blocks of rock over every roof column (`min_cover`, default 6, the owner's floor)
    ground  "fixed" for builds (what design/builds/<name>.toml switches to at the cut-over: no survey, no fit)
    y       the walking level = the plate's height: the site's ground from the rasters (svg2rasters' index.json), else
            the first-pass value of design §4.1 (Tempest 70, Dwargon's gate 146, Dragon's Nest 272), else absent

`site` and `r` come from the SVG `sites` layer when there is a map (it is the source), r raised to min_r when the circle
is drawn smaller (design §4.2: the footprint drives the site; `svg_r` keeps the drawn radius and the run warns); without
a map they are the first-pass assignment of design §4.1, r raised to min_r likewise. Keys a person sets in world/sites.toml and the generator
keeps: plate_y (the design's `ground` override of the plate level; renamed because `ground` is the build's placement
mode here), fade, biome, facing, min_cover, surface, clear_above, notes. Pins and spots only pin coordinates (r 8, no
plate). Nothing in the game reads sites.toml yet: it feeds svg2rasters.py and, at the switch, design/builds.
"""
import argparse
import json
import math
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ANCHORS = ROOT / "design" / "data" / "anchors.toml"
BUILDS = ROOT / "design" / "builds"
LANDMARKS = ROOT / "design" / "data" / "landmarks.toml"
ARRIVAL = ROOT / "design" / "data" / "arrival.toml"
GENERATED = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated"
SITES_TOML = ROOT / "world" / "sites.toml"
SVG = ROOT / "world" / "map.svg"
RASTERS = ROOT / "pack" / "config" / "ttl" / "world"

SITE_KINDS = ("clearing", "plateau", "carve", "lakeside", "coast", "village")
PLATED = ("settlement", "build", "landmark", "arrival")   # anchor kinds that get a plate; pins and spots do not
MIN_COVER = 6
ROOF_MIN = 3            # a column whose top is at least this far above the walking level has a roof to cover
PIN_R = 8
TEMPEST_GROWTH = 192    # Tempest's growth square (town, city) is the site, not the village (design §3.3)
BUILD_LIMIT = 320
OVERRIDE_KEYS = ("plate_y", "fade", "biome", "facing", "min_cover", "surface", "clear_above", "notes")
FACINGS = ("north", "south", "east", "west", "auto")

# Design §4.1 (first pass, carried by the ChatGPT brief): kind, r, biome inside r and other overrides. Where §3.3's
# examples are more specific than §4.1's grouped rows they win: Ballachia lakeside, Amrita carve, Nasca plateau.
FIRST_PASS = {
    "tempest": dict(site="clearing", r=110, biome="minecraft:plains", plate_y=70),
    "dwargon": dict(site="carve", plate_y=146, facing="south", min_cover=MIN_COVER),
    "arrival": dict(site="clearing", r=60, biome="minecraft:plains"),
    "sealed_cave": dict(site="carve", facing="south", min_cover=MIN_COVER),
    "goblin_village": dict(site="village", r=64, biome="minecraft:plains"),
    "spirit_gate": dict(site="lakeside", r=56, biome="minecraft:plains", facing="auto"),
    "treyni_grove": dict(site="village", r=64),
    "treyni_shrine": dict(site="clearing", r=48, biome="minecraft:meadow"),
    "ogre_village_ruin": dict(site="village", r=48, biome="minecraft:windswept_forest"),
    "dwarf_village": dict(site="village", r=90, biome="minecraft:meadow"),
    "dwarven_arena": dict(site="clearing", biome="minecraft:meadow"),
    "dragons_nest": dict(site="clearing", plate_y=272, biome="minecraft:stony_peaks"),
    "lizardmen_village": dict(site="lakeside", surface="water", biome="minecraft:swamp", facing="auto"),
    "lizardmen_caverns": dict(site="carve", facing="auto", min_cover=MIN_COVER, biome="minecraft:swamp"),
    "orc_camp": dict(site="village", biome="minecraft:plains"),
    "blumund": dict(site="clearing", r=110), "englassia": dict(site="clearing", r=110),
    "marris": dict(site="clearing", r=110), "forgotten_dragon_city": dict(site="clearing", r=110),
    "ballachia": dict(site="lakeside", r=90, facing="auto"),
    "amrita": dict(site="carve", facing="south", min_cover=MIN_COVER),
    "nasca": dict(site="plateau", r=90),
    "lubelius": dict(site="plateau"), "sacred_mountain": dict(site="plateau"),
    "coleus": dict(site="clearing", biome="minecraft:desert"),
    "heaven_tower": dict(site="clearing", biome="minecraft:desert"),
    "morgdahl": dict(site="lakeside", facing="auto"), "raja": dict(site="lakeside", facing="auto"),
    "nostraille": dict(site="clearing"),
    "ulgr_nature_park": dict(site="plateau"), "elmine": dict(site="clearing"), "jia": dict(site="plateau"),
    "laura": dict(site="clearing"), "clayman_castle": dict(site="clearing"),
    "great_holy_mountain": dict(site="clearing"),
    "el_dorado": dict(site="coast", facing="auto"), "siltrosso": dict(site="coast", facing="auto"),
    "frost_palace": dict(site="coast", facing="auto", biome="minecraft:snowy_plains"),
}


# ---------------------------------------------------------------------------------------------------------------- input

def load_anchors(path=ANCHORS):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return {k: dict(v, id=k) for k, v in data.items() if k != "keepout" and isinstance(v, dict)}


def unrle(values):
    out = []
    for i in range(0, len(values), 2):
        out += [values[i]] * values[i + 1]
    return out


def js_object(path, const):
    """The JSON literal of `const <name> = {...}` in a generated script."""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("const %s = " % const):
            return json.loads(line[line.index("{"):].rstrip().rstrip(";"))
    raise SystemExit("%s: no `const %s`" % (path, const))


class Sources:
    """Everything the derivation reads, loaded once (paths overridable for tests)."""

    def __init__(self, anchors=ANCHORS, builds=BUILDS, landmarks=LANDMARKS, arrival=ARRIVAL, generated=GENERATED):
        self.anchors = load_anchors(anchors)
        self.builds = {}
        for p in sorted(Path(builds).glob("*.toml")):
            if not p.name.startswith("_"):
                self.builds[p.stem] = tomllib.loads(p.read_text(encoding="utf-8"))
        self.landmarks = {lm["name"]: lm for lm in
                          tomllib.loads(Path(landmarks).read_text(encoding="utf-8")).get("landmark", [])}
        self.safe_radius = tomllib.loads(Path(arrival).read_text(encoding="utf-8")).get("life2", {}).get("safe_radius", 48)
        gen = Path(generated)
        self.footprints = js_object(gen / "builds.js", "TtlBuildFootprints")
        self.tempest = js_object(gen / "tempest_footprint.js", "TtlTempestFootprint")
        self.dwargon = js_object(gen / "dwargon_footprint.js", "TtlDwargonFootprint")


# --------------------------------------------------------------------------------------------------------- requirement

def half_diag(sx, sz):
    return math.hypot(sx, sz) / 2


def build_requirement(name, build, fp, kind):
    """Box, plate, min_r, height and (carve) roof columns of a design/builds build."""
    sx, sy, sz = fp["size"]
    ax, ay, az = build["anchor"]
    margin = max(build.get("margin", 8), build.get("repair_margin", 8))
    top = unrle(fp["top"])
    none = fp["none"]
    tops = [t for t in top if t != none]
    req = {"build": name, "box": [sx, sz], "anchor": [ax, ay, az], "margin": margin,
           "plate": [sx + 2 * margin, sz + 2 * margin], "height": (max(tops) if tops else ay) - ay,
           "min_r": math.ceil(max(half_diag(sx, sz) + 12, half_diag(sx + 2 * margin, sz + 2 * margin)))}
    if kind == "carve":
        # blueprint column (bx, bz) -> blocks the roof rises above the walking level; the cover goes on top of that
        roof = {}
        for i, t in enumerate(top):
            if t != none and t - ay >= ROOF_MIN:
                roof[(i % sx, i // sx)] = t - ay
        req["roof_cols"] = roof
        req["roof"] = max(roof.values()) if roof else 0
    return req


def dwargon_requirement(f):
    sx, sy, sz = f["size"]
    ax, ay, az = f["arrival"]
    m = f["margin"]
    w = f["grid"][0]
    none = f["none"]
    roof = {}
    for i, r in enumerate(unrle(f.get("roof", []))):
        if r != none:
            # footprint `roof` = blueprint y of the highest interior air: the rock starts one above it
            roof[(i % w - m, i // w - m)] = r + 1 - ay
    return {"build": None, "box": [sx, sz], "anchor": [ax, ay, az], "margin": m, "plate": [sx + 2 * m, sz + 2 * m],
            "height": sy - ay, "roof_cols": roof, "roof": max(roof.values()) if roof else 0,
            "min_r": math.ceil(max(half_diag(sx, sz) + 12, half_diag(sx + 2 * m, sz + 2 * m)))}


def tempest_requirement(f):
    sx, sy, sz = f["size"]
    ax, ay, az = f["arrival"]
    m = f["margin"]
    gx, gz = max(sx, TEMPEST_GROWTH), max(sz, TEMPEST_GROWTH)
    return {"build": None, "box": [gx, gz], "anchor": [ax, ay, az], "margin": m, "plate": [gx + 2 * m, gz + 2 * m],
            "height": sy - ay, "min_r": math.ceil(max(half_diag(gx, gz) + 12, half_diag(gx + 2 * m, gz + 2 * m)))}


def requirements(src, kinds=None):
    """{anchor id: requirement}. kinds: {id: site kind} (the SVG's), else the first pass."""
    out = {}
    for aid, a in src.anchors.items():
        kind = (kinds or {}).get(aid) or FIRST_PASS.get(aid, {}).get("site", "clearing")
        akind = a.get("kind")
        if aid == "tempest":
            req = tempest_requirement(src.tempest)
        elif aid == "dwargon":
            req = dwargon_requirement(src.dwargon)
        elif akind == "build" and a.get("build") in src.footprints and a.get("build") in src.builds:
            req = build_requirement(a["build"], src.builds[a["build"]], src.footprints[a["build"]], kind)
        elif akind == "landmark" and a.get("landmark") in src.landmarks:
            req = {"build": None, "min_r": int(src.landmarks[a["landmark"]].get("reach", 48)) + 8}
        elif akind == "arrival":
            req = {"build": None, "min_r": int(src.safe_radius) + 12}
        else:
            req = {"build": None, "min_r": PIN_R}
        req["anchor_kind"] = akind
        req["plated"] = akind in PLATED
        out[aid] = req
    return out


# ------------------------------------------------------------------------------------------------------------ sites

def svg_sites(path):
    """{id: (kind, r, x, z)} from the SVG `sites` layer."""
    import svgparse
    rep = svgparse.Report()
    shapes = svgparse.read_svg(path, rep)
    if shapes is None:
        raise SystemExit("%s: %s" % (path, "; ".join(e["message"] for e in rep.errors)))
    out = {}
    for s in shapes["sites"]:
        if s.get("data-id") and s.r is not None:
            out[s.get("data-id")] = (s.get("data-site", "clearing"), s.r, s.cx, s.cy)
    return out


def raster_grounds(rasters):
    """{id: y} from svg2rasters' index.json (every site: the plate ground, a pin's surface)."""
    p = Path(rasters) / "index.json"
    if not p.is_file():
        return {}
    return {s["id"]: s["y"] for s in json.loads(p.read_text(encoding="utf-8")).get("sites", []) if "y" in s}


def derive(src, svg=None, grounds=None, existing=None):
    """{id: ordered fields} for world/sites.toml. svg: svg_sites(); grounds: raster_grounds(); existing: the file's
    current tables (their override keys are kept)."""
    svg, grounds, existing = svg or {}, grounds or {}, existing or {}
    kinds = {k: v[0] for k, v in svg.items()}
    reqs = requirements(src, kinds)
    out = {}
    for aid, a in src.anchors.items():
        req, fp = reqs[aid], FIRST_PASS.get(aid, {})
        old = existing.get(aid) if isinstance(existing.get(aid), dict) else {}
        rec = {}
        if aid in svg:
            rec["site"] = svg[aid][0]
        else:
            rec["site"] = old.get("site") or fp.get("site", "clearing")
        if not req["plated"]:
            rec["r"] = PIN_R if aid not in svg else int(round(svg[aid][1]))
            rec["min_r"] = PIN_R
        else:
            if aid in svg:
                drawn = int(round(svg[aid][1]))
                rec["r"] = max(drawn, req["min_r"])
                if drawn < req["min_r"]:
                    rec["svg_r"] = drawn
            else:
                rec["r"] = max(int(old.get("r", 0)), int(fp.get("r", 0)), req["min_r"])
            rec["min_r"] = req["min_r"]
        for key in ("box", "plate", "margin", "height"):
            if key in req:
                rec[key] = req[key]
        if "roof" in req and rec["site"] == "carve":
            rec["roof"] = req["roof"]
        for key in OVERRIDE_KEYS:
            if key in old:
                rec[key] = old[key]
            elif key in fp and key != "site":
                rec[key] = fp[key]
        if rec["site"] == "carve":
            rec.setdefault("min_cover", MIN_COVER)
            if req.get("build"):
                rec.setdefault("clear_above", False)
        y = grounds.get(aid, rec.get("plate_y"))
        if req["anchor_kind"] == "build":
            rec["ground"] = "fixed"
        if y is not None:
            rec["y"] = int(y)
        out[aid] = rec
    return out, reqs


def drawn_small(sites):
    """Sites whose SVG circle is smaller than the build needs (the converter uses min_r; redraw the circle)."""
    return ["%s: drawn r %d < min_r %d; the site uses r %d (redraw the circle in world/map.svg)"
            % (aid, rec["svg_r"], rec["min_r"], rec["r"]) for aid, rec in sites.items() if "svg_r" in rec]


def overlaps(sites, svg, anchors):
    """Plated sites whose discs (r, after the footprint) overlap; an anchor and its `of` parent are one place."""
    plated = [(aid, svg[aid][2], svg[aid][3], sites[aid]["r"]) for aid in sites
              if aid in svg and anchors.get(aid, {}).get("kind") in PLATED]
    out = []
    for n, (a, ax, az, ar) in enumerate(plated):
        for b, bx, bz, br in plated[n + 1:]:
            if anchors[a].get("of") == b or anchors[b].get("of") == a:
                continue
            d = math.hypot(ax - bx, az - bz)
            if d < ar + br:
                out.append("%s and %s overlap: %d blocks apart, r %d + %d" % (a, b, d, ar, br))
    return out


def problems(sites, reqs):
    """Misfits: a site smaller than its build, a carve without cover, a top above the build limit."""
    out = []
    for aid, rec in sites.items():
        req = reqs[aid]
        if rec["site"] not in SITE_KINDS:
            out.append("%s: site %r is not one of %s" % (aid, rec["site"], ", ".join(SITE_KINDS)))
        if req["plated"] and rec["r"] < rec["min_r"]:
            out.append("%s: r %d < min_r %d (the build's box does not fit its site)" % (aid, rec["r"], rec["min_r"]))
        if "plate" in rec and half_diag(*rec["plate"]) > rec["r"] + 1e-9:
            out.append("%s: the plate %s does not fit r %d" % (aid, rec["plate"], rec["r"]))
        if rec["site"] == "carve" and rec.get("min_cover", 0) < MIN_COVER:
            out.append("%s: carve site with min_cover %s < %d" % (aid, rec.get("min_cover"), MIN_COVER))
        if "y" in rec and "height" in rec and rec["y"] + rec["height"] >= BUILD_LIMIT:
            out.append("%s: top y %d + %d reaches the build limit %d" % (aid, rec["y"], rec["height"], BUILD_LIMIT))
        if rec.get("facing", "auto") not in FACINGS:
            out.append("%s: facing %r is not one of %s" % (aid, rec.get("facing"), ", ".join(FACINGS)))
    return out


# ------------------------------------------------------------------------------------------------------------ TOML

def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    raise TypeError(v)


HEADER = """\
# Sites of the own world: what each anchor's site must be (design/architecture/own-world.md §3.3, §4). GENERATED by
# tools/world/sites_from_builds.py from the build footprints, design/data/anchors.toml and, once it exists, the SVG
# sites layer and the rasters; `python -I tools/world/sites_from_builds.py` rewrites it. Claude owns this file
# (ChatGPT never edits it). Nothing in the game reads it until the switch to the own world.
#
# Generated every run:  site (SVG data-site, else the first pass), r (SVG or first pass, at least min_r), svg_r (the
#   SVG circle when it is drawn smaller than min_r: redraw it), min_r, box, plate, margin, height, roof (carve),
#   ground = "fixed" (builds), y (the walking level = plate height, from the rasters once they exist).
# Kept when set here:   plate_y (plate level override), fade, biome (inside r), facing (north/south/east/west/auto),
#   min_cover (carve, >= 6), surface ("water": the plate lies under the water), clear_above, notes.
# tests/test_world_sites.py checks that every build fits its site and every carve site keeps >= 6 blocks of cover.
"""


EXTRA_TABLES = ("forest", "region")


def dumps(sites, existing=None):
    """The file text; the hand tables [forest] (<type> = biome) and [region.<letter>] (default_biome) of the existing
    file are kept as they are."""
    lines = [HEADER.rstrip("\n")]
    for aid, rec in sites.items():
        lines.append("")
        lines.append("[%s]" % aid)
        for k, v in rec.items():
            lines.append("%s = %s" % (k, toml_value(v)))
    existing = existing or {}
    if isinstance(existing.get("forest"), dict) and existing["forest"]:
        lines += ["", "[forest]"] + ["%s = %s" % (k, toml_value(v)) for k, v in existing["forest"].items()]
    for letter, tbl in (existing.get("region") or {}).items():
        if isinstance(tbl, dict):
            lines += ["", "[region.%s]" % letter] + ["%s = %s" % (k, toml_value(v)) for k, v in tbl.items()]
    return "\n".join(lines) + "\n"


def load_existing(path):
    p = Path(path)
    return tomllib.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--svg", default=None, help="the map (default world/map.svg when it exists)")
    ap.add_argument("--rasters", default=str(RASTERS), help="svg2rasters output dir (its index.json gives y)")
    ap.add_argument("--out", default=str(SITES_TOML))
    ap.add_argument("--check", action="store_true", help="exit 1 when the file is stale or a build misfits")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    svg_path = Path(args.svg) if args.svg else (SVG if SVG.is_file() else None)
    src = Sources()
    existing = load_existing(args.out)
    sites, reqs = derive(src, svg_sites(svg_path) if svg_path else None, raster_grounds(args.rasters), existing)
    text = dumps(sites, existing)
    bad = problems(sites, reqs)
    for b in bad:
        print("error: " + b, file=sys.stderr)
    for w in drawn_small(sites):
        print("warn: " + w, file=sys.stderr)
    out = Path(args.out)
    if args.check:
        if not out.is_file() or out.read_text(encoding="utf-8") != text:
            print("%s is stale: run python -I tools/world/sites_from_builds.py" % out, file=sys.stderr)
            return 1
        return 1 if bad else 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %s: %d sites (%d plated)%s" % (out, len(sites), sum(1 for r in reqs.values() if r["plated"]),
                                                 ", from %s" % svg_path if svg_path else ", first pass (no map yet)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
