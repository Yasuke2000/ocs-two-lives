"""tools/forge: build programs, registry checks, lints, .schem v3, the bridge client and the MCP server (offline).

The bridge itself (Java, ttl-portals) is tested in game by tests/ingame/build_bridge.rcon; here a fake bridge
(http.server on a random port) stands in for it.
"""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "forge"))
sys.path.insert(1, str(ROOT / "tools"))

import check  # noqa: E402
import client  # noqa: E402
import program  # noqa: E402
import schem  # noqa: E402
from blueprint import from_schem  # noqa: E402

HUT = {
    "name": "test_forge_hut", "size": [11, 10, 9],
    "palette": {"wall": "minecraft:spruce_planks", "roof": "minecraft:dark_oak_stairs"},
    "ops": [
        {"op": "fill", "from": [1, 0, 1], "to": [9, 0, 7], "block": "minecraft:cobblestone"},
        {"op": "walls", "from": [1, 1, 1], "to": [9, 4, 7], "block": "$wall"},
        {"op": "window_grid", "from": [1, 1, 1], "to": [9, 4, 1], "block": "minecraft:glass_pane"},
        {"op": "door", "at": [5, 1, 7], "facing": "south", "block": "minecraft:spruce_door"},
        {"op": "roof", "from": [0, 5, 0], "to": [10, 5, 8], "style": "gable", "axis": "x", "stairs": "$roof",
         "fill": "$wall"},
    ],
}

REGISTRY = {
    "data_version": 3955, "minecraft": "1.21.1", "mods": {"minecraft": "1.21.1"},
    "blocks": {
        "minecraft:air": {"default": "minecraft:air", "air": True},
        "minecraft:cobblestone": {"default": "minecraft:cobblestone"},
        "minecraft:spruce_planks": {"default": "minecraft:spruce_planks"},
        "minecraft:glass_pane": {"default": "minecraft:glass_pane", "props": {
            "east": ["true", "false"], "north": ["true", "false"], "south": ["true", "false"],
            "waterlogged": ["true", "false"], "west": ["true", "false"]}},
        "minecraft:spruce_door": {"default": "minecraft:spruce_door", "props": {
            "facing": ["north", "south", "west", "east"], "half": ["upper", "lower"], "hinge": ["left", "right"],
            "open": ["true", "false"], "powered": ["true", "false"]}},
        "minecraft:dark_oak_stairs": {"default": "minecraft:dark_oak_stairs", "props": {
            "facing": ["north", "south", "west", "east"], "half": ["top", "bottom"],
            "shape": ["straight", "inner_left", "inner_right", "outer_left", "outer_right"], "waterlogged": ["true", "false"]}},
        "minecraft:dark_oak_slab": {"default": "minecraft:dark_oak_slab", "props": {"type": ["top", "bottom", "double"],
                                                                                      "waterlogged": ["true", "false"]}},
    },
    "biomes": ["minecraft:plains", "tensura:ancient_forest_example"],
    "dimensions": {"minecraft:overworld": {"min_y": -64, "height": 384, "sea_level": 63}},
}


