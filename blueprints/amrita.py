"""Amrita, buried gallery of Jistav's ancient capital. SIZE (69, 32, 75), three z slabs.

South walking anchor (34, 16, 68). A sunken stair enters a vaulted underground gallery between two
inert ward-golems. Light novel volume 10, pp. 15–16 (Japanese edition), official Jistav glossary,
source map and adaptations in design/lore/amrita.md. Tuff, deepslate, moss, copper, calcite and glass.
"""
import math

from _dwargon_lib import AIR, rnd
from _sites_lib import M
from _lords_lib import light_pass

SIZE = (69, 32, 75)
PARTS = [0, 25, 50]
X = 34
G = 15
WALL = M("polished_tuff")
RIB = M("chiseled_tuff_bricks")
STONE = M("tuff_bricks")
DARK = M("deepslate_tiles")
EYE = M("ochre_froglight")
METAL = M("waxed_weathered_cut_copper")


def hillside(bp):
    for z in range(SIZE[2]):
        for x in range(SIZE[0]):
            dx, dz = x-X, z-31
            r = math.hypot(dx/33, dz/32)
            # The approach peters out into the surrounding turf rather than a retaining wall.
            path = z >= 45 and abs(dx) <= 4 + math.sin(z / 4)
            verge = z >= 45 and abs(dx) <= 6.8 + math.sin(z / 5)
            if r > .98 + .035 * math.cos(5*math.atan2(dz,dx)) and not verge:
                continue
            height = G + round(6 * max(0,1-r*r) ** 1.4)
            if z >= 44 and abs(dx) <= 9:
                height = G
            floor = "moss_block" if rnd(x, G, z, 83)<.35 else "grass_block"
            if path and (abs(dx)<2 or rnd(x,G,z,7)<.74):
                floor = "coarse_dirt" if rnd(x,G,z,21)<.6 else "gravel"
            # The nave, side niches, and cuts receive real stone behind every carved face.
            base = 0 if abs(dx) <= 22 and 4 <= z <= 59 else G-1
            for y in range(base, height):
                bp.blocks[x,y,z]=M("dirt" if y>=height-2 else "tuff")
            bp.blocks[x,height,z]=M(floor)
            for y in range(height+1,SIZE[1]):
                bp.blocks[x,y,z]=AIR


def chamber(bp):
    # Barrel vault running north–south, with a ring of stone behind every carved arch.
    for z in range(8,42):
        for dx in range(-15,16):
            x = X+dx
            soffit = 8 + round(7 * math.sqrt(max(0,1-(dx/15)**2)))
            rib = z in (8,15,23,31,39)
            cap = soffit - int(rib)
            bp.set(x,1,z,DARK if abs(dx) in (0,6,14) or z in (9,39) else WALL)
            for y in range(2,cap+1):
                bp.blocks[x,y,z]=AIR
            bp.set(x,cap+1,z,RIB if rib else STONE)
            if abs(dx)==15:
                bp.fill(x,2,z,x,cap,z,STONE if rib else WALL)
            if rib and abs(dx)==14:
                bp.fill(x,2,z,x,cap,z,RIB)
                bp.set(x,6,z,EYE)
                bp.set(x,7,z,METAL)
    # Memorial bays behind the spring line on both sides. Each can be entered from the nave.
    for side in (-1,1):
        for z in (12,19,27,35):
            for d in range(14,20):
                x = X+side*d
                bp.fill(x,1,z-1,x,1,z+1,DARK)
                bp.fill(x,2,z-1,x,5,z+1,AIR)
                bp.set(x,6,z,STONE)
            back = X+side*20
            bp.fill(back,2,z-1,back,5,z+1,RIB)
            bp.set(back,4,z,EYE)
            bp.set(back,3,z,METAL)
            bp.set(X+side*18,2,z,M("polished_deepslate_slab[type=bottom]"))
    # An inscribed sealed door terminates the public ruin. Luminous joints carry the eye to its crown.
    for x in range(X-6,X+7):
        for y in range(2,14):
            dx=abs(x-X)
            surface=METAL if dx<=3 and y<=11-dx else DARK
            if dx==4 and 3<=y<=9 or dx<=4 and y==13-dx:
                surface=EYE if dx in (0,4) else M("calcite")
            bp.set(x,y,7,surface)
    # A joint divides the copper leaves; their inset stone lozenge echoes the wardens' eyes.
    for y in range(2, 11):
        bp.set(X,y,7,DARK)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            distance = abs(dx) + abs(dy)
            if distance == 2:
                bp.set(X+dx,7+dy,8,M("chiseled_polished_blackstone"))
            elif distance == 1:
                bp.set(X+dx,7+dy,8,M("calcite"))
    bp.set(X,7,8,EYE)
    # Shallow stepped niches articulate the surviving end wall to either side of the seal.
    for side in (-1, 1):
        x = X + side*10
        for dx in range(-2, 3):
            ceiling = 10 - abs(dx)
            bp.fill(x+dx,2,7,x+dx,ceiling,7,WALL)
            bp.set(x+dx,ceiling+1,8,RIB)
            bp.set(x+dx,2,8,RIB)
        bp.fill(x,3,8,x,7,8,METAL)
        bp.set(x,7,8,M("chiseled_tuff"))
    for z in range(10,39,4):
        for side in (-1,1):
            bp.set(X+side*6,1,z,EYE)


