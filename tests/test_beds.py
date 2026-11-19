"""Beds in the canon builds (blueprints/_beds.py, owner 19/11/2026): python -I -m unittest discover -s tests

Reads the saved structure files (the NBT the game places), not the blueprint code: every bed is two blocks that
agree (head and foot of one colour and facing), stands on a floor with two free blocks above both halves, and never sits
on the landing in front of a door or at the foot of a ladder; the builds that got beds keep at least as many as listed
and wear their culture's colours (Dwargon red and gray, Blumund and Englassia blue and white, Tempest brown and green).
"""
import importlib
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "blueprints")]

import nbt  # noqa: E402
from tiers import heavy  # noqa: E402

STRUCTURES = ROOT / "pack" / "kubejs" / "data" / "ttl" / "structure"
OFFSET = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
AIR = "minecraft:air"

# Beds (head blocks) each build has at least, and the colours its beds may wear. The beds the Tensura goblin pieces
# bring into Tempest (tensura:thatch_bed) are Tensura's and are only counted, not checked for colour.
EXPECTED = {
    "dwargon": (55, {"red", "gray"}),
    "blumund": (29, {"blue", "white"}),
    "marris": (30, {"light_blue", "white", "purple"}),
    "englassia": (8, {"blue", "white"}),
    "ballachia": (6, {"blue", "white"}),
    "tempest": (9, {"brown", "green", "gray", "light_blue"}),
    "tempest_town": (23, {"brown", "green"}),
    "tempest_city": (10, {"brown", "green", "light_blue"}),
}
VANILLA_BED = "_bed"


def load(name: str) -> dict:
    """Every block of a build in blueprint coordinates, slabs put together (z offset per PARTS)."""
    module = importlib.import_module(name)
    parts = getattr(module, "PARTS", None)
    files = [(STRUCTURES / f"{name}_{i}.nbt", z0) for i, z0 in enumerate(parts)] if parts else [(STRUCTURES / f"{name}.nbt", 0)]
    blocks = {}
    for path, z0 in files:
        root = nbt.read_gzip(path)
        palette = []
        for entry in root["palette"]:
            props = entry.get("Properties") or {}
            palette.append((entry["Name"], props))
        for b in root["blocks"]:
            x, y, z = b["pos"]
            blocks[(x, y, z + z0)] = palette[b["state"]]
    return blocks


def is_bed(state) -> bool:
    return state is not None and state[0].endswith(VANILLA_BED) and state[0].startswith("minecraft:")


def free(blocks, pos) -> bool:
    state = blocks.get(pos)
    return state is None or state[0] == AIR


def problems(blocks: dict) -> list:
    """Everything wrong with the vanilla beds, doors' landings and ladders of one build."""
    out = []
    beds = {p: s for p, s in blocks.items() if is_bed(s)}
    for (x, y, z), (name, props) in sorted(beds.items()):
        part, facing = props.get("part"), props.get("facing")
        if facing not in OFFSET or part not in ("head", "foot"):
            out.append(f"{name} at {x},{y},{z}: bad state {props}")
            continue
        dx, dz = OFFSET[facing]
        other = (x + dx, y, z + dz) if part == "foot" else (x - dx, y, z - dz)
        mate = blocks.get(other)
        want = "head" if part == "foot" else "foot"
        if not mate or mate[0] != name or mate[1].get("part") != want or mate[1].get("facing") != facing:
            out.append(f"{name} {part} at {x},{y},{z} has no matching {want} at {other} (found {mate})")
        floor = blocks.get((x, y - 1, z))
        if floor is None or floor[0] == AIR:
            out.append(f"{name} at {x},{y},{z} has no floor")
        for dy in (1, 2):
            if not free(blocks, (x, y + dy, z)):
                out.append(f"{name} at {x},{y},{z} has no headroom at +{dy}: {blocks[(x, y + dy, z)][0]}")
    for (x, y, z), (name, props) in blocks.items():
        if name.endswith("_door") and props.get("half") == "lower" and props.get("facing") in OFFSET:
            dx, dz = OFFSET[props["facing"]]
            for step in (1, 2):
                if is_bed(blocks.get((x + dx * step, y, z + dz * step))):
                    out.append(f"a bed stands {step} block(s) inside the door at {x},{y},{z}")
        if name == "minecraft:ladder" and props.get("facing") in OFFSET:
            dx, dz = OFFSET[props["facing"]]
            if is_bed(blocks.get((x + dx, y, z + dz))):
                out.append(f"a bed stands at the foot of the ladder at {x},{y},{z}")
    return out


class BedTests(unittest.TestCase):
    @heavy("reads the big canon structures")
    def test_beds_are_whole_reachable_and_in_the_culture_colours(self):
        for name, (minimum, colours) in EXPECTED.items():
            with self.subTest(build=name):
                blocks = load(name)
                bad = problems(blocks)
                self.assertEqual(bad, [], f"{name}: " + "; ".join(bad[:6]))
                heads = Counter(s[0].split(":")[1][:-len(VANILLA_BED)] for s in blocks.values()
                                if is_bed(s) and s[1].get("part") == "head")
                self.assertGreaterEqual(sum(heads.values()), minimum, f"{name} lost beds: {dict(heads)}")
                stray = set(heads) - colours
                self.assertFalse(stray, f"{name}: beds in colours outside {sorted(colours)}: {sorted(stray)}")

    @heavy("reads the big canon structures")
    def test_dwargon_beds_are_in_the_walls_homes_and_street_houses(self):
        blocks = load("dwargon")
        heads = [p for p, s in blocks.items() if is_bed(s) and s[1]["part"] == "head"]
        # Wall homes sit on the cavern balconies (y 17 and up), the street houses below them.
        self.assertGreaterEqual(sum(1 for p in heads if p[1] >= 17), 28)
        self.assertGreaterEqual(sum(1 for p in heads if p[1] < 17), 20)

    @heavy("reads the big canon structures")
    def test_barracks_and_inns_have_several_beds(self):
        def count(name, box, y):
            blocks = load(name)
            x0, z0, x1, z1 = box
            return sum(1 for (x, yy, z), s in blocks.items()
                       if is_bed(s) and s[1]["part"] == "head" and yy == y and x0 <= x <= x1 and z0 <= z <= z1)
        self.assertGreaterEqual(count("blumund", (35, 36, 45, 44), 5), 8, "Blumund's castle barracks")
        self.assertGreaterEqual(count("marris", (34, 25, 46, 32), 9), 6, "Marris' west guard barracks")
        self.assertGreaterEqual(count("marris", (90, 25, 102, 32), 9), 6, "Marris' east guard barracks")
        self.assertGreaterEqual(count("englassia", (26, 77, 36, 85), 5), 4, "Englassia's tavern")
        self.assertGreaterEqual(count("ballachia", (5, 45, 19, 55), 4), 6, "Ballachia's lodging house")
        self.assertGreaterEqual(count("tempest_city", (4, 135, 18, 151), 9), 4, "Tempest city's inn, upstairs")


if __name__ == "__main__":
    unittest.main()
