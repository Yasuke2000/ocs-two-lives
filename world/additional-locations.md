# Additional mainland locations — evidence and drawing proposals

[Original vector study](additional-location-study.svg) · [PNG preview](additional-location-study.png).
All orange marks are proposals, not generated terrain. The matching geometry is inside an inert C14/C15
comment in [map.svg](map.svg). Production still has exactly 58 registered sites.

## Evidence and proposed geometry

| Proposal | Source-backed relationship | Authored geometry: our interpretation | Production consequence |
| --- | --- | --- | --- |
| Galut | Wiki identifies it as Ulgracia's capital (`WIK-ULG-001`). | Centre `(-900,3050)`, radius 60; a separate city south of the existing park. | Current U coverage; distinct from the park/Spirit Dwelling entrance. New registration and a city design remain required. |
| Tengu settlement | Wiki places the village on a difficult Khusha summit (`WIK-TEN-001`); range membership has a cited LN8 chapter4 lead (`WIK-KHU-001`). | Centre `(-1000,1100)`, radius 40, in western Khusha. | Existing massif supplies context; summit height, terracing, access and footprint still need a terrain design and registration. |
| Sainte-Malukshure | Wiki describes a coastal capital near its tower, with Sarion to the east (`WIK-MAL-001..002`). | Centre `(-2320,1645)`, radius 64, west of Elmine. | C14: current anchor requires H, which is Fulbrosia. This alternative lies in current gameplay O. Do not silently reassign the country, anchor or gameplay mask. |
| Magic Tower | Official volume-2 manga synopsis places it in Malukshure waters (`PUB-MAL-001`). | Centre `(-2440,1840)`, radius 40, off the proposed capital shore. | Offshore structure/access proposal only. No speculative island added to the three-landmass production map. |
| Long Wall | Wiki places the barrier between the desert and Coleus/Lubelius (`WIK-WAL-001`). | Dashed corridor from `(-4250,-1700)` to `(-3940,-100)`; bends in SVG comment. | Era and engineered wall need a separate structure/terrain decision. It is not an arbitrary mountain range. |

The official synopsis is [Tensura portal, 9 September 2024, Vacation manga volume 2 section](https://www.ten-sura.com/news/comic/tensura-comic/news/post/10534).
It directly supports the maritime setting, not our exact shore or measurements. Manga story pages were not read.
The remaining wiki-backed relationships retain `fan-wiki` confidence; cited LN chapters are leads, not verified readings.

## Measured spatial checks of the proposals

Against the current authored coastline, the proposed Galut centre is about 92 blocks inland, and its radius-60
footprint is on land. It is about 206 blocks from the park centre, so the distinct footprints do not overlap.
The capital alternative is about 116 blocks inland: enough room for the proposed radius 64 plus a 48-block
margin, while remaining a harbour-scale proposal rather than pretending the existing pin is coastal.
The tower centre is about 113 blocks offshore and its full radius-40 disc is water. These are measurements
of our SVG, not canonical distances. They do not validate a future terrain build, profile, bridge or structure.

## C14 — reviewable fixed-data conflict

The active pin is `(-100,2000)`, about 262 blocks from the sea and east of Sarion, in Fulbrosia gameplay H.
`design/data/anchors.toml` explicitly requires H; the standard checker enforces that membership.
The coastal alternative west of Sarion cannot be applied as a silent coordinate change under that binding.
The requested evidence-first alternative is therefore drawn in the production SVG comment and this study.
No technical data or checker code was changed. The PR asks Yasuke to decide this mapping conflict.

## C15 — additional locations are not registered sites

Galut, Tengu, the tower and wall require different technical treatment; a tower or wall is not necessarily a
flat circular village. Their drawn circles are review footprints. The original 58-site contract and tools
remain intact. Matching wiki inventory rows remain missing in production even though a proposal now exists.
Orbic, Silberia and the other inventory gaps still need their own sourced treatment; this sheet does not
claim the larger wiki audit or the faithful-continent goal complete.
