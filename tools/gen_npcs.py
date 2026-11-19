#!/usr/bin/env python3
"""Write the Easy NPC presets for the NPCs of design/data/npcs.toml: the guild NPCs (Fuze, the receptionists) and the story
cast (Benimaru, Shuna, ..., WP-S4 of design/architecture/story-characters.md).

One file per Easy NPC [[kind]]: pack/config/easy_npc/preset/<prefix><id>.npc.snbt, an Easy NPC 7.19 `custom` preset
(`/easy_npc preset import_new custom easy_npc:preset/<file name> <x> <y> <z>`); <prefix> is settings.preset_prefix for a guild
kind and settings.cast_prefix for a story kind. The format follows the presets that ship inside the mod
(data/easy_npc/default_preset/humanoid/threshold_warden.npc.snbt). Every button runs the PLAYER's own command (action flag
ExecAsUser, command level 0): `/ttl guild ...` for the guild, `/ttl story talk <id>` for the cast; security.cfg lists `ttl` in
executeAsUserCommandAllowList.ALL for that. A kind with `statue = "<entity id>"` has no preset: guild_npcs.js and story/cast.js
spawn that mod entity as a tame statue.

Skins. `skin` is one of Easy NPC's built-in variants of the kind's `model` (humanoid or humanoid_slim; the lists below were read
from HumanoidSkinVariant / HumanoidSlimSkinVariant in the 7.19 jar). A kind also uses our own PNG when that file exists:
pack/kubejs/assets/ttl/textures/entity/npc/<kind id>.png (64x64), written into the preset as
`SkinData:{Type:"RESOURCE_LOCATION",Texture:"ttl:textures/entity/npc/<kind id>.png"}` (SkinDataEntry in the jar reads exactly
those tags; KubeJS assets ship to every client). `skin = "ttl:textures/entity/npc/<name>.png"` points a kind at another file; the
built-in variant is then given by `variant`. A PNG that is added later is picked up by the next run of this script.

Side content wears a `look` (tools/npc_looks.py): the variant its name picks, a skin of tools/gen_npc_looks.py or a mod's
own player-layout texture, goes into SkinData the same way.

Side content (design/data/sidequests.toml, sidequests work package): one preset per [[adventurer]] (ttl_adv_<id>: strolls
round its home, speech-bubble lines, Hire / Work / Farewell buttons), per hireable adventurer (ttl_comp_<id>: vulnerable,
melee, fights what attacks it or its owner; owner and FOLLOW_OWNER are set by sidequests/companions.js after the import)
and per [[client]] (ttl_client_<id>: an escort client, vulnerable; FOLLOW_PLAYER is set by sidequests/side.js). `--spots`
also checks the build-, Tempest- and Dwargon-anchored [[place]] homes and inns of that file.

Usage: gen_npcs.py           write the presets
       gen_npcs.py --check   exit 1 if a preset is stale (used by validate.py)
       gen_npcs.py --spots   also check every spot against the structure files of its build (slow: reads the .nbt files):
                             the NPC must stand on a solid block with two free blocks above
"""
import json
import re
import struct
import sys
import tomllib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))  # python -I
import anchor_refs  # noqa: E402
import npc_gear_check  # noqa: E402
import npc_looks  # noqa: E402

DATA = ROOT / "design" / "data"
TARGET = ROOT / "pack" / "config" / "easy_npc" / "preset"
ASSETS = ROOT / "pack" / "kubejs" / "assets"
STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
NAMESPACE = uuid.UUID("5d0f6f2a-7c1e-4a55-9a52-0f7e4d2f6b11")  # fixed: the PresetUUID of a kind never changes
MAX_LABEL = 32  # Easy NPC: MAX_DIALOG_LABEL_LENGTH / MAX_BUTTON_LABEL_LENGTH
# Built-in skin variants (assets/easy_npc/textures/entity/humanoid*, enums in the 7.19 jar).
VARIANTS = {
    "humanoid": ("ALEX", "ARI", "EFE", "KAI", "MAKENA", "NOOR", "STEVE", "SUNNY", "ZURI", "JAYJASONBO", "PROFESSOR_01",
                 "SECURITY_01", "KNIGHT_01", "KNIGHT_02", "FARMER_01"),
    "humanoid_slim": ("ALEX", "ARI", "EFE", "KAI", "MAKENA", "NOOR", "STEVE", "SUNNY", "ZURI", "KAWORRU", "MAGE_01"),
}
# Where the structure of a build puts the anchors of npcs.toml: Tempest's arrival point, blueprint (45, 5, 57)
# (blueprints/tempest.py ARRIVAL); a `build` anchor is the blueprint origin itself.
TEMPEST_ARRIVAL = (45, 5, 57)


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


