// One-time world works on Lerfing's map: the planted forests (life/forests.js) and the trade roads
// (life/trade_roads.js), both from generated/placements.js (TtlPlacementData, tools/gen_placements.py). This file is
// their shared runner: one job at a time, after Tempest, Dwargon, the landmarks and the canon builds have placed (the
// works read their recorded boxes and keep clear of them), each job split into pieces whose chunks are held with
// tickets (life/chunk_hold.js: loaded in the background, never a synchronous `forceload`), worked under a time budget
// per tick (BUDGET_MS), its progress recorded per piece so a restart resumes where it stopped and a finished job never
// runs twice (persistentData ttl.forest.<id>.* / ttl.troad.<id>.*: version, piece, counts).
// Op commands: /ttl works list | run <forest|road> <id> [force] | expect forest <id> planted|standing <min giants> |
// expect road <id> laid | expect road <id> surface <arc> | where road <id> <arc> | probe <x> <z>.
const TtlWorks = {
  START_DELAY: 2400, // after the canon builds (1800 + their queue)
  RETRY: 200,
  MAX_WAITS: 90, // 90 x RETRY = 15 min waiting on the builds and landmarks, then start anyway
  LOAD_POLL: 40,
  LOAD_TIMEOUT: 12000,
  BUDGET_MS: 25,
  GAP: 20, // ticks between two pieces
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest', 'lily_pad',
    'flower', 'tulip', 'orchid', 'allium', 'bluet', 'daisy', 'poppy', 'dandelion', 'cornflower', 'lilac', 'peony',
    'rose_bush', 'sunflower', 'sugar_cane', 'sweet_berry', 'mushroom', 'sapling', 'torch', 'lantern', 'fence',
    'hipokute', 'baffledil'],
  WET: ['minecraft:water', 'minecraft:seagrass', 'minecraft:tall_seagrass', 'minecraft:kelp', 'minecraft:kelp_plant',
    'minecraft:bubble_column', 'minecraft:ice', 'minecraft:frosted_ice'],
  SOIL: ['minecraft:grass_block', 'minecraft:dirt', 'minecraft:podzol', 'minecraft:coarse_dirt', 'minecraft:moss_block',
    'minecraft:rooted_dirt', 'minecraft:mycelium', 'minecraft:mud'],
  // 'forest' / 'road' -> handler { all(), key(id, k), forget(server, id), work(server, id, force, done), describe(server, id) }
  kinds() {
    var out = {}
    // roads first: a road is a minute's work, the forests take a few
    if (typeof TtlTradeRoads !== 'undefined') out.road = TtlTradeRoads
    if (typeof TtlForests !== 'undefined') out.forest = TtlForests
    return out
  },
  queue: [],
  busy: false,
  waits: 0,

  data() {
    return typeof TtlPlacementData === 'undefined' ? { forests: {}, roads: {}, keepouts: [] } : TtlPlacementData
  },

  // The command's result (1 placed, 0 failed): `server.runCommandSilent` returns nothing in KubeJS 2101, so a check
  // on it counted every planted tree as failed (staging 19/11/2026: "0 giants ... place failed 44, no room 1267" over a
  // forest that stood). TtlCmd (life/state.js) runs it through the dispatcher.
  run(server, cmd) {
    return this.attempt(server, cmd).result
  },

  attempt(server, cmd) {
    return TtlCmd.attempt(server, `execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  ints(text) {
    return text ? String(text).split(' ').map(Number) : null
  },

  // Progress (piece, counts, skips) belongs to one version (key pversion): a bumped version starts again at piece 0,
  // a run cut short by a restart resumes where it stopped.
  begin(server, h, id, version) {
    var data = server.persistentData
    if (data.getInt(h.key(id, 'pversion')) === version) return
    ;['piece', 'counts', 'skips'].forEach(k => data.remove(h.key(id, k)))
    data.putInt(h.key(id, 'pversion'), version)
  },

  // Heightmaps through Java (as life/builds.js): ground = first free y above the terrain (trees and plants skipped;
  // on water the water surface), floor = the same under the water, top = first free y above everything, soil = the
  // ground block is dirt-like, wet = water or ice on top. null when Java is unavailable.
  heightmaps(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var skip = this.NOT_GROUND
      var wet = this.WET
      var soil = this.SOIL
      var minY = level.getMinBuildHeight()
      var block = (x, y, z) => String(level.getBlock(x, y, z).id)
      var ground = (x, z) => {
        var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
        if (y <= minY) return null
        for (var n = 0; n < 48 && y > minY + 1; n++) {
          var id = block(x, y - 1, z)
          if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
          y--
        }
        return y
      }
      var hm = {
        minY: minY,
        block: block,
        ground: ground,
        top: (x, z) => level.getHeight(Types.MOTION_BLOCKING, x, z),
        floor: (x, z) => {
          var y = ground(x, z)
          if (y === null) return null
          for (var n = 0; n < 64 && y > minY + 1 && wet.indexOf(block(x, y - 1, z)) >= 0; n++) y--
          return y
        },
        wet: (x, z) => {
          var y = ground(x, z)
          return y === null || wet.indexOf(block(x, y - 1, z)) >= 0
        },
        soil: (x, z) => {
          var y = ground(x, z)
          return y !== null && soil.indexOf(block(x, y - 1, z)) >= 0
        }
      }
      return hm
    } catch (e) {
      console.error(`[ttl] works: heightmaps unavailable (${e})`)
      return null
    }
  },

  // Everything the works keep clear of (inclusive x0 z0 x1 z1): Tempest's and Dwargon's worked areas, every placed
  // canon build (recorded box) and landmark (recorded structure box, else its reach round its spot), Lerfing's and
  // Paulzero's keepouts. `core`: Tempest and Dwargon without their terrain margins (a road runs up to their edges and
  // joins Dwargon's own road there).
  kept(server, core) {
    var out = []
    var self = this
    var add = (label, get) => {
      try {
        var r = get()
        if (r) out.push({ label: label, x0: r.x0, z0: r.z0, x1: r.x1, z1: r.z1 })
      } catch (e) {
        console.warn(`[ttl] works: ${label} box unavailable (${e})`)
      }
    }
    add('Tempest', () => {
      var b = TtlTempest.box()
      if (!core) return { x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 }
      var f = TtlTempestFootprint
      return { x0: b.x0, z0: b.z0, x1: b.x0 + f.size[0] - 1, z1: b.z0 + f.size[2] - 1 }
    })
    add('Dwargon', () => {
      var b = TtlDwargon.box()
      if (!core) return { x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 }
      var f = TtlDwargonFootprint
      return { x0: b.x0, z0: b.z0, x1: b.x0 + f.size[0] - 1, z1: b.z0 + f.size[2] - 1 }
    })
    try {
      TtlBuilds.all().forEach(b => {
        if (b.dimension !== TtlLife.OVERWORLD) return
        var box = self.ints(server.persistentData.getString(TtlBuilds.key(b, 'box')))
        if (box && box.length === 4) out.push({ label: `build ${b.name}`, x0: box[0], z0: box[1], x1: box[2], z1: box[3] })
      })
    } catch (e) {
      console.warn(`[ttl] works: build boxes unavailable (${e})`)
    }
    try {
      TtlLandmarks.all().forEach(l => {
        var box = self.ints(server.persistentData.getString(TtlLandmarks.key(l, 'box')))
        var at = self.ints(server.persistentData.getString(TtlLandmarks.key(l, 'at')))
        if (box && box.length === 6) out.push({ label: `landmark ${l.name}`, x0: box[0], z0: box[2], x1: box[3], z1: box[5] })
        else if (at && at.length === 3) out.push({ label: `landmark ${l.name}`, x0: at[0] - l.reach, z0: at[2] - l.reach, x1: at[0] + l.reach, z1: at[2] + l.reach })
      })
    } catch (e) {
      console.warn(`[ttl] works: landmark boxes unavailable (${e})`)
    }
    this.data().keepouts.forEach(k => out.push({ label: `keepout ${k[4]}`, x0: k[0], z0: k[1], x1: k[2], z1: k[3] }))
    return out
  },

  // The recorded box (x0 z0 x1 z1) of a placed build or landmark by name, or null.
  placedBox(server, kind, name) {
    try {
      if (kind === 'build') {
        var b = TtlBuilds.find(name)
        var box = b ? this.ints(server.persistentData.getString(TtlBuilds.key(b, 'box'))) : null
        return box && box.length === 4 ? box : null
      }
      var l = TtlLandmarks.find(name)
      var lb = l ? this.ints(server.persistentData.getString(TtlLandmarks.key(l, 'box'))) : null
      return lb && lb.length === 6 ? [lb[0], lb[2], lb[3], lb[5]] : null
    } catch (e) {
      return null
    }
  },

  inBox(list, x, z, pad) {
    var p = pad || 0
    for (var i = 0; i < list.length; i++) {
      var r = list[i]
      if (x >= r.x0 - p && x <= r.x1 + p && z >= r.z0 - p && z <= r.z1 + p) return r
    }
    return null
  },

  boxHits(list, b, pad) {
    var p = pad || 0
    for (var i = 0; i < list.length; i++) {
      var r = list[i]
      if (!(b.x1 < r.x0 - p || b.x0 > r.x1 + p || b.z1 < r.z0 - p || b.z0 > r.z1 + p)) return r
    }
    return null
  },

  // Runs fns (thunks) a few per tick under BUDGET_MS, then done().
  budgeted(server, fns, done) {
    var self = this
    var i = 0
    var step = () => {
      var t0 = Date.now()
      while (i < fns.length && Date.now() - t0 < self.BUDGET_MS) {
        try {
          fns[i]()
        } catch (e) {
          console.error(`[ttl] works: step ${i} failed: ${e}`)
        }
        i++
      }
      if (i < fns.length) server.scheduleInTicks(1, step)
      else done()
    }
    step()
  },

  // Holds the chunks of `area`, waits until they are FULL, runs work(hm, release) (which must call release()).
  withArea(server, area, label, work, failed) {
    var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, area, label)
    var self = this
    TtlChunks.whenReady(server, hold, this.LOAD_POLL, this.LOAD_TIMEOUT, (ready, missing) => {
      if (!ready && missing > 0) {
        TtlChunks.release(server, hold)
        failed(`${missing} chunk(s) not loaded after ${self.LOAD_TIMEOUT / 20} s`)
        return
      }
      var hm = self.heightmaps(server)
      if (!hm) {
        TtlChunks.release(server, hold)
        failed('heightmaps unavailable')
        return
      }
      work(hm, () => TtlChunks.release(server, hold))
    })
  },

  othersBusy() {
    try {
      if (typeof TtlLandmarks !== 'undefined' && (TtlLandmarks.busy || TtlLandmarks.queue.length > 0)) return true
      if (typeof TtlBuilds !== 'undefined' && (TtlBuilds.busy || TtlBuilds.queue.length > 0)) return true
    } catch (e) {
      return false
    }
    return false
  },

  enqueue(server, kind, id, force) {
    if (this.queue.some(q => q.kind === kind && q.id === id)) return
    this.queue.push({ kind: kind, id: id, force: !!force })
    this.pump(server)
  },

  pump(server) {
    if (this.busy || this.queue.length === 0) return
    var self = this
    if (this.othersBusy() && this.waits < this.MAX_WAITS) {
      this.waits++
      if (!this.retrying) {
        this.retrying = true
        server.scheduleInTicks(this.RETRY, () => {
          self.retrying = false
          self.pump(server)
        })
      }
      return
    }
    var job = this.queue.shift()
    var h = this.kinds()[job.kind]
    this.busy = true
    var finish = () => {
      self.busy = false
      server.scheduleInTicks(self.GAP, () => self.pump(server))
    }
    try {
      h.work(server, job.id, job.force, finish)
    } catch (e) {
      console.error(`[ttl] works: ${job.kind} ${job.id} failed: ${e}`)
      finish()
    }
  },

  pending(server) {
    var out = []
    var self = this
    Object.keys(this.kinds()).forEach(kind => {
      var h = self.kinds()[kind]
      Object.keys(h.all()).forEach(id => {
        if (server.persistentData.getInt(h.key(id, 'version')) !== h.all()[id].version) out.push({ kind: kind, id: id })
      })
    })
    return out
  },

  schedule(server) {
    var self = this
    server.scheduleInTicks(this.START_DELAY, () => self.pending(server).forEach(p => self.enqueue(server, p.kind, p.id, false)))
  },

  // World reset of the overworld (world_reset.js): every work goes again on the new terrain.
  reset(server, ids) {
    if (ids && ids.indexOf(TtlLife.OVERWORLD) < 0) return
    var self = this
    Object.keys(this.kinds()).forEach(kind => {
      var h = self.kinds()[kind]
      Object.keys(h.all()).forEach(id => h.forget(server, id))
    })
    this.waits = 0
    this.schedule(server)
  }
}

ServerEvents.loaded(event => TtlWorks.schedule(event.server))

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var fail = (ctx, line) => {
    ctx.source.sendSystemMessage(Text.red(`ttl: ${line}`))
    return 0
  }
  var handler = (ctx, then) => {
    var kind = String(Arguments.STRING.getResult(ctx, 'kind'))
    var id = String(Arguments.STRING.getResult(ctx, 'id'))
    var h = TtlWorks.kinds()[kind]
    if (!h) return fail(ctx, `no work kind ${kind} (forest, road)`)
    if (!h.all()[id]) return fail(ctx, `no ${kind} ${id}; see /ttl works list`)
    return then(ctx.source.getServer(), h, kind, id)
  }
  var runIt = (ctx, force) => handler(ctx, (server, h, kind, id) => {
    TtlWorks.enqueue(server, kind, id, force)
    say(ctx, `${kind} ${id} queued${force ? ' (force)' : ''}; progress in the log ([ttl] ${kind} ${id})`)
    return 1
  })
  event.register(Commands.literal('ttl')
    .then(Commands.literal('works')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('list').executes(ctx => {
        var server = ctx.source.getServer()
        Object.keys(TtlWorks.kinds()).forEach(kind => {
          var h = TtlWorks.kinds()[kind]
          Object.keys(h.all()).forEach(id => say(ctx, h.describe(server, id)))
        })
        if (TtlWorks.queue.length) say(ctx, `queued: ${TtlWorks.queue.map(q => `${q.kind} ${q.id}`).join(', ')}`)
        return 1
      }))
      .then(Commands.literal('run')
        .then(Commands.argument('kind', Arguments.STRING.create(event))
          .then(Commands.argument('id', Arguments.STRING.create(event))
            .executes(ctx => runIt(ctx, false))
            .then(Commands.literal('force').executes(ctx => runIt(ctx, true))))))
      .then(Commands.literal('expect')
        .then(Commands.literal('forest')
          .then(Commands.argument('id', Arguments.STRING.create(event))
            .then(Commands.literal('planted')
              .then(Commands.argument('min', Arguments.INTEGER.create(event)).executes(ctx => {
                var id = String(Arguments.STRING.getResult(ctx, 'id'))
                var min = Arguments.INTEGER.getResult(ctx, 'min')
                var p = TtlForests.all()[id]
                if (!p) return fail(ctx, `no forest ${id}`)
                var server = ctx.source.getServer()
                var v = server.persistentData.getInt(TtlForests.key(id, 'version'))
                var got = TtlForests.counts(server.persistentData.getString(TtlForests.key(id, 'counts')))
                if (v !== p.version) return fail(ctx, `expected forest ${id} planted at version ${p.version}, it is ${v || 'not planted'} (${TtlForests.describe(server, id)})`)
                if (got[0] + got[3] < min) return fail(ctx, `expected at least ${min} giant trees in forest ${id}, planted ${got[0]} (${got[3]} already standing)`)
                say(ctx, `forest ${id}: ${got[0] + got[3]} giants, ${got[1] + got[4]} understory trees standing as expected`)
                return 1
              })))
            // The trunks themselves on the live terrain (loads the giants' chunks): what stands, not what was counted.
            .then(Commands.literal('standing')
              .then(Commands.argument('min', Arguments.INTEGER.create(event)).executes(ctx => {
                var id = String(Arguments.STRING.getResult(ctx, 'id'))
                var min = Arguments.INTEGER.getResult(ctx, 'min')
                var p = TtlForests.all()[id]
                if (!p) return fail(ctx, `no forest ${id}`)
                var hm = TtlWorks.heightmaps(ctx.source.getServer())
                if (!hm) return fail(ctx, 'heightmaps unavailable')
                var level = ctx.source.getServer().getLevel(TtlLife.OVERWORLD)
                // Level.getHeight reads an unloaded chunk as empty; getChunk loads it (synchronously, for this check)
                var n = p.giants.filter(g => {
                  level.getChunk(g[1] >> 4, g[2] >> 4)
                  return TtlForests.standing(hm, g[1], g[2])
                }).length
                if (n < min) return fail(ctx, `expected at least ${min} giant trunks standing in forest ${id}, found ${n} of ${p.giants.length}`)
                say(ctx, `forest ${id}: ${n} of ${p.giants.length} giant trunks stand`)
                return 1
              })))))
        .then(Commands.literal('road')
          .then(Commands.argument('id', Arguments.STRING.create(event))
            .then(Commands.literal('laid').executes(ctx => {
              var id = String(Arguments.STRING.getResult(ctx, 'id'))
              var r = TtlTradeRoads.all()[id]
              if (!r) return fail(ctx, `no road ${id}`)
              var server = ctx.source.getServer()
              var v = server.persistentData.getInt(TtlTradeRoads.key(id, 'version'))
              if (v !== r.version) return fail(ctx, `expected road ${id} laid at version ${r.version}, it is ${v || 'not laid'} (${TtlTradeRoads.describe(server, id)})`)
              say(ctx, TtlTradeRoads.describe(server, id))
              return 1
            }))
            .then(Commands.literal('surface')
              .then(Commands.argument('arc', Arguments.INTEGER.create(event)).executes(ctx => {
                var id = String(Arguments.STRING.getResult(ctx, 'id'))
                var arc = Arguments.INTEGER.getResult(ctx, 'arc')
                var r = TtlTradeRoads.all()[id]
                if (!r) return fail(ctx, `no road ${id}`)
                var why = TtlTradeRoads.checkSurface(ctx.source.getServer(), id, arc)
                if (why) return fail(ctx, why)
                say(ctx, `road ${id}: the surface at arc ${arc} is laid`)
                return 1
              }))))))
      // What the works read at a column (loads its chunk): the ground, the block under and on it, soil, wet, a trunk.
      .then(Commands.literal('probe')
        .then(Commands.argument('x', Arguments.INTEGER.create(event))
          .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(ctx => {
            var x = Arguments.INTEGER.getResult(ctx, 'x')
            var z = Arguments.INTEGER.getResult(ctx, 'z')
            var server = ctx.source.getServer()
            server.getLevel(TtlLife.OVERWORLD).getChunk(x >> 4, z >> 4)
            var hm = TtlWorks.heightmaps(server)
            if (!hm) return fail(ctx, 'heightmaps unavailable')
            var y = hm.ground(x, z)
            if (y === null) return fail(ctx, `${x} ${z}: no ground`)
            say(ctx, `${x} ${z}: ground ${y} on ${hm.block(x, y - 1, z)}, at ${hm.block(x, y, z)}, top ${hm.top(x, z)}, ` +
              `soil ${hm.soil(x, z)}, wet ${hm.wet(x, z)}, trunk ${TtlForests.standing(hm, x, z)}`)
            return 1
          }))))
      .then(Commands.literal('where')
        .then(Commands.literal('road')
          .then(Commands.argument('id', Arguments.STRING.create(event))
            .then(Commands.argument('arc', Arguments.INTEGER.create(event)).executes(ctx => {
              var id = String(Arguments.STRING.getResult(ctx, 'id'))
              var r = TtlTradeRoads.all()[id]
              if (!r) return fail(ctx, `no road ${id}`)
              var p = TtlTradeRoads.centre(r, Arguments.INTEGER.getResult(ctx, 'arc'))
              say(ctx, `road ${id} arc ${p.i}: ${p.x} ${p.y} ${p.z} (/execute in ${TtlLife.OVERWORLD} run tp @s ${p.x} ${p.y + 2} ${p.z})`)
              return 1
            })))))))
})
