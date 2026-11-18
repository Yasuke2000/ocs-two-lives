// priority: 60
// Artificer commands (Brigadier merges these into the /ttl tree from commands.js). API: artifice/artifice.js,
// commissions.js, workshop.js. Data: design/data/artifice.toml. A refused player action answers "Workshop: <why>" in red
// (never "ttl: ...", which the test runner counts as a failure); op commands answer "ttl: ..." when something is wrong.
// Players: /ttl artifice                          the Workshop screen (also: right-click a Workshop Bench)
//          /ttl artifice status                   rank, points, caps, what is next
//          /ttl artifice charter                  sign the charter at a Workshop Bench (3 schematics known or carried)
//          /ttl artifice commissions              today's board, with [Take] buttons
//          /ttl artifice commission take <n|id> | turnin | abandon <n|id>
//          /ttl artifice engrave [<engraving>]    the list, or engrave the item in the main hand (rank 2+, chisel, own work)
//          /ttl artifice make [<recipe>]          the workshop recipes, or make one
//          /ttl artifice curse                    the cursed whetstone on the blade in the main hand (dark)
//          /ttl artifice schematic buy            a Dwargon schematic for coin (honest)
//          /ttl artifice steal                    a schematic from the Dwargon smithy at night (dark)
// Ops:     /ttl artifice info <player> · firsts · roll (a new commission board)
//          /ttl artifice points <player> add|set <n> · refresh <player>
//          /ttl artifice commission test <player> <id>    accept a commission that is not on today's board
//          /ttl artifice test <player> life2|life1|reset|anywhere|strict
//                 anywhere: the theft skips the smithy, night and channel rules (2 s); strict: back to normal
//          /ttl artifice test <player> craft|kiln <item>  give the item and run the bench / kiln code path (stamp, points)
//          /ttl artifice test <player> stamp              stamp the item in the main hand as the player's own work
//          /ttl artifice expect <player> <field> <value...>  test assertion (the value is the rest of the line); "ttl: ..." when it does not hold. Ids in fields
//                 use a dot for the colon (tensura.sturdy = tensura:sturdy). Fields:
//                 rank, points, week, craft, title, stage_rank<n>, jobs, job_<id>, ready_<id>, done_<id>, last_id,
//                 last_coins, last_points, metal_<metal>, stamped (items carrying the player's stamp), made_by (main hand:
//                 mine|other|none), cursed (main hand yes|no), enchant_<ns.path> (level on the main hand), schematics,
//                 has_<ns.path> (count carried), constructs, muster, unlocked_<recipe>, recipe_<ns.path> (registered yes|no),
//                 smith_products (> 0: yes), try_charter, try_take_<id>, try_engrave_<ns.path>, try_make_<recipe>,
//                 try_curse, try_buy, try_steal (ok or the reason)
const TtlArtificeCmd = {
  id(dotted) {
    var s = String(dotted)
    var i = s.indexOf('.')
    return i < 0 ? s : `${s.slice(0, i)}:${s.slice(i + 1)}`
  },

  status(server, player) {
    var s = TtlArtifice.read(player)
    var def = TtlArtifice.rankDef(s.rank)
    if (!def) {
      var need = Number((TtlArtifice.conf().charter || {}).schematics || 3)
      return ['You hold no artificer charter yet.',
        `Bring ${need} schematics (learned or carried; you have ${TtlArtifice.schematics(player).length}) to a Workshop Bench and run /ttl artifice charter.`,
        'A Workshop Bench: a Smithing Bench ringed by four low-quality magic crystals.']
    }
    var pts = TtlArtifice.conf().points || {}
    var next = TtlArtifice.rankDef(s.rank + 1)
    var out = [`Artificer rank ${s.rank}: ${def.title}. Points ${s.points}${next ? `; ${next.title} at ${next.points}${next.requires_any ? ' (and a craft unique, or Dwargon exalted)' : ''}` : ''}.`,
      `This week: ${s.week}/${pts.weekly_cap} points (crafting ${s.craft}/${pts.craft_weekly_cap}).`,
      `Commissions up to tier ${def.tier}. Engraving: ${def.engrave ? 'yes' : 'from rank 2'}. Golems: ${def.constructs} (${def.muster} mustered).`,
      `Metals worked: ${Object.keys(s.metals).join(', ') || 'none yet'}.`]
    var jobs = Object.keys(s.jobs).map(k => s.jobs[k].id)
    if (jobs.length) out.push(`Accepted commissions: ${jobs.join(', ')}.`)
    return out
  },

  enchantLevel(server, stack, id) {
    if (stack.isEmpty()) return 0
    var levels = stack.save(server.registryAccess()).getCompound('components').getCompound('minecraft:enchantments').getCompound('levels')
    return Number(levels.getInt(id))
  },

  recipeExists(server, id) {
    try {
      var RL = Java.loadClass('net.minecraft.resources.ResourceLocation')
      return server.getRecipeManager().byKey(RL.parse(id)).isPresent()
    } catch (e) {
      console.warn(`[ttl] artifice: recipe lookup ${id} failed: ${e}`)
      return false
    }
  },

  stamped(server, player) {
    var n = 0
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var st = inv.getItem(i)
      if (!st.isEmpty() && TtlArtifice.isMine(server, player, st)) n += Number(st.count)
    }
    return n
  },

  field(server, player, field) {
    var s = TtlArtifice.read(player)
    var yn = b => (b ? 'yes' : 'no')
    var hand = player.getMainHandItem()
    var m
    switch (field) {
      case 'rank': return String(s.rank)
      case 'points': return String(s.points)
      case 'week': return String(s.week)
      case 'craft': return String(s.craft)
      case 'title': return TtlArtifice.title(player) || 'none'
      case 'jobs': return String(Object.keys(s.jobs).length)
      case 'last_id': return String((s.last || {}).id || 'none')
      case 'last_coins': return String((s.last || {}).coins || 0)
      case 'last_points': return String((s.last || {}).points || 0)
      case 'stamped': return String(this.stamped(server, player))
      case 'made_by': return hand.isEmpty() || !TtlArtifice.madeBy(server, hand) ? 'none' : TtlArtifice.isMine(server, player, hand) ? 'mine' : 'other'
      case 'cursed': return yn(!hand.isEmpty() && TtlArtifice.cursed(hand))
      case 'schematics': return String(TtlArtifice.schematics(player).length)
      case 'constructs': return String(TtlArtifice.caps(player).constructs)
      case 'muster': return String(TtlArtifice.caps(player).muster)
      case 'smith_products': return yn(TtlArtifice.smithCount > 0)
      case 'try_charter': return TtlArtifice.checkCharter(player) || 'ok'
      case 'try_curse': return TtlWorkshop.checkCurse(server, player) || 'ok'
      case 'try_buy': return TtlWorkshop.checkBuy(server, player) || 'ok'
      case 'try_steal': return TtlWorkshop.checkSteal(server, player) || 'ok'
    }
    if ((m = /^stage_rank(\d)$/.exec(field))) return yn(player.stages.has(`ttl.artifice.rank${m[1]}`))
    if ((m = /^job_(.+)$/.exec(field))) return yn(!!TtlCommission.jobFor(s, m[1]))
    if ((m = /^ready_(.+)$/.exec(field))) {
      var c = TtlCommission.find(m[1])
      if (!c) throw `no commission ${m[1]}`
      return yn(TtlCommission.ready(server, player, c))
    }
    if ((m = /^done_(.+)$/.exec(field))) return yn(s.done.indexOf(`${TtlArtifice.dateKey()}:${m[1]}`) >= 0)
    if ((m = /^metal_(.+)$/.exec(field))) return yn(!!s.metals[m[1]])
    if ((m = /^enchant_(.+)$/.exec(field))) return String(this.enchantLevel(server, hand, this.id(m[1])))
    if ((m = /^has_(.+)$/.exec(field))) return String(TtlWorkshop.count(player, this.id(m[1])))
    if ((m = /^unlocked_(.+)$/.exec(field))) return yn(s.unlocked.indexOf(m[1]) >= 0)
    if ((m = /^recipe_(.+)$/.exec(field))) return yn(this.recipeExists(server, this.id(m[1])))
    if ((m = /^try_take_(.+)$/.exec(field))) return TtlCommission.check(server, player, m[1]) || 'ok'
    if ((m = /^try_engrave_(.+)$/.exec(field))) return TtlWorkshop.checkEngrave(server, player, this.id(m[1])) || 'ok'
    if ((m = /^try_make_(.+)$/.exec(field))) return TtlWorkshop.checkMake(server, player, m[1]) || 'ok'
    throw `unknown field ${field}`
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  // Op commands: "ttl: ..." on failure (the test runner counts it).
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] artifice command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  // Player actions: a refusal is a normal answer, not an error.
  var act = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      if (typeof e === 'string') {
        console.info(`[ttl] artifice: refused: ${e}`)
      } else {
        console.error(`[ttl] artifice command failed: ${e}`)
      }
      ctx.source.sendSystemMessage(Text.red(`Workshop: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var me = ctx => ctx.source.getPlayerOrException()
  var server = ctx => ctx.source.getServer()
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var rl = (ctx, name) => String(Arguments.RESOURCE_LOCATION.getResult(ctx, name))
  var tell = (p, lines) => lines.forEach(l => p.tell(Text.of(l)))

  var menu = ctx => {
    var p = me(ctx)
    if (TtlLife.phase(p) !== 'life2') throw 'the workshop opens in your second life'
    TtlWorkshop.menu(server(ctx), p)
    return 1
  }

  var status = ctx => {
    var p = me(ctx)
    tell(p, TtlArtificeCmd.status(server(ctx), p))
    return 1
  }

  var charter = ctx => {
    TtlArtifice.charter(server(ctx), me(ctx))
    return 1
  }

  var board = ctx => {
    var p = me(ctx)
    var srv = server(ctx)
    tell(p, TtlCommission.lines(srv, p))
    var s = TtlArtifice.read(p)
    var def = TtlArtifice.rankDef(s.rank)
    if (def) {
      var takeable = TtlCommission.board(srv).filter(e => !TtlCommission.check(srv, p, e.c.id))
      if (takeable.length) {
        TtlWorkshop.buttons(srv, p, 'Take:', takeable.map(e => ({ label: String(e.n), command: `/ttl artifice commission take ${e.c.id}`, hover: e.c.title })))
      }
      TtlWorkshop.buttons(srv, p, 'Ready?', [{ label: 'Deliver', command: '/ttl artifice commission turnin', hover: 'Hand in what is ready' }])
    }
    return 1
  }

  var take = ctx => {
    TtlCommission.take(server(ctx), me(ctx), str(ctx, 'ref'))
    return 1
  }

  var turnin = ctx => TtlCommission.turnin(server(ctx), me(ctx))

  var abandon = ctx => {
    var c = TtlCommission.abandon(server(ctx), me(ctx), str(ctx, 'ref'))
    me(ctx).tell(Text.gray(`Workshop: you gave up "${c.title}".`))
    return 1
  }

  var engraveList = ctx => {
    var p = me(ctx)
    var srv = server(ctx)
    var rows = TtlArtifice.conf().engraving || []
    p.tell(Text.gold('Engravings (hold your own work in the main hand, an Engraving Chisel in your pack, at a Workshop Bench):'))
    rows.forEach(e => {
      var cost = e.cost || {}
      var parts = []
      if (cost.coins) parts.push(TtlEcon.text(cost.coins))
      Object.keys(cost.items || {}).forEach(id => parts.push(`${cost.items[id]} x ${TtlCommission.pretty(id)}`))
      var why = TtlWorkshop.checkEngrave(srv, p, e.id)
      p.tell(Text.of(`- ${TtlCommission.pretty(e.id)} (rank ${e.rank}): ${parts.join(', ')}${why ? ` [${why}]` : ' [ready]'}`))
    })
    var ready = rows.filter(e => !TtlWorkshop.checkEngrave(srv, p, e.id))
    if (ready.length) TtlWorkshop.buttons(srv, p, 'Engrave:', ready.map(e => ({ label: TtlCommission.pretty(e.id), command: `/ttl artifice engrave ${e.id}` })))
    return 1
  }

  var engrave = ctx => {
    TtlWorkshop.engrave(server(ctx), me(ctx), rl(ctx, 'engraving'))
    return 1
  }

  var makeList = ctx => {
    var p = me(ctx)
    var srv = server(ctx)
    var rows = TtlArtifice.conf().recipe || []
    p.tell(Text.gold('Workshop recipes:'))
    rows.forEach(r => {
      var ins = Object.keys(r.inputs || {}).map(id => `${r.inputs[id]} x ${TtlCommission.pretty(id)}`).join(' + ')
      var why = TtlWorkshop.checkMake(srv, p, r.id)
      p.tell(Text.of(`- ${TtlCommission.pretty(r.output)} (${r.rank > 0 ? `rank ${r.rank}` : 'any soul'}, ${r.station === 'altar' ? 'at a Bone Altar' : 'at a Workshop Bench'}): ${ins}${why ? ` [${why}]` : ' [ready]'}`))
    })
    var ready = rows.filter(r => !TtlWorkshop.checkMake(srv, p, r.id))
    if (ready.length) TtlWorkshop.buttons(srv, p, 'Make:', ready.map(r => ({ label: TtlCommission.pretty(r.output), command: `/ttl artifice make ${r.id}` })))
    return 1
  }

  var make = ctx => {
    TtlWorkshop.make(server(ctx), me(ctx), str(ctx, 'recipe'))
    return 1
  }

  var curse = ctx => {
    TtlWorkshop.curse(server(ctx), me(ctx))
    return 1
  }

  var buy = ctx => {
    TtlWorkshop.buy(server(ctx), me(ctx))
    return 1
  }

  var steal = ctx => {
    TtlWorkshop.steal(server(ctx), me(ctx))
    return 1
  }

  // ---- ops ----

  var info = ctx => {
    var p = target(ctx)
    say(ctx, `artifice ${p.username}: ${p.persistentData.getString(TtlArtifice.KEY) || '{}'}`)
    TtlArtificeCmd.status(server(ctx), p).forEach(l => say(ctx, l))
    return 1
  }

  var firsts = ctx => {
    var f = TtlArtifice.firsts(server(ctx))
    var keys = Object.keys(f)
    if (!keys.length) say(ctx, 'artifice firsts: none yet')
    keys.forEach(k => say(ctx, `artifice first ${k}: ${f[k].name} ${new Date(f[k].at).toISOString()}`))
    return 1
  }

  var roll = ctx => {
    var b = TtlCommission.roll(server(ctx), true)
    say(ctx, `artifice board ${b.date}: ${JSON.stringify(b.tiers)}`)
    return 1
  }

  var points = mode => ctx => {
    var p = target(ctx)
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    if (mode === 'set') TtlArtifice.setPoints(server(ctx), p, n)
    else TtlArtifice.addPoints(server(ctx), p, 'test', n, 'ops')
    var s = TtlArtifice.read(p)
    say(ctx, `artifice ${p.username}: points ${s.points}, rank ${s.rank}`)
    return 1
  }

  var refresh = ctx => {
    var p = target(ctx)
    say(ctx, `artifice ${p.username}: rank ${TtlArtifice.refresh(server(ctx), p)}`)
    return 1
  }

  var commissionTest = ctx => {
    var p = target(ctx)
    var c = TtlCommission.force(server(ctx), p, str(ctx, 'id'))
    say(ctx, `artifice ${p.username}: accepted ${c.id}`)
    return 1
  }

  var test = ctx => {
    var p = target(ctx)
    var srv = server(ctx)
    var what = str(ctx, 'what')
    var uid = TtlLife.uuid(p)
    if (what === 'life2' || what === 'life1') {
      ;['ttl.life1', 'ttl.corridor', 'ttl.life2'].forEach(st => p.stages.remove(st))
      p.stages.add(`ttl.${what}`)
    } else if (what === 'reset') {
      TtlArtifice.clear(srv, p)
      delete TtlArtifice.flags[uid]
      delete TtlWorkshop.channels[uid]
    } else if (what === 'anywhere') {
      TtlArtifice.flags[uid] = { anywhere: true }
    } else if (what === 'strict') {
      delete TtlArtifice.flags[uid]
    } else if (what === 'stamp') {
      if (!TtlArtifice.stamp(srv, p, p.getMainHandItem(), p.getInventory().selected)) throw `${p.username}: nothing stamped (empty hand or already stamped)`
    } else {
      throw 'test hooks: life2, life1, reset, anywhere, strict, stamp, craft <item>, kiln <item>'
    }
    say(ctx, `artifice ${p.username}: ${what}`)
    return 1
  }

  var testMake = kind => ctx => {
    var p = target(ctx)
    var srv = server(ctx)
    var id = rl(ctx, 'item')
    TtlCmd.run(srv, `give ${p.username} ${id}`)
    TtlArtifice.made(srv, p, id, 1, kind)
    say(ctx, `artifice ${p.username}: ${kind} made ${id}`)
    return 1
  }

  var expect = ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = String(Arguments.GREEDY_STRING.getResult(ctx, 'value')).trim()
    var got = TtlArtificeCmd.field(server(ctx), p, field)
    if (got !== want) throw `${p.username}: expected ${field}=${want}, got ${got}`
    say(ctx, `artifice ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var op = src => src.hasPermission(2)
  var player = name => Commands.argument('target', Arguments.PLAYER.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('artifice')
      .executes(act(menu))
      .then(Commands.literal('status').executes(act(status)))
      .then(Commands.literal('charter').executes(act(charter)))
      .then(Commands.literal('commissions').executes(act(board)))
      .then(Commands.literal('commission')
        .then(Commands.literal('take').then(Commands.argument('ref', Arguments.STRING.create(event)).executes(act(take))))
        .then(Commands.literal('turnin').executes(act(turnin)))
        .then(Commands.literal('abandon').then(Commands.argument('ref', Arguments.STRING.create(event)).executes(act(abandon))))
        .then(Commands.literal('test').requires(op)
          .then(player().then(Commands.argument('id', Arguments.STRING.create(event)).executes(logged(commissionTest))))))
      .then(Commands.literal('engrave')
        .executes(act(engraveList))
        .then(Commands.argument('engraving', Arguments.RESOURCE_LOCATION.create(event)).executes(act(engrave))))
      .then(Commands.literal('make')
        .executes(act(makeList))
        .then(Commands.argument('recipe', Arguments.STRING.create(event)).executes(act(make))))
      .then(Commands.literal('curse').executes(act(curse)))
      .then(Commands.literal('schematic').then(Commands.literal('buy').executes(act(buy))))
      .then(Commands.literal('steal').executes(act(steal)))
      .then(Commands.literal('info').requires(op).then(player().executes(logged(info))))
      .then(Commands.literal('firsts').requires(op).executes(logged(firsts)))
      .then(Commands.literal('roll').requires(op).executes(logged(roll)))
      .then(Commands.literal('refresh').requires(op).then(player().executes(logged(refresh))))
      .then(Commands.literal('points').requires(op)
        .then(player()
          .then(Commands.literal('add').then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(points('add')))))
          .then(Commands.literal('set').then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(points('set')))))))
      .then(Commands.literal('test').requires(op)
        .then(player()
          .then(Commands.literal('craft').then(Commands.argument('item', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(testMake('bench')))))
          .then(Commands.literal('kiln').then(Commands.argument('item', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(testMake('kiln')))))
          .then(Commands.argument('what', Arguments.STRING.create(event)).executes(logged(test)))))
      .then(Commands.literal('expect').requires(op)
        .then(player()
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('value', Arguments.GREEDY_STRING.create(event)).executes(logged(expect))))))))
})
