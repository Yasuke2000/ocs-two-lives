"""World works (life/works.js, forests.js, trade_roads.js, world_fixes.js) on the own world: generated/placements.js is
fresh, and the Lerfing-era works stay retired while the own world is applied (pack/config/ttl/world/). On the own world
Tensura's trees grow as structures, the generator paves the designed roads and there is no imported terrain to repair;
a planted forest, trade road or fix at Lerfing's coordinates would land on an unrelated place. The planners and their
plan tests are in git history (own-world-switch; WP-W13 retires tools/lerfing/). No world, no server."""
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_placements  # noqa: E402
from lerfing import forests  # noqa: E402

DATA = ROOT / "design" / "data"
OWN_WORLD = (ROOT / "pack" / "config" / "ttl" / "world" / "index.json").is_file()


class Generated(unittest.TestCase):
    def test_placements_js_fresh(self):
        text = gen_placements.TARGET.read_text(encoding="utf-8")
        self.assertEqual(text, gen_placements.render(), "run python tools/gen_placements.py")

    def test_templates_have_no_labyrinth_portal(self):
        for tid in forests.TEMPLATES:
            self.assertNotIn("labyrinth", tid)


@unittest.skipUnless(OWN_WORLD, "Lerfing's world: its works are configured")
class OwnWorldRetiresLerfingWorks(unittest.TestCase):
    def test_no_forest_patch_trade_road_or_fix(self):
        for rel in ("forests/patches.toml", "trade_roads/roads.toml", "world_fixes/fixes.toml"):
            with (DATA / rel).open("rb") as f:
                self.assertEqual(tomllib.load(f), {}, f"{rel}: a Lerfing-era work on the own world")
        self.assertEqual(sorted(p.name for p in (DATA / "forests").glob("*.json")), [])
        self.assertEqual(sorted(p.name for p in (DATA / "trade_roads").glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
