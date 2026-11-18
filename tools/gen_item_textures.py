#!/usr/bin/env python3
"""Draw the pack's hand-made item and GUI textures (reproducible, Pillow only).

    python tools/gen_item_textures.py            # item textures + the Mana Ledger GUI + previews
    python tools/gen_item_textures.py --no-gui   # items only (no network)
    python tools/gen_item_textures.py --gui-src path/to/atm.png
    python tools/gen_item_textures.py --no-gui --force-placeholders   # redraw the path placeholders too

Writes:
  pack/kubejs/assets/ttl/textures/item/soul_gem.png      16x16, a faintly glowing soul gem
  pack/kubejs/assets/ttl/textures/item/skill_core.png    16x16, a crystalline core
  pack/kubejs/assets/lightmanscurrency/textures/gui/container/atm.png
        256x256, the Mana Ledger (ATM) screen: the mod's own layout, recoloured to the violet / gold / cyan magic
        palette of the block texture. Source: Lightman's Currency, branch LC-1.21.1 (identical to the 1.21-2.3.0.6
        release: the file last changed 19/11/2024). It is downloaded with `gh` (or urllib) when --gui-src is absent
        and never committed in its original colours.
  docs/previews/items/*.png                               8x previews (items on a dark and a light slot)
  pack/kubejs/assets/ttl/textures/item/<id>.png, .../block/<id>.png
        PLACEHOLDERS for the player paths (design/architecture/paths-necro-artificer.md section 7: soul ash, bone dust,
        the Bone Altar, the Workshop Bench, ...; see PATH_ITEMS / PATH_BLOCKS below). They are written only when the file
        is missing (or with --force-placeholders), so an artist's or an image model's replacement is never overwritten:
        drop a 16x16 PNG with the same name in place and commit it. Block textures are one face used on all six sides.

The palette is the one of lightmanscurrency/textures/block/atm.png (violet stone, gold trim, cyan screen).
"""
import argparse
import io
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ITEM_DIR = ROOT / "pack/kubejs/assets/ttl/textures/item"
GUI_PATH = ROOT / "pack/kubejs/assets/lightmanscurrency/textures/gui/container/atm.png"
PREVIEW_DIR = ROOT / "docs/previews/items"

GUI_RAW = ("repos/Lightman314/LightmansCurrency/contents/src/main/resources/assets/lightmanscurrency/"
           "textures/gui/container/atm.png?ref=LC-1.21.1")

T = (0, 0, 0, 0)


def hexc(s, a=255):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# ---------------------------------------------------------------- soul gem
# Tensura reads souls as pale cyan-white light with a violet heart; the gem is a diamond-cut cabochon.
GEM = {
    "o": hexc("121a3e"),  # outline
    "d": hexc("2a4d9c"),  # darkest facet
    "m": hexc("3f7bd6"),  # mid facet
    "l": hexc("78c8f2"),  # light facet
    "w": hexc("e6fbff"),  # highlight
    "v": hexc("b79cff"),  # violet soul heart
    "V": hexc("f2e8ff"),  # heart spark
}
GEM_ART = [
    "................",
    "................",
    ".......oo.......",
    "......olwo......",
    ".....ollwmo.....",
    "....ollwwlmo....",
    "...ollllwlmmo...",
    "...olwlvVvlmo...",
    "...olllvvvmdo...",
    "...omlmlvmdmo...",
    "....omlmmmddo...",
    ".....ommmddo....",
    "......oddmo.....",
    ".......ooo......",
    "................",
    "................",
]

# ---------------------------------------------------------------- skill core
# A double-pointed crystal (Tensura magic-crystal violet) held by a gold band: skills are stored in it.
CORE = {
    "o": hexc("160a30"),  # outline
    "d": hexc("4a2a8c"),  # shadow facet
    "m": hexc("7a50c8"),  # mid facet
    "l": hexc("b08cf5"),  # light facet
    "w": hexc("efe3ff"),  # highlight
    "g": hexc("ffd34a"),  # gold band
    "G": hexc("c08a14"),  # gold shade
    "c": hexc("5ee6ff"),  # cyan mana spark
}
CORE_ART = [
    "................",
    ".......oo.......",
    "......olwo......",
    ".....ollwmo.....",
    ".....ollwmmo....",
    "....ollwlmmdo...",
    "....oGggggggGo..",
    "....olwlcmmmdo..",
    "....ollwcmmmdo..",
    "....oGggggggGo..",
    ".....olwlmmdo...",
    ".....ollmmddo...",
    "......olmmdo....",
    ".......oddo.....",
    "........oo......",
    "................",
]

HALO = hexc("8fe6ff", 70)


