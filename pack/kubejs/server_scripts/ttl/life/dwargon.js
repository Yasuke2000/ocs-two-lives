// Places the Armed Nation of Dwargon (blueprints/dwargon.py → structures ttl:dwargon_0..n, one z slab each) in
// Lerfing's grey Canaat massif: carved INTO the real mountain (owner, 19/11/2026; WP-L7b), the gate facing south
// onto the apron and the road to Tempest. Bump TTL_DWARGON_VERSION after changing the blueprint or the placement; a
// world reset or the import of the overworld places it again (world_reset.js).
//
// Carve (TtlDwargonFootprint, generated/dwargon_footprint.js, written by tools/build_structures.py): the structures
// hold the city, the cavern's air with a 2-block lining of rock, and the open air of the cleft in front of the gate
// and of the skylight crack up to the top of the box; the rest of the box is left out, so Lerfing's rock stays above
// and around the city. GATE and BASE were chosen offline on the real heights (tools/lerfing/dwargon_fit.py: >= 6
// blocks of rock over every closed column, the forecourt running out onto the apron at the south edge).
// 1. hold the box + margin with chunk tickets (life/chunk_hold.js: generated in the background, no synchronous
//    `forceload` burst), wait at least 10 s and until every chunk is FULL (at most 10 min, then not placed);
// 2. read the real ground per column (heightmaps) BEFORE placing; the base layer is BASE (without it: the road in
//    front of the gate at the median ground height of the approach probes); log the rock cover over the city;
// 3. place the slabs, one every 2 ticks (the structure air carves the cavern, the cleft and the crack);
// 4. clear terrain above the open-sky columns that the box top does not reach (none on Lerfing's massif);
// 5. fill only gaps: under footprint columns down to the ground (the forecourt where the apron is lower than the
//    road) plus a 1:1 talus skirt round the edges, in the Canaat bands of WP-L7a; FILLS_PER_TICK fills per tick.
// 5b. terrain repair (life/repair.js): caves, lava and water under the city filled; columns the blueprint leaves
//    empty are the real mountain, so they only get the ring rules (pits and crevices closed, never above the road
//    level), all in the Canaat palette (no second slab pass, so the repair never touches a block the blueprint
//    defines, explicit air included: `bottom`).
// 5c. seal (carve mode): water, lava and waterlogged blocks in the real mountain's cells that touch the carved air
//    become tuff (footprint `shell`, seal()); every fluid in the city's own cells goes (drain()); the slabs are laid
//    again. Twice, for fluid still on its way through a cave behind the rim.
// 6. the throne room's banners get their canon Dwargon patterns (TtlDwargonRoyal.banners; structure files built
//    from code carry no block entity data).
// King Gazel (TtlDwargonGazel): tensura:gazel_dwargo seated on his throne, checked every 30 s while the throne
// is loaded and summoned again when missing. He shows a boss bar and wakes on right-click unless tamed, so he
// gets a dummy Owner (no real player), NoAI, Invulnerable, Silent, PersistenceRequired; Phase 0 = seated.
const TTL_DWARGON_VERSION = 12

