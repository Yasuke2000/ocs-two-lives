"""The look catalogue of the generic NPCs (adventurers, merchants, dwarves, monsters, church, knights): stdlib only.

One archetype ("look") has a few variants, so a crowd of the same role does not wear one face. A variant is either our
own skin, drawn by tools/gen_npc_looks.py from the spec below into
pack/kubejs/assets/ttl/textures/entity/npc/look_<look>_<n>.png, or a ready 64x64 player-layout texture (`texture`): one
that ships inside an installed mod (referenced at runtime, nothing is copied into the pack) or a hand-made skin of ours
(`ttl:textures/entity/npc/hand_<look>_<n>.png`, see docs/art/npc-skin-prompts.md).

Data that wears a look: design/data/sidequests.toml ([[adventurer]] and [[client]] `look = "<look>"`, optional
`look_name`), read by tools/gen_npcs.py (the preset's SkinData) and checked by tools/sidequests_check.py. The variant is
picked from the name (`look_name`, else `name`) with CRC-32, among the variants whose arm model matches the NPC's `model`,
so the same name always wears the same skin and renaming an NPC is the only thing that changes it.

Variant spec (all colours #rrggbb; gen_npc_looks.py documents the drawing):
  slim            three-pixel arms (Easy NPC humanoid_slim) instead of four
  race            human | dwarf | goblin | hobgoblin | kijin | lizard
  skin, eyes      skin tone, iris
  hair, hair_style  short | crop | long | tied | bald | swept
  beard, beard_style  full | short | goatee | moustache (dwarves mostly)
  head, head_color  hood | helm | cap | circlet | bandana | horns | coif (headgear)
  body            tunic | jerkin | chain | plate | robe | coat | apron | kimono | rags | vest
  main, second, trim  garment, shirt or sleeves, edging and accents
  belt, legs, boots
  cloak, pack, tabard (+ emblem), sash, pauldrons (metal), gloves, badge (guild rank letter F-A)
Colours and costumes are our interpretation of the Western Nations of Tensura (design/lore/skins.md, "Generic looks").
"""
import zlib

ASSET_DIR = "pack/kubejs/assets/ttl/textures/entity/npc"

# Guild rank plates (our interpretation: wood, copper, iron, silver, gold, mithril).
RANK = {"F": "#8a6a4a", "E": "#b87333", "D": "#8d9399", "C": "#dfe5ea", "B": "#e5bc4c", "A": "#7fd8ea"}

# Skin tones and hair colours used below.
FAIR, LIGHT, MEDIUM, TAN, DEEP, RUDDY = "#f1caa9", "#e5b48f", "#cf9a72", "#b07a55", "#87593c", "#d99a78"
BLACK, DARK, BROWN, CHESTNUT, BLOND, RED, GREY, WHITE = ("#2a2426", "#3e2c22", "#5b3b26", "#7a4a2a", "#d6b05a",
                                                          "#9a3b24", "#9a958e", "#e3dfd6")
STEEL, IRON, BRASS, GOLD = "#b9c0c7", "#7d858d", "#b8913f", "#e2b84a"
LEATHER, DARK_LEATHER, BOOT = "#8a5a35", "#5e3d27", "#4a3324"


def v(**spec) -> dict:
    spec.setdefault("slim", False)
    spec.setdefault("race", "human")
    return spec


