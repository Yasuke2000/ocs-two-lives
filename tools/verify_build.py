#!/usr/bin/env python3
"""Check that a placed build matches its structure files, block by block ("does it transfer well?").

Usage:
  verify_build.py <name> <dimension> <x> <y> <z>   corner = the structure's 0,0,0 in the world
  verify_build.py <name> --log [--dimension <dim>]  corner from the placement script's log line
                                                    (`[ttl] tempest placed: corner X Y Z`, dwargon likewise;
                                                    `mortal spawn placed at y Y` for mortal_spawn)
  verify_build.py <name> --capture <file.nbt> [<x> <y> <z>]   compare a capture already on disk (offline)
Options: --min <percent> pass mark (default 98), --top <n> mismatch pairs to list (default 12),
         --keep <file.nbt> keep the downloaded capture.

<name> is a structure in pack/kubejs/data/ttl/structure/: <name>.nbt, or the slabs <name>_0.nbt, <name>_1.nbt, ...
(PARTS builds such as tempest and dwargon), stacked along z in order. Live mode forceloads the box, runs
`/ttlcapture` on the server (tools/cluster.py), downloads ttl-captures/verify_<name>.nbt, removes it and the
forceloads it added, and compares. Read-only for the world.

Only positions the structure defines count (explicit air included; positions it leaves out are the world's).
Differences the game makes itself count as matches (listed as "adjusted"): fence/wall/pane/bars/redstone
connections, stair shapes, power and lit-by-power, leaf distance/persistence, waterlogging, snowy grass, crop
and sapling growth, fluid levels, note-block instrument, fence gates in walls, dripstone thickness, plus a few
block swaps the world does on its own (grass <-> dirt, farmland -> dirt, air variants). Exit code 1 below --min.
"""
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import nbt  # noqa: E402

STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
OVERWORLD = "minecraft:overworld"

# Properties the game recomputes from neighbours, power, randomness or growth once a block is in the world.
IGNORED_EVERYWHERE = {"waterlogged", "snowy", "powered", "power", "in_wall", "triggered", "instrument",
                      "thickness", "tilt", "attached", "disarmed"}
CONNECTIONS = {"north", "south", "east", "west", "up", "down"}
CONNECTING = ("_fence", "_wall", "_pane", "iron_bars", "redstone_wire", "tripwire", "_mushroom_block",
              "mushroom_stem", "chorus_plant", "fire", "glass_pane")
IGNORED_BY_SUFFIX = {
    "_stairs": {"shape"},
    "_leaves": {"distance", "persistent"},
    "scaffolding": {"distance", "bottom"},
    "redstone_lamp": {"lit"},
    "redstone_torch": {"lit"},
    "redstone_wall_torch": {"lit"},
    "redstone_ore": {"lit"},
    "water": {"level"},
    "lava": {"level"},
    "farmland": {"moisture"},
    "_sapling": {"stage"},
}
GROWS = ("wheat", "carrots", "potatoes", "beetroots", "_stem", "sweet_berry_bush", "cocoa", "nether_wart",
         "kelp", "cave_vines", "bamboo", "sugar_cane", "cactus", "twisting_vines", "weeping_vines", "torchflower_crop",
         "pitcher_crop", "chorus_flower")
# Blocks the world swaps by itself: grass dies under cover and spreads onto dirt, farmland dries out.
SOFT = [{"minecraft:grass_block", "minecraft:dirt"}, {"minecraft:farmland", "minecraft:dirt"},
        {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}]
_STATE = re.compile(r"^([^\[]+)(?:\[(.*)\])?$")


# --- loading -----------------------------------------------------------------------------------------------
def state_string(entry: dict) -> str:
    props = entry.get("Properties") or {}
    return entry["Name"] + ("[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]" if props else "")


def read_structure(root: dict) -> tuple[tuple[int, int, int], dict]:
    """A vanilla structure (ours, or what /ttlcapture saves) as (size, {(x, y, z): state})."""
    palette = root.get("palette") or (root.get("palettes") or [[]])[0]
    states = [state_string(e) for e in palette]
    blocks = {tuple(b["pos"]): states[b["state"]] for b in root.get("blocks", [])}
    return tuple(root["size"]), blocks


def structure_files(name: str) -> list[Path]:
    single = STRUCTURES / f"{name}.nbt"
    if single.exists():
        return [single]
    parts = []
    while (STRUCTURES / f"{name}_{len(parts)}.nbt").exists():
        parts.append(STRUCTURES / f"{name}_{len(parts)}.nbt")
    if not parts:
        sys.exit(f"no structure {name}.nbt or {name}_0.nbt in {STRUCTURES.relative_to(ROOT)}")
    return parts


