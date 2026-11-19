// After ttl-portals regenerated dimensions (WorldReset.java, marker <world>/ttl-reset.txt) it runs
// `/ttl worldreset <ids>` (comma-separated; a greedy argument, plain strings reject `:` and `,`): Wayfarer's
// Rest and the Tensura world spawn are placed again, and players whose position belongs to the old terrain are
// moved to the new spawn on their next login.
const TtlWorldReset = {
  apply(server, ids) {
    var data = server.persistentData
    data.putString('ttl.world.epoch', String(Date.now()))
    if (ids.indexOf(TtlLife.MORTAL) >= 0) {
      ;['ttl.mortal.y', 'ttl.mortal.spawn', 'ttl.mortal.version'].forEach(k => data.remove(k))
      TtlMortalSpawn.run(server, 'forceload add -16 -16 16 16')
      server.scheduleInTicks(40, () => {
        try {
          TtlMortalSpawn.place(server)
        } catch (e) {
          console.error(`[ttl] world reset: mortal spawn placement failed: ${e}`)
        }
        TtlMortalSpawn.run(server, 'forceload remove -16 -16 16 16')
      })
    }
    if (ids.indexOf(TtlLife.OVERWORLD) >= 0) {
      // Life 2 begins on the safe rim of Jura (life/arrival.js grounds it again and sets the world spawn); without
      // one, at Tempest (TtlTempest.LANDMARK, the tempest anchor of design/data/anchors.toml).
      var arrival = typeof TtlArrival !== 'undefined' && TtlArrival.active()
      if (arrival) {
        try {
          TtlArrival.reset(server)
        } catch (e) {
          console.error(`[ttl] world reset: arrival grounding failed: ${e}`)
        }
      } else {
        var tx = TtlTempest.LANDMARK.x
        var tz = TtlTempest.LANDMARK.z
        server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run forceload add ${tx - 16} ${tz - 16} ${tx + 16} ${tz + 16}`)
        server.scheduleInTicks(40, () => {
          server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} positioned ${tx} 0 ${tz} positioned over motion_blocking_no_leaves run setworldspawn ~ ~ ~`)
          server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run forceload remove ${tx - 16} ${tz - 16} ${tx + 16} ${tz + 16}`)
        })
      }
      server.persistentData.remove('ttl.dwargon.version')
      TtlDwargon.schedule(server)
      server.persistentData.remove('ttl.tempest.version')
      TtlTempest.schedule(server)
      TtlLandmarks.reset(server)
    }
    try {
      if (typeof TtlBuilds !== 'undefined') TtlBuilds.reset(server, ids)
    } catch (e) {
      console.error(`[ttl] world reset: canon builds not rescheduled: ${e}`)
    }
    console.info(`[ttl] world reset applied: ${ids.join(', ')}`)
  },

  // Players who last played before the reset stand on terrain that no longer exists.
  relocate(server, player) {
    var epoch = Number(String(server.persistentData.getString('ttl.world.epoch')) || 0)
    var data = player.persistentData
    if (!epoch || Number(String(data.getString('ttl.world.epoch')) || 0) >= epoch) return
    data.putString('ttl.world.epoch', String(epoch))
    var phase = TtlLife.phase(player)
    var dim = TtlLife.dimensionOf(player)
    if (phase === 'life1' && TtlLife.isMortal(dim) && data.getLong('ttl.l1.start') < epoch) {
      TtlLife.toMortal(server, player)
    } else if (phase === 'life2' && dim === TtlLife.OVERWORLD) {
      TtlLife.toOverworld(server, player)
    } else {
      return
    }
    TtlCorridor.voice(server, player.username, 'The world has been remade while you were away.')
    console.info(`[ttl] world reset: moved ${player.username} (${phase}) to the new spawn`)
  }
}

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  // After join.js has put new players in place (20 ticks).
  server.scheduleInTicks(30, () => TtlWorldReset.relocate(server, player))
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  event.register(Commands.literal('ttl')
    .then(Commands.literal('worldreset')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('ids', Arguments.GREEDY_STRING.create(event)).executes(ctx => {
        try {
          TtlWorldReset.apply(ctx.source.getServer(), String(Arguments.GREEDY_STRING.getResult(ctx, 'ids')).split(','))
          return 1
        } catch (e) {
          console.error(`[ttl] world reset failed: ${e}`)
          return 0
        }
      }))))
})
