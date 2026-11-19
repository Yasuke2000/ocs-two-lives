#!/usr/bin/env python3
"""Generate pack/kubejs/server_scripts/ttl/generated/placements.js (TtlPlacementData) for the one-time world works:
the planted forests (design/data/forests/patches.toml + <id>.json, life/forests.js) and the trade roads
(design/data/trade_roads/roads.toml + <id>.json, life/trade_roads.js), plus Lerfing's keepouts (anchors.toml).

The <id>.json plans come from tools/lerfing/forests.py and tools/lerfing/trade_roads.py (they need the imported world);
this script only checks them against their configs and writes the script data, so it runs anywhere (validate.py, CI).
Usage: gen_placements.py            write the file
       gen_placements.py --check    exit 1 if it is out of date or a plan does not match its config
"""
import json
import re
import math
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import anchor_refs  # noqa: E402
from lerfing import forests, trade_roads  # noqa: E402

TARGET = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "placements.js"
FOREST_KEYS = {"title", "notes", "centre", "inner", "outer", "giants_outer", "giant_spacing", "understory_spacing", "seed",
               "road_gap", "version", "clear", "keep_clear", "lanes", "giants", "understory"}
ROAD_KEYS = {"title", "notes", "from", "to", "from_y", "to_y", "via", "avoid", "half", "max_grade", "lantern_every",
             "stone_from", "surface", "stone", "bridge", "version"}


def fail(msg):
    raise SystemExit(msg)


def check_weights(where, table):
    if not isinstance(table, dict) or not table:
        fail(f"{where}: needs at least one id = weight")
    for k, v in table.items():
        if ":" not in k or not isinstance(v, int) or v <= 0:
            fail(f"{where}: {k} = {v!r} (a namespaced id = a positive integer weight)")


def forest_entry(pid, cfg):
    where = f"design/data/forests/patches.toml [{pid}]"
    extra = set(cfg) - FOREST_KEYS
    if extra:
        fail(f"{where}: unknown keys {sorted(extra)}")
    for k in ("centre", "inner", "outer", "version", "giants", "understory"):
        if k not in cfg:
            fail(f"{where}: missing {k}")
    check_weights(f"{where}.giants", cfg["giants"])
    check_weights(f"{where}.understory", cfg["understory"])
    for tid in cfg["giants"]:
        if tid not in forests.TEMPLATES:
            fail(f"{where}: giant {tid} is not a known ancient-forest template (tools/lerfing/forests.py TEMPLATES)")
    plan = forests.stored(pid)
    if plan is None:
        fail(f"{where}: no plan; run python -I tools/lerfing/forests.py plan {pid} --world <import dir>")
    if plan["giant_keys"] != sorted(cfg["giants"]) or plan["features"] != sorted(cfg["understory"]):
        fail(f"{where}: the palette changed since design/data/forests/{pid}.json was planned: plan it again")
    centre = anchor_refs.point(where, cfg["centre"])
    if list(centre) != plan["centre"]:
        fail(f"{where}: centre {cfg['centre']} is at {centre}, the plan at {plan['centre']}: plan it again")
    clear = []
    for c in cfg.get("clear", []):
        ax, az = anchor_refs.point(where, c["anchor"])
        clear.append([ax + c["x0"], az + c["z0"], ax + c["x1"], az + c["z1"]])
    keep = []
    for k in cfg.get("keep_clear", []):
        kind = "build" if "build" in k else "landmark" if "landmark" in k else None
        if kind is None or len(k["offline"]) != 4:
            fail(f"{where}: keep_clear needs build or landmark and offline = [x0, z0, x1, z1]")
        keep.append({"kind": kind, "name": k[kind], "pad": k.get("pad", 0), "offline": k["offline"]})
    lanes = []
    for ln in cfg.get("lanes", []):
        if ln["side"] not in ("west", "east", "north", "south"):
            fail(f"{where}: lane side {ln['side']!r}")
        lanes.append({"build": ln["build"], "side": ln["side"], "toward": list(anchor_refs.point(where, ln["toward"])),
                      "length": ln["length"], "half": ln["half"], "offline": ln["offline"]})
    # every planned crown in the ring, clear of the clear boxes and Lerfing's keepouts
    kos = [(k["x0"], k["z0"], k["x1"], k["z1"]) for k in anchor_refs.keepouts()]
    for ti, x, z, ri in plan["giants"]:
        tp = plan["templates"][plan["giant_keys"][ti]]
        b = forests.giant_box(tp, x, z, forests.ROTATIONS[ri])[2:]
        r = math.hypot(x - centre[0], z - centre[1])
        if not cfg["inner"] <= r <= cfg["outer"]:
            fail(f"{where}: giant at {x} {z} is {r:.0f} from the centre, outside {cfg['inner']}..{cfg['outer']}")
        for o in clear + [list(k) for k in kos]:
            if forests.box_hit(b, o):
                fail(f"{where}: the giant at {x} {z} reaches the kept box {o}: plan it again")
    return {
        "title": cfg["title"], "version": cfg["version"], "centre": list(centre), "inner": cfg["inner"],
        "outer": cfg["outer"], "road_gap": cfg.get("road_gap", 3), "clear": clear, "keep_clear": keep, "lanes": lanes,
        "templates": plan["templates"], "giant_keys": plan["giant_keys"], "features": plan["features"],
        "giants": plan["giants"], "understory": plan["understory"],
    }


