# Region book — anime-led Minecraft world

This book accompanies `world/map.svg`. Heights are proposed Minecraft y values, not measured terrain. Biome percentages are **art-direction targets**, sum to 100 per region, and are not claimed raster statistics. Every unverified boundary, elevation, palette, architectural detail and habitat share is **our interpretation**. Yasuke now prefers anime/wiki geography where the older server brief differs. The SVG and its validated site geometry govern conversion; this book must not silently override them.

## Research round 4 — source traceability and deliberate differences

Read [geography-facts.csv](../docs/research/tensura-world-2026-11-19/geography-facts.csv) and
[contradictions](../docs/research/tensura-world-2026-11-19/contradictions.md) for evidence, continuity and access limits.
The `SITE-*` rows record all 58 exact placements as **our interpretation**, not canonical measurements.
The thematic `OFF-*`, `WN13-*`, `WN31-*`, `MAP-*` and `FAN-*` rows distinguish direct evidence from secondary references.
All numeric heights, habitat percentages, drawn borders, road corridors and shoreline vertices below are
**our interpretation** unless a specific evidence row says otherwise. Mood stills do not prove geography.

Compared visually with the [official introductory map](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp):

- Restored the northern bay west of Canaat (`MAP-002`), rather than a nearly continuous full northern shore.
  Its depth and exact outline are adapted to the Falmuth/Siltrosso footprints.
- Added the deep southern gulf between the Sarion/Ulgracia peninsula and the Fulbrosia/Eurazania side (`MAP-004`).
  The Fulbrosia trail detours around the head of the gulf; it does not become a long sea bridge.
- The west coast now has an inward bay and a projecting land tongue. Its exact indentations are original,
  and the western body remains broader and smoother than the official silhouette to fit the required western sites.
- Ameld now starts at `(200,-1240)`, near the dwarven foothills, runs south beside the northern forest road,
  then bends east into Siss (`WN13-003..004`, `WN31-002..003`, `OFF-001`). The guide establishes the lake inflow;
  the WN establishes the route, not these coordinates. The LN version has not been directly verified.
- The invented west-Jura brook now drains into the newly drawn gulf. Habitat polygons and Ulgr's bluff
  are clipped to the new coast. These are hydrological/design adaptations, not new canon claims.
- The server requires Dwargon due north and Nasca at least x3000. Consequently the atlas is **not a uniform
  scaled copy** of official point spacing. Northern relief is wider and the eastern lowland is expanded.
- Islands are compressed to the fixed design box, not a claim of faithful world-scale island size.
  The mainland is about 9653 by 6250 blocks; the total design box is 12288 by 10752, 512 taller than the preferred target.
- The fixed deadly forest rings, arrival clearing, Treyni shrine, Spirit Gate by Tempest, minor camps and
  specific biomes are server content. In particular the guide places the Spirit Dwelling entrance in northern
  Ulgracia (`OFF-005..006`); the near-Tempest portal is a separate server adaptation.
- Yasuke explicitly approved updating the five default data rules for Jia, Ulgracia and the ogre ruin.
  The standard map checker now passes; the map remains a draft for source/fidelity review.

Borders in this book are gameplay coverage polygons. No precise sovereign boundary, independent-state
subordination or early/late-story political continuity can be inferred from them. C05 (Velgrynd's mountain
bearing) and C06 (Siltrosso representation) remain open; source detail is insufficient to replace the fixed constraints.

## LN evidence and unresolved alternatives — round 5

Eleven directly read publisher-hosted LN claims (`LN02-*`, `LN03-*`, `LN05-*`, `LN06-*`, `LN10-*`)
now strengthen the ledger; [passage access and limits](../docs/research/tensura-world-2026-11-19/ln-sample-findings.md).
They support Frey's Jura adjacency, Carrion's mountain backdrop, the sacred stair approach and Amrita's
ruin/surface distinction. Exact bearings and heights remain interpretation.

The official guide puts Ulgr Nature Park in northernmost Ulgracia. Its marker is **not Galut**.
The authored S/U boundary now passes about y2720, placing the unchanged park near Ulgracia's northern edge.
This border course is **our interpretation**; the park's separate northern location is source-supported.

[Review diagram](lore-alternatives.png) and [editable version](lore-alternatives.svg) show C05/C06.
The north-of-Nasca mountain trial and an illustrative independent Siltrosso polygon are drawn inside
an **inert comment in map.svg**, as requested when source geography and fixed rules conflict.
They do not alter terrain. Siltrosso's capital is labelled Shia, independently of the F gameplay mask.
No surveyed political boundary or primary-confirmed volcano bearing is invented.

## Proportions, coast and safe approaches — round 6

The current [before/after benchmark](proportion-audit.csv) compares secondary marker proportions, not surveyed canon:

