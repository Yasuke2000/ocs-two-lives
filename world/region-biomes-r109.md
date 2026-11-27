# Designed biome shares after the inland palace move — R109

[CSV](region-biomes-r109.csv) · [full counts/hashes](region-biomes-r109.json) · [R108 method and historical snapshot](region-biomes-r108.md). Run `python -B world/region_biome_census.py --round 109` against matching normal staging. R108 output stays historical.

All22 regions and107 biome rows are measured again after retiring the coastal site preparation and moving the existing palace entrance inland. The22 current descriptions use this snapshot. Native region and biome polygons are unchanged;108 biome raster cells change locally,including raster-edge beach treatment near the retired coast pad.

There are2,702,958 non-ocean cells:2,693,482 assigned to gameplay masks and9,476 outside native coast,reported separately. Exact shared-boundary samples26 follow source order; zero native-inland samples are unassigned. This measures authored gameplay masks,not sovereign borders,canon climate,tree density or runtime chunks. The R108 limits remain applicable.
