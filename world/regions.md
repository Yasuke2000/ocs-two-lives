# Current terrain guide — Coleus dune relief

This is the current creative guide for `world/map.svg`, active-geometry export source `0b8bcf56c8054ae0b03f60dcf5b8777672b5097078803390f2d82636a52f045e`. A later [Galut fit review](galut-site-review.md) changes only the inert proposal status, giving current file hash `a5e1c2f6d811ff367da3da90aa60871ce421a99a9bfeb564501a0e533cda9c3a`. The [Coleus dune review](coleus-dune-relief.md) adds one local rolling ridge to the R130 active geometry; both larger-island alternatives remain comments. One SVG unit is one block; east is +x and south is +z. Rimuru’s village is at (0,0). The mainland measures 9,983 × 6,250 blocks; the normal export box is 12,800 × 10,752. Those are authored server dimensions, not a canonical survey.

Use the **[post-Kijin S1E10 snapshot](era.md)**: the Kijin have just been named, the Orc Lord conflict is unresolved, Falmuth still exists, and Clayman, Frey and Carrion retain their earlier countries. A site reservation supplies capacity; it does not instantiate a future city, event or resident. See the [58-site era overlay](../docs/research/tensura-world-2026-11-19/era-site-state.csv).

The 22 lettered regions below are **gameplay terrain masks**, not surveyed national borders. Country pins do not establish a capital’s location. Exact shores, block heights, biome choices, travel mood and unspecified local geometry are **our interpretation**. The claim ledger distinguishes `canon-explicit`, `canon-implied`, `fan-wiki` and `our interpretation`; prefer directly verified LN > WN > manga > anime > official map > wiki. Reference images remain links, with their specific roles and limits stated below.

**Deliberate proportion difference (C12).** The Ice Continent and El Dorado remain relatively smaller than their broad extents in the official illustration, following the server island-size brief. The [original side-by-side island study](island-proportion-review.md) compares current widths with a coast-only alternative drawn in an SVG comment. Initial trial A exceeds the hard design-box height; trial B fits after western shifts, while both remain outside the smaller island-size recommendation. Neither is active terrain or accepted new island geometry.

**Current numeric basis.** All 22 biome mixes use the [R128 census](region-biomes-r128.md), retained because the biome PNG and every region polygon remain byte-identical. Rounded percentages may sum slightly away from 100%; exact values remain in the CSV/JSON. The [R130 water review](ulgr-spring-level-r130.md) remains the Ulgr foundation. The current [Coleus dune export](coleus-dune-relief.json) adds one 22-vertex hill, changing 661 height samples by at most 11.25 blocks. All 58 site exports/heights and all 22 road courses remain; ten western caravan profile heights change by at most 0.09. All 22 finite exported point profiles remain within the owner’s 1:2 grade, using floating-point tolerance. This does not substitute for final-noise or in-game travel checks.

