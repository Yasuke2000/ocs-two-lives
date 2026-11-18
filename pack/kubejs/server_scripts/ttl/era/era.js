// priority: 70
// Eras, Legendary slots and Skill Cores (Sprint 3-4, S5; the registry half is in registry.js).
//   An era is the server fact `ttl.season` (1 until set). Legendary slots are counted per era by the registry, so
//   `/ttl era next` needs no reset: the new era simply has all slots free. It also archives and clears the ERA TITLES
//   (skills.toml [era] titles); permanent titles and everything else stay.
// Server persistentData:
//   ttl.season       int            the current era
//   ttl.era.started  string millis  when it began
//   ttl.era.titles   {uuid: [id]}   era titles earned in the current era
//   ttl.era.archive  [{era, ended, titles: {uuid: [id]}}]   finished eras, newest last, capped at 20
// Commands (Brigadier merges them into the /ttl tree, as karma/commands.js does):
//   Players: /ttl era (era, Legendary slots) · /ttl core open (opens a Skill Core from the inventory; Life 2 only)
//   Ops:     /ttl era next · /ttl era title <player> <id> · /ttl registry slots
//            /ttl registry transfer <from> <to> <skill> [route] (route: duel, war, bequest, awakening, staff ...; default staff)
//            /ttl registry legend <player> <skill> (grant that uses a per-era slot, as a rebirth Legend pick does)
//            /ttl registry legendcap <max> <slots> | reset (test hook: replaces max_holders / slots_per_era)
//            /ttl core open <player> (no item) · /ttl core odds <player> · and the assertions
//            /ttl era expect number|slots|free <n> (free -1 = no per-era slots) · titles <player> <n>
//            /ttl registry expect moved <from> <to> <skill> · routed <to> <skill> <route> · holders <n> (Legendary holders)
//            /ttl core expect <player> <n> (how many uniques the registry lists for them)
const TtlEra = {
  ARCHIVE_MAX: 20,

  number(server) {
    return TtlRegistry.era(server)
  },

  titleDefs() {
    return (TtlData.skills.era || {}).titles || []
  },

  titleDef(id) {
    var want = String(id).toLowerCase()
    var found = null
    this.titleDefs().forEach(t => { if (t.id === want) found = t })
    return found
  },

  started(server) {
    var raw = String(server.persistentData.getString('ttl.era.started'))
    return raw ? Number(raw) : 0
  },

  titles(server) {
    return TtlRegistry.load(server, 'ttl.era.titles', {})
  },

  archive(server) {
    return TtlRegistry.load(server, 'ttl.era.archive', [])
  },

  // First start: era 1 begins now.
  init(server) {
    if (Number(server.persistentData.getInt('ttl.season')) > 0) return
    server.persistentData.putInt('ttl.season', 1)
    server.persistentData.putString('ttl.era.started', String(Date.now()))
    console.info('[ttl] era: era 1 begins')
  },

  // An era title for a player (name, UUID or online player). False when the id is unknown or they hold it already.
  award(server, who, id) {
    var def = this.titleDef(id)
    if (!def) return false
    var party = TtlRegistry.party(server, who)
    var all = this.titles(server)
    var mine = all[party.id] || []
    if (mine.indexOf(def.id) >= 0) return false
    all[party.id] = mine.concat([def.id])
    TtlRegistry.store(server, 'ttl.era.titles', all)
    console.info(`[ttl] era: ${TtlRegistry.nameOf(server, party.id)} earned the era title ${def.id} in era ${this.number(server)}`)
    return true
  },

  titleCount(server, who) {
    var party = TtlRegistry.party(server, who)
    return (this.titles(server)[party.id] || []).length
  },

  // Starts the next era; returns its number. Slots need no reset (the registry keys them by era).
  next(server, reason) {
    var old = this.number(server)
    var list = this.archive(server)
    list.push({ era: old, ended: Date.now(), titles: this.titles(server) })
    if (list.length > this.ARCHIVE_MAX) list = list.slice(list.length - this.ARCHIVE_MAX)
    while (list.length > 1 && JSON.stringify(list).length > TtlRegistry.MAX_JSON) list.shift()
    TtlRegistry.store(server, 'ttl.era.archive', list)
    TtlRegistry.store(server, 'ttl.era.titles', {})
    var now = old + 1
    server.persistentData.putInt('ttl.season', now)
    server.persistentData.putString('ttl.era.started', String(Date.now()))
    console.info(`[ttl] era: era ${old} ended, era ${now} begins (${reason || 'admin'}); ${this.slotText(server)}`)
    try {
      server.runCommandSilent(`tellraw @a ${JSON.stringify([
        { text: '[Voice of the World] ', color: 'gold' },
        { text: `Era ${old} is over. Era ${now} begins.`, color: 'light_purple' }
      ])}`)
      if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, `Era ${old} is over. Era ${now} begins.`)
    } catch (e) {
      console.warn(`[ttl] era: announcement failed: ${e}`)
    }
    return now
  },

  slotText(server) {
    var per = TtlRegistry.slotsPerEra(server)
    return per > 0 ? `Legendary slots ${TtlRegistry.slotsUsed(server)}/${per} used` : 'no per-era Legendary slots'
  },

  summary(server) {
    var max = TtlRegistry.maxHolders(server)
    return `Era ${this.number(server)}: ${this.slotText(server)}; Legendary holders ${TtlRegistry.legendaryHolders(server).length}/${max > 0 ? max : 'unlimited'}`
  },

  coreConf() {
    var c = TtlData.skills.core || {}
    return { item: c.item || 'ttl:skill_core', requireItem: c.require_item !== false }
  },

  // A player opens a Skill Core from their inventory. Draws first, so a core is never spent when nothing is free;
  // when the grant is refused after the core was taken, it is given back. Returns a message for the player
  // (an error) or null when it went through.
  playerOpen(server, player) {
    var conf = this.coreConf()
    if (TtlLife.phase(player) !== 'life2') return 'A Skill Core only answers in your second life.'
    var skill = TtlRegistry.coreDraw(server, player)
    if (!skill) return 'No skill is left for this core to give you. Keep it.'
    if (conf.requireItem) {
      if (!(player.inventory.count(conf.item) > 0)) return 'You carry no Skill Core.'
      server.runCommandSilent(`quietly clear ${player.username} ${conf.item} 1`)
    }
    if (!TtlRegistry.grant(server, player, skill, 'opened a Skill Core')) {
      if (conf.requireItem) server.runCommandSilent(`quietly give ${player.username} ${conf.item} 1`)
      return 'The core would not open. Try again later.'
    }
    TtlCorridor.voice(server, player.username, `The Skill Core opens. ${TtlCorridor.title(skill)} is yours.`)
    return null
  }
}

