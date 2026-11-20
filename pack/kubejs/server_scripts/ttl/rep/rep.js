// priority: 70
// Factions and reputation (design/architecture/sprint3-4.md S3; numbers in design/data/factions.toml → TtlData.factions).
// A player has an integer reputation -100..100 per faction. Its band (hostile, unfriendly, neutral, friendly, honored,
// exalted) is mirrored three ways, always together, by TtlRep.sync:
//   player persistentData `ttl.rep`   JSON {factionId: int}, the truth (survives death and rebirth)
//   scoreboard `ttl.rep.<faction>`    the raw number, for Easy NPC conditions and FTB Quests "at least n"
//   stage `ttl.faction.<f>.<band>`    exactly one per faction (FTB Quests `stage` tasks, dialog conditions)
// plus Tensura's own scalar `reputation` for the faction with tensura_mirror = true (Dwargon; same -100..100 scale,
// hostile at -50; verify in game that `tensura get stat <p> reputation` follows).
// Server persistentData `ttl.rep.log` is a ring (rules.log_size) of {t, p, f, d, v, r}.
//
// PUBLIC API (other packages call these; `f` is a faction id from factions.toml, `player` a ServerPlayer):
//   TtlRep.ids()                        every faction id; TtlRep.faction(f) its TOML table or null; TtlRep.title(f)
//   TtlRep.get(player, f)               current value (0 for none/unknown)
//   TtlRep.all(player)                  {f: value} for every faction
//   TtlRep.band(player, f)              'hostile' | 'unfriendly' | 'neutral' | 'friendly' | 'honored' | 'exalted'
//   TtlRep.bandFor(f, value)            the band a value would have
//   TtlRep.rank(band)                   0 (hostile) .. 5 (exalted), for comparing bands
//   TtlRep.atLeast(player, f, band)     true when the player's band is `band` or better (nations/guild gates)
//   TtlRep.atMost(player, f, band)      true when it is `band` or worse
//   TtlRep.add(server, player, f, delta, reason)   change by delta, clamp, sync, log; returns the new value (null: unknown faction)
//   TtlRep.set(server, player, f, n, reason)       same, absolute
//   (add/set take the faction id string; a faction table or {faction: id} is reduced to its id, anything else logs
//    "[ttl] rep: not a faction id" and returns null: TtlRep.idOf(f, reason))
//   TtlRep.seed(server, player, race)   rebirth: overwrite every faction from race + Life 1 karma ([faction.seed]); race optional (ttl.race)
//   TtlRep.sync(server, player, mirror) rewrite scoreboard + stages (+ Tensura scalar when mirror is true) from the stored values
//   TtlRep.guardsHostile(player, f)     true when guards of f attack this player (rules.guard_attack_at)
//   TtlRep.shopOpen(player, f)          false when shops of f refuse this player (rules.shop_refuse_at)
//   TtlRep.factionAt(x, z)              the faction whose canon region covers an overworld block column, or null
//   TtlRep.lines(player)                plain-text lines for /ttl rep
//   TtlRep.log(server)                  the ring as an array, oldest first
//   TtlRep.renown(server, player)       the player's renown (worth) as an int, recomputed now and mirrored to scoreboard
//                                       `ttl.renown`; 0 in Life 1. A nation's value = sum of its members' renown + holdings.
//   TtlRep.renownParts(server, player)  {tier, bosses, stages, rep, uniques, bonus, total}: where the renown comes from
//   TtlRep.addRenown(server, player, n, reason)   permanent bonus renown (quests, merit, staff); returns the new total
// Callers pass a short `reason` ('quest ch16', 'boss tempest_serpent', 'bounty', 'merit'); it lands in the log.
// Reaching Exalted for the first time posts one line to #story (TtlDiscord.post) and records it in `ttl.rep.exalted`.
const TtlRep = {
  BANDS: ['hostile', 'unfriendly', 'neutral', 'friendly', 'honored', 'exalted'],
  KEY: 'ttl.rep',
  DAY_MS: 86400000,

  conf() {
    return TtlData.factions
  },

  rules() {
    return TtlData.factions.rules
  },

  list() {
    return TtlData.factions.faction
  },

  ids() {
    return this.list().map(f => String(f.id))
  },

  faction(id) {
    var all = this.list()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  title(id) {
    var f = this.faction(id)
    return f ? String(f.title) : String(id)
  },

  bandTitle(band) {
    var b = String(band)
    return b.charAt(0).toUpperCase() + b.slice(1)
  },

  rank(band) {
    return this.BANDS.indexOf(String(band))
  },

  bounds() {
    var r = this.rules()
    return { min: Number(r.min), max: Number(r.max) }
  },

  clamp(n) {
    var b = this.bounds()
    n = Math.round(Number(n))
    if (isNaN(n)) n = 0
    return n < b.min ? b.min : (n > b.max ? b.max : n)
  },

  // Thresholds of a faction: its own bands table, else [bands].
  thresholds(f) {
    var fac = this.faction(f)
    return fac && fac.bands ? fac.bands : this.conf().bands
  },

  // hostile: value <= hostile · unfriendly: value <= unfriendly · friendly/honored/exalted: value >= threshold.
  bandFor(f, value) {
    var t = this.thresholds(f)
    var v = Number(value)
    if (v >= t.exalted) return 'exalted'
    if (v >= t.honored) return 'honored'
    if (v >= t.friendly) return 'friendly'
    if (v <= t.hostile) return 'hostile'
    if (v <= t.unfriendly) return 'unfriendly'
    return 'neutral'
  },

  // ---- storage ---------------------------------------------------------------------------------------------

  read(player) {
    try {
      var raw = String(player.persistentData.getString(this.KEY))
      var parsed = raw ? JSON.parse(raw) : {}
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (e) {
      console.error(`[ttl] rep: ${player.username}'s stored reputation is unreadable, treating it as empty: ${e}`)
      return {}
    }
  },

  write(player, map) {
    player.persistentData.putString(this.KEY, JSON.stringify(map))
  },

  // `/ttl reset`: forget every reputation, the renown bonus and the decay clock, then rewrite the mirrors at zero
  // (scoreboards, band stages, Tensura's reputation scalar).
  clear(server, player) {
    var data = player.persistentData
    ;[this.KEY, 'ttl.renown', 'ttl.renown.bonus', 'ttl.rep.exalted', 'ttl.rep.decayAt'].forEach(k => data.remove(k))
    this.sync(server, player, true)
  },

  get(player, f) {
    if (!this.faction(f)) return 0
    var v = Number(this.read(player)[f])
    return isNaN(v) ? 0 : v
  },

  all(player) {
    var map = this.read(player)
    var out = {}
    this.ids().forEach(id => {
      var v = Number(map[id])
      out[id] = isNaN(v) ? 0 : v
    })
    return out
  },

  band(player, f) {
    return this.bandFor(f, this.get(player, f))
  },

  atLeast(player, f, band) {
    return this.rank(this.band(player, f)) >= this.rank(band)
  },

  atMost(player, f, band) {
    return this.rank(this.band(player, f)) <= this.rank(band)
  },

  // A world mood (TtlChronicle, design/data/world.toml) shifts the band by whole bands for guards and shops only.
  guardsHostile(player, f) {
    var shift = 0
    try { if (typeof TtlChronicle !== 'undefined') shift = TtlChronicle.mood(f, player.getServer()) } catch (e) { console.error(`[ttl] rep: world mood failed: ${e}`) }
    return this.rank(this.band(player, f)) + shift <= this.rank(this.rules().guard_attack_at)
  },

  shopOpen(player, f) {
    var shift = 0
    try { if (typeof TtlChronicle !== 'undefined') shift = TtlChronicle.mood(f, player.getServer()) } catch (e) { console.error(`[ttl] rep: world mood failed: ${e}`) }
    return this.rank(this.band(player, f)) + shift > this.rank(this.rules().shop_refuse_at)
  },

  // ---- changing --------------------------------------------------------------------------------------------

  // A faction id from what a caller passed: the id string itself, or a faction table / {faction: id} record (TtlRep.factionAt
  // returns the table, not the id; merit and the Public Works record handed that table to add() and no reputation was
  // granted, 20/11/2026). null (and a clear error with the caller's reason) for anything else.
  idOf(f, reason) {
    var v = f
    for (var depth = 0; depth < 3 && v !== null && v !== undefined && typeof v === 'object'; depth++) {
      if (v.id !== undefined && v.id !== null) v = v.id
      else if (v.faction !== undefined && v.faction !== null) v = v.faction
      else break
    }
    var s = v === null || v === undefined ? '' : String(v)
    if (s === '' || s === '[object Object]' || s === 'undefined' || s === 'null') {
      var shown = ''
      try { shown = typeof f === 'object' && f !== null ? `object with keys ${Object.keys(f).join(',') || 'none'}` : String(f) } catch (e) { shown = typeof f }
      console.error(`[ttl] rep: not a faction id: ${shown} (reason: ${reason || 'none'}); pass the id string, e.g. TtlRep.factionAt(x, z).id`)
      return null
    }
    return s
  },

  set(server, player, f, n, reason) {
    f = this.idOf(f, reason)
    if (f === null) return null
    if (!this.faction(f)) {
      console.warn(`[ttl] rep: unknown faction ${f} (reason: ${reason || 'none'})`)
      return null
    }
    var map = this.read(player)
    var before = this.get(player, f)
    var after = this.clamp(n)
    map[f] = after
    this.write(player, map)
    this.sync(server, player, f === this.mirrorId())
    if (after !== before) {
      this.note(server, player, f, after - before, after, reason)
      this.checkExalted(server, player, f, before, after)
    }
    return after
  },

  add(server, player, f, delta, reason) {
    f = this.idOf(f, reason)
    if (f === null) return null
    if (!this.faction(f)) {
      console.warn(`[ttl] rep: unknown faction ${f} (reason: ${reason || 'none'})`)
      return null
    }
    return this.set(server, player, f, this.get(player, f) + Number(delta), reason)
  },

  // ---- mirrors ---------------------------------------------------------------------------------------------

  mirrorId() {
    var all = this.list()
    for (var i = 0; i < all.length; i++) {
      if (all[i].tensura_mirror) return String(all[i].id)
    }
    return null
  },

  // Creates the ttl.rep.<f> objectives that are missing. Called at start and before writing a score.
  ensure(server) {
    var board = server.getScoreboard()
    this.ids().forEach(id => {
      var name = `ttl.rep.${id}`
      if (!board.getObjective(name)) server.runCommandSilent(`scoreboard objectives add ${name} dummy`)
    })
  },

  // Rewrites the scoreboard and the stages from the stored values. `mirror` also writes Tensura's own scalar
  // (not on login: Tensura raises it itself through dwarf trades, and a login must not undo that).
  sync(server, player, mirror) {
    var name = String(player.username)
    var map = this.read(player)
    var self = this
    var board = server.getScoreboard()
    this.list().forEach(fac => {
      var id = String(fac.id)
      var v = Number(map[id])
      if (isNaN(v)) v = 0
      var objective = `ttl.rep.${id}`
      if (!board.getObjective(objective)) server.runCommandSilent(`scoreboard objectives add ${objective} dummy`)
      server.runCommandSilent(`scoreboard players set ${name} ${objective} ${v}`)
      var now = self.bandFor(id, v)
      self.BANDS.forEach(b => {
        var stage = `ttl.faction.${id}.${b}`
        if (b === now) {
          if (!player.stages.has(stage)) player.stages.add(stage)
        } else if (player.stages.has(stage)) {
          player.stages.remove(stage)
        }
      })
      if (mirror && fac.tensura_mirror) server.runCommandSilent(`quietly tensura edit stat ${name} reputation set ${v}`)
    })
    this.renown(server, player)
  },

  // ---- log and announcements -------------------------------------------------------------------------------

  log(server) {
    try {
      var raw = String(server.persistentData.getString('ttl.rep.log'))
      var list = raw ? JSON.parse(raw) : []
      return Array.isArray(list) ? list : []
    } catch (e) {
      console.error(`[ttl] rep: the reputation log is unreadable, starting a new one: ${e}`)
      return []
    }
  },

  note(server, player, f, delta, value, reason) {
    try {
      var list = this.log(server)
      list.push({ t: Date.now(), p: String(player.username), f: f, d: delta, v: value, r: String(reason || '') })
      var max = Number(this.rules().log_size)
      while (list.length > max) list.shift()
      var text = JSON.stringify(list)
      // An NBT string holds 64 KB; a long reason must never make the whole ring unwritable.
      while (text.length > 60000 && list.length > 1) {
        list.shift()
        text = JSON.stringify(list)
      }
      server.persistentData.putString('ttl.rep.log', text)
    } catch (e) {
      console.warn(`[ttl] rep: could not write the log: ${e}`)
    }
    console.info(`[ttl] rep: ${player.username} ${f} ${delta >= 0 ? '+' : ''}${delta} -> ${value}${reason ? ` (${reason})` : ''}`)
  },

  // First time at Exalted with this faction: one #story line (never for test bots, never twice).
  checkExalted(server, player, f, before, after) {
    try {
      var ex = this.rank('exalted')
      if (this.rank(this.bandFor(f, after)) < ex || this.rank(this.bandFor(f, before)) >= ex) return
      var data = player.persistentData
      var seen = String(data.getString('ttl.rep.exalted'))
      var done = seen ? seen.split(',') : []
      if (done.indexOf(f) >= 0) return
      done.push(f)
      data.putString('ttl.rep.exalted', done.join(','))
      var name = String(player.username)
      server.runCommandSilent(`tellraw @a ${JSON.stringify([
        { text: '[Voice of the World] ', color: 'gold' },
        { text: `Notice. ${name} is now Exalted with ${this.title(f)}.`, color: 'yellow' }
      ])}`)
      if (!TtlDiscord.isBot(name)) TtlDiscord.post(server, `${TtlDiscord.name(name)} is now Exalted with the ${this.title(f)}.`)
    } catch (e) {
      console.warn(`[ttl] rep: Exalted announcement failed: ${e}`)
    }
  },

  // ---- rebirth seeding -------------------------------------------------------------------------------------

  // Starting reputation: for every faction, the race entry plus each karma axis entry scaled by the axis score
  // (score / rules.seed_axis_cap, at most 1) plus `dark` for a Dark soul, summed and clamped. Overwrites old values.
  // corridor_flow.rebirth calls this once per reincarnation (race is passed in because ttl.race is cleared after).
  seed(server, player, race) {
    var name = String(player.username)
    var raceId = String(race || player.persistentData.getString('ttl.race')).replace(/^.*:/, '')
    var rec = null
    try {
      rec = TtlKarma.record(player)
    } catch (e) {
      console.warn(`[ttl] rep: ${name} has no readable karma record, seeding from race only: ${e}`)
    }
    var cap = Number(this.rules().seed_axis_cap)
    var map = {}
    var parts = []
    this.list().forEach(fac => {
      var id = String(fac.id)
      var seed = fac.seed || {}
      var v = 0
      var races = seed.race || {}
      if (races[raceId] !== undefined) v += Number(races[raceId])
      var axes = seed.axis || {}
      Object.keys(axes).forEach(a => {
        var score = rec && rec.axes && rec.axes[a] ? Number(rec.axes[a]) : 0
        if (score > 0) v += Number(axes[a]) * Math.min(score, cap) / cap
      })
      if (seed.dark !== undefined && rec && rec.dark) v += Number(seed.dark)
      v = this.clamp(v)
      map[id] = v
      if (v !== 0) parts.push(`${id}=${v}`)
    })
    this.write(player, map)
    // Stored ahead of the mirror so a failing Tensura command can never lose the seed.
    this.sync(server, player, true)
    this.note(server, player, '*', 0, 0, `seed ${raceId}: ${parts.join(' ') || 'all neutral'}`)
    return map
  },

  // ---- decay -----------------------------------------------------------------------------------------------

  // Every rules.decay_days real days each faction's value moves decay_per_week toward 0 (never past it). Offline
  // time counts: login (rep.js below) catches up. The first call only starts the clock.
  decay(server, player) {
    var data = player.persistentData
    var now = Date.now()
    var last = Number(data.getLong('ttl.rep.decayAt'))
    if (!last) {
      data.putLong('ttl.rep.decayAt', now)
      return 0
    }
    var period = Number(this.rules().decay_days) * this.DAY_MS
    var periods = Math.floor((now - last) / period)
    if (periods < 1) return 0
    data.putLong('ttl.rep.decayAt', last + periods * period)
    return this.drift(server, player, periods)
  },

  // Applies `periods` decay steps right now (also the test hook /ttl rep decay). Returns how many factions moved.
  drift(server, player, periods) {
    var map = this.read(player)
    var moved = 0
    var self = this
    this.list().forEach(fac => {
      var id = String(fac.id)
      var step = Number(fac.decay_per_week || 0) * periods
      var v = Number(map[id])
      if (isNaN(v) || v === 0 || step <= 0) return
      var next = v > 0 ? Math.max(0, v - step) : Math.min(0, v + step)
      if (next === v) return
      map[id] = next
      moved++
      self.note(server, player, id, next - v, next, 'decay')
    })
    if (moved > 0) {
      this.write(player, map)
      this.sync(server, player, true)
    }
    return moved
  },

  // ---- regions ---------------------------------------------------------------------------------------------

  warned: false,

  // The ttl-portals canon grid (the same one RegionTitles reads), or null before it is loaded.
  loadGrid() {
    try {
      var cls = Java.loadClass('com.yasuke.ttl.world.CanonMap')
      var g = cls.grid()
      return g || null
    } catch (e) {
      if (!this.warned) console.warn(`[ttl] rep: the canon grid is not available, region penalties are off: ${e}`)
      this.warned = true
      return null
    }
  },

  // A Java char may reach Rhino as a number or a string; normalise to a one-character string.
  ch(v) {
    return typeof v === 'number' ? String.fromCharCode(v) : String(v)
  },

  // Region letter of an overworld block column, by the RegionTitles.regionAt rule: the cell's letter, or for coastal
  // water ('.') its owner cell; null for '~', open sea and uncharted land.
  regionAt(x, z) {
    try {
      var g = this.loadGrid()
      if (!g) return null
      var cell = g.charAt(Math.floor(x), Math.floor(z))
      var c = this.ch(cell)
      if (c === '~') return null
      if (c !== '.') return g.region(c) ? c : null
      var owner = g.ownerCell(Math.floor(x), Math.floor(z))
      var oc = this.ch(owner)
      return oc !== '\u0000' && oc !== '0' && g.region(oc) ? oc : null
    } catch (e) {
      console.warn(`[ttl] rep: reading the region at ${x} ${z} failed: ${e}`)
      return null
    }
  },

  factionAt(x, z) {
    var letter = this.regionAt(x, z)
    if (!letter) return null
    var all = this.list()
    for (var i = 0; i < all.length; i++) {
      if (all[i].region && String(all[i].region) === letter) return all[i]
    }
    return null
  },

  // ---- renown ----------------------------------------------------------------------------------------------

  // Where a Life 2 soul's worth comes from (weights: factions.toml [renown]). Every part is read from state that
  // other systems already keep; a part that cannot be read counts 0 and logs once, it never breaks the total.
  renownParts(server, player) {
    var conf = this.conf().renown
    var parts = { tier: 0, bosses: 0, stages: 0, rep: 0, uniques: 0, bonus: 0, total: 0 }
    var phase = TtlLife.phase(player)
    if (phase === null || phase === 'life1') return parts
    var name = String(player.username)
    try {
      var tier = TtlKarma.tierOf(player)
      parts.tier = Number(conf.tier[String(tier.id)] || 0)
    } catch (e) {
      console.warn(`[ttl] rep: renown tier of ${name} unreadable: ${e}`)
    }
    Object.keys(conf.boss).forEach(stage => {
      if (player.stages.has(stage)) parts.bosses += Number(conf.boss[stage])
    })
    Object.keys(conf.stage).forEach(stage => {
      if (player.stages.has(stage)) parts.stages += Number(conf.stage[stage])
    })
    var map = this.all(player)
    this.ids().forEach(id => {
      parts.rep += Number(conf.band[this.bandFor(id, map[id])] || 0)
    })
    try {
      var held = TtlRegistry.heldBy(TtlRegistry.records(server), TtlRegistry.uid(player))
      held.forEach(skill => {
        parts.uniques += Number(conf.unique[TtlRegistry.rarityOf(skill)] || 0)
      })
    } catch (e) {
      console.warn(`[ttl] rep: renown uniques of ${name} unreadable: ${e}`)
    }
    parts.bonus = Number(player.persistentData.getInt('ttl.renown.bonus'))
    var total = parts.tier + parts.bosses + parts.stages + parts.rep + parts.uniques + parts.bonus
    parts.total = Math.max(Number(conf.min), Math.round(total))
    return parts
  },

  // Recomputes the renown and writes the mirrors (scoreboard ttl.renown, persistentData ttl.renown).
  renown(server, player) {
    var total = this.renownParts(server, player).total
    var name = String(player.username)
    try {
      var board = server.getScoreboard()
      if (!board.getObjective('ttl.renown')) server.runCommandSilent('scoreboard objectives add ttl.renown dummy')
      server.runCommandSilent(`scoreboard players set ${name} ttl.renown ${total}`)
      player.persistentData.putInt('ttl.renown', total)
    } catch (e) {
      console.warn(`[ttl] rep: could not mirror ${name}'s renown: ${e}`)
    }
    return total
  },

  addRenown(server, player, n, reason) {
    var data = player.persistentData
    data.putInt('ttl.renown.bonus', Math.round(Number(data.getInt('ttl.renown.bonus')) + Number(n)))
    var total = this.renown(server, player)
    console.info(`[ttl] rep: ${player.username} renown bonus ${n >= 0 ? '+' : ''}${n}${reason ? ` (${reason})` : ''} -> total ${total}`)
    return total
  },

  // ---- display ---------------------------------------------------------------------------------------------

  signed(v) {
    return v > 0 ? `+${v}` : String(v)
  },

  lines(player) {
    var out = []
    var self = this
    var map = this.all(player)
    this.list().forEach(fac => {
      var id = String(fac.id)
      if (fac.hidden && map[id] === 0) return
      var cap = fac.capital ? ` (${String(fac.capital).replace(/ \(.*$/, '')})` : ''
      out.push(`${fac.title}${cap}: ${self.bandTitle(self.bandFor(id, map[id]))} ${self.signed(map[id])}`)
    })
    return out
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlRep.ensure(server)
  } catch (e) {
    console.error(`[ttl] rep: creating the scoreboards failed: ${e}`)
  }
  // Renown follows bosses, uniques and quests that other scripts change, so it is refreshed every 5 minutes.
  var refresh = () => server.scheduleInTicks(6000, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlRep.renown(server, p)
      } catch (e) {
        console.error(`[ttl] rep: renown refresh for ${p.username} failed: ${e}`)
      }
    })
    refresh()
  })
  refresh()
  // Hourly decay for everyone online; a player who was away catches up at login.
  var loop = () => server.scheduleInTicks(72000, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) === 'life2') TtlRep.decay(server, p)
      } catch (e) {
        console.error(`[ttl] rep: decay for ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  try {
    if (TtlLife.phase(player) !== 'life2') return
    TtlRep.decay(server, player)
    TtlRep.sync(server, player, false)
  } catch (e) {
    console.error(`[ttl] rep: login sync for ${player.username} failed: ${e}`)
  }
})
