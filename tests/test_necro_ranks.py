"""necro.toml rank, Church and licence checks (WP-N3): python -I -m unittest discover -s tests

tools/gen_data.py check_necro_ranks guards what necro/necro.js reads by name: the ways in, the Rite, the four ranks, the
Church's Sense (O-N5: Marked 20, Hunt 50, decay 5 a week), the Hunt and the licence (Honored + 14 clean days).
"""
import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402


def load(name: str) -> dict:
    with (ROOT / "design" / "data" / f"{name}.toml").open("rb") as f:
        return tomllib.load(f)


class NecroRankTests(unittest.TestCase):
    def setUp(self):
        self.necro = load("necro")
        self.factions = load("factions")
        self.bosses = load("bosses")

    def check(self, n: dict) -> None:
        gen_data.check_necro_ranks(n, self.factions, self.bosses)

    def fails(self, mutate) -> None:
        n = copy.deepcopy(self.necro)
        mutate(n)
        with self.assertRaises(SystemExit):
            self.check(n)

    def test_shipped_data_passes(self):
        self.check(self.necro)

    def test_owner_values(self):
        ch, li = self.necro["church"], self.necro["licence"]
        self.assertEqual((ch["marked_at"], ch["hunt_at"], ch["decay_per_week"]), (20, 50, 5))   # O-N5
        self.assertEqual((li["band"], li["clean_days"]), ("honored", 14))
        self.assertEqual([r["title"] for r in self.necro["rank"]], ["Gravebinder", "Bonecaller", "Death Marshal", "Overlord"])
        self.assertEqual([r["points"] for r in self.necro["rank"]], [0, 30, 120, 400])
        self.assertEqual(self.necro["points"]["weekly_cap"], 60)
        self.assertEqual(self.necro["rite"]["ash"], 10)
        need = self.necro["rank"][3]["needs_any"]
        self.assertIn("tensura:wight_king", need["races"])
        self.assertIn("tensura:vampire", need["races"])
        self.assertEqual(need["skills"], ["tensura:mortal_fear"])
        self.assertIn("hinata_sakaguchi", ch["hunter_bosses"])

    def test_renown_stage_row(self):
        self.assertEqual(self.factions["renown"]["stage"].get("ttl.necro.rank4"), 10)

    def test_bad_values_fail(self):
        self.fails(lambda n: n["church"].update(marked_at=60))
        self.fails(lambda n: n["church"].update(hunter_bosses=["no_such_boss"]))
        self.fails(lambda n: n["church"].update(faction="no_such_faction"))
        self.fails(lambda n: n["church"].update(marked_mult=0.5))
        self.fails(lambda n: n["rank"][1].update(points=500))
        self.fails(lambda n: n["rank"][0].update(points=5))
        self.fails(lambda n: n["rank"][3].pop("needs_any"))
        self.fails(lambda n: n["rank"].pop())
        self.fails(lambda n: n["rite"].update(spells=["Not An Id"]))
        self.fails(lambda n: n["licence"].update(band="beloved"))
        self.fails(lambda n: n["licence"].update(revoke_rep=5))
        self.fails(lambda n: n["hunt"].update(survive_minutes=24 * 60 + 1))
        self.fails(lambda n: n["hunt"].update(announce="The Hunt is on."))
        self.fails(lambda n: n.pop("church"))


if __name__ == "__main__":
    unittest.main()
