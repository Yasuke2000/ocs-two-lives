"""Offline tests for tools/gen_quests.py (no server): python -I -m unittest discover -s tests

Covers the story extensions (WP-S5): `path`, `stage` / `command` rewards, `team_stage`, cross-chapter `deps`, `min_deps`,
and that the existing chapters still generate byte-identical. Also the quest web (quests-web work package): the `lore` field,
the Life 1 mod namespaces, the layout (tools/quest_layout.py) and the chapter groups, and the audit in tools/quest_graph.py over the real book (every quest unlockable, one connected web,
Life 1 converging on its finale, the Life 2 story order, the dailies unlocking). The last class checks every emitted FTB Quests field name
against the FTB Quests jar when it is available (skipped otherwise)."""
import os
import sys
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_quests  # noqa: E402
import quest_graph  # noqa: E402
import quest_layout  # noqa: E402

CH_A = """
[chapter]
key = "alpha"
title = "Alpha"
order = 1
life = 2

[[quests]]
key = "start"
title = "Start"
tasks = [{ type = "checkmark" }]
rewards = [{ type = "xp", xp = 5 }]

[[quests]]
key = "second"
title = "Second"
deps = ["start"]
tasks = [{ type = "checkmark" }]
"""

CH_B = """
[chapter]
key = "beta"
title = "Beta"
order = 2
life = 2

[[quests]]
key = "oath"
title = "Oath"
deps = ["alpha/second"]
tasks = [{ type = "checkmark" }]
"""


def render(chapters: dict[str, str]):
    """Render TOML chapters (file name -> text) from a scratch folder; returns (files by name, lang, ids)."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in chapters.items():
            Path(tmp, name).write_text(text, encoding="utf-8")
        with mock.patch.object(gen_quests, "SOURCES", Path(tmp)):
            files = gen_quests.render()
    return files


def chapter_text(files, key: str) -> str:
    return files[gen_quests.TARGET / "chapters" / f"{key}.snbt"]


def quest_block(text: str, key_id: str) -> str:
    """The SNBT block of one quest (from its id line to the next quest id or the end)."""
    start = text.index(f'id: "{key_id}"')
    nxt = text.find('\n\t\t{\n', start)
    return text[start:nxt if nxt > 0 else len(text)]


def one_quest(extra: str, key: str = "q", chapter_extra: str = "", life: int = 2) -> str:
    """A one-quest chapter `solo` with the given extra TOML lines inside the quest."""
    return f"""
