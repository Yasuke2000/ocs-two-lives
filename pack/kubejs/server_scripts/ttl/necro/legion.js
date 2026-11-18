// priority: 70
// The necromancer's legion (design/architecture/paths-necro-artificer.md §2.3, §6; WP-N2; owner decisions 18/11/2026).
// Data: design/data/necro.toml → TtlData.necro ([legion], [ash], [knight], [rest]). Commands: necro/legion_commands.js.
// The tomb around a Bone Altar: necro/sanctum.js (TtlSanctum). Costs of the dark road: roads/roads.js (TtlRoads).
//
// A LEGIONNAIRE is one of Tensura's own undead (`tensura:skeleton` / `tensura:zombie`, UndeadHumanoidEntity, verified in
// tensura-neoforge-2.0.1.5) raised at a Bone Altar: PersistenceRequired, BurnInSunlight off ([legion] burn_in_sunlight),
// tags `ttl.legion`, `ttl.legion.<ownerUuid>`, `ttl.lid.<id>` (+ `ttl.knight`), and Tensura's PERMANENT owner set with
// `/tensura edit owner <e> permanent set <player>` (OwnerCommand → IExistence.setPermanentOwner; fallback: the vanilla
// TamableAnimal owner). Naming is Tensura's own (its naming screen, EP cost, IExistence.getName); a named legionnaire
// counts for the army. Raised with 4 bone dust (the grey road, TtlRoads necro.raise grey) or 1 soul ash (the dark road:
// ×1.5 health and attack, TtlRoads necro.raise dark: karma, the Church, renown if seen, the first #story line).
// SLEEPING (dormant) legionnaires are not entities: /ttl necro stow writes the entity's NBT into the record (dormant is
// saved BEFORE the entity is discarded) and /ttl necro rouse summons it again at the altar from that NBT.
// Caps (O-N3): awake per soul by rank [legion] caps (muster_caps while a war muster holds), dormant per soul = the tomb's
// niches (TtlSanctum), server-wide [legion] server_cap awake undead: above it raise/rouse wait in a queue.
// Death Knights (O-N6): rank 3+, max [knight] max by rank, from the gear + 1 soul ash + a CORPSE CREDIT of the soul's own
// kill (a player in an arena or war, a story NPC), or from the gear + 32 bone dust. A fallen knight never rises again.
// PvP (world-state §6.2): a legionnaire's blow on a player is its owner's blow: cancelled unless TtlPvp allows it (WP-W4),
// else unless both stand in an arena, their nations are at war, or both carry the same `ttl.quest.pvp.<id>` stage.
// Outside the canon continent (R11, TtlWorld.onContinent): the dark road costs only the soul's own karma.
// Life 1 never: every act needs the Life 2 stage and refuses the Mortal dimensions.
//
// Storage
//   server  ttl.necro.legions   compound {ownerUuid: JSON {n (name), seen, muster (until), army {n, at}, pts (points paid),
//                               corpses [{u, n, at, how}], rest {day, n}, tiers {tierId: epoch}, last (last result code),
//                               list [{id, kind, road, knight, label, at, st (awake|dormant|fallen), dim, x, y, z, altar,
//                               nbt (dormant), tname (Tensura name), named (epoch), stand, miss, fell}]}}
//                               Kept on the server (not the player) so an offline owner's legion can fall, sleep or be found.
//           ttl.necro.altars    JSON {"dim|x|y|z": {o (owner uuid), n (name), t (placed)}}
//           ttl.necro.queue     JSON [{o, op (raise|rouse), kind, road, label, id, altar, at}]
//           ttl.necro.seq       int, the last legionnaire id
//           ttl.necro.rested    JSON {"dim|x|y|z": epoch} grave markers laid to rest (one a day each)
//           ttl.necro.testcap   int test hook: replaces [legion] server_cap while set
//   player  ttl.ash.victims     JSON {victimUuid: epoch} player kills that paid soul ash (O-N4: once per victim per 24 h)
//           ttl.necro.testrank  int test hook: the soul's necromancer rank while set
//
// PUBLIC API (other packages call these guarded with typeof; `player` is a ServerPlayer)
//   TtlLegion.rank(player)                    0..4 (test hook, TtlNecro.rank of WP-N3, else stages ttl.necro.rank<n>)
//   TtlLegion.ownerOf(entity)                 owner uuid string of a legionnaire ('' if not one); ownerPlayer(server, e)
//   TtlLegion.mayHurt(server, legionnaire, victimPlayer)   {ok, why}: the PvP owner rule
//   TtlLegion.raise(server, player, kind, road, label) · knight(server, player, name, road) · stow/rouse(server, player, which)
//                                             {ok, why, ...}; why is a short code (norank, noaltar, cap, nodust, noash,
//                                             nocorpse, nogear, knightcap, full = queued, ...)
//   TtlLegion.army(server, player, radius)    {n, all}: named (army_named_only) awake legionnaires loaded near the soul
//   TtlLegion.armyOf(server, nationKey, radius)   the army of every online member of a nation (for /ttl nation muster)
//   TtlLegion.onPlayerKill(server, killer, victim, how, test)   soul ash + corpse credit (arenas.js defeat, deaths)
//   TtlLegion.record(server, uuid) · awake(rec) · dormant(rec) · knights(rec) · serverAwake(server) · cap(player, rec)
//   TtlLegion.altarsOf(server, uuid) · nearAltar(server, player) · claimAltar(server, player, dim, x, y, z)
// WP-N3 provides TtlNecro.rank(player) and TtlNecro.addPoints(server, player, n, why); both are optional here.
const TtlLegion = {
  KEY: 'ttl.necro.legions',
  ALTARS: 'ttl.necro.altars',
  QUEUE: 'ttl.necro.queue',
  SEQ: 'ttl.necro.seq',
  RESTED: 'ttl.necro.rested',
  TESTCAP: 'ttl.necro.testcap',
  TESTRANK: 'ttl.necro.testrank',
  VICTIMS: 'ttl.ash.victims',
  DAY_MS: 86400000,
  storages: undefined,
  posClass: undefined,
  warnedAt: {},

  conf() {
    return (TtlData.necro && TtlData.necro.legion) || {}
  },

  part(name) {
    return (TtlData.necro && TtlData.necro[name]) || {}
  },

  num(table, key, fallback) {
    var v = Number(table[key])
    return isNaN(v) ? fallback : v
  },

  uid(player) {
    return TtlLife.uuid(player)
  },

  juuid(text) {
    return Java.loadClass('java.util.UUID').fromString(String(text))
  },

  // ---- records ----------------------------------------------------------------------------------------------------

  record(server, uuid) {
    var raw = ''
    try {
      raw = String(server.persistentData.getCompound(this.KEY).getString(String(uuid)) || '')
    } catch (e) {
      raw = ''
    }
    var r = {}
    try {
      r = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] legion: record of ${uuid} unreadable, starting over: ${e}`)
    }
    r.list = r.list || []
    r.corpses = r.corpses || []
    r.tiers = r.tiers || {}
    r.pts = Number(r.pts || 0)
    return r
  },

  save(server, uuid, r) {
    var data = server.persistentData
    var c = data.getCompound(this.KEY)
    c.putString(String(uuid), JSON.stringify(r))
    data.put(this.KEY, c)
  },

  drop(server, uuid) {
    var data = server.persistentData
    var c = data.getCompound(this.KEY)
    c.remove(String(uuid))
    data.put(this.KEY, c)
  },

  owners(server) {
    var out = []
    var it = server.persistentData.getCompound(this.KEY).getAllKeys().iterator()
    while (it.hasNext()) out.push(String(it.next()))
    return out
  },

  entry(rec, id) {
    for (var i = 0; i < rec.list.length; i++) {
      if (Number(rec.list[i].id) === Number(id)) return rec.list[i]
    }
    return null
  },

  awake(rec) {
    return rec.list.filter(x => x.st === 'awake').length
  },

  dormant(rec) {
    return rec.list.filter(x => x.st === 'dormant').length
  },

  knights(rec) {
    return rec.list.filter(x => x.knight && x.st !== 'fallen').length
  },

  serverAwake(server) {
    var n = 0
    var self = this
    this.owners(server).forEach(u => { n += self.awake(self.record(server, u)) })
    return n
  },

  serverCap(server) {
    var data = server.persistentData
    if (data.contains(this.TESTCAP)) return Number(data.getInt(this.TESTCAP))
    return this.num(this.conf(), 'server_cap', 60)
  },

  nextId(server) {
    var n = Number(server.persistentData.getInt(this.SEQ)) + 1
    server.persistentData.putInt(this.SEQ, n)
    return n
  },

  // ---- rank, caps, points ---------------------------------------------------------------------------------------

  rank(player) {
    var data = player.persistentData
    if (data.contains(this.TESTRANK)) return Number(data.getInt(this.TESTRANK))
    try {
      if (typeof TtlNecro !== 'undefined' && typeof TtlNecro.rank === 'function') return Number(TtlNecro.rank(player)) || 0
    } catch (e) {
      console.error(`[ttl] legion: TtlNecro.rank failed for ${player.username}: ${e}`)
    }
    for (var r = 4; r >= 1; r--) {
      if (player.stages.has(`ttl.necro.rank${r}`)) return r
    }
    return 0
  },

  byRank(list, r) {
    list = list || []
    if (list.length === 0) return 0
    return Number(list[Math.max(0, Math.min(r, list.length - 1))]) || 0
  },

  mustered(rec) {
    return Number(rec.muster || 0) > Date.now()
  },

  cap(player, rec) {
    var c = this.conf()
    return this.byRank(this.mustered(rec) ? c.muster_caps : c.caps, this.rank(player))
  },

  knightCap(player) {
    return this.byRank(this.part('knight').max, this.rank(player))
  },

  // Rank points through WP-N3 (weekly cap there). Remembered in the record so tests and staff can see what was paid.
  points(server, player, key, why) {
    var n = this.num(this.conf().points || {}, key, 0)
    if (n <= 0) return 0
    var rec = this.record(server, this.uid(player))
    rec.pts = Number(rec.pts || 0) + n
    this.save(server, this.uid(player), rec)
    try {
      if (typeof TtlNecro !== 'undefined' && typeof TtlNecro.addPoints === 'function') TtlNecro.addPoints(server, player, n, why || key)
    } catch (e) {
      console.error(`[ttl] legion: TtlNecro.addPoints for ${player.username} failed: ${e}`)
    }
    return n
  },

  // ---- inventory -------------------------------------------------------------------------------------------------

  count(server, player, id) {
    return TtlCmd.run(server, `clear ${player.username} ${id} 0`)
  },

  take(server, player, id, n) {
    return TtlCmd.run(server, `clear ${player.username} ${id} ${n}`)
  },

  // ---- Bone Altars -----------------------------------------------------------------------------------------------

  altarKey(dim, x, y, z) {
    return `${dim}|${Math.floor(x)}|${Math.floor(y)}|${Math.floor(z)}`
  },

  parseKey(key) {
    var p = String(key).split('|')
    return { key: String(key), dim: p[0], x: Number(p[1]), y: Number(p[2]), z: Number(p[3]) }
  },

  altars(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.ALTARS)) || '{}')
    } catch (e) {
      return {}
    }
  },

  saveAltars(server, all) {
    server.persistentData.putString(this.ALTARS, JSON.stringify(all))
  },

  // The soul's altars. An altar whose block is gone (an explosion, a piston, a command: BlockEvents.broken is for players
  // only) is forgotten here, the first time it is looked at while its chunk is loaded.
  altarsOf(server, uuid) {
    var all = this.altars(server)
    var self = this
    return Object.keys(all).filter(k => all[k].o === String(uuid)).map(k => self.parseKey(k)).filter(a => self.standing(server, a))
  },

  standing(server, a) {
    try {
      var level = server.getLevel(a.dim)
      var pos = this.blockPos(a.x, a.y, a.z)
      if (!level || !pos || !level.isLoaded(pos)) return true
      if (String(level.getBlock(a.x, a.y, a.z).id) === 'ttl:bone_altar') return true
    } catch (e) {
      return true
    }
    this.forgetAltar(server, a.key)
    return false
  },

  altarOwner(server, key) {
    var a = this.altars(server)[String(key)]
    return a ? a : null
  },

  // The player's own altar within [legion] altar_reach, nearest first, or null.
  nearAltar(server, player) {
    var reach = this.num(this.conf(), 'altar_reach', 6)
    var dim = TtlLife.dimensionOf(player)
    var best = null
    var bestD = reach * reach + 1
    this.altarsOf(server, this.uid(player)).forEach(a => {
      if (a.dim !== dim) return
      var dx = a.x + 0.5 - player.getX()
      var dy = a.y + 0.5 - player.getY()
      var dz = a.z + 0.5 - player.getZ()
      var d = dx * dx + dy * dy + dz * dz
      if (d < bestD) {
        best = a
        bestD = d
      }
    })
    return best
  },

  // '' when the player may own an altar there, else the reason. Never in a canon domain (TtlDomains, WP-W3).
  altarRefusal(server, player, dim, x, y, z) {
    if (TtlLife.phase(player) !== 'life2') return 'Only a soul in its second life can keep a Bone Altar.'
    if (TtlLife.isMortal(dim)) return 'The dead of the Mortal Realm do not answer.'
    try {
      if (typeof TtlDomains !== 'undefined' && typeof TtlDomains.of === 'function' && TtlDomains.of(server, dim, x, z)) {
        return 'A Bone Altar cannot stand inside the domain of a nation of this world.'
      }
    } catch (e) {
      console.error(`[ttl] legion: domain check for an altar failed: ${e}`)
    }
    var key = this.altarKey(dim, x, y, z)
    var mine = this.altarsOf(server, this.uid(player)).filter(a => a.key !== key)
    var max = this.num(this.conf(), 'altars_per_soul', 3)
    if (mine.length >= max) return `You already keep ${max} Bone Altars. Break one first.`
    return ''
  },

  claimAltar(server, player, dim, x, y, z) {
    var why = this.altarRefusal(server, player, dim, x, y, z)
    if (why) return why
    var all = this.altars(server)
    var key = this.altarKey(dim, x, y, z)
    if (all[key] && all[key].o !== this.uid(player)) return `This altar answers to ${all[key].n}.`
    all[key] = { o: this.uid(player), n: String(player.username), t: Date.now() }
    this.saveAltars(server, all)
    console.info(`[ttl] legion: ${player.username} keeps a Bone Altar at ${key}`)
    return ''
  },

  forgetAltar(server, key) {
    var all = this.altars(server)
    if (!all[key]) return
    delete all[key]
    this.saveAltars(server, all)
    try {
      if (typeof TtlSanctum !== 'undefined') TtlSanctum.forget(server, key)
    } catch (e) {
      console.error(`[ttl] legion: forgetting the tomb at ${key} failed: ${e}`)
    }
    console.info(`[ttl] legion: the Bone Altar at ${key} is gone`)
  },

  // ---- Tensura existence (owner, name) -----------------------------------------------------------------------------

  existence(e) {
    try {
      if (this.storages === undefined) {
        try {
          this.storages = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
        } catch (err) {
          console.warn(`[ttl] legion: TensuraStorages not reachable, Tensura names and owners are not read: ${err}`)
          this.storages = null
        }
      }
      return this.storages ? this.storages.getExistenceFrom(e) : null
    } catch (err) {
      return null
    }
  },

  tname(e) {
    var x = this.existence(e)
    if (!x) return ''
    try {
      var n = x.getName()
      return n ? String(n) : ''
    } catch (err) {
      return ''
    }
  },

  permanentOwner(e) {
    var x = this.existence(e)
    if (!x) return ''
    try {
      var o = x.getPermanentOwner()
      return o ? String(o) : ''
    } catch (err) {
      return ''
    }
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

  ownerOf(e) {
    var tags = this.tagsOf(e)
    if (tags.indexOf('ttl.legion') < 0) return ''
    for (var i = 0; i < tags.length; i++) {
      if (tags[i].indexOf('ttl.legion.') === 0) return tags[i].substring(11)
    }
    return ''
  },

  idOf(e) {
    var tags = this.tagsOf(e)
    for (var i = 0; i < tags.length; i++) {
      if (tags[i].indexOf('ttl.lid.') === 0) return Number(tags[i].substring(8))
    }
    return 0
  },

  onlineByUuid(server, uuid) {
    try {
      return uuid ? server.getPlayerList().getPlayer(this.juuid(uuid)) : null
    } catch (e) {
      return null
    }
  },

  ownerPlayer(server, e) {
    var u = this.ownerOf(e)
    return u ? this.onlineByUuid(server, u) : null
  },

  sel(id) {
    return `@e[tag=ttl.lid.${id},limit=1]`
  },

  // Loaded entities of one owner within `radius` of an entity/player.
  near(owner, around, radius) {
    var tag = `ttl.legion.${owner}`
    var out = []
    try {
      around.level.getEntitiesWithin(around.boundingBox.inflate(radius)).forEach(e => {
        if (!e.isPlayer() && e.getTags().contains(tag)) out.push(e)
      })
    } catch (err) {
      console.error(`[ttl] legion: looking for the legion near ${around.username || 'an entity'} failed: ${err}`)
    }
    return out
  },

  findLoaded(server, dim, id) {
    var level = server.getLevel(dim)
    if (!level) return null
    var tag = `ttl.lid.${id}`
    var found = null
    level.getEntities().forEach(e => {
      if (!found && e.getTags().contains(tag)) found = e
    })
    return found
  },

  blockPos(x, y, z) {
    if (this.posClass === undefined) {
      try {
        this.posClass = Java.loadClass('net.minecraft.core.BlockPos')
      } catch (e) {
        console.error(`[ttl] legion: BlockPos not reachable, lost legionnaires are not detected: ${e}`)
        this.posClass = null
      }
    }
    return this.posClass ? new this.posClass(Math.floor(x), Math.floor(y), Math.floor(z)) : null
  },

  levels(server) {
    var out = []
    var it = server.getAllLevels().iterator()
    while (it.hasNext()) out.push(it.next())
    return out
  },

  // ---- spawning --------------------------------------------------------------------------------------------------

  label(text) {
    return String(text || '').replace(/[^A-Za-z0-9 ,.\-]/g, '').trim().substring(0, 40)
  },

  baseNbt(server, uuid, entry, armed) {
    var c = this.conf()
    var tags = ['ttl.legion', `ttl.legion.${uuid}`, `ttl.lid.${entry.id}`]
    if (entry.knight) tags.push('ttl.knight')
    var parts = ['PersistenceRequired:1b', `BurnInSunlight:${c.burn_in_sunlight ? 1 : 0}b`, `Tags:[${tags.map(t => JSON.stringify(t)).join(',')}]`]
    if (entry.label) parts.push(`CustomName:'${JSON.stringify({ text: entry.label })}'`)
    if (!armed) parts.push('ArmorItems:[{},{},{},{}]', 'HandItems:[{},{}]')
    return `{${parts.join(',')}}`
  },

  // Summons at the altar and finds the entity again by its id tag. Returns the entity or null.
  summonAt(server, altar, type, nbt, id) {
    TtlCmd.run(server, `execute in ${altar.dim} run summon ${type} ${altar.x + 0.5} ${altar.y + 1} ${altar.z + 0.5} ${nbt}`)
    return this.findLoaded(server, altar.dim, id)
  },

  // Tensura's permanent owner (verified: OwnerCommand `permanent set <owner>` → IExistence.setPermanentOwner); the vanilla
  // tame owner as a fallback when the command does not take.
  bind(server, player, e, id) {
    var ok = TtlCmd.run(server, `tensura edit owner ${this.sel(id)} permanent set ${player.username}`) > 0
    if (!ok || this.permanentOwner(e) !== this.uid(player)) {
      try {
        e.setOwnerUUID(this.juuid(this.uid(player)))
        e.setTame(true, false)
        console.warn(`[ttl] legion: #${id} took the vanilla owner (Tensura's permanent owner did not take: ${ok ? 'not stored' : 'command failed'})`)
      } catch (err) {
        console.error(`[ttl] legion: #${id} could not be bound to ${player.username}: ${err}`)
      }
    }
  },

  scale(server, e, id, hp, attack) {
    var sel = this.sel(id)
    var set = (attr, mult) => {
      if (!(mult > 0) || mult === 1) return
      var base = TtlCmd.run(server, `attribute ${sel} ${attr} base get 1000`) / 1000
      if (base > 0) TtlCmd.run(server, `attribute ${sel} ${attr} base set ${Math.round(base * mult * 100) / 100}`)
    }
    set('minecraft:generic.max_health', hp)
    set('minecraft:generic.attack_damage', attack)
    try {
      e.setHealth(e.getMaxHealth())
    } catch (err) {
      // a full heal is cosmetic
    }
  },

  // ---- the dark road --------------------------------------------------------------------------------------------

  // TtlRoads.pay for necro.<act>. Outside the canon continent (R11) only the soul's own karma is paid.
  road(server, player, act, road, pos, dim) {
    if (typeof TtlRoads === 'undefined') return null
    var opts = { system: 'necro', act: act, road: road, pos: pos, dim: dim, reason: `necro ${act} ${road}` }
    var inside = true
    try {
      if (typeof TtlWorld !== 'undefined' && typeof TtlWorld.onContinent === 'function') inside = !!TtlWorld.onContinent(dim, pos.x, pos.z)
    } catch (e) {
      console.warn(`[ttl] legion: continent check failed, the full road is paid: ${e}`)
    }
    if (!inside) {
      var route = TtlRoads.route(`necro.${act}`, road)
      opts.costs = { chaos: route && route.chaos ? Number(route.chaos) : 0, balance: 'none' }
    }
    try {
      return TtlRoads.pay(server, player, opts)
    } catch (e) {
      console.error(`[ttl] legion: the ${road} road of necro.${act} for ${player.username} failed: ${e}`)
      return null
    }
  },

  // ---- checks shared by the acts ----------------------------------------------------------------------------------

  baseRefusal(player) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    if (TtlLife.isMortal(TtlLife.dimensionOf(player))) return 'mortal'
    return ''
  },

  // `altar` given (the queue) skips the "stand at your altar" rule.
  raiseRefusal(server, player, kind, road, altar) {
    var why = this.baseRefusal(player)
    if (why) return why
    var c = this.conf()
    if (!(c.kinds || {})[kind]) return 'kind'
    if (road !== 'dust' && road !== 'ash') return 'road'
    if (this.rank(player) < this.num(c, 'min_rank', 1)) return 'norank'
    if (!altar && !this.nearAltar(server, player)) return 'noaltar'
    var rec = this.record(server, this.uid(player))
    if (this.awake(rec) >= this.cap(player, rec)) return 'cap'
    if (road === 'dust' && this.count(server, player, 'ttl:bone_dust') < this.num(c, 'dust_cost', 4)) return 'nodust'
    if (road === 'ash' && this.count(server, player, 'ttl:soul_ash') < this.num(c, 'ash_cost', 1)) return 'noash'
    if (this.serverAwake(server) >= this.serverCap(server)) return 'full'
    return ''
  },

  why(code) {
    var c = this.conf()
    var k = this.part('knight')
    return {
      life2only: 'Only a soul in its second life can raise the dead.',
      mortal: 'The dead of the Mortal Realm do not answer.',
      kind: 'Raise a skeleton or a zombie.',
      road: 'Raise with dust (bone dust) or ash (soul ash).',
      norank: 'Only a necromancer can bind the dead. The Rite at a Bone Altar makes you one.',
      noaltar: `Stand within ${this.num(c, 'altar_reach', 6)} blocks of one of your Bone Altars.`,
      cap: 'Your legion is as large as your rank allows. Stow some of them to sleep, or grow in rank.',
      nodust: `You need ${this.num(c, 'dust_cost', 4)} bone dust.`,
      noash: `You need ${this.num(c, 'ash_cost', 1)} soul ash.`,
      full: 'The realm holds as many waking dead as it can bear. Your request waits in the queue.',
      queuefull: 'You already have as many requests waiting as the queue allows.',
      knightrank: `Death Knights answer only to a necromancer of rank ${this.num(k, 'rank', 3)}.`,
      knightcap: 'You command as many Death Knights as your rank allows.',
      nogear: `A Death Knight needs a full set of gear: ${(k.gear || []).join(', ')}.`,
      nocorpse: 'A Death Knight of ash needs a corpse you made yourself (a soul defeated in an arena or a war, a fallen NPC).',
      knightdust: `A Death Knight of dust needs ${this.num(k, 'dust_cost', 32)} bone dust.`,
      none: 'There is nobody to wake or put to sleep here.',
      fallen: 'That one has fallen for good. The dead do not rise twice.',
      niches: 'Your tomb has no free niche. Build it larger to keep more of the dead asleep.',
      spawn: 'The dead did not answer (the summon failed). Nothing was spent.',
      nomarker: 'There is no grave here to lay to rest.',
      rested: 'These dead already rest. Come back tomorrow.',
      restcap: 'You have laid enough of the dead to rest today.'
    }[code] || String(code)
  },

  tellWhy(player, code) {
    player.tell(Text.gray(this.why(code)))
  },

  // ---- raise ----------------------------------------------------------------------------------------------------

  // Raise one legionnaire. Returns {ok, why, id, queued}. opts: {altar (key, from the queue)}.
  raise(server, player, kind, road, label, opts) {
    opts = opts || {}
    var res = { ok: false, why: '', id: 0, queued: false }
    var altar = opts.altar ? this.parseKey(opts.altar) : null
    if (altar && (this.altarOwner(server, altar.key) || {}).o !== this.uid(player)) altar = null
    var why = this.raiseRefusal(server, player, kind, road, altar)
    if (why === 'full' && !opts.fromQueue) return this.enqueue(server, player, { op: 'raise', kind: kind, road: road, label: label }, res)
    if (why) {
      res.why = why
      return this.finish(server, player, res)
    }
    altar = altar || this.nearAltar(server, player)
    var c = this.conf()
    var uuid = this.uid(player)
    var rec = this.record(server, uuid)
    var entry = { id: this.nextId(server), kind: kind, road: road, knight: false, label: this.label(label), at: Date.now(), st: 'awake', dim: altar.dim, x: altar.x, y: altar.y + 1, z: altar.z, altar: altar.key }
    var e = this.summonAt(server, altar, c.kinds[kind], this.baseNbt(server, uuid, entry, this.rank(player) >= this.num(c, 'armed_rank', 2)), entry.id)
    if (!e) {
      res.why = 'spawn'
      return this.finish(server, player, res)
    }
    this.take(server, player, road === 'ash' ? 'ttl:soul_ash' : 'ttl:bone_dust', road === 'ash' ? this.num(c, 'ash_cost', 1) : this.num(c, 'dust_cost', 4))
    this.bind(server, player, e, entry.id)
    if (road === 'ash') this.scale(server, e, entry.id, this.num(c, 'ash_mult', 1.5), this.num(c, 'ash_mult', 1.5))
    rec = this.record(server, uuid)
    rec.n = String(player.username)
    rec.seen = Date.now()
    rec.list.push(entry)
    this.save(server, uuid, rec)
    this.road(server, player, 'raise', road === 'ash' ? 'dark' : 'grey', { x: altar.x, y: altar.y, z: altar.z }, altar.dim)
    this.points(server, player, 'raise', 'raised a legionnaire')
    res.ok = true
    res.id = entry.id
    player.tell(Text.darkPurple(`A ${kind} rises from the ${road === 'ash' ? 'ash of a soul' : 'bone dust'} and kneels to you (#${entry.id}). ${this.awake(rec)}/${this.cap(player, rec)} awake.`))
    console.info(`[ttl] legion: ${player.username} raised #${entry.id} ${kind} (${road}) at ${altar.key}`)
    return this.finish(server, player, res)
  },

  finish(server, player, res) {
    try {
      var uuid = this.uid(player)
      var rec = this.record(server, uuid)
      rec.last = res.ok ? (res.queued ? 'queued' : 'ok') : res.why
      this.save(server, uuid, rec)
    } catch (e) {
      console.warn(`[ttl] legion: last result for ${player.username} not stored: ${e}`)
    }
    return res
  },

  // ---- Death Knights ---------------------------------------------------------------------------------------------

  corpses(rec) {
    var days = this.num(this.part('ash'), 'corpse_days', 7)
    var cut = Date.now() - days * this.DAY_MS
    return rec.corpses.filter(c => Number(c.at) >= cut)
  },

  knightRefusal(server, player, road) {
    var why = this.baseRefusal(player)
    if (why) return why
    var k = this.part('knight')
    if (road !== 'dust' && road !== 'ash') return 'road'
    if (this.rank(player) < this.num(k, 'rank', 3)) return 'knightrank'
    if (!this.nearAltar(server, player)) return 'noaltar'
    var rec = this.record(server, this.uid(player))
    if (this.knights(rec) >= this.knightCap(player)) return 'knightcap'
    if (this.awake(rec) >= this.cap(player, rec)) return 'cap'
    var self = this
    if ((k.gear || []).some(id => self.count(server, player, id) < 1)) return 'nogear'
    if (road === 'ash') {
      if (this.count(server, player, 'ttl:soul_ash') < this.num(k, 'ash_cost', 1)) return 'noash'
      if (this.corpses(rec).length < 1) return 'nocorpse'
    } else if (this.count(server, player, 'ttl:bone_dust') < this.num(k, 'dust_cost', 32)) {
      return 'knightdust'
    }
    if (this.serverAwake(server) >= this.serverCap(server)) return 'full'
    return ''
  },

  knight(server, player, name, road) {
    var res = { ok: false, why: '', id: 0, queued: false }
    var why = this.knightRefusal(server, player, road)
    if (why) {
      res.why = why
      return this.finish(server, player, res)
    }
    var k = this.part('knight')
    var c = this.conf()
    var altar = this.nearAltar(server, player)
    var uuid = this.uid(player)
    var title = String(k.title || '{name}, Death Knight').replace('{name}', this.label(name) || 'Nameless')
    var entry = { id: this.nextId(server), kind: String(k.kind || 'skeleton'), road: road, knight: true, label: this.label(title), at: Date.now(), st: 'awake', dim: altar.dim, x: altar.x, y: altar.y + 1, z: altar.z, altar: altar.key }
    var e = this.summonAt(server, altar, c.kinds[entry.kind], this.baseNbt(server, uuid, entry, false), entry.id)
    if (!e) {
      res.why = 'spawn'
      return this.finish(server, player, res)
    }
    var self = this
    var slots = ['armor.head', 'armor.chest', 'armor.legs', 'armor.feet', 'weapon.mainhand']
    ;(k.gear || []).forEach((id, i) => {
      self.take(server, player, id, 1)
      if (slots[i]) TtlCmd.run(server, `item replace entity ${self.sel(entry.id)} ${slots[i]} with ${id}`)
    })
    if (!k.gear_drops) TtlCmd.run(server, `data merge entity ${this.sel(entry.id)} {ArmorDropChances:[0.0f,0.0f,0.0f,0.0f],HandDropChances:[0.0f,0.0f]}`)
    var stats = (road === 'ash' ? k.dark : k.grey) || {}
    if (road === 'ash') {
      this.take(server, player, 'ttl:soul_ash', this.num(k, 'ash_cost', 1))
      var rec0 = this.record(server, uuid)
      var fresh = this.corpses(rec0)
      var used = fresh[0]
      rec0.corpses = rec0.corpses.filter(x => x !== used && Number(x.at) >= Date.now() - this.num(this.part('ash'), 'corpse_days', 7) * this.DAY_MS)
      entry.corpse = used ? String(used.n) : ''
      this.save(server, uuid, rec0)
    } else {
      this.take(server, player, 'ttl:bone_dust', this.num(k, 'dust_cost', 32))
    }
    this.bind(server, player, e, entry.id)
    this.scale(server, e, entry.id, Number(stats.hp || 1), Number(stats.attack || 1))
    if (Number(stats.strength) >= 0) TtlCmd.run(server, `effect give ${this.sel(entry.id)} minecraft:strength infinite ${Number(stats.strength)} true`)
    var rec = this.record(server, uuid)
    rec.n = String(player.username)
    rec.seen = Date.now()
    rec.list.push(entry)
    this.save(server, uuid, rec)
    this.road(server, player, 'knight', road === 'ash' ? 'dark' : 'grey', { x: altar.x, y: altar.y, z: altar.z }, altar.dim)
    this.points(server, player, 'knight', 'raised a Death Knight')
    res.ok = true
    res.id = entry.id
    player.tell(Text.darkPurple(`${title} rises in full armour and waits for your word (#${entry.id}).${entry.corpse ? ` It was ${entry.corpse}.` : ''}`))
    console.info(`[ttl] legion: ${player.username} raised Death Knight #${entry.id} (${road}${entry.corpse ? `, corpse of ${entry.corpse}` : ''})`)
    return this.finish(server, player, res)
  },

  // ---- sleep and waking --------------------------------------------------------------------------------------------

  // The entity's NBT without its place in the world: what rouse summons again.
  sleepNbt(e) {
    var tag = e.getNbt()
    ;['UUID', 'Pos', 'Motion', 'Rotation', 'FallDistance', 'Fire', 'OnGround', 'Air', 'PortalCooldown', 'Brain', 'leash', 'Leash', 'Passengers', 'HurtTime', 'DeathTime', 'HurtByTimestamp', 'AngryAt', 'AngerTime', 'WanderPosX', 'WanderPosY', 'WanderPosZ'].forEach(k => {
      try {
        tag.remove(k)
      } catch (err) {
        // missing keys are fine
      }
    })
    return String(tag)
  },

  niches(server, altar) {
    var cap = this.num(this.conf(), 'dormant_cap', 12)
    var n = this.num((TtlData.necro && TtlData.necro.sanctum) || {}, 'bare_niches', 2)
    try {
      if (typeof TtlSanctum !== 'undefined' && altar) n = TtlSanctum.niches(server, altar.key)
    } catch (e) {
      console.error(`[ttl] legion: tomb niches at ${altar ? altar.key : '?'} unreadable: ${e}`)
    }
    return Math.min(cap, n)
  },

  // Put awake legionnaires near the soul to sleep in its tomb. which = 'all' or an id. {ok, why, n}.
  stow(server, player, which, opts) {
    opts = opts || {}
    var res = { ok: false, why: '', n: 0 }
    var why = opts.sweep ? '' : this.baseRefusal(player)
    var altar = opts.altar || this.nearAltar(server, player)
    if (!why && !altar) why = 'noaltar'
    if (why) {
      res.why = why
      return opts.sweep ? res : this.finish(server, player, res)
    }
    var uuid = opts.uuid || this.uid(player)
    // The offline sweep always finds room: the dead of an absent master wait in the crypt (§6).
    var room = opts.sweep ? this.num(this.conf(), 'dormant_cap', 12) : this.niches(server, altar)
    var self = this
    var list = opts.entities || this.near(uuid, player, this.num(this.conf(), 'stow_radius', 16))
    list.forEach(e => {
      var id = self.idOf(e)
      if (which !== 'all' && Number(which) !== id) return
      var rec = self.record(server, uuid)
      var entry = self.entry(rec, id)
      if (!entry || entry.st !== 'awake') return
      if (self.dormant(rec) >= room) {
        res.why = 'niches'
        return
      }
      entry.nbt = self.sleepNbt(e)
      entry.tname = self.tname(e) || entry.tname || ''
      entry.st = 'dormant'
      entry.altar = altar.key
      entry.slept = Date.now()
      self.save(server, uuid, rec)
      e.discard()
      res.n++
    })
    if (res.n > 0) {
      res.ok = true
      res.why = ''
    } else if (!res.why) {
      res.why = 'none'
    }
    if (!opts.sweep) {
      if (res.n > 0) player.tell(Text.darkPurple(`${res.n} of your dead lie down in the tomb's niches to sleep.`))
      this.finish(server, player, res)
      this.drain(server)
    }
    return res
  },

  rouseRefusal(server, player, entry, altar) {
    var why = this.baseRefusal(player)
    if (why) return why
    if (!altar) return 'noaltar'
    if (!entry) return 'none'
    if (entry.st === 'fallen') return 'fallen'
    if (entry.st !== 'dormant' || !entry.nbt) return 'none'
    var rec = this.record(server, this.uid(player))
    if (this.awake(rec) >= this.cap(player, rec)) return 'cap'
    if (this.serverAwake(server) >= this.serverCap(server)) return 'full'
    return ''
  },

  // Wake sleeping legionnaires at the altar. which = 'all' or an id. {ok, why, n}.
  rouse(server, player, which, opts) {
    opts = opts || {}
    var res = { ok: false, why: '', n: 0, queued: false }
    var altar = opts.altar ? this.parseKey(opts.altar) : this.nearAltar(server, player)
    if (altar && (this.altarOwner(server, altar.key) || {}).o !== this.uid(player)) altar = null
    var uuid = this.uid(player)
    var ids = this.record(server, uuid).list.filter(x => (which === 'all' ? x.st === 'dormant' : Number(x.id) === Number(which))).map(x => x.id)
    if (ids.length === 0) {
      res.why = which === 'all' ? 'none' : (this.baseRefusal(player) || 'none')
      return this.finish(server, player, res)
    }
    var c = this.conf()
    for (var i = 0; i < ids.length; i++) {
      var rec = this.record(server, uuid)
      var entry = this.entry(rec, ids[i])
      var why = this.rouseRefusal(server, player, entry, altar)
      if (why === 'full' && !opts.fromQueue) {
        this.enqueue(server, player, { op: 'rouse', id: entry.id }, res)
        continue
      }
      if (why) {
        res.why = why
        break
      }
      var e = this.summonAt(server, altar, c.kinds[entry.kind] || c.kinds.skeleton, entry.nbt, entry.id)
      if (!e) {
        res.why = 'spawn'
        break
      }
      this.bind(server, player, e, entry.id)
      if (entry.tname && !this.tname(e)) TtlCmd.run(server, `tensura edit owner ${this.sel(entry.id)} name set ${entry.tname}`)
      rec = this.record(server, uuid)
      entry = this.entry(rec, ids[i])
      entry.st = 'awake'
      entry.nbt = ''
      entry.dim = altar.dim
      entry.x = altar.x
      entry.y = altar.y + 1
      entry.z = altar.z
      entry.miss = 0
      this.save(server, uuid, rec)
      res.n++
    }
    if (res.n > 0) {
      res.ok = true
      if (res.why === 'full') res.why = ''
      player.tell(Text.darkPurple(`${res.n} of your dead wake and climb out of their niches.`))
    }
    if (res.queued) res.ok = true
    return this.finish(server, player, res)
  },

  // Teleport the soul's loaded legionnaires within [legion] recall_radius to it.
  recall(server, player) {
    var why = this.baseRefusal(player)
    if (why) return { ok: false, why: why, n: 0 }
    var list = this.near(this.uid(player), player, this.num(this.conf(), 'recall_radius', 64))
    list.forEach(e => {
      try {
        e.teleportTo(player.getX(), player.getY(), player.getZ())
      } catch (err) {
        console.warn(`[ttl] legion: recall of #${TtlLegion.idOf(e)} failed: ${err}`)
      }
    })
    return { ok: list.length > 0, why: list.length > 0 ? '' : 'none', n: list.length }
  },

  // Tomb guards: NoAI on (stand) or off. which = 'all' or an id; only loaded ones near the soul.
  stand(server, player, which, on) {
    var why = this.baseRefusal(player)
    if (why) return { ok: false, why: why, n: 0 }
    var uuid = this.uid(player)
    var n = 0
    var self = this
    this.near(uuid, player, this.num(this.conf(), 'stow_radius', 16)).forEach(e => {
      var id = self.idOf(e)
      if (which !== 'all' && Number(which) !== id) return
      try {
        e.setNoAi(!!on)
        var rec = self.record(server, uuid)
        var entry = self.entry(rec, id)
        if (entry) {
          entry.stand = !!on
          self.save(server, uuid, rec)
        }
        n++
      } catch (err) {
        console.warn(`[ttl] legion: stand of #${id} failed: ${err}`)
      }
    })
    return { ok: n > 0, why: n > 0 ? '' : 'none', n: n }
  },

  // ---- the queue (server cap) ----------------------------------------------------------------------------------------

  queue(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.QUEUE)) || '[]')
    } catch (e) {
      return []
    }
  },

  saveQueue(server, q) {
    server.persistentData.putString(this.QUEUE, JSON.stringify(q))
  },

  enqueue(server, player, job, res) {
    var uuid = this.uid(player)
    var q = this.queue(server)
    var mine = q.filter(j => j.o === uuid).length
    if (mine >= this.num(this.conf(), 'queue_per_soul', 3)) {
      res.why = 'queuefull'
      return this.finish(server, player, res)
    }
    var altar = this.nearAltar(server, player)
    job.o = uuid
    job.altar = altar ? altar.key : ''
    job.at = Date.now()
    q.push(job)
    this.saveQueue(server, q)
    res.ok = true
    res.queued = true
    res.why = 'full'
    player.tell(Text.gray(`The realm holds ${this.serverAwake(server)} waking dead, its limit. You are number ${q.length} in the queue: the dead rise as soon as others sleep.`))
    console.info(`[ttl] legion: ${player.username} queued ${job.op} (${q.length} waiting)`)
    return this.finish(server, player, res)
  },

  // Run queued jobs while the server has room (owners must be online; a job that cannot run any more is dropped).
  drain(server) {
    var q = this.queue(server)
    if (q.length === 0) return
    var keep = []
    var self = this
    q.forEach(job => {
      if (self.serverAwake(server) >= self.serverCap(server)) {
        keep.push(job)
        return
      }
      var p = self.onlineByUuid(server, job.o)
      if (!p) {
        keep.push(job)
        return
      }
      var r = job.op === 'raise'
        ? self.raise(server, p, job.kind, job.road, job.label, { altar: job.altar, fromQueue: true })
        : self.rouse(server, p, job.id, { altar: job.altar, fromQueue: true })
      if (!r.ok && r.why === 'full') {
        keep.push(job)
      } else if (!r.ok) {
        p.tell(Text.gray(`Your waiting ${job.op} could not happen: ${self.why(r.why)}`))
      }
    })
    this.saveQueue(server, keep)
  },

  // ---- the army (world-state §6.5) ---------------------------------------------------------------------------------

  army(server, player, radius) {
    var c = this.conf()
    var r = Number(radius || c.muster_radius || 32)
    var named = c.army_named_only !== false
    var all = this.near(this.uid(player), player, r)
    var self = this
    var n = all.filter(e => !named || self.tname(e) !== '').length
    return { n: n, all: all.length }
  },

  armyOf(server, key, radius) {
    var total = 0
    var self = this
    try {
      if (typeof TtlNations === 'undefined') return 0
      TtlNations.membersOf(key).forEach(u => {
        var p = self.onlineByUuid(server, String(u))
        if (p) total += self.army(server, p, radius).n
      })
    } catch (e) {
      console.error(`[ttl] legion: the army of nation ${key} could not be counted: ${e}`)
    }
    return total
  },

  // A nation at war (or with a declaration pending) may muster: the war cap holds [legion] muster_hours.
  muster(server, player, force) {
    var why = this.baseRefusal(player)
    if (why) return { ok: false, why: why }
    var uuid = this.uid(player)
    var war = !!force
    try {
      if (!war && typeof TtlNations !== 'undefined') {
        var n = TtlNations.of(server, player)
        war = !!(n && (n.rec.wars || []).length > 0)
      }
    } catch (e) {
      console.error(`[ttl] legion: nation lookup for the muster of ${player.username} failed: ${e}`)
    }
    var army = this.army(server, player)
    var rec = this.record(server, uuid)
    rec.army = { n: army.n, at: Date.now() }
    if (war) rec.muster = Date.now() + this.num(this.conf(), 'muster_hours', 24) * 3600000
    this.save(server, uuid, rec)
    return { ok: true, why: war ? '' : 'nowar', army: army.n, war: war }
  },

  // ---- PvP: the owner's blow (world-state §6.2) ------------------------------------------------------------------

  sharedQuestPvp(a, b) {
    try {
      var mine = []
      a.stages.getAll().forEach(s => {
        if (String(s).indexOf('ttl.quest.pvp.') === 0) mine.push(String(s))
      })
      for (var i = 0; i < mine.length; i++) {
        if (b.stages.has(mine[i])) return true
      }
    } catch (e) {
      // no stages readable: no quest window
    }
    return false
  },

  inArena(server, p) {
    try {
      return typeof TtlArenas !== 'undefined' && TtlArenas.arenaAt(TtlLife.dimensionOf(p), p.getX(), p.getY(), p.getZ()) !== null
    } catch (e) {
      return false
    }
  },

  // May a player's legion hurt `victim`? Same scope as a player's own blow: arenas, wars, PvP quests.
  pvp(server, owner, victim) {
    if (!victim || !victim.isPlayer()) return { ok: true, why: 'not a player' }
    if (owner && this.uid(owner) === this.uid(victim)) return { ok: false, why: 'own master' }
    if (TtlLife.phase(victim) !== 'life2') return { ok: false, why: 'not in Life 2' }
    try {
      if (owner && typeof TtlPvp !== 'undefined' && typeof TtlPvp.allowed === 'function') {
        var v = TtlPvp.allowed(server, owner, victim)
        var ok = v && typeof v === 'object' ? !!v.ok : !!v
        return { ok: ok, why: ok ? 'pvp rules' : `pvp rules: ${v && v.why ? v.why : 'refused'}` }
      }
    } catch (e) {
      console.error(`[ttl] legion: TtlPvp.allowed failed, using the legion's own scope: ${e}`)
    }
    if (this.inArena(server, victim) && (!owner || this.inArena(server, owner))) return { ok: true, why: 'arena' }
    if (!owner) return { ok: false, why: 'master away' }
    try {
      if (typeof TtlNations !== 'undefined') {
        var a = TtlNations.of(server, owner)
        var b = TtlNations.of(server, victim)
        if (a && b && TtlNations.atWar(server, a.key, b.key)) return { ok: true, why: 'war' }
      }
    } catch (e) {
      console.error(`[ttl] legion: war check failed: ${e}`)
    }
    if (this.sharedQuestPvp(owner, victim)) return { ok: true, why: 'quest' }
    return { ok: false, why: 'outside arenas, wars and quests' }
  },

  mayHurt(server, e, victim) {
    var owner = this.ownerPlayer(server, e)
    var v = this.pvp(server, owner, victim)
    if (!v.ok) {
      try {
        e.setTarget(null)
      } catch (err) {
        // the next blow is cancelled as well
      }
      if (owner) {
        var key = this.uid(owner)
        var now = Date.now()
        if (!this.warnedAt[key] || now - this.warnedAt[key] > 60000) {
          this.warnedAt[key] = now
          owner.tell(Text.gray('Your dead will not strike a soul outside an arena, a war or a quest that allows it.'))
        }
      }
    }
    return v
  },

  // ---- soul ash, bone dust, corpses (O-N4, O-N6) ------------------------------------------------------------------

  isNecro(player) {
    return !!player && TtlLife.phase(player) === 'life2' && this.rank(player) >= this.num(this.conf(), 'min_rank', 1)
  },

  // The necromancer behind a kill: the player, or the owner of the legionnaire that struck.
  killerOf(server, entity) {
    if (!entity) return null
    try {
      if (entity.isPlayer()) return entity
    } catch (e) {
      return null
    }
    return this.ownerPlayer(server, entity)
  },

  cursed(victim) {
    var want = String(this.part('ash').curse_effect || 'tensura:curse')
    try {
      var it = victim.getActiveEffects().iterator()
      while (it.hasNext()) {
        if (String(it.next().getEffect().getRegisteredName()) === want) return true
      }
    } catch (e) {
      return false
    }
    return false
  },

  fromSpawner(victim) {
    try {
      var t = String(victim.getSpawnType())
      return t === 'SPAWNER' || t === 'TRIAL_SPAWNER'
    } catch (e) {
      return false
    }
  },

  lootGet(ctx, names) {
    for (var i = 0; i < names.length; i++) {
      try {
        var v = ctx[names[i]]
        if (typeof v === 'function') v = v.call(ctx)
        if (v) return v
      } catch (e) {
        // the next accessor
      }
    }
    return null
  },

  // A LootJS action for an ash or dust entity: a necromancer's kill adds the reagent to the drops.
  onLoot(ctx, loot, kind) {
    var victim = this.lootGet(ctx, ['getEntity', 'entity'])
    if (!victim || victim.isPlayer()) return
    if (this.tagsOf(victim).indexOf('ttl.legion') >= 0) return
    if (this.fromSpawner(victim)) return
    var server = this.lootGet(ctx, ['getServer', 'server']) || victim.getServer()
    var killer = this.lootGet(ctx, ['getKillerPlayer', 'killerPlayer'])
    if (!killer) killer = this.killerOf(server, this.lootGet(ctx, ['getAttackingEntity', 'attackingEntity']))
    if (!this.isNecro(killer)) return
    var a = this.part('ash')
    if (kind === 'ash') {
      var chance = this.num(a, 'ash_chance', 0.25) * (this.cursed(victim) ? this.num(a, 'curse_mult', 2) : 1)
      if (Math.random() < chance) loot.addItem(Item.of('ttl:soul_ash', 1))
    } else if (Math.random() < this.num(a, 'dust_chance', 0.5)) {
      loot.addItem(Item.of('ttl:bone_dust', Math.max(1, this.num(a, 'dust_count', 2))))
    }
  },

  victims(player) {
    try {
      return JSON.parse(String(player.persistentData.getString(this.VICTIMS)) || '{}')
    } catch (e) {
      return {}
    }
  },

  // A soul defeated by a necromancer (or its legion). how: arena | war | npc | death. test = the O-N4 scope and the bot
  // rule are skipped (the test hook). Returns '' or why nothing was paid.
  onPlayerKill(server, killer, victim, how, test) {
    killer = this.killerOf(server, killer)
    if (!this.isNecro(killer)) return 'not a necromancer'
    var a = this.part('ash')
    var vid = victim.isPlayer() ? this.uid(victim) : `npc:${String(victim.type)}`
    var vname = victim.isPlayer() ? String(victim.username) : String(victim.getName().getString())
    if (victim.isPlayer()) {
      if (vid === this.uid(killer)) return 'self'
      if (!test && typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(vname)) return 'test bot'
      if (!test) {
        var scope = (a.player_scope || ['arena', 'war']).map(String)
        var where = how
        if (how === 'death') {
          where = this.inArena(server, victim) ? 'arena' : ''
          try {
            if (!where && typeof TtlNations !== 'undefined') {
              var na = TtlNations.of(server, killer)
              var nb = TtlNations.of(server, victim)
              if (na && nb && TtlNations.atWar(server, na.key, nb.key)) where = 'war'
            }
          } catch (e) {
            console.error(`[ttl] legion: war check for soul ash failed: ${e}`)
          }
        }
        if (scope.indexOf(where) < 0) return 'outside arenas and wars'
      }
      var seen = this.victims(killer)
      var cut = Date.now() - this.num(a, 'victim_hours', 24) * 3600000
      Object.keys(seen).forEach(k => { if (Number(seen[k]) < cut) delete seen[k] })
      if (seen[vid]) return 'already today'
      seen[vid] = Date.now()
      killer.persistentData.putString(this.VICTIMS, JSON.stringify(seen))
      killer.give(Item.of('ttl:soul_ash', 1))
    }
    var uuid = this.uid(killer)
    var rec = this.record(server, uuid)
    rec.corpses = this.corpses(rec)
    rec.corpses.push({ u: vid, n: vname, at: Date.now(), how: how })
    while (rec.corpses.length > this.num(a, 'corpse_max', 3)) rec.corpses.shift()
    this.save(server, uuid, rec)
    killer.tell(Text.darkPurple(`${vname}'s corpse is yours to raise${victim.isPlayer() ? ', and a soul ash with it' : ''}.`))
    console.info(`[ttl] legion: ${killer.username} took the corpse of ${vname} (${how}${test ? ', test' : ''})`)
    return ''
  },

  // ---- falling, the sweep ----------------------------------------------------------------------------------------

  fallen(server, e, why) {
    var uuid = this.ownerOf(e)
    var id = this.idOf(e)
    if (!uuid || !id) return
    var rec = this.record(server, uuid)
    var entry = this.entry(rec, id)
    if (!entry || entry.st === 'fallen') return
    entry.st = 'fallen'
    entry.fell = Date.now()
    entry.nbt = ''
    // Only knights are remembered once fallen (never re-raised, O-N6); plain legionnaires leave the list.
    if (!entry.knight) rec.list = rec.list.filter(x => x !== entry)
    this.save(server, uuid, rec)
    var owner = this.onlineByUuid(server, uuid)
    if (owner) owner.tell(Text.gray(`${entry.label || `Your ${entry.kind}`} (#${id}) has fallen${entry.knight ? ' for good' : ''}.`))
    console.info(`[ttl] legion: #${id} of ${rec.n || uuid} fell (${why})`)
  },

  // Positions and Tensura names of loaded legionnaires, owners away too long (stow into the record), lost ones.
  sweep(server) {
    var c = this.conf()
    var now = Date.now()
    var away = this.num(c, 'offline_days', 7) * this.DAY_MS
    var found = {}
    var self = this
    this.levels(server).forEach(level => {
      var dim = String(level.dimension)
      level.getEntities().forEach(e => {
        try {
          if (e.isPlayer() || !e.getTags().contains('ttl.legion')) return
          var uuid = self.ownerOf(e)
          var id = self.idOf(e)
          var rec = self.record(server, uuid)
          var entry = self.entry(rec, id)
          if (!entry || entry.st !== 'awake') {
            // an entity whose record says it sleeps or is gone (a dupe or a wiped record): it is not ours any more
            console.warn(`[ttl] legion: #${id} of ${uuid} has no awake record, removed`)
            e.discard()
            return
          }
          found[`${uuid}#${id}`] = true
          var owner = self.onlineByUuid(server, uuid)
          if (owner) rec.seen = now
          entry.dim = dim
          entry.x = Math.floor(e.getX())
          entry.y = Math.floor(e.getY())
          entry.z = Math.floor(e.getZ())
          entry.miss = 0
          var tn = self.tname(e)
          if (tn) entry.tname = tn
          self.save(server, uuid, rec)
          if (tn && !entry.named && owner) {
            entry.named = now
            self.save(server, uuid, rec)
            self.points(server, owner, 'named', `named ${tn}`)
          }
          if (!owner && rec.seen && now - Number(rec.seen) > away) {
            var altars = self.altarsOf(server, uuid)
            self.stow(server, null, id, { sweep: true, uuid: uuid, altar: altars[0] || { key: '', dim: dim, x: 0, y: 0, z: 0 }, entities: [e] })
          }
        } catch (err) {
          console.error(`[ttl] legion: sweep of an entity failed: ${err}`)
        }
      })
    })
    var lost = this.num(c, 'lost_sweeps', 2)
    this.owners(server).forEach(uuid => {
      var rec = self.record(server, uuid)
      var changed = false
      rec.list.forEach(entry => {
        if (entry.st !== 'awake' || found[`${uuid}#${entry.id}`]) return
        var level = server.getLevel(entry.dim)
        var loaded = false
        try {
          var pos = self.blockPos(entry.x, entry.y, entry.z)
          loaded = !!level && !!pos && level.isLoaded(pos)
        } catch (err) {
          loaded = false
        }
        if (!loaded) return
        entry.miss = Number(entry.miss || 0) + 1
        changed = true
      })
      if (changed) self.save(server, uuid, rec)
      rec.list.filter(x => x.st === 'awake' && Number(x.miss || 0) >= lost).forEach(entry => {
        self.fallenRecord(server, uuid, entry.id, 'lost: its chunk is loaded and it is not there')
      })
    })
  },

  fallenRecord(server, uuid, id, why) {
    var rec = this.record(server, uuid)
    var entry = this.entry(rec, id)
    if (!entry || entry.st === 'fallen') return
    entry.st = 'fallen'
    entry.fell = Date.now()
    if (!entry.knight) rec.list = rec.list.filter(x => x !== entry)
    this.save(server, uuid, rec)
    console.info(`[ttl] legion: #${id} of ${rec.n || uuid} fell (${why})`)
  },

  // ---- the Keeper's road: lay the dead to rest (§2.6) -------------------------------------------------------------

  markerNear(player) {
    var r = this.num(this.part('rest'), 'radius', 3)
    var x0 = Math.floor(player.getX())
    var y0 = Math.floor(player.getY())
    var z0 = Math.floor(player.getZ())
    var level = player.level
    for (var dx = -r; dx <= r; dx++) {
      for (var dy = -r; dy <= r; dy++) {
        for (var dz = -r; dz <= r; dz++) {
          var b = level.getBlock(x0 + dx, y0 + dy, z0 + dz)
          if (String(b.id) === 'ttl:grave_marker') return { x: x0 + dx, y: y0 + dy, z: z0 + dz }
        }
      }
    }
    return null
  },

  restRefusal(server, player) {
    var why = this.baseRefusal(player)
    if (why) return why
    var m = this.markerNear(player)
    if (!m) return 'nomarker'
    var key = this.altarKey(TtlLife.dimensionOf(player), m.x, m.y, m.z)
    var rested = this.rested(server)
    if (rested[key] && Date.now() - Number(rested[key]) < this.num(this.part('rest'), 'marker_hours', 24) * 3600000) return 'rested'
    var rec = this.record(server, this.uid(player))
    var day = Math.floor(Date.now() / this.DAY_MS)
    if (rec.rest && rec.rest.day === day && rec.rest.n >= this.num(this.part('rest'), 'per_day', 3)) return 'restcap'
    return ''
  },

  rested(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.RESTED)) || '{}')
    } catch (e) {
      return {}
    }
  },

  rest(server, player) {
    var res = { ok: false, why: '' }
    var why = this.restRefusal(server, player)
    if (why) {
      res.why = why
      return this.finish(server, player, res)
    }
    var m = this.markerNear(player)
    var dim = TtlLife.dimensionOf(player)
    var rested = this.rested(server)
    var cut = Date.now() - this.num(this.part('rest'), 'marker_hours', 24) * 3600000
    Object.keys(rested).forEach(k => { if (Number(rested[k]) < cut) delete rested[k] })
    rested[this.altarKey(dim, m.x, m.y, m.z)] = Date.now()
    server.persistentData.putString(this.RESTED, JSON.stringify(rested))
    var uuid = this.uid(player)
    var rec = this.record(server, uuid)
    var day = Math.floor(Date.now() / this.DAY_MS)
    if (!rec.rest || rec.rest.day !== day) rec.rest = { day: day, n: 0 }
    rec.rest.n++
    this.save(server, uuid, rec)
    this.road(server, player, 'rest', 'good', m, dim)
    if (this.isNecro(player)) this.points(server, player, 'rest', 'laid the dead to rest')
    TtlCmd.run(server, `execute in ${dim} run particle minecraft:soul ${m.x + 0.5} ${m.y + 1} ${m.z + 0.5} 0.3 0.6 0.3 0.02 20`)
    player.tell(Text.aqua('The dead under this grave are quiet now.'))
    res.ok = true
    return this.finish(server, player, res)
  },

  // ---- the altar menu ----------------------------------------------------------------------------------------------

  menu(server, player, key) {
    var a = this.altarOwner(server, key)
    if (a && a.o !== this.uid(player)) {
      player.tell(Text.gray(`This Bone Altar answers to ${a.n}.`))
      return
    }
    if (!a) {
      var p = this.parseKey(key)
      var why = this.claimAltar(server, player, p.dim, p.x, p.y, p.z)
      if (why) {
        player.tell(Text.gray(why))
        return
      }
    }
    var rec = this.record(server, this.uid(player))
    var rank = this.rank(player)
    var head = rank < this.num(this.conf(), 'min_rank', 1)
      ? 'The Bone Altar is cold. Only a necromancer (the Rite) can bind the dead here. /ttl guide paths'
      : `Your legion: ${this.awake(rec)}/${this.cap(player, rec)} awake, ${this.dormant(rec)} asleep. Bone dust is the honest road; soul ash is stronger, and the Church takes note.`
    var items = [
      { label: 'Raise skeleton (dust)', command: '/ttl necro raise skeleton dust', color: 'gray', hover: `${this.num(this.conf(), 'dust_cost', 4)} bone dust` },
      { label: 'Raise zombie (dust)', command: '/ttl necro raise zombie dust', color: 'gray', hover: `${this.num(this.conf(), 'dust_cost', 4)} bone dust` },
      { label: 'Raise (ash)', command: '/ttl necro raise skeleton ash', color: 'dark_red', hover: 'Soul ash: x1.5 stronger. The dark road: karma, the Church, witnesses.' },
      { label: 'Sleep', command: '/ttl necro stow', color: 'dark_purple', hover: 'Put the legion near you to sleep in the tomb' },
      { label: 'Wake', command: '/ttl necro rouse', color: 'dark_purple', hover: 'Wake every sleeping legionnaire' },
      { label: 'Legion', command: '/ttl necro legion', color: 'aqua', hover: 'List your legion' },
      { label: 'Tomb', command: '/ttl necro sanctum', color: 'aqua', hover: 'What your tomb is, and what it needs to grow' }
    ]
    try {
      TtlCorridor.buttons(server, player.username, head, items)
    } catch (e) {
      player.tell(Text.gray(head))
      player.tell(Text.gray('/ttl necro raise skeleton|zombie dust|ash · stow · rouse · legion · sanctum'))
    }
  },

  lines(server, player) {
    var rec = this.record(server, this.uid(player))
    var out = [`Legion of ${player.username}: rank ${this.rank(player)}, ${this.awake(rec)}/${this.cap(player, rec)} awake${this.mustered(rec) ? ' (mustered)' : ''}, ${this.dormant(rec)} asleep, Death Knights ${this.knights(rec)}/${this.knightCap(player)}, corpses ${this.corpses(rec).length}`]
    rec.list.forEach(x => {
      var name = x.tname || x.label || x.kind
      out.push(`#${x.id} ${name}${x.knight ? ' (Death Knight)' : ''} ${x.road}: ${x.st}${x.st === 'awake' ? ` near ${x.x} ${x.y} ${x.z}` : ''}${x.stand ? ', standing guard' : ''}`)
    })
    if (rec.list.length === 0) out.push('No dead answer to you yet.')
    return out
  }
}

