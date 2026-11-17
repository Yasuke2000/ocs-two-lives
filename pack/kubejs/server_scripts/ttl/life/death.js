// Life 1 is hardcore: the first death is cancelled and the soul moves to the Spirit Corridor.
// Cancelling (instead of letting the player respawn) keeps XP, advancements and Tensura data intact
// and skips Tensura's own death penalty.
EntityEvents.death('minecraft:player', event => {
  var player = event.entity
  var server = event.server
  var life = TtlLife
  var phase = life.phase(player)
  if (phase !== 'life1' && phase !== 'corridor') return

  player.setHealth(player.getMaxHealth())
  player.removeAllEffects()
  player.clearFire()
  player.resetFallDistance()

  if (phase === 'corridor') {
    // Void, /kill or a lost Trial fight inside the Corridor: back to the hall, Trial failed if running.
    TtlTrial.onPlayerDeath(server, player)
    server.scheduleInTicks(1, () => life.toCorridor(server, player))
    return event.cancel()
  }

  // Swap the stage now: void damage can fire another death before the tp next tick.
  player.stages.remove('ttl.life1')
  player.stages.add('ttl.corridor')
  console.info(`[ttl] ${player.username} died in Life 1 (${String(event.source)})`)

  server.scheduleInTicks(1, () => {
    var name = player.username
    server.runCommandSilent(`clear ${name}`)
    life.toCorridor(server, player)
    server.runCommandSilent(`gamemode adventure ${name}`)
    server.runCommandSilent(`title ${name} title {"text":"Your first life has ended","color":"dark_red"}`)
    server.runCommandSilent(`title ${name} subtitle {"text":"The Voice of the World is listening","color":"gray"}`)
    TtlCorridor.begin(server, player)
  })
  return event.cancel()
})
