## 2026-11-23 — concise current contradiction delivery

Branch `chatgpt/current-contradictions`: the requested short source-conflict summary now separates open choices, adopted owner decisions and remaining evidence limits. All 24 conflict IDs retained; the previous 3604-word dated record is archived byte-exact beside it. All local summary links resolve. Ledger355 and all map/art/terrain/runtime files remain unchanged;no new geographic claim or owner choice. [Current summary](research/tensura-world-2026-11-19/contradictions.md),[history/audit](research/tensura-world-2026-11-19/contradictions-summary-audit.json). The legacy Filtwood U/J dependency and two pending owner choices remain explicit. Fresh required check: 494 tests in 66.406s, 26 skipped, the same two legacy Filtwood U/J failures plus validation; zero changed JS files. The repository gate is not passing.

## 2026-11-23 — LN20/LN21 legal sample boundaries screened

Branch `chatgpt/ln21-trial-screening` follows consolidated authoring source9526890d. LN20 later chapter1 selection reaches actual93/93;LN21 normal store trial works and chapter1 heading40/89 plus available portion through89/89 are visually screened. No wall-specific passage or new map geography is verified. Dagruel wall simile rejected as a physical-wall description. Ledger355 and all confidence classes retained;only two wiki-wall verification notes are clarified. [Review](research/tensura-world-2026-11-19/licensed-trial-boundary-review.md). Source screenshots/HTML remain private;no map/art/terrain/runtime changes. Fresh gate494tests in66.398s,26skipped,the same2legacy-U/J failures plus validation;not passing. All14normal hashes retained;only2verification fields changed. Do not retry these same sample endpoints for unavailable later wall passages without changed access evidence.

## 2026-11-23 — consolidated creative map on current main history

The requested `chatgpt/world-map` authoring branch includes owner-approved Filtwood, the355-record source dossier, current guide/painting and the capital-identity correction. Upstream main 3555a00bf893d0aea2413b853e98fee209489835 is incorporated unchanged in runtime/tool/mod paths, apart from the five previously owner-approved relation data records already in authoring history. Only the decision-log and handoff conflicts needed resolution; both histories are preserved. This is a draft authoring integration, not a main merge, world apply or deployment.

The known Filtwood legacy-grid U versus approved J dependency still requires technical reconciliation. Larger-island/Malukshure owner choices and source gaps remain open. Fresh combined checks:map checker0errors/56relations/2standingwarnings;repository494tests in67.106s,26skipped,the same2legacy-U/J failures plus validation. All17upstream-changed JS files pass syntax checking. All14normal export hashes,source/preview and original art remain exact. See [consolidation audit](../world/consolidation-audit.json). Earlier check counts remain historical.

## Upstream main handoff additions


## 22/11 — owner calls on #145 and #70 (branch `life1-occultism-soulbound`, Claude)

**#145** Occultism allowed in Life 1, ritual items banned per item/tag in `mortal_banned.toml` (list and reasons in the file
and `design/decisions.md`); `/ttl stash check` asserts every id/tag exists. **#70** only `ttl:soulbound` crosses; ttl-portals
0.9.3 `EnchantmentMenuMixin` keeps Tombstone's Soulbound off enchanting tables in the Mortal dimensions, the Book of Soulbound
is stashed until Life 2; guide + wiki two-lives EN/NL explain it. Test `life1_bans.rcon` (hook `/ttl soul table`). Open edge:
a Soulbound book from a Life 1 villager or loot can still be applied with an anvil (harmless, explained in the guide).

## 22/11 — Life 1 tester issues #85 #104 (fixed) and #70 #145 (owner calls), branch `fix-life1-issues`, PR #148, Claude

**#104** Iron's spells failed in Life 1: the Tensura bridge (`manaConversionMultiplier = 50`) asks a Life 1 Human (50-70
magicules) for 50 x the cost; ttl-portals 0.9.2 `SpellManaMixin` + `TensuraIronCastMixin` make Iron's use its own mana in
the Mortal dimensions (Life 2 keeps the bridge; blood/eldritch veto O-N1 kept). **#85** frames did not light in the Mortal
Realm (vanilla `BaseFireBlock.inPortalDimension`): `BaseFireBlockMixin`. Hooks `/ttl spells`, `/ttl useon`; tests
`life1_spells.rcon`, `portals.rcon` part 2, `tests/test_life1_rules.py`. **Verified locally** (release jar 0.9.2):
life1_spells, portals, carryover, soul, race_lock, paths_items, life1_status, two_lives. **Open for Yasuke** (options on the
issues): #145 Occultism banned in Life 1 by O-N1; #70 Tombstone's Soulbound does not cross to Life 2 (only `ttl:soulbound`).
Client side not done: the bridge hides Iron's mana bar, also in Life 1 (a client mixin on `ManaBarOverlay` would fix it).

## 22/11 — tester issues #72 #73 #75 #86 #144 (branch `fix-reset-sleep-l2h`, Claude, for Yasuke)

