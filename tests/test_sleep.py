"""Sleeping through the night in the Mortal Realm (life/sleep.js, issue #86): tests/sleep_skip.js (node) on the event
handler. The in-game check is tests/ingame/sleep.rcon."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Sleep(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_sleep_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "sleep_skip.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_ingame_test_exists(self):
        rcon = (ROOT / "tests" / "ingame" / "sleep.rcon").read_text(encoding="utf-8")
        self.assertIn("ttl sleep expect morning", rcon)
        self.assertIn("ttl sleep TtlBotSleep clear", rcon)


if __name__ == "__main__":
    unittest.main()
