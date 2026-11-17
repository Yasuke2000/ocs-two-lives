"""Minimal NBT writer (big-endian, Java edition) for structure files. Stdlib only.

Values map to tags by Python type: dict → Compound, list → List (element type from the first item),
str → String, bytes → Byte_Array, bool → Byte, int → Int, float → Float. Use Long/Short/Byte/Double wrappers when needed.
"""
import gzip
import struct


class Byte(int):
    pass


class Short(int):
    pass


class Long(int):
    pass


class Double(float):
    pass


_IDS = {Byte: 1, Short: 2, int: 3, Long: 4, float: 5, Double: 6, bytes: 7, str: 8, list: 9, dict: 10}


def _tag_id(value) -> int:
    if isinstance(value, bool):
        return 1
    for kind in (Byte, Short, Long, Double):
        if type(value) is kind:
            return _IDS[kind]
    return _IDS[type(value)]


def _string(value: str) -> bytes:
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def _payload(value) -> bytes:
    tag = _tag_id(value)
    if tag == 1:
        return struct.pack(">b", int(value))
    if tag == 2:
        return struct.pack(">h", value)
    if tag == 3:
        return struct.pack(">i", value)
    if tag == 4:
        return struct.pack(">q", value)
    if tag == 5:
        return struct.pack(">f", value)
    if tag == 6:
        return struct.pack(">d", value)
    if tag == 7:
        return struct.pack(">i", len(value)) + bytes(value)
    if tag == 8:
        return _string(value)
    if tag == 9:
        element = _tag_id(value[0]) if value else 0
        return bytes([element]) + struct.pack(">i", len(value)) + b"".join(_payload(v) for v in value)
    out = b"".join(bytes([_tag_id(v)]) + _string(k) + _payload(v) for k, v in value.items())
    return out + b"\x00"


def write_gzip(path, root: dict) -> None:
    """Write `root` as an unnamed root compound, gzip-compressed (the structure file format)."""
    # mtime=0 keeps the file byte-identical across rebuilds, so validate.py can check it is fresh.
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
        f.write(b"\x0a" + _string("") + _payload(root))


def read_gzip(path) -> dict:
    """Read a gzip-compressed NBT file (a structure or a WorldEdit .schem) into Python values.

    Byte/int/long arrays become `bytes` / lists of ints; the root compound's name is dropped.
    """
    with gzip.open(path, "rb") as f:
        data = f.read()
    pos = 0

    def take(n: int) -> bytes:
        nonlocal pos
        chunk = data[pos:pos + n]
        pos += n
        return chunk

    def string() -> str:
        (length,) = struct.unpack(">H", take(2))
        return take(length).decode("utf-8")

    def payload(tag: int):
        if tag == 1:
            return struct.unpack(">b", take(1))[0]
        if tag == 2:
            return struct.unpack(">h", take(2))[0]
        if tag == 3:
            return struct.unpack(">i", take(4))[0]
        if tag == 4:
            return struct.unpack(">q", take(8))[0]
        if tag == 5:
            return struct.unpack(">f", take(4))[0]
        if tag == 6:
            return struct.unpack(">d", take(8))[0]
        if tag == 7:
            (n,) = struct.unpack(">i", take(4))
            return take(n)
        if tag == 8:
            return string()
        if tag == 9:
            element = take(1)[0]
            (n,) = struct.unpack(">i", take(4))
            return [payload(element) for _ in range(n)]
        if tag == 10:
            out = {}
            while True:
                inner = take(1)[0]
                if inner == 0:
                    return out
                key = string()  # not inline: Python evaluates the right-hand side first
                out[key] = payload(inner)
        if tag == 11:
            (n,) = struct.unpack(">i", take(4))
            return list(struct.unpack(f">{n}i", take(4 * n)))
        if tag == 12:
            (n,) = struct.unpack(">i", take(4))
            return list(struct.unpack(f">{n}q", take(8 * n)))
        raise ValueError(f"unknown NBT tag {tag}")

    root_tag = take(1)[0]
    string()
    return payload(root_tag)
