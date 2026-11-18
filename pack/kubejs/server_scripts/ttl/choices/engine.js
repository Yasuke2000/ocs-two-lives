// priority: 68
// Moral-choice world events, "Crossroads of conscience" (design/architecture/paths-necro-artificer.md §4, rules R11-R14,
// owner decisions O-C1/O-C2 of 18/11/2026; WP-C1). Data: design/data/choices.toml → TtlData.choices. The scenes themselves:
// choices/events_c1.js (4.1-4.4; WP-C2 adds 4.5-4.12 in its own file). Commands: choices/commands.js (/ttl choice).
//
// A SCENE is a small, temporary situation near a Life 2 soul on the canon continent: tagged entities (vanilla villagers,
// Tensura mobs) and a few scene blocks (#ttl:scene) round a centre. Each has a slow good/grey route and a faster dark
// shortcut. A route is either a MENU route (a clickable button: /ttl choice take <sid> <route>) or a DEED the scene's poll
// detects (healing, killing, feeding, naming). Every route is paid through TtlRoads.pay as the choice `choice.<event>`, so the
// dark one costs the five R13 costs. Rules:
//   R11  natural scenes only on the canon continent (TtlWorld.onContinent), in the Overworld; never in the Mortal Realm.
//        Never inside a protected domain (TtlDomains.of, guarded), a canon build or a safe zone (TtlWild.protectedSpot).
//   O-C1 at most [engine] max_active open scenes, one per canon region; a scene nobody resolves in ttl_minutes ends the
//        NEUTRAL way (the event's `neutral` hook + line) and the chronicle counts it unresolved. First come per scene: the
//        first route that completes resolves it. Every Life 2 soul within credit_radius at that moment who TOOK PART (hit,
//        healed, fed, freed, took the route) is credited: it pays the route's costs and gets its reward; the others within
//        the radius only hear what happened (R14 renown is TtlRoads' witness rule round the scene's centre).
//   O-C2 a dark route notes dark_deed (world.toml weight -1.5); a soul's dark routes move the balance at most
//        [balance] dark_cap points a day (fewer notes, never fewer karma/reputation/renown).
//   R12  nothing here reads or writes a story, Oath path or boss stage.
// Spawn odds: every [engine] roll_minutes, chance x (1 + per_player x (Life 2 souls online - 1)), capped; the event is
// drawn by weight x weight_if (the chronicle's tide, reached world milestones). Counts and coin rewards scale the same way.
// Timing: a poll of the event director (events/director.js `choice_scenes`, never scheduled), or our own loop without it.
//
// Storage
//   server  ttl.choices.active   JSON {sid: scene} (open scenes and resolved ones until their linger ends)
//                                scene = {sid, id, dim, x, y, z, region {key, name}, started, ends, online, mult, n {role: count},
//                                by, home, state (open|good|grey|dark|neutral), route, actor, at, clearAt, part {name: how},
//                                hits {role: name}, prog {...}, blocks [[x, y, z, prevId]], heard {name: 1}, paid [], saw []}
//           ttl.choices.done     JSON ring (20) of finished scenes (for /ttl choice expect after the cleanup)
//           ttl.choices.sweep    JSON [[dim, x, y, z, prevId]] blocks of removed scenes whose chunk was not loaded
//           ttl.choices.seq      int, the last scene number (sid = "s<n>")
//           ttl.choices.state    JSON {roll, spawn, last} last natural roll, last natural spawn, last sid
//           ttl.choices.testonline  int test hook: Life 2 souls online for the scale (0 = count them)
//   player  ttl.choices          JSON {done: {event: {good, grey, dark, last}}, tide: {day, dark}, last: {sid, event, route, road, at}}
//           ttl.choices.testskills  "a,b" test hook: skills/`necro` the soul counts as having
//   entity tags  ttl.scene, ttl.scene.<sid>, ttl.role.<role> (+ whatever the scene adds: ttl.horde, ttl.wants_name)
//
// PUBLIC API (other packages and WP-C2's scenes; `player` is a ServerPlayer)
//   TtlChoices.register(def)                 a scene type: def = {
//       id,                                  the [[choice]] id in choices.toml
//       spawn(server, scene, ctx),           place entities/blocks with ctx.summon / ctx.place; return false to refuse
//       poll(server, scene, ctx),            every engine poll while the scene is open AND loaded: detect deeds, ctx.resolve
//       interact(server, scene, player, entity, item, ctx)   right-click on a scene entity (main hand); true = handled
//       useBlock(server, scene, player, block, item, ctx)    right-click on a scene block; true = handled
//       hurt(server, scene, player, entity, role, ctx)       a player hurt a scene entity (after the engine noted the hit)
//       routes: {<routeId>: {need(server, scene, player, ctx) → '' | reason, take(server, scene, player, ctx) → '' | reason}}
//                                            extra checks and the effect of MENU routes (the engine checks `need` of the
//                                            TOML, charges coins:<n>, then calls take; '' = resolve now)
//       resolved(server, scene, routeId, actor, ctx)   the visible outcome after the costs (cure, free, despawn, ...)
//       neutral(server, scene, ctx)          nobody acted in time
//       test(server, scene, player, verb, arg, ctx) → '' | reason   test hooks for bots (/ttl choice test <p> <verb> <sid>)
//     }
//   TtlChoices.pollOne(server, sid) · test(server, player, sid, verb, arg) · roll(server, forced, onlyFor) · clearAll(server)
//   TtlChoices.spawn(server, eventId, opts) {ok, error, sid}; opts = {x, y, z, dim, by, ops (skip the spot rules), near}
//   TtlChoices.resolve(server, sid, routeId, actorName) {ok, error, paid, saw} · neutral(server, sid, why)
//   TtlChoices.take(server, player, sid, routeId) '' or the reason · check(...) {why, ...} (no side effects) · menu(server, player, scene)
//   (every sid argument also takes 'last', the newest scene)
//   TtlChoices.scenes(server) {sid: scene} · scene(server, sid) · open(server) [scenes] · near(server, player, radius)
//   TtlChoices.has(player, need) true/false · hasSkill(player, id) · isNecro(player)
//   TtlChoices.ctx(server, scene): row, knob(k, d), count(role), level(), at(dx, dz), summon(role, type, dx, dz, nbt, name),
//     place(dx, dy, dz, block), entities(role), alive(role), loaded(), part(player, how), resolve(routeId, actorName),
//     players(radius), nearest(x, y, z, radius), say(text, radius), give(player, item, n), cmd(command), sel(role), one(role)
const TtlChoices = {
  ACTIVE: 'ttl.choices.active',
  DONE: 'ttl.choices.done',
  SWEEP: 'ttl.choices.sweep',
  SEQ: 'ttl.choices.seq',
  STATE: 'ttl.choices.state',
  TESTONLINE: 'ttl.choices.testonline',
  P_KEY: 'ttl.choices',
  P_SKILLS: 'ttl.choices.testskills',
  OVERWORLD: 'minecraft:overworld',
  DAY_MS: 86400000,
  SID: /^ttl\.scene\.(s\d+)$/,
  defs: {},
  cache: null,
  aabb: undefined,
  hm: undefined,
  skillApi: undefined,
  storages: undefined,
  director: false,

  // ---- configuration -------------------------------------------------------------------------------------------

  conf() {
    return (typeof TtlData !== 'undefined' && TtlData.choices) || {}
  },

  eng() {
    var e = this.conf().engine || {}
    var n = (k, d) => (e[k] !== undefined && isFinite(Number(e[k])) ? Number(e[k]) : d)
    return {
      enabled: e.enabled !== false, max_active: n('max_active', 3), ttl_minutes: n('ttl_minutes', 30),
      credit_radius: n('credit_radius', 48), witness_radius: n('witness_radius', 32), notice_radius: n('notice_radius', 24),
      roll_minutes: n('roll_minutes', 5), chance: n('chance', 0.06), per_player: n('per_player', 0.3), max_chance: n('max_chance', 0.3),
      min_gap_minutes: n('min_gap_minutes', 15), min_distance: n('min_distance', 32), max_distance: n('max_distance', 64),
      scene_radius: n('scene_radius', 12), linger_seconds: n('linger_seconds', 20), repeat_days: n('repeat_days', 7),
      repeat_mult: n('repeat_mult', 0.5)
    }
  },

  row(id) {
    var list = this.conf().choice || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(id)) return list[i]
    }
    return null
  },

  routeOf(row, rid) {
    var list = (row && row.route) || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(rid)) return list[i]
    }
    return null
  },

  // Events with both a TOML row and a registered script.
  ids() {
    var self = this
    return (this.conf().choice || []).map(c => String(c.id)).filter(id => !!self.defs[id])
  },

  register(def) {
    if (!def || !/^[a-z0-9_]+$/.test(String(def.id))) {
      console.error(`[ttl] choices: register needs an id matching [a-z0-9_]+ (got ${def && def.id})`)
      return false
    }
    var id = String(def.id)
    this.defs[id] = def
    var row = this.row(id)
    if (!row) console.warn(`[ttl] choices: ${id} has no [[choice]] row in choices.toml, it can never spawn`)
    // The roads ledger knows the choice too (`/ttl roads list`, firsts per road): the first route of each road.
    try {
      if (row && typeof TtlRoads !== 'undefined') {
        var rd = { label: String(row.label), fair: String((this.routeOf(row, row.fair) || {}).road || 'good') }
        ;(row.route || []).forEach(r => { if (!rd[r.road]) rd[r.road] = r.costs || {} })
        TtlRoads.register(`choice.${id}`, rd)
      }
    } catch (e) {
      console.error(`[ttl] choices: registering choice.${id} with the two roads failed: ${e}`)
    }
    return true
  },

  // ---- storage -------------------------------------------------------------------------------------------------

  readJson(server, key, empty) {
    try {
      var raw = String(server.persistentData.getString(key))
      return raw ? JSON.parse(raw) : empty
    } catch (e) {
      console.warn(`[ttl] choices: ${key} unreadable, starting over (${e})`)
      return empty
    }
  },

  writeJson(server, key, value) {
    server.persistentData.putString(key, JSON.stringify(value))
  },

  // The active scenes, held in memory between writes so a poll, a click and a hit all change the same objects.
  scenes(server) {
    if (!this.cache) this.cache = this.readJson(server, this.ACTIVE, {})
    return this.cache
  },

  commit(server) {
    this.writeJson(server, this.ACTIVE, this.scenes(server))
  },

  scene(server, sid) {
    sid = this.resolveSid(server, sid)
    var s = this.scenes(server)[sid]
    if (s) return s
    var done = this.readJson(server, this.DONE, [])
    for (var i = done.length - 1; i >= 0; i--) {
      if (done[i].sid === sid) return done[i]
    }
    return null
  },

  open(server) {
    var all = this.scenes(server)
    return Object.keys(all).map(k => all[k]).filter(s => s.state === 'open')
  },

  near(server, player, radius) {
    var r = Number(radius || this.eng().credit_radius)
    var dim = TtlLife.dimensionOf(player)
    var self = this
    return this.open(server).filter(s => s.dim === dim && self.dist2(s, player.getX(), player.getY(), player.getZ()) <= r * r)
      .sort((a, b) => self.dist2(a, player.getX(), player.getY(), player.getZ()) - self.dist2(b, player.getX(), player.getY(), player.getZ()))
  },

  dist2(s, x, y, z) {
    var dx = s.x - x
    var dy = s.y - y
    var dz = s.z - z
    return dx * dx + dy * dy + dz * dz
  },

  pread(player) {
    var s = {}
    try {
      var raw = String(player.persistentData.getString(this.P_KEY))
      s = raw ? JSON.parse(raw) : {}
    } catch (e) {
      s = {}
    }
    s.done = s.done || {}
    s.tide = s.tide || { day: 0, dark: 0 }
    return s
  },

  pwrite(player, s) {
    player.persistentData.putString(this.P_KEY, JSON.stringify(s))
  },

  // ---- players ---------------------------------------------------------------------------------------------------

  isBot(name) {
    try {
      return typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(String(name))
    } catch (e) {
      return false
    }
  },

  life2(server, withBots) {
    var self = this
    var out = []
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) !== 'life2' || p.isSpectator()) return
        if (!withBots && self.isBot(p.username)) return
        out.push(p)
      } catch (e) {
        // a player mid-login
      }
    })
    return out
  },

  online(server) {
    var fake = Number(server.persistentData.getInt(this.TESTONLINE))
    if (fake > 0) return fake
    return Math.max(1, this.life2(server, true).length)
  },

  // base + per_player x (online - 1), at most base x max_mult.
  scaled(row, role, online) {
    var c = (row.count || {})[role] || { base: 1 }
    var base = Number(c.base || 1)
    var max = base * Math.max(1, Number((this.conf().scale || {}).max_mult || 3))
    return Math.max(1, Math.min(max, base + Number(c.per_player || 0) * Math.max(0, online - 1)))
  },

  multOf(online) {
    return Math.min(Math.max(1, Number((this.conf().scale || {}).max_mult || 3)), 1 + Math.max(0, online - 1) * 0.5)
  },

  // ---- skills and needs ------------------------------------------------------------------------------------------

  testSkills(player) {
    return String(player.persistentData.getString(this.P_SKILLS) || '').split(',').filter(s => s)
  },

  hasSkill(player, id) {
    id = String(id)
    if (this.testSkills(player).indexOf(id) >= 0) return true
    if (this.skillApi === undefined) {
      try {
        this.skillApi = Java.loadClass('io.github.manasmods.manascore.skill.api.SkillAPI')
      } catch (e) {
        this.skillApi = null
        console.warn(`[ttl] choices: ManasCore SkillAPI not reachable, skill routes read "no skill": ${e}`)
      }
    }
    if (!this.skillApi) return false
    var found = false
    try {
      this.skillApi.getSkillsFrom(player).getLearnedSkills().forEach(i => {
        if (!found && String(i.getSkillId()) === id && i.getMastery() >= 0) found = true
      })
    } catch (e) {
      console.warn(`[ttl] choices: reading ${player.username}'s skills failed: ${e}`)
    }
    return found
  },

  isNecro(player) {
    if (this.testSkills(player).indexOf('necro') >= 0) return true
    try {
      return typeof TtlLegion !== 'undefined' && Number(TtlLegion.rank(player)) >= 1
    } catch (e) {
      return false
    }
  },

  has(player, need) {
    need = String(need)
    if (need === 'necro') return this.isNecro(player)
    if (need.indexOf('skill:') === 0) return this.hasSkill(player, need.substring(6))
    if (need.indexOf('coins:') === 0) {
      try {
        return typeof TtlEcon !== 'undefined' && TtlEcon.canPay(player, Number(need.substring(6)))
      } catch (e) {
        return false
      }
    }
    return false
  },

  needText(need) {
    need = String(need)
    if (need === 'necro') return 'a necromancer (the Rite at a Bone Altar)'
    if (need.indexOf('skill:') === 0) {
      var id = need.substring(6)
      var name = id.split(':').pop().replace(/_/g, ' ')
      return `the skill ${name.charAt(0).toUpperCase()}${name.substring(1)}`
    }
    if (need.indexOf('coins:') === 0) {
      try {
        return typeof TtlEcon !== 'undefined' ? TtlEcon.text(Number(need.substring(6))) : `${need.substring(6)} bronze`
      } catch (e) {
        return `${need.substring(6)} bronze`
      }
    }
    return need
  },

  // Tensura's existence of a living entity (EP, name, owners), or null.
  existence(e) {
    if (this.storages === undefined) {
      try {
        this.storages = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
      } catch (err) {
        this.storages = null
        console.warn(`[ttl] choices: TensuraStorages not reachable, names, owners and EP are not read: ${err}`)
      }
    }
    try {
      return this.storages ? this.storages.getExistenceFrom(e) : null
    } catch (err) {
      return null
    }
  },

  // ---- the world around a scene -------------------------------------------------------------------------------------

  regionOf(dim, x, z) {
    try {
      if (dim === this.OVERWORLD && typeof TtlEvents !== 'undefined') {
        var r = TtlEvents.regionAt(Math.floor(x), Math.floor(z))
        if (r) return r
      }
    } catch (e) {
      console.warn(`[ttl] choices: region lookup failed: ${e}`)
    }
    var name = 'the wilds'
    try {
      if (typeof TtlRoads !== 'undefined') name = TtlRoads.regionName(dim, x, z)
    } catch (e) {
      // the fallback name
    }
    return { key: '', name: name }
  },

  onContinent(dim, x, z) {
    try {
      if (typeof TtlWorld !== 'undefined' && typeof TtlWorld.onContinent === 'function') return !!TtlWorld.onContinent(dim, x, z)
    } catch (e) {
      console.warn(`[ttl] choices: continent test failed, treated as outside: ${e}`)
      return false
    }
    return dim === this.OVERWORLD
  },

  surfaceY(level, x, z) {
    if (this.hm === undefined) {
      try {
        this.hm = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      } catch (e) {
        this.hm = null
      }
    }
    try {
      if (!this.hm || !level.hasChunkAt(x, z)) return null
      return Number(level.getHeight(this.hm.MOTION_BLOCKING_NO_LEAVES, Math.floor(x), Math.floor(z)))
    } catch (e) {
      return null
    }
  },

  // '' when a scene may stand here, else the reason. `ops` skips the continent, domain and protection rules (tests, staff).
  spotRefusal(server, dim, x, z, ops) {
    var e = this.eng()
    if (TtlLife.isMortal(dim)) return 'the Mortal Realm (Life 1) never sees a scene'
    var self = this
    var clash = this.open(server).filter(s => s.dim === dim && (s.x - x) * (s.x - x) + (s.z - z) * (s.z - z) < 4 * e.scene_radius * e.scene_radius)
    if (clash.length) return `too close to scene ${clash[0].sid}`
    if (ops) return ''
    if (dim !== this.OVERWORLD) return 'scenes appear in the Overworld only'
    var r = e.scene_radius
    var points = [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r]]
    for (var i = 0; i < points.length; i++) {
      var px = x + points[i][0]
      var pz = z + points[i][1]
      if (!this.onContinent(dim, px, pz)) return 'off the canon continent (R11)'
      try {
        if (typeof TtlDomains !== 'undefined' && TtlDomains.of(server, dim, px, pz)) return 'inside a protected domain'
      } catch (err) {
        console.warn(`[ttl] choices: domain check failed, the spot is refused: ${err}`)
        return 'domain check failed'
      }
      try {
        if (typeof TtlWild !== 'undefined' && TtlWild.protectedSpot(server, px, pz)) return 'a safe zone or a canon build'
      } catch (err) {
        console.warn(`[ttl] choices: protection check failed: ${err}`)
      }
    }
    var region = this.regionOf(dim, x, z)
    if (region.key && this.open(server).some(s => s.region && s.region.key === region.key)) return `${region.name} already has a scene`
    return ''
  },

  // A land spot min..max_distance from the player that passes spotRefusal, or null.
  pickSpot(server, player) {
    var e = this.eng()
    var level = player.level
    var dim = TtlLife.dimensionOf(player)
    for (var i = 0; i < 16; i++) {
      var ang = Math.random() * 2 * Math.PI
      var dist = e.min_distance + Math.random() * (e.max_distance - e.min_distance)
      var x = Math.floor(player.getX() + Math.cos(ang) * dist)
      var z = Math.floor(player.getZ() + Math.sin(ang) * dist)
      var y = this.surfaceY(level, x, z)
      if (y === null) continue
      var below = String(level.getBlock(x, y - 1, z).id)
      if (below === 'minecraft:water' || below === 'minecraft:lava') continue
      if (this.spotRefusal(server, dim, x, z, false)) continue
      return { x: x, y: y, z: z }
    }
    return null
  },

  // ---- entities ----------------------------------------------------------------------------------------------------

  tagsOf(e) {
    var out = []
    try {
      e.getTags().forEach(t => out.push(String(t)))
    } catch (err) {
      // no tags
    }
    return out
  },

  sidOf(e) {
    var tags = this.tagsOf(e)
    for (var i = 0; i < tags.length; i++) {
      var m = this.SID.exec(tags[i])
      if (m) return m[1]
    }
    return ''
  },

  roleOf(e) {
    var tags = this.tagsOf(e)
    for (var i = 0; i < tags.length; i++) {
      if (tags[i].indexOf('ttl.role.') === 0) return tags[i].substring(9)
    }
    return ''
  },

  // Loaded entities of a scene (optionally one role) round its centre.
  sceneEntities(server, scene, role) {
    var level = server.getLevel(scene.dim)
    if (!level) return []
    var r = this.eng().credit_radius + 16
    var tag = `ttl.scene.${scene.sid}`
    var rtag = role ? `ttl.role.${role}` : ''
    var list = null
    try {
      if (this.aabb === undefined) {
        try {
          this.aabb = Java.loadClass('net.minecraft.world.phys.AABB')
        } catch (e) {
          this.aabb = null
        }
      }
      if (this.aabb) list = level.getEntitiesWithin(new this.aabb(scene.x - r, scene.y - 64, scene.z - r, scene.x + r, scene.y + 64, scene.z + r))
    } catch (e) {
      list = null
    }
    if (!list) list = level.getEntities()
    var out = []
    list.forEach(e => {
      try {
        var tags = e.getTags()
        if (!tags.contains(tag)) return
        if (rtag && !tags.contains(rtag)) return
        out.push(e)
      } catch (err) {
        // a removed entity
      }
    })
    return out
  },

  // ---- spawning --------------------------------------------------------------------------------------------------

  nextSid(server) {
    var n = Number(server.persistentData.getInt(this.SEQ)) + 1
    server.persistentData.putInt(this.SEQ, n)
    return `s${n}`
  },

  spawn(server, id, opts) {
    opts = opts || {}
    id = String(id)
    var def = this.defs[id]
    var row = this.row(id)
    if (!def || !row) return { ok: false, error: `unknown event ${id} (${this.ids().join(', ') || 'none registered'})` }
    var e = this.eng()
    if (this.open(server).length >= e.max_active) return { ok: false, error: `${e.max_active} scenes are already open (O-C1)` }
    var dim = String(opts.dim || this.OVERWORLD)
    var x = Math.floor(Number(opts.x))
    var z = Math.floor(Number(opts.z))
    var why = this.spotRefusal(server, dim, x, z, !!opts.ops)
    if (why) return { ok: false, error: why }
    var level = server.getLevel(dim)
    if (!level) return { ok: false, error: `no dimension ${dim}` }
    var y = opts.y !== undefined ? Math.floor(Number(opts.y)) : this.surfaceY(level, x, z)
    if (y === null || y === undefined) return { ok: false, error: `the chunk at ${x} ${z} is not loaded` }
    var online = this.online(server)
    var now = Date.now()
    var scene = {
      sid: this.nextSid(server), id: id, dim: dim, x: x, y: y, z: z, region: this.regionOf(dim, x, z), started: now,
      ends: now + Number(row.ttl_minutes || e.ttl_minutes) * 60000, online: online, mult: this.multOf(online), n: {},
      by: String(opts.by || ''), home: '', state: 'open', route: '', actor: '', at: 0, clearAt: 0, part: {}, hits: {},
      prog: {}, blocks: [], heard: {}, paid: [], saw: []
    }
    var homes = (row.knobs || {}).homes || []
    if (homes.length) scene.home = String(homes[Math.floor(Math.random() * homes.length)])
    // The record exists before the first entity does: the orphan sweep (EntityEvents.spawned) only spares known scenes.
    this.scenes(server)[scene.sid] = scene
    this.commit(server)
    var ctx = this.ctx(server, scene)
    var ok = true
    try {
      ctx.summon('anchor', 'minecraft:marker', 0, 0, [], '')
      ok = def.spawn(server, scene, ctx) !== false
    } catch (err) {
      console.error(`[ttl] choices: ${id} failed to spawn: ${err}`)
      ok = false
    }
    if (!ok) {
      this.clear(server, scene)
      delete this.scenes(server)[scene.sid]
      this.commit(server)
      return { ok: false, error: `${id} could not be set up here` }
    }
    var st = this.readJson(server, this.STATE, {})
    st.last = scene.sid
    if (!opts.ops) st.spawn = now
    this.writeJson(server, this.STATE, st)
    this.commit(server)
    console.info(`[ttl] choices: ${scene.sid} ${id} at ${dim} ${x} ${y} ${z} (${scene.region.name}), online ${online}, counts ${JSON.stringify(scene.n)}${opts.ops ? ' [ops]' : ''}${scene.by ? ` near ${scene.by}` : ''}`)
    if (opts.near) this.hint(server, opts.near, scene)
    return { ok: true, sid: scene.sid, scene: scene }
  },

  // The soul a natural scene was rolled for hears which way to go.
  hint(server, player, scene) {
    var dx = scene.x - player.getX()
    var dz = scene.z - player.getZ()
    var dirs = ['south', 'south-west', 'west', 'north-west', 'north', 'north-east', 'east', 'south-east']
    var ang = Math.atan2(-dx, dz)
    var i = Math.round(ang / (Math.PI / 4))
    var dir = dirs[((i % 8) + 8) % 8]
    var dist = Math.round(Math.sqrt(dx * dx + dz * dz) / 10) * 10
    player.tell(Text.gold(`Something is happening about ${dist} blocks to the ${dir}: ${(this.row(scene.id) || {}).label || scene.id}.`))
  },

  // ---- the scene context ---------------------------------------------------------------------------------------------

  ctx(server, scene) {
    var self = this
    var row = this.row(scene.id) || { knobs: {} }
    var cmd = c => TtlCmd.run(server, `execute in ${scene.dim} run ${c}`)
    var ctx = {
      row: row,
      cmd: cmd,
      knob(k, d) {
        var v = (row.knobs || {})[k]
        return v === undefined ? d : v
      },
      count(role) {
        return self.scaled(row, role, scene.online)
      },
      level() {
        return server.getLevel(scene.dim)
      },
      at(dx, dz) {
        var x = scene.x + Math.floor(dx)
        var z = scene.z + Math.floor(dz)
        var y = self.surfaceY(server.getLevel(scene.dim), x, z)
        if (y === null || Math.abs(y - scene.y) > 6) y = scene.y
        return { x: x, y: y, z: z }
      },
      sel(role) {
        return `@e[tag=ttl.scene.${scene.sid}${role ? `,tag=ttl.role.${role}` : ''}]`
      },
      // A single-entity selector (commands such as `attribute` refuse one that may match more).
      one(role) {
        return `@e[tag=ttl.scene.${scene.sid},tag=ttl.role.${role},limit=1]`
      },
      // nbt: extra NBT parts ("NoAI:1b"); the scene and role tags and PersistenceRequired are added here.
      summon(role, type, dx, dz, nbt, name) {
        var p = ctx.at(dx, dz)
        var tags = ['ttl.scene', `ttl.scene.${scene.sid}`, `ttl.role.${role}`].concat((nbt && nbt.tags) || [])
        var parts = ['PersistenceRequired:1b', `Tags:[${tags.map(t => JSON.stringify(t)).join(',')}]`]
        ;(Array.isArray(nbt) ? nbt : ((nbt && nbt.parts) || [])).forEach(s => parts.push(s))
        if (name) parts.push(`CustomName:'${JSON.stringify({ text: String(name) })}'`)
        var ok = cmd(`summon ${type} ${p.x + 0.5} ${p.y} ${p.z + 0.5} {${parts.join(',')}}`) > 0
        if (ok) scene.n[role] = Number(scene.n[role] || 0) + 1
        else console.warn(`[ttl] choices: ${scene.sid} could not summon ${type} (${role})`)
        return ok
      },
      // A scene block on the surface (dy = 0) or above it; the previous block comes back at the cleanup.
      place(dx, dy, dz, block) {
        var p = ctx.at(dx, dz)
        var y = p.y + Math.floor(dy || 0)
        var level = server.getLevel(scene.dim)
        var prev = 'minecraft:air'
        try {
          prev = String(level.getBlock(p.x, y, p.z).id)
        } catch (e) {
          // keep air
        }
        if (cmd(`setblock ${p.x} ${y} ${p.z} ${block}`) > 0) {
          scene.blocks.push([p.x, y, p.z, prev])
          return { x: p.x, y: y, z: p.z }
        }
        return null
      },
      entities(role) {
        return self.sceneEntities(server, scene, role)
      },
      alive(role) {
        return self.sceneEntities(server, scene, role).filter(e => { try { return e.isAlive() } catch (err) { return false } })
      },
      // Entities only exist while their chunk is loaded: no deed is judged on an unloaded scene.
      loaded() {
        return self.sceneEntities(server, scene, 'anchor').length > 0
      },
      part(player, how) {
        var n = String(player.username)
        if (!scene.part[n]) scene.part[n] = String(how || 'took part')
      },
      resolve(rid, actor) {
        return self.resolve(server, scene.sid, rid, actor)
      },
      players(radius) {
        var r = Number(radius || self.eng().credit_radius)
        return self.life2(server, true).filter(p => TtlLife.dimensionOf(p) === scene.dim && self.dist2(scene, p.getX(), p.getY(), p.getZ()) <= r * r)
      },
      nearest(x, y, z, radius) {
        var best = null
        var bd = Number(radius) * Number(radius)
        ctx.players(self.eng().credit_radius).forEach(p => {
          var dx = p.getX() - x
          var dy = p.getY() - y
          var dz = p.getZ() - z
          var d = dx * dx + dy * dy + dz * dz
          if (d <= bd) {
            bd = d
            best = p
          }
        })
        return best
      },
      say(text, radius) {
        ctx.players(radius).forEach(p => p.tell(Text.of(String(text))))
      },
      give(player, item, n) {
        if (n > 0) TtlCmd.run(server, `give ${player.username} ${item} ${Math.floor(n)}`)
      }
    }
    return ctx
  },

  // ---- the menu ------------------------------------------------------------------------------------------------

  fill(text, scene) {
    return String(text || '').replace(/\{region\}/g, (scene.region && scene.region.name) || 'the wilds')
  },

  menu(server, player, scene) {
    var row = this.row(scene.id)
    if (!row) return
    var name = String(player.username)
    var left = Math.max(0, Math.ceil((scene.ends - Date.now()) / 60000))
    var color = { good: 'green', grey: 'gray', dark: 'dark_red' }
    var head = [{ text: '[Crossroads] ', color: 'gold' }, { text: `${row.label}`, color: 'yellow', bold: true }, { text: ` (${left} min) `, color: 'gray' }, { text: this.fill(row.intro, scene), color: 'white' }]
    server.runCommandSilent(`tellraw ${name} ${JSON.stringify(head)}`)
    var self = this
    ;(row.route || []).forEach(r => {
      var line = [{ text: `  ${r.road === 'dark' ? 'Shortcut' : r.road === 'grey' ? 'Grey road' : 'Honest road'}: `, color: color[r.road] || 'white' }]
      if (r.how === 'menu') {
        var needs = (r.need || []).map(n => self.needText(n)).join(' or ')
        line.push({
          text: `[${r.label}]`, color: r.road === 'dark' ? 'red' : 'aqua',
          clickEvent: { action: 'run_command', value: `/ttl choice take ${scene.sid} ${r.id}` },
          hoverEvent: { action: 'show_text', contents: needs ? `Needs ${needs}` : String(r.label) }
        })
        if (needs) line.push({ text: ` (needs ${needs})`, color: 'gray' })
      } else {
        line.push({ text: String(r.label), color: 'white' })
      }
      server.runCommandSilent(`tellraw ${name} ${JSON.stringify(line)}`)
    })
    scene.heard[name] = 1
  },

  // 'last' is the newest scene (tests); anything else is a sid.
  resolveSid(server, sid) {
    sid = String(sid)
    return sid === 'last' ? String(this.readJson(server, this.STATE, {}).last || '') : sid
  },

  // Whether a player may take a menu route now: {why ('' = yes), scene, route, hook, met (the need that is met)}.
  check(server, player, sid, rid) {
    var out = { why: '', scene: null, route: null, hook: {}, met: '' }
    var scene = this.scenes(server)[this.resolveSid(server, sid)]
    if (!scene || scene.state !== 'open') return (out.why = 'that scene is over', out)
    out.scene = scene
    if (TtlLife.phase(player) !== 'life2') return (out.why = 'only a soul in its second life can choose here', out)
    var e = this.eng()
    if (TtlLife.dimensionOf(player) !== scene.dim || this.dist2(scene, player.getX(), player.getY(), player.getZ()) > e.credit_radius * e.credit_radius) return (out.why = `you are too far away (within ${e.credit_radius} blocks)`, out)
    var row = this.row(scene.id)
    var route = this.routeOf(row, rid)
    if (!route) return (out.why = `no route ${rid} (${(row.route || []).map(r => r.id).join(', ')})`, out)
    out.route = route
    if (route.how !== 'menu') return (out.why = `${route.label}: that is done, not chosen`, out)
    out.hook = ((this.defs[scene.id] || {}).routes || {})[route.id] || {}
    var needs = route.need || []
    for (var i = 0; i < needs.length && !out.met; i++) {
      if (this.has(player, needs[i])) out.met = String(needs[i])
    }
    if (needs.length && !out.met) return (out.why = `you need ${needs.map(n => this.needText(n)).join(' or ')}`, out)
    if (typeof out.hook.need === 'function') out.why = String(out.hook.need(server, scene, player, this.ctx(server, scene)) || '')
    return out
  },

  // A menu route by a player (the button). '' when taken, else the reason.
  take(server, player, sid, rid) {
    var c = this.check(server, player, sid, rid)
    if (c.why) return c.why
    var scene = c.scene
    var route = c.route
    var ctx = this.ctx(server, scene)
    if (c.met.indexOf('coins:') === 0) {
      if (typeof TtlEcon === 'undefined' || !TtlEcon.charge(server, player, Number(c.met.substring(6)), `choice ${scene.id} ${route.id}`)) return `you cannot pay ${this.needText(c.met)}`
    }
    ctx.part(player, route.id)
    if (typeof c.hook.take === 'function') {
      var res = c.hook.take(server, scene, player, ctx)
      if (res) {
        this.commit(server)
        return String(res)
      }
    }
    var out = this.resolve(server, scene.sid, route.id, String(player.username))
    return out.ok ? '' : out.error
  },

  // ---- resolution ------------------------------------------------------------------------------------------------

  resolve(server, sid, rid, actor) {
    sid = this.resolveSid(server, sid)
    var scene = this.scenes(server)[sid]
    if (!scene) return { ok: false, error: `no scene ${sid}` }
    if (scene.state !== 'open') return { ok: false, error: `${sid} is already over (${scene.state})` }
    var row = this.row(scene.id)
    var route = this.routeOf(row, rid)
    if (!route) return { ok: false, error: `no route ${rid} in ${scene.id}` }
    var e = this.eng()
    var now = Date.now()
    actor = String(actor || '')
    scene.state = String(route.road)
    scene.route = String(route.id)
    scene.actor = actor
    scene.at = now
    scene.clearAt = now + e.linger_seconds * 1000
    var ctx = this.ctx(server, scene)
    var self = this
    var paid = []
    var saw = []
    ctx.players(e.credit_radius).forEach(p => {
      var n = String(p.username)
      if (n === actor || scene.part[n]) {
        try {
          self.payOne(server, scene, row, route, p)
          paid.push(n)
        } catch (err) {
          console.error(`[ttl] choices: paying ${n} for ${scene.sid} ${route.id} failed: ${err}`)
        }
      } else {
        saw.push(n)
      }
    })
    scene.paid = paid
    scene.saw = saw
    this.noteScene(server, scene, scene.state, actor)
    var def = this.defs[scene.id] || {}
    try {
      if (typeof def.resolved === 'function') def.resolved(server, scene, route.id, actor, ctx)
    } catch (err) {
      console.error(`[ttl] choices: ${scene.id} resolved hook failed: ${err}`)
    }
    var result = this.fill(route.result, scene)
    paid.forEach(n => {
      var p = server.getPlayerList().getPlayerByName(n)
      if (p) p.tell(Text.gold(result))
    })
    saw.forEach(n => {
      var p = server.getPlayerList().getPlayerByName(n)
      if (p) p.tell(Text.gray(`You saw it happen${actor ? ` (${actor})` : ''}: ${result}`))
    })
    this.commit(server)
    console.info(`[ttl] choices: ${scene.sid} ${scene.id} resolved ${route.id} (${route.road}) by ${actor || 'nobody'}; paid ${paid.join(', ') || 'nobody'}; saw ${saw.join(', ') || 'nobody'}`)
    return { ok: true, paid: paid, saw: saw }
  },

  // One credited soul: the dark cap of O-C2, TtlRoads.pay (the five costs), the coin reward, the chronicle flag, the ledger.
  payOne(server, scene, row, route, p) {
    var e = this.eng()
    var costs = JSON.parse(JSON.stringify(route.costs || { balance: 'none' }))
    var st = this.pread(p)
    var day = Math.floor(Date.now() / this.DAY_MS)
    if (st.tide.day !== day) st.tide = { day: day, dark: 0 }
    if (route.road === 'dark' && costs.balance === 'dark_deed') {
      var w = Math.abs(Number(((((TtlData.world || {}).balance || {}).weights) || {}).dark_deed || 1.5)) || 1.5
      var cap = Number((this.conf().balance || {}).dark_cap)
      if (!(cap >= 0)) cap = 5
      var times = Math.max(1, Number(costs.times || 1))
      var allowed = Math.max(0, Math.min(times, Math.floor((cap - st.tide.dark) / w + 1e-9)))
      st.tide.dark = Math.round((st.tide.dark + allowed * w) * 100) / 100
      costs.times = allowed
      if (allowed === 0) costs.balance = 'none'
    }
    // R11: a scene ops placed off the continent costs only the soul's own karma.
    if (!this.onContinent(scene.dim, scene.x, scene.z)) costs = { chaos: Number(costs.chaos || 0), balance: 'none' }
    var res = null
    if (typeof TtlRoads !== 'undefined') {
      res = TtlRoads.pay(server, p, {
        id: `choice.${scene.id}`, road: route.road, costs: costs, faction: scene.home || undefined,
        pos: { x: scene.x, y: scene.y, z: scene.z }, dim: scene.dim, radius: e.witness_radius, reason: `choice ${scene.id} ${route.id}`
      })
    } else {
      console.warn('[ttl] choices: TtlRoads is not loaded, the route costs nothing')
    }
    var rec = st.done[scene.id] || { good: 0, grey: 0, dark: 0, last: 0 }
    var coins = (route.reward || {}).coins
    if (coins && typeof TtlEcon !== 'undefined') {
      var amount = TtlEcon.amount(coins) * Number(scene.mult || 1)
      if (rec.last && Date.now() - rec.last < e.repeat_days * this.DAY_MS) amount *= e.repeat_mult
      amount = Math.floor(amount)
      if (amount > 0) TtlEcon.pay(server, p, amount, `choice ${scene.id} ${route.id}`)
    }
    if (route.flag) {
      try {
        if (typeof TtlChronicle !== 'undefined') TtlChronicle.note(server, 'flag', p, { flag: String(route.flag) })
      } catch (err) {
        console.error(`[ttl] choices: chronicle flag ${route.flag} failed: ${err}`)
      }
    }
    rec[route.road] = Number(rec[route.road] || 0) + 1
    rec.last = Date.now()
    st.done[scene.id] = rec
    st.last = { sid: scene.sid, event: scene.id, route: route.id, road: route.road, at: Date.now(), ok: !!(res && res.ok), noted: res ? res.noted : 0 }
    this.pwrite(p, st)
    return res
  },

  // The World Chronicle counts scenes, not souls: counts.choices.<road> and counts.choices_by.<event>.<road>.
  noteScene(server, scene, road, who) {
    try {
      if (typeof TtlChronicle === 'undefined') return
      TtlChronicle.note(server, 'choice', null, { who: who || '', count: `choices.${road}` })
      TtlChronicle.note(server, 'choice', null, { who: who || '', count: `choices_by.${scene.id}.${road}` })
    } catch (e) {
      console.error(`[ttl] choices: chronicle note for ${scene.sid} failed: ${e}`)
    }
  },

  neutral(server, sid, why) {
    var scene = this.scenes(server)[this.resolveSid(server, sid)]
    if (!scene || scene.state !== 'open') return false
    var row = this.row(scene.id) || {}
    var now = Date.now()
    scene.state = 'neutral'
    scene.route = 'neutral'
    scene.at = now
    scene.clearAt = now + this.eng().linger_seconds * 1000
    var ctx = this.ctx(server, scene)
    var def = this.defs[scene.id] || {}
    try {
      if (typeof def.neutral === 'function') def.neutral(server, scene, ctx)
    } catch (e) {
      console.error(`[ttl] choices: ${scene.id} neutral hook failed: ${e}`)
    }
    ctx.say(this.fill(row.neutral, scene))
    this.noteScene(server, scene, 'unresolved', '')
    this.commit(server)
    console.info(`[ttl] choices: ${scene.sid} ${scene.id} ended neutral (${why || 'expired'})`)
    return true
  },

  // ---- cleanup -----------------------------------------------------------------------------------------------------

  // Removes the scene's loaded entities and puts its blocks back; blocks of an unloaded chunk wait in the sweep list and
  // entities that load later are dropped by the orphan sweep.
  clear(server, scene) {
    this.sceneEntities(server, scene, '').forEach(e => {
      try {
        e.discard()
      } catch (err) {
        console.warn(`[ttl] choices: ${scene.sid} entity not removed: ${err}`)
      }
    })
    var sweep = this.readJson(server, this.SWEEP, [])
    var level = server.getLevel(scene.dim)
    ;(scene.blocks || []).slice().reverse().forEach(b => {
      if (level && level.hasChunkAt(b[0], b[2])) TtlCmd.run(server, `execute in ${scene.dim} run setblock ${b[0]} ${b[1]} ${b[2]} ${b[3]}`)
      else sweep.push([scene.dim, b[0], b[1], b[2], b[3]])
    })
    scene.blocks = []
    this.writeJson(server, this.SWEEP, sweep)
  },

  finish(server, scene) {
    this.clear(server, scene)
    delete this.scenes(server)[scene.sid]
    var done = this.readJson(server, this.DONE, [])
    done.push({ sid: scene.sid, id: scene.id, dim: scene.dim, x: scene.x, y: scene.y, z: scene.z, region: scene.region, state: scene.state, route: scene.route, actor: scene.actor, at: scene.at, n: scene.n, part: scene.part, prog: scene.prog, paid: scene.paid, saw: scene.saw, online: scene.online, mult: scene.mult, home: scene.home, cleared: true })
    while (done.length > 20) done.shift()
    this.writeJson(server, this.DONE, done)
    this.commit(server)
  },

  // Every scene now (ops: /ttl choice clear).
  clearAll(server) {
    var all = this.scenes(server)
    var self = this
    var n = 0
    Object.keys(all).forEach(sid => {
      self.finish(server, all[sid])
      n++
    })
    return n
  },

  sweep(server) {
    var list = this.readJson(server, this.SWEEP, [])
    if (!list.length) return
    var keep = []
    list.forEach(b => {
      var level = server.getLevel(b[0])
      if (level && level.hasChunkAt(b[1], b[3])) TtlCmd.run(server, `execute in ${b[0]} run setblock ${b[1]} ${b[2]} ${b[3]} ${b[4]}`)
      else keep.push(b)
    })
    this.writeJson(server, this.SWEEP, keep)
  },

  // ---- the poll --------------------------------------------------------------------------------------------------

  poll(server) {
    var all = this.scenes(server)
    var now = Date.now()
    var e = this.eng()
    var self = this
    Object.keys(all).forEach(sid => {
      var scene = all[sid]
      if (!scene) return
      try {
        if (scene.state === 'open') {
          if (now >= scene.ends) {
            self.neutral(server, sid, 'expired')
            return
          }
          var ctx = self.ctx(server, scene)
          if (!ctx.loaded()) return
          ctx.players(e.notice_radius).forEach(p => {
            if (!scene.heard[String(p.username)]) self.menu(server, p, scene)
          })
          var def = self.defs[scene.id] || {}
          if (typeof def.poll === 'function') def.poll(server, scene, ctx)
        } else if (now >= Number(scene.clearAt || 0)) {
          self.finish(server, scene)
        }
      } catch (err) {
        console.error(`[ttl] choices: poll of ${sid} failed: ${err}`)
      }
    })
    this.commit(server)
    this.sweep(server)
    if (!e.enabled) return
    var st = this.readJson(server, this.STATE, {})
    if (now - Number(st.roll || 0) < e.roll_minutes * 60000) return
    st.roll = now
    this.writeJson(server, this.STATE, st)
    this.roll(server, false)
  },

  // One open scene's poll now (test hooks and ops; the regular poll does the same every director poll).
  pollOne(server, sid) {
    var scene = this.scenes(server)[String(sid)]
    if (!scene || scene.state !== 'open') return false
    var ctx = this.ctx(server, scene)
    if (!ctx.loaded()) return false
    var def = this.defs[scene.id] || {}
    try {
      if (typeof def.poll === 'function') def.poll(server, scene, ctx)
    } catch (e) {
      console.error(`[ttl] choices: poll of ${sid} failed: ${e}`)
    }
    this.commit(server)
    return true
  },

  // Test verbs of a scene type (def.test(server, scene, player, verb, arg, ctx) → '' or the reason), then a poll.
  test(server, player, sid, verb, arg) {
    sid = this.resolveSid(server, sid)
    var scene = this.scenes(server)[sid]
    if (!scene) return `no scene ${sid}`
    if (scene.state !== 'open') return `${sid} is already over (${scene.state})`
    if (String(verb) === 'home') {
      scene.home = String(arg)
      this.commit(server)
      return ''
    }
    var def = this.defs[scene.id] || {}
    if (typeof def.test !== 'function') return `${scene.id} has no test verbs`
    var why = def.test(server, scene, player, String(verb), arg, this.ctx(server, scene))
    this.commit(server)
    if (why) return String(why)
    this.pollOne(server, sid)
    return ''
  },

  // ---- natural rolls -----------------------------------------------------------------------------------------------

  weightOf(server, row) {
    var w = Number(row.weight || 0)
    var wi = row.weight_if || {}
    try {
      if (typeof TtlChronicle !== 'undefined') {
        var tide = TtlChronicle.tide(server)
        if (tide && wi.tide && wi.tide[tide] !== undefined) w *= Number(wi.tide[tide])
        Object.keys(wi.milestone || {}).forEach(m => {
          if (TtlChronicle.reached(server, m)) w *= Number(wi.milestone[m])
        })
      }
    } catch (e) {
      console.warn(`[ttl] choices: chronicle view unreadable, plain weights: ${e}`)
    }
    return Math.max(0, w)
  },

  draw(server) {
    var self = this
    var rows = this.ids().map(id => ({ id: id, w: self.weightOf(server, self.row(id)) })).filter(r => r.w > 0)
    var total = rows.reduce((a, r) => a + r.w, 0)
    if (total <= 0) return ''
    var x = Math.random() * total
    for (var i = 0; i < rows.length; i++) {
      x -= rows[i].w
      if (x <= 0) return rows[i].id
    }
    return rows[rows.length - 1].id
  },

  // forced: /ttl choice roll (no chance, no gap). Returns {ok, error, sid}.
  roll(server, forced, onlyFor) {
    var e = this.eng()
    if (this.open(server).length >= e.max_active) return { ok: false, error: `${e.max_active} scenes already open` }
    var st = this.readJson(server, this.STATE, {})
    if (!forced && Date.now() - Number(st.spawn || 0) < e.min_gap_minutes * 60000) return { ok: false, error: 'too soon after the last scene' }
    var self = this
    var souls = this.life2(server, !!onlyFor).filter(p => {
      if (onlyFor && String(p.username) !== String(onlyFor)) return false
      var dim = TtlLife.dimensionOf(p)
      return dim === self.OVERWORLD && self.onContinent(dim, p.getX(), p.getZ())
    })
    if (!souls.length) return { ok: false, error: 'no Life 2 soul on the continent' }
    if (!forced) {
      var online = this.life2(server, false).length
      var chance = Math.min(e.max_chance, e.chance * (1 + e.per_player * Math.max(0, online - 1)))
      if (Math.random() >= chance) return { ok: false, error: 'no scene this time' }
    }
    var id = this.draw(server)
    if (!id) return { ok: false, error: 'no event has weight now' }
    var p = souls[Math.floor(Math.random() * souls.length)]
    var spot = this.pickSpot(server, p)
    if (!spot) return { ok: false, error: `no spot near ${p.username}` }
    return this.spawn(server, id, { x: spot.x, y: spot.y, z: spot.z, dim: this.OVERWORLD, by: String(p.username), near: p })
  },

  lines(server) {
    var self = this
    var now = Date.now()
    var out = []
    var all = this.scenes(server)
    var keys = Object.keys(all)
    out.push(`scenes: ${keys.length === 0 ? 'none' : ''}`)
    keys.forEach(sid => {
      var s = all[sid]
      out.push(`${sid} ${s.id} ${s.state}${s.route && s.state !== 'open' ? ` (${s.route} by ${s.actor || 'nobody'})` : ''} at ${s.dim} ${s.x} ${s.y} ${s.z} in ${s.region.name}, ${s.state === 'open' ? `${Math.max(0, Math.ceil((s.ends - now) / 60000))} min left` : 'clearing'}, counts ${JSON.stringify(s.n)}, part ${JSON.stringify(s.part)}`)
    })
    out.push(`events: ${this.ids().map(id => `${id} w${Math.round(self.weightOf(server, self.row(id)) * 100) / 100}`).join(', ') || 'none registered'}`)
    var st = this.readJson(server, this.STATE, {})
    out.push(`last roll ${st.roll ? new Date(st.roll).toISOString() : 'never'}, last natural scene ${st.spawn ? new Date(st.spawn).toISOString() : 'never'}, online (scale) ${this.online(server)}`)
    return out
  }
}

