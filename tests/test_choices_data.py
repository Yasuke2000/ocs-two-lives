"""Moral-choice scenes data (design/data/choices.toml, WP-C1): python -I -m unittest discover -s tests

tools/gen_data.py check_choices must accept the shipped file and refuse the mistakes that would silently cost or pay nothing
(an unknown faction, a dark route without karma, a light deed on a dark route, a menu-only `need` on a deed, a scene without
an honest route).
"""
import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402

DATA = ROOT / "design" / "data"


def load(name: str) -> dict:
    with (DATA / f"{name}.toml").open("rb") as f:
        return tomllib.load(f)


class ChoicesDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {n: load(n) for n in ("choices", "roads", "factions", "economy", "world")}

    def check(self, choices: dict) -> None:
        data = dict(self.data)
        data["choices"] = choices
        gen_data.check_choices(choices, data)

    def broken(self, mutate) -> str:
        ch = copy.deepcopy(self.data["choices"])
        mutate(ch)
        with self.assertRaises(SystemExit) as cm:
            self.check(ch)
        return str(cm.exception)

    def route(self, ch: dict, event: str, rid: str) -> dict:
        row = next(c for c in ch["choice"] if c["id"] == event)
        return next(r for r in row["route"] if r["id"] == rid)

    def test_shipped_file_passes(self):
        self.check(copy.deepcopy(self.data["choices"]))

    def test_c1_events_are_there(self):
        ids = {c["id"] for c in self.data["choices"]["choice"]}
        self.assertTrue({"sick_village", "bandit_hostages", "starving_band", "wants_name"} <= ids)

    def test_owner_decisions(self):
        eng = self.data["choices"]["engine"]
        self.assertEqual((eng["max_active"], eng["ttl_minutes"], eng["credit_radius"]), (3, 30, 48))
        self.assertEqual(self.data["choices"]["balance"]["dark_cap"], 5)

    def test_unknown_faction_fails(self):
        msg = self.broken(lambda ch: self.route(ch, "sick_village", "heal")["costs"]["rep"].update({"atlantis": 3}))
        self.assertIn("unknown faction", msg)

    def test_dark_route_without_karma_fails(self):
        msg = self.broken(lambda ch: self.route(ch, "sick_village", "release")["costs"].pop("chaos"))
        self.assertIn("R13", msg)

    def test_light_deed_on_a_dark_route_fails(self):
        msg = self.broken(lambda ch: self.route(ch, "wants_name", "slay")["costs"].update({"balance": "light_deed"}))
        self.assertIn("R13", msg)

    def test_chaos_on_a_good_route_fails(self):
        msg = self.broken(lambda ch: self.route(ch, "starving_band", "feed")["costs"].update({"chaos": 1}))
        self.assertIn("only a dark route", msg)

    def test_need_on_a_deed_fails(self):
        msg = self.broken(lambda ch: self.route(ch, "starving_band", "feed").update({"need": ["necro"]}))
        self.assertIn("menu routes only", msg)

    def test_scene_without_an_honest_route_fails(self):
        def only_dark(ch):
            row = next(c for c in ch["choice"] if c["id"] == "wants_name")
            row["route"] = [r for r in row["route"] if r["road"] == "dark"]
            row["fair"] = "bind"
        self.assertIn("R13", self.broken(only_dark))

    def test_unknown_milestone_weight_fails(self):
        msg = self.broken(lambda ch: next(c for c in ch["choice"] if c["id"] == "starving_band")["weight_if"]["milestone"].update({"no_such": 2}))
        self.assertIn("milestone", msg)


if __name__ == "__main__":
    unittest.main()
