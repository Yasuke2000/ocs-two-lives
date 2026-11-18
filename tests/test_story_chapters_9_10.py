"""Offline tests for the story chapters 9 (Two Hundred Thousand, Act III) and 10 (The Whirlpool, Act IV), WP-S7 (no server):
python -I -m unittest discover -s tests

The generator (tests/test_gen_quests.py) proves the TOML is well formed; these tests prove the chapters agree with the data they point
at: every boss id, flag, act, faction and entity a quest names exists, the two lanes of a chapter are the same size, a fight-start
claim happens inside the 96-block rule of `ttl story fight`, the flags are earned on their own path, and every quest carries lore."""
import os
import re
import sys
import tomllib
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_quests  # noqa: E402

TENSURA_JAR = Path(os.environ.get("TENSURA_JAR", r"C:\Users\david\AppData\Roaming\PrismLauncher\instances\OCs\minecraft\mods\tensura-neoforge-2.0.1.5.jar"))


def load(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def chapter(name: str) -> dict:
    return load(ROOT / "design" / "quests" / name)


CH9 = chapter("chapter_9_two_hundred_thousand.toml")
CH10 = chapter("chapter_10_whirlpool.toml")
STORY = load(ROOT / "design" / "data" / "story.toml")
BOSSES = {b["id"]: b for b in load(ROOT / "design" / "data" / "bosses.toml")["boss"]}
FACTIONS = {f["id"] for f in load(ROOT / "design" / "data" / "factions.toml")["faction"]}
ACTS = {a["id"]: a for a in STORY["act"]}
FLAGS = STORY["flag"]
CHAPTERS = {"9": CH9, "10": CH10}

LORE_MARKERS = ("anime season 1", "our interpretation", "in the story", "tensura's own")


def quests(ch: dict) -> dict:
    return {q["key"]: q for q in ch["quests"]}


def commands(ch: dict):
    for q in ch["quests"]:
        for r in q.get("rewards", []):
            if r["type"] == "command":
                yield q, r["command"]


class ShapeTests(unittest.TestCase):
    def test_chapter_headers(self):
        self.assertEqual((CH9["chapter"]["key"], CH9["chapter"]["order"]), ("two_hundred_thousand", 9))
        self.assertEqual((CH10["chapter"]["key"], CH10["chapter"]["order"]), ("whirlpool", 10))
        for ch in (CH9, CH10):
            self.assertEqual(ch["chapter"]["life"], 2)
            self.assertTrue(ch["chapter"]["hide_until_deps_complete"])

    def test_lanes_are_the_same_size(self):
        for name, ch in CHAPTERS.items():
            with self.subTest(chapter=name):
                lanes = [q.get("path") for q in ch["quests"] if not q.get("optional")]
                self.assertEqual(lanes.count("light"), lanes.count("dark"))
                self.assertGreaterEqual(lanes.count("light"), 5)

    def test_lanes_hold_only_their_own_path_in_a_chain(self):
        for name, ch in CHAPTERS.items():
            by_key = quests(ch)
            for q in ch["quests"]:
                if q.get("path"):
                    with self.subTest(chapter=name, quest=q["key"]):
                        same_chapter = [d for d in q["deps"] if "/" not in d]
                        for d in same_chapter:
                            self.assertIn(by_key[d].get("path"), (None, q["path"]), f"{q['key']} depends across lanes on {d}")

    def test_each_chapter_has_one_spine_start_and_one_join(self):
        self.assertEqual(quests(CH9)["act_three"]["min_deps"], 1)
        self.assertEqual(set(quests(CH9)["act_three"]["deps"]), {"spare_orcs", "horde_kneels"})
        self.assertEqual(quests(CH10)["act_four"]["min_deps"], 1)
        self.assertEqual(set(quests(CH10)["act_four"]["deps"]), {"victory_feast", "puppet_pay"})

    def test_entry_points_are_explicit_cross_chapter_deps(self):
        # Chapter 9 follows chapter 8's finale and the war of chapter 4; chapter 10 follows chapter 9's finale.
        self.assertIn("kings_test/act_two", quests(CH9)["war_council"]["deps"])
        self.assertIn("orc_lord/hold_the_line", quests(CH9)["war_council"]["deps"])
        self.assertEqual(quests(CH10)["calamity_omen"]["deps"], ["two_hundred_thousand/act_three"])

    def test_stage_tasks_only_name_known_stages(self):
        for name, ch in CHAPTERS.items():
            for q in ch["quests"]:
                for t in q["tasks"]:
                    if t["type"] != "stage":
                        continue
                    stage = t["stage"]
                    with self.subTest(chapter=name, quest=q["key"], stage=stage):
                        if stage.startswith("ttl.defeated."):
                            self.assertIn(stage.removeprefix("ttl.defeated."), BOSSES)
                        elif m := re.fullmatch(r"ttl\.story\.act(\d+)", stage):
                            self.assertIn(int(m.group(1)), ACTS)
                        else:
                            self.fail(f"unexpected stage {stage}")


class LoreTests(unittest.TestCase):
    def test_every_quest_carries_lore(self):
        for name, ch in CHAPTERS.items():
            for q in ch["quests"]:
                with self.subTest(chapter=name, quest=q["key"]):
                    text = q["text"].lower().replace("\n", " ")
                    self.assertGreater(len(text), 80)
                    self.assertTrue(any(m in text for m in LORE_MARKERS), "no canon reference or 'our interpretation' marker")

    def test_chapter_headers_cite_their_canon_and_interpretation(self):
        for name, path in (("9", "chapter_9_two_hundred_thousand.toml"), ("10", "chapter_10_whirlpool.toml")):
            head = (ROOT / "design" / "quests" / path).read_text(encoding="utf-8").split("[chapter]")[0]
            with self.subTest(chapter=name):
                self.assertIn("Canon anchors", head)
                self.assertIn("Our interpretation", head)
                self.assertIn("episode", head)


class RewardTests(unittest.TestCase):
    def test_rewards_are_modest_and_grant_nothing_unique(self):
        for name, ch in CHAPTERS.items():
            for q in ch["quests"]:
                for r in q.get("rewards", []):
                    with self.subTest(chapter=name, quest=q["key"], reward=r):
                        if r["type"] == "xp":
                            self.assertLessEqual(r["xp"], 300)
                        elif r["type"] == "item":
                            item = r["item"]
                            self.assertNotIn("core", item)
                            self.assertNotIn("skill", item)
                            self.assertNotIn("stellar", item)
                            if item.endswith("_coin"):
                                self.assertLessEqual(r.get("count", 1), 4)
                        elif r["type"] == "command":
                            self.assertRegex(r["command"], r"^ttl story (act|flag|fight|oath) ")
                        else:
                            self.fail(f"unexpected reward type {r['type']}")

    def test_command_rewards_use_the_claiming_player_placeholder(self):
        for ch in (CH9, CH10):
            for q, cmd in commands(ch):
                if cmd.startswith(("ttl story act", "ttl story flag")):
                    with self.subTest(quest=q["key"]):
                        self.assertIn("{p}", cmd)
                        self.assertNotIn("@p", cmd)

    def test_the_generator_accepts_both_chapters(self):
        files = gen_quests.render()
        self.assertEqual(gen_quests.stale_chapters(files), [])


class StoryDataTests(unittest.TestCase):
    def test_flags_and_acts_named_by_rewards_exist_and_match_the_lane(self):
        for ch in (CH9, CH10):
            for q, cmd in commands(ch):
                if m := re.fullmatch(r"ttl story flag \{p\} (\w+)", cmd):
                    flag = m.group(1)
                    with self.subTest(quest=q["key"], flag=flag):
                        self.assertIn(flag, FLAGS)
                        # a path-bound flag may only be set by a quest of that path (story.js refuses it otherwise)
                        if "path" in FLAGS[flag]:
                            self.assertEqual(q.get("path"), FLAGS[flag]["path"])
                if m := re.fullmatch(r"ttl story act \{p\} (\d+)", cmd):
                    self.assertIn(int(m.group(1)), ACTS)

    def test_the_finales_close_the_acts_the_story_data_assigns_to_the_chapters(self):
        self.assertIn(9, ACTS[3]["chapters"])
        self.assertIn(10, ACTS[4]["chapters"])
        self.assertIn("ttl story act {p} 3", [c for _, c in commands(CH9)])
        self.assertIn("ttl story act {p} 4", [c for _, c in commands(CH10)])

    def test_act_reputation_uses_known_factions_and_matches_the_quest_text(self):
        for n, ch, quest in ((3, CH9, "act_three"), (4, CH10, "act_four")):
            for lane in ("light_rep", "dark_rep"):
                self.assertTrue(set(ACTS[n][lane]) <= FACTIONS)
            text = quests(ch)[quest]["text"]
            for lane, word in (("light_rep", "light"), ("dark_rep", "dark")):
                for faction, value in ACTS[n][lane].items():
                    title = {"orc_horde": "Orc Horde", "lizardmen": "Lizardmen", "tempest": "Tempest", "outcast": "Outcast Society"}[faction]
                    sign = "+" if value > 0 else "-"
                    with self.subTest(act=n, lane=word, faction=faction):
                        self.assertIn(f"{title} {sign}{abs(value)}", text)

    def test_the_new_flags_belong_to_the_lane_that_earns_them(self):
        self.assertEqual(FLAGS["orcs_joined"]["path"], "light")
        self.assertEqual(FLAGS["horde_leader"]["path"], "dark")

    def test_both_acts_unlock_the_fights_of_the_chapter(self):
        self.assertEqual(set(ACTS[3]["unlock_bosses"]), {"orc_lord", "orc_disaster"})
        self.assertEqual(ACTS[4]["unlock_bosses"], ["charybdis"])


class FightTests(unittest.TestCase):
    def fight_quests(self):
        for ch in (CH9, CH10):
            for q, cmd in commands(ch):
                if m := re.fullmatch(r"ttl story fight (\w+)", cmd):
                    yield q, m.group(1)

    def test_fight_starts_name_bosses_and_stand_inside_the_fight_rule(self):
        near = STORY["rules"]["fight_near"]
        seen = set()
        for q, boss in self.fight_quests():
            seen.add(boss)
            with self.subTest(quest=q["key"], boss=boss):
                self.assertIn(boss, BOSSES)
                loc = [t for t in q["tasks"] if t["type"] == "location"]
                self.assertEqual(len(loc), 1, "the claim must be tied to one place")
                self.assertLessEqual(loc[0]["radius"], 60)
                spawn = BOSSES[boss]["spawn"]
                if "at" in spawn and "x" in spawn["at"]:
                    dx = loc[0]["at"][0] - spawn["at"]["x"]
                    dz = loc[0]["at"][1] - spawn["at"]["z"]
                    self.assertLessEqual((dx * dx + dz * dz) ** 0.5 + loc[0]["radius"], near)
        self.assertEqual(seen, {"orc_lord", "orc_disaster", "charybdis"})

    def test_each_lane_fights_each_boss_and_waits_for_the_kill(self):
        for ch, lane_bosses in ((CH9, ("orc_lord", "orc_disaster")), (CH10, ("charybdis",))):
            for path in ("light", "dark"):
                starts = {b for q, b in self.fight_quests() if q.get("path") == path and q in ch["quests"]}
                kills = {t["stage"].removeprefix("ttl.defeated.") for q in ch["quests"] if q.get("path") == path
                         for t in q["tasks"] if t["type"] == "stage" and t["stage"].startswith("ttl.defeated.")}
                with self.subTest(chapter=ch["chapter"]["key"], path=path):
                    self.assertEqual(starts, set(lane_bosses))
                    self.assertEqual(kills, set(lane_bosses))

    def test_a_disaster_fight_follows_the_lord_fight_it_requires(self):
        by_key = quests(CH9)
        self.assertEqual(BOSSES["orc_disaster"]["requires"], ["orc_lord"])
        self.assertIn("geld_falls", by_key["face_disaster"]["deps"])
        self.assertIn("devour_king", by_key["champion_turns"]["deps"])

    def test_charybdis_arena_matches_the_shore_quests(self):
        arena = BOSSES["charybdis"]["spawn"]["at"]
        for key in ("face_whirlpool", "wake_calamity", "shore_camp", "harlequins_toll"):
            q = quests(CH10)[key]
            loc = [t for t in q["tasks"] if t["type"] == "location"][0]
            with self.subTest(quest=key):
                self.assertEqual(loc["at"], [arena["x"], arena["z"]])


@unittest.skipUnless(TENSURA_JAR.exists(), "Tensura jar not found (set TENSURA_JAR)")
class JarIdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.lang = json.loads(zipfile.ZipFile(TENSURA_JAR).read("assets/tensura/lang/en_us.json"))

    def test_tensura_entities_items_and_icons_exist(self):
        for name, ch in CHAPTERS.items():
            for q in ch["quests"]:
                ids = [q["icon"]] if q.get("icon") else []
                ids += [t["entity"] for t in q["tasks"] if t["type"] == "kill"]
                ids += [t["item"] for t in q["tasks"] if t["type"] == "item"]
                ids += [r["item"] for r in q.get("rewards", []) if r["type"] == "item"]
                for ident in ids:
                    if not ident.startswith("tensura:"):
                        continue
                    path = ident.split(":", 1)[1]
                    with self.subTest(chapter=name, quest=q["key"], id=ident):
                        self.assertTrue(f"item.tensura.{path}" in self.lang or f"entity.tensura.{path}" in self.lang or f"block.tensura.{path}" in self.lang)

    def test_every_boss_entity_of_the_chapters_exists(self):
        for boss in ("orc_lord", "orc_disaster", "charybdis"):
            self.assertIn(BOSSES[boss]["entity"].replace("tensura:", "entity.tensura."), self.lang)
        self.assertIn("entity.tensura.lizardman", self.lang)
        self.assertIn("entity.tensura.orc", self.lang)


if __name__ == "__main__":
    unittest.main()
