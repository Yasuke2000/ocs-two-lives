# Handoff — current state of the work (update this when you stop)

## 18/11 night — PRs #18–#33 merged into main, staging at 62/67 then fixes pushed (merge-and-test run, Claude)

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
**Test results**: ttl-ops on `d1e0c09` = 66/67 (only sidequests: the ambient loop spawned an adventurer during the count; fixed with `ttl adventurers hold`; the run of 8a151d4 still failed it on the escort (a client whose chunk unloaded read as fallen) and on clearing an unloaded green, both fixed in the next commit). Before that: ttl-ops on `a78843b` = 62/67 (artifice, bosses, necro_legion, necro_ranks, sidequests failing); after the
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
