# Additional mainland locations — evidence and drawing proposals

Round55 [author source review](../docs/research/tensura-world-2026-11-19/vacation-source-review-r55.md) verifies the coastal capital cape,offshore tower and Malukshure/Sarion adjacency. The west bearing and exact proposal geometry remain qualified. The active C14 binding and fixed58 registry remain unchanged.

[Original vector study](additional-location-study.svg) · [PNG preview](additional-location-study.png).
All orange marks are proposals, not generated terrain. The matching geometry is inside an inert C14/C15
comment in [map.svg](map.svg). Production still has exactly 58 registered sites.

## Evidence and proposed geometry

| Proposal | Source-backed relationship | Authored geometry: our interpretation | Production consequence |
| --- | --- | --- | --- |
| Galut | Wiki identifies it as Ulgracia's capital (`WIK-ULG-001`). | Centre `(-900,3050)`, radius 60; a separate city south of the existing park. | Current U coverage; distinct from the park/Spirit Dwelling entrance. New registration and a city design remain required. |
| Tengu settlement | Official episode64 confirms Khusha residence (`OFF-TEN-001`); the difficult summit description remains wiki-backed (`WIK-TEN-001`). | Revised centre `(-1000,940)`, radius40, on the existing western Khusha ridge. | [Measured ridge/terrace study](tengu-settlement-study.md) replaces the earlier hillside proposal. Height/access/build design and registration remain open. No later tunnel applied. |
| Sainte-Malukshure | Author confirms a capital cape and Sarion adjacency (`AUTH-VAC-001..002`); Sarion specifically to the east remains wiki-qualified (`WIK-MAL-002`). | Centre `(-2320,1645)`, radius 64, west of Elmine. | C14: current anchor requires H, which is Fulbrosia. This alternative lies in current gameplay O. Do not silently reassign the country, anchor or gameplay mask. |
| Magic Tower | Author describes the offshore tower and new-moon approach (`AUTH-VAC-002..003`),consistent with the official manga synopsis (`PUB-MAL-001`). | Centre `(-2440,1840)`, radius 40, off the proposed capital shore. | Offshore structure/access proposal only. No speculative island added to the three-landmass production map. |
| Long Wall | Wiki places the barrier between the desert and Coleus/Lubelius (`WIK-WAL-001`). | Revised boundary corridor from `(-4045.40,-947.08)` to `(-3801.89,204.15)`; [measured review](long-wall-corridor-review.md). | Era and engineered wall need a separate structure/terrain decision. It is not an arbitrary mountain range. |

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

Round40 corrects the earlier Long Wall proposal: it now follows the authored desert edge with a local dry detour west of the Coleus oasis. The existing caravan-road crossing needs a future gate; exact wall course/width/endpoints remain our interpretation. All active terrain and58 reservations are retained.

The additional-location study backdrop is refreshed from the current active SVG layers,including the moved Coleus oasis,current roads and desert habitat. Its older backdrop predated several terrain revisions. Proposal markers remain alternatives; this presentation refresh changes no production geometry.
