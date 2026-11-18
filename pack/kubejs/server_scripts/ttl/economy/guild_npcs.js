// priority: 50
// The Free Guild's Easy NPCs: Fuze (the guild master, high-rank contracts) and the guild receptionists (the desk).
// Spots, settings and who is who come from design/data/npcs.toml (TtlData.npcs); the NPCs' look and dialogs are Easy NPC
// presets generated from the same file (tools/gen_npcs.py -> config/easy_npc/preset/ttl_guild_<kind>.npc.snbt). Their
// buttons run the player's own `/ttl guild board|take|turnin|status` (economy/commands.js), so every rule (Life 2 only,
// rank, giver) lives in guild.js and not in the dialog.
//
// Placement. Every active spot keeps exactly one NPC, found again by tags: `ttl.npc` (any guild NPC), the spot's own
// `tag` (`ttl.npc.fuze`, `ttl.npc.receptionist.<n>`) and `ttl.npc.spot.<id>`. A spot is checked on start (after
// start_delay_ticks) and every check_ticks, and only while its chunk is loaded, so nothing is spawned into a chunk that
// may already hold the NPC:
//   - none found           -> spawn one: `/easy_npc preset import_new custom easy_npc:preset/ttl_guild_<kind>.npc.snbt x y z`
//   - more than one found  -> the extras are deleted (`/easy_npc delete <uuid>`)
//   - the spot's signature (kind, position, yaw, settings.rev) differs from the one stored when it was spawned
//                          -> the old NPC is deleted and a fresh one spawned (this is how a moved spot or a bumped
//                             rev replaces an NPC that still has the old dialog)
//   - spot not active      -> its NPC is deleted (disabled, or a Tempest stand-in once its build is placed:
//                             `unless_build`; a spot anchored to a build (`anchor = "build"`) waits for
//                             `ttl.build.<name>.corner` from life/builds.js and stands at corner + blueprint offset)
// Server persistentData `ttl.npc.state` = {<spot id>: {sig}}.
//
// Staff: /ttl guild npc list | ensure [spot] | spawn <spot> | remove <spot> | goto <player> <spot> | expect <field> <value>
const TtlGuildNpc = {
  STATE: 'ttl.npc.state',
  ANY: 'ttl.npc',
  last: {},
  warned: {},

  conf() {
    return TtlData.npcs
  },

  spots() {
    return this.conf().spot
  },

  spot(id) {
    var all = this.spots()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  presetOf(spot) {
    return `easy_npc:preset/${this.conf().settings.preset_prefix}${spot.kind}.npc.snbt`
  },

  spotTag(spot) {
    return `${this.ANY}.spot.${spot.id}`
  },

  state(server) {
    var raw = String(server.persistentData.getString(this.STATE) || '')
    return raw ? JSON.parse(raw) : {}
  },

  saveState(server, st) {
    server.persistentData.putString(this.STATE, JSON.stringify(st))
  },

  // The world corner (blueprint 0,0,0) of a build placed by life/builds.js, or null while it is not placed. The key is
  // `ttl.build.<name>.corner` = "X Y Z", valid once `ttl.build.<name>.version` is set.
  corner(server, name) {
    var data = server.persistentData
    if (data.getInt(`ttl.build.${name}.version`) < 1) return null
    var raw = String(data.getString(`ttl.build.${name}.corner`) || '')
    if (!raw) return null
    var p = raw.split(' ').map(Number)
    return p.length === 3 && p.every(n => !isNaN(n)) ? p : null
  },

  // A stand-in spot (unless_build) is only active while that build is not placed.
  active(server, spot) {
    if (spot.enabled !== true) return false
    return !(spot.unless_build && this.corner(server, String(spot.unless_build)))
  },

  // {dim, x, y, z, yaw} with the NPC standing in the middle of its block, or null while an anchor is not ready
  // (Tempest or the build not placed yet).
  resolve(server, spot) {
    var x = Number(spot.x)
    var y = Number(spot.y)
    var z = Number(spot.z)
    if (String(spot.anchor) === 'build') {
      var c = this.corner(server, String(spot.build))
      if (!c) return null
      x += c[0] + 0.5
      y += c[1]
      z += c[2] + 0.5
    } else if (String(spot.anchor) === 'tempest') {
      var raw = String(server.persistentData.getString('ttl.tempest.arrival') || '')
      if (!raw) return null
      var p = raw.split(' ')
      x += Number(p[0])
      y += Number(p[1])
      z += Number(p[2])
    } else {
      x += 0.5
      z += 0.5
    }
    return { dim: String(spot.dim), x: x, y: y, z: z, yaw: Number(spot.yaw) }
  },

  signature(spot, pos) {
    return `${spot.kind}|${pos.dim} ${pos.x} ${pos.y} ${pos.z} ${pos.yaw}|rev ${this.conf().settings.rev}`
  },

  isLoaded(server, pos) {
    return server.runCommandSilent(`execute in ${pos.dim} if loaded ${pos.x} ${pos.y} ${pos.z}`) > 0
  },

  hasTag(e, tag) {
    return e.getTags().contains(tag)
  },

  // Living entities carrying `tag` in a dimension (only loaded chunks hold any).
  find(server, dim, tag) {
    var out = []
    var level = server.getLevel(dim)
    if (!level) return out
    var self = this
    level.getEntities().forEach(e => {
      if (e.isAlive() && self.hasTag(e, tag)) out.push(e)
    })
    return out
  },

  // Counts by tag across the guild's dimensions (the overworld, plus whatever the spots name).
  count(server, tag) {
    var dims = {}
    this.spots().forEach(s => { dims[String(s.dim)] = true })
    var n = 0
    var self = this
    Object.keys(dims).forEach(d => { n += self.find(server, d, tag).length })
    return n
  },

  uuidOf(e) {
    try {
      var id = String(e.uuid)
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) return id
    } catch (x) {
      // fall through
    }
    return ''
  },

  // Easy NPC keeps its own record of an NPC (storage, backups): `/easy_npc delete` forgets it for good, a bare discard
  // would leave a record that Easy NPC may restore.
  remove(server, e) {
    var id = this.uuidOf(e)
    if (id && server.runCommandSilent(`easy_npc delete ${id}`) > 0) return
    e.discard()
  },

  // Spawns one NPC at the spot and tags the new entity (the nearest Easy NPC without a guild tag). True on success.
  spawn(server, spot, pos) {
    var r = server.runCommandSilent(`execute in ${pos.dim} run easy_npc preset import_new custom ${this.presetOf(spot)} ${pos.x} ${pos.y} ${pos.z}`)
    if (!(r > 0)) {
      console.error(`[ttl] guild npc: importing ${this.presetOf(spot)} at ${pos.dim} ${pos.x} ${pos.y} ${pos.z} failed (result ${r}); is the preset in config/easy_npc/preset and does the log say why?`)
      return false
    }
    var best = null
    var bestD = 4
    var self = this
    server.getLevel(pos.dim).getEntities().forEach(e => {
      if (!String(e.type).startsWith('easy_npc:')) return
      var tags = e.getTags().toArray()
      for (var i = 0; i < tags.length; i++) {
        if (String(tags[i]).startsWith(self.ANY)) return
      }
      var dx = e.getX() - pos.x
      var dy = e.getY() - pos.y
      var dz = e.getZ() - pos.z
      var d = dx * dx + dy * dy + dz * dz
      if (d < bestD) {
        best = e
        bestD = d
      }
    })
    if (!best) {
      console.error(`[ttl] guild npc: ${spot.id} was imported but no untagged Easy NPC stands within 2 blocks of ${pos.x} ${pos.y} ${pos.z}`)
      return false
    }
    best.addTag(this.ANY)
    best.addTag(String(spot.tag))
    best.addTag(this.spotTag(spot))
    // Face the way the spot says; the head still follows players (LOOK_AT_PLAYER).
    server.runCommandSilent(`execute in ${pos.dim} as @e[tag=${this.spotTag(spot)},limit=1] run tp @s ${pos.x} ${pos.y} ${pos.z} ${pos.yaw} 0`)
    return true
  },

  // One spot. Returns 'spawned' | 'ok' | 'replaced' | 'inactive' | 'pending' | 'unloaded' | 'failed'.
  ensureSpot(server, spot) {
    var id = String(spot.id)
    var st = this.state(server)
    var found = this.find(server, String(spot.dim), this.spotTag(spot))
    var out
    if (!this.active(server, spot)) {
      if (found.length > 0) {
        var self0 = this
        found.forEach(e => self0.remove(server, e))
        console.info(`[ttl] guild npc: ${id} is ${spot.enabled === true ? 'replaced by its build' : 'disabled'}, ${found.length} removed`)
      }
      if (st[id]) {
        delete st[id]
        this.saveState(server, st)
      }
      this.last[id] = 'inactive'
      return 'inactive'
    }
    var pos = this.resolve(server, spot)
    if (!pos) {
      if (!this.warned[id]) {
        this.warned[id] = true
        console.info(`[ttl] guild npc: ${id} waits for its anchor (${spot.anchor}) to be placed`)
      }
      this.last[id] = 'pending'
      return 'pending'
    }
    if (!this.isLoaded(server, pos)) {
      this.last[id] = 'unloaded'
      return 'unloaded'
    }
    var sig = this.signature(spot, pos)
    var rec = st[id]
    var self = this
    if (found.length > 0 && (!rec || rec.sig === sig)) {
      found.slice(1).forEach(e => self.remove(server, e))
      if (found.length > 1) console.info(`[ttl] guild npc: ${id} had ${found.length} copies, ${found.length - 1} removed`)
      if (!rec) {
        st[id] = { sig: sig }
        this.saveState(server, st)
      }
      this.last[id] = 'ok'
      return 'ok'
    }
    out = 'spawned'
    if (found.length > 0) {
      found.forEach(e => self.remove(server, e))
      out = 'replaced'
    }
    if (!this.spawn(server, spot, pos)) {
      this.last[id] = 'failed'
      return 'failed'
    }
    st[id] = { sig: sig }
    this.saveState(server, st)
    console.info(`[ttl] guild npc: ${id} (${spot.kind}) ${out} at ${pos.dim} ${pos.x} ${pos.y} ${pos.z}`)
    this.last[id] = out
    return out
  },

  ensureAll(server) {
    var self = this
    return this.spots().map(s => `${s.id}: ${self.ensureSpot(server, s)}`)
  },

  // ---- facts for `ttl guild npc expect` ----

  rankIndex(id) {
    return TtlGuild.rankIndexOf(id)
  },

  fact(server, field) {
    var self = this
    var m = /^count_(.+)$/.exec(field)
    if (m) {
      var spot = this.spot(m[1])
      if (spot) return String(this.count(server, this.spotTag(spot)))
      // a kind: the tags of its enabled spots (ttl.npc.fuze, ttl.npc.receptionist.1, ...)
      var tags = {}
      this.spots().forEach(s => { if (String(s.kind) === m[1] && s.enabled === true) tags[String(s.tag)] = true })
      var n = 0
      Object.keys(tags).forEach(t => { n += self.count(server, t) })
      return String(n)
    }
    var t = /^tags_(.+)$/.exec(field)
    if (t) {
      var sp = this.spot(t[1])
      if (!sp) throw `unknown spot ${t[1]}`
      var found = this.find(server, String(sp.dim), this.spotTag(sp))
      if (found.length === 0) return 'none'
      return [this.ANY, String(sp.tag), this.spotTag(sp)].every(x => self.hasTag(found[0], x)) ? 'ok' : 'missing'
    }
    var st = /^state_(.+)$/.exec(field)
    if (st) return String(this.last[st[1]] || 'unchecked')
    var min = this.rankIndex(TtlGuild.conf().guild.fuze_min_rank)
    var all = {
      spots: () => String(self.spots().filter(s => self.active(server, s)).length),
      // Fuze's board holds only contracts of his ranks and above, the desk's only ranks below.
      fuze_board_high: () => String(TtlGuild.entries(server, 'fuze').every(e => self.rankIndex(e.b.min_rank) >= min)),
      desk_board_low: () => String(TtlGuild.entries(server, 'desk').every(e => self.rankIndex(e.b.min_rank) < min)),
      fuze_board_size: () => String(TtlGuild.entries(server, 'fuze').length),
      desk_board_size: () => String(TtlGuild.entries(server, 'desk').length),
      // The preset files the NPCs are spawned from.
      presets: () => {
        try {
          var File = Java.loadClass('java.io.File')
          var prefix = String(self.conf().settings.preset_prefix)
          return String(TtlData.npcs.kind.every(k => new File(`config/easy_npc/preset/${prefix}${k.id}.npc.snbt`).exists()))
        } catch (e) {
          return 'n/a'
        }
      }
    }
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')}, count_<spot|kind>, tags_<spot>, state_<spot>)`
    return all[field]()
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(100, Number(TtlGuildNpc.conf().settings.check_ticks))
  var check = () => {
    try {
      TtlGuildNpc.ensureAll(server)
    } catch (e) {
      console.error(`[ttl] guild npc check failed: ${e}`)
    }
    server.scheduleInTicks(every, check)
  }
  server.scheduleInTicks(Math.max(20, Number(TtlGuildNpc.conf().settings.start_delay_ticks)), check)
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] guild npc command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var server = ctx => ctx.source.getServer()
  var spotOf = ctx => {
    var s = TtlGuildNpc.spot(str(ctx, 'spot'))
    if (!s) throw `unknown spot ${str(ctx, 'spot')} (${TtlGuildNpc.spots().map(x => x.id).join(', ')})`
    return s
  }
  var ops = src => src.hasPermission(2)

  var list = ctx => {
    var s = server(ctx)
    TtlGuildNpc.spots().forEach(sp => {
      var pos = TtlGuildNpc.resolve(s, sp)
      var where = pos ? `${pos.dim} ${pos.x} ${pos.y} ${pos.z}` : `waiting for anchor ${sp.anchor}`
      say(ctx, `${sp.id} (${sp.kind}, ${sp.tag}): ${TtlGuildNpc.active(s, sp) ? 'active' : 'inactive'}, ${where}, ` +
        `${TtlGuildNpc.count(s, TtlGuildNpc.spotTag(sp))} in the world, last check ${TtlGuildNpc.last[sp.id] || 'unchecked'}`)
    })
    return 1
  }

  var ensure = one => ctx => {
    var s = server(ctx)
    var lines = one ? [`${str(ctx, 'spot')}: ${TtlGuildNpc.ensureSpot(s, spotOf(ctx))}`] : TtlGuildNpc.ensureAll(s)
    lines.forEach(l => say(ctx, `guild npc ${l}`))
    return 1
  }

  // Test hook: one more copy of the spot's NPC, whatever is there (`ensure` then removes the extra one).
  var spawn = ctx => {
    var sp = spotOf(ctx)
    var pos = TtlGuildNpc.resolve(server(ctx), sp)
    if (!pos) throw `${sp.id}: its anchor ${sp.anchor} is not placed yet`
    if (!TtlGuildNpc.spawn(server(ctx), sp, pos)) throw `${sp.id}: spawning failed (see the log)`
    say(ctx, `guild npc ${sp.id}: extra copy spawned`)
    return 1
  }

  var remove = ctx => {
    var s = server(ctx)
    var sp = spotOf(ctx)
    var found = TtlGuildNpc.find(s, String(sp.dim), TtlGuildNpc.spotTag(sp))
    found.forEach(e => TtlGuildNpc.remove(s, e))
    var st = TtlGuildNpc.state(s)
    delete st[sp.id]
    TtlGuildNpc.saveState(s, st)
    say(ctx, `guild npc ${sp.id}: ${found.length} removed`)
    return 1
  }

  // Test hook: stands a player at the spot so its chunk is loaded.
  var gotoSpot = ctx => {
    var p = Arguments.PLAYER.getResult(ctx, 'target')
    var sp = spotOf(ctx)
    var pos = TtlGuildNpc.resolve(server(ctx), sp)
    if (!pos) throw `${sp.id}: its anchor ${sp.anchor} is not placed yet`
    server(ctx).runCommandSilent(`execute in ${pos.dim} run tp ${p.username} ${pos.x} ${pos.y} ${pos.z}`)
    say(ctx, `guild npc: ${p.username} at ${sp.id}`)
    return 1
  }

  var expect = ctx => {
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlGuildNpc.fact(server(ctx), field)
    if (got !== want) throw `expected guild npc ${field}=${want}, got ${got}`
    say(ctx, `guild npc ${field}=${want} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('guild')
      .then(Commands.literal('npc').requires(ops)
        .then(Commands.literal('list').executes(logged(list)))
        .then(Commands.literal('ensure').executes(logged(ensure(false)))
          .then(Commands.argument('spot', Arguments.STRING.create(event)).executes(logged(ensure(true)))))
        .then(Commands.literal('spawn').then(Commands.argument('spot', Arguments.STRING.create(event)).executes(logged(spawn))))
        .then(Commands.literal('remove').then(Commands.argument('spot', Arguments.STRING.create(event)).executes(logged(remove))))
        .then(Commands.literal('goto').then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('spot', Arguments.STRING.create(event)).executes(logged(gotoSpot)))))
        .then(Commands.literal('expect').then(Commands.argument('field', Arguments.STRING.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))))
})
