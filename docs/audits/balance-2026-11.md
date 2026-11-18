# Balance audit · 18 November 2026

The largest discrepancy is in the currency ledger. Five eligible contributors can earn **125 gold and five Skill Cores** on a Tier 4 kill. The boss distributes coins directly, outside the ledger used by `/ttl econ`. Five people maintaining 50 claims pay **5 gold a week**. Changing upkeep on the strength of the ledger alone would disproportionately charge builders.

This is a static review of main at `674cdbb`, with calculations from its TOMLs and KubeJS consumers. Dates below are calendar days unless marked Minecraft days. Times assume 20 TPS. Gold figures use 1 gold = 10 silver = 100 bronze and 1 stellar = 10 gold. No live player distribution, fight timing, shop volume, server TPS or treasury history was available. The ranked changes are proposals for a pilot.

## Ten decisions, in priority order

Paths in the key column are relative to [design/data](../../design/data). Rows that need consumer work say so explicitly. The final column gives a measurement that can reverse the decision.

| Priority | File and key | Current → proposed | Why and what to measure |
|---|---|---|---|
| 1 | economy.toml `sinks.altar`, `sinks.core_identify` | Configured 5s / 2g, effectively 0 / 0 on the normal summon/open paths → instrument direct payouts and test 5s per successful paid altar summon, 2g per successful identification | Requires consumer work and transaction/refund tests. Distinguish quest, arena and wild summons from paid rituals. Record all minting and destruction before raising fees. Compare weekly drain/mint to the design target of 80%. |
| 2 | arenas.toml `arena[id=walpurgis/labyrinth].challenge_cooldown_minutes` and bosses.toml `boss[id=clayman/elemental_colossus].cooldown_hours` | 30 min venue retry against shared 72h / 96h defeat locks → retain both timer sets and preflight boss availability at booking, then offer a practice finish without the global reward | Consumer change. Prevent spending three waves to discover the finale is unavailable. Measure bookings refused, practice finishes and time to first story clear per cohort. |
| 3 | bosses.toml `boss[id=elemental_colossus].rewards.coins.gold` | 25 → 15 on a one-boss pilot after accounting | Five direct awards fall from 125g to 75g, while every eligible person keeps a reward. Check gold per player-minute against T3, solo completions and parties joining after registration. |
| 4 | skills.toml `core.weights.rare` | 3 → 1, keep Common at 1 | Fresh-pool Rare falls from 83.65% to 63.04%. Record pool eligibility and outcomes per draw, and weeks to saturation at 10, 20 and 30 actives. |
| 5 | economy.toml `rank[id=B].points` | 140 → 110 | Opens Fuze about five calendar days earlier for daily players and seven for three-visit players. Track actual hours and calendar days to B, plus how many who reach it take a named contract. |
| 6 | events.toml `favor.min_hours` | 5 → 3 per week | One weekly winner is already a strong throttle. Count eligible Life 2 players excluded solely by hours and compare recipients’ EP percentile before and one week after the award. |
| 7 | skills.toml `absorb.war.min_ep_ratio` | 0 → 0.5 for a measured season | A war kill ignores the relative-EP floor used in ordinary absorption. Keep the owner’s ten-holder rule. Measure EP ratios of transfers, repeated targets and whether weaker nations can retain holders. This change protects low-EP victims and still allows underdog attackers. |
| 8 | nations.toml `value.coins_per_value` | 100 → 200 bronze per value | Treasury holdings currently buy rank as well as funding claims. The alternative halves the purchased part. Replay actual nation values before changing ranks or claim allowances. |
| 9 | arenas.toml `arena[id=walpurgis/labyrinth].loot.duel.lose.coins.silver` | 2 → 1 in both venues | Two settled duels mint 22s across a pair, falling to 20s. This modest change preserves a consolation prize. Track repeat opponents and ordinary queue participation before touching winner rewards. |
| 10 | carryover.toml `book.min_axis_score` | 150 → 135 if Hero craftspeople rarely qualify | Required raw Craft falls from about 139.3 to 114.3 before score rounding. Keep Craft strongest, Hero tier and level III ceiling. Count failures separately at each gate, including missing eligible enchantments. |

## Currency, contracts and construction

The desk draws three dailies including a guaranteed rank-F contract and two weeklies. Fuze draws two additional weeklies for B and above. The authored pools contain 15 desk dailies, eight desk weeklies and eight Fuze weeklies. Three is the simultaneous **accepted** limit. Turning jobs in frees slots. Completion pays once per character for that board period. The ladder is F 0, E 10, D 30, C 70, B 140, A 250 and S 400. Early desk dailies pay 1–2 points, weeklies 5–6. Fuze offers 8–20. A 10-minute eight-rabbit contract for 2s is 1.2g per active hour at that pace, 16 iron for 3s is 1.8g/h, and six ore shards for 8s is 4.8g/h. A 30-minute six-diamond weekly worth 1g5s is 3g/h. These are job-equivalent rates. The board limits the number of times a player can earn them. [Contracts](../../design/data/economy.toml) · [Board and turn-ins](../../pack/kubejs/server_scripts/ttl/economy/guild.js)

**Rank-B model.** Start a new character at zero on a Monday. Sample 2,000 independent sequences (integer seeds 0–1999, weighted draws without replacement, one reserved rookie daily). Draw the weeklies first each Monday. On scheduled visits complete each eligible daily, then each outstanding eligible weekly in board order. Carry forward uncompleted weeklies until reset. Credit rank changes as they occur. Budget 10 minutes per daily and 30 per weekly including acquisition and travel, with no failed hunts, waiting, trading or stockpile advantage. These are simulated boards with matching selection rules, not recorded server seeds. Read each cell as a median, with calendar P10–P90 in parentheses.

| Visits | B points | Days | Active guild hours | Gold earned | Jobs |
|---|---:|---:|---:|---:|---:|
| Daily | 140 | 29 (29–31) | 16.83 | 33.5 | 89 |
| Mon/Wed/Fri | 140 | 57 (57–64) | 16.50 | 34.2 | 80 |
| Daily | 110 | 24 (22–26) | 13.33 | 26.0 | 71 |
| Mon/Wed/Fri | 110 | 50 (47–54) | 13.33 | 26.3 | 67 |

At current rates the two schedules earn about 1.99 and 2.07g per active guild hour respectively (ratio of medians). Halving or doubling completion times doubles or halves those gross rates and leaves the modeled board dates unchanged, provided sessions still fit. Unreachable enemies or distant contracts increase the real calendar time. A 50g charter needs about 25 guild hours at 2g/h, or about 12.5h each for two equal contributors. The independent Tier 1 stage and membership checks still apply.

**Weekly treasury example.** Five players each earn seven 3s dailies and one 1g weekly: 15.5g newly issued. Add one five-contributor T4 kill and total mint is 140.5g. Fifty claims cost 5g weekly. If these players fund that upkeep and incur no other costs, destruction is 3.56% of issuance. An 80% drain would require 112.4g, another 107.4g that week. This is a five-person worked example, not a server-wide prediction. Deposits and withdrawals move existing money; the nation has no guaranteed weekly income. Treat player trades and the treasury share of public-damage liability as transfers. Count an expense as destruction only when it actually removes value. A one-time 50g charter cannot stabilize all subsequent weeks. [Plan §9](../../design/master-plan.md) · [Coin accounting](../../pack/kubejs/server_scripts/ttl/economy/sinks.js) · [Nation treasury](../../pack/kubejs/server_scripts/ttl/nations/nations.js)

Guild rewards call the economy service. Boss and arena rewards issue physical coins directly. FTB quest authoring also contains 77 item-coin reward entries totaling 126 silver and 74 bronze (13.34g across all authored entries). Branches, prerequisites and claim behavior make that a content inventory rather than a per-character entitlement. Configured altar and identification prices lack corresponding charges on those action paths. The actual core opener consumes the item and handles a failed grant. Reconcile physical issuance, charges and refunds with the ledger, and report by source, reason, week and active-player count. [Boss consumer](../../pack/kubejs/server_scripts/ttl/bosses/boss.js) · [Arena consumer](../../pack/kubejs/server_scripts/ttl/arena/arenas.js) · [Core opening](../../pack/kubejs/server_scripts/ttl/era/era.js) · [Quest sources](../../design/quests)

Public Works gives one merit per eligible placement, 200 per player per week, 100 per player per chunk per week, and one faction reputation per 100. Builder needs 500, so the fastest schedule is three weekly periods using at least two chunks in each 200-point week. Someone working a single chunk needs five periods. Each player may mark four works. The trigger rewards placement and limits repeat gains by time and chunk. Check finished public infrastructure and repeated placements separately when judging whether this is paying for durable construction. [Merit consumer](../../pack/kubejs/server_scripts/ttl/economy/merit.js)

## Mortal life, judgment, trials and carryover