def is_resource(skin: str) -> bool:
    return ":" in skin


def variant_of(kind: dict) -> str:
    """The built-in variant: `skin`, or `variant` when `skin` names a texture of ours."""
    skin = kind["skin"]
    return kind["variant"] if is_resource(skin) else skin


def texture_of(kind: dict) -> str | None:
    """The resource location of our own skin PNG for this kind, when that file exists, else None."""
    skin = kind["skin"]
    rl = skin if is_resource(skin) else f"ttl:textures/entity/npc/{kind['id']}.png"
    ns, path = rl.split(":", 1)
    return rl if (ASSETS / ns / path).is_file() else None


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise SystemExit(f"{path.relative_to(ROOT)} is not a PNG file")
    return struct.unpack(">II", head[16:24])


def entity_id(kind: dict) -> str:
    return "easy_npc:" + kind.get("model", "humanoid")


def look(kind: dict) -> dict:
    """VariantType, and SkinData too when our own texture exists."""
    out = {"VariantType": variant_of(kind)}
    texture = texture_of(kind)
    if texture:
        out["SkinData"] = {"Texture": texture, "Type": "RESOURCE_LOCATION"}
    return out


def build(kind: dict, eco_guild: dict) -> str:
    d = kind["dialog"]
    giver = kind["giver"]
    slots = int(eco_guild["fuze_daily"] + eco_guild["fuze_weekly"]) if giver == "fuze" else int(eco_guild["daily"] + eco_guild["weekly"])
    # Hand-in per giver; guild.js decides what each one takes (economy.toml fuze_turnin_at_desk + per-contract `lore`).
    turnin = f"/ttl guild turnin {giver}"
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
        **look(kind),
        "id": entity_id(kind),
    }
    meta = {
        "access": "PUBLIC",
        "author": "OCS Two Lives",
        "category": "Guild",
        "created": Raw("1790000000000L"),
        "description": kind["description"],
        "entityTypeId": entity_id(kind),
        "modified": Raw("1790000000000L"),
        "name": kind["name"],
        "variantType": variant_of(kind),
        "version": "1.0.0",
    }
    return snbt({"PresetMetadata": meta, "data": data}) + "\n"


def build_talk(kind: dict) -> str:
    """A story cast preset: one intro dialog with a Talk button (`/ttl story talk <id>`, the words live in story.toml) and Leave."""
    d = kind.get("dialog", {})
    default = {
        "Buttons": [
            button("button_talk", d.get("talk", "Talk"), command(f"/ttl story talk {kind['talk']}"), CLOSE),
            button("button_leave", d.get("leave", "Goodbye"), CLOSE),
        ],
        "Label": "default",
        "Name": d.get("title", kind["name"]),
        "Priority": 5,
        "Texts": [{"Text": d.get("text", "@initiator.").replace("\n", "\\n")}],
    }
    custom_name = '{"color":"%s","text":"%s"}' % (kind["name_color"], kind["name"])
    data = {
        "ActionData": {"ActionEventSet": {"ON_INTERACTION": [{"Type": "OPEN_DEFAULT_DIALOG"}]}},
        "CustomName": Raw("'" + custom_name + "'"),
        "CustomNameVisible": True,
        "DialogData": {"DialogDataSet": [default], "Type": "STANDARD"},
        "EasyNPCVersion": 3,
        "Invulnerable": True,
        "ObjectiveData": {"ObjectiveDataSet": [{"Type": "LOOK_AT_PLAYER"}, {"Type": "LOOK_AT_RESET"}]},
        "PersistenceRequired": True,
        "PresetUUID": preset_uuid(kind["id"]),
        **look(kind),
        "id": entity_id(kind),
    }
    meta = {
        "access": "PUBLIC",
        "author": "OCS Two Lives",
        "category": "Story",
        "created": Raw("1790000000000L"),
        "description": kind["description"],
        "entityTypeId": entity_id(kind),
        "modified": Raw("1790000000000L"),
        "name": kind["name"],
        "variantType": variant_of(kind),
        "version": "1.0.0",
    }
    return snbt({"PresetMetadata": meta, "data": data}) + "\n"