def load_expected(files: list[Path]) -> tuple[tuple[int, int, int], dict, list[tuple[str, int, int]]]:
    """Every slab stacked along z: (size, blocks, [(slab, z0, z1)])."""
    blocks, slabs = {}, []
    sx = sy = z0 = 0
    for path in files:
        (px, py, pz), part = read_structure(nbt.read_gzip(path))
        blocks.update({(x, y, z + z0): s for (x, y, z), s in part.items()})
        slabs.append((path.stem, z0, z0 + pz))
        sx, sy, z0 = max(sx, px), max(sy, py), z0 + pz
    return (sx, sy, z0), blocks, slabs


# --- comparing ---------------------------------------------------------------------------------------------
def split(state: str) -> tuple[str, dict]:
    m = _STATE.match(state)
    props = dict(p.split("=", 1) for p in m.group(2).split(",")) if m.group(2) else {}
    return m.group(1), props


def normalize(state: str) -> str:
    """The state without the properties the game is free to change."""
    name, props = split(state)
    drop = set(IGNORED_EVERYWHERE)
    if any(k in name for k in CONNECTING):
        drop |= CONNECTIONS
    for suffix, keys in IGNORED_BY_SUFFIX.items():
        if name.endswith(suffix):
            drop |= keys
    if any(k in name for k in GROWS):
        drop |= {"age", "berries", "leaves", "stage"}
    kept = {k: v for k, v in props.items() if k not in drop}
    return name + ("[" + ",".join(f"{k}={v}" for k, v in sorted(kept.items())) + "]" if kept else "")


def soft_equal(a: str, b: str) -> bool:
    na, nb = split(a)[0], split(b)[0]
    return any(na in group and nb in group for group in SOFT)


def compare(expected: dict, actual: dict) -> dict:
    """Block-by-block over the positions `expected` defines. Missing positions in `actual` count as mismatches."""
    exact = adjusted = soft = 0
    pairs, samples, by_z = Counter(), {}, Counter()
    for pos, want in expected.items():
        got = actual.get(pos, "(not captured)")
        if got == want:
            exact += 1
        elif got != "(not captured)" and normalize(got) == normalize(want):
            adjusted += 1
        elif got != "(not captured)" and soft_equal(got, want):
            soft += 1
        else:
            key = (normalize(want), normalize(got) if got != "(not captured)" else got)
            pairs[key] += 1
            samples.setdefault(key, [])
            if len(samples[key]) < 4:
                samples[key].append(pos)
            by_z[pos[2]] += 1
    total = len(expected)
    matched = exact + adjusted + soft
    return {"defined": total, "exact": exact, "adjusted": adjusted, "soft": soft, "mismatched": total - matched,
            "percent": 100.0 * matched / total if total else 100.0, "pairs": pairs, "samples": samples, "by_z": by_z}


def short(state: str) -> str:
    return state.replace("minecraft:", "")


def report(name: str, result: dict, corner, slabs, top: int) -> str:
    cx, cy, cz = corner or (0, 0, 0)
    where = "world" if corner else "structure"
    lines = [f"{name}: {result['percent']:.2f}% match over {result['defined']} defined positions "
             f"({result['exact']} exact, {result['adjusted']} adjusted by the game, {result['soft']} soft swaps, "
             f"{result['mismatched']} mismatched)"]
    if len(slabs) > 1:
        per = ", ".join(f"{s}: {sum(n for z, n in result['by_z'].items() if z0 <= z < z1)}" for s, z0, z1 in slabs)
        lines.append(f"mismatches per slab: {per}")
    if result["pairs"]:
        lines.append(f"top mismatches (expected -> found, count, {where} coordinates):")
        for (want, got), n in result["pairs"].most_common(top):
            at = " ".join(f"({x + cx} {y + cy} {z + cz})" for x, y, z in result["samples"][(want, got)])
            lines.append(f"  {short(want)} -> {short(got)}  x{n}  {at}")
    return "\n".join(lines)


# --- live server ---------------------------------------------------------------------------------------------
def rcon(command: str) -> str:
    import cluster
    out = cluster.mc(f"rcon-cli '{command}'")
    return re.sub(r"\x1b\[[0-9;]*m", "", out.stdout.decode(errors="replace")).strip()


def corner_from_log(name: str) -> tuple[int, int, int, str]:
    """The last placement line for `name` in the server logs (rotated .log.gz files included)."""
    import cluster
    if name == "mortal_spawn":
        pattern, dim = r"mortal spawn placed at y (-?\d+)", "ttl:mortal_realm"
    else:
        pattern, dim = rf"\[ttl\] {re.escape(name)} placed: corner (-?\d+) (-?\d+) (-?\d+)", OVERWORLD
    out = cluster.mc("sh -c 'zcat -f /data/logs/*.log.gz /data/logs/latest.log 2>/dev/null | grep -a \"placed\"'")
    found = re.findall(pattern, out.stdout.decode(errors="replace"))
    if not found:
        sys.exit(f"no placement line for {name} in the server logs; give the corner: {name} <dimension> <x> <y> <z>")
    if name == "mortal_spawn":  # mortal_spawn.js: place template ttl:mortal_spawn -14 (y - 7) -14
        return -14, int(found[-1]) - 7, -14, dim
    x, y, z = found[-1]
    return int(x), int(y), int(z), dim


