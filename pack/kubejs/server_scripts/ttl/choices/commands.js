// priority: 60
// /ttl choice: moral-choice scenes (Brigadier merges these into the /ttl tree). Engine: choices/engine.js.
// Players: /ttl choice                                   the scenes near you and their choices (clickable)
//          /ttl choice take <sid> <route>                take a menu route (what the buttons run)
// Ops:     /ttl choice list                              open scenes, registered events and their weights now
//          /ttl choice spawn <event> [<pos>]             a scene at the position (default: where you stand), spot rules
//                                                        skipped except the Mortal Realm and other scenes (ops/tests)
//          /ttl choice spawn <event> near <player>       a scene where a natural roll would put it (every rule applies)
//          /ttl choice roll [<player>]                   a natural roll now (no chance, no gap; the caps apply)
//          /ttl choice resolve <sid> <route> [<player>]  resolve as if <player> (default: nobody) completed the route
//          /ttl choice resolve <sid> neutral             end it the neutral way now
//          /ttl choice act <player> <sid> <route>        take a menu route as that player (bots)
//          /ttl choice test <player> <verb> <sid> [<arg>]  the scene's test verbs (heal [n], free, feed <n>, kill <role>,
//                                                        owner name|bind)
//          /ttl choice test <player> skill <ids|none>    test hook: the soul counts as having these skills ("necro" = a
//                                                        necromancer), comma-separated
//          /ttl choice testonline <n>                    test hook: Life 2 souls online for the scale (0 = count them)
//          /ttl choice clear                             end and clear every scene now (no costs, no chronicle)
//          /ttl choice reset <player>                    test hook: forget the soul's choice history, dark cap and test skills
//          /ttl choice expect scene <sid|last> <field> <value>   test assertion: "ttl: ..." when it does not hold
//            fields: state (open|good|grey|dark|neutral), route, actor, event, home, mult, online, region,
//                    n_<role> (spawned), alive_<role> (now; "unloaded" when the scene is not loaded), part_<name> (how or
//                    no), paid_<name> / saw_<name> (yes|no), prog_<key>
//          /ttl choice expect player <player> <field> <value>   done_<event>.<road> (times), last_route, last_road,
//                    last_event, last_noted (balance notes of the last route), tide_dark (balance points today),
//                    can_<sid|last>.<route> (yes|no: may the soul take that menu route now)
//          /ttl choice expect world <field> <value>      open (open scenes), active (incl. clearing), events (registered),
//                    room (scenes that may still open under max_active)
//          Every <sid> also takes `last` (the newest scene). Test verb `home <faction>` sets a scene's home faction.
const TtlChoicesCmd = {
  sceneField(server, scene, field) {
    if (!scene) return 'none'
    var simple = { state: scene.state, route: scene.route || 'none', actor: scene.actor || 'none', event: scene.id, home: scene.home || 'none', mult: String(scene.mult), online: String(scene.online), region: (scene.region && scene.region.key) || 'none' }
    if (field in simple) return String(simple[field])
    var m = /^(n|alive|part|paid|saw|prog)_(.+)$/.exec(field)
    if (!m) throw `unknown field ${field} (${Object.keys(simple).join(', ')}, n_/alive_<role>, part_/paid_/saw_<name>, prog_<key>)`
    var k = m[2]
    if (m[1] === 'n') return String((scene.n || {})[k] || 0)
    if (m[1] === 'part') return String((scene.part || {})[k] || 'no')
    if (m[1] === 'paid') return (scene.paid || []).indexOf(k) >= 0 ? 'yes' : 'no'
    if (m[1] === 'saw') return (scene.saw || []).indexOf(k) >= 0 ? 'yes' : 'no'
    if (m[1] === 'prog') {
      var v = (scene.prog || {})[k]
      return v === undefined ? 'none' : (typeof v === 'object' ? JSON.stringify(v) : String(v))
    }
    if (scene.cleared) return '0'
    var ctx = TtlChoices.ctx(server, scene)
    if (!ctx.loaded()) return 'unloaded'
    return String(ctx.alive(k).length)
  },

  playerField(server, player, field) {
    var s = TtlChoices.pread(player)
    var m = /^done_([a-z0-9_]+)\.(good|grey|dark)$/.exec(field)
    if (m) return String(((s.done[m[1]] || {})[m[2]]) || 0)
    var c = /^can_([a-z0-9]+)\.([a-z0-9_]+)$/.exec(field)
    if (c) return TtlChoices.check(server, player, c[1], c[2]).why ? 'no' : 'yes'
    var last = s.last || {}
    var day = Math.floor(Date.now() / TtlChoices.DAY_MS)
    var simple = { last_route: last.route || 'none', last_road: last.road || 'none', last_event: last.event || 'none', last_noted: String(last.noted || 0), tide_dark: String(s.tide.day === day ? s.tide.dark : 0) }
    if (field in simple) return String(simple[field])
    throw `unknown field ${field} (done_<event>.<road>, can_<sid|last>.<route>, ${Object.keys(simple).join(', ')})`
  },

  worldField(server, field) {
    if (field === 'open') return String(TtlChoices.open(server).length)
    if (field === 'active') return String(Object.keys(TtlChoices.scenes(server)).length)
    if (field === 'events') return String(TtlChoices.ids().length)
    if (field === 'room') return String(Math.max(0, TtlChoices.eng().max_active - TtlChoices.open(server).length))
    throw `unknown field ${field} (open, active, events, room)`
  },

  howItWorks() {
    return [
      'No scene near you. The world sometimes puts a hard choice in a soul\'s path: a sick village, hostages, a starving band, a wounded beast.',
      'Each has an honest road and a dark shortcut. Read more: /ttl guide paths'
    ]
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] choice command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))

  var mine = ctx => {
    var player = ctx.source.getPlayerOrException()
    var server = ctx.source.getServer()
    var near = TtlChoices.near(server, player)
    if (!near.length) {
      TtlChoicesCmd.howItWorks().forEach(l => player.tell(Text.gray(l)))
      return 1
    }
    near.forEach(s => TtlChoices.menu(server, player, s))
    TtlChoices.commit(server)
    return 1
  }

  var take = ctx => {
    var player = ctx.source.getPlayerOrException()
    var why = TtlChoices.take(ctx.source.getServer(), player, str(ctx, 'sid'), str(ctx, 'route'))
    if (why) player.tell(Text.gray(`You cannot do that: ${why}.`))
    return why ? 0 : 1
  }

  var list = ctx => {
    TtlChoices.lines(ctx.source.getServer()).forEach(l => say(ctx, l))
    return 1
  }

  var spawnAt = withPos => ctx => {
    var server = ctx.source.getServer()
    var id = str(ctx, 'event')
    var dim = String(ctx.source.getLevel().dimension)
    var x, y, z
    if (withPos) {
      var pos = Arguments.BLOCK_POS.getResult(ctx, 'pos')
      x = pos.getX()
      y = pos.getY()
      z = pos.getZ()
    } else {
      var v = ctx.source.getPosition()
      x = Math.floor(v.x())
      y = Math.floor(v.y())
      z = Math.floor(v.z())
    }
    var res = TtlChoices.spawn(server, id, { x: x, y: y, z: z, dim: dim, ops: true, by: 'ops' })
    if (!res.ok) throw `${id}: ${res.error}`
    say(ctx, `choice: ${res.sid} ${id} at ${dim} ${x} ${y} ${z}, counts ${JSON.stringify(res.scene.n)}`)
    return 1
  }

  var spawnNear = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var id = str(ctx, 'event')
    var spot = TtlChoices.pickSpot(server, p)
    if (!spot) throw `no spot ${TtlChoices.eng().min_distance}-${TtlChoices.eng().max_distance} blocks from ${p.username} passes the rules`
    var res = TtlChoices.spawn(server, id, { x: spot.x, y: spot.y, z: spot.z, dim: TtlLife.dimensionOf(p), by: String(p.username), near: p })
    if (!res.ok) throw `${id}: ${res.error}`
    say(ctx, `choice: ${res.sid} ${id} at ${spot.x} ${spot.y} ${spot.z} near ${p.username}`)
    return 1
  }

  var roll = who => ctx => {
    var res = TtlChoices.roll(ctx.source.getServer(), true, who ? String(target(ctx).username) : '')
    if (!res.ok) throw `roll: ${res.error}`
    say(ctx, `choice: rolled ${res.sid} ${res.scene.id}`)
    return 1
  }

  var resolve = who => ctx => {
    var server = ctx.source.getServer()
    var sid = str(ctx, 'sid')
    var rid = str(ctx, 'route')
    if (rid === 'neutral') {
      if (!TtlChoices.neutral(server, sid, 'ops')) throw `${sid} is not open`
      say(ctx, `choice: ${sid} ended neutral`)
      return 1
    }
    var res = TtlChoices.resolve(server, sid, rid, who ? String(target(ctx).username) : '')
    if (!res.ok) throw res.error
    say(ctx, `choice: ${sid} ${rid}; paid ${res.paid.join(', ') || 'nobody'}; saw ${res.saw.join(', ') || 'nobody'}`)
    return 1
  }

  var act = ctx => {
    var p = target(ctx)
    var why = TtlChoices.take(ctx.source.getServer(), p, str(ctx, 'sid'), str(ctx, 'route'))
    if (why) throw `${p.username} cannot take ${str(ctx, 'route')}: ${why}`
    say(ctx, `choice: ${p.username} took ${str(ctx, 'route')} in ${str(ctx, 'sid')}`)
    return 1
  }

  var test = withArg => ctx => {
    var p = target(ctx)
    var verb = str(ctx, 'verb')
    var why = TtlChoices.test(ctx.source.getServer(), p, str(ctx, 'sid'), verb, withArg ? str(ctx, 'arg') : '')
    if (why) throw `${verb}: ${why}`
    say(ctx, `choice: ${p.username} ${verb} ${str(ctx, 'sid')}${withArg ? ` ${str(ctx, 'arg')}` : ''}`)
    return 1
  }

  var skill = ctx => {
    var p = target(ctx)
    var v = str(ctx, 'ids')
    if (v === 'none') p.persistentData.remove(TtlChoices.P_SKILLS)
    else p.persistentData.putString(TtlChoices.P_SKILLS, v)
    say(ctx, `choice: ${p.username} test skills ${v}`)
    return 1
  }

  var testOnline = ctx => {
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var server = ctx.source.getServer()
    if (n > 0) server.persistentData.putInt(TtlChoices.TESTONLINE, n)
    else server.persistentData.remove(TtlChoices.TESTONLINE)
    say(ctx, `choice: scale counts ${n > 0 ? n : 'the real'} Life 2 souls online`)
    return 1
  }

  var reset = ctx => {
    var p = target(ctx)
    p.persistentData.remove(TtlChoices.P_KEY)
    p.persistentData.remove(TtlChoices.P_SKILLS)
    say(ctx, `choice: ${p.username} forgot its choices (history, today's dark balance, test skills)`)
    return 1
  }

  var clear = ctx => {
    say(ctx, `choice: cleared ${TtlChoices.clearAll(ctx.source.getServer())} scene(s)`)
    return 1
  }

  var expectScene = ctx => {
    var server = ctx.source.getServer()
    var sid = str(ctx, 'sid')
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlChoicesCmd.sceneField(server, TtlChoices.scene(server, sid), field)
    if (got !== want) throw `scene ${sid}: expected ${field}=${want}, got ${got}`
    say(ctx, `choice ${sid}: ${field}=${want} as expected`)
    return 1
  }

  var expectPlayer = ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlChoicesCmd.playerField(ctx.source.getServer(), p, field)
    if (got !== want) throw `${p.username}: expected ${field}=${want}, got ${got}`
    say(ctx, `choice ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var expectWorld = ctx => {
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlChoicesCmd.worldField(ctx.source.getServer(), field)
    if (got !== want) throw `choices: expected ${field}=${want}, got ${got}`
    say(ctx, `choices: ${field}=${want} as expected`)
    return 1
  }

  var ops = src => src.hasPermission(2)
  var P = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var S = name => Commands.argument(name, Arguments.STRING.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('choice')
      .executes(logged(mine))
      .then(Commands.literal('take').then(S('sid').then(S('route').executes(logged(take)))))
      .then(Commands.literal('list').requires(ops).executes(logged(list)))
      .then(Commands.literal('spawn').requires(ops)
        .then(S('event')
          .executes(logged(spawnAt(false)))
          .then(Commands.literal('near').then(P().executes(logged(spawnNear))))
          .then(Commands.argument('pos', Arguments.BLOCK_POS.create(event)).executes(logged(spawnAt(true))))))
      .then(Commands.literal('roll').requires(ops)
        .executes(logged(roll(false)))
        .then(P().executes(logged(roll(true)))))
      .then(Commands.literal('resolve').requires(ops)
        .then(S('sid').then(S('route')
          .executes(logged(resolve(false)))
          .then(P().executes(logged(resolve(true)))))))
      .then(Commands.literal('act').requires(ops)
        .then(P().then(S('sid').then(S('route').executes(logged(act))))))
      .then(Commands.literal('test').requires(ops)
        .then(P()
          .then(Commands.literal('skill').then(S('ids').executes(logged(skill))))
          .then(S('verb').then(S('sid')
            .executes(logged(test(false)))
            .then(S('arg').executes(logged(test(true))))))))
      .then(Commands.literal('testonline').requires(ops)
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(testOnline))))
      .then(Commands.literal('clear').requires(ops).executes(logged(clear)))
      .then(Commands.literal('reset').requires(ops).then(P().executes(logged(reset))))
      .then(Commands.literal('expect').requires(ops)
        .then(Commands.literal('scene').then(S('sid').then(S('field').then(S('value').executes(logged(expectScene))))))
        .then(Commands.literal('player').then(P().then(S('field').then(S('value').executes(logged(expectPlayer))))))
        .then(Commands.literal('world').then(S('field').then(S('value').executes(logged(expectWorld))))))))
})
