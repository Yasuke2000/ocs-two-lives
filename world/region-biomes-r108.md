# Current designed regional biome shares — R108

The22 region descriptions now report the current designed biome export,
replacing old aspirational targets. [CSV](region-biomes-r108.csv) contains all107
region/biome rows; [JSON and coverage audit](region-biomes-r108.json) retains
full precision,counts and hashes. [Historical targets](region-biome-targets-history-r107.csv)
remain available. Run `python -B world/region_biome_census.py` to reproduce.

These are **our interpretation**: measured properties of authored gameplay
masks,not surveyed national borders,canonical climate or final in-game biomes.
Names aid orientation;a D/G statistic is not a claim about a sovereign country.
No geometry,normal raster,climate rule or biome ring changes.

## Method and boundary scope

Source SHA `b275095000ed41e635c72295d05dbd3516cf8fd0c596a7a0e7a9fe14159815e1`; biome PNG SHA
`77a58188f5f8e242cc0d0b95aeb7b10068f58a3899aa292c8014842c827d261d`. Every four-block pixel centre
is tested against native region outlines united per letter. Ocean palette0 is
excluded. Exact shared-boundary samples go to the first matching SVG region in
source order; this finite-grid tie rule is not runtime chunk ownership. All22
distributions sum to100% before rounding. Positive shares below0.005% are shown
as<0.01% in prose. River/beach shares include converter-assigned biomes:do not
copy those automatic-only biome IDs into hand-authored SVG data-biome values.

2,693,557 non-ocean samples are assigned to gameplay masks.26 shared-boundary
samples receive one deterministic assignment. Every non-ocean sample inside
the native coastline is covered. Another9,444 non-ocean samples lie outside
the native coast and are reported separately rather than assigned a country:
mostly beach raster-edge coverage,with small forest/plains/water mouth slivers.
Maximum distance to native coast20.44 blocks. These designed-raster edge samples
do not establish an extra nation or justify enlarging native coasts/masks.

## Measured summary

| Gameplay region | Represented area, blocks² | Largest biome | Share |
|---|---:|---|---:|
| A — Raja | 121,936 | `minecraft:plains` | 91.55% |
| B — Beast Kingdom of Eurazania | 3,413,408 | `minecraft:jungle` | 44.69% |
| D — Armed Nation of Dwargon | 5,053,456 | `minecraft:plains` | 73.55% |
| E — Eastern Empire | 2,531,344 | `minecraft:plains` | 86.12% |
| F — Kingdom of Falmuth | 2,220,624 | `minecraft:plains` | 98.24% |
| G — Kingdom of Englassia | 1,216,608 | `minecraft:plains` | 68.82% |
| H — Harpy Queendom of Fulbrosia | 2,248,512 | `minecraft:plains` | 65.30% |
| I — Ice Continent | 2,033,360 | `minecraft:snowy_plains` | 76.72% |
| J — Jura Forest / Rimuru's village (gameplay J) | 4,524,000 | `minecraft:forest` | 40.67% |
| L — Holy Empire of Lubelius | 1,246,112 | `minecraft:plains` | 94.22% |
| M — Milim's old domain | 4,815,168 | `minecraft:plains` | 87.30% |
| N — Nostraille | 129,280 | `minecraft:plains` | 99.84% |
| O — Morgdahl | 1,413,120 | `minecraft:plains` | 97.64% |
| P — Jistav | 1,188,880 | `minecraft:plains` | 54.96% |
| Q — Yggdonia | 84,304 | `minecraft:birch_forest` | 98.88% |
| R — Kingdom of Blumund | 1,868,336 | `minecraft:plains` | 93.02% |
| S — Sorcerous Dynasty of Sarion | 2,200,736 | `minecraft:old_growth_birch_forest` | 75.89% |
| U — Ulgracia | 223,152 | `minecraft:old_growth_birch_forest` | 93.53% |
| V — Damargania / western wastes | 3,288,768 | `minecraft:plains` | 44.47% |
| W — Lake Siss marsh | 1,813,216 | `minecraft:swamp` | 59.69% |
| X — El Dorado | 1,420,240 | `minecraft:plains` | 92.36% |
| Y — Yuzalgh | 42,352 | `minecraft:plains` | 99.89% |

## Why the old percentages needed correction

Jura’s old target listed20% ancient forest. The current200-block ancient core
occupies about2.4% of the larger J gameplay mask; its dark/light rings and
surrounding land are measured separately. The fixed core/rings must not be
expanded merely to chase an obsolete area target. Measured prose now describes
the authored geometry that the converter receives.

The D mask includes surrounding terrain as gameplay coverage. Its high plains
share does not override the mountain-built Dwargon setting. Biome category,
terrain elevation,underground city and sovereign extent are different quantities.
This census does not close country-boundary or whole-city questions.

The X mask has no explicit forest-biome category in this export despite its
older forest target. A dedicated source/painting review should determine where
El Dorado’s illustrated tree cover needs representation; a plains biome alone
does not prove zero generated trees. Do not add blanket forest just to reach
the old20% target. This is a concrete next visual/terrain check.

All58 sites,22 routes,source geometry,normal rasters,previews and R107 painting
remain unchanged. Inventory142/42 is retained. Ledger313 includes one explicit
design-census record. No new canonical climate fact,dated landscape change,
whole-wiki access or completed faithful-map goal is claimed.

Validation: the census CSV/JSON reproduce byte-for-byte.22 measured prose mixes
and22 archived targets are checked;313 unique claim IDs and allowed confidence
values verified. Required repository gate:472tests,26skipped,zero failures
(64.484s); validation,zero changed-JavaScript and diff checks pass. Source SVG,
normal rasters,previews,atlas geometry and protected paths remain unchanged.
