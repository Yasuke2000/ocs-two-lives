# Englassia: the capital Lura, the Freedom Academy and the Free Guild headquarters

Blueprint `blueprints/englassia.py` (structure `englassia_0..2`), placement `design/builds/englassia.toml`.
World position (14000 wide, landmark "Englassia capital (Lura): Freedom Academy, Free Guild HQ"): about x -2626, z -300, nation G.

## What canon says (verified)
Read through search results; the Fandom pages themselves answered HTTP 402 to our fetch tool, so only the quoted
facts are checked, not the full articles.
- Englassia is the most advanced human nation west of the Jura Forest before Tempest rises. The Council of the West and the
  Free Guild headquarters are stationed there, and the royal capital is large, **walled, with two gates**.
  (https://tensura.fandom.com/wiki/Kingdom_of_Englassia, via search snippet; our `design/lore/world.md` section G agrees)
- The Free Guild stands outside any country's system; branches test up to rank B, ranks B+ and above are examined at
  headquarters only. (https://tensura.fandom.com/wiki/Free_Guild)
- Class S, Shizu's students, belonged to the Freedom Academy; after Shizu, Rimuru became their teacher.
  (https://tensura.fandom.com/wiki/Class_S, https://tensura.fandom.com/wiki/Extra:_Rimuru's_Glamorous_Life_as_a_Teacher,_Part_2)
- The guild master of the Free Guild is Yuuki Kagurazaka (world.md; Free Guild headquarters in the capital).

## Our interpretation (canon gives no architecture)
Refined academic city. Stone brick walls with dark oak timber; the Academy under oxidised-copper (teal) roofs, the Guild
and the gate under slate. Blue banners for the city and the Academy, red for the Guild.
- **City wall and gate** (z 100-106): crenellated wall with buttresses, two gate towers with slate hip roofs, a 7 wide
  passage x 61-67 with a portcullis slot and hanging lanterns. The canon "second gate" is off the map.
- **Lura Square** (z 68-98): paved in three stones, a fountain with a lightning-rod finial, benches, two market stalls,
  rose beds, lamp posts; a west row of four half-timbered townhouses (2-3 floors, slate roofs).
- **Free Guild headquarters** (east side, x 86-122, z 66-98): the facade faces the square. A 31 x 17 hall with a gable
  end to the west, a columned portico with a balustrade, great doors (z 80-84), a gold-ringed emblem on the gable wall,
  red banners, two lower wings. Inside: reception counter, a quest wall of bookshelves, long tables, red carpet,
  chandeliers on timber beams. The emblem and the red are ours; the Guild has no canon heraldry we could verify.
- **Freedom Academy** (north, x 24-104, z 8-66): main hall (x 44-84, z 8-28, 13 high, copper roof), clock tower (x 58-70,
  open belfry with a bell, hip spire, gold finial, top y 57) over the grand entrance with a columned porch, two classroom
  wings (x 24-43 and 85-104) with desks and a stair to a reading floor with shelves, a walled lawn courtyard (x 44-84,
  z 29-62) with a fountain, hedges, four trees, flower beds, a cloister wall with a gate (z 63-65).
Everything inside is lit; chandeliers and lamp posts carry the light, `_citylib.Site.light()` adds lanterns where a
spot would still be dark.

## Visual references looked at (not copied)
Pieces of other mods in the pack were rendered only to get ideas: Towns and Towers (kaisyn village church, temple,
library, meeting-point pieces; CC BY-NC-ND 4.0, no changes allowed, so reference only), Iron's Spells 'n Spellbooks
(citadel, priest house; All Rights Reserved, reference only) and Tensura (dwarf library, plaza, wizard tower ruin).
None of their blocks are in these builds.
