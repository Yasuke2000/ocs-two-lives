"""Reader for world/map.svg, the layered block-coordinate map of the own world (stdlib only).

design/architecture/own-world.md §2.2: viewBox -8000 -6000 16000 12000, 1 unit = 1 block, +x east, +y south (= +z),
Tempest at 0, 0; named top-level groups `<g id="coast|lakes|rivers|mountains|hills|forests|biomes|regions|roads|sites|
labels">`, `data-*` attributes on the elements (or inherited from a nested group).

This module is the shared parser of the world tools: tools/world/svg2rasters.py uses it, and tools/world/map_check.py
(WP W-check) carries a parser with the same shapes (Shape, parse_points, parse_path, parse_transform, parse_svg(text,
report)) so the two can be unified here. It reads the geometry and attributes only; the rules (closed polygons,
attribute ranges, canon distances) are map_check's job, so this reader is lenient: it records what it cannot read in
the report and carries on.
"""
import math
import re
from xml.etree import ElementTree as ET

VIEWBOX = (-8000.0, -6000.0, 16000.0, 12000.0)
LAYERS = ("coast", "lakes", "rivers", "mountains", "hills", "forests", "biomes", "regions", "roads", "sites", "labels")
CURVE_STEPS = {"C": 16, "Q": 12}
SKIP_TAGS = {"title", "desc", "metadata", "style", "defs", "tspan", "text"}


class ParseError(Exception):
    pass


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, rule, msg):
        self.errors.append({"rule": rule, "message": msg})

    def warn(self, rule, msg):
        self.warnings.append({"rule": rule, "message": msg})

    @property
    def ok(self):
        return not self.errors


class Shape:
    """One geometric element of a layer: kind polygon | polyline | circle | rect, points in blocks."""

    def __init__(self, layer, kind, pts, attrs, label, closed=True, cx=None, cy=None, r=None):
        self.layer = layer
        self.kind = kind
        self.pts = pts
        self.attrs = attrs
        self.label = label
        self.closed = closed
        self.cx, self.cy, self.r = cx, cy, r

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def num(self, key, default=None):
        v = self.attrs.get(key)
        if v is None or str(v).strip() == "":
            return default
        try:
            f = float(v)
        except ValueError:
            return default
        return f if math.isfinite(f) else default

    @property
    def classes(self):
        return self.attrs.get("class", "").split()

    def __repr__(self):
        return "Shape(%s %s %s)" % (self.layer, self.kind, self.label)


NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(r"[MmLlHhVvZzCcQqSsTtAa]|" + NUM)
TRANSFORM = re.compile(r"\s*(\w+)\s*\(([^)]*)\)\s*,?")


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def fnum(s, what):
    try:
        v = float(s)
    except (TypeError, ValueError):
        raise ParseError("%s is not a number: %r" % (what, s))
    if not math.isfinite(v):
        raise ParseError("%s is not finite" % what)
    return v


def compose(a, b):
    """Transform a applied after b; a transform is (sx, sy, tx, ty): p' = (sx*x + tx, sy*y + ty)."""
    return (a[0] * b[0], a[1] * b[1], a[0] * b[2] + a[2], a[1] * b[3] + a[3])


def apply(t, p):
    return (t[0] * p[0] + t[2], t[1] * p[1] + t[3])


def parse_transform(s):
    """translate and scale only (the map spec forbids transforms; map_check reports them, this reader applies them)."""
    t = (1.0, 1.0, 0.0, 0.0)
    pos = 0
    s = s or ""
    while pos < len(s):
        m = TRANSFORM.match(s, pos)
        if not m:
            if s[pos:].strip():
                raise ParseError("unreadable transform %r" % s)
            break
        pos = m.end()
        vals = [fnum(v, "transform value") for v in re.split(r"[\s,]+", m.group(2).strip()) if v]
        if m.group(1) == "translate" and len(vals) in (1, 2):
            f = (1.0, 1.0, vals[0], vals[1] if len(vals) == 2 else 0.0)
        elif m.group(1) == "scale" and len(vals) in (1, 2):
            f = (vals[0], vals[1] if len(vals) == 2 else vals[0], 0.0, 0.0)
        else:
            raise ParseError("unsupported transform %s(...): only translate and scale" % m.group(1))
        t = compose(t, f)
    return t


