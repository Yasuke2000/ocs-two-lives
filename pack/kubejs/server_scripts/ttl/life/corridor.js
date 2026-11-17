// Places the Spirit Corridor hall (blueprints/spirit_corridor_hall.py → structure ttl:spirit_corridor_hall)
// centred on 0 64 0, and keeps its chunks loaded so the arrival point always exists. Bump
// TTL_HALL_VERSION after changing the blueprint to rebuild the hall on the next start.
const TTL_HALL_VERSION = 2

ServerEvents.loaded(event => {
  var server = event.server
  var run = cmd => server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run ${cmd}`)
  run('forceload add -16 -16 16 16')
  if (server.persistentData.getInt('ttl.corridor.version') === TTL_HALL_VERSION) return
  // forceload takes effect on the next tick; placing before that hits unloaded chunks.
  server.scheduleInTicks(40, () => {
    run('fill -16 63 -16 16 86 16 minecraft:air')
    run('place template ttl:spirit_corridor_hall -15 64 -15')
    server.persistentData.putInt('ttl.corridor.version', TTL_HALL_VERSION)
    console.info(`[ttl] spirit corridor hall placed (version ${TTL_HALL_VERSION})`)
  })
})
