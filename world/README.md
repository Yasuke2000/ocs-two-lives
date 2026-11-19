# world/ — the own world map

`world/map.svg` is the single source of the new, fully own Tensura world (design: [own-world.md](../design/architecture/own-world.md),
sections 2 and 6.1). ChatGPT draws it, `tools/world/map_check.py` validates it, a converter later turns it into rasters.
This branch contains a **draft research-driven redraw**, with all 58 footprint-sized sites, authored coasts,
relief, waters, habitats and roads. [Numbered atlas](atlas.png), [checker preview](preview.png),
[reference comparison](comparison.md), [evidence ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv)
and [deliberate differences](regions.md).

The owner explicitly approved exactly five data-rule corrections to the default geography matrix.
The **standard map checker passes** with two disclosed warnings; source coverage and proportional fidelity
remain under review. The local terrain build is staged only: no Minecraft chunks, pack apply or server
changes are claimed. `canon-relations-anime.toml` records the adopted proposal as history; the technical
source of truth is `tools/world/canon_relations.toml`. See [review.md](review.md).

## Format in short

- Block coordinates. `viewBox="-8000 -6000 16000 12000"` is only the canvas (the converter crops to the content plus
  1,200 blocks of sea). World (0, 0) = Tempest, x east, y south (y = Minecraft z).
- Plain SVG: no `transform`, no nested groups, polygons closed (`<polygon>` or a `<path>` ending in `Z`) with 8 to 400
  vertices and no self-crossing; paths use `M L H V C Q Z` only (curves are flattened). Attributes are `data-*`.
- Exactly these `<g id="...">` groups (a missing `labels` only warns):

| group | element | attributes (required in bold) |
| --- | --- | --- |
| `coast` | closed polygon per landmass | `data-name` |
| `lakes` | closed polygon | `data-level`, `data-depth` |
| `rivers` | polyline source to mouth | **`data-width`** 4..24, `data-head`, `data-mouth` |
| `mountains` | closed polygon, optional `<polyline class="ridge">` inside | **`data-peak`** 100..300, `data-shape` alpine/mesa/dome, `data-rugged` 0..1 |
| `hills` | closed polygon | **`data-height`** 70..150, `data-shape` rolling/mesa, `data-rugged` |
| `forests` | closed polygon | **`data-type`**: light dense dark ancient birch taiga old_taiga jungle sparse_jungle cherry mangrove |
| `biomes` | closed polygon | **`data-biome`** from [`tools/world/biomes.txt`](../tools/world/biomes.txt) |
| `regions` | closed polygon, all land, no overlap | **`data-letter`** from `pack/config/ttl/canon_regions.json` |
| `roads` | polyline site to site | **`data-kind`** main/trail, `data-id`, `data-margin` |
| `sites` | one `<circle>` per anchor id (58) | **`data-id`**, **`data-site`**, **`r`** 8..160, `data-margin` |
| `labels` | text | cosmetic, ignored |

Site kinds (`data-site`): `clearing` (flat plate; pins and spots are clearing with r 8), `plateau` (terrace in a slope),
`carve` (inside a mountain or hill polygon), `lakeside` (touches a lake or river), `coast` (touches the sea), `village`
(a Tensura landmark's clearing, r at least the landmark's `reach` in `design/data/landmarks.toml`).

`data-margin` is the exclusion margin round a site disc or road corridor in which no structure start is allowed (owner
answer Q4: all structures may generate, except in site boxes, on road corridors and in the Dwargon cavity). Without it the
checker warns.

### Site size and spacing (what the checker enforces)

- **Size**: a site is as large as its build needs. Draw `r` at least the site's `min_r` from [`site_sizes.md`](site_sizes.md)
  (generated from `world/sites.toml`; pins and spots are 8). A smaller circle is enlarged by the converter and the checker
  warns per site ("drawn too small, will be enlarged to N"). The effective radius is `r_eff = max(drawn r, min_r)`.
