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
  The mainland is about 9653 by 6130 blocks; the total design box is 12288 by 10752, 512 taller than the preferred target.
- The fixed deadly forest rings, arrival clearing, Treyni shrine, Spirit Gate by Tempest, minor camps and
  specific biomes are server content. In particular the guide places the Spirit Dwelling entrance in northern
  Ulgracia (`OFF-005..006`); the near-Tempest portal is a separate server adaptation.
- The old default checker still rejects five owner-authorized placements for Jia, Ulgracia and the ogre ruin.
  The alternate matrix is a review aid only. This map remains a draft until the normal gate passes.

Borders in this book are gameplay coverage polygons. No precise sovereign boundary, independent-state
subordination or early/late-story political continuity can be inferred from them. C05 (Velgrynd's mountain
bearing) and C06 (Siltrosso representation) remain open; source detail is insufficient to replace the fixed constraints.

## Source and era policy

The official guide and episode stills are reference links only; no official artwork is copied into this repository. Still links were extracted from the corresponding official episode pages on 19/11/2026; they provide shared series visual vocabulary and do not necessarily depict every minor nation. Where a place has no verified dedicated canonical image, the linked stills are mood references, not geographic evidence. Canon summaries below are paraphrases of the repo lore and the primary guide.

Early Tempest depicts the village after the ogres join. Later capitals and ruins exist as game destinations; the map does not assert a single unchanged political moment for every quest. Charybdis’s combat arena at Siss is a game placement; do not describe Charybdis as a canonical lake-whirlpool species.

## J — Jura-Tempest Federation

**Landform and heights.** Temperate lowlands 68–88; rocky shoulders 95–105. Tempest grows beside the west brook inside a small clearing. The road rises north through the safe rim to the Canaat apron.

**Target biome mix.** `tensura:ancient_forest` 20%, `minecraft:dark_forest` 40%, `minecraft:forest` 25%, `minecraft:plains` 10%, `minecraft:meadow` 5%.

**Palette, vegetation and crossings.** Sage and deep green, blue-grey bark, warm oak clearings. Open farmland gives way to an interlocked canopy; southeast paths disappear into Treyni’s old wood.

**Canon basis and interpretation.** Dwargon is north of Jura, Siss east, and Tempest stands in a forest clearing with running water. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 9, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img1.jpg), [episode 9, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img2.jpg).

**Anime frames actually inspected.** [rimuru city](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/rimuru_city.webp), [sealed cave](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/sealed_cave.webp), [khusha mountains](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/khusha_mountains.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## D — Armed Nation of Dwargon

**Landform and heights.** Grey alpine massif to y280; apron 95–145, south-facing escarpment at the gate. A ravine frames the entrance. The summit shoulder carries the Dragon’s Nest; natural ridges continue above the buried city.

**Target biome mix.** `minecraft:stony_peaks` 40%, `minecraft:meadow` 25%, `minecraft:windswept_gravelly_hills` 20%, `minecraft:forest` 10%, `minecraft:jagged_peaks` 5%.

**Palette, vegetation and crossings.** Tuff grey, warm yellow and anvil red. Forest thins to meadow and stone; gate lanterns replace daylight beneath the mountain.

**Canon basis and interpretation.** Dwargon occupies a natural cavern at the foot of the Canaat Mountains; the south-facing gate and exact ravine are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 4, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img1.jpg), [episode 4, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img2.jpg).

**Anime frames actually inspected.** [dwargon gate](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/dwargon_gate.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## W — Lake Siss marsh

**Landform and heights.** Lake level 66, depth 12; reed shores 68–74; limestone above the southern caverns to 103. The Ameld enters from the north and exits southeast.

**Target biome mix.** `minecraft:swamp` 60%, `minecraft:mangrove_swamp` 10%, `minecraft:plains` 20%, `minecraft:forest` 10%.

**Palette, vegetation and crossings.** Teal water, green reeds, pale limestone and weathered timber. Dry woodland opens into reed bays and flooded roots, then rises to a dry orc battlefield.

**Canon basis and interpretation.** The official guide identifies Siss in Jura and the Ameld flowing into it; episode 10 places the lizardmen in its wetlands. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 10, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no10/img1.jpg), [episode 10, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no10/img2.jpg).

