"""Canon sites (pack/config/ttl/canon_regions.json "sites"): python -I -m unittest discover -s tests

Every canon build and landmark in the Tensura overworld has a site that matches its spot and is big enough for its
box, so a world reset generates the biome and terrain its style and lore ask for (design/decisions.md, 19/11/2026:
Dwargon stands on a plain). The mod side (weights, flat ground, byte-identical outside) is checked by the CanonGrid
self-check (docs/server.md "Site biomes").
"""
import json
import math
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
GENERATED = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated"
LIFE = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "life"

TERRAINS = {"keep", "flat", "lowland", "hills", "mountain"}
# Minecraft 1.21.1 surface biomes of the overworld preset, plus the Tensura 2.0.1.5 overworld biomes (jar data/tensura/worldgen/biome).
KNOWN_BIOMES = {"minecraft:" + b for b in (
    "plains sunflower_plains snowy_plains ice_spikes desert swamp mangrove_swamp forest flower_forest birch_forest dark_forest "
    "old_growth_birch_forest old_growth_pine_taiga old_growth_spruce_taiga taiga snowy_taiga savanna savanna_plateau "
    "windswept_hills windswept_gravelly_hills windswept_forest windswept_savanna jungle sparse_jungle bamboo_jungle badlands "
    "eroded_badlands wooded_badlands meadow cherry_grove grove snowy_slopes frozen_peaks jagged_peaks stony_peaks").split()} | {
    "tensura:ancient_forest", "tensura:barren_land", "tensura:desert_of_death", "tensura:miasmic_plains"}


def need(size_x, size_z, ax, az, margin):
    """Farthest corner of a box (plus its terrain margin) from the anchor that lands on the spot."""
    return max(math.hypot(dx, dz) for dx in (-ax, size_x - 1 - ax) for dz in (-az, size_z - 1 - az)) + margin


def footprint(name, var):
    text = (GENERATED / name).read_text(encoding="utf-8")
    return json.JSONDecoder().raw_decode(text[text.index("{", text.index(var)):])[0]


class CanonSites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canon = json.loads(CANON.read_text(encoding="utf-8"))
        cls.sites = {s["name"]: s for s in cls.canon.get("sites", [])}
        text = (GENERATED / "data.js").read_text(encoding="utf-8")
        cls.data = json.loads(re.search(r"=\s*(\{.*\})\s*;?\s*$", text, re.S).group(1))
        cls.landmarks = tomllib.loads((ROOT / "design" / "data" / "landmarks.toml").read_text(encoding="utf-8"))["landmark"]

    def spot(self, centre):
        return tuple(round(c) for c in centre)

    def covers(self, site, spot, radius_needed, what):
        self.assertEqual(self.spot(site["centre"]), tuple(spot), f"{what}: the site centre is the survey spot")
        self.assertGreaterEqual(site["radius"], math.ceil(radius_needed), f"{what}: radius covers the box + margin")

    def test_shape(self):
        self.assertEqual(len(self.sites), len(self.canon["sites"]), "site names are unique")
        for s in self.canon["sites"]:
            with self.subTest(site=s["name"]):
                self.assertRegex(s["name"], r"^[a-z0-9_]+$")
                self.assertIn(s["terrain"], TERRAINS)
                self.assertGreater(s["radius"], 0)
                self.assertGreaterEqual(s.get("fade", 0), 0)
                self.assertTrue(s.get("why"), "every site says why (lore or owner decision)")
                if s["terrain"] == "flat":
                    self.assertGreaterEqual(s.get("ground", 70), 64, "a flat site stays above sea level, or the sea floods it")
                else:
                    self.assertNotIn("ground", s, "ground only means something for flat sites")
                for biome, weight in s.get("biomes", []):
                    self.assertIn(biome, KNOWN_BIOMES)
                    self.assertGreater(weight, 0)
                self.assertTrue(s.get("biomes") or s["terrain"] != "keep", "a keep site without biomes does nothing")

    def test_every_overworld_build_has_a_site(self):
        for b in self.data["builds"]:
            if b["dimension"] != "minecraft:overworld":
                continue
            with self.subTest(build=b["name"]):
                self.assertIn(b["name"], self.sites, "add a site for the new build (docs/server.md, Site biomes)")
                s = self.sites[b["name"]]
                r = need(b["size"][0], b["size"][2], b["anchor"][0], b["anchor"][2], b["margin"])
                # Biome-only sites must also cover the survey's search radius: the build may land anywhere in it.
                self.covers(s, (b["x"], b["z"]), r if s["terrain"] == "flat" else r + min(b["search"], 64), b["name"])

    def test_every_landmark_has_a_site(self):
        refs = {lm["name"]: lm["ref"] for lm in self.canon["landmarks"]}
        scale = self.canon["width"] / 2570
        for lm in self.landmarks:
            with self.subTest(landmark=lm["name"]):
                self.assertIn(lm["name"], self.sites)
                if "x" in lm:
                    spot = (lm["x"], lm["z"])
                else:
                    ref = refs[lm["canon"]]
                    spot = (round((ref[0] - self.canon["origin"][0]) * scale), round((ref[1] - self.canon["origin"][1]) * scale))
                self.covers(self.sites[lm["name"]], spot, lm["reach"], lm["name"])

    def test_tempest_and_dwargon(self):
        tempest = re.search(r"LANDMARK:\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)", (LIFE / "tempest.js").read_text(encoding="utf-8"))
        gate = re.search(r"GATE:\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)", (LIFE / "dwargon.js").read_text(encoding="utf-8"))
        for name, m, fp, var in (("tempest", tempest, "tempest_footprint.js", "TtlTempestFootprint"),
                                 ("dwargon", gate, "dwargon_footprint.js", "TtlDwargonFootprint")):
            with self.subTest(settlement=name):
                f = footprint(fp, var)
                s = self.sites[name]
                self.assertEqual(s["terrain"], "flat")
                self.covers(s, (int(m.group(1)), int(m.group(2))), need(f["size"][0], f["size"][2], f["arrival"][0], f["arrival"][2], f["margin"]), name)
        self.assertNotIn("biomes", self.sites["tempest"], "Tempest keeps Jura's rings (owner decision: the deadly core stays)")

    def test_owner_override_dwargon_on_a_plain(self):
        dwargon = self.sites["dwargon"]
        self.assertEqual(dwargon["terrain"], "flat")
        self.assertEqual(dwargon["biomes"], [["minecraft:plains", 1]])
        plain = self.sites["dwargon_plain"]
        self.assertEqual(plain["terrain"], "lowland")
        self.assertTrue(all(b in ("minecraft:plains", "minecraft:meadow") for b, _ in plain["biomes"]))
        names = list(self.sites)
        self.assertLess(names.index("dwargon"), names.index("dwargon_plain"), "the city's own site comes first (biome priority)")
        palette = {b for b, _ in self.canon["regions"]["D"]["biomes"]}
        self.assertNotIn("minecraft:snowy_slopes", palette, "no snowy slopes in Dwargon's low land palette (peaks stay vanilla)")


if __name__ == "__main__":
    unittest.main()