// ---- hooks ---------------------------------------------------------------------------------------------------------

// Right-click on a scene entity (main hand). event.cancel() exits by throwing: never inside a try that catches it.
ItemEvents.entityInteracted(event => {
  var handled = false
  try {
    var target = event.target
    var player = event.entity
    if (target && player && player.isPlayer() && String(event.hand) === 'MAIN_HAND' && target.getTags().contains('ttl.scene')) {
      var server = player.getServer()
      var sid = TtlChoices.sidOf(target)
      var scene = TtlChoices.scenes(server)[sid]
      var def = scene ? TtlChoices.defs[scene.id] : null
      if (scene && scene.state === 'open' && def && typeof def.interact === 'function' && TtlLife.phase(player) === 'life2') {
        handled = !!def.interact(server, scene, player, target, player.getMainHandItem(), TtlChoices.ctx(server, scene))
        TtlChoices.commit(server)
      }
    }
  } catch (err) {
    console.error(`[ttl] choices: right-click on a scene entity failed: ${err}`)
  }
  if (handled) event.cancel()
})

// Right-click on a scene block.
BlockEvents.rightClicked(event => {
  var handled = false
  try {
    var player = event.player
    if (player && String(event.hand) === 'MAIN_HAND' && event.block.hasTag('ttl:scene')) {
      var server = player.getServer()
      var b = event.block
      var dim = TtlLife.dimensionOf(player)
      var scene = null
      TtlChoices.open(server).forEach(s => {
        if (!scene && s.dim === dim && (s.blocks || []).some(k => k[0] === b.x && k[1] === b.y && k[2] === b.z)) scene = s
      })
      var def = scene ? TtlChoices.defs[scene.id] : null
      if (scene && def && typeof def.useBlock === 'function' && TtlLife.phase(player) === 'life2') {
        handled = !!def.useBlock(server, scene, player, b, player.getMainHandItem(), TtlChoices.ctx(server, scene))
        TtlChoices.commit(server)
      }
    }
  } catch (err) {
    console.error(`[ttl] choices: right-click on a scene block failed: ${err}`)
  }
  if (handled) event.cancel()
})

