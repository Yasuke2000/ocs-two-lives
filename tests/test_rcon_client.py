"""tools/rcon.py (the local server's RCON client) against a fake server: python -I -m unittest discover -s tests"""
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
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
    """Answers like a vanilla server (net.minecraft.server.rcon.thread.RconClient): one read of at most 1460 bytes per
    request, and the connection is dropped when the length field does not match what that read returned. It waits a
    moment before each read, so a client that sends a packet before the previous one is answered always fails here
    (on a real server that depends on timing). Long replies are split at 4096 characters."""

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.port = self.sock.getsockname()[1]
        self.seen = []  # commands in the order the server ran them
        self.gametime = 1000

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self.serve, args=(conn,), daemon=True).start()

    def serve(self, conn):
        authed = False
        try:
            while True:
                time.sleep(0.02)
                data = conn.recv(1460)
                if len(data) < 10 or struct.unpack("<i", data[:4])[0] != len(data) - 4:
                    return
                rid, kind = struct.unpack("<ii", data[4:12])
                body = data[12:-2].decode("utf-8")
                if kind == 3:
                    authed = body == PASSWORD
                    conn.sendall(packet(rid if authed else -1, 2, ""))
                    continue
                self.seen.append(body)
                if body == "time query gametime":
                    self.gametime += 1  # one tick per query: the game moves on while the client polls
                    conn.sendall(packet(rid, 0, f"The time is {self.gametime}"))
                    continue
                if body == "long":
                    reply = "x" * 9000
                elif body.startswith("exactly "):
                    reply = "y" * int(body.split()[1])
                else:
                    reply = f"echo {body}" if body else "Unknown or incomplete command"
                for k in range(0, max(len(reply), 1), 4096):
                    conn.sendall(packet(rid, 0, reply[k:k + 4096]))
        except (ConnectionError, OSError):
            pass
        finally:
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

    def test_reply_of_exactly_one_packet(self):
        rc = rcon.Rcon("127.0.0.1", self.server.port, PASSWORD, timeout=5)
        self.addCleanup(rc.close)
        self.assertEqual(rc.command("exactly 4096"), "y" * 4096)
        self.assertEqual(rc.command("exactly 4095"), "y" * 4095)
        self.assertEqual(rc.command("after"), "echo after")

    def test_too_long_command_is_refused_before_sending(self):
        rc = rcon.Rcon("127.0.0.1", self.server.port, PASSWORD, timeout=5)
        self.addCleanup(rc.close)
        with self.assertRaises(ValueError):
            rc.command("say " + "z" * 2000)
        self.assertEqual(rc.command("list"), "echo list")

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

    def test_serve_mode_waits_ticks_between_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            pw = Path(tmp, "pw")
            pw.write_text(PASSWORD + "\n", encoding="utf-8")
            self.server.seen.clear()
            out = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "rcon.py"), "--serve", "--ticks", "3",
                                  "--port", str(self.server.port), "--password-file", str(pw)],
                                 input="say c\nsay d\n", capture_output=True, text=True, timeout=30)
        self.assertEqual(out.stdout.split("\n"), ["echo say c", rcon.MARKER, "echo say d", rcon.MARKER, ""])
        seen = self.server.seen
        # One read right after "say c", then polls until the game time is 3 ticks on.
        self.assertEqual(seen[seen.index("say c") + 1:seen.index("say d")], ["time query gametime"] * 4)


if __name__ == "__main__":
    unittest.main()
