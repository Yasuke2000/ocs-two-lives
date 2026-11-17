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
- [x] Discord alerts (crash, server down/up, deploy, tests) from ttl-ops; TPS alerts still to do
- [ ] Daily off-site backups (restic CronJob) — needs a backup target
- [ ] Chunky + DH re-test on the existing world, then pregenerate
- [ ] Voice of the World NPC in the hall (Easy NPC)
- [x] Trial knobs in `design/data/trials.toml` (limits, gear, waves, questions, radii, counts)
- [ ] Singleplayer check (owner, needs a client)

## Collaboration (coworkers can see and change everything)
- [x] All server mod configs in `pack/config/` (283 files, client-only excluded) + `docs/configs.md` index
- [x] ManasCore/Tensura/addon integration guide (`design/manas-integration.md`)
- [x] Local mod build + release (`mod/gradlew`, `tools/release_mod.py`), no Actions for mod builds
- [x] Auto-deploy + tests from `main` on the homelab (`ttl-ops`, only while nobody is online), GitHub commit status "ttl staging"
- [x] `CONTRIBUTING.md`, issue/PR templates, labels, `docs/server.md`
- [x] Branch protection on `main` (PR + validate required, owner bypass)
- [ ] Collaborators: Lancelot Boden (already added); others' GitHub + Minecraft names

## Sprint 2 — building and visuals
- [x] `blueprints/` DSL (`tools/blueprint.py`) → `tools/build_structures.py` → structure .nbt + isometric/top previews (`docs/previews/`), stdlib only; `/ttl build <name>`
- [x] Capture any world region back into a blueprint without a player: `/ttlcapture` (mod 0.7.0) + `tools/capture.py`; place anywhere with `server.sh place` (proven: place → capture → 3605/3605 identical)
- [x] WorldEdit round trip: WorldEdit 7.3.8 in the pack, `//schem save` → `tools/import_schem.py` → `blueprints/<name>.schem` → structure + previews (Sponge v2/v3 reader, stdlib)
- [ ] `tools/pixelize.py` (AI concept → 16×16 / 64×64), review gallery
- [ ] Custom screens/title screen in the Great Sage visual style
- [x] Corridor hall v2 as a blueprint (`blueprints/spirit_corridor_hall.py`)
- [x] Real builds: the ten Trial arenas (`blueprints/trial_*.py`, shared `_arena.py`, `ARENA_VERSION` 2) and
      Wayfarer's Rest, the Mortal Realm spawn (`blueprints/mortal_spawn.py`, `life/mortal_spawn.js`, `/ttl spawn`)
- [x] Build gallery `docs/previews/README.md`, generated with the previews

- [x] Canon Tensura continent worldgen (`ttl:canon_map`), Mortal Realm free of Tensura worldgen, Dwargon
- [ ] Pregeneration of both worlds on the owner's PC (same seed and pack, Chunky), upload region files

## Sprint 3 — content
- [ ] Mortal Realm filters (`ttl:mortal_banned`), Iron Tyrant boss, quest generator + chapters 0–1
- [ ] Soul carryover, lore region v1 (Jura Forest + Tempest), onboarding

## Sprint 4 — politics, bosses, economy
- [ ] Factions/reputation, nations, absorption, boss framework, economy, event director, BlueMap

## Already provided by mods (don't rebuild)
- Great Sage addon: Voice of the World overlay + 246 clips, skill announcements with name clips,
  reincarnation ceremony (wishes as drawn sigils, race carousel, unique reveal), Sage menu/console
  (skill tree, archive, analysis), tips, naming/awakening/evolution cinematics, Harvest Festival and
  True Hero/Demon Lord world announcements.
- Tensura: races, skills, EP, naming, evolution, Labyrinth, Hell, `trulyUnique`.
