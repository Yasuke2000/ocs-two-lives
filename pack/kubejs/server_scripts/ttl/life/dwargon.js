// Places the Armed Nation of Dwargon (blueprints/dwargon.py → structures ttl:dwargon_0..n, one z slab each) in
// the Tensura world, in the southern mountains of Dwargon on the canon map (pack/config/ttl/canon_map.txt), its
// gate facing Jura and world spawn. Bump TTL_DWARGON_VERSION after changing the blueprint; a world reset of the
// overworld places it again on the new terrain (world_reset.js).
//
// Grounding (TtlDwargonFootprint, generated/dwargon_footprint.js, written by tools/build_structures.py):
// 1. forceload the box + margin, wait 10 s for generation;
// 2. read the real ground per column (heightmaps) BEFORE placing; the base layer is chosen so the road in
//    front of the gate sits at the median ground height of the approach probes;
// 3. place the slabs, one every 2 ticks;
// 4. clear terrain above the open-sky columns (road, ravine, skylight crack) and cut 1:1 slopes round them;
// 5. fill the gap under every footprint column down to the ground (nothing floats), plus a 1:1 talus skirt
//    round the edges, in banded sandstone like the mountain; FILLS_PER_TICK one-column fills per tick.
// 6. the throne room's banners get their canon Dwargon patterns (TtlDwargonRoyal.banners; structure files built
//    from code carry no block entity data).
// King Gazel (TtlDwargonGazel): tensura:gazel_dwargo seated on his throne, checked every 30 s while the throne
// is loaded and summoned again when missing. He shows a boss bar and wakes on right-click unless tamed, so he
// gets a dummy Owner (no real player), NoAI, Invulnerable, Silent, PersistenceRequired; Phase 0 = seated.
const TTL_DWARGON_VERSION = 5

const TtlDwargon = {
  // The arrival point in front of the gate; its blueprint coordinates are TtlDwargonFootprint.arrival.
  // At the foot of the Canaat Mountains (lore: the city fills a hollow at their base), ~270 blocks inside
  // Dwargon's southern border at the 14,000-block scale, facing the highway to Tempest.
  GATE: { x: 435, z: -1000 },
  PROBE: 'ttl_dwargon_probe',
  FILLS_PER_TICK: 150,
  FALLBACK_DEPTH: 48,
  BANDED: 12,
  BANDS: ['smooth_sandstone', 'sandstone', 'smooth_sandstone', 'white_terracotta', 'sandstone',
    'smooth_sandstone', 'terracotta', 'smooth_sandstone', 'sandstone', 'white_terracotta'],

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

  // forceload takes at most 256 chunks per command: add/remove the area in strips of 4 chunk rows.
  forceload(server, mode) {
    var b = this.box()
    for (var z = b.az0; z <= b.az1; z += 64) {
      this.run(server, `forceload ${mode} ${b.ax0} ${z} ${b.ax1} ${Math.min(z + 63, b.az1)}`)
    }
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

  // Base layer: arrival y (one above the road block) at the median ground height of the approach probes.
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
    return median - f.arrival[1]
  },

  hash(x, z) {
    // Small multipliers keep every product exact in doubles (no Math.imul needed in Rhino).
    var n = ((x * 73856) ^ (z * 19349)) | 0
    n = ((n ^ (n >>> 13)) * 5741) | 0
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296
  },

  // Banded rock like the mountain's strata: one fill per 4-block band of the column.
  // Only the top BANDED blocks are banded; deeper gaps get one sandstone fill (keeps the command count down).
  rockCommands(x, z, y1, y2, base, replaceAir, out) {
    var off = Math.floor(this.hash(x >> 3, z >> 3) * 4)
    var streak = this.hash(x, z) < 0.07 ? (this.hash(z, x) < 0.5 ? 'stone' : 'andesite') : null
    var bands = this.BANDS
    var tail = replaceAir ? ' replace minecraft:air' : ''
    var y = y1
    if (y2 - y1 >= this.BANDED) {
      out.push(`fill ${x} ${y1} ${z} ${x} ${y2 - this.BANDED} ${z} minecraft:${streak || 'sandstone'}${tail}`)
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
      self.runBatched(server, cmds, ok => {
        var gy = base + f.arrival[1]
        if (ok) self.royalBanners(server, b, base)
        if (ok) {
          server.persistentData.putInt('ttl.dwargon.version', TTL_DWARGON_VERSION)
          server.persistentData.putInt('ttl.dwargon.base', base)
          server.persistentData.putString('ttl.dwargon.gate', `${self.GATE.x + 0.5} ${gy} ${self.GATE.z + 0.5}`)
          TtlDwargonGazel.replace(server)
        }
        console.info(`[ttl] dwargon placed: corner ${b.x0} ${base} ${b.z0}, gate at ${self.GATE.x} ${gy} ${self.GATE.z} (version ${TTL_DWARGON_VERSION}, terrain ${ok ? 'done' : 'FAILED'})`)
        done(ok)
      })
    }
    placeNext()
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
    this.forceload(server, 'add')
    server.scheduleInTicks(200, () => {
      var finish = () => self.forceload(server, 'remove')
      try {
        self.place(server, finish)
      } catch (e) {
        console.error(`[ttl] dwargon placement failed: ${e}`)
        finish()
      }
    })
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
