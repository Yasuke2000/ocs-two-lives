// priority: 70
// Start at the configured arena, then let the threat roam under the boss core's wild cap and cooldown.
TtlEvents.register({
  id: 'calamity_rising',
  start(server) {
    var boss = TtlBoss.def(TtlEvents.get('calamity_rising').boss_id)
    if (!boss) return false
    var arena = TtlBoss.arenaOf(server, boss, {})
    if (typeof arena === 'string' || arena.dim !== TtlLife.OVERWORLD) return false
    var region = TtlEvents.regionAt(arena.x, arena.z)
    if (!region || TtlWild.blocker(server, boss, true)) return false
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
