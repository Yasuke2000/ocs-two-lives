// Sleeping through the night (issue #86). The Mortal Realm is a dimension of its own, and vanilla lets only the
// overworld own the clock: every other dimension reads the overworld's day time through DerivedLevelData, whose
// setDayTime (and weather setters) do nothing. So when enough souls slept in the Mortal Realm, the game woke them all
// up and the night went on. NeoForge posts SleepFinishedTimeEvent in that very tick (ServerLevel.tick, after the
// sleep-percentage check and before wakeUpAllPlayers); here its new time is written to the overworld, which is the clock
// every dimension shows, and the rain is ended the way vanilla ends it after a night's sleep.
// The rule is vanilla's, per dimension: the gamerule playersSleepingPercentage (set to SLEEP_PERCENT below) of the souls in
// that dimension (spectators do not count, test bots do, like in vanilla) must sleep. One clock means a night slept away
// in the Mortal Realm is over in the Tensura world too, exactly as a night slept away in the Tensura world already ended it
// in the Mortal Realm.
// Ops (test hooks): /ttl sleep <player> bed  (a bed in the sky above the soul, the soul in it: "ttl: ..." when Minecraft
//   refuses) · /ttl sleep <player> clear (the bed gone) · /ttl sleep expect morning · /ttl sleep <player> expect morning (back to bed when woken early) | awake | mortal
const TtlSleep = {
  SLEEP_PERCENT: 50,
  // The test bed: this high above the soul, out of the way of builds; removed by `clear`.
  BED_Y: 250,
  hooked: false,
  lastBed: {},

  // The overworld's time after a night slept away in another dimension: the event's new time (next morning).
  onFinished(event) {
    var level = event.getLevel()
    // KubeJS shows a level's dimension as a property (its id), not the vanilla method (see TtlLife.dimensionOf).
    var dim = String(level.dimension)
    if (dim === TtlLife.OVERWORLD) return
    var server = level.getServer()
    var overworld = server.overworld()
    var before = Number(overworld.getDayTime())
    var next = Number(event.getNewTime())
    if (next <= before) return
    overworld.setDayTime(next)
    try {
      var rules = overworld.getGameRules()
      var GameRules = Java.loadClass('net.minecraft.world.level.GameRules')
      if (rules.getBoolean(GameRules.RULE_WEATHER_CYCLE) && overworld.isRaining()) overworld.setWeatherParameters(0, 0, false, false)
    } catch (e) {
      console.warn(`[ttl] sleep: the rain was left alone: ${e}`)
    }
    console.info(`[ttl] sleep: the night was slept away in ${dim}, day time ${before} -> ${next}`)
  },

  // 0..23999 of the shared clock.
  timeOfDay(server) {
    return Number(server.overworld().getDayTime()) % 24000
  }
}

ServerEvents.loaded(event => {
  event.server.runCommandSilent(`gamerule playersSleepingPercentage ${TtlSleep.SLEEP_PERCENT}`)
})

