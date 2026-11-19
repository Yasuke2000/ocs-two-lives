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
| Rigurd is the goblins' leader under Rimuru (Goblin King) | Rimuru's own small house behind the longhouse; Rigurd still lives in the old goblin chief hut (Tensura's `goblin_chief_oak`) *(our choice)* | [Wikipedia, character list](https://en.wikipedia.org/wiki/List_of_That_Time_I_Got_Reincarnated_as_a_Slime_characters) |
| The goblins lived in shabby huts before; the new town replaces them gradually *(unverified)* | The goblins' old quarter in the north-east is built from Tensura's own goblin village pieces (see below), still lived in | memory of anime ep. 2–3 |
| Hipokute herbs (Rimuru's potions) are cultivated *(unverified for this period)* | Fenced herb patch beside the field | memory of the light novel |
| Hakurou trains the goblin riders; Souei scouts *(unverified details)* | Lookout tower in the north-west | our choice |
| Temperate primeval forest, clearings round Tempest | Rounded clearing (radius ~38) ringed by oak, birch, dark oak and spruce | [world.md](world.md) §J |

Not shown (deliberately, too late for "just after the ogres"): stone roads, sewers, the Tempest flag, Create
machinery, walls of stone. The palisade is only begun (west side, a south gate, low stakes where it stops).

## Tensura's goblin village (style reference, 18/11/2026)

Read from the Tensura 2.0.1.5 jar: `data/tensura/structure/goblin_village/{oak,birch,spruce,palm,jungle,acacia}/`,
pools in `worldgen/template_pool/goblin_village/<wood>/{main,streets,buildings}.json`, structures in
`worldgen/structure/villages/goblin_village/<wood>.json` (Jura is temperate forest: oak and birch sets).
Six identical layouts per wood; only the wood (planks, logs, fences, trapdoors, slabs) and the cloth colour change
(oak: white wool and banners, purple banner over the chief's door; birch: lime).

| Piece (`<wood>` = oak, birch, …) | Size x×y×z | What it is |
| --- | --- | --- |
| `goblin_start_<wood>` | 9×2×9 | Square of dirt path and grass, the village centre; jigsaws to streets and the chief hut |
| `goblin_<wood>_path_1..3`, `goblin_t_…`, `goblin_x_…`, `goblin_end_…_path_1..3` | 3×2×8, 6×2×9, 9×2×9, 3×2×4 | Streets: 3-wide dirt path frayed with grass and coarse dirt (terrain-matching) |
| `goblin_tent_<wood>` (weight 5, the common house) | 5×4×4 | A-frame of `tensura:thatch_stairs` down to the ground, `thatch_slab` ridge, plank back wall, wool front corners, one `tensura:thatch_bed`, trapdoor awning and a wall banner over the opening |
| `goblin_chief_<wood>` | 9×6×9 | Plank-walled hut 7×5 inside, roof of thatch stairs with top-slab ceilings and a `thatch_block` ridge, fence posts at the gable peaks, fence-gate "horns" on the ridge, fenced porch with open gates, banners (purple over the door), wool, carpet, flower pot, one chest with `LootTable: tensura:chests/<wood>_goblin_village` |
| `goblin_medical_tent_<wood>` | 7×5×10 | Long thatch A-frame, plank gable walls, 24 thatch beds (12 pairs) in two rows along a dirt-path aisle |
| `goblin_campfire_<wood>` | 5×2×7 | Lit campfire on dirt path, four single `<wood>_slab` seats two blocks out |
| `goblin_tower_<wood>` | 4×6×5 | Log post with fence legs, plank platform 3 up, open trapdoor railing, torch, a barrel with `LootTable: tensura:chests/goblin_tower` |
| `goblin_arch_<wood>` | 5×7×3 | Gate: two 6-high logs, trapdoors forming a point, a `skeleton_wall_skull` on the outer face |
| `goblin_spawn` | 1×3×1 | A jigsaw plus one embedded `tensura:goblin` entity (`PersistenceRequired: 0`, goblin club, `EvoState: 0`) |

- **Proportions.** Low: tents 3 high at the ridge, the chief hut 5. Everything sits on its own patch of ground
  (y 0 of each piece is grass/dirt/path), floors are bare earth; only the chief hut has plank walls.
- **Palette.** Tensura thatch (`thatch_block`, `thatch_stairs`, `thatch_slab`, `thatch_bed`), one wood
  (planks, log, fence, fence gate, trapdoor, slab), white or lime wool and banners, dirt path / coarse dirt / grass.
  No glass, no stone, no lights except the campfire and one torch on the tower.
- **Jigsaws and data blocks.** Every piece has jigsaws (final state `dirt_path`, `oak_planks` or `structure_void`);
  no data or structure blocks. Our copy replaces each jigsaw by its final state and drops the `structure_void` ones.
- **Loot.** Chief hut chest `tensura:chests/<wood>_goblin_village` (seeds, wheat, thatch, apples, sticks, …),
  tower barrel `tensura:chests/goblin_tower`.
- **Goblins.** Both ways: the pieces' jigsaws that target `tensura:goblin_village/goblin_spawn` (1 per tent, 3 in the
  chief hut, 5 in the sick tent, 2 at the campfire, 1 on the tower) pull in the `goblin_spawn` piece with an
  embedded goblin, and the structure JSON adds `spawn_overrides.creature: tensura:goblin` (1–2, weight 1) and
  an empty monster list over the whole village box. `tensura:goblin` is neutral: no prey targeting
  (the prey predicate is always false) and `InvalidateNeutralAttackTarget`, so it fights back only when hit;
  `EvoState ≥ 1` makes it a hobgoblin. It is a Tensura merchant entity. There is no separate hobgoblin entity id.

### How Tempest uses it

The goblins' old quarter (north-east) **is** a goblin village: `blueprints/tempest.py` pastes the actual pieces
from `blueprints/assets/goblin_village/` (copies of the oak and birch files above): `goblin_chief_oak` (Rigurd's
hut, door to the fire), `goblin_campfire_oak`, `goblin_arch_oak` where the quarter meets the town,
`goblin_medical_tent_birch` (the sick tent, where Rimuru's potions went after the direwolf fight *(our choice)*),
`goblin_tent_oak` ×2, `goblin_tent_birch`, `goblin_tower_oak`. The rest of the town borrows the palette: thatch roofs
are Tensura thatch stairs with a thatch-block ridge, house posts, lamp posts, the palisade and the south gate are oak,
and the green's cooking fire has slab seats like `goblin_campfire_oak`. The dwarf-built houses keep their own shapes.
`life/tempest.js` gives the chief chest and tower barrel their Tensura loot tables and summons eight hobgoblin
residents (Rigurd, Rigur, Gobta, Haruna and four unnamed) on the pieces' own goblin spawn points.

**Licence.** Tensura is "All Rights Reserved" (its `neoforge.mods.toml`). The copies in `blueprints/assets/goblin_village/`
and the pieces inside our generated structures redistribute its files in a public repo; ask the Tensura authors or
replace the copies with in-game `place template tensura:goblin_village/...` before relying on them.

## Placement

Tempest's arrival point (blueprint (45, 5, 57), the south edge of the village green at the signpost) is anchored at
**world (1720, 900)** on Lerfing's map: `design/data/anchors.toml` `[tempest]`, the middle of Jura (see [world.md](world.md#j-jura-tempest-federation-ジュラ・テンペスト連邦国)).
`TtlTempest.LANDMARK` in `life/tempest.js` reads it. Tempest is no longer the Life 2 world spawn: souls are reborn on the
rim at (1660, −100), 1,000 blocks north, and walk the road south.

**The ground under it** (`python -I tools/lerfing/jura_check.py`, exact columns of the imported world at 2-block steps,
terrain-fit margin 8 included; 19/11/2026):

| Footprint (box + margin) | x, z | Ground y p10 / median / p90 | Relief p90−p10 | Slope p95 / max | Water over ground | Off the median by more than 8 |
| --- | --- | --- | --- | --- | --- | --- |
| Early village (91², arrival 45, 57) | 1667..1773, 835..941 | 63 / 65 / 69 | 6 | 0.5 / 2.0 | 10.4 % (deepest 2) | 0 cut, 0 fill |
| Town (137², arrival 68, 68) | 1644..1796, 824..976 | 64 / 66 / 69 | 5 | 0.5 / 2.0 | 6.1 % (deepest 2) | 1 cut, 0 fill |
| City (191², arrival 95, 95) | 1617..1823, 797..1003 | 64 / 69 / 71 | 7 | 0.5 / 2.0 | 3.3 % (deepest 2) | 239 cut (the north-east corner, a knoll up to y 90), 3 fill |

Findings: the ground is buildable at all three phases (95 % of the early box lies within 4 blocks of the median; no
lava; slopes are gentle, the maximum 2.0 is a river bank). Two things the placer meets: the **pond** south of the arrival
(x 1657..1739, z 905..943, depth at most 2) cuts the early box's south-west corner (202 of 2,916 columns wet) and
is filled by the terrain fit and the repair under the box (`TtlTempest` uses the bed of the water as the floor, `keepWater: false`)
and the margin's water that touches the box is filled up to its surface, so a bank holds what lies beyond;
and the surface is **sand** (45 % of the early box, the rest grass, some gravel and clay) in `tensura:ancient_forest`
and `minecraft:beach` biomes: the blueprint lays its own grass and dirt ground layer, so only the 1:1 skirt and the
margin show Lerfing's sand.
