// priority: 72
// The World Chronicle and the continent line (design/architecture/world-state.md §2.0, §2.2, §3; WP-W1).
// Data and numbers: design/data/world.toml → TtlData.world. Commands: world/commands.js.
//
// R5 one-way flow: personal and party events are counted INTO the world; the world never writes personal story state.
// What it hands a soul is additive: stages ttl.world.*, scoreboards, Voice lines, #story lines, events unlocked, moods.
// R10: milestones are sticky for the era; only `balance`/`tide` and `rule` are reversible, and they only choose content.
// R11: every story rule asks TtlWorld.onContinent first; outside the canon continent the mods behave as shipped.
//
// Storage
//   server  ttl.world           JSON {v, era, since, counts, firsts, phases, milestones, balance, tide, decayAt, rule,
//                               conflicts, active}; written here only, kept under [chronicle] max_json
//           ttl.world.log       ring [{t, kind, who, data}] ([chronicle] log_size)
//           ttl.world.archive   [{era, ended, world}] one snapshot per finished era ([chronicle] archive_max)
//           ttl.world.souls     compound {uuid: JSON {n, s, p, k}} the LEDGER: per Life 2 soul its name, last seen, current
//                               path and the deeds it has contributed once (k: a.<path>.<act> · f.<flag> · x.<flip> · o.<path> ·
//                               k.<boss> · w.<boss>). Soul counts are derived from it, so a note and a login backfill never
//                               count one soul twice and `/ttl world recount` is exact for offline souls too.
//           ttl.world.unlocked  JSON [event ids] milestone unlocks (sticky) + the current tide's
//           ttl.world.mood      JSON {faction: bands} milestone moods (sticky) + the current tide's
//           ttl.world.loop      sync loop stamp (reload-safe)
//           ttl.world.testmark(.world|.log|.archive|.souls|.unlocked|.mood), ttl.world.testthreshold   test hooks
//   player  ttl.world.counted   backfill version (int), ttl.world.seen JSON {milestoneId: epoch} Voice lines heard
//   stages  (every online Life 2 soul, at login and every sync) milestone `stage` and `chapter` (ttl.world.chapter.<key>)
//           (additive), ttl.world.phase.<place>.<phase> up to the current phase, ttl.world.tide.light|dark,
//           ttl.world.conflict.<f>, ttl.world.rule.<f>.<mode> (exact mirrors)
//   scores  ttl.world.balance (rounded) and ttl.world.phase.<place> (phase index) per online Life 2 soul and #world
//
// Test bots (names TtlBot*) count only while `/ttl world testmark` is set: the mark saves the world, blanks it for the
// test and `/ttl world testrestore` puts it back, so a test run never moves the real world. An era turn under an era
// test mark (`/ttl era testmark`) does not archive the world either.
//
// PUBLIC API (other packages call these, always guarded with typeof; `player` is a ServerPlayer or null)
//   TtlWorld.onContinent(dim, x, z)           true on the canon continent (rivers and near-coast water included) and in
//                                             the [continent] inside_dimensions; false in the ring, the free lands and
//                                             every other dimension. TtlWorld.onContinentEntity(e) for an entity.
//   TtlWorld.ownerAt(x, z)                    the canon letter owning an overworld column ('' = none)
//   TtlChronicle.note(server, kind, player, data)   count one deed (kinds below); evaluates milestones
//   TtlChronicle.bossKill(server, bossId, rec, names)  boss.js `finish`: kills per credited soul, firsts, outside kills
//   TtlChronicle.count(server, path)          a number from counts by dotted path ('acts.light.2'), 0 when absent
//   TtlChronicle.balance(server) · addBalance(server, n, why) · tide(server) ('' | 'light' | 'dark')
//   TtlChronicle.milestones(server) {id: epoch} · reached(server, id) · fire(server, id, by)
//   TtlChronicle.phase(server, place) · setPhase(server, place, phase, by) · onPhase(place, fn(server, phase, by))
//   TtlChronicle.mood(f) bands (cached; TtlRep reads it for guards and shops) · moods(server)
//   TtlChronicle.unlocked(server) [event ids] · isUnlocked(server, id)
//   TtlChronicle.conflict(server, f) record|null · openConflict / closeConflict(server, f, by)
//   TtlChronicle.rule(server, f) {nation, mode, since, by}|null · setRule(server, f, nation, mode, by) · clearRule(server, f, by)
//   TtlChronicle.setActive(server, key, untilEpoch) · active(server, key) (e.g. `rebuilding`, WP-W9)
//   TtlChronicle.sync(server, player)         rewrite this soul's mirrors (login does it; ops: /ttl world sync)
//   TtlChronicle.view(server)                 the radiant/NPC view {era, tide, balance, phases, milestones, conflicts, mood,
//                                             rule, unlocked, active, wild, counts}
//   TtlChronicle.export(server)               one JSON line for Discord/BlueMap/Hall (WP-W10)
//   TtlChronicle.lines(server)                /ttl world
//   TtlChronicle.archive(server, oldEra, newEra)   era.js `next`: snapshot, balance and tide reset; the rest is kept (§7.4)
// note() kinds and data:
//   oath {path} · act {act, path?, catchup?} · flip {kind: atonement|corruption} · flag {flag}      per soul, once
//   kill {boss, wild?} (prefer bossKill) · kill_outside {} · nation_found {key, name} · nation_dropped {key, name}
//   war_declared {a, b} · war_ended {a, b, winner?} · muster {key, n} · raid {result: defended|sacked}
//   uprising {result: put_down|won} · radiant {faction, path?} · legendary {event, skill, name}
//   any other kind: {count: '<dotted counts path to +1>', weight: '<[balance.weights] key>'}
const TtlWorld = {
  cells: {},
  size: 0,
  gridObj: undefined,
  warned: false,

  conf() {
    return (TtlData.world && TtlData.world.continent) || {}
  },

  grid() {
    if (this.gridObj) return this.gridObj
    try {
      var g = Java.loadClass('com.yasuke.ttl.world.CanonMap').grid()
      if (g) this.gridObj = g
      return g || null
    } catch (e) {
      if (!this.warned) console.warn(`[ttl] world: the canon grid is not available, the continent test falls back to ${this.conf().fallback_inside === false ? 'outside' : 'inside'}: ${e}`)
      this.warned = true
      return null
    }
  },

  // A Java char reaches Rhino as a number or a one-character string; '' for "no owner".
  letter(v) {
    if (v === null || v === undefined) return ''
    var s = typeof v === 'number' ? String.fromCharCode(v) : String(v)
    return s === '\u0000' || s === '0' || s === '' ? '' : s
  },

  ownerAt(x, z) {
    var g = this.grid()
    if (!g) return ''
    try {
      return this.letter(g.ownerCell(Math.floor(Number(x)), Math.floor(Number(z))))
    } catch (e) {
      console.warn(`[ttl] world: reading the owner at ${x} ${z} failed: ${e}`)
      return ''
    }
  },

  // The grid's owner array is per chunk; remember the answer per chunk column.
  onContinent(dim, x, z) {
    var c = this.conf()
    dim = String(dim)
    if ((c.inside_dimensions || []).indexOf(dim) >= 0) return true
    if (dim !== String(c.overworld || 'minecraft:overworld')) return false
    var key = `${Math.floor(Number(x)) >> 4},${Math.floor(Number(z)) >> 4}`
    var hit = this.cells[key]
    if (hit !== undefined) return hit
    var g = this.grid()
    if (!g) return c.fallback_inside !== false
    var inside = this.ownerAt(x, z) !== ''
    if (this.size >= Number(c.cache_max || 4096)) {
      this.cells = {}
      this.size = 0
    }
    this.cells[key] = inside
    this.size++
    return inside
  },

  onContinentEntity(e) {
    return this.onContinent(String(e.level.dimension), e.x, e.z)
  },

  // {inside, owner, region} for /ttl world where and at.
  describe(dim, x, z) {
    var owner = String(dim) === String(this.conf().overworld || 'minecraft:overworld') ? this.ownerAt(x, z) : ''
    var region = ''
    try {
      var g = this.grid()
      if (g && owner) region = String(g.regionName(owner.charAt(0)) || '')
    } catch (e) {
      region = ''
    }
    return { inside: this.onContinent(dim, x, z), owner: owner, region: region, grid: !!this.grid() }
  }
}

