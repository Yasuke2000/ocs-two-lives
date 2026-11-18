#!/usr/bin/env python3
"""Generate pack/kubejs/server_scripts/ttl/generated/data.js from design/data/*.toml.

Gameplay numbers live in TOML so balancing never needs a code change. The scripts read them as `TtlData`.
design/builds/<name>.toml (canon-location builds, life/builds.js) is read into `TtlData.builds`, and the ground
footprint of every build's structure files goes to generated/builds.js (`TtlBuildFootprints`).
Usage: gen_data.py            write the files
       gen_data.py --check    exit 1 if a file is out of date (used by validate.py)
"""
import json
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))  # python -I (validate.py) does not put the script's folder on the path
import nbt  # noqa: E402

SOURCES = ROOT / "design" / "data"
BUILDS = ROOT / "design" / "builds"
TARGET = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "data.js"
FOOTPRINTS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "builds.js"
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
CANON_MAP = ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
SCRIPTS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl"
NONE = -999  # "no value" in the footprint grids (same marker as blueprints/_footprint.py)
AIRISH = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:structure_void"}


def check_skills(skills: dict) -> None:
    seen = {}
    for rarity in ("legendary", "rare", "common"):
        if rarity not in skills["caps"]:
            raise SystemExit(f"skills.toml: caps.{rarity} missing")
        for skill in skills[rarity]["skills"]:
            if skill in seen:
                raise SystemExit(f"skills.toml: {skill} is both {seen[skill]} and {rarity}")
            seen[skill] = rarity


def check_guide(guide: dict) -> None:
    # life/guide.js opens these sets by name; the guide screen needs a title and a body on every page.
    for name in ("main", "corridor", "life2"):
        pages = guide.get(name)
        if not isinstance(pages, list) or not pages:
            raise SystemExit(f"guide.toml: [[{name}]] pages missing")
    for name, pages in guide.items():
        for i, page in enumerate(pages, 1):
            if not str(page.get("title", "")).strip() or not str(page.get("body", "")).strip():
                raise SystemExit(f"guide.toml: {name} page {i} needs a title and a body")


def check_mortal_banned(banned: dict) -> None:
    # life/mortal_banned.js matches item ids against these lists; a typo would silently ban nothing.
    patterns = {"namespaces": r"[a-z0-9_.-]+", "items": r"[a-z0-9_.-]+:[a-z0-9_/.-]+",
                "tags": r"[a-z0-9_.-]+:[a-z0-9_/.-]+", "allow": r"[a-z0-9_.-]+:[a-z0-9_/.-]+"}
    for key, pattern in patterns.items():
        values = banned.get(key)
        if not isinstance(values, list):
            raise SystemExit(f"mortal_banned.toml: {key} must be a list (use [] for none)")
        for v in values:
            if not isinstance(v, str) or not re.fullmatch(pattern, v):
                raise SystemExit(f"mortal_banned.toml: {key} entry {v!r} is not a valid "
                                 f"{'namespace, like tensura' if key == 'namespaces' else 'full id, like mod:thing'}")
        if len(set(values)) != len(values):
            raise SystemExit(f"mortal_banned.toml: {key} lists an entry twice")


def settlement_box(script: str, anchor: str, footprint: str) -> tuple[int, int, int, int]:
    """World box (x0, z0, x1, z1, margin included) of Tempest or Dwargon, as their scripts compute it."""
    m = re.search(anchor + r":\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)", (SCRIPTS / "life" / script).read_text(encoding="utf-8"))
    line = next(t for t in (SCRIPTS / "generated" / footprint).read_text(encoding="utf-8").splitlines()
                if t.startswith("const ") and "Footprint = " in t)
    f = json.loads(line[line.index("{"):])
    x0, z0 = int(m.group(1)) - f["arrival"][0], int(m.group(2)) - f["arrival"][2]
    return x0 - f["margin"], z0 - f["margin"], x0 + f["size"][0] + f["margin"] - 1, z0 + f["size"][2] + f["margin"] - 1


