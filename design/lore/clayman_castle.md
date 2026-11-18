# Clayman's Castle: lore behind blueprints/clayman_castle.py

The build reference for the seat of the Demon Lord Clayman, "Crazy Pierrot", in the Puppet Nation of Jistav
(anime season 2, the Walpurgis arc; light novel vol. 6–7). Geography and placement are in [world.md](world.md) §P,
the placement contract in `design/builds/clayman_castle.toml`. Read this before changing the blueprint.

**Research note (18/11/2026).** tensura.fandom.com returns HTTP 402 to direct fetches and fetching its mirrors was
not allowed, so the canon below comes from search-engine extracts of episode reviews and from world.md. Canon barely
describes the castle's looks; almost everything visual is *our interpretation* and marked so.

## Facts the build follows

| Fact | How the build shows it | Source |
| --- | --- | --- |
| Clayman's castle is a defended stronghold in Jistav; the raid on it had to coincide with Walpurgis so that he was away | A full fortress: moat, curtain wall with gatehouse, four corner towers, keep | [ANN, episode 43 review](https://cdn02.animenewsnetwork.com/review/that-time-i-got-reincarnated-as-a-slime-season-2/episode-43/.176383), [animecorner, ep. 46 preview](https://animecorner.me/that-time-i-got-reincarnated-as-a-slime-episode-46-preview-images-released/) |
| Shuna, Souei and Hakurou approach through a thick fog that blocks sight and magic detection | Gloomy palette and dead trees on the bank; the fog itself cannot be placed (a later weather script could add it) | [otakuauthor, episode 45 recap](https://otakuauthor.com/?p=16844) |
| A wight king leads Clayman's defence and destroys intruders who enter without permission | A closed gate (raised portcullis) and a bone-and-skull motif; no mobs are placed | [Quote the Anime, Clayman](https://quotetheanime.com/reincarnated-as-a-slime/clayman-wiki/) |
| Clayman is "Crazy Pierrot", the puppet master | A giant pierrot mask over the keep door and on the throne hall's north wall; "puppet" stands (skulls on posts) and gallows frames hung with chains and soul lanterns in the courtyard; marionette controllers (chains and soul lanterns on an iron crossbar) in the throne hall | [MyAnimeList, Clayman "Crazy Pierrot"](https://myanimelist.net/character/168313); mask and marionettes *(our interpretation)* |
| Jistav is a gloomy, hilly, isolated country of dark forest and miasma | Podzol and coarse dirt ground, a moat of dark water, dead dark oaks on the bank; Jistav biomes come from the world, not the build | [world.md](world.md) §P (fandom: Puppet_Nation_of_Jistav) |
| Rimuru fought Clayman at the Walpurgis banquet, not in the castle | The throne hall is just the seat of a Demon Lord; no arena | [animecorner, ep. 48](https://animecorner.me/that-time-i-got-reincarnated-as-a-slime-episode-48-rimurus-victory/) |
| Colours: black, deep purple, soul-fire blue *(our interpretation)* | Deepslate and polished blackstone, purple stained glass and carpet, soul lanterns | — |

## Layout in short (blueprint coordinates, south = +z)

South to north: approach road and bridge over the moat (z 90–97) → gatehouse in the curtain wall (z 86–88, towers at
x 45 and 63) → courtyard (puppet stands, gallows frames, lamp posts) → the keep (x 40–68, z 34–62) with the pierrot
mask over its great door → entrance hall (stair up the west wall to a gallery at y 19) → the 22-block-high throne hall
with the throne on a dais and the pierrot mask behind it. Wall-walk stairs inside the gate lead up to the crenellated
wall (y 18). The keep roof and the spires are not reachable from inside.

## Reference builds looked at

The Iron's Spells 'n Spellbooks Citadel (`citadel/citadel.nbt`, 51×70×51, polished blackstone and deepslate bricks,
buttressed round hall) for the dark gothic proportion and palette, as a visual reference only (licence "All Rights
Reserved"; nothing was copied). The Tensura hell gate pieces were looked at too and not used.
