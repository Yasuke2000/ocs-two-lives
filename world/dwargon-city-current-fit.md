# Current Dwargon city proposals: surface fit and source limits

23 November 2026. [Current original plan](dwargon-city-current-plan.png) · [editable SVG](dwargon-city-current-plan.svg) · [finite audit and exact native attributes](dwargon-city-current-fit.json).

The displayed R58 plan predates the approved northeast capital relocation and still shows obsolete floors/coordinates. R86 updated the seven inert SVG elements, but its numerical evidence predates today's source. This review extracts those exact current elements and checks them against canonical534d07ad and the matching normal index. No production element or coordinate changes.

## Current interpreted geometry

West room outline is centred about(560,-1720), first-air110/ceiling140. East is about(1060,-1690), first-air80/ceiling110. Both galleries use first-air72,air-height8,width6 and lining2. Internal shafts are at(760,-1456),(590,-1680),(1060,-1620), with declared upper levels146,110,80. All coordinates, dimensions, levels, city envelopes, gallery connections and stairs are our interpretation (DES-DWG-058/086). The full city list stays wiki-qualified; [LN13 directly corroborates East/access](../docs/research/tensura-world-2026-11-19/ln13-east-city-source-review.md) only.

| Native proposal | Lined integer-column centres | Reference roof top | Minimum designed allowance |
| --- | ---: | ---: | ---: |
| `west-city` | 16167 | 142 | 15.992188 |
| `west-gallery` | 3665 | 82 | 34.421875 |
| `east-city` | 27610 | 112 | 10.085938 |
| `east-gallery` | 3760 | 82 | 13.036133 |
| `capital-stair-shaft` | 316 | 152 | 41.375000 |
| `west-stair-shaft` | 316 | 116 | 48.171875 |
| `east-stair-shaft` | 316 | 86 | 50.334961 |

The52,150column tests include every integer-column centre within the declared lined footprints. Room buffers use a round2-block distance extension; galleries use half-width3 plus lining2; shaft discs use radius8 plus lining2. Designed height is sampled bilinearly from the current4-block raster, using its declared centre convention. Reference roof top is room ceiling plus lining, gallery first-air plus air-height plus lining, or shaft upper first-air plus4headroom plus lining. These definitions are explicit; no actual carved roof was inspected.

All sampled footprints remain inside native D and mountain polygons. The room footprints have zero columns overlapping the reference capital template box(706,-1510)..(854,-1342), using the R86 placement and the current blueprint's declared148x168footprint; gallery/shaft access intentionally meets that precinct, so a zero-overlap claim is not applied to them. The drawing's capital circle is the registered reservation, not a complete city boundary. Minimum cover10.0859375exceeds the planning threshold6; this is designed surface allowance only.

## What remains before terrain adoption

The accepted source hierarchy does not locate the LN East gate, its Imperial road, an external crossing or a surveyed pass. The WN bridge/pasture remains a separate continuity-specific lead. No line is added from this room to Nasca. The proposed East room's relative location is plausible original planning, not a verified LN bearing.

These volumes remain inert in the existing C15comment. The current SVG schema expresses registered site carves; an illustration of extra volumes does not activate them. Existing capital-template landing, actual voxel conflicts, connected walkable stairs, continuous rock, natural cave voids, lining, aquifers/fluids, complete city design and initial construction require technical integration and in-game checks. Those remain Claude's work. The current data are a concrete geometry handoff, not a new registry or approval to apply it.

All58registered sites,23active roads,13lakes,coasts,watercourses,regions and biomes are retained. All14normal files and selected map/atlas/painting bytes match the pre-review state. No new checker/converter run is needed for an unchanged production SVG. Inventory143/42physical follow-ups stays open; no city is declared complete. The existing DES-DWG-058 record now points to current values and this evidence, without adding a duplicate claim or altering confidence. Ledger359. Required repository result is recorded after execution.

Fresh required repository gate:494 tests in66.158s,26skipped,the same two legacy Filtwood U/J failures plus validation;zero changed JavaScript. Gate remains failing. Original plan PNG visually inspected;all local review links resolve;git diff --check passes. No actual gameplay acceptance is claimed.
