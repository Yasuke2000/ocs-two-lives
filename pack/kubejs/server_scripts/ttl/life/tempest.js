// Places early Tempest (blueprints/tempest.py → structures ttl:tempest_0..n, one z slab each) in the Tensura
// world: the hobgoblin village just after the ogres joined, in a forest clearing. Its arrival point (the south
// edge of the village green, signpost beside it) goes on world 0, 0, the Life 2 world spawn. canon_regions.json
// puts the Tempest landmark at ref [1790, 1122] → about (-10, -70), within the fan map's precision of 0, 0;
// change LANDMARK to move it. Bump TTL_TEMPEST_VERSION after changing the blueprint; a world reset of the
// overworld places it again on the new terrain (world_reset.js).
//
// Grounding (TtlTempestFootprint, generated/tempest_footprint.js, written by tools/build_structures.py from
// blueprints/_footprint.py):
// 1. forceload the box + margin, wait 15 s for generation;
// 2. read the real terrain per column BEFORE placing: heightmap MOTION_BLOCKING_NO_LEAVES, then down through
//    logs, leaves and plants, so trees do not count as ground; the base layer is chosen so the village ground
//    sits at the median terrain height of the probes across the clearing;
// 3. place the slabs, one every 2 ticks (the box holds air above the ground layer: trees and hills in it go);
// 4. clear terrain above the box, and cut 1:1 slopes into hills round it (only where the terrain itself rises
//    above the slope, so the surrounding forest stays standing);
// 5. fill the gap under every box column down to the terrain (dirt, stone deeper down), plus a 1:1 earth
//    skirt topped with grass round the edges; FILLS_PER_TICK one-column fills per tick;
// 6. set the world spawn on the arrival point and write the signpost texts;
// 7. give the containers from Tensura's goblin village pieces their Tensura loot tables (the structure files
//    carry blocks only) and summon the goblin quarter's residents (TtlTempestExtras, generated/tempest_extras.js)
//    on Tensura's own goblin spawn points: hobgoblins (EvoState 1; every goblin evolved when Rimuru named them),
//    persistent, tagged RESIDENT. Residents from an earlier version are removed first, so each version spawns
//    them once.
const TTL_TEMPEST_VERSION = 2

