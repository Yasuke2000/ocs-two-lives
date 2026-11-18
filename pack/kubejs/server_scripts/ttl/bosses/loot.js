// priority: 70
// Extra loot for summoned bosses (design/data/bosses.toml `drops` per boss), on top of the entity's own loot table.
// Only an entity with the ttl.boss tag counts, so a boss that appears some other way drops nothing extra. Coins, the
// Skill Core and the stage are paid to the fighters by TtlBoss.reward, not dropped here. With no `drops` anywhere in
// bosses.toml nothing is registered. Each drop is its own LootJS modifier: matchEntityCustom + randomChance + addLoot.
try {
  var ttlBossDrops = TtlBoss.defs().filter(d => (d.drops || []).length > 0)
  if (ttlBossDrops.length > 0) {
    LootJS.modifiers(event => {
      ttlBossDrops.forEach(def => {
        def.drops.forEach(d => {
          event.addEntityModifier(def.entity)
            .matchEntityCustom(e => e.getTags().contains('ttl.boss'))
            .randomChance(d.chance)
            .addLoot(Item.of(d.item, d.count))
        })
      })
    })
    console.info(`[ttl] boss: extra loot registered for ${ttlBossDrops.map(d => d.id).join(', ')}`)
  }
} catch (e) {
  console.error(`[ttl] boss: loot modifiers could not be registered: ${e}`)
}