SIDE_PREFIXES = {"adventurer": "ttl_adv_", "companion": "ttl_comp_", "client": "ttl_client_"}


def side_look(kind: dict, own: str) -> dict:
    """Built-in variant, plus the skin of the kind's `look` (tools/npc_looks.py: the variant its name picks), else our
    PNG ttl:textures/entity/npc/<own>.png when it exists."""
    out = {"VariantType": kind["skin"]}
    if kind.get("look"):
        n = npc_looks.pick(kind["look"], kind.get("look_name", kind["name"]), kind.get("model", "humanoid"))
        rl = npc_looks.texture(kind["look"], n)
        ns, path = rl.split(":", 1)
        if ns == "ttl" and not (ASSETS / ns / path).is_file():
            raise SystemExit(f"sidequests.toml: {kind['id']}: look {kind['look']} #{n} has no {rl}: run python tools/gen_npc_looks.py")
        out["SkinData"] = {"Texture": rl, "Type": "RESOURCE_LOCATION"}
        return out
    rl = f"ttl:textures/entity/npc/{own}.png"
    if (ASSETS / "ttl" / rl.split(":", 1)[1]).is_file():
        out["SkinData"] = {"Texture": rl, "Type": "RESOURCE_LOCATION"}
    return out


GEAR = npc_gear_check.load()


def gear(kind: dict, role_kind: str) -> tuple[dict, list]:
    """(Mob NBT for the hands and zero drop chances, extra Easy NPC objectives) of a side kind's npc_gear.toml role. A
    companion keeps its own fighting objectives and only takes the role's items."""
    role = npc_gear_check.roles(GEAR).get(kind.get("role", ""))
    if not role:
        return {}, []
    nbt = {"ArmorDropChances": Raw("[0.0f,0.0f,0.0f,0.0f]"), "HandDropChances": Raw("[0.0f,0.0f]"),
           "HandItems": npc_gear_check.hand_items(role)}
    if role_kind == "companion":
        return nbt, []
    extra = []
    for o in npc_gear_check.objectives(GEAR, role):
        speed = npc_gear_check.SPEED.get(o)
        extra.append({"SpeedModifier": Raw(speed), "Type": o} if speed else {"Type": o})
    return nbt, extra


def message(texts: list, chance: int | None) -> dict:
    """An Easy NPC MESSAGE action shown as a speech bubble only (MessageActionData bit 4 of T), one text picked at random."""
    entry = {"Msg": {"T": Raw("4b"), "Texts": list(texts)}, "Type": "MESSAGE"}
    if chance is not None:
        entry = {"ConditionDataSet": {"ConditionDataSet": [{"Type": "CHANCE", "Value": chance}]}, **entry}
    return entry


