# Lore pass, 18/11/2026: canon accuracy and tone

Owner request (decisions.md, 18/11 afternoon): "make sure our pseudo-lore-accurate vibes are right" and "make the City
of the Forgotten Dragon lore accurate". Scope: the City of the Forgotten Dragon (placement, look), the player-facing
text (story.toml, npcs.toml, quests, guide.toml, Voice of the World lines in the scripts, region and build titles) and
a sanity check of every build's position against canon geography. Branch `lore-pass`.

**Sources.** tensura.fandom.com still answers HTTP 402 to fetch tools and its BreezeWiki/antifandom mirrors sit behind
a bot wall (Anubis), so wiki facts come from search-engine extracts of the named pages; the Japanese Wikipedia article
(転生したらスライムだった件) and anibase character pages were readable. Every claim below names its source; "unverified"
means no readable source was found and the text is our choice.

## 1. City of the Forgotten Dragon

### Where canon puts it

| Claim | Source |
| --- | --- |
| "Milim Nava's domain, sitting south of Jura Forest and east of the Beast Kingdom of Eurazania" | [City_of_the_Forgotten_Dragon](https://tensura.fandom.com/wiki/City_of_the_Forgotten_Dragon) (extract) |
| The Great Ameld River runs from the Canaat foothills to the southern ocean and feeds "the fertile plains that make up Milim Nava's territory on the southern edge of the continent" | [Great_Ameld_River](https://tensura.fandom.com/wiki/Great_Ameld_River) (mirror extract) |
| Milim's territory is "at the eastern edge of the continent"; the temple in the capital "doubles as Milim Nava's castle" | [anibase: Middray](https://anibase.net/en/character/mOvy5/Middray), [Milim Nava](https://anibase.net/en/character/4dZxB/Milim-Nava) |
| Milim "忘れられた竜の都に居城を持ち、民から信仰の対象として崇められている"; Carrion becomes her vassal and commander after Walpurgis; Clayman's Jistav is taken over | [Japanese Wikipedia](https://ja.wikipedia.org/wiki/転生したらスライムだった件) |
| Relative to Jistav/Clayman: Clayman's army reached Eurazania through Milim's "controlled" domain, and Jistav is ruled jointly by Rimuru and Milim after Walpurgis (light novel vol. 6–7) | world.md §P, [Puppet_Nation_of_Jistav](https://tensura.fandom.com/wiki/Puppet_Nation_of_Jistav) |

So the capital belongs in the south-east corner: south of Jura (J), east of Eurazania (B), south-west of Jistav (P),
on the Ameld's lower reach. That is region M on our grid, and the fan-map pixel [2244, 1295] → (2462, 839) is in
the right place **except that it converts into the painted lake** (`~` in canon_map.txt; the 18/11 survey found 34 %
water everywhere within 160 blocks and water on most probe rays out to 220 blocks).

**What was wrong.** Version 2 surveyed from (2510, 575): dry, but 276 blocks *north* of the canon pixel, away from the
river and the lake, and only 2 chunks short of the river channel that runs north of the lake. Version 1's override
(1780, 684) was computed at the old 10,000-block width and stood next to Jura.

**What changed.** `design/builds/forgotten_dragon_city.toml` version 3 surveys from **(2340, 905)**, search 128: 170
blocks south-west of the canon pixel on the lake's western shore and the Ameld's south bank. In canon_map.txt every
chunk within 80 blocks is dry `M` (nearest `~`: the lake 100 blocks east, the river 60 blocks north); it stays 200
blocks east of Eurazania's border and 60 blocks north of the diagonal B/M line, so "south of Jura, east of Eurazania,
by the river" all hold. The Milim NPC spot is anchored to the build and moves with it. The old copy at (2510, 575)
stays in the staging world until that terrain is reset (the placer never removes an old version at a new spot).
`story-characters.md` §1.2 carried the stale (1780, 684); fixed.

### How canon describes it, and the build

| Canon | Build | Status |
| --- | --- | --- |
| Fewer than 100,000 dragonewts, "Dragon's Village" in the nation table ([Magic_Continent](https://tensura.fandom.com/wiki/Magic_Continent)) | Huts, granaries, no walls, no barracks | matches |
| No government; the Dragon Faithful run daily life; crops and goods are gathered at the **Central Temple** and "handed out evenly by the head priest"; Middray sets the contributions, Hermes is his equal ([Dragon_Faithful](https://tensura.fandom.com/wiki/Dragon_Faithful), anibase) | Stepped temple with a distribution hall (counter, barrels, hay) and two granaries | matches |
| The temple is Milim's castle (anibase, ja.wikipedia) | Milim's throne at the back of the temple hall, the NPC in front of it | matches |
| Milim took the dragonewts in; they built the city in her honour ([Milim_Nava](https://tensura.fandom.com/wiki/Milim_Nava)) | Pink banners (our colour) | matches |
| A flock of wyverns lives in the city ([Wyvern](https://tensura.fandom.com/wiki/Wyvern)) | nothing | **missing** (idea below) |
| River-fed fertile plains (Great_Ameld_River) | Savanna acacias, dry wheat, coarse dirt; the region palette had desert and `tensura:barren_land` | **palette fixed**: M is now savanna 3, savanna_plateau 2, plains 2, badlands 1, wooded_badlands 1, windswept_savanna 1, sunflower_plains 1; vegetation −0.4 → −0.2 (only ungenerated chunks change) |
| "Forgotten Dragon" | A dead ancient dragon's skull as the gate and ribs over the avenue | our interpretation; it resonates with the dragon that was Milim's friend (season 4 "Milim's Friend", LN vol. 13 flashback) but no source ties the name to bones |

Canon gives no architecture for the city at all (the anime shows the Dragon Faithful and Milim's hall, not a skyline),
so the stepped pyramid, the bones and the layout stay marked as our interpretation. `design/lore/forgotten_dragon_city.md`
rewritten with the sources above; `world.md` §M rewritten (location, Middray/Hermes, wyverns, river plains, the build spot).

## 2. Tone and facts in the player-facing text

Style targets: Life 1 is a grounded mortal medieval world (no Tensura words; checked: chapter 0 has none, the
generator refuses non-vanilla items); Life 2 is early-era Tempest (just after the ogres were named, before the Orc
War); the Voice of the World / Great Sage speaks in the canon register (《告。》 "Notice.", 《報。》 "Report.",
《解。》 "Answer.", 《確認。》 "Confirmed."); character voices follow the anime/LN.

### Fixed

| Where | Was | Now | Why (source) |
| --- | --- | --- | --- |
| `story.toml` Gobta (dark) | "Oh, that mark? Cool." | "Huh." | modern slang |
| `story.toml` Gobta (act 1) | "Hey, are you new?" | "Oh, are you new?" | casual modern opener |
| `story.toml` Leon | "not a place for tourists" | "no place for the idle. State your business, or leave." | modern word; Leon is cold and curt |
| `story.toml` Edmaris | "the kingdom of Falmuth is a busy kingdom" | "Falmuth has richer guests waiting at the door" | clumsy line |
| `story.toml` Luminous statue | "The Church's patron saint" | "The Church's god … Luminous" | the Western Holy Church worships the god Luminous (Luminism); she is a god to them, not a saint ([Western_Holy_Church](https://tensura.fandom.com/wiki/Western_Holy_Church)) |
| `story.toml` Treyni (light) | "a calamity stirs in its depths" | "a calamity is gathering above its waters" | Charybdis flies; it is fought in the air, not in the lake (anime season 1 ep. 20–22) |
| `story.toml` Milim | "I am Milim, I am very strong" / "He is my friend!" | "I am Milim Nava, the strongest Demon Lord there is … Make it interesting" / "Rimuru is my best friend!" | Milim introduces herself with her full name and her strength; Rimuru is her "best friend" (anime season 1 ep. 16) |
| `story.toml`, `npcs.toml` | Elen | Eren (display name; the id `elen` and the PNG stay) | the official site lists her as Eren ([ten-sura.com/character/eren](https://www.ten-sura.com/character/eren)); world.md and blumund.md already said Eren |
| `npcs.toml` Fuze | "or just to stare at the scar?" | "the paperwork?" | Fuze has no scar (official art) |
| `npcs.toml` Yuuki | "a mask pushed up on his forehead" | "looks far too young for his office" | Yuuki wears no mask; the mask is Shizu's. His youth is the canon remark |
| `npcs.toml` Razen | "A lean man" | "An old man" | Razen is an old mage (anime season 2) |
| `guide.toml` (main + life2) | "You are reborn … in Tempest" | "at the safe edge of the Forest of Jura, on the road between Tempest (south-west) and Dwargon (north-east)" | the arrival is on the rim at (271, −624) (`arrival.toml`), not in Tempest; the deadly core is an owner decision |
| `chapter_1` "The Town of Monsters" | "Monsters and humans live side by side" | "Goblins, wolves, dwarves and kijin" | no humans live in early Tempest (the first human visitors are Kabal's party, ep. 7) |
| `chapter_1` "Rigurd's Tribe" | "west of Tempest" | "north-west" | the landmark is at (−163, −234), chapter 7 already said north-west |
| `chapter_1` header | 3.89 blocks per pixel, gate at 310,−1060 | 5.45 blocks per pixel, gate 435,−1000 | stale comment |
| `chapter_3` "Kaijin's Old Smithy" | "exiled him on a false charge" | "after a sham trial" | Kaijin did punch Vesta; the trial was rigged, the charge was not false (ep. 5; chapter 8 already said sham trial) |
| `chapter_4` "Eat or Be Eaten" | the Orc Lord "devoured the dead of the battlefield and rose again" | "devoured the majin Gelmud, the schemer who had named him, and evolved into the Orc Disaster" | Geld evolves by eating Gelmud (ep. 15–16) |
| `chapter_7` "Hear Me, Direwolves" | "Tempest Star Wolves" | "Tempest Wolves" | the pack becomes Tempest Wolves at the naming; Star Wolf is Ranga's later evolution |
| `canon_regions.json` region names | "Land of Puppets Jistav", "Sorcerous Empire of Sarion", "Ulgracia" | "Puppet Nation of Jistav" (傀儡国), "Sorcerous Dynasty of Sarion" (魔導王朝), "Republic of Ulgracia" (共和国) | the Japanese subtitles already said so; names now match world.md and the wiki |
| Voice of the World, every script line | plain sentences | `TtlCorridor.canon()` prefixes "Notice." unless a line already opens with Notice/Report/Answer/Confirmed/Warning/Question; the death verdict opens with "Report.", the trial intro with "Notice."; the reborn/Exalted/registry/era broadcasts carry "Notice." | canon register of the Great Sage (《告。》); the Great Sage addon's own clips were already in that register |

### Checked and left as is

- Region subtitles (Japanese): all match the series' names (ジュラ・テンペスト連邦国, 武装国家ドワルゴン, 神聖法皇国ルベリオス,
  東方連合統一帝国, 獣王国ユーラザニア, 天翼国フルブロジア, 魔導王朝サリオン, 聖虚ダマルガニア, 黄金郷エルドラド, 傀儡国ジスターヴ).
- Build titles: all name the canon place; "Londo", "Lura" and "Lune" are fan-map capital names (world.md marks them unverified).
- Chapter 3 "ruled for three hundred years by the Hero King": Gazel is the third king, on the throne 300+ years; Dwargon
  itself is ~1,000 years old (world.md §D). Consistent.
- Chapter 2 "five hundred goblins", the naming, Kurobe at the anvil, Shuna's looms: match season 1 ep. 9–11.
- Kabal "rank B": correct. The Outcast Society, the Horde's envoy, the Supermassive Slime, the Gazel honour duel,
  the schematics theft are all labelled "our interpretation" in the quest text.
- The Walpurgis council as statues in Clayman's castle: in canon the Banquet is held in a venue Clayman only hosts
  (the castle raid runs *while* he is away), so this is an interpretation, already noted in clayman_castle.md.
- Gobta's boast lines, Shion blocking the door, Hakurou's stance remark, Souei's shadow line, Ramiris "smallest and
  cleverest", Guy "small one": in character.

## 3. Builds against canon geography

| Build | World | Canon check |
| --- | --- | --- |
| Sealed Cave (−256, −343) | north-west of Tempest, Jura | in the forest near the goblin village: correct (ep. 1–2) |
| Dwargon gate (435, −1000), Dragon's Nest (370, −2402) | north, Canaat range | correct (Dwargon at the foot of the Canaat mountains; the Nest on the highest peak) |
| Blumund — Londo (−1024, −120) | west of Jura, east of Falmuth/Englassia | correct: the small kingdom on Jura's border, the trade hub between Jura and the West |
| Marris — Falmuth (−1286, −1040); Ballachia (−1384, −212) | north-west / west | Falmuth west of Dwargon and north of Blumund: correct; Ballachia is a western city-state the grid merged into F |
| Englassia — Lura (−2626, −300) | far west | correct (the leading Western Nation, Free Guild HQ) |
| Lubelius — Lune (−3977, −659); Sacred Mountain (−4423, −1286) | far west, highlands | correct (Lubelius in the west, Luminous's seat) |
| Heaven Tower (−7507, 245) | far west, Barren Lands | correct (Dagruel) |
| El Dorado (−4808, 3240) | south-west continent | correct (Leon) |
| Frost Palace (−2435, −4314) | north, Ice Continent | correct (Guy) |
| Laura — Eurazania (1689, 1302) | south of Jura | correct; Milim's city lies east of it |
| Clayman's Castle (3693, −959) | north-east | Jistav between Jura, the Empire and Milim: correct; trades only with Dwargon and the Empire |
| Treyni's shrine (1988, −223) | east of the Ameld | correct (the dryads govern the eastern half) |
| City of the Forgotten Dragon | (2340, 905) | fixed (above) |

Nothing else moved.

## 4. Remaining bigger ideas (not done in this pass)

1. **Wyvern roost** at the City of the Forgotten Dragon: canon says a flock lives there. A perch ring on the temple's
   upper tiers and a few tame `tensura:wyvern` (if the entity exists in 2.0.1.5; verify in the dump) would show it.
2. **Middray and Hermes** as Easy NPCs at the Central Temple (talk only): the head priest who sets the contributions
   and his rival. Their lines belong in `story.toml` next to Milim's.
3. **Regenerate `canon_map.txt`** with the recovered political plate so the painted lake does not sit on the capital's
   pixel (or move the lake paint east by ~6 chunks); then the landmark can be used without an x/z override.
4. **Walpurgis venue**: the owner wants a Walpurgis hall as a duel arena; canon's banquet is not in Clayman's castle.
   A separate "Walpurgis Hall" build (hosted venue) would let the council statues leave the castle.
5. **Capital names** Londo / Lura / Lune are fan-map inventions; if the owner prefers canon-only names, the builds
   could be titled "Blumund — royal capital" etc.
6. **Discord lines** ("The Voice of the World: …") could carry the same "Notice." register as the in-game lines.
7. **Tempest's timeline**: chapter 8's Kaijin trade pact and chapter 12's "Laura rebuilt" happen later in canon than
   early Tempest; the quest text flags them as our interpretation, a short "era note" in the chapter intros would make
   the compression explicit.
