#!/usr/bin/env python3
"""Turn a political map of the Tensura world into the canon-continent grid the Tensura world is generated from.

Usage: canon_map.py <reference.png> [--width N]   (default: "width" in canon_regions.json)
Reads a flat-colour political map (ocean one colour, nations flat fills with dark borders), floods every
nation from a seed point and writes:
  pack/config/ttl/canon_map.txt     one character per chunk (16x16 blocks): '.' sea, '~' river/lake,
                                    a letter per nation (pack/config/ttl/canon_regions.json says which)
  docs/previews/canon_map.png       the same grid in colour, for review
The reference image is not kept in the repo (fan art); the grid is ours to edit by hand afterwards.
The ttl-portals mod reads both files when the Tensura world generates (see canon_regions.json for knobs).
"""
import json
import math
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from blueprint import _write_png  # noqa: E402
from pngread import read_png  # noqa: E402

GRID = ROOT / "pack" / "config" / "ttl" / "canon_map.txt"
REGIONS = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
PREVIEW = ROOT / "docs" / "previews" / "canon_map.png"
CHUNK = 16
STEP = 2  # work on every 2nd reference pixel: borders stay closed, the flood stays fast
OCEAN = (41, 178, 185)


def classify(rgb):
    r, g, b = rgb
    if abs(r - OCEAN[0]) + abs(g - OCEAN[1]) + abs(b - OCEAN[2]) < 40:
        return "sea"
    if r + g + b < 200:
        return "line"
    if min(r, g, b) > 235:
        return "line"
    return "land"


