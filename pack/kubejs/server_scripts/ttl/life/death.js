// Life 1 is hardcore: the first death is cancelled and the soul moves to the Spirit Corridor.
// Cancelling (instead of letting the player respawn) keeps XP, advancements and Tensura data intact
// and skips Tensura's own death penalty.
EntityEvents.death('minecraft:player', event => {
  const player = event.entity
  const server = event.server
  const life = global.ttlLife
  const phase = life.phase(player)
  if (phase !== 'life1' && phase !== 'corridor') return

  player.setHealth(player.getMaxHealth())
  player.removeAllEffects()
  player.clearFire()
  player.resetFallDistance()

  if (phase === 'corridor') {
    // Void or /kill inside the Corridor: just put them back in the hall.
    server.scheduleInTicks(1, () => life.toCorridor(server, player))
    return event.cancel()
  }

  // Swap the stage now: void damage can fire another death before the tp next tick.
  player.stages.remove('ttl.life1')
  player.stages.add('ttl.corridor')
  const offers = life.rollOffers()
  player.persistentData.putString('ttl.offers', offers.join(','))
  console.info(`[ttl] ${player.username} died in Life 1 (${event.source.getMsgId()}), offers: ${offers.join(', ')}`)

  server.scheduleInTicks(1, () => {
    const name = player.username
    server.runCommandSilent(`clear ${name}`)
    life.toCorridor(server, player)
    server.runCommandSilent(`gamemode adventure ${name}`)
    server.runCommandSilent(`title ${name} title {"text":"Your first life has ended","color":"dark_red"}`)
    server.runCommandSilent(`title ${name} subtitle {"text":"The Voice of the World offers you a new body","color":"gray"}`)
    const buttons = offers.map(race => ({
      text: `[${race.charAt(0).toUpperCase()}${race.slice(1)}]`,
      color: 'aqua',
      clickEvent: { action: 'run_command', value: `/ttl choose ${race}` },
      hoverEvent: { action: 'show_text', contents: `Reincarnate as ${race}` }
    }))
    const line = [{ text: '[Voice of the World] Choose your new race: ', color: 'gold' }]
    buttons.forEach(b => line.push(b, ' '))
    server.runCommandSilent(`tellraw ${name} ${JSON.stringify(line)}`)
  })
  return event.cancel()
})
