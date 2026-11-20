// priority: 60
// Economy commands (Brigadier merges these into the /ttl tree from commands.js).
// Players (Life 2; a Life 1 soul gets "ttl: Life 2 only"):
//   /ttl guild board [giver]              the Free Guild board with your status per bounty; giver desk | fuze shows only
//                                         that giver's bounties, numbered from 1 (the Easy NPC dialogs use this)
//   /ttl guild take <slot|id> [giver]     accept a bounty (max guild.max_active at once); with a giver the number counts in
//                                         that giver's list and a bounty of the other giver is refused
//   /ttl guild turnin [giver]             hand in everything that is ready (kills and visits count by themselves,
//                                         deliveries are taken from your inventory); with a giver only that giver's
//   /ttl guild abandon <slot|id> · status
//   /ttl merit                            your merit and Public Works chunks
//   /ttl merit works mark | unmark        the chunk you stand in (Life 2, Tensura overworld)
// Ops:
//   /ttl guild roll [daily|weekly|all]    re-roll the board now (logs the ids; default all)
//   /ttl guild post <id>                  put a bounty into the first slot of its period (test hook)
//   /ttl guild sample <player>            sample kills and visits now instead of waiting poll_ticks
//   /ttl guild test <player> life2        test hook: give a bot the Life 2 stage
//   /ttl guild test <player> points_<n>   test hook: set the bot's lifetime guild points (and so its rank)
//   /ttl guild reset <player>             test hook: forget the player's guild record (bots keep data between runs)
//   /ttl guild desk add <x> <y> <z> | remove <x> <y> <z> | list   interim guild desks (Tensura overworld blocks)
//   /ttl guild npc list | ensure [spot] | spawn <spot> | remove <spot> | goto <player> <spot> | expect <field> <value>
//        the Easy NPCs (Fuze, receptionists), defined in economy/guild_npcs.js
//   /ttl guild expect <player> <field> <value>
//        fields: points, done, rank, active, ready, board (slots on the desk board; board_all, board_fuze, board_desk),
//        balance (bronze), stage (rank letter of
//        the one ttl.guild.* stage), accepted_<id>, ready_<id> (true/false), got_<id> (kills or visits counted so far, none when not accepted), rep_<faction> (needs the reputation package),
//        refuse_take (what taking slot 1 answers: life2only / allowed, real effect when allowed),
//        take_<giver>_<id> (what `take <id> <giver>` answers: wrong_giver / life2only / rank / allowed (real effect) / other: ...),
//        giver_<id> (desk or fuze), turnin_<desk|fuze|any>_<id> (who takes it back: allowed / lore / wrong_giver; no effect)
//   /ttl merit test <player> <block> [n]  count n (default 1) placed blocks at the player's feet (`stone_bricks` = minecraft:stone_bricks)
//   /ttl merit reset <player> · /ttl merit expect <player> <field> <value>
//        fields: total, week, works (how many Public Works chunks they keep), faction (the faction id the chunk under the
//        player pays, or none), builder (true/false)
//   /ttl econ                             this week's faucet / sink counters (bronze) and the last weeks
//   /ttl econ give <player> <bronze> | take <player> <bronze>
//   /ttl econ expect <player> <field> <value>   fields: balance, faucet, sink, fee_<name> (bronze), can_<bronze> (true/false),
//                                         source (diagnostics: what the inventory and Lightman's holder see)
// Every `expect` answers "ttl: ..." when the value is wrong, which `server.sh test-all` counts as a failure.
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  // Brigadier hides script errors: log them and answer with "ttl: <error>" (same as commands.js).
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] economy command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var ops = src => src.hasPermission(2)
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var self = ctx => ctx.source.getPlayerOrException()
  var server = ctx => ctx.source.getServer()

  // ---- guild: players ----

  // The optional trailing `giver` argument: a run that has none must not read it (getResult throws then).
  var board = withGiver => ctx => {
    var p = self(ctx)
    TtlGuild.requireLife2(p)
    TtlGuild.boardLines(server(ctx), p, withGiver ? str(ctx, 'giver') : null).forEach(l => say(ctx, l))
    return 1
  }

  var take = withGiver => ctx => {
    var p = self(ctx)
    var e = TtlGuild.take(server(ctx), p, str(ctx, 'ref'), withGiver ? str(ctx, 'giver') : null)
    say(ctx, `Free Guild: you accepted "${e.b.title}": ${TtlGuild.what(e.b)}. Reward: ${TtlGuild.rewardText(e.b)}.`)
    return 1
  }

  var turnin = withGiver => ctx => {
    var n = TtlGuild.turnin(server(ctx), self(ctx), withGiver ? str(ctx, 'giver') : null)
    say(ctx, `Free Guild: ${n} bount${n === 1 ? 'y' : 'ies'} handed in.`)
    return 1
  }

  var abandon = ctx => {
    var e = TtlGuild.abandon(server(ctx), self(ctx), str(ctx, 'ref'))
    say(ctx, `Free Guild: you gave up "${e.b.title}".`)
    return 1
  }

  var status = ctx => {
    var p = self(ctx)
    TtlGuild.requireLife2(p)
    TtlGuild.statusLines(server(ctx), p).forEach(l => say(ctx, l))
    return 1
  }

  // ---- guild: ops ----

  var roll = which => ctx => {
    var w = which ? str(ctx, 'which') : 'all'
    if (['daily', 'weekly', 'all'].indexOf(w) < 0) throw `roll daily, weekly or all, not ${w}`
    var b = TtlGuild.ensure(server(ctx), w)
    say(ctx, `guild board ${b.date} (week ${b.week}): daily ${b.daily.join(', ')}; weekly ${b.weekly.join(', ')}`)
    return 1
  }

  var post = ctx => {
    var list = TtlGuild.post(server(ctx), str(ctx, 'id'))
    say(ctx, `guild board: ${list.map(e => `${e.slot}=${e.b.id}`).join(' ')}`)
    return 1
  }

  var sample = ctx => {
    var p = target(ctx)
    var n = TtlGuild.sample(server(ctx), p)
    say(ctx, `guild ${p.username}: sampled ${n} accepted bounties`)
    return 1
  }

  var guildReset = ctx => {
    var p = target(ctx)
    TtlGuild.reset(server(ctx), p)
    say(ctx, `guild ${p.username}: record cleared`)
    return 1
  }

  var testHook = ctx => {
    var p = target(ctx)
    var pts = /^points_(\d+)$/.exec(str(ctx, 'what'))
    if (pts) {
      var g = TtlGuild.read(p)
      g.points = Number(pts[1])
      TtlGuild.write(p, g)
      TtlGuild.sync(server(ctx), p, g)
      say(ctx, `guild ${p.username}: ${g.points} points, rank ${TtlGuild.rankOf(g).id} (test hook)`)
      return 1
    }
    if (str(ctx, 'what') !== 'life2') throw 'test hooks: life2 | points_<n>'
    if (!p.stages.has('ttl.life2')) p.stages.add('ttl.life2')
    say(ctx, `guild ${p.username}: stage ttl.life2 added (test hook)`)
    return 1
  }

  var desk = adding => ctx => {
    var key = TtlGuild.deskKey(num(ctx, 'x'), num(ctx, 'y'), num(ctx, 'z'))
    var s = server(ctx)
    var list = TtlGuild.desks(s)
    var at = list.indexOf(key)
    if (adding && at < 0) list.push(key)
    if (!adding && at >= 0) list.splice(at, 1)
    s.persistentData.putString(TtlGuild.DESKS, JSON.stringify(list))
    say(ctx, `guild desks (${list.length}): ${list.join('; ') || 'none'}`)
    return 1
  }

  var deskList = ctx => {
    var list = TtlGuild.desks(server(ctx))
    say(ctx, `guild desks (${list.length}, Tensura overworld): ${list.join('; ') || 'none'}`)
    return 1
  }

  var guildFacts = (s, p, field) => {
    var g = TtlGuild.read(p)
    TtlGuild.prune(s, g)
    var keys = Object.keys(g.taken)
    var readyCount = 0
    keys.forEach(k => {
      var b = TtlGuild.find(g.taken[k].id)
      if (b && TtlGuild.ready(p, g.taken[k], b)) readyCount++
    })
    var giver = /^giver_(.+)$/.exec(field)
    if (giver) {
      var gb = TtlGuild.find(giver[1])
      if (!gb) throw `unknown bounty ${giver[1]}`
      return TtlGuild.giverOf(gb)
    }
    var ti = /^turnin_(desk|fuze|any)_(.+)$/.exec(field)
    if (ti) {
      var tb = TtlGuild.find(ti[2])
      if (!tb) throw `unknown bounty ${ti[2]}`
      return TtlGuild.handsIn(tb, ti[1] === 'any' ? null : ti[1])
    }
    var tg = /^take_(desk|fuze)_(.+)$/.exec(field)
    if (tg) {
      try {
        TtlGuild.take(s, p, tg[2], tg[1])
        return 'allowed'
      } catch (e) {
        var text = String(e)
        return text === 'wrong_giver' ? 'wrong_giver' : text === 'Life 2 only' ? 'life2only' : /needs guild rank/.test(text) ? 'rank' : `other: ${text}`
      }
    }
    var dyn = /^(accepted|ready|rep|got)_(.+)$/.exec(field)
    if (dyn) {
      if (dyn[1] === 'rep') return typeof TtlRep === 'undefined' ? 'n/a' : String(TtlRep.get(p, dyn[2]))
      var found = keys.filter(k => g.taken[k].id === dyn[2])
      if (dyn[1] === 'accepted') return String(found.length > 0)
      if (dyn[1] === 'got') return found.length ? String(TtlGuild.progress(p, g.taken[found[0]], TtlGuild.find(dyn[2])).have) : 'none'

      return String(found.some(k => TtlGuild.ready(p, g.taken[k], TtlGuild.find(dyn[2]))))
    }
    var all = {
      points: () => String(g.points),
      done: () => String(g.done),
      rank: () => String(TtlGuild.rankOf(g).id),
      active: () => String(keys.length),
      ready: () => String(readyCount),
      board: () => String(TtlGuild.entries(s, 'desk').length),
      board_all: () => String(TtlGuild.entries(s).length),
      board_desk: () => String(TtlGuild.entries(s, 'desk').length),
      board_fuze: () => String(TtlGuild.entries(s, 'fuze').length),
      balance: () => String(TtlEcon.balance(p)),
      stage: () => {
        var on = TtlGuild.ranks().filter(r => p.stages.has(`ttl.guild.${String(r.id).toLowerCase()}`)).map(r => String(r.id))
        return on.length === 1 ? on[0] : on.length === 0 ? 'none' : on.join('+')
      },
      refuse_take: () => {
        try {
          TtlGuild.take(s, p, '1')
          return 'allowed'
        } catch (e) {
          return String(e) === 'Life 2 only' ? 'life2only' : `other: ${e}`
        }
      }
    }
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')}, accepted_<id>, ready_<id>, got_<id>, rep_<faction>, giver_<id>, take_<giver>_<id>)`
    return all[field]()
  }

  // ---- merit ----

  var meritShow = ctx => {
    var p = self(ctx)
    TtlGuild.requireLife2(p)
    TtlMerit.lines(server(ctx), p).forEach(l => say(ctx, l))
    return 1
  }

  var worksMark = ctx => {
    var r = TtlMerit.mark(server(ctx), self(ctx))
    say(ctx, `Public Works marked: ${r.key}${r.faction ? ` (${r.faction})` : ' (no faction region: merit pays no reputation here)'}`)
    return 1
  }

  var worksUnmark = ctx => {
    say(ctx, `Public Works released: ${TtlMerit.unmark(server(ctx), self(ctx))}`)
    return 1
  }

  var meritTest = counted => ctx => {
    var p = target(ctx)
    var n = counted ? num(ctx, 'n') : 1
    // Brigadier words cannot hold a colon, so `stone_bricks` means minecraft:stone_bricks (quote the id for other mods).
    var block = str(ctx, 'block')
    if (block.indexOf(':') < 0) block = `minecraft:${block}`
    var gain = 0
    for (var i = 0; i < n; i++) gain += TtlMerit.place(server(ctx), p, block, Math.floor(p.getX()), Math.floor(p.getZ()))
    say(ctx, `merit ${p.username}: +${gain}`)
    return 1
  }

  var meritReset = ctx => {
    var p = target(ctx)
    TtlMerit.reset(server(ctx), p)
    say(ctx, `merit ${p.username}: record cleared`)
    return 1
  }

  var meritFacts = (s, p, field) => {
    var m = TtlMerit.read(p)
    var me = TtlLife.uuid(p)
    var w = TtlMerit.works(s)
    var all = {
      total: () => String(m.total),
      week: () => String(m.week),
      works: () => String(Object.keys(w).filter(k => w[k].by === me).length),
      // The faction id the Public Works chunk under the player pays ('none': not marked, or no faction region).
      faction: () => {
        var x = Math.floor(p.getX())
        var z = Math.floor(p.getZ())
        var rec = w[TtlMerit.chunkKey(TtlLife.dimensionOf(p), x, z)]
        return (rec && TtlMerit.worksFaction(rec, x, z)) || 'none'
      },
      builder: () => String(p.stages.has('ttl.title.builder'))
    }
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')})`
    return all[field]()
  }

  // ---- econ ----

  var econReport = ctx => {
    TtlEcon.report(server(ctx)).forEach(l => say(ctx, l))
    return 1
  }

  var econGive = ctx => {
    var p = target(ctx)
    var n = TtlEcon.pay(server(ctx), p, num(ctx, 'n'), 'staff')
    say(ctx, `econ ${p.username}: paid ${n} bronze (${TtlEcon.text(n)})`)
    return 1
  }

  var econTake = ctx => {
    var p = target(ctx)
    var n = num(ctx, 'n')
    if (!TtlEcon.charge(server(ctx), p, n, 'staff')) throw `${p.username} cannot pay ${n} bronze (has ${TtlEcon.balance(p)})`
    say(ctx, `econ ${p.username}: took ${n} bronze`)
    return 1
  }

  var econFacts = (s, p, field) => {
    var data = TtlEcon.load(s)
    var can = /^can_(\d+)$/.exec(field)
    if (can) return String(TtlEcon.canPay(p, Number(can[1])))
    var fee = /^fee_(.+)$/.exec(field)
    if (fee) return String(TtlEcon.fee(fee[1]))
    var all = { balance: () => String(TtlEcon.balance(p)), source: () => TtlEcon.probe(p), faucet: () => String(data.faucet), sink: () => String(data.sink) }
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')}, fee_<name>, can_<bronze>)`
    return all[field]()
  }

  var expectOn = (label, facts) => ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = facts(server(ctx), p, field)
    if (got !== want) throw `${p.username}: expected ${label} ${field}=${want}, got ${got}`
    say(ctx, `${label} ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var expectTree = (label, facts) => Commands.literal('expect')
    .then(Commands.argument('target', Arguments.PLAYER.create(event))
      .then(Commands.argument('field', Arguments.STRING.create(event))
        .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expectOn(label, facts))))))

  var xyz = run => Commands.argument('x', Arguments.INTEGER.create(event))
    .then(Commands.argument('y', Arguments.INTEGER.create(event))
      .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(logged(run))))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('guild')
      .then(Commands.literal('board').executes(logged(board(false)))
        .then(Commands.argument('giver', Arguments.STRING.create(event)).executes(logged(board(true)))))
      .then(Commands.literal('take').then(Commands.argument('ref', Arguments.STRING.create(event)).executes(logged(take(false)))
        .then(Commands.argument('giver', Arguments.STRING.create(event)).executes(logged(take(true))))))
      .then(Commands.literal('turnin').executes(logged(turnin(false)))
        .then(Commands.argument('giver', Arguments.STRING.create(event)).executes(logged(turnin(true)))))
      .then(Commands.literal('abandon').then(Commands.argument('ref', Arguments.STRING.create(event)).executes(logged(abandon))))
      .then(Commands.literal('status').executes(logged(status)))
      .then(Commands.literal('roll').requires(ops)
        .executes(logged(roll(false)))
        .then(Commands.argument('which', Arguments.STRING.create(event)).executes(logged(roll(true)))))
      .then(Commands.literal('post').requires(ops)
        .then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(post))))
      .then(Commands.literal('sample').requires(ops)
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(sample))))
      .then(Commands.literal('test').requires(ops)
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('what', Arguments.STRING.create(event)).executes(logged(testHook)))))
      .then(Commands.literal('reset').requires(ops)
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(guildReset))))
      .then(Commands.literal('desk').requires(ops)
        .then(Commands.literal('add').then(xyz(desk(true))))
        .then(Commands.literal('remove').then(xyz(desk(false))))
        .then(Commands.literal('list').executes(logged(deskList))))
      .then(expectTree('guild', guildFacts).requires(ops)))
    .then(Commands.literal('merit')
      .executes(logged(meritShow))
      .then(Commands.literal('works')
        .then(Commands.literal('mark').executes(logged(worksMark)))
        .then(Commands.literal('unmark').executes(logged(worksUnmark))))
      .then(Commands.literal('test').requires(ops)
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('block', Arguments.STRING.create(event))
            .executes(logged(meritTest(false)))
            .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(meritTest(true)))))))
      .then(Commands.literal('reset').requires(ops)
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(meritReset))))
      .then(expectTree('merit', meritFacts).requires(ops)))
    .then(Commands.literal('econ').requires(ops)
      .executes(logged(econReport))
      .then(Commands.literal('give')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(econGive)))))
      .then(Commands.literal('take')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(econTake)))))
      .then(expectTree('econ', econFacts))))
})
