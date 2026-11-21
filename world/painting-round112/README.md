# Painted atlas: southern coast alignment (R118)

![Current painted atlas](atlas.png)

[Before/after](comparison-r118.png) · [Native continent](continent.svg) · [Editable atlas](atlas.svg) · [Audit](audit.json) · [58-site registration](site-registration.json) · [Coast support](coast-support-r118.json) · [Provenance](provenance.json).

This delivery follows R117 source `5938a8239068ccdd98c8ad64220147dfbdc82ca6d6d7e54364fc902fb1e9ebe7` from [PR105](https://github.com/Yasuke2000/ocs-two-lives/pull/105). The painted southeastern foot is now a narrower curved taper. The native sea mask and shoreline use the exact current mainland path. The original land texture, 58 registration rows, 20 context labels, 42 inventory rows and all prior native children remain. Root source/review metadata and two new native children identify the correction; historical nested metadata remains historical.

The existing original ocean pattern fills the removed land. A 220-block core buffer, 380-block support and 40-block feather replace the old coast glow and blend into retained sea. The first smaller trial left a ghost shore; visual review caught it, and the final wider blend removes it. New shallow-water wash and shore ink follow the source boundary. Their color, thickness and texture are illustration choices, not surveyed bathymetry or Minecraft beach dimensions. No raw raster edit, new image generation or copyrighted reference pixels are used.

16,989 continent pixels change within the declared support plus 16 blocks for antialiasing; all exterior pixels are identical. The exact previous native child trees are retained. Atlas XML changes only its source metadata and embedded current PNG; all site/context/list geometry and text remain. Browser inspection reports no overlaps and minimum number spacing 32.47 pixels. The atlas embeds the exact final continent PNG.

The source’s 172,196 changed terrain-height samples are independently documented in [R117](../southern-coast-r117.md). This painting does not resample the whole relief or prove pixel-wise terrain-height identity. No further source-geometry correction was identified from the silhouette review. The [R117 census](../region-biomes-r117.md) remains current; all 58 art reservations and approved inland Frost Palace remain unchanged. C23 waterfall-character/fluid-placement review, full proportions, missing locations and initial-era consistency remain open. Ledger: 323; inventory: 142 with 42 physical follow-ups.

The established directory is updated in place; the original R116 delivery remains at [baseline commit b5a2fa4](https://github.com/Yasuke2000/ocs-two-lives/tree/b5a2fa4124ba2732f43a6bd11157d3e436f025e3/world/painting-round112). Earlier R112 canopy comparison/tree-symbol files retain their historical scope. No world apply, chunk generation, main merge, deployment or in-game acceptance is claimed.

Verification: default checker zero errors, all 56 relations and two prior warnings. Exact-source normal staging (67.0 seconds) is adopted unchanged. Required repository gate: 472 tests, 26 skipped, zero failures in 63.715 seconds; validation and `git diff --check` pass. The final native continent, local comparison and browser layout were inspected. All 6,128 removed-land sample centres at least 32 blocks inside the removed area have blue-dominant ocean color; this is a visual check, not fluid simulation.
