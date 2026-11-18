# Project status — OCS Tensura: Two Lives

Living page for contributors: how we work, what we measure, the feel we aim for, and what is actually built.
**Update it whenever something lands on `main`** (agents: as part of every merge). Owner: **Yasuke**.
Last update: 18/11/2026.

## Where we are

**Phase: end of Sprint 3–4, before launch.** All core systems are built and on `main`; staging has been green on the
full in-game suite (47/47 on 18/11 at commit `061a1a2`; the suite has grown since). Next: the World State waves
(`design/architecture/world-state.md`), then a **playtest with ~5 real players** (Life 1 → Life 2 end to end).
Launch only after the playtests, after the "Before launch" checklist in `docs/server.md`.

## Metrics (source: `origin/main`, 18/11/2026)

| Metric | Value | How to measure |
| --- | --- | --- |
| In-game bot tests | 50 test files (47/47 green on the last full run) | `bash tools/server.sh test-all` |
| Offline unit tests | 92 green | `python -m unittest discover -s tests` |
| Validation | must say "validation passed" | `python tools/validate.py` |
| Builds verified 1:1 in the world | 20 builds + 7 Tensura landmarks, all ≥ 99.9 % | `python tools/verify_build.py <name> --log` |
| Quests | 304 in 21 chapters, one connected web | `python tools/quest_graph.py --check` |
| Canon cast | 38 NPC spots, 28 original skins | `design/data/npcs.toml`, `/ttl cast verify all` |
| Mods | 77 | `pack/mods/*.pw.toml` |
| KubeJS server scripts | 80 | `pack/kubejs/server_scripts/ttl/` |
| Data files (TOML → generated JS) | 16 | `design/data/*.toml` → `tools/gen_data.py` |
| Logged decisions | 154 | `design/decisions.md` |

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
  Castle, City of the Forgotten Dragon, Laura, El Dorado, Frost Palace, Heaven Tower; 7 Tensura landmarks.
- Generic build placer (`design/builds/*.toml`): surveys the canon spot, fits terrain, re-places on version bump.

**Story, quests, characters**
- The Oath (light or dark, party-level), 7 acts, one path flip per life; story chapters 7–10 with equal light and
  dark lanes (Crossroads, The King's Test, the Orc War, Charybdis); 304 quests total in one connected web.
- Canon cast: mod entities as statues where they exist (Gazel, Shizu, Hinata, Folgen, Luminous, Carrion…), Easy
  NPCs with original skins for the rest (Benimaru, Shuna, Shion, Kaijin, Milim, Fuze…), story talk on right-click.

**Bosses and combat**
- Boss framework: 20+ canon bosses with fixed lairs, gates and rare wild sightings; Shizu and Rimuru at Tempest.
- Arenas (PR #19): the Walpurgis Hall in its own dimension (10 thrones) and Ramiris's Labyrinth (Tensura's own hall).
- Legendary absorption: duel, war, bequest, awakening; duel damage liability in public places.

**Social and economy**
- Parties (FTB Teams, max 5, shared quests and boss credit), nations (charter, Life 2 claims, value and ranks,
  alliances, wars, upkeep debuffs), reputation with 8 factions + renown.
- Economy: Tensura coins via Lightman's Currency, player shops, the magical Mana Ledger bank, the Adventurer's Guild
  (receptionists F–C, Fuze B–S).

**Ops and community**
- ttl-ops CD + tests, Discord bot (account linking, roles, Hall of Souls, leaderboard, `#patch-notes`), BlueMap
  (public map; DNS + tunnel route pending), world events director + World's Favor.

## In progress

- World State wave A (`design/architecture/world-state.md`): World Chronicle + continent boundary (WP-W1), boss
  instancing with per-party cooldowns and queues (WP-W2). Then W3 (protected canon domains, respawning NPCs),
  W4 (PvP only in quests, arenas and wars), and waves B–D (Tempest growth, catch-up, raid groups, radiant quests,
  the immersive Orc Lord, usurping/vassalising canon nations).
- Open PRs: #18 (ChatGPT: canon landmarks, world events, Discord nation roles), #19 (arenas) — being reviewed/merged.
- ChatGPT tasks: story chapters 11–13, Dutch localisation, player wiki.

## Open decisions and known issues

- BlueMap public URL needs a Cloudflare DNS record + tunnel route (Yasuke).
- Untested with real players: skins rendering, duels/wars between players, shops and wallets, the Labyrinth hall.
- Before launch: run the reset checklist in `docs/server.md` (era, test registry holders, test story/party/nation records).

## Where to find things

`AGENTS.md` (rules for any agent) · `CLAUDE.md` (project rules, pinned versions, data schema) · `docs/HANDOFF.md`
(current work) · `design/master-plan.md` · `design/decisions.md` · `design/architecture/` · `design/quests.md` ·
`design/lore/` · `docs/server.md` (operations) · `docs/discord-guides.md` · `docs/patch-notes/`.