**Anime frames actually inspected.** [lake siss](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/lake_siss.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## R — Kingdom of Blumund

**Landform and heights.** Low agricultural ground 68–82, with Londo on a dry trade terrace. Jura is connected by land; the west road reaches Ballachia and Englassia.

**Target biome mix.** `minecraft:plains` 65%, `minecraft:forest` 20%, `minecraft:flower_forest` 10%, `minecraft:meadow` 5%.

**Palette, vegetation and crossings.** Cream masonry, red cloth, grain gold and orchard green. The traveller leaves the heavy canopy for fields and a small walled market capital.

**Canon basis and interpretation.** Blumund is Jura’s western human neighbour; the dry land connection is retained from the reference geography. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

**Anime frames actually inspected.** [londo](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## G — Kingdom of Englassia

**Landform and heights.** Broad west-country river plains 65–85; low groves along the guild road. Lura and Ballachia remain compact, separated by agricultural country.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:forest` 25%, `minecraft:birch_forest` 15%, `minecraft:flower_forest` 5%.

**Palette, vegetation and crossings.** Slate, pale stone, navy banners and oxidized copper. Lanes widen toward the guild and academy; the western ridge closes the horizon beyond Lura.

**Canon basis and interpretation.** The official guide names Englassia a western cultural centre and the seat of the Free Guild headquarters. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## F — Kingdom of Falmuth

**Landform and heights.** Northern coastal lowlands 65–90. Marris sits inland behind Siltrosso’s coastal arm; the eastward land route reaches the Canaat gate.

**Target biome mix.** `minecraft:plains` 60%, `minecraft:meadow` 20%, `minecraft:forest` 15%, `minecraft:windswept_hills` 5%.

**Palette, vegetation and crossings.** Blue and white, pale stone and green copper. Grain fields become exposed coastal grass; roads converge at a guarded commercial town.

**Canon basis and interpretation.** Falmuth is a western trade gateway west of Dwargon and north of Blumund; exact coast and harbours are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## L — Holy Empire of Lubelius

**Landform and heights.** Western ridge to 205, with Lune on a terrace at its foot. The sacred approach climbs a separate trail toward the mountain sanctuary.

**Target biome mix.** `minecraft:windswept_hills` 30%, `minecraft:meadow` 30%, `minecraft:plains` 20%, `minecraft:forest` 15%, `minecraft:stony_peaks` 5%.

**Palette, vegetation and crossings.** Ivory, muted gold, pale blue and cool stone. Open farms tighten into terraced slopes and a ceremonial stair beneath a grey ridge.

**Canon basis and interpretation.** The pack locates Lubelius northwest of Jura and its sacred sanctuary above Lune. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 42, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no42/img1.jpg), [episode 42, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no42/img2.jpg).

## V — Damargania / western wastes

**Landform and heights.** Arid west lowlands 65–100; Coleus has a bounded oasis at level75. Desert gives way to a separate barren belt around the Heaven Tower.

**Target biome mix.** `tensura:desert_of_death` 45%, `minecraft:desert` 25%, `tensura:barren_land` 25%, `minecraft:windswept_gravelly_hills` 5%.

**Palette, vegetation and crossings.** Ochre, chalk, pale sand and ash grey. Green caravan roads end at a small oasis; farther west the horizon is bare and weathered.

**Canon basis and interpretation.** Damargania is the far-west barren territory; the oasis layout and desert transitions are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## O — Morgdahl

**Landform and heights.** Western river-bank lowland 65–78; slightly raised wharves and a dry landing approach.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:forest` 25%, `minecraft:meadow` 15%, `minecraft:swamp` 5%.

**Palette, vegetation and crossings.** Wet slate, river blue and willow green. The western road follows the river through landing fields rather than cutting across a mountain.

**Canon basis and interpretation.** The repo places Morgdahl in the western river belt; the settlement form is our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## A — Raja

**Landform and heights.** Small cultivated basin 70–85 with a rimmed lake at level72. Rostia stays on the northern approach rather than inside the water.

**Target biome mix.** `minecraft:plains` 50%, `minecraft:forest` 25%, `minecraft:meadow` 20%, `minecraft:swamp` 5%.

**Palette, vegetation and crossings.** Lake blue, earth brown and soft green. Hedges open toward a still inland lake and a modest waterside town.

**Canon basis and interpretation.** The pack places Raja west of Tempest in the small-state belt; its exact lake and gardens are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## N — Nostraille

**Landform and heights.** Gentle valley floor 70–90 between the western river landing and Yuzalgh.

**Target biome mix.** `minecraft:plains` 55%, `minecraft:meadow` 25%, `minecraft:forest` 20%.

**Palette, vegetation and crossings.** Muted greens, timber brown and pale stone. Small tilled fields alternate with low wooded shoulders.

**Canon basis and interpretation.** The repo’s west-to-east ordering places Nostraille east of Morgdahl and west of Yuzalgh. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## Y — Yuzalgh

**Landform and heights.** Narrow lowland state 70–90 with an uninterrupted through-road.

**Target biome mix.** `minecraft:plains` 65%, `minecraft:forest` 20%, `minecraft:meadow` 15%.

**Palette, vegetation and crossings.** Field green and grey-brown boundary stone. A traveller crosses a shallow valley and clustered farms without encountering a defensive sea gap.

**Canon basis and interpretation.** Yuzalgh belongs in the western sequence east of Nostraille; its architecture and borders are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## Q — Yggdonia

**Landform and heights.** Small birch country 72–90 between the western towns and Blumund’s southern edge.

**Target biome mix.** `minecraft:birch_forest` 55%, `minecraft:plains` 30%, `minecraft:flower_forest` 15%.

**Palette, vegetation and crossings.** White bark, pale green and straw. A light canopy softens the transition from town fields to Jura’s darker woodland.

**Canon basis and interpretation.** Yggdonia’s position and birch identity are pack interpretation, not independently established canon. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## U — Ulgracia

**Landform and heights.** Wooded coastal bluff to112, south of Sarion. Galut’s spring sits at102 with a contained rim; the brook descends to the southern coast.

**Target biome mix.** `minecraft:forest` 35%, `minecraft:dark_forest` 25%, `minecraft:old_growth_birch_forest` 20%, `minecraft:plains` 20%.

**Palette, vegetation and crossings.** Moss green, silver water and weathered rock. The southbound road leaves Sarion’s forest and climbs onto a wooded coastal overlook.

**Canon basis and interpretation.** The official guide and supplied reference place Ulgracia south of Sarion. Yasuke explicitly chose this over the earlier Blumund-adjacent server liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 17, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img1.jpg), [episode 17, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no17/img2.jpg).

## S — Sorcerous Dynasty of Sarion

**Landform and heights.** Southwestern forest peninsula 70–105, shaped around the river and one colossal Divine Tree at Elmine.

**Target biome mix.** `minecraft:forest` 35%, `minecraft:dark_forest` 25%, `minecraft:old_growth_birch_forest` 25%, `minecraft:flower_forest` 10%, `minecraft:plains` 5%.

**Palette, vegetation and crossings.** Gold-green canopy, ivory wood and quiet water. Deep forest opens into a living-tree city; the river runs beside, not through, its dry site.

**Canon basis and interpretation.** Sarion lies on Jura’s southern border; the single colossal tree and its waterside setting follow the supplied anime frame; exact build and size are our playable interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 28, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no28/img1.jpg), [episode 28, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no28/img2.jpg).