def parse_points(s):
    nums = [fnum(v, "points value") for v in re.findall(NUM, s or "")]
    if len(nums) % 2:
        raise ParseError("points has an odd number of values")
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]


def parse_path(d):
    """List of (points, closed) subpaths, curves flattened. M L H V Z C Q, absolute and relative."""
    toks = TOKEN.findall(d or "")
    subs, cur = [], []
    closed = False
    i = 0
    cmd = None
    x = y = sx = sy = 0.0

    def need(n):
        nonlocal i
        if i + n > len(toks) or any(t.isalpha() for t in toks[i:i + n]):
            raise ParseError("path command %s needs %d numbers" % (cmd, n))
        vals = [float(t) for t in toks[i:i + n]]
        i += n
        return vals

    def flush():
        nonlocal cur, closed
        if cur:
            subs.append((cur, closed))
        cur, closed = [], False

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                if cur:
                    closed = True
                    x, y = sx, sy
                    flush()
                continue
        elif cmd is None:
            raise ParseError("path data must start with a command")
        elif cmd in "Zz":
            raise ParseError("numbers after Z")
        rel = cmd.islower()
        c = cmd.upper()
        if c in "SAT":
            raise ParseError("unsupported path command %s (use M L H V C Q Z)" % cmd)
        if c == "M":
            a, b = need(2)
            if rel:
                a, b = x + a, y + b
            flush()
            x, y, sx, sy = a, b, a, b
            cur = [(x, y)]
            cmd = "l" if rel else "L"
        elif c == "L":
            a, b = need(2)
            cur = cur or [(x, y)]
            x, y = (x + a, y + b) if rel else (a, b)
            cur.append((x, y))
        elif c == "H":
            (a,) = need(1)
            cur = cur or [(x, y)]
            x = x + a if rel else a
            cur.append((x, y))
        elif c == "V":
            (b,) = need(1)
            cur = cur or [(x, y)]
            y = y + b if rel else b
            cur.append((x, y))
        elif c in "CQ":
            n = 6 if c == "C" else 4
            v = need(n)
            if rel:
                v = [v[k] + (x if k % 2 == 0 else y) for k in range(n)]
            cur = cur or [(x, y)]
            ctrl = [(x, y)] + [(v[k], v[k + 1]) for k in range(0, n, 2)]
            steps = CURVE_STEPS[c]
            for s in range(1, steps + 1):
                u = s / steps
                if c == "C":
                    p0, p1, p2, p3 = ctrl
                    w = ((1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u ** 3)
                    cur.append((sum(w[k] * ctrl[k][0] for k in range(4)), sum(w[k] * ctrl[k][1] for k in range(4))))
                else:
                    w = ((1 - u) ** 2, 2 * (1 - u) * u, u * u)
                    cur.append((sum(w[k] * ctrl[k][0] for k in range(3)), sum(w[k] * ctrl[k][1] for k in range(3))))
            x, y = ctrl[-1]
    flush()
    return subs


def clean_ring(pts):
    """Drop repeated points and the closing duplicate of a polygon."""
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > 1e-9:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= 1e-9:
        out.pop()
    return out


def circle_pts(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def element_label(el, layer, index):
    ident = el.get("id") or el.get("data-id") or el.get("data-letter") or el.get("data-name")
    return "%s <%s> #%s%s" % (layer, local(el.tag), index, " (%s)" % ident if ident else "")


def shapes_of(el, layer, tf, inherited, index):
    tag = local(el.tag)
    tf = compose(tf, parse_transform(el.get("transform")))
    attrs = dict(inherited)
    attrs.update({k: v for k, v in el.attrib.items() if k.startswith("data-") or k in ("class", "id")})
    label = element_label(el, layer, index)
    if tag == "polygon":
        return [Shape(layer, "polygon", clean_ring([apply(tf, p) for p in parse_points(el.get("points"))]), attrs, label)]
    if tag == "polyline":
        return [Shape(layer, "polyline", [apply(tf, p) for p in parse_points(el.get("points"))], attrs, label, False)]
    if tag == "line":
        pts = [(fnum(el.get("x1", "0"), "x1"), fnum(el.get("y1", "0"), "y1")),
               (fnum(el.get("x2", "0"), "x2"), fnum(el.get("y2", "0"), "y2"))]
        return [Shape(layer, "polyline", [apply(tf, p) for p in pts], attrs, label, False)]
    if tag == "path":
        out = []
        for k, (pts, closed) in enumerate(parse_path(el.get("d"))):
            lab = label if k == 0 else "%s subpath %d" % (label, k + 1)
            pts = [apply(tf, p) for p in pts]
            out.append(Shape(layer, "polygon" if closed else "polyline", clean_ring(pts) if closed else pts, attrs, lab,
                             closed))
        return out
    if tag == "rect":
        x, y = fnum(el.get("x", "0"), "x"), fnum(el.get("y", "0"), "y")
        w, h = fnum(el.get("width"), "width"), fnum(el.get("height"), "height")
        sh = Shape(layer, "rect", [apply(tf, p) for p in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))], attrs, label)
        sh.cx, sh.cy = apply(tf, (x + w / 2, y + h / 2))
        sh.r = max(abs(w * tf[0]), abs(h * tf[1])) / 2
        return [sh]
    if tag == "circle":
        cx, cy, r = fnum(el.get("cx", "0"), "cx"), fnum(el.get("cy", "0"), "cy"), fnum(el.get("r"), "r")
        c = apply(tf, (cx, cy))
        rr = abs(r) * (abs(tf[0]) + abs(tf[1])) / 2
        return [Shape(layer, "circle", circle_pts(c[0], c[1], rr), attrs, label, True, c[0], c[1], rr)]
    raise ParseError("unsupported element <%s> (use polygon, polyline, path, circle, rect)" % tag)


