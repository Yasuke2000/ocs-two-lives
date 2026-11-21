# Shared curves and exact region coverage — round 49

The adopted SVG uses the **same boundary arcs** in neighbouring regions and the coast.
The nine outlines that previously exceeded120 nodes are now all at or below120.
The mainland has120 nodes; the eastern foothill woodland has97. All82 closed outlines
are within the mandatory8–400 range and at most120; eight simple outlines still use
fewer than the brief's preferred20. No padding vertices are inserted to hide that.

Source: `cb07cce7f028aaaa71914209928db3a8ad1b7b9a892ab24520ab827072d62371`.
Baseline78ca1c8/source7d021766. [Geometry/export evidence](shared-curve-review.json),
[checker preview](preview.png),[updated numbered atlas](atlas.png),[terrain preview](terrain-preview.png).

## What changes and what it means

The old masks had small numerical seams/overlaps. A planar partition assigns those
faces once, then extracts57 shared arcs. Very thin numerical faces are assigned by
proximity to existing region interiors (0.02-block inset). These are gameplay masks,
not newly verified political borders. Both neighbour paths reuse each fitted arc. Removing very thin numerical spurs can move an individual mask tip farther than the coast; the largest measured region-boundary displacement is42.327 blocks inS. Per-mask area/displacement data are retained in the JSON; this is not a town move or a new canonical frontier.

Coastal joins,near-coincident border contacts,river mouths,site buffers and extreme
shore points are preserved. Coordinates use a1/1,048,576-block authoring grid so the
tool's16-step cubic sampling produces identical reversed shared segments. Dynamic
partitioning chooses fewer segments within the measured tolerance; straight closing
edges use SVG Z directly. This precision is a drawing convention,not a canon survey.

The native parsed coast moves at most15.959 blocks from the old authored shore;
141,991 square blocks change land classification,mostly balanced additions/removals.
This is0.334% of the old land area,not a measurement of the fictional continent.
The woodland edge moves at most0.499 blocks. The main landmass remains9989×6250,
in the same12800×10752 design box. Source proportional compromises remain C12.
All exact control points and minor shore bends are **our interpretation / DES-CUR-049**.

All58 site tuples,21 road geometries,9 lakes,8 rivers,10 mountains,6 hills,20 biome
polygons,11 other forests and both island coasts are unchanged. Every site remains
in its previous region; no site's full-disc coverage status becomes worse. In
particular Siltrosso's66-block circle keeps its shore contact and mask coverage.
No ruler,capital,canonical location,era event or technical rule is newly invented.

## Mandatory and exact-geometry checks

The external candidate and adopted production map both pass the standard checker:
**0 errors,all56 relations pass,the same2 warnings** (Laura crossing its escarpment;
design box above preferred target). The production preview was inspected beside
the official introductory image. The large bays,headland and country contexts remain.
No source evidence justifies changing the recorded fixed-rule alternatives here.

The actual repository16-step polygons form a valid exact coverage: **zero uncovered
land,zero mask area outside land,and no overlapping interiors**. Both islands retain
their old geometry. This verifies the converter's sampled geometry,not an analytic
claim about every point of a continuous curve or a canonical border. The rejected
[independent fit](curve-simplification-review.md) remains documented as history.

## Normal export and limits

Normal `python -I tools/world/build.py` completes in65.6s with no converter warnings;
all58 anchors export and the staging hash matches the SVG. No `--apply` is used.
The raster origin,size and numbered-atlas projection remain identical. The atlas
changes only its embedded terrain image: all58 number groups,16 labels and32 open
rows retain their positions. All15 in-mask stroked text boxes and the Ulgracia callout
endpoint remain inside the updated masks; label/bubble clearances are unchanged.

- Site,road and structure-exclusion rasters are pixel-identical. Runtime sites.json
  is byte-identical,including its34 plate entries.
- 55 of58 sampled site discs retain identical heights. Filtwood changes by at most
  0.0625,Sainte-Malukshure0.25 and one Amrita cell0.0625 blocks. These are staged
  raster readings,not runtime fit acceptance.
- All21 routes retain their horizontal points,bridge flags and metadata. Thirteen
  exported height profiles match; eight change by at most0.32 blocks. Maximum grade
  remains0.5 within floating epsilon.
- Height changes899,865 cells (median nonzero delta0.1875,max11.5 blocks),biome15,533
  and ruggedness71,191. These include derived coast/terrain effects; no claim is made
  that only a tiny coastal pixel strip changes.
- Water changes12 cells near the southern river outlets: seven level changes and
  five newly wet cells. Authored river/lake geometry and source attributes are unchanged;
  the resulting stepped levels are not claimed byte-identical.

No Minecraft chunks,inhabited-world transition,pack apply,main merge or deployment
is tested or delivered. The currentR43 painting predates these curves and needs a
native mask/source refresh before being called current again; its original pixels
and58 art pairs remain preserved. The three historical painting reviews still exist.
The225-row ledger/14 direct LN,129-entry inventory/32 follow-ups and source/era/binding
questions remain open. This change does not complete the full faithful-world goal.

Repository gate: validation and472 tests pass,26 skipped,zero failures (62.509s test tier). All58 exported anchor positions,including sampled walking levels,and anchors.toml bytes match the baseline. These are offline/staging checks,not runtime acceptance.
