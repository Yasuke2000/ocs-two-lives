"""R12, a system is not a chapter (design/architecture/paths-necro-artificer.md §0): python -I -m unittest discover -s tests

tools/validate.py fails when the data of a standalone system (necro.toml, artifice.toml, choices.toml, roads.toml) names a
story, Oath-path or boss stage, as a value or as a key. Comments may mention them.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate  # noqa: E402


class R12Tests(unittest.TestCase):
    def write(self, name: str, text: str) -> Path:
        d = Path(self.tmp.name)
        p = d / name
        p.write_text(text, encoding="utf-8")
        return p

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_planted_story_stage_fails(self):
        p = self.write("necro.toml", '[[rank]]\nid = 1\nrequires = "ttl.story.act2"\n')
        found = validate.r12_violations([p])
        self.assertEqual(len(found), 1)
        self.assertIn("ttl.story.act2", found[0])

    def test_path_and_boss_stages_and_keys_fail(self):
        p = self.write("artifice.toml", '[gate]\nstages = ["ttl.path.dark", "ttl.boss.t2"]\n[renown]\n"ttl.boss.t1" = 5\n')
        self.assertEqual(len(validate.r12_violations([p])), 3)

    def test_comments_and_system_stages_pass(self):
        p = self.write("choices.toml", '# never gate on ttl.story.* here\n[[choice]]\nid = "sick_village"\n'
                                       'stage = "ttl.necro.rank2"\nnote = "ttl.storyteller is not a story stage"\n')
        self.assertEqual(validate.r12_violations([p]), [])

    def test_the_repo_data_is_clean(self):
        files = [ROOT / "design" / "data" / n for n in validate.R12_FILES]
        self.assertEqual(validate.r12_violations(files), [])
        self.assertTrue((ROOT / "design" / "data" / "roads.toml").exists())


if __name__ == "__main__":
    unittest.main()