**#73/#72 reset kept skills**: `/ttl reset` revoked only uniques and set the race with `tensura edit race set` (keeps every
other ability, the old race's intrinsics and the EP). Now `life/soul_wipe.js`: registry `revokeAll`, every other ability
one at a time, `tensura reset <p> race tensura:human` (EP, existence, spirits, statistics; no race menu). Tensura never
forgets a resistance: a revoke puts it back to the start of learning (negative mastery, inactive), counted as not held.
The Life 1 death strips the abilities the Human learned; the command rebirth rolls the new race's EP (`... set <race> true`).
**#86**: the Mortal Realm reads the overworld clock and vanilla's sleep there could not move it; `life/sleep.js` moves it on
NeoForge's `SleepFinishedTimeEvent`; gamerule `playersSleepingPercentage` 50 (applied at server start). **#144**: L2H Life 1
caps 100/150/200 (owner call open: remove them?). **#75**: `/ttl life1 status <player> [<preset>]`, `/ttl life1 days`
(karma.toml [presets]). `TtlKarma.set` now goes through the dispatcher (runCommandSilent landed a moment later).
**Verified locally** (Lerfing): reset_full, sleep (Mortal Realm and overworld), life1_status, karma, race_lock, rebirth,
rebirth_scene, two_lives, registry, registry_reconcile, soul, carryover, bed_spawn, roads, absorb, legendary,
trial_knowledge, trial_strength, necro_ranks, quests. **Not done**: L2Archery (suggested in #144) needs `/add-mod` and an owner yes.

## Creative map handoff history

## 2026-11-23 — capital identity and consolidated authoring delivery

The Forgotten Dragon City place/lore pages,proportion note,world brief and era policy no longer assert that Milim's later capital was built at the authored `laura` coordinate. Direct LN20 evidence only fixes former Eurazania. Carrion's initial undestroyed capital remains distinct;C24 proper-name uncertainty is kept explicit instead of presenting the technical ID as proof. No numeric reservations,blueprints,terrain,art,tools,mod or pack files change. Ledger355 retained;no duplicate source claim. Fresh required gate:472tests in67.434s,26skipped,the same2legacy-U/J failures plus validation. All57matching imported-table technical tuples remain unchanged;source/anchor files remain byte-identical.

The approved Filtwood drawing and source follow-ups are ready for fast-forward inclusion in the requested `chatgpt/world-map` draft authoring branch. This is not main or runtime deployment. The known legacy-U/J validation/two-test dependency remains explicit. Do not undo the owner-approved J binding merely to obtain a green authoring check. Larger-island/Malukshure choices and unresolved source bearings remain open.

## 2026-11-23 — current terrain-guide correction

`world/regions.md` and `world/comparison.md` now identify source9526890d and23roads after approved Filtwood. Removed current-tense claims that all58sites/22roads and painted pixels remain unchanged since R127;those assertions belong to earlier revisions. Current Filtwood audit/manifest and painting are linked. Retained all22regional headings,22biome mixes and22curated-reference paragraphs. LN20 later-capital evidence is now beside the Eurazania narrative,with the S1E10 exclusion explicit. No map/art/terrain/runtime edit. See [guide audit](../world/current-guide-audit.json). Fresh required gate:472tests in67.426s,26skipped,the same2legacy-U/J failures plus validation;not passing. The same integration dependency remains.

## 2026-11-23 — licensed LN20 capital-source follow-up

Branch `chatgpt/ln20-capital-source` stacks on approved-Filtwood PR146. Ordinary ebookjapan trial now works after closing its coupon popup; selected chapter1 opening at viewer36/93 directly places the later planned Milim capital in former Eurazania. Added LN20-CAPITAL-001;355unique rows. Sample menu lists only prologue/chapter1,not the Long Wall chapter3. No whole-sample reading or exact capital coordinate/name. [Source review](research/tensura-world-2026-11-19/ln20-licensed-capital-review.md). All map/art/terrain bytes retained. Fresh gate:472tests in68.854s,26skipped,the same2inherited Filtwood legacy-U/J failures plus validation;not passing. No runtime changes or apply.

## 2026-11-22 — Yasuke-approved Filtwood forest-edge placement

Branch `chatgpt/filtwood-approved`; base `chatgpt/world-map`. Yasuke explicitly approved "Bosrandvoorstel gebruiken; Filtwood U → J". Source region changed U→J only; old Lerfing x/z retained. Own-world pin(-1050,600),r8,margin24; new1102-block trail. Fresh default checker0errors/56relations/2warnings; normal71.9s without skip-check,generated(-1050,74,600),J. All57other sites/22old roads unchanged,241height centres changed,water/biome bytes unchanged,all13lake+8Hinputs unchanged. Updated terrain/painted atlases,marker39,source354records,Filtwood sheet and manifest. Original image/prompt retained.

**Technical handoff / not main-ready:** `bash tools/check.sh` ran472tests/26skipped and fails2tests plus validation: old `canon_map.txt` reads U at legacy(-900,700) whereas approved source says J. `test_every_anchor_on_its_ground_and_in_its_region[filtwood]` and `test_gen_data_check_covers_the_env_file`. Claude must reconcile legacy/own-world source transition and generated runtime derivatives under technical scope. Do not hide this with arbitrary legacy movement or a skipped gate. No protected runtime/tool/mod edits,apply,main merge or deployment. See [reviewable adoption](../world/filtwood-approved.md) and [audit](../world/filtwood-approved-audit.json). Larger-island/Malukshure choices remain pending. Historical entries follow.

## 22/11 — Single current source/painting/art review bundle

[Delivery index](../world/DELIVERY.md) integrates sourceb3189e7with artb4b8634;current mapb48666e9/normala9b6b970/353records,58paired concept IDs and the orc-camp version2selection coexist. All58tuples/heights match R127;all14normal hashes retained;source geometry exact. One missing historical art decision is appended verbatim after the existing source decision log. Older comparison text archived exactly;current comparison/index use explicit source limits and already-pending owner choices. Art-side source-old statements are marked historical for this combined checkout. No new source fact,terrain conversion,tool/mod/pack change,world apply,main merge or deploy. Umbrella branch/PR74will advance only after bundle checks. Required gate472tests/26skips/0failures in65.795s;fresh checker0errors/56relations/2warnings. Current-source parsed geometry matches normala9b6b970;22road grades pass,58local tuples/heights match art,14normal hashes and all original58PNG/sheet bytes match art tip. Preview/atlas unchanged;official reference freshly inspected. Diff check passes.

## 22/11 — Galut terraced precinct study

[Plan](../world/galut-terraced-precinct.md):retain radius60at authored(-776,2836);716dry4mcentres,current height88.6875..112.125. Three courts112/108/104,1152blocks²;lower needs up to5.06fill/4.18cut,not accepted foundations.250.39approach joins actualroadvertex(-992,2720);69.66/35.31internal links,max plannedgrade0.35632. A first barely clear route was revised for extra4planning spare;segment checks retain48coast clearance and old-site buffers. These are proposed geometric surfaces,not normal road exports or block stair acceptance. Guide capital-name and WNtrade scopes retained;location/chronology/C15/fullcity remain open. Active SVG/58sites/22roads/14normal artifacts/painting untouched;no conversion/protected edits/apply/mainmerge/deploy. Ledger353;143/42inventory not closed. Required `bash tools/check.sh` passed:472tests,26skipped,zero failures in65.738s;validation and diff checks pass. Final diagram visually inspected. All14normal artifact hashes and the active SVG remain exact;no new conversion or active-map check is claimed.

## 22/11 — Concrete conditional Filtwood forest-edge move

[Candidate](../world/filtwood-jura-edge-candidate.md) develops the existing C20comment at(-1050,600) with the unchanged8-block pin and1102-block curved woodland trail. Final ground74,new-road maxgrade0.04,dry. First direct old-well junction raised its height1;revised32west junction retains all57other site records andall22old road exports. Normal67.9s;241height centres change,water byte-exact,all13lake+8bank height inputs retained. Conditional U→Jchecker0errors/56relations/2standingwarnings;default fails precisely that binding. Ordinary generated anchors stillU,not adoptable;proposed Jregistration generated by existing functions.75-radius study1102drycentres,height73.25..74.375;not a full city. Primary kingdom/chronology retained;near-Jura secondary,westside/coordinate authored. Active source/normal/painting/anchors unchanged,ledger352/143-42inventory. No protected edits/apply/mainmerge/deploy. Required `bash tools/check.sh` passed:472tests,26skipped,zero failures in65.341s;validation and `git diff --check` pass. Conditional checker preview,normal comparison and candidate were visually inspected.

## 22/11 — Current source and painted deliverables reconciled

[Combined delivery](../world/painting-round112/README.md) integrates source d1f4882with painting7446b2b. Source-conflict resolutions choose current source files;the prior R129painting decision remains in the append-only log. Current source ledger351,143/42inventory,mapb48666e9and14byte-exactnormala9b6b970outputs accompany the original painted atlas. Native/atlas bitmaps and58numeric registrations retained;historical brushwork/height basis is explicit. New owned same-world-frame comparison makes the actual normal export inspectable beside the painting. No new AI image,reference pixels,converter run,protected implementation,active pending proposal,apply,merge-to-main or deploy. Registration open-row metadata41→42corrected against42unchanged SVGrows. Checker0errors/56relations/2standingwarnings;required gate472tests,26skipped,zero failures in65.650s. Bitmap/XML/58registration/14normal hash assertions pass;browser no overlap or clipping;preview/atlas/comparison viewed. Diff check passes.

## 22/11 — LN14 licensed trial yields two scoped primary claims

[Review](research/tensura-world-2026-11-19/ln14-public-sample-review.md): ordinary store trial button supplied B00182145939; product-code-derived B00162145939 errors. Selected rendered title/contents/opening prologue visually read. Add two scoped primary LN claims: intended Imperial route through Jura toward Western Nations; later Milim dominion south of Jura. No exact road/border/initial military state inferred. C05 remains open because chapter2/3 body passages are unread; C08/C18 keep later ownership out of the post-Kijin snapshot. Existing349ledger rows unchanged;351unique now. Inventory143/42,map,58sites,22roads,normal/atlas/art/protected paths retained. Evidence images remain private; repository contains links/paraphrases/hashes only. Required `bash tools/check.sh` passed:472tests,26skipped,zero failures;validation and `git diff --check` pass. Direct CSV audit confirms351unique records and349unchanged prior rows. No merge or apply.

## 22/11 — Frost Palace source note no longer describes the coast

Correct only `design/data/anchors.toml` Frost Palace `notes`: distinguish unchanged legacy live coordinates from the approved own-world inland target(-1530,71,-3680),land,clearing r89. Parsed TOML comparison confirms all other fields/tables exact. The converter copies notes verbatim, so earlier generated staging retains a historical coastal note; the R109 handoff now explicitly explains it. No generated file, map, terrain, runtime, live coordinate or published artifact hash changes. Existing source/normal pins remain valid for their original snapshots. Required `bash tools/check.sh` passed: validation,472tests,26skipped,zero failures. Existing converter-function check reproduces the inland target and preserves the corrected note. `git diff --check` passes. No merge or apply.

## 22/11 — Existing Eastern Plains fringe gets a geographical label

[Label/sampling audit](../world/eastern-plains-label.md):displayb48666e9;actual parsed terrain/roads/58sites and14normal outputs remaina9b6b970exact. Fresh read-only26029strict-interior samples allplains,69.125..76.6875,no wet cells. One atlas context label/leader at authored world(2400,-690);browser box has zero text overlaps. All existing atlas nonimageXML/58markers/143-42panel retained after removing only the new group and normalising displaypin. Checker preview byte-identical and sourcecheck0errors/56relations/2standingwarnings. No new terrain build. Whole plain/grain extent stays partial;ledger349adds one original-design record. Painting companion is scoped to the matching context label,not a new height reconstruction. Island/Malukshure choices remain pending. No protected/runtime/world/merge/deploy action. Required gate472tests/26skipped/0failures65.402s;validation and diff check pass.

## 22/11 — Conditional Malukshure coast/access candidate

[Proposal](../world/malukshure-coastal-access.md):existing Sainte pin8→coastal(-2320,64,1645),cape+1970.89nativeblocks²,new749-block trail.57other registration records and22old road exports exact;all23 finite grades/all13fresh lakes pass;zero native coverage gaps. Candidate2383ed5a;normal70.2s,no converter warnings. Defaultcheckerfails exactly currentH/proposedO;explicit alternate-anchor check0errors/56relations/2priorwarnings. Normal trial used--skip-check only for that disclosed binding;generated defaultanchors stillH,separate proposed registration generated by existing tool function,not hand-edited. Active map/sourcea9b6b970,staging,atlas,art and realanchors retained. Country pin≠fullcapital;no tower/harbour or initial-state acceptance. Ledger348;C14ownerchoice/C15remain. No protected/world/merge/deploy action. Required gate472tests/26skipped/0failures65.778s;validation and diff check pass;final previews inspected. Default H/O conflict is still explicitly unresolved.

## 22/11 — Reference images have individual era attribution

[Correction](research/tensura-world-2026-11-19/reference-era-attribution.md):69 regional-reference snapshot fields and5ledger locator/snapshot pairs now have per-source limits. Nine official displayed headers rechecked;no45→42,no54→50,no57→53. All5episode4images freshly viewed;earlier image3/4hashes match. Same-episode10does not prove timing against naming;later interiors and secondary images do not certify initial structures/occupancy. All image URLs,hashes,roles,confidences and application limits retained. Ledger347unchanged;C03stillWN-qualified. Required gate472tests/26skipped/0failures65.504s;validation,diff and scoped field-retention checks pass. Active sourcea9b6b970,terrain,atlas,registrations and art unchanged;no new conversion/runtime/protected/merge/deploy action.

## 22/11 — Laura headwater uses a smaller authored fall

[Correction](../world/laura-headwater-level.md):two native scalar attributes154→139;river137gives2rather than17. Sourcea9b6b970;normal67.6s,no converter warnings. All58 site records/heights and22road exports exact;all13fresh lake cases and8head diagnostics pass. Only347height and311water samples change locally;other12lake+8buffers and all site discs retained. Biome/rugged/road/site/exclusion and generated registration outputs exact;prior22-mask census adopted without repinning. Current atlas updated;nonimage XML exact. PR130painting remains plan-compatible with historical height provenance,not a new height reconstruction. LN5mountain relation reread,not a waterfall-height source. Ledger347(one original-design record);C23fluid/noise and C24still open. Separate inactivePR132must absorb this water correction if selected. Required gate472tests/26skipped/0failures65.273s;checker0errors/56relations/2standingwarnings;validation and diff checks pass. No protected/runtime/world/merge/deploy action.

## 22/11 — Regional guide reconciled with current islet terrain

The explicit `world/regions.md` deliverable now pins the current 50c27a6f source and fresh western-islet census instead of claiming the old biome PNG is unchanged. All 22 displayed biome mixes checked against exact current counts; all curated image URLs and 22 region narratives retained. Expanded inventory is 143/42; paired painting PR130 is linked. Source geometry, normal staging, site records and images are unchanged. Required repository gate: 472 tests, 26 skipped, zero failures in 65.338 seconds; validation and diff check pass. Older entries below describe their original delivery state.

## 22/11 — Western offshore illustrated rocks gain actual terrain

Three original24-vertex coast/rock/biome/Xcoverage footprints added from the directly reviewed official image;no source pixels copied. Normal67.6s;all58site exports,22road exports,lake/rivers profiles and lake+8height/water retained. Fresh22-mask census zero unassigned inland samples;21other regions exact. Ledger346;expanded inventory143/42. Exact shape/position/heights and Xgameplay assignment are interpretation. Current painting needs local rock-islet alignment. Source/diagram/atlas inspected;required gate472tests/26skipped/0failures65.543s;checker0errors/56relations/2standing warnings;normal warnings empty. Raw biome indices shift173123cells but only574 change biome name;all3islets have at least one first-air64+sample. Diff check passes. No protected/runtime/chunk/merge/deploy action.

## 22/11 — Licensed guide8.5 map finally viewed;capital labels qualified

[Direct source review](../world/guide85-source-review.md):different legal ebookjapan trial renders;unnumbered map spreadcounter4/10 inspected. Four selected records bring ledger344. Southern layout reinforced;Galutname now primary companion-guide-supported,location still open. Electronic guide prints Rondo for both Eurazania/Blumund;wiki Laura not silently merged. New C24;source text/atlas row use Carrion capital with same laura ID/geometry. No typo,novel-prose or full-guide reading claimed. C07 and city placement remain unresolved. Private source images only,links/paraphrases in repo. Initial gate472tests/26skipped/0failures65.175s;map checker0errors/56relations/2standing warnings;preview/atlas inspected. Follow-up licensedLN1/guide13.5reader access recorded without verifiedDwargon passage/country-body pages or new facts;C03/C24 stay open. Final follow-up gate472tests/26skipped/0failures65.505s;diff check passes.

## 22/11 — Laura head drop traced to remaining-reach cap

[Source/profile review](../world/laura-waterfall-review.md) separates the authored17-block transition from canonical waterfall scale. Existing371-sample profile starts137 because63+2*floor(1480/40)=137;38reaches. Twenty official episode stills and6PV announcement images inspected,no broad waterfall confirmation;official PV playback country-restricted,zero frames. FAN-009 remains secondary and its action is qualified. No geometry/export/runtime change;C23 open. Required gate passed:472tests,26skipped,zero failures in65.284seconds;diff check passes.

## 22/11 — Frost Palace briefs match the approved inland map

Correct two stale round28 headers in the knowledge-pack and lore place pages: current own-world anchor(-1530,71,-3680),clearing,r89; coastal/Lerfing placement is historical. Link the existing R109 implementation and registration. The 85x69 model is an entrance,not a whole-palace footprint. WN central-continent support remains distinct from unread LN agreement. No new map/site/terrain/art/runtime change or live integration claim. Existing source/export evidence is retained without another terrain run. Required repository gate passed:472tests,26skipped,zero failures in65.152seconds;validation and diff check pass.

## 22/11 — Licensed English LN1 cave passages directly read

Requiredgate472tests/26skipped/0failures65.042seconds;diff/protectedchecks passed.

Tapas official serialization/notice identifies first5serialized episodes free,later paid. Selected PartThree/PartFour primary text now directly supports natural hipokute/high-local-magic and the interior water encounter,with blind-narrator lake inference qualified. Add LN01-CAVE-001/002;ledger340. No completeLN1/LN6/series read or printed page invented. Local TapasGET403;public index primary text readable,no bypass/unlock. DivineTree follow-up remains unverified:GC LN6fragment not tree passage;YenPresslisting metadataonly;Google metadata429;normalPlayreader redirects regional-unavailable. ElminePNG inspected fullresolution as lower-trunk vignette,not fulltree proof. Lore/knowledge/Juraguide and source-access notes updated;no source map,terrain,art,runtime/protected/merge/deploy change. See licensed-ln1-cave-followup.md in current research directory.

## 22/11 — Galut dry-circle proposal explicitly requires redesign

Requiredgate472tests/26skipped/0failures in65.109seconds;diff/protectedchecks passed.

The old inert(-900,3050),r60proposal intersects Ulgr brook,has39.959coast-edge clearance(<48)and43.625sampled relief. Marked requires-redesign without active XML change. Declared dry-centre search has1709.82blocks²space,104sampledcentres;best sampledrelief23.4375withonly0.263coastslack. No replacement accepted,smaller radius or whole-capital impossibility claimed. WN61L45directly supports Sarion trade;Galutname/location remain wiki-qualified. Source a5e1c2f6 comments only,active export0b8bcf56 retained;checker0/56/2andpreview byte-identical. Ledger338;inventory142/42 unchanged. Current pairedpaintingPR122alreadyincludesColeus,andguidecompanionlink refreshed without new bitmap. See world/galut-site-review.md. No protected/runtime/world/chunk/merge/deploy action.

## 22/11 — Coleus receives actual surrounding dune relief

Official linked PV WuIDVoKdVGU viewed privately at14 sampled frames;00:25 shows caravan dunes,00:08 corroborates the already-recorded hill palace. Four later seeks failed;no full episode/continuous trailer claim. New original22-vertex northern dune inside existing desert selector changes661height samples,max11.25,actualcrest81.5 (110iscontrolonly). Source0b8bcf56;normal67.5s;checker0errors/56relations/2standingwarnings;requiredgate472tests/26skipped/0failures65.253s. No site-disc or13lake+8buffer height changes;all58site exports retained;biome/water/road/site/exclusion/rugged PNGs unchanged. Ten westerncaravan profile heights shift<=0.09,all22grades<=0.5. Native atlas terrain image updated;all nonimageXML retained. Current region guide/ledger337 updated;inventory142/42 unchanged. Existing painting needs local dune alignment;all place-art numericregistrations remain applicable. Source/section/preview inspected. No protected/runtime/world/chunk/merge/deploy action.

## 22/11 — Larger island coast trial fits without relaxing box limits

Verification:472tests/26skipped/0failures in65.277seconds; checker0/56/2; preview byte-identical and original fit diagram inspected.

PR120 follow-up: trialB keeps41.5%/32.5%mainland-relative island widths and shifts both600blocks west. Nearest mainland sea927.76/961.91; box13824×11264 fits hard14336×11264. TrialA’s height overrun is not universal. Selected unchanged three site discs and four relief/rock selectors remain contained; all internal-layer/era/bearing acceptance is not claimed. Both coast proposals remain SVG comments because smaller recommended island sizes still differ. Current source9dbec534 changes comments only; active XML and preview remain identical to R130. Original normal/painting/art pins are retained without a new export. Ledger335, no new canon claims. No protected/runtime/world/chunk/merge/deploy action.

## 22/11 — Relative island size conflict drawn for review

An original side-by-side coast study now shows remaining Ice/ElDorado compression against broad official-image extent. Active widths25.22%/24.04%ofmainland; chosen inert trial41.5%/32.5%. Commented original paths in map.svg alter no active element, site, road or terrain layer. At1000-block mainland sea gaps this trial requires13312×12288 including sea margins, exceeding hard height11264 by1024. This does not prove every rearrangement impossible. See world/island-proportion-review.md. Fresh checker0errors/56relations/2standingwarnings; preview byte-identical and inspected. Required gate472tests/26skipped/0failures65.313seconds. Ledger335; no duplicated canon dimensions. Original R130 normal export and existing painting/art are adopted for identical active geometry; their original hashes remain. No protected/runtime/world/chunk/merge/deploy action.

## 22/11 — Qualify four-state anime evidence

The current guide and two legacy lore entry points now distinguish the community-reported Morgdahl/Nostraille/Yuzalgh/Yggdonia order from an authenticated anime frame. Existing FAN-WES-034 and SITE records retain their original confidence; no duplicate facts or new geometry. All four current marker x coordinates already follow the reported order. The official introductory image remains broad context; all 69 current curated image links and all 22 regional sections remain. See docs/research/tensura-world-2026-11-19/western-country-evidence.md. Source SVG ade50210 and existing preview/painting/art remain unchanged. A readable attributed frame or direct LN/manga passage is still needed for stronger geographic claims. Required repository gate passed (validation and fast unit tier); see the PR for the exact result. No protected path, runtime apply, chunk generation, merge or deployment.

## 22/11 — Ulgr head step reduced;regional guide reconciled (R130)

[Current review](../world/ulgr-spring-level-r130.md) changes only spring/head102→92,keeping plan geometry andall58 site records/heights. First interface11→1;existing91→63 river reaches remain exact.693 height/509 water samples change,max10blocks;steeper wooded bowl is shown in the measured section. All13 lake cases and202 wet route samples pass;head diagnostic7/8 with Laura17 open. All22 road profiles meet1:2 (1e-6 tolerance),no vertical duplicates. Normal67.5s. Current regions guide shrinks111009→57746chars,retaining22 narratives/69 curated image links andadding explicit interpreted mood. It fixes stale coastal-palace prose,El Dorado dimensions andinline biome snapshots;R128 census adopted by exact biome/region equality. R129 painting andR127 art values remain applicable within their scope without a counter-only image refresh. [Deliverable audit](research/tensura-world-2026-11-19/delivery-review-r130.md). Ledger333/inventory142/42;broader source/contract/era gaps remain. No protected implementation or live apply. Required gate: 472 tests, 26 skipped, zero failures in 65.094s; validation and diff check pass.

## 22/11 — Ice Continent western arm reshaped (R128)

[Source/export review](../world/ice-west-arm-r128.md) replaces the broad northwest shoulder with five original lower-arm cubic reaches;other77 shore nodes and all overall bounds retained. Only coast/snow selector/I mask change. Source8c41e924; all58 site attributes/heights and22 road courses retained,including Yasuke’s approved inland palace at71. No changed height sample inside a site disc or lake+8bank neighborhood. Normal67.6s;checker0errors/56relations/2standing warnings;all13lake cases pass. R127 art values remain applicable without another metadata copy. R126 painting needs actual ice-arm alignment. Ledger332;inventory142/42. No protected implementation or live apply. Required gate: 472 tests, 26 skipped, zero failures in 65.431s; validation and diff check pass.

## 21/11 — El Dorado island proportion corrected (R125)

[Source/export review](../world/el-dorado-coast-r125.md) replaces a narrow diagonal island with a broader original coast informed by the official silhouette. Only islandcoast/Xmask change;all58site attributes/22courses retained. Sourcea637;normal67.5s;checker0errors/56relations/2warnings;all13lake audits pass. City/volcano stagedfirst-air72→73/196→197;only corresponding volcanic-way height profile changes,maxgrade stays0.5. R124painting needs actual coastline alignment andtwo historical concept-registration elevations need review. Ledger330;inventory142/42. No live apply or protected-file edit. Required gate: 472 tests, 26 skipped, zero failures in 65.006s; validation and diff check pass.

## 21/11 — Amrita association visible on atlas (R123)

[Atlas/source review](../world/amrita-atlas-r123.md) adds a below-castle48 callout while marker49 remains the game reservation. LN10-001 is refined from the reread publisher prologue; the brief’s exact founding age is qualified, not disproved across the full novel. Ledger328 retained. Source4093, all58 sites, checker preview and terrain exports unchanged. C07 nesting/access remains open; painting continent remains aligned, its caption follow-up remains pending. Required gate passed:472 tests,26 skipped,zero failures in64.023s; validation and diff check pass.

# Current handoff

## 21/11 — Initial-era place briefs reconciled (R121)

Ten targeted narratives now separate the S1E10 post-Kijin instant from later outcomes: village/new Kijin workshops, former Kaijin premises, old goblin template occupancy, Falmuth/Farmenas, unresolved Orc invasion, lizardman allegiance/naming, Englassia teaching, Clayman raid, Coleus mission and the earlier Dwargon court visit. Thirteen Jura headers no longer imply an already formed federation. Knowledge-pack/lore guides link the priority snapshot policy. All58 state-overlay IDs/state categories remain; four notes/bases clarified. Full58 narrative/concept/architecture review remains unproved.

Official episode5/6/9/10/11 synopses reread; three new event/location records and one explicitly secondary Abiru naming record. Ledger328;inventory142/42. All map/site/preview/atlas/terrain artifacts remain byte-identical to R119/source4093; R120 painting PR108 remains aligned and is adopted without another image/counter copy. No source SVG edit, tools/mod/pack change, runtime spawn/quest action, world apply, chunks, main merge or deploy. Remaining source gaps, proportions, concept/initial architecture and C23/C18 implementation boundaries remain open. Required gate: 472 tests, 26 skipped, zero failures in 63.649 seconds; validation and diff check pass. No new terrain build/checker run is claimed for unchanged source. Branch chatgpt/initial-era-briefs-r121 is stacked over the R119 source branch.

# Current handoff

## 21/11 — Ulgr brook now descends inland to shore (R119)

Only ulgr-spring-brook points change in source `4093f844`; all other native attributes/text, 58 sites and 22 roads remain. Old line: 53.25 blocks land / 305.43 offshore. New route: 577.63 wholly inland, native-shore mouth. First exported difference reduces 37→11 blocks; Laura 17 unchanged. All 202 river wet sample centres connect cardinally to the spring; finite mouth continuation samples are below sea level 63. All 13 lake bank/contact cases and eight designed links pass. No final-noise or Minecraft fluid acceptance claim.

Normal staging: 66.4 seconds, no converter warnings. Checker: zero errors, 56 relations, two prior warnings. Height/rugged/water/biome changes: 1729/785/220/4 cells; maximum height delta 44.875 blocks, none inside any site disc. Road/site/exclusion PNGs and site/road/anchor exports are byte-identical. R119 census covers all 22 masks with no unassigned inland sample. Art reservations remain; R118 painting needs exact new brook alignment. Ledger 324; inventory 142/42. WN61 park doorway passage reread; route and numerical heights remain our interpretation. C23 style/fluid, source coverage, proportions and initial era remain open. No protected implementation, world apply, chunks, main merge or deploy. Required gate: 472 tests, 26 skipped, zero failures in 63.829 seconds. Read-only connectivity passes; the two flagged head transitions remain a separate diagnostic, not a failing repository gate. Branch chatgpt/ulgr-brook-r119 is stacked over the R117 source branch.

# Current handoff

## 21/11 — Southern mainland taper follows official silhouette (R117)

Source `5938a823` replaces the broad southeastern foot with five original cubic coast reaches. B/H masks and the Eurazania forest follow the new shore; all other native attributes/text, 58 sites, 22 roads and water/relief shapes are retained. Normal staging: 67.0 seconds; no converter warnings. Checker: zero errors, 56 relations, two prior warnings. Native land loss: 819,604.48 square blocks; no added land. Height changes affect 172,196 cells (max 92.4375 blocks), outside all site discs. Water/road/site/exclusion PNGs and site/road/anchor exports are byte-identical. R117 census measures all 22 masks with zero unassigned inland biome samples. Atlas browser check: 58 numbers, 20 labels, 42 rows, no overlaps, minimum spacing 31.62 pixels.

The approved inland palace remains. C23 stays open; the old lake/contact evidence is retained through identical water. R113 place-art reservations remain valid; R116 painting now needs actual southern silhouette alignment. Ledger 323; inventory 142/42. Orbic/Ulgracia category enumeration remains inaccessible; do not claim complete source coverage. Global proportions, initial-era semantics and runtime integration remain open. Required gate: 472 tests, 26 skipped, zero failures in 64.173 seconds. This correction is delivered on `chatgpt/southern-coast-r117`, stacked over `chatgpt/world-map`; the existing base map/painting PRs retain their earlier snapshot. No protected implementation, world apply, chunks, main merge or deploy.

# Current handoff

## 21/11 — Lake banks and two source contacts (R115)

Source `89b01c4c` moves only the Ulgr/Laura first river vertices 2/6 blocks north, remaining on land. All 13 lake bank/depth checks pass; the two missing plan contacts are repaired, giving 8/8 designed connections. Normal staging took 67.0 seconds without converter warnings; the checker reports zero errors, 56 relations and two prior warnings. Changes affect 188 height, 247 ruggedness and 26 water cells. Height deltas range from −41.375 to +41.3125 blocks at moving cliff cuts, outside all site discs. Roads, biomes, sites, exclusion and site/road/anchor exports are identical. Adopt the unchanged R114 biome census and R113 art reservations. Ledger: 321; inventory: 142 with 42 physical follow-ups. Required gate: 472 tests, 26 skipped, zero failures in 64.793 seconds.

C23 remains a style/source and technical review: adjacent lake/river export differences are 37 blocks at Ulgr and 17 at Laura. The two-block diagnostic is not an owner-defined cap. Assess waterfall character and fluid placement; do not create artificial routes just to satisfy that threshold. Bank/contact results do not establish final terrain or in-game fluid acceptance. Painting R116 is published at `b5a2fa4124ba2732f43a6bd11157d3e436f025e3` in PR102 and follows both exact native head updates. Its continent pixels are unchanged at atlas scale; the atlas legend correction is visible. Gate: 472 tests, 26 skipped, zero failures in 64.817 seconds. Visual review also found a stale coastal description in atlas legend row 54; it now reads Frost Palace inland clearing, matching the approved registration. Other source, proportion and era checks remain open. No protected implementation, world apply, chunk generation, main merge or deployment action.

# Current handoff

## 21/11 — Map deliverables and art registration reconciled (R114/R113)

Source2463d771/mapbf0ba98 andart8d468a2 published. Only Frost Palace sheet changed;all58 image/sheet pairs andnumeric fields checked,57 other sheets/all58 PNG bytes/exact palace prompt retained. Source local rock-cone choice is interpretation;LN11 sample routes exposed no story. R112 painted rock appearance adopted unchanged,its original source metadata remains historical. Source gate472/26skip/0fail64.499s;art gate462/26skip/0fail44.459s;main handoff gate472/26skip/0fail64.428s. See art-registration-r113.md anddeliverable-readiness-r114.md in current research directory. Next substantive checks:all13 lake banks as one audit;Orbic/Ulgracia child-location traversal;global proportional/contract andinitial-era review. Keep Claude-owned runtime/whole-city building separate from creative map acceptance. No new geometry orcounter-only painting/art generation in this handoff;no protected/runtime/merge/deploy action.

# Current handoff

## 21/11 — Local rocky cone and place-sheet audit (R114/R113)

Source2463d771 adds only one stony_peaks polygon over the exact existing40-vertex El Dorado cone.4577biome samples change(3039plains+1538snowy_slopes);all5850cone centres stony_peaks. All height/rugged/water/road/site/exclusion andsite/road/anchor exports retained;all58site attributes/22routes unchanged. Checker0/56/2;normal67.0s,no warnings. Required gate472/26skip/0fail64.499s;browser58/20/42,no overlap,min31.62px. Ledger318;inventory142/42. Local authored rock choice,not proven canon climate or runtime snow absence;LN11 retailer routes exposed no story passage. Existing R112 painting appearance adopted unchanged,its metadata stays historical. R113 art audit:57 numerical sheets already matched,only Frost Palace’s inland registration corrected;all58 PNGs andoriginal prompt retained. Full goal stays open;next map deliverable checks are in readiness audit,distinct from Claude-owned runtime/full-build integration.

# Current handoff

## 21/11 — El Dorado woodland source/painting aligned (R112)

R111 source74d63267/map6c9ece1 and R112 painting dfd66c1 agree. Exact72/60canopy clips,35 original scattered trees;759 changed continent pixels,maxRGB115,all inside16block support;exterior pixels identical. All58 marker groups/20context names/42open rows retain geometry;browser min32.47px,no label overlap. Native historical component metadata retained;only current root metadata refreshes. Gate472/26skip/0fail65.464s;source gate64.832s;sourcechecker0/56/2 andnormal67.0s adopted. Main handoff gate472/26skip/0fail64.731s. Ledger316;inventory142/42 unchanged;census reproduces byte-identically. No further canopy geometry correction found. Source/native volcano climate mismatch remains for source-first review;also reassess outstanding map-deliverable requirements separately from Claude-owned runtime/full-build tasks. No protected edit,world/chunk/main-merge/deploy action. Older dated notes below are history.

# Current handoff

## 21/11 — El Dorado source woodland restored (R111)

Fresh official original and enlarged island inspected;NW woodland and east/southeast lakeside group missing from source. First eastern northern draft corrected before delivery. Added72/60-vertex light-forest polygons;all old shape attributes/text,58 site attributes,22 roads retained. Source74d63267;checker0errors/56relations/2priorwarnings;normal67.0s/no converter warnings.4,788 biome cells become forest inside new polygons;all height/rugged/water/road/site/exclusion rasters and site/road/anchor exports identical. X measured forest5.3940%;no stale20% target. Required gate472/26skip/0fail64.832s;browser58/20/42,no overlaps,min31.62px. Ledger316;existing El Dorado inventory row gains evidence,142/42 classifications unchanged. R110 painting needs exact new canopy integration;source height/volcanic snow versus painting is a separate remaining review. No protected edit/runtime action.

# Current handoff

## 21/11 — Inland palace painting synchronized (R110)

R109 source0ae040ec/map5026a0d and R110 painting e3963e2 agree. Painting PR102 visibly moves only marker54 and its pointer;exact native forecourt follows,all other57 groups/20names/42rows retained. Continent pixels stay identical at this scale;no global height claim. Gate472/26skip/0fail64.953s;browser min32.47px/no labels overlap. See docs/research/tensura-world-2026-11-19/painting-alignment-r110.md. Owner’s inland choice is implemented in drawing and generated kind/r registry;staged y71/live anchor/build/runtime integration stays with Claude. LN agreement/complete palace/access remain open. Ledger314;inventory142/42. Main handoff gate472/26skip/0fail64.991s;architecture brief records owner override. No geometry/counter/art change in this handoff. Next substantive check: El Dorado illustrated woodland versus actual terrain;do not blanket-fill stale20%target. All previous dated status notes are historical.

# Current handoff

## 21/11 — Owner-approved inland Frost Palace (R109)

Owner answered inland palace and adjust coastal registration. SVG site54 now(-1530,-3680),clearing,r89;local forecourt and label follow. Other57 sites and all native geography masks remain. Checker0errors/56relations/2priorwarnings;normal67.3s/no warnings;8585 entrance-buffer samples level71,no water. world/frost-palace-inland-r109.md and exact generated table provide Claude’s integration handoff. Owner-approved generator updates only Frost Palace kind/r and its size row;live anchor/y/build/runtime integration remains with Claude. Do not apply the world here. C22 owner choice resolved; LN agreement,complete palace/access/runtime remain open. Required gate472/26skip/0fail65.002s;stale generated coastal-table failures corrected with existing generator. Ledger314;inventory142/42. Current measured shares are R109;R108 stays historical. R107 painting needs site/forecourt re-registration before called current.

## 21/11 — Region prose matches actual designed biomes (R108)

[Reproducible native-region biome census](../world/region-biomes-r108.md) replaces22 obsolete target mixes in regions.md with107 measured region/biome rows.22 original targets preserved as history. The fixed200-block ancient core occupies about2.4% of J,not the old20% target; do not resize protected rings to chase a stale proportion. All percentages describe native gameplay masks,not sovereign country climates. Converter river/beach IDs are automatic,not hand-SVG biome instructions.

Four-block census assigns2,693,557 non-ocean samples,with26 exact-boundary ties deterministically resolved. No native-inland non-ocean sample lacks a mask.9,444 outside-coast non-ocean samples (mostly raster beach edge/river mouths) are separately reported rather than inventing country extent. CSV/JSON reproduce byte-identically; source/raster hashes pinned.313 ledger unique (one new design-census record),142 inventory/42 physical unchanged. Mainland coverage summary and stale C12 dimensions corrected to current9983x6250; fields/confidences complete but not full source verification. Horn exact-name search still yields no usable identity/geography; no absence-from-canon conclusion.

Source b2750950,all58 sites/22roads,normal rasters,previews and R107 painting unchanged. No new checker/converter/image run required. Gate472tests,26skipped,zero failures(64.484s); validation,zero changed JavaScript,diff and data invariants pass. R107’s312 ledger figure is its source-commit snapshot; the new census record does not make the painting stale or require a counter-only art round. Source and art remain aligned.

Next concrete fidelity check: X has no explicit forest-biome category despite an old forest target; inspect El Dorado’s official illustrated tree cover and the native painting against actual terrain before deciding on forest boundaries. A plains biome does not itself prove zero trees; do not add blanket forest to achieve20%. Other source/location/initial-era/physical obligations and C22 owner placement choice remain open. No protected edit,biome/terrain/region change,world apply,structure generation,merge or deployment.

## 21/11 — Published painting follows southeastern landscape (R107)

[Current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/e28b579/world/painting-round107/README.md) follows source `b2750950`:exact36 lake/66 woodland vertices,55 original clipped tree symbols,2213 changed continent pixels and all58 registrations checked.20 names/42 rows,caption142 andledger312 agree. Milim orientation text follows the source southward move; other text/number geometry retained. R105 is historical; painting alignment is complete. [Evidence](research/tensura-world-2026-11-19/painting-alignment-r107.md).

Painting e28b579 gate472tests,26skipped,zero failures(65.227s); source checker0errors/56relations/2prior warnings. Main documentation gate472tests,26skipped,zero failures(64.716s); zero changed JavaScript. Main geometry/terrain remains unchanged from b0e38d0. Broader source/geography/physical/initial-era obligations remain open; C22 owner choice pending. No runtime action. Next: substantive remaining requirements,not repeated alignment/counter/gate work without changed geography or a new failure.

## 21/11 — Southeastern water and woodland restored (R106)

[Source/terrain review](../world/southeastern-water-wood-r106.md) restores the official illustration's unnamed southeastern water and woodland to its north/northwest. Exact36/66-vertex outlines,positions,level68/depth4 and light tree choice are interpretation. A wrong-side preliminary forest draft was corrected after direct image reinspection. Source `b2750950`; checker0errors/56relations/2prior warnings; normal67.7s. All previous XML and58 site/22 route exports retained exactly. No apply.

Lake4406core cells allwater68; designedbed64..66.75 (rim taper). Height/water each change4406cells inside the new lake; biome14122inside new features;rugged5041within8.92blocks. Lake/woodland gap6.58;nearest site edge497.03. Atlas58 numbers/20 names/42 rows browser-checked without overlap;minimum number spacing31.62px. Milim orientation moves south y1344.23->1395 to clear the water; all other text/number geometry retained. Panel metadata fixed from stale138 to142 along with visible caption142/42. Ledger312/inventory142 retains every prior row/classification and42 open physical follow-ups.

Required gate472tests,26skipped,zero failures(64.959s); validation,zero changed JavaScript,diff/source/XML/count checks pass. Preview,atlas/detail and original before/after inspected beside official reference. R105 painting/source e785c2b0 now predates these two features and142caption; next substantive task is PR102 alignment to R106 using exact lake/woodland and current terrain while preserving the native composition/58 registrations. Do not call R105 current after this geography change. C22 owner choice remains pending; other source/initial-era/physical obligations open. No protected edit,generated structure,world/chunk action,merge,deploy or in-game acceptance.

## 21/11 — Published painting follows western water (R105)

[Current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/8b4bbf6/world/painting-round105/README.md) follows source `e785c2b0`:exact40 lake/36 outlet vertices,1304 changed continent pixels and all58 registrations checked.20 context names/42 open rows,caption140 andledger310 agree. Blumund orientation text clears the painted projection with an explicit20px east layout adjustment; no place moves. R100 is historical and painting alignment is complete. [Evidence](research/tensura-world-2026-11-19/painting-alignment-r105.md).

Painting commit8b4bbf6 gate472tests,26skipped,zero failures(64.430s); source checker0errors/56relations/2prior warnings. Main documentation gate472tests,26skipped,zero failures(64.256s); zero changed JavaScript. Main source/terrain geometry remains unchanged from b36f284. Broader geographical/source/initial-era/physical obligations remain open; C22 owner decision pending. No world apply or runtime action. Next: substantive remaining map/source work,not another alignment/counter round without changed geography.

## 21/11 — Western illustrated basin restored (R104)

[Source/terrain review](../world/western-basin-r104.md) adds an original unnamed western lake and southwest outlet after direct visual comparison with the official introductory illustration. Source `e785c2b0`; 12 lakes/9 rivers. Checker0errors/56relations/2prior warnings; normal staging67.6s. Existing58 exported site records and22 route records remain byte-identical; all previous XML retained. Height changes7203cells within5.61blocks of new water; water/biome change6739cells inside it. Explicit inland water plus implicit sea are four-neighbour connected. No world apply.

Ledger310(252+58),inventory140/42 physical follow-ups: two unnamed terrain records added,all previous classifications retained. Atlas20 context names/58 numbered groups/42 open rows verified; only terrain/source/caption and Blumund orientation text position change. Browser text/number clearance≥10.09px; number spacing31.62px; no label overlaps. Fresh previews inspected. [Current source comparison](../world/comparison.md) is concise; previous narrative is preserved in comparison-history-r103.md. R100 painting/source dbef5ac0 is now historical and requires alignment to the new water and140-entry caption. Original art remains unchanged.

Required repository gate472tests,26skipped,zero failures(64.727s); validation and zero changed JavaScript passed. Source/hash/XML/registration/continuity checks and diff check passed. Next substantive task: align PR102's painting with R104 source using the actual lake/outlet and terrain,retain the current composition and58 registrations; do not claim R100 current. C22 owner choice remains pending,not approved by elapsed time. Whole-map source/era/physical obligations remain open. No protected implementation change,generated structure,chunk generation,merge,deploy or in-game acceptance.

## 21/11 — Frost Palace current-terrain alternatives (R103)

[Original comparison and reproducible survey](../world/frost-palace-fit-r103.md) finds76.22 blocks of relief under the old inert centroid proposal and1.96 under an alternative at(-1530,-3680),185.41 blocks from the current island centroid. All8585 buffered entrance-column centres sampled; trial floor71 has at most1.435 blocks height difference. This is the existing entrance model,not a full palace or runtime fit proof. Current coast already includes site preparation; rectangle89-radius budget does not mandate enlargement.

Yasuke was asked to choose inland palace,coast arrival plus inland palace,or await LN confirmation; response pending. C22 current coast contract remains unchanged. No dependent active map/data edit. Source `dbef5ac0`,58 sites,22 roads,terrain,R100 painting andinventory138/42 retained. Ledger308 unique(250+58); new row is original design interpretation. Required gate472 tests,26 skipped,zero failures(63.753s), validation and zero changed JavaScript passed; SVG/PNG inspected,source hash and sample/count assertions passed. No new converter/checker run needed for this inert study.

Next: apply the owner's placement choice when received,then resolve actual site kind,preparation,local forecourt/access and whole-palace scope through the permitted creative/technical contract. Do not simply activate the steep old centroid or duplicate site IDs. Other source/geography obligations remain open; no generated structure,world apply,merge,deploy or in-game acceptance.

## 21/11 — Council capital source and anime references (R102)

[Primary-source review](research/tensura-world-2026-11-19/council-capital-source-r102.md) adds WN139-COW-102: a later Council meeting in Englassia royal capital, beyond earlier country-only evidence. OFF-COW-102 records limited visible interior cues from official episode77 still1; all five gallery originals were individually viewed and retained privately. Permanent headquarters, exact parcel and S1E10 state remain unverified. The Council physical task stays missing and distinct from guild/academy/castle.

Ledger307 unique(249+58); inventory138/42 unchanged. Source `dbef5ac0`,58 sites,22 roads,terrain and R100 painting retained. No active SVG edit or new map/terrain check required. Gate472 tests,26 skipped,zero failures(63.818s); validation and zero changed JavaScript passed. Doran searches do not supply reliable geometry; C22 central-WN-palace versus coastal-site conflict remains unresolved. Next: source-backed geographical or initial-state work; Council room references now support a separate original design after footprint/era review. No generation,world apply,merge,deploy or in-game acceptance.

## 21/11 — Ballachia initial-era correction (R101)

[Source review and original comparison plan](../world/ballachia-initial-r101.md) correct the later rescue narrative and unsupported establishing-frame claim in Ballachia's lore. Ten licensed episode65 frames were individually inspected and retained privately; the publisher review names Ballachia but supplies no capital/border survey. The current reservation is (-2450,-450), radius68, gameplayG; the old Lerfing survey is historical.

An unregistered creative candidate outside `blueprints/` replaces exactly142 blocks:80 partition blocks to air,16 western-wall blocks to bricks,46 memorial paving blocks to the existing plaza palette. All other voxels match; bounds and repeated-build determinism checked. Original blueprint/generated structures, map/terrain/painting/art stay unchanged. Claude still owns generation, registration and in-game acceptance. Ballachia stays partial; ledger305/inventory138/42 unchanged. Current painted atlas remains R100/source `dbef5ac0`.

Repository gate: **472 tests,26 skipped,zero failures (64.150s)**; validation and zero changed JavaScript checks pass. `git diff --check` passes. No runtime action. Next: remaining source-backed physical/initial-era requirements; do not treat this neutral precinct proposal as verified kingdom extent or capital.

## 21/11 - Published painting follows Tengu terrain context (R100)

[Current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/260f1501ad0a009879b671291fd0e73b63fef497/world/painting-round100/README.md) follows source `dbef5ac0`: exact meadow shape,15 changed continent pixels,20 context names and all58 registrations checked. Khusha text and the Tengu partial row now agree with the main atlas. R98 is historical; painting alignment is complete. [Evidence](research/tensura-world-2026-11-19/painting-alignment-r100.md). Ledger305/inventory138/42 remain. Painting gate472 tests,26 skipped,zero failures(63.658s). Main documentation gate: 472 tests, 26 skipped, zero failures (63.549s); zero changed JavaScript. Broader source/location/initial-era obligations stay open.

## 21/11 - Tengu ridge gains partial terrain context (R99)

[Current glade/access review](../world/tengu-glade-r99.md) adds a small authored meadow selector on the existing Khusha ridge: 43 dry biome cells; all height, site, road, water and other normal exports retained. The proposed surface path fails endpoint registration and remains inactive under C15, with natural grade0.612 requiring future design. All58 sites/22 roads remain; atlas20 context names. Tengu becomes partial, with inventory138/42 still open; ledger305. R98 painting needs biome/context alignment. Checker0errors/56relations/2prior warnings; normal67.3s. Repository gate: 472 tests, 26 skipped, zero failures (64.356s); zero changed JavaScript.

## 21/11 - Published painting follows the western coast (R98)

[Current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/e9cf188ea08d0306d4803de7f2a75ceb9f8cf5b6/world/painting-round98/README.md) follows source `bb0e4b29`: exact mainland boundary/four biome shapes, 3,201 checked texture triangles and 32,050 checked height-light samples. All 58 registrations, 19 names and the 138/42 panel retain layout. R95 is historical; western painting alignment is complete. [Alignment evidence](research/tensura-world-2026-11-19/painting-alignment-r98.md). Painting gate: 472 tests, 26 skipped, zero failures (63.532s). Main documentation gate: 472 tests, 26 skipped, zero failures (63.304s); zero changed JavaScript. Broader source/location/initial-era obligations remain open.

## 21/11 - Western peninsula follows the illustrated outline (R97)

[Western coast review](../world/western-peninsula-r97.md) restores the western lobe beyond a shortened northwestern headland. Source `bb0e4b29`; mainland9983x6250/design12800x10752; checker0errors/56relations/2prior warnings. The wider10443 trial failed the repository width gate and remains an inactive C12 alternative. Normal66.5s; all58 XML site attributes retained. Heaven Tower staged ground71to73, with bounded road-profile changes. Atlas58/19/42 retained; ledger304/inventory138/42. R95 painting needs alignment. Repository gate: 472 tests, 26 skipped, zero failures (63.383s); zero changed JavaScript.

## 21/11 - Western country identity review (R96)

[Source review](../world/western-country-identity-r96.md) adds official manga-release evidence that Gaston/Ghastone is a named kingdom. The western-state listing remains wiki evidence; the English crosswalk is qualified. Rostia profile reread adds no spatial claim. Neither country's capital or boundary is verified; G/A gameplay bindings do not establish sovereign membership. Five official episode72 stills were reviewed without extracting geography from an unidentified tabletop model. Later events/characters are not backdated to S1E10.

Ledger302; inventory138 and42 physical follow-ups unchanged. Source `63df7185`, all58 sites, terrain/painting/PNG/prompt records retained. Current painting remains R95. Repository gate: 472 tests, 26 skipped, zero failures (63.711s); zero changed JavaScript. Next: source-backed spatial/initial-state work on the open physical inventory; no runtime action.

## 21/11 — Published painting follows Ice coastal source (R95)

[Current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/02ac2f8231e5712505df3bde787e03ee949b5d47/world/painting-round95/README.md) follows source `63df7185`: five exact source coasts, 1,869 checked height-light samples, all 58 registrations and 19 context names. Caption138/42 and ledger301 agree with current source scope. Painting gate472 tests,26 skipped,zero failures(63.796s). [Alignment evidence](research/tensura-world-2026-11-19/painting-alignment-r95.md). Earlier pending-painting notes below are historical. Main documentation gate **472 tests, 26 skipped, zero failures (63.631s)**; zero changed JavaScript.

## 21/11 — Illustrated Ice offshore group added (R94)

[R94 source/terrain review](../world/ice-islets-r94.md) adds five original representative islet coasts with cold biome/admin coverage. Source `63df7185`; checker 0 errors/56 relations/2 existing warnings; final normal66.687s. Every old land height/biome/ruggedness and58 reservation is retained. Atlas:19 names,138-entry caption,42 open rows. Ledger301. R93 painting source43fed303 predates the islets and requires alignment; numeric58 registration remains valid. Required repository gate: 472 tests, 26 skipped, zero failures (63.298s); zero changed JavaScript.

## 21/11 — Empire source and initial-era distinction (R93)

[Source/era review](../world/empire-chronology-r93.md) corrects the Nasca lore handoff and records qualified capital/history/later-development evidence. Ledger299; inventory137 includes one future-only town, with42 physical follow-ups unchanged. All58 reservations,18 context names and actual terrain remain unchanged. The atlas caption is137; the R92 painted geography remains valid. [Current painted caption](https://github.com/Yasuke2000/ocs-two-lives/pull/102) is a separate presentation update. Required repository gate: 472 tests, 26 skipped, zero failures (64.404s); zero changed JavaScript.

## 21/11 — Current painting follows Englassia water (R92)

[Published painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/8e47ccbef3a8f0bc36caef3a4bb4d8b01cfa2e7c/world/painting-round92/README.md) now follows R91 source `43fed303`:58 unchanged registrations,18 context names,136-entry caption and42 open physical rows. Exact lake/court vertices and22 native road records checked; WN/continuity/initial-construction limits remain. Painting gate472 tests,26 skipped,zero failures(64.466s). [Alignment evidence](research/tensura-world-2026-11-19/painting-alignment-r92.md). Main documentation gate **472 tests,26 skipped,zero failures (64.586s)**; zero changed JavaScript.

# Handoff — current state of the work (update this when you stop)

## 21/11 — Englassia capital water reconciled with dry precinct (round91)

R91 [Englassia capital-water review](../world/englassia-lake-r91.md) adds a separately placed WN-derived lake and dry court, one northern land access and three short water crossings. The existing academy/Guild precinct and all 58 reservations remain. Source `43fed303`; 22 roads, 11 lakes, 18 context names; ledger 294 and inventory 136/42. The castle and full capital remain incomplete. R90 painting predates the new local water/roads and needs alignment.

Checker 0 errors/56 relations/2 prior warnings; normal50.942s without warnings. All new water cells are below level70 in one connected basin; all registered plate heights and flat-site JSON records remain. Final comparison/source preview/atlas reviewed. Gate: 472 tests, 26 skipped, zero failures (66.962s); zero changed JavaScript. Next: painted water/road integration; remaining capital/source/era/registration work. No runtime action.

## 21/11 — Painting aligned with current Khusha (round90)

R90 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/f0b91746124104cdfc7c141dd17762a9d8783410/world/painting-round90/README.md) integrates R89 Khusha relief for source `2ce669a0`: 3,446 checked illustrative light samples, 117 rocky-biome cells and 1,859 changed continent pixels within buffered height support. All 58 registrations, 17 context names and the unchanged 135/42 panel are checked. Context-position metadata is refreshed from visible SVG coordinates. This closes only the painting alignment; broader source/location/era obligations remain open.

Source SVG, checker preview, terrain preview and terrain atlas remain unchanged. Final visual comparison identified no further production correction. Map documentation gate: 472 tests, 26 skipped, zero failures (62.560s). Painting gate: 472 tests, 26 skipped, zero failures (62.994s). Next: unresolved source/location/initial-state inventory; no runtime action.

## 21/11 — Khusha extends towards Sarion (round89)

R89 [Khusha continuation](../world/khusha-continuation-r89.md) connects western Khusha relief towards Sarion with an original lower envelope and two unequal summits. Source `2ce669a0`; checker: 0 errors / 56 relations / 2 existing warnings; normal export 47.565s. All 58 sites, roads, water and prior active shapes retained. Current atlas has 17 context names. Ledger 290; inventory 135/42 unchanged. R87 painting predates this new local relief and needs alignment.

Final current checker preview, official reference and original before/after study inspected. Final normal preview explicitly rerendered; old baseline reproduction changes0pixels. No runtime action. Gate: 472 tests, 26 skipped, zero failures (63.975s). Next: align painted Khusha relief, then remaining source/location/era obligations.

## 21/11 — Elmine current geography and tree study (round88)

R88 [Elmine source and larger-tree study](../world/elmine-tree-study-r88.md) corrects the retired Paulzero-grove handoff and lake bearing (east/southeast). A current-site north-facing terrace trial and original larger tree remain proposals; the Divine Tree stays partial. Five official episode 61 stills inspected, with bounded pavilion cues from 2/5. Ledger 289; inventory 135/42 unchanged; source `355d1a33` unchanged.

No production SVG, terrain, blueprint or placement configuration changed. Next: whole-tree/capital design and remaining source/location/initial-state questions. Gate: 472 tests, 26 skipped, zero failures (63.908s); zero changed JS.

## 21/11 — Published painting aligned with R86 (round 87)

R87 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/d98513e79e386b493410ab219d110c5d5bd1fa61/world/painting-round87/README.md) aligns R86 northeast Dwargon: six moved site groups, three revised roads and local illustrative relief. All 58 registrations and 16 context names are checked; the 135-entry inventory and 42-row coverage panel remain current. Source `355d1a33` and ledger 286 are unchanged. Painting gate: 472 tests, 26 skipped, zero failures (63.210s). This supersedes earlier pending painting notes only; broader source/location/era questions remain open.