**Current visual companions.** [Terrain atlas](atlas.png) · [checked preview](preview.png) · [current painted atlas proposal PR122](https://github.com/Yasuke2000/ocs-two-lives/pull/122) · [58-place art registration PR115](https://github.com/Yasuke2000/ocs-two-lives/pull/115). The paired painting now includes the Coleus dune and keeps its original component provenance; its lighting is not an exact height reconstruction. The R127 art registration remains numerically applicable because every site export is unchanged.

Earlier iteration notes are preserved in [the previous guide](https://github.com/Yasuke2000/ocs-two-lives/blob/b053e13b4fdd98eab5a804ea704cc59105df4e1e/world/regions.md) and Git history. They are history, not competing current instructions. This guide keeps all 22 region narratives and all curated image links while removing superseded status preambles.

## J — Jura Forest / Rimuru's village (gameplay J)

**Landform and heights.** Temperate lowlands 68–88; rocky shoulders 95–105. Tempest grows beside the west brook inside a small clearing. The road rises north through the safe rim to the Canaat apron.

**Current designed biome mix (R128 census; retained in R130).** forest 40.67%, plains 29.52%, dark_forest 23.72%, tensura:ancient_forest 2.38%, old_growth_spruce_taiga 1.80%, old_growth_birch_forest 1.00%, stony_peaks 0.63%, river 0.17%, meadow 0.11%.

**Palette, vegetation and crossings.** Sage and deep green, blue-grey bark, warm oak clearings. Open edge clearings give way to an interlocked canopy; southeast paths disappear into Treyni’s old wood.

**Mood (our interpretation).** Light at the forest edge fades into a close, dangerous old canopy.

**Canon basis and interpretation.** Dwargon is north of Jura, Siss east, and Tempest stands in a forest clearing with running water. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Cave source refinement.** The [licensed LN1 free passages](../docs/research/tensura-world-2026-11-19/licensed-ln1-cave-followup.md) support natural cave plants and interior water. They do not locate an exterior lake,confirm a connecting river or survey the authored NW hill/cave plan. The dry approach and current S1E10 state remain.

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local official woodland: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Early woodland setting, not a surveyed Tempest clearing.; [local official woodland: The ogres among trees and undergrowth.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img4.jpg) — Ogre encounter vegetation; no exact route coordinates.; [local secondary setting: Irregular dark cave opening with luminous mineral accents.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/sealed_cave.webp) — Cave visual vocabulary; attribution qualified.; [later local secondary setting: A later large planned town in a green mountain basin.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/rimuru_city.webp) — Later basin and expansion context only; no metropolis at initial snapshot.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## D — Armed Nation of Dwargon

**Landform and heights.** Grey alpine core to y280; lower eastern mountain spurs to y180, with foothill approaches around75–145. A south-facing escarpment frames the gate. A ravine frames the entrance. The summit shoulder carries the Dragon’s Nest; natural ridges continue above the buried city.

**Current designed biome mix (R128 census; retained in R130).** plains 73.55%, forest 16.19%, stony_peaks 4.71%, jagged_peaks 1.62%, snowy_slopes 1.19%, meadow 1.02%, frozen_peaks 1.00%, beach 0.69%, river 0.03%.

**Palette, vegetation and crossings.** Tuff grey, warm yellow and anvil red. Forest thins to meadow and stone; gate lanterns replace daylight beneath the mountain.

**Mood (our interpretation).** A stone approach narrows into mountain shelter and enclosed city space.

**Canon basis and interpretation.** Dwargon occupies a natural cavern at the foot of the Canaat Mountains; the south-facing gate and exact ravine are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local official approach: Travellers queue beside a pale rock wall and entrance architecture.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img3.jpg) — Rock and entrance vocabulary; no measured gate bearing.; [local official interior: Kaijin at a workshop with masonry and tools.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img4.jpg) — Workshop masonry/tools; not city street geometry.; [local secondary setting: Small gateway in a pale rocky mountain with a grassy approach.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/dwargon_gate.webp) — Gate/apron appearance, not exact scale.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## W — Lake Siss marsh

**Landform and heights.** An elongated basin about858 by410 blocks, lake level66 and depth12; reed shores68–74 and limestone above the southern caverns to103. The Ameld enters from the north and exits on the east before turning southeast. These dimensions/heights and exact joins are our interpretation.

**Current designed biome mix (R128 census; retained in R130).** swamp 59.69%, plains 29.68%, forest 4.49%, dark_forest 3.05%, old_growth_spruce_taiga 2.63%, river 0.46%.

**Palette, vegetation and crossings.** Teal water, green reeds, pale limestone and weathered timber. Dry woodland opens into reed bays and flooded roots, then rises to a dry orc battlefield.

**Mood (our interpretation).** Humid quiet, reeds and broken wet footing.

**Canon basis and interpretation.** The official guide identifies Siss in Jura and the Ameld flowing into it; episode 10 places the lizardmen in its wetlands. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local secondary setting: Dark reed-lined water; title overlay obscures part of the view.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/lake_siss.webp) — Reed/water appearance only; not lake boundaries.; [regional vegetation context: Gabiru against grassy woodland; no lake outline.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no10/img5.jpg) — Grass and woodland background only; character pose does not locate a shoreline.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## R — Kingdom of Blumund

**Landform and heights.** Low agricultural ground 68–82, with Londo on a dry trade terrace. Jura is connected by land; the west road reaches Ballachia and Englassia.

**Current designed biome mix (R128 census; retained in R130).** plains 93.02%, river 5.41%, birch_forest 1.57%.

**Palette, vegetation and crossings.** Cream masonry, red cloth, grain gold and orchard green. The traveller leaves the heavy canopy for fields and a small walled market capital.

**Mood (our interpretation).** A small border kingdom offers a calmer pause outside the great forest.

