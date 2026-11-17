# Roadmap status

Plan: owner's plan file "pure-hugging-finch" (Sprints 1–4). Tick items here as they land; details in
`decisions.md`.

## Sprint 1 — friend playtest
- [x] Deploy refuses while players are online; `server.sh test-all` (17 bot tests, all green)
- [x] Quiet script commands (`/quietly`), shipped EC2 + Distant Horizons configs, ZGC in the Prism zip
- [x] Corridor choices on screen (`/ttlmenu`), `/ttl menu`, Knowledge questions as a menu
- [x] Reset no longer rerolls skills; Life 1 starts as Human without Tensura's race menu
- [x] Voice of the World through the Great Sage addon (`/greatsage worldvoice`, recorded clips) at every Corridor step
- [ ] Great Sage reincarnation scene as the rebirth UI (decision pending; `sageReincarnation` off until then)
- [ ] Karma v1 + tiers → race offers (`server_scripts/ttl/karma/`)
- [ ] Skill registry v1: rarities in `design/skills.yaml`, Legendary slots, 10-min reconcile
- [ ] `/ttl bug <text>` → Discord `#bugs` — needs the Discord webhook secret
- [ ] Discord alerts (crash, TPS, deploy, tests) — needs the Discord webhook secret
- [ ] Daily off-site backups (restic CronJob) — needs a backup target
- [ ] Chunky + DH re-test on the existing world, then pregenerate
- [ ] Voice of the World NPC in the hall (Easy NPC)
- [ ] Trial knobs in `design/trials.yaml`
- [ ] Singleplayer check (owner, needs a client)

## Sprint 2 — building and visuals
- [ ] `blueprints/` DSL → `tools/build_structures.py` → structure .nbt; `tools/render_structure.py` previews; `/ttl build`
- [ ] WorldEdit round trip (`tools/import_schem.py`)
- [ ] `tools/pixelize.py` (AI concept → 16×16 / 64×64), review gallery
- [ ] Custom screens/title screen in the Great Sage visual style
- [ ] Real builds: Corridor hall, Trial arenas (bump `ARENA_VERSION`), Mortal Realm spawn

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
