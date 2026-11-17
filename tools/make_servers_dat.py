#!/usr/bin/env python3
"""Write a Minecraft servers.dat with one entry, so the server shows up in Multiplayer.

Usage: make_servers_dat.py <out> <name> <address>
"""
import struct
import sys


def string(value: str) -> bytes:
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def named(tag_id: int, name: str, payload: bytes) -> bytes:
    return bytes([tag_id]) + string(name) + payload


def main() -> None:
    out, name, address = sys.argv[1:4]
    entry = named(8, "name", string(name)) + named(8, "ip", string(address)) + b"\x00"
    servers = bytes([10]) + struct.pack(">i", 1) + entry
    # servers.dat is uncompressed NBT: an unnamed root compound holding the "servers" list.
    root = named(10, "", named(9, "servers", servers) + b"\x00")
    with open(out, "wb") as f:
        f.write(root)


if __name__ == "__main__":
    main()
