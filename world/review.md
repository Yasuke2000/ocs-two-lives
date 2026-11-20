# Current map review — round 12 scope audit; round 11 terrain, post-Kijin snapshot

Yasuke selected **immediately after the Kijin naming, anime S 1 episode 10**. [Era policy](era.md)
and [58-site state overlay](../docs/research/tensura-world-2026-11-19/era-site-state.csv) supersede mixed-era
presentation. Rimuru leads a young village; the Orc Lord conflict is unresolved. Later nation-building,
conquests, damage, construction and resident rosters are not the initial world state.

## Drawing and evidence

Round 12 adds a [126-entry mainland scope audit](../docs/research/tensura-world-2026-11-19/mainland-coverage-audit.md) and [city coverage schematic](city-coverage-study.md), with six source claims about Doran, Dwargon and Englassia. All 29 follow-ups stay open: 26 missing representations (19 mainland, 4 city/interior, 3 offshore) plus 3 existing parent designs awaiting verification. The guild, academy and elf venue already occur in local blueprints and non-empty NBT files; do not duplicate them. No production SVG or raster changes in this pass. Source confidence is not upgraded by the classification.

Round11 narrows the fixed brief's red Milim accent:707,757 to213,884 square blocks of authored polygon area (69.8% smaller). The surrounding former footprint uses default grassland/forest priorities. Red remains a server adaptation, and an inert no-red alternative is drawn under C10. All non-biome groups and all other biome polygons match the previous revision.

[Episode locator audit](../docs/research/tensura-world-2026-11-19/anime-episode-locators.csv) corrects route/episode labels and qualifies generic stills as contextual leads. All eight region-book still-routes were checked; five official episode41/no44 stills supply no city exterior plan.

Round 10 corrects Filtwood's unsupported Ulgracia-town identity. Official episode 24 names a pre-Rimuru kingdom; wiki puts it near Jura without a reliable side. The active U anchor stays fixed and is labelled disputed. [Source study](southern-location-study.md) draws an inert Jura-edge trial and a distinct depleted Orbic homeland vicinity. Exact trial geometry is interpretation; no terrain or new registered site is applied. C20 and the 58-site era overlay record the distinction.

Lake Siss now has an elongated east–west outline (about858 by410 blocks), following the official illustrated character. Exact shoreline, level and joins are our interpretation. C19 removes the false round-whirlpool premise. All 58 coordinates/radii are unchanged.

Round 9 replaces the long equal-height Canaat crest with a shorter bent high spine near the fixed Dragon Nest and a tapered eastern mountain apron (designed peak 180). This follows the official illustration's broad relief character. The first apron trial was visually rejected as too flat; the delivered apron is a mountain polygon, not a broad hill plate. Exact vertices, elevations and entrance bearings are **our interpretation**. All 58 site centres/radii, coast, rivers, lake geometry, roads and gameplay masks are retained. The preceding eastern woodland/open fringe remains.

[Empire follow-up](../docs/research/tensura-world-2026-11-19/eastern-empire-followup.md) keeps Silberia unlocated and its S1E10 state unverified. Publisher guide13.5 listing was read; the licensed trial did not render. Historical WN predecessor states and the frontier ruin are not silently turned into contemporary anime sites.

The ledger contains **178 records: 120 thematic/design/reference records plus 58 coordinate interpretations**.
Eleven directly read LN claims and nine newly read WN claims remain qualified by continuity and snapshot_use.
[WN findings](../docs/research/tensura-world-2026-11-19/wn-geography-followup.md),
[ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv),
[wiki coverage](../docs/research/tensura-world-2026-11-19/wiki-coverage.md).
The supplied official-map chapter screenshots remain reference evidence. Live chapter2 story and
World/character controls have now also been operated. The four story stops link to episodes9/12/14/15;
the episode10 naming event is not a standalone stop. Character selection opens an affiliation-area
view. This does not establish surveyed borders or make omitted countries nonexistent.
[Live verification](../docs/research/tensura-world-2026-11-19/official-interactive-map.md).

## Verification and exact limits

- Standard checker after each SVG edit: **0 errors, all 56 relations pass**, two disclosed warnings:
  Laura waterfall crosses its escarpment; box 12288 by 10752 is 512 above preferred height, below the hard cap.
  Mainland about 9653 by 6250; 10 mountains, 6 hills, 12 forests and 14 biome polygons.
- Latest verified normal converter build of the **current SVG** (retained from round 11): **52.6 seconds, no warnings**, 3072 by 2688
  pixels. All current labels/comments and preceding terrain revisions are included. The source SHA matches staging;
  published terrain-preview bytes match the fresh output. Earlier permission limitations are resolved.
- **58/58** centres verified against index.json; sites.json contains only the 34 runtime plate entries,
  not every marker. All 178 claim IDs are unique and carry snapshot qualification; all 58 sites have era rows.
- Actual current exported profiles: **21 roads, maximum grade 0.5** within float epsilon. Road geometry
  is unchanged; current bridge metadata has a 24-block maximum.
- Raster footprint check: Siss water1804/1804 pixels; lizardmen intentional water plate710/710 at level66
  (`sites.toml` surface=water, for stilt construction); cave dry0/1116 wet pixels.
- Current terrain samples: Dragon Nest surface 272; eastern-spur transect 91.6–109.5. These are
  server raster readings, not canonical elevations. Dwargon/carve reservations export without warnings.
- Only the red biome polygon changes physical design. Current wooded-badlands raster: 13374 cells;
  a representative released point(4034,614) is plains. These are design-raster readings, not canon shares.
  C20/Orbic and no-red alternatives remain inert.
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
