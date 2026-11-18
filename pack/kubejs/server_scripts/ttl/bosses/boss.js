// priority: 70
// Boss framework (design/architecture/sprint3-4.md S2; knobs and boss definitions: design/data/bosses.toml).
// A boss is summoned, never natural: TtlBoss.summon(server, id, opts) from a quest or altar, `/ttl boss summon` for ops
// (bosses/commands.js). The summon forceloads the arena chunk, spawns the entity with NoAI and these tags:
//   ttl.boss                the marker every hook looks for
//   ttl.bossid.<id>         which definition
//   ttl.boss.k<n>           this instance (n from server `ttl.boss.seq`); minions carry ttl.boss.minion and ttl.boss.mk<n>
// A 20-tick poll (this file) wakes it when a player comes within `range`, scales its health to the players there,
// runs the phases (announce, minions, enrage), keeps a boss bar, and finishes it when the entity is gone or dead.
// Kills are NOT read from EntityEvents.death (unreliable for mobs here): the killer is the player whose scoreboard
// objective ttl.b.<id> (criterion minecraft.killed:<entity>, same trick as discord.js checkBosses) rose since the
// previous poll. A boss that died to something else (/kill, lava) rewards whoever stood in the fight.
//
// Server persistentData: `ttl.boss.active` JSON {key: record}, `ttl.boss.seq`, `ttl.boss.lastkill` JSON {uuid: {id: millis}}
// (mirror of the per-soul defeat stamps, so offline party members still count), `ttl.boss.arena` JSON {arenaKey: {t, id}}
// (last defeat per arena: arena_gap_minutes), `ttl.boss.queue` JSON {bossId: [{party, members, by, at, akey, ready}]}.
// `ttl.boss.last.<id>` (the old server-wide stamp) is only written with cooldown_scope = "server" (the rollback knob); in
// party scope it is turned into an arena gap once at boot and removed. Player: stage `ttl.boss.t<tier>`, `ttl.boss.kills`
// JSON {id: n}, `ttl.boss.lastkill` JSON {id: millis} (story kills only), `ttl.boss.core.owed` (Skill Cores not yet handed
// out because the item does not exist yet).
// Record: {id, dim, x, y, z, started, state idle|fight, base (vanilla max hp), n (players at last scaling), phase
// (phases done), hit/near/names (uuid maps: damage dealers, polls in range, display names), dmg (uuid -> damage dealt),
// seen (objective values at the last poll), last (uuids in range at the last poll), gone (polls without the entity),
// idle (millis of the last poll with a player in range), fx/fz (forceloaded block position), wild (true: rolled by
// bosses/wild.js), duel (true: an honour duel, no kill_rep), party {teamId: [uuids]} (rosters frozen the first time a member
// stood near the boss) and pt {uuid: teamId} (what each player was seen as), akey (arena key), owner (party key of the
// summoner, '' for ops/events/wild), echo (true: a replay of a boss the world has already seen fall), ehp (echo health
// multiplier), awake (true: summoned without the NoAI wait), bar}.
// Party credit (finish): the party members of everyone credited who were in that frozen roster, are online, Life 2 and
// within party_credit_range x range share the kill (no Skill Core beyond core_per_party), so a party that stands around
// cannot farm cores and one invited after the wake or the kill gets nothing. The party is a raid group (TtlRaid.groupOf),
// else an FTB Teams party team.
// Instancing (design/architecture/world-state.md §7.1, WP-W2): the cooldown is PER PARTY (a party is on cooldown for a boss
// while any member's ttl.boss.lastkill[id] is inside cooldown_hours), an arena holds one story fight at a time (a busy or
// settling arena queues the summoner's party: place, ETA, a ping when it frees, then queue_ttl_minutes to summon),
// max_instances bosses live at once, max_per_party per summoning party. Wild bosses never lock an arena and are never
// locked out by a story fight of the same id. The continent line (§2.0, R11): in the Overworld, outside the canon
// continent, nothing of this applies: a summon is refused there and the mods' own spawns rule (block_natural is off).
// Summoning (opts): {summoner} checked against `requires` + `spawn.stages` and used for the party; {skipGate, skipCooldown}
// (force = both and also skips the arena gap, queue reservations and the instance caps, ops); {wild: true} (bosses/wild.js:
// no arena bound, announced by TtlWild); {duel: true}; {awake: true} (no NoAI wait: the boss moves at once, the March of
// the Horde); {echo: true|false} (overrides the chronicle's firsts); {x, y, z, dim}; {at}; {by}; {region}.
// A `spawn.kind = "statue"` boss with `spawn.statue = "<tag>"`: the seated statue (an entity with that tag) steps aside
// while a story instance is live (discarded at the summon; its keeper asks TtlBoss.statueAside before re-seating it).
// Never bindable as a Tombstone familiar: compat/tombstone_bosses.js refuses any entity with the ttl.boss tag.
const TtlBoss = {
  POLL: 20,
  TAG: 'ttl.boss',
  MINION: 'ttl.boss.minion',
  COLORS: { 1: 'gold', 2: 'red', 3: 'dark_purple', 4: 'dark_red' },
  BAR_COLORS: { 1: 'yellow', 2: 'red', 3: 'purple', 4: 'red' },
  // Spawn types of EntityEvents.checkSpawn that are "by themselves"; a summon, spawn egg or conversion is not.
  NATURAL: /natural|chunk_generation|structure|spawner|patrol|reinforcement|jockey/i,
  // In-memory only: damage dealers seen since the last poll per instance, summons waiting for their chunk, bars made.
  hits: {},
  dmg: {},
  // Summons waiting for their chunk: {instanceKey: {id, wild, akey, owner, dim, x, z}}.
  pending: {},
  bars: {},
  teamApi: undefined,
  // Continent test fallback (used while world/chronicle.js is not loaded): the canon grid and a per-chunk-column cache.
  grid: null,
  gridWarned: false,
  worldWarned: false,
  contCache: {},
  contN: 0,

  // ---- data -------------------------------------------------------------------------------------------------

  num(v, dflt) {
    var n = Number(v)
    return v !== undefined && v !== null && v !== '' && isFinite(n) ? n : dflt
  },

  conf() {
    var f = (TtlData.bosses && TtlData.bosses.framework) || {}
    var w = (TtlData.bosses && TtlData.bosses.wild) || {}
    var idle = f.idle_minutes === undefined ? 30 : Number(f.idle_minutes)
    return {
      blockNatural: f.block_natural !== false,
      idleMs: idle * 60000,
      wildIdleMs: (w.idle_minutes === undefined ? idle : Number(w.idle_minutes)) * 60000,
      presence: f.presence_secs === undefined ? 15 : Number(f.presence_secs),
      untame: f.untame !== false,
      partyRange: f.party_credit_range === undefined ? 2 : Number(f.party_credit_range),
      corePerParty: f.core_per_party === undefined ? 1 : Number(f.core_per_party),
      proxies: f.proxy_bosses !== false,
      wildMult: w.rewards_mult === undefined ? 1 : Number(w.rewards_mult),
      scope: f.cooldown_scope === 'server' ? 'server' : 'party',
      gapMs: this.num(f.arena_gap_minutes, 10) * 60000,
      maxInstances: this.num(f.max_instances, 4),
      maxPerParty: this.num(f.max_per_party, 1),
      queueTtlMs: this.num(f.queue_ttl_minutes, 20) * 60000,
      fightMin: this.num(f.fight_estimate_minutes, 15),
      echoPrefix: f.echo_prefix === undefined ? 'Echo · ' : String(f.echo_prefix),
      echoHp: this.num(f.echo_hp_mult, 0.85)
    }
  },

  // Display title of an instance (the echo prefix on a replay).
  titleOf(def, echo) {
    return echo ? `${this.conf().echoPrefix}${def.title}` : def.title
  },

  defs() {
    return (TtlData.bosses && TtlData.bosses.boss) || []
  },

  def(id) {
    var list = this.defs()
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === id) return list[i]
    }
    return null
  },

  byEntity(entityId) {
    var list = this.defs()
    for (var i = 0; i < list.length; i++) {
      if (list[i].entity === entityId) return list[i]
    }
    return null
  },

  load(server) {
    var raw = String(server.persistentData.getString('ttl.boss.active'))
    if (!raw) return {}
    try {
      return JSON.parse(raw)
    } catch (e) {
      console.error(`[ttl] boss: ttl.boss.active is not valid JSON, starting empty (${e})`)
      return {}
    }
  },

  save(server, active) {
    server.persistentData.putString('ttl.boss.active', JSON.stringify(active))
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  players(server) {
    var out = []
    server.getPlayerList().getPlayers().forEach(p => out.push(p))
    return out
  },

  // Distance in blocks from a player to a point of a dimension, or Infinity in another dimension.
  distance(p, dim, x, y, z) {
    if (String(p.level.dimension) !== dim) return Infinity
    var dx = p.getX() - x
    var dy = p.getY() - y
    var dz = p.getZ() - z
    return Math.sqrt(dx * dx + dy * dy + dz * dz)
  },

  readJson(server, key, dflt) {
    var raw = String(server.persistentData.getString(key) || '')
    if (!raw) return dflt
    try {
      var v = JSON.parse(raw)
      return v && typeof v === 'object' ? v : dflt
    } catch (e) {
      console.warn(`[ttl] boss: ${key} is not valid JSON, starting empty (${e})`)
      return dflt
    }
  },

  writeJson(server, key, v) {
    server.persistentData.putString(key, JSON.stringify(v))
  },

  // The old server-wide stamp; only cooldown_scope = "server" reads or writes it.
  lastDefeat(server, id) {
    return Number(String(server.persistentData.getString(`ttl.boss.last.${id}`)) || 0)
  },

  // ---- the continent line (world-state.md §2.0, R11) ---------------------------------------------------------------

  canonGrid() {
    if (this.grid) return this.grid
    try {
      this.grid = Java.loadClass('com.yasuke.ttl.world.CanonMap').grid() || null
    } catch (e) {
      if (!this.gridWarned) console.warn(`[ttl] boss: the canon grid is not available, every spot counts as the continent: ${e}`)
      this.gridWarned = true
      this.grid = null
    }
    return this.grid
  },

  // True on the canon continent (its land, rivers and near-coast water), in every dimension but the Overworld, and when
  // the test cannot be made. world/chronicle.js (TtlWorld.onContinent, WP-W1) is the one owner of the rule; the grid read
  // below is the same test (ownerCell != 0) for as long as that file is not loaded.
  onContinent(dim, x, z) {
    dim = String(dim)
    if (typeof TtlWorld !== 'undefined' && typeof TtlWorld.onContinent === 'function') {
      try {
        return !!TtlWorld.onContinent(dim, x, z)
      } catch (e) {
        if (!this.worldWarned) console.warn(`[ttl] boss: TtlWorld.onContinent failed, using the grid: ${e}`)
        this.worldWarned = true
      }
    }
    if (dim !== TtlLife.OVERWORLD) return true
    var bx = Math.floor(x)
    var bz = Math.floor(z)
    var key = `${bx >> 4},${bz >> 4}`
    if (this.contCache[key] !== undefined) return this.contCache[key]
    var g = this.canonGrid()
    if (!g) return true
    var inside = true
    try {
      var c = g.ownerCell(bx, bz)
      var code = typeof c === 'number' ? c : String(c).length > 0 ? String(c).charCodeAt(0) : 0
      inside = code !== 0 && code !== 48
    } catch (e) {
      console.warn(`[ttl] boss: reading the canon grid at ${bx} ${bz} failed: ${e}`)
      return true
    }
    if (this.contN > 4096) {
      this.contCache = {}
      this.contN = 0
    }
    this.contCache[key] = inside
    this.contN++
    return inside
  },

  // The story rules end at the coast: only the Overworld beyond the continent is "outside" (the Labyrinth, the Spirit
  // Domain, Hell and the test halls are always inside).
  outside(dim, x, z) {
    return String(dim) === TtlLife.OVERWORLD && !this.onContinent(dim, x, z)
  },

  // ---- per-party cooldown ------------------------------------------------------------------------------------------

  // {id, members: [lowercase uuids]} of the summoner: their raid group or party, else the soul alone ('solo:<uuid>').
  partyKey(server, player) {
    var team = this.partyOf(server, player)
    if (team) return { id: String(team.id), members: team.members }
    var u = this.uid(player)
    return { id: `solo:${u}`, members: [u] }
  },

  // A credited story kill: stamped on the soul (ttl.boss.lastkill) and in the server mirror (offline members still count).
  stampKill(server, p, id, now) {
    var mine = {}
    try {
      mine = JSON.parse(String(p.persistentData.getString('ttl.boss.lastkill')) || '{}')
    } catch (e) {
      mine = {}
    }
    mine[id] = now
    p.persistentData.putString('ttl.boss.lastkill', JSON.stringify(mine))
    var all = this.readJson(server, 'ttl.boss.lastkill', {})
    var u = this.uid(p)
    all[u] = all[u] || {}
    all[u][id] = now
    // Stamps older than the longest cooldown can never matter again.
    var keep = 0
    this.defs().forEach(d => { keep = Math.max(keep, Number(d.cooldown_hours) || 0) })
    var cut = now - keep * 3600000
    Object.keys(all).forEach(m => {
      Object.keys(all[m]).forEach(b => { if (all[m][b] < cut) delete all[m][b] })
      if (Object.keys(all[m]).length === 0) delete all[m]
    })
    this.writeJson(server, 'ttl.boss.lastkill', all)
  },

  // Milliseconds of cooldown left for this party (any member's stamp counts). The server mirror is the truth: it covers
  // offline members, and `cooldown clear` reaches it while an offline soul's own copy cannot be reached.
  partyCooldownLeft(server, def, party) {
    var all = this.readJson(server, 'ttl.boss.lastkill', {})
    var best = 0
    party.members.forEach(u => {
      var t = all[u] && all[u][def.id] ? Number(all[u][def.id]) : 0
      if (t > best) best = t
    })
    var left = best + def.cooldown_hours * 3600000 - Date.now()
    return left > 0 ? left : 0
  },

  // Milliseconds of cooldown left for this boss: per party of `player` (cooldown_scope party), else the server stamp.
  cooldownLeft(server, def, player) {
    if (this.conf().scope === 'server') {
      var left = this.lastDefeat(server, def.id) + def.cooldown_hours * 3600000 - Date.now()
      return left > 0 ? left : 0
    }
    if (!player) return 0
    return this.partyCooldownLeft(server, def, this.partyKey(server, player))
  },

  onlineByUid(server, u) {
    var found = null
    var self = this
    server.getPlayerList().getPlayers().forEach(p => {
      if (!found && self.uid(p) === u) found = p
    })
    return found
  },

  // Forget the story cooldown of a boss for everyone (ops, tests): the mirror, every online soul's stamp, the old server stamp.
  clearCooldown(server, id) {
    var all = this.readJson(server, 'ttl.boss.lastkill', {})
    Object.keys(all).forEach(u => {
      delete all[u][id]
      if (Object.keys(all[u]).length === 0) delete all[u]
    })
    this.writeJson(server, 'ttl.boss.lastkill', all)
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        var mine = JSON.parse(String(p.persistentData.getString('ttl.boss.lastkill')) || '{}')
        if (mine[id] === undefined) return
        delete mine[id]
        p.persistentData.putString('ttl.boss.lastkill', JSON.stringify(mine))
      } catch (e) {
        p.persistentData.remove('ttl.boss.lastkill')
      }
    })
    server.persistentData.remove(`ttl.boss.last.${id}`)
  },

  // Forget the arena gaps left by a boss (id '' = every boss) and its queue (ops, tests).
  clearArena(server, id) {
    var gaps = this.readJson(server, 'ttl.boss.arena', {})
    Object.keys(gaps).forEach(k => { if (!id || gaps[k].id === id) delete gaps[k] })
    this.writeJson(server, 'ttl.boss.arena', gaps)
    var q = this.queueLoad(server)
    if (id) delete q[id]
    else q = {}
    this.queueSave(server, q)
  },

  // ---- arenas and the queue ----------------------------------------------------------------------------------------

  // The arena of a summon position: a bound arena's centre, else the summon spot itself ('<dim>@<x>,<z>').
  arenaKey(pos) {
    if (pos.arena) return `${pos.dim}@${pos.arena.x},${pos.arena.z}`
    return `${pos.dim}@${Math.floor(pos.x)},${Math.floor(pos.z)}`
  },

  recKey(rec) {
    return rec.akey || `${rec.dim}@${Math.floor(rec.fx)},${Math.floor(rec.fz)}`
  },

  // Milliseconds the arena still settles after its last defeat (arena_gap_minutes).
  arenaGapLeft(server, akey) {
    var gaps = this.readJson(server, 'ttl.boss.arena', {})
    var g = gaps[akey]
    if (!g) return 0
    var left = Number(g.t) + this.conf().gapMs - Date.now()
    return left > 0 ? left : 0
  },

  // Live and pending instances: [{key, id, wild, akey, owner, dim, x, z, pending}].
  instances(server) {
    var out = []
    var active = this.load(server)
    for (var k in active) {
      var r = active[k]
      out.push({ key: k, id: r.id, wild: !!r.wild, akey: this.recKey(r), owner: r.owner || '', dim: r.dim, x: r.fx, z: r.fz, pending: false })
    }
    for (var p in this.pending) {
      var q = this.pending[p]
      out.push({ key: p, id: q.id, wild: !!q.wild, akey: q.akey, owner: q.owner || '', dim: q.dim, x: q.x, z: q.z, pending: true })
    }
    return out
  },

  // Why a story fight of `def` cannot start in this arena now, or null: {code: busy|gap|reserved|waiting|full, msg}.
  // Wild instances never lock an arena. `party` (may be null) is the summoner's party key; force skips all but `busy`.
  arenaBlock(server, def, pos, akey, party, force) {
    var c = this.conf()
    var list = this.instances(server)
    for (var i = 0; i < list.length; i++) {
      var r = list[i]
      if (r.wild) continue
      var other = this.def(r.id)
      var reach = Math.max(def.range, other ? other.range : def.range)
      var near = r.dim === pos.dim && (r.x - pos.x) * (r.x - pos.x) + (r.z - pos.z) * (r.z - pos.z) < reach * reach
      if (r.akey === akey || near) {
        var t = other ? other.title : r.id
        return { code: 'busy', msg: `${t} is ${r.pending ? 'being summoned' : 'being fought'} in that arena right now` }
      }
    }
    if (force) return null
    if (c.maxInstances > 0 && list.length >= c.maxInstances) {
      return { code: 'full', msg: `${list.length} bosses are out across the world (max_instances ${c.maxInstances})` }
    }
    var gap = this.arenaGapLeft(server, akey)
    if (gap > 0) return { code: 'gap', msg: `the arena is still settling after the last fight (${Math.ceil(gap / 60000)} minutes)` }
    var mine = party ? party.id : ''
    var line = this.queueOf(server, akey)
    for (var j = 0; j < line.length; j++) {
      if (line[j].party === mine) break
      if (line[j].ready) return { code: 'reserved', msg: `the arena is held for the party of ${line[j].by} (${Math.ceil((line[j].ready + c.queueTtlMs - Date.now()) / 60000)} minutes)` }
      return { code: 'waiting', msg: `the party of ${line[j].by} is waiting for that arena` }
    }
    return null
  },

  queueLoad(server) {
    return this.readJson(server, 'ttl.boss.queue', {})
  },

  queueSave(server, q) {
    Object.keys(q).forEach(id => { if (!q[id] || q[id].length === 0) delete q[id] })
    if (Object.keys(q).length === 0) server.persistentData.remove('ttl.boss.queue')
    else this.writeJson(server, 'ttl.boss.queue', q)
  },

  // Everyone waiting for one arena, any boss: reservations first, then by time of asking. [{boss, party, by, at, ready, ...}]
  queueOf(server, akey) {
    var q = this.queueLoad(server)
    var out = []
    Object.keys(q).forEach(id => q[id].forEach(e => {
      if (e.akey !== akey) return
      var row = { boss: id }
      for (var f in e) row[f] = e[f]
      out.push(row)
    }))
    out.sort((a, b) => (b.ready ? 1 : 0) - (a.ready ? 1 : 0) || a.at - b.at)
    return out
  },

  // The entry of a party in the queue of a boss, or null.
  queueEntry(server, bossId, partyId) {
    var list = this.queueLoad(server)[bossId] || []
    for (var i = 0; i < list.length; i++) {
      if (list[i].party === partyId) return list[i]
    }
    return null
  },

  // Puts the party in line (once per boss) and returns {place, eta} (eta in minutes, a rough guess).
  enqueue(server, def, akey, party, by) {
    var q = this.queueLoad(server)
    var list = q[def.id] || []
    var have = false
    list.forEach(e => { if (e.party === party.id) have = true })
    if (!have) list.push({ party: party.id, members: party.members, by: by, at: Date.now(), akey: akey, ready: 0 })
    q[def.id] = list
    this.queueSave(server, q)
    var line = this.queueOf(server, akey)
    var place = 1
    for (var i = 0; i < line.length; i++) {
      if (line[i].boss === def.id && line[i].party === party.id) {
        place = i + 1
        break
      }
    }
    var c = this.conf()
    var eta = Math.ceil(this.arenaGapLeft(server, akey) / 60000) + place * (c.fightMin + c.gapMs / 60000)
    if (!have) console.info(`[ttl] boss: ${def.id} queue: the party of ${by} is number ${place} for ${akey}`)
    return { place: place, eta: Math.round(eta) }
  },

  queueRemove(server, bossId, partyId) {
    var q = this.queueLoad(server)
    if (!q[bossId]) return
    q[bossId] = q[bossId].filter(e => e.party !== partyId)
    this.queueSave(server, q)
  },

  // Each poll: drop reservations past queue_ttl_minutes and parties with nobody online, and hand a free arena to the head
  // of its line (a ping; they have queue_ttl_minutes to summon).
  queueTick(server) {
    var q = this.queueLoad(server)
    var ids = Object.keys(q)
    if (ids.length === 0) return
    var c = this.conf()
    var now = Date.now()
    var self = this
    var online = {}
    server.getPlayerList().getPlayers().forEach(p => { online[self.uid(p)] = p })
    var changed = false
    ids.forEach(id => {
      q[id] = q[id].filter(e => {
        var here = (e.members || []).some(u => online[u])
        if (e.ready && now - e.ready > c.queueTtlMs) {
          self.tellParty(e, online, `Your turn at the arena of ${self.def(id) ? self.def(id).title : id} has passed.`)
          console.info(`[ttl] boss: ${id} queue: the party of ${e.by} let its turn pass`)
          changed = true
          return false
        }
        if (!here) {
          changed = true
          return false
        }
        return true
      })
    })
    if (changed) this.queueSave(server, q)
    var keys = {}
    ids.forEach(id => (q[id] || []).forEach(e => { keys[e.akey] = true }))
    Object.keys(keys).forEach(akey => {
      var line = self.queueOf(server, akey)
      if (line.length === 0 || line[0].ready) return
      var head = line[0]
      var def = self.def(head.boss)
      if (!def) return
      var parts = akey.split('@')
      var xz = (parts[1] || '0,0').split(',').map(Number)
      if (self.arenaBlock(server, def, { dim: parts[0], x: xz[0], z: xz[1] }, akey, { id: head.party }, false)) return
      var all = self.queueLoad(server)
      var row = all[head.boss] || []
      row.forEach(e => { if (e.party === head.party) e.ready = now })
      self.queueSave(server, all)
      self.tellParty(head, online, `The arena of ${def.title} is free. You have ${Math.round(c.queueTtlMs / 60000)} minutes to start the fight.`)
      console.info(`[ttl] boss: ${def.id} queue: the arena ${akey} is free, held for the party of ${head.by}`)
    })
  },

  tellParty(entry, online, line) {
    var members = entry.members || []
    members.forEach(u => {
      if (online[u]) online[u].tell(Text.gold(line))
    })
  },

  // A statue boss (spawn.kind = statue) has a story instance live or on the way: its seated statue stays away.
  statueAside(server, id) {
    var list = this.instances(server)
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === id && !list[i].wild) return true
    }
    return false
  },

  // ---- echoes ------------------------------------------------------------------------------------------------------

  // The world has seen this boss fall (the chronicle's firsts; test hook: server ttl.boss.testecho = JSON [ids]).
  hasFirst(server, id) {
    try {
      if (typeof TtlChronicle !== 'undefined' && typeof TtlChronicle.view === 'function') {
        var v = TtlChronicle.view(server)
        if (v && v.firsts && v.firsts[id]) return true
      }
    } catch (e) {
      console.warn(`[ttl] boss: reading the chronicle's firsts failed: ${e}`)
    }
    var w = this.readJson(server, 'ttl.world', {})
    if (w.firsts && w.firsts[id]) return true
    var t = this.readJson(server, 'ttl.boss.testecho', [])
    return Array.isArray(t) && t.indexOf(id) >= 0
  },

  // The act whose completion unlocks the boss (story.toml unlock_bosses), 0 when none.
  actOf(id) {
    var acts = (TtlData.story && TtlData.story.act) || []
    for (var i = 0; i < acts.length; i++) {
      if ((acts[i].unlock_bosses || []).indexOf(id) >= 0) return Number(acts[i].id)
    }
    return 0
  },

  // Echo health: echo_hp_mult only for a party whose highest act (online members) is below the boss's act.
  echoHp(server, def, party) {
    var act = this.actOf(def.id)
    if (!party || act === 0 || typeof TtlStory === 'undefined' || typeof TtlStory.actsDone !== 'function') return 1
    var best = 0
    var self = this
    party.members.forEach(u => {
      var p = self.onlineByUid(server, u)
      if (p) best = Math.max(best, Number(TtlStory.actsDone(p)) || 0)
    })
    return best < act ? this.conf().echoHp : 1
  },

  // ---- scoreboard kills -------------------------------------------------------------------------------------

  objective(def) {
    return `ttl.b.${def.id}`
  },

  ensureObjectives(server) {
    var board = server.getScoreboard()
    var self = this
    this.defs().forEach(def => {
      var name = self.objective(def)
      if (board.getObjective(name)) return
      server.runCommandSilent(`scoreboard objectives add ${name} minecraft.killed:${def.entity.replace(':', '.')}`)
      if (!board.getObjective(name)) console.error(`[ttl] boss: could not create objective ${name}`)
    })
  },

  score(server, player, def) {
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective(this.objective(def))
      if (!obj) return 0
      var info = board.getPlayerScoreInfo(player, obj)
      return info ? info.value() : 0
    } catch (e) {
      console.error(`[ttl] boss: reading ${this.objective(def)} for ${player.username} failed: ${e}`)
      return 0
    }
  },

  // ---- commands on a dimension --------------------------------------------------------------------------------

  exec(server, dim, clause) {
    return server.runCommandSilent(`execute in ${dim} ${clause}`)
  },

  run(server, dim, cmd) {
    return this.exec(server, dim, `run ${cmd}`)
  },

  // The entity carrying this instance's tag, or null.
  find(server, dim, key) {
    var level = server.getLevel(dim)
    if (!level) return null
    var tag = `ttl.boss.${key}`
    var found = null
    level.getEntities().forEach(e => {
      if (!found && e.getTags().contains(tag)) found = e
    })
    return found
  },

  // ---- summoning --------------------------------------------------------------------------------------------

  // The place of an arena table: a landmark (landmarks.toml), a build (the anchor where it was placed, else the canon
  // x/z of design/builds; a fixed-ground build keeps its walking level) or x/z. Returns {dim, x, y?, z} or an error string.
  centreOf(server, a) {
    if (a.landmark) {
      var lms = (TtlData.landmarks && TtlData.landmarks.landmark) || []
      for (var i = 0; i < lms.length; i++) {
        if (lms[i].name === a.landmark) return { dim: TtlLife.OVERWORLD, x: lms[i].x, z: lms[i].z }
      }
      return `arena landmark ${a.landmark} is not in landmarks.toml`
    }
    if (a.build) {
      var bs = (TtlData.builds || []).filter(b => b.name === a.build)
      if (bs.length === 0) return `arena build ${a.build} is not in design/builds`
      var b = bs[0]
      var at = String(server.persistentData.getString(`ttl.build.${a.build}.at`) || '')
      if (at) {
        var p = at.split(' ').map(Number)
        return { dim: b.dimension, x: p[0], y: p[1], z: p[2] }
      }
      return { dim: b.dimension, x: b.x, y: b.ground === 'fixed' ? b.y : undefined, z: b.z }
    }
    if (a.x !== undefined) return { dim: a.dim || TtlLife.OVERWORLD, x: a.x, y: a.y, z: a.z }
    return null
  },

  // Where a boss goes: explicit opts.x/y/z first, then the encounter's place (spawn.at, else the arena), then opts.at
  // (the caller's position). Returns {dim, x, y?, z} (no y = the surface there) or an error string. A wild summon
  // (opts.wild) goes where it is told and is never leashed to the arena.
  arenaOf(server, def, opts) {
    var a = (def.spawn && def.spawn.at) || def.arena
    var centre = null
    if (a) {
      centre = this.centreOf(server, a)
      if (typeof centre === 'string') return centre
    }
    if (opts.x !== undefined) {
      var want = { dim: opts.dim, x: Math.floor(opts.x), y: opts.y === undefined ? undefined : Math.floor(opts.y), z: Math.floor(opts.z) }
      if (opts.wild) return want
      // A bound arena (radius) only accepts a summon inside it: the encounter happens there, nowhere else.
      if (a && a.radius !== undefined) {
        var dx = want.x - centre.x
        var dz = want.z - centre.z
        if (want.dim !== centre.dim || dx * dx + dz * dz > a.radius * a.radius) {
          return `${def.title} can only be summoned within ${a.radius} blocks of ${centre.x} ${centre.z} in ${centre.dim}`
        }
        want.arena = { x: centre.x, z: centre.z, radius: a.radius }
      }
      return want
    }
    if (centre) {
      if (a.radius !== undefined) centre.arena = { x: centre.x, z: centre.z, radius: a.radius }
      return centre
    }
    if (opts.at) return { dim: opts.at.dim, x: Math.floor(opts.at.x), y: Math.floor(opts.at.y), z: Math.floor(opts.at.z) }
    return `${def.id} has no arena: give coordinates, or summon it from a player`
  },

  // A boss with `requires` (ids of bosses that must have been beaten first) and/or `spawn.stages` (stages) only answers a
  // summoner who holds all of them; opts.force or opts.skipGate (ops, the wild roll) skips it. Never a story path: anyone
  // may fight any boss. Returns an error string or ''.
  gate(def, opts) {
    var req = def.requires || []
    var stages = (def.spawn && def.spawn.stages) || []
    if ((req.length === 0 && stages.length === 0) || opts.force || opts.skipGate) return ''
    var who = opts.summoner
    if (!who) return `${def.title} needs a summoner who has defeated ${req.concat(stages).join(', ')}`
    for (var i = 0; i < req.length; i++) {
      if (!who.stages.has(`ttl.defeated.${req[i]}`)) {
        var other = this.def(req[i])
        return `${def.title} only answers someone who has defeated ${other ? other.title : req[i]}`
      }
    }
    for (var j = 0; j < stages.length; j++) {
      if (!who.stages.has(stages[j])) return `${def.title} only answers someone who holds ${stages[j]}`
    }
    return ''
  },

  // Every check of a summon without doing it: {error, queue: true when the summoner's party may wait in line} or
  // {def, pos, akey, party, echo, ehp}. Used by summon() and the dry-run test assertions.
  plan(server, id, opts) {
    opts = opts || {}
    var c = this.conf()
    var def = this.def(id)
    if (!def) return { error: `unknown boss ${id} (one of ${this.defs().map(d => d.id).join(', ')})` }
    if (def.proxy && !c.proxies) return { error: `${def.title} is a proxy boss and proxy_bosses is off in bosses.toml` }
    var pos = this.arenaOf(server, def, opts)
    if (typeof pos === 'string') return { error: pos }
    if (TtlLife.isMortal(pos.dim)) return { error: 'bosses do not exist in the Mortal Realm' }
    if (!server.getLevel(pos.dim)) return { error: `unknown dimension ${pos.dim}` }
    if (this.outside(pos.dim, pos.x, pos.z)) return { error: `${pos.x} ${pos.z} is outside the continent: the mod's own spawns rule there` }
    var akey = this.arenaKey(pos)
    var list = this.instances(server)
    if (opts.wild) {
      // A wild boss is its own thing: one wild instance per id, never blocked by (and never blocking) a story fight.
      for (var i = 0; i < list.length; i++) {
        if (list[i].id === id && list[i].wild) return { error: `${def.title} is already out there` }
      }
      if (c.maxInstances > 0 && list.length >= c.maxInstances) return { error: `${list.length} bosses are out across the world (max_instances ${c.maxInstances})` }
      return { def: def, pos: pos, akey: akey, party: null, echo: false, ehp: 1 }
    }
    var gate = this.gate(def, opts)
    if (gate) return { error: gate }
    var party = opts.summoner ? this.partyKey(server, opts.summoner) : null
    if (!opts.force && !opts.skipCooldown) {
      var left = c.scope === 'server' ? this.cooldownLeft(server, def) : party ? this.partyCooldownLeft(server, def, party) : 0
      if (left > 0) {
        return { error: c.scope === 'server' ? `${def.title} cannot be summoned for another ${Math.ceil(left / 60000)} minutes`
          : `Your party has fought ${def.title} too recently: another ${Math.ceil(left / 60000)} minutes` }
      }
    }
    if (!opts.force && party && c.maxPerParty > 0) {
      var mine = list.filter(r => r.owner === party.id && !r.wild)
      if (mine.length >= c.maxPerParty) {
        var od = this.def(mine[0].id)
        return { error: `Your party already has ${od ? od.title : mine[0].id} out: finish that fight first` }
      }
    }
    var block = this.arenaBlock(server, def, pos, akey, party, !!opts.force)
    if (block) return { error: `${def.title} cannot be summoned now: ${block.msg}`, queue: !!party, akey: akey, def: def, party: party }
    var echo = opts.echo === undefined ? this.hasFirst(server, id) : !!opts.echo
    return { def: def, pos: pos, akey: akey, party: party, echo: echo, ehp: echo ? this.echoHp(server, def, party) : 1 }
  },

  // Summons a boss; see the header for opts. {force: true} = skipGate + skipCooldown (ops). Returns an error string, or null
  // when the summon is under way: the entity appears once its chunk is loaded (a second or two), and the log says "summoned".
  // A summoner whose arena is busy is put in its queue (the returned line says the place and the ETA).
  summon(server, id, opts) {
    opts = opts || {}
    var plan = this.plan(server, id, opts)
    if (plan.error) {
      if (plan.queue && opts.summoner) {
        var q = this.enqueue(server, plan.def, plan.akey, plan.party, opts.by || String(opts.summoner.username))
        return `${plan.error}. Your party is number ${q.place} in line (about ${q.eta} minutes); you will be told when the arena is yours.`
      }
      return plan.error
    }
    var def = plan.def
    var pos = plan.pos
    if (plan.party) this.queueRemove(server, id, plan.party.id)
    var seq = Number(server.persistentData.getInt('ttl.boss.seq')) + 1
    server.persistentData.putInt('ttl.boss.seq', seq)
    var ctx = {
      id: id, key: `k${seq}`, dim: pos.dim, x: pos.x, y: pos.y, z: pos.z, by: opts.by || '', tries: 0, arena: pos.arena,
      wild: !!opts.wild, duel: !!opts.duel, region: opts.region || '', near: opts.near || '', akey: plan.akey,
      owner: plan.party ? plan.party.id : '', echo: plan.echo, ehp: plan.ehp, awake: !!opts.awake
    }
    this.pending[ctx.key] = { id: id, wild: ctx.wild, akey: ctx.akey, owner: ctx.owner, dim: pos.dim, x: pos.x, z: pos.z }
    this.run(server, pos.dim, `forceload add ${pos.x} ${pos.z}`)
    console.info(`[ttl] boss: summoning ${id} at ${pos.dim} ${pos.x} ${pos.y === undefined ? 'surface' : pos.y} ${pos.z}${ctx.by ? ` (asked by ${ctx.by})` : ''}${ctx.echo ? ' (an echo)' : ''}${ctx.awake ? ' (awake)' : ''}`)
    server.scheduleInTicks(20, () => this.attempt(server, ctx))
    return null
  },

  nbt(def, ctx) {
    var name = JSON.stringify({ text: this.titleOf(def, ctx.echo), color: this.COLORS[def.tier] || 'gold' })
    return `{NoAI:${ctx.awake ? 0 : 1}b,PersistenceRequired:1b,CustomNameVisible:1b,CustomName:'${name}',Tags:["ttl.boss","ttl.bossid.${def.id}","ttl.boss.${ctx.key}"]}`
  },

  // The seated statue of a statue boss steps aside (is discarded) while its story instance is live.
  statueStepsAside(server, def, ctx) {
    var tag = def.spawn && def.spawn.kind === 'statue' ? def.spawn.statue : ''
    if (!tag || ctx.wild) return
    var level = server.getLevel(ctx.dim)
    if (!level) return
    var n = 0
    level.getEntities().forEach(e => {
      if (e.getTags().contains(tag) && !e.getTags().contains(this.TAG)) {
        e.discard()
        n++
      }
    })
    console.info(`[ttl] boss: the statue ${tag} steps aside for ${def.id} (${n} removed)`)
  },

  // One try at spawning: the chunk may still be loading after the forceload, so it retries for ~10 seconds.
  attempt(server, ctx) {
    try {
      var def = this.def(ctx.id)
      var nbt = this.nbt(def, ctx)
      // A retry after a try whose entity find() could not see must not leave a second boss behind.
      if (ctx.tries > 0) this.run(server, ctx.dim, `kill @e[tag=ttl.boss.${ctx.key}]`)
      if (ctx.y === undefined) {
        this.exec(server, ctx.dim, `positioned ${ctx.x} 0 ${ctx.z} positioned over motion_blocking_no_leaves run summon ${def.entity} ~ ~ ~ ${nbt}`)
      } else {
        this.run(server, ctx.dim, `summon ${def.entity} ${ctx.x + 0.5} ${ctx.y} ${ctx.z + 0.5} ${nbt}`)
      }
      var e = this.find(server, ctx.dim, ctx.key)
      if (e) {
        this.register(server, def, ctx, e)
        return
      }
      ctx.tries++
      if (ctx.tries < 10) {
        server.scheduleInTicks(20, () => this.attempt(server, ctx))
        return
      }
      console.error(`[ttl] boss: ${ctx.id} could not be summoned at ${ctx.dim} ${ctx.x} ${ctx.z} (chunk never loaded, or ${def.entity} refused to spawn there)`)
    } catch (e) {
      console.error(`[ttl] boss: summoning ${ctx.id} failed: ${e}`)
    }
    delete this.pending[ctx.key]
    this.run(server, ctx.dim, `forceload remove ${ctx.x} ${ctx.z}`)
  },

  register(server, def, ctx, e) {
    var now = Date.now()
    var rec = {
      id: def.id, dim: ctx.dim, x: e.getX(), y: e.getY(), z: e.getZ(), started: now, state: 'idle',
      base: Math.round(e.getMaxHealth()), n: 0, phase: 0, hit: {}, near: {}, names: {}, seen: {}, last: [],
      gone: 0, idle: now, fx: ctx.x, fz: ctx.z, by: ctx.by, dmg: {}, party: {}, pt: {}, akey: ctx.akey || '',
      owner: ctx.owner || ''
    }
    if (ctx.wild) rec.wild = true
    if (ctx.duel) rec.duel = true
    if (ctx.echo) {
      rec.echo = true
      rec.ehp = ctx.ehp || 1
    }
    if (ctx.awake) {
      // Summoned awake (the March of the Horde): no NoAI wait, the fight runs from the first poll.
      rec.awake = true
      rec.state = 'fight'
    }
    if (ctx.arena) {
      // Leash: a boss of a bound arena that is pulled away is put back (see fight()).
      rec.ax = ctx.arena.x
      rec.az = ctx.arena.z
      rec.ay = e.getY()
      rec.rad = ctx.arena.radius
    }
    var near = this.near(this.players(server), rec, def)
    var mult = this.scale(server, rec, def, e, near.length)
    var active = this.load(server)
    active[ctx.key] = rec
    this.save(server, active)
    delete this.pending[ctx.key]
    this.ensureBar(server, ctx.key, rec, def)
    try {
      this.statueStepsAside(server, def, ctx)
    } catch (err) {
      console.error(`[ttl] boss: the statue of ${def.id} could not step aside: ${err}`)
    }
    var n = Math.max(1, near.length)
    console.info(`[ttl] boss: ${def.id} summoned${ctx.wild ? ' (wild)' : ''}${ctx.echo ? ' (an echo)' : ''}${ctx.awake ? ' (awake)' : ''} (hp ×${mult}, ${n} player${n === 1 ? '' : 's'})`)
    if (ctx.wild) {
      // A wild boss is announced by bosses/wild.js (title, chat, Discord #story), not as an ordinary summon.
      try {
        TtlWild.announce(server, def, ctx)
      } catch (err) {
        console.error(`[ttl] boss: announcing wild ${def.id} failed: ${err}`)
      }
      return
    }
    var title = this.titleOf(def, rec.echo)
    var line = rec.awake ? `${title} has arrived.` : `${title} has been summoned.`
    this.players(server).forEach(p => p.tell(Text.gold(line)))
  },

  // Players of the list within the boss's range.
  near(players, rec, def) {
    var self = this
    return players.filter(p => !p.isSpectator() && self.distance(p, rec.dim, rec.x, rec.y, rec.z) <= def.range)
  },

  // Max health = vanilla x (hp_mult + per_player_mult x (n - 1)) x the echo multiplier, n at least 1. Keeps the health
  // fraction (a boss that already took a hit keeps its wound when a second player arrives). Returns the multiplier.
  scale(server, rec, def, e, n) {
    n = Math.max(1, n)
    var mult = Math.round((def.hp_mult + def.per_player_mult * (n - 1)) * (rec.ehp || 1) * 100) / 100
    var frac = e.getMaxHealth() > 0 ? e.getHealth() / e.getMaxHealth() : 1
    var hp = Math.max(rec.base, Math.round(rec.base * mult))
    this.exec(server, rec.dim, `as @e[tag=ttl.boss.${this.keyOf(e)},limit=1] run attribute @s minecraft:generic.max_health base set ${hp}`)
    e.setHealth(Math.max(1, frac * e.getMaxHealth()))
    rec.n = n
    if (e.getMaxHealth() < hp - 1) console.warn(`[ttl] boss: ${def.id} max health is ${e.getMaxHealth()}, wanted ${hp} (attribute clamp)`)
    return mult
  },

  // The instance key of a boss or minion entity ('k3'), or null.
  keyOf(e) {
    var key = null
    e.getTags().forEach(t => {
      var s = String(t)
      if (/^ttl\.boss\.k\d+$/.test(s)) key = s.substring(9)
    })
    return key
  },

  noteHit(e, attacker, damage) {
    var key = this.keyOf(e)
    if (!key) return
    if (!this.hits[key]) this.hits[key] = {}
    var u = this.uid(attacker)
    this.hits[key][u] = String(attacker.username)
    if (!this.dmg[key]) this.dmg[key] = {}
    this.dmg[key][u] = (this.dmg[key][u] || 0) + (damage > 0 ? damage : 0)
  },

  // Folds the damage seen since the last poll into the record.
  foldHits(key, rec) {
    if (this.hits[key]) {
      for (var u in this.hits[key]) {
        rec.hit[u] = true
        rec.names[u] = this.hits[key][u]
      }
      delete this.hits[key]
    }
    if (this.dmg[key]) {
      rec.dmg = rec.dmg || {}
      for (var d in this.dmg[key]) rec.dmg[d] = (rec.dmg[d] || 0) + this.dmg[key][d]
      delete this.dmg[key]
    }
  },

  // ---- parties ----------------------------------------------------------------------------------------------------

  // The party a player is in: {id, members: [lowercase uuids]} or null. The FTB Teams party team (a player's own solo team
  // is not a party). Test hook: server `ttl.boss.testparty` = JSON {members: [uuids]} (`/ttl boss testparty`) makes those
  // players one party and lets test bots count for it; without a hook bots never share party credit.
  partyOf(server, player) {
    var u = this.uid(player)
    // A raid group (party/raid.js, WP-W7) comes first: light and dark friends fight as one roster. Contract:
    // TtlRaid.groupOf(server, player) -> {id, members: [uuids]} or null.
    if (typeof TtlRaid !== 'undefined' && typeof TtlRaid.groupOf === 'function') {
      try {
        var raid = TtlRaid.groupOf(server, player)
        if (raid && raid.members && raid.members.length) {
          var rm = []
          raid.members.forEach(m => rm.push(String(m).toLowerCase()))
          return { id: `raid:${raid.id}`, members: rm }
        }
      } catch (e) {
        console.warn(`[ttl] boss: the raid layer failed for ${player.username}: ${e}`)
      }
    }
    var fake = this.testParty(server)
    if (fake) return fake.members.indexOf(u) >= 0 ? { id: 'test', members: fake.members } : null
    // The party layer (party/party.js) is the one reader of FTB Teams; the direct read below only runs without it.
    if (typeof TtlParty !== 'undefined' && typeof TtlParty.partyOf === 'function') {
      try {
        var mine = TtlParty.partyOf(server, player)
        return mine ? { id: mine.id, members: mine.members } : null
      } catch (e) {
        console.warn(`[ttl] boss: the party layer failed for ${player.username}: ${e}`)
        return null
      }
    }
    var cls = this.ftb()
    if (!cls) return null
    try {
      var api = cls.api()
      if (!api.isManagerLoaded()) return null
      var opt = api.getManager().getTeamForPlayer(player)
      if (!opt.isPresent()) return null
      var team = opt.get()
      if (!team.isPartyTeam()) return null
      var members = []
      team.getMembers().forEach(m => members.push(String(m).toLowerCase()))
      return { id: String(team.getId()), members: members }
    } catch (e) {
      console.warn(`[ttl] boss: reading the FTB party of ${player.username} failed: ${e}`)
      return null
    }
  },

  ftb() {
    if (this.teamApi === undefined) {
      try {
        this.teamApi = Java.loadClass('dev.ftb.mods.ftbteams.api.FTBTeamsAPI')
      } catch (e) {
        this.teamApi = null
        console.warn(`[ttl] boss: FTB Teams API not available, no party credit: ${e}`)
      }
    }
    return this.teamApi
  },

  testParty(server) {
    var raw = String(server.persistentData.getString('ttl.boss.testparty') || '')
    if (!raw) return null
    try {
      var p = JSON.parse(raw)
      return p && p.members && p.members.length ? p : null
    } catch (e) {
      return null
    }
  },

  isBot(server, p) {
    try {
      return typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(String(p.username))
    } catch (e) {
      return false
    }
  },

  // First time a player stands near the boss, freeze the roster of their party (see the header).
  snapParty(server, rec, near) {
    rec.party = rec.party || {}
    rec.pt = rec.pt || {}
    near.forEach(p => {
      var u = this.uid(p)
      if (rec.pt[u] !== undefined) return
      var team = this.partyOf(server, p)
      rec.pt[u] = team ? team.id : ''
      if (team && !rec.party[team.id]) rec.party[team.id] = team.members
    })
  },

  // ---- boss bar -----------------------------------------------------------------------------------------------

  barId(key) {
    return `ttl:boss_${key}`
  },

  ensureBar(server, key, rec, def) {
    if (this.bars[key]) return
    var id = this.barId(key)
    var text = JSON.stringify({ text: this.titleOf(def, rec.echo), color: this.COLORS[def.tier] || 'gold' })
    // `bossbar add` fails when the bar survived a restart; the sets below then simply reuse it.
    server.runCommandSilent(`bossbar add ${id} ${text}`)
    server.runCommandSilent(`bossbar set ${id} color ${this.BAR_COLORS[def.tier] || 'red'}`)
    server.runCommandSilent(`bossbar set ${id} style notched_10`)
    server.runCommandSilent(`bossbar set ${id} visible true`)
    this.bars[key] = true
  },

  updateBar(server, key, rec, def, e) {
    var id = this.barId(key)
    server.runCommandSilent(`bossbar set ${id} max ${Math.max(1, Math.round(e.getMaxHealth()))}`)
    server.runCommandSilent(`bossbar set ${id} value ${Math.max(0, Math.ceil(e.getHealth()))}`)
    this.exec(server, rec.dim, `positioned ${Math.floor(rec.x)} ${Math.floor(rec.y)} ${Math.floor(rec.z)} run bossbar set ${id} players @a[distance=..${def.range + 16}]`)
  },

  // ---- the poll -----------------------------------------------------------------------------------------------

  tick(server) {
    try {
      this.queueTick(server)
    } catch (e) {
      console.error(`[ttl] boss: queue poll failed: ${e}`)
    }
    var active = this.load(server)
    var keys = Object.keys(active)
    if (keys.length === 0) return
    var players = this.players(server)
    var now = Date.now()
    var done = []
    var self = this
    keys.forEach(key => {
      try {
        if (self.step(server, key, active[key], players, now) === 'done') done.push(key)
      } catch (e) {
        console.error(`[ttl] boss: ${active[key].id} poll failed: ${e}`)
      }
    })
    done.forEach(k => delete active[k])
    this.save(server, active)
  },

  // One poll of one boss. Returns 'done' when the record is finished (defeated, lost or removed).
  step(server, key, rec, players, now) {
    var def = this.def(rec.id)
    if (!def) {
      console.warn(`[ttl] boss: ${rec.id} is no longer defined in bosses.toml, dropping it`)
      this.cleanup(server, key, rec, true)
      return 'done'
    }
    this.ensureBar(server, key, rec, def)
    var e = this.find(server, rec.dim, key)
    if (e && !e.isAlive()) {
      this.finish(server, key, rec, def, players)
      return 'done'
    }
    if (!e) {
      rec.gone = (rec.gone || 0) + 1
      // The chunk is forceloaded, so an entity that stays missing is dead or discarded.
      if (rec.gone >= 3) {
        this.finish(server, key, rec, def, players)
        return 'done'
      }
      return 'keep'
    }
    rec.gone = 0
    rec.x = e.getX()
    rec.y = e.getY()
    rec.z = e.getZ()
    var near = this.near(players, rec, def)
    var cfg = this.conf()
    rec.last = near.map(p => this.uid(p))
    this.foldHits(key, rec)
    near.forEach(p => {
      var u = this.uid(p)
      rec.near[u] = (rec.near[u] || 0) + 1
      rec.names[u] = String(p.username)
    })
    this.snapParty(server, rec, near)
    if (rec.state === 'idle') {
      var idleMs = rec.wild ? cfg.wildIdleMs : cfg.idleMs
      if (near.length > 0) {
        this.wake(server, key, rec, def, e, near)
      } else if (now - rec.idle > idleMs) {
        console.info(`[ttl] boss: ${def.id} removed, nobody came within ${idleMs / 60000} minutes${rec.wild ? ' (wild)' : ''}`)
        this.cleanup(server, key, rec, true)
        return 'done'
      }
    } else {
      // A fight everybody walked away from frees its arena after idle_minutes (it would hold the queue forever).
      if (near.length > 0) {
        rec.idle = now
      } else if (now - rec.idle > (rec.wild ? cfg.wildIdleMs : cfg.idleMs)) {
        console.info(`[ttl] boss: ${def.id} removed, the fight was left for ${Math.round((now - rec.idle) / 60000)} minutes${rec.wild ? ' (wild)' : ''}`)
        this.cleanup(server, key, rec, true)
        return 'done'
      }
      this.fight(server, key, rec, def, e, near, cfg)
    }
    // Baseline for kill credit: the objective values while the boss is still alive.
    players.forEach(p => { rec.seen[this.uid(p)] = this.score(server, p, def) })
    this.updateBar(server, key, rec, def, e)
    return 'keep'
  },

  wake(server, key, rec, def, e, near) {
    rec.state = 'fight'
    rec.idle = Date.now()
    this.scale(server, rec, def, e, near.length)
    this.exec(server, rec.dim, `as @e[tag=ttl.boss.${key},limit=1] run data merge entity @s {NoAI:0b}`)
    near.forEach(p => p.tell(Text.gold(`${def.title} awakens.`)))
    console.info(`[ttl] boss: ${def.id} awake (${near.length} player${near.length === 1 ? '' : 's'}, max health ${Math.round(e.getMaxHealth())})`)
  },

  fight(server, key, rec, def, e, near, cfg) {
    if (cfg.untame) this.exec(server, rec.dim, `as @e[tag=ttl.boss.${key},limit=1] if data entity @s Owner run data remove entity @s Owner`)
    if (rec.rad !== undefined) {
      var lx = rec.x - rec.ax
      var lz = rec.z - rec.az
      var leash = rec.rad * 2
      if (lx * lx + lz * lz > leash * leash) {
        this.exec(server, rec.dim, `as @e[tag=ttl.boss.${key},limit=1] run tp @s ${rec.ax} ${rec.ay} ${rec.az}`)
        console.info(`[ttl] boss: ${def.id} was pulled out of its arena, back to ${rec.ax} ${rec.az}`)
      }
    }
    var phases = def.phases || []
    var frac = e.getMaxHealth() > 0 ? e.getHealth() / e.getMaxHealth() : 1
    while (rec.phase < phases.length && frac <= phases[rec.phase].at_hp) {
      this.phase(server, key, rec, def, phases[rec.phase], near)
      rec.phase++
    }
  },

  phase(server, key, rec, def, ph, near) {
    console.info(`[ttl] boss: ${def.id} phase ${rec.phase + 1} at ${Math.round(ph.at_hp * 100)}% health`)
    near.forEach(p => p.tell(Text.red(ph.say)))
    if (ph.enrage !== undefined) {
      this.exec(server, rec.dim, `as @e[tag=ttl.boss.${key},limit=1] run effect give @s minecraft:strength 1200 ${ph.enrage} true`)
    }
    if (ph.minions) {
      for (var i = 0; i < ph.count; i++) {
        var angle = (2 * Math.PI * i) / ph.count
        var dx = Math.round(4 * Math.cos(angle))
        var dz = Math.round(4 * Math.sin(angle))
        this.exec(server, rec.dim, `positioned ${Math.floor(rec.x)} ${Math.floor(rec.y)} ${Math.floor(rec.z)} run summon ${ph.minions} ~${dx} ~ ~${dz} {PersistenceRequired:1b,Tags:["${this.MINION}","ttl.boss.m${key}"]}`)
      }
    }
  },

  // ---- the end ------------------------------------------------------------------------------------------------

  // Minions, bar and forceload of a finished or removed boss; `kill` also removes the boss entity itself.
  cleanup(server, key, rec, kill) {
    this.run(server, rec.dim, `kill @e[tag=ttl.boss.m${key}]`)
    if (kill) this.run(server, rec.dim, `kill @e[tag=ttl.boss.${key}]`)
    server.runCommandSilent(`bossbar remove ${this.barId(key)}`)
    delete this.bars[key]
    delete this.hits[key]
    delete this.dmg[key]
    // Leave the chunk loaded a moment so the death loot and experience are placed.
    server.scheduleInTicks(100, () => this.run(server, rec.dim, `forceload remove ${rec.fx} ${rec.fz}`))
  },

  // The boss is dead (or gone). Winners: whoever the kill objective credits; whoever hit it, or stood in range for
  // presence_secs, and is within range now; and, when no player is credited with the kill, everybody in range at the
  // last poll. Their party members (see partyExtras) share the kill. Nobody qualifying means the boss was lost without a
  // fight: no reward, no cooldown.
  finish(server, key, rec, def, players) {
    var byId = {}
    players.forEach(p => { byId[this.uid(p)] = p })
    var winners = {}
    var inRange = p => this.distance(p, rec.dim, rec.x, rec.y, rec.z) <= def.range
    var killers = 0
    players.forEach(p => {
      var u = this.uid(p)
      if (rec.seen[u] !== undefined && this.score(server, p, def) > rec.seen[u]) {
        winners[u] = p
        killers++
      }
    })
    this.foldHits(key, rec)
    var presence = this.conf().presence
    for (var u1 in rec.hit) {
      if (byId[u1] && inRange(byId[u1])) winners[u1] = byId[u1]
    }
    if (presence > 0) {
      for (var u2 in rec.near) {
        if (rec.near[u2] >= presence && byId[u2] && inRange(byId[u2])) winners[u2] = byId[u2]
      }
    }
    if (killers === 0) {
      rec.last.forEach(u3 => {
        if (byId[u3] && inRange(byId[u3])) winners[u3] = byId[u3]
      })
    }
    var names = []
    for (var w in winners) names.push(String(winners[w].username))
    this.cleanup(server, key, rec, false)
    if (names.length === 0) {
      console.info(`[ttl] boss: ${def.id} lost without a fight (no player in range, nothing rewarded)`)
      return
    }
    var now = Date.now()
    var cfgEnd = this.conf()
    if (!rec.wild) {
      // A story kill settles its arena for arena_gap_minutes; the cooldown is stamped on every credited soul below.
      var gaps = this.readJson(server, 'ttl.boss.arena', {})
      Object.keys(gaps).forEach(g => { if (now - Number(gaps[g].t) > Math.max(cfgEnd.gapMs, 3600000)) delete gaps[g] })
      gaps[this.recKey(rec)] = { t: now, id: def.id }
      this.writeJson(server, 'ttl.boss.arena', gaps)
      if (cfgEnd.scope === 'server') server.persistentData.putString(`ttl.boss.last.${def.id}`, String(now))
    }
    var stamp = p => {
      if (rec.wild) return
      try {
        this.stampKill(server, p, def.id, now)
      } catch (e) {
        console.error(`[ttl] boss: stamping the ${def.id} cooldown on ${p.username} failed: ${e}`)
      }
    }
    for (var w1 in winners) stamp(winners[w1])
    var mult = rec.wild ? cfgEnd.wildMult : 1
    for (var w2 in winners) {
      try {
        this.reward(server, def, winners[w2], { mult: mult, duel: rec.duel })
      } catch (e) {
        console.error(`[ttl] boss: rewarding ${winners[w2].username} for ${def.id} failed: ${e}`)
      }
    }
    var shared = this.partyExtras(server, rec, def, winners, byId)
    shared.forEach(x => {
      stamp(x.p)
      try {
        this.reward(server, def, x.p, { mult: mult, duel: rec.duel, core: x.core, party: true })
        names.push(String(x.p.username))
        console.info(`[ttl] boss: ${def.id} party credit for ${x.p.username} (party of ${x.via}${x.core ? ', Skill Core' : ''})`)
      } catch (e) {
        console.error(`[ttl] boss: party credit for ${x.p.username} (${def.id}) failed: ${e}`)
      }
    })
    console.info(`[ttl] boss: ${def.id} defeated by ${names.join(', ')}${killers > 0 ? '' : ' (no kill credit: shared by everyone in the fight)'}${rec.wild ? ' (wild)' : ''}${rec.echo ? ' (an echo)' : ''}`)
    this.announce(server, def, names, rec.echo)
  },

  // Party members who share the kill without being contributors themselves: in the roster frozen when their party first
  // stood near the boss (and so was the credited member), online, Life 2, not a spectator, in the boss's dimension and
  // within party_credit_range x range. Test bots count only while a `testparty` is set. At most core_per_party of each
  // party also get a Skill Core (the most damage dealt, then the longest in range). Returns [{p, core, via}].
  partyExtras(server, rec, def, winners, byId) {
    var cfg = this.conf()
    var out = {}
    var seenParty = {}
    var reach = def.range * cfg.partyRange
    var testing = !!this.testParty(server)
    var wantCore = !!(def.rewards && def.rewards.core)
    for (var w in winners) {
      var team = this.partyOf(server, winners[w])
      if (!team || !rec.party || !rec.party[team.id] || rec.party[team.id].indexOf(w) < 0) continue
      var picked = []
      rec.party[team.id].forEach(u => {
        var p = byId[u]
        if (winners[u] || out[u] || !p || seenParty[u]) return
        if (p.isSpectator() || TtlLife.phase(p) !== 'life2') return
        if (!testing && this.isBot(server, p)) return
        if (this.distance(p, rec.dim, rec.x, rec.y, rec.z) > reach) return
        seenParty[u] = true
        picked.push({ u: u, p: p, via: String(winners[w].username) })
      })
      var dmg = rec.dmg || {}
      var near = rec.near || {}
      picked.sort((a, b) => (dmg[b.u] || 0) - (dmg[a.u] || 0) || (near[b.u] || 0) - (near[a.u] || 0))
      picked.forEach((x, i) => {
        x.core = wantCore && i < cfg.corePerParty
        out[x.u] = x
      })
    }
    return Object.keys(out).map(u => out[u])
  },

  // Stage, kill count, rep, coins and Skill Core for one credited player, plus the boss's kill_rep (a regicide costs
  // Dwargon rep, light or dark). opts: {mult} (wild rewards_mult on rep and coins, never the core), {core: false} (a
  // party member without a core), {duel} (no kill_rep), {party}. WP10 (bosses/rewards.js) may later replace the payout.
  reward(server, def, p, opts) {
    opts = opts || {}
    var mult = opts.mult === undefined ? 1 : opts.mult
    var name = String(p.username)
    p.stages.add(`ttl.boss.t${def.tier}`)
    // Also the convention compat/tombstone_bosses.js and `requires` read: ttl.defeated.<boss id>.
    p.stages.add(`ttl.defeated.${def.id}`)
    var kills = {}
    try {
      kills = JSON.parse(String(p.persistentData.getString('ttl.boss.kills')) || '{}')
    } catch (e) {
      kills = {}
    }
    kills[def.id] = (kills[def.id] || 0) + 1
    p.persistentData.putString('ttl.boss.kills', JSON.stringify(kills))
    var r = def.rewards || {}
    var rep = r.rep || {}
    Object.keys(rep).forEach(f => {
      var n = Math.round(rep[f] * mult)
      if (n !== 0) server.runCommandSilent(`ttl rep add ${name} ${f} ${n}`)
    })
    var coins = r.coins || {}
    Object.keys(coins).forEach(c => {
      var n = Math.round(coins[c] * mult)
      if (n >= 1) server.runCommandSilent(`give ${name} tensura:${c}_coin ${n}`)
    })
    if (r.core && opts.core !== false) this.giveCore(server, p, def)
    if (!opts.duel) this.killRep(server, def, p)
    p.tell(Text.gold(opts.party ? `You share your party's victory over ${def.title}.` : `You defeated ${def.title}.`))
  },

  // bosses.toml kill_rep: { faction = n, flag, unless_flag }. With the story core loaded TtlStory.onBossKill applies all of
  // it (rep, flag, the honour-duel exemption) and this applies nothing, so nothing is paid twice; without it only the rep.
  killRep(server, def, p) {
    var kr = def.kill_rep
    if (!kr) return
    var name = String(p.username)
    if (typeof TtlStory !== 'undefined' && typeof TtlStory.onBossKill === 'function') {
      try {
        TtlStory.onBossKill(server, p, def.id)
      } catch (e) {
        console.error(`[ttl] boss: story kill cost of ${def.id} for ${name} failed: ${e}`)
      }
      return
    }
    Object.keys(kr).forEach(f => {
      if (f !== 'flag' && f !== 'unless_flag') server.runCommandSilent(`ttl rep add ${name} ${f} ${kr[f]}`)
    })
  },

  // ttl:skill_core is registered in startup_scripts/ttl/items.js; if the item is ever missing the core is owed and
  // counted on the player (`ttl.boss.core.owed`) and paid at the next login by payOwed.
  giveCore(server, p, def) {
    var exists = false
    try {
      exists = !!Item.exists('ttl:skill_core')
    } catch (e) {
      exists = false
    }
    if (exists) {
      server.runCommandSilent(`give ${p.username} ttl:skill_core 1`)
      return
    }
    var owed = p.persistentData.getInt('ttl.boss.core.owed') + 1
    p.persistentData.putInt('ttl.boss.core.owed', owed)
    console.warn(`[ttl] boss: ttl:skill_core does not exist yet, ${p.username} is owed ${owed} Skill Core(s) (${def.id})`)
  },

  payOwed(server, p) {
    var owed = p.persistentData.getInt('ttl.boss.core.owed')
    if (owed <= 0) return
    var exists = false
    try {
      exists = !!Item.exists('ttl:skill_core')
    } catch (e) {
      exists = false
    }
    if (!exists) return
    p.persistentData.putInt('ttl.boss.core.owed', 0)
    server.runCommandSilent(`give ${p.username} ttl:skill_core ${owed}`)
    p.tell(Text.gold(`You are handed ${owed} Skill Core(s) owed from earlier victories.`))
    console.info(`[ttl] boss: paid ${owed} owed Skill Core(s) to ${p.username}`)
  },

  announce(server, def, names, echo) {
    var line = `${this.titleOf(def, echo)} has fallen to ${names.join(', ')}.`
    this.players(server).forEach(p => p.tell(Text.gold(line)))
    try {
      if (typeof TtlDiscord === 'undefined') return
      var humans = names.filter(n => !TtlDiscord.isBot(n))
      if (humans.length === 0) return
      TtlDiscord.post(server, `${humans.map(n => TtlDiscord.name(n)).join(', ')} defeated **${def.title}**!${echo ? ' (an echo)' : ''}`)
      humans.forEach(n => TtlDiscord.also('hall boss', () => TtlHall.noteBoss(server, n, def.title)))
    } catch (e) {
      console.warn(`[ttl] boss: Discord post failed: ${e}`)
    }
  },

  // Ops: end a boss without rewards. Returns how many were removed.
  abort(server, id) {
    var active = this.load(server)
    var n = 0
    for (var k in active) {
      if (id && active[k].id !== id) continue
      this.cleanup(server, k, active[k], true)
      delete active[k]
      n++
    }
    this.save(server, active)
    // A freed arena goes to the head of its line at once.
    this.queueTick(server)
    return n
  },

  // Once per boot (cooldown_scope party): the old server-wide stamps ttl.boss.last.<id> become one arena gap at the boss's
  // own arena and are removed; records from before WP-W2 get an arena key and an empty owner.
  migrate(server) {
    if (this.conf().scope === 'server') return
    var gaps = this.readJson(server, 'ttl.boss.arena', {})
    var moved = 0
    var self = this
    this.defs().forEach(def => {
      var t = self.lastDefeat(server, def.id)
      if (!t) return
      var pos = self.arenaOf(server, def, {})
      if (typeof pos !== 'string') {
        var k = self.arenaKey(pos)
        if (!gaps[k] || gaps[k].t < t) gaps[k] = { t: t, id: def.id }
      }
      server.persistentData.remove(`ttl.boss.last.${def.id}`)
      moved++
    })
    if (moved > 0) {
      this.writeJson(server, 'ttl.boss.arena', gaps)
      console.info(`[ttl] boss: ${moved} server-wide cooldown stamp(s) turned into arena gaps (cooldowns are per party now)`)
    }
    var active = this.load(server)
    var fixed = 0
    for (var key in active) {
      if (active[key].akey === undefined) {
        active[key].akey = this.recKey(active[key])
        active[key].owner = ''
        fixed++
      }
    }
    if (fixed > 0) this.save(server, active)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlBoss.ensureObjectives(server)
  } catch (e) {
    console.error(`[ttl] boss: creating the kill objectives failed: ${e}`)
  }
  try {
    TtlBoss.migrate(server)
  } catch (e) {
    console.error(`[ttl] boss: migrating the old cooldown stamps failed: ${e}`)
  }
  var loop = () => server.scheduleInTicks(TtlBoss.POLL, () => {
    try {
      TtlBoss.tick(server)
    } catch (e) {
      console.error(`[ttl] boss: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})

// Skill Cores owed from before the item existed are paid at login.
PlayerEvents.loggedIn(event => {
  try {
    var p = event.player
    var server = event.server
    server.scheduleInTicks(100, () => {
      try {
        TtlBoss.payOwed(server, p)
      } catch (err) {
        console.error(`[ttl] boss: paying owed cores failed: ${err}`)
      }
    })
  } catch (err) {
    console.error(`[ttl] boss: owed core login hook failed: ${err}`)
  }
})

// Damage dealers are recorded here; the poll turns them into contributors.
EntityEvents.afterHurt(event => {
  try {
    var e = event.entity
    if (e.isPlayer()) return
    if (!e.getTags().contains('ttl.boss')) return
    var attacker = event.source.actual
    if (attacker && attacker.isPlayer()) TtlBoss.noteHit(e, attacker, Number(event.damage) || 0)
  } catch (err) {
    console.error(`[ttl] boss: hit tracking failed: ${err}`)
  }
})

// Never natural ON THE CONTINENT: a boss entity that Minecraft spawns by itself there is cancelled. Summons carry the
// ttl.boss tag and come from a command (spawn type "command"), so they pass. Outside the continent (the Overworld beyond
// the canon coast, world-state.md §2.0) the mods' own spawns rule: nothing is cancelled. The line per spawn shows the real
// spawn type string.
try {
  EntityEvents.checkSpawn(event => {
    var blocked = false
    try {
      if (!TtlBoss.conf().blockNatural) return
      var entity = event.entity
      var id = String(entity.type)
      var def = TtlBoss.byEntity(id)
      if (!def) return
      // A proxy boss stands on an ordinary mob (Clayman on the arch daemon): that mob keeps spawning by itself. Every real
      // boss entity is wild-rolled by bosses/wild.js instead (Shizu included), so nothing is exempt any more.
      if (def.proxy) return
      var type = String(event.type)
      if (!TtlBoss.NATURAL.test(type)) {
        console.info(`[ttl] boss: ${id} spawn type=${type}: allowed`)
        return
      }
      var lvl = entity.level || event.level
      if (lvl && TtlBoss.outside(String(lvl.dimension), entity.getX(), entity.getZ())) {
        console.info(`[ttl] boss: ${id} spawn type=${type}: allowed (outside the continent)`)
        return
      }
      blocked = true
      console.info(`[ttl] boss: ${id} spawn type=${type}: blocked`)
    } catch (err) {
      console.error(`[ttl] boss: spawn check failed: ${err}`)
    }
    // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
    if (blocked) event.cancel()
  })
} catch (e) {
  console.warn(`[ttl] boss: EntityEvents.checkSpawn is not available, natural boss spawns are not blocked (${e})`)
}
