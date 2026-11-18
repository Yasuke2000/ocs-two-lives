# The rings of Jura

**On your first trip, head northeast towards Dwargon.** You arrive on the outer edge of the Great Jura Forest in `minecraft:overworld`, near **X 271, Z -624**, already facing roughly towards the gate at **X 435, Z -1000**. The server looks for a clearing within 40 blocks of the arrival point. Tempest lies the other way, at **X 0, Z 0**, with much denser magicule country on the approach. [World map](world-map.md) · [Nederlands](../nl/jura-rings.md)

Ring widths, magicule levels and arrival protection may change.

## Reading the landscape

Veldora’s leaked magicules give the forest three bands. The rim follows Jura’s *outer border*. Only the core is measured outward from Tempest. A trip along the border can stay on the rim for a long time. Cutting across a bend can take you into the middle. Lake Siss, its marsh and the rivers inside Jura do not create another safe rim.

| Band | Where to expect it | What to look for |
| --- | --- | --- |
| Rim | About the first 280 blocks inside the outer border | Oak and birch forest, old-growth birch, flower forest, plains or swamp. These ordinary biomes have a nominal area magicule of 500. |
| Middle | Between the border belt and the central core | Mostly dark forest, nominally 2,000 area magicule, with pockets of ancient forest at 20,000. A change of biome can change the danger before you reach the core. |
| Core | Roughly a 200-block radius around Tempest | Primarily ancient forest, with some dark forest. A newly reborn soul can suffer magicule poisoning within seconds in ancient forest. |

The borders vary by roughly 50 blocks between terrain patches. Heights and water also affect biome selection. These figures describe the current pack’s nominal **area magicule**, an environmental value. Your own EP includes both your magicules and aura. It cannot be read as a universal safe-entry threshold. Terrain already generated on an older version can retain its original biome. [Region and biome settings](../../../pack/config/ttl/canon_regions.json) · [Jura geography](../../../design/lore/world.md)

## Surviving the road

- **At arrival**, use the current 20 seconds of grace to check your coordinates and find the road. Blade Tigers and Barghests can target and push you on the rim. Void damage and the kill command bypass grace. When grace ends, ordinary damage resumes.
- **While travelling**, mark the clearing and the Dwargon gate as waypoints. If you run into ancient forest or begin taking magicule damage, turn back along your approach towards the lighter forest at the border. A riverbank can lead deeper into Jura.
- **At Tempest**, the green within 56 blocks of **(0, 0)** shelters Life 2 players from magicule poison and suppresses natural hostile spawns. Creatures can walk into the green. The approach outside that small circle still crosses the core, and the green gives no general immunity to combat or curses.

These distances and timers can change with pack updates. If the arrival or forest behaves differently on your server, include your dimension, X/Z and the biome shown on the debug screen when reporting it. An operator can compare the saved arrival with `/ttl arrival` and the expected biome with `/ttlmap <x> <z>`. [Arrival settings](../../../design/data/arrival.toml) · [Life 2 protections](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Report a bug](report-bugs.md)