Each axis contributes weighted `100 × ln(1 + raw/k)`; the total adds half the strongest weighted axis. Valor uses k=100, Longevity 60 and Order, Chaos, Craft and Faith 40. Chaos contributes half weight to the total. Its **unweighted** value governs the dark prefix, requiring ≥60 and at least Order. Four villager kills at 10 raw each yield about 69.3 Chaos before comparison with Order. Tracked hostile types give full credit on the first 30 each, then 15% of the tail up to 80 full-equivalent kills; the remaining unclassified kills share 100/15%/200 settings. Travel counts distinct 64×64 cells, capped at 30 per UTC day. Longevity samples activity every 20 seconds. One 20-minute active Minecraft day at 20 TPS is the time unit for the gates. [Karma data](../../design/data/karma.toml) · [Judgment](../../pack/kubejs/server_scripts/ttl/karma/karma.js) · [Tracking](../../pack/kubejs/server_scripts/ttl/karma/tracking.js)

| Life 1 profile | Inputs | Score / outcome |
|---|---|---|
| First evening, 30m | 4 cells, 4 advancements, 10 kills across 2 tracked types | 64, Wanderer, 1 day |
| Curious newcomer, 1h | 12 cells, 6 trades, 6 animals bred, 2 diamond ore, 8 advancements, 24 kills / 4 types | 149, Survivor, 3 days |
| Mixed survival, 4h | 30 cells, Nether, 30 trades, 24 bred, 12 diamond ore, 5 anvils, 8 enchants, 24 advancements, 100 kills / 6 types | 447, Survivor, 12 days |
| Adventurer, 12h | 90 cells over ≥3 UTC dates, Nether and End, dragon, 90 trades, 60 bred, 32 diamond ore, 8 debris, 12 anvils, 20 enchants, 45 advancements, 240 kills / 10 types | 854, Hero, 36 days |
| Completionist, 20h | 120 cells over ≥4 dates, both dimensions, dragon and wither, 180 trades, 100 bred, 64 diamond ore, 18 debris, 30 anvils, 42 enchants, 70 advancements, 400 kills / 12 types | 1110, Legend, 60 days |

Scores are outputs of the shipped judge with synthetic records (unlisted stats zero, typed kills distributed evenly to within one in data order). Reaching Survivor takes 100 **and** 2 days (40m), Hero 600 and 7 days (2h20m), Legend 1,000 and 30 days (10h) plus a major boss. Additional time alone cannot guarantee a tier. The plan budgets 2–6 hours of content and explicitly reserves the 10-hour minimum for Legend. Collect score, axis mix, active minutes and reason for tier failure when a first life ends before shortening that prestige gate. [Design targets](../../design/master-plan.md)

Wanderer/Survivor/Hero/Legend offer 2/3/4/5 race slots, with 0/0/1/2 guaranteed from the tier’s own list and 1/1/3/3 normal Unique choices. Legend gains one extra skill from its configured pool and can receive a separate Legendary echo subject to availability. Ten optional Corridor trials include timed challenges and a 4-of-5 knowledge check. A pass can widen the wish selection to three. Its marginal choice benefit is greatest in the two lower tiers. The Soul Gem gives Regeneration and Resistance for 8/12/20/30 seconds at amplifier 0/0/1/1, once per 20 minutes. Perfect use covers only 0.67/1/1.67/2.5% of elapsed time. The book needs Hero+, strongest Craft of at least 150 and a qualifying remembered enchantment, capped at level III. A specialist can meet Craft yet miss Hero on total score. [Trials](../../design/data/trials.toml) · [Carryover](../../design/data/carryover.toml) · [Item consumer](../../pack/kubejs/server_scripts/ttl/life/carryover.js)

## Boss scaling, lockouts and arenas

There are 22 boss definitions: 2 Tier 1, 11 Tier 2, 6 Tier 3 and 3 Tier 4. The framework records the entity’s base maximum health, computes `max(base, round(base × (hp_mult + per_player_mult × (n − 1))))`, and writes the attribute. The count is nearby qualifying players at registration or wake-up. The normal fight poll tracks eligibility and phases without continuously reapplying scaling. Late arrivals therefore can change effective difficulty. An entity's native attributes, other mods and attribute bounds still affect the observed HP. [Roster](../../design/data/bosses.toml) · [Registration, wake and reward](../../pack/kubejs/server_scripts/ttl/bosses/boss.js)

| Tier | One player | Two | Three | Four | Five | Defeat lock per boss ID | Coin per full winner |
|---|---:|---:|---:|---:|---:|---|---|
| 1 | 2× | 2.5× | 3× | 3.5× | 4× | 24h | 1g |
| 2 | 3× | 3.75× | 4.5× | 5.25× | 6× | 48h | 3g |
| 3 | 4× | 5× | 6× | 7× | 8× | 72h | 10g, Rimuru Ogre 15g |
| 4 | 6× | 7.5× | 9× | 10.5× | 12× | 96h | 25g |

For a hypothetical 40-base-HP T4 entity the five targets are 240, 300, 360, 420 and 480 HP. With identical sustained damage and five simultaneous attackers, a registered five-person party faces twice the solo HP and requires 40% of the solo encounter time before phase mechanics. Direct damage, presence (15 seconds plus being in range) and kill attribution all matter to credit. The one-core-per-party limit applies to **additional** credited party members, outside full contributors. Five eligible participants can all receive cores on a core-dropping boss. Wild encounters allow one concurrent fight, two starts per day and a six-hour gap. Positive base wild chances range from 0.001 to 0.03 per eligible day before regional, path, time or weather checks; some bosses are disabled or have no wild schedule. A player spending a few hours outside the eligible region cannot use these rates to plan a farming session. [Wild scheduler](../../pack/kubejs/server_scripts/ttl/bosses/wild.js)

Walpurgis and the Labyrinth support duel, party and challenge modes with 5/10/15-minute limits, a 5-second countdown and 60/120/720-minute personal loot cooldowns per venue and mode. PvP requires 30 seconds for loot. A pair completing one decisive duel in both venues can mint 8s+2s and 10s+2s in an hourly reward cycle, **2.2g per pair**, before other loot. The waiting-time average is 1.1g per person per hour with an even split. Repeated opponents are a useful signal to measure alongside time actually spent fighting. [Arena tables](../../design/data/arenas.toml) · [Settlement](../../pack/kubejs/server_scripts/ttl/arena/arenas.js)

Challenge waves scale individual mob counts by `1 + 0.5 × (party − 1)`, rounded per mob entry and capped at 16 per wave. Walpurgis rises from 15 mobs solo to 40 for five, Labyrinth from 13 to 37. Waves use empty mob loot. A full five-person Walpurgis clear can issue 5 × (10g boss + 3g clear) = 65g, the Labyrinth 5 × (25g + 4g) = 145g, plus cores, when all five qualify for both payouts. The shared final bosses have 72h/96h locks. Even a permanently booked venue can get only about 2.33/1.75 rewarded boss defeats per seven days in the long run, before outside groups use the same lock. A blocked boss summon after three waves settles as partial, 12s/15s each, and can spend a player’s challenge loot cooldown. Both venues have a 2s fail reward. This creates a progression bottleneck and a repeatable consolation faucet at the same time. Distinguish pre-existing lockouts, legitimate defeats and real losses in the results.

## Unique skills, absorption and scarcity

Nine Legendary IDs admit three simultaneous copies apiece. The independent limit of **ten distinct holders** means the maximum share holding any Legendary is 100% at ten actives, 50% at twenty and 33.3% at thirty, assuming every holder is active in the denominator. A player can own more than one. A roster of ten holders can block a new eligible recipient while many of the theoretical 27 copies remain free. A holder who leaves can retain a place for 30 days. Era slots = 0 adds no further throttle. Act VII draws Light from Great Sage and Creator (six copies in total) and Dark from seven other IDs (21). Six is the ceiling for distinct people simultaneously holding a copy from the Light capstone pool, even before the global ceiling. The fallback and frequency of empty offers should be tracked by path. [Registry data](../../design/data/skills.toml) · [Holder checks](../../pack/kubejs/server_scripts/ttl/registry.js) · [Path pools](../../design/data/story.toml)

There are 29 Rare IDs × 3 = 87 seats and 17 Common IDs × 5 = 85. Even perfectly spread, that is 5.73 non-Legendary holdings per person at 30 players. Each eligible ID receives its rarity weight on an ordinary core draw. With all IDs available to the opener the Rare probability is 29×3 / (29×3 + 17) = 83.65%. At equal per-ID weights it is 29/46 = 63.04%. Player ownership, cap saturation and scarce pools change subsequent odds. Ordinary cores exclude Legendaries. Measure open attempts, returned cores, eligible pool sizes and unique owners over time.

Ordinary consensual duels require an absorber, a victim at ≥50% of the killer’s EP and a 72h absorption cooldown by default. The table permits one Legendary transfer plus one Rare/Common copy per eligible kill, while official war needs no absorber and sets the EP floor to zero. An awakening challenge targets the 50–100% EP interval and does not require the defender to accept. Voluntary bequests and staff moves provide further circulation. Public duel liability charges 5 bronze per recorded block up to 5g, reaching the fee ceiling after 100 blocks, while at most 512 changes are recorded. Restoration and suppressed drops protect public builds, and offline collection is held seven days. Monitor uncollected charges, repeated transfers between the same people, and whether war participation correlates with concentration. [Absorption settings](../../design/data/skills.toml) · [Absorption and liability](../../pack/kubejs/server_scripts/ttl/absorb)

