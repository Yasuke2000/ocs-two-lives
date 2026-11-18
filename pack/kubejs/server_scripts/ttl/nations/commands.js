// priority: 60
// Nation commands (Brigadier merges these into the /ttl tree from commands.js). API: nations.js, claims.js.
// A nation is an FTB party: create and fill it with /ftbteams party create|invite|join|leave|kick, then the owner founds it.
// Players (a name with spaces goes in quotes):
//   /ttl nation                         your nation: rank, value, members, land, treasury, allies, wars
//   /ttl nation found <name>            the party owner, Life 2, in the overworld, with the boss stage and the charter fee
//   /ttl nation dissolve                the owner ends the nation (treasury paid back); the party stays
//   /ttl nation info [<name>]           your nation, or any nation by name
//   /ttl nation top                     all nations by value
//   /ttl nation value                   what you are worth (renown) and what your nation is worth
//   /ttl nation deposit <coin> <n>      pay n coins (bronze|silver|gold|stellar) into the treasury
//   /ttl nation withdraw <coin> <n>     the owner takes coins out
//   /ttl nation ally <name>             offer an alliance (mutual once the other owner does the same) · unally <name>
//   /ttl nation war <name>              declare war (counts after diplomacy.war_notice_hours) · peace <name> ends it
// Ops:
//   /ttl nation sync                    reconcile with FTB Teams now (stages, claim allowance, disbanded parties)
//   /ttl nation test <player> life2|nolife2|boss1|noboss1|leaveparty|drop|warnow|upkeep|clearextra   test hooks
//        leaveparty the player leaves their FTB party (silently; an owner with members cannot)
//        life2/nolife2 the Life 2 stage · boss1/noboss1 the stage rules.charter_stage · drop forget the player's nation
//        record (the party stays) · warnow make every war of the player's nation active · upkeep run this week's upkeep
//        now · clearextra remove the extra claim chunks we gave the player
//   /ttl nation expect <player> <field> <value>   "ttl: ..." when it does not hold. Numeric fields also accept <field>_min and
//        <field>_max. Fields: member, owner (yes|no), name, rank, rankstage_<id> (yes|no), members, value, chunks, builds,
//        treasury (bronze), owed, home (faction id | none), claims (chunks the player's team claimed), maxclaims (its limit),
//        extra (the extra chunks FTB Chunks reports for the player), score (scoreboard ttl.nation.value), nations (how many
//        exist), ally_<name> (yes|no), war_<name> (none|pending|active), life2 (yes|no)
//        try_found_<name>, try_war_<name> and try_withdraw_<coin>_<n> run the real action as the player and answer ok (it went
//        through, for real) or what refused it: life2only, overworld, noparty, notowner, exists, members, stage, name, fee,
//        funds, allied, war, other: ...
//        claims = chunks claimed by the player's team of the moment (the party's, or their own when in no party)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] nations command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var ops = src => src.hasPermission(2)
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var self = ctx => ctx.source.getPlayerOrException()
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var server = ctx => ctx.source.getServer()

  var info = byName => ctx => {
    var s = server(ctx)
    var key
    if (byName) key = TtlNations.find(s, str(ctx, 'name')).key
    else {
      var n = TtlNations.of(s, self(ctx))
      if (!n) {
        say(ctx, 'You are in no nation. Make a party (/ftbteams party create <name>), invite your people and found it: /ttl nation found <name>.')
        return 1
      }
      key = n.key
    }
    TtlNations.lines(s, key).forEach(l => say(ctx, l))
    return 1
  }

  var found = ctx => {
    var p = self(ctx)
    var rec = TtlNations.found(server(ctx), p, str(ctx, 'name'))
    say(ctx, `${rec.name} is founded. Check it with /ttl nation.`)
    return 1
  }

  var dissolve = ctx => {
    var back = TtlNations.dissolve(server(ctx), self(ctx))
    say(ctx, `The nation is dissolved.${back > 0 ? ` The treasury paid back ${TtlEcon.text(back)}.` : ''}`)
    return 1
  }

  var top = ctx => {
    var lines = TtlNations.top(server(ctx))
    say(ctx, lines.length ? 'Nations by value:' : 'No nation has been founded yet.')
    lines.forEach(l => say(ctx, `  ${l}`))
    return 1
  }

  var value = ctx => {
    var s = server(ctx)
    var p = self(ctx)
    if (typeof TtlRep !== 'undefined') say(ctx, `Your renown: ${TtlRep.renown(s, p)} (/ttl rep renown shows where it comes from)`)
    var n = TtlNations.of(s, p)
    if (!n) {
      say(ctx, 'You are in no nation.')
      return 1
    }
    var parts = TtlNations.value(s, n.key)
    var rec = TtlNations.all(s)[n.key]
    say(ctx, `${rec.name} is worth ${parts.total}: members' renown ${parts.members} + chunks ${parts.chunks} + builds ${parts.builds} + treasury ${parts.treasury}`)
    return 1
  }

  var deposit = ctx => {
    var left = TtlNations.deposit(server(ctx), self(ctx), str(ctx, 'coin'), num(ctx, 'n'))
    say(ctx, `Paid in. The treasury holds ${TtlEcon.text(left)}.`)
    return 1
  }

  var withdraw = ctx => {
    var left = TtlNations.withdraw(server(ctx), self(ctx), str(ctx, 'coin'), num(ctx, 'n'))
    say(ctx, `Taken out. The treasury holds ${TtlEcon.text(left)}.`)
    return 1
  }

  var ally = ctx => {
    var r = TtlNations.ally(server(ctx), self(ctx), str(ctx, 'name'))
    say(ctx, r === 'allied' ? 'You are allies now.' : 'The offer is made; the alliance holds once the other owner offers the same.')
    return 1
  }

  var unally = ctx => {
    TtlNations.unally(server(ctx), self(ctx), str(ctx, 'name'))
    say(ctx, 'Your side of the alliance is withdrawn.')
    return 1
  }

  var war = ctx => {
    var h = TtlNations.declareWar(server(ctx), self(ctx), str(ctx, 'name'))
    say(ctx, h > 0 ? `War is declared; it begins in ${h} hours.` : 'War is declared.')
    return 1
  }

  var peace = ctx => {
    TtlNations.endWar(server(ctx), self(ctx), str(ctx, 'name'))
    say(ctx, 'Peace.')
    return 1
  }

  var sync = ctx => {
    TtlNations.syncAll(server(ctx))
    var s = server(ctx)
    Object.keys(TtlNations.all(s)).forEach(k => TtlNations.value(s, k))
    say(ctx, `nations: synced, ${Object.keys(TtlNations.all(s)).length} nation(s)`)
    return 1
  }

  // ---- ops: test hooks ----

  var test = ctx => {
    var s = server(ctx)
    var p = target(ctx)
    var what = str(ctx, 'what').toLowerCase()
    var stage = String(TtlNations.rules().charter_stage)
    if (what === 'life2') TtlNations.stage(p, 'ttl.life2', true)
    else if (what === 'nolife2') TtlNations.stage(p, 'ttl.life2', false)
    else if (what === 'boss1') TtlNations.stage(p, stage, true)
    else if (what === 'noboss1') TtlNations.stage(p, stage, false)
    else if (what === 'leaveparty') TtlCmd.runAs(p, "ftbteams party leave")
    else if (what === 'drop') {
      var team = TtlNations.partyOf(p)
      var all = TtlNations.all(s)
      var key = team ? TtlNations.keyOf(team) : null
      if (key && all[key]) {
        TtlNations.dropRecord(s, all, key, 'test hook')
        TtlNations.save(s, all)
      }
      TtlNations.syncAll(s)
    } else if (what === 'warnow') {
      var n = TtlNations.require(s, p)
      var map = TtlNations.all(s)
      ;(map[n.key].wars || []).forEach(w => {
        w.active_at = Date.now() - 1000
        var other = map[w.with]
        if (other) (other.wars || []).forEach(o => { if (o.with === n.key) o.active_at = w.active_at })
      })
      TtlNations.save(s, map)
    } else if (what === 'upkeep') {
      var m = TtlNations.require(s, p)
      var recs = TtlNations.all(s)
      recs[m.key].upkeepWeek = '2000-01-03'
      TtlNations.save(s, recs)
      TtlNations.upkeep(s, m.key)
    } else if (what === 'clearextra') {
      TtlNationClaims.apply(s, p, null)
    } else {
      throw 'test hooks: life2, nolife2, boss1, noboss1, leaveparty, drop, warnow, upkeep, clearextra'
    }
    say(ctx, `nations ${p.username}: test hook ${what} done`)
    return 1
  }

  // ---- ops: expect ----

  var yes = b => (b ? 'yes' : 'no')

  var refusal = text => {
    if (/Life 2/.test(text)) return 'life2only'
    if (/overworld/.test(text)) return 'overworld'
    if (/no party/.test(text)) return 'noparty'
    if (/only the owner/.test(text)) return 'notowner'
    if (/already/.test(text)) return 'exists'
    if (/at least \d+ members/.test(text)) return 'members'
    if (/needs the stage/.test(text)) return 'stage'
    if (/nation name|is taken/.test(text)) return 'name'
    if (/charter costs/.test(text)) return 'fee'
    if (/treasury holds/.test(text)) return 'funds'
    if (/is your ally/.test(text)) return 'allied'
    if (/already is a war|no war/.test(text)) return 'war'
    return `other: ${text}`
  }

  // The real action, as the player; the answer is "ok" or the reason it was refused.
  var attempt = (s, p, field) => {
    try {
      if (field.indexOf('try_found_') === 0) TtlNations.found(s, p, field.slice(10))
      else if (field.indexOf('try_war_') === 0) TtlNations.declareWar(s, p, field.slice(8))
      else if (field.indexOf('try_withdraw_') === 0) {
        var bits = field.slice(13).split('_')
        TtlNations.withdraw(s, p, bits[0], Number(bits[1]))
      } else throw `unknown nation field ${field}`
      return 'ok'
    } catch (e) {
      return refusal(String(e))
    }
  }

  // The value of one expect field for a player, as a string.
  var read = (s, p, field) => {
    var n = TtlNations.of(s, p)
    var rec = n ? TtlNations.all(s)[n.key] : null
    var parts = function () {
      return n ? TtlNations.value(s, n.key) : null
    }
    if (field.indexOf('try_') === 0) return attempt(s, p, field)
    if (field === 'life2') return yes(TtlLife.phase(p) === 'life2')
    if (field === 'member') return yes(!!n)
    if (field === 'owner') return yes(!!n && String(n.team.getOwner()) === TtlLife.uuid(p) && p.stages.has('ttl.nation.owner'))
    if (field === 'nations') return String(Object.keys(TtlNations.all(s)).length)
    if (field === 'claims') {
      var team = TtlNations.teamOf(p)
      return String(team ? TtlNationClaims.count(team) : 0)
    }
    if (field === 'maxclaims') {
      var t = TtlNations.teamOf(p)
      return String(t ? TtlNationClaims.max(t) : -1)
    }
    if (field === 'extra') return String(TtlNationClaims.extraOf(p))
    if (field === 'score') {
      var board = s.getScoreboard()
      var obj = board.getObjective('ttl.nation.value')
      var score = obj ? board.getPlayerScoreInfo(p, obj) : null
      return score ? String(score.value()) : 'none'
    }
    if (field.indexOf('rankstage_') === 0) return yes(p.stages.has(`ttl.nation.rank.${field.slice(10)}`))
    if (field.indexOf('ally_') === 0) {
      var a = TtlNations.byName(s, field.slice(5))
      return yes(!!n && !!a && TtlNations.allied(s, n.key, a.key))
    }
    if (field.indexOf('war_') === 0) {
      var w = TtlNations.byName(s, field.slice(4))
      return n && w ? TtlNations.warState(s, n.key, w.key) : 'none'
    }
    if (!rec) return field === 'name' || field === 'rank' || field === 'home' ? 'none' : '0'
    if (field === 'name') return String(rec.name)
    if (field === 'rank') {
      parts()
      return String(TtlNations.all(s)[n.key].rank)
    }
    if (field === 'home') return rec.home ? String(rec.home) : 'none'
    if (field === 'members') return String(TtlNations.memberIdsOf(n.team).length)
    if (field === 'value') return String(parts().total)
    if (field === 'chunks') return String(parts().chunks)
    if (field === 'builds') return String(parts().builds)
    if (field === 'treasury') return String(Number(rec.treasury || 0))
    if (field === 'owed') return String(Number(rec.owed || 0))
    throw `unknown nation field ${field}`
  }

  var expect = ctx => {
    var s = server(ctx)
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var bound = /_(min|max)$/.test(field) && field.indexOf('rankstage_') !== 0 && field.indexOf('ally_') !== 0 && field.indexOf('war_') !== 0
    var base = bound ? field.replace(/_(min|max)$/, '') : field
    var got = read(s, p, base)
    var who = `${p.username} nation ${field}`
    if (bound) {
      var n = Number(want)
      var g = Number(got)
      if (isNaN(n) || isNaN(g)) throw `${who}: ${base} is not a number (got ${got}, wanted ${want})`
      if (/_min$/.test(field) ? g < n : g > n) throw `${who}: expected ${/_min$/.test(field) ? 'at least' : 'at most'} ${n}, got ${g}`
    } else if (got !== want) {
      throw `${who}: expected ${want}, got ${got}`
    }
    say(ctx, `nations ${who}: ${want} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var nameArg = () => Commands.argument('name', Arguments.STRING.create(event))
  var coinArg = () => Commands.argument('coin', Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('nation')
      .executes(logged(info(false)))
      .then(Commands.literal('info').executes(logged(info(false))).then(nameArg().executes(logged(info(true)))))
      .then(Commands.literal('found').then(nameArg().executes(logged(found))))
      .then(Commands.literal('dissolve').executes(logged(dissolve)))
      .then(Commands.literal('top').executes(logged(top)))
      .then(Commands.literal('value').executes(logged(value)))
      .then(Commands.literal('deposit').then(coinArg().then(intArg('n').executes(logged(deposit)))))
      .then(Commands.literal('withdraw').then(coinArg().then(intArg('n').executes(logged(withdraw)))))
      .then(Commands.literal('ally').then(nameArg().executes(logged(ally))))
      .then(Commands.literal('unally').then(nameArg().executes(logged(unally))))
      .then(Commands.literal('war').then(nameArg().executes(logged(war))))
      .then(Commands.literal('peace').then(nameArg().executes(logged(peace))))
      .then(Commands.literal('sync').requires(ops).executes(logged(sync)))
      .then(Commands.literal('test').requires(ops)
        .then(playerArg().then(Commands.argument('what', Arguments.STRING.create(event)).executes(logged(test)))))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(Commands.argument('field', Arguments.STRING.create(event))
          .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))))
})
