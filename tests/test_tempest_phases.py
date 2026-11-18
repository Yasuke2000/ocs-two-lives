"""Regression checks for the growth rings, before a runtime phase switch is introduced."""
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "blueprints")]

import nbt
import tempest
import tempest_city
import tempest_town


def chapter_destinations():
    for pattern in ("chapter_2_*.toml", "chapter_7_*.toml"):
        source, = (ROOT / "design/quests").glob(pattern)
        for quest in tomllib.loads(source.read_text(encoding="utf-8"))["quests"]:
            for task in quest["tasks"]:
                if task["type"] == "location" and task["dimension"] == "minecraft:overworld":
                    yield tuple(task["at"])


class TempestPhaseTests(unittest.TestCase):
    def test_exported_slabs_preserve_existing_quest_and_npc_positions(self):
        previous = tempest
        protected = set(chapter_destinations())
        npcs = tomllib.loads((ROOT / "design/data/npcs.toml").read_text(encoding="utf-8"))
        protected.update((s["x"], s["z"]) for s in npcs["spot"] if s.get("anchor") == "tempest")
        structure_dir = ROOT / "pack/kubejs/data/ttl/structure"
        for phase in (tempest_town, tempest_city):
            sx, sy, sz = phase.SIZE
            ax, ay, az = phase.ARRIVAL
            px, _, pz = previous.ARRIVAL
            self.assertEqual(ay, tempest.ARRIVAL[1])
            self.assertLessEqual(max(sx, sz), 192)
            self.assertLess(previous.SIZE[0], sx)
            self.assertLess(previous.SIZE[2], sz)
            destinations = {(x, z) for x, z in protected if 0 <= x + ax < sx and 0 <= z + az < sz}
            outside_core = {(x, z) for x, z in destinations
                            if not (0 <= x + px < previous.SIZE[0] and 0 <= z + pz < previous.SIZE[2])}
            walk = {}
            for i, (start, stop) in enumerate(zip(phase.PARTS, [*phase.PARTS[1:], sz])):
                filename = structure_dir / f"{phase.__name__}_{i}.nbt"
                slab = nbt.read_gzip(filename)
                self.assertEqual(slab["size"], [sx, sy, stop - start])
                states = [entry["Name"] for entry in slab["palette"]]
                for block in slab["blocks"]:
                    x, y, z = block["pos"]
                    wx, wz = x - ax, z + start - az
                    if 0 <= wx + px < previous.SIZE[0] and 0 <= wz + pz < previous.SIZE[2]:
                        self.fail(f"{filename.name} writes inside the previous phase at {wx}, {wz}")
                    if (wx, wz) in outside_core and ay - 1 <= y <= ay + 1:
                        walk[wx, y, wz] = states[block["state"]]
            for x, z in outside_core:
                self.assertNotIn(walk.get((x, ay - 1, z)), (None, "minecraft:air", "minecraft:water"))
                for y in (ay, ay + 1):
                    self.assertEqual(walk.get((x, y, z)), "minecraft:air", (phase.__name__, x, y, z))
            previous = phase
