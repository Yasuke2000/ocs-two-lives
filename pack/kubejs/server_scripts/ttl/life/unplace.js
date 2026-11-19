// Takes a placed structure out of the world again, block for block, for the placers that move something
// (life/landmarks.js: an old copy of a landmark, design/data/landmarks.toml `remove`; life/builds.js: the old copy of a
// build whose spot changed). It never clears a box: it reads the structure files the copy was placed from and removes a
// block only where the world still holds exactly the block the file put there, so Lerfing's terrain and anything else
// in the box stays. Cells the file leaves as air or structure_void are not touched.
//
// A job = one structure file placed at an origin: { template: 'ns:path', x, y, z, rotation (net.minecraft Rotation or
// null), ground (local y of the ground layer, default 0), terrain (true for a jigsaw piece with projection
// terrain_matching, whose blocks the game set onto the surface column by column) }.
// - Cells below the ground layer become `fill` (dirt), so a cellar does not leave a pit.
// - Ground-layer cells become the site's top block (`top`, e.g. grass or gravel) where the cell below is solid, else air
//   (a floating floor leaves nothing behind).
// - Cells above it become air.
// - terrain jobs: the column's offset is found again (the run of the file's blocks under the surface), the bottom cell
//   becomes `top`, the rest air.
// A unit (every job of one copy) is removed only when at least MIN_MATCH of its non-air cells still match: a copy that is
// not there (a spot that never got one, a world that was reset) is left alone and reported.
// Reads only loaded chunks (the caller holds them, life/chunk_hold.js) and works under a time budget per tick. Blocks go
// without drops (life/drops.js TtlDrops.replace: containers emptied first, nothing that leaned on them pops off).
const TtlUnplace = {
  BUDGET_MS: 15,
  MIN_MATCH: 0.5,
  TERRAIN_WINDOW: 8, // terrain jobs: how far below the surface the column's run may start
  cache: {},

  java() {
    if (this.j !== undefined) return this.j
    try {
      this.j = {
        ResourceLocation: Java.loadClass('net.minecraft.resources.ResourceLocation'),
        CompoundTag: Java.loadClass('net.minecraft.nbt.CompoundTag'),
        BlockPos: Java.loadClass('net.minecraft.core.BlockPos'),
        StructureTemplate: Java.loadClass('net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate'),
        StructurePlaceSettings: Java.loadClass('net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings'),
        Types: Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      }
    } catch (e) {
      console.error(`[ttl] unplace: Java classes unavailable (${e})`)
      this.j = null
    }
    return this.j
  },

  // The non-air cells of a structure file: [[x, y, z, id], ...] (jigsaw blocks as their final_state). null when missing.
  cells(server, template) {
    if (this.cache[template] !== undefined) return this.cache[template]
    var J = this.java()
    var out = null
    try {
      var opt = server.getLevel(TtlLife.OVERWORLD).getStructureManager().get(J.ResourceLocation.parse(template))
      if (opt.isPresent()) {
        var tag = opt.get().save(new J.CompoundTag())
        var palette = tag.contains('palette') ? tag.getList('palette', 10) : tag.getList('palettes', 9).getList(0)
        var names = []
        for (var p = 0; p < palette.size(); p++) names.push(String(palette.getCompound(p).getString('Name')))
        var blocks = tag.getList('blocks', 10)
        out = []
        for (var i = 0; i < blocks.size(); i++) {
          var b = blocks.getCompound(i)
          var id = names[b.getInt('state')]
          if (id === 'minecraft:jigsaw' && b.contains('nbt')) id = String(b.getCompound('nbt').getString('final_state')).split('[')[0].split('{')[0]
          if (!id || id === 'minecraft:air' || id === 'minecraft:cave_air' || id === 'minecraft:void_air' ||
            id === 'minecraft:structure_void' || id === 'minecraft:jigsaw' || id === 'minecraft:structure_block') continue
          var pos = b.getList('pos', 3)
          out.push([pos.getInt(0), pos.getInt(1), pos.getInt(2), id])
        }
      }
    } catch (e) {
      console.error(`[ttl] unplace: cannot read ${template} (${e})`)
      out = null
    }
    this.cache[template] = out
    return out
  },

  // World position of a file cell for a job (vanilla's rotation round the origin, no mirror, pivot 0).
  mover(job) {
    var J = this.java()
    if (!job.rotation) return (x, y, z) => [job.x + x, job.y + y, job.z + z]
    var settings = new J.StructurePlaceSettings().setRotation(job.rotation)
    return (x, y, z) => {
      var p = J.StructureTemplate.calculateRelativePosition(settings, new J.BlockPos(x, y, z))
      return [job.x + p.getX(), job.y + p.getY(), job.z + p.getZ()]
    }
  },

  // units: [{ label, jobs: [...] }]; opts { top, fill }; done({ removed, skipped, cells, missing: [labels] }).
  remove(server, dimension, units, opts, done) {
    var self = this
    var J = this.java()
    var finish = res => {
      try {
        done(res)
      } catch (e) {
        console.error(`[ttl] unplace: after removal: ${e}`)
      }
    }
    if (!J) {
      finish(null)
      return
    }
    var level = server.getLevel(dimension)
    var source = level.getChunkSource()
    var AIR = Java.loadClass('net.minecraft.world.level.block.Blocks').AIR.defaultBlockState()
    var state = id => {
      try {
        return Java.loadClass('net.minecraft.core.registries.BuiltInRegistries').BLOCK.get(J.ResourceLocation.parse(id)).defaultBlockState()
      } catch (e) {
        return AIR
      }
    }
    var TOP = state(opts.top || 'minecraft:grass_block')
    var FILL = state(opts.fill || 'minecraft:dirt')
    var loaded = (x, z) => source.getChunkNow(x >> 4, z >> 4) !== null
    var id = (x, y, z) => String(level.getBlock(x, y, z).id)
    var res = { removed: 0, skipped: 0, cells: 0, unloaded: 0, missing: [], done: [] }
    var drops = typeof TtlDrops !== 'undefined' && !!TtlDrops.java()
    // Work list: per unit, the cells to change ([x, y, z, kind]) after its match count. Built and applied in steps.
    var u = 0
    var phase = 'scan'
    var plan = null
    var k = 0
    var jobAt = 0
    var cellAt = 0
    var stepUnit = stop => {
      var unit = units[u]
      if (phase === 'scan') {
        if (plan === null) plan = { want: 0, hit: 0, ops: [] }
        while (jobAt < unit.jobs.length) {
          var job = unit.jobs[jobAt]
          var cells = self.cells(server, job.template)
          if (!cells) {
            jobAt++
            cellAt = 0
            continue
          }
          var at = self.mover(job)
          var g = job.ground || 0
          if (job.terrain) {
            // Group the file's cells per column, then find the column's run under today's surface.
            if (!job.cols) {
              job.cols = {}
              cells.forEach(c => {
                var key = c[0] + ',' + c[2]
                ;(job.cols[key] = job.cols[key] || []).push(c)
              })
              job.keys = Object.keys(job.cols)
            }
            while (cellAt < job.keys.length) {
              var col = job.cols[job.keys[cellAt++]]
              var w0 = at(col[0][0], 0, col[0][2])
              plan.want += col.length
              if (!loaded(w0[0], w0[2])) {
                res.unloaded++
                continue
              }
              var maxY = Math.max.apply(null, col.map(c => c[1]))
              // The game set the column on the WORLD_SURFACE of its day (leaves and plants included): search from
              // today's top down to a little under the ground.
              var top = level.getHeight(J.Types.WORLD_SURFACE, w0[0], w0[2])
              var floor = level.getHeight(J.Types.MOTION_BLOCKING_NO_LEAVES, w0[0], w0[2])
              // The offset where most of the column's cells match (the highest on a tie), at least half of them: a
              // lantern or a button may have popped since.
              var best = null
              var bestN = 0
              for (var y0 = top - 1 - maxY; y0 >= floor - 1 - maxY - self.TERRAIN_WINDOW; y0--) {
                var hits = col.filter(c => id(w0[0], y0 + c[1], w0[2]) === c[3])
                if (hits.length > bestN) {
                  best = { y0: y0, hits: hits }
                  bestN = hits.length
                }
              }
              if (best && bestN * 2 >= col.length) {
                plan.hit += bestN
                best.hits.forEach(c => plan.ops.push([w0[0], best.y0 + c[1], w0[2], c[1] === 0 ? 'top' : 'air']))
              }
              if (stop()) return false
            }
          } else {
            while (cellAt < cells.length) {
              var c = cells[cellAt++]
              var w = at(c[0], c[1], c[2])
              plan.want++
              if (!loaded(w[0], w[2])) res.unloaded++
              else if (id(w[0], w[1], w[2]) === c[3]) {
                plan.hit++
                plan.ops.push([w[0], w[1], w[2], c[1] < g ? 'fill' : c[1] === g ? 'ground' : 'air'])
              }
              if ((cellAt & 63) === 0 && stop()) return false
            }
          }
          jobAt++
          cellAt = 0
        }
        var share = plan.want ? plan.hit / plan.want : 0
        if (share < self.MIN_MATCH) {
          res.skipped++
          res.missing.push(unit.label)
          console.warn(`[ttl] unplace ${unit.label}: only ${plan.hit} of ${plan.want} cells match (${Math.round(share * 100)} %, ` +
            `needs ${Math.round(self.MIN_MATCH * 100)} %); not there any more, left alone`)
          return true
        }
        plan.share = share
        // Top-down, so a ground-layer cell sees the cells below it already removed or filled.
        plan.ops.sort((a, b) => b[1] - a[1])
        phase = 'apply'
        k = 0
      }
      while (k < plan.ops.length) {
        var o = plan.ops[k++]
        var pos = new J.BlockPos(o[0], o[1], o[2])
        var put = AIR
        if (o[3] === 'fill') put = FILL
        else if (o[3] === 'top') put = TOP
        else if (o[3] === 'ground') {
          var below = TtlRepair.cls(id(o[0], o[1] - 1, o[2]))
          put = below === 'solid' ? TOP : AIR
        }
        // Without drops: a chest or barrel of the copy would spill its loot, a plant or torch on it would pop off
        // (life/drops.js); flag 2 and the old behaviour where TtlDrops is not loaded.
        if (drops) TtlDrops.replace(level, o[0], o[1], o[2], put)
        else level.setBlock(pos, put, 2)
        if ((k & 63) === 0 && stop()) return false
      }
      res.removed++
      res.cells += plan.ops.length
      res.done.push(unit.label)
      console.info(`[ttl] unplace ${unit.label}: removed ${plan.ops.length} blocks (${Math.round(plan.share * 100)} % of the ` +
        `structure's ${plan.want} cells still matched)`)
      return true
    }
    var tick = () => {
      var t0 = Date.now()
      var stop = () => Date.now() - t0 >= self.BUDGET_MS
      try {
        while (u < units.length) {
          if (!stepUnit(stop)) {
            server.scheduleInTicks(1, tick)
            return
          }
          u++
          phase = 'scan'
          plan = null
          jobAt = 0
          cellAt = 0
          if (stop()) {
            server.scheduleInTicks(1, tick)
            return
          }
        }
      } catch (e) {
        console.error(`[ttl] unplace: failed at ${units[u] ? units[u].label : '?'}: ${e}`)
        finish(null)
        return
      }
      finish(res)
    }
    tick()
  }
}