def render(art, pal, halo=None):
    assert len(art) == 16, len(art)
    im = Image.new("RGBA", (16, 16), T)
    for y, row in enumerate(art):
        assert len(row) == 16, (y, row, len(row))
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), pal[ch])
    if halo:
        src = im.copy()
        for y in range(16):
            for x in range(16):
                if src.getpixel((x, y))[3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3] == 255:
                        im.putpixel((x, y), halo)
                        break
    return im


# ---------------------------------------------------------------- Mana Ledger GUI
# Source colours of the mod's atm.png (7 flat colours) -> the magic palette.
GUI_MAP = {
    (198, 198, 198, 255): hexc("b9a6e6"),  # panel: light lavender (the mod draws dark 0x404040 text on it)
    (139, 139, 139, 255): hexc("6f58aa"),  # slots: violet stone
    (255, 255, 255, 255): hexc("ffe68c"),  # bevel highlight: gold
    (55, 55, 55, 255): hexc("33205f"),     # bevel shadow: deep violet
    (0, 0, 0, 255): hexc("1e1240"),        # outline: near-black violet
    (85, 85, 85, 255): hexc("46307a"),     # slot shadow edge: dark violet
}


def fetch_gui_source():
    try:
        raw = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw", GUI_RAW],
                             check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        import urllib.request
        url = ("https://raw.githubusercontent.com/Lightman314/LightmansCurrency/LC-1.21.1/src/main/resources/"
               "assets/lightmanscurrency/textures/gui/container/atm.png")
        raw = urllib.request.urlopen(url, timeout=30).read()
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def recolour_gui(src):
    assert src.size == (256, 256), src.size
    out = Image.new("RGBA", src.size, T)
    unknown = set()
    for y in range(src.size[1]):
        for x in range(src.size[0]):
            p = src.getpixel((x, y))
            if p[3] == 0:
                continue
            q = GUI_MAP.get(p)
            if q is None:
                unknown.add(p)
                q = p
            out.putpixel((x, y), q)
    if unknown:
        print("warning: unmapped GUI colours kept:", sorted(unknown))
    return out


# ---------------------------------------------------------------- path placeholders
# Deliberately simple shapes in each path's colours: bone white / ash grey / grave green for the necromancer, brass and
# magisteel blue for the artificer, earth tones for the choice-scene blocks. Replace freely (see the module docstring).
PATH_PAL = {
    "o": hexc("1c1a22"),  # outline
    "b": hexc("e8e0c8"),  # bone
    "B": hexc("b7ab8a"),  # bone shade
    "a": hexc("6e6a72"),  # ash
    "A": hexc("3e3a44"),  # ash dark
    "s": hexc("9fe8ff"),  # soul light
    "S": hexc("4aa3c8"),  # soul shade
    "g": hexc("7cff9a"),  # grave flame
    "G": hexc("2f9a4c"),  # grave flame shade
    "w": hexc("8a5a32"),  # wood
    "W": hexc("5c3a1e"),  # wood dark
    "m": hexc("7aa0d8"),  # magisteel
    "M": hexc("3c5a8c"),  # magisteel dark
    "y": hexc("e2b44a"),  # brass
    "Y": hexc("9a7420"),  # brass dark
    "p": hexc("efe6cf"),  # parchment
    "P": hexc("c9b98f"),  # parchment shade
    "r": hexc("b02a3a"),  # seal red / curse
    "R": hexc("6a1420"),  # curse dark
    "h": hexc("9ad86a"),  # herb
    "k": hexc("8c8c8c"),  # stone
    "K": hexc("5a5a5a"),  # stone dark
    "d": hexc("6a8cc8"),  # water
    "e": hexc("2a1a3a"),  # egg
    "E": hexc("7a4aa8"),  # egg speckle
}

