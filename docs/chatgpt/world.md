# World guide: canon geography of the Tensura world

> **Read this first.** Every coordinate in this file comes from **Lerfing's imported map** (*Tensura by Lerfing*, the
> current Life 2 world). That map **is being replaced** by a new, fully own world (owner decision of 19/11/2026), so the
> coordinates will change. **What matters is the geography relations**: what lies north, south, east and west of
> Tempest, which nations border each other, which river runs from where to where, what stands in a forest, on a
> mountain, inside a mountain, by a lake. The numbers are kept only so you can see the scale and so places can be
> found on the BlueMap screenshots. When the new map is drawn, Claude re-derives the coordinates from it.

**See the current world as a picture:** [source-map/](source-map/README.md) (overview renders, height maps and crops of the old map, with scale and origin), the nations atlas [`docs/previews/lerfing_regions.png`](../previews/lerfing_regions.png) and the Jura rings [`docs/previews/jura_check.png`](../previews/jura_check.png).

Sources in the repo: [`design/data/anchors.toml`](../../design/data/anchors.toml) (every canon place),
[`pack/config/ttl/canon_regions.json`](../../pack/config/ttl/canon_regions.json) (regions, colours, banners, landmarks),
[`design/lore/world.md`](../../design/lore/world.md) (the full canon research with source links),
[`design/decisions.md`](../../design/decisions.md) (the owner decisions). Back to the [knowledge pack](README.md).

## 1. Axes and scale

- **x grows east, z grows south. North is smaller z.** (A Minecraft rule; every table here uses X, Z in blocks.)
- Sea level is y 65 (water tops out at y 64). The highest point of the current map is the Canaat summit, y 316 at (2502, −1432); the build height limit is y 320.
- The current land is about 15,040 x 11,372 blocks (x −7400..7640, z −5540..5832), Lerfing's drawn continent plus two islands. Jura, the middle region, is about 2,400 x 2,600 blocks.
- Canon scale cannot be reproduced (two months on foot from the goblin village to Dwargon is hundreds of kilometres). Every playable scale is a compression; the question is gameplay density. The owner took Lerfing's scale as drawn. **The new map may choose its own scale**, but keep the ratios between places below (Tempest to Dwargon is the longest everyday walk, about 1,450 blocks, a long evening).
- **Beyond the continent**: an ocean (deep sea, about 2,000 blocks wide) and then the ordinary vanilla overworld. Nothing canon lives there; vanilla and mod structures are allowed there.

## 2. The world as a picture (relative geography)

Read it from **Tempest**, in the middle of Jura (the Great Jura Forest). Distances are straight lines on the current map.

| Direction | What lies there | Distance from Tempest |
|---|---|---|
| Centre | **Jura** (Jura-Tempest Federation): forest, plains with forested mesas, small lakes. The Sealed Cave (north-west), the old goblin village, the Spirit Gate (south-south-west), Treyni's grove (south-east), the hidden ogre village (north-east foot of the east massif). | 0 to about 600 |
| North | The **Canaat Mountains** and **Dwargon**: a grey massif, the largest range of the continent, climbing to the world's highest point; a lava lake near the top; the **Dragon's Nest** on the highest shoulder. Dwargon's gate is on the south flank; the city lies **inside the mountain**. The **Great Ameld River** rises at the mountain's foot. The Life 2 arrival is between the two, on Jura's rim. | Dwargon gate 1,450; arrival 1,000; Dragon's Nest about 2,540 |
| East | **Lake Siss** and the lizardmen's marsh (the Orc War battlefield at its south-east), then **Milim's Domain**, a huge red-and-green badland. | Lake Siss 1,340; Forgotten Dragon city 2,960 |
| North-east | **Jistav** (Clayman's Castle, Amrita) is the north-eastern corner of Milim's badland; the **Eastern Empire** (Nasca, the red volcano of the Great Holy Mountain) is the landmass beyond it, north of Jistav. | Clayman's Castle about 4,300, Amrita 4,650; Nasca about 4,900 |
| South-east | **Eurazania**, a jungle peninsula running far to the south, below Lake Siss. | Laura 2,320 |
| South | **Sarion**, a peninsula south of Jura's west half with the colossal **Divine Tree** (Elmine). | Elmine 1,960 |
| West | **Blumund**, across a channel at the edge of Jura (about 200 blocks wide), then **Ulgracia** (south-west), **Falmuth** (north-west, a north arm with a small islet), **Englassia** (a big plain) with the Free Guild HQ, the **small western nations** in a river-and-lake belt, and **Lubelius** on the north-western ridge. | Blumund 2,300; Englassia 4,090; Lubelius 4,560 |
| Far west | **Damargania**: the Desert of Death and the Barren Lands, with Heaven Tower. **Fulbrosia** (the harpies' crystal hills) in the south-west. | Heaven Tower 6,200 |
| Islands | The **Ice Continent** (Frost Palace) far to the north; **El Dorado** to the south-west. | Frost Palace 6,380; El Dorado 6,060 |

Canon relations the layout must keep (checked against the series, from `world.md`): Dwargon north of Jura; Falmuth west of
Dwargon and north of Blumund; Blumund between Falmuth and Jura; Sarion on Jura's southern border; Eurazania south of Jura and
Milim south-east of it; Damargania far west; the Empire far east; the Ice Continent north; El Dorado south-west. Where the current
map is looser we say so: Ulgracia lies north-west of Sarion rather than south; Fulbrosia sits on the south-western hills rather than on a
range at Jura's border; the Divine Tree is one literal giant tree (Paulzero's) on the current map.

### Which nations border which

From the current grid (`pack/config/ttl/canon_map.txt`, counted by shared chunk edges: more means a longer border). The *relations*
are what to keep; the lengths only tell you which borders are long.

| Nation | Borders |
|---|---|
| Jura (J) | Blumund (R, west, across a channel), Sarion (S, south), Ulgracia (U, south-west), Dwargon (D, north, the longest border), Lake Siss marsh (W, east), Eurazania (B, small, south-east) |
| Dwargon (D) | Jura, Lake Siss marsh, Milim, the Eastern Empire (a short stretch at its north-east) |
| Lake Siss marsh (W) | Jura, Dwargon, Milim, Eurazania |
| Milim (M) | Dwargon, Lake Siss marsh, Jistav (P, long), the Eastern Empire (E, long), Eurazania (short) |
| Jistav (P) | Milim, Eastern Empire |
| Eastern Empire (E) | Jistav, Milim, Dwargon (short) |
| Eurazania (B) | Jura, Lake Siss marsh, Milim, Sarion |
| Sarion (S) | Jura, Ulgracia, Eurazania |
| Blumund (R) | Jura, Ulgracia, Englassia, Yggdonia |
| Ulgracia (U) | Blumund, Jura, Sarion, Fulbrosia, Yuzalgh, Yggdonia |
| Falmuth (F) | Lubelius, Englassia |
| Englassia (G) | Falmuth, Lubelius, Blumund, Yggdonia, Raja, Nostraille, Morgdahl, Yuzalgh |
| Lubelius (L) | Damargania, Falmuth, Englassia |
| Damargania (V) | Lubelius, Fulbrosia, Morgdahl (and a point on Englassia) |
| Fulbrosia (H) | Damargania, Ulgracia, Raja, Nostraille, Morgdahl |
| Small western nations | Morgdahl, Raja, Nostraille, Yuzalgh in the belt between Englassia and the Fulbrosia hills, west to east; Yggdonia on Blumund's southern border |
| Ice Continent (I), El Dorado (X) | Islands; no land borders |

Note: canon puts Falmuth right next to Dwargon (to its west); on the current map they do not touch (about 850 blocks of sea lie between them). The new map may fix that.

### Travel distances from Tempest

Straight lines on the current map, before terrain. Canon travel times describe journeys on the fictional continent: the trip from the
goblin village to Dwargon takes about **two months on foot** or **three days on Tempest wolves**.

| Destination | Blocks | Note |
|---|---:|---|
| Spirit Gate | 275 | south-south-west |
| Old goblin village | 381 | north-west, between the lake and the cave |
| Hinata's ambush spot (Shizu's meeting place) | 428 | west of the lake |
| Sealed Cave | 481 | north-west, on a mesa |
| Hidden ogre village | 659 | north-east foot of the east massif |
| Treyni's grove | 671 | south-east, east of the river that drains Jura's lakes |
| Life 2 arrival | 1,002 | north, on Jura's rim |
| Lake Siss | 1,338 | east |
| Dwargon gate | 1,453 | north; the **Dwarven Road** (1,478 blocks) joins the two |
| Blumund capital | 2,296 | west, the first human neighbour |
| Laura (Eurazania) | 2,321 | south-east |
| City of the Forgotten Dragon | 2,961 | east |

