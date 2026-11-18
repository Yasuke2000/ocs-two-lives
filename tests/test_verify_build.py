"""Offline tests for tools/verify_build.py's comparison (no server): python -I -m unittest discover -s tests"""
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import nbt  # noqa: E402
import verify_build as vb  # noqa: E402
from blueprint import Blueprint  # noqa: E402


def as_capture(size, blocks: dict) -> Path:
    """Write blocks as a structure file, the way /ttlcapture saves a region."""
    bp = Blueprint("capture", size)
    bp.blocks = dict(blocks)
    path = Path(tempfile.mkdtemp(prefix="ttl-verify-test-")) / "capture.nbt"
    nbt.write_gzip(path, bp.to_structure())
    return path


class CompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.size, cls.expected, cls.slabs = vb.load_expected(vb.structure_files("tempest"))

    def roundtrip(self, blocks):
        size, actual = vb.read_structure(nbt.read_gzip(as_capture(self.size, blocks)))
        self.assertEqual(tuple(size), tuple(self.size))
        return vb.compare(self.expected, actual)

    def test_slabs_stack_along_z(self):
        self.assertEqual(len(self.slabs), 4)
        self.assertEqual(self.size, (91, 40, 91))
        self.assertEqual([s[1] for s in self.slabs], [0, 23, 46, 69])
        self.assertTrue(any(z >= 69 for _, _, z in self.expected))

    def test_self_is_identical(self):
        r = self.roundtrip(self.expected)
        self.assertEqual(r["percent"], 100.0)
        self.assertEqual(r["exact"], r["defined"])
        self.assertEqual(r["defined"], len(self.expected))

    def test_real_changes_are_counted(self):
        blocks = dict(self.expected)
        solid = sorted(p for p, s in blocks.items() if s != "minecraft:air")
        changed = random.Random(7).sample(solid, 25)
        for p in changed:
            blocks[p] = "minecraft:gold_block"
        missing = [p for p, s in sorted(blocks.items()) if s == "minecraft:air"][:5]
        for p in missing:
            blocks[p] = "minecraft:cobblestone"  # something grew or fell into the build
        r = self.roundtrip(blocks)
        self.assertEqual(r["mismatched"], 30)
        self.assertEqual(sum(r["pairs"].values()), 30)
        self.assertIn(("minecraft:air", "minecraft:cobblestone"), r["pairs"])
        self.assertLess(r["percent"], 100.0)
        text = vb.report("tempest", r, (-45, 60, -57), self.slabs, 5)
        self.assertIn("mismatches per slab", text)
        self.assertIn("-> gold_block", text)

    def test_game_adjustments_are_ignored(self):
        expected = {
            (0, 0, 0): "minecraft:oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]",
            (1, 0, 0): "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]",
            (2, 0, 0): "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]",
            (3, 0, 0): "minecraft:grass_block[snowy=false]",
            (4, 0, 0): "minecraft:wheat[age=7]",
            (5, 0, 0): "minecraft:redstone_lamp[lit=false]",
            (6, 0, 0): "minecraft:cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]",
            (7, 0, 0): "minecraft:grass_block[snowy=false]",
            (8, 0, 0): "minecraft:air",
            (9, 0, 0): "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]",
        }
        actual = {
            (0, 0, 0): "minecraft:oak_fence[east=true,north=false,south=false,waterlogged=false,west=true]",
            (1, 0, 0): "minecraft:oak_stairs[facing=north,half=bottom,shape=outer_left,waterlogged=false]",
            (2, 0, 0): "minecraft:oak_leaves[distance=2,persistent=true,waterlogged=true]",
            (3, 0, 0): "minecraft:grass_block[snowy=true]",
            (4, 0, 0): "minecraft:wheat[age=3]",
            (5, 0, 0): "minecraft:redstone_lamp[lit=true]",
            (6, 0, 0): "minecraft:cobblestone_wall[east=low,north=tall,south=none,up=false,waterlogged=false,west=none]",
            (7, 0, 0): "minecraft:dirt",
            (8, 0, 0): "minecraft:cave_air",
            # facing is a real difference: the build was rotated or edited
            (9, 0, 0): "minecraft:oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]",
        }
        r = vb.compare(expected, actual)
        self.assertEqual(r["exact"], 0)
        self.assertEqual(r["adjusted"], 7)
        self.assertEqual(r["soft"], 2)
        self.assertEqual(r["mismatched"], 1)
        (want, got), = r["pairs"]
        self.assertIn("facing=north", want)
        self.assertIn("facing=south", got)

    def test_positions_outside_the_blueprint_do_not_count(self):
        # Tempest defines its whole box (air included); a sparse build leaves the rest to the world.
        expected = {(0, 0, 0): "minecraft:stone", (1, 0, 0): "minecraft:air"}
        actual = {(0, 0, 0): "minecraft:stone", (1, 0, 0): "minecraft:air", (2, 0, 0): "minecraft:diamond_block",
                  (0, 1, 0): "minecraft:oak_log[axis=y]"}
        r = vb.compare(expected, actual)
        self.assertEqual((r["defined"], r["percent"]), (2, 100.0))

    def test_missing_capture_positions_are_mismatches(self):
        blocks = dict(self.expected)
        gone = next(iter(blocks))
        del blocks[gone]
        r = vb.compare(self.expected, blocks)
        self.assertEqual(r["mismatched"], 1)
        self.assertEqual(next(iter(r["pairs"]))[1], "(not captured)")

    def test_cli_offline_capture(self):
        path = as_capture(self.size, self.expected)
        self.assertEqual(vb.main(["tempest", "--capture", str(path), "-45", "60", "-57"]), 0)
        blocks = {p: ("minecraft:stone" if s != "minecraft:air" else s) for p, s in self.expected.items()}
        self.assertEqual(vb.main(["tempest", "--capture", str(as_capture(self.size, blocks))]), 1)

    def test_dwargon_slabs(self):
        size, expected, slabs = vb.load_expected(vb.structure_files("dwargon"))
        self.assertEqual(size, (148, 92, 168))
        self.assertEqual([(s[1], s[2]) for s in slabs], [(0, 56), (56, 112), (112, 168)])

    def test_forceload_strips_stay_under_256_chunks(self):
        strips = list(vb.chunk_strips(-300, -300, 300, 300))
        chunks = 0
        for x0, z0, x1, z1 in strips:
            n = ((x1 >> 4) - (x0 >> 4) + 1) * ((z1 >> 4) - (z0 >> 4) + 1)
            self.assertLessEqual(n, 256)
            chunks += n
        self.assertEqual(chunks, ((300 >> 4) - (-300 >> 4) + 1) ** 2)


if __name__ == "__main__":
    unittest.main()