**Canon basis and interpretation.** Blumund is Jura’s western human neighbour; the dry land connection is retained from the reference geography. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local secondary setting: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Fields and low wall appearance; no exact capital plan.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## G — Kingdom of Englassia

**Landform and heights.** Broad west-country river plains 65–85; low groves along the guild road. Lura and Ballachia remain compact, separated by agricultural country.

**Current designed biome mix (R128 census; retained in R130).** plains 68.82%, forest 26.59%, desert 2.22%, river 1.19%, birch_forest 1.18%.

**Palette, vegetation and crossings.** Slate, pale stone, navy banners and oxidized copper. Lanes widen toward the guild and academy; the western ridge closes the horizon beyond Lura.

**Mood (our interpretation).** Human roads, open fields and an old royal centre.

**Canon basis and interpretation.** The official guide names Englassia a western cultural centre and the seat of the Free Guild headquarters. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [regional official interior: Yuuki in a light and brown office interior.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no20/img2.jpg) — Yuuki office context only; no capital exterior.; [regional official interior: Children, desks and tall wooden classroom windows.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no21/img3.jpg) — Academy classroom materials; not city or campus coordinates.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## F — Kingdom of Falmuth

**Landform and heights.** Northern coastal lowlands 65–90. Marris sits inland behind Siltrosso’s coastal arm; the eastward land route reaches the Canaat gate.

**Current designed biome mix (R128 census; retained in R130).** plains 98.24%, beach 1.76%.

**Palette, vegetation and crossings.** Blue and white, pale stone and green copper. Grain fields become exposed coastal grass; roads converge at a guarded commercial town.

**Mood (our interpretation).** Sea wind crosses exposed northern fields and guarded approaches.

**Canon basis and interpretation.** Falmuth is a western trade gateway west of Dwargon and north of Blumund; exact coast and harbours are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region urban analogy: Coleus production panorama: hill palace, ramp, lower town, arid mountain backdrop and foreground vegetation.](https://www.ten-sura.com/4GfGdAp7/wp-content/uploads/2023/05/bf4a714bd04266b501beea54ae574464.jpg) — Stepped town massing and rock colour only; do not transplant Coleus palace, domes or arid climate.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## L — Holy Empire of Lubelius

**Landform and heights.** Western ridge to 205, with Lune on a terrace at its foot. The sacred approach climbs a separate trail toward the mountain sanctuary.

**Current designed biome mix (R128 census; retained in R130).** plains 94.22%, desert 3.06%, stony_peaks 1.59%, beach 0.60%, snowy_slopes 0.43%, river 0.11%.

**Palette, vegetation and crossings.** Ivory, muted gold, pale blue and cool stone. Open farms tighten into terraced slopes and a ceremonial stair beneath a grey ridge.

**Mood (our interpretation).** A sober foothill ascent leads toward the high sanctuary.

**Canon basis and interpretation.** The pack locates Lubelius northwest of Jura and its sacred sanctuary above Lune. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [regional official interior: Knights and tall stone columns in a conference scene.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no57/img3.jpg) — Lubelius meeting columns; not a capital or sacred-stair layout.; [regional official interior: Louis and Hinata in a gold-tracery interior.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no54/img5.jpg) — Gold-tracery material context; not exterior geography.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## V — Damargania / western wastes

**Landform and heights.** Arid west lowlands 65–100; Coleus has a bounded oasis at level75. A small authored northern dune reaches81.5 in the current export; its110 height control is attenuated by the hill blend. Desert gives way to a separate barren belt around the Heaven Tower.

**Current designed biome mix (R128 census; retained in R130).** plains 44.47%, tensura:desert_of_death 39.67%, tensura:barren_land 10.44%, desert 4.18%, beach 1.13%, river 0.07%, forest 0.03%.

**Palette, vegetation and crossings.** Ochre, chalk, pale sand and ash grey. Green caravan roads end at a small oasis; farther west the horizon is bare and weathered.

**Mood (our interpretation).** Dry wind, bare horizons and long gaps between useful paths.

**Canon basis and interpretation.** Damargania is the far-west barren territory; the oasis layout and desert transitions are our interpretation. The [official Coleus PV at00:25](https://www.youtube.com/watch?v=WuIDVoKdVGU&t=25s) supplies sand-dune vocabulary; the new ridge’s exact course, scale and northern placement are [our interpretation](coleus-dune-relief.md). See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [named regional component: Coleus production panorama: hill palace, ramp, lower town, arid mountain backdrop and foreground vegetation.](https://www.ten-sura.com/4GfGdAp7/wp-content/uploads/2023/05/bf4a714bd04266b501beea54ae574464.jpg) — Coleus component only; not all Damargania or Dagruel's capital.; [cross-region rock analogy: Travellers queue beside a pale rock wall and entrance architecture.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img3.jpg) — Dwargon pale rock only; does not locate a western settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## O — Morgdahl

**Landform and heights.** Western river-bank lowland 65–78; slightly raised wharves and a dry landing approach.

**Current designed biome mix (R128 census; retained in R130).** plains 97.64%, river 1.71%, beach 0.64%.

**Palette, vegetation and crossings.** Wet slate, river blue and willow green. The western road follows the river through landing fields rather than cutting across a mountain.

**Mood (our interpretation).** A settled pocket interrupts the dry western country.

**Canon basis and interpretation.** The community Council-map comparison reports Morgdahl first in a west-to-east sequence with Nostraille, Yuzalgh and Yggdonia (FAN-WES-034); the underlying map frame has not been independently authenticated here. The river-belt position, wharves and settlement form are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Continental silhouette and major-country context only; this image does not establish the four small-state names, their order or borders.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region waterbank analogy: Dark reed-lined water; title overlay obscures part of the view.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/lake_siss.webp) — Reeds/bank material only; not proof of local lakes or coast.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## A — Raja

**Landform and heights.** Small cultivated basin 70–85 with a rimmed lake at level72. Rostia stays on the northern approach rather than inside the water.

**Current designed biome mix (R128 census; retained in R130).** plains 91.55%, river 8.45%.

**Palette, vegetation and crossings.** Lake blue, earth brown and soft green. Hedges open toward a still inland lake and a modest waterside town.

**Mood (our interpretation).** Water and cultivated clearings soften the small-country travel belt.

**Canon basis and interpretation.** The pack places Raja west of Tempest in the small-state belt; its exact lake and gardens are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region waterbank analogy: Dark reed-lined water; title overlay obscures part of the view.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/lake_siss.webp) — Reeds/bank material only; no local hydrology claim.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## N — Nostraille

