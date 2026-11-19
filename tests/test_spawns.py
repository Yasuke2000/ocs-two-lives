"""Graded spawn zones round Tempest (design/data/spawns.toml, life/mortal_spawns.js TtlSpawnZones): the data check in
tools/gen_data.py and tests/spawns.js (node) on the generated data. The in-game check is tests/ingame/spawns.rcon."""
import copy
import shutil
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402

SPAWNS = tomllib.loads((ROOT / "design" / "data" / "spawns.toml").read_text(encoding="utf-8"))


class SpawnZones(unittest.TestCase):
    def test_data_passes(self):
        gen_data.check_spawns(copy.deepcopy(SPAWNS))

    def test_bad_data_refused(self):
        for key, value in (("anchor", "nowhere"), ("hostile_keep", 1.5), ("town_radius", 40), ("reduced_radius", 100),
                           ("passive_box", 2)):
            bad = copy.deepcopy(SPAWNS)
            bad["zone"]["tempest"][key] = value
            with self.assertRaises(SystemExit, msg=key):
                gen_data.check_spawns(bad)

    def test_owner_numbers(self):
        z = SPAWNS["zone"]["tempest"]
        self.assertEqual((z["town_radius"], z["reduced_radius"], z["hostile_keep"]), (150, 400, 0.25))

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_spawns_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "spawns.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
