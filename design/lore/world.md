# The Tensura world: canon geography for Life 2

The Life 2 overworld is **Lerfing's Tensura map**, imported 1:1 (credit: [CREDITS.md](../../CREDITS.md); design:
[lerfing-import.md](../architecture/lerfing-import.md)). The land is Lerfing's terrain block for block; what we add is
the canon reading of it: which part of his continent is which nation, and where each canon place stands. **World
(0, 0) is Lerfing's (0, 0)**, nothing is shifted: x grows east, z grows south, north is smaller z.

Data behind this page: `design/data/anchors.toml` (every canon place in world coordinates, the one table the other
data translates from), `pack/config/ttl/canon_map.txt` (one character per chunk, generated from Lerfing's land mask
and the region polygons by `tools/lerfing_grid.py`), `pack/config/ttl/canon_regions.json` (names, colours, banners,
the polygons, landmarks) and [the region render](../../docs/previews/lerfing_regions.png). The renders and numbers
below come from `tools/lerfing/probe.py` and `tools/lerfing/jura_check.py` on the imported world (19/11/2026).

**Research note (18/11/2026).** tensura.fandom.com refuses direct fetches (HTTP 402 and bot walls on its mirrors),
so the canon facts below come from search-engine extracts of the wiki pages listed under each region, plus the
light novel, manga and anime. Items marked *(unverified)* could not be checked against a source; treat them as our
own choice. Lerfing's map is a game map, not a canon atlas: where it disagrees with canon we keep his terrain and say
so ("our reading").

## The map in numbers

| Fact | Value |
| --- | --- |
| Land | x −7400..7640, z −5540..5832 (15,040 × 11,372 blocks), Lerfing's painted continent plus two islands |
| Imported area | x −8064..8192, z −6016..6528 (the 800 region files of his export, 796,544 chunks); everything inside is his |
| Sea level | y 64; the highest point is the Canaat summit, y 316 at (2502, −1432) |
| Beyond the import | an ocean ring that our generator makes (deep sea, about 2,000 blocks beyond the coast), then the ordinary vanilla overworld: [world map for players](../../docs/wiki/en/world-map.md) |
| Biomes on land | plains is by far the commonest; desert and barren land in the far west, snowy plains on the Ice Continent, badlands (Milim, the Eastern Empire, El Dorado), jungle (Eurazania), swamp (Lake Siss), stony peaks (the Canaat). The Nether and End biomes of his export were repainted (soul sand valley → stony peaks, nether wastes → badlands or windswept gravelly hills, the end → barren land); blocks are untouched |
| Lerfing's own builds | a stilt-hut village on Lake Siss, ice crystals on the Ice Continent's south shore, builds on the north islet, a spawn chest at (−453, 73, 979), and Paulzero's giant trees: all kept ([CREDITS.md](../../CREDITS.md)) |

## How the continent lies

Read it against the [region render](../../docs/previews/lerfing_regions.png). Distances are straight lines from the
anchors in blocks.

- **Jura (J)** fills the middle: a 2,400 × 2,600-block rolling plain dotted with forested mesas and small lakes, x −100..2350, z −400..2200.
  **Tempest** stands in its middle at (1720, 900).
- **The Canaat Mountains and Dwargon (D)** rise directly **north** of Jura. The grey massif begins at about z −250 and climbs
  to the summit (y 316) at (2502, −1432); its lava lake sits at the top (x 2250..2500, z −1450..−1300). **Dwargon's gate**
  is at (1900, −500), 1,400 blocks due north of Tempest, with the city carved into the apron.
- **Lake Siss and its marsh (W)** lie **east of Jura**: the lake at (3050, 750), 1,340 blocks east of Tempest, ringed by the swamp x 2350..3950.
  The Great Ameld rises at the apron foot (2500, −200), feeds the lake and runs on to the eastern sea at (4580, 2300).
