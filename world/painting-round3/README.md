# Third painting and SVG review

[Marked atlas: all58 reservations](atlas.png) · [clean composition](continent.png) · [editable composition](continent.svg) · [registration audit](presentation-audit.json).

This third review uses production map commit `60297bd`, normalized SVG SHA-256 `2518f19c20593d85c13581c61b58f9a25125f7a79ce94152119ec3464524360b`. It follows the first painting in [PR88](https://github.com/Yasuke2000/ocs-two-lives/pull/88), the resulting [three forest-boundary refinements](../forest-edge-review.md), and the second painting in [PR90](https://github.com/Yasuke2000/ocs-two-lives/pull/90). The intervening [Amrita source review](../amrita-placement-review.md) qualifies the mandatory eastern reservation and draws an inert castle-linked access alternative. The atlas key now preserves that distinction.

## Painting findings and production decision

| Finding from second painting / third trial | Third presentation | Production SVG decision |
| --- | --- | --- |
| Southern Fulbrosia appeared to have a long high chain extending to the coast. | Shorten the pictorial massif around its existing footprint and lower its coastal continuation. | Retain current relief; no inspected source requires the invented extra chain. |
| Northern Imperial plains and the old Dragon City area had excessive scattered woodland. | Open the plains while retaining the Jistav woodland and ancient Jura core. | Retain the already reviewed forest polygons; brush-stroke canopies are not measured masks. |
| Some small lake surroundings had faint rectangular texture seams. | Blend the ground texture. | Retain all eight lake polygons and their hydraulic metadata. |
| The first third-round trial invented a stream from the Imperial holy peak to the Jistav lake. | Remove all painted thin river strokes, then overlay the eight exact source polylines at source widths. | Reject the invented tributary. Keep current river geometry. |
| Amrita's separate marker could read as a canonical independent surface entrance. | Key49 explicitly says **Amrita game reservation (C07)**. | Retain the constrained marker plus the inert source alternative pending access/nesting reconciliation. |

The production review therefore **retains the current active SVG**, rather than converting artistic errors into new geography. No terrain polygons,58 site attributes, road metadata or hydraulic levels change in this delivery. Three painting/SVG review passes are now documented; source completeness, owner approval and in-game acceptance remain separate unfinished requirements.

## Registration and evidence limits

The two guides derive from the current checker preview and normal terrain build. World frame is(-8064,-5632,16128,10752),1536x1024 pixels, north up. Native composition clips land to the three source coast polygons and overlays eight lake polygons, eight river centrelines at their source widths, and21 road polylines. [Site registration](site-registration.json) retains all58 world anchors, their pixel projections and displaced number bubbles. Native vectors and all58 marker projections pass the recorded audit.

Painted lake-bank shading, canopy edges and perspective ridge strokes remain pictorial: the audit verifies the native overlays, not every underlying raster pixel. The northern massif's exaggerated pictorial peaks and the frozen island's white wash do not prescribe elevations or snow coverage. Roads are required terrain reservations and do not by themselves establish completed post-Kijin infrastructure. Exact biome boundaries and compressed coast shapes remain authored interpretations as recorded in [regions](../regions.md) and [comparison](../comparison.md).

The clean painting, marked atlas, checker/terrain guides and external official base illustration were visually compared. The official map supports broad context; it does not survey the server's exact coast, elevation or canopy. [Official interactive map](https://www.ten-sura.com/map) · [official base illustration](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp). Copyrighted references remain external links and local research-cache files outside the repo. Only original project artwork/guides were image-generation inputs.

[Exact prompts and selected output](prompt.json) record the built-in `image_gen.imagegen` workflow, including the rejected river-bearing intermediate. The selected raw output is retained as `paint-r25.png`; lossless PNG packaging was verified to preserve every original RGB pixel. [Provenance](provenance.json) records input/output hashes and the review decision.

Current checker: zero errors, all56 relations pass, the same two disclosed warnings (Laura waterfall/escarpment crossing and design-box height). No new converter run is needed for unchanged production bytes; the checked56.3s normal build at the recorded source hash remains the terrain evidence. Repository validation and462 tests pass (26 skips,zero failures,44.056s test tier). No runtime apply, Minecraft chunks, actual merge or deployment.
