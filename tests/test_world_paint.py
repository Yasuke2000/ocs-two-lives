"""Own world paint layers (tools/world/paint.py) through tools/world/svg2rasters.py, on test_world_rasters' synthetic isle.

A neutral paint changes nothing; painted height, ruggedness and biome change the rasters; site plates, water and the
coast keep the SVG's values whatever is painted on them; a colour outside the legend is reported, not applied.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "world"))
sys.path.insert(0, str(ROOT / "tests"))
import paint  # noqa: E402
import pngcodec  # noqa: E402
import svg2rasters as s2r  # noqa: E402
from test_world_rasters import OPTS, SYNTH, Raster  # noqa: E402


def frame_for(world, folder):
    """A paint folder covering the synthetic build's box, all layers neutral."""
    folder.mkdir(parents=True, exist_ok=True)
    frame = {"x0": world.x0, "z0": world.z0, "px": 4, "w": world.w, "h": world.h}
    (folder / "frame.json").write_text(json.dumps(frame), encoding="utf-8")
    n = world.w * world.h
    pngcodec.write_png(folder / "height.png", world.w, world.h, bytes([128]) * n)
    pngcodec.write_png(folder / "rugged.png", world.w, world.h, bytes([128]) * n)
    pngcodec.write_png(folder / "biome.png", world.w, world.h, bytes(3 * n), rgb=True)
    (folder / "legend.json").write_text(json.dumps(paint.make_legend(paint.allowed_biomes())), encoding="utf-8")


class PaintLayers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        base = s2r.build(SYNTH, s2r.Options(**OPTS), None)
        s2r.write_outputs(base, root / "base")
        cls.base = Raster(root / "base")
        cls.folder = root / "paint"
        frame_for(base, cls.folder)
        cls.neutral = paint.load(cls.folder)
        gate = next(s for s in cls.base.index["sites"] if s["id"] == "spirit_gate")
        cls.gate = gate
        # A big soft hill over the whole east half (it covers the Spirit Gate plate, the lake and the road) ...
        paint.blob("height", 300, 0, 700, 60, folder=cls.folder)
        paint.blob("rugged", 300, 0, 700, 0.5, folder=cls.folder)
        # ... a cherry grove over the gate and the dark forest, and a smudge in a colour that is in no legend.
        paint.disc(0, 230, 150, "minecraft:cherry_grove", folder=cls.folder)
        w, h, rgb = paint.read_rgb(cls.folder / "biome.png")
        rgb = bytearray(rgb)
        k = ((int((-450 - base.z0) // 4)) * w + int((-450 - base.x0) // 4)) * 3
        rgb[k:k + 3] = bytes((1, 2, 3))
        pngcodec.write_png(cls.folder / "biome.png", w, h, bytes(rgb), rgb=True)
        cls.layers = paint.load(cls.folder)
        world = s2r.build(SYNTH, s2r.Options(**OPTS), None, paint=cls.layers)
        s2r.write_outputs(world, root / "painted")
        cls.world = world
        cls.p = Raster(root / "painted")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_neutral_paint_is_no_paint(self):
        self.assertIsNone(self.neutral)

    def test_height_and_rugged_raised_on_open_land(self):
        b, p = self.base, self.p
        x, z = 350, 150   # open land east of the gate, inside the brush, away from water and the road
        self.assertGreater(p.H(x, z) - b.H(x, z), 30)
        self.assertGreater(p.val("rugged", x, z), b.val("rugged", x, z))

    def test_site_plate_stays_flat_and_at_its_level(self):
        p, gate = self.p, self.gate
        painted_gate = next(s for s in p.index["sites"] if s["id"] == "spirit_gate")
        for dx, dz in ((0, 0), (30, 0), (-30, 10), (0, -40)):
            self.assertAlmostEqual(p.H(gate["x"] + dx, gate["z"] + dz), painted_gate["y"], delta=0.01)
        self.assertEqual(p.biome(gate["x"], gate["z"]), "minecraft:plains")   # the site's biome wins over the paint

    def test_lake_keeps_its_level(self):
        self.assertEqual(self.p.water(220, -260), self.base.water(220, -260))

    def test_biome_paint_and_bad_colour(self):
        self.assertEqual(self.base.biome(-110, 300), "minecraft:dark_forest")
        self.assertEqual(self.p.biome(-110, 300), "minecraft:cherry_grove")   # the SVG forest, repainted
        self.assertEqual(self.p.biome(-450, 300), "minecraft:desert")          # outside the disc: unchanged
        self.assertEqual(sum(self.layers.bad_colours.values()), 1)
        self.assertTrue(any("not in legend.json" in w for w in self.world.warnings))

    def test_sea_stays_sea(self):
        self.assertEqual(self.p.biome(300, 560), "#ocean")
        self.assertEqual(self.p.H(300, 560), self.base.H(300, 560))

    def test_index_records_the_paint(self):
        info = self.p.index["paint"]
        self.assertEqual(info["sha256"], self.layers.fingerprint())
        self.assertNotEqual(self.p.index["source_sha256"], self.base.index["source_sha256"])
        self.assertIsNone(self.base.index["paint"])

    def test_resized_layer_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            (folder / "frame.json").write_text(json.dumps({"x0": 0, "z0": 0, "px": 4, "w": 10, "h": 10}))
            pngcodec.write_png(folder / "height.png", 9, 10, bytes([128]) * 90)
            with self.assertRaisesRegex(ValueError, "do not resize"):
                paint.Paint(folder)


if __name__ == "__main__":
    unittest.main()
