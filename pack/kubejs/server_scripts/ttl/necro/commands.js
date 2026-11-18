// priority: 60
// Necromancer rank, Church and licence commands (WP-N3; Brigadier merges them into the /ttl tree). API: necro/necro.js.
// The legion and tomb literals (raise, knight, stow, rouse, recall, stand, rest, muster, sanctum, legion …) are
// necro/legion_commands.js (WP-N2).
// Players: /ttl necro                                     who you are among the dead: rank, points, the Church's eye, licence
//          /ttl necro status                              the same
//          /ttl necro rank                                the rank ladder
//          /ttl necro rite [ash|dust]                     become a necromancer at your Bone Altar (a rite spell + the reagent)
//          /ttl necro licence                             the Church's licence (Honored, 14 clean days, in its lands)
//          /ttl necro bounties                            the Church's bounty list (Marked souls)
// Ops:     /ttl necro info <player>                       the record
//          /ttl necro points <player> add|set <n>         rank points (add goes through the weekly cap, set does not)
//          /ttl necro sense <player> add|set <n>          the Church's Sense (marks and the Hunt follow at once)
//          /ttl necro hunt <player> start|end             start the Holy Hunt on the soul now / end it
//          /ttl necro test <player> <what> [<n>]          test hooks: clean <days> (Sense 0 that long) | place <0|1> (licence
//                                                         place rule off) | continent <0|1|2> (auto|on|off for the Sense rule) |
//                                                         huntmins <n> (online minutes of the Hunt) | week (forget this week's
//                                                         points) | refresh | reset (forget everything necro of the soul)
//          /ttl necro expect <player> <field> <value>     test assertion: prints "ttl: ..." when it does not hold
//            fields: rank, title, points, week, entry (none|race|skill|rite), spells (rite spells known), aspirant (yes|no),
//                    race, rank4req (yes|no), try_rite, try_licence (ok or the refusal code), sense, marked, hunted, hunts,
//                    unbroken, licensed, licence_item (held), bounty (on the list), eye, stage_<stage suffix> (yes|no, e.g.
//                    stage_rank2, stage_marked), wildmult_<boss id>, guards_<faction> (yes|no), clean_days (whole days)
const TtlNecroCmd = {
  yesno(v) {
    return v ? 'yes' : 'no'
  },

  facts(server, p) {
    var N = TtlNecro
    delete N.cache[N.uid(p)]
    var r = N.refresh(server, p, 'expect')
    var now = Date.now()
    var out = {}
    out.rank = String(r.rank)
    out.title = N.title(p) || 'none'
    out.points = String(r.points)
    out.week = String(r.wk === N.weekKey() ? r.week : 0)
    out.entry = r.entry ? String(r.entry.how) : 'none'
    out.spells = String(N.riteSpells(server, p).length)
    out.aspirant = this.yesno(N.aspirant(p))
    out.race = N.race(p) || 'none'
    out.rank4req = this.yesno(N.needsMet(p, N.rankDef(4) || {}))
    out.try_rite = N.riteRefusal(server, p, '') || 'ok'
    out.try_licence = N.licenceRefusal(server, p) || 'ok'
    out.sense = String(r.sense)
    out.marked = this.yesno(!!r.marked)
    out.hunted = this.yesno(N.hunting(r, now))
    out.hunts = String(r.hunts || 0)
    out.unbroken = this.yesno(N.hasTitle(p, String(N.part('hunt').survive_title || 'Unbroken')))
    out.licensed = this.yesno(!!r.licensed)
    out.licence_item = String(TtlCmd.run(server, `clear ${p.username} ${N.part('licence').item || 'ttl:exorcist_licence'} 0`))
    out.bounty = this.yesno(N.bounties(server).some(b => b.uuid === N.uid(p)))
    out.eye = N.eye(r, now).split(':')[0].toLowerCase()
    out.clean_days = String(Math.floor(N.cleanDays(r, now)))
    return out
  },

  field(server, p, field) {
    var f = this.facts(server, p)
    if (field in f) return f[field]
    var m = /^stage_(.+)$/.exec(field)
    if (m) return this.yesno(p.stages.has(`ttl.necro.${m[1]}`) || p.stages.has(`ttl.${m[1]}`))
    m = /^wildmult_(.+)$/.exec(field)
    if (m) return String(TtlNecro.wildMult({ id: m[1] }, p))
    m = /^guards_(.+)$/.exec(field)
    if (m) {
      TtlNecro.bandCache = {}
      return this.yesno(TtlNecro.guardsHostile(p, m[1]))
    }
    throw `unknown field ${field} (one of ${Object.keys(f).join(', ')}, stage_<x>, wildmult_<boss>, guards_<faction>)`
  },

  report(player, res) {
    if (!res.ok) player.tell(Text.gray(TtlNecro.why(res.why)))
    return res.ok ? 1 : 0
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] necro command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var me = ctx => ctx.source.getPlayerOrException()
  var srv = ctx => ctx.source.getServer()
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))

  var status = ctx => {
    var p = me(ctx)
    TtlNecro.lines(srv(ctx), p).forEach((l, i) => p.tell(i === 0 ? Text.darkPurple(l) : Text.gray(l)))
    p.tell(Text.gray('/ttl necro rank · /ttl necro legion · /ttl guide paths'))
    return 1
  }
  var rank = ctx => {
    var p = me(ctx)
    TtlNecro.refresh(srv(ctx), p, 'rank')
    p.tell(Text.darkPurple('The ranks of the dead (points come from raising, naming, tombs and laying the dead to rest):'))
    TtlNecro.ladder(p).forEach(l => p.tell(Text.gray(l)))
    return 1
  }
  var rite = hasPay => ctx => {
    var p = me(ctx)
    return TtlNecroCmd.report(p, TtlNecro.rite(srv(ctx), p, hasPay ? str(ctx, 'pay') : ''))
  }
  var licence = ctx => {
    var p = me(ctx)
    return TtlNecroCmd.report(p, TtlNecro.licence(srv(ctx), p))
  }
  var bounties = ctx => {
    var list = TtlNecro.bounties(srv(ctx))
    if (list.length === 0) say(ctx, 'The Church has no bounty on any soul.')
    else list.forEach(b => say(ctx, `The Church's bounty: ${b.name}, marked ${Math.max(0, Math.floor((Date.now() - b.at) / 86400000))} days ago.`))
    return 1
  }

  // ---- ops ----
  var info = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var f = TtlNecroCmd.facts(server, p)
    say(ctx, `necro ${p.username}: ${Object.keys(f).sort().map(k => `${k}=${f[k]}`).join(' ')}`)
    say(ctx, `necro ${p.username}: ${String(p.persistentData.getString(TtlNecro.KEY))}`)
    return 1
  }
  var points = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var how = str(ctx, 'how')
    var n = num(ctx, 'n')
    if (how === 'add') {
      var paid = TtlNecro.addPoints(server, p, n, 'ops')
      say(ctx, `necro ${p.username}: +${paid} points (of ${n})`)
    } else if (how === 'set') {
      var r = TtlNecro.setPoints(server, p, n)
      say(ctx, `necro ${p.username}: points ${r.points}, rank ${r.rank}`)
    } else {
      throw 'add or set'
    }
    return 1
  }
  var sense = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var how = str(ctx, 'how')
    var n = num(ctx, 'n')
    var v
    if (how === 'add') v = TtlNecro.addSense(server, p, n, 'ops')
    else if (how === 'set') v = TtlNecro.setSense(server, p, n, 'ops')
    else throw 'add or set'
    say(ctx, `necro ${p.username}: Sense ${v}`)
    return 1
  }
  var hunt = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var how = str(ctx, 'how')
    if (how === 'start') {
      say(ctx, TtlNecro.startHunt(server, p, 'ops') ? `necro ${p.username}: the Hunt is on` : `necro ${p.username}: already hunted`)
    } else if (how === 'end') {
      var r = TtlNecro.read(p)
      TtlNecro.endHunt(server, p, r, 'ops')
      TtlNecro.write(p, r)
      TtlNecro.sync(server, p, r)
      say(ctx, `necro ${p.username}: the Hunt is over`)
    } else {
      throw 'start or end'
    }
    return 1
  }
  var test = hasN => ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var what = str(ctx, 'what')
    var n = hasN ? num(ctx, 'n') : 0
    var data = p.persistentData
    var r
    if (what === 'clean') {
      r = TtlNecro.read(p)
      TtlNecro.decay(r, Date.now())
      if (r.sense > 0) throw `${p.username} still has Sense ${r.sense}`
      r.zeroAt = Date.now() - n * TtlNecro.DAY_MS - 60000
      TtlNecro.write(p, r)
    } else if (what === 'place') {
      if (n) data.putBoolean(TtlNecro.TESTPLACE, true)
      else data.remove(TtlNecro.TESTPLACE)
    } else if (what === 'continent') {
      if (n === 1 || n === 2) data.putInt(TtlNecro.TESTINSIDE, n)
      else data.remove(TtlNecro.TESTINSIDE)
    } else if (what === 'huntmins') {
      r = TtlNecro.read(p)
      if (!TtlNecro.hunting(r, Date.now())) throw `${p.username} is not hunted`
      r.hunt.mins = n
      r.hunt.tick = Date.now()
      TtlNecro.checkUnbroken(server, p, r)
      TtlNecro.write(p, r)
    } else if (what === 'week') {
      r = TtlNecro.read(p)
      r.week = 0
      r.wk = ''
      TtlNecro.write(p, r)
    } else if (what === 'refresh') {
      TtlNecro.refresh(server, p, 'ops')
    } else if (what === 'reset') {
      TtlNecro.clear(server, p)
    } else {
      throw 'test hooks: clean <days>, place <0|1>, continent <0|1|2>, huntmins <n>, week, refresh, reset'
    }
    say(ctx, `necro ${p.username}: ${what}${hasN ? ` ${n}` : ''}`)
    return 1
  }
  var expect = ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlNecroCmd.field(srv(ctx), p, field)
    if (got !== want) throw `${p.username}: expected ${field}=${want}, got ${got}`
    say(ctx, `necro ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var op = src => src.hasPermission(2)
  var who = (lit, then) => Commands.literal(lit).requires(op).then(Commands.argument('target', Arguments.PLAYER.create(event)).then(then))
  event.register(Commands.literal('ttl')
    .then(Commands.literal('necro')
      .executes(logged(status))
      .then(Commands.literal('status').executes(logged(status)))
      .then(Commands.literal('rank').executes(logged(rank)))
      .then(Commands.literal('rite')
        .executes(logged(rite(false)))
        .then(Commands.argument('pay', Arguments.STRING.create(event)).executes(logged(rite(true)))))
      .then(Commands.literal('licence').executes(logged(licence)))
      .then(Commands.literal('license').executes(logged(licence)))
      .then(Commands.literal('bounties').executes(logged(bounties)))
      .then(Commands.literal('info').requires(op)
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(info))))
      .then(who('points', Commands.argument('how', Arguments.STRING.create(event))
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(points)))))
      .then(who('sense', Commands.argument('how', Arguments.STRING.create(event))
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(sense)))))
      .then(who('hunt', Commands.argument('how', Arguments.STRING.create(event)).executes(logged(hunt))))
      .then(who('test', Commands.argument('what', Arguments.STRING.create(event))
        .executes(logged(test(false)))
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(test(true))))))
      .then(who('expect', Commands.argument('field', Arguments.STRING.create(event))
        .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect)))))))
})
