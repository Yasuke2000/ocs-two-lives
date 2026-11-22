"""Life 1 tester issues #85 and #104: python -I -m unittest discover -s tests

#104: the Tensura bridge (tensura_iron_spells) pays Iron's spells from magicules at manaConversionMultiplier x the cost. A
Life 1 Human cannot pay even the cheapest spell that way, so ttl-portals must keep its SpellManaMixin (Iron's own mana in
the Mortal dimensions) and Iron's must stay allowed in Life 1 apart from the vetoed schools (O-N1).
#85: vanilla lights a Nether portal frame only in the Overworld and the Nether; ttl-portals' BaseFireBlockMixin adds the
Mortal pair. The in-game halves are tests/ingame/life1_spells.rcon and tests/ingame/portals.rcon.
"""
import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIXINS = ROOT / "mod" / "src" / "main" / "java" / "com" / "yasuke" / "ttl" / "mixin"


def toml(*parts) -> dict:
    with ROOT.joinpath(*parts).open("rb") as f:
        return tomllib.load(f)


def mixin_config() -> dict:
    return json.loads((ROOT / "mod" / "src" / "main" / "resources" / "ttl.mixins.json").read_text(encoding="utf-8"))


class IronsSpellsInLife1(unittest.TestCase):
    def test_irons_is_not_banned_in_life1(self):
        banned = toml("design", "data", "mortal_banned.toml")
        self.assertNotIn("irons_spellbooks", banned["namespaces"])
        self.assertTrue(set(banned["spell_schools"]) <= {"irons_spellbooks:blood", "irons_spellbooks:eldritch"},
                        f"only blood and eldritch are vetoed in Life 1 (O-N1), got {banned['spell_schools']}")

    def test_a_human_cannot_pay_a_spell_in_magicules(self):
        # Why the mixin exists: with the bridge on, a Life 1 Human's magicules never cover even a 1-mana spell.
        mult = toml("pack", "config", "tensura", "iron_spell_config.toml")["manaConversionMultiplier"]
        human = toml("pack", "config", "tensura", "race", "human_config.toml")["Human"]
        if mult <= 0:
            self.skipTest("the bridge is off: Iron's spends its own mana everywhere")
        self.assertLess(human["maxMagicule"], mult * 2, "a Human could pay a 2-mana spell in magicules")
        self.assertIn("SpellManaMixin", mixin_config()["mixins"])
        self.assertIn("TensuraIronCastMixin", mixin_config()["mixins"])

    def test_spell_mana_mixin_wraps_the_bridge(self):
        src = (MIXINS / "SpellManaMixin.java").read_text(encoding="utf-8")
        # Above the bridge's default priority (1000), so this wrapper is applied last and wraps the bridge's.
        priority = int(re.search(r"priority\s*=\s*(\d+)", src).group(1))
        self.assertGreater(priority, 1000)
        self.assertIn('method = "canBeCastedBy"', src)
        self.assertIn("AbstractSpell;getManaCost(I)I", src)
        self.assertIn("TtlDimensions.isMortal", src)
        cast = (MIXINS / "TensuraIronCastMixin.java").read_text(encoding="utf-8")
        self.assertIn("io.github.manasmods.tensura_iron.neoforge.NeoEventsHandler", cast)
        self.assertIn('method = "onSpellCast"', cast)

    def test_ingame_test_covers_cast_and_bridge(self):
        rcon = (ROOT / "tests" / "ingame" / "life1_spells.rcon").read_text(encoding="utf-8")
        for line in ("cancast irons_spellbooks:firebolt yes", "cast irons_spellbooks:heal yes", "spent",
                     "spell irons_spellbooks:blood yes", "ttl:spirit_corridor"):
            self.assertIn(line, rcon)


class MortalPortals(unittest.TestCase):
    def test_fire_lights_frames_in_the_mortal_pair(self):
        self.assertIn("BaseFireBlockMixin", mixin_config()["mixins"])
        src = (MIXINS / "BaseFireBlockMixin.java").read_text(encoding="utf-8")
        self.assertIn('method = "inPortalDimension"', src)
        self.assertIn("netherPortalTarget", src)
        dims = (ROOT / "mod" / "src" / "main" / "java" / "com" / "yasuke" / "ttl" / "TtlDimensions.java").read_text(encoding="utf-8")
        self.assertIn("if (from.equals(MORTAL_REALM)) return MORTAL_NETHER;", dims)
        self.assertIn("if (from.equals(MORTAL_NETHER)) return MORTAL_REALM;", dims)

    def test_ingame_test_lights_with_flint_and_steel(self):
        rcon = (ROOT / "tests" / "ingame" / "portals.rcon").read_text(encoding="utf-8")
        self.assertIn("weapon.mainhand with minecraft:flint_and_steel", rcon)
        for dim in ("ttl:mortal_realm", "ttl:mortal_nether"):
            self.assertIn(f"execute in {dim} run tp TtlBotPortal", rcon)
        self.assertEqual(rcon.count("ttl useon expect TtlBotPortal"), 4)


if __name__ == "__main__":
    unittest.main()
