# Current designed biome shares — R111

[CSV](region-biomes-r111.csv) · [full counts and hashes](region-biomes-r111.json) · [R108 method](region-biomes-r108.md). Reproduce with `python -B world/region_biome_census.py --round 111` after matching normal staging. R108/R109 outputs remain historical.

Two bounded El Dorado canopies introduce4,788 forest-biome cells;all other current biome cells retain their values. X now has5.3940% forest in its gameplay mask. This is measured authored terrain,not canonical climate,sovereignty,tree density or runtime chunks. Old20% target is not reinstated.

The census covers22 regions/108 biome rows;2,702,958 non-ocean samples,2,693,482 assigned and9,476 coastal raster-edge samples reported separately.26 shared-boundary samples follow the explicit source-order rule;zero native inland samples are unassigned. Current prose uses two decimals and displays positive shares below0.005% as<0.01%;it no longer rounds a tiny positive share to zero.
