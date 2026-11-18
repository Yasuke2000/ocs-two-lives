#!/usr/bin/env python3
"""Generate original Two Lives faction emblems, BlueMap pins and their illustrated key.

Run with Python 3.11+ and Pillow 10.1+. --check compares decoded pixels, so PNG
compression settings do not change the verdict. Artwork is drawn on integer grids.
"""

import argparse
from pathlib import Path
import tomllib

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "pack/kubejs/assets/ttl/textures/heraldry"
MAP = ROOT / "pack/config/bluemap/web/assets/ttl"
WEB = ROOT / "pack/bluemap/web/assets/ttl"
SHEET = ROOT / "docs/previews/heraldry.png"
INK = "#252430"
CLOTH = {
    "black": "#222328",
    "blue": "#39468b",
    "cyan": "#258984",
    "green": "#5c7732",
    "light_blue": "#5fb9da",
    "lime": "#86be41",
    "magenta": "#bf5da3",
    "orange": "#db8334",
    "purple": "#804997",
    "red": "#ad3d3c",
    "white": "#ece6d9",
    "yellow": "#e2bb49",
}
# Label, enamel and raised metal. All nine keep their own silhouette at native size.
PINS = {
    "town": ("Town", "#387861", "#fbdfb0"),
    "capital": ("Capital", "#984e44", "#ffe3ac"),
    "canon_build": ("Canon build", "#547e95", "#e7eed9"),
    "landmark": ("Landmark", "#5a7665", "#f2e6a3"),
    "boss_lair": ("Boss lair", "#974453", "#ffcf8e"),
    "arena": ("Arena", "#815b92", "#f9d0ba"),
    "spirit_gate": ("Spirit gate", "#24878c", "#c0fff1"),
    "walpurgis_gate": ("Walpurgis gate", "#583c72", "#f7b5da"),
    "nation_capital": ("Player nation capital", "#415a82", "#fbd886"),
}


