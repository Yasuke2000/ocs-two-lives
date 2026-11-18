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


def check_events(events: dict) -> None:
    # events/director.js schedules these, events/favor.js reads [favor]; a typo would silently drop an event or a blessing.
    ident, rule, value = r"[a-z0-9_]+", r"[A-Za-z][A-Za-z0-9_]*", r"[A-Za-z0-9_.-]+"
    sound = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    seen = set()
    for ev in events.get("event", []):
        eid = ev.get("id", "")
        where = f"events.toml: {eid or '?'}"
        if not re.fullmatch(ident, str(eid)) or eid in seen:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        seen.add(eid)
        every = ev.get("every")
        if every is not None:
            if not isinstance(every, dict) or set(every) not in ({"days"}, {"hours"}) or not isinstance(next(iter(every.values())), int) or next(iter(every.values())) < 1:
                raise SystemExit(f"{where}: every must be {{ days = n }} or {{ hours = n }} (n >= 1)")
            if "days" in every and not (isinstance(ev.get("at_hour"), int) and 0 <= ev["at_hour"] <= 23):
                raise SystemExit(f"{where}: a days schedule needs at_hour 0-23")
            if "days" in every and ev.get("at_hour", 0) + ev.get("jitter_hours", 0) >= 24:
                raise SystemExit(f"{where}: at_hour + jitter_hours must stay below 24")
        if not isinstance(ev.get("duration_minutes", 0), int) or ev.get("duration_minutes", 0) < 0:
            raise SystemExit(f"{where}: duration_minutes must be an integer >= 0")
        if ev.get("scope") not in ("region", "world", "player"):
            raise SystemExit(f"{where}: scope must be region, world or player")
        if ev.get("audience", "all") not in ("all", "life1", "life2"):
            raise SystemExit(f"{where}: audience must be all, life1 or life2")
        ann = ev.get("announce")
        if not isinstance(ann, dict) or not str(ann.get("title", "")).strip() or not str(ann.get("chat", "")).strip():
            raise SystemExit(f"{where}: announce needs a title and a chat line")
        if ann.get("sound") and not re.fullmatch(sound, ann["sound"]):
            raise SystemExit(f"{where}: announce.sound must be a namespaced sound id")
        act = ev.get("action", {})
        if not isinstance(act, dict) or not set(act) <= {"favor", "boss", "gamerule", "restore"}:
            raise SystemExit(f"{where}: action keys are favor, boss, gamerule, restore")
        rules = act.get("gamerule", {})
        for key, val in rules.items():
            if not re.fullmatch(rule, key) or not re.fullmatch(value, str(val).lower() if isinstance(val, bool) else str(val)):
                raise SystemExit(f"{where}: gamerule {key} = {val!r} is not a valid rule/value")
            if key not in act.get("restore", {}):
                raise SystemExit(f"{where}: gamerule {key} needs a restore value")
        if "restore" in act and not rules:
            raise SystemExit(f"{where}: restore without a gamerule")
    director = events.get("director", {})
    for key in ("loop_ticks", "poll_ticks", "window_hours", "retry_minutes", "min_gap_minutes", "max_per_day", "max_active"):
        if not isinstance(director.get(key), int) or director[key] < 1:
            raise SystemExit(f"events.toml: [director] {key} must be a positive integer")
    favor = events.get("favor", {})
    for key, lo, hi in (("bottom_pct", 1, 100), ("min_hours", 0, 168), ("cooldown_days", 0, 3650), ("offer_hours", 1, 720), ("offer_count", 1, 5)):
        if not isinstance(favor.get(key), int) or not lo <= favor[key] <= hi:
            raise SystemExit(f"events.toml: [favor] {key} must be an integer {lo}-{hi}")
    choices = favor.get("choices", [])
    blessings = favor.get("choice", {})
    if not choices or len(set(choices)) != len(choices):
        raise SystemExit("events.toml: [favor] choices must list each blessing once")
    for cid in choices:
        b = blessings.get(cid)
        if not b or not str(b.get("label", "")).strip() or not re.fullmatch(sound, str(b.get("icon", ""))):
            raise SystemExit(f"events.toml: [favor.choice.{cid}] needs a label and an icon (namespaced item id)")
    if len(choices) < favor.get("offer_count", 0):
        raise SystemExit("events.toml: [favor] offer_count exceeds the number of choices")
    for sk in blessings.get("resistance", {}).get("skills", []):
        if not re.fullmatch(sound, sk):
            raise SystemExit(f"events.toml: resistance skill {sk!r} is not a namespaced id")
    for e in blessings.get("protection", {}).get("effects", []):
        if not re.fullmatch(sound, str(e.get("id", ""))) or not isinstance(e.get("seconds"), int) or e["seconds"] < 1:
            raise SystemExit("events.toml: protection effects need a namespaced id and seconds >= 1")
    for i in blessings.get("relic", {}).get("items", []):
        if not re.fullmatch(sound, str(i.get("id", ""))) or not isinstance(i.get("count", 1), int) or i.get("count", 1) < 1:
            raise SystemExit("events.toml: relic items need a namespaced id and count >= 1")


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
    if "events" in data:
        check_events(data["events"])
    if "landmarks" in data:
        check_landmarks(data["landmarks"])
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