[chapter]
key = "solo"
title = "Solo"
order = 1
life = {life}
{chapter_extra}
[[quests]]
key = "{key}"
title = "Q"
{extra}
"""


class ExistingBookTests(unittest.TestCase):
    def test_existing_chapters_generate_byte_identical(self):
        files = gen_quests.render()
        stale = [p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        self.assertEqual(stale, [])
        self.assertEqual(gen_quests.stale_chapters(files), [])

    def test_plain_stage_task_is_unchanged(self):
        text = chapter_text(render({"a.toml": one_quest('tasks = [{ type = "stage", stage = "ttl.life2" }]')}), "solo")
        self.assertIn("team_stage: false", text)
        self.assertIn('type: "gamestage"', text)


class StageTaskTests(unittest.TestCase):
    def test_team_stage_flag(self):
        text = chapter_text(render({"a.toml": one_quest(
            'tasks = [{ type = "stage", stage = "ttl.story.act1", team_stage = true }]')}), "solo")
        self.assertIn("team_stage: true", text)

    def test_stage_names_are_ttl_namespaced(self):
        for bad in ("act1", "ttl", "Ttl.Story", "minecraft.x", "ttl.story act"):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                render({"a.toml": one_quest(f'tasks = [{{ type = "stage", stage = "{bad}" }}]')})


class AwakeningTaskTests(unittest.TestCase):
    def test_capstones_read_native_status_in_life_two(self):
        for status in ("HERO", "DEMON_LORD"):
            task, _ = gen_quests.build_task({"life": 2}, "capstone", {"type": "awakening", "status": status}, "AB")
            self.assertEqual(task, {"type": "tensura_ftb:awakening", "status": status, "id": "AB"})

    def test_capstones_reject_invalid_status_and_mortal_chapters(self):
        for life, status in ((2, "HERO_EGG"), (2, None), (1, "HERO"), ("both", "DEMON_LORD")):
            with self.subTest(life=life, status=status), self.assertRaises(gen_quests.QuestError):
                gen_quests.build_task({"life": life}, "capstone", {"type": "awakening", "status": status}, "AB")


class StageRewardTests(unittest.TestCase):
    def reward(self, toml: str) -> str:
        return chapter_text(render({"a.toml": one_quest(
            f'tasks = [{{ type = "checkmark" }}]\nrewards = [{toml}]')}), "solo")

    def test_default_stage_reward_is_personal_and_silent(self):
        text = self.reward('{ type = "stage", stage = "ttl.story.act2" }')
        self.assertIn('type: "gamestage"', text)
        self.assertIn('stage: "ttl.story.act2"', text)
        self.assertIn("team_reward: false", text)
        self.assertIn('auto: "invisible"', text)
        self.assertNotIn("remove:", text)

    def test_remove_team_and_auto(self):
        text = self.reward('{ type = "stage", stage = "ttl.quest.x", remove = true, team = true, auto = "default" }')
        self.assertIn("remove: true", text)
        self.assertIn("team_reward: true", text)
        self.assertNotIn("auto:", text)  # `default` is the absent key

    def test_foreign_stages_are_refused(self):
        for bad in ("ttl.life2", "ttl.race.slime", "ttl.tier.dark", "ttl.boss.t1", "ttl.path.light", "ttl.faction.x.friendly"):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                self.reward(f'{{ type = "stage", stage = "{bad}" }}')

    def test_bad_auto(self):
        with self.assertRaises(gen_quests.QuestError):
            self.reward('{ type = "stage", stage = "ttl.story.a", auto = "sometimes" }')

    def test_auto_applies_to_other_rewards_too(self):
        self.assertIn('auto: "no_toast"', self.reward('{ type = "xp", xp = 5, auto = "no_toast" }'))


class CommandRewardTests(unittest.TestCase):
    def reward(self, toml: str) -> str:
        return chapter_text(render({"a.toml": one_quest(
            f'tasks = [{{ type = "checkmark" }}]\nrewards = [{toml}]')}), "solo")

    def test_defaults(self):
        text = self.reward('{ type = "command", command = "ttl story oath" }')
        self.assertIn('type: "command"', text)
        self.assertIn('command: "/ttl story oath"', text)  # one leading slash, like FTB's own default
        self.assertIn("permission_level: 2", text)  # /ttl subcommands are op-gated; the source stays the player
        self.assertNotIn("silent", text)
        self.assertNotIn("feedback_message", text)
        self.assertNotIn("auto:", text)  # not auto-claimed: the player clicks it

    def test_slash_is_normalised_and_options(self):
        text = self.reward('{ type = "command", command = "//ttl story fight gazel_dwargo ", as_player = true, '
                           'permission_level = 0, silent = true, feedback = "The duel begins" }')
        self.assertIn('command: "/ttl story fight gazel_dwargo"', text)
        self.assertNotIn("permission_level", text)
        self.assertIn("silent: true", text)
        self.assertIn('feedback_message: "The duel begins"', text)

    def test_placeholders_pass_through(self):
        self.assertIn("{p}", self.reward('{ type = "command", command = "ttl story talk {p}" }'))

    def test_refused_commands(self):
        for bad in ("", "/", "ttl skill grant {p} tensura:x", "tensura race set {p} slime", "ttl registry draw {p}",
                    "op {p}", "ttl evolve {p}", "say 100% sure", "say a\nsay b"):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                self.reward('{ type = "command", command = %s }' % gen_quests.snbt_str(bad))

    def test_as_player_false_and_bad_level(self):
        for extra in ("as_player = false", "permission_level = 5", "permission_level = -1"):
            with self.subTest(extra=extra), self.assertRaises(gen_quests.QuestError):
                self.reward('{ type = "command", command = "ttl story oath", %s }' % extra)

    def test_unknown_reward_type_still_refused(self):
        for bad in ("skill", "race", "awakening", "ability"):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                self.reward(f'{{ type = "{bad}", skill = "x" }}')


class PathTests(unittest.TestCase):
    def test_path_adds_a_leading_stage_task_and_hides_the_quest(self):
        files = render({"a.toml": one_quest('path = "light"\ntasks = [{ type = "checkmark" }]')})
        text = chapter_text(files, "solo")
        block = quest_block(text, gen_quests.qid("solo", "q"))
        path_id = gen_quests.qid("solo", "q", "task", "path")
        self.assertIn(path_id, block)
        self.assertLess(block.index(path_id), block.index('type: "checkmark"'))  # the stage task comes first
        self.assertIn('stage: "ttl.path.light"', block)
        self.assertIn("team_stage: false", block)
        self.assertIn("require_sequential_tasks: true", block)
        self.assertIn("invisible: true", block)
        self.assertIn("invisible_until_tasks: 1", block)

    def test_path_hidden_false_keeps_the_quest_visible(self):
        text = chapter_text(render({"a.toml": one_quest(
            'path = "dark"\npath_hidden = false\ntasks = [{ type = "checkmark" }]')}), "solo")
        self.assertIn('stage: "ttl.path.dark"', text)
        self.assertIn("require_sequential_tasks: true", text)
        self.assertNotIn("invisible", text)

    def test_other_tasks_keep_their_ids_with_or_without_path(self):
        base = 'tasks = [{ type = "checkmark" }, { type = "kill", entity = "minecraft:zombie", count = 2 }]'
        plain = chapter_text(render({"a.toml": one_quest(base)}), "solo")
        lane = chapter_text(render({"a.toml": one_quest('path = "dark"\n' + base)}), "solo")
        for i in (0, 1):
            tid = gen_quests.qid("solo", "q", "task", str(i))
            self.assertIn(tid, plain)
            self.assertIn(tid, lane)

    def test_no_path_means_no_extra_fields(self):
        text = chapter_text(render({"a.toml": one_quest('tasks = [{ type = "checkmark" }]')}), "solo")
        for field in ("invisible", "require_sequential_tasks", "min_required_dependencies", "ttl.path"):
            self.assertNotIn(field, text)

    def test_bad_path(self):
        for bad in ("grey", "Light", ""):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                render({"a.toml": one_quest(f'path = "{bad}"\ntasks = [{{ type = "checkmark" }}]')})


class DependencyTests(unittest.TestCase):
    def test_cross_chapter_dependency_uses_the_other_chapters_id(self):
        files = render({"a.toml": CH_A, "b.toml": CH_B})
        text = chapter_text(files, "beta")
        self.assertIn(f'"{gen_quests.qid("alpha", "second")}"', text)
        self.assertEqual(files[gen_quests.TARGET / "chapters" / "alpha.snbt"],
                         render({"a.toml": CH_A, "b.toml": CH_B})[gen_quests.TARGET / "chapters" / "alpha.snbt"])

    def test_file_order_does_not_matter(self):
        one = render({"1_b.toml": CH_B, "2_a.toml": CH_A})
        two = render({"1_a.toml": CH_A, "2_b.toml": CH_B})
        self.assertEqual(chapter_text(one, "beta"), chapter_text(two, "beta"))

    def test_cross_chapter_dependency_does_not_move_the_quest_on_the_grid(self):
        # without local deps the column is 0, whatever the other chapter looks like
        text = chapter_text(render({"a.toml": CH_A, "b.toml": CH_B}), "beta")
        self.assertIn("x: 0.0d", text)

    def test_same_chapter_deps_may_be_qualified(self):
        chapter = CH_A.replace('deps = ["start"]', 'deps = ["alpha/start"]')
        self.assertEqual(chapter_text(render({"a.toml": chapter}), "alpha"), chapter_text(render({"a.toml": CH_A}), "alpha"))

    def test_unknown_targets(self):
        for dep in ("gamma/oath", "alpha/missing", "missing", "alpha/"):
            chapter = CH_B.replace("alpha/second", dep)
            with self.subTest(dep=dep), self.assertRaises(gen_quests.QuestError):
                render({"a.toml": CH_A, "b.toml": chapter})

    def test_cross_chapter_loop(self):
        looped = CH_A.replace('key = "start"\ntitle = "Start"', 'key = "start"\ntitle = "Start"\ndeps = ["beta/oath"]')
        with self.assertRaisesRegex(gen_quests.QuestError, "dependency loop"):
            render({"a.toml": looped, "b.toml": CH_B})

    def test_self_dependency_and_duplicates(self):
        for deps in ('["q"]', '["solo/q"]'):
            with self.subTest(deps=deps), self.assertRaises(gen_quests.QuestError):
                render({"a.toml": one_quest(f'deps = {deps}\ntasks = [{{ type = "checkmark" }}]')})
        two = CH_A.replace('deps = ["start"]', 'deps = ["start", "start"]')
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": two})

    def test_quest_key_with_slash_is_refused(self):
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": one_quest('tasks = [{ type = "checkmark" }]', key="a/b")})

    def test_min_deps(self):
        joined = CH_A + """
