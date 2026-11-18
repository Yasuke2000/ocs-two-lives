// priority: 69
// The necromancer's tomb, built by the player (owner decision 18/11/2026: O-N2 changed, no placed blueprints; WP-N2
// recognition, WP-N4 adds the visitor boss bar, the aura hall and tomb challenges on top of this API).
// Data: design/data/necro.toml [sanctum] and [[sanctum.tier]] → TtlData.necro.sanctum.
//
// The Bone Altar is the core. A check floods the air (ids in [sanctum] air) outward from the altar's air neighbours inside a
// box of scan_radius × scan_height around it. The room is ENCLOSED when the flood never needs a cell outside the box and
// stays under max_air cells. Every non-air block the flood touches (walls, floor, ceiling, furniture, the altar) is counted
// once by id. A tier holds when the air volume reaches its min_air and each `need` ({label, match [ids, * wildcards], n})
// is met; the best tier whose `rank` the owner has is the tomb (a grander build than the rank shows as `locked`). Niches =
// how many legionnaires may sleep there (necro/legion.js stow). Cheap and on demand: a forced check at most every
// cooldown_seconds per soul, results cached cache_minutes; nothing runs per tick.
//
// Storage: server `ttl.necro.sanctums` JSON {altarKey: {tier, name, locked, air, open, why, missing, at, rank}}.
// PUBLIC API
//   TtlSanctum.check(server, altarKey, player, force)   the result above (player = the owner, for the rank; null = cached rank)
//   TtlSanctum.cached(server, altarKey) · niches(server, altarKey) · forget(server, altarKey)
//   TtlSanctum.best(server, ownerUuid)                    the best cached tier result among the soul's altars, or null
//   TtlSanctum.lines(result)                              what a player reads
const TtlSanctum = {
  KEY: 'ttl.necro.sanctums',
  cls: undefined,
  ids: {},
  globs: {},
  lastCheck: {},

  conf() {
    return (TtlData.necro && TtlData.necro.sanctum) || {}
  },

  tiers() {
    return this.conf().tier || []
  },

  tier(id) {
    var list = this.tiers()
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(id)) return list[i]
    }
    return null
  },

  java() {
    if (this.cls === undefined) {
      try {
        this.cls = {
          pos: Java.loadClass('net.minecraft.core.BlockPos$MutableBlockPos'),
          reg: Java.loadClass('net.minecraft.core.registries.BuiltInRegistries')
        }
      } catch (e) {
        console.error(`[ttl] sanctum: block classes not reachable, tombs are not recognised: ${e}`)
        this.cls = null
      }
    }
    return this.cls
  },

  // Block id of a state, cached by the block's description id.
  idOf(state) {
    var block = state.getBlock()
    var d = String(block.getDescriptionId())
    var id = this.ids[d]
    if (id === undefined) {
      id = String(this.java().reg.BLOCK.getKey(block))
      this.ids[d] = id
    }
    return id
  },

  glob(pattern) {
    var re = this.globs[pattern]
    if (!re) {
      re = new RegExp(`^${String(pattern).replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*')}$`)
      this.globs[pattern] = re
    }
    return re
  },

  // Flood the air from the altar. {air, open, big, counts {id: n}, leak {x, y, z}}.
  scan(level, ax, ay, az) {
    var c = this.conf()
    var R = Math.max(2, Number(c.scan_radius || 16))
    var H = Math.max(2, Number(c.scan_height || 10))
    var MAX = Math.max(10, Number(c.max_air || 3000))
    var airIds = (c.air || ['minecraft:air', 'minecraft:cave_air']).map(String)
    var j = this.java()
    var pos = new j.pos()
    var setPos = (x, y, z) => pos['set(int,int,int)'](x, y, z)
    var W = 2 * R + 1
    var HH = 2 * H + 1
    var key = (x, y, z) => ((x - ax + R) * HH + (y - ay + H)) * W + (z - az + R)
    var seen = {}
    var counts = {}
    var out = { air: 0, open: false, big: false, counts: counts, leak: null }
    var stack = []
    var self = this
    var visit = (x, y, z) => {
      if (Math.abs(x - ax) > R || Math.abs(y - ay) > H || Math.abs(z - az) > R) {
        out.open = true
        if (!out.leak) out.leak = { x: x, y: y, z: z }
        return
      }
      var k = key(x, y, z)
      if (seen[k]) return
      seen[k] = 1
      setPos(x, y, z)
      var state = level.getBlockState(pos)
      var id = self.idOf(state)
      if (airIds.indexOf(id) >= 0) {
        out.air++
        stack.push(x, y, z)
      } else {
        counts[id] = (counts[id] || 0) + 1
      }
    }
    seen[key(ax, ay, az)] = 1
    setPos(ax, ay, az)
    var core = this.idOf(level.getBlockState(pos))
    counts[core] = (counts[core] || 0) + 1
    var dirs = [1, 0, 0, -1, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 1, 0, 0, -1]
    for (var d = 0; d < 18; d += 3) visit(ax + dirs[d], ay + dirs[d + 1], az + dirs[d + 2])
    while (stack.length > 0 && !out.open) {
      if (out.air > MAX) {
        out.big = true
        out.open = true
        break
      }
      var z = stack.pop()
      var y = stack.pop()
      var x = stack.pop()
      for (var i = 0; i < 18 && !out.open; i += 3) visit(x + dirs[i], y + dirs[i + 1], z + dirs[i + 2])
    }
    return out
  },

  // How many touched blocks match a need's patterns.
  have(counts, need) {
    var self = this
    var n = 0
    var pats = (need.match || []).map(String)
    Object.keys(counts).forEach(id => {
      if (pats.some(p => self.glob(p).test(id))) n += counts[id]
    })
    return n
  },

  // The tier a scan reaches, and for a soul of `rank`. {tier, name, locked, niches, missing [text], next}.
  judge(scan, rank) {
    var self = this
    var res = { tier: 'none', name: 'none', locked: '', niches: Number(this.conf().bare_niches || 2), missing: [], next: '' }
    if (scan.open) {
      res.why = scan.big ? 'big' : 'open'
      var first = this.tiers()[0]
      res.next = first ? String(first.id) : ''
      return res
    }
    res.why = 'ok'
    var tiers = this.tiers()
    for (var i = 0; i < tiers.length; i++) {
      var t = tiers[i]
      var miss = []
      if (scan.air < Number(t.min_air || 0)) miss.push(`more room (${scan.air}/${t.min_air} air)`)
      ;(t.need || []).forEach(nd => {
        var got = self.have(scan.counts, nd)
        if (got < Number(nd.n || 1)) miss.push(`${nd.label} ${got}/${nd.n}`)
      })
      if (miss.length > 0) {
        res.next = String(t.id)
        res.missing = miss
        break
      }
      if (Number(t.rank || 1) > rank) {
        res.locked = String(t.id)
        res.next = String(t.id)
        res.missing = [`rank ${t.rank} to claim it (you are rank ${rank})`]
        break
      }
      res.tier = String(t.id)
      res.name = String(t.name || t.id)
      res.niches = Number(t.niches || res.niches)
    }
    if (res.tier === 'none' && res.why === 'ok') res.why = 'short'
    return res
  },

  all(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.KEY)) || '{}')
    } catch (e) {
      return {}
    }
  },

  saveAll(server, all) {
    server.persistentData.putString(this.KEY, JSON.stringify(all))
  },

  cached(server, key) {
    var r = this.all(server)[String(key)]
    return r || null
  },

  forget(server, key) {
    var all = this.all(server)
    if (!all[key]) return
    delete all[key]
    this.saveAll(server, all)
  },

  niches(server, key) {
    var r = this.cached(server, key)
    var bare = Number(this.conf().bare_niches || 2)
    return r && r.tier !== 'none' ? Number(r.niches || bare) : bare
  },

  best(server, uuid) {
    if (typeof TtlLegion === 'undefined') return null
    var self = this
    var order = this.tiers().map(t => String(t.id))
    var best = null
    TtlLegion.altarsOf(server, uuid).forEach(a => {
      var r = self.cached(server, a.key)
      if (r && r.tier !== 'none' && (!best || order.indexOf(r.tier) > order.indexOf(best.tier))) best = r
    })
    return best
  },

  // Check the tomb around an altar. `force` skips the cache (a soul may force once every cooldown_seconds; 'test' always).
  check(server, key, player, force) {
    var c = this.conf()
    var cached = this.cached(server, key)
    var now = Date.now()
    var fresh = cached && now - Number(cached.at || 0) < Number(c.cache_minutes || 10) * 60000
    if (cached && fresh && !force) return cached
    if (player && force && force !== 'test') {
      var u = TtlLife.uuid(player)
      var wait = Number(c.cooldown_seconds || 5) * 1000
      if (this.lastCheck[u] && now - this.lastCheck[u] < wait && cached) return cached
      this.lastCheck[u] = now
    }
    if (!this.java()) return cached || { tier: 'none', name: 'none', why: 'unavailable', missing: [], at: now }
    var a = TtlLegion.parseKey(key)
    var level = server.getLevel(a.dim)
    if (!level) return { tier: 'none', name: 'none', why: 'nolevel', missing: [], at: now }
    var rank = player ? TtlLegion.rank(player) : Number((cached || {}).rank || 0)
    var t0 = Date.now()
    var scan = this.scan(level, a.x, a.y, a.z)
    var res = this.judge(scan, rank)
    res.air = scan.air
    res.open = scan.open
    res.leak = scan.leak
    res.at = now
    res.rank = rank
    res.ms = Date.now() - t0
    var all = this.all(server)
    all[key] = res
    this.saveAll(server, all)
    console.info(`[ttl] sanctum: ${key} is ${res.tier} (${res.why}, ${scan.air} air, rank ${rank}, ${res.ms} ms)${res.locked ? `, ${res.locked} locked` : ''}`)
    if (player && res.tier !== 'none') this.firstTier(server, player, key, res)
    return res
  },

  // The first time a soul's tomb reaches a tier: rank points (once per tier and soul), a chronicle note, and one #story
  // line the first time the server sees that tier at all.
  firstTier(server, player, key, res) {
    var uuid = TtlLife.uuid(player)
    var rec = TtlLegion.record(server, uuid)
    var order = this.tiers().map(t => String(t.id))
    var reached = order.slice(0, order.indexOf(res.tier) + 1).filter(id => !rec.tiers[id])
    if (reached.length === 0) return
    reached.forEach(id => { rec.tiers[id] = Date.now() })
    TtlLegion.save(server, uuid, rec)
    var self = this
    reached.forEach(id => {
      TtlLegion.points(server, player, 'tomb', `tomb ${id}`)
      try {
        if (typeof TtlChronicle !== 'undefined' && typeof TtlChronicle.note === 'function') TtlChronicle.note(server, 'necro_tomb', player, { count: `necro.tombs.${id}` })
      } catch (e) {
        console.error(`[ttl] sanctum: chronicle note failed: ${e}`)
      }
      var flag = `ttl.necro.first.${id}`
      var bot = typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(player.username)
      if (!bot && !server.persistentData.getBoolean(flag)) {
        server.persistentData.putBoolean(flag, true)
        var t = self.tier(id)
        var p = TtlLegion.parseKey(key)
        var region = 'the wilds'
        try {
          if (typeof TtlRoads !== 'undefined') region = TtlRoads.regionName(p.dim, p.x, p.z)
        } catch (e) {
          region = 'the wilds'
        }
        try {
          if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, `In ${region} the dead have a ${t ? t.name : id} of their own.`)
        } catch (e) {
          console.warn(`[ttl] sanctum: discord line failed: ${e}`)
        }
      }
    })
    player.tell(Text.darkPurple(`Your tomb is recognised: ${res.name}. ${res.niches} niches for the sleeping dead.`))
  },

  lines(res) {
    var out = []
    if (!res) return ['No tomb has been checked here yet.']
    if (res.why === 'open') out.push(`Not a tomb yet: the air leaks out${res.leak ? ` near ${res.leak.x} ${res.leak.y} ${res.leak.z}` : ''}. Close it with walls, a floor, a roof and doors.`)
    else if (res.why === 'big') out.push('Not a tomb: the space around the altar is too large to be one room. Wall it off.')
    else if (res.tier === 'none') out.push(`A closed room (${res.air} air), not a tomb yet.`)
    else out.push(`Your tomb: ${res.name} (${res.air} air), ${res.niches} niches for the sleeping dead.`)
    if (res.next && (res.missing || []).length > 0) {
      var t = this.tier(res.next)
      out.push(`${res.locked ? 'Built, but locked' : 'Next'}: ${t ? t.name : res.next} needs ${res.missing.join(', ')}.`)
    }
    return out
  }
}
