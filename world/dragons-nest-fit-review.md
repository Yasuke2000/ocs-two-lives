# Dragon's Nest: prepare the offset roost footprint — round62

[Measured plan and section](dragons-nest-fit-review.png) · [editable vector](dragons-nest-fit-review.svg) · [fit audit](dragons-nest-fit-review.json) · [30-template survey](template-terrain-fit-r62.json) · [current footprint CSV](../docs/research/tensura-world-2026-11-19/template-terrain-fit-r62.csv)

The public indexed [Canaat wiki article](https://tensura.fandom.com/wiki/Great_Canaat_Mountains), Background, places the nest on the range's highest peak. Its cited LN12 chapter4 is an **unread primary lead**. A direct page fetch returned402; public indexed text was readable. WIK-NEST-062 retains fan-wiki confidence. This does not establish the appearance,precise summit coordinates,block height or diameter of the roost. The existing bowl,spires,bones,hoard and snowy platform are **our interpretation**.

## Audit the actual offset

The existing73 ×46 ×73 NBT template has local anchor(36,9,62),near its south entrance,so its box extends mostly north. Two decoded z slabs contain245,134 defined entries and53,342 non-air blocks. The chosen world anchor stays(350,-2000),first air272,template corner(314,263,-2062). The highest decoded solid block lies at world y293;the declared template volume ends at308. Neither exceeds the build-height limit. This is an offline decoded-file check,not observed placement.

The old radius64 left161 of5,329 template columns and1,028 of7,921 buffered columns outside its preparation circle. Maximum designed-height mismatch was10.586 blocks across the template and52.645 with the eight-block margin. The central nest bowl was already inside; the unsupported preparation concerns outer plot corners and their margin. No claim of an observed collapsing or floating nest is made.

The continuous buffered box needs radius84; its four-block bilinear interpolation neighbours reach84.876 blocks from the anchor. **Radius85** therefore accommodates the box and all sampled raster neighbours. Every one of the7,921 integer column centres now has designed first-air272,without water or another site's mask crossing it. The radius and level are original build-accommodation choices,not canonical measurements.

## Scope of the terrain change

The active SVG tree changes only this radius. All58 IDs,world centres and walking levels remain;all58 exported anchor records are byte-identical. Coasts,country masks,forest/mountain/river outlines and road centrelines are unchanged. Native source geometry is still the converter's authority.

The normal export completes in65.6 seconds with no converter warnings. Height changes in2,507 raster cells,maximum absolute84.1875 blocks: a substantial **local summit/skirt** correction rather than an unchanged-terrain presentation. Some existing higher crest cells are lowered by at most6.4375 blocks. Water and road masks and canon_map.txt remain identical. Biome,site,exclusion and ruggedness differences are local and measured in the JSON. The Canaat high-pass profile changes at55 exported points;its centreline and bridge flags stay fixed. Twenty other road profiles remain byte-identical,and maximum exported grade stays0.5 within floating-point rounding.

The mandatory checker passes with zero errors,all56 relations and the same two warnings. The checker preview,official cached map and original plan/section were inspected. The enlarged authored summit preparation does not move the nest to another region or claim an exact canon summit shape. The terrain preview and numbered atlas are refreshed. The earlier R61 painted atlas remains reviewed against its older7a30cf41 source;it needs explicit integration for the new0b211ec7 source.

## Broader footprint survey and limits

The survey reads30 generated rectangular footprint requirements and their actual anchor offsets. It samples each integer column centre against the normal four-block height export;it does **not** decode all30 NBT models or test occupied Minecraft voxels. The other28 site IDs have no corresponding rectangular-template requirement in this survey and are not declared verified by omission.

Three carve templates require roof/cavity checks instead of a flat upper surface. Four coastal/lakeside templates can intentionally span water. For the remaining surface templates,the current CSV ranks actual variation separately from the mere fact that a rectangle extends outside a circle. Englassia and Elmine are flat;small margin-only variations at several western capitals do not justify automatically enlarging every reservation.

The dwarven arena,sacred-mountain approach and other measured surface differences remain a fit queue. The full later Tempest template also exceeds the present preparation in places;C18's initial village and future capacity must be handled separately. This round does not flatten a future metropolis into the post-Kijin forest. The source/fixed-rule/era/coverage scope remains intact.

Legacy build registries still use survey placement for the old world. This fixed-centre audit applies to the proposed own-world handoff;the technical switch must honour its intended centre/level. Runtime terrain skirts,occupied blocks,repairs,residents and walkability remain untested. No runtime code,tools,structure files,main branch,server chunks or deployment are changed.

## Evidence register

WIK-NEST-062 and DES-FIT-062 bring the ledger to250 unique records (192 thematic/design/reference +58 coordinate interpretations). The14 directly read printed-LN claims and3 separately classified author-side-story claims remain. SITE-027's stale Englassia radius is corrected98→124;SITE-018 follows the new nest radius64→85. All58 numeric site claims now match the production SVG. The seven formatting-only number differences found by the exploratory string comparison were not counted as stale geographical facts.

The129-entry inventory retains32 missing,partial or unverified representations. This survey and the nest preparation do not complete those locations or close runtime acceptance. The full goal remains open.

The high-pass grade adjustment extends beyond the site's127-block preparation/fade envelope;the JSON records those changed height cells explicitly. A future painting integration must cover the measured summit **and approach** differences. Final repository validation and472 tests pass (26 skipped,zero failures,62.286 seconds),zero changed JS. The atlas retains every non-image element;source/index/preview hashes,30 survey rows and250 unique evidence IDs are checked.
