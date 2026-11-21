# Dwargon road and forecourt connection — round52

[Before/after section](dwargon-approach-fix.png) · [editable vector](dwargon-approach-fix.svg) · [measured audit](dwargon-approach-fix.json) · [current terrain atlas](atlas.png) · [original finding](dwargon-approach-study.md).

The production SVG now includes a40-node rounded foothill (`dwargon-gate-apron`, peak146, dome, rugged0) and a32-node low forecourt shoulder (`dwargon-forecourt-shoulder`, top146, rolling, rugged0). Their exact500×540 and280×240 outlines and elevations are **our interpretation** for the existing fixed blueprint fit. They follow the open-foothill/cavern context in WN13-006 and WN13-008 without claiming a measured canon ramp. The early post-Kijin snapshot and C18 road-development qualifications remain.

The source SHA is `8c24a34906638713849bd3b82e32a362ef75c0f65b77e1175b6a0b1e97a1d2d6`. Only these two relief features were added. All existing elements,58 site attributes,21 route geometries,coasts,regions,waters,forests and biome polygons remain identical. No protected runtime/tool path or fixed blueprint base changes. Default checker passes:0errors,all56 relations,same2 warnings (Laura river/escarpment crossing and preferred design-box size).

## Connection now measured

The main road endpoint at(0,-1495) rises from profile71.33 to146. The village-branch start at(40,-1500) rises from73.36 to146. The fixed Dwargon template base remains142, giving first-air146 on its approach road. Every sampled native surface value at x-3/0/3 and x37/40/43, z-1503..-1495 is exactly146, so both centre-lines and their sampled width meet the southern template road elevation across the former gap. This resolves the specific exported interface found in round51; it does not test placed voxels, repairs or live walkability.

Only two road height profiles change:72 main-road points by at most75.09 blocks and63 village-branch points by at most72.64. All other19 profiles,all horizontal coordinates,flags and non-point metadata remain identical. Maximum exported grade is0.5000000000000491, within float epsilon of0.5. Outside the template box, maximum profile-versus-bilinear-surface difference improves from0.3496875 to0.0603125 on the main road and from0.6475 to0.1253125 on the village branch. The source centre-lines have no mutual geometric intersection; the comparison does not invent one or replace a full network connectivity test.

## Terrain and reservation audit

The normal build finishes in65.2s without converter warnings and matches the selected external trial byte-for-byte for all checked rasters,roads,sites and anchors. Height changes in9,893 four-block cells, at most75.3125 blocks, within sampled cell-centre bounds x-262..246,z-1686..-1214. Water,biome,road,site,exclusion and ruggedness rasters are pixel-identical. All58 exported site records, generated anchor tuples and sites.json remain byte-identical; all57 other site discs keep their height samples. Dwargon's disc has2,150 changed cells in its exterior approach.

All3,179 authored roof-column surface samples remain identical to the baseline. Designed cover stays minimum6.0,median14.171875,maximum48 blocks; none below six. The exterior surface over the gate remains roof rock, rather than a new walking floor. The template supplies the lower entrance/cavern when actually placed. Pin heights remain exterior samples as documented in round51; no NPC height fix is inferred.

The first single rolling-hill trial was rejected because its rounded-coordinate exported grade reached0.5121475. A dome-only trial fixed the main road but left the village-branch start at143.6; the small shoulder improves that connection. These trials are recorded as implementation evidence, not additional canonical landforms.

## Visual/source review and limits

The fresh production checker preview was viewed beside the cached official introductory illustration. Coastline,political masks and known C12 projection differences are unchanged; this is a local interpreted foothill fit. Current terrain atlas, standalone preview and before/after section are refreshed. Atlas changes only its embedded terrain image;58 marker groups,16 context names,32 open rows,projection and existing text clearances remain. No copyrighted reference art is copied into the repository.

R50 painting preserves the same coast/water/road vectors and58 positions but predates this relief adjustment; its local landform presentation needs review before it is described as fully current-source. Earlier painting/SVG rounds and original textures remain historical. No new raster generation occurs here.

Ledger231 records,including14 directly read LN claims;129 inventory entries/32 follow-ups and58 original art pairs. No extra East/West city position or tunnel is invented. Full source completeness,fixed-rule/era/coverage/build-fit/runtime obligations remain. No terrain apply,Minecraft chunk generation,main merge or deployment. Local placement/repair/era and walkability verification belong to the technical handoff.

Repository validation and472 tests pass on final source8c24a349 (26 skips,zero failures,62.421s test tier); no changed JavaScript files. Local Minecraft placement/repair/era and walkability tests remain pending.
