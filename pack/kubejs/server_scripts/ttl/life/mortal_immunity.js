// Life 1 is a world without Tensura, so Tensura's energy rules must not touch mortals: since 18/11/2026 fresh Life 1
// players died within seconds of `tensura:magicule_poison` at Wayfarer's Rest (Tensura's ExistenceStorage applies
// it when a body holds more magicules than it can take). Clearing the effect alone was not enough (the damage
// lands in the same tick), so the damage itself is refused too. Root cause: design/decisions.md 18/11.
// Protected: everyone in the Mortal dimensions, and everyone who is not in Life 2, wherever they stand (a Life 1
// or Corridor soul, or a brand-new player on the Tensura world spawn for the ~2 s before the first teleport, has
// no business in the soaked Jura forest and must not die of it). Only Life 2 souls feel the forest.
const TtlMortalImmunity = {
  EFFECTS: ['tensura:magicule_poison', 'tensura:curse'],
  // Matched against the DamageSource's text form, "DamageSource (tensura.magicule_poison)": Rhino doesn't
  // reliably expose getMsgId() here.
  SOURCES: ['tensura.magicule_poison', 'tensura.curse'],
  ticks: 0,

  refused(source) {
    var text = String(source)
    return this.SOURCES.some(s => text.indexOf(s) >= 0)
  },

  // Mortal dimensions, or any phase but Life 2 (TtlLife.phase is null before the first join has set a stage).
  protects(player) {
    return TtlLife.isMortal(TtlLife.dimensionOf(player)) || TtlLife.phase(player) !== 'life2'
  }
}

EntityEvents.beforeHurt(event => {
  var entity = event.entity
  if (!entity.isPlayer()) return
  if (!TtlMortalImmunity.protects(entity)) return
  if (TtlMortalImmunity.refused(event.source)) event.cancel()
})

ServerEvents.tick(event => {
  if (++TtlMortalImmunity.ticks % 2 !== 0) return
  var server = event.server
  server.getPlayerList().getPlayers().forEach(p => {
    if (!TtlMortalImmunity.protects(p)) return
    TtlMortalImmunity.EFFECTS.forEach(id => server.runCommandSilent(`effect clear ${p.username} ${id}`))
  })
})