**Landform and heights.** Gentle valley floor 70–90 between the western river landing and Yuzalgh.

**Current designed biome mix (R128 census; retained in R130).** plains 99.84%, river 0.16%.

**Palette, vegetation and crossings.** Muted greens, timber brown and pale stone. Small tilled fields alternate with low wooded shoulders.

**Mood (our interpretation).** Low ridges and tree cover keep the next settlement out of sight.

**Canon basis and interpretation.** The west-to-east sequence is reported by a community Council-map comparison (FAN-WES-034), not directly verified from an episode frame here. Our marker order follows that lead; the valley, fields, woods and exact national extent are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Continental silhouette and major-country context only; this image does not establish the four small-state names, their order or borders.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## Y — Yuzalgh

**Landform and heights.** Narrow lowland state 70–90 with an uninterrupted through-road.

**Current designed biome mix (R128 census; retained in R130).** plains 99.89%, birch_forest 0.11%.

**Palette, vegetation and crossings.** Field green and grey-brown boundary stone. A traveller crosses a shallow valley and clustered farms without encountering a defensive sea gap.

**Mood (our interpretation).** Open ground and river crossings set a slower pace.

**Canon basis and interpretation.** A community Council-map comparison reports Yuzalgh east of Nostraille and west of Yggdonia (FAN-WES-034). This remains secondary evidence. Exact placement, farms, architecture and borders are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Continental silhouette and major-country context only; this image does not establish the four small-state names, their order or borders.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## Q — Yggdonia

**Landform and heights.** Small birch country 72–90 between the western towns and Blumund’s southern edge.

**Current designed biome mix (R128 census; retained in R130).** birch_forest 98.88%, plains 1.12%.

**Palette, vegetation and crossings.** White bark, pale green and straw. A light canopy softens the transition from town fields to Jura’s darker woodland.

**Mood (our interpretation).** Quiet wet lowlands break the route into short crossings.

