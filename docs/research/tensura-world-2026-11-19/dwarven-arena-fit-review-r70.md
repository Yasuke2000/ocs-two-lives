# Dwarven arena: separate an enclosed rear shell from a flat plaza — round70

[Original plan and section](../../../world/dwarven-arena-fit-review.png) · [editable SVG](../../../world/dwarven-arena-fit-review.svg) · [decoded audit](../../../world/dwarven-arena-fit-review.json)

The R62 rectangular survey identified height variation east of the arena anchor. This follow-up decodes the actual existing NBT instead of enlarging a preparation disc merely to contain an offset rectangle. **Retain r58 for now.** This resolves the rectangle-only reason to enlarge it; it does not prove final interior walkability or placement.

## Model and designed surface

The 75 ×26 ×51 saved model has anchor(3,1,25). At the unchanged map centre(500,-1180),first-air75,its corner is(497,74,-1205). It has64,466 defined entries and25,856 non-air blocks in3,343 columns. The imported server model is an adaptation of the Tensura mod's arena,not evidence for an anime hall's surveyed location or architecture. See [existing provenance and owner adaptation](../../../design/lore/dwarven_arena.md) and [blueprint](../../../blueprints/dwarven_arena.py). No copyrighted anime frame or map is copied here.

810 occupied columns lie outside r58. Their designed Catmull-Rom first-air ranges74.958239..83.360323;561 differ from the entrance's75 by more than half a block. But the forecourt54 columns,entrance15,pit1476 and stair-context105 are all exactly75 with both bilinear andCatmull-Rom sampling. The raised dais-context box665 columns has first-air74.958239..77.443289. These are bounding contexts,not claims that every column is a walkable floor: pillars,decorations,walls and stairs remain.

The full occupied footprint would require geometric radius76,or84 to contain all16 Catmull-Rom neighbours. That is a **hypothetical whole-footprint flat-platform bound**,not a demonstrated need. All3,343 occupied columns have natural designed first-air at or below the highest solid column top and above the lowest solid block. The minimum clearance above the lowest solid block is0.958239. This rejects a simple roof-burial or entirely unsupported-column diagnosis in the sampled designed surface;it does not test side exposure,undefined cells,noise,caves or full collision geometry.

Every occupied column has the exported SITE exclusion bit,and none has water. The site-index raster itself is0 in860 columns and11 in2483:an exclusion buffer is not flat terrain,an interior floor,or proof that every runtime feature is suppressed. The rear shell extends into an interpreted mountain collar. Its solid and explicitly defined air cells,including the rising dais,are part of the model.

## Check real standing points without inventing a route

All seven blueprint-declared arena spawn positions have a defined non-air floor and three explicitly defined air blocks at feet/head. Their world feet are y75. This is a decoded-model headroom check,not a runtime teleport,collision,stairs or whole-interior path test. The section shows the true imported solid/air pattern;it does not replace complicated dais decorations with an imagined straight walkable stair.

The existing placement interface in life/builds.js reads terrain,places the model's defined blocks,handles foundations and clear-above fitting,and places it again. It is read-only interface evidence here;it was not executed. The legacy arena registry still says ground=survey beside dwarf_village. Any own-world technical switch must reconcile that existing behaviour with the fixed map anchor. No actual target-world placement is claimed.

## Fidelity and remaining scope

Do not flatten the complete rear rectangle solely to match the entrance level. Keep the organic collar while the technical placement/whole-interior checks remain open. This study adds no canonical geography. Exact map coordinates,radius,materials and architecture are our interpretation;the arena is a server venue. The selected world instant stays S1E10 immediately after Kijin naming,and the venue must not imply a canonical later event or resident.

Current source90ee15b1,all existing normal exports,the production SVG and R69 painted atlas are unchanged. No converter rerun,terrain application,chunk generation,runtime/protected-path/tool edit,main merge or deployment. The ledger adds DES-ARENA-070:262 unique records(204 thematic/design/reference plus58 coordinate interpretations),still14 directly read printed-LN and6 separately classified author-side-story claims. The132-entry inventory and41 physical follow-ups remain open,along with broader source,era,fixed-rule,fit and runtime obligations.

Repository validation and472 tests pass(26 skipped,zero failures,62.737s);zero changed JavaScript. The original plan/section was visually inspected. Independent source/height/input-hash,lossless-footprint,unique-ledger-ID and protected-path checks pass. No production SVG edit occurred,so its existing passing checker/export remain the unchanged inputs rather than a newly executed terrain build.
