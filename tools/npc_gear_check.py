"""Checks and helpers for design/data/npc_gear.toml (stdlib only; called by tools/gen_data.py, used by gen_npcs.py).

A role gives an NPC its items (main, off) and its fighting behaviour (ai: guard | fighter | civilian | none). The Easy NPC
objectives of each ai are written into the presets by gen_npcs.py; the Tempest residents (Tensura goblins) get their role
from [residents.tempest] and are equipped and driven by world/npc_gear.js.
"""
import re
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "design" / "data" / "npc_gear.toml"
ITEM = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_/.-]+$")
AIS = ("guard", "fighter", "civilian", "none")
# Easy NPC 7.19 ObjectiveType names that may appear in [ai.*] (the subset this pack uses; read from the jar's enum).
OBJECTIVES = ("MELEE_ATTACK", "ATTACK_MOB_WITHOUT_CREEPER", "ATTACK_MONSTER", "HURT_BY_TARGET", "FLEE_MONSTER", "FLEE_MOB",
              "PANIC", "OWNER_HURT_BY_TARGET", "OWNER_HURT_TARGET")
# Never an NPC objective here: they would make an NPC start a fight with a soul.
FORBIDDEN = ("ATTACK_PLAYER", "ATTACK_PLAYER_BY_NAME", "ATTACK_PLAYER_WITHOUT_OWNER", "ATTACK_VILLAGER", "ATTACK_MOB",
             "ATTACK_ANIMAL")
# Speed modifier written with an objective (Easy NPC SpeedModifier); the rest take none.
SPEED = {"MELEE_ATTACK": "0.8d", "ATTACK_MOB_WITHOUT_CREEPER": "0.8d", "ATTACK_MONSTER": "0.8d", "FLEE_MONSTER": "1.0d",
         "FLEE_MOB": "1.0d", "PANIC": "1.2d"}


def fail(msg: str) -> None:
    raise SystemExit(f"npc_gear.toml: {msg}")


def load() -> dict:
    return tomllib.loads(SOURCE.read_text(encoding="utf-8"))


def check_npc_gear(g: dict) -> None:
    s = g.get("settings", {})
    if not isinstance(s.get("rev"), int) or s["rev"] < 1:
        fail("[settings] rev is a whole number >= 1")
    if not isinstance(s.get("guard_check_ticks"), int) or s["guard_check_ticks"] < 20:
        fail("[settings] guard_check_ticks >= 20")
    if not isinstance(s.get("guard_radius"), int) or not 4 <= s["guard_radius"] <= 48:
        fail("[settings] guard_radius is 4-48 blocks")
    tags = s.get("guard_ignore_tags")
    if not isinstance(tags, list) or not all(isinstance(t, str) and re.fullmatch(r"[A-Za-z0-9_.]+", t) for t in tags):
        fail("[settings] guard_ignore_tags is a list of entity tags")
    ai = g.get("ai", {})
    if set(ai) != set(AIS):
        fail(f"[ai] defines exactly {', '.join(AIS)}")
    for name, a in ai.items():
        objs = a.get("easy_npc")
        if not isinstance(objs, list) or len(set(objs)) != len(objs):
            fail(f"[ai.{name}] easy_npc is a list of distinct Easy NPC objective types")
        for o in objs:
            if o in FORBIDDEN:
                fail(f"[ai.{name}] {o} would set an NPC on players or villagers")
            if o not in OBJECTIVES:
                fail(f"[ai.{name}] {o!r} is not one of {', '.join(OBJECTIVES)}")
    roles = {}
    for r in g.get("role", []):
        w = f"role {r.get('id', '?')}"
        if not re.fullmatch(r"[a-z][a-z0-9_]*", r.get("id", "")) or r["id"] in roles:
            fail(f"{w}: id must be unique [a-z0-9_]")
        for slot in ("main", "off"):
            v = r.get(slot, "")
            if v and not ITEM.match(v):
                fail(f"{w}: {slot} = {v!r} is not an item id")
        if r.get("ai") not in AIS:
            fail(f"{w}: ai is one of {', '.join(AIS)}")
        if r["ai"] in ("guard", "fighter") and not r.get("main"):
            fail(f"{w}: a {r['ai']} holds a weapon (main)")
        if r["ai"] == "civilian" and r.get("main") and "dagger" not in r["main"]:
            fail(f"{w}: a civilian runs; at most a dagger in the hand")
        unknown = set(r) - {"id", "main", "off", "ai"}
        if unknown:
            fail(f"{w}: unknown keys {sorted(unknown)}")
        roles[r["id"]] = r
    for place, table in g.get("residents", {}).items():
        if "goblin" not in table:
            fail(f"[residents.{place}] needs `goblin` (the role of every unnamed resident)")
        for k, v in table.items():
            if v not in roles:
                fail(f"[residents.{place}] {k} = {v!r} is not a [[role]]")


def roles(g: dict) -> dict:
    return {r["id"]: r for r in g.get("role", [])}


def hand_items(role: dict) -> list:
    """Mob HandItems for a role: [main, off], an empty compound for an empty hand (1.21 item stack format)."""
    return [{"id": role[slot], "count": 1} if role.get(slot) else {} for slot in ("main", "off")]


def objectives(g: dict, role: dict) -> list:
    """The Easy NPC objective types of a role's ai."""
    return list(g["ai"][role["ai"]]["easy_npc"])
