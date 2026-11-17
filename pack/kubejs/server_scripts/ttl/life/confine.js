// Each life keeps to its own worlds, whatever the route (a Tensura portal, a mod's teleport, an op command):
// Life 1 stays in the Mortal dimensions, Life 2 never enters them. The Spirit Corridor is shared ground for
// deaths, trials and test setups. Checked every 5 seconds rather than hooked, so no route can slip past.
const TtlConfine = {
  check(server, player) {
    var life = TtlLife
    var phase = life.phase(player)
    var dim = life.dimensionOf(player)
    if (dim === life.CORRIDOR || player.isSpectator()) return
    if (phase === 'life1' && !life.isMortal(dim)) {
      life.toMortal(server, player)
      TtlCorridor.voice(server, player.username, 'Your first life is bound to the mortal world.')
      console.info(`[ttl] confine: ${player.username} (life 1) left ${dim}, back to the Mortal Realm`)
    } else if (phase === 'life2' && life.isMortal(dim)) {
      life.toOverworld(server, player)
      TtlCorridor.voice(server, player.username, 'The mortal world is closed to a soul that has already died once.')
      console.info(`[ttl] confine: ${player.username} (life 2) left ${dim}, back to the Tensura world`)
    }
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(100, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlConfine.check(server, p)
      } catch (e) {
        console.error(`[ttl] confine check failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})
