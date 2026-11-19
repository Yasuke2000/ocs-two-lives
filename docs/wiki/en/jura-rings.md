# The rings of Jura

**On your first trip, head north towards Dwargon.** You arrive on the northern edge of the Great Jura Forest in `minecraft:overworld`, near **X 1780, Z -150**, already facing towards the gate at **X 1900, Z -500**, about 370 blocks away. The server looks for a clearing within 40 blocks of the arrival point. Tempest lies the other way, about 1,050 blocks south at **X 1720, Z 900**, with much denser magicule country on the approach. [World map](world-map.md) · [Nederlands](../nl/jura-rings.md)

Ring widths, magicule levels and arrival protection may change.

## Reading the landscape

Veldora’s leaked magicules give the forest three bands, all measured in rings outward from Tempest. Going north, south, west or east you cross the same distances. Lerfing’s map is open country with patches of forest, so the bands follow the distance from Tempest, not the thickness of the trees. Lakes, beaches and rivers are never repainted: the ground beside them still has the danger of its band.

| Band | Where to expect it | What to look for |
| --- | --- | --- |
| Rim | More than about 600 blocks from Tempest, which includes the arrival | Whatever Lerfing’s map grows there: plains, oak and birch forest, flower forest or swamp. These ordinary biomes have a nominal area magicule of 500. |
| Middle | About 200 to 600 blocks from Tempest | Dark forest, nominally 2,000 area magicule. The old goblin village, the Sealed Cave and the Spirit Gate lie in this band. A change of biome can change the danger before you reach the core. |
| Core | Roughly a 200-block radius around Tempest | Ancient forest, nominally 20,000 area magicule. A newly reborn soul can suffer magicule poisoning within seconds in ancient forest. |

The borders wobble by roughly 50 blocks. The rings were painted onto Lerfing’s map once, when the world was imported, so they do not move. These figures describe the current pack’s nominal **area magicule**, an environmental value. Your own EP includes both your magicules and aura. It cannot be read as a universal safe-entry threshold. [Region and biome settings](../../../pack/config/ttl/canon_regions.json) · [Jura geography](../../../design/lore/world.md)

## Surviving the road

- **At arrival**, use the current 20 seconds of grace to check your coordinates and find the road. Blade Tigers and Barghests can target and push you on the rim. Void damage and the kill command bypass grace. When grace ends, ordinary damage resumes.
- **While travelling**, mark the clearing and the Dwargon gate as waypoints. If you run into ancient forest or begin taking magicule damage, turn back along your approach, away from Tempest, towards the lighter country outside the dark band. A riverbank can lead deeper into Jura.
- **At Tempest**, the green within 56 blocks of **(1720, 900)** shelters Life 2 players from magicule poison and suppresses natural hostile spawns. Creatures can walk into the green. The approach outside that small circle still crosses the core, and the green gives no general immunity to combat or curses.

These distances and timers can change with pack updates. If the arrival or forest behaves differently on your server, include your dimension, X/Z and the biome shown on the debug screen when reporting it. An operator can compare the saved arrival with `/ttl arrival` and the expected biome with `/ttlmap <x> <z>`. [Arrival settings](../../../design/data/arrival.toml) · [Life 2 protections](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Report a bug](report-bugs.md)