## Factions, story and national power

Eight faction reputations run from −100 to +100. Band boundaries are −50 Hostile, −20 Unfriendly, +20 Friendly, +50 Honored and +80 Exalted. Drift toward zero is applied every seven real days, including catch-up after absence. Tempest and the Holy faction drift one point, Dwargon, Blumund, Falmuth, the Orc Horde and lizardmen two, and Outcasts zero. A Blumund character at +80 loses Exalted after one unpaid-in-reputation week, and −50 drifts back to −48 over the same time. In a two-point-decay faction, three positive rep per week nets only one while above zero. Four −15 NPC kills, or three −20 kills in the Holy faction, can turn a neutral character Hostile. Race, first-life axis and dark-path seeds alter the starting point. Dwargon mirrors the mod's reputation and thus has immediate guard and trade consequences. [Faction data](../../design/data/factions.toml) · [Drift, bands and renown](../../pack/kubejs/server_scripts/ttl/rep/rep.js)

The oath grants +20 Tempest on Light, or +20 Outcasts, +15 Orc Horde and −20 Tempest on Dark. The party leader’s oath can apply to online members. There is one gated reversal. Seven sequential acts pay 5+5+10+15+20+30+50 = **135 renown** before flags or other awards. Reputation affects access while renown counts toward national size. The four held boss-tier stages contribute up to 10+20+40+80 = 150 renown. Each Common/Rare/Legendary Unique adds 4/10/25. Concentrating transferable skills in one nation therefore raises both its combat strength and political value. Compare story starts and completions by path, party, and time blocked by a shared fight, with special attention to the small Light capstone pool. [Story rules](../../design/data/story.toml) · [Story consumer](../../pack/kubejs/server_scripts/ttl/story/story.js)

A nation requires 2–5 members, the Tier 1 stage and a 50g charter. Non-nation players have four base claims. National allowance uses 10 per member plus rank bonuses of 0/2/4/6/8 per member. A two-member nation ranges from 20 to 36 claims (2–3.6g/week fully claimed), a five-member nation from 50 to 90 (5–9g/week). Rank thresholds are 0/150/400/900/2000. National value sums members’ renown, one per claimed chunk, ten per Public Works and one per whole gold in treasury. Five members at 150 renown, 50 claims, four works and 100g contribute 750+50+40+100=940, enough for City and an 80-claim allowance. Rent is due on actual claims. Keeping the same holdings while halving treasury rank weight gives 890, falling below City. Replay near-threshold nations before applying the proposal. [Nation design](../../design/data/nations.toml) · [Claim consumer](../../pack/kubejs/server_scripts/ttl/nations/claims.js)

Unpaid upkeep accumulates debt, which deposits can settle. By the second unpaid week Neglect configures 75% yield, 5% nothing chance and 25% growth skip on eligible resources/crops; the next stage configures 50% yield, 15% nothing and 50% growth skip. Resource-specific events and integer item drops affect real yield. A returning nation can therefore face lower output while servicing accumulated debt. Track arrears, claim count, member activity and weeks to recovery separately from prosperous guilds’ treasuries. [Debuff consumer](../../pack/kubejs/server_scripts/ttl/nations/upkeep_debuff.js)

## Events and access to catch-up

The director polls scheduled work every minute with hook polling every five seconds. Defaults allow three capped starts per Brussels day, three concurrently active timed events and 30 minutes between capped starts. Only Favor has an automatic cadence in the two event records: once every seven days at 19:00 Brussels with a 24h catch-up window. Omen is manually started. Wild bosses have their own clock and limits. An empty calendar outside Favor follows directly from the supplied schedule. [Event data](../../design/data/events.toml) · [Director](../../pack/kubejs/server_scripts/ttl/events/director.js)

Favor filters for eligible **online** Life 2 characters with at least five online hours this week, a linked account when the Discord bridge applies, and no award within 30 days. It draws one winner at random from the lowest ceil(25%) by EP. With 10/20/30 eligible *online at the draw*, the pools are 3/5/8 and individual chances within them are 1/3, 1/5 and 1/8. Others receive zero chance for that draw. Even an uninterrupted weekly cadence is only 4.35 awards per average month. The winner gets 48h to pick one of three offers from five choices. EP grants max(100, 20% of current EP), so 1,000 EP gains 200 and 20,000 gains 4,000. Protection provides Resistance II and Absorption III for two hours. Other options include a Common Unique, resistance or relics. Count unique eligible people during the whole window separately from actual online candidates at selection. This distinguishes time-zone coverage from loot strength. [Eligibility and awards](../../pack/kubejs/server_scripts/ttl/events/favor.js)

## External comparisons and live verification