- **Milim's Domain (M)** is the huge badland to the **east** of the lake, x 3950..7700. **Jistav (P)** is its north-eastern
  corner, and the **Eastern Empire (E)** (with Velgrynd's volcano) the north-eastern landmass beyond it, north of z −1000.
- **Eurazania (B)** is the jungle peninsula **south-east** of Jura, below Lake Siss, running south to z 5100.
- **Sarion (S)** is the south-central peninsula **south** of Jura's west half, with Paulzero's giant trees (the Divine Tree, Elmine).
- **Blumund (R)** is Jura's **western** neighbour across a ~200-block channel at x ≈ −200 (Londo at (−450, 150), 2,300 blocks west of Tempest);
  **Ulgracia (U)** lies south of Blumund, **Falmuth (F)** north-west of it (the north arm and the north islet),
  **Englassia (G)** west of Blumund, **Lubelius (L)** on the north-west ridge.
- The **small western nations** (Morgdahl, Raja, Nostraille, Yuzalgh, Yggdonia) sit in the river-and-lake belt between Englassia and the Fulbrosia hills.
  **Fulbrosia (H)** holds the south-west crystal hills, **Damargania (V)** the desert and the Barren Lands in the far west.
- Two islands: the **Ice Continent (I)** far to the **north** (x −3850..2200, z −5540..−2800) and **El Dorado (X)** to the **south-west** (x −4600..−1900, z 3400..5700).

Against canon the layout holds: Dwargon north of Jura, Falmuth west of Dwargon and north of Blumund, Blumund between
Falmuth and Jura, Sarion on Jura's southern border, Eurazania south and Milim south-east, Damargania far west, the
Empire far east, the Ice Continent north, El Dorado south-west. Our readings where the map is looser: Ulgracia lies
north-west of Sarion, not south of it; Fulbrosia is on the south-western hills, not on a range at Jura's border;
Jura's forest is mostly open plain with forested mesas, and the dark forest only exists in the rings (below).

## Regions

Grid letter, name, `banner_subtitle`, then lore, terrain on Lerfing's map and landmarks (world x, z from
`anchors.toml`). "Stored biomes" is the share of the region's chunks per biome as imported.

### J: Jura-Tempest Federation (ジュラ・テンペスト連邦国)

- **Lore.** The Great Jura Forest, Veldora's old hunting ground. After Veldora was sealed it filled with goblins,
  direwolves, ogres, lizardmen, dryads and orcs. Rimuru united them into the Jura-Tempest Federation, a monster
  nation that trades with Dwargon and Blumund.
- **Terrain.** Lerfing's Jura is open rolling grass with forested mesas ("spires", gray terracotta tops at y 130–200) and
  lakes, x −100..2350, z −400..2200: between the Blumund channel (x ≈ −200) in the west, the Canaat apron foot
  (z ≈ −250..−400) in the north and Lake Siss's marsh (x ≈ 2350) in the east. The land is low in the south
  (y 63–80) and rises to the massif on the east side (x 2000..2300, z 500..1000, y 250+). The forest of the lore is the
  magicule rings below, not Lerfing's tree cover. Stored biomes: plains 73 %, dark forest 15 %, beach 5 %, forest 4 %, ancient forest 2 %.
