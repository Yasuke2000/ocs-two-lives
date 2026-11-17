// Tensura must not hand out a unique at first spawn (Life 1 is skill-less), and a unique has one holder.
ServerEvents.loaded(event => {
  event.server.runCommandSilent('gamerule noUniqueStart true')
  // Duplicates are allowed up to a cap per rarity; the registry (registry.js) enforces it, not Tensura.
  event.server.runCommandSilent('gamerule trulyUnique false')
  // The Great Sage addon's reincarnation scene plays over Tensura's reincarnation menu, which ttl-portals
  // only opens for the Life 2 rebirth (Life 1 never gets the menu). noUniqueStart keeps Tensura and the
  // scene from granting a unique; the registry grants it from the Last Wish afterwards.
  event.server.runCommandSilent('gamerule sageReincarnation true')
})