**Anime frames actually inspected.** [elmine](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/elmine.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## H — Harpy Queendom of Fulbrosia

**Landform and heights.** Southern spire country rising to235, between Sarion and Eurazania. Jia occupies ledges on a high, narrow rock pillar, with a winding ascent. The supplied anime still shows cliff dwellings rather than a conventional flat town.

**Target biome mix.** `minecraft:stony_peaks` 40%, `minecraft:windswept_forest` 25%, `minecraft:meadow` 25%, `minecraft:jagged_peaks` 10%.

**Palette, vegetation and crossings.** Cool stone, muted violet shadow and highland grass. Low fields give way to exposed ledges and wind-swept platforms.

**Canon basis and interpretation.** Frey’s territory lies south of Jura in the supplied reference, west/southwest of Eurazania. This supersedes the earlier far-southwest mesa liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 30, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img1.jpg), [episode 30, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img2.jpg).

**Anime frames actually inspected.** [jia](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/jia.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## B — Beast Kingdom of Eurazania

**Landform and heights.** Southeastern peninsula 68–100 with orchards and Laura’s dry clearing in jungle country. A north-facing escarpment behind Laura rises to225, with a headwater basin at154 feeding a stepped waterfall river past the dry city site.

**Target biome mix.** `minecraft:jungle` 60%, `minecraft:sparse_jungle` 20%, `minecraft:plains` 15%, `minecraft:bamboo_jungle` 5%.

**Palette, vegetation and crossings.** Jungle green, golden fruit, brown timber and thatch. Reeds recede behind low wooded ridges and cultivated fruit groves.

**Canon basis and interpretation.** Eurazania lies south/southeast of Jura. The supplied Laura frame shows a capital below a great mountain waterfall, and the wiki excerpt describes abundant fruit plantations. Exact waterfall reaches and playable elevations are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 30, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img1.jpg), [episode 30, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img2.jpg).

**Anime frames actually inspected.** [laura](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/laura.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## M — Milim’s Domain

**Landform and heights.** Eastern fertile lowlands 65–90, edged by a red badlands crescent. The Forgotten Dragon City sits in the green inner plain.

**Target biome mix.** `minecraft:plains` 50%, `minecraft:wooded_badlands` 25%, `minecraft:badlands` 15%, `minecraft:savanna` 10%.

**Palette, vegetation and crossings.** Green river grass, red sediment, mud brick and pink cloth. The eastern road moves from wet Jura margins to broad fields beneath a warm red ridge.

**Canon basis and interpretation.** Milim’s land lies east beyond Siss; fertile plains and a badlands crescent implement the owner’s geography brief. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 30, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img1.jpg), [episode 30, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no30/img2.jpg).

