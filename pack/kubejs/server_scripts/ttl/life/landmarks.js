// Places the canon landmarks of design/data/landmarks.toml (TtlData.landmarks) in the Tensura world with
// Tensura's own jigsaw structures: Rigurd's goblin village, the lizardmen of Lake Siss, the orc camp, the dwarf
// village on the Dwarven Road, ... Each landmark is placed once (persistentData ttl.landmark.<name>.version =
// its `version`), one at a time, after Tempest and Dwargon; world_reset.js places them again after an overworld
// reset. Op commands: /ttl landmark list | place <name|all> | where <name>.
//
// Per landmark:
// 1. hold the area (reach + the farthest candidate offset) with chunk tickets (life/chunk_hold.js, loaded in the
//    background, no synchronous `forceload` burst) and wait until every chunk is FULL; give up after LOAD_TIMEOUT;
// 2. take out the old copies its TOML `remove` list names (life/unplace.js: block for block, only where the world still
//    holds the structure's own blocks), once each (ttl.landmark.<name>.removed.<id>);
// 3. survey the nominal spot and 16 candidates 32 and 64 blocks out (heightmaps): water fraction and ground
//    spread; drop candidates that come within `keepout` + reach of Tempest's or Dwargon's box; best first;
// 4. generate the structure start the way vanilla `/place structure` does (no biome check), then GROUND it: a jigsaw
//    sets its pieces on the chunk generator's own surface (heightmap WORLD_SURFACE_WG of the noise), which on an
//    imported map (Lerfing's) is not the real ground, so a village floats or sinks by the difference. Every group of
//    touching rigid pieces (a building, a bridge chain, a cavern) moves by the median of real surface minus generator
//    surface over its own columns; terrain_matching pieces (roads) already follow the real surface when placed;
// 5. place the pieces chunk by chunk (every chunk of the start's box must be FULL). A missing chunk or an exception is
//    logged with its reason and the next candidate is tried (up to TRIES); a pass that places nothing tries again
//    RETRY_DELAY ticks later, RETRIES times, before it counts as a failed boot attempt. (Until 19/11/2026 this was
//    `/place structure` plus a marker entity summoned on success: on an import boot the marker was not found although
//    the structure stood, so "failed" spots got copies and the next candidate one more: orc_camp on staging.)
// 6. register the start in its chunks, because a placement by hand does not: the structure's spawn_overrides
//    (goblins, lizardmen, orcs and dwarves keep spawning inside) need it;
// 7. foundation (life/repair.js, TOML repair / repair_depth / repair_keep_water): under every column of a rigid piece,
//    gaps (air, plants, trees; water unless the landmark is a water one) down to the ground become dirt and stone, so
//    nothing stands on pillars or overhangs;
// 8. log `[ttl] landmark <name> placed: <structure> at <x> <y> <z>` and remember the spot and box for /ttl landmark where.
const TtlLandmarks = {
  OBJECTIVE: 'ttl.landmark',
  START_DELAY: 900, // after Tempest (300) and Dwargon have started placing
  LOAD_POLL: 40,
  LOAD_TIMEOUT: 12000, // 10 min: up to 625 fresh chunks generate in the background while the server ticks
  OFFSETS: [32, 64],
  TRIES: 4,
  BOTTOM_LAYERS: 3, // foundation: the lowest solid block of a rigid piece's bottom layers is what it stands on
  RETRIES: 2, // in-boot retries when no candidate could be placed (chunks still settling after an import)
  RETRY_DELAY: 600,
  CURRENT: 'current', // /ttl landmark remove <name>: the copy recorded in persistentData
  REMOVED_GONE: 2, // ttl.landmark.<name>.removed.<id>: 1 = taken out, 2 = was not there (nothing done)
  BOOT_ATTEMPTS: 3, // boots in a row that may fail before a landmark waits for /ttl landmark place
  NOT_GROUND: ['_log', '_wood', '_leaves', '_stem', 'mushroom_block', 'vine', 'bamboo', 'short_grass', 'tall_grass',
    'fern', 'bush', 'snow', 'moss_carpet', 'azalea', 'dripleaf', 'hanging_roots', 'cocoa', 'bee_nest', 'lily_pad'],
  queue: [],
  busy: false,
  current: null, // the landmark pump() took off the queue and is placing
  retries: {},

  all() {
    return TtlData.landmarks.landmark
  },

  find(name) {
    return this.all().find(l => l.name === name) || null
  },

  key(l, k) {
    return `ttl.landmark.${l.name}.${k}`
  },

  run(server, cmd) {
    return server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  java() {
    if (this.j !== undefined) return this.j
    try {
      this.j = {
        Registries: Java.loadClass('net.minecraft.core.registries.Registries'),
        ResourceLocation: Java.loadClass('net.minecraft.resources.ResourceLocation'),
        ChunkPos: Java.loadClass('net.minecraft.world.level.ChunkPos'),
        BoundingBox: Java.loadClass('net.minecraft.world.level.levelgen.structure.BoundingBox'),
        Types: Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      }
    } catch (e) {
      console.error(`[ttl] landmarks: Java classes unavailable (${e})`)
      this.j = null
    }
    return this.j
  },

  // Tempest's and Dwargon's worked areas (box + margin), from their own scripts.
  keepouts() {
    var out = []
    var add = (label, get) => {
      try {
        var b = get()
        out.push({ label: label, x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 })
      } catch (e) {
        console.warn(`[ttl] landmarks: ${label} box unavailable (${e})`)
      }
    }
    add('Tempest', () => TtlTempest.box())
    add('Dwargon', () => TtlDwargon.box())
    return out
  },

  clearOf(l, x, z, boxes) {
    var need = TtlData.landmarks.keepout + l.reach
    return boxes.every(b => {
      var dx = Math.max(b.x0 - x, 0, x - b.x1)
      var dz = Math.max(b.z0 - z, 0, z - b.z1)
      return Math.sqrt(dx * dx + dz * dz) >= need
    })
  },

  candidates(l) {
    var out = [{ x: l.x, z: l.z, ring: 0 }]
    this.OFFSETS.forEach(d => {
      for (var i = 0; i < 8; i++) {
        var a = Math.PI * i / 4
        out.push({ x: l.x + Math.round(d * Math.cos(a)), z: l.z + Math.round(d * Math.sin(a)), ring: d })
      }
    })
    var boxes = this.keepouts()
    var self = this
    return out.filter(c => self.clearOf(l, c.x, c.z, boxes))
  },

  area(l) {
    var r = l.reach + this.OFFSETS[this.OFFSETS.length - 1] + 16
    return { x0: l.x - r, z0: l.z - r, x1: l.x + r, z1: l.z + r }
  },

  // Ground probe through Java heightmaps: { y, water } per column (y = first free block above the ground, water
  // counts as ground), trees and plants skipped. null when unavailable.
  probe(server) {
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      var level = server.getLevel(TtlLife.OVERWORLD)
      var skip = this.NOT_GROUND
      return (x, z) => {
        var y = level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z)
        var top = String(level.getBlock(x, y - 1, z).id)
        if (top.indexOf('water') >= 0 || top === 'minecraft:seagrass' || top === 'minecraft:kelp_plant') return { y: y, water: true }
        for (var n = 0; n < 40 && y > -63; n++) {
          var id = String(level.getBlock(x, y - 1, z).id)
          if (id !== 'minecraft:air' && !skip.some(k => id.indexOf(k) >= 0)) break
          y--
        }
        return { y: y, water: false }
      }
    } catch (e) {
      console.warn(`[ttl] landmarks: heightmaps unavailable (${e}); trying candidates unsurveyed`)
      return null
    }
  },

  // 5x5 samples over the inner 60% of the reach: water fraction and land height spread -> score (lower = better).
  survey(l, c, at) {
    var r = Math.max(8, Math.round(l.reach * 0.6))
    var water = 0
    var ys = []
    for (var i = -2; i <= 2; i++) {
      for (var j = -2; j <= 2; j++) {
        var s = at(c.x + Math.round(i * r / 2), c.z + Math.round(j * r / 2))
        if (s.water) water++
        else ys.push(s.y)
      }
    }
    var wf = water / 25
    ys.sort((a, b) => a - b)
    var spread = ys.length ? ys[Math.floor(ys.length * 0.9)] - ys[Math.floor(ys.length * 0.1)] : 0
    var centre = at(c.x, c.z)
    var fit = true
    var score = spread + c.ring / 16
    if (l.surface === 'land') {
      fit = wf <= 0.25 && !centre.water
      score += wf * 40
    } else if (l.surface === 'water') {
      fit = wf >= 0.2 && wf <= 0.9
      score += Math.abs(wf - 0.55) * 30
    }
    return { fit: fit, score: score, water: wf, spread: spread, y: centre.y }
  },

  // The structure start vanilla `/place structure <id> x 64 z` would make (seed + chunk decide it; no biome check):
  // { structure, start, level, gen }, or { why } when the structure is unknown or does not generate there.
  generate(server, id, x, z) {
    var J = this.java()
    if (!J) return { why: 'Java classes unavailable' }
    var level = server.getLevel(TtlLife.OVERWORLD)
    var access = server.registryAccess()
    var structure = access.registryOrThrow(J.Registries.STRUCTURE).get(J.ResourceLocation.parse(id))
    if (!structure) return { why: `unknown structure ${id}` }
    var gen = level.getChunkSource().getGenerator()
    var start = structure.generate(access, gen, gen.getBiomeSource(), level.getChunkSource().randomState(),
      level.getStructureManager(), level.getSeed(), new J.ChunkPos(x >> 4, z >> 4), 0, level, b => true)
    if (!start.isValid()) return { why: 'the structure start does not generate here' }
    return { structure: structure, start: start, level: level, gen: gen }
  },

  // A jigsaw piece's file, rotation, origin and projection; null for a piece that is not a single pool element.
  piece(p) {
    try {
      var el = p.getElement()
      var m = /Left\[([^\]]+)\]/.exec(String(el))
      return {
        template: m ? m[1] : null,
        rigid: String(el.getProjection()).toLowerCase().indexOf('rigid') >= 0,
        rotation: p.getRotation(),
        pos: p.getPosition()
      }
    } catch (e) {
      return null
    }
  },

  pieces(start) {
    var list = start.getPieces()
    var out = []
    for (var i = 0; i < list.size(); i++) {
      var p = list.get(i)
      var bb = p.getBoundingBox()
      var info = this.piece(p)
      out.push({ p: p, i: i, info: info, rigid: !info || info.rigid,
        x0: bb.minX(), y0: bb.minY(), z0: bb.minZ(), x1: bb.maxX(), y1: bb.maxY(), z1: bb.maxZ() })
    }
    return out
  },

  // Step 4: move every group of touching rigid pieces by the median (real surface - generator surface) over its
  // columns. at(x, z) is the real surface probe, read before anything is placed. Returns { groups: [dy per group],
  // pieces: [dy per piece] } (the per-piece list is recorded, ttl.landmark.<name>.moves, so the copy can be taken out
  // again: regenerating the start gives the unmoved pieces).
  ground(server, s, at) {
    var J = this.java()
    var ps = this.pieces(s.start)
    var n = ps.length
    var up = []
    for (var i = 0; i < n; i++) up.push(i)
    var root = i => {
      while (up[i] !== i) {
        up[i] = up[up[i]]
        i = up[i]
      }
      return i
    }
    var touch = (a, b) => a.x0 <= b.x1 + 1 && b.x0 <= a.x1 + 1 && a.z0 <= b.z1 + 1 && b.z0 <= a.z1 + 1 &&
      a.y0 <= b.y1 + 1 && b.y0 <= a.y1 + 1
    for (var a = 0; a < n; a++) {
      if (!ps[a].rigid) continue
      for (var b = a + 1; b < n; b++) {
        if (ps[b].rigid && touch(ps[a], ps[b])) up[root(a)] = root(b)
      }
    }
    var groups = {}
    for (var k = 0; k < n; k++) {
      if (!ps[k].rigid) continue
      var r = root(k)
      ;(groups[r] = groups[r] || []).push(ps[k])
    }
    var rs = s.level.getChunkSource().randomState()
    var genAt = (x, z) => s.gen.getFirstFreeHeight(x, z, J.Types.WORLD_SURFACE_WG, s.level, rs)
    var moves = []
    var per = ps.map(q => 0)
    Object.keys(groups).forEach(g => {
      var seen = {}
      var d = []
      groups[g].forEach(q => {
        var st = Math.max(1, Math.ceil(Math.max(q.x1 - q.x0, q.z1 - q.z0) / 8))
        for (var x = q.x0; x <= q.x1; x += st) {
          for (var z = q.z0; z <= q.z1; z += st) {
            var key = x + ',' + z
            if (seen[key]) continue
            seen[key] = true
            var real = at(x, z)
            if (real && real.y !== null) d.push(real.y - genAt(x, z))
          }
        }
      })
      if (d.length === 0) return
      d.sort((p, q) => p - q)
      var dy = d[Math.floor(d.length / 2)]
      groups[g].forEach(q => {
        if (dy !== 0) q.p.move(0, dy, 0)
        per[q.i] = dy
      })
      moves.push(dy)
    })
    return { groups: moves, pieces: per }
  },

  // Step 5: every chunk of the start's box must be FULL; then the pieces, chunk by chunk (what /place structure does).
  // Returns null, or why it could not.
  placeStart(server, s) {
    var J = this.java()
    var level = s.level
    var source = level.getChunkSource()
    var bb = s.start.getBoundingBox()
    var c0 = [bb.minX() >> 4, bb.minZ() >> 4]
    var c1 = [bb.maxX() >> 4, bb.maxZ() >> 4]
    for (var cx = c0[0]; cx <= c1[0]; cx++) {
      for (var cz = c0[1]; cz <= c1[1]; cz++) {
        if (source.getChunkNow(cx, cz) === null) return `chunk ${cx} ${cz} (block ${cx * 16} ${cz * 16}) not loaded`
      }
    }
    var lo = level.getMinBuildHeight()
    var hi = level.getMaxBuildHeight()
    for (var x = c0[0]; x <= c1[0]; x++) {
      for (var z = c0[1]; z <= c1[1]; z++) {
        s.start.placeInChunk(level, level.structureManager(), s.gen, level.getRandom(),
          new J.BoundingBox(x * 16, lo, z * 16, x * 16 + 15, hi, z * 16 + 15), new J.ChunkPos(x, z))
      }
    }
    return null
  },

  // Step 6: record the start in its chunks (structure references), so spawn_overrides and "inside" checks see it.
  register(server, l, s) {
    try {
      var origin = s.start.getChunkPos()
      var bb = s.start.getBoundingBox()
      s.level.getChunk(origin.x, origin.z).setStartForStructure(s.structure, s.start)
      for (var cx = bb.minX() >> 4; cx <= bb.maxX() >> 4; cx++) {
        for (var cz = bb.minZ() >> 4; cz <= bb.maxZ() >> 4; cz++) {
          var chunk = s.level.getChunk(cx, cz)
          chunk.addReferenceForStructure(s.structure, origin.toLong())
          chunk.setUnsaved(true)
        }
      }
      return true
    } catch (e) {
      console.warn(`[ttl] landmark ${l.name}: placed, but the structure start could not be registered (${e}); its NPCs only spawn once`)
      return false
    }
  },

  // Fill materials like the surface at x, z: sand or red sand over sandstone, else dirt over stone.
  materials(level, x, z) {
    var m = { top: 'minecraft:grass_block', fill: 'minecraft:dirt', deep: 'minecraft:stone' }
    try {
      var y = level.getHeight(this.java().Types.MOTION_BLOCKING_NO_LEAVES, x, z)
      var id = String(level.getBlock(x, y - 1, z).id)
      if (id.indexOf('red_sand') >= 0) m = { top: 'minecraft:red_sand', fill: 'minecraft:red_sandstone', deep: 'minecraft:stone' }
      else if (id.indexOf('sand') >= 0) m = { top: 'minecraft:sand', fill: 'minecraft:sandstone', deep: 'minecraft:stone' }
    } catch (e) {
      // keep the default
    }
    return m
  },

  // Step 7: what life/repair.js needs: every column under a rigid piece is a 'build' column whose bottom is the lowest
  // rigid piece there (filled below it, never inside); every other column is left alone (no ring, no skirt).
  foundationSpec(l, s, groundY) {
    var self = this
    var ps = this.pieces(s.start).filter(q => q.rigid)
    if (ps.length === 0) return null
    var x0 = Math.min.apply(null, ps.map(q => q.x0))
    var z0 = Math.min.apply(null, ps.map(q => q.z0))
    var w = Math.max.apply(null, ps.map(q => q.x1)) - x0 + 1
    var len = Math.max.apply(null, ps.map(q => q.z1)) - z0 + 1
    var bottom = new Array(w * len)
    ps.forEach(q => {
      for (var x = q.x0; x <= q.x1; x++) {
        for (var z = q.z0; z <= q.z1; z++) {
          var i = (z - z0) * w + (x - x0)
          if (bottom[i] === undefined || q.y0 < bottom[i]) bottom[i] = q.y0
        }
      }
    })
    return {
      label: `landmark ${l.name}`, enabled: l.repair !== false, dimension: TtlLife.OVERWORLD, ring: 0,
      x0: x0, z0: z0, w: w, l: len, ground: groundY, depth: l.repair_depth || TtlRepair.DEPTH,
      keepWater: l.surface === 'water' || !!l.repair_keep_water, mat: this.materials(s.level, x0 + (w >> 1), z0 + (len >> 1)),
      // A file's bottom layer is the ground layer (a jigsaw sinks it into the ground block), often air under the
      // walls; where the ground under the group is a block or two lower than its median, the wall would stand on
      // that air. So the foundation starts under the lowest solid block of the bottom BOTTOM_LAYERS layers (as
      // placed), not under the box: an eave or a balcony higher up never gets a pillar.
      col: (gx, gz) => {
        var v = bottom[gz * w + gx]
        if (v === undefined) return null
        for (var y = v; y < v + self.BOTTOM_LAYERS; y++) {
          if (TtlRepair.cls(String(s.level.getBlock(x0 + gx, y, z0 + gz).id)) === 'solid') return { t: 'build', bottom: y }
        }
        return { t: 'build', bottom: v }
      }
    }
  },

  // The commonest natural top block on a square ring 8 blocks round a box (for the ground an old copy leaves behind).
  siteTop(level, box) {
    var Types = this.java().Types
    var source = level.getChunkSource()
    var count = {}
    var best = 'minecraft:grass_block'
    var most = 0
    var x0 = box.x0 - 8
    var z0 = box.z0 - 8
    var x1 = box.x1 + 8
    var z1 = box.z1 + 8
    var spots = []
    for (var i = 0; i <= 4; i++) {
      var fx = Math.round(x0 + (x1 - x0) * i / 4)
      var fz = Math.round(z0 + (z1 - z0) * i / 4)
      spots.push([fx, z0], [fx, z1], [x0, fz], [x1, fz])
    }
    spots.forEach(p => {
      if (source.getChunkNow(p[0] >> 4, p[1] >> 4) === null) return
      var id = String(level.getBlock(p[0], level.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, p[0], p[1]) - 1, p[1]).id)
      if (TtlRepair.TOPS.indexOf(id) < 0) return
      count[id] = (count[id] || 0) + 1
      if (count[id] > most) {
        most = count[id]
        best = id
      }
    })
    return best
  },

  removals(server, l) {
    var data = server.persistentData
    var self = this
    return (l.remove || []).filter(r => !data.getInt(self.key(l, `removed.${r.id}`)))
  },

  // Step 2: the old copies of l still to take out, regenerated from seed + chunk exactly as they were placed (not
  // grounded: they predate it); next() afterwards, also when nothing could be done.
  removeOld(server, l, next, todo) {
    todo = todo || this.removals(server, l)
    if (todo.length === 0) {
      next()
      return
    }
    var self = this
    var data = server.persistentData
    var level = server.getLevel(TtlLife.OVERWORLD)
    var units = []
    var box = null
    todo.forEach(r => {
      var label = `landmark ${l.name} old copy ${r.id} (${r.x} ${r.z})`
      var s = self.generate(server, r.structure || l.structure, r.x, r.z)
      if (s.why) {
        console.warn(`[ttl] ${label}: ${s.why}; nothing to take out`)
        if (r.id !== self.CURRENT) data.putInt(self.key(l, `removed.${r.id}`), self.REMOVED_GONE)
        return
      }
      var moves = r.moves ? String(r.moves).split(',').map(Number) : []
      var jobs = []
      self.pieces(s.start).forEach(q => {
        if (moves[q.i]) {
          q.p.move(0, moves[q.i], 0)
          q.info = self.piece(q.p)
          var bb = q.p.getBoundingBox()
          q.y0 = bb.minY()
          q.y1 = bb.maxY()
        }
        if (!q.info || !q.info.template) return
        box = box ? { x0: Math.min(box.x0, q.x0), z0: Math.min(box.z0, q.z0), x1: Math.max(box.x1, q.x1), z1: Math.max(box.z1, q.z1) } :
          { x0: q.x0, z0: q.z0, x1: q.x1, z1: q.z1 }
        jobs.push({ template: q.info.template, x: q.info.pos.getX(), y: q.info.pos.getY(), z: q.info.pos.getZ(),
          rotation: q.info.rotation, ground: 0, terrain: !q.info.rigid })
      })
      units.push({ label: label, id: r.id, jobs: jobs })
    })
    if (units.length === 0) {
      next()
      return
    }
    var top = this.siteTop(level, box)
    TtlUnplace.remove(server, TtlLife.OVERWORLD, units, { top: top, fill: 'minecraft:dirt' }, res => {
      if (res && todo.length === 1 && todo[0].id === self.CURRENT && res.removed === 1) {
        ;['version', 'at', 'box', 'spot', 'moves', 'repair'].forEach(k => data.remove(self.key(l, k)))
      }
      try {
        if (res) {
          units.forEach(u => {
            if (u.id !== self.CURRENT) data.putInt(self.key(l, `removed.${u.id}`), res.missing.indexOf(u.label) >= 0 ? self.REMOVED_GONE : 1)
          })
          console.info(`[ttl] landmark ${l.name}: ${res.removed} old cop${res.removed === 1 ? 'y' : 'ies'} taken out ` +
            `(${res.cells} blocks, ground top ${top}), ${res.skipped} not found, ${res.unloaded} cells in unloaded chunks`)
        } else console.error(`[ttl] landmark ${l.name}: taking out the old copies failed; tried again on the next boot`)
      } catch (e) {
        console.error(`[ttl] landmark ${l.name}: after taking out the old copies: ${e}`)
      }
      next()
    })
  },

  // Steps 3-8. done(placed, transient): transient = worth another try this boot (a chunk not loaded, an exception).
  place(server, l, done) {
    var data = server.persistentData
    var self = this
    var at = this.probe(server)
    var list = this.candidates(l).map(c => {
      c.s = at ? self.survey(l, c, at) : { fit: true, score: c.ring, water: -1, spread: -1, y: 0 }
      return c
    })
    var ranked = list.filter(c => c.s.fit).sort((a, b) => a.s.score - b.s.score)
    // Nothing fits the surface rule: still try the best-scoring spots rather than leave the landmark out.
    if (ranked.length === 0) {
      console.warn(`[ttl] landmark ${l.name}: no candidate fits surface=${l.surface}; trying the closest matches`)
      ranked = list.sort((a, b) => a.s.score - b.s.score)
    }
    var tries = ranked.slice(0, this.TRIES)
    var transient = false
    for (var i = 0; i < tries.length; i++) {
      var c = tries[i]
      var s = null
      var why = null
      var moves = { groups: [], pieces: [] }
      try {
        s = this.generate(server, l.structure, c.x, c.z)
        if (s.why) why = s.why
        else {
          if (at) moves = this.ground(server, s, at)
          why = this.placeStart(server, s)
          if (why) transient = true
        }
      } catch (e) {
        why = `${e}`
        transient = true
      }
      if (why) {
        console.warn(`[ttl] landmark ${l.name}: not placed at ${c.x} ${c.z}: ${why} (try ${i + 1}/${tries.length})`)
        continue
      }
      var registered = this.register(server, l, s)
      var bb = s.start.getBoundingBox()
      var first = s.start.getPieces().get(0)
      var y = first.getBoundingBox().minY() + first.getGroundLevelDelta()
      var box = `${bb.minX()} ${bb.minY()} ${bb.minZ()} ${bb.maxX()} ${bb.maxY()} ${bb.maxZ()}`
      data.putInt(this.key(l, 'version'), l.version)
      data.putString(this.key(l, 'at'), `${c.x} ${y} ${c.z}`)
      data.putString(this.key(l, 'box'), box)
      data.putInt(this.key(l, 'fails'), 0)
      data.putString(this.key(l, 'spot'), `${c.x} ${c.z}`)
      data.putString(this.key(l, 'moves'), moves.pieces.join(','))
      var g = moves.groups
      var range = g.length ? `${Math.min.apply(null, g)}..${Math.max.apply(null, g)}` : 'none'
      var tell = `[ttl] landmark ${l.name} placed: ${l.structure} at ${c.x} ${y} ${c.z} (try ${i + 1}, water ${c.s.water}, ` +
        `spread ${c.s.spread}, ${g.length} rigid group(s) grounded by ${range}, box ${box}` +
        `${registered ? '' : ', start not registered'}; version ${l.version})`
      var spec = this.foundationSpec(l, s, y - 1)
      if (!spec) {
        console.info(tell)
        done(true, false)
        return
      }
      TtlRepair.repair(server, spec, res => {
        data.putString(self.key(l, 'repair'), res ? `${res.foundation} ${res.skirt} ${res.lava}` : '')
        console.info(tell)
        done(true, false)
      })
      return
    }
    console.error(`[ttl] landmark ${l.name}: ${l.structure} could not be placed near ${l.x} ${l.z} (${tries.length} spots tried)`)
    done(false, transient)
  },

  // One landmark at a time: hold the chunks, wait until they are FULL, take out old copies, place, release, next. Not
  // placed when the area is still not loaded after LOAD_TIMEOUT (a failed boot attempt): surveying a missing chunk would
  // load it synchronously, the stall the tickets avoid.
  pump(server) {
    if (this.busy || this.queue.length === 0) return
    var l = this.queue.shift()
    var self = this
    var data = server.persistentData
    this.busy = true
    this.current = l.name
    var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, this.area(l), `landmark ${l.name}`)
    var next = () => {
      TtlChunks.release(server, hold)
      self.busy = false
      self.current = null
      server.scheduleInTicks(20, () => self.pump(server))
    }
    var failed = (transient, why) => {
      var n = self.retries[l.name] || 0
      if (transient && n < self.RETRIES) {
        self.retries[l.name] = n + 1
        console.warn(`[ttl] landmark ${l.name}: ${why}; trying again in ${self.RETRY_DELAY} ticks (${n + 1}/${self.RETRIES})`)
        server.scheduleInTicks(self.RETRY_DELAY, () => self.enqueue(server, l))
      } else {
        data.putInt(self.key(l, 'fails'), data.getInt(self.key(l, 'fails')) + 1)
        console.error(`[ttl] landmark ${l.name}: ${why}; not placed this boot`)
      }
    }
    TtlChunks.whenReady(server, hold, this.LOAD_POLL, this.LOAD_TIMEOUT, (ready, missing) => {
      if (!ready && missing > 0) {
        failed(false, `${missing} chunk(s) still not loaded after ${self.LOAD_TIMEOUT} ticks`)
        next()
        return
      }
      try {
        self.removeOld(server, l, () => {
          try {
            if (data.getInt(self.key(l, 'version')) === l.version) {
              next()
              return
            }
            self.place(server, l, (placed, transient) => {
              if (placed) delete self.retries[l.name]
              else failed(transient, 'no candidate could be placed')
              next()
            })
          } catch (e) {
            console.error(`[ttl] landmark ${l.name} placement failed: ${e}`)
            failed(true, `${e}`)
            next()
          }
        })
      } catch (e) {
        console.error(`[ttl] landmark ${l.name} placement failed: ${e}`)
        next()
      }
    })
  },

  // Once per landmark: not while it waits in the queue, and not while pump() is placing it. A world reset right after
  // boot (world_reset.js -> reset -> schedule) runs a second pass over pending() while the boot's pass is still placing
  // the first landmark; with only the queue checked, that landmark was queued again and placed twice (goblin_village
  // on staging, 19/11 16:55 and 16:56, after the Lerfing import).
  enqueue(server, l) {
    if (this.current === l.name || this.queue.some(q => q.name === l.name)) return
    this.queue.push(l)
    this.pump(server)
  },

  pending(server) {
    var data = server.persistentData
    var self = this
    return this.all().filter(l => (data.getInt(self.key(l, 'version')) !== l.version || self.removals(server, l).length > 0) &&
      data.getInt(self.key(l, 'fails')) < self.BOOT_ATTEMPTS)
  },

  schedule(server) {
    var self = this
    this.run(server, `scoreboard objectives add ${this.OBJECTIVE} dummy`)
    server.scheduleInTicks(this.START_DELAY, () => self.pending(server).forEach(l => self.enqueue(server, l)))
  },

  // World reset of the overworld: every landmark goes again on the new terrain. The old copies of the `remove` lists
  // stood on the old terrain, so there is nothing left to take out.
  reset(server) {
    var data = server.persistentData
    var self = this
    this.retries = {}
    this.all().forEach(l => {
      ;['version', 'at', 'box', 'fails', 'repair', 'spot', 'moves'].forEach(k => data.remove(self.key(l, k)))
      ;(l.remove || []).forEach(r => data.putInt(self.key(l, `removed.${r.id}`), self.REMOVED_GONE))
    })
    this.schedule(server)
  },

  describe(server, l) {
    var data = server.persistentData
    var v = data.getInt(this.key(l, 'version'))
    var at = String(data.getString(this.key(l, 'at')) || '')
    var state = v === l.version ? `placed at ${at}` : v ? `placed v${v} at ${at}, v${l.version} pending` :
      data.getInt(this.key(l, 'fails')) ? `FAILED ${data.getInt(this.key(l, 'fails'))}x` : 'pending'
    if (this.current === l.name) state += ' (placing)'
    else if (this.queue.some(q => q.name === l.name)) state += ' (queued)'
    var left = this.removals(server, l).length
    if (left) state += `, ${left} old cop${left === 1 ? 'y' : 'ies'} to take out`
    return `${l.name}: ${l.structure} near ${l.x} ${l.z}, ${state}`
  }
}

