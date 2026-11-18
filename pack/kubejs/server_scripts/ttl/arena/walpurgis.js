// The Walpurgis Hall (owner 18/11/2026): the Demon Lords' council chamber and the Banquet Floor arena in their own
// dimension ttl:walpurgis (build walpurgis_hall). Same pattern as life/spirit_domain.js: a doorway in the overworld (the dais
// of Clayman's throne, a box of blueprint cells of the placed clayman_castle) sends a soul to the hall's arrival point
// (ttl.build.walpurgis_hall.at) and the hall's return arch (TtlWalpurgisHall.portal) sends it back where it came from.
// Unlike the Dwelling, the hall is by invitation or condition (design/data/arenas.toml [walpurgis]): Life 2 AND one of a
// Legendary unique, a story capstone stage, an invitation, or a booked walpurgis arena match. A refused soul hears why (once
// per notice_seconds); a 4 second cooldown stops bouncing between the gates. Joining a walpurgis match (/ttl arena join)
// takes the fighter straight to the Banquet Floor and back (arena/arenas.js).
// Player persistentData: `ttl.walpurgis.back` ("dim x y z yaw pitch": where the soul entered from), `ttl.walpurgis.invite`
// (millis: invited until), `ttl.walpurgis.by` (who invited).
// Commands: /ttl walpurgis [status] · go (command_entry) · invite <player> (ops; Legendary holders when invite_by_legendary)
// Ops: /ttl walpurgis where | tp <player> | walk <player> gate|back | uninvite <player> | expect <player> in|out
//      | expect <player> allowed <yes|no>
const TtlWalpurgis = {
  POLL: 10,
  cool: {},
  noticed: {},

  conf() {
    return (TtlData.arenas && TtlData.arenas.walpurgis) || {}
  },

  num(v, fallback) {
    var n = Number(v)
    return v === undefined || v === null || isNaN(n) ? fallback : n
  },

  dim() {
    return String(this.conf().dim || 'ttl:walpurgis')
  },

  // The anchor of a placed build as [x, y, z], or null.
  at(server, name) {
    if (server.persistentData.getInt(`ttl.build.${name}.version`) < 1) return null
    var p = String(server.persistentData.getString(`ttl.build.${name}.at`) || '').split(' ').map(Number)
    return p.length === 3 && p.every(v => !isNaN(v)) ? p : null
  },

  corner(server, name) {
    if (server.persistentData.getInt(`ttl.build.${name}.version`) < 1) return null
    var p = String(server.persistentData.getString(`ttl.build.${name}.corner`) || '').split(' ').map(Number)
    return p.length === 3 && p.every(v => !isNaN(v)) ? p : null
  },

  buildDim(name) {
    var dim = TtlLife.OVERWORLD
    ;(TtlData.builds || []).forEach(b => { if (b.name === name && b.dimension) dim = String(b.dimension) })
    return dim
  },

  hallAt(server) {
    return this.at(server, String(this.conf().hall || 'walpurgis_hall'))
  },

  // The gate box in the world {dim, b: [x0, y0, z0, x1, y1, z1]} (feet cells, x1/z1 exclusive), or null.
  gate(server) {
    var g = this.conf().gate
    if (!g) return null
    var c = this.corner(server, String(g.build))
    if (!c) return null
    return {
      dim: this.buildDim(String(g.build)),
      b: [c[0] + g.from[0], c[1] + g.from[1], c[2] + g.from[2], c[0] + g.to[0] + 1, c[1] + g.to[1] + 1, c[2] + g.to[2] + 1]
    }
  },

  // The hall's return arch, absolute (same convention as life/spirit_domain.js).
  arch(server) {
    var at = this.hallAt(server)
    if (!at) return null
    var rel = TtlWalpurgisHall.portal
    return [at[0] + rel[0], at[1] + rel[1], at[2] + rel[2], at[0] + rel[3] + 1, at[1] + rel[4] + 1.5, at[2] + rel[5] + 1]
  },

  inside(player, b) {
    return player.x >= b[0] && player.x < b[3] && player.y >= b[1] - 0.6 && player.y < b[4] && player.z >= b[2] && player.z < b[5]
  },

  // ---- who may enter ------------------------------------------------------------------------------------------

  invitedUntil(player) {
    return this.num(String(player.persistentData.getString('ttl.walpurgis.invite') || '0'), 0)
  },

  booked(server, player) {
    try {
      var m = TtlArenas.matchOf(server, TtlArenas.uid(player))
      return !!(m && m.id === 'walpurgis')
    } catch (e) {
      return false
    }
  },

  legendary(server, player) {
    try {
      return TtlRegistry.legendaryHolders(server).indexOf(TtlRegistry.uid(player)) >= 0
    } catch (e) {
      console.warn(`[ttl] walpurgis: Legendary check failed for ${player.username}: ${e}`)
      return false
    }
  },

  // Why a soul may not enter ('' = it may).
  refusal(server, player) {
    var c = this.conf()
    if (c.life2_only !== false && TtlLife.phase(player) !== 'life2') return 'The Walpurgis does not open to a soul that has not been reborn.'
    if (c.allow_legendary && this.legendary(server, player)) return ''
    if ((c.allow_stages || []).some(s => player.stages.has(String(s)))) return ''
    if (c.allow_invited && this.invitedUntil(player) > Date.now()) return ''
    if (c.allow_booked && this.booked(server, player)) return ''
    return 'Only the Demon Lords sit at the Walpurgis, and those they invite. Hold a Legendary place, earn an invitation, or book a match on the Banquet Floor (/ttl arena join walpurgis).'
  },

  ready(server) {
    return this.hallAt(server) !== null
  },

  // ---- moving people ------------------------------------------------------------------------------------------

  // Sends a qualified soul to the hall's arrival point. Returns true when it went.
  enter(server, player, quiet) {
    var why = this.refusal(server, player)
    if (why) {
      this.refuse(server, player, why)
      return false
    }
    if (!this.ready(server)) {
      this.refuse(server, player, 'The way to the Walpurgis is still closed: the hall is not ready.')
      return false
    }
    var to = this.hallAt(server)
    var name = player.username
    if (TtlLife.dimensionOf(player) !== this.dim()) {
      var line = [TtlLife.dimensionOf(player), Number(player.getX()).toFixed(2), Number(player.getY()).toFixed(2), Number(player.getZ()).toFixed(2), Number(player.getYRot()).toFixed(1), Number(player.getXRot()).toFixed(1)].join(' ')
      player.persistentData.putString('ttl.walpurgis.back', line)
    }
    server.runCommandSilent(`execute in ${this.dim()} run tp ${name} ${to[0] + 0.5} ${to[1]} ${to[2] + 0.5} ${TtlWalpurgisHall.arrival_yaw} 0`)
    server.runCommandSilent(`execute in ${this.dim()} run playsound minecraft:block.respawn_anchor.set_spawn player ${name} ${to[0]} ${to[1]} ${to[2]} 0.6 0.7`)
    if (!quiet) TtlCorridor.voice(server, name, 'The Walpurgis opens. Ten seats wait round the table; the Banquet Floor lies to the east.')
    this.cool[TtlLife.uuid(player)] = Date.now()
    console.info(`[ttl] walpurgis: ${name} entered the hall at ${to.join(' ')}`)
    return true
  },

  // Back where the soul came from; else the configured return spot (before Clayman's throne); else the Tensura arrival.
  leave(server, player) {
    var name = player.username
    var raw = String(player.persistentData.getString('ttl.walpurgis.back') || '')
    player.persistentData.remove('ttl.walpurgis.back')
    var where = ''
    if (raw) {
      var b = raw.split(' ')
      server.runCommandSilent(`execute in ${b[0]} run tp ${name} ${b[1]} ${b[2]} ${b[3]} ${b[4] || 0} ${b[5] || 0}`)
      where = raw
    } else {
      var r = this.conf().return
      var c = r ? this.corner(server, String(r.build)) : null
      if (c) {
        var x = c[0] + r.at[0] + 0.5
        var y = c[1] + r.at[1]
        var z = c[2] + r.at[2] + 0.5
        server.runCommandSilent(`execute in ${this.buildDim(String(r.build))} run tp ${name} ${x} ${y} ${z}`)
        where = `${r.build} ${x} ${y} ${z}`
      } else {
        TtlLife.toOverworld(server, player)
        where = 'the Tensura arrival'
      }
    }
    this.cool[TtlLife.uuid(player)] = Date.now()
    console.info(`[ttl] walpurgis: ${name} left the hall for ${where}`)
  },

  refuse(server, player, text) {
    var id = TtlLife.uuid(player)
    var now = Date.now()
    if (this.noticed[id] && now - this.noticed[id] < this.num(this.conf().notice_seconds, 20) * 1000) return
    this.noticed[id] = now
    TtlCorridor.voice(server, player.username, text)
    console.info(`[ttl] walpurgis: refused ${player.username} (${TtlLife.phase(player)})`)
  },

  check(server, player) {
    if (player.isSpectator() || !player.isAlive()) return
    var id = TtlLife.uuid(player)
    if (this.cool[id] && Date.now() - this.cool[id] < this.num(this.conf().cooldown_seconds, 4) * 1000) return
    var dim = TtlLife.dimensionOf(player)
    if (dim === this.dim()) {
      var a = this.arch(server)
      if (a && this.inside(player, a)) this.leave(server, player)
      return
    }
    var g = this.gate(server)
    if (g && dim === g.dim && this.inside(player, g.b)) this.enter(server, player, false)
  },

  // An invitation: ops always; a Legendary holder when invite_by_legendary. Returns an error text or null.
  invite(server, by, target, hours) {
    var c = this.conf()
    if (!c.allow_invited) return 'Invitations to the Walpurgis are switched off.'
    var op = !by || by.hasPermissions(2)
    if (!op && !(c.invite_by_legendary && this.legendary(server, by))) return 'Only a Demon Lord (a Legendary holder) may invite a soul to the Walpurgis.'
    var h = hours > 0 ? hours : this.num(c.invite_hours, 24)
    target.persistentData.putString('ttl.walpurgis.invite', String(Date.now() + h * 3600000))
    target.persistentData.putString('ttl.walpurgis.by', by ? String(by.username) : 'the council')
    TtlCorridor.voice(server, target.username, `${by ? by.username : 'The council'} invites you to the Walpurgis for ${h} hours. The way is the dais of Clayman's throne.`)
    console.info(`[ttl] walpurgis: ${target.username} invited by ${by ? by.username : 'an op'} for ${h} h`)
    return null
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(TtlWalpurgis.POLL, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlWalpurgis.check(server, p)
      } catch (e) {
        console.error(`[ttl] walpurgis check failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] walpurgis command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var W = TtlWalpurgis

  var status = logged(ctx => {
    var s = ctx.source.getServer()
    var me = ctx.source.getPlayerOrException()
    var why = W.refusal(s, me)
    me.tell(why ? Text.gray(why) : Text.gold(`You may enter the Walpurgis${W.conf().command_entry ? ' (/ttl walpurgis go)' : ' through the dais of Clayman\'s throne'}.`))
    var until = W.invitedUntil(me)
    if (until > Date.now()) me.tell(Text.gold(`Invited by ${me.persistentData.getString('ttl.walpurgis.by')} for another ${Math.ceil((until - Date.now()) / 3600000)} h.`))
    return 1
  })
  var go = logged(ctx => {
    var me = ctx.source.getPlayerOrException()
    if (!W.conf().command_entry && !me.hasPermissions(2)) {
      me.tell(Text.red('The way to the Walpurgis is the dais of Clayman\'s throne.'))
      return 0
    }
    return W.enter(ctx.source.getServer(), me, false) ? 1 : 0
  })
  var invite = withHours => logged(ctx => {
    var s = ctx.source.getServer()
    var by = ctx.source.getPlayer()
    if (by && ctx.source.hasPermission(2) && !by.hasPermissions(2)) by = null   // `execute as` from the console counts as an op
    var err = W.invite(s, by, target(ctx), withHours ? Number(Arguments.INTEGER.getResult(ctx, 'hours')) : 0)
    if (err) throw err
    say(ctx, `walpurgis: ${target(ctx).username} invited`)
    return 1
  })
  var uninvite = logged(ctx => {
    var p = target(ctx)
    p.persistentData.remove('ttl.walpurgis.invite')
    p.persistentData.remove('ttl.walpurgis.by')
    say(ctx, `walpurgis: ${p.username}'s invitation withdrawn`)
    return 1
  })
  var where = logged(ctx => {
    var s = ctx.source.getServer()
    var hall = W.hallAt(s)
    var g = W.gate(s)
    say(ctx, `Walpurgis Hall (${W.dim()}): ${hall ? hall.join(' ') : 'not placed'}`)
    say(ctx, `Gate (${g ? g.dim : 'clayman_castle'}): ${g ? g.b.join(' ') : 'not placed'}`)
    return 1
  })
  var tp = logged(ctx => {
    var s = ctx.source.getServer()
    var p = target(ctx)
    if (!W.enter(s, p, false)) throw `${p.username} was not let into the hall (${W.refusal(s, p) || 'the hall is not placed'})`
    say(ctx, `${p.username} sent to the Walpurgis Hall`)
    return 1
  })
  // Puts the player in the gate ("gate") or the return arch ("back") to exercise the real trigger.
  var walk = which => logged(ctx => {
    var s = ctx.source.getServer()
    var p = target(ctx)
    if (which === 'gate') {
      var g = W.gate(s)
      if (!g) throw 'the gate build (clayman_castle) is not placed yet'
      s.runCommandSilent(`execute in ${g.dim} run tp ${p.username} ${(g.b[0] + g.b[3]) / 2} ${g.b[1]} ${(g.b[2] + g.b[5]) / 2}`)
    } else {
      var a = W.arch(s)
      if (!a) throw 'the Walpurgis Hall is not placed yet'
      s.runCommandSilent(`execute in ${W.dim()} run tp ${p.username} ${(a[0] + a[3]) / 2} ${a[1]} ${(a[2] + a[5]) / 2}`)
    }
    say(ctx, `${p.username} put in the ${which} doorway`)
    return 1
  })
  var expectIn = want => logged(ctx => {
    var p = target(ctx)
    var inside = TtlLife.dimensionOf(p) === W.dim()
    if (inside !== want) throw `expected ${p.username} to be ${want ? 'in' : 'out of'} ${W.dim()}, they are in ${TtlLife.dimensionOf(p)}`
    say(ctx, `walpurgis: ${p.username} is ${want ? 'in' : 'out of'} the hall as expected`)
    return 1
  })
  var expectAllowed = logged(ctx => {
    var p = target(ctx)
    var got = W.refusal(ctx.source.getServer(), p) ? 'no' : 'yes'
    var want = String(Arguments.STRING.getResult(ctx, 'value')).toLowerCase()
    if (got !== want) throw `expected ${p.username} allowed into the Walpurgis ${want}, got ${got}`
    say(ctx, `walpurgis: ${p.username} allowed ${want} as expected`)
    return 1
  })

  event.register(Commands.literal('ttl')
    .then(Commands.literal('walpurgis')
      .executes(status)
      .then(Commands.literal('status').executes(status))
      .then(Commands.literal('go').executes(go))
      .then(Commands.literal('invite')
        .then(playerArg().executes(invite(false))
          .then(Commands.argument('hours', Arguments.INTEGER.create(event)).executes(invite(true)))))
      .then(Commands.literal('uninvite').requires(op).then(playerArg().executes(uninvite)))
      .then(Commands.literal('where').requires(op).executes(where))
      .then(Commands.literal('tp').requires(op).then(playerArg().executes(tp)))
      .then(Commands.literal('walk').requires(op)
        .then(playerArg()
          .then(Commands.literal('gate').executes(walk('gate')))
          .then(Commands.literal('back').executes(walk('back')))))
      .then(Commands.literal('expect').requires(op)
        .then(playerArg()
          .then(Commands.literal('in').executes(expectIn(true)))
          .then(Commands.literal('out').executes(expectIn(false)))
          .then(Commands.literal('allowed').then(Commands.argument('value', Arguments.STRING.create(event)).executes(expectAllowed)))))))
})