| Site | Previous centre | Current centre | Distance-ratio discrepancy before → after |
| --- | --- | --- | --- |
| Blumund | (-1900,-300) | (-1500,-620) | +57.4% → +32.8% |
| Marris / Falmuth | (-2600,-1700) | (-1800,-1650) | +41.8% → +11.4% |
| Sealed Cave | (-260,-430) | (-120,-400) | +24.3% → +3.3% |

The bay bank, Shia landing (-2297,-1370), western road junctions and
cave hill move with those placements. The brook stays west of the cave footprint; all 1116 sampled
footprint pixels are dry in the final water raster. These exact placements and watercourse choices are
**our interpretation**, constrained by build sizes and fixed travel ranges.

The northeastern shore now has the reference's recognizable hooked inlet; an eastern bay replaces the
previous rounded edge. Exact vertices are authored interpretation. The P/M gameplay boundary moves to
about y-400 so the coastal tongue remains connected; no surveyed sovereign frontier is claimed.
The continent is about 9653 × 6250 blocks. All 58 IDs, footprint minima and internal offsets remain.

The [reference-scaled study](proportion-study.png) is also drawn inside `map.svg` comments. At the common
Tempest–Siss scale, the reference Blumund distance is about 1223 blocks versus the fixed minimum of 1600;
the reference Dwargon point exceeds both the fixed 1600 maximum and north-bearing tolerance. These
alternatives are **our interpretation of secondary marker geometry**, not primary-confirmed coordinates.
The active map keeps the fixed rules, and the PR makes this deliberate distortion explicit.

Climb routes retain the sketched corridors with short constructed landings. All 21 exported road profiles
now respect the 1:2 grade limit; the longest generated bridge run is 24 blocks. This validates
the delivered road data, not an in-game acceptance claim.

## Source and era policy

The official guide and episode stills are reference links only; no official artwork is copied into this repository. Still links were extracted from the corresponding official episode pages on 19/11/2026; they provide shared series visual vocabulary and do not necessarily depict every minor nation. Where a place has no verified dedicated canonical image, the linked stills are mood references, not geographic evidence. Canon summaries below are paraphrases of the repo lore and the primary guide.

**Owner-selected initial snapshot: immediately after the Kijin naming, anime S1 episode 10.** Rimuru leads a young village; the later federation/metropolis and postwar political changes are not the initial state. Existing faraway capitals remain, but later construction/events are reservations. See [era policy](era.md) and the [58-site state overlay](../docs/research/tensura-world-2026-11-19/era-site-state.csv). Charybdis's Siss arena remains a server reservation, not an event already completed.

## J — Jura Forest / Rimuru's village (gameplay J)

**Landform and heights.** Temperate lowlands 68–88; rocky shoulders 95–105. Tempest grows beside the west brook inside a small clearing. The road rises north through the safe rim to the Canaat apron.

**Target biome mix.** `tensura:ancient_forest` 20%, `minecraft:dark_forest` 40%, `minecraft:forest` 25%, `minecraft:plains` 10%, `minecraft:meadow` 5%.

**Palette, vegetation and crossings.** Sage and deep green, blue-grey bark, warm oak clearings. Open farmland gives way to an interlocked canopy; southeast paths disappear into Treyni’s old wood.

**Canon basis and interpretation.** Dwargon is north of Jura, Siss east, and Tempest stands in a forest clearing with running water. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 9, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img1.jpg), [episode 9, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img2.jpg).

**Anime frames actually inspected.** [rimuru city](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/rimuru_city.webp), [sealed cave](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/sealed_cave.webp), [khusha mountains](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/khusha_mountains.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md). The later planned Rimuru-city frame is visual context only; the initial village follows episode9/10 references in [era.md](era.md).

## D — Armed Nation of Dwargon

**Landform and heights.** Grey alpine core to y280; lower eastern mountain spurs to y180, with foothill approaches around75–145. A south-facing escarpment frames the gate. A ravine frames the entrance. The summit shoulder carries the Dragon’s Nest; natural ridges continue above the buried city.

**Target biome mix.** `minecraft:stony_peaks` 40%, `minecraft:meadow` 25%, `minecraft:windswept_gravelly_hills` 20%, `minecraft:forest` 10%, `minecraft:jagged_peaks` 5%.

**Palette, vegetation and crossings.** Tuff grey, warm yellow and anvil red. Forest thins to meadow and stone; gate lanterns replace daylight beneath the mountain.

**Canon basis and interpretation.** Dwargon occupies a natural cavern at the foot of the Canaat Mountains; the south-facing gate and exact ravine are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 4, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img1.jpg), [episode 4, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img2.jpg).

