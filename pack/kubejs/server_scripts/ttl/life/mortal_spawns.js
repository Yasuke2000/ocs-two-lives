// Life 1's dimensions are a world without Tensura: its mobs never spawn there (master plan §1).
// Arrival points are safe ground: no hostile mob spawns within a zone's radius of Wayfarer's Rest (Life 1 arrives
// there, often at night — test bots were killed within seconds by the crowd around it), of Tempest (Life 2's capital)
// or of the Life 2 arrival on Jura's rim (owner 19/11/2026: wild direwolves spawned right on the arrival point; outside
// the radius the rim stays wild). Mobs can still walk in from outside; this only keeps the square from becoming a
// spawner. The overworld centres come from design/data/anchors.toml: Tempest through TtlAnchors (generated/anchors.js),
// the arrival through TtlData.arrival.life2 (x/z = the arrival anchor, safe_radius) — both generated, priority 200.
// The graded zones round Tempest (fewer hostiles out to r 400, a cap on animals) are TtlSpawnZones below.
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

  // A spell's summon (Iron's IMagicSummon: summon_vex's vexes, raise_dead's undead, ...) carries no tag but is cast by a
  // player, not spawned by the world: a Life 1 soul summoning vexes at Wayfarer's Rest saw them vanish (issue #104).
  summonType: undefined,
  summoned(entity) {
    if (this.summonType === undefined) {
      try {
        this.summonType = Java.loadClass('io.redspace.ironsspellbooks.entity.mobs.IMagicSummon')
      } catch (e) {
        console.warn(`[ttl] spawns: Iron's IMagicSummon not found, spell summons count as natural spawns: ${e}`)
        this.summonType = null
      }
    }
    try {
      return !!this.summonType && entity instanceof this.summonType
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
  // Only natural spawns are refused: trial mobs and spawner mobs carry tags or come from commands, spell summons are
  // recognised by their type.
  if (TtlSafeSpawns.hostile(entity) && entity.getTags().isEmpty() && TtlSafeSpawns.inZone(entity) && !TtlSafeSpawns.summoned(entity)) event.cancel()
})

// Graded zones round the Life 2 towns (design/data/spawns.toml, TtlData.spawns; owner 19/11/2026: fewer mobs next to
// Tempest). Only natural spawns (MobSpawnType natural, chunk_generation, patrol): within town_radius no hostile spawn,
// out to reduced_radius a hostile spawn goes ahead with chance hostile_keep, and within passive_radius a passive animal is
// refused once passive_cap animals stand in its passive_box square. Bosses (bosses/boss.js has its own rule), arenas,
// events, choice scenes, summons, spawners and breeding are never touched; TtlSafeSpawns.ZONES above (and so the
// magicule shelter of life/mortal_immunity.js and the wild bosses' margin) stay as they are.
// Test hooks: /ttl spawns zone <x> <z> (what the rule does there), /ttl spawns expect <x> <z> <none|reduced|open>.
const TtlSpawnZones = {
  NATURAL: /^(natural|chunk_generation|patrol)$/i,
  // natural spawns in a zone since the start: hostiles refused in a town, refused / kept in a band, animals capped
  stats: { town: 0, band: 0, kept: 0, capped: 0 },

  zones() {
    if (this.z !== undefined) return this.z
    var out = []
    var conf = typeof TtlData !== 'undefined' && TtlData.spawns ? TtlData.spawns.zone || {} : {}
    Object.keys(conf).forEach(id => {
      var c = conf[id]
      var a = typeof TtlAnchors !== 'undefined' ? TtlAnchors[c.anchor] : null
      if (!a) {
        console.warn(`[ttl] spawns: zone ${id}: anchor ${c.anchor} unknown, zone off`)
        return
      }
      out.push({ id: id, dim: 'minecraft:overworld', x: a.x, z: a.z, town: c.town_radius, reduced: c.reduced_radius,
        keep: c.hostile_keep, passive: c.passive_radius || 0, cap: c.passive_cap || 0, box: c.passive_box || 32 })
    })
    this.z = out
    return out
  },

  // The zone round (x, z) in dim and the squared distance, or null.
  at(dim, x, z) {
    var zs = this.zones()
    for (var i = 0; i < zs.length; i++) {
      var s = zs[i]
      if (s.dim !== dim) continue
      var d2 = (x - s.x) * (x - s.x) + (z - s.z) * (z - s.z)
      if (d2 <= Math.max(s.reduced, s.passive) * Math.max(s.reduced, s.passive)) return { zone: s, d2: d2 }
    }
    return null
  },

  // 'none' (no hostile spawn), 'reduced' (hostile_keep of them), 'open' at a point.
  band(dim, x, z) {
    var hit = this.at(dim, x, z)
    if (!hit) return 'open'
    if (hit.d2 <= hit.zone.town * hit.zone.town) return 'none'
    if (hit.d2 <= hit.zone.reduced * hit.zone.reduced) return 'reduced'
    return 'open'
  },

  // true when this natural spawn is refused. roll: a number in [0, 1) (Math.random by default).
  refuse(entity, type, roll) {
    if (!this.NATURAL.test(String(type))) return false
    var dim = String(entity.level.dimension)
    var x = entity.getX()
    var z = entity.getZ()
    var hit = this.at(dim, x, z)
    if (!hit) return false
    var s = hit.zone
    if (entity.isMonster()) {
      if (typeof TtlBoss !== 'undefined' && TtlBoss.byEntity(String(entity.type))) return false
      if (hit.d2 <= s.town * s.town) {
        this.stats.town++
        return true
      }
      if (hit.d2 > s.reduced * s.reduced) return false
      var no = (roll === undefined ? Math.random() : roll) >= s.keep
      if (no) this.stats.band++
      else this.stats.kept++
      return no
    }
    if (s.cap > 0 && hit.d2 <= s.passive * s.passive && entity.isAnimal() && this.crowded(entity, s)) {
      this.stats.capped++
      return true
    }
    return false
  },

  crowded(entity, s) {
    var h = s.box / 2
    var AABB = Java.loadClass('net.minecraft.world.phys.AABB')
    var level = entity.level
    var box = new AABB(entity.getX() - h, level.getMinBuildHeight(), entity.getZ() - h, entity.getX() + h, level.getMaxBuildHeight(), entity.getZ() + h)
    var n = 0
    level.getEntitiesWithin(box).forEach(e => {
      if (e !== entity && e.isAlive() && e.isAnimal()) n++
    })
    return n >= s.cap
  }
}