[[quests]]
key = "join"
title = "Join"
deps = ["start", "second"]
min_deps = 1
tasks = [{ type = "checkmark" }]
"""
        self.assertIn("min_required_dependencies: 1", chapter_text(render({"a.toml": joined}), "alpha"))
        for bad in ("0", "3"):
            with self.subTest(bad=bad), self.assertRaises(gen_quests.QuestError):
                render({"a.toml": joined.replace("min_deps = 1", f"min_deps = {bad}")})

    def test_chapter_key_used_twice(self):
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": CH_A, "b.toml": CH_A.replace("order = 1", "order = 2")})


class LoreTests(unittest.TestCase):
    def test_lore_is_a_grey_italic_quoted_paragraph_between_text_and_karma(self):
        files = render({"a.toml": one_quest(
            'text = "Task line."\nlore = "A line   of voice."\nkarma = "Honest."\ntasks = [{ type = "checkmark" }]', life=1)})
        lang = files[gen_quests.TARGET / "lang" / "en_us.snbt"]
        i, j, k = lang.index("Task line."), lang.index("&7&o“A line of voice.”&r"), lang.index("Honest.")
        self.assertTrue(i < j < k)

    def test_no_lore_no_change(self):
        files = render({"a.toml": one_quest('text = "T."\ntasks = [{ type = "checkmark" }]', life=1)})
        self.assertNotIn("&7&o", files[gen_quests.TARGET / "lang" / "en_us.snbt"])


class Life1NamespaceTests(unittest.TestCase):
    def solo(self, item: str, chapter_life="1"):
        return render({"a.toml": one_quest(
            f'tasks = [{{ type = "item", item = "{item}" }}]\nrewards = [{{ type = "item", item = "{item}" }}]', life=chapter_life)})

    def test_vanilla_and_the_sophisticated_storage_mods_are_allowed_in_life_1(self):
        for item in ("minecraft:chest", "sophisticatedbackpacks:backpack", "sophisticatedstorage:chest"):
            with self.subTest(item=item):
                self.solo(item)

    def test_tensura_and_other_mods_are_refused_in_life_1_and_shared_chapters(self):
        for item in ("tensura:bronze_coin", "tensura_neb:night_rose", "greatsage:venuzdonoa", "lightmanscurrency:coin_gold", "create:cogwheel"):
            with self.subTest(item=item), self.assertRaises(gen_quests.QuestError):
                self.solo(item)
        with self.assertRaises(gen_quests.QuestError):
            self.solo("tensura:bronze_coin", chapter_life='"both"')

    def test_life_2_is_unrestricted(self):
        self.solo("tensura:bronze_coin", chapter_life="2")

    def test_allowed_namespaces_are_not_banned_in_the_mortal_realm(self):
        banned = tomllib.loads((ROOT / "design" / "data" / "mortal_banned.toml").read_text(encoding="utf-8"))["namespaces"]
        self.assertEqual(set(banned) & set(gen_quests.LIFE1_NAMESPACES), set())


def quest(key: str, deps=(), extra: str = "") -> str:
    d = ", ".join(f'"{x}"' for x in deps)
    return f'\n[[quests]]\nkey = "{key}"\ntitle = "{key.title()}"\ndeps = [{d}]\n{extra}\ntasks = [{{ type = "checkmark" }}]\n'


def chapter(key: str, body: str, life: int = 2, order: int = 1, extra: str = "") -> str:
    return f'[chapter]\nkey = "{key}"\ntitle = "{key.title()}"\norder = {order}\nlife = {life}\n{extra}\n' + body


def laid_out(files, key: str) -> dict:
    """{quest key: quest dict} of a rendered chapter, read back with the layout tool's SNBT reader."""
    ch = quest_layout.parse_snbt(chapter_text(files, key))
    by_id = {q["id"]: q for q in ch["quests"]}
    return {k: by_id[gen_quests.qid(key, k)] for k in (q for q in _keys(ch, key, by_id))}


