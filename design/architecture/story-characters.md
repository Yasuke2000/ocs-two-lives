# Story, characters, parties and wild bosses: architecture

18/11/2026 · for the implementation agents. Builds on `design/architecture/sprint3-4.md` (its §0 conventions apply
unchanged), `bosses/boss.js` (WP2), `rep/rep.js` (WP3), `karma/karma.js`, `economy/guild_npcs.js` + `tools/gen_npcs.py`
(Easy NPC presets), `events/director.js` (WP7), `tools/gen_quests.py` and the canon builds placed on 18/11/2026.
Everything below was read from the jars in the OCs Prism instance, the pack configs or the repo; **verify in game**
marks what an agent must confirm first. Owner request of 18/11/2026: (1) mods first, references always; (2) one
overarching questline with parties and a good/evil choice; (3) every boss has a definite place and condition **and**
a rare wild spawn.

## 0. What was verified, and the rules that follow from it

| Fact | Source | Consequence |
| --- | --- | --- |
| Tensura 2.0.1.5 ships these **living canon entities**: `tensura:shizu`, `hinata_sakaguchi`, `gazel_dwargo`, `folgen`, `kyoya_tachibana`, `kirara_mizutani`, `shogo_taguchi`, `mai_furuki`, `mark_lauren`, `shin_ryusei`, `shinji_tanimura`, `falmuth_knight`, `sissie`, `orc_lord`, `orc_disaster`, `ifrit`, `charybdis`, `supermassive_slime`, `elemental_colossus`, `akash`, `sylphide`, `undine`, `war_gnome`, plus races `dwarf`, `goblin`, `lizardman`, `direwolf`, `lesser/greater/arch_daemon` | `assets/tensura/lang/en_us.json` (`entity.tensura.*`), `textures/entity/otherworlder/*.png`, `data/c/tags/entity_type/bosses.json` | Never build an Easy NPC for a character that has an entity. Use the entity (fight) or the entity as a **statue** (talk; the throne-Gazel pattern of `life/dwargon.js`). |
| Tensura marks as bosses (`#c:bosses`): akash, charybdis, elemental_colossus, ifrit, orc_lord, orc_disaster, sylphide, undine, war_gnome, gazel_dwargo, hinata_sakaguchi. Shizu is **not** a boss there (she is in `#c:capturing_not_supported`). | jar tag files | Boss framework scaling/untame logic applies to all of them the same way (it keys on our `ttl.boss` tag, not Tensura's). |
| NEB 2.0.0.3 ships `tensura_neb:rimuru_ogre_fight` ("Rimuru Tempest"), `rimuru_clone`, `veldora` ("Veldora Tempest"), `luminous_valentine`, `carrion`. | `assets/tensura_neb/lang/en_us.json` | Rimuru, Veldora, Luminous, Carrion are fights, never Easy NPCs. |
| Tensura spawns otherworlders by itself (`OtherworlderSpawnDistribution`, a `chance` field) and NEB turns an otherworlder spawn into Luminous/Rimuru/Carrion with `luminousChance/rimuruChance/carrionChance` — all three are **0** in `pack/config/tensura/neb_config.toml`. Tensura has no config for the otherworlder chance itself (nothing in `pack/config/tensura/*.toml`; the class holds it). | jar classes, pack config | That is how Shizu "spawns naturally" today. The redesign (§5) blocks it and rolls wild spawns ourselves so credit, caps and announcements are ours. |
| Tensura runs its own Gazel/Hinata boss fights in `tensura:boss_area` through `BossFightStorage` + warp pads. | `data/tensura/dimension/boss_area.json`, `storage/boss/*` | We never use it: arenas stay in the overworld. The throne Gazel is tame and NoAI so it never starts one (**verify in game** that a hit from a dark-path player cannot trigger `BossFightStorage`). |
| Easy NPC 7.19.0 `SkinType` = `DEFAULT, CUSTOM, PLAYER_SKIN, SECURE_REMOTE_URL, INSECURE_REMOTE_URL, RESOURCE_LOCATION`. Presets carry `SkinData:{Type:"PLAYER_SKIN",Name:"<mc name>"}` or `{Type:"SECURE_REMOTE_URL",URL:"https://…"}` (the mod's own `default_preset/humanoid_slim/remote_skin.npc.snbt` does it) — no PNG needs shipping. URL skins are gated by `feature.URL_RESOURCE=CREATIVE_PLAYER` in `pack/config/easy_npc/security.cfg`; `remote_texture.cfg` can block private addresses. `CUSTOM` PNGs live in `config/easy_npc/skin/<type>/` **on every client**. | jar `SkinType.class`, `SecurityConfig.class`, pack `security.cfg`, Easy NPC wiki (Skins, Preset) | Skin policy in §1.3. |
| FTB Teams 2101.1.12: `/ftbteams party create|invite|decline|join|leave|kick|transfer_ownership|settings|allies`, `/ftbteams teamstage …`, `max_party_size` (currently **0** = unlimited in `pack/config/ftbteams-server.snbt`), API `FTBTeamsAPI.api().getManager().getTeamForPlayer(p)`, events `PlayerJoinedPartyTeamEvent`, `PlayerLeftPartyTeamEvent`, `PlayerChangedTeamEvent`, `TeamStagesHelper`. | jar lang + class list, FTB-Teams GitHub `FTBTeamsCommands.java` | Parties are FTB party teams (same object the nations package will use). |
| FTB Quests 2101.1.39 progress is **per team** (`TeamData` keyed on the FTB team id, saved as `data/ftbquests/<teamId>.snbt`); a solo player has a personal team. Task `gamestage` has `team_stage` (per-team stages); rewards include `command`, `gamestage` (with silent/remove), `toast`, `choice`. Our generator only emits `item/xp/xp_levels` rewards and `team_stage=False`. | jar class list + lang, FTB-Quests GitHub `TeamData.java`; `tools/gen_quests.py` | Shared quest progress needs **zero code**. The generator gets `stage` and `command` rewards (WP-S5). |
| KubeJS `player.stages` are per player. A `gamestage` task with `team_stage=false` is checked for every online member; one member holding the stage completes it for the team (FTB `BooleanTask` semantics) — **verify in game**. | FTB Quests source pattern | Branch stages must be identical for every party member (§3, §4). |
| Boss credit today: whoever the kill objective credits, hit it, or stood in `range` for `presence_secs`, and is in `range` at the death (`TtlBoss.finish`). `requires` gates on `ttl.defeated.<id>`; `block_natural` cancels natural/chunk/structure/spawner spawns except `natural_allow` (Shizu). | `bosses/boss.js`, `bosses.toml` | §4.3 extends `finish`; §5 replaces `natural_allow`. |
| Named canon goblins (Rigurd, Rigur, Gobta, Haruna) already stand in Tempest as `tensura:goblin` EvoState 1 with `CustomName` (`TtlTempestExtras.residents`). Fuze and two receptionists are Easy NPC `custom` presets with built-in skins (KNIGHT_01 / SECURITY_01). | `life/tempest.js`, `npcs.toml` | The cast (§1) reuses both patterns; the Tempest goblins get a dialog hook instead of a second NPC. |
| Dark path: `ttl.karma.dark` + stage `ttl.tier.dark`, prefix "Fallen" (`karma.toml [dark]`). Reputation API `TtlRep.get/add/set/band/seed/sync/renown/addRenown`; `renown.stage = {}` is an empty hook. Legendary ceiling `max_holders = 10` ("the Ten Great Demon Lords"), absorb skills list and `min_ep_ratio` in `skills.toml`; `absorb/` and `nations/` are **not built yet**. | `karma.js`, `rep.js`, `factions.toml`, `skills.toml`, script tree | §3.4 ties in; absorption/nations are dependencies to stub, not to build here. |

Rules: **(R1)** a character is an entity if a mod has one; an Easy NPC only otherwise. **(R2)** every fight is a
`[[boss]]` in `bosses.toml` on an existing entity type, one boss per entity type (kill objectives are per entity).
**(R3)** story state lives in `ttl.story.*` persistentData + `ttl.path.*` stages, mirrored to scoreboard `ttl.path`;
quests gate on stages only. **(R4)** no skin PNG ships unless it is ours (drawn for the pack) or its page shows a CC
licence that allows redistribution; otherwise built-in Easy NPC variants or `PLAYER_SKIN` by Minecraft name.

## 1. Verified roster

### 1.1 Fights (entity exists: Tensura / NEB) — all are `[[boss]]` entries; anyone may fight them on any path

| Character | Entity (verified) | Tier | Canon place (build / landmark, world x z) | Light path role | Dark path role | Fight condition (fixed spawn) | Wild spawn (per-day chance when a Life 2 player is in a listed region; §5) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Geld, Orc Lord | `tensura:orc_lord` | 1 | Orc camp landmark `orc_camp` (1106, 539) | Enemy of the lizardmen alliance | Rival king you must devour to lead the Horde | Quest altar at the camp (ch.9); no `requires` | 3 % in J, W, V |
| Supermassive Slime | `tensura:supermassive_slime` | 1 | Sealed Cave build (`sealed_cave`, landmark) | Veldora's leftover magicule beast | Same | Altar in the cave antechamber (ch.7 side quest) | 3 % in J |
| Ifrit (in Shizu) | `tensura:ifrit` | 2 | Tempest green (0, 0, radius 48) | The spirit that took Shizu: free her | Take Ifrit's flame for yourself | After `ttl.defeated.shizu`: Shizu's fight ends by summoning Ifrit (phase hook, ch.11) | 1 % in M (badlands/volcano), E |
| Shizu, Flame Tyrant | `tensura:shizu` | 2 | Tempest green (0, 0) | Save her (ally memory: her mask) | Kill the masked hero | Ch.11 trigger at Tempest (both paths) | 1 % in J (dark path ×1) |
| Geld, Orc Disaster | `tensura:orc_disaster` | 2 | Orc War battlefield marsh (1106, 539, radius 64) | Final battle of the Orc War | Your evolved rival, or your champion after you take the Horde | After `ttl.defeated.orc_lord` (ch.9 finale) | 1 % in W, V |
| Mimic Echo | `tensura_neb:rimuru_clone` | 2 | Spirit Dwelling (`ttl:spirit_domain`, 0 64 0) | Ramiris' test of the soul | Same | Spirit Dwelling pedestal (ch.12 side) | 0.5 % in J (storm weather only) |
| Folgen | `tensura:folgen` | 2 | Tempest south gate (0, 40) during the Falmuth invasion | Falmuth's field commander you repel | Your commander when you march with Falmuth (you still may fight him) | Invasion event (ch.11); **verify** Folgen's canon side (the mod files him under otherworlders) | 0.5 % in F, R |
| Kyoya Tachibana | `tensura:kyoya_tachibana` | 2 | Marris (`marris`, −920 −745) parade ground | Falmuth's otherworlder you duel | Sparring partner, then rival | Marris plaza altar (ch.11) | 0.5 % in F |
| Shogo Taguchi | `tensura:shogo_taguchi` | 2 | Marris | same | same | Marris (ch.11) | 0.5 % in F |
| Kirara Mizutani | `tensura:kirara_mizutani` | 2 | Marris | same | same | Marris (ch.11) | 0.5 % in F |
| Charybdis | `tensura:charybdis` | 3 | Over Lake Siss (635, 145, y surface + 20, radius 96) | The calamity Milim hits; you finish it | You wake it for Clayman, then must survive it | Ch.10 ritual at the lake shore (both) | 0.3 % in W, J (announced server-wide) |
| Gazel Dwargo | `tensura:gazel_dwargo` | 3 | Dwargon throne room (435, −1106, radius 40; the throne Gazel is a separate tame NPC, tag `ttl_gazel`) | Ally and quest giver; "the King's test" is an honour duel (no rep loss) | Regicide: dwargon rep −60 (Hostile) | Statue dialog "Challenge the King" (ch.8); dark: no dialog needed, attack the throne statue → script swaps statue for the boss (**verify** interaction hook) | 0 % (a king does not wander; knob stays) |
| Hinata Sakaguchi | `tensura:hinata_sakaguchi` | 3 | Road Blumund→Tempest (−400, −60, **verify** terrain) for the ambush; statue in Lubelius Hall of the Holy Knights | Rival turned ally after the duel; unlocks the True Hero line | Hunts you as a monster: she comes to you (wild ×3) | Ch.11 after `ttl.defeated.shizu` (both) | 0.5 % in F, R, G, L (dark path ×3) |
| Carrion | `tensura_neb:carrion` | 3 | Laura (`laura`, Eurazania capital) lion hall | Sparring for the alliance; then quest giver (via statue) | Beast Lord you must break for Clayman | Laura hall altar (ch.12) | 0.3 % in B |
| Rimuru Tempest | `tensura_neb:rimuru_ogre_fight` | 3 | Tempest green (0, 0) | "Spar with the Lord of Tempest" (title) | "The slime must fall" (Falmuth route) | `requires = ["shizu"]` as today (ch.11 finale) | 0 % |
| Clayman (proxy) | `tensura:arch_daemon` named "Clayman, the Marionette Master" | 3 | Clayman's Castle (`clayman_castle`, 2930 −685) keep | Storm the castle at Walpurgis | Serve him, then betray him for his seat | Castle keep altar (ch.12) — proxy because no mod has Clayman; **owner decision O3** | 0.2 % in P |
| Luminous Valentine | `tensura_neb:luminous_valentine` | 4 | Lubelius cathedral crypt (`lubelius`, −3977 −659) | Secret patron of the Church: her blessing (True Hero) | The vampire queen whose seat you want | Crypt altar; `requires = ["hinata_sakaguchi"]` (ch.12) | 0.1 % in L, night only |
| Veldora | `tensura_neb:veldora` | 4 | Sealed Cave sealed chamber | "Veldora's Trial": the storm dragon tests you | "Bind the Dragon" | Chamber altar; `requires = ["charybdis"]` (ch.13) | 0.1 % in J, thunder weather only |
| Dagruel (proxy, later) | `tensura:elemental_colossus` | 4 | Damargania (V) — no build yet | — | — | Not in this sprint; wild only | 0.2 % in V |
| Greater spirits | `tensura:sylphide`, `undine`, `akash` | 2 | Spirit Dwelling | Ramiris' guardians (light: trials) | Same | Pedestal (ch.12 side) | 0 % |

Tier, hp, phases, rewards, cooldown of the existing eleven bosses stay as in `bosses.toml`; the new rows (ifrit arena,
folgen, kyoya, shogo, kirara, clayman proxy, spirits) get T2 numbers (`hp_mult 3, per_player 0.75, range 56,
cooldown 48 h`) unless noted.

### 1.2 Cast without a mod entity → Easy NPC (talk only; a fight, if any, is a **proxy boss** on a distinct entity)

| Character | Easy NPC kind / look (R4) | Place (build coords are blueprint offsets like `npcs.toml`) | Light path | Dark path | Fight |
| --- | --- | --- | --- | --- | --- |
| Rigurd | existing named `tensura:goblin` (Tempest residents) + dialog hook | Tempest, chief hut | Quest giver ch.7 (the Oath), ch.9 | Refuses you after the dark Oath; the Outcast contact replaces him | none |
| Gobta | existing named goblin + hook | Tempest campfire | Comic side quests (ch.7) | Same (he does not care) | none |
| Benimaru | Easy NPC humanoid, DEFAULT variant until an own skin exists | Tempest council longhouse | War leader: Orc War + invasion quests | Enemy commander (invasion variant) | none (no entity; Kijin fight = **O4**) |
| Shuna | Easy NPC humanoid_slim | Tempest weaving hut | Hand-in quests (cloth, potions) | Same, only while Tempest ≥ Unfriendly | none |
| Shion | Easy NPC humanoid_slim | Tempest, Rimuru's house | Bodyguard quests | Blocks the dark player at Hostile | none |
| Souei | Easy NPC humanoid | Tempest lookout tower | Scouting quests (locations) | Same | none |
| Hakurou | Easy NPC humanoid | Tempest green | Training quests (`ability` tasks) | Same | none |
| Kaijin (+Garm, Dold, Mildo) | Easy NPC humanoid (dwarf scale `ScaleY 0.8`) | Tempest forge / Dwargon smithy (423, −1084) | Forge hand-ins, Gazel audience | "Steal the forge schematics" (dark ch.8) | none |
| Treyni | Easy NPC humanoid_slim | Treyni shrine (1988, −223) | Dryad quests, Charybdis warning | Warns, then silent | none |
| Gabiru | `tensura:lizardman` named statue + hook | Lizardmen caverns (926, 398) | Comic ally | Enemy: proxy boss "Gabiru" on `tensura:lizardman` T1 (dark ch.9) | proxy |
| Milim Nava | Easy NPC humanoid_slim | City of the Forgotten Dragon (1780, 684) | Friend; Charybdis scene; Walpurgis seat | Clayman's "controlled" Milim: talks, never fights | **none** (unbeatable by design) |
| Fuze | exists (`npcs.toml`) | Blumund guild hall | Contracts + Act III intel | Same (the Guild trades with anyone above Hostile) | none |
| Kabal, Elen, Gido | Easy NPC ×3 | Blumund guild hall floor | Shizu's story (ch.11 opener) | Same | none |
| Yuuki Kagurazaka | Easy NPC humanoid | Englassia Free Guild HQ (−2626, −300) | Grandmaster: Hinata quests | Secret employer of the dark path (Act VI) | none (later era) |
| King Edmaris + Razen | Easy NPC ×2 | Marris royal castle | Enemy court (talk: ultimatum) | Quest givers of the Falmuth route (ch.11) | Razen fight = **O4** |
| Luminous (human guise "Louis") | Easy NPC humanoid | Lubelius cathedral | Church patron dialog | Same | fight is the NEB entity (§1.1) |
| Carrion (talk) / Frey / Guy / Leon / Ramiris / Dagruel | Easy NPC statues at Laura / Fulbrosia (no build) / Frost Palace (no build) / Golden City (no build) / Spirit Dwelling / Damargania | Walpurgis council members (ch.12 talk scene at Clayman's castle: all seated as Easy NPCs) | — | — | Ramiris: none; others later |

### 1.3 Skin policy (owner request 1, verified against Easy NPC 7.19)

1. **Default now:** built-in Easy NPC variants (as Fuze/receptionists) + coloured name. No licence question.
2. **Own skins (recommended for the main cast):** PNGs drawn for the pack under `pack/kubejs/assets/ttl/textures/npc/<id>.png`,
   referenced as `SkinData:{Type:"RESOURCE_LOCATION", …}` — KubeJS assets ship to every client, so no per-client
   `config/easy_npc/skin/` copy is needed. **Verify in game** the exact `SkinData` field for the resource id
   (export a preset from the config UI after choosing a resource-location skin and copy its SNBT).
3. **`PLAYER_SKIN` by Minecraft name:** no file, Mojang serves it, allowed by the mod; but the skin follows that
   account's whims and no Tensura-named accounts were verifiable (NameMC/PMC/Skindex all refuse automated access —
   research 18/11/2026). Use only for accounts the owner controls (an owner alt wearing an own-drawn skin is the
   cleanest way to "host" a skin without shipping it).
4. **Remote URL skins:** possible (`SECURE_REMOTE_URL`), gated by `feature.URL_RESOURCE`; **not recommended**: hot-links
   a third party's upload (Skindex/PMC pages are All Rights Reserved unless a CC badge is shown; terms unreadable by
   script), breaks when the upload moves, and every client downloads it.
5. Never copy a PNG from Planet Minecraft, Skindex, NameMC or minecraft.how into the repo (minecraft.how ToS grants
   view access only; PMC default is All Rights Reserved). No Tensura skin pack with a permissive licence exists on
   Modrinth/CurseForge (all 98 "tensura" projects are All-Rights-Reserved mods/modpacks).
6. `npcs.toml` gets `skin = "KNIGHT_01" | { resource = "ttl:textures/npc/benimaru.png" } | { player = "<name>" }`;
   `gen_npcs.py` writes the matching `SkinData`. `tools/validate.py` fails on `{ url = … }`.

## 2. The overarching story

One main line, seven acts, mapped on the canon arc. Chapters 0–6 exist; new chapters are 7+. Every act has a shared
spine (visible to all), a **light lane** (stage `ttl.path.light`), a **dark lane** (`ttl.path.dark`) and its fights
(open to everyone: a fight quest only gates on `ttl.defeated.<id>`, never on a path). Hidden until deps complete.

| Act | Chapter(s) | Canon beat | Spine (both) | Light lane | Dark lane | Fights unlocked |
| --- | --- | --- | --- | --- | --- | --- |
| I. The Forest Awakens | 1 Reborn, 2 Tempest Rises (exist) + **7 Crossroads** | Goblins and direwolves, Shizu's arrival foreshadowed | Reach Tempest, help the town ("Tempest Stands"), then **the Oath** (§3.1): Rigurd (light) or the Outcast contact (dark) | "Rigurd's Trust": tempest +20 | "The Outcast's Mark": outcast +20, orc_horde +15, tempest −20; a Fallen soul (`ttl.tier.dark`) sees this lane pre-lit | Supermassive Slime (cave altar) |
| II. The Armed Nation | 3 (exists) + **8 The King's Test** | Dwargon, Kaijin's exile, Gazel | Audience at the throne (exists) | "Honour duel": Gazel boss via statue dialog, no rep loss, dwargon +15, Kaijin joins Tempest quests | "Regicide" (dwargon −60 → Hostile) or "Steal the schematics" (Kaijin hand-in, dwargon −20, outcast +10) | Gazel Dwargo |
| III. The Orc War | 4 (exists) + **9 Two Hundred Thousand** | Lizardmen alliance, Geld | Scout the camp, hold the line (exist) | Ally Gabiru; kill the Orc Lord; Benimaru's war council; finale Orc Disaster | "Devour the King": defeat the Orc Lord to lead the Horde (orc_horde +40), raid the caverns (proxy Gabiru), finale Orc Disaster "your champion turns on you" | Orc Lord, proxy Gabiru (dark), Orc Disaster |
| IV. Calamity | **10 The Whirlpool** | Charybdis, Milim | Treyni's warning; the lake ritual | Milim arrives (Easy NPC scene); you finish Charybdis; tempest +15, Milim becomes a quest giver | You wake Charybdis for Clayman (Yuuki's letter); survive and kill it anyway; outcast +20 | Charybdis |
| V. The Holy Knight | **11 Mask and Blade** | Shizu/Ifrit, Hinata's ambush, Falmuth invasion | Kabal's trio tell Shizu's story; Shizu comes to Tempest (both) → Ifrit; then Hinata | Repel the Falmuth invasion (event: knights + Folgen); duel Hinata on the road; "Spar with Rimuru"; holy_church +10 after the duel (she listens) | March with Falmuth (Edmaris/Razen quest givers): Marris duels (Kyoya/Shogo/Kirara), Hinata hunts you (wild ×3), "The slime must fall" (Rimuru); tempest −40, falmuth +30 | Shizu, Ifrit, Folgen, Kyoya, Shogo, Kirara, Hinata, Rimuru |
| VI. Walpurgis | **12 The Puppet Master** | Clayman, Carrion, Luminous, the council | The council scene at Clayman's castle (all Demon Lords as statues) | Storm the castle; Carrion's sparring → alliance; Luminous' blessing after Hinata | Serve Clayman (Carrion must break), then betray him for the seat; Luminous' crypt for her seat | Clayman proxy, Carrion, Luminous, Mimic Echo + spirits (side) |
| VII. Demon Lord / True Hero | **13 Harvest Festival** | Awakening, Veldora freed | Veldora's Trial at the Sealed Cave | **True Hero**: Veldora + Luminous blessing → `ttl.story.hero`; a Legendary draw from the light pool if a holder place is free | **Demon Lord**: Veldora bound + Clayman's seat → `ttl.story.demon_lord`; a Legendary draw from the dark pool if a place is free (the Ten) | Veldora |

