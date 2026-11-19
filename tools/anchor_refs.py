"""References from the pack data to design/data/anchors.toml (Lerfing import WP-L4; stdlib only).

anchors.toml holds every canon place of the Life 2 overworld in Lerfing's coordinates. The other data names an anchor
instead of repeating its numbers, and tools/gen_data.py writes the resolved x/z into generated/data.js, so the scripts
keep reading plain x/z and a moved anchor moves everything that names it:

    design/builds/<name>.toml       the anchor whose `build` = <name> gives x/z (no x/z in the build file)
    landmarks.toml [[landmark]]     the anchor whose `landmark` = <name> gives x/z (no x/z in the landmark)
    flat records (arrival.toml [life2], npcs.toml [[spot]] / sidequests.toml [[place]] with anchor = "world")
                                    at = "<anchor id>" instead of x/z
    inline place tables (bosses.toml arena / spawn.at, artifice.toml [steal] smithy)
                                    { anchor = "<anchor id>", dx = n, dz = n, ... } instead of x/z (dx/dz optional)

The per-file checkers call these too (resolving twice is harmless), so a test that loads one TOML raw still sees x/z.

life/tempest.js reads its position from generated/anchors.js (TtlAnchors, written by gen_data.py from this table).
"""
import functools
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANCHORS = ROOT / "design" / "data" / "anchors.toml"


@functools.lru_cache(maxsize=1)
def raw() -> dict:
    return tomllib.loads(ANCHORS.read_text(encoding="utf-8")) if ANCHORS.is_file() else {}


def table() -> dict:
    """{id: anchor (with "id")}; [keepout.<id>] tables are not anchors."""
    return {k: dict(v, id=k) for k, v in raw().items() if k != "keepout" and isinstance(v, dict)}


def keepouts() -> list[dict]:
    return [dict(v, id=k) for k, v in raw().get("keepout", {}).items()]


def point(where: str, aid, dx=0, dz=0) -> tuple[int, int]:
    a = table().get(aid) if isinstance(aid, str) else None
    if a is None:
        raise SystemExit(f"{where}: {aid!r} is not a design/data/anchors.toml anchor")
    for key, v in (("dx", dx), ("dz", dz)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise SystemExit(f"{where}: {key} must be an integer")
    return a["x"] + dx, a["z"] + dz


def linked(kind: str, name: str) -> dict | None:
    """The anchor whose `build` / `landmark` field names this build or landmark, or None."""
    hits = [a for a in table().values() if a.get(kind) == name]
    if len(hits) > 1:
        raise SystemExit(f"anchors.toml: {', '.join(a['id'] for a in hits)} all position {kind} {name!r}")
    return hits[0] if hits else None


def resolve_at(where: str, rec: dict) -> None:
    """A flat record with at = "<anchor id>": writes its x/z (in place; running it twice is harmless). x/z that differ
    from the anchor are refused: the numbers live in anchors.toml only."""
    if not isinstance(rec, dict) or "at" not in rec:
        return
    _write(where, rec, point(where, rec["at"]), "at")


def resolve_anchor(where: str, tbl) -> None:
    """An inline place table { anchor = "<id>", dx, dz, ... }: writes x/z (in place; keeps anchor, dx, dz)."""
    if not isinstance(tbl, dict) or "anchor" not in tbl:
        return
    _write(where, tbl, point(where, tbl["anchor"], tbl.get("dx", 0), tbl.get("dz", 0)), "anchor")


def _write(where: str, rec: dict, xz: tuple[int, int], key: str) -> None:
    if ("x" in rec or "z" in rec) and (rec.get("x"), rec.get("z")) != xz:
        raise SystemExit(f"{where}: {key} = {rec[key]!r} is at {xz}; drop x/z here (anchors.toml holds the numbers)")
    rec["x"], rec["z"] = xz


def resolve_data(data: dict) -> dict:
    """Resolve every anchor reference of the design/data tables loaded as {stem: table} (in place; returns data)."""
    if "arrival" in data:
        resolve_at("arrival.toml: [life2]", data["arrival"].get("life2"))
    for s in data.get("npcs", {}).get("spot", []):
        resolve_at(f"npcs.toml: spot {s.get('id', '?')}", s)
    for p in data.get("sidequests", {}).get("place", []):
        resolve_at(f"sidequests.toml: place {p.get('id', '?')}", p)
    for b in data.get("bosses", {}).get("boss", []):
        where = f"bosses.toml: boss {b.get('id', '?')}"
        resolve_anchor(f"{where}: arena", b.get("arena"))
        resolve_anchor(f"{where}: spawn.at", (b.get("spawn") or {}).get("at"))
    resolve_anchor("artifice.toml: [steal] smithy", data.get("artifice", {}).get("steal", {}).get("smithy"))
    return data
