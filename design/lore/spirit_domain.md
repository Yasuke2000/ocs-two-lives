# The gate to the Dwelling of the Spirits and the Dwelling itself (dimension `ttl:spirit_domain`)

Owner request (18/11/2026): "an entrance to the spirit domain", later decided to teleport into its own dimension.

Builds: `blueprints/spirit_gate.py` (57 x 40 x 57, overworld, `design/builds/spirit_gate.toml`, world about (1570, 1130), 275 blocks south-south-west of Tempest) and
`blueprints/spirit_dwelling.py` (89 x 64 x 89, `design/builds/spirit_dwelling.toml`, dimension `ttl:spirit_domain`, fixed y 64).
Entrance logic: `pack/kubejs/server_scripts/ttl/life/spirit_domain.js`. Test: `tests/ingame/spirit_domain.rcon`.

## Canon

- In the children's story, the entrance is in **Ulg Nature Park in the far north of the Republic of Ulgracia**. The official map names the park and the country in adjacent entries. Volume 4 and anime episodes 22–23 cover Rimuru's visit with Shizu’s pupils. Stills in episode 22 show a dark, stone-built chamber and Ramiris’s guardian. In episode 23 the children take turns at the pedestal, and Chloe receives a different kind of presence. [Official map, country](https://www.ten-sura.com/map/#A-72) · [Official map, park](https://www.ten-sura.com/map/#A-73) · [Episode 22](https://www.ten-sura.com/anime/tensura/story/no22) · [Episode 23](https://www.ten-sura.com/anime/tensura/story/no23)
- Ramiris later establishes a dungeon in Tempest. The pack gives Life 2 players access to its separate spirit dimension from the **Jura gateway at (1570, 1130)**, 275 blocks south-south-west of Tempest in the dark-forest band by the lake shore. That gameplay placement is recorded in the decision log. The canon grid also has a distinct “Galut / Ulgr Nature Park (Ulgracia)” landmark. [Ramiris chronology](https://ja.wikipedia.org/wiki/転生したらスライムだった件#ラミリス) · [Pack decisions](../decisions.md) · [Mapped landmarks](../../pack/config/ttl/canon_regions.json)

## What we built (our interpretation of appearance)

- **Gate (overworld):** a plaza of Tensura labyrinth stone ringed by five elemental plinths (fire red, water prismarine,
  wind green, earth sandstone, space purple: the elements of the spirits) in front of a mossy cliff; in the cliff a tall
  doorway with a pentagon-of-elements seal on its back wall. The doorway cells are the portal (box `PORTAL` in the
  blueprint, exported to `generated/spirit_gate.js`).
- **Dwelling (own dimension):** a floating glade (cherry trees, meadow, two ponds, the five plinths round the rim) with a
  dais of labyrinth stone, a broken colonnade, a glass lid over a shaft, and a stair down into the grotto: a dome with a
  summoning circle in the floor and, in the middle, a pedestal (a vanilla beacon on an iron base) whose light climbs through
  the shaft to the sky. The return arch is south of the arrival point. An invisible barrier runs along the island's rim.
- The trail's pale centreline is carved stone. Tensura 2.0.1.5's praying path runs a server-side block-entity tick for crouching players. Both structures use passive paving so the pack’s doorway script controls access. The grotto stair descends north and rises south to the glade.

## Dimension

`ttl:spirit_domain`: flat generator with no layers and its own biome `ttl:spirit_domain` (pale mist fog, soft sky, drifting
end-rod motes, no spawners, no features) so no Tensura or vanilla worldgen touches it; dimension type with skylight,
`fixed_time` 6000 (always daytime), `natural` false (no portals, no sleeping), `monster_spawn_light_level` 0. Not the Spirit
Corridor, which belongs to the Life 1 to 2 flow. Graves are off there (tombstone `no_grave_dimension`).

## Sources and references

- https://tensura.fandom.com/wiki/Dwelling_of_the_Elementals (via search extract), https://tensura.fandom.com/wiki/Elemental_Realm,
  https://tensura.fandom.com/wiki/Ramiris
- Visual references only: Tensura `labyrinth_tree` and `ruin/warp` structures, the mod `t_and_t` village `modded/waystones/waystone_default`
  (a gate-like shrine), Iron's Spells `ice_spider_den/cavern/cavern_extension/circle_henge`.
