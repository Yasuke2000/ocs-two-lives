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


def check_factions(fac: dict, karma: dict | None) -> None:
    # rep/rep.js reads these by name; a typo in a band, region, race or axis would silently seed or gate nothing.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    landmarks = {lm["name"] for lm in canon["landmarks"]}
    order = ("hostile", "unfriendly", "friendly", "honored", "exalted")
    rules = fac["rules"]
    lo, hi = rules["min"], rules["max"]
    if not (isinstance(lo, int) and isinstance(hi, int) and lo < 0 < hi):
        raise SystemExit("factions.toml: rules.min must be negative and rules.max positive integers")
    for key in ("guard_attack_at", "shop_refuse_at"):
        if rules[key] not in ("hostile", "unfriendly"):
            raise SystemExit(f"factions.toml: rules.{key} must be hostile or unfriendly")
    for key in ("decay_days", "log_size", "seed_axis_cap"):
        if not isinstance(rules[key], int) or rules[key] < 1:
            raise SystemExit(f"factions.toml: rules.{key} must be a positive integer")

    def check_bands(where: str, bands: dict) -> None:
        if sorted(bands) != sorted(order):
            raise SystemExit(f"{where}: needs exactly {', '.join(order)}")
        values = [bands[b] for b in order]
        if any(not isinstance(v, int) for v in values) or values != sorted(set(values)):
            raise SystemExit(f"{where}: thresholds must be strictly increasing integers")
        if not (lo <= values[0] < 0 < values[2] and values[-1] <= hi):
            raise SystemExit(f"{where}: hostile/unfriendly must be below 0, friendly and up above 0, all within min..max")

    check_bands("factions.toml [bands]", fac["bands"])
    axes = set(karma["axes"]) if karma else None
    seen = set()
    for f in fac["faction"]:
        fid = f.get("id", "")
        where = f"factions.toml: {fid or '?'}"
        if not re.fullmatch(r"[a-z][a-z_]*", fid) or fid in seen:
            raise SystemExit(f"{where}: id must be unique [a-z_]")
        seen.add(fid)
        if not str(f.get("title", "")).strip():
            raise SystemExit(f"{where}: needs a title")
        if "region" in f and f["region"] not in canon["regions"]:
            raise SystemExit(f"{where}: region {f['region']!r} is not a key of canon_regions.json")
        if "capital" in f and f["capital"] not in landmarks:
            raise SystemExit(f"{where}: capital {f['capital']!r} is not a canon landmark")
        if "bands" in f:
            check_bands(where + " bands", f["bands"])
        for tag in f.get("npc_tags", []):
            if not re.fullmatch(r"[a-z0-9_.]+", tag):
                raise SystemExit(f"{where}: npc tag {tag!r} must be [a-z0-9_.] (vanilla entity tags)")
        for t in f.get("npc_types", []):
            if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", t):
                raise SystemExit(f"{where}: npc type {t!r} must be a namespaced entity id")
        kp = f.get("kill_penalty", {})
        if sorted(kp) != ["npc", "player"] or any(not isinstance(v, int) or v < 0 for v in kp.values()):
            raise SystemExit(f"{where}: kill_penalty needs npc and player, non-negative integers")
        if not isinstance(f.get("decay_per_week"), int) or f["decay_per_week"] < 0:
            raise SystemExit(f"{where}: decay_per_week must be a non-negative integer")
        seed = f.get("seed", {})
        for race, n in seed.get("race", {}).items():
            if not re.fullmatch(r"[a-z_]+", race) or not isinstance(n, int) or not lo <= n <= hi:
                raise SystemExit(f"{where}: seed race {race!r} = {n!r} must be a race id and an integer within min..max")
        for axis, n in seed.get("axis", {}).items():
            if axes is not None and axis not in axes:
                raise SystemExit(f"{where}: seed axis {axis!r} is not a karma axis ({', '.join(sorted(axes))})")
            if not isinstance(n, int) or not lo <= n <= hi:
                raise SystemExit(f"{where}: seed axis {axis!r} must be an integer within min..max")
        if "dark" in seed and (not isinstance(seed["dark"], int) or not lo <= seed["dark"] <= hi):
            raise SystemExit(f"{where}: seed dark must be an integer within min..max")
    ren = fac["renown"]
    if not isinstance(ren.get("min"), int):
        raise SystemExit("factions.toml: renown.min must be an integer")
    tiers = {t["id"] for t in karma["tiers"]} if karma else None
    wanted = {"tier": tiers, "band": {"hostile", "unfriendly", "neutral", "friendly", "honored", "exalted"},
              "unique": {"common", "rare", "legendary"}}
    for table, keys in wanted.items():
        values = ren.get(table)
        if not isinstance(values, dict):
            raise SystemExit(f"factions.toml: [renown] {table} must be a table")
        for key, n in values.items():
            if keys is not None and key not in keys:
                raise SystemExit(f"factions.toml: renown.{table} has unknown key {key!r} (one of {', '.join(sorted(keys))})")
            if not isinstance(n, int):
                raise SystemExit(f"factions.toml: renown.{table}.{key} must be an integer")
        if keys is not None and set(values) != keys:
            raise SystemExit(f"factions.toml: renown.{table} must list every one of {', '.join(sorted(keys))}")
    for table in ("boss", "stage"):
        values = ren.get(table)
        if not isinstance(values, dict):
            raise SystemExit(f"factions.toml: [renown] {table} must be a table")
        for key, n in values.items():
            if not re.fullmatch(r"ttl\.[a-z0-9_.]+", key) or not isinstance(n, int):
                raise SystemExit(f"factions.toml: renown.{table} entry {key!r} must be a ttl.* stage and an integer")
    mirrors = [f["id"] for f in fac["faction"] if f.get("tensura_mirror")]
    if len(mirrors) > 1:
        raise SystemExit(f"factions.toml: only one faction can mirror into Tensura's reputation, found {', '.join(mirrors)}")


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
    if not isinstance(fw.get("natural_allow"), list):
        raise SystemExit("bosses.toml: [framework] natural_allow must be a list (use [] for none)")
    all_ids = [b.get("id") for b in bosses.get("boss", [])]
    for key in ("bindable", "natural_allow"):
        for bid in fw[key]:
            if bid not in all_ids:
                raise SystemExit(f"bosses.toml: [framework] {key} names unknown boss {bid!r}")
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
    if "carryover" in data:
        check_carryover(data["carryover"], data.get("karma"))
    if "factions" in data:
        check_factions(data["factions"], data.get("karma"))
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
