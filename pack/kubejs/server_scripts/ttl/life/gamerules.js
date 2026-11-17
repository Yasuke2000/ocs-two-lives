// Tensura must not hand out a unique at first spawn (Life 1 is skill-less), and a unique has one holder.
ServerEvents.loaded(event => {
  event.server.runCommandSilent('gamerule noUniqueStart true')
  event.server.runCommandSilent('gamerule trulyUnique true')
  // The Great Sage addon's own reincarnation scene replaces Tensura's start menu and grants uniques from
  // drawn wishes at first join, i.e. in Life 1. The Corridor owns rebirth until that scene is wired in.
  event.server.runCommandSilent('gamerule sageReincarnation false')
})
