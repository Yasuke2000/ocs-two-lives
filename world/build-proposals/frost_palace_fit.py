"""Read-only comparison of the current coast and two inland palace entrance parcels.

Run from the repository with python -B world/build-proposals/frost_palace_fit.py.
Requires current normal world/build rasters, NumPy, Pillow and Shapely.
Writes original study SVG/JSON only; never changes the production map or rasters.
"""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from shapely.geometry import Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
index = json.loads((ROOT / "world/build/index.json").read_text(encoding="utf-8"))
sha = hashlib.sha256((ROOT / "world/map.svg").read_text(encoding="utf-8").encode()).hexdigest()
assert sha == index["source_sha256"], "Normal rasters must match the current source"
height = np.asarray(Image.open(ROOT / "world/build/height.png")).astype(float) / 16 - 64
water = np.asarray(Image.open(ROOT / "world/build/water.png"))
coast = next(e for e in ET.parse(ROOT / "world/map.svg").getroot().iter() if e.get("id") == "ice-continent")
land = Polygon([tuple(map(float, p.split(","))) for p in coast.get("points").split()])


def sample(x, z):
    u = (x-index["box"]["x0"])/4-.5
    v = (z-index["box"]["z0"])/4-.5
    i, j = np.floor(u).astype(int), np.floor(v).astype(int)
    s, t = u-i, v-j
    return (1-s)*(1-t)*height[j,i]+s*(1-t)*height[j,i+1]+(1-s)*t*height[j+1,i]+s*t*height[j+1,i+1]


# Existing model: box85x69, local anchor42,4,65; eight-block buffer.
# Column centres include x=-49.5..50.5 and z=-72.5..11.5.
xx, zz = np.meshgrid(np.arange(-50, 51)+.5, np.arange(-73, 12)+.5)
assert xx.size == 101*85
rows = []
for label, x, z in (("Current coast",-1500,-3310),("Earlier centroid proposal",-1660,-3820),("Central snowfield alternative",-1530,-3680)):
    values = sample(xx+x, zz+z)
    i = np.floor((xx+x-index["box"]["x0"])/4).astype(int)
    j = np.floor((zz+z-index["box"]["z0"])/4).astype(int)
    floor = float(np.rint(np.median(values)))
    rows.append({"label":label,"x":x,"z":z,"centre_distance_to_current_land_centroid":Point(x,z).distance(land.centroid),"centre_distance_to_coast":Point(x,z).distance(land.boundary),"buffered_columns":int(xx.size),"minimum_first_air":float(values.min()),"maximum_first_air":float(values.max()),"relief":float(np.ptp(values)),"median_first_air":float(np.median(values)),"trial_first_air":floor,"maximum_absolute_height_difference_to_trial_floor":float(abs(values-floor).max()),"sampled_water_columns":int(np.count_nonzero(water[j,i])),"buffered_corner_radius":float(np.hypot(xx,zz).max()),"minimum_integer_radius_for_rectangle":int(np.ceil(np.hypot(xx,zz).max()))})
report={"round":103,"source_sha256":sha,"height_raw_sha256":hashlib.sha256((ROOT/"world/build/height.png").read_bytes()).hexdigest(),"current_land_centroid":[land.centroid.x,land.centroid.y],"method":"Every integer buffered column centre; bilinear four-block normal height; containing-cell water; unrotated existing entrance model, not full palace. Trial floor is rounded median, not an applied terrace.","candidates":rows,"active_map_changed":False,"limits":"No final noise, voxel support, density, collision, path or whole-palace fit proof. Snowfield alternative is original geography interpretation, not a canonical coordinate. Existing generated coast preparation affects the coast comparison."}
(ROOT/"world/frost-palace-fit-r103.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="760" viewBox="0 0 1120 760">','<rect width="1120" height="760" fill="#edf0e8"/>','<g font-family="Arial" fill="#213e4b">','<text x="32" y="38" font-size="25">Frost Palace: compare central terrain before moving the marker</text>','<text x="32" y="65" font-size="15">Original proposal; WN central setting. LN agreement and initial-state architecture remain open.</text>','<svg x="35" y="88" width="1050" height="340" viewBox="-3000 -4480 2780 1320">',f'<polygon points="{coast.get("points")}" fill="#dae6e7" stroke="#52747e" stroke-width="8"/>']
colors=['#aa683c','#a64242','#197582']
for row,color in zip(rows,colors):
    x,z=row['x'],row['z']
    svg.extend([f'<circle cx="{x}" cy="{z}" r="89" fill="none" stroke="{color}" stroke-width="7"/>',f'<rect x="{x-50}" y="{z-73}" width="101" height="85" fill="{color}" fill-opacity=".4"/>'])
svg.append('</svg>')
for k,(row,color) in enumerate(zip(rows,colors)):
    ox=35+k*365
    svg.append(f'<text x="{ox}" y="450" font-size="17" fill="{color}">{row["label"]}</text>')
    svg.append(f'<text x="{ox}" y="472" font-size="14">({row["x"]}, {row["z"]})</text>')
    zs=np.linspace(-72.5,11.5,100)
    vals=sample(row['x']+np.zeros(100),row['z']+zs)
    pts=' '.join(f'{ox+i*3.1:.2f},{650-(v-60)*1.25:.2f}' for i,v in enumerate(vals))
    svg.append(f'<path d="M{ox},490 V650 H{ox+310}" fill="none" stroke="#9aa9a5"/>')
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>')
    svg.append(f'<text x="{ox}" y="678" font-size="14">Whole buffer: H {row["minimum_first_air"]:.2f} to {row["maximum_first_air"]:.2f}</text>')
svg.extend(['<text x="35" y="710" font-size="14">Profiles: centreline north to south; common H60-188 scale. Survey includes 8,585 columns per alternative.</text>','<text x="35" y="735" font-size="14">89-block radius covers this buffered entrance rectangle only; no whole-palace size or in-game fit is established.</text>','</g></svg>'])
(ROOT/"world/frost-palace-fit-r103.svg").write_text("\n".join(svg),encoding="utf-8")
print(json.dumps(rows,indent=2))
