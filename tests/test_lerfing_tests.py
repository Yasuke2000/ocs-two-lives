"""The bot tests of Lerfing's import, checked offline (WP-L6; python -I -m unittest discover -s tests)

tests/ingame/lerfing.rcon and lerfing_sea.rcon run on the server after the import night; this file keeps everything they stand
on honest without a server:

* tests/anchors.env is what tools/gen_data.py writes from design/data/anchors.toml and design/data/lerfing/probes.toml, and every
  ${anchor:...} / ${probe:...} token in tests/ingame/*.rcon resolves to a number (or block, biome) in it;
* the probe points of design/data/lerfing/probes.toml agree with the committed rasters, the canon grid (ring, blend, the continent
  line off a coast) and canon_regions.json; with $TTL_LERFING_WORLD pointing at an import output they are read from the
  region files themselves (the exact block at x, y, z);
* the anchors the tests put bots on stand where the tests expect (Tempest in the core, the old goblin village in the dark band, the
  arrival on the rim, Dwargon's gate on the Canaat's stony_peaks), at the rasters' 16-block resolution;
* tools/test_lib.sh (the runner behind `tools/server.sh test`): token expansion, `@expect`, `@until`, `@import`, with a fake
  `rcon`. Skipped when no bash (4.2+) is on the PATH.
"""
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import anchors_env  # noqa: E402

INGAME = ROOT / "tests" / "ingame"
ENV = ROOT / "tests" / "anchors.env"
LIB = ROOT / "tools" / "test_lib.sh"
SERVER = ROOT / "tools" / "server.sh"
PROBES = ROOT / "design" / "data" / "lerfing" / "probes.toml"
ANCHORS = ROOT / "design" / "data" / "anchors.toml"
RASTERS = ROOT / "design" / "data" / "lerfing"
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
GRID = ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
TERRITORIAL_WATERS = 128  # CanonGrid.TERRITORIAL_WATERS
TOKEN = re.compile(r"\$\{(anchor|probe):([a-z0-9_]+)(\.[a-z]+)?([+-][0-9]+)?\}")
DIRECTIVE = re.compile(r"^@(sleep \d+|until \d+ \S.*|expect \d+ \S.* :: \S.*|import)$")


def env_table() -> dict:
    out = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k] = v
    return out


def rcon_lines(path: Path) -> list[str]:
    return [t for t in path.read_text(encoding="utf-8").splitlines() if t.strip() and not t.lstrip().startswith("#")]


