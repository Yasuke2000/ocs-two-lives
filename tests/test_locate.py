"""/locate place and /ttl where (life/locate.js): every anchor id is a place, and the script resolves them all."""
import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_data  # noqa: E402

GENERATED = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "anchors.js"


class LocatePlaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = tomllib.loads((ROOT / "design" / "data" / "anchors.toml").read_text(encoding="utf-8"))
        cls.toml = {k: v for k, v in raw.items() if k != "keepout"}
        text = GENERATED.read_text(encoding="utf-8")
        cls.js = json.loads(text[text.index("const TtlAnchors = ") + len("const TtlAnchors = "):])

    def test_every_anchor_id_is_a_place(self):
        self.assertGreaterEqual(len(self.toml), 58)
        self.assertEqual(set(self.js), set(self.toml))
        for aid, a in self.toml.items():
            with self.subTest(anchor=aid):
                self.assertTrue(self.js[aid]["title"].strip())
                self.assertEqual(self.js[aid]["title"], gen_data.anchor_title(dict(a, id=aid)))
                self.assertEqual(self.js[aid].get("map", True), a.get("map", True))

    def test_friendly_names(self):
        self.assertEqual(self.js["tempest"]["title"], "Tempest")
        self.assertEqual(self.js["dwargon"]["title"], "Dwargon")
        self.assertEqual(self.js["blumund"]["title"], "Blumund")

    def test_script_resolves_every_anchor(self):
        subprocess.run(["node", str(Path(__file__).with_name("locate.js"))], check=True)
