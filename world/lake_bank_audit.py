"""Audit every native lake's banks and river contacts in matching normal rasters.

Default: python -B world/lake_bank_audit.py
Baseline: add --baseline --svg <old.svg> --rasters <old-build> --out-base <private-path>.
Reads source/PNG data only; writes its explicit JSON/CSV report. No world apply.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json,sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Polygon,Point,LineString

ROOT=Path(__file__).resolve().parent.parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--svg',type=Path,default=ROOT/'world/map.svg')
ap.add_argument('--rasters',type=Path,default=ROOT/'world/build')
ap.add_argument('--out-base',type=Path)
ap.add_argument('--baseline',action='store_true')
ap.add_argument('--round',type=int,choices=(115,119,125),default=115)
args=ap.parse_args()
assert not args.baseline or args.out_base is not None,'Baseline output needs an explicit destination'
assert not args.baseline or args.round==115,'Historical baseline belongs to R115'
out=args.out_base or ROOT/f'world/lake-banks-r{args.round}'
expected='2463d771cd28cff62138fe2e87ae0dc0dd8bccc7c3d02bc21f6bd6bbb3ed7426' if args.baseline else '89b01c4c960b6347f680c50114debaa979c1a11c7bfd1f77b35c5268f03c847b'
if args.round==125:expected='a637aa5ce39fea793ec2ca9aa4d12e6b328c7f67d074cdd537a941e293307ef0'
if args.round==119:expected='4093f844d341962bc49704a6c2f1564c6ffa69ea19f18f5fdcaa6712a5334f89'
sha=hashlib.sha256(args.svg.read_text(encoding='utf-8').encode()).hexdigest()
index=json.loads((args.rasters/'index.json').read_text(encoding='utf-8'))
assert sha==expected==index['source_sha256'],'Audit profile and normal staging must match source'
H=np.asarray(Image.open(args.rasters/'height.png')).astype(float)/16-64
W=np.asarray(Image.open(args.rasters/'water.png'))
assert H.shape==W.shape
root=ET.parse(args.svg).getroot();ns={'s':'http://www.w3.org/2000/svg'}
def pts(e):return [tuple(map(float,p.split(','))) for p in e.get('points').split()]
rivers=[(e.get('id'),LineString(pts(e)),max(float(e.get('data-width'))/2,2.9),pts(e)) for e in root.find('s:g[@id="rivers"]',ns)]
def neighbors(a):
    b=np.zeros_like(a);b[1:]|=a[:-1];b[:-1]|=a[1:];b[:,1:]|=a[:,:-1];b[:,:-1]|=a[:,1:]
    return b
rows=[]
for e in root.find('s:g[@id="lakes"]',ns):
    p=Polygon(pts(e));x0,z0,x1,z1=p.bounds
    i0=max(0,int((x0-index['box']['x0'])//4)-3);i1=min(W.shape[1],int((x1-index['box']['x0'])//4)+4)
    j0=max(0,int((z0-index['box']['z0'])//4)-3);j1=min(W.shape[0],int((z1-index['box']['z0'])//4)+4)
    xx=index['box']['x0']+(np.arange(i0,i1)+.5)*4;zz=index['box']['z0']+(np.arange(j0,j1)+.5)*4
    inside=shapely.intersects_xy(p,xx[None,:],zz[:,None]);strict=shapely.contains_xy(p,xx[None,:],zz[:,None])
    w=W[j0:j1,i0:i1];h=H[j0:j1,i0:i1];lv=int(e.get('data-level'))
    core=inside&(w==lv+64);adj=neighbors(core);bank=adj&(w==0);external=bank&~inside;internal=bank&inside
    dry=inside&(w==0);wrong=inside&(w!=0)&(w!=lv+64)
    ties=[]
    for y,x in zip(*np.where(dry)):
        q=Point(xx[x],zz[y]);ties.append({'x':q.x,'z':q.y,'boundary_distance':q.distance(p.boundary),'strictly_interior':p.contains(q),'first_air':float(h[y,x])})
    contacts=[];observed=set();unclassified=[]
    for y,x in zip(*np.where(adj&~inside&(w!=0))):
        q=Point(xx[x],zz[y]);matches=[id for id,line,half,_ in rivers if q.distance(line)<=half+1e-7]
        item={'x':q.x,'z':q.y,'water_first_air':int(w[y,x])-64,'rivers':matches}
        contacts.append(item);observed.update(matches)
        if not matches:unclassified.append(item)
    # This finite proximity rule is a design-connection candidate,not canon evidence.
    expected_links=sorted(id for id,_,_,path in rivers if min(p.distance(Point(path[0])),p.distance(Point(path[-1])))<=8)
    missing=sorted(set(expected_links)-observed)
    depth=lv-h[core]
    row={'id':e.get('id'),'water_first_air':lv,'nominal_depth':int(e.get('data-depth')),'source_samples':int(inside.sum()),'source_wet_samples':int(core.sum()),'strict_interior_missing_water':int(np.count_nonzero(strict&(w==0))),'dry_boundary_samples':len(ties),'wrong_water_level_samples':int(wrong.sum()),'external_dry_bank_samples':int(external.sum()),'internal_dry_boundary_bank_samples':int(internal.sum()),'minimum_external_freeboard':float((h[external]-lv).min()) if external.any() else None,'minimum_all_dry_bank_freeboard':float((h[bank]-lv).min()) if bank.any() else None,'dry_bank_below_plus2':int(np.count_nonzero(bank&(h<lv+2))),'minimum_sampled_depth':float(depth.min()) if depth.size else None,'maximum_sampled_depth':float(depth.max()) if depth.size else None,'nonpositive_depth_samples':int(np.count_nonzero(depth<=0)),'external_wet_samples':len(contacts),'observed_river_ids':sorted(observed),'expected_near_endpoint_river_ids':expected_links,'missing_expected_river_ids':missing,'unclassified_wet_contacts':unclassified,'boundary_samples':ties,'wet_contacts':contacts}
    row['bank_pass']=bool(core.any()) and not any([row['strict_interior_missing_water'],row['wrong_water_level_samples'],row['dry_bank_below_plus2'],row['nonpositive_depth_samples']]) and all(t['boundary_distance']<1e-8 and not t['strictly_interior'] for t in ties)
    row['connection_pass']=not missing and not unclassified
    row['pass']=row['bank_pass'] and row['connection_pass']
    rows.append(row)
assert len(rows)==13
summary={'lakes':len(rows),'passing_lakes':sum(x['pass'] for x in rows),'passing_bank_checks':sum(x['bank_pass'] for x in rows),'passing_connection_checks':sum(x['connection_pass'] for x in rows),'external_dry_bank_samples':sum(x['external_dry_bank_samples'] for x in rows),'internal_dry_boundary_bank_samples':sum(x['internal_dry_boundary_bank_samples'] for x in rows),'source_samples':sum(x['source_samples'] for x in rows),'source_wet_samples':sum(x['source_wet_samples'] for x in rows),'dry_boundary_samples':sum(x['dry_boundary_samples'] for x in rows),'missing_expected_connections':sum(len(x['missing_expected_river_ids']) for x in rows),'observed_river_lake_links':sum(len(x['observed_river_ids']) for x in rows),'external_wet_contact_samples':sum(x['external_wet_samples'] for x in rows),'overall_pass':all(x['pass'] for x in rows)}
report={'round':args.round,'profile':'baseline' if args.baseline else 'corrected','source_sha256':sha,'height_raw_sha256':hashlib.sha256((args.rasters/'height.png').read_bytes()).hexdigest(),'water_raw_sha256':hashlib.sha256((args.rasters/'water.png').read_bytes()).hexdigest(),'method':'All four-block pixel centres inside each native lake;cardinal four-neighbor ring around matching lake water. Separate exact-boundary dry samples. Compare dry-bank first-air with designed water first-air+2;all wet bed samples below water. Classify wet exits by actual river half-width(max(width/2,2.9));candidate links have a source endpoint within8blocks of lake.','limits':'Normal raster evidence only;not continuous bank,diagonal/final-noise,per-block fluid,chunk placement or in-game leak acceptance. Source-endpoint proximity is a finite designed-connection rule,not a canonical geographical claim.','summary':summary,'lakes':rows}
out.parent.mkdir(parents=True,exist_ok=True)
out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
fields=[k for k,v in rows[0].items() if not isinstance(v,(list,dict))]+['observed_river_ids','missing_expected_river_ids']
buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
for row in rows:
    rec={k:row[k] for k in fields}
    for k in ['observed_river_ids','missing_expected_river_ids']:rec[k]=';'.join(rec[k])
    writer.writerow(rec)
out.with_suffix('.csv').write_text(buf.getvalue().replace('\r\n','\n'),encoding='utf-8',newline='\n')
print(json.dumps(summary))
sys.exit(0 if summary['overall_pass'] else 1)
