# Handoff — current state of the work (update this when you stop)

Last update: 18/11/2026 ~14:10 (Brussels), by Claude (day run for Yasuke: codex-integ merged, test fixes recovered,
tests kept out of Discord, **`bash tools/server.sh test-all` = 0 failing on main `061a1a2`**).

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

## Canon landmarks, WP8 and WP11 awaiting staging

Eleven surveyed landmarks have placements and sourced previews. After the overworld placement queue drains, run `world_landmarks.rcon`, then `python tools/verify_build.py <name> --log --min 98` for each name in that file. Walk the approaches and check night lighting and terrain joins. The Ulgr trail interprets the mapped park; the existing spirit-domain travel route stays in Jura.

Run `events_pack.rcon`, `ops.rcon`, `story.rcon`, `nations.rcon`, `bosses.rcon` and `legendary.rcon` through the muted runner. Observe a naturally forecast EC2 Blood Moon, storm loot and damage across a region boundary, restoration of the server-wide EP multiplier, and Charybdis roaming from its announced start. With linked, consenting real players after tests, verify staff delivery and redaction, six distinct story transitions, nation role colour and permissions, and removal after leaving or dissolution. A real Discord guild and live server are required for these checks.