def walk_layer(el, layer, tf, inherited, report, shapes, counter):
    for child in el:
        tag = local(child.tag)
        if not isinstance(child.tag, str) or tag in SKIP_TAGS:
            continue
        try:
            if tag == "g":
                inh = dict(inherited)
                inh.update({k: v for k, v in child.attrib.items() if k.startswith("data-") or k == "class"})
                walk_layer(child, layer, compose(tf, parse_transform(child.get("transform"))), inh, report, shapes,
                           counter)
                continue
            counter[0] += 1
            shapes.extend(shapes_of(child, layer, tf, inherited, counter[0]))
        except ParseError as e:
            counter[0] += 1
            report.error("parse", "%s: %s" % (element_label(child, layer, counter[0]), e))


def find_layers(root, report):
    found = {name: [] for name in LAYERS}

    def rec(el, tf, depth):
        for child in el:
            if not isinstance(child.tag, str) or local(child.tag) != "g":
                continue
            try:
                ctf = compose(tf, parse_transform(child.get("transform")))
            except ParseError as e:
                report.error("parse", "<g id=%s>: %s" % (child.get("id"), e))
                continue
            ident = child.get("id")
            if ident in found:
                found[ident].append((child, ctf))
            else:
                if depth == 0 and ident:
                    report.warn("layers", "unknown top-level group id=%s is ignored" % ident)
                rec(child, ctf, depth + 1)
    rec(root, (1.0, 1.0, 0.0, 0.0), 0)
    return found


def parse_svg(text, report=None):
    """{layer: [Shape]} (labels skipped), or None when the text is not an SVG. Problems go to report."""
    report = report if report is not None else Report()
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        report.error("parse", "not well-formed XML: %s" % e)
        return None
    if local(root.tag) != "svg":
        report.error("parse", "the root element is <%s>, not <svg>" % local(root.tag))
        return None
    try:
        vb = tuple(float(v) for v in re.split(r"[\s,]+", (root.get("viewBox") or "").strip()))
    except ValueError:
        vb = ()
    if vb != VIEWBOX:
        report.warn("viewbox", "viewBox is %r, the map spec says \"-8000 -6000 16000 12000\"" % root.get("viewBox"))
    found = find_layers(root, report)
    shapes = {name: [] for name in LAYERS}
    for name in LAYERS:
        if len(found[name]) > 1:
            report.error("layers", "layer id=\"%s\" exists %d times" % (name, len(found[name])))
        if name == "labels":
            continue
        counter = [0]
        for el, tf in found[name]:
            walk_layer(el, name, tf, {}, report, shapes[name], counter)
    return shapes


def read_svg(path, report=None):
    with open(path, encoding="utf-8") as f:
        return parse_svg(f.read(), report)
