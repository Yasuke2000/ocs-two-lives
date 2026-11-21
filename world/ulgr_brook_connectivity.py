"""Read-only R119 Ulgr river connectivity and coast-transition measurement.

Run python -B world/ulgr_brook_connectivity.py after matching normal staging.
Checks four-block water neighbours and containing-cell heights, not runtime fluids.
"""
from pathlib import Path
from collections import deque
import hashlib,json,runpy,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Polygon,LineString
ROOT=Path(__file__).resolve().parent.parent
source=(ROOT/'world/map.svg').read_text(encoding='utf-8')
sha=hashlib.sha256(source.encode()).hexdigest()
assert sha=='4093f844d341962bc49704a6c2f1564c6ffa69ea19f18f5fdcaa6712a5334f89'
index=json.loads((ROOT/'world/build/index.json').read_text())
assert index['source_sha256']==sha
root=ET.fromstring(source)
byid={e.get('id'):e for e in root.iter() if e.get('id')}
def points(element):return [tuple(map(float,p.split(','))) for p in element.get('points').split()]
mc=runpy.run_path(str(ROOT/'tools/world/map_check.py'))
land=Polygon(mc['parse_path'](byid['mainland'].get('d'))[0][0])
route=LineString(points(byid['ulgr-spring-brook']))
lake=Polygon(points(byid['ulgr-spring']))
assert route.difference(land.buffer(1e-6)).length<1e-6
W=np.asarray(Image.open(ROOT/'world/build/water.png'))
H=np.asarray(Image.open(ROOT/'world/build/height.png')).astype(float)/16-64
x0,z0,x1,z1=route.buffer(120).bounds
i0=int((x0-index['box']['x0'])//4);i1=int((x1-index['box']['x0'])//4)+1
j0=int((z0-index['box']['z0'])//4);j1=int((z1-index['box']['z0'])//4)+1
X=index['box']['x0']+(np.arange(i0,i1)+.5)*4
Z=index['box']['z0']+(np.arange(j0,j1)+.5)*4
q=shapely.points(X[None,:],Z[:,None]);w=W[j0:j1,i0:i1]
cells=shapely.covers(route.buffer(3.000001),q)&(w>0)
start=tuple(np.argwhere(shapely.covers(lake,q)&(w==166))[0])
seen=np.zeros(w.shape,bool);seen[start]=True;queue=deque([start])
while queue:
    y,x=queue.popleft()
    for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
        yy,xx=y+dy,x+dx
        if 0<=yy<w.shape[0] and 0<=xx<w.shape[1] and w[yy,xx]>0 and not seen[yy,xx]:
            seen[yy,xx]=True;queue.append((yy,xx))
assert seen[cells].all()
shore_distance=shapely.distance(q,land.boundary)
mouth_cells=cells&seen&(w==127)
minimum=float(shore_distance[mouth_cells].min())
assert minimum<=8 # two raster cells; finite measurement scope, not an owner rule
end=np.asarray(route.coords[-1]);vector=end-np.asarray(route.coords[-2]);vector/=np.linalg.norm(vector)
samples=[]
for distance in [-12,-8,-4,0,4,8,12]:
    x,z=end+vector*distance;i=int((x-index['box']['x0'])//4);j=int((z-index['box']['z0'])//4)
    samples.append({'distance':distance,'cell_x':index['box']['x0']+(i+.5)*4,'cell_z':index['box']['z0']+(j+.5)*4,'first_air':float(H[j,i]),'explicit_water_first_air':int(W[j,i])-64 if W[j,i] else None})
assert all(s['first_air']<63 for s in samples)
print(json.dumps({'source_sha256':sha,'river_wet_sample_centres':int(cells.sum()),'connected_to_spring':int((cells&seen).sum()),'nearest_level63_river_cell_shore_distance':minimum,'sampled_river_levels':sorted({int(v)-64 for v in w[cells]}),'mouth_continuation':samples,'limits':'Finite native/raster evidence. No final-noise, actual fluid column or in-game acceptance.'},indent=2))
