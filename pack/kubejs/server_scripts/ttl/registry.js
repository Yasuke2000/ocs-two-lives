// priority: 90
// Golden rule 1: every unique-skill grant or revoke goes through here.
// Uniques may be shared up to a cap per rarity (design/data/skills.toml → TtlData.skills). Legendary
// uniques are never drawn for a rebirth; they are only granted on purpose (admin, Legendary tier,
// absorption), up to their cap. Tensura's trulyUnique is off for this.
// Registry v2 (Sprint 3-4, S5): at most `max_holders` (10, the Ten Great Demon Lords) different players hold a
// Legendary unique at once, enforced on grant, available/draw and transfer; an optional per-era throttle
// (`slots_per_era`, 0 = off) limits NEW Legendary holders from rebirth picks (grant with opts.slot). transfer()
// moves a holder's unique to someone else by a named route (duel, war, bequest, awakening, staff ...);
// openCore() draws a Skill Core's unique. Admin grants and transfers never use a slot, but obey the global ceiling.
//
// Server persistentData (all JSON strings; one NBT string may not exceed 64 KB, so the history is trimmed by size):
//   ttl.reg.holders   {skill: [uuid, ...]}   who holds what. Keyed by player UUID, so a name change loses nothing.
//                     An entry that is not a UUID is a record from before the switch (a player name): migrate()
//                     turns it into a UUID once that player is online (or the profile cache knows the name).
//   ttl.reg.names     {uuid: name}           display names, refreshed on login/logout and every cycle
//   ttl.reg.seen      {uuid: millis}         last time each holder was online (return to pool, skills.toml [registry])
//   ttl.reg.returned  {uuid: [skill, ...]}   records returned to the pool while the player was away; the skill itself
//                     is taken from the player by reconcile() on their next login
//   ttl.reg.taken     {uuid: {skill: reason}} why a skill is waiting to be taken from an offline player (a transfer):
//                     reconcile() words its Voice line after it. Always together with an entry in ttl.reg.returned
//   ttl.reg.history   [{t, e, s, u, n, r, f?, fn?, v?}] append-only transfer log, capped (skills.toml history_max):
//                     time, event (grant | revoke | return | transfer), skill, uuid, name then, reason; a transfer
//                     is one entry for the receiver (u, n) with the giver in f / fn and the route in v
//   ttl.reg.legendarySlots {era: used}       Legendary slots spent per era; the era number is ttl.season (era/era.js).
//                     Keyed by era, so a new era starts with all slots free without any reset
// Uniques gained outside the registry (the Great Sage scene's wishes, Tensura's own Reset Counter bonus unique,
// admin commands) are caught by reconcile(), which reads what players really hold through TtlManas.
// Callers may still pass a player NAME where a holder is asked for (available/draw): resolve() maps it to a UUID.
// Test bots (TtlBot*) and real players count in separate pools (owner decision 20/11/2026): every cap, the Legendary
// ceiling and reconcile's "over its cap" see only holders of the asker's own kind (scoped()). Bots share the one
// holder map, but a real player's records never fill a bot's cap (tests pass whatever real players hold) and a test
// bot's records never fill a real player's. Nothing here ever changes or reads past a record of the other kind.
const TtlRegistry = {
  UUID: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
  // Persistent strings are written as modified UTF-8 with a 16-bit length: stay well below 65535.
  MAX_JSON: 60000,

  conf() {
    var r = TtlData.skills.registry || {}
    return {
      inactiveDays: r.inactive_days === undefined ? 30 : Number(r.inactive_days),
      historyMax: r.history_max ? Number(r.history_max) : 200,
      announce: r.announce || ['rare', 'legendary'],
      lookups: r.max_name_lookups ? Number(r.max_name_lookups) : 20
    }
  },

  // ---- eras and Legendary slots ----------------------------------------------------------------------

  // The current era: server `ttl.season` (era/era.js bumps it); 1 until anything has set it.
  era(server) {
    var n = Number(server.persistentData.getInt('ttl.season'))
    return n > 0 ? n : 1
  },

  // Test hook (/ttl registry legendcap): {max, slots} replacing the two TOML knobs until `legendcap reset`. With an `id`
  // they apply to test bots only: a real player always gets the shipped knobs, even when a test run was cut off before
  // its `legendcap reset`. Without an id (status lines, the test assertions) the test caps show while set.
  testCaps(server, id) {
    if (id !== undefined && id !== null && !this.isBotId(server, id)) return null
    return this.load(server, 'ttl.reg.testcaps', null)
  },

  // The global ceiling (owner decision: the Ten Great Demon Lords): at most this many DIFFERENT players hold a
  // Legendary unique at once, whatever the era. skills.toml [legendary] max_holders; 0 = no ceiling.
  maxHolders(server, id) {
    var o = this.testCaps(server, id)
    if (o && o.max !== undefined) return Number(o.max)
    var n = Number((TtlData.skills.legendary || {}).max_holders)
    return n >= 0 ? n : 10
  },

  // Optional per-era throttle on NEW Legendary holders from rebirth picks (skills.toml [legendary] slots_per_era);
  // 0 = none, and it can never exceed the global ceiling. Returns 0 for "no throttle".
  slotsPerEra(server, id) {
    var o = this.testCaps(server, id)
    var n = o && o.slots !== undefined ? Number(o.slots) : Number((TtlData.skills.legendary || {}).slots_per_era)
    if (!(n > 0)) return 0
    var max = this.maxHolders(server, id)
    return max > 0 ? Math.min(n, max) : n
  },

  slotLedger(server) {
    return this.load(server, 'ttl.reg.legendarySlots', {})
  },

  slotsUsed(server) {
    return Number(this.slotLedger(server)[String(this.era(server))] || 0)
  },

  // Slots left this era; -1 when there is no per-era throttle.
  slotsLeft(server, id) {
    var per = this.slotsPerEra(server, id)
    return per > 0 ? Math.max(0, per - this.slotsUsed(server)) : -1
  },

  // Different players holding any Legendary unique, from a records map ({skill: [id]}).
  legendaryHoldersIn(recs) {
    var ids = {}
    Object.keys(recs).forEach(skill => {
      if (this.rarityOf(skill) === 'legendary') recs[skill].forEach(id => { ids[id] = true })
    })
    return Object.keys(ids)
  },

  legendaryHolders(server) {
    return this.legendaryHoldersIn(this.records(server))
  },

  // May `id` hold a Legendary unique under the global ceiling? Yes when they already hold one (a second Legendary
  // adds no new holder) or when fewer than max_holders players do.
  canHoldLegendary(server, id, recs) {
    var max = this.maxHolders(server, id)
    if (!(max > 0)) return true
    var holders = this.legendaryHoldersIn(this.scoped(server, recs || this.records(server), id))
    return holders.indexOf(id) >= 0 || holders.length < max
  },

  // Legendary holders of the same kind as `id` (test bots or real players), for the refusal messages.
  legendaryHoldersFor(server, id) {
    return this.legendaryHoldersIn(this.scoped(server, this.records(server), id))
  },

  // Is a Legendary slot free this era? (Rebirth Legend picks.) Always true without a per-era throttle.
  legendarySlotFree(server, id) {
    return this.slotsPerEra(server, id) === 0 || this.slotsLeft(server, id) > 0
  },

  // Spends one slot of the current era; returns how many are used now. Eras more than nine back leave the ledger.
  useSlot(server) {
    var ledger = this.slotLedger(server)
    var era = this.era(server)
    ledger[String(era)] = Number(ledger[String(era)] || 0) + 1
    Object.keys(ledger).forEach(k => { if (Number(k) < era - 9) delete ledger[k] })
    this.store(server, 'ttl.reg.legendarySlots', ledger)
    return ledger[String(era)]
  },

  rarityOf(skill) {
    var path = String(skill).replace(/^.*:/, '')
    var s = TtlData.skills
    if (s.legendary.skills.indexOf(path) >= 0) return 'legendary'
    if (s.rare.skills.indexOf(path) >= 0) return 'rare'
    return 'common'
  },

  capOf(skill) {
    return TtlData.skills.caps[this.rarityOf(skill)]
  },

  // ---- identities ------------------------------------------------------------------------------------

  isId(x) {
    return this.UUID.test(String(x))
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  isBot(name) {
    return /^TtlBot/.test(String(name))
  },

  // Is the holder `id` (UUID or legacy name) a test bot? By its cached name, else an online player with that UUID,
  // else the entry itself (a legacy record is the name). `names` may be passed in to read it once per pass.
  isBotId(server, id, names) {
    var s = String(id)
    if (!this.isId(s)) return this.isBot(s)
    var n = (names || this.names(server))[s]
    if (n) return this.isBot(n)
    var bot = false
    server.getPlayerList().getPlayers().forEach(p => { if (this.uid(p) === s.toLowerCase()) bot = this.isBot(p.username) })
    return bot
  },

  // The records as `id` sees them: only holders of its own kind (test bots, or real players). A copy; never saved.
  scoped(server, recs, id) {
    return this.ofKind(server, recs, this.isBotId(server, id))
  },

  // Only the test bots' records (bot = true) or only the real players' (false). A copy; never saved.
  ofKind(server, recs, bot) {
    var names = this.names(server)
    var out = {}
    Object.keys(recs).forEach(skill => {
      var list = recs[skill].filter(h => this.isBotId(server, h, names) === !!bot)
      if (list.length > 0) out[skill] = list
    })
    return out
  },

  load(server, key, empty) {
    var raw = String(server.persistentData.getString(key))
    if (!raw) return empty
    try {
      return JSON.parse(raw)
    } catch (e) {
      console.error(`[ttl] registry: ${key} is unreadable (${e}); starting it empty`)
      return empty
    }
  },

  store(server, key, value) {
    server.persistentData.putString(key, JSON.stringify(value))
  },

  names(server) {
    return this.load(server, 'ttl.reg.names', {})
  },

  seen(server) {
    return this.load(server, 'ttl.reg.seen', {})
  },

  returned(server) {
    return this.load(server, 'ttl.reg.returned', {})
  },

  taken(server) {
    return this.load(server, 'ttl.reg.taken', {})
  },

  history(server) {
    return this.load(server, 'ttl.reg.history', [])
  },

  // Display name for a record entry: the cached player name, a legacy name as is, or a short UUID.
  nameOf(server, id) {
    var names = this.names(server)
    if (names[id]) return String(names[id])
    return this.isId(id) ? String(id).slice(0, 8) : String(id)
  },

  // A player name (online, or cached from an earlier login) or UUID → the key records use. An unknown name is
  // returned as is: that is how a not-yet-migrated record names its holder.
  resolve(server, who) {
    var s = String(who)
    if (this.isId(s)) return s.toLowerCase()
    var lower = s.toLowerCase()
    var found = null
    server.getPlayerList().getPlayers().forEach(p => {
      if (String(p.username).toLowerCase() === lower) found = this.uid(p)
    })
    if (found) return found
    var names = this.names(server)
    Object.keys(names).forEach(id => {
      if (String(names[id]).toLowerCase() === lower) found = id
    })
    return found || s
  },

  // The server's user cache (usercache.json), for names of players who are offline. Null when unknown. A name the
  // cache does not know may be looked up at Mojang, so callers keep the number of calls small.
  lookup(server, name) {
    try {
      // GameProfileCache has get(String) and get(UUID); Rhino picks the UUID one for a JS string and the
      // conversion throws a plain IllegalArgumentException that no JS catch sees. Name the overload.
      var cache = server.getProfileCache()
      var found = cache['get(java.lang.String)'](String(name))
      if (found && found.isPresent()) return String(found.get().getId()).toLowerCase()
    } catch (e) {
      console.warn(`[ttl] registry: profile cache lookup of ${name} failed: ${e}`)
    }
    return null
  },

  // Display names and last-seen for everyone online: one read and write per key for all players.
  touchOnline(server) {
    var names = this.names(server)
    var seen = this.seen(server)
    var now = Date.now()
    server.getPlayerList().getPlayers().forEach(p => {
      var id = this.uid(p)
      names[id] = String(p.username)
      seen[id] = now
    })
    this.store(server, 'ttl.reg.names', names)
    this.store(server, 'ttl.reg.seen', seen)
  },

  touch(server, player) {
    var id = this.uid(player)
    var names = this.names(server)
    var seen = this.seen(server)
    names[id] = String(player.username)
    seen[id] = Date.now()
    this.store(server, 'ttl.reg.names', names)
    this.store(server, 'ttl.reg.seen', seen)
  },

  // ---- records ---------------------------------------------------------------------------------------

  // {skill: [uuid | legacy name]}; what the registry itself works on.
  records(server) {
    var raw = String(server.persistentData.getString('ttl.reg.holders'))
    return raw ? JSON.parse(raw) : {}
  },

  save(server, records) {
    this.store(server, 'ttl.reg.holders', records)
  },

  // {skill: [display name]}: the read-only view for /ttl registry and the staff report.
  holders(server) {
    var recs = this.records(server)
    var out = {}
    Object.keys(recs).forEach(skill => { out[skill] = recs[skill].map(id => this.nameOf(server, id)) })
    return out
  },

  heldBy(records, id) {
    return Object.keys(records).filter(skill => records[skill].indexOf(id) >= 0).sort()
  },

  // `ttl.uniques` mirrors the holder map for /ttl inspect and bug reports.
  remember(server, player) {
    player.persistentData.putString('ttl.uniques', this.heldBy(this.records(server), this.uid(player)).join(','))
  },

  // Turns records that still name their holder (written before UUID keys) into UUID records, also in
  // last-seen and returned. A name resolves through the online players, the names seen at earlier logins and, when
  // `offline` (server start, /ttl registry migrate), the server's user cache. Anything else waits until that player
  // logs in. Returns how many entries were migrated.
  migrate(server, offline) {
    var recs = this.records(server)
    var names = this.names(server)
    var seen = this.seen(server)
    var back = this.returned(server)
    var online = {}
    server.getPlayerList().getPlayers().forEach(p => { online[String(p.username).toLowerCase()] = p })
    var budget = this.conf().lookups
    var cache = {}
    var count = 0
    var resolveLegacy = legacy => {
      var key = String(legacy).toLowerCase()
      if (cache[key] !== undefined) return cache[key]
      var id = null
      if (online[key]) {
        id = this.uid(online[key])
        names[id] = String(online[key].username)
      } else {
        Object.keys(names).forEach(i => { if (String(names[i]).toLowerCase() === key) id = i })
        if (!id && offline && budget > 0 && !this.isBot(legacy)) {
          budget--
          id = this.lookup(server, legacy)
          if (id && !names[id]) names[id] = String(legacy)
        }
      }
      cache[key] = id
      return id
    }
    var move = (obj, from, to, isList) => {
      if (obj[from] === undefined) return
      if (obj[to] === undefined) obj[to] = obj[from]
      else if (isList) obj[to] = obj[to].concat(obj[from].filter(x => obj[to].indexOf(x) < 0))
      else obj[to] = Math.max(obj[to], obj[from])
      delete obj[from]
    }
    Object.keys(recs).forEach(skill => {
      var out = []
      recs[skill].forEach(entry => {
        var id = this.isId(entry) ? String(entry).toLowerCase() : resolveLegacy(entry)
        if (id && !this.isId(entry)) {
          count++
          move(seen, entry, id, false)
          move(back, entry, id, true)
          console.info(`[ttl] registry: ${skill} record of ${entry} is now keyed by ${id}`)
        }
        var to = id || entry
        if (out.indexOf(to) < 0) out.push(to)
      })
      recs[skill] = out
    })
    // Last-seen and returned lists of legacy names whose records are gone already.
    ;[[seen, false], [back, true]].forEach(pair => {
      Object.keys(pair[0]).forEach(k => {
        if (this.isId(k)) return
        var id = resolveLegacy(k)
        if (id) {
          move(pair[0], k, id, pair[1])
          count++
        }
      })
    })
    if (count > 0) {
      this.save(server, recs)
      this.store(server, 'ttl.reg.names', names)
      this.store(server, 'ttl.reg.seen', seen)
      this.store(server, 'ttl.reg.returned', back)
    }
    return count
  },

  // ---- history and announcements ---------------------------------------------------------------------

  // Appends to the transfer log (capped by count and by size) and, for a Rare or Legendary unique, tells everyone.
  // `quiet` skips the announcement (admin clean-ups, a skill taken back that never had a record).
  log(server, event, skill, id, reason, quiet, extra) {
    var name = this.nameOf(server, id)
    var list = this.history(server)
    var entry = { t: Date.now(), e: event, s: String(skill), u: String(id), n: name, r: String(reason || '') }
    if (extra) Object.keys(extra).forEach(k => { entry[k] = extra[k] })
    list.push(entry)
    var max = this.conf().historyMax
    if (list.length > max) list = list.slice(list.length - max)
    while (list.length > 1 && JSON.stringify(list).length > this.MAX_JSON) list.shift()
    this.store(server, 'ttl.reg.history', list)
    try { if (typeof TtlChronicle !== 'undefined' && this.rarityOf(skill) === 'legendary') TtlChronicle.note(server, 'legendary', null, { event: String(event), skill: String(skill), name: String(name) }) } catch (e) { console.error(`[ttl] registry: chronicle note failed: ${e}`) }
    console.info(`[ttl] registry history: ${event} ${skill} ${name} (${reason || '-'})`)
    if (!quiet) this.announce(server, event, skill, name, extra && extra.fn)
  },

  // Voice of the World: a Rare or Legendary unique found or lost a holder. Test bots stay silent.
  // For a transfer `name` is the receiver and `from` the giver.
  announce(server, event, skill, name, from) {
    try {
      var rarity = this.rarityOf(skill)
      if (this.conf().announce.indexOf(rarity) < 0 || this.isBot(name) || (from && this.isBot(from))) return
      var title = TtlCorridor.title(skill)
      var kind = rarity === 'legendary' ? 'Legendary' : 'Rare'
      var text = event === 'grant'
        ? `${name} has become a holder of the ${kind} unique skill ${title}.`
        : event === 'transfer'
          ? `The ${kind} unique skill ${title} passes from ${from} to ${name}.`
          : event === 'return'
            ? `${name} has been away too long. The ${kind} unique skill ${title} returns to the world.`
            : `${name} no longer holds the ${kind} unique skill ${title}. It returns to the world.`
      server.runCommandSilent(`tellraw @a ${JSON.stringify([
        { text: '[Voice of the World] ', color: 'gold' },
        { text: `Notice. ${text}`, color: rarity === 'legendary' ? 'light_purple' : 'yellow' }
      ])}`)
    } catch (e) {
      console.warn(`[ttl] registry: announcement failed: ${e}`)
    }
  },

  // Oldest first. `skill` (with or without namespace) filters; `limit` keeps the newest n.
  historyLines(server, skill, limit) {
    var want = skill ? `tensura:${String(skill).replace(/^.*:/, '')}` : null
    var list = this.history(server).filter(h => !want || h.s === want)
    var shown = limit && list.length > limit ? list.slice(list.length - limit) : list
    return shown.map(h => `${new Date(h.t).toISOString().slice(0, 16).replace('T', ' ')} ${h.e} ${h.s} ${this.nameOf(server, h.u)}${h.f ? ` from ${this.nameOf(server, h.f)}` : ''}${h.v ? ` [${h.v}]` : ''}${h.r ? ` (${h.r})` : ''}`)
  },

  // ---- grants, draws, revokes ------------------------------------------------------------------------

  // Uniques from `pool` that `who` (name or UUID) could receive now: under their cap and not already theirs.
  // Legendary only when `allowLegendary` (deliberate grants, never rebirth draws, so draw() cannot hand one out),
  // and then only while the global ceiling leaves room for `who` as a Legendary holder (canHoldLegendary).
  available(server, pool, who, allowLegendary) {
    var id = this.resolve(server, who)
    var recs = this.scoped(server, this.records(server), id)
    var self = this
    var room = allowLegendary ? this.canHoldLegendary(server, id, recs) : false
    return pool.filter(skill => {
      if (self.rarityOf(skill) === 'legendary' && !(allowLegendary && room)) return false
      var list = recs[skill] || []
      return list.indexOf(id) < 0 && list.length < self.capOf(skill)
    })
  },

  // Up to n distinct grantable uniques from `pool`, in random order. Optional `weights` by rarity
  // ({common: 1, rare: 2}; a missing rarity weighs 1) makes some likelier — used by the karma tiers only.
  // Without it every unique is equally likely. Legendary stays excluded either way (available()).
  draw(server, pool, n, who, weights) {
    var free = this.available(server, pool, who)
    var out = []
    while (out.length < n && free.length > 0) {
      var i = weights ? this.weightedIndex(free, weights) : Math.floor(Math.random() * free.length)
      out.push(free.splice(i, 1)[0])
    }
    return out
  },

  weightedIndex(list, weights) {
    var self = this
    var w = list.map(id => {
      var x = weights[self.rarityOf(id)]
      return x === undefined ? 1 : Math.max(0, Number(x))
    })
    var total = w.reduce((a, b) => a + b, 0)
    if (total <= 0) return Math.floor(Math.random() * list.length)
    var r = Math.random() * total
    for (var i = 0; i < w.length; i++) {
      r -= w[i]
      if (r < 0) return i
    }
    return list.length - 1
  },

  // `opts.slot` (Legendary only): a NEW Legendary holder from a rebirth pick; needs a free slot this era and spends it.
  // Admin grants leave it out and may exceed the slots (the per-skill cap still applies).
  grant(server, player, skill, reason, opts) {
    var name = player.username
    var id = this.uid(player)
    var slot = !!(opts && opts.slot) && this.rarityOf(skill) === 'legendary'
    this.migrate(server, false)
    if (this.rarityOf(skill) === 'legendary' && !this.canHoldLegendary(server, id)) {
      console.warn(`[ttl] registry: refused ${skill} for ${name}: ${this.legendaryHoldersFor(server, id).length}/${this.maxHolders(server, id)} Legendary holders already`)
      return false
    }
    if (slot && !this.legendarySlotFree(server, id)) {
      console.warn(`[ttl] registry: refused ${skill} for ${name}: no Legendary slot left in era ${this.era(server)} (${this.slotsUsed(server)}/${this.slotsPerEra(server, id)})`)
      return false
    }
    if (this.available(server, [skill], id, true).length === 0) {
      console.warn(`[ttl] registry: refused ${skill} for ${name} (${this.rarityOf(skill)}, cap ${this.capOf(skill)} reached or already held)`)
      return false
    }
    server.runCommandSilent(`quietly tensura edit ability grant ${name} ${skill}`)
    var recs = this.records(server)
    recs[skill] = (recs[skill] || []).concat([id])
    this.save(server, recs)
    // A skill that was returned to the pool and is granted to the same player again is theirs again.
    var back = this.returned(server)
    if (back[id] && back[id].indexOf(skill) >= 0) {
      back[id] = back[id].filter(s => s !== skill)
      if (back[id].length === 0) delete back[id]
      this.store(server, 'ttl.reg.returned', back)
    }
    this.touch(server, player)
    this.remember(server, player)
    console.info(`[ttl] registry: ${skill} -> ${name} (${this.scoped(server, recs, id)[skill].length}/${this.capOf(skill)})`)
    var used = slot ? this.useSlot(server) : 0
    this.log(server, 'grant', skill, id, `${reason || 'granted through the registry'}${slot ? ` (Legendary slot ${used}/${this.slotsPerEra(server, id) || 'unlimited'}, era ${this.era(server)})` : ''}`)
    return true
  },

  // One skill only: `revoke <p> all` would also wipe race intrinsics and earned resistances.
  revoke(server, player, skill, reason) {
    var name = player.username
    var id = this.uid(player)
    server.runCommandSilent(`quietly tensura edit ability revoke ${name} ${skill}`)
    var recs = this.records(server)
    var had = !!(recs[skill] && recs[skill].indexOf(id) >= 0)
    if (recs[skill]) {
      recs[skill] = recs[skill].filter(n => n !== id)
      if (recs[skill].length === 0) delete recs[skill]
      this.save(server, recs)
    }
    this.remember(server, player)
    console.info(`[ttl] registry: revoked ${skill} from ${name}`)
    if (had) this.log(server, 'revoke', skill, id, reason || 'revoked through the registry')
  },

  // Every unique of the player, recorded or really held. Not `tensura reset <p> skill`: that rerolls one.
  revokeAll(server, player, reason) {
    var id = this.uid(player)
    var held = this.heldBy(this.records(server), id)
    ;(TtlManas.uniques(player) || []).forEach(s => { if (held.indexOf(s) < 0) held.push(s) })
    held.forEach(s => this.revoke(server, player, s, reason || 'character reset'))
    var back = this.returned(server)
    if (back[id]) {
      delete back[id]
      this.store(server, 'ttl.reg.returned', back)
    }
    player.persistentData.remove('ttl.uniques')
    console.info(`[ttl] registry: revoked all uniques of ${player.username} (${held.length})`)
  },

  // Brings the holder map in line with what the player really holds. A unique gained outside the registry
  // (a Great Sage wish, the bonus unique of Tensura's Reset Counter, an admin command) is recorded while its rarity
  // has room; over the cap, or a Legendary nobody granted, it is taken back and a free unique of the same rarity
  // is given instead, so a wish is never simply lost. Records that were returned to the pool while the player was
  // away are settled first: the skill is taken from them now, with a Voice line.
  reconcile(server, player) {
    var actual = TtlManas.uniques(player)
    if (actual === null) return
    var name = player.username
    var id = this.uid(player)
    var self = this
    this.migrate(server, false)
    this.touch(server, player)
    var back = this.returned(server)
    if (back[id]) {
      var giveBack = back[id]
      delete back[id]
      this.store(server, 'ttl.reg.returned', back)
      var whyAll = this.taken(server)
      var why = whyAll[id] || {}
      if (whyAll[id]) {
        delete whyAll[id]
        this.store(server, 'ttl.reg.taken', whyAll)
      }
      giveBack.forEach(skill => {
        if (actual.indexOf(skill) < 0) return
        server.runCommandSilent(`quietly tensura edit ability revoke ${name} ${skill}`)
        actual = actual.filter(s => s !== skill)
        TtlCorridor.voice(server, name, why[skill]
          ? `${TtlCorridor.title(skill)} was taken from you (${why[skill]}).`
          : `You were away too long. ${TtlCorridor.title(skill)} has returned to the world.`)
        console.info(`[ttl] registry: took ${skill} back from ${name}, returned to the pool while away`)
      })
    }
    var recs = this.records(server)
    var recorded = this.heldBy(recs, id)
    var refused = []
    var dropped = []
    var added = []
    recorded.forEach(skill => {
      if (actual.indexOf(skill) >= 0) return
      recs[skill] = recs[skill].filter(n => n !== id)
      if (recs[skill].length === 0) delete recs[skill]
      dropped.push(skill)
      console.info(`[ttl] registry: ${name} no longer holds ${skill}`)
    })
    var mine = this.scoped(server, recs, id)
    actual.forEach(skill => {
      if (recorded.indexOf(skill) >= 0) return
      var list = recs[skill] || []
      if (self.rarityOf(skill) === 'legendary' || (mine[skill] || []).length >= self.capOf(skill)) {
        refused.push(skill)
        return
      }
      recs[skill] = list.concat([id])
      mine[skill] = (mine[skill] || []).concat([id])
      added.push(skill)
      console.info(`[ttl] registry: recorded ${skill} for ${name}, gained outside the registry (${mine[skill].length}/${self.capOf(skill)})`)
    })
    this.save(server, recs)
    dropped.forEach(skill => this.log(server, 'revoke', skill, id, 'no longer held (reset, removed or lost outside the registry)'))
    added.forEach(skill => this.log(server, 'grant', skill, id, 'gained outside the registry (Reset Counter bonus, wish or admin)'))
    refused.forEach(skill => {
      var rarity = self.rarityOf(skill)
      console.warn(`[ttl] registry: ${name} gained ${skill} outside the registry over its cap (${rarity}); taking it back`)
      server.runCommandSilent(`quietly tensura edit ability revoke ${name} ${skill}`)
      self.log(server, 'revoke', skill, id, `taken back: ${rarity} unique over its cap`, true)
      var pool = rarity === 'legendary' ? [] : TtlData.skills[rarity].skills.map(p => `tensura:${p}`)
      var instead = self.draw(server, pool, 1, id)
      if (instead.length > 0 && self.grant(server, player, instead[0], `given instead of ${skill} (over its cap)`)) {
        TtlCorridor.voice(server, name, `${TtlCorridor.title(skill)} already has all the souls it can hold. ${TtlCorridor.title(instead[0])} answers your wish instead.`)
      } else {
        TtlCorridor.voice(server, name, `${TtlCorridor.title(skill)} already has all the souls it can hold, and no other skill answers.`)
      }
    })
    this.remember(server, player)
  },

  // Return to pool: a holder not seen for `inactive_days` loses the record. The skill stays on the player until
  // their next login (reconcile takes it, with a Voice line), or at once when they are online. The clock of a
  // holder with no last-seen yet starts now. Returns how many records were returned.
  sweep(server) {
    var days = this.conf().inactiveDays
    if (!(days > 0)) return 0
    var limit = days * 86400000
    var now = Date.now()
    var recs = this.records(server)
    var seen = this.seen(server)
    var back = this.returned(server)
    var ids = []
    Object.keys(recs).forEach(skill => recs[skill].forEach(id => { if (ids.indexOf(id) < 0) ids.push(id) }))
    var gone = []
    var stamped = false
    ids.forEach(id => {
      if (seen[id] === undefined) {
        seen[id] = now
        stamped = true
        return
      }
      if (now - seen[id] < limit) return
      this.heldBy(recs, id).forEach(skill => {
        recs[skill] = recs[skill].filter(n => n !== id)
        if (recs[skill].length === 0) delete recs[skill]
        back[id] = (back[id] || []).concat([skill])
        gone.push([skill, id])
      })
    })
    if (gone.length === 0) {
      if (stamped) this.store(server, 'ttl.reg.seen', seen)
      return 0
    }
    this.save(server, recs)
    this.store(server, 'ttl.reg.seen', seen)
    this.store(server, 'ttl.reg.returned', back)
    gone.forEach(g => this.log(server, 'return', g[0], g[1], `holder inactive for ${days}+ days`))
    // Anyone online settles at once instead of waiting for the next login.
    server.getPlayerList().getPlayers().forEach(p => {
      if (back[this.uid(p)]) this.reconcile(server, p)
    })
    return gone.length
  },

  // The periodic job (every five minutes, after the reconcile): names, last-seen, migration, return to pool.
  cycle(server) {
    this.touchOnline(server)
    this.migrate(server, false)
    this.sweep(server)
  },

  // ---- transfer and Skill Cores ----------------------------------------------------------------------

  // `who` as a holder: a player object, or a name / UUID. {id, player}; player is null while they are offline.
  party(server, who) {
    if (who && who.username !== undefined) return { id: this.uid(who), player: who }
    var id = this.resolve(server, who)
    var found = null
    server.getPlayerList().getPlayers().forEach(p => { if (this.uid(p) === id) found = p })
    return { id: id, player: found }
  },

  // Moves one unique from a holder to another player (absorption, an admin fix): revoke + grant in one step, ONE
  // history entry (`transfer`: the receiver in u/n, the giver in f/fn, the route in v), the Voice line and a #story
  // line for Rare and Legendary. `route` says HOW it moved and is free-form so several routes can coexist (skills.toml
  // [transfer] routes lists the known ones: duel, war, bequest, awakening, staff; an unknown one is logged but
  // accepted; none given = "staff"). A 5-argument call (the former `reason`) is read as the route. `from` may be offline (a combat-logger): their record moves at once and the skill is taken from them
  // at their next login (ttl.reg.returned + ttl.reg.taken, settled by reconcile). `to` must be online. It never
  // spends a Legendary slot and never changes how many hold the skill, so the per-skill cap cannot refuse it. The
  // global Legendary ceiling can: a Legendary may not go to a player who is not yet a Legendary holder when that
  // would put more than max_holders players over it (a giver who loses their last Legendary frees their place).
  // False (logged) when `from` is not a recorded holder, `to` already holds it, they are the same soul, or the
  // ceiling forbids it.
  transfer(server, from, to, skill, route, reason) {
    this.migrate(server, false)
    var src = this.party(server, from)
    var dst = this.party(server, to)
    var way = String(route || 'staff').toLowerCase().replace(/[^a-z0-9_]/g, '_')
    if ((TtlData.skills.transfer || {}).routes && TtlData.skills.transfer.routes.indexOf(way) < 0) {
      console.warn(`[ttl] registry: transfer route ${way} is not listed in skills.toml [transfer] routes`)
    }
    var why = reason ? `${way}: ${reason}` : way
    var recs = this.records(server)
    var list = recs[skill] || []
    var refuse = text => {
      console.warn(`[ttl] registry: refused transfer of ${skill} from ${src.id} to ${dst.id}: ${text}`)
      return false
    }
    if (!dst.player) return refuse('the receiver is not online')
    if (src.id === dst.id) return refuse('giver and receiver are the same player')
    if (list.indexOf(src.id) < 0) return refuse('the giver is not a recorded holder')
    if (list.indexOf(dst.id) >= 0) return refuse('the receiver already holds it')
    if (this.rarityOf(skill) === 'legendary' && !this.canHoldLegendary(server, dst.id, recs)) {
      // The receiver is a new Legendary holder at the ceiling: allowed only if the giver stops being one.
      var stays = this.heldBy(recs, src.id).filter(sk => sk !== skill && this.rarityOf(sk) === 'legendary').length > 0
      if (stays) return refuse(`${this.legendaryHoldersFor(server, dst.id).length}/${this.maxHolders(server, dst.id)} Legendary holders already`)
    }
    var fromName = this.nameOf(server, src.id)
    if (src.player) {
      server.runCommandSilent(`quietly tensura edit ability revoke ${src.player.username} ${skill}`)
    } else {
      var waiting = this.returned(server)
      if ((waiting[src.id] || []).indexOf(skill) < 0) waiting[src.id] = (waiting[src.id] || []).concat([skill])
      this.store(server, 'ttl.reg.returned', waiting)
      var taken = this.taken(server)
      taken[src.id] = taken[src.id] || {}
      taken[src.id][skill] = why
      this.store(server, 'ttl.reg.taken', taken)
    }
    server.runCommandSilent(`quietly tensura edit ability grant ${dst.player.username} ${skill}`)
    recs[skill] = list.filter(n => n !== src.id).concat([dst.id])
    this.save(server, recs)
    // A skill that was waiting to be taken from the receiver and is theirs again is no longer waiting.
    var mine = this.returned(server)
    if (mine[dst.id] && mine[dst.id].indexOf(skill) >= 0) {
      mine[dst.id] = mine[dst.id].filter(s => s !== skill)
      if (mine[dst.id].length === 0) delete mine[dst.id]
      this.store(server, 'ttl.reg.returned', mine)
    }
    this.touch(server, dst.player)
    this.remember(server, dst.player)
    if (src.player) this.remember(server, src.player)
    console.info(`[ttl] registry: ${skill} ${fromName} -> ${dst.player.username} (${why})`)
    this.log(server, 'transfer', skill, dst.id, why, false, { f: src.id, fn: fromName, v: way })
    this.story(server, skill, fromName, String(dst.player.username))
    return true
  },

  // #story line for a transfer of a Rare or Legendary unique, through TtlDiscord when it is there (one post per event).
  story(server, skill, fromName, toName) {
    try {
      if (typeof TtlDiscord === 'undefined') return
      var rarity = this.rarityOf(skill)
      if (this.conf().announce.indexOf(rarity) < 0) return
      var kind = rarity === 'legendary' ? 'Legendary' : 'Rare'
      TtlDiscordStory.post(server, rarity + '_transfer', [fromName, toName], `The ${kind} unique skill ${TtlCorridor.title(skill)} passes from ${TtlDiscord.name(fromName)} to ${TtlDiscord.name(toName)}.`)
    } catch (e) {
      console.warn(`[ttl] registry: story line for the transfer failed: ${e}`)
    }
  },

  // Every Rare and Common unique (never Legendary): what a Skill Core can hold.
  corePool() {
    return ['rare', 'common'].reduce((all, r) => all.concat(TtlData.skills[r].skills.map(p => `tensura:${p}`)), [])
  },

  coreWeights() {
    return (TtlData.skills.core || {}).weights || { rare: 3, common: 1 }
  },

  // The unique an opening Skill Core would give this player: one weighted draw (skills.toml [core] weights) from the
  // Rare and Common uniques they do not hold and that are under their cap. Null when nothing is free. Grants nothing.
  coreDraw(server, player) {
    var picked = this.draw(server, this.corePool(), 1, this.uid(player), this.coreWeights())
    return picked.length > 0 ? picked[0] : null
  },

  // Opens a Skill Core: draw + grant. The skill, or null (nothing free, or the grant was refused).
  openCore(server, player, reason) {
    var skill = this.coreDraw(server, player)
    if (!skill) return null
    return this.grant(server, player, skill, reason || 'opened a Skill Core') ? skill : null
  },

  // Name the Legendary/absorption package expects for the return-to-pool sweep.
  returnInactive(server) {
    return this.sweep(server)
  },

  // Admin: drop every record of `skill` (its holders left or were reset by hand).
  free(server, skill) {
    var recs = this.records(server)
    ;(recs[skill] || []).forEach(id => this.log(server, 'revoke', skill, id, 'released by an admin', true))
    delete recs[skill]
    this.save(server, recs)
  },

  // Test hook (/ttl registry seen): pretend the player was last online `days` days ago.
  fakeSeen(server, who, days) {
    var id = this.resolve(server, who)
    var seen = this.seen(server)
    seen[id] = Date.now() - Number(days) * 86400000
    this.store(server, 'ttl.reg.seen', seen)
    return id
  },

  // Test hook (/ttl registry legacy): rewrite the player's records the way they were stored before UUID keys.
  fakeLegacy(server, player) {
    var id = this.uid(player)
    var recs = this.records(server)
    var n = 0
    Object.keys(recs).forEach(skill => {
      var i = recs[skill].indexOf(id)
      if (i < 0) return
      recs[skill][i] = String(player.username)
      n++
    })
    var names = this.names(server)
    delete names[id]
    this.store(server, 'ttl.reg.names', names)
    this.save(server, recs)
    return n
  }
}

// Names and last-seen at login; reconcile shortly after (the Great Sage scene needs a moment to settle).
PlayerEvents.loggedIn(event => {
  var { player, server } = event
  try {
    TtlRegistry.touch(server, player)
    TtlRegistry.migrate(server, false)
  } catch (e) {
    console.error(`[ttl] registry: login bookkeeping for ${player.username} failed: ${e}`)
  }
  server.scheduleInTicks(60, () => TtlRegistry.reconcile(server, player))
})

try {
  PlayerEvents.loggedOut(event => {
    try {
      TtlRegistry.touch(event.server, event.player)
    } catch (e) {
      console.error(`[ttl] registry: logout bookkeeping failed: ${e}`)
    }
  })
} catch (e) {
  console.warn(`[ttl] registry: cannot watch logouts, last-seen is refreshed every cycle only: ${e}`)
}

// Start-up: migrate name-keyed records (user cache included), then every five minutes for everyone online:
// reconcile (catches skills from any source), then names, last-seen, migration and return to pool.
ServerEvents.loaded(event => {
  var server = event.server
  try {
    var migrated = TtlRegistry.migrate(server, true)
    if (migrated > 0) console.info(`[ttl] registry: migrated ${migrated} name-keyed records to UUIDs at start`)
    TtlRegistry.sweep(server)
  } catch (e) {
    console.error(`[ttl] registry: start-up migration failed: ${e}`)
  }
  var loop = () => server.scheduleInTicks(6000, () => {
    try {
      server.getPlayerList().getPlayers().forEach(p => TtlRegistry.reconcile(server, p))
      TtlRegistry.cycle(server)
    } catch (e) {
      console.error(`[ttl] registry: periodic cycle failed: ${e}`)
    }
    loop()
  })
  loop()
})
