// Life 1 is a world without Tensura, so Tensura's energy rules must not touch mortals: since 18/11/2026 fresh Life 1
// players died within seconds of `tensura:magicule_poison` at Wayfarer's Rest (Tensura's ExistenceStorage applies
// it when a body holds more magicules than it can take). Clearing the effect alone was not enough (the damage
// lands in the same tick), so the damage itself is refused too. Root cause: design/decisions.md 18/11.
const TtlMortalImmunity = {
  EFFECTS: ['tensura:magicule_poison', 'tensura:curse'],
  // Matched against the DamageSource's text form, "DamageSource (tensura.magicule_poison)": Rhino doesn't
  // reliably expose getMsgId() here.
  SOURCES: ['tensura.magicule_poison', 'tensura.curse'],
  ticks: 0,

  refused(source) {
    var text = String(source)
    return this.SOURCES.some(s => text.indexOf(s) >= 0)
  }
}

EntityEvents.beforeHurt(event => {
  var entity = event.entity
  if (!entity.isPlayer()) return
  if (!TtlLife.isMortal(entity.level.dimension)) return
  if (TtlMortalImmunity.refused(event.source)) event.cancel()
})

ServerEvents.tick(event => {
  if (++TtlMortalImmunity.ticks % 2 !== 0) return
  var server = event.server
  server.getPlayerList().getPlayers().forEach(p => {
    if (!TtlLife.isMortal(TtlLife.dimensionOf(p))) return
    TtlMortalImmunity.EFFECTS.forEach(id => server.runCommandSilent(`effect clear ${p.username} ${id}`))
  })
})
