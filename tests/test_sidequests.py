"""Side quests hang together: python -I -m unittest discover -s tests

The side chapters (design/quests/chapter_2x_side_*.toml) start mechanics by id (`ttl sidequest start {p} <id>`) and read the
stages those mechanics set (ttl.quest.side.<id>, ttl.quest.side.seen.<place>, ttl.quest.side.hired). A typo on either side
would leave a quest that never completes, so every reference is checked here; so are the repeat rules (a repeatable result
quest removes its own stage, its cooldown equals the mechanic's repeat_hours) and the Easy NPC presets of the side content.
"""
import re
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402
import gen_npcs  # noqa: E402
from sidequests_check import check_sidequests  # noqa: E402

SIDE = tomllib.loads((ROOT / "design" / "data" / "sidequests.toml").read_text(encoding="utf-8"))
CHAPTERS = sorted((ROOT / "design" / "quests").glob("chapter_2*_side_*.toml"))
START = re.compile(r"^ttl sidequest start \{p\} ([a-z0-9_]+)$")


def side_quests():
    for path in CHAPTERS:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for q in data.get("quests", []):
            yield path.name, data["chapter"], q


class SideQuestTests(unittest.TestCase):
    def test_data_is_valid(self):
        data = {}
        for p in sorted((ROOT / "design" / "data").glob("*.toml")):
            data[p.stem] = tomllib.loads(p.read_text(encoding="utf-8"))
        check_sidequests(data["sidequests"], data)

    def test_chapters_are_life2(self):
        self.assertGreaterEqual(len(CHAPTERS), 4)
        for path in CHAPTERS:
            ch = tomllib.loads(path.read_text(encoding="utf-8"))["chapter"]
            self.assertEqual(ch["life"], 2, path.name)

    def test_references(self):
        ids = {q["id"]: q for q in SIDE["quest"]}
        seen = {p["id"] for p in SIDE["place"] if p.get("discover")}
        started, staged = set(), set()
        for name, _, q in side_quests():
            for r in q.get("rewards", []):
                if r.get("type") == "command":
                    m = START.match(r["command"])
                    self.assertTrue(m, f"{name} {q['key']}: unexpected command {r['command']!r}")
                    self.assertIn(m.group(1), ids, f"{name} {q['key']}: starts unknown side quest {m.group(1)}")
                    started.add(m.group(1))
            for t in q.get("tasks", []):
                if t.get("type") != "stage" or not t["stage"].startswith("ttl.quest.side."):
                    continue
                rest = t["stage"][len("ttl.quest.side."):]
                if rest.startswith("seen."):
                    self.assertIn(rest[5:], seen, f"{name} {q['key']}: no discover place {rest[5:]}")
                elif rest != "hired":
                    self.assertIn(rest, ids, f"{name} {q['key']}: no side quest {rest}")
                    staged.add(rest)
        # Every mechanic the book starts is also read back by a stage task.
        self.assertEqual(started - staged, set())

    def test_repeatables(self):
        ids = {q["id"]: q for q in SIDE["quest"]}
        for name, _, q in side_quests():
            stages = [t["stage"][len("ttl.quest.side."):] for t in q.get("tasks", [])
                      if t.get("type") == "stage" and t["stage"].startswith("ttl.quest.side.") and not t["stage"].startswith("ttl.quest.side.seen.")]
            for sid in stages:
                if sid not in ids:
                    continue
                hours = ids[sid].get("repeat_hours", 0)
                if q.get("repeatable"):
                    self.assertEqual(q.get("cooldown"), hours * 3600, f"{name} {q['key']}: cooldown != repeat_hours of {sid}")
                    removes = [r for r in q.get("rewards", []) if r.get("type") == "stage" and r.get("remove")]
                    self.assertTrue(any(r["stage"] == f"ttl.quest.side.{sid}" for r in removes), f"{name} {q['key']}: must remove its stage")
                else:
                    self.assertEqual(hours, 0, f"{name} {q['key']}: {sid} repeats every {hours} h but the quest does not")

    def test_presets(self):
        files = gen_npcs.render_side()
        for k in SIDE["adventurer"]:
            self.assertIn(gen_npcs.TARGET / f"ttl_adv_{k['id']}.npc.snbt", files)
            self.assertEqual(gen_npcs.TARGET / f"ttl_comp_{k['id']}.npc.snbt" in files, "hire" in k)
        for c in SIDE["client"]:
            self.assertIn(gen_npcs.TARGET / f"ttl_client_{c['id']}.npc.snbt", files)
        for path, text in files.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, f"{path.name} is stale: run python tools/gen_npcs.py")
            if path.name.startswith("ttl_comp_"):
                self.assertIn('Type:"MELEE_ATTACK"', text)
                self.assertIn("Invulnerable:0b", text)
            if path.name.startswith("ttl_adv_"):
                self.assertIn('Type:"RANDOM_STROLL_AROUND_HOME"', text)
                self.assertIn("Invulnerable:1b", text)

    def test_places_on_land(self):
        import anchor_refs
        from sidequests_check import canon_cell
        for p in SIDE["place"]:
            if p["anchor"] == "world":
                self.assertIn("at", p, f"{p['id']}: a world place names its anchors.toml anchor (at), not numbers")
                x, z = anchor_refs.point(p["id"], p["at"])
                self.assertTrue(canon_cell(x, z).isalpha(), p["id"])

    def test_generated_data_has_it(self):
        self.assertIn('"sidequests": {', gen_data.TARGET.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
