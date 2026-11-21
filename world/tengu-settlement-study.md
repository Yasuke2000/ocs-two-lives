# Tengu settlement — official-source and ridge review


**R99 follow-up:** the active source now contains a small interpreted meadow glade on the same ridge. The village, terraces and surface approach remain unregistered/unbuilt. The new [current-terrain and access review](tengu-glade-r99.md) supersedes the missing-only coverage description below; older source qualifications and historical counts remain.

[Original plan and measured profile](tengu-settlement-study.png) · [editable SVG](tengu-settlement-study.svg) · [terrain samples](tengu-terrain-review.json).

This improves an additional-location proposal; it does not add a registered settlement to the active 58-site map. The proposed ridge, building layout and paths are our interpretation. Missing Tengu settlement coverage remains open until registration, terrain/access design and source/era fit are resolved.

## Evidence actually inspected

| Source | Supported detail | Limit |
| --- | --- | --- |
| [Official episode page, route no68](https://www.ten-sura.com/anime/tensura/story/no68), displayed episode **64**, Japanese title *Benimaru no Junan* | The Tengu inhabit Khusha. Tempest seeks a road tunnel through their mountain; Momiji objects to boring it. OFF-TEN-001/002. | A later diplomatic episode, not the initial post-Kijin state. No precise village coordinates, tunnel route or summit survey. |
| [Official still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no68/img2.jpg) | Outdoor meeting, vegetation and rocky terrain behind the visitors. OFF-TEN-003. | Partial background, not an aerial site plan. |
| [Official still 5](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no68/img5.jpg) | Small straw-roofed timber gateway, striped fence and pink-blossomed trees behind Momiji. OFF-TEN-003. | Visual interpretation of one limited frame; neither a permanent pink forest biome nor an S1E10 architectural survey. |
| [Author WN102 / URL instalment106](https://ncode.syosetu.com/n6316bn/106/), existing ledger WN102-001, summit/gateway paragraph | The WN describes a remote summit and barrier gate toward the settlement. | Separate continuity. Do not import its dimensional gateway into the anime/LN proposal without reconciliation (C16). |
| [Wiki Tengu article](https://tensura.fandom.com/wiki/Tengu), WIK-TEN-001 | Difficult Khusha summit setting. | Fan-wiki confidence. The cited LN8 chapter4 passage remains unread. |
| [Publisher-hosted LN8 fragment](https://gcnovels.jp/reading/slime8.htm) | Public prologue was inspected. | It does not expose the cited chapter4 Tengu passage; no direct LN upgrade is claimed. |

All five official episode stills were visually inspected. Stills1/3/4 are character/action context and do not independently establish geography. Reference files stay outside the repository under `ocs-world-research/references/tengu/`. The episode route was checked against its displayed heading rather than treating the URL number as an episode number. No playback timestamp was available.

## Fixing the proposal's hillside placement

The earlier illustrative point `(-1000,1100)` did not actually occupy a summit in the authored terrain. The normal staged height raster gives its centre sample as96.75, whereas the nearby ridge reaches189.75. The revised illustrative centre is `(-1000,940)`, radius40 retained:160 blocks north, on the existing western Khusha ridge. This exact point is a server design choice, not a coordinate supplied by the episode or wiki.

| Proposal disc | Centre sample | Minimum / maximum sampled height | Wet samples |
| --- | ---: | ---: | ---: |
| Former hillside `(-1000,1100)` | 96.75 | 78.0 / 123.0625 | 0 / 316 |
| Revised ridge `(-1000,940)` | 188.5 | 146.5 / 189.75 | 0 / 316 |

These are4-block raster samples from the current normal converter build; they are not Minecraft chunk measurements. The circle statistics use pixel centres; centre values use the containing raster cell. The full disc remains steep. A review footprint at a peak does not create flat building ground or verify a safe path.

## Original compact terrace proposal

The80-block review disc holds a compact upper meeting court, four small dwelling footprints on separate terraces, a roofed timber gateway and a narrow surface approach. Limited gateway/fence/tree cues come from the official stills; the number, shape, orientation, materials, terracing and path arrangement are authored. Pink circles suggest a few flowering trees; they do not replace Khusha with a pink biome. This compressed village vignette does not assert the canonical settlement's full size.

Terrace elevations, cut/fill, retaining walls, access grades and structure footprints still need a reviewed design. No flat site pad, tunnel or carving is applied. The post-Kijin baseline has no completed later Tempest tunnel or visiting envoy roster. The source does not establish precisely which buildings or trees were already present at S1E10.

The matching circle in the inert proposal comment of `world/map.svg` and the wide additional-location study now uses the ridge point. All live site coordinates/radii and every production coast, lake, river, relief, vegetation, biome, region and road element remain unchanged. The checker preview is unchanged; only the source hash changes because its inert comment changed. The old continent painting remains spatially compatible with all active geometry and58 markers at its recorded earlier hash.

## Verification scope

Default checker: zero errors, all56 relations pass, two prior warnings. Fresh normal conversion verifies current source provenance; the generated terrain preview remains byte-identical to the preceding build. Parsed live SVG elements equal the preceding commit after XML comments are excluded. The original study was rendered and visually reviewed. This evidence proves a better documented proposal; it does not close Tengu registration, all-wiki coverage or runtime placement.

Normal build completed in56.4s with no converter warnings. Repository gate `bash tools/check.sh`: validation passed;462 tests in44.952s,26 skipped,zero failures. Ledger audit:191 unique IDs, all with confidence and snapshot qualification. Both126-entry scope inventories retain26 missing representations and3 unverified parent designs.