def _keys(ch, key, by_id):
    for k in ("a", "b", "c", "d", "e", "f", "l1", "l2", "d1", "d2", "opt", "end", "pinned", "start", "second", "oath"):
        if gen_quests.qid(key, k) in by_id:
            yield k


def lang_of(files) -> dict:
    return quest_layout.parse_snbt(files[gen_quests.TARGET / "lang" / "en_us.snbt"])


class LayoutTests(unittest.TestCase):
    """tools/quest_layout.py through the generator: rows, lanes, hidden lines and the "Needs" line."""

    def test_main_line_is_one_straight_row(self):
        files = render({"a.toml": chapter("ch", quest("a") + quest("b", ["a"]) + quest("c", ["b"]) + quest("d", ["c"]))})
        q = laid_out(files, "ch")
        self.assertEqual({q[k]["y"] for k in "abcd"}, {0.0})
        self.assertEqual([q[k]["x"] for k in "abcd"], sorted(q[k]["x"] for k in "abcd"))
        self.assertEqual(len({q[k]["x"] for k in "abcd"}), 4)

    def test_a_line_along_the_main_row_is_hidden_and_named(self):
        # c needs a and b; the line a-c would run through b, so it is hidden and c's text names a
        files = render({"a.toml": chapter("ch", quest("a") + quest("b", ["a"]) + quest("c", ["a", "b"]))})
        q = laid_out(files, "ch")
        self.assertEqual(q["c"]["dep_line_visibility"], {gen_quests.qid("ch", "a"): False})
        self.assertNotIn("dep_line_visibility", q["b"])
        self.assertIn("&7Needs: A&r", lang_of(files)[f"quest.{gen_quests.qid('ch', 'c')}.quest_desc"])

    def test_a_line_across_more_than_two_layers_is_hidden(self):
        body = (quest("a") + quest("b", ["a"]) + quest("c", ["b"]) + quest("d", ["c"])
                + quest("e", ["d"]) + quest("f", ["a", "e"]))
        _pos, hidden = quest_layout.layout([
            {"key": k, "deps": d, "size": 1.0, "optional": False, "path": None, "pin": None}
            for k, d in (("a", []), ("x", ["a"]), ("b", ["x"]), ("c", ["b"]), ("f", ["a", "c"]), ("g", ["a"]),
                         ("h", ["g"]), ("i", ["h"]), ("j", ["i"]), ("k", ["g", "j"]))])
        self.assertIn(("g", "k"), hidden)
        self.assertNotIn(("j", "k"), hidden)
        render({"a.toml": chapter("ch", body)})  # renders without error

    def test_optional_branches_go_below_the_main_line(self):
        files = render({"a.toml": chapter("ch", quest("a") + quest("b", ["a"]) + quest("c", ["b"])
                                          + quest("opt", ["a"], "optional = true"))})
        q = laid_out(files, "ch")
        self.assertGreater(q["opt"]["y"], 0)

    def test_light_lane_above_dark_lane_below(self):
        body = (quest("start") + quest("l1", ["start"], 'path = "light"') + quest("l2", ["l1"], 'path = "light"')
                + quest("d1", ["start"], 'path = "dark"') + quest("d2", ["d1"], 'path = "dark"')
                + quest("end", ["l2", "d2"], "min_deps = 1"))
        q = laid_out(render({"a.toml": chapter("ch", body)}), "ch")
        self.assertEqual(q["start"]["y"], 0.0)
        self.assertEqual(q["end"]["y"], 0.0)
        self.assertLess(q["l1"]["y"], 0)
        self.assertLess(q["l2"]["y"], 0)
        self.assertGreater(q["d1"]["y"], 0)
        self.assertGreater(q["d2"]["y"], 0)

    def test_pin_keeps_its_spot_and_lane_col_are_ignored(self):
        body = quest("a") + quest("b", ["a"]) + quest("pinned", ["a"], "pin = [10, -7.5]")
        q = laid_out(render({"a.toml": chapter("ch", body)}), "ch")
        self.assertEqual((q["pinned"]["x"], q["pinned"]["y"]), (10.0, -7.5))
        plain = chapter_text(render({"a.toml": chapter("ch", quest("a") + quest("b", ["a"]))}), "ch")
        legacy = chapter_text(render({"a.toml": chapter("ch", quest("a", (), "lane = 4\ncol = 9") + quest("b", ["a"], "lane = -2"))}), "ch")
        self.assertEqual(plain, legacy)
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": chapter("ch", quest("a", (), 'pin = "here"'))})

    def test_cross_chapter_dependency_has_no_line_and_is_named(self):
        files = render({"a.toml": CH_A, "b.toml": CH_B})
        oath = gen_quests.qid("beta", "oath")
        q = quest_layout.parse_snbt(chapter_text(files, "beta"))["quests"][0]
        self.assertEqual(q["dep_line_visibility"], {gen_quests.qid("alpha", "second"): False})
        self.assertEqual(lang_of(files)[f"quest.{oath}.quest_desc"], ["&7Needs: Second &8(Alpha)&7&r"])

    def test_min_deps_names_every_dependency(self):
        body = quest("a") + quest("b", ["a", "alpha/second"], "min_deps = 1")
        files = render({"a.toml": CH_A, "b.toml": chapter("ch", body, order=5)})
        desc = lang_of(files)[f"quest.{gen_quests.qid('ch', 'b')}.quest_desc"]
        self.assertEqual(desc, ["&7Needs one of: A, Second &8(Alpha)&7&r"])

    def test_quests_without_lines_form_a_grid_without_overlaps(self):
        body = "".join(quest(f"q{i}", ["alpha/start"]) for i in range(9))
        files = render({"a.toml": CH_A, "b.toml": chapter("ch", body, order=5)})
        lang = lang_of(files)
        geo = quest_layout.chapter_geometry(quest_layout.parse_snbt(chapter_text(files, "ch")), lang)
        self.assertEqual(quest_layout.problems([geo]), [])
        self.assertEqual(len({(x, y) for x, y, _ in geo[2].values()}), 9)

    def test_checks_find_overlaps_and_lines_through_icons(self):
        geo = {"a": (0.0, 0.0, 1.0), "b": (4.0, 0.0, 1.0), "c": (2.0, 0.2, 1.0), "d": (2.5, 0.2, 1.0)}
        self.assertEqual(quest_layout.overlaps(geo), [("c", "d")])
        self.assertEqual(sorted(quest_layout.through(geo, "a", "b")), ["c", "d"])
        self.assertEqual(quest_layout.crossings({"a": (0, 0, 1), "b": (2, 2, 1), "c": (0, 2, 1), "d": (2, 0, 1)},
                                                [("a", "b"), ("c", "d")]), 1)

    def test_the_real_book_has_no_overlaps_and_no_line_through_an_icon(self):
        self.assertEqual(quest_layout.problems(quest_layout.read_book()), [])

    def test_layout_is_deterministic(self):
        files = gen_quests.render()
        again = gen_quests.render()
        self.assertEqual(files, again)