def ref_to_world(canon: dict, ref) -> tuple[int, int]:
    """Reference-map pixel -> world x/z: (ref - origin) x width / 2570 (canon_regions.json "_doc")."""
    scale = canon["width"] / 2570
    return round((ref[0] - canon["origin"][0]) * scale), round((ref[1] - canon["origin"][1]) * scale)


def check_landmarks(landmarks: dict) -> None:
    # life/landmarks.js places these; x/z come from canon_regions.json unless given, and every landmark keeps
    # `keepout` blocks (plus its reach) clear of Tempest's and Dwargon's boxes.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["ref"] for lm in canon["landmarks"]}
    boxes = {"Tempest": settlement_box("tempest.js", "LANDMARK", "tempest_footprint.js"),
             "Dwargon": settlement_box("dwargon.js", "GATE", "dwargon_footprint.js")}
    seen = set()
    for lm in landmarks["landmark"]:
        name = lm.get("name", "")
        where = f"landmarks.toml: {name or '?'}"
        if not re.fullmatch(r"[a-z0-9_]+", name) or name in seen:
            raise SystemExit(f"{where}: name must be unique [a-z0-9_]")
        seen.add(name)
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", str(lm.get("structure", ""))):
            raise SystemExit(f"{where}: structure must be a namespaced id")
        if lm.get("surface") not in ("land", "water", "any"):
            raise SystemExit(f"{where}: surface must be land, water or any")
        for key in ("reach", "version"):
            if not isinstance(lm.get(key), int) or lm[key] < 1:
                raise SystemExit(f"{where}: {key} must be a positive integer")
        if "canon" in lm and lm["canon"] not in refs:
            raise SystemExit(f"{where}: canon landmark {lm['canon']!r} not in canon_regions.json")
        if ("x" in lm) != ("z" in lm):
            raise SystemExit(f"{where}: give both x and z, or neither")
        if "x" not in lm:
            if "canon" not in lm:
                raise SystemExit(f"{where}: needs x/z or canon")
            lm["x"], lm["z"] = ref_to_world(canon, refs[lm["canon"]])
        for label, (x0, z0, x1, z1) in boxes.items():
            gap = math.hypot(max(x0 - lm["x"], 0, lm["x"] - x1), max(z0 - lm["z"], 0, lm["z"] - z1))
            if gap < landmarks["keepout"] + lm["reach"]:
                raise SystemExit(f"{where}: ({lm['x']}, {lm['z']}) is {gap:.0f} blocks from {label}, "
                                 f"needs {landmarks['keepout'] + lm['reach']} (keepout + reach)")


BUILD_KEYS = {"name", "title", "landmark", "x", "z", "anchor", "ground", "y", "search", "dimension", "version",
              "clear_above", "margin", "notes"}


def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def structure_files(name: str) -> list[Path]:
    """<name>.nbt, or the slabs <name>_0.nbt, <name>_1.nbt, ... (PARTS builds), stacked along z."""
    single = STRUCTURES / f"{name}.nbt"
    if single.exists():
        return [single]
    parts = []
    while (STRUCTURES / f"{name}_{len(parts)}.nbt").exists():
        parts.append(STRUCTURES / f"{name}_{len(parts)}.nbt")
    return parts


def rle(values: list[int]) -> list[int]:
    out: list[int] = []
    for v in values:
        if out and out[-2] == v:
            out[-1] += 1
        else:
            out += [v, 1]
    return out


