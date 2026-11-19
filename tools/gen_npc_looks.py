#!/usr/bin/env python3
"""Compose the generic NPC skins (adventurers, merchants, dwarves, goblins, church, knights) from parts.

Every variant in tools/npc_looks.py LOOKS without a `texture` becomes a 64x64 player skin
pack/kubejs/assets/ttl/textures/entity/npc/look_<look>_<n>.png. The parts, drawn in this order:
  head      skin tone and face per race (human, dwarf, goblin, hobgoblin, kijin, lizard), hair style, beard
  garment   tunic | jerkin | chain | plate | robe | coat | apron | kimono | rags | vest: torso, sleeves and legs
  details   belt and buckle, tabard with emblem, shoulder strap (sash), guild rank plate (badge), dwarf beard on the chest
  outer     backpack, cloak (shoulders, back, outer sleeves, to the knees), pauldrons, gloves
  headgear  hood | coif | helm | cap | bandana | horns, last so it sits over the hair
The look is deliberately plain: flat colours with the same woven grain as tools/gen_skins.py, a few texels of detail.

Usage: gen_npc_looks.py            write the PNGs and docs/previews/npc_skins.png (the contact sheet)
       gen_npc_looks.py --check    exit 1 when a PNG differs from what the catalogue draws (needs Pillow)
"""
import argparse
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import npc_looks  # noqa: E402
from gen_skins import PARTS, face_boxes, shade  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / npc_looks.ASSET_DIR
SHEET = ROOT / "docs" / "previews" / "npc_skins.png"
SIDES = ("front", "right", "back", "left")
OUTER = {part: outer for part, (_, _, outer, _) in PARTS.items()}


def rgb(hex_color: str) -> tuple:
    return ImageColor.getrgb(hex_color)


def mix(color: str, factor: float) -> str:
    """Darker (factor < 1) or lighter (factor > 1) version of a colour."""
    r, g, b = rgb(color)
    if factor <= 1:
        return "#%02x%02x%02x" % tuple(round(c * factor) for c in (r, g, b))
    return "#%02x%02x%02x" % tuple(round(c + (255 - c) * (factor - 1)) for c in (r, g, b))


class Skin:
    """Two layers (base, over) of per-face texel grids; None is unpainted (transparent on the over layer)."""

    def __init__(self, slim: bool):
        self.slim = slim
        self.dims = {}
        self.grid = {"base": {}, "over": {}}
        for part, (_, _, _, (w, h, d)) in PARTS.items():
            if slim and part.endswith("_arm"):
                w = 3
            self.dims[part] = (w, h, d)
            for layer in self.grid:
                self.grid[layer][part] = {face: [[None] * (x1 - x0) for _ in range(y1 - y0)]
                                          for face, (x0, y0, x1, y1) in face_boxes((0, 0), w, h, d).items()}

    def size(self, part, face):
        g = self.grid["base"][part][face]
        return len(g[0]), len(g)

    def put(self, part, face, x, y, color, layer="base", flat=False):
        w, h = self.size(part, face)
        if color and 0 <= x < w and 0 <= y < h:
            self.grid[layer][part][face][y][x] = (color, flat)

    def fill(self, part, color, layer="base", faces=None):
        for face in faces or self.grid[layer][part]:
            w, h = self.size(part, face)
            for y in range(h):
                for x in range(w):
                    self.put(part, face, x, y, color, layer)

    def band(self, part, y0, y1, color, layer="base", faces=SIDES):
        for face in faces:
            w, h = self.size(part, face)
            for y in range(y0, min(y1, h)):
                for x in range(w):
                    self.put(part, face, x, y, color, layer)

    def get(self, part, face, x, y, layer="base"):
        cell = self.grid[layer][part][face][y][x]
        return cell[0] if cell else None

    def render(self) -> Image.Image:
        image = Image.new("RGBA", (64, 64))
        for part, (base, outer, _, _) in PARTS.items():
            w, h, d = self.dims[part]
            for layer, origin in (("base", base), ("over", outer)):
                for face, (u, v, _, _) in face_boxes(origin, w, h, d).items():
                    for y, row in enumerate(self.grid[layer][part][face]):
                        for x, cell in enumerate(row):
                            if cell:
                                color, flat = cell
                                value = rgb(color) if flat else shade(rgb(color), face, x, y)
                                image.putpixel((u + x, v + y), (*value, 255))
        return image


