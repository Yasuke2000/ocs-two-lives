"""tools/world/map_check.py: one small synthetic SVG per rule, plus the repo data (python -I -m unittest discover -s tests).

The synthetic world is a 4,000 x 3,000 landmass round (0, 0) with two anchors (`tempest`, `camp`) in region J. Each test
changes one thing and looks for the rule's error (or its absence). The data tests keep canon_relations.toml, biomes.txt
and the starter world/map.svg honest.
"""
import json
import math
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "world"))
import map_check as mc  # noqa: E402

LAYERS = ("coast", "lakes", "rivers", "mountains", "hills", "forests", "biomes", "regions", "roads", "sites", "labels")


def ring(x0, y0, x1, y1):
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    return [(x0, y0), (mx, y0), (x1, y0), (x1, my), (x1, y1), (mx, y1), (x0, y1), (x0, my)]


def pts(p):
    return " ".join("%d,%d" % q for q in p)


def attrs(a):
    return " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in a.items())


def poly(p, **a):
    return '<polygon %s points="%s"/>' % (attrs(a), pts(p))


def line(p, **a):
    return '<polyline fill="none" %s points="%s"/>' % (attrs(a), pts(p))


def circle(ident, x, y, r, kind, margin=48, **a):
    return '<circle data-id="%s" data-site="%s" data-margin="%s" cx="%d" cy="%d" r="%d" %s/>' % (
        ident, kind, margin, x, y, r, attrs(a))


LAND = ring(-2000, -1500, 2000, 1500)
BASE = {
    "coast": poly(LAND),
    "regions": poly(LAND, data_letter="J"),
    "sites": circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 20, "clearing"),
    "labels": "<text>x</text>",
}


def svg(viewbox="-8000 -6000 16000 12000", top="", **layers):
    parts = dict(BASE)
    parts.update(layers)
    groups = "".join('<g id="%s">%s</g>' % (n, parts.get(n, "")) for n in LAYERS if parts.get(n, "") is not None)
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s">%s%s</svg>' % (viewbox, groups, top)


def anchor(region="J", kind="spot", surface="land", landmark=None, name="x", of=None, dx=0, dz=0):
    return {"name": name, "region": region, "kind": kind, "surface": surface, "landmark": landmark, "x": 0, "z": 0,
            "of": of, "dx": dx, "dz": dz}


def config(**kw):
    anchors = kw.pop("anchors", {"tempest": anchor(kind="settlement"), "camp": anchor()})
    c = mc.Config(anchors, kw.pop("letters", {"J", "D"}), biomes=kw.pop("biomes", {"minecraft:plains", "tensura:ancient_forest"}),
                  **kw)
    return c


class Base(unittest.TestCase):
    def setUp(self):
        self._v1 = mc.V1_ROADS
        mc.V1_ROADS = ()

    def tearDown(self):
        mc.V1_ROADS = self._v1

    def run_check(self, text, cfg=None):
        report, shapes, sites = mc.check_svg(text, cfg or config())
        return report

    def msgs(self, report, rule=None, level="errors"):
        return [e["message"] for e in getattr(report, level) if rule is None or e["rule"] == rule]

    def assertError(self, report, needle, rule=None):
        found = self.msgs(report, rule)
        self.assertTrue(any(needle in m for m in found), "no error with %r in %s" % (needle, found))

    def assertClean(self, report, rule=None):
        self.assertEqual(self.msgs(report, rule), [])


class Structure(Base):
    def test_base_world_is_clean(self):
        r = self.run_check(svg())
        self.assertEqual(r.errors, [])

    def test_viewbox(self):
        self.assertError(self.run_check(svg(viewbox="0 0 100 100")), "viewBox is", "structure")

    def test_missing_layer_is_an_error_but_labels_only_warn(self):
        r = self.run_check(svg(rivers=None, labels=None))
        self.assertError(r, 'layer <g id="rivers"> is missing', "structure")
        self.assertFalse(any("labels" in m for m in self.msgs(r, "structure")))
        self.assertTrue(any("labels" in m for m in self.msgs(r, "structure", "warnings")))

    def test_unknown_group_and_duplicate_layer(self):
        r = self.run_check(svg(top='<g id="extra"/><g id="rivers"/>'))
        self.assertError(r, "unknown group id='extra'", "structure")
        self.assertError(r, 'layer id="rivers" exists 2 times', "structure")

    def test_transform_is_not_allowed(self):
        r = self.run_check(svg(lakes='<polygon transform="translate(5 5)" points="%s"/>' % pts(ring(100, 100, 300, 300))))
        self.assertError(r, "has a transform", "structure")

    def test_nested_group_is_not_allowed(self):
        r = self.run_check(svg(forests='<g>%s</g>' % poly(ring(100, 100, 300, 300), data_type="dark")))
        self.assertError(r, "nested groups", "structure")

    def test_unsupported_element(self):
        self.assertError(self.run_check(svg(hills='<ellipse cx="0" cy="0" rx="5" ry="5"/>')), "unsupported element <ellipse>")

    def test_not_xml(self):
        r = self.run_check("<svg")
        self.assertError(r, "not well-formed", "structure")