ServerEvents.loaded(event => TtlLandmarks.schedule(event.server))

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var named = (ctx, then) => {
    var name = String(Arguments.STRING.getResult(ctx, 'name')).toLowerCase()
    var server = ctx.source.getServer()
    if (name === 'all' && then.all) return then.all(server)
    var l = TtlLandmarks.find(name)
    if (!l) {
      say(ctx, `No landmark ${name}; see /ttl landmark list`)
      return 0
    }
    return then.one(server, l)
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('landmark')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('list').executes(ctx => {
        var server = ctx.source.getServer()
        TtlLandmarks.all().forEach(l => say(ctx, TtlLandmarks.describe(server, l)))
        return 1
      }))
      .then(Commands.literal('place')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, l) => {
            server.persistentData.remove(TtlLandmarks.key(l, 'version'))
            server.persistentData.putInt(TtlLandmarks.key(l, 'fails'), 0)
            TtlLandmarks.enqueue(server, l)
            say(ctx, `Placing ${l.name} near ${l.x} ${l.z}; watch the log for "[ttl] landmark ${l.name}"`)
            return 1
          },
          all: server => {
            TtlLandmarks.all().forEach(l => {
              server.persistentData.remove(TtlLandmarks.key(l, 'version'))
              server.persistentData.putInt(TtlLandmarks.key(l, 'fails'), 0)
              TtlLandmarks.enqueue(server, l)
            })
            say(ctx, `Placing all ${TtlLandmarks.all().length} landmarks one by one`)
            return 1
          }
        }))))
      // Takes out the copy this world has now (recorded spot + grounding moves), block for block (life/unplace.js);
      // `/ttl landmark place <name>` then places it again. For testing and for moving a landmark by hand.
      .then(Commands.literal('remove')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, l) => {
            var spot = String(server.persistentData.getString(TtlLandmarks.key(l, 'spot')) || '').split(' ').map(Number)
            if (spot.length !== 2 || isNaN(spot[0])) {
              say(ctx, `${l.name} has no recorded spot (placed before 19/11/2026 or not placed); use the TOML remove list`)
              return 0
            }
            if (TtlLandmarks.busy) {
              say(ctx, `the landmark placer is busy (${TtlLandmarks.current}); try again later`)
              return 0
            }
            var r = { id: TtlLandmarks.CURRENT, x: spot[0], z: spot[1], moves: String(server.persistentData.getString(TtlLandmarks.key(l, 'moves')) || '') }
            TtlLandmarks.busy = true
            var hold = TtlChunks.hold(server, TtlLife.OVERWORLD, TtlLandmarks.area(l), `landmark ${l.name} removal`)
            TtlChunks.whenReady(server, hold, TtlLandmarks.LOAD_POLL, TtlLandmarks.LOAD_TIMEOUT, ready => {
              var done = () => {
                TtlChunks.release(server, hold)
                TtlLandmarks.busy = false
                TtlLandmarks.pump(server)
              }
              if (!ready) {
                console.error(`[ttl] landmark ${l.name}: area not loaded, nothing removed`)
                done()
                return
              }
              TtlLandmarks.removeOld(server, l, done, [r])
            })
            say(ctx, `Taking out ${l.name} at ${spot.join(' ')}; watch the log for "[ttl] unplace landmark ${l.name}"`)
            return 1
          }
        }))))
      .then(Commands.literal('where')
        .then(Commands.argument('name', Arguments.STRING.create(event)).executes(ctx => named(ctx, {
          one: (server, l) => {
            var data = server.persistentData
            var at = String(data.getString(TtlLandmarks.key(l, 'at')) || '')
            var box = String(data.getString(TtlLandmarks.key(l, 'box')) || '')
            var repair = String(data.getString(TtlLandmarks.key(l, 'repair')) || '')
            say(ctx, `${l.title}: ${at ? `placed at ${at}` : `not placed, planned near ${l.x} ~ ${l.z}`}`)
            if (box) say(ctx, `  box ${box}`)
            if (repair) say(ctx, `  foundation ${repair.split(' ')[0]} cells`)
            say(ctx, `  /execute in ${TtlLife.OVERWORLD} run tp @s ${at ? at.split(' ').map((v, i) => i === 1 ? Number(v) + 2 : v).join(' ') : `${l.x} 200 ${l.z}`}`)
            return 1
          }
        }))))))
})
