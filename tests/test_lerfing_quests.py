"""WP-L5 (Lerfing import): quest locations and player text follow design/data/anchors.toml, offline.

python -I -m unittest discover -s tests

Covers the anchor syntax of tools/gen_quests.py (`at = { anchor | landmark | build, dx, dz }` and the `${anchor:}`, `${dir:}`,
`${dist:}` text tokens), that no overworld location task of the real quest book repeats a coordinate, that every location task
sits on land or lake of the grid, and that the coordinate tables of the two wiki world maps (EN, NL) and the arrival figures of the
wiki and the guide book agree with anchors.toml."""
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_quests  # noqa: E402

QUESTS = sorted((ROOT / "design" / "quests").glob("chapter_*.toml"))
ANCHORS = gen_quests.anchors()
WIKI = {lang: (ROOT / "docs" / "wiki" / lang / "world-map.md").read_text(encoding="utf-8") for lang in ("en", "nl")}


def overworld_location_tasks():
    for src in QUESTS:
        data = tomllib.loads(src.read_text(encoding="utf-8"))
        for q in data.get("quests", []):
            for t in q.get("tasks", []):
                if t.get("type") == "location" and t.get("dimension") == "minecraft:overworld":
                    yield src.name, q["key"], t


class AnchorSyntax(unittest.TestCase):
    def test_anchor_landmark_build_and_offsets(self):
        t = ANCHORS["tempest"]
        self.assertEqual(gen_quests.resolve_at("t", {"anchor": "tempest"}), (t["x"], t["z"]))
        self.assertEqual(gen_quests.resolve_at("t", {"anchor": "tempest", "dx": 22, "dz": -39}), (t["x"] + 22, t["z"] - 39))
        o = ANCHORS["orc_camp"]
        self.assertEqual(gen_quests.resolve_at("t", {"landmark": "orc_camp"}), (o["x"], o["z"]))
        c = ANCHORS["sealed_cave"]
        self.assertEqual(gen_quests.resolve_at("t", {"build": "sealed_cave"}), (c["x"], c["z"]))
        self.assertEqual(gen_quests.resolve_at("t", [5, -7]), (5, -7))

    def test_bad_places_are_refused(self):
        for at in ({"anchor": "nowhere"}, {"landmark": "nowhere"}, {"build": "nowhere"}, {}, {"anchor": "tempest", "build": "sealed_cave"},
                   {"anchor": "tempest", "dy": 1}, "tempest"):
            with self.assertRaises(gen_quests.QuestError, msg=str(at)):
                gen_quests.resolve_at("t", at)

    def test_location_task_box(self):
        task, _ = gen_quests.build_task({"life": 2}, "t", {"type": "location", "dimension": "minecraft:overworld",
                                                           "at": {"anchor": "dwargon", "dz": -106}, "radius": 12}, "ID")
        g = ANCHORS["dwargon"]
        self.assertEqual(list(task["position"]), [g["x"] - 12, -64, g["z"] - 106 - 12])
        self.assertEqual(list(task["size"]), [25, 384, 25])


class TextTokens(unittest.TestCase):
    def test_tokens(self):
        t, d = ANCHORS["tempest"], ANCHORS["dwargon"]
        self.assertEqual(gen_quests.expand("t", "x ${anchor:tempest.x}, z ${anchor:tempest.z+40}"), f"x {t['x']}, z {t['z'] + 40}")
        self.assertEqual(gen_quests.expand("t", "${anchor:tempest.x-400}"), str(t["x"] - 400))
        self.assertEqual(gen_quests.expand("t", "${dir:tempest>dwargon}"), "north")
        self.assertEqual(gen_quests.expand("t", "${dir:dwargon>tempest}"), "south")
        self.assertEqual(gen_quests.expand("t", "${dist:tempest>dwargon}"), "1,400")
        self.assertEqual(gen_quests.expand("t", "no tokens, 100% plain"), "no tokens, 100% plain")
        self.assertEqual((d["x"] - t["x"], d["z"] - t["z"]), (180, -1400))

    def test_compass_axes(self):
        self.assertEqual([gen_quests.compass(*v) for v in ((0, -5), (5, -5), (5, 0), (5, 5), (0, 5), (-5, 5), (-5, 0), (-5, -5))],
                         list(gen_quests.COMPASS))

    def test_unknown_place_or_shape_is_refused(self):
        for s in ("${anchor:nowhere.x}", "${dir:tempest>nowhere}", "${anchor:tempest}", "${dir:tempest}", "${bogus:tempest.x}"):
            with self.assertRaises(gen_quests.QuestError, msg=s):
                gen_quests.expand("t", s)


