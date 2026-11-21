"""Measure designed biome shares per native administrative region.

Run python -B world/region_biome_census.py after a matching normal staging build.
Reads existing SVG/index/biome PNG; writes only the selected pinned round’s CSV/JSON report (default R108).
Does not change map geometry,normal rasters,technical tools or runtime data.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import numpy as np
import shapely
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools/world"))
import map_check as mc

source = (ROOT / "world/map.svg").read_text(encoding="utf-8")
sha = hashlib.sha256(source.encode()).hexdigest()
index = json.loads((ROOT / "world/build/index.json").read_text(encoding="utf-8"))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--round", type=int, choices=(108,109,111), default=108)
round_number = parser.parse_args().round
pinned_sources = {108: "b275095000ed41e635c72295d05dbd3516cf8fd0c596a7a0e7a9fe14159815e1", 109: "0ae040ec3779d96d6efac288cdc46cfaf5339b1deeafbcfcf3c07224fa6f3c2b", 111: "74d63267bfa7032d1f6d7203e8e27dfa01ae948e8e5cf03f26f4bbeab2c0c079"}
assert sha == pinned_sources[round_number], "Census round is pinned to its reviewed source; choose the matching round"
assert sha == index["source_sha256"], "Normal staging rasters must match source"
biome_path = ROOT / "world/build/biome.png"
biomes = np.asarray(Image.open(biome_path))
palette = index["files"]["biome"]["biomes"]
assert palette[0] == "#ocean"
parsed = mc.parse_svg(source, mc.Report())
letters = list(dict.fromkeys(s.get("data-letter") for s in parsed["regions"]))
assert len(letters) == 22
names = dict(re.findall(r"^## ([A-Z]) — (.+)$", (ROOT / "world/regions.md").read_text(encoding="utf-8"), re.M))
X = index["box"]["x0"] + (np.arange(biomes.shape[1]) + .5) * 4
Z = index["box"]["z0"] + (np.arange(biomes.shape[0]) + .5) * 4
labels = np.zeros(biomes.shape, np.uint8)
hits = np.zeros(biomes.shape, np.uint8)
for number, letter in enumerate(letters, 1):
    poly = unary_union([Polygon(s.pts) for s in parsed["regions"] if s.get("data-letter") == letter])
    mask = shapely.intersects_xy(poly, X[None, :], Z[:, None])
    hits += mask.astype(np.uint8)
    labels[mask & (labels == 0)] = number

rows = []
regions = []
for number, letter in enumerate(letters, 1):
    selected = (labels == number) & (biomes != 0)
    values, counts = np.unique(biomes[selected], return_counts=True)
    total = int(counts.sum())
    assert total > 0
    entries = []
    for value, count in zip(values, counts):
        entry = {"region": letter, "region_name": names[letter], "biome": palette[int(value)], "cells": int(count), "area_blocks2": int(count * 16), "share_percent": float(count / total * 100), "denominator_cells": total, "source_sha256": sha, "confidence": "our interpretation", "scope": "Designed four-block samples inside native gameplay mask; not surveyed sovereignty/climate or final in-game biome distribution"}
        entries.append(entry)
        rows.append(entry)
    assert abs(sum(e["share_percent"] for e in entries) - 100) < 1e-9
    regions.append({"region": letter, "region_name": names[letter], "cells": total, "area_blocks2": total * 16, "biomes": sorted(entries, key=lambda e: -e["cells"])})

land = unary_union([Polygon(s.pts) for s in parsed["coast"]])
y, x = np.where((labels == 0) & (biomes != 0))
points = shapely.points(X[x], Z[y])
inside = shapely.covers(land, points)
# Native administrative outlines cover every inland sample. Remaining samples
# are outside native coast: raster edge coverage/beach/river mouths,not nations.
assert not inside.any(), "Investigate an actual unassigned inland biome sample"
report = {"round": round_number, "source_sha256": sha, "biome_raw_sha256": hashlib.sha256(biome_path.read_bytes()).hexdigest(), "method": "All four-block pixel centres in current biome export; native region union per letter; exact shared-boundary samples assigned to first SVG region in source order; ocean palette0 excluded. No runtime chunk-boundary claim.", "region_count": len(regions), "biome_rows": len(rows), "non_ocean_cells": int(np.count_nonzero(biomes)), "assigned_non_ocean_cells": int(np.count_nonzero((labels != 0) & (biomes != 0))), "shared_boundary_non_ocean_cells": int(np.count_nonzero((hits > 1) & (biomes != 0))), "unassigned_inland_non_ocean_cells": int(inside.sum()), "outside_native_coast_non_ocean_cells": len(points), "maximum_outside_coast_distance": float(shapely.distance(points, land).max()) if len(points) else 0, "outside_native_coast_biomes": {palette[int(k)]: int(v) for k, v in zip(*np.unique(biomes[y, x], return_counts=True))}, "interpretation_limits": "Areas describe current designed gameplay masks,not sovereign national borders or canonical climate percentages. Edge samples outside native coastline are reported separately. Final biome/noise/tree generation requires runtime tests.", "regions": regions}
assert report["assigned_non_ocean_cells"] + report["outside_native_coast_non_ocean_cells"] == report["non_ocean_cells"]
(ROOT / f"world/region-biomes-r{round_number}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
buffer = io.StringIO(newline="")
writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
writer.writeheader()
writer.writerows(sorted(rows, key=lambda e: (e["region"], -e["cells"])))
(ROOT / f"world/region-biomes-r{round_number}.csv").write_text(buffer.getvalue().replace("\r\n", "\n"), encoding="utf-8", newline="\n")
print(json.dumps({k: v for k, v in report.items() if k not in ("regions", "outside_native_coast_biomes", "method", "interpretation_limits")}, indent=2))
