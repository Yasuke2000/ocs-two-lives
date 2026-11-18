// priority: 75
// Organised combat arenas (owner 18/11/2026: the Walpurgis hall and Ramiris's Labyrinth, with loot). Knobs and the arenas
// themselves: design/data/arenas.toml (TtlData.arenas); lore and sources: design/lore/arenas.md; commands: arena/commands.js.
//
// An arena is a box: blueprint offsets of a placed build (`ttl.build.<name>.corner`, life/builds.js) or world coordinates in a
// dimension (Ramiris's Labyrinth = the round Colossus hall of Tensura's own dimension tensura:labyrinth). One match per arena:
//   lobby  /ttl arena join <arena> [duel|party|challenge] [a|b] puts a Life 2 soul on its side's spot (the place they came
//          from is kept in `ttl.arena.back`); /ttl arena start (the one who opened it) starts the countdown
//   count  fighters are put on their spots and healed; blows between them do nothing yet
//   fight  a fatal blow on a fighter is a defeat (cancelled, healed, sent back); leaving the box, logging out or
//          /ttl arena leave is out as well. Duel/party: the last side standing wins. Challenge: waves of mobs, then the boss
//          of bosses.toml through TtlBoss.summon (its cooldown, credit and rewards stay the boss framework's)
//   done   loot per rank (arenas.toml [arena.loot.<mode>.<rank>], loot cooldown per fighter), record, Discord line for a
//          notable result; after return_seconds everyone is sent back
// This file registers its beforeHurt before absorb/absorb.js (priority 75 > 70): a fatal blow between two fighters with an
// open skill pact is settled through TtlAbsorb.onKill here (absorb_duel arenas only), then turned into the arena defeat.
// Tensura's Labyrinth saves every creature that is not in #tensura:can_die_in_labyrinth from death (1 HP, sent to the
// overworld): a wave mob's fatal blow there removes it instead, so it is counted and never leaks out.
//
// Public: TtlArenas.inArena(level, pos) / TtlArenas.arenaAt(dim, x, y, z): damage inside an arena carries no liability.
// Server persistentData: `ttl.arena.state` JSON {arenaId: match}, `ttl.arena.last` JSON {arenaId: {mode, result, at}},
// `ttl.arena.cd.<arena>` (millis: no challenge before), `ttl.arena.test.<arena>` ("dim x y z": test placement),
// `ttl.arena.testmode` (min_seconds off). Player persistentData: `ttl.arena.back` ("dim x y z yaw pitch"), `ttl.arena.cd`
// JSON {"<arena>.<mode>": millis}, `ttl.arena.record` JSON {w, l, d, c, p, f, ds} (wins, losses, draws, challenge clear /
// partial / fail, duel wins in a row).
// Match: {id, mode, by, st, t, begin, until, end, a: [uuid], b: [uuid], names: {uuid: name}, out: {uuid: why}, left: {uuid:
// millis}, wave, phase (waves | boss), boss: {id, at}, rank: {uuid: rank}, result}.
const TtlArenas = {
  STATE: 'ttl.arena.state',
  LAST: 'ttl.arena.last',
  MOB: 'ttl.arena.mob',
  STRAY: 'ttl.arena.stray',
  LABYRINTH: 'tensura:labyrinth',
  mem: null,
  boxes: null,
  boxesAt: 0,
  labApi: undefined,

  // ---- data -------------------------------------------------------------------------------------------------

  rules() {
    return (TtlData.arenas && TtlData.arenas.rules) || {}
  },

  defs() {
    return (TtlData.arenas && TtlData.arenas.arena) || []
  },

  def(id) {
    var want = String(id).toLowerCase()
    var found = null
    this.defs().forEach(a => { if (a.id === want) found = a })
    return found
  },

  num(v, fallback) {
    var n = Number(v)
    return v === undefined || v === null || isNaN(n) ? fallback : n
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  byId(server, id) {
    var found = null
    server.getPlayerList().getPlayers().forEach(p => { if (TtlArenas.uid(p) === id) found = p })
    return found
  },

  isOp(player) {
    try {
      return player.hasPermissions(2)
    } catch (e) {
      return false
    }
  },

  // ---- geometry ---------------------------------------------------------------------------------------------

  buildDim(name) {
    var dim = TtlLife.OVERWORLD
    ;(TtlData.builds || []).forEach(b => { if (b.name === name && b.dimension) dim = String(b.dimension) })
    return dim
  },

  // The world placement of an arena: {dim, ox, oy, oz, test} or an error text. A test placement (`/ttl arena testat`) wins.
  origin(server, a) {
    var test = String(server.persistentData.getString(`ttl.arena.test.${a.id}`) || '')
    if (test) {
      var t = test.split(' ')
      return { dim: t[0], ox: Number(t[1]), oy: Number(t[2]), oz: Number(t[3]), test: true }
    }
    if (a.where.build) {
      var name = String(a.where.build)
      var data = server.persistentData
      var raw = data.getInt(`ttl.build.${name}.version`) >= 1 ? String(data.getString(`ttl.build.${name}.corner`) || '') : ''
      var c = raw.split(' ').map(Number)
      if (c.length !== 3 || c.some(n => isNaN(n))) return `${a.title} is not built yet (${name} has not been placed)`
      return { dim: this.buildDim(name), ox: c[0], oy: c[1], oz: c[2], test: false }
    }
    return { dim: String(a.where.dim), ox: 0, oy: 0, oz: 0, test: false }
  },

  // Box, round floor and a point converter in world coordinates, or an error text.
  geo(server, a) {
    var o = this.origin(server, a)
    if (typeof o === 'string') return o
    var f = a.box.from
    var t = a.box.to
    var g = {
      id: a.id, dim: o.dim, test: o.test,
      x0: o.ox + f[0], y0: o.oy + f[1], z0: o.oz + f[2], x1: o.ox + t[0], y1: o.oy + t[1], z1: o.oz + t[2],
      round: a.round ? { cx: o.ox + a.round.centre[0], cz: o.oz + a.round.centre[1], r: a.round.radius } : null,
      at: p => [o.ox + p[0], o.oy + p[1], o.oz + p[2]]
    }
    return g
  },

  // A point (entity position or block) inside the box: block columns x0..x1, z0..z1; feet from one below y0 up to y1.
  contains(g, x, y, z) {
    var bx = Math.floor(x)
    var by = Math.floor(y)
    var bz = Math.floor(z)
    if (bx < g.x0 || bx > g.x1 || bz < g.z0 || bz > g.z1 || by < g.y0 - 1 || by > g.y1) return false
    if (!g.round) return true
    var dx = x - (g.round.cx + 0.5)
    var dz = z - (g.round.cz + 0.5)
    return dx * dx + dz * dz <= (g.round.r + 0.5) * (g.round.r + 0.5)
  },

  refreshBoxes(server) {
    var out = []
    this.defs().forEach(a => {
      var g = TtlArenas.geo(server, a)
      if (typeof g !== 'string') out.push(g)
    })
    this.boxes = out
    this.boxesAt = Date.now()
    return out
  },

  // The arena id at a point of a dimension, or null. Uses the boxes of the last poll (refreshed every few seconds).
  arenaAt(dim, x, y, z) {
    var found = null
    ;(this.boxes || []).forEach(g => {
      if (!found && g.dim === String(dim) && TtlArenas.contains(g, Number(x) + 0.5, Number(y), Number(z) + 0.5)) found = g.id
    })
    return found
  },

  // Public (rules-pass, public-place duel liability): true when `pos` in `level` is inside an arena box. `level` = a level or
  // a dimension id; `pos` = a BlockPos, an entity, {x, y, z} or [x, y, z]. Never throws.
  inArena(level, pos) {
    try {
      if (!level || !pos) return false
      var dim = typeof level === 'string' ? level : String(level.dimension)
      if (typeof level !== 'string' && (!this.boxes || Date.now() - this.boxesAt > 5000)) {
        var server = level.server || (level.getServer ? level.getServer() : null)
        if (server) this.refreshBoxes(server)
      }
      var x = Array.isArray(pos) ? pos[0] : pos.x
      var y = Array.isArray(pos) ? pos[1] : pos.y
      var z = Array.isArray(pos) ? pos[2] : pos.z
      if (x === undefined && pos.getX) {
        x = pos.getX()
        y = pos.getY()
        z = pos.getZ()
      }
      return this.arenaAt(dim, Math.floor(Number(x)), Math.floor(Number(y)), Math.floor(Number(z))) !== null
    } catch (e) {
      console.warn(`[ttl] arena: inArena failed: ${e}`)
      return false
    }
  },

  playerIn(g, p) {
    return TtlLife.dimensionOf(p) === g.dim && this.contains(g, p.getX(), p.getY(), p.getZ())
  },

  // Volume selector arguments for the box (entities, not the round floor).
  sel(g) {
    return `x=${g.x0},y=${g.y0 - 1},z=${g.z0},dx=${g.x1 - g.x0},dy=${g.y1 - g.y0 + 1},dz=${g.z1 - g.z0}`
  },

  // ---- Tensura's Labyrinth ------------------------------------------------------------------------------------

  // The generated floor of a `ready` arena (Tensura builds its Labyrinth the first time the level loads). '' = ready.
  readiness(server, a, g) {
    if (g.test || !a.ready) return ''
    var level = server.getLevel(g.dim)
    if (!level) return `${a.title} is not open: the dimension ${g.dim} does not exist`
    var p = g.at(a.ready.at)
    try {
      var id = String(level.getBlock(p[0], p[1], p[2]).id)
      if (id === 'minecraft:air' || id === 'minecraft:void_air') return `${a.title} is still being shaped (the dimension has not been generated yet); try again later`
    } catch (e) {
      return `${a.title} could not be checked: ${e}`
    }
    return ''
  },

  // Tensura spawns its Elemental Colossus here for the first soul that walks in (MobSpawnType NATURAL), and keeps trying every
  // tick while that spawn does not come alive; bosses.toml block_natural cancels it (the Colossus is a [[boss]]). Marking the
  // first spawn done stops the retries; the Colossus fight is this arena's challenge boss instead (design/decisions.md).
  quietColossus(server, a, g) {
    if (!a.quiet_colossus || g.test || g.dim !== this.LABYRINTH) return
    try {
      if (this.labApi === undefined) {
        try {
          this.labApi = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
        } catch (e) {
          this.labApi = null
          console.warn(`[ttl] arena: Tensura storages not available, the Labyrinth Colossus is left alone (${e})`)
        }
      }
      if (!this.labApi) return
      var level = server.getLevel(g.dim)
      if (!level) return
      var lab = this.labApi.getLabyrinthFrom(level)
      if (lab && !lab.isColossusFirstSpawn()) {
        lab.setColossusFirstSpawned(true)
        lab.markDirty()
        console.info('[ttl] arena: the Labyrinth Colossus is marked as spawned (its fight is the labyrinth challenge boss)')
      }
    } catch (e) {
      console.warn(`[ttl] arena: could not quiet the Labyrinth Colossus: ${e}`)
    }
  },

  // A Colossus of Tensura's own (not a summoned boss) still standing in the hall.
  guarded(server, a, g) {
    if (g.test || g.dim !== this.LABYRINTH) return false
    return TtlCmd.run(server, `execute in ${g.dim} if entity @e[type=tensura:elemental_colossus,tag=!ttl.boss,${this.sel(g)}]`) > 0
  },

  // ---- state ------------------------------------------------------------------------------------------------

  load(server) {
    if (this.mem) return this.mem
    try {
      this.mem = JSON.parse(String(server.persistentData.getString(this.STATE)) || '{}')
    } catch (e) {
      this.mem = {}
    }
    return this.mem
  },

  save(server) {
    server.persistentData.putString(this.STATE, JSON.stringify(this.mem || {}))
  },

  live(server) {
    return Object.keys(this.load(server)).length > 0
  },

  fighters(m) {
    return m.a.concat(m.b)
  },

  sideOf(m, u) {
    return m.a.indexOf(u) >= 0 ? 'a' : m.b.indexOf(u) >= 0 ? 'b' : ''
  },

  standing(m, side) {
    return m[side].filter(u => !m.out[u])
  },

  // The match a player is in (lobby or not settled yet), or null.
  matchOf(server, u) {
    var state = this.load(server)
    for (var k in state) {
      var m = state[k]
      if (m.st !== 'done' && this.sideOf(m, u)) return m
    }
    return null
  },

  last(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.LAST)) || '{}')
    } catch (e) {
      return {}
    }
  },

  json(player, key) {
    try {
      return JSON.parse(String(player.persistentData.getString(key)) || '{}')
    } catch (e) {
      return {}
    }
  },

  // ---- moving people ------------------------------------------------------------------------------------------

  keepBack(p) {
    if (String(p.persistentData.getString('ttl.arena.back') || '')) return
    var line = [TtlLife.dimensionOf(p), Number(p.getX()).toFixed(2), Number(p.getY()).toFixed(2), Number(p.getZ()).toFixed(2), Number(p.getYRot()).toFixed(1), Number(p.getXRot()).toFixed(1)].join(' ')
    p.persistentData.putString('ttl.arena.back', line)
  },

  sendBack(server, p) {
    var raw = String(p.persistentData.getString('ttl.arena.back') || '')
    p.persistentData.remove('ttl.arena.back')
    if (!raw) return
    var b = raw.split(' ')
    TtlCmd.run(server, `execute in ${b[0]} run tp ${p.username} ${b[1]} ${b[2]} ${b[3]} ${b[4] || 0} ${b[5] || 0}`)
  },

  put(server, p, g, spot) {
    var w = g.at(spot)
    TtlCmd.run(server, `execute in ${g.dim} run tp ${p.username} ${w[0] + 0.5} ${w[1]} ${w[2] + 0.5}`)
  },

  heal(p) {
    try {
      p.setHealth(p.getMaxHealth())
      p.clearFire()
    } catch (e) {
      console.warn(`[ttl] arena: could not heal ${p.username}: ${e}`)
    }
  },

  // A coloured chat line (Text.gold and friends; unknown colours are gold).
  text(line, color) {
    var c = String(color || 'gold')
    if (c === 'red') return Text.red(line)
    if (c === 'green') return Text.green(line)
    if (c === 'yellow') return Text.yellow(line)
    if (c === 'gray') return Text.gray(line)
    return Text.gold(line)
  },

  tell(server, m, line, color) {
    this.fighters(m).forEach(u => {
      var p = TtlArenas.byId(server, u)
      if (p) p.tell(TtlArenas.text(line, color))
    })
  },

  // ---- lobby --------------------------------------------------------------------------------------------------

  // Each returns an error text for the player, or null.
  join(server, p, arenaId, wantMode, wantSide) {
    var a = this.def(arenaId)
    if (!a) return `Unknown arena ${arenaId} (${this.defs().map(d => d.id).join(', ')}).`
    var rules = this.rules()
    if (rules.life2_only !== false && TtlLife.phase(p) !== 'life2') return 'Only souls in their second life fight in the arenas.'
    var u = this.uid(p)
    if (this.matchOf(server, u)) return 'You are in a match already (/ttl arena leave).'
    var g = this.geo(server, a)
    if (typeof g === 'string') return g
    var notReady = this.readiness(server, a, g)
    if (notReady) return notReady
    this.quietColossus(server, a, g)
    if (this.guarded(server, a, g)) return `The Elemental Colossus still guards ${a.title}. It must fall before the hall can be used.`
    var state = this.load(server)
    var m = state[a.id]
    if (m && m.st !== 'lobby') return `A match is on in ${a.title}; wait for it to end (/ttl arena list).`
    var mode = String(wantMode || (m ? m.mode : 'duel')).toLowerCase()
    if (a.modes.indexOf(mode) < 0) return `${a.title} offers ${a.modes.join(', ')}.`
    if (m && mode !== m.mode) return `The lobby in ${a.title} is for a ${m.mode}.`
    if (!m && mode === 'challenge') {
      var left = this.num(String(server.persistentData.getString(`ttl.arena.cd.${a.id}`) || '0'), 0) - Date.now()
      if (left > 0) return `${a.title} takes no new challenge for another ${Math.ceil(left / 60000)} minutes.`
    }
    var now = Date.now()
    if (!m) m = { id: a.id, mode: mode, by: u, st: 'lobby', t: now, a: [], b: [], names: {}, out: {}, left: {}, rank: {}, wave: 0, phase: '' }
    var side = this.pickSide(server, m, p, wantSide)
    if (side.indexOf(' ') >= 0) return side
    m[side].push(u)
    m.names[u] = String(p.username)
    state[a.id] = m
    this.save(server)
    this.keepBack(p)
    this.put(server, p, g, side === 'a' ? a.spawn_a : a.spawn_b)
    this.tell(server, m, `${p.username} joins the ${mode} in ${a.title} (side ${side}). ${m.names[m.by]} starts it with /ttl arena start.`)
    console.info(`[ttl] arena: ${p.username} joined ${a.id} ${mode} side ${side}`)
    return null
  },

  // 'a' or 'b', or an error text (it has a space).
  pickSide(server, m, p, want) {
    var max = this.num(this.rules().max_side, 5)
    if (m.mode === 'duel') {
      if (m.a.length === 0) return 'a'
      if (m.b.length === 0) return 'b'
      return 'This duel has its two fighters already.'
    }
    if (m.mode === 'challenge') return m.a.length < max ? 'a' : `A challenge takes at most ${max} fighters.`
    var side = want ? String(want).toLowerCase() : ''
    if (side && side !== 'a' && side !== 'b') return 'The sides are a and b.'
    if (!side) {
      side = m.a.length === 0 ? 'a' : 'b'
      // Party members of the one who opened the lobby fight on side a.
      try {
        var mine = typeof TtlBoss !== 'undefined' ? TtlBoss.partyOf(server, p) : null
        if (mine && mine.members.indexOf(m.by) >= 0) side = 'a'
      } catch (e) {
        console.warn(`[ttl] arena: party lookup failed: ${e}`)
      }
    }
    return m[side].length < max ? side : `Side ${side} is full (${max}).`
  },

  leave(server, p) {
    var u = this.uid(p)
    var m = this.matchOf(server, u)
    if (!m) {
      if (String(p.persistentData.getString('ttl.arena.back') || '')) {
        this.sendBack(server, p)
        return null
      }
      return 'You are not in an arena match.'
    }
    if (m.st === 'lobby') {
      this.drop(server, m, u)
      this.sendBack(server, p)
      return null
    }
    this.out(server, m, u, 'left')
    this.save(server)
    return null
  },

  // Takes a fighter out of a lobby; an empty lobby closes, a lobby whose opener left passes to the next fighter.
  drop(server, m, u) {
    m.a = m.a.filter(x => x !== u)
    m.b = m.b.filter(x => x !== u)
    var state = this.load(server)
    if (m.a.length + m.b.length === 0) {
      delete state[m.id]
    } else if (m.by === u) {
      m.by = m.a.length ? m.a[0] : m.b[0]
    }
    this.save(server)
  },

  start(server, m, starter) {
    var a = this.def(m.id)
    if (m.st !== 'lobby') return 'This match has started already.'
    if (starter && this.uid(starter) !== m.by && !this.isOp(starter)) return `Only ${m.names[m.by]}, who opened the lobby, can start it.`
    var rules = this.rules()
    var minSide = this.num(rules.party_min_side, 2)
    if (m.mode === 'duel' && (m.a.length !== 1 || m.b.length !== 1)) return 'A duel needs two fighters.'
    if (m.mode === 'party' && (m.a.length < minSide || m.b.length < minSide)) return `A party battle needs at least ${minSide} fighters on each side.`
    if (m.mode === 'challenge' && m.a.length < 1) return 'A challenge needs a fighter.'
    var g = this.geo(server, a)
    if (typeof g === 'string') return g
    var now = Date.now()
    m.st = 'count'
    m.begin = now + this.num(rules.countdown_seconds, 5) * 1000
    m.until = m.begin + this.num(a.minutes[m.mode], 10) * 60000
    var self = this
    this.fighters(m).forEach(u => {
      var p = self.byId(server, u)
      if (!p) return
      self.put(server, p, g, self.sideOf(m, u) === 'a' ? a.spawn_a : a.spawn_b)
      self.heal(p)
    })
    this.save(server)
    this.tell(server, m, `The ${m.mode} in ${a.title} begins in ${this.num(rules.countdown_seconds, 5)} seconds.`, 'yellow')
    console.info(`[ttl] arena: ${a.id} ${m.mode} started (${m.a.map(u => m.names[u]).join(',')} vs ${m.b.map(u => m.names[u]).join(',') || 'the arena'})`)
    return null
  },

  // ---- the fight ----------------------------------------------------------------------------------------------

  // A fighter is out: the reason is kept, they go back where they came from (a tick later: never inside a damage event).
  out(server, m, u, why) {
    if (m.out[u]) return
    m.out[u] = why
    delete m.left[u]
    var p = this.byId(server, u)
    var a = this.def(m.id)
    console.info(`[ttl] arena: ${m.names[u]} is out of ${m.id} (${why})`)
    if (!p || why === 'fell') return
    p.tell(TtlArenas.text(why === 'defeated' ? `You are defeated in ${a.title}.` : `You are out of the ${m.mode} in ${a.title}.`, 'red'))
    var self = this
    server.scheduleInTicks(1, () => {
      try {
        self.heal(p)
        self.sendBack(server, p)
      } catch (e) {
        console.error(`[ttl] arena: sending ${m.names[u]} back failed: ${e}`)
      }
    })
  },

  // A blow on a player (EntityEvents.beforeHurt). True = cancel it.
  onPlayerHurt(server, victim, attacker, damage) {
    var u = this.uid(victim)
    var m = this.matchOf(server, u)
    if (!m) return false
    var foe = attacker && attacker.isPlayer() ? this.uid(attacker) : ''
    var foeSide = foe ? this.sideOf(m, foe) : ''
    if (m.st !== 'fight') return !!foeSide
    if (m.out[u]) return false
    if (foeSide && foeSide === this.sideOf(m, u) && !this.rules().friendly_fire) return true
    if (!(damage >= Number(victim.getHealth()))) return false
    this.defeat(server, m, victim, foeSide && !m.out[foe] ? attacker : null)
    return true
  },

  // A fatal blow in a running match. An open skill pact between the two is settled first (absorb_duel arenas only).
  defeat(server, m, victim, attacker) {
    var a = this.def(m.id)
    if (attacker && a.absorb_duel && typeof TtlAbsorb !== 'undefined') {
      try {
        var d = TtlAbsorb.decide(server, attacker, victim, null)
        if (d && d.pact) {
          var res = TtlAbsorb.onKill(server, attacker, victim, null, null)
          console.info(`[ttl] arena: ${attacker.username} beat ${victim.username} under a ${d.route} pact in ${m.id}: ${res.ok ? 'settled' : res.why}`)
        }
      } catch (e) {
        console.error(`[ttl] arena: settling the skill pact failed: ${e}`)
      }
    }
    if (attacker) attacker.tell(TtlArenas.text(`You defeat ${victim.username}.`, 'green'))
    this.out(server, m, this.uid(victim), 'defeated')
    this.save(server)
  },

  // A blow on a wave mob. In the Labyrinth Tensura would save it from death and send it to the overworld: its fatal blow
  // removes it instead. True = cancel.
  onMobHurt(server, e, damage) {
    if (!(damage >= Number(e.getHealth()))) return false
    if (String(e.level.dimension) !== this.LABYRINTH) return false
    server.scheduleInTicks(1, () => {
      try {
        e.discard()
      } catch (err) {
        console.warn(`[ttl] arena: removing a wave mob failed: ${err}`)
      }
    })
    return true
  },

  mobTag(m) {
    return `${this.MOB}.${m.id}`
  },

  mobsAlive(server, m) {
    return TtlCmd.run(server, `execute if entity @e[tag=${this.mobTag(m)}]`)
  },

  // Wave mobs that wandered out of the box are put back in the middle of it.
  herd(server, m, a, g) {
    var tag = this.mobTag(m)
    var c = g.at(a.mob_spots[0])
    TtlCmd.run(server, `tag @e[tag=${tag}] add ${this.STRAY}`)
    TtlCmd.run(server, `execute in ${g.dim} run tag @e[tag=${tag},${this.sel(g)}] remove ${this.STRAY}`)
    TtlCmd.run(server, `execute in ${g.dim} run tp @e[tag=${this.STRAY}] ${c[0] + 0.5} ${c[1]} ${c[2] + 0.5}`)
    TtlCmd.run(server, `tag @e[tag=${this.STRAY}] remove ${this.STRAY}`)
  },

  clearMobs(server, m) {
    TtlCmd.run(server, `kill @e[tag=${this.mobTag(m)}]`)
  },

  spawnWave(server, m, a, g, n) {
    var ch = a.challenge
    var wave = ch.waves[n - 1]
    var k = Math.max(1, m.a.length)
    var mult = 1 + this.num(ch.per_player, 0) * (k - 1)
    var cap = this.num(ch.max_mobs, 16)
    var spots = a.mob_spots
    var made = 0
    var nbt = `{PersistenceRequired:1b,DeathLootTable:"minecraft:empty",Tags:["${this.MOB}","${this.mobTag(m)}"]}`
    wave.mobs.forEach(mob => {
      var count = Math.max(1, Math.round(mob.count * mult))
      for (var i = 0; i < count && made < cap; i++) {
        var s = g.at(spots[made % spots.length])
        var dx = (made % 3) - 1
        var dz = (Math.floor(made / 3) % 3) - 1
        TtlCmd.run(server, `execute in ${g.dim} run summon ${mob.entity} ${s[0] + 0.5 + dx} ${s[1]} ${s[2] + 0.5 + dz} ${nbt}`)
        made++
      }
    })
    m.wave = n
    m.phase = 'waves'
    this.tell(server, m, `Wave ${n} of ${ch.waves.length}: ${made} foes.`, 'yellow')
    console.info(`[ttl] arena: ${a.id} wave ${n}/${ch.waves.length} (${made} mobs)`)
  },

  // The challenge boss through the boss framework (its cooldown, scaling, credit and rewards). Returns an error or null.
  summonBoss(server, m, a, g) {
    var id = String(a.challenge.boss || '')
    if (!id) return 'no boss'
    if (typeof TtlBoss === 'undefined') return 'the boss framework is not loaded'
    var s = g.at(a.mob_spots[0])
    var summoner = this.byId(server, m.by)
    if (!summoner) this.standing(m, 'a').forEach(u => { if (!summoner) summoner = TtlArenas.byId(server, u) })
    var err = TtlBoss.summon(server, id, { x: s[0], y: s[1], z: s[2], dim: g.dim, by: `arena:${a.id}`, summoner: summoner })
    if (err) return err
    m.phase = 'boss'
    m.boss = { id: id, at: Date.now() }
    var def = TtlBoss.def(id)
    this.tell(server, m, `The last foe comes: ${def ? def.title : id}.`, 'red')
    return null
  },

  // 'clear' when our boss fell, 'gone' when it vanished without a defeat, '' while it is out there.
  bossState(server, m) {
    var id = m.boss.id
    if (TtlBoss.lastDefeat(server, id) >= m.boss.at) return 'clear'
    if (TtlBoss.pending[id]) return ''
    var active = TtlBoss.load(server)
    for (var k in active) {
      if (active[k].id === id) return ''
    }
    return Date.now() - m.boss.at > 15000 ? 'gone' : ''
  },

  // Our boss is removed when the challenge ends without it (only an instance this arena summoned).
  dropBoss(server, m) {
    if (!m.boss || typeof TtlBoss === 'undefined') return
    try {
      var active = TtlBoss.load(server)
      for (var k in active) {
        if (active[k].id === m.boss.id && active[k].by === `arena:${m.id}`) {
          TtlBoss.abort(server, m.boss.id)
          return
        }
      }
    } catch (e) {
      console.warn(`[ttl] arena: removing the challenge boss failed: ${e}`)
    }
  },

  // A challenge rank from how far it got.
  challengeRank(m, a) {
    var total = a.challenge.waves.length
    var cleared = m.phase === 'boss' ? total : Math.max(0, m.wave - 1)
    return cleared >= Math.ceil(total / 2) ? 'partial' : 'fail'
  },

  poll(server) {
    var state = this.load(server)
    var keys = Object.keys(state)
    if (keys.length === 0) return
    var now = Date.now()
    var dirty = false
    var self = this
    keys.forEach(k => {
      var m = state[k]
      try {
        if (self.step(server, m, now)) dirty = true
      } catch (e) {
        console.error(`[ttl] arena: ${k} failed, the match is called off: ${e}`)
        self.close(server, m)
        dirty = true
      }
    })
    if (dirty) this.save(server)
  },

  // One look at one match. True when it changed.
  step(server, m, now) {
    var a = this.def(m.id)
    var rules = this.rules()
    if (!a) {
      this.close(server, m)
      return true
    }
    if (m.st === 'lobby') {
      var gone = this.fighters(m).filter(u => !this.byId(server, u))
      gone.forEach(u => this.drop(server, m, u))
      if (this.fighters(m).length > 0 && now - m.t > this.num(rules.lobby_minutes, 5) * 60000) {
        this.tell(server, m, `Nobody started the ${m.mode} in ${a.title}; the lobby closes.`, 'red')
        this.close(server, m)
        return true
      }
      return gone.length > 0
    }
    if (m.st === 'done') {
      if (now < m.end) return false
      this.close(server, m)
      return true
    }
    var g = this.geo(server, a)
    if (typeof g === 'string') {
      this.close(server, m)
      return true
    }
    if (m.st === 'count') {
      if (now < m.begin) return false
      m.st = 'fight'
      this.tell(server, m, 'Fight!', 'red')
      if (m.mode === 'challenge') this.spawnWave(server, m, a, g, 1)
      return true
    }
    // fight: who is still standing in the box
    var grace = this.num(rules.leave_grace_seconds, 3) * 1000
    var self = this
    this.fighters(m).forEach(u => {
      if (m.out[u]) return
      var p = self.byId(server, u)
      if (!p) {
        self.out(server, m, u, 'logged out')
        return
      }
      if (self.playerIn(g, p)) {
        delete m.left[u]
        return
      }
      if (!m.left[u]) m.left[u] = now
      if (now - m.left[u] > grace) self.out(server, m, u, 'left the arena')
    })
    if (m.mode === 'challenge') {
      if (this.standing(m, 'a').length === 0) return this.settle(server, m, a, g, { rank: this.challengeRank(m, a) })
      if (now > m.until) return this.settle(server, m, a, g, { rank: this.challengeRank(m, a) })
      this.herd(server, m, a, g)
      if (m.phase === 'boss') {
        var b = this.bossState(server, m)
        if (b === 'clear') return this.settle(server, m, a, g, { rank: 'clear' })
        if (b === 'gone') return this.settle(server, m, a, g, { rank: 'partial' })
        return true
      }
      if (this.mobsAlive(server, m) > 0) return true
      if (m.wave < a.challenge.waves.length) {
        this.spawnWave(server, m, a, g, m.wave + 1)
        return true
      }
      if (!a.challenge.boss) return this.settle(server, m, a, g, { rank: 'clear' })
      var err = this.summonBoss(server, m, a, g)
      if (err) {
        this.tell(server, m, `The last foe does not come (${err}).`, 'red')
        return this.settle(server, m, a, g, { rank: 'partial' })
      }
      return true
    }
    var sa = this.standing(m, 'a').length
    var sb = this.standing(m, 'b').length
    if (sa === 0 && sb === 0) return this.settle(server, m, a, g, { side: '' })
    if (sb === 0) return this.settle(server, m, a, g, { side: 'a' })
    if (sa === 0) return this.settle(server, m, a, g, { side: 'b' })
    if (now > m.until) return this.settle(server, m, a, g, { side: '' })
    return true
  },

  // Ends a match without loot: everyone back, mobs and our boss removed.
  close(server, m) {
    var self = this
    this.clearMobs(server, m)
    this.dropBoss(server, m)
    this.fighters(m).forEach(u => {
      var p = self.byId(server, u)
      if (p) self.sendBack(server, p)
    })
    delete this.load(server)[m.id]
    console.info(`[ttl] arena: ${m.id} closed`)
  },

  // ---- result -------------------------------------------------------------------------------------------------

  // res = {side: 'a'|'b'|''} (duel, party; '' = draw) or {rank} (challenge). Always returns true (state changed).
  settle(server, m, a, g, res) {
    var now = Date.now()
    var rules = this.rules()
    var self = this
    this.clearMobs(server, m)
    if (m.mode === 'challenge' && res.rank !== 'clear') this.dropBoss(server, m)
    var result = m.mode === 'challenge' ? res.rank : (res.side || 'draw')
    this.fighters(m).forEach(u => {
      var side = self.sideOf(m, u)
      m.rank[u] = m.mode === 'challenge' ? res.rank : (!res.side ? 'draw' : side === res.side ? 'win' : 'lose')
    })
    var short = m.mode !== 'challenge' && now - m.begin < this.num(rules.min_seconds, 30) * 1000 &&
      !server.persistentData.getBoolean('ttl.arena.testmode')
    this.fighters(m).forEach(u => {
      var p = self.byId(server, u)
      if (!p) return
      self.note(p, m)
      if (short) {
        p.tell(TtlArenas.text(`The ${m.mode} was over too quickly to earn anything.`, 'gray'))
        return
      }
      self.reward(server, p, a, m.mode, m.rank[u])
    })
    if (m.mode === 'challenge') {
      server.persistentData.putString(`ttl.arena.cd.${a.id}`, String(now + this.num(a.challenge_cooldown_minutes, 30) * 60000))
    }
    var last = this.last(server)
    last[a.id] = { mode: m.mode, result: result, at: now }
    server.persistentData.putString(this.LAST, JSON.stringify(last))
    this.tell(server, m, this.summary(m, a, result), 'gold')
    console.info(`[ttl] arena: ${a.id} ${m.mode} settled: ${result}`)
    if (!short) this.story(server, m, a, result)
    m.st = 'done'
    m.result = result
    m.end = now + this.num(rules.return_seconds, 5) * 1000
    return true
  },

  summary(m, a, result) {
    var names = side => m[side].map(u => m.names[u]).join(', ')
    if (m.mode === 'challenge') return `The challenge of ${a.title} ends: ${result}.`
    if (result === 'draw') return `The ${m.mode} in ${a.title} ends in a draw.`
    return `${names(result)} win${m[result].length === 1 ? 's' : ''} the ${m.mode} in ${a.title}.`
  },

  // Record: wins, losses, draws, challenge ranks, duel wins in a row.
  note(p, m) {
    var r = this.json(p, 'ttl.arena.record')
    var rank = m.rank[this.uid(p)]
    var key = { win: 'w', lose: 'l', draw: 'd', clear: 'c', partial: 'p', fail: 'f' }[rank]
    r[key] = (r[key] || 0) + 1
    if (m.mode === 'duel') r.ds = rank === 'win' ? (r.ds || 0) + 1 : 0
    p.persistentData.putString('ttl.arena.record', JSON.stringify(r))
  },

  cooldownLeft(p, arenaId, mode) {
    var cd = this.json(p, 'ttl.arena.cd')
    return Math.max(0, this.num(cd[`${arenaId}.${mode}`], 0) - Date.now())
  },

  // The loot of a rank, unless the fighter is on this arena's loot cooldown for the mode.
  reward(server, p, a, mode, rank) {
    var r = ((a.loot || {})[mode] || {})[rank]
    if (!r) return
    var left = this.cooldownLeft(p, a.id, mode)
    if (left > 0) {
      p.tell(TtlArenas.text(`${a.title} gives you no ${mode} loot for another ${Math.ceil(left / 60000)} minutes.`, 'gray'))
      return
    }
    var name = String(p.username)
    var coins = r.coins || {}
    Object.keys(coins).forEach(c => server.runCommandSilent(`give ${name} tensura:${c}_coin ${coins[c]}`))
    ;(r.items || []).forEach(it => server.runCommandSilent(`give ${name} ${it.item} ${it.count}`))
    if (r.table) {
      for (var i = 0; i < this.num(r.rolls, 1); i++) server.runCommandSilent(`loot give ${name} loot ${r.table}`)
    }
    if (r.xp) server.runCommandSilent(`xp add ${name} ${r.xp} levels`)
    var cd = this.json(p, 'ttl.arena.cd')
    cd[`${a.id}.${mode}`] = Date.now() + this.num(a.cooldown_minutes[mode], 60) * 60000
    p.persistentData.putString('ttl.arena.cd', JSON.stringify(cd))
    p.tell(TtlArenas.text(`Your ${rank === 'win' || rank === 'clear' ? 'prize' : 'share'} from ${a.title} is in your pack.`, 'gold'))
  },

  // Discord (#story via sdlink; dropped while muted or a test bot is online): a duel streak, a big party win, a challenge rank.
  story(server, m, a, result) {
    if (typeof TtlDiscord === 'undefined') return
    try {
      var s = this.rules().story || {}
      var humans = side => m[side].filter(u => !TtlDiscord.isBot(m.names[u])).map(u => TtlDiscord.name(m.names[u]))
      var line = ''
      if (m.mode === 'duel' && (result === 'a' || result === 'b')) {
        var w = m[result][0]
        var p = this.byId(server, w)
        var streak = p ? this.num(this.json(p, 'ttl.arena.record').ds, 0) : 0
        var loser = result === 'a' ? 'b' : 'a'
        if (streak >= this.num(s.duel_streak, 3) && !TtlDiscord.isBot(m.names[w])) {
          line = `${TtlDiscord.name(m.names[w])} won ${streak} duels in a row in ${a.title}, the last against ${TtlDiscord.name(m.names[m[loser][0]])}.`
        }
      } else if (m.mode === 'party' && (result === 'a' || result === 'b')) {
        var other = result === 'a' ? 'b' : 'a'
        if (m[result].length >= this.num(s.party_side, 3) && humans(result).length > 0) {
          line = `${humans(result).join(', ')} won a party battle in ${a.title} against ${m[other].map(u => TtlDiscord.name(m.names[u])).join(', ')}.`
        }
      } else if (m.mode === 'challenge' && result === (s.challenge || 'clear') && humans('a').length > 0) {
        var boss = a.challenge.boss && typeof TtlBoss !== 'undefined' ? TtlBoss.def(a.challenge.boss) : null
        line = `${humans('a').join(', ')} cleared the challenge of ${a.title}${boss && result === 'clear' ? ` and felled ${boss.title}` : ''}.`
      }
      if (line) TtlDiscord.post(server, line)
    } catch (e) {
      console.warn(`[ttl] arena: Discord line failed: ${e}`)
    }
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  TtlArenas.mem = null
  var loop = () => server.scheduleInTicks(TtlArenas.num(TtlArenas.rules().poll_ticks, 20), () => {
    try {
      TtlArenas.refreshBoxes(server)
      TtlArenas.poll(server)
    } catch (e) {
      console.error(`[ttl] arena: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})

// A fatal blow on a fighter is a defeat; blows between fighters before the start or on the same side do nothing; a wave mob's
// fatal blow in the Labyrinth removes it. Registered before absorb.js (priority 75): see the header.
EntityEvents.beforeHurt(event => {
  var cancel = false
  try {
    var e = event.entity
    var server = e.server
    if (server && TtlArenas.live(server)) {
      if (e.isPlayer()) {
        cancel = TtlArenas.onPlayerHurt(server, e, event.source.actual, Number(event.damage))
      } else if (e.getTags().contains(TtlArenas.MOB)) {
        cancel = TtlArenas.onMobHurt(server, e, Number(event.damage))
      }
    }
  } catch (err) {
    console.error(`[ttl] arena: hit check failed: ${err}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
  if (cancel) event.cancel()
})

// A fighter who dies anyway (the void, /kill) is out; they respawn where Minecraft puts them, not at the arena's return spot.
EntityEvents.death('minecraft:player', event => {
  try {
    var p = event.entity
    var server = event.server
    if (!TtlArenas.live(server)) return
    var u = TtlArenas.uid(p)
    var m = TtlArenas.matchOf(server, u)
    if (!m || m.st === 'lobby') return
    p.persistentData.remove('ttl.arena.back')
    TtlArenas.out(server, m, u, 'fell')
    TtlArenas.save(server)
  } catch (e) {
    console.error(`[ttl] arena: death check failed: ${e}`)
  }
})

// Back from a match that ended (or was called off) while the soul was offline.
PlayerEvents.loggedIn(event => {
  try {
    var p = event.player
    var server = event.server
    if (!String(p.persistentData.getString('ttl.arena.back') || '')) return
    server.scheduleInTicks(40, () => {
      try {
        var m = TtlArenas.matchOf(server, TtlArenas.uid(p))
        if (m && m.st !== 'lobby' && !m.out[TtlArenas.uid(p)]) return
        TtlArenas.sendBack(server, p)
        p.tell(TtlArenas.text('The arena match ended while you were away; you are back where you joined from.', 'gray'))
      } catch (err) {
        console.error(`[ttl] arena: return at login failed: ${err}`)
      }
    })
  } catch (e) {
    console.error(`[ttl] arena: login hook failed: ${e}`)
  }
})
