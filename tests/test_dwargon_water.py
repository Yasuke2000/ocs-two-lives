"""Dwargon's water stays where the blueprint put it: python -I -m unittest discover -s tests

verify_build.py found 147 `air -> water` blocks spreading over the plaza (18/11/2026): the fountain's water sat next to
stairs and slabs, which are waterloggable, so the game let it flow into them and on from there. Every water block must have
only water or a solid full block on its four sides and below, never air, a waterloggable block or an open container.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import verify_build as vb  # noqa: E402
from tiers import heavy  # noqa: E402

WATERLOGGABLE = ("_stairs", "_slab", "_fence", "_wall", "_trapdoor", "_sign", "ladder", "chain", "lantern", "bars",
                 "_pane", "scaffolding", "campfire", "barrel", "chest", "conduit", "sea_pickle", "pointed_dripstone")
OPEN = ("air", "cave_air", "void_air")


def name(state: str) -> str:
    return state.split("[")[0].split(":")[-1]


@heavy("loads dwargon, ~6 s for the class")
class DwargonWaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.blocks, _ = vb.load_expected(vb.structure_files("dwargon"))

    def test_the_fountain_holds_water(self):
        water = [p for p, s in self.blocks.items() if name(s) == "water"]
        self.assertGreater(len(water), 10, "the plaza fountain disappeared")

    def test_water_cannot_leak(self):
        leaks = []
        for (x, y, z), state in self.blocks.items():
            if name(state) != "water":
                continue
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
                other = self.blocks.get((x + dx, y + dy, z + dz))
                if other is None:
                    # a position the structure leaves out belongs to the world: only fine below the build
                    leaks.append(((x, y, z), (dx, dy, dz), "undefined"))
                    continue
                n = name(other)
                if n == "water":
                    continue
                if n in OPEN or any(k in n for k in WATERLOGGABLE):
                    leaks.append(((x, y, z), (dx, dy, dz), other))
        self.assertEqual(leaks[:5], [], f"{len(leaks)} water side(s) are open or waterloggable")


if __name__ == "__main__":
    unittest.main()
