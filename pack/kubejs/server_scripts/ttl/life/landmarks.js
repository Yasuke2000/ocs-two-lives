// Places the canon landmarks of design/data/landmarks.toml (TtlData.landmarks) in the Tensura world with
// Tensura's own jigsaw structures: Rigurd's goblin village, the lizardmen of Lake Siss, the orc camp, the dwarf
// village on the Dwarven Road, ... Each landmark is placed once (persistentData ttl.landmark.<name>.version =
// its `version`), one at a time, after Tempest and Dwargon; world_reset.js places them again after an overworld
// reset. Op commands: /ttl landmark list | place <name|all> | where <name>.
//
// Per landmark:
// 1. hold the area (reach + the farthest candidate offset) with chunk tickets (life/chunk_hold.js, loaded in the
//    background, no synchronous `forceload` burst) and wait until every chunk is FULL; give up after LOAD_TIMEOUT;
// 2. survey the nominal spot and 16 candidates 32 and 64 blocks out (heightmaps): water fraction and ground
//    spread; drop candidates that come within `keepout` + reach of Tempest's or Dwargon's box; best first;
// 3. `place structure` (vanilla: skips the biome check, uses only the chunk, needs the chunks loaded, throws
//    when the start piece cannot generate); success is read back through `execute store success` into the
//    scoreboard ttl.landmark and a marker probe; on failure the next candidate is tried (up to TRIES);
// 4. register the structure start in its chunks (best effort, Java), because `/place structure` does not: the
//    structure's spawn_overrides (goblins, lizardmen, orcs and dwarves keep spawning inside) need it;
// 5. log `[ttl] landmark <name> placed: <structure> at <x> <y> <z>` and remember the spot for /ttl landmark where.
const TtlLandmarks = {
  OBJECTIVE: 'ttl.landmark',
  PROBE: 'ttl_landmark_probe',
  START_DELAY: 900, // after Tempest (300) and Dwargon have started placing
  LOAD_POLL: 40,
  LOAD_TIMEOUT: 12000, // 10 min: up to 625 fresh chunks generate in the background while the server ticks
  OFFSETS: [32, 64],
  TRIES: 4,
  BOOT_ATTEMPTS: 3, // boots in a row that may fail before a landmark waits for /ttl landmark place
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest', 'lily_pad'],
  queue: [],
  busy: false,

  all() {
    return TtlData.landmarks.landmark
  },

  find(name) {
    return this.all().find(l => l.name === name) || null
  },

  key(l, k) {
    return `ttl.landmark.${l.name}.${k}`
  },

  run(server, cmd) {
    return server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  // Tempest's and Dwargon's worked areas (box + margin), from their own scripts.
  keepouts() {
    var out = []
    var add = (label, get) => {
      try {
        var b = get()
        out.push({ label: label, x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 })
      } catch (e) {
        console.warn(`[ttl] landmarks: ${label} box unavailable (${e})`)
      }
    }
    add('Tempest', () => TtlTempest.box())
    add('Dwargon', () => TtlDwargon.box())
    return out
  },

  clearOf(l, x, z, boxes) {
    var need = TtlData.landmarks.keepout + l.reach
    return boxes.every(b => {
      var dx = Math.max(b.x0 - x, 0, x - b.x1)
      var dz = Math.max(b.z0 - z, 0, z - b.z1)
      return Math.sqrt(dx * dx + dz * dz) >= need
    })
  },

  candidates(l) {
    var out = [{ x: l.x, z: l.z, ring: 0 }]
    this.OFFSETS.forEach(d => {
      for (var i = 0; i < 8; i++) {
        var a = Math.PI * i / 4
        out.push({ x: l.x + Math.round(d * Math.cos(a)), z: l.z + Math.round(d * Math.sin(a)), ring: d })
      }
    })
    var boxes = this.keepouts()
    var self = this
    return out.filter(c => self.clearOf(l, c.x, c.z, boxes))
  },

  area(l) {
    var r = l.reach + this.OFFSETS[this.OFFSETS.length - 1] + 16
    return { x0: l.x - r, z0: l.z - r, x1: l.x + r, z1: l.z + r }
  },

  // Ground probe through Java heightmaps: { y, water } per column, trees and plants skipped. null when unavailable.
  probe(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var skip = this.NOT_GROUND
      return (x, z) => {
        var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
        var top = String(level.getBlock(x, y - 1, z).id)
        if (top.indexOf('water') >= 0 || top === 'minecraft:seagrass' || top === 'minecraft:kelp_plant') return { y: y, water: true }
        for (var n = 0; n < 40 && y > -63; n++) {
          var id = String(level.getBlock(x, y - 1, z).id)
          if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
          y--
        }
        return { y: y, water: false }
      }
    } catch (e) {
      console.warn(`[ttl] landmarks: heightmaps unavailable (${e}); trying candidates unsurveyed`)
      return null
    }
  },

  // 5x5 samples over the inner 60% of the reach: water fraction and land height spread -> score (lower = better).
  survey(l, c, at) {
    var r = Math.max(8, Math.round(l.reach * 0.6))
    var water = 0
    var ys = []
    for (var i = -2; i <= 2; i++) {
      for (var j = -2; j <= 2; j++) {
        var s = at(c.x + Math.round(i * r / 2), c.z + Math.round(j * r / 2))
        if (s.water) water++
        else ys.push(s.y)
      }
    }
    var wf = water / 25
    ys.sort((a, b) => a - b)
    var spread = ys.length ? ys[Math.floor(ys.length * 0.9)] - ys[Math.floor(ys.length * 0.1)] : 0
    var centre = at(c.x, c.z)
    var fit = true
    var score = spread + c.ring / 16
    if (l.surface === 'land') {
      fit = wf <= 0.25 && !centre.water
      score += wf * 40
    } else if (l.surface === 'water') {
      fit = wf >= 0.2 && wf <= 0.9
      score += Math.abs(wf - 0.55) * 30
    }
    return { fit: fit, score: score, water: wf, spread: spread, y: centre.y }
  },

  // `place structure` throws on failure (start piece cannot generate, chunks not loaded, unknown id), which
  // `execute store success` turns into 0; a marker summoned only on success, on the (new) surface at the spot,
  // carries the answer back. Returns that surface y, or null when the placement failed.
  placeAt(server, l, c) {
    var o = this.OBJECTIVE
    var probe = this.PROBE
    this.run(server, `scoreboard players set #ok ${o} 0`)
    var raw = server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} store success score #ok ${o} run place structure ${l.structure} ${c.x} 64 ${c.z}`)
    this.run(server, `execute if score #ok ${o} matches 1 positioned ${c.x} 0 ${c.z} positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~ {Tags:["${probe}"]}`)
    var y = null
    server.getLevel(TtlLife.OVERWORLD).getEntities().forEach(e => {
      if (e.getTags().contains(probe)) y = Math.floor(e.getY())
    })
    this.run(server, `kill @e[type=minecraft:marker,tag=${probe}]`)
    if (y === null && raw !== undefined && raw !== null) console.info(`[ttl] landmark ${l.name}: place structure returned ${raw}`)
    return y
  },

  // /place structure generates the start (deterministic: seed + chunk) but never records it in the chunks, so
  // spawn_overrides and "inside structure" checks miss it. Generate the same start again and record it.
  register(server, l, c) {
    try {
      var Registries = Java.loadClass('net.minecraft.core.registries.Registries')
      var ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')
      var ChunkPos = Java.loadClass('net.minecraft.world.level.ChunkPos')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var access = server.registryAccess()
      var structure = access.registryOrThrow(Registries.STRUCTURE).get(ResourceLocation.parse(l.structure))
      var gen = level.getChunkSource().getGenerator()
      var start = structure.generate(access, gen, gen.getBiomeSource(), level.getChunkSource().randomState(),
        level.getStructureManager(), level.getSeed(), new ChunkPos(c.x >> 4, c.z >> 4), 0, level, b => true)
      if (!start.isValid()) return null
      var origin = start.getChunkPos()
      var bb = start.getBoundingBox()
      level.getChunk(origin.x, origin.z).setStartForStructure(structure, start)
      for (var cx = bb.minX() >> 4; cx <= bb.maxX() >> 4; cx++) {
        for (var cz = bb.minZ() >> 4; cz <= bb.maxZ() >> 4; cz++) {
          var chunk = level.getChunk(cx, cz)
          chunk.addReferenceForStructure(structure, origin.toLong())
          chunk.setUnsaved(true)
        }
      }
      return `${bb.minX()} ${bb.minY()} ${bb.minZ()} ${bb.maxX()} ${bb.maxY()} ${bb.maxZ()}`
    } catch (e) {
      console.warn(`[ttl] landmark ${l.name}: placed, but the structure start could not be registered (${e}); its NPCs only spawn once`)
      return null
    }
  },

  place(server, l) {
    var data = server.persistentData
    var self = this
    var at = this.probe(server)
    var list = this.candidates(l).map(c => {
      c.s = at ? self.survey(l, c, at) : { fit: true, score: c.ring, water: -1, spread: -1, y: 0 }
      return c
    })
    var ranked = list.filter(c => c.s.fit).sort((a, b) => a.s.score - b.s.score)
    // Nothing fits the surface rule: still try the best-scoring spots rather than leave the landmark out.
    if (ranked.length === 0) {
      console.warn(`[ttl] landmark ${l.name}: no candidate fits surface=${l.surface}; trying the closest matches`)
      ranked = list.sort((a, b) => a.s.score - b.s.score)
    }
    var tries = ranked.slice(0, this.TRIES)
    for (var i = 0; i < tries.length; i++) {
      var c = tries[i]
      var y = this.placeAt(server, l, c)
      if (y === null) {
        console.warn(`[ttl] landmark ${l.name}: place structure failed at ${c.x} ${c.z} (try ${i + 1}/${tries.length})`)
        continue
      }
      var box = this.register(server, l, c)
      data.putInt(this.key(l, 'version'), l.version)
      data.putString(this.key(l, 'at'), `${c.x} ${y} ${c.z}`)
      data.putString(this.key(l, 'box'), box || '')
      data.putInt(this.key(l, 'fails'), 0)
      console.info(`[ttl] landmark ${l.name} placed: ${l.structure} at ${c.x} ${y} ${c.z} (try ${i + 1}, ` +
        `water ${c.s.water}, spread ${c.s.spread}${box ? `, box ${box}` : ', start not registered'}; version ${l.version})`)
      return true
    }
    data.putInt(this.key(l, 'fails'), data.getInt(this.key(l, 'fails')) + 1)
    console.error(`[ttl] landmark ${l.name}: ${l.structure} could not be placed near ${l.x} ${l.z} (${tries.length} spots tried)`)
    return false
  },

  // One landmark at a time: hold the chunks, wait until they are FULL, place, release, next. Not placed when the
  // area is still not loaded after LOAD_TIMEOUT (a failed boot attempt): surveying a missing chunk would load it
  // synchronously, the stall the tickets avoid.
  pump(server) {
    if (this.busy || this.queue.length === 0) return
    var l = this.queue.shift()
    var self = this
    this.busy = true
    var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, this.area(l), `landmark ${l.name}`)
    TtlChunks.whenReady(server, hold, this.LOAD_POLL, this.LOAD_TIMEOUT, (ready, missing) => {
      try {
        if (!ready && missing > 0) {
          server.persistentData.putInt(self.key(l, 'fails'), server.persistentData.getInt(self.key(l, 'fails')) + 1)
          console.error(`[ttl] landmark ${l.name}: ${missing} chunk(s) still not loaded after ${self.LOAD_TIMEOUT} ticks; not placed`)
        } else self.place(server, l)
      } catch (e) {
        console.error(`[ttl] landmark ${l.name} placement failed: ${e}`)
      }
      TtlChunks.release(server, hold)
      self.busy = false
      server.scheduleInTicks(20, () => self.pump(server))
    })
  },

  enqueue(server, l) {
    if (this.queue.some(q => q.name === l.name)) return
    this.queue.push(l)
    this.pump(server)
  },

  pending(server) {
    var data = server.persistentData
    var self = this
    return this.all().filter(l => data.getInt(self.key(l, 'version')) !== l.version &&
      data.getInt(self.key(l, 'fails')) < self.BOOT_ATTEMPTS)
  },

  schedule(server) {
    var self = this
    this.run(server, `scoreboard objectives add ${this.OBJECTIVE} dummy`)
    server.scheduleInTicks(this.START_DELAY, () => self.pending(server).forEach(l => self.enqueue(server, l)))
  },

  // World reset of the overworld: every landmark goes again on the new terrain.
  reset(server) {
    var data = server.persistentData
    var self = this
    this.all().forEach(l => ['version', 'at', 'box', 'fails'].forEach(k => data.remove(self.key(l, k))))
    this.schedule(server)
  },

  describe(server, l) {
    var data = server.persistentData
    var v = data.getInt(this.key(l, 'version'))
    var at = String(data.getString(this.key(l, 'at')) || '')
    var state = v === l.version ? `placed at ${at}` : v ? `placed v${v} at ${at}, v${l.version} pending` :
      data.getInt(this.key(l, 'fails')) ? `FAILED ${data.getInt(this.key(l, 'fails'))}x` : 'pending'
    if (this.queue.some(q => q.name === l.name)) state += ' (queued)'
    return `${l.name}: ${l.structure} near ${l.x} ${l.z}, ${state}`
  }
}