class PathParser(unittest.TestCase):
    def test_absolute_and_relative_lines_close(self):
        (pts_, closed, nodes), = mc.parse_path("M0 0 H10 V10 h-10 Z")
        self.assertEqual(pts_, [(0, 0), (10, 0), (10, 10), (0, 10)])
        self.assertTrue(closed)
        self.assertEqual(nodes, 4)

    def test_implicit_lineto_and_relative_move(self):
        subs = mc.parse_path("m 1 1 2 0 0 2 z m 10 10 l 5 0")
        self.assertEqual(subs[0][0], [(1, 1), (3, 1), (3, 3)])
        self.assertTrue(subs[0][1])
        self.assertEqual(subs[1][0], [(11, 11), (16, 11)])
        self.assertFalse(subs[1][1])

    def test_curves_are_flattened(self):
        (p, closed, nodes), = mc.parse_path("M0 0 C 0 10 10 10 10 0 Q 15 -10 20 0 Z")
        self.assertGreater(len(p), 20)
        self.assertEqual(nodes, 3)
        self.assertEqual(p[-1], (20.0, 0.0))

    def test_unsupported_command(self):
        with self.assertRaises(mc.ParseError):
            mc.parse_path("M0 0 A5 5 0 0 1 10 10")

    def test_transform_translate_and_scale(self):
        t = mc.parse_transform("translate(10 20) scale(2)")
        self.assertEqual(mc.apply(t, (1, 1)), (12, 22))
        with self.assertRaises(mc.ParseError):
            mc.parse_transform("rotate(45)")


class Polygons(Base):
    def test_open_path_in_a_polygon_layer(self):
        r = self.run_check(svg(hills='<path data-height="80" d="M0 0 L100 0 L100 100 L50 120 L0 100 L-20 50 L-20 20 L0 5"/>'))
        self.assertError(r, "is open", "polygon")

    def test_closed_path_is_accepted(self):
        d = "M0 0 H100 V100 H0 Z"  # 4 nodes: too few vertices, but closed
        r = self.run_check(svg(hills='<path data-height="80" d="%s"/>' % d))
        self.assertFalse(any("is open" in m for m in self.msgs(r, "polygon")))
        self.assertError(r, "4 vertices (allowed 8..400)", "polygon")

    def test_vertex_count_upper_limit(self):
        import math
        big = [(round(300 * math.cos(a / 401 * 2 * math.pi)), round(300 * math.sin(a / 401 * 2 * math.pi))) for a in range(401)]
        self.assertError(self.run_check(svg(hills=poly(big, data_height=80))), "401 vertices", "polygon")

    def test_self_intersection(self):
        bow = [(0, 0), (200, 200), (200, 0), (0, 200), (-50, 100), (-60, 50), (-40, 20), (-20, 10)]
        self.assertError(self.run_check(svg(hills=poly(bow, data_height=80))), "crosses itself", "polygon")

    def test_inside_the_viewbox(self):
        r = self.run_check(svg(forests=poly(ring(7900, 0, 8100, 100), data_type="dark")))
        self.assertError(r, "outside the viewBox", "polygon")

    def test_river_must_be_open(self):
        r = self.run_check(svg(rivers=poly(ring(0, 0, 100, 100), data_width=10)))
        self.assertError(r, "is closed", "polygon")


