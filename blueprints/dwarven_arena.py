"""The Dwarven Arena: Yasuke's `dwarf_arena` export (Tensura's Gazel Dwargo fight hall, 69x27x51), as a venue for duels.

Source: blueprints/assets/gazel_throne.nbt (byte for byte Tensura 2.0.1.5 `dwarf_village/building/dwarf_arena.nbt`, the
same file blueprints/dwargon.py cuts the throne room from). Owner request (#5): the arena without the royal warp pad, the
Dwargo boss and the black stained glass layers on the outside. What this blueprint does with the export:
  - the black stained glass shell (30,666 blocks, the void-facing envelope the mod's boss dimension needs) is dropped: the
    hall's stone, tuff and deepslate walls stand on their own and the placer fits them into the terrain;
  - the nine `royal_dwarven_warp_pad` blocks (the entry pad of the boss pit, x 1-3 z 24-26) and the four `stone_warp_pad`
    exit pads are gone. They are real teleporters (to the spawn point): no warp pad stays in the build;
  - the export holds no entity, so there is no Dwargo to strip here: the boss only ever came from LabyrinthHandler's
    code, and nothing in this build summons it (a challenge in arenas.toml uses waves only, no boss);
  - the developers' hidden nook (player heads with real account names, a sign, the second set of pads, at x 5-10 y 20-24
    z 31-36) is filled with tuff; its glass walls become tuff too, so the hall's shell stays closed;
  - the boss dimension never spawns monsters, the Tensura world does: every floor spot a monster could spawn on (about 185
    dark ones, mostly along the pit walls and on the dais) gets a glowstone tile instead of its floor block;
  - an entrance: the pad alcove at the west end of the pit gets a door (3 wide, 3 tall) and a small forecourt, because the
    hall had no way in other than the pads.
Block entity data does not survive a structure file (the pack's loader), so the yellow Dwargon banners are plain.

Layout (blueprint coordinates, the export shifted by +6 x and -1 y; the floor of the pit is the ground layer y 0, you
walk at y 1): forecourt x 0-5, door x 6, pad alcove x 7-10, the pit x 11-46 (pillars in rows, the boss pit; fighters stand
here), the stairs up at x 47-49, the throne dais x 48-68 at y 5-6 (red runner, Gazel's red nether brick throne without
Gazel: the spectators' gallery) and the rock behind it. SIZE (75, 26, 51). Anchor: the forecourt, blueprint (3, 1, 25),
facing east into the hall.
"""
from pathlib import Path

from _sites_lib import light_up
from blueprint import from_structure

SIZE = (75, 26, 51)
OFF = (6, -1, 0)
AIR = "minecraft:air"
ANCHOR = (3, 1, 25)
SOURCE = Path(__file__).resolve().parent / "assets" / "gazel_throne.nbt"

# Export coordinates of the developers' nook; everything in NOOK_INNER is filled, glass touching it becomes tuff.
NOOK_INNER = (6, 21, 32, 9, 23, 35)
NOOK_BOX = (5, 20, 31, 10, 24, 36)
GLASS = "minecraft:black_stained_glass"
FILL = "minecraft:tuff"
DOOR_Z = (24, 26)       # export z of the door (the pad alcove is z 24-26)
DOOR_Y = (2, 4)         # export y of the door cells; the alcove roof (y 6) and its lintel (y 5) stay
# Standing spots (blueprint, feet level) the arena of design/data/arenas.toml uses: kept clear and checked by the tests.
SPOTS = {
    "spawn_a": (15, 1, 25), "spawn_b": (43, 1, 25),
    "mob_0": (30, 1, 25), "mob_1": (20, 1, 25), "mob_2": (40, 1, 25), "mob_3": (30, 1, 11), "mob_4": (30, 1, 39),
}


def inside(p, box):
    return all(box[i] <= p[i] <= box[i + 3] for i in range(3))


def shift(p):
    return (p[0] + OFF[0], p[1] + OFF[1], p[2] + OFF[2])


def build(bp):
    src = from_structure("dwarf_arena", SOURCE)
    for p, state in src.blocks.items():
        name = state.split("[", 1)[0]
        if name == GLASS:
            if not inside(p, NOOK_BOX):
                continue
            state = FILL
        elif "warp_pad" in name or name in ("minecraft:player_head", "minecraft:oak_sign"):
            state = AIR
        if inside(p, NOOK_INNER):
            state = FILL
        if p[1] == 0:
            continue
        bp.set(*shift(p), state)

    # The door through the west wall of the pad alcove, with the alcove floor level with the forecourt.
    for z in range(DOOR_Z[0], DOOR_Z[1] + 1):
        for y in range(DOOR_Y[0], DOOR_Y[1] + 1):
            bp.set(*shift((0, y, z)), AIR)
    bp.fill(*shift((1, 2, 24)), *shift((3, 2, 26)), AIR)

    # Forecourt: stone brick paving, a low wall at each side of the door with a lantern on top.
    bp.fill(0, 0, 21, 5, 0, 29, "minecraft:stone_bricks")
    for z in (22, 28):
        bp.fill(5, 1, z, 5, 2, z, "minecraft:stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        bp.set(5, 3, z, "minecraft:lantern[hanging=false]")
    for z in (23, 27):
        bp.set(5, 1, z, "minecraft:stone_brick_slab[type=bottom]")

    # Monsters spawn in the dark and a duel must not be interrupted by one: a lit tile (flush with the floor) under every
    # dark standing spot of the pit and the dais, as the other builds do (_sites_lib.light_up).
    cands = [(x, y, z) for x in range(7, SIZE[0]) for z in range(SIZE[2]) for y in range(1, 12)]

    def add_light(x, y, z):
        bp.set(x, y - 1, z, "minecraft:glowstone")

    light_up(bp, cands, add_light, limit=300, spread=5)