## 3. Named features of the land

| Feature | Where and what |
|---|---|
| **Great Jura Forest** (the "Forest of Jura") | The whole of Jura. Canon: Veldora's hunting ground, now home of goblins, direwolves, ogres, lizardmen, dryads and orcs. In our game its magicule rises toward Tempest in rings (section 6): the heart is deadly to weak souls. Dense old forest; **Jura is never jungle**. |
| **Great Canaat Mountains** | North of Jura. Largest range; a grey massif; summit with a lava lake; the Dragon's Nest on the highest shoulder. Dwargon lies inside it. |
| **Dwargon in the mountain** | A cavern city carved into the massif behind one escarpment, gate on the south flank facing the apron and the road to Tempest, a skylight crack above the main street (section 6). |
| **Great Ameld River** | Rises at the Canaat's foothills (north-east of the Dwargon gate), feeds the Jura lakes (our reading) and Lake Siss, and runs on to the eastern sea between Milim's land and Eurazania. In canon it runs from the Canaat foot to the southern ocean through Milim's plains. |
| **Lake Siss** | East of Jura: the lizardmen's round lake with a swamp ring; Charybdis (the whirlpool boss) lives in it; stilt villages on its shores. |
| **Jura lakes** | A lake just west of Tempest (so the village has running water nearby) and a pond south of it; a river that drains Jura's lakes passes west of Treyni's grove. |
| **Sealed Cave** | A cave in a rocky hill (a mesa of the spire field) in the forest north-west of Tempest; the mouth in the south face. Veldora's seal. |
| **Rock spires / mesas of Jura** | Forested mesas with grey terracotta tops; the goblin village stands at the foot of one. |
| **Divine Tree** (Sarion) | A colossal tree as tall as the highest mountains. Elmine is built into it. |
| **Great Holy Mountain / Scorching God Mountain** | Velgrynd's volcano in the Eastern Empire, a red crater with a lake and lava; the sanctuary on its north-west flank. |
| **Sacred Mountain** (Lubelius) | The one real mountain of the west, a limestone ridge; the Inner Sanctum on its summit. |
| **El Dorado volcano** | A volcano at the centre of the southern island; its metals fund Leon's city. |
| **Desert of Death and the Barren Lands** | Damargania, far west: desert contaminated by Guy and Milim's seven-day battle, and a grey-teal wasteland west of it. |
| **Ice Continent / Tundral Waste** | The snowy island of Guy Crimson, with a great rift and ice floes. |
| **Blumund channel** | A ~200-block channel between Blumund and Jura (x about −200 on the current map). |
| **Raja's lake**, **Blumund's lake**, **the river-and-lake belt** | Small lakes and rivers between Englassia and the Fulbrosia hills carry the small western nations. |
| **Sacred / holy places in Jura's neighbourhood** | The Dwelling of the Spirits (Ramiris) is reached through the Spirit Gate in the forest; Treyni's grove and shrine lie deep in the old wood. |

## 4. Nations and regions

The grid letter is the key the game uses. The **colour** is the nation's colour in the pack's atlas
([`docs/previews/lerfing_regions.png`](../previews/lerfing_regions.png)), a good starting point for the political map. The **banner
subtitle** is the Japanese name shown on screen. The terrain line describes Lerfing's version; the new map is free to redraw it as long as the lore holds.
Extent = bounding box on the current map (x0..x1, z0..z1).


### J: Jura-Tempest Federation

