"""Ulgr Nature Park, the woodland approach to the Dwelling of Spirits.

SIZE (71, 28, 65), anchor (30, 4, 31), two slabs at z 0 and 33.
Episode 22's dark masonry and warm lights inform the chamber. The official map
places the entrance in northern Ulgracia. Our interpretation sets its stone vault
under a wooded chalk bluff and leads a walking trail across a spring on a timber
footbridge. Birch, oak, moss, calcite, tuff, stone bricks and warm frog lights.
Sources and the distinction from the pack's Jura gateway are in design/lore/ulgr_nature_park.md.
"""
from math import hypot, sin

from _dwargon_lib import noise2, rnd
from _lords_lib import light_pass
from _sites_lib import tree
from _town_lib import M, Town, lantern_floor, slab, stair

SIZE = (71, 28, 65)
PARTS = [0, 33]
G = 3


def trail_x(z):
    return 30 if z < 33 else 30 + round(4 * min(1, (z-33)/20))


def landscape(t):
    heights = {}
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            seam = noise2(x, z, 7, 119)
            # Broken chalk faces straddle a stone passage; a lower spur curls around the pool.
            main = 1 - hypot((x-30)/28, (z-15)/16)
            east = 1 - hypot((x-51)/13, (z-23)/19)
            west = 1 - hypot((x-14)/14, (z-23)/13)
            rise = max(main*21, east*12, west*11)
            top = G + max(0, round(rise+2*(seam-.5)))
            for y in range(G, top):
                stone = "calcite" if (y + int(seam*4)) % 7 < 2 else "tuff" if y % 4 else "andesite"
                t.put(x, y, z, M(stone))
            if top > G:
                t.put(x, top, z, M("moss_block" if seam > .4 else "grass_block"))
            heights[x, z] = top
    return heights


def spring(t):
    for x in range(5, 67):
        cz = 39 + round(3*sin(x/9))
        width = 1 + 4*max(0, 1-abs(x-49)/14)
        for z in range(32, 48):
            distance = abs(z-cz)
            if distance < width:
                t.put(x, G-1, z, M("clay" if distance < width/2 else "gravel"))
                t.put(x, G, z, M("water"))
            elif distance < width+1 and x % 4:
                t.put(x, G, z, M("coarse_dirt" if x % 3 else "moss_block"))
    # Slightly raised deck spans both banks. Slab approaches keep the footpath continuous.
    for z in range(33, 45):
        for x in range(29, 36):
            t.put(x, G+1, z, slab("spruce") if z in (33, 44) else M("spruce_planks"))
        if z in (33, 36, 41, 44):
            for x in (28, 36):
                t.fill(x, G-1, z, x, G+2, z, M("stripped_oak_log"))
                if z in (36, 41):
                    t.put(x, G+3, z, lantern_floor())
    for x in (28, 36):
        for z in range(34, 44):
            if z not in (36, 41):
                t.put(x, G+2, z, M("oak_fence[north=true,south=true]"))


def vault(t):
    # A barrel vault passed on foot, narrowing to an inset sealed stone leaf.
    for z in range(11, 31):
        for x in range(22, 39):
            dx = abs(x-30)
            ceiling = 14 - max(0, dx-3)
            if dx < 7 and z > 11:
                t.clear(x, G+1, z, x, ceiling-1, z)
            t.put(x, G, z, M("chiseled_stone_bricks" if dx == 5 else "polished_andesite"))
            if dx >= 7 or z == 11:
                t.fill(x, G+1, z, x, ceiling, z, M("stone_bricks"))
            t.put(x, ceiling, z, M("mossy_stone_bricks" if (x+z)%5==0 else "stone_bricks"))
            if z in (12, 18, 24, 30):
                if dx >= 6:
                    t.fill(x, G+1, z, x, ceiling, z, M("polished_tuff"))
                else:
                    t.put(x, ceiling-1, z, M("chiseled_tuff_bricks"))
        if z in (14, 20, 26, 29):
            for x in (23, 37):
                t.put(x, 7, z, M("ochre_froglight"))
                t.put(x, 6, z, M("chiseled_stone_bricks"))
    for x in range(27, 34):
        h = 11 - max(0, abs(x-30)-1)
        t.fill(x, G+1, 12, x, h, 12, M("polished_deepslate"))
        t.put(x, h, 13, M("waxed_oxidized_cut_copper"))
        if x in (28, 32):
            t.put(x, 6, 13, M("chiseled_copper"))
    t.put(30, 9, 13, M("verdant_froglight"))
    # Moss-covered earth softens the roof wherever the natural terrain was lower.
    for z in range(11, 31):
        for x in range(22, 39):
            ceiling = 14-max(0,abs(x-30)-3)
            if t.get(x,ceiling+1,z) == M("air"):
                t.put(x,ceiling+1,z,M("moss_block"))


def build(bp):
    t = Town(bp, G)
    t.base_ground()
    heights = landscape(t)
    for z in range(30, 65):
        cx = trail_x(z)
        for x in range(cx-2,cx+3):
            t.put(x, G, z, M("gravel" if abs(x-cx)<2 else "coarse_dirt"))
            t.clear(x, G+1, z, x, max(G+3, heights[x,z]+1), z)
    spring(t)
    vault(t)
    for x, z, h in ((8,12,6),(15,18,8),(21,9,6),(38,8,5),(46,17,7),(54,11,8),
                    (59,29,7),(65,34,6),(7,31,6),(10,49,8),(19,55,5),(58,50,7),
                    (50,60,6),(4,58,5),(65,57,7)):
        tree(bp, x, heights[x,z]+1, z, h, "birch" if x%2 else "oak", wide=3)
    for x in range(4,67):
        for z in range(45,62):
            if abs(x-trail_x(z)) <= 3 or t.get(x,G+1,z) != M("air"):
                continue
            value = rnd(x, G, z, 29)
            if value < .13:
                flower = "oxeye_daisy" if x < 33 else "cornflower"
                t.put(x,G+1,z,M(flower if value < .045 else "short_grass"))
    # A smaller path runs around the pool to a pair of mossy springheads.
    for x in range(36,60):
        z = 47 + round(1.3*sin(x/4))
        for dz in (-1,0,1):
            t.put(x,G,z+dz,M("gravel" if dz == 0 else "coarse_dirt"))
            t.clear(x,G+1,z+dz,x,G+2,z+dz)
    for x,z,h in ((55,36,3),(57,36,2),(58,38,2),(19,40,1),(10,37,2)):
        t.fill(x,G,z,x,G+h,z,M("mossy_cobblestone"))
        t.put(x,G+h,z,M("moss_block"))
        t.put(x+1,G+1,z,slab("mossy_cobblestone"))
    # Rest stop beside the approach, with an unobstructed view into the vault.
    for x in (37, 41):
        t.put(x, G+1, 49, M("oak_log[axis=z]"))
    t.fill(38, G+1, 49, 40, G+1, 49, stair("oak", "south"))
    for x, z in ((27,31),(37,48),(38,56)):
        t.lamp(x,z,h=2,post="oak_fence")
    light_pass(bp, lambda x,y,z: 22 <= x <= 38 and 11 <= z <= 30 and y < 14,
               G+1, lambda x,y,z: lantern_floor(), label="ulgr_nature_park")
    t.check_support()
