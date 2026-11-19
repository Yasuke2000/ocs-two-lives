# Project status — OCS Tensura: Two Lives

Living page for contributors: how we work, what we measure, the feel we aim for, and what is actually built.
**Update it whenever something lands on `main`** (agents: as part of every merge). Owner: **Yasuke**.
Last update: 19/11/2026 (after PR #35, the overworld reset and the re-verification of every build).

## Where we are

**Phase: before launch.** All core systems plus World State wave A (W1–W3), side content and the first player paths
(Necromancer, Artificer, moral choices) are on `main`. Staging: see the In-game row below. Next: the remaining World
State waves (`design/architecture/world-state.md`), then a **playtest with ~5 real players** (Life 1 → Life 2 end to end).
Launch only after the playtests, after the "Before launch" checklist in `docs/server.md`.

## Metrics (source: `origin/main`, 19/11/2026)

| Metric | Value | How to measure |
| --- | --- | --- |
| In-game bot tests | 70 test files: **70/70** on the reset world (19/11 05:07, by hand after the `guild_npcs` fix); ttl-ops `785036f` 69/70 (`bosses` flaked, green since) | `bash tools/server.sh test-all` (Git Bash: `MSYS2_ARG_CONV_EXCL=/data`) |
| Offline unit tests | 157 green | `python -m unittest discover -s tests` |
| Validation | must say "validation passed" | `python tools/validate.py` |
| Builds verified 1:1 in the world | All 38 build manifests + Tempest, Dwargon and mortal_spawn re-verified on the reset world 19/11, all ≥ 99.9 % (28 overworld builds, Walpurgis Hall, Spirit Dwelling, test hut, the 6 Mortal Realm waypoints); terrain round the builds repaired by hand on staging (decisions.md 19/11); every overworld build in its site biome except Treyni's shrine (half in ancient forest); night pregen of the new world started 19/11 05:08, not finished | `python tools/verify_build.py <name> --log` |
| Quests | 398 in 28 chapters, one connected web | `python tools/quest_graph.py --check` |
| Canon cast | 38 NPC spots, 28 original skins | `design/data/npcs.toml`, `/ttl cast verify all` |
| Mods | 77 | `pack/mods/*.pw.toml` |
| KubeJS server scripts | 104 | `pack/kubejs/server_scripts/ttl/` |
| Data files (TOML → generated JS) | 25 | `design/data/*.toml` → `tools/gen_data.py` |
| Logged decisions | 222 | `design/decisions.md` |

## Vibes (design pillars)

- **Two lives, both count.** Life 1 is a grounded, hardcore, mortal medieval world with **no Tensura** in it. Death
  sends your soul through the Spirit Corridor (Last Wish, Trial) into Life 2, shaped by how you lived (karma).
- **Lore-accurate first.** The Tensura world is the canon continent (14,000 blocks, regions, rivers, the Canaat
  mountains) with canon places and characters. Research references for everything; mark "our interpretation" where
  canon is silent. Use what Tensura and the other mods already have before building our own.
- **The world bites.** Jura's core around Tempest is soaked in Veldora's magicule and deadly for weak souls; you
  arrive on the safe rim and earn your way in.
- **Canon voice.** The Voice of the World / Great Sage speak in "Notice." / "Report." style; characters sound like
  themselves.
- **A small MMO that stays fair.** Personal and party story progress never gets locked by others; the world evolves
  for everyone (World Chronicle); light and dark players affect each other through events, arenas and declared wars,
  not by griefing questlines. Outside the canon continent, the mods work as they normally do (free roam).
- **Nothing silently breaks.** Every system has bot tests; every build is verified block by block after placement.

## How we work

- **Branches and PRs.** Nothing reaches `main` without Yasuke's approval (CODEOWNERS + `validate` check). Every
  task works on its own branch or git worktree and opens a PR.
- **Who does what.** Design and architecture: Claude Fable (`design/architecture/*.md`). Implementation, merges,
  test-fixing: Claude Opus/Sonnet agents. Parallel tasks: ChatGPT/Codex on `codex/*` branches (PRs reviewed by
  Claude before merging). Rules for every agent: `AGENTS.md` + `CLAUDE.md`.
- **Data-driven.** Tunable values live in `design/data/*.toml` and are validated by `tools/gen_data.py`; generated
  files are never hand-edited (`gen_data`, `gen_quests`, `gen_npcs`, `build_structures`, `packwiz refresh`).
- **Deploys.** Pushing `main` → **ttl-ops** auto-deploys to staging **only when no human is online**, then runs the
  full in-game test suite and posts the result to Discord `#server-log`. Never force-deploy with players online.
- **Decisions and handoff.** Every real decision gets a row in `design/decisions.md`. `docs/HANDOFF.md` says what is
  in progress and what is next, so anyone (human or agent) can pick up the work.
- **Player communication.** Changes for players go to Discord `#patch-notes` (`docs/patch-notes/<date>.md`,
  posted with `tools/post_patch_notes.sh`). Refer to the owner as Yasuke.
- **Ops.** Server on the homelab K3s cluster (node3, namespace `ocs-two-lives`), manifests in the Homelab repo
  (ArgoCD). Night pregeneration of the continent by ttl-ops (23:00–07:00, only when nobody is online). Backups:
  Longhorn to the NAS.

## What is built

**Life 1 (Mortal Realm)**
- Wayfarer's Rest spawn (39×39, protected against griefing and explosions), safe arrival areas.
- Karma that counts active play (anti-farming), Life 1 deaths judged into tiers (Wanderer → Legend, Fallen).
- 119 Life 1 quests in 10 chapters ending in "A Life That Counted"; the Mortal Nether/End and the Mortal Dragon.
- Life 1 items do not carry over (ender chest and Curios emptied); soulbound items + the Soul Gem do.
- Tensura content banned in Life 1 (`design/data/mortal_banned.toml`, one line per mod).

**Corridor and rebirth**
- Spirit Corridor with the Voice of the World, Last Wish, 10 trial arenas, Great Sage reincarnation scene.
- Unique registry (by UUID): caps per rarity, max 10 Legendary holders (the Ten Great Demon Lords), history.

**The Tensura world**
- Canon continent worldgen (mod `ttl-portals`), region titles, the Jura rings (safe rim, dark middle, deadly core).
- Builds (all verified): Tempest, Dwargon, Sealed Cave, Spirit Gate + the Dwelling of the Spirits (own dimension),
  Treyni's shrine, Dragon's Nest, Blumund, Marris, Ballachia, Englassia, Lubelius, Sacred Mountain, Clayman's
  Castle, City of the Forgotten Dragon, Laura, El Dorado, Frost Palace, Heaven Tower, the 11 canon landmarks (Elmine,
  Nasca, Jia, Amrita, Siltrosso, Ulgr Nature Park, Great Holy Mountain, Coleus, Morgdahl, Nostraille, Raja), the Walpurgis
  Hall and the Dwarven Arena; 7 Tensura landmarks.
- Generic build placer (`design/builds/*.toml`): surveys the canon spot, fits terrain, re-places on version bump.

**Story, quests, characters**
- The Oath (light or dark, party-level), 7 acts, one path flip per life; story chapters 7–13 with equal light and
  dark lanes (Crossroads, The King's Test, the Orc War, Charybdis, Mask and Blade, Walpurgis, the Harvest Festival);
  side chapters 20–23 (47 side jobs: escort, delivery, travel, fetch, cull); 398 quests total in one connected web.
- Side content: ambient adventurers in the towns, hireable Easy NPC companions.
- Player paths (`/ttl paths`): the two roads (slow good, fast dark, Life 2 karma ledger), the Necromancer (Bone Altar,
  legion, Death Knights, player-built tombs, four ranks, the Church's Sense and the exorcist licence), the Artificer
  (Workshop Bench, charter, maker's stamp, commissions, four ranks), moral-choice scenes (4 events).
- Canon cast: mod entities as statues where they exist (Gazel, Shizu, Hinata, Folgen, Luminous, Carrion…), Easy
  NPCs with original skins for the rest (Benimaru, Shuna, Shion, Kaijin, Milim, Fuze…), story talk on right-click.

**Bosses and combat**
- Boss framework: 20+ canon bosses with fixed lairs, gates and rare wild sightings; per-party cooldowns, an arena
  queue, echoes of fallen bosses, wild and story fights apart (WP-W2).
- Arenas: the Walpurgis Hall in its own dimension (10 thrones, the council NPCs) and Ramiris's Labyrinth.
- Legendary absorption: duel, war, bequest, awakening; duel damage liability in public places.

**Social and economy**
- Parties (FTB Teams, max 5, shared quests and boss credit), nations (charter, Life 2 claims, value and ranks,
  alliances, wars, upkeep debuffs), reputation with 8 factions + renown.
- Economy: Tensura coins via Lightman's Currency, player shops, the magical Mana Ledger bank, the Adventurer's Guild
  (receptionists F–C, Fuze B–S).

**Ops and community**
- ttl-ops CD + tests, Discord bot (account linking, roles incl. nation roles, Hall of Souls, leaderboard,
  `#patch-notes`, `#roadmap`, `#suggestions`, staff command audit), BlueMap (public map; DNS + tunnel route pending),
  world events director (World's Favor, Magicule Storm, Blood Moon, Calamity Rising).
- World Chronicle (WP-W1: the world's counts, milestones, balance and tide), the continent line (outside it the mods
  run as shipped), protected canon domains with respawning residents and the Eurazania faction (WP-W3).
- 11 canon landmarks (Elmine … Raja); Tempest growth rings and 6 Mortal Realm waypoints drawn (not placed yet).

## In progress

- World State: W4 (PvP only in quests, arenas and wars) and waves B–D (Tempest growth phases, catch-up, raid groups,
  radiant quests, the immersive Orc Lord, usurping/vassalising canon nations).
- Paths: Artificer constructs (WP-A2), moral choices 4.5–4.12 (WP-C2), Priest/Exorcist next.
- Not yet verified in game: the Mortal Realm waypoints (`test mortal_waypoints`), real-player Discord role and
  staff-audit behaviour.

## Open decisions and known issues

- BlueMap public URL needs a Cloudflare DNS record + tunnel route (Yasuke).
- Owner question: does `tensura:boss_area` count as inside the continent? Today (W1 default) it does not, so the
  mod's bosses spawn there as shipped.
- Untested with real players: skins rendering, duels/wars between players, shops and wallets, the Labyrinth hall.
- Before launch: run the reset checklist in `docs/server.md` (era, test registry holders, test story/party/nation records).

## Where to find things

`AGENTS.md` (rules for any agent) · `CLAUDE.md` (project rules, pinned versions, data schema) · `docs/HANDOFF.md`
(current work) · `design/master-plan.md` · `design/decisions.md` · `design/architecture/` · `design/quests.md` ·
`design/lore/` · `docs/server.md` (operations) · `docs/discord-guides.md` · `docs/patch-notes/`.
