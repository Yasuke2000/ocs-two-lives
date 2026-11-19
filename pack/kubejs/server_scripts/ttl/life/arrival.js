// Where Life 2 souls arrive in the Tensura world, and the world spawn (design/data/arrival.toml → TtlData.arrival).
//
// Veldora's leaked magicule soaks the Jura forest, so a weak newcomer must not appear in, or stroll to, Tempest
// (anchors.toml tempest): Jura's biomes form rings round it (canon_regions.json, J "zones", by radius; repainted into
// Lerfing's map by the import), an ancient-forest core, a dark-forest band and a safe rim beyond. The arrival point is on the rim, on the road from Tempest to
// the Dwargon gate. Brand-new players stand at the world spawn for about 2 s before their first teleport, so the
// world spawn is the arrival point too (and so is the respawn point of a Life 2 soul that dies).
//
// Grounding, once per `version` (and again after an overworld reset, world_reset.js):
// 1. provisional: spawn and teleports use the surface column at x, z right away (`positioned over`);
// 2. hold the area with chunk tickets (life/chunk_hold.js), wait DELAY_TICKS and until it is loaded, then look
//    within `search` blocks for natural, open, level ground (a clearing: soil underfoot, no canopy above, no water, heights within 2 of each other) closest to x, z; fall
//    back to the plain surface at x, z;
// 3. store "x y z" in persistentData ttl.arrival.pos (+ ttl.arrival.version) and `setworldspawn` there.
// tempest.js and world_reset.js skip their own setworldspawn while TtlArrival.active(). Without a [life2] entry
// everything falls back to Tempest's green (ttl.tempest.arrival) as before.
//
// Op commands: /ttl arrival (where it is) · /ttl arrival expect <player> near <blocks> | alive (bot tests).
const TtlArrival = {
  POS: 'ttl.arrival.pos',
  VERSION: 'ttl.arrival.version',
  DELAY_TICKS: 400,
  PROBE_STEP: 4,
  SOIL: ['minecraft:grass_block', 'minecraft:dirt', 'minecraft:podzol', 'minecraft:coarse_dirt', 'minecraft:rooted_dirt', 'minecraft:moss_block'],
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest', 'flower', 'tulip',
    'poppy', 'dandelion', 'orchid', 'allium', 'azure_bluet', 'cornflower', 'lily_of_the_valley', 'sunflower', 'lilac', 'peony', 'rose_bush'],
  busy: false,

  config() {
    try {
      var spot = TtlData.arrival.life2
      return spot && typeof spot.x === 'number' ? spot : null
    } catch (e) {
      return null
    }
  },

  // True when a [life2] arrival is configured: it owns the world spawn.
  active() {
    return this.config() !== null
  },

  // Grounded "x y z" for the current config version, or ''.
  stored(server) {
    var cfg = this.config()
    if (!cfg) return ''
    var data = server.persistentData
    if (data.getInt(this.VERSION) !== cfg.version) return ''
    return String(data.getString(this.POS))
  },

  run(server, cmd) {
    return server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  // Teleports a Life 2 soul to the arrival; false when none is configured (the caller falls back to Tempest).
  send(server, player) {
    var cfg = this.config()
    if (!cfg) return false
    var pos = this.stored(server)
    if (pos) {
      this.run(server, `tp ${player.username} ${pos} ${cfg.yaw} 0`)
    } else {
      // Not grounded yet (fresh world, or a reset a moment ago): the surface column of x, z, generated on demand.
      server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} positioned ${cfg.x + 0.5} 0 ${cfg.z + 0.5} positioned over motion_blocking_no_leaves run tp ${player.username} ~ ~ ~ ${cfg.yaw} 0`)
    }
    return true
  },

  // World spawn: the grounded point, else the surface column of x, z.
  applySpawn(server) {
    var cfg = this.config()
    if (!cfg) return
    var pos = this.stored(server)
    if (pos) {
      var p = pos.split(' ')
      this.run(server, `setworldspawn ${Math.floor(Number(p[0]))} ${Math.floor(Number(p[1]))} ${Math.floor(Number(p[2]))}`)
    } else {
      server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} positioned ${cfg.x} 0 ${cfg.z} positioned over motion_blocking_no_leaves run setworldspawn ~ ~ ~`)
    }
  },

  // Heightmaps through Java, as in tempest.js: ground = first free y above the terrain (trees and plants skipped),
  // top = first free y above everything that blocks motion (leaves included). null when that fails.
  heightmaps(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var skip = this.NOT_GROUND
      return {
        top: (x, z) => level.getHeight(Types.MOTION_BLOCKING, x, z),
        soil: (x, y, z) => this.SOIL.indexOf(String(level.getBlock(x, y - 1, z).id)) >= 0,
        ground: (x, z) => {
          var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
          for (var n = 0; n < 40 && y > -63; n++) {
            var id = String(level.getBlock(x, y - 1, z).id)
            if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
            y--
          }
          return y
        }
      }
    } catch (e) {
      console.warn(`[ttl] arrival: heightmaps unavailable (${e})`)
      return null
    }
  },

  // The clearing nearest to x, z within `search` blocks: soil underfoot, open sky, level; else the plain surface.
  find(server, cfg) {
    var hm = this.heightmaps(server)
    if (!hm) return null
    var step = this.PROBE_STEP
    var best = null
    for (var dz = -cfg.search; dz <= cfg.search; dz += step) {
      for (var dx = -cfg.search; dx <= cfg.search; dx += step) {
        var x = cfg.x + dx
        var z = cfg.z + dz
        var y = hm.ground(x, z)
        if (y <= -63 || !hm.soil(x, y, z) || hm.top(x, z) > y + 1) continue
        var lo = y
        var hi = y
        var near = [[step, 0], [-step, 0], [0, step], [0, -step]]
        for (var i = 0; i < near.length; i++) {
          var h = hm.ground(x + near[i][0], z + near[i][1])
          lo = Math.min(lo, h)
          hi = Math.max(hi, h)
        }
        if (hi - lo > 2) continue
        var score = (hi - lo) * 8 + Math.sqrt(dx * dx + dz * dz)
        if (best === null || score < best.score) best = { x: x, y: y, z: z, score: score, clearing: true }
      }
    }
    if (best) return best
    var y0 = hm.ground(cfg.x, cfg.z)
    return y0 > -63 ? { x: cfg.x, y: y0, z: cfg.z, score: 0, clearing: false } : null
  },

  // Grounds the arrival (see the header) unless it already is for this version.
  schedule(server) {
    var self = this
    var cfg = this.config()
    if (!cfg || this.busy) return
    if (this.stored(server)) {
      this.applySpawn(server)
      return
    }
    this.busy = true
    this.applySpawn(server)
    var r = cfg.search + 32
    var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, { x0: cfg.x - r, z0: cfg.z - r, x1: cfg.x + r, z1: cfg.z + r }, 'arrival')
    server.scheduleInTicks(this.DELAY_TICKS, () => TtlChunks.whenReady(server, hold, 40, 12000, (ready, missing) => {
      try {
        if (!ready && missing > 0) throw `${missing} chunk(s) still not loaded after 10 min`
        var spot = self.find(server, cfg)
        if (spot) {
          server.persistentData.putString(self.POS, `${spot.x + 0.5} ${spot.y} ${spot.z + 0.5}`)
          server.persistentData.putInt(self.VERSION, cfg.version)
          self.applySpawn(server)
          console.info(`[ttl] arrival grounded at ${spot.x} ${spot.y} ${spot.z} (${spot.clearing ? 'clearing' : 'plain surface'}, ${Math.round(Math.sqrt(Math.pow(spot.x - cfg.x, 2) + Math.pow(spot.z - cfg.z, 2)))} blocks from ${cfg.x} ${cfg.z}, version ${cfg.version})`)
        } else {
          console.warn(`[ttl] arrival: no ground found near ${cfg.x} ${cfg.z}; teleports use the surface column`)
        }
      } catch (e) {
        console.error(`[ttl] arrival grounding failed: ${e}`)
      }
      TtlChunks.release(server, hold)
      self.busy = false
    }))
  },

  // After an overworld reset the old terrain is gone: forget the grounded point and ground it again.
  reset(server) {
    server.persistentData.remove(this.POS)
    server.persistentData.remove(this.VERSION)
    this.busy = false
    this.schedule(server)
  }
}