- **Colour** `#E472D2` · **banner** ジュラ・テンペスト連邦国 · **extent** x −416..2416, z −720..2256
- **Lore.** The Great Jura Forest, Veldora's old hunting ground. After Veldora was sealed it filled with goblins, direwolves, ogres, lizardmen, dryads and orcs. Rimuru united them into the Jura-Tempest Federation, a monster nation that trades with Dwargon and Blumund.
- **Faction.** Faction `tempest` (capital Tempest). Hostile or friendly NPCs: goblins, hobgoblins, kijin, Tempest Wolves, dryads.
- **Terrain (current).** rolling plains with forested mesas (spires, grey terracotta tops) and small lakes, low in the south, rising to a massif on the east side; open grass with scattered woods on Lerfing's map, so the Great Jura Forest of the lore is planted on top of it (section 6).
- **Places.** [Tempest](places/tempest.md), [Life 2 arrival](places/arrival.md), [Wayfarers' camp on Jura's rim](places/wayfarers_camp.md), [Sealed Cave](places/sealed_cave.md), [Old goblin village](places/goblin_village.md), [Spirit Gate](places/spirit_gate.md), [Hinata's ambush west of Tempest](places/shizu_spawn.md), [The Outcast on Tempest's south road](places/outcast_road.md), [Treyni's grove](places/treyni_grove.md), [Treyni's shrine](places/treyni_shrine.md), [Hidden ogre village](places/ogre_village_ruin.md), [The old well on the Blumund road](places/old_well.md), [The abandoned rookie camp](places/rookie_camp.md)

### D: Armed Nation of Dwargon