const TtlDwargon = {
  // The arrival point in front of the gate (blueprint TtlDwargonFootprint.arrival), rotation none: the gate faces
  // south. At the foot of the escarpment on the Canaat's south flank (the plateau above it at y 200-215 holds the
  // cavern), 1,440 blocks north of Tempest (design/data/anchors.toml dwargon; tools/lerfing/dwargon_fit.py).
  GATE: { x: 1878, z: -544 },
  // World y of the blueprint's layer 0 (the road at y BASE + 3, the arrival at BASE + 4): the road meets the apron
  // at the box's south edge and the rock over the city is 7 blocks at its thinnest (median 28). null = old fit.
  BASE: 142,
  COVER: 6,
  PROBE: 'ttl_dwargon_probe',
  FILLS_PER_TICK: 150,
  SEAL_MS: 15,
  FALLBACK_DEPTH: 48,
  BANDED: 12,
  // The Canaat's sloping-ground mix (blueprints/dwargon.py CANAAT_SLOPE, sampled from Lerfing's map), one entry
  // per 4-block band, in about the map's proportions: clay 30 %, gravel/cobblestone/stone 20 % each, 5 % tuff and
  // light gray terracotta. Fills below the banded top are stone, like the map under its ~7-block cover.
  BANDS: ['clay', 'gravel', 'cobblestone', 'stone', 'clay', 'light_gray_terracotta', 'gravel', 'clay', 'cobblestone',
    'stone', 'clay', 'gravel', 'cobblestone', 'stone', 'clay', 'gravel', 'stone', 'cobblestone', 'clay', 'tuff'],

  run(server, cmd) {
    return server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  // Blueprint corner (x0, z0) in the world, and the worked area (box + margin, inclusive).
  box() {
    var f = TtlDwargonFootprint
    var x0 = this.GATE.x - f.arrival[0]
    var z0 = this.GATE.z - f.arrival[2]
    var m = f.margin
    return { x0: x0, z0: z0, ax0: x0 - m, az0: z0 - m, ax1: x0 + f.size[0] + m - 1, az1: z0 + f.size[2] + m - 1 }
  },


  decode(rle, n) {
    var out = new Array(n)
    var i = 0
    for (var k = 0; k < rle.length; k += 2) {
      for (var c = 0; c < rle[k + 1]; c++) out[i++] = rle[k]
    }
    return out
  },

  // Heightmaps (first free y above the ground) through Java; null when that fails, then marker probes and
  // fixed-depth `replace air` fills are used instead.
  heightmaps(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var hm = {
        ground: (x, z) => level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z),
        top: (x, z) => level.getHeight(Types.MOTION_BLOCKING, x, z)
      }
      hm.ground(this.GATE.x, this.GATE.z)
      return hm
    } catch (e) {
      console.warn(`[ttl] dwargon: heightmaps unavailable (${e}); using marker probes and fixed depths`)
      return null
    }
  },

  markerY(server, x, z) {
    var probe = this.PROBE
    this.run(server, `positioned ${x} 0 ${z} positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~ {Tags:["${probe}"]}`)
    var y = null
    server.getLevel(TtlLife.OVERWORLD).getEntities().forEach(e => {
      if (e.getTags().contains(probe)) y = Math.floor(e.getY())
    })
    this.run(server, `kill @e[type=minecraft:marker,tag=${probe}]`)
    return y
  },

  // Base layer: BASE when set (the carve), else the arrival y (one above the road block) at the median ground height
  // of the approach probes. The probes are logged either way.
  chooseBase(server, hm) {
    var f = TtlDwargonFootprint
    var b = this.box()
    var ys = []
    for (var i = 0; i < f.probes.length; i++) {
      var x = b.x0 + f.probes[i][0]
      var z = b.z0 + f.probes[i][1]
      var y = hm ? hm.ground(x, z) : this.markerY(server, x, z)
      if (y !== null && y > -64) ys.push(y)
    }
    if (ys.length === 0) return null
    ys.sort((a, c) => a - c)
    var median = ys[Math.floor(ys.length / 2)]
    console.info(`[ttl] dwargon: approach ground ${ys[0]}..${ys[ys.length - 1]} over ${ys.length} probes, median ${median}`)
    if (typeof this.BASE === 'number') return this.BASE
    return median - f.arrival[1]
  },

  // Rock over the city from the heightmaps read before placing (footprint `roof` = highest interior air per closed
  // column): logged, and a warning when any column has less than COVER blocks (the import is not what the fit saw).
  coverReport(hm, base) {
    var f = TtlDwargonFootprint
    if (!hm || !f.roof) return null
    var b = this.box()
    var w = f.grid[0]
    var roof = this.decode(f.roof, w * f.grid[1])
    var cov = []
    for (var i = 0; i < roof.length; i++) {
      if (roof[i] === f.none) continue
      cov.push(hm.ground(b.ax0 + i % w, b.az0 + Math.floor(i / w)) - 1 - (base + roof[i]))
    }
    if (cov.length === 0) return null
    cov.sort((a, c) => a - c)
    var thin = 0
    for (var k = 0; k < cov.length && cov[k] < this.COVER; k++) thin++
    var line = `rock cover over ${cov.length} columns min ${cov[0]}, median ${cov[Math.floor(cov.length / 2)]}, ${thin} under ${this.COVER}`
    if (thin > 0) console.warn(`[ttl] dwargon: ${line} (the skirt fills what it can; see tools/lerfing/dwargon_fit.py)`)
    else console.info(`[ttl] dwargon: ${line}`)
    return line
  },

  hash(x, z) {
    // Small multipliers keep every product exact in doubles (no Math.imul needed in Rhino).
    var n = ((x * 73856) ^ (z * 19349)) | 0
    n = ((n ^ (n >>> 13)) * 5741) | 0
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296
  },

  // Banded rock like the mountain's strata: one fill per 4-block band of the column.
  // Only the top BANDED blocks are banded; deeper gaps get one stone fill (keeps the command count down).
  rockCommands(x, z, y1, y2, base, replaceAir, out) {
    var off = Math.floor(this.hash(x >> 3, z >> 3) * 4)
    var streak = this.hash(x, z) < 0.07 ? (this.hash(z, x) < 0.5 ? 'stone' : 'andesite') : null
    var bands = this.BANDS
    var tail = replaceAir ? ' replace minecraft:air' : ''
    var y = y1
    if (y2 - y1 >= this.BANDED) {
      out.push(`fill ${x} ${y1} ${z} ${x} ${y2 - this.BANDED} ${z} minecraft:${streak || 'stone'}${tail}`)
      y = y2 - this.BANDED + 1
    }
    while (y <= y2) {
      var band = Math.floor((y - base + off) / 4)
      var end = Math.min(y2, base - off + band * 4 + 3)
      var mat = streak || bands[((band % bands.length) + bands.length) % bands.length]
      out.push(`fill ${x} ${y} ${z} ${x} ${end} ${z} minecraft:${mat}${tail}`)
      y = end + 1
    }
  },

  // Every terrain command, worked out from the heightmaps as they were before the structure went in.
  terrainCommands(hm, base) {
    var f = TtlDwargonFootprint
    var b = this.box()
    var n = f.grid[0] * f.grid[1]
    var fill = this.decode(f.fill, n)
    var clear = this.decode(f.clear, n)
    var clears = []
    var fills = []
    for (var gz = 0; gz < f.grid[1]; gz++) {
      for (var gx = 0; gx < f.grid[0]; gx++) {
        var i = gz * f.grid[0] + gx
        var x = b.ax0 + gx
        var z = b.az0 + gz
        if (clear[i] !== f.none) {
          var c1 = base + clear[i]
          var c2 = hm ? hm.top(x, z) - 1 : c1 + this.FALLBACK_DEPTH
          if (c2 >= c1) clears.push(`fill ${x} ${c1} ${z} ${x} ${c2} ${z} minecraft:air`)
        }
        if (fill[i] !== f.none) {
          var f2 = base + fill[i] - 1
          var f1 = hm ? hm.ground(x, z) : f2 - this.FALLBACK_DEPTH
          if (f2 >= f1) this.rockCommands(x, z, f1, f2, base, !hm, fills)
        }
      }
    }
    return clears.concat(fills)
  },

  // life/repair.js over the box and its margin: `bottom` (lowest defined block, explicit air included) marks the city's
  // columns; empty box columns with a talus value are slopes like the margin, the others plain ground at the road level.
  repairSpec(base) {
    var f = TtlDwargonFootprint
    var b = this.box()
    var w = f.grid[0]
    var n = w * f.grid[1]
    var fill = this.decode(f.fill, n)
    var bottom = f.bottom ? this.decode(f.bottom, n) : fill
    var carve = typeof this.BASE === 'number'
    var m = f.margin
    return {
      label: 'dwargon', enabled: true, dimension: TtlLife.OVERWORLD, ring: m, x0: b.ax0, z0: b.az0, w: w, l: f.grid[1],
      ground: base + f.arrival[1] - 1, depth: TtlRepair.DEPTH, keepWater: false,
      // The Canaat's own blocks (WP-L7a): clay and tuff, which do not fall like its gravel would over a filled gap.
      mat: { top: 'minecraft:clay', fill: 'minecraft:tuff', deep: 'minecraft:stone' },
      col: (gx, gz) => {
        var i = gz * w + gx
        var inBox = gx >= m && gz >= m && gx < m + f.size[0] && gz < m + f.size[2]
        if (inBox && bottom[i] !== f.none) return { t: 'build', bottom: base + bottom[i] }
        if (fill[i] !== f.none) return { t: 'ring', slope: base + fill[i] - 1 }
        // Carved: an empty box column is Lerfing's mountain, not a plain to continue at the road level.
        return inBox && !carve ? { t: 'ground' } : { t: 'ring', slope: null }
      }
    }
  },

  runBatched(server, cmds, done) {
    var self = this
    var i = 0
    var step = () => {
      try {
        var end = Math.min(cmds.length, i + self.FILLS_PER_TICK)
        for (; i < end; i++) self.run(server, cmds[i])
      } catch (e) {
        console.error(`[ttl] dwargon terrain step failed at ${i}: ${e}`)
        done(false)
        return
      }
      if (i < cmds.length) server.scheduleInTicks(1, step)
      else done(true)
    }
    step()
  },

  place(server, done) {
    var f = TtlDwargonFootprint
    var b = this.box()
    var hm = this.heightmaps(server)
    var base = this.chooseBase(server, hm)
    if (base === null) {
      console.warn('[ttl] dwargon: no ground found at the approach; not placed')
      done(false)
      return
    }
    var cover = this.coverReport(hm, base)
    var cmds = this.terrainCommands(hm, base)
    var self = this
    var part = 0
    var placeNext = () => {
      try {
        if (part < f.parts.length) {
          var name = f.parts.length > 1 ? `ttl:dwargon_${part}` : 'ttl:dwargon'
          var r = self.run(server, `place template ${name} ${b.x0} ${base} ${b.z0 + f.parts[part]}`)
          if (r === 0) console.warn(`[ttl] dwargon: place template ${name} reported failure`)
          part++
          server.scheduleInTicks(2, placeNext)
          return
        }
      } catch (e) {
        console.error(`[ttl] dwargon placement failed at slab ${part}: ${e}`)
        done(false)
        return
      }
      console.info(`[ttl] dwargon: ${f.parts.length} slab(s) placed, ${cmds.length} terrain commands (${self.FILLS_PER_TICK}/tick)`)
      var after = ok => {
        var gy = base + f.arrival[1]
        if (ok) self.royalBanners(server, b, base)
        if (ok) {
          server.persistentData.putInt('ttl.dwargon.version', TTL_DWARGON_VERSION)
          server.persistentData.putInt('ttl.dwargon.base', base)
          server.persistentData.putString('ttl.dwargon.gate', `${self.GATE.x + 0.5} ${gy} ${self.GATE.z + 0.5}`)
          server.persistentData.putString('ttl.dwargon.cover', cover || '')
          TtlDwargonGazel.replace(server)
        }
        console.info(`[ttl] dwargon placed: corner ${b.x0} ${base} ${b.z0}, gate at ${self.GATE.x} ${gy} ${self.GATE.z} (version ${TTL_DWARGON_VERSION}, terrain ${ok ? 'done' : 'FAILED'})`)
        done(ok)
      }
      self.runBatched(server, cmds, ok => {
        if (!ok) {
          after(false)
          return
        }
        TtlRepair.repair(server, self.repairSpec(base), res => {
          server.persistentData.putString('ttl.dwargon.repair', res ? `${res.foundation} ${res.skirt} ${res.lava}` : '')
          // 5c: seal the rim, drain the city, lay the slabs again (carpets back), and all that once more for fluid
          // that was on its way through a cave behind the rim while the first round ran.
          var round = (k, log, next) => self.seal(server, b, base, s => self.drain(server, b, base, d => self.slabs(server, b, base, () => {
            log.push(s ? `${s.water} water, ${s.lava} lava sealed, ${d === null ? '?' : d} drained` : 'failed')
            if (k > 1) round(k - 1, log, next)
            else next(log)
          })))
          round(2, [], log => {
            server.persistentData.putString('ttl.dwargon.seal', log.join(' / '))
            after(true)
          })
        })
      })
    }
    placeNext()
  },

  // The slabs once more (one every 2 ticks), then next(): every cell the blueprint defines, explicit air included, is
  // set again, so water or lava that flowed into the carve before the seal is gone and the carpets are back.
  slabs(server, b, base, next) {
    var f = TtlDwargonFootprint
    var self = this
    var part = 0
    var step = () => {
      try {
        if (part < f.parts.length) {
          var name = f.parts.length > 1 ? `ttl:dwargon_${part}` : 'ttl:dwargon'
          self.run(server, `place template ${name} ${b.x0} ${base} ${b.z0 + f.parts[part]}`)
          part++
          server.scheduleInTicks(2, step)
          return
        }
      } catch (e) {
        console.error(`[ttl] dwargon: slab pass failed at ${part}: ${e}`)
      }
      next()
    }
    step()
  },

  // 5c. Seal (carve mode): every cell of the footprint's `shell` (the real mountain's cells touching the carved air) that
  // holds water or lava becomes rock. Lerfing's map has springs and lava pockets inside the Canaat; cut open, they
  // poured into the city (staging 19/11/2026: two springs at the skylight crack's rim at y 200 flooded 2,253 cells of the
  // throne hall and the forge street; lava pockets at the cleft's west wall ran into the gate court). Budgeted per tick;
  // done({water, lava}) or done(null).
  seal(server, b, base, done) {
    var f = TtlDwargonFootprint
    var shell = f.shell || []
    var res = { water: 0, lava: 0 }
    if (shell.length === 0) {
      done(res)
      return
    }
    var self = this
    var level = server.getLevel(TtlLife.OVERWORLD)
    var BlockPos
    var rock
    try {
      BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
      rock = Java.loadClass('net.minecraft.world.level.block.Blocks').TUFF.defaultBlockState()
    } catch (e) {
      console.error(`[ttl] dwargon: seal unavailable (${e})`)
      done(null)
      return
    }
    var w = f.grid[0]
    var k = 0
    var y = null
    var step = () => {
      var t0 = Date.now()
      try {
        while (k < shell.length) {
          var x = b.ax0 + shell[k] % w
          var z = b.az0 + Math.floor(shell[k] / w)
          if (y === null) y = base + shell[k + 1]
          var y2 = base + shell[k + 2]
          while (y <= y2) {
            // Any fluid: a water or lava block, and a waterlogged block too (locally the crack's spring was a
            // waterlogged glow lichen in a cave at the rim, y 201).
            var pos = new BlockPos(x, y, z)
            var fs = level.getFluidState(pos)
            if (!fs.isEmpty()) {
              level.setBlock(pos, rock, 2)
              if (String(fs.getType()).indexOf('lava') >= 0) res.lava++
              else res.water++
            }
            y++
            if (Date.now() - t0 >= self.SEAL_MS) {
              server.scheduleInTicks(1, step)
              return
            }
          }
          k += 3
          y = null
        }
      } catch (e) {
        console.error(`[ttl] dwargon: seal failed: ${e}`)
        done(null)
        return
      }
      console.info(`[ttl] dwargon: sealed the carve's rim: ${res.water} water and ${res.lava} lava cells turned to tuff ` +
        `(${shell.length / 3} shell runs)`)
      done(res)
    }
    step()
  },

  // 5c, before each slab pass: every fluid inside the city's columns (from the lowest defined block up to the highest
  // interior air, or to the box top over the cleft and the crack: cells the blueprint defines) goes. Water and lava
  // blocks become air, waterlogged blocks dry. Without it the slab pass sets the lanterns, chains and cogwheels it
  // places into flowing water waterlogged (`place template` keeps liquids), and each is a spring of its own. The
  // pass then sets what the blueprint really has there (the fountain's water, the waterlogged throne runner).
  // done(cells) or done(null).
  drain(server, b, base, done) {
    var f = TtlDwargonFootprint
    var self = this
    var level = server.getLevel(TtlLife.OVERWORLD)
    var BlockPos
    var AIR
    var WET
    var DRY
    try {
      BlockPos = Java.loadClass('net.minecraft.core.BlockPos')
      AIR = Java.loadClass('net.minecraft.world.level.block.Blocks').AIR.defaultBlockState()
      WET = Java.loadClass('net.minecraft.world.level.block.state.properties.BlockStateProperties').WATERLOGGED
      DRY = Java.loadClass('java.lang.Boolean').FALSE
    } catch (e) {
      console.error(`[ttl] dwargon: drain unavailable (${e})`)
      done(null)
      return
    }
    var w = f.grid[0]
    var m = f.margin
    var n = w * f.grid[1]
    var bottom = this.decode(f.bottom, n)
    var roof = this.decode(f.roof, n)
    var clear = this.decode(f.clear, n)
    var i = 0
    var y = null
    var cells = 0
    var step = () => {
      var t0 = Date.now()
      try {
        while (i < n) {
          var gx = i % w
          var gz = Math.floor(i / w)
          var inBox = gx >= m && gz >= m && gx < m + f.size[0] && gz < m + f.size[2]
          var top = roof[i] !== f.none ? roof[i] : clear[i] !== f.none ? f.size[1] - 1 : null
          if (!inBox || bottom[i] === f.none || top === null) {
            i++
            continue
          }
          if (y === null) y = base + bottom[i]
          while (y <= base + top) {
            var pos = new BlockPos(b.ax0 + gx, y, b.az0 + gz)
            if (!level.getFluidState(pos).isEmpty()) {
              var st = level.getBlockState(pos)
              level.setBlock(pos, st.hasProperty(WET) ? st.setValue(WET, DRY) : AIR, 2)
              cells++
            }
            y++
            if (Date.now() - t0 >= self.SEAL_MS) {
              server.scheduleInTicks(1, step)
              return
            }
          }
          i++
          y = null
        }
      } catch (e) {
        console.error(`[ttl] dwargon: drain failed: ${e}`)
        done(null)
        return
      }
      console.info(`[ttl] dwargon: drained ${cells} fluid cells inside the city before the slab pass`)
      done(cells)
    }
    step()
  },

  royalBanners(server, b, base) {
    var n = 0
    var self = this
    TtlDwargonRoyal.banners.forEach(e => {
      if (self.run(server, `data merge block ${b.x0 + e[0]} ${base + e[1]} ${b.z0 + e[2]} {patterns:${e[3]}}`) > 0) n++
    })
    console.info(`[ttl] dwargon: ${n}/${TtlDwargonRoyal.banners.length} throne room banners patterned`)
  },

  schedule(server) {
    var self = this
    var b = this.box()
    var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, { x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 }, 'dwargon')
    var finish = () => TtlChunks.release(server, hold)
    server.scheduleInTicks(200, () => TtlChunks.whenReady(server, hold, 40, 12000, (ready, missing) => {
      if (!ready && missing > 0) {
        console.error(`[ttl] dwargon: ${missing} chunk(s) still not loaded after 10 min; not placed (next boot tries again)`)
        finish()
        return
      }
      try {
        self.place(server, finish)
      } catch (e) {
        console.error(`[ttl] dwargon placement failed: ${e}`)
        finish()
      }
    }))
  }
}

