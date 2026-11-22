"""The soul wipe (life/soul_wipe.js, issues #72 #73): tests/soul_wipe.js (node) checks a full reset takes every ability
(uniques only through the registry) and resets the body to Human, and the Life 1 death strip leaves uniques and the body
alone. The wiring is checked here: /ttl reset and the Life 1 death call it, the rebirth's race set resets the EP. The
in-game check is tests/ingame/reset_full.rcon."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl"


class SoulWipe(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_soul_wipe_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "soul_wipe.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_reset_uses_the_wipe(self):
        src = (TTL / "commands.js").read_text(encoding="utf-8")
        body = src[src.index("var reset = ctx =>"):src.index("var registryList")]
        self.assertIn("TtlSoulWipe.full(server, target", body)
        # The old partial reset: uniques only, race set without touching skills or EP.
        self.assertNotIn("TtlRegistry.revokeAll(server, target)", body)
        self.assertNotIn("makeHuman", body)

    def test_life_one_death_strips(self):
        self.assertIn("TtlSoulWipe.lifeOne(server, player)", (TTL / "life" / "death.js").read_text(encoding="utf-8"))

    def test_rebirth_resets_ep(self):
        src = (TTL / "life" / "corridor_flow.js").read_text(encoding="utf-8")
        self.assertRegex(src, r"tensura edit race \$\{name\} set tensura:\$\{race\} true`")

    def test_no_blanket_revoke(self):
        # `revoke <p> all` would take uniques behind the registry (golden rule 1).
        src = (TTL / "life" / "soul_wipe.js").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"ability revoke \$\{[^}]+\} all", src))
        self.assertNotIn("reset ${name} everything", src)


if __name__ == "__main__":
    unittest.main()
