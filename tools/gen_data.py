#!/usr/bin/env python3
"""Generate pack/kubejs/server_scripts/ttl/generated/data.js from design/data/*.toml.

Gameplay numbers live in TOML so balancing never needs a code change. The scripts read them as `TtlData`.
design/builds/<name>.toml (canon-location builds, life/builds.js) is read into `TtlData.builds`, and the ground
footprint of every build's structure files goes to generated/builds.js (`TtlBuildFootprints`).
Usage: gen_data.py            write the files
       gen_data.py --check    exit 1 if a file is out of date (used by validate.py)
"""
import functools
import hashlib
import inspect
import json
import math
import os
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))  # python -I (validate.py) does not put the script's folder on the path
import nbt  # noqa: E402
import anchor_refs  # noqa: E402
import anchors_env  # noqa: E402 (tests/anchors.env, WP-L6)

SOURCES = ROOT / "design" / "data"
BUILDS = ROOT / "design" / "builds"
TARGET = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "data.js"
ANCHORS_JS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "anchors.js"
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
    check_absorb(skills, absorb)
    pick = skills.get("legend_pick", {})
    if not isinstance(pick.get("tiers", []), list) or not all(isinstance(t, str) for t in pick.get("tiers", [])):
        raise SystemExit("skills.toml: legend_pick.tiers must be a list of karma tier ids")
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


