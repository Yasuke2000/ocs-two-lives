// Tensura must not hand out a unique at first spawn (Life 1 is skill-less), and a unique has one holder.
ServerEvents.loaded(event => {
  event.server.runCommandSilent('gamerule noUniqueStart true')
  event.server.runCommandSilent('gamerule trulyUnique true')
})