CCP publishes EVE Online’s economic report with downloadable data and explicitly identifies corrections to its figures. For this pack, publish a weekly opening balance, minted sources, destructive sinks and closing balance. A source omission as large as a boss party payout can reverse an apparent trend. The portable lesson is accounting coverage, not a price ratio borrowed from EVE. [EVE Online monthly economic report](https://www.eveonline.com/news/view/monthly-economic-report-october-2024)

Final Fantasy XIV’s Palace of the Dead separates fixed-party progress and matched-party entry and documents the corresponding save and equipment rules. Here, the venue, individual prize timer and globally shared final boss each have different owners. Display all three before a reservation and record progress by party size. This lets players decide whether an encounter can advance their story or is a practice run. [Palace of the Dead guide](https://na.finalfantasyxiv.com/lodestone/playguide/contentsguide/deepdungeon/)

For the first four weeks collect active hours by life, new-character cohorts, unique players, claims actually billed, amounts owed and paid, net currency per person, and gross generation by source. For each boss record base HP, participants at spawn and wake, eligible winners at defeat, elapsed time, loot and cooldown denials. For each core log eligible counts and success/refund. Compare solos, groups of two and five, established players and new starters. Publish medians and P10–P90 with counts. When there are only a few T4 clears, report each observation; a percentile from two fights would obscure the difference between an invited party and an open fight.

## Numeric settings at the reviewed revision

Expand a file to look up the inputs behind the estimates. Array indices start at zero. A full selector includes the row prefix and the field name. This snapshot also includes coordinates, schema versions and timing for polling so they can be distinguished from progression settings. Rates in the analysis use the scripts’ timer semantics.

<details>
<summary>arenas.toml</summary>

[Source table](../../design/data/arenas.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| arena[0] · walpurgis | `spawn_a` [92, 12, 27], `spawn_b` [92, 12, 53], `challenge_cooldown_minutes` 30 |
| arena[0] · walpurgis.box | `from` [75, 12, 23], `to` [109, 30, 57] |
| arena[0] · walpurgis.challenge | `per_player` 0.5, `max_mobs` 16 |
| arena[0] · walpurgis.challenge.waves[0].mobs[0] | `count` 4 |
| arena[0] · walpurgis.challenge.waves[0].mobs[1] | `count` 3 |
| arena[0] · walpurgis.challenge.waves[1].mobs[0] | `count` 3 |
| arena[0] · walpurgis.challenge.waves[1].mobs[1] | `count` 2 |
| arena[0] · walpurgis.challenge.waves[2].mobs[0] | `count` 1 |
| arena[0] · walpurgis.challenge.waves[2].mobs[1] | `count` 2 |
| arena[0] · walpurgis.cooldown_minutes | `duel` 60, `party` 120, `challenge` 720 |
| arena[0] · walpurgis.loot.challenge.clear | `rolls` 2, `xp` 15 |
| arena[0] · walpurgis.loot.challenge.clear.coins | `gold` 3 |
| arena[0] · walpurgis.loot.challenge.clear.items[0] · tensura:medium_quality_magic_crystal | `count` 2 |
| arena[0] · walpurgis.loot.challenge.fail.coins | `silver` 2 |
| arena[0] · walpurgis.loot.challenge.partial | `rolls` 1, `xp` 5 |
| arena[0] · walpurgis.loot.challenge.partial.coins | `silver` 12 |
| arena[0] · walpurgis.loot.duel.draw.coins | `silver` 4 |
| arena[0] · walpurgis.loot.duel.lose.coins | `silver` 2 |
| arena[0] · walpurgis.loot.duel.win | `rolls` 1, `xp` 5 |
| arena[0] · walpurgis.loot.duel.win.coins | `silver` 8 |
| arena[0] · walpurgis.loot.party.draw.coins | `silver` 5 |
| arena[0] · walpurgis.loot.party.lose.coins | `silver` 3 |
| arena[0] · walpurgis.loot.party.win | `rolls` 1, `xp` 5 |
| arena[0] · walpurgis.loot.party.win.coins | `silver` 10 |
| arena[0] · walpurgis.minutes | `duel` 5, `party` 10, `challenge` 15 |
| arena[0] · walpurgis.mob_spots[0] | [92, 12, 40] |
| arena[0] · walpurgis.mob_spots[1] | [82, 12, 40] |
| arena[0] · walpurgis.mob_spots[2] | [102, 12, 40] |
| arena[0] · walpurgis.mob_spots[3] | [92, 12, 32] |
| arena[0] · walpurgis.mob_spots[4] | [92, 12, 48] |
| arena[0] · walpurgis.round | `centre` [92, 40], `radius` 17 |
| arena[1] · labyrinth | `spawn_a` [16, 38, 512], `spawn_b` [16, 38, 562], `challenge_cooldown_minutes` 30 |
| arena[1] · labyrinth.box | `from` [-24, 38, 497], `to` [56, 100, 577] |
| arena[1] · labyrinth.challenge | `per_player` 0.5, `max_mobs` 16 |
| arena[1] · labyrinth.challenge.waves[0].mobs[0] | `count` 3 |
| arena[1] · labyrinth.challenge.waves[0].mobs[1] | `count` 3 |
| arena[1] · labyrinth.challenge.waves[1].mobs[0] | `count` 2 |
| arena[1] · labyrinth.challenge.waves[1].mobs[1] | `count` 2 |
| arena[1] · labyrinth.challenge.waves[2].mobs[0] | `count` 1 |
| arena[1] · labyrinth.challenge.waves[2].mobs[1] | `count` 2 |
| arena[1] · labyrinth.cooldown_minutes | `duel` 60, `party` 120, `challenge` 720 |
| arena[1] · labyrinth.loot.challenge.clear | `rolls` 2, `xp` 20 |
| arena[1] · labyrinth.loot.challenge.clear.coins | `gold` 4 |
| arena[1] · labyrinth.loot.challenge.clear.items[0] · tensura:high_quality_magic_crystal | `count` 1 |
| arena[1] · labyrinth.loot.challenge.clear.items[1] · tensura:medium_quality_magic_crystal | `count` 2 |
| arena[1] · labyrinth.loot.challenge.fail.coins | `silver` 2 |
| arena[1] · labyrinth.loot.challenge.partial | `xp` 5 |
| arena[1] · labyrinth.loot.challenge.partial.coins | `silver` 15 |
| arena[1] · labyrinth.loot.challenge.partial.items[0] · tensura:medium_quality_magic_crystal | `count` 1 |
| arena[1] · labyrinth.loot.duel.draw.coins | `silver` 4 |
| arena[1] · labyrinth.loot.duel.lose.coins | `silver` 2 |
| arena[1] · labyrinth.loot.duel.win | `xp` 5 |
| arena[1] · labyrinth.loot.duel.win.coins | `silver` 10 |
| arena[1] · labyrinth.loot.duel.win.items[0] · tensura:low_quality_magic_crystal | `count` 2 |
| arena[1] · labyrinth.loot.party.draw.coins | `silver` 5 |
| arena[1] · labyrinth.loot.party.lose.coins | `silver` 3 |
| arena[1] · labyrinth.loot.party.win | `xp` 5 |
| arena[1] · labyrinth.loot.party.win.coins | `silver` 12 |
| arena[1] · labyrinth.loot.party.win.items[0] · tensura:low_quality_magic_crystal | `count` 3 |
| arena[1] · labyrinth.minutes | `duel` 5, `party` 10, `challenge` 15 |
| arena[1] · labyrinth.mob_spots[0] | [16, 38, 537] |
| arena[1] · labyrinth.mob_spots[1] | [0, 38, 537] |
| arena[1] · labyrinth.mob_spots[2] | [32, 38, 537] |
| arena[1] · labyrinth.mob_spots[3] | [16, 38, 527] |
| arena[1] · labyrinth.mob_spots[4] | [16, 38, 547] |
| arena[1] · labyrinth.ready | `at` [16, 37, 537] |
| arena[1] · labyrinth.round | `centre` [16, 537], `radius` 38 |
| rules | `poll_ticks` 20, `lobby_minutes` 5, `countdown_seconds` 5, `return_seconds` 5, `min_seconds` 30, `max_side` 5, `party_min_side` 2, `leave_grace_seconds` 3 |
| rules.story | `duel_streak` 3, `party_side` 3 |
| walpurgis | `invite_hours` 24, `cooldown_seconds` 4, `notice_seconds` 20 |
| walpurgis.gate | `from` [49, 9, 36], `to` [59, 10, 39] |
| walpurgis.return | `at` [54, 8, 43] |

</details>

<details>
<summary>arrival.toml</summary>

[Source table](../../design/data/arrival.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| life2 | `x` 271, `z` -624, `yaw` -156, `search` 40, `version` 1, `grace_seconds` 20 |

</details>

<details>
<summary>bosses.toml</summary>

[Source table](../../design/data/bosses.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| boss[0] · orc_lord | `tier` 1, `hp_mult` 2.0, `per_player_mult` 0.5, `range` 48, `cooldown_hours` 24 |
| boss[0] · orc_lord.phases[0] | `at_hp` 0.6, `count` 4 |
| boss[0] · orc_lord.phases[1] | `at_hp` 0.3, `enrage` 1 |
| boss[0] · orc_lord.rewards.coins | `silver` 10 |
| boss[0] · orc_lord.rewards.rep | `tempest` 5 |
| boss[0] · orc_lord.wild | `chance_per_day` 0.03 |
| boss[10] · sylphide | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[10] · sylphide.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[10] · sylphide.rewards.coins | `gold` 3 |
| boss[11] · undine | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[11] · undine.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[11] · undine.rewards.coins | `gold` 3 |
| boss[12] · akash | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[12] · akash.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[12] · akash.rewards.coins | `gold` 3 |
| boss[13] · charybdis | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[13] · charybdis.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[13] · charybdis.phases[1] | `at_hp` 0.3, `enrage` 2 |
| boss[13] · charybdis.rewards.coins | `gold` 10 |
| boss[13] · charybdis.spawn.at | `x` 635, `z` 145, `radius` 96 |
| boss[13] · charybdis.wild | `chance_per_day` 0.003 |
| boss[14] · gazel_dwargo | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[14] · gazel_dwargo.kill_rep | `dwargon` -60 |
| boss[14] · gazel_dwargo.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[14] · gazel_dwargo.rewards.coins | `gold` 10 |
| boss[14] · gazel_dwargo.spawn.at | `x` 435, `z` -1106, `radius` 40 |
| boss[14] · gazel_dwargo.wild | `chance_per_day` 0.0 |
| boss[15] · hinata_sakaguchi | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[15] · hinata_sakaguchi.kill_rep | `holy_church` -30 |
| boss[15] · hinata_sakaguchi.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[15] · hinata_sakaguchi.rewards.coins | `gold` 10 |
| boss[15] · hinata_sakaguchi.spawn.at | `x` -400, `z` -60, `radius` 48 |
| boss[15] · hinata_sakaguchi.wild | `chance_per_day` 0.005 |
| boss[15] · hinata_sakaguchi.wild.path_mult | `dark` 3 |
| boss[16] · carrion | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[16] · carrion.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[16] · carrion.rewards.coins | `gold` 10 |
| boss[16] · carrion.wild | `chance_per_day` 0.003 |
| boss[17] · rimuru_ogre_fight | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[17] · rimuru_ogre_fight.arena | `x` 0, `z` 0, `radius` 48 |
| boss[17] · rimuru_ogre_fight.kill_rep | `tempest` -40 |
| boss[17] · rimuru_ogre_fight.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[17] · rimuru_ogre_fight.phases[1] | `at_hp` 0.3, `enrage` 2 |
| boss[17] · rimuru_ogre_fight.rewards.coins | `gold` 15 |
| boss[18] · clayman | `tier` 3, `hp_mult` 4.0, `per_player_mult` 1.0, `range` 64, `cooldown_hours` 72 |
| boss[18] · clayman.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[18] · clayman.phases[1] | `at_hp` 0.3, `enrage` 2 |
| boss[18] · clayman.rewards.coins | `gold` 10 |
| boss[18] · clayman.wild | `chance_per_day` 0.002 |
| boss[19] · luminous_valentine | `tier` 4, `hp_mult` 6.0, `per_player_mult` 1.5, `range` 72, `cooldown_hours` 96 |
| boss[19] · luminous_valentine.phases[0] | `at_hp` 0.7, `enrage` 1 |
| boss[19] · luminous_valentine.phases[1] | `at_hp` 0.35, `enrage` 2 |
| boss[19] · luminous_valentine.rewards.coins | `gold` 25 |
| boss[19] · luminous_valentine.wild | `chance_per_day` 0.001 |
| boss[1] · supermassive_slime | `tier` 1, `hp_mult` 2.0, `per_player_mult` 0.5, `range` 48, `cooldown_hours` 24 |
| boss[1] · supermassive_slime.phases[0] | `at_hp` 0.5, `count` 5 |
| boss[1] · supermassive_slime.rewards.coins | `silver` 10 |
| boss[1] · supermassive_slime.rewards.rep | `tempest` 5 |
| boss[1] · supermassive_slime.wild | `chance_per_day` 0.03 |
| boss[20] · veldora | `tier` 4, `hp_mult` 6.0, `per_player_mult` 1.5, `range` 72, `cooldown_hours` 96 |
| boss[20] · veldora.phases[0] | `at_hp` 0.7, `enrage` 1 |
| boss[20] · veldora.phases[1] | `at_hp` 0.35, `enrage` 2 |
| boss[20] · veldora.rewards.coins | `gold` 25 |
| boss[20] · veldora.wild | `chance_per_day` 0.001 |
| boss[21] · elemental_colossus | `tier` 4, `hp_mult` 6.0, `per_player_mult` 1.5, `range` 72, `cooldown_hours` 96 |
| boss[21] · elemental_colossus.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[21] · elemental_colossus.phases[1] | `at_hp` 0.3, `enrage` 2 |
| boss[21] · elemental_colossus.rewards.coins | `gold` 25 |
| boss[21] · elemental_colossus.wild | `chance_per_day` 0.002 |
| boss[2] · ifrit | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[2] · ifrit.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[2] · ifrit.phases[1] | `at_hp` 0.25, `enrage` 2 |
| boss[2] · ifrit.rewards.coins | `gold` 3 |
| boss[2] · ifrit.spawn.at | `x` 0, `z` 0, `radius` 48 |
| boss[2] · ifrit.wild | `chance_per_day` 0.01 |
| boss[3] · orc_disaster | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[3] · orc_disaster.phases[0] | `at_hp` 0.6, `count` 6 |
| boss[3] · orc_disaster.phases[1] | `at_hp` 0.3, `enrage` 1 |
| boss[3] · orc_disaster.rewards.coins | `gold` 3 |
| boss[3] · orc_disaster.rewards.rep | `tempest` 8 |
| boss[3] · orc_disaster.spawn.at | `x` 1106, `z` 539, `radius` 64 |
| boss[3] · orc_disaster.wild | `chance_per_day` 0.01 |
| boss[4] · rimuru_clone | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[4] · rimuru_clone.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[4] · rimuru_clone.rewards.coins | `gold` 3 |
| boss[4] · rimuru_clone.wild | `chance_per_day` 0.005 |
| boss[5] · folgen | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[5] · folgen.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[5] · folgen.rewards.coins | `gold` 3 |
| boss[5] · folgen.spawn.at | `x` 0, `z` 40, `radius` 48 |
| boss[5] · folgen.wild | `chance_per_day` 0.005 |
| boss[6] · kyoya_tachibana | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[6] · kyoya_tachibana.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[6] · kyoya_tachibana.rewards.coins | `gold` 3 |
| boss[6] · kyoya_tachibana.wild | `chance_per_day` 0.005 |
| boss[7] · shogo_taguchi | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[7] · shogo_taguchi.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[7] · shogo_taguchi.rewards.coins | `gold` 3 |
| boss[7] · shogo_taguchi.wild | `chance_per_day` 0.005 |
| boss[8] · kirara_mizutani | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[8] · kirara_mizutani.phases[0] | `at_hp` 0.5, `enrage` 1 |
| boss[8] · kirara_mizutani.rewards.coins | `gold` 3 |
| boss[8] · kirara_mizutani.wild | `chance_per_day` 0.005 |
| boss[9] · shizu | `tier` 2, `hp_mult` 3.0, `per_player_mult` 0.75, `range` 56, `cooldown_hours` 48 |
| boss[9] · shizu.arena | `x` 0, `z` 0, `radius` 48 |
| boss[9] · shizu.phases[0] | `at_hp` 0.6, `enrage` 1 |
| boss[9] · shizu.phases[1] | `at_hp` 0.3, `enrage` 2 |
| boss[9] · shizu.rewards.coins | `gold` 3 |
| boss[9] · shizu.rewards.rep | `tempest` 10 |
| boss[9] · shizu.wild | `chance_per_day` 0.01 |
| framework | `idle_minutes` 30, `presence_secs` 15, `party_credit_range` 2.0, `core_per_party` 1 |
| wild | `max_active` 1, `max_per_day` 2, `min_gap_hours` 6, `require_players` 1, `distance` [64, 160], `idle_minutes` 30, `rewards_mult` 1.0 |

</details>

<details>
<summary>carryover.toml</summary>

[Source table](../../design/data/carryover.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| book | `min_axis_score` 150, `max_level` 3 |
| gem.life2 | `cooldown_minutes` 20 |
| gem.life2.tiers.elite | `seconds` 20, `amplifier` 1 |
| gem.life2.tiers.legendary | `seconds` 30, `amplifier` 1 |
| gem.life2.tiers.normal | `seconds` 12, `amplifier` 0 |
| gem.life2.tiers.underdog | `seconds` 8, `amplifier` 0 |

</details>

<details>
<summary>discord.toml</summary>

[Source table](../../design/data/discord.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| limits | `recap_lines` 8, `top_lines` 5 |
| timing | `role_sync_minutes` 5, `leaderboard_minutes` 10, `recap_weekday` 0, `recap_hour` 20, `awaken_ticks` 100 |

</details>

<details>
<summary>economy.toml</summary>

[Source table](../../design/data/economy.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| bounty[0] · rabbit_cull | `count` 8, `points` 1, `weight` 10 |
| bounty[0] · rabbit_cull.reward.coins | `silver` 2 |
| bounty[0] · rabbit_cull.reward.rep | `blumund` 1 |
| bounty[10] · ration_order | `count` 16, `points` 1, `weight` 8 |
| bounty[10] · ration_order.reward.coins | `silver` 2 |
| bounty[10] · ration_order.reward.rep | `tempest` 1 |
| bounty[11] · ore_shards | `count` 6, `points` 2, `weight` 6 |
| bounty[11] · ore_shards.reward.coins | `silver` 8 |
| bounty[11] · ore_shards.reward.rep | `dwargon` 2 |
| bounty[12] · visit_goblins | `count` 1, `points` 1, `weight` 6 |
| bounty[12] · visit_goblins.reward.coins | `silver` 2 |
| bounty[12] · visit_goblins.reward.rep | `tempest` 1 |
| bounty[13] · visit_dwarves | `count` 1, `points` 2, `weight` 6 |
| bounty[13] · visit_dwarves.reward.coins | `silver` 3 |
| bounty[13] · visit_dwarves.reward.rep | `dwargon` 1 |
| bounty[14] · visit_treyni | `count` 1, `points` 2, `weight` 5 |
| bounty[14] · visit_treyni.reward.coins | `silver` 5 |
| bounty[14] · visit_treyni.reward.rep | `tempest` 1 |
| bounty[15] · week_direwolves | `count` 20, `points` 5, `weight` 8 |
| bounty[15] · week_direwolves.reward.coins | `gold` 1 |
| bounty[15] · week_direwolves.reward.rep | `blumund` 3 |
| bounty[16] · week_spiders | `count` 25, `points` 6, `weight` 6 |
| bounty[16] · week_spiders.reward.coins | `gold` 2 |
| bounty[16] · week_spiders.reward.rep | `blumund` 4 |
| bounty[17] · week_caterpillars | `count` 10, `points` 6, `weight` 5 |
| bounty[17] · week_caterpillars.reward.coins | `gold` 2 |
| bounty[17] · week_caterpillars.reward.rep | `blumund` 4 |
| bounty[18] · week_blazes | `count` 15, `points` 6, `weight` 5 |
| bounty[18] · week_blazes.reward.coins | `gold` 2 |
| bounty[19] · week_magisteel | `count` 4, `points` 6, `weight` 6 |
| bounty[19] · week_magisteel.reward.coins | `gold` 2 |
| bounty[19] · week_magisteel.reward.rep | `dwargon` 3 |
| bounty[1] · zombie_sweep | `count` 15, `points` 1, `weight` 10 |
| bounty[1] · zombie_sweep.reward.coins | `silver` 2 |
| bounty[1] · zombie_sweep.reward.rep | `blumund` 1 |
| bounty[20] · week_diamonds | `count` 6, `points` 5, `weight` 6 |
| bounty[20] · week_diamonds.reward.coins | `gold` 1, `silver` 5 |
| bounty[20] · week_diamonds.reward.rep | `blumund` 2 |
| bounty[21] · week_lizardmen | `count` 1, `points` 5, `weight` 6 |
| bounty[21] · week_lizardmen.reward.coins | `gold` 1 |
| bounty[21] · week_lizardmen.reward.rep | `lizardmen` 2 |
| bounty[22] · week_orc_camp | `count` 1, `points` 6, `weight` 5 |
| bounty[22] · week_orc_camp.reward.coins | `gold` 2 |
| bounty[22] · week_orc_camp.reward.rep | `blumund` 2 |
| bounty[23] · fz_caterpillar_plague | `count` 25, `points` 9, `weight` 8 |
| bounty[23] · fz_caterpillar_plague.reward.coins | `gold` 3 |
| bounty[23] · fz_caterpillar_plague.reward.rep | `blumund` 5 |
| bounty[24] · fz_fortress_raid | `count` 20, `points` 9, `weight` 6 |
| bounty[24] · fz_fortress_raid.reward.coins | `gold` 3 |
| bounty[25] · fz_magisteel_shipment | `count` 16, `points` 9, `weight` 6 |
| bounty[25] · fz_magisteel_shipment.reward.coins | `gold` 4 |
| bounty[25] · fz_magisteel_shipment.reward.rep | `dwargon` 4 |
| bounty[26] · fz_ogre_ruin | `count` 1, `points` 8, `weight` 6 |
| bounty[26] · fz_ogre_ruin.reward.coins | `gold` 3 |
| bounty[26] · fz_ogre_ruin.reward.rep | `tempest` 3 |
| bounty[27] · fz_ender_watch | `count` 30, `points` 12, `weight` 6 |
| bounty[27] · fz_ender_watch.reward.coins | `gold` 5 |
| bounty[28] · fz_ravager_herd | `count` 6, `points` 12, `weight` 5 |
| bounty[28] · fz_ravager_herd.reward.coins | `gold` 5 |
| bounty[28] · fz_ravager_herd.reward.rep | `blumund` 5 |
| bounty[29] · fz_diamond_vault | `count` 24, `points` 12, `weight` 5 |
| bounty[29] · fz_diamond_vault.reward.coins | `gold` 6 |
| bounty[29] · fz_diamond_vault.reward.rep | `blumund` 3 |
| bounty[2] · skeleton_sweep | `count` 12, `points` 1, `weight` 8 |
| bounty[2] · skeleton_sweep.reward.coins | `silver` 2 |
| bounty[2] · skeleton_sweep.reward.rep | `blumund` 1 |
| bounty[30] · fz_wither_hunt | `count` 1, `points` 20, `weight` 4 |
| bounty[30] · fz_wither_hunt.reward.coins | `gold` 9 |
| bounty[30] · fz_wither_hunt.reward.rep | `blumund` 6 |
| bounty[3] · direwolf_hunt | `count` 4, `points` 2, `weight` 8 |
| bounty[3] · direwolf_hunt.reward.coins | `silver` 5 |
| bounty[3] · direwolf_hunt.reward.rep | `blumund` 1 |
| bounty[4] · ant_nest | `count` 6, `points` 2, `weight` 8 |
| bounty[4] · ant_nest.reward.coins | `silver` 4 |
| bounty[4] · ant_nest.reward.rep | `blumund` 1 |
| bounty[5] · bat_swarm | `count` 6, `points` 2, `weight` 6 |
| bounty[5] · bat_swarm.reward.coins | `silver` 3 |
| bounty[5] · bat_swarm.reward.rep | `blumund` 1 |
| bounty[6] · creeper_ward | `count` 8, `points` 2, `weight` 6 |
| bounty[6] · creeper_ward.reward.coins | `silver` 3 |
| bounty[6] · creeper_ward.reward.rep | `blumund` 1 |
| bounty[7] · spider_web | `count` 5, `points` 2, `weight` 6 |
| bounty[7] · spider_web.reward.coins | `silver` 6 |
| bounty[7] · spider_web.reward.rep | `blumund` 2 |
| bounty[8] · iron_order | `count` 16, `points` 1, `weight` 8 |
| bounty[8] · iron_order.reward.coins | `silver` 3 |
| bounty[8] · iron_order.reward.rep | `dwargon` 1 |
| bounty[9] · leather_order | `count` 12, `points` 1, `weight` 8 |
| bounty[9] · leather_order.reward.coins | `silver` 2 |
| bounty[9] · leather_order.reward.rep | `dwargon` 1 |
| coins.rate | `silver` 10, `gold` 10, `stellar` 10 |
| guild | `daily` 3, `weekly` 2, `max_active` 3, `visit_radius` 48, `poll_ticks` 100, `fuze_daily` 0, `fuze_weekly` 2 |
| merit | `per_block` 1, `weekly_cap` 200, `chunk_weekly_cap` 100, `rep_per_100` 1, `builder_at` 500, `works_per_player` 4 |
| rank[0] · F | `points` 0 |
| rank[1] · E | `points` 10 |
| rank[2] · D | `points` 30 |
| rank[3] · C | `points` 70 |
| rank[4] · B | `points` 140 |
| rank[5] · A | `points` 250 |
| rank[6] · S | `points` 400 |
| sinks.altar | `silver` 5 |
| sinks.core_identify | `gold` 2 |
| sinks.upkeep_per_chunk_week | `silver` 1 |

</details>

<details>
<summary>events.toml</summary>

[Source table](../../design/data/events.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| director | `loop_ticks` 1200, `poll_ticks` 100, `window_hours` 6, `retry_minutes` 10, `min_gap_minutes` 30, `max_per_day` 3, `max_active` 3 |
| event[0] · favor | `at_hour` 19, `duration_minutes` 0, `window_hours` 24 |
| event[0] · favor.every | `days` 7 |
| event[1] · omen | `duration_minutes` 2 |
| favor | `bottom_pct` 25, `min_hours` 5, `cooldown_days` 30, `offer_hours` 48, `offer_count` 3 |
| favor.choice.ep_surge | `gain_pct` 20, `gain_min` 100 |
| favor.choice.protection.effects[0] · minecraft:resistance | `seconds` 7200, `amplifier` 1 |
| favor.choice.protection.effects[1] · minecraft:absorption | `seconds` 7200, `amplifier` 2 |
| favor.choice.relic.items[0] · tensura:full_potion | `count` 1 |
| favor.choice.relic.items[1] · tensura:high_quality_magic_crystal | `count` 4 |

</details>

<details>
<summary>factions.toml</summary>

[Source table](../../design/data/factions.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| bands | `hostile` -50, `unfriendly` -20, `friendly` 20, `honored` 50, `exalted` 80 |
| faction[0] · tempest | `decay_per_week` 1 |
| faction[0] · tempest.kill_penalty | `npc` 15, `player` 5 |
| faction[0] · tempest.seed.race | `slime` 20, `goblin` 20, `ogre` 10, `hobgoblin` 10, `lizardman` 5 |
| faction[1] · dwargon | `decay_per_week` 2 |
| faction[1] · dwargon.kill_penalty | `npc` 15, `player` 5 |
| faction[1] · dwargon.seed.axis | `craft` 10 |
| faction[1] · dwargon.seed.race | `dwarf` 20 |
| faction[2] · blumund | `decay_per_week` 2 |
| faction[2] · blumund.kill_penalty | `npc` 15, `player` 5 |
| faction[2] · blumund.seed.axis | `order` 15 |
| faction[2] · blumund.seed.race | `human` 10 |
| faction[3] · falmuth | `decay_per_week` 2 |
| faction[3] · falmuth.kill_penalty | `npc` 15, `player` 5 |
| faction[3] · falmuth.seed.axis | `valor` 10 |
| faction[3] · falmuth.seed.race | `human` 10, `orc` -10, `goblin` -10 |
| faction[4] · holy_church | `decay_per_week` 1 |
| faction[4] · holy_church.kill_penalty | `npc` 20, `player` 5 |
| faction[4] · holy_church.seed.axis | `order` 10, `faith` 10 |
| faction[4] · holy_church.seed.race | `human` 10, `elf` 5, `orc` -15, `high_orc` -20, `ghoul` -25, `wight` -25, `vampire` -40, `lesser_daemon` -40 |
| faction[5] · orc_horde | `decay_per_week` 2 |
| faction[5] · orc_horde.kill_penalty | `npc` 15, `player` 5 |
| faction[5] · orc_horde.seed.axis | `chaos` 15 |
| faction[5] · orc_horde.seed.race | `orc` 20, `high_orc` 30, `ghoul` 5 |
| faction[6] · lizardmen | `decay_per_week` 2 |
| faction[6] · lizardmen.kill_penalty | `npc` 15, `player` 5 |
| faction[6] · lizardmen.seed.race | `lizardman` 20, `dragonewt` 5 |
| faction[7] · outcast | `decay_per_week` 0 |
| faction[7] · outcast.kill_penalty | `npc` 10, `player` 0 |
| faction[7] · outcast.seed | `dark` 20 |
| renown | `min` 0 |
| renown.band | `hostile` -5, `unfriendly` -2, `neutral` 0, `friendly` 3, `honored` 8, `exalted` 15 |
| renown.boss | `ttl.boss.t1` 10, `ttl.boss.t2` 20, `ttl.boss.t3` 40, `ttl.boss.t4` 80 |
| renown.tier | `underdog` 0, `normal` 5, `elite` 15, `legendary` 30 |
| renown.unique | `common` 4, `rare` 10, `legendary` 25 |
| rules | `min` -100, `max` 100, `decay_days` 7, `log_size` 200, `seed_axis_cap` 100 |

</details>

[guide.toml](../../design/data/guide.toml) contains no numeric entries.

<details>
<summary>karma.toml</summary>

[Source table](../../design/data/karma.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| activity | `min_move` 1.5, `min_turn` 15 |
| axes.chaos | `k` 40, `weight` 0.5 |
| axes.craft | `k` 40, `weight` 1.0 |
| axes.faith | `k` 40, `weight` 1.0 |
| axes.longevity | `k` 60, `weight` 1.0 |
| axes.order | `k` 40, `weight` 1.0 |
| axes.valor | `k` 100, `weight` 1.0 |
| dark | `min_score` 60, `guaranteed` 1 |
| explore | `cell_size` 64, `cell_value` 64, `daily_cap` 30 |
| hostiles | `weight_per_kind` 4 |
| kill_cap | `full` 30, `tail` 0.15, `max` 80, `other_full` 100, `other_tail` 0.15, `other_max` 200 |
| root | `best_axis_bonus` 0.5, `track_seconds` 20, `ticks_per_day` 24000 |
| stats[0] · play_time | `weight` 10, `per` 24000 |
| stats[10] · ravager | `weight` 10 |
| stats[11] · trades | `weight` 1 |
| stats[12] · raids_won | `weight` 30 |
| stats[13] · animals_bred | `weight` 0.5 |
| stats[14] · diamond_ore | `weight` 2 |
| stats[15] · deepslate_diamond_ore | `weight` 2 |
| stats[16] · ancient_debris | `weight` 5 |
| stats[17] · anvil | `weight` 1 |
| stats[18] · smithing | `weight` 2 |
| stats[19] · enchants | `weight` 2 |
| stats[1] · far | `weight` 1, `per` 100 |
| stats[20] · brewing | `weight` 0.5 |
| stats[21] · advancements | `weight` 2 |
| stats[22] · villagers | `weight` 10 |
| stats[23] · iron_golems | `weight` 8 |
| stats[24] · traders | `weight` 8 |
| stats[25] · player_kills | `weight` 25 |
| stats[26] · raids_started | `weight` 3 |
| stats[2] · nether | `weight` 20 |
| stats[3] · end | `weight` 30 |
| stats[4] · mob_kills | `weight` 0.2 |
| stats[5] · ender_dragon | `weight` 120 |
| stats[6] · wither | `weight` 100 |
| stats[7] · warden | `weight` 100 |
| stats[8] · elder_guardian | `weight` 50 |
| stats[9] · evoker | `weight` 10 |
| tiers[0] · underdog | `min_score` 0, `offers` 2, `guaranteed` 0, `unique_choices` 1 |
| tiers[0] · underdog.weights | `common` 3, `rare` 1 |
| tiers[1] · normal | `min_score` 100, `min_days` 2, `offers` 3, `guaranteed` 0, `unique_choices` 1 |
| tiers[1] · normal.weights | `common` 1, `rare` 1 |
| tiers[2] · elite | `min_score` 600, `min_days` 7, `offers` 4, `guaranteed` 1, `unique_choices` 3 |
| tiers[2] · elite.weights | `common` 1, `rare` 2 |
| tiers[3] · legendary | `min_score` 1000, `min_days` 30, `min_bosses` 1, `offers` 5, `guaranteed` 2, `unique_choices` 3, `bonus_count` 1 |
| tiers[3] · legendary.weights | `common` 1, `rare` 4 |

</details>

<details>
<summary>landmarks.toml</summary>

[Source table](../../design/data/landmarks.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| landmark[0] · goblin_village | `reach` 48, `version` 1 |
| landmark[1] · lizardmen_village | `x` 700, `z` 344, `reach` 48, `version` 1 |
| landmark[2] · lizardmen_caverns | `reach` 56, `version` 1 |
| landmark[3] · orc_camp | `reach` 40, `version` 1 |
| landmark[4] · dwarf_village | `x` 250, `z` -740, `reach` 116, `version` 1 |
| landmark[5] · ogre_village_ruin | `reach` 24, `version` 1 |
| landmark[6] · treyni_grove | `reach` 48, `version` 1 |
| root | `keepout` 60 |

</details>

[mortal_banned.toml](../../design/data/mortal_banned.toml) contains no numeric entries.

<details>
<summary>nations.toml</summary>

[Source table](../../design/data/nations.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| diplomacy | `war_notice_hours` 24 |
| rank[0] · hamlet | `value` 0, `chunks` 0 |
| rank[1] · village | `value` 150, `chunks` 2 |
| rank[2] · town | `value` 400, `chunks` 4 |
| rank[3] · city | `value` 900, `chunks` 6 |
| rank[4] · kingdom | `value` 2000, `chunks` 8 |
| rules | `member_cap` 5, `min_members` 2, `name_min` 3, `name_max` 24, `home_rep` 10, `base_chunks` 4, `chunks_per_member` 10, `poll_ticks` 100, `value_ticks` 6000 |
| rules.charter_cost | `gold` 50 |
| upkeep.debuff | `weeks` 2 |
| upkeep.debuff.stage[0] · Neglect | `yield` 0.75, `nothing_chance` 0.05, `growth_skip` 0.25 |
| upkeep.debuff.stage[1] · Unrest | `yield` 0.5, `nothing_chance` 0.15, `growth_skip` 0.5 |
| value | `chunk_value` 1, `build_value` 10, `coins_per_value` 100 |

</details>

<details>
<summary>npcs.toml</summary>

[Source table](../../design/data/npcs.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| settings | `rev` 3, `check_ticks` 200, `start_delay_ticks` 200, `interact_cooldown_ms` 600 |
| spot[0] · fuze_blumund | `x` 107, `y` 11, `z` 61, `yaw` 90 |
| spot[10] · kaijin_tempest | `x` -26, `y` 0, `z` -12, `yaw` 90 |
| spot[11] · garm_tempest | `x` -28, `y` 0, `z` -24, `yaw` 0 |
| spot[12] · dold_tempest | `x` -24, `y` 0, `z` -24, `yaw` 0 |
| spot[13] · mildo_tempest | `x` -17, `y` 0, `z` 9, `yaw` 0 |
| spot[14] · outcast_road | `x` 0, `y` 64, `z` 52, `yaw` 180 |
| spot[15] · kabal_blumund | `x` 99, `y` 5, `z` 66, `yaw` 90 |
| spot[16] · elen_blumund | `x` 99, `y` 5, `z` 68, `yaw` 90 |
| spot[17] · gido_blumund | `x` 99, `y` 5, `z` 70, `yaw` 90 |
| spot[18] · kabal_tempest | `x` -5, `y` 0, `z` -16, `yaw` 0 |
| spot[19] · elen_tempest | `x` -3, `y` 0, `z` -16, `yaw` 0 |
| spot[1] · receptionist_blumund_1 | `x` 103, `y` 5, `z` 68, `yaw` 90 |
| spot[20] · gido_tempest | `x` -1, `y` 0, `z` -16, `yaw` 0 |
| spot[21] · treyni_shrine | `x` 20, `y` 5, `z` 16, `yaw` 90 |
| spot[22] · milim_forgotten_dragon_city | `x` 60, `y` 6, `z` 25, `yaw` 0 |
| spot[23] · yuuki_englassia | `x` 118, `y` 5, `z` 82, `yaw` 90 |
| spot[24] · edmaris_marris | `x` 68, `y` 6, `z` 11, `yaw` 0 |
| spot[25] · razen_marris | `x` 65, `y` 6, `z` 11, `yaw` 0 |
| spot[26] · folgen_marris | `x` 71, `y` 6, `z` 11, `yaw` 0 |
| spot[27] · kyoya_marris | `x` 64, `y` 5, `z` 15, `yaw` -90 |
| spot[28] · shogo_marris | `x` 72, `y` 5, `z` 15, `yaw` 90 |
| spot[29] · kirara_marris | `x` 64, `y` 5, `z` 19, `yaw` -90 |
| spot[2] · receptionist_blumund_2 | `x` 103, `y` 5, `z` 76, `yaw` 90 |
| spot[30] · hinata_lubelius | `x` 108, `y` 5, `z` 85, `yaw` 90 |
| spot[31] · luminous_lubelius | `x` 60, `y` 6, `z` 23, `yaw` 0 |
| spot[32] · carrion_laura | `x` 56, `y` 9, `z` 14, `yaw` 0 |
| spot[33] · frey_walpurgis | `x` 43, `y` 15, `z` 27, `yaw` 18 |
| spot[34] · guy_walpurgis | `x` 37, `y` 15, `z` 27, `yaw` -18 |
| spot[35] · leon_walpurgis | `x` 43, `y` 15, `z` 45, `yaw` 162 |
| spot[36] · dagruel_walpurgis | `x` 37, `y` 15, `z` 45, `yaw` -162 |
| spot[37] · ramiris_spirit_dwelling | `x` 50, `y` 41, `z` 44, `yaw` 90 |
| spot[3] · receptionist_tempest | `x` 3, `y` 0, `z` -16, `yaw` 0 |
| spot[4] · fuze_tempest | `x` 8, `y` 0, `z` -19, `yaw` 90 |
| spot[5] · benimaru_tempest | `x` -1, `y` 0, `z` -22, `yaw` 0 |
| spot[6] · shion_tempest | `x` 0, `y` 0, `z` -27, `yaw` 0 |
| spot[7] · shuna_tempest | `x` 22, `y` 0, `z` -8, `yaw` 90 |
| spot[8] · souei_tempest | `x` -29, `y` 10, `z` -43, `yaw` 0 |
| spot[9] · hakurou_tempest | `x` 2, `y` 0, `z` -5, `yaw` 135 |

</details>

<details>
<summary>skills.toml</summary>

[Source table](../../design/data/skills.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| absorb | `min_ep_ratio` 0.5, `max_ep_ratio` 0, `cooldown_hours` 72, `legendary_per_kill` 1, `copies_per_kill` 1, `offer_minutes` 5, `pact_minutes` 15, `combat_log_seconds` 30 |
| absorb.awakening | `min_ep_ratio` 0.5, `max_ep_ratio` 1.0 |
| absorb.liability | `max_blocks` 512, `restore_per_tick` 32, `hold_days` 7 |
| absorb.liability.fee_per_block | `bronze` 5 |
| absorb.liability.max_fee | `gold` 5 |
| absorb.war | `min_ep_ratio` 0 |
| caps | `legendary` 3, `rare` 3, `common` 5 |
| core.weights | `rare` 3, `common` 1 |
| legendary | `max_holders` 10, `slots_per_era` 0 |
| registry | `inactive_days` 30, `history_max` 200, `max_name_lookups` 20 |

</details>

<details>
<summary>story.toml</summary>

[Source table](../../design/data/story.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| act[0] · forest_awakens | `id` 1, `chapters` [1, 2, 7], `renown` 5 |
| act[1] · armed_nation | `id` 2, `chapters` [3, 8], `renown` 5 |
| act[1] · armed_nation.dark_rep | `dwargon` -20, `outcast` 10 |
| act[1] · armed_nation.light_rep | `dwargon` 15 |
| act[2] · orc_war | `id` 3, `chapters` [4, 9], `renown` 10 |
| act[2] · orc_war.dark_rep | `orc_horde` 40, `lizardmen` -20 |
| act[2] · orc_war.light_rep | `lizardmen` 20, `tempest` 10 |
| act[3] · calamity | `id` 4, `chapters` [10], `renown` 15 |
| act[3] · calamity.dark_rep | `outcast` 20 |
| act[3] · calamity.light_rep | `tempest` 15 |
| act[4] · holy_knight | `id` 5, `chapters` [11], `renown` 20 |
| act[4] · holy_knight.dark_rep | `tempest` -40, `falmuth` 30 |
| act[4] · holy_knight.light_rep | `holy_church` 10 |
| act[5] · walpurgis | `id` 6, `chapters` [12], `renown` 30 |
| act[5] · walpurgis.dark_rep | `outcast` 15, `orc_horde` 10 |
| act[5] · walpurgis.light_rep | `tempest` 10, `holy_church` 5 |
| act[6] · harvest_festival | `id` 7, `chapters` [13], `renown` 50 |
| act[6] · harvest_festival.dark_rep | `outcast` 20 |
| act[6] · harvest_festival.light_rep | `tempest` 10, `blumund` 10 |
| flag.demon_lord | `renown` 60 |
| flag.hero | `renown` 60 |
| flip | `max` 1 |
| flip.atonement.set | `tempest` 0 |
| flip.corruption.rep | `outcast` 10, `tempest` -10 |
| npc[0] · rigurd.talk[0] | `act` 1 |
| npc[0] · rigurd.talk[1] | `act` 2 |
| npc[0] · rigurd.talk[2] | `act` 2 |
| npc[10] · souei.talk[0] | `act` 1 |
| npc[10] · souei.talk[1] | `act` 2 |
| npc[10] · souei.talk[2] | `act` 2 |
| npc[11] · garm.talk[0] | `act` 1 |
| npc[11] · garm.talk[1] | `act` 2 |
| npc[12] · dold.talk[0] | `act` 1 |
| npc[12] · dold.talk[1] | `act` 2 |
| npc[13] · mildo.talk[0] | `act` 1 |
| npc[13] · mildo.talk[1] | `act` 2 |
| npc[14] · kabal.talk[0] | `act` 1 |
| npc[14] · kabal.talk[1] | `act` 5 |
| npc[15] · elen.talk[0] | `act` 1 |
| npc[15] · elen.talk[1] | `act` 5 |
| npc[16] · gido.talk[0] | `act` 1 |
| npc[16] · gido.talk[1] | `act` 5 |
| npc[17] · milim.talk[0] | `act` 1 |
| npc[17] · milim.talk[1] | `act` 2 |
| npc[17] · milim.talk[2] | `act` 2 |
| npc[17] · milim.talk[3] | `act` 4 |
| npc[17] · milim.talk[4] | `act` 4 |
| npc[18] · yuuki.talk[0] | `act` 1 |
| npc[18] · yuuki.talk[1] | `act` 5 |
| npc[18] · yuuki.talk[2] | `act` 5 |
| npc[19] · edmaris.talk[0] | `act` 1 |
| npc[19] · edmaris.talk[1] | `act` 5 |
| npc[19] · edmaris.talk[2] | `act` 5 |
| npc[1] · gobta.talk[0] | `act` 1 |
| npc[1] · gobta.talk[1] | `act` 2 |
| npc[1] · gobta.talk[2] | `act` 2 |
| npc[20] · razen.talk[0] | `act` 1 |
| npc[20] · razen.talk[1] | `act` 5 |
| npc[21] · frey.talk[0] | `act` 1 |
| npc[21] · frey.talk[1] | `act` 6 |
| npc[22] · guy.talk[0] | `act` 1 |
| npc[22] · guy.talk[1] | `act` 6 |
| npc[23] · leon.talk[0] | `act` 1 |
| npc[23] · leon.talk[1] | `act` 6 |
| npc[24] · dagruel.talk[0] | `act` 1 |
| npc[24] · dagruel.talk[1] | `act` 6 |
| npc[25] · ramiris.talk[0] | `act` 1 |
| npc[25] · ramiris.talk[1] | `act` 2 |
| npc[25] · ramiris.talk[2] | `act` 2 |
| npc[26] · hinata.talk[0] | `act` 1 |
| npc[26] · hinata.talk[1] | `act` 5 |
| npc[26] · hinata.talk[2] | `act` 5 |
| npc[27] · luminous.talk[0] | `act` 1 |
| npc[27] · luminous.talk[1] | `act` 6 |
| npc[27] · luminous.talk[2] | `act` 6 |
| npc[28] · carrion.talk[0] | `act` 1 |
| npc[28] · carrion.talk[1] | `act` 6 |
| npc[28] · carrion.talk[2] | `act` 6 |
| npc[29] · folgen.talk[0] | `act` 1 |
| npc[29] · folgen.talk[1] | `act` 5 |
| npc[2] · benimaru.talk[0] | `act` 1 |
| npc[2] · benimaru.talk[1] | `act` 2 |
| npc[2] · benimaru.talk[2] | `act` 2 |
| npc[30] · kyoya.talk[0] | `act` 1 |
| npc[30] · kyoya.talk[1] | `act` 5 |
| npc[30] · kyoya.talk[2] | `act` 5 |
| npc[31] · shogo.talk[0] | `act` 1 |
| npc[31] · shogo.talk[1] | `act` 5 |
| npc[32] · kirara.talk[0] | `act` 1 |
| npc[32] · kirara.talk[1] | `act` 5 |
| npc[3] · shuna.talk[0] | `act` 1 |
| npc[3] · shuna.talk[1] | `act` 2 |
| npc[3] · shuna.talk[2] | `act` 2 |
| npc[4] · shion.talk[0] | `act` 1 |
| npc[4] · shion.talk[1] | `act` 2 |
| npc[4] · shion.talk[2] | `act` 2 |
| npc[5] · hakurou.talk[0] | `act` 1 |
| npc[5] · hakurou.talk[1] | `act` 2 |
| npc[6] · kaijin.talk[0] | `act` 1 |
| npc[6] · kaijin.talk[1] | `act` 2 |
| npc[7] · treyni.talk[0] | `act` 1 |
| npc[7] · treyni.talk[1] | `act` 2 |
| npc[7] · treyni.talk[2] | `act` 2 |
| npc[8] · gazel.talk[0] | `act` 1 |
| npc[8] · gazel.talk[1] | `act` 2 |
| npc[8] · gazel.talk[2] | `act` 2 |
| npc[9] · outcast_contact.talk[0] | `act` 2 |
| npc[9] · outcast_contact.talk[1] | `act` 1 |
| oath.dark.rep | `outcast` 20, `orc_horde` 15, `tempest` -20 |
| oath.light.rep | `tempest` 20 |
| rules | `fight_near` 96, `log_size` 200 |

</details>

<details>
<summary>trials.toml</summary>

[Source table](../../design/data/trials.toml)

| Table or array entry | Current numeric settings |
| --- | --- |
| creation | `limit` 150 |
| deceit | `limit` 150, `radius` 7.5, `strikes` 3 |
| dominion | `limit` 180, `herd` 5, `needed` 3 |
| freedom | `limit` 150 |
| hunger | `limit` 90, `start_food` 4, `spiders` 2 |
| knowledge | `limit` 180, `pass_score` 4 |
| protection | `limit` 90, `every` 15, `raiders` 2 |
| strength | `limit` 180 |
| strength.waves[0][0][1] | 4 |
| strength.waves[1][0][1] | 3 |
| strength.waves[1][1][1] | 2 |
| strength.waves[2][0][1] | 3 |
| strength.waves[2][1][1] | 1 |
| strength.waves[3][0][1] | 2 |
| strength.waves[3][1][1] | 2 |
| survival | `limit` 120, `hazard_every` 8, `skeletons` 2 |
| vengeance | `limit` 120, `nemesis_health` 60 |

</details>
