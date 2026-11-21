# Dwargon moves northeast within the unchanged contract — round 86

**R87 painting follow-up closed:** [published current painting](https://github.com/Yasuke2000/ocs-two-lives/blob/d98513e79e386b493410ab219d110c5d5bd1fa61/world/painting-round87/README.md) aligns the moved relief, roads and six site groups. Earlier pending notes below retain their historical R86 context.

[Original before/after study](dwargon-relocation-study-r86.png) · [editable study](dwargon-relocation-study-r86.svg) · [independent audit](dwargon-relocation-audit-r86.json) · [current terrain atlas](atlas.png) · [58-site registration](atlas-registration-r86.json)

## Why this improves the map

The [secondary pinned-marker benchmark](proportion-audit.csv) places Dwargon northeast of Tempest. Its illustrated bearing is 35.31°; the former gate sat due north. The new authored gate **(780,−1390)** gives bearing 29.30° and distance 1593.89 blocks. The benchmark bearing discrepancy falls **35.31°→6.01°**; relative-distance error improves **−20.70%→−18.45%**. These are secondary-marker comparisons with unknown projection and precision, not verified novel coordinates. The [official introductory illustration](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) and current checker preview were visually compared. The broad mountain/forest relationship is retained.

No rule is loosened: the gate remains inside the1200..1600 distance and±30° north limits, all 56 relations pass, and the same58 IDs, radii, kinds, margins and parent offsets remain. Full common-scale reference geometry is still outside those limits and remains inert in C12's comment. This candidate is an improvement within the contract, not proof that every proportional conflict is solved.

| Site | Previous x,z | Current x,z | Radius |
| --- | --- | --- | --- |
| `dwargon` | (0,-1550) | (780,-1390) | 127 |
| `dwargo` | (0,-1650) | (780,-1490) | 8 |
| `dwargon_throne` | (0,-1656) | (780,-1496) | 8 |
| `kaijin_smithy` | (-12,-1634) | (768,-1474) | 8 |
| `dwarf_village` | (400,-1200) | (1000,-1000) | 124 |
| `dwarven_arena` | (500,-1180) | (1100,-980) | 58 |

The other 52 sites are unchanged. The original peak146 gate dome and top146 forecourt shoulder translate780 east/160 south. Three roads are adjusted: the main arrival approach, dwarf-village spur and Dragon's Nest trail. All other 18 native roads, every coast, river, lake, region, forest, biome polygon, ridge and other relief polygon remain unchanged. Dragon's Nest and Ameld source keep their coordinates. The native geometry is **our interpretation**; a road reservation does not imply later paving at S1E10.

## Export and fit

Source `355d1a338f7dccf835123ff7af6a68cfda3319363378c60f7f04359cab67d3a7` has a fresh normal export (66.1s). All21 exported road profiles have maximum grade≤0.500001 (floating tolerance), including the revised routes. The initial trial's main/spur grades0.50189/0.51988 were rejected and corrected before adoption. The main road end and spur start both meet designed first-air146 at the forecourt. All3179 authored roof columns retain at least6 blocks of designed cover. These measure the authored surface and roof envelope, not continuous rock, actual carving, structure placement or live walkability.

Height changes occupy33272 four-block cells in x−262..1186,z−1698..−818. Water pixels remain byte-identical; no hydrography is changed. Six anchor records move; only the two flat dwarf village/arena records change (ground75→73). All other anchor records are unchanged. The current atlas embeds the exact new normal PNG and reprojects all 58 site dots. Bubble packing is retained within the moved groups; the Canaat orientation label shifts within D to keep the new cluster clear. Minimum bubble spacing31.62px; all 16 names clear the padded number boxes and all 15 full stroked in-mask names fit their masks. The Ulgracia callout remains unchanged.

## Inert city proposals and remaining work

The seven C15 proposal elements translate with the capital. The first translated East room/gallery lacked sufficient cover, so that version was rejected. The adopted **planning-only** East floor/ceiling is80/110, galleries72, while West remains110/140. The two rooms, two lined galleries and three stair shafts are resampled at every lined integer-column centre. Using declared roofs plus lining/head allowances, minimum remaining cover is10.086 blocks; rooms remain inside the mountain and D masks. This is not generated void geometry, a registry addition, a constructed stair or an accepted template landing. R58's files retain their historical coordinates/levels; the current comment and R86 audit supersede that planning geometry. Exact city identities/entrances, voxel occupancy and the capital-template join remain C15 questions.

Ledger **286 unique records (228 thematic/design/reference +58 coordinate interpretations)**: six existing placement records corrected and one original-design record added. Inventory135/42 physical follow-ups is unchanged; no missing city is declared complete. **R85 painting predates these coordinates** and requires alignment. The [concept reservation audit](https://github.com/Yasuke2000/ocs-two-lives/blob/120f5d5/docs/art/registration-r86.md) updates six sheets and verifies all 58 reservations; original images/prompts remain. The original concept images remain useful setting studies, not geographically registered terrain renders. The post-Kijin S1E10 state remains. No technical file, protected runtime/mod/tool path, rule matrix, main merge, terrain application, chunks or deployment is changed.
