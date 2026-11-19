#!/usr/bin/env python3
"""Minimal Source RCON client for the local test server (tools/local.sh); the staging pod has rcon-cli.

    rcon.py [--host H] [--port P] [--password-file F] "<command>"   one command, prints the reply
    rcon.py --serve ...                                              one command per stdin line; after each reply
                                                                     a line with only <<<rcon-end>>> follows

The --serve mode keeps one connection open for a whole test run: a new process per command costs ~0.1 s on
Windows, and a test-all sends thousands of commands. --ticks N (with --serve) starts each command at least N game
ticks after the previous one ended: on staging every command is a kubectl exec (~0.17 s, 3 ticks), and tests rely on
that (a step that a script schedules one tick later is done before the next command). Exit 1 when the server does
not answer.
"""
import argparse
import re
import socket
import struct
import sys
import time
from pathlib import Path

LOGIN, COMMAND = 3, 2
MARKER = "<<<rcon-end>>>"
CHUNK = 4096  # reply bytes per packet
MAX_COMMAND = 1460 - 14  # the server reads a request in one 1460-byte buffer


class Rcon:
    def __init__(self, host: str, port: int, password: str, timeout: float = 300.0):
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

    def _read(self) -> tuple[int, bytes]:
        size = struct.unpack("<i", self._exact(4))[0]
        rid, _kind = struct.unpack("<ii", self._exact(8))
        return rid, self._exact(size - 8)[:-2]

    def _exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("RCON connection closed")
            buf += chunk
        return buf

    def _request(self, kind: int, body: str) -> tuple[int, bytes]:
        self._send(kind, body)
        return self._read()

    def command(self, cmd: str) -> str:
        # Never send a packet before the previous one is answered: the server reads one TCP chunk per packet and
        # drops the connection when the length field does not match what it read, so two packets that arrive
        # together (a command and a pipelined end probe) kill the connection, depending on timing.
        if len(cmd.encode("utf-8")) > MAX_COMMAND:
            raise ValueError(f"RCON command over {MAX_COMMAND} bytes (the server reads one 1460-byte chunk)")
        want = self._send(COMMAND, cmd)
        rid, body = self._read()
        if rid != want:
            raise ConnectionError(f"RCON reply for request {rid}, expected {want}")
        parts = [body]
        if len(body) >= CHUNK - 16:
            # Replies over 4 KiB come in 4096-byte packets, all sent before the server reads again; an empty probe
            # sent now is answered after the last of them (Minecraft answers in order).
            probe = self._send(COMMAND, "")
            while True:
                rid, body = self._read()
                if rid == probe:
                    break
                if rid == want:
                    parts.append(body)
        return b"".join(parts).decode("utf-8", "replace")

    def gametime(self) -> int | None:
        m = re.search(r"(-?\d+)\s*$", self.command("time query gametime"))
        return int(m.group(1)) if m else None

    def wait_ticks(self, since: int | None, ticks: int, limit: float = 30.0):
        if since is None or ticks <= 0:
            return
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            now = self.gametime()
            if now is None or now >= since + ticks:
                return
            time.sleep(0.005)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25575)
    ap.add_argument("--password-file", required=True)
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--ticks", type=int, default=0, help="with --serve: game ticks between commands")
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

    def reply(out: str) -> str:
        return out if not out or out.endswith("\n") else out + "\n"

    try:
        if not args.serve:
            sys.stdout.write(reply(rc.command(args.command or "list")))
            return 0
        for line in sys.stdin:
            sys.stdout.write(reply(rc.command(line.rstrip("\r\n"))) + MARKER + "\n")
            sys.stdout.flush()
    except (OSError, ValueError) as e:
        print(f"rcon: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
