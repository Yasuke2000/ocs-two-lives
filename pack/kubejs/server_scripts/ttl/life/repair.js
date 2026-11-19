// Terrain repair round a placed build: the pass after the terrain fit and before the second slab pass, shared by
// life/builds.js (every canon build), life/tempest.js and life/dwargon.js. The fit works from heightmaps read before
// the build went in, so it cannot see what lies under an overhang, a closed cave roof, or the old terrain in the
// columns a blueprint leaves undefined; after the 19/11 reset every one of those was repaired by hand
// (design/decisions.md 19/11). This pass reads the real blocks after the fit and fixes them, deterministically:
//
// 1. Foundation, every box column the build defines (lowest defined block = `bottom`, explicit air included): every
//    air, water, lava, fire or plant cell in the `depth` blocks below it becomes ground (dirt in the 3 cells right
//    under the build like the fit, stone deeper, deepslate below y 0). A gap that runs on below the depth is closed
//    down to the depth when there is ground somewhere below it; a column with nothing solid under it (a void
//    dimension, a floating island) is left alone. Nothing is ever placed at or above `bottom`.
// 2. Undefined box columns (the blueprint holds no block there): the ground layer is continued at the ground height
//    `ground` (the block under the anchor): the same fill below it, and the top block (the nearest defined column's
//    grass / path / sand at that height, else the site's top block) where that cell is a gap or exposed bare rock.
// 3. Ring of `margin` columns round the box (square): the surface (first solid block from the top, trees, plants and
//    snow skipped) is raised to T = max(slope, min(ground, closing)): `slope` is the fit's own 1:1 skirt, `closing`
//    a grey-scale morphological closing of the surface heights (box columns count as the ground height; square
//    window of 2 x CLOSE + 1), used only where it lies PIT or more above the surface: pits, crevices, slits and
//    ravine edges up to ~8 wide fill to their rim, while gentle dips, hills, wide valleys and lakes keep their shape,
//    and nothing rises above the build's ground. A gap within ROOF blocks under the surface (a cave mouth, an overhang,
//    the lip of a ravine running under the edge) is filled to its floor. Water in the ring that touches the box
//    (4-connected through ring water to a box column) is filled up to its surface, so a bank holds the water beyond;
//    other water (a pond, the lake beyond the ring) is kept, and `keepWater` keeps every water cell (Raja's lake).
//    Lava is filled up to its surface below the ground height, lava above it and fire become air.
// The planner reads blocks only in loaded chunks (it never forceloads or loads a chunk), and both planning and the
// commands run under a time budget per tick (BUDGET_MS, CMDS_PER_TICK). Fills are merged into boxes (<= 32768 cells).
// Log: `[ttl] build <name>: repaired N foundation, M skirt, K lava (...)` (cells; K counts lava and fire).
// Offline tests: tests/build_repair.js (synthetic worlds, run by tests/test_build_repair.py).
const TtlRepair = {
  BUDGET_MS: 15, // planning and commands, per tick
  CMDS_PER_TICK: 200,
  DEPTH: 48,
  ROOF: 3,
  CLOSE: 4, // closing window 2 x CLOSE + 1: gaps up to ~8 wide fill to their rim
  PIT: 3, // ... when they lie at least this deep under it
  FILL: 3, // dirt (or sandstone) cells under a surface or under the build, stone below
  EXACT: 8, // cells under the build read one by one before the scan reads every other cell
  WALK: 96, // ring: at most this many cells from the heightmap down to the ground
  VOLUME: 32768, // fill limit per command
  AIR: ['minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'],
  WATER: ['minecraft:water', 'minecraft:bubble_column', 'minecraft:seagrass', 'minecraft:tall_seagrass',
    'minecraft:kelp', 'minecraft:kelp_plant'],
  FIRE: ['minecraft:fire', 'minecraft:soul_fire'],
  // Not ground: trees, plants, decoration and loose snow (substrings of the id).
  SOFT: ['_leaves', '_log', '_wood', '_stem', '_hyphae', 'mushroom', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'sapling', 'azalea', 'dripleaf', 'roots', 'cocoa', 'bee_nest', 'lily_pad', 'lichen', 'spore_blossom',
    'carpet', 'pink_petals', 'sugar_cane', 'cactus', 'cobweb', 'sculk_vein', 'pointed_dripstone', 'flower', 'dandelion',
    'poppy', 'orchid', 'allium', 'azure_bluet', '_tulip', 'oxeye_daisy', 'lily_of_the_valley', 'wither_rose', 'lilac',
    'peony', 'pitcher', 'sweet_berry', 'powder_snow'],
  // Natural top blocks an undefined box column may copy from its defined neighbour, and keeps when it has one.
  TOPS: ['minecraft:grass_block', 'minecraft:dirt_path', 'minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:podzol',
    'minecraft:mycelium', 'minecraft:rooted_dirt', 'minecraft:moss_block', 'minecraft:mud', 'minecraft:sand',
    'minecraft:red_sand', 'minecraft:gravel', 'minecraft:snow_block', 'minecraft:clay'],
  kinds: {},

  // air | water | lava | fire | soft | solid, per block id.
  cls(id) {
    var c = this.kinds[id]
    if (c !== undefined) return c
    if (this.AIR.indexOf(id) >= 0) c = 'air'
    else if (this.WATER.indexOf(id) >= 0) c = 'water'
    else if (id === 'minecraft:lava') c = 'lava'
    else if (this.FIRE.indexOf(id) >= 0) c = 'fire'
    else if (id === 'minecraft:snow' || this.SOFT.some(k => id.indexOf(k) >= 0)) c = 'soft'
    else c = 'solid'
    this.kinds[id] = c
    return c
  },

  // The pure planner. spec: {label, x0, z0 (world x/z of grid cell 0,0), w, l, ground (y of the ground layer),
  // depth, keepWater, mat {top, fill, deep}, col(gx, gz) -> null | {t: 'build', bottom: y} | {t: 'ground'} |
  // {t: 'ring', slope: y or null}}. world: {minY, id(x, y, z) -> block id, top(x, z) -> first free y above the
  // motion-blocking blocks without leaves, loaded(x, z) -> bool}. step(stop) works until stop() says the tick's
  // budget is spent (false) or the plan is done (true, then .result = {cmds, foundation, skirt, lava, deep, unloaded}).
  planner(spec, world) {
    var self = this
    var w = spec.w
    var n = spec.w * spec.l
    var G = spec.ground
    var depth = spec.depth
    var keep = !!spec.keepWater
    var mat = spec.mat
    var minY = world.minY
    var cols = new Array(n)
    var info = new Array(n)
    var touch = new Array(n)
    var ops = []
    var res = { cmds: [], foundation: 0, skirt: 0, lava: 0, deep: 0, unloaded: 0 }
    var raw = (x, y, z) => self.cls(String(world.id(x, y, z)))
    // A cell that must become ground: anything but solid, and water unless it is kept.
    var gap = (x, y, z) => {
      var c = raw(x, y, z)
      return c !== 'solid' && !(keep && c === 'water') ? c : null
    }
    // Is there ground anywhere below y (2-block steps down to the bottom of the world)?
    var grounded = (x, z, y) => {
      for (var yy = y; yy >= minY; yy -= 2) {
        if (raw(x, yy, z) === 'solid') return true
      }
      return false
    }
    // Every gap run from yHi down to yLo: [top, bottom, lava cells]; a run still open at yLo is kept only over ground.
    // The EXACT cells under yHi are read one by one; deeper, solid ground is read every other cell (a gap found that
    // way is traced from the cell above it), so a closed pocket 1 cell high deep down may stay.
    var runs = (x, z, yHi, yLo) => {
      var out = []
      var cur = null
      var y = yHi
      var exact = false
      while (y >= yLo) {
        var c = gap(x, y, z)
        if (c === null) {
          if (cur) out.push(cur)
          cur = null
          if (!exact && yHi - y >= self.EXACT && y - 2 >= yLo) {
            if (gap(x, y - 2, z) === null) {
              y -= 2
              continue
            }
            exact = true
          }
          y--
          continue
        }
        exact = false
        if (!cur) cur = [y, y, 0]
        cur[1] = y
        if (c === 'lava' || c === 'fire') cur[2]++
        y--
      }
      if (cur && grounded(x, z, yLo - 1)) {
        out.push(cur)
        res.deep++
      }
      return out
    }
    // The first gap run from yHi down, ended by the first solid cell (at most down to yLo); null over the void.
    var firstRun = (x, z, yHi, yLo) => {
      var cur = null
      for (var y = yHi; y >= yLo; y--) {
        var c = gap(x, y, z)
        if (c === null) return cur
        if (!cur) cur = [y, y, 0]
        cur[1] = y
        if (c === 'lava' || c === 'fire') cur[2]++
      }
      return cur && grounded(x, z, yLo - 1) ? cur : null
    }
    var scan = i => {
      var gx = i % w
      var gz = Math.floor(i / w)
      var c = spec.col(gx, gz)
      cols[i] = c
      if (!c) return
      var x = spec.x0 + gx
      var z = spec.z0 + gz
      if (!world.loaded(x, z)) {
        cols[i] = null
        res.unloaded++
        return
      }
      if (c.t === 'build') {
        info[i] = { runs: runs(x, z, c.bottom - 1, c.bottom - depth) }
      } else if (c.t === 'ground') {
        var r = runs(x, z, G, G + 1 - depth)
        var bare = false
        if (!(r.length > 0 && r[0][0] === G)) {
          // The ground cell is solid: replace bare rock or a foreign block when the sky sees it.
          var here = String(world.id(x, G, z))
          bare = self.TOPS.indexOf(here) < 0 && gap(x, G + 1, z) !== null
        }
        info[i] = { runs: r, bare: bare }
      } else {
        var top = world.top(x, z)
        if (top <= minY) {
          info[i] = { S: null }
          return
        }
        var s = { S: null, wtop: null, ltop: null, lavas: [], fires: [], under: null }
        var y = top
        var k = 'air'
        for (var step = 0; step < self.WALK && y > minY; step++, y--) {
          k = raw(x, y, z)
          if (k === 'solid') break
          if (k === 'water' && s.wtop === null) s.wtop = y
          else if (k === 'lava') {
            if (s.ltop === null) s.ltop = y
            s.lavas.push(y)
          } else if (k === 'fire') s.fires.push(y)
        }
        if (k === 'solid') {
          s.S = y
          for (var u = y - 1; u >= y - self.ROOF; u--) {
            if (gap(x, u, z) !== null) {
              s.under = firstRun(x, z, u, y - depth)
              break
            }
          }
        }
        info[i] = s
      }
    }
    var isBox = i => !!cols[i] && cols[i].t !== 'ring'
    var isRing = i => !!cols[i] && cols[i].t === 'ring' && !!info[i] && info[i].S !== null
    // Ring water that touches the box through ring water (4-neighbours), unless every water cell is kept.
    var touching = () => {
      if (keep) return
      var queue = []
      var wet = i => isRing(i) && info[i].wtop !== null
      for (var i = 0; i < n; i++) {
        if (!wet(i)) continue
        var gx = i % w
        if ((gx > 0 && isBox(i - 1)) || (gx < w - 1 && isBox(i + 1)) || (i >= w && isBox(i - w)) || (i + w < n && isBox(i + w))) {
          touch[i] = true
          queue.push(i)
        }
      }
      while (queue.length > 0) {
        var j = queue.pop()
        var jx = j % w
        var next = []
        if (jx > 0) next.push(j - 1)
        if (jx < w - 1) next.push(j + 1)
        if (j >= w) next.push(j - w)
        if (j + w < n) next.push(j + w)
        next.forEach(k => {
          if (!touch[k] && wet(k)) {
            touch[k] = true
            queue.push(k)
          }
        })
      }
    }
    // Closing of the surface heights (box columns count as the ground height): max then min over the window,
    // separable, one row or column per call. NEG / POS mark cells without data.
    var NEG = -1e9
    var POS = 1e9
    var surf = new Array(n)
    var tmp = new Array(n)
    var close = new Array(n)
    var r = this.CLOSE
    var l = spec.l
    var prepare = () => {
      for (var i = 0; i < n; i++) {
        if (isBox(i)) surf[i] = G
        else if (isRing(i)) surf[i] = Math.max(info[i].S, info[i].wtop === null ? NEG : info[i].wtop, info[i].ltop === null ? NEG : info[i].ltop)
        else surf[i] = NEG
      }
    }
    // pass 0: rows max surf -> tmp; 1: columns max tmp -> close; 2: rows min close -> tmp; 3: columns min tmp -> close
    var pass = (p, line) => {
      var rows = p === 0 || p === 2
      var src = p === 0 ? surf : p === 1 ? tmp : p === 2 ? close : tmp
      var dst = p === 0 || p === 2 ? tmp : close
      var len = rows ? w : l
      var at = k => rows ? line * w + k : k * w + line
      for (var k = 0; k < len; k++) {
        var best = p < 2 ? NEG : POS
        for (var d = Math.max(0, k - r); d <= Math.min(len - 1, k + r); d++) {
          var v = src[at(d)]
          if (p < 2) {
            if (v > best) best = v
          } else if (v > NEG && v < best) best = v
        }
        dst[at(k)] = best
      }
    }
    var op = (x, z, y1, y2, block, filter) => {
      if (y2 >= y1) ops.push([x, z, y1, y2, block, filter || ''])
    }
    var deep = y => y < 0 && mat.deep === 'minecraft:stone' ? 'minecraft:deepslate' : mat.deep
    // Ground for cells y1..y2 of a column whose surface is `ref`: the top block at ref (withTop), filler in the FILL
    // cells below ref, deep material (deepslate under y 0) further down.
    var layers = (x, z, y1, y2, ref, withTop, topBlock) => {
      if (withTop && ref >= y1 && ref <= y2) op(x, z, ref, ref, topBlock)
      var f1 = Math.max(y1, ref - self.FILL)
      var f2 = Math.min(y2, ref - 1)
      op(x, z, f1, f2, mat.fill)
      var d2 = Math.min(y2, ref - self.FILL - 1)
      if (d2 >= y1) {
        if (deep(y1) !== deep(d2)) {
          op(x, z, y1, Math.min(d2, -1), deep(-1))
          op(x, z, Math.max(y1, 0), d2, deep(0))
        } else op(x, z, y1, d2, deep(y1))
      }
    }
    // The top block for an undefined box column: its nearest defined neighbour's natural top at the ground height
    // (within 2 columns, nearest first, so a path ending at a ditch runs on), else the site's top block.
    var near = []
    for (var oz = -2; oz <= 2; oz++) {
      for (var ox = -2; ox <= 2; ox++) {
        if (ox !== 0 || oz !== 0) near.push([ox, oz, ox * ox + oz * oz])
      }
    }
    near.sort((a, b) => a[2] - b[2])
    var topFor = (gx, gz) => {
      for (var j = 0; j < near.length; j++) {
        var nx = gx + near[j][0]
        var nz = gz + near[j][1]
        if (nx < 0 || nz < 0 || nx >= w || nz >= l) continue
        var c = cols[nz * w + nx]
        if (!c || c.t !== 'build') continue
        var id = String(world.id(spec.x0 + nx, G, spec.z0 + nz))
        if (self.TOPS.indexOf(id) >= 0) return id
      }
      return mat.top
    }
    var emit = i => {
      var c = cols[i]
      if (!c || !info[i]) return
      var gx = i % w
      var gz = Math.floor(i / w)
      var x = spec.x0 + gx
      var z = spec.z0 + gz
      var s = info[i]
      if (c.t === 'build') {
        s.runs.forEach(run => {
          layers(x, z, run[1], run[0], c.bottom, false, null)
          res.foundation += run[0] - run[1] + 1 - run[2]
          res.lava += run[2]
        })
        return
      }
      if (c.t === 'ground') {
        var tb = null
        s.runs.forEach(run => {
          if (run[0] === G && tb === null) tb = topFor(gx, gz)
          layers(x, z, run[1], run[0], G, true, tb)
          res.foundation += run[0] - run[1] + 1 - run[2]
          res.lava += run[2]
        })
        if (s.bare) {
          op(x, z, G, G, topFor(gx, gz))
          res.foundation++
        }
        return
      }
      if (s.S === null) return
      var T = c.slope === null || c.slope === undefined ? null : c.slope
      // A pit: the closing lies PIT or more above the surface (gentle dips between hills stay as they are).
      if (close[i] > NEG && close[i] < POS && close[i] - surf[i] >= self.PIT) {
        var cl = Math.min(G, close[i])
        T = T === null ? cl : Math.max(T, cl)
      }
      var kept = s.wtop !== null && (keep || !touch[i])
      var fillTop = s.S
      if (!kept && T !== null) {
        var Tt = T
        if (s.wtop !== null) Tt = Math.max(Tt, Math.min(G, s.wtop))
        if (s.ltop !== null) Tt = Math.max(Tt, Math.min(G, s.ltop))
        if (Tt > s.S) {
          layers(x, z, s.S + 1, Tt, Tt, true, mat.top)
          var lavaIn = s.lavas.filter(y => y <= Tt).length + s.fires.filter(y => y <= Tt).length
          res.skirt += Tt - s.S - lavaIn
          res.lava += lavaIn
          fillTop = Tt
        }
      }
      var lavaUp = s.lavas.filter(y => y > fillTop)
      if (lavaUp.length > 0) {
        op(x, z, Math.min.apply(null, lavaUp), Math.max.apply(null, lavaUp), 'minecraft:air', 'minecraft:lava')
        res.lava += lavaUp.length
      }
      var fireUp = s.fires.filter(y => y > fillTop)
      if (fireUp.length > 0) {
        op(x, z, Math.min.apply(null, fireUp), Math.max.apply(null, fireUp), 'minecraft:air', '#minecraft:fire')
        res.lava += fireUp.length
      }
      if (s.under) {
        layers(x, z, s.under[1], s.under[0], fillTop, false, null)
        res.skirt += s.under[0] - s.under[1] + 1 - s.under[2]
        res.lava += s.under[2]
      }
    }
    // Same fills next to each other become one box: strips along x, then equal strips on consecutive z.
    var merge = () => {
      var key = o => `${o[2]}|${o[3]}|${o[4]}|${o[5]}`
      ops.sort((a, b) => {
        var ka = key(a)
        var kb = key(b)
        return ka < kb ? -1 : ka > kb ? 1 : a[1] - b[1] || a[0] - b[0]
      })
      var strips = []
      ops.forEach(o => {
        var last = strips[strips.length - 1]
        if (last && last.k === key(o) && last.z1 === o[1] && last.x2 === o[0] - 1) last.x2 = o[0]
        else strips.push({ k: key(o), x1: o[0], x2: o[0], z1: o[1], z2: o[1], y1: o[2], y2: o[3], b: o[4], f: o[5] })
      })
      strips.sort((a, b) => a.k < b.k ? -1 : a.k > b.k ? 1 : a.x1 - b.x1 || a.x2 - b.x2 || a.z1 - b.z1)
      var boxes = []
      strips.forEach(s => {
        var last = boxes[boxes.length - 1]
        if (last && last.k === s.k && last.x1 === s.x1 && last.x2 === s.x2 && last.z2 === s.z1 - 1) last.z2 = s.z1
        else boxes.push(s)
      })
      boxes.forEach(bx => {
        var dx = bx.x2 - bx.x1 + 1
        var dy = bx.y2 - bx.y1 + 1
        var rows = Math.max(1, Math.floor(self.VOLUME / (dx * dy)))
        var span = dx * dy > self.VOLUME ? Math.max(1, Math.floor(self.VOLUME / dy)) : dx
        for (var z1 = bx.z1; z1 <= bx.z2; z1 += rows) {
          for (var x1 = bx.x1; x1 <= bx.x2; x1 += span) {
            res.cmds.push(`fill ${x1} ${bx.y1} ${z1} ${Math.min(bx.x2, x1 + span - 1)} ${bx.y2} ${Math.min(bx.z2, z1 + rows - 1)} ` +
              bx.b + (bx.f ? ` replace ${bx.f}` : ''))
          }
        }
      })
    }
    // Phases, each resumable: scan columns, touching water + closing input, 4 closing passes, emit, merge.
    var phase = 0
    var at = 0
    var p = {
      result: null,
      step(stop) {
        while (phase < 8) {
          if (phase === 0) {
            while (at < n) {
              scan(at++)
              if ((at & 3) === 0 && stop()) return false
            }
            phase = 1
            at = 0
          } else if (phase === 1) {
            touching()
            prepare()
            phase = 2
            at = 0
          } else if (phase <= 5) {
            var lines = phase === 2 || phase === 4 ? l : w
            while (at < lines) {
              pass(phase - 2, at++)
              if (stop()) return false
            }
            phase++
            at = 0
          } else if (phase === 6) {
            while (at < n) {
              emit(at++)
              if ((at & 15) === 0 && stop()) return false
            }
            phase = 7
          } else {
            merge()
            phase = 8
            p.result = res
          }
        }
        return true
      }
    }
    return p
  },

  // Runs a plan to the end in one go (offline tests).
  planAll(spec, world) {
    var p = this.planner(spec, world)
    p.step(() => false)
    return p.result
  },

  // The live world: blocks, the heightmap and the loaded check through KubeJS / Java.
  world(server, dimension) {
    var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
    var level = server.getLevel(dimension)
    var source = level.getChunkSource()
    var chunks = {}
    return {
      minY: level.getMinBuildHeight(),
      id: (x, y, z) => String(level.getBlock(x, y, z).id),
      top: (x, z) => level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z),
      loaded: (x, z) => {
        var k = (x >> 4) + ',' + (z >> 4)
        var v = chunks[k]
        if (v === undefined) {
          v = !!source.hasChunk(x >> 4, z >> 4)
          chunks[k] = v
        }
        return v
      }
    }
  },

  // Plan, then run the commands, both under the time budget; done(result or null). Never throws.
  repair(server, spec, done) {
    var self = this
    var started = Date.now()
    var ticks = 0
    var finish = res => {
      try {
        done(res)
      } catch (e) {
        console.error(`[ttl] build ${spec.label}: after the terrain repair: ${e}`)
      }
    }
    if (!spec.enabled) {
      console.info(`[ttl] build ${spec.label}: terrain repair off`)
      finish(null)
      return
    }
    var p
    try {
      p = this.planner(spec, this.world(server, spec.dimension))
    } catch (e) {
      console.error(`[ttl] build ${spec.label}: terrain repair unavailable (${e})`)
      finish(null)
      return
    }
    var run = res => {
      var i = 0
      var step = () => {
        ticks++
        var t0 = Date.now()
        try {
          var end = Math.min(res.cmds.length, i + self.CMDS_PER_TICK)
          while (i < end) {
            server.runCommandSilent(`execute in ${spec.dimension} run ${res.cmds[i++]}`)
            if (Date.now() - t0 >= self.BUDGET_MS) break
          }
        } catch (e) {
          console.error(`[ttl] build ${spec.label}: terrain repair failed at command ${i}: ${e}`)
          finish(null)
          return
        }
        if (i < res.cmds.length) {
          server.scheduleInTicks(1, step)
          return
        }
        console.info(`[ttl] build ${spec.label}: repaired ${res.foundation} foundation, ${res.skirt} skirt, ${res.lava} lava ` +
          `(${res.cmds.length} fills, ${ticks} ticks, ${Date.now() - started} ms; depth ${spec.depth}, ring ${spec.ring}` +
          `${spec.keepWater ? ', water kept' : ''}; ${res.deep} gaps run deeper, ${res.unloaded} columns not loaded)`)
        finish(res)
      }
      step()
    }
    var think = () => {
      ticks++
      var t0 = Date.now()
      try {
        if (!p.step(() => Date.now() - t0 >= self.BUDGET_MS)) {
          server.scheduleInTicks(1, think)
          return
        }
      } catch (e) {
        console.error(`[ttl] build ${spec.label}: terrain repair failed while planning: ${e}`)
        finish(null)
        return
      }
      run(p.result)
    }
    think()
  }
}
