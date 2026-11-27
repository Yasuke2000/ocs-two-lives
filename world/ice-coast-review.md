# Ice Continent coast review — round 32

[Before/after diagram](ice-coast-study.png) · [editable diagram](ice-coast-study.svg) · [measured audit](ice-coast-audit.json) · [current atlas](atlas.png).

## Reference and interpretation

The [official introductory map](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp) was visually compared with the current checker preview. Its frozen continent has uneven shoulders and recesses, while the earlier authored island had a much smoother envelope. This pass introduces three limited inlets on the northwest, east and southwest shores. The precise vertices, bay shapes and their size are **our interpretation**. They are not a measured reconstruction of the licensed coastline, named canonical fjords or new story locations. The reference image remains linked and cached outside the repository.

The new polygon retains 94.02% of the earlier authored area, with maximum boundary displacement about 208 blocks. It has 105 vertices, within the brief's preferred range. The existing island, I gameplay mask and permafrost polygon share the revised boundary; the permafrost boundary is now exactly aligned with the coast. No fourth landmass, new anchor, town, port or road is introduced. Mainland and El Dorado geometry remain unchanged. The mountain spine and high-peak polygons remain unchanged.

This does not resolve C22. Direct WN78 evidence places White Ice Palace centrally on the frozen continent; the required live `frost_palace` reservation remains coastal. The existing inert alternative is still about 13 blocks from the revised authored centroid, which is not a canonical coordinate. The palace's active centre, radius, site kind and nearby southern shore are retained. Coast-to-palace centre distance remains 55.36 blocks. See [the source/access decision](frost-palace-source-review.md).

## Verification

The mandatory checker ran immediately after the SVG edit: zero errors, all 56 relations pass, and the same two disclosed warnings remain. The closest authored sea gap to the mainland is 916.98 blocks, within the fixed 900–1,200 range.

A fresh normal staging build completes in 55.1 seconds with no converter warnings. Current source SHA is `d10aa45699bbbf17c6a37280b075f80fbb5f4ed39b9fc742ebc9346f81102b00`. The audit compares against commit `5260630`: all 58 site attributes, all 21 road geometries/profiles, site/exclusion rasters and the complete water raster remain unchanged. Height and biome rows south of z=-2800 are identical. The 230×230 square centred on Frost Palace also has identical height, water and biome pixels. There are 75,421 changed height cells in the northern coast blend and 8,352 changed biome cells around the revised shore. These are staging measurements, not in-game terrain acceptance.

The checker preview, current atlas and before/after diagram were visually inspected. The official map supports broad illustrated geography rather than the numerical precision of these authored inlets. Earlier painted reviews predate both this shoreline change and the Orbic habitat change; current SVG/checker/atlas output governs this version. No technical rule, runtime code, terrain apply, Minecraft chunks, actual merge or deployment is changed or claimed.

## Primary-source access limits

The GC Novels [current series page](https://gcnovels.jp/slime/novel.html) provides publisher-linked licensed trials. New trial-page links for guide 8.5 and LN14 redirected to the current BookWalker `/03/21/viewer.html` viewer, but local Chrome navigation timed out after 25 seconds without readable book pages. This is distinct from the older viewer URL failure; neither attempt verifies those contents. The publisher's LN16 trial link likewise exposes a viewer, not readable story text through the web text tool.

The [Yen Press LN16 listing](https://yenpress.com/titles/9781975369750-that-time-i-got-reincarnated-as-a-slime-vol-16-light-novel) and [LN14 listing](https://yenpress.com/titles/9781975314484-that-time-i-got-reincarnated-as-a-slime-vol-14-light-novel) establish licensed edition metadata and retailer links. Apple Books metadata and Kobo's preview listing were checked; no relevant story pages were read. Direct local page requests to Yen Press/Kobo returned 403. These are bounded access results, not a claim that legal samples do not exist or that their geography agrees with the current map. C05 and C22 primary-LN gaps remain open; the directly verified LN claim count stays 13.
