// Life 1 is a world without Tensura, so Tensura's energy rules must not touch mortals: since 18/11/2026 fresh Life 1
// players died within seconds of `tensura:magicule_poison` at Wayfarer's Rest (Tensura's ExistenceStorage applies
// it when a body holds more magicules than it can take). Clearing the effect alone was not enough (the damage
// lands in the same tick), so the damage itself is refused too. Root cause: design/decisions.md 18/11.
// Protected from poison and curse: everyone in the Mortal dimensions, and everyone who is not in Life 2, wherever
// they stand (a Life 1 or Corridor soul, or a brand-new player on the Tensura world spawn for the ~2 s before the
// first teleport, has no business in the soaked Jura forest and must not die of it). Only Life 2 souls feel the
// forest, and even they are sheltered from the poison (not the curse) around Tempest.
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
  },

  // Tempest's green sits in `tensura:ancient_forest` chunks, whose magicule is far above a fresh soul's 50 (Jura's
  // core keeps Tensura's real 20,000): a newcomer died of magicule poison the moment Life 2 began. Inside the same radius that
  // keeps hostile mobs away (mortal_spawns.js) the poison is refused too; outside it the world is as dangerous as
  // Tensura makes it.
  sheltered(player, poisonOnly) {
    return this.protects(player) || (poisonOnly && TtlSafeSpawns.inZone(player))
  },

  poison(text) {
    return String(text).indexOf('magicule_poison') >= 0
  },

  // Arrival grace: for `grace_seconds` (arrival.toml, default 20) after the rebirth a Life 2 soul takes no damage at all.
  // Blade Tigers and Barghests roam the safe rim too, and a fresh soul with 50 magicules died 2–6 s after landing
  // (staging 18/11/2026). The soul is still a target; it only has time to walk away. 0 turns the grace off.
  // Never against /kill (genericKill) or the void, and only in Life 2 (`ttl reset` drops the stamp as well).
  inGrace(player, source) {
    var at = Number(String(player.persistentData.getString('ttl.l2.arrived')) || 0)
    if (!at || TtlLife.phase(player) !== 'life2') return false
    var text = String(source)
    if (text.indexOf('genericKill') >= 0 || text.indexOf('outOfWorld') >= 0 || text.indexOf('fellOutOfWorld') >= 0) return false
    var cfg = (TtlData.arrival || {}).life2 || {}
    var secs = cfg.grace_seconds === undefined ? 20 : Number(cfg.grace_seconds)
    return Date.now() - at < secs * 1000
  }
}

EntityEvents.beforeHurt(event => {
  var entity = event.entity
  if (!entity.isPlayer()) return
  if (TtlMortalImmunity.inGrace(entity, event.source)) {
    event.cancel()
    return
  }
  if (!TtlMortalImmunity.refused(event.source)) return
  if (TtlMortalImmunity.sheltered(entity, TtlMortalImmunity.poison(event.source))) event.cancel()
})

ServerEvents.tick(event => {
  if (++TtlMortalImmunity.ticks % 2 !== 0) return
  var server = event.server
  server.getPlayerList().getPlayers().forEach(p => {
    var all = TtlMortalImmunity.protects(p)
    if (!all && !TtlSafeSpawns.inZone(p)) return
    ;(all ? TtlMortalImmunity.EFFECTS : ['tensura:magicule_poison']).forEach(id => server.runCommandSilent(`effect clear ${p.username} ${id}`))
  })
})
