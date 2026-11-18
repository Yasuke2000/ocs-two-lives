// priority: 70
// Choose one represented canon region, or any mapped nation when nobody is adventuring there.
// Check the victim's current column on every hit/drop, so crossing a border ends the hazard immediately.
const TtlStorm = {
  start(server) {
    var regions = {}
    server.getPlayerList().getPlayers().forEach(p => {
      if (TtlLife.phase(p) !== 'life2' || TtlLife.dimensionOf(p) !== 'minecraft:overworld') return
      var region = TtlEvents.regionAt(Math.floor(p.getX()), Math.floor(p.getZ()))
      if (region) regions[region.key] = region.name
    })
    if (!Object.keys(regions).length) {
      var grid = TtlEvents.grid()
      if (!grid) return false
      grid.regionMap().forEach((key, region) => { regions[String(key)] = String(region.name()) })
    }
    var keys = Object.keys(regions)
    if (!keys.length) return false
    var key = keys[Math.floor(Math.random() * keys.length)]
    return { key: key, region: regions[key] }
  },

  contains(entity) {
    if (String(entity.level.dimension) !== 'minecraft:overworld') return false
    var entry = TtlEvents.read(entity.server, 'ttl.events.active', {}).magicule_storm
    if (!entry || entry.e <= Date.now()) return false
    var region = TtlEvents.regionAt(Math.floor(entity.getX()), Math.floor(entity.getZ()))
    return !!region && region.key === entry.d.key
  }
}
TtlEvents.register({ id: 'magicule_storm', start: server => TtlStorm.start(server) })

EntityEvents.beforeHurt('minecraft:player', event => {
  var attacker = event.source.actual
  if (!attacker || !attacker.isMonster() || TtlLife.phase(event.entity) !== 'life2') return
  if (TtlStorm.contains(event.entity)) event.setDamage(event.damage * TtlEvents.get('magicule_storm').damage_multiplier)
})

LootJS.modifiers(event => {
  var def = TtlEvents.get('magicule_storm')
  event.addTableModifier(LootType.ENTITY)
    .matchPlayerCustom(p => TtlLife.phase(p) === 'life2')
    .matchEntityCustom(e => e.isMonster() && TtlStorm.contains(e))
    .randomChance(def.crystal_chance)
    .addLoot(Item.of(def.crystal))
})