No production SVG, normal export, place-concept PNG or runtime change. Next work is the unresolved source/location/initial-state inventory. Map documentation gate: 472 tests, 26 skipped, zero failures (62.901s).

## 21/11 — Dwargon moves northeast within existing rules (ChatGPT, round86)

R86 [Dwargon northeast relocation](../world/dwargon-relocation-r86.md) moves the gate to (780,−1390), retaining all 56 relations and 58 footprints. The secondary bearing discrepancy improves 35.31°→6.01°. Six related site records, two local relief shapes and three roads are aligned; water and all other native geography remain. Source355d1a33; ledger 286/inventory 135/42 follow-ups. R85 painting needs alignment; all 58 concept reservations are checked in the [art audit](https://github.com/Yasuke2000/ocs-two-lives/blob/120f5d5/docs/art/registration-r86.md).

Checker0errors/56relations/2existing warnings; normal66.1s; all 21 profiles≤1:2,3179 roof columns≥6cover. Next: painting/registration alignment; source/location/era questions remain. No protected or runtime change.

Validation: 472 tests, 26 skipped, zero failures (62.842s). Art branch: 462 tests,26 skipped,zero failures (45.465s). Current source/exports, all 58 atlas registrations and concept reservations, 3179 roof columns,21 road profiles and unchanged water are independently checked.

## 21/11 — Painting coverage follows the current inventory (ChatGPT, round85)

R85 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/cfb8055/world/painting-round85/README.md) now shows the current 135-entry inventory and 42 open rows. All noncoverage XML, the R81 continent, 58 numbered registrations and 16 context names remain unchanged. Ledger285/source9fd0c5fb retained; the painting-panel follow-up is closed. Actual source/location/initial-era questions remain open.

Painting gate: 472 tests,26 skipped,zero failures (63.024s). Map documentation gate: 472 tests,26 skipped,zero failures (62.525s). Independent XML/pixel/browser checks pass; all changes stay inside the panel. Next: actual source/location/initial-era questions. No active geography,converter,apply,chunks,protected edit or deployment.

## 21/11 — Dwargon crossing tracked separately (ChatGPT, round84)

R84 [Dwargon crossing source review](../world/dwargon-crossing-source-review.md) distinguishes the WN entrance/bridge from the two interior-city proposals. A newly explicit missing complex brings inventory 135/42 follow-ups; ledger285 (227+58). Terrain atlas coverage panel is current. Source9fd0c5fb remains unchanged; R81 painting still shows its historical134/41 panel, requiring a coverage-only refresh.

Validation: 472 tests, 26 skipped, zero failures (62.667s). All previous 284 claims and 134 inventory rows/statuses preserved. Browser checks 58 numbers, 16 context names and 42 non-overlapping panel rows; PNG changes stay inside the panel. New panel viewed.

Next: coverage-panel refresh on the painting; actual source/location/initial-state questions remain. No active geography or runtime change.

## 21/11 — Eastern Plains source and terrain assessment (ChatGPT, round 83)

R83 [Eastern Plains source/terrain review](../world/eastern-plains-source-review.md) adds two qualified WN records and a measured original current-geometry study. Coverage remains partial; source 9fd0c5fb and R81 painting remain unchanged. Ledger 284 (226+58), inventory 134/41 physical follow-ups.

Validation: 472 tests, 26 skipped, zero failures (62.851s). Independent checks retain all 282 prior facts, all 134 inventory rows/statuses and unchanged production/atlas files. Study and official geography visually inspected.

Next: resolve broader extent, continuity and actual missing locations. No runtime change or deployment.

## 21/11 — Guratol official setting evidence (ChatGPT, round 82)

R82 [Guratol source review](../world/guratol-source-review.md) verifies the official OAD mansion/cave task sequence and records the unanchored table map, with all 15 selected stills inspected. It supplies no invented global coordinates, administrative borders or S1E10 construction date. Ledger 282 (224+58); inventory 134/41 follow-ups unchanged. Source 9fd0c5fb and R81 painting remain unchanged.

Validation: 472 tests, 26 skipped, zero failures (64.055s); independent 282-record/134-row preservation, 15 image hashes and unchanged production/atlas checks pass.

Next: geographical anchoring and actual missing locations; no runtime application or deployment.

## 21/11 — Current painting follows the lake (ChatGPT, round 81)

R81 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/96b3972/world/painting-round81/README.md) now integrates the R80 El Dorado lake and bank. The exact lake polygon and 648 checked lighting samples update 361 continent pixels, within 10.75 blocks of the actual height-change footprint. All 58 registrations, 16 context names and 41 open rows remain checked; the inventory caption is 134. Source 9fd0c5fb and the 280-record ledger remain unchanged. Painting integration is closed; broader source, location and initial-era questions remain open.

Painting gate: 472 tests, 26 skipped, zero failures (63.039s). Map-branch documentation gate: 472 tests, 26 skipped, zero failures (62.876s). No production SVG change, converter rerun, runtime application or deployment. Next: remaining actual source/location/initial-era questions.

## 21/11 — Illustrated eastern El Dorado lake drawn (ChatGPT, round 80)

R80 [El Dorado eastern lake](../world/el-dorado-lake-review.md) restores an unnamed inland water cue visible in the official illustration. Original 26-vertex shore, 274×138 blocks, level 68/depth 5 and closed drainage are authored; name/outlet/initial water state remain unverified. Source 9fd0c5fb; 10 lakes, 58 sites/21 roads retained. Checker 0 errors/56 relations/2 warnings; normal 65.6s. Ledger 280(222+58), inventory 134/41 follow-ups. Terrain atlas refreshed; R78 painting requires integration.

Validation:472 tests,26 skipped,zero failures(62.581s). Existing geometry/58 anchors/road profiles retained;280 IDs,134 inventory rows with previous133 unchanged,water/rim/locality and exact atlas image/layout checks pass. Configured depth5 is nominal:sampled wet depths1.3125..5,local dry rim first-air70. Preview,study,terrain atlas and official reference viewed.

Next: R78 painting integration for the new lake/bank; remaining actual source/location/initial-era questions. No protected edit, apply, main merge, chunks or deployment.

## 21/11 — Orbic internal-country scope and atlas links (ChatGPT,round 79)

R79 [Orbic/Ulgracia scope and delivery-link review](research/tensura-world-2026-11-19/orbic-ulgr-source-review-r79.md) records the wiki royal-capital/ten-tribe distinction without invented town coordinates. Both child-category routes remain unverified. Atlas path spaces are repaired. Ledger 278(220+58),inventory 133/41 follow-ups;source e8f17470 and R78 art remain unchanged.

Validation:472 tests,26 skipped,zero failures(65.238s);link audit21 valid references;278 unique IDs and unchanged source/inventory statuses checked. Painting-link branch independently passes472/26/zero failures(65.145s).

Next: actual source/location/initial-state questions; child listings remain open. No production geometry, protected edit, apply, chunks or deployment.

## 21/11 — Current painting includes the northern island (ChatGPT, round 78)

R78 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/bc54ebe/world/painting-round78/README.md) now integrates source e8f17470 and the R77 fourth coast. The verified R69 underpainting plus native island/water layers change 5171 pixels, all inside the actual height-change footprint; all 58 registrations, 16 context names and 41 open rows retain layout. No production SVG change. Ledger 277/inventory 133/41 physical follow-ups remain; only the painting-integration follow-up is closed.

Feature validation:472 tests, 26 skipped, zero failures(62.794s); inherited checker 0 errors/56 relations/2 warnings. Source vectors/masks, underpainting hash, 2100 land samples, 2436 water samples, 5171 local changed pixels and browser registration independently checked; final preview/painting/reference visually compared. No additional source-SVG correction found in this island review.

Map reference-branch validation also passed:472 tests,26 skipped,zero failures(62.842s). Production source SHA remains e8f1747008dc6fa22609170f1175a90e977be0c0360f234cbb914d7a59259e91.

Next: remaining actual source/location/initial-era questions. No apply, main merge, chunks, protected edits or deployment.

## 21/11 — Missing illustrated northern island drawn (ChatGPT, round 77)

R77 [unnamed northern island](../world/northern-island-review.md) adds a source-visible landmass omitted from the earlier three-coast drawing. Exact shore, 615×350 scale, rolling hill and F administrative coverage are authored; ownership/name/early state remain unverified. Source e8f17470; 4 coasts, 23 region polygons, 58 sites/21 roads. Checker 0 errors/56 relations/2 existing warnings; normal 65.8s. Inventory 133/41 physical follow-ups; ledger 277(219+58), printed-LN14/author6. Terrain atlas refreshed; R69 painting requires integration.

Validation passed: 472 tests / 26 skipped / zero failures (62.818s). Native region partition, existing-shape/anchor/export preservation, raster delta locality, 277 unique IDs, 133 inventory records and exact atlas-image/layout checks passed. Final checker, source reference, study and atlas visually inspected.

Next: explicit R69 painting integration for the new fourth coast and bathymetry; remaining source/location/initial-state questions. No protected edit, apply, main merge, chunks or deployment.

## 21/11 — Nasca gate/access evidence and Empire category screen (ChatGPT, round 76)

R76 [Nasca source/access review](../world/nasca-source-topology.md) adds direct WN gates-on-four-sides and near-capital forest-road evidence, without exact bearings or initial-state claims. The 55 returned Eastern Empire category titles are enumerated; article bodies, military/child routes and unlocated settlements remain open. Ledger 275 (217+58); inventory 132/41 physical follow-ups retained. Source 82135855, terrain, R69 painting and R73 art registration are unchanged.

Validation passed: 472 tests / 26 skipped / zero failures (62.734s). Independent source-ID/hash, category, inventory and unchanged-source checks passed; original diagram PNG visually inspected.

Next: direct revised-city geography, initial state and remaining military/child-category or settlement leads. No production geometry or protected edits.

## 21/11 — Underwater Kaien andseparate later island visit (ChatGPT, round 75)

R75 [Kaien/Resort Island source review](../world/kaien-resort-source-review.md) adds scoped official movie evidence and three inspected promotional-image references. The existing two inventory entries stay open; Kaien is now explicitly an underwater-country review. Exact location, depth and initial state remain unverified. Ledger 273 unique(215+58); inventory 132/41 physical follow-ups unchanged. Source 82135855, normal terrain, R69 painting and R73 art metadata remain unchanged.

Validation: repository gate passed, 472 tests / 26 skipped / zero failures (62.807s); independent source, inventory and private-hash checks passed. Original diagram PNG inspected.

Next: remaining source/location and initial-era questions. No guessed surface islands orcoordinates; no location is marked implemented by the classification change. Technical placement remains Claude’s handoff.

## 21/11 — Englassia central-lake castle alternative drawn (ChatGPT,round74)

R74 [Englassia central-lake castle alternative](../world/englassia-castle-lake-study.md) supplies the missing C17 review geometry inside an inert source comment. One basin,four hole-free water sectors,dry plinth,castle-footprint trial andfour urban links remain authored interpretations of WN56-003. Active XML,checker preview andall13 non-index normal exports remain identical;only index source provenance changes. Current source82135855,normal65.6s. Ledger269 unique(211+58);inventory132/41 follow-ups retained. Continuity,water/model/road priority andactual castle implementation remain open. R69 painting andR73 art numeric metadata remain valid by active-geometry equivalence.

Default checker0 errors/56 relations/2 existing warnings;preview/reference andoriginal plan inspected. Validation and472 tests pass(26 skipped,zero failures,62.465s);actual-comment geometry and13-export equivalence independently checked. Next:actual source/location/era gaps andthe documented C17/C15 decisions. This closes the missing review drawing only;no protected edit,main merge,apply,chunks ordeployment.

## 21/11 — Actual creative deliverables andart metadata audit (ChatGPT,round73)

R73 [creative delivery audit](../world/delivery-audit-r73.md) checks the full brief andretains incomplete status. All58 art pairs exist;[PR101 metadata](https://github.com/Yasuke2000/ocs-two-lives/blob/7d5699b/docs/art/places/current-map-registration-r73.md) now corrects three stale radii without changing any PNG. The132-row coverage table is reconciled,with41 follow-ups retained. A concrete remaining drawing is C17’s qualified Englassia lake/castle alternative. Technical conversion/placement remains Claude’s handoff. Source90ee15b1,terrain,R69 painting and268-record ledger are unchanged.

Fresh checker0 errors/56 relations/2 existing warnings;preview/reference inspected. Art-branch gate462 tests(26 skipped,zero failures,44.559s). Main audit validation and472 tests pass(26 skipped,zero failures,62.503s);input/count/history/registration checks pass. Next:C17 drawn alternative,then actual geographical/source/era gaps;no new technical-agent task is silently added tocreative scope.

## 21/11 — Long Wall physical contour and road opening (ChatGPT,round72)

R72 [Long Wall contour and gate proposal](../world/long-wall-build-plan.md) samples the current source and fits an opening to both native/exported caravan-road projections. The5-block body follows the existing grade;exact dimensions are authored. Still inert andmissing in active coverage. Ledger268 unique(210+58),14 direct printed-LN and6 author-side-story claims;inventory132/41 follow-ups unchanged. Source90ee15b1,normal terrain and R69 painting remain unchanged. Validation and472 tests pass(26 skipped,zero failures,62.489s);both diagrams inspected;independent source/geometry/scope checks pass.

Next:final gate corner/structure-exclusion/foundation/era/registration review and remaining locations. No generated wall or gameplay barrier;protected Jura magicule core unchanged.

## 21/11 — Ulgracia identity and threshold source review (ChatGPT,round71)

R71 [Ulgracia source/identity review](../world/ulgr-spatial-source-review.md) adds three scoped WN61 claims and an original relational diagram. Corrected capital/park labels and the unsupported capital-associated spring wording;Galut and the extra-location/portal decisions remain open. Source90ee15b1,normal terrain and R69 painting are unchanged. Validation and472 tests pass(26 skipped,zero failures,62.792s);five official stills and original diagram inspected;independent scope/input checks pass. Ledger265 unique(207+58),14 direct printed-LN and6 author-side-story claims;inventory132/41 physical follow-ups unchanged. Earlier summaries below are historical.

Next:verify remaining actual locations and initial-era/source/registration questions. Do not turn the WN unnamed town into an identified Galut parcel or an ordinary physical labyrinth. No protected edit,terrain apply,main merge,chunks or deployment.

## 21/11 — Dwarven arena occupied rear shell review (ChatGPT,round70)

[R70 actual-model review](../world/dwarven-arena-fit-review.md) retains r58. Forecourt,entry,pit and stair context are exactly75 with both samplers;rear variation belongs to the enclosed raised model rather than an exposed common-level plaza. All3,343 occupied columns have SITE exclusion and source surface between their lowest solid base and highest solid top. Seven declared spawn points have explicit model floors/air. This rejects rectangle-only radius84 flattening,not runtime/collision/whole-interior acceptance. Legacy survey/beside placement still needs fixed-map reconciliation. Validation and472 tests pass(26 skipped,zero failures,62.737s);original diagram visually inspected;input/footprint/source checks pass.

Source90ee15b1,normal terrain and R69 painting unchanged. Ledger262 unique(204+58),14 direct printed-LN and6 author-side-story claims;inventory132/41 follow-ups unchanged. Next:remaining source/location/fit gaps and technical placement interfaces. No protected edit, apply, chunks,main merge or deployment.

## 21/11 — Painting follows Sacred Mountain and approach terrain (ChatGPT,round69)

R69 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round69/README.md) integrates source90ee15b1 and R68’s Sacred Mountain shoulder/approach change. Its mask covers all4,483 changed height cells,including1,003 beyond the preparation/fade envelope;1,335 gradient samples are independently checked. Only473 continent pixels change,max28/255 per RGB channel,all within16.30 blocks of the measured footprint. All58 projections,16 context names and41 inventory rows remain checked;earlier R53/R61/R63/R64 art is retained. Production geometry is unchanged in this presentation round. Ledger261;inventory132/41 physical follow-ups remain open. Earlier R68 painting-pending statements below are historical and superseded by this integration.

Next:other actual template-fit and source/location gaps. Keep initial-era,fixed-rule/extra-location decisions and local runtime acceptance open. This is a painting update,not a new source geography or completed missing location.


## 21/11 — Sacred Mountain built-perimeter accommodation (ChatGPT,round68)

[R68 support review](../world/sacred-mountain-fit-review.md) changes only the Sacred Mountain radius80→95. All6,561 occupied columns and320 built-perimeter columns are now exactly level175 with bilinear andCatmull-Rom sampling. The automatic first-air falls179→175 andfade40→48;the existing15-block model ascent remains. Current source90ee15b1/default checker0 errors,56 relations,2 warnings;normal66.6s export has no converter warnings. Height changes4,483 cells,range-29.75..+51.0625,including the shoulder/approach. All58 x/z centres and21 horizontal road routes remain;only one site record and the Sacred Mountain trail profile change. This is a real terrain change,not a tiny visual patch.

Terrain preview/numbered atlas are refreshed. R64 painting remains historical for this new source;explicit native lighting integration is next. Ledger261 unique(203+58),14 direct printed-LN plus6 author-side-story claims;inventory132/41 follow-ups unchanged. Other source,fixed-rule,era,coverage,fit and Minecraft placement obligations remain open. No protected edit,main merge,apply,chunks or deployment. Current coast/region partition was also rechecked:zero uncovered/outside/overlap area;the old R44 seams were already fixed inR49.


## 21/11 — Coleus actual occupied footprint rejects unnecessary flattening (ChatGPT,round67)