class ChapterGroupTests(unittest.TestCase):
    def test_groups_file_and_titles(self):
        files = render({"a.toml": CH_A})
        groups = quest_layout.parse_snbt(files[gen_quests.TARGET / "chapter_groups.snbt"])["chapter_groups"]
        ids = [g["id"] for g in groups]
        self.assertEqual(ids, [gen_quests.qid("_group", g) for g in gen_quests.CHAPTER_GROUPS])
        lang = lang_of(files)
        nl = quest_layout.parse_snbt(files[gen_quests.TARGET / "lang" / "nl_nl.snbt"])
        for gid, key in zip(ids, gen_quests.CHAPTER_GROUPS):
            self.assertEqual(lang[f"chapter_group.{gid}.title"], gen_quests.CHAPTER_GROUPS[key]["en_us"])
            self.assertEqual(nl[f"chapter_group.{gid}.title"], gen_quests.CHAPTER_GROUPS[key]["nl_nl"])

    def test_a_chapter_joins_the_group_of_its_life(self):
        files = render({"a.toml": chapter("one", quest("a"), life=1, order=1), "b.toml": chapter("two", quest("a"), order=2),
                        "c.toml": chapter("both", quest("a"), life='"both"', order=3)})
        grp = {k: quest_layout.parse_snbt(chapter_text(files, k))["group"] for k in ("one", "two", "both")}
        self.assertEqual(grp, {"one": gen_quests.qid("_group", "life1"), "two": gen_quests.qid("_group", "life2"), "both": ""})
        files = render({"c.toml": chapter("both", quest("a"), life='"both"', extra='group = "life2"')})
        self.assertEqual(quest_layout.parse_snbt(chapter_text(files, "both"))["group"], gen_quests.qid("_group", "life2"))

    def test_bad_groups_are_refused(self):
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": chapter("one", quest("a"), life=1, extra='group = "life2"')})
        with self.assertRaises(gen_quests.QuestError):
            render({"a.toml": chapter("one", quest("a"), extra='group = "nowhere"')})

    def test_the_real_book_is_split_by_life_in_story_order(self):
        chapters, _quests = quest_graph.load()
        life2 = sorted((c for c in chapters.values() if c.get("life") == 2), key=lambda c: c["order"])
        keys = [c["key"] for c in life2]
        story = ["reborn", "tempest_rises", "crossroads", "armed_nation", "kings_test", "orc_lord", "two_hundred_thousand",
                 "whirlpool", "mask_and_blade", "puppet_master", "harvest_festival"]
        self.assertEqual(keys[:len(story)], story)
        rest = keys[len(story):]
        self.assertEqual(rest[0], "daily_jura")  # the dailies, then the side-quest boards
        self.assertTrue(all(k.startswith("side_") for k in rest[1:]))
        self.assertEqual(chapters["daily_deeds"].get("life"), "both")
        self.assertNotIn("group", chapters["daily_deeds"])  # shared by both lives: ungrouped, above the two tabs