def read_footprint(files: list[Path]) -> dict:
    """Size, slabs and per-column ground data of a build's structure files (slabs stacked along z).

    Per column of the box (row-major, z outer, x inner; run-length encoded as [value, count, ...]):
    fill = y of the lowest non-air block (NONE: the column is air) and top = y of the highest non-air block + 1.
    life/builds.js fills the gap between the terrain and `fill` and clears from `top` up, so nothing floats.
    """
    sx = sy = z0 = 0
    slabs, offsets, low, high = [], [], {}, {}
    for path in files:
        root = nbt.read_gzip(path)
        px, py, pz = root["size"]
        palette = root.get("palette") or (root.get("palettes") or [[]])[0]
        solid = [e["Name"] not in AIRISH for e in palette]
        for block in root["blocks"]:
            if not solid[block["state"]]:
                continue
            x, y, z = block["pos"]
            k = (x, z + z0)
            if y < low.get(k, 1 << 30):
                low[k] = y
            if y > high.get(k, -1):
                high[k] = y
        slabs.append(f"ttl:{path.stem}")
        offsets.append(z0)
        sx, sy, z0 = max(sx, px), max(sy, py), z0 + pz
    cells = [(x, z) for z in range(z0) for x in range(sx)]
    return {"size": [sx, sy, z0], "slabs": slabs, "parts": offsets, "none": NONE,
            "fill": rle([low.get(c, NONE) for c in cells]),
            "top": rle([high[c] + 1 if c in high else NONE for c in cells])}


def canon_char(x: int, z: int) -> str | None:
    """The canon_map.txt character (a chunk) at world x/z, None outside the grid."""
    lines = CANON_MAP.read_text(encoding="utf-8").splitlines()
    origin = next(t for t in lines if t.startswith("# origin")).split()
    ox, oy = int(origin[2]), int(origin[3])
    rows = [t for t in lines if not t.startswith("#")]
    row, col = oy + (z >> 4), ox + (x >> 4)
    return rows[row][col] if 0 <= row < len(rows) and 0 <= col < len(rows[row]) else None