const TtlTempest = {
  // World position of the arrival point; its blueprint coordinates are TtlTempestFootprint.arrival.
  LANDMARK: { x: 0, z: 0 },
  PROBE: 'ttl_tempest_probe',
  RESIDENT: 'ttl_tempest_resident',
  FILLS_PER_TICK: 150,
  FALLBACK_DEPTH: 24,
  DELAY_TICKS: 300,
  // Signpost faces, blueprint offsets from the arrival point (see blueprints/tempest.py, SIGNPOST).
  SIGNS: [
    { dx: 1, dz: 0, lines: ['Tempest', 'Village of', 'Rimuru', '<- forge'] },
    { dx: 2, dz: -1, lines: ['', 'Meeting hall', '^', ''] },
    { dx: 3, dz: 0, lines: ['', "Shuna's", 'weaving hut', '->'] },
    { dx: 2, dz: 1, lines: ['', 'South gate', 'and fields', 'v'] }
  ],
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest'],

  run(server, cmd) {
    return server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  // Blueprint corner (x0, z0) in the world, and the worked area (box + margin, inclusive).
  box() {
    var f = TtlTempestFootprint
    var x0 = this.LANDMARK.x - f.arrival[0]
    var z0 = this.LANDMARK.z - f.arrival[2]
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

  // Heightmaps through Java: ground = first free y above the terrain (trees and plants skipped), top = first
  // free y above everything that blocks motion (leaves included). null when that fails; then marker probes
  // and fixed-depth `replace air` fills are used instead.
  heightmaps(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var skip = this.NOT_GROUND
      var hm = {
        top: (x, z) => level.getHeight(Types.MOTION_BLOCKING, x, z),
        ground: (x, z) => {
          var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
          for (var n = 0; n < 40 && y > -63; n++) {
            var id = String(level.getBlock(x, y - 1, z).id)
            if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
            y--
          }
          return y
        }
      }
      hm.ground(this.LANDMARK.x, this.LANDMARK.z)
      return hm
    } catch (e) {
      console.warn(`[ttl] tempest: heightmaps unavailable (${e}); using marker probes and fixed depths`)
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

  // Base layer: the village ground (layer f.ground) one below the median terrain height of the probes.
  chooseBase(server, hm) {
    var f = TtlTempestFootprint
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
    console.info(`[ttl] tempest: clearing ground ${ys[0]}..${ys[ys.length - 1]} over ${ys.length} probes, median ${median}`)
    return median - f.arrival[1]
  },

  // Earth fill for one column: stone deep down, dirt in the top three, grass on top outside the box.
  earthCommands(x, z, y1, y2, grass, replaceAir, out) {
    var r = replaceAir ? ' replace minecraft:air' : ''
    var dirtFrom = Math.max(y1, y2 - 2)
    if (dirtFrom > y1) out.push(`fill ${x} ${y1} ${z} ${x} ${dirtFrom - 1} ${z} minecraft:stone${r}`)
    if (grass) {
      if (y2 > dirtFrom) out.push(`fill ${x} ${dirtFrom} ${z} ${x} ${y2 - 1} ${z} minecraft:dirt${r}`)
      out.push(`fill ${x} ${y2} ${z} ${x} ${y2} ${z} minecraft:grass_block${r}`)
    } else {
      out.push(`fill ${x} ${dirtFrom} ${z} ${x} ${y2} ${z} minecraft:dirt${r}`)
    }
  },

  // Every terrain command, worked out from the heightmaps as they were before the structure went in.
  terrainCommands(hm, base) {
    var f = TtlTempestFootprint
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
        var inBox = gx >= f.margin && gz >= f.margin && gx < f.margin + f.size[0] && gz < f.margin + f.size[2]
        var ground = hm ? hm.ground(x, z) : null
        if (clear[i] !== f.none) {
          var c1 = base + clear[i]
          if (inBox) {
            var c2 = hm ? hm.top(x, z) - 1 : c1 + this.FALLBACK_DEPTH
            if (c2 >= c1) clears.push(`fill ${x} ${c1} ${z} ${x} ${c2} ${z} minecraft:air`)
          } else if (hm && ground - 1 >= c1) {
            clears.push(`fill ${x} ${c1} ${z} ${x} ${hm.top(x, z) - 1} ${z} minecraft:air`)
          }
        }
        if (fill[i] !== f.none) {
          var f2 = base + fill[i] - 1
          var f1 = hm ? ground : f2 - this.FALLBACK_DEPTH
          if (f2 >= f1 && (inBox || hm)) this.earthCommands(x, z, f1, f2, !inBox, !hm, fills)
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
        console.error(`[ttl] tempest terrain step failed at ${i}: ${e}`)
        done(false)
        return
      }
      if (i < cmds.length) server.scheduleInTicks(1, step)
      else done(true)
    }
    step()
  },

  signs(server, gy) {
    for (var i = 0; i < this.SIGNS.length; i++) {
      var s = this.SIGNS[i]
      var x = this.LANDMARK.x + s.dx
      var z = this.LANDMARK.z + s.dz
      // Each line is a JSON text component inside a double-quoted SNBT string.
      var msgs = s.lines.map(t => '"' + JSON.stringify(t).replace(/"/g, '\\"') + '"').join(',')
      this.run(server, `data merge block ${x} ${gy + 1} ${z} {is_waxed:1b,front_text:{messages:[${msgs}]}}`)
    }
  },

  // Loot tables and residents (blueprint coordinates in TtlTempestExtras, placed with corner x0, base, z0).
  extras(server, base) {
    var b = this.box()
    var e = TtlTempestExtras
    for (var i = 0; i < e.loot.length; i++) {
      var c = e.loot[i]
      this.run(server, `data merge block ${b.x0 + c[0]} ${base + c[1]} ${b.z0 + c[2]} {LootTable:"${c[3]}"}`)
    }
    this.run(server, `kill @e[type=tensura:goblin,tag=${this.RESIDENT}]`)
    var n = 0
    for (var j = 0; j < e.residents.length; j++) {
      var r = e.residents[j]
      var name = r[3] ? `,CustomName:'${JSON.stringify(r[3])}'` : ''
      n += this.run(server, `summon tensura:goblin ${b.x0 + r[0] + 0.5} ${base + r[1]} ${b.z0 + r[2] + 0.5} ` +
        `{PersistenceRequired:1b,EvoState:1,Tags:["${this.RESIDENT}"]${name}}`) > 0 ? 1 : 0
    }
    console.info(`[ttl] tempest: ${e.loot.length} loot containers, ${n}/${e.residents.length} goblin residents`)
  },

  place(server, done) {
    var f = TtlTempestFootprint
    var b = this.box()
    var hm = this.heightmaps(server)
    var base = this.chooseBase(server, hm)
    if (base === null) {
      console.warn('[ttl] tempest: no ground found in the clearing; not placed')
      done(false)
      return
    }
    var cmds = this.terrainCommands(hm, base)
    var self = this
    var part = 0
    var placeNext = () => {
      try {
        if (part < f.parts.length) {
          var name = f.parts.length > 1 ? `ttl:tempest_${part}` : 'ttl:tempest'
          var r = self.run(server, `place template ${name} ${b.x0} ${base} ${b.z0 + f.parts[part]}`)
          if (r === 0) console.warn(`[ttl] tempest: place template ${name} reported failure`)
          part++
          server.scheduleInTicks(2, placeNext)
          return
        }
      } catch (e) {
        console.error(`[ttl] tempest placement failed at slab ${part}: ${e}`)
        done(false)
        return
      }
      console.info(`[ttl] tempest: ${f.parts.length} slab(s) placed, ${cmds.length} terrain commands (${self.FILLS_PER_TICK}/tick)`)
      self.runBatched(server, cmds, ok => {
        var gy = base + f.arrival[1]
        try {
          self.signs(server, gy)
          self.run(server, `setworldspawn ${self.LANDMARK.x} ${gy} ${self.LANDMARK.z}`)
        } catch (e) {
          console.warn(`[ttl] tempest: signs or world spawn failed: ${e}`)
        }
        try {
          self.extras(server, base)
        } catch (e) {
          console.warn(`[ttl] tempest: loot tables or residents failed: ${e}`)
        }
        if (ok) {
          server.persistentData.putInt('ttl.tempest.version', TTL_TEMPEST_VERSION)
          server.persistentData.putInt('ttl.tempest.base', base)
          server.persistentData.putString('ttl.tempest.arrival', `${self.LANDMARK.x + 0.5} ${gy} ${self.LANDMARK.z + 0.5}`)
        }
        console.info(`[ttl] tempest placed: corner ${b.x0} ${base} ${b.z0}, arrival at ${self.LANDMARK.x} ${gy} ${self.LANDMARK.z} (version ${TTL_TEMPEST_VERSION}, terrain ${ok ? 'done' : 'FAILED'})`)
        done(ok)
      })
    }
    placeNext()
  },

  schedule(server) {
    var self = this
    this.forceload(server, 'add')
    server.scheduleInTicks(this.DELAY_TICKS, () => {
      var finish = () => self.forceload(server, 'remove')
      try {
        self.place(server, finish)
      } catch (e) {
        console.error(`[ttl] tempest placement failed: ${e}`)
        finish()
      }
    })
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  if (server.persistentData.getInt('ttl.tempest.version') === TTL_TEMPEST_VERSION) return
  TtlTempest.schedule(server)
})
