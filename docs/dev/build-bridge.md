# Build bridge: Claude builds in the live world (ttl-portals `bridge/` + `tools/forge`)

Claude can read terrain, preview a build and place it on a running server, with an undo for every job. Three parts:

| Part | Where | What |
| --- | --- | --- |
| Bridge | `mod/src/main/java/com/yasuke/ttl/bridge/` (ttl-portals) | HTTP API on `127.0.0.1:25599`, bearer token, block/biome registry dump, region reads, a write queue that runs in a time budget per tick, undo snapshots, build zones, `/ttlbridge` |
| Sidecar | `tools/forge/mcp_server.py` (stdlib Python) | MCP server (stdio) Claude talks to; registered in the repo's `.mcp.json` as `ttl-forge` |
| Core | `tools/forge/program.py`, `check.py`, `schem.py` + `tools/blueprint.py` | The JSON build language, registry checks, structural lints, previews, `.schem` v3 / `.nbt` export |

The canon builds (`blueprints/*.py` → `tools/build_structures.py`) keep their own flow. The bridge adds a live
"see, act, check" loop, and it can paste any of them (`paste_structure tempest_town_0`) or turn a region of the world
back into a blueprint (`export_selection ... to_blueprints=true`).

## Turning it on

The bridge is **off** by default. On first start the mod writes `config/ttl/bridge.json` (disabled) and
`config/ttl/bridge.token` (32 random bytes, file mode 600). To turn it on, edit `bridge.json` and run `/ttlbridge reload`
(or restart):

```json
{
  "enabled": true,
  "bind": "127.0.0.1",
  "port": 25599,
  "budget_ms": 3.0,
  "pause_mspt": 45.0,
  "max_job_cells": 4194304,
  "allow_anywhere": false,
  "zones":   [{"name": "jura-east-build", "dim": "minecraft:overworld", "from": [1200, -64, -400], "to": [1700, 320, 100]}],
  "protect": [{"name": "tempest", "dim": "minecraft:overworld", "from": [-200, -64, -200], "to": [200, 320, 200]}]
}
```

- **Writes** (jobs, biomes, undo) only go into a box that lies fully inside a `zones` entry and touches no `protect`
  entry. With no zones nothing is writable. `allow_anywhere: true` is for a local test server only (protect boxes still apply).
- **Reads** are allowed anywhere, capped in size (`max_read_cells` 64³ in blocks mode, `max_summary_cells` 1M,
  `max_heightmap_columns` 512²). They run on the server thread, so keep them small while players are online.
- There is **no command endpoint**: Claude cannot run `/op`, `/stop` or anything else through the bridge.
- The token can also come from the environment variable `TTL_BRIDGE_TOKEN` (k8s secret on staging). Never commit it.

## Connecting Claude

The sidecar finds the bridge with `TTL_BRIDGE_URL` (default `http://127.0.0.1:25599`). It finds the token in
`TTL_BRIDGE_TOKEN`, else the file `TTL_BRIDGE_TOKEN_FILE`, else `$TTL_LOCAL_DIR/server/config/ttl/bridge.token`.

- **Local Lerfing server** (`tools/local.sh`): with `TTL_LOCAL_DIR` set as in AGENTS.md, Claude Code picks up `.mcp.json`
  in this repo. Approve the `ttl-forge` server once, then check with `bridge_status`.
- **Staging**: forward the port through the `ttl-operator` kubeconfig, then point the sidecar at it:
  `kubectl --kubeconfig ~/.kube/ocs-two-lives.yaml -n ocs-two-lives port-forward deploy/mc 25599:25599`.
  Only with nobody online, or inside a zone far from players. Do not expose the port through a Service or Ingress.
- **Claude Desktop**: add the same command (`python -I <repo>/tools/forge/mcp_server.py`) as a stdio server with the
  env vars above.

## The build loop

1. `get_registry refresh=true` once per pack change. It writes `design/dumps/registry.json` (every block with its
   properties, biomes, dimensions and mod versions). From then on `get_registry filter="tensura:"` lists real ids.
   Every program is checked against this dump, so an invented id fails before it reaches the world.
2. `read_region mode=heightmap` (with a rendered map image) or `mode=summary` to see the site. Use `mode=blocks` for a
   small box, for example to match an existing wall.
3. `preview_build`: compile, registry check, lint (floating parts, sand over air, torches/doors without support,
   half doors) and an isometric PNG returned to Claude as an image. Fix and repeat.
