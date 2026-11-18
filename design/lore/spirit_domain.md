# The gate to the Dwelling of the Spirits and the Dwelling itself (dimension `ttl:spirit_domain`)

Owner request (18/11/2026): "an entrance to the spirit domain", later decided to teleport into its own dimension.

Builds: `blueprints/spirit_gate.py` (57 x 40 x 57, overworld, `design/builds/spirit_gate.toml`, world about (-210, 130)) and
`blueprints/spirit_dwelling.py` (89 x 64 x 89, `design/builds/spirit_dwelling.toml`, dimension `ttl:spirit_domain`, fixed y 64).
Entrance logic: `pack/kubejs/server_scripts/ttl/life/spirit_domain.js`. Test: `tests/ingame/spirit_domain.rcon`.

## Canon

- The Dwelling of the Spirits (Dwelling of the Elementals) is a labyrinth connected to the Elemental Realm, where fairies and
  elementals live; Ramiris's Unique Skill Small World created it. Light novel volume 4, chapter 50.
- Rimuru takes Shizu's former pupils there to stabilise their energy: in the deepest part the children stand on a pedestal
  bathed in light and call spirits (Kenya becomes the host of an elemental of light; Chloe's case is different). The anime
  shows a magical cavern like Veldora's cave.
- Ramiris's labyrinth ("the Dungeon") is in Tempest's territory in the Great Jura Forest; the dryads later live in it.
- **Where on the map: canon gives no coordinate.** Our interpretation: a gate in the Jura forest about 250 blocks
  south-west of Tempest (between Tempest and Blumund), well away from the Sealed Cave.

## What we built (our interpretation of appearance)

- **Gate (overworld):** a plaza of Tensura labyrinth stone ringed by five elemental plinths (fire red, water prismarine,
  wind green, earth sandstone, space purple: the elements of the spirits) in front of a mossy cliff; in the cliff a tall
  doorway with a pentagon-of-elements seal on its back wall. The doorway cells are the portal (box `PORTAL` in the
  blueprint, exported to `generated/spirit_gate.js`).
- **Dwelling (own dimension):** a floating glade (cherry trees, meadow, two ponds, the five plinths round the rim) with a
  dais of labyrinth stone, a broken colonnade, a glass lid over a shaft, and a stair down into the grotto: a dome with a
  summoning circle in the floor and, in the middle, a pedestal (a vanilla beacon on an iron base) whose light climbs through
  the shaft to the sky. The return arch is south of the arrival point. An invisible barrier runs along the island's rim.
- No Tensura warp pad or labyrinth portal block is used (they run mod logic); `tensura:labyrinth_bricks`, `labyrinth_stone`,
  `cream_labyrinth_bricks` and `labyrinth_praying_path` are used as plain decoration. *Unverified in game:* that these four
  have no side effects, and how the beacon behaves in a void dimension.

## Dimension

`ttl:spirit_domain`: flat generator with no layers and its own biome `ttl:spirit_domain` (pale mist fog, soft sky, drifting
end-rod motes, no spawners, no features) so no Tensura or vanilla worldgen touches it; dimension type with skylight,
`fixed_time` 6000 (always daytime), `natural` false (no portals, no sleeping), `monster_spawn_light_level` 0. Not the Spirit
Corridor, which belongs to the Life 1 to 2 flow. Graves are off there (tombstone `no_grave_dimension`).

## Sources and references

- https://tensura.fandom.com/wiki/Dwelling_of_the_Elementals (via search extract), https://tensura.fandom.com/wiki/Elemental_Realm,
  https://tensura.fandom.com/wiki/Ramiris
- Visual references only: Tensura `labyrinth_tree` and `ruin/warp` structures, the mod `t_and_t` village `modded/waystone_*`
  (a gate-like shrine), Iron's Spells `ice_spider_den/cavern/circle_henge`.