**Canon basis and interpretation.** A community Council-map comparison reports Yggdonia east of Yuzalgh (FAN-WES-034). This remains secondary evidence. Its exact position beside Blumund, birch identity and local extent are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Continental silhouette and major-country context only; this image does not establish the four small-state names, their order or borders.; [cross-region agrarian analogy: A low walled town beyond cultivated fields and green hills.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/londo.webp) — Blumund fields/town massing only; not a view of this country or proof of its climate.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## U — Ulgracia

**Landform and heights.** Wooded coastal bluff to 112, south of Sarion. The authored spring is now at 92, still 29 blocks above the sea, with a contained rim and a steeper wooded bowl. The unchanged inland brook begins at 91, a one-block difference, then descends in existing stepped reaches to the shore. These are server elevations, not canonical measurements. [Actual terrain and bank review](ulgr-spring-level-r130.md).

**Current designed biome mix (R128 census; retained in R130).** old_growth_birch_forest 93.53%, plains 5.60%, beach 0.87%.

**Palette, vegetation and crossings.** Moss green, silver water and weathered rock. The southbound road leaves Sarion’s forest and climbs onto a wooded coastal overlook.

**Mood (our interpretation).** A wooded bluff shelters a lower spring bowl and an old rock threshold.

**Canon basis and interpretation.** The official guide and supplied reference place Ulgracia south of Sarion. Yasuke explicitly chose this over the earlier Blumund-adjacent server liberty. The park marker is not the unlocated capital Galut. WN61 describes a doorway in a large rock, not this pond’s measured altitude; retain its separate continuity and later-scene limits (`WN61-002`). See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**City and trade limit.** [WN61 L45](https://ncode.syosetu.com/n6316bn/64/#L45) directly supports trade with Sarion in WN continuity. The licensed guide8.5 country card directly confirms the name Galut (`GUIDE85-GALUT-001`); its location remains unverified; the [old dry-circle proposal requires redesign](galut-site-review.md). The park and city are distinct, and neither the spring nor this road endpoint locates the capital.

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [associated official interior: Rimuru and Ramiris in a dark masonry interior.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no22/img5.jpg) — Spirit Dwelling masonry context only; not Ulgr park, Galut or mainland entrance placement.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## S — Sorcerous Dynasty of Sarion

**Landform and heights.** Southwestern forest peninsula 70–105, shaped around the river and one colossal Divine Tree at Elmine.

**Current designed biome mix (R128 census; retained in R130).** old_growth_birch_forest 75.89%, plains 22.86%, stony_peaks 0.88%, beach 0.32%, river 0.04%.

**Palette, vegetation and crossings.** Gold-green canopy, ivory wood and quiet water. Deep forest opens into a living-tree city; the river runs beside, not through, its dry site.

**Mood (our interpretation).** Dense green approaches frame an older elven court landscape.

**Canon basis and interpretation.** Sarion lies on Jura’s southern border; the single colossal tree and its waterside setting follow the supplied anime frame; exact build and size are our playable interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local secondary setting: A giant tree above an elevated settlement, with water in the foreground.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/elmine.webp) — Giant-tree city visual; episode/era unverified.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## H — Harpy Queendom of Fulbrosia

**Landform and heights.** Southern spire country rising to235, between Sarion and Eurazania. Jia occupies ledges on a high, narrow rock pillar, with a winding ascent. The supplied anime still shows cliff dwellings rather than a conventional flat town.

**Current designed biome mix (R128 census; retained in R130).** plains 63.92%, windswept_hills 25.54%, jungle 8.41%, beach 1.09%, river 0.57%, old_growth_birch_forest 0.47%.

**Palette, vegetation and crossings.** Cool stone, muted violet shadow and highland grass. Low fields give way to exposed ledges and wind-swept platforms.

**Mood (our interpretation).** Exposed ledges and high rock platforms feel windy and distant.

**Canon basis and interpretation.** Frey’s territory lies south of Jura in the supplied reference, west/southwest of Eurazania. This supersedes the earlier far-southwest mesa liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local secondary setting: A compact city on tall rocky cliff ledges.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/jia.webp) — Cliff city vocabulary, not measured height or bearing.; [cross-region rock analogy: Narrow tall rock spires rising above mist.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/khusha_mountains.webp) — Rock spires only; not a Fulbrosia panorama or exact site.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## B — Beast Kingdom of Eurazania

