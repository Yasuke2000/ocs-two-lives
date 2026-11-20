# Post-Kijin place concepts — twelve delivered locations

These original illustrations and their fiches use the current map reservations at `fc36e38` and the owner-selected instant immediately after Kijin naming. The four western concepts additionally verify all58 reservation attributes against current map review`a997f81`; active geometry is unchanged. They are design references, not in-game screenshots or a new source of canonical geography.

| Place | Image | Source and terrain sheet |
| --- | --- | --- |
| Rimuru's early village | [PNG](tempest.png) | [Sheet](tempest.md) |
| Dwargon southern mountain gate | [PNG](dwargon.png) | [Sheet](dwargon.md) |
| Rondo / Londo, Blumund | [PNG](blumund.png) | [Sheet](blumund.md) |
| Lake Siss southern marsh shore | [PNG](lake_siss.png) | [Sheet](lake_siss.md) |
| Treyni's shrine — server interpretation | [PNG](treyni_shrine.png) | [Sheet](treyni_shrine.md) |
| Sealed Cave exterior approach | [PNG](sealed_cave.png) | [Sheet](sealed_cave.md) |
| Dwarf meadow village — pack interpretation | [PNG](dwarf_village.png) | [Sheet](dwarf_village.md) |
| Orc advance camp — encounter reservation | [PNG](orc_camp.png) | [Sheet](orc_camp.md) |
| Lura / Englassia capital precinct | [PNG](englassia.png) | [Sheet](englassia.md) |
| Marris / early Falmuth royal precinct | [PNG](marris.png) | [Sheet](marris.md) |
| Coleus / Herbaria hill-palace precinct | [PNG](coleus.png) | [Sheet](coleus.md) |
| Shia / Siltrosso counting court — interpretation | [PNG](siltrosso.png) | [Sheet](siltrosso.md) |

The earlier `chatgpt/priority-place-art` branch and local `C:/Users/david/Documents/ocs-art-map` candidates remain untouched. That worktree contains 29 candidate PNGs and 58 sheets; many are untracked and have not been accepted against the current map. The old Tempest sheet uses radius 110, while this pass reads the current SVG. The old Orc camp depicts a large organized fortification; the selected revision depicts a small temporary advance reservation appropriate to the early baseline. The existing candidates are not counted as delivered or discarded.

[Coverage](coverage.csv) keeps all 58 IDs: twelve image/sheet pairs delivered in this branch, with existing local candidates explicitly recorded for the remainder. Do not regenerate those candidates blindly. No complete 58-image set is claimed. Forty-six image/sheet pairs remain undelivered. Country/location research remains open; the current-geometry continent painting is separately delivered in [draft PR88](https://github.com/Yasuke2000/ocs-two-lives/pull/88), with further coupled review rounds still open.

The image format is 1536x1024, RGB, opaque, below 3,000,000 bytes per PNG; [manifest](asset-manifest.json) records exact sizes and hashes. Three PNGs were losslessly repackaged; decoded RGB pixels match their original generated outputs. The selected dwarf-village correction removes an invented surface palace from its background. No mod texture, official frame, proprietary structure or map is copied into these images. The fiches distinguish canon context, server interpretations and unknown episode attribution.

The terrain/biome/road source is unchanged. These images do not verify foundations, structure placement, cave water, detailed shore alignment, NPC rosters or runtime era gates. [Map PR74](https://github.com/Yasuke2000/ocs-two-lives/pull/74) remains the geometry review.

## Western revisions — round21

The new Englassia and Marris images show compact representative precincts, replacing unsupported extra water and panoramic scale in the older local candidates. Coleus uses the inspected official INEI production concept for broad hill/dome/stair cues, while exact architecture and its S1E10 state remain interpretation/unverified. Siltrosso edits our own older concept to replace an unsupported snowy backdrop with low coastal hills; its counting court remains an explicit server design, independent of Falmuth sovereignty. All four new images were visually reviewed.

All five official episode20 and episode28/no30 stills were inspected: they provide character/interior context, not verified Englassia or Falmuth exterior plans. These leads are not upgraded to architectural evidence. Official art remains linked in the fiches and cached outside the repo; no official reference was an image-generation input. The Siltrosso edit uses only our original concept. Its first-generation prompt is unavailable; the complete current edit prompt is recorded.

[Western manifest](western-asset-manifest.json) records four asset hashes, original output hashes, exact reservation attributes and RGB pixel-preserving packaging checks; [western prompts](western-prompts.json) records exact current prompts. The earlier eight-asset manifest remains unchanged. Englassia and Marris were losslessly recompressed under3,000,000 bytes without changing a single RGB pixel. These representative scenes are not whole-city surveys, blueprints, terrain alterations or runtime acceptance.

Round21 verification: all12 PNG/sheet pairs match their manifests and the58-row coverage table; all images are RGB1536x1024 below3,000,000 bytes. Repository gate passes validation and462 tests (26 skips,zero failures,44.871s test tier). `world/`, `tools/`, `mod/` and `pack/` are unchanged from the base art branch. No in-game acceptance or deployment is claimed.
