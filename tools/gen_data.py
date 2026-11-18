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


def check_bosses(bosses: dict, landmarks: dict | None, factions: dict | None = None) -> None:
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
            if factions is not None and f not in {x["id"] for x in factions.get("faction", [])}:
                raise SystemExit(f"{where}: rewards.rep names faction {f!r}, which is not in factions.toml")
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


def check_arrival(arrival: dict) -> None:
    # life/arrival.js grounds [life2] at x, z and TtlLife.toOverworld teleports there; a wrong type would only
    # show up as a bad `tp` at the first rebirth.
    spot = arrival.get("life2")
    if not isinstance(spot, dict):
        raise SystemExit("arrival.toml: [life2] missing")
    for key in ("x", "z", "yaw"):
        if not isinstance(spot.get(key), (int, float)) or isinstance(spot.get(key), bool):
            raise SystemExit(f"arrival.toml: life2.{key} must be a number")
    if not -180 <= spot["yaw"] <= 360:
        raise SystemExit("arrival.toml: life2.yaw is a Minecraft yaw in degrees (-180..360)")
    for key, top in (("search", 48), ("version", 1_000_000)):
        if not isinstance(spot.get(key), int) or isinstance(spot.get(key), bool) or not 0 <= spot[key] <= top or (key == "version" and spot[key] < 1):
            raise SystemExit(f"arrival.toml: life2.{key} must be a whole number" + (" from 0 to 48" if key == "search" else " from 1"))
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    if abs(spot["x"]) > canon["width"] or abs(spot["z"]) > canon["width"]:
        raise SystemExit(f"arrival.toml: life2 x/z ({spot['x']}, {spot['z']}) lies outside the {canon['width']}-block continent")


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

MASTER_COIN_LIST = ROOT / "pack" / "config" / "lightmanscurrency" / "MasterCoinList.json"


def coin_table(where: str, table, coins: list) -> None:
    if not isinstance(table, dict) or not table:
        raise SystemExit(f"{where}: must be a non-empty coin table like {{ silver = 3 }}")
    for coin, n in table.items():
        if coin not in coins or not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise SystemExit(f"{where}: {coin} = {n!r} (coins are {', '.join(coins)}; amounts are positive integers)")