Design notes.
- **Both lanes are complete quest lines**, never a punishment lane: the dark lane has the same number of quests and
  comparable rewards; it costs reputation with the "good" factions and buys it with the Horde/Outcasts.
- **Fights are path-free** (owner request): a light player may still regicide Gazel (rep cost applies through
  `guards.js` kill penalty rules and a story `kill_rep` table, §6.1); a dark player may spar with Rimuru.
- **Every canon character appears in both lanes** (talk or fight), so a party never meets an empty town.
- Existing chapters 3 and 4 remain the spine; chapters 8 and 9 depend on their finales (`deps` across chapters are
  not supported by the generator today → chapter 8's first quest uses a `stage` task on `ttl.story.act2` that
  `story.js` grants when the chapter-3 throne quest completes; **verify** whether the generator can reference another
  chapter's quest id instead; if yes, use `deps`).

## 3. Choice: how it is recorded and what it gates

### 3.1 The Oath (one explicit branch point, one reversible twist)

- Quest "Crossroads" (ch.7) rewards with `command = "ttl story oath"` (new `command` reward, run as the player):
  opens a `ttlmenu` with two choices (texts from `story.toml`). A Fallen soul sees the dark choice first with
  "Your soul remembers"; a Legend-tier soul sees a third line "Walk alone" (= light for gating, title "Unaligned";
  **O5**).
- A **party** takes the Oath together: the owner chooses, every online member gets it; offline members get it at
  login (`ttl.story.pending`). A solo player is a party of one.
- **Twist (Act V):** "Atonement" (dark → light; costs: church +0, tempest reset to 0, 3 hand-ins) and "Corruption"
  (light → dark; after regicide or waking Charybdis) each allowed **once per life**; they swap stages and rep seeds.
- Life 1 carries: `ttl.tier.dark` pre-lights the dark Oath; a light Oath for a Fallen soul grants the title "Repentant".

### 3.2 State (R3)

| Where | Key | Holds |
| --- | --- | --- |
| Player persistentData | `ttl.story.path` (`light`/`dark`/``), `ttl.story.oath` (epoch), `ttl.story.flips` (0/1), `ttl.story.acts` (JSON `{act: epoch}`), `ttl.story.flags` (JSON set: `hero`, `demon_lord`, `regicide`, `charybdis_woke`, `falmuth_march`…), `ttl.story.pending` (path to apply at login) | Truth |
| Player stages | `ttl.path.light` / `ttl.path.dark` (exactly one after the Oath), `ttl.story.act<N>` (act done), `ttl.story.<flag>` | Quest gates, Easy NPC conditions |
| Scoreboard | `ttl.path` (0 none, 1 light, 2 dark) | Easy NPC dialog conditions, `/ttl inspect` |
| Server persistentData | `ttl.story.parties` (JSON `{teamId: {path, oathBy, at}}`), `ttl.story.log` (ring 200) | Party path, audit |

### 3.3 Gating

- Quests: lane quests carry `path = "light"|"dark"` in TOML (WP-S5 sugar → a `stage` task `ttl.path.<x>`).
- NPC dialog: one COMMAND button "Talk" → `/ttl story talk <npc>` (ExecAsUser, like the guild buttons); `story.js`
  answers from `story.toml` by path, act and faction band (`TtlRep.band`). Easy NPC's own objective conditions on
  `ttl.path` are optional polish (**verify** that `gen_npcs.py` can emit dialog conditions; not required).
- Bosses: `spawn.condition` (§5.1) may name stages, but **never** `ttl.path.*` (owner: anyone can fight).
- Factions: `guards.js` already turns guards hostile by band; the Oath and act deltas move the bands.

### 3.4 Ties

| System | Light | Dark |
| --- | --- | --- |
| Karma (Life 1) | `ttl.tier.dark` only pre-lights; nothing is locked | Fallen = default dark; title prefix shown in the Oath |
| Reputation | Oath +20 tempest; acts add tempest/dwargon/church/blumund | Oath +20 outcast +15 orc_horde −20 tempest; acts add orc_horde/falmuth/outcast and subtract tempest/church/dwargon |
| Renown | `factions.toml renown.stage` gets `ttl.story.act1..7 = 5,5,10,15,20,30,50`, `ttl.story.hero = 60` | the same, plus `ttl.story.demon_lord = 60` |
| Legendary (10 holders) | Act VII light draws from `legendary.light = ["great_sage", "creator"]` | Act VII dark draws from `legendary.dark = ["predator", "wrath", "pride", "greed", "lust", "envy", "sloth"]` (both via `TtlRegistry.draw` with `allowLegendary` and the `max_holders` check: a full roster = a Skill Core + title instead; **O6**) |
| Absorption (when `absorb/` lands) | — | "Devour" (ch.9) teaches it; Act VII dark gives `ttl.story.demon_lord` which `absorb.js` may read as the war-route licence (v2) |
| Nations (when `nations/` lands) | A nation founded by a light party seeds its home faction band from the party path | same, dark home = orc_horde / outcast |
| Events | Calamity Rising may pick a story boss the server has unlocked (`ttl.story.unlocked` server set) | same |
| Discord `#story` | Oath, act finales, Hero/Demon Lord | same |

## 4. Parties

### 4.1 Mechanics (verified)

- A party = an FTB **party team** (`/ftbteams party create …`). Quest progress is per team natively (TeamData), so
  "shared quest completion" is free. The same party later becomes a nation (S4), so **one party object serves both**.
- `pack/config/ftbteams-server.snbt`: `max_party_size: 5` (matches nations O2; the owner may raise it, **O1**).
  `limited_lives` stays 0 (Life 1 is hardcore by our own rules, not FTB's).
- `/ttl party` is a thin wrapper that prints members, path, boss credit range and the owner; creation stays FTB's own
  command/GUI (the FTB Teams sidebar button works with the quest book).

### 4.2 Path lock

- The Oath is a party decision (§3.1). `ttl.story.parties[teamId].path` is the party's path.
- Joining: `PlayerJoinedPartyTeamEvent` (register from JS in try/catch; fallback 5-minute roster poll from
  `ttl.story.parties`): an undecided joiner inherits the party path (and the Oath quest completes for them through
  team progress anyway); a joiner with the **other** path is removed again (`execute as <owner> run ftbteams party
  kick <name>` — **verify in game** that kick works when run as the owner through `runCommandSilent`; fallback
  `FTBTeamsAPI … Team.removeMember`) with a Voice line explaining Atonement/Corruption.
- Leaving: the player keeps their path and personal progress (FTB keeps the personal TeamData — **verify in game**
  that a player who leaves a party returns to their old personal progress and not to an empty book).

### 4.3 Shared boss credit (`boss.js` `finish`)

- At wake (`tick` first scaling), the record stores `party: {teamId: [uuids]}` for every player in range (snapshot).
- At death, after today's winners are computed, each winner's **party members** who are (a) in the snapshot or joined
  the party before the wake, (b) online, in the boss's dimension and within `party_credit_range` (`framework`
  knob, default `2 × range`), (c) Life 2 and not spectator, get **stage + kill count + rep + coins**; the **Skill Core
  goes only to contributors** (hit / presence) and to at most `core_per_party` (default 1 extra) party members chosen
  by damage order, so a party cannot farm cores by standing around.
- Anti-abuse: snapshot stops "invite after the kill"; `presence_secs` still applies to contributors; party credit is
  logged per member in `[ttl] boss:`; a member who is in another dimension gets nothing; a boss killed with no
  contributor (fall damage trick) still rewards nobody (today's rule).

### 4.4 Size cap and other guards

- Cap 5 (config). Story quests scale with `per_player_mult` already; nothing else needs a cap.
- One Oath per party per life; `/ttl story oath` by a non-owner member prints "ask your party leader".
- Bots: `ttlbot` players never count for party credit unless the test sets `ttl.testcaps` (the registry's test flag
  pattern), so tests can still assert it.

## 5. Spawn system redesign: `spawn` and `wild` per boss

### 5.1 `bosses.toml` additions (replaces `natural_allow`)

```toml
[framework]
block_natural = true          # unchanged: Tensura/NEB may never spawn a boss entity by themselves
# natural_allow is removed: Shizu goes through [boss.wild] like everyone else
party_credit_range = 2.0      # × range (§4.3)
core_per_party = 1

[wild]                        # server-wide knobs (bosses/wild.js)
enabled = true
max_active = 1                # wild bosses alive at once (summoned/arena bosses are not counted)
max_per_day = 2               # wild starts per Brussels day
min_gap_hours = 6
require_players = 1           # Life 2 players inside a listed region before a roll counts
distance = [64, 160]          # blocks from the chosen player, on the surface
idle_minutes = 30             # reuse of framework idle_minutes: nobody comes → removed
ignore_requires = true        # a wild boss answers everyone (owner request); the per-boss cooldown still applies
rewards_mult = 1.0            # knob for coins/rep of wild kills (core is never multiplied)
announce = true               # title + chat to Life 2 + Discord #story; BlueMap marker if gen_map is live
life2_only = true

[[boss]]
id = "hinata_sakaguchi"
# … existing fields …
spawn = { kind = "quest", at = { x = -400, z = -60, radius = 48 }, stages = ["ttl.defeated.shizu"] }
#   kind = quest (TtlBoss.summon from a quest command reward or `/ttl story fight <id>`), altar (an NPC/statue dialog
#          calls it), statue (attacking the tame statue swaps it for the boss; Gazel), event (director only)
#   at    = arena (same shape as `arena`; `landmark` allowed); stages = summoner must hold all of them (in addition to `requires`)
wild = { chance_per_day = 0.005, regions = ["F", "R", "G", "L"], path_mult = { dark = 3 }, weather = "any", time = "any", biomes = [] }
#   chance_per_day = probability that a day of qualifying presence produces one; rolled per minute as chance/1440
#   regions = canon letters (CanonMap.grid charAt/ownerCell); biomes = optional biome ids/tags the spot must be in
#   weather = any|thunder|rain, time = any|night|day; path_mult = per-path multiplier on the chance of the chosen player
#   cooldown_hours (optional, default = the boss cooldown), cap (optional, max wild instances of this id per day, default 1)
```

`arena` keeps working as before (fixed, bound); `spawn.at` defaults to `arena`. A boss with neither is wild-only.

### 5.2 `bosses/wild.js` (new)

- Registers with the director as a **poll** (`TtlEvents.register({id: 'wild_boss', poll(server) {...}})`) so one loop
  owns timing; no `[[event]]` entry → it is never scheduled or capped by `max_per_day` of the director, and it
  respects `TtlEvents` `max_active` by refusing a roll while a timed event with `action.boss` is active.
- Each poll (every `poll_ticks`, 100): for every boss with `wild.chance_per_day > 0`, for every Life 2 player (not
  bot, not spectator) whose region letter is in `regions` and whose dimension is the overworld: `p = chance / 1440
  × poll_minutes × path_mult[path]`; weather/time filters; global caps; boss cooldown. On a hit: choose a surface spot
  `distance` blocks away (random angle, highest block, not water unless `surface = "water"`), refuse spots inside the
  Tempest safe zone (`TtlSafeSpawns.inZone`) and any placed build box (`ttl.build.*.corner` + size), then
  `TtlBoss.summon(server, id, {x, y, z, dim, wild: true, by: 'wild', force: wild.ignore_requires})` — `force` only
  skips the `requires`/stage gate, **not** the cooldown (boss.js splits `opts.force` into `opts.skipGate` and
  `opts.skipCooldown`; ops keep both).
- Announce: `title` "A calamity stirs" / subtitle "<title> roams <region>" to Life 2, chat line, `#story`; the
  wild record (`ttl.boss.active[key].wild = true`) makes `finish` apply `rewards_mult`.
- Shizu: `wild = { chance_per_day = 0.01, regions = ["J"] }` replaces `natural_allow`; her summoned/wild instance is
  tagged and credited like every boss. The Tensura `OtherworlderSpawnDistribution` and NEB chances stay blocked
  (`block_natural`, `neb_config` zeros).

### 5.3 Coexistence

| Mechanism | Who summons | Place | Gate | Counted by |
| --- | --- | --- | --- | --- |
| Story / altar / statue | quest command reward, NPC dialog, statue hit | `spawn.at` / `arena` | `requires` + `spawn.stages` + cooldown | boss active list |
| Calamity Rising (events) | director `action.boss` | arena | ops-force (as today) | director `max_active` + boss list |
| Wild | `wild.js` poll | random spot near a player in region | cooldown only | `[wild]` caps + boss list |
| Tempest arena bosses (Shizu, Ifrit, Rimuru) | story | (0, 0, r 48) | `requires` | one at a time per id (today's rule) |

A boss id is never alive twice (`summon` refuses "already out there"), so a wild Shizu blocks the story Shizu for
`idle_minutes` at most; the story quest shows "Shizu is elsewhere — wait or hunt her".

## 6. Data

### 6.1 `design/data/story.toml` (new; `gen_data.py check_story()`)

```toml
[oath]  menu_title, light = { label, lore, rep = { tempest = 20 }, title = "" }, dark = { label, lore, rep = {…}, title = "Marked" },
        unaligned_for_legend = false, flip_once = true
[[act]] id = 1..7, key, title, chapter = 7, light_rep = {…}, dark_rep = {…}, renown = 5, story_line = "…", unlock_bosses = [...]
[[npc]] id = "rigurd", entity = "goblin_named:Rigurd" | "easy_npc:ttl_cast_benimaru" | "statue:tensura:hinata_sakaguchi", build/spot refs (npcs.toml owns positions)
        [npc.talk.light] = [{ act = 1, text, buttons = [{ label, command = "ttl story fight gazel_dwargo" }] }], [npc.talk.dark] = [...], [npc.talk.any]
[kill_rep] gazel_dwargo = { dwargon = -60, flag = "regicide" }, hinata_sakaguchi = { holy_church = -30 }, rimuru_ogre_fight = { tempest = -40 } …   # applied in finish() on top of rewards; light players too
[legendary] light = [...], dark = [...]
```

### 6.2 `npcs.toml` extension (WP-S4)

`[[kind]]` gets `talk = "story"` (one "Talk" button → `/ttl story talk <id>`) and the `skin` forms of §1.3;
`[[spot]]` gets `anchor = "build"` for `tempest`, `marris`, `blumund`, `englassia`, `lubelius`, `laura`,
`clayman_castle`, `forgotten_dragon_city`, `treyni_shrine`, `spirit_dwelling` (all placed builds expose
`ttl.build.<name>.corner`; Tempest keeps its `tempest` anchor). `kind.statue = "tensura:hinata_sakaguchi"` spawns a tame
NoAI statue (the `TtlDwargonGazel` NBT pattern) instead of an Easy NPC; the "Talk" comes from an interaction hook
(KubeJS `ItemEvents.entityInteracted` on the statue tag — **verify in game** in 2101; fallback: a tiny invisible
Easy NPC on the same block carrying the button).

### 6.3 Quest TOML additions (WP-S5)

`path = "light"|"dark"` on a quest; rewards `{ type = "stage", stage = "ttl.story.act2" }` (gamestage reward,
`team = false`, silent) and `{ type = "command", command = "ttl story fight gazel_dwargo", as_player = true }`
(FTB `command` reward: `player_command` flag — **verify** the field name in `CommandReward.writeData` with `javap`);
`deps` may reference `"<chapter>/<quest>"` (cross-chapter; the id hash already includes the chapter key).

## 7. Work packages (one agent each, ≤ ~70 min, no shared files; reserved lines named)

| # | Package | Owns | Deps | Bot test |
| --- | --- | --- | --- | --- |
| WP-S1 | **Story core**: `TtlStory.oath/path/flip/act/flag/talk/fight`, state of §3.2, Oath menu, rep deltas, `#story` lines | `story/story.js`, `story/commands.js` (`/ttl story oath|talk|fight|act|expect`), `design/data/story.toml`, `gen_data.py check_story`, `tests/ingame/story.rcon`; reserved line in `karma.js` login sync (`TtlStory.syncScoreboard`) | — | Life 2 bot `ttl story oath dark` → `expect <bot> path dark`, stage `ttl.path.dark` yes, `ttl rep expect <bot> outcast band friendly`; `flip` once ok, twice refused |
| WP-S2 | **Party layer**: path lock, join/leave hook + poll, `/ttl party`, FTB config | `party/party.js`, `party/commands.js`, `pack/config/ftbteams-server.snbt`, `tests/ingame/party.rcon`; reserved line in `story.js` (`TtlParty.membersOf`) | WP-S1 | two bots, `ftbteams party create`, owner oath light → member `expect path light`; third bot with dark path `party join` → kicked within 300 ticks |
| WP-S3 | **Boss spawn + credit redesign**: `spawn`/`wild` knobs, `skipGate/skipCooldown`, party credit snapshot, `kill_rep`, remove `natural_allow` | `bosses/boss.js`, `bosses/wild.js`, `bosses/commands.js` (`wild roll <id> [player]`, `expect`), `design/data/bosses.toml`, `tests/ingame/bosses.rcon`, `tests/ingame/wild.rcon` | WP-S2 optional (stub `TtlParty` absent = no party credit) | `ttl boss wild roll shizu <bot>` → log `[ttl] boss: wild shizu near <bot> in Jura`; second roll refused (`max_active`); kill with two party bots in range → both `expect stage t2 yes`, core only one |
| WP-S4 | **Cast**: `npcs.toml` kinds/spots for §1.2, statue kinds, skin forms, `gen_npcs.py` `talk = "story"` + `SkinData`, interaction hook, goblin dialog hook | `design/data/npcs.toml`, `tools/gen_npcs.py`, `economy/guild_npcs.js` (rename to `npcs/npcs.js` only if no other agent touches it; else extend in place), `story/cast.js` (statues + hooks), `tests/ingame/npcs.rcon` | WP-S1 (talk command; stub prints "story not loaded") | after builds placed: `ttl npc expect spot benimaru present`; `execute as <bot> run ttl story talk rigurd` prints the light line; statue `hinata_lubelius` present and `Invulnerable` |
| WP-S5 | **Quest generator**: `path`, `stage`/`command` rewards, cross-chapter `deps`, `team_stage`; `quests.md` | `tools/gen_quests.py`, `design/quests.md`, `tests/ingame/quests.rcon` | — | `gen_quests.py --check` green; `/ttl quests check` loads a chapter with a command reward |
| WP-S6 | **Chapters 7 + 8** (Crossroads, The King's Test) | `design/quests/chapter_7_crossroads.toml`, `chapter_8_kings_test.toml` | WP-S5, WP-S1 (stage names), WP-S3 (Gazel `spawn`) | bot with `ttl.path.light` sees "Honour duel", dark bot sees "Regicide" (`/ftbquests` progress via `ttl quests expect`) |
| WP-S7 | **Chapters 9 + 10** (Orc War lanes, Charybdis) | `chapter_9_two_hundred_thousand.toml`, `chapter_10_whirlpool.toml` | WP-S5/S1/S3 | Charybdis arena summon from the ritual command reward; both-path completion |
| WP-S8 | **Chapter 11 + invasion event** (Shizu→Ifrit phase hook, Hinata, Falmuth march, Rimuru) | `chapter_11_mask_and_blade.toml`, `events/invasion.js` (knight waves + Folgen via `TtlBoss.summon`), `[[event]] falmuth_invasion` in `events.toml` | WP-S3 (ifrit arena, folgen), WP-S7 | `ttl events fire falmuth_invasion` → 20 `falmuth_knight` at the south gate + Folgen boss; end clears them |
| WP-S9 | **Chapters 12 + 13** (Walpurgis council scene, Clayman proxy, Carrion, Luminous, Veldora, Hero/Demon Lord capstones + Legendary draw) | `chapter_12_puppet_master.toml`, `chapter_13_harvest_festival.toml`, `story/capstone.js` (`TtlStory.capstone` → `TtlRegistry.draw(..., {allowLegendary, pool})`) | WP-S1, WP-S3, registry `draw` pool option (reserved line in `registry.js`: accept `opts.pool`) | dark bot with all flags → `ttl story expect <bot> flag demon_lord yes`; with 10 holders → Skill Core instead |
| WP-S10 | **Docs + decisions**: `master-plan.md` divergence pass (§5 Legendary routes, §6 NPCs), `decisions.md` rows, `roadmap.md` ticks, `docs/discord-guides.md` story channel text | those files | after each merge | — |

Waves: **A** WP-S1 WP-S3 WP-S5 (independent; S3 stubs the party) → **B** WP-S2 WP-S4 WP-S6 → **C** WP-S7 WP-S8 →
**D** WP-S9 WP-S10. Each package ends with `validate.py` green, `server.sh test <name>` green, no new `[ttl]` errors,
and a `decisions.md` row.

## 8. Open owner decisions (recommendation first)

| # | Question | Recommendation |
| --- | --- | --- |
| O1 | Party cap: 5 (= nation cap) or larger story parties (8)? | **5.** One object for party and nation; bosses scale per player anyway. |
| O2 | Oath per party (leader decides, mismatched joiners are kicked) or per player (mixed parties, lanes gate per member)? | **Per party.** Team progress makes per-member lanes leak (one member's stage completes the lane for all). |
| O3 | Clayman as a proxy boss on `tensura:arch_daemon` ("Marionette Master"), or no Clayman fight until a mod ships him? | **Proxy now**, lore-named; Walpurgis without a Clayman fight is hollow. Same answer for Gabiru (`lizardman`). |
| O4 | Kijin (Benimaru) and Razen fights: proxies on `tensura:greater_daemon` / `tensura:lesser_daemon`, or talk-only? | **Talk-only this sprint**; proxies on daemon entities read wrong. Revisit when a mod adds them. |
| O5 | A third "Unaligned" Oath for Legend-tier souls? | **No** (two lanes keep every quest reachable; "unaligned" is light with a title). |
| O6 | Legendary routes: light = Great Sage/Creator pool, dark = Predator + sins; full roster (10) → Skill Core + title? | **Yes**, and the draw stays behind `TtlRegistry.draw` with `max_holders` (rule 1). |
| O7 | Wild odds: the table in §1.1 (T1 3 %/day … T4 0.1 %/day, Hinata ×3 for dark players), `max_active 1`, 2/day? | **Yes** as the starting values; tune after two weeks of `#story` data. |
| O8 | Skins: commission/draw own PNGs for the eight Tempest kijin + Milim + Treyni (shipped as `ttl:` resources), built-in variants for the rest? | **Yes**; no third-party PNGs ever (R4). |
| O9 | Hinata's ambush spot: fixed on the Blumund road (−400, −60) or wherever the player is when the quest fires? | **Fixed road spot** (definite place, owner request 3); the quest sends the party there. |
| O10 | Falmuth invasion: scripted event only, or also a weekly director event once Act V is unlocked server-wide? | **Scripted first**, director repeat after the first playthrough reaches Act V. |
