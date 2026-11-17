// Players:  /ttl wish <id> · /ttl trial · /ttl choose <race> · /ttl unique <skill> · /ttl status
// Ops:      /ttl inspect <player> (answers over RCON) · /ttl reset <player> (back to a fresh Life 1)
ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event
  const life = TtlLife

  // Corridor steps return an error message, or null when the step went through.
  const step = fn => ctx => {
    const player = ctx.source.getPlayerOrException()
    if (life.phase(player) !== 'corridor') {
      player.tell(Text.red('This only works in the Spirit Corridor.'))
      return 0
    }
    const error = fn(ctx.source.getServer(), player, ctx)
    if (error) {
      player.tell(Text.red(error))
      return 0
    }
    return 1
  }
  const word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()

  const status = ctx => {
    const player = ctx.source.getPlayerOrException()
    const step = player.persistentData.getString('ttl.step')
    player.tell(Text.gold(`Life: ${life.phase(player) || 'none'}${step ? ` (${step})` : ''}`))
    return 1
  }

  const inspect = ctx => {
    const target = Arguments.PLAYER.getResult(ctx, 'target')
    const data = target.persistentData
    const fields = ['ttl.step', 'ttl.wish', 'ttl.offers', 'ttl.race', 'ttl.uniqueOptions', 'ttl.uniques']
      .map(k => `${k}=${data.getString(k)}`)
      .concat([`ttl.trial.done=${data.getBoolean('ttl.trial.done')}`, `ttl.trial.passed=${data.getBoolean('ttl.trial.passed')}`])
    const line = `${target.username}: phase=${life.phase(target)} dim=${life.dimensionOf(target)} ${fields.join(' ')}`
    ctx.source.sendSuccess(() => Text.of(line), false)
    return 1
  }

  const reset = ctx => {
    const server = ctx.source.getServer()
    const target = Arguments.PLAYER.getResult(ctx, 'target')
    const name = target.username
    ;['ttl.life1', 'ttl.corridor', 'ttl.life2'].forEach(s => target.stages.remove(s))
    TtlCorridor.KEYS.forEach(k => target.persistentData.remove(k))
    server.runCommandSilent(`tensura reset ${name} race`)
    TtlRegistry.revokeAll(server, target)
    server.runCommandSilent(`clear ${name}`)
    server.runCommandSilent(`gamemode survival ${name}`)
    target.stages.add('ttl.life1')
    life.toMortal(server, target)
    console.info(`[ttl] ${name} reset to Life 1`)
    ctx.source.sendSuccess(() => Text.of(`${name} reset to Life 1`), true)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('wish')
      .then(Commands.argument('id', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.wish(server, player, word(ctx, 'id'))))))
    .then(Commands.literal('trial')
      .executes(step((server, player) => TtlTrial.start(server, player))))
    .then(Commands.literal('choose')
      .then(Commands.argument('race', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.choose(server, player, word(ctx, 'race'))))))
    .then(Commands.literal('unique')
      .then(Commands.argument('skill', Arguments.STRING.create(event))
        .executes(step((server, player, ctx) => TtlCorridor.unique(server, player, word(ctx, 'skill'))))))
    .then(Commands.literal('status').executes(status))
    .then(Commands.literal('inspect')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(inspect)))
    .then(Commands.literal('reset')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(reset))))
})
