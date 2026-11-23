"""Offline tests for gen_data.check_domains (design/data/factions.toml domains/thrones, WP-W3): python -I -m unittest discover -s tests"""
import contextlib
import copy
import io
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import anchor_refs  # noqa: E402
import gen_data  # noqa: E402


def load() -> tuple[dict, list]:
    data = {}
    for name in ("factions", "world", "bosses", "npcs", "landmarks", "arrival", "karma"):
        with (gen_data.SOURCES / f"{name}.toml").open("rb") as f:
            data[name] = tomllib.load(f)
    with contextlib.redirect_stderr(io.StringIO()):
        gen_data.check_landmarks(data["landmarks"])
        builds, _ = gen_data.check_builds()
    return data, builds


class DomainDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.builds = load()

    def run_check(self, fac, data=None):
        with contextlib.redirect_stderr(io.StringIO()):
            gen_data.check_domains(fac, data or self.data, self.builds)

    def bad(self, mutate, world=None):
        fac = copy.deepcopy(self.data["factions"])
        data = dict(self.data)
        if world is not None:
            data["world"] = world
        mutate(fac)
        with self.assertRaises(SystemExit):
            self.run_check(fac, data)

    def faction(self, fac, fid):
        return next(f for f in fac["faction"] if f["id"] == fid)

    def test_shipped_domains_are_valid_and_centred(self):
        fac = copy.deepcopy(self.data["factions"])
        self.run_check(fac)
        # The centres follow design/data/anchors.toml: Tempest's square sits 12 north of its arrival point (the growth
        # square's middle), Eurazania's on Laura.
        a = anchor_refs.table()
        self.assertEqual(self.faction(fac, "tempest")["domain"]["center"], [a["tempest"]["x"], a["tempest"]["z"] - 12])
        self.assertEqual(self.faction(fac, "eurazania")["domain"]["center"], [a["laura"]["x"], a["laura"]["z"]])

    def test_eurazania_is_a_faction_and_no_longer_pending(self):
        eur = self.faction(self.data["factions"], "eurazania")
        self.assertEqual(eur["region"], "B")
        self.assertEqual(eur["throne"]["boss"], "carrion")
        self.assertNotIn("eurazania", self.data["world"]["chronicle"]["pending_factions"])
        with contextlib.redirect_stderr(io.StringIO()):
            gen_data.check_factions(self.data["factions"], self.data["karma"])

    def test_tempest_is_vassal_only(self):
        self.assertEqual(self.faction(self.data["factions"], "tempest")["throne"]["roads"], ["vassal"])

    def test_unknown_or_shared_build_is_refused(self):
        self.bad(lambda f: self.faction(f, "blumund")["domain"]["builds"].append("atlantis"))
        self.bad(lambda f: self.faction(f, "blumund")["domain"]["builds"].append("dwargon"))
        self.bad(lambda f: self.faction(f, "falmuth")["domain"].update(landmarks=["no_such_place"]))

    def test_capital_and_throne_references(self):
        self.bad(lambda f: self.faction(f, "falmuth")["domain"].update(capital="build:nowhere"))
        self.bad(lambda f: self.faction(f, "falmuth")["domain"].update(capital="castle"))
        self.bad(lambda f: self.faction(f, "dwargon")["throne"].update(boss="gazel"))
        self.bad(lambda f: self.faction(f, "dwargon")["throne"].update(statue="no_statue"))
        self.bad(lambda f: self.faction(f, "dwargon")["throne"].update(seat="blumund"))
        self.bad(lambda f: self.faction(f, "tempest")["throne"].update(roads=["emperor"]))

    def test_knobs(self):
        self.bad(lambda f: f["domains"].update(member_edit="some"))
        self.bad(lambda f: f["domains"].update(invulnerable="everyone"))
        self.bad(lambda f: f["domains"].update(capital_radius=5))
        self.bad(lambda f: f["domains"].update(unowned_skip=["atlantis"]))
        self.bad(lambda f: f["domains"].update(teleport=True))
        self.bad(lambda f: self.faction(f, "tempest").update(territory="everything"))

    def test_the_life2_arrival_stays_free(self):
        # The arrival lies on the way from Tempest to Dwargon's gate: a Dwargon capital square just large enough to
        # reach it must fail.
        a = anchor_refs.table()
        reach = max(abs(a["arrival"]["x"] - a["dwargon"]["x"]), abs(a["arrival"]["z"] - a["dwargon"]["z"])) + 16
        self.bad(lambda f: self.faction(f, "dwargon")["domain"].update(capital_radius=reach))

    def test_boss_area_stays_outside(self):
        world = copy.deepcopy(self.data["world"])
        world["continent"]["inside_dimensions"].append("tensura:boss_area")
        self.bad(lambda f: None, world)


if __name__ == "__main__":
    unittest.main()