def side_preset(kind: dict, role: str) -> str:
    """role: adventurer (ambient, invulnerable), companion (hired, fights) or client (escort, follows the soul)."""
    own = ("client_" if role == "client" else "adv_") + kind["id"]
    title = kind.get("title")
    shown = f"{kind['name']}, {title}" if title and role != "client" else kind["name"]
    custom_name = json.dumps({"color": kind["name_color"], "text": shown}, separators=(",", ":"))
    lines = kind["lines"]
    objectives = [{"Type": "LOOK_AT_PLAYER"}, {"Type": "LOOK_AT_RESET"}, {"Type": "FLOAT"}]
    events = {"ON_INTERACTION": [{"Type": "OPEN_DEFAULT_DIALOG"}]}
    if role == "adventurer":
        hire = kind.get("hire")
        buttons = []
        if hire:
            buttons.append(button("button_hire", "Join my party", command("/ttl companion hire"), CLOSE))
        buttons += [button("button_work", "Heard of any work?", command("/ttl sidequest offers"), CLOSE),
                    button("button_leave", "Farewell", CLOSE)]
        intro = f"{kind['name']}, {title}, looks up. Well met, @initiator."
        if hire:
            intro += f"\n\nFor hire: rank {hire['rank']}, {hire['minutes']} minutes of company for a fee."
        objectives += [{"SpeedModifier": Raw("0.5d"), "Type": "RANDOM_STROLL_AROUND_HOME"},
                       {"SpeedModifier": Raw("0.6d"), "Type": "MOVE_BACK_TO_HOME"}]
        events["ON_INTERVAL_NORMAL"] = [message(lines, 20)]
        invulnerable = True
    elif role == "companion":
        buttons = [button("button_status", "How are you holding up?", command("/ttl companion status"), CLOSE),
                   button("button_dismiss", "Let us part ways", command("/ttl companion dismiss"), CLOSE),
                   button("button_leave", "Carry on", CLOSE)]
        intro = f"{kind['name']} checks the edge of the blade. Where to, @initiator?"
        objectives += [{"SpeedModifier": Raw("0.8d"), "Type": "MELEE_ATTACK"},
                       {"SpeedModifier": Raw("0.8d"), "Type": "ATTACK_MOB_WITHOUT_CREEPER"},
                       {"Type": "HURT_BY_TARGET"}, {"Type": "OWNER_HURT_BY_TARGET"}, {"Type": "OWNER_HURT_TARGET"}]
        events["ON_INTERVAL_LONG"] = [message(lines, 30)]
        events["ON_HURT"] = [message(["Ngh!", "That stung.", "Watch my back!"], 25)]
        invulnerable = False
    else:
        buttons = [button("button_status", "How far is it?", command("/ttl sidequest status"), CLOSE),
                   button("button_leave", "Stay close", CLOSE)]
        intro = f"{kind['name']} grips the strap of a pack. Lead on, @initiator. I will keep up."
        events["ON_INTERVAL_NORMAL"] = [message(lines, 25)]
        events["ON_HURT"] = [message(["Help!", "Get it off me!", "I am hit!"], None)]
        invulnerable = False
    default = {
        "Buttons": buttons,
        "Label": "default",
        "Name": kind["name"],
        "Priority": 5,
        "Texts": [{"Text": intro.replace("\n", "\\n")}],
    }
    hands, fight = gear(kind, role)
    have = {o["Type"] for o in objectives}
    objectives += [o for o in fight if o["Type"] not in have]
    data = {
        "ActionData": {"ActionEventSet": events},
        "CustomName": Raw("'" + custom_name.replace("\\", "\\\\").replace("'", "\\'") + "'"),
        "CustomNameVisible": True,
        "DialogData": {"DialogDataSet": [default], "Type": "STANDARD"},
        "EasyNPCVersion": 3,
        **hands,
        "Invulnerable": invulnerable,
        "ObjectiveData": {"ObjectiveDataSet": objectives},
        "PersistenceRequired": True,
        "PresetUUID": preset_uuid(f"{role}:{kind['id']}"),
        **side_look(kind, own),
        "id": "easy_npc:" + kind.get("model", "humanoid"),
    }
    meta = {
        "access": "PUBLIC",
        "author": "OCS Two Lives",
        "category": "Side",
        "created": Raw("1790000000000L"),
        "description": f"{role}: {shown} (design/data/sidequests.toml)",
        "entityTypeId": data["id"],
        "modified": Raw("1790000000000L"),
        "name": shown,
        "variantType": kind["skin"],
        "version": "1.0.0",
    }
    return snbt({"PresetMetadata": meta, "data": data}) + "\n"


def render_side() -> dict:
    path = DATA / "sidequests.toml"
    if not path.is_file():
        return {}
    sq = tomllib.loads(path.read_text(encoding="utf-8"))
    out = {}
    for k in sq.get("adventurer", []):
        out[TARGET / f"{SIDE_PREFIXES['adventurer']}{k['id']}.npc.snbt"] = side_preset(k, "adventurer")
        if k.get("hire"):
            out[TARGET / f"{SIDE_PREFIXES['companion']}{k['id']}.npc.snbt"] = side_preset(k, "companion")
    for k in sq.get("client", []):
        out[TARGET / f"{SIDE_PREFIXES['client']}{k['id']}.npc.snbt"] = side_preset(k, "client")
    return out