const TtlChronicle = {
  V: 2,
  K: 'ttl.world',
  K_LOG: 'ttl.world.log',
  K_ARCHIVE: 'ttl.world.archive',
  K_SOULS: 'ttl.world.souls',
  K_UNLOCKED: 'ttl.world.unlocked',
  K_MOOD: 'ttl.world.mood',
  K_LOOP: 'ttl.world.loop',
  K_MARK: 'ttl.world.testmark',
  K_TEST_THRESHOLD: 'ttl.world.testthreshold',
  P_COUNTED: 'ttl.world.counted',
  P_SEEN: 'ttl.world.seen',
  DAY: 86400000,
  WEEK: 604800000,
  LANES: ['light', 'dark'],
  FLIPS: ['atonement', 'corruption'],
  world: null,
  moodCache: null,
  unlockedCache: null,
  phaseHooks: {},

  // ---- data -------------------------------------------------------------------------------------------------

  conf() {
    return TtlData.world
  },

  chron() {
    return this.conf().chronicle
  },

  defs() {
    return this.conf().milestone || []
  },

  def(id) {
    var all = this.defs()
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === String(id)) return all[i]
    }
    return null
  },

  places() {
    return this.conf().places || {}
  },

  modes() {
    return (this.conf().rule || {}).modes || []
  },

  factionIds() {
    var out = []
    try {
      ;(TtlData.factions.faction || []).forEach(f => out.push(String(f.id)))
    } catch (e) {
      // no factions table: only the pending ones
    }
    ;(this.chron().pending_factions || []).forEach(f => { if (out.indexOf(String(f)) < 0) out.push(String(f)) })
    return out
  },

  readJson(holder, key, fallback) {
    try {
      var raw = String(holder.getString(key))
      if (!raw) return fallback
      var parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : fallback
    } catch (e) {
      console.error(`[ttl] world: ${key} is unreadable, treating it as empty: ${e}`)
      return fallback
    }
  },

  isBot(name) {
    return /^TtlBot/.test(String(name))
  },

  testMode(server) {
    return String(server.persistentData.getString(this.K_MARK)) !== ''
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  // Souls the chronicle counts: Life 2, and test bots only under a test mark.
  countable(server, player) {
    if (!player) return false
    if (TtlLife.phase(player) !== 'life2') return false
    return !this.isBot(player.username) || this.testMode(server)
  },

  eraNumber(server) {
    try {
      if (typeof TtlEra !== 'undefined') return Number(TtlEra.number(server))
    } catch (e) {
      // fall through
    }
    var n = Number(server.persistentData.getInt('ttl.season'))
    return n > 0 ? n : 1
  },

  // ---- the record -------------------------------------------------------------------------------------------

  emptyCounts() {
    return {
      souls: 0, active30: 0,
      oaths: { light: 0, dark: 0 }, acts: { light: {}, dark: {} }, reached: {},
      flips: { atonement: 0, corruption: 0 }, flags: {}, kills: {}, wildKills: { outside: 0 },
      nations: 0, wars: 0, armies: {}, raidsWon: { defenders: 0, raiders: 0 }, uprisings: { put_down: 0, won: 0 },
      radiant: {}, legendary: { holders: 0, moves: 0 }
    }
  },

  blank(server) {
    var now = Date.now()
    var phases = {}
    var places = this.places()
    Object.keys(places).forEach(p => { phases[p] = String(places[p][0]) })
    return {
      v: this.V, era: this.eraNumber(server), since: now, counts: this.emptyCounts(), firsts: {}, phases: phases,
      milestones: {}, balance: 0, tide: '', decayAt: now, rule: {}, conflicts: {}, active: {}
    }
  },

  // Older or partial records gain the fields they miss; new places start at their first phase.
  fill(server, w) {
    var b = this.blank(server)
    Object.keys(b).forEach(k => { if (w[k] === undefined || w[k] === null) w[k] = b[k] })
    var ec = this.emptyCounts()
    Object.keys(ec).forEach(k => { if (w.counts[k] === undefined) w.counts[k] = ec[k] })
    Object.keys(b.phases).forEach(p => { if (!w.phases[p]) w.phases[p] = b.phases[p] })
    w.v = this.V
    return w
  },

  load(server) {
    if (this.world) return this.world
    var w = this.readJson(server.persistentData, this.K, null)
    if (!w) {
      w = this.blank(server)
      if (!this.testMode(server)) this.seed(server, w)
      this.world = w
      this.save(server, w)
      console.info(`[ttl] world: the chronicle begins (era ${w.era}; firsts seeded: ${Object.keys(w.firsts).length})`)
      return w
    }
    this.world = this.fill(server, w)
    return this.world
  },

  save(server, w) {
    var text = JSON.stringify(w)
    var max = Number(this.chron().max_json)
    if (text.length > max) console.error(`[ttl] world: ttl.world is ${text.length} characters (over max_json ${max}): trim counts.armies or firsts`)
    server.persistentData.putString(this.K, text)
    this.world = w
  },

  // First boot (§9): firsts from the story log ("killed <boss>: ...") and the Legendary tally from the registry.
  seed(server, w) {
    try {
      var log = this.readJson(server.persistentData, 'ttl.story.log', [])
      if (Array.isArray(log)) {
        log.forEach(e => {
          var m = /^killed ([a-z0-9_]+)/.exec(String(e.e || ''))
          if (!m || this.isBot(e.p)) return
          var id = m[1]
          if (!w.firsts[id] || Number(w.firsts[id].at) > Number(e.t)) w.firsts[id] = { by: String(e.p), party: '', at: Number(e.t), seeded: true }
        })
      }
    } catch (err) {
      console.warn(`[ttl] world: seeding firsts from the story log failed: ${err}`)
    }
    try {
      if (typeof TtlRegistry !== 'undefined') {
        var moves = 0
        TtlRegistry.history(server).forEach(h => {
          if (h.e === 'transfer' && TtlRegistry.rarityOf(h.s) === 'legendary') moves++
        })
        w.counts.legendary = { holders: TtlRegistry.legendaryHolders(server).length, moves: moves }
      }
    } catch (err) {
      console.warn(`[ttl] world: seeding the Legendary tally failed: ${err}`)
    }
  },

  // ---- the ledger -------------------------------------------------------------------------------------------

  soulBox(server) {
    return server.persistentData.getCompound(this.K_SOULS)
  },

  soul(server, uuid) {
    var box = this.soulBox(server)
    if (!box.contains(uuid)) return null
    try {
      var s = JSON.parse(String(box.getString(uuid)))
      if (!s.k) s.k = {}
      return s
    } catch (e) {
      console.error(`[ttl] world: ledger entry ${uuid} is unreadable, starting it again: ${e}`)
      return null
    }
  },

  putSoul(server, uuid, s) {
    var box = this.soulBox(server)
    box.putString(uuid, JSON.stringify(s))
    server.persistentData.put(this.K_SOULS, box)
  },

  eachSoul(server, fn) {
    var box = this.soulBox(server)
    var keys = []
    box.getAllKeys().forEach(k => keys.push(String(k)))
    keys.forEach(k => {
      try {
        var s = JSON.parse(String(box.getString(k)))
        if (!s.k) s.k = {}
        fn(k, s)
      } catch (e) {
        console.error(`[ttl] world: ledger entry ${k} is unreadable, skipped: ${e}`)
      }
    })
  },

  // Records the soul as seen now with its current path and adds deed keys; returns the keys that were new.
  touch(server, player, keys) {
    var u = this.uid(player)
    var s = this.soul(server, u) || { n: '', s: 0, p: '', k: {} }
    s.n = String(player.username)
    s.s = Date.now()
    s.p = typeof TtlStory !== 'undefined' ? TtlStory.path(player) : ''
    var added = []
    ;(keys || []).forEach(k => {
      if (!s.k[k]) {
        s.k[k] = 1
        added.push(k)
      }
    })
    this.putSoul(server, u, s)
    return added
  },

  // Deed keys from the soul's own state (login backfill, §3.1). Acts before the backfill existed count on the soul's
  // current path: the path at the time was not recorded.
  soulKeys(player) {
    var keys = []
    if (typeof TtlStory !== 'undefined') {
      var path = TtlStory.path(player)
      if (path) keys.push(`o.${path}`)
      var acts = TtlStory.actsOf(player)
      Object.keys(acts).forEach(n => { if (path) keys.push(`a.${path}.${n}`) })
      Object.keys(TtlStory.flagsOf(player)).forEach(f => keys.push(`f.${f}`))
      if (TtlStory.flips(player) > 0 && path) keys.push(`x.${path === 'light' ? 'atonement' : 'corruption'}`)
    }
    var kills = this.readJson(player.persistentData, 'ttl.boss.kills', {})
    Object.keys(kills).forEach(id => { if (Number(kills[id]) > 0) keys.push(`k.${id}`) })
    return keys
  },

  backfill(server, player) {
    var added = this.touch(server, player, this.soulKeys(player))
    player.persistentData.putInt(this.P_COUNTED, this.V)
    if (added.length) console.info(`[ttl] world: backfilled ${player.username}: ${added.join(', ')}`)
    return added
  },

  // Soul counts from the ledger; event tallies (nations, wars, radiant ...) stay as they are.
  recount(server, w) {
    var c = w.counts
    var now = Date.now()
    var windowMs = Number(this.chron().active_window_days) * this.DAY
    var test = this.testMode(server)
    c.souls = 0
    c.active30 = 0
    c.oaths = { light: 0, dark: 0 }
    c.acts = { light: {}, dark: {} }
    c.reached = {}
    c.flips = { atonement: 0, corruption: 0 }
    c.flags = {}
    c.kills = {}
    var outside = Number((c.wildKills || {}).outside || 0)
    c.wildKills = { outside: outside }
    var add = (table, key) => { table[key] = Number(table[key] || 0) + 1 }
    this.eachSoul(server, (u, s) => {
      if (!test && this.isBot(s.n)) return
      c.souls++
      if (now - Number(s.s || 0) <= windowMs) c.active30++
      if (s.p === 'light' || s.p === 'dark') c.oaths[s.p]++
      var reached = {}
      Object.keys(s.k).forEach(k => {
        var parts = k.split('.')
        var head = parts[0]
        if (head === 'a' && parts.length === 3 && c.acts[parts[1]]) {
          add(c.acts[parts[1]], parts[2])
          reached[parts[2]] = true
        } else if (head === 'f') {
          add(c.flags, parts.slice(1).join('.'))
        } else if (head === 'x' && c.flips[parts[1]] !== undefined) {
          c.flips[parts[1]]++
        } else if (head === 'k') {
          add(c.kills, parts.slice(1).join('.'))
        } else if (head === 'w') {
          add(c.wildKills, parts.slice(1).join('.'))
        }
      })
      Object.keys(reached).forEach(n => add(c.reached, n))
    })
    return c
  },

  // ---- thresholds and conditions ------------------------------------------------------------------------------

  threshold(server, w) {
    var t = this.conf().threshold
    var test = this.readJson(server.persistentData, this.K_TEST_THRESHOLD, null)
    var souls = test ? Number(test.souls) : Number(t.souls)
    var pct = test ? Number(test.pct) : Number(t.pct)
    return Math.max(souls, Math.ceil((pct / 100) * Number(w.counts.active30 || 0)))
  },

  num(v) {
    var n = Number(v)
    return isNaN(n) ? 0 : n
  },

  met(server, w, when) {
    var c = w.counts
    var need = this.threshold(server, w)
    var ok = true
    var every = (table, src) => {
      Object.keys(table).forEach(k => { if (this.num(src[k]) < Number(table[k])) ok = false })
    }
    if (when.acts && this.num(c.reached[String(when.acts.act)]) < need) ok = false
    if (when.acts_path && this.num((c.acts[when.acts_path.path] || {})[String(when.acts_path.act)]) < need) ok = false
    if (when.flags) every(when.flags, c.flags)
    if (when.kills) every(when.kills, c.kills)
    if (when.radiant) every(when.radiant, c.radiant)
    if (when.nations !== undefined && this.num(c.nations) < Number(when.nations)) ok = false
    if (when.wars !== undefined && this.num(c.wars) < Number(when.wars)) ok = false
    if (when.armies !== undefined) {
      var armies = Object.keys(c.armies || {}).filter(k => this.num(c.armies[k]) > 0).length
      if (armies < Number(when.armies)) ok = false
    }
    if (when.balance_at_least !== undefined && this.num(w.balance) < Number(when.balance_at_least)) ok = false
    if (when.balance_at_most !== undefined && this.num(w.balance) > Number(when.balance_at_most)) ok = false
    if (when.milestone !== undefined && !w.milestones[String(when.milestone)]) ok = false
    if (when.era_days !== undefined && (Date.now() - Number(w.since)) / this.DAY < Number(when.era_days)) ok = false
    if (when.rule) {
      Object.keys(when.rule).forEach(f => { if (!w.rule[f] || w.rule[f].mode !== when.rule[f]) ok = false })
    }
    return ok
  },

  // ---- balance and tide --------------------------------------------------------------------------------------

  clamp(n) {
    return n < -100 ? -100 : n > 100 ? 100 : n
  },

  decay(w) {
    var now = Date.now()
    var dt = now - Number(w.decayAt || now)
    w.decayAt = now
    var per = Number(this.conf().balance.decay_per_week)
    if (dt <= 0 || per <= 0 || !w.balance) return
    var step = per * dt / this.WEEK
    w.balance = w.balance > 0 ? Math.max(0, w.balance - step) : Math.min(0, w.balance + step)
  },

  tideFor(balance, current) {
    var b = this.conf().balance
    var at = Number(b.tide_at)
    var end = Number(b.tide_end)
    if (balance >= at) return 'light'
    if (balance <= -at) return 'dark'
    if (current === 'light' && balance > end) return 'light'
    if (current === 'dark' && balance < -end) return 'dark'
    return ''
  },

  updateTide(w, out) {
    var was = String(w.tide || '')
    var now = this.tideFor(this.num(w.balance), was)
    if (now === was) return
    w.tide = now
    out.tide = true
    var tides = this.conf().tide
    if (was && tides[was] && tides[was].end_story) out.posts.push(tides[was].end_story)
    if (now && tides[now] && tides[now].story) out.posts.push(tides[now].story)
    out.log.push({ kind: 'tide', who: '', data: { from: was, to: now, balance: Math.round(w.balance) } })
    console.info(`[ttl] world: tide ${was || 'none'} -> ${now || 'none'} (balance ${Math.round(w.balance)})`)
  },

  weigh(w, key, out) {
    var weights = this.conf().balance.weights
    if (!key || weights[key] === undefined) return
    this.decay(w)
    w.balance = this.clamp(this.num(w.balance) + Number(weights[key]))
    this.updateTide(w, out)
  },

  // ---- milestones and effects ---------------------------------------------------------------------------------

  fresh() {
    return { fired: [], phases: [], posts: [], titles: [], log: [], tide: false, mirror: false }
  },

  evaluate(server, w, out, by) {
    for (var round = 0; round < 10; round++) {
      var more = false
      this.defs().forEach(def => {
        if (w.milestones[def.id] || !this.met(server, w, def.when)) return
        this.apply(server, w, def, out, by || 'threshold')
        more = true
      })
      if (!more) return
    }
  },

  apply(server, w, def, out, by) {
    var fx = def.effects || {}
    w.milestones[def.id] = Date.now()
    out.fired.push(def.id)
    out.mirror = true
    Object.keys(fx.phase || {}).forEach(place => this.raisePhase(w, place, fx.phase[place], out, `milestone ${def.id}`))
    if (fx.conflict) this.openIn(w, fx.conflict, `milestone ${def.id}`, out)
    if (fx.title) out.titles.push(fx.title)
    if (fx.story) out.posts.push(fx.story)
    out.log.push({ kind: 'milestone', who: '', data: { id: def.id, by: String(by) } })
    console.info(`[ttl] world: milestone ${def.id} reached (${by})`)
  },

  phaseIndex(place, phase) {
    return (this.places()[place] || []).indexOf(String(phase))
  },

  raisePhase(w, place, phase, out, by) {
    var want = this.phaseIndex(place, phase)
    if (want < 0) return
    if (this.phaseIndex(place, w.phases[place]) >= want) return
    out.phases.push({ place: place, phase: String(phase), from: String(w.phases[place] || ''), by: by })
    w.phases[place] = String(phase)
    out.mirror = true
  },

  openIn(w, f, by, out) {
    if (w.conflicts[f]) return
    w.conflicts[f] = { opened: Date.now(), by: String(by) }
    out.mirror = true
    out.log.push({ kind: 'conflict', who: '', data: { faction: f, open: true, by: String(by) } })
    console.info(`[ttl] world: conflict ${f} opened (${by})`)
  },

  // Unlocks and moods in effect: every reached milestone's (sticky) plus the current tide's.
  effects(w) {
    var unlocked = []
    var mood = {}
    var addFx = fx => {
      ;(fx.unlock_events || []).forEach(id => { if (unlocked.indexOf(id) < 0) unlocked.push(id) })
      Object.keys(fx.mood || {}).forEach(f => { mood[f] = Number(mood[f] || 0) + Number(fx.mood[f]) })
    }
    this.defs().forEach(def => { if (w.milestones[def.id]) addFx(def.effects || {}) })
    var tide = this.conf().tide[w.tide]
    if (w.tide && tide) addFx(tide)
    return { unlocked: unlocked, mood: mood }
  },

  storeEffects(server, w) {
    var fx = this.effects(w)
    server.persistentData.putString(this.K_UNLOCKED, JSON.stringify(fx.unlocked))
    server.persistentData.putString(this.K_MOOD, JSON.stringify(fx.mood))
    this.unlockedCache = fx.unlocked
    this.moodCache = fx.mood
  },

  // Saves the record and the log, then runs what the change set in motion (phase hooks, mirrors, announcements).
  commit(server, w, out) {
    this.storeEffects(server, w)
    this.save(server, w)
    out.log.forEach(e => this.log(server, e.kind, e.who, e.data))
    out.phases.forEach(ph => this.runPhase(server, ph))
    if (out.mirror || out.tide) this.syncAll(server)
    if (out.titles.length) this.titleAll(server, out.titles)
    out.posts.forEach(text => this.post(server, text))
  },

  runPhase(server, ph) {
    console.info(`[ttl] world: phase ${ph.place} ${ph.from || '?'} -> ${ph.phase} (${ph.by})`)
    if (this.testMode(server)) {
      console.info(`[ttl] world: phase ${ph.place} ${ph.phase}: test mark set, the place's hook is skipped`)
      return
    }
    var hook = this.phaseHooks[ph.place] || null
    if (!hook && ph.place === 'tempest' && typeof TtlTempest !== 'undefined' && typeof TtlTempest.grow === 'function') hook = (s, phase, by) => TtlTempest.grow(s, phase, by)
    if (!hook) {
      console.info(`[ttl] world: phase ${ph.place} ${ph.phase}: no hook for ${ph.place} yet (stub)`)
      return
    }
    try {
      hook(server, ph.phase, ph.by)
    } catch (e) {
      console.error(`[ttl] world: the ${ph.place} hook for ${ph.phase} failed: ${e}`)
    }
  },

  // Another script registers how its place grows (an alternative to the built-in TtlTempest.grow lookup).
  onPhase(place, fn) {
    this.phaseHooks[String(place)] = fn
  },

  log(server, kind, who, data) {
    try {
      var list = this.readJson(server.persistentData, this.K_LOG, [])
      if (!Array.isArray(list)) list = []
      list.push({ t: Date.now(), kind: String(kind), who: String(who || ''), data: data || {} })
      var max = Number(this.chron().log_size)
      while (list.length > max) list.shift()
      var text = JSON.stringify(list)
      var cap = Number(this.chron().max_json)
      while (text.length > cap && list.length > 1) {
        list.shift()
        text = JSON.stringify(list)
      }
      server.persistentData.putString(this.K_LOG, text)
    } catch (e) {
      console.warn(`[ttl] world: could not write the log: ${e}`)
    }
  },

  // #story (TtlDiscord drops it while test bots are online or the mute is on). WP-W10 may take over the posting.
  post(server, text) {
    if (!text) return
    console.info(`[ttl] world: story: ${text}`)
    if (!this.chron().discord) return
    try {
      if (typeof TtlWorldPost !== 'undefined' && typeof TtlWorldPost.post === 'function' && TtlWorldPost.post(server, String(text))) return
      if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, String(text))
    } catch (e) {
      console.warn(`[ttl] world: #story post failed: ${e}`)
    }
  },

  titleAll(server, titles) {
    var text = JSON.stringify({ text: String(titles[titles.length - 1]), color: 'gold' })
    this.life2Online(server).forEach(p => server.runCommandSilent(`title ${p.username} title ${text}`))
  },

  life2Online(server) {
    var out = []
    server.getPlayerList().getPlayers().forEach(p => { if (TtlLife.phase(p) === 'life2') out.push(p) })
    return out
  },

  // ---- mirrors (R3: truth in ttl.world, stages and scoreboards rewritten together) -----------------------------

  ensureBoards(server) {
    var board = server.getScoreboard()
    var names = ['ttl.world.balance']
    Object.keys(this.places()).forEach(p => names.push(`ttl.world.phase.${p}`))
    names.forEach(n => { if (!board.getObjective(n)) server.runCommandSilent(`scoreboard objectives add ${n} dummy`) })
  },

  setStage(player, stage, on) {
    var has = player.stages.has(stage)
    if (on && !has) player.stages.add(stage)
    if (!on && has) player.stages.remove(stage)
  },

  sync(server, player) {
    if (TtlLife.phase(player) !== 'life2') return
    var w = this.load(server)
    var name = String(player.username)
    // Exact mirrors first (they may drop a stage), then the additive ones (milestone stages never go).
    var places = this.places()
    Object.keys(places).forEach(place => {
      var at = this.phaseIndex(place, w.phases[place])
      places[place].forEach((ph, i) => this.setStage(player, `ttl.world.phase.${place}.${ph}`, i <= at))
    })
    this.LANES.forEach(l => this.setStage(player, `ttl.world.tide.${l}`, w.tide === l))
    var modes = this.modes()
    this.factionIds().forEach(f => {
      this.setStage(player, `ttl.world.conflict.${f}`, !!w.conflicts[f])
      modes.forEach(m => this.setStage(player, `ttl.world.rule.${f}.${m}`, !!w.rule[f] && w.rule[f].mode === m))
    })
    var seen = this.readJson(player.persistentData, this.P_SEEN, {})
    var heard = 0
    var seenChanged = false
    var voices = Number(this.chron().voice_per_login)
    this.defs().forEach(def => {
      if (!w.milestones[def.id]) return
      var fx = def.effects || {}
      if (fx.stage) this.setStage(player, String(fx.stage), true)
      if (fx.chapter) this.setStage(player, `ttl.world.chapter.${fx.chapter}`, true)
      if (fx.voice && !seen[def.id]) {
        if (heard < voices) {
          heard++
          try {
            TtlCorridor.voice(server, name, String(fx.voice))
          } catch (e) {
            player.tell(Text.gold(String(fx.voice)))
          }
        }
        seen[def.id] = Date.now()
        seenChanged = true
      }
    })
    if (seenChanged) player.persistentData.putString(this.P_SEEN, JSON.stringify(seen))
    this.ensureBoards(server)
    server.runCommandSilent(`scoreboard players set ${name} ttl.world.balance ${Math.round(this.num(w.balance))}`)
    Object.keys(places).forEach(place => server.runCommandSilent(`scoreboard players set ${name} ttl.world.phase.${place} ${Math.max(0, this.phaseIndex(place, w.phases[place]))}`))
  },

  syncAll(server) {
    var w = this.load(server)
    this.ensureBoards(server)
    server.runCommandSilent(`scoreboard players set #world ttl.world.balance ${Math.round(this.num(w.balance))}`)
    Object.keys(this.places()).forEach(place => server.runCommandSilent(`scoreboard players set #world ttl.world.phase.${place} ${Math.max(0, this.phaseIndex(place, w.phases[place]))}`))
    this.life2Online(server).forEach(p => {
      try {
        this.sync(server, p)
      } catch (e) {
        console.error(`[ttl] world: mirrors for ${p.username} failed: ${e}`)
      }
    })
  },

  // Removes every ttl.world.* stage and the heard Voice lines from a soul (test hook, fixing); the next sync gives back
  // what the world holds.
  forget(player) {
    var all = []
    player.stages.getAll().forEach(s => { if (String(s).indexOf('ttl.world.') === 0) all.push(String(s)) })
    all.forEach(s => player.stages.remove(s))
    player.persistentData.remove(this.P_SEEN)
    player.persistentData.remove(this.P_COUNTED)
    return all.length
  },

  // ---- notes -------------------------------------------------------------------------------------------------

  inc(table, key, n) {
    table[key] = this.num(table[key]) + (n === undefined ? 1 : n)
  },

  // Adds one to a dotted path inside counts ('raidsWon.defenders').
  bump(c, path) {
    var parts = String(path).split('.')
    var at = c
    for (var i = 0; i < parts.length - 1; i++) {
      if (typeof at[parts[i]] !== 'object' || at[parts[i]] === null) at[parts[i]] = {}
      at = at[parts[i]]
    }
    this.inc(at, parts[parts.length - 1])
  },

  note(server, kind, player, data) {
    data = data || {}
    kind = String(kind)
    var who = player ? String(player.username) : String(data.name || data.who || '')
    if (player && !this.countable(server, player)) return false
    if (!player && who && this.isBot(who) && !this.testMode(server)) return false
    var w = this.load(server)
    var out = this.fresh()
    var c = w.counts
    var ledger = false
    var path = data.path ? String(data.path) : (player && typeof TtlStory !== 'undefined' ? TtlStory.path(player) : '')
    var added = []
    if (kind === 'oath') {
      added = this.touch(server, player, [`o.${path}`])
      ledger = true
      if (added.length) this.weigh(w, `oath_${path}`, out)
    } else if (kind === 'act') {
      added = this.touch(server, player, [`a.${path || 'light'}.${Number(data.act)}`])
      ledger = true
      if (added.length && !data.catchup) this.weigh(w, `act_${path}`, out)
    } else if (kind === 'flip') {
      added = this.touch(server, player, [`x.${data.kind}`])
      ledger = true
      if (added.length) this.weigh(w, String(data.kind), out)
    } else if (kind === 'flag') {
      added = this.touch(server, player, [`f.${data.flag}`])
      ledger = true
      // Atonement and Corruption are weighed once, by the flip itself.
      if (added.length && this.FLIPS.indexOf(String(data.flag)) < 0) this.weigh(w, String(data.flag), out)
    } else if (kind === 'kill') {
      var keys = [`k.${data.boss}`]
      if (data.wild) keys.push(`w.${data.boss}`)
      added = this.touch(server, player, keys)
      ledger = true
    } else if (kind === 'kill_outside') {
      if (this.conf().continent.outside_counts !== false) this.inc(c.wildKills, 'outside')
    } else if (kind === 'nation_found') {
      this.inc(c, 'nations')
    } else if (kind === 'nation_dropped') {
      if (data.key && c.armies) delete c.armies[String(data.key)]
    } else if (kind === 'war_declared') {
      this.inc(c, 'wars')
    } else if (kind === 'muster') {
      c.armies[String(data.key)] = this.num(data.n)
    } else if (kind === 'raid') {
      this.inc(c.raidsWon, data.result === 'sacked' ? 'raiders' : 'defenders')
      this.weigh(w, data.result === 'sacked' ? 'raid_sacked' : 'raid_defended', out)
    } else if (kind === 'uprising') {
      this.inc(c.uprisings, data.result === 'won' ? 'won' : 'put_down')
      this.weigh(w, data.result === 'won' ? 'uprising_won' : 'uprising_put_down', out)
    } else if (kind === 'radiant') {
      this.inc(c.radiant, String(data.faction))
      if (path === 'light' || path === 'dark') this.weigh(w, `radiant_${path}`, out)
    } else if (kind === 'legendary') {
      if (data.event === 'transfer') this.inc(c.legendary, 'moves')
      try {
        if (typeof TtlRegistry !== 'undefined') c.legendary.holders = TtlRegistry.legendaryHolders(server).length
      } catch (e) {
        console.warn(`[ttl] world: Legendary holders unreadable: ${e}`)
      }
    } else if (kind !== 'war_ended') {
      if (data.count) this.bump(c, data.count)
      if (data.weight) this.weigh(w, String(data.weight), out)
    }
    if (ledger) this.recount(server, w)
    if (!ledger || added.length) out.log.push({ kind: kind, who: who, data: data })
    this.evaluate(server, w, out, `${kind} by ${who || 'the world'}`)
    this.commit(server, w, out)
    return true
  },

  // boss.js `finish`: every credited soul gets the kill (story and wild alike, `wildKills` for wild ones); the first
  // defeat of a boss on the continent is a world first. A framework boss that died outside the continent (ops summon)
  // only counts in wildKills.outside and is never a first.
  bossKill(server, bossId, rec, names) {
    rec = rec || {}
    var id = String(bossId)
    var players = []
    ;(names || []).forEach(n => {
      var p = server.getPlayerList().getPlayerByName(String(n))
      if (p && this.countable(server, p)) players.push(p)
    })
    if (!players.length) return false
    var w = this.load(server)
    var out = this.fresh()
    var dim = String(rec.dim || this.conf().continent.overworld)
    if (rec.x !== undefined && !TtlWorld.onContinent(dim, rec.x, rec.z)) {
      if (this.conf().continent.outside_counts !== false) this.inc(w.counts.wildKills, 'outside')
      out.log.push({ kind: 'kill_outside', who: String(players[0].username), data: { boss: id } })
      this.commit(server, w, out)
      return true
    }
    players.forEach(p => this.touch(server, p, rec.wild ? [`k.${id}`, `w.${id}`] : [`k.${id}`]))
    this.recount(server, w)
    var who = players.map(p => String(p.username))
    if (!w.firsts[id]) {
      w.firsts[id] = { by: who.join(', '), party: this.partyName(server, players), at: Date.now(), wild: !!rec.wild }
      var tmpl = String(this.chron().first_story || '')
      var title = id
      try {
        if (typeof TtlBoss !== 'undefined' && TtlBoss.def(id)) title = String(TtlBoss.def(id).title || id)
      } catch (e) {
        title = id
      }
      if (tmpl) out.posts.push(tmpl.replace('{names}', who.join(', ')).replace('{boss}', title))
      out.log.push({ kind: 'first', who: who.join(', '), data: { boss: id } })
      console.info(`[ttl] world: first defeat of ${id} by ${who.join(', ')}`)
    }
    out.log.push({ kind: 'kill', who: who.join(', '), data: { boss: id, wild: !!rec.wild } })
    this.evaluate(server, w, out, `kill ${id}`)
    this.commit(server, w, out)
    return true
  },

  partyName(server, players) {
    if (typeof TtlParty === 'undefined' || typeof TtlParty.info !== 'function') return ''
    for (var i = 0; i < players.length; i++) {
      try {
        var info = TtlParty.info(server, players[i])
        if (info && info.team) return String(info.team.getName().getString())
      } catch (e) {
        // a party without a readable name: try the next soul
      }
    }
    return ''
  },

  // ---- reads ---------------------------------------------------------------------------------------------------

  get(server, path) {
    var at = this.load(server)
    var parts = String(path).split('.')
    for (var i = 0; i < parts.length; i++) {
      if (at === null || at === undefined || typeof at !== 'object') return undefined
      at = at[parts[i]]
    }
    return at
  },

  count(server, path) {
    return this.num(this.get(server, `counts.${path}`))
  },

  balance(server) {
    return this.num(this.load(server).balance)
  },

  tide(server) {
    return String(this.load(server).tide || '')
  },

  milestones(server) {
    return this.load(server).milestones
  },

  reached(server, id) {
    return !!this.load(server).milestones[String(id)]
  },

  phase(server, place) {
    return String(this.load(server).phases[String(place)] || '')
  },

  firsts(server) {
    return this.load(server).firsts
  },

  conflict(server, f) {
    return this.load(server).conflicts[String(f)] || null
  },

  rule(server, f) {
    return this.load(server).rule[String(f)] || null
  },

  active(server, key) {
    var until = this.num(this.load(server).active[String(key)])
    return until > Date.now() ? until : 0
  },

  // Mood in bands for one faction (TtlRep.guardsHostile / shopOpen read this on every check: cached).
  mood(f, server) {
    if (this.moodCache === null && server) this.moodCache = this.readJson(server.persistentData, this.K_MOOD, {})
    var m = this.moodCache || {}
    return this.num(m[String(f)])
  },

  moods(server) {
    if (this.moodCache === null) this.moodCache = this.readJson(server.persistentData, this.K_MOOD, {})
    return this.moodCache
  },

  unlocked(server) {
    if (this.unlockedCache === null) {
      var list = this.readJson(server.persistentData, this.K_UNLOCKED, [])
      this.unlockedCache = Array.isArray(list) ? list : []
    }
    return this.unlockedCache
  },

  isUnlocked(server, id) {
    return this.unlocked(server).indexOf(String(id)) >= 0
  },

  // ---- changes (ops and other packages) ------------------------------------------------------------------------

  addBalance(server, n, why) {
    var w = this.load(server)
    var out = this.fresh()
    this.decay(w)
    w.balance = this.clamp(this.num(w.balance) + Number(n))
    this.updateTide(w, out)
    out.mirror = true
    out.log.push({ kind: 'balance', who: '', data: { add: Number(n), now: Math.round(w.balance), why: String(why || '') } })
    console.info(`[ttl] world: balance ${Number(n) >= 0 ? '+' : ''}${n} -> ${Math.round(w.balance)} (${why || 'admin'})`)
    this.evaluate(server, w, out, `balance (${why || 'admin'})`)
    this.commit(server, w, out)
    return w.balance
  },

  // Forces a milestone (ops); null when it went through, else why not.
  fire(server, id, by) {
    var def = this.def(id)
    if (!def) return `unknown milestone ${id} (${this.defs().map(d => d.id).join(', ')})`
    var w = this.load(server)
    if (w.milestones[def.id]) return `${def.id} is already reached`
    var out = this.fresh()
    this.apply(server, w, def, out, by || 'admin')
    this.evaluate(server, w, out, `after ${def.id}`)
    this.commit(server, w, out)
    return null
  },

  setPhase(server, place, phase, by) {
    if (!this.places()[place]) return `unknown place ${place} (${Object.keys(this.places()).join(', ')})`
    if (this.phaseIndex(place, phase) < 0) return `${place} has no phase ${phase} (${this.places()[place].join(', ')})`
    var w = this.load(server)
    var out = this.fresh()
    if (w.phases[place] === phase) return null
    out.phases.push({ place: place, phase: String(phase), from: String(w.phases[place] || ''), by: String(by || 'admin') })
    w.phases[place] = String(phase)
    out.mirror = true
    out.log.push({ kind: 'phase', who: '', data: { place: place, phase: phase, by: String(by || 'admin') } })
    this.commit(server, w, out)
    return null
  },

  openConflict(server, f, by) {
    var w = this.load(server)
    if (w.conflicts[f]) return `the conflict over ${f} is already open`
    var out = this.fresh()
    this.openIn(w, f, by || 'admin', out)
    this.commit(server, w, out)
    return null
  },

  closeConflict(server, f, by) {
    var w = this.load(server)
    if (!w.conflicts[f]) return `there is no open conflict over ${f}`
    var out = this.fresh()
    delete w.conflicts[f]
    out.mirror = true
    out.log.push({ kind: 'conflict', who: '', data: { faction: f, open: false, by: String(by || 'admin') } })
    console.info(`[ttl] world: conflict ${f} closed (${by || 'admin'})`)
    this.commit(server, w, out)
    return null
  },

  setRule(server, f, nation, mode, by) {
    if (this.modes().indexOf(String(mode)) < 0) return `mode must be one of ${this.modes().join(', ')}`
    var w = this.load(server)
    var out = this.fresh()
    w.rule[f] = { nation: String(nation), mode: String(mode), since: Date.now(), by: String(by || 'admin') }
    out.mirror = true
    out.log.push({ kind: 'rule', who: String(by || ''), data: { faction: f, nation: String(nation), mode: String(mode) } })
    console.info(`[ttl] world: rule ${f} = ${nation} (${mode}, by ${by || 'admin'})`)
    this.evaluate(server, w, out, `rule ${f}`)
    this.commit(server, w, out)
    return null
  },

  clearRule(server, f, by) {
    var w = this.load(server)
    if (!w.rule[f]) return `nobody rules ${f} but its canon ruler`
    var out = this.fresh()
    delete w.rule[f]
    out.mirror = true
    out.log.push({ kind: 'rule', who: String(by || ''), data: { faction: f, cleared: true } })
    console.info(`[ttl] world: rule ${f} cleared (${by || 'admin'})`)
    this.commit(server, w, out)
    return null
  },

  setActive(server, key, until) {
    var w = this.load(server)
    var out = this.fresh()
    if (!until) delete w.active[String(key)]
    else w.active[String(key)] = Number(until)
    out.log.push({ kind: 'active', who: '', data: { key: String(key), until: Number(until || 0) } })
    this.commit(server, w, out)
  },

  // ---- sync, login, eras -----------------------------------------------------------------------------------------

  // The 5-minute pass: decay and tide, online souls seen and backfilled, counts, stale party records, milestones, mirrors.
  pass(server) {
    var w = this.load(server)
    var out = this.fresh()
    this.decay(w)
    this.updateTide(w, out)
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (this.countable(server, p)) this.backfill(server, p)
      } catch (e) {
        console.error(`[ttl] world: backfill of ${p.username} failed: ${e}`)
      }
    })
    this.recount(server, w)
    this.pruneParties(server)
    this.evaluate(server, w, out, 'sync')
    out.mirror = true
    this.commit(server, w, out)
  },

  // H11: ttl.story.parties keeps records of parties FTB no longer has (the party.js roster rule). Only with a manager.
  pruneParties(server) {
    if (typeof TtlParty === 'undefined' || typeof TtlParty.manager !== 'function') return 0
    var mgr = TtlParty.manager()
    if (!mgr) return 0
    var parties = this.readJson(server.persistentData, 'ttl.story.parties', {})
    var gone = []
    var UUID = null
    try {
      UUID = Java.loadClass('java.util.UUID')
    } catch (e) {
      return 0
    }
    Object.keys(parties).forEach(id => {
      try {
        var opt = mgr.getTeamByID(UUID.fromString(id))
        if (!opt.isPresent() || !opt.get().isPartyTeam()) gone.push(id)
      } catch (e) {
        gone.push(id)
      }
    })
    if (!gone.length) return 0
    gone.forEach(id => { delete parties[id] })
    server.persistentData.putString('ttl.story.parties', JSON.stringify(parties))
    console.info(`[ttl] world: pruned ${gone.length} party record(s) FTB no longer has: ${gone.join(', ')}`)
    return gone.length
  },

  onLogin(server, player) {
    if (!this.countable(server, player)) {
      this.sync(server, player)
      return
    }
    var w = this.load(server)
    var out = this.fresh()
    this.backfill(server, player)
    this.recount(server, w)
    this.evaluate(server, w, out, `login of ${player.username}`)
    this.commit(server, w, out)
    this.sync(server, player)
  },

  // era.js `next`: one snapshot per finished era; balance and tide start again, phases, milestones, firsts, rule stay.
  archive(server, oldEra, newEra) {
    if (String(server.persistentData.getString('ttl.era.testmark'))) {
      console.info(`[ttl] world: era ${oldEra} -> ${newEra} under an era test mark: the chronicle is not archived`)
      return false
    }
    var w = this.load(server)
    var out = this.fresh()
    var list = this.readJson(server.persistentData, this.K_ARCHIVE, [])
    if (!Array.isArray(list)) list = []
    list.push({ era: Number(oldEra), ended: Date.now(), world: JSON.parse(JSON.stringify(w)) })
    var cap = Number(this.chron().archive_max)
    while (list.length > cap) list.shift()
    var text = JSON.stringify(list)
    while (text.length > Number(this.chron().max_json) && list.length > 1) {
      list.shift()
      text = JSON.stringify(list)
    }
    server.persistentData.putString(this.K_ARCHIVE, text)
    w.era = Number(newEra)
    w.since = Date.now()
    w.balance = 0
    w.decayAt = Date.now()
    this.updateTide(w, out)
    out.mirror = true
    out.log.push({ kind: 'era', who: '', data: { from: Number(oldEra), to: Number(newEra) } })
    console.info(`[ttl] world: era ${oldEra} archived (${list.length} in the archive); era ${newEra} starts with balance 0`)
    this.commit(server, w, out)
    return true
  },

  // ---- test hooks ----------------------------------------------------------------------------------------------

  MARK_PARTS: ['world', 'log', 'archive', 'unlocked', 'mood'],

  // Saves the world (record, log, archive, effects, ledger) and starts a blank one in which test bots count. A mark that
  // is already there (a crashed test) is kept, so the oldest real state is the one restored.
  testMark(server) {
    var d = server.persistentData
    if (this.testMode(server)) {
      console.warn('[ttl] world: a test mark is already set; keeping it (the real world stays saved)')
      return false
    }
    var keys = { world: this.K, log: this.K_LOG, archive: this.K_ARCHIVE, unlocked: this.K_UNLOCKED, mood: this.K_MOOD }
    this.MARK_PARTS.forEach(part => d.putString(`${this.K_MARK}.${part}`, String(d.getString(keys[part]))))
    d.put(`${this.K_MARK}.souls`, this.soulBox(server).copy())
    d.putString(this.K_MARK, JSON.stringify({ at: Date.now() }))
    ;[this.K, this.K_LOG, this.K_UNLOCKED, this.K_MOOD, this.K_SOULS].forEach(k => d.remove(k))
    this.world = null
    this.moodCache = null
    this.unlockedCache = null
    var w = this.load(server)
    var out = this.fresh()
    out.mirror = true
    this.commit(server, w, out)
    console.info('[ttl] world: test mark set, the chronicle is blank until testrestore')
    return true
  },

  testRestore(server) {
    var d = server.persistentData
    if (!this.testMode(server)) return false
    var keys = { world: this.K, log: this.K_LOG, archive: this.K_ARCHIVE, unlocked: this.K_UNLOCKED, mood: this.K_MOOD }
    this.MARK_PARTS.forEach(part => {
      var v = String(d.getString(`${this.K_MARK}.${part}`))
      if (v) d.putString(keys[part], v)
      else d.remove(keys[part])
      d.remove(`${this.K_MARK}.${part}`)
    })
    d.put(this.K_SOULS, d.getCompound(`${this.K_MARK}.souls`).copy())
    ;[`${this.K_MARK}.souls`, this.K_MARK, this.K_TEST_THRESHOLD].forEach(k => d.remove(k))
    this.world = null
    this.moodCache = null
    this.unlockedCache = null
    this.syncAll(server)
    console.info('[ttl] world: test state restored')
    return true
  },

  testThreshold(server, souls, pct) {
    if (souls === null) server.persistentData.remove(this.K_TEST_THRESHOLD)
    else server.persistentData.putString(this.K_TEST_THRESHOLD, JSON.stringify({ souls: Number(souls), pct: Number(pct) }))
  },

  // ---- views ---------------------------------------------------------------------------------------------------

  wildActive(server) {
    var out = []
    try {
      if (typeof TtlBoss === 'undefined') return out
      var active = TtlBoss.load(server)
      Object.keys(active).forEach(k => { if (active[k].wild && out.indexOf(String(active[k].id)) < 0) out.push(String(active[k].id)) })
    } catch (e) {
      console.warn(`[ttl] world: wild bosses unreadable: ${e}`)
    }
    return out
  },

  view(server) {
    var w = this.load(server)
    var copy = x => JSON.parse(JSON.stringify(x))
    return {
      era: w.era, since: w.since, tide: w.tide, balance: Math.round(this.num(w.balance)), phases: copy(w.phases),
      milestones: Object.keys(w.milestones), conflicts: Object.keys(w.conflicts), mood: copy(this.moods(server)),
      rule: copy(w.rule), unlocked: this.unlocked(server).slice(), active: copy(w.active), wild: this.wildActive(server),
      counts: copy(w.counts)
    }
  },

  export(server) {
    var w = this.load(server)
    var c = w.counts
    return JSON.stringify({
      v: w.v, era: w.era, since: w.since, tide: w.tide, balance: Math.round(this.num(w.balance)), phases: w.phases,
      milestones: w.milestones, firsts: w.firsts, rule: w.rule, conflicts: w.conflicts, active: w.active,
      unlocked: this.unlocked(server), mood: this.moods(server),
      counts: { souls: c.souls, active30: c.active30, oaths: c.oaths, reached: c.reached, kills: c.kills, nations: c.nations, wars: c.wars, raidsWon: c.raidsWon, legendary: c.legendary }
    })
  },

  lines(server) {
    var w = this.load(server)
    var c = w.counts
    var reached = this.defs().filter(d => w.milestones[d.id]).map(d => d.id)
    var out = [`Era ${w.era}${this.testMode(server) ? ' (TEST MARK: blank test world)' : ''} · souls ${c.souls}, active ${c.active30} · threshold ${this.threshold(server, w)}`]
    out.push(`Balance ${Math.round(this.num(w.balance))} · tide ${w.tide || 'none'}`)
    out.push(`Phases: ${Object.keys(w.phases).map(p => `${p} ${w.phases[p]}`).join(', ') || 'none'}`)
    out.push(`Milestones: ${reached.length}/${this.defs().length}${reached.length ? ` (${reached.join(', ')})` : ''}`)
    var acts = Object.keys(c.reached).sort().map(n => `${n}: ${c.reached[n]}`)
    if (acts.length) out.push(`Souls per act: ${acts.join(', ')}`)
    var conflicts = Object.keys(w.conflicts)
    if (conflicts.length) out.push(`Conflicts: ${conflicts.join(', ')}`)
    var rules = Object.keys(w.rule)
    if (rules.length) out.push(`Thrones: ${rules.map(f => `${f} ${w.rule[f].mode} (${w.rule[f].nation})`).join(', ')}`)
    var firsts = Object.keys(w.firsts)
    if (firsts.length) out.push(`Firsts: ${firsts.map(b => `${b} (${w.firsts[b].by})`).join(', ')}`)
    var unlocked = this.unlocked(server)
    if (unlocked.length) out.push(`Events unlocked: ${unlocked.join(', ')}`)
    var mood = this.moods(server)
    var moods = Object.keys(mood).filter(f => mood[f])
    if (moods.length) out.push(`Moods: ${moods.map(f => `${f} ${mood[f] > 0 ? '+' : ''}${mood[f]}`).join(', ')}`)
    return out
  },

  logLines(server, n) {
    var list = this.readJson(server.persistentData, this.K_LOG, [])
    if (!Array.isArray(list)) return []
    return list.slice(Math.max(0, list.length - n)).map(e => `${new Date(Number(e.t)).toISOString().slice(0, 16)} ${e.kind}${e.who ? ' ' + e.who : ''} ${JSON.stringify(e.data)}`)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlChronicle.world = null
    TtlChronicle.moodCache = null
    TtlChronicle.unlockedCache = null
    TtlChronicle.load(server)
    TtlChronicle.moods(server)
    TtlChronicle.unlocked(server)
    TtlChronicle.ensureBoards(server)
  } catch (e) {
    console.error(`[ttl] world: loading the chronicle failed: ${e}`)
  }
  // A script reload runs this again; the stamp makes the older loop stop instead of doubling up.
  var stamp = String(Date.now())
  server.persistentData.putString(TtlChronicle.K_LOOP, stamp)
  var poll = () => server.scheduleInTicks(Number(TtlData.world.chronicle.sync_ticks), () => {
    if (String(server.persistentData.getString(TtlChronicle.K_LOOP)) !== stamp) return
    try {
      TtlChronicle.pass(server)
    } catch (e) {
      console.error(`[ttl] world: chronicle sync failed: ${e}`)
    }
    poll()
  })
  poll()
})

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  try {
    TtlChronicle.onLogin(server, player)
  } catch (e) {
    console.error(`[ttl] world: login sync for ${player.username} failed: ${e}`)
  }
})
