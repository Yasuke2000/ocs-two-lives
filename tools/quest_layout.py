#!/usr/bin/env python3
"""Quest book layout: the layered (Sugiyama-style) placement gen_quests.py uses, the line checks, and PNG previews.

Every chapter is laid out the same way (design/quests.md, "Layout"):
  * layers run left to right: a quest's column is its dependency depth inside the chapter (a quest with other
    successors is pulled right, next to them, so lines stay short);
  * the main progression (the longest chain of required, path-less quests) is one straight row, row 0;
  * the light lane sits above it, the dark lane, the other required side branches and then the optional quests
    below it; quests with no dependency line in the chapter (dailies, boards) are a grid under everything;
  * inside a layer the order minimises crossings (barycenter sweeps), rows follow the neighbours (isotonic fit);
  * a line that spans more than LONG_SPAN layers, or would pass through another quest's icon, is hidden
    (FTB `dep_line_visibility`), and the quest text says what it needs instead (gen_quests.py).
A quest with `pin = [x, y]` in the TOML keeps that spot; nothing else is placed by hand.

The geometry (centre of each quest, `size` wide; a line runs centre to centre, as FTB Quests draws it) is checked by
`problems()`: no two icons overlap, no visible line passes through an icon. quest_graph.py --check runs it.

Usage: quest_layout.py                          crossings, overlaps and lines through icons per chapter
       quest_layout.py --png <dir> [chapter...] render previews (needs Pillow; dev only)
       quest_layout.py --from <quests dir> ...  read another generated book (pack/config/ftbquests/quests layout)
Stdlib only, except --png.
"""
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "pack" / "config" / "ftbquests" / "quests"

COL = 2.0        # grid units between layers (x)
ROW = 1.5        # grid units between rows (y)
LONG_SPAN = 2    # a line across more layers than this is hidden
SWEEPS = 12      # barycenter sweeps (left to right and back) inside a branch
EPS = 1e-6
TRIES = 24       # branch orders tried per chapter (seeded, so the layout is the same on every run)
CLEAR = 0.15     # extra room a line keeps from an icon while placing (the check itself uses the icon's own radius)


# ---- the layout --------------------------------------------------------------------------------------------------

def _topo(keys: list, preds: dict) -> list:
    """Kahn's order, ties broken by file order (deterministic)."""
    idx = {k: i for i, k in enumerate(keys)}
    indeg = {k: len(preds[k]) for k in keys}
    succs = {k: [] for k in keys}
    for k in keys:
        for p in preds[k]:
            succs[p].append(k)
    ready = sorted((k for k in keys if indeg[k] == 0), key=idx.get)
    out = []
    while ready:
        k = ready.pop(0)
        out.append(k)
        for s in succs[k]:
            indeg[s] -= 1
            if indeg[s] == 0:
                ready.append(s)
                ready.sort(key=idx.get)
    return out


def _isotonic(desired: list, lo: float = 1.0) -> list:
    """Integer rows r_0 < r_1 < ... with r_0 >= lo, as close (least squares) to `desired` as that order allows."""
    t = [d - i for i, d in enumerate(desired)]
    blocks = []  # [sum, count]: pool-adjacent-violators
    for v in t:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s, c = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
    z = []
    for s, c in blocks:
        z += [max(lo, s / c)] * c
    return [math.floor(v + 0.5) + i for i, v in enumerate(z)]


def _seg_cross_count(new: list, old: list, geo: dict) -> int:
    n = 0
    for i, (a, b) in enumerate(new):
        (ax, ay, _), (bx, by, _) = geo[a], geo[b]
        x0, x1, y0, y1 = min(ax, bx), max(ax, bx), min(ay, by), max(ay, by)
        for c, d in old + new[i + 1:]:
            (cx, cy, _), (dx, dy, _) = geo[c], geo[d]
            if max(cx, dx) <= x0 or min(cx, dx) >= x1 or max(cy, dy) <= y0 or min(cy, dy) >= y1:
                continue
            if a in (c, d) or b in (c, d):
                continue
            if _cross((ax, ay), (bx, by), (cx, cy), (dx, dy)):
                n += 1
    return n


