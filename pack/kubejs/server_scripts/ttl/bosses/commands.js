// priority: 60
// Boss commands (Brigadier merges these into the /ttl tree; boss.js has the logic).
// Ops:  /ttl boss summon <id> [x y z]   summon a boss: at x y z in the dimension the command runs in (use `execute in <dim> run`),
//                                       else at its arena (bosses.toml), else where the player running it stands. Skips the
//                                       cooldown and `requires`, but a bound arena (radius) still refuses a spot outside it.
//       /ttl boss list                  every boss, with state while one is out
//       /ttl boss abort [id]            remove a summoned boss (or all) without rewards
//       /ttl boss reset <player>        forget the player's boss stages (ttl.boss.t1-t4, ttl.defeated.<id>) and kill counts
//       /ttl boss expect <player> stage <t1|t2|t3|t4|none> <yes|no>   test assertion: prints "ttl: ..." when it does not hold
//       /ttl boss expect <player> defeated <id> <yes|no>              the stage ttl.defeated.<id>
//       /ttl boss expect <player> kills <id> <n>
//       /ttl boss expect <player> active <id> <yes|no>                whether a summoned boss of that id is out
//       /ttl boss expect <player> cooldown <id> <yes|no>              whether the id is still on cooldown
//       /ttl boss expect <player> gate <id> <yes|no>                  whether the player may summon the boss (cooldown ignored)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  // Brigadier hides script errors: log them and answer with "ttl: <error>" (what `server.sh test-all` counts as a failure).
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] boss command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))

  var summon = withPos => ctx => {
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id').toLowerCase()
    var level = ctx.source.getLevel()
    var dim = String(level.dimension)
    var opts = { force: true, by: String(ctx.source.getTextName()) }
    if (withPos) {
      opts.dim = dim
      opts.x = Number(Arguments.INTEGER.getResult(ctx, 'x'))
      opts.y = Number(Arguments.INTEGER.getResult(ctx, 'y'))
      opts.z = Number(Arguments.INTEGER.getResult(ctx, 'z'))
    } else if (ctx.source.getEntity()) {
      var pos = ctx.source.getPosition()
      opts.at = { dim: dim, x: pos.x(), y: pos.y(), z: pos.z() }
    }
    var error = TtlBoss.summon(server, id, opts)
    if (error) throw error
    say(ctx, `boss ${id}: summoning (it appears in a second or two; see the log)`)
    return 1
  }

  var list = ctx => {
    var server = ctx.source.getServer()
    var active = TtlBoss.load(server)
    TtlBoss.defs().forEach(def => {
      var out = []
      for (var k in active) {
        if (active[k].id === def.id) out.push(`${k} ${active[k].state} at ${active[k].dim} ${Math.floor(active[k].x)} ${Math.floor(active[k].y)} ${Math.floor(active[k].z)}`)
      }
      var cd = Math.ceil(TtlBoss.cooldownLeft(server, def) / 60000)
      var arena = def.arena && def.arena.radius !== undefined ? ` arena ${def.arena.x} ${def.arena.z} r${def.arena.radius}` : ''
      var req = def.requires && def.requires.length ? ` requires ${def.requires.join(',')}` : ''
      say(ctx, `T${def.tier} ${def.id} (${def.entity}) "${def.title}"${arena}${req}${out.length ? ` OUT: ${out.join('; ')}` : ''}${cd > 0 ? ` cooldown ${cd} min` : ''}`)
    })
    return 1
  }

  var abort = withId => ctx => {
    var server = ctx.source.getServer()
    var id = withId ? arg(ctx, 'id').toLowerCase() : ''
    var n = TtlBoss.abort(server, id)
    say(ctx, `boss: removed ${n} ${id || 'boss'}${n === 1 ? '' : 'es'} without rewards`)
    return 1
  }

  var reset = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    for (var t = 1; t <= 4; t++) target.stages.remove(`ttl.boss.t${t}`)
    TtlBoss.defs().forEach(def => target.stages.remove(`ttl.defeated.${def.id}`))
    target.persistentData.remove('ttl.boss.kills')
    target.persistentData.remove('ttl.boss.core.owed')
    say(ctx, `boss: forgot the boss record of ${target.username}`)
    return 1
  }

  var yesno = v => (v ? 'yes' : 'no')

  var expect = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var field = arg(ctx, 'field')
    var a = arg(ctx, 'a')
    var b = arg(ctx, 'b')
    var got
    if (field === 'stage') {
      got = yesno(target.stages.has(`ttl.boss.${a}`))
    } else if (field === 'defeated') {
      got = yesno(target.stages.has(`ttl.defeated.${a}`))
    } else if (field === 'kills') {
      var kills = JSON.parse(String(target.persistentData.getString('ttl.boss.kills')) || '{}')
      got = String(kills[a] || 0)
    } else if (field === 'active') {
      var active = TtlBoss.load(server)
      var out = false
      for (var k in active) {
        if (active[k].id === a) out = true
      }
      got = yesno(out)
    } else if (field === 'cooldown') {
      var def = TtlBoss.def(a)
      if (!def) throw `unknown boss ${a}`
      got = yesno(TtlBoss.cooldownLeft(server, def) > 0)
    } else if (field === 'gate') {
      var gated = TtlBoss.def(a)
      if (!gated) throw `unknown boss ${a}`
      got = yesno(!TtlBoss.gate(gated, { summoner: target }))
    } else {
      throw `unknown field ${field} (stage, defeated, kills, active, cooldown or gate)`
    }
    if (got !== b) throw `${target.username}: expected ${field} ${a} = ${b}, got ${got}`
    say(ctx, `boss ${target.username}: ${field} ${a} = ${b} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('boss')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('summon')
        .then(Commands.argument('id', Arguments.STRING.create(event))
          .executes(logged(summon(false)))
          .then(Commands.argument('x', Arguments.INTEGER.create(event))
            .then(Commands.argument('y', Arguments.INTEGER.create(event))
              .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(logged(summon(true))))))))
      .then(Commands.literal('list').executes(logged(list)))
      .then(Commands.literal('abort')
        .executes(logged(abort(false)))
        .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(abort(true)))))
      .then(Commands.literal('reset')
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(reset))))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('a', Arguments.STRING.create(event))
              .then(Commands.argument('b', Arguments.STRING.create(event)).executes(logged(expect)))))))))
})
