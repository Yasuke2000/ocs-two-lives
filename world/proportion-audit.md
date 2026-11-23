# Current relative-position benchmark

23 November 2026. Active canonical source `534d07ade01d21f3763bebf98cfd18428761aba50388ec70cff4b77e87e787f0`. [Current14-row CSV](proportion-audit.csv) · [recalculation/provenance](proportion-current-audit.json) · [official visual comparison](comparison.md).

All14 source marker positions were re-extracted from the three privately cached metadata files of the user-supplied pinned TensuraMap revision. This is a **fan-marker benchmark**, not a surveyed canon coordinate system. Projection, symbol placement and accuracy are unknown. Direct LN evidence and approved owner choices take precedence over its residuals; a better score alone is not a reason to move a site.

The table had not followed the approved inland Frost Palace move. It displayed normalized distance3.2901/bearing335.6° instead of current3.6082/337.4°. The distance residual changes from−41.1% to−35.4%, and the bearing residual from+6.1° to+7.9°. This corrects reporting; no palace, coast or source geometry moves. The larger-island proposal remains a separate owner choice and is not scored as the active map.

Distances use Tempest–Siss as1in each system. Current world normalizer is1104.536102blocks; reference normalizer166.207701pixels relative to Rimuru City(1670,1120). Bearings are north-up, clockwise from north; deltas wrap to[−180°,180°). Calculations use unrounded coordinates/ratios. All13other numeric rows retain their earlier displayed values; original baseline columns remain historical, not newly computed before/after experiments. New columns show actual source coordinates and SHA.

| Current marker | Authored x,z | Distance / Siss | Distance residual | Bearing residual |
| --- | ---: | ---: | ---: | ---: |
| `dwargon` | 780, -1390 | 1.4430 | -18.5% | -6.0° |
| `lake_siss` | 1100, -100 | 1.0000 | 0.0% | 1.7° |
| `blumund` | -1500, -620 | 1.4695 | 32.8% | 0.1° |
| `marris` | -1800, -1650 | 2.2107 | 11.4% | -6.8° |
| `elmine` | -1680, 1740 | 2.1898 | -0.3% | -4.9° |
| `jia` | 200, 2450 | 2.2255 | 2.7% | -4.7° |
| `laura` | 1500, 1600 | 1.9856 | -7.1% | 11.6° |
| `nasca` | 3200, -1800 | 3.3240 | -1.1% | 14.9° |
| `amrita` | 3800, -500 | 3.4700 | -7.2% | 3.6° |
| `forgotten_dragon_city` | 2650, 800 | 2.5061 | -0.3% | 0.1° |
| `frost_palace` | -1530, -3680 | 3.6082 | -35.4% | 7.9° |
| `el_dorado` | -4300, 3000 | 4.7469 | -19.3% | -7.8° |
| `sealed_cave` | -120, -400 | 0.3781 | 3.3% | -7.2° |
| `ogre_village_ruin` | 500, 300 | 0.5279 | -32.7% | -1.5° |

Amrita is the current eastern game reservation, not a verified ruin centre; see [C07choice](amrita-current-nesting-review.md). `laura` is a technical ID for Carrion's capital; the guide/wiki naming conflict remains open. Palace and city markers describe reservations, not whole urban footprints or initial resident states. The current source includes approved Filtwood and early forest trails. This14-marker test does not cover every country, coastline, border or travel distance.

## Historical benchmark notes

The following retains the earlier design iterations and their original source/count scope. References to pending artwork or limited relation exceptions describe those earlier rounds. Current artwork and separately approved data changes are recorded in [DELIVERY](DELIVERY.md).

# Relative-position audit — provisional reference benchmark

R86 [Dwargon northeast relocation](dwargon-relocation-r86.md) moves the gate to (780,−1390), retaining all 56 relations and 58 footprints. The secondary bearing discrepancy improves 35.31°→6.01°. Six related site records, two local relief shapes and three roads are aligned; water and all other native geography remain. Source355d1a33; ledger 286/inventory 135/42 follow-ups. R85 painting needs alignment; all 58 concept reservations are checked in the [art audit](https://github.com/Yasuke2000/ocs-two-lives/blob/120f5d5/docs/art/registration-r86.md).

[CSV](proportion-audit.csv) compares 14 authored sites with the user-supplied pinned interactive reference.
Distances are normalized to Tempest–Siss in each coordinate system, so absolute block scaling cancels out.
Bearings use north-up image pixels and north-up world coordinates. Values are computed from the source
metadata and current SVG, not from remembered lore.

**Limit:** these are fan marker positions over an illustrated map, not a surveyed canonical coordinate system.
A discrepancy is a review signal, not evidence that a licensed novel is wrong. No claim of official precision
or a known projection is made. The official base image is a separate visual reference in comparison.md.

The audit exposes nonuniform compression that the geometry checker cannot assess. Fixed server distances,
site footprints, parent offsets and route constraints still apply; do not loosen technical rules beyond the
five specifically approved entries. Any source-supported alternative that cannot fit those constraints must
be drawn in a comment and explained in the PR, as required by the task.

Round 6 corrects Blumund, Marris and the Sealed Cave, with matching coast/approach changes. Before/after
columns preserve the baseline at commit 4c99877. The three distance-ratio discrepancies fall from
57.4% to 32.8%, 41.8% to 11.4% and 24.3% to 3.3% respectively.

[Reference-scaled study](proportion-study.png) and the inert `reference-proportion-*` circles inside
map.svg show where fixed rules prevent a single common scale. The trial coordinates are **our interpretation**
of secondary marker pixels with an unknown projection; they do not prove primary canon coordinates.
Further changes should follow stronger source evidence or an explicit owner choice on those conflicts.

Rounds 14 and 16 improve two further locations within the unchanged fixed rules. Elmine moves to
(-1680,1740); its secondary distance discrepancy changes from -13.0% to -0.3%, and bearing discrepancy
from -17.5 to -4.9 degrees. The old Forgotten Dragon City moves to (2650,800); its corresponding values
change from -9.8% to -0.3% and from -13.3 to +0.1 degrees. The CSV retains the original baseline columns.
These near matches do not establish canonical survey accuracy: marker projection and placement precision
remain unknown. Exact coordinates and approach roads are our interpretation. The Dragon City change
concerns Milim's old settlement, not the later planned capital project in former Eurazania. The directly inspected [LN20 chapter 1 opening](../docs/research/tensura-world-2026-11-19/ln20-licensed-capital-review.md) does not establish that project's exact coordinates or identify it with the authored `laura` reservation.

Fresh required repository gate for this reporting-only follow-up:494tests in66.388s,26skipped,the same two legacy Filtwood U/J failures plus validation;zero changed JavaScript. Gate remains failing. All14normal/map/art hashes retained;360claim IDs/classes retained;local review links resolve. No new source SVG,checker preview,conversion or Minecraft run is claimed.
