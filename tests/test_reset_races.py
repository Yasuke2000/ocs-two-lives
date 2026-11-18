"""Issues #4 and #12: python -I -m unittest discover -s tests

#4: the Character/Race Reset Scroll offers `Races.startingRaces` (the first-login menu is blocked by ttl-portals), so it
must hold the normal races of reincarnationRaces (Human included) and none of the Mastered/Legend-tier ones.
#12: no wall-climbing mob may sit in a Trial of the Soul pool (they walk up the arena walls and the barrier cage).
"""
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIMBERS = {"minecraft:spider", "minecraft:cave_spider", "tensura:black_spider"}


def races() -> dict:
    with (ROOT / "pack" / "config" / "tensura" / "reincarnation_config.toml").open("rb") as f:
        return tomllib.load(f)["Races"]


class ResetRaces(unittest.TestCase):
    def test_scroll_offers_the_normal_races(self):
        r = races()
        self.assertIn("tensura:human", r["startingRaces"])
        self.assertGreater(len(r["startingRaces"]), 1)
        self.assertEqual(sorted(r["startingRaces"]), sorted(r["reincarnationRaces"]))
        self.assertEqual(sorted(r["randomRaces"]), sorted(r["reincarnationRandomRaces"]))

    def test_no_legend_tier_race_in_the_scroll(self):
        r = races()
        mastered_only = set(r["reincarnationRacesMastered"]) - set(r["reincarnationRaces"])
        self.assertTrue(mastered_only, "expected Mastered-only races to exist")
        self.assertFalse(mastered_only & set(r["startingRaces"]))
        self.assertFalse(mastered_only & set(r["randomRaces"]))


class TrialPools(unittest.TestCase):
    def test_no_wall_climbers(self):
        with (ROOT / "design" / "data" / "trials.toml").open("rb") as f:
            trials = tomllib.load(f)
        ids = set()
        for wish, t in trials.items():
            for wave in t.get("waves", []):
                ids.update(g[0] for g in wave)
            for key in ("raider", "heavy", "fallback"):
                if key in t:
                    ids.add(t[key])
            ids.update(t.get("duelists", []))
        self.assertTrue(ids)
        self.assertFalse(ids & CLIMBERS, f"wall-climbers in a trial pool: {ids & CLIMBERS}")
        self.assertNotIn("spiders", trials["hunger"])


if __name__ == "__main__":
    unittest.main()