def road_entry(rid, cfg):
    where = f"design/data/trade_roads/roads.toml [{rid}]"
    extra = set(cfg) - ROAD_KEYS
    if extra:
        fail(f"{where}: unknown keys {sorted(extra)}")
    for k in ("from", "to", "half", "max_grade", "version", "surface", "stone", "bridge"):
        if k not in cfg:
            fail(f"{where}: missing {k}")
    check_weights(f"{where}.surface", cfg["surface"])
    check_weights(f"{where}.stone", cfg["stone"])
    road = trade_roads.stored(rid)
    if road is None:
        fail(f"{where}: no plan; run python -I tools/lerfing/trade_roads.py plan {rid} --world <import dir>")
    a = list(anchor_refs.point(where, cfg["from"]["anchor"], cfg["from"].get("dx", 0), cfg["from"].get("dz", 0)))
    b = list(anchor_refs.point(where, cfg["to"]["anchor"], cfg["to"].get("dx", 0), cfg["to"].get("dz", 0)))
    if road["points"][0] != a or road["points"][-1] != b:
        fail(f"{where}: the plan runs {road['points'][0]} -> {road['points'][-1]}, the config {a} -> {b}: plan it again")
    n = len(trade_roads.arc_samples(road["points"]))
    if len(road["profile"]) != n:
        fail(f"{where}: profile has {len(road['profile'])} samples, the polyline {n}: plan it again")
    if "to_y" in cfg and road["profile"][-1] != cfg["to_y"]:
        fail(f"{where}: the profile ends at y {road['profile'][-1]}, to_y is {cfg['to_y']}")
    steps = [abs(q - p) for p, q in zip(road["profile"], road["profile"][1:])]
    if steps and max(steps) > 1:
        fail(f"{where}: the profile jumps {max(steps)} blocks in one step")
    return {
        "title": cfg["title"], "version": cfg["version"], "half": cfg["half"],
        "lantern_every": cfg.get("lantern_every", 0), "stone_from": cfg.get("stone_from", []),
        "surface": cfg["surface"], "stone": cfg["stone"], "bridge": cfg["bridge"],
        "points": road["points"], "profile": road["profile"], "bridges": road["bridges"],
        "length": road["stats"]["length"],
    }


FIXES = ROOT / "design" / "data" / "world_fixes.toml"
FILL = re.compile(r"^fill (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) \S+( (replace|keep|destroy|hollow|outline)( \S+)?)?$")


def fix_entry(fid, cfg):
    where = f"design/data/world_fixes.toml [{fid}]"
    for k in ("title", "why", "version", "area", "commands"):
        if k not in cfg:
            fail(f"{where}: missing {k}")
    if not isinstance(cfg["version"], int) or cfg["version"] < 1:
        fail(f"{where}: version must be an integer >= 1")
    a = cfg["area"]
    if len(a) != 4 or a[0] > a[2] or a[1] > a[3]:
        fail(f"{where}: area must be [x0, z0, x1, z1] with x0 <= x1, z0 <= z1")
    if ((a[2] >> 4) - (a[0] >> 4) + 1) * ((a[3] >> 4) - (a[1] >> 4) + 1) > 144:
        fail(f"{where}: area holds more than 144 chunks")
    for c in cfg["commands"]:
        m = FILL.match(c)
        if not c.startswith("fill "):
            continue
        if not m:
            fail(f"{where}: cannot read the fill '{c}'")
        x0, y0, z0, x1, y1, z1 = (int(v) for v in m.groups()[:6])
        vol = (abs(x1 - x0) + 1) * (abs(y1 - y0) + 1) * (abs(z1 - z0) + 1)
        if vol > 32768:
            fail(f"{where}: '{c}' fills {vol} blocks (at most 32768)")
        if min(x0, x1) < a[0] or max(x0, x1) > a[2] or min(z0, z1) < a[1] or max(z0, z1) > a[3]:
            fail(f"{where}: '{c}' leaves the area {a}")
    return {"title": cfg["title"], "version": cfg["version"], "area": a, "commands": cfg["commands"]}


def render():
    with forests.CONFIG.open("rb") as f:
        fcfg = tomllib.load(f)
    with trade_roads.CONFIG.open("rb") as f:
        rcfg = tomllib.load(f)
    for p in sorted(forests.FORESTS.glob("*.json")):
        if p.stem not in fcfg:
            fail(f"design/data/forests/{p.name}: no [{p.stem}] in patches.toml")
    for p in sorted(trade_roads.ROADS.glob("*.json")):
        if p.stem not in rcfg:
            fail(f"design/data/trade_roads/{p.name}: no [{p.stem}] in roads.toml")
    data = {
        "forests": {pid: forest_entry(pid, c) for pid, c in sorted(fcfg.items())},
        "roads": {rid: road_entry(rid, c) for rid, c in sorted(rcfg.items())},
        "keepouts": [[k["x0"], k["z0"], k["x1"], k["z1"], k["id"]] for k in anchor_refs.keepouts()],
        "fixes": {},
    }
    if FIXES.exists():
        with FIXES.open("rb") as f:
            xcfg = tomllib.load(f)
        data["fixes"] = {fid: fix_entry(fid, c) for fid, c in sorted(xcfg.items())}
    body = json.dumps(data, separators=(",", ":"), sort_keys=True)
    return ("// priority: 200\n"
            "// GENERATED by tools/gen_placements.py from design/data/forests/ and design/data/trade_roads/. Do not edit.\n"
            f"const TtlPlacementData = {body}\n")


def main():
    text = render()
    if "--check" in sys.argv:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print(f"FAIL {TARGET.relative_to(ROOT).as_posix()} is stale: run python tools/gen_placements.py")
            sys.exit(1)
        return
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
