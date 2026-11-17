#!/usr/bin/env python3
"""Turn every blueprints/<name>.py (code), .schem (WorldEdit) or .nbt (captured) into a structure + previews.

Writes pack/kubejs/data/ttl/structure/<name>.nbt (place in game: `/ttl build <name>`) and
docs/previews/<name>-iso.png + <name>-top.png for review.
Usage: build_structures.py [name ...]   (no names: all blueprints)
       build_structures.py --check      exit 1 if a structure file is out of date (validate.py)
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from blueprint import Blueprint, from_schem, from_structure  # noqa: E402
import nbt  # noqa: E402

BLUEPRINTS = ROOT / "blueprints"
sys.path.insert(0, str(BLUEPRINTS))  # shared helpers: blueprints/_*.py
STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
PREVIEWS = ROOT / "docs" / "previews"


def load(path: Path) -> Blueprint:
    if path.suffix == ".schem":
        return from_schem(path.stem, path)
    if path.suffix == ".nbt":
        return from_structure(path.stem, path)
    spec = importlib.util.spec_from_file_location(f"blueprint_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bp = Blueprint(path.stem, module.SIZE)
    module.build(bp)
    return bp


def main() -> None:
    check = "--check" in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    # Captured from the world (.nbt, tools/capture.py) wins over polished in WorldEdit (.schem,
    # tools/import_schem.py), which wins over code (.py) of the same name.
    by_name = {p.stem: p for p in sorted(BLUEPRINTS.glob("*.py")) if not p.stem.startswith("_")}
    by_name.update({p.stem: p for p in sorted(BLUEPRINTS.glob("*.schem"))})
    by_name.update({p.stem: p for p in sorted(BLUEPRINTS.glob("*.nbt"))})
    files = [by_name[n] for n in sorted(by_name)]
    if names:
        files = [f for f in files if f.stem in names]
    stale = []
    for path in files:
        bp = load(path)
        target = STRUCTURES / f"{bp.name}.nbt"
        if check:
            with tempfile.TemporaryDirectory() as tmp:
                fresh = Path(tmp) / "x.nbt"
                nbt.write_gzip(fresh, bp.to_structure())
                if not target.exists() or target.read_bytes() != fresh.read_bytes():
                    stale.append(bp.name)
            continue
        STRUCTURES.mkdir(parents=True, exist_ok=True)
        nbt.write_gzip(target, bp.to_structure())
        bp.render(PREVIEWS / f"{bp.name}-iso.png", PREVIEWS / f"{bp.name}-top.png")
        print(f"{bp.name}: {len(bp.blocks)} blocks, size {bp.size} -> {target.relative_to(ROOT)}")
    if stale:
        print("FAIL structures out of date: " + ", ".join(stale) + " (run python tools/build_structures.py)")
        sys.exit(1)


if __name__ == "__main__":
    main()