- **Spacing**: `edge gap = distance - (r_eff1 + r_eff2)` must be **at least the larger of the two sites' `data-margin`**
  (default 48). Example: Tempest (r_eff 148) and the Sealed Cave (r_eff 75) at 424 blocks: gap 201, fine. Anchors placed
  relative to another one (`of`/`dx`/`dz` in `design/data/anchors.toml`, e.g. Dwargo, the throne and the smithy round Dwargon)
  are one place with their parent and siblings and are exempt from this rule.
- **Relative anchors**: draw them at parent + (`dx`, `dz`) (the scripts keep the offsets), at most 32 blocks off; the
  checker warns beyond that. The distance in the report is from the parent's circle centre as drawn.
- Without `world/sites.toml` the checker falls back to the drawn `r`.

## Run the checker

```
python -I tools/world/map_check.py world/map.svg                   # report, exit 1 on errors
python -I tools/world/map_check.py world/map.svg --preview world/preview.png   # plus a PNG, 1 px = 8 blocks
python -I tools/world/map_check.py world/map.svg --json            # the report as JSON (counts, bbox, design box, distances)
python -I tools/world/map_check.py world/map.svg --jar <tensura-neoforge-2.0.1.5.jar>   # also verify the tensura: biome ids
```

Standard library only. `tools/validate.py` (and so `tools/check.sh`) runs it on `world/map.svg`. `--jar` (or the
environment variable `TTL_TENSURA_JAR`) checks every `tensura:` id of `biomes.txt` against `data/tensura/worldgen/biome/`
in the jar; vanilla ids cannot be checked offline. `preview.png` is a review aid, do not commit it unless asked.

## Build the rasters

```
python -I tools/world/build.py            # map_check, then the generator rasters, a preview, the sites and the anchors'
                                          # x/z/y, all into world/build/ (nothing live changes)
python -I tools/world/build.py --apply    # the switch: pack/config/ttl/world/ + design/data/anchors.toml
```

`world/build/preview.png` shows the rasters as the generator will see them (hillshade, biomes, water, roads, the
structure exclusion hatched, site radii); the formats are in own-world.md section 3.8. `world/sites.toml` (Claude's,
generated by `tools/world/sites_from_builds.py` from the build footprints) says how large each site must be: a circle
drawn smaller than its build's `min_r` is enlarged and listed as a warning, so redraw it. `world/site_sizes.md` is the
same table for readers (id, kind, min_r).

## Reading the report

- **ERRORS** each start with the rule in brackets and name the element (`layer <tag> #index (id)`) and the point. The
  rules: `structure` (viewBox, groups, transforms, nesting), `polygon` (closed, 8..400 vertices, simple, inside the
  viewBox), `attribute` (ranges and lists), `water` (lakes, rivers, mountains and hills on land), `region` (every land
  sample in exactly one region, one polygon per letter per landmass), `site`, `road`, `canon`, `size`.
- **WARNINGS** do not fail the run: a site drawn below its `min_r`, a relative anchor more than 32 blocks from parent +
  offset, mountain crossed by a river, sites or roads without `data-margin`, build sites more
  than 400 blocks from a road, no ancient or dark forest round Tempest (r 600), mainland above 10,000 x 7,500, design box
  above 12,288 x 10,240.
- **STATS**: land and lake area, coast length, the design box (content plus 1,200 sea, rounded to 512; cap 14,336 x 11,264),
  mainland size, road lengths and bridges, shape counts per layer.
- **DISTANCES** from Tempest to every site (block distance and compass wind).
- **CANON RELATIONS** are in [`tools/world/canon_relations.toml`](../tools/world/canon_relations.toml): "a is N of b, min..max
  blocks" (each cited to a lore file), `[[site_rule]]` (inside a mountain, east of x 3000, a lake 400 wide ...) and
  `[[gap]]` (sea between landmasses). A failure prints the relation, the actual distance and bearing, and the source.

## Notes and limits

- The two anchors whose `surface` is `water` (Lake Siss, the Great Ameld mouth) may stand in water, as `lakeside` / `coast`;
  every other site has its whole disc on land.
- Roads: the checker samples every 4 blocks; a wet run is lake, ocean or a river corridor (half the river width on each
  side). The road grade (1 in 2) is not checked yet: it needs the height estimate of the converter.
- Rules only the converter can judge (height continuity, river reach steps) are not here.
