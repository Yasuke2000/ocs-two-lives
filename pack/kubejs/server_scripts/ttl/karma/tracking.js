// Karma v1: creates the stat objectives and records what vanilla statistics don't (karma.js, karma.toml).
// Tracked values live in player persistentData and only move while the player is in Life 1:
//   ttl.l1.far    farthest horizontal distance from Wayfarer's Rest reached in the Mortal Realm (blocks)
//   ttl.l1.nether 1 once seen in the Mortal Nether · ttl.l1.end 1 once seen in the Mortal End
//   ttl.l1.adv    advancements with a display earned during Life 1 (recipe unlocks have none)
ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlKarma.ensure(server)
  } catch (e) {
    console.error(`[ttl] karma: creating the stat objectives failed: ${e}`)
  }
  var every = Math.max(1, TtlData.karma.track_seconds) * 20
  var loop = () => server.scheduleInTicks(every, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlKarmaTrack.sample(server, p)
      } catch (e) {
        console.error(`[ttl] karma: sampling ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})

const TtlKarmaTrack = {
  // Wayfarer's Rest (mortal_spawn.js stores "x y z"), or 0 0 before it has been placed.
  home(server) {
    var spawn = String(server.persistentData.getString('ttl.mortal.spawn')).split(' ')
    return spawn.length === 3 ? { x: Number(spawn[0]), z: Number(spawn[2]) } : { x: 0, z: 0 }
  },

  sample(server, player) {
    if (TtlLife.phase(player) !== 'life1') return
    var data = player.persistentData
    var keys = TtlKarma.TRACKED
    var dim = TtlLife.dimensionOf(player)
    if (dim === 'ttl:mortal_nether') data.putInt(keys.nether, 1)
    if (dim === 'ttl:mortal_end') data.putInt(keys.end, 1)
    if (dim !== TtlLife.MORTAL) return
    var home = this.home(server)
    var dx = player.getX() - home.x
    var dz = player.getZ() - home.z
    var far = Math.floor(Math.sqrt(dx * dx + dz * dz))
    if (far > data.getInt(keys.far)) data.putInt(keys.far, far)
  }
}

PlayerEvents.advancement(event => {
  var player = event.player
  if (TtlLife.phase(player) !== 'life1') return
  try {
    if (!event.advancement.hasDisplay()) return
  } catch (e) {
    return
  }
  var key = TtlKarma.TRACKED.advancements
  player.persistentData.putInt(key, player.persistentData.getInt(key) + 1)
})
