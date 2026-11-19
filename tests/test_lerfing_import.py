"""Lerfing import tool (tools/lerfing/import.py, design/architecture/lerfing-import.md §1.2): python -I -m unittest discover -s tests

Synthetic 1.18 proto chunks in tiny regions: the status rename, the biome repaint (Nether/End rules, Jura rings,
water and caves kept), the 1.18 palette re-pack, byte-exact copying of everything else, the --verify mode and the
CLI (inner tiles only, nothing but region files written, idempotent).
"""
import importlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from lerfing import nbt  # noqa: E402
from lerfing import common  # noqa: E402
from lerfing.common import Rules, pack, unpack  # noqa: E402

imp = importlib.import_module("lerfing.import")
probe = importlib.import_module("lerfing.probe")

STONE = [("Name", 8, "minecraft:stone")]
AIR = [("Name", 8, "minecraft:air")]
WATER = [("Name", 8, "minecraft:water"), ("Properties", 10, [("level", 8, "0")])]
GROUND_TOP = 63          # stone up to y 63 in every synthetic chunk


def block_section(y, wet=False):
    """Sections -4..3: stone below y 64; section 4 (y 64..79) is water up to y 70 when wet, else air."""
    if y < 4:
        return [("palette", 9, (10, [STONE]))]
    if not wet:
        return [("palette", 9, (10, [AIR]))]
    idx = [(1 if (i >> 8) <= 6 else 0) for i in range(4096)]
    return [("palette", 9, (10, [AIR, WATER])), ("data", 12, pack(idx, 4))]


def biomes(palette, cells=None):
    entries = [("palette", 9, (8, list(palette)))]
    bits = common.biome_bits(len(palette))
    if bits:
        entries.append(("data", 12, pack(cells, bits)))
    return entries


def chunk(cx, cz, biome_sections, status="liquid_carvers", wet=False, extra=True):
    """biome_sections: {Y: (palette, cells or None)} for Y in -4..5 (others plains)."""
    secs = []
    for y in range(-4, 6):
        pal, cells = biome_sections.get(y, (["minecraft:plains"], None))
        secs.append([("Y", 1, y), ("block_states", 10, block_section(y, wet)), ("biomes", 10, biomes(pal, cells)),
                     ("BlockLight", 7, bytes(range(256)) * 8)])
    entries = [("DataVersion", 3, 2860), ("xPos", 3, cx), ("zPos", 3, cz), ("yPos", 3, -4),
               ("Status", 8, status), ("LastUpdate", 4, 123456789012), ("sections", 9, (10, secs))]
    if extra:
        entries += [("block_entities", 9, (10, [[("id", 8, "minecraft:chest"), ("x", 3, cx * 16 + 3),
                                                  ("y", 3, 64), ("z", 3, cz * 16 + 5), ("keepPacked", 1, 0)]])),
                    ("PostProcessing", 9, (9, [(2, [1, 2]), (2, [])])),
                    ("structures", 10, [("References", 10, []), ("starts", 10, [])]),
                    ("InhabitedTime", 4, 0), ("isLightOn", 1, 0), ("ratio", 5, 0.5), ("big", 6, 2.25),
                    ("ints", 11, [1, 2, 3]), ("CarvingMasks", 10, [("AIR", 12, [7, 8])])]
    return nbt.enc_root(entries)


def region(rx, rz, chunks):
    """chunks: {(cx, cz): raw nbt}; returns region file bytes (zlib)."""
    out = {}
    for (cx, cz), raw in chunks.items():
        assert (cx >> 5, cz >> 5) == (rx, rz)
        out[(cx & 31, cz & 31)] = (2, nbt.compress(raw), 1700000000)
    return nbt.write_region(out)


def rules(**over):
    data = json.loads((ROOT / "design" / "data" / "lerfing" / "repaint.json").read_text(encoding="utf-8"))
    data.update(over)
    return Rules(data)


def stored(region_bytes):
    """{(cx, cz): (scan, raw)} of a region file."""
    out = {}
    for (lx, lz), (comp, payload, _ts) in nbt.read_region(region_bytes).items():
        raw = nbt.decompress(comp, payload)
        scan = nbt.scan_chunk(raw)
        out[(scan.x, scan.z)] = (scan, raw)
    return out


