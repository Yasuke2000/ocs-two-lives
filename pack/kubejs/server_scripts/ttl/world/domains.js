// priority: 71
// Canon domains and the residents that come back (design/architecture/world-state.md §6.6, H1, H4; WP-W3).
// Data: design/data/factions.toml ([domains] knobs, per faction `domain`, `throne`, `territory`) → TtlData.factions.
// Commands and test hooks: world/domain_commands.js (/ttl domain ...).
//
// A DOMAIN is the protected land of a canon nation (a faction of factions.toml), on the canon continent only (R11):
//   capital   a square of `capital_radius` blocks round the capital (`domain.capital`: "tempest" / "dwargon" = the settlement,
//             "build:<name>" = the placed build's anchor, "landmark:<name>" = the placed landmark, none = the faction's canon
//             capital; gen_data writes the nominal centre as `domain.center`, a placed build or landmark refines it)
//   builds    the boxes of its canon builds (`ttl.build.<name>.box`, Tempest's and Dwargon's worked areas), once placed
//   landmarks the reach squares of its placed landmarks (`ttl.landmark.<name>.at`)
//   region    `territory = "region"`: the whole canon letter of the faction (the knob for a sealed land; none ships so)
// plus, with [domains] unowned_builds, every placed canon build no faction owns (no members, never lifted).
// The canon parts (builds, landmarks) win over the capital square when both hold a column.
//
// THE GUARD is a block guard, not adventure mode: doors, chests, crafting stations and NPC dialogue keep working. Inside a
// domain a player who may not edit there cannot break or place blocks (BlockEvents.broken / placed), use the [domains]
// `use_items` / `use_suffixes` on blocks (buckets, flint and steel, fire charges, axes stripping, ...; BlockEvents.rightClicked
// and ItemEvents.rightClicked for the bucket's own ray), and explosions spare the protected blocks (LevelEvents.afterExplosion).
// Who may edit (TtlDomains.canEdit): staff (permission `staff_level`); anyone while a conflict over the faction is open
// (TtlChronicle.conflict, `conflict_edit`: all | land | none); the ruling nation's members (TtlChronicle.rule(f).nation, or the
// stages ttl.faction.<f>.ruler / .vassal that WP-W16 writes); members (stage ttl.faction.<f>.member or persistentData
// ttl.faction.member, `member_edit`: land = the capital square outside the canon parts, all, none). Outside the continent,
// in the free lands and every dimension that is not inside (tensura:boss_area included) nothing here applies.
// Event handlers sit at priority 71: a cancel here stops the duel liability (70) from recording a block that never broke.
//
// RESIDENTS (H1, R9). Tempest's goblins (generated/tempest_extras.js `residents`, and `rings.<phase>.residents` once WP-W5
// adds them, up to the current Tempest phase) are kept by a loop every `respawn_check_ticks`: each has the tags
// `ttl_tempest_resident` (story/cast.js hooks Rigurd and Gobta by it and the name), the faction's npc tag (`ttl.npc.tempest`:
// a kill costs kill_penalty.npc, rep/guards.js) and `ttl.resident.<id>` (id = the lowercase name, `goblin_<n>` for the
// unnamed). Canon characters (`invulnerable = "named"`: Rigurd, Rigur, Gobta, Haruna) are Invulnerable anchors and come back
// on the second check that finds them gone (a /kill still removes them); the others stay killable and come back
// `respawn_minutes` after they were first found missing. A resident is only judged while its chunk is loaded (entities
// included), so nothing is summoned into a chunk that may still hold it. Residents tempest.js spawned before this file
// existed are adopted (tags + invulnerability) by name, the unnamed by nearest free spot.
// Server persistentData: `ttl.domains.missing` JSON {id: {at, seen}}, `ttl.domains.testdelay` (seconds, test hook),
// `ttl.domains.loop` (loop stamp, reload-safe).
//
// PUBLIC API (other packages call these, guarded with typeof):
//   TtlDomains.at(level, pos)                 the domain hit at a block position of a level, or null (see `of`)
//   TtlDomains.of(server, dim, x, z)          {faction ('' = a canon build of no faction), title, kind: capital|build|landmark|
//                                             region, label (id), name (what players read), canon} or null
//   TtlDomains.canEdit(server, player, dim, x, z)   {ok, why, hit}: may this player change blocks in that column
//   TtlDomains.parts(server)                  every domain part in force (cached [domains] refresh_seconds; invalidate())
//   TtlDomains.residents(server) · ensureResidents(server) · residentsPlaced(server) (tempest.js extras, reserved line)
const TtlDomains = {
  RESIDENT: 'ttl_tempest_resident',
  RES_TAG: 'ttl.resident.',
  K_MISSING: 'ttl.domains.missing',
  K_DELAY: 'ttl.domains.testdelay',
  K_LOOP: 'ttl.domains.loop',
  OVERWORLD: 'minecraft:overworld',
  cache: null,
  cacheAt: 0,
  warnedAt: {},
  last: {},

  conf() {
    return (TtlData.factions && TtlData.factions.domains) || {}
  },

  factions() {
    return (TtlData.factions && TtlData.factions.faction) || []
  },

  faction(id) {
    var all = this.factions()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  invalidate() {
    this.cache = null
  },

  onContinent(dim, x, z) {
    try {
      if (typeof TtlWorld !== 'undefined') return TtlWorld.onContinent(dim, x, z)
    } catch (e) {
      console.error(`[ttl] domains: continent test failed, treating ${dim} ${x} ${z} as inside: ${e}`)
    }
    return String(dim) === this.OVERWORLD
  },

  ints(text) {
    var s = String(text || '').trim()
    if (!s) return null
    var out = s.split(/\s+/).map(Number)
    return out.every(n => !isNaN(n)) ? out : null
  },

  pd(server, key) {
    return String(server.persistentData.getString(key) || '')
  },

  // ---- where the domains lie ----------------------------------------------------------------------------------------

  // Worked area of Tempest or Dwargon as {x0, z0, x1, z1}, or null when the script is not loaded.
  settlement(name) {
    try {
      var b = null
      if (name === 'tempest' && typeof TtlTempest !== 'undefined') b = TtlTempest.box()
      if (name === 'dwargon' && typeof TtlDwargon !== 'undefined') b = TtlDwargon.box()
      return b ? { x0: b.ax0, z0: b.az0, x1: b.ax1, z1: b.az1 } : null
    } catch (e) {
      console.warn(`[ttl] domains: the ${name} box is unavailable: ${e}`)
      return null
    }
  },

  buildDef(name) {
    var all = TtlData.builds || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].name) === String(name)) return all[i]
    }
    return null
  },

  landmarkDef(name) {
    var all = (TtlData.landmarks && TtlData.landmarks.landmark) || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].name) === String(name)) return all[i]
    }
    return null
  },

  // A canon build's placed box {dim, x0, z0, x1, z1}; null while it is not placed.
  buildBox(server, name) {
    var s = this.settlement(name)
    if (s) {
      s.dim = this.OVERWORLD
      return s
    }
    var b = this.buildDef(name)
    if (!b) return null
    var box = this.ints(this.pd(server, `ttl.build.${name}.box`))
    if (!box || box.length !== 4) return null
    return { dim: String(b.dimension || this.OVERWORLD), x0: box[0], z0: box[1], x1: box[2], z1: box[3] }
  },

  landmarkBox(server, name) {
    var l = this.landmarkDef(name)
    var at = this.ints(this.pd(server, `ttl.landmark.${name}.at`))
    if (!l || !at || at.length !== 3) return null
    var r = Number(l.reach)
    return { dim: this.OVERWORLD, x0: at[0] - r, z0: at[2] - r, x1: at[0] + r, z1: at[2] + r }
  },

  // The capital's centre now: the settlement, the placed build or landmark, else the nominal centre gen_data wrote.
  center(server, f) {
    var d = f.domain
    var ref = String(d.capital || '')
    var c = null
    if (ref === 'tempest' || ref === 'dwargon') {
      var s = this.settlement(ref)
      if (s) c = [Math.round((s.x0 + s.x1) / 2), Math.round((s.z0 + s.z1) / 2)]
    } else if (ref.indexOf('build:') === 0) {
      var at = this.ints(this.pd(server, `ttl.build.${ref.substring(6)}.at`))
      if (at && at.length === 3) c = [at[0], at[2]]
    } else if (ref.indexOf('landmark:') === 0) {
      var lat = this.ints(this.pd(server, `ttl.landmark.${ref.substring(9)}.at`))
      if (lat && lat.length === 3) c = [lat[0], lat[2]]
    }
    return c || [Number(d.center[0]), Number(d.center[1])]
  },

  // What players read for a build or landmark: its title, else the name.
  display(kind, name) {
    if (kind === 'build' && (name === 'tempest' || name === 'dwargon')) return name === 'tempest' ? 'the village of Tempest' : 'the city of Dwargon'
    var def = kind === 'build' ? this.buildDef(name) : this.landmarkDef(name)
    return def && def.title ? String(def.title) : name
  },

  // Every part in force, canon parts first: [{faction, title, kind, label, canon, dim, x0, z0, x1, z1, letter}].
  build(server) {
    var out = []
    var capitals = []
    var owned = {}
    var self = this
    var rules = this.conf()
    this.factions().forEach(f => {
      var id = String(f.id)
      if (f.domain) {
        ;(f.domain.builds || []).forEach(n => {
          owned[String(n)] = true
          var b = self.buildBox(server, String(n))
          if (b) out.push({ faction: id, title: String(f.title), kind: 'build', label: String(n), name: self.display('build', String(n)), canon: true, dim: b.dim, x0: b.x0, z0: b.z0, x1: b.x1, z1: b.z1 })
        })
        ;(f.domain.landmarks || []).forEach(n => {
          var l = self.landmarkBox(server, String(n))
          if (l) out.push({ faction: id, title: String(f.title), kind: 'landmark', label: String(n), name: self.display('landmark', String(n)), canon: true, dim: l.dim, x0: l.x0, z0: l.z0, x1: l.x1, z1: l.z1 })
        })
        var c = self.center(server, f)
        var r = Number(f.domain.capital_radius !== undefined ? f.domain.capital_radius : rules.capital_radius)
        capitals.push({ faction: id, title: String(f.title), kind: 'capital', label: `capital ${c[0]} ${c[1]} r${r}`, canon: false, dim: self.OVERWORLD, x0: c[0] - r, z0: c[1] - r, x1: c[0] + r, z1: c[1] + r })
      }
      if (String(f.territory || 'domain') === 'region' && f.region) {
        capitals.push({ faction: id, title: String(f.title), kind: 'region', label: `region ${f.region}`, canon: false, dim: self.OVERWORLD, letter: String(f.region) })
      }
    })
    if (rules.unowned_builds === true) {
      var skip = rules.unowned_skip || []
      ;(TtlData.builds || []).forEach(b => {
        var n = String(b.name)
        if (owned[n] || skip.indexOf(n) >= 0) return
        var box = self.buildBox(server, n)
        if (box) out.push({ faction: '', title: String(b.title), kind: 'build', label: n, name: String(b.title), canon: true, dim: box.dim, x0: box.x0, z0: box.z0, x1: box.x1, z1: box.z1 })
      })
    }
    return out.concat(capitals)
  },

  parts(server) {
    var now = Date.now()
    if (this.cache && now - this.cacheAt < Number(this.conf().refresh_seconds || 10) * 1000) return this.cache
    try {
      this.cache = this.build(server)
    } catch (e) {
      console.error(`[ttl] domains: building the domain list failed: ${e}`)
      this.cache = this.cache || []
    }
    this.cacheAt = now
    return this.cache
  },

  // The domain at a column, or null. Outside the continent (R11) there are none.
  of(server, dim, x, z) {
    dim = String(dim)
    x = Math.floor(Number(x))
    z = Math.floor(Number(z))
    if (!this.onContinent(dim, x, z)) return null
    var all = this.parts(server)
    var letter = null
    for (var i = 0; i < all.length; i++) {
      var p = all[i]
      if (p.dim !== dim) continue
      if (p.kind === 'region') {
        if (letter === null) letter = typeof TtlWorld !== 'undefined' ? TtlWorld.ownerAt(x, z) : ''
        if (letter !== p.letter) continue
      } else if (x < p.x0 || x > p.x1 || z < p.z0 || z > p.z1) {
        continue
      }
      return { faction: p.faction, title: p.title, kind: p.kind, label: p.label, name: p.name || '', canon: p.canon }
    }
    return null
  },

  at(level, pos) {
    var server = level.getServer()
    return this.of(server, String(level.dimension), Number(pos.x), Number(pos.z))
  },

  // ---- who may edit ---------------------------------------------------------------------------------------------------

  isStaff(player) {
    try {
      return !!player.hasPermissions(Number(this.conf().staff_level))
    } catch (e) {
      return false
    }
  },

  // land = the capital square or region outside the canon parts.
  scopeAllows(scope, hit) {
    scope = String(scope || 'none')
    return scope === 'all' || (scope === 'land' && !hit.canon)
  },

  isMember(player, f) {
    try {
      if (player.stages.has(`ttl.faction.${f}.member`)) return true
      return String(player.persistentData.getString('ttl.faction.member') || '') === String(f)
    } catch (e) {
      return false
    }
  },

  // The ruling nation of a canon throne (WP-W16 sets it through TtlChronicle.setRule) and its stages.
  rules(server, player, f) {
    try {
      if (player.stages.has(`ttl.faction.${f}.ruler`) || player.stages.has(`ttl.faction.${f}.vassal`)) return true
      if (typeof TtlChronicle === 'undefined' || typeof TtlNations === 'undefined') return false
      var r = TtlChronicle.rule(server, f)
      if (!r || !r.nation) return false
      var mine = TtlNations.of(server, player)
      return !!mine && String(mine.key) === String(r.nation)
    } catch (e) {
      console.error(`[ttl] domains: reading the rule over ${f} failed: ${e}`)
      return false
    }
  },

  conflictOpen(server, f) {
    try {
      return typeof TtlChronicle !== 'undefined' && !!TtlChronicle.conflict(server, f)
    } catch (e) {
      console.error(`[ttl] domains: reading the conflict over ${f} failed: ${e}`)
      return false
    }
  },

  // {ok, why, hit}; `player` may be null (an explosion nobody caused): then only an open conflict lifts the guard.
  canEdit(server, player, dim, x, z) {
    var hit = this.of(server, dim, x, z)
    if (!hit) return { ok: true, why: this.onContinent(dim, x, z) ? 'no domain here' : 'outside the continent', hit: null }
    if (player && this.isStaff(player)) return { ok: true, why: 'staff', hit: hit }
    var f = hit.faction
    var rules = this.conf()
    if (f && this.conflictOpen(server, f) && this.scopeAllows(rules.conflict_edit, hit)) return { ok: true, why: `the conflict over ${f} is open`, hit: hit }
    if (f && player && this.rules(server, player, f)) return { ok: true, why: `the ruling nation of ${f}`, hit: hit }
    if (f && player && this.isMember(player, f) && this.scopeAllows(rules.member_edit, hit)) return { ok: true, why: `a member of ${f}`, hit: hit }
    if (!f) return { ok: false, why: `${hit.name} is a protected canon place`, hit: hit }
    return { ok: false, why: `The ${hit.title} protects ${hit.kind === 'capital' || hit.kind === 'region' ? 'its land' : hit.name}`, hit: hit }
  },

  // ---- the guard ----------------------------------------------------------------------------------------------------------

  tell(player, line) {
    try {
      var key = String(player.username)
      var now = Date.now()
      if (this.warnedAt[key] && now - this.warnedAt[key] < Number(this.conf().warn_seconds) * 1000) return
      this.warnedAt[key] = now
      player.tell(Text.red(line))
    } catch (e) {
      // a line that cannot be shown changes nothing
    }
  },

  // True when this player must be stopped at this block (never throws: the caller cancels outside any try/catch).
  denies(player, block, what) {
    try {
      if (!player || !player.isPlayer()) return false
      if (this.conf().enabled === false) return false
      var server = player.getServer()
      var v = this.canEdit(server, player, String(block.dimension), Number(block.x), Number(block.z))
      if (v.ok) return false
      this.tell(player, `${v.why}: you cannot ${what} here.`)
      return true
    } catch (e) {
      console.error(`[ttl] domains: the guard failed (${what}), letting it through: ${e}`)
      return false
    }
  },

  riskyItem(id) {
    id = String(id)
    var c = this.conf()
    if ((c.use_exempt || []).indexOf(id) >= 0) return false
    if ((c.use_items || []).indexOf(id) >= 0) return true
    return (c.use_suffixes || []).some(s => id.length > String(s).length && id.slice(-String(s).length) === String(s))
  },

  // ---- residents (H1, R9) ---------------------------------------------------------------------------------------------

  delayMs(server, anchor) {
    if (anchor) return 0
    var d = server.persistentData
    if (d.contains(this.K_DELAY)) return Number(d.getInt(this.K_DELAY)) * 1000
    return Number(this.conf().respawn_minutes) * 60000
  },

  setTestDelay(server, seconds) {
    if (seconds === null) server.persistentData.remove(this.K_DELAY)
    else server.persistentData.putInt(this.K_DELAY, Math.max(0, Math.floor(Number(seconds))))
  },

  missing(server) {
    try {
      var raw = this.pd(server, this.K_MISSING)
      var m = raw ? JSON.parse(raw) : {}
      return m && typeof m === 'object' ? m : {}
    } catch (e) {
      return {}
    }
  },

  saveMissing(server, m) {
    server.persistentData.putString(this.K_MISSING, JSON.stringify(m))
  },

  isAnchor(name) {
    var mode = String(this.conf().invulnerable || 'named')
    return mode === 'all' || (mode === 'named' && !!name)
  },

  // Every Tempest resident in force, in world coordinates; [] while Tempest (this version) is not placed.
  residents(server) {
    var out = []
    if (typeof TtlTempestExtras === 'undefined' || typeof TtlTempest === 'undefined' || typeof TTL_TEMPEST_VERSION === 'undefined') return out
    var d = server.persistentData
    if (d.getInt('ttl.tempest.version') !== TTL_TEMPEST_VERSION || !d.contains('ttl.tempest.base')) return out
    var base = d.getInt('ttl.tempest.base')
    var b = TtlTempest.box()
    var fac = this.faction('tempest')
    var npcTag = fac && fac.npc_tags && fac.npc_tags.length ? String(fac.npc_tags[0]) : 'ttl.npc.tempest'
    var self = this
    var add = (list, prefix) => {
      ;(list || []).forEach((r, i) => {
        var name = String(r[3] || '')
        out.push({
          id: name ? name.toLowerCase() : `${prefix}${i}`, name: name, anchor: self.isAnchor(name), npcTag: npcTag,
          dim: self.OVERWORLD, x: b.x0 + Number(r[0]) + 0.5, y: base + Number(r[1]), z: b.z0 + Number(r[2]) + 0.5
        })
      })
    }
    add(TtlTempestExtras.residents, 'goblin_')
    // WP-W5 rings: only the phases Tempest has reached.
    var rings = TtlTempestExtras.rings || {}
    var places = (TtlData.world && TtlData.world.places && TtlData.world.places.tempest) || []
    var phase = ''
    try {
      if (typeof TtlChronicle !== 'undefined') phase = TtlChronicle.phase(server, 'tempest')
    } catch (e) {
      phase = ''
    }
    var reached = places.indexOf(phase)
    places.forEach((p, i) => {
      if (i > 0 && i <= reached && rings[p]) add(rings[p].residents, `goblin_${p}_`)
    })
    return out
  },

  residentId(e) {
    var arr = e.getTags().toArray()
    for (var i = 0; i < arr.length; i++) {
      var t = String(arr[i])
      if (t.indexOf(this.RES_TAG) === 0) return t.substring(this.RES_TAG.length)
    }
    return ''
  },

  nameOf(e) {
    try {
      var n = e.getCustomName()
      return n ? String(n.getString()) : ''
    } catch (x) {
      return ''
    }
  },

  // Tags and invulnerability of a resident's entity, as the record says.
  mark(e, r) {
    var tags = e.getTags()
    if (!tags.contains(this.RESIDENT)) e.addTag(this.RESIDENT)
    if (!tags.contains(r.npcTag)) e.addTag(r.npcTag)
    if (!tags.contains(this.RES_TAG + r.id)) e.addTag(this.RES_TAG + r.id)
    if (!!e.isInvulnerable() !== r.anchor) e.setInvulnerable(r.anchor)
  },

  isLoaded(server, r) {
    return TtlCmd.run(server, `execute in ${r.dim} if loaded ${Math.floor(r.x)} ${Math.floor(r.y)} ${Math.floor(r.z)}`) > 0
  },

  summon(server, r) {
    var tags = JSON.stringify([this.RESIDENT, r.npcTag, this.RES_TAG + r.id])
    var name = r.name ? `,CustomName:'${JSON.stringify(r.name)}'` : ''
    var nbt = `{PersistenceRequired:1b,EvoState:1,Invulnerable:${r.anchor ? 1 : 0}b,Tags:${tags}${name}}`
    return TtlCmd.run(server, `execute in ${r.dim} run summon tensura:goblin ${r.x} ${r.y} ${r.z} ${nbt}`) > 0
  },

  // One pass over every resident. Returns {id: state} with state ok | adopted | missing | respawned | unloaded | outside | failed.
  ensureResidents(server) {
    var list = this.residents(server)
    var states = {}
    if (!list.length) return states
    var level = server.getLevel(this.OVERWORLD)
    if (!level) return states
    var byId = {}
    var legacy = []
    var self = this
    level.getEntities().forEach(e => {
      if (!e.isAlive() || !e.getTags().contains(self.RESIDENT)) return
      var id = self.residentId(e)
      if (id) (byId[id] = byId[id] || []).push(e)
      else legacy.push(e)
    })
    // Residents of an older tempest.js carry only ttl_tempest_resident: give each the record it stands for.
    var adopted = {}
    legacy.forEach(e => {
      var name = self.nameOf(e)
      var best = null
      var bestD = Infinity
      list.forEach(r => {
        if (byId[r.id] || r.name !== name) return
        var dx = e.getX() - r.x
        var dz = e.getZ() - r.z
        var d2 = dx * dx + dz * dz
        if (d2 < bestD) {
          best = r
          bestD = d2
        }
      })
      if (!best) return
      self.mark(e, best)
      byId[best.id] = [e]
      adopted[best.id] = true
    })
    var miss = this.missing(server)
    var changed = false
    var now = Date.now()
    list.forEach(r => {
      if (!self.onContinent(r.dim, r.x, r.z)) {
        states[r.id] = 'outside'
        if (miss[r.id]) {
          delete miss[r.id]
          changed = true
        }
        return
      }
      var ents = byId[r.id] || []
      if (ents.length > 0) {
        ents.slice(1).forEach(x => x.discard())
        if (ents.length > 1) console.info(`[ttl] domains: resident ${r.id} had ${ents.length} copies, ${ents.length - 1} removed`)
        self.mark(ents[0], r)
        if (miss[r.id]) {
          delete miss[r.id]
          changed = true
        }
        states[r.id] = adopted[r.id] ? 'adopted' : 'ok'
        return
      }
      if (!self.isLoaded(server, r)) {
        states[r.id] = 'unloaded'
        return
      }
      var m = miss[r.id] || { at: now, seen: 0 }
      m.seen = Number(m.seen) + 1
      miss[r.id] = m
      changed = true
      if (m.seen < Number(self.conf().confirm_checks) || now - Number(m.at) < self.delayMs(server, r.anchor)) {
        states[r.id] = 'missing'
        return
      }
      if (self.summon(server, r)) {
        delete miss[r.id]
        states[r.id] = 'respawned'
        console.info(`[ttl] domains: resident ${r.id}${r.name ? ` (${r.name})` : ''} came back at ${Math.floor(r.x)} ${r.y} ${Math.floor(r.z)}${r.anchor ? ' (anchor, invulnerable)' : ''}`)
      } else {
        states[r.id] = 'failed'
        console.error(`[ttl] domains: summoning resident ${r.id} at ${r.x} ${r.y} ${r.z} failed`)
      }
    })
    if (changed) this.saveMissing(server, miss)
    var n = Object.keys(adopted).length
    if (n) console.info(`[ttl] domains: adopted ${n} Tempest resident(s) placed before the respawn loop (${Object.keys(adopted).join(', ')})`)
    this.last = states
    return states
  },

  // tempest.js extras(): the residents were just (re)summoned; forget old absences and tag them now.
  residentsPlaced(server) {
    this.saveMissing(server, {})
    this.ensureResidents(server)
  }
}

