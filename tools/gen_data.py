#!/usr/bin/env python3
"""Generate pack/kubejs/server_scripts/ttl/generated/data.js from design/data/*.toml.

Gameplay numbers live in TOML so balancing never needs a code change. The scripts read them as `TtlData`.
Usage: gen_data.py            write the file
       gen_data.py --check    exit 1 if the file is out of date (used by validate.py)
"""
import json
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "design" / "data"
TARGET = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "data.js"
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
SCRIPTS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl"


def check_skills(skills: dict) -> None:
    seen = {}
    for rarity in ("legendary", "rare", "common"):
        if rarity not in skills["caps"]:
            raise SystemExit(f"skills.toml: caps.{rarity} missing")
        for skill in skills[rarity]["skills"]:
            if skill in seen:
                raise SystemExit(f"skills.toml: {skill} is both {seen[skill]} and {rarity}")
            seen[skill] = rarity
    legendary = skills.get("legendary", {})
    for key in ("max_holders", "slots_per_era"):
        value = legendary.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise SystemExit(f"skills.toml: legendary.{key} must be an integer >= 0")
    for route in skills.get("transfer", {}).get("routes", []):
        if not re.fullmatch(r"[a-z0-9_]+", str(route)):
            raise SystemExit(f"skills.toml: transfer.routes has a bad route {route!r}")
    absorb = skills.get("absorb", {})
    for skill in absorb.get("skills", []):
        if not re.fullmatch(r"[a-z0-9_]+", skill):
            raise SystemExit(f"skills.toml: absorb.skills has a bad id {skill!r}")
    core = skills.get("core", {})
    for rarity, weight in core.get("weights", {}).items():
        if rarity not in ("rare", "common"):
            raise SystemExit(f"skills.toml: core.weights.{rarity}: a Skill Core never holds that rarity (rare, common only)")
        if not isinstance(weight, (int, float)) or weight < 0:
            raise SystemExit(f"skills.toml: core.weights.{rarity} must be a number >= 0")
    if not any(core.get("weights", {}).get(r, 1) > 0 for r in ("rare", "common")):
        raise SystemExit("skills.toml: core.weights must leave at least one rarity above 0")
    era_ids = set()
    for title in skills.get("era", {}).get("titles", []):
        if not re.fullmatch(r"[a-z0-9_]+", str(title.get("id", ""))) or not str(title.get("name", "")).strip():
            raise SystemExit(f"skills.toml: era.titles needs an id [a-z0-9_] and a name: {title}")
        if title["id"] in era_ids:
            raise SystemExit(f"skills.toml: era title id {title['id']} twice")
        era_ids.add(title["id"])


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


def check_carryover(carry: dict, karma: dict | None) -> None:
    # life/carryover.js reads these by name; a tier or axis typo would silently give nobody a book or an echo.
    for key in ("lore_unjudged", "lore_judged"):
        lines = carry.get("gem", {}).get(key)
        if not isinstance(lines, list) or not lines or not all(isinstance(t, str) and t.strip() for t in lines):
            raise SystemExit(f"carryover.toml: gem.{key} must be a non-empty list of lines")
    life2 = carry["gem"].get("life2", {})
    if not isinstance(life2.get("cooldown_minutes"), int) or life2["cooldown_minutes"] < 0:
        raise SystemExit("carryover.toml: gem.life2.cooldown_minutes must be a whole number >= 0")
    book = carry.get("book", {})
    for key in ("min_axis_score", "max_level"):
        if not isinstance(book.get(key), int) or book[key] < 1:
            raise SystemExit(f"carryover.toml: book.{key} must be a whole number >= 1")
    if not isinstance(book.get("lore"), list):
        raise SystemExit("carryover.toml: book.lore must be a list (use [] for none)")
    if karma is None:
        return
    tiers = [t["id"] for t in karma["tiers"]]
    for tier, echo in life2.get("tiers", {}).items():
        if tier not in tiers:
            raise SystemExit(f"carryover.toml: gem.life2.tiers.{tier} is not a tier in karma.toml ({', '.join(tiers)})")
    for tier in tiers:
        echo = life2.get("tiers", {}).get(tier)
        if not echo or not isinstance(echo.get("seconds"), int) or echo["seconds"] < 1                 or not isinstance(echo.get("amplifier"), int) or not 0 <= echo["amplifier"] <= 4:
            raise SystemExit(f"carryover.toml: gem.life2.tiers.{tier} needs seconds >= 1 and amplifier 0-4")
    if book.get("min_tier") not in tiers:
        raise SystemExit(f"carryover.toml: book.min_tier {book.get('min_tier')!r} is not a tier in karma.toml ({', '.join(tiers)})")
    if book.get("axis") not in karma["axes"]:
        raise SystemExit(f"carryover.toml: book.axis {book.get('axis')!r} is not an axis in karma.toml ({', '.join(karma['axes'])})")


def settlement_box(script: str, anchor: str, footprint: str) -> tuple[int, int, int, int]:
    """World box (x0, z0, x1, z1, margin included) of Tempest or Dwargon, as their scripts compute it."""
    m = re.search(anchor + r":\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)", (SCRIPTS / "life" / script).read_text(encoding="utf-8"))
    line = next(t for t in (SCRIPTS / "generated" / footprint).read_text(encoding="utf-8").splitlines()
                if t.startswith("const ") and "Footprint = " in t)
    f = json.loads(line[line.index("{"):])
    x0, z0 = int(m.group(1)) - f["arrival"][0], int(m.group(2)) - f["arrival"][2]
    return x0 - f["margin"], z0 - f["margin"], x0 + f["size"][0] + f["margin"] - 1, z0 + f["size"][2] + f["margin"] - 1


def check_landmarks(landmarks: dict) -> None:
    # life/landmarks.js places these; x/z come from canon_regions.json unless given, and every landmark keeps
    # `keepout` blocks (plus its reach) clear of Tempest's and Dwargon's boxes.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["ref"] for lm in canon["landmarks"]}
    scale = canon["width"] / 2570
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
            ref = refs[lm["canon"]]
            lm["x"] = round((ref[0] - canon["origin"][0]) * scale)
            lm["z"] = round((ref[1] - canon["origin"][1]) * scale)
        for label, (x0, z0, x1, z1) in boxes.items():
            gap = math.hypot(max(x0 - lm["x"], 0, lm["x"] - x1), max(z0 - lm["z"], 0, lm["z"] - z1))
            if gap < landmarks["keepout"] + lm["reach"]:
                raise SystemExit(f"{where}: ({lm['x']}, {lm['z']}) is {gap:.0f} blocks from {label}, "
                                 f"needs {landmarks['keepout'] + lm['reach']} (keepout + reach)")


def render() -> str:
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
    if "carryover" in data:
        check_carryover(data["carryover"], data.get("karma"))
    body = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    return (
        "// priority: 200\n"
        "// GENERATED by tools/gen_data.py from design/data/*.toml. Do not edit; edit the TOML and regenerate.\n"
        f"const TtlData = {body}\n"
    )


def main() -> None:
    text = render()
    if "--check" in sys.argv:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print("FAIL generated/data.js is stale: run python tools/gen_data.py")
            sys.exit(1)
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