def chunk_strips(x0: int, z0: int, x1: int, z1: int):
    """forceload takes at most 256 chunks per command: whole chunk rows, as many as fit."""
    width = (x1 >> 4) - (x0 >> 4) + 1
    rows = max(1, 256 // width)
    cz = z0 >> 4
    while cz <= z1 >> 4:
        last = min(cz + rows - 1, z1 >> 4)
        yield x0, max(z0, cz * 16), x1, min(z1, last * 16 + 15)
        cz = last + 1


def capture_live(name: str, dim: str, corner, size, keep: Path | None) -> Path:
    x0, y0, z0 = corner
    x1, y1, z1 = x0 + size[0] - 1, y0 + size[1] - 1, z0 + size[2] - 1
    if max(size) > 256:
        sys.exit(f"{name} is larger than /ttlcapture's 256-block limit: {size}")
    tag = f"verify_{name}"
    before = {tuple(map(int, m)) for m in re.findall(r"\[(-?\d+), (-?\d+)\]", rcon(f"execute in {dim} run forceload query"))}
    area = {(cx, cz) for cx in range(x0 >> 4, (x1 >> 4) + 1) for cz in range(z0 >> 4, (z1 >> 4) + 1)}
    for a in chunk_strips(x0, z0, x1, z1):
        rcon(f"execute in {dim} run forceload add {a[0]} {a[1]} {a[2]} {a[3]}")
    try:
        message = ""
        for _ in range(24):  # the chunks need a moment to load (or generate)
            message = rcon(f"execute in {dim} run ttlcapture {tag} {x0} {y0} {z0} {x1} {y1} {z1}")
            if "Captured" in message:
                break
            time.sleep(5)
        print(message)
        if "Captured" not in message:
            sys.exit("capture failed")
    finally:
        added = area - before
        if not area & before:
            for a in chunk_strips(x0, z0, x1, z1):
                rcon(f"execute in {dim} run forceload remove {a[0]} {a[1]} {a[2]} {a[3]}")
        else:  # someone else forceloads part of it (a placement in progress): leave theirs alone
            for cx, cz in sorted(added):
                rcon(f"execute in {dim} run forceload remove {cx * 16} {cz * 16}")
    import cluster
    data = cluster.mc(f"cat /data/ttl-captures/{tag}.nbt").stdout
    cluster.mc(f"rm -f /data/ttl-captures/{tag}.nbt")
    path = keep or Path(tempfile.mkdtemp(prefix="ttl-verify-")) / f"{tag}.nbt"
    path.write_bytes(data)
    print(f"downloaded {len(data)} bytes -> {path}")
    return path


# --- main ----------------------------------------------------------------------------------------------------
def option(args: list[str], flag: str, default=None):
    if flag in args:
        i = args.index(flag)
        value = args[i + 1]
        del args[i:i + 2]
        return value
    return default


def main(argv: list[str]) -> int:
    args = list(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    minimum = float(option(args, "--min", "98"))
    top = int(option(args, "--top", "12"))
    keep = option(args, "--keep")
    capture = option(args, "--capture")
    dim_override = option(args, "--dimension")
    from_log = "--log" in args
    if from_log:
        args.remove("--log")
    name, rest = args[0], args[1:]
    size, expected, slabs = load_expected(structure_files(name))
    corner = None
    if capture:
        if rest:
            corner = tuple(int(v) for v in rest[-3:])
        path = Path(capture)
    else:
        if from_log:
            *corner, dim = corner_from_log(name)
            corner = tuple(corner)
        elif len(rest) == 4:
            dim, corner = rest[0], tuple(int(v) for v in rest[1:])
        else:
            print(__doc__)
            return 2
        dim = dim_override or dim
        print(f"{name}: {len(slabs)} structure file(s), box {size[0]}x{size[1]}x{size[2]} at {' '.join(map(str, corner))} in {dim}")
        path = capture_live(name, dim, corner, size, Path(keep) if keep else None)
    csize, actual = read_structure(nbt.read_gzip(path))
    if tuple(csize) != tuple(size):
        print(f"note: capture is {csize}, structure box is {size}")
    result = compare(expected, actual)
    print(report(name, result, corner, slabs, top))
    passed = result["percent"] >= minimum
    print(f"{'PASS' if passed else 'FAIL'} (pass mark {minimum}%)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