4. `apply_build` with the default `dry_run=true`: cells set and changed, block entities it would replace, the zone check.
5. `apply_build dry_run=false` → job id. The bridge snapshots the cells it will change (block entities included) to
   `<world>/ttl-bridge/history/<id>.snapshot.nbt`. It places the blocks within `budget_ms` per tick (skipping ticks
   while the average tick is over `pause_mspt`), then lets fences, panes, walls and stairs connect.
6. `job_status`, then `read_region` to look at the result. `undo <id>` restores the box. An undo is itself a job, so it
   can be undone. Undo works after a restart. Undo jobs newest first when several jobs overlap.

Op side: `/ttlbridge status | jobs | undo <id> | cancel <id> | reload` (permission 3).

## The build language

A program is JSON: `{"name", "size": [x, y, z], "palette": {"alias": "state"}, "clear": false, "ops": [...]}`.
Coordinates are relative to the corner, y up. Cells no op sets are **kept** as they are in the world; `"clear": true`
makes them air. Blocks use command syntax (`minecraft:oak_stairs[facing=east]`), `$alias` from the palette, and an
optional block-entity SNBT tail (`minecraft:chest[facing=east]{Items:[{Slot:0b,id:"minecraft:bread",count:5}]}`; the
bridge places it like `/setblock`; `.nbt`/`.schem` exports leave it out).

| Op | Arguments |
| --- | --- |
| `set` | `at`, `block` |
| `fill` / `clear` | `from`, `to`, `block` (clear: air) |
| `hollow_box` | `from`, `to`, `block`, `open: ["top", "bottom"]` |
| `walls` | `from`, `to`, `block`: the four sides only |
| `replace` | `from`, `to`, `match` (id or exact state), `block`: on cells this program set |
| `cylinder` | `center [x, z]`, `y [y1, y2]`, `radius`, `block`, `hollow` |
| `sphere` | `center`, `radius`, `block`, `hollow`, `half: upper\|lower` |
| `line` | `from`, `to`, `block` |
| `path` | `points [[x, z], ...]`, `y`, `width`, `block` |
| `roof` | `from [x1, y, z1]`, `to [x2, _, z2]`, `style: gable\|hip\|shed\|flat`, `stairs`, `axis: x\|z`, `fill` (gable ends / hip core), `ridge` |
| `window_grid` | `from`, `to` (a flat wall), `block`, `spacing 3`, `width 1`, `height 2`, `bottom 1`, `margin 1` |
| `door` | `at`, `facing`, `block`, `hinge`: both halves |
| `scatter` | `from`, `to`, `block`, `density`, `seed`, `on` (only on top of this block) |
| `stamp` | `structure` (pack structure, blueprint name or `.nbt`/`.schem` path), `at`, `rotate 0/90/180/270`, `mirror` |

Example: `tools/forge/examples/spruce_hut.json`.

## Limits and choices

- Placement is "quiet" by default: client updates, no neighbour updates, no drops. Water does not flow, sand does not
  fall and redstone does not react until something else updates the block. `updates: "neighbors"` behaves like `/setblock`.
  Shapes (fences, panes, stairs) are fixed in a pass after placing (`fix_shapes`, default on).
- `set_biome` uses vanilla `fillbiome` chunk by chunk and has **no undo**: read the old biome first.
- Chunks a request needs (region reads with `load`, jobs, biome fills) are loaded first through an expiring chunk
  ticket, so new chunks generate in the background while the server keeps ticking; the HTTP call waits (at most
  10 minutes, `max_preload_chunks` 4096 per request). Before this, a big read generated chunks on the server thread and
  the watchdog stopped the server (found on the local pack server, 23/11/2026).
- `read_region mode=heightmap surface=terrain` reads the ground under trees (MOTION_BLOCKING_NO_LEAVES, water
  surface included); the default `world` includes leaves.
- Measured on a dev server (flat world, no players, 22/11/2026): a job of 1,444,000 cells (472,514 changed) placed in
  17 s with the 3 ms budget, average tick at most 5.1 ms; its undo took 10 s.
- `tools/world/compare_design.py` uses the bridge to compare a generated world with the own-world design rasters, site
  by site (plates, ground, water, biomes, a side-by-side picture); see `world/README.md`.
- Not built (decisions.md 22/11/2026): a WorldPainter pipeline (the own world is generated by the mod from
  `world/map.svg`) and a browser voxel editor.
