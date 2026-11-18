# Handoff — current state of the work (update this when you stop)

Last update: 18/11/2026 ~13:30 (Brussels), by Claude (day run for Yasuke: codex-integ merged, test fixes recovered,
tests kept out of Discord).

## Today (18/11, day)

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
- **Not verified as a full `test-all` by me**: Tailscale SSH to the node went into *check mode* at ~11:40 ("Tailscale SSH requires an
  additional check. To authenticate, visit: https://login.tailscale.com/a/…"); nobody but Yasuke can approve that in a browser.
  Until then every `tools/server.sh` call hangs. ttl-ops (in-cluster) still deploys and tests every push: its verdict is the
  commit status "ttl staging" on GitHub and the message in Discord #server-log (`gh api repos/Yasuke2000/ocs-two-lives/commits/<sha>/status`).
  ttl-ops results today: `901bef1` 9 failing (absorb, bosses, cast, guild, guild_npcs, nations, party, story, wild), `dd85654` 9 failing
  (same code; my `/reload` landed in the middle of its absorb test), `3e7c05c` → see the status.

## Next steps (in order)

1. Yasuke: run `ssh root@100.109.28.21` once in a terminal and open the printed login.tailscale.com link (check mode); then
   `bash tools/server.sh test-all` → fix what is left (`bash tools/server.sh test <name>`; `push-scripts` for KubeJS-only edits).
   Note `guild.rcon` was in the 9 but its output was not among the morning's green runs: look at it first.
2. `python tools/verify_build.py <name> --log --min 98` for the new/re-placed builds (el_dorado, frost_palace, sacred_mountain,
   ballachia, heaven_tower, blumund, englassia, laura, marris, treyni_shrine, clayman_castle, dragons_nest,
   forgotten_dragon_city, lubelius, sealed_cave, spirit_gate, dwargon; `mortal_spawn --dimension ttl:mortal_realm`,
   `spirit_dwelling --dimension ttl:spirit_domain`) after their `[ttl] <name> placed` lines.
3. `/ttl era reset` on staging (the era is ~20 from test runs), then the Before-launch list below.
4. Pregenerate the continent with Distant Horizons; BlueMap; wave B leftovers (WP8 event pack, WP10 boss payouts, WP11 Discord roles).

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

- Gluttony: Common (now) or Legendary?.
- `fuze_turnin_at_desk` (false: Fuze contracts handed in to Fuze only) · BlueMap public or behind access control.

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