def check_places() -> list:
    """Homes and inns of sidequests.toml places anchored to a build, Tempest or Dwargon: solid floor, two free blocks."""
    path = DATA / "sidequests.toml"
    if not path.is_file():
        return []
    sq = tomllib.loads(path.read_text(encoding="utf-8"))
    problems, cache = [], {}
    for p in sq.get("place", []):
        if p["anchor"] not in ("build", "tempest", "dwargon"):
            continue
        build = {"tempest": "tempest", "dwargon": "dwargon"}.get(p["anchor"], p.get("build"))
        ox, oy, oz = TEMPEST_ARRIVAL if p["anchor"] == "tempest" else (0, 0, 0)
        if build not in cache:
            cache[build] = structure_blocks(build)
        blocks = cache[build]
        spots = [("home", (p["x"], p["y"], p["z"]))] + ([("inn", tuple(p["inn"]))] if "inn" in p else [])
        for label, (bx, by, bz) in spots:
            x, y, z = ox + bx, oy + by, oz + bz
            floor, feet, head = blocks.get((x, y - 1, z)), blocks.get((x, y, z)), blocks.get((x, y + 1, z))
            if floor is None or passable(floor) or "water" in floor or "lava" in floor or not passable(feet) or not passable(head):
                problems.append(f"sidequests.toml: place {p['id']} {label} ({build} {x} {y} {z}): floor {floor}, feet {feet}, head {head}")
    return problems


