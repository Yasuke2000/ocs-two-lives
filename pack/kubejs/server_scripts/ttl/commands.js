// Players:  /ttl menu (reopen choices) · /ttl wish <id> · /ttl trial · /ttl answer <word> · /ttl choose <race> · /ttl unique <skill> · /ttl status
// Ops:      /ttl inspect <player> (answers over RCON) · /ttl reset <player> (back to a fresh Life 1)
//           /ttl as <player> <command> (test hook: run a command as the player typed it, e.g. FTB party commands)
//           /ttl registry · /ttl registry free <skill> (release a unique whose holder is gone)
//           /ttl registry history [skill] (the newest 20 transfers: grants, revokes, returns to the pool)
//           /ttl registry sweep (return to pool now: holders inactive for skills.toml [registry] inactive_days) · migrate (name → UUID records)
//           /ttl registry seen <player> <days> · legacy <player> (test hooks) · expect count|holds|has|keyed|last|pending|rarity ... ("ttl: ..." on failure)
//           /ttl reconcile <player> (match the registry to the uniques they really hold; also runs every 5 min)
//           /ttl grant <player> <skill> (through the registry, caps apply)
//           /ttl build <name> (place blueprints/<name>.py with its corner at your feet)
//           /ttl spawn (where Life 1 starts: Wayfarer's Rest in the Mortal Realm)
// Places:   /ttl where <place> (players: direction + rounded distance) · /locate place <id> (ops: exact, vanilla style) — life/locate.js
// Karma:    /ttl life (players) · /ttl karma <player> [set <stat> <n> | expect <field> <value>] — karma/commands.js
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var life = TtlLife

  // Corridor steps return an error message, or null when the step went through.
  var step = fn => ctx => {
    var player = ctx.source.getPlayerOrException()
    if (life.phase(player) !== 'corridor') {
      player.tell(Text.red('This only works in the Spirit Corridor.'))
      return 0
    }
    var error
    try {
      error = fn(ctx.source.getServer(), player, ctx)
    } catch (e) {
      console.error(`[ttl] ${player.username}: corridor step failed: ${e}`)
      error = 'Something went wrong. Tell an admin.'
    }
    if (error) {
      player.tell(Text.red(error))
      return 0
    }
    return 1
  }
  var word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()

  var status = ctx => {
    var player = ctx.source.getPlayerOrException()
    var step = player.persistentData.getString('ttl.step')
    player.tell(Text.gold(`Life: ${life.phase(player) || 'none'}${step ? ` (${step})` : ''}`))
    return 1
  }

  var inspect = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var data = target.persistentData
    var fields = ['ttl.step', 'ttl.wish', 'ttl.offers', 'ttl.race', 'ttl.uniqueOptions', 'ttl.uniques', 'ttl.killer']
      .map(k => `${k}=${data.getString(k)}`)
      .concat([`ttl.trial.done=${data.getBoolean('ttl.trial.done')}`, `ttl.trial.passed=${data.getBoolean('ttl.trial.passed')}`,
        `strikes=${data.getInt('ttl.trial.strikes')}`, `correct=${data.getInt('ttl.trial.correct')}`, `food=${target.getFoodData().getFoodLevel()}`,
        TtlKarma.brief(ctx.source.getServer(), target)])
    var pos = `${Math.floor(target.getX())},${Math.floor(target.getY())},${Math.floor(target.getZ())}`
    var line = `${target.username}: phase=${life.phase(target)} dim=${life.dimensionOf(target)} pos=${pos} ${fields.join(' ')}`
    ctx.source.sendSystemMessage(Text.of(line))
    return 1
  }

  // Brigadier swallows script errors as "An unexpected error occurred"; log the real cause.
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var reset = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var name = target.username
    ;['ttl.life1', 'ttl.corridor', 'ttl.life2'].forEach(s => target.stages.remove(s))
    TtlCorridor.KEYS.forEach(k => target.persistentData.remove(k))
    TtlRegistry.revokeAll(server, target)
    server.runCommandSilent(`quietly clear ${name}`)
    server.runCommandSilent(`quietly gamemode survival ${name}`)
    target.stages.add('ttl.life1')
    // Karma v1: a fresh Life 1 forgets the old verdict and starts counting again.
    TtlKarma.startLife(server, target)
    TtlLife.makeHuman(server, target)
    life.toMortal(server, target)
    // Soul carryover (WP1), reputation (WP3) and story state (WP-S1) belong to the old soul; guarded so a missing script cannot break a reset.
    try {
      if (typeof TtlSoul !== 'undefined' && typeof TtlSoul.clear === 'function') TtlSoul.clear(target)
      if (typeof TtlRep !== 'undefined' && typeof TtlRep.clear === 'function') TtlRep.clear(server, target)
      if (typeof TtlStory !== 'undefined' && typeof TtlStory.clear === 'function') TtlStory.clear(server, target)
      // A staff full reset is the one thing that gives a soul its awakening claim back (absorb/absorb.js ttl.absorb.souls).
      if (typeof TtlAbsorb !== 'undefined' && typeof TtlAbsorb.clear === 'function') TtlAbsorb.clear(server, target)
    } catch (e) {
      console.error(`[ttl] reset of soul/reputation data for ${name} failed: ${e}`)
    }
    // The Artificer (artifice/artifice.js, ttl.artifice): rank, points, stages and scoreboard belong to the old soul too.
    try {
      if (typeof TtlArtifice !== 'undefined' && typeof TtlArtifice.clear === 'function') TtlArtifice.clear(server, target)
    } catch (e) {
      console.error(`[ttl] reset of the artificer data for ${name} failed: ${e}`)
    }
    console.info(`[ttl] ${name} reset to Life 1`)
    ctx.source.sendSystemMessage(Text.of(`${name} reset to Life 1`))
    return 1
  }

  var registryList = ctx => {
    var holders = TtlRegistry.holders(ctx.source.getServer())
    var lines = Object.keys(holders).sort().map(id => `${id} ${holders[id].length}/${TtlRegistry.capOf(id)}: ${holders[id].join(', ')}`)
    ctx.source.sendSystemMessage(Text.of(lines.length ? 'Held uniques:' : 'Held uniques: none'))
    lines.forEach(line => ctx.source.sendSystemMessage(Text.of(line)))
    return 1
  }

  var registryFree = ctx => {
    var server = ctx.source.getServer()
    var skill = `tensura:${word(ctx, 'skill')}`
    TtlRegistry.free(server, skill)
    console.info(`[ttl] registry: ${skill} released by an admin`)
    ctx.source.sendSystemMessage(Text.of(`Released ${skill}`))
    return 1
  }

  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))

  var registryHistory = withSkill => ctx => {
    var skill = withSkill ? word(ctx, 'skill') : null
    var lines = TtlRegistry.historyLines(ctx.source.getServer(), skill, 20)
    say(ctx, lines.length ? `Registry history${skill ? ` of ${skill}` : ''} (newest last):` : 'Registry history: nothing yet')
    lines.forEach(line => say(ctx, line))
    return 1
  }

  var registrySweep = ctx => {
    var n = TtlRegistry.sweep(ctx.source.getServer())
    say(ctx, `Returned ${n} unique record${n === 1 ? '' : 's'} to the pool`)
    return 1
  }

  var registryMigrate = ctx => {
    var n = TtlRegistry.migrate(ctx.source.getServer(), true)
    say(ctx, `Migrated ${n} name-keyed record${n === 1 ? '' : 's'} to UUIDs`)
    return 1
  }

  var registrySeen = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var days = Number(Arguments.INTEGER.getResult(ctx, 'days'))
    TtlRegistry.fakeSeen(ctx.source.getServer(), target.username, days)
    say(ctx, `${target.username} last seen ${days} days ago (test hook)`)
    return 1
  }

  var registryLegacy = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var n = TtlRegistry.fakeLegacy(ctx.source.getServer(), target)
    say(ctx, `${target.username}: ${n} record${n === 1 ? '' : 's'} rewritten as name entries (test hook)`)
    return 1
  }

  // Assertions for tests/ingame/registry*.rcon: a failed one throws, which `logged` prints as "ttl: ...".
  var flag = (ctx, name) => {
    var v = String(Arguments.STRING.getResult(ctx, name)).toLowerCase()
    if (v !== 'true' && v !== 'false') throw `${name} must be true or false`
    return v === 'true'
  }
  var expectCount = ctx => {
    var skill = `tensura:${word(ctx, 'skill')}`
    var want = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var got = (TtlRegistry.records(ctx.source.getServer())[skill] || []).length
    if (got !== want) throw `expected ${skill} to have ${want} holders, it has ${got}`
    say(ctx, `registry: ${skill} has ${want} holders as expected`)
    return 1
  }
  var expectHolds = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var skill = `tensura:${word(ctx, 'skill')}`
    var want = flag(ctx, 'value')
    var got = (TtlRegistry.records(ctx.source.getServer())[skill] || []).indexOf(TtlRegistry.uid(target)) >= 0
    if (got !== want) throw `expected the registry to ${want ? '' : 'not '}list ${target.username} for ${skill}`
    say(ctx, `registry: ${target.username} ${want ? 'is' : 'is not'} a holder of ${skill} as expected`)
    return 1
  }
  var expectHas = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var skill = `tensura:${word(ctx, 'skill')}`
    var want = flag(ctx, 'value')
    var actual = TtlManas.uniques(target)
    if (actual === null) throw 'the Manas bridge cannot read skills'
    if ((actual.indexOf(skill) >= 0) !== want) throw `expected ${target.username} to ${want ? '' : 'not '}hold ${skill}; holds ${actual.join(', ') || 'no uniques'}`
    say(ctx, `registry: ${target.username} ${want ? 'holds' : 'does not hold'} ${skill} as expected`)
    return 1
  }
  var expectKeyed = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var recs = TtlRegistry.records(server)
    var id = TtlRegistry.uid(target)
    var legacy = Object.keys(recs).filter(s => recs[s].indexOf(String(target.username)) >= 0)
    if (legacy.length > 0) throw `${target.username} still has name-keyed records: ${legacy.join(', ')}`
    if (TtlRegistry.heldBy(recs, id).length === 0) throw `${target.username} has no UUID-keyed records`
    if (TtlRegistry.nameOf(server, id) !== String(target.username)) throw `the name cache has ${TtlRegistry.nameOf(server, id)} for ${target.username}`
    say(ctx, `registry: ${target.username} is keyed by ${id} as expected`)
    return 1
  }
  var expectLast = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var id = TtlRegistry.uid(target)
    var kind = word(ctx, 'kind')
    var skill = `tensura:${word(ctx, 'skill')}`
    var mine = TtlRegistry.history(server).filter(h => h.u === id)
    var last = mine.length > 0 ? mine[mine.length - 1] : null
    if (!last || last.e !== kind || last.s !== skill) throw `expected the last history entry of ${target.username} to be ${kind} ${skill}, got ${last ? `${last.e} ${last.s}` : 'none'}`
    say(ctx, `registry: last entry of ${target.username} is ${kind} ${skill} as expected`)
    return 1
  }
  var expectPending = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var want = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var got = (TtlRegistry.returned(ctx.source.getServer())[TtlRegistry.uid(target)] || []).length
    if (got !== want) throw `expected ${want} returned skills waiting for ${target.username}, found ${got}`
    say(ctx, `registry: ${want} returned skills waiting for ${target.username} as expected`)
    return 1
  }
  var expectRarity = ctx => {
    var skill = `tensura:${word(ctx, 'skill')}`
    var want = word(ctx, 'value')
    var got = TtlRegistry.rarityOf(skill)
    if (got !== want) throw `expected ${skill} to be ${want}, it is ${got} (cap ${TtlRegistry.capOf(skill)})`
    say(ctx, `registry: ${skill} is ${want} (cap ${TtlRegistry.capOf(skill)}) as expected`)
    return 1
  }
  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var skillArg = () => Commands.argument('skill', Arguments.STRING.create(event))
  var valueArg = () => Commands.argument('value', Arguments.STRING.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('wish')
      .then(Commands.argument('id', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.wish(server, player, word(ctx, 'id'))))))
    .then(Commands.literal('trial')
      .executes(step((server, player) => TtlTrial.start(server, player))))
    .then(Commands.literal('menu')
      .executes(step((server, player) => {
        TtlCorridor.showStep(server, player)
        return null
      })))
    .then(Commands.literal('answer')
      .then(Commands.argument('word', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlTrial.answer(server, player, word(ctx, 'word'))))))
    .then(Commands.literal('rebirth')
      .executes(step((server, player) => TtlCorridor.startRebirth(server, player))))
    // Called by ttl-portals when the reincarnation menu (Great Sage scene) confirms a race.
    .then(Commands.literal('reborn')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.argument('race', Arguments.STRING.create(event)).executes(logged(ctx => {
          var target = Arguments.PLAYER.getResult(ctx, 'target')
          var error = TtlCorridor.reborn(ctx.source.getServer(), target, String(Arguments.STRING.getResult(ctx, 'race')))
          if (error) console.warn(`[ttl] reborn ${target.username}: ${error}`)
          return error ? 0 : 1
        })))))
    .then(Commands.literal('choose')
      .then(Commands.argument('race', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.choose(server, player, word(ctx, 'race'))))))
    .then(Commands.literal('unique')
      .then(Commands.argument('skill', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.unique(server, player, word(ctx, 'skill'))))))
    .then(Commands.literal('status').executes(status))
    .then(Commands.literal('inspect')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(inspect))))
    .then(Commands.literal('grant')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.argument('skill', Arguments.STRING.create(event)).executes(logged(ctx => {
          var target = Arguments.PLAYER.getResult(ctx, 'target')
          var skill = `tensura:${word(ctx, 'skill')}`
          var ok = TtlRegistry.grant(ctx.source.getServer(), target, skill)
          ctx.source.sendSystemMessage(Text.of(ok ? `Granted ${skill} to ${target.username}` : `Refused ${skill} for ${target.username}`))
          return ok ? 1 : 0
        })))))
    .then(Commands.literal('build')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('name', Arguments.STRING.create(event)).executes(logged(ctx => {
        var player = ctx.source.getPlayerOrException()
        var name = word(ctx, 'name')
        ctx.source.getServer().runCommandSilent(`execute as ${player.username} at @s run place template ttl:${name} ~ ~ ~`)
        console.info(`[ttl] ${player.username} placed blueprint ${name}`)
        return 1
      }))))
    .then(Commands.literal('reconcile')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(ctx => {
        var target = Arguments.PLAYER.getResult(ctx, 'target')
        TtlRegistry.reconcile(ctx.source.getServer(), target)
        var held = String(target.persistentData.getString('ttl.uniques'))
        ctx.source.sendSystemMessage(Text.of(`${target.username} holds: ${held || 'no uniques'}`))
        return 1
      }))))
    .then(Commands.literal('spawn')
      .requires(src => src.hasPermission(2))
      .executes(logged(ctx => {
        var data = ctx.source.getServer().persistentData
        var spawn = String(data.getString('ttl.mortal.spawn'))
        if (!spawn) throw 'the mortal spawn is not placed (see the server log)'
        ctx.source.sendSystemMessage(Text.of(`Mortal spawn: ${spawn} in ${life.MORTAL} (version ${data.getInt('ttl.mortal.version')})`))
        return 1
      })))
    .then(Commands.literal('registry')
      .requires(src => src.hasPermission(2))
      .executes(logged(registryList))
      .then(Commands.literal('free')
        .then(Commands.argument('skill', Arguments.STRING.create(event)).executes(logged(registryFree))))
      .then(Commands.literal('history')
        .executes(logged(registryHistory(false)))
        .then(skillArg().executes(logged(registryHistory(true)))))
      .then(Commands.literal('sweep').executes(logged(registrySweep)))
      .then(Commands.literal('migrate').executes(logged(registryMigrate)))
      .then(Commands.literal('seen')
        .then(playerArg().then(Commands.argument('days', Arguments.INTEGER.create(event)).executes(logged(registrySeen)))))
      .then(Commands.literal('legacy')
        .then(playerArg().executes(logged(registryLegacy))))
      .then(Commands.literal('expect')
        .then(Commands.literal('count')
          .then(skillArg().then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(expectCount)))))
        .then(Commands.literal('holds')
          .then(playerArg().then(skillArg().then(valueArg().executes(logged(expectHolds))))))
        .then(Commands.literal('has')
          .then(playerArg().then(skillArg().then(valueArg().executes(logged(expectHas))))))
        .then(Commands.literal('keyed')
          .then(playerArg().executes(logged(expectKeyed))))
        .then(Commands.literal('last')
          .then(playerArg().then(Commands.argument('kind', Arguments.STRING.create(event))
            .then(skillArg().executes(logged(expectLast))))))
        .then(Commands.literal('pending')
          .then(playerArg().then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(expectPending)))))
        .then(Commands.literal('rarity')
          .then(skillArg().then(valueArg().executes(logged(expectRarity)))))))
    .then(Commands.literal('reset')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(reset))))
    // Test hook: run a command as the player typed it (TtlCmd.runAs), e.g. FTB Teams party commands for test bots.
    // Prints the result; a refusal is not an error here (the tests check the outcome with their own expects).
    .then(Commands.literal('as')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.argument('command', Arguments.GREEDY_STRING.create(event)).executes(logged(ctx => {
          var target = Arguments.PLAYER.getResult(ctx, 'target')
          var cmd = String(Arguments.GREEDY_STRING.getResult(ctx, 'command')).replace(/^\//, '')
          var r = TtlCmd.runAs(target, cmd)
          // The parse error text ("Incorrect argument ...") goes to the log only: test-all counts it as a failure.
          if (r.error) console.info(`[ttl] as ${target.username}: /${cmd} not run: ${r.error}`)
          ctx.source.sendSystemMessage(Text.of(`as ${target.username}: /${cmd} -> ${r.error ? 'not run (see the log)' : r.result}`))
          return r.result > 0 ? 1 : 0
        }))))))
})
