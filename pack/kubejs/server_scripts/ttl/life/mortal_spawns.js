// Life 1's dimensions are a world without Tensura: its mobs never spawn there (master plan §1).
EntityEvents.spawned(event => {
  const entity = event.entity
  if (entity.isPlayer()) return
  if (!TtlLife.isMortal(entity.level.dimension)) return
  if (String(entity.type).startsWith('tensura:')) event.cancel()
})