def shield(faction):
    img = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(img)
    dark, field, accent, light = faction["palette"]
    # Engraved rim with one pixel of edge shadow and a bright upper lip.
    d.polygon(
        [(2, 2), (29, 2), (29, 18), (27, 23), (21, 28), (16, 31), (10, 28), (4, 23), (2, 18)], fill=INK
    )
    d.polygon(
        [(3, 3), (28, 3), (28, 18), (26, 22), (20, 27), (16, 29), (11, 27), (5, 22), (3, 18)], fill=light
    )
    d.polygon(
        [(5, 5), (26, 5), (26, 17), (24, 21), (19, 25), (16, 27), (12, 25), (7, 21), (5, 17)], fill=dark
    )
    d.polygon([(6, 6), (25, 6), (25, 16), (22, 21), (16, 25), (11, 22), (7, 18)], fill=field)
    id = faction["id"]
    if id == "tempest":
        d.polygon(
            [
                (6, 11),
                (12, 9),
                (10, 11),
                (17, 10),
                (20, 8),
                (25, 7),
                (22, 11),
                (18, 13),
                (12, 14),
                (9, 16),
                (8, 15),
            ],
            fill=light,
        )
        d.polygon([(23, 12), (23, 16), (19, 20), (13, 21), (9, 19), (17, 18), (20, 16)], fill=accent)
        d.rectangle((13, 15, 16, 16), fill=light)
    elif id == "dwargon":
        d.polygon(
            [
                (7, 13),
                (12, 13),
                (13, 12),
                (23, 12),
                (22, 15),
                (18, 17),
                (18, 19),
                (21, 21),
                (11, 21),
                (14, 19),
                (14, 17),
                (10, 16),
            ],
            fill=accent,
        )
        d.line((13, 12, 23, 12), fill=light)
        for pt in [(15, 7), (11, 9), (20, 8), (17, 9)]:
            d.point(pt, fill=light)
    elif id == "blumund":
        d.line((15, 22, 16, 11), fill=light, width=2)
        d.polygon([(16, 7), (18, 9), (17, 12), (15, 12), (14, 10)], fill=light)
        for y in (11, 15, 19):
            d.polygon([(10, y - 2), (13, y - 1), (15, y + 2), (12, y + 1), (10, y)], fill=accent)
            d.polygon([(21, y - 3), (21, y), (17, y + 2), (17, y)], fill=light)
    elif id == "falmuth":
        d.polygon([(9, 8), (12, 10), (15, 7), (18, 10), (22, 8), (21, 12), (10, 12)], fill=light)
        d.rectangle((7, 15, 24, 17), fill=accent)
        for x in (8, 15, 22):
            d.rectangle((x, 17, x + 1, 20), fill=accent)
        d.line((10, 15, 21, 15), fill=light)
    elif id == "holy_church":
        d.polygon(
            [
                (15, 6),
                (17, 8),
                (17, 11),
                (20, 11),
                (22, 13),
                (20, 15),
                (17, 15),
                (17, 20),
                (15, 23),
                (14, 20),
                (14, 15),
                (11, 15),
                (9, 13),
                (11, 11),
                (14, 11),
                (14, 8),
            ],
            fill=dark,
        )
        d.line((15, 9, 15, 20), fill=accent, width=2)
        d.line((11, 13, 20, 13), fill=accent, width=2)
        d.rectangle((15, 12, 16, 13), fill="#91d8da")
    elif id == "orc_horde":
        for side in (-1, 1):

            def mirror(points):
                return [(16 + side * x, y) for x, y in points]

            d.polygon(mirror([(8, 8), (8, 15), (6, 19), (2, 20), (2, 17), (5, 16), (6, 13)]), fill=light)
        d.polygon([(12, 15), (15, 13), (18, 13), (20, 15), (19, 18), (13, 18)], fill=accent)
        d.point((14, 16), fill=INK)
        d.point((17, 16), fill=INK)
    elif id == "lizardmen":
        for x, y in ((11, 10), (16, 7), (21, 10)):
            d.line((x, 16, x, y + 1), fill=accent)
            d.polygon([(x - 1, y), (x, y - 2), (x + 1, y), (x + 1, y + 2), (x - 1, y + 2)], fill=light)
        for y in (17, 21):
            d.line(
                [(8, y - 1), (11, y + 1), (14, y + 1), (17, y - 1), (20, y - 1), (23, y + 1)],
                fill=light if y == 17 else accent,
                width=2,
            )
    elif id == "outcast":
        d.polygon(
            [(16, 7), (18, 12), (24, 14), (19, 16), (16, 22), (14, 17), (8, 15), (13, 12)], fill=light
        )
        d.polygon([(17, 11), (19, 14), (16, 17), (13, 15)], fill=field)
        d.line([(8, 7), (13, 12), (12, 14), (18, 18), (22, 23)], fill=dark, width=2)
        d.point((23, 9), fill=accent)
    else:
        raise ValueError(f"No shield drawing for {id}")
    return img