const TtlDwargonGazel = {
  TAG: 'ttl_gazel',
  NBT: '{NoAI:1b,Invulnerable:1b,Silent:1b,PersistenceRequired:1b,Phase:0,Owner:[I;0,0,0,1],' +
    'Rotation:[0f,0f],Tags:["ttl_gazel"]}',

  // World position of the seat, or null while Dwargon (this version) is not placed.
  seat(server) {
    var pd = server.persistentData
    if (pd.getInt('ttl.dwargon.version') !== TTL_DWARGON_VERSION) return null
    var b = TtlDwargon.box()
    var g = TtlDwargonRoyal.gazel
    return `${b.x0 + g[0]} ${pd.getInt('ttl.dwargon.base') + g[1]} ${b.z0 + g[2]}`
  },

  find(server) {
    var found = []
    var tag = this.TAG
    server.getLevel(TtlLife.OVERWORLD).getEntities().forEach(e => {
      if (e.isAlive() && e.getTags().contains(tag)) found.push(e)
    })
    return found
  },

  // Exactly one Gazel, only while his throne is loaded (never summoned into an unloaded chunk).
  ensure(server) {
    var pos = this.seat(server)
    if (pos === null) return
    // WP-W2: the seated king steps aside while his fight (bosses.toml gazel_dwargo, spawn.kind statue) is out.
    try { if (typeof TtlBoss !== 'undefined' && typeof TtlBoss.statueAside === 'function' && TtlBoss.statueAside(server, 'gazel_dwargo')) { this.find(server).forEach(e => e.discard()); return } } catch (e) { console.error(`[ttl] dwargon: asking the boss framework about Gazel's fight failed: ${e}`) }
    var found = this.find(server)
    found.slice(1).forEach(e => e.discard())
    if (found.length > 0) return
    var r = TtlDwargon.run(server, `execute if loaded ${pos} run summon tensura:gazel_dwargo ${pos} ${this.NBT}`)
    if (r > 0) console.info(`[ttl] dwargon: King Gazel seated at ${pos}`)
  },

  replace(server) {
    this.find(server).forEach(e => e.discard())
    this.ensure(server)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var check = () => {
    try {
      TtlDwargonGazel.ensure(server)
    } catch (e) {
      console.error(`[ttl] dwargon gazel check failed: ${e}`)
    }
    server.scheduleInTicks(600, check)
  }
  server.scheduleInTicks(100, check)
  if (server.persistentData.getInt('ttl.dwargon.version') === TTL_DWARGON_VERSION) return
  TtlDwargon.schedule(server)
})
