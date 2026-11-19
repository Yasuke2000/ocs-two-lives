// Generic placer for canon-location builds: every design/builds/<name>.toml (TtlData.builds, written by
// tools/gen_data.py; per-column ground data in generated/builds.js, TtlBuildFootprints) is a structure from
// blueprints/<name>.py (pack/kubejs/data/ttl/structure/<name>.nbt or the slabs <name>_0..n) that goes on its
// canon spot. Each build is placed once (persistentData ttl.build.<name>.version = its `version`), one at a time
// with a gap, after Tempest, Dwargon and the landmarks; bump `version` in the TOML to place it again, and
// world_reset.js places every build of a reset dimension again on the new terrain (TtlBuilds.reset).
// Op commands: /ttl build list | where <name> | place <name|all> [force] | expect <name> placed.
// (/ttl build <blueprint> from commands.js, a build at your feet, still works: only these four words are taken.)
//
// Per build (same grounding as tempest.js / dwargon.js, worked out from the structure files):
// 1. hold the area (box + margin + the survey radius) with chunk tickets (life/chunk_hold.js: loaded in the background,
//    never a synchronous `forceload` burst) and wait until every chunk is FULL; give up after LOAD_TIMEOUT;
// 2. where: the spot recorded by an earlier placement of this build (a version bump puts the new version over the
//    old one at the same corner) or, with ground = "fixed", x/z at y; with ground = "survey" the flattest dry spot
//    within `search` blocks of x/z: candidates on a grid, samples over the build's own columns (heightmaps, trees
//    and plants skipped); a lava or void sample rules a candidate out, so does more than `max_wet` of the samples
//    over water or ice, or a keepout (Tempest, Dwargon, placed landmarks and builds, KEEPOUT blocks); score = 2 x
//    mean deviation from the median ground height + half the p10..p90 spread + distance/16 + WET_COST x the water
//    share (lower is better); the anchor's y is that median;
// 3. read the real terrain per column BEFORE placing, then place the slabs, one every 2 ticks;
// 4. terrain fit (clear_above for step b): a) under every column of the box that has blocks: fill the gap between
//    the terrain (the bed, under water) and the column's lowest block (dirt, stone deeper down), so nothing floats; b) above the column's
//    highest block: clear trees and hills up to the sky; c) round the box a 1:1 skirt (`margin` columns) falling
//    away from the ground layer (the block under the anchor) and a 1:1 cut into hills, grass (sand, red sand) on top;
// 4b. place the slabs a second time on the finished ground (supported blocks that popped in the first pass);
// 5. record the placement and log `[ttl] <name> placed: corner X Y Z, anchor at x y z (version N, terrain done)`;
//    tools/verify_build.py reads the corner from that line (non-overworld builds: --dimension <dim>).
// A column that is void (no terrain at all, e.g. the Spirit Corridor) is left alone: ground = "fixed" builds
// float in a void dimension exactly as the blueprint says.
const TtlBuilds = {
  START_DELAY: 1800, // after Tempest (300), Dwargon (200) and the landmarks (900 + their own queue)
  GAP: 100, // ticks between two builds
  RETRY: 200, // while the landmarks are still placing
  LOAD_POLL: 40,
  LOAD_TIMEOUT: 12000, // 10 min: a fresh 600-chunk area generates in the background while the server ticks
  FILLS_PER_TICK: 150,
  BOOT_ATTEMPTS: 3, // boots in a row that may fail before a build waits for /ttl build place
  KEEPOUT: 24, // blocks kept clear of other placed things
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest', 'lily_pad'],
  WET: ['minecraft:water', 'minecraft:seagrass', 'minecraft:tall_seagrass', 'minecraft:kelp',
    'minecraft:kelp_plant', 'minecraft:bubble_column', 'minecraft:ice', 'minecraft:frosted_ice'],
  WET_COST: 20, // score per wet fraction: 10 % water under the build costs as much as 32 blocks of distance
  queue: [],
  busy: false,
  waits: 0,

  all() {
    return TtlData.builds || []
  },

  find(name) {
    return this.all().find(b => b.name === name) || null
  },

  key(b, k) {
    return `ttl.build.${b.name}.${k}`
  },

  foot(b) {
    return typeof TtlBuildFootprints === 'undefined' ? null : TtlBuildFootprints[b.name] || null
  },

  run(server, b, cmd) {
    return server.runCommandSilent(`execute in ${b.dimension} run ${cmd}`)
  },

  str(server, b, k) {
    return String(server.persistentData.getString(this.key(b, k)) || '')
  },

  ints(text) {
    return text ? text.split(' ').map(Number) : null
  },

  decode(rle, n) {
    var out = new Array(n)
    var i = 0
    for (var k = 0; k < rle.length; k += 2) {
      for (var c = 0; c < rle[k + 1]; c++) out[i++] = rle[k]
    }
    return out
  },

  // Changing where or how the build stands (not version, search or margin) means a new survey. `beside` is part of
  // it only when set, so plans recorded before the field existed still match.
  plan(b) {
    var p = [b.dimension, b.x, b.z, b.ground, b.y === undefined ? '' : b.y, b.anchor.join(',')]
    if (b.beside) p.push(`beside=${b.beside}`)
    return p.join('|')
  },

  // The anchor recorded by the last placement of this build (x, y, z), when it was made for the same plan.
  stored(server, b) {
    if (this.str(server, b, 'plan') !== this.plan(b)) return null
    var at = this.ints(this.str(server, b, 'at'))
    return at && at.length === 3 ? { x: at[0], y: at[1], z: at[2] } : null
  },

  // Blueprint corner and base layer in the world for an anchor point.
  geometry(b, at) {
    return { x0: at.x - b.anchor[0], z0: at.z - b.anchor[2], base: at.y - b.anchor[1] }
  },

  // The area to forceload: every candidate box with its margin, or just the box of a known spot.
  area(b, spot) {
    var s = (spot || b.ground === 'fixed') ? 0 : b.search
    var cx = spot ? spot.x : b.x
    var cz = spot ? spot.z : b.z
    var m = b.margin + 2
    return {
      x0: cx - b.anchor[0] - s - m, z0: cz - b.anchor[2] - s - m,
      x1: cx - b.anchor[0] + b.size[0] - 1 + s + m, z1: cz - b.anchor[2] + b.size[2] - 1 + s + m
    }
  },

  // Heightmaps through Java. ground = first free y above the terrain (trees and plants skipped; on water the water
  // surface), floor = the same under the water (the bed of a river or pond), top = first free y above everything
  // that blocks motion (leaves included); all null in a void column. wet = water or ice on top, lava = lava on top.
  // null when Java is unavailable (the build then waits for a fix).
  heightmaps(server, b) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(b.dimension)
      var skip = this.NOT_GROUND
      var wet = this.WET
      var minY = level.getMinBuildHeight()
      var block = (x, y, z) => String(level.getBlock(x, y, z).id)
      var surface = (x, z) => {
        var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
        return y > minY ? block(x, y - 1, z) : ''
      }
      var ground = (x, z) => {
        var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
        if (y <= minY) return null
        for (var n = 0; n < 40 && y > minY + 1; n++) {
          var id = block(x, y - 1, z)
          if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
          y--
        }
        return y
      }
      var hm = {
        minY: minY,
        top: (x, z) => {
          var y = level.getHeight(Types.MOTION_BLOCKING, x, z)
          return y <= minY ? null : y
        },
        ground: ground,
        floor: (x, z) => {
          var y = ground(x, z)
          if (y === null) return null
          for (var n = 0; n < 64 && y > minY + 1 && wet.indexOf(block(x, y - 1, z)) >= 0; n++) y--
          return y
        },
        wet: (x, z) => wet.indexOf(surface(x, z)) >= 0,
        lava: (x, z) => surface(x, z) === 'minecraft:lava',
        block: block
      }
      hm.ground(b.x, b.z)
      return hm
    } catch (e) {
      console.error(`[ttl] build ${b.name}: heightmaps unavailable (${e})`)
      return null
    }
  },

  // Rectangles (inclusive x0 z0 x1 z1) this build must keep KEEPOUT blocks away from (gap: blocks on top of the
  // build's margin; KEEPOUT unless set). A placed landmark counts with the bounding box landmarks.js recorded for
  // its structure start; without one (start not registered) with the square of its reach round its spot. The
  // landmark a build stands `beside` (TOML) gets gap 0: only the build's own terrain margin stays off its box.
  keepouts(server, b) {
    var out = []
    var self = this
    if (b.dimension === TtlLife.OVERWORLD) {
      var add = (label, get) => {
        try {
          var r = get()
          out.push({ label: label, x0: r.ax0, z0: r.az0, x1: r.ax1, z1: r.az1 })
        } catch (e) {
          console.warn(`[ttl] build ${b.name}: ${label} box unavailable (${e})`)
        }
      }
      add('Tempest', () => TtlTempest.box())
      add('Dwargon', () => TtlDwargon.box())
      try {
        TtlLandmarks.all().forEach(l => {
          var gap = b.beside === l.name ? 0 : undefined
          var box = self.ints(String(server.persistentData.getString(TtlLandmarks.key(l, 'box')) || ''))
          var at = self.ints(String(server.persistentData.getString(TtlLandmarks.key(l, 'at')) || ''))
          if (box && box.length === 6) out.push({ label: `landmark ${l.name}`, x0: box[0], z0: box[2], x1: box[3], z1: box[5], gap: gap })
          else if (at && at.length === 3) out.push({ label: `landmark ${l.name}`, x0: at[0] - l.reach, z0: at[2] - l.reach, x1: at[0] + l.reach, z1: at[2] + l.reach, gap: gap })
        })
      } catch (e) {
        console.warn(`[ttl] build ${b.name}: landmark spots unavailable (${e})`)
      }
    }
    this.all().forEach(o => {
      var box = o.name !== b.name && o.dimension === b.dimension ? self.ints(self.str(server, o, 'box')) : null
      if (box && box.length === 4) out.push({ label: `build ${o.name}`, x0: box[0], z0: box[1], x1: box[2], z1: box[3] })
    })
    return out
  },

  // The flattest dry candidate within `search` of x/z, or null. Samples lie on the build's own columns.
  survey(server, b, f, hm) {
    var sx = f.size[0]
    var sz = f.size[2]
    var ax = b.anchor[0]
    var az = b.anchor[2]
    var low = this.decode(f.fill, sx * sz)
    var stride = 4 * Math.max(1, Math.ceil(Math.max(sx, sz) / 100))
    var steps = n => {
      var out = []
      for (var i = 0; i < n; i += stride) out.push(i)
      if (out[out.length - 1] !== n - 1) out.push(n - 1)
      return out
    }
    var cols = [[ax, az]]
    steps(sz).forEach(gz => steps(sx).forEach(gx => {
      if (low[gz * sx + gx] !== f.none) cols.push([gx, gz])
    }))
    var step = stride * Math.max(1, Math.ceil(b.search / (12 * stride)))
    var kmax = Math.floor(b.search / step)
    var keep = this.KEEPOUT
    var kos = this.keepouts(server, b).map(r => {
      r.m = b.margin + (r.gap === undefined ? keep : r.gap)
      return r
    })
    var cache = {}
    var sample = (x, z) => {
      var k = x + ',' + z
      var s = cache[k]
      if (s === undefined) {
        s = { y: hm.ground(x, z), wet: hm.wet(x, z), lava: hm.lava(x, z) }
        cache[k] = s
      }
      return s
    }
    // Water is a cost, not a veto: on a 120-block box nearly every candidate has a stream or a pond somewhere, and
    // the terrain fit fills wet columns from their bed. Lava and void columns still rule a candidate out.
    var maxWet = b.max_wet === undefined ? 0.1 : b.max_wet
    var leastWet = null
    var best = null
    var seen = { total: 0, keepout: 0, wet: 0, lava: 0, void: 0 }
    for (var kz = -kmax; kz <= kmax; kz++) {
      for (var kx = -kmax; kx <= kmax; kx++) {
        var dx = kx * step
        var dz = kz * step
        if (dx * dx + dz * dz > b.search * b.search) continue
        seen.total++
        var x0 = b.x + dx - ax
        var z0 = b.z + dz - az
        var hit = kos.some(r => !(x0 + sx - 1 + r.m < r.x0 || x0 - r.m > r.x1 || z0 + sz - 1 + r.m < r.z0 || z0 - r.m > r.z1))
        if (hit) {
          seen.keepout++
          continue
        }
        var ys = []
        var bad = null
        var wetN = 0
        for (var i = 0; i < cols.length && bad === null; i++) {
          var s = sample(x0 + cols[i][0], z0 + cols[i][1])
          if (s.lava) bad = 'lava'
          else if (s.y === null) bad = 'void'
          else {
            if (s.wet) wetN++
            ys.push(s.y)
          }
        }
        if (bad !== null) {
          seen[bad]++
          continue
        }
        var wetFrac = wetN / cols.length
        if (leastWet === null || wetFrac < leastWet) leastWet = wetFrac
        if (wetFrac > maxWet) {
          seen.wet++
          continue
        }
        ys.sort((p, q) => p - q)
        var median = ys[Math.floor(ys.length / 2)]
        var mad = ys.reduce((t, y) => t + Math.abs(y - median), 0) / ys.length
        var spread = ys[Math.floor(ys.length * 0.9)] - ys[Math.floor(ys.length * 0.1)]
        var dist = Math.sqrt(dx * dx + dz * dz)
        var score = 2 * mad + 0.5 * spread + dist / 16 + this.WET_COST * wetFrac
        if (best === null || score < best.score) {
          best = { x: b.x + dx, z: b.z + dz, y: median, score: score, mad: mad, spread: spread, dist: dist, wet: wetFrac }
        }
      }
    }
    var pct = v => `${Math.round(v * 100)} %`
    console.info(`[ttl] build ${b.name}: surveyed ${seen.total} spots within ${b.search} of ${b.x} ${b.z} ` +
      `(${seen.keepout} in a keepout, ${seen.wet} over ${pct(maxWet)} water, ${seen.lava} lava, ${seen.void} without ground` +
      (leastWet === null ? '' : `; least water ${pct(leastWet)}`) + ')' +
      (best ? `; best at ${best.x} ${best.z}, ${best.dist.toFixed(0)} blocks from the canon point, ground ${best.y}, ` +
        `mean deviation ${best.mad.toFixed(1)}, spread ${best.spread}, water ${pct(best.wet)}` : ''))
    if (best === null) {
      best = { none: `no spot within ${b.search} blocks of ${b.x} ${b.z} with at most ${pct(maxWet)} water, ` +
        `no lava and clear of other builds` + (leastWet === null ? '' : ` (least water seen ${pct(leastWet)})`) }
    }
    return best
  },

  // Surface materials like the terrain round the anchor: grass over dirt, or sand / red sand over sandstone.
  materials(hm, at) {
    var m = { top: 'minecraft:grass_block', fill: 'minecraft:dirt', deep: 'minecraft:stone' }
    try {
      var y = hm.ground(at.x, at.z)
      var id = y === null ? '' : hm.block(at.x, y - 1, at.z)
      if (id.indexOf('red_sand') >= 0) m = { top: 'minecraft:red_sand', fill: 'minecraft:red_sandstone', deep: 'minecraft:stone' }
      else if (id.indexOf('sand') >= 0) m = { top: 'minecraft:sand', fill: 'minecraft:sandstone', deep: 'minecraft:stone' }
    } catch (e) {
      // keep the default
    }
    return m
  },

  // Earth for one column: deep material down below, filler in the top three, the surface block on top outside the box.
  earthCommands(x, z, y1, y2, onTop, mat, out) {
    var from = Math.max(y1, y2 - 2)
    if (from > y1) out.push(`fill ${x} ${y1} ${z} ${x} ${from - 1} ${z} ${mat.deep}`)
    if (onTop) {
      if (y2 > from) out.push(`fill ${x} ${from} ${z} ${x} ${y2 - 1} ${z} ${mat.fill}`)
      out.push(`fill ${x} ${y2} ${z} ${x} ${y2} ${z} ${mat.top}`)
    } else {
      out.push(`fill ${x} ${from} ${z} ${x} ${y2} ${z} ${mat.fill}`)
    }
  },

  // Every terrain command, worked out from the heightmaps as they were before the structure went in.
  terrainCommands(b, f, hm, geo, mat) {
    var sx = f.size[0]
    var sz = f.size[2]
    var m = b.margin
    var g = b.anchor[1] - 1 // the ground layer: the block under the anchor
    var low = this.decode(f.fill, sx * sz)
    var top = this.decode(f.top, sx * sz)
    var clears = []
    var fills = []
    for (var gz = -m; gz < sz + m; gz++) {
      for (var gx = -m; gx < sx + m; gx++) {
        var x = geo.x0 + gx
        var z = geo.z0 + gz
        var ground = hm.ground(x, z)
        if (ground === null) continue
        // Earth goes in from the bed of a stream or pond, not from its surface: no dirt bridges over water.
        var floor = hm.floor(x, z)
        var inBox = gx >= 0 && gz >= 0 && gx < sx && gz < sz
        if (inBox) {
          var i = gz * sx + gx
          if (b.clear_above) {
            var c1 = geo.base + (top[i] === f.none ? g + 1 : top[i])
            var c2 = hm.top(x, z) - 1
            if (c2 >= c1) clears.push(`fill ${x} ${c1} ${z} ${x} ${c2} ${z} minecraft:air`)
          }
          if (low[i] !== f.none && geo.base + low[i] - 1 >= floor) this.earthCommands(x, z, floor, geo.base + low[i] - 1, false, mat, fills)
        } else {
          var d = Math.ceil(Math.sqrt(Math.pow(Math.max(0, -gx, gx - sx + 1), 2) + Math.pow(Math.max(0, -gz, gz - sz + 1), 2)))
          if (b.clear_above && ground - 1 >= geo.base + g + 1 + d) {
            clears.push(`fill ${x} ${geo.base + g + 1 + d} ${z} ${x} ${hm.top(x, z) - 1} ${z} minecraft:air`)
          }
          if (geo.base + g - d >= floor) this.earthCommands(x, z, floor, geo.base + g - d, true, mat, fills)
        }
      }
    }
    return clears.concat(fills)
  },

  runBatched(server, b, cmds, done) {
    var self = this
    var i = 0
    var step = () => {
      try {
        var end = Math.min(cmds.length, i + self.FILLS_PER_TICK)
        for (; i < end; i++) self.run(server, b, cmds[i])
      } catch (e) {
        console.error(`[ttl] build ${b.name}: terrain step failed at ${i}: ${e}`)
        done(false)
        return
      }
      if (i < cmds.length) server.scheduleInTicks(1, step)
      else done(true)
    }
    step()
  },

  failed(server, b, why) {
    var data = server.persistentData
    data.putInt(this.key(b, 'fails'), data.getInt(this.key(b, 'fails')) + 1)
    console.error(`[ttl] build ${b.name}: not placed (${why}); /ttl build place ${b.name} tries again`)
  },

  record(server, b, f, at, geo) {
    var data = server.persistentData
    var m = b.margin
    data.putInt(this.key(b, 'version'), b.version)
    data.putString(this.key(b, 'at'), `${at.x} ${at.y} ${at.z}`)
    data.putString(this.key(b, 'corner'), `${geo.x0} ${geo.base} ${geo.z0}`)
    data.putString(this.key(b, 'box'), `${geo.x0 - m} ${geo.z0 - m} ${geo.x0 + f.size[0] - 1 + m} ${geo.z0 + f.size[2] - 1 + m}`)
    data.putString(this.key(b, 'plan'), this.plan(b))
    data.putInt(this.key(b, 'fails'), 0)
  },

  place(server, b, spot, done) {
    var f = this.foot(b)
    if (!f) {
      this.failed(server, b, 'no footprint in generated/builds.js; run python tools/gen_data.py')
      done(false)
      return
    }
    var hm = this.heightmaps(server, b)
    if (!hm) {
      this.failed(server, b, 'heightmaps unavailable')
      done(false)
      return
    }
    var at = spot
    var how = 'same spot as before'
    if (!at && b.ground === 'fixed') {
      at = { x: b.x, y: b.y, z: b.z }
      how = 'fixed ground'
    } else if (!at) {
      var best = this.survey(server, b, f, hm)
      if (best.none) {
        this.failed(server, b, best.none)
        done(false)
        return
      }
      at = { x: best.x, y: best.y, z: best.z }
      how = `surveyed, ${best.dist.toFixed(0)} blocks from the canon point, ${Math.round(best.wet * 100)} % water`
    }
    var geo = this.geometry(b, at)
    var cmds = this.terrainCommands(b, f, hm, geo, this.materials(hm, at))
    var self = this
    // All slabs, one every 2 ticks, then next(ok).
    var placeSlabs = next => {
      var part = 0
      var step = () => {
        try {
          if (part < f.slabs.length) {
            var r = self.run(server, b, `place template ${f.slabs[part]} ${geo.x0} ${geo.base} ${geo.z0 + f.parts[part]}`)
            if (r === 0) console.warn(`[ttl] build ${b.name}: place template ${f.slabs[part]} reported failure`)
            part++
            server.scheduleInTicks(2, step)
            return
          }
        } catch (e) {
          self.failed(server, b, `placement failed at slab ${part}: ${e}`)
          next(false)
          return
        }
        next(true)
      }
      step()
    }
    var finish = ok => {
      try {
        if (ok) self.record(server, b, f, at, geo)
        else self.failed(server, b, 'terrain fit failed')
        console.info(`[ttl] ${b.name} placed: corner ${geo.x0} ${geo.base} ${geo.z0}, anchor at ${at.x} ${at.y} ${at.z} ` +
          `(version ${b.version}, ${how}, terrain ${ok ? 'done' : 'FAILED'})`)
      } catch (e) {
        console.error(`[ttl] build ${b.name}: recording the placement failed: ${e}`)
      }
      done(ok)
    }
    // Two passes. In the first, blocks that need support (beds, doors, ladders, lanterns, crops that need light or sky)
    // are judged against the old terrain and the trees not cleared yet, and some pop; the second pass, after the
    // terrain fit, sets them again on finished ground. It only rewrites the positions the structure defines, which
    // the terrain fit never touches (it works below a column's lowest and above its highest block).
    // `dry` builds (a gallery cut below the water table): `place template` keeps the water of the old terrain, so every
    // stair, slab or wall set on a flooded cell comes out waterlogged and keeps feeding a puddle (Amrita, 11 blocks). The
    // box is drained first. A re-placement over an old copy does not help: its waterlogged blocks still hold water.
    var drain = []
    if (b.dry) {
      var rows = Math.max(1, Math.floor(30000 / (f.size[0] * f.size[1])))
      for (var dz = 0; dz < f.size[2]; dz += rows) {
        drain.push(`fill ${geo.x0} ${geo.base} ${geo.z0 + dz} ${geo.x0 + f.size[0] - 1} ${geo.base + f.size[1] - 1} ` +
          `${geo.z0 + Math.min(f.size[2], dz + rows) - 1} minecraft:air replace minecraft:water`)
      }
    }
    self.runBatched(server, b, drain, drained => {
      if (!drained) {
        finish(false)
        return
      }
      placeSlabs(placed => {
        if (!placed) {
          done(false)
          return
        }
        console.info(`[ttl] build ${b.name}: ${f.slabs.length} slab(s) placed, ${cmds.length} terrain commands (${self.FILLS_PER_TICK}/tick)`)
        self.runBatched(server, b, cmds, ok => {
          if (!ok) {
            finish(false)
            return
          }
          placeSlabs(again => {
            if (again) finish(true)
            else done(false)
          })
        })
      })
    })
  },

  // Tempest and Dwargon (they record their version when done; waited for at most 15 retries, 10 s each) and the
  // landmarks (queue and busy flag of landmarks.js) go first.
  othersBusy(server) {
    try {
      if (typeof TtlLandmarks !== 'undefined' && (TtlLandmarks.busy || TtlLandmarks.queue.length > 0)) return true
      var data = server.persistentData
      var waiting = (typeof TTL_TEMPEST_VERSION !== 'undefined' && data.getInt('ttl.tempest.version') !== TTL_TEMPEST_VERSION) ||
        (typeof TTL_DWARGON_VERSION !== 'undefined' && data.getInt('ttl.dwargon.version') !== TTL_DWARGON_VERSION)
      if (waiting && this.waits < 15) {
        this.waits++
        return true
      }
      return false
    } catch (e) {
      return false
    }
  },

  // One build at a time: hold the chunks, wait until they are FULL, place, release, gap, next. A build whose chunks
  // are not all loaded after LOAD_TIMEOUT is not placed (counted as a failed boot attempt): reading heightmaps or
  // filling in a missing chunk would load it synchronously, the server stall the chunk tickets avoid.
  pump(server) {
    if (this.busy || this.queue.length === 0) return
    var self = this
    if (this.othersBusy(server)) {
      server.scheduleInTicks(this.RETRY, () => self.pump(server))
      return
    }
    var b = this.queue.shift()
    var spot = this.stored(server, b)
    var a = this.area(b, spot)
    this.busy = true
    var hold = TtlChunks.hold(server, b.dimension, a, `build ${b.name}`)
    var finish = () => {
      TtlChunks.release(server, hold)
      self.busy = false
      server.scheduleInTicks(self.GAP, () => self.pump(server))
    }
    TtlChunks.whenReady(server, hold, this.LOAD_POLL, this.LOAD_TIMEOUT, (ready, missing) => {
      if (!ready && missing > 0) {
        self.failed(server, b, `${missing} chunk(s) of its area still not loaded after ${self.LOAD_TIMEOUT} ticks`)
        finish()
        return
      }
      try {
        self.place(server, b, spot, finish)
      } catch (e) {
        self.failed(server, b, `${e}`)
        finish()
      }
    })
  },

  enqueue(server, b) {
    if (this.queue.some(q => q.name === b.name)) return
    this.queue.push(b)
    this.pump(server)
  },

  pending(server) {
    var data = server.persistentData
    var self = this
    return this.all().filter(b => data.getInt(self.key(b, 'version')) !== b.version &&
      data.getInt(self.key(b, 'fails')) < self.BOOT_ATTEMPTS)
  },

  schedule(server) {
    var self = this
    server.scheduleInTicks(this.START_DELAY, () => self.pending(server).forEach(b => self.enqueue(server, b)))
  },

  // World reset (world_reset.js passes the reset dimensions): every build in them goes again on the new terrain.
  reset(server, ids) {
    var data = server.persistentData
    var self = this
    var hit = false
    this.waits = 0
    this.all().forEach(b => {
      if (ids && ids.indexOf(b.dimension) < 0) return
      hit = true
      ;['version', 'at', 'corner', 'box', 'plan', 'fails'].forEach(k => data.remove(self.key(b, k)))
    })
    if (hit) this.schedule(server)
  },

  describe(server, b) {
    var data = server.persistentData
    var v = data.getInt(this.key(b, 'version'))
    var at = this.str(server, b, 'at')
    var state = v === b.version ? `placed at ${at}` : v ? `placed v${v} at ${at}, v${b.version} pending` :
      data.getInt(this.key(b, 'fails')) ? `FAILED ${data.getInt(this.key(b, 'fails'))}x` : 'pending'
    if (this.queue.some(q => q.name === b.name)) state += ' (queued)'
    return `${b.name}: ${b.title}, near ${b.x} ${b.z} in ${b.dimension}, ${state}`
  },

  // Players who walk into a placed build for the first time (per version) see its title.
  greet(server) {
    var self = this
    var players = server.getPlayerList().getPlayers()
    if (players.size() === 0) return
    var placed = []
    this.all().forEach(b => {
      var f = self.foot(b)
      var c = self.ints(self.str(server, b, 'corner'))
      if (f && c && c.length === 3 && server.persistentData.getInt(self.key(b, 'version')) === b.version) {
        placed.push({ b: b, x0: c[0], y0: c[1], z0: c[2], x1: c[0] + f.size[0] - 1, y1: c[1] + f.size[1] + 4, z1: c[2] + f.size[2] - 1 })
      }
    })
    if (placed.length === 0) return
    players.forEach(p => {
      var dim = TtlLife.dimensionOf(p)
      var x = p.getX()
      var y = p.getY()
      var z = p.getZ()
      placed.forEach(r => {
        if (r.b.dimension !== dim || x < r.x0 || x > r.x1 + 1 || z < r.z0 || z > r.z1 + 1 || y < r.y0 - 4 || y > r.y1) return
        var mark = `ttl.build.seen.${r.b.name}`
        if (p.persistentData.getInt(mark) === r.b.version) return
        p.persistentData.putInt(mark, r.b.version)
        server.runCommandSilent(`title ${p.username} times 10 70 20`)
        server.runCommandSilent(`title ${p.username} subtitle {"text":"Canon location","color":"gray"}`)
        server.runCommandSilent(`title ${p.username} title {"text":${JSON.stringify(r.b.title)},"color":"gold"}`)
      })
    })
  },

  watch(server) {
    var self = this
    var step = () => {
      try {
        self.greet(server)
      } catch (e) {
        console.error(`[ttl] builds: arrival title check failed: ${e}`)
      }
      server.scheduleInTicks(40, step)
    }
    server.scheduleInTicks(200, step)
  }
}

