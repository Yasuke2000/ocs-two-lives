// priority: 65
// Duel damage liability (owner 18/11/2026: "duels may happen anywhere, but whoever starts a duel in a public place pays
// for the damage done"). Knobs: skills.toml [absorb.liability] (TtlData.skills.absorb.liability).
//
//   Public place  inside the box of a placed build (life/builds.js `ttl.build.<name>.box`), Tempest's or Dwargon's worked
//                 area, a placed landmark (its `reach`), or a chunk claimed (FTB Chunks) by a team that is neither
//                 duellist's (their own land is never "public"). The wild is not: no liability there.
//   Liable pact   a duel (or an awakening challenge, `routes`) whose initiator or opponent stood in a public place when it
//                 opened (TtlAbsorb.accept / challenge call onOpen). The pact carries `lia` {label, ex: [team ids, uuids]}.
//   Recording     while a liable pact is open, a block broken or placed by either duellist, or blown up by an explosion
//                 one of them caused, is recorded when that block itself lies in a public place (BlockEvents.broken /
//                 placed, LevelEvents.afterExplosion). Server persistentData `ttl.absorb.damage` = JSON {pactKey: {payer,
//                 payerName, label, at, changes: [{d, x, y, z, s (state before), k: broken|placed|exploded, p (placed id),
//                 o (owner nation key or ''), l (label)}]}}, at most max_blocks changes per duel.
//   Settling      when the duel ends (TtlAbsorb.onKill) or its pact expires (a 10 s sweep): the INITIATOR (pact.a, who
//                 issued /ttl absorb duel or challenge) pays fee_per_block x changes, at most max_fee, as far as they can,
//                 through TtlEcon.charge. A share per owner goes to that nation's treasury (booked as a transfer, like a
//                 deposit); the rest (towns, builds, landmarks, personal claims) stays a sink. A Voice line tells the
//                 payer, the owning nation is told, and the server log has a line. An offline initiator is settled at the
//                 next sweep after they log in (`hold_days`, then the record is dropped with a log line).
//   Restore       restore = true: the recorded blocks are put back after settling (a broken block only where the spot is
//                 still air, a placed block only removed while it is still there), restore_per_tick per tick; no_drops
//                 = true makes a recorded broken block drop nothing, so a restored block cannot be farmed.
// Why the initiator and not the breaker: it is the owner's wording, a duel is consensual so where it is fought is the
// challenger's choice, and one payer per duel needs no per-block attribution (explosions and Tensura magic rarely
// name the breaking player). An opponent who wrecks the place on purpose still costs the initiator at most max_fee.
const TtlLiability = {
  KEY: 'ttl.absorb.damage',
  cache: null, // {uuid: {key, until}} of the duellists in a live liable pact; null = rebuild from the pacts
  boxCache: null,
  boxAt: 0,
  noDrop: {}, // "dim|x|y|z" -> millis: recorded broken blocks whose drops are swallowed
  sweepTicks: 0,

  conf() {
    var base = (TtlData.skills.absorb || {}).liability || {}
    return {
      enabled: base.enabled !== false,
      routes: base.routes || ['duel', 'awakening'],
      places: base.places || ['claims', 'towns', 'builds', 'landmarks'],
      exempt: base.exempt || [],
      perBlock: TtlEcon.amount(base.fee_per_block || { bronze: 5 }),
      maxFee: TtlEcon.amount(base.max_fee || { gold: 5 }),
      maxBlocks: Number(base.max_blocks || 512),
      restore: base.restore !== false,
      perTick: Math.max(1, Number(base.restore_per_tick || 32)),
      noDrops: base.no_drops !== false,
      holdDays: Number(base.hold_days === undefined ? 7 : base.hold_days)
    }
  },

  pactKey(p) {
    return `${p.k}|${p.a}|${p.b}|${p.t}`
  },

  routeOf(p) {
    return p.k === 'duel' ? 'duel' : p.k === 'challenge' ? 'awakening' : p.k
  },

  // ---- where is public --------------------------------------------------------------------------------

  // Boxes of towns, builds and landmarks: [{dim, x0, z0, x1, z1, label, name}], rebuilt once a minute.
  boxes(server) {
    var now = Date.now()
    if (this.boxCache && now - this.boxAt < 60000) return this.boxCache
    var c = this.conf()
    var out = []
    var ow = TtlLife.OVERWORLD
    var add = (name, label, dim, get) => {
      if (c.exempt.indexOf(name) >= 0) return
      try {
        var b = get()
        if (b) out.push({ dim: dim, x0: b.x0, z0: b.z0, x1: b.x1, z1: b.z1, label: label, name: name })
      } catch (e) {
        console.warn(`[ttl] liability: ${label} box unavailable (${e})`)
      }
    }
    if (c.places.indexOf('towns') >= 0) {
      add('tempest', 'Tempest', ow, () => { var t = TtlTempest.box(); return { x0: t.ax0, z0: t.az0, x1: t.ax1, z1: t.az1 } })
      add('dwargon', 'Dwargon', ow, () => { var d = TtlDwargon.box(); return { x0: d.ax0, z0: d.az0, x1: d.ax1, z1: d.az1 } })
    }
    if (c.places.indexOf('landmarks') >= 0 && typeof TtlLandmarks !== 'undefined') {
      TtlLandmarks.all().forEach(l => add(l.name, String(l.title || l.name), ow, () => {
        var at = String(server.persistentData.getString(TtlLandmarks.key(l, 'at')) || '').split(' ').map(Number)
        return at.length === 3 && !isNaN(at[0]) ? { x0: at[0] - l.reach, z0: at[2] - l.reach, x1: at[0] + l.reach, z1: at[2] + l.reach } : null
      }))
    }
    if (c.places.indexOf('builds') >= 0 && typeof TtlBuilds !== 'undefined') {
      TtlBuilds.all().forEach(b => add(b.name, String(b.title || b.name), String(b.dimension), () => {
        var box = String(server.persistentData.getString(TtlBuilds.key(b, 'box')) || '').split(' ').map(Number)
        return box.length === 4 && !isNaN(box[0]) ? { x0: box[0], z0: box[1], x1: box[2], z1: box[3] } : null
      }))
    }
    this.boxCache = out
    this.boxAt = now
    return out
  },

  // The FTB team id that claimed the chunk at x/z, or '' (unclaimed, or the nations package / FTB Chunks unreachable).
  claimTeam(server, dim, x, z) {
    return typeof TtlNationClaims !== 'undefined' ? TtlNationClaims.teamAt(server, dim, x, z) : ''
  },

  // True inside an arena box (arena/arenas.js): organised combat there never carries liability, even where the arena sits
  // in a placed build (the Walpurgis Hall). Guarded: the arenas may be absent.
  inArena(server, dim, x, y, z) {
    if (y === undefined || typeof TtlArenas === 'undefined' || !TtlArenas.inArena) return false
    var level = server ? server.getLevel(String(dim)) : null
    return TtlArenas.inArena(level || String(dim), [Number(x), Number(y), Number(z)]) === true
  },

  // {label, owner} of the public place at dim x/z (y: the height, for the arena exemption), or null for the wild, an arena
  // box or the duellists' own land (`ex` = their team ids and UUIDs). owner = the nation key that is paid, '' = a sink.
  placeAt(server, dim, x, z, ex, y) {
    var c = this.conf()
    if (this.inArena(server, dim, x, y, z)) return null
    if (c.places.indexOf('claims') >= 0) {
      var team = this.claimTeam(server, String(dim), x, z)
      if (team) {
        if ((ex || []).indexOf(team) >= 0) return null
        var nat = typeof TtlNations !== 'undefined' ? TtlNations.all(server)[team] : null
        return { label: nat ? String(nat.name) : 'claimed land', owner: nat ? team : '' }
      }
    }
    var list = this.boxes(server)
    for (var i = 0; i < list.length; i++) {
      var b = list[i]
      if (b.dim === String(dim) && x >= b.x0 && x <= b.x1 && z >= b.z0 && z <= b.z1) return { label: b.label, owner: '' }
    }
    return null
  },

  // Team ids and UUIDs that count as the duellists' own.
  ownIds(players) {
    var out = []
    players.forEach(p => {
      if (!p) return
      out.push(TtlRegistry.uid(p))
      try {
        var t = typeof TtlNations !== 'undefined' ? TtlNations.teamOf(p) : null
        if (t) out.push(String(t.getId()))
      } catch (e) {
        // no FTB Teams: UUIDs only
      }
    })
    return out
  },

  // ---- pacts ------------------------------------------------------------------------------------------

  // A pact just opened between `a` (initiator) and `b`: mark it liable when either stands in a public place. Returns the
  // place label or ''. Called by TtlAbsorb.accept (duel) and TtlAbsorb.challenge (awakening).
  onOpen(server, pact, a, b) {
    var c = this.conf()
    if (!c.enabled || c.routes.indexOf(this.routeOf(pact)) < 0) return ''
    var ex = this.ownIds([a, b])
    var place = null
    ;[a, b].forEach(p => {
      if (!place && p) place = this.placeAt(server, TtlLife.dimensionOf(p), Number(p.x), Number(p.z), ex, Number(p.y))
    })
    if (!place) return ''
    var list = TtlAbsorb.live(server)
    var key = this.pactKey(pact)
    list.forEach(p => { if (this.pactKey(p) === key) p.lia = { label: place.label, ex: ex } })
    TtlAbsorb.savePacts(server, list)
    var all = this.load(server)
    all[key] = { payer: pact.a, payerName: pact.an, label: place.label, at: Date.now(), changes: [] }
    this.save(server, all)
    this.cache = null
    var line = `This duel starts in ${place.label}, a public place: ${pact.an} pays for every block the fight breaks here (${TtlEcon.text(c.perBlock)} a block, at most ${TtlEcon.text(c.maxFee)}).`
    TtlAbsorb.voice(server, a, line)
    if (b) TtlAbsorb.voice(server, b, line)
    console.info(`[ttl] liability: ${pact.an} vs ${pact.bn} opened in ${place.label}; ${pact.an} is liable`)
    return place.label
  },

  // {uuid: {key, ex, until}} for the duellists of every live liable pact.
  liable(server) {
    if (this.cache) return this.cache
    var map = {}
    TtlAbsorb.live(server).forEach(p => {
      if (!p.lia || p.st !== 'open') return
      var entry = { key: this.pactKey(p), ex: p.lia.ex || [], until: Number(p.u) }
      map[p.a] = entry
      map[p.b] = entry
    })
    this.cache = map
    return map
  },

  entryFor(server, player) {
    if (!player || !player.isPlayer()) return null
    var e = this.liable(server)[TtlRegistry.uid(player)]
    return e && e.until > Date.now() ? e : null
  },

  load(server) {
    return TtlRegistry.load(server, this.KEY, {})
  },

  save(server, all) {
    TtlRegistry.store(server, this.KEY, all)
  },

  // One block change by (or caused by) a duellist. `block` is a KubeJS LevelBlock with the state BEFORE the change
  // (for 'placed': the new block; its spot is restored to air). Returns true when it was recorded.
  record(server, player, block, kind) {
    var e = this.entryFor(server, player)
    if (!e) return false
    var dim = String(block.dimension)
    var x = Number(block.x)
    var y = Number(block.y)
    var z = Number(block.z)
    var place = this.placeAt(server, dim, x, z, e.ex, y)
    if (!place) return false
    var all = this.load(server)
    var rec = all[e.key]
    if (!rec || rec.changes.length >= this.conf().maxBlocks) return false
    var state = kind === 'placed' ? 'minecraft:air' : String(block.toBlockStateString())
    if (state === 'minecraft:air' && kind !== 'placed') return false
    rec.changes.push({ d: dim, x: x, y: y, z: z, s: state, k: kind, p: kind === 'placed' ? String(block.id) : '', o: place.owner, l: place.label })
    this.save(server, all)
    if (kind === 'broken' && this.conf().restore && this.conf().noDrops) this.noDrop[`${dim}|${x}|${y}|${z}`] = Date.now()
    return true
  },

  // ---- settling ---------------------------------------------------------------------------------------

  // Charges the initiator for the duel `key` and restores the blocks. Keeps the record while the payer is offline.
  settle(server, key) {
    var all = this.load(server)
    var rec = all[key]
    if (!rec) return null
    this.cache = null
    var c = this.conf()
    var n = rec.changes.length
    var payer = TtlAbsorb.byId(server, rec.payer)
    if (n > 0 && !payer) {
      if (Date.now() - Number(rec.at) < c.holdDays * 86400000) return null
      console.warn(`[ttl] liability: ${rec.payerName} never came back to pay for ${n} blocks in ${rec.label}; record dropped`)
    }
    delete all[key]
    this.save(server, all)
    if (n === 0) return { blocks: 0, fee: 0, paid: 0 }
    var fee = Math.min(n * c.perBlock, c.maxFee)
    var paid = 0
    if (payer) {
      paid = Math.min(fee, Math.floor(TtlEcon.balance(payer)))
      if (paid > 0 && !TtlEcon.charge(server, payer, paid, 'liability:duel')) paid = 0
    }
    // Shares per owning nation; a remainder from rounding stays a sink.
    var per = {}
    rec.changes.forEach(ch => { if (ch.o) per[ch.o] = (per[ch.o] || 0) + 1 })
    var self = this
    Object.keys(per).forEach(owner => {
      var share = Math.floor(paid * per[owner] / n)
      if (share <= 0) return
      try {
        var nations = TtlNations.all(server)
        if (!nations[owner]) return
        nations[owner].treasury = Number(nations[owner].treasury || 0) + share
        TtlNations.save(server, nations)
        TtlEcon.note(server, 'sink', -share, 'liability:transfer')
        TtlNations.tell(server, owner, `${rec.payerName} pays ${TtlEcon.text(share)} into the treasury for ${per[owner]} block${per[owner] === 1 ? '' : 's'} a duel broke on your land.`)
        if (typeof TtlNations.settleOwed === 'function') TtlNations.settleOwed(server, owner)
      } catch (e) {
        console.error(`[ttl] liability: paying ${owner} failed: ${e}`)
      }
    })
    if (payer) {
      TtlAbsorb.voice(server, payer, `Your duel in ${rec.label} damaged ${n} block${n === 1 ? '' : 's'}. You pay ${TtlEcon.text(paid)} for the repairs${paid < fee ? ` (of ${TtlEcon.text(fee)}: all you carried)` : ''}.${c.restore ? ' The damage is being mended.' : ''}`)
    }
    console.info(`[ttl] liability: ${rec.payerName} charged ${paid} of ${fee} bronze for ${n} blocks in ${rec.label} (${Object.keys(per).map(o => `${o}:${per[o]}`).join(', ') || 'no nation'})`)
    if (c.restore) self.restore(server, rec.changes.slice().reverse(), c.perTick)
    return { blocks: n, fee: fee, paid: paid }
  },

  restore(server, list, perTick) {
    var self = this
    var batch = list.splice(0, perTick)
    batch.forEach(ch => {
      try {
        var level = server.getLevel(ch.d)
        if (!level) return
        var now = String(level.getBlock(ch.x, ch.y, ch.z).id)
        if (ch.k === 'placed' ? now !== ch.p : now !== 'minecraft:air') return
        TtlCmd.run(server, `execute in ${ch.d} run setblock ${ch.x} ${ch.y} ${ch.z} ${ch.s}`)
      } catch (e) {
        console.warn(`[ttl] liability: restoring ${ch.x} ${ch.y} ${ch.z} failed: ${e}`)
      }
    })
    if (list.length > 0) server.scheduleInTicks(1, () => self.restore(server, list, perTick))
  },

  // Records whose pact is no longer live (expired, or ended without onKill): settle them.
  sweep(server) {
    var all = this.load(server)
    var keys = Object.keys(all)
    if (keys.length === 0) return
    var live = {}
    TtlAbsorb.live(server).forEach(p => { live[this.pactKey(p)] = true })
    keys.forEach(k => {
      if (!live[k]) this.settle(server, k)
    })
    var now = Date.now()
    Object.keys(this.noDrop).forEach(k => { if (now - this.noDrop[k] > 5000) delete this.noDrop[k] })
  },

  clear(server) {
    this.save(server, {})
    this.cache = null
    this.noDrop = {}
  }
}

