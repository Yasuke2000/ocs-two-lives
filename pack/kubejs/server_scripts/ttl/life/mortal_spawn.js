// Places Wayfarer's Rest (blueprints/mortal_spawn.py → structure ttl:mortal_spawn) on the surface at 0, 0
// of the Mortal Realm, where every Life 1 starts (TtlLife.toMortal). Bump TTL_MORTAL_SPAWN_VERSION after
// changing the blueprint to rebuild it on the next start. The plaza height is measured once and kept:
// after the first placement the surface at 0, 0 is the shrine roof.
const TTL_MORTAL_SPAWN_VERSION = 1

const TtlMortalSpawn = {
  PROBE: 'ttl_spawn_probe',

  run(server, cmd) {
    server.runCommandSilent(`execute in ${TtlLife.MORTAL} run ${cmd}`)
  },

  // The surface at 0, 0: a marker dropped onto the heightmap, read back, removed. Water counts as surface,
  // so an ocean spawn becomes a platform rather than a sunken plaza.
  surfaceY(server) {
    server.runCommandSilent(`execute in ${TtlLife.MORTAL} positioned 0 0 0 positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~ {Tags:["${this.PROBE}"]}`)
    var y = null
    var probe = this.PROBE
    server.getLevel(TtlLife.MORTAL).getEntities().forEach(e => {
      if (e.getTags().contains(probe)) y = Math.floor(e.getY())
    })
    this.run(server, `kill @e[type=minecraft:marker,tag=${probe}]`)
    return y
  },

  place(server) {
    var data = server.persistentData
    // y is the arrival height: one above the plaza, which is layer 6 of the structure.
    var y = data.contains('ttl.mortal.y') ? data.getInt('ttl.mortal.y') : this.surfaceY(server)
    if (y === null) {
      console.warn('[ttl] mortal spawn: no surface found at 0 0; Life 1 keeps spreading players instead')
      return
    }
    this.run(server, `place template ttl:mortal_spawn -14 ${y - 7} -14`)
    data.putInt('ttl.mortal.y', y)
    data.putString('ttl.mortal.spawn', `0.5 ${y} 5.5`)
    data.putInt('ttl.mortal.version', TTL_MORTAL_SPAWN_VERSION)
    console.info(`[ttl] mortal spawn placed at y ${y} (version ${TTL_MORTAL_SPAWN_VERSION})`)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  if (server.persistentData.getInt('ttl.mortal.version') === TTL_MORTAL_SPAWN_VERSION) return
  TtlMortalSpawn.run(server, 'forceload add -16 -16 16 16')
  // forceload takes effect on the next tick; the heightmap and placement need the chunks loaded.
  server.scheduleInTicks(40, () => {
    try {
      TtlMortalSpawn.place(server)
    } catch (e) {
      console.error(`[ttl] mortal spawn placement failed: ${e}`)
    }
    TtlMortalSpawn.run(server, 'forceload remove -16 -16 16 16')
  })
})
