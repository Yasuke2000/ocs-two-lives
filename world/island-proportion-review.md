# Island proportions against the official illustration

![Original comparison](island-proportion-review.png)

[Editable comparison](island-proportion-review.svg) · [Measurements and transforms](island-proportion-review.json) · [Official reference, linked only](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp).

## A remaining C12 difference

The two large outlying islands remain compressed relative to the mainland. Their current coast shapes were improved in R125/R128, but shape improvements did not establish faithful relative size. A new visual comparison with the official base image exposes this distinction.

| Landmass | Active width / mainland width | Broad reading of official image | Chosen illustrative alternative |
| --- | ---: | ---: | ---: |
| Ice Continent | 25.22% | About 40–43% | 41.5% (4,143.12 blocks wide) |
| El Dorado island | 24.04% | About 31–34% | 32.5% (3,244.61 blocks wide) |

The reference bands are approximate visual horizontal-span readings, not surveyed canon dimensions, a known projection or a traced shoreline. They measure apparent extent on an illustration; land height and area are not inferred. The exact chosen percentages and all trial coordinates are **our interpretation**. A directly verified LN geographic statement would outrank this image evidence.

The active mainland width is 9,983.41 blocks. Its current Ice Continent is 2,518.15 × 1,129.02; El Dorado is 2,400.50 × 1,280.55. The server brief instead recommends islands around 2,500 × 1,500 and 2,000 × 1,600 respectively. Those compressed server dimensions are not a canonical proportion claim.

## Concrete alternative, kept inactive

`world/map.svg` now contains `reference-island-scale-*` paths inside a **comment**. They uniformly transform our existing original coast geometry, including the five detached ice-coast forms. They contain no licensed reference pixels or traced coast. The study does not activate a new shoreline, move a site or rescale relief, lakes, biomes, forest, roads, gameplay masks or art.

The Ice Continent's coast is enlarged by 1.645302 about the current inland palace, then moved 377.68 blocks north. El Dorado's coast is enlarged by 1.351640 about its city reservation, then moved 420.40 blocks south. Those anchors define the transforms; their sites are **not** accepted at new transformed coordinates. Each large trial island is separated from the unchanged mainland by a measured nearest-boundary distance of 1,000 blocks. Distances are computed from the checker's flattened original curves, rather than image pixels.

With the required 1,200-block outer sea margin and 512-block rounding, this particular coast-only layout needs **13,312 × 12,288** blocks. Its height exceeds the **11,264** hard design-box limit by **1,024 blocks**. This demonstrates a real conflict for this trial, not a proof that every possible rearrangement is impossible. Repositioning, changing sea gaps or changing mainland scale would require a separate whole-map review; none is silently accepted here.

## Verification and delivery scope

Every active XML element, attribute, non-whitespace text and child order is identical to the baseline before adding the comment. All 58 sites, all 22 roads and all native terrain layers are unchanged. The freshly generated standard preview is byte-identical to the previous preview; checker: **zero errors, all 56 relations, two standing warnings**. The preview and original comparison were visually inspected.

Adding a comment changes the file SHA256 to `016977e5c503277d1f741599c1d4c98b84386cc1fe3f9417ae2b4f18cd895bb3`. The existing normal rasters remain outputs from the original R130 source `ade502105956db450831e0991b2f10e6b29f8b73a1827f1d0184299c505917bb`; they are adopted for the identical active geometry. No new converter run or acceptance of the alternative is claimed. Historical hash-pinned audit commands continue to describe their original input.

The facts ledger adds one qualified image observation and one original-design record. C12 and the region guide now explicitly disclose the relative-island compression. The post-Kijin snapshot, existing inland-palace choice and initial political state remain applicable. No tools, runtime data, world application, chunk generation, merge or deployment changes accompany this study.

Required repository gate: `bash tools/check.sh` passed; 472 tests in65.313seconds,26skipped,zero failures. `git diff --check` passed. These checks validate the delivered inert study and unchanged active map, not the unactivated larger-island terrain.
