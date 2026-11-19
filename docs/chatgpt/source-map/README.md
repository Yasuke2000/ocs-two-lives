# Source map: the current world as reference

These are **reference renders of the current Life 2 world**, *Tensura by Lerfing* (purchased by Yasuke; the licence allows use on
servers; see [CREDITS.md](../../../CREDITS.md)). They exist so the **new, fully own world map** can be drawn with the right
geography relations: which land lies where, how big it is, where the mountains, rivers, lakes, deserts and islands are.
**Do not copy the drawing.** The new map must be original; take the relations (see [world.md](../world.md)), not the coastline.

Licensing: the map's world, region and zip files are paid content and are **not in this repository** and must never be added.
Only these downsampled renders are (JPEG). Credit line wherever they are shown: **Map: Tensura by Lerfing (current, being replaced).**

## Scale and origin (all renders except the two links at the end)

- Source: top-down renders of the whole export, **1 pixel = 4 blocks** in the full-size files (`overview.jpg`, `surface16.jpg`, `heightmap16.jpg`: 5376 x 4480 px).
- Pixel (0, 0) is the north-west corner at block **x = −10752, z = −8704**. Pixel to block: `x = −10752 + 4 * px`, `z = −8704 + 4 * py`.
  So world (0, 0) is at pixel (2688, 2176). **x grows east (right), z grows south (down); north is up.**
- Sea level is y 64 (sea surface); the highest point is y 316 (Canaat summit at about (2502, −1432)).
- The whole land is about 15,000 x 11,400 blocks. Lerfing's drawn area is x −8064..8192, z −6016..6528; the rest of the frame is open sea that our generator makes.
- Grid lines on the labelled images are every 1,000 blocks; the yellow lines are x = 0 and z = 0.

## The files

| File | Size | What it shows |
|---|---|---|
| [`overview.jpg`](overview.jpg) | 5376 x 4480 (1 px = 4 blocks) | The plain top-down colour render of the whole map: land, biomes, lakes, rivers, sea. The best picture for reading the geography. |
| [`overview_labeled.jpg`](overview_labeled.jpg) | 5516 x 4620 | The same render with a 70-pixel frame (so add about 70 px to every pixel coordinate) holding axis labels in blocks, a 1,000-block grid, and the slightly darker rectangle of Lerfing's own exported area (x −8064..8192, z −6016..6528). Use it to read coordinates. |
| [`identification.jpg`](identification.jpg) | 2062 x 1587 (1 px = 8 blocks) | An early, **half-size annotated render** made while we worked out which land is which nation. Red dots are features really in the map (Lake Siss, the Great Ameld, the El Dorado volcano, the north islet, the spawn); yellow dots are **our early guesses** of canon names. **The yellow labels are outdated** (for example it puts Tempest at (−250, 450); the canon places now are in [world.md](../world.md)). Trust the geography, not the labels. |
| [`surface16.jpg`](surface16.jpg) | 5376 x 4480 | Grey-scale **surface height**: the top non-leaf block, water at its water level. Brightness `v = ((y + 14) / 330) ^ 0.55 * 255`. The sea surface (y 64) is a flat grey of about 115; anything brighter is above sea level; the Canaat massif is the brightest. Good for seeing mountains versus plains. |
| [`heightmap16.jpg`](heightmap16.jpg) | 5376 x 4480 | Grey-scale **terrain floor** (the ground under water too, like the ocean floor), same brightness formula. Shows the sea shelf, river beds and lake floors. |
| [`crops/ice_panes.jpg`](crops/ice_panes.jpg) | 400 x 450, 1 px = 1 block | x −2100..−1700, z −4700..−4250: ice crystals of white concrete and glass on the Ice Continent's south shore (Lerfing's own build). |
| [`crops/jura_spires.jpg`](crops/jura_spires.jpg) | 600 x 500, 1:1 | x 900..1500, z 1200..1700: the forested rock spires (mesas with grey terracotta tops) of Jura's south. |
| [`crops/lake_east.jpg`](crops/lake_east.jpg) | 700 x 600, 1:1 | x 2900..3600, z 400..1000: the west shore of Lake Siss with Lerfing's stilt-hut village. |
| [`crops/ne_crater.jpg`](crops/ne_crater.jpg) | 950 x 750, 1:1 | x 4700..5650, z −2100..−1350: the red crater volcano of the Eastern Empire (Velgrynd's mountain). |
| [`crops/north_islet.jpg`](crops/north_islet.jpg) | 600 x 500, 1:1 | x −1100..−500, z −1800..−1300: the north islet with Lerfing's small builds. |
| [`crops/paulzero.jpg`](crops/paulzero.jpg) | 700 x 550, 1:1 | x 350..1050, z 2600..3150: Paulzero's giant trees in the south (Sarion's Divine Tree in our reading). |
| [`crops/spawn_test.jpg`](crops/spawn_test.jpg) | 400 x 400, 1:1 | x −656..−256, z 776..1176: Lerfing's spawn area (a lake with a spawn chest) west of Jura. |
| [`crops/volcano_objs.jpg`](crops/volcano_objs.jpg), [`volcano_obj_zoom.jpg`](crops/volcano_obj_zoom.jpg) | 800 x 600 / 600 x 420, 1:1 | x 1500..1900, z −1100..−800 and x 1730..1830, z −930..−860: small man-made objects Lerfing placed on the Canaat massif, west of its centre. |

Crops are 1 pixel per block; the box in each row is its world rectangle (x0..x1, z0..z1).

## Two renders that were already in the repository

These are not copied here; they are linked.

- [`docs/previews/lerfing_regions.png`](../../previews/lerfing_regions.png): the **nations and anchors atlas** (2392 x 1568; 1 px = 2 chunks = 32 blocks in the map area, a legend on the right). Each grid letter has its colour (J Jura green, D Dwargon grey, M Milim tan, ...), thin black lines are the region polygons, red dots are the 58 canon places of [world.md](../world.md), the white circles round Tempest are the Jura rings (r 200 and r 600). This is the best single picture of *which land is which nation*.
- [`docs/previews/jura_check.png`](../../previews/jura_check.png): a **close-up of Jura's rings** round Tempest (804 x 804, radius 800 blocks, 40,000 samples). Dark green is the deadly core (ancient forest), mid green the dark-forest band, light green the safe rim, yellow beach and sand, blue lakes, grey stony land; the red dot is Tempest, the white circles r 200 and r 600. It shows how the lake shore (sand) breaks the core.

Also useful: [`docs/previews/canon_map.png`](../../previews/canon_map.png) (the 1-px-per-chunk grid the game uses for nation borders).

## How to read the continent (a short guide to the pictures)

- **Middle**: Jura (green, forested mesas and lakes), with the grey **Canaat dome** directly north of it; the grey dome's orange patch is the lava lake.
- **North-east**: the Eastern Empire's landmass with the red crater (the dark red ring with lava).
- **East**: Lake Siss (the blue lake with branches) and the huge red-orange badlands of Milim's Domain, with the dark crescent ridge.
- **South-east**: the long jungle peninsula (Eurazania) pointing south. **South**: the stubby peninsula with the giant trees (Sarion).
- **West**: the big green plain (Blumund, Englassia and the small nations), the sandy **desert** (Damargania, light yellow) and the grey-teal **Barren Lands** at the far west edge. The Falmuth arm and the **north islet** lie in the north-west.
- **Islands**: the white **Ice Continent** far north (with a river running to its south shore) and the **El Dorado** island (with its volcano) to the south-west.
