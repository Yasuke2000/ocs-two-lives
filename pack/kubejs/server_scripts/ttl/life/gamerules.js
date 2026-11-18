// Tensura must not hand out a unique at first spawn (Life 1 is skill-less), and a unique has one holder.
ServerEvents.loaded(event => {
  event.server.runCommandSilent('gamerule noUniqueStart true')
  // Duplicates are allowed up to a cap per rarity; the registry (registry.js) enforces it, not Tensura.
  event.server.runCommandSilent('gamerule trulyUnique false')
  // The Great Sage addon's reincarnation scene plays over Tensura's reincarnation menu, which ttl-portals
  // only opens for the Life 2 rebirth (Life 1 never gets the menu). noUniqueStart stops Tensura's own
  // unique, but the scene's wishes still grant skills (design/manas-integration.md §3.1), on purpose:
  // registry.js reconciles them against the caps. Legendaries are kept out of its pool by
  // pack/config/greatsage-common.toml (reincarnationExcludedSkills).
  event.server.runCommandSilent('gamerule sageReincarnation true')
  // Tensura's own Life 2 resets (Reset Counter: bosses, evolution, awakening): each reset earns a bonus unique,
  // and skills are locked per reset (owner's choice). Bonus uniques still pass the registry reconcile (caps).
  event.server.runCommandSilent('gamerule resetCounterBonusUnique 1')
  event.server.runCommandSilent('gamerule resetPerSkillLock 1')
})
