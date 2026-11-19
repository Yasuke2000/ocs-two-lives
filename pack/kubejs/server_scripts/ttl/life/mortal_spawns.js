// Life 1's dimensions are a world without Tensura: its mobs never spawn there (master plan §1).
// Arrival points are safe ground: no hostile mob spawns within a zone's radius of Wayfarer's Rest (Life 1 arrives
// there, often at night — test bots were killed within seconds by the crowd around it), of Tempest (Life 2's capital)
// or of the Life 2 arrival on Jura's rim (owner 19/11/2026: wild direwolves spawned right on the arrival point; outside
// the radius the rim stays wild). Mobs can still walk in from outside; this only keeps the square from becoming a
// spawner. The overworld centres come from design/data/anchors.toml: Tempest through TtlAnchors (generated/anchors.js),
// the arrival through TtlData.arrival.life2 (x/z = the arrival anchor, safe_radius) — both generated, priority 200.
const TtlSafeSpawns = {
  ZONES: (function () {
    var zones = [{ dim: 'ttl:mortal_realm', x: 0, z: 0, radius: 48 }]
    var t = typeof TtlAnchors !== 'undefined' ? TtlAnchors.tempest : null
    if (t) zones.push({ dim: 'minecraft:overworld', x: t.x, z: t.z, radius: 56, id: 'tempest' })
    var a = typeof TtlData !== 'undefined' && TtlData.arrival ? TtlData.arrival.life2 : null
    if (a && a.safe_radius > 0) zones.push({ dim: 'minecraft:overworld', x: a.x, z: a.z, radius: a.safe_radius, id: 'arrival' })
    return zones
  })(),

  hostile(entity) {
    try {
      // entity.getType() is the id string in KubeJS (no getCategory); isMonster() is the Enemy check. The old
      // category test threw, was swallowed here, and so no hostile mob was ever refused.
      return !!entity.isMonster()
    } catch (e) {
      return false
    }
  },

  inZone(entity) {
    var dim = String(entity.level.dimension)
    var x = entity.getX()
    var z = entity.getZ()
    return this.ZONES.some(s => s.dim === dim && (x - s.x) * (x - s.x) + (z - s.z) * (z - s.z) <= s.radius * s.radius)
  }
}

EntityEvents.spawned(event => {
  var entity = event.entity
  if (entity.isPlayer()) return
  if (TtlLife.isMortal(entity.level.dimension) && String(entity.type).startsWith('tensura:')) {
    event.cancel()
    return
  }
  // Only natural spawns are refused: trial mobs, summons and spawner mobs carry tags or come from commands.
  if (TtlSafeSpawns.hostile(entity) && entity.getTags().isEmpty() && TtlSafeSpawns.inZone(entity)) event.cancel()
})
