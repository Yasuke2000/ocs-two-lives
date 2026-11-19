"""Jura check of the imported map (tools/lerfing/jura_check.py, WP-L8): python -I -m unittest discover -s tests

The logic is tested on synthetic landscapes (no 9 GB world needed): the verdict of a sample against the repaint
rules, the fewest-ancient-forest-blocks walk, the footprint slope and water figures, the lattice of cell centres, and
the whole run with a fake world that follows repaint.json exactly (exit 0) and one that breaks a ring (exit 1).
"""
import contextlib
import importlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from lerfing.common import RULES, Rules  # noqa: E402

jc = importlib.import_module("lerfing.jura_check")

CORE, BAND = jc.CORE_BIOME, jc.BAND_BIOME


def col(y=65, biome="minecraft:plains", wet=False, block="minecraft:grass_block"):
    return {"class": "water" if wet else "land", "ground_y": y, "ground_block": block, "top_block": block,
            "water_y": y + 2 if wet else None, "water_depth": 2 if wet else None, "biome": biome}


class FakeWorld:
    """A world that returns what repaint.json says, except where `override(x, z)` answers."""

    def __init__(self, override=None):
        self.rules = Rules.load(RULES)
        self.chunks = {}
        self.override = override

    def at(self, x, z):
        if self.override:
            got = self.override(x, z)
            if got is not None:
                return got
        return col(biome=self.rules.area_biome(x, z) or "minecraft:plains")


class TestClassify(unittest.TestCase):
    def setUp(self):
        self.rules = Rules.load(RULES)

    def sample(self, x, z, biome, kind="land"):
        return {"x": x, "z": z, "biome": biome, "kind": kind}

    def test_verdicts(self):
        c = (1722, 902)
        self.assertEqual(jc.classify(self.sample(*c, CORE), self.rules)[1], "ok")
        self.assertEqual(jc.classify(self.sample(*c, "minecraft:plains"), self.rules)[1], "WRONG")
        self.assertEqual(jc.classify(self.sample(*c, "minecraft:beach"), self.rules)[1], "kept")
        self.assertEqual(jc.classify(self.sample(*c, "minecraft:river", "water"), self.rules)[1], "kept")
        self.assertEqual(jc.classify(self.sample(*c, CORE, "water"), self.rules)[1], "kept")
        far = (1780, -150)
        self.assertEqual(jc.classify(self.sample(*far, "minecraft:plains"), self.rules)[1], "rim")
        self.assertEqual(jc.classify(self.sample(*far, BAND), self.rules)[1], "WRONG")
        # inside the band, 400 blocks out
        self.assertEqual(jc.classify(self.sample(1722, 1302, BAND), self.rules)[1], "ok")


class TestWalk(unittest.TestCase):
    def lattice(self, beach_path):
        step = 8
        s = {}
        for x in range(1720 - 320, 1720 + 328, step):
            for z in range(900 - 320, 900 + 328, step):
                d = jc.dist(x, z)
                b = CORE if d < 200 else BAND if d < 600 else "minecraft:plains"
                if beach_path and z == 900 and x >= 1720 and d < 320:
                    b = "minecraft:beach"
                s[(x, z)] = b
        return s

    def test_solid_core_must_be_crossed(self):
        blocks = jc.min_deadly_walk(self.lattice(False), 8)
        self.assertGreaterEqual(blocks, 100)
        self.assertLessEqual(blocks, 144 + 16)

    def test_beach_path_opens_a_way(self):
        self.assertEqual(jc.min_deadly_walk(self.lattice(True), 8), 0)

    def test_blocked_cells_close_it_again(self):
        lat = self.lattice(True)
        wet = {k for k in lat if k[1] == 900 and k[0] == 1720 + 80}
        self.assertGreater(jc.min_deadly_walk(lat, 8, blocked=wet), 0)

    def test_dark_counts_when_asked(self):
        lat = self.lattice(True)
        self.assertEqual(jc.min_deadly_walk(lat, 8, outer=300, bad=(CORE, BAND)), 0)
        no_path = self.lattice(False)
        self.assertGreater(jc.min_deadly_walk(no_path, 8, outer=300, bad=(CORE, BAND)), 100)


class TestFootprint(unittest.TestCase):
    def test_flat_dry_box(self):
        cols = {(x, z): col() for x in range(0, 40, 2) for z in range(0, 40, 2)}
        st = jc.footprint_stats(cols, 2)
        self.assertEqual(st["water_share"], 0.0)
        self.assertEqual(st["slope_max"], 0.0)
        self.assertEqual(st["relief_p90_p10"], 0)
        self.assertEqual(st["within_2_of_median"], 1.0)

    def test_slope_and_water(self):
        cols = {}
        for x in range(0, 40, 2):
            for z in range(0, 40, 2):
                cols[(x, z)] = col(y=65 + (4 if x >= 20 else 0), wet=(z == 0))
        st = jc.footprint_stats(cols, 2)
        self.assertEqual(st["slope_max"], 2.0)          # a 4-block step over 2 blocks
        self.assertAlmostEqual(st["water_share"], 1 / 20, places=3)
        self.assertEqual(st["water_max_depth"], 2)
        self.assertGreater(st["steep_share_gt_0_5"], 0)


class TestSweep(unittest.TestCase):
    def test_samples_sit_on_cell_centres(self):
        s = jc.sweep(FakeWorld(), jc.TEMPEST, 100, 8, Rules.load(RULES))
        self.assertTrue(s)
        self.assertTrue(all(x % 4 == 2 and z % 4 == 2 for x, z in s))
        self.assertTrue(all(abs(x - 1720) <= 100 and abs(z - 900) <= 100 for x, z in s))


class TestRun(unittest.TestCase):
    def args(self, **kw):
        class A:
            world = "(fake)"
            rules = str(RULES)
            step = 16
            radius = 700
            json = None
            png = None
        a = A()
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    def run_with(self, world):
        real = jc.World
        jc.World = lambda world=None: world_obj
        world_obj = world
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = jc.run(self.args())
            return code, buf.getvalue()
        finally:
            jc.World = real

    def test_a_world_that_follows_the_rules_passes(self):
        code, out = self.run_with(FakeWorld())
        self.assertEqual(code, 0, out)
        self.assertIn("0 failed", out)
        self.assertIn("arrival is on the rim", out)

    def test_a_broken_ring_fails(self):
        def override(x, z):
            if abs(x - 1722) < 40 and abs(z - 902) < 40:
                return col(biome="minecraft:plains")      # a plains hole inside the core
            return None
        code, out = self.run_with(FakeWorld(override))
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL", out)

    def test_a_wet_arrival_fails(self):
        def override(x, z):
            if abs(x - 1780) < 6 and abs(z + 150) < 6:
                return col(wet=True)
            return None
        code, out = self.run_with(FakeWorld(override))
        self.assertEqual(code, 1, out)
        self.assertIn("[FAIL] arrival column is dry land", out)


if __name__ == "__main__":
    unittest.main()
