# City of the Forgotten Dragon: lore behind blueprints/forgotten_dragon_city.py

The build reference for Milim Nava's capital. Geography and placement are in [world.md](world.md) §M, the placement
contract in `design/builds/forgotten_dragon_city.toml`. Read this before changing the blueprint.

**Research note (18/11/2026).** tensura.fandom.com returns HTTP 402 to direct fetches and fetching its mirrors was
not allowed, so the facts below come from search-engine extracts of the wiki pages and from world.md. Canon says what
the city is and how it is run, not what it looks like: the architecture is *our interpretation*.

## Facts the build follows

| Fact | How the build shows it | Source |
| --- | --- | --- |
| The city is Milim Nava's domain; fewer than 100,000 dragonewt citizens, managed by the Dragon Faithful | A town of round huts and open granaries, no walls and no barracks; a priests' pavilion on the temple | [Fandom: City_of_the_Forgotten_Dragon (search extract)](https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon) |
| No government; the system revolves around a Central Temple that distributes goods | The Central Temple (stepped pyramid) with a distribution hall (counter, barrels, hay) and two granaries on the avenue | same |
| A primitive commune of those who worship Milim ("Dragon's Village") | Mud-brick huts with thatch cone roofs (Tensura thatch), campfires, dry wheat plots, a pond | [Fandom: Magic_Continent (search extract)](https://tensura.fandom.com/wiki/Magic_Continent) |
| The domain is poor and underdeveloped until Tempest helps; dry, rugged savanna and badlands by a lake and the Great Ameld River | Savanna acacias, coarse dirt and packed mud, plain materials; no Tempest tech (a later version could add some) | [world.md](world.md) §M |
| It is an old city: one source calls it the former capital of the Forgotten Dragon | The "forgotten dragon" is a dead ancient dragon whose skull is the temple gate and whose ribs arch over the avenue *(our interpretation)* | [Quote the Anime, Milim Nava](https://quotetheanime.com/reincarnated-as-a-slime/milim-nava/) |
| Milim is the Demon Lord of the place and uses it as her base | A bone-and-pink-terracotta throne at the back of the distribution hall, pink banners (her hair colour, *our choice*) | [Fandom: Milim_Nava (search extract)](https://tensura.fandom.com/wiki/Milim_Nava) |

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