## P — Jistav

**Landform and heights.** Northeastern dark-wood basin 72–95, castle on a dry site beside its separate moat; Amrita is buried in a low mound to93.

**Target biome mix.** `minecraft:dark_forest` 60%, `minecraft:forest` 20%, `minecraft:plains` 15%, `tensura:miasmic_plains` 5%.

**Palette, vegetation and crossings.** Deep green, muted violet, grey stone and cold lantern light. The road enters a closed canopy before reaching the castle clearing and eastern ruin.

**Canon basis and interpretation.** The official guide identifies Jistav as Clayman’s territory; exact basin, moat and ruin placement are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 48, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 48, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

**Anime frames actually inspected.** [amrita](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/amrita.webp). Frame provenance and limitations are recorded in [anime reference notes](anime-reference-notes.md).

## E — Eastern Empire

**Landform and heights.** Far-eastern northern valley 75–110, with Nasca north of a volcanic sanctuary rising to250.

**Target biome mix.** `minecraft:plains` 45%, `minecraft:forest` 25%, `minecraft:meadow` 15%, `minecraft:stony_peaks` 10%, `minecraft:badlands` 5%.

**Palette, vegetation and crossings.** Dark green roofs, red devices, copper and amber glass. Open plains are interrupted by long volcanic spurs rather than a continuous impassable wall.

**Canon basis and interpretation.** The Empire occupies the far northeast; the brief fixes Nasca’s valley north of Velgrynd’s volcano. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 48, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 48, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## I — Ice Continent

**Landform and heights.** Separate frozen island, 900–1,200 blocks of sea from the mainland; low ice ledges rise toward a210 spine. Frost Palace occupies the southern coastal plate.

**Target biome mix.** `minecraft:snowy_plains` 60%, `minecraft:frozen_peaks` 20%, `minecraft:snowy_slopes` 15%, `minecraft:ice_spikes` 5%.

**Palette, vegetation and crossings.** Blue ice, white rock and violet lights. A cold crossing ends at a coastal palace below an empty frozen interior.

**Canon basis and interpretation.** The Ice Continent is northern and contains Guy’s Frost Palace; the playable shoreline and causeway are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 48, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 48, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## X — El Dorado

**Landform and heights.** Separate southwest volcanic island, roughly 1,850 by1,400; Leon’s city lies northwest of the volcano, which rises to230.

**Target biome mix.** `minecraft:plains` 45%, `minecraft:meadow` 20%, `minecraft:forest` 20%, `minecraft:stony_peaks` 10%, `minecraft:flower_forest` 5%.

**Palette, vegetation and crossings.** White and gold, green foothills, black volcanic stone and purple-red interiors. The sea crossing reaches a sheltered city plain below the caldera.

**Canon basis and interpretation.** El Dorado lies on a southwestern continent; its playable island compression is an explicit owner liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Visual references (3).** [official world guide](https://www.ten-sura.com/map), [episode 48, still 1](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img1.jpg), [episode 48, still 2](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no48/img2.jpg).

## Open lore and implementation questions

- The owner explicitly reversed the earlier Fulbrosia and Ulgracia liberties. Use the anime-aligned positions and reconcile the old default checker matrix.
- Several small-state identities and capital names rely on secondary repo research. No new flags, rulers or political borders are asserted as verified canon here.
- Drawn site radii now meet all footprint minima from `world/sites.toml`, including Tempest r148 and Dwargon r127. Relative internal anchors remain within their parent complexes. Final in-game ground, cover and water containment still need technical acceptance.
- Treyni’s shrine is an original pack interpretation; the separated grove and shrine sites follow the accepted checker, replacing the old imported-world +38 offset.
- Preserve the Lerfing and Paulzero credit history for the prior world attempt. The new coast and artwork are original, with no copied paid terrain.

EN: The continent has fixed story geography; the outer ocean and free lands are generated around it.
NL: Het continent heeft vaste verhaalgeografie; de buitenste oceaan en vrije gebieden worden eromheen gegenereerd.

The ogre ruin is placed at the southeastern Khusha foothills, using the supplied wiki and pinned reference marker instead of the older northeastern guess. Siltrosso is an independent kingdom in the supplied wiki; the existing F region groups its coastal marker for game data and does not establish Falmuth sovereignty. Its separate nation metadata needs Claude’s reconciliation. The interactive reference places Velgrynd’s mountain north of Nasca, while the old server brief places it south; the supplied wiki only says adjacent. This unresolved compass detail is retained as a PR lore question, not claimed as confirmed canon.
