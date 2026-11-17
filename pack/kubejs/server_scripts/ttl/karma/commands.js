// Karma v1 commands (Brigadier merges these into the /ttl tree from commands.js).
// Players: /ttl life                                  the Life screen: what your first life earned
// Ops:     /ttl karma <player>                        stats, axes, score and tier (a live preview in Life 1)
//          /ttl karma <player> set <stat> <n>          make a Life 1 stat exactly n (bot tests, admin fixes)
//          /ttl karma <player> expect <field> <value>  test assertion: prints "ttl: ..." when it does not hold
//            fields: tier, dark, days, bosses, offers (count), darkoffer (true when an offer is a dark race),
//                    step (Corridor step), phase, bonus (count of karma bonus skills granted)
//          /ttl karma <player> odds <wish>             400 trial draws from the wish's pool with the player's tier
//                                                      weights; "ttl: ..." when the rare share is off by > 10 points
//          /ttl karma <player> pick                    test hook: take the first unique option at the unique step
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  // Same as commands.js: Brigadier hides script errors, so log them and answer with "ttl: <error>".
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] karma command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))

  var show = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var v = TtlKarma.current(server, target)
    if (!v) {
      say(ctx, `karma ${target.username}: no Life 1 record (default tier ${TtlData.karma.default_tier})`)
      return 1
    }
    var deeds = v.deeds || {}
    say(ctx, `karma ${target.username}${v.preview ? ' (Life 1 preview)' : ''}: tier=${v.tier} (${TtlKarmaView.title(v)}) score=${v.score} dark=${v.dark} days=${v.days} bosses=${v.bosses} kinds=${v.kinds}`)
    say(ctx, `axes: ${TtlKarma.axes().map(a => `${a}=${v.axes[a]} (raw ${v.raw[a]})`).join(' ')}`)
    say(ctx, `deeds: ${Object.keys(deeds).sort().map(k => `${k}=${deeds[k]}`).join(' ') || 'none'}`)
    var offers = String(target.persistentData.getString('ttl.offers'))
    if (offers) say(ctx, `offers: ${offers}`)
    return 1
  }

  var set = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var key = String(Arguments.STRING.getResult(ctx, 'stat'))
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    if (TtlLife.phase(target) !== 'life1') throw `${target.username} is not in Life 1; karma was judged at death`
    TtlKarma.set(server, target, key, n)
    say(ctx, `karma ${target.username}: ${key}=${n}`)
    return 1
  }

  var facts = (server, target) => {
    var v = TtlKarma.current(server, target)
    var offers = String(target.persistentData.getString('ttl.offers'))
    var list = offers ? offers.split(',') : []
    var tier = v ? v.tier : TtlData.karma.default_tier
    var darkPool = TtlKarma.darkPool(tier)
    return {
      tier: tier,
      dark: String(!!(v && v.dark)),
      days: String(v ? v.days : 0),
      bosses: String(v ? v.bosses : 0),
      offers: String(list.length),
      darkoffer: String(list.some(r => darkPool.indexOf(r) >= 0)),
      step: String(target.persistentData.getString('ttl.step')) || 'none',
      phase: String(TtlLife.phase(target)),
      bonus: String(String(target.persistentData.getString('ttl.karma.bonus')).split(',').filter(s => s).length)
    }
  }

  var expect = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var field = String(Arguments.STRING.getResult(ctx, 'field'))
    var want = String(Arguments.STRING.getResult(ctx, 'value'))
    var all = facts(server, target)
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')})`
    if (all[field] !== want) throw `${target.username}: expected ${field}=${want}, got ${all[field]} (offers ${target.persistentData.getString('ttl.offers') || 'none'})`
    say(ctx, `karma ${target.username}: ${field}=${want} as expected`)
    return 1
  }

  // Checks the weighted unique draw (TtlRegistry.draw with the tier's weights) without granting anything.
  var odds = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var name = target.username
    var wish = TtlWishes.get(String(Arguments.STRING.getResult(ctx, 'wish')).toLowerCase())
    if (!wish) throw 'unknown wish'
    var weights = TtlKarma.drawWeights(target)
    var free = TtlRegistry.available(server, wish.pool, name)
    var total = 0
    var rareWeight = 0
    free.forEach(id => {
      var r = TtlRegistry.rarityOf(id)
      var x = weights && weights[r] !== undefined ? Number(weights[r]) : 1
      total += x
      if (r === 'rare') rareWeight += x
    })
    var expected = total > 0 ? rareWeight / total : 0
    var n = 400
    var rare = 0
    for (var i = 0; i < n; i++) {
      var d = TtlRegistry.draw(server, wish.pool, 1, name, weights)
      if (d.length > 0 && TtlRegistry.rarityOf(d[0]) === 'rare') rare++
    }
    var pct = x => `${Math.round(x * 100)}%`
    say(ctx, `odds ${name} ${wish.id}: rare ${rare}/${n} (${pct(rare / n)}), expected ${pct(expected)}, weights ${JSON.stringify(weights || {})}, ${free.length} free`)
    if (Math.abs(rare / n - expected) > 0.1) throw `${name}: rare share ${pct(rare / n)} is far from the expected ${pct(expected)}`
    return 1
  }

  var pick = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var first = String(target.persistentData.getString('ttl.uniqueOptions')).split(',')[0]
    if (!first) throw `${target.username} has no unique options`
    var error = TtlCorridor.unique(server, target, first.replace(/^.*:/, ''))
    if (error) throw error
    say(ctx, `karma ${target.username}: picked ${first}`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('life').executes(logged(ctx => {
      var player = ctx.source.getPlayerOrException()
      TtlKarmaView.showLife(ctx.source.getServer(), player)
      return 1
    })))
    .then(Commands.literal('karma')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('set')
          .then(Commands.argument('stat', Arguments.STRING.create(event))
            .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(set)))))
        .then(Commands.literal('pick').executes(logged(pick)))
        .then(Commands.literal('odds')
          .then(Commands.argument('wish', Arguments.STRING.create(event)).executes(logged(odds))))
        .then(Commands.literal('expect')
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))))
})