def pin(id):
    _, field, light = PINS[id]
    img = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(img)
    d.polygon(
        [
            (3, 7),
            (7, 3),
            (24, 3),
            (28, 7),
            (28, 19),
            (24, 23),
            (20, 23),
            (16, 30),
            (12, 23),
            (8, 23),
            (3, 19),
        ],
        fill=INK,
    )
    d.polygon(
        [
            (5, 8),
            (8, 5),
            (23, 5),
            (26, 8),
            (26, 18),
            (23, 21),
            (19, 21),
            (16, 26),
            (13, 21),
            (9, 21),
            (5, 18),
        ],
        fill=field,
    )
    d.line([(6, 9), (9, 6), (22, 6)], fill=light)

    def polygon(points):
        d.polygon(points, fill=light)

    def box(bounds):
        d.rectangle(bounds, fill=light)

    if id == "town":
        polygon([(7, 14), (12, 9), (17, 14)])
        box((9, 15, 15, 18))
        polygon([(15, 13), (20, 8), (25, 13)])
        box((17, 14, 22, 18))
        d.line((12, 16, 12, 18), fill=field)
        d.point((19, 15), fill=field)
    elif id == "capital":
        polygon([(8, 10), (12, 13), (16, 8), (20, 13), (24, 10), (22, 17), (10, 17)])
        box((10, 18, 22, 19))
        d.point((16, 13), fill=field)
    elif id == "canon_build":
        for x in (8, 14, 20):
            box((x, 9, x + 3, 12))
        box((8, 12, 23, 18))
        d.rectangle((14, 15, 17, 18), fill=field)
        d.line((10, 14, 11, 14), fill=field)
        d.line((20, 14, 21, 14), fill=field)
    elif id == "landmark":
        polygon([(7, 18), (14, 9), (17, 13), (19, 10), (25, 18)])
        d.polygon([(10, 16), (14, 11), (16, 14), (14, 13)], fill=field)
    elif id == "boss_lair":
        polygon(
            [
                (7, 8),
                (12, 12),
                (14, 10),
                (18, 10),
                (20, 12),
                (25, 8),
                (23, 15),
                (20, 17),
                (17, 19),
                (14, 19),
                (11, 17),
                (9, 15),
            ]
        )
        d.line((11, 13, 14, 15), fill=field, width=2)
        d.line((20, 13, 17, 15), fill=field, width=2)
        d.point((16, 17), fill=field)
    elif id == "arena":
        for x in (10, 21):
            sign = 1 if x == 10 else -1
            polygon(
                [(x, 8), (x + sign * 4, 10), (x + sign * 10, 17), (x + sign * 8, 18), (x + sign, 11)]
            )
            d.line((x + sign * 7, 18, x + sign * 11, 15), fill=light, width=2)
    elif id == "spirit_gate":
        d.arc((8, 8, 23, 21), 180, 360, fill=light, width=2)
        for x in (8, 22):
            box((x, 14, x + 1, 19))
        polygon([(16, 10), (19, 14), (16, 18), (13, 14)])
    elif id == "walpurgis_gate":
        polygon([(7, 8), (12, 11), (12, 18), (9, 19)])
        polygon([(24, 8), (19, 11), (19, 18), (22, 19)])
        polygon([(16, 8), (18, 12), (16, 15), (14, 12)])
        box((15, 17, 16, 18))
    elif id == "nation_capital":
        box((11, 8, 12, 19))
        polygon([(13, 8), (22, 8), (19, 11), (22, 13), (13, 13)])
        box((9, 18, 23, 19))
        box((16, 15, 18, 17))
    return img


def banner(faction):
    """A loom diagram drawn from geometric primitives. Minecraft supplies the actual cloth textures."""
    w, h = 20, 40
    img = Image.new("RGB", (w, h), CLOTH[faction["base"]])
    d = ImageDraw.Draw(img)
    for layer in faction["layers"]:
        p = layer["pattern"].removeprefix("minecraft:")
        c = CLOTH[layer["color"]]
        if p == "circle":
            d.ellipse((5, 14, 14, 24), fill=c)
        elif p == "rhombus":
            d.polygon([(10, 7), (17, 19), (10, 32), (2, 19)], fill=c)
        elif p == "border":
            d.rectangle((0, 0, w - 1, h - 1), outline=c, width=2)
        elif p == "stripe_top":
            d.rectangle((0, 0, 19, 6), fill=c)
        elif p == "stripe_bottom":
            d.rectangle((0, 33, 19, 39), fill=c)
        elif p == "stripe_middle":
            d.rectangle((0, 17, 19, 23), fill=c)
        elif p == "stripe_center":
            d.rectangle((8, 0, 12, 39), fill=c)
        elif p == "straight_cross":
            d.rectangle((8, 0, 12, 39), fill=c)
            d.rectangle((0, 17, 19, 22), fill=c)
        elif p == "small_stripes":
            for x in range(1, w, 5):
                d.rectangle((x, 0, x + 1, 39), fill=c)
        elif p == "half_horizontal_bottom":
            d.rectangle((0, 20, 19, 39), fill=c)
        elif p == "triangle_bottom":
            d.polygon([(0, 39), (10, 21), (19, 39)], fill=c)
        elif p == "triangle_top":
            d.polygon([(0, 0), (10, 19), (19, 0)], fill=c)
        elif p in ("triangles_top", "triangles_bottom"):
            y, tip = (0, 8) if p == "triangles_top" else (39, 31)
            for x in range(-3, 20, 8):
                d.polygon([(x, y), (x + 4, tip), (x + 8, y)], fill=c)
        elif p == "bricks":
            for y in range(0, h, 6):
                for x in range(-7 if y % 12 else -2, w, 10):
                    d.rectangle((x, y, x + 7, y + 3), fill=c)
        elif p == "stripe_downright":
            d.polygon([(0, 0), (3, 0), (19, 33), (19, 39), (16, 39), (0, 6)], fill=c)
        elif p == "flow":
            d.line(
                [
                    (2, 25),
                    (6, 29),
                    (13, 28),
                    (17, 23),
                    (17, 17),
                    (14, 13),
                    (8, 13),
                    (6, 16),
                    (7, 21),
                    (11, 22),
                    (13, 19),
                ],
                fill=c,
                width=2,
            )
        else:
            raise ValueError(f"No banner diagram for {p}")
    return img