ServerEvents.loaded(event => {
  TtlBuilds.schedule(event.server)
  if (TtlBuilds.all().length > 0) TtlBuilds.watch(event.server)
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var fail = (ctx, line) => {
    ctx.source.sendSystemMessage(Text.red(`ttl: ${line}`))
    return 0
  }
  var named = (ctx, then) => {
    var name = String(Arguments.STRING.getResult(ctx, 'name')).toLowerCase()
    var server = ctx.source.getServer()
    if (name === 'all' && then.all) return then.all(server)
    var b = TtlBuilds.find(name)
    if (!b) return fail(ctx, `no build ${name}; see /ttl build list`)
    return then.one(server, b)
  }
  // Without force, only builds whose version is not placed yet; with force every one again at its recorded spot.
  var request = (ctx, server, b, force) => {
    var data = server.persistentData
    if (!force && data.getInt(TtlBuilds.key(b, 'version')) === b.version) {
      say(ctx, `${b.name} is already placed (version ${b.version}); add force to place it again`)
      return 0
    }
    data.putInt(TtlBuilds.key(b, 'fails'), 0)
    TtlBuilds.enqueue(server, b)
    say(ctx, `Placing ${b.name}${TtlBuilds.stored(server, b) ? ' at its recorded spot' : ` near ${b.x} ${b.z}`}; watch the log for "[ttl] ${b.name} placed"`)
    return 1
  }
  var placeCmd = force => ctx => named(ctx, {
    one: (server, b) => request(ctx, server, b, force),
    all: server => {
      var n = 0
      TtlBuilds.all().forEach(b => {
        n += request(ctx, server, b, force)
      })
      say(ctx, `${n} of ${TtlBuilds.all().length} builds queued, one by one`)
      return n
    }
  })
  event.register(Commands.literal('ttl')
    .then(Commands.literal('build')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('list').executes(ctx => {
        var server = ctx.source.getServer()
        if (TtlBuilds.all().length === 0) say(ctx, 'No canon builds (design/builds/*.toml)')
        TtlBuilds.all().forEach(b => say(ctx, TtlBuilds.describe(server, b)))
        return 1
      }))
      .then(Commands.literal('where')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, b) => {
            var at = TtlBuilds.str(server, b, 'at')
            var box = TtlBuilds.str(server, b, 'box')
            say(ctx, `${b.title}: ${at ? `placed at ${at}` : `not placed, planned near ${b.x} ~ ${b.z}`}`)
            if (box) say(ctx, `  worked area ${box} (x0 z0 x1 z1, margin included)`)
            say(ctx, `  /execute in ${b.dimension} run tp @s ${at ? at.split(' ').map((v, i) => i === 1 ? Number(v) + 2 : v).join(' ') : `${b.x} 200 ${b.z}`}`)
            return 1
          }
        }))))
      .then(Commands.literal('place')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(placeCmd(false))
          .then(Commands.literal('force').executes(placeCmd(true)))))
      .then(Commands.literal('expect')
        .then(Commands.argument('name', Arguments.STRING.create(event))
          .then(Commands.literal('placed').executes(ctx => named(ctx, {
            one: (server, b) => {
              var v = server.persistentData.getInt(TtlBuilds.key(b, 'version'))
              if (v !== b.version) return fail(ctx, `expected ${b.name} to be placed at version ${b.version}, it is ${v ? `at version ${v}` : 'not placed'}`)
              say(ctx, `builds: ${b.name} is placed at ${TtlBuilds.str(server, b, 'at')} as expected`)
              return 1
            }
          })))))))
})
