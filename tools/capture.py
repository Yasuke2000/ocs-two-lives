#!/usr/bin/env python3
"""Capture a region of the staging world into blueprints/ (no player, no size-48 limit).

Usage: capture.py <name> <dimension> <x1> <y1> <z1> <x2> <y2> <z2>
Runs /ttlcapture on the server, copies ttl-captures/<name>.nbt to blueprints/<name>.nbt (which then wins
over a .schem or .py of the same name) and rebuilds the structure + previews. Place it again with
`tools/server.sh place <name> <dimension> <x> <y> <z>` or `/ttl build <name>`.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cluster  # noqa: E402




def main() -> None:
    if len(sys.argv) != 9:
        sys.exit(__doc__)
    name, dim, *coords = sys.argv[1:]
    out = cluster.mc(f"rcon-cli 'execute in {dim} run ttlcapture {name} {' '.join(coords)}'")
    message = out.stdout.decode(errors="replace").strip()
    print(message)
    if "Captured" not in message:
        sys.exit("capture failed")
    data = cluster.mc(f"cat /data/ttl-captures/{name}.nbt").stdout
    dest = ROOT / "blueprints" / f"{name}.nbt"
    dest.write_bytes(data)
    print(f"saved {dest.relative_to(ROOT)} ({len(data)} bytes)")
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "build_structures.py"), name], check=True)


if __name__ == "__main__":
    main()
