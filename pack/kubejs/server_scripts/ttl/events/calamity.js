// priority: 70
// Start at the configured arena, then let the threat roam under the boss core's wild cap and cooldown.
TtlEvents.register({
  id: 'calamity_rising',
  start(server) {
    var why = text => {
      console.info(`[ttl] events: calamity_rising cannot start: ${text}`)
      return false
    }
    var boss = TtlBoss.def(TtlEvents.get('calamity_rising').boss_id)
    if (!boss) return why('no such boss')
    var arena = TtlBoss.arenaOf(server, boss, {})
    if (typeof arena === 'string') return why(arena)
    if (arena.dim !== TtlLife.OVERWORLD) return why(`the arena is in ${arena.dim}`)
    var region = TtlEvents.regionAt(arena.x, arena.z)
    if (!region) return why(`no canon region at ${arena.x} ${arena.z}`)
    var blocked = TtlWild.blocker(server, boss, true)
    if (blocked) return why(blocked)
    var refusal = TtlBoss.summon(server, boss.id, {
      by: 'event calamity_rising', event: 'calamity_rising', wild: true, region: region.name,
      dim: arena.dim, x: arena.x, y: arena.y, z: arena.z
    })
    if (refusal) {
      console.info(`[ttl] events: calamity_rising waits: ${refusal}`)
      return false
    }
    return { boss: boss.title, region: region.name, x: arena.x, z: arena.z }
  }
})