[R67 decoded fit review](../world/coleus-fit-review.md) reads the actual85 ×47 ×79 model. Seven functional support boxes are exactly75 with bilinear and current Catmull-Rom sampling. Seven of eight rectangle flags are empty;one is a four-block outer rock column. All5,313 occupied columns have exported SITE exclusion. The40-position ascent centreline retains defined floors74..90 and model-level headroom. Retain r73;the old rectangle-plus-margin98 is not a demonstrated need to flatten this hill. This resolves that proposed enlargement reason,not whole-city/era/runtime acceptance.

Ledger260 unique(202+58),14 direct printed-LN plus6 author-side-story claims;inventory132/41 follow-ups unchanged. Source c2f806a9,all terrain and R64 atlas unchanged. No converter rerun,protected edit,main merge,apply or deployment. Next:review other actual occupied/functional fits and source/location gaps;do not generalize flat rectangle criteria to intentionally stepped models or claim bilinear planning values are exact runtime heights.


## 21/11 — Source-backed Malukshure districts and tower interfaces (ChatGPT,round66)

[R66 source layout](../world/malukshure-source-layout.md) directly reads author-side-story episode02 L81,episode05 L36-L40 andepisode07 L300-L316. It separates the outer general district,protected capital-side fishing harbour,offshore rooftop arrival and transferred hall. The original diagram is topological,not a scaled plan or implementation. Construction date and unchanged S1E10 state remain unverified;later visit/crisis/damage is not activated. C14/C15 and actual city/tower coverage remain open.

Ledger259 unique(201+58),14 directly read printed-LN plus6 separately classified author-side-story claims. Inventory132/41 physical follow-ups unchanged. Source c2f806a9,all terrain and R64 atlas unchanged;no converter rerun,main merge,apply or deployment. Next:continue actual missing-location,source/fixed-rule and template-fit work;source relations do not prove completed architecture.


## 21/11 — Official named Night Garden interior reference (ChatGPT,round65)

[R65 material brief](../world/night-garden-visual-brief.md) directly reads the official Coleus announcement and opening00:01/00:03. The article names the chaise scene as Night Garden;visible blue-grey masonry,burgundy seating and cool dim light now supply a local interior reference. Original swatches/symbols are schematic,not copied frames or room geometry. The00:05 crystal shot does not prove adjacency or access. Underground relationship and initial chamber state remain separately qualified.

Ledger256 unique(198+58),14 direct printed-LN plus3 author-side-story claims;inventory132/41 physical follow-ups unchanged. Source c2f806a9,all terrain and R64 painting remain unchanged. Night Garden/chamber are still missing active representations;C15 remains open. No converter rerun,main merge,terrain application or deployment. Next:continue primary-source/location and actual fit work;do not equate a visual reference with a completed city.


## 21/11 — Hidden Lubelius locations and full partial-location panel (ChatGPT, round64)

Round64 [Night Garden study](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/world-map/world/night-garden-plan.md) adds the underground city, nested burial chamber and separate historical Night Rose to the inventory. The source relationship is fan-wiki-qualified; depth, dimensions and initial room state are unverified. City/room geometry stays inside the existing C15 comment. Production source c2f806a9 has exactly the same active XML as0b211ec7. Normal export65.9s:13 non-index files identical, index source hash only; checker0 errors,56 relations,2 existing warnings.

The [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round64/README.md) retains the R63 landscape unchanged and updates only its coverage panel. Inventory132;41 physical follow-ups include seven formerly omitted partial records, plus broader historical/source queues. Ledger254 unique(196+58),14 direct printed-LN plus3 author-side-story claims;58 original place-art pairs retained. No new active location or Minecraft application.

Next: verify primary hidden-city evidence and remaining distinct locations/template-fit issues. Inert proposals are not completed locations. Keep post-Kijin era, source/fixed-rule decisions and technical/runtime acceptance open.


## 21/11 — Painting follows summit and high-pass terrain (ChatGPT, round63)

Round63 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round63/README.md) integrates source 0b211ec7 and the R62 summit/high-pass update. The native blend mask covers all 2,507 changed height cells, including 205 beyond the site fade; 863 lighting samples are independently checked. Only 402 continent pixels change, at most 28/255 per RGB channel, all local to the measured footprint. All 58 projections, 16 context names and 32 open rows remain verified; original R53/R61 art is retained. Production geometry is unchanged in this presentation round. Ledger: 250 unique records; inventory: 129 entries with 32 coverage follow-ups. Earlier painting-pending notes are historical and superseded by this integration.

Next: other measured template-fit issues,missing distinct locations and primary evidence. Keep the post-Kijin state and fixed-rule/source distinctions;local runtime acceptance remains open.

## 21/11 — Dragon's Nest support and offset-template survey (ChatGPT,round62)

Round62 [Dragon's Nest fit and30-template audit](../world/dragons-nest-fit-review.md) enlarges only the nest preparation radius64→85 at its unchanged centre/first-air272. All7,921 buffered columns are now level;all 58 exported anchor records stay byte-identical. The normal terrain atlas is refreshed for source0b211ec7;R61 painting is historical pending explicit integration. Other offset-template findings are queued with carve/water/initial-era exceptions. Two site-radius summaries are corrected;all 58 numeric coordinate records now match. Ledger250 unique(192+58),14 direct LN plus3 author-side-story claims;129 inventory/32 coverage follow-ups remain open.

Next: current-source painting integration;review dwarven-arena/sacred-mountain and other actual template variation. Do not apply a flat-surface criterion to cavern roofs,water templates or later Tempest capacity. Existing coverage/source/fixed-rule/runtime work stays open.

## 21/11 — Painting integrates Englassia terrain update (ChatGPT, round61)

Round61 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round61/README.md) explicitly integrates source 7a30cf41 and R60's Englassia preparation update. Native SVG lighting from 1,634 measured height-difference samples changes only 31 continent pixels, at most 2/255 per RGB channel, all local to Englassia. All 58 projections, 16 context labels and 32 open rows remain verified; original R53 files and textures are retained. Production geometry and terrain are unchanged in this presentation round. Ledger: 248 unique records; inventory: 129 entries with 32 coverage follow-ups. Earlier R60 painting-pending notes below are historical and superseded by this reviewed integration.

Next: other parent-template fit/source audits and distinct missing locations. The selected post-Kijin era,source conflicts and technical registration/runtime work remain open; no completeness claim.

## 21/11 — Englassia offset-template preparation (ChatGPT, round60)

Round60 [Englassia fit review](../world/englassia-fit-review.md) decodes the existing capital fragment and expands only its preparation radius98→124 for the offset template plus eight-block margin. Academy/guild already fitted; the corrected outer corners are a small terrain-preparation issue. All18,432 buffered columns are now level76;58 x/z centres stay fixed and only Englassia changes exported y75→76. Current terrain atlas is refreshed; R53 painting remains historical pending explicit integration. Ledger248 unique(190+58),14 direct LN plus3 author-side-story claims;129 inventory/32 follow-ups remain open.

Next: explicit current-source painting integration; other parent-city fit/source checks; registered extra locations and local runtime acceptance remain open. The mapper did not change tools or runtime to fix the centred-footprint minimum.

## 21/11 — Regional visual reference curation (ChatGPT, round59)

Round59 [regional image review](research/tensura-world-2026-11-19/region-image-review-r59.md) curates69 role-labelled references across22 regions (24 distinct assets). Shared maps, local settings, interiors and cross-region analogies are explicit; country-specific landscape gaps remain. Five narrow visual records bring the ledger to247 unique(189+58);14 direct printed-LN and3 author-side-story records remain. Source1b9e151a,production geometry,terrain and R53 painting are unchanged;129 inventory/32 coverage follow-ups remain open.

## 21/11 — Dwargon East/West spatial proposals (ChatGPT, round58)

Round58 [Dwargon additional-city plan](../world/dwargon-cities-plan.md) draws interpreted East/West cavern reservations,deep galleries and stair shafts in the inert C15 comment. Two shallow routes are rejected for negative surface cover. All lined room/gallery/shaft columns are checked against the current height raster; existing occupied voxels,carving and landings remain untested. City identities remain wiki-backed; no licensed LN story passage became readable. Ledger242 unique(184+58),14 direct LN plus3 author-side-story claims;129 inventory/32 follow-ups and 58 art pairs remain. Active SVG geometry/terrain/registry are retained; full goal stays open. Current source1b9e151a changes only the inert comment. The normal65.1s export retains all13 non-index files byte-for-byte;index differs only in source_sha256. Validation and472 tests pass (26 skips,zero failures,62.588s);no changed JS or in-game run. Protected implementation paths and active preview/terrain/atlas bytes are unchanged.

Next:underground registration/carving,capital landing/occupied-voxel fit and primary city/gate evidence remain open. The current proposals do not add live sites or alter fixed template base142. R57/R58 made progress.

## 21/11 — treant routes and unsupported territorial claim corrected (ChatGPT, round57)

Round57 [treant source/route review](research/tensura-world-2026-11-19/treant-route-context-r57.md) adds4 qualified primary records. WN43 supplies sanctuary-limited movement and a conditional wetland food-transport comparison; neither establishes a Tempest cart distance. The old lore page's east-of-Ameld sovereign half and profile sister-count attribution are corrected. Ledger241 unique(183+58),14 direct printed-LN plus3 LN-aligned author-side-story claims;129 inventory/32 follow-ups and 58 art pairs remain. Source e886217d and all production geometry/terrain/painting remain unchanged. Full goal stays open. Repository validation and472 tests pass (26 skips,zero failures,62.329s);no changed JavaScript or in-game run. The source diagram was visually inspected. Source/preview/terrain/atlas and implementation paths are unchanged from485ef65; no converter rerun.

Next:continue actual source/coverage work; no arbitrary settlement parcel or Tempest supply road follows from the new comparison. R56/R57 made concrete progress.

## 21/11 — coastal capital proposal reaches its cape (ChatGPT, round56)

Round56 [Malukshure cape alternative](../world/malukshure-cape-study.md) corrects the old city disc that stopped58.7 blocks before the current shore. A connected city envelope and36-block cape remain inert C14/C15 geometry; tower disc retains30.3 blocks of sea clearance. The active SVG tree,all 58 sites and21 roads remain identical; only the source comment changes. Ledger237 unique(179+58),14 direct printed-LN plus3 selected LN-aligned author-web claims;129 inventory/32 follow-ups and 58 art pairs remain. Full goal is open. Current source e886217d is a comment-only revision of8c24a349. A normal65.5s export confirms all13 non-index files byte-identical; index differs only in source_sha256. Current preview/terrain/atlas and R53 painting geometry are retained. Repository validation and472 tests pass (26 skips,zero failures,62.583s);no changed JS or in-game run.

Next:continue primary-source and actual coverage/fit work; keep C14/H reconciliation open. An inert geometry correction is not a mapped city or runtime acceptance. R55/R56 made progress.

## 21/11 — primary Malukshure coastal evidence (ChatGPT, round55)

Round55 [Vacation author-source review](research/tensura-world-2026-11-19/vacation-source-review-r55.md) verifies the Malukshure capital cape,offshore tower and Sarion adjacency in the author public LN-aligned side serial. Exact west bearing remains wiki-qualified; C14 active binding stays open. Ledger236 unique (178+58),14 printed-LN claims plus3 new author-side-story records;129 inventory/32 follow-ups and 58 art pairs retained. Source8c24a349/geometry/terrain/R53 painting unchanged. No main merge,apply,chunks or deploy. Repository validation and472 tests pass (26 skips,zero failures,62.584s test tier);no changed JavaScript or in-game run. This validates repository integrity,not full lore coverage or runtime placement.

Next:inspect remaining source-backed location/era gaps. Keep C14 coordinates/binding qualified; do not import the later vacation trip or claim printed-LN access from a web serial. This round found new primary evidence; full goal remains active.

## 21/11 — source-key correction and anonymous Imperial geography (ChatGPT, round54)

Round54 [Imperial source and claim-key review](research/tensura-world-2026-11-19/empire-source-review-r54.md) repairs two reused keys:originalWN13-005/006 preserved,new trade/cavern records007/008;actual HTML locators verified. Direct WN147 supports an anonymous lakeside Imperial vassal,without proving Silberia identity or a map-basin position. Galut remains separate in Ulgracia. Ledger233 unique records(175+58),14directLN;129inventory/32follow-ups and 58art pairs retained. Source8c24a349/SVG/terrain/art/protected paths unchanged;no converter rerun,apply,main merge or deploy. Full goal remains open. Repository validation and472 tests pass (26 skips,zero failures,64.641s test tier);no changed JavaScript or in-game test run. Source-key integrity and current reference checks pass;these do not certify complete lore coverage.

Next:continue primary-source/identity review,especially unlocated Imperial and western-country candidates;do not rename the basin from an event parallel. R53/R54 made progress;no repeated blocker.

## 21/11 — current Dwargon relief presented in original atlas (ChatGPT, round53)

Round53 [current-source painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round53/README.md) adds native analytical lighting for the round52 Dwargon foothill/forecourt. Both source masks and666 bilinear height samples verified;1387 composition pixels change,max RGB channel32/255,all inside a96-block relief buffer. Original R38/R43 raster textures and generation records retained;no new image generation. Source8c24a349,all 58 projections,16 names and32 open rows verified;all 15 full non-callout text boxes fit current masks. Production SVG/current terrain exports/protected paths unchanged;no converter rerun,apply,main merge or deploy. Ledger231/14directLN,129inventory/32follow-ups and 58art pairs retained. Full source/era/binding/coverage/fit/runtime goal remains open. Repository validation and472 tests pass on both feature branches (26 skips,zero failures): painting64.352s,map-pointer64.333s. Final native lighting/geometry/browser audits pass;no changed JavaScript or in-game test run.

Next:continue unresolved primary-source/mainland and fixed-rule/initial-era/fit/runtime obligations. R52 andR53 make concrete progress;no repeated blocker.

## 21/11 — authored Dwargon access graded to fixed template (ChatGPT, round52)

Round52 [Dwargon approach correction](../world/dwargon-approach-fix.md) adopts a rounded foothill and low forecourt shoulder. Both road access points and sampled join widths now meet fixed first-air146/base142; maximum exported grade0.5. All3179 roof samples,58 exported site records,water/biome/road/site/exclusion/ruggedness rasters and19 other road profiles retained. Height9893cells and2profiles change; fresh normal build65.2s/no warnings. Checker0errors/all 56relations/same2warnings. Current terrain atlas/preview refreshed;R50 painting predates this relief change. Source8c24a349,ledger231(173+58)/14directLN;129inventory/32follow-ups and 58art pairs. Full goal remains open;no apply,main merge or deploy. Repository validation and472 tests pass on final source8c24a349 (26 skips,zero failures,62.421s test tier); no changed JavaScript files. Local Minecraft placement/repair/era and walkability tests remain pending.

Next:review the local relief in PR102 painting,then continue source/binding/coverage and technical local-placement acceptance. R51 andR52 made concrete progress;no repeated blocker.

## 21/11 — Dwargon approach mismatch measured (ChatGPT, round51)

Round51 [Dwargon source and approach review](../world/dwargon-approach-study.md) adds four qualified direct WN claims and a measured offline interface finding. Current road endpoint y71.33 is seven blocks from the fixed template south boundary at first-air146; roof cover passes for all3179 columns but does not verify this join. Next: grade the authored approach to fixed base142 and verify exports/local walkability. Sourcecb07cce7 and all 58 site tuples retained; no production or protected-path edit, converter rerun,apply or deploy. Ledger230(172+58),14directLN;129inventory/32follow-ups,58art pairs. Full goal remains open. Repository validation and472 tests pass (26 skips,zero failures,62.692s test tier); no changed JavaScript files. These offline checks do not verify the road/template join or live placement.

Previous goal turn50 delivered current-source painting; progress. This turn adds source evidence and identifies a concrete next terrain correction, not a repeated blocker.

## 21/11 — shared-curve painted presentation refreshed (ChatGPT, round50)

