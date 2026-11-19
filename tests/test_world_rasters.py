"""Own world, WP-W1: world/map.svg -> the generator rasters (python -I -m unittest discover -s tests)

design/architecture/own-world.md §2-§3. A synthetic small map (an island coast, a mountain with a ridge, a hill with a
lake at 90 that a brook steps down into, a dark forest, a desert, two regions, a paved road and three sites: the Sealed
Cave carved into the mountain, the Spirit Gate in a clearing, Siltrosso on the coast) goes through
tools/world/svg2rasters.py once; the tests read the PNGs and JSON it writes and check pixel values, the crop and its
margins, determinism, and that the structure exclusion mask covers the sites, the road and the carve cavity.
"""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "world"))
import build as world_build  # noqa: E402
import pngcodec  # noqa: E402
import sites_from_builds as sfb  # noqa: E402
import svg2rasters as s2r  # noqa: E402
import svgparse  # noqa: E402

SYNTH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8000 -6000 16000 12000">
  <g id="coast"><polygon data-name="isle" points="-600,-300 -450,-450 0,-470 450,-450 600,-300 620,0 600,300 450,450
    0,470 -450,450 -600,300 -620,0"/></g>
  <g id="lakes"><polygon id="hill_lake" data-level="90" points="140,-330 300,-330 300,-200 140,-200"/></g>
  <g id="rivers"><polyline id="brook" data-width="8" points="480,-110 420,-150 340,-210 280,-250"/></g>
  <g id="mountains">
    <polygon id="peak" data-peak="180" points="-560,-430 -60,-430 -60,-30 -560,-30"/>
    <polyline class="ridge" points="-500,-300 -120,-300"/>
  </g>
  <g id="hills"><polygon id="hill" data-height="96" points="40,-420 580,-420 580,-20 40,-20"/></g>
  <g id="forests"><polygon data-type="dark" points="-200,100 200,100 200,350 -200,350"/></g>
  <g id="biomes"><polygon data-biome="minecraft:desert" points="-560,200 -300,200 -300,420 -560,420"/></g>
  <g id="regions">
    <polygon data-letter="J" points="-700,-600 0,-600 0,600 -700,600"/>
    <polygon data-letter="R" points="0,-600 700,-600 700,600 0,600"/>
  </g>
  <g id="roads"><polyline data-kind="main" data-id="test_road" points="0,200 200,300 400,400"/></g>
  <g id="sites">
    <circle data-id="sealed_cave" data-site="carve" cx="-300" cy="-150" r="80"/>
    <circle data-id="spirit_gate" data-site="clearing" cx="0" cy="200" r="56"/>
    <circle data-id="siltrosso" data-site="coast" cx="400" cy="400" r="70"/>
  </g>
  <g id="labels"><text x="0" y="0">Isle</text></g>
