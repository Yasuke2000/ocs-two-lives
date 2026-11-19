"""Preview of the planned forests and trade roads over Lerfing's terrain (a PNG for docs/previews; needs Pillow).

    python tools/lerfing/works_preview.py --world <import dir> [--out docs/previews/tempest-forest-road.png]

(no -I when Pillow lives in the user site-packages)

Three panels: the whole Dwarven Road with both forests (4 blocks per pixel), Tempest's ring and Treyni's wood
(2 blocks per pixel). Terrain from the imported world's exact columns: water blue, sand tan, rock grey, soil green
shaded by height, Lerfing's own trees dark green. Planned: giant crowns (Tensura ancient-forest templates) deep green
with a trunk dot, understory trees green dots, the road brown (stone stretch grey, lantern posts yellow), the kept
boxes red (settlements), magenta (placed builds/landmarks, keepouts), the clear box orange, lanes yellow.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lerfing.terrain import Terrain  # noqa: E402
from lerfing import forests, trade_roads  # noqa: E402
import anchor_refs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def colour(a):
    if a is None or a['ground'] is None:
        return (20, 20, 30)
    if a['water'] is not None:
        d = max(0, min(8, a['water'] - a['ground']))
        return (40, 90 - d * 5, 170 - d * 6)
    g = a['ground']
    s = max(0.0, min(1.0, (g - 60) / 90))
    if a['tree']:
        return (int(30 + 30 * s), int(80 + 30 * s), int(30 + 20 * s))
    if a['cls'] == 'sand':
        return (218, 205, 150)
    if a['cls'] == 'rock':
        v = int(120 + 90 * s)
        return (v, v, v - 8)
    return (int(110 + 90 * s), int(165 + 60 * s), int(90 + 60 * s))


def panel(t, x0, z0, x1, z1, scale, title, data):
    from PIL import Image, ImageDraw
    bpp = t.step if scale is None else scale  # blocks per pixel
    w = (x1 - x0) // bpp
    h = (z1 - z0) // bpp
    img = Image.new('RGB', (w, h + 18), (16, 16, 22))
    px = img.load()
    for j in range(h):
        for i in range(w):
            px[i, j + 18] = colour(t.at(x0 + i * bpp, z0 + j * bpp))
    d = ImageDraw.Draw(img)

    def P(x, z):
        return ((x - x0) / bpp, (z - z0) / bpp + 18)

    def rect(b, col, width=1):
        d.rectangle([P(b[0], b[1]), P(b[2] + 1, b[3] + 1)], outline=col, width=width)
    for k in anchor_refs.keepouts():
        rect((k['x0'], k['z0'], k['x1'], k['z1']), (230, 60, 230))
    for name, b in trade_roads.settlement_boxes().items():
        rect(b, (230, 50, 50), 2)
    for pid, (cfg, plan, geo) in data['forests'].items():
        centre, boxes, lanes, roads = geo
        for c in cfg.get('clear', []):
            ax, az = anchor_refs.point('preview', c['anchor'])
            rect((ax + c['x0'], az + c['z0'], ax + c['x1'], az + c['z1']), (240, 150, 40))
        for k in cfg.get('keep_clear', []):
            rect(k['offline'], (230, 60, 230))
        for seg, half in lanes:
            d.line([P(seg[0], seg[1]), P(seg[2], seg[3])], fill=(250, 220, 60), width=max(1, int(2 * half / bpp)))
        for r in (cfg['inner'], cfg['outer']):
            cx, cz = P(*centre)
            d.ellipse([cx - r / bpp, cz - r / bpp, cx + r / bpp, cz + r / bpp], outline=(255, 255, 255))
        for ti, x, z, ri in plan['giants']:
            tp = plan['templates'][plan['giant_keys'][ti]]
            rad = max(tp['size'][0], tp['size'][2]) / 2.2 / bpp
            cx, cz = P(x, z)
            d.ellipse([cx - rad, cz - rad, cx + rad, cz + rad], fill=(18, 70, 28), outline=(10, 40, 15))
            tr = max(1, tp['trunk_r'] / bpp)
            d.ellipse([cx - tr, cz - tr, cx + tr, cz + tr], fill=(110, 70, 30))
        for fi, x, z in plan['understory']:
            rr = max(1, forests.FEATURE_CROWN.get(plan['features'][fi], 3) / bpp)
            cx, cz = P(x, z)
            d.ellipse([cx - rr, cz - rr, cx + rr, cz + rr], fill=(45, 120, 45))
    for rid, (cfg, road) in data['roads'].items():
        cols = trade_roads.rasterize(road['points'], road['profile'], cfg['half'])
        stone = cfg.get('stone_from', [])
        for (x, z), (y, i, o) in cols.items():
            if not (x0 <= x < x1 and z0 <= z < z1):
                continue
            inb = any(b[0] <= x <= b[2] and b[1] <= z <= b[3] for b in stone)
            bridge = any(b[0] <= i <= b[1] for b in road['bridges'])
            col = (150, 90, 50) if bridge else (150, 150, 150) if inb else (120, 82, 45)
            cx, cz = P(x, z)
            d.rectangle([cx, cz, cx + max(0, 1 / bpp), cz + max(0, 1 / bpp)], fill=col)
        for x, z, _ in trade_roads.lanterns(road, cfg):
            cx, cz = P(x, z)
            d.ellipse([cx - 1.5, cz - 1.5, cx + 1.5, cz + 1.5], fill=(255, 220, 60))
    for aid in ('tempest', 'arrival', 'dwargon', 'treyni_shrine', 'dwarf_village', 'spirit_gate'):
        x, z = anchor_refs.point('preview', aid)
        if x0 <= x < x1 and z0 <= z < z1:
            cx, cz = P(x, z)
            d.text((cx + 3, cz - 5), aid, fill=(255, 255, 255))
    d.text((4, 3), title, fill=(255, 255, 255))
    return img


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', default=str(ROOT / 'docs' / 'previews' / 'tempest-forest-road.png'))
    args = ap.parse_args(argv)
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit('works_preview.py needs Pillow (pip install pillow)')
    pcfg = forests.load_config()
    data = {'forests': {}, 'roads': {}}
    for pid in pcfg:
        plan = forests.stored(pid)
        if plan:
            data['forests'][pid] = (pcfg[pid], plan, forests.patch_geometry(pid, pcfg[pid]))
    rcfg = trade_roads.load_config()
    for rid in rcfg:
        road = trade_roads.stored(rid)
        if road:
            data['roads'][rid] = (rcfg[rid], road)
    over = Terrain.from_world(args.world, 1400, -720, 2240, 1800, 4)
    p1 = panel(over, 1400, -720, 2240, 1800, 4, 'Dwarven Road + forests (4 blocks/px)', data)
    tc = anchor_refs.point('preview', 'tempest')
    tz = Terrain.from_world(args.world, tc[0] - 290, tc[1] - 290, tc[0] + 290, tc[1] + 290, 2)
    p2 = panel(tz, tc[0] - 280, tc[1] - 280, tc[0] + 280, tc[1] + 280, 2, 'Tempest ring 60-250 (2 blocks/px)', data)
    sc = anchor_refs.point('preview', 'treyni_shrine')
    sz = Terrain.from_world(args.world, sc[0] - 230, sc[1] - 230, sc[0] + 230, sc[1] + 230, 2)
    p3 = panel(sz, sc[0] - 220, sc[1] - 220, sc[0] + 220, sc[1] + 220, 2, "Treyni's wood 25-180 (2 blocks/px)", data)
    W = p1.width + p2.width + 8
    H = max(p1.height, p2.height + p3.height + 8)
    img = Image.new('RGB', (W, H), (16, 16, 22))
    img.paste(p1, (0, 0))
    img.paste(p2, (p1.width + 8, 0))
    img.paste(p3, (p1.width + 8, p2.height + 8))
    img = img.resize((W * 2, H * 2), Image.NEAREST)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out, optimize=True)
    print(f'wrote {args.out} ({img.width} x {img.height})')


if __name__ == '__main__':
    main()