// A duellist breaks a block (the state is still the old one here).
BlockEvents.broken(event => {
  try {
    var player = event.player
    if (!player || !TtlLiability.conf().enabled) return
    TtlLiability.record(player.server, player, event.block, 'broken')
  } catch (e) {
    console.error(`[ttl] liability: broken check failed: ${e}`)
  }
})

// A duellist places a block (event.block is the new block; restoring removes it).
BlockEvents.placed(event => {
  try {
    var entity = event.entity
    if (!entity || !entity.isPlayer() || !TtlLiability.conf().enabled) return
    TtlLiability.record(entity.server, entity, event.block, 'placed')
  } catch (e) {
    console.error(`[ttl] liability: placed check failed: ${e}`)
  }
})

// An explosion a duellist caused (KubeJS: the exploder is the explosion's indirect source). The affected blocks are
// still in place in afterExplosion (NeoForge ExplosionEvent.Detonate fires before they are removed).
LevelEvents.afterExplosion(event => {
  try {
    var who = event.exploder
    if (!who || !who.isPlayer() || !TtlLiability.conf().enabled) return
    var server = event.level.getServer()
    if (!TtlLiability.entryFor(server, who)) return
    event.affectedBlocks.forEach(b => TtlLiability.record(server, who, b, 'exploded'))
  } catch (e) {
    console.error(`[ttl] liability: explosion check failed: ${e}`)
  }
})

