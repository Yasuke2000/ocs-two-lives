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


def check_bosses(bosses: dict, landmarks: dict | None) -> None:
    # bosses/boss.js summons these; a typo would fail only when a quest or altar summons the boss.
    ident = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    names = {lm["name"] for lm in (landmarks or {}).get("landmark", [])}
    fw = bosses.get("framework", {})
    for key, kind in (("block_natural", bool), ("untame", bool), ("idle_minutes", int), ("presence_secs", int)):
        if not isinstance(fw.get(key), kind):
            raise SystemExit(f"bosses.toml: [framework] {key} must be a {kind.__name__}")
    if not isinstance(fw.get("bindable"), list):
        raise SystemExit("bosses.toml: [framework] bindable must be a list (use [] for none)")
    all_ids = [b.get("id") for b in bosses.get("boss", [])]
    for bid in fw["bindable"]:
        if bid not in all_ids:
            raise SystemExit(f"bosses.toml: [framework] bindable names unknown boss {bid!r}")
    ids, entities = set(), set()
    for b in bosses.get("boss", []):
        bid = b.get("id", "")
        where = f"bosses.toml: boss {bid or '?'}"
        if not re.fullmatch(r"[a-z0-9_]+", bid) or bid in ids:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        ids.add(bid)
        if not re.fullmatch(ident, str(b.get("entity", ""))) or b["entity"] in entities:
            raise SystemExit(f"{where}: entity must be a unique namespaced id")
        entities.add(b["entity"])
        if bid != b["entity"].split(":", 1)[1]:
            raise SystemExit(f"{where}: id must equal the entity path ({b['entity'].split(':', 1)[1]}); "
                             f"the stage ttl.defeated.<id> is read by compat/tombstone_bosses.js")
        for req in b.get("requires", []):
            if req not in all_ids or req == bid:
                raise SystemExit(f"{where}: requires names an unknown boss or itself: {req!r}")
        if b.get("tier") not in (1, 2, 3, 4):
            raise SystemExit(f"{where}: tier must be 1..4")
        if not str(b.get("title", "")).strip() or re.search(r"['\\\"]", b["title"]):
            raise SystemExit(f"{where}: title is empty or contains a quote or backslash")
        arena = b.get("arena")
        if arena is not None:
            if "landmark" in arena:
                if arena["landmark"] not in names:
                    raise SystemExit(f"{where}: arena landmark {arena['landmark']!r} not in landmarks.toml")
            elif not all(isinstance(arena.get(k), int) for k in "xz") or not isinstance(arena.get("y", 0), int):
                raise SystemExit(f"{where}: arena needs a landmark or integer x and z (y optional)")
            elif "radius" in arena and (not isinstance(arena["radius"], int) or not 4 <= arena["radius"] <= 256):
                raise SystemExit(f"{where}: arena radius must be an integer 4..256")
            if "landmark" in arena and "radius" in arena:
                raise SystemExit(f"{where}: a landmark arena cannot have a radius (give x and z)")
        for key in ("hp_mult", "per_player_mult"):
            if not isinstance(b.get(key), (int, float)) or b[key] < (1 if key == "hp_mult" else 0):
                raise SystemExit(f"{where}: {key} must be a number (hp_mult >= 1, per_player_mult >= 0)")
        if not isinstance(b.get("range"), int) or not 8 <= b["range"] <= 128:
            raise SystemExit(f"{where}: range must be an integer 8..128")
        if not isinstance(b.get("cooldown_hours"), (int, float)) or b["cooldown_hours"] < 0:
            raise SystemExit(f"{where}: cooldown_hours must be >= 0")
        last = 1.0
        for ph in b.get("phases", []):
            if not isinstance(ph.get("at_hp"), (int, float)) or not 0 < ph["at_hp"] < last:
                raise SystemExit(f"{where}: phases need at_hp between 0 and 1, strictly descending")
            last = ph["at_hp"]
            if not str(ph.get("say", "")).strip():
                raise SystemExit(f"{where}: every phase needs a say line")
            if ("minions" in ph) != ("count" in ph):
                raise SystemExit(f"{where}: a phase gives both minions and count, or neither")
            if "minions" in ph and (not re.fullmatch(ident, ph["minions"]) or not isinstance(ph["count"], int)
                                    or not 1 <= ph["count"] <= 12 or ph["minions"] in entities):
                raise SystemExit(f"{where}: minions must be a namespaced id (not a boss), count 1..12")
            if "enrage" in ph and (not isinstance(ph["enrage"], int) or not 0 <= ph["enrage"] <= 5):
                raise SystemExit(f"{where}: enrage must be a strength amplifier 0..5")
        rw = b.get("rewards", {})
        for f, n in rw.get("rep", {}).items():
            if not re.fullmatch(r"[a-z0-9_]+", f) or not isinstance(n, int):
                raise SystemExit(f"{where}: rewards.rep wants faction = integer")
        for coin, n in rw.get("coins", {}).items():
            if coin not in ("bronze", "silver", "gold", "stellar_gold") or not isinstance(n, int) or n < 1:
                raise SystemExit(f"{where}: rewards.coins wants bronze|silver|gold|stellar_gold = positive integer")
        if rw.get("core") and b["tier"] < 3:
            raise SystemExit(f"{where}: Skill Cores drop from tier 3 and up only")
        for d in b.get("drops", []):
            if not re.fullmatch(ident, str(d.get("item", ""))) or not isinstance(d.get("count"), int)                     or not 0 < d.get("chance", 0) <= 1:
                raise SystemExit(f"{where}: drops need item, integer count and chance in (0, 1]")
    # The entity tag the datapack side uses (kubejs/data/ttl/tags/entity_type/boss.json) lists exactly these bosses.
    tag = json.loads((ROOT / "pack" / "kubejs" / "data" / "ttl" / "tags" / "entity_type" / "boss.json").read_text(encoding="utf-8"))
    if set(tag["values"]) != entities:
        raise SystemExit("bosses.toml: kubejs/data/ttl/tags/entity_type/boss.json does not list exactly the [[boss]] entities")


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
    if "bosses" in data:
        check_bosses(data["bosses"], data.get("landmarks"))
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