LOOKS = {
    # ---- Free Guild adventurers, by rank: leather for F/E, chain for D/C, steel and a cape for B/A -------------------
    "guild_rookie": dict(
        title="Free Guild rookie (rank F-E)",
        variants=[
            v(skin=LIGHT, hair=CHESTNUT, hair_style="short", eyes="#4c6a3a", body="tunic", main="#7d8a4a", second="#d8c9a4",
              trim="#5c6634", belt=LEATHER, legs="#6b5a44", boots=BOOT, gloves=DARK_LEATHER, badge="F"),
            v(skin=MEDIUM, hair=DARK, hair_style="crop", eyes="#4a3a2a", body="jerkin", main=LEATHER, second="#b9ab8c",
              trim=DARK_LEATHER, belt=DARK_LEATHER, legs="#5d6470", boots=BOOT, cloak="#6e5a3c", badge="E"),
            v(skin=FAIR, hair=BLOND, hair_style="swept", eyes="#3f6d8f", body="tunic", main="#8c4b3b", second="#cdbf9c",
              trim="#5e3028", belt=LEATHER, legs="#4f4a42", boots=BOOT, sash=DARK_LEATHER, badge="E"),
        ]),
    "guild_veteran": dict(
        title="Free Guild veteran (rank D-C)",
        variants=[
            v(skin=TAN, hair=BROWN, hair_style="short", beard=BROWN, beard_style="short", eyes="#4a3a2a", body="chain",
              main=IRON, second="#5a4a3a", trim=STEEL, belt=DARK_LEATHER, legs="#4b4237", boots=BOOT, cloak="#5b4a32",
              gloves=DARK_LEATHER, badge="C"),
            v(skin=LIGHT, hair=GREY, hair_style="crop", beard=GREY, beard_style="moustache", eyes="#3f5f7a", body="jerkin",
              main=DARK_LEATHER, second="#7a6a52", trim=BRASS, belt=LEATHER, legs="#3f3a35", boots=BOOT, pauldrons=IRON,
              sash=LEATHER, badge="D"),
            v(skin=DEEP, hair=BLACK, hair_style="tied", eyes="#3a2a22", body="chain", main=IRON, second="#2f4a3a",
              trim=STEEL, belt=DARK_LEATHER, legs="#2f3a32", boots=BOOT, tabard="#35563f", emblem="#c9b98a",
              gloves=DARK_LEATHER, badge="C"),
        ]),
    "guild_elite": dict(
        title="Free Guild elite (rank B-A)",
        variants=[
            v(skin=LIGHT, hair=WHITE, hair_style="swept", eyes="#5a7fa0", body="plate", main=STEEL, second="#3b4a66",
              trim=GOLD, belt=DARK_LEATHER, legs="#3b4250", boots=IRON, cloak="#2f3f6a", badge="A"),
            v(skin=MEDIUM, hair=RED, hair_style="short", beard=RED, beard_style="goatee", eyes="#4a3a2a", body="plate",
              main="#9aa2aa", second="#6a2a2a", trim=BRASS, belt=DARK_LEATHER, legs="#3a3030", boots=IRON,
              cloak="#7a2c2c", badge="B"),
        ]),
    "guild_scout": dict(
        title="Free Guild scout or ranger",
        variants=[
            v(slim=True, skin=LIGHT, hair=CHESTNUT, hair_style="tied", eyes="#3f7a5a", head="hood", head_color="#3d5a3a",
              body="jerkin", main="#5b4630", second="#6f7f4a", trim="#3a2c20", belt=DARK_LEATHER, legs="#4a4f3a",
              boots=BOOT, cloak="#3d5a3a", sash=DARK_LEATHER, gloves=DARK_LEATHER, badge="D"),
            v(slim=True, skin=TAN, hair=BLACK, hair_style="long", eyes="#5a4a2a", body="tunic", main="#4a5a3a",
              second="#8a7a5a", trim="#2f3a28", belt=LEATHER, legs="#5a4a38", boots=BOOT, cloak="#5e4a32",
              sash=LEATHER, badge="E"),
            v(skin=MEDIUM, hair=BROWN, hair_style="short", eyes="#4a5a3a", head="hood", head_color="#5a4632",
              body="jerkin", main=DARK_LEATHER, second="#6a6a4a", trim="#2f2418", belt=LEATHER, legs="#3f4434",
              boots=BOOT, cloak="#5a4632", sash=LEATHER, gloves=DARK_LEATHER, badge="D"),
        ]),
    "guild_mage": dict(
        title="Free Guild mage",
        variants=[
            v(slim=True, skin=FAIR, hair="#6a4a8a", hair_style="long", eyes="#8a5ac0", body="robe", main="#4b3a72",
              second="#6c5a9a", trim="#d9b85a", belt="#2f2448", legs="#3a2c58", boots="#2a2232", badge="E"),
            v(slim=True, skin=LIGHT, hair=BLOND, hair_style="tied", eyes="#3f6d8f", head="hood", head_color="#2f4a6a",
              body="robe", main="#2f4a6a", second="#d8cfb8", trim="#c9a34a", belt=LEATHER, legs="#26384f",
              boots=BOOT, badge="D"),
            v(skin=TAN, hair=GREY, hair_style="swept", beard=GREY, beard_style="goatee", eyes="#5a4a7a", body="robe",
              main="#5a2a3a", second="#3a2a3a", trim="#d9b85a", belt="#2a1e24", legs="#4a2230", boots="#2a2232",
              cloak="#3a2a4a", badge="C"),
        ]),
    "bard": dict(
        title="wandering bard",
        variants=[
            v(skin=LIGHT, hair=CHESTNUT, hair_style="swept", eyes="#4a6a3a", head="cap", head_color="#8a2f4a",
              body="tunic", main="#a8445a", second="#e3c98a", trim="#e2b84a", belt=LEATHER, legs="#3f5a6a",
              boots=BOOT, cloak="#3f5a6a", sash="#e3c98a"),
            v(skin=MEDIUM, hair=BLACK, hair_style="tied", eyes="#4a3a2a", body="coat", main="#3f6a5a", second="#d8b86a",
              trim="#e2b84a", belt=DARK_LEATHER, legs="#6a3a4a", boots=BOOT, sash="#a8445a"),
        ]),
    "otherworlder": dict(
        title="otherworlder in adventurer gear",
        variants=[
            v(skin=FAIR, hair=BLACK, hair_style="short", eyes="#3a2a22", body="coat", main="#262a36", second="#e8e2d4",
              trim="#c9a34a", belt=DARK_LEATHER, legs="#2f3340", boots=BOOT, sash=DARK_LEATHER, badge="E"),
            v(skin=LIGHT, hair="#3a3438", hair_style="swept", eyes="#5a3a2a", body="jerkin", main="#3a3f4f",
              second="#d8d2c4", trim=STEEL, belt=LEATHER, legs="#2a2e38", boots=BOOT, cloak="#7a2a2a", badge="D"),
        ]),
    # ---- Merchants: a Blumund pedlar, a Dwargon trader, an Englassian factor ----------------------------------------
    "merchant": dict(
        title="travelling merchant (Blumund pedlar, southern trader, Englassian factor)",
        variants=[
            v(skin=LIGHT, hair=BROWN, hair_style="short", beard=BROWN, beard_style="short", eyes="#4a3a2a",
              head="cap", head_color="#8a2f2a", body="coat", main="#8a2f2a", second="#e8dcb8", trim="#d9b85a",
              belt=DARK_LEATHER, legs="#5a4a38", boots=BOOT, pack="#7a5a3a"),
            v(skin=TAN, hair=BLACK, hair_style="tied", eyes="#3a2a22", head="hood", head_color="#6a5a3a", body="robe",
              main="#a07a3a", second="#5a3a2a", trim="#e2b84a", belt="#8a2f2a", legs="#7a5a2a", boots=BOOT,
              pack="#6a4a2a"),
            v(skin=FAIR, hair=GREY, hair_style="swept", beard=GREY, beard_style="moustache", eyes="#3f5f7a",
              body="coat", main="#2a3a5a", second="#d8d2c4", trim="#b83a3a", belt=DARK_LEATHER, legs="#2f2f3a",
              boots=BOOT, sash="#b83a3a"),
        ]),
    "dwarf_trader": dict(
        title="Dwargon trader or caravan master",
        variants=[
            v(race="dwarf", skin=RUDDY, hair=CHESTNUT, hair_style="bald", beard=CHESTNUT, beard_style="full",
              eyes="#4a3a2a", body="coat", main="#c9a23a", second="#8a2f2a", trim="#8a2f2a", belt=DARK_LEATHER,
              legs="#5a3a2a", boots=BOOT, pack="#5e3d27"),
            v(race="dwarf", skin=TAN, hair=GREY, hair_style="short", beard=GREY, beard_style="full", eyes="#3a2a22",
              head="cap", head_color="#8a2f2a", body="coat", main="#6a3a2a", second="#e8c64a", trim="#e8c64a",
              belt=DARK_LEATHER, legs="#4a3a30", boots=BOOT, cloak="#b8332f", gloves=DARK_LEATHER),
        ]),
    "commoner": dict(
        title="carter, farmer or townsfolk",
        variants=[
            v(skin=MEDIUM, hair=BROWN, hair_style="crop", eyes="#4a3a2a", head="cap", head_color="#8a7a5a", body="tunic",
              main="#a89a72", second="#d8ccb0", trim="#6a5a40", belt=LEATHER, legs="#5a5040", boots=BOOT),
            v(skin=LIGHT, hair=BLOND, hair_style="short", beard=BLOND, beard_style="short", eyes="#4a6a8a",
              body="vest", main="#6a4a2a", second="#cfc3a2", trim="#4a3420", belt=DARK_LEATHER, legs="#4a5a6a",
              boots=BOOT),
        ]),
    "scholar": dict(
        title="scholar of the Englassia academy",
        variants=[
            v(slim=True, skin=FAIR, hair=CHESTNUT, hair_style="tied", eyes="#4a6a3a", body="robe", main="#2a3a5a",
              second="#d8d2c4", trim="#b83a3a", belt="#b83a3a", legs="#22304a", boots="#2a2232", sash=LEATHER),
            v(skin=LIGHT, hair=GREY, hair_style="bald", beard=WHITE, beard_style="goatee", eyes="#3f5f7a", body="robe",
              main="#3a2a4a", second="#d8d2c4", trim="#d9b85a", belt="#2a1e30", legs="#2f2240", boots="#2a2232"),
        ]),
    # ---- Armed Nation of Dwargon -----------------------------------------------------------------------------------
    "dwarf_warrior": dict(
        title="Dwargon warrior or guard",
        variants=[
            v(race="dwarf", skin=RUDDY, hair=CHESTNUT, hair_style="short", beard=CHESTNUT, beard_style="full",
              eyes="#3a2a22", head="helm", head_color=STEEL, body="chain", main=IRON, second="#8a2f2a", trim=GOLD,
              belt=DARK_LEATHER, legs="#4a3a30", boots=IRON, tabard="#b8332f", emblem="#e8c64a", gloves=DARK_LEATHER),
            v(race="dwarf", skin=TAN, hair=BLACK, hair_style="tied", beard=BLACK, beard_style="full", eyes="#3a2a22",
              body="plate", main="#8d9399", second="#6a2a22", trim=BRASS, belt=DARK_LEATHER, legs="#3a302a",
              boots=IRON, cloak="#8a2f2a", gloves=IRON),
            v(race="dwarf", skin=LIGHT, hair=RED, hair_style="bald", beard=RED, beard_style="full", eyes="#4a5a3a",
              body="jerkin", main=DARK_LEATHER, second="#c9a23a", trim=BRASS, belt=LEATHER, legs="#4a4030",
              boots=BOOT, pauldrons=IRON, sash=LEATHER, badge="D"),
        ]),
    "dwarf_smith": dict(
        title="Dwargon smith or craftsman",
        variants=[
            v(race="dwarf", skin=RUDDY, hair=GREY, hair_style="bald", beard=GREY, beard_style="full", eyes="#3a2a22",
              body="apron", main="#6a3a2a", second="#a87a4a", trim=BRASS, belt=DARK_LEATHER, legs="#3f3630",
              boots=BOOT, gloves=DARK_LEATHER),
            v(race="dwarf", skin=TAN, hair=BROWN, hair_style="short", beard=BROWN, beard_style="full", eyes="#4a3a2a",
              head="bandana", head_color="#b8332f", body="apron", main="#5a4a3a", second="#c9a23a", trim=IRON,
              belt=DARK_LEATHER, legs="#4a3a30", boots=BOOT, gloves=DARK_LEATHER),
        ]),
    # ---- The Church and the knights of the Western Nations ----------------------------------------------------------
    "luminist_cleric": dict(
        title="priest or cleric of Luminism",
        variants=[
            v(slim=True, skin=FAIR, hair=BLOND, hair_style="long", eyes="#3f6d8f", body="robe", main="#ece6d6",
              second="#d8cfb8", trim=GOLD, belt="#3a5a9a", legs="#e0d8c4", boots="#8a7a5a", tabard="#ece6d6",
              emblem=GOLD),
            v(slim=True, skin=MEDIUM, hair=BROWN, hair_style="tied", eyes="#4a3a2a", head="hood", head_color="#ece6d6",
              body="robe", main="#ece6d6", second="#3a5a9a", trim=GOLD, belt=GOLD, legs="#e0d8c4", boots="#8a7a5a"),
            v(skin=LIGHT, hair=GREY, hair_style="bald", eyes="#3f5f7a", body="robe", main="#ece6d6", second="#3a5a9a",
              trim=GOLD, belt="#3a5a9a", legs="#e0d8c4", boots="#6a5a40", tabard="#3a5a9a", emblem=GOLD),
        ]),
    "holy_knight": dict(
        title="Holy Knight of Lubelius",
        variants=[
            v(skin=FAIR, hair=BLOND, hair_style="short", eyes="#3f6d8f", body="plate", main="#e8e8ea", second="#3a5a9a",
              trim=GOLD, belt="#3a5a9a", legs="#d0d4da", boots="#c9ced6", cloak="#ece6d6", tabard="#ece6d6",
              emblem=GOLD),
            v(skin=MEDIUM, hair=BLACK, hair_style="swept", eyes="#3a2a22", head="coif", head_color="#c9ced6",
              body="plate", main="#dcdfe4", second="#3a5a9a", trim=GOLD, belt="#3a5a9a", legs="#c9ced6",
              boots="#b9c0c7", cloak="#3a5a9a", tabard="#ece6d6", emblem=GOLD),
        ]),
    "englassia_knight": dict(
        title="knight of Englassia",
        variants=[
            v(skin=LIGHT, hair=CHESTNUT, hair_style="short", eyes="#4a6a8a", body="plate", main=STEEL, second="#1f2f5a",
              trim=GOLD, belt=DARK_LEATHER, legs="#1f2f5a", boots=IRON, tabard="#1f2f5a", emblem="#b83a3a",
              cloak="#1f2f5a"),
            v(skin=TAN, hair=DARK, hair_style="crop", beard=DARK, beard_style="short", eyes="#4a3a2a", head="helm",
              head_color=STEEL, body="chain", main=IRON, second="#1f2f5a", trim=GOLD, belt=DARK_LEATHER,
              legs="#2a2f3a", boots=IRON, tabard="#1f2f5a", emblem="#b83a3a", gloves=IRON),
        ]),
    # Tensura's own Falmuth knight (the tensura:falmuth_knight entity) is a 64x64 player-layout skin: Easy NPC draws it
    # straight from the installed mod. All Rights Reserved, so it is referenced, never copied into the pack.
    "falmuth_knight": dict(
        title="knight of Falmuth (Tensura's own texture)",
        variants=[dict(slim=False, texture="tensura:textures/entity/human/falmuth_knight.png")]),
    # ---- Jura's peoples -----------------------------------------------------------------------------------------------
    "goblin": dict(
        title="goblin of the Jura forest",
        variants=[
            v(race="goblin", skin="#7f9a4a", hair="#3a3428", hair_style="crop", eyes="#e0c040", body="rags",
              main="#7a6a4a", second="#7f9a4a", trim="#5a4a32", belt="#5a4a32", legs="#6a5a3a", boots="#7f9a4a"),
            v(race="goblin", skin="#6a8a44", hair="#2a2620", hair_style="bald", eyes="#d84a3a", head="bandana",
              head_color="#8a3a2a", body="rags", main="#5a4a32", second="#6a8a44", trim="#3a2e20", belt="#3a2e20",
              legs="#5a4a32", boots="#6a8a44", sash="#5a4a32"),
        ]),
    "hobgoblin": dict(
        title="hobgoblin of Tempest",
        variants=[
            v(race="hobgoblin", skin="#9aa86e", hair="#2f2a2a", hair_style="short", eyes="#c0402a", body="vest",
              main="#6a4a2e", second="#d8ccb0", trim="#4a3420", belt=DARK_LEATHER, legs="#5a5a4a", boots=BOOT,
              pauldrons=IRON),
            v(race="hobgoblin", slim=True, skin="#a3b07a", hair="#5a3a5a", hair_style="long", eyes="#c0402a",
              body="kimono", main="#3a5a8a", second="#e8dcc0", trim="#e2b84a", belt="#e2b84a", legs="#2f4a6a",
              boots="#5a4632"),
        ]),
    "kijin": dict(
        title="kijin (ogre-folk) of Tempest",
        variants=[
            v(race="kijin", skin="#efd2bd", hair="#3a3a52", hair_style="tied", eyes="#b83a3a", head="horns",
              head_color="#f2ecdc", body="kimono", main="#2a2a36", second="#d8d0c0", trim="#b83a3a", belt="#b83a3a",
              legs="#3a3448", boots="#2a2232"),
            v(race="kijin", slim=True, skin="#f3dccb", hair="#c8c8d8", hair_style="long", eyes="#8a3ab0", head="horns",
              head_color="#2a2a30", body="kimono", main="#e8e2d8", second="#8a2f3a", trim="#8a2f3a", belt="#5a2a4a",
              legs="#8a2f3a", boots="#3a2a2a"),
        ]),
    "lizardman": dict(
        title="lizardman of Lake Siss",
        variants=[
            v(race="lizard", skin="#4f8a5b", hair="#2f5a3a", eyes="#e8c63a", second="#c9c48a", body="chain",
              main="#7d858d", trim="#3a7ab0", belt="#5e3d27", legs="#4f8a5b", boots="#3f6e4a", tabard="#3a7ab0",
              emblem="#c9c48a"),
            v(race="lizard", skin="#3f6e7a", hair="#2a4a52", eyes="#e8a83a", second="#c8c0a0", body="rags",
              main="#6a5a3a", trim="#3a7ab0", belt="#5e3d27", legs="#3f6e7a", boots="#2f5660", sash="#5e3d27"),
        ]),
    "tempest_citizen": dict(
        title="citizen of Tempest",
        variants=[
            v(skin=LIGHT, hair=DARK, hair_style="short", eyes="#4a3a2a", body="kimono", main="#3a5a8a", second="#e8dcc0",
              trim="#e2b84a", belt="#e2b84a", legs="#4a4a5a", boots="#5a4632"),
            v(slim=True, skin=MEDIUM, hair=CHESTNUT, hair_style="long", eyes="#4a6a3a", body="kimono", main="#6a8a5a",
              second="#e8dcc0", trim="#3a5a8a", belt="#3a5a8a", legs="#5a6a4a", boots="#5a4632"),
        ]),
    # ---- The enemies of the roads (design/data/enemies.toml; our interpretation): patched, mud-coloured, no guild plate --
    "bandit": dict(
        title="bandit of the trade roads",
        variants=[
            v(skin=TAN, hair=DARK, hair_style="crop", beard=DARK, beard_style="short", eyes="#4a3a2a", head="bandana",
              head_color="#6a2a22", body="rags", main="#6a5a42", second="#4a3e30", trim="#3a2e22", belt=DARK_LEATHER,
              legs="#4a4034", boots=BOOT, sash="#6a2a22", gloves=DARK_LEATHER),
            v(skin=LIGHT, hair=CHESTNUT, hair_style="long", eyes="#4a5a3a", head="hood", head_color="#4a4a32",
              body="jerkin", main="#5a4a32", second="#7a6a4a", trim="#2f2418", belt=LEATHER, legs="#3f3a2c",
              boots=BOOT, cloak="#4a4a32"),
            v(skin=DEEP, hair=BLACK, hair_style="bald", beard=BLACK, beard_style="goatee", eyes="#3a2a22", body="vest",
              main="#3a3026", second="#8a7a5a", trim="#2a221a", belt=DARK_LEATHER, legs="#4a3a2c", boots=BOOT,
              pauldrons=IRON, sash=DARK_LEATHER),
        ]),
    "highwayman": dict(
        title="highwayman of the Blumund road",
        variants=[
            v(skin=FAIR, hair=BLACK, hair_style="tied", eyes="#3f5f7a", head="cap", head_color="#2a2226", body="coat",
              main="#2f2a30", second="#8a2f2a", trim="#b8913f", belt=DARK_LEATHER, legs="#2a2630", boots=BOOT,
              cloak="#1f1c22", gloves="#2a2226"),
            v(skin=MEDIUM, hair=RED, hair_style="swept", beard=RED, beard_style="moustache", eyes="#4a3a2a",
              head="hood", head_color="#3a2f2a", body="coat", main="#4a2f2a", second="#d8ccb0", trim="#7d858d",
              belt=DARK_LEATHER, legs="#2f2a26", boots=BOOT, cloak="#3a2f2a", sash="#8a2f2a", gloves=DARK_LEATHER),
        ]),
    "deserter": dict(
        title="Falmuth deserter (a torn royal tabard)",
        variants=[
            v(skin=LIGHT, hair=BROWN, hair_style="crop", beard=BROWN, beard_style="short", eyes="#4a5a6a", body="chain",
              main=IRON, second="#3a3a3a", trim="#486c99", belt=DARK_LEATHER, legs="#3a3630", boots=BOOT,
              tabard="#283c67", emblem="#6a6450", gloves=DARK_LEATHER),
            v(skin=RUDDY, hair=BLOND, hair_style="short", eyes="#3f6d8f", head="coif", head_color=IRON, body="chain",
              main="#6d747a", second="#283c67", trim="#5a5040", belt=LEATHER, legs="#2f3340", boots=BOOT,
              cloak="#4a4438", tabard="#283c67", emblem="#b5d1dc"),
            v(skin=TAN, hair=GREY, hair_style="bald", beard=GREY, beard_style="full", eyes="#4a3a2a", body="jerkin",
              main=DARK_LEATHER, second="#283c67", trim=IRON, belt=DARK_LEATHER, legs="#3a3630", boots=BOOT,
              pauldrons=IRON, sash="#283c67"),
        ]),
    "rogue_adventurer": dict(
        title="rogue adventurer (struck from the Free Guild's rolls)",
        variants=[
            v(skin=LIGHT, hair="#3a3438", hair_style="swept", eyes="#6a3a3a", head="hood", head_color="#2a2a2e",
              body="jerkin", main="#2a2a2e", second="#5a2a2a", trim=STEEL, belt=DARK_LEATHER, legs="#26262a",
              boots=BOOT, cloak="#2a2a2e", sash="#5a2a2a", gloves=DARK_LEATHER),
            v(skin=MEDIUM, hair=BLOND, hair_style="short", beard=BLOND, beard_style="goatee", eyes="#4a6a3a",
              body="chain", main=IRON, second="#3a2f3a", trim="#5a2a2a", belt=DARK_LEATHER, legs="#2f2a30", boots=BOOT,
              cloak="#4a2a2a", gloves=DARK_LEATHER),
        ]),
    # ---- Outcast Society (the pack's own faction): a hooded, purple-cloaked contact ---------------------------------
    "outcast": dict(
        title="hooded contact of the Outcast Society",
        variants=[
            v(skin=LIGHT, hair=BLACK, hair_style="short", eyes="#9a8ab8", head="hood", head_color="#3a2a4a",
              body="coat", main="#2a2230", second="#4a3a5a", trim="#d8d2e4", belt=DARK_LEATHER, legs="#2a2630",
              boots=BOOT, cloak="#3a2a4a", gloves="#2a2230", sash="#5a4a6a"),
        ]),
}


