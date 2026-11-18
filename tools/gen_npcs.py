#!/usr/bin/env python3
"""Write the Easy NPC presets for the guild NPCs (Fuze, the receptionists) from design/data/npcs.toml.

One file per [[kind]]: pack/config/easy_npc/preset/<preset_prefix><id>.npc.snbt, an Easy NPC 7.19 `custom` preset
(`/easy_npc preset import_new custom easy_npc:preset/<file name> <x> <y> <z>`). The format follows the presets that ship
inside the mod (data/easy_npc/default_preset/humanoid/threshold_warden.npc.snbt). Every button runs the PLAYER's own
`/ttl guild ...` command (action flag ExecAsUser, command level 0); security.cfg lists `ttl` in
executeAsUserCommandAllowList.ALL for that.

Usage: gen_npcs.py           write the presets
       gen_npcs.py --check   exit 1 if a preset is stale (used by validate.py)
"""
import re
import sys
import tomllib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "design" / "data"
TARGET = ROOT / "pack" / "config" / "easy_npc" / "preset"
NAMESPACE = uuid.UUID("5d0f6f2a-7c1e-4a55-9a52-0f7e4d2f6b11")  # fixed: the PresetUUID of a kind never changes
MAX_LABEL = 32  # Easy NPC: MAX_DIALOG_LABEL_LENGTH / MAX_BUTTON_LABEL_LENGTH


class Raw(str):
    """An SNBT literal written as is (1b, 0.5f, [I;...])."""


