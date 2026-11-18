# Roadmap status

Plan: owner's plan file "pure-hugging-finch" (Sprints 1–4). Tick items here as they land; details in
`decisions.md`.

## Sprint 1 — friend playtest
- [x] Deploy refuses while players are online; `server.sh test-all` (17 bot tests, all green)
- [x] Quiet script commands (`/quietly`), shipped EC2 + Distant Horizons configs, ZGC in the Prism zip
- [x] Corridor choices on screen (`/ttlmenu`), `/ttl menu`, Knowledge questions as a menu
- [x] Reset no longer rerolls skills; Life 1 starts as Human without Tensura's race menu
- [x] Voice of the World through the Great Sage addon (`/greatsage worldvoice`, recorded clips) at every Corridor step
- [x] Great Sage reincarnation scene as the Life 2 rebirth (ttl-portals opens Tensura's menu with the
      player's offers; no race menu in Life 1)
- [x] The scene's own wishes (up to 3 skills, `ReincarnationGrants.apply`) stay on top of the Last Wish; the registry
      reconcile records them or swaps an over-cap one for a free unique of the same rarity
- [x] Karma v1 + tiers → race offers, unique choice and odds, Legend bonus (`server_scripts/ttl/karma/`, `design/data/karma.toml`, `/ttl life`)
- [x] Skill registry v1: rarities + caps in `design/data/skills.toml` (Legendary 3, Rare 3, Common 5),
      duplicates allowed, Legendary never drawn at rebirth, `/ttl grant`, `/ttl registry`
- [x] Legendaries removed from Tensura's reincarnation pools and Great Sage's wish pool (configs)
- [x] Registry reconcile from ManasCore storage (`SkillAPI.getSkillsFrom(p).getLearnedSkills()`, mastery ≥ 0)
      (`manas.js`, `/ttl reconcile`)
- [ ] Veto hooks on `SkillEvents.UNLOCK_SKILL`, `TensuraSkillEvents.SKILL_PLUNDER` in ttl-portals (instant instead of
      within 5 min; design/manas-integration.md §5)
- [x] Revoke one skill at a time (`revoke <p> all` also wipes intrinsics/resistances)
- [x] `/bug <text>` with full player/server state; saved on the server, GitHub issue once the token exists
- [x] Discord alerts (crash, server down/up, deploy, tests) and TPS alerts from ttl-ops
- [x] Backups: Longhorn snapshot every night + NAS backup every day, newest checked by ttl-ops (`docs/server.md`)
- [ ] Off-site copy (restic CronJob) and a tested restore drill — needs a backup target
- [ ] Pregenerate the worlds with Chunky (back in the pack; DH + Chunky re-test on the existing world first): Mortal Realm square r=2000, then the canon continent rectangle
- [x] Voice of the World NPC in the hall: a glowing allay (not Easy NPC: a vanilla entity kept by `life/voice_npc.js`,
      right-click handled in ttl-portals `guide/VoiceNpc.java` → `/ttl talk`: the current Corridor step, else the guide)
- [x] Guide pop-up for new players in the Great Sage style (ttl-portals `guide/`, text in `design/data/guide.toml`):
      `/ttl guide`, once on the first join, on the first arrival in the Corridor and at the start of Life 2
- [x] Trial knobs in `design/data/trials.toml` (limits, gear, waves, questions, radii, counts)
- [ ] Singleplayer check (owner, needs a client)
- [x] Privacy: guide page "Privacy: what we keep", `docs/server.md` "Data we keep", 180-day purge snippet for `ttl-reports/` and CervLogger
- [ ] Schedule the 180-day purge in ttl-ops, and check `cl purge` over RCON once (until then the guide's "180 days" is not enforced)
- [x] PvP in Life 1 stays open: one line in the guide and a row in `docs/server.md`; a post in Discord `#welcome` is still to do
- [x] Boss capture gated: `design/data/bosses.toml` `[tombstone]` (default: only a player who has slain the boss), `compat/tombstone_bosses.js`
- [x] `master-plan.md` synced with what was decided and built (status table + notes); PR approval rule fixed in `decisions.md`

## Collaboration (coworkers can see and change everything)
- [x] All server mod configs in `pack/config/` (283 files, client-only excluded) + `docs/configs.md` index
- [x] ManasCore/Tensura/addon integration guide (`design/manas-integration.md`)
- [x] Local mod build + release (`mod/gradlew`, `tools/release_mod.py`), no Actions for mod builds
- [x] Auto-deploy + tests from `main` on the homelab (`ttl-ops`, only while nobody is online), GitHub commit status "ttl staging"
- [x] `CONTRIBUTING.md`, issue/PR templates, labels, `docs/server.md`
- [x] Branch protection on `main` (PR + validate required, owner bypass)
- [ ] Collaborators: Lancelot Boden (already added); others' GitHub + Minecraft names
- [x] Discord: Simple Discord Link bot, account linking instead of the whitelist, roles, Hall of Souls, leaderboard (`docs/server.md`)

## Sprint 2 — building and visuals
- [x] `blueprints/` DSL (`tools/blueprint.py`) → `tools/build_structures.py` → structure .nbt + isometric/top previews (`docs/previews/`), stdlib only; `/ttl build <name>`
- [x] Capture any world region back into a blueprint without a player: `/ttlcapture` (mod 0.7.0) + `tools/capture.py`; place anywhere with `server.sh place` (proven: place → capture → 3605/3605 identical)
- [x] WorldEdit round trip: WorldEdit 7.3.8 in the pack, `//schem save` → `tools/import_schem.py` → `blueprints/<name>.schem` → structure + previews (Sponge v2/v3 reader, stdlib)
- [ ] `tools/pixelize.py` (AI concept → 16×16 / 64×64), review gallery
- [ ] Custom screens/title screen in the Great Sage visual style (first one done: the guide, `guide/client/GuideScreen.java`)
- [x] Corridor hall v2 as a blueprint (`blueprints/spirit_corridor_hall.py`)
- [x] Real builds: the ten Trial arenas (`blueprints/trial_*.py`, shared `_arena.py`, `ARENA_VERSION` 2) and
      Wayfarer's Rest, the Mortal Realm spawn (`blueprints/mortal_spawn.py`, `life/mortal_spawn.js`, `/ttl spawn`)
- [x] Build gallery `docs/previews/README.md`, generated with the previews

- [x] Canon Tensura continent worldgen (`ttl:canon_map`), Mortal Realm free of Tensura worldgen, Dwargon
- [ ] Pregeneration of both worlds on the owner's PC (same seed and pack, Chunky), upload region files

## Sprint 3 — content
- [x] Quest generator (TOML → FTB Quests) + chapters 0 "A Mortal Life" and 1 "Reborn" (`design/quests/`, `tools/gen_quests.py`)
- [x] Life 1 finale: the Mortal Dragon in the Mortal End (own dragon fight, `ttl-portals`)
- [ ] Mortal Realm filters (`ttl:mortal_banned`, data-driven)
- [ ] Iron Tyrant mid-boss: postponed, decide whether it comes at all
- [x] Lore region v1: Early Tempest at the Life 2 spawn, Dwargon, six canon landmarks (Tensura's own structures); onboarding: guide pop-up and the Voice NPC
- [ ] Soul carryover: ender chest and Curios cleared at Life 1 death, Soul Gem, Remembered Enchantment (`design/architecture/sprint3-4.md` S1)
- [ ] Quests: chapter 0 to 60 quests, chapters 2-4 (Tempest rises, Dwargon, the Orc Lord), dailies and weeklies; rewards touch karma, titles and reputation, never uniques
- [ ] Legendary tier pick (a Legendary unique through `registry.js`, plan section 3); Western Nations builds (Blumund, Falmuth, Englassia), canon NPCs, the atlas item

## Sprint 4 — politics, bosses, economy
- [ ] Factions/reputation, nations, absorption, boss framework, economy, event director, BlueMap

## Blind spots from the master-plan gap analysis (open unless ticked)
Found 18/11/2026 by reading `master-plan.md` against the repo; each fix gets a bot test in `tests/ingame/`.
- [ ] Life 1 items reach Life 2: the ender chest and Curios/backpack slots are not emptied at the Life 1 death (`life/death.js` only clears the inventory); keep `ttl:soulbound` as the carry-over tag
- [ ] Mortal Realm item filter: data-driven (`design/data/mortal_banned.toml`: namespaces, items, tags), Tensura content banned in the Mortal dimensions; a bot test that a Tensura item is refused
- [x] PvP in Life 1 stays open and is documented (guide, `docs/server.md`); `#welcome` still to do
- [ ] Karma anti-farming: active time instead of idle time, diminishing kill counts, exploration on foot with a daily cap (numbers in `karma.toml`; verify in game)
- [ ] Registry keyed by name: key it by UUID with a name cache and migrate the records (`registry.js`, `manas.js`)
- [ ] Unique pool hygiene: return to pool after 30 days inactive, Tensura reset-counter bonus uniques recorded and capped, transfer history and Voice announcements (plan section 5)
- [x] Bosses tamable through Tombstone: gated by `bosses.toml` (see Sprint 1)
- [x] Privacy: stored data documented, purge snippet written; scheduling it is open (see Sprint 1)
- [x] Docs drift: `master-plan.md` status notes, PR approval rule (`decisions.md` 18/11/2026)
- [ ] Ops: off-site backup and a restore drill, a load test (MSPT under 40 with 10 players; view distance 16 against the plan's 8–10), a 5-tester playtest of Life 1 → Life 2 (the plan's Phase 1 exit), the player-count target (plan Q2)
- [ ] Docs: `docs/server.md` still lists the whitelist as the way in; joining is through Discord linking since 18/11/2026

## Already provided by mods (don't rebuild)
- Great Sage addon: Voice of the World overlay + 246 clips, skill announcements with name clips,
  reincarnation ceremony (wishes as drawn sigils, race carousel, unique reveal), Sage menu/console
  (skill tree, archive, analysis), tips, naming/awakening/evolution cinematics, Harvest Festival and
  True Hero/Demon Lord world announcements.
- Tensura: races, skills, EP, naming, evolution, Labyrinth, Hell, `trulyUnique`.