class RealBook(unittest.TestCase):
    def test_no_overworld_location_task_repeats_a_coordinate(self):
        raw = [(f, k) for f, k, t in overworld_location_tasks() if not isinstance(t["at"], dict)]
        self.assertEqual(raw, [], "write `at = { anchor | landmark | build, dx, dz }`, never [x, z], for the overworld")

    def test_every_location_task_is_on_the_lerfing_continent(self):
        lines = (ROOT / "pack" / "config" / "ttl" / "canon_map.txt").read_text(encoding="utf-8").splitlines()
        m = next(re.match(r"# origin (\d+) (\d+)", t) for t in lines if t.startswith("# origin"))
        oc, orow = int(m[1]), int(m[2])
        rows = [t for t in lines if not t.startswith("#")]
        for f, k, t in overworld_location_tasks():
            x, z = gen_quests.resolve_at(f"{f}:{k}", t["at"])
            c, r = oc + (x >> 4), orow + (z >> 4)
            ch = rows[r][c] if 0 <= r < len(rows) and 0 <= c < len(rows[r]) else "."
            self.assertNotEqual(ch, ".", f"{f}:{k} at {x}, {z} is open sea")

    def test_build_locations_reach_their_survey(self):
        # a box that is narrower than the placer's survey could leave the placed build outside the task
        survey = {"sealed_cave": 128, "blumund": 128, "marris": 128, "forgotten_dragon_city": 128, "clayman_castle": 160, "treyni_shrine": 132}
        for f, k, t in overworld_location_tasks():
            if isinstance(t["at"], dict) and t["at"].get("build") in survey and "dx" not in t["at"] and "dz" not in t["at"]:
                self.assertGreaterEqual(int(t["radius"]), survey[t["at"]["build"]], f"{f}:{k}")

    def test_book_generates_with_every_token_resolved(self):
        files = gen_quests.render()
        lang = next(v for p, v in files.items() if p.name == "en_us.snbt")
        self.assertNotIn("${", lang)
        self.assertIn("About 1,400 blocks north of Tempest", lang)

    def test_no_old_world_places_left_in_the_text(self):
        # the 14,000-block fan map put Tempest at 0, 0 and Dwargon's gate at 435, -1000; neither exists any more
        for f in QUESTS:
            text = f.read_text(encoding="utf-8")
            for old in ("435, -1000", "635, 145", "(0, 0)", "fan map", "14,000"):
                self.assertNotIn(old, text, f"{f.name} still cites {old}")


class WikiAndGuide(unittest.TestCase):
    ROW = re.compile(r"^\| [^|]+ \| (-?\d+), (-?\d+) \| [^|]+ \| `([a-z0-9_]+)` \|$", re.M)

    def test_world_map_rows_match_anchors(self):
        # `| place | X, Z | region | `anchor id` |`: the id names the anchors.toml table the numbers come from
        for lang, text in WIKI.items():
            text = text.replace("−", "-")
            rows = self.ROW.findall(text)
            self.assertGreaterEqual(len(rows), 25, lang)
            for x, z, aid in rows:
                self.assertIn(aid, ANCHORS, f"{lang}: {aid}")
                self.assertEqual((int(x), int(z)), (ANCHORS[aid]["x"], ANCHORS[aid]["z"]), f"{lang}: {aid}")

    def test_world_map_markers_are_canon_landmarks(self):
        import json
        landmarks = json.loads((ROOT / "pack" / "config" / "ttl" / "canon_regions.json").read_text(encoding="utf-8"))["landmarks"]
        for lang, text in WIKI.items():
            pairs = set(re.findall(r"\| (-?\d+), (-?\d+) \|", text.replace("−", "-")))
            missing = [lm["name"] for lm in landmarks if (str(lm["at"][0]), str(lm["at"][1])) not in pairs]
            self.assertEqual(missing, [], f"{lang}: landmarks missing from the world map table")

    def test_arrival_and_gate_in_the_wiki(self):
        a, g, t = ANCHORS["arrival"], ANCHORS["dwargon"], ANCHORS["tempest"]
        for lang in ("en", "nl"):
            for name in ("two-lives", "jura-rings", "world-map"):
                text = (ROOT / "docs" / "wiki" / lang / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn(f"{a['x']}, ", text, f"{lang}/{name}")
                self.assertNotIn("271", text, f"{lang}/{name} still cites the old arrival")
        self.assertEqual((a["x"], a["z"], g["x"], g["z"], t["x"], t["z"]), (1780, -150, 1900, -500, 1720, 900))

    def test_guide_directions(self):
        guide = (ROOT / "design" / "data" / "guide.toml").read_text(encoding="utf-8")
        self.assertNotIn("south-west", guide)
        self.assertNotIn("north-east", guide)


if __name__ == "__main__":
    unittest.main()