def key_sheet(factions, badges, pins):
    sheet = Image.new("RGB", (1064, 795), "#f2ebdd")
    d = ImageDraw.Draw(sheet)

    def label(x, y, s, size, fill=INK):
        d.text((x, y), s, font=ImageFont.load_default(size=size), fill=fill)

    def place(im, x, y, w, h):
        scaled = im.resize((w, h), Image.Resampling.NEAREST)
        sheet.paste(scaled, (x, y), scaled if im.mode == "RGBA" else None)

    label(32, 20, "Heraldry of the Two Lives", 39)
    label(34, 72, "Faction emblems and their loom patterns", 20, "#665948")
    for i, f in enumerate(factions):
        x, y = 32 + (i % 4) * 250, 118 + (i // 4) * 201
        d.rectangle((x, y, x + 239, y + 188), fill="#fcf8ee")
        place(badges[f["id"]], x + 31, y + 8, 108, 108)
        place(banner(f), x + 165, y + 18, 40, 80)
        d.line((x + 160, y + 16, x + 209, y + 16), fill="#76624f", width=3)
        label(x + 15, y + 120, f["id"].replace("_", " ").title(), 20)
        label(x + 15, y + 152, f["title"], 17, "#665948")
    label(32, 533, "BlueMap marker key", 27)
    for i, (id, img) in enumerate(pins.items()):
        x, y = 34 + (i % 5) * 202, 580 + (i // 5) * 86
        place(img, x, y, 60, 60)
        name = PINS[id][0]
        if id == "nation_capital":
            label(x + 63, y + 11, "Player nation", 16)
            label(x + 63, y + 30, "capital", 16)
        else:
            label(x + 63, y + 18, name, 16)
    return sheet


def render():
    data = tomllib.loads((ROOT / "design/data/heraldry.toml").read_text(encoding="utf-8"))["faction"]
    ids = [f["id"] for f in data]
    registry = tomllib.loads((ROOT / "design/data/factions.toml").read_text(encoding="utf-8"))["faction"]
    if len(set(ids)) != len(ids) or set(ids) != {f["id"] for f in registry}:
        raise ValueError("Heraldry needs exactly one emblem per reputation faction")
    badges = {f["id"]: shield(f) for f in data}
    pins = {name: pin(name) for name in PINS}
    images = {}
    for f in data:
        id = f["id"]
        prefix = "/give @s minecraft:" + f["base"] + "_banner[minecraft:banner_patterns=["
        layers = ",".join(
            '{pattern:"' + l["pattern"] + '",color:"' + l["color"] + '"}' for l in f["layers"]
        )
        if f["give"] != prefix + layers + "]] 1" or not 1 <= len(f["layers"]) <= 6:
            raise ValueError(f"{id}: inconsistent banner command or layer count")
        for n in (32, 64):
            images[GAME / f"{id}_{n}.png"] = badges[id].resize((n, n), Image.Resampling.NEAREST)
    for id, img in pins.items():
        for dest in (MAP, WEB):
            images[dest / f"{id}.png"] = img
    images[SHEET] = key_sheet(data, badges, pins)
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, img in render().items():
        if args.check:
            if path.exists():
                with Image.open(path) as actual:
                    if (
                        actual.mode == img.mode
                        and actual.size == img.size
                        and actual.tobytes() == img.tobytes()
                    ):
                        continue
            stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            img.save(path, optimize=True)
    if stale:
        raise SystemExit("Stale heraldry: " + ", ".join(stale))
    print("heraldry checked" if args.check else "heraldry generated")


if __name__ == "__main__":
    main()
