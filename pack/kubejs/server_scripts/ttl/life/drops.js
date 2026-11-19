// Placement without junk on the ground: the placers (life/trade_roads.js, unplace.js, dwargon.js; every chunk hold of
// life/chunk_hold.js) remove blocks through here instead of `fill ... air` / `setblock` / level.setBlock(..., 2).
//
// Why: vanilla `fill` and `setblock` (and setBlock with flag 2) update the neighbours' shapes, and every neighbour that can
// no longer stand there (short grass and flowers on a removed grass block, moss carpet, azalea, saplings, vines, cocoa,
// torches, the top half of a tall plant) is destroyed WITH its drops; a sand or gravel block over a new gap falls. On
// staging (19/11/2026) the Jura round held 2,348 item entities (wheat seeds, moss carpet, azalea, saplings, logs) and 152
// falling blocks, the overworld tick went from 66.8 to 33 ms when they were killed. A chunk hold keeps its chunks at
// ticket level 32 (block ticking, NO entity ticking), so what drops or falls there never moves, never despawns, and is
// saved with the chunk: falling gravel with Time 0 hung in mid-air in caves and showed up again whenever a player came by.
//
// - set(level, x, y, z, state): one block, flags FLAGS (no neighbour shape updates), a container emptied first (a chest
//   or barrel removed with setBlock spills its loot).
// - replace(level, x, y, z, state): set() and what leaned on that one block (life/unplace.js, cell by cell).
// - clearColumn(server, dim, x, y0, y1, z): the column top-down to air, then what leaned on it (above, below, beside:
//   anything whose canSurvive is now false) goes too without drops, and a sand/gravel block left over the gap becomes its
//   solid twin (sandstone, stone, concrete). Returns the blocks changed, -1 when Java is unavailable (callers fall back
//   to their command).
// - underpin(server, dim, x, y, z): a falling block at x y z over a gap gets dirt under it.
// - sweep(server, dim, box, maxAge, label): after a piece, items and falling blocks that appeared inside the box during it
//   (item age / falling time <= maxAge ticks; in a level-32 hold both stay 0) and that no player stands within PLAYER_GAP
//   of: items are removed, a falling block is set down where it would have landed. Log: `[ttl] drops: <label>: swept N
//   item(s), set down M falling block(s)` when there was anything.
// Test: /ttl drops test <x> <y> <z> (tests/ingame/drops.rcon) builds a column with plants, a carpet, a torch and gravel,
// clears it, and counts the item entities after a few ticks (must be 0).
const TtlDrops = {
  FLAGS: 18, // Block.UPDATE_CLIENTS (2) | Block.UPDATE_KNOWN_SHAPE (16)
  PLAYER_GAP: 32,
  CHAIN: 8, // dependents followed up / down from a cleared column (a tall plant, a vine or cave vine run)
  TWIN: { 'minecraft:sand': 'minecraft:sandstone', 'minecraft:suspicious_sand': 'minecraft:sandstone',
    'minecraft:red_sand': 'minecraft:red_sandstone', 'minecraft:gravel': 'minecraft:stone', 'minecraft:suspicious_gravel': 'minecraft:stone' },

  java() {
    if (this.j !== undefined) return this.j
    try {
      var Blocks = Java.loadClass('net.minecraft.world.level.block.Blocks')
      this.j = {
        BlockPos: Java.loadClass('net.minecraft.core.BlockPos'),
        AABB: Java.loadClass('net.minecraft.world.phys.AABB'),
        Clearable: Java.loadClass('net.minecraft.world.Clearable'),
        FallingBlock: Java.loadClass('net.minecraft.world.level.block.FallingBlock'),
        ItemEntity: Java.loadClass('net.minecraft.world.entity.item.ItemEntity'),
        FallingBlockEntity: Java.loadClass('net.minecraft.world.entity.item.FallingBlockEntity'),
        Registries: Java.loadClass('net.minecraft.core.registries.BuiltInRegistries'),
        ResourceLocation: Java.loadClass('net.minecraft.resources.ResourceLocation'),
        AIR: Blocks.AIR.defaultBlockState(),
        DIRT: Blocks.DIRT.defaultBlockState()
      }
    } catch (e) {
      console.error(`[ttl] drops: Java classes unavailable (${e}); the placers fall back to their commands`)
      this.j = null
    }
    return this.j
  },

  state(id) {
    var J = this.java()
    try {
      return J.Registries.BLOCK.get(J.ResourceLocation.parse(id)).defaultBlockState()
    } catch (e) {
      return null
    }
  },

  id(st) {
    return String(this.java().Registries.BLOCK.getKey(st.getBlock()))
  },

  set(level, x, y, z, st) {
    var J = this.java()
    var pos = new J.BlockPos(x, y, z)
    var be = level.getBlockEntity(pos)
    if (be) J.Clearable.tryClear(be)
    return level.setBlock(pos, st || J.AIR, this.FLAGS)
  },

  falls(st) {
    return st.getBlock() instanceof this.java().FallingBlock
  },

  // The solid block for a falling one that would hang over a gap, or null (anvils, dragon eggs: left as they are).
  twin(st) {
    var id = this.id(st)
    if (this.TWIN[id]) return this.state(this.TWIN[id])
    if (/_concrete_powder$/.test(id)) return this.state(id.replace(/_powder$/, ''))
    return null
  },

  // Removes what can no longer stand at x y z, then follows the run in direction dy (a tall plant up, cave vines down).
  dependents(level, x, y, z, dy) {
    var J = this.java()
    var n = 0
    for (var k = 0; k < this.CHAIN; k++) {
      var pos = new J.BlockPos(x, y, z)
      var st = level.getBlockState(pos)
      if (st.isAir() || st.canSurvive(level, pos)) break
      this.set(level, x, y, z, J.AIR)
      n++
      if (!dy) break
      y += dy
    }
    return n
  },

  // One block replaced (air or another block) without drops, then what leaned on it: above (a plant run), below (cave
  // vines, a lantern) and on its four sides. Returns the blocks changed.
  replace(level, x, y, z, st) {
    this.set(level, x, y, z, st)
    return 1 + this.dependents(level, x, y + 1, z, 1) + this.dependents(level, x, y - 1, z, -1) +
      this.dependents(level, x + 1, y, z, 0) + this.dependents(level, x - 1, y, z, 0) +
      this.dependents(level, x, y, z + 1, 0) + this.dependents(level, x, y, z - 1, 0)
  },

  clearColumn(server, dim, x, y0, y1, z) {
    var J = this.java()
    if (!J) return -1
    if (y1 < y0) return 0
    var level = server.getLevel(dim)
    var n = 0
    for (var y = y1; y >= y0; y--) {
      if (level.getBlockState(new J.BlockPos(x, y, z)).isAir()) continue
      this.set(level, x, y, z, J.AIR)
      n++
    }
    n += this.dependents(level, x, y1 + 1, z, 1)
    n += this.dependents(level, x, y0 - 1, z, -1)
    for (var yy = y0; yy <= y1; yy++) {
      n += this.dependents(level, x + 1, yy, z, 0)
      n += this.dependents(level, x - 1, yy, z, 0)
      n += this.dependents(level, x, yy, z + 1, 0)
      n += this.dependents(level, x, yy, z - 1, 0)
    }
    // the first block left above the gap: sand or gravel there would fall into it
    for (var up = y1 + 1; up <= y1 + this.CHAIN; up++) {
      var st = level.getBlockState(new J.BlockPos(x, up, z))
      if (st.isAir()) continue
      if (this.falls(st)) {
        var solid = this.twin(st)
        if (solid) {
          this.set(level, x, up, z, solid)
          n++
        }
      }
      break
    }
    return n
  },

  underpin(server, dim, x, y, z) {
    var J = this.java()
    if (!J) return false
    var level = server.getLevel(dim)
    if (!this.falls(level.getBlockState(new J.BlockPos(x, y, z)))) return false
    if (!J.FallingBlock.isFree(level.getBlockState(new J.BlockPos(x, y - 1, z)))) return false
    this.set(level, x, y - 1, z, J.DIRT)
    return true
  },

  nearPlayer(players, e) {
    var g = this.PLAYER_GAP * this.PLAYER_GAP
    for (var i = 0; i < players.length; i++) {
      var dx = players[i].getX() - e.getX()
      var dy = players[i].getY() - e.getY()
      var dz = players[i].getZ() - e.getZ()
      if (dx * dx + dy * dy + dz * dz < g) return true
    }
    return false
  },

  // box: { x0, z0, x1, z1 } (blocks, inclusive), every height. Returns { items, falling } or null.
  sweep(server, dim, box, maxAge, label) {
    var J = this.java()
    if (!J) return null
    var res = { items: 0, falling: 0 }
    try {
      var level = server.getLevel(dim)
      var players = []
      level.players().forEach(p => players.push(p))
      var aabb = new J.AABB(box.x0, level.getMinBuildHeight(), box.z0, box.x1 + 1, level.getMaxBuildHeight(), box.z1 + 1)
      var self = this
      var items = []
      var falling = []
      level.getEntitiesWithin(aabb).forEach(e => {
        if (e instanceof J.ItemEntity) items.push(e)
        else if (e instanceof J.FallingBlockEntity) falling.push(e)
      })
      items.forEach(e => {
        if (!e.isAlive() || e.getAge() > maxAge || self.nearPlayer(players, e)) return
        e.discard()
        res.items++
      })
      falling.forEach(e => {
        if (!e.isAlive() || e.time > maxAge || self.nearPlayer(players, e)) return
        var st = e.getBlockState()
        var x = Math.floor(e.getX())
        var y = Math.floor(e.getY())
        var z = Math.floor(e.getZ())
        var minY = level.getMinBuildHeight()
        while (y > minY && J.FallingBlock.isFree(level.getBlockState(new J.BlockPos(x, y - 1, z)))) y--
        if (J.FallingBlock.isFree(level.getBlockState(new J.BlockPos(x, y, z)))) self.set(level, x, y, z, st)
        e.discard()
        res.falling++
      })
    } catch (e) {
      console.error(`[ttl] drops: sweep of ${label} failed: ${e}`)
      return null
    }
    if (res.items || res.falling) {
      console.info(`[ttl] drops: ${label}: swept ${res.items} item(s), set down ${res.falling} falling block(s)`)
    }
    return res
  }
}

