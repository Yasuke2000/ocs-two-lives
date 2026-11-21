# Dwargon approach: roof cover is not entrance continuity — round51

Historical round51 finding,sourcecb07cce7. The authored terrain interface is corrected in [round52](dwargon-approach-fix.md); the original measurements below are retained. Runtime placement/walkability remains unverified.

[Measured section](dwargon-approach-study.png) · [editable vector](dwargon-approach-study.svg) · [audit and samples](dwargon-approach-audit.json) · [direct-source review](../docs/research/tensura-world-2026-11-19/dwargon-source-review-r51.md).

The production source is unchanged at `cb07cce7f028aaaa71914209928db3a8ad1b7b9a892ab24520ab827072d62371`. This read-only study consumes the existing matching normal build, its road profile, and the actual generated Dwargon footprint. The section at x0 has equal horizontal/vertical scale; its gate reference is a blueprint arrival coordinate, not an exterior surface promise.

## Measured finding

The `tempest_dwargon` road ends at **(0,-1495), profile first-air y71.33**. The existing148×168 blueprint's arrival is(74,4,120); at world gate(0,-1550), that puts its southern box boundary at z-1502. Fixed base142 plus arrival4 gives reference first-air146; the blueprint approach path has ground block at base+3. The endpoint therefore lies seven blocks outside the box boundary with a **74.67-block reference-height difference**. The gate-centre exterior surface is185; that surface sample is not the intended tunnel/arrival elevation.

The placed structure and its repair ring can modify eventual terrain. This audit identifies an exported road/template mismatch; it neither proves a live impassable step nor verifies a successful entrance. A low maximum grade within the exported road's own points does not test the missing connection to the template. No silent technical fix is applied.

## Roof result and pin semantics

All **3,179** authored roof columns were sampled bilinearly against the current16-bit designed surface. Surface minus the required first rock above each authored roof has minimum6.0, median14.171875 and maximum48.0 blocks; no column falls below six. This checks the designed surface envelope, not voxel carving or final structure placement. Intentional footprint openings and skylight columns are outside the roof-column set.

The unplated `dwargo`, `dwargon_throne` and `kaijin_smithy` index heights (188,182,198) are exterior surface samples, as `pin_grounds()` specifies. They are not certified interior floor levels. The current horizontal anchor resolver returns x/z; seated Gazel uses placed blueprint base and royal local coordinates. These readings do not establish a current NPC height bug, and changing those values blindly would be unjustified.

## Next terrain action

Preserve the fixed template base142, all58 anchor positions/radii and current river contacts. Author a graded exterior approach to the template's southern road edge and a suitable open foothill transition. Check the road-to-template join explicitly after the normal build, then examine all nearby site-disc samples, roof cover, water, profile grades and affected road intersections. Compare the new checker/terrain preview and original painting against the official geographical reference. Any production SVG edit requires the immediate default checker. The exact ramp and pasture extent will remain our interpretation, not WN measurements.

Do not add the unlocated East/West cities merely to make the inventory count shrink. No new runtime/tool change, terrain application, Minecraft chunk generation, main merge or deployment is made here. The32 inventory follow-ups and wider initial-era/source/binding/fit/runtime obligations remain open.

Repository validation and472 tests pass (26 skips,zero failures,62.692s test tier); no changed JavaScript files. These offline checks do not verify the road/template join or live placement.
