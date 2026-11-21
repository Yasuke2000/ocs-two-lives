# Lura: accommodate the existing offset build — round60

[Original measured plan](englassia-fit-review.png) · [editable SVG](englassia-fit-review.svg) · [audit data](englassia-fit-review.json)

Englassia's existing blueprint contains an authored Freedom Academy and Free Guild fragment. Their national/capital setting is separately qualified by WIK-GUI-002 and OFF-EDU-001; the inspected classroom image OFF-VIS-G-059 supplies material context, not a surveyed campus. The architecture, street arrangement, clock tower, footprint and exact placement are **our interpretation**. This is not a measured canonical capital or a complete reconstruction of Lura.

## Measured fit and change

The three existing NBT slabs decode to128 ×60 ×112, with139,978 defined block entries, of which103,061 are non-air. Their local placement anchor is(64,5,92), not the box centre. The world anchor stays(-2900,-550). The old circle's98-block radius was derived from centred dimensions; actual placement extends mostly north of the anchor.

At integer column centres,464 of the14,336 template columns lay outside that circle. Including the existing eight-block build margin,1,688 of18,432 columns lay outside. The academy and guild envelopes themselves already fitted; this change must not be described as rescuing clipped school buildings. The actual former terrain mismatch was small: maximum0.1797 blocks across the template and0.3672 including its margin. No observed collapsed or flooded building is claimed.

The production circle is now **radius124**. The continuous buffered box requires123.223 blocks to its furthest corner, rounded up; all18,432 sampled columns are now within the circle and bilinearly level with the exported plate. The normal converter's larger sample disc selects walking height76 instead of75. This changes the planned template corner from(-2964,70,-642) to(-2964,71,-642). It does not move or migrate an existing Minecraft structure.

Only this one radius changes in the active SVG tree. All58 IDs and x/z centres, coasts, rivers, mountain/forest polygons, gameplay masks and road centrelines are retained. All other57 anchor records remain identical; Englassia alone changes exported y75→76. Circle radius and new level are build-accommodation choices, not new geographical source facts.

## Export and visual verification

The mandatory map checker passes: zero errors, all56 relations, the same two warnings (Laura's river/escarpment crossing and the preferred design-box size). The checker preview and cached official world illustration were inspected. The larger western reservation does not change national placement; existing deliberate scale and coast adaptations remain documented in regions.md.

A normal staging export completes in66.2 seconds with no converter warnings. Height changes in6,267 raster cells, maximum1.625 blocks, confined to the Englassia approach area. Biome, site, exclusion and ruggedness changes are local too; exact extents are in the JSON. Water and road masks and canon_map.txt remain byte-identical. Road centreline/bridge flags stay identical; profile-height changes and rounded-export grades are recorded separately. The terrain preview and numbered atlas are refreshed from the new normal export without changing labels or markers.

This checks designed surface accommodation and decoded template presence. It does not prove occupied-world clearance, lighting, repairs, local placement, era-correct residents or walkability. No structure files, build registry, protected runtime scripts, tools, main branch or server world are changed. In-game acceptance remains a technical handoff.

## Painting, evidence and remaining scope

The original R53 painting and its older equivalence sidecars remain historical evidence for their recorded sources. **The changed radius and height invalidate a claim of whole-source byte equivalence.** Current terrain is shown by world/atlas.png; the painted branch remains at its previous reviewed source until explicit integration/review. The tiny local preparation change is not silently relabelled as an unchanged painted heightmap.

One original design record, DES-ENG-060, brings the ledger to248 unique records (190 thematic/design/reference +58 coordinate interpretations). Fourteen directly read printed-LN claims and three separately classified author-side-story claims remain. Inventory129 and32 follow-ups retain their classifications: this improves a fit check, not complete capital geography or runtime coverage. No extra site ID, future Tempest development or later political event is activated. The full goal remains open.

The first repository run found the generated world/sites.toml stale at radius98. Running python -I tools/world/sites_from_builds.py updated only its Englassia radius to124; site_sizes.md and minimum98 remain unchanged. The generic derivation still uses centred dimensions; other offset-anchor templates require their own measured review. No generator code is changed.

Final repository validation and472 tests pass (26 skipped,zero failures,62.351 seconds);zero changed JS files. The source/normal-export hashes and248 unique ledger IDs are checked; the numbered atlas changes only its embedded terrain image.
