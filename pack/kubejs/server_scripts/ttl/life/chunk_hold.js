// Keeps the chunks of a block rectangle loaded for the placers (Tempest, Dwargon, landmarks, canon builds) WITHOUT
// loading them on the server thread. `forceload add` calls ServerLevel.setChunkForced, which loads (and on a fresh
// world generates) every newly forced chunk synchronously in the same tick: a 200-600 chunk area after a world reset
// made ticks of 10-20 s, and five of them in a row put the server 60 s behind schedule, which the watchdog kills
// (crash reports 18/11 01:24, 18/11 06:18, 19/11 03:09: server thread in ForceLoadCommand -> setChunkForced ->
// getChunkBlocking). A region ticket only asks the chunk system for the chunks; generation runs on the worker threads
// and the server keeps ticking. The placers poll ready() and work once every chunk is FULL.
//
// Ticket: TicketType.FORCED at level 32 (distance 1: full chunk, block ticking), which never equals the level-31
// ticket of an administrator's /forceload, so releasing ours never drops theirs. The tickets are not saved: a crash
// or restart drops them (no stale forced chunks). Fallback without Java: `forceload add` one chunk every SPACING ticks
// (each still a synchronous load, but one at a time), released with `forceload remove`.
//
// Level 32 ticks blocks but not entities: an item that drops or a gravel block that falls while the chunks are held
// never moves or despawns and is saved with the chunk (staging 19/11/2026: 152 falling blocks with Time 0, thousands of
// items round Jura). release() first sweeps what appeared in the held area during the hold (life/drops.js TtlDrops.sweep:
// items removed, falling blocks set down where they would land; never within 32 blocks of a player).
const TtlChunks = {
  LEVEL_DISTANCE: 1,
  SPACING: 4,

  java() {
    if (this.j !== undefined) return this.j
    try {
      this.j = {
        TicketType: Java.loadClass('net.minecraft.server.level.TicketType'),
        ChunkPos: Java.loadClass('net.minecraft.world.level.ChunkPos')
      }
    } catch (e) {
      console.warn(`[ttl] chunks: tickets unavailable (${e}); placers fall back to forceload one chunk at a time`)
      this.j = null
    }
    return this.j
  },

  // a = { x0, z0, x1, z1 } in blocks (inclusive). Returns the hold to pass to ready() and release().
  hold(server, dim, a, label) {
    var h = { dim: dim, cx0: a.x0 >> 4, cz0: a.z0 >> 4, cx1: a.x1 >> 4, cz1: a.z1 >> 4, label: label || '', mode: 'ticket', released: false,
      t0: server.getTickCount() }
    var n = (h.cx1 - h.cx0 + 1) * (h.cz1 - h.cz0 + 1)
    var j = this.java()
    if (j) {
      try {
        var src = server.getLevel(dim).getChunkSource()
        var d = this.LEVEL_DISTANCE
        this.each(h, (cx, cz) => {
          var p = new j.ChunkPos(cx, cz)
          src.addRegionTicket(j.TicketType.FORCED, p, d, p)
        })
        console.info(`[ttl] chunks: holding ${n} chunks for ${h.label} (tickets, loading in the background)`)
        return h
      } catch (e) {
        console.warn(`[ttl] chunks: ticket for ${h.label} failed (${e}); forceload one chunk at a time instead`)
        this.dropTickets(server, h)
      }
    }
    h.mode = 'forceload'
    var list = []
    this.each(h, (cx, cz) => list.push([cx, cz]))
    var i = 0
    var self = this
    var step = () => {
      if (h.released || i >= list.length) return
      var c = list[i++]
      server.runCommandSilent(`execute in ${dim} run forceload add ${c[0] * 16} ${c[1] * 16}`)
      server.scheduleInTicks(self.SPACING, step)
    }
    console.info(`[ttl] chunks: holding ${n} chunks for ${h.label} (forceload, one every ${this.SPACING} ticks)`)
    step()
    return h
  },

  each(h, fn) {
    for (var cx = h.cx0; cx <= h.cx1; cx++) {
      for (var cz = h.cz0; cz <= h.cz1; cz++) fn(cx, cz)
    }
  },

  // Chunks of the hold that are not FULL yet (0 = ready); -1 when that cannot be checked.
  missing(server, h) {
    try {
      var src = server.getLevel(h.dim).getChunkSource()
      var n = 0
      // getChunkNow, not hasChunk: hasChunk only compares the ticket level, so it is true one tick after the ticket
      // while the chunk is still generating; getChunkNow returns the chunk only once it is FULL and in memory.
      this.each(h, (cx, cz) => {
        if (src.getChunkNow(cx, cz) === null) n++
      })
      return n
    } catch (e) {
      return -1
    }
  },

  ready(server, h) {
    return this.missing(server, h) === 0
  },

  // Polls every `poll` ticks until the hold is ready or `timeout` ticks have passed, then calls done(ok, missing).
  // Never loads a chunk itself: on timeout the caller decides (the placers give up rather than load the rest
  // synchronously, which is the stall this file exists to avoid).
  whenReady(server, h, poll, timeout, done) {
    var waited = 0
    var self = this
    var check = () => {
      var miss = self.missing(server, h)
      if (miss === 0 || miss === -1) {
        done(miss === 0, miss)
        return
      }
      waited += poll
      if (waited >= timeout) {
        done(false, miss)
        return
      }
      server.scheduleInTicks(poll, check)
    }
    server.scheduleInTicks(poll, check)
  },

  dropTickets(server, h) {
    var j = this.java()
    if (!j) return
    var src = server.getLevel(h.dim).getChunkSource()
    var d = this.LEVEL_DISTANCE
    this.each(h, (cx, cz) => {
      var p = new j.ChunkPos(cx, cz)
      src.removeRegionTicket(j.TicketType.FORCED, p, d, p)
    })
  },

  // Items and falling blocks younger than the hold (+2 ticks) in its chunks; at most 6000 ticks (an item's lifetime).
  sweep(server, h) {
    if (typeof TtlDrops === 'undefined') return
    var age = Math.min(6000, server.getTickCount() - (h.t0 || 0) + 2)
    TtlDrops.sweep(server, h.dim, { x0: h.cx0 * 16, z0: h.cz0 * 16, x1: h.cx1 * 16 + 15, z1: h.cz1 * 16 + 15 }, age, h.label)
  },

  release(server, h) {
    if (!h || h.released) return
    h.released = true
    this.sweep(server, h)
    try {
      if (h.mode === 'ticket') this.dropTickets(server, h)
      else {
        for (var z = h.cz0 * 16; z <= h.cz1 * 16 + 15; z += 64) {
          server.runCommandSilent(`execute in ${h.dim} run forceload remove ${h.cx0 * 16} ${z} ${h.cx1 * 16 + 15} ${Math.min(z + 63, h.cz1 * 16 + 15)}`)
        }
      }
    } catch (e) {
      console.warn(`[ttl] chunks: releasing ${h.label} failed (${e}); the tickets go with the next restart`)
    }
  }
}

