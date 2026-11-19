"""tools/rcon.py (the local server's RCON client) against a fake server: python -I -m unittest discover -s tests"""
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rcon  # noqa: E402

PASSWORD = "s3cret"


def packet(rid, kind, body):
    data = body.encode("utf-8") + b"\0\0"
    return struct.pack("<iii", len(data) + 8, rid, kind) + data


def read_packet(conn):
    def exact(n):
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError
            buf += chunk
        return buf
    size = struct.unpack("<i", exact(4))[0]
    rid, kind = struct.unpack("<ii", exact(8))
    return rid, kind, exact(size - 8)[:-2].decode("utf-8")


class FakeMinecraft(threading.Thread):
    """Answers like a vanilla server: login, then each command in order, long replies split at 4096 chars."""

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.port = self.sock.getsockname()[1]

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self.serve, args=(conn,), daemon=True).start()

    def serve(self, conn):
        try:
            rid, kind, body = read_packet(conn)
            conn.sendall(packet(rid if body == PASSWORD else -1, 2, ""))
            while True:
                rid, kind, body = read_packet(conn)
                reply = "x" * 9000 if body == "long" else (f"echo {body}" if body else "Unknown or incomplete command")
                for i in range(0, max(len(reply), 1), 4096):
                    conn.sendall(packet(rid, 0, reply[i:i + 4096]))
        except (ConnectionError, OSError):
            conn.close()


class RconClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = FakeMinecraft()
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.sock.close()

    def test_commands_answer_in_order(self):
        rc = rcon.Rcon("127.0.0.1", self.server.port, PASSWORD, timeout=5)
        self.addCleanup(rc.close)
        self.assertEqual(rc.command("list"), "echo list")
        self.assertEqual(rc.command("ttl inspect TtlBot"), "echo ttl inspect TtlBot")

    def test_long_replies_are_joined(self):
        rc = rcon.Rcon("127.0.0.1", self.server.port, PASSWORD, timeout=5)
        self.addCleanup(rc.close)
        self.assertEqual(rc.command("long"), "x" * 9000)
        self.assertEqual(rc.command("after"), "echo after")

    def test_wrong_password_is_refused(self):
        with self.assertRaises(PermissionError):
            rcon.Rcon("127.0.0.1", self.server.port, "wrong", timeout=5)

    def test_serve_mode_marks_each_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            pw = Path(tmp, "pw")
            pw.write_text(PASSWORD + "\n", encoding="utf-8")
            out = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "rcon.py"), "--serve", "--port",
                                  str(self.server.port), "--password-file", str(pw)],
                                 input="say a\nsay b\n", capture_output=True, text=True, timeout=30)
        self.assertEqual(out.stdout.split("\n"), ["echo say a", rcon.MARKER, "echo say b", rcon.MARKER, ""])


if __name__ == "__main__":
    unittest.main()
