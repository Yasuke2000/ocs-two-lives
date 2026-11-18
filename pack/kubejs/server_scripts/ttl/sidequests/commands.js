// priority: 60
// Side content commands (Brigadier merges these into the /ttl tree; logic in side.js, companions.js, adventurers.js).
// Players: /ttl sidequest                     your side jobs
//          /ttl sidequest offers              the jobs offered where you stand (the adventurers' "work" button)
//          /ttl sidequest take <id>           take one (its giver place must be within settings.take_radius)
//          /ttl sidequest abandon <key>       drop one (an escort client walks off, a parcel is taken back)
//          /ttl sidequest turnin              hand in fetch jobs that have no hand-in place
//          /ttl companion                     your companion; /ttl companion hire | dismiss
// Ops:     /ttl sidequest start <player> <id>        start a job without the giver check (FTB quest command reward:
//                                                   `ttl sidequest start {p} <id>`)
//          /ttl sidequest complete|fail <player> <key>   force an outcome (test hook)
//          /ttl sidequest poll [<player>]            run the poll now (tests do not wait)
//          /ttl sidequest goto <player> <place>      stand the player at a place (resolved position; test hook)
//          /ttl sidequest bring <player>             bring the player's escort clients beside them (test hook)
//          /ttl sidequest reset <player>             forget the player's side record and stages
//          /ttl sidequest where <place>              where a place resolves now
//          /ttl sidequest expect <player> <field> <a> [<b>]   test assertion, prints "ttl: ..." when it does not hold:
//            active <key> yes|no · done <id> yes|no · stage <id> yes|no · seen <place> yes|no · count <n> (active jobs)
//            parcel <key> <n> · client <key> alive|none · progress <key> <n> (cull kills) · phase <key> <phase>
//            place <id> resolved|pending · continent <x,z> yes|no · refused <id> yes|no (would a start be refused now)
//          /ttl companion grant <player> <kind> [minutes] | clear <player> | expect <player> <field> <value>
//            count <0|1> · kind <id|none> · alive yes|no · can_hire <kind>:<yes|off|life|max|cap|kind|fee>
//          /ttl adventurers list | populate [place] | sweep | clear [place] | expect <place> count <n>
//          /ttl adventurers hold <seconds>         test hook: the ambient loop spawns nothing for that long (0 = release)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] side command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var opt = (ctx, name) => {
    try {
      return arg(ctx, name)
    } catch (e) {
      return ''
    }
  }
  var who = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var me = ctx => ctx.source.getPlayerOrException()
  var server = ctx => ctx.source.getServer()
  var ops = src => src.hasPermission(2)
  var refuse = (ctx, text) => {
    var p = ctx.source.getPlayer()
    if (p) p.tell(Text.red(text))
    else ctx.source.sendSystemMessage(Text.red(`ttl: ${text}`))
    return 0
  }
  var yesno = v => (v ? 'yes' : 'no')

  // ---- /ttl sidequest ----

  var status = target => ctx => {
    var p = target ? who(ctx) : me(ctx)
    TtlSide.statusLines(server(ctx), p).forEach(l => say(ctx, l))
    return 1
  }

  var offers = ctx => {
    var p = me(ctx)
    var list = TtlSide.offerLines(server(ctx), p)
    if (list.length === 0) {
      say(ctx, 'Nobody here has work for you. Ask at a guild hall, a plaza or a road camp.')
      return 1
    }
    say(ctx, 'Work offered here:')
    list.forEach(o => {
      var line = Text.of(`- ${o.text}${o.open ? ` (/ttl sidequest take ${o.id})` : ''}`)
      try {
        if (o.open) line = line.green().clickRunCommand(`/ttl sidequest take ${o.id}`)
      } catch (e) {
        // plain text
      }
      ctx.source.sendSystemMessage(line)
    })
    return 1
  }

  var take = ctx => {
    var r = TtlSide.start(server(ctx), me(ctx), arg(ctx, 'id').toLowerCase(), {}, true)
    return r.ok ? 1 : refuse(ctx, r.error)
  }

  var start = ctx => {
    var p = who(ctx)
    var r = TtlSide.start(server(ctx), p, arg(ctx, 'id').toLowerCase(), {}, false)
    if (!r.ok) {
      // Run as a quest reward the player reads this; staff get the reason too.
      p.tell(Text.red(`${r.error}. Ask for the job again with /ttl sidequest take ${arg(ctx, 'id')} at its giver.`))
      throw r.error
    }
    say(ctx, `side ${p.username}: started ${r.key}`)
    return 1
  }

  var abandon = ctx => {
    var p = me(ctx)
    var key = arg(ctx, 'key').toLowerCase()
    return TtlSide.fail(server(ctx), p, key, '', 'abandoned') ? 1 : refuse(ctx, `you are not on ${key} (/ttl sidequest)`)
  }

  var turnin = ctx => {
    var n = TtlSide.turnin(server(ctx), me(ctx))
    return n > 0 ? 1 : refuse(ctx, 'nothing is ready to hand in (/ttl sidequest)')
  }

  var force = done => ctx => {
    var p = who(ctx)
    var key = arg(ctx, 'key').toLowerCase()
    var ok = done ? TtlSide.complete(server(ctx), p, key, 'forced') : TtlSide.fail(server(ctx), p, key, 'forced by staff')
    if (!ok) throw `${p.username} is not on ${key}`
    say(ctx, `side ${p.username}: ${key} ${done ? 'completed' : 'failed'}`)
    return 1
  }

  var poll = target => ctx => {
    var s = server(ctx)
    var list = []
    if (target) list.push(who(ctx))
    else s.getPlayerList().getPlayers().forEach(x => list.push(x))
    list.forEach(p => {
      if (TtlLife.phase(p) !== 'life2') return
      TtlSide.tick(s, p, Number(TtlSide.set().poll_ticks) * 50)
      TtlSide.discover(s, p)
      TtlCompanion.tick(s, p)
    })
    say(ctx, `side: polled ${list.length} player(s)`)
    return 1
  }

  var place = ctx => {
    var id = arg(ctx, 'place')
    if (!TtlSidePlaces.get(id)) throw `unknown place ${id} (${TtlSidePlaces.all().map(p => p.id).join(', ')})`
    return id
  }

  var gotoPlace = ctx => {
    var p = who(ctx)
    var id = place(ctx)
    var pos = TtlSidePlaces.resolve(server(ctx), id, null, true)
    if (!pos) throw `${id} is not placed yet`
    server(ctx).runCommandSilent(`execute in ${pos.dim} run tp ${p.username} ${pos.x} ${pos.y} ${pos.z}`)
    // A surface place resolves at y 64 until its chunk is loaded: stand on the ground once it is.
    server(ctx).scheduleInTicks(20, () => {
      var full = TtlSidePlaces.resolve(server(ctx), id)
      if (full) server(ctx).runCommandSilent(`execute in ${full.dim} run tp ${p.username} ${full.x} ${full.y} ${full.z}`)
    })
    say(ctx, `side: ${p.username} at ${id}`)
    return 1
  }

  var bring = ctx => {
    var p = who(ctx)
    var s = server(ctx)
    var d = TtlSide.read(p)
    var n = 0
    Object.keys(d.active).forEach(key => {
      var rec = d.active[key]
      if (rec.kind !== 'escort' || !rec.st.npc) return
      if (TtlCmd.run(s, `execute in ${TtlLife.dimensionOf(p)} run tp ${rec.st.npc} ${p.getX()} ${p.getY()} ${p.getZ()}`) > 0) n++
    })
    say(ctx, `side: ${n} client(s) brought to ${p.username}`)
    return 1
  }

  var reset = ctx => {
    var p = who(ctx)
    var s = server(ctx)
    var d = TtlSide.read(p)
    Object.keys(d.active).forEach(key => TtlSide.cleanup(s, p, d.active[key]))
    p.persistentData.remove(TtlSide.KEY)
    var all = p.stages.getAll().toArray()
    var drop = []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i]).startsWith(TtlSide.STAGE)) drop.push(String(all[i]))
    }
    drop.forEach(st => p.stages.remove(st))
    say(ctx, `side ${p.username}: record and stages forgotten`)
    return 1
  }

  var where = ctx => {
    var id = place(ctx)
    var pos = TtlSidePlaces.resolve(server(ctx), id, null, true)
    say(ctx, pos ? `${id}: ${pos.dim} ${pos.x} ${pos.y} ${pos.z} (continent ${yesno(TtlSidePlaces.onContinent(pos.x, pos.z))}, ambient ${TtlAdventurers.last[id] || 'unchecked'})` : `${id}: pending (its anchor is not placed)`)
    return 1
  }

  var expect = ctx => {
    var s = server(ctx)
    var p = who(ctx)
    var field = arg(ctx, 'field').toLowerCase()
    var a = arg(ctx, 'a')
    var b = opt(ctx, 'b')
    var d = TtlSide.read(p)
    var got
    var want = b
    if (field === 'active') got = yesno(!!d.active[a])
    else if (field === 'done') got = yesno(!!d.done[a])
    else if (field === 'stage') got = yesno(p.stages.has(TtlSide.stageOf(a)))
    else if (field === 'seen') got = yesno(p.stages.has(`${TtlSide.STAGE}seen.${a}`))
    else if (field === 'count') {
      got = String(Object.keys(d.active).length)
      want = a
    } else if (field === 'parcel') {
      var rec = d.active[a] || { key: a }
      got = String(TtlSide.parcels(s, p, rec))
    } else if (field === 'client') {
      var r1 = d.active[a]
      var c = r1 && r1.st && r1.st.npc ? TtlSideNpc.byUuid(s, r1.st.dim, r1.st.npc) : null
      got = c && c.isAlive() ? 'alive' : 'none'
    } else if (field === 'progress') {
      var r2 = d.active[a]
      got = String(r2 && r2.st ? Number(r2.st.got || 0) : -1)
    } else if (field === 'phase') {
      var r3 = d.active[a]
      got = String(r3 && r3.st ? r3.st.phase || 'none' : 'none')
    } else if (field === 'refused') {
      var q = TtlSide.def(a)
      if (!q) throw `unknown side quest ${a}`
      var qd = {}
      for (var k in q) qd[k] = q[k]
      qd.authored = true
      got = yesno(!!TtlSide.refusal(s, p, qd, String(q.id), false))
    } else if (field === 'place') got = TtlSidePlaces.resolve(s, a, null, true) ? 'resolved' : 'pending'
    else if (field === 'continent') {
      var xz = a.split(',').map(Number)
      got = yesno(TtlSidePlaces.onContinent(xz[0], xz[1]))
    } else throw `unknown field ${field} (active, done, stage, seen, count, parcel, client, progress, phase, refused, place, continent)`
    if (got !== want) throw `${p.username}: expected side ${field} ${field === 'count' ? '' : a + ' '}= ${want}, got ${got}`
    say(ctx, `side ${p.username}: ${field} ${a}${b ? ' ' + b : ''} as expected`)
    return 1
  }

  // ---- /ttl companion ----

  var compStatus = ctx => {
    say(ctx, TtlCompanion.statusLine(me(ctx)))
    return 1
  }

  var hire = ctx => {
    var err = TtlCompanion.hire(server(ctx), me(ctx))
    return err ? refuse(ctx, err) : 1
  }

  var dismiss = ctx => {
    return TtlCompanion.end(server(ctx), me(ctx), 'you parted ways') ? 1 : refuse(ctx, 'you have no companion')
  }

  var grant = withMinutes => ctx => {
    var p = who(ctx)
    var minutes = withMinutes ? Number(Arguments.INTEGER.getResult(ctx, 'minutes')) : 0
    var err = TtlCompanion.grant(server(ctx), p, arg(ctx, 'kind'), minutes)
    if (err) throw err
    say(ctx, `companion ${p.username}: ${arg(ctx, 'kind')} granted`)
    return 1
  }

  var compClear = ctx => {
    var p = who(ctx)
    TtlCompanion.end(server(ctx), p, 'staff')
    say(ctx, `companion ${p.username}: cleared`)
    return 1
  }

  var compExpect = ctx => {
    var s = server(ctx)
    var p = who(ctx)
    var field = arg(ctx, 'field').toLowerCase()
    var want = arg(ctx, 'value')
    var rec = TtlCompanion.read(p)
    var got
    if (field === 'count') got = rec ? '1' : '0'
    else if (field === 'kind') got = rec ? String(rec.kind) : 'none'
    else if (field === 'alive') {
      var e = TtlCompanion.find(s, rec)
      got = yesno(!!e && e.isAlive())
    } else if (field === 'can_hire') {
      var parts = want.split(':')
      var code = TtlCompanion.refusal(s, p, parts[0])
      got = `${parts[0]}:${code || 'yes'}`
    } else throw `unknown field ${field} (count, kind, alive, can_hire)`
    if (got !== want) throw `${p.username}: expected companion ${field} = ${want}, got ${got}`
    say(ctx, `companion ${p.username}: ${field} ${want} as expected`)
    return 1
  }

  // ---- /ttl adventurers ----

  var advList = ctx => {
    var s = server(ctx)
    TtlSidePlaces.all().filter(pl => Number(pl.cap || 0) > 0).forEach(pl => {
      var pos = TtlSidePlaces.resolve(s, pl, null, true)
      say(ctx, `${pl.id}: cap ${pl.cap}, ${pos ? `at ${Math.floor(pos.x)} ${Math.floor(pos.z)}` : 'pending'}, last ${TtlAdventurers.last[pl.id] || 'unchecked'}`)
    })
    return 1
  }

  var advPopulate = one => ctx => {
    var s = server(ctx)
    var lines = one ? [`${place(ctx)}: ${TtlAdventurers.populate(s, TtlSidePlaces.get(place(ctx)))}`] : TtlAdventurers.populateAll(s)
    lines.forEach(l => say(ctx, `adventurers ${l}`))
    return 1
  }

  var advSweep = ctx => {
    var r = TtlAdventurers.sweep(server(ctx), true)
    say(ctx, `adventurers: ${r.found} loaded, ${r.removed} removed, ${r.moved} moved (${r.night ? 'night' : 'day'})`)
    return 1
  }

  var advClear = one => ctx => {
    say(ctx, `adventurers: ${TtlAdventurers.clear(server(ctx), one ? place(ctx) : '')} removed`)
    return 1
  }

  var advExpect = ctx => {
    var s = server(ctx)
    var pl = TtlSidePlaces.get(place(ctx))
    var field = arg(ctx, 'field')
    var want = arg(ctx, 'value')
    if (field !== 'count') throw 'unknown field (count)'
    var pos = TtlSidePlaces.resolve(s, pl, null, true)
    var got = pos ? String(TtlAdventurers.count(s, pl, pos)) : 'pending'
    if (got !== want) throw `expected adventurers ${pl.id} count ${want}, got ${got}`
    say(ctx, `adventurers ${pl.id}: count ${want} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('sidequest')
      .executes(logged(status(false)))
      .then(Commands.literal('status').executes(logged(status(false)))
        .then(playerArg().requires(ops).executes(logged(status(true)))))
      .then(Commands.literal('offers').executes(logged(offers)))
      .then(Commands.literal('take').then(strArg('id').executes(logged(take))))
      .then(Commands.literal('abandon').then(strArg('key').executes(logged(abandon))))
      .then(Commands.literal('turnin').executes(logged(turnin)))
      .then(Commands.literal('start').requires(ops).then(playerArg().then(strArg('id').executes(logged(start)))))
      .then(Commands.literal('complete').requires(ops).then(playerArg().then(strArg('key').executes(logged(force(true))))))
      .then(Commands.literal('fail').requires(ops).then(playerArg().then(strArg('key').executes(logged(force(false))))))
      .then(Commands.literal('poll').requires(ops).executes(logged(poll(false))).then(playerArg().executes(logged(poll(true)))))
      .then(Commands.literal('goto').requires(ops).then(playerArg().then(strArg('place').executes(logged(gotoPlace)))))
      .then(Commands.literal('bring').requires(ops).then(playerArg().executes(logged(bring))))
      .then(Commands.literal('reset').requires(ops).then(playerArg().executes(logged(reset))))
      .then(Commands.literal('where').requires(ops).then(strArg('place').executes(logged(where))))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(strArg('field').then(strArg('a').executes(logged(expect))
          .then(strArg('b').executes(logged(expect))))))))
    .then(Commands.literal('companion')
      .executes(logged(compStatus))
      .then(Commands.literal('status').executes(logged(compStatus)))
      .then(Commands.literal('hire').executes(logged(hire)))
      .then(Commands.literal('dismiss').executes(logged(dismiss)))
      .then(Commands.literal('grant').requires(ops).then(playerArg().then(strArg('kind').executes(logged(grant(false)))
        .then(Commands.argument('minutes', Arguments.INTEGER.create(event)).executes(logged(grant(true)))))))
      .then(Commands.literal('clear').requires(ops).then(playerArg().executes(logged(compClear))))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(strArg('field').then(strArg('value').executes(logged(compExpect)))))))
    .then(Commands.literal('adventurers').requires(ops)
      .then(Commands.literal('list').executes(logged(advList)))
      .then(Commands.literal('populate').executes(logged(advPopulate(false))).then(strArg('place').executes(logged(advPopulate(true)))))
      .then(Commands.literal('sweep').executes(logged(advSweep)))
      .then(Commands.literal('hold').then(Commands.argument('seconds', Arguments.INTEGER.create(event)).executes(logged(ctx => {
        var sec = Number(Arguments.INTEGER.getResult(ctx, 'seconds'))
        var d = server(ctx).persistentData
        if (sec > 0) d.putLong('ttl.adventurers.hold', Date.now() + sec * 1000)
        else d.remove('ttl.adventurers.hold')
        say(ctx, `adventurers: ambient spawns ${sec > 0 ? `held for ${sec} s` : 'released'}`)
        return 1
      }))))
      .then(Commands.literal('clear').executes(logged(advClear(false))).then(strArg('place').executes(logged(advClear(true)))))
      .then(Commands.literal('expect').then(strArg('place').then(strArg('field').then(strArg('value').executes(logged(advExpect))))))))
})
