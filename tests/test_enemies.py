"""The enemies of the roads (design/data/enemies.toml): python -I -m unittest discover -s tests -p test_enemies.py

The data passes tools/enemies_check.py against the generated TtlData (domains, builds, landmarks, spawn zones, roads,
bounties); a camp in Tempest, near an anchor or across water, a loot table with the enemy's own weapon, an unknown ttl:
bounty target and a group named like an archetype are refused; every archetype has presets (the ones gen_npcs writes) that
are attackable by players, never invulnerable, drop nothing from their hands and point at their loot table; every loot
pool needs a kill by a soul. The friendly NPC presets stay unattackable. The in-game half is tests/ingame/enemies.rcon.
"""
import copy
import json
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import enemies_check  # noqa: E402
import anchor_refs  # noqa: E402
import gen_npcs  # noqa: E402

DATA_JS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "data.js"
DATA = json.loads(re.search(r"const TtlData = (\{.*\})\s*$", DATA_JS.read_text(encoding="utf-8"), re.S).group(1))
SOURCE = tomllib.loads((ROOT / "design" / "data" / "enemies.toml").read_text(encoding="utf-8"))


def fresh() -> dict:
    return copy.deepcopy(SOURCE)


def camp(en: dict, cid: str) -> dict:
    return next(c for c in en["camp"] if c["id"] == cid)


class Enemies(unittest.TestCase):
    def check(self, en: dict) -> None:
        enemies_check.check_enemies(en, DATA)

    def test_data_is_valid(self):
        self.check(fresh())

    def test_generated_presets_match(self):
        en = fresh()
        self.check(en)
        self.assertEqual(en["presets"], DATA["enemies"]["presets"])
        files = gen_npcs.render_enemies()
        for arch, names in en["presets"].items():
            for name in names:
                self.assertIn(gen_npcs.TARGET / f"{name}.npc.snbt", files)
            self.assertIn(gen_npcs.LOOT / f"enemy_{arch}.json", files)

    def test_camp_spots_are_refused(self):
        tempest = DATA["factions"]["faction"][0]["domain"]["center"]
        a = anchor_refs.table()
        box = json.loads((ROOT / "pack" / "config" / "ttl" / "world" / "index.json").read_text(encoding="utf-8"))["box"] \
            if (ROOT / "pack" / "config" / "ttl" / "world" / "index.json").is_file() else {"x0": -9000, "z0": -7000}
        for x, z, why in ((tempest[0], tempest[1] - 300, "domain or spawn zone"),
                          (a["arrival"]["x"] + 30, a["arrival"]["z"] + 40, "the arrival"),
                          (a["dwarf_village"]["x"] + 20, a["dwarf_village"]["z"] + 20, "the dwarf village"),
                          (box["x0"] + 200, box["z0"] + 200, "sea")):
            en = fresh()
            c = camp(en, "dwarven_road_south")
            c["x"], c["z"] = x, z
            with self.assertRaises(SystemExit, msg=why):
                self.check(en)

    def test_two_camps_too_close(self):
        en = fresh()
        c = camp(en, "dwarven_road_north")
        c["x"], c["z"] = camp(en, "dwarven_road_south")["x"] + 40, camp(en, "dwarven_road_south")["z"]
        with self.assertRaises(SystemExit):
            self.check(en)

    def test_gear_never_in_loot(self):
        en = fresh()
        a = en["archetype"][0]
        a["loot"].append({"item": a["main"], "min": 1, "max": 1, "chance": 1.0})
        with self.assertRaises(SystemExit):
            self.check(en)

    def test_bad_bounty_target_and_group(self):
        data = copy.deepcopy(DATA)
        data["economy"]["bounty"].append({"id": "x", "kind": "kill", "target": "ttl:goblin_raider"})
        with self.assertRaises(SystemExit):
            enemies_check.check_enemies(fresh(), data)
        en = fresh()
        en["group"]["bandit"] = {"title": "bandits"}
        with self.assertRaises(SystemExit):
            self.check(en)

    def test_bounties_target_known_enemies(self):
        targets = {a["id"] for a in SOURCE["archetype"]} | set(SOURCE["group"])
        enemy = [b for b in DATA["economy"]["bounty"] if str(b["target"]).startswith("ttl:")]
        self.assertGreaterEqual(len(enemy), 4)
        for b in enemy:
            self.assertIn(b["target"][4:], targets)
        self.assertTrue(any(b["target"] == "ttl:dwarven_road" for b in enemy))
        self.assertTrue(any(b.get("region") for b in DATA["economy"]["bounty"] if b["weight"] > 0), "a region-bound bounty")

    def test_presets_are_hostile_and_drop_nothing(self):
        for path, text in gen_npcs.render_enemies().items():
            if path.suffix == ".json":
                pools = json.loads(text)["pools"]
                self.assertTrue(pools)
                for pool in pools:
                    self.assertIn({"condition": "minecraft:killed_by_player"}, pool["conditions"])
                continue
            self.assertIn("IsAttackableByPlayers:1b", text)
            self.assertIn("Invulnerable:0b", text)
            self.assertIn("HandDropChances:[0.0f,0.0f]", text)
            self.assertIn('Type:"ATTACK_PLAYER"', text)
            self.assertRegex(text, r'DeathLootTable:"ttl:entities/enemy_[a-z_]+"')

    def test_friendly_presets_stay_unattackable(self):
        for path in gen_npcs.TARGET.glob("*.npc.snbt"):
            if path.name.startswith(("ttl_guild_", "ttl_cast_", "ttl_adv_")):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("IsAttackableByPlayers:1b", text, path.name)
                self.assertNotIn('Type:"ATTACK_PLAYER"', text, path.name)


if __name__ == "__main__":
    unittest.main()
