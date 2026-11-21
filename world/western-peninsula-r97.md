# Western peninsula silhouette correction - R97

[Current terrain atlas](atlas.png) · [original before/after](western-peninsula-r97.png) · [editable comparison](western-peninsula-r97.svg) · [independent audit](western-peninsula-r97.json) · [58-site projection](atlas-registration-r97.json)

The [official introductory illustration](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) shows the unnamed western lobe farther west than the northwestern headland. Our previous outline reversed that relationship. The privately cached original was visually reread; MAP-WES-097 is canon-implied illustrated geography, not a surveyed coordinate claim. The interactive-page reader exceeded16MiB; no unread page data supplies evidence. [Source/hash record](../docs/research/tensura-world-2026-11-19/western-peninsula-source-r97.json).

## Final coast and the rejected wider trial

The active map extends the western lobe and shortens the northwestern headland, changing six existing outlines: mainland coast, four biome outlines and the V gameplay mask. No detached island or site moves. Exact coordinates,scale,biomes and administrative V coverage are our interpretation (DES-WES-097), not verified sovereignty. Parsed land addition207092.69 blocks² and removal140651.52 blocks² are recorded separately. Native coast/biome/region polygons are valid and regional land coverage is exact.

The first wider trial was10443x6250 with design13312x10752. It passed the checker hard11000-width limit but failed the repository's stricter `test_starter_map_has_one_site_per_anchor_and_passes`, which requires width<=10000. Its original mainland path is retained in an inactive C12 comment in map.svg. No test or tool rule was changed. The final compact silhouette preserves the illustrated ordering within9983x6250, retaining the previous12800x10752 design box and default1200-block ocean margin. This is a disclosed scale adaptation, not a claim of exact source proportions.

Final default checker:0errors,56/56relations,2prior warnings (Laura river/escarpment and preferred design-box size). No new width warning remains. C12 and the other source conflicts stay open. Fixed58 site XML attributes,22 road geometries,lakes,rivers,forests,hills,mountains,ridges and detached coasts remain identical.

## Terrain and site handoff

Normal export66.5s. Changed height/biome/ruggedness is bounded in the far west; unchanged-box water,road,site and exclusion rasters are byte-identical to the previous export. The Heaven Tower preparation ground changes71to73; every sampled radius84 disc cell changes+2blocks, while the other57 site discs retain their exact height samples. Staged anchor/site files differ only in that ground value. Keep those generated records together when Claude applies the map.

Road profiles: western_desert_caravan: 46 changed height samples, max delta2.00, grade0.382500. All other profiles are unchanged. These are designed-raster checks, not actual structure placement,collision or Minecraft walking tests. No live anchors,technical implementation,terrain application,chunks,merge or deployment changed.

The atlas embeds the exact normal preview and retains58 numeric markers,19 context names and42 open rows. Browser collision checks and all58 actual anchor-dot projections pass; maximum projection error0.000159px. The official image,final checker preview,terrain atlas and original before/after comparison were visually inspected. R95 painting predates this western coast and requires alignment before being described as current geometry.

Ledger304 unique records (246 thematic/design/reference plus58 coordinate records). Inventory138 and42 physical follow-ups are unchanged. The coast correction does not locate a missing country or establish an initial building,resident or later event.

Repository validation and 472 tests pass (26 skipped, zero failures, 63.383s); zero changed JavaScript. The final atlas differs in 86,302 pixels, bounded to x188..493/y684..1304 in its western portion. The rejected wider trial is recorded above; only the final compact source is published as active geometry.
