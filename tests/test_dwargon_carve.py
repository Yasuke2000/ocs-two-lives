"""Dwargon is carved into Lerfing's Canaat (WP-L7b, TTL_DWARGON_VERSION 8, sealed rim since 9): python -I -m unittest discover -s tests

The structure keeps no mountain shell over the city (only a lining of LINING blocks), the placement in life/dwargon.js
matches design/data/anchors.toml, and on the committed exact ground sample (design/data/lerfing/dwargon_ground.png,
cut from the imported world by tools/lerfing/dwargon_fit.py --save-sample) the city has at least 6 blocks of
Lerfing's rock over every closed column and the forecourt runs out onto the apron at the box's south edge.
"""
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "blueprints"))
import dwargon  # noqa: E402
from lerfing import dwargon_fit as fit  # noqa: E402

SCRIPT = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "life" / "dwargon.js"


class DwargonCarveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fit.load_footprint()
        cls.model = fit.Model(cls.f)
        cls.gx, cls.gz, cls.base = fit.placement()
        cx, cz = fit.corner(cls.f, cls.gx, cls.gz)
        cls.sample = fit.Sample()
        area = (cx, cz, cx + cls.model.w - 1, cz + cls.model.l - 1)
        cls.covered = cls.sample.covers(*area)
        cls.G, cls.S = fit.heights(cls.sample.at, *area)

    def test_placement_matches_the_anchor_table(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertGreaterEqual(int(re.search(r"TTL_DWARGON_VERSION = (\d+)", text).group(1)), 9)
        self.assertTrue(dwargon.CARVE)
        self.assertIsInstance(self.base, int, "the carve needs a fixed BASE")
        anchors = tomllib.loads((ROOT / "design" / "data" / "anchors.toml").read_text(encoding="utf-8"))
        self.assertEqual((anchors["dwargon"]["x"], anchors["dwargon"]["z"]), (self.gx, self.gz))

    def test_no_shell_over_the_city(self):
        none = self.f["none"]
        roofs = [(i, r) for i, r in enumerate(self.f["roof"]) if r != none]
        self.assertGreater(len(roofs), 2500, "the cavern lost its roof columns")
        # North of the gate wall nothing solid stands above the highest interior air plus the lining (the old massif
        # rose to the top of the box there); evaluate() checks on the real ground that no lining block is exposed.
        w, m = self.model.w, self.f["margin"]
        gate_row = m + dwargon.GATE_Z
        north = [y for i, y in self.model.top.items() if i // w < gate_row]
        self.assertLessEqual(max(north), max(r for _, r in roofs) + dwargon.LINING)

    def test_the_box_top_clears_the_real_ground_over_open_columns(self):
        # The cleft and the crack are explicit air up to the box top; dwargon.js clears above it only as a fallback.
        none, w = self.f["none"], self.model.w
        cx, cz = fit.corner(self.f, self.gx, self.gz)
        top = self.base + self.f["size"][1] - 1
        over = [i for i, c in enumerate(self.f["clear"]) if c != none and self.G.get((cx + i % w, cz + i // w), -999) > top]
        self.assertEqual(over, [])

    def test_cover_and_road_on_the_real_ground(self):
        self.assertTrue(self.covered, "dwargon_ground.png does not cover the box: rerun dwargon_fit.py --world ... --save-sample")
        rep = fit.evaluate(self.model, self.G, self.S, self.gx, self.gz, self.base)
        self.assertEqual(rep["missing"], 0)
        self.assertGreaterEqual(rep["cover"]["min"], fit.MIN_COVER, rep["cover"]["worst"])
        self.assertEqual(rep["cover"]["exposed"], 0, "lining blocks would stand at or above Lerfing's surface")
        self.assertLessEqual(abs(rep["road"]["road_minus_ground"]), 2, "the road must meet the apron at the south edge")
        # Lerfing's mountain stays: only the cleft, the crack and the forecourt's gap fill touch the surface.
        self.assertLess(rep["surface"]["changed_share"], 0.3)
        self.assertLessEqual(rep["surface"]["raised_max"], 16)


if __name__ == "__main__":
    unittest.main()

    def test_shell_covers_the_staging_leaks(self):
        # Staging 19/11/2026 (place audit): Lerfing's springs at the skylight crack's rim and the lava pocket at the
        # cleft's west wall touch the carved air; dwargon.js seals every water and lava cell of the footprint shell.
        f = self.f
        w, m = f["grid"][0], f["margin"]
        cells = set()
        s = f["shell"]
        for k in range(0, len(s), 3):
            x, z = s[k] % w - m, s[k] // w - m
            for y in range(s[k + 1], s[k + 2] + 1):
                cells.add((x, y, z))
        corner = (1804, 142, -664)  # dwargon placed: corner 1804 142 -664 (staging log, version 8)
        leaks = [(1888, 200, -629), (1888, 201, -630), (1836, 149, -527), (1837, 149, -528), (1835, 150, -526),
                 (1836, 150, -528), (1836, 150, -527)]
        for wx, wy, wz in leaks:
            self.assertIn((wx - corner[0], wy - corner[1], wz - corner[2]), cells, f"leak at {wx} {wy} {wz}")
        self.assertLess(len(cells), 60000)