def sentinel(bp, x):
    """Two tall stone figures set flush with the cut. Their mineral cores are decorative."""
    bp.fill(x-2, G-1, 47, x+2,G+1,51,DARK)
    for dx in (-1,1):
        bp.fill(x+dx,G+2,48,x+dx,G+4,50,STONE)
        bp.fill(x+dx,G+2,50,x+dx,G+2,51,RIB)
    bp.fill(x-2,G+5,48,x+2,G+8,50,STONE)
    bp.set(x,G+7,50,EYE)
    for dx in (-3,3):
        bp.fill(x+dx,G+5,48,x+dx,G+8,49,RIB)
        bp.set(x+dx,G+4,49,METAL)
    bp.fill(x-1,G+9,48,x+1,G+11,50,RIB)
    bp.fill(x-1,G+10,50,x+1,G+10,50,DARK)
    for dx in (-1,1):
        bp.set(x+dx,G+10,50,EYE)


def build(bp):
    hillside(bp)
    chamber(bp)
    # Fifteen north-facing treads descend from the surface apron towards the buried hall.
    for z in range(40,61):
        step = max(1, min(G, z-42))
        for x in range(X-4,X+5):
            bp.fill(x,step+1,z,x,SIZE[1]-1,z,AIR)
            tread = M("polished_tuff_stairs[facing=south]") if 44<=z<=57 else WALL
            bp.set(x,step,z,tread)
        for x in (X-5,X+5):
            bp.fill(x,step,z,x,G,z,STONE)
            bp.set(x,G+1,z,M("tuff_brick_slab[type=bottom]"))
            if z in (43,48,53,58):
                bp.set(x,step+1,z,EYE)
    # The stair emerges beneath a corbelled transverse portal. Three intact ribs step up from it.
    for z in (40,43,46):
        top = 12+(z-40)//3*2
        for side in (-1,1):
            x=X+side*5
            bp.fill(x,2,z,x,top-2,z,RIB)
            bp.set(x-side, top-1,z,STONE)
            bp.set(x-side*2, top,z,STONE)
        bp.fill(X-2,top+1,z,X+2,top+1,z,METAL)
        bp.set(X,top+1,z,EYE)
    # Collapsed oculus pierces both hill and vault, with part of its curb broken down.
    for x in range(X-6,X+7):
        for z in range(16,29):
            r=math.hypot(x-X,z-22)
            if r<=4.4:
                bp.fill(x,13,z,x,SIZE[1]-1,z,AIR)
                if r>=3.5:
                    bp.set(x,14,z,METAL)
            elif r<=6:
                tops=[y for y in range(15,25) if bp.blocks.get((x,y,z),AIR)!=AIR]
                if tops:
                    y=max(tops)
                    bp.set(x,y,z,STONE)
                    # A continuous low parapet protects the shaft, with uneven capstones above it.
                    bp.set(x,y+1,z,M("tuff_brick_wall"))
                    if z<21 and rnd(x,y,z,91)<.42:
                        bp.set(x,y+2,z,M("tuff_brick_slab[type=bottom]"))
    # Broken column bases trace the earlier building around the exposed oculus.
    # Their surviving parts follow the actual slope instead of floating above the turf.
    for x,z,h in ((17,16,3),(19,30,1),(23,40,3),(50,14,2),(51,31,3),(45,39,1)):
        for dx in range(-1,2):
            for dz in range(-1,2):
                bx,bz=x+dx,z+dz
                top=max(y for y in range(G,25) if bp.blocks.get((bx,y,bz),AIR)!=AIR)
                bp.set(bx,top,bz,STONE)
                bp.set(bx,top+1,bz,M("tuff_brick_slab[type=bottom]"))
        top=max(y for y in range(G,25) if bp.blocks.get((x,y,z),AIR)!=AIR)
        bp.fill(x,top,z,x,top+h,z,RIB)
        bp.set(x,top+h+1,z,METAL)
    for x in (X-10,X+10):
        sentinel(bp,x)
    # Excavation markers and fragments lead from the exterior to the first surviving arch.
    for x,z in ((X-7,57),(X+7,57),(X-6,62),(X+6,62)):
        bp.set(x,G,z,STONE)
        bp.set(x,G+1,z,RIB)
        bp.set(x,G+2,z,M("lantern"))
    light_pass(bp,lambda x,y,z: abs(x-X)<=20 and 7<=z<=59 and y<=G+1,2,
               lambda x,y,z:M("lantern"),label="amrita")
