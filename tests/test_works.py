"""World works (life/works.js, forests.js, trade_roads.js): the checked-in plans against their configs, the keepouts and
each other, and the JS geometry against the planners' (tests/works.js, node). No world, no server."""
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import anchor_refs  # noqa: E402
import gen_placements  # noqa: E402
from lerfing import forests, trade_roads  # noqa: E402


class TradeRoadPlan(unittest.TestCase):
    def setUp(self):
        self.cfg = trade_roads.load_config()["tempest_dwargon"]
        self.road = trade_roads.stored("tempest_dwargon")
        self.cols = trade_roads.rasterize(self.road["points"], self.road["profile"], self.cfg["half"])

    def test_ends_and_stops(self):
        pts = self.road["points"]
        self.assertEqual(pts[0], list(anchor_refs.point("t", "tempest", 0, -58)))
        self.assertEqual(pts[-1], list(anchor_refs.point("t", "dwargon", 0, 47)))
        via = anchor_refs.point("t", "arrival", 30, 0)
        self.assertIn(list(via), pts, "the road passes the Life 2 arrival")
        self.assertEqual(self.road["profile"][-1], self.cfg["to_y"], "meets Dwargon's own road block")

    def test_profile_walks(self):
        p = self.road["profile"]
        self.assertEqual(len(p), len(trade_roads.arc_samples(self.road["points"])))
        self.assertLessEqual(max(abs(b - a) for a, b in zip(p, p[1:])), 1)
        for i in range(0, len(p) - 12):  # never steeper than max_grade over a dozen blocks (rounding: +1)
            self.assertLessEqual(abs(p[i + 12] - p[i]), math.ceil(self.cfg["max_grade"] * 12) + 1, f"arc {i}")
        self.assertLessEqual(self.road["stats"]["cut_max"], 8)
        self.assertLessEqual(self.road["stats"]["fill_max"], 8)

    def test_clear_of_keepouts_and_places(self):
        kos = anchor_refs.keepouts()
        boxes = trade_roads.settlement_boxes()
        start = self.road["points"][0]
        for (x, z), (y, i, o) in self.cols.items():
            for k in kos:
                self.assertFalse(k["x0"] <= x <= k["x1"] and k["z0"] <= z <= k["z1"], f"{x} {z} in keepout {k['id']}")
            t = boxes["tempest"]
            if t[0] <= x <= t[2] and t[1] <= z <= t[3]:  # only the terrain margin north of the village
                self.assertLessEqual(math.hypot(x - start[0], z - start[1]), 12, f"{x} {z} inside Tempest's box")
                self.assertLessEqual(z, start[1] + 1, f"{x} {z} inside the village")
        # the dwarf village (staging box 19/11/2026: 1928..2081 x -206..-75) and the arena stay off the road
        for (x, z) in self.cols:
            self.assertFalse(1928 - 16 <= x <= 2081 + 16 and -206 - 16 <= z <= -75 + 16, f"{x} {z} at the dwarf village")
            self.assertFalse(2247 <= x <= 2333 and -107 <= z <= -45, f"{x} {z} in the dwarven arena")

    def test_stone_stretch_reaches_dwargon(self):
        stone = self.cfg["stone_from"]
        end = self.road["points"][-1]
        self.assertTrue(any(b[0] <= end[0] <= b[2] and b[1] <= end[1] <= b[3] for b in stone))
        start = self.road["points"][0]
        self.assertFalse(any(b[0] <= start[0] <= b[2] and b[1] <= start[1] <= b[3] for b in stone))

    def test_build_profile_bridges_and_ramps(self):
        ground = [70] * 10 + [60] * 6 + [70] * 10
        wet = [None] * 10 + [64] * 6 + [None] * 10
        prof, bridges = trade_roads.build_profile(ground, wet, 0.5)
        self.assertEqual(bridges, [[10, 15]])
        self.assertTrue(all(prof[k] == 70 for k in range(10, 16)), prof)  # deck at the banks (above water + 2)
        wet2 = [None] * 10 + [69] * 6 + [None] * 10
        prof2, _ = trade_roads.build_profile(ground, wet2, 0.5)
        self.assertEqual(prof2[12], 71)
        self.assertLessEqual(max(abs(b - a) for a, b in zip(prof2, prof2[1:])), 1, prof2)


