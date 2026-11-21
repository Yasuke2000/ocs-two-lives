# Vertex-budget study — round 44

The active map is retained. Nine polygon outlines exceed the creative brief's preferred
20–120 vertices, while remaining within the checker's mandatory 8–400 range.
Reducing the mainland to 120 straight-line vertices with the tested method moves its
boundary by up to 31.951 blocks and changes 320,719 square blocks of land classification.
This study does not justify that geographical change merely to reduce authoring complexity.

Source: `world/map.svg`, normalized UTF-8 text SHA-256
`7d021766b648dcfd89a6dcbebeaede431d4b7375773692a341d27bb3506503aa`.
Full diagnostics: [vertex-budget-study.json](vertex-budget-study.json).

## Method and results

Read-only Shapely 2.2.0 / GEOS 3.14.1 Douglas-Peucker simplification, preserving each
polygon's individual topology. Tested tolerances: 1, 2, 4, 6, 8, 10, 12, 16, 20, 24 and
32 blocks. The table shows the first tested tolerance reaching 120 vertices; it is
not an optimization proof or an adopted alternative.

| Outline | Active vertices | Tested tolerance, blocks | Candidate vertices | Boundary Hausdorff distance, blocks |
| --- | ---: | ---: | ---: | ---: |
| coast/Magic Continent | 388 | 32 | 120 | 31.951 |
| forests/jura-eastern-foothill-woodland | 212 | 1 | 90 | 0.999 |
| regions/V | 170 | 2 | 117 | 1.990 |
| regions/F | 140 | 1 | 100 | 0.997 |
| regions/D | 168 | 1 | 115 | 0.994 |
| regions/J | 182 | 1 | 113 | 0.998 |
| regions/M | 170 | 2 | 104 | 2.377 |
| regions/B | 134 | 1 | 106 | 0.910 |
| regions/R | 128 | 1 | 76 | 0.980 |

Simplifying the seven country masks independently can alter their shared borders or
their match to the coast. A valid candidate polygon alone does not prove valid combined
coverage. No candidates were written into production, and no converter run or new
terrain geometry is claimed. Curve fitting and shared-edge simplification remain
possible approaches; this experiment did not assess them and does not establish that
the preferred range is impossible.

## Exact coverage diagnostic

An additional exact-coordinate check of the **existing** 22 masks found 53.045 square
blocks of land outside their union and 0.712 square blocks of masks outside land.
Three positive-area overlaps occur: J/S 7.730, S/O 40.668 and S/H 2.280 square blocks.
These are geometric areas, not counts of affected Minecraft columns or proof of a
runtime fault. The repository checker still governs mandatory acceptance and uses
its own tolerances. The exact coverage is consequently not claimed to be perfect.

A future simplification should preserve shared edges, coast adjacency, river mouths,
site buffers and road/water alignment, then pass the normal checker, converter and
coordinate-aligned export review. Do not change checker limits to conceal the issue.

## Visual and source review

The current checker preview was inspected beside the cached official introductory
map. The broad northern bay, Jura between the Canaat range and southern territories,
eastern empire, southern gulf and western headland remain legible. Existing scale,
site and fixed-rule departures stay disclosed in [regions.md](regions.md) and C12.
No new canon fact or source priority is inferred from this authoring experiment.
Later official chapter markers do not move the selected initial post-Kijin story date.

The current numbered [terrain atlas](atlas.png) and
[painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round43/atlas.png)
remain valid presentations of the retained source. All 58 site tuples and the 217-entry
ledger remain unchanged; 129 inventory entries still include 32 tracked follow-ups.
No main merge, apply, chunk generation or deployment occurred.
