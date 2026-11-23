"""Checks for design/data/sidequests.toml (called by tools/gen_data.py; stdlib only).

Refuses unknown fields and references: places (anchors, builds, landmarks, canon-continent test for `world` places),
adventurer and client kinds (Easy NPC variants come from gen_npcs.VARIANTS), quests (kind fields, place/client ids,
entity and item ids shaped like ids, factions from factions.toml). What cannot be checked offline (does the mob spawn
there, does the build stand where the survey put it) is listed under "verify in game" in design/quests.md.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import anchor_refs  # noqa: E402
import npc_looks  # noqa: E402
BUILDS = ROOT / "design" / "builds"
# The grid the mod reads (CanonMap): the own world's (tools/world/build.py --apply) when present, else Lerfing's.
_OWN_WORLD_MAP = ROOT / "pack" / "config" / "ttl" / "world" / "canon_map.txt"
CANON_MAP = _OWN_WORLD_MAP if _OWN_WORLD_MAP.is_file() else ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
ID = re.compile(r"^[a-z][a-z0-9_]*$")
RES = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_/.-]+$")
STAGE = re.compile(r"^ttl(\.[a-z0-9_]+)+$")
ANCHORS = ("tempest", "build", "build_at", "dwargon", "landmark", "world")
KINDS = ("escort", "deliver", "travel", "fetch", "cull")
ARMOR = ("", "leather", "chainmail", "iron")
VARIANTS = {
    "humanoid": ("ALEX", "ARI", "EFE", "KAI", "MAKENA", "NOOR", "STEVE", "SUNNY", "ZURI", "JAYJASONBO", "PROFESSOR_01",
                 "SECURITY_01", "KNIGHT_01", "KNIGHT_02", "FARMER_01"),
    "humanoid_slim": ("ALEX", "ARI", "EFE", "KAI", "MAKENA", "NOOR", "STEVE", "SUNNY", "ZURI", "KAWORRU", "MAGE_01"),
}
MAX_LINES = 6       # MessageActionData.MAX_TEXTS in Easy NPC 7.19
MAX_LINE = 160


def fail(msg: str) -> None:
    raise SystemExit(f"sidequests.toml: {msg}")


def canon_cell(x: int, z: int) -> str:
    """The canon_map.txt character of a world column ('.' sea, '~' water, letters = nations), '?' off the map."""
    lines = [ln.rstrip("\n") for ln in CANON_MAP.read_text(encoding="utf-8").splitlines()]
    origin = next((ln for ln in lines if ln.startswith("# origin ")), None)
    rows = [ln for ln in lines if not ln.startswith("#")]
    if not origin:
        return "?"
    ox, oz = (int(v) for v in origin.split()[2:4])
    cx, cz = ox + x // 16, oz + z // 16
    if 0 <= cz < len(rows) and 0 <= cx < len(rows[cz]):
        return rows[cz][cx]
    return "?"


def coins(where: str, table, coin_names: set) -> None:
    if not isinstance(table, dict) or not table:
        fail(f"{where} must be a coin table like {{ silver = 5 }}")
    for k, v in table.items():
        if k not in coin_names or not isinstance(v, int) or v <= 0:
            fail(f"{where}: {k} = {v!r} (coins: {', '.join(sorted(coin_names))}, whole numbers > 0)")


def check_lines(where: str, lines) -> None:
    if not isinstance(lines, list) or not lines or len(lines) > MAX_LINES:
        fail(f"{where}: lines must be 1-{MAX_LINES} strings")
    for ln in lines:
        if not isinstance(ln, str) or not ln.strip() or len(ln) > MAX_LINE or '"' in ln or "\n" in ln:
            fail(f"{where}: line {ln!r} must be one line up to {MAX_LINE} characters without double quotes")


def check_look(where: str, k: dict) -> None:
    model = k.get("model", "humanoid")
    if model not in VARIANTS:
        fail(f"{where}: model is humanoid or humanoid_slim")
    if k.get("skin") not in VARIANTS[model]:
        fail(f"{where}: skin {k.get('skin')!r} is not a built-in {model} variant ({', '.join(VARIANTS[model])})")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", k.get("name_color", "")):
        fail(f"{where}: name_color must be #RRGGBB")
    if not k.get("name") or "'" in k["name"] or '"' in k["name"] or len(k["name"]) > 32:
        fail(f"{where}: name is needed, up to 32 characters, no quotes")
    if "look" in k or "look_name" in k:
        for why in npc_looks.problems(k.get("look"), model, k.get("look_name", k["name"])):
            fail(f"{where}: {why}")


def check_role(where: str, k: dict, data: dict) -> None:
    """`role` names a [[role]] of npc_gear.toml: the NPC's weapon and whether it fights or flees."""
    roles = {r["id"] for r in data.get("npc_gear", {}).get("role", [])}
    if k.get("role") not in roles:
        fail(f"{where}: role {k.get('role')!r} must be a [[role]] of npc_gear.toml ({', '.join(sorted(roles))})")