_MEMO: dict = {}


def layout(quests: list) -> tuple:
    """quests: [{key, deps (keys in this chapter), size, optional, path, pin ((x, y) or None)}] in file order.
    Returns ({key: (x, y)}, hidden) with hidden = {(dep, key)}: dependency lines in this chapter to hide.
    The search takes a second for the biggest chapter, so a process that renders the book twice reuses it."""
    memo = repr(quests)
    if memo not in _MEMO:
        _MEMO[memo] = _layout(quests)
    pos, hidden = _MEMO[memo]
    return dict(pos), set(hidden)


def _layout(quests: list) -> tuple:
    keys = [q["key"] for q in quests]
    info = {q["key"]: q for q in quests}
    order_ix = {k: i for i, k in enumerate(keys)}
    size = {k: float(info[k].get("size") or 1.0) for k in keys}
    pinned = [k for k in keys if info[k].get("pin") is not None]
    free = [k for k in keys if k not in pinned]
    preds = {k: [d for d in info[k]["deps"] if d in info and d not in pinned] for k in free}
    succs = {k: [] for k in free}
    for k in free:
        for p in preds[k]:
            succs[p].append(k)
    connected = [k for k in free if preds[k] or succs[k]]
    isolated = [k for k in free if not (preds[k] or succs[k])]

    # 1. layers: longest path from the roots; a root (a quest with no dependency here) then moves right, next to the
    #    nearest quest that needs it, so its line stays short
    topo = _topo(connected, {k: preds[k] for k in connected})
    layer = {}
    for k in topo:
        layer[k] = max((layer[p] + 1 for p in preds[k]), default=0)
    for k in reversed(topo):
        if succs[k] and not preds[k]:
            layer[k] = max(layer[k], min(layer[s] for s in succs[k]) - 1)

    # 2. the main line: a chain of required, path-less quests, each an ancestor of the next
    def eligible(k):
        return not info[k].get("optional") and not info[k].get("path")

    anc = {}
    for k in topo:
        a = set()
        for p in preds[k]:
            a |= anc[p] | {p}
        anc[k] = a
    best, back = {}, {}
    for k in topo:
        if not eligible(k):
            continue
        cands = [u for u in anc[k] if u in best]
        if cands:
            # the longest chain, then a direct dependency, then the closer layer, then file order
            u = max(cands, key=lambda u: (best[u], u in preds[k], layer[u], -order_ix[u]))
            best[k], back[k] = best[u] + 1, u
        else:
            best[k], back[k] = 1, None
    main = []
    if best:
        # it ends at the chapter's goal: the biggest quest nothing here depends on, else the longest chain wins
        sinks = [k for k in best if not succs[k]] or list(best)
        end = max(sinks, key=lambda k: (size[k], best[k], -layer[k], -order_ix[k]))
        while end is not None:
            main.append(end)
            end = back[end]
        main.reverse()
    main_set = set(main)

    # 3. side branches: connected groups of the other quests that share a lane (light, dark or none)
    def lane(k):
        return info[k].get("path") or ""

    comp_of, comps = {}, []
    for k in connected:
        if k in main_set or k in comp_of:
            continue
        comp_of[k] = len(comps)
        stack, group = [k], []
        while stack:
            v = stack.pop()
            group.append(v)
            for w in preds[v] + succs[v]:
                if w not in main_set and w not in comp_of and lane(w) == lane(v):
                    comp_of[w] = comp_of[k]
                    stack.append(w)
        comps.append(sorted(group, key=order_ix.get))

    def block(group: list) -> dict:
        """Rows inside a branch, 0 = next to the main line: barycenter order per layer (optional quests last),
        then rows that follow the neighbours (the main line counts as row -1), a few sweeps both ways."""
        gset = set(group)
        by_layer: dict = {}
        for v in group:
            by_layer.setdefault(layer[v], []).append(v)
        rel = {}
        for vs in by_layer.values():
            vs.sort(key=lambda v: (bool(info[v].get("optional")), order_ix[v]))
            for i, v in enumerate(vs):
                rel[v] = i

        def want(v):
            rs = [rel[w] if w in gset else -1.0 for w in preds[v] + succs[v]
                  if (w in gset or w in main_set) and abs(layer[w] - layer[v]) <= LONG_SPAN]
            return sum(rs) / len(rs) if rs else rel[v]

        for sweep in range(SWEEPS):
            for li in sorted(by_layer, reverse=sweep % 2 == 1):
                vs = by_layer[li]
                w = {v: want(v) for v in vs}
                vs.sort(key=lambda v: (bool(info[v].get("optional")), w[v], rel[v], order_ix[v]))
                for v, r in zip(vs, _isotonic([w[v] for v in vs], lo=0.0)):
                    rel[v] = r
        low = min(rel.values())
        return {v: r - low for v, r in rel.items()}

    # 4. place: main line on row 0, then each branch at the offset with no line through an icon, the fewest crossings
    #    and the shortest lines (dark lane, required branches, optional ones below; the light lane above)
    pos = {k: (float(info[k]["pin"][0]), float(info[k]["pin"][1])) for k in pinned}
    for k in main:
        pos[k] = (layer[k] * COL, 0.0)
    edges = [(d, k) for k in keys for d in info[k]["deps"] if d in info]

    def kind(group):
        if lane(group[0]) == "dark":
            return 0
        return 1 if any(not info[v].get("optional") for v in group) else 2

    has_light = any(lane(k) == "light" for k in connected)

    def sides(group):
        """-1 above the main line, 1 below: the light lane above, the dark lane and optional branches below; other
        required branches below as well in a chapter with a light lane, else on whichever side reads better."""
        if lane(group[0]) == "light":
            return (-1,)
        if kind(group) == 1 and not has_light:
            return (1, -1)
        return (1,)

    rels = [block(c) for c in comps]
    fixed = dict(pos)

    def arrange(order: list) -> tuple:
        """Place the branches in this order; returns (positions, layers, score: lower reads better)."""
        at, lay = dict(fixed), dict(layer)

        def drawn_(a, b):
            return not (a in lay and b in lay and lay[b] - lay[a] > LONG_SPAN)

        for ci in order:
            group, rel = comps[ci], rels[ci]
            gset = set(group)
            geo = {k: (x, y, size[k]) for k, (x, y) in at.items()}
            old = [(a, b) for a, b in edges if a in at and b in at and drawn_(a, b)]
            # a branch that leads nowhere else may also start one layer further right (a flatter first line)
            shifts = (0, 1) if not any(s not in gset for v in group for s in succs[v]) else (0,)
            touch = [(a, b) for a, b in edges if (a in gset or b in gset) and (a in at or a in gset) and (b in at or b in gset)]
            best, best_cost = None, None
            for dx in shifts:
                for sign in sides(group):
                    reach = max([abs(y) / ROW for _, y in at.values() if y * sign > 0] or [0])
                    for t in range(1, int(reach) + max(rel.values()) + 3):
                        if best_cost is not None and best_cost[0] == 0 and t * 0.5 > best_cost[1]:
                            break  # every later offset costs more than the best already found
                        trial = {v: ((layer[v] + dx) * COL, sign * (t + rel[v]) * ROW, size[v]) for v in group}
                        if any(abs(x - px) < (s + ps) / 2 - EPS and abs(y - py) < (s + ps) / 2 - EPS
                               for x, y, s in trial.values() for px, py, ps in geo.values()):
                            continue
                        g = dict(geo)
                        g.update(trial)
                        for v in group:
                            lay[v] = layer[v] + dx
                        new = [(a, b) for a, b in touch if drawn_(a, b)]
                        thr = sum(len(through(g, a, b, CLEAR)) for a, b in new)
                        thr += sum(1 for a, b in old for v, (x, y, s) in trial.items()
                                   if _seg_dist(x, y, *g[a][:2], *g[b][:2]) < s / 2 + CLEAR)
                        vert = sum(abs(g[a][1] - g[b][1]) for a, b in new) / ROW
                        lost = len(touch) - len(new)
                        # a block above the main line or shifted right costs a little more, so a tie keeps it below
                        cost = (thr + lost, _seg_cross_count(new, old, g) * 4 + vert + t * 0.5
                                + (0.75 if sign < 0 else 0) + dx * 1.5)
                        if best_cost is None or cost < best_cost:
                            best, best_cost = (dx, sign, t), cost
            dx, sign, t = best
            for v in group:
                lay[v] = layer[v] + dx
                at[v] = (lay[v] * COL, sign * (t + rel[v]) * ROW)
        geo = {k: (x, y, size[k]) for k, (x, y) in at.items()}
        vis = [(a, b) for a, b in edges if a in at and b in at and drawn_(a, b) and not through(geo, a, b)]
        lost = sum(1 for a, b in edges if a in at and b in at) - len(vis)
        ys = [y / ROW for _, y in at.values()]
        steep = sum(max(0.0, abs(geo[a][1] - geo[b][1]) / ROW - 1) ** 2 for a, b in vis)
        return at, lay, (lost * 6 + crossings(geo, vis) * 3 + (max(ys) - min(ys) if ys else 0) * 0.4 + steep * 0.5)

    def rank(i):
        return (lane(comps[i][0]) == "light", kind(comps[i]))

    base = sorted(range(len(comps)), key=lambda i: rank(i) + (min(layer[v] for v in comps[i]), order_ix[comps[i][0]]))
    pos, layer, score = arrange(base)
    rng = random.Random(len(keys))
    for _ in range(TRIES if len(comps) > 2 else 0):
        # shuffle inside each rank only: required branches still claim the rows before optional ones
        order = sorted(base, key=lambda i: rank(i) + (rng.random(),))
        cand = arrange(order)
        if cand[2] < score - EPS:
            pos, layer, score = cand

    def drawn(a, b) -> bool:
        return not (a in layer and b in layer and layer[b] - layer[a] > LONG_SPAN)

    # 5. quests with no line in this chapter: a grid under the rest, in file order
    if isolated:
        depth = max(layer.values(), default=-1) + 1
        top = (max(y for _, y in pos.values()) / ROW + 2) if pos else 0
        width = max(3, depth) if connected else max(3, math.ceil(math.sqrt(len(isolated))))
        for i, k in enumerate(isolated):
            pos[k] = ((i % width) * COL, (top + i // width) * ROW)

    # 6. lines to hide: long spans, and any line that still passes through another icon
    geo = {k: (pos[k][0], pos[k][1], size[k]) for k in keys}
    hidden = {(a, b) for a, b in edges if not drawn(a, b) or through(geo, a, b)}
    return {k: (round(x, 3), round(y, 3)) for k, (x, y) in pos.items()}, hidden


# ---- geometry checks ---------------------------------------------------------------------------------------------

def _seg_dist(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    ll = dx * dx + dy * dy
    t = 0.0 if ll == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ll))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def through(geo: dict, a, b, clear: float = 0.0) -> list:
    """Quests (other than a and b) whose icon the line a-b passes through: closer to it than half their size
    (plus `clear`)."""
    ax, ay, _ = geo[a]
    bx, by, _ = geo[b]
    x0, x1, y0, y1 = min(ax, bx), max(ax, bx), min(ay, by), max(ay, by)
    out = []
    for c, (x, y, s) in geo.items():
        r = s / 2 + clear - EPS
        if x + r <= x0 or x - r >= x1 or y + r <= y0 or y - r >= y1 or c == a or c == b:
            continue
        if _seg_dist(x, y, ax, ay, bx, by) < r:
            out.append(c)
    return out


def overlaps(geo: dict) -> list:
    out = []
    ks = list(geo)
    for i, a in enumerate(ks):
        ax, ay, sa = geo[a]
        for b in ks[i + 1:]:
            bx, by, sb = geo[b]
            m = (sa + sb) / 2 - EPS
            if abs(ax - bx) < m and abs(ay - by) < m:
                out.append((a, b))
    return out


def _cross(p, q, r, s) -> bool:
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < EPS else (1 if v > 0 else -1)

    o1, o2, o3, o4 = orient(p, q, r), orient(p, q, s), orient(r, s, p), orient(r, s, q)
    return o1 * o2 < 0 and o3 * o4 < 0


def crossings(geo: dict, edges: list) -> int:
    n = 0
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1:]:
            if {a, b} & {c, d}:
                continue
            if _cross(geo[a][:2], geo[b][:2], geo[c][:2], geo[d][:2]):
                n += 1
    return n


