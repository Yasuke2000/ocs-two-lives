"""Morgdahl, a timber landing and water-powered mill yard in the western realm.

SIZE (69, 31, 61), anchor (50, 5, 51) on the south cart road, z slabs 0 and 31.
The western Council map and fan political plate locate Morgdahl. Its sawmill,
contained millpond and crane are our interpretation of the pack's river-mouth realm.
Oak, spruce, pale plaster, brick, slate, iron and weathered copper.
Sources and the distinction between mapped name and invented industry are in design/lore/morgdahl.md.
"""
from math import hypot

from _dwargon_lib import rnd
from _lords_lib import light_pass
from _town_lib import M, Town, lantern_floor, lantern_hung, log, slab

SIZE = (69, 31, 61)
PARTS = [0, 31]
G = 4


def basin(t):
    # Both ends of the channel are bounded. No surveyed river or sea is required.
    for x in range(3, 66):
        for z in range(19, 42):
            pond = hypot((x-11)/9, (z-30)/10)
            tail = hypot((x-58)/7, (z-32)/6)
            wet = pond < 1 or tail < 1 or 11 <= x <= 58 and 29 <= z <= 34
            if wet:
                t.put(x, G, z, M("air"))
                t.put(x, G-1, z, M("water"))
                t.put(x, G-2, z, M("clay" if z % 4 else "gravel"))
            elif 1 <= min(pond,tail) < 1.2:
                t.put(x, G, z, M("mud" if z % 3 else "mossy_cobblestone"))
    for x,z in ((6,29),(8,25),(12,22),(12,37),(57,36),(63,33)):
        if t.get(x,G-1,z) == M("water"):
            t.put(x,G,z,M("lily_pad"))
    for x in range(20, 52):
        for z in (28,35):
            t.put(x, G, z, M("mossy_stone_bricks" if x % 4 == 2 else "stone_bricks"))
    # Sluice gate with an open lower channel.
    for z in (28,35):
        t.fill(20, G, z, 20, G+5, z, log("stripped_oak_log"))
    t.fill(20,G+5,28,20,G+5,35,log("stripped_oak_log","z"))
    t.fill(20,G+2,29,20,G+3,34,M("spruce_planks"))
    t.put(20,G+4,31,M("chain"))
    t.put(20,G+4,32,M("chain"))


def mill(t):
    t.fill(17,G,10,44,G,26,M("spruce_planks"))
    t.ring(17,10,44,26,G+1,15,M("white_terracotta"))
    for x in (17,23,30,37,44):
        for z in (10,26):
            t.fill(x,G+1,z,x,15,z,log("stripped_dark_oak_log"))
        t.fill(x,14,10,x,14,26,log("spruce_log","z"))
        for z in (14,22):
            t.put(x,13,z,lantern_hung())
    for z in (10,26):
        for y in (6,12,15):
            t.fill(17,y,z,44,y,z,log("spruce_log","x"))
        for x in (20,26,33,40):
            t.fill(x-1,8,z,x+1,11,z,M("glass"))
            t.put(x,10,z,log("stripped_oak_log"))
    t.clear(44,G+1,15,44,12,21)
    t.gable(17,10,44,26,16,"slate","x",M("white_terracotta"))
    # Three raised timber vents have their own little gables in the long roof.
    for x in (21,30,39):
        t.ring(x-2,19,x+2,25,17,19,M("spruce_planks"))
        t.fill(x-1,17,25,x+1,18,25,M("waxed_weathered_copper_grate"))
        t.gable(x-2,19,x+2,25,20,"brick","z",M("white_terracotta"))
    # Slide carriage and a vertical framed saw clearly visible from the loading door.
    for z in (16,20):
        t.fill(20,G+1,z,39,G+1,z,log("dark_oak_log","x"))
        t.fill(30,G+1,z,30,12,z,log("stripped_oak_log"))
    t.fill(30,12,16,30,12,20,log("dark_oak_log","z"))
    t.fill(30,8,18,30,11,18,M("iron_bars"))
    t.fill(22,G+1,18,34,G+1,18,log("oak_log","x"))
    t.put(39,G+1,12,M("barrel[facing=up]"))
    t.put(40,G+1,12,M("crafting_table"))
    t.put(41,G+1,12,M("grindstone[face=floor,facing=south]"))


