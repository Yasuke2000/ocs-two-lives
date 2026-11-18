"""Offline tests for tools/gen_quests.py (no server): python -I -m unittest discover -s tests

Covers the story extensions (WP-S5): `path`, `stage` / `command` rewards, `team_stage`, cross-chapter `deps`, `min_deps`,
and that the existing chapters still generate byte-identical. The last class checks every emitted FTB Quests field name
against the FTB Quests jar when it is available (skipped otherwise)."""
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_quests  # noqa: E402

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
                     "invisible_until_tasks", "dependencies", "hide_until_deps_complete")


if __name__ == "__main__":
    unittest.main()
