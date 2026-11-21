"""Unregistered initial-era cart court: original project interpretation.

Outside blueprints/ and excluded from automatic structure discovery.
Load with tools/ and blueprints/ on sys.path. See ../ballachia-initial-r101.md.
"""
import ballachia as original
from _town_lib import M, Town

SIZE = original.SIZE
PARTS = original.PARTS


def build(bp):
    original.build(bp)
    # Restore the western outer wall; open the five internal bay fragments.
    bp.fill(10, 4, 8, 10, 5, 15, M("bricks"))
    for x in (18, 26, 34, 42, 50):
        bp.fill(x, 4, 8, x, 5, 15, M("air"))
    # Repave the rescue-link motifs using the existing neutral plaza palette.
    court = Town(bp, original.G)
    for x in (27, 38):
        court.pave(x, 31, x + 8, 35, "plaza")