class Water(Base):
    def test_river_width_range(self):
        for w, ok in ((3, False), (4, True), (24, True), (25, False)):
            r = self.run_check(svg(rivers=line([(-500, -500), (-500, 1505)], data_width=w)))
            self.assertEqual(not self.msgs(r, "attribute"), ok, w)

    def test_river_without_width(self):
        r = self.run_check(svg(rivers=line([(-500, -500), (-500, 1505)])))
        self.assertError(r, "no data-width", "attribute")

    def test_river_ends_in_the_sea_or_a_lake(self):
        self.assertClean(self.run_check(svg(rivers=line([(-500, -500), (-500, 1510)], data_width=10))), "water")
        lake = poly(ring(-700, 100, -300, 300))
        self.assertClean(self.run_check(svg(lakes=lake, rivers=line([(-500, -500), (-500, 200)], data_width=10))), "water")

    def test_river_ending_on_dry_land(self):
        r = self.run_check(svg(rivers=line([(-500, -500), (-500, 400)], data_width=10)))
        self.assertError(r, "on dry land", "water")

    def test_river_ending_too_far_at_sea(self):
        r = self.run_check(svg(rivers=line([(-500, -500), (-500, 1600)], data_width=10)))
        self.assertError(r, "out at sea", "water")

    def test_river_starting_in_the_sea_or_in_a_lake(self):
        r = self.run_check(svg(rivers=line([(-3000, 0), (-1900, 0)], data_width=10)))
        self.assertError(r, "starts at", "water")
        lake = poly(ring(-700, 100, -300, 300))
        r = self.run_check(svg(lakes=lake, rivers=line([(-500, 200), (-500, 1510)], data_width=10)))
        self.assertError(r, "starts at", "water")

    def test_river_crossing_a_mountain_warns(self):
        r = self.run_check(svg(mountains=poly(ring(-800, 0, -200, 600), data_peak=200),
                               rivers=line([(-500, -500), (-500, 1505)], data_width=10)))
        self.assertTrue(any("crosses the mountain" in m for m in self.msgs(r, "water", "warnings")))

    def test_lake_outside_land(self):
        r = self.run_check(svg(lakes=poly(ring(1900, 0, 2400, 300))))
        self.assertError(r, "outside the land", "water")

    def test_lake_crossing_the_coast_line(self):
        bay = [(-2000, -1500), (2000, -1500), (2000, 1500), (500, 1500), (500, 0), (-500, 0), (-500, 1500), (-2000, 1500)]
        lake = [(-800, 290), (-790, 290), (790, 290), (800, 290), (800, 310), (790, 310), (-790, 310), (-800, 310)]
        r = self.run_check(svg(coast=poly(bay), lakes=poly(lake)))
        self.assertError(r, "crosses the coast line", "water")

    def test_mountain_in_the_sea(self):
        r = self.run_check(svg(mountains=poly(ring(2500, 0, 3000, 400), data_peak=200)))
        self.assertError(r, "lies partly in the sea", "water")


class Attributes(Base):
    def test_mountain_peak(self):
        for v, ok in ((99, False), (100, True), (300, True), (301, False), (None, False)):
            a = {} if v is None else {"data_peak": v}
            r = self.run_check(svg(mountains=poly(ring(-800, 0, -200, 600), **a)))
            self.assertEqual(not self.msgs(r, "attribute"), ok, v)

    def test_hill_height(self):
        for v, ok in ((69, False), (70, True), (150, True), (151, False)):
            r = self.run_check(svg(hills=poly(ring(-800, 0, -200, 600), data_height=v)))
            self.assertEqual(not self.msgs(r, "attribute"), ok, v)

    def test_optional_shape_and_rugged_are_validated(self):
        r = self.run_check(svg(mountains=poly(ring(-800, 0, -200, 600), data_peak=200, data_shape="cone", data_rugged=2)))
        self.assertError(r, "data-shape 'cone'", "attribute")
        self.assertError(r, "data-rugged '2'", "attribute")

    def test_forest_types(self):
        for t in mc.FOREST_TYPES:
            r = self.run_check(svg(forests=poly(ring(-800, 0, -200, 600), data_type=t)))
            self.assertClean(r, "attribute")
        r = self.run_check(svg(forests=poly(ring(-800, 0, -200, 600), data_type="mixed")))
        self.assertError(r, "data-type 'mixed'", "attribute")

    def test_biome_list(self):
        ok = self.run_check(svg(biomes=poly(ring(-800, 0, -200, 600), data_biome="minecraft:plains")))
        self.assertClean(ok, "attribute")
        bare = self.run_check(svg(biomes=poly(ring(-800, 0, -200, 600), data_biome="plains")))
        self.assertClean(bare, "attribute")
        bad = self.run_check(svg(biomes=poly(ring(-800, 0, -200, 600), data_biome="minecraft:beach")))
        self.assertError(bad, "is not allowed", "attribute")

    def test_region_letter(self):
        r = self.run_check(svg(regions=poly(LAND, data_letter="Z")))
        self.assertError(r, "letter 'Z' is not in canon_regions.json", "attribute")

    def test_road_kind(self):
        r = self.run_check(svg(roads=line([(55, 0), (480, 0)], data_kind="highway")))
        self.assertError(r, "data-kind 'highway'", "attribute")

    def test_jar_check(self):
        with tempfile.TemporaryDirectory() as d:
            jar = Path(d) / "t.jar"
            with zipfile.ZipFile(jar, "w") as z:
                z.writestr("data/tensura/worldgen/biome/ancient_forest.json", "{}")
            self.assertEqual(mc.check_jar({"tensura:ancient_forest", "minecraft:plains"}, jar), [])
            bad = mc.check_jar({"tensura:ancient_forest", "tensura:nonsense"}, jar)
            self.assertEqual(len(bad), 1)
            self.assertIn("tensura:nonsense", bad[0])
            self.assertEqual(mc.check_jar({"tensura:x"}, None), [])


