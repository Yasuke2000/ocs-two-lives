# Handoff — current state of the work (update this when you stop)

Last update: 18/11/2026 ~03:50 (Brussels), by Claude (night run for Yasuke, who wants a stable pack + a
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

1. **Tests green after deploy of `263db25`** (LuckPerms removed). If `tools/server.sh test-all` is not
   "0 failing": fix scripts/tests (most failures so far came from untested agent code; see decisions.md).
2. **Overworld reset** (owner approved): `/ttl worldreset minecraft:overworld` per `docs/server.md`
   (backup is automatic) so the Jura rings apply everywhere; then wait for Tempest, Dwargon, landmarks and
   the canon builds to place (`[ttl] … placed` log lines, `/ttl build list`).
3. **Verify every build 1:1**: `python tools/verify_build.py <name> --log` (≥ 98 %) for tempest, dwargon and
   each `design/builds/*.toml`; fix and bump `version` where it fails.
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