def check_absorb(skills: dict, absorb: dict) -> None:
    # absorb/absorb.js reads these by name; a typo would silently turn a route or a ratio off.
    def number(where: str, table: dict, key: str, whole: bool = False) -> None:
        if key not in table:
            return
        v = table[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or (whole and int(v) != v):
            raise SystemExit(f"skills.toml: {where}.{key} must be a number >= 0{' (whole)' if whole else ''}")

    for key in ("min_ep_ratio", "max_ep_ratio", "cooldown_hours", "offer_minutes", "pact_minutes", "combat_log_seconds"):
        number("absorb", absorb, key)
    for key in ("legendary_per_kill", "copies_per_kill"):
        number("absorb", absorb, key, True)
    known = set(skills.get("transfer", {}).get("routes", []))
    legendary = set(skills["legendary"]["skills"])
    for route in ("duel", "war", "bequest", "awakening"):
        conf = absorb.get(route)
        if conf is None:
            continue
        if not isinstance(conf, dict):
            raise SystemExit(f"skills.toml: absorb.{route} must be a table")
        if route not in known:
            raise SystemExit(f"skills.toml: absorb.{route} is not listed in transfer.routes")
        for key in ("enabled", "requires_absorber", "legendary", "copies", "lethal", "use_nations", "staff_flags",
                    "legendary_only", "claim", "challenge", "spend_slot"):
            if key in conf and not isinstance(conf[key], bool):
                raise SystemExit(f"skills.toml: absorb.{route}.{key} must be true or false")
        for key in ("min_ep_ratio", "max_ep_ratio", "cooldown_hours", "legendary_per_kill", "copies_per_kill"):
            number(f"absorb.{route}", conf, key)
        dims = conf.get("dimensions", [])
        if not isinstance(dims, list) or not all(isinstance(d, str) and re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", d) for d in dims):
            raise SystemExit(f"skills.toml: absorb.{route}.dimensions must be a list of dimension ids like tensura:labyrinth")
        low, high = conf.get("min_ep_ratio", absorb.get("min_ep_ratio", 0)), conf.get("max_ep_ratio", absorb.get("max_ep_ratio", 0))
        if high and low > high:
            raise SystemExit(f"skills.toml: absorb.{route}: min_ep_ratio {low} is above max_ep_ratio {high}")
        ex = conf.get("exclude_dimensions", [])
        if not isinstance(ex, list) or not all(isinstance(d, str) and re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", d) for d in ex):
            raise SystemExit(f"skills.toml: absorb.{route}.exclude_dimensions must be a list of dimension ids")
    lia = absorb.get("liability")
    if lia is not None:
        if not isinstance(lia, dict):
            raise SystemExit("skills.toml: absorb.liability must be a table")
        for key in ("enabled", "restore", "no_drops"):
            if key in lia and not isinstance(lia[key], bool):
                raise SystemExit(f"skills.toml: absorb.liability.{key} must be true or false")
        for key in ("max_blocks", "restore_per_tick", "hold_days"):
            number("absorb.liability", lia, key, True)
        for route in lia.get("routes", []):
            if route not in ("duel", "awakening"):
                raise SystemExit(f"skills.toml: absorb.liability.routes: {route!r} (duel, awakening: the routes with a pact someone starts)")
        for place in lia.get("places", []):
            if place not in ("claims", "towns", "builds", "landmarks"):
                raise SystemExit(f"skills.toml: absorb.liability.places: {place!r} (claims, towns, builds, landmarks)")
        if not isinstance(lia.get("exempt", []), list):
            raise SystemExit("skills.toml: absorb.liability.exempt must be a list of build/landmark names")
        for key in ("fee_per_block", "max_fee"):
            table = lia.get(key, {})
            if not isinstance(table, dict) or not table or not all(c in ("bronze", "silver", "gold", "stellar") and isinstance(n, int) and not isinstance(n, bool) and n >= 0 for c, n in table.items()):
                raise SystemExit(f"skills.toml: absorb.liability.{key} must be a coin table like {{ bronze = 5 }}")
    claims = absorb.get("awakening", {}).get("claim_skills", {})
    for kind, names in claims.items():
        if kind not in ("true_demon_lord", "true_hero"):
            raise SystemExit(f"skills.toml: absorb.awakening.claim_skills.{kind}: unknown kind (true_demon_lord, true_hero)")
        for name in names:
            if name not in legendary:
                raise SystemExit(f"skills.toml: absorb.awakening.claim_skills.{kind} lists {name}, which is not a Legendary unique")


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
    # Iron's schools whose casts are vetoed in the Mortal dimensions (life/mortal_banned.js, SpellPreCastEvent).
    schools = banned.get("spell_schools", [])
    if not isinstance(schools, list) or any(not isinstance(v, str) or not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", v) for v in schools):
        raise SystemExit("mortal_banned.toml: spell_schools must be a list of school ids, like irons_spellbooks:blood")


ROAD_FIELDS = {"chaos", "order", "craft", "faith", "balance", "weight", "times", "rep", "victim", "renown",
               "witnessed_only", "story", "extra"}


def check_roads(roads: dict, factions: dict | None, karma: dict | None) -> None:
    # roads/roads.js (TtlRoads) pays these; a typo in a faction or an axis would silently cost nothing.
    for key in ("witness", "karma2", "balance", "discord", "defaults"):
        if not isinstance(roads.get(key), dict):
            raise SystemExit(f"roads.toml: [{key}] missing")
    if not (isinstance(roads["witness"].get("radius"), int) and roads["witness"]["radius"] > 0):
        raise SystemExit("roads.toml: [witness] radius must be a positive int")
    axes = roads["karma2"].get("axes")
    known_axes = set((karma or {}).get("axes", {}).keys())
    if not isinstance(axes, list) or not axes or (known_axes and not set(axes) <= known_axes):
        raise SystemExit(f"roads.toml: [karma2] axes must be karma.toml axes ({', '.join(sorted(known_axes))})")
    if not is_num(roads["karma2"].get("mult")) or roads["karma2"]["mult"] < 0:
        raise SystemExit("roads.toml: [karma2] mult must be a number >= 0")
    for k in ("dark_cap_per_day", "light_cap_per_day"):
        if not isinstance(roads["balance"].get(k), int) or roads["balance"][k] < 0:
            raise SystemExit(f"roads.toml: [balance] {k} must be an int >= 0")
    facs = {f["id"] for f in (factions or {}).get("faction", [])}
    seen = set()
    for c in roads.get("choice", []):
        cid = str(c.get("id", ""))
        if not re.fullmatch(r"[a-z0-9_]+\.[a-z0-9_]+", cid):
            raise SystemExit(f"roads.toml: choice id {cid!r} must be <system>.<act> (lowercase)")
        if cid in seen:
            raise SystemExit(f"roads.toml: choice {cid} defined twice")
        seen.add(cid)
        routes = [r for r in ("good", "grey", "dark") if r in c]
        if not routes:
            raise SystemExit(f"roads.toml: choice {cid} has no route (good, grey or dark)")
        if c.get("fair") not in routes:
            raise SystemExit(f"roads.toml: choice {cid} fair = {c.get('fair')!r} must name one of its routes {routes}")
        for r in routes:
            route = c[r]
            where = f"roads.toml: choice {cid} route {r}"
            unknown = set(route) - ROAD_FIELDS
            if unknown:
                raise SystemExit(f"{where}: unknown field(s) {sorted(unknown)} (known: {sorted(ROAD_FIELDS)})")
            for ax in ("chaos", "order", "craft", "faith"):
                if ax in route and (not isinstance(route[ax], int) or ax not in axes):
                    raise SystemExit(f"{where}: {ax} must be an int and a [karma2] axis")
            if route.get("balance", "none") not in ("dark_deed", "light_deed", "none"):
                raise SystemExit(f"{where}: balance must be dark_deed, light_deed or none")
            if r == "dark" and route.get("balance") == "light_deed":
                raise SystemExit(f"{where}: a dark route cannot note a light deed")
            for f, n in (route.get("rep") or {}).items():
                if facs and f not in facs:
                    raise SystemExit(f"{where}: unknown faction {f}")
                if not isinstance(n, int):
                    raise SystemExit(f"{where}: rep.{f} must be an int")
            for k in ("victim", "renown", "times"):
                if k in route and not isinstance(route[k], int):
                    raise SystemExit(f"{where}: {k} must be an int")
            if r == "dark" and int(route.get("chaos", 0)) <= 0:
                raise SystemExit(f"{where}: a dark route always costs karma (chaos > 0, rule R13)")


ITEM_ID = re.compile(r"[a-z0-9_.-]+:[a-z0-9_/.-]+")


def check_artifice(art: dict, data: dict) -> None:
    # artifice/*.js reads these by name; a typo in an id, a faction, a band or a road would silently do nothing in game.
    where = "artifice.toml"
    anchor_refs.resolve_data({"artifice": art})
    facs = {f["id"] for f in data.get("factions", {}).get("faction", [])}
    bands = {"hostile", "unfriendly", "neutral", "friendly", "honored", "exalted"}
    coins = data.get("economy", {}).get("coins", {}).get("chain", [])
    choices = {c["id"]: c for c in data.get("roads", {}).get("choice", [])}

    def item(label: str, v) -> None:
        if not isinstance(v, str) or not ITEM_ID.fullmatch(v):
            raise SystemExit(f"{where}: {label} {v!r} is not a full id like mod:thing")

    def rep_table(label: str, rep) -> None:
        for f, n in (rep or {}).items():
            if facs and f not in facs:
                raise SystemExit(f"{where}: {label} names unknown faction {f}")
            if not is_int(n):
                raise SystemExit(f"{where}: {label}.{f} must be an int")

    def items_table(label: str, table) -> None:
        if not isinstance(table, dict) or not table:
            raise SystemExit(f"{where}: {label} must be a non-empty table {{ \"mod:item\" = n }}")
        for k, n in table.items():
            item(label, k)
            if not is_int(n) or n < 1:
                raise SystemExit(f"{where}: {label} {k} = {n!r} must be a positive int")

    for key in ("bench", "charter", "points", "made_by", "commissions", "engrave", "curse", "schematics", "steal"):
        if not isinstance(art.get(key), dict):
            raise SystemExit(f"{where}: [{key}] missing")
    item("[bench] block", art["bench"].get("block"))
    if not is_int(art["bench"].get("reach")) or not 1 <= art["bench"]["reach"] <= 8:
        raise SystemExit(f"{where}: [bench] reach must be an int 1..8")
    for k in ("center", "ring"):
        item(f"[bench] recipe.{k}", (art["bench"].get("recipe") or {}).get(k))
    if not is_int(art["charter"].get("schematics")) or art["charter"]["schematics"] < 1:
        raise SystemExit(f"{where}: [charter] schematics must be a positive int")
    item("[charter] schematic_tag", art["charter"].get("schematic_tag"))
    item("[charter] item", art["charter"].get("item"))

    ranks = art.get("rank", [])
    if [r.get("id") for r in ranks] != list(range(1, len(ranks) + 1)) or not ranks:
        raise SystemExit(f"{where}: [[rank]] ids must be 1, 2, 3 ... in order")
    last = -1
    for r in ranks:
        label = f"rank {r['id']}"
        if not str(r.get("title", "")).strip():
            raise SystemExit(f"{where}: {label} needs a title")
        for k in ("points", "constructs", "muster", "tier", "renown"):
            if not is_int(r.get(k)) or r[k] < 0:
                raise SystemExit(f"{where}: {label} {k} must be an int >= 0")
        if r["points"] <= last:
            raise SystemExit(f"{where}: {label} points must rise rank by rank")
        last = r["points"]
        if not 1 <= r["tier"] <= 4:
            raise SystemExit(f"{where}: {label} tier must be 1..4")
        req = r.get("requires_any")
        if req is not None:
            for s in req.get("skills", []):
                item(f"{label} requires_any.skills", s)
            for f, b in (req.get("bands") or {}).items():
                if (facs and f not in facs) or b not in bands:
                    raise SystemExit(f"{where}: {label} requires_any.bands {f} = {b!r} (faction and band must exist)")

    pts = art["points"]
    for k in ("weekly_cap", "craft_weekly_cap", "engrave", "metal_first_soul", "metal_first_server", "construct", "engine",
              "engine_commons_mult", "event"):
        if not is_int(pts.get(k)) or pts[k] < 0:
            raise SystemExit(f"{where}: [points] {k} must be an int >= 0")
    if not (isinstance(pts.get("commission"), list) and len(pts["commission"]) == 4 and all(is_int(n) and n >= 0 for n in pts["commission"])):
        raise SystemExit(f"{where}: [points] commission must list 4 ints (tier 1..4)")
    metals = pts.get("craft") or {}
    if not metals or any(not re.fullmatch(r"[a-z_]+", m) or not is_int(n) or n < 0 for m, n in metals.items()):
        raise SystemExit(f"{where}: [points.craft] must map metal names to ints >= 0")
    if "{name}" not in str(art["made_by"].get("lore", "")):
        raise SystemExit(f"{where}: [made_by] lore must contain {{name}}")
    if not is_int(art["made_by"].get("poll_ticks")) or art["made_by"]["poll_ticks"] < 1:
        raise SystemExit(f"{where}: [made_by] poll_ticks must be a positive int")

    if not is_int(art["commissions"].get("board")) or art["commissions"]["board"] < 1:
        raise SystemExit(f"{where}: [commissions] board must be a positive int")
    seen = set()
    tiers = set()
    for c in art.get("commission", []):
        cid = str(c.get("id", ""))
        label = f"commission {cid}"
        if not re.fullmatch(r"[a-z0-9_]+", cid) or cid in seen:
            raise SystemExit(f"{where}: commission id {cid!r} must be lowercase and unique")
        seen.add(cid)
        if not str(c.get("title", "")).strip():
            raise SystemExit(f"{where}: {label} needs a title")
        if not is_int(c.get("tier")) or not 1 <= c["tier"] <= 4:
            raise SystemExit(f"{where}: {label} tier must be 1..4")
        tiers.add(c["tier"])
        if c.get("giver") not in ("kaijin", "smithy", "vester"):
            raise SystemExit(f"{where}: {label} giver must be kaijin, smithy or vester")
        item(f"{label} item", c.get("item"))
        if not is_int(c.get("count")) or c["count"] < 1 or not is_int(c.get("weight")) or c["weight"] < 1:
            raise SystemExit(f"{where}: {label} count and weight must be positive ints")
        if not isinstance(c.get("made_by"), bool):
            raise SystemExit(f"{where}: {label} made_by must be true or false")
        rw = c.get("reward") or {}
        if coins:
            coin_table(f"{where}: {label} reward.coins", rw.get("coins"), coins)
        rep_table(f"{label} reward.rep", rw.get("rep"))
        if "schematic" in rw:
            item(f"{label} reward.schematic", rw["schematic"])
        if "points" in rw and (not is_int(rw["points"]) or rw["points"] < 0):
            raise SystemExit(f"{where}: {label} reward.points must be an int >= 0")
    if tiers != {1, 2, 3, 4}:
        raise SystemExit(f"{where}: every commission tier 1..4 needs at least one [[commission]] (have {sorted(tiers)})")

    item("[engrave] chisel", art["engrave"].get("chisel"))
    for e in art.get("engraving", []):
        item("engraving id", e.get("id"))
        if not is_int(e.get("rank")) or not 1 <= e["rank"] <= len(ranks):
            raise SystemExit(f"{where}: engraving {e.get('id')} rank must be 1..{len(ranks)}")
        cost = e.get("cost") or {}
        if "coins" in cost and coins:
            coin_table(f"{where}: engraving {e['id']} cost.coins", cost["coins"], coins)
        if "items" in cost:
            items_table(f"engraving {e['id']} cost.items", cost["items"])
    rids = set()
    for r in art.get("recipe", []):
        rid = str(r.get("id", ""))
        if not re.fullmatch(r"[a-z0-9_]+", rid) or rid in rids:
            raise SystemExit(f"{where}: recipe id {rid!r} must be lowercase and unique")
        rids.add(rid)
        if not is_int(r.get("rank")) or not 0 <= r["rank"] <= len(ranks):
            raise SystemExit(f"{where}: recipe {rid} rank must be 0..{len(ranks)}")
        if r.get("station") not in ("bench", "altar"):
            raise SystemExit(f"{where}: recipe {rid} station must be bench or altar")
        item(f"recipe {rid} output", r.get("output"))
        if not is_int(r.get("count")) or r["count"] < 1:
            raise SystemExit(f"{where}: recipe {rid} count must be a positive int")
        items_table(f"recipe {rid} inputs", r.get("inputs"))
        if "coins" in r and coins:
            coin_table(f"{where}: recipe {rid} coins", r["coins"], coins)
        if "road" in r:
            cid, _, road = str(r["road"]).rpartition(".")
            if cid not in choices or road not in choices[cid]:
                raise SystemExit(f"{where}: recipe {rid} road {r['road']!r} is not a roads.toml choice route")

    cu = art["curse"]
    item("[curse] item", cu.get("item"))
    if not is_num(cu.get("chance")) or not 0 < cu["chance"] <= 1:
        raise SystemExit(f"{where}: [curse] chance must be in (0, 1]")
    for ef in cu.get("effects", []):
        item("[curse] effects id", ef.get("id"))
        if not is_int(ef.get("seconds")) or ef["seconds"] < 1 or not is_int(ef.get("amplifier")) or ef["amplifier"] < 0:
            raise SystemExit(f"{where}: [curse] effect {ef.get('id')} needs seconds >= 1 and amplifier >= 0")

    sch = art["schematics"]
    if coins:
        coin_table(f"{where}: [schematics] buy_price", sch.get("buy_price"), coins)
    for f, b in (sch.get("buy_band") or {}).items():
        if (facs and f not in facs) or b not in bands:
            raise SystemExit(f"{where}: [schematics] buy_band {f} = {b!r} (faction and band must exist)")
    pool = sch.get("pool") or []
    if not pool:
        raise SystemExit(f"{where}: [schematics] pool must list schematics")
    for s in pool:
        item("[schematics] pool", s)
    for s, g in (sch.get("gated") or {}).items():
        item("[schematics.gated]", s)
        if s in pool:
            raise SystemExit(f"{where}: {s} is gated and may not be in the buy/steal pool")
        if not is_int(g.get("boss_tier")) or not 1 <= g["boss_tier"] <= 4 or not is_num(g.get("chance")) or not 0 < g["chance"] <= 1:
            raise SystemExit(f"{where}: [schematics.gated] {s} needs boss_tier 1..4 and chance in (0, 1]")

    st = art["steal"]
    if not (isinstance(st.get("smithy"), dict) and is_int(st["smithy"].get("x")) and is_int(st["smithy"].get("z"))):
        raise SystemExit(f"{where}: [steal] smithy must be {{ anchor = \"<anchors.toml id>\" }} or {{ x = n, z = n }}")
    night = st.get("night")
    if not (isinstance(night, list) and len(night) == 2 and all(is_int(t) and 0 <= t < 24000 for t in night)):
        raise SystemExit(f"{where}: [steal] night must be [from, to] day-time ticks 0..23999")
    for k in ("radius", "channel_seconds", "move_tolerance", "cooldown_hours"):
        if not is_int(st.get(k)) or st[k] < 1:
            raise SystemExit(f"{where}: [steal] {k} must be a positive int")
    for cid in ("artifice.engrave", "artifice.schematic"):
        if choices and cid not in choices:
            raise SystemExit(f"{where}: roads.toml must define the choice {cid} (the curse and the stolen schematics pay it)")


NECRO_KINDS = {"tensura:skeleton", "tensura:zombie"}   # UndeadHumanoidEntity, verified in tensura-neoforge-2.0.1.5


def check_necro(necro: dict, roads: dict | None, factions: dict | None = None, bosses: dict | None = None) -> None:
    # necro/legion.js and necro/sanctum.js (WP-N2) read these by name; WP-N3 adds [[rank]] and [church] to the same file.
    for key in ("legion", "ash", "knight", "rest", "sanctum"):
        if not isinstance(necro.get(key), dict):
            raise SystemExit(f"necro.toml: [{key}] missing")
    lg = necro["legion"]

    def ranks(where: str, v, length: int = 5) -> list:
        if not (isinstance(v, list) and len(v) == length and all(isinstance(x, int) and x >= 0 for x in v)):
            raise SystemExit(f"necro.toml: {where} must be {length} ints >= 0 (rank 0..4)")
        if any(b < a for a, b in zip(v, v[1:])):
            raise SystemExit(f"necro.toml: {where} must not shrink with rank")
        return v

    caps = ranks("[legion] caps", lg.get("caps"))
    muster = ranks("[legion] muster_caps", lg.get("muster_caps"))
    if any(m < c for c, m in zip(caps, muster)):
        raise SystemExit("necro.toml: [legion] muster_caps must be >= caps at every rank")
    for k in ("min_rank", "muster_hours", "muster_radius", "server_cap", "queue_per_soul", "dormant_cap", "altars_per_soul",
              "altar_reach", "stow_radius", "recall_radius", "armed_rank", "offline_days", "loop_seconds", "sweep_minutes",
              "lost_sweeps", "dust_cost", "ash_cost"):
        if not (isinstance(lg.get(k), int) and lg[k] > 0):
            raise SystemExit(f"necro.toml: [legion] {k} must be a positive int")
    if not (is_num(lg.get("ash_mult")) and lg["ash_mult"] >= 1):
        raise SystemExit("necro.toml: [legion] ash_mult must be a number >= 1 (the dark road is never weaker)")
    kinds = lg.get("kinds")
    if not (isinstance(kinds, dict) and kinds and set(kinds.values()) <= NECRO_KINDS):
        raise SystemExit(f"necro.toml: [legion] kinds must map names to {sorted(NECRO_KINDS)}")
    for k, v in (lg.get("points") or {}).items():
        if not (isinstance(v, int) and v >= 0):
            raise SystemExit(f"necro.toml: [legion.points] {k} must be an int >= 0")

    a = necro["ash"]
    for k in ("ash_chance", "dust_chance"):
        if not (is_num(a.get(k)) and 0 <= a[k] <= 1):
            raise SystemExit(f"necro.toml: [ash] {k} must be between 0 and 1")
    for k in ("ash_entities", "dust_entities"):
        if not (isinstance(a.get(k), list) and all(isinstance(x, str) and re.fullmatch(r"#?[a-z0-9_.-]+:[a-z0-9_/.-]+", x) for x in a[k])):
            raise SystemExit(f"necro.toml: [ash] {k} must be entity ids or #tags")
    if not set(a.get("player_scope", [])) <= {"arena", "war"}:
        raise SystemExit("necro.toml: [ash] player_scope may only hold arena and war (O-N4)")
    for k in ("dust_count", "victim_hours", "corpse_days", "corpse_max"):
        if not (isinstance(a.get(k), int) and a[k] > 0):
            raise SystemExit(f"necro.toml: [ash] {k} must be a positive int")

    kn = necro["knight"]
    ranks("[knight] max", kn.get("max"))
    if kn.get("kind") not in kinds:
        raise SystemExit("necro.toml: [knight] kind must be a [legion] kinds name")
    if not (isinstance(kn.get("gear"), list) and 1 <= len(kn["gear"]) <= 5):
        raise SystemExit("necro.toml: [knight] gear must list 1-5 items (head, chest, legs, feet, main hand)")
    for road in ("dark", "grey"):
        st = kn.get(road) or {}
        if not (is_num(st.get("hp")) and is_num(st.get("attack")) and isinstance(st.get("strength"), int)):
            raise SystemExit(f"necro.toml: [knight] {road} needs hp, attack (numbers) and strength (int, -1 = none)")
    if "{name}" not in str(kn.get("title", "")):
        raise SystemExit("necro.toml: [knight] title must contain {name}")

    sc = necro["sanctum"]
    for k in ("scan_radius", "scan_height", "max_air", "cache_minutes", "cooldown_seconds", "bare_niches"):
        if not (isinstance(sc.get(k), int) and sc[k] > 0):
            raise SystemExit(f"necro.toml: [sanctum] {k} must be a positive int")
    tiers = sc.get("tier") or []
    if not tiers:
        raise SystemExit("necro.toml: [[sanctum.tier]] missing (owner 18/11/2026: tombs are recognised by tier)")
    ids, last_rank, last_air = set(), 0, 0
    for t in tiers:
        tid = str(t.get("id", ""))
        where = f"necro.toml: sanctum tier {tid}"
        if not re.fullmatch(r"[a-z_]+", tid) or tid in ids or tid == "none":
            raise SystemExit(f"{where}: id must be unique, lowercase and not 'none'")
        ids.add(tid)
        if not (isinstance(t.get("rank"), int) and 1 <= t["rank"] <= 4 and t["rank"] >= last_rank):
            raise SystemExit(f"{where}: rank must be 1..4 and never below the tier before it")
        if not (isinstance(t.get("min_air"), int) and t["min_air"] > last_air and t["min_air"] <= sc["max_air"]):
            raise SystemExit(f"{where}: min_air must grow from tier to tier and stay <= [sanctum] max_air")
        if not (isinstance(t.get("niches"), int) and 0 < t["niches"] <= lg["dormant_cap"]):
            raise SystemExit(f"{where}: niches must be 1..[legion] dormant_cap")
        last_rank, last_air = t["rank"], t["min_air"]
        for n in t.get("need") or []:
            if not (isinstance(n.get("label"), str) and isinstance(n.get("n"), int) and n["n"] > 0
                    and isinstance(n.get("match"), list) and n["match"]
                    and all(isinstance(m, str) and re.fullmatch(r"[a-z0-9_*.-]+:[a-z0-9_/*.-]+", m) for m in n["match"])):
                raise SystemExit(f"{where}: every need is {{label, match = [block ids, * wildcards], n > 0}}")
    if roads is not None:
        for cid in ("necro.raise", "necro.knight", "necro.rest"):
            if cid not in {str(c.get("id")) for c in roads.get("choice", [])}:
                raise SystemExit(f"necro.toml: the legion pays {cid} through TtlRoads, roads.toml has no such choice")
    check_necro_ranks(necro, factions, bosses)


NECRO_BANDS = ("hostile", "unfriendly", "neutral", "friendly", "honored", "exalted")
NS_ID = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"


def check_necro_ranks(necro: dict, factions: dict | None = None, bosses: dict | None = None) -> None:
    # necro/necro.js (WP-N3) reads these by name: entry roads, the Rite, the rank ladder, the Church's Sense, the Hunt
    # and the licence. O-N5: Marked 20, Hunt 50, decay 5 a week; licence at Honored + 14 clean days.
    for key in ("points", "entry", "rite", "rank", "church", "hunt", "licence"):
        if key not in necro:
            raise SystemExit(f"necro.toml: [{key}] missing (WP-N3)")

    def ids(where: str, v, allow_empty: bool = False) -> list:
        if not (isinstance(v, list) and (v or allow_empty) and all(isinstance(x, str) and re.fullmatch(NS_ID, x) for x in v)):
            raise SystemExit(f"necro.toml: {where} must be a list of namespaced ids")
        return v

    def pos_int(where: str, v, zero: bool = False) -> int:
        if not (isinstance(v, int) and not isinstance(v, bool) and (v >= 0 if zero else v > 0)):
            raise SystemExit(f"necro.toml: {where} must be an int {'>= 0' if zero else '> 0'}")
        return v

    pos_int("[points] weekly_cap", necro["points"].get("weekly_cap"))
    for k, v in necro["points"].items():
        pos_int(f"[points] {k}", v, True)
    ids("[entry] races", necro["entry"].get("races"), True)
    ids("[entry] skills", necro["entry"].get("skills"), True)
    rite = necro["rite"]
    ids("[rite] spells", rite.get("spells"))
    ids("[rite] iron_spells", rite.get("iron_spells"), True)
    pos_int("[rite] ash", rite.get("ash"))
    pos_int("[rite] dust", rite.get("dust"), True)
    if not isinstance(rite.get("aspirant_drops"), bool):
        raise SystemExit("necro.toml: [rite] aspirant_drops must be true or false")

    ranks = necro["rank"]
    if not (isinstance(ranks, list) and [r.get("rank") for r in ranks] == [1, 2, 3, 4]):
        raise SystemExit("necro.toml: [[rank]] must be ranks 1, 2, 3, 4 in order (Gravebinder .. Overlord)")
    last = -1
    for r in ranks:
        where = f"necro.toml: rank {r['rank']}"
        if not (isinstance(r.get("title"), str) and r["title"].strip()):
            raise SystemExit(f"{where}: title missing")
        pts = r.get("points")
        if not (isinstance(pts, int) and pts >= 0 and pts > last):
            raise SystemExit(f"{where}: points must be an int that grows with the rank")
        last = pts
        need = r.get("needs_any")
        if need is not None:
            if not (isinstance(need, dict) and set(need) <= {"races", "skills"} and need):
                raise SystemExit(f"{where}: needs_any holds races and/or skills")
            for k, v in need.items():
                ids(f"rank {r['rank']} needs_any.{k}", v)
    if ranks[0]["points"] != 0:
        raise SystemExit("necro.toml: rank 1 comes from a way in (race, skill, the Rite), its points must be 0")
    if ranks[3].get("needs_any") is None:
        raise SystemExit("necro.toml: rank 4 (Overlord) needs Wight King, Vampire or Mortal Fear (needs_any, §2.2)")

    ch = necro["church"]
    marked, hunt = pos_int("[church] marked_at", ch.get("marked_at")), pos_int("[church] hunt_at", ch.get("hunt_at"))
    if not marked < hunt <= pos_int("[church] max_sense", ch.get("max_sense")):
        raise SystemExit("necro.toml: [church] marked_at < hunt_at <= max_sense")
    for k in ("decay_per_week", "band_min", "band_radius", "loop_seconds"):
        pos_int(f"[church] {k}", ch.get(k))
    for k in ("marked_mult", "hunt_mult"):
        if not (is_num(ch.get(k)) and ch[k] >= 1):
            raise SystemExit(f"necro.toml: [church] {k} must be a number >= 1")
    if not (isinstance(ch.get("marked_rep"), int) and ch["marked_rep"] <= 0):
        raise SystemExit("necro.toml: [church] marked_rep must be an int <= 0")
    hu = necro["hunt"]
    if not (isinstance(hu.get("event"), str) and re.fullmatch(r"[a-z0-9_]+", hu["event"])):
        raise SystemExit("necro.toml: [hunt] event must be a director event id")
    for k in ("hours", "rearm_hours", "survive_minutes"):
        pos_int(f"[hunt] {k}", hu.get(k))
    if hu["survive_minutes"] > hu["hours"] * 60:
        raise SystemExit("necro.toml: [hunt] survive_minutes must fit in the Hunt")
    if "{soul}" not in str(hu.get("announce", "")):
        raise SystemExit("necro.toml: [hunt] announce must name {soul}")
    li = necro["licence"]
    if li.get("band") not in NECRO_BANDS:
        raise SystemExit(f"necro.toml: [licence] band must be one of {', '.join(NECRO_BANDS)}")
    pos_int("[licence] clean_days", li.get("clean_days"))
    if not (isinstance(li.get("min_rank"), int) and 0 <= li["min_rank"] <= 4):
        raise SystemExit("necro.toml: [licence] min_rank must be 0..4")
    if li.get("place") not in ("region", "anywhere"):
        raise SystemExit("necro.toml: [licence] place must be region or anywhere")
    if not (isinstance(li.get("item"), str) and re.fullmatch(NS_ID, li["item"])):
        raise SystemExit("necro.toml: [licence] item must be an item id")
    if not (isinstance(li.get("revoke_rep"), int) and li["revoke_rep"] <= 0):
        raise SystemExit("necro.toml: [licence] revoke_rep must be an int <= 0 (a dark act revokes the licence)")

    if factions is not None:
        fids = {str(f["id"]) for f in factions.get("faction", [])}
        want = [ch.get("faction")] + list(ch.get("band_factions") or []) + list((hu.get("survive_rep") or {}).keys())
        for f in want:
            if f not in fids:
                raise SystemExit(f"necro.toml: faction {f!r} is not in factions.toml")
    if bosses is not None:
        bids = {str(b.get("id")) for b in bosses.get("boss", [])}
        for b in ch.get("hunter_bosses") or []:
            if b not in bids:
                raise SystemExit(f"necro.toml: [church] hunter_bosses {b!r} is not a bosses.toml id")


CHOICE_ENGINE_NUMS = ("max_active", "ttl_minutes", "credit_radius", "witness_radius", "notice_radius", "roll_minutes",
                      "chance", "per_player", "max_chance", "min_gap_minutes", "min_distance", "max_distance",
                      "scene_radius", "linger_seconds", "repeat_days", "repeat_mult")
CHOICE_ROUTE_FIELDS = {"id", "road", "how", "label", "need", "result", "flag", "reward", "costs"}


def check_choices(ch: dict, data: dict) -> None:
    # choices/engine.js (TtlChoices) pays every route through TtlRoads.pay with the `costs` table as given: a typo in a
    # faction, an axis or a coin would silently cost or pay nothing, and a dark route without karma breaks R13.
    eng = ch.get("engine")
    if not isinstance(eng, dict):
        raise SystemExit("choices.toml: [engine] missing")
    for k in CHOICE_ENGINE_NUMS:
        if not is_num(eng.get(k)) or eng[k] < 0:
            raise SystemExit(f"choices.toml: [engine] {k} must be a number >= 0")
    for k in ("max_active", "ttl_minutes", "credit_radius", "witness_radius", "roll_minutes"):
        if eng[k] <= 0:
            raise SystemExit(f"choices.toml: [engine] {k} must be > 0")
    if eng["min_distance"] > eng["max_distance"]:
        raise SystemExit("choices.toml: [engine] min_distance > max_distance")
    if not (0 <= eng["chance"] <= 1 and 0 <= eng["max_chance"] <= 1 and 0 <= eng["repeat_mult"] <= 1):
        raise SystemExit("choices.toml: [engine] chance, max_chance and repeat_mult are shares between 0 and 1")
    if not isinstance((ch.get("balance") or {}).get("dark_cap"), (int, float)) or ch["balance"]["dark_cap"] < 0:
        raise SystemExit("choices.toml: [balance] dark_cap must be a number >= 0")
    if not is_num((ch.get("scale") or {}).get("max_mult")) or ch["scale"]["max_mult"] < 1:
        raise SystemExit("choices.toml: [scale] max_mult must be a number >= 1")
    axes = set(((data.get("roads") or {}).get("karma2") or {}).get("axes") or ["chaos", "order", "craft", "faith"])
    facs = {f["id"] for f in (data.get("factions") or {}).get("faction", [])}
    coins = ((data.get("economy") or {}).get("coins") or {}).get("chain") or []
    milestones = {m.get("id") for m in (data.get("world") or {}).get("milestone", [])}
    seen = set()
    for c in ch.get("choice", []):
        cid = str(c.get("id", ""))
        where = f"choices.toml: choice {cid}"
        if not re.fullmatch(r"[a-z0-9_]+", cid):
            raise SystemExit(f"choices.toml: choice id {cid!r} must be [a-z0-9_]+")
        if cid in seen:
            raise SystemExit(f"{where} defined twice")
        seen.add(cid)
        for k in ("label", "intro", "neutral"):
            if not isinstance(c.get(k), str) or not c[k].strip():
                raise SystemExit(f"{where}: {k} must be a non-empty string")
        if not is_num(c.get("weight")) or c["weight"] < 0:
            raise SystemExit(f"{where}: weight must be a number >= 0")
        wi = c.get("weight_if") or {}
        if set(wi) - {"tide", "milestone"}:
            raise SystemExit(f"{where}: weight_if takes tide and milestone only")
        if set(wi.get("tide") or {}) - {"light", "dark"}:
            raise SystemExit(f"{where}: weight_if.tide keys are light and dark")
        for m, x in (wi.get("milestone") or {}).items():
            if milestones and m not in milestones:
                raise SystemExit(f"{where}: weight_if.milestone {m} is not a world.toml milestone")
        for part in (wi.get("tide") or {}, wi.get("milestone") or {}):
            for k, x in part.items():
                if not is_num(x) or x < 0:
                    raise SystemExit(f"{where}: weight_if multiplier {k} must be a number >= 0")
        count = c.get("count")
        if not isinstance(count, dict) or not count:
            raise SystemExit(f"{where}: count = {{ <role> = {{ base, per_player }} }} missing")
        for role, n in count.items():
            if not re.fullmatch(r"[a-z0-9_]+", role) or not isinstance(n, dict) \
                    or not isinstance(n.get("base"), int) or n["base"] < 1 \
                    or not isinstance(n.get("per_player", 0), int) or n.get("per_player", 0) < 0:
                raise SystemExit(f"{where}: count.{role} must be {{ base = int >= 1, per_player = int >= 0 }}")
        for f in (c.get("knobs") or {}).get("homes", []):
            if facs and f not in facs:
                raise SystemExit(f"{where}: knobs.homes names unknown faction {f}")
        routes = c.get("route") or []
        ids = [r.get("id") for r in routes]
        if len(ids) < 2 or len(set(ids)) != len(ids):
            raise SystemExit(f"{where}: needs at least two routes with distinct ids (an honest one and a shortcut)")
        if c.get("fair") not in ids:
            raise SystemExit(f"{where}: fair = {c.get('fair')!r} must name one of its routes {ids}")
        roads = {r.get("road") for r in routes}
        if not roads & {"good", "grey"} or "dark" not in roads:
            raise SystemExit(f"{where}: R13 wants a good or grey route and a dark shortcut")
        for r in routes:
            rw = f"{where} route {r.get('id')}"
            if not re.fullmatch(r"[a-z0-9_]+", str(r.get("id", ""))):
                raise SystemExit(f"{rw}: id must be [a-z0-9_]+")
            unknown = set(r) - CHOICE_ROUTE_FIELDS
            if unknown:
                raise SystemExit(f"{rw}: unknown field(s) {sorted(unknown)} (known: {sorted(CHOICE_ROUTE_FIELDS)})")
            if r.get("road") not in ("good", "grey", "dark"):
                raise SystemExit(f"{rw}: road must be good, grey or dark")
            if r.get("how") not in ("menu", "deed"):
                raise SystemExit(f"{rw}: how must be menu or deed")
            for k in ("label", "result"):
                if not isinstance(r.get(k), str) or not r[k].strip():
                    raise SystemExit(f"{rw}: {k} must be a non-empty string")
            for n in r.get("need", []):
                if not (n == "necro" or re.fullmatch(r"skill:[a-z0-9_]+:[a-z0-9_/]+", n) or re.fullmatch(r"coins:[1-9][0-9]*", n)):
                    raise SystemExit(f"{rw}: need {n!r} must be necro, skill:<ns>:<id> or coins:<bronze>")
            if r.get("need") and r["how"] != "menu":
                raise SystemExit(f"{rw}: need is for menu routes only")
            if "flag" in r and not re.fullmatch(r"[a-z0-9_]+", str(r["flag"])):
                raise SystemExit(f"{rw}: flag must be [a-z0-9_]+")
            if set(r.get("reward") or {}) - {"coins"}:
                raise SystemExit(f"{rw}: reward takes coins only")
            if (r.get("reward") or {}).get("coins"):
                coin_table(f"{rw} reward.coins", r["reward"]["coins"], coins)
            costs = r.get("costs")
            if not isinstance(costs, dict):
                raise SystemExit(f"{rw}: [choice.route.costs] missing (balance = \"none\" for a route that costs nothing)")
            bad = set(costs) - ROAD_FIELDS
            if bad:
                raise SystemExit(f"{rw}: unknown cost field(s) {sorted(bad)} (known: {sorted(ROAD_FIELDS)})")
            for ax in ("chaos", "order", "craft", "faith"):
                if ax in costs and (not isinstance(costs[ax], int) or ax not in axes):
                    raise SystemExit(f"{rw}: {ax} must be an int and a roads.toml [karma2] axis")
            bal = costs.get("balance", "none")
            if bal not in ("dark_deed", "light_deed", "none"):
                raise SystemExit(f"{rw}: balance must be dark_deed, light_deed or none")
            if r["road"] == "dark" and (bal != "dark_deed" or int(costs.get("chaos", 0)) <= 0):
                raise SystemExit(f"{rw}: a dark route costs karma and notes a dark deed (rule R13)")
            if r["road"] != "dark" and (bal == "dark_deed" or int(costs.get("chaos", 0)) > 0):
                raise SystemExit(f"{rw}: only a dark route costs chaos or notes a dark deed")
            for f, n in (costs.get("rep") or {}).items():
                if facs and f not in facs:
                    raise SystemExit(f"{rw}: unknown faction {f}")
                if not isinstance(n, int):
                    raise SystemExit(f"{rw}: rep.{f} must be an int")
            for k in ("victim", "renown", "times"):
                if k in costs and not isinstance(costs[k], int):
                    raise SystemExit(f"{rw}: {k} must be an int")
            if "victim" in costs and not (c.get("knobs") or {}).get("homes"):
                raise SystemExit(f"{rw}: victim needs knobs.homes (the factions a scene's victims come from)")


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


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_arena(where: str, label: str, a: dict, landmarks: set, builds: set, allow_build: bool) -> None:
    """An arena / spawn.at table: landmark, build (spawn.at only) or x/z (+ y, dim, radius)."""
    ident = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    if not isinstance(a, dict):
        raise SystemExit(f"{where}: {label} must be a table")
    if "landmark" in a:
        if a["landmark"] not in landmarks:
            raise SystemExit(f"{where}: {label} landmark {a['landmark']!r} not in landmarks.toml")
        if set(a) - {"landmark"}:
            raise SystemExit(f"{where}: a landmark {label} cannot have a radius (give x and z)")
    elif "build" in a:
        if not allow_build:
            raise SystemExit(f"{where}: {label} build is only allowed in spawn.at")
        if a["build"] not in builds:
            raise SystemExit(f"{where}: {label} build {a['build']!r} is not in design/builds")
        if set(a) - {"build"}:
            raise SystemExit(f"{where}: a build {label} takes no other field")
    else:
        if not all(isinstance(a.get(k), int) for k in "xz") or not isinstance(a.get("y", 0), int):
            raise SystemExit(f"{where}: {label} needs a landmark, a build, an anchor or integer x and z (y optional)")
        if "radius" in a and (not isinstance(a["radius"], int) or not 4 <= a["radius"] <= 256):
            raise SystemExit(f"{where}: {label} radius must be an integer 4..256")
        if "dim" in a and not re.fullmatch(ident, str(a["dim"])):
            raise SystemExit(f"{where}: {label} dim must be a namespaced id")
        if "anchor" in a and a.get("dim", "minecraft:overworld") != "minecraft:overworld":
            raise SystemExit(f"{where}: {label} anchor names an overworld place (anchors.toml); drop dim")
        if ("dx" in a or "dz" in a) and "anchor" not in a:
            raise SystemExit(f"{where}: {label} dx/dz only go with an anchor")
        if set(a) - {"x", "y", "z", "dim", "radius", "anchor", "dx", "dz"}:
            raise SystemExit(f"{where}: {label} knows anchor (+ dx, dz), x, y, z, dim and radius only")


def check_wild_knobs(w: dict | None) -> None:
    if not isinstance(w, dict):
        raise SystemExit("bosses.toml: the [wild] table is missing")
    for key in ("enabled", "ignore_requires", "announce", "life2_only"):
        if not isinstance(w.get(key), bool):
            raise SystemExit(f"bosses.toml: [wild] {key} must be true or false")
    for key in ("max_active", "max_per_day", "require_players", "idle_minutes"):
        if not isinstance(w.get(key), int) or isinstance(w[key], bool) or w[key] < (1 if key in ("require_players", "idle_minutes") else 0):
            raise SystemExit(f"bosses.toml: [wild] {key} must be an integer ({'1' if key in ('require_players', 'idle_minutes') else '0'} or more)")
    if not is_num(w.get("min_gap_hours")) or w["min_gap_hours"] < 0:
        raise SystemExit("bosses.toml: [wild] min_gap_hours must be a number 0 or more")
    if not is_num(w.get("rewards_mult")) or not 0 <= w["rewards_mult"] <= 5:
        raise SystemExit("bosses.toml: [wild] rewards_mult must be a number 0..5")
    d = w.get("distance")
    if not (isinstance(d, list) and len(d) == 2 and all(isinstance(v, int) and not isinstance(v, bool) for v in d)
            and 16 <= d[0] < d[1] <= 256):
        raise SystemExit("bosses.toml: [wild] distance must be [min, max] integers, 16 <= min < max <= 256")


def check_wild(where: str, w: dict, letters: set, boss: dict) -> None:
    known = {"chance_per_day", "regions", "path_mult", "weather", "time", "biomes", "surface", "cooldown_hours", "cap"}
    if not isinstance(w, dict) or set(w) - known:
        raise SystemExit(f"{where}: wild is a table with {', '.join(sorted(known))} only")
    if not is_num(w.get("chance_per_day")) or not 0 <= w["chance_per_day"] <= 0.25:
        raise SystemExit(f"{where}: wild.chance_per_day must be a number 0..0.25 (a fraction per day; 0.01 = 1 %)")
    regions = w.get("regions")
    if not (isinstance(regions, list) and regions and all(isinstance(r, str) and r in letters for r in regions)):
        raise SystemExit(f"{where}: wild.regions must be a non-empty list of canon region letters ({''.join(sorted(letters))})")
    pm = w.get("path_mult", {})
    if not isinstance(pm, dict) or set(pm) - {"light", "dark"} or not all(is_num(v) and 0 <= v <= 10 for v in pm.values()):
        raise SystemExit(f"{where}: wild.path_mult is {{ light = n, dark = n }} with n 0..10")
    for key, allowed in (("weather", ("any", "thunder", "rain")), ("time", ("any", "night", "day")), ("surface", ("land", "water", "any"))):
        if w.get(key, allowed[0] if key != "surface" else "land") not in allowed:
            raise SystemExit(f"{where}: wild.{key} must be one of {', '.join(allowed)}")
    biomes = w.get("biomes", [])
    if not isinstance(biomes, list) or not all(isinstance(x, str) and re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", x) for x in biomes):
        raise SystemExit(f"{where}: wild.biomes must be a list of biome ids")
    if "cooldown_hours" in w and (not is_num(w["cooldown_hours"]) or w["cooldown_hours"] < 0):
        raise SystemExit(f"{where}: wild.cooldown_hours must be a number 0 or more")
    if "cap" in w and (not isinstance(w["cap"], int) or isinstance(w["cap"], bool) or w["cap"] < 1):
        raise SystemExit(f"{where}: wild.cap must be an integer 1 or more")

def check_bosses(bosses: dict, landmarks: dict | None, factions: dict | None = None) -> None:
    # bosses/boss.js summons these; a typo would fail only when a quest or altar summons the boss.
    ident = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    anchor_refs.resolve_data({"bosses": bosses})
    names = {lm["name"] for lm in (landmarks or {}).get("landmark", [])}
    fw = bosses.get("framework", {})
    for key, kind in (("block_natural", bool), ("untame", bool), ("proxy_bosses", bool), ("idle_minutes", int),
                      ("presence_secs", int), ("core_per_party", int)):
        if not isinstance(fw.get(key), kind) or (kind is int and isinstance(fw.get(key), bool)):
            raise SystemExit(f"bosses.toml: [framework] {key} must be a {kind.__name__}")
    if fw["core_per_party"] < 0:
        raise SystemExit("bosses.toml: [framework] core_per_party must be 0 or more")
    if not is_num(fw.get("party_credit_range")) or not 1 <= fw["party_credit_range"] <= 8:
        raise SystemExit("bosses.toml: [framework] party_credit_range must be a number 1..8 (x the boss range)")
    if "natural_allow" in fw:
        raise SystemExit("bosses.toml: [framework] natural_allow was removed: give the boss a [boss.wild] table instead")
    # WP-W2 instancing knobs (world-state.md §7.1).
    if fw.get("cooldown_scope", "party") not in ("party", "server"):
        raise SystemExit("bosses.toml: [framework] cooldown_scope must be party or server")
    for key, lo in (("arena_gap_minutes", 0), ("max_instances", 1), ("max_per_party", 1), ("queue_ttl_minutes", 1),
                    ("fight_estimate_minutes", 1)):
        v = fw.get(key)
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < lo):
            raise SystemExit(f"bosses.toml: [framework] {key} must be an integer {lo} or more")
    if "echo_prefix" in fw and (not isinstance(fw["echo_prefix"], str) or re.search(r"['\\\"]", fw["echo_prefix"])):
        raise SystemExit("bosses.toml: [framework] echo_prefix must be text without quotes or backslashes")
    if "echo_hp_mult" in fw and (not is_num(fw["echo_hp_mult"]) or not 0.25 <= fw["echo_hp_mult"] <= 1):
        raise SystemExit("bosses.toml: [framework] echo_hp_mult must be a number 0.25..1")
    if not isinstance(fw.get("bindable"), list):
        raise SystemExit("bosses.toml: [framework] bindable must be a list (use [] for none)")
    all_ids = [b.get("id") for b in bosses.get("boss", [])]
    for bid in fw["bindable"]:
        if bid not in all_ids:
            raise SystemExit(f"bosses.toml: [framework] bindable names unknown boss {bid!r}")
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    letters = set(canon["regions"])
    build_names = {f.stem for f in BUILDS.glob("*.toml") if not f.name.startswith("_")} if BUILDS.exists() else set()
    check_wild_knobs(bosses.get("wild"))
    ids, entities, proxies = set(), set(), set()
    for b in bosses.get("boss", []):
        bid = b.get("id", "")
        where = f"bosses.toml: boss {bid or '?'}"
        if not re.fullmatch(r"[a-z0-9_]+", bid) or bid in ids:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        ids.add(bid)
        if not re.fullmatch(ident, str(b.get("entity", ""))) or b["entity"] in entities:
            raise SystemExit(f"{where}: entity must be a unique namespaced id")
        entities.add(b["entity"])
        if "proxy" in b and not isinstance(b["proxy"], bool):
            raise SystemExit(f"{where}: proxy must be true or false")
        if b.get("proxy"):
            proxies.add(b["entity"])
        elif bid != b["entity"].split(":", 1)[1]:
            raise SystemExit(f"{where}: id must equal the entity path ({b['entity'].split(':', 1)[1]}) unless proxy = true; "
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
            check_arena(where, "arena", arena, names, build_names, allow_build=False)
        spawn = b.get("spawn")
        if spawn is not None:
            if set(spawn) - {"kind", "at", "stages", "statue"}:
                raise SystemExit(f"{where}: spawn knows kind, at, stages and statue only")
            if spawn.get("kind") not in ("quest", "altar", "statue", "event"):
                raise SystemExit(f"{where}: spawn.kind must be quest, altar, statue or event")
            if "statue" in spawn and (spawn["kind"] != "statue" or not re.fullmatch(r"[a-z0-9_.]+", str(spawn["statue"]))):
                raise SystemExit(f"{where}: spawn.statue (the seated statue's entity tag) needs kind = statue and a [a-z0-9_.] tag")
            if "at" in spawn:
                check_arena(where, "spawn.at", spawn["at"], names, build_names, allow_build=True)
            elif arena is None:
                raise SystemExit(f"{where}: spawn needs `at` or an `arena`: every boss has a definite place")
            stages = spawn.get("stages", [])
            if not isinstance(stages, list) or not all(isinstance(x, str) and re.fullmatch(r"ttl\.[a-z0-9_.]+", x) for x in stages):
                raise SystemExit(f"{where}: spawn.stages must be a list of ttl.* stage names")
            if any(x.startswith("ttl.path.") for x in stages):
                raise SystemExit(f"{where}: spawn.stages never names a ttl.path.* stage: anyone may fight any boss")
        wild = b.get("wild")
        if wild is not None:
            check_wild(where, wild, letters, b)
        if spawn is None and arena is None and not (wild and wild.get("chance_per_day", 0) > 0):
            raise SystemExit(f"{where}: needs a `spawn` (or `arena`) for its fixed place, or a wild chance above 0 if it is wild-only")
        kr = b.get("kill_rep", {})
        for f, n in kr.items():
            if f in ("flag", "unless_flag"):
                if not isinstance(n, str) or not re.fullmatch(r"[a-z0-9_]+", n):
                    raise SystemExit(f"{where}: kill_rep.{f} must be a [a-z0-9_] story flag")
            elif not isinstance(n, int) or isinstance(n, bool) or not -100 <= n <= 100:
                raise SystemExit(f"{where}: kill_rep.{f} must be an integer -100..100")
            elif factions is not None and f not in {x["id"] for x in factions.get("faction", [])}:
                raise SystemExit(f"{where}: kill_rep names faction {f!r}, which is not in factions.toml")
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
    if set(tag["values"]) != entities - proxies:
        raise SystemExit("bosses.toml: kubejs/data/ttl/tags/entity_type/boss.json does not list exactly the [[boss]] entities "
                         "(proxy = true bosses stay out of it: their mob also spawns on its own)")


def check_story(story: dict, factions: dict | None, bosses: dict | None, skills: dict | None) -> None:
    # story/story.js reads these by name; a typo in a faction, boss, flag or skill id would only show up when a soul
    # swears the Oath, finishes an act or talks to an NPC.
    where = "story.toml"
    fac_ids = {f["id"] for f in factions["faction"]} if factions else None
    boss_ids = {b["id"] for b in bosses["boss"]} if bosses else None
    bounds = (factions["rules"]["min"], factions["rules"]["max"]) if factions else (-100, 100)
    bands = ("hostile", "unfriendly", "neutral", "friendly", "honored", "exalted")
    ident = r"[a-z][a-z0-9_]*"

    def rep_table(label: str, table) -> None:
        if not isinstance(table, dict):
            raise SystemExit(f"{where}: {label} must be a table of faction = integer")
        for f, n in table.items():
            if fac_ids is not None and f not in fac_ids:
                raise SystemExit(f"{where}: {label} names the unknown faction {f!r} ({', '.join(sorted(fac_ids))})")
            if not is_int(n) or not bounds[0] <= n <= bounds[1]:
                raise SystemExit(f"{where}: {label}.{f} must be an integer within {bounds[0]}..{bounds[1]}")

    def text(label: str, value, required: bool = True) -> None:
        if not isinstance(value, str) or (required and not value.strip()):
            raise SystemExit(f"{where}: {label} needs text")

    rules = story.get("rules", {})
    for key in ("fight_near", "log_size"):
        if not is_int(rules.get(key)) or rules[key] < 1:
            raise SystemExit(f"{where}: rules.{key} must be a positive integer")
    for key in ("sequential_acts", "party_oath"):
        if not isinstance(rules.get(key), bool):
            raise SystemExit(f"{where}: rules.{key} must be true or false")

    flags = story.get("flag", {})
    for fid, flag in flags.items():
        if not re.fullmatch(ident, fid) or re.fullmatch(r"act\d*", fid):
            raise SystemExit(f"{where}: flag id {fid!r} must be [a-z_] and not act<N> (that is the act stage)")
        if flag.get("path", "light") not in ("light", "dark"):
            raise SystemExit(f"{where}: flag {fid} path must be light or dark")
        if not is_int(flag.get("renown", 0)) or flag.get("renown", 0) < 0:
            raise SystemExit(f"{where}: flag {fid} renown must be an integer >= 0")
        text(f"flag {fid} title", flag.get("title", ""), False)
        text(f"flag {fid} line", flag.get("line", ""), False)
        rep_table(f"flag {fid} rep", flag.get("rep", {}))

    def flag_ref(label: str, fid) -> None:
        if fid not in flags:
            raise SystemExit(f"{where}: {label} names the unknown flag {fid!r} (a [flag.*] table)")

    oath = story.get("oath", {})
    if not isinstance(oath.get("unaligned_for_legend"), bool):
        raise SystemExit(f"{where}: oath.unaligned_for_legend must be true or false")
    for key in ("menu_title", "unaligned_title"):
        text(f"oath.{key}", oath.get(key))
    if not re.fullmatch(r"([a-z0-9_.]+)?", str(oath.get("require_stage", ""))):
        raise SystemExit(f"{where}: oath.require_stage must be a stage name or empty")
    for lane in ("light", "dark"):
        cfg = oath.get(lane)
        if not isinstance(cfg, dict):
            raise SystemExit(f"{where}: [oath.{lane}] missing")
        for key in ("label", "lore", "say", "line"):
            text(f"oath.{lane}.{key}", cfg.get(key))
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", str(cfg.get("item", ""))):
            raise SystemExit(f"{where}: oath.{lane}.item must be a namespaced item id")
        rep_table(f"oath.{lane}.rep", cfg.get("rep", {}))
    text("oath.light.fallen_title", oath["light"].get("fallen_title", ""), False)
    text("oath.dark.remembers", oath["dark"].get("remembers"))

    flip = story.get("flip", {})
    if not is_int(flip.get("max")) or flip["max"] < 0:
        raise SystemExit(f"{where}: flip.max must be an integer >= 0")
    for name in ("atonement", "corruption"):
        cfg = flip.get(name)
        if not isinstance(cfg, dict):
            raise SystemExit(f"{where}: [flip.{name}] missing")
        if not cfg.get("requires_any"):
            raise SystemExit(f"{where}: flip.{name}.requires_any needs at least one flag")
        for fid in cfg["requires_any"]:
            flag_ref(f"flip.{name}.requires_any", fid)
        rep_table(f"flip.{name}.set", cfg.get("set", {}))
        rep_table(f"flip.{name}.rep", cfg.get("rep", {}))
        text(f"flip.{name}.say", cfg.get("say"))
        text(f"flip.{name}.line", cfg.get("line"))
        text(f"flip.{name}.title", cfg.get("title", ""), False)

    acts = story.get("act", [])
    if not acts or [a.get("id") for a in acts] != list(range(1, len(acts) + 1)):
        raise SystemExit(f"{where}: [[act]] ids must run 1, 2, 3, ... in order")
    unlocked = set()
    for a in acts:
        label = f"act {a['id']}"
        if not re.fullmatch(ident, str(a.get("key", ""))):
            raise SystemExit(f"{where}: {label} key must be [a-z_]")
        text(f"{label} title", a.get("title"))
        text(f"{label} story_line", a.get("story_line"))
        if not a.get("chapters") or any(not is_int(c) or c < 0 for c in a["chapters"]):
            raise SystemExit(f"{where}: {label} chapters must be a non-empty list of chapter numbers")
        if not is_int(a.get("renown")) or a["renown"] < 0:
            raise SystemExit(f"{where}: {label} renown must be an integer >= 0")
        rep_table(f"{label} light_rep", a.get("light_rep"))
        rep_table(f"{label} dark_rep", a.get("dark_rep"))
        for b in a.get("unlock_bosses", []):
            if boss_ids is not None and b not in boss_ids:
                raise SystemExit(f"{where}: {label} unlock_bosses names the unknown boss {b!r}")
            if b in unlocked:
                raise SystemExit(f"{where}: boss {b} is unlocked by two acts")
            unlocked.add(b)

    if "kill_rep" in story:
        raise SystemExit(f"{where}: [kill_rep] moved to bosses.toml (a kill_rep per [[boss]]): one source of kill costs")
    # The kill costs live in bosses.toml (check_bosses validates their shape); the flags they name must exist here.
    for b in (bosses or {}).get("boss", []):
        for key in ("flag", "unless_flag"):
            if key in b.get("kill_rep", {}):
                flag_ref(f"bosses.toml boss {b['id']} kill_rep.{key}", b["kill_rep"][key])

    legendary = story.get("legendary", {})
    allowed = set(skills["legendary"]["skills"]) if skills else None
    for lane in ("light", "dark"):
        pool = legendary.get(lane)
        if not isinstance(pool, list) or not pool:
            raise SystemExit(f"{where}: legendary.{lane} must be a non-empty list of skill ids")
        for skill in pool:
            if allowed is not None and skill not in allowed:
                raise SystemExit(f"{where}: legendary.{lane} has {skill!r}, which is not a skills.toml [legendary] skill")
    if set(legendary["light"]) & set(legendary["dark"]):
        raise SystemExit(f"{where}: a Legendary skill cannot be in both pools")

    seen = set()
    for npc in story.get("npc", []):
        nid = npc.get("id", "")
        label = f"npc {nid or '?'}"
        if not re.fullmatch(ident, nid) or nid in seen:
            raise SystemExit(f"{where}: {label}: id must be unique [a-z_]")
        seen.add(nid)
        text(f"{label} name", npc.get("name"))
        talk = npc.get("talk", [])
        if not talk:
            raise SystemExit(f"{where}: {label} needs at least one [[npc.talk]]")
        for i, t in enumerate(talk, 1):
            tl = f"{label} talk {i}"
            text(f"{tl} text", t.get("text"))
            if t.get("path", "any") not in ("light", "dark", "any"):
                raise SystemExit(f"{where}: {tl}: path must be light, dark or any")
            for key in ("act", "until_act"):
                if key in t and (not is_int(t[key]) or not 1 <= t[key] <= len(acts)):
                    raise SystemExit(f"{where}: {tl}: {key} must be an act number 1..{len(acts)}")
            if t.get("until_act", len(acts)) < t.get("act", 1):
                raise SystemExit(f"{where}: {tl}: until_act is before act")
            if ("faction" in t) != (("at_most" in t) or ("at_least" in t)):
                raise SystemExit(f"{where}: {tl}: faction needs at_most or at_least (and the other way round)")
            if "faction" in t and fac_ids is not None and t["faction"] not in fac_ids:
                raise SystemExit(f"{where}: {tl}: unknown faction {t['faction']!r}")
            for key in ("at_most", "at_least"):
                if key in t and t[key] not in bands:
                    raise SystemExit(f"{where}: {tl}: {key} must be one of {', '.join(bands)}")
            for b in t.get("buttons", []):
                cmd = str(b.get("command", ""))
                if not str(b.get("label", "")).strip() or not re.fullmatch(r"ttl [a-z0-9_ ]+", cmd):
                    raise SystemExit(f"{where}: {tl}: a button needs a label and a plain `ttl ...` command, got {cmd!r}")
                if cmd.startswith("ttl story fight "):
                    fight_id = cmd.split()[-1]
                    if boss_ids is not None and fight_id not in boss_ids:
                        raise SystemExit(f"{where}: {tl}: button fights the unknown boss {fight_id!r}")


def check_arrival(arrival: dict) -> None:
    # life/arrival.js grounds [life2] at x, z and TtlLife.toOverworld teleports there; a wrong type would only
    # show up as a bad `tp` at the first rebirth.
    anchor_refs.resolve_data({"arrival": arrival})
    spot = arrival.get("life2")
    if not isinstance(spot, dict):
        raise SystemExit("arrival.toml: [life2] missing")
    for key in ("x", "z", "yaw"):
        if not isinstance(spot.get(key), (int, float)) or isinstance(spot.get(key), bool):
            raise SystemExit(f"arrival.toml: life2.{key} must be a number")
    if not -180 <= spot["yaw"] <= 360:
        raise SystemExit("arrival.toml: life2.yaw is a Minecraft yaw in degrees (-180..360)")
    if not is_int(spot.get("safe_radius", 0)) or not 0 <= spot.get("safe_radius", 0) <= 128:
        raise SystemExit("arrival.toml: life2.safe_radius must be a whole number from 0 to 128 (0 = no hostile-free zone)")
    for key, top in (("search", 48), ("version", 1_000_000)):
        if not isinstance(spot.get(key), int) or isinstance(spot.get(key), bool) or not 0 <= spot[key] <= top or (key == "version" and spot[key] < 1):
            raise SystemExit(f"arrival.toml: life2.{key} must be a whole number" + (" from 0 to 48" if key == "search" else " from 1"))
    x0, z0, x1, z1 = json.loads(CANON.read_text(encoding="utf-8"))["lerfing"]["inner"]
    if not (x0 <= spot["x"] < x1 and z0 <= spot["z"] < z1):
        raise SystemExit(f"arrival.toml: life2 x/z ({spot['x']}, {spot['z']}) lies outside Lerfing's map {x0}..{x1} x {z0}..{z1}")
    at = anchor_table().get("arrival")
    if at and (spot["x"], spot["z"]) != (at["x"], at["z"]):
        raise SystemExit(f"arrival.toml: life2 must stand on the anchors.toml arrival ({at['x']}, {at['z']}): "
                         f"write at = \"arrival\" instead of x/z")


def settlement_box(script: str, anchor: str, footprint: str) -> tuple[int, int, int, int]:
    """World box (x0, z0, x1, z1, margin included) of Tempest or Dwargon, as their scripts compute it, at the position
    design/data/anchors.toml gives them (the source of truth since the Lerfing import). The script's literal (tempest.js:
    the fallback next to TtlAnchors.tempest; dwargon.js: GATE itself) must equal the anchor."""
    text = (SCRIPTS / "life" / script).read_text(encoding="utf-8")
    m = re.search(r"\b" + anchor + r":[^\n]*?\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)\s*\}", text)
    sx, sz = int(m.group(1)), int(m.group(2))
    aid = script.removesuffix(".js")
    at = anchor_table().get(aid)
    if at and (at["x"], at["z"]) != (sx, sz):
        # tempest.js reads TtlAnchors.tempest (the literal is its fallback); dwargon.js (WP-L7b) keeps GATE as a literal
        # chosen on the real heights. Either way the number must be the anchor, or the checks and the game disagree.
        raise SystemExit(f"life/{script} {anchor} ({sx}, {sz}) differs from anchors.toml {at['id']} ({at['x']}, {at['z']}): "
                         f"move them together")
    line = next(t for t in (SCRIPTS / "generated" / footprint).read_text(encoding="utf-8").splitlines()
                if t.startswith("const ") and "Footprint = " in t)
    f = json.loads(line[line.index("{"):])
    x0, z0 = sx - f["arrival"][0], sz - f["arrival"][2]
    return x0 - f["margin"], z0 - f["margin"], x0 + f["size"][0] + f["margin"] - 1, z0 + f["size"][2] + f["margin"] - 1


def landmark_world(at) -> tuple[int, int]:
    """A canon_regions.json landmark's `at` (world [x, z] on Lerfing's map, checked against anchors.toml)."""
    return int(at[0]), int(at[1])


ANCHOR_KEYS = {"id", "name", "x", "z", "region", "kind", "surface", "canon", "build", "landmark", "of", "dx", "dz",
               "old_x", "old_z", "map", "notes"}
ANCHOR_KINDS = {"settlement", "arrival", "build", "landmark", "pin", "spot"}
ANCHOR_SURFACES = {"land", "water", "shore", "any"}
KEEPOUT_KEYS = {"id", "name", "x0", "z0", "x1", "z1"}
_warned: set = set()


def warn_once(msg: str) -> None:
    if msg not in _warned:
        _warned.add(msg)
        print(msg, file=sys.stderr)


@functools.lru_cache(maxsize=1)
def anchor_table() -> dict:
    """{id: anchor} from design/data/anchors.toml ({} when the file is missing)."""
    return anchor_refs.table()


def box_gap(box: tuple, k: dict) -> float:
    """Blocks between a world box (x0, z0, x1, z1) and a keepout ({} with x0..z1); 0 when they touch or overlap."""
    return math.hypot(max(k["x0"] - box[2], 0, box[0] - k["x1"]), max(k["z0"] - box[3], 0, box[1] - k["z1"]))


def anchors_js() -> str:
    """generated/anchors.js: TtlAnchors = {id: {x, z, region, kind}} (life/tempest.js, life/mortal_spawns.js read it)."""
    rows = {a["id"]: {"x": a["x"], "z": a["z"], "region": a["region"], "kind": a["kind"]}
            for a in anchor_table().values()}
    return ("// priority: 200\n"
            "// GENERATED by tools/gen_data.py from design/data/anchors.toml (Lerfing's coordinates). Do not edit.\n"
            f"const TtlAnchors = {json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True)}\n")


def anchor_rows(table: dict) -> dict:
    """anchors.toml -> {id: anchor with "id"}; [<id>] tables are anchors, [keepout.<id>] tables Lerfing's builds."""
    return {k: dict(v, id=k) for k, v in table.items() if k != "keepout" and isinstance(v, dict)}


def check_anchors(anchors: dict) -> None:
    # design/data/anchors.toml: every canon place in Lerfing's coordinates (design/architecture/lerfing-import.md §3.5),
    # the table builds, landmarks, NPC spots, bosses, quests and tests translate from. tests/test_lerfing_anchors.py
    # adds the land-mask and nearest-owner checks.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    letters = set(canon["regions"])
    ix0, iz0, ix1, iz1 = canon["lerfing"]["inner"]
    landmark_at = {lm["name"]: tuple(lm["at"]) for lm in canon["landmarks"]}
    lm_names = {lm["name"] for lm in tomllib.loads((SOURCES / "landmarks.toml").read_text(encoding="utf-8")).get("landmark", [])}
    builds = {p.stem for p in BUILDS.glob("*.toml") if not p.name.startswith("_")}
    loose = [k for k, v in anchors.items() if not isinstance(v, dict)]
    if loose:
        raise SystemExit(f"anchors.toml: top-level keys {loose} must be [<id>] tables")
    rows = list(anchor_rows(anchors).values())
    by_id: dict[str, dict] = {}
    for a in rows:
        aid = a.get("id", "?")
        where = f"anchors.toml: {aid}"
        if not re.fullmatch(r"[a-z0-9_]+", str(aid)):
            raise SystemExit(f"{where}: the table name must be [a-z0-9_]")
        by_id[aid] = a
        unknown = set(a) - ANCHOR_KEYS
        if unknown:
            raise SystemExit(f"{where}: unknown field(s) {sorted(unknown)} (known: {', '.join(sorted(ANCHOR_KEYS))})")
        for key, value in a.items():
            if isinstance(value, (list, dict, float)):
                raise SystemExit(f"{where}: {key} must be an integer, boolean or string (the file stays flat)")
        for key in ("x", "z"):
            if not is_int(a.get(key)):
                raise SystemExit(f"{where}: {key} must be an integer")
        if not (ix0 <= a["x"] < ix1 and iz0 <= a["z"] < iz1):
            raise SystemExit(f"{where}: ({a['x']}, {a['z']}) lies outside Lerfing's inner tiles {ix0}..{ix1} x {iz0}..{iz1}")
        if not str(a.get("name", "")).strip():
            raise SystemExit(f"{where}: name is missing")
        region = a.get("region")
        if not isinstance(region, str) or not region or not set(region) <= letters:
            raise SystemExit(f"{where}: region must be one or more canon region letters ({''.join(sorted(letters))})")
        if a.get("kind") not in ANCHOR_KINDS:
            raise SystemExit(f"{where}: kind must be one of {', '.join(sorted(ANCHOR_KINDS))}")
        if a.get("surface") not in ANCHOR_SURFACES:
            raise SystemExit(f"{where}: surface must be one of {', '.join(sorted(ANCHOR_SURFACES))}")
        if "map" in a and not isinstance(a["map"], bool):
            raise SystemExit(f"{where}: map must be true or false")
        if ("old_x" in a) != ("old_z" in a) or any(k in a and not is_int(a[k]) for k in ("old_x", "old_z")):
            raise SystemExit(f"{where}: old_x and old_z are integers, both or neither")
        if "canon" in a:
            if a["canon"] not in landmark_at:
                raise SystemExit(f"{where}: canon {a['canon']!r} is not a canon_regions.json landmark")
            if landmark_at[a["canon"]] != (a["x"], a["z"]):
                raise SystemExit(f"{where}: canon_regions.json landmark {a['canon']!r} is at {list(landmark_at[a['canon']])}, "
                                 f"the anchor at [{a['x']}, {a['z']}]: set its `at` to the anchor")
        if "build" in a and a["build"] not in builds:
            raise SystemExit(f"{where}: build {a['build']!r} is not a design/builds name")
        if "landmark" in a and a["landmark"] not in lm_names:
            raise SystemExit(f"{where}: landmark {a['landmark']!r} is not a landmarks.toml name")
        if (a["kind"] == "build" and "build" not in a) or (a["kind"] == "landmark" and "landmark" not in a):
            raise SystemExit(f"{where}: a {a['kind']} anchor names its {a['kind']}")
        ch = canon_char(a["x"], a["z"])
        if a["surface"] == "land" and (ch is None or ch not in region):
            raise SystemExit(f"{where}: ({a['x']}, {a['z']}) reads {ch!r} in canon_map.txt, not land of {region}")
        if a["surface"] == "water" and ch not in ("~", "."):
            raise SystemExit(f"{where}: ({a['x']}, {a['z']}) reads {ch!r} in canon_map.txt, not water")
        if a["surface"] in ("shore", "any") and ch not in ("~", ".") and (ch is None or ch not in region):
            raise SystemExit(f"{where}: ({a['x']}, {a['z']}) reads {ch!r} in canon_map.txt, not {region} or water")
    for a in rows:
        where = f"anchors.toml: {a['id']}"
        if ("of" in a) != ("dx" in a) or ("dx" in a) != ("dz" in a):
            raise SystemExit(f"{where}: of, dx and dz go together")
        if "of" in a:
            base = by_id.get(a["of"])
            if not base or "of" in base:
                raise SystemExit(f"{where}: of {a['of']!r} must name an anchor that is not relative itself")
            if not is_int(a["dx"]) or not is_int(a["dz"]) or (base["x"] + a["dx"], base["z"] + a["dz"]) != (a["x"], a["z"]):
                raise SystemExit(f"{where}: x, z must equal {a['of']} + (dx, dz) = "
                                 f"({base['x'] + a.get('dx', 0)}, {base['z'] + a.get('dz', 0)})")
    for need, kind in (("tempest", "settlement"), ("dwargon", "settlement"), ("arrival", "arrival")):
        if by_id.get(need, {}).get("kind") != kind:
            raise SystemExit(f"anchors.toml: needs the {kind} anchor {need!r}")
    missing = set(landmark_at) - {a["canon"] for a in rows if "canon" in a}
    if missing:
        raise SystemExit(f"anchors.toml: no anchor for canon landmark(s) {sorted(missing)}")
    zones = canon["regions"]["J"].get("zones", {})
    if tuple(zones.get("centre", ())) != (by_id["tempest"]["x"], by_id["tempest"]["z"]):
        raise SystemExit("canon_regions.json: J zones centre must be the tempest anchor")
    for kid, k in anchors.get("keepout", {}).items():
        k = dict(k, id=kid)
        where = f"anchors.toml: keepout.{kid}"
        if set(k) - KEEPOUT_KEYS or not re.fullmatch(r"[a-z0-9_]+", kid) or "x" in k or "z" in k:
            raise SystemExit(f"{where}: keys are {', '.join(sorted(KEEPOUT_KEYS - {'id'}))}; the name [a-z0-9_]")
        if not all(is_int(k.get(c)) for c in ("x0", "z0", "x1", "z1")) or k["x0"] >= k["x1"] or k["z0"] >= k["z1"]:
            raise SystemExit(f"{where}: x0 < x1 and z0 < z1 (integers)")
        for a in rows:
            if a["kind"] in ("settlement", "arrival", "build", "landmark") and k["x0"] <= a["x"] <= k["x1"] and k["z0"] <= a["z"] <= k["z1"]:
                raise SystemExit(f"anchors.toml: {a['id']} ({a['x']}, {a['z']}) stands inside {k['id']} ({k['name']})")


def check_landmarks(landmarks: dict) -> None:
    # life/landmarks.js places these; x/z come from canon_regions.json (`at`) unless given, and every landmark keeps
    # `keepout` blocks (plus its reach) clear of Tempest's and Dwargon's boxes.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["at"] for lm in canon["landmarks"]}
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
        # Where: the anchors.toml anchor that names this landmark, else x/z, else the canon landmark's `at`.
        linked = anchor_refs.linked("landmark", name)
        if linked and "x" in lm and (lm["x"], lm["z"]) != (linked["x"], linked["z"]):
            raise SystemExit(f"{where}: anchors.toml {linked['id']} positions it at ({linked['x']}, {linked['z']}); "
                             f"drop x/z here")
        if linked:
            lm["x"], lm["z"] = linked["x"], linked["z"]
        elif "x" not in lm:
            if "canon" not in lm:
                raise SystemExit(f"{where}: needs x/z or canon")
            lm["x"], lm["z"] = landmark_world(refs[lm["canon"]])
        # Lerfing's and Paulzero's builds: the structure spreads `reach` round a spot up to 64 blocks off the nominal one
        # (life/landmarks.js OFFSETS).
        spread = lm["reach"] + 64
        for k in anchor_refs.keepouts():
            if box_gap((lm["x"] - spread, lm["z"] - spread, lm["x"] + spread, lm["z"] + spread), k) == 0:
                raise SystemExit(f"{where}: ({lm['x']}, {lm['z']}) reach {lm['reach']} + 64 can reach anchors.toml "
                                 f"keepout {k['id']} ({k['name']})")
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
        if not isinstance(b.get("lore", False), bool):
            raise SystemExit(f"{where}: lore is true or false")
        if b.get("lore") and giver != "fuze":
            raise SystemExit(f"{where}: lore = true only means something on Fuze's contracts (giver = \"fuze\")")
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


ARENA_MODES = ("duel", "party", "challenge")
ARENA_RANKS = {"duel": ("win", "lose", "draw"), "party": ("win", "lose", "draw"), "challenge": ("clear", "partial", "fail")}
COINS = ("bronze", "silver", "gold", "stellar_gold")


def check_arenas(arenas: dict, bosses: dict | None) -> None:
    """design/data/arenas.toml (arena/arenas.js): rules, and per arena its box, spots, modes, challenge and loot."""
    ident = r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    rules = arenas.get("rules")
    if not isinstance(rules, dict):
        raise SystemExit("arenas.toml: the [rules] table is missing")
    for key in ("life2_only", "friendly_fire"):
        if not isinstance(rules.get(key), bool):
            raise SystemExit(f"arenas.toml: [rules] {key} must be true or false")
    for key, low in (("poll_ticks", 5), ("lobby_minutes", 1), ("countdown_seconds", 0), ("return_seconds", 0),
                     ("min_seconds", 0), ("max_side", 1), ("party_min_side", 1), ("leave_grace_seconds", 0)):
        v = rules.get(key)
        if not isinstance(v, int) or isinstance(v, bool) or v < low:
            raise SystemExit(f"arenas.toml: [rules] {key} must be a whole number >= {low}")
    if rules["party_min_side"] > rules["max_side"]:
        raise SystemExit("arenas.toml: [rules] party_min_side is above max_side")
    story = rules.get("story", {})
    if not isinstance(story, dict) or set(story) - {"duel_streak", "party_side", "challenge"}:
        raise SystemExit("arenas.toml: [rules] story knows duel_streak, party_side and challenge")
    if story.get("challenge", "clear") not in ARENA_RANKS["challenge"]:
        raise SystemExit("arenas.toml: [rules] story.challenge must be a challenge rank (clear, partial, fail)")
    boss_ids = {b.get("id") for b in (bosses or {}).get("boss", [])}
    build_names = {f.stem for f in BUILDS.glob("*.toml") if not f.name.startswith("_")} if BUILDS.exists() else set()
    wal = arenas.get("walpurgis")
    if wal is not None:
        ww = "arenas.toml: [walpurgis]"
        if not re.fullmatch(ident, str(wal.get("dim", ""))) or wal.get("hall") not in build_names:
            raise SystemExit(f"{ww} needs dim (a dimension id) and hall (a design/builds name)")
        for key in ("life2_only", "allow_legendary", "allow_invited", "invite_by_legendary", "allow_booked", "command_entry"):
            if not isinstance(wal.get(key), bool):
                raise SystemExit(f"{ww} {key} must be true or false")
        if not isinstance(wal.get("allow_stages"), list) or not all(re.fullmatch(r"ttl\.[a-z0-9_.]+", str(s)) for s in wal["allow_stages"]):
            raise SystemExit(f"{ww} allow_stages must be a list of ttl.* stages")
        for key in ("invite_hours", "cooldown_seconds", "notice_seconds"):
            if not isinstance(wal.get(key), int) or isinstance(wal.get(key), bool) or wal[key] < 0:
                raise SystemExit(f"{ww} {key} must be a whole number >= 0")
        for key, fields in (("gate", ("from", "to")), ("return", ("at",))):
            t = wal.get(key)
            if not isinstance(t, dict) or t.get("build") not in build_names:
                raise SystemExit(f"{ww} {key} needs build = <a design/builds name>")
            for f in fields:
                v = t.get(f)
                if not (isinstance(v, list) and len(v) == 3 and all(isinstance(n, int) for n in v)):
                    raise SystemExit(f"{ww} {key}.{f} must be [x, y, z] whole numbers")
        if any(wal["gate"]["from"][i] > wal["gate"]["to"][i] for i in range(3)):
            raise SystemExit(f"{ww} gate.from must be the low corner")
    seen = set()
    for a in arenas.get("arena", []):
        aid = a.get("id")
        where = f"arenas.toml: arena {aid or '?'}"
        if not isinstance(aid, str) or not re.fullmatch(r"[a-z0-9_]+", aid) or aid in seen:
            raise SystemExit(f"{where}: id must be [a-z0-9_] and unique")
        seen.add(aid)
        title = a.get("title")
        if not isinstance(title, str) or not title or any(c in title for c in "\\\""):
            raise SystemExit(f"{where}: title must be text without double quotes or backslashes")
        w = a.get("where")
        if not isinstance(w, dict) or len(w) != 1 or not ({"build", "dim"} & set(w)):
            raise SystemExit(f"{where}: where must be {{ build = <name> }} or {{ dim = <dimension> }}")
        if "build" in w and w["build"] not in build_names:
            raise SystemExit(f"{where}: where.build {w['build']!r} is not in design/builds")
        if "dim" in w and not re.fullmatch(ident, str(w["dim"])):
            raise SystemExit(f"{where}: where.dim must be a namespaced dimension id")

        def point(label, v):
            if not (isinstance(v, list) and len(v) == 3 and all(isinstance(n, int) and not isinstance(n, bool) for n in v)):
                raise SystemExit(f"{where}: {label} must be [x, y, z] whole numbers")
            return v

        box = a.get("box", {})
        lo = point("box.from", box.get("from"))
        hi = point("box.to", box.get("to"))
        if any(lo[i] > hi[i] for i in range(3)):
            raise SystemExit(f"{where}: box.from must be the low corner and box.to the high one")
        rnd = a.get("round")
        if rnd is not None:
            c = rnd.get("centre")
            if not (isinstance(c, list) and len(c) == 2 and all(isinstance(n, int) for n in c)) \
                    or not isinstance(rnd.get("radius"), int) or rnd["radius"] < 2:
                raise SystemExit(f"{where}: round = {{ centre = [x, z], radius = r >= 2 }}")

        def inside(label, v):
            point(label, v)
            if not all(lo[i] <= v[i] <= hi[i] for i in range(3)):
                raise SystemExit(f"{where}: {label} {v} is outside the box")
            if rnd is not None and (v[0] - rnd["centre"][0]) ** 2 + (v[2] - rnd["centre"][1]) ** 2 > rnd["radius"] ** 2:
                raise SystemExit(f"{where}: {label} {v} is outside the round floor")

        inside("spawn_a", a.get("spawn_a"))
        inside("spawn_b", a.get("spawn_b"))
        spots = a.get("mob_spots")
        if not isinstance(spots, list) or not spots:
            raise SystemExit(f"{where}: mob_spots must list at least one [x, y, z]")
        for i, s in enumerate(spots):
            inside(f"mob_spots[{i}]", s)
        if "ready" in a:
            point("ready.at", a["ready"].get("at"))
        for key in ("absorb_duel", "quiet_colossus"):
            if not isinstance(a.get(key), bool):
                raise SystemExit(f"{where}: {key} must be true or false")
        modes = a.get("modes")
        if not isinstance(modes, list) or not modes or any(m not in ARENA_MODES for m in modes) or len(set(modes)) != len(modes):
            raise SystemExit(f"{where}: modes must list some of {', '.join(ARENA_MODES)} (each once)")
        for table, low in (("minutes", 1), ("cooldown_minutes", 0)):
            t = a.get(table, {})
            for m in modes:
                v = t.get(m)
                if not isinstance(v, int) or isinstance(v, bool) or v < low:
                    raise SystemExit(f"{where}: {table}.{m} must be a whole number >= {low}")
        cc = a.get("challenge_cooldown_minutes", 0)
        if not isinstance(cc, int) or cc < 0:
            raise SystemExit(f"{where}: challenge_cooldown_minutes must be a whole number >= 0")
        if "challenge" in modes:
            ch = a.get("challenge")
            if not isinstance(ch, dict) or not isinstance(ch.get("waves"), list) or not ch["waves"]:
                raise SystemExit(f"{where}: [arena.challenge] needs waves")
            if not is_num(ch.get("per_player", 0)) or not 0 <= ch.get("per_player", 0) <= 2:
                raise SystemExit(f"{where}: challenge.per_player must be a number 0..2")
            if not isinstance(ch.get("max_mobs"), int) or not 1 <= ch["max_mobs"] <= 40:
                raise SystemExit(f"{where}: challenge.max_mobs must be a whole number 1..40")
            for i, wave in enumerate(ch["waves"]):
                mobs = wave.get("mobs") if isinstance(wave, dict) else None
                if not isinstance(mobs, list) or not mobs:
                    raise SystemExit(f"{where}: challenge wave {i + 1} needs mobs")
                for m in mobs:
                    if not re.fullmatch(ident, str(m.get("entity", ""))) or not isinstance(m.get("count"), int) \
                            or not 1 <= m["count"] <= 20:
                        raise SystemExit(f"{where}: challenge wave {i + 1}: each mob needs an entity id and a count 1..20")
            if ch.get("boss", "") and ch["boss"] not in boss_ids:
                raise SystemExit(f"{where}: challenge.boss {ch['boss']!r} is not a [[boss]] id in bosses.toml")
        for m, ranks in a.get("loot", {}).items():
            if m not in modes:
                raise SystemExit(f"{where}: loot.{m} is not one of this arena's modes")
            for rank, r in ranks.items():
                if rank not in ARENA_RANKS[m]:
                    raise SystemExit(f"{where}: loot.{m}.{rank}: the ranks of {m} are {', '.join(ARENA_RANKS[m])}")
                lw = f"{where}: loot.{m}.{rank}"
                if set(r) - {"coins", "items", "table", "rolls", "xp"}:
                    raise SystemExit(f"{lw} knows coins, items, table, rolls and xp")
                for c, n in r.get("coins", {}).items():
                    if c not in COINS or not isinstance(n, int) or n < 1:
                        raise SystemExit(f"{lw}: coins.{c}: one of {', '.join(COINS)} with a whole number >= 1")
                for it in r.get("items", []):
                    if not re.fullmatch(ident, str(it.get("item", ""))) or not isinstance(it.get("count"), int) \
                            or not 1 <= it["count"] <= 64:
                        raise SystemExit(f"{lw}: items need an item id and a count 1..64")
                if "table" in r and not re.fullmatch(ident, str(r["table"])):
                    raise SystemExit(f"{lw}: table must be a namespaced loot table id")
                if not isinstance(r.get("rolls", 1), int) or not 1 <= r.get("rolls", 1) <= 8:
                    raise SystemExit(f"{lw}: rolls must be a whole number 1..8")
                if not isinstance(r.get("xp", 0), int) or r.get("xp", 0) < 0:
                    raise SystemExit(f"{lw}: xp must be a whole number >= 0")


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
        if data["economy"].get("sinks", {}).get("charter") != r["charter_cost"]:
            raise SystemExit("economy.toml [sinks].charter must not be set by hand: nations.toml rules.charter_cost is the only source")
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
    deb = nat.get("upkeep", {}).get("debuff")
    if deb is not None:
        # nations/upkeep_debuff.js registers a random-tick listener per crop id: an unknown id must not reach it.
        if not isinstance(deb.get("enabled"), bool) or not is_int(deb.get("weeks")) or deb["weeks"] < 1:
            raise SystemExit("nations.toml: upkeep.debuff needs enabled (true/false) and weeks >= 1")
        for k in ("resource_blocks", "crops"):
            if not all(isinstance(i, str) and re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", i) for i in deb.get(k, [])):
                raise SystemExit(f"nations.toml: upkeep.debuff.{k} must be block ids")
        if not all(isinstance(i, str) and i for i in deb.get("resource_suffixes", [])):
            raise SystemExit("nations.toml: upkeep.debuff.resource_suffixes must be non-empty strings")
        stages = deb.get("stage", [])
        if not stages:
            raise SystemExit("nations.toml: upkeep.debuff needs at least one [[upkeep.debuff.stage]]")
        for st in stages:
            if not st.get("name"):
                raise SystemExit("nations.toml: every upkeep.debuff.stage needs a name")
            for k in ("yield", "nothing_chance", "growth_skip"):
                x = st.get(k)
                if isinstance(x, bool) or not isinstance(x, (int, float)) or not 0 <= x <= 1:
                    raise SystemExit(f"nations.toml: upkeep.debuff.stage {st['name']}: {k} must be a number from 0 to 1")
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


WORLD_WHEN = {"acts", "acts_path", "flags", "kills", "nations", "wars", "armies", "radiant", "balance_at_least",
              "balance_at_most", "milestone", "era_days", "rule"}
WORLD_EFFECTS = {"stage", "phase", "unlock_events", "mood", "conflict", "chapter", "title", "voice", "story"}


def check_world(world: dict, data: dict) -> None:
    # world/chronicle.js reads this as TtlData.world; a wrong id would make a milestone that can never be reached, or an
    # effect that silently names nothing (design/architecture/world-state.md §3).
    ident, dim = r"[a-z0-9_]+", r"[a-z0-9_.-]+:[a-z0-9_/.-]+"
    unknown = set(world) - {"chronicle", "continent", "threshold", "places", "rule", "balance", "milestone", "tide"}
    if unknown:
        raise SystemExit(f"world.toml: unknown tables {sorted(unknown)}")
    chron = world.get("chronicle", {})
    for key, lo, hi in (("log_size", 1, 5000), ("sync_ticks", 200, 72000), ("active_window_days", 1, 365),
                        ("max_json", 1000, 64000), ("archive_max", 1, 50), ("voice_per_login", 0, 20)):
        if not is_int(chron.get(key)) or not lo <= chron[key] <= hi:
            raise SystemExit(f"world.toml: [chronicle] {key} must be an integer {lo}-{hi}")
    if not isinstance(chron.get("discord"), bool) or not isinstance(chron.get("first_story", ""), str):
        raise SystemExit("world.toml: [chronicle] discord must be true/false and first_story a string")
    story = data.get("story", {})
    flags = set(story.get("flag", {}))
    acts = {a.get("id") for a in story.get("act", [])}
    bosses = {b.get("id") for b in data.get("bosses", {}).get("boss", [])}
    factions = {f.get("id") for f in data.get("factions", {}).get("faction", [])}
    kill_kinds = chron.get("kill_kinds", [])
    pending = chron.get("pending_factions", [])
    for k in kill_kinds:
        if not re.fullmatch(ident, str(k)) or k in bosses:
            raise SystemExit(f"world.toml: kill_kinds {k!r} must be an id that is not already a [[boss]]")
    for f in pending:
        if not re.fullmatch(ident, str(f)) or f in factions:
            raise SystemExit(f"world.toml: pending_factions {f!r} must be an id factions.toml does not define yet")
    known_factions = factions | set(pending)
    cont = world.get("continent", {})
    if not re.fullmatch(dim, str(cont.get("overworld", ""))):
        raise SystemExit("world.toml: [continent] overworld must be a dimension id")
    for d in cont.get("inside_dimensions", []):
        if not re.fullmatch(dim, str(d)):
            raise SystemExit(f"world.toml: [continent] inside_dimensions {d!r} is not a dimension id")
    for key in ("outside_counts", "fallback_inside"):
        if not isinstance(cont.get(key), bool):
            raise SystemExit(f"world.toml: [continent] {key} must be true or false")
    if not is_int(cont.get("cache_max")) or cont["cache_max"] < 64:
        raise SystemExit("world.toml: [continent] cache_max must be an integer >= 64")
    th = world.get("threshold", {})
    if not is_int(th.get("souls")) or th["souls"] < 1 or not is_int(th.get("pct")) or not 0 <= th["pct"] <= 100:
        raise SystemExit("world.toml: [threshold] souls must be >= 1 and pct 0-100")
    places = world.get("places", {})
    for place, phases in places.items():
        if not re.fullmatch(ident, place) or not isinstance(phases, list) or len(phases) < 1 or len(set(phases)) != len(phases) \
                or not all(isinstance(p, str) and re.fullmatch(ident, p) for p in phases):
            raise SystemExit(f"world.toml: [places] {place} must be a list of distinct phase ids, lowest first")
    modes = world.get("rule", {}).get("modes", [])
    if not modes or not all(isinstance(m, str) and re.fullmatch(ident, m) for m in modes) or len(set(modes)) != len(modes):
        raise SystemExit("world.toml: [rule] modes must be a list of distinct ids")
    bal = world.get("balance", {})
    weights = bal.get("weights", {})
    if not weights or not all(re.fullmatch(ident, k) and is_num(v) for k, v in weights.items()):
        raise SystemExit("world.toml: [balance] weights must map ids to numbers")
    if not is_num(bal.get("decay_per_week")) or bal["decay_per_week"] < 0:
        raise SystemExit("world.toml: [balance] decay_per_week must be a number >= 0")
    if not is_num(bal.get("tide_at")) or not is_num(bal.get("tide_end")) or not 0 <= bal["tide_end"] < bal["tide_at"] <= 100:
        raise SystemExit("world.toml: [balance] needs 0 <= tide_end < tide_at <= 100")
    events = {e.get("id") for e in data.get("events", {}).get("event", [])}
    later_events: set[str] = set()

    def check_fx(where: str, fx: dict, allowed: set) -> None:
        if not isinstance(fx, dict) or not fx or not set(fx) <= allowed:
            raise SystemExit(f"{where}: keys are {', '.join(sorted(allowed))}")
        if "stage" in fx and not re.fullmatch(r"ttl\.world\.[a-z0-9_.]+", str(fx["stage"])):
            raise SystemExit(f"{where}: stage must start with ttl.world.")
        for place, phase in fx.get("phase", {}).items():
            if phase not in places.get(place, []):
                raise SystemExit(f"{where}: phase {place} = {phase!r} is not in [places]")
        for ev in fx.get("unlock_events", []):
            if not re.fullmatch(ident, str(ev)):
                raise SystemExit(f"{where}: unlock_events {ev!r} is not an id")
            if ev not in events:
                later_events.add(ev)
        for f, n in fx.get("mood", {}).items():
            if f not in known_factions or not is_int(n) or n == 0 or not -3 <= n <= 3:
                raise SystemExit(f"{where}: mood {f} = {n!r} needs a known faction and a band shift -3..3 (not 0)")
        if "conflict" in fx and fx["conflict"] not in known_factions:
            raise SystemExit(f"{where}: conflict {fx['conflict']!r} is not a faction")
        if "chapter" in fx and not re.fullmatch(ident, str(fx["chapter"])):
            raise SystemExit(f"{where}: chapter must be a world chapter key")
        for key in ("title", "voice", "story", "end_story"):
            if key in fx and not str(fx[key]).strip():
                raise SystemExit(f"{where}: {key} must not be empty")

    def count_table(where: str, table, ids: set, what: str) -> None:
        if not isinstance(table, dict) or not table:
            raise SystemExit(f"{where}: needs {{ <{what}> = n }}")
        for k, n in table.items():
            if k not in ids or not is_int(n) or n < 1:
                raise SystemExit(f"{where}: {k} = {n!r} needs a known {what} and n >= 1")

    seen: set[str] = set()
    for m in world.get("milestone", []):
        mid = m.get("id", "")
        where = f"world.toml: milestone {mid or '?'}"
        if not re.fullmatch(ident, str(mid)) or mid in seen:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        seen.add(mid)
        if set(m) - {"id", "when", "effects"}:
            raise SystemExit(f"{where}: keys are id, when, effects")
        when = m.get("when")
        if not isinstance(when, dict) or not when or not set(when) <= WORLD_WHEN:
            raise SystemExit(f"{where}: when keys are {', '.join(sorted(WORLD_WHEN))}")
        if "acts" in when and (set(when["acts"]) != {"act"} or when["acts"]["act"] not in acts):
            raise SystemExit(f"{where}: acts = {{ act = n }} with an act of story.toml")
        if "acts_path" in when:
            ap = when["acts_path"]
            if set(ap) != {"act", "path"} or ap["act"] not in acts or ap["path"] not in ("light", "dark"):
                raise SystemExit(f"{where}: acts_path = {{ act = n, path = light|dark }}")
        if "flags" in when:
            count_table(where + " flags", when["flags"], flags, "story flag")
        if "kills" in when:
            count_table(where + " kills", when["kills"], bosses | set(kill_kinds), "boss or kill_kinds id")
        if "radiant" in when:
            count_table(where + " radiant", when["radiant"], known_factions, "faction")
        for key in ("nations", "wars", "armies"):
            if key in when and (not is_int(when[key]) or when[key] < 1):
                raise SystemExit(f"{where}: {key} must be an integer >= 1")
        for key in ("balance_at_least", "balance_at_most"):
            if key in when and (not is_num(when[key]) or not -100 <= when[key] <= 100):
                raise SystemExit(f"{where}: {key} must be a number -100..100")
        if "era_days" in when and (not is_int(when["era_days"]) or when["era_days"] < 0):
            raise SystemExit(f"{where}: era_days must be an integer >= 0")
        for f, mode in when.get("rule", {}).items():
            if f not in known_factions or mode not in modes:
                raise SystemExit(f"{where}: rule {f} = {mode!r} needs a known faction and a [rule] mode")
        check_fx(where + " effects", m.get("effects"), WORLD_EFFECTS)
    for m in world.get("milestone", []):
        ref = m["when"].get("milestone")
        if ref is not None and (ref not in seen or ref == m["id"]):
            raise SystemExit(f"world.toml: milestone {m['id']}: milestone = {ref!r} must name another milestone")
    tide = world.get("tide", {})
    if set(tide) != {"light", "dark"}:
        raise SystemExit("world.toml: needs [tide.light] and [tide.dark]")
    for side, fx in tide.items():
        check_fx(f"world.toml: [tide.{side}]", fx, {"unlock_events", "mood", "story", "end_story"})
    if later_events:
        print(f"warn: world.toml unlocks events events.toml does not define yet: {', '.join(sorted(later_events))}", file=sys.stderr)


BUILD_KEYS = {"name", "title", "landmark", "x", "z", "anchor", "ground", "y", "search", "dimension", "version",
              "clear_above", "margin", "max_wet", "dry", "beside", "repair", "repair_depth", "repair_margin",
              "repair_keep_water", "notes"}


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
    """_read_footprint, cached on disk when TTL_FOOTPRINT_CACHE names a folder (tools/test_fast.sh, tools/check.sh).

    Parsing the big structures in pure Python is ~1 minute per check_builds; the cache key is the structure files'
    names and bytes plus the code that reads them, so a changed slab or reader is always read again. Unset (CI,
    gen_data.py, validate.py on their own) nothing is cached.
    """
    cache = os.environ.get("TTL_FOOTPRINT_CACHE")
    if not cache:
        return _read_footprint(files)
    h = hashlib.sha256()
    for part in (inspect.getsource(_read_footprint), Path(nbt.__file__).read_text(encoding="utf-8"),
                 repr(sorted(AIRISH)), str(NONE)):
        h.update(part.encode("utf-8"))
    for path in files:
        h.update(Path(path).name.encode("utf-8") + b"\0" + Path(path).read_bytes())
    entry = Path(cache) / f"footprint-{h.hexdigest()}.json"
    try:
        return json.loads(entry.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    fp = _read_footprint(files)
    try:
        entry.parent.mkdir(parents=True, exist_ok=True)
        tmp = entry.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(fp), encoding="utf-8")
        os.replace(tmp, entry)
    except OSError:
        pass
    return fp


def _read_footprint(files: list[Path]) -> dict:
    """Size, slabs and per-column ground data of a build's structure files (slabs stacked along z).

    Per column of the box (row-major, z outer, x inner; run-length encoded as [value, count, ...]):
    fill = y of the lowest non-air block (NONE: the column is air) and top = y of the highest non-air block + 1.
    life/builds.js fills the gap between the terrain and `fill` and clears from `top` up, so nothing floats.
    bottom = y of the lowest block the structure defines, explicit air included (NONE: the blueprint leaves the
    column undefined): life/repair.js fills caves only below it and continues the ground layer in NONE columns.
    """
    sx = sy = z0 = 0
    slabs, offsets, low, high, bottom = [], [], {}, {}, {}
    for path in files:
        root = nbt.read_gzip(path)
        px, py, pz = root["size"]
        palette = root.get("palette") or (root.get("palettes") or [[]])[0]
        solid = [e["Name"] not in AIRISH for e in palette]
        void = [e["Name"] == "minecraft:structure_void" for e in palette]
        for block in root["blocks"]:
            x, y, z = block["pos"]
            k = (x, z + z0)
            if not void[block["state"]] and y < bottom.get(k, 1 << 30):
                bottom[k] = y
            if not solid[block["state"]]:
                continue
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
            "top": rle([high[c] + 1 if c in high else NONE for c in cells]),
            "bottom": rle([bottom.get(c, NONE) for c in cells])}


@functools.lru_cache(maxsize=1)
def canon_rows() -> tuple[int, int, list[str]]:
    lines = CANON_MAP.read_text(encoding="utf-8").splitlines()
    origin = next(t for t in lines if t.startswith("# origin")).split()
    return int(origin[2]), int(origin[3]), [t for t in lines if not t.startswith("#")]


def canon_char(x: int, z: int) -> str | None:
    """The canon_map.txt character (a chunk) at world x/z, None outside the grid."""
    ox, oy, rows = canon_rows()
    row, col = oy + (z >> 4), ox + (x >> 4)
    return rows[row][col] if 0 <= row < len(rows) and 0 <= col < len(rows[row]) else None


def check_builds() -> tuple[list[dict], dict]:
    """design/builds/<name>.toml -> (TtlData.builds, footprints); files starting with `_` are examples."""
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["at"] for lm in canon["landmarks"]}
    landmark_names = {lm["name"] for lm in tomllib.loads((SOURCES / "landmarks.toml").read_text(encoding="utf-8")).get("landmark", [])}
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
        b["dry"] = b.get("dry", False)
        if not isinstance(b["dry"], bool):
            raise SystemExit(f"{where}: dry must be true or false")
        if "beside" in b and (not isinstance(b["beside"], str) or b["beside"] not in landmark_names):
            raise SystemExit(f"{where}: beside must name a landmark of design/data/landmarks.toml "
                             f"({', '.join(sorted(landmark_names))})")
        b["margin"] = b.get("margin", 8)
        if not is_int(b["margin"]) or not 0 <= b["margin"] <= 16:
            raise SystemExit(f"{where}: margin must be an integer 0..16")
        # Terrain repair after the fit (life/repair.js, docs/server.md "Terrain repair").
        for key in ("repair", "repair_keep_water"):
            b[key] = b.get(key, key == "repair")
            if not isinstance(b[key], bool):
                raise SystemExit(f"{where}: {key} must be true or false")
        b["repair_depth"] = b.get("repair_depth", 48)
        if not is_int(b["repair_depth"]) or not 1 <= b["repair_depth"] <= 96:
            raise SystemExit(f"{where}: repair_depth must be an integer 1..96 (blocks below the build that are made solid)")
        b["repair_margin"] = b.get("repair_margin", 8)
        if not is_int(b["repair_margin"]) or not 0 <= b["repair_margin"] <= 16:
            raise SystemExit(f"{where}: repair_margin must be an integer 0..16 (columns round the box)")
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
        b["max_wet"] = b.get("max_wet", 0.1)
        if isinstance(b["max_wet"], bool) or not isinstance(b["max_wet"], (int, float)) or not 0 <= b["max_wet"] <= 0.5:
            raise SystemExit(f"{where}: max_wet must be a fraction 0..0.5 (share of the build's columns over water)")

        # Where: the anchors.toml anchor that names this build (every overworld build has one), else x/z (the other
        # dimensions), else the canon landmark's `at`.
        if ("x" in b) != ("z" in b):
            raise SystemExit(f"{where}: give both x and z, or neither")
        linked = anchor_refs.linked("build", name)
        if linked and "x" in b:
            raise SystemExit(f"{where}: anchors.toml {linked['id']} positions this build at ({linked['x']}, {linked['z']}); "
                             f"drop x/z here")
        if linked:
            if b["dimension"] != "minecraft:overworld":
                raise SystemExit(f"{where}: anchors.toml {linked['id']} places it in the overworld, the build is in {b['dimension']}")
            b["x"], b["z"] = linked["x"], linked["z"]
        elif b["dimension"] == "minecraft:overworld" and anchor_table():
            raise SystemExit(f"{where}: an overworld build needs its anchor in design/data/anchors.toml (build = \"{name}\")")
        elif "x" in b:
            if not is_int(b["x"]) or not is_int(b["z"]):
                raise SystemExit(f"{where}: x and z must be integers")
        elif "landmark" in b:
            if b["landmark"] not in refs:
                raise SystemExit(f"{where}: landmark {b['landmark']!r} is not in canon_regions.json "
                                 f"(names are matched exactly)")
            b["x"], b["z"] = landmark_world(refs[b["landmark"]])
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
        if max(size[0], size[2]) + 2 * max(b["margin"], b["repair_margin"]) + 2 * b["search"] > 1000:
            raise SystemExit(f"{where}: box + margin + 2 x search is wider than 1000 blocks (forceload limit)")
        b["size"] = size

        if b["dimension"] == "minecraft:overworld":
            # Lerfing's and Paulzero's builds (anchors.toml keepouts): whatever spot the survey picks within `search`,
            # the box with its terrain and repair margin stays off them.
            reach = max(b["margin"], b["repair_margin"]) + b["search"]
            x0, z0 = b["x"] - anchor[0], b["z"] - anchor[2]
            box = (x0 - reach, z0 - reach, x0 + size[0] - 1 + reach, z0 + size[2] - 1 + reach)
            for k in anchor_refs.keepouts():
                if box_gap(box, k) == 0:
                    raise SystemExit(f"{where}: the box + margin + search {box} reaches anchors.toml keepout {k['id']} "
                                     f"({k['name']})")
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


DOMAIN_RULES = {"enabled", "capital_radius", "member_edit", "conflict_edit", "staff_level", "unowned_builds", "unowned_skip",
                "use_items", "use_suffixes", "use_exempt", "warn_seconds", "refresh_seconds", "invulnerable",
                "respawn_minutes", "respawn_check_ticks", "confirm_checks"}
SETTLEMENTS = {"tempest": ("tempest.js", "LANDMARK", "tempest_footprint.js"),
               "dwargon": ("dwargon.js", "GATE", "dwargon_footprint.js")}


def check_domains(fac: dict, data: dict, builds: list[dict]) -> None:
    # world/domains.js reads these (design/architecture/world-state.md §6.6, WP-W3). A wrong name would leave a canon build
    # unprotected without a word, a domain off the continent would guard nothing, and two domains on one build would make
    # the second faction's members and rulers silently powerless there. Writes domain.center (the nominal capital centre).
    rules = fac.get("domains")
    if not isinstance(rules, dict):
        raise SystemExit("factions.toml: needs a [domains] table")
    unknown = set(rules) - DOMAIN_RULES
    if unknown:
        raise SystemExit(f"factions.toml: [domains] unknown keys {sorted(unknown)}")
    scopes = ("none", "land", "all")
    for key in ("enabled", "unowned_builds"):
        if not isinstance(rules.get(key), bool):
            raise SystemExit(f"factions.toml: [domains] {key} must be true or false")
    for key, lo, hi in (("capital_radius", 16, 1024), ("staff_level", 0, 4), ("warn_seconds", 0, 60),
                        ("refresh_seconds", 1, 300), ("respawn_check_ticks", 20, 6000), ("confirm_checks", 1, 10)):
        if not is_int(rules.get(key)) or not lo <= rules[key] <= hi:
            raise SystemExit(f"factions.toml: [domains] {key} must be an integer {lo}-{hi}")
    if not is_num(rules.get("respawn_minutes")) or not 0 <= rules["respawn_minutes"] <= 1440:
        raise SystemExit("factions.toml: [domains] respawn_minutes must be a number 0-1440")
    for key in ("member_edit", "conflict_edit"):
        if rules.get(key) not in scopes:
            raise SystemExit(f"factions.toml: [domains] {key} must be one of {', '.join(scopes)}")
    if rules.get("invulnerable") not in ("named", "all", "none"):
        raise SystemExit("factions.toml: [domains] invulnerable must be named, all or none")
    for key in ("use_items", "use_exempt"):
        for item in rules.get(key, []):
            if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", str(item)):
                raise SystemExit(f"factions.toml: [domains] {key} {item!r} is not a namespaced item id")
    if not all(isinstance(s, str) and re.fullmatch(r"[a-z0-9_]+", s) for s in rules.get("use_suffixes", [])):
        raise SystemExit("factions.toml: [domains] use_suffixes must be [a-z0-9_] strings")

    world = data.get("world", {})
    inside = set(world.get("continent", {}).get("inside_dimensions", []))
    if "tensura:boss_area" in inside:
        raise SystemExit("world.toml: tensura:boss_area must stay outside the story rules (owner decision 18/11/2026): "
                         "remove it from [continent] inside_dimensions")
    overworld = world.get("continent", {}).get("overworld", "minecraft:overworld")
    modes = set(world.get("rule", {}).get("modes", ["vassal", "usurper"]))
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["at"] for lm in canon["landmarks"]}
    by_build = {b["name"]: b for b in builds}
    landmarks = {lm["name"]: lm for lm in data.get("landmarks", {}).get("landmark", [])}
    bosses = {b.get("id") for b in data.get("bosses", {}).get("boss", [])}
    npcs = data.get("npcs", {})
    statues = {h.get("id") for h in npcs.get("hook", [])} | {s.get("id") for s in npcs.get("spot", [])}
    for name in rules.get("unowned_skip", []):
        if name not in by_build:
            raise SystemExit(f"factions.toml: [domains] unowned_skip {name!r} is not a design/builds name")

    def settlement_center(name: str) -> tuple[int, int]:
        x0, z0, x1, z1 = settlement_box(*SETTLEMENTS[name])
        return round((x0 + x1) / 2), round((z0 + z1) / 2)

    def where_of(name: str) -> tuple[str, int, int]:
        """(dimension, x, z) of a build or settlement by name."""
        if name in SETTLEMENTS:
            return (overworld, *settlement_center(name))
        b = by_build[name]
        return b["dimension"], b["x"], b["z"]

    def on_continent(dim: str, x: int, z: int) -> bool:
        if dim in inside:
            return True
        return dim == overworld and canon_char(x, z) not in (None, ".")

    # The Life 2 arrival must stay free ground: newcomers gather and build there. A landmark may land up to 64 blocks off
    # its nominal spot (life/landmarks.js OFFSETS), so its square is widened by that much.
    # arrival.toml [life2] is at = "arrival" (check_arrival): the anchor is the position.
    anchored = anchor_table().get("arrival")
    arrival = {"x": anchored["x"], "z": anchored["z"]} if anchored else data.get("arrival", {}).get("life2")

    def covers_arrival(cx: int, cz: int, r: int) -> bool:
        return bool(arrival) and abs(arrival["x"] - cx) <= r and abs(arrival["z"] - cz) <= r

    owner: dict[str, str] = {}
    for f in fac["faction"]:
        fid = f["id"]
        where = f"factions.toml: {fid}"
        territory = f.get("territory", "domain")
        if territory not in ("domain", "region"):
            raise SystemExit(f"{where}: territory must be domain or region")
        if territory == "region" and "region" not in f:
            raise SystemExit(f"{where}: territory = \"region\" needs a region letter")
        d = f.get("domain")
        if d is not None:
            if not isinstance(d, dict) or set(d) - {"capital", "capital_radius", "builds", "landmarks"}:
                raise SystemExit(f"{where}: domain keys are capital, capital_radius, builds, landmarks")
            if "region" not in f:
                raise SystemExit(f"{where}: a domain needs the faction's canon region")
            if "capital_radius" in d and (not is_int(d["capital_radius"]) or not 16 <= d["capital_radius"] <= 1024):
                raise SystemExit(f"{where}: domain capital_radius must be an integer 16-1024")
            cap = d.get("capital")
            if cap is None:
                if f.get("capital") not in refs:
                    raise SystemExit(f"{where}: a domain without capital needs the faction's canon capital")
                center = landmark_world(refs[f["capital"]])
            elif cap in SETTLEMENTS:
                center = settlement_center(cap)
            elif isinstance(cap, str) and cap.startswith("build:"):
                b = by_build.get(cap[6:])
                if not b or b["dimension"] != overworld:
                    raise SystemExit(f"{where}: domain capital {cap!r} must name an overworld design/builds build")
                center = (b["x"], b["z"])
            elif isinstance(cap, str) and cap.startswith("landmark:"):
                lm = landmarks.get(cap[9:])
                if not lm:
                    raise SystemExit(f"{where}: domain capital {cap!r} names no landmarks.toml landmark")
                center = (lm["x"], lm["z"])
            else:
                raise SystemExit(f"{where}: domain capital must be tempest, dwargon, build:<name> or landmark:<name>")
            if not on_continent(overworld, *center):
                raise SystemExit(f"{where}: the domain's capital {center} is not on the canon continent")
            d["center"] = list(center)
            if covers_arrival(center[0], center[1], d.get("capital_radius", rules["capital_radius"])):
                raise SystemExit(f"{where}: the domain's capital square covers the Life 2 arrival ({arrival['x']}, {arrival['z']})")
            for name in d.get("builds", []):
                if name not in by_build and name not in SETTLEMENTS:
                    raise SystemExit(f"{where}: domain build {name!r} is not a design/builds name, tempest or dwargon")
                dim, x, z = where_of(name)
                if not on_continent(dim, x, z):
                    raise SystemExit(f"{where}: domain build {name!r} ({dim} {x} {z}) is not on the canon continent")
                if name in owner:
                    raise SystemExit(f"{where}: build {name!r} is already in the domain of {owner[name]}")
                owner[name] = fid
                ch = canon_char(x, z) if dim == overworld else None
                if ch not in (None, "~", f["region"]):
                    print(f"warn: {where}: domain build {name} stands in canon region {ch}, not {f['region']}", file=sys.stderr)
            for name in d.get("landmarks", []):
                lm = landmarks.get(name)
                if not lm:
                    raise SystemExit(f"{where}: domain landmark {name!r} is not a landmarks.toml name")
                if not on_continent(overworld, lm["x"], lm["z"]):
                    raise SystemExit(f"{where}: domain landmark {name!r} is not on the canon continent")
                if covers_arrival(lm["x"], lm["z"], lm["reach"] + 64):
                    raise SystemExit(f"{where}: domain landmark {name!r} (reach {lm['reach']}, may move 64) can cover the "
                                     f"Life 2 arrival ({arrival['x']}, {arrival['z']})")
                key = "landmark:" + name
                if key in owner:
                    raise SystemExit(f"{where}: landmark {name!r} is already in the domain of {owner[key]}")
                owner[key] = fid
        t = f.get("throne")
        if t is not None:
            if not isinstance(t, dict) or set(t) - {"boss", "statue", "seat", "roads"} or "boss" not in t or "seat" not in t:
                raise SystemExit(f"{where}: throne = {{ boss, seat, statue (optional), roads (optional) }}")
            if d is None:
                raise SystemExit(f"{where}: a throne needs a domain")
            if t["boss"] not in bosses:
                raise SystemExit(f"{where}: throne boss {t['boss']!r} is not a bosses.toml [[boss]]")
            if "statue" in t and t["statue"] not in statues:
                raise SystemExit(f"{where}: throne statue {t['statue']!r} is not an npcs.toml [[hook]] or [[spot]] id")
            if t["seat"] not in d.get("builds", []):
                raise SystemExit(f"{where}: throne seat {t['seat']!r} must be one of the domain's builds")
            roads = t.get("roads", sorted(modes))
            if not roads or not set(roads) <= modes:
                raise SystemExit(f"{where}: throne roads must be a non-empty subset of world.toml [rule] modes ({', '.join(sorted(modes))})")


def render() -> dict[Path, str]:
    data = {}
    for path in sorted(SOURCES.glob("*.toml")):
        with path.open("rb") as f:
            data[path.stem] = tomllib.load(f)
    # One source for the charter fee: nations.toml rules.charter_cost. economy.toml [sinks].charter is derived from it so
    # TtlEcon.fee('charter') and `ttl econ expect <p> fee_charter` keep working without a second number to keep in step.
    if "economy" in data and "nations" in data:
        if "charter" in data["economy"].get("sinks", {}):
            raise SystemExit("economy.toml: remove [sinks].charter, nations.toml rules.charter_cost is the only source")
        data["economy"]["sinks"]["charter"] = data["nations"]["rules"]["charter_cost"]
    # anchors.toml is not a script table (generated/anchors.js holds it as TtlAnchors): check it, then write the anchors'
    # x/z into every table that names one (tools/anchor_refs.py), before the per-file checks read x/z.
    if "anchors" in data:
        check_anchors(data.pop("anchors"))
    anchor_refs.resolve_data(data)
    if "skills" in data:
        check_skills(data["skills"])
    if "guide" in data:
        check_guide(data["guide"])
    if "mortal_banned" in data:
        check_mortal_banned(data["mortal_banned"])
    if "roads" in data:
        check_roads(data["roads"], data.get("factions"), data.get("karma"))
    if "artifice" in data:
        check_artifice(data["artifice"], data)
    if "necro" in data:
        check_necro(data["necro"], data.get("roads"), data.get("factions"), data.get("bosses"))
    if "choices" in data:
        check_choices(data["choices"], data)
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
    if "story" in data:
        check_story(data["story"], data.get("factions"), data.get("bosses"), data.get("skills"))
    if "nations" in data:
        check_nations(data["nations"], data)
    if "arenas" in data:
        check_arenas(data["arenas"], data.get("bosses"))
    if "world" in data:
        check_world(data["world"], data)
    if "sidequests" in data:
        from sidequests_check import check_sidequests  # noqa: E402 (tools/ is on sys.path above)
        check_sidequests(data["sidequests"], data)
    data["builds"], footprints = check_builds()
    if "factions" in data:
        check_domains(data["factions"], data, data["builds"])
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
        ANCHORS_JS: anchors_js(),
    }


def main() -> None:
    files = render()
    files.update(anchors_env.render())  # tests/anchors.env: the bot tests' ${anchor:...} / ${probe:...} numbers (WP-L6)
    if "--check" in sys.argv:
        for path, text in files.items():
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != text:
                print(f"FAIL {path.relative_to(ROOT).as_posix()} is stale: run python tools/gen_data.py")
                sys.exit(1)
        return
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
