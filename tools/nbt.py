"""Minimal NBT writer (big-endian, Java edition) for structure files. Stdlib only.

Values map to tags by Python type: dict → Compound, list → List (element type from the first item),
str → String, bool → Byte, int → Int, float → Float. Use Long/Short/Byte/Double wrappers when needed.
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


_IDS = {Byte: 1, Short: 2, int: 3, Long: 4, float: 5, Double: 6, str: 8, list: 9, dict: 10}


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