- **Colour** `#D1CC3B` · **banner** 武装国家ドワルゴン · **extent** x 688..3952, z −2704..304
- **Lore.** The dwarf kingdom of Gazel Dwargo, founded about a thousand years ago by Hero King Guran Dwargo in a natural hollow at the foot of the Great Canaat Mountains: an underground cavern city behind fortified gates, a neutral trade hub. The Canaat is the largest range on the continent (some peaks higher than Everest; dragons grow stronger with altitude; the Dragon's Nest sits on the highest peak) and makes invasion over the mountains impractical.
- **Faction.** Faction `dwargon` (capital Dwargo, throne `gazel_dwargo`).
- **Terrain (current).** a grey dome (gravel, clay, tuff, cobble, stone) from the foothills to the highest summit with a lava lake at its top; the south face is a long apron broken by escarpments.
- **Places.** [Dwargon](places/dwargon.md), [Dwargo](places/dwargo.md), [Gazel's throne room](places/dwargon_throne.md), [Kaijin's smithy](places/kaijin_smithy.md), [Dwarf village on the road to Dwargon](places/dwarf_village.md), [Dwarven Arena](places/dwarven_arena.md), [Dragon's Nest](places/dragons_nest.md), [Great Ameld River source](places/ameld_source.md)

### W: Lizardmen's Marsh of Lake Siss

- **Colour** `#468C6E` · **banner** シス湖 — 蜥蜴人族の湿地帯 · **extent** x 2400..4304, z 304..1312
- **Lore.** A large expanse of marsh and limestone on the shores of Lake Siss. Its caverns form a labyrinth that is the lizardmen's fortress and seat of government; they live off the lake's fish.
- **Faction.** Faction `lizardmen` (capital: the lizardmen's caverns).
- **Terrain (current).** a round lake with a swamp ring (mangrove, swamp).
- **Places.** [Lake Siss](places/lake_siss.md), [Lizardmen's stilt village](places/lizardmen_village.md), [Lizardmen's caverns](places/lizardmen_caverns.md), [Orc War battlefield](places/orc_camp.md)

### M: Milim's Domain

- **Colour** `#E2CDA4` · **banner** ミリム領 — 忘れられた竜の都 · **extent** x 3888..7648, z −1056..2720
- **Lore.** The south-eastern lands of Milim Nava. Her capital, the City of the Forgotten Dragon, is run by the Dragon Faithful (no government: head priest Middray and priest Hermes collect what people produce at the Central Temple and hand it out evenly; the temple is Milim's castle). A flock of wyverns lives in the city. The wiki places the domain south of the Jura Forest and east of Eurazania; the Great Ameld feeds its plains. Poor and primitive until Tempest develops it.
- **Faction.** No faction in the pack yet.
- **Terrain (current).** a huge badland: plains and red badlands, a crescent ridge, lakes, river plains.
- **Places.** [Great Ameld River mouth](places/ameld_mouth.md), [City of the Forgotten Dragon](places/forgotten_dragon_city.md)

### P: Puppet Nation of Jistav

- **Colour** `#D7A546` · **banner** 傀儡国ジスターヴ · **extent** x 5296..7040, z −1104..−304
- **Lore.** Clayman's former domain, now ruled jointly by Rimuru and Milim and governed by the dark-elf elder Eva. Its capital Amrita was founded 2,000 years ago as a haven for dark elves. Large-scale trade only with Dwargon and the Eastern Empire.
- **Faction.** No faction in the pack yet (Clayman is a boss, `clayman`).
- **Terrain (current).** plains and badlands, Clayman's Castle in a dark forest spot.
- **Places.** [Clayman's Castle](places/clayman_castle.md), [Amrita](places/amrita.md)

### E: Eastern Empire

- **Colour** `#87D944` · **banner** 東の帝国 — 東方連合統一帝国 · **extent** x 3488..7104, z −3376..−1056
- **Lore.** The great military empire of the far east under Emperor Rudra. Its capital Nasca stands beside the Great Holy Mountain, home of its guardian dragon Velgrynd.
- **Faction.** No faction in the pack yet.
- **Terrain (current).** lowland plains with a red crater volcano in the south-west.
- **Places.** [Nasca](places/nasca.md), [Great Holy Mountain](places/great_holy_mountain.md)

### B: Beast Kingdom of Eurazania

- **Colour** `#87DC45` · **banner** 獣王国ユーラザニア · **extent** x 1504..4544, z 1312..5440
- **Lore.** Carrion's kingdom of beastmen, south of Jura and east of Fulbrosia: agricultural, fertile, tropical, famous for fruit. Milim destroyed its old capital; Tempest helped build the new one, Laura.
- **Faction.** Faction `eurazania` (capital Laura, throne `carrion`).
- **Terrain (current).** a jungle peninsula reaching far to the south (jungle, savanna, plains).
- **Places.** [Laura](places/laura.md)

### S: Sorcerous Dynasty of Sarion

- **Colour** `#CBC937` · **banner** 魔導王朝サリオン · **extent** x −800..1504, z 2256..3632
- **Lore.** Emperor Elmesia's elven empire of 13 vassal kingdoms on Jura's southern border. Its capital Elmine is built into and on the Divine Tree, a colossal tree as tall as the highest mountains and one of two surviving holy relics made by Veldanava.
- **Faction.** No faction in the pack yet.
- **Terrain (current).** south-central peninsula of plains with a grove of giant trees.
- **Places.** [Elmine](places/elmine.md)

### R: Kingdom of Blumund

- **Colour** `#E2AA45` · **banner** ブルムンド王国 · **extent** x −1456..−144, z −512..992
- **Lore.** A small kingdom on the Jura border, next to Falmuth (later Farmenas) and the Federation; home of Fuze's Free Guild branch and the adventurers Kabal, Eren and Gido; Tempest's first human partner.
- **Faction.** Faction `blumund` (capital Londo).
- **Terrain (current).** farmland and plains that meet Jura across a channel.
- **Places.** [Blumund](places/blumund.md), [Blumund road camp at Jura's edge](places/blumund_road.md)

### U: Republic of Ulgracia

- **Colour** `#D4AD53` · **banner** ウルグレイシア共和国 · **extent** x −1552..−320, z 592..2320
- **Lore.** A republic south of Sarion and near Jura that lives from trade with Sarion and from farming. Citizens are elemental magic users; citizenship needs a spirit-contract ceremony. Capital Galut; Ulgr Nature Park holds the entrance to Ramiris's Dwelling of the Spirits in the series.
- **Faction.** No faction in the pack yet.
- **Terrain (current).** woodland and plains south of Blumund.
- **Places.** [Filtwood](places/filtwood.md), [Galut / Ulgr Nature Park](places/ulgr_nature_park.md)

### F: Kingdom of Falmuth

- **Colour** `#81D742` · **banner** ファルムス王国 · **extent** x −2704..160, z −2016..−752
- **Lore.** A rich trade kingdom west of Dwargon with its capital at Marris. King Edmaris started the Tempest Holy War; after Rimuru destroyed his army it became Farmenas under Yohm. The Migam frontier province borders the forest; Count Muller's march lies on the Blumund border.
- **Faction.** Faction `falmuth` (capital Marris).
- **Terrain (current).** plains and beach along a north arm of the western landmass, plus a small islet.
- **Places.** [Marris](places/marris.md), [Siltrosso](places/siltrosso.md)

### G: Kingdom of Englassia

- **Colour** `#D1A747` · **banner** イングラシア王国 · **extent** x −2528..−1456, z −752..496
- **Lore.** The leading power of the Western Nations. The royal capital holds the Free Guild headquarters (Yuuki) and the Freedom Academy where Rimuru taught Shizu's students; a school outing runs south to the town of Guratol.
- **Faction.** No own faction; the Free Guild is not a faction in the pack.
- **Terrain (current).** the big flat western plain.
- **Places.** [Ballachia](places/ballachia.md), [Englassia](places/englassia.md), [Ghastone](places/ghastone.md), [Englassia road post](places/englassia_road.md)

### L: Holy Empire of Lubelius

- **Colour** `#E59A6B` · **banner** 神聖法皇国ルベリオス · **extent** x −3616..−2448, z −1712..384
- **Lore.** The theocratic seat of the Western Holy Church and secretly the domain of the vampire Demon Lord Luminous Valentine. The Sacred Mountain carries the Inner Sanctum at its summit; under the human holy city lies the Night Garden for non-human subjects. Hinata's Holy Knights are based here.
- **Faction.** Faction `holy_church` (capital Lubelius, throne `luminous_valentine`).
- **Terrain (current).** a north-western ridge and coast, the one real mountain of the west.
- **Places.** [Holy City Lubelius](places/lubelius.md), [Sacred Mountain](places/sacred_mountain.md)

### V: Holy Void of Damargania

- **Colour** `#E0CCA5` · **banner** 聖虚ダマルガニア · **extent** x −7408..−2528, z −1600..2384
- **Lore.** Dagruel's country of giants in the Barren Lands of the far west. Most of it is the Desert of Death, once bountiful land made uninhabitable (and still magicule-contaminated) by the ancient seven-day battle between Guy and Milim. Its capital is the Heaven Tower.
- **Faction.** No nation faction in the pack (the `orc_horde` faction lists region V in the data, but is not a territory).
- **Terrain (current).** desert and the grey-teal Barren Lands in the far west.
- **Places.** [Coleus](places/coleus.md), [Heaven Tower](places/heaven_tower.md)

### O: Morgdahl

- **Colour** `#9646AF` · **banner** A river-mouth realm on the southern coast of the Western Nations · **extent** x −2608..−2256, z 416..1056
- **Lore.** A river-mouth realm on the southern coast of the Western Nations (pack epithet). Seen on the Western Council map in anime season 4.
- **Faction.** No faction.
- **Terrain (current).** river-mouth landing in the river-and-lake belt.
- **Places.** [Morgdahl](places/morgdahl.md)

### A: Raja

- **Colour** `#87DA44` · **banner** A small Western state of hills and old mines on the Jura border · **extent** x −2256..−1952, z 496..1056
- **Lore.** A small Western state of hills and old mines on the Jura border (film Scarlet Bond: Queen Towa, gold mines, a contaminated lake). A fan cartographer calls its exact position speculative.
- **Faction.** No faction.
- **Terrain (current).** a lake in the belt.
- **Places.** [Raja](places/raja.md), [Rostia](places/rostia.md)

### N: Nostraille

- **Colour** `#E09A6C` · **banner** A quiet hill kingdom of the Western Nations · **extent** x −1952..−1648, z 496..1056
- **Lore.** A quiet hill kingdom of the Western Nations (pack epithet), east of Raja.
- **Faction.** No faction.
- **Terrain (current).** hills in the belt.
- **Places.** [Nostraille](places/nostraille.md)

### Y: Yuzalgh

- **Colour** `#BE508C` · **banner** A lakeside kingdom on the road between Englassia and Jura · **extent** x −1648..−1504, z 496..1056
- **Lore.** A lakeside kingdom on the road between Englassia and Jura (pack epithet).
- **Faction.** No faction.
- **Terrain (current).** lakeside in the belt.
- **Places.** [Yuzalgh](places/yuzalgh.md)

### Q: Yggdonia

- **Colour** `#E2A06E` · **banner** A small birchwood realm on Blumund's southern border · **extent** x −1504..−1296, z 0..592
- **Lore.** A small birchwood realm on Blumund's southern border (pack epithet).
- **Faction.** No faction.
- **Terrain (current).** birch woods north of the belt.
- **Places.** [Yggdonia](places/yggdonia.md)

### H: Harpy Queendom of Fulbrosia

- **Colour** `#DD9668` · **banner** 天翼国フルブロジア · **extent** x −3952..−1552, z 1056..2672
- **Lore.** Frey's sky kingdom of harpies; in canon it sits on top of a mountain range on Jura's border, capital Jia.
- **Faction.** No faction in the pack yet.
- **Terrain (current).** south-western crystal hills with mesas (windswept hills, desert edge).
- **Places.** [Sainte Malukshure](places/sainte_malukshure.md), [Jia](places/jia.md)

### I: Ice Continent

- **Colour** `#D3A549` · **banner** 氷の大陸 — 白氷宮 · **extent** x −3856..2192, z −5536..−2816
- **Lore.** Guy Crimson's frozen northern continent with the Frost Palace (White Ice Palace). The illustrated map calls it the 'Tundral Waste' and shows a great rift and ice-floe islands.
- **Faction.** No faction.
- **Terrain (current).** a snowy island far to the north with a river to its south shore.
- **Places.** [Frost Palace](places/frost_palace.md)

### X: El Dorado

- **Colour** `#E1DA42` · **banner** 黄金郷エルドラド · **extent** x −5824..−1104, z 2848..5840
- **Lore.** The south-western continent ruled alone by Demon Lord Leon Cromwell from the Golden City. A volcano at its centre supplies the precious metals that fund the country.
- **Faction.** No faction.
- **Terrain (current).** a southern island with plains, a volcano and lakes.
- **Places.** [Golden City of El Dorado](places/el_dorado.md), [El Dorado volcano](places/el_dorado_volcano.md)

## 5. Every canon place (58 anchors)

One row per entry of `design/data/anchors.toml`. **Kind**: *settlement* (own scripts), *build* (our own blueprint),
*landmark* (a Tensura mod structure placed in game), *pin* (map label only), *spot* (an NPC, boss, quest or camp point),
*arrival* (the Life 2 spawn). **x, z are Lerfing's coordinates and will change**; the last column says where the place lies
relative to Tempest. Each name links to its place page (lore, design intent, BlueMap audit, screenshots); "Lore page" is the
long canon note in `design/lore/`.


### Jura

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Tempest (Rimuru, capital of the Federation)](places/tempest.md) | J | settlement | 1720, 900 | Tempest itself | Rimuru's capital, the Jura-Tempest Federation. Built as the early hobgoblin village just after the six ogres were named, then grown in two later rings (trade town, festival capital). | [tempest.md](../../design/lore/tempest.md) |
| [Life 2 arrival (world spawn), yaw -149](places/arrival.md) | J | arrival | 1660, −100 | 1,000 blocks N | Where every Life 2 soul wakes. On the safe rim of Jura, on the road between Tempest and Dwargon. | [world.md](../../design/lore/world.md) |
| [Wayfarers' camp on Jura's rim (sidequests rim_camp)](places/wayfarers_camp.md) | J | spot | 1675, −85 | 990 blocks N | Small camp beside the arrival where wayfarers and the first side quests wait. | [world.md](../../design/lore/world.md) |
| [Sealed Cave (Veldora's prison, Rimuru's birthplace)](places/sealed_cave.md) | J | build | 1380, 560 | 480 blocks NW | Veldora's prison and Rimuru's birthplace, a cave in a rocky hill of the Jura forest. | [sealed_cave.md](../../design/lore/sealed_cave.md) |
| [Old goblin village (Rigurd's tribe)](places/goblin_village.md) | J | landmark | 1390, 710 | 380 blocks NW | Rigurd's tribe's old village: poor wooden huts in the Jura forest, north-west of Tempest. | [world.md](../../design/lore/world.md) |
| [Spirit Gate (Ramiris' doorway)](places/spirit_gate.md) | J | build | 1570, 1130 | 270 blocks SW | Ramiris' doorway to the Dwelling of the Spirits (own dimension), south-south-west of Tempest. | [spirit_domain.md](../../design/lore/spirit_domain.md) |
| [Hinata's ambush west of Tempest (bosses.toml hinata_sakaguchi spawn, r 48)](places/shizu_spawn.md) | J | spot | 1300, 820 | 430 blocks W | Where Hinata's ambush party waits, west of the Tempest lake (Shizu's meeting place in the novels). | [world.md](../../design/lore/world.md) |
| [The Outcast on Tempest's south road](places/outcast_road.md) | J | spot | 1720, 952 | 50 blocks S | Spot on Tempest's south road where the Outcast Society's contact waits. | [world.md](../../design/lore/world.md) |
| [Treyni's grove (Dryad sanctuary)](places/treyni_grove.md) | J | landmark | 1920, 1540 | 670 blocks S | Treyni's grove: the dryad sanctuary of the Great Jura Forest, with an ancient tree. | [treyni_shrine.md](../../design/lore/treyni_shrine.md) |
| [Treyni's shrine (beside the grove's tree)](places/treyni_shrine.md) | J | build | 1958, 1540 | 680 blocks S | Dryad altar beside the ancient tree, 38 blocks east of the grove. | [treyni_shrine.md](../../design/lore/treyni_shrine.md) |
| [Hidden ogre village (Kijin homeland, burned)](places/ogre_village_ruin.md) | J | landmark | 2150, 400 | 660 blocks NE | The hidden ogre village, the kijin homeland the orcs burned. North-eastern hills of Jura. | [world.md](../../design/lore/world.md) |
| [The old well on the Blumund road (sidequests old_well)](places/old_well.md) | J | spot | 300, 410 | 1,500 blocks W | The old well on the straight road from Blumund to Tempest. | [world.md](../../design/lore/world.md) |
| [The abandoned rookie camp (sidequests rookie_camp)](places/rookie_camp.md) | J | spot | 1550, −60 | 970 blocks N | Abandoned rookie camp on the rim between the arrival and Tempest. | [world.md](../../design/lore/world.md) |

### Dwargon and the Canaat

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Dwargon](places/dwargon.md) | D | settlement | 1878, −544 | 1,450 blocks N | The Armed Nation of Dwargon's main gate. The dwarf kingdom's underground city lies inside the Canaat mountain behind it. | [dwargon.md](../../design/lore/dwargon.md) |
| [Dwargo (Dwargon cavern capital)](places/dwargo.md) | D | pin | 1878, −644 | 1,550 blocks N | Map pin of the cavern capital, under the mountain behind the gate. | [dwargon.md](../../design/lore/dwargon.md) |
| [Gazel's throne room (statue)](places/dwargon_throne.md) | D | spot | 1878, −650 | 1,560 blocks N | Gazel Dwargo's throne room, a statue boss spot at the top of the city. | [dwargon.md](../../design/lore/dwargon.md) |
| [Kaijin's smithy](places/kaijin_smithy.md) | D | spot | 1866, −628 | 1,530 blocks N | Kaijin's smithy on the forge street, where the Artificer path steals and works. | [dwargon.md](../../design/lore/dwargon.md) |
| [Dwarf village on the road to Dwargon](places/dwarf_village.md) | D | landmark | 2000, −110 | 1,050 blocks N | Dwarf village on the Canaat apron foot beside the road to Dwargon. | [world.md](../../design/lore/world.md) |
| [Dwarven Arena](places/dwarven_arena.md) | D | build | 2260, −80 | 1,120 blocks NE | The Dwarven Arena: the duel and party arena of the dwarves, east of the dwarf village. | [dwarven_arena.md](../../design/lore/dwarven_arena.md) |
| [Dragon's Nest (highest peak of the Great Canaat Mountains)](places/dragons_nest.md) | D | build | 2420, −1536 | 2,530 blocks N | The Dragon's Nest on the summit shoulder of the Great Canaat Mountains, the highest range of the continent. | [dragons_nest.md](../../design/lore/dragons_nest.md) |
| [Great Ameld River source (Canaat foothills)](places/ameld_source.md) | D | pin | 2500, −200 | 1,350 blocks NE | Source of the Great Ameld River in the Canaat foothills. | [world.md](../../design/lore/world.md) |

### Lake Siss and its marsh

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Lake Siss (Charybdis arena centre, r 96)](places/lake_siss.md) | W | pin | 3050, 750 | 1,340 blocks E | Lake Siss, the lizardmen's lake, with its marsh ring and the arena of the whirlpool boss Charybdis. | [world.md](../../design/lore/world.md) |
| [Lizardmen's stilt village](places/lizardmen_village.md) | W | landmark | 3184, 988 | 1,470 blocks E | The lizardmen's stilt village on the south shore of Lake Siss. | [world.md](../../design/lore/world.md) |
| [Lizardmen's caverns (Gabiru, Avalos)](places/lizardmen_caverns.md) | W | landmark | 3300, 1200 | 1,610 blocks E | The lizardmen's underground caverns: fortress and seat of government (Gabiru, Avalos). | [world.md](../../design/lore/world.md) |
| [Orc War battlefield (Orc Lord, Orc Disaster)](places/orc_camp.md) | W | landmark | 3600, 1250 | 1,910 blocks E | The Orc War battlefield, where Geld's horde gathered south-east of Lake Siss. | [world.md](../../design/lore/world.md) |

### Milim, Jistav and the Eastern Empire

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Great Ameld River mouth](places/ameld_mouth.md) | MB | pin | 4580, 2300 | 3,180 blocks SE | Mouth of the Great Ameld River in the eastern sea, between Milim's land and Eurazania. | [world.md](../../design/lore/world.md) |
| [City of the Forgotten Dragon (Milim)](places/forgotten_dragon_city.md) | M | build | 4680, 840 | 2,960 blocks E | The City of the Forgotten Dragon, Milim Nava's capital and temple-castle. | [forgotten_dragon_city.md](../../design/lore/forgotten_dragon_city.md) |
| [Clayman's Castle (Walpurgis gate inside)](places/clayman_castle.md) | P | build | 5620, −900 | 4,300 blocks NE | Clayman's Castle in Jistav, seat of the Demon Lord Clayman, 'Crazy Pierrot'. | [clayman_castle.md](../../design/lore/clayman_castle.md) |
| [Amrita (Jistav capital)](places/amrita.md) | P | build | 6100, −650 | 4,650 blocks E | Amrita, the buried ancient capital of Jistav, a dark elf ruin. | [amrita.md](../../design/lore/amrita.md) |
| [Nasca (Eastern Empire capital)](places/nasca.md) | E | build | 5100, −2680 | 4,920 blocks NE | Nasca, capital of the Eastern Empire under Emperor Rudra. | [nasca.md](../../design/lore/nasca.md) |
| [Great Holy Mountain (Velgrynd's sanctuary)](places/great_holy_mountain.md) | E | build | 5120, −1860 | 4,380 blocks NE | The Great Holy Mountain (Scorching God Mountain), Velgrynd's sanctuary, north-west flank of the red crater of the Eastern Empire. | [great_holy_mountain.md](../../design/lore/great_holy_mountain.md) |

### Eurazania and Sarion

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Elmine (Sarion capital in the Divine Tree)](places/elmine.md) | S | build | 1100, 2760 | 1,960 blocks S | Elmine, capital of Emperor Elmesia's elven Sorcerous Dynasty of Sarion, built in the colossal Divine Tree. | [elmine.md](../../design/lore/elmine.md) |
| [Laura (Eurazania capital, rebuilt)](places/laura.md) | B | build | 3300, 2600 | 2,320 blocks SE | Laura, the rebuilt capital of Carrion's Beast Kingdom of Eurazania. | [laura.md](../../design/lore/laura.md) |

### The west: Blumund, Falmuth, Englassia, Lubelius, Ulgracia

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Blumund](places/blumund.md) | R | build | −450, 150 | 2,300 blocks W | Blumund's capital Londo with Fuze's Free Guild branch hall; Tempest's first human partner. | [blumund.md](../../design/lore/blumund.md) |
| [Ballachia](places/ballachia.md) | G | build | −1660, −460 | 3,640 blocks W | Ballachia, the former Orthrus exchange, where the freed elves start their journey home. | [ballachia.md](../../design/lore/ballachia.md) |
| [Englassia](places/englassia.md) | G | build | −2150, −410 | 4,090 blocks W | Englassia's capital (Lura): the Freedom Academy and the Free Guild headquarters. | [englassia.md](../../design/lore/englassia.md) |
| [Marris (Falmuth capital)](places/marris.md) | F | build | −2000, −1450 | 4,400 blocks NW | Marris, capital of the rich kingdom of Falmuth (later Farmenas). | [marris.md](../../design/lore/marris.md) |
| [Siltrosso](places/siltrosso.md) | F | build | −2450, −1650 | 4,890 blocks NW | Siltrosso, the small kingdom of the Rosso family (Granbell, Mariabell). | [siltrosso.md](../../design/lore/siltrosso.md) |
| [Holy City Lubelius (Lune)](places/lubelius.md) | L | build | −2550, −700 | 4,560 blocks W | The holy city Lubelius (Lune), seat of the Western Holy Church and secret domain of Luminous. | [lubelius.md](../../design/lore/lubelius.md) |
| [Sacred Mountain (Inner Sanctum, Luminous)](places/sacred_mountain.md) | L | build | −2980, −900 | 5,030 blocks W | The Sacred Mountain and the sealed Inner Sanctum gate of Lubelius. | [sacred_mountain.md](../../design/lore/sacred_mountain.md) |
| [Filtwood](places/filtwood.md) | U | pin | −900, 700 | 2,630 blocks W | Filtwood, a pin in Ulgracia's woodland. | [world.md](../../design/lore/world.md) |
| [Ghastone](places/ghastone.md) | G | pin | −2000, 300 | 3,770 blocks W | Ghastone, a pin on Englassia's western plain. | [world.md](../../design/lore/world.md) |
| [Galut / Ulgr Nature Park (Ulgracia)](places/ulgr_nature_park.md) | U | build | −1040, 1060 | 2,760 blocks W | Galut / Ulgr Nature Park, Ulgracia's woodland park and the entrance to the Dwelling of the Spirits in the series. | [ulgr_nature_park.md](../../design/lore/ulgr_nature_park.md) |
| [Blumund road camp at Jura's edge (sidequests blumund_road)](places/blumund_road.md) | R | spot | −250, 250 | 2,070 blocks W | Road camp on the Londo-Tempest road, at Jura's edge. | [world.md](../../design/lore/world.md) |
| [Englassia road post (sidequests englassia_road)](places/englassia_road.md) | G | spot | −1880, −500 | 3,860 blocks W | Road post on the eastbound road between Ballachia and Lura. | [world.md](../../design/lore/world.md) |

### The small western nations, Fulbrosia and Damargania

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Coleus](places/coleus.md) | V | build | −3080, 600 | 4,810 blocks W | Coleus, the oasis palace kingdom of Herbaria (film Visions of Coleus). | [coleus.md](../../design/lore/coleus.md) |
| [Heaven Tower (Dagruel, Damargania)](places/heaven_tower.md) | V | build | −4500, 560 | 6,230 blocks W | Heaven Tower, capital of Dagruel's Holy Void of Damargania in the Desert of Death. | [heaven_tower.md](../../design/lore/heaven_tower.md) |
| [Morgdahl](places/morgdahl.md) | O | build | −2440, 740 | 4,160 blocks W | Morgdahl, a river-mouth kingdom of the small western nations. | [morgdahl.md](../../design/lore/morgdahl.md) |
| [Raja](places/raja.md) | A | build | −2050, 760 | 3,770 blocks W | Raja, a small western state of lakes and gold mines (film Scarlet Bond). | [raja.md](../../design/lore/raja.md) |
| [Nostraille](places/nostraille.md) | N | build | −1780, 550 | 3,520 blocks W | Nostraille, a quiet hill kingdom of the western council. | [nostraille.md](../../design/lore/nostraille.md) |
| [Yuzalgh](places/yuzalgh.md) | Y | pin | −1580, 650 | 3,310 blocks W | Yuzalgh, lakeside kingdom on the road between Englassia and Jura. | [world.md](../../design/lore/world.md) |
| [Yggdonia](places/yggdonia.md) | Q | pin | −1400, 300 | 3,180 blocks W | Yggdonia, small birchwood realm on Blumund's southern border. | [world.md](../../design/lore/world.md) |
| [Rostia](places/rostia.md) | A | pin | −2100, 1000 | 3,820 blocks W | Rostia, a pin on the river-and-lake belt near Raja. | [world.md](../../design/lore/world.md) |
| [Sainte Malukshure](places/sainte_malukshure.md) | H | pin | −2500, 1300 | 4,240 blocks W | Sainte Malukshure, a pin south of Morgdahl. | [world.md](../../design/lore/world.md) |
| [Jia (Fulbrosia capital, Frey)](places/jia.md) | H | build | −2700, 1500 | 4,460 blocks W | Jia, capital of Frey's harpy queendom of Fulbrosia, in the south-western crystal hills. | [jia.md](../../design/lore/jia.md) |

### The islands

| Place | Region | Kind | x, z | From Tempest | Lore summary | Lore page |
|---|---|---|---|---|---|---|
| [Golden City of El Dorado (Leon)](places/el_dorado.md) | X | build | −3300, 4300 | 6,060 blocks SW | The Golden City of El Dorado, Demon Lord Leon Cromwell's city on the south-western continent. | [el_dorado.md](../../design/lore/el_dorado.md) |
| [El Dorado volcano](places/el_dorado_volcano.md) | X | pin | −2850, 4600 | 5,880 blocks SW | The volcano of El Dorado, source of its gold (peak 221 at (-2858, 4672)). | [world.md](../../design/lore/world.md) |
| [Frost Palace (Guy Crimson)](places/frost_palace.md) | I | build | −1980, −4300 | 6,380 blocks NW | The Frost Palace of Guy Crimson on the Ice Continent. | [frost_palace.md](../../design/lore/frost_palace.md) |

Not canon but part of the game (pack inventions, listed so you do not mistake them for sources): the Life 2 arrival, the wayfarers' camp,
the Outcast contact on Tempest's south road, the rookie camp, the old well, the road camps and the Dwarven Road itself.

Lerfing's own builds (a stilt-hut village on Lake Siss, ice crystals on the Ice Continent, builds on a north islet, a spawn chest, Paulzero's
giant trees) are kept on the current map only. They are **not** part of the new world.

## 6. Owner decisions about the world

These are decisions of the owner (Yasuke), recorded in [`design/decisions.md`](../../design/decisions.md) and
[`design/architecture/`](../../design/architecture/). They hold for the new world unless Yasuke says otherwise.

1. **A new, fully own map (19/11/2026).** It replaces Lerfing's imported map. ChatGPT draws it; Claude does the technical import. The relations in this file are the brief.
2. **Continent, ocean, vanilla beyond.** The canon continent, then an ocean ring, then the ordinary vanilla overworld. Life 2 is the Tensura world (overworld of `world-ttl`); Life 1 is a separate dimension, the Mortal Realm.
3. **The Jura rings.** Veldora's leaked magicule soaks the Jura forest, so weak souls must not stroll to Tempest. By radius from Tempest: a **core** (r about 200) of Tensura's ancient forest with 20,000 magicule, **deadly for a fresh soul** (decision: never "fix" it); a **dark band** (r 200 to about 600) of dark forest with 2,000; a **rim** (the rest of Jura) of ordinary forest and plains with 500, safe. Water, rivers and beach are not repainted (a lake shore inside the core is the one place the magicule thins). Player-facing: [wiki/en/jura-rings.md](../wiki/en/jura-rings.md).
4. **The arrival on the edge of the forest.** Every Life 2 soul wakes on Jura's safe rim, on the road between Tempest and Dwargon, about 1,000 blocks north of Tempest and 500 south of Dwargon's gate, facing the gate. Open natural ground at the forest's edge; no hostile mob spawns within 48 blocks; 20 seconds of grace. Weak souls reach Tempest only by crossing the dark band and the core, on purpose.
5. **Dwargon INSIDE the mountain.** The gate stands at the foot of an escarpment on the Canaat's south flank facing south onto the apron; the city is a cavern under the plateau with at least 7 blocks of rock above it; a skylight crack opens over the main street. The mountain is grey rock (gravel, clay, tuff, cobble). (An earlier "Dwargon on a plain" override was superseded.)
6. **Tempest and Treyni deep in forest.** "This should be in the middle of a forest": Tempest stands in a cleared hollow in the middle of a dense old forest (ring r 60..250 planted with Tensura's giant ancient-forest trees and ordinary trees, about 55 % canopy), and Treyni's shrine and grove stand deep in old, dense forest (planned canopy 76 %). The new map must grow these forests as the terrain, not as an afterthought.
7. **Roads.** "There is also no road to Dwargon?" The **Dwarven Road** links Tempest and Dwargon: 4 to 5 blocks wide, 1,478 blocks, a lantern post every 40 blocks, dirt and gravel in Jura, stone on the mountain, passing about 30 blocks east of the arrival; bridges where it crosses water. A road to Blumund (leaving Tempest's west gate) is wanted next; later roads to the other nations (canon: Tempest builds roads to its trade partners).
8. **No structures pasted on.** The world must not look like buildings dropped on a map. Builds grow out of their terrain: cut into a hill, standing on a real slope, with no flat square pads, no floating foundations, no stray water or lava in the box. (The audit lists the pad problems of the current placement per place.)
9. **Real trees.** Forests are real trees: Tensura's giant ancient-forest trees (up to about 45 blocks high) with ordinary trees between them, on dry soil, never painted grass under a forest biome. Open plains stay open.
10. **No generated structures inside the continent.** No wild Tensura villages and no vanilla structures (treasure maps, trial chambers) on the continent; only our builds and landmarks. The free lands beyond the ocean keep them.
11. **Sarion and Fulbrosia swap (decision Q3):** Sarion (Elmine, the Divine Tree) sits on the south-central peninsula; Fulbrosia (the harpies, Jia) in the south-western hills.
12. **Sea level y 65; highest peak under y 320.** The Dragon's Nest build is 46 blocks tall and must top out below 320.
13. **The BlueMap stays public** with the credit "Map: Tensura by Lerfing" while Lerfing's map is in use. The map was purchased by Yasuke and its licence allows use on servers, but it is **not redistributed as world files**: no world, region or zip files, and no full-resolution terrain exports, ever go in this public repository. Only renders and screenshots do. The new map is original and needs no such credit.

## 7. What the new map must keep (the brief in short)

- Tempest in the middle of Jura, in a clearing of an old, dense forest, with a lake to the west and a pond to the south (running water).
- A magicule gradient round Tempest: deadly core, dark band, safe rim; the arrival on the rim at the forest's edge, on a road that leads north to the mountain.
- Dwargon in the mountain north of Jura, about 1,450 blocks from Tempest, gate facing south; the Canaat is the highest range; the Dragon's Nest on its highest shoulder; the Great Ameld River rising at its foot.
- Lake Siss and its marsh east of Jura; Milim's badland beyond; Jistav and the Eastern Empire north-east of it.
- Eurazania (jungle) south-east, Sarion (the Divine Tree) south, Blumund west across a channel, then the Western Nations; Damargania's desert far west; the Ice Continent north; El Dorado south-west.
- Treyni's grove east of the river that drains Jura's lakes, deep in forest, about 670 blocks south-east of Tempest; the Spirit Gate in dark forest by the lake, about 275 blocks south-south-west; the Sealed Cave on a rocky hill north-west; the old goblin village between the lake and the cave.
- Everything listed in section 5 needs a place on the map; builds need ground that suits them (see the place pages: a desert palace on a sandstone hill, a harbour town by the sea, an underground ruin in badlands, and so on).

See [tasks.md](tasks.md) for the open world-map task; the deliverable spec will follow there.
