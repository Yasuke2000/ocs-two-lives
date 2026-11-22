"""Life 1 status presets (design/data/karma.toml [presets], karma/life1_status.js, issue #75): the data check in
tools/gen_data.py and tests/life1_status.js (node: every preset is judged as its tier by the real karma formula).
The in-game check is tests/ingame/life1_status.rcon."""
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

KARMA = tomllib.loads((ROOT / "design" / "data" / "karma.toml").read_text(encoding="utf-8"))


class Life1Status(unittest.TestCase):
    def test_data_passes(self):
        gen_data.check_karma_presets(copy.deepcopy(KARMA))

    def test_bad_data_refused(self):
        for name, key, value in (("elite", "tier", "godlike"), ("dark", "dark", "yes"), ("normal", "stats", [1]),
                                 ("normal", "extra", 1)):
            bad = copy.deepcopy(KARMA)
            bad["presets"][name][key] = value
            with self.assertRaises(SystemExit, msg=f"{name}.{key}"):
                gen_data.check_karma_presets(bad)
        for stat, n in (("diamonds_mined", 1), ("play_time", -5), ("trades", 1.5)):
            bad = copy.deepcopy(KARMA)
            bad["presets"]["normal"]["stats"][stat] = n
            with self.assertRaises(SystemExit, msg=stat):
                gen_data.check_karma_presets(bad)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_presets_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "life1_status.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
