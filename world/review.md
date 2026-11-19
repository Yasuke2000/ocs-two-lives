# Research-driven map review — round 6

The standard checker and repository gate pass. This remains a source-qualified, server-scale adaptation:
exact vertices, heights and point coordinates are interpretation. Primary-source coverage and the
remaining owner-facing lore/scale alternatives are kept explicit rather than called proven canon.

## Current drawing and evidence

Western placements now follow the supplied point pattern more closely within unchanged server ranges:
Blumund `(-1500,-620)`, Marris `(-1800,-1650)`, and the Sealed Cave `(-120,-400)`. The northern bay bank,
Shia landing, western junction and cave hill/stream move with them. The northeastern coast has a hooked
inlet and the east coast a bay; P/M gameplay coverage follows the new connected land tongue.
All 58 site IDs, radius minima and relative internal offsets are retained.

[Regions and deliberate differences](regions.md), [claim ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv),
[publisher LN findings](../docs/research/tensura-world-2026-11-19/ln-sample-findings.md),
[source access](../docs/research/tensura-world-2026-11-19/source-access.csv), [reference comparison](comparison.md).
The ledger contains **128 records: 70 thematic/design records and 58 site-coordinate interpretations**,
including 11 directly read LN claims; not all records are verified canon.

## Measured verification

```
python -I tools/world/map_check.py world/map.svg --preview world/preview.png
python -I tools/world/build.py
bash tools/check.sh
```

- Required standard checker after every SVG edit: **0 errors, all 56 relations pass**. Two warnings:
  Laura's intended mountain-waterfall crossing and a 12288 by 10752 box, 512 taller than preferred but
  below the hard cap. Mainland about 9653 by 6250 blocks.
- Final normal build, without skip-check: **57.6 seconds, 0 converter warnings**, 3072 by 2688 pixels.
  The normalized source SHA matches the current SVG. No apply performed.
- **58/58** generated x/z positions match the drawing; all effective radii meet footprint minima;
  every internal anchor keeps its exact parent offset.
- Actual water raster: **0 wet pixels out of 1116** sampled over the cave's complete radius-75 disc.
- Actual exported profiles: **21 roads, maximum grade 0.5 (1:2)**, allowing only numerical float epsilon;
  longest generated bridge run **24 blocks**, below the 64-block limit.
- Repository gate on the integrated main-a1848be branch: validation passes; **462 tests, 0 failures,
  26 skips**. Installed Git Bash is used because system bash points at missing WSL. No tests changed.
- All 22 regional biome-mix target lists sum to 100; they are design targets, not raster measurements.
- Checker preview, converter terrain, numbered atlas and reference/alternative drawings inspected.
  Source art is linked only in the repo; combined reference screenshots remain outside it.

An additional profile audit found ten old climb routes slightly above 1:2 despite zero converter warnings.
Only authored road geometry was changed: short axis or rational diagonal segments stay within nine blocks
of the sketched corridor and make four-block centreline intervals exact. Final exported profiles satisfy
the real distance-based slope limit. No grading algorithm or tool code was edited.

## Proportion and lore alternatives

[Before/after audit](proportion-audit.csv): distance-ratio discrepancies drop **57.4 → 32.8%** for Blumund,
**41.8 → 11.4%** for Marris and **24.3 → 3.3%** for the cave. These compare secondary marker pixels with an
unknown projection, not a surveyed canonical coordinate system.
[Reference-scaled study](proportion-study.png) shows why remaining differences cannot silently be removed
under the fixed ranges/bearings. The three trial circles are also inside an inert map.svg comment.
[Other lore alternatives](lore-alternatives.png) likewise show C05/C06 without applying unverified terrain.

The owner specifically authorized five data-entry corrections in tools/world/canon_relations.toml.
Other 51 relations, site/sea rules, checker code and tests remain unchanged; no further technical file
differs from the integrated main. See design/lore/world-map-corrections.md.

Further relevant WN/LN geography, manga page-level sources and exact anime timestamps still warrant
primary-source review. Unavailable licensed fragments are not presented as read. No Minecraft chunks,
runtime acceptance, pack application, merge to main or deployment are claimed.

## Wiki coverage audit

The [126-entry audit](../docs/research/tensura-world-2026-11-19/wiki-coverage.md) enumerates all 31 owner-listed Location entries and the 44-entry Countries index, plus related geography. It identifies 29 entries without distinct production representation. These include interior and historical candidates, not 29 automatically approved new continent sites. Eastern Empire region E and its two markers are present; exhaustive city/interior coverage is not. No production geometry changed in this documentation pass.
