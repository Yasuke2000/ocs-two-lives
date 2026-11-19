"""WP-L4, data re-anchoring: every overworld position of the pack data follows design/data/anchors.toml
(python -I -m unittest discover -s tests)

Builds and landmarks take x/z from the anchor that names them, the flat records (arrival, NPC and side-quest world spots)
name an anchor with `at`, boss arenas and the artifice smithy with `anchor` (+ dx/dz); tools/anchor_refs.py resolves them
and gen_data writes the numbers into generated/data.js, and anchors.toml itself into generated/anchors.js (TtlAnchors,
read by life/tempest.js and life/mortal_spawns.js). Also: Lerfing's builds stay clear of every survey envelope, and the
Life 2 arrival is a hostile-spawn-free zone of 48 blocks (owner 19/11/2026).
"""
import json
import math
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import anchor_refs  # noqa: E402

DATA = ROOT / "design" / "data"
BUILDS = ROOT / "design" / "builds"
SCRIPTS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl"
GENERATED = SCRIPTS / "generated"


def load(name: str) -> dict:
    return tomllib.loads((DATA / f"{name}.toml").read_text(encoding="utf-8"))


def generated(name: str, const: str) -> dict:
    text = (GENERATED / name).read_text(encoding="utf-8")
    return json.loads(text[text.index(f"const {const} = ") + len(f"const {const} = "):])


def gap(box, k) -> float:
    return math.hypot(max(k["x0"] - box[2], 0, box[0] - k["x1"]), max(k["z0"] - box[3], 0, box[1] - k["z1"]))


class AnchorRefs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchors = anchor_refs.table()
        cls.keepouts = anchor_refs.keepouts()
        cls.data = generated("data.js", "TtlData")

    def test_generated_anchor_table(self):
        js = generated("anchors.js", "TtlAnchors")
        self.assertEqual({k: (v["x"], v["z"]) for k, v in js.items()},
                         {k: (a["x"], a["z"]) for k, a in self.anchors.items()})

    def test_overworld_builds_take_their_anchor(self):
        by_build = {a["build"]: a for a in self.anchors.values() if "build" in a}
        for b in self.data["builds"]:
            if b["dimension"] != "minecraft:overworld":
                continue
            with self.subTest(build=b["name"]):
                self.assertIn(b["name"], by_build)
                self.assertEqual((b["x"], b["z"]), (by_build[b["name"]]["x"], by_build[b["name"]]["z"]))
                src = tomllib.loads((BUILDS / f"{b['name']}.toml").read_text(encoding="utf-8"))
                self.assertNotIn("x", src, "the numbers live in anchors.toml")

    def test_landmarks_take_their_anchor(self):
        by_lm = {a["landmark"]: a for a in self.anchors.values() if "landmark" in a}
        src = {lm["name"]: lm for lm in load("landmarks")["landmark"]}
        for lm in self.data["landmarks"]["landmark"]:
            with self.subTest(landmark=lm["name"]):
                self.assertEqual((lm["x"], lm["z"]), (by_lm[lm["name"]]["x"], by_lm[lm["name"]]["z"]))
                self.assertNotIn("x", src[lm["name"]])

    def test_named_places_resolve(self):
        a = self.anchors
        life2 = self.data["arrival"]["life2"]
        self.assertEqual((life2["x"], life2["z"]), (a["arrival"]["x"], a["arrival"]["z"]))
        bosses = {b["id"]: b for b in self.data["bosses"]["boss"]}
        t = a["tempest"]
        for bid, key, want in (("shizu", "arena", (t["x"], t["z"])), ("rimuru_ogre_fight", "arena", (t["x"], t["z"])),
                               ("ifrit", "spawn", (t["x"], t["z"])), ("folgen", "spawn", (t["x"], t["z"] + 40)),
                               ("orc_disaster", "spawn", (a["orc_camp"]["x"], a["orc_camp"]["z"])),
                               ("charybdis", "spawn", (a["lake_siss"]["x"], a["lake_siss"]["z"])),
                               ("gazel_dwargo", "spawn", (a["dwargon_throne"]["x"], a["dwargon_throne"]["z"])),
                               ("hinata_sakaguchi", "spawn", (a["shizu_spawn"]["x"], a["shizu_spawn"]["z"]))):
            with self.subTest(boss=bid):
                place = bosses[bid]["arena"] if key == "arena" else bosses[bid]["spawn"]["at"]
                self.assertEqual((place["x"], place["z"]), want)
        smithy = self.data["artifice"]["steal"]["smithy"]
        self.assertEqual((smithy["x"], smithy["z"]), (a["kaijin_smithy"]["x"], a["kaijin_smithy"]["z"]))
        outcast = next(s for s in self.data["npcs"]["spot"] if s["id"] == "outcast_road")
        self.assertEqual((outcast["x"], outcast["z"]), (a["outcast_road"]["x"], a["outcast_road"]["z"]))
        for p in self.data["sidequests"]["place"]:
            if p["anchor"] == "world":
                with self.subTest(place=p["id"]):
                    self.assertEqual((p["x"], p["z"]), (a[p["at"]]["x"], a[p["at"]]["z"]))

    def test_no_old_overworld_numbers_in_the_data(self):
        # Every overworld x/z of these files names an anchor now; a literal world position would not follow a move.
        for name in ("arrival", "bosses", "artifice"):
            text = (DATA / f"{name}.toml").read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIsNone(re.search(r"^[^#\n]*\{[^}#\n]*\bx = -?\d+[^}\n]*\bz = -?\d+", text, re.M))
        life2 = load("arrival")["life2"]
        self.assertNotIn("x", life2)

    def test_tempest_reads_its_anchor(self):
        text = (SCRIPTS / "life" / "tempest.js").read_text(encoding="utf-8")
        m = re.search(r"LANDMARK: typeof TtlAnchors !== 'undefined' && TtlAnchors\.tempest \? .*: \{ x: (-?\d+), z: (-?\d+) \}", text)
        self.assertIsNotNone(m, "LANDMARK reads TtlAnchors.tempest")
        self.assertEqual((int(m[1]), int(m[2])), (self.anchors["tempest"]["x"], self.anchors["tempest"]["z"]),
                         "the fallback literal is the anchor")

    def test_builds_and_landmarks_keep_off_lerfings_builds(self):
        # Wherever the survey puts a build (search) or the landmark placer a landmark (64 blocks, then its reach).
        sizes = {k: v["size"] for k, v in generated("builds.js", "TtlBuildFootprints").items()}
        for b in self.data["builds"]:
            if b["dimension"] != "minecraft:overworld":
                continue
            ax, _, az = b["anchor"]
            sx, _, sz = sizes[b["name"]]
            r = max(b["margin"], b["repair_margin"]) + b["search"]
            box = (b["x"] - ax - r, b["z"] - az - r, b["x"] - ax + sx - 1 + r, b["z"] - az + sz - 1 + r)
            for k in self.keepouts:
                with self.subTest(build=b["name"], keepout=k["id"]):
                    self.assertGreater(gap(box, k), 0)
        for lm in self.data["landmarks"]["landmark"]:
            r = lm["reach"] + 64
            for k in self.keepouts:
                with self.subTest(landmark=lm["name"], keepout=k["id"]):
                    self.assertGreater(gap((lm["x"] - r, lm["z"] - r, lm["x"] + r, lm["z"] + r), k), 0)

    def test_lizardmen_village_on_the_lake_clear_of_lerfings_huts(self):
        lv = self.anchors["lizardmen_village"]
        huts = [k for k in self.keepouts if k["id"].startswith("lerfing_lake_village")]
        self.assertEqual(len(huts), 9)
        self.assertGreater(min(gap((lv["x"], lv["z"], lv["x"], lv["z"]), k) for k in huts), 48 + 64)
        self.assertLess(math.hypot(lv["x"] - self.anchors["lake_siss"]["x"], lv["z"] - self.anchors["lake_siss"]["z"]), 400)


