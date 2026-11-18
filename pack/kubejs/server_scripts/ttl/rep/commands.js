// priority: 60
// Reputation commands (Brigadier merges these into the /ttl tree from commands.js). API: rep.js.
// Players: /ttl rep                                        your standing with every faction (hidden ones once they are not 0)
// Ops:     /ttl rep list <player>                          the same for someone else
//          /ttl rep set <player> <faction> <n>             exact value (clamped to -100..100)
//          /ttl rep add <player> <faction> <n>             change by n (negative lowers it); also what an NPC dialog action runs
//          /ttl rep seed <player> [<race>]                 redo the rebirth seeding from race + the stored karma verdict (test hook)
//          /ttl rep decay <player> <weeks>                 apply that many decay steps now (test hook)
//          /ttl rep renown <player>                        renown (worth) with its parts; players see their own with /ttl rep renown
//          /ttl rep bonus <player> <n>                     permanent bonus renown (quests, merit, staff); negative lowers it
//          /ttl rep log [<n>]                              the newest n (default 10) changes
//          /ttl rep expect <player> <faction> <field> <value>   test assertion: prints "ttl: ..." when it does not hold
//            fields: band (hostile|unfriendly|neutral|friendly|honored|exalted), value (exact), min, max (value >= / <=),
//                    stage (the stage ttl.faction.<f>.<value> is held), nostage (it is not held),
//                    score (the scoreboard mirror ttl.rep.<f> equals value)
//          /ttl rep expect <player> renown <field> <value>   the same with the faction "renown": fields value, min, max, score
//                    (scoreboard ttl.renown) and the parts tier, bosses, stages, rep, uniques, bonus (exact)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] rep command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()
  var player = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var int = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var faction = ctx => {
    var id = word(ctx, 'faction')
    if (!TtlRep.faction(id)) throw `unknown faction ${id} (one of ${TtlRep.ids().join(', ')})`
    return id
  }
  var ops = src => src.hasPermission(2)

  var show = target => ctx => {
    var who = target ? player(ctx) : ctx.source.getPlayerOrException()
    say(ctx, target ? `Reputation of ${who.username}:` : 'Your reputation:')
    TtlRep.lines(who).forEach(line => say(ctx, `  ${line}`))
    return 1
  }

  var change = absolute => ctx => {
    var target = player(ctx)
    var id = faction(ctx)
    var n = int(ctx, 'n')
    var server = ctx.source.getServer()
    var now = absolute ? TtlRep.set(server, target, id, n, 'command') : TtlRep.add(server, target, id, n, 'command')
    if (now === null) throw `could not change ${id}`
    say(ctx, `rep ${target.username} ${id}: ${now} (${TtlRep.band(target, id)})`)
    return 1
  }

  var seed = withRace => ctx => {
    var target = player(ctx)
    var map = TtlRep.seed(ctx.source.getServer(), target, withRace ? word(ctx, 'race') : undefined)
    say(ctx, `rep ${target.username}: seeded ${Object.keys(map).filter(k => map[k] !== 0).map(k => `${k}=${map[k]}`).join(' ') || 'all neutral'}`)
    return 1
  }

  var decay = ctx => {
    var target = player(ctx)
    var moved = TtlRep.drift(ctx.source.getServer(), target, int(ctx, 'weeks'))
    say(ctx, `rep ${target.username}: ${moved} faction${moved === 1 ? '' : 's'} drifted toward 0`)
    return 1
  }

  var tail = withN => ctx => {
    var n = withN ? int(ctx, 'n') : 10
    var list = TtlRep.log(ctx.source.getServer())
    var shown = list.slice(Math.max(0, list.length - n))
    say(ctx, shown.length ? `Reputation log (newest last, ${shown.length} of ${list.length}):` : 'Reputation log: nothing yet')
    shown.forEach(e => say(ctx, `  ${new Date(e.t).toISOString()} ${e.p} ${e.f} ${e.d >= 0 ? '+' : ''}${e.d} -> ${e.v} ${e.r}`))
    return 1
  }

  var renown = target => ctx => {
    var who = target ? player(ctx) : ctx.source.getPlayerOrException()
    var p = TtlRep.renownParts(ctx.source.getServer(), who)
    TtlRep.renown(ctx.source.getServer(), who)
    say(ctx, `Renown of ${who.username}: ${p.total}`)
    say(ctx, `  karma tier ${p.tier} · bosses ${p.bosses} · other stages ${p.stages} · reputation ${p.rep} · uniques ${p.uniques} · bonus ${p.bonus}`)
    return 1
  }

  var bonus = ctx => {
    var target = player(ctx)
    var total = TtlRep.addRenown(ctx.source.getServer(), target, int(ctx, 'n'), 'command')
    say(ctx, `renown ${target.username}: ${total}`)
    return 1
  }

  var expectRenown = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx)
    var field = word(ctx, 'field')
    var want = String(Arguments.STRING.getResult(ctx, 'value')).toLowerCase()
    var n = Number(want)
    if (isNaN(n)) throw `${field} needs a number, got ${want}`
    var parts = TtlRep.renownParts(server, target)
    TtlRep.renown(server, target)
    var who = `${target.username} renown`
    var got
    if (field === 'value') got = parts.total
    else if (field === 'min') {
      if (parts.total < n) throw `${who}: expected at least ${n}, got ${parts.total}`
      say(ctx, `rep ${who}: ${parts.total} >= ${n} as expected`)
      return 1
    } else if (field === 'max') {
      if (parts.total > n) throw `${who}: expected at most ${n}, got ${parts.total}`
      say(ctx, `rep ${who}: ${parts.total} <= ${n} as expected`)
      return 1
    } else if (field === 'score') {
      var board = server.getScoreboard()
      var obj = board.getObjective('ttl.renown')
      var info = obj ? board.getPlayerScoreInfo(target, obj) : null
      got = info ? info.value() : null
    } else if (['tier', 'bosses', 'stages', 'rep', 'uniques', 'bonus'].indexOf(field) >= 0) got = parts[field]
    else throw `unknown renown field ${field} (one of value, min, max, score, tier, bosses, stages, rep, uniques, bonus)`
    if (got !== n) throw `${who}: expected ${field}=${n}, got ${got} (parts ${JSON.stringify(parts)})`
    say(ctx, `rep ${who}: ${field}=${n} as expected`)
    return 1
  }

  var expect = ctx => {
    if (word(ctx, 'faction') === 'renown') return expectRenown(ctx)
    var target = player(ctx)
    var id = faction(ctx)
    var field = word(ctx, 'field')
    var want = String(Arguments.STRING.getResult(ctx, 'value')).toLowerCase()
    var value = TtlRep.get(target, id)
    var band = TtlRep.bandFor(id, value)
    var who = `${target.username} ${id}`
    var fail = got => { throw `${who}: expected ${field}=${want}, got ${got} (value ${value}, band ${band})` }
    var number = () => {
      var n = Number(want)
      if (isNaN(n)) throw `${field} needs a number, got ${want}`
      return n
    }
    if (field === 'band') {
      if (TtlRep.BANDS.indexOf(want) < 0) throw `unknown band ${want} (one of ${TtlRep.BANDS.join(', ')})`
      if (band !== want) fail(band)
    } else if (field === 'value') {
      if (value !== number()) fail(value)
    } else if (field === 'min') {
      if (value < number()) fail(value)
    } else if (field === 'max') {
      if (value > number()) fail(value)
    } else if (field === 'stage' || field === 'nostage') {
      if (TtlRep.BANDS.indexOf(want) < 0) throw `unknown band ${want} (one of ${TtlRep.BANDS.join(', ')})`
      var has = target.stages.has(`ttl.faction.${id}.${want}`)
      if (has !== (field === 'stage')) fail(has ? `stage ${want} held` : `stage ${want} missing`)
    } else if (field === 'score') {
      var board = ctx.source.getServer().getScoreboard()
      var obj = board.getObjective(`ttl.rep.${id}`)
      var info = obj ? board.getPlayerScoreInfo(target, obj) : null
      var score = info ? info.value() : null
      if (score === null || score !== number()) fail(score)
    } else {
      throw `unknown field ${field} (one of band, value, min, max, stage, nostage, score)`
    }
    say(ctx, `rep ${who}: ${field}=${want} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var factionArg = () => Commands.argument('faction', Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('rep')
      .executes(logged(show(false)))
      .then(Commands.literal('list').requires(ops)
        .then(playerArg().executes(logged(show(true)))))
      .then(Commands.literal('set').requires(ops)
        .then(playerArg().then(factionArg().then(intArg('n').executes(logged(change(true)))))))
      .then(Commands.literal('add').requires(ops)
        .then(playerArg().then(factionArg().then(intArg('n').executes(logged(change(false)))))))
      .then(Commands.literal('seed').requires(ops)
        .then(playerArg().executes(logged(seed(false)))
          .then(Commands.argument('race', Arguments.STRING.create(event)).executes(logged(seed(true))))))
      .then(Commands.literal('decay').requires(ops)
        .then(playerArg().then(intArg('weeks').executes(logged(decay)))))
      .then(Commands.literal('renown')
        .executes(logged(renown(false)))
        .then(playerArg().requires(ops).executes(logged(renown(true)))))
      .then(Commands.literal('bonus').requires(ops)
        .then(playerArg().then(intArg('n').executes(logged(bonus)))))
      .then(Commands.literal('log').requires(ops)
        .executes(logged(tail(false)))
        .then(intArg('n').executes(logged(tail(true)))))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(factionArg().then(Commands.argument('field', Arguments.STRING.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect)))))))))
})
