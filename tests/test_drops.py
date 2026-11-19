"""Placement without junk drops (life/drops.js, the sweep in life/chunk_hold.js): tests/drops.js on a fake level (node).
No world, no server; the in-game check is tests/ingame/drops.rcon."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Drops(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_drops_js(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "drops.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_placers_remove_without_drops(self):
        life = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "life"
        roads = (life / "trade_roads.js").read_text(encoding="utf-8")
        self.assertNotIn("minecraft:air`)", roads.split("clear(server, x, y0, y1, z) {")[0],
                         "trade_roads.js clears through clear() (TtlDrops), not a plain fill ... air")
        self.assertIn("TtlDrops.replace", (life / "unplace.js").read_text(encoding="utf-8"))
        self.assertNotIn("setBlock(pos, rock, 2)", (life / "dwargon.js").read_text(encoding="utf-8"))
        self.assertIn("this.sweep(server, h)", (life / "chunk_hold.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
