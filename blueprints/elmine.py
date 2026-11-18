"""Elmine, the Divine Tree's lower embassy terrace. SIZE (75, 60, 75), three z slabs.

South walking anchor (37, 4, 67). Sarion's capital in the Divine Tree is represented by its
root gate, a raised annular promenade and two open diplomatic pavilions. Oak, pale quartz,
birch, weathered copper and persistent leaves. Sources and scale interpretation in design/lore/elmine.md.
"""
import math

from _dwargon_lib import AIR, rnd
from _sites_lib import M
from _lords_lib import light_pass


SIZE = (75, 60, 75)
PARTS = [0, 25, 50]
X, Z = 37, 32
G = 3
BARK = M("oak_wood[axis=y]")
STONE = M("smooth_quartz")
BRASS = M("waxed_cut_copper")
COPPER = M("waxed_oxidized_cut_copper")
LAMP = M("verdant_froglight")


def limb(bp, start, end, thick, thin):
    """Taper a branch between two joints, keeping bark on each exposed face."""
    vector = [b - a for a, b in zip(start, end)]
    steps = max(abs(v) for v in vector)
    axis = "xyz"[max(range(3), key=lambda i: abs(vector[i]))]
    wood = M(f"oak_wood[axis={axis}]")
    for step in range(steps + 1):
        t = step / steps
        x, y, z = [round(a + t * v) for a, v in zip(start, vector)]
        r = thick + t * (thin - thick)
        for dx in range(-math.ceil(r), math.ceil(r) + 1):
            for dy in range(-math.ceil(r), math.ceil(r) + 1):
                for dz in range(-math.ceil(r), math.ceil(r) + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r and y + dy >= G:
                        bp.blocks[x + dx, y + dy, z + dz] = wood


def foliage(bp, x, y, z, rx, ry, rz, seed):
    for dx in range(-rx, rx + 1):
        for dy in range(-ry, ry + 1):
            for dz in range(-rz, rz + 1):
                d = (dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2
                p = x + dx, y + dy, z + dz
                if d > .91 + .16 * rnd(*p, seed) or bp.blocks.get(p, AIR) != AIR:
                    continue
                species = "oak" if dy < 0 else "azalea"
                if dy >= 1 and seed % 4 == 0 and rnd(*p, 71) < .23:
                    species = "flowering_azalea"
                bp.blocks[p] = M(species + "_leaves[persistent=true]")


def divine_tree(bp):
    for y in range(G, 44):
        radius = 4.1 + 4.8 * math.exp(-(y - G) / 10)
        for dx in range(-10, 11):
            for dz in range(-10, 11):
                a = math.atan2(dz, dx)
                length = math.hypot(dx - math.sin(y / 8), dz)
                if length < radius + .7 * math.cos(7 * a - y / 18):
                    bp.blocks[X + dx, y, Z + dz] = BARK
    # Spreading roots, and two generations of living forks below the crown.
    crowns = []
    for i in range(9):
        angle = i * math.tau / 9 + .16
        def point(radius, height, turn=0):
            return X + round(radius * math.cos(angle + turn)), height, Z + round(radius * math.sin(angle + turn))
        root = point(12, 5, .2)
        limb(bp, point(4, 10), root, 3.1, 2.0)
        limb(bp, root, point(23 + i % 4, G, .31), 2, .75)
        shoulder = point(11, 32 + i % 5, -.18)
        limb(bp, point(1, 22 + i % 4), shoulder, 3.3, 2.25)
        for side in (-1, 1):
            tip = point(22 + (i + side) % 4, 38 + (i * 3 + side) % 7, .18 * side)
            limb(bp, shoulder, tip, 2.2, .85)
            crowns.append((*tip, 7 + i % 3, 4 + i % 2, 7, i * 3 + side))
        crest = point(10 + i % 4, 49 + i % 3)
        limb(bp, (X, 38, Z), crest, 2.5, 1)
        crowns.append((*crest, 9, 6, 9, i))
    for args in crowns + [(X, 53, Z, 10, 6, 10, 9)]:
        foliage(bp, *args)


def pavilion(bp, x):
    z = Z
    # Raised reading bays open in all four directions; pointed roofs echo the branch tips.
    for y, radius in ((10, 6), (11, 5), (19, 6)):
        bp.disc(x, y, z, radius, STONE)
    for dx, dz in ((-3,-3),(-3,3),(3,-3),(3,3)):
        bp.pillar(x+dx, z+dz, 12, 17, M("quartz_pillar"))
        bp.set(x+dx, 18, z+dz, BRASS)
    for y, r in enumerate((5.6, 4.8, 4, 3.2, 2.4, 1.4), 20):
        bp.disc(x, y, z, r, COPPER)
    bp.set(x, 26, z, BRASS)
    bp.set(x, 27, z, M("end_rod[facing=up]"))
    bp.set(x, 18, z, M("lantern[hanging=true]"))
    bp.set(x, 12, z-2, M("lectern[facing=south]"))
    for dx in (-2, 2):
        bp.set(x+dx, 12, z, M("birch_stairs[facing=" + ("west" if dx < 0 else "east") + "]"))


def build(bp):
    # Author only the tree clearing and the curving apron. The land outside the roots keeps its own terrain.
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            dx, dz = x-X, z-Z
            radial = math.hypot(dx, dz)
            path_dist = abs(dx - 2 * math.sin(dz / 6))
            path = z >= Z and path_dist <= 3.3
            verge = z >= Z and path_dist <= 5.4 + math.sin(z / 3)
            if radial > 30 + 2 * math.sin(5 * math.atan2(dz, dx)) and not verge:
                continue
            bp.blocks[x,G-1,z] = M("dirt")
            floor = "moss_block" if rnd(x, 1, z, 12) < .31 else "grass_block"
            if path and (path_dist < 1.6 or rnd(x,G,z,5) < .67):
                floor = "dirt_path" if rnd(x,G,z,4) < .38 else "coarse_dirt"
            bp.blocks[x,G,z] = M(floor)
            for y in range(G+1, SIZE[1]):
                bp.blocks[x,y,z] = AIR
    divine_tree(bp)
    # A continuous promenade bridges over the roots. Lime-glass panels mark the thirteen royal houses.
    for x in range(X-23,X+24):
        for z in range(Z-20,Z+21):
            r = math.hypot(x-X,z-Z)
            if 7 < r <= 17.4 or abs(z-Z)<=2 and 13<abs(x-X)<=21:
                bp.blocks[x,10,z] = STONE if r>16.2 else M("birch_planks")
                bp.blocks[x,9,z] = BRASS if r>16.6 else M("birch_planks")
                for y in (11,12,13):
                    bp.blocks[x,y,z] = AIR
                if 16.4<=r<=17.4 and abs(x-X)>3 and abs(z-Z)>3:
                    bp.blocks[x,11,z] = M("smooth_quartz_slab[type=bottom]")
    for i in range(13):
        a = math.tau * i / 13
        px, pz = X + round(13 * math.sin(a)), Z + round(13 * math.cos(a))
        bp.set(px,10,pz,LAMP)
        bp.set(px+1,10,pz,M("lime_stained_glass"))
    for x in (X-20,X+20):
        for dx,dz in ((-3,-3),(-3,3),(3,-3),(3,3)):
            bp.pillar(x+dx,Z+dz,4,10,M("stripped_birch_log"))
        pavilion(bp,x)
    # A public charter room cut into the tree. Its south arch opens directly off the terrace.
    for dx in range(-4, 5):
        for dz in range(-4, 9):
            if dx*dx + dz*dz > 18 and not (abs(dx) <= 2 and dz >= 0):
                continue
            x, z = X + dx, Z + dz
            bp.set(x, 10, z, M("birch_planks"))
            for y in range(11, 16 if abs(dx) < 2 else 15):
                bp.set(x,y,z,AIR)
    for dx in (-3,3):
        bp.pillar(X+dx,Z+6,11,14,M("quartz_pillar"))
        bp.set(X+dx,15,Z+6,BRASS)
        bp.set(X+dx,16,Z+6,STONE)
    bp.fill(X-2,16,Z+6,X+2,16,Z+6,STONE)
    bp.set(X,16,Z+6,LAMP)
    bp.fill(X-2,11,Z-3,X+2,12,Z-3,M("bookshelf"))
    bp.set(X,12,Z-3,LAMP)
    bp.set(X,11,Z-1,M("lectern[facing=south]"))
    for dx in (-5,5):
        bp.set(X+dx,10,Z+11,LAMP)
    for step in range(7):
        z = Z + 24 - step
        y = G + 1 + step
        bp.fill(X-2,G,z,X+2,y-1,z,STONE)
        bp.fill(X-2,y,z,X+2,y,z,M("smooth_quartz_stairs[facing=north]"))
        for dx in (-3,3):
            bp.fill(X+dx,G,z,X+dx,y,z,STONE)
            bp.set(X+dx,y+1,z,M("smooth_quartz_slab[type=bottom]"))
    # Each overhanging leaf column needs a ground sample too: otherwise the terrain fitter
    # can build a dirt pillar up to the first leaf where the crown extends beyond its clearing.
    columns = {(x,z) for x,y,z in bp.blocks if y>G and bp.blocks[x,y,z]!=AIR}
    for x,z in columns:
        if (x,G,z) not in bp.blocks:
            bp.set(x,G-1,z,M("dirt"))
            bp.set(x,G,z,M("grass_block"))
            for y in range(G+1,SIZE[1]):
                bp.blocks.setdefault((x,y,z),AIR)
    # Light the reading bays and all levels of the public promenade, including the stairs' shoulders.
    light_pass(bp,lambda x,y,z: (x-X)**2+(z-Z)**2<29**2 and y<28,4,
               lambda x,y,z:M("lantern"),label="elmine")
