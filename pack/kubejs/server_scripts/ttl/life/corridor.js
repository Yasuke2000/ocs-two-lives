// Builds the Spirit Corridor hall once: a lit quartz floor inside a barrier box, chunks kept loaded
// so the tp target always exists. Replace with a real build later; the flag stops a rebuild over it.
ServerEvents.loaded(event => {
  const server = event.server
  if (server.persistentData.getBoolean('ttl.corridor.built')) return
  const run = cmd => server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run ${cmd}`)
  run('forceload add -12 -12 12 12')
  // forceload takes effect on the next tick; filling before that hits unloaded chunks.
  server.scheduleInTicks(40, () => {
    run('fill -11 64 -11 11 74 11 minecraft:barrier hollow')
    run('fill -10 64 -10 10 64 10 minecraft:quartz_block')
    run('fill -10 64 -10 10 64 10 minecraft:sea_lantern replace minecraft:quartz_block')
    run('fill -9 64 -9 9 64 9 minecraft:smooth_quartz')
    run('setblock 0 64 0 minecraft:sea_lantern')
    server.persistentData.putBoolean('ttl.corridor.built', true)
    console.info('[ttl] spirit corridor hall built')
  })
})
