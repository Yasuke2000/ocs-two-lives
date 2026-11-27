"""Diagnose native lake/river water-level steps,including the open C23 style/source review.

Run after matching R115 normal staging. Exit1 means a measured interface exceeds
the2-block ordinary-step diagnostic threshold;the owner did not set an exact numeric cap. It is not a map_check.py result.
"""
from pathlib import Path
import argparse,hashlib,json,csv,io,sys,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,Point
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--round',type=int,choices=(115,119,130),default=115)
round_number=parser.parse_args().round
pinned={130: 'ade502105956db450831e0991b2f10e6b29f8b73a1827f1d0184299c505917bb', 115:'89b01c4c960b6347f680c50114debaa979c1a11c7bfd1f77b35c5268f03c847b',119:'4093f844d341962bc49704a6c2f1564c6ffa69ea19f18f5fdcaa6712a5334f89'}
sha=hashlib.sha256((ROOT/'world/map.svg').read_text(encoding='utf-8').encode()).hexdigest()
assert sha==pinned[round_number]
index=json.loads((ROOT/'world/build/index.json').read_text(encoding='utf-8'))
assert index['source_sha256']==sha
bank=json.loads((ROOT/f'world/lake-banks-r{round_number}.json').read_text(encoding='utf-8'))
assert bank['source_sha256']==sha
root=ET.parse(ROOT/'world/map.svg').getroot();byid={e.get('id'):e for e in root.iter() if e.get('id')}
rows=[]
for lake in bank['lakes']:
    poly=Polygon([tuple(map(float,p.split(','))) for p in byid[lake['id']].get('points').split()])
    for river in lake['expected_near_endpoint_river_ids']:
        e=byid[river];path=[tuple(map(float,p.split(','))) for p in e.get('points').split()]
        direction='outlet' if poly.distance(Point(path[0]))<=8 else 'inlet'
        contacts=[v for v in lake['wet_contacts'] if river in v['rivers']]
        levels=sorted({v['water_first_air'] for v in contacts})
        gap=max((abs(v-lake['water_first_air']) for v in levels),default=None)
        rows.append({'lake':lake['id'],'river':river,'direction':direction,'lake_first_air':lake['water_first_air'],'adjacent_river_first_airs':levels,'maximum_level_difference':gap,'normal_step_threshold':2,'small_step_pass':gap is not None and gap<=2,'scope':'Adjacent exported water first-air;not runtime fluid simulation.'})
assert len(rows)==8
report={'round':round_number,'source_sha256':sha,'criterion':'Diagnostic 2-block threshold matches ordinary converter MAX_STEP. The brief asks for small falls but sets no exact numeric cap;larger headwaterfalls require style/source assessment, not automatic rejection.','passing_interfaces':sum(v['small_step_pass'] for v in rows),'interfaces':len(rows),'open_conflict':'C23','overall_pass':all(v['small_step_pass'] for v in rows),'rows':rows,'limits':'Containing four-block export samples;does not simulate a filled vertical fall,fluid updates or final terrain noise.'}
(ROOT/f'world/river-head-profiles-r{round_number}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
buf=io.StringIO(newline='');fields=[k for k in rows[0] if k!='scope'];writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
for row in rows:
    rec={k:row[k] for k in fields};rec['adjacent_river_first_airs']=';'.join(map(str,rec['adjacent_river_first_airs']));writer.writerow(rec)
(ROOT/f'world/river-head-profiles-r{round_number}.csv').write_text(buf.getvalue().replace('\r\n','\n'),encoding='utf-8',newline='\n')
W=np.asarray(Image.open(ROOT/'world/build/water.png'));H=np.asarray(Image.open(ROOT/'world/build/height.png')).astype(float)/16-64
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="660" viewBox="0 0 1160 660"><rect width="1160" height="660" fill="#edf0e8"/><g font-family="Arial" fill="#213e4b"><text x="28" y="36" font-size="25">Open C23: connected in plan, large exported water-level steps</text><text x="28" y="65" font-size="15">Containing four-block samples; blue dots are water levels, brown line is terrain first-air. No fluid simulation.</text>']
for col,river in enumerate(['ulgr-spring-brook','laura-mountain-falls']):
    e=byid[river];path=[tuple(map(float,p.split(','))) for p in e.get('points').split()];start=np.asarray(path[0],float);vector=np.asarray(path[1],float)-start;vector/=np.linalg.norm(vector)
    selected=next(v for v in rows if v['river']==river);ox=60+col*570;top=132;bottom=530;low=50 if col==0 else 115;high=115 if col==0 else 170
    def xy(distance,height):return ox+(distance+40)/110*480,bottom-(height-low)/(high-low)*(bottom-top)
    terrain=[];water=[]
    for distance in np.arange(-40,71,2):
        x,z=start+vector*distance;i=int((x-index['box']['x0'])//4);j=int((z-index['box']['z0'])//4)
        px,py=xy(float(distance),float(H[j,i]));terrain.append(f'{px:.2f},{py:.2f}')
        if W[j,i]:
            px,py=xy(float(distance),int(W[j,i])-64);water.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="2.6" fill="#297fa5"/>')
    svg.extend([f'<text x="{ox}" y="104" font-size="20">{river}</text>',f'<path d="M{ox},{top} V{bottom} H{ox+480}" fill="none" stroke="#8da097"/>'])
    for height in range(low,high+1,10):
        px,py=xy(-40,height);svg.extend([f'<path d="M{ox},{py:.2f} H{ox+480}" stroke="#d4dbce"/>',f'<text x="{ox-8}" y="{py+5:.2f}" font-size="13" text-anchor="end">{height}</text>'])
    svg.extend([f'<polyline points="{" ".join(terrain)}" fill="none" stroke="#907148" stroke-width="2.5"/>',*water,f'<text x="{ox}" y="561" font-size="15">distance relative to current source head:−40 to+70 blocks</text>',f'<text x="{ox}" y="591" font-size="17">Lake {selected["lake_first_air"]};adjacent river {"/".join(map(str,selected["adjacent_river_first_airs"]))};difference {selected["maximum_level_difference"]}</text>'])
svg.append(f'<text x="28" y="634" font-size="15">Bank/contact checks pass; the 2-block diagnostic flags {report["interfaces"]-report["passing_interfaces"]} larger head transition(s). Assess waterfall intent and fluid placement separately.</text></g></svg>')
(ROOT/f'world/river-head-profiles-r{round_number}.svg').write_text(''.join(svg),encoding='utf-8',newline='\n')
print(json.dumps({'interfaces':8,'passing':report['passing_interfaces'],'failures':[v for v in rows if not v['small_step_pass']]}))
sys.exit(0 if report['overall_pass'] else 1)
