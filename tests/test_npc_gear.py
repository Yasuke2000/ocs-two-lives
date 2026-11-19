"""NPC weapons and fighting behaviour (design/data/npc_gear.toml): python -I -m unittest discover -s tests -p test_npc_gear.py

The role table is valid, every generic NPC has a role, the presets carry exactly the role's items with drop chance 0 and
the role's objectives, fighters and guards hold a weapon, civilians flee, no NPC is ever told to attack players, and every
Tempest resident maps to a role. The in-game half is tests/ingame/npc_defend.rcon.
"""
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_npcs  # noqa: E402
import npc_gear_check  # noqa: E402

GEAR = npc_gear_check.load()
ROLES = npc_gear_check.roles(GEAR)
SIDE = tomllib.loads((ROOT / "design" / "data" / "sidequests.toml").read_text(encoding="utf-8"))
EXTRAS = (ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "tempest_extras.js").read_text(encoding="utf-8")


class NpcGear(unittest.TestCase):
    def test_table_is_valid(self):
        npc_gear_check.check_npc_gear(GEAR)

    def test_refuses_player_attacks_and_bad_roles(self):
        bad = tomllib.loads(npc_gear_check.SOURCE.read_text(encoding="utf-8"))
        bad["ai"]["guard"]["easy_npc"] = bad["ai"]["guard"]["easy_npc"] + ["ATTACK_PLAYER"]
        with self.assertRaises(SystemExit):
            npc_gear_check.check_npc_gear(bad)
        bad = tomllib.loads(npc_gear_check.SOURCE.read_text(encoding="utf-8"))
        bad["role"].append({"id": "unarmed_guard", "ai": "guard"})
        with self.assertRaises(SystemExit):
            npc_gear_check.check_npc_gear(bad)

    def test_ai_meaning(self):
        for name in ("guard", "fighter"):
            objs = GEAR["ai"][name]["easy_npc"]
            self.assertIn("MELEE_ATTACK", objs)
            self.assertIn("HURT_BY_TARGET", objs)
            self.assertIn("ATTACK_MOB_WITHOUT_CREEPER", objs)
        self.assertIn("FLEE_MONSTER", GEAR["ai"]["civilian"]["easy_npc"])
        for a in GEAR["ai"].values():
            self.assertFalse(any("PLAYER" in o and "OWNER" not in o for o in a["easy_npc"]))

    def test_role_mapping(self):
        want = {
            ("adventurer", "rookie_swordsman"): ("minecraft:stone_sword", "", "fighter"),
            ("adventurer", "veteran_knight"): ("minecraft:iron_sword", "minecraft:shield", "fighter"),
            ("adventurer", "dwarf_axe"): ("minecraft:iron_axe", "", "fighter"),
            ("adventurer", "hunter"): ("tensura:iron_spear", "", "fighter"),
            ("adventurer", "merchant"): ("", "", "civilian"),
            ("adventurer", "bard"): ("", "", "civilian"),
            ("client", "merchant"): ("", "", "civilian"),
            ("client", "scholar"): ("", "", "civilian"),
        }
        rows = {(t, k["id"]): k for t in ("adventurer", "client") for k in SIDE[t]}
        for key, (main, off, ai) in want.items():
            r = ROLES[rows[key]["role"]]
            self.assertEqual((r.get("main", ""), r.get("off", ""), r["ai"]), (main, off, ai), key)
        tempest = GEAR["residents"]["tempest"]
        self.assertEqual(ROLES[tempest["goblin"]]["ai"], "guard")
        self.assertTrue(ROLES[tempest["goblin"]]["main"].startswith("tensura:"))
        self.assertEqual(ROLES[tempest["rigur"]].get("off"), "minecraft:shield")
        self.assertEqual(ROLES[tempest["haruna"]]["ai"], "none")

    def test_every_side_npc_has_a_role_and_its_preset_carries_it(self):
        files = gen_npcs.render_side()
        rows = [("ttl_adv_", "adventurer", k) for k in SIDE["adventurer"]] + [("ttl_client_", "client", k) for k in SIDE["client"]]
        rows += [("ttl_comp_", "companion", k) for k in SIDE["adventurer"] if k.get("hire")]
        for prefix, table, k in rows:
            self.assertIn(k.get("role"), ROLES, f"{table} {k['id']}")
            role = ROLES[k["role"]]
            text = files[gen_npcs.TARGET / f"{prefix}{k['id']}.npc.snbt"]
            self.assertIn("HandDropChances:[0.0f,0.0f]", text, k["id"])
            self.assertIn("ArmorDropChances:[0.0f,0.0f,0.0f,0.0f]", text, k["id"])
            hands = re.search(r"HandItems:\[(.*?)\n    \]", text, re.S).group(1)
            for slot in ("main", "off"):
                if role.get(slot):
                    self.assertIn(f'id:"{role[slot]}"', hands, f"{k['id']} {slot}")
            self.assertEqual(hands.count("id:"), sum(1 for s in ("main", "off") if role.get(s)), k["id"])
            types = re.findall(r'Type:"([A-Z_]+)"', text.split("ObjectiveData:")[1])
            self.assertNotIn("ATTACK_PLAYER", types)
            if table != "companion":
                for o in GEAR["ai"][role["ai"]]["easy_npc"]:
                    self.assertIn(o, types, f"{k['id']}: {o}")
            if role["ai"] in ("guard", "fighter"):
                self.assertTrue(role.get("main"), f"{k['id']}: a fighter is armed")

    def test_every_tempest_resident_has_a_role(self):
        tempest = GEAR["residents"]["tempest"]
        names = re.findall(r'\[-?\d+,-?\d+,-?\d+,"([^"]*)","[a-z_]+"\]', EXTRAS)
        self.assertTrue(names)
        for n in names:
            self.assertIn(tempest.get(n.lower()) or tempest["goblin"], ROLES, n)
        for named in ("Rigurd", "Rigur", "Gobta", "Haruna"):
            self.assertIn(named, names)
            self.assertIn(named.lower(), tempest)


if __name__ == "__main__":
    unittest.main()