// A recorded broken block that will be restored drops nothing (no free blocks from a public build).
BlockEvents.drops(event => {
  var swallow = false
  try {
    var b = event.block
    var k = `${String(b.dimension)}|${Number(b.x)}|${Number(b.y)}|${Number(b.z)}`
    if (TtlLiability.noDrop[k]) {
      delete TtlLiability.noDrop[k]
      swallow = true
    }
  } catch (e) {
    console.error(`[ttl] liability: drops check failed: ${e}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
  if (swallow) event.cancel()
})

// Expired duels are settled within 10 s.
ServerEvents.tick(event => {
  if (++TtlLiability.sweepTicks % 200 !== 0) return
  try {
    TtlLiability.sweep(event.server)
  } catch (e) {
    console.error(`[ttl] liability: sweep failed: ${e}`)
  }
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] liability command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var player = (ctx, name) => Arguments.PLAYER.getResult(ctx, name)
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var check = (ctx, label, got, want) => {
    if (String(got) !== String(want)) throw `expected ${label} ${want}, got ${got}`
    say(ctx, `liability: ${label} ${want} as expected`)
    return 1
  }
  var changes = s => {
    var all = TtlLiability.load(s)
    return Object.keys(all).reduce((n, k) => n + all[k].changes.length, 0)
  }
  // The block two above the player's head: what the test hook breaks and the test checks.
  var above = p => p.level.getBlock(Math.floor(Number(p.x)), Math.floor(Number(p.y)) + 2, Math.floor(Number(p.z)))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('liability').requires(op)
      // Where a player stands: the public place (and who is paid) or "wild".
      .then(Commands.literal('where').then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(ctx => {
        var p = player(ctx, 'target')
        var place = TtlLiability.placeAt(ctx.source.getServer(), TtlLife.dimensionOf(p), Number(p.x), Number(p.z), TtlLiability.ownIds([p]), Number(p.y))
        say(ctx, place ? `${p.username} stands in ${place.label} (${place.owner ? 'paid to nation ' + place.owner : 'a sink'})` : `${p.username} stands in the wild`)
        return 1
      }))))
      // Test hook: the player breaks the block two above their head, through the same path as BlockEvents.broken.
      .then(Commands.literal('testbreak').then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(ctx => {
        var s = ctx.source.getServer()
        var p = player(ctx, 'target')
        var b = above(p)
        var ok = TtlLiability.record(s, p, b, 'broken')
        TtlCmd.run(s, `execute in ${TtlLife.dimensionOf(p)} run setblock ${b.x} ${b.y} ${b.z} minecraft:air`)
        say(ctx, `liability: ${p.username} broke ${b.id} at ${b.x} ${b.y} ${b.z} (${ok ? 'recorded' : 'not recorded'})`)
        return 1
      }))))
      .then(Commands.literal('sweep').executes(logged(ctx => {
        TtlLiability.sweep(ctx.source.getServer())
        say(ctx, 'liability: sweep done')
        return 1
      })))
      .then(Commands.literal('clear').executes(logged(ctx => {
        TtlLiability.clear(ctx.source.getServer())
        say(ctx, 'liability: every damage record dropped')
        return 1
      })))
      .then(Commands.literal('expect')
        .then(Commands.literal('changes').then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(ctx =>
          check(ctx, 'recorded changes', changes(ctx.source.getServer()), Arguments.INTEGER.getResult(ctx, 'n'))))))
        .then(Commands.literal('liable').then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(ctx => {
            var p = player(ctx, 'target')
            return check(ctx, `${p.username} liable`, TtlLiability.entryFor(ctx.source.getServer(), p) ? 'yes' : 'no', str(ctx, 'value'))
          })))))
        .then(Commands.literal('arena').then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(ctx => {
            var p = player(ctx, 'target')
            var inside = TtlLiability.inArena(ctx.source.getServer(), TtlLife.dimensionOf(p), Number(p.x), Number(p.y), Number(p.z))
            return check(ctx, `${p.username} in an arena`, inside ? 'yes' : 'no', str(ctx, 'value'))
          })))))
        .then(Commands.literal('public').then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(ctx => {
            var p = player(ctx, 'target')
            var place = TtlLiability.placeAt(ctx.source.getServer(), TtlLife.dimensionOf(p), Number(p.x), Number(p.z), TtlLiability.ownIds([p]), Number(p.y))
            return check(ctx, `${p.username} in a public place`, place ? 'yes' : 'no', str(ctx, 'value'))
          })))))
        .then(Commands.literal('above').then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(ctx => {
            var p = player(ctx, 'target')
            // A block id without its namespace means minecraft: (Brigadier's plain word cannot hold a colon).
            var want = str(ctx, 'value')
            return check(ctx, `block above ${p.username}`, String(above(p).id), want.indexOf(':') < 0 ? `minecraft:${want}` : want)
          }))))))))
})
