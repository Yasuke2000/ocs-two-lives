// Life 1 status for staff and testers (issue #75: "a command to up the first life status, to test if the feature works").
// The Life 1 "status" is the karma verdict the Life screen and `/ttl life` show: the tier (Wanderer, Survivor, Hero,
// Legend), Dark or not, and the days survived. Living a Legend's life to test the Legend offers takes ~10 hours, so a
// preset of design/data/karma.toml [presets] sets the Life 1 stats that reach a tier (karma/karma.js TtlKarma.set, the
// same stats as `/ttl karma <p> set`), and the command checks the live preview gives that tier.
// The gates of Life 1 progression (karma.toml [[tiers]]): a tier needs min_score, min_days (days of ACTIVE play: idle time
// and tick-speed tricks do not count, so a Legend's 30 days are ~10 real hours of play) and min_bosses; the Legend pick of
// a Legendary unique needs the legendary tier (skills.toml [legend_pick]). In the Corridor the Trial of the Soul decides
// 1-of-3 uniques (passed) or a random one; the Last Wish itself has no gate (any wish, /ttl wish).
// Ops only (permission 2), never a player command. Every use is logged ([ttl] life1 ...) and stamped on the soul
// (`ttl.l1.staffset`: JSON list of {by, what, at}, the last 10; kept through the rebirth so the verdict shows it was
// staff-set, cleared by the next Life 1 start with the other karma keys, TtlKarma.KEYS), and the staff command feed
// (ops/cmdlog.js, prefix "ttl") posts it to the staff channel.
//   /ttl life1 status <player>              phase, tier preview, score, active days, Dark, what each higher tier still
//                                           needs, the Corridor step and Trial, staff stamps
//   /ttl life1 status <player> <preset>     underdog | normal | elite | legendary | dark (see karma.toml): Life 1 only
//   /ttl life1 days <player> <n>            the days of active play (Life 1 play time = n x ticks_per_day): Life 1 only
//   /ttl life1 trial <player> <pass|fail>   the Trial of the Soul's result, in the Corridor after the Last Wish (a running
//                                           Trial is ended with that result)
const TtlLife1Status = {
  KEY: 'ttl.l1.staffset',

  presets() {
    return (TtlData.karma && TtlData.karma.presets) || {}
  },

  // Every stat any preset names: zeroed first, so presets can follow each other in any order.
  presetStats() {
    var all = {}
    var presets = this.presets()
    Object.keys(presets).forEach(n => Object.keys(presets[n].stats || {}).forEach(k => { all[k] = true }))
    return Object.keys(all).sort()
  },

  stamps(player) {
    var raw = String(player.persistentData.getString(this.KEY))
    if (!raw) return []
    try {
      var v = JSON.parse(raw)
      return Array.isArray(v) ? v : [{ by: v.by, what: v.preset || v.what, at: v.at }]
    } catch (e) {
      return []
    }
  },

  stamp(player, by, what) {
    var list = this.stamps(player).concat([{ by: by, what: what, at: Date.now() }]).slice(-10)
    player.persistentData.putString(this.KEY, JSON.stringify(list))
  },

  // What each tier above the verdict's still needs: [{tier, title, missing: ['score 671/1000', ...]}] (empty = reached).
  gates(v) {
    var out = []
    var at = TtlKarma.tierIndex(v.tier)
    TtlKarma.tiers().forEach((t, i) => {
      if (i <= at) return
      var missing = []
      if (v.score < (t.min_score || 0)) missing.push(`score ${v.score}/${t.min_score}`)
      if (v.days < (t.min_days || 0)) missing.push(`active days ${v.days}/${t.min_days}`)
      if (v.bosses < (t.min_bosses || 0)) missing.push(`major bosses ${v.bosses}/${t.min_bosses}`)
      out.push({ tier: t.id, title: t.title, missing: missing })
    })
    return out
  },

  // The Trial of the Soul's result, set by staff. The soul must be in the Corridor with its Last Wish made.
  trial(server, player, passed, by) {
    if (TtlLife.phase(player) !== 'corridor') throw `${player.username} is not in the Spirit Corridor (${TtlLife.phase(player) || 'no life'})`
    var data = player.persistentData
    var step = String(data.getString('ttl.step'))
    var done = data.getBoolean('ttl.trial.done')
    if (step === 'trial') {
      TtlTrial.finish(server, player, String(data.getString('ttl.wish')), passed, `set by ${by}`)
    } else if (step === 'race' && !done) {
      data.putBoolean('ttl.trial.done', true)
      data.putBoolean('ttl.trial.passed', passed)
    } else {
      throw `${player.username} is at step ${step || 'none'}${done ? ' with the Trial done' : ''}: the Trial result is set after the Last Wish, before the race`
    }
    this.stamp(player, by, `trial ${passed ? 'pass' : 'fail'}`)
    console.info(`[ttl] life1 trial: ${by} set the Trial of ${player.username} to ${passed ? 'passed' : 'failed'}`)
  },

  // Applies a preset; returns the live verdict. Throws when the soul is not in Life 1 or the verdict misses the preset.
  apply(server, player, name, by) {
    var p = this.presets()[name]
    if (!p) throw `unknown preset ${name} (one of ${Object.keys(this.presets()).join(', ')})`
    if (TtlLife.phase(player) !== 'life1') throw `${player.username} is not in Life 1 (${TtlLife.phase(player) || 'no life'}); karma was judged at death`
    this.presetStats().forEach(k => TtlKarma.set(server, player, k, 0))
    var stats = p.stats || {}
    Object.keys(stats).forEach(k => TtlKarma.set(server, player, k, Number(stats[k])))
    this.stamp(player, by, name)
    var v = TtlKarma.current(server, player)
    console.info(`[ttl] life1 status: ${by} set ${player.username} to preset ${name} -> tier ${v ? v.tier : '?'}${v && v.dark ? ' (dark)' : ''}`)
    if (!v || v.tier !== p.tier || !!v.dark !== !!p.dark) {
      throw `preset ${name} gave tier ${v ? v.tier : '?'}${v && v.dark ? ' (dark)' : ''}, expected ${p.tier}${p.dark ? ' (dark)' : ''}: karma.toml [presets.${name}] is out of date`
    }
    return v
  },

  days(server, player, n, by) {
    if (TtlLife.phase(player) !== 'life1') throw `${player.username} is not in Life 1 (${TtlLife.phase(player) || 'no life'})`
    TtlKarma.set(server, player, 'play_time', n * Number(TtlData.karma.ticks_per_day))
    this.stamp(player, by, `days ${n}`)
    console.info(`[ttl] life1 days: ${by} set ${player.username} to ${n} days of active play`)
    return TtlKarma.current(server, player)
  },

  describe(server, player) {
    var v = TtlKarma.current(server, player)
    var phase = TtlLife.phase(player) || 'none'
    var st = this.stamps(player)
    var staff = st.length ? ` [staff: ${st.map(x => `${x.what} by ${x.by}`).join('; ')}]` : ''
    if (!v) return `life1 ${player.username}: phase=${phase}, no Life 1 record${staff}`
    var title = typeof TtlKarmaView !== 'undefined' ? TtlKarmaView.title(v) : v.tier
    var line = `life1 ${player.username}: phase=${phase} tier=${v.tier} (${title})${v.preview ? ' preview' : ''} score=${v.score} active days=${v.days} bosses=${v.bosses} dark=${v.dark}`
    var next = this.gates(v).map(g => `${g.tier}: ${g.missing.length ? g.missing.join(', ') : 'reached'}`)
    if (next.length) line += ` | next: ${next.join(' / ')}`
    if (phase === 'corridor') {
      var data = player.persistentData
      var trial = data.getBoolean('ttl.trial.done') ? (data.getBoolean('ttl.trial.passed') ? 'passed' : 'failed') : 'not done'
      line += ` | step=${data.getString('ttl.step') || 'none'} wish=${data.getString('ttl.wish') || 'none'} trial=${trial}`
    }
    return line + staff
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] life1 command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var actor = ctx => {
    var p = ctx.source.getPlayer()
    return p ? String(p.getGameProfile().getName()) : String(ctx.source.getTextName())
  }

  var show = ctx => {
    say(ctx, TtlLife1Status.describe(ctx.source.getServer(), target(ctx)))
    return 1
  }
  var preset = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    TtlLife1Status.apply(server, p, String(Arguments.STRING.getResult(ctx, 'preset')).toLowerCase(), actor(ctx))
    say(ctx, TtlLife1Status.describe(server, p))
    return 1
  }
  var days = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    if (n < 0) throw 'days must be 0 or more'
    TtlLife1Status.days(server, p, n, actor(ctx))
    say(ctx, TtlLife1Status.describe(server, p))
    return 1
  }
  var trial = passed => ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    TtlLife1Status.trial(server, p, passed, actor(ctx))
    say(ctx, TtlLife1Status.describe(server, p))
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('life1')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('status')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .executes(logged(show))
          .then(Commands.argument('preset', Arguments.STRING.create(event))
            .suggests((ctx, builder) => {
              Object.keys(TtlLife1Status.presets()).forEach(n => builder.suggest(n))
              return builder.buildFuture()
            })
            .executes(logged(preset)))))
      .then(Commands.literal('days')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(days)))))
      .then(Commands.literal('trial')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.literal('pass').executes(logged(trial(true))))
          .then(Commands.literal('fail').executes(logged(trial(false))))))))
})
