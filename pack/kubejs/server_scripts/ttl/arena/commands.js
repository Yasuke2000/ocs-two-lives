// Arena commands (arena/arenas.js, design/data/arenas.toml).
// Players: /ttl arena [list] · join <arena> [duel|party|challenge] [a|b] · leave · start
// Ops:     /ttl arena start <arena> · reset [arena] · clear <player> · defeat <player> [by] · wave <arena> clear
//          · end <arena> <a|b|draw|clear|partial|fail> · testat <arena> <x y z> | testat <arena> clear · testmode on|off
//          · expect arena <arena> state|mode|phase|result <word> | players|wave <n>
//          · expect player <player> inarena|back <yes|no> | wins|losses|draws|clears|streak <n> | cooldown <arena> <mode> <yes|no>
// `expect` prints "ttl: expected ..." when a value is wrong (tests/ingame/arenas2.rcon).
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] arena command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var player = (ctx, name) => Arguments.PLAYER.getResult(ctx, name)
  var playerArg = name => Commands.argument(name, Arguments.PLAYER.create(event))
  var stringArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))
  var server = ctx => ctx.source.getServer()
  var self = ctx => ctx.source.getPlayerOrException()
  var yn = v => v ? 'yes' : 'no'
  var check = (ctx, label, got, want) => {
    if (String(got) !== String(want)) throw `expected ${label} ${want}, got ${got}`
    say(ctx, `arena: ${label} ${want} as expected`)
    return 1
  }
  var arenaOf = ctx => {
    var a = TtlArenas.def(word(ctx, 'arena'))
    if (!a) throw `unknown arena ${word(ctx, 'arena')} (${TtlArenas.defs().map(d => d.id).join(', ')})`
    return a
  }
  // A player step: an error text goes back in red, null means it went through.
  var step = fn => logged(ctx => {
    var me = self(ctx)
    var error = fn(server(ctx), me, ctx)
    if (error) {
      me.tell(Text.red(error))
      return 0
    }
    return 1
  })

  // ---- players -------------------------------------------------------------------------------------------------

  var list = logged(ctx => {
    var s = server(ctx)
    var state = TtlArenas.load(s)
    var last = TtlArenas.last(s)
    var me = ctx.source.getPlayer()
    TtlArenas.defs().forEach(a => {
      var g = TtlArenas.geo(s, a)
      var m = state[a.id]
      var status = 'free'
      if (typeof g === 'string') status = 'closed'
      else if (m && m.st === 'lobby') status = `lobby: ${m.mode}, ${m.a.length + m.b.length} fighter(s), opened by ${m.names[m.by]}`
      else if (m && m.st !== 'done') status = `${m.mode} under way: ${TtlArenas.standing(m, 'a').length} vs ${m.mode === 'challenge' ? `wave ${m.wave}${m.phase === 'boss' ? ' (the boss)' : ''}` : TtlArenas.standing(m, 'b').length}`
      var prev = last[a.id] ? `, last ${last[a.id].mode}: ${last[a.id].result}` : ''
      say(ctx, `${a.title} (${a.id}, ${a.modes.join('/')}): ${status}${prev}`)
    })
    if (me) {
      var r = TtlArenas.json(me, 'ttl.arena.record')
      say(ctx, `Your record: ${r.w || 0} won, ${r.l || 0} lost, ${r.d || 0} drawn, challenges ${r.c || 0} cleared, ${r.p || 0} partly. /ttl arena join <arena> [duel|party|challenge]`)
    }
    return 1
  })
  var join = (withMode, withSide) => step((s, me, ctx) => TtlArenas.join(s, me, word(ctx, 'arena'),
    withMode ? word(ctx, 'mode') : '', withSide ? word(ctx, 'side') : ''))
  var leave = step((s, me) => TtlArenas.leave(s, me))
  var startMine = step((s, me) => {
    var m = TtlArenas.matchOf(s, TtlArenas.uid(me))
    if (!m) return 'You are not in an arena lobby (/ttl arena join <arena>).'
    return TtlArenas.start(s, m, me)
  })

  // ---- ops -----------------------------------------------------------------------------------------------------

  var startArena = logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    var m = TtlArenas.load(s)[a.id]
    if (!m) throw `no lobby in ${a.id}`
    var err = TtlArenas.start(s, m, null)
    if (err) throw err
    say(ctx, `arena: ${a.id} ${m.mode} started`)
    return 1
  })
  var reset = all => logged(ctx => {
    var s = server(ctx)
    var ids = all ? TtlArenas.defs().map(d => d.id) : [arenaOf(ctx).id]
    var state = TtlArenas.load(s)
    ids.forEach(id => {
      if (state[id]) TtlArenas.close(s, state[id])
      ;[`ttl.arena.test.${id}`, `ttl.arena.cd.${id}`].forEach(k => s.persistentData.remove(k))
      var last = TtlArenas.last(s)
      delete last[id]
      s.persistentData.putString(TtlArenas.LAST, JSON.stringify(last))
    })
    if (all) s.persistentData.remove('ttl.arena.testmode')
    TtlArenas.save(s)
    TtlArenas.refreshBoxes(s)
    say(ctx, `arena: reset ${ids.join(', ')}`)
    return 1
  })
  var clearPlayer = logged(ctx => {
    var p = player(ctx, 'target')
    ;['ttl.arena.cd', 'ttl.arena.record', 'ttl.arena.back'].forEach(k => p.persistentData.remove(k))
    say(ctx, `arena: cleared ${p.username} (cooldowns, record, return spot)`)
    return 1
  })
  // Test hook: the fatal-blow path without a real fight (bots cannot hit each other).
  var defeat = withBy => logged(ctx => {
    var s = server(ctx)
    var p = player(ctx, 'target')
    var m = TtlArenas.matchOf(s, TtlArenas.uid(p))
    if (!m || m.st !== 'fight') throw `${p.username} is not in a running match`
    TtlArenas.defeat(s, m, p, withBy ? player(ctx, 'by') : null)
    say(ctx, `arena: ${p.username} defeated in ${m.id}`)
    return 1
  })
  var waveClear = logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    var m = TtlArenas.load(s)[a.id]
    if (!m || m.mode !== 'challenge') throw `no challenge in ${a.id}`
    TtlArenas.clearMobs(s, m)
    say(ctx, `arena: wave ${m.wave} of ${a.id} cleared (test hook)`)
    return 1
  })
  var end = logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    var m = TtlArenas.load(s)[a.id]
    if (!m || (m.st !== 'fight' && m.st !== 'count')) throw `no running match in ${a.id}`
    var how = word(ctx, 'how')
    var g = TtlArenas.geo(s, a)
    if (typeof g === 'string') throw g
    if (m.mode === 'challenge') {
      if (['clear', 'partial', 'fail'].indexOf(how) < 0) throw 'a challenge ends clear, partial or fail'
      TtlArenas.settle(s, m, a, g, { rank: how })
    } else {
      if (['a', 'b', 'draw'].indexOf(how) < 0) throw 'a duel or party match ends a, b or draw'
      TtlArenas.settle(s, m, a, g, { side: how === 'draw' ? '' : how })
    }
    TtlArenas.save(s)
    say(ctx, `arena: ${a.id} ended ${how}`)
    return 1
  })
  // Test placement: the arena's blueprint/world origin moves to x y z in the dimension the command runs in
  // (`execute in <dim> run ttl arena testat ...`); `ready` and the Colossus checks are skipped there.
  var testat = logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    var dim = String(ctx.source.getLevel().dimension)
    s.persistentData.putString(`ttl.arena.test.${a.id}`, `${dim} ${num(ctx, 'x')} ${num(ctx, 'y')} ${num(ctx, 'z')}`)
    TtlArenas.refreshBoxes(s)
    var g = TtlArenas.geo(s, a)
    say(ctx, `arena: ${a.id} placed for a test in ${dim}, box ${g.x0} ${g.y0} ${g.z0} to ${g.x1} ${g.y1} ${g.z1}`)
    return 1
  })
  var testatClear = logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    s.persistentData.remove(`ttl.arena.test.${a.id}`)
    TtlArenas.refreshBoxes(s)
    say(ctx, `arena: ${a.id} back at its real place`)
    return 1
  })
  var testmode = logged(ctx => {
    var on = word(ctx, 'state') === 'on'
    server(ctx).persistentData.putBoolean('ttl.arena.testmode', on)
    say(ctx, `arena: test mode ${on ? 'on (min_seconds off)' : 'off'}`)
    return 1
  })

  // ---- expect ---------------------------------------------------------------------------------------------------

  var expectArena = field => logged(ctx => {
    var s = server(ctx)
    var a = arenaOf(ctx)
    var m = TtlArenas.load(s)[a.id]
    if (field === 'state') {
      var st = !m ? 'free' : m.st === 'count' ? 'fight' : m.st
      return check(ctx, `${a.id} state`, st, word(ctx, 'value'))
    }
    if (field === 'mode') return check(ctx, `${a.id} mode`, m ? m.mode : 'none', word(ctx, 'value'))
    if (field === 'phase') return check(ctx, `${a.id} phase`, m && m.phase ? m.phase : 'none', word(ctx, 'value'))
    if (field === 'result') {
      var last = TtlArenas.last(s)[a.id]
      return check(ctx, `${a.id} last result`, last ? last.result : 'none', word(ctx, 'value'))
    }
    if (field === 'players') return check(ctx, `${a.id} fighters`, m ? m.a.length + m.b.length : 0, num(ctx, 'n'))
    return check(ctx, `${a.id} wave`, m ? m.wave : 0, num(ctx, 'n'))
  })
  var expectPlayer = field => logged(ctx => {
    var s = server(ctx)
    var p = player(ctx, 'target')
    if (field === 'inarena') {
      TtlArenas.refreshBoxes(s)
      return check(ctx, `${p.username} in an arena`, yn(TtlArenas.inArena(p.level, [p.getX(), p.getY(), p.getZ()])), word(ctx, 'value'))
    }
    if (field === 'back') return check(ctx, `${p.username} has a return spot`, yn(String(p.persistentData.getString('ttl.arena.back') || '')), word(ctx, 'value'))
    if (field === 'cooldown') {
      var a = arenaOf(ctx)
      return check(ctx, `${p.username} ${a.id} ${word(ctx, 'mode')} loot cooldown`, yn(TtlArenas.cooldownLeft(p, a.id, word(ctx, 'mode')) > 0), word(ctx, 'value'))
    }
    var r = TtlArenas.json(p, 'ttl.arena.record')
    var key = { wins: 'w', losses: 'l', draws: 'd', clears: 'c', streak: 'ds' }[field]
    return check(ctx, `${p.username} ${field}`, r[key] || 0, num(ctx, 'n'))
  })

  var expectArenaNode = stringArg('arena')
  ;['state', 'mode', 'phase', 'result'].forEach(f => {
    expectArenaNode = expectArenaNode.then(Commands.literal(f).then(stringArg('value').executes(expectArena(f))))
  })
  ;['players', 'wave'].forEach(f => {
    expectArenaNode = expectArenaNode.then(Commands.literal(f).then(intArg('n').executes(expectArena(f))))
  })
  var expectPlayerNode = playerArg('target')
  ;['inarena', 'back'].forEach(f => {
    expectPlayerNode = expectPlayerNode.then(Commands.literal(f).then(stringArg('value').executes(expectPlayer(f))))
  })
  ;['wins', 'losses', 'draws', 'clears', 'streak'].forEach(f => {
    expectPlayerNode = expectPlayerNode.then(Commands.literal(f).then(intArg('n').executes(expectPlayer(f))))
  })
  expectPlayerNode = expectPlayerNode.then(Commands.literal('cooldown')
    .then(stringArg('arena').then(stringArg('mode').then(stringArg('value').executes(expectPlayer('cooldown'))))))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('arena')
      .executes(list)
      .then(Commands.literal('list').executes(list))
      .then(Commands.literal('join')
        .then(stringArg('arena').executes(join(false, false))
          .then(stringArg('mode').executes(join(true, false))
            .then(stringArg('side').executes(join(true, true))))))
      .then(Commands.literal('leave').executes(leave))
      .then(Commands.literal('start').executes(startMine)
        .then(stringArg('arena').requires(op).executes(startArena)))
      .then(Commands.literal('reset').requires(op).executes(reset(true))
        .then(stringArg('arena').executes(reset(false))))
      .then(Commands.literal('clear').requires(op).then(playerArg('target').executes(clearPlayer)))
      .then(Commands.literal('defeat').requires(op)
        .then(playerArg('target').executes(defeat(false)).then(playerArg('by').executes(defeat(true)))))
      .then(Commands.literal('wave').requires(op)
        .then(stringArg('arena').then(Commands.literal('clear').executes(waveClear))))
      .then(Commands.literal('end').requires(op)
        .then(stringArg('arena').then(stringArg('how').executes(end))))
      .then(Commands.literal('testat').requires(op)
        .then(stringArg('arena')
          .then(Commands.literal('clear').executes(testatClear))
          .then(intArg('x').then(intArg('y').then(intArg('z').executes(testat))))))
      .then(Commands.literal('testmode').requires(op).then(stringArg('state').executes(testmode)))
      .then(Commands.literal('expect').requires(op)
        .then(Commands.literal('arena').then(expectArenaNode))
        .then(Commands.literal('player').then(expectPlayerNode)))))
})
