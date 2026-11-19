"""Beds for the blueprints (stdlib only).

A bed is two blocks: the foot and the head. `facing` is the direction from the foot to the head (the pillow side,
which belongs against a wall); `part=head` is the block one step toward `facing`. Colours per culture (owner,
19/11/2026): Tempest goblins and hobgoblins simple brown and green wool, Dwargon red and gray, Blumund and
Englassia blue and white, nobles a finer colour (CULTURE below). Both blocks must stand on a floor with two free
blocks above (a player is 1.8 high), and a bed never goes on a cell in `keep_clear` (door landings, ladder feet).
tests/test_beds.py checks the same rules on the saved structure files.
"""
from _dwargon_lib import AIR, rnd

OFFSET = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

CULTURE = {
    "tempest": ("brown", "green"),
    "dwargon": ("red", "gray"),
    "blumund": ("blue", "white"),
    "englassia": ("blue", "white"),
    "falmuth": ("light_blue", "white"),
    "noble": ("purple", "magenta"),
}


def bed_state(colour: str, facing: str, part: str) -> str:
    return f"minecraft:{colour}_bed[facing={facing},occupied=false,part={part}]"


def free(get, x, y, z) -> bool:
    """A cell nothing stands in (air, or never set in a blueprint that leaves its interior open)."""
    return get(x, y, z) in (None, AIR)


def pick(colours, x, z, seed=7) -> str:
    """A colour from `colours` for the room at (x, z): stable between runs."""
    return colours[int(rnd(x, 0, z, seed) * len(colours)) % len(colours)]


def fits(get, head, foot, y) -> bool:
    for (x, z) in (head, foot):
        floor = get(x, y - 1, z)
        if floor in (None, AIR) or not all(free(get, x, y + dy, z) for dy in (0, 1, 2)):
            return False
    return True


def place_bed(put, get, x, y, z, facing, colour, keep_clear=(), strict=True) -> bool:
    """The bed whose head is at (x, y, z), foot one block away from `facing`. False (or ValueError when `strict`)
    when a cell is taken, has no floor or no headroom, or lies in `keep_clear`."""
    dx, dz = OFFSET[facing]
    head, foot = (x, z), (x - dx, z - dz)
    if head in keep_clear or foot in keep_clear or not fits(get, head, foot, y):
        if strict:
            raise ValueError(f"bed {colour} facing {facing} at {x},{y},{z}: cell taken, no floor, no headroom or in the way")
        return False
    put(head[0], y, head[1], bed_state(colour, facing, "head"))
    put(foot[0], y, foot[1], bed_state(colour, facing, "foot"))
    return True


def bed_row(put, get, y, wall, line, span, colours, step=2, keep_clear=(), seed=7) -> int:
    """Beds in a row with their heads against `wall` ('north', 'south', 'east' or 'west'): the head cells lie on
    `line` (the z of a north or south wall's first interior row, the x for east or west) at positions
    span[0], span[0] + step, ... up to span[1]. Colours cycle through `colours`. Returns how many fitted."""
    n = 0
    for i, a in enumerate(range(span[0], span[1] + 1, step)):
        x, z = (a, line) if wall in ("north", "south") else (line, a)
        if place_bed(put, get, x, y, z, wall, colours[i % len(colours)], keep_clear, strict=False):
            n += 1
    return n


def around(cell, r=1):
    """The cells within r of `cell` (square), for a keep_clear set round a door landing or a ladder foot."""
    return {(cell[0] + dx, cell[1] + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1)}
