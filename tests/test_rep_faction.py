"""Faction argument of TtlRep.add/set and the merit code that feeds it (rep/rep.js, economy/merit.js, economy/guild.js):
tests/rep_faction.js on a fake player and server (node). The in-game check is tests/ingame/guild.rcon (merit)."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RepFaction(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_rep_faction_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "rep_faction.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