**Capital name (C24).** The readable map uses Carrion's capital. The stable technical ID and older prose use `laura`; wiki Laura conflicts with the inspected electronic guide8.5 card's Rondo, also printed for Blumund. An erratum/edition or LN-prose check remains open; neither a renaming nor a typo is assumed. [Licensed guide review](guide85-source-review.md).

**Landform and heights.** Southeastern peninsula 68–100 with orchards and Laura’s dry clearing in jungle country. A north-facing escarpment behind Laura rises to225, with a headwater basin at154 feeding a stepped waterfall river past the dry city site.

**Current designed biome mix (R128 census; retained in R130).** jungle 43.70%, plains 30.61%, sparse_jungle 13.21%, tensura:barren_land 8.89%, swamp 1.74%, stony_peaks 0.51%, river 0.43%, beach 0.42%, snowy_slopes 0.26%, old_growth_spruce_taiga 0.24%.

**Palette, vegetation and crossings.** Jungle green, golden fruit, brown timber and thatch. Reeds recede behind low wooded ridges and cultivated fruit groves.

**Mood (our interpretation).** Fruit-growing lowlands meet steep mountain and waterfall country.

**Canon basis and interpretation.** Eurazania lies south/southeast of Jura. LN5 supports the castle mountain backdrop and town below (`LN05-001..002`). The secondary Laura frame suggests the waterfall; its episode/timestamp remains unverified ([source/profile review](laura-waterfall-review.md)). The wiki excerpt describes fruit plantations. Exact waterfall reaches and playable elevations are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [local secondary setting: A waterfall between sharp peaks behind a city and cultivated foreground.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/laura.webp) — Intact waterfall city, not a surveyed plan; attribution qualified.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## M — Milim's old domain

**Landform and heights.** Eastern lowlands65–90 with a narrow red crescent retained solely as the fixed brief's server accent. The large former red-biome footprint is reduced from707,757 to213,884 square blocks of authored polygon area (69.8% smaller). Surrounding land follows existing default grassland/forest priorities. No new hill, river or settlement is added.

**Current designed biome mix (R128 census; retained in R130).** plains 87.30%, forest 4.70%, wooded_badlands 4.44%, river 1.50%, dark_forest 1.40%, beach 0.66%.

**Palette, vegetation and crossings.** Green lowlands and established woodland, with a restrained warm-soil accent near the eastern coast. Exact tree species, settlement palette and field layout remain interpretation.

**Mood (our interpretation).** Open green plains are interrupted by the authored red-rock accent.

**Canon basis and limits.** The official guide identifies Milim's old dragonewt settlement and its unusual social organisation; it does not define a red desert. The official illustrated map is a broad visual reference, not a biome survey. The fixed [brief](../design/architecture/own-world.md) explicitly retains some red badlands. C10 now draws an inert grassland replacement for the former large footprint, so the remaining design liberty is visible. No later annexation or new castle is treated as initial geography.

