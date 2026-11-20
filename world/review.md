# Current map review — round 7, post-Kijin snapshot

Yasuke selected **immediately after the Kijin naming, anime S 1 episode 10**. [Era policy](era.md)
and [58-site state overlay](../docs/research/tensura-world-2026-11-19/era-site-state.csv) supersede mixed-era
presentation. Rimuru leads a young village; the Orc Lord conflict is unresolved. Later nation-building,
conquests, damage, construction and resident rosters are not the initial world state.

## Drawing and evidence

The live map adds irregular light woodland north of Siss toward the eastern Canaat foothills and an open
fringe toward the Empire. Exact habitat outlines are **our interpretation**. No new military ruin position,
road, sovereign frontier, river or height is invented. Coast and all 58 registered site positions are retained.
The atlas uses the early village label and calls the footprints terrain reservations.

The ledger contains **159 records: 101 thematic/design/reference records plus 58 coordinate interpretations**.
Eleven directly read LN claims and nine newly read WN claims remain qualified by continuity and snapshot_use.
[WN findings](../docs/research/tensura-world-2026-11-19/wn-geography-followup.md),
[ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv),
[wiki coverage](../docs/research/tensura-world-2026-11-19/wiki-coverage.md).
Supplied official-map chapter screenshots were inspected separately from live controls. Early/later markers
are not conflated, and unexplained highlights are not treated as timeless sovereign borders. Direct web
retrieval exceeded the content limit; a local live-page request was declined. Live controls were not operated.

## Verification and exact limits

- Standard checker after each SVG edit: **0 errors, all 56 relations pass**, two disclosed warnings:
  Laura waterfall crosses its escarpment; box 12288 by 10752 is 512 above preferred height, below the hard cap.
  Mainland about 9653 by 6250; 12 forests and 14 biome polygons.
- Latest successful normal converter: **53.9 seconds, no warnings**, 3072 by 2688 pixels. This includes the
  eastern habitat edits. A requested repeat after era-only metadata was declined (tool returned
  `rejected by user`, with no explanatory reason). No generated index was patched or bypass used.
- Current raw SVG SHA differs from staging. Removing only C18 comment/root data-era and restoring two
  cosmetic labels reconstructs the exact staged SHA. Active geographic geometry matches that successful
  build. This does not turn an earlier run into a claimed rerun.
- **58/58** centres verified against index.json; sites.json contains only the 34 runtime plate entries,
  not every marker. All 159 claim IDs are unique and carry snapshot qualification; all 58 sites have era rows.
- Actual current exported profiles: **21 roads, maximum grade 0.5** within float epsilon. Road geometry
  is unchanged; the earlier measured 24-block bridge maximum remains unchanged-route evidence.
- Repository gate: validation passes, **462 tests,26 skips,0 failures**.
- Checker preview, numbered atlas and side-by-side official-base comparison visually inspected. Copyrighted
  reference art remains outside the repository; [comparison](comparison.md) links the official source.

No apply, Minecraft chunks, in-game acceptance, main merge or server deployment is claimed.

## Remaining fidelity decisions

[Additional proposals](additional-locations.md) remain inert. C14 exposes Sainte-Malukshure's H/Fulbrosia
anchor conflict; C15 separates new locations from the 58-site contract; C16 keeps WN Tengu access distinct;
C17 flags Englassia's lake/castle interior. C18 distinguishes the early village/trails from mandatory
future-ready road metadata and later content capacity. Runtime era gating is not implemented.
[Proportion alternatives](proportion-study.png) retain unresolved fixed-range distortions.
Only the five explicitly approved TOML relation entries are changed in tools/. The 126-entry wiki inventory
still contains missing or uncertain places; neither the complete wiki nor the faithful-continent goal is finished.