def biome_cells(scan, y):
    sec = next(s for s in scan.sections if s.y == y)
    pal, idx = common.section_biomes(sec)
    return pal, [pal[i] for i in idx], dict((n, v) for _t, n, _r, v in sec.biomes)


class PackTest(unittest.TestCase):
    def test_round_trip_and_no_spanning(self):
        for bits in range(1, 7):
            vals = [(i * 7) % (1 << bits) for i in range(64)]
            raw = pack(vals, bits)
            self.assertEqual(len(raw), 8 * -(-64 // (64 // bits)), bits)
            self.assertEqual(unpack(raw, 64, bits), vals)
        # 3 bits: 21 values per long, the 22nd starts the next long (1.16+ layout, no spanning)
        raw = pack([7] * 22, 3)
        self.assertEqual(len(raw), 16)
        self.assertEqual(int.from_bytes(raw[:8], "big") >> 63, 0)
        self.assertEqual(int.from_bytes(raw[8:], "big"), 7)

    def test_value_noise_range_and_determinism(self):
        vals = [common.value_noise(x * 13, z * 17, 64, 5) for x in range(40) for z in range(40)]
        self.assertTrue(all(-1 <= v < 1 for v in vals))
        self.assertEqual(vals, [common.value_noise(x * 13, z * 17, 64, 5) for x in range(40) for z in range(40)])


class RepaintTest(unittest.TestCase):
    def run_region(self, rx, rz, chunks, rs=None):
        src = region(rx, rz, chunks)
        out, stats, samples = imp.process_region(src, rx, rz, rs or rules())
        return src, out, stats, samples

    def test_status_rename_and_full_kept(self):
        a, b = (100, 40), (101, 40)
        _, out, stats, _ = self.run_region(3, 1, {a: chunk(*a, {}), b: chunk(*b, {}, status="full")})
        got = stored(out)
        self.assertEqual(got[a][0].status, "minecraft:carvers")
        self.assertEqual(got[b][0].status, "full")
        self.assertEqual(stats["status_after"], {"minecraft:carvers": 1, "full": 1})

    def test_nether_and_end_rules(self):
        canaat = (2500 >> 4, -1432 >> 4)            # r.4.-3
        ne = (5000 >> 4, -2000 >> 4)                # r.9.-4, inside the NE volcano box
        sw = (-3000 >> 4, 1500 >> 4)                # r.-6.2, the crystal hills
        west = (-6000 >> 4, 0)                      # r.-12.0, the Barren Lands
        cells = [i % 2 for i in range(64)]
        cases = {
            canaat: ({0: (["minecraft:soul_sand_valley"], None)}, "minecraft:stony_peaks"),
            ne: ({0: (["minecraft:nether_wastes", "minecraft:plains"], cells)}, "minecraft:badlands"),
            sw: ({0: (["minecraft:nether_wastes", "minecraft:plains"], cells)}, "minecraft:windswept_gravelly_hills"),
            west: ({0: (["minecraft:the_end"], None)}, "tensura:barren_land"),
        }
        for pos, (secs, want) in cases.items():
            rx, rz = pos[0] >> 5, pos[1] >> 5
            _, out, stats, _ = self.run_region(rx, rz, {pos: chunk(*pos, secs)})
            scan = stored(out)[pos][0]
            pal, names, entries = biome_cells(scan, 0)
            self.assertIn(want, pal, pos)
            for n in names:
                self.assertNotIn(n, ("minecraft:soul_sand_valley", "minecraft:nether_wastes", "minecraft:the_end"))
            if len(secs[0][0]) == 2:
                self.assertEqual(names, [want if c == 0 else "minecraft:plains" for c in cells])
                self.assertEqual(len(entries["data"]), 8)
            else:
                self.assertEqual(pal, [want])
                self.assertNotIn("data", entries)
            self.assertGreater(sum(stats["transitions"].values()), 0)

    def test_palette_merge_drops_data(self):
        pos = (2500 >> 4, -1432 >> 4)
        cells = [i % 2 for i in range(64)]
        _, out, _, _ = self.run_region(4, -3, {pos: chunk(*pos, {1: (
            ["minecraft:soul_sand_valley", "minecraft:stony_peaks"], cells)})})
        pal, names, entries = biome_cells(stored(out)[pos][0], 1)
        self.assertEqual(pal, ["minecraft:stony_peaks"])
        self.assertNotIn("data", entries)

    def test_palette_repack_bits(self):
        pos = (2500 >> 4, -1432 >> 4)
        five = ["minecraft:soul_sand_valley", "minecraft:plains", "minecraft:desert", "minecraft:forest",
                "minecraft:jungle"]
        cells5 = [i % 5 for i in range(64)]
        merge = ["minecraft:soul_sand_valley", "minecraft:stony_peaks", "minecraft:plains", "minecraft:desert",
                 "minecraft:forest"]
        _, out, _, _ = self.run_region(4, -3, {pos: chunk(*pos, {0: (five, cells5), 1: (merge, cells5)})})
        scan = stored(out)[pos][0]
        pal, names, entries = biome_cells(scan, 0)       # 5 entries stay 5: 3 bits, 21 per long, 4 longs
        self.assertEqual(len(pal), 5)
        self.assertEqual(len(entries["data"]), 32)
        self.assertEqual(names, [("minecraft:stony_peaks" if c == 0 else five[c]) for c in cells5])
        pal, names, entries = biome_cells(scan, 1)       # 5 → 4 entries: 2 bits, 2 longs
        self.assertEqual(len(pal), 4)
        self.assertEqual(len(entries["data"]), 16)
        self.assertEqual(names, [("minecraft:stony_peaks" if c <= 1 else merge[c]) for c in cells5])

    def test_jura_rings(self):
        core = (1720 >> 4, 900 >> 4)                # Tempest
        band = (1720 >> 4, 550 >> 4)                # 350 north: dark band
        lake = (1900 >> 4, 600 >> 4)                # 350 away, in the band but under water
        rim = ((1720 - 1000) >> 4, 900 >> 4)        # 1000 west (r.1.1): Lerfing's own biome
        cells = [i % 2 for i in range(64)]
        chunks = {core: chunk(*core, {-2: (["minecraft:lush_caves", "minecraft:plains"], cells),
                                      2: (["minecraft:river", "minecraft:plains"], cells)}),
                  band: chunk(*band, {3: (["minecraft:badlands"], None)}), lake: chunk(*lake, {}, wet=True)}
        _, out, stats, samples = self.run_region(3, 1, chunks)
        got = stored(out)
        got.update(stored(self.run_region(1, 1, {rim: chunk(*rim, {})})[1]))
        pal, names, _ = biome_cells(got[core][0], 0)
        self.assertEqual(pal, ["tensura:ancient_forest"])
        _, names, _ = biome_cells(got[core][0], -2)      # caves keep their biome under the core
        self.assertEqual(names, ["minecraft:lush_caves" if c == 0 else "tensura:ancient_forest" for c in cells])
        _, names, _ = biome_cells(got[core][0], 2)       # river cells are never repainted
        self.assertEqual(names, ["minecraft:river" if c == 0 else "tensura:ancient_forest" for c in cells])
        for y in (0, 3):
            self.assertEqual(biome_cells(got[band][0], y)[0], ["minecraft:dark_forest"])
        self.assertEqual(biome_cells(got[rim][0], 0)[0], ["minecraft:plains"])
        self.assertEqual(biome_cells(got[lake][0], 0)[0], ["minecraft:plains"])   # water over the ground
        self.assertIn("minecraft:badlands > minecraft:dark_forest", stats["transitions"])
        # raster samples: dry land vs water, ground y 63
        self.assertEqual(samples[(core[0] & 31, core[1] & 31)][:2], [common.LAND, GROUND_TOP])
        self.assertEqual(samples[(lake[0] & 31, lake[1] & 31)][0], common.SEA)

    def test_ring_boundary_creates_data(self):
        rs = rules(jura={"centre": [2, 2], "core": 6, "band": 100, "wobble": 0, "core_biome": "tensura:ancient_forest",
                         "band_biome": "minecraft:dark_forest"}, spots=[])
        _, out, _, _ = self.run_region(0, 0, {(0, 0): chunk(0, 0, {})}, rs)
        pal, names, entries = biome_cells(stored(out)[(0, 0)][0], 0)
        self.assertEqual(sorted(pal), ["minecraft:dark_forest", "tensura:ancient_forest"])
        self.assertEqual(len(entries["data"]), 8)
        for i, n in enumerate(names):
            x, z = (i & 3) * 4 + 2, ((i >> 2) & 3) * 4 + 2
            want = "tensura:ancient_forest" if ((x - 2) ** 2 + (z - 2) ** 2) ** 0.5 < 6 else "minecraft:dark_forest"
            self.assertEqual(n, want, i)

    def test_bytes_untouched_elsewhere(self):
        pos = (1720 >> 4, 900 >> 4)
        src, out, _, _ = self.run_region(3, 1, {pos: chunk(*pos, {0: (["minecraft:soul_sand_valley"], None)})})
        (sscan, sraw), = stored(src).values()
        (oscan, oraw), = stored(out).values()
        self.assertNotEqual(sraw, oraw)
        self.assertEqual(imp._strip(sraw, sscan), imp._strip(oraw, oscan))
        self.assertEqual(nbt.parse(oraw)["block_entities"], nbt.parse(sraw)["block_entities"])
        self.assertEqual(nbt.read_region(out)[(pos[0] & 31, pos[1] & 31)][2], 1700000000)   # timestamp kept

    def test_border_chunks_dropped(self):
        inner, border = (-504, -376), (-505, -376)
        _, out, stats, _ = self.run_region(-16, -12, {inner: chunk(*inner, {}),
                                                      border: chunk(*border, {}, status="full")})
        self.assertEqual(set(stored(out)), {inner})
        self.assertEqual(stats["dropped_border"], {"full": 1})

    def test_idempotent(self):
        pos = (1720 >> 4, 900 >> 4)
        _, out, _, _ = self.run_region(3, 1, {pos: chunk(*pos, {0: (["minecraft:nether_wastes"], None)})})
        again, stats, _ = imp.process_region(out, 3, 1, rules())
        self.assertEqual(again, out)
        self.assertEqual(stats["chunks_rewritten"], 0)


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.pos = (1720 >> 4, 900 >> 4)
        self.src = region(3, 1, {self.pos: chunk(*self.pos, {0: (["minecraft:the_end", "minecraft:plains"],
                                                                 [i % 2 for i in range(64)])})})
        self.rs = rules(rules=[{"from": "minecraft:the_end", "to": "tensura:barren_land"}])
        self.out, _, _ = imp.process_region(self.src, 3, 1, self.rs)

    def test_clean_output_passes(self):
        problems, counts = imp.verify_region(self.out, 3, 1, self.rs, self.src)
        self.assertEqual(problems, [])
        self.assertEqual(counts["byte-identical outside Status/biomes"], 1)
        self.assertEqual(counts["status minecraft:carvers"], 1)

    def test_source_fails(self):
        problems, _ = imp.verify_region(self.src, 3, 1, self.rs)
        text = "\n".join(problems)
        self.assertIn("status 'liquid_carvers'", text)
        self.assertIn("forbidden biome minecraft:the_end", text)

    def rewrite(self, biome_entries):
        (scan, raw), = stored(self.out).values()
        sec = next(s for s in scan.sections if s.y == 0)
        raw2 = nbt.splice(raw, [(sec.biomes_span[0], sec.biomes_span[1], nbt.enc_payload(10, biome_entries))])
        return nbt.write_region({(self.pos[0] & 31, self.pos[1] & 31): (2, nbt.compress(raw2), 0)})

    def test_bad_index_and_short_data_fail(self):
        bad = self.rewrite([("palette", 9, (8, ["minecraft:plains", "minecraft:forest", "minecraft:desert"])),
                            ("data", 12, pack([3] * 64, 2))])
        problems, _ = imp.verify_region(bad, 3, 1, self.rs)
        self.assertTrue(any("biome index 3 >= palette 3" in p for p in problems), problems)
        short = self.rewrite([("palette", 9, (8, ["minecraft:plains", "minecraft:forest", "minecraft:desert"])),
                              ("data", 12, [0])])
        problems, _ = imp.verify_region(short, 3, 1, self.rs)
        self.assertTrue(any("biome data 1 longs, need 2" in p for p in problems), problems)

    def test_byte_change_elsewhere_fails(self):
        (scan, raw), = stored(self.out).values()
        i = raw.index(b"minecraft:chest")
        raw2 = raw[:i] + b"minecraft:chess" + raw[i + 15:]
        bad = nbt.write_region({(self.pos[0] & 31, self.pos[1] & 31): (2, nbt.compress(raw2), 0)})
        problems, _ = imp.verify_region(bad, 3, 1, self.rs, self.src)
        self.assertTrue(any("differ from the source" in p for p in problems), problems)

    def test_overlapping_sectors_fail(self):
        a, b = (100, 40), (101, 40)
        reg = bytearray(region(3, 1, {a: chunk(*a, {}, extra=False), b: chunk(*b, {}, extra=False)}))
        reg[(b[0] & 31) * 4 + (b[1] & 31) * 128:(b[0] & 31) * 4 + (b[1] & 31) * 128 + 4] = \
            reg[(a[0] & 31) * 4 + (a[1] & 31) * 128:(a[0] & 31) * 4 + (a[1] & 31) * 128 + 4]
        problems, _ = imp.verify_region(bytes(reg), 3, 1, self.rs)
        self.assertTrue(any("shared by slots" in p for p in problems), problems)


class CliTest(unittest.TestCase):
    def test_import_verify_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "lerfing.zip")
            core, canaat = (1720 >> 4, 900 >> 4), (2500 >> 4, -1432 >> 4)
            outer = (-17 * 32, 0)       # r.-17.0: WorldPainter's border tile, not an inner region
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("Tensura By Lerfing/level.dat", b"\x1f\x8b not read")
                z.writestr("Tensura By Lerfing/entities/r.3.1.mca", b"\0" * 8192)
                z.writestr("Tensura By Lerfing/region/r.3.1.mca", region(3, 1, {core: chunk(*core, {})}))
                z.writestr("Tensura By Lerfing/region/r.4.-3.mca", region(4, -3, {canaat: chunk(*canaat, {
                    y: (["minecraft:soul_sand_valley"], None) for y in range(-4, 6)})}))
                z.writestr("Tensura By Lerfing/region/r.-17.0.mca", region(-17, 0, {outer: chunk(*outer, {})}))
            out = os.path.join(tmp, "world")
            with self._quiet():
                self.assertEqual(imp.main([zpath, "--out", out, "--workers", "1"]), 0)
            self.assertEqual(sorted(os.listdir(os.path.join(out, "region"))), ["r.3.1.mca", "r.4.-3.mca"])
            self.assertFalse(os.path.exists(os.path.join(out, "level.dat")))
            self.assertFalse(os.path.exists(os.path.join(out, "entities")))
            report = json.loads(Path(out, "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status_after"], {"minecraft:carvers": 2})
            self.assertIn("Tensura By Lerfing/level.dat", report["not_copied"])
            self.assertEqual(report["kept_block_entities"][0][0], "minecraft:chest")
            self.assertIn("minecraft:soul_sand_valley > minecraft:stony_peaks", report["repaint_cells_3d"])
            manifest = Path(out, "sha256.txt").read_text(encoding="utf-8").split()
            self.assertIn("region/r.3.1.mca", manifest)
            before = Path(out, "region", "r.3.1.mca").read_bytes()
            with self._quiet():
                imp.main([zpath, "--out", out, "--workers", "1"])
                self.assertEqual(imp.main([zpath, "--out", out, "--workers", "1", "--verify"]), 0)
            self.assertEqual(Path(out, "region", "r.3.1.mca").read_bytes(), before)
            self.assertEqual(json.loads(Path(out, "report.json").read_text(encoding="utf-8"))["skipped_regions"], 2)
            verify = json.loads(Path(out, "verify.json").read_text(encoding="utf-8"))
            self.assertEqual((verify["problems"], verify["sha256_ok"]), (0, 2))
            # probes: the exact column from the world, and the raster pixel
            p = probe.probe(1720, 900, None, world=out, rasters=os.path.join(out, "rasters"))
            self.assertEqual(p["column"]["ground_y"], GROUND_TOP)
            self.assertEqual(p["column"]["top_block"], "minecraft:stone")
            self.assertEqual(p["column"]["biome"], "tensura:ancient_forest")
            self.assertEqual(p["landmask16"]["class"], "land")
            self.assertEqual(p["jura_ring"], "core")
            p = probe.probe(2500, -1432, 16, rasters=os.path.join(out, "rasters"))
            self.assertEqual((p["column"]["biome"], p["column"]["ground_y"]), ("minecraft:stony_peaks", GROUND_TOP))
            self.assertEqual(p["window"]["relief_p90_p10"], 0)
            with self._quiet(), self.assertRaises(SystemExit):
                imp.main([zpath, "--out", str(ROOT / "out")])

    @staticmethod
    def _quiet():
        import contextlib
        return contextlib.redirect_stdout(io.StringIO())


if __name__ == "__main__":
    unittest.main()
