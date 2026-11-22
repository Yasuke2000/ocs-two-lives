// Life 1 status for staff and testers (issue #75: "a command to up the first life status, to test if the feature works").
// The Life 1 "status" is the karma verdict the Life screen and `/ttl life` show: the tier (Wanderer, Survivor, Hero,
// Legend), Dark or not, and the days survived. Living a Legend's life to test the Legend offers takes ~10 hours, so a
// preset of design/data/karma.toml [presets] sets the Life 1 stats that reach a tier (karma/karma.js TtlKarma.set, the
// same stats as `/ttl karma <p> set`), and the command checks the live preview gives that tier.
// Ops only (permission 2). Every use is logged ([ttl] life1 status ...) and stamped on the soul (`ttl.l1.staffset`:
// JSON {by, preset, at}; kept through the rebirth so the verdict shows it was staff-set, cleared by the next Life 1 start
// with the other karma keys, TtlKarma.KEYS), and the staff command feed (ops/cmdlog.js, prefix "ttl")
// posts it to the staff channel. Only a soul in Life 1 can be changed: Life 2 karma was judged at death.
//   /ttl life1 status <player>              phase, tier preview, score, days, Dark, and a staff stamp if any
//   /ttl life1 status <player> <preset>     underdog | normal | elite | legendary | dark (see karma.toml)
//   /ttl life1 days <player> <n>            the days survived (Life 1 play time = n x ticks_per_day), the rest unchanged
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

  stamp(player, by, what) {
    player.persistentData.putString(this.KEY, JSON.stringify({ by: by, preset: what, at: Date.now() }))
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
    console.info(`[ttl] life1 status: ${by} set ${player.username} to ${n} days survived`)
    return TtlKarma.current(server, player)
  },

  describe(server, player) {
    var v = TtlKarma.current(server, player)
    var phase = TtlLife.phase(player) || 'none'
    var raw = String(player.persistentData.getString(this.KEY))
    var staff = ''
    if (raw) {
      try {
        var s = JSON.parse(raw)
        staff = ` [staff: ${s.preset} by ${s.by}]`
      } catch (e) {
        staff = ' [staff stamp unreadable]'
      }
    }
    if (!v) return `life1 ${player.username}: phase=${phase}, no Life 1 record${staff}`
    var title = typeof TtlKarmaView !== 'undefined' ? TtlKarmaView.title(v) : v.tier
    return `life1 ${player.username}: phase=${phase} tier=${v.tier} (${title})${v.preview ? ' preview' : ''} score=${v.score} days=${v.days} bosses=${v.bosses} dark=${v.dark}${staff}`
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
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(days)))))))
})
