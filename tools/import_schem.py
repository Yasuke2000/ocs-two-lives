#!/usr/bin/env python3
"""Bring a build polished in game with WorldEdit back into the repo.

In game (op): select exactly the build's box (//wand, pos1/pos2), `//copy`, `//schem save <name>`.
Then: import_schem.py <name> [--as <blueprint>]
It copies the schematic from the staging server into blueprints/<blueprint>.schem (which then wins over
blueprints/<blueprint>.py) and rebuilds the structure + previews. Commit the .schem, the .nbt and the
previews; anything placing that structure (e.g. the Corridor hall) uses the new version.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE = os.environ.get("TTL_NODE", "root@100.109.28.21")
SCHEMATICS = "/data/config/worldedit/schematics"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="the name used in //schem save")
    ap.add_argument("--as", dest="target", help="blueprint name in the repo (default: same)")
    args = ap.parse_args()
    target = args.target or args.name
    cmd = ["ssh", "-n", "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR", NODE,
           f"k3s kubectl -n ocs-two-lives exec deploy/mc -- cat {SCHEMATICS}/{args.name}.schem"]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        sys.exit(f"could not read {SCHEMATICS}/{args.name}.schem on the server: {result.stderr.decode(errors='replace').strip()}")
    dest = ROOT / "blueprints" / f"{target}.schem"
    dest.write_bytes(result.stdout)
    print(f"saved {dest.relative_to(ROOT)} ({len(result.stdout)} bytes)")
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "build_structures.py"), target], check=True)
    print(f"review docs/previews/{target}-iso.png, then commit blueprints/, the .nbt and the previews")


if __name__ == "__main__":
    main()