PATH_ITEMS = {
    "soul_ash": [
        "................", "................", "................", "................",
        "................", "................", ".......s........", "......oAo.......",
        ".....oaaAo......", "....oaaaaAo.....", "...oaasaaaAo....", "..oaaaaaaaaAo...",
        "..oAaaaasaaAo...", "...oooooooooo...", "................", "................"],
    "bone_dust": [
        "................", "................", "................", "................",
        "................", "................", "................", ".......oo.......",
        "......obBo......", ".....obbbBo.....", "....obbBbbBo....", "...obbbbbbbBo...",
        "...oBbbbBbbBo...", "....oooooooo....", "................", "................"],
    "soul_remnant": [
        "................", "................", "......oooo......", ".....osssso.....",
        "....ossssSso....", "....osoSsoSo....", "....ossssssSo...", "....osssssSSo...",
        ".....ossSSSo....", ".....oSsSSo.....", "......oSsSo.....", ".......oSo......",
        "........oS......", ".........o......", "................", "................"],
    "hipokute_salve": [
        "................", "................", "................", ".....oooooo.....",
        ".....oPPPPo.....", "....oooooooo....", "....ohhhhhho....", "...ohhhhhhhho...",
        "...ohhhhhhhho...", "...ohhhhhhhho...", "...ohhhhhhhho...", "...ohhhhhhhho...",
        "....ohhhhhho....", ".....oooooo.....", "................", "................"],
    "engraving_chisel": [
        "................", "............oo..", "...........omo..", "..........omMo..",
        ".........omMo...", "........omMo....", ".......oyYo.....", "......oyYo......",
        ".....owWo.......", "....owWo........", "...owWo.........", "..owWo..........",
        "..oWo...........", "..oo............", "................", "................"],
    "cursed_whetstone": [
        "................", "................", "................", "................",
        "................", "...oooooooooo...", "..okkkkkkkkKKo..", "..okrkkkkrkkKo..",
        "..okkkRkkkkKKo..", "..oKkkkkrkkKKo..", "..oKKKKKKKKKKo..", "...oooooooooo...",
        "................", "................", "................", "................"],
    "warden_core": [
        "................", "......oooo......", ".....oyyyYo.....", "....oyMmmMYo....",
        "...oyMmsmmMYo...", "...oyMssSmMYo...", "..oyMmsSSmmMYo..", "..oyMmmSmmmMYo..",
        "..oyMmmmmmmMYo..", "...oyMmmmmMYo...", "...oyMMmmMMYo...", "....oyMMMMYo....",
        ".....oYYYYo.....", "......oooo......", "................", "................"],
    "artificer_charter": [
        "................", "................", "..oooooooooooo..", "..oPppppppppPo..",
        "...opppppppppo..", "...opWWWWWWppo..", "...oppppppppo...", "...opWWWWWpppo..",
        "...oppppppppo...", "...opWWWWWWppo..", "...opppppyyyo...", "..oPppppyYYyPo..",
        "..ooooooyyYooo..", "........oyo.....", "................", "................"],
    "exorcist_licence": [
        "................", "................", "..oooooooooooo..", "..oPppppppppPo..",
        "...oppppyppppo..", "...opppyyypppo..", "...oppppyppppo..", "...oppppyppppo..",
        "...opWWWWWWppo..", "...oppppppppo...", "...opWWWWWrrro..", "..oPppppprRrPo..",
        "..ooooooorrroo..", "................", "................", "................"],
}

PATH_BLOCKS = {
    "bone_altar": [
        "oooooooooooooooo", "obbbbbbbbbbbbbBo", "obBBBBBBBBBBBBBo", "oooooooooooooooo",
        "oaaaobbbbbboaaao", "oaaaobooobboaaao", "oaaaobosobboaaao", "oaaaobooobboaaao",
        "oaaaobbbbbboaaao", "oaaaoboboboaaaao", "oaaaobbbbbboaaao", "oAAAoooooooaAAAo",
        "oaaaaaaaaaaaaaao", "oAAAAAAAAAAAAAAo", "oAAAAAAAAAAAAAAo", "oooooooooooooooo"],
    "workshop_bench": [
        "oooooooooooooooo", "ommmmmmmmmmmmmMo", "oMMMMMMMMMMMMMMo", "oooooooooooooooo",
        "owwwwwwwwwwwwwwo", "owWWWWWWWWWWWWwo", "owWyyWWWWWmmWWwo", "owWyyWWWWWmmWWwo",
        "owWWWWWWWWWWWWwo", "owwwwwwwwwwwwwwo", "oWWWWWWWWWWWWWWo", "oooooooooooooooo",
        "owo..........owo", "owo..........owo", "oWo..........oWo", "ooo..........ooo"],
    "grave_lantern": [
        "................", "......oooo......", ".....oKKKKo.....", "....oooooooo....",
        "....oK....Ko....", "....oK.gg.Ko....", "....oKgGgg.o....", "....o.gGGgKo....",
        "....oKgGGg.o....", "....oK.gg.Ko....", "....oK....Ko....", "....oooooooo....",
        ".....oKKKKo.....", "......oooo......", "................", "................"],
    "grave_marker": [
        "kkkkkkkkkkkkkkkk", "kKkkkkkkkkkkkkKk", "kkkkkooooookkkkk", "kkkkokkkkkkokkkk",
        "kkkokkkKKkkkokkk", "kkkokkKKKKkkokkk", "kkkokkkKKkkkokkk", "kkkokkkKKkkkokkk",
        "kkkokkkKKkkkokkk", "kkkokkkkkkkkokkk", "kkkokkkkkkkkokkk", "kkkooooooooookkk",
        "kKkkkkkkkkkkkkKk", "kkkKkkkkkkkKkkkk", "kKkkkkkkkkkkkkKk", "kkkkkkkkkkkkkkkk"],
    "offering_bowl": [
        "................", "................", "................", "................",
        "................", "................", "oooooooooooooooo", "owwhhhhhhhhhhwwo",
        "owwwwwwwwwwwwwwo", ".owWWWWWWWWWWwo.", "..owWWWWWWWWwo..", "...owwwwwwwwo...",
        "....oooooooo....", ".....oWWWWo.....", "....oooooooo....", "................"],
    "cracked_dam": [
        "kkkkkkkkokkkkkkk", "kKkkkkkkokkkkKkk", "kkkkkkkoKkkkkkkk", "ooooooooKooooooo",
        "kkkkokkkKkkkkkkk", "kKkkokkkoKkkkkKk", "kkkkokkkkoddkkkk", "kkkkokkkkkodkkkk",
        "ooooooooooodoooo", "kkkkkkkkokkdkkkk", "kKkkkkkkokkdkkKk", "kkkkkkkkokkkdkkk",
        "kkkkkkkkokkkkdkk", "ooooooooooooooKo", "kkkkkokkkkkkkkkk", "kKkkkokkkkkkkKkk"],
    "rubble": [
        "KkkkoKKkkkokkkKK", "kkkokkkkkkkokkkk", "kKokkKkkKkkkoKkk", "ookkkkkkkkkkkooo",
        "kkkkKkkoookkkkkK", "kkkkkkoKkkokkkkk", "oKkkkokkkkkokkKo", "kkkkkokkKkkokkkk",
        "kkKkkkooookkkkkk", "kkkkkkkkkkkkoooo", "ooookkkKkkkokkkk", "kKkkokkkkkkokKkk",
        "kkkkkokkKkkkokkk", "kkKkkkooooookkkk", "oookkkkkkkkkkkkK", "kkkkkkkKkkkkkkkk"],
    "dragon_egg_cradle": [
        "................", "................", "......oooo......", ".....oeEeeo.....",
        "....oeeeEeeo....", "....oeEeeeeo....", "...oeeeeeEeeo...", "...oeeEeeeeeo...",
        "...oeeeeeEeeo...", "..owoeeEeeeowWo.", ".owWwoooooowWwo.", "owWwWwWwWwWwWwWo",
        "oWwWwWwWwWwWwWwo", ".oWwWwWwWwWwWwo.", "..oooooooooooo..", "................"],
}


