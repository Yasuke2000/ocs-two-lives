"""Lerfing's map as the Life 2 overworld: the grid, the regions and every canon anchor (python -I -m unittest discover -s tests)

design/architecture/lerfing-import.md §3: canon_map.txt is Lerfing's land mask (tools/lerfing_grid.py), the region letters
come from the polygons in canon_regions.json, and design/data/anchors.toml holds every canon place in his coordinates.
These tests keep them in step: each anchor stands on land (or on water when it is meant to) inside its region, Tempest is
in Jura and Dwargon in the Canaat, the Jura rings fall where the owner decided (Q4), nothing of ours stands on Lerfing's or
Paulzero's builds, and the Dragon's Nest stays under the build limit. The raster checks run when the land mask is
available (design/data/lerfing/, WP-L1; or $LERFING_RASTERS for the analysis rasters) and are skipped otherwise.
"""
import json
import math
import os
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
GRID = ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
ANCHORS = ROOT / "design" / "data" / "anchors.toml"
BUILDS = ROOT / "design" / "builds"
GENERATED = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated"
TERRITORIAL_WATERS = 128  # CanonGrid.TERRITORIAL_WATERS
BUILD_LIMIT = 320


def raster_dir():
    for d in (os.environ.get("LERFING_RASTERS"), ROOT / "design" / "data" / "lerfing"):
        if d and any((Path(d) / n).is_file() for n in ("landmask16.png", "landmask.png")):
            return Path(d)
    return None