// /ttl drops test <x> <y> <z> (op): builds a test column at x z from y (dirt and a grass block on a stone plinth, tall grass
// on top, a wall torch on its side, a moss carpet beside it on its own stone, gravel on two stone blocks above), clears
// the dirt + grass block and the two stones with clearColumn, logs `[ttl] drops test: N item(s), M falling block(s)` 5
// ticks later. /ttl drops expect clean <x> <y> <z>: fails unless no item entity or falling block lies round x y z.
// /ttl drops sweep <x> <y> <z>: TtlDrops.sweep over 9 x 9 round x z (age <= 100 ticks).
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var int = (ctx, n) => Arguments.INTEGER.getResult(ctx, n)
  var count = (server, x, y, z) => {
    var J = TtlDrops.java()
    var out = { items: 0, falling: 0 }
    server.getLevel(TtlLife.OVERWORLD).getEntitiesWithin(new J.AABB(x - 6, y - 6, z - 6, x + 7, y + 12, z + 7)).forEach(e => {
      if (e instanceof J.ItemEntity) out.items++
      else if (e instanceof J.FallingBlockEntity) out.falling++
    })
    return out
  }
  var pos = (ctx, then) => {
    if (!TtlDrops.java()) {
      ctx.source.sendSystemMessage(Text.red('ttl: drops: Java classes unavailable'))
      return 0
    }
    return then(ctx.source.getServer(), int(ctx, 'x'), int(ctx, 'y'), int(ctx, 'z'))
  }
  var xyz = fn => Commands.argument('x', Arguments.INTEGER.create(event))
    .then(Commands.argument('y', Arguments.INTEGER.create(event))
      .then(Commands.argument('z', Arguments.INTEGER.create(event)).executes(ctx => pos(ctx, fn(ctx)))))
  event.register(Commands.literal('ttl')
    .then(Commands.literal('drops')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('test').then(xyz(ctx => (server, x, y, z) => {
        var run = cmd => server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
        // a stone plinth with the test column in the middle, everything round it air
        run(`fill ${x - 3} ${y} ${z - 3} ${x + 3} ${y + 9} ${z + 3} minecraft:air`)
        run(`fill ${x - 2} ${y} ${z - 2} ${x + 2} ${y} ${z + 2} minecraft:stone`)
        run(`fill ${x} ${y + 1} ${z} ${x} ${y + 2} ${z} minecraft:dirt`)
        run(`setblock ${x} ${y + 3} ${z} minecraft:grass_block`)
        run(`setblock ${x} ${y + 4} ${z} minecraft:tall_grass[half=lower]`)
        run(`setblock ${x} ${y + 5} ${z} minecraft:tall_grass[half=upper]`)
        run(`setblock ${x + 1} ${y + 1} ${z} minecraft:stone`)
        run(`setblock ${x + 1} ${y + 2} ${z} minecraft:moss_carpet`)
        run(`setblock ${x - 1} ${y + 2} ${z} minecraft:wall_torch[facing=west]`)
        run(`fill ${x} ${y + 6} ${z} ${x} ${y + 7} ${z} minecraft:stone`)
        run(`setblock ${x} ${y + 8} ${z} minecraft:gravel`)
        // what the set-up itself knocked off (vanilla fill and setblock: a re-run pops the last run's carpet) is not counted
        var J0 = TtlDrops.java()
        server.getLevel(TtlLife.OVERWORLD).getEntitiesWithin(new J0.AABB(x - 6, y - 6, z - 6, x + 7, y + 12, z + 7)).forEach(e => {
          if (e instanceof J0.ItemEntity || e instanceof J0.FallingBlockEntity) e.discard()
        })
        // clear dirt + grass block (the plants on top and the torch on its side lean on them), and the stone under the gravel
        var n = TtlDrops.clearColumn(server, TtlLife.OVERWORLD, x, y + 1, y + 3, z)
        n += TtlDrops.clearColumn(server, TtlLife.OVERWORLD, x, y + 6, y + 7, z)
        var level = server.getLevel(TtlLife.OVERWORLD)
        var J = TtlDrops.java()
        var left = TtlDrops.id(level.getBlockState(new J.BlockPos(x, y + 8, z)))
        ctx.source.sendSystemMessage(Text.of(`drops test at ${x} ${y} ${z}: cleared ${n} block(s), the gravel is now ${left}`))
        server.scheduleInTicks(5, () => {
          var c = count(server, x, y, z)
          console.info(`[ttl] drops test: ${c.items} item(s), ${c.falling} falling block(s)`)
        })
        return 1
      })))
      .then(Commands.literal('expect')
        .then(Commands.literal('clean').then(xyz(ctx => (server, x, y, z) => {
          var c = count(server, x, y, z)
          if (c.items || c.falling) {
            ctx.source.sendSystemMessage(Text.red(`ttl: expected no item entities or falling blocks round ${x} ${y} ${z}, found ${c.items} item(s), ${c.falling} falling block(s)`))
            return 0
          }
          ctx.source.sendSystemMessage(Text.of(`drops: nothing on the ground round ${x} ${y} ${z} as expected`))
          return 1
        }))))
      .then(Commands.literal('sweep').then(xyz(ctx => (server, x, y, z) => {
        // a 9 x 9 sweep round x z of everything younger than 100 ticks (players' surroundings excepted), for the test
        var r = TtlDrops.sweep(server, TtlLife.OVERWORLD, { x0: x - 4, z0: z - 4, x1: x + 4, z1: z + 4 }, 100, `test sweep ${x} ${y} ${z}`)
        ctx.source.sendSystemMessage(Text.of(`drops: swept ${r ? r.items : '?'} item(s), set down ${r ? r.falling : '?'} falling block(s)`))
        return r ? 1 : 0
      })))))
})