// ---- the guard's events (event.cancel() leaves by throwing: never inside a try/catch) -----------------------------------

BlockEvents.broken(event => {
  if (TtlDomains.denies(event.player, event.block, 'break blocks')) event.cancel()
})

BlockEvents.placed(event => {
  if (TtlDomains.denies(event.entity, event.block, 'place blocks')) event.cancel()
})

// Buckets, fire and the tools that change a block on a right-click. Doors, chests and stations (any other item, an empty
// hand) pass. The fluid goes to the face's neighbour, so both blocks are checked.
BlockEvents.rightClicked(event => {
  var stop = false
  try {
    var player = event.player
    if (player && TtlDomains.riskyItem(event.item.id)) {
      var b = event.block
      var next = null
      try {
        next = event.facing ? b.offset(event.facing) : null
      } catch (e) {
        next = null
      }
      stop = TtlDomains.denies(player, b, 'use that') || (next !== null && TtlDomains.denies(player, next, 'use that'))
    }
  } catch (e) {
    console.error(`[ttl] domains: right-click check failed: ${e}`)
  }
  if (stop) event.cancel()
})

// A bucket is also used through its own ray (the item click), not only on a targeted block.
ItemEvents.rightClicked(event => {
  var stop = false
  try {
    var player = event.player
    var id = String(event.item.id)
    if (player && TtlDomains.riskyItem(id) && /bucket$/.test(id)) {
      var t = null
      try {
        t = event.target
      } catch (e) {
        t = null
      }
      var b = t && t.block ? t.block : player.block
      stop = !!b && TtlDomains.denies(player, b, 'use that')
    }
  } catch (e) {
    console.error(`[ttl] domains: item-click check failed: ${e}`)
  }
  if (stop) event.cancel()
})

