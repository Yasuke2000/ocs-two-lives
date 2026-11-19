"""Generic NPC looks (tools/npc_looks.py): python -I -m unittest tests.test_npc_looks

Stdlib only, so CI checks it without Pillow: every variant of our own has its 64x64 PNG, a mod texture is referenced and
never copied, the pick is stable and fits the arm model, and every side NPC with a look ends up with that skin in its
preset. The pixels themselves are compared by `python tools/gen_npc_looks.py --check` (needs Pillow).
"""
import struct
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_npcs  # noqa: E402
import npc_looks  # noqa: E402

SIDE = tomllib.loads((ROOT / "design" / "data" / "sidequests.toml").read_text(encoding="utf-8"))
ASSETS = ROOT / npc_looks.ASSET_DIR


def png_size(path: Path) -> tuple:
    head = path.read_bytes()[:24]
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)


class NpcLooks(unittest.TestCase):
    def test_every_own_variant_has_its_png(self):
        for look, entry in npc_looks.LOOKS.items():
            self.assertTrue(entry.get("title"), look)
            for n, spec in enumerate(entry["variants"], 1):
                if spec.get("texture"):
                    ns, path = spec["texture"].split(":", 1)
                    if ns == "ttl":  # a hand-made skin (docs/art/npc-skin-prompts.md), never a generated name
                        self.assertFalse(Path(path).name.startswith("look_"), f"{look} #{n}")
                        self.assertEqual(png_size(ROOT / "pack/kubejs/assets/ttl" / path), (64, 64), f"{look} #{n}")
                    continue
                path = ASSETS / npc_looks.file_name(look, n)
                self.assertEqual(png_size(path), (64, 64), f"{path.name}: run python tools/gen_npc_looks.py")

    def test_no_orphan_pngs(self):
        known = {npc_looks.file_name(look, n) for look, e in npc_looks.LOOKS.items()
                 for n, s in enumerate(e["variants"], 1) if not s.get("texture")}
        self.assertEqual({p.name for p in ASSETS.glob("look_*.png")} - known, set())

    def test_pick_is_stable_and_fits_the_model(self):
        self.assertEqual(npc_looks.pick("merchant", "Marlo", "humanoid"), npc_looks.pick("merchant", " marlo ", "humanoid"))
        for look in npc_looks.LOOKS:
            for model in ("humanoid", "humanoid_slim"):
                fits = npc_looks.candidates(look, model)
                for name in ("Bram", "Lyra", "Durn", "Ilse"):
                    if fits:
                        n = npc_looks.pick(look, name, model)
                        self.assertIn(n, fits)
                        self.assertEqual(bool(npc_looks.variants(look)[n - 1].get("slim")), model == "humanoid_slim")

    def test_side_npcs_wear_their_look(self):
        files = gen_npcs.render_side()
        rows = [("adventurer", k) for k in SIDE["adventurer"]] + [("client", k) for k in SIDE["client"]]
        for table, k in rows:
            self.assertIn("look", k, f"{table} {k['id']}: every generic NPC wears a Tensura look, not a default skin")
            n = npc_looks.pick(k["look"], k.get("look_name", k["name"]), k.get("model", "humanoid"))
            want = f'Texture:"{npc_looks.texture(k["look"], n)}"'
            prefix = "ttl_client_" if table == "client" else "ttl_adv_"
            self.assertIn(want, files[gen_npcs.TARGET / f"{prefix}{k['id']}.npc.snbt"], f"{table} {k['id']}")
            if table == "adventurer" and k.get("hire"):
                self.assertIn(want, files[gen_npcs.TARGET / f"ttl_comp_{k['id']}.npc.snbt"], f"companion {k['id']}")

    def test_client_marlo_is_adventurer_marlo(self):
        adv = next(k for k in SIDE["adventurer"] if k["id"] == "merchant")
        cli = next(k for k in SIDE["client"] if k["id"] == "merchant")
        self.assertEqual(npc_looks.pick(adv["look"], adv["name"], adv["model"]),
                         npc_looks.pick(cli["look"], cli.get("look_name", cli["name"]), cli["model"]))


if __name__ == "__main__":
    unittest.main()