def check_npcs(npcs: dict, eco: dict, story: dict) -> None:
    where0 = "npcs.toml"
    kinds = {k["id"]: k for k in npcs["kind"]}
    if len(kinds) != len(npcs["kind"]) or not all(re.fullmatch(r"[a-z][a-z0-9_]*", k) for k in kinds):
        raise SystemExit(f"{where0}: [[kind]] ids must be unique [a-z0-9_]")
    talk_ids = {n["id"] for n in story.get("npc", [])}
    guild_keys = ("board", "take", "turnin", "rank", "leave", "take_title", "take_text", "take_item", "back", "title", "text")
    for k in npcs["kind"]:
        w = f"{where0}: kind {k['id']}"
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", k.get("name_color", "")) or not k.get("name") or not k.get("description"):
            raise SystemExit(f"{w}: name, description and name_color (#RRGGBB) are needed")
        if "'" in k["name"] or '"' in k["name"]:
            raise SystemExit(f"{w}: the name goes into a JSON text component: no quotes")
        if "talk" in k:
            if k["talk"] not in talk_ids:
                raise SystemExit(f"{w}: talk = {k['talk']!r} is not an [[npc]] of story.toml ({', '.join(sorted(talk_ids))})")
            if "giver" in k:
                raise SystemExit(f"{w}: a story kind (talk) has no giver")
        elif k.get("giver") not in ("desk", "fuze"):
            raise SystemExit(f"{w}: giver is desk or fuze (or give the kind a talk id)")
        if "statue" in k:
            if "talk" not in k or not re.fullmatch(r"[a-z0-9_]+:[a-z0-9_/]+", k["statue"]):
                raise SystemExit(f'{w}: statue = "<namespace:entity>" needs a talk id')
            for key in ("skin", "model", "dialog", "variant", "giver"):
                if key in k:
                    raise SystemExit(f"{w}: a statue is a mod entity: no {key}")
            continue
        model = k.get("model", "humanoid")
        if model not in VARIANTS:
            raise SystemExit(f"{w}: model is {' or '.join(VARIANTS)}")
        skin = k.get("skin", "")
        if is_resource(skin):
            if not re.fullmatch(r"ttl:textures/entity/npc/[a-z0-9_]+\.png", skin):
                raise SystemExit(f"{w}: a skin texture is ttl:textures/entity/npc/<name>.png")
            if k.get("variant") not in VARIANTS[model]:
                raise SystemExit(f"{w}: skin names a texture, so `variant` must be a built-in {model} variant")
        elif skin not in VARIANTS[model]:
            raise SystemExit(f"{w}: skin {skin!r} is not a built-in {model} variant ({', '.join(VARIANTS[model])})")
        elif "variant" in k:
            raise SystemExit(f"{w}: `variant` only goes with a texture in `skin`")
        texture = texture_of(k)
        if texture:
            path = ASSETS / "ttl" / texture.split(":", 1)[1]
            if png_size(path) not in ((64, 64), (128, 128)):
                raise SystemExit(f"{path.relative_to(ROOT)} must be a 64x64 Minecraft skin, is {png_size(path)}")
        if "talk" not in k:
            for key in guild_keys:
                if not k.get("dialog", {}).get(key):
                    raise SystemExit(f"{w}: dialog.{key} missing")
        for key in ("talk", "leave"):
            if len(k.get("dialog", {}).get(key, "")) > MAX_LABEL:
                raise SystemExit(f"{w}: dialog.{key} is longer than {MAX_LABEL} characters")
    ids, by_tag = set(), {}
    for s in npcs["spot"]:
        where = f"{where0}: spot {s.get('id', '?')}"
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
            raise SystemExit(f'{where}: anchor = "build" needs build = "<name>" (and only then)')
        for b in (s.get("build"), s.get("unless_build")):
            if b and not (ROOT / "design" / "builds" / f"{b}.toml").is_file():
                raise SystemExit(f"{where}: build {b!r} has no design/builds/{b}.toml")
        if "surface" in s and (s["surface"] is not True or s["anchor"] != "world"):
            raise SystemExit(f"{where}: surface = true only goes with anchor = \"world\"")
        if "at" in s:
            if s["anchor"] != "world":
                raise SystemExit(f"{where}: at = \"<anchors.toml id>\" only goes with anchor = \"world\"")
            anchor_refs.resolve_at(where, s)
        if not all(isinstance(s.get(a), int) for a in ("x", "y", "z", "yaw")):
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
    hook_ids = set()
    for h in npcs.get("hook", []):
        w = f"{where0}: hook {h.get('id', '?')}"
        if h.get("id") in hook_ids or not re.fullmatch(r"[a-z][a-z0-9_]*", h.get("id", "")):
            raise SystemExit(f"{w}: id must be unique [a-z0-9_]")
        hook_ids.add(h["id"])
        if not re.fullmatch(r"[A-Za-z0-9_.]+", h.get("tag", "")):
            raise SystemExit(f"{w}: tag is the entity tag the hook listens to")
        if h.get("talk") not in talk_ids:
            raise SystemExit(f"{w}: talk = {h.get('talk')!r} is not an [[npc]] of story.toml")
    settings = npcs["settings"]
    if not (isinstance(settings["rev"], int) and settings["check_ticks"] >= 100):
        raise SystemExit("npcs.toml: settings.rev is an integer and check_ticks >= 100")
    for key in ("preset_prefix", "cast_prefix"):
        if not re.fullmatch(r"[a-z0-9_]+", settings.get(key, "")):
            raise SystemExit(f"npcs.toml: settings.{key} is a [a-z0-9_] word")
    if settings["preset_prefix"] == settings["cast_prefix"]:
        raise SystemExit("npcs.toml: settings.preset_prefix and settings.cast_prefix must differ")
    if not (isinstance(settings.get("interact_cooldown_ms"), int) and settings["interact_cooldown_ms"] >= 0):
        raise SystemExit("npcs.toml: settings.interact_cooldown_ms is a whole number of milliseconds")


# ---- spots against the structure files (--spots) -------------------------------------------------------------------------

# Blocks an NPC may stand in: air and things without a collision box.
PASSABLE = ("air", "carpet", "torch", "lantern", "banner", "flower", "_pot", "sign", "button", "pressure_plate", "rail",
            "ladder", "vine", "sapling", "short_grass", "tall_grass", "fern", "bush", "tulip", "daisy", "bluet", "candle",
            "_head", "_skull", "lever", "tripwire", "snow", "moss_carpet", "allium", "cornflower", "dandelion", "poppy",
            "lily_of_the_valley", "wheat", "carrots", "potatoes", "beetroots")


def passable(block: str | None) -> bool:
    name = block.split("[")[0].removeprefix("minecraft:") if block else "air"
    return any(p in name for p in PASSABLE)