try {
  EntityEvents.checkSpawn(event => {
    var refuse = false
    try {
      refuse = TtlSpawnZones.refuse(event.entity, event.type)
    } catch (e) {
      console.error(`[ttl] spawns: zone check failed: ${e}`)
    }
    // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
    if (refuse) event.cancel()
  })
} catch (e) {
  console.warn(`[ttl] spawns: EntityEvents.checkSpawn is not available, the graded zones are off (${e})`)
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var int = (ctx, n) => Arguments.INTEGER.getResult(ctx, n)
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var describe = (x, z) => {
    var hit = TtlSpawnZones.at('minecraft:overworld', x, z)
    var band = TtlSpawnZones.band('minecraft:overworld', x, z)
    if (!hit) return `${x} ${z}: ${band} (no spawn zone)`
    var s = hit.zone
    return `${x} ${z}: ${band} (zone ${s.id}, ${Math.round(Math.sqrt(hit.d2))} blocks from ${s.x} ${s.z}; town r ${s.town}, ` +
      `hostiles kept ${Math.round(s.keep * 100)} % to r ${s.reduced}, ${s.cap} animals per ${s.box} x ${s.box} to r ${s.passive})`
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('spawns')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('zone')
        .then(Commands.argument('x', Arguments.INTEGER.create(event))
          .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(ctx => {
            say(ctx, describe(int(ctx, 'x'), int(ctx, 'z')))
            var st = TtlSpawnZones.stats
            say(ctx, `natural spawns since the start: ${st.town} hostiles refused in a town, ${st.band} refused and ${st.kept} kept in a ` +
              `reduced band, ${st.capped} animals refused by the cap`)
            return 1
          }))))
      .then(Commands.literal('expect')
        .then(Commands.argument('x', Arguments.INTEGER.create(event))
          .then(Commands.argument('z', Arguments.INTEGER.create(event))
            .then(Commands.argument('band', Arguments.STRING.create(event)).executes(ctx => {
              var x = int(ctx, 'x')
              var z = int(ctx, 'z')
              var want = String(Arguments.STRING.getResult(ctx, 'band'))
              var got = TtlSpawnZones.band('minecraft:overworld', x, z)
              if (got !== want) {
                ctx.source.sendSystemMessage(Text.red(`ttl: expected the spawn band at ${x} ${z} to be ${want}, it is ${describe(x, z)}`))
                return 0
              }
              say(ctx, `spawns: ${describe(x, z)} as expected`)
              return 1
            })))))))
})
