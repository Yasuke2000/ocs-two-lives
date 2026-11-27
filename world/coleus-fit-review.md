# Coleus: retain the occupied hillside, not an enlarged empty rectangle — round67

[Original support plan and ascent profile](coleus-fit-review.png) · [editable diagram](coleus-fit-review.svg) · [decoded audit](coleus-fit-review.json) · [earlier rectangular survey](template-terrain-fit-r62.json)

The [official INEI concept](https://www.ten-sura.com/news/anime/coleus/news/post/8574) depicts a palace above a dry hill and a long inclined approach,with a lower town and water context. That previously recorded visual was inspected again. The current blueprint supplies its own stepped hill and approach. The world drawing should support that model without interpreting the whole template rectangle as a flat inhabited platform. Exact scale,compass orientation and architecture remain authored;this is not a whole-city or initial-resident acceptance.

## What the actual files contain

Three existing NBT slabs decode to85 ×47 ×79,with75,372 defined entries and66,242 non-air blocks in5,313 occupied x/z columns. Local anchor(42,4,72) maps to world(-3520,75,-860);the volume starts at(-3562,71,-932). The highest defined non-air block is114. No structure file,registry,anchor or production geometry is edited.

The R62 rectangle survey found eight columns differing by more than half a block from first-air75. **Seven contain no non-air model column.** The remaining point is local(81,0):four rock blocks at local y0..3,not a palace room or path. Its designed first air is74.458984 bilinear,74.486273 bicubic. The whole occupied footprint is not perfectly flat:the bicubic range is74.486273..75.015118. The small positive overshoot must not be described as an exactly level entire template.

## Functional support and the real interpolation scope

All seven measured boxes—the main pavilion,two annexes,ascent,two lower gates and small oasis context—have underlying designed first air **exactly75** with both methods. Their box extents and column counts are in the audit. These are support levels below the authored stepped model,not a claim that every room or stair tread is at75.

The forty centreline ascent floor blocks are present in the NBT,from world y74 to90. Each has air or undefined entries at the next two y positions. This is a model-level centreline observation,not full-width collision validation or proof that undefined positions are air in a generated world. Real placement,noise,obstructions and walking remain untested.

The R62 diagnostic used a four-neighbour **bilinear planning sampler**. The current terrain code's CanonRasters.height uses sixteen-neighbour **Catmull-Rom bicubic** sampling. This follow-up reads that implementation and evaluates both against the same normal export. It does not claim to run the entire Minecraft density/noise/carving pipeline. Earlier staging surveys remain valid descriptions of their stated bilinear method;they are not exact runtime surfaces. Future fit decisions need the appropriate interpolation and actual occupied/functional shape.

Although247 occupied column centres lie beyond the drawn73-block radius,all5,313 occupied columns have the exported **SITE exclusion bit** in their containing raster cells. No designed external-water pixel lies under them. The site-class raster is zero in227 occupied containing-pixel samples and23 in5,086;that classification edge is distinct from the exclusion mask. Exported structure exclusion is not proof of every tree/decoration rule or runtime placement.

## Decision and remaining scope

**Retain r73 and the current terrain.** The rectangle-plus-margin estimate of98 is a geometric enclosure,not evidence that the authored hill must be flattened that far. Functional support is already level;the outer rock variation is compatible with a natural collar and the model's intentionally irregular outcrop. This resolves the specific reason to enlarge the Coleus clearing. It does not close whole-country Coleus coverage,C21 sovereignty/binding questions,initial-era architecture or technical placement.

The original diagram uses decoded occupied columns and the seven authored functional boxes. It reproduces no copyrighted source image. Its staircase profile shows defined floor-block y indices,not a player collision trace. Copyrighted reference art remains linked and cached outside the repository.

DES-COLFIT-067 is an original analysis record. Ledger260 unique(202 thematic/design/reference +58 coordinate interpretations);14 directly read printed-LN and6 separately classified author-side-story claims remain. Inventory132/41 physical follow-ups is unchanged. Source c2f806a9,all terrain and R64 atlas are retained. No converter rerun,main merge,terrain apply,chunk generation or Minecraft test is claimed.

Repository validation and472 tests pass (26 skipped,zero failures,63.234s);zero changed JavaScript files. The native plan/profile was visually inspected. Source,checker/terrain previews and atlas remain identical;the previous handoff history is retained. This is a file/data audit,not a generated-world or walkability test.
