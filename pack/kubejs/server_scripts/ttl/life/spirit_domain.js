// The Dwelling of the Spirits (owner request 18/11/2026): a gate in the Great Jura Forest (build spirit_gate, overworld)
// leads into its own dimension ttl:spirit_domain (build spirit_dwelling: a floating glade with the summoning grotto),
// and a return gate there leads back. This is NOT the Spirit Corridor, which belongs to the Life 1 -> 2 flow.
//
// Entrance: stepping into the doorway (a box fixed relative to the gate's anchor: generated/spirit_gate.js
// TtlSpiritGate.portal, the anchor itself is where life/builds.js recorded the placement in persistentData
// ttl.build.spirit_gate.at) sends a Life 2 soul to the Dwelling's arrival point (ttl.build.spirit_dwelling.at, the
// anchor of the build); the return arch there (TtlSpiritDwelling.portal) sends it to the gate's anchor. A Life 1 or
// corridor soul in the doorway is refused with a Voice line (life/confine.js keeps them out of the overworld anyway,
// so this is a safety net for staff and test setups). Nobody is sent before the Dwelling is placed, so no one drops into the
// void. Checked twice a second for players near the gates only; a 4 second cooldown stops a soul bouncing between gates.
// Ops: /ttl spiritdomain where | tp <player> | walk <player> gate|back | expect <player> in|out
const TtlSpiritDomain = {
  DIM: 'ttl:spirit_domain',
  GATE: 'spirit_gate',
  DWELLING: 'spirit_dwelling',
  POLL: 10,
  COOLDOWN_MS: 4000,
  NOTICE_MS: 20000,
  cool: {},
  noticed: {},

  placed(server, name) {
    return server.persistentData.getInt(`ttl.build.${name}.version`) > 0
  },

  // The anchor of a placed build as [x, y, z], or null.
  at(server, name) {
    var text = String(server.persistentData.getString(`ttl.build.${name}.at`) || '')
    if (!text) return null
    var p = text.split(' ').map(Number)
    return p.length === 3 && p.every(v => !isNaN(v)) ? p : null
  },

  // An anchor-relative box [dx0, dy0, dz0, dx1, dy1, dz1] as an absolute box around the anchor.
  box(at, rel) {
    return [at[0] + rel[0], at[1] + rel[1], at[2] + rel[2], at[0] + rel[3] + 1, at[1] + rel[4] + 1.5, at[2] + rel[5] + 1]
  },

  inside(player, b) {
    return player.x >= b[0] && player.x < b[3] && player.y >= b[1] - 0.6 && player.y < b[4] && player.z >= b[2] && player.z < b[5]
  },

  ready(server) {
    return this.placed(server, this.DWELLING) && this.at(server, this.DWELLING) !== null
  },

  // Sends a Life 2 soul to the Dwelling's arrival point. Returns true when it went.
  enter(server, player, quiet) {
    var name = player.username
    if (TtlLife.phase(player) !== 'life2') {
      this.refuse(server, player, 'The gate does not answer a soul that is not yet reborn.')
      return false
    }
    if (!this.ready(server)) {
      this.refuse(server, player, 'The gate is still sealed. Come back when the spirits have prepared their home.')
      return false
    }
    var to = this.at(server, this.DWELLING)
    server.runCommandSilent(`execute in ${this.DIM} run tp ${name} ${to[0] + 0.5} ${to[1]} ${to[2] + 0.5} ${TtlSpiritDwelling.arrival_yaw} 0`)
    server.runCommandSilent(`execute in ${this.DIM} run playsound minecraft:block.beacon.activate player ${name} ${to[0]} ${to[1]} ${to[2]} 0.6 1.4`)
    if (!quiet) TtlCorridor.voice(server, name, 'You step through the gate. The spirits\' home opens around you.')
    this.cool[TtlLife.uuid(player)] = Date.now()
    console.info(`[ttl] spirit domain: ${name} entered the Dwelling at ${to.join(' ')}`)
    return true
  },

  // Sends a soul from the Dwelling back to the gate's anchor (or the Tensura arrival if the gate is not placed).
  leave(server, player) {
    var name = player.username
    var to = this.at(server, this.GATE)
    if (to) {
      server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run tp ${name} ${to[0] + 0.5} ${to[1]} ${to[2] + 0.5} ${TtlSpiritGate.arrival_yaw} 0`)
    } else {
      TtlLife.toOverworld(server, player)
    }
    this.cool[TtlLife.uuid(player)] = Date.now()
    console.info(`[ttl] spirit domain: ${name} left the Dwelling for ${to ? to.join(' ') : 'the Tensura arrival'}`)
  },

  refuse(server, player, text) {
    var id = TtlLife.uuid(player)
    var now = Date.now()
    if (this.noticed[id] && now - this.noticed[id] < this.NOTICE_MS) return
    this.noticed[id] = now
    TtlCorridor.voice(server, player.username, text)
    console.info(`[ttl] spirit domain: refused ${player.username} (${TtlLife.phase(player)})`)
  },

  check(server, player) {
    if (player.isSpectator()) return
    var id = TtlLife.uuid(player)
    if (this.cool[id] && Date.now() - this.cool[id] < this.COOLDOWN_MS) return
    var dim = TtlLife.dimensionOf(player)
    if (dim === TtlLife.OVERWORLD) {
      var gate = this.at(server, this.GATE)
      if (gate && this.inside(player, this.box(gate, TtlSpiritGate.portal))) this.enter(server, player, false)
    } else if (dim === this.DIM) {
      var home = this.at(server, this.DWELLING)
      if (home && this.inside(player, this.box(home, TtlSpiritDwelling.portal))) this.leave(server, player)
    }
  },

  // A soft shimmer in both doorways so players see where to step (Life 2 only matters to the check, not the effect).
  shimmer(server) {
    var gate = this.at(server, this.GATE)
    if (gate) {
      var g = this.box(gate, TtlSpiritGate.portal)
      server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run particle minecraft:end_rod ${(g[0] + g[3]) / 2} ${g[1] + 2} ${(g[2] + g[5]) / 2} 1.5 1.5 0.2 0.01 6`)
    }
    var home = this.at(server, this.DWELLING)
    if (home) {
      var h = this.box(home, TtlSpiritDwelling.portal)
      server.runCommandSilent(`execute in ${this.DIM} run particle minecraft:end_rod ${(h[0] + h[3]) / 2} ${h[1] + 2} ${(h[2] + h[5]) / 2} 1.5 1.5 0.2 0.01 6`)
    }
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var tick = 0
  var loop = () => server.scheduleInTicks(TtlSpiritDomain.POLL, () => {
    tick++
    var anyone = false
    server.getPlayerList().getPlayers().forEach(p => {
      anyone = true
      try {
        TtlSpiritDomain.check(server, p)
      } catch (e) {
        console.error(`[ttl] spirit domain check failed: ${e}`)
      }
    })
    if (anyone && tick % 6 === 0) {
      try {
        TtlSpiritDomain.shimmer(server)
      } catch (e) {
        console.error(`[ttl] spirit domain shimmer failed: ${e}`)
      }
    }
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var D = TtlSpiritDomain

  var where = ctx => {
    var server = ctx.source.getServer()
    var gate = D.at(server, D.GATE)
    var home = D.at(server, D.DWELLING)
    say(ctx, `Spirit gate (${TtlLife.OVERWORLD}): ${gate ? gate.join(' ') : 'not placed'}`)
    say(ctx, `Dwelling (${D.DIM}): ${home ? home.join(' ') : 'not placed'}`)
    return 1
  }
  var tp = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    if (!D.enter(server, p, false)) throw `${p.username} was not sent to the Dwelling (phase ${TtlLife.phase(p)}, placed ${D.ready(server)})`
    say(ctx, `${p.username} sent to the Dwelling`)
    return 1
  }
  // Puts the player on the doorway of the gate ("gate") or the return arch ("back") to exercise the real trigger.
  var walk = (ctx, which) => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var inGate = which === 'gate'
    var at = D.at(server, inGate ? D.GATE : D.DWELLING)
    if (!at) throw `${inGate ? D.GATE : D.DWELLING} is not placed yet`
    var b = D.box(at, inGate ? TtlSpiritGate.portal : TtlSpiritDwelling.portal)
    var dim = inGate ? TtlLife.OVERWORLD : D.DIM
    server.runCommandSilent(`execute in ${dim} run tp ${p.username} ${(b[0] + b[3]) / 2} ${b[1]} ${(b[2] + b[5]) / 2}`)
    say(ctx, `${p.username} put in the ${which} doorway`)
    return 1
  }
  var expect = (ctx, want) => {
    var p = target(ctx)
    var inside = TtlLife.dimensionOf(p) === D.DIM
    if (inside !== want) throw `expected ${p.username} to be ${want ? 'in' : 'out of'} ${D.DIM}, they are in ${TtlLife.dimensionOf(p)}`
    say(ctx, `spirit domain: ${p.username} is ${want ? 'in' : 'out of'} ${D.DIM} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('spiritdomain')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('where').executes(logged(where)))
      .then(Commands.literal('tp')
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(tp))))
      .then(Commands.literal('walk')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.literal('gate').executes(logged(ctx => walk(ctx, 'gate'))))
          .then(Commands.literal('back').executes(logged(ctx => walk(ctx, 'back'))))))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.literal('in').executes(logged(ctx => expect(ctx, true))))
          .then(Commands.literal('out').executes(logged(ctx => expect(ctx, false))))))))
})
