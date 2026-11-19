# The rings of Jura

**On your first trip, head north to Dwargon.** You arrive on the northern rim of Jura in `minecraft:overworld`, near **X 1660, Z −100**, on the road between the dwarven kingdom and Tempest. Dwargon’s white gate stands about 500 blocks north-north-east at **X 1900, Z −500**. Tempest lies the other way, at **X 1720, Z 900**, with much denser magicule country on the approach. [World map](world-map.md) · [Nederlands](../nl/jura-rings.md)

Ring widths, magicule levels and arrival protection may change.

## Reading the landscape

Veldora’s leaked magicules give Jura three rings. The rings are measured **outward from Tempest** and follow the biome, so the biome under your feet (press F3) tells you the danger better than the distance does.

| Ring | Where to expect it | What to look for |
| --- | --- | --- |
| Rim | More than about 650 blocks from Tempest: the open plains and woods of Jura | Ordinary biomes such as plains and forest, with a nominal area magicule of 500. The arrival is here. |
| Band | Roughly 200 to 600 blocks from Tempest | Dark forest, nominally 2,000 area magicule. The old goblin village, the Sealed Cave and the Spirit Gate are in it. |
| Core | Roughly 200 blocks round Tempest | Ancient forest, nominally 20,000 area magicule. A newly reborn soul can suffer magicule poison within seconds. |

Each edge wobbles by about 50 blocks. Rivers, lakes and their sandy shores keep their own ordinary biome, also inside the rings, so the danger follows the biome you stand in. Heights and water also change what you see. These figures describe the current pack’s nominal **area magicule**, an environmental value. Your own EP includes both your magicules and aura. It cannot be read as a universal safe-entry threshold. [Ring settings](../../../design/data/lerfing/repaint.json) · [Jura geography](../../../design/lore/world.md)

## Surviving the road

- **At arrival**, use the current 20 seconds of grace to check your coordinates and find the road. Blade Tigers and Barghests can target and push you on the rim, and the stony foot of the Canaat just east of the arrival has its own mountain creatures. Void damage and the kill command bypass grace. When grace ends, ordinary damage resumes.
- **While travelling**, mark the Dwargon gate as a waypoint. If you run into dark forest and begin to feel the air thicken, or take magicule damage in ancient forest, turn back along your approach towards the plains. A riverbank can lead deeper into Jura.
- **At Tempest**, the green within 56 blocks of **(1720, 900)** shelters Life 2 players from magicule poison and suppresses natural hostile spawns. Creatures can walk into the green. The approach outside that small circle still crosses the core, and the green gives no general immunity to combat or curses.

These distances and timers can change with pack updates. If the arrival or forest behaves differently on your server, include your dimension, X/Z and the biome shown on the debug screen when reporting it. An operator can compare the saved arrival with `/ttl arrival` and the expected biome with `/ttlmap <x> <z>`. [Arrival settings](../../../design/data/arrival.toml) · [Life 2 protections](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Report a bug](report-bugs.md)