// Who hit which scene entity: participation (the credit rule) and the last attacker per role (who killed it).
EntityEvents.afterHurt(event => {
  try {
    var e = event.entity
    if (e.isPlayer() || !e.getTags().contains('ttl.scene')) return
    var attacker = event.source.actual
    if (!attacker || !attacker.isPlayer()) return
    var server = attacker.getServer()
    var scene = TtlChoices.scenes(server)[TtlChoices.sidOf(e)]
    if (!scene || scene.state !== 'open') return
    var role = TtlChoices.roleOf(e)
    var name = String(attacker.username)
    scene.hits[role] = name
    if (!scene.part[name]) scene.part[name] = 'hit'
    var def = TtlChoices.defs[scene.id] || {}
    if (typeof def.hurt === 'function') def.hurt(server, scene, attacker, e, role, TtlChoices.ctx(server, scene))
    TtlChoices.commit(server)
  } catch (err) {
    console.error(`[ttl] choices: hit tracking failed: ${err}`)
  }
})

// Orphans: a scene entity whose scene is gone (its chunk was unloaded at the cleanup) never comes back.
EntityEvents.spawned(event => {
  var orphan = false
  try {
    var e = event.entity
    if (!e.isPlayer() && e.getTags().contains('ttl.scene')) {
      var sid = TtlChoices.sidOf(e)
      orphan = !sid || !TtlChoices.scenes(e.getServer())[sid]
    }
  } catch (err) {
    console.error(`[ttl] choices: orphan check failed: ${err}`)
  }
  if (orphan) event.cancel()
})

// Timing: a poll of the event director (no [[event]] row: never scheduled, `ttl events fire choice_scenes` is refused).
try {
  if (typeof TtlEvents !== 'undefined') {
    TtlChoices.director = TtlEvents.register({
      id: 'choice_scenes',
      label: 'Crossroads of conscience',
      canStart() {
        return 'choice scenes roll by themselves (choices/engine.js); use /ttl choice spawn or /ttl choice roll'
      },
      poll(server) {
        TtlChoices.poll(server)
      }
    })
  }
} catch (e) {
  console.error(`[ttl] choices: director registration failed, using our own loop: ${e}`)
}

ServerEvents.loaded(event => {
  var server = event.server
  TtlChoices.cache = null
  if (TtlChoices.director) return
  console.warn('[ttl] choices: the event director is not loaded, scenes poll on their own loop')
  var stamp = String(Date.now())
  server.persistentData.putString('ttl.choices.loop', stamp)
  var loop = () => server.scheduleInTicks(100, () => {
    if (String(server.persistentData.getString('ttl.choices.loop')) !== stamp) return
    try {
      TtlChoices.poll(server)
    } catch (e) {
      console.error(`[ttl] choices: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})
