#!/usr/bin/env python3
"""Render front and back three-quarter views of modern 64×64 Java player skins.

Run `python tools/preview_skins.py [id ...]` after generating the skin PNGs.
Dependencies: Pillow and the Python standard library.
"""
import argparse
from math import ceil, cos, floor, radians, sin

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont

from gen_skins import PARTS, ROOT, SKINS, TARGET, face_boxes

PREVIEW_DIR = ROOT / "docs/previews/skins"
VIEW_WIDTH, VIEW_HEIGHT = 144, 218
SCALE = 6
BACKGROUND = (46, 49, 58)


def model(slim):
    """Yield a world origin, dimensions, UV rectangles and overlay inflation.

    Origin is between the player's feet. Front is positive Z. Positive X
    points to the player's left, which appears on the right of a front view.
    """
    arm = 3 if slim else 4
    origins = {
        "head": (-4, 24, -4), "body": (-4, 12, -2),
        "right_arm": (-4 - arm, 12, -2), "left_arm": (4, 12, -2),
        "right_leg": (-4, 0, -2), "left_leg": (0, 0, -2),
    }
    for name, (base, overlay, _, size) in PARTS.items():
        width, height, depth = size
        if name.endswith("_arm"):
            width = arm
        for uv, pad in ((base, 0), (overlay, 0.5 if name == "head" else 0.25)):
            dims = (width, height, depth)
            yield origins[name], dims, face_boxes(uv, *dims), pad


def visible_faces(origin, size, tiles, pad, front, left):
    """For each visible face, give its UV crop and the top-left, top-right and bottom-left corners."""
    x, y, z = (v - pad for v in origin)
    X, Y, Z = (v + length + pad for v, length in zip(origin, size))
    # The upper edge of a top tile meets the back of the head/body.
    yield tiles["top"], ((x, Y, z), (X, Y, z), (x, Y, Z)), 1.05
    if front:
        yield tiles["front"], ((x, Y, Z), (X, Y, Z), (x, y, Z)), 1.0
    else:
        yield tiles["back"], ((X, Y, z), (x, Y, z), (X, y, z)), 1.0
    if left:  # player's left, adjacent to the right edge of the front UV
        yield tiles["left"], ((X, Y, Z), (X, Y, z), (X, y, Z)), 0.86
    else:
        yield tiles["right"], ((x, Y, z), (x, Y, Z), (x, y, z)), 0.86


def paint_face(pixels, tile, corners):
    """Sample texels at pixel centres and store fragments with their camera depth."""
    (x, y, depth), (x1, y1, d1), (x2, y2, d2) = corners
    ax, ay, bx, by = x1 - x, y1 - y, x2 - x, y2 - y
    det = ax * by - ay * bx
    # Orthographic projection preserves parallelograms.
    xs = [x, x1, x2, x + ax + bx]
    ys = [y, y1, y2, y + ay + by]
    texels = tile.load()
    for py in range(max(0, floor(min(ys))), min(VIEW_HEIGHT, ceil(max(ys)))):
        for px in range(max(0, floor(min(xs))), min(VIEW_WIDTH, ceil(max(xs)))):
            dx, dy = px + 0.5 - x, py + 0.5 - y
            s, t = (dx * by - dy * bx) / det, (ax * dy - ay * dx) / det
            if 0 <= s < 1 and 0 <= t < 1:
                rgba = texels[int(s * tile.width), int(t * tile.height)]
                if rgba[3]:
                    distance = depth + s * (d1 - depth) + t * (d2 - depth)
                    pixels.setdefault((px, py), []).append((distance, rgba))


def view(skin, slim, yaw, scale=1.0):
    pitch = radians(10)
    yaw = radians(yaw)

    def project(point):
        # Model origin is at the feet, so every NPC shares the ground plane.
        x, y, z = (value * scale for value in point)
        y -= 16
        horizontal = x * sin(yaw) + z * cos(yaw)
        return (VIEW_WIDTH / 2 + SCALE * (x * cos(yaw) - z * sin(yaw)),
                VIEW_HEIGHT / 2 - SCALE * (y * cos(pitch) - horizontal * sin(pitch)),
                horizontal * cos(pitch) + y * sin(pitch))

    pixels = {}
    for origin, size, tiles, pad in model(slim):
        for crop, corners, shade in visible_faces(origin, size, tiles, pad, cos(yaw) > 0, sin(yaw) > 0):
            tile = skin.crop(crop)
            if tile.getbbox() is None:
                continue
            tile = ImageEnhance.Brightness(tile).enhance(shade)
            paint_face(pixels, tile, [project(p) for p in corners])

    canvas = Image.new("RGB", (VIEW_WIDTH, VIEW_HEIGHT), BACKGROUND)
    screen = canvas.load()
    for point, fragments in pixels.items():
        color = BACKGROUND
        for _, (r, g, b, a) in sorted(fragments):
            color = tuple((old * (255 - a) + new * a + 127) // 255 for old, new in zip(color, (r, g, b)))
        screen[point] = color
    return canvas


def preview(skin, slim, scale=1.0):
    if skin.size != (64, 64):
        raise ValueError(f"expected a 64×64 skin, got {skin.width}×{skin.height}")
    skin = skin.convert("RGBA")
    canvas = Image.new("RGB", (VIEW_WIDTH * 2, VIEW_HEIGHT + 18), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    # Use Pillow's embedded bitmap font for consistent labels across systems.
    font = getattr(ImageFont, "load_default_imagefont", ImageFont.load_default)()
    for i, (yaw, name) in enumerate([(-26, "Front"), (154, "Back")]):
        canvas.paste(view(skin, slim, yaw, scale), (VIEW_WIDTH * i, 0))
        x = round(VIEW_WIDTH * (i + 0.5) - draw.textlength(name, font=font) / 2)
        draw.text((x, VIEW_HEIGHT), name, font=font, fill=(205, 209, 219))
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report stale or missing previews without writing")
    parser.add_argument("ids", nargs="*", help="NPC ids; by default render the entire roster")
    args = parser.parse_args()
    ids = args.ids or list(SKINS)
    unknown = set(ids).difference(SKINS)
    if unknown:
        parser.error("unknown skin ids: " + ", ".join(sorted(unknown)))
    if not args.check:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    stale = []
    for npc in ids:
        with Image.open(TARGET / f"{npc}.png") as skin:
            output = PREVIEW_DIR / f"{npc}.png"
            spec = SKINS[npc]
            render = preview(skin, spec["slim"], spec.get("scale", 1.0))
        if args.check:
            if output.is_file():
                with Image.open(output) as current:
                    if current.mode == render.mode and current.size == render.size:
                        if ImageChops.difference(current, render).getbbox() is None:
                            continue
            stale.append(str(output.relative_to(ROOT)))
        else:
            render.save(output)
            print(output.relative_to(ROOT))
    if stale:
        raise SystemExit("Stale or missing previews: " + ", ".join(stale))


if __name__ == "__main__":
    main()
