"""Checks for design/data/enemies.toml (called by tools/gen_data.py after the domains are known; stdlib only).

Archetypes (looks of tools/npc_looks.py, item ids, numbers), groups, camps (on canon land of one region, outside every
domain square, away from every anchor of anchors.toml, every placed build and landmark, and outside every spawns.toml
zone) and the economy.toml kill bounties whose target is ttl:<archetype> or ttl:<group>. What cannot be checked offline
(the ground at the camp, a road the world has moved) is the in-game test tests/ingame/enemies.rcon.
"""
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import npc_looks  # noqa: E402

ANCHORS = ROOT / "design" / "data" / "anchors.toml"
# The grid the mod reads (CanonMap): the own world's (tools/world/build.py --apply) when present, else Lerfing's.
_OWN_WORLD_MAP = ROOT / "pack" / "config" / "ttl" / "world" / "canon_map.txt"
CANON_MAP = _OWN_WORLD_MAP if _OWN_WORLD_MAP.is_file() else ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
ID = re.compile(r"^[a-z][a-z0-9_]*$")
ITEM = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_/.-]+$")
MODELS = ("humanoid", "humanoid_slim")
SETTINGS_INT = {"rev": 1, "check_ticks": 40, "wake_radius": 16, "sleep_radius": 32, "sleep_checks": 1,
                "min_player_distance": 8, "leash": 8, "max_total": 1, "spawn_per_check": 1, "credit_seconds": 1,
                "anchor_margin": 0, "domain_margin": 0, "zone_margin": 0}
ARCH_KEYS = {"id", "name", "plural", "look", "model", "main", "off", "ranged", "lines", "health", "damage", "armor", "speed",
             "loot"}
CAMP_KEYS = {"id", "title", "group", "x", "z", "radius", "count", "regen_minutes", "mix", "faction"}


def fail(msg: str) -> None:
    raise SystemExit(f"enemies.toml: {msg}")


def canon_rows() -> tuple:
    lines = CANON_MAP.read_text(encoding="utf-8").splitlines()
    origin = next(t for t in lines if t.startswith("# origin")).split()
    return int(origin[2]), int(origin[3]), [t for t in lines if not t.startswith("#")]


def canon_cell(rows: tuple, x: int, z: int) -> str:
    ox, oz, grid = rows
    r, c = oz + (z >> 4), ox + (x >> 4)
    return grid[r][c] if 0 <= r < len(grid) and 0 <= c < len(grid[r]) else "?"


def num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_archetype(a: dict) -> None:
    w = f"archetype {a.get('id', '?')}"
    unknown = set(a) - ARCH_KEYS
    if unknown:
        fail(f"{w}: unknown keys {sorted(unknown)}")
    if not ID.match(str(a.get("id", ""))):
        fail(f"{w}: id is [a-z][a-z0-9_]*")
    for key in ("name", "plural"):
        if not isinstance(a.get(key), str) or not a[key].strip() or '"' in a[key] or "'" in a[key]:
            fail(f"{w}: {key} is a text without quotes")
    model = a.get("model", "humanoid")
    if model not in MODELS:
        fail(f"{w}: model is {' or '.join(MODELS)}")
    probs = npc_looks.problems(a.get("look"), model, a.get("name"))
    if probs:
        fail(f"{w}: {probs[0]}")
    for slot in ("main", "off"):
        if a.get(slot) and not ITEM.match(a[slot]):
            fail(f"{w}: {slot} = {a[slot]!r} is not an item id")
    lines = a.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 6 or not all(isinstance(t, str) and 0 < len(t) <= 160 for t in lines):
        fail(f"{w}: lines is a list of 1-6 texts of at most 160 characters")
    if not a.get("main"):
        fail(f"{w}: an enemy holds a weapon (main)")
    if a.get("ranged") and "bow" not in a["main"]:
        fail(f"{w}: ranged = true needs a bow in main")
    for key, lo, hi in (("health", 4, 200), ("damage", 0, 20), ("armor", 0, 20), ("speed", 0.1, 0.5)):
        if not num(a.get(key)) or not lo <= a[key] <= hi:
            fail(f"{w}: {key} must be a number {lo}-{hi}")
    loot = a.get("loot", [])
    if not isinstance(loot, list):
        fail(f"{w}: [[archetype.loot]] is a list")
    for i, entry in enumerate(loot):
        lw = f"{w} loot {i + 1}"
        if set(entry) - {"item", "min", "max", "chance"} or not ITEM.match(str(entry.get("item", ""))):
            fail(f"{lw}: item, min, max, chance")
        if not (isinstance(entry.get("min"), int) and isinstance(entry.get("max"), int) and 1 <= entry["min"] <= entry["max"] <= 16):
            fail(f"{lw}: 1 <= min <= max <= 16")
        if not num(entry.get("chance")) or not 0 < entry["chance"] <= 1:
            fail(f"{lw}: chance is in (0, 1]")
        for slot in ("main", "off"):
            if entry["item"] == a.get(slot):
                fail(f"{lw}: an enemy never drops its gear ({entry['item']})")


