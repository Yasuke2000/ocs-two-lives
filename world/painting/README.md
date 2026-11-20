# Current-geometry continent painting — round 19

[Marked painted atlas](../painted-atlas.png) · [clean painting](continent.png) · [native composition](continent.svg)

This is an original painted review of the current Minecraft map, at the owner's baseline immediately after the six ogres are named Kijin (anime S1E10). Rimuru's settlement is still a village. Later encounters, buildings and rulers are not silently treated as already present; the marked atlas retains explicit server/future reservations and disputed bindings from the current era atlas.

## Compare the sources

| Current project geometry | Original painting | External official reference |
| --- | --- | --- |
| [Checker preview](../preview.png), [terrain preview](../terrain-preview.png) | [58-site atlas](../painted-atlas.png), [unmarked composition](continent.png) | [Official interactive map](https://www.ten-sura.com/map), [official base image](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) |

The guides use only the project's own preview images. No copyrighted reference image or copied anime artwork is bundled. The official reference is linked for comparison; the painting is not evidence for a new geographic claim. Existing differences from the illustrated reference, scale compression and fixed-rule conflicts remain recorded in [regions.md](../regions.md), [review.md](../review.md) and the [research dossier](../../docs/research/tensura-world-2026-11-19/).

## Geometry and registration

Source commit: `0e5bd64` on `chatgpt/world-map`; production geometry last changed in `fc36e38`. The normalized UTF-8 SVG SHA-256 is `0d3b7723fb7e2775d24bd429031430684ca3fac361e909707c510fb0be9eb166`.

The common world frame is x=-8064..8064, z=-5632..5120. Guides and clean painting are 1536x1024 pixels at 10.5 blocks/pixel, north up. The marked atlas is 2200x2147 including its title and 58-entry key. Marker leaders point to the actual world anchor; number bubbles can be displaced for readability.

- [Geometry guide](geometry-guide.png) derives from current `world/preview.png`.
- [Terrain guide](terrain-guide.png) derives from the same current build's `world/terrain-preview.png`.
- [Raw generated painting](paint-r19.png) retains the original tool output. The [exact prompt](prompt.json) and [provenance](provenance.json) record its inputs.
- [Native composition](continent.svg) clips the painted land to all three original coast polygons. Exact lake polygons, eight river centrelines and original widths, and 21 road polylines are overlaid from the production SVG. The sea wash suppresses stray painted land beyond the true coast.
- [Site registration](site-registration.json) records every site ID, world position, projected anchor and displaced label position. The atlas SVG also carries the source world coordinates.
- [Presentation audit](presentation-audit.json) verifies exact source vector coordinates and all 58 projected anchors. Production SVG, checker preview and terrain preview remain unchanged from the stated source commit.

The native SVG composition is editable presentation artwork. Only `world/map.svg` governs generated terrain. Painted ridges, trees, shading and apparent heights are pictorial; they are not measured elevation or new river geometry. Minor brush features should not be traced into terrain without separate reference evidence. Existing roads include future/server reservations under the era handoff policy.

## Visual review and remaining work

The older `ocs-art-map/world/map-art-study-round-2.png` was inspected and rejected as the current delivery: its labels misplaced Sarion and Fulbrosia. It remains preserved in that separate worktree. The current painting follows the reviewed geometry, including the southern gulf, Sarion west of it, Fulbrosia east of it, Lake Siss, the northern island and the southwest island.

The first composition attempt produced repeating ocean-tile seams and discolored icy shadows. The final composition uses continuous sea texture and unfiltered land colors; the marked atlas was inspected after these corrections. The current review found no independently sourced reason to move a production coastline or site. Artistic ridge exaggeration is not such a reason.

This is the first painting review coupled to the current geometry, not a claim that three painting/SVG revision rounds are complete. Remaining location concepts, source gaps, unresolved fixed bindings and technical era gating remain open. The [mainland coverage audit](../../docs/research/tensura-world-2026-11-19/mainland-coverage-audit.md) tracks missing representations; the eight priority place concepts are separately delivered in [draft PR #87](https://github.com/Yasuke2000/ocs-two-lives/pull/87).

## Verification

Default map checker: zero errors, all 56 relations pass. Its two existing warnings remain: Laura's waterfall crosses its intended escarpment and the design-box height exceeds the preferred target while remaining below the hard cap. Presentation registration audit passes for three coasts, eight lakes, eight rivers, 21 roads and 58 sites. No runtime files, tool code, generated terrain, server application or deployment are part of this delivery.

Repository gate `bash tools/check.sh`: validation passed; 462 tests, 26 skipped, zero failures (46.001s test tier). This is offline verification, not an in-game acceptance test.
