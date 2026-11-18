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

  // The Trial of Vengeance brings back whatever killed you.
  try {
    // KubeJS names the attacker `actual`; DamageSource.getEntity() is not visible to scripts.
    var killer = event.source.actual
    player.persistentData.putString('ttl.killer', killer ? String(killer.type) : '')
  } catch (e) {
    player.persistentData.putString('ttl.killer', '')
  }

  // Karma v1: judge the life that just ended before the Corridor rolls the race offers.
  TtlKarma.close(server, player)

  // Swap the stage now: void damage can fire another death before the tp next tick.
  player.stages.remove('ttl.life1')
  player.stages.add('ttl.corridor')
  console.info(`[ttl] ${player.username} died in Life 1 (${String(event.source)})`)
  TtlDiscord.life1Death(server, player.username)

  server.scheduleInTicks(1, () => {
    var name = player.username
    // Life 1 items must not reach Life 2: soulbound stacks are kept, banned ones stashed, the ender chest and Curios
    // slots emptied (life/mortal_banned.js). A failure must never trap the soul in Life 1.
    try {
      // The soul remembers its best enchantment while it is still on the body (life/carryover.js).
      try { if (typeof TtlSoul !== 'undefined') TtlSoul.lifeEnds(server, player) } catch (e) { console.error(`[ttl] ${name}: soul memory failed: ${e}`) }
      TtlStash.lifeEnds(server, player)
    } catch (e) {
      console.error(`[ttl] ${name}: Life 1 strip failed: ${e}`)
    }
    server.runCommandSilent(`quietly clear ${name}`)
    life.toCorridor(server, player)
    server.runCommandSilent(`quietly gamemode adventure ${name}`)
    TtlCorridor.begin(server, player)
  })
  return event.cancel()
})