class ForestPlans(unittest.TestCase):
    def test_every_patch_is_planned_and_in_its_ring(self):
        cfg = forests.load_config()
        self.assertEqual(set(cfg), {"tempest", "treyni"})
        roads = []
        for rid in trade_roads.load_config():
            r = trade_roads.stored(rid)
            pts = r["points"]
            roads += [((a[0], a[1], b[0], b[1]), trade_roads.load_config()[rid]["half"]) for a, b in zip(pts, pts[1:])]
        for pid, c in cfg.items():
            plan = forests.stored(pid)
            self.assertIsNotNone(plan, pid)
            cx, cz = plan["centre"]
            self.assertGreater(len(plan["giants"]), 30, pid)
            self.assertGreater(len(plan["understory"]), 500, pid)
            keep = [k["offline"] for k in c.get("keep_clear", [])]
            for ti, x, z, ri in plan["giants"]:
                tp = plan["templates"][plan["giant_keys"][ti]]
                b = forests.giant_box(tp, x, z, forests.ROTATIONS[ri])[2:]
                self.assertLessEqual(math.hypot(x - cx, z - cz), c["giants_outer"])
                for k in keep:
                    self.assertFalse(forests.box_hit(b, k), f"{pid}: giant {x} {z} over {k}")
                for s, half in roads:
                    self.assertGreaterEqual(forests.seg_dist(x, z, *s), half + c["road_gap"] + tp["trunk_r"], f"{pid}: giant {x} {z} on a road")
            for fi, x, z in plan["understory"]:
                self.assertTrue(c["inner"] <= math.hypot(x - cx, z - cz) <= c["outer"])
                for s, half in roads:
                    self.assertGreaterEqual(forests.seg_dist(x, z, *s), half + c["road_gap"], f"{pid}: tree {x} {z} on a road")

    def test_tempest_growth_box_stays_open(self):
        plan = forests.stored("tempest")
        tx, tz = anchor_refs.point("t", "tempest")
        for ti, x, z, ri in plan["giants"]:
            b = forests.giant_box(plan["templates"][plan["giant_keys"][ti]], x, z, forests.ROTATIONS[ri])[2:]
            self.assertFalse(forests.box_hit(b, (tx - 103, tz - 103, tx + 103, tz + 103)), f"giant {x} {z} over Tempest's city box")
        for fi, x, z in plan["understory"]:
            self.assertFalse(abs(x - tx) <= 103 and abs(z - tz) <= 103)

    def test_treyni_lane_open(self):
        c = forests.load_config()["treyni"]
        plan = forests.stored("treyni")
        ln = c["lanes"][0]
        seg = forests.lane_segment(ln["offline"], ln["side"], anchor_refs.point("t", ln["toward"]), ln["length"])
        for fi, x, z in plan["understory"]:
            self.assertGreaterEqual(forests.seg_dist(x, z, *seg), ln["half"] + 2)

    def test_templates_have_no_labyrinth_portal(self):
        for tid in forests.TEMPLATES:
            self.assertNotIn("labyrinth", tid)


class Generated(unittest.TestCase):
    def test_placements_js_fresh(self):
        text = gen_placements.TARGET.read_text(encoding="utf-8")
        self.assertEqual(text, gen_placements.render(), "run python tools/gen_placements.py")

    def test_preview_exists(self):
        self.assertTrue((ROOT / "docs" / "previews" / "tempest-forest-road.png").is_file())

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_matches_planners(self):
        want = {"roads": {}, "forests": {}}
        rcfg = trade_roads.load_config()
        for rid in rcfg:
            road = trade_roads.stored(rid)
            cols = trade_roads.rasterize(road["points"], road["profile"], rcfg[rid]["half"])
            want["roads"][rid] = {
                "columns": sorted([f"{x},{z}", y, i] for (x, z), (y, i, o) in cols.items()),
                "lanterns": [list(l) for l in trade_roads.lanterns(road, rcfg[rid])],
            }
        fcfg = forests.load_config()
        for pid in fcfg:
            plan = forests.stored(pid)
            boxes = [list(forests.giant_box(plan["templates"][plan["giant_keys"][g[0]]], g[1], g[2], forests.ROTATIONS[g[3]]))
                     for g in plan["giants"]]
            lanes = [{"k": k, "seg": list(forests.lane_segment(ln["offline"], ln["side"], anchor_refs.point("t", ln["toward"]), ln["length"]))}
                     for k, ln in enumerate(fcfg[pid].get("lanes", []))]
            want["forests"][pid] = {"boxes": boxes, "lanes": lanes}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "want.json"
            p.write_text(json.dumps(want), encoding="utf-8")
            r = subprocess.run(["node", str(ROOT / "tests" / "works.js"), str(p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