Round50 [current painted atlas](https://github.com/Yasuke2000/ocs-two-lives/blob/chatgpt/current-painted-map-r38/world/painting-round50/README.md) refreshes the native land/sea masks and coast outlines against sourcecb07cce7 (06de1b2). Original R38/R43 texture PNGs and their generation records are retained; this round uses no new image generation. Exact3coasts/9lakes/8rivers/21roads/2habitat overlays,58 source positions,16 context names and32 open rows pass the geometry/browser audit. All15 full non-callout text boxes remain inside their current sampled masks; Ulgracia's callout endpoint remains inside U. The atlas keeps every non-image element and the32.47px number spacing. The composition changes7,109 pixels from R43; no local-headland-only change claim is made for this coast refresh. Painting/checker/official-reference visual review retains production geometry. Fresh checker0errors/all 56relations/same2warnings. No production SVG,terrain export or protected path edits; no converter rerun,apply,main merge or deploy. Ledger225/14directLN,inventory129/32follow-ups and 58art pairs retained. Full source/era/binding/coverage/build-fit/runtime obligations remain open. Repository validation and472 tests pass on both feature branches (26 skips,zero failures): painting64.588s, map-pointer63.704s. No changed JavaScript files or in-game test run. These are offline checks.

Next: continue the unresolved mainland-source and fixed-rule/era/fit obligations. R49 and R50 made concrete progress; no repeated blocker.

## 20/11 — Eurazania cultivation and Laura era correction (ChatGPT, PR #74 round17)

Eurazania now has a sparse-jungle transition and three separated open field reservations within its existing southern woodland. This follows the official guide's warm climate/fruit-orchard premise (OFF-008); exact cultivation extent, vegetation species and polygon boundaries are our interpretation (DES-EUR-017). The overlays reserve a more open setting rather than automatically planting fruit crops. All58 site centres/radii and all 21 road profiles are retained; the complete height/water PNGs are byte-identical to5afa13d's staged build. No coast, river, relief, forest boundary or gameplay mask changes.

Fresh build54.4s/no warnings/source SHA matched. All58 sites/21 profiles verified; max grade0.5 and bridge40 unchanged. Sparse/plains/retained-jungle sample cells checked. Ledger187 (129 thematic/design/reference +58 coordinates). Laura creative docs distinguish old capital from later reconstruction. Repository validation and462 tests pass (26 skips); current gate: world/review.md. No apply/deployment; missing places and technical-era handoff remain open.

**Art follow-up:** [draft PR #87](https://github.com/Yasuke2000/ocs-two-lives/pull/87), branch
`chatgpt/post-kijin-place-art-r18`, worktree `C:/Users/david/Documents/ocs-place-art`, delivers eight
current image/sheet pairs based on fc36e38 (tempest, dwargon, blumund, lake_siss, treyni_shrine,
sealed_cave, dwarf_village, orc_camp). All are 1536x1024 RGB PNGs below 3,000,000 bytes; pixels of
losslessly repackaged files were verified unchanged. The original built-in image-generation outputs
remain under `.codex/generated_images/01a1f4df-fe07-7eb1-b3ee-abe4feb653a6`.
The older `chatgpt/priority-place-art` / `ocs-art-map` worktree has 29 PNG candidates and 58 sheets,
many untracked; these were left intact. Use the new art coverage table before generating replacements.
Current art delivery:58/58 registered PNG/sheet pairs in twelve stacked drafts through [PR101](https://github.com/Yasuke2000/ocs-two-lives/pull/101). Art-file coverage is complete; full geography/source/build/runtime acceptance remains open. Latest branch `chatgpt/final-place-art-r37`,worktree `C:/Users/david/Documents/ocs-final-place-art`,commit975c210. All58 reservation attributes match1209e38;58 pairs/twelve manifests/58-row coverage verified. Six new originals: Filtwood,Ghastone,Rostia,Sainte-Malukshure,old Dragon City,old well. Sainte depicts inert C14 coastal alternative,not inland H pin; C20 remains. All RGB<3MB;Ulgr native1362×1155,other57 images1536×1024;selected pixels preserved. Art validation/462 tests/26 skips pass (44.337s). Existing bone-avenue blueprint is outside the modest goods-yard camera and separately unverified. No terrain change in this art delivery.

The first historical [painted atlas is delivered in draft PR #88](https://github.com/Yasuke2000/ocs-two-lives/pull/88),
branch `chatgpt/continent-painting-r19`, worktree `C:/Users/david/Documents/ocs-continent-painting`.
Its native composition preserves3 coasts/8 lakes/8 rivers/21 roads and all 58 source anchors; registration
audit, checker and repository gate pass (462 tests,26 skips). Pictorial relief remains interpretation.
This is the first painting review coupled to current geometry; three requested painting/SVG rounds are
not complete. Map geometry is unchanged by either art delivery; no runtime apply or deployment.

**Updated painting:** [draft PR #90](https://github.com/Yasuke2000/ocs-two-lives/pull/90), branch `chatgpt/continent-painting-r22`, worktree `C:/Users/david/Documents/ocs-continent-painting-r22`, delivers the second painted atlas at efa2cc8 after the round22 forest refinement. Source SHA5e736ccc; native3 coast/8 lake/8 river/21 road vectors and all 58 projected anchors pass audit. Clean/marked images inspected; validation/462 tests pass (26 skips). Use its `world/painting-round2/` index for the current painting; PR88 remains historical. The [third painted atlas and SVG review is now delivered in PR92](https://github.com/Yasuke2000/ocs-two-lives/pull/92), branch `chatgpt/continent-painting-r25`, worktree `C:/Users/david/Documents/ocs-continent-painting-r25`, commit8cfd2c3/source60297bd. It corrects pictorial southern relief/Imperial woodland, restores8 exact native rivers after removing an invented stream, and keeps the C07 game-reservation label. Native3 coasts/8 lakes/21 roads/58 anchors and bubble clearance pass audit; validation/462 tests/26 skips pass. Current active SVG retained after review. Three painting/SVG passes documented; source/site/fixed-rule gaps,26 concepts, owner approval and technical/in-game acceptance remain open. No production change by painting or deployment.

## 20/11 — Eastern forest edge refinement (ChatGPT, PR #74 round22)

 [Eastern forest edge review](../world/forest-edge-review.md) reshapes only3 forest point lists: Jistav darkwood,northern Imperial woodland and eastern Jura foothill woodland. Selected areas retain89.4..91.0%, max boundary shift63.7; stronger21.8..24.8% removal trial rejected. Existing forest types retained;9 other forests and all other layers identical. All58 sites/radii and21 road profiles unchanged; complete height/water PNGs byte-identical. Current normal build55.7s/no warnings/hash matched.11850 biome cells change, all within old/new boundary differences. Full discs of Clayman's castle/Amrita remain in darkwood. DES-FOR-022 marks exact extents as interpretation; ledger192(134 thematic/design/reference+58 coordinates). First painting now historical; refreshed painting/final coupled round remain open. No runtime/apply/deploy. Gate result in world/review.md.

## 20/11 — Amrita/Soma source and access review (ChatGPT, PR #74 round24)

 Official episode81(no86) explicitly places Amrita beneath Clayman's former castle; all5 stills inspected (mural/doorway/cavern context, not plans). LN10 historical passage directly verifies Soma as older ruined homeland, Amrita as distant later refuge. [Plan/section and review](../world/amrita-placement-review.md) draws inert castle-linked access projection(3300,-600), r8, depth/whole footprint unknown; eastern chambers possible. Active E350..700 reservation(3800,-500),r63 remains fixed and labelled as game adaptation/C07. No sixth data-rule change authorized/applied. Every non-label layer/all 58 sites unchanged; current build56.3s/no warnings/SHA matched, complete height/water/biome/21-road/terrain-preview bytes identical to052f262. Ledger196(138 thematic/design/reference+58 coordinates),12 direct LN claims. Source versus access/marker semantics remains an owner/technical decision. Soma exact placement, other gaps and full underground design remain open; no runtime/apply/deployment. Gate result in world/review.md.

## 20/11 — Tengu official source and ridge proposal (ChatGPT, PR #74 round20)

 Official episode64 (route no68) synopsis directly confirms Tengu residence in Khusha and a later road-tunnel proposal. All five official stills visually inspected; still2/5 give limited outdoor/gateway/fence/blossom cues, not a surveyed village plan. [Original ridge/terrace study](../world/tengu-settlement-study.md) moves only the inert Tengu proposal from(-1000,1100) to(-1000,940), radius40. Old centre sampled96.75 versus new188.5; new disc remains steep146.5..189.75 and needs terrace/access design.58 live sites and all live XML elements unchanged. Fresh normal build56.4s/no converter warnings/current SHA match; terrain/checker preview bytes unchanged. Ledger191(133 thematic/design/reference+58 coordinate interpretations). LN8 chapter4 unread; WN access remains separate. Registration, source gaps and three painting/SVG rounds remain open; no runtime apply/deployment.

## 20/11 — Frost Palace WN/source review (ChatGPT, round28)

WN78 directly read: central frozen-continent setting and limited corridor/carved-door/top-terrace context. WN078-001/002 and DES-FRO-028 bring ledger199(141 thematic/design/reference+58 coordinates),12 direct LN claims. C22 contrasts fixed coast-kind reserve(-1500,-3310),r67 with inert inland near-centroid proposal(-1660,-3820),r67. Exact canonical coordinate/LN agreement/height/access remain unverified; decide coastal entry versus inland palace and site-kind/build contract. All live XML/58 sites unchanged; fresh build55.1s/no warnings/SHA32aa6e10 matched. Complete height/water/biome/21-road/terrain/checker previews identical to046d7c3. Gate result in world/review.md; no tools/runtime/apply/deploy changes.

## 20/11 — Natural-landmark source qualification (ChatGPT, round29)

WIK-ELD-029/WIK-HOL-029 record indexed volcano/mineral and near-Nasca/Velgrynd context as fan-wiki; cited LN story passages remain unread. Cached official Ameld glossary reread verifies OFF-001 without duplicate claim. Ledger201(143 thematic/design/reference+58 coordinates),12 direct LN claims;29 supplemental visual/design records. PR96 four natural-feature pairs bring art to32/58,26 remaining; masks/58 sites/SHA32aa6e10 unchanged. No new build required for source-only update. C03/C05 and other scope/fit/runtime/fixed-rule obligations remain open. Gate result in world/review.md; no apply/deploy.

## 20/11 — Sanctuary scale/source qualification (ChatGPT, round30)

LN06-004 directly rereads public LN6 summit-arrival paragraphs246-248: shrine smaller than cathedral but more lavish. Ledger202(144 thematic/design/reference+58 coordinates),13 directly read LN claims;36 supplemental visual/design records. Ten official stills do not survey exteriors. Heaven Tower LN18/19 citations remain secondary/unread; later damage excluded. PR97 brings art to36/58,22 remaining. Active SVG/58 sites/source SHA32aa6e10 unchanged; no converter rerun for research-only update. Fixed-rule/source/coverage/fit/runtime obligations remain open. Gate result in world/review.md; no apply/deploy.

## 20/11 — Orbic depleted-ground habitat (ChatGPT, round31)

Active orbic-depleted-ground biome and matching eurazania-jungle edge opening now partially represent exhausted homeland distinct from orc_camp. Direct LN2 depletion/junction reread; wiki bearings and exact239623-block² patch/mod biome remain interpretation. No capital,rift,new anchor or sovereign border. All58 sites/21 roads/height/water/site/exclusion outputs unchanged;14975 biome cells change only inside patch. Fresh build54.9s/no warnings/SHA bfe13bca;checker0 errors/56 relations/same2 warnings. Preview,atlas and native before/after inspected. Ledger203(145+58),13 direct LN.25 missing+1 partial Orbic+3 parent designs retain all29 obligations; art36/58 remains. Fifteen official Coleus stills do not verify Long Wall course/exterior. Earlier painted reviews predate this habitat change. Gate result world/review.md. No apply/deploy. Do not rerun legacy external author_canon_map.py blindly: production SVG is authoritative and later edits are not all reproduced by that old helper.

## 20/11 — Ice Continent local coast review (ChatGPT, round32)

Three authored inlets refine smooth island envelope after official-map comparison;94.02% area retained,105 vertices,max shift208 blocks. Exact coast remains interpretation. Fixed palace shore/58 site attributes/mainland/ElDorado/21 roads retained;sea gap916.98. Fresh build55.1s/no warnings/SHA d10aa456;checker0 errors/56 relations/same2 warnings. Complete water/road/site/exclusion outputs unchanged;all height/biome rows south ofz-2800 and palace230×230 square identical. Preview/atlas/native study inspected. Ledger204(146+58),13 direct LN. Current BookWalker guide8.5/LN14 trials and licensed English retailer leads remain unread;C05/C22 not resolved. Coverage25 missing+1 partial+3 parent;art36/58 unchanged. Earlier painted passes predate this shoreline/Orbic. Gate world/review.md. No apply/deploy;production SVG authoritative over old external author helper.

## 20/11 — Jura approach art and Council country source (ChatGPT, round33)

PR98 (f335f38,stacked on PR97) brings art to40/58,18 remain. Four corrections preserve current58 reservations/e619fb7; nine manifests and all40 pairs verified. WIK-CAN-033 keeps summit association at wiki confidence,LN12ch2/4 unread; OFF-COW-033 directly reads official episode77/route82 country-level Englassia meeting context without assigning an HQ parcel or early event. Ledger206(148+58),13 direct LN;43 visual/design supplements. Current SVG/source SHA d10aa456 and terrain unchanged; no new converter run required. Coverage25 missing+1 partial+3 parent and other source/fixed-rule/fit/runtime requirements stay open. Gate result in world/review.md; no apply/deploy.

## 20/11 — Smaller western source/art follow-up (ChatGPT, round34)

PR99 (558b032,stacked on PR98) delivers six concepts,total46/58,12 remain;all 58 attrs match13f4cfb.46 pairs/ten manifests verified. OFF-RAJ-034 directly reads distributor page2 west/gold/lake film context; FAN-WES-034 qualifies later four-country map names/order as secondary. Official65/76 ten stills inspected,not verified map/exterior surveys. Six creative briefs qualify project industries/birch/trade context,correct manga108 versus LN and exclude later Ballachia liberation/Raja cure from initial snapshot. Ledger208(150+58),13 direct LN;52 visual/design supplements. SVG/source SHA d10aa456 and terrain unchanged; no new converter run. Coverage25 missing+1 partial+3 parent and other source/fixed-rule/fit/runtime obligations remain. Gate world/review.md;no apply/deploy.

## 20/11 — Imperial illustrated basin (ChatGPT, PR #74 round35)

Adds one active unnamed basin east/southeast of the fixed Imperial cone after direct visual comparison with official base. MAP-IMP-035 is canon-implied; DES-IMP-035 qualifies all28 vertices/355×122-block extent/level68/depth5. No Silberia name,city,outlet or C05 resolution. Fresh normal build55.0s,no warnings,SHA1ea6782d. All58 site attributes/21 road profiles and other active layers retained; roads/sites/exclusion exports byte-identical to cd89e26. Height/water/biome each change1892 local cells;1888 strictly interior samples wet. Checker0 errors/56 relations/same2 warnings. Current preview/atlas/study visually inspected; see world/imperial-basin-review.md and audit.json. Ledger210(152+58),13 direct LN;art46/58,12 remain. Coverage25 missing+1 partial+3 parent and source/fixed-rule/fit/runtime obligations stay open. Earlier paintings predate this change. Gate in world/review.md; no apply/deploy. Previous round34 made progress; no blocking condition repeated.

## 20/11 — world-map branch integration with upstream main (ChatGPT, round35)

The map feature branch incorporates upstream main09ca601, preserving both complete additions in the two overlapping documentation hunks (this handoff and design/decisions.md). No pull request was merged into main and no server action ran. Runtime scripts/mod files exactly match upstream main; the sole tools difference remains the five owner-approved canon_relations.toml data corrections. World converter code/SVG source hash/normal staging exports are unchanged by this integration. Current map build/source review is world/imperial-basin-review.md; integration validation is recorded in world/review.md. Repository validation,20 JS syntax checks and472 tests pass (26 skips,zero failures,44.221s test tier). Mainline's new local-server/deploy-gate instructions are retained. Full geography/source/site/build-fit/runtime obligations remain open.


## 20/11 — bounty boards, NPCs and guards audit; killable enemies of the roads (branch `bounties-npcs-enemies`, Claude, for Yasuke)

Yasuke: "Also check the bounty boards, NPCs and the guards; add killable NPCs as well." **Audit fixes**: Tensura's Severance,
Disintegration, Death Wish, ... are in `minecraft:bypasses_invulnerability`, so the "invulnerable" named residents and
statues could be killed by a soul (proved locally on an invulnerable husk): `world/npc_protect.js` shields `ttl.npc`,
`ttl.adv` and the invulnerable residents from everything but /kill; guards now also fight the enemies, never tames, owned
mobs or other NPCs, and walk back to a post they strayed 16+ from (`npc_gear.toml guard_leash`); `fz_ravager_herd` retired
(ravagers need a raid, none on Lerfing's map); a region-bound bounty (`jura_direwolves`) so PR #80's fix is tested in game
(`guild.rcon`); `ttl cast verify` also checks the ground (no wall, water, floating) and the skin. **New**: enemies of the
roads (`design/data/enemies.toml`, `world/enemies.js`, decision row 20/11 "Killable NPCs"), 8 camps, bounty targets
`ttl:<archetype|group>`, the road `enemies.slay` (good for outlaws, dark for peaceful kills), test `enemies`.
**Verified locally**: see the PR. **Not done**: orc raiders (no orc look in the skin generator); a Tensura skill that eats
an entity whole (Predator) is not a damage event and is not shielded; `docs/dev/ttl-commands.md` is not regenerated (main's
toml already misses rows for bedspawn, drops, spawns, ...; the enemies and npcprotect rows are in the toml).
**On staging after the deploy**: `ttl enemies list` (all camps asleep, stock full), then walk a Life 2 soul to the Dwarven
Road camp (1818, 420): bandits appear at ~70 blocks, `[ttl] enemies: <name> killed bandit of dwarven_road_south` on a kill.

## 20/11 — deploy gate and tests independent of real players (branch `test-isolation-gate`, Claude, for Yasuke)

Staging failed `registry` (real holders of berserker/gluttony/great_sage counted against the bots) and `arena_dwarven`
(a deploy re-placed dwarf_village during test-all; the lag outran a fixed 7 s). **Done** (decision row 20/11 "Deploy
gate"): test bots and real players count in separate registry pools (`scoped()`), bot-only test assertions, test scopes
for boss cooldown clears and choice scenes, `@until` arena waits, test-all waits for start-up placements;
`tools/local.sh verify` + lock; ttl-ops gate in the Homelab PR `ttl-ops-local-gate`. **Verified locally** (Lerfing
server, with a simulated real player holding berserker, gluttony, seeker and great_sage and an open real choice scene,
both untouched afterwards): registry, legendary, absorb, registry_pool, registry_reconcile, choices, arena_dwarven,
arenas2, bosses, wild, story, events_pack, quests. **Next**: after every merge run `local.sh verify` (AGENTS.md).
Not covered (low risk, noted): `nations` claims a chunk 100 blocks from Tempest (fails if a real player claimed it);
`events` ends a real running event (`ttl events end`) and `ttl arena reset` resets every arena (both only while nobody
is online).
## 20/11 — Jura route art and treant-source distinction (ChatGPT, round36)

PR100/96e1069 delivers six revised/new original pairs (shizu_spawn,outcast_road,treyni_grove,blumund_road,englassia_road,rookie_camp),total52/58,6 remaining. Main creative briefs correct legacy coordinates,initial residents,tree/settlement equivalence and false safe-rim context; no runtime changes. WIK-TRE-036 is secondary indexed geography,not a directly read LN passage. The distinct treant community gains an explicit missing mainland row;127 inventory entries,26 missing+1 partial+3 parent,30 follow-up obligations. Ledger211(153+58),13 direct LN;61 visual/design supplements. All58 attributes match48b0846; current SVG/source SHA1ea6782d and terrain unchanged,no converter rerun. Exact prompts,readability cleanup and selected/own-input hashes in the art stack. Main gate in world/review.md. No apply/deploy;full geographic/source/fixed-rule/fit/runtime requirements remain. Previous round35 made progress; no blocking condition repeated.

## 20/11 — registered art coverage and final-place source distinctions (ChatGPT, round37)

PR101/975c210 completes58 registered PNG/sheet pairs and twelve manifests,not full world acceptance. All58 attributes match1209e38. Six creative briefs correct country identities and source/era/architecture limits; Sainte art depicts only inert C14 coastal proposal. Official Johann and Middray profiles directly establish Rostia kingdom and Dragon City temple; Ghastone list is wiki-level. Ledger214(156+58),13 direct LN;72 visual/design supplements. Two newly inventoried country pins remain unverified:129 entries,26 missing+1 partial Orbic+2 country pins+3 parent designs,32 follow-ups. Current terrain/source SHA1ea6782d,exports and 58 reservations unchanged,no converter rerun. Two atlas legend entries clarify country pins. Main gate in world/review.md. Full geometry/source/fixed-rule/era/fit/runtime requirements remain open; no apply/deploy. Previous round36 made progress; no repeating blocker.

## 21/11 — current painting and standalone preview refresh (ChatGPT, round38)

Draft PR102,branch chatgpt/current-painted-map-r38,worktree C:/Users/david/Documents/ocs-current-painted-map,commit31cc28e. Refreshes the third original painting using current own guides against dc92845/source1ea6782d. Native3 coasts/9 lakes/8 rivers/21 roads/1 Orbic highlight and 58 projected anchors verified; number spacing32.47px. Current clipping/raw-blue suppression prevents painted water defining new geography. Source/era/conflict labels retained. Fresh checker0 errors/56 relations/same2 warnings; painting branch validation/472 tests/26 skips pass (44.520s). Production SVG/checker preview/protected paths unchanged; no converter rerun. Main atlas already used the correct export; standalone terrain-preview.png had last changed at efa2cc8 and is now copied byte-identically from current normal build,with provenance. Main gate in world/review.md. Earlier3 painting/SVG passes remain historical.214 claims/13 direct LN/72 supplements/129 inventory entries/32 follow-ups/58 art pairs unchanged;full source/geometry/fixed-rule/era/fit/runtime requirements remain. No apply/deploy. Previous round37 made progress; no repeating blocker.

## 21/11 — public LN fragment screening (ChatGPT, round39)

Four public GC publisher fragments accessed; selected geographic passages/context read, not complete volumes. LN07-001 records later organized Tempest road patrols after Walpurgis, without backdating paving/security to the initial Kijin snapshot. No new small-country location established. All eighteen names in the wiki western-state list already occur in the inventory. Ledger215(157+58),14 direct LN; inventory129/32 follow-ups and 58 art pairs unchanged. Access manifest stores hashes only, copyrighted cache outside repo. Production SVG/terrain/painting/runtime bytes unchanged; source1ea6782d, current presentation PR102. Full goal remains active; no repeating blocker, merge, apply or deploy. Validation recorded in world/review.md.

## 21/11 — Long Wall border-corridor correction (ChatGPT, round40)

Corrects DES-ADD-wall and its inert SVG proposal; old route crossed856.63blocks of desert interior,now follows existing NE/east boundary with a dry oasis detour. Original before/after vector study,measured audit and future caravan-gate obligation in world/long-wall-corridor-review.md. Sourcea24cea9b changes only a comment: all11active layers/58sites/checker preview/9normal exports identical to5bb2467. Fresh checker0errors/56relations/2warnings; normal build no warnings; repository gate in world/review.md. Ledger215/14directLN,inventory129/32follow-ups,58art pairs unchanged. Wall stays absent from production,full source/era/fit/runtime requirements remain. No merge/apply/deploy. Previous round39 made progress;no repeating blocker.

## 21/11 — geographical atlas labels and full index (ChatGPT, round41)

Current numbered atlas adds16 broad context names,including Eastern Empire,and a separate32-entry M/P/U panel. Full world/location-index.md preserves all129 inventory source/scope rows. Wiki-coverage display now matches current129 rather than stale126. All58 number groups/terrain image bytes retained; actual Chrome text boxes verify no overlap with padded number bubbles and all32 appendix rows fit. Fifteen labels fit gameplay contexts; Ulgracia callout ends inside U. No new capitals/borders/coordinates inferred; none of32 obligations closed. Production sourcea24cea9b,exports/painting/runtime unchanged. Ledger215/14directLN and 58art pairs retained. Gate in world/review.md;full goal remains open. No merge/apply/deploy. Previous round40 made progress;no repeating blocker.

## 21/11 — western mainland headland (ChatGPT, round42)

Active source7d021766 adds the original northwestern cape after official-image comparison. Mainland9989x6250/design12800x10752 below hard limits;preferred target deviations remain C12. All58site attributes/earlier waters/relief/forests/21routes/21other masks retained. Fresh checker0errors/56relations/2warnings;normal build57.0s/no warnings. Wider raster origin needs128-column alignment:water/road/site/exclusion match;all 58site-disc heights match;20road profiles match,Sacred trail34heights change at most0.04blocks. Current atlas reprojected0.96plusorigin;16labels/58numbers/32open rows retained. Ledger217(159+58)/14directLN;inventory129/32follow-ups;58art pairs. PR102 R38 painting is historical; its basis now integrates map50e0715 in painting head4847edd. Shared preview/provenance conflicts are resolved; normalized text and byte-identical previews verified. Painting basis build58.7s/no warnings and472tests/26skips pass (45.880s). Next:refresh actual painting pixels/native registration from current7d021766 guides. Main gate in world/review.md. Full goal remains active;no merge/apply/deploy. Previous round41 made progress;no repeating blocker.

## 21/11 — current-source painted headland delivered (ChatGPT, round43)

PR102 adds world/painting-round43:built-in image_gen edit using only original R38 painting and own current checker/terrain guides. Local native feathered mask limits the new texture to the source headland; R38 pixels/provenance retained historically. Source7d021766 unchanged. Exact3coasts/9lakes/8rivers/21roads/2habitat overlays,58source projections,16context labels and32open names audited. Larger pixel changes within320-block headland buffer;12outside edge pixels differ at most2/255. Leader lines now behind all number bubbles; spacing32.47px. Browser text bounds clear padded bubbles. Painting/checker/official-reference visual review retains geometry. Painting gate472tests/26skips/0failures (44.683s); pointer gate472tests/26skips/0failures (44.328s). Next:remaining mainland/source/binding obligations; repeat painting only if the source geometry changes. Living contradiction summary updated to14directLN claims and the current C12 coast/scale status; all 58 coordinate-ledger centres/radii match the current SVG. Ledger217/14directLN,129inventory/32follow-ups,58art pairs retained;full goal remains open. No source/terrain/runtime apply or deploy. Previous round42 made progress;no repeating blocker.

## 20/11 — Old Dragon City southeastern proportion correction (ChatGPT, PR #74 round16)

Round 16 moves the old Forgotten Dragon City from(2500,150) to(2650,800), retaining radius100, M membership and all fixed relations. This follows the official illustration's broad southeastern pattern and the wiki territory relationship south of Jura/east of Eurazania. The pinned secondary marker distance discrepancy improves from-9.8% to-0.3% and bearing discrepancy from-13.3 to+0.1 degrees; projection and precision remain unknown. Exact city coordinates and two rerouted approach trails are our interpretation. All other57 site centres/radii and every coast, lake, river, mountain, hill, forest, biome and gameplay polygon remain unchanged frome129131. This is the old settlement, not the later city/castle built at Laura.

Ledger186 (128 thematic/design/reference +58 coordinates). Doran remains unlocated beyond west-of-Jura; licensed Trinity chapter25 story pages not accessed. Fresh normal export54.3s/no warnings/source SHA matches; old Dragon City0/1954 wet, all 21 road profiles<=0.5, max bridge40. Repository validation and462 tests pass (26 skips). See world/review.md. No apply/deployment; previous constraints and coverage gaps remain open.

## 20/11 — Official Coleus placement correction (ChatGPT, PR #74 round15)

Round 15 corrects Coleus using the directly read official anime outline: the independent kingdom lies between Ingrassia and Lubelius. Its authored centre moves from(-3650,-250) to(-3520,-860), retaining radius73, V membership and all fixed relations. The dunes move(+130,-610); the oasis moves(-175,-610), keeping water separate from the city and river. One caravan trail skirts the pond on its north side. The other57 site centres/radii, coasts, rivers, mountains, hills, forests and gameplay masks remain unchanged from147ea7e. Exact city position, shore/level and trail bends remain our interpretation; countries lying between others does not survey their capitals.

Official synopsis and INEI concept inspected; ledger184 (126 thematic/design/reference +58 coordinates). Existing hill-palace blueprint reused as evidence, unchanged. Era-sensitive palace state remains unverified. Fresh build54.0s/no warnings/SHA matched; Coleus0/1044 wet, all 21 road grades<=0.5, max bridge40. Repository validation and462 tests pass (26 skips). See world/review.md; no apply/deployment. Coverage obligations and prior conflicts remain open.

## 20/11 — Sarion proportion refinement (ChatGPT, PR #74 round14)

Round 14 moves Elmine from (-1100,1800) to (-1680,1740), retaining its 100-block radius and all fixed relations. Relative to the pinned fan marker pattern, its Siss-normalized distance discrepancy improves from -13.0% to -0.3% and bearing discrepancy from -17.5 to -4.9 degrees. Unknown projection and marker precision limit this comparison: exact server coordinates remain our interpretation. The pond follows the city (-580,-60); the hill shifts (-480,-60) to remain on the existing coast. Three trails approach the north edge and skirt the pond. The other 57 site centres/radii, coast, rivers, mountains, forests, biomes and gameplay regions remain unchanged from a2748f3.

Verified: default checker 0 errors / 56 relations pass / 2 prior warnings; fresh normal build 54.6s, no converter warnings, source SHA matches. All 21 road grades <=0.5 with float epsilon; max bridge 40 <64. Elmine 0/1976 wet; cave 0/1116; goblin 0/612; Siss 1804/1804 and lizardmen stilt plate 710/710 wet. Ledger 181 (123 thematic/design/reference +58 coordinate interpretations). Repository gate: validation passed; 462 tests, 26 skips, 0 failures. No apply/deployment. Remaining source/location conflicts and the 29 coverage follow-ups stay open.

## 20/11 — Rounded river bends and measured western trail grade (ChatGPT, PR #74 round13)

Five existing reaches (Ameld head/outlet, Tempest upper brook, Jura–Sarion, western trade river) now have rounded bends. All original control points/endpoints, widths and head/mouth levels retained; measured maximum plan deviation14.17 blocks. Exact channels are interpretation under C03. [Measurements](../world/river-centreline-review.csv). One western trail waypoint within20 blocks corrects an exported grade0.5022 after the river change; old path points/endpoints retained. All58 sites/radii and other geometry unchanged. Ledger180 records.
Verified: default checker0 errors/all 56 relations pass/2 prior warnings; fresh build54.0s/no warnings/current source SHA match. All21 actual road grades<=0.5 with float epsilon; max bridge40<64. Water: cave0/1116 and goblin0/612 wet; Siss1804/1804 and intentional lizardmen plate710/710 wet, level66. Current atlas/official comparison refreshed. Repository gate: validation passed;462 tests,26 skips,0 failures. No apply/deployment or new canonical hydrography claim. Continue missing places, source evidence and fixed-binding review.

## 20/11 — Mainland scope routing and city coverage study (ChatGPT, PR #74 round12)

All126 inventory entries routed without dropping any obligation. All29 review obligations retained:26 missing representations (19 mainland,4 city/interior,3 offshore) plus3 parent designs found in blueprints/NBT. Elf venue in dwargon.py; guild()/academy() in englassia.py. Reuse existing designs after source/fit review; do not confuse absent SVG submarkers with absent implementations. [Audit](research/tensura-world-2026-11-19/mainland-coverage-audit.md). [City schematic](../world/city-coverage-study.md) groups Dwargon East/West/bar and Englassia guild/council/academy/castle; box layout is not geographical geometry. Six new claims (ledger178) preserve wiki confidence and official ep20's limited school context. Doran remains west-of-Jura only, with no fabricated capital/outline. Licensed LN1 retailer preview did not expose book pages; no LN evidence upgrade.
Production SVG/rasters unchanged from f42bdbf; current source/preview provenance and all178 unique claim IDs checked. Full gate passes validation and462 tests (26 skips). No new IDs, tool changes or runtime work. Next: resolve remaining physical gaps, source placement and fixed-binding choices; internal city plans and placements remain open, not counted complete by this classification.

## 20/11 — Restrained Milim biome scope and episode-source audit (ChatGPT, PR #74 round11)

C10: narrow red accent remains per fixed brief, but authored area drops707757 to213884 blocks2 (69.8%). No other biome polygon, site, coast, height, water, road or mask changes. A conservative no-red replacement is drawn inert for review; no claim of canonical desert or exact ecosystem. [Locator audit](research/tensura-world-2026-11-19/anime-episode-locators.csv) checks eight region-book routes: no28/30/42/48 actually display episodes26/28/39/45. Episode41 is no44, not no41. Generic still links now contextual leads. Five official no44 stills inspected; no city exterior verified. Pinned secondary city-frame raw fetch403. Ledger172 unique records.
Verified: checker0 errors/all 56 relations pass/2 prior warnings; current build52.6s/no warnings/SHA match. All58 centres/radii and21 grade profiles verified. Current wooded-badlands raster13374 cells; released-ground sample4034,614 is plains. Full gate passes validation and462 tests (26 skips). Atlas and official comparison refreshed. No tool/runtime edits or server apply. Continue missing-place/primary-source coverage and fixed-rule reconciliation; do not claim full fidelity/completeness.

## 20/11 — Filtwood source correction and Orbic homeland study (ChatGPT, PR #74 round10)

Official S1E24 synopsis names Filtwood a kingdom in a story before Rimuru; wiki puts it near Jura. The creative pack's town-in-Ulgracia claim was unsupported. C20 corrects prose, era overlay and coverage crosswalk; active U anchor is unchanged and visibly disputed. [New study](../world/southern-location-study.md) draws an inert western Jura-edge trial (side unverified) and a separate depleted Orbic homeland vicinity. LN2 famine/junction reread; wiki bearings stay secondary. All five official episode24 stills inspected: interiors/characters, no exterior plan. Ledger170 unique records.
Verified: standard checker0 errors/all 56 relations pass/2 prior warnings; fresh build52.3s/no warnings/current SHA match. All non-label SVG groups and converter preview bytes equal prior terrain; all 58 exported centres/radii verified and21 road grades<=0.5. Repository gate: validation passed;462 tests,26 skips,0 failures. No extra technical, runtime or live terrain edits. Next: remaining missing-place/source evidence and fixed-binding reconciliation; no exhaustive wiki/completion claim.

## 20/11 — Canaat relief and Empire evidence gaps (ChatGPT, PR #74 round9)

Replaced the long equal-height Canaat crest with a shorter bent high spine and a lower tapered180-block eastern mountain apron, following broad official illustrated massing. Exact relief is interpretation. All58 centres/radii, coasts, waters, roads and masks unchanged. [Empire follow-up](research/tensura-world-2026-11-19/eastern-empire-followup.md): Silberia remains unlocated; publisher13.5 listing read but licensed trial timed out. WN historical states/frontier ruin remain continuity-qualified. Ledger165 records.
Verified: checker0 errors/all 56 relations pass/2 prior warnings; fresh build52.2s/no warnings/current SHA match; all 58 sites match, all 21 grades<=0.5, max bridge24. Lake/village intentional wet footprints and dry cave retained. Atlas/comparison refreshed. Full repository gate: validation passed;462 tests,26 skips,0 failures. No apply/deployment. Next: remaining source/era/coverage gaps and fixed-rule alternatives; do not claim exhaustive wiki or final fidelity acceptance.

## 20/11 — Lake Siss source correction and elongated basin (ChatGPT, PR #74 round8)

Official glossary A-77 describes Charybdis as an aerial calamity; the older creative pack's aquatic-whirlpool/circular-lake premise was false. Corrected that prose and episode reference, retaining later server arena reservations. Official illustrated lake character supports a broad east–west basin; exact authored858 by410 blocks is interpretation. Shore/inlet/outlet revised, all 58 site positions/radii and roads retained. Ledger162 records; C19 records the correction.
Verified: checker0 errors/all 56 relations pass/2 prior warnings; normal current-SVG build52.4s/no warnings, source SHA matches. Raster: lake1804/1804 wet; village710/710 intentionally water per sites.toml for stilts; cave0/1116 wet. All21 road grades<=0.5, max bridge24. Updated atlas/comparison; full repository gate passes validation and462 tests (26 skips). No apply or deployment. Continue primary-source/wiki coverage and fixed-rule fidelity decisions.

## 20/11 — Official live map verified; current-SVG staging rebuilt (ChatGPT, PR #74)

Restored session permissions remove earlier operational limits. Fresh normal build of current SVG:53.7s, no converter warnings, source SHA matches index; published terrain-preview bytes match output. No generated index patched and no apply.
Official interactive map operated in Chrome: enter/tutorial, chapter2, all four story stops (episodes9/12/14/15), World mode and Gazel/Rimuru affiliation selection. [Notes](research/tensura-world-2026-11-19/official-interactive-map.md). There is no separate episode10 navigation stop; keep naming-event synopsis as precise snapshot anchor. Affiliation highlighting is not a surveyed sovereign border, and omitted countries are not nonexistent. Live screenshots/trace stay outside repo. Ledger remains159 records, with one previously indirect label claim upgraded to directly observed official display evidence. Main/source/geometry unchanged.

## 20/11 — Initial era after Kijin naming and eastern landscape (ChatGPT, PR #74)

Owner selected immediately after the six ogres are named: official anime S1E10 synopsis verified. [Era policy](../world/era.md) and 58-site overlay supersede mixed-era presentation. Atlas: Rimuru's village, unresolved orc approach, future/server reservations. Falmuth, Frey, Carrion, Clayman and Rudra baseline; no later Tempest metropolis or ruler outcomes. Supplied official map chapters1/2/3/4/6/9 inspected separately from live controls.
Live geometry adds only eastern Jura/Canaat light woodland and open fringe. All58 sites, roads, heights, waters and political masks retained. Ledger159 records (101 thematic/design +58 coordinates); every row has snapshot_use, with nine new direct WN claims. C16/17 qualify WN access and city water; C18 exposes future highway/content contract versus the early snapshot.
Verified: checker0 errors/all 56 relations pass/2 prior warnings; normal build53.9s/no warnings includes habitats. Later converter repeat declined; removing only era metadata/cosmetic labels exactly reconstructs staged source SHA. Generated index unchanged. All58 centres verified from index.json (sites.json has34 plate entries); actual21 road profiles <=0.5. Validation and462 tests pass,26 skips. [Current review](../world/review.md). No runtime apply. Next: close source/wiki gaps and reconcile era construction/residents with the runtime team; do not claim future content already exists.

## 20/11 — Coastal Malukshure evidence and additional-location drawings (ChatGPT, PR #74)

[Five proposals](../world/additional-locations.md), [view](../world/additional-location-study.png): Galut, Tengu summit settlement, coastal Sainte-Malukshure, offshore Magic Tower, western Long Wall corridor. Exact geometry is interpretation and remains inert in map.svg comment. New primary official manga synopsis places the tower in Malukshure waters; wiki neighbours/coast remain qualified. C14 exposes current Sainte pin in H/Fulbrosia versus coastal/west-of-Sarion source alternative. C15 keeps proposed places separate from the fixed 58-site contract. No additional tool/anchor/runtime changes. Ledger now 141 records, 11 direct LN claims.
Verified: standard checker 0 errors/2 disclosed warnings; normal build 54.6s, source hash matches staging; checker and converter previews byte-identical to prior live geometry. Repository gate passes validation and 462 tests, 26 skips. Current goal active; owner requests continued autonomous overnight work. Next: primary-source strengthening and further missing-mainland geography; keep C14/15 interpretation/registration limits explicit.

## 20/11 — Wiki completeness audit (ChatGPT, PR #74)

Owner asks to check the whole wiki geography, beyond the original 58 sites. [Audit](research/tensura-world-2026-11-19/wiki-coverage.md): all 31 owner-listed Locations entries, all 44 accessible Countries index entries, linked indexes/article geography; 126 deduplicated records, 29 missing distinct representations. 58 actual SVG sites cross-referenced; all map references validated against SVG identifiers. Empire E/Nasca/Velgrynd mountain exist, but Silberia, frontier settlements and interiors are not comprehensively represented. Long Wall, Magic Tower, Galut, Tengu settlement, Orbic and ocean/movie destinations need further coverage. Category access and Horn Empire are qualified; do not say the entire wiki or every primary source was read. No SVG/tool/runtime changes. Next: close source/traversal gaps and research additional-location proposals before final fidelity acceptance.

## 20/11 — Western proportions, eastern coast and measured climb grades (ChatGPT, PR #74 round 6)

Moved Blumund (-1500,-620), Marris (-1800,-1650), cave (-120,-400), Shia's coastal landing and one road pin;
redrew bay bank/approaches, northeastern hook and eastern bay. P/M coverage adjusted to connected shore.
No fixed rules relaxed. [Benchmark](../world/proportion-audit.csv): three distance discrepancies improve
57.4→32.8%, 41.8→11.4%, 24.3→3.3%. Residual fixed-range alternatives drawn in inert SVG comment and
[proportion study](../world/proportion-study.png). All 58 IDs/minima/internal offsets preserved.
128 evidence records (70 thematic/design + 58 coordinates), 11 direct LN claims. [Review](../world/review.md).
**Verified:** standard checker 0 errors/2 disclosed warnings; normal build 57.6s/0 warnings, source SHA
matches; cave water raster 0/1116 wet pixels. Profile audit found ten old climbs >1:2; authored routes
now stay in their corridors with exact sampling lengths: all 21 profiles <=0.5, longest bridge 24 blocks.
Full gate passes validation + 462 tests, 26 skips. No further tools/code edits beyond approved five data rules.
**Next:** strengthen remaining primary WN/LN geography evidence and qualify open lore/scale alternatives;
do not undo source/constraint distinctions or claim runtime generation/deployment. Main a1848be integrated.


## 19/11 — Latest main integrated; proportion review now measurable (ChatGPT, PR #74)

Merged main a1848be into chatgpt/world-map (79178d8), retaining both agents' decision/handoff additions.
Integrated gate passes validation and **462 tests (26 skips)**. World format, site-size table and map tools
unchanged upstream; only the previously authorized five relation entries differ technically from main.
[14-site audit](../world/proportion-audit.md) normalizes reference and authored distances to Tempest–Siss.
Blumund +57.4% and Marris +41.8% in this secondary benchmark are clear review signals, not canonical survey
errors. Next: revise western/central proportions within fixed constraints, updating coast/roads/regions
and checking every geometry edit; draw/explain source alternatives where constraints prevent fidelity.
The earlier source-evidence and round-5 entries remain current; do not mark the full goal complete yet.


## 19/11 — LN evidence and northern Ulgr park (ChatGPT, PR #74 round 5)

Read relevant publisher-hosted Japanese LN2/3/5/6/10 passages: 11 direct geography claims added.
[Findings](research/tensura-world-2026-11-19/ln-sample-findings.md). Ledger now 122 records (64 thematic/design,
58 coordinate interpretations), with access limits. Guidebook 8.5 trial loader stalled; no pages claimed read.
Moved only S/U border to about y2720 for the officially northern park; preserved all 58 coordinates/radii.
Atlas separates park/Spirit Dwelling entrance from Galut and labels independent Shia/Siltrosso. C05/C06
alternatives drawn inside inert SVG comment plus [review diagram](../world/lore-alternatives.png).
**Verified:** standard checker 0 errors/2 disclosed warnings; normal build 54.2s/0 warnings, matching SHA,
58 coordinate/minimum-radius/offset checks; full gate passes validation + 456 tests (26 skips); previews inspected.
No further tools changes; only the previously approved five data entries differ from main. Fetched a1848be:
world format/tools/sizes unchanged; integrating main before next push. Source/fidelity review stays open.


## 19/11 — Five owner-approved geography corrections; normal gate green (ChatGPT, PR #74)

Yasuke explicitly approved an exception for **only five data entries** in `tools/world/canon_relations.toml`.
Adopted the Jia/Ulgracia/ogre proposal, with a [lore source note](../design/lore/world-map-corrections.md).
Other 51 relations, site/sea rules, checker code and tests unchanged. Added superseding owner clarification
to own-world.md; precise distances/bearings remain server adaptation where evidence is secondary.
**Verified current state:** standard map checker 0 errors/2 disclosed warnings; normal `build.py` (no skip)
60.5s, 0 converter warnings, matching source SHA, 58/58 coordinates/minima/exact relative offsets;
`tools/check.sh` via Git Bash passes validation and 456 tests (26 skips). Preview/atlas refreshed.
See [review](../world/review.md), [comparison](../world/comparison.md), [region differences](../world/regions.md).
**Remaining:** source/proportion review and open lore questions; no runtime Minecraft acceptance, pack apply,
merge or deployment. The red-gate status in older handoff entries is historical and superseded by this result.


## 19/11 — Research-driven map round 4 (ChatGPT, `chatgpt/world-map`, PR #74)

Replaced the starter with the current authored map and corrected its northern bay, southern gulf,
western coastal tongue and Ameld foothill corridor/eastward bend. Trail to Jia detours around the gulf.
All 58 footprint-sized sites retained; exact parent offsets verified. [Numbered atlas](../world/atlas.png),
[comparison](../world/comparison.md), [review](../world/review.md), [region differences](../world/regions.md).
Research ledger: 50 thematic claims plus 58 coordinate interpretations, not 108 verified canon facts.
Added access log: publisher LN1 sample read (prologue only); licensed BookWalker trial timed out.
**Verified:** default checker after each SVG edit and preview inspection; five known canon-rule errors;
alternate 56-rule matrix 0 errors/2 disclosed warnings; final converter 68.8s/0 warnings; source hash
matches; 58/58 generated coordinates, radii minima and relative offsets match SVG. Gate via Git Bash:
456 tests, 3 failures/26 skips; failures only on the same five default-map relations. Gate remains red.
**Next:** reconcile technical matrix with owner geography choice (tools edits forbidden to this agent),
strengthen primary LN/manga/anime evidence and audit remaining nonuniform proportions/open lore questions.
Do not apply, merge or deploy until default gate passes and the map review is accepted. No runtime
code, tools, pack configuration, Minecraft chunks or server state changed. PR #69 is prior reference.


## 19/11 — Primary geography evidence checkpoint (ChatGPT, `chatgpt/world-map`)

Yasuke confirmed anime/wiki placement over earlier server liberties: Fulbrosia south of Jura and
Ulgracia south of Sarion. Pulled main through `4b304cd` into a separate `ocs-map-canon` worktree.
[Research ledger](research/tensura-world-2026-11-19/geography-facts.csv): 50 claims with explicit
continuity, confidence, locator, verification and map action; [12 conflict topics](research/tensura-world-2026-11-19/contradictions.md).
Read the author's public WN chapters 13 and 31 and the official anime world guide; visually inspected
the official introductory map. Found a northern Ameld travel corridor/eastward bend and a large northern
coastal bay missing from the previous draft. LN geography passages and exact anime timestamps remain
unverified; publisher listings are not treated as evidence. Files store original paraphrases and links.
**Verified:** CSV parsing, 50 unique claim IDs, required fields, permitted confidence values, HTTPS links.
**Next:** extend LN/manga/anime coverage, redraw silhouette and river corridor against verified evidence,
retain all 58 markers/footprints, then run the default checker and inspect preview. The existing map
is still draft PR #69 and fails five default relations superseded by owner geography corrections.
No map, runtime, tools, generated terrain or server files changed in this research checkpoint.

## 19/11 night — no junk from placement, spawn zones round Tempest, staging profiled (branch `perf-and-spawns`, Claude)

Owner: fewer mobs next to Tempest, less lag. **Done** (design/decisions.md 19/11 "Placement leaves no junk"): `life/drops.js`
(no-drop removal used by trade_roads, unplace, dwargon seal/drain, forests' floor clear; every chunk hold sweeps its young
items and falling blocks on release), `design/data/spawns.toml` + `TtlSpawnZones` in `life/mortal_spawns.js` (r 150 no
natural hostiles, 25 % to r 400, 4 animals per 32 x 32), the magicule loop clears effects only when present.
**Verified locally**: `drops` (0 items, gravel kept; vanilla fill on the same column: 1 item, gravel fell) and `spawns`
pass; a bot at midnight: 101 natural hostiles refused in the town, 45 refused and 13 kept (22 %) at r 280; tests/drops.js, tests/spawns.js.
**On the next staging deploy**: `tools/server.sh test drops`, `test spawns`; `ttl spawns zone 1720 900` after an evening
of play (counts); `neoforge tps` and `execute in minecraft:overworld run neoforge entity list` (items, falling_block) to
compare with 19/11 (overworld 23-26 ms with 2 players, 313-461 items, 152 falling blocks). The frozen junk already saved
in chunks is not swept by this; kill it away from players when it shows up. Suggestions not done (owner/ops): simulation
distance 8 -> 6, Tensura spawn weights (tensuramoreconfig) if Jura stays crowded.
## 19/11 night — dev log feed `#dev-server-log` (branch `dev-server-feed`, Claude, for Yasuke)

New read-only channel in DEVELOPMENT (`tools/discord_setup.sh`, mode `rostaff`; created live 19/11, id in the Homelab
manifest) with a privacy-filtered feed of the server log, posted by the `logfeed` sidecar of the ttl-ops pod (Homelab PR
`ttl-ops-logfeed`). It is deliberately not called `#server-log`: that is the existing staff-only channel. Docs:
`docs/server.md` "Server log feed", decision row 19/11. **Verified**: 49 unit tests (filter, dedupe, batching, rate cap,
reconnect against a fake kubectl), a dry run on `kubectl logs --tail=500` and a live follow of the mc pod from a PC.
**After the Homelab merge**: the startup line `FEED  Log feed started` must appear in `#dev-server-log`; joins and leaves
are off (`FEED_JOINS`), say if Yasuke wants them on.


## 19/11 late — staging round 2 (branch `fix-staging-round2`, Claude)

Bugs from the 9d27705 deploy, fixed and verified on the local Lerfing server (design/decisions.md 19/11 "Staging round 2"):
**forests** v2 (the trees stood; `runCommandSilent` returns nothing, so all were counted failed; now real counts, no
double planting, floor cleared, giants' check box held: local tempest 40/52 giants and ~1060 understory standing, treyni
69/69; a second forced run plants ~0); **NPC gear** (goblins picked up loot into the weapon hand; rev 2, re-equip on
mismatch); **locate** (`ServerLevel.dimension` is a KubeJS property); **arena_dwarven** (stale loop after `/reload`;
local only); **banners** (were patterned; count fixed); **landmarks** lizardmen_village, lizardmen_caverns,
ogre_village_ruin, treyni_grove v2 grounded (old copies removed 100 %); **world fixes** raja_lava,
sacred_mountain_water, frost_palace_skirt; tests: npc_defend, domains, sidequests (escort), nations (bots resist Jura's
mobs), walpurgis, arena_dwarven (fill split). **On the next staging deploy** watch: `[ttl] forest tempest planted: G
giants, U understory trees, A already standing ...` (A large, G/U small: v1's trees stand), `forest treyni planted`,
`landmark ... old copy lerfing_1 ... removed`, `... placed ... grounded by`, `world fix <id>: ... 0 failed`, no `npc
gear command failed`; then `tools/server.sh test works` (`expect forest ... standing`). **Not done**: Dragon's Nest
white pad and Sealed Cave's 32 missing logs/pad (need the build repair to use the site's top block / a re-placement).

## 19/11 night — map_check spacing rule and relative anchors (branch `map-check-spacing`, Claude)

`tools/world/map_check.py`: sites keep an edge gap (distance - (r_eff1 + r_eff2)) of at least the larger `data-margin` (default 48), r_eff = max(drawn r, `min_r` from `world/sites.toml`); a circle drawn below `min_r` warns; a relative anchor more than 32 blocks from parent + (dx, dz) warns (parent/child and siblings are exempt from the spacing). Starter `world/map.svg` redrawn at `min_r` and its 7 relative anchors moved to parent + offset: 0 errors, 1 warning (roads). `world/site_sizes.md` is generated by `sites_from_builds.py`. Decision row in design/decisions.md. **Verified**: `tools/check.sh`, tests/test_map_check.py, test_world_*.

## 19/11 night — Dwargon flood sealed (branch `fix-dwargon-flood`, Claude)

TTL_DWARGON_VERSION 12: the carve's shell (footprint) is sealed (water, lava, waterlogged blocks -> tuff), the city drained
and its slabs laid again, twice (design/decisions.md 19/11 "Dwargon sealed"). `verify_build.py` fails on unexpected fluids
(`--max-fluids`, default 0). **Verified locally**: 529 flooded cells -> verify 100.00 %, 0 fluids. **On the next staging
deploy**: log `[ttl] dwargon: sealed the carve's rim: N water and M lava` (expect a few water at the crack, lava at the
cleft) and `drained N fluid cells`, then `tools/server.sh verify dwargon` must PASS with 0 unexpected fluids. **Still open**
(not in this branch): `0/10 throne room banners patterned` (the banner `data merge` fails on staging and locally); the
place audit's items 3-5 (Raja lava pool, Sealed Cave 113 blocks off with a pad, Dragon's Nest pad, Frost Palace skirt,
Sacred Mountain terraces, ogre ruin, the orange patch near the arrival); `locate.rcon` fails locally (TypeError
"Cannot call property dimension" in life/locate.js); `sidequests` merchant_escort done/stage fail locally (also before);
`arena_dwarven` duel step "not in a running match" fails locally since 19/11 evening (arenas.rcon passes).

## 19/11 evening — Lerfing placements: grounded landmarks, no duplicates, arena in the dwarf village (branch `fix-lerfing-placements`, Claude)

**Fixed** (design/decisions.md 19/11 "Lerfing placements"): landmarks are grounded on the real terrain with a foundation
(the dwarf village floated on the generator's heights); placed once per boot (the world-reset pass re-queued the one
being placed: goblin_village twice); the marker read-back that reported placed structures as "failed" is gone (orc_camp's
4 "failures" on staging may be 4 orc villages); old copies are taken out block for block (`life/unplace.js`, TOML
`remove`, builds whose plan changed); the Dwarven Arena moves next to the dwarf village (version 2, `beside`).
**Verified locally** (local Lerfing server): removals 90-100 % matched, absent copies left alone, arena v2 verify
100.00 %, old arena site clean; in-game tests landmarks, builds, build_repair, world_landmarks, lerfing, nations pass.
**On the next staging deploy** (watch the log): `[ttl] unplace landmark goblin_village old copy lerfing_1/2`, `orc_camp
lerfing_1..4` (only the spots that really hold a copy: "not there any more" for the others), `dwarf_village lerfing_1`,
then `landmark ... placed ... grounded by`, `build dwarven_arena: old copy taken out`, `dwarven_arena placed`. Then
`tools/server.sh verify dwarven_arena` and `/ttl landmark where dwarf_village`.
**Not touched**: lizardmen_village, lizardmen_caverns, ogre_village_ruin, treyni_grove keep their ungrounded v1 copies
(staging placed each at try 1 and nobody reported them); bump their version to re-place them grounded.


## 19/11 evening — quest book layout and the two chapter tabs (branch `quest-layout`, Claude)

Yasuke: the quest lines "are going through one another", and Life 1 / Life 2 chapters were one flat list.
`tools/quest_layout.py` (called by `gen_quests.py`) now places every quest: main line on one row, side branches as blocks
above/below, long or blocked lines hidden per dependency (`dep_line_visibility`) with a grey "Needs: ..." line in the quest
text (also for every cross-chapter dependency). Over 28 chapters: crossings 41 → 7, overlaps 1 → 0, lines through an icon
66 → 0. `quest_graph.py --check` and `tests/test_gen_quests.py` fail on overlaps and lines through icons. Previews:
`docs/previews/quests/` (all chapters; `-before` for mortal_life, fields, side_guild). Chapter groups "First Life — the
Mortal Realm" / "Second Life — Reborn in Tempest" (`chapter_groups.snbt`, Dutch titles in `lang/nl_nl.snbt`), Daily Deeds
ungrouped on top; Life 2 chapter `order` renumbered to the story path. Ids unchanged. **Verified offline only**
(check.sh, field names against the FTB Quests 2101.1.39 jar); the local server was busy. **To check in game after the
deploy**: `tests/ingame/quests.rcon`, the two tabs in the chapter list (and their Dutch titles with the game in Dutch),
that hidden lines stay hidden and the "Needs" line reads well. The `lane`/`col` lines in the chapter TOMLs are now
ignored and can be deleted once the open quest branches have landed.
## 19/11 evening — Tempest in the forest, the Dwarven Road, Treyni's old wood (Claude, branch `tempest-forest-road`)

Owner requests: Tempest stands on open grass (it should be deep in the forest), no road to Dwargon, Treyni's shrine in the open.
Cause of the bare core: Tensura's ancient-forest trees are jigsaw structures, and the import counts structure steps as done.
New: `life/works.js` (one-time world works runner: chunk tickets per piece, 25 ms/tick, resumable, versioned), `life/forests.js`
(patches `tempest` r 60..250 and `treyni` r 25..180), `life/trade_roads.js` (`tempest_dwargon`, 1,478 blocks); data in
`design/data/forests/` and `design/data/trade_roads/`, planned offline by `tools/lerfing/forests.py` / `trade_roads.py` on the
imported world, `tools/gen_placements.py` -> `generated/placements.js`; preview `docs/previews/tempest-forest-road.png`;
docs/server.md "Forests and trade roads". **Verified offline**: `tests/test_works.py` + `tests/works.js` (JS geometry equals the
planners', commands on synthetic terrain), `tools/check.sh`. **Not verified in game yet**: the local Lerfing server was
owned by the landmark agent; next is `tools/local.sh sync` + `test works` on a slot, then staging after the deploy
(`tools/server.sh test works`, log lines `[ttl] trade road tempest_dwargon laid` / `[ttl] forest <id> planted`). Next
possible: Tempest -> Blumund as a second `roads.toml` entry (crosses the Blumund channel: a long bridge).

## 19/11 evening — NPC weapons and self-defence (branch `npc-gear-ai`, Claude)

Yasuke: the Tempest guards and the NPCs had no weapons and did not defend themselves. `design/data/npc_gear.toml` (roles:
items + ai), `tools/npc_gear_check.py`, `world/npc_gear.js` (resident equipment, guard loop, drop filter, `/ttl npcgear`).
Tempest goblins were summoned with NBT, so Tensura never armed them; now guards hold iron katanas, Rigur a long sword and
shield, Gobta a kodachi, Rigurd a goblin club, and the guards are set on monsters near their post through their
SmartBrainLib brain (`BrainUtils.setTargetOfEntity`, falls back to `setTarget`). Easy NPC adventurers fight
(MELEE_ATTACK, ATTACK_MOB_WITHOUT_CREEPER, HURT_BY_TARGET), merchants and civilian clients flee (FLEE_MONSTER, PANIC).
**Verified offline only** (check.sh, `tests/test_npc_gear.py`). **Needs a local-server slot**: `bash tools/local.sh test
npc_defend` (and `domains`, `companions`, `sidequests`). Unverified in game, in order of risk: the brain target on Tensura
goblins (if the husk survives, look for the "BrainUtils cannot be loaded" warning); `EntityEvents.drops` firing for a
goblin (the katana check); Easy NPC reading HandItems from the preset (`equipSide` sets them anyway after the import).

## 19/11 evening — Tensura looks for the generic NPCs (branch `tensura-npc-skins`, Claude)

Yasuke: the generic NPCs (Hald, Marlo, ...) wore Easy NPC's default modern skins. Now `tools/npc_looks.py` (catalogue,
stdlib) + `tools/gen_npc_looks.py` (Pillow composer) give 23 archetypes / 50 original skins
(`pack/kubejs/assets/ttl/textures/entity/npc/look_*.png`), plus Tensura's own `falmuth_knight` texture referenced at
runtime. All 10 adventurers, 5 companions, 5 escort clients and the Outcast contact wear one (`look` in
`sidequests.toml`, variant = CRC-32 of the name). Contact sheet `docs/previews/npc_skins.png` (**waits for Yasuke's
approval**); ChatGPT prompts for hand-made art `docs/art/npc-skin-prompts.md`; sources and licences in
`design/lore/skins.md` "Generic looks". The ambient spawner (`sidequests/adventurers.js`) now prefers a kind not yet at
the place. **Refresh**: `[ambient] rev` 1 → 2 (the minute sweep, or `/ttl adventurers sweep`, removes the old ones and
`populate` refills; hired companions take the new look at their next summon, e.g. relog), `npcs.toml rev` 3 → 4 (guild
and cast NPCs respawn on the next check). **Verified offline only** (check.sh, `tests/test_npc_looks.py`,
`gen_npc_looks.py --check`); the local server was busy (another agent). **To check in game after the deploy**: skins
render on a client (front/back, slim arms of Lyra/Mira/Anne/Ilse), `tests/ingame/sidequests.rcon` and
`guild_npcs.rcon`, and that a town no longer shows the same adventurer twice.

## 19/11 evening — `/ttl` command reference (branch `ttl-command-docs`, Claude, for Yasuke)

**`docs/dev/ttl-commands.md`**: every `/ttl` command (68, plus `/locate place`) by system, PLAYER / staff / test, with its
arguments. `tools/gen_ttl_commands.py` reads the command tree and the op level from the KubeJS registration source (it
matched the live `/help ttl`, 67 entries, on 19/11/2026) and the descriptions from `docs/dev/ttl-commands.toml`; a command
without a row makes it exit 1 (`--check`). **`tools/post_ttl_commands.sh`** posts it to `#dev-chat` (pinned header, one or
more messages per group, edited in place on a re-run); docs/server.md "The /ttl command reference". **Not in CI**:
`--check` is not in `validate.py` on purpose (it would turn every open branch with a new command red); add it there once
the branches have landed. After a new command: add its row to the toml, regenerate, re-post.

## 19/11 afternoon — local test loop runs on this PC (branch `local-up-wait`, Claude)

**Verified on the workstation**: `local.sh up` cold 384 s, warm restart 48-63 s, clean stop 6-9 s ("All dimensions are
saved"), `sync` of a server script ~4 s, `test all` 70/71 ok in 23 min. Fixed: `rcon.py` pipelined the command and its
end probe, and Minecraft's RCON drops the connection when two packets arrive in one read (empty replies, "connection
closed", test-all dying on its first command, `stop` never reaching the server so every stop was a kill after 120 s);
tests now wait 2 game ticks between commands like staging's kubectl latency (`--ticks`); `test` and the first-boot
snapshot wait for the start-up builds; `sync` used a misspelt `/kubejs reload` and now uses `/reload`. **Still failing
locally**: `guild_npcs` (its forceload box is staging's Blumund; local Blumund is at -1024 70 -120). **Latent test bug**
(staging too): `build_repair` passes `minecraft:grass_block` to `ttl build expect ... cell`, an unquoted string that
cannot hold `:` ("Expected whitespace ..."); the runner does not count that message, so those three cells are never
checked. docs/server.md "Local testing" has the timings.

## 19/11 afternoon — WP-L10: fast import path, runbook and rollback, Homelab PR (Claude, branch `lerfing-l10`)

**`tools/import_world.sh`** uploads Lerfing's prepared world and arms the `ttl-import.txt` marker any time nobody is online;
the swap is the normal `tools/server.sh deploy` restart. Runbook and rollback: `docs/server.md` "World import"; design §6.3.
The dry run against staging (read-only) passed. It found nobody online, 800 local files (6.59 GB) and `/data` at 31.53 GB
with 22.05 GB used and 9.46 GB free; after the upload about 2.9 GB would stay free (90 %). The measured upload speed is
8.3 MB/s, so about 13 min. `main` is **not ready for the marker yet**: it has ttl-portals 0.8.3, no Lerfing grid and no
anchor table, so a real run today would upload and verify, then stop with exit 4 and write no marker.
**Homelab PR #60** (not merged): `mc-data` 30 → 60 Gi; ttl-ops pregen `64 256 520`. The namespace key cannot read the
StorageClass; the Longhorn 1.11.1 chart hard-codes `allowVolumeExpansion: true`. **Next**: release mod-v0.9.0, merge
L4/L5/L8 and `lerfing-import` into `main`, merge PR #60, then run `tools/import_world.sh` and `tools/server.sh deploy`
(docs/server.md, Runbook steps 3–7).
**Not done in L10**: `pack/config/bluemap/maps/tensura.conf` (mask and markers come from `gen_map.py` after WP-L2/L4).

## 19/11 — local test loop (branch `local-test-loop`, Claude)

`tools/local.sh` (local NeoForge server: up/down/restart/sync/test/snapshot/reset), `tools/ingame.sh` (the in-game
runner, now shared by `server.sh` and `local.sh`), `tools/rcon.py`, `tools/test_fast.sh`, `tools/check.sh`;
docs/server.md "Local testing". **Verified**: quick unit tier 192 tests in ~7 s warm (~70 s on a cold cache), `--all`
in ~45 s, plain full suite unchanged (192 OK, ~230 s); the shared runner against a stub RCON (verdicts, trial
pass/fail, skips) and `tools/rcon.py` against a fake server (unit test). **Not yet verified**: `local.sh up` and
everything after it never ran — the session that wrote it was not allowed to download NeoForge/packwiz-installer or
start the server. First thing to do: `bash tools/local.sh up` on the workstation, fix what breaks (pid lookup on
Windows, packwiz-installer on a localhost URL, BlueMap `ip:`), then measure cold up / restart / sync / `test all`
and list the tests that cannot pass locally in `ingame_skip_reason`. `server.sh test`/`test-all` on staging go
through `tools/ingame.sh` now: watch the first ttl-ops run after the merge.

## 19/11 day — watchdog root cause fixed (chunk tickets), events/bosses made deterministic, Treyni's shrine moved, boss_area DECIDED (Claude)

**Watchdog crash (18/11 01:24, 18/11 06:18, 19/11 03:09)**: all three have the server thread in `ForceLoadCommand ->
ServerLevel.setChunkForced -> getChunkBlocking`, from a KubeJS scheduled callback (a placer's `forceload add`).
`setChunkForced` loads every newly forced chunk synchronously; after a reset that is generation (measured on staging:
one `forceload add` of 121 fresh chunks = an 8.9 s tick). Landmark areas are 200-625 chunks; the 03:09 log shows five
landmarks placed 03:08:40-03:09:50, each in a 10-20 s tick, and the watchdog fires on the accumulated lag behind the
tick schedule. The IO worker in `CompoundTag.write` and the gen workers in `isOldChunkAround` are the chunk system busy
with the burst (no mod frame, no off-thread NBT work in our scripts or mod; no matching upstream bug found). **Fix**
(`4ddd009`): `life/chunk_hold.js` (`TtlChunks`) holds areas with region tickets (level 32, not saved) and waits for
FULL chunks (`getChunkNow`); Tempest, Dwargon, the arrival, landmarks and builds use it, give up after 10 min instead
of loading the rest synchronously. Staging: 100 fresh chunks ready in 7.5 s, no "Can't keep up"; Treyni's v4 was
placed through it. Watchdog timeout unchanged. **Not yet exercised**: a full reset boot with the new placers
(Tempest/Dwargon/landmarks only run then) — watch the next reset's log for `[ttl] chunks: holding ...` and no crash.
**Flaky `events`**: a due Blood Moon started at 18/11 23:30 because test bots counted as online and was still
active when events.rcon asserted 0 events. Fix (`3b3a820`): scheduled starts ignore `TtlBot*`; `/ttl events tick <id>`
test hook; events.rcon ends all events first. **Flaky `bosses`** (785036f, 02:44): the Orc Lord spawned 2.4 s late
(lag: a second test run, quests/TtlBotSaga*, ran at the same time), the test killed it 1 s later before any poll saw
the bots -> "lost without a fight", 6 expects failed. Fix: `tools/server.sh` `@until <s> <cmd>`, `/ttl boss expect
<p> fighting <id>`, bosses.rcon waits for the fight before kills and for the finish after. Only one agent may use
RCON at a time (lead's rule): two test runs at once corrupt each other.
**Treyni's shrine** (`fd042e9`): builds keep off a landmark's recorded box (not reach square); `beside` TOML field;
shrine v4 at anchor 2000 70 -223 (old v3 box 2032..2064 65..86 -227..-195 cleared to grass/dirt/stone after a 100 %
verify; its Treyni NPC removed and respawned at the new spot 2004.5 70 -222.5). Verify 100.00 %, `execute if biome`
flower_forest at anchor + 4 corners, `/ttlmap 2000 -223` both Treyni sites "its biomes", every biome cell of the
worked area flower_forest, groundcheck clean. The lead's later note: **Treyni biome: moot, continent will be replaced
by the imported world** — the move had already been done and verified when that arrived; it was kept (reverting would
mean placing v3 again and clearing v4, and a repo at v3 with staging at v4 would place a duplicate on the next deploy).
**tensura:boss_area**: DECIDED (owner) — outside the story rules; `world.rcon` asserts it.
**Mortal Realm waypoints**: skipped (night agent verified 99.97-100 %).
**Tests on `40e1e51`**: ttl-ops (fresh boot, ~09:50-10:15) **all green (70/70)**; my run 10:15-10:44 70/70 ok (events,
bosses, world included; the only failure was `build_repair`, a file of the not-yet-deployed PR #36 in my checkout).
**PR #36 `placer-terrain-repair`** merged with `--no-ff` (conflicts: decisions.md kept every row, gen_data BUILD_KEYS
beside + repair*, `_example.toml` both field docs, generated files and index regenerated); `repair.js` reads a chunk only
when `getChunkNow` has it. Offline 169 unit tests OK, validation passed (`854089a`, pushed with `60d9d07`).
**Staging after the merge**: `test build_repair` 0 failing (`repaired 57 foundation, 50 skirt, 28 lava (12 fills, 5 ticks,
163 ms; depth 48, ring 8; 0 gaps run deeper, 0 columns not loaded)`), `test builds` 0 failing (void hut: 0/0/0, 151 ms).
ttl-ops on `60d9d07`: 70/71 (`arrival`: the reborn bot stood 36 blocks from the arrival point 10 s later; passed twice
alone right after; cause not found, nothing in the log moved it: watch it). My test-all 11:13-11:53: 69/71, `arena_dwarven`
(wave-3 mobs knocked the bot out of the arena: "left the arena", result partial; also failed alone once) and
`trial_vengeance` (RCON round trips took 15 s under load, the nemesis killed the bot before the test's kill: "faltered").
Fixed in the tests: knockback resistance for the arena bot; the vengeance bot gets resistance, the test waits for the
nemesis with `@until`, kills it at once and waits for `ttl.trial.passed`. Both pass alone after the fix. Note: `@until`
retries log a `[ttl] ... command failed` line per failed attempt, so after a test run the log grep for `failed` shows
those waits too (only the last reply counts).
**Test-all 12:15-12:55 on `b13d7cd`**: 69/71: `arrival` (bot 3 blocks off right after rebirth) and `quests` (the Walpurgis
leave took longer than the fixed 2 s). Causes: three wild `tensura:direwolf` stood within 16 blocks of the arrival point
(272 -623) and attacked/knocked the bot (also the 10:49 "36 blocks" failure); walpurgis join/leave teleports are
asynchronous. Fixed in the tests: arrival.rcon kills direwolves within 96 of the arrival first; quests.rcon and
walpurgis.rcon wait with `@until` for in/out. All three pass alone. **Owner question**: wild direwolves (hostile) spawn
right at the Life 2 arrival on the "safe rim": should the arrival get a hostile-spawn-free radius like Tempest and
Wayfarer's Rest (`life/mortal_spawns.js`)? Not changed (gameplay decision).
**Final**: ttl-ops on `adbd6ab` (main with PR #36, these test fixes and PRs #37/#38/#40; fresh boot ~12:50) = **all tests
green (71/71)**. That boot placed Dwargon v7 through the chunk tickets (`holding 156 chunks for dwargon`, then `repaired
14365 foundation, 2361 skirt, 142 lava (2237 fills, 589 ticks, 34125 ms)`), no watchdog, only two 2-4 s "Can't keep up"
at start-up.

## 19/11 night — overworld reset done: every build verified on the new world, terrain repaired by hand, test-all 70/70, pregen running (Claude)

**State**: the 03:05 reset (`ttl-backup/20261119-030516`) generated the new site terrain; Tempest and Dwargon were placed on the
03:05 boot, the 7 landmarks and 28 overworld builds on the 03:07 boot after one crash (below). `ttl build list` / `ttl landmark
list`: everything placed. `/ttlmap 435 -1000` = site dwargon flat y72, plains; `ttlmap 370 -2402` = dragons_nest flat y190, frozen_peaks.
**Verify 1:1** (`verify_build.py <name> --log --min 98`, after all repairs): amrita, ballachia, blumund, clayman_castle, dragons_nest
(6 snow layers), dwarven_arena, el_dorado, elmine, englassia, forgotten_dragon_city, frost_palace, great_holy_mountain, heaven_tower,
jia, laura, lubelius, marris, morgdahl, nasca, nostraille, raja, sacred_mountain, sealed_cave, siltrosso, spirit_gate, treyni_shrine,
ulgr_nature_park, tempest (3 lanterns), dwargon all **100.00 %**; coleus 99.99 (lightning-rod facing); walpurgis_hall 100.00
(`ttl:walpurgis -40 49 -79`); spirit_dwelling 99.99 (`ttl:spirit_domain -44 23 -66`, vines); test_hut 100.00; mortal_spawn 99.90;
the 6 Mortal Realm waypoints 99.97-100.00 (`--dimension ttl:mortal_realm`).
**Site biomes** (`execute if biome` at the anchor and the 4 box corners + `/ttlmap`): every overworld build sits in its site biome
at all 5 points, except Raja's SW corner (river: the lake it is built on, `keep` site) and **Treyni's shrine** (anchor and the east
corners in `tensura:ancient_forest`, west corners flower_forest): the survey had to put it 61 blocks east of its site centre because
the grove landmark's keepout (reach 48 + 24 + margin 8) covers the canon spot. Fix needs a site change (mod release) or a new spot
plus removal of the old copy; left for the day.
**Ground** (throw-away capture of each box + a 4-column ring: gaps under the build connected to open sky, ditches in box columns
the blueprint leaves undefined, stray lava/fire) — repaired by hand on staging (decisions.md row of 19/11, not reproducible from
the repo): Nostraille's ravine under the north edge (275 columns), Laura and Sacred Mountain edge caves, El Dorado's plaza-edge
slit and its north lava pool, Coleus' west-edge water crevice, Amrita's 25-deep sinkhole beside the stair, the 2-row ditches inside
the Heaven Tower, El Dorado and Elmine boxes, stray lava near 8 builds and under Dwargon. Re-checked: no sky-connected gap or lava
left at any build; remaining "gaps" are closed cave roofs (Blumund, Sealed Cave, Dwarven Arena, Sacred Mountain: 5+ blocks from
any opening). A shallow 4-deep grassy bowl in Dwargon's NE box corner (x 496-508, z -1113..-1095) was left (outside the walls).
**Tests**: `MSYS2_ARG_CONV_EXCL=/data bash tools/server.sh test-all` at 04:40-05:07 = **70/70, 0 failing** (with the guild_npcs fix
of the entry below; an earlier run at 03:28 was 69/70, only guild_npcs).
**Pregen**: held back during the checks (temporary `/data/ttl-pregen.done`, removed again), started by hand at 05:08 with ttl-ops'
commands (`dh config generation.chunkMode INTERNAL_SERVER`, `common.threadPreset BALANCED`, `dh pregen start minecraft:overworld
-2088 -616 450`): ~35 cps, ETA ~6 h, so it will NOT finish tonight; ttl-ops stops it at 07:00 (or when someone joins) and resumes
next night (no `ttl-pregen.done` until ≥ 99 %). Result: reached radius ~250 / 450 chunks (~30 %) and was cancelled at 07:21 (end of the night window), no crash; the next night resumes from the centre and skips the done part.
**Crash at 03:09** (`crash-2026-11-19_03.09.53-server.txt`): watchdog, the server thread waited 60 s in a `forceload add` of the
landmark placer for a chunk while `IO-Worker-3` spun in `CompoundTag.write` (fastutil map iterator: looks like an NBT map changed
during the chunk save) and generation workers waited on that IO worker (`isOldChunkAround`). Second boot clean; one more
watchdog crash on 18/11 06:18 in the same family. Watch for it during pregen (ttl-ops stops the pregen for the night on a crash).
**Open**: Treyni shrine biome (above); a placer pass for undefined box columns, caves and lava next to the box (so a future reset
needs no hand repairs); the IO-worker hang; BlueMap still rendering the new world.

## 19/11 — PR #35 `site-biomes` (merged, `785036f`, ttl-portals 0.8.3): biomes and terrain round every canon build; overworld reset runbook (Claude)

**Why**: Yasuke on the public BlueMap: "the biomes of the map don't match up — Dwargon should be on a plain, not an ice
mountain." Audit (`/ttlmap` at every overworld build/landmark spot and 4 points 120 blocks out, live server 19/11):
Dwargon frozen_peaks at y 170 and snowy_slopes all round; the Dwarven Arena jagged_peaks y 158; the Dragon's Nest
old-growth spruce taiga at y 125 (not a peak); the Sacred Mountain a meadow at y 77 (no mountain); the Great Holy
Mountain plains at y 70; El Dorado jungle at y 115; Lubelius grove at y 120 (snow); the Forgotten Dragon City on a
river; Coleus in desert_of_death; Spirit Gate and Treyni dark_forest. Full table in the PR.
**Owner decision (coordinator, 19/11)**: players have built nothing, so the Tensura overworld is **reset from scratch**
after this change; the `/fillbiome` fix script and the partial Dwargon reset were dropped.
**What**: `sites` in `canon_regions.json` (43: every overworld build, every `landmarks.toml` landmark, Tempest,
Dwargon, plus landform sites for Dwargon's plain, the arena, the Dragon's Nest massif, the Sacred Mountain, Velgrynd's
volcano and El Dorado's volcano); mod `CanonSites` (weights, organic edges, presets), `CanonSiteTerrain`
(`ttl:canon_sites`, wraps `final_density` and `initial_density_without_jaggedness` in `noise_settings/overworld.json`),
a `ridges` channel for `ttl:canon_map` (`density_function/overworld/ridges.json`), site biomes first in `CanonBiomes`,
`/ttlmap` prints the sites and ridges. Dwargon's land palette lost snowy_slopes. Docs: docs/server.md "Site biomes",
decisions.md row of 19/11, world.md and dwargon.md (owner override).
**Verified offline**: `gradlew build` OK; CanonGrid self-check passed (synthetic: 778 columns outside the sites
byte-identical, ragged biome edge, flat surface exactly at `ground` and solid below it, presets, config errors;
real: 43 sites parse cleanly, every centre on canon land, ground 64..240, the Life 2 arrival only near safe site
biomes; the Jura ring checks unchanged); `tests/test_canon_sites.py` (5 tests: every build/landmark/Tempest/Dwargon
covered by a big enough site at its spot, known biome ids, the owner override). **Not verified**: the new density
function and the `ridges` channel in a running server (no local server run): check with `/ttlmap` right after the
deploy (step 2), before the reset.

### Overworld reset runbook (lead; in this order)

1. **Release the mod from this branch, before merging**: `git checkout site-biomes && python tools/release_mod.py`
   (0.8.2 -> 0.8.3, gh release `mod-v0.8.3`, packwiz relink, validate, commit + push to the branch). Then merge the PR
   (`--no-ff`). Never let `noise_settings/overworld.json` or `ridges.json` reach `main` with the 0.8.2 mod: it does not
   know `ttl:canon_sites` / channel `ridges` and the overworld would not load (ttl-ops auto-deploys `main`).
2. **Deploy only when nobody is online**: `bash tools/server.sh deploy` (refuses with players online; ttl-ops may
   also deploy `main` on its own when the server is empty). Check: `bash tools/server.sh logs 2000 | grep -E "canon
   (map|biomes)"` shows `43 sites` and `biomes for 40 of 43 sites`, no `canon site ... skipped`; `bash tools/server.sh
   rcon "ttlmap 435 -1000"` says `site 'dwargon' (flat y72)`, `surface y72`, `minecraft:plains`;
   `ttlmap 370 -2402` names `site 'dragons_nest' (flat y190)` inside `canaat_summit` (mountain), `surface y190`;
   `ttlmap -4808 3240` savanna. If the overworld
   fails to load, roll back the pack commit (the old world is untouched until step 3).
3. **Reset**: stop the night pregen (`bash tools/server.sh rcon "dh pregen stop"`), then
   `kubectl --kubeconfig ~/.kube/ocs-two-lives.yaml -n ocs-two-lives exec deploy/mc -- sh -c 'echo minecraft:overworld > /data/world-ttl/ttl-reset.txt'`
   and `bash tools/server.sh restart`. The log says `[ttl] world reset: [minecraft:overworld] regenerate; old terrain in
   ttl-backup/<time>` (region, entities, poi and the overworld's DistantHorizons* files are moved, nothing deleted).
   Player data, the Mortal Realm, the Spirit Corridor and the other dimensions stay.
4. **DH LODs**: WorldReset moves `/data/world-ttl/data/DistantHorizons.sqlite*` into the backup; check that
   `ls /data/world-ttl/data/DistantHorizons.sqlite*` only shows a fresh, small file. If an old one is still there,
   scale the server down (`kubectl ... scale deploy/mc --replicas=0`), delete `/data/world-ttl/data/DistantHorizons.sqlite*`
   from a debug pod on the volume, scale back to 1.
5. **BlueMap**: `bash tools/server.sh rcon "bluemap purge tensura"`, then `bash tools/server.sh rcon "bluemap force-update tensura"`
   (renders as chunks generate; `bluemap` shows the queue).
6. **Pregen**: `kubectl ... exec deploy/mc -- rm -f /data/ttl-pregen.done`, so ttl-ops' night pregen walks the
   continent again.
7. **Placements, then verify**: about 45-90 s after the start Tempest, Dwargon, the 7 landmarks and the 28 overworld
   builds are placed one by one (`[ttl] tempest placed`, `[ttl] <name> placed: corner ...`); `/ttl build list` and
   `/ttl landmark list` must show all placed. Then `python tools/verify_build.py <name> --log --min 98` for each
   overworld build (and the dimension builds if anything moved), a column check for floating or wet blocks under each
   footprint (Nostraille and Amrita had both before), `/ttl arrival`, and `bash tools/server.sh test-all` = 0 failing.
   Look at the map at https://map.daviddelporte.com once the render has passed Dwargon.

## 19/11 — PR #34 merged (issues #12, #4, #5 closed); 13 builds verified, again after the world reset (Claude)

**Merged**: PR #34 `fix-issues-12-4-5` with `--no-ff` into main (`eca49d2`); GitHub closed #12, #4, #5. Conflicts: decisions.md
(kept every row), pack.toml (regenerated); gen_data, gen_quests, gen_npcs, build_structures --check, config_index re-run.
**While I worked** PR #35 (site-biomes, ttl-portals 0.8.3) landed and the Overworld was reset: every overworld build was placed
again on the new terrain (the mc pod crashed once on the 60 s watchdog inside a `forceload add` of the landmark placer, then
placed all 38 builds on the second boot). My first verification (old world, 12 builds + Walpurgis, all >= 99.9 %) and my manual
repairs on it are gone; everything below was **re-verified on the new world** at ~03:30 (nobody online, pod stable).
**Verified** (`verify_build.py <name> --log --min 98`): dwarven_arena 100.00, amrita 100.00, coleus 99.99 (9 `lightning_rod` facing
defaults), elmine 100.00, great_holy_mountain 100.00, jia 100.00, morgdahl 100.00, nasca 100.00, nostraille 100.00, raja 100.00,
siltrosso 100.00, ulgr_nature_park 100.00, walpurgis_hall 100.00 (`walpurgis_hall ttl:walpurgis -40 49 -79`; v2, 10 glazed
terracotta facing defaults). Wet: no waterlogged block and no water on defined air in any of them (Amrita included). Floating: no
column of any build is unsupported except Nostraille (161 columns, 3.5 %) and Ulgr Nature Park (185, 4.0 %): their lowest dirt layer is
the roof of a natural cave (air 6 to 56 blocks below, 12-27 for Nostraille); the terrain fit only fills when the heightmap surface is
below the layer, so a cave under a hillside edge stays open. Invisible from outside, the layer itself carries the hall. (Later the
same night: Nostraille's cave was a ravine open to the sky at the hall's north edge and was filled by hand; Ulgr's caves have no
opening near the park. See the entry above.) Not fixed in the placer:
a probe-and-fill pass in `terrainCommands` (look down from the layer's lowest block through air/water, fill to the first solid) would
close them; it touches every build on every reset, so it needs its own PR and a re-verify of all builds.
**Fixes** (decisions.md row of 19/11): Dwarven Arena moved to -30 -850 (the old spot lay inside the dwarf village's keepout once the
survey moved it; on the new world the village stands at its nominal 250 -740, the arena at -30 72 -850, both fine); new TOML field `dry`
(builds.js drains the box before placing; docs/server.md "Dry builds"; Amrita `dry = true`; on the old world 11 waterlogged stairs and
slabs flooded its gallery floor); Walpurgis Hall v2 (two hanging lanterns now on chains); `arena_dwarven` test (bot got resistance:
wave 2's armorsaurus felled it); `guild_npcs` test (the forceload box of Fuze's stand follows Blumund's new spot: corner
-1086 65 -224, Fuze at -979 76 -163).
**Tests**: ttl-ops: `eca49d2` 69/70 (events flaked, green alone), `cf7ad82` 69/70 (arena_dwarven, now fixed), `785036f` (PR #35,
after the reset) 69/70 (bosses, green alone). My own full `test-all` on the new world after the placement (`MSYS2_ARG_CONV_EXCL=/data`
needed from Git Bash, or the trial verdicts read nothing): **69/70, only guild_npcs** (stale Blumund coordinates), fixed and green
alone; 70 test files in all (trial_climb, race_lock, arena_dwarven green), 157 offline unit tests OK. ttl-ops redeploys only when the
pack changes, so the next pack commit gets the full ttl-ops run: expect 70/70, and watch `events` / `bosses`, which flaked once each.
**Open**: Nostraille/Ulgr cave roofs (above; Nostraille filled since); Mortal Realm waypoints (verified since, see the entry
above); `tensura:boss_area` question (entry below); the watchdog crash when the landmark placer forceloads a big area on freshly
reset terrain (PR #35's domain: `forceload add` blocks the tick; consider smaller strips or `--no-wait` chunk loading). Git Bash on
Windows: `push-scripts` and `exec ... /data` need `sh -c "tar -C /data -xf -"` / `MSYS2_ARG_CONV_EXCL=/data`.

## 18/11 night — PRs #18–#33 merged into main; ttl-ops on `bae23df`: **67/67 green** (merge-and-test run, Claude)

Last step: the maker's-stamp lore line fix (`withColor` overload, artifice.js) came after the green run; `test artifice`
was green with it via push-scripts, and ttl-ops on `66941f0` is **67/67 green** as well (log clean of KubeJS errors).

**Merged** (`--no-ff`, GitHub shows them merged): #19 arenas, #21 codex/life2-saga-wiki (it supersedes #18, which is
closed with a comment), #22 world-w1, #23 world-w2, #27 sidequests, #25 roadmap-suggestions, #20 project-status,
#26 codex/tempest-realm-heraldry, #29 world-w3, #28 paths-n0n1, #30 paths-a1, #31 paths-n2, #32 paths-n3, #33 paths-c1.
Conflict rules as before: decisions.md keeps every row; generated files took main's side and were regenerated
(gen_data, gen_quests, gen_npcs, config_index, previews gallery, packwiz refresh); gen_data validators of both sides kept.
Combined by hand: boss.js (W2's instancing + #21's `event` summon option + W1's `TtlChronicle.bossKill` in `finish` +
the story-transport announce with W2's echo suffix); factions.toml `stage` keeps both path rank-4 rows; CLAUDE.md data
schema lists `ttl.boss.lastkill`, `ttl.boss.arena`, `ttl.boss.queue` (docs/server.md too).
**Review changes**: #21/#18 staff command audit (`ops/cmdlog.js`) records only player and RCON commands (it hooked every
command the scripts dispatch); #26 accepted as is (Tempest rings and Mortal waypoints are built but not placed by a
phase switch); world.toml gains `light_deed 1`, `dark_deed -1.5`, `rest 1` (O-C2) for roads.js; `/ttl reset` clears the
Artificer; `/ttl paths` describes the real Artificer and the Crossroads.
**Fixes from the ttl-ops runs** (details: decisions.md rows of 18/11 night): claim lookups (KubeJS shadows
`ServerLevel.dimension()`), arena/Walpurgis yaw, arena exemption from duel liability, Walpurgis council NPCs moved into
the hall, Blood Moon kills on `EntityEvents.death`, LootJS `addTableModifier`, Amrita search 128, calamity region lookup
through `TtlWorld.ownerAt`, sidequest `byUuid` scan + continent signature, domains testbreak, artifice `getClass` and
synchronous give/clear, legion test hook, `ttl story testunlock mark|restore|drop` (quests.rcon's Act VII bot had unlocked
Veldora for everyone on staging; dropped with `drop veldora`), plus test fixes (world sync, events_pack end-all, bosses
queue answer and Gazel position, sidequests forceload, artifice main hand, necro_ranks cleanup order).
**Test results**: ttl-ops on `d1e0c09` = 66/67 (only sidequests: the ambient loop spawned an adventurer during the count; fixed with `ttl adventurers hold`; the run of 8a151d4 still failed it on the escort (a client whose chunk unloaded read as fallen) and on clearing an unloaded green, both fixed in `bae23df`, whose ttl-ops run was 67/67 green). Before that: ttl-ops on `a78843b` = 62/67 (artifice, bosses, necro_legion, necro_ranks, sidequests failing); after the
fixes artifice, necro_legion, necro_ranks and sidequests passed one by one on staging (push-scripts), bosses still showed
`ttl discord expect TtlBotBoss boss 1` = 0 after a reload (check on the fresh boot). The commit after this one gets a full
ttl-ops run: read `kubectl --kubeconfig ~/.kube/ocs-two-lives.yaml -n ocs-two-lives logs deploy/ttl-ops --tail=60`.
**Open / owner**: does `tensura:boss_area` count as inside the continent? W1's default (`world.toml [continent]
inside_dimensions` = labyrinth, spirit_domain, hell) says no, so the mod's bosses spawn there as shipped; left as is until
Yasuke answers. **Not verified in game**: the 11 canon landmarks with `verify_build.py` (all placed except Amrita, now
surveying 128 blocks), Walpurgis Hall build, Mortal Realm waypoints (`test mortal_waypoints`), Discord nation roles and
staff audit with real accounts, the council NPCs at the Walpurgis thrones. A local stray: an older copy of
design/architecture/world-state.md was uncommitted in the main checkout; PR #22's version (a superset) is on main.

## 18/11 night — branch `paths-c1` (PR open, depends on #28, now on main): WP-C1 moral-choice scenes

Engine `pack/kubejs/server_scripts/ttl/choices/engine.js` (`TtlChoices.register/spawn/resolve/take`, director poll
`choice_scenes`), scenes 4.1-4.4 in `choices/events_c1.js` (sick village, bandit hostages, starving band, wounded monster
that wants a name), `/ttl choice` in `choices/commands.js`, data `design/data/choices.toml` (checked by
`gen_data.check_choices`, unit test `tests/test_choices_data.py`), guide page "Crossroads of conscience", roadmap line.
Offline: validate.py passed, unit tests OK. **Not run in game yet**: `bash tools/server.sh test choices`; watch for
`[ttl] choices` errors. WP-C2 adds 4.5-4.12 as `choices/events_c2.js` with `TtlChoices.register` (API in the engine header).
Verify in game: Tensura naming/Dominate set IExistence name/permanent/temporary owner on a NoAI beast; `tensura:orc` bandits
fight and the captain's `attribute` takes; `tensura edit stat <p> ep current add`; ManasCore `getLearnedSkills` sees
Predator/Gluttony/Starved; `getEntitiesWithin(new AABB(...))` from Rhino; food detection (`DataComponents.FOOD`).
## 18/11 evening — branch `sidequests` (PR open, not merged): side quests, ambient adventurers, companions

Isekai side content for Life 2 (design: `design/quests.md` "Side quests", decisions.md rows of 18/11/2026):
`pack/kubejs/server_scripts/ttl/sidequests/` (places.js, side.js, companions.js, adventurers.js, commands.js), data
`design/data/sidequests.toml` (checked by `tools/sidequests_check.py` from gen_data), presets `ttl_adv_* / ttl_comp_* / ttl_client_*`
(gen_npcs.py), chapters 20-23 (47 side jobs, 64 FTB quests). Companions are Easy NPC (no new mod). Offline: validate.py passed,
unit tests OK (tests/test_sidequests.py). **Not run in game yet**: `bash tools/server.sh test sidequests` and `test companions`
after the merge (needs Tempest, Dwargon, Blumund and Englassia placed); watch for `[ttl] side` / `[ttl] companion` /
`[ttl] adventurers` errors. Radiant boards (WP-W13/W15) should call `TtlSide.start(server, player, kind, params)` and `TtlSide.listen`.
## 18/11 late afternoon — public roadmap + #suggestions (branch `roadmap-suggestions`, Homelab `ttl-ops-suggestions`)

Live on Discord already (made by the scripts of this branch, idempotent re-runs verified): `#roadmap` (START,
1572640872615518290) with its pinned how-to and the three sections of `docs/roadmap-public.md`; the forum
`#suggestions` (COMMUNITY, 1572640884049055874) with tags, 👍 reaction, guidelines and the pinned, locked how-to post;
updated how-tos/maps in #welcome, #ideas-and-feedback, #contribute. GitHub labels `suggestion`, `quality-of-life`,
`status:planned|in-progress|done|declined` exist. The sync (`suggestions.sh` in ttl-ops) was tested by hand on the node
against a bot-made test post (issue #24: created, Under review → Planned → Declined + archived, idempotent re-runs),
then the post and the issue were deleted. **Not live until the Homelab PR is merged** (ArgoCD restarts ttl-ops).
Open: Yasuke enables the board's "Auto-add to project" workflow (`docs/server.md`, "Roadmap and suggestions"); after
PR #20, `docs/project-status.md` can point to `#roadmap`. Keep `docs/roadmap-public.md` in step with project-status.

## 18/11 afternoon — six PRs merged into main (`7898d90`), ttl-ops run pending

Merged with `--no-ff` in this order: #15 ocs-bluemap-pregen, #11 polish, #13 lore-pass, #17 rules-pass, #16 quests-web, #14 story-s7
(GitHub closed all six as merged). Conflict calls: decisions.md keeps every row; generated files (data.js, quests.js, FTB SNBT,
en_us.snbt, index.toml, pack.toml, docs/configs.md) took main's side and were regenerated (gen_data, gen_npcs, gen_quests, config_index,
packwiz refresh; `quest_graph.py --check` passes: 21 chapters, 304 quests). Deliberate overlaps: chapter 10's Milim/dragon-city location
now points at the lore-pass build (survey start 2340 905 v3 -> centre 2340 830, radius 140; the old v2 copy at 2510 575 is still in the
staging world); chapter 9's entry dropped the redundant `kings_test/act_two` (orc_lord/envoy already needs it in #16's web) and
`whirlpool/ep_20000` joins the EP ladder through `reborn/ep_20000` (tests/test_story_chapters_9_10.py adjusted). quests.rcon: the web
section is 6, the chapter 9-10 section is 7. Verified offline: `validate.py` passed on every merge commit, 92 unit tests OK.
**Not yet verified in game**: ttl-ops deploys `7898d90` when nobody is online and runs test-all (last green run was on `2863fe1`); new
tests to watch: duel_liability, wayfarer_guard, tempest_pass2, quests sections 6-7, registry/absorb/guild_npcs/nations. Dwargon v6
and Tempest v3 re-place on that boot. Still open: PR #19 `arenas` (merge after this run; wire `absorb/liability.js` to treat
`TtlArenas.inArena(level, pos)` as exempt, guarded with a typeof check; optionally move the Walpurgis council NPC spots to the new
hall) and PR #18 (not reviewed here).

Last update: 18/11/2026 ~14:10 (Brussels), by Claude (day run for Yasuke: codex-integ merged, test fixes recovered,
tests kept out of Discord, **`bash tools/server.sh test-all` = 0 failing on main `061a1a2`**).

## Today (18/11, day)

- **Lore pass (branch `lore-pass`, PR open):** `design/lore/lore-pass-2026-11.md` lists every finding and change. The City of the
  Forgotten Dragon moves to survey start (2340, 905), version 3 (the v2 copy at 2510 575 stays in the staging world until that
  terrain is reset: the placer never removes an old version); region M palette and three region names changed (ungenerated chunks
  only); `TtlCorridor.canon()` gives every Voice of the World line the canon "Notice." header; NPC dialog rev 3 (Fuze/Yuuki/Razen/Eren
  intros). **Not verified in game** (no server access from the lore pass): the new survey spot (watch the `[ttl] builds` log line for
  how far it drifted and the water share), the Milim NPC standing before the throne at the new spot, the "Notice." prefix in chat
  during a corridor run (`test guide`, `test arrival`, `test story`).

- `dd85654` **codex-integ merged into main** (ChatGPT PRs #6–#9, closed as merged): 5 canon builds (el_dorado, frost_palace,
  sacred_mountain, ballachia, heaven_tower), 28 NPC skins, Wayfarer's Rest 39×39 v2, world-audit repairs with version bumps
  that re-place 13 builds. Deployed to staging 11:20 (`deploy --force`; Belgiancandyman was online and got kicked). Boot clean.
- `849a1f2` **tests stay out of Discord**: `TtlDiscord.post` drops every line while `ttl.discord.muted` is set
  (`tools/server.sh test|test-all` set `/ttl discord mute on|off` around the run) or while any test bot is online.
  `/ttl era reset` (era 1, silent), `/ttl boss cooldown clear <id|all>`.
- `3e7c05c` **the morning's test fixes recovered from `git stash`** (the earlier session verified them green per test on staging
  10:46–11:08 but never committed): `/ttl as <player> <command>` (`TtlCmd.runAs`) for FTB party commands of bots, nation
  extra claims through the dispatcher, `ttl absorb expect <player> ...`, Easy NPC remove discards, Carrion two-hit kills,
  `era testmark|testrestore|next silent|set`, Fuze tested in Blumund, cast without the presets check. The stash was applied
  wholesale (then dropped); see the decisions.md rows of 18/11/2026.
- `6609962` **arrival grace + NPC hold + Ballachia 128**: ttl-ops on `3e7c05c` left 3 failing (arrival, guide, guild_npcs):
  a Blade Tiger and a Barghest killed the fresh bots 2–6 s after landing on the rim (the rim is safe from magicule, not from
  Tensura's mobs) → `arrival.toml grace_seconds = 20` (life/mortal_immunity.js refuses all damage to a Life 2 soul for 20 s
  after rebirth; never `/kill`, never in Life 1, `ttl reset` drops the stamp); the periodic NPC check removed the test copy
  before its expect → a test-hook `guild npc spawn` holds the check 15 s; Ballachia found no dry spot within 32 blocks →
  `search = 128` (placed 68 blocks from the canon point, 5 % water). ttl-ops on `6609962`: **1 failing** (guide: the grace
  swallowed the test's `/kill` of a just-reset bot) → fixed in the next commit, `test guide` green via push-scripts.
- **Tailscale SSH check mode** hit at ~11:40 ("Tailscale SSH requires an additional check. To authenticate, visit:
  https://login.tailscale.com/a/…"); only Yasuke can approve it in a browser (done ~12:20). Until then every `tools/server.sh`
  call hangs; ttl-ops keeps deploying and testing every push (verdict: commit status "ttl staging" on GitHub, the names in
  Discord #server-log, the full table in the ttl-ops pod: `kubectl -n ocs-two-lives exec deploy/ttl-ops -- cat /work/tests.txt`).
- **Builds verified** (`tools/verify_build.py`, pass mark 98): el_dorado, frost_palace, sacred_mountain, heaven_tower, ballachia,
  blumund, englassia, laura, marris, treyni_shrine, clayman_castle, dragons_nest, forgotten_dragon_city, lubelius, sealed_cave,
  spirit_dwelling all **100.00 %**; spirit_gate 99.96 % (55 mismatched of 129,960); dwargon v5 99.99 % (42 of 797,912);
  mortal_spawn v2 (Wayfarer's Rest) 99.92 % (19 of 23,867). All above the 98 % mark.
- `8ac1124` arrival grace never swallows `/kill` / the void and only holds in Life 2 (`ttl reset` drops the stamp) → ttl-ops
  **1 failing** (arrival: alive but shoved 9 blocks by the mobs it can no longer be hurt by) → `061a1a2` arrival.rcon: after 10 s
  only `alive` + `near 32`. **Full `test-all` run from this PC on `061a1a2`: 0 failing** (ttl-ops does not re-run for a
  tests-only commit, its last status is the 1 failing of `8ac1124`; the next pack change will show green).
- Staging state after the runs: `/ttl era reset` done (era 1), legendcap reset, cooldowns cleared, no bosses out, events ended,
  war flags cleared, mute off, no nation; registry holds only ultimate_Yasuke_'s chosen_one + usurper (a real player).

## Next steps (in order)

1. Main is green (`test-all` 0 failing, 18/11 14:05). The next pack change gets a ttl-ops run; expect ✅.
   If Tailscale SSH asks for a check again, run `ssh root@100.109.28.21` in a terminal and open the printed link.
2. Builds: all verified today (above); only `spirit_gate` has 55 real mismatches worth a look (`verify_build.py spirit_gate minecraft:overworld -246 68 106`).
3. Before launch: the list below once more on the final pack (era reset etc. were run today, ~13:10).
4. Night pregeneration (ttl-ops `night_pregen`) and the public BlueMap route are in Homelab PR branch
   `ocs-bluemap-pregen` (docs/server.md); after merge: Yasuke adds the `map` DNS record + tunnel rule, then watch the
   first night (TPS, memory, disk). Wave B leftovers (WP8 event pack, WP10 boss payouts, WP11 Discord roles).

## Live / merged on main (night 17–18/11)

- Newcomer magicule-poison deaths fixed (Life 1 and corridor souls protected; Tempest green sheltered 56 blocks).
- Jura forest rings (mod 0.8.2): safe rim (Life 2 arrival + world spawn at 271 -624 on the road to Dwargon),
  dark middle, deadly ancient_forest core around Tempest (Tensura's real 20,000 magicule, owner decision).
- Blind spots: Life 1 items stripped at death (ender chest, Curios), Tensura items banned in Life 1
  (`design/data/mortal_banned.toml`), karma anti-farming, registry keyed by UUID + pool hygiene, boss Tombstone gate.
- Sprint 3–4 wave A: soul gem/carryover (WP1), boss framework (WP2; Shizu + Rimuru at Tempest), reputation +
  renown (WP3), registry v2 with max 10 Legendary holders + transfer routes (WP5), event director + World's
  Favor (WP7), BlueMap (WP12, LuckPerms removed again), economy with Lightman's Currency on Tensura coins,
  magical "Mana Ledger" ATM, Adventurer's Guild (WP9), Fuze + receptionist Easy NPCs.
- Generic canon-build placer (`design/builds/*.toml`, `life/builds.js`) + 13 builds: sealed_cave, spirit_gate,
  spirit_dwelling (`ttl:spirit_domain` dimension, Life 2 teleport), treyni_shrine, dragons_nest, blumund,
  marris, englassia, lubelius, clayman_castle, forgotten_dragon_city, laura (+ test_hut in the corridor).
- Quests ch. 2–6 (129 quests total). Discord rebuilt (START / MINECRAFT / COMMUNITY / DEVELOPMENT / STAFF,
  how-to pinned first in every channel, EN + NL).

## Before launch (state the tests leave behind)

Full table and the ops commands: docs/server.md "Before launch: what the tests leave behind". Short form, nobody online:
1. `bash tools/server.sh test-all` green on the final pack; wait for the ttl-ops run to finish.
2. `/ttl era reset` · `/ttl registry legendcap reset` · `/ttl boss abort` · `/ttl boss cooldown clear all` · `/ttl boss testparty clear`
   · `/ttl events end` · `/ttl absorb war clear` · `/ttl guild roll` · `/ttl discord mute off` · `/ttl party poll` · `/ttl nation sync`.
3. `/ttlbot list` none, `/list` nobody, `/ttl registry` no holder, `/ttl nation top` empty, `/ttl era` = era 1, log clean.
4. Only by hand with the server down, if wanted: bot playerdata, bot FTB personal teams, bot scoreboard rows, `test_hut`.
Tests never post to Discord any more (`server.sh test|test-all` mute + the bots-online rule in discord.js; `legendary`/`absorb`
advance the era silently and restore it with `era testmark`/`testrestore`).

## Open owner questions

- Answered 18/11/2026 (branch `rules-pass`): gluttony Rare; Fuze's contracts at the desk unless `lore = true`; awakening
  claim once per soul; duels anywhere with damage liability; unpaid upkeep = debuffs. Still open: may a Skill Core draw
  gluttony (it can now, like the other Rare absorbers)? BlueMap public (answered: public, not yet wired).

## Offline world audit for Yasuke

The [November audit](audits/world-audit-2026-11.md) compares 22 territory masks, 43 map pins, 14 canon templates and seven runtime jigsaws. El Dorado and Frost Palace already project onto X and I land. The audit includes source changes for 12 version-2 survey/fixed builds, bespoke Dwargon v5, a dry dragon-city placement, one river outlet and Fulbrosia's climate. Templates, generated scripts, map raster and packwiz metadata must be regenerated together. Validate this regenerated pack before deployment. Check old corners for duplicate structures and player edits before placing new versions. The report lists the coordinates for `/ttlmap`, the dimensions for the 98% template check, remaining jigsaw/command-result issues and the structure assets whose redistribution permission needs confirmation.

## Codex PRs integrated on branch `codex-integ` (#7 skins, #6 five landmarks, #9 Wayfarer's Rest, #8 world audit)

Offline: validate passes, 49 unit tests OK, all structures rebuilt. In game after it lands on main:
- `python tools/verify_build.py <name> --log --min 98` for the new builds el_dorado, frost_palace, sacred_mountain,
  ballachia, heaven_tower; the re-placed blumund, englassia, laura, marris, treyni_shrine (v3), clayman_castle,
  dragons_nest, forgotten_dragon_city, lubelius, sealed_cave, spirit_gate (v2), dwargon (v5), mortal_spawn (v2,
  `--dimension ttl:mortal_realm`), spirit_dwelling (v2, `--dimension ttl:spirit_domain`).
- Tests: mortal_spawn, rebirth, guide, two_lives (arrival 0.5 y 5.5 unchanged), builds, landmarks, cast and
  guild_npcs (npcs.toml rev 2 respawns every NPC with its PNG skin; receptionist is now humanoid_slim, Frey and
  Ramiris humanoid), spirit_domain, arrival.
- Look: the RESOURCE_LOCATION skins actually render (unverified), Kaijin's 0.8 scale is not set (Easy NPC scale
  tags unverified), non-op players cannot break Wayfarer's Rest but can use doors, beds and the bell.
- canon_map.txt is not regenerated for the audit's Ameld outlet (needs the political plate,
  `python tools/canon_map.py <plate.png>`); the H palette change and the outlet only reach ungenerated chunks.

## Eleven landmarks, world events, Discord, and story acts V–VII

- On staging, wait for the survey queue. Run `world_landmarks.rcon` and `python tools/verify_build.py <name> --log --min 98` on elmine, nasca, jia, amrita, siltrosso, ulgr_nature_park, great_holy_mountain, coleus, morgdahl, nostraille and raja. Walk each approach from the wild and check the transition to its skirt.
- Run `events_pack.rcon`, then observe a natural Enhanced Celestials Blood Moon, regional storm drops and roaming Charybdis. Check a storm ending across a restart with a non-default EP multiplier.
- Run the muted ops, nations, bosses, story and legendary scenarios. With real linked accounts on staging, check nation role colour and cleanup, one-line story delivery and staff command redaction.
- Run `quests.rcon` and play acts V–VII in the FTB book on both oaths. Check claim context, party credit, castle visit radius, native True Hero and True Demon Lord recognition and each finale. Check the Walpurgis visit and castle encounter separately, including a player without a Legendary or capstone title. In an FTB party with one awakened member, confirm that the others can earn their titles later via `/ttl story capstone`. Wiki publishing is a separate owner action.
## Tempest growth, Mortal Realm destinations, balance and heraldry

- The town and city are additive structure sets with no runtime registration. See [the growth plan](../design/lore/tempest_growth.md) for the world anchor, slab order, preserved core and full comparison. Stage-test the phase switch when it lands, including a previously inhabited village with containers, quest NPCs and the Outcast contact.
- Wait for all six Mortal surveys, run `tools/server.sh test mortal_waypoints`, then `python tools/verify_build.py <name> --dimension ttl:mortal_realm --log --min 98`. Check the actual terrain joins, ferry water containment, tower climb and market workstations at night. The coordinates listed in the quest notes are survey centres.
- The [balance audit](audits/balance-2026-11.md) is for Yasuke to review before any tuning. For heraldry, try each banner command as a staging player and retrieve a marker from the BlueMap webroot. The map generator still needs a separate integration.

## 21/11 — vertex-budget diagnostic, source retained (ChatGPT, round44)

Read-only study in world/vertex-budget-study.md/json counts9 outlines above preferred120 but within mandatory400. Independent DP simplification would require the tested32-block tolerance to reduce mainland388 to120 (Hausdorff31.951;320719 square blocks change), so no candidate adopted. Exact current-mask union has53.045 square blocks of land gaps,0.712 outside land,and J/S7.730,S/O40.668,S/H2.280 overlaps; these areas are not raster/runtime failure counts. Future shared-edge/curve approaches remain untested. Viewed unchanged checker preview beside cached official map; no source/preview/export/art/ledger edits or converter rerun. Corrected historical/current summary labels and painting refresh pointer. Full source/geography/fixed-rule/era/fit/runtime obligations remain. No merge/apply/deploy.

Round44 repository gate: validation and 472 tests pass, 26 skipped, zero failures (45.027s test tier); no changed JS.

## 21/11 — direct WN treant evidence (ChatGPT, round45)

Directly read author WN chapter42 (URL episode44; HTML L279,L299,L309-L312): guarded treants cannot move themselves and have limited outside contact. WN42-001 supports a distinct community, not a surveyed parcel/capital/tree plan. Post-Orc WN meeting/alliance timing does not replace anime S1E10. Ledger218 (160+58),14 direct LN; inventory129/32 follow-ups unchanged. Current publisher LN20/21 trial links identified; browser attempt produced no readable pages/status/title and its own hanging helper/descendants were stopped. Long Wall chapter locators remain secondary. Same routes need changed access evidence before another attempt. Source7d021766/58 sites/previews/terrain/art unchanged; no converter/runtime action. Previous round44 produced diagnostic evidence; full goal remains active.

Round45 repository gate: validation and 472 tests pass, 26 skipped, zero failures (44.579s test tier). Ledger uniqueness, all 58 prior coordinate rows, unchanged inventory classifications and retained source/presentation bytes were verified; research files mirrored to the local research checkout.

## 21/11 — early Tempest landscape/capacity study (ChatGPT, round46)

Native SVG/PNG study in world/tempest-early-landscape.md compares current r148 future reservation with inert r85 initial surface. Existing91×91 core, arrival45,57 and margin8 require84.5725 to enclose padded cell-edge corners;85 is an engineering proposal, not canon. Current requirements include192 future growth, so merely shrinking SVG radius fails/gets raised again. C18 technical handoff: separate initial surface from future capacity, preserve future city envelope, test inhabited-era transitions; no tools/generated/site rules edited. WN20-001/002 directly verify cave/water/open-ground setting and survey/planning context without compass bearings or completed-sewer certification. Legacy place guide now qualifies its lake/pond bearings and links current snapshot. Ledger221 (163+58),14 direct LN;129 inventory/32 follow-ups,58 art pairs and source7d021766 unchanged. No SVG/preview/export/runtime mutation, converter rerun, main merge or deployment. Previous round45 made primary-source progress.

Round46 gate: fresh checker 0 errors/all 56 relations/same2 warnings; preview byte-identical. Validation and472 tests pass,26 skipped,zero failures (44.674s). Native study SVG/PNG inspected; all prior218 ledger rows/58 coordinate rows retained, current221 unique, source/atlas/terrain preview/protected paths unchanged.

## 21/11 — licensed manga cave-setting review (ChatGPT, round47)

Public Comic DAYS chapter1 normal unauthenticated viewer rendered selected story panels; reader positions9/11/13 support natural pointed formations,plants and underground water. MNG01-001/002 record narrow visual claims,not printed page numbers,full chapter reading or surveyed geometry. Later blank rapid-navigation captures are not evidence. Chapter2 remains login/ticket/145-point gated; no story read/login/purchase. Official ep2 OFF-CAV-047 confirms absorption/cave exit,not destroyed skill or physical chains. Corrected spent-seal wording and original-decoration qualifications in lore/place briefs; era overlay cave row strengthened without moving any site. Ledger224 (166+58),14 direct LN;129 inventory/32 follow-ups,58 art pairs and source7d021766 unchanged. Dry cave plate retained; no converter,blueprint/runtime correction,main merge,apply or deploy. Previous round46 delivered a concrete landscape study.

Round47 gate: validation and472 tests pass,26 skipped,zero failures (44.606s). All prior221 ledger rows and 58 coordinate rows retained; inventory129 classifications unchanged; only sealed_cave era row revised. Source/preview/atlas/terrain/art,blueprints and protected paths unchanged. Dossier files mirrored locally; no full manga/source/goal completion claimed.

## 21/11 — coupled geography required for curve simplification (ChatGPT, round48)

Read-only external cubic prototype reduces all9 over-budget outlines; mainland113 segments/114 nodes,dense measured deviation11.770,native16-step deviation11.868. Candidate5af7c175 fails3 mandatory checks: western/Laura river mouths and45 uncovered land samples,all 56 site relations pass. Exact native gaps60217.923/outside48383.279 square blocks; not affected runtime-column counts. Do not adopt. world/curve-simplification-review.md/json/svg/png records rejection; actual failing candidate stays outside repo. Shared coast/region arcs plus river-mouth anchors must be fitted jointly next. Independent old-mask grid snapping0.01..2 never yields valid coverage. No production/source/preview/export/art/registry/protected-path changes; source7d021766,224 ledger/14 direct LN,129 inventory/32 follow-ups,58 art pairs retained. No main merge/apply/chunks/deploy. PR74 discussion has only bot draft notice,no new owner decision. Limited local filename search found no matching ebook; not a full-storage search,unverified video not used. Previous round47 made primary-source progress; no blocker streak.

Round48 retained-branch repository gate: validation and472 tests pass,26 skipped,zero failures (44.833s). This gate applies to source7d021766 plus diagnostic docs; the external candidate still fails3 map checks. Production source/presentation/protected paths and224-record ledger are unchanged.

## 21/11 — shared curves adopted with exact sampled coverage (ChatGPT, round49)

Sourcecb07cce7 replaces source7d021766 using57 common arcs; coast120 nodes,woodland97,all9 upper overruns closed (eight simple outlines still below preferred20). Actual native16-step masks form valid exact coverage with zero land gaps/outside/overlapping interiors. Protected5 mouths,near-collinear coastal junctions and site contacts; Siltrosso full66-disc retained. All58 site tuples/21 route geometry/prior waters/relief/biomes/other11 forests/island coasts unchanged. Default production checker0errors/56relations/same2warnings; normal build65.6s,no converter warnings,58 anchors. Site/road/exclusion rasters and34-entry sites.json identical.55 site discs heights match; Filtwood0.0625,Sainte0.25,oneAmrita cell0.0625 change.13 road profiles match,8 max0.32; grade0.5. Water12 cells change (7 levels/5 newly wet); derived height899865 cells,max11.5,median0.1875; no false all-terrain-identical claim. Same raster box; atlas only embedded image changes,all 58 number groups/16 labels/32 rows retained,full15 text boxes andUcallout endpoint insideupdatedmasks. Source/terrain/atlas audits in world/shared-curve-review.md/json. Ledger225 (167+58),14 direct LN;129 inventory/32 follow-ups,58 art pairs. R43 painting now historical: NEXT refresh native painted masks/source registration fromcb07cce7 without treating old pixels as new canonical geometry. No technical rule edits,apply,chunks,main merge or deployment. Previous round48 produced actionable rejection evidence; full goal remains active.

Round49 gate: validation and472 tests pass,26 skipped,zero failures (62.509s). All58 exported anchor positions/ground y and anchors.toml bytes match. Site/road/exclusion rasters and sites.json are identical; other terrain deltas remain disclosed. Native atlas visually inspected; next is current-source painted mask refresh.
