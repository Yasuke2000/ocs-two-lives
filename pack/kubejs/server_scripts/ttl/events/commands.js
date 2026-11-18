// priority: 60
// Event director and World's Favor commands (Brigadier merges these into the /ttl tree from commands.js).
// Players: /ttl events mute            toggle the chat lines (and Great Sage clips) of world events for yourself; titles stay
//          /ttl favor                   reopen your open World's Favor offer
//          /ttl favor choose <id>       take one of the offered blessings
// Ops:     /ttl events                  active events and every event's next start
//          /ttl events next             the schedule only
//          /ttl events fire <id> [force]   start an event now (not counted in the daily cap; `force` restarts an active one)
//          /ttl events end [<id>]       end one event (or all of them)
//          /ttl events due <id>         test hook: make the event due now (the next tick or scheduler pass starts it)
//          /ttl events tick             test hook: run one scheduler pass now
//          /ttl events reschedule <id>  forget the stored next start and compute it again from events.toml
//          /ttl events setup <player> <ep> <hours>   test hook: a Life 2 player with this EP and this many hours played this week
//          /ttl events offerset <player> <id,id,..>  test hook: give a player exactly this Favor offer (also starts their cooldown)
//          /ttl events clear <player>   test hook: forget a player's Favor offer, cooldown and play week
//          /ttl events expect <field> ...   test assertion, prints "ttl: ..." when it does not hold
//            active <id|none> · count <n> (active events) · scheduled <id> <true|false> · registered <id> <true|false>
//            rule <gamerule> <value> (0/1 for booleans) · winner <player> (latest Favor pick)
//            offer|cooldown|unique|muted <player> <true|false>
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] events command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var player = (ctx, name) => Arguments.PLAYER.getResult(ctx, name)
  var ops = ctx => {
    if (!ctx.source.hasPermission(2)) throw 'ops only'
  }

  var status = ctx => {
    ops(ctx)
    TtlEvents.lines(ctx.source.getServer()).forEach(l => say(ctx, `events ${l}`))
    return 1
  }

  var next = ctx => {
    ops(ctx)
    var server = ctx.source.getServer()
    var times = TtlEvents.read(server, 'ttl.events.next', {})
    var ids = Object.keys(times).sort((a, b) => times[a] - times[b])
    if (ids.length === 0) say(ctx, 'events: nothing scheduled')
    ids.forEach(id => say(ctx, `events ${id}: ${TtlEvents.local(times[id]).text}`))
    return 1
  }

  var fire = force => ctx => {
    ops(ctx)
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id')
    var res = TtlEvents.fire(server, id, { force: force })
    if (!res.ok) throw res.error
    say(ctx, `events: ${id} fired`)
    return 1
  }

  var end = ctx => {
    ops(ctx)
    var server = ctx.source.getServer()
    var id = arg(ctx, 'id')
    if (!TtlEvents.end(server, id, 'manual')) throw `${id} is not active`
    say(ctx, `events: ${id} ended`)
    return 1
  }

  var endAll = ctx => {
    ops(ctx)
    say(ctx, `events: ended ${TtlEvents.endAll(ctx.source.getServer(), 'manual')} event(s)`)
    return 1
  }

  var due = ctx => {
    ops(ctx)
    var id = arg(ctx, 'id')
    if (!TtlEvents.due(ctx.source.getServer(), id)) throw `unknown event ${id}`
    say(ctx, `events: ${id} is due`)
    return 1
  }

  var tick = ctx => {
    ops(ctx)
    TtlEvents.tick(ctx.source.getServer())
    say(ctx, 'events: scheduler pass done')
    return 1
  }

  var reschedule = ctx => {
    ops(ctx)
    var id = arg(ctx, 'id')
    if (!TtlEvents.reschedule(ctx.source.getServer(), id)) throw `unknown event ${id}`
    say(ctx, `events: ${id} rescheduled`)
    return 1
  }

  var mute = ctx => {
    var p = ctx.source.getPlayerOrException()
    var on = !TtlEvents.muted(p)
    TtlEvents.setMuted(p, on)
    p.tell(Text.gold(on ? 'World event chat lines are muted; the titles stay.' : 'World event chat lines are back.'))
    return 1
  }

  var setup = ctx => {
    ops(ctx)
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var ep = Number(Arguments.INTEGER.getResult(ctx, 'ep'))
    var hours = Number(Arguments.INTEGER.getResult(ctx, 'hours'))
    ;['ttl.life1', 'ttl.corridor'].forEach(s => target.stages.remove(s))
    target.stages.add('ttl.life2')
    server.runCommandSilent(`quietly tensura edit stat ${target.username} ep current set ${ep}`)
    TtlFavor.setWeekHours(target, hours)
    say(ctx, `events: ${target.username} is a Life 2 test player (EP ${ep} requested, read back ${TtlFavor.ep(target)}, ${hours} h this week)`)
    return 1
  }

  var offerset = ctx => {
    ops(ctx)
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var ids = arg(ctx, 'ids').split(',').filter(s => s)
    var c = TtlFavor.conf()
    ids.forEach(id => { if (!c.choice[id]) throw `unknown blessing ${id}` })
    TtlFavor.offer(server, target, ids)
    say(ctx, `events: ${target.username} is offered ${ids.join(', ')}`)
    return 1
  }

  var clear = ctx => {
    ops(ctx)
    var target = player(ctx, 'target')
    TtlFavor.clear(ctx.source.getServer(), target)
    say(ctx, `events: ${target.username} cleared`)
    return 1
  }

  var favorShow = ctx => {
    var p = ctx.source.getPlayerOrException()
    if (!TtlFavor.show(ctx.source.getServer(), p)) p.tell(Text.red('You have no open blessing.'))
    return 1
  }

  var favorChoose = ctx => {
    var p = ctx.source.getPlayerOrException()
    var error = TtlFavor.choose(ctx.source.getServer(), p, arg(ctx, 'id'))
    if (error) {
      p.tell(Text.red(error))
      return 0
    }
    return 1
  }

  var bool = v => String(v) === 'true'
  var online = (ctx, name) => {
    var p = ctx.source.getServer().getPlayerList().getPlayerByName(name)
    if (!p) throw `${name} is not online`
    return p
  }
  var truth = (ctx, what, got, want) => {
    if (got !== want) throw `expected ${what} to be ${want}, it is ${got}`
    say(ctx, `events: ${what} is ${want} as expected`)
    return 1
  }

  var expect = ctx => {
    var server = ctx.source.getServer()
    var field = arg(ctx, 'field')
    var a = arg(ctx, 'a')
    var b = ''
    try {
      b = arg(ctx, 'b')
    } catch (e) {
      b = ''
    }
    var active = TtlEvents.activeIds(server)
    if (field === 'active') {
      if (a === 'none') return truth(ctx, 'the number of active events', active.length, 0)
      return truth(ctx, `${a} active`, active.indexOf(a) >= 0, true)
    }
    if (field === 'count') return truth(ctx, 'the number of active events', String(active.length), a)
    if (field === 'scheduled') return truth(ctx, `${a} scheduled`, TtlEvents.scheduled(server, a), bool(b))
    if (field === 'registered') return truth(ctx, `${a} registered`, TtlEvents.registered(a), bool(b))
    if (field === 'rule') {
      var r = server.runCommandSilent(`gamerule ${a}`)
      if (r === undefined || r === null) throw `cannot read gamerule ${a}`
      var want = b === 'true' ? '1' : b === 'false' ? '0' : b
      return truth(ctx, `gamerule ${a}`, String(r), want)
    }
    if (field === 'winner') return truth(ctx, 'the latest Favor winner', String(server.persistentData.getString('ttl.favor.winner')), a)
    var p = online(ctx, a)
    if (field === 'offer') return truth(ctx, `${p.username} having an open Favor offer`, TtlFavor.hasOffer(p), bool(b))
    if (field === 'cooldown') return truth(ctx, `${p.username} being on Favor cooldown`, TtlFavor.onCooldown(server, p), bool(b))
    if (field === 'unique') return truth(ctx, `${p.username} holding a unique`, String(p.persistentData.getString('ttl.uniques')) !== '', bool(b))
    if (field === 'muted') return truth(ctx, `${p.username} having muted events`, TtlEvents.muted(p), bool(b))
    throw `unknown field ${field}`
  }

  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('events')
      .executes(logged(status))
      .then(Commands.literal('next').executes(logged(next)))
      .then(Commands.literal('mute').executes(logged(mute)))
      .then(Commands.literal('fire')
        .then(strArg('id').executes(logged(fire(false)))
          .then(Commands.literal('force').executes(logged(fire(true))))))
      .then(Commands.literal('end')
        .executes(logged(endAll))
        .then(strArg('id').executes(logged(end))))
      .then(Commands.literal('due').then(strArg('id').executes(logged(due))))
      .then(Commands.literal('tick').executes(logged(tick)))
      .then(Commands.literal('reschedule').then(strArg('id').executes(logged(reschedule))))
      .then(Commands.literal('setup')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(intArg('ep').then(intArg('hours').executes(logged(setup))))))
      .then(Commands.literal('offerset')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(strArg('ids').executes(logged(offerset)))))
      .then(Commands.literal('clear')
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(clear))))
      .then(Commands.literal('expect')
        .then(strArg('field')
          .then(strArg('a').executes(logged(expect))
            .then(strArg('b').executes(logged(expect)))))))
    .then(Commands.literal('favor')
      .executes(logged(favorShow))
      .then(Commands.literal('choose').then(strArg('id').executes(logged(favorChoose))))))
})
