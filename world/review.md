# Minecraft map handoff — anime-led revision

## What to review

- [Readable 58-location atlas](atlas.png): numbered sites over the **actual converter terrain preview**, not an AI-painted replacement.
- [Geometry checker preview](preview.png): region boundaries, rivers, relief footprints, roads and all site IDs.
- `map.svg`: the terrain source. `atlas.svg` is presentation only and must not be passed to the converter.
- [Region book](regions.md) and [anime reference notes](anime-reference-notes.md): evidence and interpretation.
- `world/build/`: local, ignored staging rasters, generated anchors and site data. No `--apply` was run.

## Three review rounds

1. The first original map replaced the blocky starter and passed the original 56 relations without errors or warnings.
   It was submitted in PR #63 with the preview. This version followed the old Fulbrosia/Ulgracia liberties.
2. A painterly study was made over that exact preview. Visual review rejected it as geography evidence because its
   regional labels were misplaced. It was not used to generate Minecraft terrain. The owner then supplied anime
   references and explicitly prioritized the Minecraft map over further concept illustrations.
3. Eleven actual reference frames, the supplied atlas, pinned interactive-map metadata and wiki excerpt were examined.
   Fulbrosia, Ulgracia, Sarion, Khusha, Jia's rock city, Laura's mountain waterfall and Elmine's foreground water were
   corrected. Footprint radii now match W1 minima and internal anchors retain their exact parent offsets.

## Verification

```
python -I tools/world/map_check.py world/map.svg --relations world/canon-relations-anime.toml --preview world/preview.png
python -I tools/world/build.py --skip-check
python -I -m unittest discover -s tests -p test_world_rasters.py
python -I -m unittest discover -s tests -p test_world_sites.py
```

The explicit checker passes all 56 relations with **0 errors** and **2 disclosed warnings**: Laura's deliberate
mountain-waterfall channel crosses its source escarpment, and the 12,288 x 10,752 box is 512 blocks taller than
the preferred target while remaining below the hard cap. Site and sea-gap rules are unchanged. Exactly five
relation entries differ from the current default matrix, all due to the owner's anime-first decision.

The converter completed in about 71 seconds at 3,072 x 2,688 pixels, with **0 converter warnings**. Its normalized
source hash matches the current SVG; **58/58 generated x/z coordinates match the SVG**, all drawn radii meet
their blueprint minima, and every relative anchor retains its parent offset. Nineteen raster tests and ten
site tests pass. Both the checker image and the generated terrain image were inspected visually.

`--skip-check` is used only after the successful explicit check above: `build.py` cannot forward an alternate
relations file. The obsolete default checker still rejects the five owner-approved geography corrections.
The normal repository gate therefore cannot be claimed green until the technical agent reconciles that matrix. The gate ran 456 fast-tier tests: three default-map assertions fail on that outdated matrix (26 skips); the targeted 19 raster and 10 site tests pass.

## Technical next step

Claude must reconcile the five relations into the default technical matrix and the superseded owner-answer text,
then run the normal gate and consume this SVG through W1. Preserve the current structure exclusions, site sizes
and internal offsets. Review the high-water basin and stepped waterfall near Laura in game, plus Dwargon's roof
cover and all site water/grade constraints. Then generate Jura, Tempest and Dwargon locally using the ongoing
mod work. **No Minecraft chunks, live world, reset or deployment have been performed in this creative PR.**

EN: Anime-referenced world design; terrain layers generated locally, Minecraft acceptance pending.
NL: Wereldontwerp op basis van animebeelden; terreinlagen lokaal gegenereerd, Minecraft-controle volgt nog.