class LerfingAnchors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canon = json.loads(CANON.read_text(encoding="utf-8"))
        data = tomllib.loads(ANCHORS.read_text(encoding="utf-8"))
        cls.anchors = {k: dict(v, id=k) for k, v in data.items() if k != "keepout"}
        cls.keepouts = [dict(v, id=k) for k, v in data.get("keepout", {}).items()]
        lines = GRID.read_text(encoding="utf-8").splitlines()
        m = next(re.match(r"# origin (\d+) (\d+)", t) for t in lines if t.startswith("# origin"))
        cls.oc, cls.orow = int(m[1]), int(m[2])
        cls.rows = [t for t in lines if not t.startswith("#")]

    # --- helpers ------------------------------------------------------------------------------------------------------

    def cell(self, x, z):
        c, r = self.oc + (x >> 4), self.orow + (z >> 4)
        return self.rows[r][c] if 0 <= r < len(self.rows) and 0 <= c < len(self.rows[r]) else "."

    def owner(self, x, z):
        """CanonGrid.ownerCell: the letter on land; for '~' and for '.' within TERRITORIAL_WATERS, the nearest nation."""
        ch = self.cell(x, z)
        if ch.isalpha():
            return ch
        reach = 64 if ch == "~" else TERRITORIAL_WATERS // 16 + 1
        best = None
        for dr in range(-reach, reach + 1):
            for dc in range(-reach, reach + 1):
                other = self.cell(x + dc * 16, z + dr * 16)
                if other.isalpha():
                    d = math.hypot(dc, dr) * 16
                    if best is None or d < best[0]:
                        best = (d, other)
        if best is None or (ch == "." and best[0] > TERRITORIAL_WATERS):
            return None
        return best[1]

    def dist(self, a, b):
        return math.hypot(a["x"] - b["x"], a["z"] - b["z"])

    # --- the grid -----------------------------------------------------------------------------------------------------

    def test_grid_is_lerfings_inner_tiles(self):
        x0, z0, x1, z1 = self.canon["lerfing"]["inner"]
        self.assertEqual((x0, z0, x1, z1), (-8064, -6016, 8192, 6528))
        self.assertEqual(len(self.rows), (z1 - z0) // 16, "784 rows")
        self.assertTrue(all(len(r) == (x1 - x0) // 16 for r in self.rows), "1,016 columns in every row")
        self.assertEqual((self.oc, self.orow), (-x0 // 16, -z0 // 16), "world 0, 0 is Lerfing's 0, 0")
        allowed = set(self.canon["regions"]) | {".", "~"}
        used = set("".join(self.rows))
        self.assertLessEqual(used, allowed)
        self.assertEqual(used - {".", "~"}, set(self.canon["regions"]), "every region owns land")
        self.assertEqual(self.cell(-453, 979), "U", "Lerfing's spawn chest stands in Ulgracia")

    def test_regions_file(self):
        c = self.canon
        for gone in ("reference", "width", "paint_width", "origin", "paint"):
            self.assertNotIn(gone, c)
        self.assertEqual((c["ring"], c["blend"]), (2000, 800))
        self.assertEqual(c["sites"], [], "no sites; the key stays so every reader parses the file")
        for key, r in c["regions"].items():
            self.assertNotIn("seeds", r, key)
            self.assertIn(key, c["lerfing"]["polygons"], f"{key} has a polygon")
        for lm in c["landmarks"]:
            self.assertNotIn("ref", lm)
            self.assertEqual(len(lm["at"]), 2)

    def test_jura_rings_by_radius_from_tempest(self):
        z = self.canon["regions"]["J"]["zones"]
        t = self.anchors["tempest"]
        self.assertEqual(z["centre"], [t["x"], t["z"]])
        rings = z["rings"]
        self.assertEqual([(r["name"], r.get("radius")) for r in rings], [("core", 200), ("band", 600), ("rim", None)])
        self.assertFalse(any("depth" in r for r in rings), "Q4: rings by radius only")
        self.assertEqual(rings[0]["biomes"], [["tensura:ancient_forest", 1]])
        self.assertEqual(rings[1]["biomes"], [["minecraft:dark_forest", 1]])
        fade = z["fade"]
        # §3.6: the band holds the goblin village, the Sealed Cave and the Spirit Gate; the arrival, Treyni and the
        # dwarf village lie outside it.
        for aid in ("goblin_village", "sealed_cave", "spirit_gate"):
            with self.subTest(anchor=aid):
                self.assertTrue(200 < self.dist(self.anchors[aid], t) < 600, self.dist(self.anchors[aid], t))
        for aid in ("arrival", "wayfarers_camp", "treyni_grove", "treyni_shrine", "dwarf_village", "rookie_camp", "old_well"):
            with self.subTest(anchor=aid):
                self.assertGreater(self.dist(self.anchors[aid], t), 600 + fade + 16, "outside the dark band")

    # --- anchors ------------------------------------------------------------------------------------------------------

    def test_every_anchor_on_its_ground_and_in_its_region(self):
        for aid, a in self.anchors.items():
            with self.subTest(anchor=aid):
                ch = self.cell(a["x"], a["z"])
                if a["surface"] == "land":
                    self.assertIn(ch, a["region"], f"({a['x']}, {a['z']}) reads {ch!r}, want land of {a['region']}")
                elif a["surface"] == "water":
                    self.assertIn(ch, ".~", f"({a['x']}, {a['z']}) reads {ch!r}, want water")
                self.assertIn(self.owner(a["x"], a["z"]) or "-", a["region"], "owned by its region")

    def test_tempest_in_jura_dwargon_in_the_canaat(self):
        a = self.anchors
        self.assertEqual((a["tempest"]["x"], a["tempest"]["z"]), (1720, 900))
        self.assertEqual(self.cell(1720, 900), "J")
        self.assertEqual((a["dwargon"]["x"], a["dwargon"]["z"]), (1878, -544))
        for aid in ("dwargon", "dwargo", "dwargon_throne", "kaijin_smithy", "dragons_nest"):
            self.assertEqual(self.cell(a[aid]["x"], a[aid]["z"]), "D", aid)
        # The gate faces south down the road to Tempest: the city lies north of the gate, Tempest straight south.
        self.assertLess(a["dwargo"]["z"], a["dwargon"]["z"])
        self.assertLess(abs(a["dwargon"]["x"] - a["tempest"]["x"]), 300)

    def test_arrival_is_safe_jura_rim(self):
        a = self.anchors["arrival"]
        self.assertEqual(self.cell(a["x"], a["z"]), "J")
        for dz in range(-128, 129, 16):
            for dx in range(-128, 129, 16):
                self.assertNotIn(self.cell(a["x"] + dx, a["z"] + dz), ".~W", f"no water within 128 blocks ({dx}, {dz})")
        # 100-150 blocks inside Jura (§3.2): a non-J land cell is within reach, but not within 64 blocks.
        near = min((math.hypot(dx, dz) for dz in range(-256, 257, 16) for dx in range(-256, 257, 16)
                    if self.cell(a["x"] + dx, a["z"] + dz) not in "J~"), default=999)
        self.assertTrue(64 <= near <= 200, f"border {near:.0f} blocks away")

    def test_relative_anchors(self):
        for aid, a in self.anchors.items():
            if "of" in a:
                with self.subTest(anchor=aid):
                    base = self.anchors[a["of"]]
                    self.assertEqual((a["x"], a["z"]), (base["x"] + a["dx"], base["z"] + a["dz"]))

    def test_canon_landmarks_match_their_anchor(self):
        by_canon = {a["canon"]: a for a in self.anchors.values() if "canon" in a}
        for lm in self.canon["landmarks"]:
            with self.subTest(landmark=lm["name"]):
                self.assertIn(lm["name"], by_canon)
                self.assertEqual(lm["at"], [by_canon[lm["name"]]["x"], by_canon[lm["name"]]["z"]])

    def test_sarion_fulbrosia_swap(self):
        # Q3: Elmine (Sarion, the Divine Tree) beside Paulzero's giant trees; Jia (Fulbrosia) in the SW crystal hills.
        e, j = self.anchors["elmine"], self.anchors["jia"]
        self.assertEqual(self.cell(e["x"], e["z"]), "S")
        grove = next(k for k in self.keepouts if k["id"] == "paulzero_grove")
        gap = math.hypot(max(grove["x0"] - e["x"], 0, e["x"] - grove["x1"]), max(grove["z0"] - e["z"], 0, e["z"] - grove["z1"]))
        self.assertLess(gap, 128, "beside the grove")
        self.assertEqual(self.cell(j["x"], j["z"]), "H")
        self.assertLess(j["x"], -1600)

    def test_spacing(self):
        beside = {}
        for p in BUILDS.glob("*.toml"):
            b = tomllib.loads(p.read_text(encoding="utf-8"))
            if "beside" in b:
                beside[b["name"]] = b["beside"]
        placed = [a for a in self.anchors.values() if a["kind"] in ("settlement", "arrival", "build", "landmark")]
        for i, a in enumerate(placed):
            for b in placed[i + 1:]:
                names = {a.get("build"), a.get("landmark"), b.get("build"), b.get("landmark")}
                if any(beside.get(n) in names for n in names if n):
                    continue
                with self.subTest(a=a["id"], b=b["id"]):
                    self.assertGreaterEqual(self.dist(a, b), 64)

    def test_builds_clear_of_lerfings_builds(self):
        text = (GENERATED / "builds.js").read_text(encoding="utf-8")
        sizes = {k: v["size"] for k, v in json.loads(text[text.index("{"):]).items()}
        for a in self.anchors.values():
            if a["kind"] not in ("settlement", "arrival", "build", "landmark"):
                continue
            box = (a["x"], a["z"], a["x"], a["z"])
            if a["kind"] == "build":
                b = tomllib.loads((BUILDS / f"{a['build']}.toml").read_text(encoding="utf-8"))
                ax, _, az = b["anchor"]
                sx, _, sz = sizes[a["build"]]
                m = max(b.get("margin", 8), b.get("repair_margin", 8))
                box = (a["x"] - ax - m, a["z"] - az - m, a["x"] - ax + sx - 1 + m, a["z"] - az + sz - 1 + m)
            for k in self.keepouts:
                with self.subTest(anchor=a["id"], keepout=k["id"]):
                    overlap = box[0] <= k["x1"] and k["x0"] <= box[2] and box[1] <= k["z1"] and k["z0"] <= box[3]
                    self.assertFalse(overlap, f"{a['id']} box {box} reaches {k['name']}")

    # --- rasters (skipped without the land mask) ----------------------------------------------------------------------

    def test_rasters(self):
        d = raster_dir()
        if d is None:
            self.skipTest("no Lerfing land mask (design/data/lerfing/ or $LERFING_RASTERS)")
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self.skipTest("numpy and Pillow are needed to read the rasters")
        import lerfing_grid
        inner = self.canon["lerfing"]["inner"]
        x0, z0 = inner[0], inner[1]
        path = next(d / n for n in ("landmask16.png", "landmask.png") if (d / n).is_file())
        classes, bpp, split = lerfing_grid.read_classes(path, inner)

        for aid, a in self.anchors.items():
            with self.subTest(anchor=aid):
                cz, cx = (a["z"] - z0) // bpp, (a["x"] - x0) // bpp
                if a["surface"] == "land":
                    self.assertEqual(classes[cz, cx], 0, f"land in {path.name}")
                    k = max(1, 32 // bpp)
                    self.assertGreaterEqual((classes[cz - k:cz + k + 1, cx - k:cx + k + 1] == 0).mean(), 0.6,
                                            "mostly dry within 32 blocks")
                elif a["surface"] == "water":
                    self.assertNotEqual(classes[cz, cx], 0, f"water in {path.name}")
        if split:
            lake = self.anchors["lake_siss"]
            self.assertEqual(classes[(lake["z"] - z0) // bpp, (lake["x"] - x0) // bpp], 1, "Lake Siss is a lake, not sea")
        cells, _, split = lerfing_grid.load_cells(path, inner)
        grid = lerfing_grid.grid_text(lerfing_grid.build_grid(cells, self.canon, split), self.canon)
        self.assertEqual(grid, GRID.read_text(encoding="utf-8"), "canon_map.txt is what lerfing_grid.py makes")

        heights = next((d / n for n in ("heights16.png", "heightmap16.png") if (d / n).is_file()), None)
        if heights is not None:
            hx, hz, hb = lerfing_grid.raster_meta(heights, inner)
            h = np.array(Image.open(heights)).astype(np.int32) - 64  # both rasters store y + 64
            nest = self.anchors["dragons_nest"]
            b = tomllib.loads((BUILDS / "dragons_nest.toml").read_text(encoding="utf-8"))
            text = (GENERATED / "builds.js").read_text(encoding="utf-8")
            sx, sy, sz = json.loads(text[text.index("{"):])["dragons_nest"]["size"]
            cz, cx = (nest["z"] - hz) // hb, (nest["x"] - hx) // hb
            k = max(1, max(sx, sz) // 2 // hb)
            ground = int(np.percentile(h[cz - k:cz + k + 1, cx - k:cx + k + 1], 90))
            self.assertLess(ground + sy - b["anchor"][1], BUILD_LIMIT, f"Dragon's Nest top on ground y {ground}")

    def test_anchors_on_l1_landmask(self):
        # Pure-Python twin of the raster check (no numpy): WP-L1's landmask16.png through tools/lerfing/common.read_png.
        path = ROOT / "design" / "data" / "lerfing" / "landmask16.png"
        try:
            from lerfing.common import LAKE, LAND, read_png
        except ImportError:
            self.skipTest("tools/lerfing/common.py arrives with WP-L1")
        if not path.is_file():
            self.skipTest("no design/data/lerfing/landmask16.png")
        _, _, rows = read_png(path)
        x0, z0 = self.canon["lerfing"]["inner"][:2]
        for aid, a in self.anchors.items():
            with self.subTest(anchor=aid):
                v = rows[(a["z"] - z0) // 16][(a["x"] - x0) // 16]
                if a["surface"] == "land":
                    self.assertEqual(v, LAND)
                elif a["surface"] == "water":
                    self.assertNotEqual(v, LAND)
        lake = self.anchors["lake_siss"]
        self.assertEqual(rows[(lake["z"] - z0) // 16][(lake["x"] - x0) // 16], LAKE, "Lake Siss is a lake, not sea")

    def test_repaint_agrees(self):
        # WP-L1's offline biome repaint (design/data/lerfing/repaint.json): the Jura rings and the per-build spots
        # must match the anchors and the J zones, and a spot stays inside its build's region.
        path = ROOT / "design" / "data" / "lerfing" / "repaint.json"
        if not path.is_file():
            self.skipTest("design/data/lerfing/repaint.json arrives with WP-L1")
        rp = json.loads(path.read_text(encoding="utf-8"))
        t, zones = self.anchors["tempest"], self.canon["regions"]["J"]["zones"]
        jura = rp["jura"]
        self.assertEqual(jura["centre"], [t["x"], t["z"]])
        self.assertEqual((jura["core"], jura["band"]), (zones["rings"][0]["radius"], zones["rings"][1]["radius"]))
        self.assertEqual(jura["wobble"], zones["fade"])
        spot_anchor = {"claymans_castle": "clayman_castle"}
        for s in rp.get("spots", []):
            with self.subTest(spot=s["name"]):
                a = self.anchors[spot_anchor.get(s["name"], s["name"])]
                self.assertEqual(s["centre"], [a["x"], a["z"]], "the spot is centred on its anchor")
                r = s["radius"]
                for dz in range(-r, r + 1, 16):
                    for dx in range(-r, r + 1, 16):
                        if dx * dx + dz * dz <= r * r:
                            ch = self.cell(a["x"] + dx, a["z"] + dz)
                            self.assertIn(ch, a["region"] + ".~", f"spot reaches {ch} at ({a['x'] + dx}, {a['z'] + dz})")


if __name__ == "__main__":
    unittest.main()
