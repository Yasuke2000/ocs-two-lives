# Research-driven map review — round 5

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
- Normal build, **without `--skip-check`**: 54.2 seconds, 3072 by 2688 pixels at 4 blocks/pixel,
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

Eleven geographic claims are now directly verified in publisher-hosted LN2/3/5/6/10 fragments.
Further LN passages, manga page-level evidence and exact anime timestamps remain unverified.
The official guide and author's WN chapters are distinguished in the ledger. Velgrynd's mountain bearing,
Siltrosso representation, the provisional ogre bearing and nonuniform compression remain explicit review items.
No Minecraft chunks, runtime build acceptance, pack application, merge or deployment are claimed.


## Round 5 evidence and interpretation review

[Publisher LN findings](../docs/research/tensura-world-2026-11-19/ln-sample-findings.md) add eleven direct
claims. The ledger has **122 records: 64 thematic/design records and 58 site-coordinate interpretations**;
this is not a claim of 122 independently verified canon facts.

The S/U border moves to about y2720 so Ulgr Nature Park lies in northern Ulgracia, as the official guide
states. All 58 coordinates/footprints stay fixed. The atlas no longer conflates that park with Galut and
labels Shia/Siltrosso's independent political status separately from gameplay F coverage.

C05/C06 alternatives are drawn in an inert SVG comment and in the [review diagram](lore-alternatives.png).
The north-mountain bearing is secondary evidence, and the independent-state outline is illustrative.
No unconfirmed alternative is applied to terrain or smuggled into a new region letter.

The standard checker still passes with 0 errors/2 disclosed warnings. Normal build: 54.2s, no converter
warnings, matching source SHA, 58 coordinate/radius/relative-offset checks pass. Final preview, numbered
atlas and review diagram inspected. Full repository gate passes validation and 456 tests (26 skips).
The technical matrix is unchanged from the previous owner-approved five-entry correction.

Fetched current main (`a1848be`) before submission; its intervening commits do not change the world
format, site-size table, map tools or relation matrix. Integration into this branch is checked separately.


## Integration and proportion benchmark

Integrated main `a1848be` on the map branch, preserving both sides of the two append-only documentation
conflicts. No upstream technical code was edited by hand. The integrated gate passes validation and
**462 tests (26 skips)**. Relative to current main, the only technical file changed remains the five
owner-authorized entries in `tools/world/canon_relations.toml`.

[Fourteen-site proportion audit](proportion-audit.md) records differences from the supplied secondary
marker reference. Normalizing to Tempest–Siss exposes particularly large western-distance differences.
This is a diagnostic benchmark with an unknown illustration projection, not a surveyed canon map.
Further proportional revision remains necessary; a passing checker alone does not complete that review.
