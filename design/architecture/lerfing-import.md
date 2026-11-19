# Lerfing's Tensura map as the Life 2 overworld — import design

> Target path in the repo: `design/architecture/lerfing-import.md`. Design only (19/11/2026, Claude for Yasuke).
> Owner decisions of 19/11/2026 (final): import Lerfing's map 1:1 as `minecraft:overworld` of `world-ttl`; ocean ring,
> then normal vanilla generation (free roam, non-story quests); let Minecraft populate the proto chunks; repaint the
> Nether/End biomes to fitting overworld or Tensura biomes, blocks untouched; Tempest in the middle of Jura; Dwargon
> inside the Canaat mountain; everything lore-accurate; credit Lerfing and Paulzero. Earlier decisions still hold:
> Jura rings with the deadly core, the continent rule (R11), protected domains, sites per build (re-read in §2.3),
> the Life 2 arrival on a safe rim, night-only pregen.
>
> Map analysis used: `scratchpad/lerfing_extract/out/` (overview_labeled.png, identification.png, heightmap16.png,
> surface16.png, biomes.json/png, landmask.png, chunks_per_region.json, nonnatural_blocks.json, block_entities.json,
> crops/). Working renders made for this design: `scratchpad/lerfing-design/` (jura_height.png, canaat_height.png,
> ov_jura_centre.png, ov_west.png, ov_east.png, ov_south.png).

## 0. Facts the design rests on

| Fact | Value | Consequence |
| --- | --- | --- |
| Export | WorldPainter, every chunk DataVersion 2860 (1.18.0), 1,474,944 chunks in 1,470 region files, 9.40 GB on disk | DFU upgrade 1.18 → 1.21.1 (3955) on load; no `poi/`; `entities/` holds 15 files with 11 dropped items and 14 creepers only (not copied) |
| Inner tiles | x −8064..8192, z −6016..6528 = regions r.−16..15 × r.−12..12 = **800 files, 6.70 GB**, status `liquid_carvers` (proto chunks, "allow Minecraft to populate") | populate = ores (Tensura magic ore via biome modifiers), vegetation features, heightmaps, light, initial mobs |
| Outer border | 2,560 blocks of flat shallow sea (floor y 47–51), 670 files, 2.69 GB, status `full` | WorldPainter's automatic border, not part of the drawn map |
| Land | x −7400..7640, z −5540..5832 (15,040 × 11,372); water surface y 64, i.e. top water block y 64 (vanilla `sea_level` 63 tops water at y 62); peak y 316 at (2502, −1432) | a 1-block sea step at any seam unless our generator's `sea_level` becomes 65; world build limit 320 caps anything on the summit |
| Biomes on land | plains 10.1 % (almost all land), snowy_plains (Ice), badlands (Milim, El Dorado), desert (Damargania), **soul_sand_valley** 1.14 % (the grey Canaat), **nether_wastes** 0.30 % (red NE crater + patches in the SW crystal hills, bbox −3820..6268), **the_end** 0.71 % (grey-teal far west), jungle (SE peninsula), swamp (round Lake Siss), mushroom_fields (small, Canaat edges) | three Nether/End biomes to repaint offline; everything else stays |
| Nothing else | no structures, no Tensura blocks, no villages; 8,288 legacy banners (NE, dropped), 674 flower pots (dropped), 13 "built by Paulzero" signs (giant trees at ~ (610, 2930)), one chest at (−453, 73, 979) (Lerfing's spawn kit), Lerfing's own small builds: a lake village at Lake Siss (brown glass/oak fence, 2900..3600 × 400..1000), an ice structure on the water at (−1900, −4480), pots on the north islet | keep all of them (owner: 1:1); nothing of ours overlaps them |
| Status strings | 1.21.1 has no `liquid_carvers`; `ChunkStatus.byName` on an unknown name returns **EMPTY** → the chunk would be regenerated from scratch by our generator and Lerfing's terrain overwritten | the status MUST be rewritten offline to `minecraft:carvers` before the first boot (§1.2). This is the one step that cannot be done in game |
| Server | PVC `mc-data` **30 Gi** Longhorn (Homelab `apps/ocs-two-lives/manifests/server.yaml`), heap 7 G, pod limit 10 Gi, 2 CPU, DH 3.3.3 night pregen (~35 cps measured on fresh generation), BlueMap 5.7 in the game JVM | disk is the binding constraint (§1.4) |

## 1. Import pipeline

### 1.1 What to copy

**Copy the 800 inner-tile regions only** (6.70 GB, 796,544 chunks); drop the 670 flat border regions. The 800 files also
hold 22,656 `full` border chunks (the 8-chunk strip outside x −8064..8192, z −6016..6528); the tool drops those too, so
the output is exactly the 796,544 drawn chunks (6.59 GB).

Trade-off: the border is WorldPainter's automatic 2,560-block shallow shelf (floor 47–51), not Lerfing's drawing. Keeping it
costs 2.7 GB, 46 % of all chunks for DH/BlueMap to process, and still leaves a seam (shelf → our ocean) further out.
Dropping it moves the seam to the inner-tile edge, where Lerfing's painted sea is already deep ocean (floor y 19–26 probed at
(4100, 4100), (4400, 4400); biome `deep_ocean`, 29 % of the map), and our generator makes deep ocean there too
(`CanonGrid.canonContinents`: continentalness falls to −0.95 over 700 blocks beyond the land mask; the inner-tile edge is
476–696 blocks beyond the land bbox on every side). With the sea level matched (§2.1) the seam is an underwater floor
step of a few blocks, 500+ blocks from any coast. The import tool prints the floor histogram along the four inner edges
so the ring's `SEA_DROP` can be tuned if an edge turns out shallow (owner question Q2 if he wants the shelf kept anyway).

### 1.2 Offline pre-processing (workstation, Python, no server) — `tools/lerfing/import.py`