def check_economy(eco: dict, data: dict) -> None:
    # economy/*.js read the coin chain, bounties and fees from here; the Lightman's Currency config must agree with
    # the coin chain, or the shops, ATMs and bounty payouts would count different money.
    coins = eco["coins"]["chain"]
    items, rates = eco["coins"]["item"], eco["coins"]["rate"]
    if set(items) != set(coins) or set(rates) != set(coins[1:]):
        raise SystemExit("economy.toml: [coins.item] needs every coin and [coins.rate] every coin but the first")
    for coin in coins:
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", items[coin]):
            raise SystemExit(f"economy.toml: coins.item.{coin} {items[coin]!r} is not a namespaced id")
        if coin in rates and (not isinstance(rates[coin], int) or rates[coin] < 2):
            raise SystemExit(f"economy.toml: coins.rate.{coin} must be an integer >= 2")
    if MASTER_COIN_LIST.exists():
        main = [c for c in json.loads(MASTER_COIN_LIST.read_text(encoding="utf-8"))["Chains"] if c["chain"] == "main"]
        if len(main) != 1:
            raise SystemExit("MasterCoinList.json: needs exactly one chain named main")
        core = main[0]["CoreChain"]
        want = [(items[c], None if i == 0 else rates[c]) for i, c in enumerate(coins)]
        have = [(e["Coin"], e.get("exchangeRate")) for e in core]
        if want != have:
            raise SystemExit(f"economy.toml [coins] and MasterCoinList.json main CoreChain disagree: {want} vs {have}")
    ranks = [r["id"] for r in eco["rank"]]
    if not ranks or eco["rank"][0]["points"] != 0 or len(set(ranks)) != len(ranks) or             [r["points"] for r in eco["rank"]] != sorted(r["points"] for r in eco["rank"]):
        raise SystemExit("economy.toml: [[rank]] ids must be unique and points ascending from 0")
    if eco["guild"].get("announce_rank") not in ranks:
        raise SystemExit("economy.toml: guild.announce_rank is not a rank id")
    landmarks = {lm["name"] for lm in data.get("landmarks", {}).get("landmark", [])}
    factions = {f["id"] for f in data.get("factions", {}).get("faction", [])}
    g = eco["guild"]
    # giver: desk (guild receptionists) or fuze (the guild master); Fuze's bounties are exactly the ones at
    # fuze_min_rank and above, so a receptionist never has to hand out a contract she may not let anyone accept.
    fuze_from = g.get("fuze_min_rank", ranks[-1])
    if fuze_from not in ranks:
        raise SystemExit("economy.toml: guild.fuze_min_rank is not a rank id")
    seen, per = set(), {"daily": 0, "weekly": 0}
    for b in eco["bounty"]:
        where = f"economy.toml: bounty {b.get('id', '?')}"
        if not re.fullmatch(r"[a-z0-9_]+", b.get("id", "")) or b["id"] in seen:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        seen.add(b["id"])
        if b.get("kind") not in ("kill", "deliver", "visit") or b.get("period") not in per:
            raise SystemExit(f"{where}: kind is kill|deliver|visit and period daily|weekly")
        if b.get("min_rank") not in ranks:
            raise SystemExit(f"{where}: min_rank is not a rank id")
        giver = b.get("giver", "desk")
        if giver not in ("desk", "fuze"):
            raise SystemExit(f"{where}: giver is desk or fuze")
        if (giver == "fuze") != (ranks.index(b["min_rank"]) >= ranks.index(fuze_from)):
            raise SystemExit(f"{where}: giver {giver} but min_rank {b['min_rank']} (Fuze gives rank {fuze_from} and up, "
                             f"the desk everything below)")
        if not all(isinstance(b.get(k), int) and b[k] >= 0 for k in ("count", "points", "weight")) or b["count"] < 1:
            raise SystemExit(f"{where}: count >= 1, points and weight >= 0 (integers)")
        if b["kind"] == "visit":
            if landmarks and b["target"] not in landmarks:
                raise SystemExit(f"{where}: target {b['target']!r} is not a landmark in landmarks.toml")
        elif not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", b.get("target", "")):
            raise SystemExit(f"{where}: target must be a namespaced id")
        if "region" in b and (b["kind"] != "kill" or (factions and b["region"] not in factions)):
            raise SystemExit(f"{where}: region is a faction id and only for kill bounties")
        coin_table(f"{where} reward.coins", b.get("reward", {}).get("coins"), coins)
        for f, n in b["reward"].get("rep", {}).items():
            if (factions and f not in factions) or not isinstance(n, int) or n < 1:
                raise SystemExit(f"{where}: reward.rep.{f} = {n!r} (a faction id and a positive integer)")
        if b["weight"] > 0:
            per[b["period"]] += 1
    first = ranks[0]
    for giver, period, n in (("desk", "daily", g["daily"]), ("desk", "weekly", g["weekly"]),
                             ("fuze", "daily", g.get("fuze_daily", 0)), ("fuze", "weekly", g.get("fuze_weekly", 0))):
        pool = [b for b in eco["bounty"] if b.get("giver", "desk") == giver and b["period"] == period and b["weight"] > 0]
        if len(pool) < n or (giver == "desk" and period == "daily" and not any(b["min_rank"] == first for b in pool)):
            raise SystemExit(f"economy.toml: needs >= {n} {giver} {period} bounties with weight > 0 "
                             f"(the desk's daily ones need at least one for rank {first})")
    if not isinstance(g.get("fuze_turnin_at_desk", False), bool):
        raise SystemExit("economy.toml: guild.fuze_turnin_at_desk is true or false")
    for name, table in eco["sinks"].items():
        coin_table(f"economy.toml: sinks.{name}", table, coins)
    for block in eco["merit"]["blocks"]:
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", block):
            raise SystemExit(f"economy.toml: merit block {block!r} is not a namespaced id")


def snbt_value(path: Path, key: str) -> str:
    # The value of a top-level or nested `key: value` line in an FTB .snbt config (FTB Library writes one per line).
    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"{path.relative_to(ROOT)}: no {key} line")
    return m.group(1)


