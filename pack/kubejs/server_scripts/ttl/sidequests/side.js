// priority: 70
// Side quests: the reusable mechanics of the classic isekai side jobs (sidequests work package; data in
// design/data/sidequests.toml -> TtlData.sidequests, places in places.js). Life 2 only, personal (a party member takes
// the same job for themselves), never a gate for the story and never a skill or unique.
//
// Kinds
//   escort   an Easy NPC client (ttl_client_<id>) waits at `from` (or appears beside the soul), follows the soul
//            (FOLLOW_PLAYER) to `to`; ambush waves spawn round it at fractions of the way and are set on it; the job
//            fails when the client dies, or when the soul stays farther than settings.leash for leash_seconds
//   deliver  a parcel (paper with custom_data {ttl_parcel:"<key>"} and a name) is given at start or picked up at `pickup`,
//            and handed over automatically within deliver_radius of `to`; optional time limit (`minutes`)
//   travel   reach `to` (a place) within `radius`
//   fetch    have `items` and stand at `at` (handed in automatically), or `/ttl sidequest turnin` anywhere when `at` = ""
//   cull     kill `count` of `entity` (minecraft.killed:<id> objectives `ttl.sq.<ns>_<path>`, sampled every poll, like
//            the guild); only kills while the soul stands in faction `region` or within `radius` of place `near` count
// Success sets the stage ttl.quest.side.<id> (FTB stage tasks read it; a repeatable chapter quest removes it again with a
// stage reward), pays the optional `reward` and calls the listeners. A failure tells why and frees the slot.
// Discovery: a place with `discover = true` gives ttl.quest.side.seen.<place> when a Life 2 soul comes within
// settings.discover_radius (travel quests in the book are stage tasks on it).
//
// PUBLIC API (radiant boards, events, other packages):
//   TtlSide.start(server, player, kind, params)   kind = an authored quest id (params may override its fields) or one of
//            escort|deliver|travel|fetch|cull with params shaped like a [[quest]] row (to/from/pickup/near may be place ids;
//            params.key names the job, default the id; params.stage = false skips the stage). Returns {ok, key, error}.
//   TtlSide.complete(server, player, key, why) / TtlSide.fail(server, player, key, why)
//   TtlSide.listen(name, fn)      fn(server, player, rec, outcome) with outcome 'done' | 'failed' | 'abandoned'
//   TtlSide.active(player)        {key: rec} of the soul's running jobs
// Player persistentData `ttl.side` = {active: {key: rec}, done: {id: ms}, fail: {id: ms}, n}. Entity tags:
// `ttl.side`, `ttl.side.client`, `ttl.side.o.<owner uuid>` (escort clients), `ttl.side.amb.<token>` (ambush mobs).
const TtlSide = {
  KEY: 'ttl.side',
  STAGE: 'ttl.quest.side.',
  KINDS: ['escort', 'deliver', 'travel', 'fetch', 'cull'],
  OBJ: 'ttl.sq.',
  listeners: {},

  conf() {
    return TtlData.sidequests
  },

  set() {
    return this.conf().settings
  },

  def(id) {
    var all = this.conf().quest || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  client(id) {
    var all = this.conf().client || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  defOf(rec) {
    return rec.def || this.def(rec.id)
  },

  listen(name, fn) {
    this.listeners[String(name)] = fn
  },

  emit(server, player, rec, outcome) {
    var self = this
    Object.keys(this.listeners).forEach(n => {
      try {
        self.listeners[n](server, player, rec, outcome)
      } catch (e) {
        console.error(`[ttl] side: listener ${n} failed on ${rec.key} (${outcome}): ${e}`)
      }
    })
  },

  // ---- records ----

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY) || '')
    var d = {}
    try {
      d = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] side: ${player.username}'s record is unreadable, starting fresh: ${e}`)
    }
    d.active = d.active || {}
    d.done = d.done || {}
    d.fail = d.fail || {}
    d.n = d.n || 0
    return d
  },

  write(player, d) {
    player.persistentData.putString(this.KEY, JSON.stringify(d))
  },

  active(player) {
    return this.read(player).active
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  stageOf(id) {
    return this.STAGE + id
  },

  safeKey(k) {
    return String(k).toLowerCase().replace(/[^a-z0-9_.-]/g, '_').slice(0, 48)
  },

  // ---- starting ----

  // Why this soul may not start def now, or ''. `taking` = through `/ttl sidequest take` (the giver must be near).
  refusal(server, player, def, key, taking) {
    if (TtlLife.phase(player) !== 'life2') return 'side quests are for souls reborn in the Tensura world'
    var d = this.read(player)
    if (d.active[key]) return `you are already on "${def.title}" (/ttl sidequest)`
    if (Object.keys(d.active).length >= Number(this.set().max_active)) return `you carry ${this.set().max_active} jobs already: finish or abandon one`
    if (def.authored) {
      if (player.stages.has(this.stageOf(def.id))) {
        return Number(def.repeat_hours || 0) > 0 ? `claim the reward of "${def.title}" in the quest book first` : `you already did "${def.title}"`
      }
      var last = Number(d.done[def.id] || 0)
      var hours = Number(def.repeat_hours || 0)
      if (last > 0 && hours <= 0) return `you already did "${def.title}"`
      if (last > 0 && Date.now() - last < hours * 3600000) {
        return `"${def.title}" is not on offer again for ${Math.ceil((last + hours * 3600000 - Date.now()) / 3600000)} h`
      }
    }
    var req = def.requires || []
    for (var i = 0; i < req.length; i++) {
      if (!player.stages.has(String(req[i]))) return `"${def.title}" is not open to you yet`
    }
    if (taking && def.giver) {
      var pos = TtlSidePlaces.resolve(server, String(def.giver), null, true)
      if (!pos || !TtlSidePlaces.near(player, pos, Number(this.set().take_radius))) return `ask for "${def.title}" at ${TtlSidePlaces.title(def.giver)}`
    }
    return ''
  },

  start(server, player, kind, params, taking) {
    var opts = params || {}
    var base = this.def(kind)
    var def = {}
    var k
    if (base) {
      for (k in base) def[k] = base[k]
      for (k in opts) def[k] = opts[k]
      def.authored = true
    } else if (this.KINDS.indexOf(String(kind)) >= 0) {
      for (k in opts) def[k] = opts[k]
      def.kind = String(kind)
      def.id = this.safeKey(def.id || `api_${kind}`)
      def.title = def.title || `${kind} job`
      def.authored = false
    } else {
      return { ok: false, error: `unknown side quest or kind ${kind} (kinds: ${this.KINDS.join(', ')})` }
    }
    var key = this.safeKey(opts.key || def.id)
    var why = this.refusal(server, player, def, key, taking)
    if (why) return { ok: false, error: why }
    var rec = { id: String(def.id), key: key, kind: String(def.kind), title: String(def.title), t0: Date.now(), st: {},
      until: Number(def.minutes || 0) > 0 ? Date.now() + Number(def.minutes) * 60000 : 0,
      tok: Math.floor(Math.random() * 1e9).toString(36) }
    if (!def.authored) rec.def = def
    var err = this.begin(server, player, def, rec)
    if (err) return { ok: false, error: err }
    var d = this.read(player)
    d.active[key] = rec
    this.write(player, d)
    player.tell(Text.gold(`Side quest: ${def.title}.`))
    if (def.text) player.tell(Text.gray(String(def.text)))
    if (rec.until) player.tell(Text.gray(`You have ${def.minutes} minutes.`))
    console.info(`[ttl] side: ${player.username} started ${key} (${def.kind})`)
    return { ok: true, key: key, error: '' }
  },

  // Kind-specific setup; '' or an error (nothing is recorded on an error).
  begin(server, player, def, rec) {
    var S = this.set()
    if (def.kind === 'escort') {
      if (!this.client(def.client)) return `unknown client ${def.client}`
      var to = TtlSidePlaces.resolve(server, String(def.to), null, true)
      if (!to) return `${TtlSidePlaces.title(def.to)} is not in the world yet`
      if (def.from) {
        var from = TtlSidePlaces.resolve(server, String(def.from), null, true)
        if (!from) return `${TtlSidePlaces.title(def.from)} is not in the world yet`
        rec.st = { phase: 'wait', fired: [], away: 0 }
        player.tell(Text.gray(`${this.client(def.client).name} waits for you at ${TtlSidePlaces.title(def.from)}.`))
        return ''
      }
      rec.st = { phase: 'go', fired: [], away: 0 }
      var here = { dim: TtlLife.dimensionOf(player), x: player.getX(), y: player.getY(), z: player.getZ() }
      return this.spawnClient(server, player, def, rec, here) ? '' : 'the client could not be summoned (see the log)'
    }
    if (def.kind === 'deliver') {
      if (!TtlSidePlaces.get(def.to) || !TtlSidePlaces.resolve(server, String(def.to), null, true)) return `${TtlSidePlaces.title(def.to)} is not in the world yet`
      if (def.pickup) {
        rec.st = { phase: 'pickup' }
        player.tell(Text.gray(`Collect it at ${TtlSidePlaces.title(def.pickup)}.`))
        return ''
      }
      rec.st = { phase: 'carry' }
      this.giveParcel(server, player, def, rec)
      return ''
    }
    if (def.kind === 'travel') {
      if (!TtlSidePlaces.get(def.to)) return `unknown place ${def.to}`
      return ''
    }
    if (def.kind === 'fetch') {
      if (!def.items || Object.keys(def.items).length === 0) return 'nothing to fetch'
      return ''
    }
    if (def.kind === 'cull') {
      this.ensureObjective(server, def.entity)
      rec.st = { got: 0, last: this.killValue(server, player, def.entity) }
      return ''
    }
    return `unknown kind ${def.kind}`
  },

  // ---- escort ----

  spawnClient(server, player, def, rec, pos) {
    var c = this.client(def.client)
    var e = TtlSideNpc.spawn(server, pos, `ttl_client_${c.id}`, ['ttl.side', 'ttl.side.client', `ttl.side.o.${this.uid(player)}`])
    if (!e) return false
    TtlSideNpc.health(server, e, Number(this.set().client_hp))
    TtlSideNpc.cmd(server, e, `objective {npc} set follow player ${player.username}`)
    var to = TtlSidePlaces.resolve(server, String(def.to), null, true)
    rec.st.npc = TtlSideNpc.uuidOf(e)
    rec.st.dim = pos.dim
    rec.st.lx = e.getX()
    rec.st.lz = e.getZ()
    rec.st.total = Math.max(1, TtlSidePlaces.dist(e.getX(), e.getZ(), to.x, to.z))
    console.info(`[ttl] side: ${player.username}'s client ${c.id} (${rec.st.npc}) for ${rec.key} at ${pos.x} ${pos.y} ${pos.z}`)
    return true
  },

  ambush(server, player, def, rec, client, wave) {
    var S = this.set()
    var mobs = wave.mobs || {}
    var tag = `ttl.side.amb.${rec.tok}`
    var n = 0
    var self = this
    Object.keys(mobs).forEach(id => {
      for (var i = 0; i < Number(mobs[id]); i++) {
        var ang = Math.random() * Math.PI * 2
        var r = S.ambush_distance[0] + Math.random() * (S.ambush_distance[1] - S.ambush_distance[0])
        var x = Math.floor(client.getX() + Math.cos(ang) * r) + 0.5
        var z = Math.floor(client.getZ() + Math.sin(ang) * r) + 0.5
        var y = TtlSidePlaces.surfaceY(server, rec.st.dim, x, z)
        if (y === null) continue
        if (TtlCmd.run(server, `execute in ${rec.st.dim} run summon ${id} ${x} ${y} ${z} {Tags:["ttl.side","ttl.side.amb","${tag}"]}`) > 0) n++
      }
    })
    rec.st.aim = 3
    player.tell(Text.red(`Ambush! Protect ${self.client(def.client).name}!`))
    console.info(`[ttl] side: ambush on ${player.username}'s ${rec.key}: ${n} spawned`)
  },

  // Sets the ambush mobs of a job on its client (a few polls after each wave: mobs that spawn out of reach pick it later).
  aim(server, rec, client) {
    var tag = `ttl.side.amb.${rec.tok}`
    try {
      server.getLevel(rec.st.dim).getEntities().forEach(e => {
        if (!e.isAlive() || !TtlSideNpc.hasTag(e, tag)) return
        try {
          e.setTarget(client)
        } catch (x) {
          // not a Mob
        }
      })
    } catch (e2) {
      console.warn(`[ttl] side: aiming the ambush of ${rec.key} failed: ${e2}`)
    }
  },

  tickEscort(server, player, def, rec, ms) {
    var S = this.set()
    var st = rec.st
    if (st.phase === 'wait') {
      var from = TtlSidePlaces.resolve(server, String(def.from))
      if (!from || !TtlSidePlaces.near(player, from, Number(S.appear_radius))) return ''
      st.phase = 'go'
      if (!this.spawnClient(server, player, def, rec, from)) return 'fail:the client could not be summoned'
      player.tell(Text.green(`${this.client(def.client).name} is with you now. Lead them to ${TtlSidePlaces.title(def.to)}.`))
      return 'save'
    }
    var client = TtlSideNpc.byUuid(server, st.dim, st.npc)
    if (!client || !client.isAlive()) {
      // Found but dead is a fall; a death is also failed at once by the EntityEvents.death hook below. Not found is only
      // "away": an entity unloads with its chunk while `execute if loaded` still answers yes (seen 18/11/2026).
      if (client) return `fail:${this.client(def.client).name} has fallen`
      st.away += ms
      return st.away > Number(S.leash_seconds) * 1000 ? `fail:you left ${this.client(def.client).name} behind` : 'save'
    }
    st.lx = client.getX()
    st.lz = client.getZ()
    var to = TtlSidePlaces.resolve(server, String(def.to), null, true)
    if (!to) return ''
    var far = TtlLife.dimensionOf(player) !== String(st.dim) ||
      TtlSidePlaces.dist(player.getX(), player.getZ(), client.getX(), client.getZ()) > Number(S.leash)
    if (far) {
      st.away += ms
      if (st.away > Number(S.leash_seconds) * 1000) return `fail:you left ${this.client(def.client).name} behind`
      if (st.away === ms) player.tell(Text.red(`${this.client(def.client).name} has lost sight of you. Go back!`))
    } else {
      st.away = 0
    }
    var left = TtlSidePlaces.dist(client.getX(), client.getZ(), to.x, to.z)
    if (left <= Number(S.arrive_radius)) return 'done'
    var progress = 1 - left / Number(st.total)
    var waves = def.ambush || []
    for (var i = 0; i < waves.length; i++) {
      if (st.fired.indexOf(i) < 0 && progress >= Number(waves[i].at)) {
        st.fired.push(i)
        this.ambush(server, player, def, rec, client, waves[i])
      }
    }
    if (st.aim > 0) {
      st.aim--
      this.aim(server, rec, client)
    }
    return 'save'
  },

  // ---- deliver ----

  parcelPredicate(rec) {
    return `minecraft:paper[minecraft:custom_data={ttl_parcel:"${rec.key}"}]`
  },

  snbtText(obj) {
    return "'" + JSON.stringify(obj).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'"
  },

  giveParcel(server, player, def, rec) {
    var name = this.snbtText({ text: String(def.parcel), italic: false, color: 'gold' })
    var lore = this.snbtText({ text: `Side quest: ${def.title}. For ${TtlSidePlaces.title(def.to)}.`, italic: true, color: 'gray' })
    TtlCmd.run(server, `give ${player.username} minecraft:paper[minecraft:custom_name=${name},minecraft:lore=[${lore}],` +
      `minecraft:custom_data={ttl_parcel:"${rec.key}"}] 1`)
    player.tell(Text.gold(`You carry: ${def.parcel}.`))
  },

  // How many of this job's parcels the soul carries (`clear <p> <item> 0` counts without removing).
  parcels(server, player, rec) {
    return TtlCmd.run(server, `clear ${player.username} ${this.parcelPredicate(rec)} 0`)
  },

  takeParcels(server, player, rec) {
    TtlCmd.run(server, `clear ${player.username} ${this.parcelPredicate(rec)} 64`)
  },

  tickDeliver(server, player, def, rec) {
    var S = this.set()
    if (rec.st.phase === 'pickup') {
      var at = TtlSidePlaces.resolve(server, String(def.pickup), null, true)
      if (!at || !TtlSidePlaces.near(player, at, Number(S.deliver_radius) * 2)) return ''
      rec.st.phase = 'carry'
      player.tell(Text.green(`Found at ${TtlSidePlaces.title(def.pickup)}.`))
      this.giveParcel(server, player, def, rec)
      return 'save'
    }
    var to = TtlSidePlaces.resolve(server, String(def.to), null, true)
    var have = this.parcels(server, player, rec)
    if (have < 1) {
      if (!rec.st.lost) {
        rec.st.lost = 1
        player.tell(Text.red(`You no longer carry ${def.parcel}. Find it, or /ttl sidequest abandon ${rec.key}.`))
        return 'save'
      }
      return ''
    }
    if (rec.st.lost) {
      rec.st.lost = 0
      return 'save'
    }
    if (to && TtlSidePlaces.near(player, to, Number(S.deliver_radius))) return 'done'
    return ''
  },

  // ---- fetch ----

  hasItems(player, items) {
    return Object.keys(items).every(id => Number(player.inventory.count(id)) >= Number(items[id]))
  },

  takeItems(server, player, items) {
    Object.keys(items).forEach(id => TtlCmd.run(server, `clear ${player.username} ${id} ${Number(items[id])}`))
  },

  tickFetch(server, player, def, rec) {
    if (!def.at) return ''
    var at = TtlSidePlaces.resolve(server, String(def.at), null, true)
    if (!at || !TtlSidePlaces.near(player, at, Number(this.set().take_radius))) return ''
    if (!this.hasItems(player, def.items)) {
      if (!rec.st.told) {
        rec.st.told = 1
        player.tell(Text.gray(`"${def.title}": still missing ${this.missing(player, def.items)}.`))
        return 'save'
      }
      return ''
    }
    this.takeItems(server, player, def.items)
    return 'done'
  },

  missing(player, items) {
    return Object.keys(items).filter(id => Number(player.inventory.count(id)) < Number(items[id]))
      .map(id => `${Number(items[id]) - Number(player.inventory.count(id))} ${id.replace(/^[^:]*:/, '').replace(/_/g, ' ')}`).join(', ')
  },

  // ---- cull ----

  objective(entity) {
    return this.OBJ + String(entity).replace(/[^a-z0-9_.+-]/g, '_')
  },

  ensureObjective(server, entity) {
    var name = this.objective(entity)
    var crit = 'minecraft.killed:' + String(entity).replace(':', '.')
    var board = server.getScoreboard()
    var obj = board.getObjective(name)
    if (obj && String(obj.getCriteria().getName()) === crit) return
    if (obj) TtlCmd.run(server, `scoreboard objectives remove ${name}`)
    TtlCmd.run(server, `scoreboard objectives add ${name} ${crit}`)
    if (!board.getObjective(name)) console.error(`[ttl] side: could not create objective ${name} (${crit})`)
  },

  killValue(server, player, entity) {
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective(this.objective(entity))
      if (!obj) return 0
      var info = board.getPlayerScoreInfo(player, obj)
      return info ? Number(info.value()) : 0
    } catch (e) {
      return 0
    }
  },

  inCullArea(server, player, def) {
    if (def.region) {
      try {
        if (typeof TtlRep === 'undefined' || TtlLife.dimensionOf(player) !== TtlSidePlaces.OVERWORLD) return false
        var f = TtlRep.factionAt(Math.floor(player.getX()), Math.floor(player.getZ()))
        return !!f && String(f.id) === String(def.region)
      } catch (e) {
        return false
      }
    }
    if (def.near) {
      var pos = TtlSidePlaces.resolve(server, String(def.near), null, true)
      return !!pos && TtlSidePlaces.near(player, pos, Number(def.radius || 64))
    }
    return true
  },

  tickCull(server, player, def, rec) {
    var cur = this.killValue(server, player, def.entity)
    var delta = cur - Number(rec.st.last)
    if (delta === 0) return ''
    rec.st.last = cur
    if (delta > 0 && this.inCullArea(server, player, def)) {
      rec.st.got = Math.min(Number(def.count), Number(rec.st.got) + delta)
      if (rec.st.got >= Number(def.count)) return 'done'
      player.tell(Text.gray(`"${def.title}": ${rec.st.got}/${def.count}.`))
    }
    return 'save'
  },

  // ---- the poll ----

  tickOne(server, player, rec, ms) {
    var def = this.defOf(rec)
    if (!def) return 'fail:this job no longer exists'
    if (rec.until && Date.now() > Number(rec.until)) return 'fail:time ran out'
    if (rec.kind === 'escort') return this.tickEscort(server, player, def, rec, ms)
    if (rec.kind === 'deliver') return this.tickDeliver(server, player, def, rec)
    if (rec.kind === 'travel') {
      var to = TtlSidePlaces.resolve(server, String(def.to), null, true)
      return to && TtlSidePlaces.near(player, to, Number(def.radius || this.set().travel_radius)) ? 'done' : ''
    }
    if (rec.kind === 'fetch') return this.tickFetch(server, player, def, rec)
    if (rec.kind === 'cull') return this.tickCull(server, player, def, rec)
    return ''
  },

  tick(server, player, ms) {
    var d = this.read(player)
    var keys = Object.keys(d.active)
    if (keys.length === 0) return
    var changed = false
    var self = this
    var outcomes = []
    keys.forEach(key => {
      var out = ''
      try {
        out = self.tickOne(server, player, d.active[key], ms)
      } catch (e) {
        console.error(`[ttl] side: ${player.username} ${key} poll failed: ${e}`)
      }
      if (out === 'save') changed = true
      else if (out === 'done' || String(out).startsWith('fail:')) outcomes.push([key, out])
    })
    if (changed) this.write(player, d)
    outcomes.forEach(o => {
      if (o[1] === 'done') self.complete(server, player, o[0], 'done')
      else self.fail(server, player, o[0], String(o[1]).slice(5))
    })
  },

  // Despawns what a job left in the world (its client, its parcels).
  cleanup(server, player, rec) {
    if (rec.kind === 'escort' && rec.st && rec.st.npc) {
      var c = TtlSideNpc.byUuid(server, rec.st.dim, rec.st.npc)
      if (c) TtlSideNpc.remove(server, c)
    }
    if (rec.kind === 'deliver') this.takeParcels(server, player, rec)
  },

  complete(server, player, key, why) {
    var d = this.read(player)
    var rec = d.active[key]
    if (!rec) return false
    var def = this.defOf(rec) || {}
    if (rec.kind === 'escort') {
      var c = this.client(def.client)
      if (c) player.tell(Text.green(`${c.name}: "Thank you. I would not have made it alone."`))
    }
    this.cleanup(server, player, rec)
    delete d.active[key]
    d.done[rec.id] = Date.now()
    d.n += 1
    this.write(player, d)
    if (def.stage !== false && rec.id) player.stages.add(this.stageOf(rec.id))
    this.pay(server, player, def, rec)
    player.tell(Text.green(`Side quest complete: ${rec.title}.${def.authored === false || !this.def(rec.id) ? '' : ' Claim your reward in the quest book.'}`))
    console.info(`[ttl] side: ${player.username} completed ${key} (${why || 'done'})`)
    this.emit(server, player, rec, 'done')
    return true
  },

  pay(server, player, def, rec) {
    var rw = def.reward || {}
    try {
      if (rw.coins && typeof TtlEcon !== 'undefined') TtlEcon.pay(server, player, rw.coins, `side:${rec.id}`)
    } catch (e) {
      console.error(`[ttl] side: paying ${rec.id} failed: ${e}`)
    }
    var rep = rw.rep || {}
    Object.keys(rep).forEach(f => {
      try {
        if (typeof TtlRep !== 'undefined') TtlRep.add(server, player, f, rep[f], `side ${rec.id}`)
      } catch (e) {
        console.error(`[ttl] side: reputation for ${rec.id} (${f}) failed: ${e}`)
      }
    })
  },

  fail(server, player, key, why, outcome) {
    var d = this.read(player)
    var rec = d.active[key]
    if (!rec) return false
    this.cleanup(server, player, rec)
    delete d.active[key]
    if (outcome !== 'abandoned') d.fail[rec.id] = Date.now()
    this.write(player, d)
    player.tell(Text.red(`Side quest ${outcome === 'abandoned' ? 'abandoned' : 'failed'}: ${rec.title}${why ? ` (${why})` : ''}.`))
    console.info(`[ttl] side: ${player.username} ${outcome || 'failed'} ${key}: ${why}`)
    this.emit(server, player, rec, outcome || 'failed')
    return true
  },

  // `/ttl sidequest turnin`: fetch jobs without a hand-in place, wherever the soul stands.
  turnin(server, player) {
    var d = this.read(player)
    var n = 0
    var self = this
    Object.keys(d.active).forEach(key => {
      var rec = d.active[key]
      var def = self.defOf(rec)
      if (!def || rec.kind !== 'fetch' || def.at) return
      if (!self.hasItems(player, def.items)) return
      self.takeItems(server, player, def.items)
      self.complete(server, player, key, 'turnin')
      n++
    })
    return n
  },

  // ---- discovery ----

  discover(server, player) {
    var r = Number(this.set().discover_radius)
    var self = this
    TtlSidePlaces.all().forEach(p => {
      if (p.discover !== true) return
      var stage = `${self.STAGE}seen.${p.id}`
      if (player.stages.has(stage)) return
      var pos = TtlSidePlaces.resolve(server, p, null, true)
      if (!pos || !TtlSidePlaces.near(player, pos, r)) return
      player.stages.add(stage)
      player.tell(Text.aqua(`Discovered: ${p.title}.`))
    })
  },

  // ---- text ----

  statusLines(server, player) {
    var d = this.read(player)
    var keys = Object.keys(d.active)
    var out = [`Side quests: ${keys.length}/${this.set().max_active} carried, ${d.n} done.`]
    var self = this
    keys.forEach(key => {
      var rec = d.active[key]
      var def = self.defOf(rec) || {}
      var line = `- ${rec.title}: `
      if (rec.kind === 'escort') {
        line += rec.st.phase === 'wait' ? `meet ${self.client(def.client).name} at ${TtlSidePlaces.title(def.from)}`
          : `bring ${self.client(def.client).name} to ${TtlSidePlaces.title(def.to)}`
      } else if (rec.kind === 'deliver') {
        line += rec.st.phase === 'pickup' ? `collect it at ${TtlSidePlaces.title(def.pickup)}` : `deliver ${def.parcel} to ${TtlSidePlaces.title(def.to)}`
      } else if (rec.kind === 'travel') {
        line += `reach ${TtlSidePlaces.title(def.to)}`
      } else if (rec.kind === 'fetch') {
        var miss = self.missing(player, def.items)
        line += miss ? `still missing ${miss}` : (def.at ? `bring it to ${TtlSidePlaces.title(def.at)}` : 'ready: /ttl sidequest turnin')
      } else if (rec.kind === 'cull') {
        line += `${rec.st.got}/${def.count} ${String(def.entity).replace(/^[^:]*:/, '').replace(/_/g, ' ')}`
      }
      if (rec.until) line += ` (${Math.max(0, Math.ceil((rec.until - Date.now()) / 60000))} min left)`
      out.push(line + ` [${key}]`)
    })
    return out
  },

  // The jobs offered where the soul stands (a giver place within take_radius).
  offerLines(server, player) {
    var here = TtlSidePlaces.placesNear(server, player, Number(this.set().take_radius)).map(p => String(p.id))
    var d = this.read(player)
    var self = this
    var out = []
    ;(this.conf().quest || []).forEach(q => {
      if (!q.giver || here.indexOf(String(q.giver)) < 0) return
      var def = {}
      for (var k in q) def[k] = q[k]
      def.authored = true
      var why = d.active[q.id] ? 'on it' : self.refusal(server, player, def, String(q.id), true)
      out.push({ id: String(q.id), text: `${q.title}: ${why ? why : 'open'}`, open: !why })
    })
    return out
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(20, Number(TtlSide.set().poll_ticks))
  var ms = every * 50
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      server.getPlayerList().getPlayers().forEach(p => {
        try {
          if (TtlLife.phase(p) !== 'life2') return
          TtlSide.tick(server, p, ms)
          TtlSide.discover(server, p)
        } catch (e) {
          console.error(`[ttl] side: poll of ${p.username} failed: ${e}`)
        }
      })
    } catch (e) {
      console.error(`[ttl] side: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})

// An escort client that dies fails its job at once (the poll also notices a missing client whose chunk is loaded).
EntityEvents.death(event => {
  try {
    var e = event.entity
    if (!TtlSideNpc.hasTag(e, 'ttl.side.client')) return
    var server = e.getServer()
    var id = TtlSideNpc.uuidOf(e)
    server.getPlayerList().getPlayers().forEach(p => {
      var d = TtlSide.read(p)
      Object.keys(d.active).forEach(key => {
        var rec = d.active[key]
        if (rec.kind === 'escort' && rec.st && rec.st.npc === id) {
          var c = TtlSide.client((TtlSide.defOf(rec) || {}).client)
          TtlSide.fail(server, p, key, `${c ? c.name : 'your client'} has fallen`)
        }
      })
    })
  } catch (x) {
    console.error(`[ttl] side: client death handling failed: ${x}`)
  }
})
