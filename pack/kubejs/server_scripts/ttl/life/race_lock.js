// priority: 60
// Life 1 is always Human (#4). Tensura's Character/Race Reset Scroll opens a race menu fed by `Races.startingRaces`
// (pack/config/tensura/reincarnation_config.toml), which now lists the normal races so a Life 2 soul can reset into
// them. A Life 1 soul must never get that far:
//   1. every Tensura item is banned in the Mortal dimensions (design/data/mortal_banned.toml: a right click on a scroll
//      is cancelled by mortal_banned.js, and a scroll that gets onto the body is stashed);
//   2. this loop is the net under that: a Life 1 soul whose race is anything but Human (a scroll through some other
//      route, a command, a mod) is set back to Human within 5 seconds.
// Life 2 and the Corridor are never touched. Ops: /ttl racelock <player> [enforce | expect <race id>] (bot tests).
const TtlRaceLock = {
  HUMAN: 'tensura:human',

  api() {
    if (this.apiObj !== undefined) return this.apiObj
    try {
      this.apiObj = Java.loadClass('io.github.manasmods.manascore.race.api.RaceAPI')
    } catch (e) {
      console.error(`[ttl] race lock: ManasCore RaceAPI unavailable, Life 1 is only protected by the item ban: ${e}`)
      this.apiObj = null
    }
    return this.apiObj
  },

  // The soul's current Tensura race id ('' when unknown or not set yet).
  race(player) {
    var a = this.api()
    if (!a) return ''
    try {
      var r = a.getRaceFrom(player).getRace()
      return r.isPresent() ? String(r.get().getRaceId()) : ''
    } catch (e) {
      console.warn(`[ttl] race lock: reading ${player.username}'s race failed: ${e}`)
      return ''
    }
  },

  // Sets a Life 1 soul back to Human when it is anything else. Returns true when it had to.
  enforce(server, player) {
    if (TtlLife.phase(player) !== 'life1') return false
    var race = this.race(player)
    // '' = not set yet (join.js sets Human a second after the first login): nothing to undo.
    if (race === '' || race === this.HUMAN) return false
    console.warn(`[ttl] race lock: ${player.username} (life 1) was ${race}, set back to human`)
    TtlLife.makeHuman(server, player)
    return true
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(100, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlRaceLock.enforce(server, p)
      } catch (e) {
        console.error(`[ttl] race lock failed for ${p.username}: ${e}`)
      }
    })
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] racelock command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')

  var show = ctx => {
    var p = target(ctx)
    say(ctx, `racelock ${p.username}: phase=${TtlLife.phase(p)} race=${TtlRaceLock.race(p) || '(none)'}`)
    return 1
  }
  var enforce = ctx => {
    var p = target(ctx)
    say(ctx, `racelock ${p.username}: ${TtlRaceLock.enforce(ctx.source.getServer(), p) ? 'set back to human' : 'nothing to do'}`)
    return 1
  }
  var expect = ctx => {
    var p = target(ctx)
    var want = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'race'))
    var got = TtlRaceLock.race(p)
    if (got !== want) throw `${p.username}: expected race ${want}, got ${got || '(none)'}`
    say(ctx, `racelock ${p.username}: race ${want} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('racelock')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('enforce').executes(logged(enforce)))
        .then(Commands.literal('expect')
          .then(Commands.argument('race', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(expect)))))))
})