**Anime frames actually inspected.** [dwargon gate](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/dwargon_gate.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## W — Lake Siss marsh

**Landform and heights.** An elongated basin about858 by410 blocks, lake level66 and depth12; reed shores68–74 and limestone above the southern caverns to103. The Ameld enters from the north and exits on the east before turning southeast. These dimensions/heights and exact joins are our interpretation.

**Target biome mix.** `minecraft:swamp` 60%, `minecraft:mangrove_swamp` 10%, `minecraft:plains` 20%, `minecraft:forest` 10%.

**Palette, vegetation and crossings.** Teal water, green reeds, pale limestone and weathered timber. Dry woodland opens into reed bays and flooded roots, then rises to a dry orc battlefield.

**Canon basis and interpretation.** The official guide identifies Siss in Jura and the Ameld flowing into it; episode 10 places the lizardmen in its wetlands. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 10, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no10/img1.jpg), [episode 10, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no10/img2.jpg).

**Anime frames actually inspected.** [lake siss](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/lake_siss.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## R — Kingdom of Blumund

**Landform and heights.** Low agricultural ground 68–82, with Londo on a dry trade terrace. Jura is connected by land; the west road reaches Ballachia and Englassia.

**Target biome mix.** `minecraft:plains` 65%, `minecraft:forest` 20%, `minecraft:flower_forest` 10%, `minecraft:meadow` 5%.

**Palette, vegetation and crossings.** Cream masonry, red cloth, grain gold and orchard green. The traveller leaves the heavy canopy for fields and a small walled market capital.

**Canon basis and interpretation.** Blumund is Jura’s western human neighbour; the dry land connection is retained from the reference geography. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

**Anime frames actually inspected.** [londo](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## G — Kingdom of Englassia

**Landform and heights.** Broad west-country river plains 65–85; low groves along the guild road. Lura and Ballachia remain compact, separated by agricultural country.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:forest` 25%, `minecraft:birch_forest` 15%, `minecraft:flower_forest` 5%.

**Palette, vegetation and crossings.** Slate, pale stone, navy banners and oxidized copper. Lanes widen toward the guild and academy; the western ridge closes the horizon beyond Lura.

**Canon basis and interpretation.** The official guide names Englassia a western cultural centre and the seat of the Free Guild headquarters. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## F — Kingdom of Falmuth

**Landform and heights.** Northern coastal lowlands 65–90. Marris sits inland behind Siltrosso’s coastal arm; the eastward land route reaches the Canaat gate.

**Target biome mix.** `minecraft:plains` 60%, `minecraft:meadow` 20%, `minecraft:forest` 15%, `minecraft:windswept_hills` 5%.

**Palette, vegetation and crossings.** Blue and white, pale stone and green copper. Grain fields become exposed coastal grass; roads converge at a guarded commercial town.

**Canon basis and interpretation.** Falmuth is a western trade gateway west of Dwargon and north of Blumund; exact coast and harbours are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## L — Holy Empire of Lubelius

**Landform and heights.** Western ridge to 205, with Lune on a terrace at its foot. The sacred approach climbs a separate trail toward the mountain sanctuary.

**Target biome mix.** `minecraft:windswept_hills` 30%, `minecraft:meadow` 30%, `minecraft:plains` 20%, `minecraft:forest` 15%, `minecraft:stony_peaks` 5%.

**Palette, vegetation and crossings.** Ivory, muted gold, pale blue and cool stone. Open farms tighten into terraced slopes and a ceremonial stair beneath a grey ridge.

**Canon basis and interpretation.** The pack locates Lubelius northwest of Jura and its sacred sanctuary above Lune. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 39, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no42/img1.jpg), [episode 39, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no42/img2.jpg).

## V — Damargania / western wastes

**Landform and heights.** Arid west lowlands 65–100; Coleus has a bounded oasis at level75. Desert gives way to a separate barren belt around the Heaven Tower.

**Target biome mix.** `tensura:desert_of_death` 45%, `minecraft:desert` 25%, `tensura:barren_land` 25%, `minecraft:windswept_gravelly_hills` 5%.

**Palette, vegetation and crossings.** Ochre, chalk, pale sand and ash grey. Green caravan roads end at a small oasis; farther west the horizon is bare and weathered.

**Canon basis and interpretation.** Damargania is the far-west barren territory; the oasis layout and desert transitions are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## O — Morgdahl

**Landform and heights.** Western river-bank lowland 65–78; slightly raised wharves and a dry landing approach.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:forest` 25%, `minecraft:meadow` 15%, `minecraft:swamp` 5%.

**Palette, vegetation and crossings.** Wet slate, river blue and willow green. The western road follows the river through landing fields rather than cutting across a mountain.

**Canon basis and interpretation.** The repo places Morgdahl in the western river belt; the settlement form is our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## A — Raja

**Landform and heights.** Small cultivated basin 70–85 with a rimmed lake at level72. Rostia stays on the northern approach rather than inside the water.

**Target biome mix.** `minecraft:plains` 50%, `minecraft:forest` 25%, `minecraft:meadow` 20%, `minecraft:swamp` 5%.

**Palette, vegetation and crossings.** Lake blue, earth brown and soft green. Hedges open toward a still inland lake and a modest waterside town.

**Canon basis and interpretation.** The pack places Raja west of Tempest in the small-state belt; its exact lake and gardens are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## N — Nostraille

**Landform and heights.** Gentle valley floor 70–90 between the western river landing and Yuzalgh.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:meadow` 25%, `minecraft:forest` 20%.

**Palette, vegetation and crossings.** Muted greens, timber brown and pale stone. Small tilled fields alternate with low wooded shoulders.

**Canon basis and interpretation.** The repo’s west-to-east ordering places Nostraille east of Morgdahl and west of Yuzalgh. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## Y — Yuzalgh

**Landform and heights.** Narrow lowland state 70–90 with an uninterrupted through-road.

**Target biome mix.** `minecraft:plains` 65%, `minecraft:forest` 20%, `minecraft:meadow` 15%.

**Palette, vegetation and crossings.** Field green and grey-brown boundary stone. A traveller crosses a shallow valley and clustered farms without encountering a defensive sea gap.

**Canon basis and interpretation.** Yuzalgh belongs in the western sequence east of Nostraille; its architecture and borders are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## Q — Yggdonia

**Landform and heights.** Small birch country 72–90 between the western towns and Blumund’s southern edge.

**Target biome mix.** `minecraft:birch_forest` 55%, `minecraft:plains` 30%, `minecraft:flower_forest` 15%.

**Palette, vegetation and crossings.** White bark, pale green and straw. A light canopy softens the transition from town fields to Jura’s darker woodland.

**Canon basis and interpretation.** Yggdonia’s position and birch identity are pack interpretation, not independently established canon. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## U — Ulgracia

**Landform and heights.** Wooded coastal bluff to112, south of Sarion. Galut’s spring sits at102 with a contained rim; the brook descends to the southern coast.

**Target biome mix.** `minecraft:forest` 35%, `minecraft:dark_forest` 25%, `minecraft:old_growth_birch_forest` 20%, `minecraft:plains` 20%.

**Palette, vegetation and crossings.** Moss green, silver water and weathered rock. The southbound road leaves Sarion’s forest and climbs onto a wooded coastal overlook.

**Canon basis and interpretation.** The official guide and supplied reference place Ulgracia south of Sarion. Yasuke explicitly chose this over the earlier Blumund-adjacent server liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## S — Sorcerous Dynasty of Sarion

**Landform and heights.** Southwestern forest peninsula 70–105, shaped around the river and one colossal Divine Tree at Elmine.

**Target biome mix.** `minecraft:forest` 35%, `minecraft:dark_forest` 25%, `minecraft:old_growth_birch_forest` 25%, `minecraft:flower_forest` 10%, `minecraft:plains` 5%.

**Palette, vegetation and crossings.** Gold-green canopy, ivory wood and quiet water. Deep forest opens into a living-tree city; the river runs beside, not through, its dry site.

**Canon basis and interpretation.** Sarion lies on Jura’s southern border; the single colossal tree and its waterside setting follow the supplied anime frame; exact build and size are our playable interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 26, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no28/img1.jpg), [episode 26, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no28/img2.jpg).

**Anime frames actually inspected.** [elmine](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/elmine.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## H — Harpy Queendom of Fulbrosia

**Landform and heights.** Southern spire country rising to235, between Sarion and Eurazania. Jia occupies ledges on a high, narrow rock pillar, with a winding ascent. The supplied anime still shows cliff dwellings rather than a conventional flat town.

**Target biome mix.** `minecraft:stony_peaks` 40%, `minecraft:windswept_forest` 25%, `minecraft:meadow` 25%, `minecraft:jagged_peaks` 10%.

**Palette, vegetation and crossings.** Cool stone, muted violet shadow and highland grass. Low fields give way to exposed ledges and wind-swept platforms.

**Canon basis and interpretation.** Frey’s territory lies south of Jura in the supplied reference, west/southwest of Eurazania. This supersedes the earlier far-southwest mesa liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 28, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img1.jpg), [episode 28, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img2.jpg).

**Anime frames actually inspected.** [jia](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/jia.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## B — Beast Kingdom of Eurazania

**Landform and heights.** Southeastern peninsula 68–100 with orchards and Laura’s dry clearing in jungle country. A north-facing escarpment behind Laura rises to225, with a headwater basin at154 feeding a stepped waterfall river past the dry city site.

**Target biome mix.** `minecraft:jungle` 60%, `minecraft:sparse_jungle` 20%, `minecraft:plains` 15%, `minecraft:bamboo_jungle` 5%.

**Palette, vegetation and crossings.** Jungle green, golden fruit, brown timber and thatch. Reeds recede behind low wooded ridges and cultivated fruit groves.

**Canon basis and interpretation.** Eurazania lies south/southeast of Jura. LN5 supports the castle mountain backdrop and town below (`LN05-001..002`). The supplied Laura frame shows the waterfall; the wiki excerpt describes fruit plantations. Exact waterfall reaches and playable elevations are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 28, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img1.jpg), [episode 28, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img2.jpg).

**Anime frames actually inspected.** [laura](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/laura.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## M — Milim's old domain

**Landform and heights.** Eastern lowlands65–90 with a narrow red crescent retained solely as the fixed brief's server accent. The large former red-biome footprint is reduced from707,757 to213,884 square blocks of authored polygon area (69.8% smaller). Surrounding land follows existing default grassland/forest priorities. No new hill, river or settlement is added.

**Target biome mix (our interpretation).** `minecraft:plains`85%, `minecraft:wooded_badlands`10%, `minecraft:forest`5%. These are palette targets, not measured raster percentages or canonical biome shares. The red biome remains a server adaptation, not evidence of an arid country.

**Palette, vegetation and crossings.** Green lowlands and established woodland, with a restrained warm-soil accent near the eastern coast. Exact tree species, settlement palette and field layout remain interpretation.

**Canon basis and limits.** The official guide identifies Milim's old dragonewt settlement and its unusual social organisation; it does not define a red desert. The official illustrated map is a broad visual reference, not a biome survey. The fixed [brief](../design/architecture/own-world.md) explicitly retains some red badlands. C10 now draws an inert grassland replacement for the former large footprint, so the remaining design liberty is visible. No later annexation or new castle is treated as initial geography.

**References.** [Official world guide](https://www.ten-sura.com/map), [official base image](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp), [city source notes](../design/lore/forgotten_dragon_city.md). Official episode41 is at [route no44](https://www.ten-sura.com/anime/tensura/story/no44); its five inspected stills do not establish a city exterior or biome footprint. The pinned fan metadata's city frame could not be re-fetched this round, so its episode attribution remains secondary.

## P — Jistav

**Landform and heights.** Northeastern dark-wood basin 72–95, castle on a dry site beside its separate moat; the separate Amrita ruin footprint uses an authored low mound to93.

**Target biome mix.** `minecraft:dark_forest` 60%, `minecraft:forest` 20%, `minecraft:plains` 15%, `tensura:miasmic_plains` 5%.

**Palette, vegetation and crossings.** Deep green, muted violet, grey stone and cold lantern light. The road enters a closed canopy before reaching the castle clearing and eastern ruin.

**Canon basis and interpretation.** The official guide identifies Jistav as Clayman’s territory. LN10 distinguishes Amrita from the surface city and older Soma homeland (`LN10-001..003`); official episode81 explicitly places the ruins beneath the former castle (`OFF-AMR-001`). The separate eastern circle is a mandatory game reservation under C07, not a verified independent surface entrance. An inert castle-linked access projection is drawn; exact depth/full footprint/entrance coordinates remain unknown and eastern chambers remain possible. Basin, moat and external mound are authored. [Access/reservation study](amrita-placement-review.md) · [existing lore](../design/lore/world.md) · [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 45, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 45, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

**Anime frames actually inspected.** [amrita](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/amrita.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## E — Eastern Empire

**Landform and heights.** Far-eastern northern valley 75–110, with Nasca north of a volcanic sanctuary rising to250.

**Target biome mix.** `minecraft:plains` 45%, `minecraft:forest` 25%, `minecraft:meadow` 15%, `minecraft:stony_peaks` 10%, `minecraft:badlands` 5%.

**Palette, vegetation and crossings.** Dark green roofs, red devices, copper and amber glass. Open plains are interrupted by long volcanic spurs rather than a continuous impassable wall.

**Canon basis and interpretation.** The Empire occupies the far northeast; the brief fixes Nasca’s valley north of Velgrynd’s volcano. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 45, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 45, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## I — Ice Continent

**Landform and heights.** Separate frozen island, 900–1,200 blocks of sea from the mainland; low ice ledges rise toward a210 spine. Frost Palace occupies the southern coastal plate.

**Target biome mix.** `minecraft:snowy_plains` 60%, `minecraft:frozen_peaks` 20%, `minecraft:snowy_slopes` 15%, `minecraft:ice_spikes` 5%.

**Palette, vegetation and crossings.** Blue ice, white rock and violet lights. A cold crossing ends at a coastal palace below an empty frozen interior.

**Canon basis and interpretation.** The Ice Continent is northern and contains Guy’s Frost Palace; the playable shoreline and causeway are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 45, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 45, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## X — El Dorado

**Landform and heights.** Separate southwest volcanic island, roughly 1,850 by1,400; Leon’s city lies northwest of the volcano, which rises to230.

**Target biome mix.** `minecraft:plains` 45%, `minecraft:meadow` 20%, `minecraft:forest` 20%, `minecraft:stony_peaks` 10%, `minecraft:flower_forest` 5%.

**Palette, vegetation and crossings.** White and gold, green foothills, black volcanic stone and purple-red interiors. The sea crossing reaches a sheltered city plain below the caldera.

**Canon basis and interpretation.** El Dorado lies on a southwestern continent; its playable island compression is an explicit owner liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Reference links (stills are contextual leads unless separately verified).** [official world guide](https://www.ten-sura.com/map), [episode 45, still 1; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 45, still 2; contextual lead](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## Open lore and implementation questions

- The owner explicitly reversed the earlier Fulbrosia and Ulgracia liberties. The anime-aligned positions are now adopted into the five owner-approved default data rules.
- Several small-state identities and capital names rely on secondary repo research. No new flags, rulers or political borders are asserted as verified canon here.
- Drawn site radii now meet all footprint minima from `world/sites.toml`, including Tempest r148 and Dwargon r127. Relative internal anchors remain within their parent complexes. Final in-game ground, cover and water containment still need technical acceptance.
- Treyni’s shrine is an original pack interpretation; the separated grove and shrine sites follow the accepted checker, replacing the old imported-world +38 offset.
- Preserve the Lerfing and Paulzero credit history for the prior world attempt. The new coast and artwork are original, with no copied paid terrain.

EN: The continent has fixed story geography; the outer ocean and free lands are generated around it.
NL: Het continent heeft vaste verhaalgeografie; de buitenste oceaan en vrije gebieden worden eromheen gegenereerd.

The ogre ruin is placed at the southeastern Khusha foothills, using the supplied wiki and pinned reference marker instead of the older northeastern guess. Siltrosso is an independent kingdom in the supplied wiki; the existing F region groups its coastal marker for game data and does not establish Falmuth sovereignty. Its separate nation metadata needs Claude’s reconciliation. The interactive reference places Velgrynd’s mountain north of Nasca, while the old server brief places it south; the supplied wiki only says adjacent. This unresolved compass detail is retained as a PR lore question, not claimed as confirmed canon.

## Additional-location source review — C14/C15

[Evidence and measured proposals](additional-locations.md), [original study](additional-location-study.png). The Galut capital, Tengu summit settlement, coastal Sainte-Malukshure, offshore Magic Tower and Long Wall corridor are drawn as inert alternatives inside map.svg. Exact coordinates and dimensions are **our interpretation**. No active geography was changed in this pass. The official Vacation manga volume-2 synopsis supports the tower in Malukshure waters; the coastal city and neighbour relationship remain wiki-qualified. The current Sainte pin is inland/east of Sarion and tied to H/Fulbrosia by anchor data. That contradiction is disclosed as C14, not called canon. The new-location proposals remain outside the fixed 58-site registry (C15).

## Eastern foothill landscape — round 7

The [direct WN follow-up](../docs/research/tensura-world-2026-11-19/wn-geography-followup.md) supports an eastern Jura frontier history; the wiki describes Eastern Plains shared by Jura and the Empire. The live drawing now adds light foothill woodland north of Siss and an irregular grassland fringe toward the eastern approach. Exact forest/plains outlines and biome choice are **our interpretation**. Geographical Jura does not have to equal the Tempest gameplay polygon. The shapes preserve the Siss marsh, mountains, roads, all 58 sites and all political masks. No frontier ruin coordinate is asserted. This deliberately fills the earlier empty transition, rather than leaving the geographical forest extent implicit in a political region name. WN102 gate access (C16) and WN56 capital water (C17) remain qualified continuity/interior matters.

## Lake Siss shape and source correction — round 8

The official illustrated basin is read as elongated east–west. The authored shore now follows that character, rather than the older round-arena premise. Bounds change from about696 by549 to858 by410 blocks. The full fixed radius96 water reservation remains inside the lake, and the southern lizardmen access is preserved. Northern inlet and eastern outlet joins move with the shore. All 58 site coordinates, roads and region masks are retained. Exact vertices and dimensions are **our interpretation**. C19 corrects the older aquatic-whirlpool claim: the official glossary describes Charybdis as an aerial calamity; any lake arena is later server adaptation, not a physical-geography source.

## Canaat relief and Empire evidence — round 9

The official illustrated relief is read as a concentrated northern summit mass with a southern foot and lower lateral spurs. The earlier authored crest spanned 2240 blocks horizontally at a single specified 280-block height. It has been replaced by a shorter bent crest around the fixed Dragon Nest, a more compact high core, and a separate tapered eastern mountain polygon with peak 180. No broad flat hill plateau is used for the eastern spurs. The mountain footprint and all elevations are **our interpretation**, not surveyed canon. The image supplies broad massing only (MAP-CANAAT-001/DES-CANAAT-003).

All 58 site centres/radii, the coastline, lakes, rivers, roads, gameplay masks and the post-Kijin snapshot are retained. The Ameld headwater marker stays at the southern foot outside the mountain polygon. Exact entrance bearings and valley positions remain interpretations. Road profiles and underground reservations are verified against the new staging output in [review](review.md).

The [Empire follow-up](../docs/research/tensura-world-2026-11-19/eastern-empire-followup.md) keeps Silberia as an unlocated research gap. Wiki political membership is not a geographical coordinate or a reliable S1E10 survival date. The publisher confirms guide 13.5 includes the lakeshore story, but its trial did not load. No unread passage, unnamed city grid or present-day Namrium/Ulmeria capital is invented. Eastern settlement and interior coverage remains incomplete.

## Filtwood and Orbic — round 10 source correction

[New source/constraint diagram](southern-location-study.png) separates the active Filtwood U anchor from an illustrative Jura-edge alternative, and the depleted Orc homeland from the Siss battlefield. C20 corrects the unsupported Ulgracia-town claim: official episode 24 names a kingdom in a pre-Rimuru story; wiki supplies only Jura proximity. The exact side of Jura remains unknown. All trial coordinates and the Orbic vicinity outline are **our interpretation**. Neither alternative is active terrain or a new sovereign region. Detailed evidence and era limits are in [the study](southern-location-study.md).

All live terrain and registered sites remain unchanged in this round; only the disputed Filtwood label and inert comment are added. Do not relocate the production anchor without reconciling its required U binding, or use the homeland study as a source-confirmed capital plan.

## Biome scope and anime locators — round 11

C10 retains the brief's red accent while reducing its unverified authored extent by69.8%. A no-red alternative is drawn in an inert SVG comment rather than silently breaking the brief. All58 sites/radii, coasts, relief, waters, roads and gameplay masks remain fixed. Exact soil/biome choices are **our interpretation**; this revision does not assert that absent evidence proves a particular canonical ecosystem.

The [episode-locator audit](../docs/research/tensura-world-2026-11-19/anime-episode-locators.csv) checks every distinct official still-route used in this region book. Recap/special entries mean the route number can differ from the displayed episode. Labels now match the official header: no28=episode26, no30=28, no42=39 and no48=45. Generic still links are explicitly contextual leads, not proof of each region's terrain. This corrects overconfident image attribution without inventing timestamps or exterior views.

## Rounded river bends — round 13

The two Great Ameld reaches, Tempest's upper brook, the Jura–Sarion river and the western trade river now have rounded bends instead of long sharp joins. The [plan measurements](river-centreline-review.csv) compare the authored lines with commit9c71909. Maximum deviation is14.17 blocks; every former control point and endpoint, source/mouth level and width is retained. No new river, valley, lake, story location or country border is inferred.

These exact channels remain **our interpretation** under the existing C03 continuity limits. The interpolated vertices improve the physical drawing, rather than claim a surveyed canonical meander. The Raja stream, Ulgr spring and Laura waterfall are unchanged. All58 site centres/radii, coasts, relief, biomes and region masks are retained. One western trail approach gains a waypoint within20 blocks of its old line, keeping all former route points/endpoints and correcting an exported climb overshoot (DES-ROAD-013); final water/bridge/site checks are recorded in [review](review.md).

## Sarion proportion refinement — round 14

Round 14 moves Elmine from (-1100,1800) to (-1680,1740), retaining its 100-block radius and all fixed relations. Relative to the pinned fan marker pattern, its Siss-normalized distance discrepancy improves from -13.0% to -0.3% and bearing discrepancy from -17.5 to -4.9 degrees. Unknown projection and marker precision limit this comparison: exact server coordinates remain our interpretation. The pond follows the city (-580,-60); the hill shifts (-480,-60) to remain on the existing coast. Three trails approach the north edge and skirt the pond. The other 57 site centres/radii, coast, rivers, mountains, forests, biomes and gameplay regions remain unchanged from a2748f3.

Validation: all 56 relations pass, no checker errors and the same two disclosed warnings. Fresh normal export: 54.6 seconds, no converter warnings; all 21 actual road grades <=0.5 (floating-point tolerance), longest bridge 40 blocks. Elmine is dry over all 1,976 sampled footprint pixels. No terrain apply or in-game validation.

## Coleus official-source placement correction — round 15

Round 15 corrects Coleus using the directly read official anime outline: the independent kingdom lies between Ingrassia and Lubelius. Its authored centre moves from(-3650,-250) to(-3520,-860), retaining radius73, V membership and all fixed relations. The dunes move(+130,-610); the oasis moves(-175,-610), keeping water separate from the city and river. One caravan trail skirts the pond on its north side. The other57 site centres/radii, coasts, rivers, mountains, hills, forests and gameplay masks remain unchanged from147ea7e. Exact city position, shore/level and trail bends remain our interpretation; countries lying between others does not survey their capitals.

The official INEI concept board shows the palace hill, lower town and oasis setting. Existing blueprints/coleus.py already builds an original sandstone hill and approach, so no duplicate hill terrain is added. The concept is later OVA design evidence, not a measured plan or S1E10 building-state guarantee. Country sovereignty is independent; gameplay V is only its existing terrain binding. No invented sovereign border is drawn. [Source/fit review](../docs/research/tensura-world-2026-11-19/coleus-placement-review.md).

## Old Dragon City southeastern proportion correction — round 16

Round 16 moves the old Forgotten Dragon City from(2500,150) to(2650,800), retaining radius100, M membership and all fixed relations. This follows the official illustration's broad southeastern pattern and the wiki territory relationship south of Jura/east of Eurazania. The pinned secondary marker distance discrepancy improves from-9.8% to-0.3% and bearing discrepancy from-13.3 to+0.1 degrees; projection and precision remain unknown. Exact city coordinates and two rerouted approach trails are our interpretation. All other57 site centres/radii and every coast, lake, river, mountain, hill, forest, biome and gameplay polygon remain unchanged frome129131. This is the old settlement, not the later city/castle built at Laura.

WIK-FDC-001 is wiki-level territorial evidence; DES-FDC-001 records exact authored geometry. No LN or manga story page was read for the bearing. The licensed Trinity chapter25 listing is a research lead, not a read chapter. Earlier server red-biome liberty and the initial-era building/roster qualifications remain. [Proportion audit](proportion-audit.csv).

## Eurazania cultivation reservation — round 17

Eurazania now has a sparse-jungle transition and three separated open field reservations within its existing southern woodland. This follows the official guide's warm climate/fruit-orchard premise (OFF-008); exact cultivation extent, vegetation species and polygon boundaries are our interpretation (DES-EUR-017). The overlays reserve a more open setting rather than automatically planting fruit crops. All58 site centres/radii and all21 road profiles are retained; the complete height/water PNGs are byte-identical to5afa13d's staged build. No coast, river, relief, forest boundary or gameplay mask changes.

The outer authored area is about523300 square blocks; separated field areas about65016/57796/44617, overlapping the fringe. The source supplies neither parcel locations nor ecosystem percentages. Existing Laura blueprint orchard details are reusable design work, but its later Tempest banners and post-destruction reconstruction are not the selected initial era. Current samples: (1560,1950) sparse jungle; (1350,1850)/(1610,2200)/(1310,2250) plains; (950,2100) retained jungle. These are server raster readings. No crop placement or in-game result is claimed.

## Tengu source/proposal comparison — round20

Round20 comparison note: the official map and current preview were reinspected. The Tengu review changes only an inert proposal comment,160 blocks north to an existing Khusha ridge; all active geography and58 markers remain identical. The official episode64 synopsis independently confirms Khusha residence and a later proposed tunnel. [The original terrace study](tengu-settlement-study.md) uses limited official stills and clearly authored buildings/paths. It does not add a new sovereign border, a completed later tunnel, a WN dimensional gateway or a pink forest biome. Existing continental scale/binding differences remain open; no new deliberate terrain difference is introduced.

## Eastern forest edges — round22

Three eastern forest boundaries now use restrained broad bays/lobes rather than smooth oval/ribbon edges. All sites, water, relief, roads, gameplay masks and nine other forests remain unchanged. The official base illustration, first painted study and new checker/terrain previews were compared; precise woodland boundaries are still our interpretation. [Before/after measurements and deliberate differences](forest-edge-review.md). No new sovereign border, canonical acreage or climate zone is inferred.

## Frost Palace continuity/placement difference — round28

The active coastal palace reserve remains a server interpretation. WN78 supplies an inland relationship; LN agreement is unread. C22 draws an inert near-centroid alternative, with no exact canonical coordinate or active site-kind change. Review coastal arrival versus inland palace representation before changing terrain or build data. [Source study](frost-palace-source-review.md).

## Orbic depleted ground — round31

[Source/terrain review](orbic-terrain-review.md) adds one rounded barren habitat patch south of Jura and north of the main Eurazania/Fulbrosia settlements, distinct from orc_camp. Public LN2 supports exhausted land/famine; broad bearings remain wiki-backed. Exact239623-block² extent and tensura:barren_land selection are our interpretation, not sovereign borders, a canonical biome name, a complete kingdom or a capital. About141942 blocks² is trimmed from one overlapping jungle edge; other11 forests,all58 sites/21 roads,height/water and gameplay masks remain unchanged. Every changed raster biome cell lies within the patch. The official map does not survey this boundary; checker/terrain previews and fresh atlas were visually compared with it. Existing continental distortions remain disclosed. Earlier three painted reviews predate this small vegetation change. No rift,tribal villages,later restoration or runtime acceptance is inferred.

## Ice Continent shoreline — round 32

[Source and measured review](ice-coast-review.md) replaces three parts of the rounded coastal envelope with limited irregular inlets after visual comparison with the official illustrated map. Exact bays and vertices are our interpretation, not surveyed canon. About94.02% of prior island area remains; maximum displacement208 blocks. The I gameplay mask and permafrost edge follow the coast. Frost Palace and its southern shore segment remain fixed, as do all58 site attributes and the916.98-block mainland strait. C22 remains unresolved; the inert inland proposal is still near the authored centroid. All mainland/El Dorado geography and21 roads remain unchanged. The fresh atlas/checker preview and before/after study were inspected; earlier paintings predate this coast and the Orbic habitat change. No new fjord name, port, island, structure or resident is inferred.
