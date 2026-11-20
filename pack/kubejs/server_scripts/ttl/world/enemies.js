// priority: 45
// The enemies of the roads: hostile humanoid Easy NPCs that souls MAY kill (Yasuke 20/11/2026), bounty targets of the Free
// Guild. Data and the life of a camp: design/data/enemies.toml (TtlData.enemies; read its header first). Presets and loot
// tables: tools/gen_npcs.py (ttl_enemy_<archetype>_<n>, ttl:entities/enemy_<archetype>).
//
// Entity tags: `ttl.enemy` (every one), `ttl.enemy.<archetype>`, `ttl.camp.<camp id>` (or `ttl.enemy.test` for a test
// spawn), `ttl.enemy.r<settings.rev>`.
// Server persistentData `ttl.enemies.state` = JSON {<camp id>: {stock, regen (ms the next stock point is due, 0 = full),
// sleep (checks in a row without a soul within sleep_radius), members: [uuid], kills, last ({who, at})}}.
// Performance (PR #78: entity ticking is the main tick cost): nothing is spawned unless a Life 2 soul is within wake_radius,
// at most settings.max_total on the server, members are looked up by UUID (no world scans) and a sleeping camp is emptied.
//
// Kill credit (see enemies.toml): EntityEvents.death names the killer; EntityEvents.afterHurt remembers the last soul that
// hurt each enemy, which the loop uses when a member vanished from a loaded chunk without a death event (mob deaths are
// unreliable here, guild.js). A credited kill: +1 on the guild objectives `ttl.g.ttl_<archetype>` and `ttl.g.ttl_<group>`,
// TtlRoads.pay(enemies.slay, good) with the camp's faction as the `victim` rep, one line to the soul.
//
// Ops (/ttl enemies ...): list · check · spawn <camp> [n] (wakes it now, ignoring the distance rules) · sleep <camp> ·
//   testspawn <archetype> <pos> · clear [<camp>|test|all] · reset <camp> (full stock, no members) ·
//   expect <alive|stock|kills|members> <camp|test> <n> · expect spot <x> <z> <ok|refused> · expect killedby <player|resident|
//   <entity type>> (the last enemy death) (test assertions, "ttl: ..." when false)
const TtlEnemies = {
  TAG: 'ttl.enemy',
  TEST: 'ttl.enemy.test',
  K_STATE: 'ttl.enemies.state',
  K_LOOP: 'ttl.enemies.loop',
  OVERWORLD: 'minecraft:overworld',
  hits: {},
  credited: {},
  // The last enemy death: {arch, camp, by ('player' | 'resident' (a Tempest resident: the guards) | entity type | ''), at}.
  lastDeath: null,
  uuidClass: undefined,
  hm: undefined,

  conf() {
    return TtlData.enemies || { settings: {}, archetype: [], camp: [], group: {} }
  },

  set() {
    return this.conf().settings || {}
  },

  camps() {
    return this.conf().camp || []
  },

  camp(id) {
    var all = this.camps()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  archetype(id) {
    var all = this.conf().archetype || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  // ---- state -----------------------------------------------------------------------------------------------------

  state(server) {
    var raw = String(server.persistentData.getString(this.K_STATE) || '')
    var st = {}
    try {
      st = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] enemies: state unreadable, starting over: ${e}`)
    }
    var self = this
    this.camps().forEach(c => {
      var s = st[c.id] || {}
      st[c.id] = {
        stock: s.stock === undefined ? Number(c.count) : Math.min(Number(s.stock), Number(c.count)),
        regen: Number(s.regen || 0), sleep: Number(s.sleep || 0), members: s.members || [], kills: Number(s.kills || 0),
        last: s.last || null
      }
    })
    return st
  },

  save(server, st) {
    server.persistentData.putString(this.K_STATE, JSON.stringify(st))
  },

  // ---- helpers ---------------------------------------------------------------------------------------------------

  tagsOf(e) {
    var out = []
    try {
      e.getTags().forEach(t => out.push(String(t)))
    } catch (x) {
      // no tags readable: not ours
    }
    return out
  },

  isEnemy(e) {
    try {
      return !!e && e.getTags().contains(this.TAG)
    } catch (x) {
      return false
    }
  },

  // {arch, camp} from an enemy's tags (camp '' for a test spawn).
  whoIs(e) {
    var out = { arch: '', camp: '' }
    this.tagsOf(e).forEach(t => {
      if (t.indexOf('ttl.camp.') === 0) out.camp = t.substring(9)
      else if (t.indexOf('ttl.enemy.') === 0 && t !== this.TEST && !/^ttl\.enemy\.r\d+$/.test(t)) out.arch = t.substring(10)
    })
    return out
  },

  uuidOf(e) {
    try {
      return String(e.uuid)
    } catch (x) {
      return ''
    }
  },

  byUuid(level, id) {
    if (this.uuidClass === undefined) {
      try {
        this.uuidClass = Java.loadClass('java.util.UUID')
      } catch (x) {
        this.uuidClass = null
        console.error(`[ttl] enemies: java.util.UUID cannot be loaded (${x}); members are found by a scan`)
      }
    }
    try {
      if (this.uuidClass) return level['getEntity(java.util.UUID)'](this.uuidClass.fromString(String(id)))
    } catch (x) {
      // fall through to the scan
    }
    var found = null
    level.getEntities().forEach(e => { if (!found && String(e.uuid) === String(id)) found = e })
    return found
  },

  // Life 2 souls in the overworld that may wake a camp (test bots count: they are how the tests stand there).
  souls(server) {
    var out = []
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (p.isSpectator() || TtlLife.phase(p) !== 'life2' || TtlLife.dimensionOf(p) !== this.OVERWORLD) return
        out.push({ p: p, x: p.getX(), z: p.getZ() })
      } catch (e) {
        console.warn(`[ttl] enemies: reading ${p.username} failed: ${e}`)
      }
    })
    return out
  },

  nearest(souls, x, z) {
    var best = Infinity
    souls.forEach(s => {
      var d = Math.sqrt((s.x - x) * (s.x - x) + (s.z - z) * (s.z - z))
      if (d < best) best = d
    })
    return best
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

  // '' when an enemy may stand at this column, else why not. Never in a domain, a safe square (Tempest r 56, the
  // arrival), a town's spawn zone (spawns.toml, both bands), water or lava.
  refusal(server, level, x, z) {
    var dim = this.OVERWORLD
    try {
      if (typeof TtlDomains !== 'undefined' && TtlDomains.of(server, dim, x, z)) return 'domain'
    } catch (e) {
      return `domain check failed: ${e}`
    }
    if (typeof TtlSpawnZones !== 'undefined' && TtlSpawnZones.band(dim, x, z) !== 'open') return 'spawn zone'
    if (typeof TtlSafeSpawns !== 'undefined') {
      var safe = TtlSafeSpawns.ZONES.some(s => s.dim === dim && (x - s.x) * (x - s.x) + (z - s.z) * (z - s.z) <= s.radius * s.radius)
      if (safe) return 'safe square'
    }
    var y = this.surfaceY(level, x, z)
    if (y === null) return 'not loaded'
    var below = String(level.getBlock(Math.floor(x), y - 1, Math.floor(z)).id)
    if (/water|lava|bubble/.test(below)) return `on ${below}`
    var feet = String(level.getBlock(Math.floor(x), y, Math.floor(z)).id)
    if (/water|lava/.test(feet)) return `in ${feet}`
    return ''
  },

  // A spawn position within the camp's radius, at least min_player_distance from every soul, or null.
  spot(server, level, c, souls, ignoreSouls) {
    var r = Number(c.radius)
    var min = Number(this.set().min_player_distance || 20)
    for (var i = 0; i < 8; i++) {
      var a = Math.random() * Math.PI * 2
      var d = Math.random() * r
      var x = Math.floor(Number(c.x) + Math.cos(a) * d) + 0.5
      var z = Math.floor(Number(c.z) + Math.sin(a) * d) + 0.5
      if (!ignoreSouls && this.nearest(souls, x, z) < min) continue
      if (this.refusal(server, level, x, z)) continue
      return { dim: this.OVERWORLD, x: x, y: this.surfaceY(level, x, z), z: z }
    }
    return null
  },

  pick(c) {
    var mix = c.mix || {}
    var keys = Object.keys(mix)
    var total = 0
    keys.forEach(k => { total += Number(mix[k]) })
    var roll = Math.random() * total
    for (var i = 0; i < keys.length; i++) {
      roll -= Number(mix[keys[i]])
      if (roll < 0) return keys[i]
    }
    return keys[keys.length - 1]
  },

  // The presets of an archetype, one per look variant of its arm width (tools/enemies_check.py writes the list into
  // TtlData.enemies.presets; gen_npcs.py writes the files under the same names).
  presets(arch) {
    var all = (this.conf().presets || {})[arch] || []
    return all.length ? all : [`ttl_enemy_${arch}_1`]
  },

  // Imports one enemy at pos with its tags, stats, hands and home. Entity or null.
  spawnOne(server, pos, archId, campId) {
    var a = this.archetype(archId)
    if (!a) return null
    var list = this.presets(archId)
    var preset = list[Math.floor(Math.random() * list.length)]
    var tags = [this.TAG, `${this.TAG}.${archId}`, `${this.TAG}.r${Number(this.set().rev || 1)}`, campId ? `ttl.camp.${campId}` : this.TEST]
    var e = TtlSideNpc.spawn(server, pos, preset, tags)
    if (!e) return null
    var id = this.uuidOf(e)
    var attr = (name, v) => TtlCmd.run(server, `attribute ${id} minecraft:generic.${name} base set ${Number(v)}`)
    attr('max_health', a.health)
    attr('attack_damage', a.damage)
    attr('armor', a.armor)
    attr('movement_speed', a.speed)
    TtlCmd.run(server, `data merge entity ${id} {Health:${Number(a.health)}f}`)
    if (typeof TtlNpcGear !== 'undefined') TtlNpcGear.equip(server, e, { main: a.main || '', off: a.off || '' })
    TtlSideNpc.cmd(server, e, `navigation set home {npc} ${Math.floor(pos.x)} ${Math.floor(pos.y)} ${Math.floor(pos.z)}`)
    return e
  },

  remove(server, e) {
    var id = this.uuidOf(e)
    delete this.hits[id]
    TtlSideNpc.remove(server, e)
  },

  // ---- kills -----------------------------------------------------------------------------------------------------

  // A soul hurt an enemy: remembered for the fallback credit.
  onHurt(event) {
    var e = event.entity
    if (!this.isEnemy(e)) return
    var src = event.source
    var who = src ? src.actual : null
    if (!who || !who.isPlayer()) return
    this.hits[this.uuidOf(e)] = { name: String(who.username), at: Date.now() }
  },

  // Credit a kill once per enemy (the death event and the loop's fallback may both see it).
  credit(server, player, e, info) {
    var id = info.uuid
    if (this.credited[id]) return false
    this.credited[id] = Date.now()
    var a = this.archetype(info.arch)
    var c = info.camp ? this.camp(info.camp) : null
    var name = String(player.username)
    var add = obj => TtlCmd.run(server, `scoreboard players add ${name} ${obj} 1`)
    if (info.arch) add(`ttl.g.ttl_${info.arch}`)
    if (c) add(`ttl.g.ttl_${c.group}`)
    var res = null
    try {
      if (typeof TtlRoads !== 'undefined' && TtlLife.phase(player) === 'life2') {
        res = TtlRoads.pay(server, player, {
          id: String(this.set().road || 'enemies.slay'), road: 'good', faction: c && c.faction ? String(c.faction) : undefined,
          reason: `slew a ${a ? a.name : 'foe'}`, dim: this.OVERWORLD, pos: { x: info.x, y: info.y, z: info.z }
        })
      }
    } catch (x) {
      console.error(`[ttl] enemies: road for ${name} failed: ${x}`)
    }
    player.tell(Text.gray(`${a ? a.name : 'Outlaw'} slain${c ? ` (${c.title})` : ''}.`))
    console.info(`[ttl] enemies: ${name} killed ${info.arch || '?'} of ${info.camp || 'test'}${res && res.ok ? '' : ' (no road)'}`)
    return true
  },

  // One member of a camp is gone: the stock drops (a kill) and the regen clock starts.
  lose(server, campId, id, who) {
    var st = this.state(server)
    var s = st[campId]
    if (!s) return
    var at = s.members.indexOf(String(id))
    if (at >= 0) s.members.splice(at, 1)
    var c = this.camp(campId)
    if (s.stock >= Number(c.count)) s.regen = Date.now() + Number(c.regen_minutes) * 60000
    s.stock = Math.max(0, s.stock - 1)
    s.kills++
    s.last = { who: who || '', at: Date.now() }
    this.save(server, st)
  },

  onDeath(event) {
    var e = event.entity
    if (!this.isEnemy(e)) return
    var server = event.server
    var info = this.whoIs(e)
    info.uuid = this.uuidOf(e)
    info.x = e.getX()
    info.y = e.getY()
    info.z = e.getZ()
    var killer = null
    try {
      killer = event.source.actual
    } catch (x) {
      killer = null
    }
    var by = ''
    try {
      if (killer && killer.isPlayer()) by = 'player'
      else if (killer && killer.getTags().contains('ttl_tempest_resident')) by = 'resident'
      else if (killer) by = String(killer.type)
    } catch (x) {
      by = ''
    }
    this.lastDeath = { arch: info.arch, camp: info.camp, by: by, at: Date.now() }
    if (!killer || !killer.isPlayer()) {
      var h = this.hits[info.uuid]
      var secs = Number(this.set().credit_seconds || 15)
      if (h && Date.now() - h.at <= secs * 1000) killer = server.getPlayerList().getPlayerByName(h.name)
    }
    if (killer && killer.isPlayer()) this.credit(server, killer, e, info)
    if (info.camp) this.lose(server, info.camp, info.uuid, killer && killer.isPlayer() ? String(killer.username) : '')
    delete this.hits[info.uuid]
  },

  // ---- the loop --------------------------------------------------------------------------------------------------

  // One pass over every camp. Returns {awake, spawned, removed, alive}.
  pass(server, opts) {
    var o = opts || {}
    var set = this.set()
    var out = { awake: 0, spawned: 0, removed: 0, alive: 0 }
    var level = server.getLevel(this.OVERWORLD)
    if (!level) return out
    var souls = this.souls(server)
    var st = this.state(server)
    var now = Date.now()
    var self = this
    var rev = `${this.TAG}.r${Number(set.rev || 1)}`
    var leash = Number(set.leash || 40)
    var secs = Number(set.credit_seconds || 15)
    var living = {}
    // Pass 1: members, regen, credit for the vanished, leash, rev.
    this.camps().forEach(c => {
      var s = st[c.id]
      if (s.stock < Number(c.count) && !s.regen) s.regen = now + Number(c.regen_minutes) * 60000
      while (s.stock < Number(c.count) && s.regen > 0 && now >= s.regen) {
        s.stock++
        s.regen = s.stock < Number(c.count) ? s.regen + Number(c.regen_minutes) * 60000 : 0
      }
      var keep = []
      var alive = []
      s.members.forEach(id => {
        var e = self.byUuid(level, id)
        if (e && e.isAlive()) {
          var dx = e.getX() - Number(c.x)
          var dz = e.getZ() - Number(c.z)
          var far = Math.sqrt(dx * dx + dz * dz) > 2 * leash && self.nearest(souls, e.getX(), e.getZ()) > 24
          if (far || !e.getTags().contains(rev)) {
            self.remove(server, e)
            out.removed++
            return
          }
          keep.push(id)
          alive.push(e)
          return
        }
        if (e || self.credited[id]) return
        // Not found: still in an unloaded chunk (keep it), or gone from a loaded one (a death without an event, a /kill).
        if (!level.hasChunkAt(Number(c.x), Number(c.z))) {
          keep.push(id)
          return
        }
        var h = self.hits[id]
        if (h && now - h.at <= secs * 1000) {
          var p = server.getPlayerList().getPlayerByName(h.name)
          if (p) self.credit(server, p, null, { uuid: id, arch: '', camp: c.id, x: Number(c.x), y: 64, z: Number(c.z) })
          if (s.stock >= Number(c.count)) s.regen = now + Number(c.regen_minutes) * 60000
          s.stock = Math.max(0, s.stock - 1)
          s.kills++
        }
        delete self.hits[id]
      })
      s.members = keep
      living[c.id] = alive
      out.alive += alive.length
    })
    // Pass 2: wake (top up), sleep (empty), extras.
    this.camps().forEach(c => {
      var s = st[c.id]
      var alive = living[c.id]
      var forced = o.camp === c.id
      var d = self.nearest(souls, Number(c.x), Number(c.z))
      if (forced || d <= Number(set.wake_radius)) {
        out.awake++
        s.sleep = 0
        var want = Math.min(Number(c.count), s.stock)
        var room = Math.max(0, Number(set.max_total) - out.alive)
        var n = Math.min(want - s.members.length, forced ? Number(o.n || want) : Number(set.spawn_per_check), room)
        for (var i = 0; i < n; i++) {
          var pos = self.spot(server, level, c, souls, forced)
          if (!pos) break
          var e = self.spawnOne(server, pos, self.pick(c), c.id)
          if (!e) break
          s.members.push(self.uuidOf(e))
          alive.push(e)
          out.spawned++
          out.alive++
        }
        if (alive.length > Number(c.count)) {
          alive.sort((p, q) => {
            var dp = (p.getX() - c.x) * (p.getX() - c.x) + (p.getZ() - c.z) * (p.getZ() - c.z)
            var dq = (q.getX() - c.x) * (q.getX() - c.x) + (q.getZ() - c.z) * (q.getZ() - c.z)
            return dq - dp
          })
          while (alive.length > Number(c.count)) {
            var extra = alive.shift()
            s.members.splice(s.members.indexOf(self.uuidOf(extra)), 1)
            self.remove(server, extra)
            out.removed++
          }
        }
      } else if (d > Number(set.sleep_radius) && !o.keep) {
        s.sleep++
        if (s.sleep >= Number(set.sleep_checks) && alive.length) {
          alive.forEach(e => {
            s.members.splice(s.members.indexOf(self.uuidOf(e)), 1)
            self.remove(server, e)
            out.removed++
          })
        }
      }
    })
    this.save(server, st)
    // Forget old credit marks (a death and the fallback never come more than a minute apart).
    Object.keys(this.credited).forEach(id => { if (now - self.credited[id] > 120000) delete self.credited[id] })
    return out
  },

  // An enemy that joins the world (a chunk loads) and is no member of its camp is an orphan: removed next tick.
  onJoin(event) {
    var e = event.entity
    if (!this.isEnemy(e)) return
    var server = e.getServer()
    if (!server) return
    var self = this
    server.scheduleInTicks(1, () => {
      try {
        if (!e.isAlive()) return
        var info = self.whoIs(e)
        if (!info.camp) return
        var s = self.state(server)[info.camp]
        if (s && s.members.indexOf(self.uuidOf(e)) >= 0) return
        console.info(`[ttl] enemies: orphan ${info.arch} of ${info.camp} removed`)
        self.remove(server, e)
      } catch (x) {
        console.error(`[ttl] enemies: orphan check failed: ${x}`)
      }
    })
  }
}

EntityEvents.afterHurt(event => {
  try {
    TtlEnemies.onHurt(event)
  } catch (e) {
    console.error(`[ttl] enemies: hurt record failed: ${e}`)
  }
})

EntityEvents.death(event => {
  try {
    TtlEnemies.onDeath(event)
  } catch (e) {
    console.error(`[ttl] enemies: death handling failed: ${e}`)
  }
})

EntityEvents.spawned(event => {
  try {
    TtlEnemies.onJoin(event)
  } catch (e) {
    console.error(`[ttl] enemies: join check failed: ${e}`)
  }
})

// An enemy drops its loot table, never what it holds (the hands have drop chance 0; this is the belt and braces).
EntityEvents.drops(event => {
  try {
    var e = event.entity
    if (!TtlEnemies.isEnemy(e)) return
    var a = TtlEnemies.archetype(TtlEnemies.whoIs(e).arch)
    if (!a) return
    var gear = {}
    if (a.main) gear[String(a.main)] = true
    if (a.off) gear[String(a.off)] = true
    var drops = event.getDrops()
    var gone = []
    drops.forEach(d => { if (gear[String(d.getItem().id)]) gone.push(d) })
    gone.forEach(d => drops.remove(d))
  } catch (x) {
    console.error(`[ttl] enemies: drop filter failed: ${x}`)
  }
})

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(40, Number(TtlEnemies.set().check_ticks || 100))
  var stamp = Date.now()
  server.persistentData.putLong(TtlEnemies.K_LOOP, stamp)
  var loop = () => server.scheduleInTicks(every, () => {
    // A /reload starts a new loop; the old one stops at its next turn.
    if (Number(server.persistentData.getLong(TtlEnemies.K_LOOP)) !== stamp) return
    try {
      if (server.getPlayerList().getPlayers().size() > 0) TtlEnemies.pass(server)
    } catch (e) {
      console.error(`[ttl] enemies: pass failed: ${e}`)
    }
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var ops = src => src.hasPermission(2)
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] enemies command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var server = ctx => ctx.source.getServer()
  var str = (ctx, n) => String(Arguments.STRING.getResult(ctx, n))
  var needCamp = id => {
    var c = TtlEnemies.camp(id)
    if (!c) throw `unknown camp ${id} (${TtlEnemies.camps().map(x => x.id).join(', ')})`
    return c
  }
  // Living enemies of a camp ('test' = the test spawns) in loaded chunks.
  var livingOf = (s, which) => {
    var tag = which === 'test' ? TtlEnemies.TEST : `ttl.camp.${which}`
    var out = []
    s.getAllLevels().forEach(level => level.getEntities().forEach(e => {
      if (e.isAlive() && e.getTags().contains(tag)) out.push(e)
    }))
    return out
  }

  var list = ctx => {
    var s = server(ctx)
    var st = TtlEnemies.state(s)
    var souls = TtlEnemies.souls(s)
    TtlEnemies.camps().forEach(c => {
      var r = st[c.id]
      var d = TtlEnemies.nearest(souls, Number(c.x), Number(c.z))
      say(ctx, `${c.id} (${c.group}) at ${c.x} ${c.z}: ${r.members.length} member(s), stock ${r.stock}/${c.count}` +
        `${r.regen ? `, +1 in ${Math.max(0, Math.round((r.regen - Date.now()) / 1000))} s` : ''}, ${r.kills} kill(s), ` +
        `${d === Infinity ? 'no soul online' : `nearest soul ${Math.round(d)}`}${r.sleep ? `, asleep ${r.sleep}` : ''}`)
    })
    return 1
  }

  var check = ctx => {
    var r = TtlEnemies.pass(server(ctx))
    say(ctx, `enemies: ${r.awake} camp(s) awake, ${r.spawned} spawned, ${r.removed} removed, ${r.alive} alive`)
    return 1
  }

  var spawn = n => ctx => {
    var c = needCamp(str(ctx, 'camp'))
    var r = TtlEnemies.pass(server(ctx), { camp: c.id, n: n ? Arguments.INTEGER.getResult(ctx, 'n') : 0, keep: true })
    say(ctx, `enemies: ${c.id} woken, ${r.spawned} spawned`)
    return 1
  }

  var sleep = ctx => {
    var s = server(ctx)
    var c = needCamp(str(ctx, 'camp'))
    var st = TtlEnemies.state(s)
    var n = 0
    livingOf(s, c.id).forEach(e => {
      TtlEnemies.remove(s, e)
      n++
    })
    st[c.id].members = []
    st[c.id].sleep = Number(TtlEnemies.set().sleep_checks)
    TtlEnemies.save(s, st)
    say(ctx, `enemies: ${c.id} asleep, ${n} removed`)
    return 1
  }

  var testspawn = ctx => {
    var s = server(ctx)
    var arch = str(ctx, 'archetype')
    if (!TtlEnemies.archetype(arch)) throw `unknown archetype ${arch}`
    var bp = Arguments.BLOCK_POS.getResult(ctx, 'pos')
    var pos = { dim: String(ctx.source.getLevel().dimension), x: bp.getX() + 0.5, y: bp.getY(), z: bp.getZ() + 0.5 }
    var e = TtlEnemies.spawnOne(s, pos, arch, '')
    if (!e) throw `could not spawn a ${arch}`
    say(ctx, `enemies: test ${arch} at ${pos.x} ${pos.y} ${pos.z}`)
    return 1
  }

  var clear = ctx => {
    var s = server(ctx)
    var which = str(ctx, 'which')
    var st = TtlEnemies.state(s)
    var n = 0
    var tag = which === 'all' ? TtlEnemies.TAG : which === 'test' ? TtlEnemies.TEST : `ttl.camp.${needCamp(which).id}`
    var gone = []
    s.getAllLevels().forEach(level => level.getEntities().forEach(e => { if (e.getTags().contains(tag)) gone.push(e) }))
    gone.forEach(e => {
      TtlEnemies.remove(s, e)
      n++
    })
    Object.keys(st).forEach(id => { if (which === 'all' || which === id) st[id].members = [] })
    TtlEnemies.save(s, st)
    say(ctx, `enemies: ${n} removed (${which})`)
    return 1
  }

  var reset = ctx => {
    var s = server(ctx)
    var c = needCamp(str(ctx, 'camp'))
    livingOf(s, c.id).forEach(e => TtlEnemies.remove(s, e))
    var st = TtlEnemies.state(s)
    st[c.id] = { stock: Number(c.count), regen: 0, sleep: 0, members: [], kills: 0, last: null }
    TtlEnemies.save(s, st)
    say(ctx, `enemies: ${c.id} reset (stock ${c.count}, no members)`)
    return 1
  }

  var expect = ctx => {
    var s = server(ctx)
    var p = String(Arguments.GREEDY_STRING.getResult(ctx, 'what')).trim().split(/\s+/)
    var cmp = (got, want) => {
      var m = /^(>=|<=)?(\d+)$/.exec(want)
      if (!m) throw `bad number ${want}`
      var n = Number(m[2])
      return m[1] === '>=' ? got >= n : m[1] === '<=' ? got <= n : got === n
    }
    if (p[0] === 'spot' && p.length === 4) {
      var why = TtlEnemies.refusal(s, s.getLevel(TtlEnemies.OVERWORLD), Number(p[1]) + 0.5, Number(p[2]) + 0.5)
      var ok = why === '' || why === 'not loaded'
      if ((p[3] === 'ok') !== ok) throw `enemies: spot ${p[1]} ${p[2]} is ${ok ? 'allowed' : `refused (${why})`}, expected ${p[3]}`
      say(ctx, `enemies: spot ${p[1]} ${p[2]} ${p[3]} as expected${why ? ` (${why})` : ''}`)
      return 1
    }
    if (p[0] === 'killedby' && p.length === 2) {
      var ld = TtlEnemies.lastDeath
      if (!ld || ld.by !== p[1]) throw `enemies: expected the last enemy killed by ${p[1]}, got ${ld ? ld.by || 'nothing' : 'no death yet'}`
      say(ctx, `enemies: the last ${ld.arch} was killed by ${ld.by} as expected`)
      return 1
    }
    if (p.length !== 3) throw 'expect <alive|stock|kills|members> <camp|test> <n|>=n|<=n> · expect spot <x> <z> <ok|refused> · expect killedby <player|resident|<type>>'
    var got
    if (p[0] === 'alive') got = livingOf(s, p[1]).length
    else {
      var r = TtlEnemies.state(s)[needCamp(p[1]).id]
      if (p[0] === 'stock') got = r.stock
      else if (p[0] === 'kills') got = r.kills
      else if (p[0] === 'members') got = r.members.length
      else throw `unknown field ${p[0]}`
    }
    if (!cmp(got, p[2])) throw `enemies: expected ${p[0]} ${p[1]} ${p[2]}, got ${got}`
    say(ctx, `enemies: ${p[0]} ${p[1]} ${got} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('enemies').requires(ops)
      .then(Commands.literal('list').executes(logged(list)))
      .then(Commands.literal('check').executes(logged(check)))
      .then(Commands.literal('spawn').then(Commands.argument('camp', Arguments.STRING.create(event)).executes(logged(spawn(false)))
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(spawn(true))))))
      .then(Commands.literal('sleep').then(Commands.argument('camp', Arguments.STRING.create(event)).executes(logged(sleep))))
      .then(Commands.literal('testspawn').then(Commands.argument('archetype', Arguments.STRING.create(event))
        .then(Commands.argument('pos', Arguments.BLOCK_POS.create(event)).executes(logged(testspawn)))))
      .then(Commands.literal('clear').then(Commands.argument('which', Arguments.STRING.create(event)).executes(logged(clear))))
      .then(Commands.literal('reset').then(Commands.argument('camp', Arguments.STRING.create(event)).executes(logged(reset))))
      .then(Commands.literal('expect').then(Commands.argument('what', Arguments.GREEDY_STRING.create(event)).executes(logged(expect))))))
})
