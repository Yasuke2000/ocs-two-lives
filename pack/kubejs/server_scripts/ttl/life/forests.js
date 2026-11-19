// Planted forests (design/data/forests/patches.toml, the spots planned offline by tools/lerfing/forests.py, data in
// generated/placements.js): Jura's forest round Tempest and Treyni's old wood. Why planted: Tensura's ancient forest
// grows its giant trees as jigsaw STRUCTURES (tensura:ancient_forest/tree), and the import counted every structure step
// of Lerfing's proto chunks as done, so the repainted ancient_forest round Tempest populated without a single tree.
// Each patch is planted once (persistentData ttl.forest.<id>.version = its version) by the runner in life/works.js,
// one 64 x 64 tile at a time (chunk tickets over the tile's crowns), after the builds and landmarks are placed.
//
// Per tree, on the live terrain (the plan was made on the imported world; anything placed since wins):
// - giant (a Tensura ancient-forest template, x/z = the trunk centre): its rotated template box must stay clear of
//   Tempest's and Dwargon's boxes, every placed build and landmark, Lerfing's keepouts, the patch's clear and keep_clear
//   boxes; the trunk clear of the lanes; the trunk centre and 8 points on the trunk's rim on dry dirt-like soil within
//   LEVEL blocks of level; then `place template <id> <corner> <rotation>` with the corner ROOTS blocks under the lowest
//   ground (the jigsaw's own start_height -5: the roots go into the ground);
// - understory (a vanilla tree feature): dry soil, 3 blocks clear of every kept box, clear of the lanes; then
//   `place feature <id> x y z` (it grows only where the tree fits, like a sapling).
// A spot whose trunk already stands (a re-run, a bumped version: v1 planted but counted nothing) is left as it is.
// Log: `[ttl] forest <id> planted: G giants, U understory trees, A already standing (g giants), S skipped (...)
// (version V)`.
const TtlForests = {
  TILE: 64,
  ROOTS: 5,
  LEVEL: 4,
  ROT: ['none', 'clockwise_90', '180', 'counterclockwise_90'],
  TRUNK: ['_log', '_wood', '_stem'],
  told: 0, // giants whose place failed, logged with the reason (the first 5 per boot)
  // The forest floor in a tree's way: a tree feature grows only where its lower crown is air or #replaceable_by_trees,
  // and Tensura's hipokute grass and baffledil are not (local 19/11/2026: most of the understory's 'no room'); a dark
  // oak over tall grass grew without the log on its own spot. Cleared round the trunk before `place feature`.
  FLOOR: ['minecraft:short_grass', 'minecraft:tall_grass', 'minecraft:fern', 'minecraft:large_fern', 'minecraft:dead_bush',
    'minecraft:snow', 'minecraft:sweet_berry_bush', 'minecraft:moss_carpet', 'minecraft:pink_petals', 'tensura:hipokute_grass',
    'tensura:baffledil'],
  FLOWERS: ['tulip', 'orchid', 'allium', 'bluet', 'daisy', 'poppy', 'dandelion', 'cornflower', 'lily_of_the_valley',
    'lilac', 'peony', 'rose_bush', 'sunflower', 'torchflower', 'mushroom'],

  all() {
    return TtlWorks.data().forests || {}
  },

  key(id, k) {
    return `ttl.forest.${id}.${k}`
  },

  forget(server, id) {
    var self = this
    ;['version', 'pversion', 'piece', 'counts', 'skips'].forEach(k => server.persistentData.remove(self.key(id, k)))
  },

  // Template-local offset -> world offset for a /place template rotation (pivot = the corner).
  rotate(rot, lx, lz) {
    if (rot === 'clockwise_90') return [-lz, lx]
    if (rot === '180') return [-lx, -lz]
    if (rot === 'counterclockwise_90') return [lz, -lx]
    return [lx, lz]
  },

  // Corner and box of template tp placed with its trunk centre on (x, z) (tools/lerfing/forests.py giant_box).
  giantBox(tp, x, z, rot) {
    var o = this.rotate(rot, tp.trunk[0], tp.trunk[1])
    var cx = x - o[0]
    var cz = z - o[1]
    var a = this.rotate(rot, tp.size[0] - 1, tp.size[2] - 1)
    return { cx: cx, cz: cz, x0: Math.min(cx, cx + a[0]), z0: Math.min(cz, cz + a[1]), x1: Math.max(cx, cx + a[0]), z1: Math.max(cz, cz + a[1]) }
  },

  segDist(px, pz, s) {
    var vx = s[2] - s[0]
    var vz = s[3] - s[1]
    var L2 = vx * vx + vz * vz
    var f = L2 === 0 ? 0 : Math.max(0, Math.min(1, ((px - s[0]) * vx + (pz - s[1]) * vz) / L2))
    var dx = px - (s[0] + f * vx)
    var dz = pz - (s[1] + f * vz)
    return Math.sqrt(dx * dx + dz * dz)
  },

  // The lane's centre segment from the middle of the box's side towards `toward` (forests.py lane_segment).
  laneSegment(box, side, toward, length) {
    var sx = side === 'west' ? box[0] : side === 'east' ? box[2] : (box[0] + box[2]) / 2
    var sz = side === 'north' ? box[1] : side === 'south' ? box[3] : (box[1] + box[3]) / 2
    var dx = toward[0] - sx
    var dz = toward[1] - sz
    var L = Math.sqrt(dx * dx + dz * dz) || 1
    return [sx, sz, sx + dx / L * length, sz + dz / L * length]
  },

  // Tiles of the plan: {area, giants: [...], under: [...]}, row by row (deterministic: a restart resumes at a tile index).
  pieces(p) {
    var self = this
    var tiles = {}
    var get = (x, z) => {
      var k = `${Math.floor(x / self.TILE)},${Math.floor(z / self.TILE)}`
      if (!tiles[k]) tiles[k] = { tx: Math.floor(x / self.TILE), tz: Math.floor(z / self.TILE), giants: [], under: [], x0: 1e9, z0: 1e9, x1: -1e9, z1: -1e9 }
      return tiles[k]
    }
    var grow = (t, x0, z0, x1, z1) => {
      t.x0 = Math.min(t.x0, x0)
      t.z0 = Math.min(t.z0, z0)
      t.x1 = Math.max(t.x1, x1)
      t.z1 = Math.max(t.z1, z1)
    }
    p.giants.forEach(g => {
      var t = get(g[1], g[2])
      var b = self.giantBox(p.templates[p.giant_keys[g[0]]], g[1], g[2], self.ROT[g[3]])
      t.giants.push(g)
      grow(t, b.x0 - 2, b.z0 - 2, b.x1 + 2, b.z1 + 2)
      // `place template` checks that the UNROTATED box from the corner (corner + size, +x +z) is loaded, whatever the
      // rotation: without it, rotated giants failed with "That position is not loaded" (local 19/11/2026)
      var tp = p.templates[p.giant_keys[g[0]]]
      grow(t, b.cx, b.cz, b.cx + tp.size[0], b.cz + tp.size[2])
    })
    p.understory.forEach(u => {
      var t = get(u[1], u[2])
      t.under.push(u)
      // `place feature` wants the tree's chunk and its 8 neighbours loaded
      grow(t, ((u[1] >> 4) - 1) * 16, ((u[2] >> 4) - 1) * 16, ((u[1] >> 4) + 2) * 16 - 1, ((u[2] >> 4) + 2) * 16 - 1)
    })
    return Object.keys(tiles).map(k => tiles[k]).sort((a, b) => a.tz - b.tz || a.tx - b.tx)
      .map(t => ({ area: { x0: t.x0, z0: t.z0, x1: t.x1, z1: t.z1 }, giants: t.giants, under: t.under }))
  },

  // What stays clear for this patch: TtlWorks.kept + the patch's clear boxes + keep_clear (recorded box, else the
  // planner's offline box, + pad); lanes from the recorded build box.
  rules(server, p) {
    var kept = TtlWorks.kept(server, false)
    p.clear.forEach(c => kept.push({ label: 'clear', x0: c[0], z0: c[1], x1: c[2], z1: c[3] }))
    p.keep_clear.forEach(k => {
      var b = TtlWorks.placedBox(server, k.kind, k.name) || k.offline
      kept.push({ label: `${k.kind} ${k.name}`, x0: b[0] - k.pad, z0: b[1] - k.pad, x1: b[2] + k.pad, z1: b[3] + k.pad })
    })
    var self = this
    var lanes = p.lanes.map(l => ({
      half: l.half,
      seg: self.laneSegment(TtlWorks.placedBox(server, 'build', l.build) || l.offline, l.side, l.toward, l.length)
    }))
    return { kept: kept, lanes: lanes }
  },

  laneHit(rules, x, z, gap) {
    var self = this
    return rules.lanes.some(l => self.segDist(x, z, l.seg) < l.half + gap)
  },

  // A tree stands on (x, z): hm.ground looks through logs and leaves, so on a trunk it ends at the trunk's foot. The
  // 2 x 2 from (x, z) (dark oak, mega spruce: v1 left some with a plant on the spot itself and the log beside it).
  standing(hm, x, z) {
    for (var d = 0; d < 4; d++) {
      var cx = x + (d & 1)
      var cz = z + (d >> 1)
      var y = hm.ground(cx, cz)
      if (y === null) continue
      var id = String(hm.block(cx, y, cz))
      if (this.TRUNK.some(k => id.indexOf(k) >= 0)) return true
    }
    return false
  },

  // Clears the forest floor (FLOOR, FLOWERS) in the tree's lower crown: x-2..x+3, z-2..z+3, ground and one above.
  clearFloor(server, hm, x, y, z) {
    var self = this
    for (var dx = -2; dx <= 3; dx++) {
      for (var dz = -2; dz <= 3; dz++) {
        for (var dy = 0; dy <= 1; dy++) {
          var id = String(hm.block(x + dx, y + dy, z + dz))
          if (id === 'minecraft:air') continue
          if (self.FLOOR.indexOf(id) >= 0 || (id.indexOf('minecraft:') === 0 && self.FLOWERS.some(k => id.indexOf(k) >= 0) &&
            !/_block|_stem|potted_/.test(id))) {
            // without drops (life/drops.js): a plain setblock pops the top half of a tall plant as seeds
            if (typeof TtlDrops === 'undefined' || TtlDrops.clearColumn(server, TtlLife.OVERWORLD, x + dx, y + dy, y + dy, z + dz) < 0) {
              TtlWorks.run(server, `setblock ${x + dx} ${y + dy} ${z + dz} minecraft:air`)
            }
          }
        }
      }
    }
  },

  // [giants, understory, skipped, giants standing, understory standing] (v1 stored the first three).
  counts(text) {
    var c = TtlWorks.ints(text) || []
    for (var i = 0; i < 5; i++) c[i] = c[i] || 0
    return c
  },

  // Plants one giant; returns null, 'standing' or why it was skipped.
  giant(server, hm, p, rules, g) {
    var tid = p.giant_keys[g[0]]
    var tp = p.templates[tid]
    var rot = this.ROT[g[3]]
    var x = g[1]
    var z = g[2]
    var b = this.giantBox(tp, x, z, rot)
    if (TtlWorks.boxHits(rules.kept, b, 0)) return 'kept'
    if (this.laneHit(rules, x, z, tp.trunk_r + 1)) return 'lane'
    if (this.standing(hm, x, z)) return 'standing'
    var r = tp.trunk_r
    var ys = []
    for (var dx = -r; dx <= r; dx += r) {
      for (var dz = -r; dz <= r; dz += r) {
        if (!hm.soil(x + dx, z + dz) || hm.wet(x + dx, z + dz)) return 'ground'
        ys.push(hm.ground(x + dx, z + dz))
      }
    }
    var lo = Math.min.apply(null, ys)
    if (Math.max.apply(null, ys) - lo > this.LEVEL) return 'slope'
    var cmd = `place template ${tid} ${b.cx} ${lo - this.ROOTS} ${b.cz} ${rot}`
    var at = TtlWorks.attempt(server, cmd)
    if (at.result > 0) return null
    if (this.told < 5) {
      this.told++
      console.warn(`[ttl] forest: giant at ${x} ${z} not placed (${cmd}): ${at.error || 'no result'}`)
    }
    return 'place failed'
  },

  understory(server, hm, p, rules, u) {
    var x = u[1]
    var z = u[2]
    if (TtlWorks.inBox(rules.kept, x, z, 3)) return 'kept'
    if (this.laneHit(rules, x, z, 2)) return 'lane'
    if (this.standing(hm, x, z)) return 'standing'
    if (!hm.soil(x, z) || hm.wet(x, z)) return 'ground'
    var y = hm.ground(x, z)
    this.clearFloor(server, hm, x, y, z)
    var ok = TtlWorks.run(server, `place feature ${p.features[u[0]]} ${x} ${y} ${z}`)
    return ok > 0 ? null : 'no room'
  },

  work(server, id, force, done) {
    var p = this.all()[id]
    var data = server.persistentData
    if (!force && data.getInt(this.key(id, 'version')) === p.version) {
      done()
      return
    }
    if (force) this.forget(server, id)
    TtlWorks.begin(server, this, id, p.version)
    var pieces = this.pieces(p)
    var counts = this.counts(data.getString(this.key(id, 'counts')))
    var skips = {}
    try {
      skips = JSON.parse(String(data.getString(this.key(id, 'skips')) || '{}'))
    } catch (e) {
      skips = {}
    }
    var rules = this.rules(server, p)
    var self = this
    var start = data.getInt(this.key(id, 'piece'))
    console.info(`[ttl] forest ${id}: planting ${p.giants.length} giants and ${p.understory.length} understory trees in ${pieces.length} tiles` +
      (start ? ` (resuming at tile ${start})` : ''))
    var next = i => {
      if (i >= pieces.length) {
        data.putInt(self.key(id, 'version'), p.version)
        var why = Object.keys(skips).map(k => `${k} ${skips[k]}`).join(', ')
        console.info(`[ttl] forest ${id} planted: ${counts[0]} giants, ${counts[1]} understory trees, ${counts[3] + counts[4]} already standing (${counts[3]} giants), ${counts[2]} skipped (${why || 'none'}) (version ${p.version})`)
        done()
        return
      }
      var pc = pieces[i]
      TtlWorks.withArea(server, pc.area, `forest ${id} tile ${i + 1}/${pieces.length}`, (hm, release) => {
        var fns = []
        var tally = (why, slot) => {
          if (why === null) counts[slot]++
          else if (why === 'standing') counts[slot + 3]++
          else {
            counts[2]++
            skips[why] = (skips[why] || 0) + 1
          }
        }
        pc.giants.forEach(g => fns.push(() => tally(self.giant(server, hm, p, rules, g), 0)))
        pc.under.forEach(u => fns.push(() => tally(self.understory(server, hm, p, rules, u), 1)))
        TtlWorks.budgeted(server, fns, () => {
          release()
          data.putInt(self.key(id, 'piece'), i + 1)
          data.putString(self.key(id, 'counts'), counts.join(' '))
          data.putString(self.key(id, 'skips'), JSON.stringify(skips))
          server.scheduleInTicks(TtlWorks.GAP, () => next(i + 1))
        })
      }, why => {
        console.error(`[ttl] forest ${id}: tile ${i + 1}/${pieces.length} skipped: ${why}; the next boot tries it again`)
        done()
      })
    }
    next(start)
  },

  describe(server, id) {
    var p = this.all()[id]
    var data = server.persistentData
    var v = data.getInt(this.key(id, 'version'))
    var c = this.counts(data.getString(this.key(id, 'counts')))
    var state = v === p.version ? `planted (${c[0]} giants, ${c[1]} understory, ${c[3] + c[4]} already standing, ${c[2]} skipped)` :
      `pending, tile ${data.getInt(this.key(id, 'piece'))}/${this.pieces(p).length} (${c[0]} giants, ${c[1]} understory so far)`
    return `forest ${id}: ${p.title}, r ${p.inner}-${p.outer} round ${p.centre[0]} ${p.centre[1]}, v${p.version} ${state}`
  }
}