def structure_blocks(name: str) -> dict:
    """{(x, y, z): block id} of a build's structure files, the z slabs of a PARTS build stacked in order."""
    sys.path.insert(0, str(ROOT / "tools"))
    import nbt  # noqa: E402
    single = STRUCTURES / f"{name}.nbt"
    files = [single] if single.exists() else []
    while not single.exists() and (STRUCTURES / f"{name}_{len(files)}.nbt").exists():
        files.append(STRUCTURES / f"{name}_{len(files)}.nbt")
    if not files:
        raise SystemExit(f"no structure {name}.nbt or {name}_0.nbt in {STRUCTURES.relative_to(ROOT)}")
    out, z0 = {}, 0
    for path in files:
        root = nbt.read_gzip(path)
        palette = root.get("palette") or (root.get("palettes") or [[]])[0]
        names = [e["Name"] for e in palette]
        for b in root.get("blocks", []):
            x, y, z = b["pos"]
            out[(x, y, z + z0)] = names[b["state"]]
        z0 += root["size"][2]
    return out


def check_spots(npcs: dict) -> list:
    """Every build-anchored and Tempest-anchored spot must stand on a solid block with two free blocks above it."""
    problems, cache = [], {}
    for s in npcs["spot"]:
        if s["anchor"] == "world":
            continue
        build = "tempest" if s["anchor"] == "tempest" else s["build"]
        ox, oy, oz = TEMPEST_ARRIVAL if s["anchor"] == "tempest" else (0, 0, 0)
        x, y, z = ox + s["x"], oy + s["y"], oz + s["z"]
        if build not in cache:
            cache[build] = structure_blocks(build)
        blocks = cache[build]
        floor, feet, head = blocks.get((x, y - 1, z)), blocks.get((x, y, z)), blocks.get((x, y + 1, z))
        why = None
        if floor is None or passable(floor) or "water" in floor or "lava" in floor:
            why = f"no solid floor under it (blueprint {x} {y - 1} {z} is {floor})"
        elif not passable(feet) or not passable(head):
            why = f"is inside a block (blueprint {x} {y} {z} is {feet}, {x} {y + 1} {z} is {head})"
        if why:
            problems.append(f"npcs.toml: spot {s['id']} ({build}): {why}")
    return problems


def render() -> dict:
    npcs = tomllib.loads((DATA / "npcs.toml").read_text(encoding="utf-8"))
    eco = tomllib.loads((DATA / "economy.toml").read_text(encoding="utf-8"))
    story = tomllib.loads((DATA / "story.toml").read_text(encoding="utf-8"))
    check_npcs(npcs, eco, story)
    out = {}
    for k in npcs["kind"]:
        if "statue" in k:
            continue
        if "talk" in k:
            out[TARGET / f"{npcs['settings']['cast_prefix']}{k['id']}.npc.snbt"] = build_talk(k)
        else:
            out[TARGET / f"{npcs['settings']['preset_prefix']}{k['id']}.npc.snbt"] = build(k, eco["guild"])
    out.update(render_side())
    return out


def stale_files(files: dict) -> list:
    """Presets that are missing or differ, and generated presets of kinds that no longer exist."""
    stale = [p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    ours = [p for p in TARGET.glob("*.npc.snbt") if p.name.startswith(("ttl_guild_", "ttl_cast_") + tuple(SIDE_PREFIXES.values()))] if TARGET.is_dir() else []
    return stale + [p for p in ours if p not in files]


def main() -> None:
    files = render()
    problems = []
    if "--spots" in sys.argv:
        npcs = tomllib.loads((DATA / "npcs.toml").read_text(encoding="utf-8"))
        problems = check_spots(npcs) + check_places()
        for line in problems:
            print(f"FAIL {line}")
        if not problems:
            print(f"ok: {len(npcs['spot'])} spots (anchor 'world' is not checked) stand on solid ground with room above")
    if "--check" in sys.argv or "--spots" in sys.argv:
        stale = stale_files(files)
        for p in stale:
            print(f"FAIL {p.relative_to(ROOT)} is stale: run python tools/gen_npcs.py")
        sys.exit(1 if stale or problems else 0)
    TARGET.mkdir(parents=True, exist_ok=True)
    for p in stale_files(files):
        if p not in files:
            p.unlink()
            print(f"removed {p.relative_to(ROOT)}")
    for p, text in files.items():
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
