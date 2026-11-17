// New players start Life 1 in the Mortal Realm; returning players are put back where their life belongs.
PlayerEvents.loggedIn(event => {
  var { player, server } = event
  var life = TtlLife
  var phase = life.phase(player)

  if (phase === null) {
    player.stages.add('ttl.life1')
    player.persistentData.putLong('ttl.l1.start', Date.now())
    // The login tp lands before the client finishes joining unless it waits a moment.
    server.scheduleInTicks(20, () => {
      life.makeHuman(server, player)
      life.toMortal(server, player)
      TtlCorridor.say(server, player.username, 'hajimari')
      player.tell(Text.gold('You are human, and you only live once here. Die, and your soul moves on.'))
    })
    console.info(`[ttl] ${player.username} started Life 1`)
    return
  }

  // A restart during the Trial ends it; count it as failed rather than leave the player stuck.
  if (phase === 'corridor' && player.persistentData.getString('ttl.step') === 'trial') {
    player.persistentData.putBoolean('ttl.trial.done', true)
    player.persistentData.putBoolean('ttl.trial.passed', false)
    player.persistentData.putString('ttl.step', 'race')
    server.runCommandSilent(`quietly clear ${player.username}`)
  }
  if (phase === 'corridor') server.scheduleInTicks(40, () => TtlCorridor.voice(server, player.username, 'Your soul is still waiting between lives.'))
  if (phase === 'corridor') TtlCorridor.showLater(server, player)

  var dim = life.dimensionOf(player)
  if (phase === 'corridor' && dim !== life.CORRIDOR) server.scheduleInTicks(20, () => life.toCorridor(server, player))
  if (phase === 'life1' && !life.isMortal(dim)) server.scheduleInTicks(20, () => life.toMortal(server, player))
})

// Fallback if a Life 1 death slipped past death.js: the respawn lands in the Corridor anyway.
PlayerEvents.respawned(event => {
  var { player, server } = event
  var phase = TtlLife.phase(player)
  if (phase === 'life1' || phase === 'corridor') {
    server.scheduleInTicks(1, () => TtlLife.toCorridor(server, player))
  }
})
