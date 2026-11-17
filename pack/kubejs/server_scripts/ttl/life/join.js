// New players start Life 1 in the Mortal Realm; returning players are put back where their life belongs.
PlayerEvents.loggedIn(event => {
  const { player, server } = event
  const life = global.ttlLife
  const phase = life.phase(player)

  if (phase === null) {
    player.stages.add('ttl.life1')
    player.persistentData.putLong('ttl.l1.start', server.overworld().getGameTime())
    // The login tp lands before the client finishes joining unless it waits a moment.
    server.scheduleInTicks(20, () => {
      life.toMortal(server, player)
      player.tell(Text.gold('You are human, and you only live once here. Die, and your soul moves on.'))
    })
    console.info(`[ttl] ${player.username} started Life 1`)
    return
  }

  const dim = life.dimensionOf(player)
  if (phase === 'corridor' && dim !== life.CORRIDOR) server.scheduleInTicks(20, () => life.toCorridor(server, player))
  if (phase === 'life1' && dim !== life.MORTAL) server.scheduleInTicks(20, () => life.toMortal(server, player))
})

// Fallback if a Life 1 death slipped past death.js: the respawn lands in the Corridor anyway.
PlayerEvents.respawned(event => {
  const { player, server } = event
  const phase = global.ttlLife.phase(player)
  if (phase === 'life1' || phase === 'corridor') {
    server.scheduleInTicks(1, () => global.ttlLife.toCorridor(server, player))
  }
})
