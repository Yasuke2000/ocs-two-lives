# City of the Forgotten Dragon: lore behind blueprints/forgotten_dragon_city.py

The build reference for Milim Nava's capital (忘れられた竜の都). Geography and placement are in [world.md](world.md) §M,
the placement contract in `design/builds/forgotten_dragon_city.toml`. Read this before changing the blueprint.

**Research note (18/11/2026, lore pass).** tensura.fandom.com refuses direct fetches (HTTP 402; its BreezeWiki and
antifandom mirrors sit behind a bot wall), so the wiki facts below come from search-engine extracts of the pages named
under each row, plus the Japanese Wikipedia article and anibase character pages. Items marked *(our interpretation)*
are ours. The full findings of the pass are in [lore-pass-2026-11.md](lore-pass-2026-11.md).

## Where it is (canon)

**Own-world placement, 20 November 2026:** the current authored anchor is (2650,800), radius 100.
The broad territory relationship below remains wiki-level evidence; exact city coordinates and the two
approach trails are our interpretation. The secondary marker benchmark is in
[proportion-audit.csv](../../world/proportion-audit.csv). This old settlement is distinct from later
planned capital project in former Eurazania. [LN20 chapter 1's opening](../../docs/research/tensura-world-2026-11-19/ln20-licensed-capital-review.md) establishes that broader setting, not an exact site at `laura`. No later annexation or castle construction is applied to the post-Kijin baseline.

| Fact | Source |
| --- | --- |
| The city is "Milim Nava's domain, sitting south of Jura Forest and east of the Beast Kingdom of Eurazania" | [Fandom: City_of_the_Forgotten_Dragon](https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon) (search extract) |
| The Great Ameld River "flows all the way from the base of the Great Canaat Mountains into the southern ocean" and "feeds … the fertile plains that make up Milim Nava's territory on the southern edge of the continent" | [Fandom: Great_Ameld_River](https://tensura.fandom.com/wiki/Great_Ameld_River) (mirror extract) |
| Milim's territory lies "at the eastern edge of the continent"; the temple in the capital "doubles as Milim Nava's castle" | [anibase, Middray](https://anibase.net/en/character/mOvy5/Middray), [anibase, Milim Nava](https://anibase.net/en/character/4dZxB/Milim-Nava) |
| Milim "忘れられた竜の都に居城を持ち、民から信仰の対象として崇められている" (has her castle in the City of the Forgotten Dragon and is worshipped by its people) | [Japanese Wikipedia, ミリム・ナーヴァ](https://ja.wikipedia.org/wiki/転生したらスライムだった件) |
| After Walpurgis Clayman's Jistav is jointly ruled by Rimuru and Milim; Carrion's Eurazania becomes her vassal state | world.md §P, Japanese Wikipedia (カリオン: Milim's vassal and commander) |

On Lerfing's map that puts the capital in region M, east of Lake Siss and Jura, north-east of Eurazania (B) and south-west of Jistav (P). The
build surveys from (4680, 840), 2,960 blocks east of Tempest on the lake-and-river plain of the badlands (relief 2, stored biome
badlands and plains), see the toml for the reasoning.

## What it is (canon)

| Fact | How the build shows it | Source |
| --- | --- | --- |
| Milim's domain; fewer than 100,000 citizens, dragonewts, called "Dragon's Village" in the nation table | A town of round huts and open granaries, no walls and no barracks | [Fandom: Magic_Continent](https://tensura.fandom.com/wiki/Magic_Continent), [City_of_the_Forgotten_Dragon](https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon) |
| No government: the Dragon Faithful run daily life as worshippers of Milim; the economy runs through the **Central Temple**, where crops and goods are gathered and "handed out evenly by the head priest"; Middray holds the right to set the contributions, Hermes is his equal in strength | The Central Temple (stepped pyramid) with a distribution hall (counter, barrels, hay) and two granaries on the avenue; a priests' pavilion on the summit | [Fandom: Dragon_Faithful](https://tensura.fandom.com/wiki/Dragon_Faithful), [anibase, Hermes](https://anibase.net/en/character/moQMD/Hermes) |
| The temple is Milim's castle | Milim's throne on the dais at the back of the temple hall (the Milim NPC stands before it, `npcs.toml`) | anibase (above), Japanese Wikipedia |
| Milim took the dragonewts in and protected them; they built the city in her honour | Pink banners at the gate and by the throne (her colour, *our choice*) | [Fandom: Milim_Nava](https://tensura.fandom.com/wiki/Milim_Nava) |
| A flock of wyverns lives in the city | **Not built yet** (idea: a wyvern roost on the temple's upper tiers) | [Fandom: Wyvern](https://tensura.fandom.com/wiki/Wyvern) |
| The land is primitive and poor until Tempest develops it; a commune, not a kingdom | Mud-brick huts with thatch cone roofs (Tensura thatch), campfires, wheat plots, animal pens, a pond; no Tempest technology | world.md §M; light novel vol. 7–8 (Tempest's aid to Milim's domain) |
| River-fed plains, warm south | Savanna acacias, coarse dirt and packed mud; the region palette gives savanna and plains round it | [Fandom: Great_Ameld_River](https://tensura.fandom.com/wiki/Great_Ameld_River) |
| "Forgotten Dragon": the name most likely recalls the dragon that was Milim's friend, whose death drove her awakening (anime season 4 "Milim's Friend", light novel vol. 13 flashback) | The city grew inside the bones of a dead ancient dragon: skull gate, rib arches over the avenue *(our interpretation, a resonance, not a sourced fact)* | [Milim's Friend, season 4 episode 11](https://www.animeoshi.com/anime/that-time-i-got-reincarnated-as-a-slime-season-4/episode/11) |

Canon gives no floor plan or architecture for the city; the stepped temple, the skull and ribs, the bone throne and
the layout below are *our interpretation*.

## Layout in short (blueprint coordinates, south = +z)

South to north: avenue (x 56–64) under six bone rib arches (z 72–112), granaries either side (z 74–94), a plaza with
bone fires (z 58–71), the dragon skull (cranium, glowing eye sockets, horns) whose mouth (x 56–64) is the tunnel into the
Central Temple's hall (x 49–71, z 22–46); stairs on the east and west faces climb the five tiers to a summit pavilion
with a bonfire. Huts, a field, animal pens and a pond fill the sides.

## Reference builds looked at

Tensura's own village pieces (the `dwarf_village` and `goblin_village` sets, the palm goblin variant) for the thatch and
mud palette; Towns and Towers' `jungle_tribal`, `sparse_jungle_polynesian`, `savanna_plateau_ramshackled` and
`desert_temple_mimic` pieces for hut and temple massing, as visual references only (licence CC-BY-NC-ND 4.0: no
derivatives, so nothing was copied). Nothing from the owner's Downloads fits a dragon temple.
