// priority: 60
// Boss commands (Brigadier merges these into the /ttl tree; boss.js has the logic).
// Ops:  /ttl boss summon <id> [x y z]   summon a boss: at x y z in the dimension the command runs in (use `execute in <dim> run`),
//                                       else at its arena (bosses.toml), else where the player running it stands. Skips the
//                                       cooldown and `requires`, but a bound arena (radius) still refuses a spot outside it.
//       /ttl boss list                  every boss: tier, fixed spawn (kind, place, summoner conditions), wild chance, state while one is out
//       /ttl boss wild                  the wild roll: knobs, today's starts, what is roaming, every boss's chance per day
//       /ttl boss wild roll <id> [player]   start a wild boss near the player (default: you) now: no chance, region, weather or day cap, but
//                                       the boss cooldown, max_active and "already out there" still refuse (printed, not an error)
//       /ttl boss testparty set <a> <b> [c]   test hook: these players are one party for boss credit (test bots then count); `clear` ends it
//       /ttl boss abort [id]            remove a summoned boss (or all) without rewards (a freed arena goes to the head of its queue)
//       /ttl boss reset <player>        forget the player's boss stages (ttl.boss.t1-t4, ttl.defeated.<id>), kill counts and cooldown stamps
//       /ttl boss cooldown clear <id|all>   forget the boss's per-party cooldown stamps (every soul) and its arena gaps (tests leave
//                                       no cooldown behind)
//       /ttl boss arena clear <id|all>  forget the arena gaps a boss left and its queue (the party stamps stay)
//       /ttl boss queue [id]            who waits for which arena (place, party, held or waiting); `queue clear [id]` empties it
//       /ttl boss testecho set <id> | clear   test hook: the boss counts as already fallen in the world (its fights are echoes)
//       /ttl boss expect <player> stage <t1|t2|t3|t4|none> <yes|no>   test assertion: prints "ttl: ..." when it does not hold
//       /ttl boss expect <player> defeated <id> <yes|no>              the stage ttl.defeated.<id>
//       /ttl boss expect <player> kills <id> <n>
//       /ttl boss expect <player> active <id> <yes|no>                whether a summoned boss of that id is out
//       /ttl boss expect <player> fighting <id> <yes|no>              whether a boss of that id is out and its last poll saw the
//                                                                     player in range (what a kill without a killer pays; tests
//                                                                     wait for it with `@until` before killing the boss)
//       /ttl boss expect <player> cooldown <id> <yes|no>              whether the player's PARTY is on cooldown for the id (any
//                                                                     member's stamp; cooldown_scope server: the old global stamp)
//       /ttl boss expect <player> busy <id> <yes|no>                  whether the boss's arena is busy, settling or held for others
//       /ttl boss expect <player> queued <id> <yes|no>                whether the player's party waits in the boss's queue
//       /ttl boss expect <player> ready <id> <yes|no>                 whether the arena is held for the player's party now
//       /ttl boss expect <player> cansummon <id> <yes|no>             dry run of the player summoning the boss at its arena (every rule)
//       /ttl boss expect <player> summonhere <id> <yes|no>            dry run of an ops summon at the player's position (continent line)
//       /ttl boss expect <player> continent here <yes|no>             whether the player stands on the canon continent
//       /ttl boss expect <player> story <id> <yes|no>                 whether a story (not wild) instance of that id is out
//       /ttl boss expect <player> echo <id> <yes|no>                  whether an out-there instance of that id is an echo
//       /ttl boss expect <player> gate <id> <yes|no>                  whether the player may summon the boss (cooldown ignored; requires + spawn.stages)
//       /ttl boss expect <player> spawn <id> <kind|none>              the fixed spawn kind (quest, altar, statue, event)
//       /ttl boss expect <player> wild <id> <yes|no>                  whether an out-there instance of that id came from the wild roll
//       /ttl boss expect <player> wildblock <id> <yes|no>             whether a manual wild roll of that id is refused right now
//       /ttl boss expect <player> chance <id> <fraction>              the player's wild chance per day for that boss (with path_mult)
//       /ttl boss expect <player> wildregion <id> <yes|no>            whether the player stands in one of the boss's wild regions
//       /ttl boss expect <player> cores <names|-> <n>                 Skill Cores held by the player plus the comma-separated names
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
        if (active[k].id === def.id) out.push(`${k}${active[k].wild ? ' wild' : ''}${active[k].echo ? ' echo' : ''} ${active[k].state} at ${active[k].dim} ${Math.floor(active[k].x)} ${Math.floor(active[k].y)} ${Math.floor(active[k].z)}`)
      }
      var cd = Math.ceil(TtlBoss.cooldownLeft(server, def) / 60000)
      var spot = TtlBoss.arenaOf(server, def, {})
      var gap = typeof spot === 'string' ? 0 : Math.ceil(TtlBoss.arenaGapLeft(server, TtlBoss.arenaKey(spot)) / 60000)
      var waiting = (TtlBoss.queueLoad(server)[def.id] || []).length
      var where = (def.spawn && def.spawn.at) || def.arena
      var place = ''
      if (where) {
        place = where.build ? ` at build ${where.build}` : where.landmark ? ` at landmark ${where.landmark}` : ` at ${where.x} ${where.z}${where.radius !== undefined ? ` r${where.radius}` : ''}`
      }
      var kind = def.spawn ? ` ${def.spawn.kind}${place}` : place ? ` arena${place}` : ' wild only'
      var req = (def.requires || []).concat((def.spawn && def.spawn.stages) || [])
      var wild = def.wild && Number(def.wild.chance_per_day) > 0 ? ` wild ${Math.round(Number(def.wild.chance_per_day) * 10000) / 100}%/day in ${def.wild.regions.join('')}` : ''
      say(ctx, `T${def.tier} ${def.id} (${def.entity}${def.proxy ? ', proxy' : ''}) "${def.title}"${kind}${req.length ? ` needs ${req.join(',')}` : ''}${wild}${out.length ? ` OUT: ${out.join('; ')}` : ''}${cd > 0 ? ` cooldown ${cd} min` : ''}${gap > 0 ? ` arena settles ${gap} min` : ''}${waiting ? ` queue ${waiting}` : ''}`)
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
    target.persistentData.remove('ttl.boss.lastkill')
    var server = ctx.source.getServer()
    var stamps = TtlBoss.readJson(server, 'ttl.boss.lastkill', {})
    delete stamps[TtlBoss.uid(target)]
    TtlBoss.writeJson(server, 'ttl.boss.lastkill', stamps)
    say(ctx, `boss: forgot the boss record of ${target.username}`)
    return 1
  }

  var wildStatus = ctx => {
    TtlWild.lines(ctx.source.getServer()).forEach(l => say(ctx, l))
    return 1
  }

  // Refusals are printed as plain lines, not "ttl: ..." errors, so a test can provoke one and assert on state afterwards.
  var wildRoll = withTarget => ctx => {
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id').toLowerCase()
    var def = TtlBoss.def(id)
    if (!def) throw `unknown boss ${id}`
    if (!def.wild) throw `${id} has no wild table in bosses.toml`
    var player = withTarget ? Arguments.PLAYER.getResult(ctx, 'target') : ctx.source.getEntity()
    if (!player || !player.isPlayer()) throw 'give a player: /ttl boss wild roll <id> <player>'
    var res = TtlWild.roll(server, def, player, { manual: true, by: String(ctx.source.getTextName()) })
    if (!res.ok) {
      say(ctx, `boss wild ${id}: refused: ${res.error}`)
      return 0
    }
    say(ctx, `boss wild ${id}: rolled near ${player.username} at ${res.x} ${res.z}${res.region ? ` in ${res.region}` : ''} (it appears in a second or two; see the log)`)
    return 1
  }

  var testParty = ctx => {
    var server = ctx.source.getServer()
    var uuids = []
    var names = ['a', 'b', 'c']
    for (var i = 0; i < names.length; i++) {
      try {
        uuids.push(TtlBoss.uid(Arguments.PLAYER.getResult(ctx, names[i])))
      } catch (e) {
        // the optional third player
      }
    }
    server.persistentData.putString('ttl.boss.testparty', JSON.stringify({ members: uuids }))
    say(ctx, `boss: ${uuids.length} players now share boss credit as one test party`)
    return 1
  }

  var testPartyClear = ctx => {
    ctx.source.getServer().persistentData.remove('ttl.boss.testparty')
    say(ctx, 'boss: test party cleared')
    return 1
  }

  var cores = (server, p) => {
    var n = 0
    var inv = p.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var stack = inv.getItem(i)
      if (!stack.isEmpty() && String(stack.id) === 'ttl:skill_core') n += Number(stack.count)
    }
    return n
  }

  var yesno = v => (v ? 'yes' : 'no')

  var queueStatus = withId => ctx => {
    var server = ctx.source.getServer()
    var only = withId ? arg(ctx, 'id').toLowerCase() : ''
    var q = TtlBoss.queueLoad(server)
    var keys = {}
    Object.keys(q).forEach(id => q[id].forEach(e => { if (!only || id === only) keys[e.akey] = true }))
    var n = 0
    Object.keys(keys).forEach(akey => {
      TtlBoss.queueOf(server, akey).forEach((e, i) => {
        if (only && e.boss !== only) return
        var state = e.ready ? `held for ${Math.ceil((e.ready + TtlBoss.conf().queueTtlMs - Date.now()) / 60000)} min` : `waiting ${Math.round((Date.now() - e.at) / 60000)} min`
        say(ctx, `queue ${akey} #${i + 1}: ${e.boss} for the party of ${e.by} (${e.party}), ${state}`)
        n++
      })
    })
    if (n === 0) say(ctx, `queue: nobody waits${only ? ` for ${only}` : ''}`)
    return 1
  }

  var queueClear = withId => ctx => {
    var server = ctx.source.getServer()
    var id = withId ? arg(ctx, 'id').toLowerCase() : ''
    var q = TtlBoss.queueLoad(server)
    if (id) delete q[id]
    else q = {}
    TtlBoss.queueSave(server, q)
    console.info(`[ttl] boss: queue cleared${id ? ` for ${id}` : ''}`)
    say(ctx, `boss: queue cleared${id ? ` for ${id}` : ''}`)
    return 1
  }

  var arenaClear = ctx => {
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id').toLowerCase()
    if (id !== 'all' && !TtlBoss.def(id)) throw `unknown boss ${id}`
    TtlBoss.clearArena(server, id === 'all' ? '' : id)
    console.info(`[ttl] boss: arena gaps and queue cleared for ${id}`)
    say(ctx, `boss: arena gaps and queue cleared for ${id}`)
    return 1
  }

  var testEcho = ctx => {
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id').toLowerCase()
    if (!TtlBoss.def(id)) throw `unknown boss ${id}`
    var list = TtlBoss.readJson(server, 'ttl.boss.testecho', [])
    if (!Array.isArray(list)) list = []
    if (list.indexOf(id) < 0) list.push(id)
    TtlBoss.writeJson(server, 'ttl.boss.testecho', list)
    say(ctx, `boss: ${id} counts as already fallen (test echo)`)
    return 1
  }

  var testEchoClear = ctx => {
    ctx.source.getServer().persistentData.remove('ttl.boss.testecho')
    say(ctx, 'boss: test echoes cleared')
    return 1
  }

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
    } else if (field === 'fighting') {
      var fights = TtlBoss.load(server)
      var me = TtlBoss.uid(target)
      var seen = false
      for (var k4 in fights) {
        if (fights[k4].id === a && (fights[k4].last || []).indexOf(me) >= 0) seen = true
      }
      got = yesno(seen)
    } else if (field === 'cooldown') {
      var def = TtlBoss.def(a)
      if (!def) throw `unknown boss ${a}`
      got = yesno(TtlBoss.cooldownLeft(server, def, target) > 0)
    } else if (field === 'busy') {
      var bd = TtlBoss.def(a)
      if (!bd) throw `unknown boss ${a}`
      var bpos = TtlBoss.arenaOf(server, bd, {})
      if (typeof bpos === 'string') throw bpos
      got = yesno(!!TtlBoss.arenaBlock(server, bd, bpos, TtlBoss.arenaKey(bpos), TtlBoss.partyKey(server, target), false))
    } else if (field === 'queued' || field === 'ready') {
      if (!TtlBoss.def(a)) throw `unknown boss ${a}`
      var qe = TtlBoss.queueEntry(server, a, TtlBoss.partyKey(server, target).id)
      got = yesno(!!qe && (field === 'ready' ? !!qe.ready : !qe.ready))
    } else if (field === 'cansummon') {
      if (!TtlBoss.def(a)) throw `unknown boss ${a}`
      var dry = TtlBoss.plan(server, a, { summoner: target })
      if (dry.error) say(ctx, `boss ${target.username}: ${a} would be refused: ${dry.error}`)
      got = yesno(!dry.error)
    } else if (field === 'summonhere') {
      if (!TtlBoss.def(a)) throw `unknown boss ${a}`
      var here = TtlBoss.plan(server, a, { force: true, dim: String(target.level.dimension), x: Math.floor(target.getX()), y: Math.floor(target.getY()), z: Math.floor(target.getZ()) })
      if (here.error) say(ctx, `boss ${target.username}: ${a} here would be refused: ${here.error}`)
      got = yesno(!here.error)
    } else if (field === 'continent') {
      if (a !== 'here') throw 'use: expect <player> continent here <yes|no>'
      got = yesno(TtlBoss.onContinent(String(target.level.dimension), target.getX(), target.getZ()))
    } else if (field === 'story' || field === 'echo') {
      var st = TtlBoss.load(server)
      var hit = false
      for (var k3 in st) {
        if (st[k3].id !== a) continue
        if (field === 'story' ? !st[k3].wild : !!st[k3].echo) hit = true
      }
      got = yesno(hit)
    } else if (field === 'gate') {
      var gated = TtlBoss.def(a)
      if (!gated) throw `unknown boss ${a}`
      got = yesno(!TtlBoss.gate(gated, { summoner: target }))
    } else if (field === 'spawn') {
      var sp = TtlBoss.def(a)
      if (!sp) throw `unknown boss ${a}`
      got = sp.spawn ? String(sp.spawn.kind) : 'none'
    } else if (field === 'wild') {
      var live = TtlBoss.load(server)
      var wildOut = false
      for (var k2 in live) {
        if (live[k2].id === a && live[k2].wild) wildOut = true
      }
      got = yesno(wildOut)
    } else if (field === 'wildblock') {
      var wd = TtlBoss.def(a)
      if (!wd) throw `unknown boss ${a}`
      got = yesno(!!TtlWild.blocker(server, wd, true))
    } else if (field === 'chance') {
      var cd2 = TtlBoss.def(a)
      if (!cd2 || !cd2.wild) throw `${a} has no wild table`
      var chance = TtlWild.chanceFor(cd2, target)
      if (Math.abs(chance - Number(b)) > 1e-9) throw `${target.username}: expected chance ${a} = ${b}, got ${chance}`
      say(ctx, `boss ${target.username}: chance ${a} = ${b} as expected`)
      return 1
    } else if (field === 'wildregion') {
      var rd = TtlBoss.def(a)
      if (!rd || !rd.wild) throw `${a} has no wild table`
      var region = TtlWild.regionOf(Math.floor(target.getX()), Math.floor(target.getZ()))
      got = yesno(!!region && rd.wild.regions.indexOf(region.key) >= 0)
    } else if (field === 'cores') {
      var total = cores(server, target)
      if (a !== '-') {
        a.split(',').forEach(n => {
          var other = server.getPlayerList().getPlayerByName(n)
          if (!other) throw `no player ${n} online`
          if (String(other.username) !== String(target.username)) total += cores(server, other)
        })
      }
      if (String(total) !== b) throw `${target.username}: expected cores ${a} = ${b}, got ${total}`
      say(ctx, `boss ${target.username}: cores ${a} = ${b} as expected`)
      return 1
    } else {
      throw `unknown field ${field} (stage, defeated, kills, active, cooldown, busy, queued, ready, cansummon, summonhere, continent, story, echo, gate, spawn, wild, wildblock, chance, wildregion or cores)`
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
      .then(Commands.literal('wild')
        .executes(logged(wildStatus))
        .then(Commands.literal('roll')
          .then(Commands.argument('id', Arguments.STRING.create(event))
            .executes(logged(wildRoll(false)))
            .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(wildRoll(true)))))))
      .then(Commands.literal('testparty')
        .then(Commands.literal('set')
          .then(Commands.argument('a', Arguments.PLAYER.create(event))
            .then(Commands.argument('b', Arguments.PLAYER.create(event))
              .executes(logged(testParty))
              .then(Commands.argument('c', Arguments.PLAYER.create(event)).executes(logged(testParty))))))
        .then(Commands.literal('clear').executes(logged(testPartyClear))))
      .then(Commands.literal('abort')
        .executes(logged(abort(false)))
        .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(abort(true)))))
      .then(Commands.literal('reset')
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(reset))))
      .then(Commands.literal('cooldown')
        .then(Commands.literal('clear')
          .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(ctx => {
            var server = ctx.source.getServer()
            var id = String(Arguments.STRING.getResult(ctx, 'id')).toLowerCase()
            var ids = id === 'all' ? TtlBoss.defs().map(d => d.id) : [id]
            if (id !== 'all' && !TtlBoss.def(id)) throw `unknown boss ${id}`
            ids.forEach(b => {
              TtlBoss.clearCooldown(server, b)
              var gaps = TtlBoss.readJson(server, 'ttl.boss.arena', {})
              Object.keys(gaps).forEach(g => { if (gaps[g].id === b) delete gaps[g] })
              TtlBoss.writeJson(server, 'ttl.boss.arena', gaps)
            })
            console.info(`[ttl] boss: cooldown cleared for ${id}`)
            ctx.source.sendSystemMessage(Text.of(`boss: cooldown cleared for ${id}`))
            return 1
          })))))
      .then(Commands.literal('arena')
        .then(Commands.literal('clear')
          .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(arenaClear)))))
      .then(Commands.literal('queue')
        .executes(logged(queueStatus(false)))
        .then(Commands.literal('clear')
          .executes(logged(queueClear(false)))
          .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(queueClear(true)))))
        .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(queueStatus(true)))))
      .then(Commands.literal('testecho')
        .then(Commands.literal('set')
          .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(testEcho))))
        .then(Commands.literal('clear').executes(logged(testEchoClear))))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('a', Arguments.STRING.create(event))
              .then(Commands.argument('b', Arguments.STRING.create(event)).executes(logged(expect)))))))))
})
