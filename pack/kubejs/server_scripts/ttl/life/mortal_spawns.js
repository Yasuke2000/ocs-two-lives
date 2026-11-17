// The Mortal Realm is a world without Tensura: its mobs never spawn there (master plan §1).
EntityEvents.spawned(event => {
  const entity = event.entity
  if (entity.isPlayer()) return
  if (String(entity.level.dimension) !== TtlLife.MORTAL) return
  if (String(entity.type).startsWith('tensura:')) event.cancel()
})
