# Current painted map — terrain source 1ea6782d

[Numbered atlas](atlas.png) · [clean painting](continent.png) · [editable composition](continent.svg) · [reference comparison](comparison.md) · [registration audit](presentation-audit.json).

This presentation follows map commit `dc92845`, normalized SVG SHA-256 `1ea6782d789523627c6c7c5469742fea26a1f1fb772ba5ac3a400c5da4c8ebf5`. It refreshes the original third-round painting from [PR92](https://github.com/Yasuke2000/ocs-two-lives/pull/92) using only that original artwork and current project checker/terrain guides as image-generation inputs. No copyrighted reference image was supplied to generation.

The three earlier painting/SVG reviews remain historical at their recorded sources. This refresh brings the presentation forward to the current Orbic habitat, Ice coast and unnamed Imperial basin. It is not a new terrain build, a claim that all geography is verified, or a replacement for the active SVG.

## Changes and SVG review

| Review finding | Current presentation | Production decision |
| --- | --- | --- |
| Earlier painting predates the three limited Ice inlets. | Current coast clips and ocean mask follow all105 source vertices. The native land base prevents painted blue pigment from defining an additional inlet. | Retain the current coast and fixed palace precinct. Pictorial ice cliffs do not prescribe height. |
| Orbic habitat was still green in the old painting. | Modest depleted-ground texture plus an exact native highlight of `orbic-depleted-ground`. | Retain the reviewed habitat polygon; do not invent a capital, battlefield or complete sovereign outline. |
| The old painting omitted the small Imperial basin. | All9 exact lake polygons are restored, including the unnamed basin. | Retain current water metadata and C05 qualification; do not identify the lake as Silberia. |
| Painted water could otherwise introduce a stray tributary or oversized lake. | Raw blue pigment is suppressed in the land texture before9 exact lakes and8 exact river polylines are overlaid. | Reject pictorial drainage changes; active water geometry is unchanged. |
| Disputed reservations could look like verified surface places. | Legend preserves C07 Amrita game reservation, C14 Sainte game pin, C20 Filtwood binding and C22 coastal palace reserve. Ghastone/Rostia remain country pins. | Retain the disclosed source/fixed-rule decisions. A number bubble is not a complete city or initial building. |
| The tracked standalone terrain preview lagged behind the normal export. | `world/terrain-preview.png` now equals the current staged preview byte for byte, with a separate provenance record. The main numbered terrain atlas already embedded that current export. | Refresh the presentation copy only; no converter or terrain modification. |

The active `world/map.svg` and checker preview remain byte-identical to `dc92845`. No painting finding justifies new physical geography. Current explicit source, era, fixed-rule, country coverage, structure-fit and runtime obligations remain open.

## Geometry and registration evidence

World frame is `(-8064,-5632,16128,10752)`, north up,1536×1024 clean composition. Native source geometry contains3 coasts,9 lakes,8 river centrelines at source widths,21 road polylines and the1 Orbic habitat highlight. Source point lists, current coast clip/ocean mask and58 projected anchors are verified in the audit. Number bubbles have a minimum32.47-pixel centre separation. The2200×2147 atlas embeds the exact current clean composition bytes.

Filters and clipping define the native composition, while the raster provides original texture. Pictorial canopy, ridge, bank and snow strokes are not surveyed biome or elevation masks. The frozen island's snow and the northern painted mountains do not prescribe new peaks. Mandatory main-road metadata also does not prove these routes were paved at the selected post-Kijin instant.

The raw image was packaged without changing any decoded RGB pixel. [Exact prompt](prompt.json), [input/output provenance](provenance.json) and [guide images](terrain-guide.png) preserve the process. The production source SVG, checker preview, normal index and current tracked terrain copy have matching recorded provenance; no new converter run was needed for unchanged source bytes.

Current painting, numbered atlas, source guides and cached official base illustration were visually compared. The official reference supports broad geography; exact server coast, compression and habitat dimensions remain authored. [Official interactive map](https://www.ten-sura.com/map) · [official base illustration](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp). Reference artwork is linked, not copied into this repository.

Standard checker:zero errors, all56 relations pass, same2 warnings (Laura waterfall/escarpment crossing and preferred design-box height). Repository validation and472 tests pass (26 skips,zero failures,44.520s test tier). No runtime apply, Minecraft chunks, PR merge to main or deployment.
