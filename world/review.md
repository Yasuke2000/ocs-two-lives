# Research-driven map review

The map remains a **draft**, with five default checker errors. No worldgen acceptance or deployment is claimed.

## Changes from the previous visible iteration

Restored the northern bay west of Canaat, introduced a southern gulf between the peninsulas, and gave the
west coast a projecting tongue and inward bay. Moved the Ameld source from `(900,-1000)` to `(200,-1240)` and
routed it south then east toward Siss, following the WN route and official guide inflow. The Fulbrosia trail
goes around the gulf head. Reconnected the west-Jura brook to the gulf and clipped habitats/Ulgr's bluff.
All 58 footprints and relative internal offsets are preserved. The exact vertices remain authored interpretation.

See [regions.md](regions.md) for deliberate differences, [source claims](../docs/research/tensura-world-2026-11-19/geography-facts.csv)
and [contradictions](../docs/research/tensura-world-2026-11-19/contradictions.md). The official image was inspected
locally outside this repo; only its link is stored here. No source art or map file is embedded.

## Verification status

The required default command was run after every SVG edit and the checker preview was inspected after each round:

```
python -I tools/world/map_check.py world/map.svg --preview world/preview.png
```

It reports **5 errors**, all old geography relations: ogre NE, Jia SW, Jia/Laura old separation, Ulgr near Blumund,
and Ulgr NW of Elmine. The owner approved anime/wiki priority; this is not a green default result.
No spacing, footprints, region coverage, water or road errors remain.

The unchanged 56-entry alternate matrix passes with **0 errors and 2 warnings**: Laura's intentional
waterfall cuts its source mountain, and the total design box is 512 blocks taller than the preferred target,
within the hard cap. The alternate matrix does not change tool behavior for other users or the normal gate.

```
python -I tools/world/map_check.py world/map.svg --relations world/canon-relations-anime.toml
```

A temporary `build.py --skip-check` run is used only for local draft terrain inspection after that explicit
geometry check. It is not acceptance, and no `--apply` is authorized or performed here. Technical reconciliation
of the five geography constraints remains required. The current requested PR is #74; older PR #69 is reference only.


## Current build and repository gate

The final local converter completed in 68.8 seconds at 3072 by 2688 pixels (4 blocks per pixel),
with **0 converter warnings**. Its normalized source SHA matches the committed SVG content. Generated
anchors match **58/58** drawn x/z coordinates; every radius meets `min_r` and all relative anchors retain
exact parent offsets. The two initial dry-mouth warnings were fixed by placing the mouths within the
16-block coastal tolerance on the sea side. Final checker preview, terrain preview and numbered atlas
were all visually inspected. This is raster validation, not Minecraft runtime acceptance.

The standard `bash` command pointed at a missing WSL shell; the same `tools/check.sh` was therefore run
with installed Git Bash. Validation reports only the five disclosed relation errors. The fast tier ran
**456 tests: 3 failures, 26 skips**, all three failures are default-map acceptance tests reporting those
same five relations. The gate is red. No tests, checker code or technical matrix were changed to hide it.
