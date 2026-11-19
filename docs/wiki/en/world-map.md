# Tensura world map

The Tensura continent is Lerfing’s map, imported as it was drawn. You begin Life 2 on the northern edge of Jura, near **(1780, -150)**. Follow the road north towards Dwargon’s gate at **(1900, -500)**. Tempest lies far to the south, at **(1720, 900)**, across the forest’s dangerous inner rings. In every table the horizontal coordinates are **X, Z in blocks**. North means decreasing Z, east means increasing X. [Jura rings and first journey](jura-rings.md) · [Nederlands](../nl/world-map.md)

Survey radii and preferred placement coordinates may change.

Use the atlas to see where neighbouring countries meet. On BlueMap, select **Tensura (Life 2)** for the continent or the Mortal Realm for Wayfarer’s Rest. The public map displays terrain and markers without live player dots. The static atlas is available even when the web map is offline. [Annotated continent atlas](../../previews/lerfing_regions.png) · [BlueMap](https://map.daviddelporte.com)

## The 43 map markers

These are the geographical reference points in `minecraft:overworld`. A marker can represent a river, an entire battle or a country. Some western states share a terrain region. The region column identifies the cell under the pin. For a building entrance, use the settlement and structure tables below. [Map coordinates](../../../pack/config/ttl/canon_regions.json) · [Regions and anchors on the map](../../previews/lerfing_regions.png) · Map by Lerfing, giant trees by Paulzero

| Marker | X, Z | Terrain region |
| --- | --- | --- |
| Tempest (Rimuru, capital of the Federation) | 1720, 900 | Jura |
| Sealed Cave (Veldora's prison, Rimuru's birthplace) | 1380, 560 | Jura |
| Old goblin village (Rigurd's tribe) | 1390, 710 | Jura |
| Lake Siss | 3050, 750 | Inland water |
| Lizardmen's caverns (Gabiru, Avalos) | 3300, 1200 | Lake Siss marsh |
| Orc War battlefield (Lake Siss marsh) | 3600, 1250 | Lake Siss marsh |
| Great Ameld River source (Canaat foothills) | 2500, -200 | Dwargon |
| Great Ameld River mouth | 4580, 2300 | Coastal water |
| Hidden ogre village (Kijin homeland, burned) | 2150, 400 | Jura |
| Treyni's grove (Dryad sanctuary) | 1920, 1540 | Jura |
| Dwargo (Dwargon cavern capital) | 1900, -600 | Dwargon |
| Dwargon main gate | 1900, -500 | Dwargon |
| Dragon's Nest (highest peak of the Great Canaat Mountains) | 2420, -1536 | Dwargon |
| Marris (Falmuth capital) | -2000, -1450 | Falmuth |
| Siltrosso | -2450, -1650 | Falmuth |
| Blumund capital (Londo) | -450, 150 | Blumund |
| Ballachia | -1660, -460 | Englassia |
| Englassia capital (Lura): Freedom Academy, Free Guild HQ | -2150, -410 | Englassia |
| Holy City Lubelius (Lune) | -2550, -700 | Lubelius |
| Sacred Mountain (Inner Sanctum, Luminous) | -2980, -900 | Lubelius |
| Coleus | -3080, 600 | Damargania |
| Morgdahl | -2440, 740 | Morgdahl |
| Nostraille | -1780, 550 | Nostraille |
| Ghastone | -2000, 300 | Englassia |
| Rostia | -2100, 1000 | Raja |
| Yuzalgh | -1580, 650 | Yuzalgh |
| Yggdonia | -1400, 300 | Yggdonia |
| Filtwood | -900, 700 | Ulgracia |
| Raja | -2050, 760 | Raja |
| Sainte Malukshure | -2500, 1300 | Fulbrosia |
| Elmine (Sarion capital in the Divine Tree) | 1100, 2760 | Sarion |
| Galut / Ulgr Nature Park (Ulgracia) | -1040, 1060 | Ulgracia |
| Heaven Tower (Dagruel, Damargania) | -4500, 560 | Damargania |
| Golden City of El Dorado (Leon) | -3300, 4300 | El Dorado |
| El Dorado volcano | -2850, 4600 | El Dorado |
| Frost Palace (Guy Crimson) | -1980, -4300 | Ice Continent |
| Nasca (Eastern Empire capital) | 5100, -2680 | Eastern Empire |
| Great Holy Mountain (Velgrynd) | 5120, -1860 | Eastern Empire |
| Amrita (Jistav capital) | 6100, -650 | Jistav |
| Clayman's Castle | 5620, -900 | Jistav |
| City of the Forgotten Dragon (Milim) | 4680, 840 | Milim's Domain |
| Laura (Eurazania capital, rebuilt) | 3300, 2600 | Eurazania |
| Jia (Fulbrosia capital, Frey) | -2700, 1500 | Fulbrosia |

## Where to find the builds

All rows in the next table are in **`minecraft:overworld`**. Use the search centre as a waypoint. The radius gives the configured search range in blocks, and the actual entrance depends on dry, suitable ground. Yasuke or another operator can read the saved placement with `/ttl build where <id>`. Changes to the pack or a world reset can move the destination. For example, the Forgotten Dragon City search starts at **(4680, 840)**, on the plain east of Lake Siss. [Build manifests](../../../design/builds) · [Recorded staging checks](../../HANDOFF.md)

| Destination | Build ID | Search centre X, Z | Radius |
| --- | --- | --- | --- |
| Amrita — Buried Gallery of Jistav | `amrita` | 6100, -650 | 128 |
| Ballachia — The Freed Travellers' Yard | `ballachia` | -1660, -460 | 128 |
| Blumund — Londo | `blumund` | -450, 150 | 128 |
| Clayman's Castle — the Puppet Nation of Jistav | `clayman_castle` | 5620, -900 | 160 |
| Coleus — The Palace of Herbaria | `coleus` | -3080, 600 | 64 |
| The Dragon's Nest | `dragons_nest` | 2420, -1536 | 32 |
| Golden City of El Dorado — Leon’s Audience Court | `el_dorado` | -3300, 4300 | 160 |
| Elmine — Terrace of the Divine Tree | `elmine` | 1100, 2760 | 128 |
| Englassia — Lura | `englassia` | -2150, -410 | 160 |
| City of the Forgotten Dragon — Milim's domain | `forgotten_dragon_city` | 4680, 840 | 128 |
| The Frost Palace — Guy Crimson's gate | `frost_palace` | -1980, -4300 | 160 |
| Scorching God Mountain — Velgrynd’s sanctuary | `great_holy_mountain` | 5120, -1860 | 64 |
| Heaven Tower — Holy Void of Damargania | `heaven_tower` | -4500, 560 | 64 |
| Jia — Frey's Landing Court | `jia` | -2700, 1500 | 160 |
| Laura — capital of the Beast Kingdom of Eurazania | `laura` | 3300, 2600 | 256 |
| Holy City Lubelius — Lune | `lubelius` | -2550, -700 | 160 |
| Marris — Falmuth | `marris` | -2000, -1450 | 128 |
| Morgdahl — The Timber Landing | `morgdahl` | -2440, 740 | 96 |
| Nasca — Imperial audience court | `nasca` | 5100, -2680 | 96 |
| Nostraille — The Wool Hall | `nostraille` | -1780, 550 | 48 |
| Raja — The Old Lakeside Workings | `raja` | -2050, 760 | 48 |
| Sacred Mountain — the seal of the Inner Sanctum | `sacred_mountain` | -2980, -900 | 128 |
| The Sealed Cave: Veldora's prison, Rimuru's birthplace | `sealed_cave` | 1380, 560 | 128 |
| Siltrosso — The Rosso counting court | `siltrosso` | -2450, -1650 | 96 |
| The gate to the Dwelling of the Spirits | `spirit_gate` | 1540, 1080 | 64 |
| Treyni's shrine | `treyni_shrine` | 1958, 1540 | 132 |
| Ulgr Nature Park — The Spirit Trail | `ulgr_nature_park` | -1040, 1060 | 64 |

**Two entrances with fixed horizontal coordinates.** Tempest’s arrival green is at **(1720, 900)** in `minecraft:overworld`. The road ends at the physical Dwargon gate at **(1900, -500)** in the same dimension, cut into the southern face of the Canaat Mountains. The capital and gate dots in the atlas record the geographical references. The green and the physical gate make better walking destinations. [Tempest](../../../pack/kubejs/server_scripts/ttl/life/tempest.js) · [Dwargon](../../../pack/kubejs/server_scripts/ttl/life/dwargon.js)

## Seven settlements and sites assembled in the world

Tensura assembles these sites from its own structure pieces in **`minecraft:overworld`**. It searches the nominal point and nearby candidates up to 64 blocks away. A shore village needs both water and dry land. A jigsaw start is the point from which the pieces grow, so its last house may be much farther away. Operators can check the stored start with `/ttl landmark where <id>`. [Runtime locations](../../../design/data/landmarks.toml)

| Site | Landmark ID | Nominal X, Z |
| --- | --- | --- |
| Old goblin village (Rigurd's tribe) | `goblin_village` | 1390, 710 |
| Lizardmen's village on Lake Siss | `lizardmen_village` | 2900, 1020 |
| Lizardmen's caverns (Gabiru, Avalos) | `lizardmen_caverns` | 3300, 1200 |
| Orc camp at the Orc War battlefield | `orc_camp` | 3600, 1250 |
| Dwarf village on the Dwarven Road | `dwarf_village` | 2000, -110 |
| Burned ruin at the hidden ogre village | `ogre_village_ruin` | 2150, 400 |
| Treyni's grove (dryad sanctuary) | `treyni_grove` | 1920, 1540 |

## Other dimensions and the Last Wish trials

Use the story transitions to enter these dimensions. The Spirit Gate in the overworld carries a reborn player to the Dwelling once the destination exists. Its return arch brings you back to the gate. The test hut belongs to the build checker. [Spirit Gate travel](../../../pack/kubejs/server_scripts/ttl/life/spirit_domain.js)

| Place | Dimension | X, Z | Position |
| --- | --- | --- | --- |
| Wayfarer’s Rest (`mortal_spawn`) | `ttl:mortal_realm` | 0.5, 5.5 | Life 1 arrival, surface height |
| Spirit Corridor hall (`spirit_corridor_hall`) | `ttl:spirit_corridor` | 0.5, 0.5 | Arrival at Y 65 |
| The Dwelling of the Spirits (`spirit_dwelling`) | `ttl:spirit_domain` | 0, 0 | Fixed anchor at Y 64 |
| Test hut (`test_hut`) | `ttl:spirit_corridor` | 2500, 0 | Fixed anchor at Y 64 |
| Walpurgis Hall (`walpurgis_hall`) | `ttl:walpurgis` | 0, 0 | Fixed arrival at Y 64 beside the council chamber |
| Walpurgis Banquet Floor (`walpurgis`) | `ttl:walpurgis` | 52, -39 | Fighting floor centre at Y 61, radius 17 |
| Ramiris’s Labyrinth (`labyrinth`) | `tensura:labyrinth` | 16, 537 | Colossus hall centre at Y 38, fighting radius 38 |

**Walpurgis and the Labyrinth.** In Life 2, the throne dais in Clayman’s Castle opens the way to Walpurgis Hall for Legendary skill holders, players with the Demon Lord or True Hero story stage, invited guests and fighters booked for Walpurgis. The Banquet Floor is beside the council chamber. A Labyrinth match takes you directly to Ramiris’s Colossus hall once the room has generated. [Matches and entry](arenas.md) · [Arena settings](../../../design/data/arenas.toml)

All ten Trial of the Soul arenas are in **`ttl:spirit_corridor`**. Each row gives the arena centre. Your Last Wish sends you to its own starting tile inside the corresponding arena. [Trial definitions](../../../pack/kubejs/server_scripts/ttl/life/trial_defs.js)

| Wish | Template | Centre X, Z |
| --- | --- | --- |
| Strength | `trial_strength` | 1000, 0 |
| Vengeance | `trial_vengeance` | 1100, 0 |
| Protection | `trial_protection` | 1200, 0 |
| Knowledge | `trial_knowledge` | 1300, 0 |
| Hunger | `trial_hunger` | 1400, 0 |
| Freedom | `trial_freedom` | 1500, 0 |
| Deceit | `trial_deceit` | 1600, 0 |
| Creation | `trial_creation` | 1700, 0 |
| Dominion | `trial_dominion` | 1800, 0 |
| Survival | `trial_survival` | 1900, 0 |