// Test hook (tests/ingame/chunk_hold.rcon): /ttl chunks hold <x0> <z0> <x1> <z1> holds an overworld rectangle,
// reports in the log when it is loaded (`[ttl] chunks: test hold ... ready after N ticks`) and releases it.
// /ttl chunks expect loaded <x> <z>: fails unless that chunk is FULL right now.
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var int = (ctx, n) => Arguments.INTEGER.getResult(ctx, n)
  event.register(Commands.literal('ttl')
    .then(Commands.literal('chunks')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('hold')
        .then(Commands.argument('x0', Arguments.INTEGER.create(event))
          .then(Commands.argument('z0', Arguments.INTEGER.create(event))
            .then(Commands.argument('x1', Arguments.INTEGER.create(event))
              .then(Commands.argument('z1', Arguments.INTEGER.create(event)).executes(ctx => {
                var server = ctx.source.getServer()
                var a = { x0: int(ctx, 'x0'), z0: int(ctx, 'z0'), x1: int(ctx, 'x1'), z1: int(ctx, 'z1') }
                var h = TtlChunks.hold(server, TtlLife.OVERWORLD, a, `test hold ${a.x0} ${a.z0} ${a.x1} ${a.z1}`)
                var t0 = server.getTickCount()
                ctx.source.sendSystemMessage(Text.of(`holding ${TtlChunks.missing(server, h)} unloaded chunk(s) of ${a.x0} ${a.z0} ${a.x1} ${a.z1}`))
                TtlChunks.whenReady(server, h, 10, 12000, (ok, miss) => {
                  console.info(`[ttl] chunks: ${h.label} ${ok ? 'ready' : `NOT ready (${miss} missing)`} after ${server.getTickCount() - t0} ticks`)
                  TtlChunks.release(server, h)
                })
                return 1
              }))))))
      .then(Commands.literal('expect')
        .then(Commands.literal('loaded')
          .then(Commands.argument('x', Arguments.INTEGER.create(event))
            .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(ctx => {
              var server = ctx.source.getServer()
              var x = int(ctx, 'x')
              var z = int(ctx, 'z')
              if (server.getLevel(TtlLife.OVERWORLD).getChunkSource().getChunkNow(x >> 4, z >> 4) === null) {
                ctx.source.sendSystemMessage(Text.red(`ttl: expected the chunk at ${x} ${z} to be loaded`))
                return 0
              }
              ctx.source.sendSystemMessage(Text.of(`chunks: ${x} ${z} is loaded as expected`))
              return 1
            })))))))
})