def measure(geo: dict, edges: list) -> dict:
    """edges: visible (dep, quest) lines inside the chapter."""
    thr = [(a, b, c) for a, b in edges for c in through(geo, a, b)]
    return {"quests": len(geo), "lines": len(edges), "crossings": crossings(geo, edges),
            "overlaps": overlaps(geo), "through": thr}


# ---- reading a generated book ------------------------------------------------------------------------------------

class _Snbt:
    """Just enough SNBT for the files gen_quests.py writes (and FTB itself writes)."""
    TOKEN = re.compile(r'\s*(?:(\{)|(\})|(\[)|(\])|(:)|(,)|("(?:[^"\\]|\\.)*")|([^\s{}\[\]:,"]+))')

    def __init__(self, text: str):
        self.toks = []
        for m in self.TOKEN.finditer(text):
            g = m.lastindex
            if g is not None:
                self.toks.append((g, m.group(g)))
        self.i = 0

    def value(self):
        g, t = self.toks[self.i]
        self.i += 1
        if g == 1:
            out = {}
            while self.toks[self.i][0] != 2:
                if self.toks[self.i][0] == 6:
                    self.i += 1
                    continue
                key = self.toks[self.i][1]
                key = key[1:-1] if key.startswith('"') else key
                self.i += 2
                out[key] = self.value()
            self.i += 1
            return out
        if g == 3:
            out = []
            if self.toks[self.i][1] in ("I;", "I", "B;", "L;"):
                self.i += 1
            while self.toks[self.i][0] != 4:
                if self.toks[self.i][0] == 6:
                    self.i += 1
                    continue
                out.append(self.value())
            self.i += 1
            return out
        if g == 7:
            return t[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        if t in ("true", "false"):
            return t == "true"
        m = re.fullmatch(r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)([dDfFbBsSlL]?)", t)
        if m:
            return float(m.group(1)) if ("." in m.group(1) or m.group(2) in "dDfF" and m.group(2)) else int(m.group(1))
        return t


def parse_snbt(text: str):
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    return _Snbt(text).value()


def read_book(book: Path = BOOK) -> list:
    """[(chapter key, title, geo {id: (x, y, size)}, titles {id: title}, visible [(dep, quest)], hidden count)]."""
    lang = parse_snbt((book / "lang" / "en_us.snbt").read_text(encoding="utf-8"))
    out = []
    for f in sorted((book / "chapters").glob("*.snbt")):
        ch = parse_snbt(f.read_text(encoding="utf-8"))
        out.append(chapter_geometry(ch, lang))
    return out


def chapter_geometry(ch: dict, lang: dict) -> tuple:
    qs = ch.get("quests", [])
    geo = {q["id"]: (float(q.get("x", 0.0)), float(q.get("y", 0.0)), float(q.get("size", 1.0))) for q in qs}
    titles = {q["id"]: lang.get(f"quest.{q['id']}.title", q["id"]) for q in qs}
    visible, hidden = [], 0
    for q in qs:
        vis = q.get("dep_line_visibility", {})
        hide_all = q.get("hide_dependency_lines") is True or ch.get("default_hide_dependency_lines") is True
        for d in q.get("dependencies", []):
            if d not in geo:
                continue  # another chapter: FTB Quests draws no line for it
            if hide_all or vis.get(d) is False:
                hidden += 1
            else:
                visible.append((d, q["id"]))
    title = lang.get(f"chapter.{ch['id']}.title", ch.get("filename", "?"))
    return ch.get("filename", "?"), title, geo, titles, visible, hidden


def problems(chapters: list) -> list:
    """Lines for every overlap and every visible line through an icon (chapters as read_book / chapter_geometry)."""
    out = []
    for key, _title, geo, titles, visible, _h in chapters:
        m = measure(geo, visible)
        for a, b in m["overlaps"]:
            out.append(f"{key}: '{titles[a]}' and '{titles[b]}' overlap")
        for a, b, c in m["through"]:
            out.append(f"{key}: the line '{titles[a]}' -> '{titles[b]}' passes through '{titles[c]}'")
    return out


# ---- previews ----------------------------------------------------------------------------------------------------

def render_png(chapter: tuple, path: Path, note: str = "") -> None:
    from PIL import Image, ImageDraw, ImageFont  # dev only

    key, title, geo, titles, visible, hidden = chapter
    m = measure(geo, visible)
    bad = {(a, b) for a, b, _ in m["through"]}
    bad_nodes = {x for pair in m["overlaps"] for x in pair}
    scale, pad, head = 46, 70, 64
    xs = [x for x, _, _ in geo.values()] or [0]
    ys = [y for _, y, _ in geo.values()] or [0]
    minx, maxx, miny, maxy = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    w = int((maxx - minx) * scale) + 2 * pad
    h = int((maxy - miny) * scale) + 2 * pad + head
    img = Image.new("RGB", (max(w, 640), h), (24, 26, 31))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
        big = ImageFont.truetype("arialbd.ttf", 17)
    except OSError:
        font = big = ImageFont.load_default()

    def pt(x, y):
        return (pad + (x - minx) * scale, head + pad + (y - miny) * scale)

    for a, b in visible:
        col = (232, 70, 70) if (a, b) in bad else (140, 150, 168)
        d.line([pt(*geo[a][:2]), pt(*geo[b][:2])], fill=col, width=3 if (a, b) in bad else 2)
    for q, (x, y, s) in geo.items():
        cx, cy = pt(x, y)
        r = s * scale / 2
        outline = (232, 70, 70) if q in bad_nodes else (29, 113, 184)
        d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=6, fill=(46, 52, 64), outline=outline, width=3)
        label = titles[q]
        lines, cur = [], ""
        for word in label.split():
            if cur and d.textlength(cur + " " + word, font=font) > COL * scale - 6:
                lines.append(cur)
                cur = word
            else:
                cur = (cur + " " + word).strip()
        lines.append(cur)
        for i, line in enumerate(lines[:3]):
            tw = d.textlength(line, font=font)
            d.text((cx - tw / 2, cy + r + 2 + i * 12), line, font=font, fill=(225, 228, 235))
    d.text((pad / 2, 14), f"{title} ({key}){' - ' + note if note else ''}", font=big, fill=(253, 195, 0))
    stats = (f"{m['quests']} quests, {m['lines']} lines shown, {hidden} hidden, {m['crossings']} crossings, "
             f"{len(m['overlaps'])} overlaps, {len(m['through'])} lines through an icon")
    d.text((pad / 2, 38), stats, font=font, fill=(200, 205, 215))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def main() -> None:
    args = sys.argv[1:]
    book = BOOK
    if "--from" in args:
        i = args.index("--from")
        book = Path(args[i + 1])
        del args[i:i + 2]
    chapters = read_book(book)
    if args and args[0] == "--png":
        out = Path(args[1])
        rest = args[2:]
        suffix = ""
        if "--suffix" in rest:
            i = rest.index("--suffix")
            suffix = rest[i + 1]
            del rest[i:i + 2]
        for ch in chapters:
            if not rest or ch[0] in rest:
                render_png(ch, out / f"{ch[0]}{suffix}.png", note=suffix.strip("-"))
        return
    tot = [0, 0, 0, 0]
    print(f"{'chapter':24} {'quests':>6} {'lines':>5} {'hidden':>6} {'cross':>5} {'overlap':>7} {'through':>7}")
    for key, _t, geo, _ti, visible, hidden in chapters:
        m = measure(geo, visible)
        row = [m["crossings"], len(m["overlaps"]), len(m["through"]), hidden]
        tot = [a + b for a, b in zip(tot, row)]
        print(f"{key:24} {m['quests']:6} {m['lines']:5} {hidden:6} {row[0]:5} {row[1]:7} {row[2]:7}")
    print(f"{'total':24} {'':6} {'':5} {tot[3]:6} {tot[0]:5} {tot[1]:7} {tot[2]:7}")


if __name__ == "__main__":
    main()
