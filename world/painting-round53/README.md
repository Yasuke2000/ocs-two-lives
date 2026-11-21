# Current painted continent — round53

Round58 [current-source equivalence audit](current-source-equivalence-r58.json): the current source1b9e151a includes inert Malukshure and Dwargon East/West proposals. Its complete active XML tree and normal height export match the original painting source8c24a349. All58 sites/projections and all SVG/PNG bytes are retained. The original provenance below remains unchanged; the new cape and city proposals are not active or painted. The normal export was checked in the map worktree,not regenerated in this painting worktree.

Round56 [current-source equivalence audit](current-source-equivalence-r56.json): the current source e886217d adds only an inert Malukshure capital/cape alternative. Its complete active XML tree and normal height export match the original painting source8c24a349. All58 sites/projections and all SVG/PNG bytes are retained. The original provenance below remains unchanged; the new cape is not active or painted. The normal export was checked in the map worktree,not regenerated in this painting worktree.

Source-register erratum (round54): the [current ledger review](../../docs/research/tensura-world-2026-11-19/empire-source-review-r54.md) restores unique claim keys and records233 unique entries. Original WN13-005/006 keep their earlier meanings; trade/cavern records are007/008. The original art,terrain source8c24a349,projections and numerical lighting provenance below remain unchanged.

[Marked atlas](atlas.png) · [clean continent](continent.png) · [editable native composition](continent.svg) · [provenance](provenance.json) · [height samples](relief-samples.json) · [geometry/layout audit](presentation-audit.json) · [official comparison](comparison.md).

This presentation follows production source `8c24a34906638713849bd3b82e32a362ef75c0f65b77e1175b6a0b1e97a1d2d6`, map commit `d02956c`. The [round52 correction](../dwargon-approach-fix.md) graded the Dwargon access roads to the fixed template. The current native composition now includes both actual foothill/forecourt masks and a local lighting layer derived from the changed height surface.

This is a deterministic **SVG presentation update**, not a new generated raster painting. Original R38 and R43 texture PNGs remain byte-identical, with their [historical generation provenance](../painting-round43/provenance.json) and [prompt](../painting-round43/prompt.json). The current source masks define the land/sea, three coasts, nine lakes, eight rivers with source widths, 21 roads and two habitat highlights. No copyrighted anime, official or fan-map image was supplied as an image-generation input.

## Local relief layer

The layer samples the normal build for current source8c24a349 and the retained round51 baselinecb07cce7. Baseline can be reproduced by checking out map commitf118b6e and running the normal converter to an isolated output directory; current input comes from the normald02956c build. No apply is required. Input height hashes, fixed world frame, lighting rule, source-mask hashes and sampling bounds are recorded in provenance.json.

At 16-block cell centres,666 positive height-change samples produce a quantized light/dark SVG overlay from the delta-surface gradient. Alpha uses1/64 increments,at most0.15625. Exact source polygons,48-block mask stroke and8-block feather sigma govern the local patch. Both source masks and all numerical height samples are verified. The rendered composition changes1,387 pixels compared with R50,with maximum per-channel delta32/255. Every changed pixel centre lies within96 blocks of the union of the two relief shapes. The sea and the rest of the continent retain their previous composition pixels.

The patch illustrates the interpreted graded foothill. It is not a new canyon,capital,tunnel,road route or canonical elevation claim. Painted mountain ridges,tree canopies,soil and bank strokes elsewhere remain illustrative rather than an exact heightmap. Runtime placement still supplies Dwargon's lower tunnel; the outer mountain surface is roof rock.

## Labels and painting-to-SVG review

All58 world positions and projections pass; every non-image atlas element is retained. Leader lines remain behind number bubbles with minimum centre spacing32.47px. Actual Chrome bounds confirm that16 context names clear padded number bubbles;15 non-callout text boxes lie inside current sampled region masks. Ulgracia's callout ends inside U. All32 open-inventory rows fit the separate panel; the129-entry source inventory and its uncertainty classifications are preserved.

The local before/after detail,current whole composition,marked atlas and current terrain view were visually inspected alongside the cached official introductory map. The softened foothill shading fits the existing original art; no further production SVG change was justified by this review. Existing coastline/projection departures remain disclosed in regions.md/C12. The initial era stays immediately after Kijin naming; later chapter maps supply enduring geography only.

The production SVG and current checker/terrain outputs remain byte-identical to d02956c during round53. The retained round52 default checker result is0errors,all56 relations,same2 warnings. Normal terrain export source and height hashes are verified; the painting worktree's ignored older build directory is not claimed as a fresh export. No converter rerun is necessary for this presentation change.

Ledger231 records,including14 directly read LN claims;129 inventory entries/32 follow-ups and58 original art pairs. Full source completeness,fixed-rule conflicts,initial-era implementation,structure fit and local runtime acceptance remain open. No new terrain geometry,extra site ID,Minecraft chunk generation,main merge,terrain apply or deployment.

Repository validation and472 tests pass on both feature branches (26 skips,zero failures): painting64.352s,map-pointer64.333s. Final native lighting/geometry/browser audits pass;no changed JavaScript or in-game test run.

The round54 source-register backport passes validation and472 tests (26 skips,zero failures,62.483s). Art renders,native composition,terrain source and numerical lighting inputs remain unchanged.