def close(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) < 45


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    regions = json.loads(REGIONS.read_text(encoding="utf-8"))
    # The continent's width in blocks lives in canon_regions.json ("width"); --width overrides it once.
    width_blocks = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else regions.get("width", 10000)
    w0, h0, px = read_png(args[0])
    sx = regions["reference"]["width"] / w0  # seeds are given in reference-map coordinates
    w, h = w0 // STEP, h0 // STEP
    colour = [[px(x * STEP, y * STEP) for x in range(w)] for y in range(h)]
    kind = [[classify(colour[y][x]) for x in range(w)] for y in range(h)]

    # Flood every nation from its seeds, through pixels of the seed's colour.
    owner = [[None] * w for _ in range(h)]
    # Small nations first: neighbours share colours (Jura, Yuzalgh and Morgdahl are all pink), so a big flood
    # through a gap in a border must not claim them.
    for letter, region in reversed(list(regions["regions"].items())):
        for sxr, syr in region["seeds"]:
            x0, y0 = int(sxr / sx) // STEP, int(syr / sx) // STEP
            best = None
            for r in range(0, 12):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        x, y = x0 + dx, y0 + dy
                        if best is None and 0 <= x < w and 0 <= y < h and kind[y][x] == "land" and owner[y][x] is None:
                            best = (x, y)
                if best:
                    break
            if not best:
                sys.exit(f"seed {letter} {sxr},{syr} is not on land")
            seed_colour = colour[best[1]][best[0]]
            queue = deque([best])
            owner[best[1]][best[0]] = letter
            while queue:
                x, y = queue.popleft()
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and owner[ny][nx] is None and kind[ny][nx] == "land" \
                            and close(colour[ny][nx], seed_colour):
                        owner[ny][nx] = letter
                        queue.append((nx, ny))

    # Borders, labels and unseeded micro-states go to the nearest nation.
    queue = deque((x, y) for y in range(h) for x in range(w) if owner[y][x])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and owner[ny][nx] is None and kind[ny][nx] != "sea":
                owner[ny][nx] = owner[y][x]
                queue.append((nx, ny))

    # Land extent → scale: the continent and its islands span `width_blocks` blocks.
    xs = [x for y in range(h) for x in range(w) if owner[y][x]]
    ys = [y for y in range(h) for x in range(w) if owner[y][x]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    blocks_per_px = width_blocks / ((x1 - x0 + 1) * STEP)
    cell = CHUNK / (blocks_per_px * STEP)  # working pixels per chunk
    cols = int((x1 - x0 + 1) / cell) + 1
    rows = int((y1 - y0 + 1) / cell) + 1
    grid = []
    for gy in range(rows):
        line = []
        for gx in range(cols):
            votes = {}
            for yy in range(int(y0 + gy * cell), int(y0 + (gy + 1) * cell)):
                for xx in range(int(x0 + gx * cell), int(x0 + (gx + 1) * cell)):
                    if 0 <= xx < w and 0 <= yy < h:
                        k = owner[yy][xx] or "."
                        votes[k] = votes.get(k, 0) + 1
            line.append(max(votes, key=votes.get) if votes else ".")
        grid.append(line)

    # Water that is not wide open sea (rivers, lakes) becomes '~': open sea is reached from the edge through
    # cells at least 2 cells from land.
    def near_land(x, y):
        return any(0 <= x + dx < cols and 0 <= y + dy < rows and grid[y + dy][x + dx] != "."
                   for dy in range(-2, 3) for dx in range(-2, 3))
    open_sea = set()
    queue = deque((x, y) for y in range(rows) for x in range(cols)
                  if (x in (0, cols - 1) or y in (0, rows - 1)) and grid[y][x] == ".")
    open_sea.update(queue)
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in open_sea and grid[ny][nx] == "." \
                    and not near_land(nx, ny):
                open_sea.add((nx, ny))
                queue.append((nx, ny))
    # The coastal fringe (water within 2 cells of open sea) is sea too; what is left is inland water. Limited
    # to 2 steps so rivers that reach the sea stay rivers.
    frontier = list(open_sea)
    for _ in range(2):
        grown = []
        for x, y in frontier:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in open_sea and grid[ny][nx] == ".":
                    open_sea.add((nx, ny))
                    grown.append((nx, ny))
        frontier = grown
    for y in range(rows):
        for x in range(cols):
            if grid[y][x] == "." and (x, y) not in open_sea:
                grid[y][x] = "~"

    # World 0, 0 sits on the configured origin (a seed point in reference coordinates).
    ox, oy = regions["origin"]
    origin_cell = [round(((ox / sx) / STEP - x0) / cell), round(((oy / sx) / STEP - y0) / cell)]
    # Water and wetlands the reference map can't show (a nation's label is printed over Lake Siss, rivers break
    # at the map's lines): "paint" in canon_regions.json, in world blocks, applied after tracing so a
    # regenerated grid keeps them. A lake is a wobbly ellipse of '~' with an optional ring of a region around
    # it; a river is a polyline of '~' `width` chunks wide that only replaces land.
    def cell_of(wx, wz):
        return origin_cell[0] + wx / CHUNK, origin_cell[1] + wz / CHUNK

    def land(x, y):
        return 0 <= x < cols and 0 <= y < rows and grid[y][x] not in ".~"

    # Paint coordinates and sizes are written for a continent `paint_width` blocks wide and scale with "width".
    k = width_blocks / regions.get("paint_width", width_blocks)
    for item in regions.get("paint", []):
        if item["kind"] == "lake":
            cx, cy = cell_of(item["center"][0] * k, item["center"][1] * k)
            rx, ry = item["size"][0] * k / 2, item["size"][1] * k / 2
            ring = item.get("ring", 0) * k
            for y in range(max(0, int(cy - ry - ring - 2)), min(rows, int(cy + ry + ring + 3))):
                for x in range(max(0, int(cx - rx - ring - 2)), min(cols, int(cx + rx + ring + 3))):
                    a = math.atan2(y - cy, x - cx)
                    wobble = 1 + 0.12 * math.sin(3 * a + 1.3) + 0.07 * math.sin(7 * a + 0.4)
                    d = math.hypot((x - cx) / rx, (y - cy) / ry) / wobble
                    if d <= 1:
                        grid[y][x] = "~"
                    elif ring and land(x, y) and math.hypot((x - cx) / (rx + ring), (y - cy) / (ry + ring)) / wobble <= 1:
                        grid[y][x] = item["ring_region"]
        elif item["kind"] == "river":
            half = item.get("width", 2) * min(k, 1.25) / 2
            points = [cell_of(pt[0] * k, pt[1] * k) for pt in item["points"]]
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                steps = max(1, int(math.hypot(bx - ax, by - ay) * 2))
                for i in range(steps + 1):
                    t = i / steps
                    # A gentle meander so the channel isn't ruler-straight.
                    nx, ny = -(by - ay), bx - ax
                    norm = math.hypot(nx, ny) or 1
                    m = 1.5 * math.sin(t * math.pi * 3 + ax)
                    px, py = ax + (bx - ax) * t + nx / norm * m, ay + (by - ay) * t + ny / norm * m
                    for y in range(int(py - half - 1), int(py + half + 2)):
                        for x in range(int(px - half - 1), int(px + half + 2)):
                            if land(x, y) and math.hypot(x + 0.5 - px, y + 0.5 - py) <= half:
                                grid[y][x] = "~"

    header = [
        "# Canon continent of the Tensura world, one character per chunk (16x16 blocks). Generated by",
        "# tools/canon_map.py, then free to edit by hand: '.' sea, '~' river/lake, letters = nations",
        "# (pack/config/ttl/canon_regions.json). Changes only affect chunks that are not generated yet.",
        f"# origin {origin_cell[0]} {origin_cell[1]}  (this cell's north-west corner is world 0, 0)",
    ]
    GRID.parent.mkdir(parents=True, exist_ok=True)
    GRID.write_text("\n".join(header + ["".join(line) for line in grid]) + "\n", encoding="utf-8", newline="\n")

    rgba = bytearray()
    for line in grid:
        for c in line:
            col = regions["regions"][c]["colour"] if c in regions["regions"] else ((40, 120, 190) if c == "~" else (30, 70, 140))
            rgba += bytes(col) + b"\xff"
    _write_png(PREVIEW, cols, rows, rgba)
    land = sum(c not in ".~" for line in grid for c in line)
    print(f"{cols}x{rows} chunks ({cols * CHUNK}x{rows * CHUNK} blocks), {land} land chunks, origin cell {origin_cell}")
    print(f"wrote {GRID.relative_to(ROOT)} and {PREVIEW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
