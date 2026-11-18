// priority: 70
// Two roads (design/architecture/paths-necro-artificer.md §0: R12 a system is not a chapter, R13 two roads, R14
// witnesses; WP-N1). Data: design/data/roads.toml → TtlData.roads. Commands: roads/commands.js.
//
// Every player path and every moral-choice event is a CHOICE (`<system>.<act>`, e.g. necro.raise) with a good and/or
// grey route and usually a dark shortcut. Taking the dark route always costs the same five things, in this order:
//   1. karma    Life 2 soul ledger `ttl.karma2.<axis>` (ints): karma.js scores Life 1 only (deeds since the Life 1 start,
//               judged at the Life 1 death), so a Life 2 deed cannot go to `ttl.karma.chaos`. The NEXT Life 1 judgement
//               adds ledger × [karma2] mult to its raw axes (TtlKarma.judge, `carry`) and then spends the ledger.
//   2. balance  TtlChronicle.note(server, 'dark_deed' | 'light_deed', player, {system, act, road, count, weight}) when the
//               World Chronicle (WP-W1) is loaded; at most [balance] *_cap_per_day notes a soul a day (O-C2).
//   3. rep      TtlRep.add per faction of the route's `rep`; `victim` goes to the faction the caller names.
//   4. renown   TtlRep.addRenown; a dark route only when witnessed (R14), a good one always (unless witnessed_only).
//   5. discord  one #story line (TtlDiscord.post), only the first time a soul takes that route of that choice.
// Life 1 never pays (the paths open in Life 2). R12: nothing here reads or writes a story, path or boss stage.
//
// Storage
//   player  ttl.karma2.<axis>   int, the Life 2 ledger (chaos, order, craft, faith) until the next Life 1 judgement
//           ttl.karma2.spent    JSON [{at, ledger}] ledgers already judged (newest last, max 10)
//           ttl.roads           JSON {counts: {"<id>.<road>": n}, firsts: {"<id>.<road>": epoch}, tide: {day, dark, light},
//                               last: <the last pay result>}
//   server  ttl.roads.log       ring (200) [{t, p, id, road, w}]
//
// PUBLIC API (other packages call these guarded with typeof; `player` is a ServerPlayer)
//   TtlRoads.register(id, def)                 add or replace a choice at runtime: def = {label, fair, good?, grey?, dark?},
//                                              each route a table with the roads.toml fields. Returns the def.
//   TtlRoads.choice(id) · ids()                a choice ({id, label, fair, good, grey, dark}) or null · every id
//   TtlRoads.check(player, id, road)           '' when the soul may take that route now, else the reason
//   TtlRoads.pay(server, player, opts)         take a route and pay it. opts = {system, act | id, road ('good'|'grey'|'dark'),
//                                              faction (the wronged faction for `victim`), costs (a route table that replaces
//                                              the TOML one), pos {x, y, z} + dim (default: the player), radius (witnesses),
//                                              reason}. Returns {ok, why, id, road, karma, balance, noted, chronicle, rep,
//                                              renown, witnesses, first, story}
//   TtlRoads.witnesses(server, player, radius, pos, dim)  {players: [names], npcs: n, total}
//   TtlRoads.ledger(player) {axis: n} · carry(player) {axis: n × mult} or null · spent(player) (karma.js only)
//   TtlRoads.taken(player, id, road) times taken · counts(player) · listen(fn(server, player, result, route))
// Listeners run after the five costs (e.g. WP-N3 adds the Church's Sense from `route.extra.sense` for necro.* dark routes).
const TtlRoads = {
  KEY: 'ttl.roads',
  LEDGER: 'ttl.karma2.',
  SPENT: 'ttl.karma2.spent',
  LOG: 'ttl.roads.log',
  ROUTES: ['good', 'grey', 'dark'],
  DAY_MS: 86400000,
  extra: {},
  listeners: [],

  conf() {
    return TtlData.roads || {}
  },

  // ---- choices -------------------------------------------------------------------------------------------------

  register(id, def) {
    var c = { id: String(id), label: String(def.label || id), fair: def.fair || (def.good ? 'good' : 'grey') }
    this.ROUTES.forEach(r => { if (def[r]) c[r] = def[r] })
    this.extra[c.id] = c
    return c
  },

  choice(id) {
    id = String(id)
    if (this.extra[id]) return this.extra[id]
    var list = this.conf().choice || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === id) return list[i]
    }
    return null
  },

  ids() {
    var out = (this.conf().choice || []).map(c => String(c.id))
    Object.keys(this.extra).forEach(id => { if (out.indexOf(id) < 0) out.push(id) })
    return out.sort()
  },

  listen(fn) {
    this.listeners.push(fn)
  },

  // ---- player state ----------------------------------------------------------------------------------------------

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY))
    var s = {}
    try {
      s = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] roads: ${player.username} ${this.KEY} unreadable, starting over: ${e}`)
    }
    s.counts = s.counts || {}
    s.firsts = s.firsts || {}
    s.tide = s.tide || { day: 0, dark: 0, light: 0 }
    return s
  },

  write(player, s) {
    player.persistentData.putString(this.KEY, JSON.stringify(s))
  },

  axes() {
    return (this.conf().karma2 || {}).axes || ['chaos', 'order', 'craft', 'faith']
  },

  ledger(player) {
    var out = {}
    var data = player.persistentData
    this.axes().forEach(a => { out[a] = Number(data.getInt(this.LEDGER + a)) })
    return out
  },

  // What the next Life 1 judgement adds to its raw axes, or null when the ledger is empty.
  carry(player) {
    var mult = Number((this.conf().karma2 || {}).mult)
    if (!(mult >= 0)) mult = 0.5
    var led = this.ledger(player)
    var out = null
    Object.keys(led).forEach(a => {
      if (!led[a]) return
      out = out || {}
      out[a] = led[a] * mult
    })
    return out
  },

  // The judgement used the ledger: archive it and start a new one.
  spent(player) {
    var data = player.persistentData
    var led = this.ledger(player)
    var hist = []
    try {
      hist = JSON.parse(String(data.getString(this.SPENT)) || '[]')
    } catch (e) {
      hist = []
    }
    hist.push({ at: Date.now(), ledger: led })
    while (hist.length > 10) hist.shift()
    data.putString(this.SPENT, JSON.stringify(hist))
    this.axes().forEach(a => data.remove(this.LEDGER + a))
    console.info(`[ttl] roads: ${player.username} karma ledger judged and spent (${JSON.stringify(led)})`)
  },

  counts(player) {
    return this.read(player).counts
  },

  taken(player, id, road) {
    return Number(this.read(player).counts[`${id}.${road}`] || 0)
  },

  clear(player) {
    var data = player.persistentData
    data.remove(this.KEY)
    data.remove(this.SPENT)
    this.axes().forEach(a => data.remove(this.LEDGER + a))
  },

  // ---- the world around the act ----------------------------------------------------------------------------------

  // R14: Life 2 players (not the actor) and NPCs tagged [witness] npc_tag within `radius` blocks of the act.
  witnesses(server, player, radius, pos, dim) {
    var conf = this.conf().witness || {}
    var r = Number(radius || conf.radius || 32)
    var d = String(dim || TtlLife.dimensionOf(player))
    var p = pos || { x: player.getX(), y: player.getY(), z: player.getZ() }
    var me = String(player.username)
    var names = []
    server.getPlayerList().getPlayers().forEach(o => {
      try {
        if (String(o.username) === me || TtlLife.phase(o) !== 'life2' || TtlLife.dimensionOf(o) !== d) return
        var dx = o.getX() - p.x
        var dy = o.getY() - p.y
        var dz = o.getZ() - p.z
        if (dx * dx + dy * dy + dz * dz <= r * r) names.push(String(o.username))
      } catch (e) {
        console.warn(`[ttl] roads: witness check of ${o.username} failed: ${e}`)
      }
    })
    var tag = String(conf.npc_tag || 'ttl.npc')
    var npcs = TtlCmd.run(server, `execute in ${d} positioned ${p.x} ${p.y} ${p.z} if entity @e[type=!minecraft:player,tag=${tag},distance=..${r}]`)
    return { players: names, npcs: npcs, total: names.length + npcs }
  },

  // The canon region's name at an overworld column, or [defaults] region.
  regionName(dim, x, z) {
    var fallback = String((this.conf().defaults || {}).region || 'the wilds')
    if (String(dim) !== 'minecraft:overworld') return fallback
    try {
      var grid = Java.loadClass('com.yasuke.ttl.world.CanonMap').grid()
      if (!grid) return fallback
      var ch = v => (typeof v === 'number' ? String.fromCharCode(v) : String(v))
      var cell = grid.charAt(Math.floor(x), Math.floor(z))
      if (ch(cell) === '.') cell = grid.ownerCell(Math.floor(x), Math.floor(z))
      var region = grid.region(cell)
      return region ? String(region.name()) : fallback
    } catch (e) {
      return fallback
    }
  },

  // ---- taking a route ------------------------------------------------------------------------------------------

  route(id, road, costs) {
    if (costs) return costs
    var c = this.choice(id)
    return c && c[road] ? c[road] : null
  },

  check(player, id, road) {
    if (this.ROUTES.indexOf(String(road)) < 0) return 'unknown road (good, grey or dark)'
    if (!this.choice(id)) return `unknown choice ${id}`
    if (!this.route(id, road)) return `${id} has no ${road} route`
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    return ''
  },

  pay(server, player, opts) {
    var id = String(opts.id || `${opts.system}.${opts.act}`)
    var road = String(opts.road || 'dark')
    var res = { ok: false, why: '', id: id, road: road, karma: {}, balance: 'none', noted: 0, chronicle: false, rep: {}, renown: 0, witnesses: 0, first: false, story: '' }
    var route = this.route(id, road, opts.costs)
    var why = opts.costs ? (TtlLife.phase(player) === 'life2' ? '' : 'life2only') : this.check(player, id, road)
    if (!why && !route) why = `${id} has no ${road} route`
    if (why) {
      res.why = why
      console.info(`[ttl] roads: ${player.username} cannot take ${id} ${road}: ${why}`)
      return res
    }
    var name = String(player.username)
    var reason = String(opts.reason || `${id} ${road}`)
    var dim = String(opts.dim || TtlLife.dimensionOf(player))
    var pos = opts.pos || { x: player.getX(), y: player.getY(), z: player.getZ() }
    var state = this.read(player)
    var self = this
    var conf = this.conf()

    // 1. karma: the Life 2 ledger.
    var data = player.persistentData
    this.axes().forEach(a => {
      var n = Math.round(Number(route[a] || 0))
      if (!n) return
      data.putInt(self.LEDGER + a, Number(data.getInt(self.LEDGER + a)) + n)
      res.karma[a] = n
    })

    // 2. balance: the World Chronicle, capped per soul and day.
    var kind = String(route.balance || 'none')
    if (kind === 'dark_deed' || kind === 'light_deed') {
      res.balance = kind
      var side = kind === 'dark_deed' ? 'dark' : 'light'
      var cap = Number((conf.balance || {})[`${side}_cap_per_day`])
      var day = Math.floor(Date.now() / this.DAY_MS)
      if (state.tide.day !== day) state.tide = { day: day, dark: 0, light: 0 }
      var times = Math.max(1, Number(route.times || 1))
      for (var i = 0; i < times; i++) {
        if (state.tide[side] >= cap) break
        state.tide[side]++
        res.noted++
        try {
          if (typeof TtlChronicle !== 'undefined' && typeof TtlChronicle.note === 'function') {
            TtlChronicle.note(server, kind, player, { system: id.split('.')[0], act: id, road: road, count: `roads.${road}.${id.split('.')[0]}`, weight: String(route.weight || kind) })
            res.chronicle = true
          }
        } catch (e) {
          console.error(`[ttl] roads: chronicle note for ${name} ${id} failed: ${e}`)
        }
      }
    }

    // 3. reputation, the route's fixed factions and the caller's wronged faction.
    var repAdd = (f, n) => {
      try {
        if (typeof TtlRep === 'undefined' || !n) return
        var v = TtlRep.add(server, player, String(f), Number(n), reason)
        if (v !== null && v !== undefined) res.rep[String(f)] = v
      } catch (e) {
        console.error(`[ttl] roads: rep ${f} for ${name} failed: ${e}`)
      }
    }
    var rep = route.rep || {}
    Object.keys(rep).forEach(f => repAdd(f, rep[f]))
    if (route.victim && opts.faction) repAdd(opts.faction, route.victim)

    // 4. renown, with the witness rule.
    var seen = { players: [], npcs: 0, total: 0 }
    try {
      seen = this.witnesses(server, player, opts.radius, pos, dim)
    } catch (e) {
      console.error(`[ttl] roads: witness check for ${name} failed, nobody saw it: ${e}`)
    }
    res.witnesses = seen.total
    var renown = Number(route.renown || 0)
    var onlySeen = route.witnessed_only !== undefined ? !!route.witnessed_only : road === 'dark'
    if (renown && (!onlySeen || seen.total > 0)) {
      try {
        if (typeof TtlRep !== 'undefined') {
          TtlRep.addRenown(server, player, renown, reason)
          res.renown = renown
        }
      } catch (e) {
        console.error(`[ttl] roads: renown for ${name} failed: ${e}`)
      }
    }

    // 5. the chronicle line in Discord: the first time this soul takes this route of this choice.
    var key = `${id}.${road}`
    if (!state.firsts[key]) {
      state.firsts[key] = Date.now()
      res.first = true
      if (route.story && (conf.discord || {}).enabled !== false) {
        res.story = String(route.story).replace('{region}', this.regionName(dim, pos.x, pos.z))
        try {
          if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, res.story)
        } catch (e) {
          console.warn(`[ttl] roads: discord line failed: ${e}`)
        }
      }
    }

    state.counts[key] = Number(state.counts[key] || 0) + 1
    res.ok = true
    state.last = res
    this.write(player, state)
    this.note(server, name, id, road, seen.total)
    console.info(`[ttl] roads: ${name} took ${id} ${road}: karma ${JSON.stringify(res.karma)} balance ${res.balance} x${res.noted} rep ${JSON.stringify(res.rep)} renown ${res.renown} (${seen.total} witnesses)${res.first ? ', first' : ''}`)
    this.listeners.forEach(fn => {
      try {
        fn(server, player, res, route)
      } catch (e) {
        console.error(`[ttl] roads: a listener failed on ${id} ${road}: ${e}`)
      }
    })
    return res
  },

  note(server, name, id, road, witnesses) {
    try {
      var data = server.persistentData
      var ring = []
      try {
        ring = JSON.parse(String(data.getString(this.LOG)) || '[]')
      } catch (e) {
        ring = []
      }
      ring.push({ t: Date.now(), p: name, id: id, road: road, w: witnesses })
      while (ring.length > 200) ring.shift()
      data.putString(this.LOG, JSON.stringify(ring))
    } catch (e) {
      console.warn(`[ttl] roads: log write failed: ${e}`)
    }
  },

  log(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.LOG)) || '[]')
    } catch (e) {
      return []
    }
  },

  // Plain lines for /ttl roads (a soul's own view: what it did, not the ledger's numbers).
  lines(player) {
    var s = this.read(player)
    var out = []
    var by = {}
    Object.keys(s.counts).forEach(k => {
      var parts = k.split('.')
      var road = parts.pop()
      var id = parts.join('.')
      by[id] = by[id] || {}
      by[id][road] = s.counts[k]
    })
    Object.keys(by).sort().forEach(id => {
      var c = this.choice(id)
      var label = c ? c.label : id
      out.push(`${label}: ${this.ROUTES.filter(r => by[id][r]).map(r => `${r} ${by[id][r]}`).join(', ')}`)
    })
    var led = this.ledger(player)
    var dark = Number(led.chaos || 0)
    out.push(dark > 0 ? 'Your soul carries the weight of its shortcuts into the next life.' : 'Your soul carries no shortcut into the next life.')
    return out
  }
}
