// Test hook: a player right-clicks a block with what it holds in the main hand, the way a real click arrives
// (ServerPlayerGameMode.useItemOn: NeoForge's RightClickBlock, so our own BlockEvents.rightClicked refusals, then the
// block and the item). Test bots cannot click by themselves. First used by tests/ingame/portals.rcon: flint and steel on
// an obsidian frame in the Mortal Realm lights a Nether portal (issue #85).
//   /ttl useon <player> <x> <y> <z> <face>     face: down, up, north, south, west, east (the clicked side of the block)
//   /ttl useon expect <player> <x> <y> <z> <block>   test assertion: the block at x y z in the player's dimension is
//                                                    <block> (full id); prints "ttl: ..." when it is not
// Prints "ttl: ..." when the click could not be made.
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var useon = ctx => {
    var p = Arguments.PLAYER.getResult(ctx, 'target')
    var x = Number(Arguments.INTEGER.getResult(ctx, 'x'))
    var y = Number(Arguments.INTEGER.getResult(ctx, 'y'))
    var z = Number(Arguments.INTEGER.getResult(ctx, 'z'))
    var faceName = String(Arguments.STRING.getResult(ctx, 'face')).toUpperCase()
    var BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
    var Vec3 = Java.loadClass('net.minecraft.world.phys.Vec3')
    var Direction = Java.loadClass('net.minecraft.core.Direction')
    var Hand = Java.loadClass('net.minecraft.world.InteractionHand')
    var Hit = Java.loadClass('net.minecraft.world.phys.BlockHitResult')
    var face = Direction[faceName]
    if (!face) throw `unknown face ${faceName.toLowerCase()} (down, up, north, south, west, east)`
    var pos = new BlockPos(x, y, z)
    var held = String(p.getMainHandItem().id)
    // The block's centre as the hit point (like world/domain_commands.js); the face decides where a placed block goes.
    var result = p.gameMode.useItemOn(p, p.level, p.getMainHandItem(), Hand.MAIN_HAND, new Hit(Vec3.atCenterOf(pos), face, pos, false))
    ctx.source.sendSystemMessage(Text.of(`useon ${p.username}: ${held} on ${x} ${y} ${z} (${faceName.toLowerCase()}): ${String(result)}`))
    return 1
  }

  var expect = ctx => {
    var p = Arguments.PLAYER.getResult(ctx, 'target')
    var x = Number(Arguments.INTEGER.getResult(ctx, 'x'))
    var y = Number(Arguments.INTEGER.getResult(ctx, 'y'))
    var z = Number(Arguments.INTEGER.getResult(ctx, 'z'))
    var want = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'block'))
    var got = String(p.level.getBlock(x, y, z).id)
    if (got !== want) throw `expected ${want} at ${x} ${y} ${z} in ${TtlLife.dimensionOf(p)}, found ${got}`
    ctx.source.sendSystemMessage(Text.of(`useon: ${want} at ${x} ${y} ${z} in ${TtlLife.dimensionOf(p)} as expected`))
    return 1
  }

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] useon command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var at = (then) => Commands.argument('x', Arguments.INTEGER.create(event))
    .then(Commands.argument('y', Arguments.INTEGER.create(event))
      .then(Commands.argument('z', Arguments.INTEGER.create(event)).then(then)))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('useon')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(at(Commands.argument('block', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(expect))))))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(at(Commands.argument('face', Arguments.STRING.create(event)).executes(logged(useon)))))))
})
