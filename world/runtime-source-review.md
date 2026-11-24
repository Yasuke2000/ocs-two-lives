# Current technical-world source handoff

24 November 2026. Read-only comparison with [own-world-switch `a944e35a`](https://github.com/Yasuke2000/ocs-two-lives/commit/a944e35ae6199769251112c11c4f4152c9b6c397). The branch now includes local-server/map-rendering helpers,but still uses the earlier drawing. This is a source-alignment audit,not a new game test. No technical code,world files,server process or deployment is changed here.

| Bundle | Source SHA256 | Normal box |
| --- | --- | --- |
| Technical applied index | `b48666e9a6785a5900bb694525c38487fea2c9ade1171df62d843589c671c661` | 12800x10752 |
| Current approved drawing and normal export | `36c77b45ee33edb37d737e062327ae936eeae68eeb6904d5054b4325196a8627` | 13824x11264 |

All **11 of11 core runtime files differ**: biome.png, canon_map.txt, exclude.png, height.png, index.json, road.png, roads.json, rugged.png, sites.json, sites.png, water.png. After the larger-island and coastal adoption,the earlier six-difference comparison is obsolete. Raster arrays must be regenerated together with the matching index,box,grid,roads and registrations;copying only a drawing or selected PNGs cannot establish alignment. [Exact hashes and records](runtime-source-review.json).

## Five changed placement records

| Site | Technical x,y,z | Current x,y,z | Current meaning |
| --- | --- | --- | --- |
| `filtwood` | -1200,65,2750 | -1050,74,600 | Owner-approved source placement |
| `sainte_malukshure` | -100,69,2000 | -2320,64,1645 | Independent coastal country pin;gameplay O |
| `el_dorado` | -4300,73,3000 | -4900,70,3202 | Owner-approved source placement |
| `el_dorado_volcano` | -3900,197,3200 | -4359,222,3473 | Owner-approved source placement |
| `frost_palace` | -1530,71,-3680 | -2130,75,-3799 | Owner-approved source placement |

The other **53 of58 full index records are exact**. Identities,radii and interpretation limits remain. The technical branch has22 roads;the current drawing has24. **18 existing road exports match**;changed routes are el_dorado_volcanic_way, tempest_dwargon, frost_palace_forecourt, tempest_blumund. Added routes: filtwood_jura_trail, malukshure_coastal_approach. Tempest's two kinds are now trail;the island routes follow the selected enlarged landmasses.

**Practical consequence:** both current El Dorado positions read open sea on the applied technical grid but X on the selected current grid. The new drawing cannot be tested faithfully by changing only its markers. The inland palace reads I at both old and new coordinates,so a correct region letter alone would miss that displacement.

## Registration and test scope

The technical generator chooses the applied own-world grid when present. A region-letter check alone can accept an old or wrong coordinate within the same broad mask. The JSON records all five actual positions,technical canonical anchors,retained authoring legacy anchors,current generated anchors and grid letters at each. Verify **x,y,z and exact source**,alongside region and terrain;do not clear the current Filtwood U/J and Sainte H/O dependency by selecting a different grid without adopting generated coordinates.

The exporter contains58index records,34flat preparations,4carves and20unplated markers. `compare_design.py` at the pinned technical commit selects only `plated` entries by default: **38 windows**,not all58. It omits the20unplated pins,including Filtwood and Sainte;the five changed sites therefore need explicit coordinate/region/source verification. Its carve windows do not receive the same flat-plate gate,and village plate results are reported without that gate. Ground-window success is not underground-room,fluid,actual-structure,all-location or early-era acceptance.

The technical HANDOFF reports `/ttlsite check all`38/38 and ground deviations0-2blocks at36/38,with three initial worldgen defects fixed. Those are the technical branch's reports on sourceb48666e9;this audit does not independently rerun them or extend them to source36c77b45. Current authoring checks remain0map errors/56relations/2warnings,normal91.6seconds withoutskipcheck,and13passing finite lake cases. The authoring repository gate still has3legacy-registration test failures plus validation. No current Minecraft acceptance is proven.

## Generation extent and existing chunks

The current half-open normal box is **x[-7680,6144),z[-6144,5120)**:864by704chunk cells,608256in the rectangle. The technical local-world guide still documents a radius400chunk footprint centred(-256,-256). Under that guide's chunk-radius model,its square is x/z[-6656,6144). It contains the current native land,but **misses1024blocks of the new western output/ocean margin**. Do not label that old footprint a complete generation of the new box.

Geometrically,an enclosing square centred **(-768,-512)** with half-width **6912blocks =432chunks** contains the full new box. This is a bounds calculation,not an executed or runtime-verified command. Claude must confirm actual command radius,edge inclusion,seed and storage budget before choosing the generation command. Preserve generated worlds under distinct names:existing chunks do not repaint when the SVG or rasters change. The existing import manifest also needs the current source/seed/artifact hashes,not an old rendering or timestamp.

## Ordered technical acceptance

1. Adopt current `world/map.svg` and its matching generated bundle in Claude's integration workflow;retain the selected larger islands,coastal O binding,Filtwood J and early-trail arrival relation. Match the source hash,box,all11core inputs,all58index records and24road records. Reconcile canonical generated anchors as one source-aligned change.
2. Coordinate [Amrita below Clayman's castle](amrita-approved.md):parent/vertical geometry,carve support,Jistav road destination and public-shaft template. Retire the eastern reservation without losing the named underground location. Depth,extent and initial access are not established by the owner choice;the failed marker-only trial stays inactive.
3. Run the combined offline gate,then use a fresh isolated local world with the correct seed/source. Verify the38prepared/carved locations plus explicit20unplated registrations,especially all five changed records. Check actual structures,underground rock/fluids,road/bridge transitions,full generation extent and initial-era state. Resolve the technical WIP quest-distance and Dwargon-carve checks.
4. Follow the existing main/reset/import/deploy gate only after technical acceptance and the scheduled reset authorization. This creative branch does not merge the switch branch,apply data,start a server,generate chunks or deploy.

[Owner-approved current map](approved-islands-coast.md) Ã‚Â· [current delivery](DELIVERY.md) Ã‚Â· [historical source review](https://github.com/Yasuke2000/ocs-two-lives/blob/7599d01f93380dc9cb9205fef1459dd1ca112c89/world/runtime-source-review.md). No owner geography choice is pending;technical and source-evidence requirements remain open.

Verification: fresh required `bash tools/check.sh` ran494tests in74.539seconds,26skipped,the same3legacy-registration failures plus validation;0changedJavaScript. Source,map/art/ledger and all14normal artifact hashes are retained. No new SVG edit,checker/preview,converter or Minecraft run is claimed for this documentation-only audit.