def check_nations(nat: dict, data: dict) -> None:
    # nations/*.js read the rules and ranks from here. The two FTB configs implement half of them (party size, the
    # claim dimension, the per-soul and per-party chunk limits); they must agree or the nation rules silently differ
    # from what FTB enforces.
    r, v, d, t = nat["rules"], nat["value"], nat["diplomacy"], nat["treasury"]
    ints = ("member_cap", "min_members", "name_min", "name_max", "home_rep", "base_chunks", "chunks_per_member", "poll_ticks", "value_ticks")
    for k in ints:
        if not is_int(r.get(k)) or r[k] < 0:
            raise SystemExit(f"nations.toml: rules.{k} must be a non-negative integer")
    if not 2 <= r["min_members"] <= r["member_cap"] or r["name_min"] < 1 or r["name_min"] > r["name_max"]:
        raise SystemExit("nations.toml: rules needs 2 <= min_members <= member_cap and 1 <= name_min <= name_max")
    if r["poll_ticks"] < 20 or r["value_ticks"] < r["poll_ticks"] or r["base_chunks"] < 1 or r["chunks_per_member"] < r["base_chunks"]:
        raise SystemExit("nations.toml: rules.poll_ticks >= 20, value_ticks >= poll_ticks, base_chunks >= 1, chunks_per_member >= base_chunks")
    if not re.fullmatch(r"ttl\.[a-z0-9_.]+", r.get("charter_stage", "")):
        raise SystemExit("nations.toml: rules.charter_stage must be a ttl.* stage")
    coins = data.get("economy", {}).get("coins", {}).get("chain")
    if coins:
        coin_table("nations.toml: rules.charter_cost", r.get("charter_cost"), coins)
        sink = data["economy"].get("sinks", {}).get("charter")
        if sink != r["charter_cost"]:
            print(f"warn: nations.toml rules.charter_cost {r['charter_cost']} differs from economy.toml sinks.charter {sink}",
                  file=sys.stderr)
    for k in ("chunk_value", "build_value", "coins_per_value"):
        if not is_int(v.get(k)) or v[k] < (1 if k == "coins_per_value" else 0):
            raise SystemExit(f"nations.toml: value.{k} must be an integer (coins_per_value >= 1)")
    ranks = nat["rank"]
    ids = [x["id"] for x in ranks]
    if not ranks or ranks[0]["value"] != 0 or len(set(ids)) != len(ids) or [x["value"] for x in ranks] != sorted(x["value"] for x in ranks):
        raise SystemExit("nations.toml: [[rank]] ids must be unique and value ascending from 0")
    for x in ranks:
        if not re.fullmatch(r"[a-z0-9_]+", x["id"]) or not x.get("title") or not is_int(x.get("chunks")) or x["chunks"] < 0:
            raise SystemExit(f"nations.toml: rank {x.get('id')!r} needs an [a-z0-9_] id, a title and chunks >= 0")
    if not isinstance(t.get("enabled"), bool) or not isinstance(t.get("upkeep"), bool):
        raise SystemExit("nations.toml: treasury.enabled and treasury.upkeep are true or false")
    if not is_int(d.get("war_notice_hours")) or d["war_notice_hours"] < 0:
        raise SystemExit("nations.toml: diplomacy.war_notice_hours must be a non-negative integer")
    chunks_cfg = ROOT / "pack" / "config" / "ftbchunks-world.snbt"
    teams_cfg = ROOT / "pack" / "config" / "ftbteams-server.snbt"
    if chunks_cfg.exists() and teams_cfg.exists():
        if snbt_value(teams_cfg, "max_party_size") != str(r["member_cap"]):
            raise SystemExit("nations.toml rules.member_cap != max_party_size in pack/config/ftbteams-server.snbt")
        if snbt_value(chunks_cfg, "max_claimed_chunks") != str(r["base_chunks"]):
            raise SystemExit("nations.toml rules.base_chunks != max_claimed_chunks in pack/config/ftbchunks-world.snbt")
        if snbt_value(chunks_cfg, "party_limit_mode") != '"sum"':
            raise SystemExit('ftbchunks-world.snbt party_limit_mode must be "sum" (a nation claims members x allowance)')
        wl = snbt_value(chunks_cfg, "claim_dimension_whitelist")
        if '"minecraft:overworld"' not in wl or "ttl:" in wl:
            raise SystemExit('ftbchunks-world.snbt claim_dimension_whitelist must list minecraft:overworld and no ttl:* '
                             "dimension (claims are Life 2 only)")


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
    if "events" in data:
        check_events(data["events"])
    if "arrival" in data:
        check_arrival(data["arrival"])
    if "landmarks" in data:
        check_landmarks(data["landmarks"])
    if "carryover" in data:
        check_carryover(data["carryover"], data.get("karma"))
    if "factions" in data:
        check_factions(data["factions"], data.get("karma"))
    if "bosses" in data:
        check_bosses(data["bosses"], data.get("landmarks"), data.get("factions"))
    if "economy" in data:
        check_economy(data["economy"], data)
    if "nations" in data:
        check_nations(data["nations"], data)
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