def check_sidequests(sq: dict, data: dict) -> None:
    anchor_refs.resolve_data({"sidequests": sq})  # world places name an anchors.toml anchor (at = "<id>")
    s = sq.get("settings", {})
    for key in ("poll_ticks", "max_active", "take_radius", "discover_radius", "arrive_radius", "leash", "leash_seconds",
                "appear_radius", "client_hp", "deliver_radius", "travel_radius"):
        if not isinstance(s.get(key), int) or s[key] < 1:
            fail(f"[settings] {key} must be a whole number >= 1")
    if s["poll_ticks"] < 20:
        fail("[settings] poll_ticks must be >= 20")
    ad = s.get("ambush_distance")
    if not (isinstance(ad, list) and len(ad) == 2 and all(isinstance(v, int) for v in ad) and 4 <= ad[0] < ad[1] <= 32):
        fail("[settings] ambush_distance must be [min, max] with 4 <= min < max <= 32")
    c = sq.get("companions", {})
    if not isinstance(c.get("enabled"), bool):
        fail("[companions] enabled must be true or false")
    for key in ("max_per_soul", "party_cap", "teleport_distance", "offline_grace_minutes"):
        if not isinstance(c.get(key), int) or c[key] < 1:
            fail(f"[companions] {key} must be a whole number >= 1")
    if c["party_cap"] > 5:
        fail("[companions] party_cap may not exceed the FTB party cap of 5")
    a = sq.get("ambient", {})
    if not isinstance(a.get("enabled"), bool):
        fail("[ambient] enabled must be true or false")
    for key in ("check_ticks", "active_range", "night_start", "night_end", "rev"):
        if not isinstance(a.get(key), int) or a[key] < 0:
            fail(f"[ambient] {key} must be a whole number >= 0")
    if a["check_ticks"] < 100 or not (0 <= a["night_start"] < 24000 and 0 <= a["night_end"] <= 24000):
        fail("[ambient] check_ticks >= 100, night_start/night_end within 0-24000")

    coin_names = set(data.get("economy", {}).get("coins", {}).get("chain", []))
    factions = {f["id"] for f in data.get("factions", {}).get("faction", [])}
    landmarks = {lm["name"] for lm in data.get("landmarks", {}).get("landmark", [])}
    builds = {f.stem for f in BUILDS.glob("*.toml") if not f.name.startswith("_")} if BUILDS.exists() else set()

    advs = {}
    for k in sq.get("adventurer", []):
        w = f"adventurer {k.get('id', '?')}"
        if not ID.match(k.get("id", "")) or k["id"] in advs:
            fail(f"{w}: id must be unique [a-z0-9_]")
        advs[k["id"]] = k
        check_look(w, k)
        check_role(w, k, data)
        if not k.get("title") or len(k["title"]) > 32:
            fail(f"{w}: title (up to 32 characters) is needed")
        check_lines(w, k.get("lines"))
        h = k.get("hire")
        if h is not None:
            coins(f"{w}: hire.fee", h.get("fee"), coin_names)
            if not isinstance(h.get("minutes"), int) or not 5 <= h["minutes"] <= 600:
                fail(f"{w}: hire.minutes must be 5-600")
            if not isinstance(h.get("hp"), int) or not 10 <= h["hp"] <= 100:
                fail(f"{w}: hire.hp must be 10-100")
            if not RES.match(h.get("weapon", "")):
                fail(f"{w}: hire.weapon must be an item id")
            if h.get("armor", "") not in ARMOR:
                fail(f"{w}: hire.armor is one of {ARMOR}")
            if h.get("rank") not in ("F", "E", "D", "C", "B", "A", "S"):
                fail(f"{w}: hire.rank is a guild rank letter F-S")
    clients = {}
    for k in sq.get("client", []):
        w = f"client {k.get('id', '?')}"
        if not ID.match(k.get("id", "")) or k["id"] in clients:
            fail(f"{w}: id must be unique [a-z0-9_]")
        clients[k["id"]] = k
        check_look(w, k)
        check_role(w, k, data)
        check_lines(w, k.get("lines"))

    places = {}
    for p in sq.get("place", []):
        w = f"place {p.get('id', '?')}"
        if not ID.match(p.get("id", "")) or p["id"] in places:
            fail(f"{w}: id must be unique [a-z0-9_]")
        places[p["id"]] = p
        anchor = p.get("anchor")
        if anchor not in ANCHORS:
            fail(f"{w}: anchor is one of {', '.join(ANCHORS)}")
        if not p.get("title"):
            fail(f"{w}: title is needed (players read it)")
        if anchor in ("build", "build_at") and p.get("build") not in builds:
            fail(f"{w}: build {p.get('build')!r} has no design/builds/<name>.toml")
        if anchor == "landmark" and p.get("landmark") not in landmarks:
            fail(f"{w}: landmark {p.get('landmark')!r} is not in landmarks.toml")
        if "at" in p and anchor != "world":
            fail(f"{w}: at = \"<anchors.toml id>\" only goes with anchor = \"world\"")
        if anchor in ("tempest", "build", "dwargon", "world"):
            if not all(isinstance(p.get(k), int) for k in ("x", "y", "z")):
                fail(f"{w}: x, y, z are whole numbers for anchor {anchor}")
        if anchor == "world":
            cell = canon_cell(p["x"], p["z"])
            if not cell.isalpha():
                fail(f"{w}: {p['x']}, {p['z']} is not canon land (canon_map.txt reads {cell!r}); rule R11 keeps places on the continent")
        inn = p.get("inn")
        if inn is not None and not (isinstance(inn, list) and len(inn) == 3 and all(isinstance(v, int) for v in inn)):
            fail(f"{w}: inn is [x, y, z] in the place's own anchor")
        if inn is not None and anchor not in ("tempest", "build", "dwargon"):
            fail(f"{w}: an inn needs an anchor with blueprint offsets (tempest, build, dwargon)")
        if not isinstance(p.get("cap", 0), int) or not 0 <= p.get("cap", 0) <= 6:
            fail(f"{w}: cap must be 0-6")
        if p.get("cap", 0) > 0:
            kinds = p.get("kinds")
            if not isinstance(kinds, list) or not kinds or any(k not in advs for k in kinds):
                fail(f"{w}: kinds must list [[adventurer]] ids ({', '.join(sorted(advs))})")
        if "radius" in p and (not isinstance(p["radius"], int) or not 0 <= p["radius"] <= 32):
            fail(f"{w}: radius must be 0-32")
        if "discover" in p and not isinstance(p["discover"], bool):
            fail(f"{w}: discover must be true or false")

    def place_ref(w: str, key: str, value, allow_empty: bool) -> None:
        if value in (None, "") and allow_empty:
            return
        if value not in places:
            fail(f"{w}: {key} = {value!r} is not a [[place]]")

    seen = set()
    for q in sq.get("quest", []):
        w = f"quest {q.get('id', '?')}"
        if not ID.match(q.get("id", "")) or q["id"] in seen:
            fail(f"{w}: id must be unique [a-z0-9_]")
        if q["id"].startswith("seen") or q["id"] == "hired":
            fail(f"{w}: ids seen* and hired are reserved stages")
        seen.add(q["id"])
        kind = q.get("kind")
        if kind not in KINDS:
            fail(f"{w}: kind is one of {', '.join(KINDS)}")
        if not q.get("title") or not q.get("text"):
            fail(f"{w}: title and text are needed")
        place_ref(w, "giver", q.get("giver", ""), True)
        for key in ("minutes", "repeat_hours"):
            if not isinstance(q.get(key, 0), int) or q.get(key, 0) < 0:
                fail(f"{w}: {key} must be a whole number >= 0")
        for st in q.get("requires", []):
            if not STAGE.match(st):
                fail(f"{w}: requires {st!r} is not a ttl.* stage")
        rw = q.get("reward", {})
        if rw:
            if "coins" in rw:
                coins(f"{w}: reward.coins", rw["coins"], coin_names)
            for f in rw.get("rep", {}):
                if f not in factions:
                    fail(f"{w}: reward.rep faction {f!r} is not in factions.toml")
        if kind == "escort":
            if q.get("client") not in clients:
                fail(f"{w}: client must be a [[client]] id ({', '.join(sorted(clients))})")
            place_ref(w, "from", q.get("from", ""), True)
            place_ref(w, "to", q.get("to"), False)
            for amb in q.get("ambush", []):
                at = amb.get("at")
                if not isinstance(at, (int, float)) or not 0 <= at < 1:
                    fail(f"{w}: ambush.at must be 0 <= at < 1")
                mobs = amb.get("mobs", {})
                if not mobs or any(not RES.match(m) or not isinstance(n, int) or not 1 <= n <= 6 for m, n in mobs.items()):
                    fail(f"{w}: ambush.mobs = {{ \"<entity id>\" = 1-6 }}")
        elif kind == "deliver":
            if not q.get("parcel") or '"' in q["parcel"] or "\\" in q["parcel"] or len(q["parcel"]) > 48:
                fail(f"{w}: parcel (the item's name, up to 48 characters, no double quotes) is needed")
            place_ref(w, "to", q.get("to"), False)
            place_ref(w, "pickup", q.get("pickup", ""), True)
        elif kind == "travel":
            place_ref(w, "to", q.get("to"), False)
        elif kind == "fetch":
            items = q.get("items", {})
            if not items or any(not RES.match(i) or not isinstance(n, int) or n < 1 for i, n in items.items()):
                fail(f"{w}: items = {{ \"<item id>\" = n }}")
            place_ref(w, "at", q.get("at", ""), True)
        elif kind == "cull":
            if not RES.match(q.get("entity", "")) or not isinstance(q.get("count"), int) or q["count"] < 1:
                fail(f"{w}: entity (id) and count (>= 1) are needed")
            if q.get("region") and q["region"] not in factions:
                fail(f"{w}: region {q['region']!r} is not a faction of factions.toml")
            if q.get("near"):
                place_ref(w, "near", q["near"], False)
                if not isinstance(q.get("radius"), int) or q["radius"] < 8:
                    fail(f"{w}: near needs radius >= 8")
            if q.get("region") and q.get("near"):
                fail(f"{w}: region or near, not both")
