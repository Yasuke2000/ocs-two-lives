# Research-driven map review — round 4

**Standard map checker and repository gate pass.** The PR remains a draft for source coverage and
proportional-fidelity review; passing geometry tests does not prove every canon claim or in-game acceptance.

## Current drawing

Restored the northern bay west of Canaat, introduced a southern gulf between the peninsulas and gave the
west coast a projecting tongue and inward bay. Ameld starts at `(200,-1240)`, runs south beside the northern
forest road and bends east into Siss, following the WN route and official guide inflow. The Jia trail detours
around the gulf head. The west-Jura brook drains into the new gulf. All 58 footprints/relative offsets remain.
Exact vertices are authored interpretation; [regions.md](regions.md) lists deliberate adaptations.

[Claim ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv),
[contradictions](../docs/research/tensura-world-2026-11-19/contradictions.md),
[source access](../docs/research/tensura-world-2026-11-19/source-access.csv),
[side-by-side links](comparison.md). Source images remain external links.

## Owner-authorized correction and validation

Yasuke explicitly authorized editing **only five data entries** in `tools/world/canon_relations.toml`.
They adopt the previously proposed Jia/Ulgracia/ogre placements. All other 51 relations, site rules, sea
rules, checker code and tests are unchanged. Sources now point to the proper
[design/lore note](../design/lore/world-map-corrections.md). The former alternate matrix is retained only
as proposal history and now has identical parsed data to the default matrix.

```
python -I tools/world/map_check.py world/map.svg --preview world/preview.png
python -I tools/world/build.py
bash tools/check.sh
```

- Standard map checker: **0 errors, 2 warnings**, all 56 relations pass. Warnings are Laura's intentional
  mountain-waterfall crossing and a 12288 by 10752 design box, 512 taller than preferred but below the hard cap.
- Normal build, **without `--skip-check`**: 60.5 seconds, 3072 by 2688 pixels at 4 blocks/pixel,
  **0 converter warnings**. No `--apply` performed.
- Final normalized source SHA matches the SVG. Generated anchors match **58/58** drawn x/z coordinates;
  every radius meets `min_r` and every relative anchor keeps its exact parent offset.
- Repository gate: validation passes; **456 tests pass, 26 skipped**. Installed Git Bash runs the script
  because the system `bash` points at a missing WSL shell. No tests were weakened or bypassed.
- Final checker preview, terrain preview and numbered atlas inspected visually against the linked reference.

Earlier draft runs failed the five geography rules; an intermediate run also rejected source paths outside
`design/lore/`. Those issues are resolved in the current state. Temporary draft builds used `--skip-check`
only for inspection before permission arrived; the final build uses the normal command above.

## Remaining review

Licensed LN geography passages, manga page-level evidence and exact anime timestamps remain unverified.
The official guide and author's WN chapters are distinguished in the ledger. Velgrynd's mountain bearing,
Siltrosso representation, the provisional ogre bearing and nonuniform compression remain explicit review items.
No Minecraft chunks, runtime build acceptance, pack application, merge or deployment are claimed.