def domain_squares(data: dict) -> list:
    """[(faction, cx, cz, r)] of every domain capital square (centres written by gen_data.check_domains)."""
    rules = data.get("factions", {}).get("domains", {})
    out = []
    for f in data.get("factions", {}).get("faction", []):
        d = f.get("domain")
        if isinstance(d, dict) and d.get("center"):
            out.append((f["id"], d["center"][0], d["center"][1], d.get("capital_radius", rules.get("capital_radius", 256))))
    return out


def sites(data: dict) -> list:
    """[(label, x, z, reach)] of every anchor, overworld build and landmark."""
    out = []
    anchors = tomllib.loads(ANCHORS.read_text(encoding="utf-8"))
    for k, a in anchors.items():
        if isinstance(a, dict) and num(a.get("x")) and num(a.get("z")):
            out.append((f"anchor {k}", a["x"], a["z"], 0))
    for b in data.get("builds", []):
        if b.get("dimension", "minecraft:overworld") == "minecraft:overworld" and num(b.get("x")) and num(b.get("z")):
            out.append((f"build {b['name']}", b["x"], b["z"], 0))
    for lm in data.get("landmarks", {}).get("landmark", []):
        out.append((f"landmark {lm['name']}", lm["x"], lm["z"], lm.get("reach", 0)))
    return out


def zones(data: dict) -> list:
    """[(id, x, z, reduced_radius)] of spawns.toml, plus the arrival's safe square."""
    anchors = tomllib.loads(ANCHORS.read_text(encoding="utf-8"))
    out = []
    for zid, z in data.get("spawns", {}).get("zone", {}).items():
        a = anchors.get(z.get("anchor"), {})
        if num(a.get("x")):
            out.append((f"spawn zone {zid}", a["x"], a["z"], max(z["reduced_radius"], z.get("passive_radius", 0))))
    life2 = data.get("arrival", {}).get("life2", {})
    if num(life2.get("x")) and num(life2.get("z")):
        out.append(("the Life 2 arrival", life2["x"], life2["z"], life2.get("safe_radius", 48)))
    return out