class Regions(Base):
    def test_uncovered_land_is_an_error(self):
        r = self.run_check(svg(regions=poly(ring(-2000, -1500, 0, 1500), data_letter="J")))
        self.assertError(r, "belong to no region", "region")

    def test_overlap_on_land_is_an_error(self):
        r = self.run_check(svg(regions=poly(LAND, data_letter="J") + poly(ring(0, -1500, 2000, 1500), data_letter="D")))
        self.assertError(r, "overlap on land", "region")

    def test_a_letter_once_per_landmass(self):
        two = poly(ring(-2000, -1500, 0, 1500), data_letter="J") + poly(ring(0, -1500, 2000, 1500), data_letter="J")
        self.assertError(self.run_check(svg(regions=two)), "letter J has 2 polygons", "region")

    def test_two_regions_that_share_an_edge_are_fine(self):
        two = poly(ring(-2000, -1500, 0, 1500), data_letter="J") + poly(ring(0, -1500, 2000, 1500), data_letter="D")
        cfg = config(anchors={"tempest": anchor(region="D", kind="settlement"), "camp": anchor(region="D")})
        r = self.run_check(svg(regions=two, sites=circle("tempest", 500, 0, 50, "clearing") + circle("camp", 900, 0, 20, "clearing")), cfg)
        self.assertClean(r, "region")

    def test_lake_water_needs_no_region(self):
        lake = poly(ring(-1000, -500, 1000, 500))
        r = self.run_check(svg(lakes=lake, regions=poly(ring(-2000, -1500, -1000, 1500), data_letter="J")
                               + poly(ring(1000, -1500, 2000, 1500), data_letter="J")))
        self.assertTrue(any("letter J has 2 polygons" in m for m in self.msgs(r, "region")))


