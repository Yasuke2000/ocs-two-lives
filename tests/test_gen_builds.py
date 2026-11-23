"""Offline tests for the canon-build part of tools/gen_data.py (no server): python -I -m unittest discover -s tests"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402


class BuildDataTests(unittest.TestCase):
    def test_landmarks_carry_the_anchor_coordinates(self):
        canon = json.loads(gen_data.CANON.read_text(encoding="utf-8"))
        # Tempest's canon landmark stands at its anchor (design/data/anchors.toml; build.py --apply moves them together).
        at = next(lm["at"] for lm in canon["landmarks"] if lm["name"].startswith("Tempest"))
        t = gen_data.anchor_table()["tempest"]
        self.assertEqual(gen_data.landmark_world(at), (t["x"], t["z"]))

    def test_footprint_of_the_test_hut(self):
        fp = gen_data.read_footprint(gen_data.structure_files("test_hut"))
        self.assertEqual(fp["size"], [5, 6, 5])
        self.assertEqual(fp["slabs"], ["ttl:test_hut"])
        self.assertEqual(fp["fill"], [0, 25])  # every column starts at the floor layer
        self.assertEqual(fp["top"], [5, 25])  # and ends at the roof layer 4 (layer 5 is explicit air)

    def test_rle_round_trip(self):
        self.assertEqual(gen_data.rle([3, 3, 3, -999, 3]), [3, 3, -999, 1, 3, 1])

    def test_builds_are_validated(self):
        builds, footprints = gen_data.check_builds()
        names = [b["name"] for b in builds]
        self.assertIn("test_hut", names)
        self.assertEqual(sorted(footprints), sorted(names))
        for b in builds:
            self.assertTrue(all(0 <= a < s for a, s in zip(b["anchor"], b["size"])))


if __name__ == "__main__":
    unittest.main()
