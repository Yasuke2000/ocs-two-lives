# Tempest (early): lore behind blueprints/tempest.py

The build reference for early Tempest: the hobgoblin village just after the ogres were named (anime season 1,
episodes 9–11; light novel vol. 1–2). Geography and placement are in [world.md](world.md) §J. Read this before
changing the blueprint.

**Research note (18/11/2026).** tensura.fandom.com returns HTTP 402 to direct fetches and its BreezeWiki mirror
blocks bots (Anubis), so the facts below come from Wikipedia and episode reviews. Items marked *(unverified)* are
from memory of the anime, manga and light novel and could not be checked; treat them as our own design choices.

## Facts the build follows

| Fact | How the build shows it | Source |
| --- | --- | --- |
| Rimuru brought dwarf artisans from Dwargon so the goblins could make their own food, shelter and clothing; King Gazel exiled Kaijin and his men, who joined Rimuru | Kaijin's workshop house and open forge on the west road; finished timber houses | [Wikipedia, season 1 (ep. 4–5)](https://en.wikipedia.org/wiki/That_Time_I_Got_Reincarnated_as_a_Slime_season_1); search extract on vol. 1 *Empowerment* |
| Kaijin is a master blacksmith; Garm (eldest) makes armour, Dold jewellery/crafts, the youngest (Mildo, "Myrd" on Wikipedia) is the architect who barely speaks | Forge (anvil, blast furnaces, smithing table, grindstone, quench cauldron); workshop with crafting, fletching, cartography tables, loom and stonecutter; houses in different finishing stages | [Wikipedia, character list](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| Episode 9: "the village is developing nicely; the dwarves are building all kinds of houses and furniture"; "as work on the goblin village continues" | Building site in the south-west: half-roofed house with scaffolding, a timber frame on a plank floor, a stone foundation, log piles, plank stacks, sawhorse | [episode 9 summary (search extract)](https://tools.latamautos.com/series/82684/that-time-i-got-reincarnated-as-a-slime/season-1/episode-9), [ANN ep. 9 review](https://animenewsnetwork.com/review/that-time-i-got-reincarnated-as-a-slime/episode-9/.140005) |
| Ogres attack, Rimuru persuades them to talk at the goblin village; he names six (Benimaru, Shuna, Shion, Souei, Hakurou, Kurobe) who become kijin; ep. 11: the kijin settle in, Gabiru comes to the village | Council longhouse on the green where Rimuru holds meetings (long table, his seat on a dais at the end); the cooking fire on the green | [Wikipedia, season 1 (ep. 9–11)](https://en.wikipedia.org/wiki/That_Time_I_Got_Reincarnated_as_a_Slime_season_1) |
| Shuna makes clothing and teaches the goblins the craft | Shuna's weaving hut (looms inside and under an awning, dyed wool bales, a cloth drying line) | [Wikipedia, character list](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| Kurobe, "Blacksmith", makes most tools and weapons with Kaijin | His anvil in Kaijin's forge | [Wikipedia, character list](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| The ogres' weapons and clothing have a Japanese look, unlike the western-fantasy world | Not built yet (no ogre house); a later version could add one with dark oak and paper-lantern style | [ANN ep. 9 review](https://animenewsnetwork.com/review/that-time-i-got-reincarnated-as-a-slime/episode-9/.140005) |
| Goblin riders wear hell-moth cloth; Shuna's fabric work uses hell-moth cocoons | White wool bales and cloth in the weaving hut | [TV Tropes (search extract)](https://tvtropes.org/pmwiki/pmwiki.php/Anime/TenseiShitaraSlimeDattaKen); web-novel ch. 30 translator note (search extract) |
| Rigurd is the goblins' leader under Rimuru (Goblin King) | Rimuru's own small house behind the longhouse; Rigurd has no house of his own yet *(our choice)* | [Wikipedia, character list](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| The goblins lived in shabby huts before; the new town replaces them gradually *(unverified)* | Four domed huts of straw, leaves and hides and three hide tents in the north-east, still lived in | memory of anime ep. 2–3 |
| Hipokute herbs (Rimuru's potions) are cultivated *(unverified for this period)* | Fenced herb patch beside the field | memory of the light novel |
| Hakurou trains the goblin riders; Souei scouts *(unverified details)* | Lookout tower in the north-west | our choice |
| Temperate primeval forest, clearings round Tempest | Rounded clearing (radius ~38) ringed by oak, birch, dark oak and spruce | [world.md](world.md) §J |

Not shown (deliberately, too late for "just after the ogres"): stone roads, sewers, the Tempest flag, Create
machinery, walls of stone. The palisade is only begun (west side, a south gate, low stakes where it stops).

## Placement

World 0, 0 (the Life 2 world spawn) = the arrival point, blueprint (45, 5, 57). canon_regions.json puts the
Tempest landmark at ref [1790, 1122] → about (-10, -70); that is inside the fan map's precision, and the spawn
is the more important anchor, so 0, 0 is kept. `TtlTempest.LANDMARK` in `life/tempest.js` moves it.