def check_enemies(en: dict, data: dict) -> None:
    s = en.get("settings", {})
    for key, lo in SETTINGS_INT.items():
        if not isinstance(s.get(key), int) or s[key] < lo:
            fail(f"[settings] {key} must be a whole number >= {lo}")
    if not s["wake_radius"] < s["sleep_radius"]:
        fail("[settings] wake_radius < sleep_radius (a camp must not wake and sleep at the same distance)")
    if s["min_player_distance"] >= s["wake_radius"]:
        fail("[settings] min_player_distance < wake_radius")
    if s["max_total"] > 64:
        fail("[settings] max_total at most 64 (entity ticking is the main tick cost)")
    road = s.get("road")
    choices = {c["id"]: c for c in data.get("roads", {}).get("choice", [])}
    if road not in choices or "good" not in choices[road] or "dark" not in choices[road]:
        fail(f"[settings] road = {road!r} must be a roads.toml [[choice]] with a good and a dark route")

    pe = en.get("peaceful", {})
    if set(pe) - {"tags", "types"} or not all(isinstance(pe.get(k, []), list) for k in ("tags", "types")):
        fail("[peaceful] tags = [...], types = [...]")
    for t in pe.get("tags", []):
        if not re.fullmatch(r"[A-Za-z0-9_.]+", str(t)) or str(t).startswith("ttl.enemy"):
            fail(f"[peaceful] tag {t!r} (an entity tag, never an enemy's)")
    for t in pe.get("types", []):
        if not ITEM.match(str(t)):
            fail(f"[peaceful] type {t!r} is not an entity id")

    archetypes = {}
    for a in en.get("archetype", []):
        check_archetype(a)
        if a["id"] in archetypes:
            fail(f"archetype {a['id']} defined twice")
        archetypes[a["id"]] = a
    if not archetypes:
        fail("at least one [[archetype]]")
    groups = en.get("group", {})
    for gid, g in groups.items():
        if not ID.match(gid) or set(g) != {"title"} or not str(g["title"]).strip():
            fail(f"[group.{gid}]: id [a-z0-9_] and a title")
        if gid in archetypes:
            fail(f"[group.{gid}]: a group id may not equal an archetype id (both are bounty targets ttl:<id>)")

    factions = {f["id"] for f in data.get("factions", {}).get("faction", [])}
    rows = canon_rows()
    squares = domain_squares(data)
    places = sites(data)
    safe = zones(data)
    camps = {}
    used_groups = set()
    total = 0
    for c in en.get("camp", []):
        w = f"camp {c.get('id', '?')}"
        unknown = set(c) - CAMP_KEYS
        if unknown:
            fail(f"{w}: unknown keys {sorted(unknown)}")
        if not ID.match(str(c.get("id", ""))) or c["id"] in camps:
            fail(f"{w}: id must be unique [a-z0-9_]")
        if c.get("group") not in groups:
            fail(f"{w}: group {c.get('group')!r} is not a [group.<id>]")
        used_groups.add(c["group"])
        if not str(c.get("title", "")).strip():
            fail(f"{w}: title")
        for key, lo, hi in (("x", -30000, 30000), ("z", -30000, 30000), ("radius", 4, 32), ("count", 1, 8),
                            ("regen_minutes", 1, 240)):
            if not isinstance(c.get(key), int) or not lo <= c[key] <= hi:
                fail(f"{w}: {key} must be a whole number {lo}-{hi}")
        mix = c.get("mix")
        if not isinstance(mix, dict) or not mix:
            fail(f"{w}: mix = {{ <archetype> = weight }}")
        for k, v in mix.items():
            if k not in archetypes or not isinstance(v, int) or v < 1:
                fail(f"{w}: mix {k} = {v!r} (archetypes: {', '.join(sorted(archetypes))}, weights >= 1)")
        if "faction" in c and (not factions or c["faction"] not in factions):
            fail(f"{w}: faction {c['faction']!r} is not a factions.toml id")
        x, z, r = c["x"], c["z"], c["radius"]
        cells = {canon_cell(rows, x + dx, z + dz) for dx in range(-r, r + 1, 4) for dz in range(-r, r + 1, 4)}
        letters = {ch for ch in cells if ch.isalpha()}
        if cells - letters or len(letters) != 1:
            fail(f"{w}: the camp ({x}, {z}, r {r}) must lie on canon land of one region (canon_map.txt reads {sorted(cells)})")
        for fid, cx, cz, half in squares:
            gap = max(abs(x - cx), abs(z - cz)) - half - r
            if gap < s["domain_margin"]:
                fail(f"{w}: ({x}, {z}) is {gap} blocks from the {fid} domain square (needs {s['domain_margin']})")
        for label, px, pz, reach in places:
            d = math.hypot(x - px, z - pz) - reach - r
            if d < s["anchor_margin"]:
                fail(f"{w}: ({x}, {z}) is {round(d)} blocks from {label} (needs {s['anchor_margin']})")
        for label, px, pz, radius in safe:
            d = math.hypot(x - px, z - pz) - radius - r
            if d < s["zone_margin"]:
                fail(f"{w}: ({x}, {z}) is {round(d)} blocks from the edge of {label} (needs {s['zone_margin']})")
        for other in camps.values():
            if math.hypot(x - other["x"], z - other["z"]) < 2 * s["wake_radius"]:
                fail(f"{w}: closer than 2 x wake_radius to camp {other['id']} (two camps would wake as one)")
        camps[c["id"]] = c
        total += c["count"]
    if not camps:
        fail("at least one [[camp]]")
    for gid in groups:
        if gid not in used_groups:
            fail(f"[group.{gid}] has no camp")

    # world/enemies.js picks a preset per spawn from this list (the files are tools/gen_npcs.py's).
    en["presets"] = {}
    for a, n, base in presets(en):
        en["presets"].setdefault(a["id"], []).append(base)

    targets = set(archetypes) | set(groups)
    for b in data.get("economy", {}).get("bounty", []):
        t = str(b.get("target", ""))
        if b.get("kind") == "kill" and t.startswith("ttl:") and t[4:] not in targets:
            fail(f"economy.toml bounty {b.get('id')}: target {t} is not ttl:<archetype> or ttl:<group> "
                 f"({', '.join(sorted(targets))})")


def presets(en: dict) -> list:
    """[(archetype, variant n, preset base name)] for every look variant that fits the archetype's model."""
    out = []
    for a in en.get("archetype", []):
        for n in npc_looks.candidates(a["look"], a.get("model", "humanoid")):
            out.append((a, n, f"ttl_enemy_{a['id']}_{n}"))
    return out
