# El Dorado eastern lake-like basin — round 80

**R81 follow-up:** [the published current painting](https://github.com/Yasuke2000/ocs-two-lives/blob/96b3972/world/painting-round81/README.md) includes this exact lake and local bank change. Earlier pending statements below record the R80 handoff and are superseded for painting integration only.

[Original before/after study](el-dorado-lake-study.png) · [editable study](el-dorado-lake-study.svg) · [terrain audit](el-dorado-lake-audit.json) · [current terrain atlas](atlas.png)

## Evidence and interpretation

The [official introductory illustration](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) visibly shows an unnamed lake-like inland waterbody east of the volcanic cone on the southwestern island. The previous nine-lake source omitted this cue. **MAP-ELD-LAKE-080 is canon-implied visual geography**, not a named lake or a surveyed water boundary. The cached original and current source previews were directly compared; the official image’s SHA is d306892d8ca705742628ec75c2163082ab40da1ef4b1e691903a5926bc4a3f7a. No copyrighted image is embedded in the original study and no exact source outline is traced.

The active addition is an original 26-vertex shore, 274×138 blocks, 26764.5 blocks², in bounds x-3651..-3377, z3054..3192. Water first-air 68, depth 5, position, size, shore and closed drainage are **our interpretation**. No source-derived lake name, capital association, outlet, artificial origin or dated S1E10 water condition is claimed. No extra river or numbered reservation is added.

This interpreted basin is 157.32 blocks inside the unchanged island coast, 263.43 from the nearest road centreline and 256.77 from the nearest reserved site edge. It does not overlap the native volcano polygon. Exact physical margins are server measurements; the source image does not supply them. El Dorado’s compressed island scale remains C12’s explicit adaptation.

## Source and export checks

The required default checker ran immediately after the SVG edit:zero errors, 56/56 relations and the same two existing warnings(Laura river/escarpment; preferred design-box size). The normal staging build completes in 65.6s with no converter warnings. Current source/index SHA is `9fd0c5fba52560dc035fc1552a6e364b087931174e20503a7677de942daa6f9e`. There are four coasts, ten lakes, eight rivers, 21 roads and 58 registered sites; every previous parsed shape and site attribute remains unchanged.

All site/anchor/road JSON/TOML and site, road, exclusion rasters are byte-identical to source e8f17470. Water changes 1668 four-block cells from dry 0 to encoded 132(level 68+64), including all 1665 strictly interior source-polygon sample centres; the remaining three centres lie on the polygon boundary. All previous water is retained. Biome changes 1668 cells, roughness 2045 and height 2123; all changed centres lie inside El Dorado. Height differences are -6.9375..+7.375 blocks and remain within 14.09 blocks of the lake. These are normal-export measurements rather than runtime simulation.

The immediate four-neighbour dry rim samples are first-air 70 throughout, two blocks above the authored water surface. That checks the local raster bank; it is not a full noise/density/water-placement or in-game swimming acceptance test. No apply, chunk generation, main merge or deployment.

## Presentation and coverage

The terrain atlas is refreshed from the exact new normal preview. Its 58 numbered markers, 16 context names and 41 open rows retain layout; only the embedded terrain and inventory caption 133→134 change. All 58 site coordinates/radii/kinds remain, so per-place numeric art registration is unchanged. **R78’s painted atlas predates this lake and requires explicit integration.** Earlier R78 current-source statements are historical for this real water change.

The inventory now has 134 records: 133 previous entries plus this official-image water cue. It is terrain-present; the 41 existing physical follow-ups remain open. No missing named settlement is closed. The ledger has 280 unique records (222 thematic/design/reference + 58 coordinate interpretations); 14 directly read printed-LN and 6 author-side-story claims are unchanged.

The source hierarchy, remaining wiki/source/initial-era questions, fixed-rule alternatives and full faithful-world objective stay in scope. Technical conversion and placement remain Claude’s handoff. This is one illustrated landscape omission corrected, not a completed Minecraft world.

## Final verification

Validation and 472 tests pass (26 skipped, zero failures, 62.581s). Independent checks confirm 280 unique evidence IDs,134 inventory rows with all133 prior records unchanged,14 printed-LN and6 author-side-story claims,all previous parsed geometry and58 site attributes retained,unchanged road/site/anchor exports and local raster deltas. The atlas embeds the exact new normal-preview PNG;its other XML elements match the prior atlas apart from the 133-to-134 inventory caption. Final source preview,original study and terrain atlas were visually compared with the official image.

The configured depth5 is nominal. Exported wet-bed first-air ranges63..66.6875,so sampled water depths range1.3125..5 blocks before runtime noise/placement. The local dry four-neighbour rim remains70 throughout. This preserves natural shallows without claiming uniform depth or in-game containment acceptance.
