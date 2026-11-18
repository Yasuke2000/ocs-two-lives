// Life 1's dimensions are a world without Tensura: its mobs never spawn there (master plan §1).
// Arrival points are safe ground: no hostile mob spawns within SAFE.radius of Wayfarer's Rest (Life 1 arrives
// there, often at night — test bots were killed within seconds by the crowd around it) or of Tempest (Life 2).
// Mobs can still walk in from outside; this only keeps the arrival square from becoming a spawner.
const TtlSafeSpawns = {
  ZONES: [
    { dim: 'ttl:mortal_realm', x: 0, z: 0, radius: 48 },
    { dim: 'minecraft:overworld', x: 0, z: 0, radius: 56 }
  ],

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