class ArrivalSafeZone(unittest.TestCase):
    """Owner 19/11/2026: no hostile mob spawns within 48 blocks of the Life 2 arrival, like Tempest and Wayfarer's Rest."""

    def test_data(self):
        life2 = generated("data.js", "TtlData")["arrival"]["life2"]
        a = anchor_refs.table()["arrival"]
        self.assertEqual(life2["safe_radius"], 48)
        self.assertEqual((life2["x"], life2["z"]), (a["x"], a["z"]), "centred on the arrival anchor")

    def test_same_mechanism_as_tempest(self):
        text = (SCRIPTS / "life" / "mortal_spawns.js").read_text(encoding="utf-8")
        zones = text[text.index("ZONES:"):text.index("hostile(entity)")]
        self.assertIn("TtlAnchors.tempest", zones)
        self.assertIn("TtlData.arrival.life2", zones)
        self.assertRegex(zones, r"radius: a\.safe_radius")
        self.assertIn("{ dim: 'ttl:mortal_realm', x: 0, z: 0, radius: 48 }", zones, "Wayfarer's Rest unchanged")

    def test_zone_is_open_rim_ground(self):
        # The zone must not swallow a canon place: nothing of ours is placed within it (the rim stays free ground).
        life2 = generated("data.js", "TtlData")["arrival"]["life2"]
        for a in anchor_refs.table().values():
            if a["id"] in ("arrival", "wayfarers_camp") or a["kind"] in ("pin",):
                continue
            with self.subTest(anchor=a["id"]):
                self.assertGreater(math.hypot(a["x"] - life2["x"], a["z"] - life2["z"]), life2["safe_radius"])


if __name__ == "__main__":
    unittest.main()