def wheel(t):
    cx, cy = 35, 10
    for x in range(cx-7,cx+8):
        for y in range(cy-7,cy+8):
            dx,dy = x-cx,y-cy
            r = hypot(dx,dy)
            if 5.65 <= r <= 6.8:
                for z in (30,33):
                    t.put(x,y,z,M("spruce_planks"))
            if r <= 6 and (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                t.put(x,y,31,log("stripped_oak_log","y" if abs(dy)>abs(dx) else "x"))
    for dx,dy in ((0,7),(4,6),(6,4),(7,0),(6,-4),(4,-6),(0,-7),
                  (-4,-6),(-6,-4),(-7,0),(-6,4),(-4,6)):
        t.fill(cx+dx,cy+dy,30,cx+dx,cy+dy,33,log("dark_oak_log","z"))
    t.fill(cx,cy,24,cx,cy,35,log("stripped_dark_oak_log","z"))
    for x in (33,37):
        t.fill(x,G+1,35,x,8,35,M("stone_bricks"))
    t.fill(33,9,35,37,9,35,log("oak_log","x"))
    t.put(cx,cy,36,M("waxed_exposed_chiseled_copper"))


def yard(t):
    t.pave(47,6,53,60)
    # Carry the road across the millrace. The deck meets the yard at grade.
    t.fill(47,G,27,53,G,36,M("spruce_planks"))
    for x in (46,54):
        t.fill(x,G,27,x,G,36,log("oak_log","z"))
        for z in range(27,37):
            t.put(x,G+1,z,M("spruce_fence[north=true,south=true]"))
        for z in (27,36):
            t.put(x,G+1,z,log("spruce_log"))
            t.put(x,G+2,z,lantern_floor())
    t.pave(11,43,46,54,"street")
    t.pave(43,15,55,21,"cobble")
    # An open lumber shelter at the far side of the cartway.
    for x in (55,64):
        for z in (8,15,22):
            t.fill(x,G+1,z,x,10+(65-x)//4,z,log("spruce_log"))
    for z in range(7,24):
        for x in range(54,66):
            t.put(x,11+(65-x)//4,z,slab("spruce","top"))
    for z in (10,14,18):
        for x in range(57,63):
            t.fill(x,G+1,z,x,G+2,z,log("stripped_birch_log","x"))
    # The loading jib holds a bundled oak trunk just above its trestles.
    for x,z in ((31,44),(31,47),(34,44),(34,47)):
        t.fill(x,G+1,z,x,11,z,log("dark_oak_log"))
    t.fill(31,12,44,34,12,47,M("spruce_planks"))
    t.fill(32,13,45,32,22,45,log("stripped_spruce_log"))
    t.fill(24,21,45,35,21,45,log("dark_oak_log","x"))
    for i in range(6):
        t.put(31-i,15+i,45,M("spruce_planks"))
    for x in (24,27):
        t.fill(x,10,45,x,20,45,M("chain"))
    t.fill(22,9,45,29,9,45,log("oak_log","x"))
    for x in (23,28):
        t.put(x,G+1,45,M("stripped_oak_log"))
    for x in (13,21):
        t.fill(x,G+1,46,x,G+1,52,log("dark_oak_log","z"))
    for z in (47,49,51):
        t.fill(11,G+2,z,25,G+2,z,log("oak_log","x"))
    for z in (48,50):
        t.fill(12,G+3,z,24,G+3,z,log("oak_log","x"))


def build(bp):
    t = Town(bp,G)
    t.base_ground()
    basin(t)
    mill(t)
    wheel(t)
    yard(t)
    for x,z in ((5,8),(10,13),(7,53),(61,49),(57,55),(35,6)):
        t.tree(x,z,"birch" if x%2 else "oak",6,3)
    for x in range(3,66):
        for z in range(3,58):
            if t.get(x,G,z) != M("grass_block") or t.get(x,G+1,z) != M("air"):
                continue
            if rnd(x,G,z,23) < .11:
                t.put(x,G+1,z,M("fern" if x<15 else "short_grass"))
    for x,z in ((46,15),(46,50),(26,42),(57,25),(53,57)):
        t.lamp(x,z,h=2,post="spruce_fence")
    for x,z in ((20,14),(26,22),(35,14),(40,23),(56,11),(63,21)):
        t.put(x,G,z,M("ochre_froglight"))
    light_pass(bp, lambda x,y,z: (17 <= x <= 44 and 10 <= z <= 26 and y < 22)
               or (54 <= x <= 65 and 7 <= z <= 23 and y <= 11), G+1,
               lambda x,y,z: lantern_floor(), label="morgdahl")
    t.check_support()
