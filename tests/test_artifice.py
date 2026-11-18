"""The Artificer's data (design/data/artifice.toml, WP-A1): python -I -m unittest discover -s tests

tools/gen_data.py check_artifice must accept the repo's file and refuse the typos that would silently do nothing in game
(an unknown faction, a gated schematic sold in the open pool, a rank that does not rise, a missing roads choice).
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


class ArtificeDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {n: load(n) for n in ("artifice", "factions", "economy", "roads")}

    def check(self, art: dict) -> None:
        gen_data.check_artifice(art, self.data)

    def bad(self, mutate) -> str:
        art = copy.deepcopy(self.data["artifice"])
        mutate(art)
        with self.assertRaises(SystemExit) as ctx:
            self.check(art)
        return str(ctx.exception)

    def test_the_repo_file_passes(self):
        self.check(self.data["artifice"])

    def test_unknown_faction_in_a_reward_fails(self):
        msg = self.bad(lambda a: a["commission"][0]["reward"].__setitem__("rep", {"dwarves": 2}))
        self.assertIn("unknown faction dwarves", msg)

    def test_a_gated_schematic_may_not_be_sold(self):
        msg = self.bad(lambda a: a["schematics"]["pool"].append("tensura:adamantite_gear_schematic"))
        self.assertIn("gated", msg)

    def test_ranks_must_rise(self):
        msg = self.bad(lambda a: a["rank"][2].__setitem__("points", 10))
        self.assertIn("must rise", msg)

    def test_every_commission_tier_is_filled(self):
        msg = self.bad(lambda a: a.__setitem__("commission", [c for c in a["commission"] if c["tier"] != 4]))
        self.assertIn("tier 1..4", msg)

    def test_a_recipe_road_must_exist(self):
        msg = self.bad(lambda a: a["recipe"][0].__setitem__("road", "artifice.nothing.dark"))
        self.assertIn("roads.toml", msg)

    def test_bad_band_requirement_fails(self):
        msg = self.bad(lambda a: a["rank"][3]["requires_any"]["bands"].__setitem__("dwargon", "beloved"))
        self.assertIn("requires_any.bands", msg)


if __name__ == "__main__":
    unittest.main()
