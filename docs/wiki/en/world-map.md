# Tensura world map

You begin Life 2 on the northern edge of Jura, near **(271, -624)**. Follow the road north towards Dwargon’s gate at **(435, -1000)**. Tempest lies southwest, across the forest’s dangerous inner rings. In every table the horizontal coordinates are **X, Z in blocks**. North means decreasing Z, east means increasing X. [Jura rings and first journey](jura-rings.md) · [Nederlands](../nl/world-map.md)

Survey radii and preferred placement coordinates may change.

Use the atlas to see where neighbouring countries meet. On BlueMap, select **Tensura (Life 2)** for the continent or the Mortal Realm for Wayfarer’s Rest. The public map displays terrain and markers without live player dots. The static atlas is available even when the web map is offline. [Annotated continent atlas](../../audits/world-audit-2026-11-map.png) · [BlueMap](https://map.daviddelporte.com)

## The 43 map markers

These are the geographical reference points in `minecraft:overworld`. A marker can represent a river, an entire battle or a country. Some western states share a terrain region. The region column identifies the cell under the pin. For a building entrance, use the settlement and structure tables below. [Map coordinates](../../../pack/config/ttl/canon_regions.json) · [Cartographer’s source plate](https://i.redd.it/q1p4ksudqyah1.png)

| Marker | X, Z | Terrain region |
| --- | --- | --- |
| Tempest (Rimuru, capital of the Federation) | -11, -104 | Jura |
| Sealed Cave (Veldora's prison, Rimuru's birthplace) | -256, -343 | Jura |
| Old goblin village (Rigurd's tribe) | -163, -234 | Jura |
| Lake Siss | 888, 202 | Inland water |
| Lizardmen's caverns (Gabiru, Avalos) | 926, 398 | Lake Siss marsh |
| Orc War battlefield (Lake Siss marsh) | 1106, 539 | Jura |
| Great Ameld River source (Canaat foothills) | 1335, -1106 | Jura |
| Great Ameld River mouth | 3497, 1324 | Inland water |
| Hidden ogre village (Kijin homeland, burned) | 1460, -959 | Jura |
| Treyni's grove (Dryad sanctuary) | 1950, -223 | Jura |
| Dwargo (Dwargon cavern capital) | 419, -1661 | Dwargon |
| Dwargon main gate | 436, -1487 | Dwargon |
| Dragon's Nest (highest peak of the Great Canaat Mountains) | 370, -2402 | Dwargon |
| Marris (Falmuth capital) | -1286, -1040 | Falmuth |
| Siltrosso | -2026, -921 | Englassia |
| Blumund capital (Londo) | -1024, -120 | Blumund |
| Ballachia | -1384, -212 | Falmuth |
| Englassia capital (Lura): Freedom Academy, Free Guild HQ | -2626, -300 | Englassia |
| Holy City Lubelius (Lune) | -3977, -659 | Lubelius |
| Sacred Mountain (Inner Sanctum, Luminous) | -4423, -1286 | Lubelius |
| Coleus | -4151, 370 | Damargania |
| Morgdahl | -4009, 1002 | Morgdahl |
| Nostraille | -2560, 360 | Nostraille |
| Ghastone | -2364, 490 | Nostraille |
| Rostia | -2440, 975 | Nostraille |
| Yuzalgh | -1874, 321 | Yuzalgh |
| Yggdonia | -1329, 180 | Yggdonia |
| Filtwood | -1062, 616 | Raja |
| Raja | -1084, 763 | Raja |
| Sainte Malukshure | -2996, 1291 | Morgdahl |
| Elmine (Sarion capital in the Divine Tree) | -1471, 1629 | Sarion |
| Galut / Ulgr Nature Park (Ulgracia) | -1171, 2152 | Ulgracia |
| Heaven Tower (Dagruel, Damargania) | -7507, 245 | Damargania |
| Golden City of El Dorado (Leon) | -4805, 3241 | El Dorado |
| El Dorado volcano | -5077, 2991 | El Dorado |
| Frost Palace (Guy Crimson) | -2435, -4314 | Ice Continent |
| Nasca (Eastern Empire capital) | 2631, -2059 | Eastern Empire |
| Great Holy Mountain (Velgrynd) | 2386, -2511 | Eastern Empire |
| Amrita (Jistav capital) | 3552, -703 | Jistav |
| Clayman's Castle | 3693, -959 | Jistav |
| City of the Forgotten Dragon (Milim) | 2462, 839 | Inland water |
| Laura (Eurazania capital, rebuilt) | 1689, 1302 | Eurazania |
| Jia (Fulbrosia capital, Frey) | 349, 1819 | Fulbrosia |

## Where to find the builds

All rows in the next table are in **`minecraft:overworld`**. Use the search centre as a waypoint. The radius gives the configured search range in blocks, and the actual entrance depends on dry, suitable ground. Yasuke or another operator can read the saved placement with `/ttl build where <id>`. Changes to the pack or a world reset can move the destination. For example, the current Forgotten Dragon City search starts at **(2340, 905)**, while an older staging copy stood at **(2510, 575)**. Its map pin is in water. [Build manifests](../../../design/builds) · [Recorded staging checks](../../HANDOFF.md)

| Destination | Build ID | Search centre X, Z | Radius |
| --- | --- | --- | --- |
| Amrita — Buried Gallery of Jistav | `amrita` | 3552, -703 | 32 |
| Ballachia — The Freed Travellers' Yard | `ballachia` | -1384, -212 | 128 |
| Blumund — Londo | `blumund` | -1024, -120 | 64 |
| Clayman's Castle — the Puppet Nation of Jistav | `clayman_castle` | 3693, -959 | 160 |
| Coleus — The Palace of Herbaria | `coleus` | -4151, 370 | 48 |
| The Dragon's Nest | `dragons_nest` | 370, -2402 | 32 |
| Golden City of El Dorado — Leon’s Audience Court | `el_dorado` | -4808, 3240 | 48 |
| Elmine — Terrace of the Divine Tree | `elmine` | -1471, 1629 | 32 |
| Englassia — Lura | `englassia` | -2626, -300 | 64 |
| City of the Forgotten Dragon — Milim's domain | `forgotten_dragon_city` | 2340, 905 | 128 |
| The Frost Palace — Guy Crimson's gate | `frost_palace` | -2435, -4314 | 48 |
| Scorching God Mountain — Velgrynd’s sanctuary | `great_holy_mountain` | 2386, -2511 | 48 |
| Heaven Tower — Holy Void of Damargania | `heaven_tower` | -7507, 245 | 48 |
| Jia — Frey's Landing Court | `jia` | 349, 1819 | 96 |
| Laura — capital of the Beast Kingdom of Eurazania | `laura` | 1689, 1302 | 64 |
| Holy City Lubelius — Lune | `lubelius` | -3977, -659 | 64 |
| Marris — Falmuth | `marris` | -1286, -1040 | 64 |
| Morgdahl — The Timber Landing | `morgdahl` | -4009, 1002 | 96 |
| Nasca — Imperial audience court | `nasca` | 2631, -2059 | 96 |
| Nostraille — The Wool Hall | `nostraille` | -2560, 360 | 32 |
| Raja — The Old Lakeside Workings | `raja` | -1084, 763 | 48 |
| Sacred Mountain — the seal of the Inner Sanctum | `sacred_mountain` | -4423, -1286 | 48 |
| The Sealed Cave: Veldora's prison, Rimuru's birthplace | `sealed_cave` | -256, -343 | 128 |
| Siltrosso — The Rosso counting court | `siltrosso` | -2026, -921 | 96 |
| The gate to the Dwelling of the Spirits | `spirit_gate` | -210, 130 | 64 |
| Treyni's shrine | `treyni_shrine` | 1988, -223 | 132 |
| Ulgr Nature Park — The Spirit Trail | `ulgr_nature_park` | -1171, 2152 | 64 |

**Two entrances with fixed horizontal coordinates.** Tempest’s arrival green is at **(0, 0)** in `minecraft:overworld`. The road ends at the physical Dwargon gate at **(435, -1000)** in the same dimension. The capital and gate dots in the atlas record the geographical references. The green and the physical gate make better walking destinations. [Tempest](../../../pack/kubejs/server_scripts/ttl/life/tempest.js) · [Dwargon](../../../pack/kubejs/server_scripts/ttl/life/dwargon.js)

## Seven settlements and sites assembled in the world

Tensura assembles these sites from its own structure pieces in **`minecraft:overworld`**. It searches the nominal point and nearby candidates up to 64 blocks away. A shore village needs both water and dry land. A jigsaw start is the point from which the pieces grow, so its last house may be much farther away. Operators can check the stored start with `/ttl landmark where <id>`. [Runtime locations](../../../design/data/landmarks.toml)

| Site | Landmark ID | Nominal X, Z |
| --- | --- | --- |
| Old goblin village (Rigurd's tribe) | `goblin_village` | -163, -234 |
| Lizardmen's village on Lake Siss | `lizardmen_village` | 700, 344 |
| Lizardmen's caverns (Gabiru, Avalos) | `lizardmen_caverns` | 926, 398 |
| Orc camp at the Orc War battlefield | `orc_camp` | 1106, 539 |
| Dwarf village on the Dwarven Road | `dwarf_village` | 250, -740 |
| Burned ruin at the hidden ogre village | `ogre_village_ruin` | 1460, -959 |
| Treyni's grove (dryad sanctuary) | `treyni_grove` | 1950, -223 |

## Other dimensions and the Last Wish trials

Use the story transitions to enter these dimensions. The Spirit Gate in the overworld carries a reborn player to the Dwelling once the destination exists. Its return arch brings you back to the gate. The test hut belongs to the build checker. [Spirit Gate travel](../../../pack/kubejs/server_scripts/ttl/life/spirit_domain.js)

| Place | Dimension | X, Z | Position |
| --- | --- | --- | --- |
| Wayfarer’s Rest (`mortal_spawn`) | `ttl:mortal_realm` | 0.5, 5.5 | Life 1 arrival, surface height |
| Spirit Corridor hall (`spirit_corridor_hall`) | `ttl:spirit_corridor` | 0.5, 0.5 | Arrival at Y 65 |
| The Dwelling of the Spirits (`spirit_dwelling`) | `ttl:spirit_domain` | 0, 0 | Fixed anchor at Y 64 |
| Test hut (`test_hut`) | `ttl:spirit_corridor` | 2500, 0 | Fixed anchor at Y 64 |

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
