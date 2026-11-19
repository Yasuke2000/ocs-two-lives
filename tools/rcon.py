#!/usr/bin/env python3
"""Minimal Source RCON client for the local test server (tools/local.sh); the staging pod has rcon-cli.

    rcon.py [--host H] [--port P] [--password-file F] "<command>"   one command, prints the reply
    rcon.py --serve ...                                              one command per stdin line; after each reply
                                                                     a line with only <<<rcon-end>>> follows

The --serve mode keeps one connection open for a whole test run: a new process per command costs ~0.1 s on
Windows, and a test-all sends thousands of commands. Exit 1 when the server does not answer.
"""
import argparse
import socket
import struct
import sys
from pathlib import Path

LOGIN, COMMAND = 3, 2
MARKER = "<<<rcon-end>>>"


class Rcon:
    def __init__(self, host: str, port: int, password: str, timeout: float = 60.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.seq = 0
        if self._request(LOGIN, password)[0] == -1:
            self.close()
            raise PermissionError("RCON login refused (wrong password)")

    def close(self):
        self.sock.close()

    def _send(self, kind: int, body: str) -> int:
        self.seq += 1
        data = body.encode("utf-8") + b"\0\0"
        self.sock.sendall(struct.pack("<iii", len(data) + 8, self.seq, kind) + data)
        return self.seq

    def _read(self) -> tuple[int, str]:
        size = struct.unpack("<i", self._exact(4))[0]
        rid, _kind = struct.unpack("<ii", self._exact(8))
        body = self._exact(size - 8)[:-2]
        return rid, body.decode("utf-8", "replace")

    def _exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("RCON connection closed")
            buf += chunk
        return buf

    def _request(self, kind: int, body: str) -> tuple[int, str]:
        self._send(kind, body)
        return self._read()

    def command(self, cmd: str) -> str:
        # Replies over 4 KiB arrive in several packets; an empty probe command after the real one marks the end
        # (Minecraft answers requests in order).
        want = self._send(COMMAND, cmd)
        probe = self._send(COMMAND, "")
        parts = []
        while True:
            rid, body = self._read()
            if rid == probe:
                return "".join(parts)
            if rid == want:
                parts.append(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25575)
    ap.add_argument("--password-file", required=True)
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("command", nargs="?")
    args = ap.parse_args()
    password = Path(args.password_file).read_text(encoding="utf-8").strip()
    try:
        rc = Rcon(args.host, args.port, password)
    except OSError as e:
        print(f"rcon: server not answering on {args.host}:{args.port} ({e})", file=sys.stderr)
        return 1
    # bash reads the replies: UTF-8 and no CR, also on Windows.
    sys.stdout.reconfigure(encoding="utf-8", newline=chr(10))
    sys.stdin.reconfigure(encoding="utf-8")
    if not args.serve:
        print(rc.command(args.command or "list"))
        return 0
    for line in sys.stdin:
        out = rc.command(line.rstrip("\r\n"))
        sys.stdout.write(out + ("\n" if out and not out.endswith("\n") else "") + MARKER + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