ServerEvents.loaded(event => {
  try {
    TtlEra.init(event.server)
  } catch (e) {
    console.error(`[ttl] era: init failed: ${e}`)
  }
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] era command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var player = (ctx, name) => Arguments.PLAYER.getResult(ctx, name)
  var skillOf = (ctx, name) => `tensura:${word(ctx, name).replace(/^.*:/, '')}`
  var playerArg = name => Commands.argument(name, Arguments.PLAYER.create(event))
  var stringArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))
  var check = (ctx, label, got, want) => {
    if (got !== want) throw `expected ${label} ${want}, got ${got}`
    say(ctx, `era: ${label} ${want} as expected`)
    return 1
  }

  var eraStatus = ctx => {
    var server = ctx.source.getServer()
    say(ctx, TtlEra.summary(server))
    return 1
  }

  var eraNext = ctx => {
    var n = TtlEra.next(ctx.source.getServer(), 'admin')
    say(ctx, `Era ${n} begins`)
    return 1
  }

  var eraTitle = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var id = word(ctx, 'id')
    if (!TtlEra.titleDef(id)) throw `unknown era title ${id} (${TtlEra.titleDefs().map(t => t.id).join(', ')})`
    var ok = TtlEra.award(server, target, id)
    say(ctx, ok ? `${target.username} earned the era title ${id}` : `${target.username} already has the era title ${id}`)
    return ok ? 1 : 0
  }

  var slots = ctx => {
    var server = ctx.source.getServer()
    var ledger = TtlRegistry.slotLedger(server)
    say(ctx, `${TtlEra.summary(server)}; ledger ${JSON.stringify(ledger)}`)
    return 1
  }

  var transferWith = withRoute => ctx => {
    var route = withRoute ? word(ctx, 'route') : 'staff'
    var server = ctx.source.getServer()
    var to = player(ctx, 'to')
    var skill = skillOf(ctx, 'skill')
    var from = String(Arguments.STRING.getResult(ctx, 'from'))
    var ok = TtlRegistry.transfer(server, from, to, skill, route, 'admin transfer')
    say(ctx, ok ? `Moved ${skill} from ${from} to ${to.username} (${route})` : `Refused: ${from} -> ${to.username} for ${skill} (see the log)`)
    return ok ? 1 : 0
  }

  // The same grant a rebirth Legend pick makes: a Legendary NEW holder needs, and spends, a slot.
  var legend = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var skill = skillOf(ctx, 'skill')
    var ok = TtlRegistry.grant(server, target, skill, 'Legend pick (test hook)', { slot: true })
    say(ctx, ok ? `Granted ${skill} to ${target.username} in a Legendary slot (${TtlEra.summary(server)})` : `Refused ${skill} for ${target.username}`)
    return ok ? 1 : 0
  }

  var legendCap = ctx => {
    var server = ctx.source.getServer()
    server.persistentData.putString('ttl.reg.testcaps', JSON.stringify({ max: num(ctx, 'max'), slots: num(ctx, 'slots') }))
    say(ctx, `Legendary ceiling for tests: ${TtlEra.summary(server)}`)
    return 1
  }
  var legendCapReset = ctx => {
    var server = ctx.source.getServer()
    server.persistentData.remove('ttl.reg.testcaps')
    say(ctx, `Legendary ceiling back to skills.toml: ${TtlEra.summary(server)}`)
    return 1
  }
  var expectRouted = ctx => {
    var server = ctx.source.getServer()
    var to = player(ctx, 'to')
    var skill = skillOf(ctx, 'skill')
    var route = word(ctx, 'route')
    var toId = TtlRegistry.uid(to)
    var mine = TtlRegistry.history(server).filter(h => h.e === 'transfer' && h.s === skill && h.u === toId)
    var last = mine.length > 0 ? mine[mine.length - 1] : null
    if (!last || last.v !== route) throw `expected the last transfer of ${skill} to ${to.username} to go by ${route}, got ${last ? last.v : 'none'}`
    say(ctx, `registry: ${skill} reached ${to.username} by ${route} as expected`)
    return 1
  }

  var expectMoved = ctx => {
    var server = ctx.source.getServer()
    var from = TtlRegistry.party(server, String(Arguments.STRING.getResult(ctx, 'from')))
    var to = player(ctx, 'to')
    var skill = skillOf(ctx, 'skill')
    var toId = TtlRegistry.uid(to)
    var mine = TtlRegistry.history(server).filter(h => h.e === 'transfer' && h.s === skill && h.u === toId && h.f === from.id)
    if (mine.length === 0) throw `no transfer of ${skill} from ${from.id} to ${to.username} in the history`
    say(ctx, `registry: ${skill} moved from ${TtlRegistry.nameOf(server, from.id)} to ${to.username} as expected`)
    return 1
  }

  var coreOpen = ctx => {
    var src = ctx.source
    var player0 = src.getPlayerOrException()
    var err = TtlEra.playerOpen(src.getServer(), player0)
    if (err) {
      player0.tell(Text.red(err))
      return 0
    }
    return 1
  }
  var coreOpenFor = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var skill = TtlRegistry.openCore(server, target, 'opened a Skill Core (admin)')
    say(ctx, skill ? `${target.username} opened a Skill Core: ${skill}` : `Nothing to give ${target.username}`)
    return skill ? 1 : 0
  }

  // 300 draws without granting: a Skill Core must never hold a Legendary, and the weights must favour Rare.
  var coreOdds = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var pool = TtlRegistry.corePool()
    var weights = TtlRegistry.coreWeights()
    var id = TtlRegistry.uid(target)
    var counts = { legendary: 0, rare: 0, common: 0 }
    var none = 0
    for (var i = 0; i < 300; i++) {
      var d = TtlRegistry.draw(server, pool, 1, id, weights)
      if (d.length === 0) none++
      else counts[TtlRegistry.rarityOf(d[0])]++
    }
    say(ctx, `core odds for ${target.username}: rare ${counts.rare} common ${counts.common} legendary ${counts.legendary} none ${none}`)
    if (counts.legendary > 0) throw `a Skill Core drew a Legendary ${counts.legendary} times`
    return 1
  }

  var coreExpect = ctx => {
    var server = ctx.source.getServer()
    var target = player(ctx, 'target')
    var held = TtlRegistry.heldBy(TtlRegistry.records(server), TtlRegistry.uid(target)).length
    return check(ctx, `${target.username} listed uniques`, held, num(ctx, 'n'))
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('era')
      .executes(logged(eraStatus))
      .then(Commands.literal('next').requires(op).executes(logged(eraNext)))
      .then(Commands.literal('title').requires(op)
        .then(playerArg('target').then(stringArg('id').executes(logged(eraTitle)))))
      .then(Commands.literal('expect').requires(op)
        .then(Commands.literal('number').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'era number', TtlEra.number(ctx.source.getServer()), num(ctx, 'n'))))))
        .then(Commands.literal('slots').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'Legendary slots used', TtlRegistry.slotsUsed(ctx.source.getServer()), num(ctx, 'n'))))))
        .then(Commands.literal('free').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'Legendary slots free', TtlRegistry.slotsLeft(ctx.source.getServer()), num(ctx, 'n'))))))
        .then(Commands.literal('titles').then(playerArg('target').then(intArg('n').executes(logged(ctx =>
          check(ctx, `era titles of ${player(ctx, 'target').username}`, TtlEra.titleCount(ctx.source.getServer(), player(ctx, 'target')), num(ctx, 'n')))))))))
    .then(Commands.literal('registry').requires(op)
      .then(Commands.literal('slots').executes(logged(slots)))
      .then(Commands.literal('legendcap')
        .then(Commands.literal('reset').executes(logged(legendCapReset)))
        .then(intArg('max').then(intArg('slots').executes(logged(legendCap)))))
      .then(Commands.literal('transfer')
        .then(stringArg('from').then(playerArg('to').then(stringArg('skill')
          .executes(logged(transferWith(false)))
          .then(stringArg('route').executes(logged(transferWith(true))))))))
      .then(Commands.literal('legend')
        .then(playerArg('target').then(stringArg('skill').executes(logged(legend)))))
      .then(Commands.literal('expect')
        .then(Commands.literal('holders').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'Legendary holders', TtlRegistry.legendaryHolders(ctx.source.getServer()).length, num(ctx, 'n'))))))
        .then(Commands.literal('routed')
          .then(playerArg('to').then(stringArg('skill').then(stringArg('route').executes(logged(expectRouted))))))
        .then(Commands.literal('moved')
          .then(stringArg('from').then(playerArg('to').then(stringArg('skill').executes(logged(expectMoved))))))))
    .then(Commands.literal('core')
      .then(Commands.literal('open')
        .executes(logged(coreOpen))
        .then(playerArg('target').requires(op).executes(logged(coreOpenFor))))
      .then(Commands.literal('odds').requires(op)
        .then(playerArg('target').executes(logged(coreOdds))))
      .then(Commands.literal('expect').requires(op)
        .then(playerArg('target').then(intArg('n').executes(logged(coreExpect)))))))
})