// Explosions (TNT, creepers, Tensura blasts) spare the blocks of a domain the exploder may not edit; nobody's explosion is
// held to the strictest rule. Entities still take the blast.
LevelEvents.afterExplosion(event => {
  try {
    if (TtlDomains.conf().enabled === false) return
    var level = event.level
    var server = level.getServer()
    var dim = String(level.dimension)
    if (!TtlDomains.onContinent(dim, event.x, event.z)) return
    var who = null
    try {
      who = event.exploder
      if (who && !who.isPlayer()) who = null
    } catch (e) {
      who = null
    }
    var hit = event.getAffectedBlocks()
    var keep = []
    var seen = {}
    for (var i = 0; i < hit.size(); i++) {
      var b = hit.get(i)
      var key = `${b.x},${b.z}`
      if (seen[key] === undefined) seen[key] = !TtlDomains.canEdit(server, who, dim, b.x, b.z).ok
      if (seen[key]) keep.push(b)
    }
    for (var j = 0; j < keep.length; j++) event.removeAffectedBlock(keep[j])
    if (keep.length > 0) console.info(`[ttl] domains: ${keep.length} block(s) spared from an explosion at ${Math.floor(event.x)} ${Math.floor(event.y)} ${Math.floor(event.z)}`)
  } catch (e) {
    console.error(`[ttl] domains: explosion check failed: ${e}`)
  }
})

// ---- the resident loop ----------------------------------------------------------------------------------------------------

ServerEvents.loaded(event => {
  var server = event.server
  TtlDomains.invalidate()
  var stamp = String(Date.now())
  server.persistentData.putString(TtlDomains.K_LOOP, stamp)
  var every = Math.max(20, Number(TtlDomains.conf().respawn_check_ticks || 100))
  var tick = () => server.scheduleInTicks(every, () => {
    if (String(server.persistentData.getString(TtlDomains.K_LOOP)) !== stamp) return
    try {
      TtlDomains.ensureResidents(server)
    } catch (e) {
      console.error(`[ttl] domains: resident check failed: ${e}`)
    }
    tick()
  })
  tick()
})
