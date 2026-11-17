// Players:  /ttl wish <id> · /ttl trial · /ttl answer <word> · /ttl choose <race> · /ttl unique <skill> · /ttl status
// Ops:      /ttl inspect <player> (answers over RCON) · /ttl reset <player> (back to a fresh Life 1)
//           /ttl registry · /ttl registry free <skill> (release a unique whose holder is gone)
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
        `strikes=${data.getInt('ttl.trial.strikes')}`, `correct=${data.getInt('ttl.trial.correct')}`, `food=${target.getFoodData().getFoodLevel()}`])
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
    server.runCommandSilent(`tensura reset ${name} race`)
    TtlRegistry.revokeAll(server, target)
    server.runCommandSilent(`clear ${name}`)
    server.runCommandSilent(`gamemode survival ${name}`)
    target.stages.add('ttl.life1')
    life.toMortal(server, target)
    console.info(`[ttl] ${name} reset to Life 1`)
    ctx.source.sendSystemMessage(Text.of(`${name} reset to Life 1`))
    return 1
  }

  var registryList = ctx => {
    var held = TtlRegistry.held(ctx.source.getServer())
    ctx.source.sendSystemMessage(Text.of(`Held uniques: ${held.length ? held.join(', ') : 'none'}`))
    return 1
  }

  var registryFree = ctx => {
    var server = ctx.source.getServer()
    var skill = `tensura:${word(ctx, 'skill')}`
    var held = TtlRegistry.held(server).filter(id => id !== skill)
    server.persistentData.putString('ttl.reg.held', held.join(','))
    console.info(`[ttl] registry: ${skill} released by an admin`)
    ctx.source.sendSystemMessage(Text.of(`Released ${skill}`))
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('wish')
      .then(Commands.argument('id', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.wish(server, player, word(ctx, 'id'))))))
    .then(Commands.literal('trial')
      .executes(step((server, player) => TtlTrial.start(server, player))))
    .then(Commands.literal('answer')
      .then(Commands.argument('word', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlTrial.answer(server, player, word(ctx, 'word'))))))
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
    .then(Commands.literal('registry')
      .requires(src => src.hasPermission(2))
      .executes(logged(registryList))
      .then(Commands.literal('free')
        .then(Commands.argument('skill', Arguments.STRING.create(event)).executes(logged(registryFree)))))
    .then(Commands.literal('reset')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(reset)))))
})
