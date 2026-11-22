"""L2Hostility levels in the Life 1 dimensions (pack/kubejs/data/l2hostility/l2hostility_config/difficulty/
ttl_two_lives.json, issue #144). The caps were 40/50/60, which left only L2H's six cheapest traits (min level 20) and
almost none of its trait drops; they are 100/150/200 now. Kept on purpose: no leveling in the Spirit Corridor (the
trials' balance), half the per-level damage bonus in Life 1, and no cap at all in the Tensura world."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIFF = json.loads((ROOT / "pack" / "kubejs" / "data" / "l2hostility" / "l2hostility_config" / "difficulty"
                   / "ttl_two_lives.json").read_text(encoding="utf-8"))


class L2HDifficulty(unittest.TestCase):
    def cap(self, dim):
        (entry,) = DIFF["levelDefaultTraits"][dim]
        return entry

    def test_life_one_caps(self):
        self.assertEqual({d: self.cap(d)["maxLevel"] for d in ("ttl:mortal_realm", "ttl:mortal_nether", "ttl:mortal_end")},
                         {"ttl:mortal_realm": 100, "ttl:mortal_nether": 150, "ttl:mortal_end": 200})
        self.assertEqual([self.cap(d)["maxTraitCount"] for d in ("ttl:mortal_realm", "ttl:mortal_nether", "ttl:mortal_end")],
                         [3, 4, 4])

    def test_life_one_still_gentle(self):
        for d in ("ttl:mortal_realm", "ttl:mortal_nether", "ttl:mortal_end"):
            self.assertEqual(self.cap(d)["attackScale"], 0.5, d)
        self.assertEqual(DIFF["levelMap"]["ttl:mortal_realm"]["base"], 0)

    def test_corridor_untouched(self):
        self.assertEqual(self.cap("ttl:spirit_corridor")["maxLevel"], 1)
        self.assertEqual(DIFF["levelMap"]["ttl:spirit_corridor"]["apply_chance"], 0.0)

    def test_tensura_world_uncapped(self):
        self.assertNotIn("minecraft:overworld", DIFF["levelDefaultTraits"])


if __name__ == "__main__":
    unittest.main()
