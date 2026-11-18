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
// Server persistentData: `ttl.boss.active` JSON {key: record}, `ttl.boss.seq`, `ttl.boss.last.<id>` (millis of the
// last defeat). Player: stage `ttl.boss.t<tier>`, `ttl.boss.kills` JSON {id: n}, `ttl.boss.core.owed` (Skill Cores
// not yet handed out because the item does not exist yet).
// Record: {id, dim, x, y, z, started, state idle|fight, base (vanilla max hp), n (players at last scaling), phase
// (phases done), hit/near/names (uuid maps: damage dealers, polls in range, display names), seen (objective values
// at the last poll), last (uuids in range at the last poll), gone (polls without the entity), idle (millis since
// nobody came), fx/fz (forceloaded block position), bar}.
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
  pending: {},
  bars: {},

  // ---- data -------------------------------------------------------------------------------------------------

  conf() {
    var f = (TtlData.bosses && TtlData.bosses.framework) || {}
    return {
      blockNatural: f.block_natural !== false,
      naturalAllow: f.natural_allow || [],
      idleMs: (f.idle_minutes === undefined ? 30 : Number(f.idle_minutes)) * 60000,
      presence: f.presence_secs === undefined ? 15 : Number(f.presence_secs),
      untame: f.untame !== false
    }
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

  lastDefeat(server, id) {
    return Number(String(server.persistentData.getString(`ttl.boss.last.${id}`)) || 0)
  },

  // Milliseconds of cooldown left for this boss (0 when free).
  cooldownLeft(server, def) {
    var left = this.lastDefeat(server, def.id) + def.cooldown_hours * 3600000 - Date.now()
    return left > 0 ? left : 0
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

  // Where a boss goes: explicit opts.x/y/z first, then the definition's arena, then opts.at (the caller's position).
  // Returns {dim, x, y?, z} (no y = the surface there) or an error string.
  arenaOf(def, opts) {
    var a = def.arena
    var centre = null
    if (a && a.landmark) {
      var lms = (TtlData.landmarks && TtlData.landmarks.landmark) || []
      for (var i = 0; i < lms.length; i++) {
        if (lms[i].name === a.landmark) centre = { dim: TtlLife.OVERWORLD, x: lms[i].x, z: lms[i].z }
      }
      if (!centre) return `arena landmark ${a.landmark} is not in landmarks.toml`
    } else if (a && a.x !== undefined) {
      centre = { dim: a.dim || TtlLife.OVERWORLD, x: a.x, y: a.y, z: a.z }
    }
    if (opts.x !== undefined) {
      var want = { dim: opts.dim, x: Math.floor(opts.x), y: Math.floor(opts.y), z: Math.floor(opts.z) }
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

  // A boss with `requires` (ids of bosses that must have been beaten first) only answers a summoner who has the stage
  // ttl.defeated.<id> for each; opts.force (ops) skips it. Returns an error string or ''.
  gate(def, opts) {
    var req = def.requires || []
    if (req.length === 0 || opts.force) return ''
    var who = opts.summoner
    if (!who) return `${def.title} needs a summoner who has defeated ${req.join(', ')}`
    for (var i = 0; i < req.length; i++) {
      if (!who.stages.has(`ttl.defeated.${req[i]}`)) {
        var other = this.def(req[i])
        return `${def.title} only answers someone who has defeated ${other ? other.title : req[i]}`
      }
    }
    return ''
  },

  // Summons a boss. opts: {summoner: player} (checked against `requires`; quests and altars pass it), {x, y, z, dim} (explicit spot), {at: {dim, x, y, z}} (fallback spot), {force: true} (skip the
  // cooldown, ops only), {by: name} (who asked, for the log). Returns an error string, or null when the summon is
  // under way: the entity appears once its chunk is loaded (a second or two), and the log says "summoned".
  summon(server, id, opts) {
    opts = opts || {}
    var def = this.def(id)
    if (!def) return `unknown boss ${id} (one of ${this.defs().map(d => d.id).join(', ')})`
    var active = this.load(server)
    for (var k in active) {
      if (active[k].id === id) return `${def.title} is already out there`
    }
    if (this.pending[id]) return `${def.title} is already being summoned`
    if (!opts.force) {
      var left = this.cooldownLeft(server, def)
      if (left > 0) return `${def.title} cannot be summoned for another ${Math.ceil(left / 60000)} minutes`
    }
    var gate = this.gate(def, opts)
    if (gate) return gate
    var pos = this.arenaOf(def, opts)
    if (typeof pos === 'string') return pos
    if (TtlLife.isMortal(pos.dim)) return 'bosses do not exist in the Mortal Realm'
    if (!server.getLevel(pos.dim)) return `unknown dimension ${pos.dim}`
    var seq = Number(server.persistentData.getInt('ttl.boss.seq')) + 1
    server.persistentData.putInt('ttl.boss.seq', seq)
    var ctx = { id: id, key: `k${seq}`, dim: pos.dim, x: pos.x, y: pos.y, z: pos.z, by: opts.by || '', tries: 0, arena: pos.arena }
    this.pending[id] = true
    this.run(server, pos.dim, `forceload add ${pos.x} ${pos.z}`)
    console.info(`[ttl] boss: summoning ${id} at ${pos.dim} ${pos.x} ${pos.y === undefined ? 'surface' : pos.y} ${pos.z}${ctx.by ? ` (asked by ${ctx.by})` : ''}`)
    server.scheduleInTicks(20, () => this.attempt(server, ctx))
    return null
  },

  nbt(def, key) {
    var name = JSON.stringify({ text: def.title, color: this.COLORS[def.tier] || 'gold' })
    return `{NoAI:1b,PersistenceRequired:1b,CustomNameVisible:1b,CustomName:'${name}',Tags:["ttl.boss","ttl.bossid.${def.id}","ttl.boss.${key}"]}`
  },

  // One try at spawning: the chunk may still be loading after the forceload, so it retries for ~10 seconds.
  attempt(server, ctx) {
    try {
      var def = this.def(ctx.id)
      var nbt = this.nbt(def, ctx.key)
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
    delete this.pending[ctx.id]
    this.run(server, ctx.dim, `forceload remove ${ctx.x} ${ctx.z}`)
  },

  register(server, def, ctx, e) {
    var now = Date.now()
    var rec = {
      id: def.id, dim: ctx.dim, x: e.getX(), y: e.getY(), z: e.getZ(), started: now, state: 'idle',
      base: Math.round(e.getMaxHealth()), n: 0, phase: 0, hit: {}, near: {}, names: {}, seen: {}, last: [],
      gone: 0, idle: now, fx: ctx.x, fz: ctx.z, by: ctx.by
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
    delete this.pending[def.id]
    this.ensureBar(server, ctx.key, rec, def)
    var n = Math.max(1, near.length)
    console.info(`[ttl] boss: ${def.id} summoned (hp ×${mult}, ${n} player${n === 1 ? '' : 's'})`)
    var title = def.title
    this.players(server).forEach(p => p.tell(Text.gold(`${title} has been summoned.`)))
  },

  // Players of the list within the boss's range.
  near(players, rec, def) {
    var self = this
    return players.filter(p => !p.isSpectator() && self.distance(p, rec.dim, rec.x, rec.y, rec.z) <= def.range)
  },

  // Max health = vanilla x (hp_mult + per_player_mult x (n - 1)), n at least 1. Keeps the health fraction (a boss that
  // already took a hit keeps its wound when a second player arrives). Returns the multiplier.
  scale(server, rec, def, e, n) {
    n = Math.max(1, n)
    var mult = Math.round((def.hp_mult + def.per_player_mult * (n - 1)) * 100) / 100
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

  noteHit(e, attacker) {
    var key = this.keyOf(e)
    if (!key) return
    if (!this.hits[key]) this.hits[key] = {}
    this.hits[key][this.uid(attacker)] = String(attacker.username)
  },

  // ---- boss bar -----------------------------------------------------------------------------------------------

  barId(key) {
    return `ttl:boss_${key}`
  },

  ensureBar(server, key, rec, def) {
    if (this.bars[key]) return
    var id = this.barId(key)
    var text = JSON.stringify({ text: def.title, color: this.COLORS[def.tier] || 'gold' })
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
    if (this.hits[key]) {
      for (var u in this.hits[key]) {
        rec.hit[u] = true
        rec.names[u] = this.hits[key][u]
      }
      delete this.hits[key]
    }
    near.forEach(p => {
      var u = this.uid(p)
      rec.near[u] = (rec.near[u] || 0) + 1
      rec.names[u] = String(p.username)
    })
    if (rec.state === 'idle') {
      if (near.length > 0) {
        this.wake(server, key, rec, def, e, near)
      } else if (now - rec.idle > cfg.idleMs) {
        console.info(`[ttl] boss: ${def.id} removed, nobody came within ${cfg.idleMs / 60000} minutes`)
        this.cleanup(server, key, rec, true)
        return 'done'
      }
    } else {
      this.fight(server, key, rec, def, e, near, cfg)
    }
    // Baseline for kill credit: the objective values while the boss is still alive.
    players.forEach(p => { rec.seen[this.uid(p)] = this.score(server, p, def) })
    this.updateBar(server, key, rec, def, e)
    return 'keep'
  },

  wake(server, key, rec, def, e, near) {
    rec.state = 'fight'
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
    // Leave the chunk loaded a moment so the death loot and experience are placed.
    server.scheduleInTicks(100, () => this.run(server, rec.dim, `forceload remove ${rec.fx} ${rec.fz}`))
  },

  // The boss is dead (or gone). Winners: whoever the kill objective credits; whoever hit it, or stood in range for
  // presence_secs, and is within range now; and, when no player is credited with the kill, everybody in range at the
  // last poll. Nobody qualifying means the boss was lost without a fight: no reward, no cooldown.
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
    if (this.hits[key]) {
      for (var h in this.hits[key]) rec.hit[h] = true
    }
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
    server.persistentData.putString(`ttl.boss.last.${def.id}`, String(Date.now()))
    for (var w2 in winners) {
      try {
        this.reward(server, def, winners[w2])
      } catch (e) {
        console.error(`[ttl] boss: rewarding ${winners[w2].username} for ${def.id} failed: ${e}`)
      }
    }
    console.info(`[ttl] boss: ${def.id} defeated by ${names.join(', ')}${killers > 0 ? '' : ' (no kill credit: shared by everyone in the fight)'}`)
    this.announce(server, def, names)
  },

  // Stage, kill count, rep, coins and Skill Core for one winner. WP10 (bosses/rewards.js) may later replace the payout.
  reward(server, def, p) {
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
    Object.keys(rep).forEach(f => server.runCommandSilent(`ttl rep add ${name} ${f} ${rep[f]}`))
    var coins = r.coins || {}
    Object.keys(coins).forEach(c => server.runCommandSilent(`give ${name} tensura:${c}_coin ${coins[c]}`))
    if (r.core) this.giveCore(server, p, def)
    p.tell(Text.gold(`You defeated ${def.title}.`))
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

  announce(server, def, names) {
    var line = `${def.title} has fallen to ${names.join(', ')}.`
    this.players(server).forEach(p => p.tell(Text.gold(line)))
    try {
      if (typeof TtlDiscord === 'undefined') return
      var humans = names.filter(n => !TtlDiscord.isBot(n))
      if (humans.length === 0) return
      TtlDiscord.post(server, `${humans.map(n => TtlDiscord.name(n)).join(', ')} defeated **${def.title}**!`)
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
    return n
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlBoss.ensureObjectives(server)
  } catch (e) {
    console.error(`[ttl] boss: creating the kill objectives failed: ${e}`)
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
    if (attacker && attacker.isPlayer()) TtlBoss.noteHit(e, attacker)
  } catch (err) {
    console.error(`[ttl] boss: hit tracking failed: ${err}`)
  }
})

// Never natural: a boss entity that Minecraft spawns by itself is cancelled. Summons carry the ttl.boss tag and come
// from a command (spawn type "command"), so they pass. The first line per spawn shows the real spawn type string.
try {
  EntityEvents.checkSpawn(event => {
    var blocked = false
    try {
      if (!TtlBoss.conf().blockNatural) return
      var entity = event.entity
      var id = String(entity.type)
      var def = TtlBoss.byEntity(id)
      if (!def) return
      // Wild spawns of these stay (Shizu); a summoned instance is spawned by command and tagged afterwards.
      if (TtlBoss.conf().naturalAllow.indexOf(def.id) >= 0) return
      var type = String(event.type)
      blocked = TtlBoss.NATURAL.test(type)
      console.info(`[ttl] boss: ${id} spawn type=${type}: ${blocked ? 'blocked' : 'allowed'}`)
    } catch (err) {
      console.error(`[ttl] boss: spawn check failed: ${err}`)
    }
    // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
    if (blocked) event.cancel()
  })
} catch (e) {
  console.warn(`[ttl] boss: EntityEvents.checkSpawn is not available, natural boss spawns are not blocked (${e})`)
}
