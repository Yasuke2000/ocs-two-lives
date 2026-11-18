// priority: 60
// World Chronicle commands (Brigadier merges these into the /ttl tree; world/chronicle.js has the logic,
// design/data/world.toml the numbers; design/architecture/world-state.md §7.5). Every ops change logs `[ttl] world:`.
// Players: /ttl world                                  era, balance and tide, phases, milestones, thrones
//          /ttl world where                            is where you stand on the canon continent (story rules) or outside
// Ops:     /ttl world at <x> <z>                       the same for an overworld column
//          /ttl world log [n]                          the last n chronicle entries (default 10)
//          /ttl world balance add <n>                  move the balance (-100..100); the tide follows
//          /ttl world milestone list | fire <id>       list milestones / force one (its effects run, it stays reached)
//          /ttl world phase set <place> <phase>        set a place's growth phase (calls the place's hook outside a test mark)
//          /ttl world conflict open|close <faction>    the takeover path of a canon nation
//          /ttl world rule set <faction> <nation> <mode> | rule clear <faction>   who sits on a canon throne
//          /ttl world active set <key> <hours> | clear <key>   timed world states (e.g. rebuilding)
//          /ttl world recount                          backfill every online soul, recount from the ledger, evaluate
//          /ttl world sync <player>                    rewrite that soul's mirrors now (what login does)
//          /ttl world forget <player>                  remove that soul's ttl.world.* stages and heard Voice lines
//          /ttl world export                           one JSON line (Discord/BlueMap/Hall)
//          /ttl world testmark | testrestore           test hooks: save the world and start a blank one in which test bots
//                                                      count / put the saved world back
//          /ttl world testthreshold <souls> <pct> | testthreshold reset   test hook: replaces [threshold] until testrestore
//          /ttl world expect <what>                    test assertion: prints "ttl: ..." when it does not hold
//            continent <x> <z> <yes|no> · continentin <dim> <x> <z> <yes|no> · milestone <id> <yes|no> · phase <place> <phase>
//            tide <light|dark|none> · balance <n> · unlocked <event> <yes|no> · mood <faction> <n> · conflict <f> <yes|no>
//            rule <f> <mode|none> · first <boss> <yes|no> · threshold <n> · test <yes|no> · <dotted path in ttl.world> <value>
//            (e.g. counts.acts.light.2 3, counts.souls 4, rule.dwargon.mode vassal)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] world command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var word = (ctx, name) => arg(ctx, name).toLowerCase()
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var who = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var server = ctx => ctx.source.getServer()
  var by = ctx => String(ctx.source.getTextName())
  var ops = src => src.hasPermission(2)
  var check = err => {
    if (err) throw err
  }

  var status = ctx => {
    say(ctx, 'The world:')
    TtlChronicle.lines(server(ctx)).forEach(l => say(ctx, `  ${l}`))
    return 1
  }

  var placeText = d => `${d.inside ? 'on the continent' : 'outside the continent'}${d.owner ? ` (${d.region || d.owner})` : ''}${d.grid ? '' : ' [no canon grid: fallback]'}`

  var where = ctx => {
    var p = ctx.source.getPlayerOrException()
    var dim = TtlLife.dimensionOf(p)
    var d = TtlWorld.describe(dim, p.x, p.z)
    say(ctx, `${Math.floor(p.x)} ${Math.floor(p.z)} in ${dim}: ${placeText(d)}. ${d.inside ? 'The story rules hold here.' : 'The mods rule here, as shipped.'}`)
    return 1
  }

  var at = ctx => {
    var x = num(ctx, 'x')
    var z = num(ctx, 'z')
    say(ctx, `world: ${x} ${z}: ${placeText(TtlWorld.describe('minecraft:overworld', x, z))}`)
    return 1
  }

  var log = n => ctx => {
    var count = n ? num(ctx, 'n') : 10
    var lines = TtlChronicle.logLines(server(ctx), count)
    say(ctx, lines.length ? `world log (last ${lines.length}):` : 'world log: empty')
    lines.forEach(l => say(ctx, `  ${l}`))
    return 1
  }

  var balanceAdd = ctx => {
    var n = num(ctx, 'n')
    var now = TtlChronicle.addBalance(server(ctx), n, `ops ${by(ctx)}`)
    say(ctx, `world: balance ${n >= 0 ? '+' : ''}${n} -> ${Math.round(now)}, tide ${TtlChronicle.tide(server(ctx)) || 'none'}`)
    return 1
  }

  var milestoneList = ctx => {
    var ms = TtlChronicle.milestones(server(ctx))
    TtlChronicle.defs().forEach(d => say(ctx, `  ${d.id}: ${ms[d.id] ? `reached ${new Date(Number(ms[d.id])).toISOString().slice(0, 16)}` : 'not yet'}`))
    return 1
  }

  var milestoneFire = ctx => {
    var id = word(ctx, 'id')
    check(TtlChronicle.fire(server(ctx), id, `ops ${by(ctx)}`))
    say(ctx, `world: milestone ${id} fired`)
    return 1
  }

  var phaseSet = ctx => {
    var place = word(ctx, 'place')
    var phase = word(ctx, 'phase')
    check(TtlChronicle.setPhase(server(ctx), place, phase, `ops ${by(ctx)}`))
    say(ctx, `world: ${place} is now ${phase}`)
    return 1
  }

  var faction = (ctx, f) => {
    if (TtlChronicle.factionIds().indexOf(f) < 0) throw `unknown faction ${f} (${TtlChronicle.factionIds().join(', ')})`
    return f
  }

  var conflict = open => ctx => {
    var f = faction(ctx, word(ctx, 'faction'))
    check(open ? TtlChronicle.openConflict(server(ctx), f, `ops ${by(ctx)}`) : TtlChronicle.closeConflict(server(ctx), f, `ops ${by(ctx)}`))
    say(ctx, `world: conflict ${f} ${open ? 'opened' : 'closed'}`)
    return 1
  }

  // A nation by its name (TtlNations), stored by its team key; without the nations package the text is kept as is.
  var nationKey = (s, name) => {
    if (typeof TtlNations === 'undefined') return name
    return String(TtlNations.find(s, name).key)
  }

  var ruleSet = ctx => {
    var f = faction(ctx, word(ctx, 'faction'))
    var nation = arg(ctx, 'nation')
    var key = nationKey(server(ctx), nation)
    check(TtlChronicle.setRule(server(ctx), f, key, word(ctx, 'mode'), `ops ${by(ctx)}`))
    say(ctx, `world: ${f} is ruled by ${nation} (${word(ctx, 'mode')})`)
    return 1
  }

  var ruleClear = ctx => {
    var f = faction(ctx, word(ctx, 'faction'))
    check(TtlChronicle.clearRule(server(ctx), f, `ops ${by(ctx)}`))
    say(ctx, `world: the rule over ${f} is cleared`)
    return 1
  }

  var activeSet = on => ctx => {
    var key = word(ctx, 'key')
    TtlChronicle.setActive(server(ctx), key, on ? Date.now() + num(ctx, 'hours') * 3600000 : 0)
    console.info(`[ttl] world: active ${key} ${on ? `set for ${num(ctx, 'hours')} h` : 'cleared'} by ${by(ctx)}`)
    say(ctx, `world: ${key} ${on ? 'active' : 'cleared'}`)
    return 1
  }

  var recount = ctx => {
    TtlChronicle.pass(server(ctx))
    var c = TtlChronicle.load(server(ctx)).counts
    console.info(`[ttl] world: recount by ${by(ctx)}: ${c.souls} souls, ${c.active30} active`)
    say(ctx, `world: recounted ${c.souls} souls (${c.active30} active)`)
    return 1
  }

  var sync = ctx => {
    var p = who(ctx)
    TtlChronicle.onLogin(server(ctx), p)
    say(ctx, `world: ${p.username} synced`)
    return 1
  }

  var forget = ctx => {
    var p = who(ctx)
    var n = TtlChronicle.forget(p)
    console.info(`[ttl] world: ${p.username} forgot ${n} world stage(s) (by ${by(ctx)})`)
    say(ctx, `world: ${p.username} lost ${n} ttl.world.* stage(s)`)
    return 1
  }

  var exportLine = ctx => {
    var line = TtlChronicle.export(server(ctx))
    console.info(`[ttl] world: export ${line}`)
    say(ctx, line)
    return 1
  }

  var testmark = ctx => {
    say(ctx, TtlChronicle.testMark(server(ctx)) ? 'world: test mark set (blank test world)' : 'world: a test mark was already set, kept')
    return 1
  }

  var testrestore = ctx => {
    say(ctx, TtlChronicle.testRestore(server(ctx)) ? 'world: test state restored' : 'world: no test mark to restore')
    return 1
  }

  var testthreshold = reset => ctx => {
    if (reset) TtlChronicle.testThreshold(server(ctx), null, null)
    else TtlChronicle.testThreshold(server(ctx), num(ctx, 'souls'), num(ctx, 'pct'))
    var s = server(ctx)
    say(ctx, `world: threshold now ${TtlChronicle.threshold(s, TtlChronicle.load(s))}`)
    return 1
  }

  var yesno = v => (v ? 'yes' : 'no')

  // The value as text; numbers rounded to one decimal (the balance decays by fractions between two commands).
  var text = v => {
    if (v === undefined || v === null) return 'missing'
    if (typeof v === 'number') return String(Math.round(v * 10) / 10)
    if (typeof v === 'object') return JSON.stringify(v)
    return String(v)
  }

  var expect = ctx => {
    var s = server(ctx)
    var parts = String(Arguments.GREEDY_STRING.getResult(ctx, 'what')).trim().split(/\s+/)
    var field = parts[0]
    var need = n => {
      if (parts.length !== n + 1) throw `expect ${field} takes ${n} value(s): ${parts.slice(1).join(' ') || 'none given'}`
    }
    var got
    var want
    if (field === 'continent') {
      need(3)
      got = yesno(TtlWorld.onContinent('minecraft:overworld', Number(parts[1]), Number(parts[2])))
      want = parts[3]
    } else if (field === 'continentin') {
      need(4)
      got = yesno(TtlWorld.onContinent(parts[1], Number(parts[2]), Number(parts[3])))
      want = parts[4]
    } else if (field === 'milestone') {
      need(2)
      if (!TtlChronicle.def(parts[1])) throw `unknown milestone ${parts[1]}`
      got = yesno(TtlChronicle.reached(s, parts[1]))
      want = parts[2]
    } else if (field === 'phase') {
      need(2)
      got = TtlChronicle.phase(s, parts[1]) || 'missing'
      want = parts[2]
    } else if (field === 'tide') {
      need(1)
      got = TtlChronicle.tide(s) || 'none'
      want = parts[1]
    } else if (field === 'balance') {
      need(1)
      got = text(TtlChronicle.balance(s))
      want = text(Number(parts[1]))
    } else if (field === 'unlocked') {
      need(2)
      got = yesno(TtlChronicle.isUnlocked(s, parts[1]))
      want = parts[2]
    } else if (field === 'mood') {
      need(2)
      got = text(TtlChronicle.mood(parts[1], s))
      want = text(Number(parts[2]))
    } else if (field === 'conflict') {
      need(2)
      got = yesno(!!TtlChronicle.conflict(s, parts[1]))
      want = parts[2]
    } else if (field === 'rule') {
      need(2)
      var r = TtlChronicle.rule(s, parts[1])
      got = r ? String(r.mode) : 'none'
      want = parts[2]
    } else if (field === 'first') {
      need(2)
      got = yesno(!!TtlChronicle.firsts(s)[parts[1]])
      want = parts[2]
    } else if (field === 'threshold') {
      need(1)
      got = text(TtlChronicle.threshold(s, TtlChronicle.load(s)))
      want = text(Number(parts[1]))
    } else if (field === 'test') {
      need(1)
      got = yesno(TtlChronicle.testMode(s))
      want = parts[1]
    } else {
      need(1)
      var v = TtlChronicle.get(s, field)
      want = parts[1]
      // A count nobody has reached yet is absent from the record: it reads as 0.
      got = v === undefined && /^-?\d+(\.\d+)?$/.test(want) && field.indexOf('counts.') === 0 ? '0' : text(v)
      if (/^-?\d+(\.\d+)?$/.test(want)) want = text(Number(want))
    }
    if (got !== want) throw `world: expected ${parts.slice(0, parts.length - 1).join(' ')} = ${want}, got ${got}`
    say(ctx, `world: ${parts.join(' ')} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('world')
      .executes(logged(status))
      .then(Commands.literal('where').executes(logged(where)))
      .then(Commands.literal('at').requires(ops)
        .then(intArg('x').then(intArg('z').executes(logged(at)))))
      .then(Commands.literal('log').requires(ops)
        .executes(logged(log(false)))
        .then(intArg('n').executes(logged(log(true)))))
      .then(Commands.literal('balance').requires(ops)
        .then(Commands.literal('add').then(intArg('n').executes(logged(balanceAdd)))))
      .then(Commands.literal('milestone').requires(ops)
        .then(Commands.literal('list').executes(logged(milestoneList)))
        .then(Commands.literal('fire').then(strArg('id').executes(logged(milestoneFire)))))
      .then(Commands.literal('phase').requires(ops)
        .then(Commands.literal('set').then(strArg('place').then(strArg('phase').executes(logged(phaseSet))))))
      .then(Commands.literal('conflict').requires(ops)
        .then(Commands.literal('open').then(strArg('faction').executes(logged(conflict(true)))))
        .then(Commands.literal('close').then(strArg('faction').executes(logged(conflict(false))))))
      .then(Commands.literal('rule').requires(ops)
        .then(Commands.literal('set').then(strArg('faction').then(strArg('nation').then(strArg('mode').executes(logged(ruleSet))))))
        .then(Commands.literal('clear').then(strArg('faction').executes(logged(ruleClear)))))
      .then(Commands.literal('active').requires(ops)
        .then(Commands.literal('set').then(strArg('key').then(intArg('hours').executes(logged(activeSet(true))))))
        .then(Commands.literal('clear').then(strArg('key').executes(logged(activeSet(false))))))
      .then(Commands.literal('recount').requires(ops).executes(logged(recount)))
      .then(Commands.literal('sync').requires(ops).then(playerArg().executes(logged(sync))))
      .then(Commands.literal('forget').requires(ops).then(playerArg().executes(logged(forget))))
      .then(Commands.literal('export').requires(ops).executes(logged(exportLine)))
      .then(Commands.literal('testmark').requires(ops).executes(logged(testmark)))
      .then(Commands.literal('testrestore').requires(ops).executes(logged(testrestore)))
      .then(Commands.literal('testthreshold').requires(ops)
        .then(Commands.literal('reset').executes(logged(testthreshold(true))))
        .then(intArg('souls').then(intArg('pct').executes(logged(testthreshold(false))))))
      .then(Commands.literal('expect').requires(ops)
        .then(Commands.argument('what', Arguments.GREEDY_STRING.create(event)).executes(logged(expect))))))
})
