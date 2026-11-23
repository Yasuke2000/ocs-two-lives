#!/usr/bin/env python3
"""ttl-forge: MCP server (stdio, JSON-RPC 2.0) that lets Claude plan, preview and place builds on the server.

    claude mcp add ttl-forge -- python -I tools/forge/mcp_server.py      (or the repo's .mcp.json)

The loop it is made for: read_region (what is there) -> preview_build (compile, check against the registry, lint,
render; no world write) -> look at the image, fix the program -> apply_build dry_run=true (counts, zone check) ->
apply_build dry_run=false (queued job, undo snapshot) -> job_status -> undo if it looks wrong.
World access goes through the ttl-portals bridge (tools/forge/client.py); everything else runs offline.
Docs: docs/dev/build-bridge.md. Stdlib only.
"""
import base64
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))

import check  # noqa: E402
import client  # noqa: E402
import program  # noqa: E402
import schem  # noqa: E402
from blueprint import _color, _write_png, parse_state  # noqa: E402

ROOT = program.ROOT
OUT = ROOT / "build" / "forge"
PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_IMAGE = 2_500_000

BOX = {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3}
DIM = {"type": "string", "description": "dimension id, default minecraft:overworld (ttl:mortal_realm for Life 1)"}
PROGRAM = {"description": "build program (object) or path to a .json file; see the preview_build description",
           "anyOf": [{"type": "object"}, {"type": "string"}]}