class QuestGraphUnitTests(unittest.TestCase):
    """quest_graph on tiny synthetic books."""

    def book(self, **chapters):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for name, text in chapters.items():
            Path(tmp.name, f"{name}.toml").write_text(text, encoding="utf-8")
        return quest_graph.load(Path(tmp.name))

    def test_orphan_root_and_split_web_are_reported(self):
        chapters, quests = self.book(a=CH_A, b=CH_B.replace('deps = ["alpha/second"]', 'deps = []'))
        with mock.patch.object(quest_graph, "ROOTS", {("alpha", "start")}):
            bad = quest_graph.problems(chapters, quests)
        self.assertTrue(any("beta/oath has no dependency" in b for b in bad), bad)
        self.assertTrue(any("not one web" in b for b in bad), bad)

    def test_a_clean_book_has_no_problems(self):
        chapters, quests = self.book(a=CH_A, b=CH_B)
        with mock.patch.object(quest_graph, "ROOTS", {("alpha", "start")}):
            self.assertEqual(quest_graph.problems(chapters, quests), [])

    def test_min_deps_unlock_counts_unlockable_dependencies(self):
        loop = """
[[quests]]
key = "never"
title = "Never"
deps = ["never2"]
tasks = [{ type = "checkmark" }]

[[quests]]
key = "never2"
title = "Never 2"
deps = ["never"]
tasks = [{ type = "checkmark" }]

[[quests]]
key = "either"
title = "Either"
deps = ["start", "never"]
min_deps = 1
tasks = [{ type = "checkmark" }]

[[quests]]
key = "both"
title = "Both"
deps = ["start", "never"]
tasks = [{ type = "checkmark" }]
"""
        # `never` and `never2` loop (the generator refuses that; quest_graph only reports it): they never unlock
        chapters, quests = self.book(a=CH_A + loop)
        unlock = quest_graph.unlockable(quests)
        self.assertIn(("alpha", "either"), unlock)
        self.assertNotIn(("alpha", "both"), unlock)
        self.assertNotIn(("alpha", "never"), unlock)