// ---- events --------------------------------------------------------------------------------------------------------

// The Bone Altar: placing claims it (never in a canon domain, at most [legion] altars_per_soul), right-click opens the
// menu, breaking forgets it and its tomb.
BlockEvents.placed('ttl:bone_altar', event => {
  var refuse = ''
  try {
    var p = event.entity
    if (p && p.isPlayer()) {
      var b = event.block
      refuse = TtlLegion.claimAltar(p.server, p, String(event.level.dimension), b.x, b.y, b.z)
      if (refuse) p.tell(Text.gray(refuse))
      else p.tell(Text.darkPurple('The Bone Altar takes your name. Build your tomb around it; right-click it to raise the dead.'))
    }
  } catch (e) {
    console.error(`[ttl] legion: altar placement failed: ${e}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
  if (refuse) event.cancel()
})

BlockEvents.broken('ttl:bone_altar', event => {
  try {
    var b = event.block
    TtlLegion.forgetAltar(event.level.server, TtlLegion.altarKey(String(event.level.dimension), b.x, b.y, b.z))
  } catch (e) {
    console.error(`[ttl] legion: altar break failed: ${e}`)
  }
})

BlockEvents.rightClicked('ttl:bone_altar', event => {
  try {
    var player = event.player
    if (!player || String(event.hand) !== 'MAIN_HAND') return
    var b = event.block
    TtlLegion.menu(player.server, player, TtlLegion.altarKey(String(event.level.dimension), b.x, b.y, b.z))
  } catch (e) {
    console.error(`[ttl] legion: altar menu failed: ${e}`)
  }
})

// The PvP owner rule: a legionnaire's blow on a player is cancelled outside arenas, wars and PvP quests.
EntityEvents.beforeHurt(event => {
  var cancel = false
  try {
    var victim = event.entity
    if (victim.isPlayer()) {
      var a = event.source.actual
      if (a && !a.isPlayer() && a.getTags().contains('ttl.legion')) cancel = !TtlLegion.mayHurt(victim.server, a, victim).ok
    }
  } catch (e) {
    console.error(`[ttl] legion: PvP check failed: ${e}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
  if (cancel) event.cancel()
})

// Soul ash from a soul killed in a war or an arena's lethal blow that got through (arena defeats come from arenas.js),
// corpses of story NPCs, and fallen legionnaires (also caught by the loot hook and the sweep: mob deaths are unreliable).
EntityEvents.death(event => {
  try {
    var victim = event.entity
    var server = event.server
    var killer = event.source.actual
    if (victim.isPlayer()) {
      if (killer && TtlLife.phase(victim) === 'life2') TtlLegion.onPlayerKill(server, killer, victim, 'death', false)
      return
    }
    var tags = TtlLegion.tagsOf(victim)
    if (tags.indexOf('ttl.legion') >= 0) {
      TtlLegion.fallen(server, victim, 'death')
      return
    }
    if (killer && tags.indexOf(String(TtlLegion.part('ash').npc_tag || 'ttl.npc')) >= 0) TtlLegion.onPlayerKill(server, killer, victim, 'npc', false)
  } catch (e) {
    console.error(`[ttl] legion: death check failed: ${e}`)
  }
})

PlayerEvents.loggedIn(event => {
  try {
    var p = event.player
    var server = event.server
    var uuid = TtlLegion.uid(p)
    if (TtlLegion.owners(server).indexOf(uuid) < 0) return
    var rec = TtlLegion.record(server, uuid)
    rec.seen = Date.now()
    rec.n = String(p.username)
    TtlLegion.save(server, uuid, rec)
  } catch (e) {
    console.error(`[ttl] legion: login stamp failed: ${e}`)
  }
})

PlayerEvents.loggedOut(event => {
  try {
    var p = event.player
    var server = event.server
    var uuid = TtlLegion.uid(p)
    if (TtlLegion.owners(server).indexOf(uuid) < 0) return
    var rec = TtlLegion.record(server, uuid)
    rec.seen = Date.now()
    TtlLegion.save(server, uuid, rec)
  } catch (e) {
    console.error(`[ttl] legion: logout stamp failed: ${e}`)
  }
})

// The queue every [legion] loop_seconds, the sweep every sweep_minutes. Reload-safe: a stamp stops an older loop.
ServerEvents.loaded(event => {
  var server = event.server
  var stamp = Date.now()
  server.persistentData.putLong('ttl.necro.loop', stamp)
  var last = Date.now()
  var loop = () => server.scheduleInTicks(Math.max(1, TtlLegion.num(TtlLegion.conf(), 'loop_seconds', 10)) * 20, () => {
    if (Number(server.persistentData.getLong('ttl.necro.loop')) !== stamp) return
    try {
      TtlLegion.drain(server)
      if (Date.now() - last >= TtlLegion.num(TtlLegion.conf(), 'sweep_minutes', 5) * 60000) {
        last = Date.now()
        TtlLegion.sweep(server)
      }
    } catch (e) {
      console.error(`[ttl] legion: loop failed: ${e}`)
    }
    loop()
  })
  loop()
})

// Soul ash and bone dust as drops of a necromancer's kills (LootJS 3.7.0, like bosses/loot.js), and a fallen legionnaire
// when its loot is rolled. Each spec of necro.toml [ash] is its own modifier; a spec LootJS refuses is logged and skipped.
try {
  LootJS.modifiers(event => {
    var a = TtlLegion.part('ash')
    var add = (spec, kind) => {
      try {
        event.addEntityModifier(String(spec)).customAction((ctx, loot) => {
          try {
            TtlLegion.onLoot(ctx, loot, kind)
          } catch (e) {
            console.error(`[ttl] legion: ${kind} drop failed: ${e}`)
          }
        })
      } catch (e) {
        console.error(`[ttl] legion: ${kind} drops for ${spec} not registered: ${e}`)
      }
    }
    ;(a.ash_entities || []).forEach(s => add(s, 'ash'))
    ;(a.dust_entities || []).forEach(s => add(s, 'dust'))
    Object.keys(TtlLegion.conf().kinds || {}).forEach(k => {
      try {
        event.addEntityModifier(String(TtlLegion.conf().kinds[k])).customAction((ctx, loot) => {
          try {
            var e = TtlLegion.lootGet(ctx, ['getEntity', 'entity'])
            if (e && e.getTags().contains('ttl.legion')) TtlLegion.fallen(e.getServer(), e, 'loot')
          } catch (err) {
            console.error(`[ttl] legion: fallen check from loot failed: ${err}`)
          }
        })
      } catch (e) {
        console.error(`[ttl] legion: fallen hook for ${k} not registered: ${e}`)
      }
    })
  })
  console.info('[ttl] legion: soul ash and bone dust drops registered')
} catch (e) {
  console.error(`[ttl] legion: LootJS modifiers could not be registered: ${e}`)
}