ServerEvents.loaded(event => {
  try {
    TtlArrival.schedule(event.server)
  } catch (e) {
    console.error(`[ttl] arrival schedule failed: ${e}`)
  }
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] arrival command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var player = ctx => Arguments.PLAYER.getResult(ctx, 'target')

  var show = ctx => {
    var server = ctx.source.getServer()
    var cfg = TtlArrival.config()
    if (!cfg) {
      say(ctx, `Arrival: none configured, Tempest's green (${String(server.persistentData.getString('ttl.tempest.arrival')) || 'not placed'})`)
      return 1
    }
    var pos = TtlArrival.stored(server)
    var spawn = server.overworld().getSharedSpawnPos()
    var where = pos ? `${pos} (grounded)` : `surface at ${cfg.x} ${cfg.z} (not grounded yet)`
    say(ctx, `Arrival: ${where}, facing ${cfg.yaw}, version ${cfg.version}; world spawn ${spawn.getX()} ${spawn.getY()} ${spawn.getZ()}`)
    return 1
  }

  // Horizontal distance from the stored arrival (or the configured x, z while it is not grounded).
  var near = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx)
    var limit = Arguments.INTEGER.getResult(ctx, 'blocks')
    var cfg = TtlArrival.config()
    if (!cfg) throw 'no arrival configured (design/data/arrival.toml)'
    var dim = TtlLife.dimensionOf(target)
    if (dim !== TtlLife.OVERWORLD) throw `${target.username} is in ${dim}, not the Tensura world`
    var pos = TtlArrival.stored(server)
    var ax = pos ? Number(pos.split(' ')[0]) : cfg.x + 0.5
    var az = pos ? Number(pos.split(' ')[2]) : cfg.z + 0.5
    var d = Math.sqrt(Math.pow(target.x - ax, 2) + Math.pow(target.z - az, 2))
    if (d > limit) throw `${target.username} is ${Math.round(d)} blocks from the arrival (${Math.round(ax)} ${Math.round(az)}), expected within ${limit} (at ${Math.round(target.x)} ${Math.round(target.z)})`
    say(ctx, `arrival ${target.username}: ${Math.round(d)} blocks from ${Math.round(ax)} ${Math.round(az)} as expected`)
    return 1
  }

  var alive = ctx => {
    var target = player(ctx)
    if (!target.isAlive() || target.health <= 0) throw `${target.username} is dead (health ${target.health})`
    say(ctx, `arrival ${target.username}: alive, health ${Math.round(target.health)}`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('arrival')
      .requires(src => src.hasPermission(2))
      .executes(logged(show))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.literal('near')
            .then(Commands.argument('blocks', Arguments.INTEGER.create(event)).executes(logged(near))))
          .then(Commands.literal('alive').executes(logged(alive)))))))
})
