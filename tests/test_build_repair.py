"""Terrain repair after the fit (life/repair.js): the planner on synthetic worlds (tests/build_repair.js, node), the TOML
knobs gen_data validates, and the footprint data the placers hand the planner (no server)."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402

GENERATED = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated"


def unrle(values):
    out = []
    for v, n in zip(values[::2], values[1::2]):
        out += [v] * n
    return out


def generated(name, var):
    text = (GENERATED / name).read_text(encoding="utf-8")
    return json.loads(re.search(rf"^const {var} = (\{{.*\}})$", text, re.M).group(1))


_builds = None


def builds():
    global _builds
    if _builds is None:
        _builds = gen_data.check_builds()
    return _builds


class Planner(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_synthetic_worlds(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "build_repair.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class Knobs(unittest.TestCase):
    def test_defaults_and_opt_outs(self):
        by = {b["name"]: b for b in builds()[0]}
        for b in by.values():
            self.assertIn(b["repair"], (True, False))
            self.assertTrue(1 <= b["repair_depth"] <= 96)
            self.assertTrue(0 <= b["repair_margin"] <= 16)
        self.assertTrue(by["raja"]["repair_keep_water"])  # built on its lake
        self.assertFalse(by["walpurgis_hall"]["repair"])  # own dimensions, placed 1:1
        self.assertFalse(by["spirit_dwelling"]["repair"])
        self.assertTrue(by["test_hut"]["repair"])  # tests/ingame/build_repair.rcon
        self.assertTrue(by["nostraille"]["repair"] and by["nostraille"]["repair_depth"] == 48)

    def test_bad_values_are_refused(self):
        source = (gen_data.BUILDS / "test_hut.toml").read_text(encoding="utf-8")
        old = gen_data.BUILDS
        try:
            for line in ('repair = "yes"', "repair_depth = 0", "repair_depth = 97", "repair_margin = 17",
                         "repair_keep_water = 1"):
                with tempfile.TemporaryDirectory() as tmp:
                    (Path(tmp) / "test_hut.toml").write_text(source + line + "\n", encoding="utf-8")
                    gen_data.BUILDS = Path(tmp)
                    with self.assertRaises(SystemExit, msg=line):
                        gen_data.check_builds()
        finally:
            gen_data.BUILDS = old


class Footprints(unittest.TestCase):
    def test_bottom_of_the_test_hut(self):
        fp = gen_data.read_footprint(gen_data.structure_files("test_hut"))
        self.assertEqual(fp["bottom"], [0, 25])

    def test_bottom_includes_explicit_air_and_marks_undefined_columns(self):
        for name, fp in builds()[1].items():
            n = fp["size"][0] * fp["size"][2]
            fill, bottom = unrle(fp["fill"]), unrle(fp["bottom"])
            self.assertEqual(len(bottom), n, name)
            for f, b in zip(fill, bottom):
                if f != fp["none"]:
                    # A defined column: the planner starts below the lowest defined block, never above its solid one.
                    self.assertTrue(b != fp["none"] and b <= f, name)

    def test_tempest_is_defined_from_its_lowest_solid_block(self):
        # tempest.js hands the planner the footprint's `fill` as the bottom of every box column: that is only right
        # while no box column holds explicit air under its lowest solid block, and every column holds a block.
        fp = gen_data.read_footprint(gen_data.structure_files("tempest"))
        self.assertEqual(fp["fill"], fp["bottom"])
        self.assertNotIn(fp["none"], unrle(fp["fill"]))

    def test_dwargon_footprint_carries_bottom(self):
        f = generated("dwargon_footprint.js", "TtlDwargonFootprint")
        fp = gen_data.read_footprint(gen_data.structure_files("dwargon"))
        w, l = f["grid"]
        m = f["margin"]
        grid = unrle(f["bottom"])
        self.assertEqual(len(grid), w * l)
        box = [grid[(z + m) * w + x + m] for z in range(f["size"][2]) for x in range(f["size"][0])]
        self.assertEqual(box, unrle(fp["bottom"]))
        margin = [grid[i] for i in range(w * l) if not (m <= i % w < m + f["size"][0] and m <= i // w < m + f["size"][2])]
        self.assertEqual(set(margin), {f["none"]})


if __name__ == "__main__":
    unittest.main()