class QuestWebTests(unittest.TestCase):
    """The real book: design/quests.md "The web"."""

    @classmethod
    def setUpClass(cls):
        cls.chapters, cls.quests = quest_graph.load()

    def ancestors(self, chapter: str, key: str) -> set:
        seen, todo = set(), [(chapter, key)]
        while todo:
            for d in self.quests[todo.pop()]["deps"]:
                if d not in seen:
                    seen.add(d)
                    todo.append(d)
        return seen

    def test_no_problems(self):
        self.assertEqual(quest_graph.problems(self.chapters, self.quests), [])

    def test_only_two_entries_into_the_book(self):
        roots = {k for k, q in self.quests.items() if not q["deps"]}
        self.assertEqual(roots, {("mortal_life", "only_once"), ("reborn", "eyes_open")})

    def test_every_quest_can_be_unlocked(self):
        self.assertEqual(quest_graph.unlockable(self.quests), set(self.quests))

    def test_chapters_are_one_connected_web(self):
        self.assertEqual(len(quest_graph.components(self.chapters, quest_graph.chapter_edges(self.quests))), 1)

    def test_life_1_chapters_hang_off_the_spine_and_converge_on_the_finale(self):
        life1 = [c for c, ch in self.chapters.items() if ch.get("life") == 1]
        self.assertEqual(len(life1), 11)
        legend = self.ancestors("a_life_that_counts", "legend")
        for needed in (("mortal_life", "dragon"), ("mortal_life", "days_30"), ("mortal_life", "only_once"), ("a_life_that_counts", "ledger")):
            self.assertIn(needed, legend)
        for capstone in ("first_days/ready_for_road", "homestead/home_fires", "fields/harvest_home", "delving/deep_delver",
                         "roads_ruins/cartographers_pride", "folk/friend_of_hamlet", "arts/master_hands", "nether_road/hellwalker",
                         "end_road/dragons_eve"):
            self.assertIn(tuple(capstone.split("/")), legend)
        # every non-optional Life 1 quest leads somewhere: into the finale
        stray = [f"{c}/{k}" for (c, k), q in self.quests.items()
                 if q["life"] == 1 and not q["optional"] and (c, k) not in legend and (c, k) != ("a_life_that_counts", "legend")]
        self.assertEqual(stray, [])

    def test_life_1_chapters_sit_before_every_other_chapter_in_the_book(self):
        orders = {c: ch["order"] for c, ch in self.chapters.items()}
        last1 = max(o for c, o in orders.items() if self.chapters[c].get("life") == 1)
        first_other = min(o for c, o in orders.items() if self.chapters[c].get("life") != 1)
        self.assertLess(last1, first_other)
        self.assertEqual(min(orders, key=orders.get), "mortal_life")

    def test_life_1_has_many_quests_each_with_lore_and_karma(self):
        new = [(c, k) for (c, k), q in self.quests.items() if q["life"] == 1 and c != "mortal_life"]
        self.assertGreaterEqual(len(new), 80)
        self.assertLessEqual(len(new), 120)
        missing = []
        for src in sorted(gen_quests.SOURCES.glob("chapter_0[a-z]_*.toml")):
            data = tomllib.loads(src.read_text(encoding="utf-8"))
            missing += [f"{src.name}:{q['key']}" for q in data["quests"] if not q.get("lore") or not q.get("karma")]
        self.assertEqual(missing, [])

    def test_life_2_story_order(self):
        # rebirth -> Tempest Rises -> Crossroads (Act I) -> Armed Nation -> King's Test (Act II) -> Orc Lord (Act III)
        self.assertIn(("reborn", "tempest"), self.ancestors("tempest_rises", "join_town"))
        self.assertIn(("tempest_rises", "tempest_stands"), self.ancestors("crossroads", "crossroads"))
        self.assertIn(("crossroads", "forest_awakens"), self.ancestors("armed_nation", "road_supplies"))
        kt = self.ancestors("kings_test", "act_two")
        self.assertIn(("armed_nation", "throne"), kt)
        self.assertIn(("crossroads", "forest_awakens"), kt)
        self.assertIn(("kings_test", "act_two"), self.ancestors("orc_lord", "envoy"))
        self.assertIn(("orc_lord", "orc_lord_kill"), self.ancestors("reborn", "orc_war"))

    def test_each_oath_can_finish_the_last_three_acts(self):
        sources = [tomllib.loads(src.read_text(encoding="utf-8"))
                   for src in gen_quests.SOURCES.glob("*.toml")]
        oath = {(data["chapter"]["key"], q["key"]): q.get("path")
                for data in sources for q in data["quests"]}
        for data in sources:
            if data["chapter"]["key"] in ("mask_and_blade", "puppet_master", "harvest_festival"):
                for quest in data["quests"]:
                    self.assertTrue(quest.get("lore", "").strip(), quest["key"])
        for path, other in (("light", "dark"), ("dark", "light")):
            available = {k: q for k, q in self.quests.items() if oath[k] != other}
            reached = quest_graph.unlockable(available)
            for chapter in ("mask_and_blade", "puppet_master", "harvest_festival"):
                with self.subTest(chapter=chapter, path=path):
                    keys = {k for k in self.quests if k[0] == chapter}
                    lane = {k for k in keys if oath[k] == path}
                    opposite = {k for k in keys if oath[k] == other}
                    self.assertTrue(lane)
                    self.assertEqual(len(lane), len(opposite))
                    self.assertLessEqual(keys - opposite, reached)

    def test_dailies_unlock_at_sensible_points(self):
        for k, q in self.quests.items():
            if k[0] == "daily_deeds":
                self.assertEqual(set(q["deps"]), {("mortal_life", "first_night"), ("reborn", "tempest")})
                self.assertEqual(q["min"], 1)  # either life's first step opens the shared dailies
            if k[0] == "daily_jura":
                self.assertTrue(q["deps"] and all(d[0] in ("reborn", "tempest_rises") for d in q["deps"]), k)

    def test_ep_ladder_is_ordered(self):
        self.assertIn(("tempest_rises", "ep_3000"), self.ancestors("reborn", "ep_5000"))
        self.assertIn(("armed_nation", "ep_6000"), self.ancestors("reborn", "ep_20000"))
        self.assertIn(("reborn", "ep_20000"), self.ancestors("orc_lord", "ep_50000"))


