"""Checks on a compiled build: block ids and states against the server's registry, and structural lints.

The registry is the bridge's /v1/registry dump, cached in design/dumps/registry.json (`get_registry refresh=true`
writes it). Without the dump only syntax is checked and a warning says so (CLAUDE.md rule 4: never invent ids).
"""
import json
from collections import Counter, deque
from pathlib import Path

from program import ROOT
from blueprint import AIR, parse_state

REGISTRY = ROOT / "design" / "dumps" / "registry.json"

NON_SOLID = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:structure_void", "minecraft:water",
             "minecraft:lava", "minecraft:light"}
GRAVITY = ("_sand", "sand", "gravel", "_concrete_powder", "anvil", "pointed_dripstone", "scaffolding")
# Blocks that hang or stand on something and pop off without it.
NEEDS_SUPPORT = ("_door", "torch", "lantern", "_carpet", "_pressure_plate", "rail", "_sapling", "flower", "_button",
                 "redstone_wire", "_bed", "candle", "_banner", "_sign")


def load_registry(path: Path = REGISTRY):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check_states(states, registry) -> tuple[list[str], list[str]]:
    """Errors (unknown block, unknown property or value) and warnings, for a set of block-state strings."""
    errors, warnings = [], []
    if registry is None:
        warnings.append(f"no registry dump at {REGISTRY.relative_to(ROOT)}: ids not verified "
                        "(run get_registry with refresh=true against a running server)")
        return errors, warnings
    blocks = registry.get("blocks", {})
    for state in sorted(states):
        name, props = parse_state(state)
        entry = blocks.get(name)
        if entry is None:
            near = [b for b in blocks if b.split(":", 1)[1] == name.split(":", 1)[1]]
            errors.append(f"unknown block {name}" + (f" (did you mean {', '.join(near[:3])}?)" if near else ""))
            continue
        known = entry.get("props", {})
        for k, v in props.items():
            if k not in known:
                errors.append(f"{state}: {name} has no property '{k}' (has: {', '.join(known) or 'none'})")
            elif v not in known[k]:
                errors.append(f"{state}: {k}={v} not allowed (one of {', '.join(known[k])})")
    return errors, warnings


def check_biome(biome: str, registry) -> list[str]:
    if registry is None:
        return []
    return [] if biome in registry.get("biomes", []) else [f"unknown biome {biome}"]


def _solid(state: str) -> bool:
    return parse_state(state)[0] not in NON_SOLID


def lint(bp) -> dict:
    """Structural warnings: floating parts, gravity blocks over air, things that need support, counts."""
    blocks = bp.blocks
    solid = {p for p, s in blocks.items() if _solid(s)}
    warnings = []
    # Floating: solid cells not connected (6 neighbours) to the bottom layer y=0, which stands on the ground.
    grounded = set()
    queue = deque(p for p in solid if p[1] == 0)
    grounded.update(queue)
    while queue:
        x, y, z = queue.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + d[0], y + d[1], z + d[2])
            if n in solid and n not in grounded:
                grounded.add(n)
                queue.append(n)
    floating = sorted(solid - grounded, key=lambda p: (p[1], p[0], p[2]))
    if floating:
        warnings.append(f"{len(floating)} solid blocks are not connected to the ground layer (y=0), e.g. "
                        + ", ".join(str(list(p)) for p in floating[:5]) + ": they float when the build is placed")
    gravity = [p for p in solid if any(parse_state(blocks[p])[0].endswith(g) for g in GRAVITY)
               and p[1] > 0 and (p[0], p[1] - 1, p[2]) not in solid]
    if gravity:
        warnings.append(f"{len(gravity)} gravity blocks (sand, gravel, powder) have air under them, e.g. {list(gravity[0])}: they fall")
    hanging = []
    for p, s in blocks.items():
        name = parse_state(s)[0]
        if any(name.endswith(k) for k in NEEDS_SUPPORT) and "wall_" not in name and "hanging" not in name and p[1] > 0:
            below = blocks.get((p[0], p[1] - 1, p[2]))
            if below is None or not _solid(below):
                if name.endswith("_door") and parse_state(s)[1].get("half") == "upper":
                    continue
                hanging.append(p)
    if hanging:
        warnings.append(f"{len(hanging)} blocks that need a block under them have none (doors, torches, carpets...), "
                        f"e.g. {list(hanging[0])}")
    doors = [p for p, s in blocks.items() if parse_state(s)[0].endswith("_door")]
    halves = Counter(parse_state(blocks[p])[1].get("half") for p in doors)
    if halves.get("lower", 0) != halves.get("upper", 0):
        warnings.append(f"doors: {halves.get('lower', 0)} lower halves, {halves.get('upper', 0)} upper halves (use the door op)")
    counts = Counter(parse_state(s)[0] for s in blocks.values())
    return {
        "cells_set": len(blocks),
        "solid": len(solid),
        "air": counts.get(AIR, 0),
        "top_blocks": dict(counts.most_common(12)),
        "warnings": warnings,
    }
