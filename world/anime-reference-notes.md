# Anime-led map revision — 19/11/2026

Yasuke explicitly chose **anime and wiki geography over earlier server liberties** after supplying the map image,
the interactive reference below and a wiki excerpt. Fulbrosia now lies south of Jura, while Ulgracia lies south
of Sarion. These decisions supersede the corresponding southwest-Fulbrosia and Blumund-adjacent-Ulgracia answers
in `design/architecture/own-world.md`; the owner-authorized five data-rule corrections and superseding owner clarification now record that change.

## References actually inspected

- [Official world guide](https://www.ten-sura.com/map): the guide describes the Ameld feeding Lake Siss,
  the Khusha range extending between Jura and Sarion, and Ulgracia south of Sarion.
- [Interactive reference, pinned commit](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6).
  Read its README and location metadata. The author identifies the wiki and a fan map as sources; this is a
  **secondary reference**, not proof that every marker or coastline is official. Its software licence does not
  establish ownership of anime screenshots. No code, polygons or copyrighted image files are copied into this repo.
- The user-supplied map images: used to compare broad geography, not traced into coastline vertices.
- The supplied wiki excerpt: confirms the northern mountain-built Dwargon, the eastern Empire and Velgrynd's
  mountain, Eurazania's warm fruit-growing country, the southern forest landmarks and western farming states.
  Names and politics vary by translation and story era; the excerpt's `Central` for Dwargon and `Rondo` for Blumund
  are recorded as variants rather than silently replacing the project's existing names.

The following original frames were read from that pinned repository's `public/img/locations/` directory and
visually inspected locally. They stay outside the modpack repository as research references:

| Frame | What the map takes from it |
| --- | --- |
| `dwargon_gate.webp` | Massive pale, angular rock walls enclosing a comparatively small south-facing gate, with a grassy apron. The city belongs inside the rock. |
| `lake_siss.webp` | Broad, open, reed-fringed water and low distant shores; avoid making it a tiny ornamental pond. |
| `khusha_mountains.webp` | Tall, narrow rock pillars with sparse trees and mist, rather than a smooth rounded hill. The range continues toward Sarion. |
| `rimuru_city.webp` (credited to episode 62) | A later planned city in a green basin, a principal avenue and room to grow. This is not the early village era. |
| `sealed_cave.webp` | Irregular natural rock mouth, steep cave walls and faint magic-ore light, not a monumental built portal. |
| `jia.webp` | A high, narrow cliff city with ledges carved into rock pillars, not a flat town in southwestern grassland. |
| `laura.webp` | A city below a great waterfall between sharp mountain walls, with a broad main approach and extensive cultivated ground. |
| `elmine.webp` (credited to episode 61) | A colossal living tree above broad green terraces and foreground water. |
| `ogre_village.webp` | A modest settlement enclosed by woodland, useful for the pre-destruction layout; the pack depicts its later ruins. |
| `londo.webp` | A low walled town beyond open cultivated fields, with hills behind it. |
| `amrita.webp` (credited to episode 38) | A dark castle above a wooded wet basin, rather than a colourful city on an exposed plain. |

These eleven frame files were all inspected. Frames remain research inputs outside the modpack repository.

## Terrain changes

Fulbrosia's `H` region and Jia move south of Jura and west/southwest of Eurazania. Jia stands on an explicitly
drawn high rock footprint. Sarion and Elmine move southwest of Jura, and Ulgracia's bluff and woods move beyond
Sarion's southern border. The previous western mesa footprint is removed. Two Khusha spire footprints flank a
river pass on the Jura–Sarion transition. Dwargon, Siss and the main western/eastern relationships remain intact.

Site discs are enlarged to the actual `min_r` values from Claude's new `world/sites.toml`; nearby small sites are
separated to preserve the checker clearance. No changes are made to that generated file, runtime anchors or tools.
After PR #66 supplied the correct spacing rule, the relative internal anchors were restored exactly to their
parent offsets; Dwargo, the throne and smithy are inside Dwargon, and the arena remains by the dwarf village.
The revised map also adds Elmine's foreground water and Laura's mountain-wall/waterfall setting from the anime frames.
The ogre ruin and its wooded hill move southeast of Tempest, toward the Khusha foothills: the user's wiki names
that range, and the pinned reference puts the former village southeast of Rimuru City. The old northeast claim
was not retained as authoritative. This is the fifth changed relation; the other four concern Fulbrosia/Ulgracia.

Two remaining evidence conflicts are left as explicit questions for the PR: the wiki treats Siltrosso as an
independent kingdom whereas the current F region groups its coastal marker with Falmuth; and the interactive
reference marks Velgrynd's mountain north of Nasca while the server brief places it south. The supplied wiki
only establishes adjacency. No new sovereign status or confirmed compass bearing is invented here.

## Adopted geography corrections

Yasuke explicitly authorized updating **only five data entries** in `tools/world/canon_relations.toml`.
The default matrix now contains the proposed corrections, with sources under
[design/lore/world-map-corrections.md](../design/lore/world-map-corrections.md). All other 51 relation
entries, site rules, sea-gap rules and checker code are unchanged. Compression ranges remain design choices.
`world/canon-relations-anime.toml` is the historical proposal, now identical in data to the default matrix.

The standard command passes with zero errors and two disclosed warnings:

```
python -I tools/world/map_check.py world/map.svg --preview world/preview.png
```

The official source supports country adjacency but does not make every exact site coordinate canonical.
In particular the ogre ruin's precise southeast bearing and Jia's compressed separation from Laura remain
secondary-reference adaptations under the owner choice. See the research confidence fields and conflicts.
The coast and terrain geometry are original; the surrounding ocean is generated beyond the authored land.
