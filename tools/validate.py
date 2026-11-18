"""Repo validation: run before every push and in CI. Exit 1 on any failure."""
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"
FORBIDDEN = re.compile(r"epic.?fight|better.?combat|predation|mekanism", re.I)

# R12 (design/architecture/paths-necro-artificer.md §0): a system is not a chapter. No stage of the story, the Oath path or
# the boss ladder may appear in the data of a standalone system: not as a value, not as a key. Comments may name them.
R12_FILES = ("necro.toml", "artifice.toml", "choices.toml", "roads.toml")
R12_STAGE = re.compile(r"(?<![a-z0-9_.])ttl\.(story|path|boss)(\.|$)")

errors: list[str] = []


def r12_violations(paths) -> list[str]:
    """Every story/path/boss stage id found in the parsed TOML of these system data files, as 'file: where = id'."""
    found: list[str] = []

    def walk(name: str, where: str, v) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                if R12_STAGE.search(str(k)):
                    found.append(f"{name}: key {where}{k}")
                walk(name, f"{where}{k}.", x)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                walk(name, f"{where}{i}.", x)
        elif isinstance(v, str) and R12_STAGE.search(v):
            found.append(f"{name}: {where.rstrip('.')} = {v!r}")

    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        with p.open("rb") as f:
            walk(p.name, "", tomllib.load(f))
    return found


def check_r12() -> None:
    for v in r12_violations(ROOT / "design" / "data" / n for n in R12_FILES):
        errors.append(f"R12 a system is not a chapter: {v} (gate on EP, items, rank points, faction bands or nation rank instead)")


def check_json() -> None:
    for p in PACK.rglob("*.json"):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"JSON {p.relative_to(ROOT)}: {e}")


def check_js() -> None:
    node = shutil.which("node")
    if not node:
        print("warn: node not found, skipping JS syntax check")
        return
    for p in (PACK / "kubejs").rglob("*.js"):
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"JS {p.relative_to(ROOT)}: {r.stderr.strip().splitlines()[-1]}")


def check_mods() -> None:
    for p in (PACK / "mods").glob("*.pw.toml"):
        text = p.read_text(encoding="utf-8")
        name = re.search(r'^name = "(.*)"', text, re.M)
        if FORBIDDEN.search(p.stem) or (name and FORBIDDEN.search(name.group(1))):
            errors.append(f"forbidden mod: {p.name}")


def check_index_fresh() -> None:
    packwiz = shutil.which("packwiz")
    if not packwiz:
        print("warn: packwiz not found, skipping index freshness check")
        return
    before = (PACK / "index.toml").read_bytes()
    subprocess.run([packwiz, "refresh"], cwd=PACK, capture_output=True, check=True)
    if (PACK / "index.toml").read_bytes() != before:
        errors.append("pack/index.toml was stale — refreshed it, commit the change")


def check_config_text() -> None:
    # Some mods keep a database in config/ (CervLogger's SQLite); shipping one overwrites and corrupts
    # the live file on every server start.
    for p in (PACK / "config").rglob("*"):
        if p.is_file() and bytes([0]) in p.read_bytes()[:4096]:
            errors.append(f"binary file in pack/config (a mod database?): {p.relative_to(ROOT)}")


def check_generated() -> None:
    for tool in ("gen_data.py", "gen_npcs.py", "gen_quests.py", "quest_graph.py", "config_index.py", "build_structures.py"):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / tool), "--check"], capture_output=True, text=True)
        if r.returncode != 0:
            errors.append(r.stdout.strip() or r.stderr.strip())


def main() -> int:
    for check in (check_json, check_js, check_mods, check_config_text, check_r12, check_generated, check_index_fresh):
        check()
    for e in errors:
        print(f"FAIL {e}")
    print("validation passed" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