FTB_QUESTS_JAR = Path(os.environ.get("FTB_QUESTS_JAR", r"C:\Users\david\AppData\Roaming\PrismLauncher\instances\OCs\minecraft\mods\ftb-quests-neoforge-2101.1.39.jar"))


@unittest.skipUnless(FTB_QUESTS_JAR.exists(), "FTB Quests jar not found (set FTB_QUESTS_JAR)")
class JarFieldNameTests(unittest.TestCase):
    """Every key the generator emits must be a string constant of the FTB Quests class that reads it."""

    @classmethod
    def setUpClass(cls):
        cls.jar = zipfile.ZipFile(FTB_QUESTS_JAR)

    def cls_has(self, cls: str, *names: str):
        data = self.jar.read(f"dev/ftb/mods/ftbquests/quest/{cls}.class")
        for name in names:
            with self.subTest(cls=cls, name=name):
                self.assertIn(name.encode(), data)

    def test_reward_and_task_type_names(self):
        self.cls_has("reward/RewardTypes", "command", "gamestage")
        self.cls_has("task/TaskTypes", "gamestage")

    def test_command_reward_fields(self):
        self.cls_has("reward/CommandReward", "command", "permission_level", "silent", "feedback_message")

    def test_stage_reward_and_task_fields(self):
        self.cls_has("reward/StageReward", "stage", "remove")
        self.cls_has("task/StageTask", "stage", "team_stage")

    def test_common_reward_fields(self):
        self.cls_has("reward/Reward", "team_reward", "auto")
        self.cls_has("reward/RewardAutoClaim", *gen_quests.AUTO_CLAIM)

    def test_quest_fields(self):
        self.cls_has("Quest", "min_required_dependencies", "require_sequential_tasks", "invisible",
                     "invisible_until_tasks", "dependencies", "hide_until_deps_complete", "dep_line_visibility")

    def test_chapter_group_fields(self):
        self.cls_has("BaseQuestFile", "chapter_groups", "chapter_groups.snbt", "group")
        self.cls_has("QuestObjectType", "chapter_group")


if __name__ == "__main__":
    unittest.main()
