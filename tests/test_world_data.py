"""Offline tests for gen_data.check_world (design/data/world.toml, WP-W1): python -I -m unittest discover -s tests"""
import copy
import contextlib
import io
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402


def load() -> dict:
    data = {}
    for name in ("world", "story", "bosses", "factions", "events"):
        with (gen_data.SOURCES / f"{name}.toml").open("rb") as f:
            data[name] = tomllib.load(f)
    return data


class WorldDataTests(unittest.TestCase):
    def setUp(self):
        self.data = load()

    def check(self, world):
        with contextlib.redirect_stderr(io.StringIO()):
            gen_data.check_world(world, self.data)

    def bad(self, mutate):
        world = copy.deepcopy(self.data["world"])
        mutate(world)
        with self.assertRaises(SystemExit):
            self.check(world)

    def milestone(self, world, mid):
        return next(m for m in world["milestone"] if m["id"] == mid)

    def test_shipped_world_is_valid(self):
        self.check(self.data["world"])

    def test_threshold_is_the_owner_decision(self):
        self.assertEqual(self.data["world"]["threshold"], {"souls": 3, "pct": 25})

    def test_unknown_flag_boss_or_phase_is_refused(self):
        self.bad(lambda w: self.milestone(w, "first_demon_lord")["when"].update(flags={"demonlord": 1}))
        self.bad(lambda w: self.milestone(w, "walpurgis_held")["when"].update(kills={"klayman": 1}))
        self.bad(lambda w: self.milestone(w, "tempest_town")["effects"].update(phase={"tempest": "metropolis"}))
        self.bad(lambda w: self.milestone(w, "act2_reached")["when"].update(acts={"act": 9}))

    def test_effects_are_additive_world_stages_and_known_factions(self):
        self.bad(lambda w: self.milestone(w, "act2_reached")["effects"].update(stage="ttl.story.act2"))
        self.bad(lambda w: self.milestone(w, "dwargon_pact")["effects"].update(conflict="atlantis"))
        self.bad(lambda w: self.milestone(w, "first_true_hero")["effects"].update(mood={"holy_church": 0}))
        self.bad(lambda w: self.milestone(w, "act2_reached")["effects"].update(demolish="tempest"))

    def test_ids_and_tides(self):
        self.bad(lambda w: w["milestone"].append(copy.deepcopy(w["milestone"][0])))
        self.bad(lambda w: self.milestone(w, "act2_reached")["when"].update(milestone="act2_reached"))
        self.bad(lambda w: w["balance"].update(tide_end=30))
        self.bad(lambda w: w["tide"].pop("light"))

    def test_pending_faction_must_not_shadow_a_real_one(self):
        self.bad(lambda w: w["chronicle"]["pending_factions"].append("dwargon"))


if __name__ == "__main__":
    unittest.main()
