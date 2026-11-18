# Blumund: lore behind blueprints/blumund.py

The build reference for the walled capital of the Kingdom of Blumund (ブルムンド王国) with the Free Guild's Blumund
branch hall. Geography and placement are in [world.md](world.md) §R. Read this before changing the blueprint.

**Research note (18/11/2026).** tensura.fandom.com returns HTTP 402 to direct fetches, so the facts below come from
Wikipedia's character list and search-engine extracts of the wiki and episode reviews. Canon gives **no architecture
description** of Blumund's capital; everything about how it looks is *our interpretation*. The capital's name is
*unverified*: the fan map labels it "Londo" and world.md keeps that as the landmark name.

## Facts the build follows

| Fact | How the build shows it | Source |
| --- | --- | --- |
| A small human kingdom east of Falmuth, bordering the Jura Tempest Federation; ruled by King Drum Blumund, who gets on well with Rimuru | A compact walled town on the Jura side of Falmuth; a royal castle at the end of the main street; red and cream banners (colours are ours) | [Wikipedia, list of characters](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| The country is essentially its royal capital; the Free Guild's Blumund branch is in the capital and has a strong presence there | The guild hall is the largest civic building on the market square | [search extract of tensura.fandom.com/wiki/Kingdom_of_Blumund](https://tensura.fandom.com/wiki/Kingdom_of_Blumund) |
| Fuze is the branch's Guild Master and assistant supervisor of the kingdom's intelligence department; his father Heinz ran the branch before him | A mezzanine office for the branch master overlooking the hall (desk, map table, shelves, a cot); a counter, boards and a quiet archive below | [tensura.fandom.com/wiki/Fuze](https://tensura.fandom.com/wiki/Fuze) (search extract), Wikipedia |
| Rimuru visits Fuze's guild branch (season 3, after the Seven Days Clergy affair) and invites him to the coronation | The guild door faces the market square, so a visitor from the main gate walks straight to it | [Anime News Network review](https://www.animenewsnetwork.com/review/that-time-i-got-reincarnated-as-a-slime-season-3/episode-60/.212338) |
| Tempest's first human partner, a trading kingdom with adventurers (Kabal, Eren, Gido) | Market square with twelve striped stalls, a merchant cross street, timber-frame shops | world.md §R |
| Blumund sits between Falmuth and Jura | The approach is farmland: wheat fields, a signpost and a milestone on the king's road | world.md §R |
| Minister Velyard hands Fuze his missions *(Wikipedia list; no place named)* | Not built | Wikipedia |

## Our interpretation (canon is silent)

- **Look.** Plastered timber-frame houses (calcite, cream and white terracotta; dark-oak frame; red tile roofs),
  grey stone walls and towers with slate-roofed watch rooms. Chosen to be clearly different from Dwargon (dwarven
  stone in a mountain) and Tempest (goblin timber and thatch). Colours: red and cream for the crown, blue and white
  for the Free Guild.
- **Size.** About 124 x 116 blocks including the king's road and the fields; walls 8 high; keep 14 high with four
  corner towers up to 32.
- **Free Guild hall.** A double-height hall under a slate gable roof: reception counter with a staff gate, two framed
  notice boards (quest board and bounty board) on the west wall, tables and a tavern nook, an archive of shelves, a
  mezzanine office. Banners are plain blue and white; the real Free Guild emblem is not used.

## Layout in short

South to north: king's road (z 93-115) between wheat fields -> town wall and south gate (z 90-92, two gate towers) ->
main street -> market square (x 34-90, z 54-80; fountain at 62,67; stalls; the guild hall on the east side, houses on
the west and south) -> merchant cross street (z 50-52) -> royal castle: ward wall and gatehouse (z 46-48),
courtyard, keep (x 50-74, z 10-28) with the throne hall below and a council chamber above. Orchards flank the
castle; the town wall closes the north.

## Points for other systems (blueprint coordinates)

Guild: door (92, 5, 67), counter x 102 z 60-78, quest board panel x 94 z 58-64 y 6-8, bounty board x 94 z 72-78,
branch master's desk (109, 11, 61). Castle: throne (62, 6, 12). Arrival (62, 5, 108). Placement:
design/builds/blumund.toml.

## Visual references

Looked at, not reused, for style: the Towns and Towers mod's "classic" and "tudor" structure sets (timber-frame
houses, fort and tower base plates). They are CC BY-NC-ND (no modification allowed), so none of their pieces are
placed; see CREDITS.md. Iron's Spellbooks' citadel and village pieces (All Rights Reserved) were viewed likewise.