def check_builds() -> tuple[list[dict], dict]:
    """design/builds/<name>.toml -> (TtlData.builds, footprints); files starting with `_` are examples."""
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["ref"] for lm in canon["landmarks"]}
    builds, footprints = [], {}
    for path in sorted(BUILDS.glob("*.toml")) if BUILDS.exists() else []:
        if path.name.startswith("_"):
            continue
        with path.open("rb") as f:
            b = tomllib.load(f)
        name = b.get("name", "")
        where = f"builds/{path.name}"
        if not re.fullmatch(r"[a-z0-9_]+", str(name)) or name != path.stem:
            raise SystemExit(f"{where}: name must be [a-z0-9_] and equal the file name ({path.stem})")
        unknown = sorted(set(b) - BUILD_KEYS)
        if unknown:
            raise SystemExit(f"{where}: unknown field(s) {', '.join(unknown)} (known: {', '.join(sorted(BUILD_KEYS))})")
        if not str(b.get("title", "")).strip():
            raise SystemExit(f"{where}: title is missing")
        b["dimension"] = b.get("dimension", "minecraft:overworld")
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", str(b["dimension"])):
            raise SystemExit(f"{where}: dimension {b['dimension']!r} is not a namespaced id")
        b["version"] = b.get("version", 1)
        if not is_int(b["version"]) or b["version"] < 1:
            raise SystemExit(f"{where}: version must be a positive integer")
        b["clear_above"] = b.get("clear_above", True)
        if not isinstance(b["clear_above"], bool):
            raise SystemExit(f"{where}: clear_above must be true or false")
        b["margin"] = b.get("margin", 8)
        if not is_int(b["margin"]) or not 0 <= b["margin"] <= 16:
            raise SystemExit(f"{where}: margin must be an integer 0..16")
        b["ground"] = b.get("ground", "survey")
        if b["ground"] not in ("survey", "fixed"):
            raise SystemExit(f"{where}: ground must be \"survey\" or \"fixed\"")
        if b["ground"] == "fixed" and not is_int(b.get("y")):
            raise SystemExit(f"{where}: ground = \"fixed\" needs y = <walking level>")
        if b["ground"] == "survey" and "y" in b:
            raise SystemExit(f"{where}: y only goes with ground = \"fixed\"")
        b["search"] = b.get("search", 48)
        if not is_int(b["search"]) or not 0 <= b["search"] <= 192:
            raise SystemExit(f"{where}: search must be an integer 0..192")

        # Where: x/z win, else the canon landmark's reference pixel.
        if ("x" in b) != ("z" in b):
            raise SystemExit(f"{where}: give both x and z, or neither")
        if "x" in b:
            if not is_int(b["x"]) or not is_int(b["z"]):
                raise SystemExit(f"{where}: x and z must be integers")
        elif "landmark" in b:
            if b["landmark"] not in refs:
                raise SystemExit(f"{where}: landmark {b['landmark']!r} is not in canon_regions.json "
                                 f"(names are matched exactly)")
            b["x"], b["z"] = ref_to_world(canon, refs[b["landmark"]])
        else:
            raise SystemExit(f"{where}: needs a landmark or x and z")

        # The structure files and the anchor.
        files = structure_files(name)
        if not files:
            raise SystemExit(f"{where}: no structure pack/kubejs/data/ttl/structure/{name}.nbt or {name}_0.nbt "
                             f"(run python tools/build_structures.py {name})")
        fp = read_footprint(files)
        anchor = b.get("anchor")
        if not (isinstance(anchor, list) and len(anchor) == 3 and all(is_int(v) for v in anchor)):
            raise SystemExit(f"{where}: anchor must be [x, y, z] in blueprint coordinates")
        size = fp["size"]
        if not all(0 <= a < s for a, s in zip(anchor, size)) or anchor[1] < 1:
            raise SystemExit(f"{where}: anchor {anchor} is outside the structure ({size[0]}x{size[1]}x{size[2]}; "
                             f"y must be 1 or more, the block below it is the ground layer)")
        if max(size[0], size[2]) + 2 * b["margin"] + 2 * b["search"] > 1000:
            raise SystemExit(f"{where}: box + margin + 2 x search is wider than 1000 blocks (forceload limit)")
        b["size"] = size

        if b["dimension"] == "minecraft:overworld":
            ch = canon_char(b["x"], b["z"])
            if ch is None or ch == ".":
                print(f"warn: {where}: ({b['x']}, {b['z']}) is open sea or outside canon_map.txt", file=sys.stderr)
            elif ch == "~":
                print(f"warn: {where}: ({b['x']}, {b['z']}) is a river or lake in canon_map.txt "
                      f"(the placer looks for dry land within search = {b['search']})", file=sys.stderr)
        builds.append(b)
        footprints[name] = fp
    for i, a in enumerate(builds):
        for c in builds[i + 1:]:
            if a["dimension"] == c["dimension"] and abs(a["x"] - c["x"]) < 40 and abs(a["z"] - c["z"]) < 40:
                print(f"warn: builds {a['name']} and {c['name']} are less than 40 blocks apart", file=sys.stderr)
    return builds, footprints


def render() -> dict[Path, str]:
    data = {}
    for path in sorted(SOURCES.glob("*.toml")):
        with path.open("rb") as f:
            data[path.stem] = tomllib.load(f)
    if "skills" in data:
        check_skills(data["skills"])
    if "guide" in data:
        check_guide(data["guide"])
    if "mortal_banned" in data:
        check_mortal_banned(data["mortal_banned"])
    if "landmarks" in data:
        check_landmarks(data["landmarks"])
    data["builds"], footprints = check_builds()
    body = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    grids = json.dumps(footprints, separators=(",", ":"), sort_keys=True)
    return {
        TARGET: (
            "// priority: 200\n"
            "// GENERATED by tools/gen_data.py from design/data/*.toml and design/builds/*.toml. Do not edit; edit the TOML and regenerate.\n"
            f"const TtlData = {body}\n"
        ),
        FOOTPRINTS: (
            "// priority: 200\n"
            "// GENERATED by tools/gen_data.py from design/builds/*.toml and their structure files (pack/kubejs/data/ttl/structure). Do not edit.\n"
            f"const TtlBuildFootprints = {grids}\n"
        ),
    }


def main() -> None:
    files = render()
    if "--check" in sys.argv:
        for path, text in files.items():
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != text:
                print(f"FAIL generated/{path.name} is stale: run python tools/gen_data.py")
                sys.exit(1)
        return
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
