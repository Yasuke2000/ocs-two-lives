"""Dwargon's mountain shell wears Lerfing's Canaat surface (WP-L7a, TTL_DWARGON_VERSION 7): python -I -m unittest discover -s tests

No sandstone strata, no grass and no moss in the built structure (the city interior is unchanged), and the patch noise
hands each Canaat block out in the measured proportions (blueprints/dwargon.py CANAAT_FLAT / CANAAT_SLOPE).
"""
import collections
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "blueprints"))
import dwargon  # noqa: E402
import verify_build as vb  # noqa: E402


class DwargonPaletteTests(unittest.TestCase):
    def test_no_sandstone_or_meadow_in_the_structure(self):
        _, blocks, _ = vb.load_expected(vb.structure_files("dwargon"))
        names = collections.Counter(s.split("[")[0].split(":")[-1] for s in blocks.values())
        bad = {n: c for n, c in names.items()
               if re.search(r"sandstone|^(white_)?terracotta$|^(grass_block|moss_block|short_grass|dandelion|poppy)$", n)}
        self.assertEqual(bad, {})

    def test_patch_noise_keeps_the_measured_mix(self):
        for flat, mix in ((True, dwargon.CANAAT_FLAT), (False, dwargon.CANAAT_SLOPE)):
            got = collections.Counter(dwargon.canaat_pick(x, z, flat) for x in range(dwargon.SX) for z in range(dwargon.SZ))
            total, want_total = sum(got.values()), sum(w for _, w in mix)
            for name, w in mix:
                self.assertAlmostEqual(100 * got[name] / total, 100 * w / want_total, delta=0.6, msg=name)


if __name__ == "__main__":
    unittest.main()