</svg>
"""
OPTS = dict(sea_margin=256, region=256)
FILES = ("height.png", "rugged.png", "water.png", "road.png", "biome.png", "sites.png", "exclude.png", "index.json",
         "sites.json", "roads.json", "canon_map.txt")


class Raster:
    """One output dir read back: values by block position (the pixel that holds the block)."""

    def __init__(self, out):
        self.out = Path(out)
        self.index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        b = self.index["box"]
        self.x0, self.z0, self.w, self.h = b["x0"], b["z0"], b["width_px"], b["height_px"]
        self.png = {}
        for name in ("height", "rugged", "water", "road", "biome", "sites", "exclude"):
            w, h, data, pal = pngcodec.read_png(self.out / ("%s.png" % name))
            assert (w, h) == (self.w, self.h), name
            self.png[name] = data
        self.biomes = self.index["files"]["biome"]["biomes"]

    def g(self, x, z):
        i, j = int((x - self.x0) // 4), int((z - self.z0) // 4)
        return j * self.w + i

    def H(self, x, z):
        return self.png["height"][self.g(x, z)] / 16 - 64

    def Hb(self, x, z):
        """Bilinear between pixel centres, as the generator samples."""
        u, v = (x - self.x0) / 4 - 0.5, (z - self.z0) / 4 - 0.5
        i, j = math.floor(u), math.floor(v)
        tu, tv = u - i, v - j
        hv = self.png["height"]
        def at(a, b):  # noqa: E306
            a, b = min(max(a, 0), self.w - 1), min(max(b, 0), self.h - 1)
            return hv[b * self.w + a] / 16 - 64
        top = at(i, j) + (at(i + 1, j) - at(i, j)) * tu
        bot = at(i, j + 1) + (at(i + 1, j + 1) - at(i, j + 1)) * tu
        return top + (bot - top) * tv

    def water(self, x, z):
        v = self.png["water"][self.g(x, z)]
        return v - 64 if v else None

    def biome(self, x, z):
        return self.biomes[self.png["biome"][self.g(x, z)]]

    def val(self, name, x, z):
        return self.png[name][self.g(x, z)]


def run_synth(out, svg=SYNTH, seed=s2r.SEED):
    world = s2r.build(svg, s2r.Options(seed=seed, **OPTS), None)
    s2r.write_outputs(world, out)
    return world


class WorldRasters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "a"
        cls.world = run_synth(cls.out)
        cls.r = Raster(cls.out)
        cls.site = {s["id"]: s for s in cls.r.index["sites"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---- crop, margins, formats
    def test_crop_and_margins(self):
        b = self.r.index["box"]
        # content: the coast polygon's bbox -620..620 x -470..470; + 256 of sea, rounded out to 256
        self.assertEqual(b["content"], [-620, -470, 620, 470])
        self.assertEqual((b["x0"], b["z0"], b["x1"], b["z1"]), (-1024, -768, 1024, 768))
        self.assertEqual((b["width_px"], b["height_px"]), (512, 384))
        for v in (b["x0"], b["z0"], b["x1"], b["z1"]):
            self.assertEqual(v % 256, 0)
        self.assertGreaterEqual(-620 - b["x0"], 256)
        self.assertGreaterEqual(b["x1"] - 620, 256)
        self.assertGreaterEqual(-470 - b["z0"], 256)
        self.assertGreaterEqual(b["z1"] - 470, 256)
        self.assertEqual(self.r.index["pixel"]["blocks"], 4)
        for name in FILES:
            self.assertTrue((self.out / name).is_file(), name)

    def test_default_box_rounds_to_regions(self):
        w = s2r.World(svgparse.parse_svg(SYNTH), s2r.Options())
        x0, z0, x1, z1, _ = w.design_box()
        self.assertEqual((x0, z0, x1, z1), (-2048, -2048, 2048, 2048))
        tiny = s2r.Options(sea_margin=1200, hard_limit=(2048, 2048))
        with self.assertRaises(s2r.MapError):
            s2r.World(svgparse.parse_svg(SYNTH), tiny).design_box()

    def test_png_codec_roundtrip(self):
        p = Path(self.tmp.name) / "rt.png"
        data = [0, 1, 65535, 300, 7, 9]
        pngcodec.write_png(p, 3, 2, data, depth=16)
        self.assertEqual(pngcodec.read_png(p)[:3], (3, 2, data))
        pngcodec.write_png(p, 2, 1, bytes([1, 0]), palette=[(1, 2, 3), (4, 5, 6)])
        self.assertEqual(pngcodec.read_png(p)[2:], ([1, 0], [(1, 2, 3), (4, 5, 6)]))

    # ---- relief
    def test_sea_and_coast(self):
        r = self.r
        self.assertAlmostEqual(r.H(-1000, -700), s2r.DEEP_Y, delta=0.1)
        self.assertEqual(r.biome(-1000, -700), "#ocean")
        self.assertEqual(r.val("biome", -1000, -700), 0)
        self.assertIsNone(r.water(-1000, -700))
        self.assertEqual(r.val("rugged", -1000, -700), round(s2r.RUGGED["default_sea"] * 255))
        # the shelf falls away from the coast, the lowland rises from 63
        self.assertGreater(r.H(0, 520), r.H(0, 700))
        self.assertTrue(60 <= r.H(-620, 0) <= 66, r.H(-620, 0))
        self.assertTrue(64 <= r.H(-400, 150) <= 80, r.H(-400, 150))
        # the first land pixel coming in from the sea is a beach (the coastline wiggles up to WIGGLE blocks)
        first = next(z for z in range(-560, -400, 4) if r.biome(0, z) != "#ocean")
        self.assertLessEqual(abs(first + 470), s2r.WIGGLE + 4)
        self.assertIn(r.biome(0, first), ("minecraft:beach", "minecraft:stony_shore"))

    def test_mountain(self):
        r = self.r
        crest = max(r.H(x, -300) for x in range(-480, -140, 4))
        self.assertTrue(170 <= crest <= 180, crest)
        self.assertLess(r.H(-300, -425), 100)
        self.assertGreater(r.H(-300, -300), r.H(-300, -380))
        self.assertGreaterEqual(r.val("rugged", -300, -300), round(0.75 * 255) - 2)
        self.assertIn(r.biome(-300, -300), ("minecraft:stony_peaks", "minecraft:snowy_slopes"))

    def test_lake_at_90_with_a_rim(self):
        r = self.r
        self.assertEqual(r.water(220, -265), 90)
        self.assertLessEqual(r.H(220, -265), 89)
        self.assertAlmostEqual(r.H(220, -265), 84, delta=0.6)    # floor = level - depth (6)
        self.assertEqual(r.biome(220, -265), "minecraft:river")
        lake = next(lk for lk in self.r.index["lakes"] if lk["id"] == "hill_lake")
        self.assertEqual((lake["level"], lake["depth"]), (90, 6))
        # every dry pixel within 8 blocks of the lake holds the water (rim >= level + 2)
        for x in range(124, 320, 4):
            for z in range(-346, -184, 4):
                if r.water(x, z) is None and r.val("road", x, z) == 0:
                    inside_x = 140 <= x < 300
                    inside_z = -330 <= z < -200
                    dx = 0 if inside_x else min(abs(x - 140), abs(x - 300))
                    dz = 0 if inside_z else min(abs(z + 330), abs(z + 200))
                    if math.hypot(dx, dz) <= 8:
                        self.assertGreaterEqual(r.H(x, z), 92, (x, z))

    def test_river_steps_down_into_the_lake(self):
        river = next(rv for rv in self.r.index["rivers"] if rv["id"] == "brook")
        levels = [rc["level"] for rc in river["reaches"]]
        self.assertGreater(len(levels), 1, river)
        self.assertEqual(levels[-1], 90)
        for a, b in zip(levels, levels[1:]):
            self.assertTrue(1 <= a - b <= s2r.MAX_STEP, levels)
        for rc in river["reaches"][:-1]:
            self.assertGreaterEqual(rc["length"], s2r.MIN_REACH)
        # wet pixels along the brook carry those levels, the bed is cut 1-4 below, the banks stand 2 above
        r = self.r
        for x, z in ((470, -117), (400, -165), (330, -217)):
            lv = r.water(x, z)
            self.assertIn(lv, levels, (x, z))
            self.assertTrue(lv - 4.01 <= r.H(x, z) <= lv - 1, (x, z, r.H(x, z)))
            self.assertEqual(r.biome(x, z), "minecraft:river")

    def test_road_corridor(self):
        r = self.r
        road = json.loads((self.out / "roads.json").read_text(encoding="utf-8"))["roads"][0]
        self.assertEqual((road["id"], road["kind"], road["half"], road["corridor"]), ("test_road", "main", 2, 5))
        pts = road["points"]
        for a, b in zip(pts, pts[1:]):
            run = math.hypot(b[0] - a[0], b[1] - a[1])
            self.assertLessEqual(abs(b[2] - a[2]), s2r.ROAD_GRADE * run + 1e-6)
        mids = [p for p in pts if math.hypot(p[0] - 0, p[1] - 200) > 70 and math.hypot(p[0] - 400, p[1] - 400) > 80]
        self.assertTrue(mids)
        for x, z, y, _ in mids:
            self.assertEqual(r.val("road", x, z), s2r.ROAD_CLASS["main"], (x, z))
            self.assertAlmostEqual(r.H(x, z), y, delta=1.0)
            self.assertEqual(r.val("rugged", x, z), 0)
        self.assertEqual(self.r.index["roads"][0]["bridges"], [])

    # ---- sites
    def test_site_plates(self):
        r, gate = self.r, self.site["spirit_gate"]
        self.assertEqual(gate["kind"], "clearing")
        for d in range(0, 52, 4):
            for ang in range(0, 360, 45):
                x = gate["x"] + d * math.cos(math.radians(ang))
                z = gate["z"] + d * math.sin(math.radians(ang))
                self.assertAlmostEqual(r.H(x, z), gate["y"], delta=0.01, msg=(x, z))
                self.assertEqual(r.val("sites", x, z), gate["index"])
                self.assertEqual(r.val("rugged", x, z), 0)
        self.assertEqual(r.biome(0, 200), "minecraft:plains")     # the site's treeless biome wins
        self.assertEqual(r.biome(-150, 300), "minecraft:dark_forest")   # the forest resumes beyond r
        self.assertEqual(r.biome(-450, 300), "minecraft:desert")
        coast = self.site["siltrosso"]
        self.assertEqual(r.H(coast["x"] - 20, coast["z"] - 20), coast["y"])
        self.assertGreaterEqual(coast["y"], 65)
        self.assertEqual(r.biome(coast["x"], coast["z"] + 69), "#ocean")    # the sea side of a coast site stays sea

    def test_carve_cover(self):
        """Sealed Cave carved into the mountain: >= 6 blocks over every roof column, sampled as the generator does."""
        r, cave = self.r, self.site["sealed_cave"]
        req = sfb.requirements(sfb.Sources(), {"sealed_cave": "carve"})["sealed_cave"]
        ax, _, az = req["anchor"]
        bx0, bz0 = cave["x"] - ax, cave["z"] - az
        worst = min(r.Hb(bx0 + bx + 0.5, bz0 + bz + 0.5) - (cave["y"] + rel) for (bx, bz), rel in req["roof_cols"].items())
        self.assertGreaterEqual(worst, cave["cover"])
        self.assertGreaterEqual(cave["cover"], 6)
        # the approach ravine runs south out of the massif at the gate's level
        self.assertAlmostEqual(r.H(cave["x"], bz0 + 88 + 30), cave["y"], delta=0.01)

    def test_exclusion_mask_covers_sites_roads_and_cavity(self):
        r = self.r
        margin = self.r.index["files"]["exclude"]["margins"]
        for s in self.r.index["sites"]:
            if not s["plated"]:
                continue
            self.assertEqual(s["margin"], margin["site"])     # no data-margin on the synthetic sites: the default
            reach = s["r"] + s["margin"]
            for d in range(0, int(reach) - 3, 6):
                for ang in range(0, 360, 30):
                    x = s["x"] + d * math.cos(math.radians(ang))
                    z = s["z"] + d * math.sin(math.radians(ang))
                    self.assertTrue(r.val("exclude", x, z) & s2r.EXCL["site"], (s["id"], x, z))
        road = json.loads((self.out / "roads.json").read_text(encoding="utf-8"))["roads"][0]
        for x, z, _, _ in road["points"]:
            for off in (-5, 0, 5):
                self.assertTrue(r.val("exclude", x + off * 0.447, z - off * 0.894) & s2r.EXCL["road"], (x, z))
        req = sfb.requirements(sfb.Sources(), {"sealed_cave": "carve"})["sealed_cave"]
        cave = self.site["sealed_cave"]
        bx0, bz0 = cave["x"] - req["anchor"][0], cave["z"] - req["anchor"][2]
        for bx in range(0, 88, 8):
            for bz in range(0, 88, 8):
                self.assertTrue(r.val("exclude", bx0 + bx, bz0 + bz) & s2r.EXCL["cavity"], (bx, bz))
        self.assertEqual(r.val("exclude", -1000, -700), 0)
        self.assertEqual(r.val("exclude", -450, 0), 0)

    def test_sites_json_for_canon_sites(self):
        data = json.loads((self.out / "sites.json").read_text(encoding="utf-8"))
        names = [s["name"] for s in data["sites"]]
        self.assertEqual(names, ["spirit_gate", "siltrosso"])   # carve sites are not flattened
        for s in data["sites"]:
            self.assertEqual(s["terrain"], "flat")
            self.assertTrue(isinstance(s["ground"], int) and isinstance(s["radius"], int))
            self.assertEqual(len(s["centre"]), 2)
        silt = data["sites"][1]
        self.assertLess(silt["radius"], 70)   # the flat pull stops short of the sea

    def test_canon_map(self):
        lines = (self.out / "canon_map.txt").read_text(encoding="utf-8").splitlines()
        origin = next(t for t in lines if t.startswith("# origin")).split()
        self.assertEqual((int(origin[2]), int(origin[3])), (64, 48))
        rows = [t for t in lines if not t.startswith("#")]
        self.assertEqual((len(rows), len(rows[0])), (96, 128))

        def cell(x, z):
            return rows[48 + (z >> 4)][64 + (x >> 4)]
        self.assertEqual(cell(-300, 0), "J")
        self.assertEqual(cell(300, 100), "R")
        self.assertEqual(cell(220, -265), "~")
        self.assertEqual(cell(-1000, -700), ".")

    # ---- determinism
    def test_deterministic(self):
        out = Path(self.tmp.name) / "b"
        run_synth(out)
        for name in FILES:
            self.assertEqual((self.out / name).read_bytes(), (out / name).read_bytes(), name)
        other = Path(self.tmp.name) / "c"
        run_synth(other, seed=s2r.SEED + 1)
        self.assertNotEqual((self.out / "height.png").read_bytes(), (other / "height.png").read_bytes())
        self.assertEqual(json.loads((other / "index.json").read_text(encoding="utf-8"))["box"], self.r.index["box"])


class WorldRasterParts(unittest.TestCase):
    def test_reach_levels(self):
        terr = [100 - k * 0.1 for k in range(120)]        # 480 blocks falling 12
        lv = s2r.reach_levels(terr, 97, 88, 7)
        self.assertEqual((lv[0], lv[-1]), (97, 88))
        last, at = lv[0], 0
        for k, v in enumerate(lv):
            self.assertLessEqual(v, last)
            if v < last:
                self.assertLessEqual(last - v, s2r.MAX_STEP)
                self.assertGreaterEqual((k - at) * 4, s2r.MIN_REACH)
                at = k
            last = v
        self.assertEqual(s2r.reach_levels([70] * 50, 63, 63, 1), [63] * 50)   # a tidal reach stays at 63

    def test_road_profile_bridge(self):
        ys = [70.0] * 10 + [60.0] * 5 + [70.0] * 10
        wet = [False] * 10 + [True] * 5 + [False] * 10
        levels = [63] * 10 + [66] * 5 + [63] * 10
        prof = s2r.road_profile(ys, wet, levels)
        for k in range(10, 15):
            self.assertGreaterEqual(prof[k], 68)        # the deck stands 2 above the water level
        for a, b in zip(prof, prof[1:]):
            self.assertLessEqual(abs(a - b), s2r.ROAD_GRADE * 4 + 1e-9)

    def test_svgparse_path(self):
        shapes = svgparse.parse_svg('<svg viewBox="-8000 -6000 16000 12000"><g id="coast">'
                                    '<path d="M0,0 l10,0 0,10 H0 z"/></g><g id="roads">'
                                    '<path d="M0 0 C 10 0 10 10 20 10"/></g></svg>')
        self.assertEqual(shapes["coast"][0].pts, [(0, 0), (10, 0), (10, 10), (0, 10)])
        self.assertTrue(shapes["coast"][0].closed)
        road = shapes["roads"][0]
        self.assertFalse(road.closed)
        self.assertEqual((road.pts[0], road.pts[-1]), ((0, 0), (20, 10)))

    def test_update_anchors_keeps_everything_else(self):
        text = ('# head\n[a]\nname = "A"\nx = 1\nz = 2\nnotes = "x = 9"\n\n[b]\nx = 5\nz = 6\ny = 7\n'
                '[keepout.k]\nx0 = 1\n')
        out = world_build.update_anchors(text, {"a": (10, 20, 70), "b": (-5, -6, 80)})
        self.assertEqual(out, '# head\n[a]\nname = "A"\nx = 10\nz = 20\ny = 70\nnotes = "x = 9"\n\n'
                              '[b]\nx = -5\nz = -6\ny = 80\n[keepout.k]\nx0 = 1\n')
        anchors = {"p": {}, "c": {"of": "p", "dx": 15, "dz": -5}}
        index = {"sites": [{"id": "p", "x": 100, "z": 200, "y": 70}, {"id": "c", "x": 120, "z": 190, "y": 71}]}
        self.assertEqual(world_build.anchor_coords(index, anchors), {"p": (100, 200, 70), "c": (115, 195, 71)})

    def test_update_canon(self):
        text = '{"landmarks": [\n {\n  "name": "Old \\"x\\"",\n  "kind": "village",\n  "at": [1, 2]\n }\n]}'
        out = world_build.update_canon(text, {"a": {"canon": 'Old "x"'}}, {"a": (5, -6, 70)})
        self.assertEqual(json.loads(out)["landmarks"][0]["at"], [5, -6])


if __name__ == "__main__":
    unittest.main()