try {
  var TtlSleepFinishedTimeEvent = Java.loadClass('net.neoforged.neoforge.event.level.SleepFinishedTimeEvent')
  NativeEvents.onEvent(TtlSleepFinishedTimeEvent, event => {
    try {
      TtlSleep.onFinished(event)
    } catch (e) {
      console.error(`[ttl] sleep: carrying the night over to the overworld failed: ${e}`)
    }
  })
  TtlSleep.hooked = true
  console.info('[ttl] sleep: a night slept away in the Mortal Realm now moves the shared clock')
} catch (e) {
  console.error(`[ttl] sleep: SleepFinishedTimeEvent hook NOT registered, sleeping in the Mortal Realm will not skip the night (${e})`)
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] sleep command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')

  var bed = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    if (!TtlSleep.hooked) throw 'the SleepFinishedTimeEvent hook is not registered (see the startup log)'
    var dim = TtlLife.dimensionOf(p)
    var x = Math.floor(p.getX())
    var z = Math.floor(p.getZ())
    var y = TtlSleep.BED_Y
    var at = `execute in ${dim} run`
    TtlCmd.run(server, `${at} setblock ${x} ${y} ${z} minecraft:red_bed[facing=south,part=foot]`)
    TtlCmd.run(server, `${at} setblock ${x} ${y} ${z + 1} minecraft:red_bed[facing=south,part=head]`)
    var b = { dim: dim, x: x, y: y, z: z }
    TtlSleep.lastBed[p.username] = b
    intoBed(server, p, b)
    say(ctx, `sleep ${p.username}: asleep in a bed at ${x} ${y} ${z} in ${dim} (time of day ${TtlSleep.timeOfDay(server)})`)
    return 1
  }

  var intoBed = (server, p, b) => {
    TtlCmd.run(server, `execute in ${b.dim} run tp ${p.username} ${b.x + 0.5} ${b.y + 1} ${b.z + 0.5}`)
    var BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
    var r = p.startSleepInBed(BlockPos.containing(b.x, b.y, b.z))
    if (r.left().isPresent()) throw `${p.username} could not sleep in ${b.dim}: ${r.left().get()}`
  }

  // The morning, for a soul asleep in its test bed. A soul woken without the morning (a late teleport: the Life 2 arrival
  // moves a reborn soul once its chunks are ready, on a freshly started server seconds after the rebirth) is put back to
  // bed and the check fails this time; `@until` asks again.
  var morningFor = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var t = TtlSleep.timeOfDay(server)
    if (t < 2000) {
      say(ctx, `sleep ${p.username}: morning (time of day ${t}) as expected`)
      return 1
    }
    var b = TtlSleep.lastBed[p.username]
    if (!b) throw `no test bed of ${p.username}`
    if (!p.isSleeping()) {
      intoBed(server, p, b)
      throw `not morning yet (time of day ${t}); ${p.username} had woken up, back to bed`
    }
    throw `not morning yet (time of day ${t}), ${p.username} asleep`
  }

  var clear = ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var b = TtlSleep.lastBed[p.username]
    if (!b) throw `no test bed of ${p.username} to clear`
    if (p.isSleeping()) p.stopSleepInBed(false, false)
    TtlCmd.run(server, `execute in ${b.dim} run setblock ${b.x} ${b.y} ${b.z + 1} minecraft:air`)
    TtlCmd.run(server, `execute in ${b.dim} run setblock ${b.x} ${b.y} ${b.z} minecraft:air`)
    delete TtlSleep.lastBed[p.username]
    say(ctx, `sleep ${p.username}: test bed removed`)
    return 1
  }

  var morning = ctx => {
    var t = TtlSleep.timeOfDay(ctx.source.getServer())
    // A night slept away lands on 0 (sunrise); a few seconds of ticking later it is still early morning.
    if (t >= 2000) throw `expected morning, the time of day is ${t}`
    say(ctx, `sleep: morning (time of day ${t}) as expected`)
    return 1
  }

  var mortal = ctx => {
    var p = target(ctx)
    var dim = TtlLife.dimensionOf(p)
    if (dim !== TtlLife.MORTAL) throw `${p.username} is in ${dim}, not ${TtlLife.MORTAL}`
    say(ctx, `sleep ${p.username}: in ${dim} as expected`)
    return 1
  }

  var awake = ctx => {
    var p = target(ctx)
    if (p.isSleeping()) throw `${p.username} is still asleep`
    say(ctx, `sleep ${p.username}: awake as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('sleep')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('expect')
        .then(Commands.literal('morning').executes(logged(morning))))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.literal('bed').executes(logged(bed)))
        .then(Commands.literal('clear').executes(logged(clear)))
        .then(Commands.literal('expect')
          .then(Commands.literal('awake').executes(logged(awake)))
          .then(Commands.literal('morning').executes(logged(morningFor)))
          .then(Commands.literal('mortal').executes(logged(mortal)))))))
})
