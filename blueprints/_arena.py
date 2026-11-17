"""Shared shell for the Trial of the Soul arenas (one per Last Wish, see pack/kubejs/.../trial_defs.js).

Every arena is 33x33 with its centre (the trial's origin) at blueprint x=16, z=16. Layer y=0 is the floor
(the Freedom arena lifts everything by FREEDOM_PIT so its pit sits below the course). Walls are visible up
to `wall_height`, then invisible barrier up to the ceiling, so nobody climbs out or falls into the void.
Trial logic depends on fixed spots (start pads, exits, pens, lecterns): keep those in each blueprint.
"""

SIZE = (33, 17, 33)
C = 16          # centre on x and z
CEILING = 16    # barrier ceiling layer


def at(dx: int, dz: int) -> tuple[int, int]:
    """Blueprint x, z of a spot given relative to the arena centre (the trial's own coordinates)."""
    return C + dx, C + dz


def shell(bp, floor: str, wall: str, trim: str, wall_height: int = 4, base: int = 0, pillar: str | None = None,
          light: str = "minecraft:sea_lantern", ceiling: int = CEILING) -> None:
    """Floor, walls, corner pillars, floor lights and the barrier cage. `base` is the floor layer."""
    bp.fill(0, base, 0, 32, base, 32, floor)
    for y in range(base + 1, base + wall_height + 1):
        state = trim if y == base + wall_height else wall
        for i in range(33):
            for x, z in ((i, 0), (i, 32), (0, i), (32, i)):
                bp.set(x, y, z, state)
    for y in range(base + wall_height + 1, ceiling):
        for i in range(33):
            for x, z in ((i, 0), (i, 32), (0, i), (32, i)):
                bp.set(x, y, z, "minecraft:barrier")
    bp.fill(0, ceiling, 0, 32, ceiling, 32, "minecraft:barrier")
    if pillar:
        for x, z in ((1, 1), (31, 1), (1, 31), (31, 31)):
            bp.pillar(x, z, base + 1, base + wall_height + 2, pillar)
            bp.set(x, base + wall_height + 3, z, "minecraft:lantern[hanging=false]")
    for dx, dz in ((-8, -8), (8, -8), (-8, 8), (8, 8), (0, 0)):
        x, z = at(dx, dz)
        bp.set(x, base, z, light)


def ring(bp, y: int, radius: float, state: str, width: float = 1.0) -> None:
    bp.disc(C, y, C, radius, state, inner=radius - width)