TOOLS = [
    {"name": "bridge_status",
     "description": "Is the bridge reachable: players online, MSPT, queued jobs, build zones and protected areas.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_registry",
     "description": "Real block ids (with state properties), biomes and dimensions from the running server. "
                    "refresh=true fetches it and caches design/dumps/registry.json; filter narrows the answer "
                    "(e.g. 'tensura:' or 'stairs'). Use it before writing any modded id.",
     "inputSchema": {"type": "object", "properties": {
         "refresh": {"type": "boolean"}, "filter": {"type": "string"},
         "limit": {"type": "integer", "description": "max blocks listed, default 80"}}}},
    {"name": "read_region",
     "description": "What is in the world. mode=summary: block and biome counts of a box; heightmap: surface heights, "
                    "blocks and biomes per column of from/to x,z (returned with a rendered map image); blocks: every "
                    "block of a small box (<= 64x64x64). load=false skips chunks that are not loaded.",
     "inputSchema": {"type": "object", "required": ["from", "to"], "properties": {
         "dim": DIM, "from": BOX, "to": BOX, "mode": {"enum": ["summary", "heightmap", "blocks"]},
         "surface": {"enum": ["world", "terrain"], "description": "heightmap: world = top block incl. trees; terrain = ground (no leaves)"},
         "load": {"type": "boolean"}}}},
    {"name": "preview_build",
     "description": "Compile a build program, check every block against the registry, lint it (floating parts, "
                    "falling sand, unsupported torches/doors) and render an isometric PNG. Writes nothing to the world. "
                    "Program: {name, size:[x,y,z], palette:{alias: state}, clear?, ops:[...]}. Ops: "
                    + "; ".join(f"{k}({v})" for k, v in program.OPS.items())
                    + ". Blocks use command syntax 'ns:id[prop=value]'; '$alias' refers to the palette.",
     "inputSchema": {"type": "object", "required": ["program"], "properties": {
         "program": PROGRAM, "view": {"enum": ["iso", "top", "both"], "description": "default iso"}}}},
    {"name": "apply_build",
     "description": "Place a build program in the world with its corner (0,0,0) at origin. dry_run (default true) "
                    "only reports cells set/changed, block entities replaced and the zone check. With dry_run=false "
                    "the bridge snapshots the box (for undo) and places it over several ticks; returns the job id.",
     "inputSchema": {"type": "object", "required": ["program", "origin"], "properties": {
         "program": PROGRAM, "origin": BOX, "dim": DIM, "dry_run": {"type": "boolean"},
         "label": {"type": "string"},
         "updates": {"enum": ["quiet", "neighbors"], "description": "quiet (default): no neighbour updates (no water flow, no redstone); neighbors: like /setblock"},
         "fix_shapes": {"type": "boolean", "description": "connect fences, panes and stairs after placing (default true)"}}}},
    {"name": "paste_structure",
     "description": "Place a saved build: a pack structure name (pack/kubejs/data/ttl/structure/<name>.nbt), a "
                    "blueprint name (blueprints/<name>.py) or a .nbt/.schem path. Same dry_run flow as apply_build.",
     "inputSchema": {"type": "object", "required": ["structure", "origin"], "properties": {
         "structure": {"type": "string"}, "origin": BOX, "dim": DIM, "rotate": {"enum": [0, 90, 180, 270]},
         "mirror": {"type": "boolean"}, "dry_run": {"type": "boolean"}, "label": {"type": "string"}}}},
    {"name": "set_biome",
     "description": "Set the biome of a box (vanilla fillbiome, chunk by chunk; players see it after the chunk resends). "
                    "Not undoable through the bridge: note the old biome with read_region first.",
     "inputSchema": {"type": "object", "required": ["from", "to", "biome"], "properties": {
         "dim": DIM, "from": BOX, "to": BOX, "biome": {"type": "string"}, "dry_run": {"type": "boolean"}}}},
    {"name": "job_status", "description": "Progress of a bridge job (phase, changed cells, error).",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
    {"name": "list_jobs", "description": "Recent bridge jobs, newest first (also after a restart).",
     "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "undo", "description": "Restore the box of a job to what it was before (queues a new, undoable job).",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
    {"name": "cancel", "description": "Stop a queued or running job (undo it afterwards if it had started placing).",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
    {"name": "export_selection",
     "description": "Save a box of the world (<= 64x64x64) as a file: .schem (Sponge v3, WorldEdit) or .nbt "
                    "(vanilla structure; to_blueprints=true puts it in blueprints/<name>.nbt so "
                    "tools/build_structures.py makes it a canon build).",
     "inputSchema": {"type": "object", "required": ["from", "to", "name"], "properties": {
         "dim": DIM, "from": BOX, "to": BOX, "name": {"type": "string", "pattern": "^[a-z0-9_]+$"},
         "format": {"enum": ["schem", "nbt"]}, "to_blueprints": {"type": "boolean"}}}},
    {"name": "export_program",
     "description": "Compile a build program to a file without touching the world: .schem (Sponge v3) or .nbt.",
     "inputSchema": {"type": "object", "required": ["program"], "properties": {
         "program": PROGRAM, "format": {"enum": ["schem", "nbt"]}}}},
]


class ToolError(Exception):
    pass


def _bridge():
    return client.Bridge()


def _box_query(args):
    a, b = args["from"], args["to"]
    return {"dim": args.get("dim") or "minecraft:overworld", "x1": a[0], "y1": a[1], "z1": a[2], "x2": b[0], "y2": b[1], "z2": b[2]}


def _image(path: Path):
    data = path.read_bytes()
    if len(data) > MAX_IMAGE:
        return None
    return {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": "image/png"}


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _compile(source, registry=None):
    """Compile + registry check + lint. Raises ToolError on program or registry errors."""
    try:
        bp, warnings = program.compile_program(source)
    except (program.ProgramError, json.JSONDecodeError, OSError) as e:
        raise ToolError(f"program error: {e}")
    states = set(bp.blocks.values())
    errors, reg_warnings = check.check_states(states, registry if registry is not None else check.load_registry())
    report = check.lint(bp)
    report["warnings"] = warnings + reg_warnings + report["warnings"]
    if errors:
        raise ToolError("registry errors (fix the ids/states):\n- " + "\n- ".join(errors[:40]))
    return bp, report


# --- tools ---------------------------------------------------------------------------------------------------------

def t_bridge_status(args):
    b = _bridge()
    return {"health": b.get("health"), "zones": b.get("zones"), "url": b.url}


def t_get_registry(args):
    if args.get("refresh"):
        reg = _bridge().get("registry")
        check.REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        check.REGISTRY.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    else:
        reg = check.load_registry()
        if reg is None:
            raise ToolError("no cached registry; call get_registry with refresh=true while the server runs")
    flt = (args.get("filter") or "").lower()
    limit = int(args.get("limit") or 80)
    blocks = {k: v for k, v in reg["blocks"].items() if flt in k}
    out = {
        "data_version": reg.get("data_version"), "minecraft": reg.get("minecraft"),
        "block_count": len(reg["blocks"]), "biome_count": len(reg["biomes"]),
        "namespaces": sorted({k.split(":")[0] for k in reg["blocks"]}),
        "dimensions": reg.get("dimensions"),
        "cached": _rel(check.REGISTRY),
    }
    if flt:
        out["blocks_matching"] = len(blocks)
        out["blocks"] = {k: v.get("props", {}) for k, v in list(sorted(blocks.items()))[:limit]}
        out["biomes"] = [b for b in reg["biomes"] if flt in b]
    else:
        out["mods"] = reg.get("mods")
        out["hint"] = "pass filter (e.g. 'tensura:', 'spruce', 'stairs') to list blocks and biomes"
    return out


def _render_heightmap(hm, path: Path):
    w, l = hm["size"]
    heights = hm["heights"]
    blocks = []
    for count, value in hm["blocks_rle"]:
        blocks.extend([value] * count)
    palette = hm["block_palette"]
    scale = max(1, min(4, 512 // max(w, l)))
    W, H = w * scale, l * scale
    buf = bytearray(W * H * 4)
    for z in range(l):
        for x in range(w):
            i = z * w + x
            hgt = heights[i]
            if hgt is None or blocks[i] < 0:
                rgb = (0, 0, 0)
            else:
                rgb = _color(palette[blocks[i]])
                west = heights[i - 1] if x > 0 and heights[i - 1] is not None else hgt
                north = heights[i - w] if z > 0 and heights[i - w] is not None else hgt
                shade = max(0.55, min(1.35, 1.0 + 0.12 * ((hgt - west) + (hgt - north))))
                rgb = tuple(max(0, min(255, int(c * shade))) for c in rgb)
            for dz in range(scale):
                row = ((z * scale + dz) * W + x * scale) * 4
                buf[row:row + scale * 4] = (bytes(rgb) + b"\xff") * scale
    _write_png(path, W, H, buf)


def t_read_region(args):
    mode = args.get("mode") or "summary"
    q = _box_query(args)
    q["mode"] = mode
    if args.get("load") is False:
        q["load"] = "false"
    if mode == "heightmap" and args.get("surface"):
        q["surface"] = args["surface"]
    data = _bridge().get("region", **q)
    if mode == "heightmap":
        valid = [h for h in data["heights"] if h is not None]
        palette = data["block_palette"]
        counts = {}
        for count, value in data["blocks_rle"]:
            if value >= 0:
                counts[palette[value]] = counts.get(palette[value], 0) + count
        bcounts = {}
        for count, value in data["biomes_rle"]:
            if value >= 0:
                bcounts[data["biome_palette"][value]] = bcounts.get(data["biome_palette"][value], 0) + count
        path = OUT / "region" / f"heightmap_{q['x1']}_{q['z1']}_{q['x2']}_{q['z2']}.png"
        _render_heightmap(data, path)
        summary = {"from": data["from"], "size": data["size"],
                   "height_min": min(valid) if valid else None, "height_max": max(valid) if valid else None,
                   "height_mean": round(sum(valid) / len(valid), 1) if valid else None,
                   "unloaded_columns": len(data["heights"]) - len(valid),
                   "surface_blocks": dict(sorted(counts.items(), key=lambda kv: -kv[1])[:16]),
                   "surface_biomes": dict(sorted(bcounts.items(), key=lambda kv: -kv[1])),
                   "image": _rel(path)}
        w = data["size"][0]
        if w * data["size"][1] <= 64 * 64:  # small areas: the grid itself (rows = z, columns = x)
            summary["heights_rows_z"] = [data["heights"][r * w:(r + 1) * w] for r in range(data["size"][1])]
        return summary, path
    if mode == "blocks":
        bp = client.decode_blocks(data, "region")
        counts = {}
        for s in bp.blocks.values():
            counts[parse_state(s)[0]] = counts.get(parse_state(s)[0], 0) + 1
        path = OUT / "region" / f"blocks_{q['x1']}_{q['y1']}_{q['z1']}.png"
        bp.render(path, OUT / "region" / f"blocks_{q['x1']}_{q['y1']}_{q['z1']}-top.png")
        result = {"origin": data["origin"], "size": data["size"], "palette": data["palette"],
                  "block_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
                  "block_entities": data.get("block_entities", [])[:50], "image": _rel(path)}
        if len(json.dumps(data["rle"])) < 20000:
            result["rle"] = data["rle"]
            result["rle_order"] = "x fastest, then z, then y; values index palette"
        return result, path if path.exists() else None
    return data, None


def t_preview_build(args):
    bp, report = _compile(args["program"])
    view = args.get("view") or "iso"
    iso = OUT / "previews" / f"{bp.name}-iso.png"
    top = OUT / "previews" / f"{bp.name}-top.png"
    bp.render(iso, top)
    report.update({"name": bp.name, "size": list(bp.size), "palette_used": sorted(set(bp.blocks.values()))[:60],
                   "iso": _rel(iso), "top": _rel(top)})
    images = [p for p, want in ((iso, view in ("iso", "both")), (top, view in ("top", "both"))) if want and p.exists()]
    return report, images


def _apply(bp, report, args, label):
    job = client.encode_job(bp, args["origin"], args.get("dim") or "minecraft:overworld", label=label,
                            dry_run=args.get("dry_run", True), updates=args.get("updates") or "quiet",
                            fix_shapes=args.get("fix_shapes", True))
    result = _bridge().post("jobs", job)
    if result.get("dry_run"):
        result["note"] = "dry run: nothing changed. Call again with dry_run=false to place it."
    result["lint"] = report["warnings"]
    return result


def t_apply_build(args):
    bp, report = _compile(args["program"])
    return _apply(bp, report, args, args.get("label") or bp.name)


def t_paste_structure(args):
    prog = {"name": args["structure"].replace("/", "_").replace(".", "_"), "ops": [
        {"op": "stamp", "structure": args["structure"], "at": [0, 0, 0], "rotate": args.get("rotate", 0),
         "mirror": bool(args.get("mirror"))}]}
    try:
        src = program.load_structure(args["structure"])
    except program.ProgramError as e:
        raise ToolError(str(e))
    sx, sy, sz = src.size
    prog["size"] = [sz, sy, sx] if (int(args.get("rotate", 0)) // 90) % 2 else [sx, sy, sz]
    bp, report = _compile(prog)
    return _apply(bp, report, args, args.get("label") or f"paste {args['structure']}")


def t_set_biome(args):
    reg = check.load_registry()
    errors = check.check_biome(args["biome"], reg)
    if errors:
        raise ToolError(errors[0])
    return _bridge().post("biome", {"dim": args.get("dim") or "minecraft:overworld", "from": args["from"],
                                    "to": args["to"], "biome": args["biome"], "dry_run": bool(args.get("dry_run"))})


def t_job_status(args):
    return _bridge().get(f"jobs/{args['id']}")


def t_list_jobs(args):
    return _bridge().get("jobs", limit=int(args.get("limit") or 20))


def t_undo(args):
    return _bridge().post(f"jobs/{args['id']}/undo", {})


def t_cancel(args):
    return _bridge().post(f"jobs/{args['id']}/cancel", {})


def _write(bp, fmt, folder: Path) -> Path:
    import nbt
    if fmt == "nbt":
        path = folder / f"{bp.name}.nbt"
        path.parent.mkdir(parents=True, exist_ok=True)
        nbt.write_gzip(path, bp.to_structure())
        return path
    return schem.write(bp, folder / f"{bp.name}.schem")


def t_export_selection(args):
    q = _box_query(args)
    q["mode"] = "blocks"
    data = _bridge().get("region", **q)
    if data.get("unloaded_cells"):
        raise ToolError(f"{data['unloaded_cells']} cells are in unloaded chunks; read with load=true first")
    bp = client.decode_blocks(data, args["name"])
    fmt = args.get("format") or "schem"
    folder = ROOT / "blueprints" if args.get("to_blueprints") else OUT / "exports"
    if args.get("to_blueprints"):
        fmt = "nbt"
        if (folder / f"{bp.name}.py").exists() or (folder / f"{bp.name}.nbt").exists():
            raise ToolError(f"blueprints/{bp.name} already exists; pick another name")
    path = _write(bp, fmt, folder)
    return {"file": _rel(path), "size": list(bp.size), "cells": len(bp.blocks),
            "next": "python tools/build_structures.py " + bp.name if args.get("to_blueprints") else None}


def t_export_program(args):
    bp, report = _compile(args["program"])
    path = _write(bp, args.get("format") or "schem", OUT / "exports")
    return {"file": _rel(path), "size": list(bp.size), "lint": report["warnings"]}


HANDLERS = {t["name"]: globals()["t_" + t["name"]] for t in TOOLS}


def call_tool(name, args):
    if name not in HANDLERS:
        raise ToolError(f"unknown tool {name}")
    result = HANDLERS[name](args or {})
    images = []
    if isinstance(result, tuple):
        result, extra = result
        extra = extra if isinstance(extra, list) else [extra] if extra else []
        images = [img for img in (_image(p) for p in extra) if img]
    content = [{"type": "text", "text": json.dumps(result, indent=1, default=str)}]
    return content + images


# --- JSON-RPC over stdio ---------------------------------------------------------------------------------------------

def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:
        return None  # notifications (initialized, cancelled): nothing to answer
    try:
        if method == "initialize":
            asked = (msg.get("params") or {}).get("protocolVersion")
            result = {"protocolVersion": asked if asked in PROTOCOLS else PROTOCOLS[0],
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "ttl-forge", "version": "0.1.0"},
                      "instructions": "Build loop: read_region -> preview_build (look at the image, fix) -> "
                                      "apply_build dry_run -> apply_build -> job_status -> undo if wrong. "
                                      "Never invent modded ids: get_registry filter first."}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params") or {}
            try:
                result = {"content": call_tool(params.get("name"), params.get("arguments")), "isError": False}
            except (ToolError, client.BridgeError, program.ProgramError, ValueError, KeyError) as e:
                text = str(e) if not isinstance(e, KeyError) else f"missing argument {e}"
                result = {"content": [{"type": "text", "text": text}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as e:  # a bug here must not kill the session
        traceback.print_exc(file=sys.stderr)
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": repr(e)}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = [r for r in map(handle, msg) if r] if isinstance(msg, list) else handle(msg)
        if reply:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