def variants(look: str) -> list:
    return LOOKS[look]["variants"]


def file_name(look: str, n: int) -> str:
    """The PNG of our own variant n (1-based)."""
    return f"look_{look}_{n}.png"


def texture(look: str, n: int) -> str:
    """The resource location Easy NPC reads for variant n (1-based)."""
    spec = variants(look)[n - 1]
    return spec.get("texture") or f"ttl:textures/entity/npc/{file_name(look, n)}"


def candidates(look: str, model: str) -> list:
    """1-based variant numbers whose arm width fits the Easy NPC model (humanoid or humanoid_slim)."""
    slim = model == "humanoid_slim"
    return [i + 1 for i, s in enumerate(variants(look)) if bool(s.get("slim")) == slim]


def pick(look: str, name: str, model: str) -> int:
    """The variant a named NPC wears: CRC-32 of the name over the fitting variants. Stable across runs and machines."""
    fits = candidates(look, model)
    if not fits:
        raise ValueError(f"look {look!r} has no {model} variant")
    return fits[zlib.crc32(name.strip().lower().encode("utf-8")) % len(fits)]


def problems(look, model: str, name) -> list:
    """Why a data row's look cannot be used ([] = fine); for the validators."""
    if not isinstance(look, str) or look not in LOOKS:
        return [f"look {look!r} is not in tools/npc_looks.py LOOKS ({', '.join(sorted(LOOKS))})"]
    if not candidates(look, model):
        return [f"look {look!r} has no {model} variant"]
    if not isinstance(name, str) or not name.strip():
        return ["a look needs a name (or look_name) to pick the variant from"]
    return []