- **The rings** (owner decision Q4, 19/11/2026; `design/data/lerfing/repaint.json`, applied offline by the import tool;
  verified with `python -I tools/lerfing/jura_check.py`): rings by radius from Tempest. **Core** r 200 ± 50:
  `tensura:ancient_forest` (about 20,000 area magicule, deadly for a fresh soul). **Band** r 200..600 ± 50:
  `minecraft:dark_forest` (2,000). **Rim**: everything else keeps Lerfing's own biome (plains, forest; 500, safe).
  Water, rivers and **beach are never repainted**, so Lerfing's lake shores stay sand inside the core
  ([the check's figures](#the-jura-check-19112026)). The Life 2 arrival is on the rim.
- **Landmarks:**
  - Tempest, the capital: (1720, 900).
  - Sealed Cave (Veldora, Rimuru's birthplace; later a hipokute farm and dungeon): (1380, 560), 480 blocks north-west of Tempest,
    on a mesa of the spire field in the dark band ("a rocky hill in a clearing, the mouth in its south face"); Veldora's leak is the band.
  - Old goblin village (Rigurd's tribe): (1390, 710), 380 blocks north-west, between the lake and the cave.
  - Spirit Gate: (1570, 1130), 275 blocks south-south-west.
  - Treyni's grove, the dryad sanctuary, and her shrine: (1920, 1540) / (1958, 1540), 670 blocks south-east, on the plain east of the river that drains Jura's lakes.
  - Hidden ogre village (the Kijin homeland, burned by the orcs): (2150, 400), at the north foot of the east massif ("north-eastern hills", *placement unverified*).
  - Life 2 arrival: (1660, −100), 1,000 blocks north of Tempest on the way to Dwargon, on pure plains.
  - Source of the Great Ameld River: (2500, −200), in D.
- Sources: https://tensura.fandom.com/wiki/Great_Jura_Forest, https://tensura.fandom.com/wiki/Lake_Siss,
  https://tensura.fandom.com/wiki/Great_Ameld_River, https://tensura.fandom.com/wiki/Orc_War,
  https://tensura.fandom.com/wiki/Sealed_Cave, https://tensura.fandom.com/wiki/Jura-Tempest_Federation

### W: Lizardmen's Marsh of Lake Siss (シス湖 — 蜥蜴人族の湿地帯), Lerfing's swamp

- **Lore.** A large expanse of marsh and limestone formations on the shores of Lake Siss. Its caverns form a natural
  labyrinth that is the lizardmen's fortress and seat of government. The lizardmen live off the lake's fish.
- **Terrain.** Lerfing's round lake (floor y 34–50, `swamp` biome all over it) with the swamp ring x 2350..3950, z 290..1230. Stored biomes:
  plains 61 %, swamp 36 %. **Lerfing's stilt-hut village** stands on the lake's west shore (x 2900..3600, z 400..1000, kept as he built it).
- **Landmarks:** Lake Siss (3050, 750; the Charybdis arena is the lake itself, r 96); the lizardmen's stilt village (3184, 988) on the south shore;
  the lizardmen's caverns (3300, 1200) on the south shore; the Orc War battlefield (3600, 1250) at the south-east,
  where the marsh meets Eurazania's jungle: Geld's horde came up from the south.
- Lake Siss is the lizardmen's lake, far off from Tempest (1,340 blocks): reaching it needed an envoy (Gabiru) and an army march.

### D: Armed Nation of Dwargon (武装国家ドワルゴン)

- **Lore.** The dwarf kingdom of Gazel Dwargo, founded about a thousand years ago by Hero King Guran Dwargo in a
  natural hollow at the foot of the Great Canaat Mountains. It is an underground cavern city behind fortified
  gates, a trade hub that stays neutral. The Great Canaat Mountains are the largest range on the continent: some
  peaks rise higher than Everest, dragons grow stronger with altitude, and the Dragon's Nest sits on the highest
  peak. The range makes invasion over the mountains impractical.
- **Terrain.** Lerfing's Canaat is a 2,900 × 2,100-block grey dome (gravel, clay, tuff, cobblestone, stone; stored biome
  stony peaks, 76 % of the region) from y ~90 at z −250 to the summit y 316 at (2502, −1432), with a lava lake at its top.
  Its south face is a long apron, not a cliff. Dwargon itself is **inside the mountain** (owner, 19/11/2026): the city body
  is carved into the apron with the mountain closing over it. See [dwargon.md](dwargon.md).
- **Landmarks:** the gate (1900, −500), base y ≈ 146, facing south down the road to Tempest (1,400 blocks, straight south);
  Dwargo, the capital (1900, −600); Gazel's throne room (1900, −606); Kaijin's smithy (1888, −584); the dwarf village
  (2000, −110) on the apron foot, 150 blocks east of the road; the Dwarven Arena (2200, −80); the Dragon's Nest on the
  summit shoulder (2420, −1536, y 273), 100 blocks north of the lava lake.
- **Distances.** The trip from the goblin village to Dwargon takes about two months on foot and three days on
  Tempest wolves.
- Sources: https://tensura.fandom.com/wiki/Armed_Nation_of_Dwargon,
  https://tensura.fandom.com/wiki/Great_Canaat_Mountains, https://tensura.fandom.com/wiki/In_the_Kingdom_of_the_Dwarves,
  https://tensura.fandom.com/wiki/Head_for_the_Dwarf_Kingdom

### E: Eastern Empire (東の帝国 — 東方連合統一帝国)

- **Lore.** The great military empire of the far east under Emperor Rudra. Its capital, Nasca, stands beside the
  Great Holy Mountain, home of its guardian dragon Velgrynd.
- **Terrain.** The north-eastern landmass, x 3700..7700, z −3400..−1000: lowland plains with a red crater volcano in the
  south-west (stored biome badlands after the repaint of Lerfing's nether wastes; crater lake and lava untouched). Stored biomes: plains 79 %, badlands 14 %.
- **Landmarks:** Nasca (5100, −2680), in the valley north of the volcano; the Great Holy Mountain, Velgrynd's sanctuary (5120, −1860), on the north-west flank of the crater (y ~110).
- Sources: https://tensura.fandom.com/wiki/Magic_Continent, https://tensura.fandom.com/wiki/Central_World

### P: Puppet Nation of Jistav (傀儡国ジスターヴ)

- **Lore.** Clayman's former domain, now ruled jointly by Rimuru and Milim and governed by the dark-elf elder Eva.
  Its capital, Amrita, was founded 2,000 years ago as a haven for dark elves. The country's position limits its
  large-scale trade to Dwargon and the Eastern Empire.
- **Terrain.** Jistav's plain, x 5500..7700, z −1000..−300, the north-eastern corner of Milim's badland, touching the Empire's volcano country. Plains with
  badlands; Clayman's Castle gets a dark-forest spot (r 180, repaint rule) to match its gloom.
- **Landmarks:** Clayman's Castle (5620, −900) on the flat east of the volcano (the Walpurgis gate inside); Amrita (6100, −650), 540 blocks east of it.
- Sources: https://tensura.fandom.com/wiki/Puppet_Nation_of_Jistav, https://tensura.fandom.com/wiki/Amrita,
  https://tensura.fandom.com/wiki/Clayman

### M: Milim's Domain (ミリム領 — 忘れられた竜の都)

- **Lore.** The south-eastern lands of Milim Nava, on the southern edge of the continent. Her capital is the City
  of the Forgotten Dragon ("Dragon's Village" on the wiki's nation table, fewer than 100,000 dragonewts), run by the
  Dragon Faithful: there is no government, the head priest Middray and the priest Hermes gather what the people
  produce at the Central Temple and hand it out evenly, and the temple is also Milim's own castle. A flock of
  wyverns lives in the city. The wiki places the domain **south of the Jura Forest and east of the Beast Kingdom
  of Eurazania**; its plains are fed by the Great Ameld River, which runs from the Canaat foothills to the southern
  ocean. The domain is primitive and poor until Tempest develops it (light novel vol. 7–8). After Walpurgis the
  Puppet Nation of Jistav (north-east) is ruled jointly with Rimuru, so Milim's land touches Jura, Eurazania and
  Jistav.
- **Terrain.** The huge eastern badland, x 3950..7700, z −1000..2700 (minus Jistav): plains and red badlands with a crescent ridge and
  lakes. Stored biomes: plains 54 %, badlands 41 %. The wiki calls the land fertile river plains; Lerfing's red badlands are his reading, kept.
- **Landmarks:** the City of the Forgotten Dragon (4680, 840), on the lake-and-river plain (relief 2); the mouth of the Great Ameld (4580, 2300), Lerfing's river to the eastern sea.
- Sources: https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon, https://tensura.fandom.com/wiki/Dragon_Faithful,
  https://tensura.fandom.com/wiki/Great_Ameld_River, https://tensura.fandom.com/wiki/Wyvern,
  https://tensura.fandom.com/wiki/Magic_Continent (all via search extracts, 18/11/2026; the lore pass is in
  [lore-pass-2026-11.md](lore-pass-2026-11.md))

### B: Beast Kingdom of Eurazania (獣王国ユーラザニア)

- **Lore.** Carrion's kingdom of beastmen, south of Jura and east of Fulbrosia. It is an agricultural state with
  fertile soil and a **tropical climate**, famous for its fruit. Milim destroyed its old capital, and Tempest helped
  build the new one, Laura.
- **Terrain.** The south-eastern jungle peninsula, x 2200..4700, z 1250..5100 (jungle 40 %, plains 51 %).
- **Landmark.** Laura (3300, 2600), in the heart of the peninsula.
- Sources: https://tensura.fandom.com/wiki/Beast_Kingdom_of_Eurazania, https://tensura.fandom.com/wiki/Carrion

### H: Harpy Queendom of Fulbrosia (天翼国フルブロジア)

- **Lore.** Frey's sky kingdom of harpies, south of Jura and west of Eurazania. The country sits on top of a
  mountain range on Jura's border, and its capital is Jia.
- **Terrain.** Our reading (Q3): the **south-western crystal hills**, x −3700..−1600, z 950..2200 (plains 58 %, desert 24 %, windswept gravelly hills 5 %; the hills are
  the only mesa country in the south-west). [Official map, Fulbrosia](https://www.ten-sura.com/map/#A-140)
- **Landmark.** Jia (−2700, 1500), on a mesa of the hills.
- Sources: https://tensura.fandom.com/wiki/Harpy_Queendom_of_Fulbrosia, https://tensura.fandom.com/wiki/Frey

### S: Sorcerous Dynasty of Sarion (魔導王朝サリオン)

- **Lore.** Emperor Elmesia's elven empire of 13 vassal kingdoms on Jura's southern border. Its capital, Elmine,
  is built into and on the **Divine Tree**, a colossal tree as tall as the highest mountains and one of two
  surviving holy relics made by Veldanava.
- **Terrain.** Our reading (Q3): the south-central peninsula, x 0..1300, z 2150..3650, with **Paulzero's giant trees** (his 13 "built by Paulzero" signs,
  around (610, 2930)): the one literal Divine Tree on the map. Plains 96 %.
- **Landmark.** Elmine (1100, 2760), on the terrace beside the giant tree; the trees themselves are kept as Paulzero built them (x 350..1050, z 2600..3150).
- Sources: https://tensura.fandom.com/wiki/Sorcerous_Dynasty_of_Sarion, https://tensura.fandom.com/wiki/Divine_Tree,
  https://tensura.fandom.com/wiki/Elmesia_El_Ru_Sarion

### U: Republic of Ulgracia (ウルグレイシア共和国)

- **Lore.** A republic south of Sarion and near Jura that lives from trade with Sarion and from farming. Its
  citizens are elemental magic users, and citizenship requires a spirit-contract ceremony. Its capital is Galut.
- **Terrain.** The woodland south of Blumund, x −1600..−100, z 600..2150 (plains 76 %, forest 17 %); Lerfing's own spawn (−456, 976) is here. Our reading: north-west of Sarion rather than south of it.
- **Landmark.** Galut / Ulgr Nature Park (−1040, 1060). The fan map's dot is "Ulgr Nature Park", so Galut's exact site is *unverified*; Filtwood (−900, 700) is a pin.
- Source: https://tensura.fandom.com/wiki/Republic_of_Ulgracia

### R: Kingdom of Blumund (ブルムンド王国)

- **Lore.** A small kingdom on the Jura border, next to Falmuth (later Farmenas) and the Federation. It is home to
  Fuze's Free Guild branch and the adventurers Kabal, Eren and Gido, and it is Tempest's first human partner.
- **Terrain.** x −1500..−100, z −300..600: farmland and plains that meet Jura across the Blumund channel (x ≈ −200).
- **Landmark.** Blumund's capital (Londo on the fan map): (−450, 150), right at Jura's western door. The canon capital name is *unverified*. The road camp (−250, 250) stands at Jura's edge.
- Source: https://tensura.fandom.com/wiki/Kingdom_of_Blumund

### F: Kingdom of Falmuth (ファルムス王国)

- **Lore.** A rich trade kingdom west of Dwargon with its capital at Marris. King Edmaris started the Tempest Holy
  War, and after Rimuru destroyed his army the kingdom became Farmenas under Yohm. The Migam frontier province
  borders the forest, and Count Muller's march lies on the Blumund border.
- **Terrain.** The north arm of the western landmass, x −2600..−1300, z −2000..−650, plus the north islet (x −1100..−500, z −1800..−1300, with Lerfing's small builds on it): plains with beach (88 % / 11 %), by the sea, north-west of Jura and west of the Canaat.
- **Landmarks:** Marris (−2000, −1450); Siltrosso (−2450, −1650), at the arm's western tip.
- Sources: https://tensura.fandom.com/wiki/Kingdom_of_Falmuth, https://tensura.fandom.com/wiki/Kingdom_of_Farmenas,
  https://tensura.fandom.com/wiki/Tempest_Holy_War

### G: Kingdom of Englassia (イングラシア王国)

- **Lore.** The leading power of the Western Nations. Its royal capital holds the Free Guild headquarters (Yuuki)
  and the Freedom Academy, where Rimuru taught Shizu's students. A school outing runs south from the capital to
  the town of Guratol.
- **Terrain.** The big western plain, x −2600..−1500, z −650..500, flat (y 66).
- **Landmarks:** the royal capital (Lura on the fan map), with the Freedom Academy and the Free Guild HQ (−2150, −410); Ballachia (−1660, −460), on the eastbound road between Lura and Londo; the Englassia road post (−1880, −500); Ghastone (−2000, 300), a pin.
- Sources: https://tensura.fandom.com/wiki/Kingdom_of_Englassia,
  https://tensura.fandom.com/wiki/Extra:_Rimuru's_Glamorous_Life_as_a_Teacher,_Part_2

### L: Holy Empire of Lubelius (神聖法皇国ルベリオス)

- **Lore.** The theocratic seat of the Western Holy Church and secretly the domain of the vampire Demon Lord
  Luminous Valentine. The **Sacred Mountain**, its holiest site, carries the Inner Sanctum at its summit. Under the
  human holy city lies the Night Garden, the underground capital for its non-human subjects. Hinata's Holy Knights
  are based here.
- **Terrain.** The north-western ridge and coast, x −3300..−2600, z −1700..300: Lerfing's one real mountain in the west, a ridge peaking at y 187 at (−2976, −992). Plains 73 %, forest 19 %.
- **Landmarks:** the Holy City (Lune on the fan map) at the east foot of the ridge (−2550, −700); the Sacred Mountain with the Inner Sanctum (−2980, −900), on the ridge (y 120–187).
- Sources: https://tensura.fandom.com/wiki/Holy_Empire_of_Lubelius, https://tensura.fandom.com/wiki/WN:Holy_City_Lubelius,
  https://tensura.fandom.com/wiki/Luminous_Twilight_Valentine

### V: Holy Void of Damargania (聖虚ダマルガニア)

- **Lore.** Dagruel's country of giants in the Barren Lands of the far west. Most of it is the **Desert of Death**:
  once bountiful land, made uninhabitable and still magicule-contaminated by the ancient seven-day battle between
  Guy and Milim. Its capital is the Heaven Tower.
- **Terrain.** The desert x −5000..−2900, z −1500..1000, and the grey-teal Barren Lands west of it to x −7400 (stored biome `tensura:barren_land`, repainted from Lerfing's end biomes). Desert 43 %, barren land 30 %, plains 25 %.
- **Landmarks:** Coleus (−3080, 600), on the desert's eastern edge; the Heaven Tower (−4500, 560), deep in the desert (relief 1).
- Sources: https://tensura.fandom.com/wiki/Holy_Void_of_Damargania, https://tensura.fandom.com/wiki/Dagruel,
  https://tensura.fandom.com/wiki/Heaven_Tower

### I: Ice Continent (氷の大陸 — 白氷宮)

- **Lore.** Guy Crimson's frozen northern continent, with his Frost Palace (White Ice Palace). The illustrated map
  calls it the "Tundral Waste" and shows a great rift and ice-floe islands.
- **Terrain.** The island far to the north, x −3850..2200, z −5540..−2800 (snowy plains 87 %), with a river running to its south shore. **Lerfing's ice crystals** stand on the water at (−1900, −4480) (kept).
- **Landmark.** Frost Palace (−1980, −4300), on the shore beside them.
- Sources: https://tensura.fandom.com/wiki/Ice_Continent, https://tensura.fandom.com/wiki/Frost_Palace,
  https://tensura.fandom.com/wiki/Guy_Crimson

### X: El Dorado (黄金郷エルドラド)

- **Lore.** The south-western continent, ruled alone by Demon Lord Leon Cromwell from the Golden City. A volcano
  at its centre supplies the precious metals that fund the country.
- **Terrain.** The south island, x −4600..−1900, z 3400..5700 (plains 84 %, badlands 7 %) with a volcano (peak y 221 at (−2858, 4672)) and lakes.
- **Landmarks.** Golden City (−3300, 4300), on the green plain north-west of the volcano; the volcano (−2850, 4600).
- Sources: https://tensura.fandom.com/wiki/Golden_City_of_El_Dorado, https://tensura.fandom.com/wiki/WN:El_Dorado

### O, N, Y, Q, A: small Western Nations (Morgdahl, Nostraille, Yuzalgh, Yggdonia, Raja)

The anime map seen at the Western Council supports the west-to-east sequence Morgdahl, Nostraille, Yuzalgh and Yggdonia. The fan cartographer identifies Raja's exact position as speculative. The English epithets are pack choices. [Council map comparison](https://www.reddit.com/r/TenseiSlime/comments/1suz7yb/new_countries/) · [Cartographer's account](https://www.reddit.com/r/TenseiSlime/comments/1um7i81/i_created_a_bunch_of_tensura_political_maps/)

They share the river-and-lake belt (z 500..1000) between Englassia and the Fulbrosia hills, from west to east:

| Grid | Name | Belt | Landmark |
| --- | --- | --- | --- |
| O | Morgdahl, the river-mouth landing | x −2600..−2250 | (−2440, 740); Sainte Malukshure (−2500, 1300), pin |
| A | Raja, on the belt's lake | x −2250..−1950 | (−2050, 760); Rostia (−2100, 1000), pin |
| N | Nostraille, quiet hill kingdom | x −1950..−1650 | (−1780, 550) |
| Y | Yuzalgh | x −1650..−1500 | (−1580, 650), pin |
| Q | Yggdonia, birch realm | north of the belt, x −1500..−1300, z 0..500 | (−1400, 300), pin |

## Tempest (early): for the build team

This is the moment right after the ogres joined and were named Benimaru, Shuna, Shion, Souei, Hakurou and Kurobe.
The build depicts the village before the Orc Lord war, after the ogres arrive in episodes 9–11. Volume 2 covers the ogres and the Orc Lord conflict. The blueprint follows the anime for visual details. [Fuse, light novel volume 2](https://yenpress.com/titles/9781975301118-that-time-i-got-reincarnated-as-a-slime-vol-2-light-novel)

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

**Surroundings.** The settlement sits in a cleared hollow in a temperate forest (oak and dark oak; Jura is
never jungle) with tree stumps on the cleared margins. A river or stream runs by the town for water and washing.
The anime shows a riverbank by the village; the LN states that water access drove the move, *exact layout
unverified*. On Lerfing's map the spot is a sandy flat at (1720, 900) beside a lake (x 1500..1600, z 780..1000) with a
pond of its own just to the south (x 1657..1739, z 905..943): running water nearby. Lake Siss is not next to the town: it is
the lizardmen's lake, 1,340 blocks east, which needed an envoy (Gabiru) and an army march to reach.

**Why here.** The scan of every 200 × 200 window inside x 600..1800, z 500..1500 (land, relief, water share, trees)
gave this spot as the winner (relief 5–7, water 11 %, plains): open ground to grow into, the east massif as a
backdrop, the mesa field for the Sealed Cave to the north-west. The runner-up is (1620, 1460).
[tempest.md](tempest.md#placement) has the footprint measurements.

**Distances from the Tempest arrival point (1720, 900).** Straight lines before the terrain survey. Canon travel times describe journeys on the fictional continent.

| Destination | World x, z | Distance in blocks |
| --- | --- | ---: |
| Spirit Gate | (1570, 1130) | 275 |
| Old goblin village | (1390, 710) | 381 |
| Shizu's meeting place | (1300, 820) | 428 |
| Sealed Cave | (1380, 560) | 481 |
| Hidden ogre village | (2150, 400) | 659 |
| Treyni's grove | (1920, 1540) | 671 |
| Life 2 arrival | (1660, −100) | 1,002 |
| Lake Siss | (3050, 750) | 1,338 |
| Dwargon gate | (1900, −500) | 1,412 |
| Blumund capital | (−450, 150) | 2,296 |
| Laura | (3300, 2600) | 2,321 |
| City of the Forgotten Dragon | (4680, 840) | 2,961 |

## The Jura check (19/11/2026)

`python -I tools/lerfing/jura_check.py --world <import out>` reads the stored biomes of the imported world (read only) and
checks the rings, the arrival and Tempest's ground. The figures (lattice of 8 blocks on the 4 × 4 biome-cell centres,
radius 800 round (1720, 900), 40,000 samples), also drawn in [docs/previews/jura_check.png](../../docs/previews/jura_check.png):

| Check | Result |
| --- | --- |
| Core r < 150: every land sample is ancient forest | 841 of 841 (the rest is beach, river or water) |
| Core r < 200 (nominal; the rule jitters edges by ±50) | ancient forest 71 %, beach 15 %, dark forest 7 % (the ±50 wobble), river and lake 7 % |
| Band r 250..550: every land sample is dark forest | 11,041 of 11,041 |
| Rim beyond r 650: no ancient or dark forest | 0 of 9,033 |
| Every sample equals what `repaint.json` says | 40,000 of 40,000 |
| Arrival (1660, −100): dry, rim, non-deadly | biome plains in all of the 40-block area (0 % stony peaks; WP-L4 moved it off the design's (1780, −150), 42 % stony peaks), 0 % water; `tools/lerfing/jura_check.py` 11 checks, 0 failed |
| Beach in the core | 16 % of the dry land (37 % inside r 100, 8–10 % beyond r 100); assessment in the [decisions](../decisions.md) row of 19/11/2026 |

Our interpretation of the beach in the core: Lerfing's lake shores are the one place where Veldora's magicule thins
(sand holds none of the forest); souls who know the shore can reach the green from the band without crossing the
ancient forest. Nothing canon says so; it is how his map reads.

## Scale

Canon scale cannot be reproduced. Two months on foot from the goblin village to Dwargon is hundreds of kilometres
(around 600 km at a forest pace of 10 km a day), which would make the continent several thousand kilometres wide
and millions of blocks in Minecraft. Every playable scale is a compression, so the question is gameplay density.

The owner chose to take Lerfing's scale as drawn: land 15,040 × 11,372 blocks; the grid of `canon_map.txt` is 1,016 × 784
chunks. Jura is 23,954 chunks (about 2,400 × 2,600 blocks), the Canaat and Dwargon 21,895, Milim's Domain 32,769, the
Ice Continent 31,689. The old traced grid (14,016 × 10,128 blocks, Tempest at 0, 0) and its 10,000- and 14,000-block
coordinates are gone; git history keeps those notes.