def path_placeholders(force):
    """Writes the missing path placeholder PNGs; returns the images (for the preview) and the paths written."""
    written = []
    images = []
    for folder, table in (("item", PATH_ITEMS), ("block", PATH_BLOCKS)):
        out_dir = ROOT / "pack/kubejs/assets/ttl/textures" / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, art in table.items():
            path = out_dir / f"{name}.png"
            if path.exists() and not force:
                images.append(Image.open(path).convert("RGBA"))
                continue
            im = render(art, PATH_PAL)
            im.save(path)
            images.append(im)
            written.append(path)
    return images, written

# ---------------------------------------------------------------- previews
def preview(images, path, scale=8):
    w = 16 * scale
    sheet = Image.new("RGBA", (w * len(images) * 2 + 8 * (len(images) * 2 + 1), w + 16), (40, 40, 48, 255))
    x = 8
    for im in images:
        for bg in ((55, 55, 66, 255), (198, 198, 198, 255)):
            cell = Image.new("RGBA", (w, w), bg)
            big = im.resize((w, w), Image.NEAREST)
            cell.paste(big, (0, 0), big)
            sheet.paste(cell, (x, 8))
            x += w + 8
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gui", action="store_true")
    ap.add_argument("--gui-src")
    ap.add_argument("--force-placeholders", action="store_true",
                    help="redraw the path placeholders even where a PNG exists (overwrites replacements)")
    args = ap.parse_args()

    gem = render(GEM_ART, GEM, HALO)
    core = render(CORE_ART, CORE, HALO)
    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    gem.save(ITEM_DIR / "soul_gem.png")
    core.save(ITEM_DIR / "skill_core.png")
    preview([gem, core], PREVIEW_DIR / "ttl_items.png")
    print("wrote soul_gem.png, skill_core.png")
    paths, written = path_placeholders(args.force_placeholders)
    preview(paths, PREVIEW_DIR / "ttl_path_items.png", scale=4)
    print(f"path placeholders: {len(written)} written, {len(paths) - len(written)} kept")

    if args.no_gui:
        return 0
    src = Image.open(args.gui_src).convert("RGBA") if args.gui_src else fetch_gui_source()
    gui = recolour_gui(src)
    GUI_PATH.parent.mkdir(parents=True, exist_ok=True)
    gui.save(GUI_PATH)
    big = Image.new("RGBA", (gui.size[0] * 2, gui.size[1] * 2), (40, 40, 48, 255))
    g2 = gui.resize((512, 512), Image.NEAREST)
    big.paste(g2, (0, 0), g2)
    big.crop((0, 0, 180 * 2, 245 * 2)).save(PREVIEW_DIR / "mana_ledger_gui.png")
    print("wrote", GUI_PATH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
