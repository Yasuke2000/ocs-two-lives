"""Issue #5, the Dwarven Arena: python -I -m unittest discover -s tests

blueprints/dwarven_arena.py must not carry the royal warp pad, a Dwargo, the black stained glass or the developers' player
heads, must have a way in, a sealed hall and lit standing spots; design/data/arenas.toml's "dwarven" arena must agree with it.
"""
import collections
import importlib.util
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "blueprints"))
from blueprint import Blueprint  # noqa: E402
import _dwargon_lib  # noqa: E402

AIR = "minecraft:air"


def load():
    spec = importlib.util.spec_from_file_location("dwarven_arena", ROOT / "blueprints" / "dwarven_arena.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bp = Blueprint("dwarven_arena", module.SIZE)
    module.build(bp)
    return module, bp


class DwarvenArena(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.bp = load()
        with (ROOT / "design" / "data" / "arenas.toml").open("rb") as f:
            cls.arena = next(a for a in tomllib.load(f)["arena"] if a["id"] == "dwarven")

    def names(self):
        return {s.split("[", 1)[0] for s in self.bp.blocks.values()}

    def test_nothing_that_was_asked_out(self):
        names = self.names()
        self.assertNotIn("minecraft:black_stained_glass", names)
        self.assertNotIn("minecraft:player_head", names)
        self.assertFalse([n for n in names if "warp_pad" in n], "a warp pad is a teleporter")
        self.assertNotIn("minecraft:oak_sign", names)

    def test_door_and_forecourt(self):
        for z in (24, 25, 26):
            for y in (1, 2, 3):
                self.assertEqual(self.bp.blocks[(6, y, z)], AIR, f"door cell 6 {y} {z}")
        self.assertEqual(self.bp.blocks[(3, 0, 25)], "minecraft:stone_bricks")
        self.assertEqual(self.m.ANCHOR, (3, 1, 25))

    def test_hall_is_sealed_but_for_the_door(self):
        start = self.m.SPOTS["spawn_a"]
        seen = {start}
        todo = collections.deque([start])
        while todo:
            p = todo.popleft()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
                if n in seen:
                    continue
                state = self.bp.blocks.get(n)
                if state is None:
                    self.assertLess(p[0], 7, f"the hall opens to the outside at {p} -> {n}")
                elif state == AIR:
                    seen.add(n)
                    todo.append(n)
        self.assertGreater(len(seen), 30000)

    def test_standing_spots_are_free_solid_and_lit(self):
        light = _dwargon_lib.dark_spots(self.bp.blocks, self.bp.size,
                                        [(x, y, z) for x in range(7, self.m.SIZE[0]) for z in range(self.m.SIZE[2]) for y in range(1, 12)])
        self.assertEqual(light, [], "dark spots a monster could spawn on")
        for name, (x, y, z) in self.m.SPOTS.items():
            self.assertEqual(self.bp.blocks.get((x, y, z)), AIR, name)
            self.assertEqual(self.bp.blocks.get((x, y + 1, z)), AIR, name)
            self.assertNotIn(self.bp.blocks.get((x, y - 1, z), AIR), (AIR,), name)

    def test_arenas_toml_agrees(self):
        a = self.arena
        self.assertEqual(a["where"], {"build": "dwarven_arena"})
        lo, hi = a["box"]["from"], a["box"]["to"]
        for i, n in enumerate(self.m.SIZE):
            self.assertTrue(0 <= lo[i] <= hi[i] < n)
        spots = {"spawn_a": a["spawn_a"], "spawn_b": a["spawn_b"]}
        spots.update({f"mob_{i}": s for i, s in enumerate(a["mob_spots"])})
        self.assertEqual({k: tuple(v) for k, v in spots.items()}, self.m.SPOTS)
        self.assertEqual(a["challenge"]["boss"], "", "no Dwargo here")
        self.assertNotIn("round", a)

    def test_build_toml(self):
        import anchor_refs
        import math
        with (ROOT / "design" / "builds" / "dwarven_arena.toml").open("rb") as f:
            b = tomllib.load(f)
        self.assertEqual(tuple(b["anchor"]), self.m.ANCHOR)
        self.assertNotIn("x", b, "design/data/anchors.toml positions the arena (Lerfing's map)")
        a, village, arrival = (anchor_refs.table()[k] for k in ("dwarven_arena", "dwarf_village", "arrival"))
        self.assertEqual(a["build"], "dwarven_arena")
        # The arena's box + margin + search, wherever the survey puts it.
        ax, _, az = self.m.ANCHOR
        sx, _, sz = self.m.SIZE
        reach = max(b["margin"], b.get("repair_margin", 8)) + b["search"]
        box = (a["x"] - ax - reach, a["z"] - az - reach, a["x"] - ax + sx - 1 + reach, a["z"] - az + sz - 1 + reach)
        # Outside the dwarf village's keepout whatever happens: the landmark placer may put the village up to 64 blocks off
        # its anchor, its jigsaw spreads `reach` (landmarks.toml, 116) round that, and every placed build keeps 24 more.
        lm = next(l for l in tomllib.loads((ROOT / "design" / "data" / "landmarks.toml").read_text(encoding="utf-8"))["landmark"]
                  if l["name"] == "dwarf_village")
        keep = lm["reach"] + 64 + 24
        vbox = (village["x"] - keep, village["z"] - keep, village["x"] + keep, village["z"] + keep)
        overlap = box[0] <= vbox[2] and vbox[0] <= box[2] and box[1] <= vbox[3] and vbox[1] <= box[3]
        self.assertFalse(overlap, f"arena {box} reaches the dwarf village's keepout {vbox}")
        # The Life 2 arrival stays free ground well away from it.
        gap = math.hypot(max(box[0] - arrival["x"], 0, arrival["x"] - box[2]), max(box[1] - arrival["z"], 0, arrival["z"] - box[3]))
        self.assertGreater(gap, 200)

if __name__ == "__main__":
    unittest.main()
