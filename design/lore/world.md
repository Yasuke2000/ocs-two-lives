# The Tensura world: canon geography for Life 2

The Life 2 overworld is the canon continent of *That Time I Got Reincarnated as a Slime*. It is generated from
`pack/config/ttl/canon_map.txt` (one character per chunk) and `pack/config/ttl/canon_regions.json` (per region:
climate knobs, biome palette, banner subtitle; plus named landmarks). This file is the lore record behind those
values. World 0,0 = Tempest.

**Research note (18/11/2026).** tensura.fandom.com refuses direct fetches (HTTP 402 and bot walls on its mirrors),
so the facts below come from search-engine extracts of the wiki pages listed under each region, plus the
light novel, manga and anime. Items marked *(unverified)* could not be checked against a source; treat them as our
own choice. Two maps were used: the political fan map (`17.png`, 2800x2050, source of the grid and of every `ref`
coordinate) and an illustrated terrain map (`16.png`, Dragon's Nest, Sealed Cave, volcanoes, the Divine Tree).

Coordinates: `ref` = pixel on the political map. World ≈ (ref − origin [1792, 1141]) × 3.89 blocks at the current
`--width 10000`. World positions below are rounded to about 10 blocks.

## Continent overview

The Magic Continent: the Western Nations and the Great Jura Forest in the centre, the Barren Lands in the far
west, the Eastern Empire in the far east, the Great Canaat Mountains north-central between Jura and the north
coast, the Ice Continent to the north, El Dorado to the south-west. Demon Lords hold most of the land: Dagruel and
Luminous in the west, Rimuru in the centre, Milim in the south-east.
Source: https://tensura.fandom.com/wiki/Magic_Continent, https://tensura.fandom.com/wiki/Central_World

## Regions

Grid letter, name, `banner_subtitle`, then lore, terrain and landmarks.

### J: Jura-Tempest Federation (ジュラ・テンペスト連邦国)

- **Lore.** The Great Jura Forest, Veldora's old hunting ground. After Veldora was sealed it filled with goblins,
  direwolves, ogres, lizardmen, dryads and orcs. Rimuru united them into the Jura-Tempest Federation, a monster
  nation that trades with Dwargon and Blumund.
- **Terrain.** A **temperate** primeval forest, not a jungle: dense dark forest and ancient forest, with birch
  stands and clearings around Tempest. It is lower and rolling in the south and rises to hills where it meets the
  Canaat range in the north. Lake Siss sits in the centre, ringed by marsh and limestone caves. The Great Ameld
  River comes down from the Canaat foothills, feeds Lake Siss and splits the forest into a western half and an
  eastern, dryad-governed half before it flows south-east to the sea through Milim's lands.
- **Landmarks** (ref → world):
  - Tempest, the capital: [1790, 1122] → (-10, -70).
  - Sealed Cave (Veldora, Rimuru's birthplace; later a hipokute farm and dungeon): [1745, 1078] → (-180, -245),
    north-west of Tempest. The illustrated map puts the cave west of the lake.
  - Old goblin village (Rigurd's tribe): [1762, 1098] → (-115, -165).
  - Lake Siss: [1955, 1178] → (635, 145). On the political map it is about 570 x 200 blocks.
  - Lizardmen's caverns (Gabiru, Avalos): [1962, 1214] → (660, 285), on the south shore.
  - Orc War battlefield (Lake Siss marsh): [1995, 1240] → (790, 385). Geld's horde marched north along the Ameld
    to the lake.
  - Source of the Great Ameld River: [2037, 938] → (955, -790).
  - Hidden ogre village (the Kijin homeland, burned by the orcs): [2060, 965] → (1045, -685), north-eastern hills
    *(placement unverified)*.
  - Treyni's grove, the dryad sanctuary: [2150, 1100] → (1395, -160), east of the Ameld.
- **Biomes (rings, 18/11/2026).** Veldora's leaked magicule soaks the forest, so the biome depends on the
  distance from the border and from Tempest (`zones` in `canon_regions.json`; Tensura's area magicule per biome:
  every unlisted biome 500, dark_forest +1,500, tensura:ancient_forest +19,500). **Rim** (safe): within 280 +- 50
  blocks of Jura's border, forest 4, birch 3, old_growth_birch 2, flower_forest 2, plains 2, swamp 1; the Life 2
  arrival is here, on the road to the Dwargon gate (`design/data/arrival.toml`). **Core**: within 200 +- 50 blocks
  of Tempest, ancient_forest 6, dark_forest 3 (labyrinth trees). **Middle**: everything between, dark_forest 7,
  ancient_forest 2. Ring edges are ragged fringes of whole patches. Peaks are replaced by stony_peaks and
  windswept_forest so the forest never gets snowy peaks (both are safe biomes). Erosion goes to 0.3 for rolling
  ground. Before this the palette was one random mix (dark_forest 4, ancient_forest 3, forest 3 ...) everywhere.
- Sources: https://tensura.fandom.com/wiki/Great_Jura_Forest, https://tensura.fandom.com/wiki/Lake_Siss,
  https://tensura.fandom.com/wiki/Great_Ameld_River, https://tensura.fandom.com/wiki/Orc_War,
  https://tensura.fandom.com/wiki/Sealed_Cave, https://tensura.fandom.com/wiki/Jura-Tempest_Federation

### W: Lizardmen's Marsh of Lake Siss (シス湖 — 蜥蜴人族の湿地帯), new and not painted yet

- **Lore.** A large expanse of marsh and limestone formations on the shores of Lake Siss. Its caverns form a natural
  labyrinth that is the lizardmen's fortress and seat of government. The lizardmen live off the lake's fish.
- **Terrain.** Flat wetland with mangrove_swamp 4 and swamp 4. Mangrove is the only biome where Tensura places its
  surface lizardman villages, and swamp holds its underground ones. Erosion 0.75 keeps it flat.
- **Grid.** Paint `W` as a ring 6–12 chunks wide around the lake (see the grid fixes below). The region is defined
  with empty `seeds`, so `canon_map.py` ignores it.

### D: Armed Nation of Dwargon (武装国家ドワルゴン)

- **Lore.** The dwarf kingdom of Gazel Dwargo, founded about a thousand years ago by Hero King Guran Dwargo in a
  natural hollow at the foot of the Great Canaat Mountains. It is an underground cavern city behind fortified
  gates, a trade hub that stays neutral. The Great Canaat Mountains are the largest range on the continent: some
  peaks rise higher than Everest, dragons grow stronger with altitude, and the Dragon's Nest sits on the highest
  peak. The range makes invasion over the mountains impractical.
- **Terrain.** High, cold mountains with meadows and conifer valleys at their feet. Erosion goes to −0.72 (was
  −0.9) so the city's base still has valleys while the core stays alpine. Vanilla keeps choosing the peaks:
  jagged and frozen peaks at temperature −0.3.
- **Landmarks:**
  - Dwargo, the cavern capital: [1869, 836] → (300, -1185).
  - Main gate, facing Jura: [1872, 868] → (310, -1060).
  - Dragon's Nest: [1860, 700] → (265, -1715).
- **Biomes.** meadow 3 (dwarf villages), grove 2, windswept_hills 2, windswept_forest 2, snowy_slopes 2,
  old_growth_spruce_taiga 1, taiga 1, windswept_gravelly_hills 1.
- **Distances.** The trip from the goblin village to Dwargon takes about two months on foot and three days on
  Tempest wolves.
- Sources: https://tensura.fandom.com/wiki/Armed_Nation_of_Dwargon,
  https://tensura.fandom.com/wiki/Great_Canaat_Mountains, https://tensura.fandom.com/wiki/In_the_Kingdom_of_the_Dwarves,
  https://tensura.fandom.com/wiki/Head_for_the_Dwarf_Kingdom

### E: Eastern Empire (東の帝国 — 東方連合統一帝国)

- **Lore.** The great military empire of the far east under Emperor Rudra. Its capital, Nasca, stands beside the
  Great Holy Mountain, home of its guardian dragon Velgrynd.
- **Terrain.** Broad temperate lowland of plains, forest and taiga. The illustrated map shows a volcano (the Holy
  Mountain), an inland lake by the capital and forest in the south-east.
- **Landmarks:**
  - Nasca: [2275, 763] → (1880, -1470).
  - Great Holy Mountain: [2230, 680] → (1705, -1795).
- **Biomes.** plains 3, forest 2, taiga 2, birch 1, meadow 1, sunflower_plains 1, windswept_hills 1,
  old_growth_pine_taiga 1.
- Sources: https://tensura.fandom.com/wiki/Magic_Continent, https://tensura.fandom.com/wiki/Central_World

### P: Puppet Nation of Jistav (傀儡国ジスターヴ)

- **Lore.** Clayman's former domain, now ruled jointly by Rimuru and Milim and governed by the dark-elf elder Eva.
  Its capital, Amrita, was founded 2,000 years ago as a haven for dark elves. The country's position limits its
  large-scale trade to Dwargon and the Eastern Empire.
- **Terrain.** Gloomy, hilly, isolated country: dark forest, taiga and miasmic hollows left by the puppet master.
  The illustrated map draws mountains. Temperature is retuned 0.3 → 0.0 (it sits between the cold Empire and
  Jura) and erosion to −0.3 for hills.
- **Landmarks:**
  - Amrita: [2444, 1012] → (2535, -500).
  - Clayman's Castle: [2470, 965] → (2635, -685) *(position unverified)*.
- **Biomes.** dark_forest 3, taiga 2, windswept_hills 2, tensura:miasmic_plains 2, old_growth_spruce_taiga 1,
  swamp 1.
- Sources: https://tensura.fandom.com/wiki/Puppet_Nation_of_Jistav, https://tensura.fandom.com/wiki/Amrita,
  https://tensura.fandom.com/wiki/Clayman

### M: Milim's Domain (ミリム領 — 忘れられた竜の都)

- **Lore.** The south-eastern lands of Milim Nava. Her capital is the City of the Forgotten Dragon, run by the
  Dragon Faithful and peopled by dragonewts, with no army beyond its priest-warriors. It lies south of Jura and
  east of Eurazania. The domain is poor and underdeveloped until Tempest helps it, and the Great Ameld River
  crosses it on the way to the sea.
- **Terrain.** Dry, rugged savanna and badland plateaus with a river valley and a lake by the capital.
  Erosion is −0.1 for broken plateaus.
- **Landmarks:**
  - City of the Forgotten Dragon: [2244, 1295] → (1760, 600).
  - Mouth of the Great Ameld River: [2420, 1340] → (2445, 775).
- **Biomes.** savanna 2, badlands 2, savanna_plateau 2, wooded_badlands 1, windswept_savanna 1,
  tensura:barren_land 1, desert 1.
- Sources: https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon, https://tensura.fandom.com/wiki/Magic_Continent

### B: Beast Kingdom of Eurazania (獣王国ユーラザニア)

- **Lore.** Carrion's kingdom of beastmen, south of Jura and east of Fulbrosia. It is an agricultural state with
  fertile soil and a **tropical climate**, famous for its fruit. Milim destroyed its old capital, and Tempest helped
  build the new one, Laura.
- **Terrain.** Tropical savanna and open jungle with farmland. Peaks are replaced by stony_peaks and
  windswept_savanna instead of vanilla badlands.
- **Landmark.** Laura: [2102, 1380] → (1205, 930).
- **Biomes.** sparse_jungle 3, savanna 3, jungle 2, plains 1, bamboo_jungle 1, savanna_plateau 1.
- Sources: https://tensura.fandom.com/wiki/Beast_Kingdom_of_Eurazania, https://tensura.fandom.com/wiki/Carrion

### H: Harpy Queendom of Fulbrosia (天翼国フルブロジア)

- **Lore.** Frey's sky kingdom of harpies, south of Jura and west of Eurazania. The country sits on top of a
  mountain range on Jura's border, and its capital is Jia.
- **Terrain.** A high, windswept mountain spine with pine forest on the illustrated map. Temperature drops 0.45 →
  0.3 and vegetation 0.6 → 0.3 (the old values bred jungle), and erosion is −0.6 for mountains. Vanilla stony
  peaks fit.
- **Landmark.** Jia: [1856, 1475] → (250, 1300).
- **Biomes.** windswept_hills 3, windswept_forest 2, meadow 2, old_growth_pine_taiga 2, sparse_jungle 1,
  savanna_plateau 1.
- Sources: https://tensura.fandom.com/wiki/Harpy_Queendom_of_Fulbrosia, https://tensura.fandom.com/wiki/Frey

### S: Sorcerous Dynasty of Sarion (魔導王朝サリオン)

- **Lore.** Emperor Elmesia's elven empire of 13 vassal kingdoms on Jura's southern border. Its capital, Elmine,
  is built into and on the **Divine Tree**, a colossal tree as tall as the highest mountains and one of two
  surviving holy relics made by Veldanava.
- **Terrain.** Lush, magical old-growth forest with flower meadows. Ancient forest gives the giant trees, and the
  Divine Tree itself should be a custom build at Elmine.
- **Landmark.** Elmine and the Divine Tree: [1522, 1440] → (-1050, 1165).
- **Biomes.** tensura:ancient_forest 3, forest 2, flower_forest 2, birch 2, old_growth_birch 2, cherry_grove 1,
  plains 1.
- Sources: https://tensura.fandom.com/wiki/Sorcerous_Dynasty_of_Sarion, https://tensura.fandom.com/wiki/Divine_Tree,
  https://tensura.fandom.com/wiki/Elmesia_El_Ru_Sarion

### U: Republic of Ulgracia (ウルグレイシア共和国)

- **Lore.** A republic south of Sarion and near Jura that lives from trade with Sarion and from farming. Its
  citizens are elemental magic users, and citizenship requires a spirit-contract ceremony. Its capital is Galut.
- **Terrain.** Gentle farmland and flower country.
- **Landmark.** Galut / Ulgr Nature Park: [1577, 1536] → (-835, 1535). The fan map's dot is "Ulgr Nature Park",
  so Galut's exact site is *unverified*.
- **Biomes.** plains 3, flower_forest 2, sunflower_plains 1, forest 1, meadow 1, cherry_grove 1.
- Source: https://tensura.fandom.com/wiki/Republic_of_Ulgracia

### R: Kingdom of Blumund (ブルムンド王国)

- **Lore.** A small kingdom on the Jura border, next to Falmuth (later Farmenas) and the Federation. It is home to
  Fuze's Free Guild branch and the adventurers Kabal, Eren and Gido, and it is Tempest's first human partner.
- **Terrain.** Mixed farmland and forest that turns into Jura's woods on the east side.
- **Landmark.** Blumund's capital (Londo on the fan map): [1604, 1119] → (-730, -85). The canon capital name is
  *unverified*.
- **Biomes.** plains 3, forest 3, birch 2, flower_forest 1, sunflower_plains 1.
- Source: https://tensura.fandom.com/wiki/Kingdom_of_Blumund

### F: Kingdom of Falmuth (ファルムス王国)

- **Lore.** A rich trade kingdom west of Dwargon with its capital at Marris. King Edmaris started the Tempest Holy
  War, and after Rimuru destroyed his army the kingdom became Farmenas under Yohm. The Migam frontier province
  borders the forest, and Count Muller's march lies on the Blumund border.
- **Terrain.** Plains and farmland with forested hills, rising to mountains on the Dwargon side.
- **Landmarks:**
  - Marris: [1556, 950] → (-920, -745).
  - Ballachia: [1538, 1102] → (-990, -150). On the fan map it is a city-state that the grid merged into Falmuth.
- **Biomes.** plains 3, forest 2, birch 1, sunflower_plains 1, meadow 1, windswept_hills 1, taiga 1.
- Sources: https://tensura.fandom.com/wiki/Kingdom_of_Falmuth, https://tensura.fandom.com/wiki/Kingdom_of_Farmenas,
  https://tensura.fandom.com/wiki/Tempest_Holy_War

### G: Kingdom of Englassia (イングラシア王国)

- **Lore.** The leading power of the Western Nations. Its royal capital holds the Free Guild headquarters (Yuuki)
  and the Freedom Academy, where Rimuru taught Shizu's students. A school outing runs south from the capital to
  the town of Guratol.
- **Terrain.** The illustrated map's "Western Nations": green lowland plains with a lake.
- **Landmarks:**
  - Royal capital (Lura on the fan map), with the Freedom Academy and the Free Guild HQ: [1310, 1086] → (-1875, -215).
  - Siltrosso: [1420, 972] → (-1445, -655).
- **Biomes.** plains 4, forest 2, sunflower_plains 1, flower_forest 1, birch 1, meadow 1.
- Sources: https://tensura.fandom.com/wiki/Kingdom_of_Englassia,
  https://tensura.fandom.com/wiki/Extra:_Rimuru's_Glamorous_Life_as_a_Teacher,_Part_2

### L: Holy Empire of Lubelius (神聖法皇国ルベリオス)

- **Lore.** The theocratic seat of the Western Holy Church and secretly the domain of the vampire Demon Lord
  Luminous Valentine. The **Sacred Mountain**, its holiest site, carries the Inner Sanctum at its summit. Under the
  human holy city lies the Night Garden, the underground capital for its non-human subjects. Hinata's Holy Knights
  are based here.
- **Terrain.** Highland country: alpine meadows and forest below one dominant holy mountain. The illustrated map
  draws a cathedral among mountains. Erosion is −0.4 and the region is cool.
- **Landmarks:**
  - Holy City (Lune on the fan map): [1062, 1020] → (-2840, -470).
  - Sacred Mountain: [980, 905] → (-3160, -920).
- **Biomes.** meadow 3, forest 2, plains 2, taiga 1, windswept_forest 1, flower_forest 1 (Luminous's rose
  gardens), grove 1.
- Sources: https://tensura.fandom.com/wiki/Holy_Empire_of_Lubelius, https://tensura.fandom.com/wiki/WN:Holy_City_Lubelius,
  https://tensura.fandom.com/wiki/Luminous_Twilight_Valentine

### V: Holy Void of Damargania (聖虚ダマルガニア)

- **Lore.** Dagruel's country of giants in the Barren Lands of the far west. Most of it is the **Desert of Death**:
  once bountiful land, made uninhabitable and still magicule-contaminated by the ancient seven-day battle between
  Guy and Milim. Its capital is the Heaven Tower.
- **Terrain.** A flat, inhospitable sand sea with badland breaks. Erosion goes to 0.5 for flatness.
- **Landmark.** Heaven Tower: [414, 1186] → (-5360, 175).
- **Biomes.** tensura:desert_of_death 4, tensura:barren_land 3, desert 2 (orc villages), badlands 1,
  eroded_badlands 1.
- Sources: https://tensura.fandom.com/wiki/Holy_Void_of_Damargania, https://tensura.fandom.com/wiki/Dagruel,
  https://tensura.fandom.com/wiki/Heaven_Tower

### I: Ice Continent (氷の大陸 — 白氷宮)

- **Lore.** Guy Crimson's frozen northern continent, with his Frost Palace (White Ice Palace). The illustrated map
  calls it the "Tundral Waste" and shows a great rift and ice-floe islands.
- **Terrain.** Snowfields, ice spikes and frozen peaks.
- **Landmark.** Frost Palace: [1345, 349] → (-1740, -3080).
- **Biomes.** snowy_plains 3, ice_spikes 2, snowy_slopes 2, snowy_taiga 1, grove 1.
- Sources: https://tensura.fandom.com/wiki/Ice_Continent, https://tensura.fandom.com/wiki/Frost_Palace,
  https://tensura.fandom.com/wiki/Guy_Crimson

### X: El Dorado (黄金郷エルドラド)

- **Lore.** The south-western continent, ruled alone by Demon Lord Leon Cromwell from the Golden City. A volcano
  at its centre supplies the precious metals that fund the country.
- **Terrain.** Hot, lush land with volcanoes, lakes and jungle (illustrated map). It uses wooded and plain badlands
  because vanilla badlands carry extra gold ore, and vanilla badlands peaks stay because they suit a gold
  country.
- **Landmarks:**
  - Golden City: [910, 1736] → (-3430, 2315).
  - Central volcano: [860, 1690] → (-3625, 2135).
- **Biomes.** sparse_jungle 2, jungle 2, savanna 2, wooded_badlands 2, badlands 1, bamboo_jungle 1,
  windswept_savanna 1.
- Sources: https://tensura.fandom.com/wiki/Golden_City_of_El_Dorado, https://tensura.fandom.com/wiki/WN:El_Dorado

### O, N, Y, Q, A: small Western Nations (Morgdahl, Nostraille, Yuzalgh, Yggdonia, Raja)

These five come from the fan political map. Only Raja is likely canon (a small Western Nations state); I could not
verify the other names in any source, so treat them as fan additions that fill the "Western Nations" band. Their
subtitles are English epithets, not Japanese names.

| Grid | Name | Landmark (ref → world) | Palette |
| --- | --- | --- | --- |
| O | Morgdahl, the south-coast river mouth | [1056, 1325] → (-2865, 715); Sainte Malukshure [1242, 1378]; Coleus [1030, 1209] | plains 3, forest 2, birch 1, swamp 1, savanna 1 |
| N | Nostraille, hill kingdom | [1322, 1207] → (-1830, 255); Ghastone, Rostia | plains 2, meadow 2, forest 2, windswept_hills 1 |
| Y | Yuzalgh, lakeside kingdom | [1448, 1200] → (-1340, 230) | forest 2, plains 2, birch 2, flower_forest 1 |
| Q | Yggdonia, birch realm (59 chunks) | [1550, 1174] → (-940, 130) | old_growth_birch 2, birch 2, flower_forest 1 |
| A | Raja, hills and old mines | [1593, 1281] → (-775, 545); Filtwood [1597, 1254] | plains 2, forest 1, meadow 1, windswept_hills 1 |

## Tempest (early): for the build team

This is the moment right after the ogres joined and were named Benimaru, Shuna, Shion, Souei, Hakurou and Kurobe.
It covers the anime's episodes 9–11 and light novel volume 1, before the Orc Lord war. Canon details come from the
LN, manga and anime. Where they differ, the anime look is used because players know it best.

**Who is there.** Rimuru and Ranga with the direwolves (now Tempest Wolves). Rigurd, the goblin lord, and the
named hobgoblins: Rigur, Gobta and the goblin riders. About 500 goblins, after the neighbouring tribes joined. The
dwarves from Dwargon: Kaijin (smith, the town's head of production) and the three brothers Garm (armour), Dold
(fine work and crafts) and Mildo (carpentry and architecture; silent). The six ogres turned kijin.

**State of the town.** It is a construction site, not a city. Rimuru had the village moved to open ground with
room to grow and running water nearby. Mildo surveys and lays out a planned grid, and Rimuru insists on proper
housing, sanitation and roads from day one.

- **Tents and lean-tos.** Most goblins still sleep in hide and cloth tents and rough shelters while houses go up.
  A tent quarter ringing the build site is the dominant look.
- **The first wooden houses.** Simple log or plank cabins with shingle or thatch roofs, raised on stone footings,
  some only framed. Mildo's crews build them in rows along cleared dirt streets. A few stand finished, more are
  half-built with scaffolding, and timber piles and sawhorses lie in between.
- **Kaijin's workshop and forge**, the first proper building. A stone hearth and chimney, an open-fronted smithy
  with anvils and quench tubs, a charcoal store and an ore pile. Kurobe (the ogre smith) works here with Kaijin,
  forging the first katana and armour for the kijin. Garm's armour corner is next to it.
- **Shuna's weaving house.** Shuna leads the goblinas in weaving and sewing clothes: looms, spinning wheels, dye
  vats and drying lines for cloth. Hell moth and spider silk are added later.
- **Meeting place.** A large covered hall or open pavilion in the centre, used for the leaders' councils (the
  ogres' acceptance, the lizardmen envoy, and planning against the orcs) and for communal meals. Shion's infamous
  cooking happens here.
- **Rimuru's house.** A modest house, slightly larger and better finished, near the meeting place.
- **Other pieces.** A training ground where Hakurou drills the hobgoblins and goblin riders, a storehouse for
  food and hides, a lumber yard and sawpit, a pottery or kiln spot, field plots being dug at the edge, a wolf
  pen and resting area for Ranga's pack, and a palisade gate on the forest road.

**Surroundings.** The settlement sits in a cleared hollow in dense temperate forest (oak and dark oak; Jura is
never jungle) with tree stumps on the cleared margins. A river or stream runs by the town for water and washing.
The anime shows a riverbank by the village; the LN states that water access drove the move, *exact layout
unverified*. Lake Siss is not next to the town: it is the lizardmen's lake, far off in the centre of the forest,
which needed an envoy (Gabiru) and an army march to reach.

**Distances in the build** (from `landmarks`):

| From | To | Distance | Note |
| --- | --- | --- | --- |
| Tempest [1790, 1122] → (-10, -70) | Sealed Cave [1745, 1078] → (-180, -245) | about 250 blocks, NW | In canon a short trip: Rimuru goes back on foot for hipokute grass |
| Tempest | Old goblin village (-115, -165) | about 140 blocks | Between the town and the cave |
| Tempest | Lake Siss (635, 145) | about 680 blocks, E | The lizardmen's marsh |
| Tempest | Dwargon gate (310, -1060) | about 1,040 blocks, N | Canon: three days by wolf, two months on foot |
| Tempest | Blumund capital (-730, -85) | about 720 blocks, W | |

The build should keep Tempest within about 64 blocks of world (0, 0). The landmark ref [1790, 1122] is the
map's city dot, about 70 blocks north of the grid origin.

## Scale

Canon scale cannot be reproduced. Two months on foot from the goblin village to Dwargon is hundreds of kilometres
(around 600 km at a forest pace of 10 km a day), which would make the continent several thousand kilometres wide
and millions of blocks in Minecraft. Every playable scale is a compression, so the question is gameplay
density.

Current scale: 10,000 blocks across the land, about 3.89 blocks per reference pixel. That puts Jura at about
2,860 x 2,270 blocks (12,900 chunks), Dwargon at 2,000 x 1,420, and the whole grid at 626 x 452 chunks plus the
1,600-block sea ring, about 0.5 M chunks to pregenerate.

| Width | Tempest → Dwargon | Jura | Grid + ring (chunks) | Verdict |
| --- | --- | --- | --- | --- |
| 8,000 | about 830 | 2,290 x 1,820 | about 0.36 M | Too tight: western micro-states shrink to 10 chunks or fewer |
| **10,000 (now)** | **about 1,040** | **2,860 x 2,270** | **about 0.5 M** | **Keep** |
| 12,000 | about 1,250 | 3,440 x 2,730 | about 0.7 M | Only if playtests show Jura crowded |
| 16,000 | about 1,660 | 4,580 x 3,630 | about 1.1 M | Too heavy, and too empty for about 10 players |

**Recommendation: keep 10,000.**

1. Jura, where every Life 2 player is reborn, already offers about 3.3 M square blocks (12,900 chunks). That is room for Tempest,
   the cave, Lake Siss, the goblin and lizardmen settlements, and dozens of player bases.
2. A walk to Dwargon of about 1,000 blocks (about 4 minutes on foot, 2 on a horse) feels like a journey without
   becoming a chore. Tensura flight and Spatial Motion shorten it further for strong players.
3. The cost stays at about 0.5 M chunks. 12,000 nearly doubles pregeneration and Distant Horizons LOD data, and
   10+ players will not fill the extra land.
4. The real problem is not size but missing water: the lake and river fixes below matter more than scale.

If more room around Tempest is wanted later, enlarge Jura in the grid (pull Blumund and Falmuth back by about 10
chunks) rather than scaling the whole continent.

## Grid issues (canon_map.txt) for the grid owner

1. **Lake Siss is missing.** The fan map's "Jura-Tempest Federation" label is printed over the lake, so the flood
   turned it into land. Only scattered `~` cells remain around chunks x 40–60, z −12..3. Paint a solid lake of
   about 36 x 13 chunks centred on world (635, 145), roughly x 350..930 and z 40..250. Canon calls it "extremely
   large", so 40 x 16 would be fine. Then ring it with `W` (Lizardmen's Marsh), 6–12 chunks wide, wider on the
   south shore where the caverns and the Orc War battlefield are.
2. **The Great Ameld River is broken into fragments.** It should be one continuous channel, 2–3 chunks wide: from
   the Canaat foothills (world 955, −790, on the Dwargon–Jura border) south into Lake Siss, out of the lake's east
   end, then south-east along the Jura–Milim border into Milim's Domain, past the City of the Forgotten Dragon's
   lake, to the sea at about (2445, 775). Canon says it splits Jura into a western half and an eastern, dryad
   half, and feeds Milim's lands.
3. **Add a stream near Tempest** if the build wants canon water access: one or two chunks of `~` running past
   world (0, 0) towards Lake Siss.
4. **The western river is missing.** It runs on the fan map from inland Lubelius to the coast at Coleus, along
   the Lubelius/Damargania border. Optional.
5. **City-states the grid absorbed:** Ballachia (into F), Doran, Filtwood, Coleus, Ghastone, Rostia and Siltrosso
   are dots or tiny fills on the fan map. They are fine as towns (landmarks) inside bigger regions.
6. **Jistav does not touch Dwargon.** Canon says its trade is limited to Dwargon and the Empire, so a thin `P`
   corridor along Dwargon's east flank would be more faithful. Cosmetic.
7. **Small fan nations.** O, N, Y and Q could not be verified as canon. Keep them as the generic Western Nations,
   or merge them into G and F if strict canon matters more than variety.
8. **Positions match canon:** Dwargon north of Jura; Falmuth west of Dwargon; Blumund between Falmuth and Jura;
   Sarion and Ulgracia south-west; Fulbrosia south (west of Eurazania); Eurazania south (east of Fulbrosia);
   Milim's domain south-east and east of Eurazania; Damargania far west; the Eastern Empire far east; the Ice
   Continent north; El Dorado south-west.