class ProgramTest(unittest.TestCase):
    def test_hut_compiles_and_passes_lint(self):
        bp, warnings = program.compile_program(HUT)
        self.assertEqual(warnings, [])
        self.assertEqual(bp.blocks[(5, 1, 7)], "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
        self.assertEqual(bp.blocks[(5, 2, 7)], "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
        self.assertIn("minecraft:glass_pane", bp.blocks[(2, 2, 1)])
        self.assertEqual(bp.blocks[(4, 5, 0)], "minecraft:dark_oak_stairs[facing=south,half=bottom]")
        self.assertEqual(bp.blocks[(4, 5, 8)], "minecraft:dark_oak_stairs[facing=north,half=bottom]")
        report = check.lint(bp)
        # The eaves overhang one block past the walls on air: the only structural note expected is none.
        self.assertEqual([w for w in report["warnings"] if "door" in w or "gravity" in w], [])
        errors, _ = check.check_states(set(bp.blocks.values()), REGISTRY)
        self.assertEqual(errors, [])

    def test_alias_and_errors(self):
        with self.assertRaisesRegex(program.ProgramError, "unknown palette alias"):
            program.compile_program({"size": [2, 2, 2], "ops": [{"op": "set", "at": [0, 0, 0], "block": "$nope"}]})
        with self.assertRaisesRegex(program.ProgramError, "unknown op"):
            program.compile_program({"size": [2, 2, 2], "ops": [{"op": "explode"}]})
        _, warnings = program.compile_program({"size": [2, 2, 2], "ops": [
            {"op": "fill", "from": [0, 0, 0], "to": [3, 0, 0], "block": "stone"}]})
        self.assertIn("2 cells fell outside", warnings[0])

    def test_floating_and_gravity_lint(self):
        bp, _ = program.compile_program({"size": [5, 6, 5], "ops": [
            {"op": "set", "at": [2, 0, 2], "block": "stone"},
            {"op": "set", "at": [2, 4, 2], "block": "stone"},
            {"op": "set", "at": [0, 3, 0], "block": "sand"},
            {"op": "set", "at": [4, 2, 4], "block": "torch"}]})
        text = " ".join(check.lint(bp)["warnings"])
        self.assertIn("not connected to the ground", text)
        self.assertIn("gravity blocks", text)
        self.assertIn("need a block under them", text)

    def test_registry_errors(self):
        errors, _ = check.check_states({"minecraft:spruce_door[facing=up]", "tensura:made_up_block",
                                        "minecraft:cobblestone[color=red]"}, REGISTRY)
        self.assertEqual(len(errors), 3)
        _, warnings = check.check_states({"minecraft:stone"}, None)
        self.assertIn("ids not verified", warnings[0])

    def test_rotation(self):
        self.assertEqual(program.rotate_state("minecraft:oak_stairs[facing=north,half=bottom]", 1),
                         "minecraft:oak_stairs[facing=east,half=bottom]")
        self.assertEqual(program.rotate_state("minecraft:oak_log[axis=x]", 1), "minecraft:oak_log[axis=z]")
        self.assertEqual(program.rotate_state("minecraft:glass_pane[east=true,north=false,south=false,west=false]", 1),
                         "minecraft:glass_pane[east=false,north=false,south=true,west=false]")
        # A 3 x 1 x 1 bar rotated 90° clockwise becomes 1 x 1 x 3, its x=0 end at z=0.
        with tempfile.TemporaryDirectory() as d:
            src, _ = program.compile_program({"name": "bar", "size": [3, 1, 1], "ops": [
                {"op": "set", "at": [0, 0, 0], "block": "red_wool"}, {"op": "fill", "from": [1, 0, 0], "to": [2, 0, 0], "block": "stone"}]})
            path = schem.write(src, Path(d) / "bar.schem")
            bp, w = program.compile_program({"size": [1, 1, 3], "ops": [
                {"op": "stamp", "structure": str(path), "at": [0, 0, 0], "rotate": 90}]})
            self.assertEqual(w, [])
            self.assertEqual(bp.blocks[(0, 0, 0)], "minecraft:red_wool")

    def test_stamp_pack_structure(self):
        bp, _ = program.compile_program({"size": [64, 64, 64], "ops": [{"op": "stamp", "structure": "test_hut", "at": [0, 0, 0]}]})
        self.assertGreater(len(bp.blocks), 10)


class SchemTest(unittest.TestCase):
    def test_roundtrip(self):
        bp, _ = program.compile_program(HUT)
        with tempfile.TemporaryDirectory() as d:
            path = schem.write(bp, Path(d) / "hut.schem")
            back = from_schem("hut", path)
        self.assertEqual(back.size, bp.size)
        for pos, state in bp.blocks.items():
            self.assertEqual(back.blocks[pos], state)
        self.assertEqual(sum(1 for s in back.blocks.values() if s != "minecraft:air"), len(bp.blocks))


class FakeBridge(BaseHTTPRequestHandler):
    jobs = []

    def log_message(self, *a):
        pass

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth(self):
        if self.headers.get("Authorization") != "Bearer secret-token-123456":
            self._send(401, {"error": "missing or wrong bearer token"})
            return False
        return True

    def do_GET(self):
        if not self._auth():
            return
        if self.path.startswith("/v1/health"):
            return self._send(200, {"ok": True, "players": 0, "mspt": 3.1, "queued_jobs": 0})
        if self.path.startswith("/v1/zones"):
            return self._send(200, {"zones": [], "protect": [], "allow_anywhere": True})
        if self.path.startswith("/v1/region") and "mode=heightmap" in self.path:
            return self._send(200, {"dim": "minecraft:overworld", "from": [0, 0], "size": [4, 2], "heights": [64, 65, 66, None, 64, 64, 70, 71],
                                    "block_palette": ["minecraft:grass_block", "minecraft:stone"], "blocks_rle": [[3, 0], [1, -1], [2, 0], [2, 1]],
                                    "biome_palette": ["minecraft:plains"], "biomes_rle": [[3, 0], [1, -1], [4, 0]]})
        if self.path.startswith("/v1/region"):
            return self._send(200, {"dim": "minecraft:overworld", "origin": [0, 64, 0], "size": [2, 1, 2],
                                    "palette": ["minecraft:stone", "minecraft:air"], "rle": [[3, 0], [1, 1]], "block_entities": []})
        self._send(404, {"error": "no endpoint"})

    def do_POST(self):
        if not self._auth():
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/v1/jobs":
            FakeBridge.jobs.append(body)
            if body["dry_run"]:
                return self._send(200, {"dry_run": True, "cells_set": sum(n for n, v in body["rle"] if v >= 0)})
            return self._send(200, {"id": "j1", "phase": "queued"})
        if self.path == "/v1/jobs/j1/undo":
            return self._send(200, {"id": "j2", "phase": "queued", "undo_of": "j1"})
        self._send(404, {"error": "no endpoint"})


class BridgeFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeBridge)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_encode_decode(self):
        bp, _ = program.compile_program(HUT)
        job = client.encode_job(bp, [10, 64, 10])
        self.assertEqual(sum(n for n, _ in job["rle"]), 11 * 10 * 9)
        self.assertEqual(sum(n for n, v in job["rle"] if v >= 0), len(bp.blocks))
        back = client.decode_blocks({"size": job["size"], "palette": job["palette"], "rle": job["rle"]})
        self.assertEqual(back.blocks, bp.blocks)

    def test_wrong_token(self):
        with self.assertRaises(client.BridgeError) as e:
            client.Bridge(self.url, "wrong").get("health")
        self.assertEqual(e.exception.status, 401)

    def test_mcp_session(self):
        """The MCP server end to end over stdio: handshake, list, preview (with image), dry run, place, undo."""
        env = {"TTL_BRIDGE_URL": self.url, "TTL_BRIDGE_TOKEN": "secret-token-123456", "PATH": "/usr/bin:/bin"}
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                                                           "clientInfo": {"name": "test", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "preview_build", "arguments": {"program": HUT}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "apply_build", "arguments": {"program": HUT, "origin": [0, 64, 0]}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "apply_build", "arguments": {"program": HUT, "origin": [0, 64, 0], "dry_run": False}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "undo", "arguments": {"id": "j1"}}},
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "read_region", "arguments": {"from": [0, 0, 0], "to": [3, 0, 1], "mode": "heightmap"}}},
            {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "preview_build", "arguments": {"program": {"size": [1, 1, 1], "ops": [{"op": "nope"}]}}}},
        ]
        proc = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "forge" / "mcp_server.py")],
                              input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True,
                              env=env, timeout=120, cwd=ROOT)
        replies = {r["id"]: r for r in map(json.loads, proc.stdout.splitlines())}
        self.assertEqual(sorted(replies), [1, 2, 3, 4, 5, 6, 7, 8], proc.stderr)
        self.assertEqual(replies[1]["result"]["protocolVersion"], "2025-06-18")
        names = {t["name"] for t in replies[2]["result"]["tools"]}
        self.assertTrue({"preview_build", "apply_build", "undo", "get_registry", "read_region"} <= names)
        preview = replies[3]["result"]
        self.assertFalse(preview["isError"], preview)
        self.assertEqual(preview["content"][1]["type"], "image")
        dry = json.loads(replies[4]["result"]["content"][0]["text"])
        self.assertTrue(dry["dry_run"])
        self.assertEqual(json.loads(replies[5]["result"]["content"][0]["text"])["id"], "j1")
        self.assertEqual(json.loads(replies[6]["result"]["content"][0]["text"])["undo_of"], "j1")
        hm = json.loads(replies[7]["result"]["content"][0]["text"])
        self.assertEqual((hm["height_min"], hm["height_max"], hm["unloaded_columns"]), (64, 71, 1))
        self.assertTrue(replies[8]["result"]["isError"])
        self.assertIn("unknown op", replies[8]["result"]["content"][0]["text"])
        self.assertTrue(FakeBridge.jobs[0]["dry_run"])
        self.assertFalse(FakeBridge.jobs[1]["dry_run"])


if __name__ == "__main__":
    unittest.main()