ServerEvents.loaded(event => TtlLandmarks.schedule(event.server))

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var named = (ctx, then) => {
    var name = String(Arguments.STRING.getResult(ctx, 'name')).toLowerCase()
    var server = ctx.source.getServer()
    if (name === 'all' && then.all) return then.all(server)
    var l = TtlLandmarks.find(name)
    if (!l) {
      say(ctx, `No landmark ${name}; see /ttl landmark list`)
      return 0
    }
    return then.one(server, l)
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('landmark')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('list').executes(ctx => {
        var server = ctx.source.getServer()
        TtlLandmarks.all().forEach(l => say(ctx, TtlLandmarks.describe(server, l)))
        return 1
      }))
      .then(Commands.literal('place')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, l) => {
            server.persistentData.remove(TtlLandmarks.key(l, 'version'))
            server.persistentData.putInt(TtlLandmarks.key(l, 'fails'), 0)
            TtlLandmarks.enqueue(server, l)
            say(ctx, `Placing ${l.name} near ${l.x} ${l.z}; watch the log for "[ttl] landmark ${l.name}"`)
            return 1
          },
          all: server => {
            TtlLandmarks.all().forEach(l => {
              server.persistentData.remove(TtlLandmarks.key(l, 'version'))
              server.persistentData.putInt(TtlLandmarks.key(l, 'fails'), 0)
              TtlLandmarks.enqueue(server, l)
            })
            say(ctx, `Placing all ${TtlLandmarks.all().length} landmarks one by one`)
            return 1
          }
        }))))
      .then(Commands.literal('where')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, l) => {
            var data = server.persistentData
            var at = String(data.getString(TtlLandmarks.key(l, 'at')) || '')
            var box = String(data.getString(TtlLandmarks.key(l, 'box')) || '')
            say(ctx, `${l.title}: ${at ? `placed at ${at}` : `not placed, planned near ${l.x} ~ ${l.z}`}`)
            if (box) say(ctx, `  box ${box}`)
            say(ctx, `  /execute in ${TtlLife.OVERWORLD} run tp @s ${at ? at.split(' ').map((v, i) => i === 1 ? Number(v) + 2 : v).join(' ') : `${l.x} 200 ${l.z}`}`)
            return 1
          }
        }))))))
})
