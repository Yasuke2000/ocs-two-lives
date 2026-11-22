"""Sponge schematic v3 writer (WorldEdit `//schem load`, Simple Schematics) for a Blueprint. Stdlib only.

Format: gzipped NBT, root compound {"Schematic": {Version 3, DataVersion, Width/Height/Length (shorts), Offset
(int[3]), Blocks {Palette {state: index}, Data (varint bytes, index = x + z*Width + y*Width*Length), BlockEntities},
Metadata {Name, RequiredMods}}}. Cells the blueprint does not set are written as air (a schematic has no "keep").
Reading is tools/blueprint.py `from_schem`.
"""
from pathlib import Path

import nbt
from blueprint import AIR, DATA_VERSION, parse_state


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def to_schem(bp, data_version: int = DATA_VERSION, offset=(0, 0, 0)) -> dict:
    w, h, l = bp.size
    palette = {AIR: 0}
    data = bytearray()
    for y in range(h):
        for z in range(l):
            for x in range(w):
                state = bp.blocks.get((x, y, z), AIR)
                if state not in palette:
                    palette[state] = len(palette)
                data += _varint(palette[state])
    mods = sorted({parse_state(s)[0].split(":", 1)[0] for s in palette} - {"minecraft"})
    return {"Schematic": {
        "Version": 3,
        "DataVersion": data_version,
        "Width": nbt.Short(w), "Height": nbt.Short(h), "Length": nbt.Short(l),
        "Offset": nbt.IntArray(list(offset)),
        "Blocks": {"Palette": palette, "Data": bytes(data), "BlockEntities": []},
        "Metadata": {"Name": bp.name, "RequiredMods": mods} if mods else {"Name": bp.name},
    }}


def write(bp, path: Path, data_version: int = DATA_VERSION) -> Path:
    if max(bp.size) > 32767:
        raise ValueError("schematic sides are shorts: at most 32767")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nbt.write_gzip(path, to_schem(bp, data_version))
    return path
