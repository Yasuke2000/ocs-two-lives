"""Velgrynd's Great Holy Mountain: an imperial approach to Scorching God Mountain.

SIZE (89, 52, 85), south trail anchor (44, 5, 78). Several dark basalt ridges
enclose a copper-coloured summit vent. A five-wide stair leads into a lit
votive gallery carved into its southern shoulder. Basalt, andesite, tuff,
oxidised copper and red sandstone. References: Fuse, LN 14 ch. 2, and the
location references in design/lore/great_holy_mountain.md.
"""
import math

from _dwargon_lib import AIR, dark_spots, noise2
from _sites_lib import M

SIZE = (89, 52, 85)
PARTS = [0, 42]
G = 4
C = 44


def elevation(x, z):
    dx, dz = x - 44, z - 32
    angle = math.atan2(dz, dx)
    radius = math.hypot(dx, dz * 0.96)
    waviness = noise2(x, z, 7, 37) - 0.5
    # Eroded ridges radiate from an off-centre summit; the north wall of the
    # crater is taller than the southern lip seen from the footpath.
    outline = 38 + 3 * math.sin(3 * angle) + 3 * math.cos(5 * angle)
    flank = max(0, 1 - radius / outline)
    height = 42 * flank + 8 * flank * waviness
    if radius < 10:
        height = min(height, 20 + 1.45 * radius - 2 * math.sin(angle))
    spur = max(0, 1 - math.hypot((x - 65) / 17, (z - 44) / 20))
    edge = max(0, min(x, z, SIZE[0] - 1 - x, SIZE[2] - 1 - z))
    return G + round(max(height, 16 * spur) * min(1, edge / 8))


def build(bp):
    sx, sy, sz = SIZE
    for x in range(sx):
        for z in range(sz):
            top = elevation(x, z)
            grain = noise2(x, z, 4, 71)
            radius = math.hypot(x - 44, z - 32)
            if top <= G + 4:
                face = 'coarse_dirt' if top > G and grain > 0.72 else 'grass_block'
            elif radius < 7:
                face = 'red_sandstone' if radius > 3.5 else 'ochre_froglight'
            elif top < G + 11:
                face = 'tuff' if grain < 0.6 else 'andesite'
            else:
                face = 'basalt' if grain < 0.53 else 'smooth_basalt'
            bp.pillar(x, z, 0, top - 1, M('stone'))
            bp.set(x, top, z, M(face))
            bp.pillar(x, z, top + 1, sy - 1, AIR)

    # Approach alternates pairs of level pavers with shallow risers. Its stone
    # parapet becomes exposed retaining masonry where the path crosses a spur.
    for z in range(40, 84):
        rise = max(0, (72 - z) // 2)
        floor = G + rise
        stair = 40 <= z <= 70 and z % 2 == 0
        for x in range(40, 49):
            edge = x in (40, 48)
            bp.pillar(x, z, G, floor, M('tuff'))
            bp.pillar(x, z, floor + 1, min(sy - 1, max(elevation(x, z) + 1, floor + 4)), AIR)
            bp.set(x, floor, z, M('polished_andesite_stairs[facing=north]' if stair else 'polished_andesite'))
            if edge and z < 75:
                bp.set(x, floor + 1, z, M('polished_blackstone_brick_slab[type=bottom]'))
                if z in (44, 54, 64, 74):
                    bp.set(x, floor + 1, z, M('polished_basalt'))
                    bp.set(x, floor + 2, z, M('lantern'))

    # A recessed arcade at the end of the stair, facing south. The shell is
    # built even at thin parts of the slope so the gallery stays enclosed.
    floor = G + 16
    bp.fill(36, floor, 31, 52, floor + 6, 40, M('smooth_basalt'))
    bp.fill(37, floor + 1, 32, 51, floor + 5, 39, AIR)
    bp.fill(41, floor + 1, 40, 47, floor + 4, 40, AIR)
    bp.fill(41, floor, 40, 47, floor, 40, M('polished_andesite_stairs[facing=north]'))
    bp.fill(37, floor, 32, 51, floor, 39, M('polished_andesite'))
    for x in (37, 40, 48, 51):
        bp.pillar(x, 40, floor + 1, floor + 4, M('polished_basalt'))
        bp.set(x, floor + 5, 40, M('chiseled_red_sandstone'))
    bp.fill(36, floor + 6, 40, 52, floor + 6, 40, M('waxed_cut_copper_slab[type=bottom]'))
    for x in (38, 50):
        bp.fill(x, floor + 1, 34, x, floor + 1, 36, M('polished_blackstone_brick_stairs[facing=' +
                ('west' if x == 38 else 'east') + ']'))
        for z in (33, 38):
            bp.set(x, floor + 5, z, M('lantern[hanging=true]'))
    # A flame mosaic is set into the apse. All light is enclosed behind the
    # glass and real lava never flows into the aisle.
    for dx, height in ((-2, 2), (-1, 3), (0, 5), (1, 4), (2, 2)):
        bp.pillar(C + dx, 31, floor + 1, floor + height, M('ochre_froglight'))
        bp.pillar(C + dx, 32, floor + 1, floor + height, M('orange_stained_glass'))
    candidates = [(x, y, z) for x in range(37, 52) for z in range(32, 41)
                  for y in range(floor + 1, floor + 6)]
    if dark_spots(bp.blocks, SIZE, candidates):
        raise ValueError('unlit floor in the imperial gallery')
