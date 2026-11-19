# Open creative tasks

The checklist for ChatGPT's side of the project. Tick a box (in the pull request that delivers it) when the item is merged. File locations and naming:
[README.md](README.md) section 3. Claude does everything technical (placement, generators, scripts, tests); Yasuke decides.

Legend: **[ ]** open, **[~]** started or partly done, **[x]** done.

## 1. World map drawing (the biggest task)

A **new, fully own Tensura world map** replaces Lerfing's imported map (owner decision, 19/11/2026).

- [ ] Draw the new world map. Brief: the geography relations in [world.md](world.md) (what lies north, south, east and west of Tempest, which nations border which, rivers, lakes, mountains, forests, Dwargon in the mountain, the Jura rings, the arrival on the forest edge, roads). Reference of the old world: [source-map/](source-map/README.md). **The spec for the deliverable (format, size, layers, scale) follows in the placeholder section at the end of this file.**
- [ ] A political map (nation borders and colours, see world.md section 4) and a terrain / relief map (heights, rivers, lakes, forests, deserts, snow).
- [ ] A small-scale map of Jura (Tempest, the rings, the lakes, the Sealed Cave, the goblin village, Treyni's grove, the Spirit Gate, the Dwarven Road) and one of the Canaat and Dwargon.
- [ ] A short note on every place whose position or terrain changes from the old map (it will not be many; the relations hold).

## 2. Concept art per place

One image and one note per place: `docs/art/places/<id>.png` + `<id>.md` ([art.md](art.md) section 2). The place pages hold the lore and the intent. Start with the places that the audit flags and the open builds; the order below is the suggested one. Tick when the image and the note are merged.


**Priority places**

- [ ] [Hidden ogre village](places/ogre_village_ruin.md) (`ogre_village_ruin`; audit: issue · medium)
- [ ] [Orc War battlefield](places/orc_camp.md) (`orc_camp`; audit: missing)
- [ ] [Tempest](places/tempest.md) (`tempest`; audit: issue · medium)
- [ ] [Treyni's grove](places/treyni_grove.md) (`treyni_grove`; audit: issue · medium)
- [ ] [Treyni's shrine](places/treyni_shrine.md) (`treyni_shrine`; audit: issue · medium)
- [ ] [Dwargon](places/dwargon.md) (`dwargon`; audit: issue · high)
- [ ] [Dwarf village on the road to Dwargon](places/dwarf_village.md) (`dwarf_village`; audit: issue · high)
- [ ] [Dwarven Arena](places/dwarven_arena.md) (`dwarven_arena`; audit: issue · medium)
- [ ] [Old goblin village](places/goblin_village.md) (`goblin_village`; audit: issue · high)
- [ ] [Sealed Cave](places/sealed_cave.md) (`sealed_cave`; audit: issue · low)
- [ ] [Life 2 arrival](places/arrival.md) (`arrival`; audit: OK)
- [ ] [Dragon's Nest](places/dragons_nest.md) (`dragons_nest`; audit: issue · low)

**All other places**

- [ ] [Wayfarers' camp on Jura's rim](places/wayfarers_camp.md) (`wayfarers_camp`)
- [ ] [Spirit Gate](places/spirit_gate.md) (`spirit_gate`)
- [ ] [Hinata's ambush west of Tempest](places/shizu_spawn.md) (`shizu_spawn`)
- [ ] [The Outcast on Tempest's south road](places/outcast_road.md) (`outcast_road`)
- [ ] [Dwargo](places/dwargo.md) (`dwargo`)
- [ ] [Gazel's throne room](places/dwargon_throne.md) (`dwargon_throne`)
- [ ] [Kaijin's smithy](places/kaijin_smithy.md) (`kaijin_smithy`)
- [ ] [Great Ameld River source](places/ameld_source.md) (`ameld_source`)
- [ ] [Great Ameld River mouth](places/ameld_mouth.md) (`ameld_mouth`)
- [ ] [Lake Siss](places/lake_siss.md) (`lake_siss`)
- [ ] [Lizardmen's stilt village](places/lizardmen_village.md) (`lizardmen_village`)
- [ ] [Lizardmen's caverns](places/lizardmen_caverns.md) (`lizardmen_caverns`)
- [ ] [Blumund](places/blumund.md) (`blumund`)
- [ ] [Ballachia](places/ballachia.md) (`ballachia`)
- [ ] [Englassia](places/englassia.md) (`englassia`)
- [ ] [Marris](places/marris.md) (`marris`)
- [ ] [Siltrosso](places/siltrosso.md) (`siltrosso`)
- [ ] [Holy City Lubelius](places/lubelius.md) (`lubelius`)
- [ ] [Sacred Mountain](places/sacred_mountain.md) (`sacred_mountain`)
- [ ] [Coleus](places/coleus.md) (`coleus`)
- [ ] [Heaven Tower](places/heaven_tower.md) (`heaven_tower`)
- [ ] [Morgdahl](places/morgdahl.md) (`morgdahl`)
- [ ] [Raja](places/raja.md) (`raja`)
- [ ] [Nostraille](places/nostraille.md) (`nostraille`)
- [ ] [Yuzalgh](places/yuzalgh.md) (`yuzalgh`)
- [ ] [Yggdonia](places/yggdonia.md) (`yggdonia`)
- [ ] [Filtwood](places/filtwood.md) (`filtwood`)
- [ ] [Ghastone](places/ghastone.md) (`ghastone`)
- [ ] [Rostia](places/rostia.md) (`rostia`)
- [ ] [Sainte Malukshure](places/sainte_malukshure.md) (`sainte_malukshure`)
- [ ] [Galut / Ulgr Nature Park](places/ulgr_nature_park.md) (`ulgr_nature_park`)
- [ ] [Elmine](places/elmine.md) (`elmine`)
- [ ] [Jia](places/jia.md) (`jia`)
- [ ] [Laura](places/laura.md) (`laura`)
- [ ] [City of the Forgotten Dragon](places/forgotten_dragon_city.md) (`forgotten_dragon_city`)
- [ ] [Clayman's Castle](places/clayman_castle.md) (`clayman_castle`)
- [ ] [Amrita](places/amrita.md) (`amrita`)
- [ ] [Nasca](places/nasca.md) (`nasca`)
- [ ] [Great Holy Mountain](places/great_holy_mountain.md) (`great_holy_mountain`)
- [ ] [Golden City of El Dorado](places/el_dorado.md) (`el_dorado`)
- [ ] [El Dorado volcano](places/el_dorado_volcano.md) (`el_dorado_volcano`)
- [ ] [Frost Palace](places/frost_palace.md) (`frost_palace`)
- [ ] [Blumund road camp at Jura's edge](places/blumund_road.md) (`blumund_road`)
- [ ] [Englassia road post](places/englassia_road.md) (`englassia_road`)
- [ ] [The old well on the Blumund road](places/old_well.md) (`old_well`)
- [ ] [The abandoned rookie camp](places/rookie_camp.md) (`rookie_camp`)

## 3. Blueprints for builds

Blueprint = a Python file in the format of [builds.md](builds.md), or a plan sketch and block brief that Claude turns into one.

- [ ] **`ogre_village_ruin`**: the hidden ogre village, the kijin homeland the orcs burned. A burnt village of several ruined buildings in forest (see the [place page](places/ogre_village_ruin.md)); today only a single burnt tower stands on a bare hill. Suggested size: 60 to 100 blocks wide, set in the forest edge of a hill, with a ground that blends into the terrain. Canon is silent on the layout; mark our interpretation.
- [ ] **`orc_camp`**: the Orc Lord's war camp at the Lake Siss marsh, south-east of the lake ([place page](places/orc_camp.md)). A sprawling camp of crude tents, pens, bone and skull banners and a command pavilion; it must work on marsh ground (some water is fine). Replaces Tensura's jigsaw stand-in, which failed to place.
- [ ] Small camps: the wayfarers' camp at the arrival, the rookie camp, the old well, the Blumund and Englassia road camps.
- [ ] Better looks for builds flagged in the audit ([builds.md](builds.md) section 5), above all flat-pad builds (Dragon's Nest, Sealed Cave, Great Holy Mountain, Sacred Mountain): ideas for an irregular silhouette so the build grows out of its site.

## 4. Lore consistency pass

- [ ] Read `design/lore/*.md`, `design/data/story.toml`, `design/data/npcs.toml` and the world text against [world.md](world.md) and the canon. Report contradictions (names, who lives where, directions, distances, dates), facts marked unverified, and interpretations that are not marked as ours. The previous pass is [`design/lore/lore-pass-2026-11.md`](../../design/lore/lore-pass-2026-11.md) (its section 4 lists ideas that are still open: wyvern roost, Middray and Hermes as NPCs, capital names, era notes for the Tempest timeline).
- [ ] Deliver as `docs/chatgpt/drafts/lore-pass.md` (a table: file, line or place, problem, suggested fix, source). Claude applies the fixes; lore pages themselves (`design/lore/<id>.md`) may be edited directly, keeping the "Canon / What we built / Sources" shape.
- [ ] Make the lore of the 58 places consistent with the new world map once it exists (directions and distances).

## 5. Story chapters 11 to 13

The Life 2 saga chapters exist as quest data: [`chapter_11_mask_and_blade.toml`](../../design/quests/chapter_11_mask_and_blade.toml), [`chapter_12_puppet_master.toml`](../../design/quests/chapter_12_puppet_master.toml), [`chapter_13_harvest_festival.toml`](../../design/quests/chapter_13_harvest_festival.toml); canon sources and design notes in [`design/quests.md`](../../design/quests.md) ("Life 2 saga, chapters 11-13") and `design/architecture/story-characters.md`.

- [ ] Review the text of the three chapters (titles, `lore` lines, quest `text`): tone, canon accuracy, clarity, a consistent voice (the Voice of the World speaks in a short "Notice." register), the two Oath paths (light and dark) given equal care.
- [ ] Write improved EN text for each quest and a chapter intro; keep every quest `key`, `deps`, `tasks` and `rewards` untouched (those are Claude's).
- [ ] Add NL text for the same (task 6).
- Deliver as `docs/chatgpt/drafts/chapter_<nn>.md`: for each quest key a table row `key | field | current EN | new EN | NL`. Claude applies it to the TOML and regenerates the quest book.

## 6. NL localisation (Dutch, Flemish register)

The in-game text is English only today (quest book, NPC dialogue, guide book); the player wiki exists in EN and NL ([`docs/wiki/en`](../wiki/en/index.md), [`docs/wiki/nl`](../wiki/nl/index.md)).

- [ ] Review and polish the NL wiki pages against the EN ones (they must stay in step).
- [ ] Translate the quest chapters (`design/quests/*.toml`: `title`, `subtitle`, `lore`, `text`), `design/data/story.toml`, `design/data/npcs.toml` and `design/data/guide.toml` player text, starting with the Life 2 chapters 1 to 4 and 11 to 13.
- [ ] Translate the place lore summaries of [world.md](world.md) section 5 for the NL wiki.
- Deliver as `docs/chatgpt/drafts/nl/<source file stem>.md` with rows `key | EN | NL` (the key as in the source file). Claude adds the localisation to the quest generator and the game. Register: Flemish Dutch (Vlaams-Nederlands), informal "je/jij", game terms as in the NL wiki (`docs/wiki/nl/`); keep proper names (Rimuru, Tempest, Dwargon) and Tensura terms unchanged.

## 7. Nicer NPC skins

- [ ] Replace the generated generic looks with hand-made skins, archetype by archetype ([art.md](art.md) section 4, prompts in [`docs/art/npc-skin-prompts.md`](../art/npc-skin-prompts.md), contact sheet [`docs/previews/npc_skins.png`](../previews/npc_skins.png)). Suggested order, the ones players meet first: `guild_rookie`, `guild_veteran`, `merchant`, `dwarf_trader`, `dwarf_warrior`, `dwarf_smith`, `luminist_cleric`, `holy_knight`, `goblin`, `hobgoblin`, `kijin`, `tempest_citizen`, `lizardman`, `outcast`.
- [ ] Named characters (28 roster skins, [`design/lore/skins.md`](../../design/lore/skins.md)): proposals for a better look of the main cast (Rimuru, Benimaru, Shuna, Shion, Souei, Hakurou, Kurobe, Rigurd, Kaijin, Gazel, Hinata).

## 8. World map deliverable spec: follows from design/architecture/own-world.md (in progress)

> **Placeholder.** The architect is writing `design/architecture/own-world.md` now (the file does not exist yet). Claude will fill this section in once it is
> decided: file format, size and scale of the drawing, layers, how the drawing becomes a world, naming and review steps. Until then work only on the preparation tasks of
> section 1 (briefs and notes), not on the final drawing.
