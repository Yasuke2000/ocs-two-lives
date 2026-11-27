# Sacred Mountain: support the existing tapered perimeter — round68

[Original plan and section](sacred-mountain-fit-review.png) · [editable SVG](sacred-mountain-fit-review.svg) · [before/after audit](sacred-mountain-fit-review.json) · [current terrain atlas](atlas.png)

Only the active Sacred Mountain preparation radius changes: **80 to95**,at unchanged x/z(-3900,-1600). The normal converter's median selection changes its first-air level **179 to175** and fade40 to48. These are authored Minecraft preparation values,not canonical dimensions or a newly discovered mountain height. The existing selected summit/stair source relationships remain unchanged. The current initial story instant stays just after Kijin naming,S1E10.

## Actual model and reason for the change

Three existing NBT slabs decode to81 ×57 ×81,with83,337 defined entries and80,912 non-air blocks. All6,561 x/z columns contain model material. Unlike the empty Coleus rectangle corners,the Sacred Mountain model has a terrain lip around all320 perimeter columns,with a defined ground skin at local y3. Its local anchor is(40,4,76),so the saved box lies mostly north of the placement anchor. The model builds its own rock shoulders,two flights and threshold.

At r80,the perimeter's Catmull-Rom designed first air ranges176.479428..182.291726 against target179. Twenty-eight perimeter columns differ by over half a block;the maximum mismatch is3.291726. Forty perimeter centres lie outside r80. This is an actual saved perimeter-interface question,not merely a warning about unused rectangular padding.

The occupied box needs radius86 geometrically. Its sixteen-neighbour height-sampling stencil needs95. R68 therefore chooses95 rather than flattening the whole113 ×113 margin rectangle. In the normal export,all6,561 occupied column centres,all320 perimeter centres and all six functional support boxes are **exactly175** with Catmull-Rom and bilinear sampling. The model's15-block two-flight rise is retained:56 defined centre-floor positions now span world y174..189. The last two reach the intentionally closed threshold,not an open passage. No walkability or generated-world clearance is claimed.

The model's highest saved non-air block moves225 to221 solely because the placement base falls four blocks. Its architecture,internal heights and NBT bytes are unchanged. Legacy registries still use their old-world survey mode;the technical own-world handoff must use the intended fixed centre and exported level. No runtime registry,structure or tool code is edited here.

## Export consequences

- Every one of58 x/z centres is unchanged. The other57 site records are identical;only Sacred Mountain's radius,first-air and fade differ. Generated anchors change its y accordingly.
- All21 road centrelines and bridge flags remain. Only sacred_mountain_trail's exported profile changes:60 points,at most2.58 blocks. The rounded-export maximum grade remains0.5 within floating epsilon.
- Height changes in4,483 four-block cells,from-29.75 to+51.0625 blocks. This includes the surrounding shoulder and graded approach;it is **not** a claim that only the old three-block edge mismatch changes. Changed height-pixel bounds are x-4060..-3688,z-1744..-1400.
- Biome changes1,291 cells,ruggedness2,586,site classification516 and structure exclusion792. Water and horizontal road rasters are byte-identical. Complete raster deltas and unchanged files are in the audit.
- The current native coast/22-region partition has zero uncovered land,zero masks outside land and zero positive-area pair overlaps. Those layers are unchanged by this edit. The earlier R44 seams were already resolved by R49;no region repair is newly claimed.

The default checker passes with0 errors,all56 relations and the same2 warnings (Laura river/escarpment and preferred design-box size). Normal conversion completes in66.6s with no converter warnings. The checker preview was visually inspected beside the cached official base;the major continental relationships,scale compromises and fixed-rule alternatives remain as documented.

The terrain preview and numbered terrain atlas are refreshed;the atlas's embedded terrain image changes. Its42/54 legend entries now explicitly identify Sainte as a game pin(C14) and Frost Palace as a coastal reservation(C22),matching the existing source qualifications. All58 marker/legend positions,16 context labels and41 open rows retain their layout. The R64 painted atlas is **historical for this new terrain source**:its underlying landscape follows c2f806a9 and needs an explicit native height-lighting update before being called current. Earlier art files remain untouched. Painting integration is the next work item,not silently claimed complete.

## Remaining scope

The support diagram and exact values are original analysis,DES-SACFIT-068. The Sacred Mountain SITE radius summary is updated in place. Ledger261 unique(203 thematic/design/reference +58 coordinate interpretations);14 directly read printed-LN and6 separately classified author-side-story claims remain. Inventory132/41 physical follow-ups is unchanged. Source/era/fixed-rule decisions,other fit cases,missing locations and local Minecraft acceptance remain open. No main merge,terrain application,chunk generation,protected edit or deployment occurs.

Repository validation and472 tests pass (26 skipped,zero failures,62.335s);zero changed JavaScript files. The initial stale-sites check was resolved by the existing sites_from_builds generator;its only generated change is Sacred Mountain r80 to95. No tools code was changed. The two qualified legend labels fit within the atlas in browser measurements. The source checker and normal export pass;in-game placement and painting integration remain untested/pending.
