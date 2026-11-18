// priority: 60
// Domain commands (world/domains.js has the logic, design/data/factions.toml the data; world-state.md §6.6, §7.5).
// Players: /ttl domain                                   the domain you stand in and whether you may change blocks there
// Ops:     /ttl domain check <x> <z>                     inside/outside the continent, the domain, who may edit (overworld)
//          /ttl domain list                              every domain part in force (placed builds and landmarks only)
//          /ttl domain residents                         Tempest's residents and their last state
//          /ttl domain respawn                           run the resident check now
//          /ttl domain testdelay <seconds> | reset       test hook: the respawn delay of killable residents
//          /ttl domain testbreak <player> <x> <z> kept|broken   test hook: puts stone on the surface at x z (overworld) and
//                                                        lets the player break it through the game's own path
//                                                        (ServerPlayerGameMode.destroyBlock → BlockEvents.broken), then
//                                                        clears it; "ttl: ..." when the outcome differs
//          /ttl domain testdoor <player> <x> <z> opens|shut   test hook: an oak door on the surface, the player right-clicks
//                                                        it with what they hold (useItemOn → BlockEvents.rightClicked)
//          /ttl domain expect <what>                     test assertion, prints "ttl: ..." when it does not hold:
//            <player> edit <x> <z> <yes|no> · at <x> <z> <faction|none> · resident <id> <alive|missing> ·
//            invulnerable <id> <yes|no> · parts <faction> <n>
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var OW = 'minecraft:overworld'

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] domain command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var server = ctx => ctx.source.getServer()
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var ops = src => src.hasPermission(2)

  var describe = (s, player, dim, x, z) => {
    var v = TtlDomains.canEdit(s, player, dim, x, z)
    if (!v.hit) return `${x} ${z}: ${v.why}`
    var h = v.hit
    var owner = h.faction ? `${h.title} (${h.faction})` : `${h.title} (a canon build of no faction)`
    var road = h.faction && TtlDomains.conflictOpen(s, h.faction) ? ', conflict open' : ''
    return `${x} ${z}: ${owner}, ${h.kind} ${h.label}${road}; ${player ? `${player.username} ${v.ok ? 'may' : 'may not'} edit (${v.why})` : `edit: ${v.ok ? 'open' : 'staff, members and the ruling nation only'}`}`
  }

  var here = ctx => {
    var p = ctx.source.getPlayerOrException()
    say(ctx, describe(server(ctx), p, TtlLife.dimensionOf(p), Math.floor(p.x), Math.floor(p.z)))
    return 1
  }

  var check = ctx => {
    say(ctx, `domain: ${describe(server(ctx), null, OW, num(ctx, 'x'), num(ctx, 'z'))}`)
    return 1
  }

  var list = ctx => {
    TtlDomains.invalidate()
    var parts = TtlDomains.parts(server(ctx))
    say(ctx, `domains: ${parts.length} part(s) in force`)
    parts.forEach(p => say(ctx, `  ${p.faction || '(none)'} ${p.kind} ${p.label}${p.kind === 'region' ? '' : ` [${p.dim} ${p.x0} ${p.z0} .. ${p.x1} ${p.z1}]`}`))
    return 1
  }

  var residents = ctx => {
    var s = server(ctx)
    var all = TtlDomains.residents(s)
    if (!all.length) {
      say(ctx, 'domains: no residents (Tempest is not placed at this version)')
      return 1
    }
    var miss = TtlDomains.missing(s)
    all.forEach(r => say(ctx, `  ${r.id}${r.name ? ` (${r.name})` : ''} at ${Math.floor(r.x)} ${r.y} ${Math.floor(r.z)}: ${r.anchor ? 'anchor' : 'killable'}, last ${TtlDomains.last[r.id] || 'unchecked'}${miss[r.id] ? `, missing since ${new Date(Number(miss[r.id].at)).toISOString().slice(11, 19)}` : ''}`))
    return 1
  }

  var respawn = ctx => {
    var st = TtlDomains.ensureResidents(server(ctx))
    var ids = Object.keys(st)
    say(ctx, `domains: ${ids.length ? ids.map(id => `${id} ${st[id]}`).join(', ') : 'no residents'}`)
    return 1
  }

  var testdelay = reset => ctx => {
    TtlDomains.setTestDelay(server(ctx), reset ? null : num(ctx, 'seconds'))
    say(ctx, `domains: respawn delay of killable residents ${reset ? 'back to respawn_minutes' : `${num(ctx, 'seconds')} s (test)`}`)
    return 1
  }

  // The first free y above everything that blocks motion at x z (the chunk must be loaded).
  var surface = (s, x, z) => {
    var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
    return Number(s.getLevel(OW).getHeight(Types.MOTION_BLOCKING, x, z))
  }

  var blockAt = (s, x, y, z) => String(s.getLevel(OW).getBlock(x, y, z).id)

  var loadedOrThrow = (s, x, z) => {
    if (!(TtlCmd.run(s, `execute in ${OW} if loaded ${x} 64 ${z}`) > 0)) throw `the chunk at ${x} ${z} is not loaded (forceload it first)`
  }

  var testbreak = want => ctx => {
    var s = server(ctx)
    var p = Arguments.PLAYER.getResult(ctx, 'player')
    var x = num(ctx, 'x')
    var z = num(ctx, 'z')
    if (TtlLife.dimensionOf(p) !== OW) throw `${p.username} must be in the overworld (the break runs in the player's own level)`
    loadedOrThrow(s, x, z)
    var y = surface(s, x, z)
    if (blockAt(s, x, y, z) !== 'minecraft:air') throw `no free block at ${x} ${y} ${z}`
    TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y} ${z} minecraft:stone`)
    var BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
    var broke = false
    var got = ''
    try {
      broke = !!p.gameMode.destroyBlock(new BlockPos(x, y, z))
    } finally {
      got = blockAt(s, x, y, z)
      TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y} ${z} minecraft:air`)
    }
    var outcome = got === 'minecraft:stone' ? 'kept' : 'broken'
    if (outcome !== want) throw `expected the stone at ${x} ${y} ${z} ${want} when ${p.username} breaks it, it was ${outcome} (destroyBlock ${broke})`
    say(ctx, `domain: ${p.username} breaking at ${x} ${y} ${z}: ${outcome} as expected`)
    return 1
  }

  var testdoor = want => ctx => {
    var s = server(ctx)
    var p = Arguments.PLAYER.getResult(ctx, 'player')
    var x = num(ctx, 'x')
    var z = num(ctx, 'z')
    if (TtlLife.dimensionOf(p) !== OW) throw `${p.username} must be in the overworld`
    loadedOrThrow(s, x, z)
    var y = surface(s, x, z)
    if (blockAt(s, x, y, z) !== 'minecraft:air' || blockAt(s, x, y + 1, z) !== 'minecraft:air') throw `no room for a door at ${x} ${y} ${z}`
    TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y} ${z} minecraft:oak_door[half=lower,facing=north,open=false]`)
    TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y + 1} ${z} minecraft:oak_door[half=upper,facing=north,open=false]`)
    var open = 'missing'
    try {
      var BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
      var Vec3 = Java.loadClass('net.minecraft.world.phys.Vec3')
      var Direction = Java.loadClass('net.minecraft.core.Direction')
      var Hand = Java.loadClass('net.minecraft.world.InteractionHand')
      var Hit = Java.loadClass('net.minecraft.world.phys.BlockHitResult')
      var pos = new BlockPos(x, y, z)
      var hit = new Hit(Vec3.atCenterOf(pos), Direction.NORTH, pos, false)
      p.gameMode.useItemOn(p, s.getLevel(OW), p.getMainHandItem(), Hand.MAIN_HAND, hit)
      var b = s.getLevel(OW).getBlock(x, y, z)
      if (String(b.id) === 'minecraft:oak_door') open = String(b.properties.get('open'))
    } finally {
      TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y + 1} ${z} minecraft:air`)
      TtlCmd.run(s, `execute in ${OW} run setblock ${x} ${y} ${z} minecraft:air`)
    }
    var outcome = open === 'true' ? 'opens' : 'shut'
    if (outcome !== want) throw `expected the door at ${x} ${y} ${z} to be ${want} after ${p.username} used it, it is ${outcome} (open=${open})`
    say(ctx, `domain: ${p.username} used a door at ${x} ${y} ${z}: ${outcome} as expected`)
    return 1
  }

  var yesno = v => (v ? 'yes' : 'no')

  var expect = ctx => {
    var s = server(ctx)
    var parts = String(Arguments.GREEDY_STRING.getResult(ctx, 'what')).trim().split(/\s+/)
    var need = n => {
      if (parts.length !== n) throw `expect ${parts[0]} takes ${n - 1} value(s), got: ${parts.slice(1).join(' ') || 'none'}`
    }
    var got
    var want
    var resident = id => {
      var r = TtlDomains.residents(s).filter(x => x.id === id)[0]
      if (!r) throw `unknown resident ${id} (${TtlDomains.residents(s).map(x => x.id).join(', ') || 'none: Tempest not placed'})`
      var found = []
      s.getLevel(r.dim).getEntities().forEach(e => {
        if (e.isAlive() && e.getTags().contains(TtlDomains.RES_TAG + id)) found.push(e)
      })
      return found
    }
    if (parts[0] === 'at') {
      need(4)
      var hit = TtlDomains.of(s, OW, Number(parts[1]), Number(parts[2]))
      got = hit ? hit.faction || '(unowned)' : 'none'
      want = parts[3]
    } else if (parts[0] === 'resident') {
      need(3)
      got = resident(parts[1]).length > 0 ? 'alive' : 'missing'
      want = parts[2]
    } else if (parts[0] === 'invulnerable') {
      need(3)
      var ents = resident(parts[1])
      if (!ents.length) throw `resident ${parts[1]} is not loaded`
      got = yesno(!!ents[0].isInvulnerable())
      want = parts[2]
    } else if (parts[0] === 'parts') {
      need(3)
      TtlDomains.invalidate()
      got = String(TtlDomains.parts(s).filter(p => p.faction === parts[1]).length)
      want = parts[2]
    } else if (parts[1] === 'edit') {
      need(5)
      var p = s.getPlayerList().getPlayerByName(parts[0])
      if (!p) throw `${parts[0]} is not online`
      got = yesno(TtlDomains.canEdit(s, p, OW, Number(parts[2]), Number(parts[3])).ok)
      want = parts[4]
    } else {
      throw `unknown expect ${parts[0]} (<player> edit <x> <z> <yes|no>, at <x> <z> <faction|none>, resident <id> <alive|missing>, invulnerable <id> <yes|no>, parts <faction> <n>)`
    }
    if (got !== want) throw `domain: expected ${parts.slice(0, parts.length - 1).join(' ')} = ${want}, got ${got}`
    say(ctx, `domain: ${parts.join(' ')} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('player', Arguments.PLAYER.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))
  var xz = (fn, outcomes) => {
    var z = intArg('z')
    outcomes.forEach(o => { z = z.then(Commands.literal(o).executes(logged(fn(o)))) })
    return intArg('x').then(z)
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('domain')
      .executes(logged(here))
      .then(Commands.literal('check').requires(ops).then(intArg('x').then(intArg('z').executes(logged(check)))))
      .then(Commands.literal('list').requires(ops).executes(logged(list)))
      .then(Commands.literal('residents').requires(ops).executes(logged(residents)))
      .then(Commands.literal('respawn').requires(ops).executes(logged(respawn)))
      .then(Commands.literal('testdelay').requires(ops)
        .then(Commands.literal('reset').executes(logged(testdelay(true))))
        .then(intArg('seconds').executes(logged(testdelay(false)))))
      .then(Commands.literal('testbreak').requires(ops).then(playerArg().then(xz(testbreak, ['kept', 'broken']))))
      .then(Commands.literal('testdoor').requires(ops).then(playerArg().then(xz(testdoor, ['opens', 'shut']))))
      .then(Commands.literal('expect').requires(ops)
        .then(Commands.argument('what', Arguments.GREEDY_STRING.create(event)).executes(logged(expect))))))
})
