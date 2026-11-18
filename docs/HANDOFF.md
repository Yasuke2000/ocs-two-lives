# Handoff — current state of the work (update this when you stop)

Last update: 18/11/2026 ~07:35 (Brussels), by Claude (night run for Yasuke, who wants a stable pack + a
report at 08:30).

## Live / merged on main tonight

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

## In progress / next steps (in order)

1. **Tests green after deploy of `263db25`** (LuckPerms removed). Fixed on main (pushed to staging with
   `push-scripts`, ~05:50): swallowed `event.cancel()`, `runCommandSilent` has no result (`TtlCmd.run`), economy
   balance (Lightman's holder does not see inventory coins), Favor ids, test argument/setup mistakes; see the
   decisions.md rows of 18/11/2026 at the end. **Still failing until step 2**: every Life 2 bot dies of magicule
   poison 1 s after rebirth, because the arrival (259 63 -608) stands in `tensura:ancient_forest` chunks generated
   before the ring worldgen (`/ttlmap` says rim, the stored chunk biome says ancient_forest). That breaks arrival
   and, depending on timing, carryover, guide, soul, spirit_domain (all pass with the bots sheltered).
   After a restart the scripts' `ServerEvents.loaded` loops (spirit domain gate) run the new code; a `/reload` keeps
   the old loop running.
2. **Overworld reset: done 06:10.** Tempest, Dwargon, the 7 landmarks and all 13 canon builds are placed on
   staging (`/ttl build list`, `/ttl landmark list`).
3. **Builds verified 1:1: done ~07:30** (all on staging, scripts pushed with `push-scripts`, commits local on main).
   Every build ≥ 99.93 %: tempest 99.96, dwargon 99.98, mortal_spawn 100, spirit_dwelling 100, test_hut 100,
   blumund/clayman_castle/englassia/laura/treyni_shrine/forgotten_dragon_city/sealed_cave/dragons_nest/marris 100.00,
   lubelius 99.99, spirit_gate 100 (verify_build now counts left-out properties as defaults; Lubelius' 97.16 % was
   only `quartz_pillar` vs `[axis=y]`). Fixes: survey takes water as a cost (`max_wet`), wet columns filled from the
   bed, two slab passes (wheat/doors/beds no longer pop), stale 10,000-width x/z of Clayman and the Forgotten Dragon
   City corrected, blueprint fixes (town-lib bed facing, Laura hut ladders, Englassia planters, fountain lantern,
   Treyni bluets/lantern), Tempest's south-east rim no longer sits on a lake (tempest.js fills from the bed; the live
   world got a one-off `fill ... replace water`, 4,480 blocks). Floating check: no build floats (Sealed Cave has one
   enclosed natural cave pocket under its north edge, 5 blocks below the walking level).
   Left: tiny game-made leftovers (Tempest crops/lanterns from its single-pass placer, Dwargon 147 `air -> water` at
   y 156 near 430 -1069 and 18 lanterns, Lubelius 5 path -> dirt, a lone Marris bed head, Dragon's Nest snow layers);
   the Forgotten Dragon City stands 299 blocks north of its landmark because the real terrain there is lakes.
4. **Pregenerate the continent** with Distant Horizons (Chunky is banned): `dh pregen start minecraft:overworld
   -2088 -616 <chunkRadius>` (continent ≈ 14,000 × 10,000 blocks), status with `dh pregen status`; then BlueMap
   renders (`bluemap` commands; web port 8100 needs a k8s Service + tunnel route — snippet in docs/server.md).
5. **Story, characters and parties** — design: `design/architecture/story-characters.md` (Fable), then its work
   packages: canon character roster (Tensura entities first, Easy NPC + online skins for the rest), overarching
   questline with good/evil branches, FTB Teams parties, per-boss fixed spawn + condition + rare wild spawn.
6. Wave B of sprint3-4.md: WP4 nations (cap 5 members, claims Life 2 only), WP6 Legendary absorption
   (routes: duel, war, bequest, awakening), WP8 event pack, WP10 boss payouts, WP11 Discord story/roles.

## Open owner questions

- Gluttony: Common (now) or Legendary? · El Dorado / Frost Palace need explicit x/z (landmarks are at sea).
- `fuze_turnin_at_desk` (false: Fuze contracts handed in to Fuze only) · BlueMap public or behind access control.
