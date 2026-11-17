// /ttl choose <race>  — pick one of your Corridor offers and start Life 2.
// /ttl status         — show which life you are in.
// /ttl reset <player> — (op) send a player back to a fresh Life 1, for testing.
ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event
  const life = TtlLife

  const choose = ctx => {
    const player = ctx.source.getPlayerOrException()
    const server = ctx.source.getServer()
    const race = String(Arguments.STRING.getResult(ctx, 'race')).toLowerCase()
    if (life.phase(player) !== 'corridor') {
      player.tell(Text.red('You can only choose a race in the Spirit Corridor.'))
      return 0
    }
    const offers = player.persistentData.getString('ttl.offers').split(',')
    if (offers.indexOf(race) < 0) {
      player.tell(Text.red(`Not one of your offers: ${offers.join(', ')}`))
      return 0
    }
    const name = player.username
    server.runCommandSilent(`tensura edit race ${name} set tensura:${race}`)
    const skill = TtlRegistry.grantInnate(server, player)
    player.stages.remove('ttl.corridor')
    player.stages.add('ttl.life2')
    player.persistentData.remove('ttl.offers')
    server.runCommandSilent(`gamemode survival ${name}`)
    life.toOverworld(server, player)
    server.runCommandSilent(`tellraw @a ${JSON.stringify([
      { text: '[Voice of the World] ', color: 'gold' },
      { text: `${name} has been reborn as a ${race}.`, color: 'yellow' }
    ])}`)
    console.info(`[ttl] ${name} reborn as ${race} with ${skill}`)
    return 1
  }

  const status = ctx => {
    const player = ctx.source.getPlayerOrException()
    const phase = life.phase(player) || 'none'
    player.tell(Text.gold(`Life: ${phase}`))
    return 1
  }

  const reset = ctx => {
    const server = ctx.source.getServer()
    const target = Arguments.PLAYER.getResult(ctx, 'target')
    const name = target.username
    ;['ttl.life1', 'ttl.corridor', 'ttl.life2'].forEach(s => target.stages.remove(s))
    target.persistentData.remove('ttl.offers')
    server.runCommandSilent(`tensura reset ${name} race`)
    TtlRegistry.revokeAll(server, target)
    server.runCommandSilent(`clear ${name}`)
    server.runCommandSilent(`gamemode survival ${name}`)
    target.stages.add('ttl.life1')
    life.toMortal(server, target)
    console.info(`[ttl] ${name} reset to Life 1`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('choose')
      .then(Commands.argument('race', Arguments.STRING.create(event)).executes(choose)))
    .then(Commands.literal('status').executes(status))
    .then(Commands.literal('reset')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(reset))))
})
