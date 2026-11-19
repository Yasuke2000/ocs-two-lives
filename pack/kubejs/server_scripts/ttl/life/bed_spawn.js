// Beds and respawn points. The canon builds have beds now (blueprints/_beds.py, 19/11/2026), so a soul can set a
// respawn point in a bed, a respawn anchor or with /spawnpoint. Two rules keep that from leaking across the lives
// (decisions.md, 19/11/2026):
//   1. A respawn point is set only in the soul's own worlds: Life 1 (and the Corridor) in the Mortal dimensions, Life 2
//      anywhere that is not one of ours (`ttl:*`: the Mortal dimensions, the Corridor, the arenas and Walpurgis Hall). Tempest,
//      Dwargon and every other build of the Tensura world are fine for Life 2: a soul that walked there may sleep there.
//      NeoForge's PlayerSetSpawnEvent is cancelled otherwise (reached through NativeEvents.onEvent like Tombstone's
//      CaptureSoulEvent, compat/tombstone_bosses.js). /spawnpoint (forced) is an op's decision and always goes through;
//      clearing a respawn point always does too.
//   2. Life 1 deaths are cancelled (life/death.js), so a Life 1 respawn point is never used in Life 1; but vanilla keeps it
//      across the rebirth. A Life 2 soul that dies with a Mortal Realm bed behind it would respawn in the Mortal Realm
//      (confine.js sends it back within 5 s). It is moved to the Tensura world at once and the stale point cleared.
// Ops: /ttl bedspawn <player> try <dimension> <x> <y> <z> <set|refused>   test hook: attempt a (not forced) respawn point
//      and fail with "ttl: ..." when the outcome is not the expected one; the point is cleared again afterwards.
const TtlBedSpawn = {
  // True once the PlayerSetSpawnEvent veto is registered (bottom of this file).
  vetoed: false,

  // May a soul in `phase` set a respawn point in `dimension`? An untracked player (ops, test setups) may.
  allowed(phase, dimension) {
    var dim = String(dimension)
    if (phase === 'life1') return TtlLife.isMortal(dim)
    if (phase === 'corridor') return false
    if (phase === 'life2') return dim.indexOf('ttl:') !== 0
    return true
  },

  refusal(phase, dimension) {
    if (phase === 'life2') return 'The mortal world is closed to a soul that has already died once.'
    return 'Your first life is bound to the mortal world; this bed will not hold your soul.'
  },

  onSet(event) {
    if (event.isForced() || event.getNewSpawn() === null) return
    var player = event.getEntity()
    var phase = TtlLife.phase(player)
    var dimension = String(event.getSpawnLevel().location())
    if (this.allowed(phase, dimension)) return
    event.setCanceled(true)
    console.info(`[ttl] bed spawn: ${player.getGameProfile().getName()} (${phase}) may not set a respawn point in ${dimension}`)
    try {
      player.displayClientMessage(Text.red(this.refusal(phase, dimension)), true)
    } catch (e) {
      // the log line above is enough
    }
  },

  clear(player) {
    var Level = Java.loadClass('net.minecraft.world.level.Level')
    player.setRespawnPosition(Level.OVERWORLD, null, 0, false, false)
  },

  // After a respawn: a Life 2 soul that came back in a Mortal dimension (its Life 1 bed) goes to the Tensura world.
  onRespawned(event) {
    var player = event.player
    var server = event.server
    if (TtlLife.phase(player) !== 'life2' || !TtlLife.isMortal(TtlLife.dimensionOf(player))) return
    console.info(`[ttl] bed spawn: ${player.username} (life 2) respawned in ${TtlLife.dimensionOf(player)}, moved to the Tensura world and the stale respawn point cleared`)
    try {
      this.clear(player)
    } catch (e) {
      console.error(`[ttl] bed spawn: could not clear the respawn point of ${player.username}: ${e}`)
    }
    TtlLife.toOverworld(server, player)
  }
}

PlayerEvents.respawned(event => TtlBedSpawn.onRespawned(event))

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] bedspawn command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var attempt = ctx => {
    var p = Arguments.PLAYER.getResult(ctx, 'target')
    var dim = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'dimension'))
    var x = Arguments.INTEGER.getResult(ctx, 'x')
    var y = Arguments.INTEGER.getResult(ctx, 'y')
    var z = Arguments.INTEGER.getResult(ctx, 'z')
    var want = String(Arguments.STRING.getResult(ctx, 'outcome'))
    if (want !== 'set' && want !== 'refused') throw `outcome is "set" or "refused", not "${want}"`
    if (!TtlBedSpawn.vetoed) throw 'the PlayerSetSpawnEvent veto is not registered (see the startup log)'
    var Registries = Java.loadClass('net.minecraft.core.registries.Registries')
    var ResourceKey = Java.loadClass('net.minecraft.resources.ResourceKey')
    var ResourceLocation = Java.loadClass('net.minecraft.resources.ResourceLocation')
    var BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
    var key = ResourceKey.create(Registries.DIMENSION, ResourceLocation.parse(dim))
    var pos = new BlockPos(x, y, z)
    TtlBedSpawn.clear(p)
    p.setRespawnPosition(key, pos, 0, false, false)
    var got = p.getRespawnPosition()
    var took = got !== null && got.equals(pos) && String(p.getRespawnDimension().location()) === dim
    TtlBedSpawn.clear(p)
    var outcome = took ? 'set' : 'refused'
    if (outcome !== want) throw `${p.username} (${TtlLife.phase(p)}): a respawn point at ${dim} ${x} ${y} ${z} was ${outcome}, expected ${want}`
    ctx.source.sendSystemMessage(Text.of(`bedspawn ${p.username} (${TtlLife.phase(p)}): ${dim} ${outcome} as expected`))
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('bedspawn')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.literal('try')
          .then(Commands.argument('dimension', Arguments.RESOURCE_LOCATION.create(event))
            .then(Commands.argument('x', Arguments.INTEGER.create(event))
              .then(Commands.argument('y', Arguments.INTEGER.create(event))
                .then(Commands.argument('z', Arguments.INTEGER.create(event))
                  .then(Commands.argument('outcome', Arguments.STRING.create(event)).executes(logged(attempt)))))))))))
})

try {
  var TtlPlayerSetSpawnEvent = Java.loadClass('net.neoforged.neoforge.event.entity.player.PlayerSetSpawnEvent')
  NativeEvents.onEvent(TtlPlayerSetSpawnEvent, event => {
    try {
      TtlBedSpawn.onSet(event)
    } catch (e) {
      console.error(`[ttl] bed spawn: check failed, the respawn point is left alone: ${e}`)
    }
  })
  TtlBedSpawn.vetoed = true
  console.info('[ttl] bed spawn: respawn-point veto registered (Life 1 only in the Mortal dimensions, Life 2 never in ttl: dimensions)')
} catch (e) {
  console.error(`[ttl] bed spawn: respawn-point veto NOT registered, a soul can set a respawn point in the wrong world (${e})`)
}
