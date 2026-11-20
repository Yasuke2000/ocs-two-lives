# Post-Kijin place concepts — twenty-eight delivered locations

Latest: four original demon-seat/ruin concepts bring delivery to28/58, with30 remaining. All58 reservation attributes match main-map8ea1e96. C07 and C22 remain explicit source/access/type decisions, not resolved by concept pictures.

Four further Dwargon/interior revisions now bring delivery to24/58, with34 remaining; their58 reservation attributes match24897fa. The prior Jura/marsh revisions compare all58 site attributes against main-map6a66e5d and previously brought delivery to20/58. [Third painting/SVG review](https://github.com/Yasuke2000/ocs-two-lives/pull/92) is separately delivered.

These original illustrations and their fiches use the owner-selected instant immediately after Kijin naming. The first eight use reservation source`fc36e38`; the western four were checked against`a997f81`; the southern/Imperial four check all58 reservation attributes against`052f262` (current main terrain geometry`efa2cc8`). This art branch stacks on the earlier art delivery and does not include later map/source commits. These are design references, not in-game screenshots or a new source of canonical geography.

| Place | Image | Source and terrain sheet |
| --- | --- | --- |
| Rimuru's early village | [PNG](tempest.png) | [Sheet](tempest.md) |
| Dwargon southern mountain gate | [PNG](dwargon.png) | [Sheet](dwargon.md) |
| Rondo / Londo, Blumund | [PNG](blumund.png) | [Sheet](blumund.md) |
| Lake Siss southern marsh shore | [PNG](lake_siss.png) | [Sheet](lake_siss.md) |
| Treyni's shrine — server interpretation | [PNG](treyni_shrine.png) | [Sheet](treyni_shrine.md) |
| Sealed Cave exterior approach | [PNG](sealed_cave.png) | [Sheet](sealed_cave.md) |
| Dwarf meadow village — pack interpretation | [PNG](dwarf_village.png) | [Sheet](dwarf_village.md) |
| Orc advance camp — encounter reservation | [PNG](orc_camp.png) | [Sheet](orc_camp.md) |
| Lura / Englassia capital precinct | [PNG](englassia.png) | [Sheet](englassia.md) |
| Marris / early Falmuth royal precinct | [PNG](marris.png) | [Sheet](marris.md) |
| Coleus / Herbaria hill-palace precinct | [PNG](coleus.png) | [Sheet](coleus.md) |
| Shia / Siltrosso counting court — interpretation | [PNG](siltrosso.png) | [Sheet](siltrosso.md) |
| Elmine / Divine Tree public terrace | [PNG](elmine.png) | [Sheet](elmine.md) |
| Jia / Fulbrosia cliff court | [PNG](jia.png) | [Sheet](jia.md) |
| Undestroyed old Laura / Eurazania | [PNG](laura.png) | [Sheet](laura.md) |
| Nasca / interpreted Imperial court | [PNG](nasca.png) | [Sheet](nasca.md) |
| Old goblin village | [PNG](goblin_village.png) | [Sheet](goblin_village.md) |
| Recently destroyed ogre village | [PNG](ogre_village_ruin.png) | [Sheet](ogre_village_ruin.md) |
| Siss stilt hamlet — project/mod adaptation | [PNG](lizardmen_village.png) | [Sheet](lizardmen_village.md) |
| Lizardmen labyrinth chamber | [PNG](lizardmen_caverns.png) | [Sheet](lizardmen_caverns.md) |
| Dwargon inner-city precinct | [PNG](dwargo.png) | [Sheet](dwargo.md) |
| Dwargon audience chamber | [PNG](dwargon_throne.png) | [Sheet](dwargon_throne.md) |
| Kaijin's former workshop | [PNG](kaijin_smithy.png) | [Sheet](kaijin_smithy.md) |
| Dwarf-village arena — server adaptation | [PNG](dwarven_arena.png) | [Sheet](dwarven_arena.md) |
| Clayman's intact castle | [PNG](clayman_castle.png) | [Sheet](clayman_castle.md) |
| Ancient Amrita gallery | [PNG](amrita.png) | [Sheet](amrita.md) |
| White Ice Palace corridor | [PNG](frost_palace.png) | [Sheet](frost_palace.md) |
| El Dorado court precinct | [PNG](el_dorado.png) | [Sheet](el_dorado.md) |

The earlier `chatgpt/priority-place-art` branch and local `C:/Users/david/Documents/ocs-art-map` candidates remain untouched. That worktree contains 29 candidate PNGs and 58 sheets; many are untracked and have not been accepted against the current map. The old Tempest sheet uses radius 110, while this pass reads the current SVG. The old Orc camp depicts a large organized fortification; the selected revision depicts a small temporary advance reservation appropriate to the early baseline. The existing candidates are not counted as delivered or discarded.

[Coverage](coverage.csv) keeps all 58 IDs: twenty-eight image/sheet pairs delivered in this branch, with existing local candidates explicitly recorded for the remainder. Do not regenerate those candidates blindly. No complete 58-image set is claimed. Thirty image/sheet pairs remain undelivered. Country/location research remains open; the third painted atlas and SVG review is separately delivered in [draft PR92](https://github.com/Yasuke2000/ocs-two-lives/pull/92). Prior PR88/PR90 remain historical.

The image format is 1536x1024, RGB, opaque, below 3,000,000 bytes per PNG; [manifest](asset-manifest.json) records exact sizes and hashes. Among the first eight, three PNGs were losslessly repackaged; decoded RGB pixels match their original generated outputs. The selected dwarf-village correction removes an invented surface palace from its background. No mod texture, official frame, proprietary structure or map is copied into these images. The fiches distinguish canon context, server interpretations and unknown episode attribution.

The terrain/biome/road source is unchanged. These images do not verify foundations, structure placement, cave water, detailed shore alignment, NPC rosters or runtime era gates. [Map PR74](https://github.com/Yasuke2000/ocs-two-lives/pull/74) remains the geometry review.



## Western revisions — round21

The new Englassia and Marris images show compact representative precincts, replacing unsupported extra water and panoramic scale in the older local candidates. Coleus uses the inspected official INEI production concept for broad hill/dome/stair cues, while exact architecture and its S1E10 state remain interpretation/unverified. Siltrosso edits our own older concept to replace an unsupported snowy backdrop with low coastal hills; its counting court remains an explicit server design, independent of Falmuth sovereignty. All four new images were visually reviewed.

All five official episode20 and episode28/no30 stills were inspected: they provide character/interior context, not verified Englassia or Falmuth exterior plans. These leads are not upgraded to architectural evidence. Official art remains linked in the fiches and cached outside the repo; no official reference was an image-generation input. The Siltrosso edit uses only our original concept. Its first-generation prompt is unavailable; the complete current edit prompt is recorded.

[Western manifest](western-asset-manifest.json) records four asset hashes, original output hashes, exact reservation attributes and RGB pixel-preserving packaging checks; [western prompts](western-prompts.json) records exact current prompts. The earlier eight-asset manifest remains unchanged. Englassia and Marris were losslessly recompressed under3,000,000 bytes without changing a single RGB pixel. These representative scenes are not whole-city surveys, blueprints, terrain alterations or runtime acceptance.

Round21 verification: all12 PNG/sheet pairs match their manifests and the58-row coverage table; all images are RGB1536x1024 below3,000,000 bytes. Repository gate passes validation and462 tests (26 skips,zero failures,44.871s test tier). `world/`, `tools/`, `mod/` and `pack/` are unchanged from the base art branch. No in-game acceptance or deployment is claimed.

## Southern and Imperial revisions — round23

Elmine,Jia,Laura and Nasca add four current original image/sheet pairs. The cached secondary anime frames for the first three were reinspected; their exact episode/timestamps remain unverified. Elmine shows only a compressed lower tree precinct, Jia one supported cliff court, and Laura an intact pale-stone old-capital precinct distinct from the later reconstructed timber city. LN5 castle/town/mountain evidence and the official climate/cultivation guide remain separate from secondary visual cues and our exact architecture. Nasca remains an explicit server court interpretation: no independently verified anime exterior was found. The three empty chairs do not identify a canonical trio.

[Southern/Imperial manifest](southern-imperial-asset-manifest.json) records original/output hashes, dimensions, byte sizes and current reservation attributes. [Exact prompts](southern-imperial-prompts.json) are retained. All four outputs were visually inspected and losslessly packaged; decoded RGB pixels match the original generated files exactly. Copyrighted references stay outside the repo and were not generation inputs. No named ruler/resident roster, war damage, later technology or Tempest reconstruction banners are depicted.

All58 reservation attributes match current main-map review052f262 (geometryefa2cc8). This art branch stacks on840c26f and does not contain the later map/source commits; use [map PR74](https://github.com/Yasuke2000/ocs-two-lives/pull/74) for current terrain. The [second painted atlas is in PR90](https://github.com/Yasuke2000/ocs-two-lives/pull/90); PR88 is historical. A third coupled review and other source/location gaps remain open. The earlier manifests remain historical deliveries; total16/58 concepts are delivered,42 remain. Concepts do not complete city/tree/cliff builds, terrain fit or runtime acceptance.

Round23 gate: validation passed;462 tests in44.845s,26 skipped,zero failures. All16 PNG/sheet pairs match their three manifests and the58-ID coverage table; every image is RGB1536x1024 below3,000,000 bytes. World/tools/mod/pack remain unchanged from840c26f. No in-game acceptance is claimed.

## Jura and marsh revisions — round26

Four revised original project images remove unsupported spectacular set dressing: goblin spire/brook; ogre wizard tower, shrine/memorial and stream; marsh cliff wall/flags; cavern waterfall/skylight/flags/huge lake. Recent ogre destruction, dry forest goblin reserve, wet stilt supports and a restrained underground chamber fit the selected baseline more closely. The surface hamlet remains a project/mod adaptation, not an anime-verified plan. Original legacy candidates remain untouched.

Official episode2/9/10/12/13 stills inspected; selected evidence and confidence are in [reference review](jura-marsh-reference-review.csv). Secondary ogre-village/Siss frames remain attribution-limited. New images used only original project candidates as edit inputs; copyrighted references remain outside the repo. [Exact prompts](jura-marsh-prompts.json), four sheets and [manifest](jura-marsh-asset-manifest.json) record the scope and output/input hashes. Current58 reservations match6a66e5d. Geometry is supplied by current map PR74, not the older world files retained in this stacked art branch. No actual terrain, structure or runtime change.

All20 delivered image/sheet pairs and their manifests/coverage table are checked. Four new images are1536x1024 RGB,under3,000,000 bytes; lossless packaging preserves every original output RGB pixel. Full-settlement fidelity, current blueprint fit, cave roof/drainage, stilt foundation and runtime-era review remain open. No named early resident roster is asserted. Round26 gate passes repository validation and462 tests (26 skips,zero failures,44.523s test tier).

## Dwargon interiors and village hall — round27

The registered dwargo city-centre pin receives a new internal street/plaza vignette instead of a duplicate exterior gate. The throne hall closes its unverified mountain-view windows and removes the figure/emblems. Kaijin's old smithy becomes a compact covered cavern-city shop with the warm brick/tool-wall cue from official episode4 still4; the selected era does not put Kaijin back in Dwargon. The separate server arena is grounded beside dwarf cottages rather than a cliff/ravine/dragon-nest panorama. It remains an explicit gameplay interpretation.

[Six visual/design records](dwargon-interior-reference-review.csv), [exact prompts](dwargon-interior-prompts.json), four sheets and [manifest](dwargon-interior-asset-manifest.json) distinguish direct official episode4/5 context from authored plans. All10 stills visually inspected; no playback timestamps claimed. The city-centre image is new original generation; the other three edit only older original project candidates. Copyrighted frames are cached outside the repo and were not generation inputs. Old candidates remain intact.

All58 reservations match main-map24897fa, though this stacked art branch retains older map/source files. The three radius8 spots belong to the parent cavern city and do not define separate16-block-wide cities or independent surface pads. All24 image/sheet pairs match five manifests and coverage; four new RGB1536x1024 PNGs are under3,000,000 bytes and preserve selected output pixels through lossless packaging. Full city/hall/workshop source fidelity, roof/ventilation, build fit, nested placement and runtime-era acceptance remain open. Third continent painting/SVG review is in PR92. Round27 gate passes repository validation and462 tests (26 skips,zero failures,44.770s test tier); no world/tools/mod/pack/blueprint changes or apply/deployment.

## Demon seats and ancient gallery — round28

Four new originals: clayman_castle,amrita,frost_palace,el_dorado. Source-qualified written prompts use inspected official anime contexts and public LN/WN evidence without supplying copyrighted images to generation. Castle architecture is an intact original forest fortress; Amrita is a dormant subsurface gallery rather than a public mound; Frost Palace is an interior avoiding the unresolved coast/inland dispute; El Dorado is one pale/gold/purple court precinct rather than the entire city. No later visitors, raids, active wards or fixed NPC roster are depicted.

[Nine reference/design records](demon-seats-reference-review.csv), [exact prompts](demon-seats-prompts.json), four sheets and [manifest](demon-seats-asset-manifest.json) preserve evidence limits. WN continuity remains separate; public LN10 evidence does not measure Amrita's entrance or depth. Later El Dorado interiors do not certify exact early architecture. C07/C22 and full city/palace/source/roof/water/build-fit/runtime obligations stay open. Current58 reservation attributes match8ea1e96; this art branch retains older map/source files, so current terrain/source decisions belong to map PR74.

All28 pairs match six manifests/coverage. The four new images are1536x1024 RGB,<3,000,000 bytes; lossless PNG packaging preserves every original output pixel. Existing legacy materials are untouched. Third continent painting/SVG review is separately in PR92. Round28 art gate passes repository validation and462 tests (26 skips,zero failures,43.977s test tier). No world/tools/mod/pack/blueprint/apply/deploy changes.
