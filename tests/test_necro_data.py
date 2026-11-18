"""necro.toml checks (WP-N2): python -I -m unittest discover -s tests

tools/gen_data.py check_necro guards what necro/legion.js and necro/sanctum.js read by name: the O-N3 caps, the O-N4 ash
scope, the O-N6 knights, and the tiers of the player-built tomb.
"""
import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402


def load(name: str) -> dict:
    with (ROOT / "design" / "data" / f"{name}.toml").open("rb") as f:
        return tomllib.load(f)


class NecroDataTests(unittest.TestCase):
    def setUp(self):
        self.necro = load("necro")
        self.roads = load("roads")

    def fails(self, mutate) -> None:
        n = copy.deepcopy(self.necro)
        mutate(n)
        with self.assertRaises(SystemExit):
            gen_data.check_necro(n, self.roads)

    def test_shipped_data_passes(self):
        gen_data.check_necro(self.necro, self.roads)

    def test_owner_values(self):
        lg = self.necro["legion"]
        self.assertEqual(lg["caps"], [0, 2, 4, 6, 8])          # O-N3
        self.assertEqual(lg["muster_caps"][4], 10)
        self.assertEqual(lg["server_cap"], 60)
        self.assertEqual(self.necro["knight"]["max"], [0, 0, 0, 1, 2])   # O-N6
        self.assertEqual(self.necro["knight"]["dust_cost"], 32)
        self.assertEqual(self.necro["ash"]["victim_hours"], 24)          # O-N4
        self.assertEqual(sorted(self.necro["ash"]["player_scope"]), ["arena", "war"])
        self.assertEqual([t["id"] for t in self.necro["sanctum"]["tier"]], ["crypt", "mausoleum", "great_tomb"])

    def test_bad_values_fail(self):
        self.fails(lambda n: n["legion"].update(caps=[0, 4, 2, 6, 8]))
        self.fails(lambda n: n["legion"].update(muster_caps=[0, 2, 4, 6, 6]))
        self.fails(lambda n: n["legion"].update(caps=[0, 2, 4, 6, 8, 9]))
        self.fails(lambda n: n["legion"].update(kinds={"skeleton": "minecraft:skeleton"}))
        self.fails(lambda n: n["ash"].update(player_scope=["arena", "anywhere"]))
        self.fails(lambda n: n["ash"].update(ash_chance=1.5))
        self.fails(lambda n: n["knight"].update(title="Death Knight"))
        self.fails(lambda n: n["sanctum"]["tier"][1].update(min_air=10))
        self.fails(lambda n: n["sanctum"]["tier"][0]["need"][0].update(match=["Not An Id"]))
        self.fails(lambda n: n["sanctum"]["tier"][2].update(niches=99))
        self.fails(lambda n: n.pop("sanctum"))

    def test_roads_must_know_the_acts(self):
        roads = copy.deepcopy(self.roads)
        roads["choice"] = [c for c in roads["choice"] if c["id"] != "necro.knight"]
        with self.assertRaises(SystemExit):
            gen_data.check_necro(self.necro, roads)


if __name__ == "__main__":
    unittest.main()