def q(s: str) -> str:
    """SNBT double-quoted string."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def snbt(v, level: int = 0) -> str:
    pad = "  " * (level + 1)
    end = "  " * level
    if isinstance(v, Raw):
        return str(v)
    if isinstance(v, str):
        return q(v)
    if isinstance(v, bool):
        return "1b" if v else "0b"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[\n" + ",\n".join(pad + snbt(x, level + 1) for x in v) + "\n" + end + "]"
    if isinstance(v, dict):
        if not v:
            return "{}"
        return "{\n" + ",\n".join(f"{pad}{k}:{snbt(x, level + 1)}" for k, x in v.items()) + "\n" + end + "}"
    raise TypeError(type(v))


def command(cmd: str) -> dict:
    return {"Cmd": cmd, "ExecAsUser": True, "PermLevel": 0, "Type": "COMMAND"}


def open_dialog(label: str) -> dict:
    return {"Cmd": label, "Type": "OPEN_NAMED_DIALOG"}


CLOSE = {"Type": "CLOSE_DIALOG"}


def button(label: str, name: str, *actions: dict) -> dict:
    if len(label) > MAX_LABEL or len(name) > MAX_LABEL:
        raise SystemExit(f"npcs.toml: button {name!r} / label {label!r} is longer than {MAX_LABEL} characters")
    return {"Actions": list(actions), "Label": label, "Name": name}


def preset_uuid(kind_id: str) -> Raw:
    n = uuid.uuid5(NAMESPACE, kind_id).int
    parts = [(n >> shift) & 0xFFFFFFFF for shift in (96, 64, 32, 0)]
    parts = [p - (1 << 32) if p >= 1 << 31 else p for p in parts]
    return Raw("[I;" + ",".join(str(p) for p in parts) + "]")


def build(kind: dict, eco_guild: dict) -> str:
    d = kind["dialog"]
    giver = kind["giver"]
    slots = int(eco_guild["fuze_daily"] + eco_guild["fuze_weekly"]) if giver == "fuze" else int(eco_guild["daily"] + eco_guild["weekly"])
    # Hand-in: a receptionist also takes Fuze's contracts only when the knob says so.
    turnin = "/ttl guild turnin" if giver == "desk" and eco_guild.get("fuze_turnin_at_desk") else f"/ttl guild turnin {giver}"
    text = lambda s: s.replace("{max}", str(eco_guild["max_active"]))  # noqa: E731

    default = {
        "Buttons": [
            button("button_board", d["board"], command(f"/ttl guild board {giver}"), CLOSE),
            button("button_take", d["take"], command(f"/ttl guild board {giver}"), open_dialog("take")),
            button("button_turnin", d["turnin"], command(turnin), CLOSE),
            button("button_rank", d["rank"], command("/ttl guild status"), CLOSE),
            button("button_leave", d["leave"], CLOSE),
        ],
        "Label": "default",
        "Name": d["title"],
        "Priority": 5,
        "Texts": [{"Text": text(d["text"]).replace("\n", "\\n")}],
    }
    take = {
        "Buttons": [button(f"button_slot_{n}", d["take_item"].replace("{n}", str(n)),
                           command(f"/ttl guild take {n} {giver}"), CLOSE) for n in range(1, slots + 1)]
        + [button("button_back", d["back"], open_dialog("default"))],
        "Label": "take",
        "Name": d["take_title"],
        "Priority": -1,
        "Texts": [{"Text": text(d["take_text"]).replace("\n", "\\n")}],
    }
    custom_name = '{"color":"%s","text":"%s"}' % (kind["name_color"], kind["name"])
    data = {
        "ActionData": {"ActionEventSet": {"ON_INTERACTION": [{"Type": "OPEN_DEFAULT_DIALOG"}]}},
        "CustomName": Raw("'" + custom_name + "'"),
        "CustomNameVisible": True,
        "DialogData": {"DialogDataSet": [default, take], "Type": "STANDARD"},
        "EasyNPCVersion": 3,
        "Invulnerable": True,
        "ObjectiveData": {"ObjectiveDataSet": [{"Type": "LOOK_AT_PLAYER"}, {"Type": "LOOK_AT_RESET"}]},
        "PersistenceRequired": True,
        "PresetUUID": preset_uuid(kind["id"]),
        "VariantType": kind["skin"],
        "id": "easy_npc:humanoid",
    }
    meta = {
        "access": "PUBLIC",
        "author": "OCS Two Lives",
        "category": "Guild",
        "created": Raw("1790000000000L"),
        "description": kind["description"],
        "entityTypeId": "easy_npc:humanoid",
        "modified": Raw("1790000000000L"),
        "name": kind["name"],
        "variantType": kind["skin"],
        "version": "1.0.0",
    }
    return snbt({"PresetMetadata": meta, "data": data}) + "\n"


def check_npcs(npcs: dict, eco: dict) -> None:
    kinds = {k["id"]: k for k in npcs["kind"]}
    if len(kinds) != len(npcs["kind"]):
        raise SystemExit("npcs.toml: [[kind]] ids must be unique")
    for k in npcs["kind"]:
        if k["giver"] not in ("desk", "fuze"):
            raise SystemExit(f"npcs.toml: kind {k['id']}: giver is desk or fuze")
        for key in ("board", "take", "turnin", "rank", "leave", "take_title", "take_text", "take_item", "back", "title", "text"):
            if not k.get("dialog", {}).get(key):
                raise SystemExit(f"npcs.toml: kind {k['id']}: dialog.{key} missing")
    ids, by_tag = set(), {}
    for s in npcs["spot"]:
        where = f"npcs.toml: spot {s.get('id', '?')}"
        if s["id"] in ids or not s["id"].replace("_", "").isalnum() or not s["id"].islower():
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        ids.add(s["id"])
        if s["kind"] not in kinds:
            raise SystemExit(f"{where}: kind {s['kind']!r} is not a [[kind]]")
        prefix = "ttl.npc." + s["kind"]
        if not (s["tag"] == prefix or s["tag"].startswith(prefix + ".")) or not all(c.isalnum() or c in "._" for c in s["tag"]):
            raise SystemExit(f"{where}: tag must be {prefix} or {prefix}.<n>")
        if s["anchor"] not in ("tempest", "world", "build"):
            raise SystemExit(f"{where}: anchor is tempest, world or build")
        if (s["anchor"] == "build") != ("build" in s) or ("build" in s and not re.fullmatch(r"[a-z0-9_]+", s["build"])):
            raise SystemExit(f"{where}: anchor = \"build\" needs build = \"<name>\" (and only then)")
        if not all(isinstance(s[a], int) for a in ("x", "y", "z", "yaw")):
            raise SystemExit(f"{where}: x, y, z, yaw are integers")
        if s["enabled"]:
            by_tag.setdefault(s["tag"], []).append(s)
    # One tag may be shared only by a spot and its stand-ins (unless_build): exactly one Fuze, one receptionist per tag.
    for tag, group in by_tag.items():
        main = [s for s in group if "unless_build" not in s]
        if len(main) > 1:
            raise SystemExit(f"npcs.toml: tag {tag} is used by several enabled spots: {', '.join(s['id'] for s in main)}")
        for s in group:
            if "unless_build" in s and not any(m.get("build") == s["unless_build"] for m in main):
                raise SystemExit(f"npcs.toml: spot {s['id']}: unless_build {s['unless_build']!r} needs a spot with the same "
                                 f"tag anchored to that build")
    if not (isinstance(npcs["settings"]["rev"], int) and npcs["settings"]["check_ticks"] >= 100):
        raise SystemExit("npcs.toml: settings.rev is an integer and check_ticks >= 100")


def render() -> dict:
    npcs = tomllib.loads((DATA / "npcs.toml").read_text(encoding="utf-8"))
    eco = tomllib.loads((DATA / "economy.toml").read_text(encoding="utf-8"))
    check_npcs(npcs, eco)
    prefix = npcs["settings"]["preset_prefix"]
    return {TARGET / f"{prefix}{k['id']}.npc.snbt": build(k, eco["guild"]) for k in npcs["kind"]}


def main() -> None:
    files = render()
    if "--check" in sys.argv:
        stale = [p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        for p in stale:
            print(f"FAIL {p.relative_to(ROOT)} is stale: run python tools/gen_npcs.py")
        sys.exit(1 if stale else 0)
    TARGET.mkdir(parents=True, exist_ok=True)
    for p, text in files.items():
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