Input: the zip (`Tensura By Lerfing.zip`). Output: `<out>/region/` (800 files, `--out` outside the repo) + rasters for the repo. One pass per region,
chunk by chunk (the extractor's `nbt.py` reads; the tool adds a minimal NBT writer or uses `nbtlib`):

1. **Status**: `Status: "liquid_carvers"` → `"minecraft:carvers"` (every proto chunk). `full` stays `full`. Nothing else in the
   pipeline is skipped: `features` (populate), `initialize_light`, `light`, `spawn`, `full` still run on first load. Structure
   steps count as done → **no vanilla or Tensura structures generate inside the import** (no villages, temples, Tensura goblin
   or dwarf villages); our landmarks placer `/place`s the canon ones as today (Q5).
2. **Biome repaint** (per section palette, strings only; blocks untouched), rules in `design/data/lerfing/repaint.json`:

   | Stored biome | Where | New biome | Why |
   | --- | --- | --- | --- |
   | `minecraft:soul_sand_valley` | everywhere (= the grey Canaat massif) | `minecraft:stony_peaks` | high cold rock, no ghasts, no snow features, dragons/peaks mobs of Tensura |
   | `minecraft:nether_wastes` | inside x 3700..7700, z −3400..−1000 (the NE volcano) | `minecraft:badlands` | Velgrynd's scorching mountain: hot, red, no rain |
   | `minecraft:nether_wastes` | elsewhere (SW crystal hills) | `minecraft:windswept_gravelly_hills` | hills of Fulbrosia, no piglins |
   | `minecraft:the_end` | far west (x < −4900) | `tensura:barren_land` | canon Barren Lands; Tensura's own biome, allowed in our palettes |
   | `minecraft:mushroom_fields` | — | keep | harmless, vanilla |
   | land biomes inside Jura (J polygon) | ring test (§3.6) | core → `tensura:ancient_forest`, band → `minecraft:dark_forest`, rest keep | the owner's deadly core; water/beach/river cells are never repainted |

   Everything else keeps Lerfing's biome. The tool writes `design/data/lerfing/biomes16.png` after the repaint.
3. **Rasters for the repo** (1 px = 16 blocks, inner tiles, ~1,016 × 784 px): `landmask16.png` (land / lake-or-river / sea,
   open sea = water reached from the inner edge through water more than 64 blocks from land, plus 64 blocks of shore;
   every other water = `~`, so Lake Siss and the rivers are `~` although they drain to the sea), `heights16.png`
   (ground y + 64, 16-bit: the summit is y 316),
   `biomes16.png` (index + legend json). Small enough to commit (< 1.5 MB together); they feed `lerfing_grid.py`,
   `tools/lerfing/probe.py` and the unit tests, so nobody needs the 9 GB zip to work on anchors.
4. **Report** `<out>/report.json`: chunk/status counts before and after, biome counts after, the inner-edge floor histogram,
   the list of block entities kept. `tests/test_lerfing_import.py` runs the rewrite on a synthetic region and asserts the
   status and palette rewrites are byte-exact elsewhere.

Not done offline: the 1.18 → 1.21.1 DFU (`grass` → `short_grass`, sign `Text1..4` → `front_text`, `legacy:block_175`
→ air, …). It runs on the IO threads when a chunk loads, so it never blocks the server thread; the night pregen is where
it happens. Fallback if pregen shows DFU dominating: one boot with `EXTRA_ARGS="--forceUpgrade --eraseCache"` (vanilla
WorldUpgrader, all 796k chunks before the level opens, ~15–40 min on 2 CPU; raise the pod's startup probe for that boot).

### 1.3 On the server (the PVC) and the upgrade path to 1.21.1

- Files go where the overworld already lives: `/data/world-ttl/region/` (overworld terrain is the world folder itself;
  `WorldReset.move` shows which folders belong to it: `region`, `entities`, `poi`, `data/DistantHorizons*`).
- Upload: `tools/import_world.sh` (WP-L10) streams the 800 files (6.59 GB) into the running pod with tar over
  `kubectl exec`, in resumable batches, then checks the sha256 manifest on the pod. Measured on 19/11/2026: 8.3 MB/s,
  about 14 min. `/data/import` is not part of the world, so the server keeps running.
- The swap needs no scale to 0: the marker is read at server start, before the levels load, so the restart is the normal
  deploy (runbook §6.3). The mod gets a new marker `ttl-import.txt` (§2.4): like
  `ttl-reset.txt` it moves the old overworld (`region`, `entities`, `poi`, DH sqlite) to `ttl-backup/<time>/`, but then
  **moves `/data/import/region` into place instead of leaving the folder empty**, and triggers `/ttl worldreset
  minecraft:overworld` so the scripts re-place Tempest, Dwargon, landmarks, builds and the arrival and move players.
- Upgrade: lazy DFU + populate on first load (pregen, §5). The pack's `noise_settings/overworld.json` gets `sea_level: 65`
  so the generated ring matches the import (§2.1).

### 1.4 Disk budget (30 Gi today)

| Item | Estimate |
| --- | --- |
| Import after DFU + populate (ores, trees, heightmaps, light add 20–40 %) | 8–9.5 GB |
| DH LOD database for 16.3k × 12.5k blocks (old continent 14k × 10k was being built; the new one is ~1.5× the area) | 3–5 GB |
| BlueMap tiles, hires, 1.5× the old render mask | 3–6 GB |
| Mortal Realm, Spirit Corridor, Walpurgis, Spirit Domain, player data, logs | 1–3 GB |
| `ttl-backup/<time>/` of the current generated overworld (the November reset world + its pregen) | 3–6 GB until deleted |
| **Total** | **18–30 GB** |

Recommendation (Q1): grow `mc-data` to **60 Gi** (Longhorn expansion: edit the PVC in the Homelab manifest (PR #60, WP-L10),
ArgoCD syncs; Longhorn grows an attached volume online, else at the next attach), and move the old overworld backup to the NAS (Longhorn backup
target) before deleting `ttl-backup/<time>/` from the PVC. ttl-ops already pauses the pregen at 85 % disk.

### 1.5 Backup and rollback

- Before: the nightly 03:00 Longhorn snapshot and the 04:30 NAS backup of `mc-data` exist, and a manual one (Yasuke,
  Longhorn UI) is optional. No scale to 0: the marker is applied at the next start, and the restart's shutdown saves the
  world first.
- The marker keeps the old overworld in `ttl-backup/<time>/` (nothing deleted); the DH sqlite goes with it; BlueMap is purged.
- Rollback (WP-L10, `docs/server.md` "World import", "Rollback") uses the same marker. Revert the data commits (anchors,
  grid, `sea_level`) on `main` and keep ttl-portals 0.9.0; once that is deployed, move
  `ttl-backup/<time>/minecraft/overworld/{region,entities,poi}` to `/data/rollback` (a rename; the marker refuses a source
  inside `ttl-backup`), write `minecraft:overworld rollback <count>` and restart. Lerfing's map goes to a new
  `ttl-backup/<time>/`. No scale to 0 is needed. The old DH database only goes back by hand, with the server stopped. Like any import, the
  rollback runs `/ttl worldreset`, so players are moved to spawn when they log in (`world_reset.js` epoch).
- The runbook (§6.3) does the import at any time when nobody is online (owner, 19/11/2026: test as soon as possible). It
  does not delete `ttl-backup` until the bot tests are green and the owner has looked at the map. Only the pregen waits for
  the night.

## 2. Worldgen outside the import

### 2.1 What generates where

- **Inside the inner tiles**: nothing of ours. Chunks exist; `CanonMap`, `CanonBiomes`, `CanonSites` are never asked. The
  `features` step uses the **stored** section biomes (Lerfing's + our repaint), so Tensura's ores and plants come from biome
  modifiers as in any world. In-game biome lookups (magicule, spawns, `execute if biome`) read the stored biomes too.
- **The ocean ring**: beyond the inner tiles our generator runs. `CanonGrid` keeps working unchanged: the new `canon_map.txt`
  (§3.1) is Lerfing's land mask, `signed` distance from it drives `canonContinents` to −0.95 (deep ocean) over `FADE` 700
  blocks, held for `ring` blocks from the land bbox, then blended over `blend` into vanilla. Set **`ring = 2000`,
  `blend = 800`** (was 1600/800): the inner-tile edge is 476–696 blocks beyond the land bbox, so the generated ring is
  1,300–1,500 blocks of open sea on every side, and vanilla land can begin ~2,100–2,300 blocks from Lerfing's coast
  (a boat trip of a few minutes; the owner's "ocean ring, then vanilla"). Climate channels (`erosion`, `temperature`,
  `vegetation`) fade to vanilla over the sea as today (`SEA_CLIMATE` 300) — they no longer shape any land.
- **Sea level**: `pack/kubejs/data/minecraft/worldgen/noise_settings/overworld.json` `sea_level` 63 → **65**, so the generated
  ring's top water block is y 64 like the import's (a 1-block step would let a 7-block fringe of flowing water creep over the
  generated sea along the whole seam). Vanilla beaches/aquifers in the ring and the free lands simply sit one block higher.
- **Beyond the ring**: vanilla (TerraBlender regions where installed) as today; the free lands are never pregenerated.
- **Edge seams**: the generator never touches an existing chunk, and the chunk pipeline's neighbour requirements at the edge
  are satisfied by the imported chunks' statuses (`carvers` ≥ anything a new chunk needs from a neighbour), so no edge chunk is
  ever regenerated. The only visible seam is the sea-floor step at the inner-tile edge (§1.1).

### 2.2 CanonMap / CanonBiomes / sites

- `CanonMap` density functions: keep; they are the ring. `CanonBiomes`: keep; inside the grid's letters it still returns
  palette biomes, but it is never asked for imported columns; in the ring and beyond it returns vanilla/TerraBlender.
  Palettes, `replace_peaks`, `peaks` and the climate knobs of the 22 regions become documentation only; leave them in
  `canon_regions.json` (RegionTitles, `/ttlregion`, factions and nations keep reading `name`, `colour`, `banner_*`).
- **Sites are removed** (`"sites": []`). They only shape chunks that generate, and no canon build stands on a generated chunk
  any more. `CanonSites.NONE` is already the empty case; `CanonGrid` self-check and `tests/test_canon_sites.py` are replaced by
  the anchor tests of §3.9. Terrain fitting for a build is the placer's job (survey + fit + `repair.js`), as it already is.
- `/ttlmap x z` inside the import prints `imported chunk: stored biome <id>` when the chunk is loaded (else "imported, not
  loaded") instead of the generator's opinion; outside it works as today.
- `/ttlregion <player>` names the Jura ring from the **stored** biome's magicule class (ancient_forest = core, dark_forest =
  band, else rim) rather than the grid's ring maths, so what it says matches what hurts.

### 2.3 "Sites per build" (standing decision) re-read

The decision's intent — a build must stand in the biome and on the terrain its lore asks for — is now met by choosing the
spot on Lerfing's map (§3) and verifying it offline with `tools/lerfing/probe.py` (land, water share, relief, stored biome
at the anchor and the box corners) before the placer ever runs. The `sites` mechanism itself has nothing to shape. Where the
stored biome is wrong for a build (e.g. Clayman's Castle wants dark forest in Jistav's plains) the import tool's repaint rules
can add a per-build circle (`repaint.json` "spots": name, centre, radius, biome) — same data, same tool, applied offline.

### 2.4 Mod changes (ttl-portals 0.9.0)

- `WorldReset`: new marker `<world>/ttl-import.txt` with one line `minecraft:overworld <folder>` → back up as for a reset, then
  `Files.move(<world>/<folder>/region, <world>/region)` (and `entities`/`poi` if present), delete the marker, run
  `ttl worldreset minecraft:overworld` after start. Refuses (and keeps the marker) if the source folder is missing.
- `CanonMapCommand` (`/ttlmap`): the imported-chunk branch; `CanonGrid.main`: drop site checks, keep the zone/arrival checks
  on the new grid, add "every anchor of `design/data/anchors.toml` lies on a land cell" (reads the TOML through a tiny
  parser or a JSON the generator writes).
- No change to `CanonMap`/`CanonBiomes`/`CanonSiteTerrain` code; `sites` empty is already valid.
- Deploy order as for 0.8.3: release the mod from the branch before the data reaches `main` (the import marker is only
  used by ops, so the order is not load-bearing this time, but `sea_level` and the new grid go in the same pack commit).

## 3. Re-anchoring to Lerfing's coordinates

Decision taken from the analysis: **our data moves to his coordinates; the map is not shifted.** World (0, 0) stays Lerfing's
(0, 0): his spawn chest at (−453, 979), the Paulzero signs and every analysis coordinate stay valid, and the grid's origin
becomes trivial.

### 3.1 The new canon grid (`tools/lerfing_grid.py` → `canon_map.txt`)

- Cells = chunks of the inner tiles (1,016 × 784, origin cell = chunk (0, 0); header `# origin <col> <row>` as today).
- Cell class from `landmask16.png`: sea `.`, lake/river `~` (water that is not open sea, §1.2), land → a
  letter. The letter comes from **region polygons in world coordinates** (`canon_regions.json` → `lerfing.polygons`:
  `{"J": [[x, z], ...], ...}`); a land cell inside no polygon takes the nearest polygon's letter (so every land cell is
  owned and the continent rule is exactly the land mask, §4); islets likewise.
- Border dither, `TERRITORIAL_WATERS` (128 blocks of coastal water belong to the nearest nation), river weight and
  `signed` distance are computed by `CanonGrid` from this file exactly as today — no mod change.
- `canon_regions.json` loses `reference`, `width`, `paint_width`, `origin`, `paint`, `seeds` and `sites`; gains
  `"lerfing": {"inner": [-8064, -6016, 8192, 6528], "polygons": {...}}`; `landmarks[*].ref` → `landmarks[*].at: [x, z]`;
  `ring`/`blend` 2000/800; J `zones` become radius rings (§3.6). `tools/canon_map.py` (political-plate tracer) is retired.
- `tools/gen_data.py` `landmark_world()` (`(ref − origin) × width / 2570`) → returns `at`. `tools/gen_map.py` (BlueMap
  markers) reads `at` and the new grid for region labels.

Region polygons (approximate bounding outlines; WP-L2 traces them on `ov_*.png` and the land mask; nothing else depends
on their exact shape because builds carry explicit coordinates):

| Letter | Nation | Outline on Lerfing's map (x, z) | Why |
| --- | --- | --- | --- |
| J | Jura-Tempest | x −100..2350, z −400..2200: the forest-and-mesa land between the Blumund channel (x ≈ −200), the Canaat apron foot (z ≈ −250..−400) and Lake Siss's marsh | the Great Jura Forest, Veldora's ground |
| W | Lake Siss marsh | the swamp ring round the lake: x 2350..3950, z 290..1230 (Lerfing's `swamp`) | lizardmen's wetland |
| D | Dwargon | the grey massif and its apron: x 1000..3900, z −2400..−250 | Canaat Mountains, Dwargon inside |
| E | Eastern Empire | the NE landmass north of z −1000: x 3700..7700, z −3400..−1000, volcano included | far east, Velgrynd's mountain in the Empire |
| P | Jistav | x 5500..7700, z −1000..−300 | north-east of Milim's land, touching the Empire |
| M | Milim's Domain | the badlands x 3950..7700, z −1000..2700 minus P; the crescent ridge and the lakes | "forgotten dragon" plains fed by the Ameld |
| B | Eurazania | the SE jungle peninsula x 2200..4700, z 1250..5100 | tropical beast kingdom south of Jura |
| S | Sarion | the south-central peninsula x 0..1300, z 2150..3650 (Paulzero's giant trees) | Elmine, the capital in the Divine Tree, is a giant tree: Paulzero's grove is the only one on the map (Q3) |
| H | Fulbrosia | the SW crystal hills x −3700..−1600, z 950..2200 | harpies' mesas and stairs (Jia) (Q3) |
| U | Ulgracia | south of Blumund, x −1600..−100, z 600..2150 (woodland, Lerfing's spawn at (−456, 976)) | Ulgr Nature Park woodland |
| R | Blumund | x −1500..−100, z −300..600 | the small kingdom at Jura's door |
| G | Englassia | x −2600..−1500, z −650..500 | the big western kingdom, Lura at its centre |
| F | Falmuth | the north arm x −2600..−1300, z −2000..−650, plus the north islet (−1100..−500, −1800..−1300) | north-west of Jura, by the sea |
| L | Lubelius | the NW ridge and coast x −3300..−2600, z −1700..300 | Holy City at the foot of the Sacred Mountain ridge (peak y 187 at (−2976, −992)) |
| O, A, N, Y, Q | Morgdahl, Raja, Nostraille, Yuzalgh, Yggdonia | the river-and-lake belt between Englassia and the hills, z 500..1000, west → east: O −2600..−2250, A −2250..−1950, N −1950..−1650, Y −1650..−1500; Q north of the belt x −1500..−1300, z 0..500 | the five small western nations, one build each at most |
| V | Damargania | the desert x −5000..−2900, z −1500..1000 and the grey-teal Barren Lands west of it to x −7400 | Dagruel's Holy Void and the Barren Lands |
| I | Ice Continent | the island x −3850..2200, z −5540..−2800 | Guy's white ice palace |
| X | El Dorado | the south island x −4600..−1900, z 3400..5700 (volcano −2850, 4600) | Leon's golden city |

### 3.2 Tempest: the middle of Jura

Jura on Lerfing's map is open rolling grass dotted with forested mesas ("spires", gray terracotta tops y 130–200) and lakes;
dense tree cover is patchy. The scan of every 200 × 200 window inside x 600..1800, z 500..1500 (land, relief p10–p90,
water share, tree cover; `ov_jura_centre.png`, `jura_height.png`) gives one clear winner:

**Tempest arrival point (`TtlTempest.LANDMARK`) = (1720, 900)**, ground y ≈ 68, relief 7 over 200 × 200, water 11 % (the
lake at x 1500..1600, z 780..1000 just west: "running water nearby", LN vol. 2), trees 15 %, biome plains. 1,330 blocks
from Lake Siss (the lizardmen's lake is "far off" in the lore), the east-Jura massif (x 2000..2300, z 500..1000, y 250+)
as a backdrop to the east, the mesa field to the north-west for the Sealed Cave. Runner-up: (1620, 1460), relief 9,
460 blocks further south. The 192 × 192 growth square (town, city) fits inside the 200 × 200 window; the placer's fit and
repair handle the ±7 blocks.

Satellites (offsets kept from today's layout where the lore allows; `survey` = the placer's own search radius; every spot
re-checked by WP-L8 with `tools/lerfing/probe.py`):

| Place | New (x, z) | Offset from Tempest | Note |
| --- | --- | --- | --- |
| Sealed Cave (Veldora, Rimuru's birthplace) | (1380, 560), survey 128 | 480 NW | a mesa of the spire field (y 139–160): "a rocky hill in a forest clearing with the cave mouth in its south face"; the cave lies in the dark band (2,000 magicule): Veldora's leak |
| Old goblin village (Rigurd) | (1480, 720), survey 64 | 300 NW | between the lake and the cave, in the dark band |
| Spirit Gate | (1540, 1080), survey 64 | 250 SW | as today |
| Shizu quest spawn | (1300, 820), r 48 | 420 W | west of the lake, as today's (−400, −60) |
| Outcast contact (south road) | (1720, 952) | (0, +52) | tempest-relative, unchanged |
| Treyni's grove + shrine | (1920, 1540) / (1958, 1540) | 660 SE | east of the river that drains Jura's lakes (the choices-test river at (1500, 1500)); dryad half of the forest |
| Hidden ogre village ruin | (2150, 400), survey 64 | 650 NE | north foot of the east-Jura massif: "north-eastern hills" |
| Life 2 arrival (world spawn) | (1780, −150), yaw −161 | 1,050 N | on the road Tempest → Dwargon gate, 100–150 blocks inside Jura's border with the apron, relief 13, no water: the safe rim (§3.6) |
| Wayfarers' camp (sidequests) | (1795, −135) | arrival + (15, 15) | arrival-relative |

### 3.3 Dwargon inside the mountain

The Canaat massif is a 2,900 × 2,100 grey (`gray_concrete`/`gray_terracotta`) dome rising from y ~90 at z −250 to the
summit y 316 at (2502, −1432) with a lava lake at its top (x 2250..2500, z −1450..−1300, `canaat_height.png`). Its south
face is a long apron (~0.23 slope), not a cliff: a 92-high, 168-deep city cannot be buried by a single rise, so "inside"
means **the city body carved into the apron with the mountain closing over it**.

- **Gate (`TtlDwargon.GATE`) = (1900, −500)**, base y ≈ 136 (front probe spread 12, no water); the mountain behind rises to
  186–215 within the city's depth. The gate faces south, down the road to Tempest (1,400 blocks, straight north of it), as
  canon. Alternative with the same profile: (2600, −550), base 155 (further from Tempest; not preferred).
- **Blueprint** (`blueprints/dwargon.py`): the built-in sandstone massif stays (it closes the cavern where Lerfing's slope is
  lower than the ceiling, i.e. the north third), but its palette becomes the Canaat's: `BANDS` and the talus bands → stone,
  andesite, tuff, gray terracotta, gray concrete, light gray concrete powder (sampled from `nonnatural_blocks.json`); the
  white gate wall, towers and the road furniture keep their colours. A `MOUNTAIN_PALETTE` switch, one rebuild, version 7.
- **Placer** (`life/dwargon.js`): a `carve` mode = today's steps with two changes: (4) clear-above applies only to the
  blueprint's open-sky columns (the approach road, the queue lanes, the skylight crack) — on the apron that is a sunken road
  and a shaft, which is the point; everything the blueprint leaves undefined keeps Lerfing's rock, so the city is a cavern
  with the real mountain above and around it; (5) the fill under footprint columns and the 1:1 skirt use the grey bands.
  `repair.js` runs as today (caves/lava under the city filled; the summit lava lake is 1,000 blocks away).
- **Dwargo capital pin** (city centre) = (1900, −600); throne room = gate + (0, −106) = (1900, −606); Kaijin's smithy =
  gate + (−12, −84) = (1888, −584); checkpoint arch gate + (0, +40); plaza gate + (0, −66); all dwargon-relative data.
- **Dwarf village** (Tensura jigsaw, reach 116): (2000, −110), 150 blocks east of the road, on the apron foot (y 86, relief
  14, dry). **Dwarven Arena**: (2200, −80), survey 24, outside the village's keepout, in D.
  *Superseded 19/11/2026:* the arena belongs IN the village (owner); it is `beside` the village at (2100, −90), survey 48,
  against the village's real box (design/decisions.md 19/11 "Lerfing placements").
- **Dragon's Nest**: the summit shoulder **(2420, −1536)**, y 273, relief 6 over 90 × 90, 100 blocks north of the lava lake,
  under the 316 peak; the build is 46 high with its floor at layer 8 → top ≈ 311 < 320 (WP-L7 asserts this; the lava lake
  itself and the peak are left as Lerfing made them).
- **Great Ameld source** pin: (2500, −200) at the apron foot (the brook that feeds the Jura lakes is our reading);
  **mouth** pin: (4500, 2400) (Lerfing's river to the eastern sea).

### 3.4 Every other canon place (lore reading of the map)

Builds are placed by survey (`search`) at the given x/z; "pin" = a landmark on the map only. Heights/biomes from the probes.

| Item | Old (x, z) | New (x, z) | Why |
| --- | --- | --- | --- |
| Lake Siss (pin, Charybdis arena centre) | (888, 202) / arena (635, 145) | **(3050, 750)**, arena r 96 over the water | Lerfing's lake with its marsh ring; Lerfing's own lake village stands on its west shore |
| Lizardmen's stilt village | (700, 344) | (2900, 1020), surface water | SW shore, swamp (mangrove not present: `/place` skips the biome check) |
| Lizardmen's caverns | (926, 398) | (3300, 1150), survey 64 | south shore, inside the marsh |
| Orc camp / Orc War battlefield (Orc Lord + Orc Disaster spawns) | (1106, 539) | (3600, 1250), r 64 | south-east of the lake, where the marsh meets Eurazania's jungle: Geld's horde came up from the south |
| Blumund — Londo (Fuze, guild) | (−1024, −120) | (−450, 150), survey 128 | the small kingdom right at Jura's door, west of the channel |
| Ballachia | (−1384, −212) | (−1660, −460), survey 128 | on the eastbound road between Londo and Lura |
| Englassia — Lura | (−2626, −300) | (−2150, −410), survey 160 | centre of the western plain, flat, y 66 |
| Falmuth — Marris | (−1286, −1040) | (−2000, −1450), survey 128 | the north arm, north-west of Jura |
| Siltrosso | (−2026, −921) | (−2450, −1650), survey 96 | the arm's western tip, folded into F's neighbourhood as today |
| Lubelius — Lune | (−3977, −659) | (−2550, −700), survey 160 | east foot of the NW ridge |
| Sacred Mountain (Inner Sanctum) | (−4423, −1286) | (−2980, −900), survey 128, `max_wet` 0 | on the ridge (y 120–187), the only real mountain in the west |
| Coleus | (−4151, 370) | (−3080, 600), survey 64 | the Damargania border: desert edge, y 75 |
| Heaven Tower (Dagruel) | (−7507, 245) | (−4500, 560), survey 64 | deep in the desert, relief 8 |
| Morgdahl | (−4009, 1002) | (−2350, 750), survey 96 | west end of the river belt: a timber landing on the river |
| Raja | (−1084, 763) | (−2050, 760), survey 48, `repair_keep_water` | on the belt's lake, as its lore asks |
| Nostraille | (−2560, 360) | (−1780, 550), survey 48 | quiet hill kingdom east of Raja |
| Yuzalgh / Yggdonia / Filtwood / Ghastone / Rostia / Sainte Malukshure (pins) | various | (−1580, 650) / (−1400, 300) / (−900, 700) / (−2000, 300) / (−2100, 1000) / (−2500, 1300) | map labels only |
| Ulgr Nature Park (Galut) | (−1171, 2152) | (−1040, 1060), survey 64 | Ulgracia's woodland south of Blumund |
| Elmine (Sarion, the Divine Tree) | (−1471, 1629) | (900, 2700), survey 128, `beside` Paulzero's tree box | the terrace beside the giant tree at (610, 2930) (Q3) |
| Jia (Fulbrosia, harpies) | (349, 1819) | (−2700, 1500), survey 160, terrain kept | a mesa of the crystal hills (Q3) |
| Laura (Eurazania) | (1689, 1302) | (3300, 2600), survey 256 | heart of the jungle peninsula |
| City of the Forgotten Dragon (Milim) | (2340, 905) | (4680, 840), survey 128 | the lake-and-river plain of the badlands, relief 6 |
| Clayman's Castle (Walpurgis gate inside) | (3693, −959) | (5620, −900), survey 160 + repaint spot dark_forest r 180 | Jistav, east of the volcano, flat |
| Amrita (Jistav capital) | (3552, −703) | (6100, −650), survey 128 | Jistav's plain |
| Nasca (Eastern Empire) | (2631, −2059) | (5100, −2680), survey 96 | the valley north of the volcano, relief 2 |
| Great Holy Mountain (Velgrynd's sanctuary) | (2386, −2511) | (5120, −1860), survey 64 | NW flank of the red crater (y 110); the crater lake and lava stay |
| El Dorado (Leon) | (−4808, 3240) | (−3300, 4300), survey 160 | the green plain NW of the island's volcano (peak 221 at (−2858, 4672)); volcano pin (−2850, 4600) |
| Frost Palace (Guy Crimson) | (−2435, −4314) | (−1850, −4250), survey 160, `surface` any | the shore beside Lerfing's white-concrete ice structure on the water at (−1900, −4480): his palace, our causeway |
| Dwargon gate / Dwargo / main gate pins | (435, −1000) / (419, −1661) / (436, −1487) | (1900, −500) / (1900, −600) / (1900, −500) | §3.3 |
| Dragon's Nest | (370, −2402) | (2420, −1536) | §3.3 |
| Test hut, Walpurgis Hall, Spirit Dwelling, Mortal builds | unchanged | unchanged | other dimensions |

### 3.5 Data-driven translations (so this never has to be done by hand again)

- **Anchor table** `design/data/anchors.toml`, written by `gen_data.py` from the sources of truth (`tempest`, `dwargon`,
  `arrival` from `world.toml [anchors]` — `TtlTempest.LANDMARK` and `TtlDwargon.GATE` move out of the scripts into data —
  plus every build's and landmark's x/z) → `generated/anchors.js` (`TtlAnchors`) and `tests/anchors.env`.
- **NPC spots**: already `anchor = build|tempest|dwargon`; the one `world` spot (`outcast_road`) and the five sidequest
  `world` places become `anchor = "tempest"` / `"arrival"` with offsets.
- **Bosses**: `spawn.at` already accepts `landmark`/`build`; the five fixed spawns become `landmark = "orc_camp"` (Orc Lord,
  Orc Disaster), `{ anchor = "dwargon", dx = 0, dz = −106 }` (Gazel statue), `{ anchor = "tempest", dx = −420, dz = −80 }`
  (Shizu), `{ x = 3050, z = 750 }` (Charybdis; a lake is nobody's build). `gen_data.check_arena` learns `anchor + dx/dz`.
- **Artifice** smithy `{ anchor = "dwargon", dx = −12, dz = −84 }`.
- **Quests**: `gen_quests.py` location tasks accept `at = { anchor = "tempest", dx = 0, dz = −7 }`, `{ landmark = "…" }`,
  `{ build = "…" }` besides `[x, z]`; the ~60 overworld location tasks of chapters 1–13 and 20–23 are rewritten that way
  (their comments already state the derivation). `quest_graph.py --check` stays the gate.
- **Tests**: `tools/server.sh test` substitutes `${anchor:tempest.x}`-style tokens from `tests/anchors.env` before sending a
  line; rcon files use tokens instead of numbers (list in §3.9).
- **BlueMap markers**: `gen_map.py` from `landmarks[*].at`; the Tensura map's `render-mask` becomes the inner tiles.
- **Docs**: `design/lore/world.md` (region table, landmarks), `tempest.md` (distances table), `dwargon.md` (the owner's
  "inside the mountain" replaces the 19/11 "on a plain" override), `docs/server.md` ("Site biomes" → "Lerfing's map"),
  `CREDITS.md`.

### 3.6 The Jura rings on his forest

Still meaningful: weak souls must not stroll to Tempest, and the deadly core is an owner decision. But Jura is now a
2,400 × 2,600 open landscape and a depth-based "middle" ring would paint `dark_forest` over nearly all of it and plant dark
oak everywhere at populate time. Proposal (Q4): rings by **radius from Tempest only** — core r 200 ± 50 `tensura:ancient_forest`
(20,000 magicule; labyrinth trees), a dark band r 200..600 ± 50 `minecraft:dark_forest` (2,000), everything else = Lerfing's
own biome (safe, 500). Water, beach and river cells are never repainted. The band holds the goblin village, the Sealed Cave
(Veldora's leak, fitting) and the Spirit Gate; the arrival (1,050 N), Treyni (660 SE) and the dwarf village are outside it.
The repaint is done offline by the import tool from the same `zones` entry (a value-noise wobble of ±50 replaces the mod's
seeded patch jitter); `J.zones` in `canon_regions.json` keeps the geometry for `/ttlregion` and the arrival self-check.

### 3.7 Domains, NPCs, arenas, gates

- **Domains** (`factions.toml`) are capital/build/landmark-relative already; only the nominal `domain.center` gen_data writes
  changes with the anchors. The Tempest domain's 192 × 192 square fits the window.
- **NPC spots**: see §3.5. The Tempest residents are blueprint-relative.
- **Arenas**: Walpurgis (own dimension), Labyrinth (Tensura dimension), Dwarven (build-relative): unchanged. The Walpurgis
  gate is a cell box of Clayman's Castle: moves with it.
- **Spirit Gate / Dwelling**: the gate build moves (§3.2); the Dwelling is its own dimension.
- **Mortal Realm**: untouched (`ttl:mortal_realm`, `MortalWorldgen`), Life 1 unchanged.
- **Nations**: a home region comes from the letter under the founder; unchanged logic.

### 3.8 Full item table (summary of §3.2–3.7)

| Item | Old | New | Why / rule |
| --- | --- | --- | --- |
| World origin | fan-map origin cell | Lerfing's (0, 0) | re-anchor data, not the map |
| `canon_map.txt` | 876 × 633 traced plate | 1,016 × 784 from land mask + polygons | §3.1 |
| `canon_regions.json` landmarks | `ref` pixels | `at` world coords (§3.4) | §3.5 |
| `sites` | 43 | none | §2.2 |
| `ring` / `blend` | 1600 / 800 | 2000 / 800 | §2.1 |
| `sea_level` | 63 | 65 | §2.1 |
| Tempest | (0, 0) | (1720, 900) | §3.2 |
| Dwargon gate | (435, −1000) | (1900, −500) | §3.3 |
| Arrival | (271, −624) | (1780, −150), yaw −161 | §3.2 |
| 28 overworld builds | §3.4 old column | §3.4 new column | lore reading |
| 7 landmarks | old | §3.2–3.4 | lore reading |
| Boss spawns (5) | fixed | anchored | §3.5 |
| NPC `world` spots (1 + 5) | fixed | tempest/arrival-relative | §3.5 |
| Quest location tasks (~60) | fixed | anchored | §3.5 |
| rcon tests (§3.9) | fixed | `${anchor:…}` tokens | §3.5 |
| BlueMap markers + mask | ref-derived, 14k mask | `at`, inner tiles | §3.5 |
| J zones | core r 200 + rim depth 280 + middle | core r 200, band r 600, rest keep | §3.6 |
| `TtlWorld.onContinent` | grid letter ≠ 0 | same test, grid = land mask | §4 |

### 3.9 Tests with fixed overworld coordinates

| Test | Today | Change |
| --- | --- | --- |
| `world.rcon` | continent 0 0 yes; 435 −1106 yes; 9000 0 no; 0 9000 no | `${anchor:tempest}` yes; `${anchor:dwargon.throne}` yes; 9000 0 and 0 9000 stay (flat sea, outside); add a coast check 200 blocks off Jura's south coast = no |
| `wild.rcon` | tp 9000 120 0 (outside), 600 120 600 | keep 9000; 600 600 is Jura land (y 81) → keep |
| `bosses.rcon` | Gazel throne 435 −1106; tp 600 120 600; summon shizu 500 70 500 | throne token; 500 500 is a Jura pond (water) → `${anchor:tempest}` + offset |
| `nations.rcon` | 100 100 / 300 100 | both in the Blumund channel (water) → tempest-relative dry spots |
| `guild_npcs.rcon` | Fuze's stand −984..−975, −168..−158; Tempest 3..8, −19..−16 | `${anchor:blumund}` + offsets (the stand is build-relative in npcs.toml already), tempest offsets |
| `domains.rcon` | forceload −16 −48 47 (Tempest box) | tempest tokens |
| `sidequests.rcon` | rim camp 285 −612 | arrival token |
| `builds.rcon` / `build_repair.rcon` | 2496..2520 in `ttl:spirit_corridor` (test hut) | unchanged (other dimension) |
| `artifice.rcon`, `necro_legion.rcon` | sky platforms at 4100/4400 "outside the continent" | still deep ocean, > 128 from any coast: unchanged |
| `choices.rcon` | platform 1500 150 1500 "on the continent" | now a Jura river cell (`~` → owner J): still inside; comment updated |
| `arrival.rcon`, `tempest_pass2.rcon`, `landmarks.rcon`, `story.rcon` | use `/ttl arrival`, `/ttl build where` | unchanged |
| `tests/test_canon_sites.py` | sites cover builds | replaced by `tests/test_lerfing_anchors.py`: every build/landmark/anchor on a land cell of the grid, not in water on `landmask16.png`, inside its faction's region letter, ≥ keepout from each other, Dragon's Nest top < 320 |

## 4. The continent rule

`TtlWorld.onContinent(dim, x, z)` keeps its implementation: `CanonMap.grid().ownerCell(x, z) !== 0`, cached per chunk column,
plus `world.toml [continent] inside_dimensions`. What changes is the grid: every land cell of the inner tiles carries a letter,
lakes and rivers are `~` (nearest nation), coastal water within 128 blocks belongs to the nearest nation, open sea is 0. So
"on the continent" now means **on Lerfing's land (or its lakes, rivers and 128 blocks of coast)** — the Ice Continent and El
Dorado included (they are canon land), the sea between them and the mainland excluded (free roam by boat). The channel
between Blumund and Jura (~200 wide) reads inside near both shores and outside in its middle 50 blocks — acceptable (R11 is
about the free lands, not a strait). No script changes: every consumer (`boss.js`, `guards.js`, `domains.js`, `necro.js`,
`roads.js`, `sidequests/places.js`, `events/director.js regionAt`, `rep.js regionAt/factionAt`) reads the letter.

## 5. Risks

| Risk | Where | Mitigation |
| --- | --- | --- |
| **Unknown status → EMPTY → terrain regenerated** | first load of any proto chunk | offline status rename (§1.2); the import tool refuses to write a region that still contains `liquid_carvers`; the runbook's first check after boot: `/ttlmap` at three imported spots says "imported chunk" and `verify` that a known Lerfing block (the spawn chest at (−453, 73, 979)) is still there |
| Memory and IO during population | DFU allocation churn + features + light per chunk on 7 G heap, 2 CPU; the IO-worker `CompoundTag.write` spin seen on 19/11 | populate only during the night pregen (DH `INTERNAL_SERVER`, `BALANCED`); ttl-ops stops on a crash or at 85 % disk; watch `neoforge tps` and pod RSS the first night; if GC thrashes, `PREGEN_THREADS` 2 and heap 8 G (pod limit 10 Gi allows it) |
| Watchdog on fresh terrain | placers waiting for FULL chunks; an imported chunk needs populate + light to reach FULL | `life/chunk_hold.js` tickets (no synchronous forceload) already; 600-chunk areas took 7.5 s/100 chunks on generation, populate is cheaper; nothing of ours runs `forceload add` on first boot |
| Populate changes the look | `dark_forest`/`jungle`/`forest` cells get vanilla trees on top of Lerfing's; Jura's band gets dark oak; the core gets labyrinth trees | accepted for the Jura rings (owner decision, Q4); jungle/forest are Lerfing's own intent; plains (10 % of the map) only get grass and the rare tree |
| Sea-level seam | 1-block water step along 4 × 16k blocks of seam | `sea_level` 65 (§2.1); the tool prints the edge histogram |
| BlueMap render size | 1.5× the old mask; the first full render takes hours in the game JVM at 1 thread | purge + `force-update` on the import day; render mask = inner tiles; `min-inhabited-time` 0 so pregen'd chunks render; watch tiles size |
| DH | a fresh LOD db for 1.5× the area; clients keep stale LODs of the old terrain | move the server sqlite with the backup (marker does it); tell players to clear the DH client cache for the server (known from the 19/11 reset) |
| Pregen of the outer ring | the ring is generated, not imported: deep ocean, cheap; the vanilla free lands beyond must NOT be pregenerated | `PREGEN_X=64, PREGEN_Z=256, PREGEN_RADIUS=520` chunks (covers the inner tiles; the square's corners are ring sea); ~1.0 M chunks; at 60–100 cps (populate, not generation) 3–5 h → one or two nights |
| Disk | §1.4 | PVC 60 Gi (Q1), backup to NAS, delete `ttl-backup` after sign-off |
| No structures inside the import | no Tensura wild villages, no vanilla structures (treasure maps, trial chambers) on the continent | Q5; the free lands have them |
| Lost decoration | 8,288 legacy banners (NE), 674 pots dropped by DFU; `legacy:block_175` (1,041 double-plant halves) → air | cosmetic; noted in CREDITS/lore |
| Dragon's Nest over the limit | summit 316, limit 320 | shoulder at y 273 (§3.3), unit test |
| A build's stored biome contradicts its lore | e.g. Clayman wants dark forest | repaint spots (§2.3) |
| Lerfing's own builds collide with ours | Lake Siss village, ice structure, Paulzero tree, north islet | keepouts: the placer's survey + `beside` for Elmine/Frost Palace; `test_lerfing_anchors.py` checks distance to the three recorded boxes |

## 6. Work packages

Owned files only; cross-package touch points are reserved, guarded lines. ≤ ~70 min each. Bot tests named per package.
Wave A is offline and parallel; B needs A's anchor table; C needs B; D is the night.

| WP | Wave | What | Owned files | Done when |
| --- | --- | --- | --- | --- |
| **WP-L1 Import tool** | A | `tools/lerfing/import.py` (status rename, repaint from `repaint.json` + J rings, inner tiles only, rasters, report, sha256 manifest, `--verify`); `tools/lerfing/probe.py x z [half]` (land/water/height/biome/relief from the rasters, or exact columns with `--world`/`--zip`); NBT reader/writer | `tools/lerfing/{import,probe,nbt,common}.py`, `design/data/lerfing/{repaint.json,landmask16.png,heights16.png,biomes16.png,legend.json}`, `tests/test_lerfing_import.py` | unit test green on a synthetic region; a real run on the zip reports 796,544 chunks, 0 × `liquid_carvers`, 0 × nether/end biomes; rasters committed |
| **WP-L2 Grid and regions** | A | `tools/lerfing_grid.py` (land mask + polygons → `canon_map.txt`); `canon_regions.json` rewrite (lerfing block, polygons of §3.1, `at` landmarks, no sites, ring 2000, J radius zones); `gen_data.py` landmark/anchor table + `anchors.toml`; `gen_map.py` on `at`; `tests/test_lerfing_anchors.py` replaces `test_canon_sites.py` | `tools/lerfing_grid.py`, `pack/config/ttl/canon_map.txt`, `pack/config/ttl/canon_regions.json`, `tools/gen_data.py` (anchor section), `tools/gen_map.py`, `design/data/anchors.toml` (generated), `tests/test_lerfing_anchors.py`, `tools/canon_map.py` (deleted) | `validate.py` passes; `CanonGrid` self-check passes on the new grid with the arrival; every landmark on land; the BlueMap conf regenerated |
| **WP-L3 Mod 0.9.0** | A | `ttl-import.txt` marker in `WorldReset`; `/ttlmap` imported branch; `/ttlregion` from stored biome; `CanonGrid.main` anchor checks; `sea_level` 65 in the pack's noise settings | `mod/.../WorldReset.java`, `CanonMapCommand.java`, `RegionTitles.java`/`CanonGrid.java` (main), `pack/kubejs/data/minecraft/worldgen/noise_settings/overworld.json`, `tools/release_mod.py` run | `gradlew build`; self-check; released as mod-v0.9.0 before the pack commit |
| **WP-L7 Dwargon in the mountain** | A (blueprint) / B (placer) | `dwargon.py` grey palette switch, version 7; `dwargon.js` carve mode + bands from data; Dragon's Nest height assert; lore `dwargon.md` | `blueprints/dwargon.py`, `blueprints/_dwargon_lib.py`, `pack/kubejs/server_scripts/ttl/life/dwargon.js`, `design/lore/dwargon.md`, `tests/ingame/builds.rcon` (dwargon cells) | structures rebuilt; `builds.rcon` dwargon cells green on staging after the import; `verify_build.py dwargon --min 98` |
| **WP-L4 Data re-anchoring** | B | `world.toml [anchors]` (tempest, dwargon, arrival) read by `tempest.js`/`dwargon.js`/`arrival.toml`; new x/z in all 28 build TOMLs and `landmarks.toml`; NPC and sidequest world spots; `bosses.toml` anchored spawns; `artifice.toml` smithy; `gen_data` anchor syntax for `check_arena`; `generated/anchors.js` | `design/data/{world,arrival,landmarks,npcs,sidequests,bosses,artifice}.toml`, `design/builds/*.toml` (x/z/search/beside only), `tools/gen_data.py` (anchor syntax), `generated/*` regenerated, `life/tempest.js` + `life/dwargon.js` (read the anchor: two lines) | `validate.py`, unit tests, `test_lerfing_anchors.py` green; every spot probed with `tools/lerfing/probe.py` (land, water < max_wet, relief noted in the TOML `notes`) |
| **WP-L5 Quests** | B | `gen_quests.py` anchor syntax; rewrite the overworld location tasks of chapters 1–13, 20–23; comments updated | `tools/gen_quests.py`, `design/quests/*.toml`, FTB SNBT regenerated, `tests/test_story_chapters_*.py` | `quest_graph.py --check`: 21 chapters, 304 quests; `quests.rcon` sections 1–7 green after the import |
| **WP-L8 Jura placement and lore** | B | the Tempest/Sealed Cave/goblin village/Spirit Gate/arrival/Treyni/ogre ruin coordinates verified with the probe and the 1:1 crops; `world.md` region table, `tempest.md`, `sealed_cave.md`, `spirit_domain.md`; `CREDITS.md` (Lerfing's map, Paulzero's giant trees, Lerfing's lake village and ice structure); `decisions.md` rows; `roadmap-public.md` | `design/lore/*.md`, `CREDITS.md`, `design/decisions.md`, `docs/roadmap-public.md` | lore files cite the probes; `post_roadmap.sh` run by the owner |
| **WP-L6 Tests and server.sh** | C | `${anchor:…}` substitution in `tools/server.sh test`; `tests/anchors.env` written by gen_data; rcon files of §3.9 updated; `world.rcon` coast check | `tools/server.sh`, `tests/anchors.env`, `tests/ingame/{world,wild,bosses,nations,guild_npcs,domains,sidequests,choices}.rcon` | `test-all` = 0 failing on staging after the import night |
| **WP-L10 Ops docs and BlueMap** | C | `docs/server.md` (import runbook, "Lerfing's map" section replacing "Site biomes", pregen numbers), `docs/HANDOFF.md`, `pack/config/bluemap/maps/tensura.conf` (mask, markers via gen_map), Homelab PR (PVC 60 Gi, `PREGEN_X/Z/RADIUS`) | `docs/server.md`, `docs/HANDOFF.md`, `pack/config/bluemap/maps/tensura.conf`, Homelab `apps/ocs-two-lives/manifests/{server,ops}.yaml` | PR merged; ArgoCD synced; `bluemap` shows the new mask |
| **WP-L9 The import night** | D | run §6.3; verify; bot tests; owner look | staging world, `docs/HANDOFF.md` entry, `decisions.md` row | runbook ticked, `test-all` 0 failing, map rendering, pregen started |

### 6.1 Reserved lines (one each, guarded with `typeof`)

`life/tempest.js` and `life/dwargon.js` read `TtlData.world.anchors` (WP-L4); `life/world_reset.js` logs the import epoch
(WP-L3's marker reuses `/ttl worldreset`, no script change); `tools/server.sh` token pass (WP-L6).

### 6.2 Order on `main`

L1, L2, L3 (mod released first), L7-blueprint → one merge; L4, L5, L8, L7-placer → one merge (data + structures regenerated
together, `validate.py`, `--check` generators); L6, L10 → merge; then L9 (any time nobody is online). ttl-ops deploys `main` only when
nobody is online. The import is a manual step on top (`tools/import_world.sh` and a deploy restart, §6.3). It needs nobody
online, but not a night and not a stopped server (WP-L10).

### 6.3 Import runbook (lead, in this order; any time nobody is online — WP-L10)

The import is pre-made terrain, so it no longer waits for a night. Only the pregen stays night-only (owner rule).
The step-by-step version, with the log lines, is `docs/server.md` "World import".

1. Offline: `python -I tools/lerfing/import.py "<zip>" --out <dir>`, then `… --out <dir> --verify`. Check
   `<dir>/report.json` (796,544 chunks, statuses, biomes, edge histogram) and commit the rasters. Run
   `python tools/validate.py` and `python -m unittest discover -s tests`.
2. `main` is ready: mod-v0.9.0 is released and `main` carries it with the Lerfing grid, `sea_level` 65 and the anchor
   table (L1–L8 merged, §6.2). ttl-ops deploys it when nobody is online.
3. Disk: merge the Homelab PR (PVC 60 Gi, pregen `64 256 520`) and confirm `df -h /data` shows the new size. 30 Gi holds
   the upload (about 90 % used afterwards), but no pregen runs above 85 %.
4. `bash tools/import_world.sh --dry-run`, then `bash tools/import_world.sh`. The script refuses while anyone is online,
   checks the free space, uploads to `/data/import/region` (resumable), checks sha256 on the pod, writes
   `minecraft:overworld import 800` to `/data/world-ttl/ttl-import.txt` (only if `main` is ready) and removes
   `/data/ttl-pregen.done`. The server keeps running throughout.
5. Restart with the normal deploy: `bash tools/server.sh deploy` (or ttl-ops' own deploy of a new `main`). No scale to 0
   and no debug pod. The nightly Longhorn snapshot plus `ttl-backup/<time>/` are the safety net.
6. The log must show `[ttl] world import: source OK: 800 region files (6.59 GB), 796544 chunks; …`, then
   `[ttl] world import: minecraft:overworld from import; old terrain in ttl-backup/<time> (moved); …`, then
   `[ttl] arrival grounded at 1780 … −150`, `[ttl] tempest placed`, `[ttl] dwargon placed`, the 7 landmarks and the 28 builds
   (`[ttl] chunks: holding …` lines, no watchdog). First checks: `ttlmap 1720 900` = imported chunk;
   `execute in minecraft:overworld if block -453 73 979 minecraft:chest` = Lerfing's spawn chest is still there (proof that
   no proto chunk was regenerated); `/ttl world expect continent 1720 900 yes`, `… 9000 0 no`.
7. `bluemap purge tensura`, `bluemap force-update tensura`; `/ttl build list` and `/ttl landmark list` show everything
   placed; `verify_build.py <name> --log --min 98` for dwargon, tempest and a sample of six builds (one per quadrant);
   `MSYS2_ARG_CONV_EXCL=/data bash tools/server.sh test-all` = 0 failing.
8. Players can test at once: chunks are populated on first load. The pregen (`64 256 520`: every imported tile plus the
   ring north and south) is run only by ttl-ops at night, 23:00–07:00, with nobody online and the disk under 85 %.
9. The owner looks at https://map.daviddelporte.com. Then delete `ttl-backup/<time>/` from the PVC (the NAS backup
   keeps it). Rollback, if he does not want it: `docs/server.md` "World import", "Rollback".
10. `docs/HANDOFF.md`, `decisions.md`, `roadmap-public.md`.

## 7. Open questions for the owner (with recommendations)

| # | Question | Recommendation |
| --- | --- | --- |
| Q1 | Grow the `mc-data` PVC from 30 Gi to 60 Gi (Longhorn, node3 disk)? Without it the import + DH + BlueMap + the old-world backup do not fit (§1.4). | **Yes, 60 Gi**, and keep the old overworld only on the NAS. |
| Q2 | Import the inner tiles only (6.7 GB, Lerfing's drawing) and let our generator make the sea beyond, or also the 2,560-block WorldPainter shelf (+2.7 GB, +46 % chunks)? | **Inner tiles only** (§1.1). |
| Q3 | Sarion ↔ Fulbrosia: put Sarion (Elmine, "the capital in the Divine Tree") on the south-central peninsula with Paulzero's giant trees, and Fulbrosia (harpy mesas, Jia's mountain stair) in the SW crystal hills — the reverse of our old grid. | **Swap**: the giant tree is the one literal Divine Tree on the map; the crystal hills are the only mesa country in the south-west. |
| Q4 | Jura rings by radius only (core 200, dark band to 600, the rest Lerfing's open forest) instead of a depth-based middle that would turn all of Jura into dark forest at populate time. | **Radius rings** (§3.6); the deadly core stays as decided. |
| Q5 | No structures generate inside the import (status past `structure_starts`): no Tensura wild goblin/dwarf/orc villages, no vanilla structures on the continent; the free lands beyond the ring keep them. Accept, or add a one-off `/place` pass of a handful of Tensura villages in lore-fitting spots? | **Accept** for the import; a later data-driven `landmarks.toml` extension can add villages where quests want them. |

Everything else in this document is a design decision inside the owner's decisions of 19/11/2026 and goes into
`design/decisions.md` as rows when WP-L8 lands.

---
**Owner decisions 19/11/2026 (Yasuke) — all recommendations accepted:** Q1 PVC 30 → 60 Gi; Q2 import only the inner tiles
(drop WorldPainter's 2,560-block border); Q3 swap Sarion ↔ Fulbrosia so Paulzero's giant tree is the Divine Tree (Elmine);
Q4 Jura rings by radius around Tempest (core r 200 ancient_forest, dark band r 200..600, rest Lerfing's biomes);
Q5 no vanilla/Tensura structures inside the import (only our builds/landmarks). Earlier today: populate on first load;
repaint Nether/End biomes; Tempest in the middle of Jura; Dwargon INSIDE the mountain.