class Sites(Base):
    def test_every_anchor_exactly_once(self):
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing")))
        self.assertError(r, "anchor camp (x) has no site", "site")
        r = self.run_check(svg(sites=BASE["sites"] + circle("camp", 900, 0, 20, "clearing")))
        self.assertError(r, "anchor camp has 2 sites", "site")

    def test_unknown_site_id(self):
        r = self.run_check(svg(sites=BASE["sites"] + circle("ghost", 900, 0, 20, "clearing")))
        self.assertError(r, "site ghost is not an anchor", "site")

    def test_kind_and_radius(self):
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "pin") + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "data-site 'pin'", "site")
        for rad, ok in ((7, False), (8, True), (160, True), (161, False)):
            r = self.run_check(svg(sites=circle("tempest", 0, 0, rad, "clearing") + circle("camp", 900, 0, 20, "clearing")))
            self.assertEqual(not any("outside 8..160" in m for m in self.msgs(r, "site")), ok, rad)

    def test_a_site_in_the_sea(self):
        r = self.run_check(svg(sites=circle("tempest", 3000, 0, 50, "clearing") + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "is in the ocean", "site")

    def test_a_disc_must_not_touch_the_coast(self):
        r = self.run_check(svg(sites=circle("tempest", 1980, 0, 50, "clearing") + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "reaches the coast line", "site")

    def test_48_blocks_from_the_coast(self):
        r = self.run_check(svg(sites=circle("tempest", 1960, 0, 8, "clearing") + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "40 blocks from the coast (minimum 48)", "site")
        r = self.run_check(svg(sites=circle("tempest", 1940, 0, 8, "clearing") + circle("camp", 500, 0, 20, "clearing")))
        self.assertClean(r, "site")

    def test_a_disc_must_not_reach_a_lake(self):
        r = self.run_check(svg(lakes=poly(ring(510, -100, 700, 100))))
        self.assertError(r, "reaches a lake", "site")

    def two(self, d, r1=50, r2=20, m1=48, m2=48, **kw):
        return self.run_check(svg(sites=circle("tempest", 0, 0, r1, "clearing", margin=m1) +
                                  circle("camp", d, 0, r2, "clearing", margin=m2)), config(**kw))

    def test_spacing_is_the_edge_gap_against_the_margin(self):
        # edge gap = distance - (r1 + r2) must reach the larger data-margin (48): 50 + 20 + 48 = 118
        self.assertError(self.two(117), "edge gap 47 = distance - (r1_eff 50 + r2_eff 20) is below the larger data-margin 48", "site")
        self.assertClean(self.two(118), "site")
        self.assertClean(self.two(300), "site")

    def test_the_larger_margin_of_the_two_sites_counts(self):
        self.assertError(self.two(150, m2=100), "below the larger data-margin 100", "site")
        self.assertClean(self.two(171, m2=100), "site")
        self.assertClean(self.two(171, m1=100, m2=8), "site")

    def test_a_missing_margin_is_48_for_the_spacing(self):
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing", margin=48).replace('data-margin="48"', "")
                               + circle("camp", 100, 0, 20, "clearing", margin=0)))
        self.assertError(r, "below the larger data-margin 48", "site")

    def test_spacing_uses_min_r_from_sites_toml(self):
        # drawn 50 and 20, but the builds need 148 and 75: 148 + 75 + 48 = 271
        need = {"tempest": 148, "camp": 75}
        self.assertError(self.two(270, min_r=need), "r1_eff 148 + r2_eff 75", "site")
        self.assertClean(self.two(271, min_r=need), "site")
        self.assertClean(self.two(270), "site")          # no sites.toml: the drawn r stands alone

    def test_tempest_and_the_sealed_cave_fit_at_the_starter_distance(self):
        # the W1 report: 2 x (r1 + r2) wanted 446 blocks, canon has 424; the edge gap is 424 - 223 = 201
        self.assertClean(self.two(424, r1=148, r2=75, min_r={"tempest": 148, "camp": 75}), "site")

    def test_drawn_too_small_warns_per_site(self):
        r = self.two(500, min_r={"tempest": 148, "camp": 20})
        w = self.msgs(r, "site", "warnings")
        self.assertEqual(len(w), 1, w)
        self.assertIn("site tempest: drawn too small, r 50 < min_r 148", w[0])
        self.assertIn("enlarged to 148", w[0])
        self.assertEqual(self.msgs(self.two(500, r1=148, min_r={"tempest": 148}), "site", "warnings"), [])
        self.assertEqual(self.msgs(self.two(500), "site", "warnings"), [])

    def test_min_r_file_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(mc.load_min_r(Path(d) / "nope.toml"), {})
            self.assertEqual(mc.load_min_r(None), {})
            f = Path(d) / "sites.toml"
            f.write_text('[tempest]\nmin_r = 148\n[camp]\nr = 8\n[forest]\nlight = "x"\n', encoding="utf-8")
            self.assertEqual(mc.load_min_r(f), {"tempest": 148})
            f.write_text("not = [toml", encoding="utf-8")
            self.assertEqual(mc.load_min_r(f), {})

    def relative(self, camp_at, **kw):
        cfg = config(anchors={"tempest": anchor(kind="settlement"), "camp": anchor(of="tempest", dx=300, dz=-100)}, **kw)
        return self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing") + circle("camp", camp_at[0], camp_at[1], 20, "clearing")), cfg)

    def test_relative_anchor_far_from_parent_plus_offset_warns(self):
        w = self.msgs(self.relative((300, 0)), "site", "warnings")        # 100 off
        self.assertTrue(any("relative anchor camp is drawn at (300, 0), 100 blocks from tempest + (300, -100)" in m for m in w), w)
        self.assertEqual(self.msgs(self.relative((300, -100)), "site", "warnings"), [])
        self.assertEqual(self.msgs(self.relative((320, -120)), "site", "warnings"), [])     # 28 off
        self.assertEqual(len(self.msgs(self.relative((340, -100)), "site", "warnings")), 1)  # 40 off

    def test_relative_anchors_are_exempt_from_the_spacing_of_their_family(self):
        cfg = config(anchors={"tempest": anchor(kind="settlement"), "camp": anchor(of="tempest", dx=10, dz=10),
                              "pin": anchor(of="tempest", dx=14, dz=10)})
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing") + circle("camp", 10, 10, 8, "clearing")
                               + circle("pin", 14, 10, 8, "clearing")), cfg)
        self.assertClean(r, "site")
        # an unrelated site still has to keep its distance
        self.assertError(self.two(60), "below the larger data-margin", "site")

    def test_region_of_the_anchor(self):
        two = poly(ring(-2000, -1500, 0, 1500), data_letter="J") + poly(ring(0, -1500, 2000, 1500), data_letter="D")
        cfg = config(anchors={"tempest": anchor(region="J", kind="settlement"), "camp": anchor(region="D")})
        r = self.run_check(svg(regions=two, sites=circle("tempest", -500, 0, 50, "clearing") + circle("camp", -900, 0, 20, "clearing")), cfg)
        self.assertError(r, "site camp at (-900, 0) is in region J, anchors.toml says region D", "site")
        cfg = config(anchors={"tempest": anchor(region="J", kind="settlement"), "camp": anchor(region="Q")}, letters={"J", "Q"})
        r = self.run_check(svg(), cfg)
        self.assertError(r, "no region polygon with letter Q", "site")

    def test_carve_needs_a_mountain_or_hill(self):
        sites = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 20, "carve")
        self.assertError(self.run_check(svg(sites=sites)), "carve site camp", "site")
        self.assertClean(self.run_check(svg(sites=sites, mountains=poly(ring(300, -200, 700, 200), data_peak=200))), "site")
        self.assertClean(self.run_check(svg(sites=sites, hills=poly(ring(300, -200, 700, 200), data_height=90))), "site")

    def test_village_reach(self):
        cfg = config(anchors={"tempest": anchor(kind="settlement"), "camp": anchor(kind="landmark", landmark="lm")}, reach={"lm": 56})
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 40, "village")), cfg)
        self.assertError(r, "below the landmark lm's reach 56", "site")
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 60, "village")), cfg)
        self.assertClean(r, "site")

    def test_lakeside_must_touch_water(self):
        sites = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 20, "lakeside")
        self.assertError(self.run_check(svg(sites=sites)), "lakeside site camp", "site")
        self.assertError(self.run_check(svg(sites=sites, lakes=poly(ring(560, -100, 700, 100)))), "lakeside site camp", "site")
        self.assertClean(self.run_check(svg(sites=sites, lakes=poly(ring(530, -100, 700, 100)))), "site")
        self.assertClean(self.run_check(svg(sites=sites, rivers=line([(520, -400), (520, 1510)], data_width=24))), "site")

    def test_coast_must_touch_the_sea(self):
        far = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 1900, 0, 20, "coast")
        near = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 1970, 0, 20, "coast")
        self.assertError(self.run_check(svg(sites=far)), "coast site camp", "site")
        self.assertClean(self.run_check(svg(sites=near)), "site")

    def test_only_water_anchors_may_stand_in_water(self):
        lake = poly(ring(300, -200, 700, 200))
        sites = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 20, "lakeside")
        self.assertError(self.run_check(svg(sites=sites, lakes=lake)), "is in a lake", "site")
        cfg = config(anchors={"tempest": anchor(kind="settlement"), "camp": anchor(kind="pin", surface="water")})
        self.assertClean(self.run_check(svg(sites=sites, lakes=lake), cfg), "site")

    def test_margins_warn_when_missing(self):
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing", margin=48).replace('data-margin="48"', "")
                               + circle("camp", 500, 0, 20, "clearing")))
        self.assertTrue(any("1 sites have no data-margin" in m and "tempest" in m for m in self.msgs(r, "margin", "warnings")))
        self.assertEqual(self.msgs(self.run_check(svg()), "margin", "warnings"), [])
        r = self.run_check(svg(roads=line([(55, 0), (480, 0)], data_kind="main", data_id="a_b")))
        self.assertTrue(any("1 roads have no data-margin" in m for m in self.msgs(r, "margin", "warnings")))
        r = self.run_check(svg(sites=circle("tempest", 0, 0, 50, "clearing", margin=999) + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "data-margin '999'", "attribute")


class Roads(Base):
    def road(self, pts_=((55, 0), (480, 0)), **a):
        a.setdefault("data_kind", "main")
        a.setdefault("data_margin", 24)
        return line(list(pts_), **a)

    def test_a_clean_road_derives_its_id(self):
        r = self.run_check(svg(roads=self.road()))
        self.assertClean(r, "road")

    def test_ends_must_touch_sites(self):
        r = self.run_check(svg(roads=self.road(((55, 0), (300, 400)))))
        self.assertError(r, "its end", "road")

    def test_water_run_longer_than_64_is_an_error(self):
        r = self.run_check(svg(roads=self.road(), lakes=poly(ring(200, -100, 300, 100))))
        self.assertError(r, "crosses water", "road")

    def test_short_bridge_over_water_is_fine(self):
        r = self.run_check(svg(roads=self.road(), lakes=poly(ring(200, -100, 250, 100))))
        self.assertClean(r, "road")
        self.assertEqual(r.stats["bridges"], 1)

    def test_river_corridor_counts_as_water(self):
        r = self.run_check(svg(roads=self.road(), rivers=line([(250, -400), (250, 1510)], data_width=24)))
        self.assertClean(r, "road")
        self.assertEqual(r.stats["bridges"], 1)
        r = self.run_check(svg(roads=self.road(((55, 0), (250, 0), (255, 600), (500, 0))), rivers=line([(250, -400), (250, 1510)], data_width=24)))
        self.assertError(r, "crosses water", "road")

    def test_the_four_v1_roads_are_required(self):
        mc.V1_ROADS = self._v1
        r = self.run_check(svg(roads=self.road(data_id="tempest_dwargon")))
        self.assertError(r, "the v1 road tempest_blumund is missing", "road")
        self.assertFalse(any("tempest_dwargon is missing" in m for m in self.msgs(r, "road")))

    def test_duplicate_road_ids(self):
        r = self.run_check(svg(roads=self.road(data_id="x") + self.road(data_id="x")))
        self.assertError(r, "road id x is used twice", "road")

    def test_distant_build_sites_warn(self):
        cfg = config(anchors={"tempest": anchor(kind="settlement"), "camp": anchor(kind="build")})
        r = self.run_check(svg(roads=self.road(((55, 0), (70, 0)))), cfg)
        self.assertTrue(any("build sites are more than 400 blocks" in m for m in self.msgs(r, "road", "warnings")))


class Canon(Base):
    def rel(self, **kw):
        d = {"a": "camp", "b": "tempest", "dir": "E", "min": 400, "max": 600, "source": "design/lore/world.md"}
        d.update(kw)
        return config(relations=[d])

    def test_a_holding_relation(self):
        r = self.run_check(svg(), self.rel())
        self.assertEqual(r.errors, [])
        self.assertEqual(len(r.relations), 1)
        self.assertTrue(r.relations[0]["ok"])

    def test_distance_range(self):
        self.assertError(self.run_check(svg(), self.rel(min=600, max=900)), "distance 500 is outside 600..900", "canon")
        self.assertError(self.run_check(svg(), self.rel(max=450)), "distance 500 is outside 400..450", "canon")

    def test_direction_and_tolerance(self):
        self.assertError(self.run_check(svg(), self.rel(dir="W")), "is not within 45 deg of W", "canon")
        self.assertError(self.run_check(svg(), self.rel(dir="NNE")), "is not within 25 deg of NNE", "canon")
        self.assertClean(self.run_check(svg(), self.rel(dir="SE", tol=50)), "canon")

    def test_bearing_range_wraps_through_north(self):
        self.assertClean(self.run_check(svg(), self.rel(dir="any", bearing=[60, 120])), "canon")
        self.assertError(self.run_check(svg(), self.rel(dir="any", bearing=[100, 170])), "outside 100..170 deg", "canon")
        self.assertTrue(mc.bearing_in(5, 330, 30))
        self.assertFalse(mc.bearing_in(90, 330, 30))

    def test_defaults_of_tolerance(self):
        self.assertEqual([mc.default_tolerance(d) for d in ("N", "NE", "NNE")], [45.0, 35.0, 25.0])

    def test_compass(self):
        self.assertEqual(mc.bearing((0, 0), (0, -10)), 0)
        self.assertEqual(round(mc.bearing((0, 0), (10, 0))), 90)
        self.assertEqual(round(mc.bearing((0, 0), (0, 10))), 180)
        self.assertEqual(mc.wind(315), "NW")

    def test_site_rules(self):
        cfg = config(site_rules=[{"id": "camp", "x_min": 600, "source": "s"}])
        self.assertError(self.run_check(svg(), cfg), "x 500 is not >= 600", "canon")
        cfg = config(site_rules=[{"id": "camp", "inside": "forests", "forest_types": ["dark"], "source": "s"}])
        self.assertError(self.run_check(svg(), cfg), "not inside a forest polygon of type dark", "canon")
        ok = self.run_check(svg(forests=poly(ring(300, -200, 700, 200), data_type="dark")), cfg)
        self.assertClean(ok, "canon")
        cfg = config(site_rules=[{"id": "camp", "lake_width_min": 400, "source": "s"}])
        self.assertError(self.run_check(svg(), cfg), "the lake there is 0 blocks wide", "canon")
        cfg = config(site_rules=[{"id": "camp", "near_road": 16, "road_kind": "main", "source": "s"}])
        self.assertError(self.run_check(svg(), cfg), "from a main road", "canon")

    def test_sea_gap_between_landmasses(self):
        isl = poly(ring(2600, -300, 3400, 300))
        cfg = config(gaps=[{"a": "camp", "b": "tempest", "min": 500, "max": 800, "source": "s"}])
        sites = circle("tempest", 0, 0, 50, "clearing") + circle("camp", 3000, 0, 20, "clearing")
        regions = poly(LAND, data_letter="J") + poly(ring(2600, -300, 3400, 300), data_letter="D")
        cfg.anchors["camp"]["region"] = "D"
        r = self.run_check(svg(coast=poly(LAND) + isl, regions=regions, sites=sites), cfg)
        self.assertEqual(self.msgs(r, "canon"), [])
        cfg.gaps[0].update(min=100, max=300)
        r = self.run_check(svg(coast=poly(LAND) + isl, regions=regions, sites=sites), cfg)
        self.assertError(r, "the sea between the landmasses of camp and tempest is 600 blocks", "canon")

    def test_relation_data_problems_are_errors(self):
        cfg = config(problems=["relation #1 (a -> b): dir 'up' is not a compass wind"])
        self.assertError(self.run_check(svg(), cfg), "dir 'up'", "canon")


class Size(Base):
    def test_mainland_over_the_limit(self):
        big = poly(ring(-6000, -1000, 6000, 1000))
        r = self.run_check(svg(coast=big, regions=poly(ring(-6000, -1000, 6000, 1000), data_letter="J"),
                               sites=circle("tempest", 0, 0, 50, "clearing") + circle("camp", 500, 0, 20, "clearing")))
        self.assertError(r, "the mainland is 12000 x 2000 blocks, over the limit 11000 x 8000", "size")

    def test_mainland_warning_and_design_box(self):
        w = poly(ring(-5200, -1000, 5200, 1000))
        r = self.run_check(svg(coast=w, regions=poly(ring(-5200, -1000, 5200, 1000), data_letter="J")))
        self.assertTrue(any("over 10000 x 7500" in m for m in self.msgs(r, "size", "warnings")))
        box = r.stats["design_box"]
        self.assertEqual((box["width"], box["height"]), (13312, 5120))
        self.assertTrue(any("above the target" in m for m in self.msgs(r, "size", "warnings")))

    def test_design_box_cap_and_land_share(self):
        tall = poly(ring(-1000, -5000, 1000, 5000))
        r = self.run_check(svg(coast=tall, regions=poly(ring(-1000, -5000, 1000, 5000), data_letter="J")))
        self.assertEqual(r.stats["design_box"]["height"], 13312)
        self.assertError(r, "is 5120 x 13312, over the cap 14336 x 11264", "size")

    def test_small_world_is_fine(self):
        r = self.run_check(svg())
        self.assertEqual(self.msgs(r, "size"), [])
        self.assertEqual(r.stats["mainland_bbox"], [4000, 3000])


class Jura(Base):
    def test_rings_need_forest(self):
        r = self.run_check(svg())
        self.assertTrue(any("round Tempest" in m for m in self.msgs(r, "jura", "warnings")))

    def test_ancient_or_dark_forest_round_tempest(self):
        r = self.run_check(svg(forests=poly(ring(-700, -700, 700, 700), data_type="dark")))
        self.assertEqual(self.msgs(r, "jura", "warnings"), [])
        r = self.run_check(svg(forests=poly(ring(-700, -700, 700, 700), data_type="light")))
        self.assertTrue(any("round Tempest" in m for m in self.msgs(r, "jura", "warnings")))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "world" / "map_check.py"), *args],
                              capture_output=True, text=True, cwd=ROOT)

    def test_exit_codes_json_and_preview(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.svg"
            bad.write_text(svg(viewbox="0 0 1 1"), encoding="utf-8")
            r = self.run_cli(str(bad), "--json")
            self.assertEqual(r.returncode, 1)
            rep = json.loads(r.stdout)
            self.assertFalse(rep["ok"])
            self.assertTrue(rep["errors"])
            r = self.run_cli(str(Path(d) / "missing.svg"))
            self.assertEqual(r.returncode, 2)
            png = Path(d) / "p.png"
            r = self.run_cli(str(ROOT / "world" / "map.svg"), "--preview", str(png))
            self.assertEqual(r.returncode, 0, r.stdout)
            data = png.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(int.from_bytes(data[16:20], "big"), 2000)
            self.assertEqual(int.from_bytes(data[20:24], "big"), 1500)


class RepoData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = mc.load_config()

    def test_relations_file_is_consistent(self):
        self.assertEqual(self.cfg.problems, [])
        self.assertGreaterEqual(len(self.cfg.relations), 50)
        for r in self.cfg.relations + self.cfg.site_rules + self.cfg.gaps:
            src = r["source"]
            self.assertTrue(src.startswith("design/lore/"), src)
            self.assertTrue((ROOT / src).is_file(), src)
        for r in self.cfg.relations:
            self.assertTrue(r.get("note"), r)
            self.assertLessEqual(r.get("min", 0), r.get("max", 1e9), r)

    def test_biome_list_follows_the_design(self):
        b = self.cfg.biomes
        for want in ("tensura:ancient_forest", "tensura:barren_land", "tensura:desert_of_death", "tensura:miasmic_plains",
                     "minecraft:plains", "minecraft:jagged_peaks", "minecraft:mushroom_fields"):
            self.assertIn(want, b)
        for banned in ("minecraft:river", "minecraft:beach", "minecraft:ocean", "minecraft:stony_shore", "minecraft:frozen_river"):
            self.assertNotIn(banned, b)
        self.assertEqual(len([x for x in b if x.startswith("tensura:")]), 4)

    def test_starter_map_has_one_site_per_anchor_and_passes(self):
        text = (ROOT / "world" / "map.svg").read_text(encoding="utf-8")
        report, shapes, sites = mc.check_svg(text, self.cfg)
        self.assertEqual(report.errors, [])
        self.assertEqual(sorted(s.id for s in sites), sorted(self.cfg.anchors))
        self.assertEqual(len(sites), 58)
        self.assertEqual(len([r for r in report.relations if r["ok"]]), len(self.cfg.relations))
        self.assertEqual(report.stats["mainland_bbox"][0] <= 10000, True)
        self.assertEqual(self.msgs_of(report, "margin"), [])
        # the starter is drawn at the real rule: no site below its min_r, every relative anchor at parent + offset
        self.assertEqual(self.msgs_of(report, "site"), [])
        self.assertEqual(self.cfg.min_r["tempest"], 148)
        self.assertEqual(self.cfg.min_r["sealed_cave"], 75)
        by = {s.id: s for s in sites}
        self.assertGreaterEqual(math.dist(by["tempest"].pt, by["sealed_cave"].pt) - 223, 48)
        self.assertEqual(len([a for a in self.cfg.anchors.values() if a.get("of")]), 7)

    def test_starter_map_without_sites_toml_still_passes(self):
        cfg = mc.load_config(sites=ROOT / "does-not-exist.toml")
        self.assertEqual(cfg.min_r, {})
        report, _, _ = mc.check_svg((ROOT / "world" / "map.svg").read_text(encoding="utf-8"), cfg)
        self.assertEqual(report.errors, [])

    @staticmethod
    def msgs_of(report, rule):
        return [e for e in report.warnings if e["rule"] == rule]


if __name__ == "__main__":
    unittest.main()
