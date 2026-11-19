// Trade roads between the canon nations (design/data/trade_roads/roads.toml; the path and its height profile planned
// offline by tools/lerfing/trade_roads.py, data in generated/placements.js). Tempest -> Dwargon now; Tempest -> Blumund
// and the others are a second [id] + plan later. Each road is laid once (persistentData ttl.troad.<id>.version =
// its version) by the runner in life/works.js, one stretch of STRETCH blocks at a time (chunk tickets over the stretch).
//
// The road: every column within `half` of the centre line (columns(): the polyline walked one block of arc at a time,
// mirrored by tools/lerfing/trade_roads.py rasterize()) takes the profile's height y of its arc sample:
// - land: the gap between the ground and y filled (dirt, stone deeper; small dips and ponds), the surface block at y
//   (a weighted mix per column: dirt path, gravel, coarse dirt, cobble in Jura; cobble, stone, andesite, tuff, gravel on
//   the stone stretch below Dwargon), everything from y + 1 up to y + 4 (or the cut, at most CUT) cleared: grass,
//   flowers, saplings, logs and leaves, without drops (life/drops.js clearColumn: what leaned on the cleared blocks goes
//   too, a gravel block left over a cut turns to stone, a gravel surface over a gap gets dirt under it). A column whose neighbour along the road is one higher gets a slab, so the road
//   walks without jumping;
// - bridges (the planner's wet runs): a plank deck at y (2 above the water), fence railings on the edge columns,
//   log pillars down to the bed every 5 blocks, the water under the deck left as it is;
// - a fence post with a lantern every lantern_every blocks beside the road, alternating sides.
// Columns inside Tempest's worked area, Dwargon's box (not its margin: the road meets Dwargon's own road there), a placed
// build or landmark or one of Lerfing's keepouts are left alone.
// Log: `[ttl] trade road <id> laid: N columns, B bridge columns, L lanterns, S kept clear (version V)`.
const TtlTradeRoads = {
  STRETCH: 48,
  CLEAR: 4,
  CUT: 16,
  SLAB: { jura: 'minecraft:cobblestone_slab', stone: 'minecraft:andesite_slab' },
  POST: 'minecraft:spruce_fence',
  LANTERN: 'minecraft:lantern',

  all() {
    return TtlWorks.data().roads || {}
  },

  key(id, k) {
    return `ttl.troad.${id}.${k}`
  },

  forget(server, id) {
    var self = this
    ;['version', 'pversion', 'piece', 'counts'].forEach(k => server.persistentData.remove(self.key(id, k)))
  },

  // Positions every block of arc length along the polyline (trade_roads.py arc_samples).
  arcSamples(points) {
    var out = []
    var carry = 0
    for (var k = 0; k + 1 < points.length; k++) {
      var ax = points[k][0]
      var az = points[k][1]
      var bx = points[k + 1][0]
      var bz = points[k + 1][1]
      var seg = Math.sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az))
      var s = carry
      while (s < seg - 1e-9) {
        var f = s / seg
        out.push([ax + (bx - ax) * f, az + (bz - az) * f])
        s += 1
      }
      carry = s - seg
    }
    out.push([points[points.length - 1][0], points[points.length - 1][1]])
    return out
  },

  // {"x,z": [y, arc index, |offset|]} for every paved column (trade_roads.py rasterize).
  columns(r) {
    var pts = r.points
    var samples = this.arcSamples(pts)
    var dirs = []
    var lens = []
    for (var k = 0; k + 1 < pts.length; k++) {
      var dx = pts[k + 1][0] - pts[k][0]
      var dz = pts[k + 1][1] - pts[k][1]
      var L = Math.sqrt(dx * dx + dz * dz)
      lens.push(L)
      dirs.push([dx / (L || 1), dz / (L || 1)])
    }
    var seg = 0
    var acc = 0
    var cols = {}
    var steps = Math.floor(r.half * 2) * 2
    for (var i = 0; i < samples.length; i++) {
      while (seg < lens.length - 1 && i >= acc + lens[seg] - 1e-9) {
        acc += lens[seg]
        seg++
      }
      var d = dirs[seg]
      var nx = -d[1]
      var nz = d[0]
      var y = r.profile[Math.min(i, r.profile.length - 1)]
      for (var h = 0; h < 2; h++) {
        var hi = h * 0.5
        if (hi && i === samples.length - 1) continue
        var cx = samples[i][0] + d[0] * hi
        var cz = samples[i][1] + d[1] * hi
        for (var s = -steps; s <= steps; s++) {
          var o = s * r.half / steps
          var x = Math.floor(cx + nx * o + 0.5)
          var z = Math.floor(cz + nz * o + 0.5)
          var key = x + ',' + z
          var cur = cols[key]
          if (cur === undefined || Math.abs(o) < cur[2]) cols[key] = [y, i, Math.abs(o)]
        }
      }
    }
    return cols
  },

  // Lantern posts [x, z, arc] (works_preview.py lanterns()).
  lanterns(r) {
    var every = r.lantern_every
    if (!every) return []
    var samples = this.arcSamples(r.points)
    var out = []
    var side = 1
    for (var i = every; i < samples.length - Math.floor(every / 2); i += every) {
      if (r.bridges.some(b => b[0] - 2 <= i && i <= b[1] + 2)) continue
      var a = samples[Math.max(0, i - 1)]
      var b = samples[Math.min(samples.length - 1, i + 1)]
      var L = Math.sqrt((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1])) || 1
      var nx = -(b[1] - a[1]) / L
      var nz = (b[0] - a[0]) / L
      var off = r.half + 1.5
      out.push([Math.floor(samples[i][0] + nx * off * side + 0.5), Math.floor(samples[i][1] + nz * off * side + 0.5), i])
      side = -side
    }
    return out
  },

  centre(r, arc) {
    var samples = this.arcSamples(r.points)
    var i = Math.max(0, Math.min(samples.length - 1, arc))
    return { i: i, x: Math.floor(samples[i][0] + 0.5), z: Math.floor(samples[i][1] + 0.5), y: r.profile[Math.min(i, r.profile.length - 1)] }
  },

  stone(r, x, z) {
    return r.stone_from.some(b => x >= b[0] && x <= b[2] && z >= b[1] && z <= b[3])
  },

  // The weighted surface block of a column (deterministic per x, z).
  material(r, x, z) {
    var table = this.stone(r, x, z) ? r.stone : r.surface
    var keys = Object.keys(table).sort()
    var total = 0
    keys.forEach(k => { total += table[k] })
    var h = ((x * 73856093) ^ (z * 19349663) ^ 0x5bd1e995) >>> 0
    var v = h % total
    for (var i = 0; i < keys.length; i++) {
      v -= table[keys[i]]
      if (v < 0) return keys[i]
    }
    return keys[keys.length - 1]
  },

  bridgeAt(r, i) {
    return r.bridges.some(b => i >= b[0] && i <= b[1])
  },

  // Commands for one column; returns 'road', 'bridge' or 'kept'.
  lay(server, hm, r, kept, x, z, c) {
    var y = c[0]
    var i = c[1]
    var o = c[2]
    if (TtlWorks.inBox(kept, x, z, 0)) return 'kept'
    var run = cmd => TtlWorks.run(server, cmd)
    if (this.bridgeAt(r, i)) {
      this.clear(server, x, y + 1, y + this.CLEAR, z)
      run(`setblock ${x} ${y} ${z} ${r.bridge.deck}`)
      if (o > r.half - 0.6) {
        run(`setblock ${x} ${y + 1} ${z} ${r.bridge.railing}`)
        if (i % 5 === 0) {
          var bed = hm.floor(x, z)
          if (bed !== null && bed < y) run(`fill ${x} ${bed} ${z} ${x} ${y - 1} ${z} ${r.bridge.pillar}`)
        }
      }
      return 'bridge'
    }
    var g = hm.ground(x, z)
    var base = hm.wet(x, z) ? hm.floor(x, z) : g
    if (base !== null && base <= y - 1) {
      var dirtFrom = Math.max(base, y - 3)
      if (dirtFrom > base) run(`fill ${x} ${base} ${z} ${x} ${dirtFrom - 1} ${z} minecraft:stone`)
      run(`fill ${x} ${dirtFrom} ${z} ${x} ${y - 1} ${z} minecraft:dirt`)
    }
    var top = Math.min(y + this.CUT, Math.max(y + this.CLEAR, g === null ? y : g - 1))
    this.clear(server, x, y + 1, top, z)
    run(`setblock ${x} ${y} ${z} ${this.material(r, x, z)}`)
    if (typeof TtlDrops !== 'undefined') TtlDrops.underpin(server, TtlLife.OVERWORLD, x, y, z)
    var p = r.profile
    if ((i + 1 < p.length && p[i + 1] > y) || (i > 0 && p[i - 1] > y)) {
      run(`setblock ${x} ${y + 1} ${z} ${this.stone(r, x, z) ? this.SLAB.stone : this.SLAB.jura}[type=bottom]`)
    }
    return 'road'
  },

  // The column x z from y0 to y1 to air without drops (life/drops.js: nothing that leaned on it pops off, gravel left
  // over the cut turns to stone); the plain `fill` where TtlDrops is not loaded (tests/works.js).
  clear(server, x, y0, y1, z) {
    if (y1 < y0) return
    if (typeof TtlDrops !== 'undefined' && TtlDrops.clearColumn(server, TtlLife.OVERWORLD, x, y0, y1, z) >= 0) return
    TtlWorks.run(server, `fill ${x} ${y0} ${z} ${x} ${y1} ${z} minecraft:air`)
  },

  post(server, hm, kept, x, z) {
    if (TtlWorks.inBox(kept, x, z, 0)) return false
    var g = hm.ground(x, z)
    if (g === null || hm.wet(x, z)) return false
    TtlWorks.run(server, `fill ${x} ${g} ${z} ${x} ${g + 1} ${z} ${this.POST}`)
    TtlWorks.run(server, `setblock ${x} ${g + 2} ${z} ${this.LANTERN}`)
    return true
  },

  pieces(r) {
    var cols = this.columns(r)
    var lan = this.lanterns(r)
    var out = []
    var self = this
    var get = i => {
      var k = Math.floor(i / self.STRETCH)
      if (!out[k]) out[k] = { cols: [], posts: [], x0: 1e9, z0: 1e9, x1: -1e9, z1: -1e9 }
      return out[k]
    }
    var grow = (pc, x, z) => {
      pc.x0 = Math.min(pc.x0, x - 1)
      pc.z0 = Math.min(pc.z0, z - 1)
      pc.x1 = Math.max(pc.x1, x + 1)
      pc.z1 = Math.max(pc.z1, z + 1)
    }
    Object.keys(cols).sort().forEach(k => {
      var c = cols[k]
      var xz = k.split(',').map(Number)
      var pc = get(c[1])
      pc.cols.push([xz[0], xz[1], c])
      grow(pc, xz[0], xz[1])
    })
    lan.forEach(l => {
      var pc = get(l[2])
      pc.posts.push(l)
      grow(pc, l[0], l[1])
    })
    return out.filter(pc => pc).map(pc => ({ area: { x0: pc.x0, z0: pc.z0, x1: pc.x1, z1: pc.z1 }, cols: pc.cols, posts: pc.posts }))
  },

  work(server, id, force, done) {
    var r = this.all()[id]
    var data = server.persistentData
    if (!force && data.getInt(this.key(id, 'version')) === r.version) {
      done()
      return
    }
    if (force) this.forget(server, id)
    TtlWorks.begin(server, this, id, r.version)
    var pieces = this.pieces(r)
    var kept = TtlWorks.kept(server, true)
    var counts = TtlWorks.ints(data.getString(this.key(id, 'counts'))) || [0, 0, 0, 0]
    var self = this
    var start = data.getInt(this.key(id, 'piece'))
    console.info(`[ttl] trade road ${id}: laying ${r.length} blocks in ${pieces.length} stretches` + (start ? ` (resuming at ${start})` : ''))
    var next = i => {
      if (i >= pieces.length) {
        data.putInt(self.key(id, 'version'), r.version)
        console.info(`[ttl] trade road ${id} laid: ${counts[0]} columns, ${counts[1]} bridge columns, ${counts[2]} lanterns, ${counts[3]} kept clear (version ${r.version})`)
        done()
        return
      }
      var pc = pieces[i]
      TtlWorks.withArea(server, pc.area, `trade road ${id} stretch ${i + 1}/${pieces.length}`, (hm, release) => {
        var fns = []
        pc.cols.forEach(c => fns.push(() => {
          var what = self.lay(server, hm, r, kept, c[0], c[1], c[2])
          counts[what === 'road' ? 0 : what === 'bridge' ? 1 : 3]++
        }))
        pc.posts.forEach(l => fns.push(() => {
          if (self.post(server, hm, kept, l[0], l[1])) counts[2]++
        }))
        TtlWorks.budgeted(server, fns, () => {
          release()
          data.putInt(self.key(id, 'piece'), i + 1)
          data.putString(self.key(id, 'counts'), counts.join(' '))
          server.scheduleInTicks(TtlWorks.GAP, () => next(i + 1))
        })
      }, why => {
        console.error(`[ttl] trade road ${id}: stretch ${i + 1}/${pieces.length} skipped: ${why}; the next boot tries it again`)
        done()
      })
    }
    next(start)
  },

  // null when the centre column of arc sample `arc` carries the road (or lies in a kept box), else why not.
  checkSurface(server, id, arc) {
    var r = this.all()[id]
    var c = this.centre(r, arc)
    if (TtlWorks.inBox(TtlWorks.kept(server, true), c.x, c.z, 0)) return null
    var level = server.getLevel(TtlLife.OVERWORLD)
    var at = String(level.getBlock(c.x, c.y, c.z).id)
    var ok = Object.keys(r.surface).concat(Object.keys(r.stone), [r.bridge.deck, 'minecraft:dirt'])
    if (ok.indexOf(at) < 0) return `expected the road surface at ${c.x} ${c.y} ${c.z} (arc ${c.i}), found ${at}`
    var above = String(level.getBlock(c.x, c.y + 1, c.z).id)
    if (above !== 'minecraft:air' && above.indexOf('_slab') < 0 && above !== r.bridge.railing) return `expected the road clear above ${c.x} ${c.y} ${c.z}, found ${above}`
    return null
  },

  describe(server, id) {
    var r = this.all()[id]
    var data = server.persistentData
    var v = data.getInt(this.key(id, 'version'))
    var c = TtlWorks.ints(data.getString(this.key(id, 'counts'))) || [0, 0, 0, 0]
    var state = v === r.version ? `laid (${c[0]} columns, ${c[1]} bridge, ${c[2]} lanterns, ${c[3]} kept clear)` :
      `pending, stretch ${data.getInt(this.key(id, 'piece'))}/${this.pieces(r).length}`
    var a = r.points[0]
    var b = r.points[r.points.length - 1]
    return `road ${id}: ${r.title}, ${r.length} blocks ${a[0]} ${a[1]} -> ${b[0]} ${b[1]}, v${r.version} ${state}`
  }
}
