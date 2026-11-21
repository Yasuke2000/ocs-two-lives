# Unnamed western basin and outlet — R104

[Current checker preview](preview.png) · [terrain atlas](atlas.png) ·
[measurements](western-basin-r104.json) · [source comparison](comparison.md).

The official introductory illustration shows a broad lake-like inland water in
the western states, west of Jura, with a narrow course toward the southwestern
coast. The earlier production map represented small design lakes but omitted
this distinct broad cue. The original official image was freshly downloaded and
visually compared locally with our preview. References remain links; no licensed
image or traced vertices are distributed.

This visual reading is **canon-implied** (MAP-WES-WATER-104), not a verified LN
name, measured shoreline or dated hydrological survey. The exact new lake and
course are **our interpretation** (DES-WES-WATER-104), distinct from Raja's small
lake and the WN-derived royal lake. No country border or named city is inferred.

## Original geometry

`western-unnamed-basin`:40 vertices, centred approximately(-1950,450), bounds
x−2212.82..−1659.88,z328.36..558.51; area97,399.81 blocks², level68,depth5.
`western-basin-outlet`:36 original vertices, length1287.99,width8,head68,mouth63.
It follows the lower western ground to the existing coast. The centreline starts
three blocks outside the lake as required by the river contract; its four-block
half-width joins the shore. Exact water level,depth,bends,outlet and catchment
are design choices. No invented lake name or initial-era urban development.

## Verification and practical limits

The final standard checker passes0errors,56 relations and2 prior warnings
(Laura escarpment and preferred box size). An initial start-on-shore point was
rejected because a river must start outside a lake; the final shore-width join
passes without changing tooling. Normal staging build67.6s; no `--apply`.

All prior active XML elements,58 site records and22 road records retain their
attributes. Exported sites.json and roads.json are byte-identical to the previous
normal build. Nearest site edge is188.00 blocks from the lake.12 lakes/9 rivers
now accompany9 coasts,14 mountain polygons,10 hills,12 forests,27 biome polygons,
28 region polygons and4 ridges. Continent and box sizes remain unchanged.

Normal height changes7203 cells,all within5.61 blocks of the new water geometry.
Water and biome change6739 cells each,all inside that geometry. A bounded
four-neighbour connectivity check connects the lake to the sea; ocean water is
implicit where designed ground lies below63 even when water.png is zero.
This confirms raster continuity,not Minecraft flow simulation or final terrain
noise,bank vegetation,chunk generation or in-game placement.

Atlas retains all58 registrations and20 context names; the terrain image,
source metadata and140-entry inventory caption change. The Blumund orientation
text moves north so that it does not read as the new lake’s name; numbered
markers and other context text positions stay fixed. Inventory140/42 open
physical follow-ups; all previous classifications retained. Ledger310 unique.
[R105 painting](https://github.com/Yasuke2000/ocs-two-lives/blob/8b4bbf6/world/painting-round105/README.md) now follows this lake/outlet and the140-entry caption. R100 and its prior source/caption are historical. Existing art pairs remain
unchanged. Source `e785c2b0`; current atlas/checker/terrain previews inspected.

The earlier coastline,scale,political,initial-era and C22 differences remain
open. This is a concrete landform correction,not proof of exhaustive wiki
coverage or the completed faithful continent.

Required repository gate:472 tests,26 skipped,zero failures(64.727s);
validation and zero changed-JavaScript check passed. Browser inspection checks
58 numbered circles,20 names,42 open rows,no overlapping context labels and
minimum10.09px text-to-number-circle clearance. All old numbered geometry is
retained. `git diff --check` passes. These are offline checks,not runtime acceptance.
