// priority: 72
// Event director (design/architecture/sprint3-4.md S6): a scheduler that fires world events with a title, a sound, a
// chat line, an optional Great Sage clip and a Discord #story line. Schedule, announcement and declarative action of
// each event live in design/data/events.toml (TtlData.events); this file is the engine.
//
// Adding an event (storm, Blood Moon, Calamity, Labyrinth: WP8). In a file with `// priority: 70` (below this one, so
// TtlEvents exists) call, at the top level of the script:
//   TtlEvents.register({
//     id: 'magicule_storm',                    // same id as the [[event]] in events.toml (optional: no [[event]] = manual only)
//     start(server, ctx) { ... },              // required unless the TOML action says it all. Return:
//                                              //   false          -> could not start (retried inside the window, manual fire says so)
//                                              //   an object      -> kept as ctx.data (JSON-able). Special keys: region (name for
//                                              //                     logs/chat {region}), player ({player}), audience (array of player
//                                              //                     names: only they see the announcement), any other key = chat variable
//                                              //   anything else  -> started
//     end(server, ctx, why) { ... },           // optional; why = 'expired' | 'manual' | 'forced'
//     resume(server, ctx) { ... },             // optional; server restarted while the event was active (re-assert what a restart loses)
//     canStart(server) { return null },        // optional; a reason string refuses this start (retried like a failed start)
//     poll(server, ctx) { ... }                // optional; runs every [director] poll_ticks, active or not (ctx is null when idle).
//                                              // This is the fallback for listeners that cannot be registered (Enhanced Celestials'
//                                              // EnhancedCelestialsEvents.registerLunarEventChanged is a verify item): poll the
//                                              // overworld's lunar state here and call TtlEvents.fire(server, 'blood_moon', {...}).
//   })
// Any other key (every, announce, duration_minutes, ...) overrides the TOML value of the same name. ctx = {id, startedAt,
// endsAt, data, manual}. Event code never needs to touch the schedule: TtlEvents.fire / end / isActive / update are the API.
//
// Server persistentData (JSON strings): ttl.events.next {id: epoch ms}, ttl.events.active {id: {s, e, d, g, gr, m}},
// ttl.events.last {id: {t, n}} (last start, count), ttl.events.hold {id: epoch ms} (retry not before), ttl.events.day
// {k, n, t} (capped starts today and the last one), ttl.events.loop (loop stamp, see boot). Player: ttl.events.muted.
const TtlEvents = {
  HOUR: 3600000,
  DAY: 86400000,
  js: {},
  cache: null,
  ID: /^[a-z0-9_]+$/,
  RULE: /^[A-Za-z][A-Za-z0-9_]*$/,
  VALUE: /^[A-Za-z0-9_.-]+$/,

  // ---- configuration ----------------------------------------------------------------------------------------------

  num(v, dflt) {
    var n = Number(v)
    return v !== undefined && v !== null && v !== '' && isFinite(n) ? n : dflt
  },

  dir() {
    var d = (typeof TtlData !== 'undefined' && TtlData.events && TtlData.events.director) || {}
    return {
      loop_ticks: this.num(d.loop_ticks, 1200),
      poll_ticks: this.num(d.poll_ticks, 100),
      window_hours: this.num(d.window_hours, 6),
      retry_minutes: this.num(d.retry_minutes, 10),
      min_gap_minutes: this.num(d.min_gap_minutes, 30),
      max_per_day: this.num(d.max_per_day, 3),
      max_active: this.num(d.max_active, 3),
      story: d.story !== false
    }
  },

  // The registered object merged over the [[event]] of the same id; announce and action merge one level deeper.
  merge(base, over) {
    var out = {}
    Object.keys(base || {}).forEach(k => { out[k] = base[k] })
    Object.keys(over || {}).forEach(k => {
      var v = over[k]
      if ((k === 'announce' || k === 'action') && v && typeof v === 'object' && out[k] && typeof out[k] === 'object') {
        var m = {}
        Object.keys(out[k]).forEach(j => { m[j] = out[k][j] })
        Object.keys(v).forEach(j => { m[j] = v[j] })
        out[k] = m
      } else {
        out[k] = v
      }
    })
    return out
  },

  all() {
    if (this.cache) return this.cache
    var out = {}
    var self = this
    var rows = (typeof TtlData !== 'undefined' && TtlData.events && TtlData.events.event) || []
    rows.forEach(e => { out[e.id] = self.merge(e, {}) })
    Object.keys(this.js).forEach(id => { out[id] = self.merge(out[id] || { id: id }, self.js[id]) })
    this.cache = out
    return out
  },

  get(id) {
    return this.all()[String(id)] || null
  },

  ids() {
    return Object.keys(this.all()).sort()
  },

  label(def) {
    return String(def.label || def.id)
  },

  // See the header. Returns false (and logs) for a bad spec; a second registration of an id replaces the first.
  register(spec) {
    if (!spec || !this.ID.test(String(spec.id))) {
      console.error(`[ttl] events: register needs an id matching [a-z0-9_]+ (got ${spec && spec.id})`)
      return false
    }
    this.js[String(spec.id)] = spec
    this.cache = null
    console.info(`[ttl] events: registered ${spec.id}`)
    return true
  },

  registered(id) {
    return !!this.js[String(id)]
  },

  // ---- Europe/Brussels wall clock (same rule as discord/hall.js: CEST from the last Sunday of March to October) --------

  offsetHours(ms) {
    var y = new Date(ms).getUTCFullYear()
    var lastSunday = month => {
      var last = new Date(Date.UTC(y, month + 1, 0))
      return Date.UTC(y, month, last.getUTCDate() - last.getUTCDay(), 1)
    }
    return ms >= lastSunday(2) && ms < lastSunday(9) ? 2 : 1
  },

  local(ms) {
    var d = new Date(ms + this.offsetHours(ms) * this.HOUR)
    var pad = n => (n < 10 ? '0' : '') + n
    return {
      y: d.getUTCFullYear(), m: d.getUTCMonth(), d: d.getUTCDate(), h: d.getUTCHours(), wd: d.getUTCDay(),
      key: `${d.getUTCFullYear()}-${d.getUTCMonth() + 1}-${d.getUTCDate()}`,
      text: `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`
    }
  },

  // Wall clock (month 0-11; day may overflow) to epoch ms.
  utc(y, m, d, h) {
    var guess = Date.UTC(y, m, d, h)
    return guess - this.offsetHours(guess - 2 * this.HOUR) * this.HOUR
  },

  // ---- schedule -----------------------------------------------------------------------------------------------------

  jitter(def) {
    return Math.random() * this.num(def.jitter_hours, 0) * this.HOUR
  },

  // The start after `t` (a start time), keeping the phase of the schedule.
  step(def, t) {
    var every = def.every || {}
    if (every.hours) return t + every.hours * this.HOUR + this.jitter(def)
    var l = this.local(t)
    return this.utc(l.y, l.m, l.d + every.days, this.num(def.at_hour, 12)) + this.jitter(def)
  },

  first(def, now) {
    var every = def.every || {}
    if (every.hours) return now + every.hours * this.HOUR + this.jitter(def)
    var at = this.num(def.at_hour, 12)
    var l = this.local(now)
    var t = this.utc(l.y, l.m, l.d, at)
    if (t <= now) t = this.utc(l.y, l.m, l.d + 1, at)
    return t + this.num(def.delay_days, 0) * this.DAY + this.jitter(def)
  },

  after(def, base, now) {
    var t = this.step(def, base)
    for (var i = 0; t <= now && i < 1000; i++) t = this.step(def, t)
    return t
  },

  read(server, key, empty) {
    try {
      var raw = String(server.persistentData.getString(key))
      return raw ? JSON.parse(raw) : empty
    } catch (e) {
      console.warn(`[ttl] events: ${key} unreadable, starting over (${e})`)
      return empty
    }
  },

  write(server, key, value) {
    server.persistentData.putString(key, JSON.stringify(value))
  },

  // Events with a schedule and no entry yet get their first start; entries of vanished events are dropped.
  ensure(server, now) {
    var next = this.read(server, 'ttl.events.next', {})
    var changed = false
    var self = this
    this.ids().forEach(id => {
      var def = self.get(id)
      var every = def.every
      if (next[id] === undefined && every && (every.days || every.hours)) {
        next[id] = self.first(def, now)
        changed = true
        console.info(`[ttl] events: ${id} scheduled for ${self.local(next[id]).text}`)
      }
    })
    Object.keys(next).forEach(id => {
      if (!self.get(id)) {
        delete next[id]
        changed = true
      }
    })
    if (changed) this.write(server, 'ttl.events.next', next)
    return next
  },

  // Test and ops hooks.
  due(server, id) {
    var def = this.get(id)
    if (!def) return false
    var next = this.read(server, 'ttl.events.next', {})
    next[def.id] = Date.now() - 1000
    this.write(server, 'ttl.events.next', next)
    var hold = this.read(server, 'ttl.events.hold', {})
    delete hold[def.id]
    this.write(server, 'ttl.events.hold', hold)
    return true
  },

  reschedule(server, id) {
    var def = this.get(id)
    if (!def) return false
    var next = this.read(server, 'ttl.events.next', {})
    delete next[def.id]
    this.write(server, 'ttl.events.next', next)
    this.ensure(server, Date.now())
    return true
  },

  scheduled(server, id) {
    return this.read(server, 'ttl.events.next', {})[String(id)] !== undefined
  },

  // Why a scheduled start must wait, or null. Manual fires skip all of this except "already active".
  blocked(server, def, now) {
    var d = this.dir()
    var active = this.read(server, 'ttl.events.active', {})
    if (active[def.id]) return 'already active'
    if (this.num(def.duration_minutes, 0) > 0 && Object.keys(active).length >= d.max_active) return `${d.max_active} events already running`
    if (server.getPlayerList().getPlayerCount() < 1) return 'nobody online'
    if (def.capped !== false) {
      var day = this.read(server, 'ttl.events.day', { k: '', n: 0, t: 0 })
      if (day.t && now - day.t < d.min_gap_minutes * 60000) return `less than ${d.min_gap_minutes} min after the previous event`
      if (day.k === this.local(now).key && day.n >= d.max_per_day) return `${d.max_per_day} events already today`
    }
    if (typeof def.canStart === 'function') {
      try {
        var why = def.canStart(server)
        if (why) return String(why)
      } catch (e) {
        console.error(`[ttl] events: ${def.id} canStart failed: ${e}`)
        return `canStart failed: ${e}`
      }
    }
    return null
  },

  // One scheduler pass (every loop_ticks, or /ttl events tick).
  tick(server) {
    var now = Date.now()
    var self = this
    this.expire(server, now)
    var next = this.ensure(server, now)
    var due = Object.keys(next).filter(id => next[id] <= now).sort((a, b) => next[a] - next[b])
    due.forEach(id => {
      try {
        self.runDue(server, id, next[id], now)
      } catch (e) {
        console.error(`[ttl] events: ${id} scheduler failed: ${e}`)
      }
    })
    try {
      if (typeof TtlFavor !== 'undefined') TtlFavor.track(server)
    } catch (e) {
      console.error(`[ttl] events: play-time tracking failed: ${e}`)
    }
  },

  settle(server, def, dueAt, now) {
    var next = this.read(server, 'ttl.events.next', {})
    if (def.every && (def.every.days || def.every.hours)) {
      next[def.id] = this.after(def, dueAt, now)
      console.info(`[ttl] events: ${def.id} next ${this.local(next[def.id]).text}`)
    } else {
      delete next[def.id]
    }
    this.write(server, 'ttl.events.next', next)
    var hold = this.read(server, 'ttl.events.hold', {})
    delete hold[def.id]
    this.write(server, 'ttl.events.hold', hold)
  },

  runDue(server, id, dueAt, now) {
    var def = this.get(id)
    if (!def) return
    var d = this.dir()
    var hold = this.read(server, 'ttl.events.hold', {})
    if (hold[id] && hold[id] > now) return
    var window = this.num(def.window_hours, d.window_hours) * this.HOUR
    if (now - dueAt > window) {
      console.warn(`[ttl] events: ${id} skipped (due ${this.local(dueAt).text}, not started within ${window / this.HOUR} h)`)
      this.settle(server, def, dueAt, now)
      return
    }
    var why = this.blocked(server, def, now)
    var res = null
    if (!why) {
      res = this.fire(server, id, { scheduled: true })
      if (res.ok) {
        this.settle(server, def, dueAt, now)
        return
      }
      why = res.error
    }
    hold[id] = now + d.retry_minutes * 60000
    this.write(server, 'ttl.events.hold', hold)
    console.info(`[ttl] events: ${id} waits (${why}), next try in ${d.retry_minutes} min`)
  },

  // ---- fire / end ---------------------------------------------------------------------------------------------------

  ctxOf(id, entry) {
    return { id: id, startedAt: entry.s, endsAt: entry.e || 0, data: entry.d || {}, manual: !!entry.m }
  },

  isActive(server, id) {
    return !!this.read(server, 'ttl.events.active', {})[String(id)]
  },

  activeIds(server) {
    return Object.keys(this.read(server, 'ttl.events.active', {})).sort()
  },

  // Replaces the stored data of an active event (e.g. the storm remembers its region for a restart).
  update(server, id, data) {
    var active = this.read(server, 'ttl.events.active', {})
    if (!active[id]) return false
    active[id].d = data
    this.write(server, 'ttl.events.active', active)
    return true
  },

  // Starts an event. opts: {scheduled: true} (the loop; caps were already checked), {force: true} (restart an active
  // one), {vars: {...}} (extra data handed to start() as ctx.vars). Returns {ok, error, ctx}.
  fire(server, id, opts) {
    opts = opts || {}
    var def = this.get(id)
    if (!def) return { ok: false, error: `unknown event ${id}` }
    var now = Date.now()
    var active = this.read(server, 'ttl.events.active', {})
    if (active[def.id]) {
      if (!opts.force) return { ok: false, error: `${def.id} is already active` }
      this.end(server, def.id, 'forced')
    }
    var minutes = this.num(def.duration_minutes, 0)
    var ctx = { id: def.id, startedAt: now, endsAt: minutes > 0 ? now + minutes * 60000 : 0, data: {}, manual: !opts.scheduled, vars: opts.vars || {} }
    var out
    try {
      out = this.run(server, def, ctx)
    } catch (e) {
      console.error(`[ttl] events: ${def.id} failed to start: ${e}`)
      return { ok: false, error: `start failed: ${e}` }
    }
    if (out === false) return { ok: false, error: `${def.id} could not start now` }
    ctx.data = out
    if (minutes > 0) {
      active = this.read(server, 'ttl.events.active', {})
      active[def.id] = { s: now, e: ctx.endsAt, d: out, g: ctx.rules || null, gr: ctx.restore || null, m: ctx.manual }
      this.write(server, 'ttl.events.active', active)
    }
    var last = this.read(server, 'ttl.events.last', {})
    last[def.id] = { t: now, n: ((last[def.id] && last[def.id].n) || 0) + 1 }
    this.write(server, 'ttl.events.last', last)
    if (opts.scheduled && def.capped !== false) {
      var day = this.read(server, 'ttl.events.day', { k: '', n: 0, t: 0 })
      var key = this.local(now).key
      this.write(server, 'ttl.events.day', { k: key, n: (day.k === key ? day.n : 0) + 1, t: now })
    }
    var where = out.region ? ` in ${out.region}` : ''
    var who = out.player ? ` for ${out.player}` : ''
    console.info(`[ttl] events: ${def.id} started${where}${who}${minutes > 0 ? ` (${minutes} min)` : ''}${ctx.manual ? ' [manual]' : ''}`)
    this.announce(server, def, 'start', this.vars(def, out, minutes), out)
    return { ok: true, ctx: ctx }
  },

  // start() first (it may refuse), then the declarative actions. Returns false or the data object.
  run(server, def, ctx) {
    var res = typeof def.start === 'function' ? def.start(server, ctx) : {}
    if (res === false) return false
    var out = res && typeof res === 'object' ? res : {}
    var a = def.action || {}
    if (a.boss) {
      if (typeof TtlBoss === 'undefined' || typeof TtlBoss.summon !== 'function') throw `${def.id}: action.boss needs TtlBoss.summon (boss core, WP2)`
      // TtlBoss.summon returns an error string when it refuses and null when the summon is under way; the boss core
      // checks its own cooldown, which only a manual (ops) start bypasses.
      var refusal = TtlBoss.summon(server, String(a.boss), { by: `event ${def.id}`, force: !!ctx.manual })
      if (refusal) {
        console.warn(`[ttl] events: ${def.id}: boss ${a.boss} not summoned: ${refusal}`)
        return false
      }
    }
    if (a.favor) {
      if (typeof TtlFavor === 'undefined') throw `${def.id}: action.favor needs events/favor.js`
      var favor = TtlFavor.run(server, ctx)
      if (favor === false) return false
      if (favor && typeof favor === 'object') out = this.merge(out, favor)
    }
    if (a.gamerule) {
      var restore = a.restore || {}
      var rules = {}
      var back = {}
      Object.keys(a.gamerule).forEach(r => {
        if (!this.RULE.test(r) || !this.VALUE.test(String(a.gamerule[r]))) throw `${def.id}: bad gamerule ${r}`
        if (restore[r] === undefined || !this.VALUE.test(String(restore[r]))) throw `${def.id}: gamerule ${r} needs a restore value`
        rules[r] = String(a.gamerule[r])
        back[r] = String(restore[r])
      })
      ctx.rules = rules
      ctx.restore = back
      Object.keys(rules).forEach(r => server.runCommandSilent(`gamerule ${r} ${rules[r]}`))
    }
    return out
  },

  // Ends an active event. why: expired | manual | forced.
  end(server, id, why) {
    var active = this.read(server, 'ttl.events.active', {})
    var entry = active[String(id)]
    if (!entry) return false
    var def = this.get(id) || { id: String(id) }
    delete active[def.id]
    this.write(server, 'ttl.events.active', active)
    try {
      if (typeof def.end === 'function') def.end(server, this.ctxOf(def.id, entry), why || 'manual')
    } catch (e) {
      console.error(`[ttl] events: ${def.id} end hook failed: ${e}`)
    }
    this.restoreRules(server, entry, active)
    console.info(`[ttl] events: ${def.id} ended (${why || 'manual'})`)
    if (why !== 'forced') this.announce(server, def, 'end', this.vars(def, entry.d || {}, 0), entry.d || {})
    return true
  },

  endAll(server, why) {
    var self = this
    var n = 0
    this.activeIds(server).forEach(id => { if (self.end(server, id, why || 'manual')) n++ })
    return n
  },

  // A rule the ended event changed goes back to what the still-running events want (the latest start wins), or to
  // this event's own restore value when none is left.
  restoreRules(server, entry, stillActive) {
    if (!entry.g) return
    Object.keys(entry.g).forEach(rule => {
      var winner = null
      Object.keys(stillActive).forEach(id => {
        var o = stillActive[id]
        if (o.g && o.g[rule] !== undefined && (!winner || o.s > winner.s)) winner = o
      })
      var value = winner ? winner.g[rule] : entry.gr && entry.gr[rule]
      if (value === undefined || value === null || !this.RULE.test(rule) || !this.VALUE.test(String(value))) return
      server.runCommandSilent(`gamerule ${rule} ${value}`)
    })
  },

  expire(server, now) {
    var self = this
    var active = this.read(server, 'ttl.events.active', {})
    Object.keys(active).forEach(id => {
      if (active[id].e && active[id].e <= now) self.end(server, id, 'expired')
    })
  },

  // Server (re)started with events still active: re-assert their rules in start order, then the events' own hooks.
  boot(server) {
    var self = this
    var active = this.read(server, 'ttl.events.active', {})
    var ids = Object.keys(active).sort((a, b) => active[a].s - active[b].s)
    ids.forEach(id => {
      var entry = active[id]
      if (entry.g) {
        Object.keys(entry.g).forEach(r => {
          if (self.RULE.test(r) && self.VALUE.test(String(entry.g[r]))) server.runCommandSilent(`gamerule ${r} ${entry.g[r]}`)
        })
      }
      var def = self.get(id)
      try {
        if (def && typeof def.resume === 'function') def.resume(server, self.ctxOf(id, entry))
      } catch (e) {
        console.error(`[ttl] events: ${id} resume failed: ${e}`)
      }
      console.info(`[ttl] events: ${id} still active after the restart`)
    })
    try {
      var board = server.getScoreboard()
      if (!board.getObjective('ttl.play')) server.runCommandSilent('scoreboard objectives add ttl.play minecraft.custom:minecraft.play_time')
    } catch (e) {
      console.warn(`[ttl] events: could not create the ttl.play objective: ${e}`)
    }
  },

  // The `poll` hooks of registered events.
  pollAll(server) {
    var self = this
    var active = this.read(server, 'ttl.events.active', {})
    Object.keys(this.js).forEach(id => {
      var def = self.get(id)
      if (!def || typeof def.poll !== 'function') return
      try {
        def.poll(server, active[id] ? self.ctxOf(id, active[id]) : null)
      } catch (e) {
        console.error(`[ttl] events: ${id} poll failed: ${e}`)
      }
    })
  },

  // ---- announcements ------------------------------------------------------------------------------------------------

  vars(def, data, minutes) {
    var v = { label: this.label(def), minutes: String(minutes || '') }
    Object.keys(data || {}).forEach(k => {
      var x = data[k]
      if (x === null || x === undefined || typeof x === 'object') return
      v[k] = String(x)
    })
    return v
  },

  fill(text, vars, bold) {
    return String(text || '').replace(/\{(\w+)\}/g, (all, k) => {
      if (vars[k] === undefined) return ''
      return bold && k === 'player' && typeof TtlDiscord !== 'undefined' ? TtlDiscord.name(vars[k]) : vars[k]
    })
  },

  muted(player) {
    return player.persistentData.getBoolean('ttl.events.muted')
  },

  setMuted(player, on) {
    player.persistentData.putBoolean('ttl.events.muted', !!on)
  },

  // Online players that should see the announcement: the event's audience (life) and, when start() returned an
  // `audience` list (names), only those.
  audience(server, def, data) {
    var want = String(def.audience || 'all')
    var names = data && Array.isArray(data.audience) ? data.audience.map(String) : null
    var out = []
    server.getPlayerList().getPlayers().forEach(p => {
      var phase = TtlLife.phase(p)
      if (want === 'life1' && phase !== 'life1') return
      if (want === 'life2' && phase !== 'life2') return
      if (names && names.indexOf(String(p.username)) < 0) return
      out.push(p)
    })
    return out
  },

  json(text) {
    return JSON.stringify({ text: String(text) })
  },

  announce(server, def, phase, vars, data) {
    var a = def.announce || {}
    var start = phase === 'start'
    var title = this.fill(start ? a.title : a.end_title, vars)
    var subtitle = this.fill(start ? a.subtitle : a.end_subtitle, vars)
    var chat = this.fill(start ? a.chat : a.end_chat, vars)
    var self = this
    var color = String(a.color || 'yellow')
    var players = this.audience(server, def, data)
    players.forEach(p => {
      var name = String(p.username)
      try {
        if (title) {
          server.runCommandSilent(`title ${name} times 10 80 30`)
          if (subtitle) server.runCommandSilent(`title ${name} subtitle ${self.json(subtitle)}`)
          server.runCommandSilent(`title ${name} title ${JSON.stringify({ text: title, color: color })}`)
        }
        if (start && a.sound) server.runCommandSilent(`playsound ${a.sound} master ${name} ~ ~ ~ 1 1`)
        if (chat && !self.muted(p)) {
          server.runCommandSilent(`tellraw ${name} ${JSON.stringify([{ text: '[World Event] ', color: 'gold' }, { text: chat, color: color }])}`)
        }
        if (start && a.clip && !self.muted(p) && typeof TtlCorridor !== 'undefined' && TtlCorridor.CLIPS && TtlCorridor.CLIPS[a.clip]) {
          TtlCorridor.say(server, name, String(a.clip))
        }
      } catch (e) {
        console.warn(`[ttl] events: announcing ${def.id} to ${name} failed: ${e}`)
      }
    })
    if (start) this.story(server, def, vars)
  },

  // Discord #story + the Hall of Souls. Guarded: no Discord bridge, a test bot as the subject or `story = false` post nothing.
  story(server, def, vars) {
    var a = def.announce || {}
    var text = this.fill(a.story, vars, true)
    var d = this.dir()
    if (!text || !d.story) return
    if (vars.player && typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(vars.player)) return
    var posted = false
    try {
      if (typeof TtlDiscord !== 'undefined') posted = TtlDiscord.post(server, text)
    } catch (e) {
      console.warn(`[ttl] events: Discord post failed: ${e}`)
    }
    console.info(`[ttl] events: ${def.id} #story line ${posted ? 'posted' : 'not posted'}: ${text}`)
    try {
      if (typeof TtlHall !== 'undefined' && typeof TtlHall.noteEvent === 'function') TtlHall.noteEvent(server, def.id, this.label(def), vars)
    } catch (e) {
      console.warn(`[ttl] events: Hall note failed: ${e}`)
    }
  },

  // ---- regions (nations are canon regions; §0 of the architecture doc) ---------------------------------------------

  grid() {
    try {
      return Java.loadClass('com.yasuke.ttl.world.CanonMap').grid()
    } catch (e) {
      return null
    }
  },

  // {key, name} of the canon region at a block column, or null (no grid, open sea, uncharted). Coastal water
  // belongs to its nation (ownerCell), like RegionTitles.regionAt.
  regionAt(x, z) {
    var grid = this.grid()
    if (!grid) return null
    try {
      var cell = grid.charAt(x, z)
      if (String(cell) === '.') cell = grid.ownerCell(x, z)
      var region = grid.region(cell)
      if (!region) return null
      return { key: String(cell), name: String(region.name()) }
    } catch (e) {
      console.warn(`[ttl] events: region lookup failed: ${e}`)
      return null
    }
  },

  // Human-readable state for /ttl events.
  lines(server) {
    var now = Date.now()
    var self = this
    var out = []
    var active = this.read(server, 'ttl.events.active', {})
    var next = this.read(server, 'ttl.events.next', {})
    var last = this.read(server, 'ttl.events.last', {})
    out.push(`active: ${Object.keys(active).length === 0 ? 'none' : Object.keys(active).sort().map(id => `${id}${active[id].e ? ` (${Math.max(0, Math.ceil((active[id].e - now) / 60000))} min left)` : ''}`).join(', ')}`)
    this.ids().forEach(id => {
      var def = self.get(id)
      out.push(`${id}: ${next[id] ? `next ${self.local(next[id]).text}` : 'manual only'}${last[id] ? `, last ${self.local(last[id].t).text} (${last[id].n}x)` : ''}${self.registered(id) ? '' : ', TOML only'}${def.poll ? ', polls' : ''}`)
    })
    return out
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlEvents.boot(server)
  } catch (e) {
    console.error(`[ttl] events: start-up failed: ${e}`)
  }
  // A script reload runs this again; the stamp makes the older loops stop instead of doubling up.
  var stamp = String(Date.now())
  server.persistentData.putString('ttl.events.loop', stamp)
  var alive = () => String(server.persistentData.getString('ttl.events.loop')) === stamp
  var loop = () => server.scheduleInTicks(TtlEvents.dir().loop_ticks, () => {
    if (!alive()) return
    try {
      TtlEvents.tick(server)
    } catch (e) {
      console.error(`[ttl] events: scheduler pass failed: ${e}`)
    }
    loop()
  })
  var poll = () => server.scheduleInTicks(TtlEvents.dir().poll_ticks, () => {
    if (!alive()) return
    try {
      TtlEvents.pollAll(server)
    } catch (e) {
      console.error(`[ttl] events: poll pass failed: ${e}`)
    }
    poll()
  })
  loop()
  poll()
})