**References.** [Official world guide](https://www.ten-sura.com/map), [official base image](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp), [city source notes](../design/lore/forgotten_dragon_city.md). Official episode41 is at [route no44](https://www.ten-sura.com/anime/tensura/story/no44); its five inspected stills do not establish a city exterior or biome footprint. The pinned fan metadata's city frame could not be re-fetched this round, so its episode attribution remains secondary.

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [neighbouring valley analogy: A waterfall between sharp peaks behind a city and cultivated foreground.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/laura.webp) — Cultivated valley vocabulary only; not Milim's temple or local city.; [cross-region urban analogy: Coleus production panorama: hill palace, ramp, lower town, arid mountain backdrop and foreground vegetation.](https://www.ten-sura.com/4GfGdAp7/wp-content/uploads/2023/05/bf4a714bd04266b501beea54ae574464.jpg) — Stepped town massing and rock colour only; do not transplant Coleus palace, domes or arid climate.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## P — Jistav

**Landform and heights.** Northeastern dark-wood basin 72–95, castle on a dry site beside its separate moat; the separate Amrita ruin footprint uses an authored low mound to93.

**Current designed biome mix (R128 census; retained in R130).** plains 54.96%, dark_forest 43.96%, stony_peaks 0.72%, beach 0.36%.

**Palette, vegetation and crossings.** Deep green, muted violet, grey stone and cold lantern light. The road enters a closed canopy before reaching the castle clearing and eastern ruin.

**Mood (our interpretation).** Dark woods and old stone suggest a guarded eastern domain.

**Canon basis and interpretation.** The official guide identifies Jistav as Clayman’s territory. LN10 distinguishes Amrita from the surface city and older Soma homeland (`LN10-001..003`); official episode81 explicitly places the ruins beneath the former castle (`OFF-AMR-001`). The separate eastern circle is a mandatory game reservation under C07, not a verified independent surface entrance. An inert castle-linked access projection is drawn; exact depth/full footprint/entrance coordinates remain unknown and eastern chambers remain possible. Basin, moat and external mound are authored. [Access/reservation study](amrita-placement-review.md) · [existing lore](../design/lore/world.md) · [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [associated secondary surface setting: A dark castle and wooded wet basin; not an underground city plan.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/amrita.webp) — Clayman castle/wet basin context; not the underground Amrita city layout.; [cross-region vegetation analogy: Rimuru, Rigur and Ranga in leafy woodland.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no9/img3.jpg) — Neighbouring Jura woodland vocabulary only; does not establish this country's vegetation share or settlement.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## E — Eastern Empire

**Landform and heights.** Far-eastern northern valley 75–110, with Nasca north of a volcanic sanctuary rising to250.

**Current designed biome mix (R128 census; retained in R130).** plains 86.12%, snowy_slopes 5.08%, stony_peaks 3.43%, forest 2.65%, beach 1.48%, river 1.20%, frozen_peaks 0.05%.

**Palette, vegetation and crossings.** Dark green roofs, red devices, copper and amber glass. Open plains are interrupted by long volcanic spurs rather than a continuous impassable wall.

**Mood (our interpretation).** Broad eastern approaches give way to woodland and volcanic ground.

**Canon basis and interpretation.** The Empire occupies the far northeast; the brief fixes Nasca’s valley north of Velgrynd’s volcano. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [cross-region valley analogy: A waterfall between sharp peaks behind a city and cultivated foreground.](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6/public/img/locations/laura.webp) — Valley/farmland vocabulary only; not an Imperial settlement.; [cross-region rock analogy: Travellers queue beside a pale rock wall and entrance architecture.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no4/img3.jpg) — Canaat rock material only; not Nasca or an Empire panorama.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## I — Ice Continent

**Landform and heights.** Separate frozen landmass with a lower western arm and five offshore islets. The current coast is an original R128 interpretation of the official silhouette. It lies 900–1,200 blocks of sea from the mainland; low ice ledges rise toward a210 spine. Following Yasuke’s R109 decision, Frost Palace occupies the central snowfield at(-1530,-3680), with an original89-block inland clearing for the existing entrance and its preparation buffer. The old coastal palace plate is retired in the drawing; this does not establish a full palace footprint.

**Current designed biome mix (R128 census; retained in R130).** snowy_plains 75.84%, frozen_peaks 24.16%.

**Palette, vegetation and crossings.** Blue ice, white rock and violet shadow. A cold sea crossing reaches bare coastal ice; travel then continues across the interior to the approved palace snowfield. No new coastal palace or arrival facility is registered.

**Mood (our interpretation).** A cold sea crossing reaches bare ice; the palace remains inland.

**Canon basis and interpretation.** The Ice Continent is northern and contains Guy’s Frost Palace. Fuse’s WN78 supplies a central-continent relationship; LN agreement remains unread. Yasuke chose inland placement in R109; the exact snowfield coordinate,clearing,shoreline and entrance forecourt are our interpretation. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [associated official interior: Leon before a blue fractured-looking wall; no exterior panorama.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no45/img3.jpg) — Cold blue wall material only; no confirmed exterior palace or coastline.; [associated official interior: Velzard on a blue fractured-looking floor; no coastline.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no45/img4.jpg) — Cold blue floor material only; no measured island geometry or C22 resolution.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## X — El Dorado

**Landform and heights.** Separate southwest volcanic island with authored bounds about 2,400.5 × 1,280.5 blocks after the R125 coast correction; Leon’s city lies northwest of the volcano, which rises to 230. R114 selects a local stony_peaks biome over the exact cone outline;the rock treatment is our interpretation,not proof of canonical climate or absence of runtime snow. [Review](el-dorado-rock-cone-r114.md). R80 adds an interpreted unnamed inland lake east of the cone, water first-air 68 and depth 5; its natural rim and exact outline are authored.

**Current designed biome mix (R128 census; retained in R130).** plains 85.06%, stony_peaks 5.85%, forest 4.79%, beach 2.62%, river 1.67%.

**Palette, vegetation and crossings.** White and gold, green foothills, black volcanic stone and purple-red interiors. Two source-informed wooded patches lie northwest of the cone and east/southeast of the eastern lake. Rounded outlines and generic forest type are our interpretation;no tree species,density or dated logging claim. The sea crossing reaches a sheltered city plain below the caldera. [R111 source/terrain review](el-dorado-woodland-r111.md).

**Mood (our interpretation).** Green island foothills lead toward pale court stone and a rocky cone.

**Canon basis and interpretation.** El Dorado lies on a southwestern continent; its playable island compression is an explicit owner liberty. See [existing lore](../design/lore/world.md) and the [owner brief](../design/architecture/own-world.md#8-chatgpt-brief--the-world-map-drawing-and-its-layer-specification).

**Curated image references.** [broad map context: Official illustrated world silhouette and named-country context.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) — Country placement and continental silhouette only; no surveyed border, height, street or exact distance.; [cross-region urban analogy: Coleus production panorama: hill palace, ramp, lower town, arid mountain backdrop and foreground vegetation.](https://www.ten-sura.com/4GfGdAp7/wp-content/uploads/2023/05/bf4a714bd04266b501beea54ae574464.jpg) — Stepped town massing and rock colour only; do not transplant Coleus palace, domes or arid climate.; [persona palette only: Leon before a blue fractured-looking wall; no exterior panorama.](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/anime/tensura-portal-anime-tensura/assets/images/story/no45/img3.jpg) — Leon's colour association only; meeting-room wall is not El Dorado architecture or geography.

**Evidence limit.** A shared world map, an interior or a cross-region analogy is not a dedicated landscape reference for this country. See the [reference-role audit](../docs/research/tensura-world-2026-11-19/region-image-review-r59.md) and its CSV for provenance, confidence and outstanding gaps.

## Deliberate differences and open source questions

| Topic | Current treatment |
| --- | --- |
| Scale and projections (C12) | Fixed site distances, template reservations and the unknown illustrated projection prevent a claim of one exact canonical scale. Compare the [current native/reference links](comparison.md) and [proportion study](proportion-audit.md). Shores remain original interpretations. |
| Owner corrections | Fulbrosia lies south of Jura, Ulgracia south of Sarion, and Frost Palace occupies its approved inland snowfield. The five specifically approved relation changes remain the only technical-rule exception; no new rule is edited. |
| Contract versus canon | Read the [contradictions](../docs/research/tensura-world-2026-11-19/contradictions.md) and inert SVG alternatives for the Imperial mountain bearing, Amrita’s below-castle relation versus eastern reserve, Sainte’s coastal setting, Filtwood’s binding and other fixed-contract differences. Do not silently treat a gameplay mask or reserved entrance as surveyed canon. |
| Initial roads and future capacity (C18) | The fixed source contract retains mandatory main-road corridors and representative city capacity. Their presence does not assert that Tempest’s later paved highways or developed capital already exist at S1E10. The inert early-trail alternative and runtime gating remain Claude’s integration work. |
| Water style (C23) | The Ulgr interface is now 92→91. Laura’s unchanged 154→137 head transition remains a 17-block style/fluid review, separately source-qualified as mountain-waterfall context. The diagnostic’s ordinary two-block threshold is not an owner-set exact waterfall cap. All 13 finite lake bank/depth/contact checks pass; final fluid columns/noise remain separate. |
| Biomes and climate (C10) | Jungle saturation, Minecraft habitat shares and the retained small red badlands crescent are authored/server choices, not proof of canonical climate. Source roles and the inert no-red alternative remain explicit. |
| Missing or partial places | The [location inventory](location-index.md) has 142 entries and 42 physical follow-ups, including unlocated capitals, minor countries and city interiors. It is not a claim that the entire wiki was read or that 58 markers represent 58 complete cities. Keep source-backed proposals distinct from registered terrain and put unresolved lore/contract choices in the PR. |

All technical conversion, live structure placement, final-noise/fluid acceptance and deployment belong to Claude’s handoff. This creative guide does not claim those tasks complete.
