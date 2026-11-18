// priority: 68
// Companions: adventurers you hire for coins (sidequests work package; [companions] and [[adventurer]].hire in
// design/data/sidequests.toml). Built on Easy NPC 7.19 (no extra mod, decisions.md 18/11/2026): the companion is the
// preset ttl_comp_<kind> (vulnerable; MELEE_ATTACK, ATTACK_MOB_WITHOUT_CREEPER, HURT_BY_TARGET, OWNER_HURT_BY_TARGET,
// OWNER_HURT_TARGET), and after the import this script runs `/easy_npc owner set <npc> <player>` and
// `/easy_npc objective <npc> set follow owner`, sets max health and puts the weapon and armour in its hands.
//
// Rules
//   - hire: the "Join my party" button of an ambient adventurer (`/ttl companion hire`, the nearest hireable one within
//     6 blocks), Life 2, at most companions.max_per_soul, and the party cap: online FTB party members + their companions +
//     the new one <= companions.party_cap (5). The fee is a sink (TtlEcon.charge). The ambient adventurer leaves the town
//     and the companion stands in its place.
//   - a companion is never an FTB party member and never earns boss credit (bosses/boss.js credits players only).
//   - the contract ends when its minutes run out, when the companion dies, on `/ttl companion dismiss`, or when the soul
//     stays offline longer than offline_grace_minutes (logout puts the companion away, login brings it back).
//   - it cannot hurt players and players cannot hurt it (EntityEvents.beforeHurt below), so OWNER_HURT_TARGET never
//     turns it on another soul and nobody grief-kills someone else's companion.
// Player persistentData `ttl.comp` = {kind, npc, dim, lx, lz, until, hired, away (ms the owner logged out, 0 online)}.
// Entity tags: `ttl.comp`, `ttl.comp.o.<owner uuid>`. Stage `ttl.quest.side.hired` the first time (the book's tutorial).
const TtlCompanion = {
  KEY: 'ttl.comp',
  TAG: 'ttl.comp',
  HIRE_RANGE: 6,

  conf() {
    return TtlData.sidequests.companions
  },

  kind(id) {
    var all = TtlData.sidequests.adventurer || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY) || '')
    try {
      return raw ? JSON.parse(raw) : null
    } catch (e) {
      return null
    }
  },

  write(player, rec) {
    if (rec) player.persistentData.putString(this.KEY, JSON.stringify(rec))
    else player.persistentData.remove(this.KEY)
  },

  // ---- the party cap ----

  // {members, companions} of the soul's online party (the soul included; a soul alone is a party of one).
  party(server, player) {
    var members = [player]
    try {
      if (typeof TtlParty !== 'undefined') members = TtlParty.membersOf(server, player)
    } catch (e) {
      console.warn(`[ttl] companion: reading ${player.username}'s party failed, counting them alone: ${e}`)
    }
    var comps = 0
    var self = this
    members.forEach(m => {
      if (self.read(m)) comps++
    })
    return { members: members.length, companions: comps }
  },

  // '' or a reason code: off, life, max, cap, kind, fee.
  refusal(server, player, kindId) {
    var c = this.conf()
    if (!c.enabled) return 'off'
    if (TtlLife.phase(player) !== 'life2') return 'life'
    var k = this.kind(kindId)
    if (!k || !k.hire) return 'kind'
    if (this.read(player) && Number(c.max_per_soul) <= 1) return 'max'
    var p = this.party(server, player)
    if (p.members + p.companions + 1 > Number(c.party_cap)) return 'cap'
    if (typeof TtlEcon !== 'undefined' && !TtlEcon.canPay(player, k.hire.fee)) return 'fee'
    return ''
  },

  reasonText(code, k) {
    return {
      off: 'nobody is hiring out right now',
      life: 'only souls reborn in the Tensura world can hire adventurers',
      max: 'you already travel with a companion (/ttl companion dismiss first)',
      cap: `your party is full: party members and their companions together may be ${this.conf().party_cap} at most`,
      kind: 'this adventurer is not for hire',
      fee: `you cannot pay the fee (${k && k.hire && typeof TtlEcon !== 'undefined' ? TtlEcon.text(k.hire.fee) : '?'})`
    }[code] || code
  },

  // ---- the entity ----

  find(server, rec) {
    return rec && rec.npc ? TtlSideNpc.byUuid(server, rec.dim, rec.npc) : null
  },

  equip(server, e, hire) {
    var id = TtlSideNpc.uuidOf(e)
    TtlCmd.run(server, `item replace entity ${id} weapon.mainhand with ${hire.weapon}`)
    var a = String(hire.armor || '')
    if (a) {
      var mat = a === 'chainmail' ? 'chainmail' : a
      ;[['armor.head', 'helmet'], ['armor.chest', 'chestplate'], ['armor.legs', 'leggings'], ['armor.feet', 'boots']].forEach(s => {
        TtlCmd.run(server, `item replace entity ${id} ${s[0]} with minecraft:${mat}_${s[1]}`)
      })
    }
  },

  // Summons the companion of kind beside pos for player; the record's npc/dim are updated. Entity or null.
  summon(server, player, rec, pos) {
    var k = this.kind(rec.kind)
    if (!k || !k.hire) return null
    var e = TtlSideNpc.spawn(server, pos, `ttl_comp_${k.id}`, [this.TAG, `${this.TAG}.o.${this.uid(player)}`, 'ttl.side'])
    if (!e) return null
    TtlSideNpc.cmd(server, e, `owner set {npc} ${player.username}`)
    TtlSideNpc.cmd(server, e, 'objective {npc} set follow owner')
    TtlSideNpc.health(server, e, Number(k.hire.hp))
    TtlCmd.run(server, `attribute ${TtlSideNpc.uuidOf(e)} minecraft:generic.attack_damage base set 2`)
    this.equip(server, e, k.hire)
    rec.npc = TtlSideNpc.uuidOf(e)
    rec.dim = String(pos.dim)
    rec.lx = e.getX()
    rec.lz = e.getZ()
    return e
  },

  here(player) {
    return { dim: TtlLife.dimensionOf(player), x: Math.floor(player.getX()) + 0.5, y: Math.floor(player.getY()), z: Math.floor(player.getZ()) + 0.5 }
  },

  // The nearest ambient adventurer within HIRE_RANGE whose kind is hireable: {e, kind} or null.
  nearestHireable(server, player) {
    var best = null
    var bestD = this.HIRE_RANGE * this.HIRE_RANGE
    var self = this
    try {
      player.level.getEntities().forEach(e => {
        if (!e.isAlive() || !TtlSideNpc.hasTag(e, 'ttl.adv')) return
        var dx = e.getX() - player.getX()
        var dy = e.getY() - player.getY()
        var dz = e.getZ() - player.getZ()
        var d = dx * dx + dy * dy + dz * dz
        if (d > bestD) return
        var kind = TtlAdventurers.kindOfEntity(e)
        var k = self.kind(kind)
        if (!k || !k.hire) return
        best = { e: e, kind: kind }
        bestD = d
      })
    } catch (x) {
      console.error(`[ttl] companion: looking for adventurers near ${player.username} failed: ${x}`)
    }
    return best
  },

  // ---- actions (they return '' or a refusal text) ----

  hire(server, player) {
    var near = this.nearestHireable(server, player)
    if (!near) return 'nobody here is for hire (stand next to an adventurer)'
    var k = this.kind(near.kind)
    var code = this.refusal(server, player, near.kind)
    if (code) return this.reasonText(code, k)
    if (typeof TtlEcon !== 'undefined' && !TtlEcon.charge(server, player, k.hire.fee, `companion:${k.id}`)) return this.reasonText('fee', k)
    var pos = { dim: TtlLife.dimensionOf(player), x: near.e.getX(), y: near.e.getY(), z: near.e.getZ() }
    TtlSideNpc.remove(server, near.e)
    return this.begin(server, player, k, pos, Number(k.hire.minutes), 'hired')
  },

  // Staff/test hook: a companion of kind for player beside them, no fee, no town adventurer used.
  grant(server, player, kindId, minutes) {
    var k = this.kind(kindId)
    if (!k || !k.hire) return `unknown hireable adventurer ${kindId}`
    if (this.read(player)) return 'that soul already has a companion'
    return this.begin(server, player, k, this.here(player), minutes > 0 ? minutes : Number(k.hire.minutes), 'granted')
  },

  begin(server, player, k, pos, minutes, how) {
    var rec = { kind: String(k.id), npc: '', dim: String(pos.dim), lx: pos.x, lz: pos.z, hired: Date.now(), until: Date.now() + minutes * 60000, away: 0 }
    if (!this.summon(server, player, rec, pos)) return 'the companion could not be summoned (see the log)'
    this.write(player, rec)
    if (!player.stages.has('ttl.quest.side.hired')) player.stages.add('ttl.quest.side.hired')
    player.tell(Text.green(`${k.name}, ${k.title}, joins you for ${minutes} minutes.`))
    player.tell(Text.gray('A companion fights beside you but is no party member: no boss credit, no share of party rewards.'))
    console.info(`[ttl] companion: ${player.username} ${how} ${k.id} for ${minutes} min (${rec.npc})`)
    return ''
  },

  // Ends the contract: the companion walks off (removed), the record is gone.
  end(server, player, why) {
    var rec = this.read(player)
    if (!rec) return false
    var e = this.find(server, rec)
    if (e) TtlSideNpc.remove(server, e)
    this.write(player, null)
    var k = this.kind(rec.kind)
    player.tell(Text.gold(`${k ? k.name : 'Your companion'} leaves you${why ? `: ${why}` : ''}.`))
    console.info(`[ttl] companion: ${player.username}'s ${rec.kind} contract ended (${why})`)
    return true
  },

  statusLine(player) {
    var rec = this.read(player)
    if (!rec) return 'No companion. Hire one in a guild hall or a town (the "Join my party" button of an adventurer).'
    var k = this.kind(rec.kind)
    return `${k ? `${k.name}, ${k.title}` : rec.kind}: ${Math.max(0, Math.ceil((rec.until - Date.now()) / 60000))} minutes of contract left.`
  },

  // ---- upkeep ----

  tick(server, player) {
    var rec = this.read(player)
    if (!rec) return
    if (Date.now() > Number(rec.until)) {
      this.end(server, player, 'the contract is over')
      return
    }
    var e = this.find(server, rec)
    if (!e || !e.isAlive()) {
      if (e || TtlSidePlaces.isLoaded(server, rec.dim, rec.lx, rec.lz)) {
        this.end(server, player, 'fallen in battle')
        return
      }
      // Its chunk is unloaded (the soul teleported away): it catches up.
      if (this.summon(server, player, rec, this.here(player))) this.write(player, rec)
      return
    }
    var dim = TtlLife.dimensionOf(player)
    if (dim !== String(rec.dim)) {
      TtlSideNpc.remove(server, e)
      if (this.summon(server, player, rec, this.here(player))) this.write(player, rec)
      return
    }
    rec.lx = e.getX()
    rec.lz = e.getZ()
    if (TtlSidePlaces.dist(rec.lx, rec.lz, player.getX(), player.getZ()) > Number(this.conf().teleport_distance)) {
      TtlCmd.run(server, `execute in ${dim} run tp ${rec.npc} ${player.getX()} ${player.getY()} ${player.getZ()}`)
      rec.lx = player.getX()
      rec.lz = player.getZ()
    }
    this.write(player, rec)
  },

  onLogout(server, player) {
    var rec = this.read(player)
    if (!rec) return
    var e = this.find(server, rec)
    if (e) TtlSideNpc.remove(server, e)
    rec.npc = ''
    rec.away = Date.now()
    this.write(player, rec)
  },

  onLogin(server, player) {
    var rec = this.read(player)
    if (!rec) return
    var grace = Number(this.conf().offline_grace_minutes) * 60000
    if (Date.now() > Number(rec.until) || (rec.away && Date.now() - Number(rec.away) > grace)) {
      this.write(player, null)
      var k = this.kind(rec.kind)
      player.tell(Text.gold(`${k ? k.name : 'Your companion'} did not wait for you: the contract is over.`))
      return
    }
    rec.away = 0
    // Summoned a few seconds later, once the soul's chunk is loaded.
    var self = this
    server.scheduleInTicks(60, () => {
      try {
        if (self.summon(server, player, rec, self.here(player))) self.write(player, rec)
      } catch (e) {
        console.error(`[ttl] companion: bringing back ${player.username}'s companion failed: ${e}`)
      }
    })
    this.write(player, rec)
  },

  // beforeHurt: true when this hit must not land (companions and escort clients vs players, both ways).
  shield(event) {
    var target = event.entity
    var src = event.source ? event.source.actual : null
    if (!src || !target) return false
    var tProtected = TtlSideNpc.hasTag(target, this.TAG) || TtlSideNpc.hasTag(target, 'ttl.side.client')
    if (tProtected && src.isPlayer()) return true
    if (TtlSideNpc.hasTag(src, this.TAG) && (target.isPlayer() || TtlSideNpc.hasTag(target, this.TAG) || TtlSideNpc.hasTag(target, 'ttl.side.client'))) return true
    return false
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(20, Number(TtlData.sidequests.settings.poll_ticks))
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      server.getPlayerList().getPlayers().forEach(p => {
        try {
          TtlCompanion.tick(server, p)
        } catch (e) {
          console.error(`[ttl] companion: upkeep of ${p.username} failed: ${e}`)
        }
      })
    } catch (e) {
      console.error(`[ttl] companion: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})

PlayerEvents.loggedIn(event => {
  try {
    TtlCompanion.onLogin(event.player.getServer(), event.player)
  } catch (e) {
    console.error(`[ttl] companion: login of ${event.player.username} failed: ${e}`)
  }
})

PlayerEvents.loggedOut(event => {
  try {
    TtlCompanion.onLogout(event.player.getServer(), event.player)
  } catch (e) {
    console.error(`[ttl] companion: logout of ${event.player.username} failed: ${e}`)
  }
})

EntityEvents.death(event => {
  try {
    var e = event.entity
    if (!TtlSideNpc.hasTag(e, TtlCompanion.TAG)) return
    var id = TtlSideNpc.uuidOf(e)
    e.getServer().getPlayerList().getPlayers().forEach(p => {
      var rec = TtlCompanion.read(p)
      if (rec && rec.npc === id) {
        rec.npc = ''
        TtlCompanion.write(p, rec)
        TtlCompanion.end(e.getServer(), p, 'fallen in battle')
      }
    })
  } catch (x) {
    console.error(`[ttl] companion: death handling failed: ${x}`)
  }
})

EntityEvents.beforeHurt(event => {
  var stop = false
  try {
    stop = TtlCompanion.shield(event)
  } catch (e) {
    console.error(`[ttl] companion: hurt check failed: ${e}`)
  }
  // event.cancel() exits by throwing: never inside a try that catches it.
  if (stop) event.cancel()
})