# ---- head ----------------------------------------------------------------------------------------------------------

def side_cols(face, near_front, width=8):
    """Columns of a head side face: near_front=True gives the half next to the face."""
    half = range(width // 2, width) if (face == "right") == near_front else range(0, width // 2)
    return list(half)


def draw_hair(sk: Skin, s: dict):
    hair, style = s.get("hair"), s.get("hair_style", "short")
    if not hair or s["race"] == "lizard":
        return
    streak = mix(hair, 0.82)

    def h(face, x, y, layer="base"):
        sk.put("head", face, x, y, streak if (x * 3 + y) % 5 == 0 else hair, layer)

    if style == "bald":
        for face in ("right", "left"):
            for y in (3, 4, 5):
                for x in side_cols(face, False):
                    h(face, x, y)
        for y in (3, 4, 5, 6):
            for x in range(8):
                h("back", x, y)
        return
    for y in range(8):
        for x in range(8):
            h("top", x, y)
    depth = {"crop": 6, "short": 7, "swept": 7, "tied": 7, "long": 8}[style]
    for y in range(depth):
        for x in range(8):
            h("back", x, y)
    for face in ("right", "left"):
        cheek = 7 if face == "right" else 0
        for y in range(8):
            for x in range(8):
                if style == "long":
                    if not (x == cheek and y >= 3):
                        h(face, x, y)
                elif y < (2 if style == "crop" else 3) or (x not in side_cols(face, True) and y < depth - 1):
                    h(face, x, y)
    rows = {"crop": [range(8), (0, 1, 6, 7)], "short": [range(8), range(8), (0, 7)],
            "swept": [range(8), (0, 1, 2, 5, 6, 7), (0, 7)], "tied": [range(8), (0, 1, 2, 3, 6, 7), (0, 7)],
            "long": [range(8), range(8)] + [(0, 7)] * 6}[style]
    for y, xs in enumerate(rows):
        for x in xs:
            h("front", x, y)
    if style == "tied":
        for y in range(3, 8):
            for x in (3, 4):
                sk.put("head", "back", x, y, streak if y % 2 else hair, "over")
        sk.put("head", "back", 3, 3, s.get("trim", streak), "over", flat=True)
        sk.put("head", "back", 4, 3, s.get("trim", streak), "over", flat=True)


def draw_face(sk: Skin, s: dict):
    race, skin = s["race"], s["skin"]
    eyes = s.get("eyes", "#3a2a22")
    f = lambda x, y, c: sk.put("head", "front", x, y, c, flat=True)  # noqa: E731
    brow = mix(s.get("hair") or skin, 0.7)
    if race == "lizard":
        scale = mix(skin, 0.85)
        for face in sk.grid["base"]["head"]:
            w, hgt = sk.size("head", face)
            for y in range(hgt):
                for x in range(w):
                    if (x + 2 * y) % 4 == 0:
                        sk.put("head", face, x, y, scale)
        belly = s.get("second", "#c9c48a")
        for y in (5, 6, 7):
            for x in range(1, 7):
                sk.put("head", "front", x, y, belly)
        for x in range(8):
            sk.put("head", "bottom", x, 7 - x // 4, belly)
        f(2, 5, "#1e2a20"), f(5, 5, "#1e2a20")              # nostrils
        for x in range(0, 8):
            f(x, 6, mix(belly, 0.62) if x in (0, 7) else mix(belly, 0.75))  # the jaw line
        f(2, 7, "#efe8d0"), f(5, 7, "#efe8d0")              # teeth
        f(1, 3, mix(skin, 0.6)), f(6, 3, mix(skin, 0.6))   # brow ridges
        f(1, 4, eyes), f(2, 4, "#141414"), f(5, 4, "#141414"), f(6, 4, eyes)
        crest = s.get("hair", mix(skin, 0.6))
        for y in range(8):
            sk.put("head", "top", 3, y, crest, "over"), sk.put("head", "top", 4, y, crest, "over")
            if y < 7 and y % 2 == 0:
                sk.put("head", "back", 3, y, crest, "over"), sk.put("head", "back", 4, y, crest, "over")
        return
    if race == "goblin":
        f(1, 3, brow), f(2, 3, skin), f(5, 3, skin), f(6, 3, brow)
        f(1, 4, eyes), f(2, 4, "#161616"), f(5, 4, "#161616"), f(6, 4, eyes)
        f(3, 4, mix(skin, 0.8)), f(4, 4, mix(skin, 0.8))
        f(3, 5, mix(skin, 0.7)), f(4, 5, mix(skin, 0.7))
        for x in range(2, 6):
            f(x, 6, "#3a1e1a")
        f(2, 6, "#e8e0c8"), f(5, 6, "#e8e0c8")             # fangs
        draw_ears(sk, skin, long=True)
        return
    f(1, 3, brow), f(2, 3, brow), f(5, 3, brow), f(6, 3, brow)
    if race == "dwarf":
        f(0, 3, brow), f(7, 3, brow)
    f(1, 4, "#f2efe8"), f(2, 4, eyes), f(5, 4, eyes), f(6, 4, "#f2efe8")
    nose = mix(skin, 0.86) if race != "dwarf" else mix(skin, 0.78)
    f(3, 5, nose), f(4, 5, nose)
    if race == "dwarf":
        f(3, 4, mix(skin, 0.9)), f(4, 4, mix(skin, 0.9))
    f(3, 6, mix(skin, 0.7)), f(4, 6, mix(skin, 0.7))
    if race == "hobgoblin":
        f(4, 6, "#e8e0c8")
        draw_ears(sk, skin, long=False)
    if race == "kijin":
        f(3, 6, mix(skin, 0.75))


def draw_ears(sk: Skin, skin: str, long: bool):
    """Pointed ears on the hat layer of the head's sides, sweeping back from the cheek."""
    shape = {3: (2, 3, 4), 4: (1, 2, 3, 4, 5), 5: (3, 4, 5)} if long else {4: (3, 4), 5: (3, 4, 5)}
    for y, xs in shape.items():
        for x in xs:
            sk.put("head", "right", 7 - x, y, skin, "over")
            sk.put("head", "left", x, y, skin, "over")


def draw_beard(sk: Skin, s: dict):
    beard, style = s.get("beard"), s.get("beard_style", "full")
    if not beard:
        return
    dark = mix(beard, 0.8)
    f = lambda x, y, c=beard: sk.put("head", "front", x, y, c)  # noqa: E731
    if style == "full":
        for y in (5, 6, 7):
            for x in range(8):
                f(x, y)
        f(0, 4), f(7, 4)
        f(3, 6, dark), f(4, 6, dark)
        for face in ("right", "left"):
            for y in (4, 5, 6, 7):
                for x in side_cols(face, True):
                    sk.put("head", face, x, y, beard)
        sk.fill("head", beard, faces=("bottom",))
        for y in (6, 7):
            for x in range(1, 7):
                sk.put("head", "front", x, y, beard if (x + y) % 3 else dark, "over")
        if s["race"] == "dwarf":  # the long dwarf beard falls onto the chest
            for y, xs in ((0, range(1, 7)), (1, range(1, 7)), (2, range(2, 6)), (3, (3, 4))):
                for x in xs:
                    sk.put("body", "front", x, y, beard if (x + y) % 3 else dark)
    elif style == "short":
        for x in range(8):
            f(x, 7)
        f(0, 6), f(7, 6), f(0, 5), f(7, 5), f(1, 6), f(6, 6)
        f(3, 6, mix(s["skin"], 0.7)), f(4, 6, mix(s["skin"], 0.7))
    elif style == "goatee":
        f(3, 7), f(4, 7), f(2, 6), f(5, 6), f(3, 6, dark), f(4, 6, dark)
    elif style == "moustache":
        for x in (1, 2, 3, 4, 5, 6):
            f(x, 6)
        f(3, 7, mix(s["skin"], 0.7)), f(4, 7, mix(s["skin"], 0.7))


def draw_headgear(sk: Skin, s: dict):
    gear, color = s.get("head"), s.get("head_color")
    if not gear:
        return
    edge = mix(color, 0.75)
    if gear in ("hood", "coif"):
        weave = (lambda x, y: color if (x + y) % 2 else mix(color, 0.82)) if gear == "coif" else (lambda x, y: color)
        for face in ("top", "back", "right", "left"):
            w, h = sk.size("head", face)
            for y in range(h):
                for x in range(w):
                    sk.put("head", face, x, y, weave(x, y), "over")
        for y in range(8):
            for x in range(8):
                if y < 2 or x in (0, 7):
                    sk.put("head", "front", x, y, edge if (y == 1 and 0 < x < 7) or (x in (0, 7) and y >= 1) else weave(x, y),
                           "over")
        for x in range(1, 7):  # shadow under the rim
            sk.put("head", "front", x, 2, mix(s["skin"], 0.72))
    elif gear == "helm":
        rim = mix(color, 0.7)
        sk.fill("head", color, faces=("top",))
        for face, rows in (("front", 2), ("right", 3), ("left", 3), ("back", 4)):
            sk.band("head", 0, rows, color, faces=(face,))
            sk.band("head", rows, rows + 1, rim, faces=(face,))
        for y in (2, 3, 4):
            sk.put("head", "front", 3, y, color, "over"), sk.put("head", "front", 4, y, color, "over")
        sk.put("head", "front", 3, 0, mix(color, 1.25), flat=True), sk.put("head", "front", 4, 0, mix(color, 1.25), flat=True)
    elif gear == "cap":
        sk.fill("head", color, faces=("top",))
        for face in SIDES:
            sk.band("head", 0, 1, color, faces=(face,))
            sk.band("head", 1, 2, edge, faces=(face,))
        feather = s.get("trim", "#e8e0c8")
        for y, x in ((0, 6), (0, 7), (1, 6), (2, 5)):
            sk.put("head", "right", x - 2, y, feather, "over", flat=True)
    elif gear == "bandana":
        for face in SIDES:
            sk.band("head", 1, 3, color, faces=(face,))
        sk.fill("head", color, faces=("top",))
        for y in (3, 4, 5):
            sk.put("head", "back", 3, y, edge, "over"), sk.put("head", "back", 4, y, color, "over")
    elif gear == "horns":
        for x in (1, 6):
            sk.put("head", "front", x, 0, color, "over", flat=True)
            sk.put("head", "front", x, 1, mix(color, 0.85), "over", flat=True)
            sk.put("head", "top", x, 7, color, "over", flat=True)
            sk.put("head", "top", x, 6, mix(color, 0.85), "over", flat=True)


# ---- body ----------------------------------------------------------------------------------------------------------

def arms():
    return ("right_arm", "left_arm")


def legs():
    return ("right_leg", "left_leg")


def outer_face(arm):
    return "right" if arm == "right_arm" else "left"


def draw_limbs(sk: Skin, s: dict, sleeve: str, sleeve_rows: int, cuff: str | None, leg: str, boot_from: int):
    skin = s["skin"]
    for arm in arms():
        sk.fill(arm, skin)
        sk.band(arm, 0, sleeve_rows, sleeve)
        sk.fill(arm, sleeve, faces=("top",))
        if cuff:
            sk.band(arm, sleeve_rows - 1, sleeve_rows, cuff)
    boots = s.get("boots", "#4a3324")
    for lg in legs():
        sk.fill(lg, leg)
        sk.band(lg, boot_from, 12, boots)
        sk.band(lg, boot_from, boot_from + 1, mix(boots, 1.15))
        sk.fill(lg, mix(boots, 0.8), faces=("bottom",))


def draw_garment(sk: Skin, s: dict):
    body = s.get("body", "tunic")
    main, second, trim = s.get("main", "#7a6a4a"), s.get("second", "#d8ccb0"), s.get("trim", "#5a4a32")
    legs_c = s.get("legs", "#5a5040")
    skin = s["skin"]
    sk.fill("body", main)
    if body == "tunic":
        draw_limbs(sk, s, main, 10, trim, legs_c, 8)
        sk.put("body", "front", 3, 0, skin), sk.put("body", "front", 4, 0, skin)
        sk.put("body", "front", 3, 1, second), sk.put("body", "front", 4, 1, second)
        sk.put("body", "front", 2, 0, trim), sk.put("body", "front", 5, 0, trim)
        sk.band("body", 11, 12, mix(main, 0.8))
    elif body == "jerkin":
        draw_limbs(sk, s, second, 9, mix(second, 0.8), legs_c, 8)
        for y in range(1, 8):
            sk.put("body", "front", 3, y, mix(main, 0.7) if y % 2 else trim, flat=True)
            sk.put("body", "front", 4, y, trim if y % 2 else mix(main, 0.7), flat=True)
        sk.put("body", "front", 3, 0, second), sk.put("body", "front", 4, 0, second)
        sk.band("body", 10, 12, second)
        for arm in arms():  # leather shoulder caps
            sk.band(arm, 0, 2, main)
    elif body == "chain":
        sk.band("body", 0, 10, main)
        for face in SIDES:
            w, _ = sk.size("body", face)
            for y in range(0, 10):
                for x in range(w):
                    if (x + y) % 2:
                        sk.put("body", face, x, y, mix(main, 0.78))
        sk.band("body", 10, 12, second)
        draw_limbs(sk, s, main, 8, second, legs_c, 8)
        for arm in arms():
            for face in SIDES:
                w, _ = sk.size(arm, face)
                for y in range(0, 7):
                    for x in range(w):
                        if (x + y) % 2:
                            sk.put(arm, face, x, y, mix(main, 0.78))
        sk.put("body", "front", 3, 0, trim), sk.put("body", "front", 4, 0, trim)
    elif body == "plate":
        light, dark = mix(main, 1.25), mix(main, 0.72)
        for y in range(0, 8):
            sk.put("body", "front", 0, y, dark), sk.put("body", "front", 7, y, dark)
            if 1 <= y <= 6:
                sk.put("body", "front", 3, y, light), sk.put("body", "front", 4, y, light)
        sk.band("body", 7, 8, trim)
        for y in range(8, 12):
            sk.band("body", y, y + 1, main if y % 2 == 0 else dark)
        draw_limbs(sk, s, main, 9, trim, legs_c, 6)
        for arm in arms():
            sk.band(arm, 0, 3, light)
            sk.band(arm, 3, 4, trim)
            sk.band(arm, 9, 12, mix(main, 0.85))
        for lg in legs():
            sk.band(lg, 6, 7, trim)
            sk.put(lg, "front", 1, 8, light), sk.put(lg, "front", 2, 8, light)
    elif body == "robe":
        draw_limbs(sk, s, main, 10, trim, main, 11)
        for lg in legs():
            sk.band(lg, 10, 11, trim)
        for y in range(12):
            sk.put("body", "front", 4, y, trim)
        for y in range(10):
            sk.put("right_leg", "front", 3, y, trim), sk.put("left_leg", "front", 0, y, trim)
        for x in (2, 3, 4, 5):
            sk.put("body", "front", x, 0, trim)
        sk.put("body", "front", 3, 1, second), sk.put("body", "front", 3, 2, second)
        s = dict(s, belt_row=7)
    elif body == "coat":
        draw_limbs(sk, s, main, 10, trim, legs_c, 8)
        for y in range(1, 10):
            for x in (3, 4):
                sk.put("body", "front", x, y, second)
        for y in range(0, 4):
            sk.put("body", "front", 2, y, trim), sk.put("body", "front", 5, y, trim)
        for y in (4, 6):
            sk.put("body", "front", 2, y, mix(trim, 1.2), flat=True)
        sk.put("body", "front", 3, 0, skin), sk.put("body", "front", 4, 0, skin)
        for lg in legs():  # coat tails
            sk.band(lg, 0, 5, main, faces=("back", outer_face(lg.replace("leg", "arm"))))
        for y in range(5):
            for x in (0, 1):
                sk.put("right_leg", "front", x, y, main), sk.put("left_leg", "front", 3 - x, y, main)
            sk.put("right_leg", "front", 1, y, trim), sk.put("left_leg", "front", 2, y, trim)
    elif body == "apron":
        sk.fill("body", second)
        draw_limbs(sk, s, second, 6, mix(second, 0.8), legs_c, 8)
        for y in range(2, 12):
            for x in range(1, 7):
                sk.put("body", "front", x, y, main)
        for y in (0, 1):
            sk.put("body", "front", 1, y, main), sk.put("body", "front", 6, y, main)
        sk.band("body", 7, 8, main, faces=("back", "right", "left"))
        for y in range(0, 7):
            for x in (1, 2, 3):
                sk.put("right_leg", "front", x, y, main), sk.put("left_leg", "front", x - 1, y, main)
        sk.put("body", "front", 4, 5, trim, flat=True), sk.put("body", "front", 5, 5, trim, flat=True)
        s = dict(s, belt=None)
    elif body == "kimono":
        draw_limbs(sk, s, main, 10, mix(main, 0.8), legs_c, 11)
        for y, x in ((0, 2), (1, 2), (2, 3), (3, 3), (4, 4), (5, 4), (6, 4)):
            sk.put("body", "front", x, y, second)
        for y, x in ((0, 5), (1, 5), (2, 4)):
            sk.put("body", "front", x, y, second)
        sk.put("body", "front", 3, 0, skin), sk.put("body", "front", 4, 0, skin), sk.put("body", "front", 4, 1, skin)
        sk.band("body", 7, 9, s.get("belt") or trim)
        sk.put("body", "front", 5, 8, trim, flat=True)
        for lg in legs():  # hakama pleats
            for y in range(0, 11):
                sk.put(lg, "front", 1, y, mix(legs_c, 0.82))
        s = dict(s, belt=None)
    elif body == "rags":
        sk.fill("body", skin)
        draw_limbs(sk, s, skin, 1, None, skin, 10)
        for lg in legs():
            sk.band(lg, 0, 12, skin)
            sk.band(lg, 10, 12, mix(skin, 0.8))
            sk.fill(lg, mix(skin, 0.75), faces=("bottom",))
        for y in range(0, 8):
            for x in (0, 1, 6, 7):
                if y < 7 or x % 2:
                    sk.put("body", "front", x, y, main)
        sk.band("body", 0, 8, main, faces=("back", "right", "left"))
        sk.band("body", 9, 12, main, faces=("front", "back"))
        for lg in legs():
            for y in range(0, 4):
                for x in range(4):
                    if y < 3 or x % 2:
                        sk.put(lg, "front", x, y, main), sk.put(lg, "back", x, y, main)
        for arm in arms():  # forearm wraps
            sk.band(arm, 6, 9, trim)
            sk.band(arm, 7, 8, mix(trim, 0.8))
    elif body == "vest":
        sk.fill("body", second)
        draw_limbs(sk, s, second, 7, mix(second, 0.85), legs_c, 8)
        for y in range(12):
            for x in (0, 1, 2, 5, 6, 7):
                sk.put("body", "front", x, y, main)
        sk.band("body", 0, 12, main, faces=("back", "right", "left"))
        sk.put("body", "front", 2, 3, trim, flat=True), sk.put("body", "front", 2, 6, trim, flat=True)
    else:
        raise ValueError(f"unknown body {body!r}")
    return s


def draw_details(sk: Skin, s: dict):
    belt, row = s.get("belt"), s.get("belt_row", 8)
    if s.get("tabard"):
        tab, emblem = s["tabard"], s.get("emblem", "#e2b84a")
        for face in ("front", "back"):
            for y in range(0, 12):
                for x in (2, 3, 4, 5):
                    sk.put("body", face, x, y, tab)
            for y in range(1, 6):
                sk.put("body", face, 3, y, emblem, flat=True), sk.put("body", face, 4, y, emblem, flat=True)
            for x in (2, 5):
                sk.put("body", face, x, 2, emblem, flat=True)
        for y in range(0, 4):
            for x in (2, 3):
                sk.put("right_leg", "front", x, y, tab), sk.put("left_leg", "front", x - 2, y, tab)
    if belt:
        sk.band("body", row, row + 1, belt)
        sk.put("body", "front", 3, row, s.get("trim", "#c9a34a"), flat=True)
        sk.put("body", "front", 4, row, mix(s.get("trim", "#c9a34a"), 0.8), flat=True)
    if s.get("sash"):
        for i in range(8):  # from the right shoulder down to the left hip, front and back
            sk.put("body", "front", i, i, s["sash"])
            sk.put("body", "back", 7 - i, i, s["sash"])
    if s.get("badge"):
        plate = npc_looks.RANK[s["badge"]]
        sk.put("body", "front", 5, 2, plate, flat=True)
        sk.put("body", "front", 5, 3, mix(plate, 0.75), flat=True)


def draw_outer(sk: Skin, s: dict):
    if s.get("pack"):
        pack, strap = s["pack"], mix(s["pack"], 0.65)
        for y in range(1, 10):
            for x in range(1, 7):
                sk.put("body", "back", x, y, pack if y > 3 else mix(pack, 0.85), "over")
        sk.put("body", "back", 3, 4, s.get("trim", "#c9a34a"), "over", flat=True)
        for x in range(0, 8):  # bedroll on top
            sk.put("body", "back", x, 0, s.get("second", "#d8ccb0"), "over")
            sk.put("body", "top", x, 0, s.get("second", "#d8ccb0"), "over")
        for y in range(0, 8):
            sk.put("body", "front", 1, y, strap), sk.put("body", "front", 6, y, strap)
    if s.get("cloak"):
        cloak, inner = s["cloak"], mix(s["cloak"], 0.7)
        sk.band("body", 0, 12, cloak, "over", faces=("back",))
        sk.fill("body", cloak, "over", faces=("top",))
        for y in range(12):
            sk.put("body", "right", 0, y, cloak, "over"), sk.put("body", "right", 1, y, inner if y > 2 else cloak, "over")
            sk.put("body", "left", 3, y, cloak, "over"), sk.put("body", "left", 2, y, inner if y > 2 else cloak, "over")
        sk.put("body", "front", 0, 0, cloak, "over"), sk.put("body", "front", 7, 0, cloak, "over")
        sk.put("body", "front", 1, 0, s.get("trim", "#c9a34a"), "over", flat=True)
        for arm in arms():
            sk.band(arm, 0, 9, cloak, "over", faces=(outer_face(arm), "back"))
            sk.fill(arm, cloak, "over", faces=("top",))
        for lg in legs():
            sk.band(lg, 0, 6, cloak, "over", faces=("back",))
            sk.band(lg, 5, 6, inner, "over", faces=("back",))
    if s.get("pauldrons"):
        metal = s["pauldrons"]
        for arm in arms():
            sk.band(arm, 0, 3, metal, "over", faces=(outer_face(arm), "front", "back"))
            sk.band(arm, 2, 3, mix(metal, 0.75), "over", faces=(outer_face(arm), "front", "back"))
            sk.fill(arm, mix(metal, 1.15), "over", faces=("top",))
    if s.get("gloves"):
        for arm in arms():
            sk.band(arm, 9, 12, s["gloves"])
            sk.band(arm, 9, 10, mix(s["gloves"], 1.15))
            sk.fill(arm, mix(s["gloves"], 0.85), faces=("bottom",))


def draw(spec: dict) -> Image.Image:
    sk = Skin(bool(spec.get("slim")))
    sk.fill("head", spec["skin"])
    draw_hair(sk, spec)
    draw_face(sk, spec)
    s = draw_garment(sk, spec)
    draw_details(sk, s)
    draw_beard(sk, spec)
    draw_outer(sk, s)
    draw_headgear(sk, spec)
    return sk.render()


def own_variants():
    """(look, n, spec) for every variant drawn by this tool."""
    for look, entry in npc_looks.LOOKS.items():
        for i, spec in enumerate(entry["variants"]):
            if not spec.get("texture"):
                yield look, i + 1, spec


# ---- contact sheet -------------------------------------------------------------------------------------------------

def wearers() -> dict:
    """{(look, n): [names]} from sidequests.toml (look) and npcs.toml (skin = a look PNG)."""
    out = {}
    data = ROOT / "design" / "data"
    sq = tomllib.loads((data / "sidequests.toml").read_text(encoding="utf-8"))
    seen = set()
    for table in ("adventurer", "client"):
        for k in sq.get(table, []):
            if not k.get("look"):
                continue
            key = (k["look"], npc_looks.pick(k["look"], k.get("look_name", k["name"]), k.get("model", "humanoid")))
            if (key, k["name"]) not in seen:
                seen.add((key, k["name"]))
                out.setdefault(key, []).append(k["name"])
    npcs = tomllib.loads((data / "npcs.toml").read_text(encoding="utf-8"))
    for k in npcs.get("kind", []):
        name = Path(k.get("skin", "")).name
        for look, n, _ in own_variants():
            if name == npc_looks.file_name(look, n):
                out.setdefault((look, n), []).append(k["name"])
    return out


def contact_sheet(images: dict) -> Image.Image:
    from preview_skins import view  # noqa: E402 (same Pillow dependency)
    cell_w, cell_h, cols, pad = 150, 262, 8, 6
    cards = list(images.items())
    rows = -(-len(cards) // cols)
    header = 64
    sheet = Image.new("RGB", (cols * cell_w + pad * 2, header + rows * cell_h + pad), (46, 49, 58))
    draw = ImageDraw.Draw(sheet)
    try:
        big, small = ImageFont.load_default(size=20), ImageFont.load_default(size=11)
    except TypeError:  # Pillow without FreeType
        big = small = ImageFont.load_default()
    draw.text((pad + 4, 10), "OCS Two Lives: generic NPC looks (tools/gen_npc_looks.py)", font=big, fill=(236, 232, 220))
    draw.text((pad + 4, 38), "Front three-quarter views. Name under a card = the NPC wearing it; spare = for future roles. "
              "falmuth_knight uses Tensura's own texture at runtime (not shown, not copied).", font=small,
              fill=(175, 180, 192))
    who = wearers()
    for i, ((look, n), (image, slim)) in enumerate(cards):
        x, y = pad + (i % cols) * cell_w, header + (i // cols) * cell_h
        card = view(image, slim, -26)
        sheet.paste(card, (x + (cell_w - card.width) // 2, y))
        label = f"{look} #{n}" + (" (slim)" if slim else "")
        names = ", ".join(who.get((look, n), [])) or "spare"
        draw.text((x + 4, y + card.height + 2), label, font=small, fill=(236, 232, 220))
        draw.text((x + 4, y + card.height + 18), names[:26], font=small,
                  fill=(229, 188, 76) if names != "spare" else (140, 146, 158))
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare the committed PNGs with a fresh draw")
    args = parser.parse_args()
    images, stale = {}, []
    for look, n, spec in own_variants():
        image = draw(spec)
        images[(look, n)] = (image, bool(spec.get("slim")))
        path = TARGET / npc_looks.file_name(look, n)
        if args.check:
            if not path.is_file():
                stale.append(path)
                continue
            with Image.open(path) as saved:
                if saved.convert("RGBA").tobytes() != image.tobytes():
                    stale.append(path)
        else:
            image.save(path)
    known = {npc_looks.file_name(look, n) for look, n, _ in own_variants()}
    orphans = [p for p in TARGET.glob("look_*.png") if p.name not in known]
    if args.check:
        for p in stale + orphans:
            print(f"FAIL {p.relative_to(ROOT)} is stale or no longer in the catalogue: run python tools/gen_npc_looks.py")
        sys.exit(1 if stale or orphans else 0)
    for p in orphans:
        p.unlink()
        print(f"removed {p.relative_to(ROOT)}")
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet(images).save(SHEET)
    print(f"wrote {len(images)} looks in {TARGET.relative_to(ROOT)} and {SHEET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