def find_bash():
    """A bash of 4.2+ that can read our paths (Git bash on Windows: the WSL launcher in System32 cannot), else None."""
    candidates = [os.environ.get("TTL_BASH"), shutil.which("bash"), r"C:\Program Files\Git\bin\bash.exe", "/bin/bash"]
    for c in candidates:
        if not c or not (shutil.which(c) or os.path.exists(c)):
            continue
        try:
            r = subprocess.run([c, "-c", f'[ -f "{LIB.as_posix()}" ] && echo "$BASH_VERSINFO $BASH_VERSION"'],
                               capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        parts = r.stdout.split()
        if r.returncode == 0 and parts and parts[0].isdigit() and int(parts[0]) >= 4:
            return c
    return None


BASH = find_bash()


class Env(unittest.TestCase):
    def test_env_file_is_what_gen_data_writes(self):
        self.assertEqual(ENV.read_text(encoding="utf-8"), anchors_env.text(), "run python tools/gen_data.py")

    def test_gen_data_check_covers_the_env_file(self):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "gen_data.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_every_anchor_is_there(self):
        anchors = {k for k, v in tomllib.loads(ANCHORS.read_text(encoding="utf-8")).items() if k != "keepout" and isinstance(v, dict)}
        env = env_table()
        for a in anchors:
            self.assertIn(f"anchor.{a}.x", env)
            self.assertIn(f"anchor.{a}.z", env)
        self.assertFalse([k for k in env if k.startswith("anchor.") and k.split(".")[1] not in anchors])

    def test_every_probe_is_there(self):
        env = env_table()
        for pid, row in tomllib.loads(PROBES.read_text(encoding="utf-8")).items():
            for key, value in row.items():
                if key != "what":
                    self.assertEqual(env[f"probe.{pid}.{key}"], str(value))

    def test_the_tests_use_these_anchors(self):
        env = env_table()
        for need in ("tempest", "arrival", "dwargon", "dwargon_throne", "goblin_village", "wayfarers_camp"):
            self.assertIn(f"anchor.{need}.x", env)
        for need in ("chest", "canaat_summit", "paulzero_trunk", "barren_lands", "ring_east", "ring_south", "ring_west",
                     "vanilla_east", "vanilla_south", "coast_in", "coast_out", "sea_east_in", "sea_east_out", "sea_south_in",
                     "sea_south_out"):
            self.assertIn(f"probe.{need}.x", env)


class RconFiles(unittest.TestCase):
    def test_directives_are_well_formed(self):
        for path in sorted(INGAME.glob("*.rcon")):
            for line in rcon_lines(path):
                if line.startswith("@"):
                    self.assertRegex(line, DIRECTIVE, f"{path.name}: {line}")

    def test_import_guard_comes_first(self):
        for path in sorted(INGAME.glob("*.rcon")):
            lines = rcon_lines(path)
            if "@import" in lines:
                self.assertEqual(lines[0], "@import", f"{path.name}: @import must be the first command line")
        self.assertIn("@import", rcon_lines(INGAME / "lerfing.rcon"))
        self.assertIn("@import", rcon_lines(INGAME / "lerfing_sea.rcon"))

    def test_every_token_resolves(self):
        env = env_table()
        used = 0
        for path in sorted(INGAME.glob("*.rcon")):
            for line in rcon_lines(path):
                for m in TOKEN.finditer(line):
                    used += 1
                    kind, ident, field, off = m.group(1), m.group(2), (m.group(3) or "")[1:], m.group(4)
                    if field:
                        self.assertIn(f"{kind}.{ident}.{field}", env, f"{path.name}: {m.group(0)}")
                        if off:
                            self.assertRegex(env[f"{kind}.{ident}.{field}"], r"^-?\d+$", f"{path.name}: offset on {m.group(0)}")
                    else:
                        self.assertIsNone(off, f"{path.name}: offset without a field: {m.group(0)}")
                        self.assertIn(f"{kind}.{ident}.x", env, f"{path.name}: {m.group(0)}")
                self.assertNotRegex(TOKEN.sub("", line), r"\$\{", f"{path.name}: unparsed token in {line}")
        self.assertGreater(used, 50)

    def test_no_old_geometry_left(self):
        """The overworld spots of the old generated continent (Tempest at 0 0, the old arrival, Dwargon's old gate and throne
        room, the old rim camp, the fixed forceload boxes) must not come back in a command line."""
        old = [r"\b271 -?624\b", r"\b272 72 -623\b", r"\b435 -1000\b", r"\b435 -1106\b", r"\b434 -1036\b", r"\b285 -612\b",
               r"forceload (add|remove) -?16 -48 47 0", r"forceload (add|remove) 3 -19 8 -16", r"forceload (add|remove) -984 -168",
               r"\btp \S+ 600 120 600\b", r"\btp \S+ (100|102|300) 100 100\b", r"\bat 0 0 tempest\b", r"edit 0 -7", r"edit 200 200",
               r"continent 0 0 yes", r"continent 0,0 yes", r"\b0 0 -7 positioned"]
        for path in sorted(INGAME.glob("*.rcon")):
            for line in rcon_lines(path):
                for pat in old:
                    self.assertNotRegex(line, pat, f"{path.name}: {line}")


class Probes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probes = tomllib.loads(PROBES.read_text(encoding="utf-8"))
        cls.canon = json.loads(CANON.read_text(encoding="utf-8"))
        cls.anchor_data = tomllib.loads(ANCHORS.read_text(encoding="utf-8"))
        lines = GRID.read_text(encoding="utf-8").splitlines()
        m = next(re.match(r"# origin (\d+) (\d+)", t) for t in lines if t.startswith("# origin"))
        cls.oc, cls.orow = int(m[1]), int(m[2])
        cls.rows = [t for t in lines if not t.startswith("#")]
        land = [(c, r) for r, row in enumerate(cls.rows) for c, ch in enumerate(row) if ch != "."]
        cls.land_x0 = (min(c for c, _ in land) - cls.oc) * 16
        cls.land_x1 = (max(c for c, _ in land) + 1 - cls.oc) * 16
        cls.land_z0 = (min(r for _, r in land) - cls.orow) * 16
        cls.land_z1 = (max(r for _, r in land) + 1 - cls.orow) * 16

    def cell(self, x, z):
        c, r = self.oc + (x >> 4), self.orow + (z >> 4)
        return self.rows[r][c] if 0 <= r < len(self.rows) and 0 <= c < len(self.rows[r]) else "."

    def on_continent(self, x, z):
        """CanonGrid.ownerCell != 0: a nation's land, or '.'/'~' within reach of one (coastal water: 128 blocks)."""
        ch = self.cell(x, z)
        if ch.isalpha():
            return True
        reach = 64 if ch == "~" else TERRITORIAL_WATERS // 16 + 1
        best = None
        for dr in range(-reach, reach + 1):
            for dc in range(-reach, reach + 1):
                if self.cell(x + dc * 16, z + dr * 16).isalpha():
                    d = math.hypot(dc, dr) * 16
                    best = d if best is None else min(best, d)
        return best is not None and (ch == "~" or best <= TERRITORIAL_WATERS)

    def canon_weight(self, x, z):
        """CanonGrid.canonWeight: 1 within `ring` of the land bbox, 0 beyond ring + blend, smoothstep between."""
        ring, blend = self.canon["ring"], self.canon["blend"]
        dx = max(self.land_x0 - x, x - self.land_x1, 0)
        dz = max(self.land_z0 - z, z - self.land_z1, 0)
        e = math.hypot(dx, dz)
        if e <= ring:
            return 1.0
        if e >= ring + blend:
            return 0.0
        t = (e - ring) / blend
        return 1 - t * t * (3 - 2 * t)

    def of_kind(self, kind):
        return {k: v for k, v in self.probes.items() if v["kind"] == kind}

    # --- the data ----------------------------------------------------------------------------------------------------

    def test_ids_and_fields(self):
        kinds = {"block", "biome", "seam", "ring", "vanilla", "coast"}
        for pid, p in self.probes.items():
            with self.subTest(probe=pid):
                self.assertRegex(pid, r"^[a-z0-9_]+$")
                self.assertIn(p["kind"], kinds)
                self.assertTrue(p.get("what"), "every probe says why it is there")
                if p["kind"] in ("block", "seam"):
                    self.assertTrue(all(isinstance(p[k], int) for k in "xyz") and p["block"].startswith("minecraft:"))
                if p["kind"] == "biome":
                    self.assertRegex(p["biome"], r"^[a-z_]+:[a-z_]+$")
                if p["kind"] in ("ring", "vanilla"):
                    self.assertIn("weight", p)
                if p["kind"] == "coast":
                    self.assertIn(p["inside"], ("yes", "no"))

    def test_the_inner_tiles_hold_the_block_probes(self):
        x0, z0, x1, z1 = self.canon["lerfing"]["inner"]
        for pid, p in {**self.of_kind("block"), **self.of_kind("biome"), **self.of_kind("seam")}.items():
            inside = x0 <= p["x"] < x1 and z0 <= p["z"] < z1
            with self.subTest(probe=pid):
                if pid.endswith("_out"):
                    self.assertFalse(inside, "the far side of the seam is the generator's")
                else:
                    self.assertTrue(inside, "his chunks")
        self.assertEqual((x0, z0, x1, z1), (-8064, -6016, 8192, 6528))

    def test_seam_probes_straddle_the_edge(self):
        x0, z0, x1, z1 = self.canon["lerfing"]["inner"]
        p = self.probes
        self.assertTrue(p["sea_east_in"]["x"] < x1 <= p["sea_east_out"]["x"])
        self.assertTrue(p["sea_south_in"]["z"] < z1 <= p["sea_south_out"]["z"])
        self.assertEqual(p["sea_east_in"]["z"], p["sea_east_out"]["z"])
        self.assertEqual(p["sea_south_in"]["x"], p["sea_south_out"]["x"])
        for pid in ("sea_east_in", "sea_east_out", "sea_south_in", "sea_south_out"):
            self.assertEqual(p[pid]["y"], 64, "his sea is topped at y 64 (probe.py on the import: top_block water, water_y 64)")
            self.assertEqual(p[pid]["block"], "minecraft:water")

    def test_ring_and_vanilla_points_have_the_canon_weight(self):
        ring, blend = self.canon["ring"], self.canon["blend"]
        for pid, p in {**self.of_kind("ring"), **self.of_kind("vanilla")}.items():
            with self.subTest(probe=pid):
                self.assertEqual(self.canon_weight(p["x"], p["z"]), p["weight"])
                dx = max(self.land_x0 - p["x"], p["x"] - self.land_x1, 0)
                dz = max(self.land_z0 - p["z"], p["z"] - self.land_z1, 0)
                e = math.hypot(dx, dz)
                if p["kind"] == "ring":
                    self.assertLess(e, ring - 100, "clear of the smoothstep so a small ring change keeps it a ring point")
                    self.assertGreater(e, 1000, "open sea well off the coast")
                else:
                    self.assertGreater(e, ring + blend + 100)
                self.assertEqual(self.cell(p["x"], p["z"]), ".", "open sea in the grid")
                self.assertFalse(self.on_continent(p["x"], p["z"]))

    def test_ring_points_lie_beyond_the_inner_tiles(self):
        x0, z0, x1, z1 = self.canon["lerfing"]["inner"]
        for pid, p in self.of_kind("ring").items():
            with self.subTest(probe=pid):
                self.assertFalse(x0 <= p["x"] < x1 and z0 <= p["z"] < z1, "the generator makes the ring, not his chunks")

    def test_coast_probes_follow_the_continent_rule(self):
        coast = self.of_kind("coast")
        self.assertEqual({v["inside"] for v in coast.values()}, {"yes", "no"})
        for pid, p in coast.items():
            with self.subTest(probe=pid):
                self.assertEqual(self.on_continent(p["x"], p["z"]), p["inside"] == "yes")
        a, b = self.probes["coast_in"], self.probes["coast_out"]
        self.assertEqual(a["x"], b["x"])
        self.assertLess(a["z"], b["z"])
        self.assertTrue(self.cell(a["x"], a["z"]) == "." and self.cell(b["x"], b["z"]) == ".", "both in open sea cells")

    def test_landmark_probes_sit_inside_his_keepout_boxes(self):
        k = self.anchor_data["keepout"]
        c, t = self.probes["chest"], self.probes["paulzero_trunk"]
        box = k["lerfing_spawn_chest"]
        self.assertTrue(box["x0"] <= c["x"] <= box["x1"] and box["z0"] <= c["z"] <= box["z1"])
        box = k["paulzero_grove"]
        self.assertTrue(box["x0"] <= t["x"] <= box["x1"] and box["z0"] <= t["z"] <= box["z1"])
        self.assertEqual(self.cell(c["x"], c["z"]), "U", "Lerfing's chest stands in Ulgracia")
        self.assertEqual(self.cell(t["x"], t["z"]), "S", "the Divine Tree stands in Sarion")

    def test_summit_stays_under_the_build_limit(self):
        self.assertLess(self.probes["canaat_summit"]["y"], 320)

    # --- the rasters (design/data/lerfing, 1 px = 16 blocks) ---------------------------------------------------------------

    def rasters(self):
        if not (RASTERS / "legend.json").is_file():
            self.skipTest("no committed rasters")
        from lerfing import probe as lp
        return lp.Rasters(str(RASTERS))

    def test_probes_against_the_rasters(self):
        r = self.rasters()
        for pid, p in {**self.of_kind("block"), **self.of_kind("biome")}.items():
            col = r.at(p["x"], p["z"])
            with self.subTest(probe=pid):
                self.assertEqual(col["class"], "land", "his land")
                if "biome" in p:
                    self.assertEqual(col["biome"], p["biome"])
                if p["kind"] == "block":
                    self.assertGreaterEqual(p["y"], col["ground_y"] - 16, "not under his ground")
        s = r.at(self.probes["canaat_summit"]["x"], self.probes["canaat_summit"]["z"])
        self.assertAlmostEqual(s["ground_y"], self.probes["canaat_summit"]["y"], delta=8, msg="the summit raster height")
        for pid, p in self.of_kind("seam").items():
            if pid.endswith("_in"):
                with self.subTest(probe=pid):
                    col = r.at(p["x"], p["z"])
                    self.assertEqual(col["class"], "sea")
                    self.assertLess(col["ground_y"], 40, "deep sea")

    def test_anchors_stand_where_the_tests_expect(self):
        """lerfing.rcon: Tempest in the core, the old goblin village in the dark band, the arrival on the rim, Dwargon's gate on
        the Canaat's rock. At the rasters' 16-block resolution (the exact columns: probe.py --world)."""
        r = self.rasters()
        a = {k: v for k, v in self.anchor_data.items() if k != "keepout"}
        at = lambda name: r.at(a[name]["x"], a[name]["z"])
        self.assertEqual(at("tempest")["biome"], "tensura:ancient_forest")
        self.assertEqual(at("goblin_village")["biome"], "minecraft:dark_forest")
        self.assertNotIn(at("arrival")["biome"], ("tensura:ancient_forest", "minecraft:dark_forest"))
        self.assertEqual(at("dwargon")["biome"], "minecraft:stony_peaks")
        for name in ("tempest", "goblin_village", "arrival", "dwargon"):
            self.assertEqual(at(name)["class"], "land", name)
        # the arrival is the rim, 600 + fade from Tempest (canon_regions.json J zones)
        t, ar = a["tempest"], a["arrival"]
        self.assertGreater(math.hypot(ar["x"] - t["x"], ar["z"] - t["z"]), 600 + self.canon["regions"]["J"]["zones"]["fade"])
        g = a["goblin_village"]
        self.assertTrue(200 < math.hypot(g["x"] - t["x"], g["z"] - t["z"]) < 600)

    def test_world_columns_when_an_import_is_at_hand(self):
        """$TTL_LERFING_WORLD = the import tool's output folder (holds region/): the exact blocks and biomes of the probes."""
        world = os.environ.get("TTL_LERFING_WORLD")
        if not world or not (Path(world) / "region").is_dir():
            self.skipTest("set TTL_LERFING_WORLD to an import output to read the probes from its region files")
        from lerfing import nbt
        from lerfing.common import block_bits, value_at
        from lerfing.probe import World
        w = World(world)

        def block(x, y, z):
            scan, _ = w.chunk(x >> 4, z >> 4)
            for sec in scan.sections:
                if sec.y == y >> 4:
                    pal, data = nbt.block_states(scan, sec) or ([], b"")
                    bits = block_bits(len(pal))
                    i = value_at(data, ((y & 15) * 16 + (z & 15)) * 16 + (x & 15), bits) if bits else 0
                    return pal[i]["Name"]
            return "minecraft:air"

        for pid, p in {**self.of_kind("block"), **self.of_kind("seam")}.items():
            if pid.endswith("_out"):
                continue
            with self.subTest(probe=pid):
                self.assertEqual(block(p["x"], p["y"], p["z"]), p["block"])
                if p["kind"] == "seam":
                    self.assertEqual(block(p["x"], p["y"] + 1, p["z"]), "minecraft:air")
        for pid, p in {**self.of_kind("block"), **self.of_kind("biome")}.items():
            if "biome" in p:
                with self.subTest(probe=pid):
                    self.assertEqual(w.at(p["x"], p["z"])["biome"], p["biome"])
        for name, biome in (("tempest", "tensura:ancient_forest"), ("goblin_village", "minecraft:dark_forest"),
                            ("dwargon", "minecraft:stony_peaks")):
            a = self.anchor_data[name]
            with self.subTest(anchor=name):
                self.assertEqual(w.at(a["x"], a["z"])["biome"], biome)
        a = self.anchor_data["arrival"]
        col = w.at(a["x"], a["z"])
        self.assertNotIn(col["biome"], ("tensura:ancient_forest", "minecraft:dark_forest"))
        self.assertIsNone(col["water_y"], "the arrival is dry")
        self.assertEqual(w.at(self.probes["chest"]["x"], self.probes["chest"]["z"])["status"], "minecraft:carvers")


@unittest.skipUnless(BASH, "no bash 4.2+ on the PATH (set TTL_BASH)")
class Runner(unittest.TestCase):
    """tools/test_lib.sh with a fake `rcon`: the server never answers a real one here."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.env = self.dir / "anchors.env"
        self.env.write_text(
            "anchor.tempest.x=1720\nanchor.tempest.z=900\nanchor.arrival.x=1780\nanchor.arrival.z=-150\n"
            "probe.chest.x=-453\nprobe.chest.y=73\nprobe.chest.z=979\nprobe.chest.block=minecraft:chest\n"
            "probe.ring.x=9000\nprobe.ring.z=0\nprobe.ring.weight=1.0\n", encoding="utf-8", newline="\n")
        self.log = self.dir / "rcon.log"

    def tearDown(self):
        self.tmp.cleanup()

    def bash(self, body, fake="rcon() { echo \"$1\" >> \"$LOG\"; echo ok; }", env=None):
        script = (f'set -uo pipefail\nLIB="{LIB.as_posix()}"\nLOG="{self.log.as_posix()}"\nST="{(self.dir / "st").as_posix()}"\n'
                  f'export TTL_ANCHORS_ENV="{self.env.as_posix()}"\nsource "$LIB"\nnap() {{ echo "(sleep $1)" >> "$LOG"; }}\n'
                  f"plain() {{ sed 's/\\[[0-9;]*m//g'; }}\n{fake}\n{body}\n")
        e = {k: v for k, v in os.environ.items() if k != "TTL_IMPORTED"}
        e.update(env or {})
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True, env=e, timeout=120)
        return r.returncode, r.stdout, r.stderr

    def rcon_file(self, text):
        p = self.dir / "t.rcon"
        p.write_text(text, encoding="utf-8", newline="\n")
        return p.as_posix()

    def sent(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def test_scripts_parse(self):
        for f in (LIB, SERVER):
            r = subprocess.run([BASH, "-n", f.as_posix()], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f.name}: {r.stderr}")

    def test_server_sh_sources_the_runner(self):
        text = SERVER.read_text(encoding="utf-8")
        self.assertIn('source "$(dirname "$0")/test_lib.sh"', text)
        ingame = (ROOT / "tools" / "ingame.sh").read_text(encoding="utf-8")
        self.assertIn("skipped", ingame, "test-all must not count a skipped @import test as failing")
        local = (ROOT / "tools" / "local.sh").read_text(encoding="utf-8")
        self.assertIn("tools/test_lib.sh", local, "local.sh must run the same runner as staging")

    def test_expand_tokens(self):
        cases = {
            "tp b ${anchor:tempest.x} 100 ${anchor:tempest.z}": "tp b 1720 100 900",
            "forceload add ${anchor:tempest}": "forceload add 1720 900",
            "x ${anchor:tempest.x+100} ${anchor:tempest.z-19}": "x 1820 881",
            "x ${anchor:arrival.z-5} ${anchor:arrival.z+5}": "x -155 -145",
            "if block ${probe:chest} ${probe:chest.block}": "if block -453 73 979 minecraft:chest",
            "y ${probe:chest.y+1}": "y 74",
            "ring ${probe:ring}": "ring 9000 0",
            "c ${anchor:tempest.x},${anchor:tempest.z}": "c 1720,900",
            "no tokens at all": "no tokens at all",
        }
        for src, want in cases.items():
            rc, out, err = self.bash(f'expand_tokens {shlex.quote(src)}')
            self.assertEqual((rc, out), (0, want), f"{src}: {err}")

    def test_expand_tokens_refuses_what_it_cannot_resolve(self):
        for src in ("${anchor:nowhere}", "${anchor:tempest.y}", "${probe:chest.block+1}", "${anchor:tempest+5}", "${probe:chest.nothing}"):
            rc, out, err = self.bash(f'expand_tokens {shlex.quote(src)}; echo "rc=$?"')
            self.assertIn("rc=1", out, src)
            self.assertIn("ttl: ", out, src)

    def test_run_test_sends_expanded_lines_and_flags_unknown_tokens(self):
        f = self.rcon_file("# comment\n\ntp bot ${anchor:tempest.x+1} 70 ${anchor:tempest.z}\nsay ${anchor:nowhere}\nsay after\n")
        rc, out, err = self.bash(f'run_test "{f}"')
        self.assertEqual(self.sent(), ["tp bot 1721 70 900", "say after"])
        self.assertIn("ttl: unknown token ${anchor:nowhere}", out)

    def test_expect_retries_until_the_reply_matches(self):
        fake = ('rcon() { echo "$1" >> "$LOG"; n=$(cat "$ST" 2>/dev/null || echo 0); echo $((n + 1)) > "$ST";\n'
                '  if [ "$n" -ge 2 ]; then echo "[ttl] canon map: imported chunk: stored biome tensura:ancient_forest at y65";\n'
                '  else echo "imported, not loaded"; fi; }')
        f = self.rcon_file("@expect 10 imported chunk: stored biome tensura:ancient_forest :: ttlmap ${anchor:tempest}\n")
        rc, out, err = self.bash(f'run_test "{f}"', fake)
        self.assertEqual(self.sent().count("ttlmap 1720 900"), 3)
        self.assertEqual(self.sent().count("(sleep 1)"), 2)
        self.assertNotIn("ttl: ", out)

    def test_expect_fails_loudly_after_the_last_try(self):
        f = self.rcon_file("@expect 2 zone core :: ttlregion bot\nsay after\n")
        rc, out, err = self.bash(f'run_test "{f}"', 'rcon() { echo "$1" >> "$LOG"; echo "zone rim (safe)"; }')
        self.assertEqual(self.sent().count("ttlregion bot"), 3, "one try plus two retries")
        self.assertIn("ttl: expected /zone core/ in the reply to: ttlregion bot", out)
        self.assertIn("say after", self.sent(), "the test goes on; the failure is the printed line test-all greps")

    def test_expect_with_zero_seconds_tries_once(self):
        f = self.rcon_file("@expect 0 nothing :: say hi\n")
        rc, out, err = self.bash(f'run_test "{f}"')
        self.assertEqual(self.sent(), ["say hi"])
        self.assertIn("ttl: expected /nothing/", out)

    def test_expect_needs_the_separator(self):
        f = self.rcon_file("@expect 3 oops say hi\n")
        rc, out, err = self.bash(f'run_test "{f}"')
        self.assertIn("ttl: bad @expect line", out)
        self.assertEqual(self.sent(), [])

    def test_unknown_directive_is_a_failure(self):
        f = self.rcon_file("@frobnicate 3\n")
        rc, out, err = self.bash(f'run_test "{f}"')
        self.assertIn("ttl: unknown directive", out)

    def test_until_still_waits_for_a_reply_that_holds(self):
        fake = ('rcon() { echo "$1" >> "$LOG"; n=$(cat "$ST" 2>/dev/null || echo 0); echo $((n + 1)) > "$ST";\n'
                '  if [ "$n" -ge 1 ]; then echo "Test passed"; else echo "Test failed"; fi; }')
        f = self.rcon_file("@until 5 execute if loaded ${anchor:tempest.x} 64 ${anchor:tempest.z}\n")
        rc, out, err = self.bash(f'run_test "{f}"', fake)
        self.assertEqual(self.sent().count("execute if loaded 1720 64 900"), 2)
        self.assertNotIn("ttl: ", out)

    def test_sleep_directive(self):
        f = self.rcon_file("@sleep 3\nsay hi\n")
        rc, out, err = self.bash(f'run_test "{f}"')
        self.assertEqual(self.sent(), ["(sleep 3)", "say hi"])

    IMPORTED = ('rcon() { echo "$1" >> "$LOG"; case "$1" in\n'
                '  "execute in minecraft:overworld if block -453 73 979 minecraft:chest") echo "Test passed" ;;\n'
                '  *) echo ok ;; esac; }')
    PLAIN = IMPORTED.replace('echo "Test passed"', 'echo "Test failed"')

    def test_import_guard_runs_the_test_on_an_imported_world(self):
        f = self.rcon_file("@import\nsay hi\n")
        rc, out, err = self.bash(f'run_test "{f}"', self.IMPORTED)
        sent = self.sent()
        self.assertIn("say hi", sent)
        self.assertNotIn("skipped:", out)
        self.assertEqual(sent[0], "execute in minecraft:overworld run forceload add -453 979")
        self.assertEqual(sent[-2], "execute in minecraft:overworld run forceload remove -453 979", "the check releases its chunk")

    def test_import_guard_skips_the_test_on_any_other_world(self):
        f = self.rcon_file("@import\nsay hi\nsay there\n")
        rc, out, err = self.bash(f'run_test "{f}"', self.PLAIN)
        self.assertNotIn("say hi", self.sent())
        self.assertRegex(out, r"(?m)^skipped: ")
        self.assertNotIn("ttl: ", out, "a skip is not a failure for test-all (its failure grep is 'ttl: ')")

    def test_import_guard_waits_for_an_unloaded_chunk_and_then_runs_anyway(self):
        fake = ('rcon() { echo "$1" >> "$LOG"; case "$1" in *"if block"*) echo "That position is not loaded" ;; *) echo ok ;; esac; }')
        f = self.rcon_file("@import\nsay hi\n")
        rc, out, err = self.bash(f'run_test "{f}"', fake)
        self.assertEqual(sum(1 for s in self.sent() if "if block" in s), 60)
        self.assertIn("say hi", self.sent(), "unknown counts as imported: the test runs and fails visibly")

    def test_import_override_variable(self):
        f = self.rcon_file("@import\nsay hi\n")
        rc, out, err = self.bash(f'run_test "{f}"', self.PLAIN, env={"TTL_IMPORTED": "1"})
        self.assertIn("say hi", self.sent())
        self.log.unlink()
        rc, out, err = self.bash(f'run_test "{f}"', self.IMPORTED, env={"TTL_IMPORTED": "0"})
        self.assertNotIn("say hi", self.sent())
        self.assertRegex(out, r"(?m)^skipped: ")

    def test_every_rcon_file_expands_with_the_real_env(self):
        """The real tests/anchors.env and every real line: no token is left unresolved, nothing is printed as a failure."""
        lines = [t for p in sorted(INGAME.glob("*.rcon")) for t in rcon_lines(p) if "${" in t]
        self.assertGreater(len(lines), 50)
        data = self.dir / "lines.txt"
        data.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        script = (f'set -uo pipefail\nsource "{LIB.as_posix()}"\nTTL_ANCHORS_ENV="{ENV.as_posix()}"\n'
                  f'while IFS= read -r l; do expand_tokens "$l"; echo; done < "{data.as_posix()}"')
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout.splitlines()
        self.assertEqual(len(out), len(lines))
        for src, got in zip(lines, out):
            self.assertNotIn("ttl: ", got, src)
            self.assertNotIn("${", got, src)
            self.assertNotRegex(got, r"(?<![\w-])None(?![\w-])", src)


if __name__ == "__main__":
    unittest.main()
