// priority: 70
// Wild bosses (design/architecture/story-characters.md section 5; knobs: design/data/bosses.toml [wild] and each boss's
// `wild` table). Every boss with wild.chance_per_day > 0 has a very rare chance to appear in the wilderness while a Life 2
// player stands in one of its regions: each poll rolls chance x elapsed minutes / 1440 per player (x path_mult for the
// player's story path). A hit picks a surface spot `distance` blocks away (loaded chunk, right surface, inside a listed
// region, outside Tempest's safe zone and every placed build) and summons the boss through TtlBoss.summon with
// {wild: true, skipGate: ignore_requires}. Wild and story are separate (world-state.md H3, WP-W2): a wild boss never reads
// or writes the per-party story cooldown, a story fight of the same boss never blocks the roll and a wild one never blocks
// the story fight; only another wild instance of the same id, max_active and the framework's max_instances do. A wild boss
// answers everyone and is announced (title, chat, Discord #story); a wild kill pays rep and coins x rewards_mult (boss.js
// finish) and stamps no cooldown. Only on the continent: the spot must lie in one of the boss's canon regions (outside the
// coast the mods' own spawns rule, boss.js checkSpawn).
// The roll is a poll of the event director (events/director.js, no [[event]] entry: it is never scheduled or fired), so one
// loop owns the timing; it refuses while a timed event with action.boss is active. Caps: max_active wild bosses alive,
// max_per_day starts per Brussels day, min_gap_hours between starts, per boss `cap` per day and `cooldown_hours` (hours
// between two wild starts of the boss; default its story cooldown_hours).
// Server persistentData `ttl.boss.wild` JSON {day, n, last, per: {id: {n, t}}} (starts today, last start, per boss starts
// today and last start). Ops: `/ttl boss wild roll <id> [player]` (no chance, region, weather or wild cooldown; the caps for
// active bosses still apply; not counted in the day caps) and `/ttl boss wild` (state).
const TtlWild = {
  lastPoll: 0,
  hm: undefined,
  warned: false,

  num(v, dflt) {
    var n = Number(v)
    return v !== undefined && v !== null && v !== '' && isFinite(n) ? n : dflt
  },

  conf() {
    var w = (typeof TtlData !== 'undefined' && TtlData.bosses && TtlData.bosses.wild) || {}
    var d = w.distance || [64, 160]
    return {
      enabled: w.enabled !== false,
      maxActive: this.num(w.max_active, 1),
      maxPerDay: this.num(w.max_per_day, 2),
      gapMs: this.num(w.min_gap_hours, 6) * 3600000,
      requirePlayers: this.num(w.require_players, 1),
      lo: this.num(d[0], 64),
      hi: this.num(d[1], 160),
      ignoreRequires: w.ignore_requires !== false,
      announce: w.announce !== false,
      life2Only: w.life2_only !== false
    }
  },

  // Bosses with a wild table whose chance is above 0.
  defs() {
    return TtlBoss.defs().filter(d => d.wild && Number(d.wild.chance_per_day) > 0)
  },

  // ---- state ------------------------------------------------------------------------------------------------------

  dayKey(now) {
    try {
      return TtlEvents.local(now).key
    } catch (e) {
      return new Date(now).toISOString().substring(0, 10)
    }
  },

  // The persisted counters, rolled over to today (the per-boss start time survives the day change).
  state(server, now) {
    var st = { day: '', n: 0, last: 0, per: {} }
    try {
      var raw = String(server.persistentData.getString('ttl.boss.wild') || '')
      if (raw) st = JSON.parse(raw)
    } catch (e) {
      console.warn(`[ttl] boss: ttl.boss.wild unreadable, starting over (${e})`)
    }
    st.per = st.per || {}
    var key = this.dayKey(now)
    if (st.day !== key) {
      st.day = key
      st.n = 0
      Object.keys(st.per).forEach(id => { st.per[id].n = 0 })
    }
    return st
  },

  // A wild start was made (counted in the day caps and the boss's own cap).
  count(server, def, now) {
    var st = this.state(server, now)
    st.n++
    st.last = now
    var per = st.per[def.id] || { n: 0, t: 0 }
    per.n++
    per.t = now
    st.per[def.id] = per
    server.persistentData.putString('ttl.boss.wild', JSON.stringify(st))
  },

  // ---- rules ------------------------------------------------------------------------------------------------------

  // Why no wild boss may start at all right now, or ''. Manual rolls (ops) skip the schedule rules.
  globalBlock(server, manual, now) {
    var c = this.conf()
    var list = TtlBoss.instances(server)
    var out = list.filter(r => r.wild).length
    if (out >= c.maxActive) return `${out} wild boss${out === 1 ? '' : 'es'} already roaming (max_active ${c.maxActive})`
    var fw = TtlBoss.conf()
    if (fw.maxInstances > 0 && list.length >= fw.maxInstances) return `${list.length} bosses are out across the world (max_instances ${fw.maxInstances})`
    if (manual) return ''
    if (!c.enabled) return 'wild bosses are switched off'
    try {
      if (typeof TtlEvents !== 'undefined') {
        var live = TtlEvents.read(server, 'ttl.events.active', {})
        for (var id in live) {
          var ev = TtlEvents.get(id)
          if (ev && ev.action && ev.action.boss) return `the timed event ${id} has a boss out`
        }
      }
    } catch (e) {
      console.warn(`[ttl] boss: reading the active events failed: ${e}`)
    }
    var st = this.state(server, now)
    if (st.n >= c.maxPerDay) return `${st.n} wild starts today (max_per_day ${c.maxPerDay})`
    if (now - st.last < c.gapMs) return `the last wild start was ${Math.round((now - st.last) / 60000)} minutes ago (min_gap_hours)`
    return ''
  },

  // Why this boss may not start in the wild right now, or ''.
  bossBlock(server, def, manual, now) {
    if (def.proxy && !TtlBoss.conf().proxies) return `${def.title} is a proxy boss and proxy_bosses is off`
    // Only another WILD instance of this boss blocks it: a story fight of the same boss is a different thing.
    var list = TtlBoss.instances(server)
    for (var k = 0; k < list.length; k++) {
      if (list[k].id === def.id && list[k].wild) return `${def.title} is already ${list[k].pending ? 'being summoned' : 'out there'} (wild)`
    }
    if (manual) return ''
    var st = this.state(server, now)
    var per = st.per[def.id] || { n: 0, t: 0 }
    var cap = def.wild.cap === undefined ? 1 : Number(def.wild.cap)
    if (per.n >= cap) return `${def.id} already had ${per.n} wild start${per.n === 1 ? '' : 's'} today`
    var cdh = def.wild.cooldown_hours !== undefined ? Number(def.wild.cooldown_hours) : Number(def.cooldown_hours) || 0
    if (per.t && now - per.t < cdh * 3600000) {
      return `${def.id} had a wild start ${Math.round((now - per.t) / 3600000)} hours ago (wild cooldown ${cdh} h)`
    }
    return ''
  },

  // Both of the above (what `ttl boss expect <p> wildblock <id>` reads).
  blocker(server, def, manual) {
    var now = Date.now()
    return this.globalBlock(server, manual, now) || this.bossBlock(server, def, manual, now)
  },

  pathOf(p) {
    try {
      if (p.stages.has('ttl.path.dark')) return 'dark'
      if (p.stages.has('ttl.path.light')) return 'light'
      var s = String(p.persistentData.getString('ttl.story.path') || '')
      return s === 'dark' || s === 'light' ? s : ''
    } catch (e) {
      return ''
    }
  },

  // Chance per day for this player (per day of presence in a listed region), with the boss's path multiplier.
  chanceFor(def, p) {
    var pm = def.wild.path_mult || {}
    var path = this.pathOf(p)
    var mult = path && pm[path] !== undefined ? Number(pm[path]) : 1
    return Number(def.wild.chance_per_day) * mult
  },

  // {key, name} of the canon region at a block column, or null (open sea, uncharted).
  regionOf(x, z) {
    try {
      if (typeof TtlRep === 'undefined' || typeof TtlRep.regionAt !== 'function') return null
      var key = TtlRep.regionAt(x, z)
      if (!key) return null
      var name = String(key)
      try {
        var g = TtlRep.loadGrid()
        var r = g ? g.region(key) : null
        if (r) name = String(r.name())
      } catch (e) {
        // the letter stays the name
      }
      return { key: String(key), name: name }
    } catch (e) {
      return null
    }
  },

  weatherOk(level, want) {
    if (!want || want === 'any') return true
    try {
      return want === 'thunder' ? !!level.isThundering() : !!level.isRaining()
    } catch (e) {
      return false
    }
  },

  timeOk(level, want) {
    if (!want || want === 'any') return true
    try {
      var t = Number(level.getDayTime()) % 24000
      var night = t >= 13000 && t < 23000
      return want === 'night' ? night : !night
    } catch (e) {
      return false
    }
  },

  // ---- spots ------------------------------------------------------------------------------------------------------

  heightmap() {
    if (this.hm === undefined) {
      try {
        this.hm = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      } catch (e) {
        this.hm = null
        console.warn(`[ttl] boss: Heightmap is not available, wild spots cannot be checked: ${e}`)
      }
    }
    return this.hm
  },

  // What is at a block column: {known: false} when its chunk is not loaded (or the check is unavailable), else
  // {known, y (the first free block above the ground, or above the water), water, lava, biome}.
  surface(level, x, z) {
    try {
      var hm = this.heightmap()
      if (!hm || !level.hasChunkAt(x, z)) return { known: false }
      var y = Number(level.getHeight(hm.MOTION_BLOCKING_NO_LEAVES, x, z))
      var id = String(level.getBlock(x, y - 1, z).id)
      var biome = ''
      try {
        biome = String(level.getBlock(x, y - 1, z).biomeId)
      } catch (e) {
        biome = ''
      }
      return { known: true, y: y, water: id === 'minecraft:water', lava: id === 'minecraft:lava', biome: biome }
    } catch (e) {
      if (!this.warned) console.warn(`[ttl] boss: reading the surface at ${x} ${z} failed: ${e}`)
      this.warned = true
      return { known: false }
    }
  },

  // Tempest's safe square and every placed build keep a margin: a wild boss never appears inside a town.
  protectedSpot(server, x, z) {
    var pad = 24
    try {
      if (typeof TtlSafeSpawns !== 'undefined') {
        var zones = TtlSafeSpawns.ZONES.filter(s => s.dim === TtlLife.OVERWORLD)
        for (var i = 0; i < zones.length; i++) {
          var r = zones[i].radius + pad
          if ((x - zones[i].x) * (x - zones[i].x) + (z - zones[i].z) * (z - zones[i].z) <= r * r) return true
        }
      }
      var builds = (TtlData.builds || []).filter(b => b.dimension === TtlLife.OVERWORLD)
      for (var j = 0; j < builds.length; j++) {
        var box = String(server.persistentData.getString(`ttl.build.${builds[j].name}.box`) || '')
        if (!box) continue
        var b = box.split(' ').map(Number)
        if (x >= b[0] - pad && z >= b[1] - pad && x <= b[2] + pad && z <= b[3] + pad) return true
      }
    } catch (e) {
      console.warn(`[ttl] boss: wild spot protection check failed: ${e}`)
    }
    return false
  },

  // A spot `distance` blocks from the player for this boss: {x, z, y?, region}, or null. Natural rolls only take a spot in
  // a loaded chunk (so the surface, water and biome are known) inside one of the boss's regions; a manual roll falls back to
  // an unchecked spot (the summon finds the surface itself).
  pickSpot(server, def, player, manual) {
    var c = this.conf()
    var w = def.wild
    var level = player.level
    var fallback = null
    for (var i = 0; i < 14; i++) {
      var ang = Math.random() * 2 * Math.PI
      var dist = c.lo + Math.random() * (c.hi - c.lo)
      var x = Math.floor(player.getX() + Math.cos(ang) * dist)
      var z = Math.floor(player.getZ() + Math.sin(ang) * dist)
      var region = this.regionOf(x, z)
      if (!manual && (!region || w.regions.indexOf(region.key) < 0)) continue
      if (TtlBoss.outside(TtlLife.OVERWORLD, x, z)) continue
      if (this.protectedSpot(server, x, z)) continue
      var s = this.surface(level, x, z)
      if (!s.known) {
        if (manual && !fallback) fallback = { x: x, z: z, region: region }
        continue
      }
      var mode = w.surface || 'land'
      if (mode === 'land' && (s.water || s.lava)) continue
      if (mode === 'water' && !s.water) continue
      if (w.biomes && w.biomes.length > 0 && w.biomes.indexOf(s.biome) < 0) continue
      return { x: x, z: z, y: s.y, region: region }
    }
    return fallback
  },

  // ---- the roll ---------------------------------------------------------------------------------------------------

  // One wild start of `def` near `player`. opts: {manual: true, by}. Returns {ok, error, x, z, region}.
  roll(server, def, player, opts) {
    opts = opts || {}
    var manual = !!opts.manual
    var c = this.conf()
    var why = this.blocker(server, def, manual)
    if (why) return { ok: false, error: why }
    var name = String(player.username)
    if (String(player.level.dimension) !== TtlLife.OVERWORLD) return { ok: false, error: `${name} is not in the Overworld` }
    var spot = this.pickSpot(server, def, player, manual)
    if (!spot) return { ok: false, error: `no suitable spot ${c.lo}-${c.hi} blocks from ${name}` }
    var region = spot.region ? spot.region.name : ''
    var err = TtlBoss.summon(server, def.id, {
      wild: true, skipGate: c.ignoreRequires, x: spot.x, y: spot.y, z: spot.z, dim: TtlLife.OVERWORLD,
      by: manual ? `wild roll (${opts.by || 'ops'})` : 'wild', region: region, near: name
    })
    if (err) return { ok: false, error: err }
    if (!manual) this.count(server, def, Date.now())
    console.info(`[ttl] boss: wild ${def.id} near ${name} in ${region || 'uncharted land'}${manual ? ' (manual)' : ''}`)
    return { ok: true, x: spot.x, z: spot.z, region: region }
  },

  // Life 2 players in the Overworld with their region key: [{p, key}].
  eligible(server, c) {
    var out = []
    var self = this
    TtlBoss.players(server).forEach(p => {
      try {
        if (p.isSpectator() || String(p.level.dimension) !== TtlLife.OVERWORLD) return
        if (c.life2Only && (TtlLife.phase(p) !== 'life2' || TtlBoss.isBot(server, p))) return
        var r = self.regionOf(Math.floor(p.getX()), Math.floor(p.getZ()))
        if (r) out.push({ p: p, key: r.key })
      } catch (e) {
        console.warn(`[ttl] boss: wild eligibility of ${p.username} failed: ${e}`)
      }
    })
    return out
  },

  // The director's poll (every [director] poll_ticks): one roll per boss and eligible player, at most one start.
  poll(server) {
    var c = this.conf()
    if (!c.enabled) return
    var now = Date.now()
    var last = this.lastPoll
    this.lastPoll = now
    if (!last) return
    // A stalled server must not turn the missed time into a burst of rolls.
    var minutes = Math.min(5, Math.max(0, (now - last) / 60000))
    var defs = this.defs()
    if (defs.length === 0 || this.globalBlock(server, false, now)) return
    var players = this.eligible(server, c)
    if (players.length === 0) return
    var level = server.overworld()
    var self = this
    var hits = []
    defs.forEach(def => {
      var w = def.wild
      if (self.bossBlock(server, def, false, now)) return
      if (!self.weatherOk(level, w.weather) || !self.timeOk(level, w.time)) return
      var here = players.filter(x => w.regions.indexOf(x.key) >= 0)
      if (here.length < c.requirePlayers) return
      here.forEach(x => {
        if (Math.random() < (self.chanceFor(def, x.p) * minutes) / 1440) hits.push({ def: def, p: x.p })
      })
    })
    if (hits.length === 0) return
    var h = hits[Math.floor(Math.random() * hits.length)]
    var res = this.roll(server, h.def, h.p, { manual: false })
    if (!res.ok) console.info(`[ttl] boss: wild roll for ${h.def.id} near ${h.p.username} not started: ${res.error}`)
  },

  // ---- announcement -----------------------------------------------------------------------------------------------

  // Title + chat to the Life 2 players, one #story line (never for a test bot). ctx: the summon context (region, near).
  announce(server, def, ctx) {
    var c = this.conf()
    if (!c.announce) return
    var where = ctx.region || 'the wilds'
    var line = `A calamity stirs: ${def.title} roams ${where}.`
    var title = JSON.stringify({ text: 'A calamity stirs', color: 'dark_red' })
    var sub = JSON.stringify({ text: `${def.title} roams ${where}`, color: 'gray' })
    TtlBoss.players(server).forEach(p => {
      try {
        if (TtlLife.phase(p) !== 'life2') return
        p.tell(Text.red(line))
        server.runCommandSilent(`title ${p.username} times 10 70 20`)
        server.runCommandSilent(`title ${p.username} subtitle ${sub}`)
        server.runCommandSilent(`title ${p.username} title ${title}`)
      } catch (e) {
        console.warn(`[ttl] boss: wild announcement to ${p.username} failed: ${e}`)
      }
    })
    try {
      if (typeof TtlDiscord === 'undefined' || (ctx.near && TtlDiscord.isBot(ctx.near))) return
      TtlDiscord.post(server, line)
    } catch (e) {
      console.warn(`[ttl] boss: Discord post failed: ${e}`)
    }
  },

  // Human-readable state for `/ttl boss wild`.
  lines(server) {
    var now = Date.now()
    var c = this.conf()
    var st = this.state(server, now)
    var out = TtlBoss.instances(server).filter(r => r.wild).length
    var lines = [`wild: ${c.enabled ? 'on' : 'OFF'}, ${out}/${c.maxActive} roaming, ${st.n}/${c.maxPerDay} starts today, distance ${c.lo}-${c.hi}, gap ${c.gapMs / 3600000} h`]
    var block = this.globalBlock(server, false, now)
    if (block) lines.push(`wild: no start possible now: ${block}`)
    this.defs().forEach(d => {
      var w = d.wild
      var extra = (w.weather && w.weather !== 'any' ? ` ${w.weather}` : '') + (w.time && w.time !== 'any' ? ` ${w.time}` : '') +
        (w.surface && w.surface !== 'land' ? ` surface=${w.surface}` : '') + (w.path_mult ? ` path_mult=${JSON.stringify(w.path_mult)}` : '')
      lines.push(`wild ${d.id}: ${Math.round(Number(w.chance_per_day) * 10000) / 100} %/day in ${w.regions.join(',')}${extra}`)
    })
    return lines
  }
}

// One poll of the event director owns the timing (events/director.js header). No [[event]] entry exists, so the director
// never schedules it and `ttl events fire wild_boss` is refused.
try {
  if (typeof TtlEvents !== 'undefined') {
    TtlEvents.register({
      id: 'wild_boss',
      label: 'Wild boss roll',
      canStart() {
        return 'wild bosses are rolled by bosses/wild.js; use /ttl boss wild roll <id> [player]'
      },
      poll(server) {
        TtlWild.poll(server)
      }
    })
  } else {
    console.warn('[ttl] boss: TtlEvents is not loaded, wild bosses will not roll')
  }
} catch (e) {
  console.error(`[ttl] boss: registering the wild roll with the event director failed: ${e}`)
}
